# H3-H6: target-reach models on the candidate table built by cands.py. Pre-registered in Part A.3-A.6.
# All models: fitted on in-sample (IS) rows only, evaluated on out-of-sample (OOS) rows (embargoed, see cands.py).
# Uncertainty: moving-block bootstrap over CALENDAR dates (correlated instruments on one date are resampled together),
# block = ceil(H in days)+1 days. Brier/log-loss: 2,000 reps; AUC: 500 reps.
import sys, math, json, time, warnings
import numpy as np, pandas as pd
import statsmodels.api as sm
import e3lib as L, common_load as C

warnings.filterwarnings("ignore")
H = 60
TFS = sys.argv[1:] or ["1h", "5m"]
OUT = L.OUT
RES = {}
LINES = []


def log(s=""):
    print(s, flush=True)
    LINES.append(s)


# ----------------------------------------------------------------------------- design helpers
def rcs_basis(x, knots):
    """Restricted (natural) cubic spline basis, Harrell parameterisation: len(knots)-1 columns (incl. linear)."""
    k = np.asarray(knots, float)
    K = len(k)
    out = [x]
    den = (k[-1] - k[0]) ** 2
    p3 = lambda u: np.maximum(u, 0) ** 3
    for j in range(K - 2):
        v = (p3(x - k[j]) - p3(x - k[K - 2]) * (k[K - 1] - k[j]) / (k[K - 1] - k[K - 2])
             + p3(x - k[K - 1]) * (k[K - 2] - k[j]) / (k[K - 1] - k[K - 2])) / den
        out.append(v)
    return np.column_stack(out)


def dummies(v, levels, prefix):
    v = np.asarray(v)
    levels = [lv_ for lv_ in levels if (v == lv_).any()]   # never emit an all-zero column
    if not levels:
        return np.zeros((len(v), 0)), []
    return np.column_stack([(v == lv_).astype(float) for lv_ in levels]), [f"{prefix}={lv_}" for lv_ in levels]


class Design:
    def __init__(self, D, is_mask):
        self.D = D
        x = np.log(D.d.values)
        self.knots = np.quantile(x[is_mask], [0.05, 0.275, 0.5, 0.725, 0.95])
        self.dss = sorted(D.ds.unique())

    def base(self):
        D = self.D
        cols = [rcs_basis(np.log(D.d.values), self.knots), D.lvr.values[:, None], D.side.values[:, None].astype(float)]
        names = [f"logd_s{i}" for i in range(4)] + ["lvr", "side"]
        dm, dn = dummies(D.ds.values, self.dss[1:], "ds")
        cols.append(dm); names += dn
        X = np.column_stack(cols)
        return np.column_stack([np.ones(len(D)), X]), ["const"] + names

    def add(self, X, names, extra):
        cols = [X]
        nn = list(names)
        for e, en in extra:
            e = np.asarray(e, float)
            if e.ndim == 1:
                e = e[:, None]
            cols.append(e)
            nn += en
        return np.column_stack(cols), nn


def factor(D, key):
    """Candidate factor columns (only bars <= t are used in every feature; see cands.py)."""
    if key == "kind":
        return dummies(D.kind.values, [L.SES, L.PD, L.PW, L.FVG], "kind")   # ref = SW
    if key == "logage":
        return np.log1p(D.age.values), ["log_age"]
    if key == "fresh":
        return np.log1p(D.fresh.values), ["log_fresh"]
    if key == "touch":
        tc = np.minimum(D.ntouch.values, 3)
        return dummies(tc, [1, 2, 3], "touch")                              # ref = 0
    if key == "prior_sweeps":
        return np.log1p(D.prior_sweeps.values), ["log1p_prior_sweeps"]
    if key == "n_opp":
        return D.n_opp.values.astype(float), ["n_opp_fvg"]
    if key == "stack":
        return np.log1p(D["stack"].values), ["log1p_stack"]
    if key == "lvr2":
        return D.lvr.values ** 2, ["lvr2"]
    if key == "session":
        return dummies(D.sess.values, [1, 2], "sess")                       # ref = ASIA
    if key == "mom":
        return np.clip(D.mom.values, -6, 6), ["mom12"]
    if key == "htf":
        return dummies(D.htf.values, [1, 0], "htf")                         # ref = counter (-1)
    if key == "htf_tr":
        return dummies(D.htf_tr.values, [1, 0], "htfema")                   # ref = counter (-1)
    raise KeyError(key)


