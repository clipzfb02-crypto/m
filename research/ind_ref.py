"""Reference implementation with indicator semantics (mirrors pine/MNQ_5m_ORB_Signals.pine): entry at signal-bar close, stop = OR opposite side,
target = entry +/- tpR*risk, managed from the next bar (stop checked first), EOD exit at close."""
import numpy as np, pandas as pd
def indicator_ref(df, or_minutes=15, body_min=0.8, entry_end=720, tp_r=0.5, flat_min=950, cost=1.5):
    o, h, l, c = [df[k].values.astype(float) for k in ('open','high','low','close')]
    t = df.index; mins = np.asarray(t.hour*60 + t.minute); day = np.asarray(t.normalize())
    n = len(c); orh = orl = np.nan; done = False; cur = None
    tdir = 0; te = ts = tt = np.nan; tb = -1
    sig = np.zeros(n, int); trades = []
    for i in range(n):
        if day[i] != cur:  # calendar-day reset (OR only uses 09:30+ bars, so equivalent to 18:00 reset)
            cur = day[i]; orh = orl = np.nan; done = False
        m = mins[i]; out_of_day = m >= flat_min or m < 570
        if tdir != 0 and i > tb:
            xp = np.nan; why = ''
            if tdir == 1:
                if l[i] <= ts: xp = min(o[i], ts); why = 'SL'
                elif h[i] >= tt: xp = max(o[i], tt); why = 'TP'
            else:
                if h[i] >= ts: xp = max(o[i], ts); why = 'SL'
                elif l[i] <= tt: xp = min(o[i], tt); why = 'TP'
            if np.isnan(xp) and out_of_day: xp = c[i]; why = 'EOD'
            if not np.isnan(xp):
                trades.append((tb, i, tdir, te, xp, why, (xp-te)*tdir - cost)); tdir = 0
        if 570 <= m < 570 + or_minutes:
            orh = h[i] if np.isnan(orh) else max(orh, h[i]); orl = l[i] if np.isnan(orl) else min(orl, l[i])
        rngb = max(h[i]-l[i], 0.25)
        can = (not done) and tdir == 0 and not np.isnan(orh) and m >= 570 + or_minutes and m <= entry_end
        bull = can and c[i] > orh and (c[i]-l[i])/rngb >= body_min
        bear = can and c[i] < orl and (h[i]-c[i])/rngb >= body_min
        if bull or bear:
            done = True; d = 1 if bull else -1
            risk = c[i]-orl if bull else orh-c[i]
            tdir = d; te = c[i]; ts = orl if bull else orh; tt = c[i] + d*max(1, np.floor(tp_r*risk/0.25 + 1e-6))*0.25; tb = i; sig[i] = d
    return sig, pd.DataFrame(trades, columns=['sig_i','exit_i','dir','entry','exit','why','pnl'])
