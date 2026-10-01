"""TradingView-equivalent indicators + broker-emulator style trade simulator."""
import numpy as np, pandas as pd
from numba import njit

# ---------------- TV-equivalent indicators ----------------
@njit(cache=True)
def _ema_seeded(x, n, alpha):
    out = np.full(x.shape[0], np.nan)
    s = 0.0; cnt = 0; prev = np.nan
    for i in range(x.shape[0]):
        v = x[i]
        if np.isnan(prev):
            # seed with SMA of first n valid values
            if not np.isnan(v):
                s += v; cnt += 1
                if cnt == n:
                    prev = s / n; out[i] = prev
        else:
            if not np.isnan(v):
                prev = alpha * v + (1 - alpha) * prev
            out[i] = prev
    return out

def ema(x, n):  return _ema_seeded(np.asarray(x, float), n, 2.0 / (n + 1))
def rma(x, n):  return _ema_seeded(np.asarray(x, float), n, 1.0 / n)
def sma(x, n):  return pd.Series(x).rolling(n).mean().values

def rsi(c, n):
    ch = np.diff(c, prepend=np.nan)
    u = np.where(np.isnan(ch), np.nan, np.maximum(ch, 0)); d = np.where(np.isnan(ch), np.nan, np.maximum(-ch, 0))
    ru, rd = rma(u, n), rma(d, n)
    with np.errstate(divide='ignore', invalid='ignore'):
        r = np.where(rd == 0, 100.0, np.where(ru == 0, 0.0, 100 - 100 / (1 + ru / rd)))
    r[np.isnan(ru) | np.isnan(rd)] = np.nan
    return r

def true_range(h, l, c):
    pc = np.roll(c, 1); pc[0] = np.nan
    tr = np.maximum(h - l, np.maximum(np.abs(h - pc), np.abs(l - pc)))
    tr[0] = h[0] - l[0]
    return tr

def atr(h, l, c, n): return rma(true_range(h, l, c), n)

def dmi(h, l, c, n, sm):
    up = np.diff(h, prepend=np.nan); dn = -np.diff(l, prepend=np.nan)
    pdm = np.where((up > dn) & (up > 0), up, 0.0); mdm = np.where((dn > up) & (dn > 0), dn, 0.0)
    pdm[0] = np.nan; mdm[0] = np.nan
    tr = rma(true_range(h, l, c), n)
    p = 100 * rma(pdm, n) / tr; m = 100 * rma(mdm, n) / tr
    s = p + m
    a = 100 * rma(np.abs(p - m) / np.where(s == 0, 1, s), sm)
    return p, m, a

def session_vwap(df):
    """VWAP of hlc3 anchored to CME trading-day start (18:00 ET)."""
    tday = (df.index + pd.Timedelta(hours=6)).normalize()  # 18:00 ET -> next calendar day
    hlc3 = (df.high + df.low + df.close) / 3
    pv = (hlc3 * df.volume).groupby(tday).cumsum(); vv = df.volume.groupby(tday).cumsum()
    v = (pv / vv.replace(0, np.nan)).values
    return pd.Series(v, index=df.index).ffill().values, np.asarray(tday)

def htf_ema(df, rule, n, src='close'):
    """request.security(tf, ta.ema(close,n)[1], lookahead_on): last *completed* HTF bar value."""
    h = df[src].resample(rule, label='left', closed='left').last().dropna()
    e = pd.Series(ema(h.values, n), index=h.index).shift(1)
    key = df.index.floor(rule)
    return e.reindex(key).values

def htf_close_prev(df, rule):
    h = df['close'].resample(rule, label='left', closed='left').last().dropna().shift(1)
    return h.reindex(df.index.floor(rule)).values

