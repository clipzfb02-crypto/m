#!/usr/bin/env python3
"""E1 forecast paths: evaluation of the walk-forward forecasts written by e1_run.py.

Usage: python3 e1_eval.py            -> out/results.json, out/tables.md
Metrics and pass criteria are pre-registered in apex/research/experiments/E1_forecast_paths.md (section 1).
"""
import os, json, math
import numpy as np
import pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out')
HS = (20, 60, 120)
J = (10, 20, 40, 60, 90, 120)
VARIANTS = ['a2', 'b50', 'b100', 'b200', 'bL100', 'c0', 'c', 'd', 'e', 'f', 'g']
POOLS = {
    'CME_5m': ['NQ_5m', 'ES_5m', 'YM_5m', 'RTY_5m', 'CL_5m', 'GC_5m'],
    'CME_1h': ['NQ_1h', 'ES_1h', 'YM_1h', 'RTY_1h', 'CL_1h'],
    'BTC_1h': ['BTC_1h'],
}
RNG = np.random.default_rng(20261127)
NBOOT = 1000


# ----------------------------------------------------------------------------- stats helpers
def nw_var(d, L):
    d = d - d.mean()
    n = len(d)
    v = np.dot(d, d) / n
    for l in range(1, min(L, n - 1) + 1):
        v += 2 * (1 - l / (L + 1)) * np.dot(d[l:], d[:-l]) / n
    return v


def dm_test(d, H):
    """One-sided DM (H1: mean(d) < 0, method better). HAC Bartlett lag H, HLN correction."""
    d = np.asarray(d, float)
    d = d[~np.isnan(d)]
    n = len(d)
    v = nw_var(d, H)
    if v <= 0 or n < 3 * H:
        return np.nan, np.nan
    dm = d.mean() / math.sqrt(v / n)
    corr = math.sqrt(max((n + 1 - 2 * H + H * (H - 1) / n) / n, 1e-12))
    dm *= corr
    return float(dm), float(stats.t.cdf(dm, n - 1))


def wilson(k, n, z=1.959964):
    if n == 0:
        return (np.nan, np.nan, np.nan)
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (p, c - h, c + h)


