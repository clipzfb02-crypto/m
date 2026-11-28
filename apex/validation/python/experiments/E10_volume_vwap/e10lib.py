"""E10_volume_vwap shared library: loaders, session tagging, features, statistics.

Standalone: apexdata.py / apexstats.py were not present when this ran (checked 2026-11-27).
Loader conventions reuse the study / E2 findings:
  * CME amt_data 1h and 1min files are UTC, bar-open labelled, unadjusted (rolls on the dates in ROLL_UTC).
  * NQ 1min 2022-2025 (i2 dataset) is ET, close-labelled -> shifted -1 min to open time; back-adjusted.
  * smt_data "tick" files are 1-second OHLCV bars in UTC (no aggressor side).
  * Binance BTCUSDC 1h JSON carries takerBuyBaseAssetVolume (true aggressor delta); btc_1h.csv is UTC spot.
Every bar-level frame has columns ts (naive local time: ET for CME, UTC for BTC), open, high, low, close, volume,
plus sess (session date; CME session = ET date of ts + 6h, i.e. Globex opens 18:00 ET).
"""
import glob
import json
import math
import numpy as np
import pandas as pd

SP = "/tmp/claude-0/-home-user-m/7ce60006-3639-59b1-8cd3-87355409d58a/scratchpad"
NQ1M = SP + "/i2/dl/data_src/data/Dataset_NQ_1min_2022_2025.csv"
CME = SP + "/brief/study/amt_data/cme/"
SMT = SP + "/brief/study/smt_data/cme/"
BTC_CSV = SP + "/brief/study/classic_tools/btc_1h.csv"
BTC_JSON = SP + "/brief/study/pine_eng_tools/pinets/tests/compatibility/_data/BTCUSDC-1h-1704067200000-1763683199000.json"
EURUSD = SP + "/brief/study/bias_data/EURUSD.csv"
OUT = "/home/user/m/apex/validation/python/experiments/E10_volume_vwap/out/"

# equity-index quarterly roll bars in the unadjusted CME 1h files (UTC), from E2's pre-registration A6
ROLL_UTC = ["2025-06-08 22:00", "2025-09-01 00:00", "2025-12-14 23:00", "2026-03-15 22:00"]
TICK = {"NQ": 0.25, "ES": 0.25, "YM": 1.0, "RTY": 0.1, "CL": 0.01, "GC": 0.1,
        "6E": 0.00005, "6B": 0.0001, "M6E": 0.0001, "M6B": 0.0001, "MBT": 5.0, "MET": 0.5}


# ----------------------------------------------------------------------------- loaders
def _to_et(t_utc):
    return t_utc.dt.tz_localize("UTC").dt.tz_convert("America/New_York").dt.tz_localize(None)


def add_sess(d, futures=True):
    if futures:
        d["sess"] = (d.ts + pd.Timedelta(hours=6)).dt.normalize()
    else:
        d["sess"] = d.ts.dt.normalize()
    return d


def load_nq1m():
    d = pd.read_csv(NQ1M)
    d.columns = ["ts", "open", "high", "low", "close", "volume", "vwap_rth", "vwap_eth"]
    d["ts"] = pd.to_datetime(d.ts, format="%m/%d/%Y %H:%M") - pd.Timedelta(minutes=1)
    d = d.sort_values("ts").drop_duplicates("ts").reset_index(drop=True)
    return add_sess(d, True)


def load_cme(sym, tf):
    """tf in {'1h','1min','5min'}; returns ET-local frame with a roll flag (bar is the first after a roll)."""
    f = glob.glob(CME + f"{sym}/{sym}_{tf}_*.csv")[0]
    d = pd.read_csv(f)
    t_utc = pd.to_datetime(d.datetime)
    d["ts"] = _to_et(t_utc)
    d["ts_utc"] = t_utc
    d = d[["ts", "ts_utc", "open", "high", "low", "close", "volume"]].sort_values("ts").drop_duplicates("ts")
    d = d.reset_index(drop=True)
    return add_sess(d, True)


def load_1s(sym):
    f = glob.glob(SMT + f"{sym}/{sym}_tick_*.csv")[0]
    d = pd.read_csv(f)
    d["ts_utc"] = pd.to_datetime(d.datetime)
    d["ts"] = _to_et(d.ts_utc)
    d = d[["ts", "ts_utc", "open", "high", "low", "close", "volume"]].sort_values("ts").reset_index(drop=True)
    return add_sess(d, True)


def load_smt_bars(sym, tf):
    f = glob.glob(SMT + f"{sym}/{sym}_{tf}_*.csv")[0]
    d = pd.read_csv(f)
    t_utc = pd.to_datetime(d.datetime)
    d["ts"] = _to_et(t_utc)
    d["ts_utc"] = t_utc
    d = d[["ts", "ts_utc", "open", "high", "low", "close", "volume"]].sort_values("ts").reset_index(drop=True)
    return add_sess(d, True)


def load_btc_csv():
    d = pd.read_csv(BTC_CSV)
    d["ts"] = pd.to_datetime(d.datetime)
    d = d[["ts", "open", "high", "low", "close", "volume"]].sort_values("ts").reset_index(drop=True)
    return add_sess(d, False)


def load_btc_binance():
    k = json.load(open(BTC_JSON))
    d = pd.DataFrame({
        "ts": pd.to_datetime(np.array([x["openTime"] for x in k], np.int64), unit="ms"),
        "open": [float(x["open"]) for x in k], "high": [float(x["high"]) for x in k],
        "low": [float(x["low"]) for x in k], "close": [float(x["close"]) for x in k],
        "volume": [float(x["volume"]) for x in k],
        "takerbuy": [float(x["takerBuyBaseAssetVolume"]) for x in k],
        "ntrades": [float(x.get("numberOfTrades", np.nan)) for x in k],
    })
    d["delta"] = 2 * d.takerbuy - d.volume
    return add_sess(d.sort_values("ts").reset_index(drop=True), False)


