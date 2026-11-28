import numpy as np, pandas as pd
F = "/tmp/claude-0/-home-user-m/7ce60006-3639-59b1-8cd3-87355409d58a/scratchpad/i2/dl/data_src/data/Dataset_NQ_1min_2022_2025.csv"
d = pd.read_csv(F)
d["t"] = pd.to_datetime(d["timestamp ET"], format="%m/%d/%Y %H:%M")
print(len(d), d.t.min(), d.t.max(), "sorted", d.t.is_monotonic_increasing, "dups", d.t.duplicated().sum())
d = d.sort_values("t").drop_duplicates("t")
st = d.t.diff().dt.total_seconds()
print("step counts", st.value_counts().head(8).to_dict())
o, h, l, c = [d[k].values.astype(float) for k in "open high low close".split()]
pc = np.r_[np.nan, c[:-1]]
tr = np.maximum(h - l, np.maximum(np.abs(h - pc), np.abs(l - pc)))
atr = pd.Series(tr).rolling(60, min_periods=5).mean().shift(1).values
j = np.abs(o - pc) / atr
big = np.nonzero(j > 8)[0]
print("gaps>8ATR(1m,60)", len(big))
for i in big[:40]:
    print("  ", d.t.iloc[i], "prevC", pc[i], "O", o[i], f"{j[i]:.1f}", "step_h", st.iloc[i]/3600)
days = d.t.dt.date.nunique(); print("days", days)
mon = d.groupby(d.t.dt.to_period("M")).size(); print(mon.to_string())
