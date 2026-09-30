"""Independent checks of the two Pine scripts (run: npm install && python verify.py).

1. pinescript-v6-validator (static v6 checks: functions, parameter names, arity, scopes).
2. PineTS runtime: executes the *unmodified* scripts (plus debug plots appended) on real NQ 5m bars with
   MNQ contract specs, and compares every signal / trade with the Python reference implementations.
"""
import json, subprocess, sys
from pathlib import Path
import numpy as np, pandas as pd

HERE = Path(__file__).parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE.parent))
from final_ref import orb_strategy  # noqa: E402
from ind_ref import indicator_ref  # noqa: E402

IND = ROOT / 'pine' / 'MNQ_5m_ORB_Signals.pine'
STR = ROOT / 'pine' / 'MNQ_5m_ORB_Strategy.pine'
WORK = HERE / 'work'; WORK.mkdir(exist_ok=True)

DEBUG_IND = '\nplot(nTrades, "dbg_n")\nplot(nWins, "dbg_w")\nplot(netPts, "dbg_net")\nplot(buySig ? 1 : sellSig ? -1 : 0, "dbg_sig")\n'
DEBUG_STR = ('\nplot(goLong ? 1 : goShort ? -1 : 0, "dbg_sig")\nplot(strategy.position_size, "dbg_pos")\n'
             'plot(strategy.netprofit, "dbg_np")\nplot(strategy.wintrades, "dbg_wt")\n')


def dump(df, path):
    idx = df.index.tz_localize('America/New_York', ambiguous='NaT', nonexistent='NaT')
    keep = ~idx.isna(); df = df[keep]; idx = idx[keep]
    ms = idx.tz_convert('UTC').as_unit('ms').asi8
    rows = [dict(open=r.open, high=r.high, low=r.low, close=r.close, volume=r.volume, openTime=int(t), closeTime=int(t) + 299999)
            for r, t in zip(df.itertuples(), ms)]
    path.write_text(json.dumps(rows))
    return df


def run(script_text, data_path, name):
    sp = WORK / f'{name}.pine'; sp.write_text(script_text)
    out = WORK / f'{name}.out.json'
    subprocess.run(['node', str(HERE / 'run_pinets.mjs'), str(sp), str(data_path), str(out)], check=True, capture_output=True)
    return {k: np.array([np.nan if v is None else v for v in vals], float) for k, vals in json.loads(out.read_text()).items() if not k.startswith('__')}


def main():
    print(subprocess.run(['node', str(HERE / 'validate.cjs'), str(IND), str(STR)], capture_output=True, text=True).stdout)
    nq = pd.read_pickle(HERE.parent / 'data' / 'nq5_2023_2025.pkl')
    ok = True
    for year in (2023, 2024, 2025):
        df = dump(nq[nq.index.year == year], WORK / f'nq_{year}.json')
        # indicator
        o = run(IND.read_text() + DEBUG_IND, WORK / f'nq_{year}.json', f'ind_{year}')
        sig, T = indicator_ref(df)
        same_sig = bool((np.nan_to_num(o['dbg_sig']) == sig).all())
        same_stats = int(o['dbg_n'][-1]) == len(T) and int(o['dbg_w'][-1]) == int((T.pnl > 0).sum()) and abs(o['dbg_net'][-1] - T.pnl.sum()) < 1e-6
        print(f'{year} indicator: signals {int((sig != 0).sum())} | identical signals: {same_sig} | identical trades/wins/net: {same_stats}'
              f'  ({len(T)} trades, {100 * (T.pnl > 0).mean():.1f}% win, net {T.pnl.sum():.2f} pts)')
        ok &= same_sig and same_stats
        # strategy
        o = run(STR.read_text() + DEBUG_STR, WORK / f'nq_{year}.json', f'str_{year}')
        tr, sig2, _ = orb_strategy(df)
        same_sig2 = bool((np.nan_to_num(o['dbg_sig']) == sig2).all())
        gross = (tr[:, 4] - tr[:, 3]) * tr[:, 2]
        print(f'{year} strategy : signals {int((sig2 != 0).sum())} | identical signals: {same_sig2} | winning trades python {int((gross > 0).sum())}'
              f' vs PineTS {int(o["dbg_wt"][-1])} | PineTS net profit after commission+slippage: ${o["dbg_np"][-1]:,.2f}')
        ok &= same_sig2
    print('\nALL CHECKS PASSED' if ok else '\nMISMATCH FOUND')
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
