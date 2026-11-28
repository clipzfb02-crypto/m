"""E7_structure_rules shared library: data, pivots, structure state machine, outcomes, statistics.

Reuses the E2 loader (E2_signals/e2data.py) unchanged. All features at bar t use bars <= t.
Pivots are usable only from their confirmation bar. See the pre-registration in
apex/research/experiments/E7_structure_rules.md (section A).
"""
import os
import sys
import math
import numpy as np
import pandas as pd
from numba import njit

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "E2_signals"))
import e2data  # noqa: E402

OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)

WARM = 600
HMAX = 60
HS = (5, 20, 60)
FAM_1H = ["NQ_1h", "ES_1h", "YM_1h", "RTY_1h", "CL_1h", "BTC_1h"]
FAM_ID = ["NQ_5m", "NQ_15m"]


# ----------------------------------------------------------------------------------------------
# data
# ----------------------------------------------------------------------------------------------
def wilder_atr(h, l, c, n=14):
    pc = np.concatenate([[c[0]], c[:-1]])
    tr = np.maximum(h - l, np.maximum(np.abs(h - pc), np.abs(l - pc)))
    atr = np.empty_like(tr)
    atr[:n] = np.nan
    atr[n - 1] = tr[:n].mean()
    a = 1.0 / n
    for i in range(n, len(tr)):
        atr[i] = atr[i - 1] + a * (tr[i] - atr[i - 1])
    return atr


class DS:
    """Arrays for one dataset (real or synthetic)."""

    def __init__(self, name, o, h, l, c, sess, guard, ts=None):
        self.name = name
        self.o, self.h, self.l, self.c = [np.ascontiguousarray(x, dtype=np.float64) for x in (o, h, l, c)]
        self.n = len(c)
        self.sess = sess  # int day key
        self.guard = np.asarray(guard, bool)
        self.ts = ts
        self.atr = wilder_atr(self.h, self.l, self.c)
        n = self.n
        self.split = WARM + int(0.6 * (n - WARM))
        # guard within [t, t+HMAX]
        g = self.guard.astype(np.int64)
        cg = np.concatenate([[0], np.cumsum(g)])
        idx = np.arange(n)
        hi = np.minimum(idx + HMAX + 1, n)
        gwin = (cg[hi] - cg[idx]) > 0
        elig = (idx >= WARM) & (idx + HMAX < n) & (~gwin) & np.isfinite(self.atr) & (self.atr > 0)
        self.sp = np.full(n, -1, np.int8)  # 0 IS, 1 OOS, -1 not eligible
        self.sp[elig & (idx + HMAX < self.split)] = 0
        self.sp[elig & (idx >= self.split)] = 1
        # forward returns in ATR units (up frame)
        self.R = {}
        for H in HS:
            r = np.full(n, np.nan)
            r[: n - H] = (self.c[H:] - self.c[: n - H]) / self.atr[: n - H]
            self.R[H] = r
        # split means for drift baseline
        self.mu = {H: [np.nanmean(self.R[H][self.sp == s]) for s in (0, 1)] for H in HS}
        self.pup = {H: [np.nanmean(self.R[H][self.sp == s] > 0) for s in (0, 1)] for H in HS}
        bps = n / max(1, len(np.unique(sess)))
        self.bars_per_sess = bps
        # 1-bar signed return in ATR for matched baseline (IS deciles)
        r1 = np.full(n, np.nan)
        r1[1:] = (self.c[1:] - self.c[:-1]) / self.atr[1:]
        self.r1 = r1
        qs = np.nanquantile(r1[self.sp == 0], np.linspace(0.1, 0.9, 9))
        self.r1cell = np.searchsorted(qs, np.nan_to_num(r1))


def load_real(name):
    d, meta = e2data.load(name)
    sess = (pd.to_datetime(d.sess).values.astype("datetime64[D]").astype(np.int64))
    ds = DS(name, d.open.values, d.high.values, d.low.values, d.close.values, sess, d.guard.values, d.ts.values)
    ds.meta = meta
    return ds