def cbb_ratio(a, b, L, reps=NBOOT):
    """Circular block bootstrap CI (2.5, 97.5) of sum(a)/sum(b)."""
    a = np.asarray(a, float); b = np.asarray(b, float)
    n = len(a)
    L = max(1, min(L, n // 4))
    nb = int(np.ceil(n / L))
    ca = np.r_[0.0, np.cumsum(np.r_[a, a[:L]])]
    cb = np.r_[0.0, np.cumsum(np.r_[b, b[:L]])]
    st = RNG.integers(0, n, size=(reps, nb))
    sa = (ca[st + L] - ca[st]).sum(1)
    sb = (cb[st + L] - cb[st]).sum(1)
    r = sa / sb
    return float(np.percentile(r, 2.5)), float(np.percentile(r, 97.5))


def holm(p):
    p = np.asarray(p, float)
    out = np.full(len(p), np.nan)
    ok = ~np.isnan(p)
    idx = np.where(ok)[0][np.argsort(p[ok])]
    m = len(idx)
    run = 0.0
    for r, i in enumerate(idx):
        run = max(run, min(1.0, (m - r) * p[i]))
        out[i] = run
    return out


def bh(p):
    p = np.asarray(p, float)
    out = np.full(len(p), np.nan)
    ok = ~np.isnan(p)
    idx = np.where(ok)[0][np.argsort(p[ok])]
    m = len(idx)
    prev = 1.0
    for r in range(m - 1, -1, -1):
        i = idx[r]
        prev = min(prev, p[i] * m / (r + 1))
        out[i] = prev
    return out


def dsr(sr, T, skew, kurt, sr_trials):
    """Deflated Sharpe Ratio (Bailey & Lopez de Prado 2014). SRs per period (not annualised)."""
    N = len(sr_trials)
    v = np.var(sr_trials, ddof=1)
    g = 0.5772156649
    sr0 = math.sqrt(v) * ((1 - g) * stats.norm.ppf(1 - 1 / N) + g * stats.norm.ppf(1 - 1 / (N * math.e)))
    den = math.sqrt(max(1 - skew * sr + (kurt - 1) / 4 * sr * sr, 1e-9))
    return float(stats.norm.cdf((sr - sr0) * math.sqrt(T - 1) / den)), float(sr0)


# ----------------------------------------------------------------------------- loading
def load_all():
    S = {}
    for pool, names in POOLS.items():
        for s in names:
            z = dict(np.load(os.path.join(OUT, f'{s}.npz')))
            z['meta'] = json.load(open(os.path.join(OUT, f'{s}_meta.json')))
            S[s] = z
    return S


def errs(z, m, H, period):
    """Terminal error e (ATR units), path MAE, realized move, delta, atr for a period."""
    if period == 'IS':
        dev = z['dev']
        A = z['atr'][dev].astype(float)
        Y = z[f'Y_{H}'][dev].astype(float)
        dT = z[f'IS_dT_{m}_{H}'].astype(float)
        pm = z[f'IS_pm_{m}_{H}'].astype(float)
        tm = z['time'][dev]
        idx = np.arange(len(dev))[dev]
    else:
        msk = z['dev'] if period == 'DEV' else ~z['dev']
        A = z['atr'][msk].astype(float)
        Y = z[f'Y_{H}'][msk].astype(float)
        dT = z[f'WF_dT_{m}_{H}'][msk].astype(float)
        pm = z[f'WF_pm_{m}_{H}'][msk].astype(float)
        tm = z['time'][msk]
        idx = np.arange(len(msk))[msk]
    e = (dT - Y) / A
    return dict(e=e, pm=pm, Y=Y, dT=dT, A=A, t=tm, idx=idx)


def pooled_series(S, names, m, H, period, field):
    """Cross-sectional mean per timestamp of field for method m and for rw (requires >= half of symbols)."""
    cols_m, cols_r = [], []
    for s in names:
        a = errs(S[s], m, H, period)
        r = errs(S[s], 'rw', H, period)
        if field == 'abs':
            vm, vr = np.abs(a['e']), np.abs(r['e'])
        elif field == 'sq':
            vm, vr = a['e'] ** 2, r['e'] ** 2
        else:
            vm, vr = a['pm'], r['pm']
        cols_m.append(pd.Series(vm, index=a['t'], name=s))
        cols_r.append(pd.Series(vr, index=r['t'], name=s))
    M = pd.concat(cols_m, axis=1).sort_index()
    Rr = pd.concat(cols_r, axis=1).sort_index()
    need = int(np.ceil(len(names) / 2))
    ok = (M.notna().sum(axis=1) >= need).values
    return M.mean(axis=1).values[ok], Rr.mean(axis=1).values[ok]


# ----------------------------------------------------------------------------- point metrics
def point_metrics(S):
    rows = []
    for pool, names in POOLS.items():
        for period in ('HOLD', 'DEV', 'IS'):
            for H in HS:
                for m in VARIANTS:
                    row = dict(pool=pool, period=period, H=H, m=m)
                    # per symbol
                    per = {}
                    for s in names:
                        a = errs(S[s], m, H, period)
                        r = errs(S[s], 'rw', H, period)
                        per[s] = dict(mae=float(np.mean(np.abs(a['e'])) / np.mean(np.abs(r['e']))),
                                      rmse=float(math.sqrt(np.mean(a['e'] ** 2) / np.mean(r['e'] ** 2))),
                                      pmae=float(np.mean(a['pm']) / np.mean(r['pm'])),
                                      n=int(len(a['e'])))
                    row['per'] = per
                    row['n_sym_better'] = int(sum(v['mae'] < 1 for v in per.values()))
                    row['n_obs'] = int(sum(v['n'] for v in per.values()))
                    am, ar = pooled_series(S, names, m, H, period, 'abs')
                    row['mae_ratio'] = float(am.sum() / ar.sum())
                    row['mae_rw'] = float(ar.mean())
                    row['dm'], row['p'] = dm_test(am - ar, H)
                    if period == 'HOLD':
                        row['mae_ci'] = cbb_ratio(am, ar, 2 * H)
                    sm, sr = pooled_series(S, names, m, H, period, 'sq')
                    row['rmse_ratio'] = float(math.sqrt(sm.sum() / sr.sum()))
                    row['dm_sq'], row['p_sq'] = dm_test(sm - sr, H)
                    pm, pr = pooled_series(S, names, m, H, period, 'pm')
                    row['pmae_ratio'] = float(pm.sum() / pr.sum())
                    row['dm_pm'], row['p_pm'] = dm_test(pm - pr, H)
                    rows.append(row)
            # multiple testing within pool x period: 11 variants x 3 horizons
            fam = [r for r in rows if r['pool'] == pool and r['period'] == period]
            for key in ('p', 'p_sq', 'p_pm'):
                ph, pb = holm([r[key] for r in fam]), bh([r[key] for r in fam])
                for r, a, b in zip(fam, ph, pb):
                    r[key + '_holm'] = float(a); r[key + '_bh'] = float(b)
    return rows


# ----------------------------------------------------------------------------- direction
def direction(S):
    rows = []
    for pool, names in POOLS.items():
        for period in ('HOLD', 'DEV'):
            for H in HS:
                for m in VARIANTS:
                    row = dict(pool=pool, period=period, H=H, m=m, per={})
                    hit_c, up_c, val_c = [], [], []
                    for s in names:
                        a = errs(S[s], m, H, period)
                        fd, yd = np.sign(a['dT']), np.sign(a['Y'])
                        val = (fd != 0) & (yd != 0)
                        hit = (fd == yd) & val
                        up = (yd > 0) & val
                        no = (a['idx'] % H == 0)
                        k, nn = int(hit[no].sum()), int(val[no].sum())
                        w = wilson(k, nn)
                        row['per'][s] = dict(acc_all=float(hit.sum() / max(val.sum(), 1)), n_all=int(val.sum()),
                                             acc_no=w[0], lo=w[1], hi=w[2], n_no=nn,
                                             up_no=float(up[no].sum() / max(nn, 1)),
                                             zero_fc=int((fd == 0).sum()))
                        hit_c.append(pd.Series(hit.astype(float), index=a['t'], name=s))
                        up_c.append(pd.Series(up.astype(float), index=a['t'], name=s))
                        val_c.append(pd.Series(val.astype(float), index=a['t'], name=s))
                    Hh = pd.concat(hit_c, axis=1).sort_index().fillna(0).sum(axis=1).values
                    U = pd.concat(up_c, axis=1).sort_index().fillna(0).sum(axis=1).values
                    V = pd.concat(val_c, axis=1).sort_index().fillna(0).sum(axis=1).values
                    row['acc'] = float(Hh.sum() / V.sum()) if V.sum() else np.nan
                    row['acc_up'] = float(U.sum() / V.sum()) if V.sum() else np.nan
                    row['n'] = int(V.sum())
                    if V.sum() > 0:
                        row['acc_ci'] = cbb_ratio(Hh, V, 2 * H)
                        row['diff_up'] = row['acc'] - row['acc_up']
                        row['diff_ci'] = cbb_ratio(Hh - U, V, 2 * H)
                        row['diff_50_ci'] = cbb_ratio(Hh - 0.5 * V, V, 2 * H)
                    row['n_sym_wilson_gt50'] = int(sum((v['lo'] > 0.5) for v in row['per'].values() if not np.isnan(v['lo'])))
                    rows.append(row)
    return rows


# ----------------------------------------------------------------------------- economics
def economics(S):
    rows = []
    for pool, names in POOLS.items():
        for period in ('HOLD',):
            weekly = {}
            for H in HS:
                for m in VARIANTS:
                    trades = []
                    per = {}
                    for s in names:
                        z = S[s]
                        meta = z['meta']
                        tick, cost = meta['tick'], meta['cost']
                        O = z['O']
                        msk = ~z['dev']
                        idx = np.arange(len(msk))[msk]
                        idx = idx[idx % H == 0]
                        t = z['org'][idx]
                        ok = t + H + 1 <= len(O) - 1
                        idx, t = idx[ok], t[ok]
                        dT = z[f'WF_dT_{m}_{H}'][idx]
                        dr = np.sign(dT)
                        keep = dr != 0
                        idx, t, dr = idx[keep], t[keep], dr[keep]
                        ent, ex = O[t + 1], O[t + H + 1]
                        cpx = (cost * 1e-4 * ent) if s.startswith('BTC') else cost * tick
                        pnl = dr * (ex - ent) - 2 * cpx
                        A = z['atr'][idx].astype(float)
                        per[s] = dict(n=int(len(pnl)), mean_ticks=float(np.mean(pnl / tick)) if len(pnl) else np.nan,
                                      mean_atr=float(np.mean(pnl / A)) if len(pnl) else np.nan,
                                      gross_atr=float(np.mean((pnl + 2 * cpx) / A)) if len(pnl) else np.nan,
                                      cost_atr=float(np.mean(2 * cpx / A)) if len(pnl) else np.nan)
                        trades.append(pd.DataFrame({'t': pd.to_datetime(z['time'][idx]), 'pnl': pnl / A, 's': s}))
                    T = pd.concat(trades)
                    if len(T) == 0:
                        continue
                    T['wk'] = T.t.dt.to_period('W').astype(str)
                    # equal weight across symbols: weekly mean of each symbol, then mean across symbols
                    wk = T.groupby(['wk', 's']).pnl.sum().unstack().fillna(0.0)
                    wks = wk.mean(1)
                    weekly[(m, H)] = wks
                    mean_trade = T.groupby('s').pnl.mean().mean()
                    # weekly block bootstrap of the equal-weight per-trade mean
                    wkn = T.groupby(['wk', 's']).pnl.count().unstack().fillna(0.0)
                    sums, cnts = wk.values, wkn.values
                    bs = []
                    for _ in range(NBOOT):
                        ii = RNG.integers(0, len(sums), len(sums))
                        ss, cc = sums[ii].sum(0), cnts[ii].sum(0)
                        bs.append(np.mean(ss[cc > 0] / cc[cc > 0]))
                    rows.append(dict(pool=pool, H=H, m=m, per=per, mean_trade_atr=float(mean_trade),
                                     ci=(float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))),
                                     n_trades=int(len(T)), n_weeks=int(len(wks)),
                                     sr_week=float(wks.mean() / wks.std(ddof=1)) if wks.std(ddof=1) > 0 else np.nan,
                                     skew=float(stats.skew(wks)), kurt=float(stats.kurtosis(wks, fisher=False))))
            fam = [r for r in rows if r['pool'] == pool]
            srs = np.array([r['sr_week'] for r in fam])
            for r in fam:
                r['dsr'], r['sr0'] = dsr(r['sr_week'], r['n_weeks'], r['skew'], r['kurt'], srs[~np.isnan(srs)])
    return rows


