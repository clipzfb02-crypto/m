#!/usr/bin/env python3
"""E1 summary: apply the pre-registered pass criteria (report section 1.5) to out/results.json.

Usage: python3 -I e1_summary.py   -> prints verdicts and writes out/summary.md
"""
import os, json, math
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out')
R = json.load(open(os.path.join(OUT, 'results.json')))
POOLS = {'CME_5m': 6, 'CME_1h': 5, 'BTC_1h': 1}
HS = (20, 60, 120)
VARIANTS = ['a2', 'b50', 'b100', 'b200', 'bL100', 'c0', 'c', 'd', 'e', 'f', 'g']
L = []


def f3(x):
    return 'n/a' if x is None or (isinstance(x, float) and math.isnan(x)) else f'{x:.3f}'


def fp(p):
    if p is None or (isinstance(p, float) and math.isnan(p)):
        return 'n/a'
    return f'{p:.2g}' if p >= 0.001 else '<0.001'


pt = {(r['pool'], r['period'], r['H'], r['m']): r for r in R['point']}
L.append('## Pre-registered point-forecast verdicts (holdout)\n')
L.append('| pool | H | method | MAE ratio [95% CI] | p (Holm) | sym<1 | WF-dev ratio | (a) | (b) | (c) | PASS | >=2% |')
L.append('|---|---|---|---|---|---|---|---|---|---|---|---|')
passes = []
for pool, ns in POOLS.items():
    need = math.ceil(2 * ns / 3)
    for H in HS:
        for m in VARIANTS:
            h, dv = pt[(pool, 'HOLD', H, m)], pt[(pool, 'DEV', H, m)]
            a = h['mae_ratio'] < 1 and (h['p_holm'] is not None and h['p_holm'] < 0.05)
            b = h['n_sym_better'] >= need
            c = dv['mae_ratio'] < 1
            ok = a and b and c
            big = h['mae_ratio'] <= 0.98
            if ok:
                passes.append((pool, H, m, h['mae_ratio']))
            L.append(f"| {pool} | {H} | {m} | {f3(h['mae_ratio'])} [{f3(h['mae_ci'][0])}, {f3(h['mae_ci'][1])}] | "
                     f"{fp(h['p'])} ({fp(h['p_holm'])}) | {h['n_sym_better']}/{ns} | {f3(dv['mae_ratio'])} | "
                     f"{'Y' if a else '-'} | {'Y' if b else '-'} | {'Y' if c else '-'} | {'PASS' if ok else 'fail'} | {'Y' if big else '-'} |")
L.append(f'\nPasses: {passes if passes else "none"}\n')

# nominal (uncorrected) wins, for transparency
L.append('## Nominal one-sided p < 0.05 before correction (holdout, MAE)\n')
for r in R['point']:
    if r['period'] == 'HOLD' and r['p'] is not None and not (isinstance(r['p'], float) and math.isnan(r['p'])) and r['p'] < 0.05:
        L.append(f"- {r['pool']} H={r['H']} {r['m']}: ratio {f3(r['mae_ratio'])}, p {fp(r['p'])}, Holm {fp(r['p_holm'])}, BH {fp(r['p_bh'])}")
L.append('')

# path-shape and RMSE best per pool/H
L.append('## Best method per pool and horizon (holdout)\n')
L.append('| pool | H | best MAE (ratio, p Holm) | best RMSE (ratio, p Holm) | best path-MAE (ratio, p Holm) |')
L.append('|---|---|---|---|---|')
for pool in POOLS:
    for H in HS:
        rows = [pt[(pool, 'HOLD', H, m)] for m in VARIANTS]
        bm = min(rows, key=lambda r: r['mae_ratio'])
        br = min(rows, key=lambda r: r['rmse_ratio'])
        bp = min(rows, key=lambda r: r['pmae_ratio'])
        L.append(f"| {pool} | {H} | {bm['m']} ({f3(bm['mae_ratio'])}, {fp(bm['p_holm'])}) | {br['m']} ({f3(br['rmse_ratio'])}, {fp(br['p_sq_holm'])}) | "
                 f"{bp['m']} ({f3(bp['pmae_ratio'])}, {fp(bp['p_pm_holm'])}) |")
L.append('')