def signflip(ds, seed):
    """Mirror each bar (its close-to-close move and shape) with a random sign. Keeps volatility
    clustering, removes direction dependence. Guard bars and sessions are kept."""
    rng = np.random.default_rng(seed)
    n = ds.n
    pc = np.concatenate([[ds.c[0]], ds.c[:-1]])
    do, dh, dl, dc = ds.o - pc, ds.h - pc, ds.l - pc, ds.c - pc
    s = rng.choice([-1.0, 1.0], n)
    s[0] = 1.0
    no = np.where(s > 0, do, -do)
    nh = np.where(s > 0, dh, -dl)
    nl = np.where(s > 0, dl, -dh)
    nc = np.where(s > 0, dc, -dc)
    # rebuild (additive). Shift so that the minimum stays positive (percent-based rules need price > 0)
    C = ds.c[0] + np.cumsum(np.concatenate([[0.0], nc[1:]]))
    PC = np.concatenate([[C[0]], C[:-1]])
    O, H, L = PC + no, PC + nh, PC + nl
    O[0], H[0], L[0], C[0] = ds.o[0], ds.h[0], ds.l[0], ds.c[0]
    m = min(L.min(), 0.0)
    if m <= 0:
        sh = -m + 0.5 * ds.c.mean()
        O, H, L, C = O + sh, H + sh, L + sh, C + sh
    out = DS(ds.name + f"_sf{seed}", O, H, L, C, ds.sess, ds.guard)
    return out


# ----------------------------------------------------------------------------------------------
# pivots
# ----------------------------------------------------------------------------------------------
@njit(cache=True)
def fractal_pivots(h, l, p):
    """Leftmost-wins fractal: high at i if h[i] > max(h[i-p:i]) and h[i] >= max(h[i+1:i+p+1]).
    Returns arrays (bar, conf, price, typ) sorted by conf; typ +1 high, -1 low."""
    n = len(h)
    bars = np.empty(2 * n, np.int64)
    confs = np.empty(2 * n, np.int64)
    prices = np.empty(2 * n, np.float64)
    typs = np.empty(2 * n, np.int64)
    k = 0
    for i in range(p, n - p):
        ok = True
        for j in range(i - p, i):
            if not (h[i] > h[j]):
                ok = False
                break
        if ok:
            for j in range(i + 1, i + p + 1):
                if not (h[i] >= h[j]):
                    ok = False
                    break
        okl = True
        for j in range(i - p, i):
            if not (l[i] < l[j]):
                okl = False
                break
        if okl:
            for j in range(i + 1, i + p + 1):
                if not (l[i] <= l[j]):
                    okl = False
                    break
        if ok:
            bars[k] = i; confs[k] = i + p; prices[k] = h[i]; typs[k] = 1; k += 1
        if okl:
            bars[k] = i; confs[k] = i + p; prices[k] = l[i]; typs[k] = -1; k += 1
    return bars[:k], confs[:k], prices[:k], typs[:k]


@njit(cache=True)
def zigzag_pivots(h, l, thrA, pct, start):
    """ZigZag. threshold at bar t = thrA[t] + pct*extreme. A bar that sets a new extreme cannot
    confirm the reversal. Pivot confirmed at the first bar whose low (high) reaches the threshold."""
    n = len(h)
    bars = np.empty(n, np.int64)
    confs = np.empty(n, np.int64)
    prices = np.empty(n, np.float64)
    typs = np.empty(n, np.int64)
    k = 0
    mode = 1
    ext = h[start]
    eb = start
    for t in range(start + 1, n):
        th = thrA[t]
        if not (th == th):
            continue
        if mode == 1:
            if h[t] > ext:
                ext = h[t]; eb = t
            elif l[t] <= ext - (th + pct * ext):
                bars[k] = eb; confs[k] = t; prices[k] = ext; typs[k] = 1; k += 1
                mode = -1
                ext = l[eb + 1]; nb = eb + 1
                for j in range(eb + 1, t + 1):
                    if l[j] < ext:
                        ext = l[j]; nb = j
                eb = nb
        else:
            if l[t] < ext:
                ext = l[t]; eb = t
            elif h[t] >= ext + (th + pct * ext):
                bars[k] = eb; confs[k] = t; prices[k] = ext; typs[k] = -1; k += 1
                mode = 1
                ext = h[eb + 1]; nb = eb + 1
                for j in range(eb + 1, t + 1):
                    if h[j] > ext:
                        ext = h[j]; nb = j
                eb = nb
    return bars[:k], confs[:k], prices[:k], typs[:k]


