"""Reproduces every number in the top-level README.

    ./fetch_data.sh && python prepare_data.py && python backtest.py
"""
import numpy as np, pandas as pd
from pathlib import Path
from bt import stats
from final_ref import orb_strategy
from ind_ref import indicator_ref

DATA = Path(__file__).parent / 'data'
COST = 1.5          # round-trip points (= $3 per MNQ contract): commission + slippage
PV = 2.0            # MNQ $ per point
pd.set_option('display.width', 200)


def row(label, pnl_pts):
    p = np.asarray(pnl_pts, float)
    if len(p) == 0:
        return dict(period=label, trades=0)
    w = p > 0
    eq = np.cumsum(p); dd = (np.maximum.accumulate(eq) - eq).max()
    return dict(period=label, trades=len(p), win_rate=f'{100 * w.mean():.1f}%',
                profit_factor=round(p[w].sum() / -p[~w].sum(), 2), net_usd_1_mnq=round(p.sum() * PV),
                avg_trade_usd=round(p.mean() * PV, 2), max_dd_usd=round(dd * PV))


def by_year(df, tr):
    pnl = (tr[:, 4] - tr[:, 3]) * tr[:, 2] - COST
    yrs = df.index.year.values[tr[:, 0].astype(int)]
    out = [row(str(y), pnl[yrs == y]) for y in sorted(set(yrs)) if (yrs == y).sum() > 10]
    m = yrs >= 2023
    out.append(row('2023-2025 total', pnl[m]))
    return out


def main():
    nq = pd.read_pickle(DATA / 'nq5_2023_2025.pkl')
    nq26 = pd.read_pickle(DATA / 'nq5_2026_holdout.pkl')
    mnq26 = pd.read_pickle(DATA / 'mnq5_2026_holdout.pkl')

    print('\n=== Strategy-Tester semantics (fill next bar open), default settings, 1 contract, 1.5 pts cost ===')
    tr, _, _ = orb_strategy(nq)
    rows = by_year(nq, tr)
    t, _, _ = orb_strategy(nq26); rows.append(row('2026 holdout (NQ, Feb 17 - Apr 28)', (t[:, 4] - t[:, 3]) * t[:, 2] - COST))
    t, _, _ = orb_strategy(mnq26); rows.append(row('2026 holdout (MNQ, Mar 5 - May 1)', (t[:, 4] - t[:, 3]) * t[:, 2] - COST))
    print(pd.DataFrame(rows).to_string(index=False))

    print('\n=== Indicator semantics (entry at signal close) - what the stats table shows ===')
    _, T = indicator_ref(nq)
    ty = nq.index[T.sig_i.values].year
    rows = [row(str(y), T.pnl[ty == y]) for y in (2023, 2024, 2025)] + [row('2023-2025 total', T.pnl[ty >= 2023])]
    print(pd.DataFrame(rows).to_string(index=False))

    print('\n=== Take-profit setting trade-off (Strategy-Tester semantics) ===')
    rows = []
    for r in (0.4, 0.5, 0.75, 1.0):
        a, _, _ = orb_strategy(nq, tp_r=r); b, _, _ = orb_strategy(nq26, tp_r=r)
        pa = (a[:, 4] - a[:, 3]) * a[:, 2] - COST; pb = (b[:, 4] - b[:, 3]) * b[:, 2] - COST
        pa = pa[nq.index.year.values[a[:, 0].astype(int)] >= 2023]
        ra = row(f'TP {r}R 2023-25', pa); rb = row('2026', pb)
        rows.append({**ra, 'holdout_2026_win': rb['win_rate'], 'holdout_2026_pf': rb['profit_factor']})
    print(pd.DataFrame(rows).to_string(index=False))

    print('\n=== Robustness: profit factor in 2023-24 (design) / 2025 (validation) for neighbouring settings ===')
    yrs = nq.index.year.values
    grid = []
    for orm in (10, 15, 20):
        for body in (0.7, 0.8, 0.9):
            for r in (0.5, 0.75, 1.0):
                tr, _, _ = orb_strategy(nq, or_minutes=orm, body_min=body, tp_r=r)
                pnl = (tr[:, 4] - tr[:, 3]) * tr[:, 2] - COST; y = yrs[tr[:, 0].astype(int)]
                f = lambda p: round(p[p > 0].sum() / -p[p < 0].sum(), 2)
                grid.append(dict(or_min=orm, body=body, tp_r=r, pf_2023_24=f(pnl[(y >= 2023) & (y <= 2024)]), pf_2025=f(pnl[y == 2025])))
    g = pd.DataFrame(grid)
    print(g.pivot_table(index=['or_min', 'body'], columns='tp_r', values=['pf_2023_24', 'pf_2025']).to_string())

    print('\n=== Stress: cost per round trip ===')
    tr, _, _ = orb_strategy(nq)
    raw = (tr[:, 4] - tr[:, 3]) * tr[:, 2]; m = yrs[tr[:, 0].astype(int)] >= 2023
    print(pd.DataFrame([row(f'cost {c} pts (${c * PV:.0f})', raw[m] - c) for c in (1.5, 2.5, 3.5)]).to_string(index=False))

    tr, _, _ = orb_strategy(nq)
    pnl = (tr[:, 4] - tr[:, 3]) * tr[:, 2] - COST; idx = nq.index[tr[:, 0].astype(int)]
    mon = pd.Series(pnl * PV, index=idx)[idx.year >= 2023]
    mon = mon.groupby(mon.index.to_period('M')).sum()
    print(f'\nProfitable months 2023-2025: {(mon > 0).sum()} / {len(mon)}   worst month ${mon.min():,.0f}   best month ${mon.max():,.0f}')
    _, sig, sl = orb_strategy(nq)
    risk = sl[(sig != 0) & (nq.index.year >= 2023)]
    print('Stop distance per trade (points): median %.1f, 90th percentile %.1f  (x $2 = risk per MNQ contract)' % (np.median(risk), np.percentile(risk, 90)))

if __name__ == '__main__':
    main()
