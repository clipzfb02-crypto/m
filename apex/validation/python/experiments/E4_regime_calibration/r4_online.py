"""R4: online calibration feasibility for Pine. Simulates the on-chart pipeline on independent, non-overlapping streams.
Pre-registered in apex/research/experiments/E4_regime_calibration.md section R4 (deviations are listed there).

Probe designs
  random (default; the draft's design, a deviation): each bar issues 2 probes, one above and one below the close,
         at independent log-uniform distances d in [0.3, 6] ATR14. Buckets: EDGES.
  grid   (--grid; the PRE-REGISTERED design): each bar issues 14 probes, the R2 grid {0.5,1,1.5,2,3,4,6} x 2 sides.
A probe resolves at its touch bar (hit) or at t+H (miss). The learner only uses probes with resolution bar <= t.

Pipelines (all Pine-feasible: fixed-size arrays, O(1) updates, refits on a bounded buffer)
  RAW      analytic Brownian prior p0(d) = 2*Phi(-d/(0.625*sqrt(H)))  (no learning)
  BB0/10/50  Beta-Binomial per distance bucket, prior Beta(m0*p0(bucket centre), m0*(1-p0)), m0 in {0, 10, 50}
  BB50c    EXPLORATORY: BB50 with cohort-delayed updates (every outcome is applied at t+H, hits included)
  BB50s    EXPLORATORY: BB50 split by the Hys-A ATR-percentile state at issue time, shrunk (m=50) to the BB50 bucket value
  OE50     EXPLORATORY: continuous prior p0(d) shifted per bucket by (observed - expected)/(50 + n_b)
  BIN/ISO  p0(d) + online 10-bin / isotonic (PAV) recalibration on the last 1,000 resolved probes, once >= 200
  XP       PRE-REGISTERED pipeline (b): cross-market prior = isotonic P(hit|d) fitted on OTHER symbols' streams of the
           same family whose calendar span does not overlap the target stream (BTC: the CME 1h family), no learning
  XP_OE50, XP_BIN, XP_ISO   XP followed by the same online corrections
Truth
  pt_pop   PRE-REGISTERED: leave-stream-out curve (isotonic on all other streams; same symbol's other periods included)
  pt_in    in-stream hindsight curve (isotonic on the stream's own probes), secondary
"""
import json, sys, math
import numpy as np
import e4lib as E
from numpy.lib.stride_tricks import sliding_window_view as sw

HS = [20, 60]
EDGES = np.array([0.3, 0.75, 1.25, 1.75, 2.5, 3.5, 5.0, 6.0001])
NB = len(EDGES) - 1
GRID = np.array([0.5, 1, 1.5, 2, 3, 4, 6])
M0S = [0, 10, 50]
NBUF, NMIN, REFIT = 1000, 200, 20
STREAM = {"1h": 3000, "5m": 3000, "btc": 5000}
NBINS_N = [0, 25, 50, 100, 200, 400, 800, 1600, 3200, 6400, 12800, 25600, 51200, 102400]
MODELS = ["RAW", "BB0", "BB10", "BB50", "BB50c", "BB50s", "OE50", "BIN", "ISO", "XP", "XP_OE50", "XP_BIN", "XP_ISO"]


def pav_decreasing(x, y, w=None):
    """weighted isotonic non-increasing fit of y on x; ties in x are pooled first. returns (unique xs, fit)."""
    xs, inv = np.unique(x, return_inverse=True)
    w0 = np.ones(len(y)) if w is None else w
    sw_ = np.bincount(inv, weights=w0); sy = np.bincount(inv, weights=w0 * y)
    v = list(-(sy / sw_)); wt = list(sw_)
    vals, wts, cnt = [], [], []
    for i in range(len(v)):
        vals.append(v[i]); wts.append(wt[i]); cnt.append(1)
        while len(vals) > 1 and vals[-2] > vals[-1]:
            tw = wts[-2] + wts[-1]; tv = (vals[-2] * wts[-2] + vals[-1] * wts[-1]) / tw
            tc = cnt[-2] + cnt[-1]
            vals.pop(); wts.pop(); cnt.pop(); vals[-1] = tv; wts[-1] = tw; cnt[-1] = tc
    return xs, np.repeat(-np.array(vals), cnt)