# ----------------------------------------------------------------------------- bands
def rolling_q(z, lag, W, qs):
    s = pd.Series(z).shift(lag)
    if W == 'exp':
        r = s.expanding(min_periods=100)
    else:
        r = s.rolling(W, min_periods=W)
    return np.vstack([r.quantile(q).values for q in qs]).T


def rolling_q_group(z, g, lag, W, qs):
    """Quantiles of the last W realized z within the same group as the origin."""
    n = len(z)
    out = np.full((n, len(qs)), np.nan)
    for v in np.unique(g[g >= 0]):
        pos = np.where(g == v)[0]
        rq = pd.Series(z[pos]).rolling(W, min_periods=W)
        Q = np.vstack([rq.quantile(q).values for q in qs]).T
        tgt = np.arange(n)[g == v]
        last = np.searchsorted(pos, tgt - lag, side='right') - 1   # last same-group origin realized at t
        ok = last >= 0
        out[tgt[ok]] = Q[last[ok]]
    return out


QS = (0.1, 0.5, 0.9)


def band_scores(r, scale, Q, A):
    """r: residual (price), scale: price units per z unit, Q: (n,3) quantiles of z. Scores in ATR units."""
    lo, md, hi = (Q[:, 0] * scale, Q[:, 1] * scale, Q[:, 2] * scale)
    ok = ~np.isnan(lo)
    lo, md, hi, r, A = lo[ok], md[ok], hi[ok], r[ok], A[ok]
    cov = (r >= lo) & (r <= hi)
    a = 0.2
    isc = (hi - lo) + (2 / a) * np.maximum(lo - r, 0) + (2 / a) * np.maximum(r - hi, 0)
    return ok, dict(cov=cov, below=r < lo, above=r > hi, med=r > md, width=(hi - lo) / A, isc=isc / A)


