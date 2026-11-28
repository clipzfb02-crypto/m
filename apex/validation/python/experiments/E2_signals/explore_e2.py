"""E2_signals EXPLORATORY analyses (post-hoc, written after the primary results; no pass/fail weight).
(a) IS vs OOS pooled net/gross R per variant: does any OOS sign replicate in-sample?
(b) C2 long/short split and per-dataset IS/OOS (is the pooled C2|BALANCED result long-drift or concentrated?).
(c) Outcome-free signal-stability metrics for the design of FAST/BALANCED: % NEUTRAL, onsets per day,
    direction reversals per day, median run length, for persistence K in {1,2,3,5,8} with/without HTF agreement.
    These use NO returns, so they cannot overfit performance.
Writes out/explore.md.
"""
import json
import os
import sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import e2data as D  # noqa: E402
import e2features as FE  # noqa: E402
from run_e2 import CANDS  # noqa: E402

OUT = os.path.join(HERE, "out")
DS = D.DATASETS
R = {d: json.load(open(os.path.join(OUT, f"res_{d}.json"))) for d in DS}
T = {d: dict(np.load(os.path.join(OUT, f"trades_{d}.npz"))) for d in DS}
rng = np.random.default_rng(11)
L = ["# E2_signals exploratory analyses (post-hoc, descriptive only)\n"]


def boot(x, B=4000):
    if len(x) < 5:
        return (np.nan, np.nan)
    m = x[rng.integers(0, len(x), (B, len(x)))].mean(1)
    return (np.percentile(m, 2.5), np.percentile(m, 97.5))


def gross_net(d, tr):
    meta = R[d]["meta"]
    cpt = (meta["cost_side"] * (tr[:, 3] + tr[:, 4])) if meta["pct"] else 2 * meta["cost_side"] * np.ones(len(tr))
    with np.errstate(divide="ignore", invalid="ignore"):
        atr = tr[:, 5] / tr[:, 7]
    g = tr[:, 7] + cpt / atr
    ok = np.isfinite(g)
    return tr[ok, 7], g[ok], tr[ok, 1]


# (a)
L.append("## (a) Pooled net / gross R per variant, IS vs OOS (H=12; 8 datasets; trade bootstrap ignores cross-dataset correlation)\n")
L.append("| Variant | IS n | IS net R [CI] | IS gross R [CI] | OOS n | OOS net R [CI] | OOS gross R [CI] | sign replicates? |")
L.append("|---|---|---|---|---|---|---|---|")
for v in CANDS:
    k = v.replace("|", "__")
    row = {}
    for seg, kk in (("IS", k + "__IS"), ("OOS", k)):
        nets, grs = [], []
        for d in DS:
            if kk in T[d] and len(T[d][kk]):
                a, b, _ = gross_net(d, T[d][kk]); nets.append(a); grs.append(b)
        row[seg] = (np.concatenate(nets), np.concatenate(grs))
    i, o = row["IS"], row["OOS"]
    rep = "yes" if np.sign(i[1].mean()) == np.sign(o[1].mean()) else "NO"
    L.append(f"| {v} | {len(i[0])} | {i[0].mean():.3f} [{boot(i[0])[0]:.3f}, {boot(i[0])[1]:.3f}] | {i[1].mean():.3f} [{boot(i[1])[0]:.3f}, {boot(i[1])[1]:.3f}] | "
             f"{len(o[0])} | {o[0].mean():.3f} [{boot(o[0])[0]:.3f}, {boot(o[0])[1]:.3f}] | {o[1].mean():.3f} [{boot(o[1])[0]:.3f}, {boot(o[1])[1]:.3f}] | {rep} |")

# (b)
L.append("\n## (b) C2 SWEEP_RECLAIM by dataset and direction (net R per trade, H=12)\n")
L.append("| Dataset | mode | IS n | IS net R | OOS n | OOS net R | OOS long n / R | OOS short n / R |")
L.append("|---|---|---|---|---|---|---|---|")
for d in DS:
    for mode in ("FAST", "BALANCED"):
        k = f"C2_SWEEP_RECLAIM__{mode}"
        o = T[d].get(k, np.zeros((0, 9))); i = T[d].get(k + "__IS", np.zeros((0, 9)))
        lo = o[o[:, 1] > 0]; sh = o[o[:, 1] < 0]
        fm = lambda x: f"{x[:, 7].mean():.3f}" if len(x) else "n/a"  # noqa: E731
        L.append(f"| {d} | {mode} | {len(i)} | {fm(i)} | {len(o)} | {fm(o)} | {len(lo)} / {fm(lo)} | {len(sh)} / {fm(sh)} |")
