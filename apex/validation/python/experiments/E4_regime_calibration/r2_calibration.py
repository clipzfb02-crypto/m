"""R2: does the volatility regime improve calibration of P(level at distance d reached within H)?
Models (fitted IS): P0 pooled, P1 regime (hysA ATR-pct), P1b TOD clock, P2 regime+clock, P3 blended unit, P4 blended+clock.
Pre-registered in apex/research/experiments/E4_regime_calibration.md section R2."""
import json, sys
import numpy as np
import e4lib as E

D = np.array([0.5, 1, 1.5, 2, 3, 4, 6])
HS = [20, 60]
M_POOL = 200
MODELS = ["P0", "P1", "P1b", "P2", "P3", "P4"]


def surv_fit(e):
    e = np.sort(e[np.isfinite(e)]); return e


def surv(es, x):
    k = np.searchsorted(es, x, side="left")
    return np.clip(1.0 - k / len(es), 1e-3, 1 - 1e-3)


def clock(a, f, mins, isx, H):
    """TOD variance clock fitted on IS bars; returns s_t = sqrt(mean_fwd c / mean_back14 c) for all t."""
    b = E.tod_bucket(a, mins)
    tr = E.true_range(a["H"], a["L"], a["C"])
    A100p = np.r_[np.nan, f["A100"][:-1]]
    r = tr / A100p
    nb = int(b.max()) + 1
    c = np.ones(nb)
    ok = isx[np.isfinite(r[isx])]
    m_all = np.nanmean(r[ok])
    for k in range(nb):
        mk = ok[b[ok] == k]
        if len(mk) >= 20:
            c[k] = (np.mean(r[mk]) / m_all) ** 2
    cb = c[b]
    cb = cb / cb[ok].mean()
    n = len(cb); cs = np.r_[0, np.cumsum(cb)]
    fwd = np.full(n, np.nan); back = np.full(n, np.nan)
    t = np.arange(n)
    okf = t + H < n
    fwd[okf] = (cs[t[okf] + H + 1] - cs[t[okf] + 1]) / H
    okb = t >= 13
    back[okb] = (cs[t[okb] + 1] - cs[t[okb] - 13]) / 14
    return np.sqrt(fwd / back)


def build(fam, H):
    stride = 2 if fam == "5m" else 1
    rec = {k: [] for k in ["y", "blk", "st", "d", "ds"] + MODELS}
    rec_is = {k: [] for k in ["y"] + MODELS}
    for name, a, mins in E.datasets(fam):
        f = E.features(name, a, mins)
        s = E.classify(f["p_atr"], **E.HYS["hysA"])
        A14 = f["A14"]; u = np.sqrt(f["A14"] * f["A100"])
        mx, mn = E.fwd_max_min(a["H"], a["L"], H)
        C = a["C"]
        eu = (mx - C) / A14; ed = (C - mn) / A14
        n = len(C)
        isx, oos, cut = E.split_idx(n, H)
        isx = isx[::stride]; oos = oos[::stride]
        sc = clock(a, f, mins, isx, H)
        valid = np.isfinite(eu) & np.isfinite(ed) & (s >= 0) & np.isfinite(sc) & np.isfinite(u) & (A14 > 0)
        isx = isx[valid[isx]]; oos = oos[valid[oos]]
        # IS samples (both sides pooled)
        def two(x, idx):
            return np.r_[x[idx], x[idx]]
        eI = np.r_[eu[isx], ed[isx]]; sI = two(s, isx); scI = two(sc, isx); bI = two(A14 / u, isx)
        S0 = surv_fit(eI)
        Sk = [surv_fit(eI[sI == k]) for k in range(3)]; nk = [np.sum(s[isx] == k) for k in range(3)]
        S0c = surv_fit(eI / scI)
        Skc = [surv_fit((eI / scI)[sI == k]) for k in range(3)]
        S0u = surv_fit(eI * bI)
        S0uc = surv_fit(eI * bI / scI)

        def predict(idx):
            out = {m: [] for m in MODELS}; ys = []; st = []; dd = []
            for side in (0, 1):
                e = eu if side == 0 else ed
                for d in D:
                    y = (e[idx] >= d).astype(float); ys.append(y); st.append(s[idx]); dd.append(np.full(len(idx), d))
                    p0 = surv(S0, d) * np.ones(len(idx))
                    out["P0"].append(p0)
                    p1 = np.empty(len(idx)); p2 = np.empty(len(idx))
                    pc0 = surv(S0c, d / sc[idx])
                    for k in range(3):
                        mk = s[idx] == k
                        if len(Sk[k]) > 0:
                            p1[mk] = (nk[k] * surv(Sk[k], d) + M_POOL * surv(S0, d)) / (nk[k] + M_POOL)
                            p2[mk] = (nk[k] * surv(Skc[k], d / sc[idx][mk]) + M_POOL * pc0[mk]) / (nk[k] + M_POOL)
                        else:
                            p1[mk] = surv(S0, d); p2[mk] = pc0[mk]
                    out["P1"].append(p1); out["P2"].append(p2); out["P1b"].append(pc0)
                    out["P3"].append(surv(S0u, d * A14[idx] / u[idx]))
                    out["P4"].append(surv(S0uc, d * A14[idx] / u[idx] / sc[idx]))
            return {m: np.concatenate(v) for m, v in out.items()}, np.concatenate(ys), np.concatenate(st), np.concatenate(dd)

        po, yo, so, do_ = predict(oos)
        pi, yi, _, _ = predict(isx)
        blk = E.day_blocks(a, oos, H, E.BPD[fam])
        blk = np.tile(blk, 2 * len(D))
        rec["y"].append(yo); rec["blk"].append(blk); rec["st"].append(so); rec["d"].append(do_)
        rec["ds"].append(np.full(len(yo), name, dtype=object))
        rec_is["y"].append(yi)
        for m in MODELS:
            rec[m].append(po[m]); rec_is[m].append(pi[m])
    return {k: np.concatenate(v) for k, v in rec.items()}, {k: np.concatenate(v) for k, v in rec_is.items()}