def pivots(ds, method, pct_cache=None):
    """method: F2,F3,F5,ZA1.5,ZA3,ZP1.5,ZP3. Returns dict of arrays sorted by conf."""
    if method.startswith("F"):
        b, c, p, t = fractal_pivots(ds.h, ds.l, int(method[1:]))
    elif method.startswith("ZA"):
        k = float(method[2:])
        thr = k * ds.atr
        b, c, p, t = zigzag_pivots(ds.h, ds.l, thr, 0.0, 20)
    elif method.startswith("ZP"):
        k = float(method[2:])
        if pct_cache is not None and method in pct_cache:
            pct = pct_cache[method]
        else:
            m = ds.sp == 0
            pct = float(np.nanmedian(k * ds.atr[m] / ds.c[m]))
        thr = np.zeros(ds.n)
        b, c, p, t = zigzag_pivots(ds.h, ds.l, thr, pct, 20)
    else:
        raise ValueError(method)
    o = np.argsort(c, kind="stable")
    return dict(bar=b[o], conf=c[o], price=p[o], typ=t[o])


def last_pivot_series(n, piv, typ, delay=0):
    """price of the latest pivot of type typ with conf <= t - delay, per bar t (nan before)."""
    m = piv["typ"] == typ
    conf = piv["conf"][m] + delay
    pr = piv["price"][m]
    out = np.full(n, np.nan)
    ok = conf < n
    out_idx = conf[ok]
    tmp = np.full(n, np.nan)
    tmp[out_idx] = pr[ok]  # later pivots with same conf overwrite (sorted by conf, stable)
    s = pd.Series(tmp).ffill().values
    return s


# ----------------------------------------------------------------------------------------------
# structure state machine
# ----------------------------------------------------------------------------------------------
@njit(cache=True)
def structure(h, l, c, hconf, hprice, lconf, lprice, rule):
    """rule 0 = close beyond the reference, 1 = wick beyond.
    Reference = most recent swing confirmed at bar <= t-1, consumed when broken.
    Returns per bar: evdir (+1/-1/0), evlev, evlab (0 first,1 BOS,2 CHoCH,-1 none), state,
    protL, protH, legH, legL (after processing bar t)."""
    n = len(c)
    evdir = np.zeros(n, np.int64)
    evlev = np.full(n, np.nan)
    evlab = np.full(n, -1, np.int64)
    st = np.zeros(n, np.int64)
    pL = np.full(n, np.nan)
    pH = np.full(n, np.nan)
    lgH = np.full(n, np.nan)
    lgL = np.full(n, np.nan)
    state = 0
    refH = np.nan
    refL = np.nan
    legH = -1e300
    legL = 1e300
    protH = np.nan
    protL = np.nan
    ih = 0
    il = 0
    nh = len(hconf)
    nl = len(lconf)
    for t in range(n):
        while ih < nh and hconf[ih] <= t - 1:
            refH = hprice[ih]; ih += 1
        while il < nl and lconf[il] <= t - 1:
            refL = lprice[il]; il += 1
        if h[t] > legH:
            legH = h[t]
        if l[t] < legL:
            legL = l[t]
        if rule == 0:
            up = (refH == refH) and c[t] > refH
            dn = (refL == refL) and c[t] < refL
        else:
            up = (refH == refH) and h[t] > refH
            dn = (refL == refL) and l[t] < refL
        if up and dn:
            pass
        elif up:
            evdir[t] = 1; evlev[t] = refH
            evlab[t] = 0 if state == 0 else (1 if state == 1 else 2)
            protL = legL; state = 1; refH = np.nan
            legH = h[t]; legL = l[t]
        elif dn:
            evdir[t] = -1; evlev[t] = refL
            evlab[t] = 0 if state == 0 else (1 if state == -1 else 2)
            protH = legH; state = -1; refL = np.nan
            legH = h[t]; legL = l[t]
        st[t] = state
        pL[t] = protL; pH[t] = protH; lgH[t] = legH; lgL[t] = legL
    return evdir, evlev, evlab, st, pL, pH, lgH, lgL


def run_structure(ds, piv, rule):
    mh = piv["typ"] == 1
    ml = piv["typ"] == -1
    return structure(ds.h, ds.l, ds.c, piv["conf"][mh], piv["price"][mh], piv["conf"][ml], piv["price"][ml], rule)


# ----------------------------------------------------------------------------------------------
# outcomes
# ----------------------------------------------------------------------------------------------
@njit(cache=True)
def false_ext(c, idx, dirs, lev, F, include_t):
    """false: a close on the other side of lev within t..t+F (t only if include_t);
    ext: a close >= C_t + (C_t - lev) in the direction within t+1..t+F."""
    m = len(idx)
    fa = np.zeros(m, np.int8)
    ex = np.zeros(m, np.int8)
    n = len(c)
    for k in range(m):
        t = idx[k]; d = dirs[k]; L = lev[k]
        k0 = 0 if include_t else 1
        for j in range(k0, F + 1):
            if t + j >= n:
                break
            if d * (c[t + j] - L) <= 0:
                fa[k] = 1
                break
        gap = d * (c[t] - L)
        for j in range(1, F + 1):
            if t + j >= n:
                break
            if d * (c[t + j] - c[t]) >= gap:
                ex[k] = 1
                break
    return fa, ex


