# Trade execution around a Draw on Liquidity: combined final study (researchers A + B)

Domain: what a trader does with a DOL target, and how the engine should support it.
- Entry models aimed at a DOL: sweep → MSS → FVG/OB; iFVG continuation; breaker retest; market entry at activation; limit entry in a zone.
- Invalidation: beyond the opposing pool, beyond the sweep extreme, beyond the entry array, protected swing, MAE-based.
- Management: partials at intermediate liquidity, break-even and trailing stops, time stops, R:R, expectancy, MAE/MFE, ETA, costs, sizing.
- Decision-time information on the chart, and actionable alerts.
- Audit of the engine's invalidation, R:R, WIN≤H race, EV, ETA and ledger logic (`baseline_v2.pine` = `indicators/dol_engine.pine`; line numbers refer to it).

**Provenance tags.**
- **[A✓]** A's item, re-checked by B against the source, the code or the raw output.
- **[A]** A's item, kept as A read it. B could not re-open the source because WebFetch to dev.to, backtestingmax.com, repec.org and dspace.mit.edu was blocked by the session's network allowlist, and Firecrawl web search had run out of credits. These items are flagged in the evidence table.
- **[B-fix]** a correction of A.
- **[B-new]** new material from B.

**Tools and raw outputs.**
- A: `study/trade_tools/` (`tlib.py`, `series.py`, `t1_order.py`, `t2_ev.py`, `t34.py`, `analyze.py`; outputs `out_5min.txt`, `out_1h.txt`).
- B: `study/trade_b_tools/` (`b1_baseline.py`, `b2_manage.py`, `b2_analyze.py`, `b3_theory.py`, `b3b_bayes.py`; outputs `out_b1.txt`, `out_b2.txt`, `out_b3.txt`).
- Section 7 gives the commands to reproduce everything.

---

## 0. Executive summary

1. **The HUD's EV is a geometric artefact.** [A✓]
   - It is shown at 2245 (HUD) and 2359 (panel) as `EV = invWin·RR − (1 − invWin)`, with `invWin` = P(target first | decided within H).
   - Under any martingale every stop/target/time-stop bracket has E[R] = 0 (optional stopping).
   - Because the formula drops the undecided branch, it shows about 0 for near targets and **−0.34R to −0.97R** for far targets in a fair market (A, T2).
   - On 163,249 real records it has **corr +0.02** with realized R. For R:R > 4 it shows −0.39R where the realized value was +0.03R / +0.06R (A, T4-B).

2. **[B-fix] A's TM-1 fix would have re-introduced a smaller version of the same bias.**
   - A proposed storing the breakeven win rate BE = r/(r+d) as the ledger's race baseline and shifting it by `f_raceAdj`.
   - The ledger only counts races decided within H, and conditioning on "decided within H" favours the nearer barrier (`quant_pot.final.md` 1.3).
   - On A's own records (B1):
     - decided races beat BE by **−2.1 pp (5-min) / −1.9 pp (1h)**, a learned logit shift of −0.089 / −0.078;
     - the HUD would then show **−0.05R to −0.07R for R:R > 1** where realized R was −0.02 to +0.06R.
   - Against the driftless *conditional* baseline (QPOT-02), the residual is −0.6 pp, which is the strict trade-through rule for targets.
   - Corrected TM-1:
     - drift-free conditional race as the baseline;
     - BE shown beside it;
     - EV replaced by the ledger's model-free average realized R with its standard error (SKEP-4).

3. **Brackets do not create expectancy on these markets, and B measured the management rules directly.** [B-new]
   - Design: 61,804 paired records (6 CME futures, 5-min, real 1-minute path) and 109,999 (CME + BTC 1h). Market entry toward the nearest pool, engine stop, H = 30.
   - On 5-min with the real path, every management rule changed mean R by less than 0.01R:
     - break-even after +1R: −0.008 (SE 0.003);
     - break-even at half-way: −0.003 (0.003);
     - 50% partial at half-way with a break-even runner: −0.004 (0.004);
     - 1R trailing stop: +0.001 (0.005).
   - Each rule cut the standard deviation of R by 8-26%.
   - Fixed-ATR "shadow stops" from 0.5 to 3 ATR all gave mean R within ±0.01R (|z| < 1.5).
   - This agrees with:
     - Carr & López de Prado (2014): under a random walk there is no optimal profit-take/stop mesh, and optimising one is backtest overfitting;
     - Kaminski & Lo (2014);
     - Glynn & Iglehart (1995): trailing stops do not help under a diffusion.

4. **[B-new] Trailing stops cannot be graded on OHLC bars.**
   - On the same 5-min records, the 1R trailing stop gains +0.001R with the real 1-minute path.
   - With the engine's assumed bar path (O-L-H-C / O-H-L-C) it gains **+0.016R (3.2 SE)**; on 1h it gains +0.035R.
   - Barrier rules (fixed stop, fixed target, TP1 at a level, break-even armed from the next bar) move by at most 0.005R between the two paths.
   - The Pine ledger may grade barrier rules only, never trailing rules.

