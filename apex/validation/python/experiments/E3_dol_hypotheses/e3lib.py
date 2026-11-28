# E3_dol_hypotheses shared library: loaders, levels, outcomes, statistics.
# No lookahead: every level carries `avail` = the bar index at whose CLOSE it is first known.
# Outcomes are measured on bars strictly after the decision bar.
import glob, math
import numpy as np, pandas as pd

SP = "/tmp/claude-0/-home-user-m/7ce60006-3639-59b1-8cd3-87355409d58a/scratchpad"
ST = SP + "/brief/study/"
CME = ST + "amt_data/cme/"
NQL_FILE = SP + "/i2/dl/data_src/data/Dataset_NQ_1min_2022_2025.csv"
BTC_FILE = ST + "classic_tools/btc_1h.csv"
OUT = "/home/user/m/apex/validation/python/experiments/E3_dol_hypotheses/out/"

TICK = {"NQ": 0.25, "NQL": 0.25, "ES": 0.25, "YM": 1.0, "RTY": 0.1, "CL": 0.01, "GC": 0.1, "BTC": 0.01}
DATASETS_1H = ["NQ", "ES", "YM", "RTY", "CL", "BTC"]
DATASETS_5M = ["NQL", "NQ", "ES", "YM", "RTY", "CL"]

# kinds
SW, SES, PD, PW, FVG = 0, 1, 2, 3, 4
KNAME = {SW: "SW", SES: "SES", PD: "PD", PW: "PW", FVG: "FVG"}


# ----------------------------------------------------------------------------- loading
def _finish(df, btc=False, gap_hours=80.0):
    """df: columns t (naive ET bar-open time), open, high, low, close, volume. Adds seg/day/week/session."""
    df = df.sort_values("t").drop_duplicates("t").reset_index(drop=True)
    step = df.t.diff().dt.total_seconds().fillna(0) / 3600.0
    df["seg"] = (step > gap_hours).cumsum().astype(int)
    if btc:
        tu = df["tu"]
        df["dayk"] = tu.dt.floor("D")
        # trading week starts Monday 00:00 UTC
        df["weekk"] = (tu.dt.floor("D") - pd.to_timedelta(tu.dt.weekday, unit="D"))
    else:
        g = df.t + pd.Timedelta(hours=6)  # Globex day starts 18:00 ET
        df["dayk"] = g.dt.floor("D")
        df["weekk"] = (g.dt.floor("D") - pd.to_timedelta(g.dt.weekday, unit="D"))
    df["day"] = pd.factorize(df["dayk"])[0]
    df["week"] = pd.factorize(df["weekk"])[0]
    hr = df.t.dt.hour + df.t.dt.minute / 60.0
    # sessions on the ET clock by bar-open time: 0 ASIA [18,02), 1 LON [02,08), 2 NY [08,17), NY also takes 17-18 (BTC)
    s = np.where((hr >= 18) | (hr < 2), 0, np.where(hr < 8, 1, 2))
    df["sess"] = s
    # session instance id: increments when the session code changes
    df["sessid"] = (pd.Series(s).diff().fillna(0) != 0).cumsum().values
    return df


def load_1h(name):
    if name == "BTC":
        d = pd.read_csv(BTC_FILE)
        tu = pd.to_datetime(d.datetime)
        d["tu"] = tu
        d["t"] = tu.dt.tz_localize("UTC").dt.tz_convert("America/New_York").dt.tz_localize(None)
        return _finish(d[["t", "tu", "open", "high", "low", "close", "volume"]], btc=True, gap_hours=3.0)
    f = glob.glob(CME + f"{name}/{name}_1h_*.csv")[0]
    d = pd.read_csv(f)
    d["t"] = pd.to_datetime(d.datetime).dt.tz_localize("UTC").dt.tz_convert("America/New_York").dt.tz_localize(None)
    return _finish(d[["t", "open", "high", "low", "close", "volume"]])


