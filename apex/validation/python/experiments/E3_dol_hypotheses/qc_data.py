# Data QC (structure only: timestamps, gaps, jumps). Not outcome analysis.
import sys, glob, numpy as np, pandas as pd
ST = "/tmp/claude-0/-home-user-m/7ce60006-3639-59b1-8cd3-87355409d58a/scratchpad/brief/study/"
CME = ST + "amt_data/cme/"
def qc(name, df):
    t = pd.to_datetime(df.datetime)
    d = t.diff().dt.total_seconds()
    o, h, l, c = [df[k].values.astype(float) for k in "open high low close".split()]
    pc = np.r_[np.nan, c[:-1]]
    gap = np.abs(o - pc) / pc
    tr = np.maximum(h - l, np.maximum(np.abs(h - pc), np.abs(l - pc)))
    atr = pd.Series(tr).rolling(14, min_periods=5).mean().shift(1).values
    j = np.abs(o - pc) / atr
    big = np.nonzero(j > 4)[0]
    jb = 0
    for i in big:
        if i + 1 < len(o) and np.sign(o[i] - pc[i]) != np.sign(o[i + 1] - c[i]) and abs(o[i + 1] - c[i]) / atr[i] > 4:
            jb += 1
    print(f"{name}: n={len(df)} {t.iloc[0]}..{t.iloc[-1]} sorted={t.is_monotonic_increasing} dups={t.duplicated().sum()} "
          f"medstep={np.nanmedian(d):.0f}s neg_steps={(d<0).sum()} hl_bad={(h<l).sum()+(h<np.maximum(o,c)).sum()+(l>np.minimum(o,c)).sum()} "
          f"open-gap>4ATR={len(big)} jump-and-back={jb} zero-range={(h==l).mean():.3f}")
    if len(big):
        for i in big[:8]:
            print("   ", t.iloc[i], f"prevC={pc[i]:.2f} O={o[i]:.2f} gapATR={j[i]:.1f}")
for sym in ["NQ", "ES", "YM", "RTY", "GC", "CL"]:
    for tf in ["1h", "1min"]:
        f = glob.glob(CME + f"{sym}/{sym}_{tf}_*.csv")[0]
        qc(f"{sym}_{tf}", pd.read_csv(f))
qc("BTC_1h", pd.read_csv(ST + "classic_tools/btc_1h.csv"))
