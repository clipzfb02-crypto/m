"""R3: breakout from compression vs extension in an expanded regime (spec section 9).
Event: first close beyond the N-bar Donchian channel; state = hysA ATR-pct state at t-1.
Pre-registered in apex/research/experiments/E4_regime_calibration.md section R3."""
import json, sys
import numpy as np
import e4lib as E
from numpy.lib.stride_tricks import sliding_window_view as sw

HS = [20, 60]
NS = [20, 50]
K_FAIL = 5


def donchian(H, L, N):
    n = len(H); hi = np.full(n, np.nan); lo = np.full(n, np.nan)
    hi[N:] = sw(H[:-1], N).max(1)[: n - N]
    lo[N:] = sw(L[:-1], N).min(1)[: n - N]
    return hi, lo


def group_diff_boot(v, g, blk, g1, g0, reps=2000, seed=5):
    rng = np.random.default_rng(seed)
    ok = np.isfinite(v); v = v[ok]; g = g[ok]; blk = blk[ok]
    u, inv = np.unique(blk, return_inverse=True); k = len(u)
    s1 = np.bincount(inv, weights=v * (g == g1), minlength=k); c1 = np.bincount(inv, weights=(g == g1) * 1.0, minlength=k)
    s0 = np.bincount(inv, weights=v * (g == g0), minlength=k); c0 = np.bincount(inv, weights=(g == g0) * 1.0, minlength=k)
    est = s1.sum() / c1.sum() - s0.sum() / c0.sum()
    idx = rng.integers(0, k, size=(reps, k))
    bs = s1[idx].sum(1) / c1[idx].sum(1) - s0[idx].sum(1) / c0[idx].sum(1)
    return float(est), float(np.nanpercentile(bs, 2.5)), float(np.nanpercentile(bs, 97.5))


def events(name, a, mins, fam, H, N):
    f = E.features(name, a, mins)
    s = E.classify(f["p_atr"], **E.HYS["hysA"])
    Hh, Ll, C = a["H"], a["L"], a["C"]
    n = len(C)
    hi, lo = donchian(Hh, Ll, N)
    up = np.zeros(n, bool); dn = np.zeros(n, bool)
    up[1:] = (C[1:] > hi[1:]) & (C[:-1] <= hi[:-1])
    dn[1:] = (C[1:] < lo[1:]) & (C[:-1] >= lo[:-1])
    isx, oos, cut = E.split_idx(n, H)
    seg = np.full(n, -1); seg[isx] = 0; seg[oos] = 1
    t = np.where((up | dn) & (seg >= 0))[0]
    t = t[(t >= 1) & (s[t - 1] >= 0)]
    dirn = np.where(up[t], 1.0, -1.0)
    lev = np.where(up[t], hi[t], lo[t])
    u = f["A14"][t - 1]; ub = np.sqrt(f["A14"][t - 1] * f["A100"][t - 1])
    dist = dirn * (C[t] - lev)
    # closes over next K and H bars
    Cw5 = sw(np.r_[C[1:], np.full(K_FAIL, np.nan)], K_FAIL)[t]
    CwH = sw(np.r_[C[1:], np.full(H, np.nan)], H)[t]
    rel5 = dirn[:, None] * (Cw5 - C[t][:, None])
    relH = dirn[:, None] * (CwH - C[t][:, None])
    fail5 = (rel5 < -dist[:, None]).any(1).astype(float)
    ext5 = (rel5 >= dist[:, None]).any(1).astype(float)
    failH = (relH < -dist[:, None]).any(1).astype(float)
    mx, mn = E.fwd_max_min(Hh, Ll, H)
    mfe_up = mx[t] - C[t]; mfe_dn = C[t] - mn[t]
    mfe_dir = np.where(dirn > 0, mfe_up, mfe_dn); mfe_opp = np.where(dirn > 0, mfe_dn, mfe_up)
    net = dirn * (E.fwd_close(C, H)[t] - C[t])
    # same-state random-bar baseline for MFE (mean of both sides, all bars of that state in the same segment)
    allb = np.where((seg >= 0) & (s >= 0))[0]; allb = allb[allb >= 1]
    base = {}
    for sg in (0, 1):
        for k in range(3):
            m = allb[(seg[allb] == sg) & (s[allb - 1] == k)]
            mm = np.r_[(mx[m] - C[m]) / f["A14"][m - 1], (C[m] - mn[m]) / f["A14"][m - 1]]
            base[(sg, k)] = np.nanmean(mm)
    mfe_base = np.array([base[(seg[i], s[i - 1])] for i in t])
    blk = E.day_blocks(a, t, H, E.BPD[fam])
    return dict(seg=seg[t], st=s[t - 1], dirn=dirn, fail5=fail5, ext5=ext5, failH=failH,
                asym=(mfe_dir - mfe_opp) / u, asym_b=(mfe_dir - mfe_opp) / ub,
                net=net / u, net_b=net / ub, mfe=mfe_dir / u, mfe_b=mfe_dir / ub, mfe_x=mfe_dir / u - mfe_base,
                dist=dist / u, blk=blk, ds=np.full(len(t), name, dtype=object))