def pav_increasing(x, y):
    xs, f = pav_decreasing(-x, y)
    return -xs[::-1], f[::-1]


def curve_eval(xs, fit, x):
    """step-interpolated isotonic curve (linear between knots, flat outside)."""
    return np.interp(x, xs, fit)


def p0(d, H):
    return np.clip(2 * E.norm_cdf(-d / (0.625 * math.sqrt(H))), 1e-3, 1 - 1e-3)


def make_probes(a, A14, st, start, L, H, rng, grid=False):
    Hh, Ll, C = a["H"], a["L"], a["C"]
    n = len(C)
    t = np.arange(start, min(start + L, n - H))
    m = len(t)
    if grid:
        k = len(GRID)
        d = np.tile(np.r_[GRID, GRID], (m, 1))           # m x 14: first 7 up, last 7 down
        side = np.r_[np.zeros(k), np.ones(k)]
    else:
        d = np.exp(rng.uniform(np.log(0.3), np.log(6.0), size=(m, 2)))
        side = np.array([0.0, 1.0])
    WH = sw(Hh[1:], H)[t]; WL = sw(Ll[1:], H)[t]
    T, D, Y, R, S = [], [], [], [], []
    for j in range(d.shape[1]):
        if side[j] == 0:
            lvl = C[t] + d[:, j] * A14[t]; hh = WH >= lvl[:, None]
        else:
            lvl = C[t] - d[:, j] * A14[t]; hh = WL <= lvl[:, None]
        yy = hh.any(1); rr = np.where(yy, hh.argmax(1) + 1, H)
        T.append(t - start); D.append(d[:, j]); Y.append(yy.astype(float)); R.append(t - start + rr); S.append(st[t])
    return dict(t=np.concatenate(T), d=np.concatenate(D), y=np.concatenate(Y), r=np.concatenate(R),
                st=np.concatenate(S))


def bucket_of(d):
    return np.clip(np.searchsorted(EDGES, d, side="right") - 1, 0, NB - 1)


def cum_by_bucket(key, r, vals, nkeys, T, t):
    """sum of vals over probes with resolution bar <= t, in the probe's own key cell, evaluated at each probe's t."""
    acc = np.zeros((nkeys, T)); np.add.at(acc, (key, r), vals)
    return np.cumsum(acc, 1)[key, t]


def recal(prior, y, r, t, Lb):
    """online 10-bin and isotonic recalibration of `prior`, refitted every REFIT bars on the last NBUF resolved."""
    order = np.argsort(r, kind="stable"); r_sorted = r[order]
    pbin = prior.copy(); piso = prior.copy()
    for t0 in range(0, Lb, REFIT):
        k = np.searchsorted(r_sorted, t0, side="right")  # probes with r <= t0
        if k < NMIN:
            continue
        sel = order[max(0, k - NBUF):k]
        x = prior[sel]; yy = y[sel]
        tgt = (t >= t0) & (t < t0 + REFIT)
        if not tgt.any():
            continue
        bins = np.minimum((x * 10).astype(int), 9)
        hb = np.bincount(bins, weights=yy, minlength=10); nb = np.bincount(bins, minlength=10)
        cen = (np.arange(10) + 0.5) / 10
        mapb = (hb + 2 * cen) / (nb + 2)
        pbin[tgt] = mapb[np.minimum((prior[tgt] * 10).astype(int), 9)]
        xs, fit = pav_increasing(x, yy)
        piso[tgt] = np.interp(prior[tgt], xs, fit)
    return np.clip(pbin, 1e-3, 1 - 1e-3), np.clip(piso, 1e-3, 1 - 1e-3)


