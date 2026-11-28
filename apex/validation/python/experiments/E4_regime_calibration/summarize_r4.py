"""R4 readout tables (appended to out/summary_r4.txt)."""
import json, glob
import numpy as np
import e4lib as E
L = []
def P(s=""):
    L.append(s); print(s)
KEYM = ["RAW", "BB10", "BB50", "BB50c", "BB50s", "OE50", "BIN", "ISO", "XP", "XP_OE50", "XP_BIN", "XP_ISO"]
for design, pref in (("random", "r4_"), ("grid", "r4grid_")):
    allr = []
    for f in E.FAMS:
        allr += json.load(open(E.OUT + f"/{pref}{f}.json"))
    P(f"\n## R4 design={design}")
    P("n* = resolved probes after which CE stays < 5 pp (median | p90 across streams); truth = leave-stream-out (pop) or in-stream (in).")
    P("| fam | H | streams | " + " | ".join(KEYM) + " |")
    P("|---|---|---|" + "---|" * len(KEYM))
    for s in allr:
        P(f"| {s['fam']} | {s['H']} | {s['n_streams']} | " + " | ".join(
            f"{s['n_star'][m]['ce_pop_med']}/{s['n_star'][m]['ce_pop_p90']} ; {s['n_star'][m]['ce_in_med']}/{s['n_star'][m]['ce_in_p90']}" for m in KEYM) + " |")
    P("\nCE vs truth (pp, median across streams; pop | in) at selected resolved-probe windows:")
    for s in allr:
        wins = [w for w in s["by_n"] if w.split("-")[0] in ("0", "100", "400", "1600", "3200", "6400", "25600")]
        P(f"- {s['fam']} H={s['H']}: " + " ; ".join(
            f"n {w} (bar~{s['by_n'][w]['median_bar']:.0f}): " + ", ".join(
                f"{m} {s['by_n'][w]['models'][m]['ce_pop_med']*100:.1f}|{s['by_n'][w]['models'][m]['ce_in_med']*100:.1f}"
                for m in ("RAW", "BB50", "OE50", "ISO", "XP", "XP_OE50") if m in s['by_n'][w]['models']) for w in wins))
    P("\nPer-bucket half-width (pp): nominal Beta, empirical raw (batch means), design effect; 1.96*RMSE of BB50 / OE50 / XP_OE50 vs pop truth:")
    P("| fam | H | n_b | nominal | empirical raw | deff | BB10 vs pop | BB50 vs pop | BB50 vs in | XP_OE50 vs pop |")
    P("|---|---|---|---|---|---|---|---|---|---|")
    for s in allr:
        for nb, v in s["halfwidth"].items():
            P(f"| {s['fam']} | {s['H']} | {nb} | {v['nominal_hw']*100:.1f} | {v['emp_hw_raw']*100:.1f} | {s['deff'][nb]:.2f} | {v['hw_vs_pop']['BB10']*100:.1f} | "
              f"{v['hw_vs_pop']['BB50']*100:.1f} | {v['hw_vs_in']['BB50']*100:.1f} | {v['hw_vs_pop']['XP_OE50']*100:.1f} |")
    P("\nObserved (prequential) ECE in 500-probe windows, median/p90 (pp), and the noise floor of a perfectly calibrated forecast:")
    for s in allr:
        P(f"- {s['fam']} H={s['H']}: " + ", ".join(f"{m} {s['prequential'][m]['med']*100:.1f}/{s['prequential'][m]['p90']*100:.1f}" for m in ("RAW", "BB50", "XP", "XP_OE50", "ISO", "TRUTH")) +
          " | floor " + ", ".join(f"w{w}: {v['med']*100:.1f}/{v['p90']*100:.1f}" for w, v in s["ece_noise_floor"].items()))
    P("\nPrequential log loss vs RAW and vs BB50, % (stream bootstrap 95% CI), all probes:")
    for s in allr:
        P(f"- {s['fam']} H={s['H']}: " + "; ".join(f"{k.split(':')[1]} {v[0]:+.2f} [{v[1]:+.2f},{v[2]:+.2f}]" for k, v in s["dLL"].items()
                                                 if k.startswith("burn0:") and (k.endswith("-RAW") or k.endswith("-XP")) and k.split(':')[1].split('-')[0] in ("BB50", "BB50c", "BB50s", "OE50", "ISO", "BIN", "XP", "XP_OE50", "XP_ISO")))
open(E.OUT + "/summary_r4.txt", "w").write("\n".join(L) + "\n")
