"""E9_momentum_factors: loaders, causal indicators, features, regimes, block bootstrap.

Conventions reused from the parallel tracks (not imported, to keep this track frozen):
  - E2_signals/e2data.py: NQ 1-min source shifted -1 min (close label -> open), session day = ET date of
    (bar open + 6 h), the roll-bar list for the CME equity-index files.
  - E4_regime_calibration/e4lib.py (itself from study/quant_regime_tools/rlib.py): Wilder RMA/ATR, ADX,
    Kaufman ER, VR-Hurst, Pine-style percent rank, the Hys-A / R5 hysteresis classifier.
Extensions here: volume kept (VWAP), Panama back-adjustment at roll bars, 5m/FX/BTC 4h/1d datasets.
All features at bar t use bars <= t only. Outcomes use bars t+1..t+H.
"""
import glob
import os

import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view as sw
from scipy.signal import lfilter
from scipy.stats import rankdata

SP = "/tmp/claude-0/-home-user-m/7ce60006-3639-59b1-8cd3-87355409d58a/scratchpad"
NQ1M = SP + "/i2/dl/data_src/data/Dataset_NQ_1min_2022_2025.csv"
CME = SP + "/brief/study/amt_data/cme/"
FX = SP + "/brief/study/smt_data/cme/"
BTC = SP + "/brief/study/classic_tools/btc_1h.csv"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
os.makedirs(OUT, exist_ok=True)

ROLL_UTC = ["2025-06-08 22:00", "2025-09-01 00:00", "2025-12-14 23:00", "2026-03-15 22:00"]
WARM = 600
W_NORM = 500
W_PCT = 500

DATASETS = ["NQ_L5m", "NQ_L15m", "NQ_L1h", "NQ_5m26", "ES_5m", "YM_5m", "RTY_5m",
            "ES_1h", "YM_1h", "RTY_1h", "6E_5m", "6B_5m", "BTC_1h", "BTC_4h", "BTC_1d"]
GROUP = {d: ("crypto" if d.startswith("BTC") else "fx" if d[:2] in ("6E", "6B") else "cme")
         for d in DATASETS}

DIR_FEATS = ["stack", "slope20", "slope50", "slope100", "slope200", "sep20_50", "sep50_200", "dist20",
             "dist200", "rsi", "macd", "macdh", "roc10", "roc40", "didiff", "tstat20", "tstat50", "vwapdev",
             "ser20", "acc20", "accroc", "dmacdh"]
UNS_FEATS = ["adx", "er20", "vr"]


# ------------------------------------------------------------------ loading
def _resample(d, rule):
    r = d.set_index("ts").resample(rule, label="left", closed="left").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}).dropna(subset=["open"])
    return r.reset_index()


def panama(d, roll_ts):
    """subtract the reopen gap at each roll bar from every earlier price (difference back-adjustment).
    d.ts_utc must exist. Returns adjusted frame and a list of (roll, gap)."""
    d = d.copy()
    log = []
    for r in sorted(pd.to_datetime(roll_ts), reverse=True):
        idx = np.where(d.ts_utc.values >= np.datetime64(r))[0]
        if len(idx) == 0 or idx[0] == 0:
            continue
        k = idx[0]
        if abs((d.ts_utc.iloc[k] - r).total_seconds()) > 3600:  # roll bar not present in this file
            continue
        gap = d.open.iloc[k] - d.close.iloc[k - 1]
        for c in ("open", "high", "low", "close"):
            d.loc[: k - 1, c] = d.loc[: k - 1, c] + gap
        log.append((str(r), float(gap)))
    return d, log


_NQ = {}


def _nq1m():
    if "d" not in _NQ:
        d = pd.read_csv(NQ1M, usecols=[0, 1, 2, 3, 4, 5])
        d.columns = ["ts", "open", "high", "low", "close", "volume"]
        d["ts"] = pd.to_datetime(d.ts, format="%m/%d/%Y %H:%M") - pd.Timedelta(minutes=1)
        _NQ["d"] = d
    return _NQ["d"]


