"""Integrity check (pre-registered): bars with |O - prevC| > 4 ATR14 or |C - prevC| > 6 ATR14.
Exclude a file if > 0.5% flagged or any jump > 15 ATR14."""
import json, numpy as np
import e4lib as E
res = {}
for fam in ("1h", "5m", "btc"):
    for name, a, mins in E.datasets(fam, include_excluded=True):
        r = E.integrity(a)
        bpd = len(a["C"]) / len(set(a["date"]))
        r["bars_per_day"] = round(bpd, 1)
        r["start"] = str(a["T"][0]); r["end"] = str(a["T"][-1])
        r["exclude_preregistered_rule"] = bool(r["rate"] > 0.005 or r["max_jump_atr"] > 15); r["exclude_final"] = name in E.EXCLUDE
        # list the largest jumps
        A = E.atr(a["H"], a["L"], a["C"], 14)
        pc = np.r_[np.nan, a["C"][:-1]]; pa = np.r_[np.nan, A[:-1]]
        g = np.maximum(np.abs(a["O"] - pc), np.abs(a["C"] - pc)) / pa
        g[:20] = 0
        top = np.argsort(-np.nan_to_num(g))[:3]
        r["top_jumps"] = [(str(a["T"][i]), round(float(g[i]), 1)) for i in top]
        res[name] = r
        print(name, r)
json.dump(res, open(E.OUT + "/data_check.json", "w"), indent=1)