def simulate(P, H, Lb, pxp):
    t, d, y, r, st = P["t"], P["d"], P["y"], P["r"], P["st"]
    b = bucket_of(d)
    pr0 = p0(d, H)
    T = Lb + H + 2
    kh = cum_by_bucket(b, r, y, NB, T, t); kn = cum_by_bucket(b, r, np.ones_like(y), NB, T, t)
    tot_r = np.zeros(T); np.add.at(tot_r, r, 1.0); ctot = np.cumsum(tot_r)
    out = dict(n_tot=ctot[t], n_b=kn, b=b, RAW=pr0, y=y, d=d, t=t)
    p0b = p0(np.sqrt(EDGES[:-1] * EDGES[1:]), H)[b]  # bucket-centre prior
    for m0 in M0S:
        if m0 == 0:
            out["BB0"] = np.clip(np.where(kn > 0, kh / np.maximum(kn, 1), 0.5), 1e-3, 1 - 1e-3)
        else:
            out[f"BB{m0}"] = (m0 * p0b + kh) / (m0 + kn)
    # cohort-delayed updates
    rc = t + H
    khc = cum_by_bucket(b, rc, y, NB, T, t); knc = cum_by_bucket(b, rc, np.ones_like(y), NB, T, t)
    out["BB50c"] = (50 * p0b + khc) / (50 + knc)
    # state split, hierarchical shrinkage to the BB50 bucket value
    okst = st >= 0
    key = b * 3 + np.where(okst, st, 0)
    khs = cum_by_bucket(key, r, y * okst, NB * 3, T, t); kns = cum_by_bucket(key, r, okst * 1.0, NB * 3, T, t)
    out["BB50s"] = np.where(okst, (50 * out["BB50"] + khs) / (50 + kns), out["BB50"])
    # observed-minus-expected shift on a continuous prior
    for tag, pri in (("OE50", pr0), ("XP_OE50", pxp)):
        ke = cum_by_bucket(b, r, pri, NB, T, t)
        out[tag] = np.clip(pri + (kh - ke) / (50 + kn), 1e-3, 1 - 1e-3)
    out["BIN"], out["ISO"] = recal(pr0, y, r, t, Lb)
    out["XP"] = np.clip(pxp, 1e-3, 1 - 1e-3)
    out["XP_BIN"], out["XP_ISO"] = recal(out["XP"], y, r, t, Lb)
    return out


def truth_curve(d, y, grid):
    """isotonic P(hit | d); ties pooled (needed for the grid design)."""
    xs, fit = pav_decreasing(d, y)
    return xs, fit


def build_streams(fam, H, rng, grid):
    L = STREAM[fam]
    streams = []
    for name, a, mins in E.datasets(fam):
        f = E.features(name, a, mins)
        A14 = f["A14"]; st = E.classify(f["p_atr"], **E.HYS["hysA"])
        n = len(a["C"]); s0 = 200
        while s0 + L + H < n:
            P = make_probes(a, A14, st, s0, L, H, rng, grid)
            P["T0"] = a["T"][s0]; P["T1"] = a["T"][min(s0 + L, n - H) - 1]  # issue span
            streams.append((name, s0, P))
            s0 += L
    return streams