def load(name):
    """returns DataFrame with ts_et (naive ET or UTC for BTC), open/high/low/close/volume, anchor, rth, meta"""
    info = {}
    if name.startswith("NQ_L"):
        tf = name[4:]
        d = _resample(_nq1m(), {"5m": "5min", "15m": "15min", "1h": "1h"}[tf])
        d["ts_et"] = d.ts
        futures = True
    elif name.startswith("BTC"):
        tf = name.split("_")[1]
        b = pd.read_csv(BTC)
        b["ts"] = pd.to_datetime(b.datetime)
        b = b[["ts", "open", "high", "low", "close", "volume"]]
        d = b if tf == "1h" else _resample(b, {"4h": "4h", "1d": "1D"}[tf])
        d["ts_et"] = d.ts  # UTC for BTC
        futures = False
    else:
        sym, tf = name.split("_")
        if tf == "5m26":
            sym, tf = "NQ", "5m"
        if sym in ("6E", "6B"):
            f = glob.glob(FX + f"{sym}/{sym}_5min_*.csv")[0]
            d = pd.read_csv(f)
        elif tf == "1h":
            d = pd.read_csv(glob.glob(CME + f"{sym}/{sym}_1h_*.csv")[0])
        else:
            d = pd.read_csv(glob.glob(CME + f"{sym}/{sym}_1min_*.csv")[0])
        d["ts_utc"] = pd.to_datetime(d.datetime)
        d = d.sort_values("ts_utc").drop_duplicates("ts_utc").reset_index(drop=True)
        if sym in ("ES", "YM", "RTY", "NQ"):
            d, info["panama"] = panama(d, ROLL_UTC)
        if tf == "5m" and sym not in ("6E", "6B"):
            d["ts"] = d.ts_utc
            d = _resample(d[["ts", "open", "high", "low", "close", "volume"]], "5min")
            d["ts_utc"] = d.ts
        d["ts_et"] = d.ts_utc.dt.tz_localize("UTC").dt.tz_convert("America/New_York").dt.tz_localize(None)
        futures = True
    d = d.reset_index(drop=True)
    if futures:
        d["anchor"] = (d.ts_et + pd.Timedelta(hours=6)).dt.normalize()
        mins = d.ts_et.dt.hour * 60 + d.ts_et.dt.minute
        d["rth"] = ((mins >= 570) & (mins < 960)).values
    else:
        if name == "BTC_1d":
            iso = d.ts_et.dt.isocalendar()
            d["anchor"] = iso.year.astype(str) + "-" + iso.week.astype(str)
        else:
            d["anchor"] = d.ts_et.dt.normalize()
        d["rth"] = np.zeros(len(d), bool)
    d["volume"] = d.volume.fillna(0.0).astype(float)
    info["name"] = name
    info["group"] = GROUP[name]
    info["bars_per_session"] = float(d.groupby("anchor").size().median()) if name != "BTC_1d" else 1.0
    return d, info


# ------------------------------------------------------------------ primitives
def ema(x, n):
    a = 2.0 / (n + 1)
    x = np.asarray(x, float)
    y, _ = lfilter([a], [1, -(1 - a)], x, zi=[(1 - a) * x[0]])
    return y


def rma(x, n):
    """Wilder RMA seeded with the SMA of the first n values (Pine ta.rma); x must be finite."""
    x = np.asarray(x, float)
    out = np.full(len(x), np.nan)
    if len(x) < n:
        return out
    s0 = x[:n].mean()
    out[n - 1] = s0
    a = 1.0 / n
    if len(x) > n:
        y, _ = lfilter([a], [1, -(1 - a)], x[n:], zi=[(1 - a) * s0])
        out[n:] = y
    return out


def true_range(H, L, C):
    pc = np.r_[np.nan, C[:-1]]
    tr = np.maximum(H - L, np.maximum(np.abs(H - pc), np.abs(L - pc)))
    tr[0] = H[0] - L[0]
    return tr


def lag(x, k):
    out = np.full(len(x), np.nan)
    out[k:] = x[:-k]
    return out


def rsi(C, n=14):
    ch = np.diff(C)
    g = np.maximum(ch, 0.0); l = np.maximum(-ch, 0.0)
    rg = rma(g, n); rl = rma(l, n)
    r = np.where(rl == 0, 100.0, 100.0 - 100.0 / (1.0 + rg / np.where(rl == 0, 1, rl)))
    return np.r_[np.nan, r]