def bands_series(z, m, W, schemes=('U0', 'U1', 'U2', 'U3', 'U4')):
    A = z['atr'].astype(float)
    vt = z['vt'].astype(int)
    out = {}
    pooled_cache = {}
    for sch in schemes:
        for k in HS:
            r = z[f'Y_{k}'].astype(float) - z[f'WF_dJ_{m}_{k}'].astype(float)
            if sch == 'U0':
                Q = rolling_q(r / A, k, W, QS); scale = A
            elif sch == 'U3':
                Wg = W if W == 'exp' else max(int(W) // 3, 30)
                Q = rolling_q_group(r / A, vt, k, 100 if W == 'exp' else Wg, QS); scale = A
            elif sch == 'U4':
                scale = z[f'sig_{k}'].astype(float)
                Q = np.tile(np.array([-1.2815516, 0.0, 1.2815516]), (len(r), 1))
            else:
                if sch not in pooled_cache:
                    qsum = 0
                    for j in J:
                        rj = z[f'Y_{j}'].astype(float) - z[f'WF_dJ_{m}_{j}'].astype(float)
                        sc = A * math.sqrt(j) if sch == 'U1' else z[f'sig_{j}'].astype(float)
                        qsum = qsum + rolling_q(rj / sc, j, W, QS)
                    pooled_cache[sch] = qsum / len(J)
                Q = pooled_cache[sch]
                scale = A * math.sqrt(k) if sch == 'U1' else z[f'sig_{k}'].astype(float)
            ok, sc = band_scores(r, scale, Q, A)
            out[(sch, k)] = (ok, sc)
    return out


def bands(S, methods=('rw', 'g', 'd', 'e', 'b100', 'c', 'f', 'a2', 'c0'), W=2000):
    rows = []
    for pool, names in POOLS.items():
        for m in methods:
            acc = {}
            for s in names:
                z = S[s]
                hold = ~z['dev']
                res = bands_series(z, m, W)
                for key, (ok, sc) in res.items():
                    msk = hold & ok
                    sel = msk[ok]
                    vt = z['vt'][ok][sel]
                    tm = pd.to_datetime(z['time'][ok][sel]).to_period('W').astype(str)
                    d = acc.setdefault(key, {f: [] for f in ('cov', 'below', 'above', 'med', 'width', 'isc', 'vt', 'wk', 'valid_frac')})
                    for f in ('cov', 'below', 'above', 'med', 'width', 'isc'):
                        d[f].append(sc[f][sel])
                    d['vt'].append(vt); d['wk'].append(np.asarray(tm)); d['valid_frac'].append(msk.sum() / hold.sum())
            for (sch, k), d in acc.items():
                cov = np.concatenate(d['cov']); vt = np.concatenate(d['vt']); wk = np.concatenate(d['wk'])
                row = dict(pool=pool, m=m, sch=sch, k=k, W=W, n=int(len(cov)), cov=float(cov.mean()),
                           below=float(np.concatenate(d['below']).mean()), above=float(np.concatenate(d['above']).mean()),
                           med=float(np.concatenate(d['med']).mean()), width=float(np.concatenate(d['width']).mean()),
                           isc=float(np.concatenate(d['isc']).mean()), valid_frac=float(np.mean(d['valid_frac'])))
                row['cov_vt'] = {int(v): float(cov[vt == v].mean()) for v in (0, 1, 2) if (vt == v).any()}
                # weekly block bootstrap CI for coverage
                dfw = pd.DataFrame({'wk': wk, 'c': cov}).groupby('wk').c.agg(['sum', 'count']).values
                bs = []
                for _ in range(300):
                    ii = RNG.integers(0, len(dfw), len(dfw))
                    bs.append(dfw[ii, 0].sum() / dfw[ii, 1].sum())
                row['cov_ci'] = (float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5)))
                rows.append(row)
    return rows


