"""Engine wiring check: a leaky (future) signal must look spectacular; a random signal ~ -cost."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import e2data as D, e2features as FE, e2engine as E
df, meta = D.load("NQ_1h"); F = FE.compute_features(df); cb = E.bad_prefix(df); o = F["o"]; n = len(o); H = 12
leak = np.zeros(n, int); leak[:n-H-1] = np.sign(o[1+H:n] - o[1:n-H])  # uses the future: must win big
rng = np.random.default_rng(1); rnd = rng.choice([-1, 0, 1], size=n)
for nm, st in [("leak", leak), ("random", rnd)]:
    tr = E.onset_trades(st, F, meta, cb, 0, n, H)
    print(nm, "n", len(tr), "hit", round((tr[:,5] > 0).mean(), 3), "avg pts", round(tr[:,5].mean(), 2), "cost_rt", 2*meta["cost_side"])
# check fill timing: entry = O[t+1], exit = O[t+1+H]
tr = E.onset_trades(rnd, F, meta, cb, 0, n, H)
t = tr[:,0].astype(int); assert np.allclose(tr[:,3], o[t+1]) and np.allclose(tr[:,4], o[t+1+H]); print("fill timing OK")
