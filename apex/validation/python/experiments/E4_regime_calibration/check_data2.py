"""Data audit, part 2 (added on resume, 2026-11-28). It extends check_data.py.

1. Applies the study's corruption scan (bar-to-bar |log gap| > 1.5% and jump-and-back pairs) to every raw file,
   including the 1-minute files behind the 5m family.
2. Classifies each bar flagged by the pre-registered >15xATR14 rule by its NY weekday and time. A jump at the
   Sunday 18:00 NY reopen is a weekend gap; it is not file corruption.
3. Lists calendar holes > 3 days (CL 1H).
"""
import json
import numpy as np
import pandas as pd
import e4lib as E


def jump_scan(C, thr=0.015):
    lg = np.diff(np.log(C))
    big = np.abs(lg) > thr
    # jump-and-back: a gap > thr followed within 3 bars by an opposite gap of similar size (ratio 0.7-1.3)
    jb = 0
    idx = np.where(big)[0]
    for i in idx:
        for j in range(i + 1, min(i + 4, len(lg))):
            if abs(lg[j]) > thr and np.sign(lg[j]) != np.sign(lg[i]) and 0.7 < abs(lg[j]) / abs(lg[i]) < 1.3:
                jb += 1
                break
    return int(big.sum()), jb


res = {}
for fam in ("1h", "5m", "btc"):
    for name, a, mins in E.datasets(fam, include_excluded=True):
        C = a["C"]
        nbig, njb = jump_scan(C)
        A = E.atr(a["H"], a["L"], a["C"], 14)
        pc = np.r_[np.nan, C[:-1]]; pa = np.r_[np.nan, A[:-1]]
        g = np.maximum(np.abs(a["O"] - pc), np.abs(C - pc)) / pa
        g[:20] = 0
        flag15 = np.where(np.nan_to_num(g) > 15)[0]
        T = a["T"]
        loc = T.tz_convert(a["tz"])
        cls = []
        for i in flag15:
            gap_h = (T[i] - T[i - 1]).total_seconds() / 3600
            wd = loc[i].day_name()
            reopen = gap_h >= 1.0  # bar follows a session halt (daily halt or weekend)
            cls.append(dict(t_utc=str(T[i]), ny=str(loc[i]), weekday=wd, gap_hours=round(gap_h, 2),
                            jump_atr=round(float(g[i]), 1), after_halt=bool(reopen)))
        dts = np.diff(T.values).astype("timedelta64[h]").astype(float)
        holes = [(str(T[i]), str(T[i + 1]), round(dts[i] / 24, 1)) for i in np.where(dts > 72)[0]]
        r = dict(n=len(C), gaps_gt_1p5pct=nbig, jump_and_back=njb, n_flag15=len(flag15),
                 n_flag15_after_halt=int(sum(c["after_halt"] for c in cls)), flag15=cls, holes_gt_3d=holes)
        res[name] = r
        print(f"{name:8s} n={len(C):6d} gaps>1.5%={nbig:4d} jump&back={njb:4d} flag15={len(flag15)} "
              f"(after halt {r['n_flag15_after_halt']}) holes>3d={len(holes)}")
        for c in cls:
            print("    ", c)
        for h in holes:
            print("     hole", h)
json.dump(res, open(E.OUT + "/data_check2.json", "w"), indent=1)
