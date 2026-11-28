"""R1: volatility-regime definitions x hysteresis: persistence and OOS information on next-H realised range.
Pre-registered in apex/research/experiments/E4_regime_calibration.md section R1."""
import json, sys
import numpy as np
import e4lib as E

DEFS = ["p_atr", "p_rv", "p_bbw", "p_des"]
CLS = ["raw", "hysA", "hysB"]
HS = [20, 60]
rng = np.random.default_rng(20261127)


def one(a, f, H, null=None):
    """returns per-dataset arrays for IS/OOS and per (def, cls) states"""
    n = len(a["C"])
    mx, mn = E.fwd_max_min(a["H"], a["L"], H)
    rngH = mx - mn
    Y = np.log(rngH / f["A14"]); Ya = np.log(rngH / f["A100"])
    isx, oos, cut = E.split_idx(n, H)
    return Y, Ya, isx, oos


def run_family(fam, use_null=False):
    rows = []
    dsets = E.datasets(fam)
    store = {}
    for name, a, mins in dsets:
        if use_null:
            a = E.shuffle(a, rng)
            f = {}
            f["A14"] = E.atr(a["H"], a["L"], a["C"], 14); f["A100"] = E.atr(a["H"], a["L"], a["C"], 100)
            f["p_atr"] = E.pct_rank(f["A14"]); f["p_rv"] = E.pct_rank(E.rv(a["C"], 20))
            f["p_bbw"] = E.pct_rank(E.bbw(a["C"], 20)); f["p_des"] = E.pct_rank(E.tod_deseason_atr(a, mins))
        else:
            f = E.features(name, a, mins)
        states = {(d, c): E.classify(f[d], **E.HYS[c]) for d in DEFS for c in CLS}
        store[name] = (a, f, states)
    for H in HS:
        for d in DEFS:
            for c in CLS:
                per = dict(dwell=[], sw1000=[], pstay=[], occ=[])
                eS = {"Y": [], "Ya": []}; e0 = {"Y": [], "Ya": []}; eL = {"Y": [], "Ya": []}
                eSi = {"Y": [], "Ya": []}; e0i = {"Y": [], "Ya": []}
                blocks = []; means = {"Y": [], "Ya": []}
                for name, (a, f, states) in store.items():
                    s = states[(d, c)]
                    Y, Ya, isx, oos = one(a, f, H)
                    valid = np.isfinite(Y) & np.isfinite(Ya) & (s >= 0) & np.isfinite(f[d])
                    pm = np.zeros(len(s), bool); pm[E.WARM:] = True
                    pr = E.persistence(s, H, mask=pm & (s >= 0))
                    for k in ("dwell", "sw1000", "pstay"):
                        per[k].append(pr[k])
                    per["occ"].append(pr["occ"])
                    iv = isx[valid[isx]]; ov = oos[valid[oos]]
                    blocks.append(E.day_blocks(a, ov, H, E.BPD[fam]))
                    for key, YY in (("Y", Y), ("Ya", Ya)):
                        mu0 = YY[iv].mean()
                        mus = np.array([YY[iv][s[iv] == k].mean() if np.any(s[iv] == k) else mu0 for k in range(3)])
                        means[key].append(dict(IS=[float(YY[iv][s[iv] == k].mean()) if np.any(s[iv] == k) else None for k in range(3)],
                                               OOS=[float(YY[ov][s[ov] == k].mean()) if np.any(s[ov] == k) else None for k in range(3)]))
                        # linear on raw percentile
                        X = np.c_[np.ones(len(iv)), f[d][iv]]
                        beta = np.linalg.lstsq(X, YY[iv], rcond=None)[0]
                        predL = beta[0] + beta[1] * f[d][ov]
                        eS[key].append((YY[ov] - mus[s[ov]]) ** 2)
                        e0[key].append((YY[ov] - mu0) ** 2)
                        eL[key].append((YY[ov] - predL) ** 2)
                        eSi[key].append((YY[iv] - mus[s[iv]]) ** 2); e0i[key].append((YY[iv] - mu0) ** 2)
                bl = np.concatenate(blocks)
                row = dict(fam=fam, H=H, defn=d, cls=c, null=use_null,
                           dwell=float(np.nanmean(per["dwell"])), sw1000=float(np.nanmean(per["sw1000"])),
                           pstay=float(np.nanmean(per["pstay"])),
                           occ=[float(np.nanmean([o[k] for o in per["occ"]])) for k in range(3)],
                           n_oos=int(len(bl)))
                for key in ("Y", "Ya"):
                    es = np.concatenate(eS[key]); e0_ = np.concatenate(e0[key]); el = np.concatenate(eL[key])
                    r, lo, hi = E.block_boot_ratio(es, e0_, bl, reps=2000 if not use_null else 300)
                    rL, loL, hiL = E.block_boot_ratio(el, e0_, bl, reps=2000 if not use_null else 300)
                    row[f"R2_{key}"] = 1 - r; row[f"R2_{key}_lo"] = 1 - hi; row[f"R2_{key}_hi"] = 1 - lo
                    row[f"R2lin_{key}"] = 1 - rL; row[f"R2lin_{key}_lo"] = 1 - hiL; row[f"R2lin_{key}_hi"] = 1 - loL
                    row[f"R2IS_{key}"] = 1 - np.concatenate(eSi[key]).sum() / np.concatenate(e0i[key]).sum()
                    row[f"means_{key}"] = means[key]
                    row[f"p_{key}"] = E.p_from_ci(row[f"R2_{key}"], row[f"R2_{key}_lo"], row[f"R2_{key}_hi"])
                rows.append(row)
                print(fam, H, d, c, "null" if use_null else "", "dwell %.1f sw %.1f pstay %.3f occ %s | R2_Y %.4f [%.4f,%.4f] lin %.4f | R2_Ya %.4f [%.4f,%.4f]" % (
                    row["dwell"], row["sw1000"], row["pstay"], np.round(row["occ"], 2), row["R2_Y"], row["R2_Y_lo"], row["R2_Y_hi"],
                    row["R2lin_Y"], row["R2_Ya"], row["R2_Ya_lo"], row["R2_Ya_hi"]), flush=True)
    return rows


if __name__ == "__main__":
    fams = sys.argv[1:] or list(E.FAMS)
    allrows = []
    for fam in fams:
        allrows += run_family(fam, False)
        allrows += run_family(fam, True)
    # Holm within each family over defs x H for hysA (the primary classifier) on Y
    for fam in fams:
        prim = [r for r in allrows if r["fam"] == fam and not r["null"] and r["cls"] == "hysA"]
        adj = E.holm([r["p_Y"] for r in prim])
        for r, q in zip(prim, adj):
            r["holm_Y"] = float(q)
    json.dump(allrows, open(E.OUT + "/r1_" + "_".join(fams) + ".json", "w"), indent=1, default=float)
