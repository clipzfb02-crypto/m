"""E2_signals features and signal states. Every value at index t uses bars <= t only.
Pivots become usable at their confirmation bar (i + P). See the pre-registration A2-A4.
"""
import numpy as np
import pandas as pd

P = 3          # pivot half-width
L_MOM = 20     # momentum lookback
W_SWEEP = 12   # sweep-event window (bars)
K_BAL = 3      # BALANCED persistence
N_SWING = 5    # unswept swing levels kept per side
CAP = 10.0     # distance cap (ATR)
L_TSMOM = 48


def wilder_atr(h, l, c, n=14):
    pc = np.r_[np.nan, c[:-1]]
    tr = np.nanmax(np.vstack([h - l, np.abs(h - pc), np.abs(l - pc)]), axis=0)
    a = np.full(len(tr), np.nan)
    if len(tr) < n:
        return a
    a[n - 1] = tr[:n].mean()
    for i in range(n, len(tr)):
        a[i] = (a[i - 1] * (n - 1) + tr[i]) / n
    return a


def ema(x, n):
    return pd.Series(x).ewm(span=n, adjust=False).mean().values


def confirmed_pivots(h, l):
    """ph_conf[t] = level of a swing high whose pivot bar is t-P (known at close of t), else nan."""
    n = len(h)
    ph = np.full(n, np.nan)
    pl = np.full(n, np.nan)
    for i in range(P, n - P):
        hi = h[i]
        if hi > h[i - P:i].max() and hi >= h[i + 1:i + P + 1].max():
            ph[i + P] = hi
        lo = l[i]
        if lo < l[i - P:i].min() and lo <= l[i + 1:i + P + 1].min():
            pl[i + P] = lo
    return ph, pl


def prior_period_levels(sess_key, h, l):
    """For each bar, high/low of the previous complete period (by key). nan for the first period."""
    k = pd.Series(sess_key)
    df = pd.DataFrame({"k": k, "h": h, "l": l})
    g = df.groupby("k", sort=False).agg(h=("h", "max"), l=("l", "min"))
    prev_h = g.h.shift(1)
    prev_l = g.l.shift(1)
    return k.map(prev_h).values.astype(float), k.map(prev_l).values.astype(float)


def compute_features(df):
    o = df.open.values.astype(float)
    h = df.high.values.astype(float)
    l = df.low.values.astype(float)
    c = df.close.values.astype(float)
    n = len(c)
    atr = wilder_atr(h, l, c)
    z = np.full(n, np.nan)
    z[L_MOM:] = (c[L_MOM:] - c[:-L_MOM]) / (atr[L_MOM:] * np.sqrt(L_MOM))
    mom = np.tanh(z)
    e20, e50, e80 = ema(c, 20), ema(c, 50), ema(c, 80)
    htf = np.zeros(n)
    htf[4:] = np.sign(e80[4:] - e80[:-4])
    sess = df.sess.values
    pdh, pdl = prior_period_levels(sess, h, l)
    wk = pd.to_datetime(df.sess).dt.isocalendar()
    wkey = (wk.year.astype(int) * 100 + wk.week.astype(int)).values
    pwh, pwl = prior_period_levels(wkey, h, l)
    ph, pl = confirmed_pivots(h, l)

    struct = np.zeros(n, int)
    bull_brk = np.zeros(n, bool)
    bear_brk = np.zeros(n, bool)
    sw_bull = np.zeros(n, bool)  # sweep-and-reclaim events
    sw_bear = np.zeros(n, bool)
    dol = np.full(n, np.nan)
    d_up = np.full(n, np.nan)
    d_dn = np.full(n, np.nan)

    sh = np.nan; sh_ok = False; sl = np.nan; sl_ok = False; st = 0
    highs = []; lows = []          # unswept confirmed swing levels
    day_start = 0; bull_done = False; bear_done = False
    for t in range(n):
        if t > 0 and sess[t] != sess[t - 1]:
            day_start = t; bull_done = False; bear_done = False
        # newly confirmed pivots
        if not np.isnan(ph[t]):
            sh = ph[t]; sh_ok = True
            highs.append(ph[t])
            if len(highs) > N_SWING:
                highs.pop(0)
        if not np.isnan(pl[t]):
            sl = pl[t]; sl_ok = True
            lows.append(pl[t])
            if len(lows) > N_SWING:
                lows.pop(0)
        # structure breaks on close
        ub = sh_ok and c[t] > sh
        db = sl_ok and c[t] < sl
        if ub:
            sh_ok = False; bull_brk[t] = True
        if db:
            sl_ok = False; bear_brk[t] = True
        if ub and not db:
            st = 1
        elif db and not ub:
            st = -1
        struct[t] = st
        # remove swing levels traded through by this bar
        if highs:
            highs = [x for x in highs if not (h[t] > x)]
        if lows:
            lows = [x for x in lows if not (l[t] < x)]
        # sweep-and-reclaim of prior-day levels (window: bar t and 2 prior bars of the same session day)
        a = max(day_start, t - 2)
        if not np.isnan(pdl[t]) and not bull_done:
            if l[a:t + 1].min() < pdl[t] and c[t] > pdl[t]:
                sw_bull[t] = True; bull_done = True
        if not np.isnan(pdh[t]) and not bear_done:
            if h[a:t + 1].max() > pdh[t] and c[t] < pdh[t]:
                sw_bear[t] = True; bear_done = True
        # DOL distances
        if not np.isnan(atr[t]) and atr[t] > 0:
            ups = [x for x in highs if x > c[t]]
            for x in (pdh[t], pwh[t]):
                if not np.isnan(x) and x > c[t]:
                    ups.append(x)
            dns = [x for x in lows if x < c[t]]
            for x in (pdl[t], pwl[t]):
                if not np.isnan(x) and x < c[t]:
                    dns.append(x)
            du = min(CAP, (min(ups) - c[t]) / atr[t]) if ups else CAP
            dd = min(CAP, (c[t] - max(dns)) / atr[t]) if dns else CAP
            d_up[t] = du; d_dn[t] = dd
            dol[t] = (dd - du) / (dd + du) if (dd + du) > 0 else 0.0

    return dict(o=o, h=h, l=l, c=c, atr=atr, z=z, mom=mom, e20=e20, e50=e50, e80=e80, htf=htf,
                pdh=pdh, pdl=pdl, struct=struct, bull_brk=bull_brk, bear_brk=bear_brk,
                sw_bull=sw_bull, sw_bear=sw_bear, dol=dol, d_up=d_up, d_dn=d_dn)


