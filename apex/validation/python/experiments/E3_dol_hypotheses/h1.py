# H1: prior-day extremes -> race (H1a), directional travel (H1b), single-level reach (H1c). Pre-registered in Part A.1.
import sys, json, math
import numpy as np, pandas as pd
import e3lib as L, common_load as C

RES = []


def race_h(tf, name):
    if tf == "5m":
        return 552
    return 48 if name == "BTC" else 46


def run(name, tf):
    o = C.get(name, tf)
    df, lv, tick = o["df"], o["lv"], o["tick"]
    h, l, c, op = df.high.values, df.low.values, df.close.values, df.open.values
    atr, seg, day = df.atr.values, df.seg.values, df.day.values
    n = len(df)
    H = race_h(tf, name)
    nd = day.max() + 1
    oos0 = L.split_days(df)
    emb_days = int(math.ceil(2)) + 1  # race horizon 2 days
    first_bar = np.r_[0, np.flatnonzero(np.diff(day)) + 1]
    last_bar = np.r_[first_bar[1:] - 1, n - 1]
    pd_lv = lv[lv.kind == L.PD]
    pdh = pd_lv[pd_lv.side > 0].set_index("avail"); pdl = pd_lv[pd_lv.side < 0].set_index("avail")
    tmin = df.t.dt.hour * 60 + df.t.dt.minute
    step = 60 if tf == "1h" else 5
    rows = []
    for D in range(1, nd):
        fb, lb = first_bar[D], last_bar[D]
        pb = fb - 1  # last bar of day D-1 = avail of its PD levels
        if pb not in pdh.index or pb not in pdl.index:
            continue
        H_ = pdh.loc[pb, "price"]; Lo = pdl.loc[pb, "price"]
        if isinstance(H_, pd.Series):
            H_ = H_.iloc[0]; Lo = Lo.iloc[0]
        pdo, pdc = op[first_bar[D - 1]], c[pb]
        # decision points
        cands = {"E_open": fb}
        tm = tmin.values[fb:lb + 1]
        k = np.flatnonzero((tm <= 9 * 60 + 30) & (tm + step > 9 * 60 + 30))
        if len(k):
            cands["E_ny"] = fb + k[0]
        for ev, t in cands.items():
            if not np.isfinite(atr[t]) or atr[t] <= 0:
                continue
            if h[fb:t + 1].max() > H_ or l[fb:t + 1].min() < Lo:
                continue  # one already taken
            if not (Lo < c[t] < H_):
                continue
            du = (H_ - c[t]) / atr[t]; dd = (c[t] - Lo) / atr[t]
            r, tau = L.race(h, l, seg, t, H_, Lo, H)
            if r == -9:
                continue
            eod = c[lb] - c[t]
            reach_up = r == 1 or r == 0 or (h[t + 1:t + H + 1] > H_).any()
            reach_dn = r == -1 or r == 0 or (l[t + 1:t + H + 1] < Lo).any()
            rows.append(dict(ds=name, tf=tf, ev=ev, day=D, t=t, dk=int(L.dkey(df, t)), du=du, dd=dd, race=r, tau=tau, eod=eod,
                             pdcdir=np.sign(pdc - pdo), reach_up=reach_up, reach_dn=reach_dn,
                             oos=D >= oos0 + emb_days, is_=(D < oos0) and (D + 2 < oos0)))
    R = pd.DataFrame(rows)
    # baseline surface from IS random starts (window must end before OOS start)
    is_end_bar = first_bar[oos0] if oos0 < nd else n
    rng = np.random.default_rng(0)
    cand = np.arange(200, max(201, is_end_bar - H - 1))
    starts = rng.choice(cand, size=min(6000, len(cand)), replace=False)
    S = L.RaceSurface(df, np.sort(starts), H, tick)
    R["p_up_emp"] = S.p_up_first(R.du.values, R.dd.values)
    R["p_none_emp"] = S.p_none(R.du.values, R.dd.values)
    R["p_up_geo"] = R.dd / (R.du + R.dd)
    R["near_up"] = R.du < R.dd
    R["p_reach_up"] = S.p_reach(R.du.values, 1)
    R["p_reach_dn"] = S.p_reach(R.dd.values, -1)
    return R, S.n


