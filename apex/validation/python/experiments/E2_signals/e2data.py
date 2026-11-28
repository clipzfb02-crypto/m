"""E2_signals data loaders. Standalone (apexdata.py was not ready when this ran).

Every loader returns a DataFrame indexed 0..n-1 with columns:
  ts (naive local bar-open time), open, high, low, close, sess (session date),
  guard (bool: bar is a roll / data-break bar; trades spanning it are dropped),
  gap_days (float: time since previous bar in days)
plus a metadata dict: name, tf, cost_side (price units, or fraction of price if pct=True), pct, ann, tick.
"""
import glob
import os
import numpy as np
import pandas as pd

# 1 = pre-registered guard (primary). 2 = repaired guard for the CME equity 1h files (deviation D2, reported beside v1).
GUARD_VERSION = int(os.environ.get("E2_GUARD", "1"))

SP = "/tmp/claude-0/-home-user-m/7ce60006-3639-59b1-8cd3-87355409d58a/scratchpad"
NQ1M = SP + "/i2/dl/data_src/data/Dataset_NQ_1min_2022_2025.csv"
CME = SP + "/brief/study/amt_data/cme/"
BTC = SP + "/brief/study/classic_tools/btc_1h.csv"

# roll bars for the CME equity-index 1h files (UTC), see the pre-registration A6
ROLL_UTC = ["2025-06-08 22:00", "2025-09-01 00:00", "2025-12-14 23:00", "2026-03-15 22:00"]

COST = {  # per side, price units; slip_ticks=1 base
    "NQ": dict(tick=0.25, comm_pts=2.5 / 20.0),
    "ES": dict(tick=0.25, comm_pts=2.5 / 50.0),
    "YM": dict(tick=1.0, comm_pts=2.5 / 5.0),
    "RTY": dict(tick=0.1, comm_pts=2.5 / 50.0),
    "CL": dict(tick=0.01, comm_pts=2.5 / 1000.0),
}


def _resample(d, rule):
    r = d.set_index("ts").resample(rule, label="left", closed="left").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
    return r.reset_index()


def _finish(d, name, tf, futures, guard_mask=None):
    d = d.reset_index(drop=True)
    if futures:
        d["sess"] = (d.ts + pd.Timedelta(hours=6)).dt.normalize()
    else:
        d["sess"] = d.ts.dt.normalize()
    d["gap_days"] = d.ts.diff().dt.total_seconds().fillna(0) / 86400.0
    d["guard"] = False if guard_mask is None else guard_mask
    return d


def meta_for(sym, tf, slip_ticks=1.0):
    if sym == "BTC":
        return dict(name=f"BTC_{tf}", sym=sym, tf=tf, pct=True, cost_side=0.0004 + 0.0001 * slip_ticks,
                    ann=np.sqrt(365.0), tick=0.01)
    c = COST[sym]
    return dict(name=f"{sym}_{tf}", sym=sym, tf=tf, pct=False, cost_side=c["tick"] * slip_ticks + c["comm_pts"],
                ann=np.sqrt(252.0), tick=c["tick"])


_NQ1M_CACHE = {}


def load_nq(tf):
    if "d" not in _NQ1M_CACHE:
        d = pd.read_csv(NQ1M, usecols=[0, 1, 2, 3, 4])
        d.columns = ["ts", "open", "high", "low", "close"]
        d["ts"] = pd.to_datetime(d.ts, format="%m/%d/%Y %H:%M") - pd.Timedelta(minutes=1)  # close-label -> open
        _NQ1M_CACHE["d"] = d
    d = _NQ1M_CACHE["d"]
    rule = {"5m": "5min", "15m": "15min", "1h": "1h"}[tf]
    r = _resample(d, rule)
    return _finish(r, f"NQ_{tf}", tf, True), meta_for("NQ", tf)


