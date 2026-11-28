"""R4: online calibration feasibility for Pine. Simulates the on-chart pipeline on independent streams.
Each bar issues 2 probes (one above, one below) at random log-uniform distances d in [0.3, 6] ATR14.
A probe resolves at its touch bar (hit) or at t+H (miss); the learner only sees resolved probes.
Pipelines:
  BB_m0   Beta-Binomial per distance bucket, prior Beta(m0*p0(d), m0*(1-p0(d))), p0 = Brownian reflection 2*Phi(-d/(0.625*sqrt(H)))
  RAW     the analytic p0(d) itself (no learning)
  BIN     analytic p0 + online binned recalibration (10 bins) on the last N=1000 resolved probes (once >= 200)
  ISO     analytic p0 + online isotonic (PAV) recalibration on the same buffer
Truth: in-stream hindsight curve (isotonic P(hit|d) on the stream's own probes) and population curve (other streams).
Pre-registered in apex/research/experiments/E4_regime_calibration.md section R4 (deviations listed there)."""
import json, sys, math
import numpy as np
import e4lib as E
from numpy.lib.stride_tricks import sliding_window_view as sw

HS = [20, 60]
EDGES = np.array([0.3, 0.75, 1.25, 1.75, 2.5, 3.5, 5.0, 6.0001])
NB = len(EDGES) - 1
M0S = [0, 10, 50]
NBUF, NMIN, REFIT = 1000, 200, 20
STREAM = {"1h": 3000, "5m": 3000, "btc": 5000}
NBINS_N = [0, 25, 50, 100, 200, 400, 800, 1600, 3200, 6400, 12800]


def pav_decreasing(x, y):
    """isotonic non-increasing fit of y on x; returns (xs_sorted, fitted)"""
    o = np.argsort(x); xs = x[o]; ys = y[o].astype(float)
    # PAV for non-increasing = PAV increasing on -y
    v = list(-ys); w = [1.0] * len(v); idx = [[i] for i in range(len(v))]
    vals, wts, cnt = [], [], []
    for i in range(len(v)):
        vals.append(v[i]); wts.append(1.0); cnt.append(1)
        while len(vals) > 1 and vals[-2] > vals[-1]:
            tw = wts[-2] + wts[-1]; tv = (vals[-2] * wts[-2] + vals[-1] * wts[-1]) / tw
            tc = cnt[-2] + cnt[-1]
            vals.pop(); wts.pop(); cnt.pop(); vals[-1] = tv; wts[-1] = tw; cnt[-1] = tc
    fit = np.repeat(-np.array(vals), cnt)
    return xs, fit


def pav_increasing(x, y):
    xs, f = pav_decreasing(-x, y)
    return -xs[::-1], f[::-1]


def curve_eval(xs, fit, x):
    i = np.clip(np.searchsorted(xs, x), 0, len(xs) - 1)
    return fit[i]


def p0(d, H):
    return np.clip(2 * E.norm_cdf(-d / (0.625 * math.sqrt(H))), 1e-3, 1 - 1e-3)


def make_probes(a, A14, start, L, H, rng):
    Hh, Ll, C = a["H"], a["L"], a["C"]
    n = len(C)
    t = np.arange(start, min(start + L, n - H))
    m = len(t)
    d = np.exp(rng.uniform(np.log(0.3), np.log(6.0), size=(m, 2)))
    lvl_up = C[t] + d[:, 0] * A14[t]; lvl_dn = C[t] - d[:, 1] * A14[t]
    WH = sw(Hh[1:], H)[t]; WL = sw(Ll[1:], H)[t]
    hu = WH >= lvl_up[:, None]; hd = WL <= lvl_dn[:, None]
    yu = hu.any(1); yd = hd.any(1)
    ru = np.where(yu, hu.argmax(1) + 1, H); rd = np.where(yd, hd.argmax(1) + 1, H)
    T = np.r_[t, t] - start
    return dict(t=T, d=np.r_[d[:, 0], d[:, 1]], y=np.r_[yu, yd].astype(float), r=T + np.r_[ru, rd])