def _resample(d, rule):
    d = d.set_index("t")
    r = d.resample(rule, label="left", closed="left").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}).dropna()
    return r.reset_index()


def load_5m(name):
    if name == "NQL":
        d = pd.read_csv(NQL_FILE)
        # stamps are bar END times in ET (first bar of a session is 18:01): shift to bar-open time
        d["t"] = pd.to_datetime(d["timestamp ET"], format="%m/%d/%Y %H:%M") - pd.Timedelta(minutes=1)
        d = d[["t", "open", "high", "low", "close", "volume"]]
    else:
        f = glob.glob(CME + f"{name}/{name}_1min_*.csv")[0]
        d = pd.read_csv(f)
        d["t"] = pd.to_datetime(d.datetime).dt.tz_localize("UTC").dt.tz_convert("America/New_York").dt.tz_localize(None)
        d = d[["t", "open", "high", "low", "close", "volume"]]
    return _finish(_resample(d, "5min"))


def load(name, tf):
    return load_1h(name) if tf == "1h" else load_5m(name)


# ----------------------------------------------------------------------------- indicators
def rma(x, n):
    out = np.full(len(x), np.nan)
    if len(x) < n:
        return out
    out[n - 1] = np.nanmean(x[:n])
    a = 1.0 / n
    for i in range(n, len(x)):
        out[i] = out[i - 1] + a * (x[i] - out[i - 1])
    return out


def true_range(h, l, c):
    pc = np.r_[c[0], c[:-1]]
    return np.maximum(h - l, np.maximum(np.abs(h - pc), np.abs(l - pc)))


def add_basic(df):
    h, l, c = df.high.values, df.low.values, df.close.values
    tr = true_range(h, l, c)
    df["atr"] = rma(tr, 14)
    df["atr100"] = rma(tr, 100)
    df["lvr"] = np.log(df.atr / df.atr100)
    return df


def fwd_extremes(h, l, seg, H):
    """max(high[t+1..t+H]), min(low[t+1..t+H]); NaN if the window leaves the segment or the data."""
    n = len(h)
    mx = pd.Series(h[::-1]).rolling(H, min_periods=H).max().values[::-1]  # window [t, t+H)
    mn = pd.Series(l[::-1]).rolling(H, min_periods=H).min().values[::-1]
    fmx = np.full(n, np.nan); fmn = np.full(n, np.nan)
    fmx[:-1] = mx[1:]; fmn[:-1] = mn[1:]
    ok = np.zeros(n, bool)
    idx = np.arange(n)
    j = idx + H
    valid = j < n
    ok[valid] = seg[j[valid]] == seg[idx[valid]]
    fmx[~ok] = np.nan; fmn[~ok] = np.nan
    return fmx, fmn


# ----------------------------------------------------------------------------- levels
def pivots(h, l, L=5, R=5):
    """Confirmed pivots. Returns lists of (pivot_bar, confirm_bar, price, side)."""
    n = len(h)
    out = []
    w = L + R + 1
    hs = pd.Series(h); ls = pd.Series(l)
    # centred rolling max/min over [i-L, i+R]
    cmx = hs.rolling(w).max().shift(-R).values
    cmn = ls.rolling(w).min().shift(-R).values
    for i in range(L, n - R):
        if h[i] == cmx[i] and h[i] > h[i - L:i].max() if L > 0 else True:
            out.append((i, i + R, h[i], 1))
        if l[i] == cmn[i] and l[i] < l[i - L:i].min() if L > 0 else True:
            out.append((i, i + R, l[i], -1))
    return out


