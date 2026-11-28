"""No-lookahead check: states computed on a data prefix must equal the full-data states on that prefix."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import e2data as D, e2features as FE

for name in sys.argv[1:] or ["NQ_1h", "ES_1h", "BTC_1h"]:
    df, meta = D.load(name)
    df = df.iloc[:12000].reset_index(drop=True)
    Sf = FE.all_states(FE.compute_features(df))
    bad = 0
    for k in [500, 2001, 4777, 9000]:
        sub = df.iloc[:k].reset_index(drop=True)
        Sp = FE.all_states(FE.compute_features(sub))
        for v in Sf:
            mism = np.flatnonzero(Sf[v][:k] != Sp[v])
            if len(mism):
                bad += 1
                print(name, k, v, "MISMATCH at", mism[:5])
    print(name, "prefix test", "PASS" if bad == 0 else f"FAIL ({bad})")
