"""E4 regime + calibration: shared loaders, indicators, hysteresis classifier, scoring and bootstrap.
All features at bar t use bars <= t only. Outcomes use bars t+1..t+H.
Data: raw CME CSVs (UTC) from the study clone and BTC 1h. Loader conventions follow
study/quant_regime_tools/rlib.py and quant_regime_b_tools/blib.py (reused definitions: Wilder ATR,
Kaufman ER, ADX, VR-Hurst), re-implemented here with exact NY time via zoneinfo.
"""
import glob, math, os
import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view as sw

SP = "/tmp/claude-0/-home-user-m/7ce60006-3639-59b1-8cd3-87355409d58a/scratchpad/"
CME = SP + "brief/study/amt_data/cme/"
BTC = SP + "brief/study/classic_tools/btc_1h.csv"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
os.makedirs(OUT, exist_ok=True)

W_PCT = 500
WARM = 600


# ---------------------------------------------------------------- loading
def _frame(df):
    df = df.sort_values("datetime").drop_duplicates("datetime")
    return df.reset_index(drop=True)


def load_cme(sym, tf):
    fn = glob.glob(CME + f"{sym}/{sym}_{tf}_*.csv")[0]
    d = pd.read_csv(fn, parse_dates=["datetime"])
    return _frame(d)


def resample(d, minutes):
    d = d.set_index("datetime")
    r = d.resample(f"{minutes}min", label="left", closed="left").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}).dropna(subset=["open"])
    return r.reset_index()


def load_btc():
    d = pd.read_csv(BTC)
    d["datetime"] = pd.to_datetime(d["datetime"])
    return _frame(d)


REPAIR_LOG = []


def repair_spikes(d, name, k_spike=10.0, k_back=3.0):
    """Evidence-based repair of single bad prints (added on resume, 2026-11-28; see check_data2.py).
    A bar's open or close is a bad print when it lies > k_spike * ATR14[t-1] from BOTH the previous close and the
    next open, while the previous close and the next open agree within k_back * ATR14[t-1] (price was back at once).
    The print is replaced by the neighbouring price (open <- previous close, close <- next open); a high or low
    that sits beyond the repaired body by > k_spike * ATR14[t-1] on the same side is clipped to the body.
    This uses bar t+1, so it is a data-cleaning step only (never a feature). Every repair is logged."""
    O = d["open"].values.astype(float).copy(); Hh = d["high"].values.astype(float).copy()
    L = d["low"].values.astype(float).copy(); C = d["close"].values.astype(float).copy()
    A = atr(Hh, L, C, 14)
    for t in range(15, len(C) - 1):
        a = A[t - 1]
        if not np.isfinite(a) or a <= 0:
            continue
        pc, no = C[t - 1], O[t + 1]
        if abs(no - pc) > k_back * a:
            continue
        badO = abs(O[t] - pc) > k_spike * a and abs(O[t] - no) > k_spike * a
        badC = abs(C[t] - pc) > k_spike * a and abs(C[t] - no) > k_spike * a
        if not (badO or badC):
            continue
        rec = dict(ds=name, t=str(d["datetime"].iloc[t]), O=O[t], H=Hh[t], L=L[t], C=C[t], atr=round(float(a), 4))
        if badO:
            O[t] = pc
        if badC:
            C[t] = no
        top, bot = max(O[t], C[t]), min(O[t], C[t])
        if Hh[t] - top > k_spike * a:
            Hh[t] = top
        if bot - L[t] > k_spike * a:
            L[t] = bot
        Hh[t] = max(Hh[t], top); L[t] = min(L[t], bot)
        rec.update(newO=O[t], newH=Hh[t], newL=L[t], newC=C[t])
        REPAIR_LOG.append(rec)
    d = d.copy()
    d["open"], d["high"], d["low"], d["close"] = O, Hh, L, C
    return d


def to_arrays(d, tzname):
    t = pd.DatetimeIndex(d["datetime"]).tz_localize("UTC")
    loc = t.tz_convert(tzname)
    return dict(T=t, O=d["open"].values.astype(float), H=d["high"].values.astype(float),
                L=d["low"].values.astype(float), C=d["close"].values.astype(float),
                hour=loc.hour.values, minute=loc.minute.values, date=np.array(loc.date),
                tz=tzname)