@njit(cache=True)
def first_touch(h, l, c, atr, k, W):
    """+1 up level first, -1 down first, 0 none within W, -2 both on one bar."""
    n = len(c)
    out = np.zeros(n, np.int8)
    for t in range(n - 1):
        a = atr[t]
        if not (a == a):
            continue
        up = c[t] + k * a
        dn = c[t] - k * a
        r = 0
        for j in range(1, W + 1):
            if t + j >= n:
                break
            hu = h[t + j] >= up
            hd = l[t + j] <= dn
            if hu and hd:
                r = -2
                break
            if hu:
                r = 1
                break
            if hd:
                r = -1
                break
        out[t] = r
    return out


def fwd_max(x, N):
    """max of x[t+1..t+N] per t (nan when incomplete)."""
    n = len(x)
    s = pd.Series(x[::-1]).rolling(N, min_periods=N).max().values[::-1]
    out = np.full(n, np.nan)
    out[: n - 1] = s[1:]
    return out


def fwd_min(x, N):
    return -fwd_max(-x, N)


# ----------------------------------------------------------------------------------------------
# event tables
# ----------------------------------------------------------------------------------------------
def event_frame(ds, idx, dirs, extra=None, H_list=HS, matched_mask=None):
    """Build a per-event DataFrame with drift- and matched-baseline excess outcomes.
    idx: bar indices of events; dirs: +1/-1. Events on non-eligible bars are dropped.
    matched_mask: boolean array of event bars (to exclude from the matched pool)."""
    idx = np.asarray(idx, np.int64)
    dirs = np.asarray(dirs, np.int64)
    sp = ds.sp[idx]
    keep = sp >= 0
    idx, dirs, sp = idx[keep], dirs[keep], sp[keep]
    df = pd.DataFrame(dict(ds=ds.name, t=idx, dir=dirs, sp=sp, day=ds.sess[idx]))
    if extra is not None:
        for k, v in extra.items():
            df[k] = np.asarray(v)[keep]
    for H in H_list:
        r = ds.R[H][idx]
        y = dirs * r
        mu = np.where(sp == 0, ds.mu[H][0], ds.mu[H][1])
        pu = np.where(sp == 0, ds.pup[H][0], ds.pup[H][1])
        df[f"y{H}"] = y
        df[f"ex{H}"] = y - dirs * mu
        df[f"hit{H}"] = (y > 0).astype(float)
        df[f"exh{H}"] = (y > 0).astype(float) - np.where(dirs > 0, pu, 1 - pu)
        if matched_mask is not None:
            # cell means of up-frame R over non-event eligible bars, per split and r1 decile
            cm = np.zeros((2, 10))
            for s in (0, 1):
                m = (ds.sp == s) & (~matched_mask) & np.isfinite(ds.R[H])
                cells = ds.r1cell[m]
                sums = np.bincount(cells, weights=ds.R[H][m], minlength=10)
                cnts = np.bincount(cells, minlength=10)
                cm[s] = sums / np.maximum(cnts, 1)
            df[f"exm{H}"] = y - dirs * cm[sp, ds.r1cell[idx]]
    return df


# ----------------------------------------------------------------------------------------------
# statistics
# ----------------------------------------------------------------------------------------------
def block_len(bars_per_sess):
    return max(2, int(math.ceil(HMAX / bars_per_sess)) + 1)


def _boot_idx(nd, Lb, reps, rng):
    nb = int(math.ceil(nd / Lb))
    starts = rng.integers(0, nd, size=(reps, nb))
    idx = (starts[:, :, None] + np.arange(Lb)[None, None, :]) % nd
    return idx.reshape(reps, -1)[:, :nd]