def metrics(p, y):
    a, b = E.calib_slope(p, y)
    mu = E.murphy(p, y)
    return dict(n=int(len(y)), base=float(y.mean()), LL=float(E.logloss_vec(p, y).mean()), BS=float(E.brier_vec(p, y).mean()),
                ECE=float(E.ece(p, y)), slope=b, intercept=a, CITL=float(y.mean() - p.mean()),
                REL=mu["REL"], RES=mu["RES"], UNC=mu["UNC"])


def reliab(p, y, bins=10):
    b = np.minimum((p * bins).astype(int), bins - 1); out = []
    for k in range(bins):
        m = b == k
        if m.sum() > 0:
            out.append((k, int(m.sum()), float(p[m].mean()), float(y[m].mean())))
    return out


def run(fam):
    rows = []
    for H in HS:
        R, RI = build(fam, H)
        y = R["y"]; blk = R["blk"]
        res = dict(fam=fam, H=H, n_probes=int(len(y)), n_blocks=int(len(np.unique(blk))), OOS={}, IS={}, cmp={}, by_state={}, by_d={}, reliab={}, per_ds={})
        for m in MODELS:
            res["OOS"][m] = metrics(R[m], y)
            res["IS"][m] = metrics(RI[m], RI["y"])
            res["reliab"][m] = reliab(R[m], y)
            res["by_state"][m] = {int(k): dict(n=int(np.sum(R["st"] == k)), CITL=float(y[R["st"] == k].mean() - R[m][R["st"] == k].mean()),
                                              LL=float(E.logloss_vec(R[m][R["st"] == k], y[R["st"] == k]).mean())) for k in range(3)}
            res["by_d"][m] = {float(d): float(y[R["d"] == d].mean() - R[m][R["d"] == d].mean()) for d in D}
            res["per_ds"][m] = {}
            for ds in np.unique(R["ds"]):
                mk = R["ds"] == ds
                res["per_ds"][m][ds] = dict(LL=float(E.logloss_vec(R[m][mk], y[mk]).mean()), BS=float(E.brier_vec(R[m][mk], y[mk]).mean()),
                                            ECE=float(E.ece(R[m][mk], y[mk])))
        for (m1, m0) in [("P1", "P0"), ("P2", "P0"), ("P2", "P1"), ("P1b", "P0"), ("P3", "P0"), ("P4", "P0"), ("P4", "P3"), ("P2", "P1b")]:
            l1 = E.logloss_vec(R[m1], y); l0 = E.logloss_vec(R[m0], y)
            r, lo, hi = E.block_boot_ratio(l1, l0, blk)
            b1 = E.brier_vec(R[m1], y); b0 = E.brier_vec(R[m0], y)
            dB, dBlo, dBhi = E.block_boot_mean(b1 - b0, blk)
            # per-dataset sign count
            wins = sum(1 for ds in np.unique(R["ds"]) if res["per_ds"][m1][ds]["LL"] < res["per_ds"][m0][ds]["LL"])
            res["cmp"][f"{m1}_vs_{m0}"] = dict(dLLpct=100 * (r - 1), lo=100 * (lo - 1), hi=100 * (hi - 1),
                                               dBS=dB, dBS_lo=dBlo, dBS_hi=dBhi, ds_wins=wins, n_ds=int(len(np.unique(R["ds"]))),
                                               dREL=res["OOS"][m1]["REL"] - res["OOS"][m0]["REL"],
                                               dRES=res["OOS"][m1]["RES"] - res["OOS"][m0]["RES"],
                                               p=E.p_from_ci(100 * (r - 1), 100 * (lo - 1), 100 * (hi - 1)))
        rows.append(res)
        print(f"== {fam} H={H} probes={len(y)} blocks={res['n_blocks']}")
        for m in MODELS:
            o = res["OOS"][m]
            print(f"  {m:4s} LL {o['LL']:.5f} BS {o['BS']:.5f} ECE {o['ECE']:.4f} slope {o['slope']:.3f} int {o['intercept']:+.3f} CITL {o['CITL']:+.4f} REL {o['REL']:.5f} RES {o['RES']:.5f} | IS LL {res['IS'][m]['LL']:.5f} | stateCITL " +
                  " ".join(f"{res['by_state'][m][k]['CITL']:+.3f}" for k in range(3)))
        for k, v in res["cmp"].items():
            print(f"  {k:10s} dLL% {v['dLLpct']:+.3f} [{v['lo']:+.3f},{v['hi']:+.3f}] dBS {v['dBS']:+.6f} [{v['dBS_lo']:+.6f},{v['dBS_hi']:+.6f}] wins {v['ds_wins']}/{v['n_ds']} dREL {v['dREL']:+.6f} dRES {v['dRES']:+.6f}", flush=True)
    return rows


if __name__ == "__main__":
    fams = sys.argv[1:] or list(E.FAMS)
    out = []
    for fam in fams:
        out += run(fam)
    json.dump(out, open(E.OUT + "/r2_" + "_".join(fams) + ".json", "w"), indent=1, default=float)