def build_levels(df, piv_L=5, piv_R=5, sw_life=500, fvg_life=500, fvg_min_atr=0.10, ses_days=2):
    """Return DataFrame of levels: kind, side, price, far (FVG far edge), avail, exp, origin, seg."""
    h, l, c, o = df.high.values, df.low.values, df.close.values, df.open.values
    atr = df.atr.values
    n = len(df)
    seg = df.seg.values
    rows = []
    # swings
    for (i, cb, p, s) in pivots(h, l, piv_L, piv_R):
        if seg[i] != seg[cb] if cb < n else True:
            continue
        rows.append((SW, s, p, np.nan, cb, min(n, cb + sw_life), i))
    # periods: day / week / session instances
    for kind, key, life in ((PD, "day", 1), (PW, "week", 1), (SES, "sessid", ses_days)):
        k = df[key].values
        last_idx = np.r_[np.nonzero(np.diff(k))[0], n - 1]  # last bar of each instance
        first_idx = np.r_[0, last_idx[:-1] + 1]
        days = df.day.values
        for a, b in zip(first_idx, last_idx):
            if a == 0:
                continue  # first instance may be partial
            if b == n - 1:
                continue  # incomplete last instance
            hi = h[a:b + 1].max(); lo = l[a:b + 1].min()
            if kind in (PD, PW):
                # valid during the next instance only
                nxt = np.nonzero(k[b + 1:] != k[b + 1])[0]
                exp = b + 1 + (nxt[0] if len(nxt) else n - b - 1)
            else:
                # session level valid for `ses_days` trading days after the session ends
                d_end = days[b] + ses_days
                nx = np.nonzero(days[b + 1:] > d_end)[0]
                exp = b + 1 + (nx[0] if len(nx) else n - b - 1)
            # partial-instance guard: a period that spans a data hole is skipped
            if seg[a] != seg[b] or (b + 1 < n and seg[b + 1] != seg[b]):
                continue
            rows.append((kind, 1, hi, np.nan, b, exp, a))
            rows.append((kind, -1, lo, np.nan, b, exp, a))
    # FVGs (3-bar). Bullish FVG: low[t] > high[t-2] -> zone below later price, a DOWNSIDE target (side -1),
    # near edge = low[t] (top), far edge = high[t-2]. Bearish mirror: side +1, near = high[t], far = low[t-2].
    for t in range(2, n):
        if seg[t] != seg[t - 2] or not np.isfinite(atr[t]):
            continue
        if l[t] > h[t - 2] and (l[t] - h[t - 2]) >= fvg_min_atr * atr[t]:
            rows.append((FVG, -1, l[t], h[t - 2], t, min(n, t + fvg_life), t - 1))
        if h[t] < l[t - 2] and (l[t - 2] - h[t]) >= fvg_min_atr * atr[t]:
            rows.append((FVG, 1, h[t], l[t - 2], t, min(n, t + fvg_life), t - 1))
    lv = pd.DataFrame(rows, columns=["kind", "side", "price", "far", "avail", "exp", "origin"])
    lv = lv.sort_values(["avail", "kind"]).reset_index(drop=True)
    # cap exp at segment end
    seg_end = pd.Series(np.arange(n)).groupby(seg).max().reindex(seg).values  # last index in each bar's segment
    lv["exp"] = np.minimum(lv.exp.values, seg_end[lv.avail.values] + 1)
    return lv