def tod_bucket(a, mins):
    return (a["hour"] * 60 + a["minute"]) // mins


# ---------------------------------------------------------------- indicators
def rma(x, n):
    out = np.full(len(x), np.nan); a = 1.0 / n
    s = np.nan; cnt = 0; acc = 0.0
    for i, v in enumerate(x):
        if np.isnan(v):
            out[i] = s; continue
        if cnt < n:
            acc += v; cnt += 1
            if cnt == n:
                s = acc / n
        else:
            s = s + a * (v - s)
        out[i] = s
    return out


def true_range(H, L, C):
    pc = np.r_[np.nan, C[:-1]]
    tr = np.maximum(H - L, np.maximum(np.abs(H - pc), np.abs(L - pc)))
    tr[0] = H[0] - L[0]
    return tr


def atr(H, L, C, n=14):
    return rma(true_range(H, L, C), n)


def roll_std(x, n):
    out = np.full(len(x), np.nan)
    if len(x) >= n:
        out[n - 1:] = sw(x, n).std(1)
    return out


def roll_mean(x, n):
    out = np.full(len(x), np.nan)
    if len(x) >= n:
        out[n - 1:] = sw(x, n).mean(1)
    return out


def rv(C, n=20):
    r = np.r_[np.nan, np.diff(np.log(C))]
    out = np.full(len(C), np.nan)
    out[n:] = sw(r[1:], n).std(1)
    return out


def bbw(C, n=20):
    return 4.0 * roll_std(C, n) / roll_mean(C, n)


def pct_rank(x, W=W_PCT):
    """Pine ta.percentrank: % of the previous W values <= current value (current excluded)."""
    n = len(x); out = np.full(n, np.nan)
    if n <= W:
        return out
    win = sw(x[:-1], W)  # win[i] = x[i .. i+W-1], previous window for t = i+W
    cur = x[W:]
    ok = np.isfinite(cur) & np.isfinite(win).all(1)
    res = 100.0 * (win <= cur[:, None]).sum(1) / W
    res[~ok] = np.nan
    out[W:] = res
    return out


def er(C, n=20):
    out = np.full(len(C), np.nan)
    d = np.abs(np.diff(C))
    s = np.r_[np.nan, d]
    cs = np.nancumsum(np.r_[0.0, d])
    for_t = np.arange(n, len(C))
    num = np.abs(C[for_t] - C[for_t - n])
    den = cs[for_t] - cs[for_t - n]
    out[for_t] = np.where(den > 0, num / den, 0.0)
    return out


def adx(H, L, C, n=14):
    up = np.r_[0, np.diff(H)]; dn = np.r_[0, -np.diff(L)]
    pdm = np.where((up > dn) & (up > 0), up, 0.0)
    mdm = np.where((dn > up) & (dn > 0), dn, 0.0)
    tr = true_range(H, L, C)
    atr_ = rma(tr, n)
    pdi = 100 * rma(pdm, n) / atr_; mdi = 100 * rma(mdm, n) / atr_
    dx = 100 * np.abs(pdi - mdi) / np.where(pdi + mdi > 0, pdi + mdi, np.nan)
    dx = np.nan_to_num(dx, nan=0.0)
    return rma(dx, n)


def vr_hurst(C, q=4, w=96):
    lr = np.log(C)
    r1 = np.r_[np.nan, np.diff(lr)]
    rq = np.full(len(C), np.nan); rq[q:] = lr[q:] - lr[:-q]
    v1 = np.full(len(C), np.nan); vq = np.full(len(C), np.nan)
    if len(C) > w + q:
        v1[w:] = sw(r1[1:], w).var(1)
        vq[w + q - 1:] = sw(rq[q:], w).var(1)[: len(C) - (w + q - 1)]
    vr = vq / (q * v1)
    h = 0.5 + np.log(vr) / (2 * np.log(q))
    return vr, h


