# H2: does a CONFIRMED sweep-and-reclaim improve reversal (opposite liquidity before a new extreme)? Pre-registered A.2.
import math, json
import numpy as np, pandas as pd
import e3lib as L, common_load as C

HR = 60          # race horizon (bars)
RANK = {L.PW: 3, L.PD: 2, L.SES: 1, L.SW: 0}


def joint_boot_diff(a_vals, a_blk, b_vals, b_blk, nrep=2000, block_len=3, seed=0):
    """Moving-block bootstrap (shared ordered block ids) of mean(a) - mean(b)."""
    ub = np.unique(np.r_[a_blk, b_blk])
    ia = np.searchsorted(ub, a_blk); ib = np.searchsorted(ub, b_blk)
    nb = len(ub)
    sa = np.bincount(ia, a_vals, nb); ca = np.bincount(ia, minlength=nb).astype(float)
    sb = np.bincount(ib, b_vals, nb); cb = np.bincount(ib, minlength=nb).astype(float)
    rng = np.random.default_rng(seed)
    Lb = block_len; k = int(math.ceil(nb / Lb)); nst = max(1, nb - Lb + 1)
    cs = lambda x: np.r_[0, np.cumsum(x)]
    Sa, Ca, Sb, Cb = cs(sa), cs(ca), cs(sb), cs(cb)
    st = rng.integers(0, nst, size=(nrep, k)); en = np.minimum(st + Lb, nb)
    da = (Sa[en] - Sa[st]).sum(1) / np.maximum((Ca[en] - Ca[st]).sum(1), 1)
    db = (Sb[en] - Sb[st]).sum(1) / np.maximum((Cb[en] - Cb[st]).sum(1), 1)
    d = da - db
    m = sa.sum() / ca.sum() - sb.sum() / cb.sum()
    return m, np.percentile(d, 2.5), np.percentile(d, 97.5), d.std()