def level_events(df, lv, touch_eps=0.10, touch_gap=3):
    """For each level: end = first bar > avail that trades through (strict) [pools] / touches near edge [FVG].
    For FVG also fill = first bar that trades to the far edge. touches: episode starts within eps*ATR."""
    h, l = df.high.values, df.low.values
    atr = df.atr.values
    n = len(df)
    end = np.full(len(lv), n, dtype=np.int64)
    fill = np.full(len(lv), n, dtype=np.int64)
    touches = []
    K, S, P, F, A, E = (lv[c].values for c in ["kind", "side", "price", "far", "avail", "exp"])
    for j in range(len(lv)):
        a, e = A[j] + 1, E[j]
        if a >= e:
            end[j] = a; fill[j] = a; touches.append(np.empty(0, np.int64)); continue
        if K[j] == FVG:
            hit = (h[a:e] >= P[j]) if S[j] > 0 else (l[a:e] <= P[j])
            w = np.flatnonzero(hit)
            end[j] = a + w[0] if len(w) else e if e < n else n
            fh = (h[a:e] >= F[j]) if S[j] > 0 else (l[a:e] <= F[j])
            w2 = np.flatnonzero(fh)
            fill[j] = a + w2[0] if len(w2) else (e if e < n else n)
            touches.append(np.empty(0, np.int64))
        else:
            hit = (h[a:e] > P[j]) if S[j] > 0 else (l[a:e] < P[j])
            w = np.flatnonzero(hit)
            stop = a + w[0] if len(w) else e
            end[j] = a + w[0] if len(w) else n  # n = never traded within life (expired)
            # touch episodes before the trade-through
            if stop > a:
                band = touch_eps * atr[a:stop]
                near = (h[a:stop] >= P[j] - band) if S[j] > 0 else (l[a:stop] <= P[j] + band)
                idx = np.flatnonzero(near)
                if len(idx):
                    starts = idx[np.r_[True, np.diff(idx) > touch_gap]] + a
                else:
                    starts = np.empty(0, np.int64)
            else:
                starts = np.empty(0, np.int64)
            touches.append(starts)
    lv = lv.copy()
    lv["end"] = end
    lv["fill"] = fill
    lv["traded"] = (end < lv.exp.values) & (end < n)
    return lv, touches


# ----------------------------------------------------------------------------- HTF structure bias
def htf_bias(df, key, L=2, R=2):
    """Structure bias from HTF bars built by grouping chart bars on `key` (e.g. 'day', or an hour key).
    bias = +1 after an HTF close above the last confirmed HTF swing high, -1 after a close below the last
    confirmed swing low. Returned per chart bar = bias as of the last HTF bar COMPLETED BEFORE the HTF bar
    that contains the chart bar (Pine: request.security(..., expr[1], lookahead_on))."""
    k = df[key].values
    g = df.groupby(key, sort=False)
    hh = g.high.max().values; ll = g.low.min().values; cc = g.close.last().values
    ee = None
    m = len(hh)
    bias = np.zeros(m)
    ema = np.full(m, np.nan)
    a = 2.0 / 21
    for i in range(m):
        ema[i] = cc[i] if i == 0 else ema[i - 1] + a * (cc[i] - ema[i - 1])
    last_sh = np.nan; last_sl = np.nan; b = 0
    for i in range(m):
        # pivot at i-R confirmed at i
        p = i - R
        if p - L >= 0:
            if hh[p] == hh[p - L:i + 1].max() and hh[p] > hh[p - L:p].max():
                last_sh = hh[p]
            if ll[p] == ll[p - L:i + 1].min() and ll[p] < ll[p - L:p].min():
                last_sl = ll[p]
        if np.isfinite(last_sh) and cc[i] > last_sh:
            b = 1
        elif np.isfinite(last_sl) and cc[i] < last_sl:
            b = -1
        bias[i] = b
    trend = np.sign(cc - ema)
    # map: chart bar in HTF bar j sees HTF bar j-1
    codes = pd.factorize(k)[0]
    prev = codes - 1
    bias_c = np.where(prev >= 0, bias[np.maximum(prev, 0)], 0.0)
    trend_c = np.where(prev >= 1, trend[np.maximum(prev, 0)], 0.0)
    return bias_c, trend_c


# ----------------------------------------------------------------------------- statistics
def wilson(k, n, z=1.96):
    if n == 0:
        return (np.nan, np.nan)
    p = k / n
    den = 1 + z * z / n
    cen = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (cen - half, cen + half)