def dmi(H, L, C, n=14):
    up = np.r_[0.0, np.diff(H)]; dn = np.r_[0.0, -np.diff(L)]
    pdm = np.where((up > dn) & (up > 0), up, 0.0)
    mdm = np.where((dn > up) & (dn > 0), dn, 0.0)
    atr_ = rma(true_range(H, L, C), n)
    pdi = 100 * rma(pdm, n) / atr_; mdi = 100 * rma(mdm, n) / atr_
    den = pdi + mdi
    dx = np.where(den > 0, 100 * np.abs(pdi - mdi) / np.where(den > 0, den, 1), 0.0)
    dx = np.nan_to_num(dx, nan=0.0)
    return pdi, mdi, rma(dx, n)


def reg_tstat(C, N):
    out = np.full(len(C), np.nan)
    x = np.arange(N) - (N - 1) / 2.0
    sxx = (x * x).sum()
    step = 50000
    for s in range(0, len(C) - N + 1, step):
        W = sw(C[s: s + step + N - 1], N)
        b = W @ x / sxx
        ss = ((W - W.mean(1, keepdims=True)) ** 2).sum(1)
        sse = np.maximum(ss - b * b * sxx, 1e-12 * np.maximum(ss, 1e-12))
        se = np.sqrt(sse / (N - 2) / sxx)
        out[s + N - 1: s + N - 1 + len(b)] = b / se
    return out


def ser(C, n=20):
    out = np.full(len(C), np.nan)
    d = np.abs(np.diff(C))
    cs = np.r_[0.0, np.cumsum(d)]
    t = np.arange(n, len(C))
    num = C[t] - C[t - n]
    den = cs[t] - cs[t - n]
    out[t] = np.where(den > 0, num / np.where(den > 0, den, 1), 0.0)
    return out


def vr_q(C, q=4, w=96):
    lr = np.log(C)
    r1 = np.r_[np.nan, np.diff(lr)]
    rq = np.full(len(C), np.nan); rq[q:] = lr[q:] - lr[:-q]
    v1 = np.full(len(C), np.nan); vq = np.full(len(C), np.nan)
    if len(C) > w + q:
        v1[w:] = sw(r1[1:], w).var(1)
        vq[w + q - 1:] = sw(rq[q:], w).var(1)[: len(C) - (w + q - 1)]
    return vq / (q * v1)


def pct_rank(x, W=W_PCT):
    n = len(x); out = np.full(n, np.nan)
    if n <= W:
        return out
    step = 20000
    for s in range(W, n, step):
        e = min(n, s + step)
        win = sw(x[s - W: e - 1], W)
        cur = x[s:e]
        ok = np.isfinite(cur) & np.isfinite(win).all(1)
        res = 100.0 * (win <= cur[:, None]).sum(1) / W
        res[~ok] = np.nan
        out[s:e] = res
    return out


def classify(p, lo_in, lo_out, hi_in, hi_out, dwell):
    """E4 hysteresis classifier: 0 = low (C / RANGE), 1 = mid, 2 = high (E / TREND), -1 undefined"""
    n = len(p); s = np.full(n, -1, dtype=int)
    st = -1; dw = 0
    for i in range(n):
        v = p[i]
        if not np.isfinite(v):
            s[i] = st; continue
        if st == -1:
            st = 0 if v <= lo_in else (2 if v >= hi_in else 1); dw = 0
        elif dw < dwell:
            dw += 1
        else:
            new = st
            if st == 1:
                if v <= lo_in: new = 0
                elif v >= hi_in: new = 2
            elif st == 0:
                if v >= hi_in: new = 2
                elif v > lo_out: new = 1
            else:
                if v <= lo_in: new = 0
                elif v < hi_out: new = 1
            if new != st:
                st = new; dw = 0
            else:
                dw += 1
        s[i] = st
    return s


def pivots(H, L, p):
    """confirmed pivots: arrays of pivot-bar indices (highs, lows); usable at i + p"""
    n = len(H)
    lh = pd.Series(H).shift(1).rolling(p).max().values
    rh = pd.Series(H[::-1]).shift(1).rolling(p).max().values[::-1]
    ll = pd.Series(L).shift(1).rolling(p).min().values
    rl = pd.Series(L[::-1]).shift(1).rolling(p).min().values[::-1]
    ph = np.where((H > lh) & (H >= rh))[0]
    pl = np.where((L < ll) & (L <= rl))[0]
    return ph, pl