5. **[B-new] After the opposing pool is taken first, the target is still reached about 1 time in 5, exactly as geometry predicts.**
   - Rest of the window: 22.8% vs 20.8% predicted (5-min); 21.2% vs 21.5% (1h).
   - A fresh H window: 27.8% vs 25.6%; 26.7% vs 26.7%.
   - So the status after a stop-out is "STOPPED, target PoT now x%", not "draw failed". The event carries no information beyond the new distance (A's TM-2 wording corrected).

6. **A stop just beyond the opposing pool is a race barrier, not a protective stop.** [A✓]
   - Once a swing pool is traded through, a stop 0.3 ATR beyond it is hit on the sweep bar itself 64% (5-min) / 70% (1h) of the time; within 12 bars 92%, within 30 bars 95%.
   - Random grid levels: 57-62% / 90% / 93%.
   - Rejected-sweep wicks are exceeded later 76-82% of the time (random 78-81%).
   - **[B-fix]** The engine's invalidation is not always a pool. It can be an opposing FVG/OB far edge, the execution swing, or a 1.5 ATR fallback (5-7% of cases). Label it by source (TM-7).

7. **Costs are first-order on intraday charts.** [B-new]
   - With $4.50 per round turn plus 1 tick of slippage (inside the 2026 ES all-in range of $2.80-$5.76; one public Silver Bullet test used $4.50 + 2 ticks), the engine's 5-min stop costs a median **0.027R** per trade (p90 0.11R).
   - Per symbol: ES/CL/RTY/YM 0.037-0.043R; NQ/GC 0.010-0.013R.
   - At a 0.5 ATR stop the cost is **0.087R**; on 1h it is 0.009R.
   - Mean realized R goes from −0.002 gross to −0.050 net.
   - Cost-adjusted breakeven is BE_net = (1 + c)/(1 + RR), with c = cost/risk (TM-8).

8. **The engine's intrabar race rule is optimal, and the reason is plain geometry.** [A✓ + B-new]
   - A measured 88.1-88.7% correct high/low ordering on real bars, against 80.6-80.7% for TradingView's broker-emulator rule.
   - B: a driftless Brownian bar gives exactly **0.887 vs 0.806**.
   - The engine rule is the shortest-path rule: the O-L-H-C path is shorter than O-H-L-C iff close > open, since the difference is 2(O − C).
   - A Bayes rule that uses where O and C sit in the range does no better (0.884).
   - Keep `f_step`'s rule; lower-timeframe resolution is not worth a request.

9. **Mechanical ICT entry models show no edge over geometry.** [A✓ numbers from A's tests; public tests partly A]
   - Sweep → MSS → FVG limit entry: 853 setups (5-min) and 1,124 (1h). Win rate within ±3 pp of the finite-horizon race and of a random-entry null. Mean R −0.06 to +0.05.
   - Public tests: the Silver Bullet [GBB] study found the Silver Bullet hours not special and every variant unprofitable after costs, with the stop beyond the sweep extreme the best variant.
   - The 25,000-variant study kept only 1.7% of configurations, which is about what multiple testing alone would leave.
   - So: no score bonus for setup alignment.

10. **Limit entries in a draw-aligned zone follow geometry.** [A✓ + B-new interpretation]
    - P(fill before target) = d/(d+e) predicted 0.735 vs 0.696 observed (5-min) and 0.774 vs 0.752 (1h). 20-26% of setups ran to the target unfilled.
    - Win given a fill, with the stop beyond the zone: 0.195 vs model 0.181 (5-min); 0.170 vs 0.189 (1h).
    - No measurable adverse selection beyond geometry. Handa & Schwartz (1996) and Linnainmaa (2010) name the two risks (non-execution, adverse execution) that the TM-4 ledger should measure per chart.

11. **Obstacles.** [B-fix]
    - Inner same-side pools carry no information beyond distance: residual −0.018 vs −0.019 (5-min), −0.025 vs −0.024 (1h).
    - Untouched *opposing FVGs* are not neutral. A's own residuals were −1.7 pp (5-min, 1.4 SE) and −0.5 pp (1h), the same sign as `ict_liq.final.md` B5: −2 to −3 pp of reach per FVG, negative in 11 of 12 datasets.
    - TM-3 shows obstacles as TP1 candidates and leaves the small ledger-guarded penalty to ICT-5. A's "obstacles add no information" was too strong.

12. **The R:R / WIN / EV readout describes a trade nobody took.** [A✓]
    - The HUD re-runs `f_invalidation` from the live close every tick (2127). The ledger grades a bracket frozen at activation (1426-1431).
    - **[B-fix]** A's TM-2 also showed statuses that can never appear: a trial is booked and replaced on the same bar it hits or expires.
    - It also fails when the ledger is off (the 2038 gate). TM-2 is re-specified around the states that can actually be seen.

13. **Pre-commitment is better supported than A said.** [B-new]
    - Fischbacher, Hoffmann & Schudy (2017, RFS): the option to pre-commit to automatic stop-loss/take-gain orders causally reduces the disposition effect. A reminder alone does not.
    - Richards et al. (2017, EJF): UK investors' stop-loss use inoculates against it.
    - This supports a visible frozen plan (TM-2): evidence moderate for the mechanism, weak for the chart-UX benefit.

### 0.1 What B changed relative to A

| # | Item | Change |
|---|---|---|
| 1 | TM-1 race baseline | **Corrected.** BE is the wrong null for races decided within H (−2 pp bias, B1). Baseline = driftless conditional (QPOT-02). EV = ledger realized R̄ ± SE (SKEP-4), gated on SE, not n |
| 2 | TM-2 states | **Corrected.** Only OPEN and STOPPED are visible on a live trial. TARGET FIRST and WINDOW ENDED happen on booking. A trial is always opened (`graded` flag) so the plan exists with the ledger off. Post-stop wording "STOPPED · target PoT x%" (B2) |
| 3 | Obstacles | **Corrected.** Opposing untouched FVGs cost −0.5 to −1.7 pp (A) / −2 to −3 pp (ICT-5); inner pools 0. TM-3 shows; ICT-5 penalises |
| 4 | Kaminski & Lo | **Precision.** Their negative "stopping premium" is relative to holding an asset with a positive premium (stop → bonds). For zero-drift races the applicable result is optional stopping (E[R] = 0). "+50-100 bp/month" is from Kaminski's 2006 thesis abstract (monthly 1950-2004) |
| 5 | Intrabar rule | **Upgraded.** Brownian optimum (0.887 vs 0.806), shortest-path identity, no better OHLC rule exists (B3) |
| 6 | Partials / BE / trailing / shadow stops | **New measurement** on 61.8k + 110k paired records with cluster SEs (B2). A's +0.107R partial effect (n = 226, 5-min) did not replicate at scale |
| 7 | Trailing-stop grading | **New constraint.** OHLC path inflates trailing rules (+0.016R, 3.2 SE). The ledger grades barrier rules only |
| 8 | Costs and sizing | **New** (TM-8): cost in R, BE_net, position size via `syminfo.pointvalue` |
| 9 | Invalidation label | **Corrected.** Label by source (pool / array / swing / ATR), not always "OPP. POOL" (TM-7) |
| 10 | TM-4 | **Fixed.** `f_invalidation` usually selects the entry zone itself as the "opposing" level, since a draw-aligned array below price has side −1. Spec now derives the zone stop explicitly |
| 11 | Evidence grades | P3 (Silver Bullet public tests) stays moderate but is marked "A, not re-opened" except the GBB and 25,000-variant items, which B re-found. P8/P9 stay weak. TM-2 UX rationale: weak → moderate (mechanism) |
| 12 | Alerts | **Added** the platform throttle (more than 15 alerts in 3 minutes halts alerts; Pine FAQ). Events restricted to states that exist (TM-5) |
| 13 | ETA / duration | **New concept**: closed-form race durations (MC-checked). Not proposed, because QPOT-06 owns ETA |
| 14 | Doc citations | **Corrected.** The broker-emulator rule is at concepts/strategies.md:204 and the global-variable rule at language/user_defined_functions.md:29 in the current mirror |

---

## 1. Concepts (definitions and parameters)

### 1.1 R-multiple, expectancy, SQN, profit factor [A✓]
- R = side·(exit − entry)/|entry − stop|. Expectancy = mean R. SQN = √N·mean(R)/sd(R) (a t-statistic). PF = gross win R / gross loss R.
- The engine books a realized R per graded window, `rOut` (1457-1458):
  - +rr0 if the target came first;
  - −1, or worse on a gap through the stop at the open (1451-1452), if the stop came first;
  - mark-to-market at H if neither.
- Avg R and PF appear only in the Full view (2419-2426).
- **[B-new] Sample size.** sd(R) grows with R:R. Measured on 5-min: 0.73 (R:R ≤ 1), 1.11 (1-2), 1.52 (2-4), 2.40 (> 4).
  - A ±0.10R standard error needs about 50 / 120 / 230 / 580 *independent* trades per bucket, more with overlap.
  - So R̄ must be gated on its SE, not on "n ≥ 30".

### 1.2 Breakeven win rate and the martingale identity [A✓, B-fix on horizon]
- BE = 1/(1 + RR) (Brooks' "traders' equation": P·reward > (1 − P)·risk).
- For a driftless continuous martingale whose race is eventually decided, P(target at d before stop at r) = r/(r + d) = BE exactly.
- **[B-fix]** This holds for the infinite horizon. Among races decided within H, the nearer barrier is favoured (`quant_pot.final.md` 1.3).
  - On real data, decided races sat at BE − 2.1 pp (5-min) and BE − 1.9 pp (1h) overall.
  - By R:R bucket (5-min): 0.389 vs BE 0.412 (1-2), 0.229 vs 0.266 (2-4), 0.107 vs 0.144 (> 4).
  - The driftless conditional model is 0.400 / 0.232 / 0.103 (B1).
- Brooks' "directional probability" (reaching +X before −X) is the symmetric race. It is 50% under a martingale, and his "60% setups" are practitioner claims without published statistics.
- **DOL role:** "is this target worth trading?" is answered by WIN − BE (or realized R̄), not by PoT or R:R alone.

### 1.3 Two-barrier race with a horizon (triple-barrier labelling) [A✓]
- Upper barrier = target near edge, lower = invalidation, vertical = H bars (López de Prado, AFML ch. 3). The engine's ledger is exactly this (`f_step` 1434-1459).
- Unconditional pW = `f_raceH(d, r, σ, μ, H)` and pL; P(neither) = 1 − pW − pL.
- WIN≤H = pW/(pW + pL) (1364), the probability *conditional* on a decision within H.
- Brownian motion over-predicts P(decided within H): 0.84-0.87 predicted vs 0.80 observed (`quant_pot.final.md` 1.3). Do not display the unconditional pW without empirical calibration.
- **Meta-labelling** (López de Prado): a secondary model learns P(the bracket wins) from features. `f_raceAdj` (1367-1371) is the intercept-only version. Feature versions belong to `calib_ml.final.md`.

### 1.4 Optional stopping: brackets cannot create expectancy [A✓, B-fix on Kaminski & Lo]
- For a martingale price and a bounded stopping time τ (first touch of target or stop, capped at H): E[X_τ] = X₀.
- So any bracket has E[R] = 0 before costs: tight or wide stop, partials, break-even stops, trailing stops, time stops.
- **[B-fix]** Kaminski & Lo (2014, J. Fin. Markets 18:234-254) study stopping *out of a risky asset into bonds*.
  - Their "stopping premium" is negative under the random-walk hypothesis because the stop forgoes the risk premium.
  - It can be positive with momentum or regime switching.
  - For zero-drift futures races the operative result is optional stopping (0, not negative).
  - The "+50-100 bp per month during stop-out periods" figure comes from Kaminski's 2006 MIT thesis (monthly data 1950-2004), not from the 2014 paper.
- Lo & Remorov (2017, J. Fin. Markets 34:1-15): tight stops underperform buy-and-hold on US stocks *because of trading costs*. Outperformance needs sufficiently high serial correlation, and downside-risk reduction is "not substantial".
- **[B-new] Carr & López de Prado (2014, arXiv:1408.1159).** They simulate profit-take/stop-loss meshes under a discrete Ornstein-Uhlenbeck process:
  - With strong mean reversion (half-life 5), small profit-takes with wide stops are optimal (Sharpe about 3.2).
  - With a positive expected profit, profit-takes about 6σ with stops 4-10σ are optimal.
  - As the process approaches a random walk "there are no recognizable areas where performance can be maximized", and calibrating the mesh "would lead to backtest overfitting".
  - Lipton & López de Prado (2020, arXiv:2003.10502) give the closed form.
- **[B-new] Glynn & Iglehart (1995, Management Science 41(6):1096-1106).** Trailing stops under a positive-drift random walk / Brownian motion. Later work summarises the result as "never use the trailing stop" under those models (Leung & Zhang 2017, arXiv:1701.03960).
- **[B-new] Shiryaev, Xu & Zhou (2008, Quantitative Finance 8(8):765-776).** Optimal selling time is bang-bang: hold to the horizon if the stock is "good enough", sell at once otherwise (confirmed by Majumdar & Bouchaud, arXiv:0809.2878). There is no interior optimal time stop.
- **DOL role:** edge can only come from *selection* (which target) or *race information* (which side first). The ledger can measure both; exit mechanics manage variance and exposure.

### 1.5 Entry models that target a DOL (exact rules as coded in A's test) [A✓]
Long side; mirror for short. ICT does not fix these parameters.

**(a) Sweep → MSS → FVG ("2022 model" / Silver Bullet without the time window).**
1. Sweep: a confirmed unswept pivot(5, 5) low P is traded through, `low[s] < P`. Take the outermost P when several are swept. Require `close[s] > P` and `low[s] > P − 3·ATR`.
2. Sweep extreme SX = running min of low until the MSS.
3. MSS level M = the most recent confirmed fractal(1) high with pivot bar in [s − 20, s − 1] and above close[s].
4. MSS = the first bar m ∈ (s, s + 12] with `close[m] > M`; otherwise abandon.
5. FVG = the last bullish gap `low[j] > high[j−2]`, j ∈ [s + 2, m + 1]. Entry E = FVG top (CE variant = midpoint). Known at a = m + 1.
6. Target = the nearest live BSL (pivot 5) at least 0.25 ATR above close[a] and at most 10 ATR above E.
7. Limit at E valid for 20 bars. If the target trades first: "ran without fill".
8. Stops, each with a risk floor of 0.25 ATR:
   - sweep: SX − 0.1 ATR;
   - fvg: FVG bottom − 0.1 ATR;
   - engine: the nearest SSL below E − 0.3 ATR, else E − 1.5 ATR.
9. First touch on the real 1-minute path (5-min) or the engine path (1h); H = 30 after the fill.

**(b) iFVG continuation.**
- An FVG inverted by a body close beyond its far edge (engine `close < z.bottom`, 1603).
- Entry on the retest; stop beyond the iFVG or the sweep candle; target = internal liquidity, then the DOL.
- No published statistics. `ict_pd.final.md` found that broken gaps hold on retest as often as random zones.

**(c) Breaker retest / Unicorn.**
- A breaker is an OB whose leg swept liquidity and was then broken (1646-1661). Unicorn = breaker ∩ same-direction FVG.
- Entry in the overlap, stop beyond the breaker. No statistics.

**(d) OTE (62-79% retracement):** see `ict_struct.final.md`.

**(e) Market entry at activation.**
- This is the ledger's unit (`f_openTrial` 1426-1431): entry at the close of the committing bar.
- It is the right unit for grading a *forecast*. A limit trader faces a different R:R plus fill risk (1.12).

**(f) [B-new] Confirmation (stop) entry.**
- A buy-stop above the MSS swing M: it fills only if the structure shift completes.
- It pays the spread plus stop-order slippage (Osler 2005: stop orders execute into cascades).
- Same martingale bookkeeping. Not tested; it is the costliest entry in ticks, so TM-8's cost term matters most here.

**Failure modes.**
- Definitions are not standardised (sweep depth, MSS swing strength, FVG choice), so results depend on coding.
- Annotated examples are survivorship-selected.
- In rigorous tests win rates match R:R geometry (2.2).

### 1.6 Invalidation placement [A✓, B-fix on labels]

| Rule | Definition | Engine |
|---|---|---|
| Opposing level (race barrier) | Just beyond the nearest opposing pool-list level (liquidity zone bottom/top, *or the far edge of an opposing FVG/OB/breaker*), buffer 0.1 ATR, within maxATR. Fallbacks: exec-TF range extreme, then 1.5 ATR. Risk floor 0.25 ATR | `f_invalidation` 1343-1358 |
| Post-raid extreme | After a raid of the opposing pool that closed back inside: beyond the raid's extreme | missing (raid event at 1579-1582 not stored) |
| Entry-array far edge | Beyond the FVG/OB used for entry | implicit: when the nearest "opposing" level *is* the entry array (side −1 bullish array for a long), `f_invalidation` already returns its far edge |
| Protected swing | Beyond the strong extreme of the current leg | only as fallback; `exeProtL/H` returned at 925, unused (ICTS-5) |
| Volatility | k·ATR from entry | 1.5 ATR fallback |
| MAE percentile (Sweeney) | Stop at p75-p90 of winners' MAE | heat p80 shown (2404-2408), not used |

- Engine rule in practice (A, T4-B): median risk 1.53 ATR (5-min) and 1.69 ATR (1h); fallback 6.6% / 5.4%; floor 0.3% / 0.6%; median R:R 1.68 / 1.50.
- B2 reproduced this: 1.63 ATR / 1.77 ATR, R:R 1.63 / 1.45.
- **[B-fix]** For a buy-side target every level below price has `side == −1`, including *bullish* FVG/OB/breakers. So the "opposing" barrier is often a draw-aligned array (the ICT entry zone), and the label "OPP. POOL" would be wrong. Label by source (TM-7).

### 1.7 Sweep penetration depth and stop buffers [A✓]
- Depth = the excursion beyond the level within N bars of the first trade-through, in ATR. Rejected = the sweep bar closes back inside; accepted = it closes beyond.
- Pools vs random levels:
  - medians 0.43 / 0.60 ATR on the sweep bar and 2.84 / 2.87 ATR within 30 bars (5-min / 1h);
  - pools close back inside *less* often than random levels: 44.9% vs 52.7%, 46.7% vs 54.8%. This is consistent with Osler (2005) stop cascades: an extra +0.27 to +2.35 hundredths of a percent over 15 min-2 h after crossing FX round numbers.
- **DOL role:** no affordable buffer survives a sweep. The stop means "exit when the opposing pool is taken", which is the race's definition of failure.

### 1.8 Partials, break-even and trailing stops [A, B-new measurements]
- TP1 = the first same-side pool or opposing array between entry and target. Typical rule: 50% off, stop to entry, runner to the DOL.
- Under a martingale none of these change expectancy (1.4); they cut dispersion.
- **B2 measurements** (paired, same records, cluster-robust SE in 2H-bar blocks):

| Rule (vs base bracket, mark-to-market at H) | 5-min real path: ΔR̄ (SE) / sd | 1h engine path: ΔR̄ (SE) / sd | 5-min engine path: ΔR̄ (SE) |
|---|---|---|---|
| Base (engine stop, nearest pool) | R̄ −0.002 (0.006) / 1.42 | R̄ +0.001 (0.006) / 1.38 | — |
| Break-even after +1R | **−0.008 (0.003)** / 1.21 | +0.004 (0.003) / 1.22 | −0.003 (0.003) |
| Break-even at half-way | −0.003 (0.003) / 1.31 | +0.003 (0.003) / 1.27 | +0.002 (0.003) |
| 50% at half-way + BE runner | −0.004 (0.004) / 1.14 | +0.004 (0.003) / 1.10 | −0.001 (0.004) |
| Trail 1R behind the peak after +1R | +0.001 (0.005) / 1.05 | **+0.035 (0.004)** | **+0.016 (0.005)** |

- Reading:
  - On the real path every rule is within ±0.01R; the break-even stop costs a little (−0.008R) because the break-even stop is a touch while the target needs a trade-through.
  - The trailing stop's gains appear **only** with the assumed OHLC path (+0.016R on the same 5-min data, 3.2 SE), so they are path artefacts.
  - A's model-A partial result (+0.107R, SE 0.040, n = 226 on 5-min; +0.010R on 1h) did not replicate at scale.
- Practitioner sources: partial profit-taking reduced return in every tested trend-following variant (Enlightened Stock Trading [A]). Break-even stops: no rigorous public test; forum and vendor claims point both ways (ATAS, NexusFi, Tradeify; weak).

### 1.9 Next obstacles (path map) [A, B-fix]
- Levels between price and the target that price must cross first:
  - same-side inner pools;
  - opposite-polarity arrays (for a buy-side target: bearish FVG/OB/breakers above price, all `side == +1` and nearer than the target);
  - high-volume nodes (`f_pathVol` 1417-1424, used at 1945-1947).
- **Evidence:**
  - inner pools: no effect beyond distance (−0.018 vs −0.019 at 5-min; −0.025 vs −0.024 at 1h);
  - **untouched opposing FVGs: small negative effect.** A's race residuals −0.025 vs −0.008 (5-min, 1.4 SE) and −0.026 vs −0.021 (1h); `ict_liq.final.md` B5: −2.8 ± 0.8 / −2.1 ± 1.0 pp of reach per FVG, negative in 11 of 12 datasets, robust within trend strata.
- **DOL role:** natural TP1 candidates (display), plus a small ledger-guarded path cost for opposing FVGs (ICT-5, not here).

### 1.10 MAE / MFE [A✓, B-new on stop optimisation]
- MAE = maximum adverse excursion before exit; MFE = maximum favourable excursion. Sweeney (1996/97) plots them against outcome. Practitioner rules put the stop at p90-p95 of winners' MAE (MQL5, NexusFi).
- A, engine stop: winners' MAE p50/p80/p90 = 0.27/0.60/0.76R (5-min), 0.26/0.58/0.75R (1h). Losers' MFE median 19-20% of the way to the target.
- **[B-new]** Conditioning on winners is circular (winners are by definition the trades the stop did not take). The unconditional test is the shadow-stop curve (1.17), which is flat on these markets.
- SKEP-1: the engine's hits-only "heat" understates the all-record p80 by about 2×.

### 1.11 Time stops, horizon, ETA and race duration [A, B-new formulas]
- Time stop = the vertical barrier. A: exiting open trades at 5/10/20 bars instead of 30 changed R̄ by −0.012 to +0.004 (SE 0.02-0.03). Theory: no interior optimal sell time under GBM (1.4).
- **ETA:** the engine shows the median bars-to-hit of past hits within ±0.5 ATR of the current distance, n ≥ 5 (2116-2126).
  - `quant_pot.final.md`: constant-σ ETA rank-correlates −0.09 with realized time, vol-time +0.11 to +0.22 (QPOT-05/06 own this).
  - SKEP-1: hits-only ETA is 2-3× optimistic.
- **[B-new] Closed-form race durations** (driftless, infinite horizon, σ per bar). Checked by Monte Carlo up to the known discrete-monitoring barrier shift (+0.5826σ√Δt):
  - E[τ] = d·r/σ²;
  - E[τ | target first] = d(d + 2r)/(3σ²);
  - E[τ | stop first] = r(r + 2d)/(3σ²).
- Observed (B2): races resolve fast. The median decided race took 4.8 bars (5-min) and 5.3 bars (1h); 62% / 58% were resolved within 10 bars.
- The live PoT is a rolling H-bar window from now. It never reflects time already used by the plan (TM-2 adds "time left").

### 1.12 Limit-entry fill probability and the two limit-order risks [A✓, B-new framing]
- Entry e behind price, target d ahead (driftless):
  - P(fill before target) = d/(d + e);
  - given a fill with stop r from the reference price, P(target before stop) = (r − e)/(r + d) = 1/(1 + RR_zone), with RR_zone = (d + e)/(r − e).
  - So E[R] = 0 for limit plans too.
- Handa & Schwartz (1996, J. Finance 51(5):1835-1861): limit orders carry two risks, non-execution and adverse execution. Linnainmaa (2010, J. Finance 65(4):1473-1506): limit orders are price-contingent and adversely selected, which changes measured investor performance.
- Measured (A, T4-A):
  - fill 0.696 vs 0.735 (5-min), 0.752 vs 0.774 (1h); 4.0-4.7% expired unfilled after 20 bars;
  - win|fill with the zone stop 0.195 vs 0.181 model (5-min), 0.170 vs 0.189 (1h).
  - Non-execution matches geometry within 2-4 pp. No adverse execution is measurable at these sample sizes.

### 1.13 Intrabar ambiguity [A✓, B-new theory]
- When both barriers are inside one bar, a path assumption decides the order:
  - engine (1440-1441): bull bar O-L-H-C, bear bar O-H-L-C, gaps settled at the open;
  - TradingView's broker emulator: open nearer the high → O-H-L-C (concepts/strategies.md:204).
- **Shortest-path identity [B-new]:** len(O-L-H-C) − len(O-H-L-C) = 2(O − C). The engine rule always assumes the path with less travel.
- **Brownian benchmark [B-new]** (40,000 driftless bars, 500 steps each):
  - engine rule 0.887 correct (bull 0.885, bear 0.890);
  - TV rule 0.806;
  - a 10 × 10 binned Bayes rule on the open's and close's position in the range: 0.884.
- Real bars (A): 0.881-0.887 and 0.806-0.807. The engine rule is the geometric optimum; nothing in OHLC improves it.

### 1.14 What a trader needs on the chart at decision time [A, B-updated]

| Item | Why | Engine today | Proposal |
|---|---|---|---|
| Target, PoT within H | objective, how likely | zone + `Target:` label (2214-2226) | — (COMP-4 / UX-3 own wording) |
| Which side first vs the opposing level | the literal "which liquidity next" | Terminal HUD WIN≤H only with `showInv` | TM-1, ICTS-3 |
| Invalidation and what it means | sizing, exits | `showInv` default off (172), live-recomputed | TM-2, TM-7 |
| R:R, BE, BE net of costs | trade quality | R:R Terminal only; BE missing | TM-1, TM-8 |
| Expectancy with uncertainty | should I trade it | shown but wrong (2245, 2359) | TM-1 (ledger R̄ ± SE) |
| Entry zone + fill probability | how to get in | missing | TM-4 |
| Obstacles / TP1 | where price may stall; partials | missing | TM-3 |
| Time: ETA, time left | patience, exit | ETA\|hit, killzone (Terminal); time left missing | TM-2, QPOT-06 |
| Plan status | management | missing | TM-2, TM-5 |
| Position size | execution | missing | TM-8 |
| Track record | trust | Terminal accuracy panel | TM-1, TM-6, SKEP-4 |

Uncertainty displays improve decisions (Fernandes et al. 2018 CHI: about 97% of optimal payoff, +5 pp over no-uncertainty; `ux_design.md`). That argues for "R̄ ±SE" and quantile ETAs over bare point numbers.

### 1.15 Actionable alerts [A, B-new constraints]
- An alert is actionable when the payload lets the trader act without the chart: event, side, target, entry/zone, stop, TP1, R:R, BE, probability plus sample size, bars left.
- Events that map to decisions:
  - new plan;
  - entry zone tapped;
  - TP1 reached;
  - stopped (opposing level first);
  - target reached;
  - plan window rolled.
- Platform facts (Pine docs):
  - `alert()` takes a series string (concepts/alerts.md:63);
  - `alertcondition()` needs a const string but can embed `{{plot("title")}}`, also for `display.none` plots (concepts/alerts.md:262-266; visuals/plots.md:151-159);
  - **more than 15 alerts in 3 minutes halts the script's alerts** (faq/alerts.md:201).
- So plan events must use `freq_once_per_bar_close` with per-trial once-flags (COMP-2 frame).

### 1.16 Behaviour: disposition effect and pre-commitment [A✓ + B-new]
- Odean (1998, J. Finance; 10,000 accounts 1987-93): PGR 0.148 vs PLR 0.098.
- **[B-new]** Fischbacher, Hoffmann & Schudy (2017, RFS 30(6):2110-2129), lab: automatic stop-loss/take-gain orders significantly reduce the disposition effect, mainly by increasing realised losses. Mere reminders do not.
- **[B-new]** Richards, Rutterford, Kodwani & Fenton-O'Creevy (2017, EJF 23(2):130-152), UK brokerage 2006-09: stop-loss use inoculates against the disposition effect.
- A frozen plan visible on the chart (TM-2) is the display analogue. Evidence for the mechanism is moderate; for the chart's effect it is weak (untested).

### 1.17 Stop-distance expectancy curve ("shadow stops") [A, B-new preview]
- For each stop s (ATR at entry): outcome = −1 if MAE ≥ s before the target; d0/s if the target was hit first; MTM/s otherwise.
- Sufficient statistics per trial: MAE until hit or H, d0, MTM at H. This is exact up to the intrabar rule, since MAE is monotone.
- **B2 preview** (same nearest-pool targets):

| s (ATR) | 0.5 | 1.0 | 1.5 | 2.0 | 3.0 |
|---|---|---|---|---|---|
| 5-min R̄ (SE) | +0.009 (0.010) | −0.002 (0.007) | −0.004 (0.005) | −0.003 (0.004) | −0.005 (0.003) |
| 1h R̄ (SE) | +0.004 (0.009) | −0.005 (0.006) | −0.005 (0.005) | −0.009 (0.004) | −0.011 (0.003) |
| P(stopped) | 0.80 | 0.67 | 0.56 | 0.47 | 0.33 |

- Flat to within ±0.01R; the 1h drift at 3 ATR is the trade-through asymmetry plus trend beta.
- After 1-tick + $4.50 costs, 0.5 ATR stops lose −0.12R at 5-min.
- Per Carr & López de Prado, a per-chart curve must be read with its SE and a multiple-comparison guard, never optimised.

### 1.18 Costs, cost-adjusted breakeven, position size [B-new]
- With c = round-trip cost / risk (in R):
  - a win pays RR − c, a loss −1 − c;
  - **BE_net = (1 + c)/(1 + RR)**;
  - E[R]_net = E[R]_gross − c.
- Measured cost for the engine stop with $4.50 RT + 1 tick slippage:
  - 5-min median 0.027R, p90 0.109R, mean 0.048R;
  - by symbol: CL 0.041, ES 0.042, RTY 0.043, YM 0.037, NQ 0.013, GC 0.010;
  - with 2 ticks: median 0.044R;
  - 1h median 0.009R.
- At R:R 1.6 and c = 0.04, BE rises from 38.5% to 40.0%.
- 2026 ES all-in round turn: $2.80 (exchange + NFA only) to $5.76 (Tradeify / Tradovate all-in); NexusFi fee table. The GBB public test assumed $4.50 + 2 ticks.
- **Position size** = cash at risk / (risk in price × point value). Pine: `syminfo.pointvalue` (simple float; e.g. 50 for ES, 100 for GC) and `syminfo.mintick`.

### 1.19 Kelly sizing [A✓]
- f* = p − (1 − p)/RR. With p from geometry, p = BE and f* = 0.
- A ledger p would need confidence intervals and invites over-sizing. Not recommended.

### 1.20 ICT projections as targets [B-new, for completeness]
- "Standard-deviation projections" extend a manipulation leg by −2 to −2.5 of its range as exhaustion or partial targets (LuxAlgo, community study notes). No statistics exist and "standard deviation" here is a measured-move multiple, not a statistic.
- Not proposed: the engine's targets are liquidity, and COMP-12 already offers a same-side ladder.

---

## 2. Evidence

### 2.1 Published evidence

| # | Claim | Source and data | Numbers | Grade | Verification |
|---|---|---|---|---|---|
| P1 | Brackets have E[R] = 0 under a martingale | Optional stopping theorem | exact | strong | theorem |
| P1b | Stop-loss into bonds lowers return under the RWH; can help with momentum or regime switching | Kaminski & Lo 2014, J. Fin. Markets 18:234-254; Kaminski 2006 MIT thesis | thesis: +50-100 bp/month during stop-out periods (monthly 1950-2004) | strong (theory), moderate (empirics) | B via abstracts [B-fix: context] |
| P2 | Tight stops lose to buy-and-hold after costs unless serial correlation is high | Lo & Remorov 2017, J. Fin. Markets 34:1-15 | closed form plus US stocks; downside risk cut "not substantially" | strong | B via abstract |
| P2b | No optimal PT/SL mesh under a random walk; mesh optimisation = overfitting; optimal meshes exist under O-U | Carr & López de Prado 2014, arXiv:1408.1159 | Sharpe about 3.2 at half-life 5 (small PT, wide SL); about 12 with positive expected profit; no pattern as half-life → ∞ | moderate (simulation) | B read full text [B-new] |
| P2c | Trailing stops do not help under positive-drift RW/BM | Glynn & Iglehart 1995, Mgmt Sci 41(6):1096-1106 | optimal = never trail (as summarised by Leung & Zhang 2017) | strong (theory) | B via abstracts [B-new] |
| P2d | No interior optimal sell time under GBM | Shiryaev, Xu & Zhou 2008, Quant. Finance 8(8):765-776; Majumdar & Bouchaud arXiv:0809.2878 | bang-bang: hold to T or sell at 0 | strong (theory) | B via abstracts [B-new] |
| P3 | ICT Silver Bullet / 2022 model mechanical tests lose | Silver Bullet [GBB] (1-min ES/NQ/YM/GC 2011-2026, 2 ticks + $4.50 RT, results in R); 25,000-variant study (16 y NQ/ES, video summary); dev.to 79 setups; backtestingmax 10 tests | GBB: SB hours "no better" than equally active hours; sweep-extreme stop best in held-out years "did not make the model profitable". 25k: 1.7% of configurations survived the testing stack. [A] PF 0.66-0.94; SB win 26.5% ES / 27.9% NQ vs BE 33.3% at 2R; 0/10 profitable | moderate (independent, consistent, not peer-reviewed) | GBB and 25k re-found by B; dev.to/backtestingmax numbers [A, not re-opened] |
| P4 | ICT FVG retest component has no edge | Backtrex (GBP/USD NY AM FVG); AI-run ICT bot (1 year) | win 33.89%, PF 0.80; bot win 29.6%, PF 0.81 | weak-moderate | bot numbers re-found by B; Backtrex [A] |
| P5 | FVGs behave like size-matched placebo zones | placebo-control script; `ict_pd.final.md` | no advantage in 14 measurements | moderate | sibling |
| P6 | Stop clusters cascade after crossing | Osler 2003 (J. Finance 58(5)), 2005 (JIMF 24(2)) | +0.27 to +2.35 hundredths of a percent, 15 min-2 h; gone at 1-2 days | strong (FX) | consistent with `academic_sr.final.md` |
| P7 | Published S/R interrupts trends slightly more than arbitrary levels | Osler 2000, FRBNY EPR 6(2) | 60.8% vs 56.2% | strong | sibling [A] |
| P8 | Partial profit-taking lowers return in trend following | Enlightened Stock Trading (RealTest) | "every instance … reduced the overall rate of return" | weak | [A] |
| P8b | Break-even stops | ATAS (citing Quantified Strategies), NexusFi, Tradeify, Substack | no rigorous test; claims point both ways | weak/none | B [B-new] |
| P9 | MAE-based stops | Sweeney 1996/97; MQL5, NexusFi | p90-p95 of winners' MAE; no controlled study | weak | B |
| P10 | Time exits rarely beat holding | FlashAlpha, 481k short-option trades | none beat hold-to-expiry | weak (other asset class) | [A] |
| P11 | Disposition effect | Odean 1998, J. Finance | PGR 0.148 vs PLR 0.098 | strong | well known |
| P11b | Pre-commitment (automatic stops) causally reduces it | Fischbacher, Hoffmann & Schudy 2017, RFS; Richards et al. 2017, EJF | significant reduction via more realised losses; reminders do not work | strong (lab causal) / moderate (field) | B via abstracts [B-new] |
| P12 | Limit orders: non-execution and adverse-execution risk; adverse selection | Handa & Schwartz 1996, J. Finance; Linnainmaa 2010, J. Finance | qualitative plus DJIA 1988 / Finnish investors | strong (concept) | B via abstracts [B-new] |
| P13 | Triple barrier, meta-labelling | López de Prado 2018, AFML ch. 3 | definitions | n/a | — |
| P14 | Broker-emulator intrabar rule; alert throttle; `{{plot()}}`; `syminfo.pointvalue` | Pine v6 docs (local mirror) | open nearer the high → O-H-L-C; more than 15 alerts / 3 min halts | n/a (platform facts) | B read docs |
| P15 | Showing uncertainty improves decisions | Fernandes et al. 2018 CHI | about 97% of optimal payoff, +5 pp | strong (sibling `ux_design.md`) | sibling |
| P16 | ES round-turn costs 2026 | NexusFi fee table, Tradeify, Top One/Tradovate, Topstep | $2.80 (fees only) to $5.76 all-in | moderate (fee schedules) | B [B-new] |

### 2.2 A's tests (kept; numbers re-checked against `out_5min.txt` / `out_1h.txt`) [A✓]

**Data.**
- 6 CME futures (ES, NQ, RTY, YM, GC, CL), 1-minute bars 2026-01-20 to 2026-04-15, resampled to 5-min with races on the real 1-minute path.
- The same contracts at 1h from 2025-03-21 (CL from 2025-06-01) to 2026-04-15, plus BTC/USD 1h 2016-2025.
- On 1h, a pseudo-path of 3 sub-bars per bar follows the engine rule.
- ATR = Wilder 14, pools = pivot(5, 5), strict sweep, H = 30, σ = stdev of Δclose over 50 bars, μ = 0.5·mean of Δclose (as at 915-917).
- No costs (B adds them).

**T1 · intrabar order (vs 1-minute truth).**

| Bars | Engine correct | TV correct | Two-long-wick bars (engine / TV) |
|---|---|---|---|
| 5-min (n = 93,428) | 0.881 | 0.806 | 0.696 / 0.644 |
| 15-min (n = 32,377) | 0.882 | 0.807 | 0.714 / 0.668 |
| 60-min (n = 8,211) | 0.887 | 0.807 | 0.727 / 0.666 |

**T2 · the EV readout in a fair market** (σ = 1/bar, H = 30, μ = 0; distances in σ√H).

| d | r | RR | pW | pL | neither | WIN≤H | BE | EV shown | true E[R] |
|---|---|---|---|---|---|---|---|---|---|
| 0.5 | 0.5 | 1 | 0.495 | 0.495 | 0.009 | 0.500 | 0.500 | +0.000 | 0 |
| 1.0 | 0.5 | 2 | 0.272 | 0.605 | 0.123 | 0.310 | 0.333 | −0.070 | 0 |
| 1.5 | 0.5 | 3 | 0.121 | 0.617 | 0.262 | 0.164 | 0.250 | −0.343 | 0 |
| 2.0 | 0.5 | 4 | 0.043 | 0.617 | 0.340 | 0.065 | 0.200 | −0.676 | 0 |
| 3.0 | 1.0 | 3 | 0.003 | 0.317 | 0.680 | 0.008 | 0.250 | −0.966 | 0 |

Drift noise: μ = ±1 standard error of a 50-bar mean shifts WIN≤H at d = r to 0.40/0.60 and EV by ∓0.19R. The truth is 0.50 / 0R.

**T3 · sweep depth** (events: first trade-through of an unswept pivot pool; control: first cross of a random-phase grid level after at least 10 bars on one side).

| | 5-min pools | 5-min grid | 1h pools | 1h grid |
|---|---|---|---|---|
| n | 10,219 | 10,075 | 12,879 | 17,435 |
| Close back inside on the sweep bar | 0.449 | 0.527 | 0.467 | 0.548 |
| Depth on sweep bar: median / P ≥ 0.3 ATR | 0.43 / 0.64 | 0.37 / 0.57 | 0.60 / 0.70 | 0.45 / 0.62 |
| Within 12 bars: P ≥ 0.3 ATR | 0.92 | 0.90 | 0.92 | 0.90 |
| Within 30 bars: median / P ≥ 0.3 ATR | 2.84 / 0.95 | 2.56 / 0.93 | 2.87 / 0.95 | 2.62 / 0.93 |
| Rejected sweeps: sweep-bar extreme exceeded within 30 bars | 0.82 | 0.81 | 0.76 | 0.78 |

**T4-B · engine readout on real data** (market entry toward the nearest pool, engine stop; n = 57,728 at 5-min and 105,521 at 1h).
- Win / loss / neither: 0.323 / 0.533 / 0.145 (5-min); 0.340 / 0.510 / 0.150 (1h). R̄ −0.008 (SE 0.019) and −0.001 (0.017).
- WIN≤H log-loss, drift vs driftless: 0.5816 vs **0.5680** (5-min); 0.5928 vs **0.5769** (1h).
- Top calibration bin: 0.792 shown vs 0.737 driftless vs 0.738 observed.
- corr(EV shown, realized R) = +0.019 / +0.016.
- EV shown vs realized R by R:R bucket (5-min | 1h): > 4: −0.393 / −0.381 shown vs +0.033 / +0.057 realized; 2-4: −0.232 / −0.231 vs −0.015 / −0.005.
- Obstacles: residual (observed − driftless pW): inner pool −0.018 vs −0.019 (5-min), −0.025 vs −0.024 (1h); opposing untouched FVG −0.025 vs −0.008 (5-min), −0.026 vs −0.021 (1h).
- Heat: winners' MAE p50/p80/p90 0.27/0.60/0.76R (5-min), 0.26/0.58/0.75R (1h).
- Time stops at 5/10/20 bars: ΔR̄ −0.002/+0.003/+0.003 (5-min), −0.012/−0.000/+0.004 (1h).

**T4-A · sweep → MSS → FVG limit entry (rules 1.5a).**

| | 5-min | 1h |
|---|---|---|
| Setups / filled / ran unfilled / expired | 853 / 594 / 225 / 34 | 1,124 / 845 / 226 / 53 |
| Fill: observed vs d/(d+e) | 0.696 vs 0.735 | 0.752 vs 0.774 |
| Sweep stop: risk / R:R / win / finite-H model / R̄ (SE) | 2.46 ATR / 1.12 / 0.394 / 0.381 / −0.004 (0.042) | 2.49 / 1.13 / 0.351 / 0.378 / −0.024 (0.036) |
| FVG stop: risk / R:R / win / model / R̄ (SE) | 0.53 / 4.80 / 0.195 / 0.181 / +0.047 (0.099) | 0.54 / 5.22 / 0.170 / 0.189 / −0.056 (0.079) |
| Engine stop: risk / R:R / win / model / R̄ (SE) | 2.88 / 1.00 / 0.406 / 0.394 / −0.012 (0.040) | 3.14 / 0.91 / 0.375 / 0.396 / −0.030 (0.032) |
| Random-entry null (same geometry as the sweep stop) | 0.375 | 0.370 |
| Partials at the first inner pool (n / R̄ full → partial / sd) | 226 / −0.120 → −0.013 / 1.12 → 0.94 | 269 / −0.154 → −0.144 / 1.01 → 0.84 |

### 2.3 B's tests [B-new]

**B1 · Which null should the ledger's race shift learn against?** (`b1_baseline.py`, on A's model-B records; decided races only, as the ledger counts them)

| Baseline stored as `pRace` | 5-min: mean / observed / wins − Σp per race / logit shift | 1h: same |
|---|---|---|
| BE = r/(r + d) (A's TM-1) | 0.398 / 0.377 / **−0.021** / −0.089 | 0.419 / 0.400 / **−0.019** / −0.078 |
| Driftless conditional pW/(pW+pL) (QPOT-02) | 0.383 / 0.377 / −0.006 / −0.025 | 0.407 / 0.400 / −0.006 / −0.026 |
| Engine drift conditional (today) | 0.381 / 0.377 / −0.004 / −0.015 | 0.406 / 0.400 / −0.006 / −0.023 |

Resulting HUD EV (shift applied to BE, EV = (WIN − BE)(1 + RR)) vs realized R:

| R:R | 5-min: A's TM-1 / corrected / realized | 1h: A's TM-1 / corrected / realized |
|---|---|---|
| 1-2 | −0.052 / −0.015 / −0.023 | −0.045 / −0.015 / −0.001 |
| 2-4 | −0.064 / −0.018 / −0.015 | −0.056 / −0.019 / −0.005 |
| > 4 | −0.074 / −0.021 / +0.033 | −0.065 / −0.022 / +0.057 |

- An intercept-only shift cannot correlate with realized R: corr = −0.006 / −0.018 for both versions.
- So the EV cell should show the ledger's *measured* R̄ ± SE (model-free; SKEP-4) rather than any model-shifted number.
- The drift conditional has a mean residual similar to the driftless one but worse log-loss (A, T4-B). Mean calibration is not the issue; sharpness at the extremes is.

**B2 · Management rules, post-stop outcomes, shadow stops and costs** (`b2_manage.py`, `b2_analyze.py`)
- Design: as A's model B (sample every 3rd 5-min / 2nd 1h bar, both sides). Target = nearest unswept pivot(5) pool 0.5-10 ATR away. Engine-style stop. Market entry at the close. Real 1-minute path (5-min) or engine path (1h). H = 30, then 2H to follow the target after a stop-out.
- Cluster-robust SE in 60-bar blocks per symbol (1,622 / 1,909 clusters). n = 61,804 (5-min), 109,999 (1h).
- Management: see the table in 1.8.
- Shadow stops: see 1.17.
- **After the stop is hit first** (n = 32,267 / 55,079):

  | | Target hit in the rest of the window | Geometric prediction from the stop price | Target hit within a fresh H window | Prediction |
  |---|---|---|---|---|
  | 5-min | 0.228 | 0.208 | 0.278 | 0.256 |
  | 1h | 0.212 | 0.215 | 0.267 | 0.267 |

  The stop-out carries no information beyond the new distance d + r.
- **Costs** (CME only, $4.50 RT + 1 tick): 5-min median 0.027R (p90 0.109R); R̄ −0.002 gross → −0.050 net (2 ticks: −0.080). 1h median 0.009R. At a 0.5 ATR stop: 0.087R (5-min), 0.033R (1h).
- **Path artefact:** the 5-min rerun on the engine's assumed OHLC path (`5minPseudo`) changes the trailing-stop gain from +0.001 to +0.016R (3.2 SE). Barrier rules change by at most 0.005R.
- **Drift beta:** 1h per-symbol R̄ ranged from −0.036 (ES) to +0.312 (GC, the 2025-26 gold trend). Raw R̄ carries trend beta, so SKEP-4's Wald adjustment (R − side·μ̂·τ/risk) is needed before calling R̄ an edge.

**B3 · Theory checks** (`b3_theory.py`, `b3b_bayes.py`)
- Brownian bars: engine rule 0.887, TV rule 0.806, binned Bayes 0.884 (1.13).
- Race durations: Monte Carlo confirms E[τ] = ab/σ², E[τ|win] = a(a + 2b)/(3σ²) and E[τ|loss] = b(b + 2a)/(3σ²). Simulated values sit about 17% above the formulas at Δt = 0.02, which matches the discrete-monitoring shift.

### 2.4 Evidence summary for the engine

| Finding | Grade | Implication |
|---|---|---|
| Brackets, partials, break-even, trailing and time stops cannot create expectancy; measured ΔR̄ ≤ 0.01R | strong (theory) + moderate (B2, A) | EV comes from the ledger, not from geometry; management is variance control |
| The displayed EV has no predictive value and a geometric sign | moderate (A T2, T4-B) | TM-1 |
| BE is the wrong null for decided-within-H races (−2 pp) | moderate (B1) | TM-1 uses the driftless conditional |
| Drift in the race hurts calibration | moderate (A, QPOT-01/02) | μ = 0 |
| Mechanical sweep → MSS → FVG has no edge | moderate (A T4-A, P3, P4) | no score bonus |
| Stops just beyond a pool do not survive its sweep | moderate (A T3) | TM-7 wording |
| After a stop-out, target odds follow geometry | moderate (B2) | TM-2 status wording |
| Inner pools: no information beyond distance; opposing untouched FVGs: −0.5 to −3 pp | moderate (A, ICT-5 B5) | TM-3 shows; ICT-5 penalises |
| Fill law d/(d+e) calibrated within 2-4 pp; win\|fill = geometry | moderate (A T4-A) | TM-4 |
| Intrabar rule = Brownian optimum | strong (B3 theory) + moderate (A T1) | keep `f_step` |
| OHLC paths inflate trailing-stop results | moderate (B2) | grade barrier rules only |
| Costs 0.01-0.09R per trade intraday | moderate (B2 + fee schedules) | TM-8 |
| Pre-commitment reduces the disposition effect | strong (lab) / moderate (field); weak for the chart UX | TM-2 |

---

## 3. Engine gap analysis (`baseline_v2.pine`; all line numbers re-checked by B)

| Concept | Status | Lines | What the engine does and how it differs |
|---|---|---|---|
| Two-barrier finite-horizon race (math) | present | `f_race` 447-461, `f_raceH` 466-482 | Correct (MC-verified in `quant_pot`) |
| WIN≤H readout | partial | `f_invalidation` 1359-1364; 2127-2130; HUD 2244-2246; panel 2357-2363 | Drift `potMu·side` (917, 1361); conditional on a decision within H (fine as a label, needs QPOT-02's σ); recomputed from the live close every tick |
| EV readout | **wrong** | 2245, 2359 | `invWin·RR − (1 − invWin)`: geometry only, corr +0.02 with R. Panel colours EV > 0.2 green / ≥ 0 amber / else red (2363), so far targets are always painted red |
| Breakeven win rate | missing | — | — |
| Cost-adjusted BE, position size | missing | — | `syminfo.pointvalue`/`mintick` available |
| Ledger realized R, PF, race win | present | `rOut` 1457-1458; `raceSt` 1079, 1489-1498; Full panel 2419-2426 | Honest but Full-only, with no SE, no drift adjustment (SKEP-4) and no R:R split |
| Ledger race correction | present | `f_raceAdj` 1367-1371; `pRace` stored at 1430 | Baseline is the drift conditional. Do **not** switch it to BE (B1); switch it to the driftless conditional |
| Race edge vs model | missing | — | No "wins − Σp" with z |
| Invalidation rule | present; semantics partial | 1343-1358 | Nearest opposing pool-list level by near-edge distance (liquidity or *any* array with `side == −tgt.side`), far edge − 0.1 ATR; fallback `exeRL/exeRH` then 1.5 ATR; floor 0.25 ATR. Distance gate uses `atr` (1350) while ejection uses `atrE` (minor). Source not reported |
| Invalidation label | wrong wording | 2210-2213 | "⊗ INVALIDATION" for all sources; shown in Clean only when `showInv` (default false, 172) |
| R:R row gating | inconsistent | HUD 2244 (`showInv`), panel 2357 (`not na(invRR)`) | The panel shows R:R / WIN / EV whenever a target exists; the HUD only with `showInv` |
| Post-raid stop | missing | raid detection 1579-1582 | Extreme not stored |
| Protected-swing stop | partial | `exeProtL/H` returned at 925, unused; fallback 1354 uses `exeRL/RH` | ICTS-5 |
| Frozen trade plan | missing | ledger freezes at 1426-1431; HUD recomputes at 2127 | Display and ledger describe different trades |
| Trial existence | conditional | 2038 `(accView != "Off" or useCal)` | `useCal` defaults to true, so usually on, but a plan readout cannot rely on it |
| Plan status | missing | `t.race`, `t.status` 1444-1456 | Visible states on a live trial are only OPEN (race 0) and STOPPED (race −1): hits and expiries are booked and replaced on the same bar (1550-1556, 2038-2045) |
| Time left | missing | `t.bars`, `t.bar0` | Live PoT is a rolling H window (2067) |
| ETA | partial | 2116-2126, HUD 2240 | Hits-only median (survivorship, SKEP-1); constant-σ (QPOT-05/06) |
| Entry zone | missing | arrays in `pool` (kinds 2/4/6, 3/5/7), `ifvgs` (1026) | Arrays only as targets; origin-locked arrays (689-690) are typical entries |
| Limit fill probability | missing | — | d/(d+e) validated |
| Entry models | missing as models (correctly) | raids 1579-1582, BOS 1542-1547, FVG 907-913 / 1867-1889, iFVG 1598-1644, breakers 1646-1661 | No score bonus (correct) |
| Obstacles | partial | `inner` 1240-1248 / ×0.70 at 684-685; `f_pathVol` 1417-1424 / 1945-1947 | Not listed. Opposing-FVG path cost missing (ICT-5) |
| Partials / TP1 | missing | — | — |
| MAE (heat) | partial | 1442-1443; `maeHit` 1073/1483; p80 2404-2408 | Hits only; in ATR, not R; after a stop-out it keeps growing (heat of a stop-less hold) |
| MFE | missing | — | — |
| Stop-distance curve | missing | — | `t.mae`, `t.d0` exist; MTM at H not stored |
| Time stop (vertical barrier) | present | 1455-1456 | A long-lived DOL is re-graded in consecutive windows (2038-2045) |
| Intrabar path rule | present, optimal | 1438-1441 | Brownian optimum (B3); gaps settled at the open |
| Hit asymmetry | present, correct | 1436-1437 | Target strict trade-through for liquidity, stop on touch. Matches limit-exit vs stop-order fills; costs about 0.6 pp of race (B1), which `f_raceAdj` absorbs |
| Alerts | partial | 2077-2093 | No plan fields; no stop / TP1 / zone / window events; `alertcondition` messages carry no values |
| Decision info in Clean | partial | 2214-2226 | Target + PoT only (by design: reference look) |

**Audit notes.**
1. **`f_invalidation` (1343-1364).**
   - Includes draw-aligned arrays as "opposing" (by side). This is ICT-consistent: the stop goes below the bullish FVG the trader would buy.
   - Price inside an opposing FVG gives dd < 0, so that level is skipped and the next is used.
   - The returned probability is conditional with drift; `f_race` is the fallback when pW + pL ≈ 0.
2. **`f_openTrial` (1426-1431).** Stores `pRace` = drift conditional and `rr0`; `risk = |close − inv|` equals the floored risk because `inv := close − side·risk` (1358).
3. **`f_step` (1434-1459).**
   - `t.mae` is updated before the race and keeps growing after a stop-out until the target is hit or H expires.
   - After race = −1 the record runs on, so the PoT grade (hit within H) and the race grade coexist. This is correct.
   - A hit at the bar's open (`tgtOpn`) books rr0, not the better open price. This is conservative and fine.
4. **Ledger driver (2038-2045).**
   - A new trial opens on the same bar the previous one for this level is booked (status 3), so a long-lived DOL is re-graded every H bars with a *new* entry reference and stop.
   - When the target is hit (status 1) the level leaves the pool in step 3 of the same bar, and a different target becomes active.
5. **Rendering (2111-2130).** Re-runs `f_invalidation(activeLv)` with the live close, so R:R, WIN and the stop line move every tick.
6. **ETA (2116-2126).** Compares the current distance with activation distances of past hits (consistent), needs at least 5 hits, bar count only, survivorship-biased.
7. **Alerts (2079-2081).** The new-target alert waits for the PoT filter (`annNow`, 2071), which is good. No plan payload.

---

## 4. Proposals (best first)

Interactions are noted per proposal. Line numbers refer to `baseline_v2.pine`. Siblings referenced:
- `quant_pot.final.md`: QPOT-01 drift, QPOT-02 calibrated race, QPOT-05/06 time and ETA;
- `skeptic.md`: SKEP-1 readouts, SKEP-3 overlap variance, SKEP-4 R-expectancy;
- `ict_struct.final.md`: ICTS-3 race in the Clean tooltip, ICTS-5 protected-swing stop;
- `ict_liq.final.md`: ICT-5 opposing-FVG penalty;
- `competitors.final.md`: COMP-2 alerts, COMP-4 Clean label, COMP-5 stamps, COMP-12 ladder;
- `smc_impl.final.md`: SMC-2 lock.

### TM-1 (P1, S) · Honest race economics: driftless conditional race, breakeven, measured R̄ instead of model EV [A, CORRECTED by B]

**Why.**
- The EV at 2245 and 2359 is a geometric artefact (A, T2 and T4-B).
- A's fix (BE as the ledger baseline) would still show −0.05R to −0.07R for R:R > 1 where realized R is about 0 (B1), because decided-within-H races sit 2 pp below BE.
- No intercept-only shift can predict R (corr ≈ 0). The honest number is the ledger's own realized R̄ with its uncertainty.
- The race probability should be the driftless conditional (QPOT-01/02: drift costs 2.4-3.6% log-loss).

**Spec.**

1. **`f_invalidation` (1343-1364).** Drift removed; the source and the opposing index (for TM-7 and ICTS-3) are returned. This is one shared tuple change:
   ```pine
   f_invalidation(Level tgt) =>
       float buf  = 0.10 * atr
       float inv  = na
       float best = 1e100
       int   src  = 3        // 0 opposing liquidity · 1 opposing array · 2 exec swing · 3 ATR fallback
       int   oppI = -1
       for [i, lv] in pool
           if lv.side == -tgt.side and lv.id != tgt.id
               float dd = lv.distance(close)
               if dd >= 0 and dd < best and dd / atr <= maxATR
                   best := dd
                   inv  := tgt.side == 1 ? lv.bottom - buf : lv.top + buf
                   src  := lv.isLiquidity() ? 0 : 1
                   oppI := i
       if na(inv)
           float sw = tgt.side == 1 ? exeRL : exeRH
           bool  ok = not na(sw) and (tgt.side == 1 ? sw < close : sw > close) and math.abs(close - sw) / atr <= maxATR
           inv := ok ? sw - tgt.side * buf : close - tgt.side * 1.5 * atr
           src := ok ? 2 : 3
       float risk = math.max(math.abs(close - inv), 0.25 * atr)
       inv := close - tgt.side * risk
       float d  = math.max(0.0, tgt.distance(close))
       float sg = nz(potSig)                       // QPOT-05 σ_eff when available
       float pW = f_raceH(d, risk, sg, 0.0, H)
       float pL = f_raceH(risk, d, sg, 0.0, H)
       float pC = pW + pL > 1e-9 ? pW / (pW + pL) : d + risk > 0 ? risk / (d + risk) : 0.5
       [inv, d / risk, pC, src, oppI]
   ```
   Call sites (unique names, all elements bound):
   - 1428: `[inv, rr, pR, iSrc, iOpp] = f_invalidation(lv)`;
   - 2127: `[i0, i1, i2, i3, i4] = f_invalidation(activeLv)`.

2. **Ledger baseline.**
   - `f_openTrial` keeps `pRace = pR`, now the driftless conditional. This is the correct null for races decided within H (B1: residual −0.6 pp vs −2.1 pp for BE).
   - Do not store BE as the baseline.

3. **STATE (1079).**
   - `raceSt` grows from 7 to 9 entries: index 7 = Σ p(1 − p) over decided races; index 8 = Σ rOut² over all booked trials.
   - In `f_book`:
     - inside `if t.race != 0`: `raceSt.set(7, raceSt.get(7) + t.pRace * (1.0 - t.pRace))`;
     - after `rOut` is used: `raceSt.set(8, raceSt.get(8) + t.rOut * t.rOut)`.

4. **Readouts (2127-2130), last bar.**
   ```pine
   invL   := i0
   invRR  := i1
   invWin := f_raceAdj(i2)                       // calibrated WIN≤H (conditional)
   invBE  := 1.0 / (1.0 + i1)                    // geometric breakeven (infinite horizon)
   float nR  = raceSt.get(4)
   float mR  = nR > 0 ? raceSt.get(3) / nR : na
   float vR  = nR > 1 ? math.max(0.0, raceSt.get(8) / nR - mR * mR) : na
   // overlapping windows: inflate by the hit-ledger design effect already computed for the panel (2386-2390), floor 1
   float seR = nR > 1 ? math.sqrt(vR / nR * math.max(1.0, deffNow)) : na
   rBar   := not na(seR) and seR <= 0.15 ? mR : na  // show only when the SE is useful, not on n >= 30
   ```
   - `deffNow` is the same `vEdge / vInd` computed at 2387-2389. Move that computation above the HUD into the last-bar block so both can use it.
   - When SKEP-4 lands, use its drift-adjusted cluster R̄ and SE instead. The display contract stays the same.

5. **HUD (2244-2246).** Replace the EV line:
   ```
   R:R   1.6 · BE 38% · WIN≤H 39%
   R̄     +0.03R ±0.05 (n 212)          // or "R̄ —  (n 41, SE 0.31)" while seR > 0.15
   ```
   - Panel row (2357-2363): col 1 `"1.6 · BE 38%"`, col 2 `"WIN≤H 39%"`, col 3 `"R̄ +0.03 ±0.05"`.
   - Colour col 3 green/red only when |R̄| > 2·SE, otherwise grey.
   - Gate both the HUD line and the panel row on `showInv` for consistency, or on neither.

6. **Full view RACE row (2419-2426).**
   ```pine
   float dW = raceSt.get(1) - raceSt.get(2)
   float zR = raceSt.get(7) > 0 ? dW / math.sqrt(raceSt.get(7)) : na
   f_cell(dash, 1, row, rN > 0 ? "EDGE " + f_signed(100.0 * dW / rN, "0.0") + "pp" : "—", cText, na)
   f_cell(dash, 2, row, na(zR) ? "z —" : "z " + str.tostring(zR, "0.0"), cText, na)
   ```
   Keep PF in col 3.

7. **Tooltip.** "Every stop/target pair breaks even in a random walk: the target wins risk/(risk + reward) of the time (BE). WIN≤H is the calibrated chance the target trades before the stop, among races decided within H bars. R̄ is what this chart's past plans actually returned, ± one standard error."

**Value.** EV stops lying about far targets. BE vs WIN answers "worth it?". R̄ is a model-free, per-chart answer.

**Ledger-measurable.** It is ledger output (race EDGE z, R̄ ± SE).

**Evidence.** Strong (optional stopping), moderate (A T2/T4-B, B1).

**Risk.**
- R̄ shows "—" for a long time (SE ≤ 0.15R needs roughly 100-500 trials). That is honest; say so in the tooltip.
- Raw R̄ includes trend beta (GC 1h +0.31R in B2) until SKEP-4's Wald adjustment is in.
- `pRace` semantics change, so old `raceSt` sums are stale. `var` state resets on reload anyway.

**Effort.** S.

### TM-2 (P1, M) · Frozen trade plan with live progress, time left and honest status [A, CORRECTED by B]

**Why.**
- The HUD recomputes R:R / WIN / EV from the live close (2127) while the ledger grades a bracket frozen at activation (1426-1431). The numbers jump and describe no trade taken.
- Pre-commitment devices measurably reduce the disposition effect (Fischbacher et al. 2017; Richards et al. 2017; Odean 1998).
- B corrected two things in A's spec:
  - it assumed statuses that never appear on a live trial;
  - it relied on a trial existing when the ledger is off.

**Spec.**

1. **Always keep a trial for the active DOL.**
   - Add `bool graded = true` to `Trial`.
   - At 2038 drop the `(accView != "Off" or useCal)` condition from the *opening* test, but pass `graded = (accView != "Off" or useCal) and bar_index >= math.max(0, last_bar_index - calcBars) + warmup`. Opening still needs `not na(activeLv)`.
   - In step 2 (1554-1556): `if f_step(t) != 0` → `if t.graded` → `f_book(t)`; then `openT.remove(i)`.
   - Cost: at most `max(64, H + 1)` trials, as today.

2. **Window counter (engine block, global scope, so assignment is allowed).**
   - STATE: `var int planWin = 1`.
   - In step 2, when booking `t.lvId == activeId and t.status == 3`: `planWin += 1`.
   - At 2031-2035, when `pickId != activeId`: `planWin := 1`.

3. **Render (last bar, after 2127).** Find the plan:
   ```pine
   Trial aT = na
   for t in openT
       if t.lvId == activeId
           aT := t
           break
   ```
   With `aT` present:
   ```pine
   float prog  = aT.side * (close - aT.entry) / aT.risk                          // live R
   float heatL = aT.side == 1 ? aT.entry - low : high - aT.entry                 // live bar's excursion
   float heatR = math.max(aT.mae * aT.atr0, heatL) / aT.risk
   int   used  = bar_index - aT.bar0                                             // includes the live bar
   int   left  = math.max(0, H - used)
   float dNow  = math.max(0.0, activeLv.distance(close))
   float pLeft = activePoT * f_pot(dNow, nz(potSig), 0.0, math.max(left, 1)) / math.max(f_pot(dNow, nz(potSig), 0.0, H), 1e-6)
   ```
   `f_pot(dist, sig, mu, h)` is at 434 and caps at 0.95.

4. **Statuses** (only those that can exist on a live trial):
   - `aT.race == 0` → `PLAN` (open);
   - `aT.race == -1` → `✕ STOPPED · target still ` + PoT(left) + `% in ` + left + `b` (B2: after a stop-out the target is reached 21-23% of the time in the rest of the window, as geometry predicts; do not say "draw failed").
   - Target reached and window ended happen at booking. They are shown by the existing "✕ SWEPT" ghost (COMP-5 adds the plan R stamp) and by `planWin > 1` ("window 2").

5. **HUD block** (Terminal; Clean only via a new input `cleanPlan`, default false, in the tooltip as ICTS-3 places it, never as a third label line):
   ```
   PLAN  w1 · ref 18452.25 · stop 18410.00 (OPP. SSL) · R:R 1.8 · BE 36%
   NOW   +0.42R · heat 0.31R · 18/30b · PoT(left) 41%
   ```

6. **Lines.**
   - Plan reference (dotted, `cText` at 60%) and plan stop (dotted, `cIBear` at 40%) from `f_x(aT.bar0)` to `xR`.
   - They replace the live invalidation line at 2210-2213 when `showInv`.
   - The stop label comes from TM-7. Budget +1 line, +0 labels (the stop label already exists).

7. **Data window plots** for alert placeholders (TM-5): `plot(na(aT) ? na : aT.inv, "DOL Plan Stop", display = display.data_window)` and `plot(na(aT) ? na : aT.rr0, "DOL Plan R:R", display = display.data_window)`.
   - These must be computed at global scope on every bar, since `plot` cannot sit in a local block. Keep `var float planStopOut` and `var float planRROut` updated on confirmed bars from the active trial.

8. **Shared bar-race helper (hygiene).** Factor the hit / stop / `advFirst` logic of `f_step` (1436-1441) into a pure helper `f_barRace(int side, float edge, float inv, bool liq, float entry)`, returning `[hit, stp, advFirst]`. TM-3's TP1 and TM-5's events then reuse the exact same rule.

**Value.** Stable numbers; the plan on screen is the one being graded; time left and post-stop odds are explicit.

**Ledger-measurable.** It is the ledger record.

**Evidence.** Moderate: the display/ledger mismatch is a code fact; P11/P11b; B2 for the post-stop wording.

**Risk.**
- Two R:R numbers (plan vs from here) can confuse. Show the plan by default and the "from here" race in the tooltip.
- Trials now exist with the ledger off: a small CPU cost.

**Effort.** M.

**Interaction.** SMC-2 (lock), COMP-5 (stamps), ICTS-3 (tooltip placement).

### TM-7 (P2, S) · Invalidation semantics: label by source, and optional modes (post-raid extreme, protected swing) [A, CORRECTED]

**Why.**
- The stop is a race barrier. Once a pool is swept, a stop 0.3 ATR beyond it is hit 64-70% of the time on that bar and 92-95% within 12-30 bars (A, T3).
- Its source varies: a liquidity pool, an *array* (often the trader's own entry zone), the execution swing, or a 1.5 ATR fallback (5-7%). The label must say which.
- ICT traders' post-raid stop changes R:R but matches geometry: win − model +1.2 pp (SE 1.9) on 5-min and −2.7 pp (SE 1.5) on 1h (A, T4-A). GBB's best but still unprofitable variant.

**Spec.**

1. **Label (2212)**, from TM-1's `i3` (`src`) and `i4` (`oppI`):
   ```pine
   string invTag = i3 == 0 ? "⊗ OPP. " + f_shortName(pool.get(i4).kind, pool.get(i4).src)
                  : i3 == 1 ? "⊗ BEYOND " + f_shortName(pool.get(i4).kind, pool.get(i4).src)
                  : i3 == 2 ? "⊗ EXEC SWING" : "⊗ 1.5 ATR"
   ```
   Tooltip: "If price trades here before the target, the plan is stopped. Once a pool is swept, a stop this close is taken about 9 times in 10, and the target is still reached about 1 time in 5 afterwards."

2. **Input.** `string invMode = input.string("Opposing Level", "Invalidation", options = ["Opposing Level", "Post-Raid Extreme", "Protected Swing"], group = G_DOL, display = display.none)`. Protected Swing = ICTS-5; share the input.

3. **Post-raid state** (STATE, before `f_invalidation`, so the function can *read* it):
   - `var float raidX = na`, `var int raidSide = 0`, `var int raidBar = na`.
   - In step 3 (1579-1582, global engine scope, so assignment is allowed): when a liquidity level is hit and the bar closes back inside (`evt == -lv.side`, i.e. rejection), set `raidSide := lv.side`, `raidX := lv.side == 1 ? high : low`, `raidBar := bar_index`.
   - Extend `raidX` on later bars while `bar_index - raidBar <= raidWin` (input, default 20).

4. **In `f_invalidation`.**
   - If `invMode == "Post-Raid Extreme"`, `raidSide == -tgt.side`, `bar_index - raidBar <= raidWin` and `raidX` is beyond `close`: `inv := raidX - tgt.side * buf` and `src := 4` ("⊗ RAID EXTREME").
   - Protected swing: `exeProtL/H` with `src := 5`.

5. **Mode on the trial.** Store `int mode` on `Trial`, so race and R̄ stats can be split, or reset `raceSt` when the input changes (it does on reload).

**Value.** Honest wording and the user's own stop model.

**Evidence.** Moderate (A T3, T4-A; P3).

**Risk.** Changing the mode changes R:R and the ledger stats.

**Effort.** S.

**Interaction.** ICTS-3 (shares `oppI`), ICTS-5, ICTS-2 / ICT-9 (raid semantics).

### TM-8 (P2, S) · Cost-aware breakeven and position size [B-new]

**Why.**
- On 5-min futures the engine stop pays a median 0.027R per trade in costs (p90 0.11R), and 0.087R at 0.5 ATR stops. R̄ moves from −0.002 to −0.05R net (B2).
- Lo & Remorov show costs are why tight stops lose.
- A gross BE overstates how good near, tight-stop plans are.
- Traders also need the size for their cash risk. That is pure arithmetic, and the platform exposes `syminfo.pointvalue`.

**Spec.**

1. **Inputs (G_DOL, `display = display.none`).**
   - `float costTk = input.float(0.0, "Round-Trip Cost (ticks)", minval = 0.0, step = 0.5, tooltip = "Spread + slippage + commission per round turn, in ticks. ES ≈ 1.5 (1 tick + $4.50); NQ ≈ 2; 0 = off.")`.
   - `float riskCash = input.float(0.0, "Risk per Trade (account ccy)", minval = 0.0, tooltip = "0 = hide size.")`.

2. **Last bar, with plan risk `rk` (TM-2's `aT.risk`, or `math.abs(close - invL)`) and `rr`:**
   ```pine
   float cR    = costTk * syminfo.mintick / math.max(rk, syminfo.mintick)
   float beNet = (1.0 + cR) / (1.0 + rr)
   float size  = riskCash > 0 ? riskCash / (rk * syminfo.pointvalue) : na
   ```

3. **Display.**
   - `BE 38% (net 40%)` when `costTk > 0`.
   - `size 2.4` (one decimal; futures users round down) when `riskCash > 0`.
   - Tooltip: "Size ignores currency conversion and exchange margin."

4. **Ledger (optional, one line in `f_book`).** Accumulate `cR` of graded trials into `raceSt` (index 9), so the panel can show `R̄ net = R̄ − mean cost`.

**Value.** An honest breakeven and an immediately usable size.

**Evidence.** Moderate (B2 costs; fee schedules; P2). Sizing is arithmetic.

**Risk.** Users must enter their own costs (default 0 = unchanged display). Currency conversion is ignored for FX and crypto.

**Effort.** S.

### TM-5 (P2, S) · Plan events and a trade-plan payload for alerts [A, CORRECTED events]

**Why.**
- Alerts carry only tag, price, score and PoT (2079-2093).
- COMP-2 builds the alert framework (toggles, JSON, `{{plot()}}`, new / reached / approaching / abandoned). This adds the plan fields and the plan events that actually exist (TM-2 states).

**Spec.**

1. **Events** (confirmed bars, `alert.freq_once_per_bar_close`, per-trial once-flags `bool stopAnn = false`, `bool tp1Ann = false`, `bool zoneAnn = false` on `Trial`, set in the engine block, never in a function):
   - **Plan Stopped**: the active trial's `race` became −1 on this bar. Message: `"DOL ▸ STOPPED · " + tag + " · stop " + str.tostring(t.inv, format.mintick) + " · plan R " + f_signed(t.stopR, "0.0") + " · target still " + pLeft + "% in " + left + "b"`.
   - **TP1 Reached** (TM-3): `tp1Hit` became true.
   - **Entry Zone Tapped** (TM-4): `low <= zTop` (long) while the trial is open and `race == 0`. An optional live variant uses `alert.freq_once_per_bar`.
   - **Plan Window Rolled**: a trial of the active level was booked with status 3. Message with plan R (MTM) and the new plan's stop and R:R.
   - Target reached stays COMP-2's "reached", with the plan R added.

2. **Payload** (COMP-2 JSON; numbers via `str.tostring`, prices via `format.mintick`). Add `entry_ref, stop, stop_src, tp1, target, rr, be, be_net, win, rbar, rbar_se, n_ledger, pot, pot_left, bars_left, zone_top, zone_bot, p_fill, size`.

3. **`alertcondition`** (const titles; messages in single quotes):
   - `'DOL plan stopped on {{ticker}} ({{interval}}): stop {{plot("DOL Plan Stop")}}, R:R was {{plot("DOL Plan R:R")}}'`;
   - same pattern for TP1 / Zone / Window.

4. **Toggles.** `alPlan` default false.
   - Mind the platform throttle: more than 15 alerts in 3 minutes halts the script's alerts (faq/alerts.md:201).
   - Never use `alert.freq_all`. Once-flags make each event fire once per trial.

**Value.** Trade management from alerts, plus machine-readable fields for journals and bots.

**Evidence.** Weak (practitioner conventions); platform facts verified.

**Risk.** Noise (off by default); JSON validity.

**Effort.** S on top of COMP-2 and TM-2.

### TM-3 (P2, M) · Path map: next obstacles as TP1 candidates, graded as barrier rules [A, CORRECTED]

**Why.**
- Traders scale out at the first liquidity or opposing array on the path. The engine knows these levels but never shows them.
- Inner pools add no information beyond distance. Opposing untouched FVGs cost a little (−0.5 to −3 pp; ICT-5 owns that penalty).
- Partials are EV-neutral at scale: 50% at half-way −0.004R (SE 0.004) on 5-min, +0.004R (0.003) on 1h, with sd down about 20% (B2). So show them and measure them; do not score them.

**Spec.**

1. **Helper** (after `f_invalidation`; pool ≤ 80, nMax ≤ 3):
   ```pine
   f_obstacles(Level tgt, int nMax) =>
       array<int> out = array.new<int>()
       float dT = tgt.distance(close)
       for k = 1 to nMax
           int   bI = -1
           float bD = 1e100
           for [i, lv] in pool
               if lv.side == tgt.side and lv.id != tgt.id and not out.includes(i)
                   float dd = lv.distance(close)
                   if dd >= 0.25 * atr and dd < dT - 0.10 * atr and dd < bD
                       bD := dd
                       bI := i
           if bI >= 0
               out.push(bI)
       out
   ```
   For a buy-side target this returns, nearest first, inner BSL pools and bearish FVG/OB/breakers above price. `array.includes` is a v6 built-in (reference/array.md:443).

2. **Inputs.** `obsN` (0-3, default 1) and `obsClean` (default false).

3. **Render.** A dotted tick from `bar_index` to `xR` at `lv.nearEdge()`, with a tiny label `"TP1 · " + f_shortName(lv.kind, lv.src) + " · " + str.tostring(dd / rk, "0.0") + "R · " + str.tostring(f_potModel(dd, lv.side, 0.0) * 100, "0") + "%"`. Mark opposing untouched FVGs with "▲ resist" (ICT-5's bit). Budget ≤ 3 lines + 3 labels.

4. **Ledger (barrier rules only, per B2's path-artefact finding).**
   - `Trial` gets `float tp1 = na`, `bool tp1Liq = false`, `bool tp1Hit = false`, `int tp1Bar = -1`, `bool beHit = false`. `f_openTrial` sets `tp1` from the first obstacle.
   - In `f_step`, before the race update, using `f_barRace` (TM-2 step 8) with `edge = t.tp1`:
     - if `tp1` and the stop fall in one bar, `advFirst` decides;
     - break-even is armed only from the *next* bar (`t.bars > t.tp1Bar`), so no intrabar ordering assumption enters it.
   - In `f_book`: `rP = t.tp1Hit ? 0.5 * math.abs(t.tp1 - t.entry) / t.risk + 0.5 * (t.race == 1 ? t.rr0 : t.beHit ? 0.0 : t.rOut) : t.rOut`. Accumulate `tpSt = [n with TP1, TP1-before-stop, ΣR, ΣR², ΣrP, ΣrP²]`.
   - **Do not grade trailing stops**: on OHLC paths they show a spurious +0.016R to +0.035R (B2).

5. **Full panel row.** `TP1 1ST 58% | PART +0.01R sd 1.10 | FULL −0.01R sd 1.38`.

**Value.** Shows where price must go first, the natural scale-out point, and this chart's record of doing so.

**Evidence.** Moderate (A T4-B; B2; ICT-5 B5).

**Risk.** Clutter (Terminal default 1 tick). The `f_step` ordering must reuse `f_barRace`.

**Effort.** M.

**Interaction.** ICT-5 (penalty), COMP-12 (same-side ladder beyond the target).

### TM-4 (P2, M) · Entry zone with fill probability and the zone plan [A, CORRECTED stop derivation]

**Why.**
- ICT traders enter on a retracement into a draw-aligned array, not at market.
- The fill law is calibrated within 2-4 pp and win|fill matches geometry (A, T4-A). Both of Handa & Schwartz's limit-order risks are measurable per chart.
- **[B-fix]** For a long, a bullish array below price has `side == −1`, so `f_invalidation` usually picks *the zone itself* as the opposing level. The zone plan's stop must therefore be derived explicitly. A reused `inv` blindly.

**Spec.**

1. **Helper.**
   ```pine
   // nearest draw-aligned array beyond price: buy-side target -> bullish FVG/OB/breaker below price
   f_entryZone(Level tgt) =>
       int   bI = -1
       float bE = 1e100
       for [i, lv] in pool
           bool polar = tgt.side == 1 ? (lv.kind == 2 or lv.kind == 4 or lv.kind == 6) : (lv.kind == 3 or lv.kind == 5 or lv.kind == 7)
           if polar and lv.side == -tgt.side
               float e = lv.distance(close)            // close - top for a long
               if e >= 0.10 * atr and e / atr <= maxATR and e < bE
                   bE := e
                   bI := i
       bI
   ```
   A parallel loop over `ifvgs` (Zone: `dir == tgt.side`, zone beyond price) returns the nearer of the two. Origin-locked arrays (689-690) are allowed here: entry is not target.

2. **Zone plan (last bar).**
   - `zNear` = near edge (limit price), `zFar` = far edge;
   - `invZ = tgt.side == 1 ? math.min(invL, zFar - 0.10 * atr) : math.max(invL, zFar + 0.10 * atr)`;
   - `e = |close − zNear|`, `d = tgt.distance(close)`;
   - `rkZ = math.max(math.abs(zNear - invZ), 0.25 * atr)`;
   - `pFill = d / (d + e)`, `rrZ = (d + e) / rkZ`, `beZ = 1 / (1 + rrZ)`;
   - with TM-8: `beZnet = (1 + costTk * syminfo.mintick / rkZ) / (1 + rrZ)`.

3. **Render.** A dotted border box on the zone to `xR`, label `"ENTRY · BUFVG · fill ≈72% · R:R 4.8 · BE 17%"`. Terminal by default; Clean via `cleanPlan`. +1 box, +1 label.

4. **Ledger stage (optional).** A limit trial with fields `limE`, `filled`, `missed`, `pFill`, `invZ`.
   - Until filled: a target hit means missed.
   - A touch of `limE` means filled; the race then runs from `limE` against `invZ` with the same `f_barRace` rule.
   - Book fill rate vs Σ pFill (non-execution risk) and win|fill vs Σ beZ (adverse execution).
   - Panel: `FILL 70% (exp 73%) · WIN|fill 18% (BE 17%)`.

5. **Input.** Zone pick rule: "Nearest" or "Best R:R".

**Value.** Turns the DOL into an executable plan with an honest miss risk.

**Evidence.** Moderate (A T4-A; P12).

**Risk.** Zone choice is a design choice. The FVG-stop geometry gives high R:R with low win rates (about 0.17-0.20): show BE beside it.

**Effort.** M (S without the ledger stage).

### TM-6 (P3, S) · Stop-distance expectancy curve from the ledger ("shadow stops") [A, kept; B preview and guard]

**Why.**
- Traders ask "where should my stop be?". On these markets the curve is flat (B2: every s from 0.5 to 3 ATR within ±0.01R, |z| < 1.5).
- A per-chart curve that departs from flat is a measurable selection edge. One that does not is an honest demonstration that no stop is magic.
- Carr & López de Prado warn that picking the best cell is overfitting.

**Spec.**

1. `Trial` gets `float endA = 0.0`. In `f_step` at `status == 3`: `t.endA := t.side * (close - t.entry) / t.atr0`.

2. STATE: `var array<float> sgSt = array.new<float>(11, 0.0)`, i.e. [ΣR, ΣR²] × grid (0.5, 1, 1.5, 2, 3 ATR) plus index 10 = n. It must be an array: "the function cannot modify … any global variables" (language/user_defined_functions.md:29).

3. `f_book` (graded trials only):
   ```pine
   sgSt.set(10, sgSt.get(10) + 1.0)
   for [k, s] in array.from(0.5, 1.0, 1.5, 2.0, 3.0)
       float r = t.mae >= s ? -1.0 : t.status == 1 ? t.d0 / s : t.endA / s
       sgSt.set(2 * k, sgSt.get(2 * k) + r)
       sgSt.set(2 * k + 1, sgSt.get(2 * k + 1) + r * r)
   ```
   This is exact for the stopped condition, even though `t.mae` keeps growing after an engine stop-out.

4. Full panel row: `STOP·ATR 0.5 +0.01 | 1 −0.00 | 1.5 −0.00 | 2 −0.00 | 3 −0.01 (n 140)`.
   - Highlight a cell only when |mean| > 2.6·SE (Bonferroni for 5 cells) and SE ≤ 0.1R.
   - Subtract TM-8's cost per cell (cost scales as 1/s).

**Value.** An empirical, per-chart answer to stop placement, guarded against overfitting.

**Evidence.** Moderate (theory P1/P2b; B2).

**Risk.** Variance at small s (show SE).

**Effort.** S.

### Considered and rejected
- **Score bonus for sweep → MSS → FVG alignment.** No edge over geometry (A T4-A, P3, P4). ICTS-6 alerts on structure shifts with their measured follow-through.
- **Model-based EV of any kind** (formula, or BE shifted by `f_raceAdj`). An intercept shift cannot predict R (B1 corr ≈ 0) and carries the decided-within-H bias. Use measured R̄.
- **Penalising inner same-side pools in the path.** No information beyond distance (A). Opposing FVGs are ICT-5's job, with a ledger guard.
- **Trailing-stop or MFE-trail grading in the Pine ledger.** OHLC path artefact of +0.016R to +0.035R (B2).
- **Automatic time decay or time stop on targets.** EV-neutral (A); no interior optimum (P2d). Show time left (TM-2).
- **Kelly / leverage readout.** p from geometry gives f* = 0; a ledger p invites over-sizing. TM-8 sizes by cash risk only.
- **Lower-timeframe intrabar resolution in `f_step`.** The rule is already the Brownian optimum (88.7%); the residual errors are irreducible from OHLC and hit only same-bar double touches.
- **Fixed 2R/3R targets or ICT SD projections.** EV-neutral, no statistics. The DOL is the target; COMP-12 offers a liquidity ladder.
- **Analytic race-duration ETA** (E[τ|win] = d(d+2r)/(3σ²)). Constant-σ timing ranks poorly (QPOT-05: −0.09); QPOT-06 owns ETA in volatility time.

---

## 5. Notes for implementers

**Order of work.**
1. TM-1, together with QPOT-01/02 (same function, same tuple change as ICTS-3 and TM-7).
2. TM-2 (needs the always-on trial and the `f_barRace` helper).
3. TM-7 and TM-8 (small; read TM-1's tuple).
4. TM-5 on top of COMP-2 and TM-2.
5. TM-3 and TM-4 share the "levels on the path" scan.
6. TM-6 (independent).

**One tuple, three proposals.** `f_invalidation` returns `[inv, rr, pC, src, oppI]` (TM-1 + TM-7 + ICTS-3). Edit 1428 and 2127 together and bind every element with a unique name.

**Globals in functions.**
- "The function cannot modify its declared parameters or any global variables" (language/user_defined_functions.md:29). Counters touched inside `f_book`/`f_step` live in arrays (`raceSt`, `sgSt`, `tpSt`) or in UDT fields.
- `planWin`, `raidX/raidSide/raidBar` are assigned in the engine block (global scope) and only *read* inside functions. Declare them in STATE (1020-1080), before the functions that read them.

**Plots.** `plot()` must be at global scope with a series value on every bar. Keep `var float planStopOut` / `planRROut`, update them on confirmed bars, and plot them with `display = display.data_window` (or `display.none`; `{{plot()}}` still works, visuals/plots.md:151).

**Pine built-ins verified in the local v6 docs:**
- `array.includes` (reference/array.md:443);
- `str.format_time(time, format, timezone)` (reference/str.md:177-183);
- `timeframe.in_seconds()` (reference/timeframe.md:166-172);
- `syminfo.pointvalue` (simple float, reference/syminfo.md:134-142);
- `alertcondition` const message with placeholders (concepts/alerts.md:262-266);
- the alert throttle (faq/alerts.md:201).

**Non-repainting.** Plan values come from trials frozen on confirmed bars. Only NOW fields (progress, live heat, PoT(left)) are live, as the PoT readout already is.

**Drawing budget.** At most +4 lines, +4 labels, +1 box per tick, against the declared 500 each (line 32).

**Measurement plan.** Every proposal adds a ledger statistic:
- race EDGE z;
- R̄ ± SE (gross / net);
- TP1-first rate and partial R;
- fill rate vs Σ pFill and win|fill vs BE_zone;
- the stop curve.

Check before and after on NQ, ES, EURUSD, XAU and BTC at 5m, 15m and 1H.

---

## 6. Sources

**Peer-reviewed / working papers**
- Kaminski, K. & Lo, A. (2014). When do stop-loss rules stop losses? J. Financial Markets 18:234-254. https://dspace.mit.edu/handle/1721.1/114876 ; https://econpapers.repec.org/RePEc:eee:finmar:v:18:y:2014:i:c:p:234-254 ; Kaminski thesis (2006): https://dspace.mit.edu/handle/1721.1/40384
- Lo, A. & Remorov, A. (2017). Stop-loss strategies with serial correlation, regime switching, and transaction costs. J. Financial Markets 34:1-15. https://dspace.mit.edu/handle/1721.1/107017 ; https://econbiz.de/Record/stop-loss-strategies-with-serial-correlation-regime-switching-and-transactions-costs-andrew/10013011284
- Carr, P. & López de Prado, M. (2014). Determining Optimal Trading Rules without Backtesting. arXiv:1408.1159 (read via the paper index).
- Lipton, A. & López de Prado, M. (2020). A closed-form solution for optimal mean-reverting trading strategies. arXiv:2003.10502.
- Glynn, P. & Iglehart, D. (1995). Trading securities using trailing stops. Management Science 41(6):1096-1106. https://web.stanford.edu/~glynn/papers/1995/GI95a.html ; Leung, T. & Zhang, H. (2017). Optimal trading with a trailing stop. arXiv:1701.03960.
- Shiryaev, A., Xu, Z. & Zhou, X. Y. (2008). Thou shalt buy and hold. Quantitative Finance 8(8):765-776. Comment: Majumdar & Bouchaud, arXiv:0809.2878.
- Fischbacher, U., Hoffmann, G. & Schudy, S. (2017). The causal effect of stop-loss and take-gain orders on the disposition effect. RFS 30(6):2110-2129, doi:10.1093/rfs/hhx016. WP: https://www.uibk.ac.at/economics/bbl/bbl_papiere_ss15/schudy.pdf
- Richards, D., Rutterford, J., Kodwani, D. & Fenton-O'Creevy, M. (2017). Stock market investors' use of stop losses and the disposition effect. European J. Finance 23(2):130-152. https://oro.open.ac.uk/44069
- Odean, T. (1998). Are investors reluctant to realize their losses? J. Finance 53(5). Summary: https://rpc.cfainstitute.org/-/media/documents/article/cfa-digest/1999/dig-v29-n2-469-pdf.pdf
- Handa, P. & Schwartz, R. (1996). Limit order trading. J. Finance 51(5):1835-1861. https://econpapers.repec.org/RePEc:bla:jfinan:v:51:y:1996:i:5:p:1835-61
- Linnainmaa, J. (2010). Do limit orders alter inferences about investor performance and behavior? J. Finance 65(4):1473-1506. https://econpapers.repec.org/RePEc:bla:jfinan:v:65:y:2010:i:4:p:1473-1506
- Osler, C. (2000) FRBNY EPR 6(2): https://www.newyorkfed.org/medialibrary/media/research/epr/00v06n2/0007osle.html ; (2003) J. Finance 58(5): https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr125.pdf ; (2005) JIMF 24(2): https://www.newyorkfed.org/research/staff_reports/sr150.html
- López de Prado, M. (2018). Advances in Financial Machine Learning, ch. 3. Summaries: https://hudsonthames.org/does-meta-labeling-add-to-signal-efficacy/ ; https://open-quant.github.io/openquant/modules/labeling
- Fernandes, M. et al. (2018). Uncertainty displays using quantile dotplots or CDFs improve transit decision-making. CHI. https://idl.uw.edu/papers/uncertainty-bus (via `ux_design.md`).

**Practitioner tests and descriptions**
- Silver Bullet [GBB] (Sierra Chart study, 1-min ES/NQ/YM/GC 2011-2026, 2 ticks + $4.50 RT): https://kr.tradingview.com/script/teL2dDvS-Silver-Bullet-GBB/
- 25,000-variant Silver Bullet study (video summary): https://gist.ly/youtube-summarizer/i-backtested-25000-ict-silver-bullet-trades
- [A, not re-opened] https://dev.to/moonthetrain/ict-trading-strategy-backtest-79-setups-on-es-and-nq-d4o ; https://www.backtestingmax.com/backtests/ict-silver-bullet ; https://es.tradingview.com/script/SuBXi3p8-ICT-Silver-Bullet-Backtest/ ; https://backtrex.com/en/backtests/ict-kill-zone-fvg-gbp-usd
- Vendor claims (not relied on): https://takeprofitapp.com/en/learn/ict-silver-bullet-strategy
- Mechanical ICT bot: https://offbeatforex.com/is-ict-strategy-profitable/
- FVG placebo control: https://de.tradingview.com/script/Kbq3WncE-Fair-Value-Gap-FVG-Statistics-with-Placebo-Control/
- 2022 model / Unicorn / iFVG rules: https://www.luxalgo.com/library/concept/model-2022/ ; https://in.tradingview.com/script/FK960gz8-2022-Model-ICT-Entry-Strategy-TradingFinder-One-Setup-For-Life ; https://www.luxalgo.com/blog/ict-unicorn-model-strategy-how-to-use/ ; https://www.tradezella.com/strategies/ifvg-trading-model
- SD projections: https://www.luxalgo.com/library/concept/standard-deviation-projections/
- Traders' equation (Brooks): https://www.topstep.com/blog/the-traders-equation-should-i-take-this-trade ; https://www.brookstradingcourse.com/support-forum/30-traders-equation-and-probability/trade-probability-math/
- Break-even stops: https://atas.net/blog/break-even-in-trading/ ; https://nexusfi.com/showthread.php?p=355842 ; https://tradeify.co/education/break-even-stops ; https://traderpeter.substack.com/p/there-might-be-more-potential-in
- Scaling out: https://enlightenedstocktrading.com/trend-following-profit-targets-do-they-work ; https://www.luxalgo.com/library/concept/scaling-out/
- MAE/MFE: https://nexusfi.com/wiki/trading-wiki/MAE ; https://www.mql5.com/en/articles/23245 ; https://www.luxalgo.com/library/concept/mae-mfe-distributions.md
- Time stops: https://www.tradesviz.com/glossary/time-stop/ ; https://flashalpha.com/articles/when-to-exit-short-options-take-profit-stop-loss-backtest
- Sweep depth: https://www.tradingview.com/script/FRKI2rGw-Liquidity-Sweeps-Stop-Depth-Rider-Algo/ ; https://raw.githubusercontent.com/yeboster/liquidity-sweep-freqtrade/main/README.md
- Futures costs 2026: https://nexusfi.com/a/risk-management/futures-trading-costs ; https://intercom.help/tradeify/en/articles/10468315-trading-commission-fees ; https://intercom.help/top-one-futures/en/articles/12829687-top-one-futures-commissions-and-fees-on-tradovate-accounts ; https://help.topstep.com/en/articles/8284213-what-are-the-commissions-and-fees-in-the-trading-combine-and-express-funded-account ; https://www.cmegroup.com/company/files/cme-fee-schedule-2026-09-14.pdf
- Expectancy / SQN: https://www.tradesviz.com/glossary/system-quality-number/

**Local**
- Pine v6 docs (`scratchpad/docsrc/jabez4jc_pinescriptv6/`):
  - concepts/strategies.md:204;
  - concepts/alerts.md:63, 262-268;
  - faq/alerts.md:201;
  - visuals/plots.md:151-159;
  - reference/array.md:443;
  - reference/str.md:177-183;
  - reference/timeframe.md:166-172;
  - reference/syminfo.md:134-142;
  - language/user_defined_functions.md:29.
- Sibling studies:
  - `quant_pot.final.md` (1.3, QPOT-01/02/05/06/08);
  - `skeptic.md` (SKEP-1/3/4);
  - `ict_liq.final.md` (ICT-5, B5);
  - `ict_struct.final.md` (ICTS-3/5/6);
  - `ict_pd.final.md`;
  - `academic_sr.final.md`;
  - `competitors.final.md` (COMP-2/4/5/12);
  - `ux_design.md`;
  - `smc_impl.final.md` (SMC-2);
  - `calib_ml.final.md`.

## 7. Reproduction
```
T=/tmp/claude-0/-home-user-m/7ce60006-3639-59b1-8cd3-87355409d58a/scratchpad/brief/study
cd $T/trade_tools                                   # A
python3 -I t1_order.py $(pwd); python3 -I t2_ev.py $(pwd)
python3 -I t34.py $(pwd) 5min; python3 -I t34.py $(pwd) 1h
python3 -I analyze.py $(pwd) 5min; python3 -I analyze.py $(pwd) 1h
cd $T/trade_b_tools                                 # B
python3 -I b1_baseline.py ../trade_tools > out_b1.txt          # B1 (needs A's res_*.pkl)
python3 -I b2_manage.py ../trade_tools . 5min                  # about 8 s
python3 -I b2_manage.py ../trade_tools . 1h                    # about 14 s
python3 -I b2_manage.py ../trade_tools . 5minPseudo            # same 5-min bars, engine OHLC path
python3 -I b2_analyze.py . 5min 1h 5minPseudo > out_b2.txt
python3 -I b3_theory.py > out_b3.txt; python3 -I b3b_bayes.py >> out_b3.txt
```
Data come from the sibling folders `amt_data/cme/*` and `classic_tools/btc_1h.csv`. Nothing is downloaded.
