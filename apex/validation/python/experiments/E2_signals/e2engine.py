"""E2_signals trade engines and statistics (pre-registration A5-A9)."""
import itertools
import math
import numpy as np
from scipy import stats

RNG_SEED = 20261127


# ----------------------------------------------------------------------------- helpers
def bad_prefix(df):
    """cumulative count of 'bad' bars: guard bars or bars after a > 4 day data gap."""
    bad = (df.guard.values.astype(bool)) | (df.gap_days.values > 4.0)
    return np.r_[0, np.cumsum(bad)]


def spans_bad(cb, a, b):
    """True if any bar in (a, b] is bad (a = entry bar index, b = exit bar index)."""
    return (cb[b + 1] - cb[a + 1]) > 0


def cost_rt(meta, entry, exit_):
    if meta["pct"]:
        return meta["cost_side"] * (entry + exit_)
    return 2.0 * meta["cost_side"]


# ----------------------------------------------------------------------------- primary engine
def onset_trades(state, F, meta, cb, lo, hi, H, entry_from=None):
    """Onset + fixed-horizon trades. Signal at close t in [entry_from, hi), fill O[t+1], exit O[t+1+H] <= hi.
    lo..hi are bar indices (hi exclusive) bounding the segment; exit bar must be < hi."""
    o = F["o"]; atr = F["atr"]
    d = np.sign(state)
    start = lo if entry_from is None else entry_from
    tr = []
    free_at = start  # first signal bar allowed
    for t in range(max(start, 1), hi):
        if t < free_at:
            continue
        if d[t] == 0 or d[t] == d[t - 1]:
            continue
        e = t + 1; x = t + 1 + H
        if x >= hi:
            break
        if spans_bad(cb, e, x) or np.isnan(atr[t]) or atr[t] <= 0:
            continue
        ep, xp = o[e], o[x]
        pnl = d[t] * (xp - ep) - cost_rt(meta, ep, xp)
        tr.append((t, int(d[t]), int(abs(state[t]) == 2), ep, xp, pnl, pnl / ep, pnl / atr[t], x))
        free_at = x  # can signal again at the exit bar's close? exit happens at O[x]; next signal at close >= x
    if not tr:
        return np.zeros((0, 9))
    return np.array(tr, dtype=float)


# ----------------------------------------------------------------------------- state-held engine
def state_held_bar_returns(state, F, meta, cb, lo, hi):
    """p[t]=sign(state[t]) held O[t+1]->O[t+2]. Returns per-bar return array aligned to realisation bar t+2."""
    o = F["o"]
    p = np.sign(state[lo:hi]).astype(float)
    n = hi - lo
    ret = np.zeros(n)
    real_idx = np.arange(lo, hi) + 2
    valid = real_idx < hi
    for j in range(n):
        if not valid[j]:
            break
        t = lo + j
        prev = p[j - 1] if j > 0 else 0.0
        ep, xp = o[t + 1], o[t + 2]
        r = p[j] * (xp - ep)
        if spans_bad(cb, t + 1, t + 2):
            r = 0.0
        c = abs(p[j] - prev) * (meta["cost_side"] * ep if meta["pct"] else meta["cost_side"])
        ret[j] = (r - c) / ep
    return real_idx[valid], ret[valid]


# ----------------------------------------------------------------------------- daily series & metrics
def daily_series(days_all, real_days, rets):
    """Sum returns by session day over the full list of days (zeros where none)."""
    idx = {d: i for i, d in enumerate(days_all)}
    out = np.zeros(len(days_all))
    for d, r in zip(real_days, rets):
        i = idx.get(d)
        if i is not None:
            out[i] += r
    return out


def wilson(k, n, z=1.96):
    if n == 0:
        return (np.nan, np.nan)
    p = k / n
    den = 1 + z * z / n
    cen = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (cen - half, cen + half)


def block_boot_idx(T, B, block, rng):
    nb = int(math.ceil(T / block))
    starts = rng.integers(0, T, size=(B, nb))
    idx = (starts[:, :, None] + np.arange(block)[None, None, :]) % T
    return idx.reshape(B, -1)[:, :T]