def run(fam, H, rng, grid):
    L = STREAM[fam]
    streams = build_streams(fam, H, rng, grid)
    if fam == "btc":
        xstreams = build_streams("1h", H, rng, grid)  # cross-asset prior for the single BTC series
    res = []
    for i, (name, s0, P) in enumerate(streams):
        xs, fit = truth_curve(P["d"], P["y"], grid)
        P["pt_in"] = curve_eval(xs, fit, P["d"])
        others = [Q for j, (_, _, Q) in enumerate(streams) if j != i]
        dd = np.concatenate([Q["d"] for Q in others]); yy = np.concatenate([Q["y"] for Q in others])
        if len(dd) > 200000:
            sel = rng.choice(len(dd), 200000, replace=False); dd = dd[sel]; yy = yy[sel]
        xs2, fit2 = truth_curve(dd, yy, grid)
        P["pt_pop"] = curve_eval(xs2, fit2, P["d"])
        sym = name.split("_")[0]
        if fam == "btc":
            xq = [Q for (_, _, Q) in xstreams]
        else:
            # other symbols only, and only streams whose calendar span does not overlap this stream's span
            # (avoids leaking common shocks into the prior)
            xq = [Q for (nm, _, Q) in streams if nm.split("_")[0] != sym and (Q["T1"] < P["T0"] or Q["T0"] > P["T1"])]
        if not xq:
            raise RuntimeError(f"no non-overlapping cross-market streams for {name} s0={s0}")
        dx = np.concatenate([Q["d"] for Q in xq]); yx = np.concatenate([Q["y"] for Q in xq])
        if len(dx) > 200000:
            sel = rng.choice(len(dx), 200000, replace=False); dx = dx[sel]; yx = yx[sel]
        xs3, fit3 = truth_curve(dx, yx, grid)
        pxp = curve_eval(xs3, fit3, P["d"])
        O = simulate(P, H, L, pxp)
        O["pt_in"] = P["pt_in"]; O["pt_pop"] = P["pt_pop"]; O["name"] = name; O["s0"] = s0
        res.append(O)
    return res


def ece_truth(p, pt, bins=10):
    bb = np.minimum((p * bins).astype(int), bins - 1); tot = 0.0
    for k in range(bins):
        m = bb == k
        if m.any():
            tot += m.sum() * abs(p[m].mean() - pt[m].mean())
    return tot / len(p)


def n_star(by_n, model, key, thr=0.05):
    """smallest window lower edge n such that `key` < thr in that window and in every later window with data."""
    wins = [(int(k.split("-")[0]), v["models"].get(model)) for k, v in by_n.items()]
    wins = [(lo, v) for lo, v in wins if v is not None]
    best = None
    for i, (lo, v) in enumerate(wins):
        if all(w[key] < thr for _, w in wins[i:]):
            best = lo
            break
    return best


def stream_boot_diff(a, b, reps=2000, seed=17):
    """bootstrap over streams of mean(a) - mean(b), a and b per-stream means."""
    rng = np.random.default_rng(seed); a = np.asarray(a); b = np.asarray(b); k = len(a)
    idx = rng.integers(0, k, size=(reps, k))
    dd = a[idx].mean(1) - b[idx].mean(1)
    return float(a.mean() - b.mean()), float(np.percentile(dd, 2.5)), float(np.percentile(dd, 97.5))