def band_minsample(S, methods=('rw', 'g'), Ws=(100, 250, 500, 1000, 2000, 4000, 'exp')):
    rows = []
    for pool, names in POOLS.items():
        for m in methods:
            for sch in ('U0', 'U1'):
                cache = {(s, W): bands_series(S[s], m, W, schemes=(sch,)) for s in names for W in Ws}
                for k in HS:
                    per_W = {}
                    masks = {(s, W): cache[(s, W)][(sch, k)] for s in names for W in Ws}
                    # common valid set per series across W that keep >= 50% of holdout valid
                    usable = []
                    for W in Ws:
                        fr = [np.mean((~S[s]['dev']) & masks[(s, W)][0]) / np.mean(~S[s]['dev']) for s in names]
                        if min(fr) >= 0.5:
                            usable.append(W)
                    for W in usable:
                        covs, iscs, ws = [], [], []
                        for s in names:
                            z = S[s]
                            common = ~z['dev'].copy()
                            for W2 in usable:
                                common &= masks[(s, W2)][0]
                            ok, sc = masks[(s, W)]
                            sel = common[ok]
                            covs.append(sc['cov'][sel]); iscs.append(sc['isc'][sel]); ws.append(sc['width'][sel])
                        c = np.concatenate(covs)
                        per_W[str(W)] = dict(cov=float(c.mean()), isc=float(np.concatenate(iscs).mean()),
                                             width=float(np.concatenate(ws).mean()), n=int(len(c)))
                    rows.append(dict(pool=pool, m=m, sch=sch, k=k, per_W=per_W, usable=[str(w) for w in usable]))
    return rows