def simulate(P, H, Lb):
    """run the online learners over one stream's probes; returns per-probe predictions."""
    t, d, y, r = P["t"], P["d"], P["y"], P["r"]
    nP = len(t)
    b = np.clip(np.searchsorted(EDGES, d, side="right") - 1, 0, NB - 1)
    pr0 = p0(d, H)
    T = Lb + H + 2
    # cumulative resolved counts by bar, per bucket
    hits_r = np.zeros((NB, T)); n_r = np.zeros((NB, T))
    np.add.at(hits_r, (b, r), y); np.add.at(n_r, (b, r), 1.0)
    ch = np.cumsum(hits_r, 1); cn = np.cumsum(n_r, 1)
    kh = ch[b, t]; kn = cn[b, t]  # resolved (r <= t) counts in the probe's bucket at prediction time
    tot_r = np.zeros(T); np.add.at(tot_r, r, 1.0); ctot = np.cumsum(tot_r)
    out = dict(n_tot=ctot[t], n_b=kn, b=b, RAW=pr0, y=y, d=d, t=t)
    p0b = p0(np.sqrt(EDGES[:-1] * EDGES[1:]), H)[b]  # bucket-centre prior
    for m0 in M0S:
        if m0 == 0:
            out[f"BB{m0}"] = np.where(kn > 0, (kh + 0.0) / np.maximum(kn, 1), 0.5)
        else:
            out[f"BB{m0}"] = (m0 * p0b + kh) / (m0 + kn)
    out["BB0"] = np.clip(out["BB0"], 1e-3, 1 - 1e-3)
    # recalibration on a bounded buffer, refitted every REFIT bars
    order = np.argsort(r, kind="stable")
    r_sorted = r[order]
    pbin = pr0.copy(); piso = pr0.copy()
    for t0 in range(0, Lb, REFIT):
        k = np.searchsorted(r_sorted, t0, side="right")  # probes with r <= t0
        if k < NMIN:
            continue
        sel = order[max(0, k - NBUF):k]
        x = pr0[sel]; yy = y[sel]
        tgt = (t >= t0) & (t < t0 + REFIT)
        if not tgt.any():
            continue
        # binned
        bins = np.minimum((x * 10).astype(int), 9)
        hb = np.bincount(bins, weights=yy, minlength=10); nb = np.bincount(bins, minlength=10)
        cen = (np.arange(10) + 0.5) / 10
        mapb = (hb + 2 * cen) / (nb + 2)
        pbin[tgt] = mapb[np.minimum((pr0[tgt] * 10).astype(int), 9)]
        # isotonic increasing map from x to y
        xs, fit = pav_increasing(x, yy)
        piso[tgt] = np.clip(np.interp(pr0[tgt], xs, fit), 1e-3, 1 - 1e-3)
    out["BIN"] = np.clip(pbin, 1e-3, 1 - 1e-3); out["ISO"] = piso
    return out


MODELS = ["RAW", "BB0", "BB10", "BB50", "BIN", "ISO"]


def ece_truth(p, pt, bins=10):
    bb = np.minimum((p * bins).astype(int), bins - 1); tot = 0.0
    for k in range(bins):
        m = bb == k
        if m.any():
            tot += m.sum() * abs(p[m].mean() - pt[m].mean())
    return tot / len(p)


def run(fam, H, rng):
    L = STREAM[fam]
    streams = []
    for name, a, mins in E.datasets(fam):
        A14 = E.atr(a["H"], a["L"], a["C"], 14)
        n = len(a["C"]); s0 = 200
        while s0 + L + H < n:
            P = make_probes(a, A14, s0, L, H, rng)
            streams.append((name, s0, P))
            s0 += L
    # truths
    res = []
    for i, (name, s0, P) in enumerate(streams):
        xs, fit = pav_decreasing(P["d"], P["y"])
        P["pt_in"] = curve_eval(xs, fit, P["d"])
        others = [Q for j, (_, _, Q) in enumerate(streams) if j != i]
        dd = np.concatenate([Q["d"] for Q in others]); yy = np.concatenate([Q["y"] for Q in others])
        if len(dd) > 200000:
            sel = rng.choice(len(dd), 200000, replace=False); dd = dd[sel]; yy = yy[sel]
        xs2, fit2 = pav_decreasing(dd, yy)
        P["pt_pop"] = curve_eval(xs2, fit2, P["d"])
        O = simulate(P, H, L)
        O["pt_in"] = P["pt_in"]; O["pt_pop"] = P["pt_pop"]; O["name"] = name; O["s0"] = s0
        # in-stream bucket truth (hindsight mean of y in bucket)
        O["bt_in"] = np.array([P["y"][O["b"] == k].mean() if np.any(O["b"] == k) else np.nan for k in range(NB)])
        res.append(O)
    return res


