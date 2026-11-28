"""Data verification for E2_signals (run on resume, 2026-11-28). No outcomes are computed here.
Checks: (1) NQ 1m file is ET and close-labelled; (2) CME 1h files are UTC; (3) the NQ 1m series is back-adjusted
(no roll jumps) while the CME files are not; (4) the roll bars listed in A6 coincide with jumps; (5) CL holes.
"""
import glob
import os
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import e2data as D  # noqa: E402

raw = pd.read_csv(D.NQ1M, usecols=[0, 1, 2, 3, 4])
raw.columns = ["ts", "open", "high", "low", "close"]
raw["ts"] = pd.to_datetime(raw.ts, format="%m/%d/%Y %H:%M")
hm = raw.ts.dt.strftime("%H:%M")
print("NQ1m rows", len(raw), raw.ts.min(), raw.ts.max())
print("  bars stamped 18:00:", int((hm == "18:00").sum()), " 18:01:", int((hm == "18:01").sum()),
      " 17:00:", int((hm == "17:00").sum()), " 17:01:", int((hm == "17:01").sum()))
print("  -> a close-labelled ET file has 18:01 as first and 17:00 as last bar of each Globex day")

# CME 1h hour-of-day histogram (UTC): maintenance break is 21-22 UTC (EDT) / 22-23 UTC (EST)
for sym in ["NQ", "ES", "CL"]:
    f = glob.glob(D.CME + f"{sym}/{sym}_1h_*.csv")[0]
    d = pd.read_csv(f, parse_dates=["datetime"])
    cnt = d.datetime.dt.hour.value_counts().sort_index()
    print(sym, "1h rows", len(d), d.datetime.min(), d.datetime.max(), "least-populated UTC hours:",
          cnt.nsmallest(3).to_dict())

# overlap: CME NQ 1h (UTC->ET) vs NQ 1m resampled to 1h (ET, open-labelled)
nq1m, _ = D.load_nq("1h")
c = pd.read_csv(glob.glob(D.CME + "NQ/NQ_1h_*.csv")[0], parse_dates=["datetime"])
c["ts"] = c.datetime.dt.tz_localize("UTC").dt.tz_convert("America/New_York").dt.tz_localize(None)
m = nq1m.merge(c[["ts", "open", "close"]], on="ts", suffixes=("", "_cme"))
m["diff"] = m.close_cme - m.close
r1 = np.log(m.close / m.open); r2 = np.log(m.close_cme / m.open_cme)
print("overlap bars", len(m), "corr of 1h log returns (UTC assumption):", round(np.corrcoef(r1, r2)[0, 1], 4))
for sh in [-1, 1]:
    c2 = c.copy(); c2["ts"] = c2.ts + pd.Timedelta(hours=sh)
    mm = nq1m.merge(c2[["ts", "open", "close"]], on="ts", suffixes=("", "_cme"))
    print(f"  shifted {sh:+d}h corr:", round(np.corrcoef(np.log(mm.close / mm.open), np.log(mm.close_cme / mm.open_cme))[0, 1], 4))
# level offset steps (back-adjustment differences) and where they change
dd = m["diff"].round(2)
chg = m.loc[dd.diff().abs() > 20, ["ts", "diff"]]
print("offset (CME - NQ1m) at start/end:", dd.iloc[0], dd.iloc[-1], "| offset steps >20pt at:")
print(chg.to_string())

# NQ 1m continuity: largest 1h open gaps relative to the median bar range
g = (nq1m.open - nq1m.close.shift()).abs() / (nq1m.high - nq1m.low).median()
print("NQ1m(1h) largest open gaps / median range:", g.nlargest(5).round(1).to_dict())

# roll bars in the CME equity files
for sym in ["ES", "YM", "RTY"]:
    df, meta = D.load_cme1h(sym)
    gap = (df.open - df.close.shift()).abs() / (df.high - df.low).median()
    top = gap.nlargest(6)
    print(sym, "guard bars", int(df.guard.sum()), "| top open-gap bars (ET):",
          [(str(df.ts[i]), round(v, 1), bool(df.guard[i])) for i, v in top.items()])
df, meta = D.load_cme1h("CL")
print("CL guard bars", int(df.guard.sum()), "gap_days>4:", int((df.gap_days > 4).sum()),
      "largest gaps (days):", df.gap_days.nlargest(5).round(2).tolist())
b, _ = D.load_btc()
print("BTC rows", len(b), b.ts.min(), b.ts.max(), "gaps>4d:", int((b.gap_days > 4).sum()),
      "dup ts:", int(b.ts.duplicated().sum()))
