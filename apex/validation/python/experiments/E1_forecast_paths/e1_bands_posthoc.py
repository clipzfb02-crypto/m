#!/usr/bin/env python3
"""E1 POST-HOC (not pre-registered) band-window sensitivity for the zero-drift path.

Why: the pre-registered run showed every band scheme under-covering at k = 120 and the minimum-W
search landing on the largest windows. Overlapping k-step residuals are strongly autocorrelated,
so a window of W origins holds only about W/k independent outcomes. This script measures holdout
coverage as a function of c = W/k (independent horizons in the window) for:
  U0c: unconditional per-horizon quantiles of resid/ATR, window W = c*k
  U3c: the same within the current volatility tercile, window W_g = c*k per tercile
Method: rw (the recommended central path). Pools and holdout as in e1_eval.py.
All results are exploratory: the holdout has already been seen once by the pre-registered run.

Usage: python3 -I e1_bands_posthoc.py   -> out/bands_posthoc.json, prints a table
"""
import os, sys, json
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import e1_eval as E  # noqa: E402

CS = (5, 10, 17, 25, 33, 50)
HS = (20, 60, 120)


def scheme(z, sch, k, c):
    A = z['atr'].astype(float)
    r = z[f'Y_{k}'].astype(float)          # rw residual = realized move
    W = int(c * k)
    if sch == 'U0c':
        Q = E.rolling_q(r / A, k, W, E.QS)
    else:
        Q = E.rolling_q_group(r / A, z['vt'].astype(int), k, W, E.QS)
    ok, sc = E.band_scores(r, A, Q, A)
    return ok, sc


def main():
    S = E.load_all()
    out = []
    for pool, names in E.POOLS.items():
        for sch in ('U0c', 'U3c'):
            for k in HS:
                res = {(s, c): scheme(S[s], sch, k, c) for s in names for c in CS}
                usable = [c for c in CS if min(np.mean((~S[s]['dev']) & res[(s, c)][0]) / np.mean(~S[s]['dev'])
                                               for s in names) >= 0.5]
                for c in usable:
                    cov, isc, wid, vt, below, above = [], [], [], [], [], []
                    for s in names:
                        z = S[s]
                        common = ~z['dev'].copy()
                        for c2 in usable:
                            common &= res[(s, c2)][0]
                        ok, sc = res[(s, c)]
                        sel = common[ok]
                        cov.append(sc['cov'][sel]); isc.append(sc['isc'][sel]); wid.append(sc['width'][sel])
                        below.append(sc['below'][sel]); above.append(sc['above'][sel])
                        vt.append(z['vt'][ok][sel])
                    cv = np.concatenate(cov); vv = np.concatenate(vt)
                    out.append(dict(pool=pool, sch=sch, k=k, c=c, W=int(c * k), n=int(len(cv)), cov=float(cv.mean()),
                                    below=float(np.concatenate(below).mean()), above=float(np.concatenate(above).mean()),
                                    isc=float(np.concatenate(isc).mean()), width=float(np.concatenate(wid).mean()),
                                    cov_vt={int(v): float(cv[vv == v].mean()) for v in (0, 1, 2) if (vv == v).any()},
                                    usable=[int(x) for x in usable]))
                    o = out[-1]
                    print(f"{pool} {sch} k={k} c={c} W={o['W']} n={o['n']} cov={o['cov']:.3f} "
                          f"(lo {o['below']:.3f} hi {o['above']:.3f}) isc={o['isc']:.2f} terc="
                          + '/'.join(f"{o['cov_vt'].get(v, float('nan')):.3f}" for v in (0, 1, 2)), flush=True)
    json.dump(out, open(os.path.join(E.OUT, 'bands_posthoc.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