def run(name, tf):
    o = C.get(name, tf)
    df, lv, tick = o["df"], o["lv"], o["tick"]
    h, l, c = df.high.values, df.low.values, df.close.values
    atr, seg, day, bias = df.atr.values, df.seg.values, df.day.values, df.htf_bias.values
    n = len(df)
    oos0 = L.split_days(df)
    first_bar = np.r_[0, np.flatnonzero(np.diff(day)) + 1]
    oos_bar = first_bar[oos0]
    bars_day = n / (day.max() + 1)
    emb_bars = int(HR + (math.ceil(HR / bars_day) + 1) * bars_day)
    pools = lv[lv.kind.isin([L.SW, L.SES, L.PD, L.PW])].copy()
    pools["stop"] = np.minimum(pools.end.values, pools.exp.values)
    pools = pools.sort_values("avail").reset_index(drop=True)
    PA, PS, PP, PST, PK = pools.avail.values, pools.side.values, pools.price.values, pools.stop.values, pools.kind.values
    win = 2600 if tf == "5m" else 600
    sw = lv[lv.kind == L.SW].sort_values("avail")
    swA, swS, swP = sw.avail.values, sw.side.values, sw.price.values
    ev = pools[pools.traded].copy()
    events = []
    for pen_name in ("tick", "atr10"):
        recs = []
        for _, r in ev.iterrows():
            t0 = int(r.end); s = int(r.side); P = r.price
            if pen_name == "tick":
                t = t0
            else:
                k = 0.10 * atr[t0 - 1]
                e = min(n, t0 + 12)
                pen = (h[t0:e] - P) if s > 0 else (P - l[t0:e])
                w = np.flatnonzero(pen >= k)
                if not len(w):
                    continue
                t = t0 + w[0]
                if seg[t] != seg[t0]:
                    continue
            recs.append((t, s, RANK[int(r.kind)], int(r.kind), P))
        E = pd.DataFrame(recs, columns=["t", "side", "rank", "kind", "price"])
        # one event per (bar, side): keep the highest-ranked pool (stacked sweeps are one event)
        E = E.sort_values(["t", "side", "rank"], ascending=[True, True, False]).drop_duplicates(["t", "side"])
        for _, e in E.iterrows():
            t, s, P = int(e.t), int(e.side), e.price
            if not np.isfinite(atr[t]) or t + 4 >= n:
                continue
            inside = lambda j: (c[j] <= P) if s > 0 else (c[j] >= P)
            decs = {"W": t}
            if inside(t):
                decs["R0"] = t
            js = [j for j in range(t, min(n, t + 4)) if seg[j] == seg[t] and inside(j)]
            if js:
                decs["R3"] = js[0]
                j = js[0]
                # MSS: close beyond the most recent confirmed opposite swing (as of each bar m) within 12 bars
                for m in range(j, min(n, j + 13)):
                    if seg[m] != seg[t]:
                        break
                    i1 = np.searchsorted(swA, m, side="right")
                    lo_ = max(0, i1 - 400)
                    msk = swS[lo_:i1] == -s
                    if not msk.any():
                        break
                    ref = swP[lo_:i1][msk][-1]
                    if (s > 0 and c[m] < ref) or (s < 0 and c[m] > ref):
                        decs["R3M"] = m
                        break
            elif all(seg[j] == seg[t] for j in range(t, t + 4)):
                decs["ACC"] = t + 3
            for cls, d in decs.items():
                if not np.isfinite(atr[d]) or atr[d] <= 0:
                    continue
                ext = h[t:d + 1].max() if s > 0 else l[t:d + 1].min()
                # nearest active opposite-side pool at d, 0.25-8 ATR away
                i1 = np.searchsorted(PA, d, side="right"); i0 = np.searchsorted(PA, d - win, side="left")
                a_ = slice(i0, i1)
                act = (PST[a_] > d) & (PS[a_] == -s)
                pr = PP[a_][act]
                dist = ((c[d] - pr) if s > 0 else (pr - c[d])) / atr[d]
                ok = (dist >= 0.25) & (dist <= 8)
                if not ok.any():
                    continue
                q = np.argmin(np.where(ok, dist, np.inf))
                tgt = pr[q]; d_opp = dist[q]
                d_ext = abs(ext - c[d]) / atr[d]
                if s > 0:
                    rr, tau = L.race(h, l, seg, d, ext, tgt, HR)
                    rev = {-1: 1, 1: 0}.get(rr, np.nan)
                else:
                    rr, tau = L.race(h, l, seg, d, tgt, ext, HR)
                    rev = {1: 1, -1: 0}.get(rr, np.nan)
                if rr == -9:
                    continue
                events.append(dict(ds=name, tf=tf, pen=pen_name, cls=cls, t=t, dbar=d, side=s, kind=int(e.kind),
                                   d_opp=d_opp, d_ext=d_ext, race=rr, rev=rev, day=day[d], dk=int(L.dkey(df, d)),
                                   with_bias=(bias[d] == s), against_bias=(bias[d] == -s),
                                   oos=d >= oos_bar + emb_bars, is_=d + HR < oos_bar))
    X = pd.DataFrame(events)
    # baseline surface from IS random starts
    rng = np.random.default_rng(0)
    cand = np.arange(200, max(201, oos_bar - HR - 1))
    S = L.RaceSurface(df, np.sort(rng.choice(cand, size=min(6000, len(cand)), replace=False)), HR, tick)
    pu = np.where(X.side > 0, S.p_up_first(X.d_ext.values, X.d_opp.values), S.p_up_first(X.d_opp.values, X.d_ext.values))
    X["p_rev"] = np.where(X.side > 0, 1 - pu, pu)
    X["p_none"] = np.where(X.side > 0, S.p_none(X.d_ext.values, X.d_opp.values), S.p_none(X.d_opp.values, X.d_ext.values))
    return X


def summ(X):
    r = X[X.race.isin([1, -1])]
    b = r.ds.astype("category").cat.codes.astype("int64").values * 100000 + r.day.values
    m, lo, hi, se = L.block_boot_mean(r.rev.values - r.p_rev.values, b, block_len=3)
    mc, loc, hic, sec = L.block_boot_mean(r.rev.values - r.p_rev.values, r.dk.values, block_len=3, seed=7)
    k = int(r.rev.sum()); nn = len(r)
    return dict(ci_cal=(loc, hic),n=len(X), res=nn, tie=int((X.race == 0).sum()), none=int((X.race == 9).sum()),
                rev=k / max(nn, 1), rev_ci=L.wilson(k, nn), base=r.p_rev.mean(), edge=m, ci=(lo, hi),
                p=L.p_from_ci(m, se), cont=1 - k / max(nn, 1), none_obs=(X.race == 9).mean(), none_base=X.p_none.mean(),
                med_dopp=r.d_opp.median(), med_dext=r.d_ext.median())


