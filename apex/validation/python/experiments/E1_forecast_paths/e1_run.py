#!/usr/bin/env python3
"""E1 forecast paths: walk-forward forecasts for every method and series.

Usage: python3 -I e1_run.py [SERIES ...]   (default: all 12 series)
Writes out/<series>.npz and out/<series>_meta.json (git-ignored).

Pre-registered design: apex/research/experiments/E1_forecast_paths.md section 1.
No lookahead: every feature at origin t uses bars <= t; every fitted parameter used for
origins in [T, T+R) comes from training origins s <= T-121 (purged: outcomes realized before T).
"""
import sys, os, glob, json, time
import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view as swv

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out')
os.makedirs(OUT, exist_ok=True)
SP = '/tmp/claude-0/-home-user-m/7ce60006-3639-59b1-8cd3-87355409d58a/scratchpad'
CME = SP + '/brief/study/amt_data/cme/'
BTC = SP + '/brief/study/classic_tools/btc_1h.csv'

KMAX = 120
HS = (20, 60, 120)
J = (10, 20, 40, 60, 90, 120)
PIV = 5
WARM = 600
METHODS = ['rw', 'a2', 'b50', 'b100', 'b200', 'bL100', 'c0', 'c', 'd', 'e', 'f', 'g']
GCOMP = ['b100', 'c', 'd', 'e', 'f']
HL_GRID = [1, 2, 3, 5, 8, 12, 20, 30, 50, 80, 120, 200, 500, np.inf]
DBUCK = np.array([0, 0.5, 1, 1.5, 2, 3, 4, 6, 10, np.inf])

# series -> (tick, cost per side in ticks (CME) or bp (BTC), T0, R, EWMA half-life bars)
SPECS = {
    'NQ_5m': (0.25, 2.0, 2000, 500, 288), 'ES_5m': (0.25, 1.25, 2000, 500, 288),
    'YM_5m': (1.0, 2.0, 2000, 500, 288), 'RTY_5m': (0.1, 2.0, 2000, 500, 288),
    'CL_5m': (0.01, 1.25, 2000, 500, 288), 'GC_5m': (0.1, 1.25, 2000, 500, 288),
    'NQ_1h': (0.25, 2.0, 1500, 250, 120), 'ES_1h': (0.25, 1.25, 1500, 250, 120),
    'YM_1h': (1.0, 2.0, 1500, 250, 120), 'RTY_1h': (0.1, 2.0, 1500, 250, 120),
    'CL_1h': (0.01, 1.25, 1500, 250, 120), 'BTC_1h': (0.01, 5.0, 3000, 2000, 120),
}


