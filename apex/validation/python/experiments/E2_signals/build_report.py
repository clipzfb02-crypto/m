"""Builds apex/research/experiments/E2_signals.md = frozen pre-registration (byte-identical, hash-checked)
+ report_template.md with <!-- TABLE:name --> markers replaced by tables generated from out/*.json / out/explore.md.
"""
import hashlib
import json
import os
import re
import sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import e2engine as E  # noqa: E402
from run_e2 import CANDS, BASES, H0  # noqa: E402
from e2data import DATASETS  # noqa: E402

OUT = os.path.join(HERE, "out")
REPORT = os.path.abspath(os.path.join(HERE, "../../../../research/experiments/E2_signals.md"))
R = {d: json.load(open(os.path.join(OUT, f"res_{d}.json"))) for d in DATASETS}
G2 = {d: json.load(open(os.path.join(OUT, f"res_{d}_g2.json"))) for d in ["ES_1h", "YM_1h", "RTY_1h"]}
SHORT = {"C1_STRUCT_MOM": "C1", "C2_SWEEP_RECLAIM": "C2", "C3_DOL_DIR": "C3", "C4_COMPOSITE": "C4",
         "B1_EMA20_50": "B1 EMA20/50", "B2_TSMOM48": "B2 TSMOM48"}


def sv(v):
    a = v.split("|")
    return SHORT[a[0]] + (" " + ("FAST" if a[1] == "FAST" else "BAL") if len(a) > 1 else "")


def f(x, nd=2):
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return "n/a"
    return f"{x:.{nd}f}"


def ci(x, nd=2):
    if x is None or x[0] is None:
        return "[n/a]"
    return f"[{f(x[0], nd)}, {f(x[1], nd)}]"


# P4 BH across 64 tests
keys, pv = [], []
for d in DATASETS:
    for v in CANDS:
        m = R[d]["variants"][f"{v}|H{H0}|onset"]["OOS"]
        keys.append((d, v)); pv.append(m["rand_p"] if m.get("rand_p") is not None else np.nan)
BH = dict(zip(keys, E.bh(pv, 0.10)))


def flags(d, v, res=None):
    res = res or R[d]
    V = res["variants"]
    base = max(V[f"{b}|H{H0}|onset"]["OOS"]["sharpe"] for b in BASES)
    m = V[f"{v}|H{H0}|onset"]["OOS"]; c = m["sharpe_ci"] or [None, None]
    p = (m["n"] >= 30, m["sharpe"] > 0 and c[0] is not None and c[0] > 0, m["sharpe"] > base,
         m.get("rand_p") is not None and m["rand_p"] < 0.05 and BH[(d, v)], m.get("dsr60") is not None and m["dsr60"] >= 0.95)
    allp = all(p)
    weak = (not allp) and p[0] and m["sharpe"] > 0 and p[2]
    return "".join("Y" if x else "." for x in p), ("PASS" if allp else ("weak" if weak else "fail"))


