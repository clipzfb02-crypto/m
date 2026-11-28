"""R5b (EXPLORATORY robustness, added on resume 2026-11-28; not pre-registered):
1. Drift-adjusted outcome: y_dm = sign(C_t - C_{t-20}) * ((C_{t+h} - C_t)/ATR14_t - m), where m is the mean of
   (C_{t+h} - C_t)/ATR14_t over the same dataset and segment (a diagnostic only: m uses the segment's own data).
   It removes the part of TREND - RANGE that comes from a drifting asset plus a sign imbalance between states.
2. Sign balance: share of positive past-20 signs inside TREND and RANGE.
3. BTC by calendar year: TREND - RANGE per year (ER20 hysteresis classifier), with day-block bootstrap CIs.
"""
import json
import numpy as np
import pandas as pd
import e4lib as E
from r3_breakout import group_diff_boot
from r5_trend_regime import states_for, LB, HS

out = dict(drift_adj=[], btc_year=[])
for fam in E.FAMS:
    dsets = [(name, a, mins, states_for(a)) for name, a, mins in E.datasets(fam)]
    for h in HS:
        for meas in ("er", "adx", "vr"):
            for sgn, sg in (("IS", 0), ("OOS", 1)):
                Y, YD, S, B, PS = [], [], [], [], []
                for name, a, mins, st in dsets:
                    C = a["C"]; A = E.atr(a["H"], a["L"], C, 14)
                    past = np.full(len(C), np.nan); past[LB:] = C[LB:] - C[:-LB]
                    fwd = (E.fwd_close(C, h) - C) / A
                    isx, oos, cut = E.split_idx(len(C), h)
                    idx = isx if sg == 0 else oos
                    s = st[(meas, "hys")][idx]
                    ok = np.isfinite(fwd[idx]) & np.isfinite(past[idx]) & (s >= 0)
                    idx = idx[ok]; s = s[ok]
                    m = np.mean(fwd[idx])
                    Y.append(np.sign(past[idx]) * fwd[idx]); YD.append(np.sign(past[idx]) * (fwd[idx] - m))
                    S.append(s); B.append(E.day_blocks(a, idx, h, E.BPD[fam])); PS.append(np.sign(past[idx]))
                Y, YD, S, B, PS = map(np.concatenate, (Y, YD, S, B, PS))
                raw = group_diff_boot(Y, S, B, 2, 0); dm = group_diff_boot(YD, S, B, 2, 0)
                pos_tr = float(np.mean(PS[S == 2] > 0)); pos_rg = float(np.mean(PS[S == 0] > 0))
                row = dict(fam=fam, h=h, measure=meas, seg=sgn, TR_raw=raw, TR_driftadj=dm, pos_share_TREND=pos_tr,
                           pos_share_RANGE=pos_rg, n=int(len(Y)))
                out["drift_adj"].append(row)
                print(f"{fam} h={h} {meas} {sgn}: T-R raw {raw[0]:+.3f} [{raw[1]:+.3f},{raw[2]:+.3f}]  drift-adj {dm[0]:+.3f} "
                      f"[{dm[1]:+.3f},{dm[2]:+.3f}]  P(past>0) TREND {pos_tr:.3f} RANGE {pos_rg:.3f}", flush=True)

# BTC by year
name, a, mins = E.datasets("btc")[0]
st = states_for(a)
C = a["C"]; A = E.atr(a["H"], a["L"], C, 14)
past = np.full(len(C), np.nan); past[LB:] = C[LB:] - C[:-LB]
yr = np.array([t.year for t in a["T"]])
for h in HS:
    fwd = (E.fwd_close(C, h) - C) / A
    y = np.sign(past) * fwd
    s = st[("er", "hys")]
    for Y_ in range(2016, 2025):
        idx = np.where((yr == Y_) & np.isfinite(y) & (s >= 0) & (np.arange(len(C)) >= E.WARM))[0]
        if len(idx) < 1000:
            continue
        blk = E.day_blocks(a, idx, h, E.BPD["btc"])
        m = np.mean(fwd[idx])
        r = group_diff_boot(y[idx], s[idx], blk, 2, 0)
        rd = group_diff_boot(np.sign(past[idx]) * (fwd[idx] - m), s[idx], blk, 2, 0)
        out["btc_year"].append(dict(h=h, year=Y_, n=int(len(idx)), TR=r, TR_driftadj=rd))
        print(f"BTC h={h} {Y_}: n={len(idx)} T-R {r[0]:+.3f} [{r[1]:+.3f},{r[2]:+.3f}] drift-adj {rd[0]:+.3f} [{rd[1]:+.3f},{rd[2]:+.3f}]", flush=True)
json.dump(out, open(E.OUT + "/r5b_robust.json", "w"), indent=1, default=float)