for mode in ("FAST", "BALANCED"):
    k = f"C2_SWEEP_RECLAIM__{mode}"
    o = np.vstack([T[d][k] for d in DS if k in T[d] and len(T[d][k])])
    for nm, sel in (("long", o[:, 1] > 0), ("short", o[:, 1] < 0)):
        x = o[sel, 7]
        L.append(f"\nPooled OOS C2|{mode} {nm}: n {len(x)}, net R {x.mean():.3f} [{boot(x)[0]:.3f}, {boot(x)[1]:.3f}]")
    # leave-one-instrument-out for NQ: pooled without the three NQ timeframes
    o2 = np.vstack([T[d][k] for d in DS if not d.startswith("NQ") and k in T[d] and len(T[d][k])])
    L.append(f"\nPooled OOS C2|{mode} excluding NQ: n {len(o2)}, net R {o2[:, 7].mean():.3f} [{boot(o2[:, 7])[0]:.3f}, {boot(o2[:, 7])[1]:.3f}]")

# (c)
L.append("\n## (c) Signal stability vs persistence (outcome-free; full sample)\n")
L.append("onsets/day = bars where the emitted direction becomes non-zero or changes; reversals/day = onsets whose previous non-NEUTRAL "
         "direction was the opposite one; run = median length (bars) of uninterrupted non-NEUTRAL runs.\n")
L.append("| Dataset | Candidate | K | HTF | % NEUTRAL | onsets/day | reversals/day | median run (bars) |")
L.append("|---|---|---|---|---|---|---|---|")


def stab(s, sess):
    sg = np.sign(s)
    prev = np.r_[0, sg[:-1]]
    on = (sg != 0) & (sg != prev)
    last = 0; rev = 0
    for t in np.flatnonzero(sg != 0):
        if on[t] and last != 0 and sg[t] != last:
            rev += 1
        last = sg[t]
    nd = len(np.unique(sess))
    runs = []; cur = 0
    for t in range(len(sg)):
        if sg[t] != 0 and (t == 0 or sg[t] == sg[t - 1]):
            cur += 1
        elif sg[t] != 0:
            if cur: runs.append(cur)
            cur = 1
        else:
            if cur: runs.append(cur)
            cur = 0
    if cur: runs.append(cur)
    return 100 * (sg == 0).mean(), on.sum() / nd, rev / nd, float(np.median(runs)) if runs else np.nan


def persist(r, htf, k, use_htf):
    sg = np.sign(r); n = len(r); out = np.zeros(n, int)
    for t in range(k - 1, n):
        dd = sg[t]
        if dd != 0 and np.all(sg[t - k + 1:t + 1] == dd) and (not use_htf or htf[t] == dd):
            out[t] = r[t]
    return out


for d in ["NQ_5m", "NQ_1h", "ES_1h", "BTC_1h"]:
    df, meta = D.load(d)
    F = FE.compute_features(df)
    raw = FE.raw_states(F)
    sess = df.sess.values
    for c in ["C1_STRUCT_MOM", "C3_DOL_DIR", "C4_COMPOSITE", "C2_SWEEP_RECLAIM"]:
        for k in (1, 2, 3, 5, 8):
            for uh in (False, True):
                if c == "C2_SWEEP_RECLAIM" and k not in (1, 3):
                    continue
                s = persist(raw[c], F["htf"], k, uh)
                a, b, cc, e = stab(s, sess)
                tag = " (FAST)" if (k == 1 and not uh) else (" (BALANCED)" if (k == 3 and uh) else "")
                L.append(f"| {d} | {c} | {k}{tag} | {'on' if uh else 'off'} | {a:.1f} | {b:.2f} | {cc:.2f} | {e:.0f} |")
    print(d, "stability done", flush=True)

open(os.path.join(OUT, "explore.md"), "w").write("\n".join(L) + "\n")
print("\n".join(L[:40]))
