# H1 secondary (added after seeing H1c; flagged as a deviation): time-of-day-matched single-level reach baseline.
# Starts = the same decision bar (E_open / E_ny) on every IS day, so the ATR unit has the same vol-clock position.
import numpy as np, pandas as pd, math, json
import e3lib as L, common_load as C, h1
A = pd.read_pickle(L.OUT + "h1_rows.pkl")
out = []
rows = []
for (tf, ds), g in A.groupby(["tf", "ds"]):
    o = C.get(ds, tf); df = o["df"]; n = len(df)
    day = df.day.values; first_bar = np.r_[0, np.flatnonzero(np.diff(day)) + 1]
    oos0 = L.split_days(df); H = h1.race_h(tf, ds)
    tmin = (df.t.dt.hour * 60 + df.t.dt.minute).values; step = 60 if tf == "1h" else 5
    for ev in ("E_open", "E_ny"):
        st = []
        for D in range(1, min(oos0 - 2, day.max() + 1)):
            fb = first_bar[D]; lb = first_bar[D + 1] - 1 if D + 1 <= day.max() else n - 1
            if ev == "E_open":
                st.append(fb)
            else:
                tm = tmin[fb:lb + 1]
                k = np.flatnonzero((tm <= 570) & (tm + step > 570))
                if len(k): st.append(fb + k[0])
        S = L.RaceSurface(df, np.array(st), H, o["tick"])
        gg = g[g.ev == ev].copy()
        gg["p_up_tm"] = S.p_reach(gg.du.values, 1); gg["p_dn_tm"] = S.p_reach(gg.dd.values, -1)
        gg["nstart_tm"] = S.n
        rows.append(gg)
B = pd.concat(rows)
lines = []
for tf in ("1h", "5m"):
    for ev in ("E_open", "E_ny"):
        for part in ("IS", "OOS"):
            s = B[(B.tf == tf) & (B.ev == ev) & (B.oos if part == "OOS" else B.is_)]
            y = np.r_[s.reach_up.astype(float), s.reach_dn.astype(float)]
            p = np.r_[s.p_up_tm, s.p_dn_tm]
            b = np.r_[s.ds.astype("category").cat.codes.astype("int64").values * 100000 + s.day.values] 
            b = np.r_[b, b]
            m, lo, hi, se = L.block_boot_mean(y - p, b, block_len=3)
            lines.append(f"{tf} {ev} {part}: n={len(y)} obs {100*y.mean():.1f} base_tm {100*p.mean():.1f} edge {100*m:+.2f} [{100*lo:+.2f},{100*hi:+.2f}] p={L.p_from_ci(m,se):.3f}")
            for ds in s.ds.unique():
                s2 = s[s.ds == ds]
                y2 = np.r_[s2.reach_up.astype(float), s2.reach_dn.astype(float)]; p2 = np.r_[s2.p_up_tm, s2.p_dn_tm]
                b2 = np.r_[s2.day.values, s2.day.values]
                if len(y2) < 40: continue
                m2, lo2, hi2, se2 = L.block_boot_mean(y2 - p2, b2, block_len=3)
                lines.append(f"     {ds:4s} n={len(y2)} obs {100*y2.mean():.1f} base_tm {100*p2.mean():.1f} edge {100*m2:+.2f} [{100*lo2:+.2f},{100*hi2:+.2f}] (starts {int(s2.nstart_tm.iloc[0])})")
txt = "\n".join(lines); print(txt); open(L.OUT + "h1_tm_results.txt", "w").write(txt)
