"""Builds 5-minute bars (TradingView style: labelled by bar OPEN time, New York time)."""
import pandas as pd
from pathlib import Path

SRC = Path(__file__).parent / 'data_src' / 'data'
OUT = Path(__file__).parent / 'data'
AGG = {'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'}


def to_5m(df):
    return df.resample('5min', label='left', closed='left').agg(AGG).dropna()


def main():
    OUT.mkdir(exist_ok=True)
    # NQ 1m, Dec 2022 - Dec 2025. Timestamps are New York time labelled by bar CLOSE -> shift to bar open.
    d = pd.read_csv(SRC / 'Dataset_NQ_1min_2022_2025.csv')
    d.columns = ['ts', 'open', 'high', 'low', 'close', 'volume', 'vwap_rth', 'vwap_eth']
    d['ts'] = pd.to_datetime(d['ts'], format='%m/%d/%Y %H:%M') - pd.Timedelta(minutes=1)
    to_5m(d.set_index('ts').sort_index()[list(AGG)]).to_pickle(OUT / 'nq5_2023_2025.pkl')
    # NQ 5m, Feb - Apr 2026 (New York time, bar open labels) -> untouched holdout
    n5 = pd.read_csv(SRC / 'NQ_5min.csv', parse_dates=['datetime']).set_index('datetime')[list(AGG)]
    n5.to_pickle(OUT / 'nq5_2026_holdout.pkl')
    # MNQ 1m 2026 (UTC). Rows before 2026-03-04 17:00 are not on the 0.25 tick grid (synthetic) -> dropped.
    m = pd.read_csv(SRC / 'mnq_2026_1min.csv', parse_dates=['datetime'])
    m['datetime'] = m['datetime'].dt.tz_convert('America/New_York').dt.tz_localize(None)
    m = m.set_index('datetime')
    to_5m(m[m.index > '2026-03-04 17:00'][list(AGG)]).to_pickle(OUT / 'mnq5_2026_holdout.pkl')
    print('wrote', sorted(p.name for p in OUT.glob('*.pkl')))


if __name__ == '__main__':
    main()