# ---------------- simulator ----------------
@njit(cache=True)
def simulate(o, h, l, c, sig, sl_pts, tp_pts, be_pts, flat, allow_entry, max_bars, conservative):
    """sig: +1 long / -1 short decided on bar close -> market fill at next bar open.
    sl_pts/tp_pts/be_pts: distances (points) from fill price, taken from the signal bar.
    be_pts>0: once price has reached +be_pts, stop moves to entry (effective next bar).
    flat[i]: close all at next bar open (EOD). Returns trades array."""
    n = o.shape[0]
    out = np.zeros((n, 7))  # entry_idx, exit_idx, dir, entry, exit, reason, mfe
    k = 0; pos = 0; ep = 0.0; sp = 0.0; tp = 0.0; ei = 0; be_armed = False; bep = 0.0; mfe = 0.0
    pend = 0; psl = 0.0; ptp = 0.0; pbe = 0.0
    for i in range(n):
        # fill pending entry at this bar's open
        if pend != 0 and pos == 0:
            pos = pend; ep = o[i]; ei = i
            sp = ep - pos * psl; tp = ep + pos * ptp
            be_armed = False; bep = pbe; mfe = 0.0
        pend = 0
        if pos != 0:
            exited = False; xp = 0.0; reason = 0
            # EOD flat from previous bar decision is handled below via flat[i-1]
            if i > ei and flat[i - 1]:
                xp = o[i]; reason = 3; exited = True
            else:
                # gap through stop/target at open
                if pos == 1:
                    hit_sl = l[i] <= sp; hit_tp = h[i] >= tp
                else:
                    hit_sl = h[i] >= sp; hit_tp = l[i] <= tp
                if hit_sl and hit_tp:
                    if conservative:
                        first_sl = True
                    else:
                        # TV emulator path: open closer to high -> O,H,L,C
                        up_first = (h[i] - o[i]) < (o[i] - l[i])
                        first_sl = (pos == 1 and not up_first) or (pos == -1 and up_first)
                    if first_sl:
                        xp = sp; reason = 1
                    else:
                        xp = tp; reason = 2
                    exited = True
                elif hit_sl:
                    xp = sp; reason = 1; exited = True
                elif hit_tp:
                    xp = tp; reason = 2; exited = True
                if exited:
                    # gap handling: fill at open if open already beyond level
                    if reason == 1 and ((pos == 1 and o[i] < sp) or (pos == -1 and o[i] > sp)):
                        xp = o[i]
                    if reason == 2 and ((pos == 1 and o[i] > tp) or (pos == -1 and o[i] < tp)):
                        xp = o[i]
            fav = (h[i] - ep) if pos == 1 else (ep - l[i])
            if fav > mfe: mfe = fav
            if not exited and max_bars > 0 and i - ei + 1 >= max_bars:
                xp = c[i]; reason = 4; exited = True
            if exited:
                out[k, 0] = ei; out[k, 1] = i; out[k, 2] = pos; out[k, 3] = ep; out[k, 4] = xp
                out[k, 5] = reason; out[k, 6] = mfe; k += 1
                pos = 0
            else:
                if bep > 0 and not be_armed and mfe >= bep:
                    be_armed = True
                    if pos == 1 and sp < ep: sp = ep
                    if pos == -1 and sp > ep: sp = ep
        if pos == 0 and sig[i] != 0 and allow_entry[i] and i + 1 < n:
            pend = sig[i]; psl = sl_pts[i]; ptp = tp_pts[i]; pbe = be_pts[i]
    return out[:k]

def stats(tr, cost_pts=1.5, pv=2.0, label=''):
    if len(tr) == 0:
        return dict(label=label, n=0)
    pnl = (tr[:, 4] - tr[:, 3]) * tr[:, 2] - cost_pts
    w = pnl > 0
    gp, gl = pnl[w].sum(), -pnl[~w].sum()
    eq = np.cumsum(pnl); dd = (np.maximum.accumulate(eq) - eq).max()
    return dict(label=label, n=len(pnl), win=round(100 * w.mean(), 1), pf=round(gp / gl if gl > 0 else np.inf, 2),
                net_pts=round(pnl.sum(), 1), net_usd_1mnq=round(pnl.sum() * pv, 0), avg=round(pnl.mean(), 2),
                maxdd_pts=round(dd, 1), avgW=round(pnl[w].mean() if w.any() else 0, 1), avgL=round(pnl[~w].mean() if (~w).any() else 0, 1))