def block_boot_mean(vals, blocks, nrep=2000, seed=0, block_len=1):
    """Moving-block bootstrap over ordered block ids (e.g. trading days) of the mean of `vals`.
    Returns (mean, lo, hi, se)."""
    vals = np.asarray(vals, float)
    blocks = np.asarray(blocks)
    ub, inv = np.unique(blocks, return_inverse=True)
    sums = np.bincount(inv, weights=vals, minlength=len(ub))
    cnts = np.bincount(inv, minlength=len(ub)).astype(float)
    nb = len(ub)
    if nb < 3:
        m = vals.mean() if len(vals) else np.nan
        return (m, np.nan, np.nan, np.nan)
    rng = np.random.default_rng(seed)
    L = max(1, int(block_len))
    nstart = max(1, nb - L + 1)
    k = int(math.ceil(nb / L))
    cs = np.r_[0, np.cumsum(sums)]; cc = np.r_[0, np.cumsum(cnts)]
    st = rng.integers(0, nstart, size=(nrep, k))
    s = (cs[np.minimum(st + L, nb)] - cs[st]).sum(1)
    c = (cc[np.minimum(st + L, nb)] - cc[st]).sum(1)
    bm = s / np.maximum(c, 1)
    m = sums.sum() / cnts.sum()
    return (m, np.percentile(bm, 2.5), np.percentile(bm, 97.5), bm.std())


def block_boot_stat(blocks, fn, nrep=500, seed=0, block_len=1):
    """Generic moving-block bootstrap: fn(index_array) -> scalar."""
    blocks = np.asarray(blocks)
    ub, inv = np.unique(blocks, return_inverse=True)
    nb = len(ub)
    order = np.argsort(inv, kind="stable")
    starts = np.searchsorted(inv[order], np.arange(nb))
    ends = np.r_[starts[1:], len(order)]
    rng = np.random.default_rng(seed)
    L = max(1, int(block_len)); nstart = max(1, nb - L + 1); k = int(math.ceil(nb / L))
    out = []
    for _ in range(nrep):
        st = rng.integers(0, nstart, size=k)
        bl = np.concatenate([np.arange(s, min(s + L, nb)) for s in st])
        idx = np.concatenate([order[starts[b]:ends[b]] for b in bl])
        out.append(fn(idx))
    out = np.array(out)
    return np.nanpercentile(out, 2.5), np.nanpercentile(out, 97.5), np.nanstd(out)


def holm(pvals):
    p = np.asarray(pvals, float)
    m = len(p)
    order = np.argsort(p)
    adj = np.empty(m)
    run = 0.0
    for r, i in enumerate(order):
        run = max(run, (m - r) * p[i])
        adj[i] = min(1.0, run)
    return adj


def bh(pvals):
    p = np.asarray(pvals, float)
    m = len(p)
    order = np.argsort(p)
    adj = np.empty(m)
    prev = 1.0
    for r in range(m - 1, -1, -1):
        i = order[r]
        prev = min(prev, p[i] * m / (r + 1))
        adj[i] = prev
    return adj


def split_days(df, frac=0.6):
    """Chronological split on trading days: returns the first OOS day index."""
    nd = df.day.max() + 1
    return int(nd * frac)


def p_from_ci(m, se):
    from scipy.stats import norm
    if not np.isfinite(se) or se <= 0:
        return np.nan
    return 2 * (1 - norm.cdf(abs(m / se)))


