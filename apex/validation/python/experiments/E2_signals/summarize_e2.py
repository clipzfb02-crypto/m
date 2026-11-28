"""Builds out/summary.md from out/res_*.json and applies the pre-registered pass criterion (A9)."""
import json
import os
import sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import e2engine as E  # noqa: E402
from run_e2 import CANDS, BASES, H0  # noqa: E402
from e2data import DATASETS  # noqa: E402

OUT = os.path.join(HERE, "out")
R = {d: json.load(open(os.path.join(OUT, f"res_{d}.json"))) for d in DATASETS}
L = []


def f(x, nd=2):
    if x is None:
        return "n/a"
    if isinstance(x, (list, tuple)):
        return "[" + ", ".join(f(v, nd) for v in x) + "]"
    if isinstance(x, float) and not np.isfinite(x):
        return "n/a"
    return f"{x:.{nd}f}" if isinstance(x, float) else str(x)


def g(m, k, nd=2):
    return f(m.get(k), nd)


# ---------- P4 BH across 64 tests
keys, pv = [], []
for d in DATASETS:
    for v in CANDS:
        m = R[d]["variants"][f"{v}|H{H0}|onset"]["OOS"]
        keys.append((d, v)); pv.append(m.get("rand_p") if m.get("rand_p") is not None else np.nan)
bh_ok = dict(zip(keys, E.bh(pv, 0.10)))
holm_ok = dict(zip(keys, E.holm(pv, 0.05)))

passes = {}
L.append("## Pass/fail table (OOS, onset engine, H=12, base costs)\n")
L.append("| Dataset | Variant | n | hit [Wilson] | avg R | avg bp [CI] | PF | Sharpe [CI] | best base Sh | rand p | BH | DSR60 | P1-P5 | verdict |")
L.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
for d in DATASETS:
    V = R[d]["variants"]
    base_sh = max(V[f"{b}|H{H0}|onset"]["OOS"]["sharpe"] for b in BASES)
    for v in CANDS:
        m = V[f"{v}|H{H0}|onset"]["OOS"]
        ci = m["sharpe_ci"] or [None, None]
        p1 = m["n"] >= 30
        p2 = m["sharpe"] > 0 and ci[0] is not None and ci[0] > 0
        p3 = m["sharpe"] > base_sh
        p4 = (m.get("rand_p") is not None and m["rand_p"] < 0.05 and bh_ok[(d, v)])
        p5 = m.get("dsr60") is not None and m["dsr60"] >= 0.95
        allp = p1 and p2 and p3 and p4 and p5
        weak = (not allp) and m["sharpe"] > 0 and p3 and p1
        verdict = "PASS" if allp else ("weak" if weak else "fail")
        passes[(d, v)] = verdict
        flags = "".join("Y" if x else "." for x in (p1, p2, p3, p4, p5))
        L.append(f"| {d} | {v} | {m['n']} | {g(m,'hit')} {f(m['hit_ci'])} | {g(m,'avg_R',3)} | {g(m,'avg_bp',1)} {f(m['avg_bp_ci'],1)} | {g(m,'pf')} | {g(m,'sharpe')} {f(m['sharpe_ci'])} | {f(base_sh)} | {g(m,'rand_p',3)} | {'Y' if bh_ok[(d,v)] else '.'} | {g(m,'dsr60',3)} | {flags} | {verdict} |")

L.append("\n### Verdict count per candidate (8 datasets)\n")
L.append("| Variant | PASS | weak | fail | datasets with PASS |")
L.append("|---|---|---|---|---|")
for v in CANDS:
    vs = [passes[(d, v)] for d in DATASETS]
    L.append(f"| {v} | {vs.count('PASS')} | {vs.count('weak')} | {vs.count('fail')} | {', '.join(d for d in DATASETS if passes[(d,v)]=='PASS') or '-'} |")

# ---------- full OOS table incl. baselines, trades/day, %neutral, maxDD, IS vs OOS
L.append("\n## IS vs OOS detail (onset engine, H=12)\n")
L.append("| Dataset | Variant | IS n | IS Sharpe | IS avg bp | OOS n | OOS Sharpe | OOS avg bp | OOS hit | OOS PF | OOS maxDD % | trades/day | % bars NEUTRAL | stress avg bp | stress Sharpe |")
L.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
for d in DATASETS:
    V = R[d]["variants"]
    for v in CANDS + BASES:
        a = V[f"{v}|H{H0}|onset"]["IS"]; b = V[f"{v}|H{H0}|onset"]["OOS"]
        s = b.get("stress", {})
        L.append(f"| {d} | {v} | {a['n']} | {g(a,'sharpe')} | {g(a,'avg_bp',1)} | {b['n']} | {g(b,'sharpe')} | {g(b,'avg_bp',1)} | {g(b,'hit')} | {g(b,'pf')} | {g(b,'maxdd_pct')} | {g(b,'trades_per_day',3)} | {g(b,'pct_neutral',1)} | {f(s.get('avg_bp'),1)} | {f(s.get('sharpe'))} |")

# ---------- horizons
L.append("\n## Horizon sensitivity (OOS Sharpe, onset engine)\n")
L.append("| Dataset | Variant | H6 | H12 | H24 |")
L.append("|---|---|---|---|---|")
for d in DATASETS:
    V = R[d]["variants"]
    for v in CANDS + BASES:
        L.append(f"| {d} | {v} | " + " | ".join(f(V[f"{v}|H{H}|onset"]["OOS"]["sharpe"]) for H in (6, 12, 24)) + " |")

