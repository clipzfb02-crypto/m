"""Sanity tests for the statistics in e2engine (added on resume, 2026-11-28).
1. PBO on pure-noise variants ~ 0.5; PBO with one genuinely dominant variant ~ 0.
2. DSR of the best of N noise strategies is not significant; DSR of a real edge is.
3. BH / Holm agree with hand-computed cases.
4. State-held engine in run_e2 equals a direct loop.
5. Onset trades never overlap and respect the segment bounds.
"""
import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import e2engine as E  # noqa: E402

rng = np.random.default_rng(0)
T, N = 800, 40
M = rng.normal(0, 0.01, (T, N))
pbo_noise = E.pbo_cscv(M)[0]
M2 = M.copy(); M2[:, 7] += 0.004                      # SR ~0.4/day: dominant
pbo_edge = E.pbo_cscv(M2)[0]
print("PBO noise", round(pbo_noise, 3), "(expect ~0.5) | PBO with dominant variant", round(pbo_edge, 3), "(expect ~0)")
assert 0.3 < pbo_noise < 0.7 and pbo_edge < 0.05

srs = M.mean(0) / M.std(0, ddof=1)
best = int(np.argmax(srs))
dsr_noise = E.deflated_sharpe(M[:, best], srs, N)[0]
srs2 = M2.mean(0) / M2.std(0, ddof=1)
dsr_edge = E.deflated_sharpe(M2[:, 7], srs2, N)[0]
print("DSR best-of-40 noise", round(dsr_noise, 3), "(expect < 0.95) | DSR real edge", round(dsr_edge, 3), "(expect > 0.95)")
assert dsr_noise < 0.95 and dsr_edge > 0.95

p = [0.001, 0.008, 0.039, 0.041, 0.042, 0.06, 0.074, 0.205, 0.212, 0.216]
print("BH q=0.05:", E.bh(p, 0.05).astype(int).tolist(), "(expect first 2)")
assert E.bh(p, 0.05).tolist() == [True, True] + [False] * 8
assert E.holm(p, 0.05).tolist() == [True, False] + [False] * 8   # 0.001<=0.005, 0.008>0.0056

# state-held vs direct loop
import e2data as D  # noqa: E402
import e2features as FE  # noqa: E402
from run_e2 import state_held_daily, seg_days  # noqa: E402
df, meta = D.load("ES_1h")
F = FE.compute_features(df); S = FE.all_states(F); cb = E.bad_prefix(df); sess = df.sess.values
st = S["C1_STRUCT_MOM|FAST"]; lo, hi = 100, 3000
days = seg_days(sess, lo, hi)
d1, _ = state_held_daily(st, F, meta, cb, sess, lo, hi, days)
o = F["o"]; acc = {}
prev = 0.0
for t in range(lo, hi - 2):
    p_ = float(np.sign(st[t]))
    mv = 0.0 if df.guard.values[t + 2] or df.gap_days.values[t + 2] > 4 else p_ * (o[t + 2] - o[t + 1])
    r = (mv - abs(p_ - prev) * meta["cost_side"]) / o[t + 1]
    acc[sess[t + 2]] = acc.get(sess[t + 2], 0.0) + r
    prev = p_
d2 = np.array([acc.get(d, 0.0) for d in days])
print("state-held max abs diff", float(np.abs(d1 - d2).max()))
assert np.allclose(d1, d2)

tr = E.onset_trades(st, F, meta, cb, lo, hi, 12, entry_from=lo + 12)
ent = tr[:, 0].astype(int) + 1; ex = tr[:, 8].astype(int)
assert (ent[1:] >= ex[:-1]).all() and ent.min() >= lo + 13 and ex.max() < hi
print("onset: no overlap, inside bounds; n =", len(tr))
print("ALL STAT TESTS PASS")
