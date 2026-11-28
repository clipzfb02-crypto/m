"""Data QC (format / timezone / gaps / zero volume / rolls). No outcome variables are computed here."""
import sys
import numpy as np
import pandas as pd
sys.path.insert(0, "/home/user/m/apex/validation/python/experiments/E10_volume_vwap")
import e10lib as L

out = []
def P(*a):
    s = " ".join(str(x) for x in a); print(s); out.append(s)

def summ(name, d, step):
    dt = d.ts.diff().dt.total_seconds()
    v = d.volume.values
    zr = (v == 0)
    # longest zero-volume run
    run = mx = 0
    for z in zr:
        run = run + 1 if z else 0; mx = max(mx, run)
    lr = np.log(d.close / d.close.shift()).abs()
    med = lr.median()
    P(f"{name:10s} n={len(d):8d} {d.ts.iloc[0]} -> {d.ts.iloc[-1]}  med_step={np.median(dt.dropna()):.0f}s "
      f"dup={d.ts.duplicated().sum()} zeroV={zr.mean():.4f} maxZeroRun={mx} gaps>{3*step}s={int((dt>3*step).sum())} "
      f"big|r|>20med={int((lr>20*med).sum())} vol_med={np.median(v):.0f}")

P("== NQ 1min 2022-2025 (ET, close-labelled -> shifted)")
nq = L.load_nq1m(); summ("NQ1m", nq, 60)
# which ET hours have rows (timezone sanity): halt should be 17:00 ET
h = nq.ts.dt.hour.value_counts().sort_index(); P("NQ1m rows by ET hour:", dict(h))
# VWAP column check: Vwap_ETH vs our session VWAP from hlc3
nq["tp"] = (nq.high + nq.low + nq.close) / 3
g = nq.groupby("sess")
nq["cv"] = g.volume.cumsum(); nq["cpv"] = (nq.tp * nq.volume).groupby(nq.sess).cumsum()
nq["vw"] = nq.cpv / nq.cv
m = nq.vwap_eth > 0
P("ETH VWAP: median |ours - file| (pts) =", float((nq.vw[m] - nq.vwap_eth[m]).abs().median()),
  " 99th pct =", float((nq.vw[m] - nq.vwap_eth[m]).abs().quantile(0.99)))
# rows per session
rps = nq.groupby("sess").size(); P("NQ1m sessions:", len(rps), " rows/session median", rps.median(), " min", rps.min())

P("\n== CME amt_data (UTC files -> ET)")
for sym in ["ES", "NQ", "YM", "RTY", "CL", "GC"]:
    for tf, step in [("1h", 3600), ("1min", 60)]:
        d = L.load_cme(sym, tf); summ(f"{sym}_{tf}", d, step)
        if tf == "1min":
            hh = d.ts.dt.hour.value_counts().sort_index()
            P(f"   {sym} 1min rows by ET hour (17 should be ~0):", int(hh.get(17, 0)), " hour18:", int(hh.get(18, 0)))
    # GC/1h interleave check: share of bars whose close jumps > 1.5% from previous close
d = L.load_cme("GC", "1h"); r = (d.close / d.close.shift() - 1).abs()
P("GC 1h: bars with |close/prev-1| > 1.5%:", int((r > 0.015).sum()), "of", len(d), "; volume<=50 bars:", int((d.volume <= 50).sum()))
d = L.load_cme("GC", "1min"); r = (d.close / d.close.shift() - 1).abs()
P("GC 1min: bars with |close/prev-1| > 1.0%:", int((r > 0.01).sum()), "of", len(d), "; volume<=2:", int((d.volume <= 2).sum()))
# roll jumps in 1min files: biggest |log ret| minutes
for sym in ["ES", "NQ", "YM", "RTY", "CL", "GC"]:
    d = L.load_cme(sym, "1min"); lr = np.log(d.close / d.close.shift()).abs()
    top = d.loc[lr.nlargest(3).index, ["ts", "close"]]
    P(f"   {sym} 1min top-3 |logret| minutes:", [(str(t), round(float(x), 5)) for t, x in zip(top.ts, lr.nlargest(3).values)])

P("\n== smt 1-second files (UTC -> ET)")
for sym in ["6E", "6B", "M6E", "M6B", "MBT", "MET"]:
    d = L.load_1s(sym); summ(f"{sym}_1s", d, 1)
    single = ((d.high == d.low)).mean()
    P(f"   {sym}: share of 1s bars with H==L (single price) {single:.3f}; seconds with trades per active hour median "
      f"{d.groupby(d.ts.dt.floor('h')).size().median():.0f}")
    hh = d.ts.dt.hour.value_counts().sort_index(); P(f"   rows ET hour 17: {int(hh.get(17,0))}  hour 18: {int(hh.get(18,0))}")

P("\n== BTC")
b = L.load_btc_csv(); summ("BTCcsv", b, 3600)
bb = L.load_btc_binance(); summ("BTCbin", bb, 3600)
P("   binance delta/V range:", float((bb.delta / bb.volume).min()), float((bb.delta / bb.volume).max()),
  " ntrades present:", bool(bb.ntrades.notna().any()))
ov = b.merge(bb, on="ts", suffixes=("_c", "_b"))
P("   overlap hours csv vs binance:", len(ov), ov.ts.min() if len(ov) else None, ov.ts.max() if len(ov) else None)
if len(ov):
    P("   close ratio median", float((ov.close_c / ov.close_b).median()), " corr log V", float(np.corrcoef(np.log1p(ov.volume_c), np.log1p(ov.volume_b))[0, 1]))
e = L.load_eurusd_spot(); summ("EURUSDspot", e, 3600)
open(L.OUT + "qc_data.txt", "w").write("\n".join(out) + "\n")

P("\n== interleave check: immediate full reversals of >0.5% moves (two contract months mixed)")
for sym in ["ES", "NQ", "YM", "RTY", "CL", "GC"]:
    for tf in ["1min", "1h"]:
        d = L.load_cme(sym, tf); r = np.log(d.close / d.close.shift()).values
        big = np.abs(r) > 0.005
        rev = big[1:-1] & big[2:] & (np.sign(r[1:-1]) != np.sign(r[2:])) & (np.abs(r[1:-1] + r[2:]) < 0.3 * np.abs(r[1:-1]))
        P(f"   {sym}_{tf}: big={int(big.sum())} immediate_full_reversals={int(rev.sum())}")
open(L.OUT + "qc_data.txt", "w").write("\n".join(out) + "\n")