def boot_mean(df, col, Lb=4, reps=2000, seed=7):
    """circular block bootstrap over calendar days of the mean of df[col].
    Returns dict(est, lo, hi, se, p, n, deff)."""
    d = df[["day", col]].dropna()
    n = len(d)
    if n < 10:
        return dict(est=np.nan, lo=np.nan, hi=np.nan, se=np.nan, p=np.nan, n=n, deff=np.nan)
    g = d.groupby("day")[col].agg(["sum", "count"]).sort_index()
    S = g["sum"].values
    N = g["count"].values.astype(float)
    est = S.sum() / N.sum()
    rng = np.random.default_rng(seed)
    idx = _boot_idx(len(S), Lb, reps, rng)
    bs = S[idx].sum(1) / np.maximum(N[idx].sum(1), 1)
    se = bs.std(ddof=1)
    lo, hi = np.percentile(bs, [2.5, 97.5])
    from scipy.stats import norm
    p = 2 * (1 - norm.cdf(abs(est) / se)) if se > 0 else np.nan
    iid_se = d[col].std(ddof=1) / math.sqrt(n)
    deff = (se / iid_se) ** 2 if iid_se > 0 else np.nan
    return dict(est=est, lo=lo, hi=hi, se=se, p=p, n=n, deff=deff)


def boot_slope(df, xcol, ycol, zcol=None, Lb=4, reps=2000, seed=7):
    """OLS slope of y on x (optionally controlling for z) with per-day sufficient statistics."""
    cols = ["day", xcol, ycol] + ([zcol] if zcol else [])
    d = df[cols].dropna().copy()
    n = len(d)
    if n < 30:
        return dict(est=np.nan, lo=np.nan, hi=np.nan, se=np.nan, p=np.nan, n=n)
    x = d[xcol].values; y = d[ycol].values
    d["one"] = 1.0
    d["x"] = x; d["y"] = y; d["xx"] = x * x; d["xy"] = x * y
    agg = ["one", "x", "y", "xx", "xy"]
    if zcol:
        z = d[zcol].values
        d["z"] = z; d["zz"] = z * z; d["xz"] = x * z; d["zy"] = z * y
        agg += ["z", "zz", "xz", "zy"]
    g = d.groupby("day")[agg].sum().sort_index()
    A = g.values  # days x k

    def slope(T):
        # T: (..., k) sums
        if zcol is None:
            nn, sx, sy, sxx, sxy = [T[..., i] for i in range(5)]
            vx = sxx - sx * sx / nn
            cxy = sxy - sx * sy / nn
            return cxy / vx
        nn, sx, sy, sxx, sxy, sz, szz, sxz, szy = [T[..., i] for i in range(9)]
        vx = sxx - sx * sx / nn; vz = szz - sz * sz / nn; cxz = sxz - sx * sz / nn
        cxy = sxy - sx * sy / nn; czy = szy - sz * sy / nn
        det = vx * vz - cxz * cxz
        return (vz * cxy - cxz * czy) / det

    est = float(slope(A.sum(0)))
    rng = np.random.default_rng(seed)
    idx = _boot_idx(len(A), Lb, reps, rng)
    bs = slope(A[idx].sum(1))
    se = bs.std(ddof=1)
    lo, hi = np.percentile(bs, [2.5, 97.5])
    from scipy.stats import norm
    p = 2 * (1 - norm.cdf(abs(est) / se)) if se > 0 else np.nan
    return dict(est=est, lo=lo, hi=hi, se=se, p=p, n=n)


def wilson(k, n, z=1.96):
    if n <= 0:
        return (np.nan, np.nan)
    ph = k / n
    den = 1 + z * z / n
    cen = (ph + z * z / (2 * n)) / den
    hw = z * math.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / den
    return (cen - hw, cen + hw)


def holm(ps):
    ps = np.asarray(ps, float)
    m = np.sum(np.isfinite(ps))
    o = np.argsort(np.where(np.isfinite(ps), ps, np.inf))
    adj = np.full(len(ps), np.nan)
    run = 0.0
    for r, i in enumerate(o):
        if not np.isfinite(ps[i]):
            continue
        v = min(1.0, (m - r) * ps[i])
        run = max(run, v)
        adj[i] = run
    return adj


def bh(ps):
    ps = np.asarray(ps, float)
    fin = np.isfinite(ps)
    m = fin.sum()
    adj = np.full(len(ps), np.nan)
    o = np.argsort(np.where(fin, ps, np.inf))[:m]
    vals = ps[o] * m / (np.arange(m) + 1)
    vals = np.minimum.accumulate(vals[::-1])[::-1]
    adj[o] = np.minimum(vals, 1.0)
    return adj


def fmt(r, k=3, pct=False):
    if r is None or not np.isfinite(r.get("est", np.nan)):
        return "n/a"
    f = 100.0 if pct else 1.0
    return f"{r['est']*f:+.{k}f} [{r['lo']*f:+.{k}f}, {r['hi']*f:+.{k}f}]"