def summarize(R, label):
    out = {}
    bl = 3  # block length in days
    res = R[R.race.isin([1, -1])].copy()
    res["near_first"] = ((res.race == 1) & res.near_up) | ((res.race == -1) & ~res.near_up)
    res["p_near_emp"] = np.where(res.near_up, res.p_up_emp, 1 - res.p_up_emp)
    res["p_near_geo"] = np.where(res.near_up, res.p_up_geo, 1 - res.p_up_geo)
    y_up = (res.race == 1).astype(float)
    blocks = res.ds + ":" + res.day.astype(str)
    blocks_ord = res.ds.astype("category").cat.codes.astype("int64") * 100000 + res.day
    m, lo, hi, se = L.block_boot_mean(res.near_first - res.p_near_emp, blocks_ord, block_len=bl)
    mg, log_, hig, seg_ = L.block_boot_mean(res.near_first - res.p_near_geo, blocks_ord, block_len=bl, seed=1)
    # robustness: calendar-date blocks (correlated instruments on the same date resampled together)
    mc, loc, hic, sec = L.block_boot_mean(res.near_first - res.p_near_emp, res.dk.values, block_len=bl, seed=4)
    k = int(res.near_first.sum()); nn = len(res)
    out.update(edge_emp_ci_cal=(loc, hic), edge_emp_p_cal=L.p_from_ci(mc, sec),
               n_dec=len(R), n_res=nn, ties=int((R.race == 0).sum()), unres=int((R.race == 9).sum()),
               near_first=k / max(nn, 1), near_ci=L.wilson(k, nn), base_emp=res.p_near_emp.mean(),
               base_geo=res.p_near_geo.mean(), edge_emp=m, edge_emp_ci=(lo, hi), edge_emp_p=L.p_from_ci(m, se),
               edge_geo=mg, edge_geo_ci=(log_, hig),
               brier_emp=np.mean((res.p_up_emp - y_up) ** 2), brier_geo=np.mean((res.p_up_geo - y_up) ** 2),
               brier_half=np.mean((0.5 - y_up) ** 2), unres_obs=(R.race == 9).mean(), unres_emp=R.p_none_emp.mean())
    # H1b directional travel to EOD
    dr = R[R.eod != 0].copy()
    dr["pred"] = np.where(dr.near_up, 1, -1)
    dr["acc"] = (np.sign(dr.eod) == dr.pred).astype(float)
    dr["acc_mom"] = np.where(dr.pdcdir != 0, (np.sign(dr.eod) == dr.pdcdir).astype(float), 0.5)
    kb = int(dr.acc.sum()); nb = len(dr)
    bo = dr.ds.astype("category").cat.codes.astype("int64") * 100000 + dr.day
    md, lod, hid, sed = L.block_boot_mean(dr.acc - dr.acc_mom, bo, block_len=bl, seed=2)
    ma, loa, hia, sea = L.block_boot_mean(dr.acc - 0.5, dr.dk.values, block_len=bl, seed=5)
    out.update(dir_ci_cal=(0.5 + loa, 0.5 + hia))
    out.update(dir_n=nb, dir_acc=kb / max(nb, 1), dir_ci=L.wilson(kb, nb), dir_mom=dr.acc_mom.mean(),
               dir_diff_mom=md, dir_diff_ci=(lod, hid), dir_diff_p=L.p_from_ci(md, sed))
    # H1c single-level reach within H_race (both levels per decision)
    rr = pd.concat([pd.DataFrame({"y": R.reach_up.astype(float), "p": R.p_reach_up, "b": R.ds.astype("category").cat.codes.astype("int64") * 100000 + R.day}),
                    pd.DataFrame({"y": R.reach_dn.astype(float), "p": R.p_reach_dn, "b": R.ds.astype("category").cat.codes.astype("int64") * 100000 + R.day})])
    mr, lor, hir, ser = L.block_boot_mean(rr.y - rr.p, rr.b, block_len=bl, seed=3)
    m2, lo2, hi2, se2 = L.block_boot_mean(np.r_[R.reach_up.astype(float) - R.p_reach_up, R.reach_dn.astype(float) - R.p_reach_dn],
                                          np.r_[R.dk.values, R.dk.values], block_len=bl, seed=6)
    out.update(reach_ci_cal=(lo2, hi2))
    out.update(reach_n=len(rr), reach_obs=rr.y.mean(), reach_base=rr.p.mean(), reach_edge=mr, reach_ci=(lor, hir),
               reach_p=L.p_from_ci(mr, ser))
    return out