# ----------------------------------------------------------------------------- fitting and scoring
def fit(X, y, groups=None):
    m = sm.GLM(y, X, family=sm.families.Binomial())
    if groups is None:
        return m.fit()
    return m.fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(groups)[0]})


def predict(res, X):
    return np.clip(res.predict(X), 1e-6, 1 - 1e-6)


def mb_weights(nd, Lb, nrep, seed):
    rng = np.random.default_rng(seed)
    Lb = max(1, min(Lb, nd))
    k = int(math.ceil(nd / Lb)); nst = max(1, nd - Lb + 1)
    st = rng.integers(0, nst, size=(nrep, k))
    W = np.zeros((nrep, nd))
    rr = np.repeat(np.arange(nrep), k)
    for j in range(Lb):
        np.add.at(W, (rr, (st + j).ravel()), 1.0)
    return W


def wauc(s_sorted_y, w):
    """AUC from rows pre-sorted by score: s_sorted_y = y in score order; w = row weights in the same order."""
    y = s_sorted_y
    wn = w * (1 - y); wp = w * y
    cn = np.cumsum(wn) - wn
    den = wp.sum() * wn.sum()
    return (wp * cn).sum() / den if den > 0 else np.nan


def auc(p, y):
    o = np.argsort(p, kind="mergesort")
    return wauc(y[o].astype(float), np.ones(len(y)))


class Boot:
    """Moving-block bootstrap over calendar dates for OOS rows."""

    def __init__(self, dk, Lb, nrep=2000, nrep_auc=500, seed=0):
        self.ud, self.inv = np.unique(dk, return_inverse=True)
        self.W = mb_weights(len(self.ud), Lb, nrep, seed)
        self.Wa = self.W[:nrep_auc]
        self.cnt = np.bincount(self.inv, minlength=len(self.ud)).astype(float)

    def mean(self, x):
        s = np.bincount(self.inv, weights=x, minlength=len(self.ud))
        bm = (self.W @ s) / np.maximum(self.W @ self.cnt, 1)
        m = x.mean()
        se = bm.std()
        return m, np.percentile(bm, 2.5), np.percentile(bm, 97.5), se

    def dauc(self, y, p0, p1):
        o0 = np.argsort(p0, kind="mergesort"); o1 = np.argsort(p1, kind="mergesort")
        y0 = y[o0].astype(float); y1 = y[o1].astype(float)
        i0 = self.inv[o0]; i1 = self.inv[o1]
        out = []
        for w in self.Wa:
            out.append(wauc(y1, w[i1]) - wauc(y0, w[i0]))
        out = np.array(out)
        return auc(p1, y) - auc(p0, y), np.nanpercentile(out, 2.5), np.nanpercentile(out, 97.5)


def brier(p, y):
    return (p - y) ** 2


def ll(p, y):
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def compare(tag, y, p0, p1, B, do_auc=True):
    """OOS skill of model 1 over reference model 0. dBrier = Brier0 - Brier1 (> 0 = model 1 better)."""
    b0, b1 = brier(p0, y), brier(p1, y)
    m, lo, hi, se = B.mean(b0 - b1)
    l0, l1 = ll(p0, y), ll(p1, y)
    ml, lol, hil, _ = B.mean(l0 - l1)
    o = dict(n=int(len(y)), brier0=float(b0.mean()), brier1=float(b1.mean()), dbrier=float(m), dbrier_ci=(float(lo), float(hi)),
             dbrier_p=float(L.p_from_ci(m, se)), bss_rel=float(m / b0.mean()), dll=float(ml), dll_ci=(float(lol), float(hil)))
    if do_auc:
        da, loa, hia = B.dauc(y, p0, p1)
        o.update(auc0=float(auc(p0, y)), auc1=float(auc(p1, y)), dauc=float(da), dauc_ci=(float(loa), float(hia)))
    RES[tag] = o
    s = (f"{tag:46s} n={o['n']:7d} Brier {o['brier0']:.5f}->{o['brier1']:.5f} dBrier {1e4*m:+.2f}e-4 [{1e4*lo:+.2f},{1e4*hi:+.2f}] "
         f"p={o['dbrier_p']:.4f} BSSrel {100*o['bss_rel']:+.3f}% dLL {1e4*ml:+.1f}e-4 [{1e4*lol:+.1f},{1e4*hil:+.1f}]")
    if do_auc:
        s += f" AUC {o['auc0']:.4f}->{o['auc1']:.4f} dAUC {o['dauc']:+.4f} [{o['dauc_ci'][0]:+.4f},{o['dauc_ci'][1]:+.4f}]"
    log(s)
    return o