def load_eurusd_spot():
    d = pd.read_csv(EURUSD)
    d.columns = ["ts", "open", "high", "low", "close", "volume"]
    d["ts"] = pd.to_datetime(d.ts)
    return add_sess(d, False)


def resample(d, rule, extra=None):
    agg = {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
    if extra:
        agg.update(extra)
    r = d.set_index("ts").resample(rule, label="left", closed="left").agg(agg)
    r = r.dropna(subset=["open"]).reset_index()
    return r


# ----------------------------------------------------------------------------- features
def atr(d, n=14):
    h, l, c = d.high.values, d.low.values, d.close.values
    pc = np.r_[np.nan, c[:-1]]
    tr = np.nanmax(np.c_[h - l, np.abs(h - pc), np.abs(l - pc)], axis=1)
    tr[0] = h[0] - l[0]
    out = np.full(len(tr), np.nan)
    if len(tr) < n:
        return out
    out[n - 1] = tr[:n].mean()
    a = 1.0 / n
    for i in range(n, len(tr)):
        out[i] = out[i - 1] + a * (tr[i] - out[i - 1])
    return out


def tod_rvol(d, slot_col="slot", lookback_days=20, min_obs=10):
    """Relative volume vs the same clock slot: V_t / mean(V over the previous `lookback_days` sessions at the same slot).
    Uses only completed prior sessions (no same-bar or future data)."""
    v = d.volume.astype(float).values
    out = np.full(len(d), np.nan)
    for _, idx in d.groupby(slot_col).indices.items():
        vs = v[idx]
        s = pd.Series(vs)
        m = s.shift(1).rolling(lookback_days, min_periods=min_obs).mean().values
        out[idx] = vs / m
    return out


def rolling_pct(x, n=100, min_obs=50):
    """Percentile rank of x_t within x_{t-n+1..t} (inclusive of t), in [0,1]."""
    s = pd.Series(x)
    return s.rolling(n, min_periods=min_obs).apply(lambda w: (w[:-1] < w[-1]).mean() + 0.5 * (w[:-1] == w[-1]).mean(),
                                                   raw=True).values


# ----------------------------------------------------------------------------- statistics
def wilson(k, n, z=1.96):
    if n == 0:
        return (np.nan, np.nan, np.nan)
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return p, c - h, c + h


def block_boot_diff(y, g, blocks, n_boot=2000, seed=7, stat="mean"):
    """Bootstrap CI for mean(y | g==1) - mean(y | g==0), resampling whole blocks (days/weeks) with replacement."""
    rng = np.random.default_rng(seed)
    y = np.asarray(y, float); g = np.asarray(g, bool); blocks = np.asarray(blocks)
    ub, inv = np.unique(blocks, return_inverse=True)
    nb = len(ub)
    s1 = np.bincount(inv, weights=y * g, minlength=nb); n1 = np.bincount(inv, weights=g.astype(float), minlength=nb)
    s0 = np.bincount(inv, weights=y * ~g, minlength=nb); n0 = np.bincount(inv, weights=(~g).astype(float), minlength=nb)
    est = s1.sum() / max(n1.sum(), 1) - s0.sum() / max(n0.sum(), 1)
    bs = np.empty(n_boot)
    for b in range(n_boot):
        w = np.bincount(rng.integers(0, nb, nb), minlength=nb)
        a1, b1, a0, b0 = (w * s1).sum(), (w * n1).sum(), (w * s0).sum(), (w * n0).sum()
        bs[b] = (a1 / b1 if b1 else np.nan) - (a0 / b0 if b0 else np.nan)
    lo, hi = np.nanpercentile(bs, [2.5, 97.5])
    se = np.nanstd(bs)
    p = 2 * min((bs <= 0).mean(), (bs >= 0).mean())
    return est, lo, hi, se, max(p, 1.0 / n_boot)


def block_boot_mean(y, blocks, n_boot=2000, seed=7):
    rng = np.random.default_rng(seed)
    y = np.asarray(y, float); blocks = np.asarray(blocks)
    ub, inv = np.unique(blocks, return_inverse=True); nb = len(ub)
    s = np.bincount(inv, weights=y, minlength=nb); n = np.bincount(inv, minlength=nb).astype(float)
    est = s.sum() / n.sum()
    bs = np.empty(n_boot)
    for b in range(n_boot):
        w = np.bincount(rng.integers(0, nb, nb), minlength=nb)
        bs[b] = (w * s).sum() / (w * n).sum()
    lo, hi = np.percentile(bs, [2.5, 97.5])
    p = 2 * min((bs <= 0).mean(), (bs >= 0).mean())
    return est, lo, hi, np.std(bs), max(p, 1.0 / n_boot)


def holm(pvals):
    p = np.asarray(pvals, float); m = len(p); o = np.argsort(p)
    adj = np.empty(m); run = 0.0
    for k, i in enumerate(o):
        run = max(run, min(1.0, (m - k) * p[i])); adj[i] = run
    return adj


def bh(pvals):
    p = np.asarray(pvals, float); m = len(p); o = np.argsort(p)[::-1]
    adj = np.empty(m); run = 1.0
    for k, i in enumerate(o):
        rank = m - k
        run = min(run, p[i] * m / rank); adj[i] = run
    return adj


def fmt_ci(est, lo, hi, scale=100.0, nd=1):
    return f"{est*scale:+.{nd}f} [{lo*scale:+.{nd}f}, {hi*scale:+.{nd}f}]"
