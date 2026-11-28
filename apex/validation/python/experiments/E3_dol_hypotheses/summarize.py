# Collects the pre-registered PRIMARY tests from all result files, applies Holm within each hypothesis family and
# Benjamini-Hochberg across every primary test, and evaluates each pre-registered pass rule mechanically.
import json
import numpy as np
import e3lib as L

O = L.OUT
h1 = json.load(open(O + "h1_results.json"))
h2 = json.load(open(O + "h2_results.json"))
m = {}
for tf in ("1h", "5m"):
    m.update(json.load(open(O + f"models_results_{tf}.json")))

rows = []   # (family, label, estimate, ci_lo, ci_hi, p, direction_ok)


def add(fam, lab, est, ci, p, want_pos=True):
    ok = (est > 0) if want_pos else (est < 0)
    rows.append([fam, lab, est, ci[0], ci[1], p, ok])


# H1a
for ev in ("E_open", "E_ny"):
    for tf in ("1h", "5m"):
        o = h1[f"{tf}|{ev}|OOS|POOLED"]
        add("H1a", f"{tf} {ev} OOS race edge vs RaceSurface", o["edge_emp"], o["edge_emp_ci"], o["edge_emp_p"])
# H2
for tf in ("1h", "5m"):
    o = h2[f"{tf}|tick|OOS|R3|POOLED"]
    add("H2", f"{tf} R3 REV edge vs RaceSurface", o["edge"], o["ci"], o["p"])
for tf in ("1h", "5m"):
    o = h2[f"{tf}|tick|OOS|R3-W"]
    add("H2", f"{tf} (R3 - W) edge diff", o["diff"], o["ci"], o["p"])
# H3
for tf in ("1h", "5m"):
    o = m[f"H3|{tf}|hit60|BASE+htf vs BASE"]
    add("H3-skill", f"{tf} OOS dBrier BASE+align vs BASE", o["dbrier"], o["dbrier_ci"], o["dbrier_p"])
for tf in ("1h", "5m"):
    c = m[f"H3|{tf}|hit60|htf|coef_IS"]["htf=1"]
    add("H3-coef", f"{tf} IS aligned-vs-counter coef", c["b"], (c["b"] - 1.96 * c["se"], c["b"] + 1.96 * c["se"]), c["p"])
# H4a
for tf in ("1h", "5m"):
    o = m[f"H4a|{tf}|OOS|isolated"]
    add("H4a", f"{tf} isolated-FVG touch edge vs random level", o["edge_touch"], o["ci_touch"], o["p_touch"])
# H4b
for tf in ("1h", "5m"):
    c = m[f"H4b|{tf}|coef_IS"]["n_opp_fvg"]
    add("H4b-coef", f"{tf} IS opposing-FVG coef", c["b"], (c["b"] - 1.96 * c["se"], c["b"] + 1.96 * c["se"]), c["p"], want_pos=False)
for tf in ("1h", "5m"):
    o = m[f"H4b|{tf}|+n_opp vs BASE+mom+stack"]
    add("H4b-skill", f"{tf} OOS dBrier +n_opp", o["dbrier"], o["dbrier_ci"], o["dbrier_p"])
# H5
for tf in ("1h", "5m"):
    o = m[f"H5i|{tf}|+touch dummies vs BASE+logage"]
    add("H5i", f"{tf} OOS dBrier touch dummies", o["dbrier"], o["dbrier_ci"], o["dbrier_p"])
for tf in ("1h", "5m"):
    c = m[f"H5ii|{tf}|IS|coef"]["k=3+"]
    rows.append(["H5ii", f"{tf} IS break coef k=3+ vs k=1", c["b"], c["b"] - 1.96 * c["se"], c["b"] + 1.96 * c["se"], c["p"], True])
# H6
KEYS = ["kind", "logage", "fresh", "touch", "prior_sweeps", "n_opp", "stack", "lvr2", "session", "mom", "htf"]
for fk in KEYS:
    for tf in ("1h", "5m"):
        o = m[f"H6|{tf}|+{fk}"]
        add("H6", f"{tf} +{fk}", o["dbrier"], o["dbrier_ci"], o["dbrier_p"])

fams = {}
for i, r in enumerate(rows):
    fams.setdefault(r[0], []).append(i)
holm = np.empty(len(rows))
for f, idx in fams.items():
    holm[idx] = L.holm([rows[i][5] for i in idx])
bh = L.bh([r[5] for r in rows])
lines = [f"{'family':10s} {'test':48s} {'estimate':>11s} {'95% CI':>24s} {'p':>8s} {'p_Holm':>8s} {'q_BH':>8s} dir"]
for i, r in enumerate(rows):
    scale = 1e4 if r[0] in ("H3-skill", "H4b-skill", "H5i", "H6") else (1.0 if "coef" in r[0] or r[0] == "H5ii" else 100.0)
    unit = "e-4" if scale == 1e4 else ("pp" if scale == 100 else "")
    lines.append(f"{r[0]:10s} {r[1]:48s} {scale*r[2]:+9.3f}{unit:>2s} [{scale*r[3]:+9.3f},{scale*r[4]:+9.3f}] {r[5]:8.4f} {holm[i]:8.4f} {bh[i]:8.4f} {'ok' if r[6] else 'WRONG-SIGN'}")
txt = "\n".join(lines)
print(txt)
open(O + "primary_tests.txt", "w").write(txt)
json.dump([dict(family=r[0], test=r[1], est=r[2], lo=r[3], hi=r[4], p=r[5], p_holm=float(holm[i]), q_bh=float(bh[i]), sign_ok=bool(r[6]))
           for i, r in enumerate(rows)], open(O + "primary_tests.json", "w"), indent=1)