def coef_line(res, names, keys):
    out = {}
    for kk in keys:
        i = names.index(kk)
        b, se, p = res.params[i], res.bse[i], res.pvalues[i]
        out[kk] = dict(b=float(b), se=float(se), p=float(p))
    return out, "  ".join(f"{k}: b={v['b']:+.4f} se={v['se']:.4f} p={v['p']:.4g}" for k, v in out.items())


def calib_table(p, y, nb=10):
    q = np.quantile(p, np.linspace(0, 1, nb + 1))
    b = np.clip(np.searchsorted(q, p, side="right") - 1, 0, nb - 1)
    rows = []
    for i in range(nb):
        m = b == i
        rows.append((float(p[m].mean()), float(y[m].mean()), int(m.sum())))
    ece = sum(abs(a - o) * k for a, o, k in rows) / len(p)
    return rows, ece


# ----------------------------------------------------------------------------- data
def load_tf(tf):
    R = pd.read_pickle(OUT + f"cands_{tf}.pkl")
    T = pd.read_pickle(OUT + f"touch_{tf}.pkl")
    dks, dkt, strict, pbase_s, pbase_t, oos_bar_by = [], [], [], [], [], {}
    for ds in R.ds.unique():
        o = C.get(ds, tf); df, lv = o["df"], o["lv"]
        m = (R.ds == ds).values
        R.loc[m, "dk"] = L.dkey(df, R.t.values[m])
        mt = (T.ds == ds).values
        T.loc[mt, "dk"] = L.dkey(df, T.t.values[mt])
        # strict (trade-through) outcome for every row: FVG rows used the >= touch rule in cands.py
        f60x, f60n = L.fwd_extremes(df.high.values, df.low.values, df.seg.values, H)
        tt = R.t.values[m]; pr = lv.price.values[R.lvl.values[m]]; sd = R.side.values[m]
        R.loc[m, "price"] = pr
        R.loc[m, "hit_strict"] = np.where(sd > 0, f60x[tt] > pr, f60n[tt] < pr).astype(np.int8)
        # distance-matched random-level single-reach baselines (IS random starts; window ends before OOS)
        day = df.day.values; oos0 = L.split_days(df)
        first_bar = np.r_[0, np.flatnonzero(np.diff(day)) + 1]
        oos_bar = first_bar[oos0]
        rng = np.random.default_rng(0)
        cand = np.arange(200, max(201, oos_bar - H - 1))
        starts = np.sort(rng.choice(cand, size=min(6000, len(cand)), replace=False))
        Ss = L.RaceSurface(df, starts, H, o["tick"], pairs=False)
        St = L.RaceSurface(df, starts, H, o["tick"], touch=True, pairs=False)
        dd = R.d.values[m]
        R.loc[m, "p_rand_strict"] = np.where(sd > 0, Ss.p_reach(dd, 1), Ss.p_reach(dd, -1))
        R.loc[m, "p_rand_touch"] = np.where(sd > 0, St.p_reach(dd, 1), St.p_reach(dd, -1))
        bars_day = len(df) / (day.max() + 1)
        oos_bar_by[ds] = (oos_bar, bars_day)
    R["dk"] = R.dk.astype(np.int64); T["dk"] = T.dk.astype(np.int64)
    Lb = int(math.ceil(H / np.mean([v[1] for v in oos_bar_by.values()]))) + 1
    return R, T, Lb