# ----------------------------------------------------------------------------- data
def load(series):
    sym, tf = series.split('_')
    if sym == 'BTC':
        d = pd.read_csv(BTC, parse_dates=['datetime'])
    elif tf == '1h':
        assert sym != 'GC', 'GC 1h excluded (interleaved contract months)'
        d = pd.read_csv(glob.glob(CME + f'{sym}/{sym}_1h_*.csv')[0], parse_dates=['datetime'])
    else:
        m = pd.read_csv(glob.glob(CME + f'{sym}/{sym}_1min_*.csv')[0], parse_dates=['datetime'])
        m = m.set_index('datetime')
        d = m.resample('5min', label='left', closed='left').agg(
            {'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'})
        d = d.dropna(subset=['close']).reset_index()
    d = d.sort_values('datetime').drop_duplicates('datetime').reset_index(drop=True)
    utc = d['datetime'].dt.tz_localize('UTC')
    if sym == 'BTC':
        loc = utc.dt.tz_localize(None)
        day = loc.dt.normalize()
        slot = loc.dt.hour.values
        bucket = slot.copy()
    else:
        loc = utc.dt.tz_convert('America/New_York').dt.tz_localize(None)
        day = (loc + pd.Timedelta(hours=6)).dt.normalize()   # CME day starts 18:00 NY
        if tf == '5m':
            slot = (loc.dt.hour * 12 + loc.dt.minute // 5).values
            bucket = slot // 6                                  # 30-minute NY buckets
        else:
            slot = loc.dt.hour.values
            bucket = slot.copy()
    d['dayid'] = pd.factorize(day)[0]
    d['slot'] = slot.astype(int)
    d['bucket'] = bucket.astype(int)
    return d


# ----------------------------------------------------------------------------- features
def atr_wilder(h, l, c, n=14):
    pc = np.r_[np.nan, c[:-1]]
    tr = np.nanmax(np.vstack([h - l, np.abs(h - pc), np.abs(l - pc)]), axis=0)
    return pd.Series(tr).ewm(alpha=1.0 / n, adjust=False).mean().values


def roll_ols(c, L):
    n = len(c)
    i = np.arange(n, dtype=float)
    cy = np.r_[0.0, np.cumsum(c)]
    ciy = np.r_[0.0, np.cumsum(i * c)]
    beta = np.full(n, np.nan)
    yend = np.full(n, np.nan)
    t = np.arange(L - 1, n)
    Sy = cy[t + 1] - cy[t + 1 - L]
    Siy = ciy[t + 1] - ciy[t + 1 - L]
    x0 = (t - L + 1).astype(float)
    Sxy = Siy - x0 * Sy
    xbar = (L - 1) / 2.0
    Sxx = L * (L * L - 1) / 12.0
    ybar = Sy / L
    b = (Sxy - L * xbar * ybar) / Sxx
    beta[t] = b
    yend[t] = ybar + b * (L - 1 - xbar)
    return beta, yend


def pivots(h, l, p=PIV):
    n = len(h)
    ph = np.zeros(n, bool)
    pl = np.zeros(n, bool)
    hmax = swv(h, p).max(1)   # hmax[j] = max(h[j:j+p])
    lmin = swv(l, p).min(1)
    i = np.arange(p, n - p)
    ph[i] = (h[i] > hmax[i - p]) & (h[i] >= hmax[i + 1])
    pl[i] = (l[i] < lmin[i - p]) & (l[i] <= lmin[i + 1])
    return ph, pl


def structure(h, l, c, ph, pl, p=PIV, cap=50):
    """BOS bias and nearest unbroken confirmed swing levels; pivot at i is usable from bar i+p."""
    n = len(c)
    bias = np.zeros(n, np.int8)
    nearSH = np.full(n, np.nan)
    nearSL = np.full(n, np.nan)
    lastSH = lastSL = np.nan
    shB = slB = True
    b = 0
    unSH, unSL = [], []
    for t in range(n):
        i = t - p
        if i >= p:
            if ph[i]:
                lastSH = h[i]; shB = False; unSH.append(h[i])
                if len(unSH) > cap: unSH.pop(0)
            if pl[i]:
                lastSL = l[i]; slB = False; unSL.append(l[i])
                if len(unSL) > cap: unSL.pop(0)
        if (not shB) and c[t] > lastSH:
            b = 1; shB = True
        if (not slB) and c[t] < lastSL:
            b = -1; slB = True
        bias[t] = b
        ht, lt = h[t], l[t]
        if unSH:
            unSH = [x for x in unSH if x > ht]
        if unSL:
            unSL = [x for x in unSL if x < lt]
        if unSH: nearSH[t] = min(unSH)
        if unSL: nearSL[t] = max(unSL)
    return bias, nearSH, nearSL


def features(d):
    O, Hh, Ll, C = (d[k].values.astype(float) for k in ('open', 'high', 'low', 'close'))
    n = len(C)
    F = dict(O=O, H=Hh, L=Ll, C=C, n=n)
    F['atr'] = atr_wilder(Hh, Ll, C)
    D = np.r_[0.0, np.diff(C)]
    F['D'] = D
    x = np.r_[0.0, D[1:] / F['atr'][:-1]]
    F['m'] = pd.Series(x).ewm(span=20, adjust=False).mean().values
    for L in (50, 100, 200):
        F[f'beta{L}'], F[f'yend{L}'] = roll_ols(C, L)
    ph, pl = pivots(Hh, Ll)
    F['bias'], nSH, nSL = structure(Hh, Ll, C, ph, pl)
    r = pd.Series(F['atr'] / C).rolling(500).rank(pct=True).values
    F['vt'] = np.where(np.isnan(r), -1, np.where(r < 1 / 3, 0, np.where(r < 2 / 3, 1, 2))).astype(np.int8)
    # prior-day high/low, untaken today
    dayid = d['dayid'].values
    g = pd.DataFrame({'d': dayid, 'h': Hh, 'l': Ll})
    dh = g.groupby('d').h.max().values
    dl = g.groupby('d').l.min().values
    pdh = np.where(dayid > 0, dh[np.maximum(dayid - 1, 0)], np.nan)
    pdl = np.where(dayid > 0, dl[np.maximum(dayid - 1, 0)], np.nan)
    runh = g.groupby('d').h.cummax().values
    runl = g.groupby('d').l.cummin().values
    pdh_ok = np.where(runh < pdh, pdh, np.nan)
    pdl_ok = np.where(runl > pdl, pdl, np.nan)
    up = np.fmin(nSH, pdh_ok)
    dn = np.fmax(nSL, pdl_ok)
    tgt = np.where(F['bias'] == 1, up, np.where(F['bias'] == -1, dn, np.nan))
    F['tgt'] = tgt
    dist = np.abs(tgt - C) / F['atr']
    F['tb'] = np.where(np.isnan(dist), -1, np.searchsorted(DBUCK, dist, side='right') - 1).astype(int)
    # first hit time within KMAX (evaluation outcome for reach-rate training only)
    hit = np.full(n, 999, dtype=np.int32)
    idx = np.arange(0, n - KMAX)
    Hw = swv(Hh, KMAX)[idx + 1]
    Lw = swv(Ll, KMAX)[idx + 1]
    tt = tgt[idx]
    bb = F['bias'][idx]
    ok = ~np.isnan(tt)
    with np.errstate(invalid='ignore'):
        reach = np.where((bb == 1)[:, None], Hw >= tt[:, None], Lw <= tt[:, None]) & ok[:, None]
    anyr = reach.any(1)
    hit[idx[anyr]] = reach[anyr].argmax(1) + 1
    F['hit'] = hit
    # clock pieces
    F['u'] = np.r_[np.nan, np.diff(np.log(C)) ** 2]
    F['slot'] = d['slot'].values
    F['bucket'] = d['bucket'].values
    nslots = F['slot'].max() + 1
    first = d.iloc[:2000]
    ndays = first['dayid'].nunique()
    sd = first.groupby('slot').dayid.nunique()
    active = np.array(sorted(sd[sd >= 0.5 * ndays].index.values))
    F['active'] = active
    pos = np.searchsorted(active, F['slot'], side='right') - 1
    F['pos'] = np.where(pos < 0, len(active) - 1, pos)
    F['bucket_of_active'] = pd.Series(F['bucket'], index=F['slot']).groupby(level=0).first().reindex(active).values
    return F


# ----------------------------------------------------------------------------- fits
def fit_a2(F, tr):
    return dict(mu=float(np.mean(F['D'][tr + 1] / F['atr'][tr])))


def fit_c(F, tr):
    Dw = swv(F['D'], KMAX)          # Dw[j] = D[j:j+KMAX]
    w = F['m'][tr] / F['atr'][tr]
    ck = (w @ Dw[tr + 1]) / np.sum(F['m'][tr] ** 2)
    k = np.arange(KMAX)
    best = None
    for hl in HL_GRID:
        phi = 1.0 if np.isinf(hl) else 0.5 ** (1.0 / hl)
        gk = phi ** k
        b = np.dot(ck, gk) / np.dot(gk, gk)
        sse = np.sum((ck - b * gk) ** 2)
        if best is None or sse < best[0]:
            best = (sse, b, phi, hl)
    return dict(b=float(best[1]), phi=float(best[2]), hl=float(best[3]), c1=float(ck[0]))


def clock(F, T, hl):
    u = F['u']
    bk = F['bucket']
    nb = bk.max() + 1
    bs = np.bincount(bk[1:T], weights=u[1:T], minlength=nb)
    bc = np.bincount(bk[1:T], minlength=nb)
    vb = np.where(bc >= 5, bs / np.maximum(bc, 1), np.nan) / np.nanmean(u[1:T])
    vb = np.where(np.isnan(vb), 1.0, vb)
    ratio = u / vb[bk]
    ratio[0] = np.nanmean(u[1:T])
    ell = pd.Series(ratio).ewm(halflife=hl, adjust=False).mean().values
    va = vb[F['bucket_of_active']]
    A = len(va)
    reps = int(np.ceil((A + KMAX + 2) / A)) + 1
    ext = np.tile(va, reps)
    S = np.r_[0.0, np.cumsum(ext)]
    p = np.arange(A)[:, None]
    k = np.arange(1, KMAX + 1)[None, :]
    CV = S[p + k + 1] - S[p + 1]    # sum_{j=1..k} v(slot pos+j)
    return ell, CV, vb


def sigclk(F, ell, CV, t, ks=None):
    s = F['C'][t][:, None] * np.sqrt(ell[t][:, None] * CV[F['pos'][t]])
    return s if ks is None else s[:, np.asarray(ks) - 1]


def zsig(F, ell, t):
    C = F['C']
    return np.clip((C[t] - C[t - 100]) / (C[t] * np.sqrt(ell[t]) * 10.0), -3, 3)


def fit_d(F, tr, T, hl):
    ell, CV, vb = clock(F, T, hl)
    s60 = sigclk(F, ell, CV, tr, [60])[:, 0]
    y = (F['C'][tr + 60] - F['C'][tr]) / s60
    z = zsig(F, ell, tr)
    kappa = float(np.sum(y * z) / np.sum(z * z))
    return dict(kappa=kappa, ell=ell, CV=CV, vmax=float(vb.max()), vmin=float(vb.min()))


def fit_e(F, tr):
    st = 3 * (F['bias'][tr].astype(int) + 1) + F['vt'][tr]
    ok = F['vt'][tr] >= 0
    tr2, st = tr[ok], st[ok]
    Cw = swv(F['C'], KMAX + 1)[tr2]
    Ym = (Cw[:, 1:] - Cw[:, :1]) / F['atr'][tr2][:, None]
    oh = np.zeros((9, len(tr2)))
    oh[st, np.arange(len(tr2))] = 1.0
    cnt = oh.sum(1)
    M = (oh @ Ym) / np.maximum(cnt, 1)[:, None]
    M[cnt < 300] = 0.0
    return dict(M=M, cnt=cnt.astype(int).tolist())


def fit_f(F, tr):
    tb = F['tb'][tr]
    hit = F['hit'][tr]
    p = np.zeros((len(DBUCK) - 1, len(HS)))
    ks = np.full(len(DBUCK) - 1, float(KMAX))
    cnt = np.zeros(len(DBUCK) - 1, int)
    for b in range(len(DBUCK) - 1):
        msk = tb == b
        cnt[b] = msk.sum()
        if cnt[b] < 50:
            continue
        for j, H in enumerate(HS):
            p[b, j] = np.mean(hit[msk] <= H)
        hh = hit[msk][hit[msk] <= KMAX]
        if len(hh):
            ks[b] = float(np.median(hh))
    return dict(p=p, ks=ks, cnt=cnt.tolist())


# ----------------------------------------------------------------------------- paths
def path(F, m, P, t, H):
    """Delta(t,k) = Phat(t,k) - C_t for k=1..H, origins t (array). P = params of block."""
    k = np.arange(1, H + 1)[None, :].astype(float)
    C, A = F['C'], F['atr']
    nt = len(t)
    if m == 'rw':
        return np.zeros((nt, H))
    if m == 'a2':
        return P['a2']['mu'] * A[t][:, None] * k
    if m in ('b50', 'b100', 'b200'):
        L = int(m[1:])
        return F[f'beta{L}'][t][:, None] * k
    if m == 'bL100':
        return (F['yend100'][t] - C[t])[:, None] + F['beta100'][t][:, None] * k
    if m == 'c0':
        g = np.cumsum(0.5 ** ((k - 1) / 12.0), axis=1)
        return (A[t] * F['m'][t])[:, None] * g
    if m == 'c':
        q = P['c']
        g = np.cumsum(q['phi'] ** (k - 1), axis=1)
        return (A[t] * q['b'] * F['m'][t])[:, None] * g
    if m == 'd':
        q = P['d']
        s = sigclk(F, q['ell'], q['CV'], t)[:, :H]
        return q['kappa'] * zsig(F, q['ell'], t)[:, None] * s
    if m == 'e':
        q = P['e']
        st = 3 * (F['bias'][t].astype(int) + 1) + F['vt'][t]
        out = A[t][:, None] * q['M'][np.clip(st, 0, 8), :H]
        out[F['vt'][t] < 0] = 0.0
        return out
    if m == 'f':
        q = P['f']
        j = HS.index(H)
        tb = F['tb'][t]
        ok = tb >= 0
        tbc = np.clip(tb, 0, len(DBUCK) - 2)
        w = np.where(ok, q['p'][tbc, j], 0.0)
        gap = np.where(ok, F['tgt'][t] - C[t], 0.0)
        shape = np.minimum(1.0, k / q['ks'][tbc][:, None])
        return (w * gap)[:, None] * shape
    if m == 'g':
        beta = P['g'][H]
        out = np.zeros((nt, H))
        for c in GCOMP:
            if beta[c] > 0:
                out += beta[c] * path(F, c, P, t, H)
        return out / len(GCOMP)
    raise ValueError(m)


# ----------------------------------------------------------------------------- driver
def run(series):
    t0 = time.time()
    tick, cost, T0, R, hl = SPECS[series]
    d = load(series)
    F = features(d)
    n = F['n']
    C, A = F['C'], F['atr']
    org = np.arange(T0, n - KMAX)
    no = len(org)
    split = int(org[0] + no // 2)
    blocks = [(T, min(T + R, org[-1] + 1)) for T in range(T0, org[-1] + 1, R)]
    Cw = swv(C, KMAX + 1)[org]
    Y = (Cw[:, 1:] - Cw[:, :1]).astype(np.float32)   # realized moves k=1..120
    Ao = A[org]

    def fit_all(T):
        tr = np.arange(WARM, T - KMAX)   # purge: s + 120 <= T - 1
        P = dict(a2=fit_a2(F, tr), c=fit_c(F, tr), d=fit_d(F, tr, T, hl), e=fit_e(F, tr), f=fit_f(F, tr))
        return P

    WF = [fit_all(T) for T, _ in blocks]
    IS = fit_all(split)   # IS diagnostic: fit on dev period, evaluated on dev origins
    dev = org < split
    t_dev = org[dev]

    res = {}
    termWF = {}   # terminal deltas, for g weights

    def build(m, H, Pblocks, mode):
        """Delta matrix for all origins (WF) or dev origins (IS)."""
        if mode == 'WF':
            out = np.zeros((no, H), np.float32)
            for (T, E), P in zip(blocks, Pblocks):
                sl = slice(T - T0, E - T0)
                out[sl] = path(F, m, P, org[sl], H)
            return out
        return path(F, m, Pblocks, t_dev, H).astype(np.float32)

    # g weights (WF): least squares through origin on purged WF component terminal forecasts (ATR units)
    def g_weights(term, idx_ok, H):
        y = Y[:, H - 1] / Ao
        w = {}
        for c in GCOMP:
            f = term[(c, H)] / Ao
            if idx_ok.sum() < 1000:
                w[c] = 0.0
                continue
            ff, yy = f[idx_ok], y[idx_ok]
            den = np.sum(ff * ff)
            w[c] = float(np.clip(np.sum(ff * yy) / den, 0, 1)) if den > 0 else 0.0
        return w

    meta = dict(series=series, n=int(n), T0=T0, R=R, split=split, no=int(no), n_dev=int(dev.sum()),
                n_hold=int((~dev).sum()), first=str(d['datetime'].iloc[0]), last=str(d['datetime'].iloc[-1]),
                split_time=str(d['datetime'].iloc[split]), tick=tick, cost=cost, active_slots=int(len(F['active'])))
    for mode in ('WF', 'IS'):
        Pb = WF if mode == 'WF' else IS
        Yref = Y if mode == 'WF' else Y[dev]
        Aref = Ao if mode == 'WF' else Ao[dev]
        term = {}
        for m in METHODS:
            if m == 'g':
                if mode == 'WF':
                    for (T, E), P in zip(blocks, WF):
                        P['g'] = {H: g_weights(term, org <= T - KMAX - 1, H) for H in HS}
                else:
                    IS['g'] = {H: g_weights_is(term, Yref, Aref, t_dev, split, H) for H in HS}
            dJ = {}
            for H in HS:
                M = build(m, H, Pb, mode)
                term[(m, H)] = M[:, H - 1].copy()
                res[f'{mode}_dT_{m}_{H}'] = M[:, H - 1].copy()
                res[f'{mode}_pm_{m}_{H}'] = (np.abs(M - Yref[:, :H]).mean(1) / Aref).astype(np.float32)
                if mode == 'WF':
                    for j in J:
                        if j <= H and j not in dJ:
                            dJ[j] = M[:, j - 1].copy()
                del M
            if mode == 'WF':
                for j in J:
                    res[f'WF_dJ_{m}_{j}'] = dJ[j]
        if mode == 'WF':
            termWF = term
    # clock sigma at J (WF)
    sig = np.zeros((no, len(J)), np.float32)
    zs = np.zeros(no, np.float32)
    for (T, E), P in zip(blocks, WF):
        sl = slice(T - T0, E - T0)
        sig[sl] = sigclk(F, P['d']['ell'], P['d']['CV'], org[sl], J)
    for i, j in enumerate(J):
        res[f'sig_{j}'] = sig[:, i]
    for i, j in enumerate(J):
        res[f'Y_{j}'] = Y[:, j - 1].copy()
    res.update(org=org, time=d['datetime'].values[org].astype('datetime64[ns]').astype(np.int64),
               atr=Ao.astype(np.float32), vt=F['vt'][org], bias=F['bias'][org], close=C[org],
               O=F['O'], Cfull=C, Afull=A, dev=dev)
    # parameter summaries
    meta['blocks'] = [dict(T=int(T), mu=P['a2']['mu'], c_b=P['c']['b'], c_hl=P['c']['hl'], c_c1=P['c']['c1'],
                           kappa=P['d']['kappa'], e_cnt=P['e']['cnt'], f_p60=P['f']['p'][:, 1].round(3).tolist(),
                           f_ks=P['f']['ks'].tolist(), g={str(H): P['g'][H] for H in HS})
                      for (T, E), P in zip(blocks, WF)]
    meta['IS'] = dict(mu=IS['a2']['mu'], c_b=IS['c']['b'], c_hl=IS['c']['hl'], kappa=IS['d']['kappa'],
                      g={str(H): IS['g'][H] for H in HS})
    meta['target_coverage'] = float(np.mean(F['tb'][org] >= 0))
    meta['secs'] = round(time.time() - t0, 1)
    np.savez_compressed(os.path.join(OUT, f'{series}.npz'), **res)
    with open(os.path.join(OUT, f'{series}_meta.json'), 'w') as fh:
        json.dump(meta, fh, indent=1, default=float)
    print(series, 'n', n, 'origins', no, 'split', meta['split_time'], 'secs', meta['secs'], flush=True)


def g_weights_is(term, Yref, Aref, t_dev, split, H):
    ok = t_dev <= split - KMAX - 1
    y = Yref[:, H - 1] / Aref
    w = {}
    for c in GCOMP:
        f = term[(c, H)] / Aref
        ff, yy = f[ok], y[ok]
        den = np.sum(ff * ff)
        w[c] = float(np.clip(np.sum(ff * yy) / den, 0, 1)) if (den > 0 and ok.sum() >= 1000) else 0.0
    return w


if __name__ == '__main__':
    todo = sys.argv[1:] or list(SPECS)
    for s in todo:
        run(s)