def dol_feature(H, L, C, A, p=3, keep=5, cap=10.0):
    n = len(C)
    ph, pl = pivots(H, L, p)
    conf_h = {i + p: i for i in ph}; conf_l = {i + p: i for i in pl}
    highs = []; lows = []
    out = np.full(n, np.nan)
    for t in range(n):
        if highs:
            highs = [lv for lv in highs if H[t] < lv]
        if lows:
            lows = [lv for lv in lows if L[t] > lv]
        if t in conf_h:
            highs.append(H[conf_h[t]])
        if t in conf_l:
            lows.append(L[conf_l[t]])
        a = A[t]
        if not np.isfinite(a) or a <= 0:
            continue
        cu = highs[-keep:]; cd = lows[-keep:]
        du = min(cap, (min(cu) - C[t]) / a) if cu else cap
        dd = min(cap, (C[t] - max(cd)) / a) if cd else cap
        du = max(du, 0.0); dd = max(dd, 0.0)
        out[t] = (dd - du) / (dd + du) if (dd + du) > 0 else 0.0
    return out


# ------------------------------------------------------------------ features
def features(d):
    O = d.open.values.astype(float); H = d.high.values.astype(float)
    L = d.low.values.astype(float); C = d.close.values.astype(float); V = d.volume.values.astype(float)
    A = rma(true_range(H, L, C), 14)
    f = {"A": A}
    E = {k: ema(C, k) for k in (12, 20, 26, 50, 100, 200)}
    sg = np.sign
    f["stack"] = sg(C - E[20]) + sg(E[20] - E[50]) + sg(E[50] - E[100]) + sg(E[100] - E[200])
    for k in (20, 50, 100, 200):
        f[f"slope{k}"] = (E[k] - lag(E[k], 5)) / (5 * A)
    f["sep20_50"] = (E[20] - E[50]) / A
    f["sep50_200"] = (E[50] - E[200]) / A
    f["dist20"] = (C - E[20]) / A
    f["dist200"] = (C - E[200]) / A
    f["rsi_raw"] = rsi(C, 14)
    f["rsi"] = f["rsi_raw"] - 50.0
    macd = E[12] - E[26]
    sig = ema(macd, 9)
    f["macd"] = macd / A
    f["macdh"] = (macd - sig) / A
    f["roc10"] = (C - lag(C, 10)) / A
    f["roc40"] = (C - lag(C, 40)) / A
    pdi, mdi, adx = dmi(H, L, C, 14)
    f["didiff"] = pdi - mdi
    f["adx"] = adx
    f["tstat20"] = reg_tstat(C, 20)
    f["tstat50"] = reg_tstat(C, 50)
    hlc3 = (H + L + C) / 3.0
    g = d.anchor.values
    df = pd.DataFrame({"g": g, "pv": hlc3 * V, "v": V, "p": hlc3, "one": 1.0})
    cpv = df.groupby("g", sort=False).pv.cumsum().values
    cv = df.groupby("g", sort=False).v.cumsum().values
    cp = df.groupby("g", sort=False).p.cumsum().values
    cn = df.groupby("g", sort=False).one.cumsum().values
    vwap = np.where(cv > 0, cpv / np.where(cv > 0, cv, 1), cp / cn)
    f["vwap_eqw_frac"] = float(np.mean(cv <= 0))
    f["vwapdev"] = (C - vwap) / A
    f["ser20"] = ser(C, 20)
    f["er20"] = np.abs(f["ser20"])
    f["acc20"] = f["slope20"] - lag(f["slope20"], 5)
    f["accroc"] = f["roc10"] - lag(f["roc10"], 10)
    f["dmacdh"] = f["macdh"] - lag(f["macdh"], 5)
    f["vr"] = vr_q(C, 4, 96)
    f["b1"] = sg(E[20] - E[50])
    f["dol"] = dol_feature(H, L, C, A, 3)
    # regimes (E4 definitions)
    f["vol_reg"] = classify(pct_rank(A), 20, 30, 80, 70, 5)
    f["tr_reg"] = classify(pct_rank(f["er20"]), 30, 40, 70, 60, 5)
    f["rth"] = d.rth.values
    f["sgn20"] = sg(C - lag(C, 20))
    for k in ("O", "H", "L", "C"):
        f["px_" + k] = locals()[k]
    return f


def norm(x, W=W_NORM):
    """n(x) = clip(x / sqrt(SMA(x^2, W)), -3, 3), causal"""
    s = pd.Series(np.asarray(x, float) ** 2).rolling(W, min_periods=W).mean().values
    z = x / np.sqrt(np.where(s > 0, s, np.nan))
    return np.clip(z, -3, 3)