def guard_v2_extra(d, t_utc):
    """DEVIATION (added on resume, 2026-11-28, see report section D): objective detector for the defects found
    in the CME equity-index 1h files after the pre-registration:
      (a) 'in-out' bars: |O_t - C_{t-1}| and |O_{t+1} - C_t| both > 2.5 median bar ranges with opposite signs.
          These are bars from the other contract month interleaved into the series (YM/RTY around the
          2025-06 and 2025-09 rolls, one ES bar 2025-09-03). The bar and the next bar are marked, and every bar
          from a roll bar to the last in-out bar within 14 days after it (+1 bar) is marked.
      (b) stale bars: range < 0.15 median range and |O_{t+1} - C_t| > 2 median ranges (e.g. 2025-05-01 11:00 ET).
          The bar and the next bar are marked.
    Returns a boolean mask to OR with the pre-registered guard."""
    o, h, l, c = (d[k].values.astype(float) for k in ("open", "high", "low", "close"))
    med = np.median(h - l)
    g1 = np.r_[np.nan, o[1:] - c[:-1]] / med
    g2 = np.r_[o[1:] - c[:-1], np.nan] / med
    inout = (np.abs(g1) > 2.5) & (np.abs(g2) > 2.5) & (np.sign(g1) != np.sign(g2))
    stale = ((h - l) < 0.15 * med) & (np.abs(np.nan_to_num(g2)) > 2.0)
    m = inout | stale
    m = m | np.r_[False, m[:-1]]
    tu = t_utc.values
    for r in pd.to_datetime(ROLL_UTC).values:
        idx = np.flatnonzero(inout & (tu >= r) & (tu <= r + np.timedelta64(14, "D")))
        if len(idx):
            a = int(np.searchsorted(tu, r))
            m[a:idx.max() + 2] = True
    # (c) cross-instrument check against the clean, back-adjusted NQ 1m series (period it covers only):
    #     on a continuous hourly bar (previous bar exactly 1 h earlier, i.e. not a session reopen) the open gap,
    #     after removing beta * NQ open gap, exceeds 60 robust sigma. Catches the unguarded ES roll
    #     2025-05-21 20:00 ET and the ES open discontinuity 2025-04-04 09:00 ET.
    nq, _ = load_nq("1h")
    ng = pd.Series(nq.open.values / np.r_[np.nan, nq.close.values[:-1]] - 1.0, index=nq.ts.values)
    gg = o / np.r_[np.nan, c[:-1]] - 1.0
    gn = ng.reindex(d.ts.values).values
    cont = np.r_[False, np.diff(d.ts.values).astype("timedelta64[m]").astype(float) == 60.0]
    ok = np.isfinite(gn) & np.isfinite(gg) & cont & ~m
    if ok.sum() > 500:
        beta = np.polyfit(gn[ok], gg[ok], 1)[0]
        res = gg - beta * gn
        sd = 1.4826 * np.nanmedian(np.abs(res[ok]))
        x = ok & (np.abs(res) > 60 * sd)
        m = m | x
    return m


def load_cme1h(sym):
    f = glob.glob(CME + f"{sym}/{sym}_1h_*.csv")[0]
    d = pd.read_csv(f)
    t_utc = pd.to_datetime(d.datetime)
    d["ts"] = t_utc.dt.tz_localize("UTC").dt.tz_convert("America/New_York").dt.tz_localize(None)
    d = d[["ts", "open", "high", "low", "close"]].copy()
    guard = np.zeros(len(d), bool)
    if sym in ("ES", "YM", "RTY", "NQ"):
        rset = set(pd.to_datetime(ROLL_UTC))
        guard = t_utc.isin(rset).values
        if GUARD_VERSION == 2:
            guard = guard | guard_v2_extra(d, t_utc)
    elif sym == "CL":
        g = np.log(d.open / d.close.shift()).values
        oc = np.log(d.close / d.open).values
        sig = 1.4826 * np.nanmedian(np.abs(oc))
        hole = (t_utc.diff().dt.total_seconds() / 3600.0).values > 50.0
        guard = (np.abs(np.nan_to_num(g)) > 8 * sig) | hole
    out = _finish(d, f"{sym}_1h", "1h", True, guard)
    return out, meta_for(sym, "1h")


def load_btc():
    d = pd.read_csv(BTC)
    d["ts"] = pd.to_datetime(d.datetime)
    d = d[["ts", "open", "high", "low", "close"]].copy()
    return _finish(d, "BTC_1h", "1h", False), meta_for("BTC", "1h")


def load(name):
    if name.startswith("NQ_"):
        return load_nq(name.split("_")[1])
    if name == "BTC_1h":
        return load_btc()
    return load_cme1h(name.split("_")[0])


DATASETS = ["NQ_5m", "NQ_15m", "NQ_1h", "ES_1h", "YM_1h", "RTY_1h", "CL_1h", "BTC_1h"]
