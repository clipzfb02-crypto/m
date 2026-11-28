"""R3b (EXPLORATORY check, added on resume): is the fail5-vs-ext5 mirror null unbiased on these series?
Re-runs the R3 event study on sign-flipped series (random signs on close-to-close returns, bar shapes kept),
5 seeds per family, and reports fail5 - ext5 by state. Under the null it should be ~0."""
import json
import numpy as np
import e4lib as E
import r3_breakout as R3

out = []
rng = np.random.default_rng(2026)
for fam in E.FAMS:
    for seed in range(5):
        parts = []
        for name, a, mins in E.datasets(fam):
            b = E.sign_flip(a, rng)
            E._FEAT_CACHE.pop(name + "_null", None)
            parts.append(R3.events(name + "_null", b, mins, fam, 20, 20))
            E._FEAT_CACHE.pop(name + "_null", None)
        R = {k: np.concatenate([p[k] for p in parts]) for k in parts[0]}
        for k, kn in ((0, "C"), (1, "N"), (2, "E")):
            m = (R["st"] == k) & (R["seg"] == 1)
            fe = R["fail5"][m] - R["ext5"][m]
            r = E.block_boot_mean(fe, R["blk"][m], reps=500)
            out.append(dict(fam=fam, seed=seed, state=kn, n=int(m.sum()), fail_minus_ext=r))
            print(f"{fam} seed {seed} {kn}: n={m.sum()} fail-ext {r[0]:+.3f} [{r[1]:+.3f},{r[2]:+.3f}]", flush=True)
json.dump(out, open(E.OUT + "/r3b_null.json", "w"), indent=1)