def summarise(fam, H, res):
    out = dict(fam=fam, H=H, n_streams=len(res), by_n={}, halfwidth={}, deff={}, prequential={}, overall={})
    # ECE vs truth as a function of resolved-probe count n_tot
    for lo, hi in zip(NBINS_N[:-1], NBINS_N[1:]):
        rowm = {}
        for m in MODELS:
            e_in, e_pop, mae = [], [], []
            for O in res:
                sel = (O["n_tot"] >= lo) & (O["n_tot"] < hi)
                if sel.sum() < 20:
                    continue
                e_in.append(ece_truth(O[m][sel], O["pt_in"][sel])); e_pop.append(ece_truth(O[m][sel], O["pt_pop"][sel]))
                mae.append(np.mean(np.abs(O[m][sel] - O["pt_in"][sel])))
            if e_in:
                rowm[m] = dict(k=len(e_in), ece_in_med=float(np.median(e_in)), ece_in_p90=float(np.percentile(e_in, 90)),
                               ece_pop_med=float(np.median(e_pop)), ece_pop_p90=float(np.percentile(e_pop, 90)),
                               mae_in_med=float(np.median(mae)))
        bars = [float(np.median(O["t"][(O["n_tot"] >= lo) & (O["n_tot"] < hi)])) for O in res if ((O["n_tot"] >= lo) & (O["n_tot"] < hi)).sum() > 0]
        out["by_n"][f"{lo}-{hi}"] = dict(models=rowm, median_bar=float(np.median(bars)) if bars else None)
    # (i) sampling spread of a raw bucket frequency from n_b consecutive resolved probes (batch means within
    #     stream x bucket, around that stream-bucket mean; K/(K-1) finite-batch correction) -> design effect
    # (ii) error of the online estimators vs the population (leave-stream-out) bucket rate when n_b is first reached
    for nb in (10, 25, 50, 100, 200, 400):
        sq = []; nom = []; z = []
        for O in res:
            r_order = np.argsort(O["t"] + 0.0)  # creation order ~ resolution order within a bucket up to H
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
        errs = {m: [] for m in ("BB0", "BB10", "BB50")}
        for O in res:
            for k in range(NB):
                sel = np.where((O["b"] == k) & (O["n_b"] >= nb))[0]
                if len(sel) == 0:
                    continue
                i = sel[0]
                popk = O["pt_pop"][O["b"] == k].mean()  # population curve averaged over this bucket's distances
                for m in errs:
                    errs[m].append(O[m][i] - popk)
        if sq:
            out["halfwidth"][nb] = dict(emp_hw_raw=float(1.96 * np.sqrt(np.mean(sq))), nominal_hw=float(1.96 * np.sqrt(np.mean(nom))),
                                        n_batches=len(sq),
                                        rmse_pop={m: float(1.96 * np.sqrt(np.mean(np.square(v)))) for m, v in errs.items() if v})
            out["deff"][nb] = float(np.mean(z))
    # prequential observed ECE in windows of 500 resolved predictions (what a chart readout would show)
    for O in res:
        O["TRUTH"] = np.clip(O["pt_in"], 1e-3, 1 - 1e-3)
    for m in MODELS + ["TRUTH"]:
        vals = []
        for O in res:
            for w0 in range(0, len(O["y"]) - 500, 500):
                sel = np.argsort(O["t"])[w0:w0 + 500]
                vals.append(E.ece(O[m][sel], O["y"][sel]))
        out["prequential"][m] = dict(med=float(np.median(vals)), p90=float(np.percentile(vals, 90)))
        yy = np.concatenate([O["y"] for O in res]); pp = np.concatenate([O[m] for O in res])
        if m == "TRUTH":
            floor = {}
            for wsz in (200, 500, 1000, 2000, 4000):
                v2 = []
                for O in res:
                    o = np.argsort(O["t"])
                    for w0 in range(0, len(o) - wsz, wsz):
                        v2.append(E.ece(O["TRUTH"][o[w0:w0 + wsz]], O["y"][o[w0:w0 + wsz]]))
                if v2:
                    floor[wsz] = dict(med=float(np.median(v2)), p90=float(np.percentile(v2, 90)), k=len(v2))
            out["ece_noise_floor"] = floor
        out["overall"][m] = dict(LL=float(E.logloss_vec(pp, yy).mean()), BS=float(E.brier_vec(pp, yy).mean()), ECE=float(E.ece(pp, yy)))
    return out


if __name__ == "__main__":
    fams = sys.argv[1:] or list(E.FAMS)
    rng = np.random.default_rng(424242)
    allout = []
    for fam in fams:
        for H in HS:
            res = run(fam, H, rng)
            s = summarise(fam, H, res)
            allout.append(s)
            print(f"== {fam} H={H} streams={s['n_streams']}")
            for k, v in s["by_n"].items():
                print(f"  n {k:>11s} bar~{v['median_bar']}: " + " ".join(f"{m} {v['models'][m]['ece_in_med']*100:.1f}/{v['models'][m]['ece_in_p90']*100:.1f}/{v['models'][m]['ece_pop_med']*100:.1f}" for m in MODELS if m in v["models"]))
            for nb, v in s["halfwidth"].items():
                print(f"  bucket n_b={nb}: nominal hw {v['nominal_hw']*100:.1f}pp emp hw(raw, batch) {v['emp_hw_raw']*100:.1f} deff {s['deff'][nb]:.2f} (batches {v['n_batches']}) | 1.96*RMSE vs pop: " + " ".join(f"{m} {x*100:.1f}" for m, x in v['rmse_pop'].items()))
            print("  prequential ECE(500) med/p90: " + " ".join(f"{m} {v['med']*100:.1f}/{v['p90']*100:.1f}" for m, v in s["prequential"].items()))
            print("  ECE noise floor of a perfectly calibrated model (window: med/p90): " + " ".join(f"{w}: {v['med']*100:.1f}/{v['p90']*100:.1f}" for w, v in s["ece_noise_floor"].items()))
            print("  overall: " + " ".join(f"{m} LL {v['LL']:.4f} ECE {v['ECE']*100:.2f}" for m, v in s["overall"].items()), flush=True)
    json.dump(allout, open(E.OUT + "/r4_" + "_".join(fams) + ".json", "w"), indent=1, default=float)
