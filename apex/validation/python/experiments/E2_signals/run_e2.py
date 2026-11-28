"""E2_signals runner. Usage: python run_e2.py [DATASET ...]  (default: all)
Writes out/res_<dataset>.json and out/trades_<dataset>.npz. summarize_e2.py builds the tables.
"""
import json
import os
import sys
import time
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import e2data as D  # noqa: E402
import e2features as FE  # noqa: E402
import e2engine as E  # noqa: E402

OUT = os.path.join(HERE, "out")
HS = [6, 12, 24]
H0 = 12
CANDS = [f"{c}|{m}" for c in ["C1_STRUCT_MOM", "C2_SWEEP_RECLAIM", "C3_DOL_DIR", "C4_COMPOSITE"] for m in ["FAST", "BALANCED"]]
BASES = ["B1_EMA20_50", "B2_TSMOM48"]
N_PREREG = 60


def state_held_daily(state, F, meta, cb, sess, lo, hi, days):
    o = F["o"]
    t = np.arange(lo, hi - 2)
    p = np.sign(state[t]).astype(float)
    prev = np.r_[0.0, p[:-1]]
    bad = (cb[t + 3] - cb[t + 2]) > 0  # bar t+2 bad
    move = np.where(bad, 0.0, p * (o[t + 2] - o[t + 1]))
    cst = np.abs(p - prev) * (meta["cost_side"] * o[t + 1] if meta["pct"] else meta["cost_side"])
    ret = (move - cst) / o[t + 1]
    return E.daily_series(days, sess[t + 2], ret), p


def bh_daily(F, df, cb, lo, hi, days, meta):
    c = F["c"]; o = F["o"]
    t = np.arange(max(lo, 1) + 1, hi)
    bad = (cb[t + 1] - cb[t]) > 0
    r = np.where(bad, c[t] / o[t] - 1.0, c[t] / c[t - 1] - 1.0)
    d = E.daily_series(days, df.sess.values[t], r)
    if len(d):
        cst = (meta["cost_side"] if meta["pct"] else meta["cost_side"] / c[lo])
        d[0] -= cst; d[-1] -= cst
    return d


def seg_days(sess, lo, hi):
    s = sess[lo:hi]
    _, i = np.unique(s, return_index=True)
    return s[np.sort(i)]