def fmt(o):
    return (f"n={o['n_dec']:5d} res={o['n_res']:5d} tie={o['ties']:3d} unres={o['unres']:4d} | near-first {100*o['near_first']:.1f}% "
            f"[{100*o['near_ci'][0]:.1f},{100*o['near_ci'][1]:.1f}] base_emp {100*o['base_emp']:.1f} geo {100*o['base_geo']:.1f} | "
            f"edge_emp {100*o['edge_emp']:+.2f}pp [{100*o['edge_emp_ci'][0]:+.2f},{100*o['edge_emp_ci'][1]:+.2f}] p={o['edge_emp_p']:.3f} "
            f"edge_geo {100*o['edge_geo']:+.2f} | Brier emp {o['brier_emp']:.4f} geo {o['brier_geo']:.4f} 0.5 {o['brier_half']:.4f} | "
            f"unres obs {100*o['unres_obs']:.1f} emp {100*o['unres_emp']:.1f}\n"
            f"      H1b dir n={o['dir_n']} acc {100*o['dir_acc']:.1f}% [{100*o['dir_ci'][0]:.1f},{100*o['dir_ci'][1]:.1f}] "
            f"PDcandle {100*o['dir_mom']:.1f}% diff {100*o['dir_diff_mom']:+.2f} [{100*o['dir_diff_ci'][0]:+.2f},{100*o['dir_diff_ci'][1]:+.2f}] p={o['dir_diff_p']:.3f}\n"
            f"      H1c reach n={o['reach_n']} obs {100*o['reach_obs']:.1f} base {100*o['reach_base']:.1f} edge {100*o['reach_edge']:+.2f} "
            f"[{100*o['reach_ci'][0]:+.2f},{100*o['reach_ci'][1]:+.2f}] p={o['reach_p']:.3f} calCI[{100*o['reach_ci_cal'][0]:+.2f},{100*o['reach_ci_cal'][1]:+.2f}]")


if __name__ == "__main__":
    allR = []
    for tf, names in (("1h", L.DATASETS_1H), ("5m", L.DATASETS_5M)):
        for nm in names:
            R, ns = run(nm, tf)
            allR.append(R)
            print(nm, tf, "decisions", len(R), "surface starts", ns, flush=True)
    A = pd.concat(allR, ignore_index=True)
    A.to_pickle(L.OUT + "h1_rows.pkl")
    summ = {}
    lines = []
    for tf in ("1h", "5m"):
        for ev in ("E_open", "E_ny"):
            for part in ("IS", "OOS"):
                sub = A[(A.tf == tf) & (A.ev == ev) & (A.oos if part == "OOS" else A.is_)]
                if len(sub) < 20:
                    continue
                o = summarize(sub, f"{tf} {ev} {part}")
                summ[f"{tf}|{ev}|{part}|POOLED"] = o
                lines.append(f"== {tf} {ev} {part} POOLED  " + fmt(o))
                for ds in sub.ds.unique():
                    s2 = sub[sub.ds == ds]
                    if len(s2) < 20:
                        continue
                    o2 = summarize(s2, "")
                    summ[f"{tf}|{ev}|{part}|{ds}"] = o2
                    lines.append(f"   {ds:4s} " + fmt(o2))
    txt = "\n".join(lines)
    print(txt)
    open(L.OUT + "h1_results.txt", "w").write(txt)
    json.dump(summ, open(L.OUT + "h1_results.json", "w"), default=lambda x: float(x) if np.isscalar(x) else list(map(float, x)), indent=1)