def f(o):
    return (f"n={o['n']:6d} res={o['res']:6d} tie={o['tie']:4d} none={o['none']:5d} | REV {100*o['rev']:.1f}% "
            f"[{100*o['rev_ci'][0]:.1f},{100*o['rev_ci'][1]:.1f}] base {100*o['base']:.1f} edge {100*o['edge']:+.2f}pp "
            f"[{100*o['ci'][0]:+.2f},{100*o['ci'][1]:+.2f}] p={o['p']:.3f} calCI[{100*o['ci_cal'][0]:+.2f},{100*o['ci_cal'][1]:+.2f}] | CONT {100*o['cont']:.1f}% | none obs {100*o['none_obs']:.1f} "
            f"base {100*o['none_base']:.1f} | med d_opp {o['med_dopp']:.2f} d_ext {o['med_dext']:.2f}")


if __name__ == "__main__":
    allX = []
    for tf, names in (("1h", L.DATASETS_1H), ("5m", L.DATASETS_5M)):
        for nm in names:
            X = run(nm, tf)
            allX.append(X)
            print(nm, tf, "event rows", len(X), flush=True)
    A = pd.concat(allX, ignore_index=True)
    A.to_pickle(L.OUT + "h2_rows.pkl")
    lines = []; res = {}
    for tf in ("1h", "5m"):
        for pen in ("tick", "atr10"):
            for part in ("IS", "OOS"):
                P = A[(A.tf == tf) & (A.pen == pen) & (A.oos if part == "OOS" else A.is_)]
                lines.append(f"===== {tf} pen={pen} {part}")
                for cls in ("W", "R0", "R3", "R3M", "ACC"):
                    s = P[P.cls == cls]
                    if len(s) < 30:
                        continue
                    o = summ(s); res[f"{tf}|{pen}|{part}|{cls}|POOLED"] = o
                    lines.append(f"  {cls:4s} POOLED " + f(o))
                    for ds in s.ds.unique():
                        s2 = s[s.ds == ds]
                        if len(s2) < 30:
                            continue
                        o2 = summ(s2); res[f"{tf}|{pen}|{part}|{cls}|{ds}"] = o2
                        lines.append(f"       {ds:4s} " + f(o2))
                # R3 - W difference in edge
                a = P[(P.cls == "R3") & P.race.isin([1, -1])]; w = P[(P.cls == "W") & P.race.isin([1, -1])]
                if len(a) > 30 and len(w) > 30:
                    ba = a.ds.astype("category").cat.codes.astype("int64").values * 100000 + a.day.values
                    bw = w.ds.astype("category").cat.codes.astype("int64").values * 100000 + w.day.values
                    # use consistent ds coding
                    cats = sorted(P.ds.unique())
                    ba = a.ds.map({k: i for i, k in enumerate(cats)}).values * 100000 + a.day.values
                    bw = w.ds.map({k: i for i, k in enumerate(cats)}).values * 100000 + w.day.values
                    m, lo, hi, se = joint_boot_diff((a.rev - a.p_rev).values, ba, (w.rev - w.p_rev).values, bw)
                    mc, loc, hic, sec = joint_boot_diff((a.rev - a.p_rev).values, a.dk.values, (w.rev - w.p_rev).values, w.dk.values, seed=8)
                    res[f"{tf}|{pen}|{part}|R3-W"] = dict(diff=m, ci=(lo, hi), p=L.p_from_ci(m, se), ci_cal=(loc, hic), p_cal=L.p_from_ci(mc, sec))
                    lines.append(f"  R3-W edge diff {100*m:+.2f}pp [{100*lo:+.2f},{100*hi:+.2f}] p={L.p_from_ci(m, se):.3f} calCI[{100*loc:+.2f},{100*hic:+.2f}] p_cal={L.p_from_ci(mc, sec):.3f}")
                # exploratory: R3 by HTF bias relation
                for lab, msk in (("with-bias", "with_bias"), ("against-bias", "against_bias")):
                    s = P[(P.cls == "R3") & P[msk]]
                    if len(s) >= 30:
                        o = summ(s); res[f"{tf}|{pen}|{part}|R3|{lab}"] = o
                        lines.append(f"  R3 {lab:12s} " + f(o))
    txt = "\n".join(lines)
    print(txt)
    open(L.OUT + "h2_results.txt", "w").write(txt)
    json.dump(res, open(L.OUT + "h2_results.json", "w"), default=lambda x: float(x) if np.isscalar(x) else list(map(float, x)), indent=1)