def run(name, slip_stress=2.0):
    t0 = time.time()
    df, meta = D.load(name)
    F = FE.compute_features(df)
    S = FE.all_states(F)
    cb = E.bad_prefix(df)
    sess = df.sess.values
    n = len(df)
    i60 = int(0.6 * n)
    ann = meta["ann"]
    res = dict(name=name, n_bars=n, start=str(df.ts.iloc[0]), end=str(df.ts.iloc[-1]), i60=i60,
               split_ts=str(df.ts.iloc[i60]), meta={k: (float(v) if isinstance(v, (float, np.floating)) else v) for k, v in meta.items()},
               n_guard=int(df.guard.sum()), n_gap4=int((df.gap_days > 4).sum()), variants={})
    trades_keep = {}
    segs = {}
    for H in HS:
        segs[H] = {"IS": (0, i60, 0), "OOS": (i60, n, i60 + H), "FULL": (0, n, 0)}
    names = CANDS + BASES
    daily_store = {}  # (variant key, seg) -> daily
    for v in names:
        st = S[v]
        for H in HS:
            for sg, (lo, hi, ef) in segs[H].items():
                tr = E.onset_trades(st, F, meta, cb, lo, hi, H, entry_from=ef)
                days = seg_days(sess, ef if ef else lo, hi)
                daily = E.daily_series(days, sess[tr[:, 8].astype(int)] if len(tr) else [], tr[:, 6] if len(tr) else [])
                nb = hi - (ef if ef else lo)
                nneu = int((st[(ef if ef else lo):hi] == 0).sum())
                m = E.trade_metrics(tr, daily, ann, len(days), nb, nneu)
                key = f"{v}|H{H}|onset"
                res["variants"].setdefault(key, {})[sg] = m
                daily_store[(key, sg)] = daily
                if sg in ("OOS", "IS") and H == H0 and v in CANDS:
                    trades_keep[v if sg == "OOS" else v + "|IS"] = tr
                if len(tr):
                    cbp = np.array([E.cost_rt(meta, a, b) for a, b in zip(tr[:, 3], tr[:, 4])]) / tr[:, 3]
                    m["gross_bp"] = float((tr[:, 6] + cbp).mean() * 1e4)
                    m["cost_bp"] = float(cbp.mean() * 1e4)
        # state-held (H independent): use H0 embargo for OOS
        for sg, (lo, hi, ef) in segs[H0].items():
            a = ef if ef else lo
            days = seg_days(sess, a, hi)
            daily, p = state_held_daily(st, F, meta, cb, sess, a, hi, days)
            nch = int(np.abs(np.diff(np.r_[0.0, p])).sum() / 2)
            m = dict(n_pos_changes=nch, days=len(days), pct_neutral=100.0 * float((st[a:hi] == 0).mean()),
                     sharpe=E.sharpe(daily, ann), sharpe_ci=E.sharpe_ci(daily, ann), maxdd_pct=100 * E.max_dd(daily),
                     total_ret_pct=100 * float(daily.sum()), exposure=float(np.mean(p != 0)))
            key = f"{v}|state"
            res["variants"].setdefault(key, {})[sg] = m
            daily_store[(key, sg)] = daily

    # random-entry permutation (candidates, OOS + IS, H0) and cost stress
    meta_s = D.meta_for(meta["sym"], meta["tf"], slip_ticks=slip_stress)
    for v in CANDS:
        for sg in ["IS", "OOS"]:
            lo, hi, ef = segs[H0][sg]
            m = res["variants"][f"{v}|H{H0}|onset"][sg]
            if m["n"] > 0:
                p, p95, rmean = E.random_entry_pvalue(F, meta, cb, ef if ef else lo, hi, H0, m["n_long"], m["n_short"],
                                                      m["avg_bp"] / 1e4)
            else:
                p, p95, rmean = np.nan, np.nan, np.nan
            m["rand_p"] = p; m["rand_p95_bp"] = p95; m["rand_mean_bp"] = rmean
        lo, hi, ef = segs[H0]["OOS"]
        tr = E.onset_trades(S[v], F, meta_s, cb, lo, hi, H0, entry_from=ef)
        days = seg_days(sess, ef, hi)
        daily = E.daily_series(days, sess[tr[:, 8].astype(int)] if len(tr) else [], tr[:, 6] if len(tr) else [])
        res["variants"][f"{v}|H{H0}|onset"]["OOS"]["stress"] = dict(
            n=len(tr), avg_bp=float(tr[:, 6].mean() * 1e4) if len(tr) else np.nan, sharpe=E.sharpe(daily, ann),
            pf=float(tr[tr[:, 5] > 0, 5].sum() / -tr[tr[:, 5] < 0, 5].sum()) if len(tr) and (tr[:, 5] < 0).any() else np.nan)

    # DSR on OOS (distinct variants = 30 onset + 10 state)
    distinct = [k for k in res["variants"]]
    for sg in ["OOS", "FULL", "IS"]:
        srs = []
        for k in distinct:
            d = daily_store[(k, sg)]
            sd = d.std(ddof=1)
            srs.append(d.mean() / sd if sd > 0 else 0.0)
        srs = np.array(srs)
        res.setdefault("sr_trials", {})[sg] = dict(mean=float(srs.mean()), var=float(srs.var(ddof=1)), n=len(srs))
        for k in distinct:
            d = daily_store[(k, sg)]
            dsr60, sr0_60 = E.deflated_sharpe(d, srs, N_PREREG)
            dsr40, sr0_40 = E.deflated_sharpe(d, srs, len(srs))
            res["variants"][k][sg]["dsr60"] = dsr60
            res["variants"][k][sg]["dsr40"] = dsr40
            res["variants"][k][sg]["sr0_60_ann"] = sr0_60 * ann if sr0_60 == sr0_60 else np.nan

    # PBO (CSCV) on FULL daily matrix across the 40 distinct variants; also candidates-only primary (8)
    M = np.column_stack([daily_store[(k, "FULL")] for k in distinct])
    res["pbo_all40"] = E.pbo_cscv(M)
    Mc = np.column_stack([daily_store[(f"{v}|H{H0}|onset", "FULL")] for v in CANDS])
    res["pbo_cands8_H12"] = E.pbo_cscv(Mc)

    # walk-forward selection among the 8 candidates (H0)
    folds = np.linspace(0, n, 6).astype(int)
    wf_daily = []; wf_trades = []; wf_pick = []
    for k in range(1, 5):
        tr_lo, tr_hi = 0, folds[k]
        te_lo, te_hi = folds[k], folds[k + 1]
        best, best_sr = None, -np.inf
        for v in CANDS:
            tr = E.onset_trades(S[v], F, meta, cb, tr_lo, tr_hi, H0)
            days = seg_days(sess, tr_lo, tr_hi)
            dly = E.daily_series(days, sess[tr[:, 8].astype(int)] if len(tr) else [], tr[:, 6] if len(tr) else [])
            s = E.sharpe(dly, ann)
            if s > best_sr:
                best, best_sr = v, s
        tr = E.onset_trades(S[best], F, meta, cb, te_lo, te_hi, H0, entry_from=te_lo + H0)
        days = seg_days(sess, te_lo + H0, te_hi)
        dly = E.daily_series(days, sess[tr[:, 8].astype(int)] if len(tr) else [], tr[:, 6] if len(tr) else [])
        wf_daily.append(dly); wf_trades.append(tr); wf_pick.append((best, float(best_sr), float(E.sharpe(dly, ann))))
    wd = np.concatenate(wf_daily); wt = np.vstack([t for t in wf_trades if len(t)]) if any(len(t) for t in wf_trades) else np.zeros((0, 9))
    res["walkforward"] = dict(picks=wf_pick, metrics=E.trade_metrics(wt, wd, ann, len(wd), 1, 0))
    # same WF window for baselines and B&H, for comparison
    wf_base = {}
    for v in BASES:
        dl = []; tl = []
        for k in range(1, 5):
            te_lo, te_hi = folds[k], folds[k + 1]
            tr = E.onset_trades(S[v], F, meta, cb, te_lo, te_hi, H0, entry_from=te_lo + H0)
            days = seg_days(sess, te_lo + H0, te_hi)
            dl.append(E.daily_series(days, sess[tr[:, 8].astype(int)] if len(tr) else [], tr[:, 6] if len(tr) else [])); tl.append(tr)
        d = np.concatenate(dl); t = np.vstack([x for x in tl if len(x)])
        wf_base[v] = E.trade_metrics(t, d, ann, len(d), 1, 0)
    res["walkforward"]["baselines"] = wf_base
    a = folds[1] + H0
    days = seg_days(sess, a, n)
    d = bh_daily(F, df, cb, a, n, days, meta)
    res["walkforward"]["buyhold"] = dict(sharpe=E.sharpe(d, ann), sharpe_ci=E.sharpe_ci(d, ann), total_ret_pct=100 * float(d.sum()))

    # buy and hold
    res["buyhold"] = {}
    for sg, (lo, hi, ef) in segs[H0].items():
        a = ef if ef else lo
        days = seg_days(sess, a, hi)
        d = bh_daily(F, df, cb, a, hi, days, meta)
        res["buyhold"][sg] = dict(sharpe=E.sharpe(d, ann), sharpe_ci=E.sharpe_ci(d, ann), maxdd_pct=100 * E.max_dd(d),
                                  total_ret_pct=100 * float(d.sum()), days=len(days))
    res["runtime_s"] = time.time() - t0
    with open(os.path.join(OUT, f"res_{name}.json"), "w") as f:
        json.dump(res, f, default=lambda x: None if (isinstance(x, float) and not np.isfinite(x)) else (x.tolist() if hasattr(x, "tolist") else str(x)))
    np.savez_compressed(os.path.join(OUT, f"trades_{name}.npz"), **{k.replace("|", "__"): v for k, v in trades_keep.items()})
    print(name, "done", round(res["runtime_s"], 1), "s", flush=True)
    return res


if __name__ == "__main__":
    todo = sys.argv[1:] or D.DATASETS
    for nm in todo:
        run(nm)
