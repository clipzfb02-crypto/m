# Candidate-level dataset for H3-H6 (+ touch-event table for H5-ii). All features use bars <= t only.
import math
import numpy as np, pandas as pd
import e3lib as L, common_load as C

H_MAIN, H_SEC = 60, 20
BIG = 1e6


def explode(avail, stop, k):
    """For intervals [avail, stop): eval bars that are multiples of k. Returns (level_idx, t)."""
    e0 = ((avail + k - 1) // k) * k
    cnt = np.maximum(0, (stop - 1 - e0) // k + 1)
    cnt = np.where(stop > e0, cnt, 0)
    idx = np.repeat(np.arange(len(avail)), cnt)
    off = np.arange(cnt.sum()) - np.repeat(np.cumsum(cnt) - cnt, cnt)
    t = np.repeat(e0, cnt) + off * k
    return idx, t


def interval_count(item_key, item_price, q_key, q_lo, q_hi):
    """Count items with same key and lo < price < hi."""
    comp = item_key.astype(np.float64) * BIG + (item_price - 0.0)
    order = np.argsort(comp, kind="stable"); comp = comp[order]
    lo = q_key.astype(np.float64) * BIG + q_lo
    hi = q_key.astype(np.float64) * BIG + q_hi
    return np.searchsorted(comp, hi, side="left") - np.searchsorted(comp, lo, side="right")


def build(name, tf):
    o = C.get(name, tf)
    df, lv, touches = o["df"], o["lv"], o["touches"]
    h, l, c, atr = df.high.values, df.low.values, df.close.values, df.atr.values
    lvr, seg, day, sess = df.lvr.values, df.seg.values, df.day.values, df.sess.values
    bias, trend = df.htf_bias.values, df.htf_trend.values
    n = len(df)
    k = 4 if tf == "1h" else 12
    f60x, f60n = L.fwd_extremes(h, l, seg, H_MAIN)
    f20x, f20n = L.fwd_extremes(h, l, seg, H_SEC)
    oos0 = L.split_days(df)
    first_bar = np.r_[0, np.flatnonzero(np.diff(day)) + 1]
    oos_bar = first_bar[oos0]
    bars_day = n / (day.max() + 1)
    emb_days = math.ceil(H_MAIN / bars_day) + 1
    oos_first_ok = first_bar[min(oos0 + emb_days, len(first_bar) - 1)]
    lv = lv.reset_index(drop=True)
    K, S, P, A, E, X, F = (lv[cname].values for cname in ["kind", "side", "price", "avail", "end", "exp", "fill"])
    stop = np.minimum(E, X)
    isfvg = K == L.FVG
    # ---- active items at eval bars (all distances)
    li, t = explode(A, stop, k)
    keep = (t >= 200) & np.isfinite(atr[t])
    li, t = li[keep], t[keep]
    key = t * 2 + (S[li] > 0)
    pool_m = ~isfvg[li]
    # touched FVGs still within life: [end, exp)
    fv = np.flatnonzero(isfvg)
    tli, tt = explode(E[fv], X[fv], k)
    tli = fv[tli]
    tkey = tt * 2 + (S[tli] > 0)
    # ---- rows: levels at 0.25-6 ATR on the correct side
    cc = c[t]; aa = atr[t]
    d = S[li] * (P[li] - cc) / aa
    rm = (d >= 0.25) & (d <= 6.0) & np.isfinite(f60x[t])
    r_li, r_t, r_d = li[rm], t[rm], d[rm]
    side = S[r_li]; price = P[r_li]; kind = K[r_li]
    fv_r = kind == L.FVG
    up = side > 0
    hit60 = np.where(up, np.where(fv_r, f60x[r_t] >= price, f60x[r_t] > price),
                     np.where(fv_r, f60n[r_t] <= price, f60n[r_t] < price))
    hit20 = np.where(up, np.where(fv_r, f20x[r_t] >= price, f20x[r_t] > price),
                     np.where(fv_r, f20n[r_t] <= price, f20n[r_t] < price))
    hit20 = np.where(np.isfinite(f20x[r_t]), hit20, False)
    cr = c[r_t]
    lo = np.where(up, cr, price); hi = np.where(up, price, cr)
    rkey = r_t * 2 + up
    # stack: active same-side pools strictly between price and target
    stack = interval_count(key[pool_m], P[li][pool_m], rkey, lo, hi)
    # untouched same-side FVGs (opposing FVGs for this target) with near edge strictly between
    fm = isfvg[li]
    n_opp = interval_count(key[fm], P[li][fm], rkey, lo, hi)
    n_opp_t = interval_count(tkey, P[tli], rkey, lo, hi)
    # overlap of FVG target with any active pool within 0.25 ATR (structure overlap)
    any_key = t[pool_m]  # side-agnostic key
    ov = interval_count(any_key, P[li][pool_m], r_t, price - 0.25 * atr[r_t], price + 0.25 * atr[r_t])
    # touches / freshness (pools only)
    ntouch = np.zeros(len(r_li), np.int32); fresh = (r_t - A[r_li]).astype(float)
    for i in np.flatnonzero(~fv_r):
        tv = touches[r_li[i]]
        if len(tv):
            m = np.searchsorted(tv, r_t[i], side="right")
            if m:
                ntouch[i] = m; fresh[i] = r_t[i] - tv[m - 1]
    # prior sweeps: same-side pools traded in (t-24, t]
    tr = (~isfvg) & (E < X) & (E < n)
    ps = np.zeros(len(r_li), np.int32)
    for s_ in (1, -1):
        eb = np.sort(E[tr & (S == s_)])
        m_ = side == s_
        ps[m_] = np.searchsorted(eb, r_t[m_], side="right") - np.searchsorted(eb, r_t[m_] - 24, side="right")
    mom = side * (c[r_t] - c[np.maximum(r_t - 12, 0)]) / atr[r_t]
    R = pd.DataFrame(dict(ds=name, tf=tf, t=r_t, day=day[r_t], kind=kind, side=side, d=r_d,
                          hit60=hit60.astype(np.int8), hit20=hit20.astype(np.int8), lvr=lvr[r_t],
                          age=(r_t - A[r_li]), ntouch=ntouch, fresh=fresh, prior_sweeps=ps, stack=stack,
                          n_opp=n_opp, n_opp_t=n_opp_t, overlap=ov, mom=mom, sess=sess[r_t],
                          htf=side * bias[r_t], htf_tr=side * trend[r_t], lvl=r_li))
    R["is_"] = R.t + H_MAIN < oos_bar
    R["oos"] = R.t >= oos_first_ok
    # ---- H5-ii touch events: k-th touch of a pool, break within 12 bars
    trows = []
    for j in np.flatnonzero(~isfvg):
        tv = touches[j]
        for kk, b in enumerate(tv, start=1):
            if b + 12 >= n or seg[b + 12] != seg[b] or X[j] <= b + 12 or not np.isfinite(atr[b]):
                continue
            if E[j] <= b:
                continue
            brk = int(E[j] <= b + 12)
            trows.append((name, tf, j, K[j], kk, b, day[b], b - A[j], lvr[b], brk))
    T = pd.DataFrame(trows, columns=["ds", "tf", "lvl", "kind", "k", "t", "day", "age", "lvr", "brk"])
    T["is_"] = T.t + 12 < oos_bar
    T["oos"] = T.t >= oos_first_ok
    return R, T


if __name__ == "__main__":
    import time
    for tf, names in (("1h", L.DATASETS_1H), ("5m", L.DATASETS_5M)):
        Rs, Ts = [], []
        for nm in names:
            t0 = time.time()
            R, T = build(nm, tf)
            Rs.append(R); Ts.append(T)
            print(nm, tf, "rows", len(R), "kinds", R.kind.value_counts().sort_index().to_dict(), "touch events", len(T),
                  f"{time.time()-t0:.1f}s", flush=True)
        pd.concat(Rs, ignore_index=True).to_pickle(L.OUT + f"cands_{tf}.pkl")
        pd.concat(Ts, ignore_index=True).to_pickle(L.OUT + f"touch_{tf}.pkl")