def tod_deseason_atr(a, mins, sessions=20):
    """TR / trailing mean TR at the same TOD bucket over the last `sessions` occurrences (excl. t), RMA14."""
    H, L, C = a["H"], a["L"], a["C"]
    tr = true_range(H, L, C)
    b = tod_bucket(a, mins)
    ratio = np.full(len(tr), np.nan)
    hist = {}
    for i in range(len(tr)):
        lst = hist.setdefault(b[i], [])
        if len(lst) >= 5:
            m = np.mean(lst[-sessions:])
            if m > 0:
                ratio[i] = tr[i] / m
        lst.append(tr[i])
    ratio = np.where(np.isfinite(ratio), ratio, 1.0)
    return rma(ratio, 14)


# ---------------------------------------------------------------- hysteresis
HYS = {
    "raw": dict(lo_in=20, lo_out=20, hi_in=80, hi_out=80, dwell=0, raw=True),
    "hysA": dict(lo_in=20, lo_out=30, hi_in=80, hi_out=70, dwell=5, raw=False),
    "hysB": dict(lo_in=15, lo_out=35, hi_in=85, hi_out=65, dwell=10, raw=False),
}


def classify(p, lo_in, lo_out, hi_in, hi_out, dwell, raw):
    """3-state classifier. returns int array: 0 = low state (C / RANGE), 1 = mid, 2 = high (E / TREND); -1 = undefined"""
    n = len(p); s = np.full(n, -1, dtype=int)
    if raw:
        ok = np.isfinite(p)
        s[ok] = np.where(p[ok] < lo_in, 0, np.where(p[ok] > hi_in, 2, 1))
        return s
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


def persistence(s, H, mask=None):
    """mean dwell (bars), switches per 1000 bars, P(s[t+H]==s[t]) on valid bars"""
    if mask is None:
        mask = s >= 0
    idx = np.where(mask)[0]
    ss = s[idx]
    if len(ss) < 10:
        return dict(dwell=np.nan, sw1000=np.nan, pstay=np.nan, occ=[np.nan] * 3)
    ch = np.sum(ss[1:] != ss[:-1])
    runs = ch + 1
    a = s[:-H]; b = s[H:]
    m2 = mask[:-H] & mask[H:]
    pstay = np.mean(a[m2] == b[m2]) if m2.any() else np.nan
    occ = [float(np.mean(ss == k)) for k in range(3)]
    return dict(dwell=len(ss) / runs, sw1000=1000.0 * ch / len(ss), pstay=float(pstay), occ=occ)


# ---------------------------------------------------------------- forward quantities
def fwd_max_min(H, L, K):
    n = len(H); mx = np.full(n, np.nan); mn = np.full(n, np.nan)
    if n > K:
        mx[: n - K] = sw(H[1:], K).max(1)
        mn[: n - K] = sw(L[1:], K).min(1)
    return mx, mn


def fwd_close(C, K):
    out = np.full(len(C), np.nan); out[: len(C) - K] = C[K:]
    return out


# ---------------------------------------------------------------- nulls
def sign_flip(a, rng):
    """random signs on close-to-close log returns; bar shape (O,H,L relative to C) kept."""
    C = a["C"]; lr = np.diff(np.log(C))
    sg = rng.choice([-1.0, 1.0], size=len(lr))
    C2 = C[0] * np.exp(np.r_[0, np.cumsum(lr * sg)])
    f = C2 / C
    # mirror the bar shape when the sign is flipped so that H stays the high
    flip = np.r_[1.0, sg] < 0
    hrel = np.log(a["H"] / C); lrel = np.log(a["L"] / C); orel = np.log(a["O"] / C)
    H2 = np.where(flip, C2 * np.exp(-lrel), C2 * np.exp(hrel))
    L2 = np.where(flip, C2 * np.exp(-hrel), C2 * np.exp(lrel))
    O2 = np.where(flip, C2 * np.exp(-orel), C2 * np.exp(orel))
    b = dict(a); b.update(O=O2, H=H2, L=L2, C=C2)
    return b