def outcome(f, H, entry="close"):
    C = f["px_C"]; A = f["A"]
    fc = np.full(len(C), np.nan); fc[: len(C) - H] = C[H:]
    if entry == "close":
        ref = C
    else:
        ref = np.full(len(C), np.nan); ref[:-1] = f["px_O"][1:]
    return (fc - ref) / A


def split(n, H, frac=0.6, warm=WARM):
    cut = warm + int((n - warm) * frac)
    return np.arange(warm, cut - H), np.arange(cut, n - H), cut


# ------------------------------------------------------------------ bootstrap IC
class BlockBoot:
    """non-overlapping contiguous blocks of length B over a segment; shared resample counts"""

    def __init__(self, n, B, reps=2000, seed=0):
        self.n = n; self.B = max(1, int(B))
        self.blk = np.arange(n) // self.B
        self.nb = int(self.blk.max()) + 1
        rng = np.random.default_rng(seed)
        idx = rng.integers(0, self.nb, size=(reps, self.nb))
        cnt = np.zeros((reps, self.nb))
        np.add.at(cnt, (np.repeat(np.arange(reps), self.nb), idx.ravel()), 1.0)
        self.cnt = cnt

    def _stats(self, rx, ry, mask=None):
        b = self.blk if mask is None else self.blk[mask]
        S = np.zeros((self.nb, 6))
        for j, v in enumerate((np.ones_like(rx), rx, ry, rx * rx, ry * ry, rx * ry)):
            S[:, j] = np.bincount(b, weights=v, minlength=self.nb)
        return S

    @staticmethod
    def _corr(T):
        n, sx, sy, sxx, syy, sxy = [T[..., j] for j in range(6)]
        cov = sxy - sx * sy / n
        vx = sxx - sx * sx / n; vy = syy - sy * sy / n
        return cov / np.sqrt(np.maximum(vx * vy, 1e-300))

    def ic(self, x, y, mask=None):
        """Spearman IC (ranks within the (masked) segment) + bootstrap distribution"""
        xs = x if mask is None else x[mask]
        ys = y if mask is None else y[mask]
        if len(xs) < 30 or np.nanstd(xs) == 0:
            return np.nan, np.full(self.cnt.shape[0], np.nan)
        rx = rankdata(xs); ry = rankdata(ys)
        S = self._stats(rx, ry, mask)
        est = float(self._corr(S.sum(0)))
        dist = self._corr(self.cnt @ S)
        return est, dist


def summarize(est, dist):
    dist = dist[np.isfinite(dist)]
    if not np.isfinite(est) or len(dist) < 100:
        return dict(ic=est, lo=np.nan, hi=np.nan, p=np.nan)
    lo, hi = np.percentile(dist, [2.5, 97.5])
    p = 2 * min(np.mean(dist <= 0), np.mean(dist >= 0))
    p = max(p, 1.0 / len(dist))
    return dict(ic=est, lo=float(lo), hi=float(hi), p=float(min(p, 1.0)))


def wilson(k, n, z=1.96):
    if n == 0:
        return (np.nan, np.nan, np.nan)
    ph = k / n; den = 1 + z * z / n
    c = (ph + z * z / (2 * n)) / den
    h = z * np.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / den
    return ph, c - h, c + h


def bh(p, q=0.10):
    p = np.asarray(p, float); ok = np.isfinite(p)
    rej = np.zeros(len(p), bool)
    pv = p[ok]; m = len(pv)
    if m == 0:
        return rej
    o = np.argsort(pv); th = q * (np.arange(1, m + 1)) / m
    passed = pv[o] <= th
    k = np.where(passed)[0].max() + 1 if passed.any() else 0
    r = np.zeros(m, bool); r[o[:k]] = True
    rej[np.where(ok)[0]] = r
    return rej


def holm(p, alpha=0.05):
    p = np.asarray(p, float); m = np.isfinite(p).sum()
    o = np.argsort(np.where(np.isfinite(p), p, np.inf))
    rej = np.zeros(len(p), bool)
    for r, i in enumerate(o):
        if not np.isfinite(p[i]):
            break
        if p[i] <= alpha / (m - r):
            rej[i] = True
        else:
            break
    return rej
