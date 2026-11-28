#!/usr/bin/env python3
"""E1 verification checks (run before trusting e1_run.py outputs).

1. Timezone: the missing daily hour on CME 1h must be 17:00 New York (maintenance break)
   in both EST and EDT if the stamps are UTC.
2. GC integrity: count bar-to-bar jumps > 1.5% that reverse on the next bar (contract interleaving)
   on GC 1h and on GC 1-minute (and NQ for reference).
3. No-lookahead truncation test: features computed on data[:N] must equal the features computed
   on the full data for every bar < N (excluding the outcome-only 'hit' array).
4. Walk-forward fit truncation test: parameters fitted at refit T must be identical whether the
   data ends at T or at the full length.

Usage: python3 -I e1_verify.py
"""
import os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import e1_run as R  # noqa: E402


def tz_check(sym='NQ'):
    import glob
    d = pd.read_csv(glob.glob(R.CME + f'{sym}/{sym}_1h_*.csv')[0], parse_dates=['datetime'])
    utc = d['datetime'].dt.tz_localize('UTC')
    ny = utc.dt.tz_convert('America/New_York')
    out = {}
    for name, msk in (('EST (Jan)', ny.dt.month == 1), ('EDT (Jul)', ny.dt.month == 7)):
        hrs_utc = utc[msk].dt.hour.value_counts().sort_index()
        hrs_ny = ny[msk].dt.hour.value_counts().sort_index()
        out[name] = dict(missing_utc=sorted(set(range(24)) - set(hrs_utc.index)),
                         missing_ny=sorted(set(range(24)) - set(hrs_ny.index)))
    return out


def jump_back(sym, tf, thr=0.015):
    import glob
    f = glob.glob(R.CME + f'{sym}/{sym}_{tf}_*.csv')[0]
    d = pd.read_csv(f)
    c = d['close'].values.astype(float)
    r = np.diff(np.log(c))
    big = np.abs(r) > thr
    back = big[:-1] & big[1:] & (np.sign(r[:-1]) != np.sign(r[1:]))
    return dict(bars=len(c), jumps=int(big.sum()), jump_and_back=int(back.sum()))


def trunc_feature_test(series, N):
    d = R.load(series)
    Ff = R.features(d)
    Ft = R.features(d.iloc[:N].reset_index(drop=True))
    keys = ['atr', 'm', 'beta50', 'beta100', 'beta200', 'yend100', 'bias', 'vt', 'tgt', 'tb', 'u', 'pos']
    bad = {}
    for k in keys:
        a, b = np.asarray(Ff[k])[:N], np.asarray(Ft[k])[:N]
        eq = np.allclose(a.astype(float), b.astype(float), equal_nan=True, rtol=1e-10, atol=1e-10)
        if not eq:
            diff = np.where(~np.isclose(a.astype(float), b.astype(float), equal_nan=True))[0]
            bad[k] = (len(diff), int(diff[0]))
    return bad


def trunc_fit_test(series, T):
    """Fit at refit T on the full data vs on data truncated to T bars (bars 0..T-1)."""
    tick, cost, T0, Rr, hl = R.SPECS[series]
    d = R.load(series)
    Ff = R.features(d)
    Ft = R.features(d.iloc[:T].reset_index(drop=True))
    # 'hit' needs bars up to s+120 <= T-1: recompute hit on the truncated set is identical for s <= T-121
    tr = np.arange(R.WARM, T - R.KMAX)
    out = {}
    pa = R.fit_a2(Ff, tr)['mu'], R.fit_a2(Ft, tr)['mu']
    pc = R.fit_c(Ff, tr), R.fit_c(Ft, tr)
    pd_ = R.fit_d(Ff, tr, T, hl), R.fit_d(Ft, tr, T, hl)
    pe = R.fit_e(Ff, tr)['M'], R.fit_e(Ft, tr)['M']
    pf = R.fit_f(Ff, tr), R.fit_f(Ft, tr)
    out['a2'] = np.isclose(*pa)
    out['c'] = np.isclose(pc[0]['b'], pc[1]['b']) and pc[0]['hl'] == pc[1]['hl']
    out['d_kappa'] = np.isclose(pd_[0]['kappa'], pd_[1]['kappa'])
    out['d_ell'] = np.allclose(pd_[0]['ell'][:T], pd_[1]['ell'][:T])
    out['e'] = np.allclose(pe[0], pe[1])
    out['f'] = np.allclose(pf[0]['p'], pf[1]['p']) and np.allclose(pf[0]['ks'], pf[1]['ks'])
    out['hit_train_equal'] = bool(np.array_equal(Ff['hit'][tr], Ft['hit'][tr]))
    return out


if __name__ == '__main__':
    print('timezone check NQ 1h:', tz_check('NQ'))
    for sym, tf in (('GC', '1h'), ('GC', '1min'), ('NQ', '1h'), ('NQ', '1min'), ('CL', '1h'), ('CL', '1min')):
        print('jump-and-back', sym, tf, jump_back(sym, tf))
    for series, N in (('NQ_1h', 3001), ('NQ_5m', 7777), ('BTC_1h', 20011)):
        print('feature truncation', series, N, 'mismatches:', trunc_feature_test(series, N) or 'none')
    for series, T in (('NQ_1h', 2750), ('ES_5m', 6000)):
        print('fit truncation', series, T, trunc_fit_test(series, T))