# ----------------------------------------------------------------------------- hypotheses
def run_tf(tf):
    t0 = time.time()
    R, T, Lb = load_tf(tf)
    log(f"\n######## TF {tf}: candidate rows {len(R)} (IS {int(R.is_.sum())}, OOS {int(R.oos.sum())}), touch events {len(T)}, "
        f"bootstrap block {Lb} calendar days  [{time.time()-t0:.0f}s]")
    log("rows by dataset x kind (all splits): " + json.dumps({ds: g.kind.map(L.KNAME).value_counts().to_dict() for ds, g in R.groupby('ds')}))
    pools = R[R.kind != L.FVG].reset_index(drop=True)
    allr = R.reset_index(drop=True)

    # ======================= H3
    log(f"\n=== H3 ({tf}) target proximity x HTF alignment. Rows = pools (SW/SES/PD/PW) at 0.25-6 ATR.")
    for hcol in ("hit60", "hit20"):
        D = pools if hcol == "hit60" else pools[pools.hit20.notna()].reset_index(drop=True)
        ism, oom = D.is_.values, D.oos.values
        des = Design(D, ism)
        X0, n0 = des.base()
        y = D[hcol].values.astype(float)
        dk = D.dk.values
        B = Boot(dk[oom], Lb if hcol == "hit60" else max(2, Lb - 1), seed=11)
        r0 = fit(X0[ism], y[ism])
        p0 = predict(r0, X0[oom])
        log(f"  [{hcol}] IS n={ism.sum()} hit={y[ism].mean():.4f} | OOS n={oom.sum()} hit={y[oom].mean():.4f}")
        log("  alignment shares IS: " + json.dumps({int(k): round(float(v), 4) for k, v in D[ism].htf.value_counts(normalize=True).items()}))
        for fk in ("htf", "htf_tr"):
            e, en = factor(D, fk)
            X1, n1 = des.add(X0, n0, [(e, en)])
            r1 = fit(X1[ism], y[ism], groups=dk[ism])
            p1 = predict(r1, X1[oom])
            o = compare(f"H3|{tf}|{hcol}|BASE+{fk} vs BASE", y[oom], p0, p1, B, do_auc=(hcol == "hit60"))
            cd, cs = coef_line(r1, n1, en)
            RES[f"H3|{tf}|{hcol}|{fk}|coef_IS"] = cd
            log("     IS coefs, ref=counter (date-clustered SE): " + cs)
            vv = D[fk].values
            lit = [(vv == a_).astype(float) for a_ in (1, -1) if (vv[ism] == 0).any()]
            if len(lit) == 2:
                Xl, nl = des.add(X0, n0, [(np.column_stack(lit), [f"{fk}=+1(vs none)", f"{fk}=-1(vs none)"])])
                rl = fit(Xl[ism], y[ism], groups=dk[ism])
                cdl, csl = coef_line(rl, nl, [f"{fk}=+1(vs none)", f"{fk}=-1(vs none)"])
                RES[f"H3|{tf}|{hcol}|{fk}|coef_IS_ref_none"] = cdl
                log("     IS coefs, literal ref=none: " + csl + f"  (none share IS {np.mean(vv[ism] == 0):.4f})")
            # raw hit rates by alignment, OOS, with Wilson CIs
            for a_ in (1, 0, -1):
                mm = oom & (D[fk].values == a_)
                k_, n_ = int(y[mm].sum()), int(mm.sum())
                if n_:
                    w_ = L.wilson(k_, n_)
                    log(f"     OOS {fk}={a_:+d}: hit {k_/n_:.4f} [{w_[0]:.4f},{w_[1]:.4f}] n={n_} mean d={D.d.values[mm].mean():.2f}")
            if fk == "htf" and hcol == "hit60":
                # secondary: alignment x distance interaction
                Xi, ni = des.add(X1, n1, [(e * np.log(D.d.values)[:, None], [f"{c}*logd" for c in en])])
                ri = fit(Xi[ism], y[ism], groups=dk[ism])
                compare(f"H3|{tf}|hit60|BASE+htf+htf*logd vs BASE+htf", y[oom], p1, predict(ri, Xi[oom]), B, do_auc=False)
                # robustness: CME-only (exclude BTC / the long NQL series) and per-dataset OOS skill
                for ds in des.dss:
                    md = oom & (D.ds.values == ds)
                    if md.sum() < 500:
                        continue
                    Bd = Boot(dk[md], Lb, nrep=1000, seed=12)
                    compare(f"H3|{tf}|hit60|BASE+htf vs BASE|{ds}", y[md], predict(r0, X0[md]), predict(r1, X1[md]), Bd, do_auc=False)

    # ======================= H4
    log(f"\n=== H4 ({tf}) FVGs beyond structure")
    F = allr[allr.kind == L.FVG].reset_index(drop=True)
    for part in ("IS", "OOS"):
        m = F.is_.values if part == "IS" else F.oos.values
        Bp = Boot(F.dk.values[m], Lb, seed=21)
        for lab, sel in (("all", np.ones(m.sum(), bool)), ("overlap(<=0.25ATR of a pool)", F.overlap.values[m] >= 1),
                         ("isolated", F.overlap.values[m] == 0)):
            yy = F.hit60.values[m][sel].astype(float); pp = F.p_rand_touch.values[m][sel]
            ys = F.hit_strict.values[m][sel].astype(float); ps = F.p_rand_strict.values[m][sel]
            if len(yy) < 100:
                continue
            Bs = Boot(F.dk.values[m][sel], Lb, seed=22)
            mt_, lot, hit_, set_ = Bs.mean(yy - pp)
            ms_, los, his, ses = Bs.mean(ys - ps)
            RES[f"H4a|{tf}|{part}|{lab}"] = dict(n=int(len(yy)), touch_rate=float(yy.mean()), base_touch=float(pp.mean()),
                                                  edge_touch=float(mt_), ci_touch=(float(lot), float(hit_)), p_touch=float(L.p_from_ci(mt_, set_)),
                                                  strict_rate=float(ys.mean()), base_strict=float(ps.mean()), edge_strict=float(ms_),
                                                  ci_strict=(float(los), float(his)), p_strict=float(L.p_from_ci(ms_, ses)), mean_d=float(F.d.values[m][sel].mean()))
            log(f"  H4a {part} FVG {lab:30s} n={len(yy):6d} mean d={F.d.values[m][sel].mean():.2f} | touch(>=) {100*yy.mean():.2f}% vs rand {100*pp.mean():.2f}% "
                f"edge {100*mt_:+.2f}pp [{100*lot:+.2f},{100*hit_:+.2f}] p={L.p_from_ci(mt_, set_):.4f} | strict(>) {100*ys.mean():.2f}% vs rand {100*ps.mean():.2f}% "
                f"edge {100*ms_:+.2f}pp [{100*los:+.2f},{100*his:+.2f}]")
        # swing pools in the same band, same baseline (strict) for comparison
        S_ = allr[(allr.kind == L.SW) & (allr.is_ if part == "IS" else allr.oos)]
        Bs = Boot(S_.dk.values, Lb, seed=23)
        ms_, los, his, ses = Bs.mean(S_.hit_strict.values - S_.p_rand_strict.values)
        RES[f"H4a|{tf}|{part}|SW_ref"] = dict(n=int(len(S_)), rate=float(S_.hit_strict.mean()), base=float(S_.p_rand_strict.mean()), edge=float(ms_), ci=(float(los), float(his)))
        log(f"  H4a {part} SW reference                     n={len(S_):6d} mean d={S_.d.mean():.2f} | strict {100*S_.hit_strict.mean():.2f}% vs rand {100*S_.p_rand_strict.mean():.2f}% edge {100*ms_:+.2f}pp [{100*los:+.2f},{100*his:+.2f}]")
    # logistic: FVG vs SW (rule-matched strict outcome), hit ~ BASE + is_FVG (+ overlap flag)
    G = allr[allr.kind.isin([L.SW, L.FVG])].reset_index(drop=True)
    ism, oom = G.is_.values, G.oos.values
    des = Design(G, ism); X0, n0 = des.base()
    isf = (G.kind.values == L.FVG).astype(float)
    iso = isf * (G.overlap.values == 0)
    y = G.hit_strict.values.astype(float)
    B = Boot(G.dk.values[oom], Lb, seed=24)
    r0 = fit(X0[ism], y[ism]); p0 = predict(r0, X0[oom])
    X1, n1 = des.add(X0, n0, [(isf, ["is_FVG"]), (iso, ["is_FVG_isolated"])])
    r1 = fit(X1[ism], y[ism], groups=G.dk.values[ism])
    cd, cs = coef_line(r1, n1, ["is_FVG", "is_FVG_isolated"])
    RES[f"H4a|{tf}|logit_FVG_vs_SW|coef_IS"] = cd
    log("  H4a logit (SW+FVG rows, strict outcome) IS coefs: " + cs)
    compare(f"H4a|{tf}|BASE+is_FVG(+isolated) vs BASE [SW+FVG rows]", y[oom], p0, predict(r1, X1[oom]), B, do_auc=False)

    # H4b barriers on pool rows
    D = pools
    ism, oom = D.is_.values, D.oos.values
    des = Design(D, ism); X0, n0 = des.base()
    y = D.hit60.values.astype(float); dk = D.dk.values
    B = Boot(dk[oom], Lb, seed=25)
    em, emn = factor(D, "mom"); es, esn = factor(D, "stack")
    Xr, nr = des.add(X0, n0, [(em, emn), (es, esn)])
    rr = fit(Xr[ism], y[ism]); pr = predict(rr, Xr[oom])
    X1, n1 = des.add(Xr, nr, [(D.n_opp.values.astype(float), ["n_opp_fvg"])])
    r1 = fit(X1[ism], y[ism], groups=dk[ism]); p1 = predict(r1, X1[oom])
    cd, cs = coef_line(r1, n1, ["n_opp_fvg", "mom12", "log1p_stack"])
    RES[f"H4b|{tf}|coef_IS"] = cd
    log(f"  H4b path-barrier model IS coefs: " + cs)
    log(f"  H4b n_opp distribution IS: mean {D.n_opp.values[ism].mean():.3f}, share>0 {(D.n_opp.values[ism] > 0).mean():.3f}, q95 {np.quantile(D.n_opp.values[ism], .95):.0f}")
    compare(f"H4b|{tf}|+n_opp vs BASE+mom+stack", y[oom], pr, p1, B)
    X2, n2 = des.add(X1, n1, [(D.n_opp_t.values.astype(float), ["n_opp_touched"])])
    r2 = fit(X2[ism], y[ism], groups=dk[ism]); p2 = predict(r2, X2[oom])
    cd2, cs2 = coef_line(r2, n2, ["n_opp_fvg", "n_opp_touched"])
    RES[f"H4b|{tf}|coef_IS_with_control"] = cd2
    log(f"  H4b with touched-FVG control IS coefs: " + cs2)
    Xc, nc = des.add(Xr, nr, [(D.n_opp_t.values.astype(float), ["n_opp_touched"])])
    rc = fit(Xc[ism], y[ism]); pc = predict(rc, Xc[oom])
    compare(f"H4b|{tf}|+n_opp vs BASE+mom+stack+touched_ctrl", y[oom], pc, p2, B, do_auc=False)
    # OOS refit sign check
    r1o = fit(X1[oom], y[oom], groups=dk[oom])
    cdo, cso = coef_line(r1o, n1, ["n_opp_fvg"])
    RES[f"H4b|{tf}|coef_OOSrefit"] = cdo
    log(f"  H4b OOS-refit coef: " + cso)

    # ======================= H5
    log(f"\n=== H5 ({tf}) lifecycle: repeated touches")
    e_age, n_age = factor(D, "logage"); e_t, n_t = factor(D, "touch")
    Xa, na = des.add(X0, n0, [(e_age, n_age)])
    ra = fit(Xa[ism], y[ism]); pa = predict(ra, Xa[oom])
    X1, n1 = des.add(Xa, na, [(e_t, n_t)])
    r1 = fit(X1[ism], y[ism], groups=dk[ism]); p1 = predict(r1, X1[oom])
    cd, cs = coef_line(r1, n1, n_t + n_age)
    RES[f"H5i|{tf}|coef_IS"] = cd
    log("  H5(i) reach model IS coefs (ref = 0 touches): " + cs)
    compare(f"H5i|{tf}|+touch dummies vs BASE+logage", y[oom], pa, p1, B)
    for k_ in (0, 1, 2, 3):
        mm = oom & (np.minimum(D.ntouch.values, 3) == k_)
        if mm.sum():
            w_ = L.wilson(int(y[mm].sum()), int(mm.sum()))
            log(f"     OOS touches={k_}{'+' if k_ == 3 else ''}: hit {y[mm].mean():.4f} [{w_[0]:.4f},{w_[1]:.4f}] n={int(mm.sum())} mean d={D.d.values[mm].mean():.2f} "
                f"model-BASE+age pred {pa[mm[oom]].mean():.4f}")
    # H5(ii) conditional break after the k-th touch
    T2 = T[np.isfinite(T.lvr.values) & np.isfinite(T.age.values)].reset_index(drop=True)   # drop ATR100 warm-up events
    log(f"  H5(ii) touch events with finite lvr: {len(T2)} of {len(T)}")
    kk = np.minimum(T2.k.values, 3)
    dss = sorted(T2.ds.unique())
    cols = [np.ones(len(T2))]
    names = ["const"]
    for v, nm in ((kk == 2, "k=2"), (kk == 3, "k=3+")):
        cols.append(v.astype(float)); names.append(nm)
    cols.append(np.log1p(T2.age.values)); names.append("log_age")
    cols.append(T2.lvr.values); names.append("lvr")
    for kd in (L.SES, L.PD, L.PW):
        cols.append((T2.kind.values == kd).astype(float)); names.append(f"kind={L.KNAME[kd]}")
    for ds in dss[1:]:
        cols.append((T2.ds.values == ds).astype(float)); names.append(f"ds={ds}")
    XT = np.column_stack(cols); yT = T2.brk.values.astype(float)
    for part in ("IS", "OOS"):
        m = T2.is_.values if part == "IS" else T2.oos.values
        rT = fit(XT[m], yT[m], groups=T2.dk.values[m])
        cd, cs = coef_line(rT, names, ["k=2", "k=3+", "log_age"])
        RES[f"H5ii|{tf}|{part}|coef"] = cd
        log(f"  H5(ii) {part} break-within-12 after k-th touch: n={m.sum()} break rate {yT[m].mean():.4f} | " + cs)
        for k_ in (1, 2, 3):
            mm = m & (kk == k_)
            if mm.sum():
                w_ = L.wilson(int(yT[mm].sum()), int(mm.sum()))
                log(f"     {part} k={k_}{'+' if k_ == 3 else ''}: break {yT[mm].mean():.4f} [{w_[0]:.4f},{w_[1]:.4f}] n={int(mm.sum())} median age {np.median(T2.age.values[mm]):.0f}")
    # OOS predictive check: IS model with vs without touch dummies on OOS touch events
    m_is, m_oos = T2.is_.values, T2.oos.values
    XT0 = np.delete(XT, [1, 2], axis=1)
    rT0 = fit(XT0[m_is], yT[m_is]); rT1 = fit(XT[m_is], yT[m_is])
    BT = Boot(T2.dk.values[m_oos], 2, seed=31)
    compare(f"H5ii|{tf}|+k dummies vs no-k [touch events]", yT[m_oos], predict(rT0, XT0[m_oos]), predict(rT1, XT[m_oos]), BT)

    # ======================= H6
    log(f"\n=== H6 ({tf}) ranking factors, each added alone to BASE; rows = pools + FVGs")
    D = allr
    ism, oom = D.is_.values, D.oos.values
    des = Design(D, ism); X0, n0 = des.base()
    y = D.hit60.values.astype(float); dk = D.dk.values
    B = Boot(dk[oom], Lb, seed=41)
    r0 = fit(X0[ism], y[ism]); p0 = predict(r0, X0[oom])
    # BASE calibration and skill vs climatology (IS hit rate per dataset)
    clim = D[ism].groupby("ds").hit60.mean()
    pc = D.ds[oom].map(clim).values
    compare(f"H6|{tf}|BASE vs climatology(IS rate per ds)", y[oom], pc, p0, B)
    # distance-only (no vol) reference
    Xd = np.column_stack([np.ones(len(D)), rcs_basis(np.log(D.d.values), des.knots)])
    rd = fit(Xd[ism], y[ism])
    compare(f"H6|{tf}|BASE vs distance-only spline", y[oom], predict(rd, Xd[oom]), p0, B, do_auc=True)
    rows_, ece = calib_table(p0, y[oom])
    RES[f"H6|{tf}|BASE_calibration_OOS"] = dict(deciles=rows_, ece=ece)
    log(f"  BASE OOS reliability (pred, obs, n) by decile: " + "; ".join(f"{a:.3f}/{o:.3f}/{k}" for a, o, k in rows_) + f"  ECE={ece:.4f}")
    cd, cs = coef_line(r0, n0, ["lvr", "side"])
    log("  BASE IS coefs: " + cs)
    keys = ["kind", "logage", "fresh", "touch", "prior_sweeps", "n_opp", "stack", "lvr2", "session", "mom", "htf"]
    allx = []
    for fk in keys:
        e, en = factor(D, fk)
        allx.append((e, en))
        X1, n1 = des.add(X0, n0, [(e, en)])
        r1 = fit(X1[ism], y[ism], groups=dk[ism])
        compare(f"H6|{tf}|+{fk}", y[oom], p0, predict(r1, X1[oom]), B)
        cd, cs = coef_line(r1, n1, en)
        RES[f"H6|{tf}|{fk}|coef_IS"] = cd
        log("       IS: " + cs)
    XA, nA = des.add(X0, n0, allx)
    rA = fit(XA[ism], y[ism], groups=dk[ism]); pA = predict(rA, XA[oom])
    compare(f"H6|{tf}|+ALL", y[oom], p0, pA, B)
    cd, cs = coef_line(rA, nA, [c for e, en in allx for c in en])
    RES[f"H6|{tf}|ALL|coef_IS"] = cd
    log("       ALL IS: " + cs)
    rows_, ece = calib_table(pA, y[oom])
    RES[f"H6|{tf}|ALL_calibration_OOS"] = dict(deciles=rows_, ece=ece)
    log(f"  ALL OOS reliability by decile: " + "; ".join(f"{a:.3f}/{o:.3f}/{k}" for a, o, k in rows_) + f"  ECE={ece:.4f}")
    # per-dataset OOS skill of ALL vs BASE (stability)
    for ds in des.dss:
        md = oom & (D.ds.values == ds)
        if md.sum() < 500:
            continue
        Bd = Boot(dk[md], Lb, nrep=1000, seed=42)
        compare(f"H6|{tf}|+ALL vs BASE|{ds}", y[md], p0[md[oom]], pA[md[oom]], Bd, do_auc=False)
    # per-kind BASE calibration (does one curve serve all level types?)
    for kd in sorted(D.kind.unique()):
        mk = D.kind.values[oom] == kd
        log(f"  OOS kind={L.KNAME[kd]:3s} n={mk.sum():6d} obs {y[oom][mk].mean():.4f} BASE pred {p0[mk].mean():.4f} ALL pred {pA[mk].mean():.4f}")
    log(f"[TF {tf} done in {time.time()-t0:.0f}s]")


if __name__ == "__main__":
    for tf in TFS:
        run_tf(tf)
    tag = "_".join(TFS)
    open(OUT + f"models_results_{tag}.txt", "w").write("\n".join(LINES))
    json.dump(RES, open(OUT + f"models_results_{tag}.json", "w"), indent=1,
              default=lambda x: float(x) if np.isscalar(x) else list(x))