def summarise(fam, H, res, grid):
    out = dict(fam=fam, H=H, design="grid" if grid else "random", n_streams=len(res), by_n={}, halfwidth={}, deff={},
               prequential={}, overall={}, n_star={}, dLL={})
    for lo, hi in zip(NBINS_N[:-1], NBINS_N[1:]):
        rowm = {}
        for m in MODELS:
            cp, ci, ei = [], [], []
            for O in res:
                sel = (O["n_tot"] >= lo) & (O["n_tot"] < hi)
                if sel.sum() < 20:
                    continue
                cp.append(np.mean(np.abs(O[m][sel] - O["pt_pop"][sel])))
                ci.append(np.mean(np.abs(O[m][sel] - O["pt_in"][sel])))
                ei.append(ece_truth(O[m][sel], O["pt_in"][sel]))
            if cp:
                rowm[m] = dict(k=len(cp), ce_pop_med=float(np.median(cp)), ce_pop_p90=float(np.percentile(cp, 90)),
                               ce_in_med=float(np.median(ci)), ce_in_p90=float(np.percentile(ci, 90)),
                               ece_in_med=float(np.median(ei)))
        bars = [float(np.median(O["t"][(O["n_tot"] >= lo) & (O["n_tot"] < hi)])) for O in res
                if ((O["n_tot"] >= lo) & (O["n_tot"] < hi)).sum() > 0]
        if rowm:
            out["by_n"][f"{lo}-{hi}"] = dict(models=rowm, median_bar=float(np.median(bars)) if bars else None)
    for m in MODELS:
        out["n_star"][m] = {k: n_star(out["by_n"], m, k) for k in ("ce_pop_med", "ce_pop_p90", "ce_in_med", "ce_in_p90")}
    # per-bucket spread of a raw frequency from n_b consecutive probes (batch means) -> empirical half-width, deff;
    # and the error of the online estimators vs the leave-stream-out bucket rate when n_b is first reached
    for nb in (10, 25, 50, 100, 200, 400):
        sq = []; nom = []; z = []
        for O in res:
            r_order = np.argsort(O["t"], kind="stable")
            for k in range(NB):
                yk = O["y"][r_order][O["b"][r_order] == k]
                K = len(yk) // nb
                if K < 2:
                    continue
                bm = yk[: K * nb].reshape(K, nb).mean(1); pk = yk[: K * nb].mean()
                if pk <= 0 or pk >= 1:
                    continue
                dev2 = np.square(bm - pk) * K / (K - 1)
                sq.extend(dev2); nom.extend([pk * (1 - pk) / nb] * K); z.extend(dev2 / (pk * (1 - pk) / nb))
        errs = {m: [] for m in ("BB0", "BB10", "BB50", "BB50c", "OE50", "XP_OE50")}
        for O in res:
            for k in range(NB):
                sel = np.where((O["b"] == k) & (O["n_b"] >= nb))[0]
                if len(sel) == 0:
                    continue
                i = sel[0]
                popk = O["pt_pop"][O["b"] == k].mean()
                ink = O["pt_in"][O["b"] == k].mean()
                for m in errs:
                    if m in ("OE50", "XP_OE50"):  # continuous models: compare with the truth at this probe's distance
                        errs[m].append((O[m][i] - O["pt_pop"][i], O[m][i] - O["pt_in"][i]))
                    else:                         # bucket-constant models: compare with the bucket-average truth
                        errs[m].append((O[m][i] - popk, O[m][i] - ink))
        if sq:
            out["halfwidth"][nb] = dict(emp_hw_raw=float(1.96 * np.sqrt(np.mean(sq))),
                                        nominal_hw=float(1.96 * np.sqrt(np.mean(nom))), n_batches=len(sq),
                                        hw_vs_pop={m: float(1.96 * np.sqrt(np.mean(np.square([e[0] for e in v])))) for m, v in errs.items() if v},
                                        hw_vs_in={m: float(1.96 * np.sqrt(np.mean(np.square([e[1] for e in v])))) for m, v in errs.items() if v})
            out["deff"][nb] = float(np.mean(z))
    for O in res:
        O["TRUTH"] = np.clip(O["pt_in"], 1e-3, 1 - 1e-3)
    for m in MODELS + ["TRUTH"]:
        vals = []
        for O in res:
            o = np.argsort(O["t"], kind="stable")
            for w0 in range(0, len(o) - 500, 500):
                sel = o[w0:w0 + 500]
                vals.append(E.ece(O[m][sel], O["y"][sel]))
        out["prequential"][m] = dict(med=float(np.median(vals)), p90=float(np.percentile(vals, 90)))
        yy = np.concatenate([O["y"] for O in res]); pp = np.concatenate([O[m] for O in res])
        out["overall"][m] = dict(LL=float(E.logloss_vec(pp, yy).mean()), BS=float(E.brier_vec(pp, yy).mean()),
                                 ECE=float(E.ece(pp, yy)))
    floor = {}
    for wsz in (200, 500, 1000, 2000, 4000):
        v2 = []
        for O in res:
            o = np.argsort(O["t"], kind="stable")
            for w0 in range(0, len(o) - wsz, wsz):
                v2.append(E.ece(O["TRUTH"][o[w0:w0 + wsz]], O["y"][o[w0:w0 + wsz]]))
        if v2:
            floor[wsz] = dict(med=float(np.median(v2)), p90=float(np.percentile(v2, 90)), k=len(v2))
    out["ece_noise_floor"] = floor
    # prequential log loss, per stream, all probes and after burn-in (n_tot >= 800); stream bootstrap of differences
    for burn in (0, 800):
        per = {m: [] for m in MODELS}
        for O in res:
            sel = O["n_tot"] >= burn
            for m in MODELS:
                per[m].append(E.logloss_vec(O[m][sel], O["y"][sel]).mean())
        for m in MODELS:
            for ref in ("RAW", "BB50", "XP"):
                if m != ref:
                    est, lo, hi = stream_boot_diff(per[m], per[ref])
                    out["dLL"][f"burn{burn}:{m}-{ref}"] = [100 * est / np.mean(per[ref]), 100 * lo / np.mean(per[ref]),
                                                            100 * hi / np.mean(per[ref])]
    return out


