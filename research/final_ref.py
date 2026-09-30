"""Reference implementation of the final rules with Strategy-Tester semantics (fill at next bar open).
Mirrors pine/MNQ_5m_ORB_Strategy.pine. Returns (trades, signal per bar, stop distance per signal bar)."""
import numpy as np, pandas as pd
from bt import simulate, stats

def orb_strategy(df, or_minutes=15, body_min=0.8, last_entry=(12, 0), tp_r=0.5, flat_at=(15, 50),
                 max_risk_pts=0.0, cost_pts=1.5, long_ok=True, short_ok=True):
    o, h, l, c = [df[k].values.astype(float) for k in ('open', 'high', 'low', 'close')]
    t = df.index; mins = np.asarray(t.hour * 60 + t.minute)
    tday = np.asarray((t + pd.Timedelta(hours=6)).normalize())
    n = len(c)
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
