"""Reference implementation of the final rules with Strategy-Tester semantics (fill at next bar open).
Mirrors pine/MNQ_5m_ORB_Strategy.pine. Returns (trades, signal per bar, stop distance per signal bar)."""
import numpy as np, pandas as pd
from bt import simulate, stats

def liquidity_levels(df):
    """Liquidity levels known at each bar's close (mirrors the Pine scripts):
    PDH/PDL = previous regular session (09:30-16:00 NY) high/low, rolled at the first regular-hours bar;
    ONH/ONL = overnight (18:00-09:30 NY) high/low, reset at the first bar at/after 18:00;
    RH/RL   = today's regular-hours high/low so far (including the current bar)."""
    h = df.high.values.astype(float); l = df.low.values.astype(float)
    t = df.index; mins = np.asarray(t.hour * 60 + t.minute); n = len(h)
    out = {k: np.full(n, np.nan) for k in ('PDH', 'PDL', 'ONH', 'ONL', 'RH', 'RL')}
    rh = rl = pdh = pdl = onh = onl = np.nan
    prev_rth = False; prev_min = None
    for i in range(n):
        m = mins[i]; is_rth = 570 <= m < 960; is_on = m >= 1080 or m < 570
        if is_rth and not prev_rth:
            if not np.isnan(rh): pdh, pdl = rh, rl
            rh = rl = np.nan
        if m >= 1080 and (prev_min is None or prev_min < 1080):
            onh = onl = np.nan
        if is_on:
            onh = h[i] if np.isnan(onh) else max(onh, h[i]); onl = l[i] if np.isnan(onl) else min(onl, l[i])
        if is_rth:
            rh = h[i] if np.isnan(rh) else max(rh, h[i]); rl = l[i] if np.isnan(rl) else min(rl, l[i])
        out['PDH'][i], out['PDL'][i], out['ONH'][i], out['ONL'][i], out['RH'][i], out['RL'][i] = pdh, pdl, onh, onl, rh, rl
        prev_rth = is_rth; prev_min = m
    lt = lambda a, b: (~np.isnan(a)) & (~np.isnan(b)) & (a < b)
    out['SSL_SWEPT'] = lt(out['RL'], out['ONL']) | lt(out['RL'], out['PDL'])   # sell-side liquidity taken today
    out['BSL_SWEPT'] = lt(out['ONH'], out['RH']) | lt(out['PDH'], out['RH'])   # buy-side liquidity taken today
    return out


def orb_strategy(df, or_minutes=15, body_min=0.8, last_entry=(12, 0), tp_r=0.2, flat_at=(15, 50),
                 max_risk_pts=0.0, cost_pts=1.5, long_ok=True, short_ok=True, require_sweep=False):
    o, h, l, c = [df[k].values.astype(float) for k in ('open', 'high', 'low', 'close')]
    t = df.index; mins = np.asarray(t.hour * 60 + t.minute)
    tday = np.asarray((t + pd.Timedelta(hours=6)).normalize())
    n = len(c)
    liq = liquidity_levels(df) if require_sweep else None
    sig = np.zeros(n, np.int64); sl = np.zeros(n); tp = np.zeros(n)
    orh = orl = np.nan; traded = False; cur = None
    or_start, or_end = 570, 570 + or_minutes
    cut = last_entry[0] * 60 + last_entry[1]
    for i in range(n):
        if tday[i] != cur:
            cur = tday[i]; orh = np.nan; orl = np.nan; traded = False
        m = mins[i]
        if or_start <= m < or_end:
            orh = h[i] if np.isnan(orh) else max(orh, h[i])
            orl = l[i] if np.isnan(orl) else min(orl, l[i])
            continue
        if traded or np.isnan(orh) or m < or_end or m > cut:
            continue
        rngb = max(h[i] - l[i], 0.25)
        up = c[i] > orh and (c[i] - l[i]) / rngb >= body_min
        dn = c[i] < orl and (h[i] - c[i]) / rngb >= body_min
        if up or dn:
            traded = True   # first qualifying breakout of the day only
            d = 1 if up else -1
            risk = (c[i] - orl) if d == 1 else (orh - c[i])
            if (d == 1 and not long_ok) or (d == -1 and not short_ok): continue
            if max_risk_pts > 0 and risk > max_risk_pts: continue
            if require_sweep and not (liq['SSL_SWEPT'][i] if d == 1 else liq['BSL_SWEPT'][i]): continue
            sig[i] = d; sl[i] = risk; tp[i] = max(1, np.floor(risk * tp_r / 0.25 + 1e-6)) * 0.25
    last_of_day = np.r_[tday[1:] != tday[:-1], True]
    flat = (mins >= flat_at[0] * 60 + flat_at[1]) | (mins < 570) | last_of_day
    allow = np.ones(n, bool)
    tr = simulate(o, h, l, c, sig, sl, tp, np.zeros(n), flat, allow, 0, True)
    return tr, sig, sl

def summarize(df, tr, cost_pts=1.5, label=''):
    yrs = df.index.year.values[tr[:, 0].astype(int)]
    rows = []
    for y in sorted(set(yrs)):
        s = stats(tr[yrs == y], cost_pts=cost_pts); s['label'] = f'{label} {y}'; rows.append(s)
    s = stats(tr, cost_pts=cost_pts); s['label'] = f'{label} ALL'; rows.append(s)
    return pd.DataFrame(rows)