def run(fam):
    out = []
    for N in NS:
        for H in HS:
            parts = [events(name, a, mins, fam, H, N) for name, a, mins in E.datasets(fam)]
            R = {k: np.concatenate([p[k] for p in parts]) for k in parts[0]}
            ok = np.isfinite(R["asym"]) & np.isfinite(R["net"])
            R = {k: v[ok] for k, v in R.items()}
            for sg, sgn in ((0, "IS"), (1, "OOS")):
                m = R["seg"] == sg
                Q = {k: v[m] for k, v in R.items()}
                row = dict(fam=fam, N=N, H=H, seg=sgn, n=int(m.sum()), by_state={}, diffCE={})
                for k, kn in ((0, "C"), (1, "N"), (2, "E")):
                    mk = Q["st"] == k
                    nk = int(mk.sum())
                    d = dict(n=nk)
                    if nk > 0:
                        for v in ("fail5", "ext5", "failH"):
                            ph, lo_, hi_ = E.wilson(Q[v][mk].sum(), nk); d[v] = [ph, lo_, hi_]
                        for v in ("asym", "asym_b", "net", "net_b", "mfe", "mfe_b", "mfe_x", "dist"):
                            d[v] = list(E.block_boot_mean(Q[v][mk], Q["blk"][mk], reps=1000))
                        d["fail_minus_ext"] = list(E.block_boot_mean(Q["fail5"][mk] - Q["ext5"][mk], Q["blk"][mk], reps=1000))
                    row["by_state"][kn] = d
                for v in ("fail5", "failH", "asym", "asym_b", "net", "net_b", "mfe", "mfe_b", "mfe_x"):
                    est, lo_, hi_ = group_diff_boot(Q[v], Q["st"], Q["blk"], 0, 2)
                    row["diffCE"][v] = [est, lo_, hi_, E.p_from_ci(est, lo_, hi_)]
                fe = Q["fail5"] - Q["ext5"]
                est, lo_, hi_ = group_diff_boot(fe, Q["st"], Q["blk"], 0, 2)
                row["diffCE"]["fail_minus_ext"] = [est, lo_, hi_, E.p_from_ci(est, lo_, hi_)]
                out.append(row)
                bs = row["by_state"]
                print(f"{fam} N={N} H={H} {sgn} n={row['n']} | " + " | ".join(
                    f"{kn}: n={bs[kn]['n']} fail5 {bs[kn]['fail5'][0]:.3f} ext5 {bs[kn]['ext5'][0]:.3f} f-e {bs[kn]['fail_minus_ext'][0]:+.3f} [{bs[kn]['fail_minus_ext'][1]:+.3f},{bs[kn]['fail_minus_ext'][2]:+.3f}] asym {bs[kn]['asym'][0]:+.3f} [{bs[kn]['asym'][1]:+.3f},{bs[kn]['asym'][2]:+.3f}] net {bs[kn]['net'][0]:+.3f} mfe {bs[kn]['mfe'][0]:.2f} mfe_b {bs[kn]['mfe_b'][0]:.2f} mfeX {bs[kn]['mfe_x'][0]:+.3f}"
                    for kn in ("C", "N", "E") if bs[kn]["n"] > 0), flush=True)
                print("    C-E: " + " ".join(f"{k} {v[0]:+.3f} [{v[1]:+.3f},{v[2]:+.3f}]" for k, v in row["diffCE"].items()), flush=True)
    return out


if __name__ == "__main__":
    fams = sys.argv[1:] or list(E.FAMS)
    rows = []
    for fam in fams:
        rows += run(fam)
    json.dump(rows, open(E.OUT + "/r3_" + "_".join(fams) + ".json", "w"), indent=1, default=float)