def shuffle(a, rng):
    C = a["C"]; lr = np.diff(np.log(C))
    perm = rng.permutation(len(lr))
    C2 = C[0] * np.exp(np.r_[0, np.cumsum(lr[perm])])
    idx = np.r_[0, perm + 1]
    hrel = np.log(a["H"] / C)[idx]; lrel = np.log(a["L"] / C)[idx]; orel = np.log(a["O"] / C)[idx]
    b = dict(a); b.update(O=C2 * np.exp(orel), H=C2 * np.exp(hrel), L=C2 * np.exp(lrel), C=C2)
    return b


# ---------------------------------------------------------------- integrity
def integrity(a):
    A = atr(a["H"], a["L"], a["C"], 14)
    pc = np.r_[np.nan, a["C"][:-1]]; pa = np.r_[np.nan, A[:-1]]
    g1 = np.abs(a["O"] - pc) / pa; g2 = np.abs(a["C"] - pc) / pa
    flag = (g1 > 4) | (g2 > 6)
    mx = np.nanmax(np.maximum(g1, g2)[20:])
    return dict(n=len(A), flagged=int(np.nansum(flag[20:])), rate=float(np.nanmean(flag[20:])), max_jump_atr=float(mx))


# ---------------------------------------------------------------- datasets
REPAIR = os.environ.get("E4_NOREPAIR", "0") != "1"


def _rep(d, name):
    return repair_spikes(d, name) if REPAIR else d


def datasets(fam, include_excluded=False):
    """returns list of (name, arrays dict, tod_minutes)"""
    out = []
    if fam == "1h":
        for s in ("ES", "NQ", "RTY", "YM", "CL", "GC"):
            if not include_excluded and s + "_1h" in EXCLUDE:
                continue
            out.append((s + "_1h", to_arrays(_rep(load_cme(s, "1h"), s + "_1h"), "America/New_York"), 60))
    elif fam == "5m":
        for s in ("ES", "NQ", "RTY", "YM", "CL", "GC"):
            d = resample(load_cme(s, "1min"), 5)
            out.append((s + "_5m", to_arrays(_rep(d, s + "_5m"), "America/New_York"), 30))
    elif fam == "btc":
        out.append(("BTC_1h", to_arrays(_rep(load_btc(), "BTC_1h"), "UTC"), 60))
    if not include_excluded:
        out = [x for x in out if x[0] not in EXCLUDE]
    return out


BPD = {"1h": 18.8, "5m": 226.8, "btc": 24.0}  # measured bars per calendar day (check_data.py)
FAMS = ("1h", "5m", "btc")


_FEAT_CACHE = {}


def features(name, a, mins):
    """volatility features at bar t (bars <= t only)."""
    if name in _FEAT_CACHE:
        return _FEAT_CACHE[name]
    H, L, C = a["H"], a["L"], a["C"]
    f = {}
    f["A14"] = atr(H, L, C, 14); f["A100"] = atr(H, L, C, 100)
    f["p_atr"] = pct_rank(f["A14"])
    f["p_rv"] = pct_rank(rv(C, 20))
    f["p_bbw"] = pct_rank(bbw(C, 20))
    f["p_des"] = pct_rank(tod_deseason_atr(a, mins))
    _FEAT_CACHE[name] = f
    return f


EXCLUDE = {"GC_1h", "CL_1h"}  # GC_1h: 2.1% bars flagged (study: corrupted). CL_1h: data holes of 23, 10, 7 days (check_data.py)


def split_idx(n, H, frac=0.6, warm=WARM):
    """IS = [warm, cut-H), OOS = [cut, n-H)"""
    cut = warm + int((n - warm) * frac)
    return np.arange(warm, cut - H), np.arange(cut, n - H), cut


# ---------------------------------------------------------------- scoring
def clip(p):
    return np.clip(p, 1e-4, 1 - 1e-4)


def logloss_vec(p, y):
    p = clip(p); return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def brier_vec(p, y):
    return (p - y) ** 2


def ece(p, y, bins=10):
    b = np.minimum((p * bins).astype(int), bins - 1)
    tot = 0.0
    for k in range(bins):
        m = b == k
        if m.any():
            tot += m.sum() * abs(p[m].mean() - y[m].mean())
    return tot / len(p)