# direction
L.append('## Directional edge (holdout)\n')
L.append('| pool | H | method | acc [95% CI] | always-up | diff vs up [95% CI] | Wilson lo>50% syms | edge (2/3 syms) | edge (all syms) |')
L.append('|---|---|---|---|---|---|---|---|---|')
dir_pass = []
for r in R['dir']:
    if r['period'] != 'HOLD' or 'acc_ci' not in r:
        continue
    ns = POOLS[r['pool']]
    beat_up = r['diff_ci'][0] > 0
    e23 = beat_up and r['n_sym_wilson_gt50'] >= math.ceil(2 * ns / 3)
    eall = beat_up and r['n_sym_wilson_gt50'] == ns
    if e23:
        dir_pass.append((r['pool'], r['H'], r['m']))
    if r['H'] == 60 or e23 or r['acc_ci'][0] > 0.5:
        L.append(f"| {r['pool']} | {r['H']} | {r['m']} | {f3(r['acc'])} [{f3(r['acc_ci'][0])}, {f3(r['acc_ci'][1])}] | {f3(r['acc_up'])} | "
                 f"{f3(r['diff_up'])} [{f3(r['diff_ci'][0])}, {f3(r['diff_ci'][1])}] | {r['n_sym_wilson_gt50']}/{ns} | {'Y' if e23 else '-'} | {'Y' if eall else '-'} |")
L.append(f'\nDirectional passes (2/3-symbol reading): {dir_pass if dir_pass else "none"}\n')

# economics
L.append('## Economic check (holdout, after costs)\n')
ec = sorted(R['econ'], key=lambda r: -r['mean_trade_atr'])
L.append('| pool | H | method | net ATR/trade [95% CI] | trades | DSR |')
L.append('|---|---|---|---|---|---|')
for r in ec[:12]:
    L.append(f"| {r['pool']} | {r['H']} | {r['m']} | {f3(r['mean_trade_atr'])} [{f3(r['ci'][0])}, {f3(r['ci'][1])}] | {r['n_trades']} | {f3(r['dsr'])} |")
npos = sum(1 for r in R['econ'] if r['ci'][0] > 0)
L.append(f'\nTrials with CI lower bound > 0: {npos} of {len(R["econ"])}; max DSR = {f3(max(r["dsr"] for r in R["econ"]))}\n')

# bands
L.append('## Band calibration (holdout, W = 2000): coverage within +-5pp at every k and +-8pp in every vol tercile\n')
L.append('| pool | method | scheme | cov k20 | cov k60 | cov k120 | worst tercile dev (pp) | isc k60 | calibrated |')
L.append('|---|---|---|---|---|---|---|---|---|')
bd = {}
for r in R['bands']:
    bd.setdefault((r['pool'], r['m'], r['sch']), {})[r['k']] = r
for (pool, m, sch), d in bd.items():
    if m not in ('rw', 'g', 'd', 'c'):
        continue
    covs = [d[k]['cov'] for k in HS]
    terc = [abs(v - 0.8) for k in HS for v in d[k]['cov_vt'].values()]
    ok = all(abs(c - 0.8) <= 0.05 for c in covs) and all(t <= 0.08 for t in terc)
    L.append(f"| {pool} | {m} | {sch} | {f3(covs[0])} | {f3(covs[1])} | {f3(covs[2])} | {100 * max(terc):.1f} | {d[60]['isc']:.2f} | {'Y' if ok else '-'} |")
L.append('')

# minimum sample
L.append('## Band minimum sample W (holdout, common origins)\n')
L.append('| pool | method | scheme | k | min W (cov within 3pp of 80%, isc within 2% of best) | coverage by W |')
L.append('|---|---|---|---|---|---|')
for r in R['minsample']:
    pw = r['per_W']
    if not pw:
        continue
    best = min(v['isc'] for v in pw.values())
    ok = [w for w, v in pw.items() if abs(v['cov'] - 0.8) <= 0.03 and v['isc'] <= 1.02 * best]
    order = ['100', '250', '500', '1000', '2000', '4000', 'exp']
    ok = sorted(ok, key=order.index)
    L.append(f"| {r['pool']} | {r['m']} | {r['sch']} | {r['k']} | {ok[0] if ok else 'none'} | " +
             '; '.join(f"{w}: {v['cov']:.3f}" for w, v in pw.items()) + ' |')
txt = '\n'.join(L)
open(os.path.join(OUT, 'summary.md'), 'w').write(txt)
print(txt)