# ----------------------------------------------------------------------------- tables
def fmt(x, d=3):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return 'n/a'
    return f'{x:.{d}f}'


def fp(p):
    if p is None or np.isnan(p):
        return 'n/a'
    return f'{p:.2g}' if p >= 0.001 else '<0.001'


def tables(R):
    L = []
    pm = R['point']
    for pool in POOLS:
        L.append(f'\n### Point forecasts · {pool}\n')
        L.append('| H | method | MAE ratio HOLD [95% CI] | DM p (Holm) | sym<1 | RMSE ratio | path-MAE ratio (p Holm) | WF-dev MAE ratio | IS MAE ratio |')
        L.append('|---|---|---|---|---|---|---|---|---|')
        for H in HS:
            for m in VARIANTS:
                h = next(r for r in pm if r['pool'] == pool and r['period'] == 'HOLD' and r['H'] == H and r['m'] == m)
                dv = next(r for r in pm if r['pool'] == pool and r['period'] == 'DEV' and r['H'] == H and r['m'] == m)
                is_ = next(r for r in pm if r['pool'] == pool and r['period'] == 'IS' and r['H'] == H and r['m'] == m)
                L.append(f"| {H} | {m} | {fmt(h['mae_ratio'])} [{fmt(h['mae_ci'][0])}, {fmt(h['mae_ci'][1])}] | {fp(h['p'])} ({fp(h['p_holm'])}) | "
                         f"{h['n_sym_better']}/{len(POOLS[pool])} | {fmt(h['rmse_ratio'])} | {fmt(h['pmae_ratio'])} ({fp(h['p_pm_holm'])}) | "
                         f"{fmt(dv['mae_ratio'])} | {fmt(is_['mae_ratio'])} |")
        rw = [r for r in pm if r['pool'] == pool and r['period'] == 'HOLD' and r['m'] == 'a2']
        L.append('\nRandom-walk MAE (ATR units), holdout: ' + ', '.join(f"H={r['H']}: {fmt(r['mae_rw'], 2)}" for r in rw)
                 + f"; holdout origins (all symbols): {rw[0]['n_obs']}.")
    L.append('\n### Directional accuracy (holdout)\n')
    L.append('| pool | H | method | acc [95% CI] | always-up | diff vs up [95% CI] | sym with Wilson lo > 50% (non-overlap) | n |')
    L.append('|---|---|---|---|---|---|---|---|')
    for r in R['dir']:
        if r['period'] != 'HOLD' or 'acc_ci' not in r:
            continue
        L.append(f"| {r['pool']} | {r['H']} | {r['m']} | {fmt(r['acc'])} [{fmt(r['acc_ci'][0])}, {fmt(r['acc_ci'][1])}] | {fmt(r['acc_up'])} | "
                 f"{fmt(r['diff_up'])} [{fmt(r['diff_ci'][0])}, {fmt(r['diff_ci'][1])}] | {r['n_sym_wilson_gt50']}/{len(POOLS[r['pool']])} | {r['n']} |")
    L.append('\n### Economic check (holdout, non-overlapping, after costs; ATR units per trade)\n')
    L.append('| pool | H | method | mean net/trade [95% CI] | trades | weekly SR | DSR (33 trials) |')
    L.append('|---|---|---|---|---|---|---|')
    for r in R['econ']:
        L.append(f"| {r['pool']} | {r['H']} | {r['m']} | {fmt(r['mean_trade_atr'])} [{fmt(r['ci'][0])}, {fmt(r['ci'][1])}] | {r['n_trades']} | {fmt(r['sr_week'])} | {fmt(r['dsr'])} |")
    L.append('\n### Bands (holdout, W = 2000)\n')
    L.append('| pool | method | scheme | k | coverage [95% CI] (80%) | below (10%) | above (10%) | >q50 (50%) | width ATR | interval score | cov low/mid/high vol |')
    L.append('|---|---|---|---|---|---|---|---|---|---|---|')
    for r in R['bands']:
        cv = r['cov_vt']
        L.append(f"| {r['pool']} | {r['m']} | {r['sch']} | {r['k']} | {fmt(r['cov'])} [{fmt(r['cov_ci'][0])}, {fmt(r['cov_ci'][1])}] | {fmt(r['below'])} | {fmt(r['above'])} | "
                 f"{fmt(r['med'])} | {fmt(r['width'], 2)} | {fmt(r['isc'], 2)} | {'/'.join(fmt(cv.get(v)) for v in (0, 1, 2))} |")
    L.append('\n### Band minimum sample (holdout, common origins)\n')
    L.append('| pool | method | scheme | k | W: coverage / interval score |')
    L.append('|---|---|---|---|---|')
    for r in R['minsample']:
        L.append(f"| {r['pool']} | {r['m']} | {r['sch']} | {r['k']} | " + '; '.join(f"{w}: {fmt(v['cov'])}/{fmt(v['isc'], 2)}" for w, v in r['per_W'].items()) + ' |')
    return '\n'.join(L)


if __name__ == '__main__':
    S = load_all()
    R = {}
    R['point'] = point_metrics(S); print('point done', flush=True)
    R['dir'] = direction(S); print('dir done', flush=True)
    R['econ'] = economics(S); print('econ done', flush=True)
    R['bands'] = bands(S); print('bands done', flush=True)
    R['minsample'] = band_minsample(S); print('minsample done', flush=True)
    R['meta'] = {s: {k: v for k, v in S[s]['meta'].items() if k != 'blocks'} for s in S}
    R['params'] = {s: S[s]['meta']['blocks'] for s in S}

    def conv(o):
        if isinstance(o, (np.floating,)): return float(o)
        if isinstance(o, (np.integer,)): return int(o)
        if isinstance(o, tuple): return list(o)
        return str(o)
    with open(os.path.join(OUT, 'results.json'), 'w') as fh:
        json.dump(R, fh, default=conv)
    with open(os.path.join(OUT, 'tables.md'), 'w') as fh:
        fh.write(tables(R))
    print('wrote results.json, tables.md')
