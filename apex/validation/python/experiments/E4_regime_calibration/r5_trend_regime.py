"""R5: trend / range / transition classification with hysteresis; stability and whether the state conditions
the sign of momentum vs mean-reversion returns out of sample.
Pre-registered in apex/research/experiments/E4_regime_calibration.md section R5."""
import json, sys
import numpy as np
import e4lib as E
from r3_breakout import group_diff_boot

HS = [20, 60]
LB = 20
N_NULL = 20
CLS = {
    "hys": dict(lo_in=30, lo_out=40, hi_in=70, hi_out=60, dwell=5, raw=False),
    "raw": dict(lo_in=30, lo_out=30, hi_in=70, hi_out=70, dwell=0, raw=True),
}
ABS = {"ER_abs": ("er", dict(lo_in=0.20, lo_out=0.20, hi_in=0.40, hi_out=0.40, dwell=0, raw=True)),
       "ADX_abs": ("adx", dict(lo_in=20, lo_out=20, hi_in=25, hi_out=25, dwell=0, raw=True))}


def measures(a):
    H, L, C = a["H"], a["L"], a["C"]
    m = {"er": E.er(C, 20), "adx": E.adx(H, L, C, 14)}
    vr, h = E.vr_hurst(C, 4, 96); m["vr"] = h
    return m


def states_for(a):
    m = measures(a)
    st = {}
    for k in ("er", "adx", "vr"):
        p = E.pct_rank(m[k])
        for c, kw in CLS.items():
            st[(k, c)] = E.classify(p, **kw)
    for name, (k, kw) in ABS.items():
        st[(name, "abs")] = E.classify(m[k], **kw)
    return st


def outcome(a, h):
    C = a["C"]; A = E.atr(a["H"], a["L"], C, 14)
    past = np.full(len(C), np.nan); past[LB:] = C[LB:] - C[:-LB]
    y = np.sign(past) * (E.fwd_close(C, h) - C) / A
    return y


def collect(fam, arrs, h):
    """pooled arrays of y, state per key, segment, blocks"""
    Y, SEG, BLK = [], [], []
    ST = {}
    for name, a, mins, st in arrs:
        y = outcome(a, h)
        n = len(y)
        isx, oos, cut = E.split_idx(n, h)
        seg = np.full(n, -1); seg[isx] = 0; seg[oos] = 1
        idx = np.where((seg >= 0) & np.isfinite(y))[0]
        Y.append(y[idx]); SEG.append(seg[idx]); BLK.append(E.day_blocks(a, idx, h, E.BPD[fam]))
        for k, s in st.items():
            ST.setdefault(k, []).append(s[idx])
    return np.concatenate(Y), np.concatenate(SEG), np.concatenate(BLK), {k: np.concatenate(v) for k, v in ST.items()}


def run(fam):
    dsets = E.datasets(fam)
    real = [(name, a, mins, states_for(a)) for name, a, mins in dsets]
    rng = np.random.default_rng(99)
    nulls = []
    for i in range(N_NULL):
        nulls.append([(name, b, mins, states_for(b)) for name, a, mins in dsets for b in [E.sign_flip(a, rng)]])
    rows = []
    for h in HS:
        Y, SEG, BLK, ST = collect(fam, real, h)
        nullstats = []
        for nl in nulls:
            Yn, SEGn, BLKn, STn = collect(fam, nl, h)
            d = {}
            for k in STn:
                for sg in (0, 1):
                    m = (SEGn == sg) & (STn[k] >= 0)
                    yy = Yn[m]; ss = STn[k][m]
                    d[(k, sg)] = (yy[ss == 2].mean() - yy[ss == 0].mean()) if (ss == 2).any() and (ss == 0).any() else np.nan
            nullstats.append(d)
        for k in ST:
            for sg, sgn in ((0, "IS"), (1, "OOS")):
                m = (SEG == sg) & (ST[k] >= 0)
                yy = Y[m]; ss = ST[k][m]; bb = BLK[m]
                row = dict(fam=fam, h=h, measure=k[0], cls=k[1], seg=sgn, n=int(m.sum()))
                for kk, kn in ((0, "RANGE"), (1, "TRANS"), (2, "TREND")):
                    mk = ss == kk
                    row[kn] = list(E.block_boot_mean(yy[mk], bb[mk], reps=1000)) + [int(mk.sum())]
                row["all"] = list(E.block_boot_mean(yy, bb, reps=1000))
                est, lo, hi = group_diff_boot(yy, ss, bb, 2, 0)
                row["diff_TR"] = [est, lo, hi, E.p_from_ci(est, lo, hi)]
                nv = np.array([d[(k, sg)] for d in nullstats], float)
                row["null_band"] = [float(np.nanpercentile(nv, 2.5)), float(np.nanpercentile(nv, 97.5)), float(np.nanmean(nv))]
                rows.append(row)
                print(f"{fam} h={h} {k[0]:7s} {k[1]:3s} {sgn:3s} n={row['n']} RANGE {row['RANGE'][0]:+.3f} TRANS {row['TRANS'][0]:+.3f} TREND {row['TREND'][0]:+.3f} all {row['all'][0]:+.3f} | T-R {est:+.3f} [{lo:+.3f},{hi:+.3f}] null [{row['null_band'][0]:+.3f},{row['null_band'][1]:+.3f}]", flush=True)
    # stability (persistence) real vs null
    stab = []
    for k in real[0][3]:
        for H in HS:
            pr = [E.persistence(st[k], H, mask=(np.arange(len(st[k])) >= E.WARM) & (st[k] >= 0)) for _, _, _, st in real]
            pn = [E.persistence(st[k], H, mask=(np.arange(len(st[k])) >= E.WARM) & (st[k] >= 0)) for nl in nulls[:5] for _, _, _, st in nl]
            r = dict(fam=fam, measure=k[0], cls=k[1], H=H,
                     dwell=float(np.mean([p["dwell"] for p in pr])), sw1000=float(np.mean([p["sw1000"] for p in pr])),
                     pstay=float(np.mean([p["pstay"] for p in pr])), occ=[float(np.mean([p["occ"][j] for p in pr])) for j in range(3)],
                     null_dwell=float(np.mean([p["dwell"] for p in pn])), null_sw1000=float(np.mean([p["sw1000"] for p in pn])),
                     null_pstay=float(np.mean([p["pstay"] for p in pn])))
            stab.append(r)
            print(f"STAB {fam} {k[0]:7s} {k[1]:3s} H={H} dwell {r['dwell']:.1f} (null {r['null_dwell']:.1f}) sw/1000 {r['sw1000']:.1f} (null {r['null_sw1000']:.1f}) pstay {r['pstay']:.3f} (null {r['null_pstay']:.3f}) occ {np.round(r['occ'], 2)}", flush=True)
    return rows, stab


if __name__ == "__main__":
    fams = sys.argv[1:] or list(E.FAMS)
    rows, stab = [], []
    for fam in fams:
        r, s = run(fam); rows += r; stab += s
    json.dump(dict(rows=rows, stab=stab), open(E.OUT + "/r5_" + "_".join(fams) + ".json", "w"), indent=1, default=float)