def murphy(p, y, bins=10):
    """BS = REL - RES + UNC (+ within-bin term WBV so that it sums exactly)."""
    b = np.minimum((p * bins).astype(int), bins - 1)
    ybar = y.mean(); n = len(y)
    rel = res = 0.0
    for k in range(bins):
        m = b == k
        if m.any():
            nk = m.sum(); ok = y[m].mean(); fk = p[m].mean()
            rel += nk * (fk - ok) ** 2; res += nk * (ok - ybar) ** 2
    rel /= n; res /= n; unc = ybar * (1 - ybar)
    bs = np.mean((p - y) ** 2)
    return dict(BS=bs, REL=rel, RES=res, UNC=unc, resid=bs - (rel - res + unc))


def logit(p):
    p = clip(p); return np.log(p / (1 - p))


def calib_slope(p, y, it=30):
    """logistic recalibration y ~ a + b*logit(p); returns (a, b)"""
    x = logit(p); X = np.c_[np.ones_like(x), x]
    w = np.array([0.0, 1.0])
    for _ in range(it):
        z = X @ w; q = 1 / (1 + np.exp(-z))
        g = X.T @ (q - y); Hm = (X * (q * (1 - q))[:, None]).T @ X + 1e-9 * np.eye(2)
        step = np.linalg.solve(Hm, g); w -= step
        if np.abs(step).max() < 1e-8:
            break
    return float(w[0]), float(w[1])


def wilson(k, n, z=1.96):
    if n == 0:
        return (np.nan, np.nan, np.nan)
    ph = k / n; den = 1 + z * z / n
    c = (ph + z * z / (2 * n)) / den; h = z * math.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / den
    return (ph, c - h, c + h)


def block_boot_mean(vals, blocks, reps=2000, rng=None, stat="mean"):
    """cluster bootstrap of the mean of vals with cluster ids `blocks` (resample clusters with replacement)."""
    if rng is None:
        rng = np.random.default_rng(7)
    vals = np.asarray(vals, float); blocks = np.asarray(blocks)
    ok = np.isfinite(vals); vals = vals[ok]; blocks = blocks[ok]
    if len(vals) == 0:
        return (np.nan, np.nan, np.nan)
    u, inv = np.unique(blocks, return_inverse=True)
    s = np.bincount(inv, weights=vals); c = np.bincount(inv)
    k = len(u)
    idx = rng.integers(0, k, size=(reps, k))
    bs = s[idx].sum(1) / c[idx].sum(1)
    return (float(vals.mean()), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5)))


def block_boot_ratio(num, den, blocks, reps=2000, rng=None):
    """bootstrap of sum(num)/sum(den) by clusters"""
    if rng is None:
        rng = np.random.default_rng(11)
    u, inv = np.unique(np.asarray(blocks), return_inverse=True)
    sn = np.bincount(inv, weights=num); sd = np.bincount(inv, weights=den)
    k = len(u); idx = rng.integers(0, k, size=(reps, k))
    bs = sn[idx].sum(1) / sd[idx].sum(1)
    return (float(num.sum() / den.sum()), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5)))


def day_blocks(a, idx, H, bars_per_day):
    """cluster ids: calendar-day ordinal (dataset clock) // k, with k = ceil(H / bars_per_day) so that a block
    spans >= H bars. Calendar ids are shared across symbols, so pooled families cluster by calendar time."""
    k = max(1, int(math.ceil(H / bars_per_day)))
    d = a["date"][idx]
    return np.array([x.toordinal() // k for x in d])


def holm(pvals):
    p = np.asarray(pvals, float); m = len(p); order = np.argsort(p)
    adj = np.empty(m); run = 0.0
    for r, i in enumerate(order):
        run = max(run, (m - r) * p[i]); adj[i] = min(1.0, run)
    return adj


def p_from_ci(est, lo, hi):
    """two-sided normal approx p-value from a 95% CI"""
    se = (hi - lo) / (2 * 1.96)
    if not np.isfinite(se) or se <= 0:
        return np.nan
    z = abs(est) / se
    return math.erfc(z / math.sqrt(2))


def norm_cdf(x):
    return 0.5 * (1 + np.vectorize(math.erf)(np.asarray(x) / math.sqrt(2)))