if __name__ == "__main__":
    args = sys.argv[1:]
    grid = "--grid" in args
    fams = [x for x in args if not x.startswith("--")] or list(E.FAMS)
    rng = np.random.default_rng(424242)
    allout = []
    for fam in fams:
        for H in HS:
            res = run(fam, H, rng, grid)
            s = summarise(fam, H, res, grid)
            allout.append(s)
            print(f"== {fam} H={H} design={s['design']} streams={s['n_streams']}")
            for k, v in s["by_n"].items():
                print(f"  n {k:>12s} bar~{v['median_bar']}: " + " ".join(
                    f"{m} {v['models'][m]['ce_pop_med']*100:.1f}/{v['models'][m]['ce_pop_p90']*100:.1f}|{v['models'][m]['ce_in_med']*100:.1f}"
                    for m in MODELS if m in v["models"]))
            print("  n* (CE_pop med<5pp, p90<5pp | CE_in med, p90): " + " ".join(
                f"{m} {v['ce_pop_med']}/{v['ce_pop_p90']}|{v['ce_in_med']}/{v['ce_in_p90']}" for m, v in s["n_star"].items()))
            for nb, v in s["halfwidth"].items():
                print(f"  bucket n_b={nb}: nominal hw {v['nominal_hw']*100:.1f}pp emp hw {v['emp_hw_raw']*100:.1f} deff {s['deff'][nb]:.2f}"
                      f" (batches {v['n_batches']}) | hw vs pop: " + " ".join(f"{m} {x*100:.1f}" for m, x in v['hw_vs_pop'].items()) +
                      " | vs in-stream: " + " ".join(f"{m} {x*100:.1f}" for m, x in v['hw_vs_in'].items()))
            print("  prequential ECE(500) med/p90: " + " ".join(f"{m} {v['med']*100:.1f}/{v['p90']*100:.1f}" for m, v in s["prequential"].items()))
            print("  ECE noise floor (perfect model; window: med/p90): " + " ".join(f"{w}: {v['med']*100:.1f}/{v['p90']*100:.1f}" for w, v in s["ece_noise_floor"].items()))
            print("  overall: " + " ".join(f"{m} LL {v['LL']:.4f} ECE {v['ECE']*100:.2f}" for m, v in s["overall"].items()))
            print("  dLL% (stream bootstrap): " + " ".join(f"{k} {v[0]:+.2f} [{v[1]:+.2f},{v[2]:+.2f}]" for k, v in s["dLL"].items()
                                                        if k.endswith("-BB50") or k.endswith("-RAW")), flush=True)
    json.dump(allout, open(E.OUT + ("/r4grid_" if grid else "/r4_") + "_".join(fams) + ".json", "w"), indent=1, default=float)