def sharpe(x, ann):
    s = x.std(ddof=1) if len(x) > 1 else 0.0
    return 0.0 if s == 0 or not np.isfinite(s) else x.mean() / s * ann


def sharpe_ci(x, ann, B=2000, block=10, seed=RNG_SEED):
    if len(x) < 20 or x.std() == 0:
        return (np.nan, np.nan)
    rng = np.random.default_rng(seed)
    idx = block_boot_idx(len(x), B, block, rng)
    xs = x[idx]
    sd = xs.std(axis=1, ddof=1)
    sr = np.where(sd > 0, xs.mean(axis=1) / np.where(sd > 0, sd, 1) * ann, 0.0)
    return (float(np.percentile(sr, 2.5)), float(np.percentile(sr, 97.5)))


def mean_ci(x, B=2000, block=5, seed=RNG_SEED):
    if len(x) < 10:
        return (np.nan, np.nan)
    rng = np.random.default_rng(seed + 1)
    idx = block_boot_idx(len(x), B, block, rng)
    m = x[idx].mean(axis=1)
    return (float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5)))


def max_dd(daily):
    if len(daily) == 0:
        return 0.0
    cum = np.cumsum(daily)
    peak = np.maximum.accumulate(np.r_[0.0, cum])[1:]
    return float((peak - cum).max())


def trade_metrics(tr, daily, ann, n_days, n_bars, n_neutral):
    n = len(tr)
    m = dict(n=n, days=n_days, trades_per_day=n / n_days if n_days else np.nan,
             pct_neutral=100.0 * n_neutral / n_bars if n_bars else np.nan)
    if n:
        pnl = tr[:, 5]; ret = tr[:, 6]; R = tr[:, 7]
        wins = int((pnl > 0).sum())
        m.update(hit=wins / n, hit_ci=wilson(wins, n), avg_R=float(R.mean()), avg_R_ci=mean_ci(R),
                 avg_bp=float(ret.mean() * 1e4), avg_bp_ci=tuple(np.array(mean_ci(ret)) * 1e4),
                 pf=float(pnl[pnl > 0].sum() / -pnl[pnl < 0].sum()) if (pnl < 0).any() else np.inf,
                 n_long=int((tr[:, 1] > 0).sum()), n_short=int((tr[:, 1] < 0).sum()),
                 n_strong=int(tr[:, 2].sum()))
    else:
        m.update(hit=np.nan, hit_ci=(np.nan, np.nan), avg_R=np.nan, avg_R_ci=(np.nan, np.nan), avg_bp=np.nan,
                 avg_bp_ci=(np.nan, np.nan), pf=np.nan, n_long=0, n_short=0, n_strong=0)
    m["sharpe"] = sharpe(daily, ann)
    m["sharpe_ci"] = sharpe_ci(daily, ann)
    m["maxdd_pct"] = 100.0 * max_dd(daily)
    m["total_ret_pct"] = 100.0 * float(daily.sum())
    return m


# ----------------------------------------------------------------------------- random-entry baseline
def random_entry_pvalue(F, meta, cb, lo, hi, H, n_long, n_short, obs_mean, B=2000, seed=RNG_SEED):
    o = F["o"]; atr = F["atr"]
    ts = np.arange(max(lo, 1), hi - H - 1)
    ok = np.array([not spans_bad(cb, t + 1, t + 1 + H) and np.isfinite(atr[t]) for t in ts], bool)
    ts = ts[ok]
    if len(ts) == 0 or (n_long + n_short) == 0:
        return np.nan, np.nan, np.nan
    ep = o[ts + 1]; xp = o[ts + 1 + H]
    cst = np.array([cost_rt(meta, a, b) for a, b in zip(ep, xp)])
    fl = ((xp - ep) - cst) / ep
    fs = ((ep - xp) - cst) / ep
    rng = np.random.default_rng(seed + 7)
    tot = np.zeros(B)
    if n_long:
        tot += fl[rng.integers(0, len(ts), size=(B, n_long))].sum(axis=1)
    if n_short:
        tot += fs[rng.integers(0, len(ts), size=(B, n_short))].sum(axis=1)
    means = tot / (n_long + n_short)
    p = float((np.sum(means >= obs_mean) + 1) / (B + 1))
    return p, float(np.percentile(means, 95) * 1e4), float(means.mean() * 1e4)


