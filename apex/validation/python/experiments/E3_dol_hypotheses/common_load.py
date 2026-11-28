# Build and cache per-dataset frames + levels (no outcomes here).
import os, pickle, sys
import numpy as np, pandas as pd
import e3lib as L

def get(name, tf, force=False):
    fn = L.OUT + f"cache_{name}_{tf}.pkl"
    if os.path.exists(fn) and not force:
        return pickle.load(open(fn, "rb"))
    df = L.add_basic(L.load(name, tf))
    lv = L.build_levels(df)
    lv, touches = L.level_events(df, lv)
    # HTF bias: 1h chart -> trading day; 5m chart -> clock hour
    if tf == "1h":
        b, tr = L.htf_bias(df, "day")
    else:
        df["hourk"] = df.t.dt.floor("h")
        b, tr = L.htf_bias(df, "hourk")
    df["htf_bias"] = b; df["htf_trend"] = tr
    obj = {"df": df, "lv": lv, "touches": touches, "name": name, "tf": tf, "tick": L.TICK[name]}
    pickle.dump(obj, open(fn, "wb"))
    return obj

if __name__ == "__main__":
    import time
    for tf, names in (("1h", L.DATASETS_1H), ("5m", L.DATASETS_5M)):
        for nm in names:
            t0 = time.time()
            o = get(nm, tf, force=True)
            lv = o["lv"]
            print(nm, tf, "bars", len(o["df"]), "segs", o["df"].seg.nunique(), "days", o["df"].day.nunique(),
                  "levels", lv.kind.value_counts().sort_index().to_dict(), f"{time.time()-t0:.1f}s", flush=True)