# ----------------------------------------------------------------------------- race surface (random-start baseline)
class RaceSurface:
    """Distance-matched random-level baseline. From random start bars s (decision at close s), measure in TICKS the
    running max up-excursion U_k and down-excursion D_k over bars s+1..s+k. A phantom level at distance d (ATR_s units)
    is placed at q = round(d*ATR_s/tick) ticks and is HIT when the excursion EXCEEDS it (strict trade-through, the same
    rule as real pools on the same tick grid). Gives P(up first | d_up, d_dn), P(none), P(tie), and single-level reach."""

    def __init__(self, df, starts, H, tick, grid=None):
        h, l, c, atr, seg = df.high.values, df.low.values, df.close.values, df.atr.values, df.seg.values
        n = len(df)
        self.g = grid if grid is not None else np.exp(np.linspace(np.log(0.05), np.log(25.0), 56))
        self.lg = np.log(self.g)
        G = len(self.g)
        st = [s for s in starts if s + H < n and seg[s + H] == seg[s] and np.isfinite(atr[s]) and atr[s] > 0]
        self.starts = np.array(st)
        Tu = np.full((len(st), G), H + 1, dtype=np.int32)
        Td = np.full((len(st), G), H + 1, dtype=np.int32)
        for i, s in enumerate(st):
            up = np.round((np.maximum.accumulate(h[s + 1:s + H + 1]) - c[s]) / tick)
            dn = np.round((c[s] - np.minimum.accumulate(l[s + 1:s + H + 1])) / tick)
            q = np.round(self.g * atr[s] / tick)
            Tu[i] = np.searchsorted(up, q, side="right") + 1   # first k with up > q (1-based); H+1 = never
            Td[i] = np.searchsorted(dn, q, side="right") + 1
        self.H = H
        # pair matrices
        U = Tu[:, :, None]; D = Td[:, None, :]
        upf = (U < D) & (U <= H)
        dnf = (D < U) & (D <= H)
        tie = (U == D) & (U <= H)
        none = (U > H) & (D > H)
        res = upf.sum(0) + dnf.sum(0)
        self.PU = np.where(res > 0, upf.sum(0) / np.maximum(res, 1), np.nan)   # P(up first | resolved, no tie)
        self.PN = none.mean(0)
        self.PT = tie.mean(0)
        self.single_up = (Tu <= H).mean(0)
        self.single_dn = (Td <= H).mean(0)
        self.n = len(st)

    def _interp1(self, arr, d):
        x = np.log(np.clip(d, self.g[0], self.g[-1]))
        return np.interp(x, self.lg, arr)

    def _interp2(self, M, du, dd):
        xu = np.log(np.clip(du, self.g[0], self.g[-1])); xd = np.log(np.clip(dd, self.g[0], self.g[-1]))
        iu = np.clip(np.searchsorted(self.lg, xu) - 1, 0, len(self.g) - 2)
        idd = np.clip(np.searchsorted(self.lg, xd) - 1, 0, len(self.g) - 2)
        fu = (xu - self.lg[iu]) / (self.lg[iu + 1] - self.lg[iu])
        fd = (xd - self.lg[idd]) / (self.lg[idd + 1] - self.lg[idd])
        m00 = M[iu, idd]; m10 = M[iu + 1, idd]; m01 = M[iu, idd + 1]; m11 = M[iu + 1, idd + 1]
        return (m00 * (1 - fu) * (1 - fd) + m10 * fu * (1 - fd) + m01 * (1 - fu) * fd + m11 * fu * fd)

    def p_up_first(self, du, dd):
        return self._interp2(self.PU, np.asarray(du, float), np.asarray(dd, float))

    def p_none(self, du, dd):
        return self._interp2(self.PN, np.asarray(du, float), np.asarray(dd, float))

    def p_reach(self, d, side):
        return self._interp1(self.single_up if side > 0 else self.single_dn, np.asarray(d, float))


def race(h, l, seg, t, up_lvl, dn_lvl, H):
    """First-passage race from decision bar t over bars t+1..t+H: +1 up level traded first, -1 down first,
    0 tie (same bar), 9 none, -9 window leaves segment/data."""
    n = len(h)
    if t + H >= n or seg[t + H] != seg[t]:
        e = t + 1
        while e < n and e <= t + H and seg[e] == seg[t]:
            e += 1
        # partial window: only valid if resolved before the hole
        hi = h[t + 1:e] > up_lvl; lo = l[t + 1:e] < dn_lvl
        iu = np.argmax(hi) if hi.any() else 10 ** 9
        idn = np.argmax(lo) if lo.any() else 10 ** 9
        if iu == idn == 10 ** 9:
            return -9, -1
    else:
        hi = h[t + 1:t + H + 1] > up_lvl; lo = l[t + 1:t + H + 1] < dn_lvl
        iu = np.argmax(hi) if hi.any() else 10 ** 9
        idn = np.argmax(lo) if lo.any() else 10 ** 9
    if iu == idn == 10 ** 9:
        return 9, -1
    if iu == idn:
        return 0, iu + 1
    return (1, iu + 1) if iu < idn else (-1, idn + 1)