T = {}
# ---- T1 primary table
rows = ["| Dataset | Variant | n | hit [Wilson 95%] | avg net R [95% CI] | avg net bp | PF | Sharpe [95% CI] | maxDD % | trades/day | % NEUTRAL | rand-entry p | DSR (N=60) | P1-P5 | verdict |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
for d in DATASETS:
    V = R[d]["variants"]
    for v in CANDS + BASES:
        m = V[f"{v}|H{H0}|onset"]["OOS"]
        fl, vd = flags(d, v) if v in CANDS else ("", "baseline")
        rows.append(f"| {d} | {sv(v)} | {m['n']} | {f(m['hit'])} {ci(m['hit_ci'])} | {f(m['avg_R'],3)} {ci(m['avg_R_ci'],2)} | {f(m['avg_bp'],1)} | {f(m['pf'])} | "
                    f"{f(m['sharpe'])} {ci(m['sharpe_ci'])} | {f(m['maxdd_pct'],1)} | {f(m['trades_per_day'],2)} | {f(m['pct_neutral'],1)} | "
                    f"{f(m.get('rand_p'),3) if v in CANDS else '-'} | {f(m.get('dsr60'),3)} | {fl or '-'} | {vd} |")
T["T1"] = "\n".join(rows)

# ---- T2 verdict counts
rows = ["| Variant | PASS | weak | fail | OOS Sharpe > 0 (of 8) | beats best baseline (of 8) | min / max OOS Sharpe |", "|---|---|---|---|---|---|---|"]
for v in CANDS:
    vs = [flags(d, v)[1] for d in DATASETS]
    sh = [R[d]["variants"][f"{v}|H{H0}|onset"]["OOS"]["sharpe"] for d in DATASETS]
    beat = sum(R[d]["variants"][f"{v}|H{H0}|onset"]["OOS"]["sharpe"] > max(R[d]["variants"][f"{b}|H{H0}|onset"]["OOS"]["sharpe"] for b in BASES) for d in DATASETS)
    rows.append(f"| {sv(v)} | {vs.count('PASS')} | {vs.count('weak')} | {vs.count('fail')} | {sum(s > 0 for s in sh)} | {beat} | {min(sh):.2f} / {max(sh):.2f} |")
T["T2"] = "\n".join(rows)

# ---- T3 dataset context
rows = ["| Dataset | period | IS/OOS split | OOS session days | B&H OOS Sharpe [CI] | B1 / B2 OOS Sharpe (onset) | B1 / B2 OOS Sharpe (state-held) | SR0 (N=60, ann.) | PBO 40 variants | PBO 8 candidates | WF-selected OOS: n, Sharpe [CI] | B&H over WF window |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|"]
for d in DATASETS:
    r = R[d]; V = r["variants"]; b = r["buyhold"]["OOS"]; w = r["walkforward"]; o = V[f"C1_STRUCT_MOM|FAST|H{H0}|onset"]["OOS"]
    rows.append(f"| {d} | {r['start'][:10]} to {r['end'][:10]} | {r['split_ts'][:10]} | {o['days']} | {f(b['sharpe'])} {ci(b['sharpe_ci'])} | "
                f"{f(V['B1_EMA20_50|H12|onset']['OOS']['sharpe'])} / {f(V['B2_TSMOM48|H12|onset']['OOS']['sharpe'])} | "
                f"{f(V['B1_EMA20_50|state']['OOS']['sharpe'])} / {f(V['B2_TSMOM48|state']['OOS']['sharpe'])} | {f(o['sr0_60_ann'])} | "
                f"{f(r['pbo_all40'][0])} | {f(r['pbo_cands8_H12'][0])} | {w['metrics']['n']}, {f(w['metrics']['sharpe'])} {ci(w['metrics']['sharpe_ci'])} | {f(w['buyhold']['sharpe'])} |")
T["T3"] = "\n".join(rows)

# ---- T4 WF picks
rows = ["| Dataset | fold 2 | fold 3 | fold 4 | fold 5 |", "|---|---|---|---|---|"]
for d in DATASETS:
    rows.append(f"| {d} | " + " | ".join(f"{sv(p[0])}: {p[1]:.2f} -> {p[2]:.2f}" for p in R[d]["walkforward"]["picks"]) + " |")
T["T4"] = "\n".join(rows)

# ---- T5 gross vs net (candidates, OOS)
rows = ["| Dataset | " + " | ".join(sv(v) for v in CANDS) + " | B1 | B2 |", "|---|" + "---|" * (len(CANDS) + 2)]
for d in DATASETS:
    V = R[d]["variants"]
    cells = []
    for v in CANDS + BASES:
        m = V[f"{v}|H{H0}|onset"]["OOS"]
        cells.append(f"{f(m.get('gross_R'),2)} / {f(m.get('avg_R'),2)}")
    cost = V[f"C1_STRUCT_MOM|FAST|H{H0}|onset"]["OOS"]
    rows.append(f"| {d} (cost {f(cost.get('cost_R'),3)} R, {f(cost.get('cost_bp'),2)} bp) | " + " | ".join(cells) + " |")
T["T5"] = "\n".join(rows)

# ---- T6 horizon + state-held
rows = ["| Dataset | " + " | ".join(sv(v) for v in CANDS) + " |", "|---|" + "---|" * len(CANDS)]
for d in DATASETS:
    V = R[d]["variants"]
    rows.append(f"| {d} | " + " | ".join("/".join(f(V[f'{v}|H{H}|onset']['OOS']['sharpe'], 1) for H in (6, 12, 24)) for v in CANDS) + " |")
T["T6"] = "\n".join(rows)
rows = ["| Dataset | " + " | ".join(sv(v) for v in CANDS + BASES) + " |", "|---|" + "---|" * (len(CANDS) + 2)]
for d in DATASETS:
    V = R[d]["variants"]
    rows.append(f"| {d} | " + " | ".join(f(V[f'{v}|state']['OOS']['sharpe']) for v in CANDS + BASES) + " |")
T["T7"] = "\n".join(rows)

# ---- T8 IS vs OOS Sharpe per candidate (onset H12)
rows = ["| Dataset | " + " | ".join(sv(v) for v in CANDS) + " |", "|---|" + "---|" * len(CANDS)]
for d in DATASETS:
    V = R[d]["variants"]
    rows.append(f"| {d} | " + " | ".join(f"{f(V[f'{v}|H12|onset']['IS']['sharpe'],1)} -> {f(V[f'{v}|H12|onset']['OOS']['sharpe'],1)}" for v in CANDS) + " |")
T["T8"] = "\n".join(rows)

# ---- T9 g2 comparison
rows = ["| Dataset | guard bars g1 / g2 | candidates' OOS results | IS Sharpe range over 8 candidates g1 / g2 | PBO40 g1 / g2 | PBO8 g1 / g2 | WF Sharpe g1 / g2 | WF picks g2 |",
        "|---|---|---|---|---|---|---|---|"]
for d, r2 in G2.items():
    r1 = R[d]
    same = all(abs(r1["variants"][f"{v}|H12|onset"]["OOS"]["sharpe"] - r2["variants"][f"{v}|H12|onset"]["OOS"]["sharpe"]) < 1e-12 for v in CANDS + BASES)
    is1 = [r1["variants"][f"{v}|H12|onset"]["IS"]["sharpe"] for v in CANDS]; is2 = [r2["variants"][f"{v}|H12|onset"]["IS"]["sharpe"] for v in CANDS]
    v2 = [flags(d, v, r2)[1] for v in CANDS]
    rows.append(f"| {d} | {r1['n_guard']} / {r2['n_guard']} | {'identical (all defects are before the split)' if same else 'CHANGED'}; verdicts {v2.count('PASS')} PASS | "
                f"{min(is1):.2f}..{max(is1):.2f} / {min(is2):.2f}..{max(is2):.2f} | {f(r1['pbo_all40'][0])} / {f(r2['pbo_all40'][0])} | "
                f"{f(r1['pbo_cands8_H12'][0])} / {f(r2['pbo_cands8_H12'][0])} | {f(r1['walkforward']['metrics']['sharpe'])} / {f(r2['walkforward']['metrics']['sharpe'])} | "
                f"{'; '.join(sv(p[0]) for p in r2['walkforward']['picks'])} |")
T["T9"] = "\n".join(rows)

# ---- T10/T11 secondary + exploratory, lifted from generated files
summ = open(os.path.join(OUT, "summary.md")).read()
sec = summ.split("## Secondary hypotheses")[1].split("## Pooled OOS")[0]
T["T10"] = "\n".join(l for l in sec.splitlines()[1:] if l.startswith("|"))
exp = open(os.path.join(OUT, "explore.md")).read()
a = exp.split("## (a)")[1].split("## (b)")[0]
T["T11"] = "\n".join(l for l in a.splitlines() if l.startswith("|"))
b = exp.split("## (b)")[1].split("## (c)")[0]
T["T12"] = "\n".join(l for l in b.splitlines() if l.startswith("|"))
T["T12b"] = "\n".join("- " + l.strip() for l in b.splitlines() if l.startswith("Pooled"))
c = exp.split("## (c)")[1]
keep = [l for l in c.splitlines() if l.startswith("|") and (l.startswith("| Dataset") or l.startswith("|---") or
        (("NQ_5m" in l or "ES_1h" in l) and re.search(r"\| (1|3|8)( \((FAST|BALANCED)\))? \|", l)))]
T["T13"] = "\n".join(keep)

tpl = open(os.path.join(HERE, "report_template.md")).read()
for k, v in T.items():
    tpl = tpl.replace(f"<!-- TABLE:{k} -->", v)
assert "<!-- TABLE:" not in tpl, re.findall(r"<!-- TABLE:\w+ -->", tpl)

pre = open(os.path.join(OUT, "prereg_frozen.md")).read()
lines = pre.splitlines(keepends=True)
sectionA = "".join(lines[7:])
h = hashlib.sha256(sectionA.encode()).hexdigest()
stored = open(os.path.join(OUT, "prereg.sha256")).read().split()[1]
assert h == stored, (h, stored)
header = tpl.split("<!-- PREREG -->")[0]
body = tpl.split("<!-- PREREG -->")[1]
open(REPORT, "w").write(header + sectionA + body)
print("wrote", REPORT, "| section A sha256", h, "matches stored hash")