# ----------------------------------------------------------------------------- DSR / PBO / BH
def deflated_sharpe(daily, sr_trials, N):
    """daily: per-period returns of the chosen strategy; sr_trials: per-period (non-annualised) SRs of all trials."""
    T = len(daily)
    if T < 10 or daily.std(ddof=1) == 0:
        return np.nan, np.nan
    sr = daily.mean() / daily.std(ddof=1)
    g3 = stats.skew(daily)
    g4 = stats.kurtosis(daily, fisher=False)
    V = np.var(sr_trials, ddof=1)
    em = 0.5772156649
    sr0 = math.sqrt(V) * ((1 - em) * stats.norm.ppf(1 - 1.0 / N) + em * stats.norm.ppf(1 - 1.0 / (N * math.e)))
    den = 1 - g3 * sr + (g4 - 1) / 4.0 * sr * sr
    if den <= 0:
        return np.nan, sr0
    z = (sr - sr0) * math.sqrt(T - 1) / math.sqrt(den)
    return float(stats.norm.cdf(z)), float(sr0)


def pbo_cscv(M, S=16):
    """M: T x N daily returns. Returns PBO and the median logit."""
    T, N = M.shape
    bl = T // S
    if bl < 2 or N < 2:
        return np.nan, np.nan
    M = M[:bl * S]
    B1 = M.reshape(S, bl, N).sum(axis=1)
    B2 = (M ** 2).reshape(S, bl, N).sum(axis=1)
    combos = np.array([c for c in itertools.combinations(range(S), S // 2)])
    mask = np.zeros((len(combos), S))
    mask[np.arange(len(combos))[:, None], combos] = 1.0
    cnt = bl * S // 2

    def sr(mk):
        s1 = mk @ B1; s2 = mk @ B2
        mu = s1 / cnt
        var = s2 / cnt - mu ** 2
        sd = np.sqrt(np.maximum(var, 0))
        return np.where(sd > 0, mu / np.where(sd > 0, sd, 1), 0.0)

    is_sr = sr(mask); oos_sr = sr(1.0 - mask)
    best = is_sr.argmax(axis=1)
    oos_best = oos_sr[np.arange(len(combos)), best]
    rank = (oos_sr < oos_best[:, None]).sum(axis=1) + 0.5 * ((oos_sr == oos_best[:, None]).sum(axis=1) - 1) + 1
    w = rank / (N + 1)
    lam = np.log(w / (1 - w))
    return float((lam <= 0).mean()), float(np.median(lam))


def bh(pvals, q=0.10):
    p = np.asarray(pvals, float)
    ok = np.isfinite(p)
    res = np.zeros(len(p), bool)
    if ok.sum() == 0:
        return res
    pv = p[ok]; m = len(pv)
    order = np.argsort(pv)
    thr = q * (np.arange(1, m + 1)) / m
    passed = pv[order] <= thr
    kmax = np.max(np.where(passed)[0]) + 1 if passed.any() else 0
    sel = np.zeros(m, bool)
    sel[order[:kmax]] = True
    res[np.where(ok)[0]] = sel
    return res


def holm(pvals, alpha=0.05):
    p = np.asarray(pvals, float)
    ok = np.isfinite(p)
    res = np.zeros(len(p), bool)
    pv = p[ok]; m = len(pv)
    order = np.argsort(pv)
    sel = np.zeros(m, bool)
    for i, j in enumerate(order):
        if pv[j] <= alpha / (m - i):
            sel[j] = True
        else:
            break
    res[np.where(ok)[0]] = sel
    return res
