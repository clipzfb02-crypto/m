"""Builds the verdict tables for the report from the out/*.json files: Holm adjustment within each research
question's primary family and the pre-registered pass rules, evaluated mechanically. Writes out/summary.txt/.json."""
import json, glob
import numpy as np
import e4lib as E

L = []
S = {}


def P(s=""):
    L.append(s); print(s)


def ld(p):
    return json.load(open(E.OUT + "/" + p))


# ------------------------------------------------------------------ R1
P("## R1 volatility-regime classification")
r1 = []
for f in E.FAMS:
    r1 += ld(f"r1_{f}.json")
S["R1"] = []
for fam in E.FAMS:
    prim = [r for r in r1 if r["fam"] == fam and not r["null"] and r["cls"] == "hysA"]
    adj = E.holm([r["p_Y"] for r in prim])
    for r, q in zip(prim, adj):
        r["holm_Y"] = float(q)
    P(f"\n### {fam}: OOS R^2 of the state-mean model (hysA primary; Y = log(range/ATR14), Ya = log(range/ATR100))")
    P("| def | H | cls | dwell all/OOS | sw/1000 all/OOS | P(same@H) OOS | R2(Y) [CI] | Holm p | null R2(Y) | R2(Ya) [CI] | null R2(Ya) | lin R2(Y) |")
    P("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for H in (20, 60):
        for d in ("p_atr", "p_rv", "p_bbw", "p_des"):
            for c in ("raw", "hysA", "hysB"):
                r = [x for x in r1 if x["fam"] == fam and x["H"] == H and x["defn"] == d and x["cls"] == c and not x["null"]]
                n = [x for x in r1 if x["fam"] == fam and x["H"] == H and x["defn"] == d and x["cls"] == c and x["null"]]
                if not r:
                    continue
                r = r[0]; n = n[0]
                hp = f"{r['holm_Y']:.3g}" if c == "hysA" else ""
                P(f"| {d} | {H} | {c} | {r['dwell']:.1f}/{r.get('dwell_oos', np.nan):.1f} | {r['sw1000']:.1f}/{r.get('sw1000_oos', np.nan):.1f} | "
                  f"{r.get('pstay_oos', np.nan):.3f} | {r['R2_Y']:.3f} [{r['R2_Y_lo']:.3f},{r['R2_Y_hi']:.3f}] | {hp} | {n['R2_Y']:.3f} | "
                  f"{r['R2_Ya']:.3f} [{r['R2_Ya_lo']:.3f},{r['R2_Ya_hi']:.3f}] | {n['R2_Ya']:.3f} | {r['R2lin_Y']:.3f} |")
                S["R1"].append(dict(fam=fam, H=H, defn=d, cls=c, R2_Y=r["R2_Y"], ci=[r["R2_Y_lo"], r["R2_Y_hi"]], holm=r.get("holm_Y"),
                                    null_R2_Y=n["R2_Y"], R2_Ya=r["R2_Ya"], ci_a=[r["R2_Ya_lo"], r["R2_Ya_hi"]], null_R2_Ya=n["R2_Ya"],
                                    sw=r["sw1000"], sw_null=n["sw1000"], dwell=r["dwell"], dwell_null=n["dwell"],
                                    pstay_oos=r.get("pstay_oos"), pstay_null=n["pstay"]))
    # pass rule and hysteresis cost
    P("")
    for H in (20, 60):
        for d in ("p_atr", "p_rv", "p_bbw", "p_des"):
            rr = {c: [x for x in r1 if x["fam"] == fam and x["H"] == H and x["defn"] == d and x["cls"] == c and not x["null"]][0] for c in ("raw", "hysA", "hysB")}
            ok = rr["hysA"]["R2_Y_lo"] > 0 and rr["hysA"]["holm_Y"] < 0.05
            keep = rr["hysA"]["R2_Y"] / rr["raw"]["R2_Y"] if rr["raw"]["R2_Y"] > 0 else np.nan
            cut = 1 - rr["hysA"]["sw1000"] / rr["raw"]["sw1000"]
            keepB = rr["hysB"]["R2_Y"] / rr["raw"]["R2_Y"] if rr["raw"]["R2_Y"] > 0 else np.nan
            cutB = 1 - rr["hysB"]["sw1000"] / rr["raw"]["sw1000"]
            P(f"- {fam} H={H} {d}: R1 pass (hysA R2(Y)>0, CI>0, Holm<.05) = {ok}; hysA keeps {keep:.2f} of raw R2 with "
              f"{100*cut:.0f}% fewer switches (rule: >=0.80 and >=50% -> {bool(keep >= 0.8 and cut >= 0.5)}); "
              f"hysB keeps {keepB:.2f}, cuts {100*cutB:.0f}%")

# ------------------------------------------------------------------ R2
P("\n## R2 calibration of P(level reached within H)")
r2 = []
for f in E.FAMS:
    r2 += ld(f"r2_{f}.json")
tests = []
for res in r2:
    for k in ("P1_vs_P0", "P2_vs_P0", "P2_vs_P1"):
        c = res["cmp"][k]; tests.append((res["fam"], res["H"], k, c))
adj = E.holm([t[3]["p"] for t in tests])
P("| fam | H | comparison | dLL% [CI] | Holm p | dBrier [CI] | dREL [CI] | dREL_cond [CI] | dRES | symbols better |")
P("|---|---|---|---|---|---|---|---|---|---|")
S["R2"] = []
for (fam, H, k, c), q in zip(tests, adj):
    P(f"| {fam} | {H} | {k} | {c['dLLpct']:+.2f} [{c['lo']:+.2f},{c['hi']:+.2f}] | {q:.3g} | {c['dBS']*1e3:+.2f}e-3 [{c['dBS_lo']*1e3:+.2f},{c['dBS_hi']*1e3:+.2f}] | "
      f"{c['dREL']*1e4:+.2f}e-4 [{c['dREL_ci'][0]*1e4:+.2f},{c['dREL_ci'][1]*1e4:+.2f}] | {c['dREL_cond']*1e4:+.2f}e-4 [{c['dREL_cond_ci'][0]*1e4:+.2f},{c['dREL_cond_ci'][1]*1e4:+.2f}] | "
      f"{c['dRES']*1e4:+.2f}e-4 | {c['ds_wins']}/{c['n_ds']} |")
    S["R2"].append(dict(fam=fam, H=H, cmp=k, holm=float(q), **c))
for k in ("P1_vs_P0", "P2_vs_P0", "P2_vs_P1"):
    verdict = {}
    for H in (20, 60):
        sig = [t for t, q in zip(tests, adj) if t[2] == k and t[1] == H and t[3]["hi"] < 0 and q < 0.05]
        verdict[H] = len(sig)
    relfall = [t[3]["dREL"] < 0 for t in tests if t[2] == k]
    relcond = [t[3]["dREL_cond"] < 0 for t in tests if t[2] == k]
    P(f"- {k}: families with dLL<0, CI<0 and Holm<.05: H20 {verdict[20]}/3, H60 {verdict[60]}/3 (need >=2 at both); "
      f"marginal REL fell in {sum(relfall)}/6 family-horizons; conditional REL fell in {sum(relcond)}/6")
P("\nOOS metrics per model (LL, Brier, ECE, slope, CITL, REL, REL_cond, RES; state CITL C/N/E):")
for res in r2:
    P(f"\n{res['fam']} H={res['H']} probes={res['n_probes']} blocks={res['n_blocks']}")
    P("| model | LL | Brier | ECE | slope | int | CITL | REL | REL_cond | RES | CITL C | CITL N | CITL E | IS LL |")
    P("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for m, o in res["OOS"].items():
        bs = res["by_state"][m]
        P(f"| {m} | {o['LL']:.4f} | {o['BS']:.4f} | {o['ECE']*100:.2f} | {o['slope']:.3f} | {o['intercept']:+.3f} | {o['CITL']*100:+.2f} | "
          f"{o['REL']*1e4:.2f}e-4 | {o['REL_cond']*1e4:.2f}e-4 | {o['RES']:.4f} | {bs['0']['CITL']*100 if '0' in bs else bs[0]['CITL']*100:+.1f} | "
          f"{bs['1']['CITL']*100 if '1' in bs else bs[1]['CITL']*100:+.1f} | {bs['2']['CITL']*100 if '2' in bs else bs[2]['CITL']*100:+.1f} | {res['IS'][m]['LL']:.4f} |")
    P("exploratory comparisons: " + "; ".join(f"{k} {v['dLLpct']:+.2f}% [{v['lo']:+.2f},{v['hi']:+.2f}]" for k, v in res["cmp"].items()
                                              if k not in ("P1_vs_P0", "P2_vs_P0", "P2_vs_P1")))

# ------------------------------------------------------------------ R3
P("\n## R3 breakout from compression vs extension in expansion")
r3 = ld("r3_1h_5m_btc.json")
prim = [r for r in r3 if r["N"] == 20 and r["H"] == 20 and r["seg"] == "OOS"]
tl = []
for r in prim:
    for v in ("fail5", "asym"):
        tl.append((r["fam"], v, r["diffCE"][v]))
adj = E.holm([t[2][3] for t in tl])
P("Primary (N=20, H=20, OOS), C - E differences, Holm over 3 families x 2 outcomes:")
P("| fam | outcome | C - E [CI] | Holm p | IS C - E | same sign IS |")
P("|---|---|---|---|---|---|")
S["R3"] = []
for (fam, v, d), q in zip(tl, adj):
    isr = [r for r in r3 if r["N"] == 20 and r["H"] == 20 and r["seg"] == "IS" and r["fam"] == fam][0]["diffCE"][v]
    P(f"| {fam} | {v} | {d[0]:+.3f} [{d[1]:+.3f},{d[2]:+.3f}] | {q:.3g} | {isr[0]:+.3f} [{isr[1]:+.3f},{isr[2]:+.3f}] | {np.sign(isr[0]) == np.sign(d[0])} |")
    S["R3"].append(dict(fam=fam, outcome=v, oos=d, holm=float(q), IS=isr))
P("\nR3c fail5 - ext5 by state (mirror null = 0), OOS and IS, N=20 H=20 (Holm over 3 families x 3 states, OOS):")
tl2 = []
for r in prim:
    for kn in ("C", "N", "E"):
        b = r["by_state"][kn]; d = b["fail_minus_ext"]
        tl2.append((r["fam"], kn, d, b["n"], b["fail5"], b["ext5"]))
adj2 = E.holm([E.p_from_ci(*t[2]) for t in tl2])
P("| fam | state | n OOS | fail5 [Wilson] | ext5 [Wilson] | fail-ext [CI] | Holm p | IS fail-ext [CI] |")
P("|---|---|---|---|---|---|---|---|")
for (fam, kn, d, n, f5, e5), q in zip(tl2, adj2):
    isb = [r for r in r3 if r["N"] == 20 and r["H"] == 20 and r["seg"] == "IS" and r["fam"] == fam][0]["by_state"][kn]["fail_minus_ext"]
    P(f"| {fam} | {kn} | {n} | {f5[0]:.3f} [{f5[1]:.3f},{f5[2]:.3f}] | {e5[0]:.3f} [{e5[1]:.3f},{e5[2]:.3f}] | {d[0]:+.3f} [{d[1]:+.3f},{d[2]:+.3f}] | {q:.3g} | "
      f"{isb[0]:+.3f} [{isb[1]:+.3f},{isb[2]:+.3f}] |")
P("\nAll R3 variants, OOS C - E (fail5, failH, asym, net, mfe, mfe_b, mfe_x):")
for r in r3:
    if r["seg"] != "OOS":
        continue
    P(f"- {r['fam']} N={r['N']} H={r['H']} n={r['n']} (C {r['by_state']['C']['n']}, E {r['by_state']['E']['n']}): " +
      "; ".join(f"{k} {v[0]:+.3f} [{v[1]:+.3f},{v[2]:+.3f}]" for k, v in r["diffCE"].items() if k in ("fail5", "failH", "asym", "asym_b", "net", "mfe", "mfe_b", "mfe_x")))

# ------------------------------------------------------------------ R5
P("\n## R5 trend / range / transition")
r5rows, r5stab = [], []
for f in E.FAMS:
    j = ld(f"r5_{f}.json"); r5rows += j["rows"]; r5stab += j["stab"]
prim = [r for r in r5rows if r["cls"] == "hys" and r["seg"] == "OOS"]
adj = E.holm([r["diff_TR"][3] for r in prim])
P("Primary: OOS TREND - RANGE of y = sign(past20) * fwd_h / ATR14 (positive = momentum), hysteresis classifier, Holm over 3x3x2:")
P("| fam | h | measure | TREND - RANGE [CI] | Holm p | sign-flip null band | IS TREND - RANGE [CI] | pass |")
P("|---|---|---|---|---|---|---|---|")
S["R5"] = []
for r, q in zip(prim, adj):
    isr = [x for x in r5rows if x["fam"] == r["fam"] and x["h"] == r["h"] and x["measure"] == r["measure"] and x["cls"] == "hys" and x["seg"] == "IS"][0]
    d = r["diff_TR"]; nb = r["null_band"]
    ok = d[1] > 0 and q < 0.05 and isr["diff_TR"][0] > 0 and d[0] > nb[1]
    P(f"| {r['fam']} | {r['h']} | {r['measure']} | {d[0]:+.3f} [{d[1]:+.3f},{d[2]:+.3f}] | {q:.3g} | [{nb[0]:+.3f},{nb[1]:+.3f}] | "
      f"{isr['diff_TR'][0]:+.3f} [{isr['diff_TR'][1]:+.3f},{isr['diff_TR'][2]:+.3f}] | {ok} |")
    S["R5"].append(dict(fam=r["fam"], h=r["h"], measure=r["measure"], oos=d, holm=float(q), null=nb, IS=isr["diff_TR"], ok=bool(ok)))
P("\nOther classifiers (raw, absolute thresholds), OOS:")
for r in r5rows:
    if r["cls"] != "hys" and r["seg"] == "OOS":
        d = r["diff_TR"]; nb = r["null_band"]
        P(f"- {r['fam']} h={r['h']} {r['measure']} {r['cls']}: {d[0]:+.3f} [{d[1]:+.3f},{d[2]:+.3f}] null [{nb[0]:+.3f},{nb[1]:+.3f}]")
P("\nStability (real vs sign-flip null), H=20:")
P("| fam | measure | cls | dwell (null) | switches/1000 (null) | P(same@20) (null) | occupancy R/T/Tr |")
P("|---|---|---|---|---|---|---|")
for r in r5stab:
    if r["H"] == 20:
        P(f"| {r['fam']} | {r['measure']} | {r['cls']} | {r['dwell']:.1f} ({r['null_dwell']:.1f}) | {r['sw1000']:.1f} ({r['null_sw1000']:.1f}) | "
          f"{r['pstay']:.3f} ({r['null_pstay']:.3f}) | {r['occ'][0]:.2f}/{r['occ'][2]:.2f}/{r['occ'][1]:.2f} |")

json.dump(S, open(E.OUT + "/summary.json", "w"), indent=1, default=float)
open(E.OUT + "/summary.txt", "w").write("\n".join(L) + "\n")