def _levels(S, buy, strong, strict_buy=False):
    r = np.zeros(len(S), int)
    ok = ~np.isnan(S)
    Sv = np.where(ok, S, 0.0)
    if strict_buy:
        r[Sv > buy] = 1; r[Sv < -buy] = -1
    else:
        r[Sv >= buy] = 1; r[Sv <= -buy] = -1
    r[Sv >= strong] = 2; r[Sv <= -strong] = -2
    r[~ok] = 0
    return r


def raw_states(F):
    n = len(F["c"])
    mom = F["mom"]
    struct = F["struct"].astype(float)
    # C1 STRUCT_MOM
    S1 = 0.5 * struct + 0.5 * mom
    r1 = _levels(S1, 0.5, 0.75, strict_buy=True)
    # C2 SWEEP_RECLAIM
    r2 = np.zeros(n, int)
    eb_bull = -10 ** 9; eb_bear = -10 ** 9; lb_bull = -10 ** 9; lb_bear = -10 ** 9
    for t in range(n):
        if F["sw_bull"][t]:
            eb_bull = t
        if F["sw_bear"][t]:
            eb_bear = t
        if F["bull_brk"][t]:
            lb_bull = t
        if F["bear_brk"][t]:
            lb_bear = t
        bull = (t - eb_bull <= W_SWEEP - 1) and lb_bull >= eb_bull and F["struct"][t] == 1
        bear = (t - eb_bear <= W_SWEEP - 1) and lb_bear >= eb_bear and F["struct"][t] == -1
        m = mom[t] if not np.isnan(mom[t]) else 0.0
        if bull and not bear:
            r2[t] = 2 if m >= 0.5 else 1
        elif bear and not bull:
            r2[t] = -2 if m <= -0.5 else -1
    # C3 DOL_DIR
    r3 = _levels(F["dol"], 0.33, 0.6)
    # C4 COMPOSITE
    S4 = (struct + mom + F["dol"]) / 3.0
    r4 = _levels(S4, 0.4, 0.7)
    return {"C1_STRUCT_MOM": r1, "C2_SWEEP_RECLAIM": r2, "C3_DOL_DIR": r3, "C4_COMPOSITE": r4}


def balanced(r, htf, k=K_BAL):
    n = len(r)
    sg = np.sign(r)
    out = np.zeros(n, int)
    for t in range(k - 1, n):
        d = sg[t]
        if d != 0 and np.all(sg[t - k + 1:t + 1] == d) and htf[t] == d:
            out[t] = r[t]
    return out


def all_states(F):
    raw = raw_states(F)
    S = {}
    for k, r in raw.items():
        S[k + "|FAST"] = r
        S[k + "|BALANCED"] = balanced(r, F["htf"])
    c = F["c"]
    b1 = np.sign(F["e20"] - F["e50"]).astype(int)
    b1[:50] = 0
    b2 = np.zeros(len(c), int)
    b2[L_TSMOM:] = np.sign(c[L_TSMOM:] - c[:-L_TSMOM]).astype(int)
    S["B1_EMA20_50"] = b1
    S["B2_TSMOM48"] = b2
    return S