# ---------- state-held
L.append("\n## State-held engine (position = sign(state)), OOS\n")
L.append("| Dataset | Variant | Sharpe [CI] | total ret % | maxDD % | exposure | pos changes | % NEUTRAL | DSR60 |")
L.append("|---|---|---|---|---|---|---|---|---|")
for d in DATASETS:
    V = R[d]["variants"]
    for v in CANDS + BASES:
        m = V[f"{v}|state"]["OOS"]
        L.append(f"| {d} | {v} | {g(m,'sharpe')} {f(m['sharpe_ci'])} | {g(m,'total_ret_pct')} | {g(m,'maxdd_pct')} | {g(m,'exposure')} | {m['n_pos_changes']} | {g(m,'pct_neutral',1)} | {g(m,'dsr60',3)} |")

# ---------- buy & hold, PBO, WF
L.append("\n## Buy-and-hold, PBO, walk-forward selection\n")
L.append("| Dataset | period | split | B&H OOS Sharpe [CI] | B&H OOS ret % | B&H OOS maxDD % | PBO (40 variants) | PBO (8 cands, H12) | WF picks (fold: pick, train Sh -> test Sh) | WF OOS n | WF Sharpe [CI] | WF avg bp | WF B1 Sh | WF B2 Sh |")
L.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
for d in DATASETS:
    r = R[d]; b = r["buyhold"]["OOS"]; w = r["walkforward"]
    picks = "; ".join(f"{p[0].replace('C1_STRUCT_MOM','C1').replace('C2_SWEEP_RECLAIM','C2').replace('C3_DOL_DIR','C3').replace('C4_COMPOSITE','C4')}: {p[1]:.2f}->{p[2]:.2f}" for p in w["picks"])
    L.append(f"| {d} | {r['start'][:10]}..{r['end'][:10]} | {r['split_ts'][:10]} | {g(b,'sharpe')} {f(b['sharpe_ci'])} | {g(b,'total_ret_pct')} | {g(b,'maxdd_pct')} | {f(r['pbo_all40'][0])} | {f(r['pbo_cands8_H12'][0])} | {picks} | {w['metrics']['n']} | {g(w['metrics'],'sharpe')} {f(w['metrics']['sharpe_ci'])} | {g(w['metrics'],'avg_bp',1)} | {f(w['baselines']['B1_EMA20_50']['sharpe'])} | {f(w['baselines']['B2_TSMOM48']['sharpe'])} |")

# ---------- pooled secondary hypotheses (OOS H12 trades)
L.append("\n## Secondary hypotheses (OOS, H=12, pooled over 8 datasets; mean net R per trade)\n")
rng = np.random.default_rng(5)


def boot_diff(a, b, B=4000):
    if len(a) < 5 or len(b) < 5:
        return (np.nan, np.nan)
    da = a[rng.integers(0, len(a), (B, len(a)))].mean(1)
    db = b[rng.integers(0, len(b), (B, len(b)))].mean(1)
    dd = da - db
    return (float(np.percentile(dd, 2.5)), float(np.percentile(dd, 97.5)))


T = {d: dict(np.load(os.path.join(OUT, f"trades_{d}.npz"))) for d in DATASETS}
L.append("| Candidate | mode | n STRONG | R STRONG | n plain | R plain | diff [95% CI] |")
L.append("|---|---|---|---|---|---|---|")
for v in CANDS:
    k = v.replace("|", "__")
    tr = np.vstack([T[d][k] for d in DATASETS if k in T[d] and len(T[d][k])])
    s = tr[tr[:, 2] == 1, 7]; p = tr[tr[:, 2] == 0, 7]
    L.append(f"| {v.split('|')[0]} | {v.split('|')[1]} | {len(s)} | {f(float(s.mean()) if len(s) else None,3)} | {len(p)} | {f(float(p.mean()) if len(p) else None,3)} | {f(float(s.mean()-p.mean()) if len(s) and len(p) else None,3)} {f(boot_diff(s,p),3)} |")
L.append("\n| Candidate | n FAST | R FAST | n BAL | R BAL | BAL − FAST [95% CI] |")
L.append("|---|---|---|---|---|---|")
for c in ["C1_STRUCT_MOM", "C2_SWEEP_RECLAIM", "C3_DOL_DIR", "C4_COMPOSITE"]:
    a = np.concatenate([T[d][f"{c}__FAST"][:, 7] for d in DATASETS if len(T[d].get(f"{c}__FAST", []))])
    b = np.concatenate([T[d][f"{c}__BALANCED"][:, 7] for d in DATASETS if len(T[d].get(f"{c}__BALANCED", []))])
    L.append(f"| {c} | {len(a)} | {a.mean():.3f} | {len(b)} | {b.mean():.3f} | {b.mean()-a.mean():.3f} {f(boot_diff(b,a),3)} |")

# Holm summary
L.append(f"\nHolm (alpha 0.05) survivors among 64 random-entry tests: {[k for k, ok in holm_ok.items() if ok] or 'none'}")
L.append(f"BH (q 0.10) survivors among 64 random-entry tests: {[k for k, ok in bh_ok.items() if ok] or 'none'}")
L.append(f"Raw p<0.05 count: {int(np.nansum(np.array(pv) < 0.05))} of {int(np.isfinite(pv).sum())} (expected by chance ~{0.05*np.isfinite(pv).sum():.1f})")
open(os.path.join(OUT, "summary.md"), "w").write("\n".join(L) + "\n")
print("\n".join(L))
