# Skeptical evaluation: which DOL claims hold, and is the engine's ledger honest? (study for DOL Engine v2)

Domain: which ICT/SMC/liquidity claims have empirical support, which are base-rate or geometry artefacts, and which are
folklore. What a naive model already achieves. Survivorship and look-ahead traps in indicator "accuracy". Multiple testing.
An audit of the engine's accuracy ledger, EDGE z-score, random-level baseline and calibration. Proposals that make the
engine's claims honest and make its choices beat *strong* baselines, not just a random level.

Line numbers refer to `/tmp/claude-0/-home-user-m/7ce60006-3639-59b1-8cd3-87355409d58a/scratchpad/brief/baseline_v2.pine`
(identical to `/home/user/m/indicators/dol_engine.pine`).

Reproducible study code and raw outputs (all new, written for this report):
`/tmp/claude-0/-home-user-m/7ce60006-3639-59b1-8cd3-87355409d58a/scratchpad/brief/study/skeptic_tools/`

| Script | Question | Output |
|---|---|---|
| `ev_bias.py` | Is the HUD "EV" (line 2359) an unbiased expected R? | `out_ev_bias.txt` |
| `ledger_null.py` | Is the EDGE z-score (1461-1469, 2383-2390) correctly sized? Which variance estimator is right? | `out_ledger_null.txt` |
| `real_placebo.py` | What EDGE does a *no-skill* picker show on real CME data? | `out_real_placebo.txt` |
| `survivorship.py` | How biased are "ETA\|hit" (2116-2127) and "heat" (2404)? | `out_survivorship.txt` |
| `beta_trap.py` | Does sample-period drift masquerade as directional skill? | `out_beta_trap.txt` |
| `mirror_control.py`, `mirror_seeds.py` | Does a mirror-level control remove baseline miscalibration? | `out_mirror_control.txt`, `out_mirror_seeds.txt` |
| `mt_power.py` | Multiple testing across charts/settings; minimum detectable edge | `out_mt_power.txt` |

Data: the local CME futures files used by the sibling studies (ES, NQ, CL, GC, RTY, YM: 1-hour Mar/Jun 2025 to Apr 2026;
1-minute Jan to Apr 2026, resampled to 5-minute), EURUSD 1-hour.

Research note. The Firecrawl web-search credits were exhausted on the first call, the shared WebSearch budget ran out midway,
and WebFetch could not resolve most hosts (tradingview, arxiv.org, vendor blogs). The Firecrawl *paper index* still worked, so
academic sources were read directly from it (passages quoted below). Vendor studies cited by sibling reports (Nordman,
MarketTrace, Trader Markus, Barot SSRN, Mahadzva SSRN) could not be re-fetched; where a WebSearch summary confirmed them it
is said so, otherwise they are marked "via sibling" and graded no higher than the sibling did.

---

## 0. Key findings (read this first)

1. **Almost every ICT/SMC "magnet" claim that has been tested reduces to geometry.** Pools, FVGs, order blocks, PDH/PDL and
   session extremes are reached at the rate of a *random level at the same distance* (FVG 73.0% vs 72.9%, OB 73.7% vs
   73.7%, S&P daily FVG 69% vs 69%, PDH/PDL within ±3 pp of a day-bootstrap null). What survives is small and short-lived:
   reactions of +2.5 to +5 pp at 1-15 minutes, S/R bounce rates of 60.8% vs 56.2% for random levels (Osler 2000), and the
   stop-cluster mechanism itself (Osler 2003/2005, strong). Directional ICT claims (AMD/Power of 3, sweep → reversal,
   structure-based draw) carry **no information beyond the trend regime or geometry**: AMD bullish 46.9% (coin flip), bearish
   39.9% (inverted), with trend explaining all of it (Taylor 2026, N = 484).
2. **The base rates are high, so raw "hit %" is meaningless.** On CME futures and EURUSD, a *random* level 1 ATR away is
   traded through within 30 bars **75-80%** of the time, 2 ATR **54-62%**, 3 ATR **39-47%** (this study). "Take the nearer
   pool" wins the which-side-first race **64.5-70.6%** of the time (gambler's ruin b/(a+b); sibling quant_regime). Any
   indicator advertising 70-80% target hits is quoting geometry.
3. **The engine's ledger is leak-free and its baseline is the right *kind* of baseline** (distance-matched, regime-split,
   learned prequentially). Its regime split even absorbs trend beta: an "always long" picker beats the mirror level by
   **+8.3 ± 3.9 pp** on EURUSD 1h and **+10.8 ± 6.2 pp** on GC 1h by drift alone, and a model-free comparison would call that
   skill.
4. **But four readouts are biased by construction** (this study):
   - **ETA|hit** (2116-2127) is a median over *hits only*. It shows 9 bars at 2 ATR when the true median time-to-touch is
     19-25 bars, and 12-13 bars at 3 ATR when the true median is "> 30 bars" (P(touch ≤ 30) is only 39-47%).
   - **heat** (2404, from `maeHit` 1481-1483) is the 80th-percentile adverse excursion of *hits only*: 1.6-2.3 ATR, against
     **3.2-5.1 ATR over all trials** and 5.9-7.8 ATR for misses. It understates the pain of holding toward the target about 2×.
   - **EV** (2359) is computed from P(target first | race decided within H). Under a driftless martingale the true expectancy is
     exactly 0, but the readout shows **−0.62R** (target 2R, σ√H = 1R) to **−0.97R** (3R) and ≈ 0 only when nearly all races
     decide. Add the drift term and the number is noise plus conditioning bias.
   - **L50** (2395-2396) is a raw rolling hit rate with no expected rate: it rises and falls with target distance, not skill.
5. **The EDGE z-score has the right size at one look but the wrong failure modes.**
   - Peeking: re-evaluated every bar, z ≥ 2 shows "✓ EDGE" for 10/15/20% of null charts within 100/300/1,000 trials
     (sibling calib_ml simulation).
   - Baseline miscalibration shifts it. A *no-skill* picker graded on real data shows a mean excess from **−4.0 pp** (GC 1h,
     roll gaps; 25% of runs at z ≤ −2) to **+1.0 pp**; a picker that only fires in busy US hours shows **+2.0 pp** (z̄ +0.6) and
     one that fires in quiet Asia hours **−2.0 pp** (z̄ −1.1; ES/NQ runs at z ≈ −2.2 to −2.5).
   - The variance is uncentred, keyed by booking bar, and uses 2H blocks (1463-1469). Under intraday seasonality it is
     *conservative* (z sd 0.76 under the null) and **costs power**: a real +3.3 pp edge is flagged 10% of the time versus 30%
     with centred 8H blocks.
6. **A mirror control fixes the miscalibration problem cheaply.** Subtract the residual of a level at the same ATR distance on
   the opposite side, opened on the same bar with the same hit rule. For clock-timed no-skill pickers on real 5-minute data
   the mean |bias z| falls from **0.69 to 0.24** (busy hours +2.04 pp → +0.24 pp, quiet hours −1.97 pp → −0.06 pp), with
   the same spread. On independent 1-minute segments a paired placebo test had z sd 0.96 and a 2.6% two-sided false-alarm rate.
7. **The ledger cannot see small edges.** With the active-DOL ledger's standard error of 1.4-2.4 pp per 5,000 bars (sibling
   calib_ml), the minimum detectable edge at 80% power is **3.9-6.7 pp** at a fixed look and **5.5-9.5 pp** with an
   anytime-valid boundary. The best-supported ICT effects are 2-5 pp. "NO EDGE" at default depth mostly means "not
   measurable", and the panel should say so.
8. **Multiple testing is the user's real enemy.** Flipping through 10 symbols at one fixed look gives a 21% chance of at least
   one false "✓ EDGE"; with peeking, 80%. Keeping the best of 45 settings gives E[max z] = 2.21 and P(max z ≥ 2) = 64% under
   the null. The defaults themselves were chosen on charts, so every on-chart ledger is in-sample until bars arrive after the
   settings were fixed.
9. **The engine's scoring pillars are mostly not supported beyond geometry** (sibling evidence, consolidated here):
   - Draw (weight 30): D-first selection *loses* 9-12 pp of first-touch accuracy intraday versus geometry (quant_regime).
   - Confluence (15) and source tier: external/key levels are hit *less* than random at the same distance (−0.14 to −0.27
     logit; calib_ml).
   - Tests (+0.35 each in density): prior bounces make the *next* bounce more likely (Garzarelli 2014; Chung & Bellotti
     2021), so for a trade-through target they should lower, not raise, short-horizon odds.
   - Killzone affinities (597-602): session take rates are within ±3 pp of a clock-matched null (session_stats).
   - Drift in PoT and races: hurts log-loss by 1.2-7.1% (quant_pot, quant_regime).

   EQH/EQL (+0.08/+0.29 logit) is the only density feature with weak positive support.
10. **"Draw on liquidity" is a destination, not "the next liquidity taken".** The engine deliberately targets the *outermost*
    pool (inner-pool penalty ×0.70, line 685), so by construction the inner pools are taken first. The ledger measures
    "touched within H", which is the right metric for a destination. The README's "most likely drawing to next" is the wrong
    claim for it.

**Bottom line for design.** The honest DOL engine treats geometry (distance, volatility, clock) as the backbone and every ICT
feature as a modifier that must *earn* its weight on the user's chart. It grades itself with:
- survivorship-free readouts;
- a mirror-controlled, anytime-valid edge test;
- a model-free R-expectancy test (martingale null);
- a league table against strong naive selectors (nearest pool, max expected reach, trend-side nearest);
- a forward-only sub-ledger.

The ten proposals in §4 do exactly that. Each is measurable by the engine's own ledger.

---

## 1. Concepts (definitions and parameters)

### A. The claims under test

Each entry gives the testable definition used in the quantitative studies, the practitioner use for "where / when / how
likely", and the null hypothesis it must beat.

**1.1 Liquidity pools as magnets (BSL/SSL).**
- *Definition:* resting stop orders sit just beyond swing highs/lows. Engine version: a pivot high with `pivLen = 5`
  (`ta.pivothigh(high, 5, 5)`, confirmed 5 bars late), with a zone of `zoneATR = 0.20` ATR beyond it (1848).
- *"Swept"* means trade-through: strict `high > level` (624).
- *Practitioner use:* the unswept pool on the bias side is the target, and the outermost pool of a stack is the real draw.
- *Null:* a random level at the same distance (and side and regime), touched with the same rule within H bars.
- *Mechanism vs magnet:* Osler's order-book data prove the *mechanism* (stops cluster beyond extremes and round numbers;
  crossing them accelerates price). The *magnet* claim is that pools are reached more often than geometry predicts. That is
  a different, much stronger claim.

**1.2 Equal highs/lows (EQH/EQL, "relative equal").**
- *Definition:* two or more pivots within `eqTol = 0.10` ATR (engine 56, folded by `f_mergeAt`).
- *Use:* "double tops are engineered liquidity, the obvious target".
- *Null:* an ordinary swing pool at the same distance.

**1.3 Sweep → reversal (turtle soup, "raid then reverse", Judas swing).**
- *Definition:* price trades through a pool, then closes back inside within k bars (`k = 1-2`). The claim is that it then
  runs to the opposite pool.
- *Null:* the symmetric ±x ATR race from the post-sweep close is 50/50 (martingale).
- *Engine:* `liqEvt` in D treats a raid that "holds" as continuation and one that "rejects" as reversal.

**1.4 Fair value gaps (FVG), consequent encroachment (CE), inversion (iFVG).**
- *Definition (3-candle):* bull FVG when `low > high[2]`. The engine adds a size gate `fvgMin = 0.15` ATR and a quality gate
  (869-887).
- *Claims:*
  - (a) price returns to fill;
  - (b) the gap is a reaction level (CE = 50% midpoint);
  - (c) once closed through, it inverts (iFVG) and holds as the opposite S/R.
- *Null:* a same-size zone at the same distance and time with no gap (placebo zone).

**1.5 Order blocks (OB), breakers, mitigation/rejection/propulsion blocks.**
- *Definition (OB):* the last opposite-colour candle before the displacement leg that broke structure.
- *Breaker:* a failed OB that swept liquidity.
- *Claims:* price returns to the OB and reacts; a breaker flips polarity.
- *Null:* a random zone at the same distance.

**1.6 Killzones and session raids.**
- *Definition (ET):* Asia 20:00-00:00, London 02:00-05:00, NY AM 07:00-10:00, NY PM 13:30-16:00 (engine 184-187).
- *Claims:* "London raids Asia, NY raids London and the prior day" (engine `f_kzAff` 597-602: ×1.05 to ×1.20). Raids are
  more productive inside killzones.
- *Null:* a clock-matched random path (the day bootstrap with the same volatility clock).

**1.7 AMD / Power of 3 / Judas swing.**
- *Definition:* Asia accumulates. London breaches one side of the Asia range by ≥ δ and closes back inside. NY delivers to
  the *opposite* Asia extreme (Taylor 2026, δ = 10 NQ points, breach before 04:00 ET, close-back before 05:00).
- *Null:* 50/50 for the close vs Asia midpoint, or the trend regime alone.

**1.8 Market structure (BOS/CHoCH) and the draw direction.**
- *Definition:* a close beyond the protected swing (BOS), or the first break against the prevailing swing sequence (CHoCH).
- *Use:* bias → draw side → choose the target on that side.
- *Engine:* `D = 0.5·htfBias + 0.3·stfBias + 0.2·exeIB` blended with displacement and liquidity events (1892-1895). Selection
  is draw-side first (1975) with 2× hysteresis to flip sides (2012).
- *Null:* which-side-first by geometry, b/(a+b).

**1.9 Premium/discount and the dealing range.**
- *Definition:* above 50% of the dealing range is premium (sell), below is discount (buy).
- *Null:* none in ICT. The academic analogue is the 52-week-high effect (George & Hwang 2004), which predicts
  *continuation* near highs.

**1.10 Key levels: PDH/PDL, PWH/PWL, session highs/lows, midnight open.**
- *Claims:* they are taken (frequent, obvious); they are taken in a characteristic session; the opposite side follows
  (Judas).
- *Null:* the day-bootstrap path with the same clock.

**1.11 S/R tests ("the more touches, the weaker the level").**
- *Definition:* the number of prior bounces (b_prev) at a level within a lag window.
- *Engine:* `tests` counts approaches within `testATR = 0.30` ATR (652-656) and *adds* density (+0.35 per test, up to 6; 682).
- *Null:* shuffled-return series give p(bounce) = 0.5.

**1.12 Round numbers and stop clusters.**
- *Definition:* prices ending in 00/50.
- *Evidence:* take-profits cluster *at* them (reversals); stops cluster just *beyond* them (cascades).

### B. Base rates and naive models (what any DOL engine must beat)

**1.13 Random-walk touch probability.**
- For driftless Brownian motion with per-bar σ and horizon H, `P(touch d) = 2Φ(−d/(σ√H))` (reflection principle; engine
  `f_pot` 434-444). It is about twice the probability of *finishing* beyond d (the options "probability of touch ≈ 2× ITM"
  rule; optionsanalysissuite).
- Using highs/lows makes the continuous formula appropriate. A close-based event needs the Broadie-Glasserman-Kou shift
  (sibling quant_pot).
- Empirical touch rates within H = 30 bars for random levels (this study, `survivorship.py`; probes every 3rd bar, both
  sides, strict trade-through):

  | Distance | ES/NQ/CL 1h | ES/NQ/CL 5m | EURUSD 1h |
  |---|---|---|---|
  | 1 ATR | 77-80% | 75-76% | 77% |
  | 2 ATR | 58-62% | 54-56% | 59% |
  | 3 ATR | 42-47% | 39-41% | 43% |

**1.14 Gambler's ruin: nearest-first.**
- For levels a above and b below, `P(up first) = b/(a+b)` for any continuous martingale (optional stopping), whatever the
  volatility clustering or seasonality.
- Sibling quant_pot found real races within 0.4-1.2 pp of it on about 28k races per cell.
- The naive "nearer pool first" rule scores **0.645-0.706** among decided races (sibling quant_regime: 1H / 5m / 15m / D).
- This is the *strong* baseline for "which side is taken next".

**1.15 Martingale expectancy (optional stopping / Wald).**
- For any bounded exit rule (target, stop, time-out at H), `E[X_τ − X_0] = μ·E[τ]`. With no drift, the expected R of
  *every* target/stop choice is exactly 0.
- So the race's average R is a model-free edge statistic. The only nuisance term is drift (beta), and it is removable:
  `E[R] = side·μ·E[τ]/risk`.

**1.16 Arcsine law (timing).**
- The time of a Brownian path's maximum on [0, T] has density `1/(π√(t(T−t)))`. Window edges are over-represented.
- "The HOD forms in the first hour" and "the weekly low forms Mon/Tue" are largely this arithmetic (sibling ict_time §2.3;
  random-walk weekday baseline Mon 29.5 / Tue 14.1 / Wed 12.8 / Thu 14.1 / Fri 29.5%).

### C. Evaluation traps (how indicator "accuracy" goes wrong)

**1.17 Base-rate trap.** A hit rate with no expected rate. The fix is to always print "hit / expected", where expected is the
distance-matched baseline.

**1.18 Survivorship (conditioning on success).**
- Statistics computed over hits only: time-to-hit, adverse excursion, R of winners.
- The fixes:
  - time-to-event with censoring (Kaplan-Meier; with a fixed horizon and no early censoring, the KM curve equals the
    empirical CDF of `min(T, H+1)`);
  - excursions over *all* trials.
- The visual analogue: a chart that only keeps swept targets (ghosts) invites hindsight. Abandoned and expired targets must
  stay visible.

**1.19 Conditioning on decided races.** `P(target first | decided by H)` is a legitimate quantity. An "EV" built from it
ignores the undecided mass, whose mean R is not zero when targets and stops are asymmetric. This study shows the bias is
large (§2.3 A).

**1.20 Look-ahead and repainting.**
- Pivots need `pivLen` future bars; drawing them at the pivot bar repaints.
- `request.security(..., lookahead_on)` without a `[1]` offset leaks the current HTF bar.
- Intrabar order is unknown on OHLC bars: the engine assumes O-L-H-C for bull bars and O-H-L-C for bear bars (1440-1441);
  trade_mgmt found TradingView's broker-emulator rule right 80.6-80.7% of the time.
- Exits evaluated on coarse bars inflate results: Barot's apparently profitable FVG construction (PF ≈ 2.4) fell to PF ≈ 1.0
  on 1-minute data (via sibling ict_pd).
- A deliberately leaky oracle with Sharpe 35 *survives* deflated-Sharpe and PBO tests (Gençay 2026). Statistics cannot catch
  look-ahead; only construction can.

**1.21 Overlap and dependence.**
- H-bar windows that overlap share one price path. The design effect is `deff = V_cluster / V_independent`.
- Clusters must be keyed by the window's *open* bar, centred, and wide enough to span the dependence. Intraday seasonality
  creates positive short-lag and negative long-lag correlation of residuals, so the right block width is at least a session
  (this study, §2.3 B).

**1.22 Baseline miscalibration.**
- The baseline is a model. If it is off by b pp for the picker's mix of distances, hours and sides, the excess is shifted by
  b, whatever the skill.
- *Placebo control:* grade a no-skill comparator on the same bars and subtract.
- *Mirror control:* the level at the same distance on the opposite side, same bar, same rule. It cancels miscalibration that
  is common to both sides (clock, volatility regime, roll gaps).

**1.23 Beta masquerading as skill.**
- In a trending sample, any picker biased to the trend side looks skilled.
- The fixes: a regime-split baseline (engine) or a drift term in the R test (Wald).

**1.24 Peeking (optional stopping of the *analyst*).**
- A fixed-α test re-evaluated after every sample eventually rejects.
- The fixes: confidence sequences / e-processes (Robbins 1970; Howard et al. 2021; Waudby-Smith & Ramdas 2020–2024;
  Johari et al. 2017).

**1.25 Multiple testing and forking paths.**
- Many charts × many families × many settings.
- Corrections: Bonferroni/Holm/BH, White's Reality Check, Hansen's SPA, deflated Sharpe, PBO.
- Literature hurdles: t > 3 (Harvey-Liu-Zhu), bootstrap 4.5 and forking paths ≥ 8.2 (Coqueret 2023).
- Minimum backtest length: `MinBTL ≈ (E[max of N standard normals])² / SR²` years. About 45 configurations exhaust 5 years
  of data for a target annual Sharpe of 1 (Bailey, Borwein, López de Prado & Zhu 2014; recalled from the paper, formula
  checked: E[max of 45] ≈ 2.2 → 4.9 years).

**1.26 Bandit feedback / selection.** A ledger that grades only the chosen target learns only about what it already
prefers. Full-information shadow probes fix it (sibling calib_ml CAL-3).

**1.27 Destination vs "next".**
- "Which liquidity is taken *next*" is a first-passage question over *all* pools. The nearest pool on each side always comes
  first on its side.
- A *destination* (outermost pool) is never "next" while inner pools exist. Its correct metrics are "touched within H" and
  "before the invalidation".

**1.28 Power and minimum detectable effect (MDE).**
- `MDE ≈ (z_crit + z_power) · SE`.
- A verdict without its MDE turns "not measurable" into "no edge".

**1.29 In-sample vs forward.**
- A prequential ledger is leak-free per trial. But the settings (and the developer's defaults) were chosen on the same history.
- Only trials opened after the settings were fixed (realtime bars) are truly out-of-sample.

---

## 2. Evidence

Grades: **strong** = peer-reviewed or large replicated quantitative study; **moderate** = published, reproducible statistics
or backtests with numbers; **weak** = practitioner consensus or anecdote; **none** = folklore or unfalsifiable.
"[this study]" = `skeptic_tools/`. "[sibling X]" = another report in this folder; the numbers were checked against its
outputs where available.

### 2.1 Claims ledger (verdict per claim)

Verdict classes:
- **Supported:** survives a proper null.
- **Geometry:** the outcome is true but fully explained by distance, volatility or the clock.
- **Small/short:** real, but a few pp and minutes to hours.
- **Contradicted:** the measured effect has the opposite sign.
- **Unsupported:** tested, no effect.
- **Untested / unfalsifiable:** as typically stated.

| # | Claim | Verdict | Key numbers | Grade | Sources |
|---|---|---|---|---|---|
| C1 | Stops cluster beyond extremes/round numbers; crossing them accelerates price | **Supported** (mechanism) | 9,667 orders: 8.7% at "00" vs about 1% uniform. Stop-loss buys 14.4% at 01-10 above 00 vs 7.4% at 90-99 below (p = 0.029). Cascades significant from 15 min to 2 h, not at 1-2 days | strong | Osler 2003 JF / FRBNY SR125; Osler 2005 JIMF / SR150 |
| C2 | Pools are reached more often than a random level at the same distance (magnet) | **Geometry** | External pools vs random: −0.14 / −0.27 logit (t −1.1 / −2.9, 5m / 1h). PDH/PDL take rates within ±3 pp of a day-bootstrap null on 7 markets (ES PDH 58.8% vs 57.0%) | moderate | [sibling calib_ml §0.6], [sibling session_stats §0.1] |
| C3 | Equal highs/lows are taken more than single swings | **Small** | +0.08 / +0.29 logit (t +0.7 / +3.6). An open-source distance-matched test: EQ improves the odds by < 1% | moderate | [sibling calib_ml], [sibling ict_liq E6] |
| C4 | Sweep → reversal (turtle soup) | **Contradicted / unsupported** | Post-sweep ±1 ATR race 0.497-0.510 whether the raid "holds" or "rejects" (5m/15m/1h); daily continuation 0.539. 65 of 66 walk-forward fold selections favour continuation (G10 FX). Mesfin's "liquidity grab reversal" family failed out of sample (MNQ) | moderate | [sibling quant_regime §0.7]; Mahadzva SSRN 7430998 (via ict_liq, confirmed only by a vendor summary); Mesfin 2026 arXiv 2605.04004 |
| C5 | FVGs get filled / are magnets | **Geometry** | Return to 73.0% of FVGs vs 72.9% of random twins (38k FVGs, 5m futures). S&P daily: 69% vs 69% within 20 days. BTC 1h full fill 75.6% vs 72.4% (+3.2 pp). TradingView placebo-control script: no detectable advantage over size-matched placebo zones in 14 measurements (3 asset classes × 3 TFs × 2 periods) | moderate | Nordman, Trader Markus, MarketTrace (via sibling ict_pd); placebo script (WebSearch summary) |
| C6 | FVG/CE is a reaction level | **Small/short** | Reaction about 5 pp above random (≈40k FVGs, 4 futures, 3 TFs, 7 years), "no tradeable edge". Edge ratio +3.7% at 5 min, +2.5% at 15 min, −0.2% at 1 h | moderate | Barot SSRN 7148099; Nordman (via ict_pd) |
| C7 | iFVG holds as flipped S/R | **Unsupported** | Broken bullish gaps held as resistance 38% vs 38% random; bearish 47% vs 47% | moderate (one source) | Trader Markus (via ict_pd) |
| C8 | Order blocks attract and hold price | **Geometry** (reach), **small/short** (reaction) | Revisited 73.7% vs 73.7% random. Next-bar entry +3.3-4.8% edge ratio at 1-5 min. Negative after costs except one market | moderate | Nordman (via ict_pd) |
| C9 | Breakers, mitigation/rejection/propulsion blocks, CE/MT, PD-array matrix ordering, IRL/ERL alternation | **Untested** | No audited statistics found by any sibling | none-weak | [sibling ict_pd §2.7] |
| C10 | Volatility is concentrated in killzones (timing) | **Supported** | ES 5m variance at 09:30 is 4.7× the daily mean and 0.20× at 23:30. Peak/quiet hourly range 2.1-4.0× across 10 instruments | strong | Andersen & Bollerslev 1997; [sibling quant_pot §0.4], [sibling ict_time E1-E2] |
| C11 | Sessions raid specific liquidity ("London raids Asia") beyond the clock | **Geometry** (exception below) | Session take rates within ±3 pp of the clock-matched null. Exception: the opposite Asia-range side is taken +3.5 to +6.2 pp more on ES/NQ/YM/RTY (≈3 SE), not on CL/EURUSD/BTC | moderate | [sibling session_stats §0.1-0.2] |
| C12 | AMD / Power of 3 / Judas | **Unsupported** (trend explains) | Bullish 46.9% (CI 40.5-53.4), bearish 39.9% (inverted, p = 0.002). Trend-aligned 62-71%, trend-opposed 25-30% (all BH-corrected). 57% of targets were delivered *before* the 09:40 entry | moderate (one preprint, N = 484, code public) | Taylor 2026 arXiv 2610.35887 (passages read) |
| C13 | Silver Bullet | **Unsupported** | 108 trades, 38.9% win rate at 1:1, net loss | weak (negative) | tradestar.app (via ict_time) |
| C14 | Structure/draw vector picks the side taken first | **Contradicted** (as a selector) | D-proxy 49.9-51.6% for which side first. D-first selection 0.550-0.652 vs geometry 0.645-0.706 (−9 to −12 pp intraday). ER-gating recovers geometry within 0.2 pp. Displacement/MSS edge ratio ≈ 1.00 at 1 h | moderate | [sibling bias_dol], [sibling quant_regime §0.4], Nordman MSS (via ict_pd) |
| C15 | Premium → sell, discount → buy | **Contradicted** at monthly horizons; **untested** intraday | Nearness to the 52-week high predicts continuation (George & Hwang 2004) | strong (equities, monthly) | via sibling ict_pd |
| C16 | Prior bounces make a level *weaker* (folk) | **Contradicted** | p(bounce \| b_prev) > 0.5 and rising with b_prev (independence rejected p < 0.0001 at 45-90 s, LSE). 1-bounce EURUSD levels decay to 0.5 at ≈350 min, 4-bounce at ≈900 min | strong (HF) / moderate (1-min) | Garzarelli et al. 2014 Sci. Rep.; Chung & Bellotti 2021 arXiv 2101.07410 (passages read) |
| C17 | S/R levels interrupt trends more than random levels | **Supported, small** | Published S/R levels: 60.8% bounce vs 56.2% for 10,000 sets of arbitrary levels (+4.0 to +5.6 pp per currency; effect persists 5 days, 1.7 pp weaker) | strong | Osler 2000 FRBNY EPR (the 56.2% figure confirmed via a second copy; the 60.8% via sibling ict_pd) |
| C18 | Round numbers act as price barriers (holding) | **Mixed** | Round levels attract more limit liquidity but do not show longer depth-adjusted durations (5 Nasdaq stocks, 2025). EBS FX books cluster at old round prices; algos front-run them by one tick | moderate | Jung & Lee 2026 arXiv 2610.34787; Lallouache & Abergel arXiv 1307.5440 |
| C19 | ADR is "exhausted" after a full ADR | **Contradicted** | After ≥ 1 ADR used, real extension exceeds the null by +4 to +10 pp | moderate | [sibling session_stats §0.3] |
| C20 | "HOD forms in the first hour"; "weekly low Mon/Tue" | **Geometry** (arcsine) | Weekday of weekly extreme Mon/Fri 23-34%, Tue-Thu 12-18%, equal to a day-order shuffle | strong (null) | [sibling session_stats §0.1], [sibling ict_time E15] |
| C21 | Intraday momentum from OHLCV signals | **Unsupported after costs** | 14 signal families, none passed walk-forward (gross edge 0.07-1.50 pts vs a 2-pt friction floor). Asia expansion-bar continuation T = −10.96 (wrong sign) | moderate | Mesfin 2026 arXiv 2605.04004 (passages read) |
| C22 | Technical trading rules in general | **Mostly data-snooped** | The BLL rule universe on 100 years of DJIA, Reality Check; 21,000 rules on MSCI with an FDR correction; 7,000+ rules with SPA on Chinese indices: significance concentrated in less-efficient periods, gone after costs or in later samples | strong | Sullivan, Timmermann & White 1999; Sermpinis et al. 2018 arXiv 1811.06766; Wang et al. 2015 arXiv 1504.06397 |

### 2.2 Literature on evaluation, overfitting and honest inference

| Topic | Numbers | Grade | Source |
|---|---|---|---|
| Random-level baseline is the established control for S/R claims | 10,000 artificial level sets as the null | strong | Osler 2000 |
| Shuffled returns / AR(1) as the null for S/R memory | p(b \| b_prev) ≈ 0.5 for random walks; stationary AR(1) gives a *decreasing* p(b \| b_prev), so real S/R memory is not mean reversion | moderate | Chung & Bellotti 2021 |
| Data snooping in technical rules | Reality Check bootstrap; "by looking long enough … an investor will always find a trading rule parameterization that works" | strong | Sullivan, Timmermann & White 1999, JF 54(5) |
| False-discovery hurdles | Multiple-testing algorithms give t-hurdles above 3.0 | strong | Chen & Zimmermann 2022 arXiv 2209.13623; Harvey & Liu 2020 arXiv 2006.04269 |
| Forking paths | Each extra degree of freedom widens the t-stat range by ≥ 30%. The 5% threshold is 4.5 (bootstrap) vs ≥ 8.2 (paths) | moderate-strong | Coqueret 2023 arXiv 2401.08606 |
| Backtest overfitting | PBO via CSCV; MinBTL. With 5 years of data, about 45 trials suffice to fake a Sharpe-1 backtest | strong (theory) | Bailey, Borwein, López de Prado & Zhu 2014/2015 (SSRN 2326253) |
| Statistics cannot detect look-ahead | A leaky oracle with Sharpe 35 survives DSR and PBO | moderate | Gençay 2026 arXiv 2608.27734 |
| Holdout discipline | An LLM-found survivor with Sharpe ≈ 3 in discovery and validation fell to 0.26 on its single holdout | moderate | Zhang 2026 arXiv 2611.06607 |
| Peeking | Optimizely's false-positive rate fell "from over 20% to under 5%" with always-valid inference. Re-testing z ≥ 2 each trial gives 10/15/20% false "EDGE" at 100/300/1,000 trials | strong / moderate | Johari et al. 2017; [sibling calib_ml `peek_sim.py`] |
| Anytime-valid inference | Normal-mixture confidence sequence `|S| < √((V+ρ)ln((V+ρ)/(ρα²)))`: boundary z ≈ 3.0-3.7 for V = 10-250 (ρ = 10). Betting confidence sequences for bounded means are variance-adaptive and tight | strong (theory) | Howard et al. 2021 arXiv 1810.08240; Waudby-Smith & Ramdas arXiv 2010.09686 |
| Optional stopping (martingale expectancy) | E[X_τ] = X_0 for bounded τ; Wald: E[X_τ − X_0] = μE[τ] | strong (theory) | standard probability; races ≈ b/(a+b) within 0.4-1.2 pp on real data [sibling quant_pot §0.6] |

### 2.3 This study's experiments

**A. The HUD "EV" is conditioned on decided races (`ev_bias.py`).** Driftless Brownian motion with 20 sub-steps per bar,
H = 30, risk b = 1, 40,000 paths per cell. The formulas are ported from `f_race` / `f_raceH` (447-482). "EV shown" is
`win·rr − (1 − win)` with `win = pW/(pW + pL)`, as at 2359.

| Target a (R) | σ√H (R) | P(decided ≤ H) | WIN\|dec model / MC | **EV shown** | E[R \| decided] MC | **E[R] all** MC |
|---|---|---|---|---|---|---|
| 0.5 | 1 | 0.86 | 0.690 / 0.686 | +0.03 | +0.03 | −0.01 |
| 2 | 1 | 0.34 | 0.125 / 0.118 | **−0.62** | −0.65 | **+0.00** |
| 3 | 1 | 0.31 | 0.008 / 0.008 | **−0.97** | −0.97 | +0.01 |
| 3 | 2 | 0.72 | 0.164 / 0.163 | **−0.34** | −0.35 | +0.01 |
| 5 | 2 | 0.61 | 0.019 / 0.018 | **−0.89** | −0.89 | +0.03 |
| 5 | 4 | 0.92 | 0.141 / 0.147 | −0.15 | −0.12 | +0.05 |

- The engine's `f_raceH` matches Monte Carlo, so the maths is right.
- The *label* is wrong: the readout is E[R | decided], not the expectancy. The true expectancy is 0 (small positive values
  are sub-step discretisation).
- Far targets look like −0.6R to −1.0R "EV" trades when they are fair bets, and near targets look fair even with drift
  noise added.
- Grade: strong (theory plus simulation).

**B. Is the EDGE z correctly sized? (`ledger_null.py`, 400 synthetic replications per scenario).**
- *Setup:* engine-like ledger mechanics.
  - A random-side, random-distance (0.5-4 ATR) "DOL" that switches with probability 0.08 per bar.
  - One trial per active level; a trial re-opens after it resolves; trade-through within H = 30; 300-bar warm-up; 5,000 bars.
  - pBase is the engine-style online excursion surface blended with the driftless analytic prior (priorM = 30).
- *Scenarios:* constant volatility; stochastic volatility with a 5-minute intraday cycle ("sv"); slow stochastic volatility
  ("sv_slow").
- *Estimators:*
  - **ind**: Σp(1−p).
  - **eng**: the engine's uncentred, booking-keyed 2H blocks.
  - **open**: open-keyed, centred 2H.
  - **hac**: open + lag-1.
  - **wide**: open-keyed, centred 8H.

| Scenario | sd of z: ind / **eng** / open / hac / **wide** | P(z ≥ 2) eng / wide | deff eng / wide |
|---|---|---|---|
| NULL const | 1.02 / **0.96** / 1.00 / 0.97 / 1.06 | 0.003 / 0.007 | 1.13 / 1.07 |
| NULL sv (seasonal) | 1.05 / **0.76** / 0.79 / 0.76 / **1.00** | 0.018 / 0.072 | 1.93 / 1.30 |
| NULL sv_slow | 0.99 / **0.90** / 0.93 / 0.90 / 0.99 | 0.007 / 0.013 | 1.21 / 1.13 |
| ALT sv, +3.3 pp informed picker | mean z 1.70 / **1.21** / 1.29 / 1.23 / **1.59** | **0.100** / **0.302** | 1.97 / 1.23 |

- The engine's z is not anti-conservative at a single look. Under seasonality it is *too conservative* (sd 0.76): 2H blocks
  capture the positive short-lag residual correlation of busy hours but miss the negative long-lag correlation of quiet hours.
- Centred, open-keyed blocks at least a session wide have the right size (sd 0.99-1.06) and **3× the power** on a real
  +3.3 pp edge.
- The mean z under the null sits at ±0.4-0.6. That shift is baseline miscalibration, not variance (next experiment).
- Grade: moderate.

**C. A no-skill picker on real data (`real_placebo.py`).**
- *Setup:* random side, random distance, same ledger. 12 seeds per dataset on 1h and 5m (shared path), plus 76 *independent*
  6,000-bar 1-minute segments.

| Set | Placebo excess (pp) | mean z_eng | P(z ≥ 2) | P(z ≤ −2) |
|---|---|---|---|---|
| GC 1h | **−4.00** | −1.82 | 0 | **0.25** |
| CL 1h | +1.02 | +0.49 | 0 | 0 |
| RTY 1m | −1.94 | −1.00 | 0 | 0.15 |
| YM 1m | −1.79 | −0.88 | 0 | 0.23 |
| NQ 5m | +0.66 | +0.53 | 0.08 | 0 |
| YM 5m | +0.97 | +0.73 | 0.08 | 0 |
| other 13 sets | −1.2 to +0.7 | −0.6 to +0.3 | 0 | ≤ 0.08 |
| **1-min pooled, 76 independent segments** | **−1.11 (sd 1.87)** | sd 0.91 | 0 | P(\|z\| ≥ 2) 0.079 |
| 1-min paired placebo (picker − second picker) | — | **sd 0.96** | — | **P(\|z\| ≥ 2) 0.026** |

- The baseline is off by −4 to +1 pp per dataset. GC 1h has roll gaps, the same corruption sibling quant_pot and calib_ml
  found.
- That shift is the same order as the active ledger's SE (1.4-2.4 pp). On GC 1h *any* picker reads "✕ NO EDGE".
- A paired placebo restores the nominal size.
- Grade: moderate.

**D. Survivorship in ETA and heat (`survivorship.py`).** Random levels at 1/2/3 ATR, both sides, every 3rd bar, H = 30,
strict trade-through. The KM median is the unconditional median of min(T, H+1).

| Set | d (ATR) | P(touch ≤ 30) | **ETA \| hit** (engine) | **true median** | **heat \| hit** (engine) | heat all | heat misses |
|---|---|---|---|---|---|---|---|
| ES 1h | 1 | 0.80 | 5 | 7 | 1.81 | 3.57 | 7.36 |
| ES 1h | 2 | 0.62 | 9 | 19 | 2.18 | 4.68 | 6.79 |
| ES 1h | 3 | 0.45 | 12 | **> 30** | 2.25 | 5.09 | 6.36 |
| ES 5m | 2 | 0.54 | 9 | 25 | 1.87 | 4.26 | 6.40 |
| ES 5m | 3 | 0.39 | 13 | **> 30** | 2.02 | 4.62 | 5.92 |
| NQ 1h | 2 | 0.62 | 9 | 19 | 2.17 | 4.69 | 6.88 |
| CL 5m | 2 | 0.56 | 9 | 23 | 1.90 | 4.49 | 6.72 |
| EURUSD 1h | 2 | 0.59 | 10 | 20 | 1.95 | 4.66 | 6.87 |
| EURUSD 1h | 3 | 0.43 | 13 | **> 30** | 1.90 | 4.97 | 6.35 |

ETA|hit is 2-3× too optimistic and can never say "unlikely within H". Heat|hit is about half the 80th-percentile adverse
excursion of all trials. Grade: moderate (direct measurement, 7 datasets, consistent).

**E. Beta trap (`beta_trap.py`).**
- *Setup:* touch rate at 2 ATR within 30 bars for an "always long" picker vs its mirror (same distance, opposite side, same
  bar). The SE uses 8H blocks.

| Set | always-long − mirror (pp) |
|---|---|
| GC 1h | **+10.8 ± 6.2** |
| EURUSD 1h | **+8.3 ± 3.9** (z ≈ 2.1) |
| CL 1h | +5.4 ± 5.0 |
| RTY 1h | +4.4 ± 3.8 |
| ES 1h | +3.5 ± 4.2 |
| 5m sets | −3.7 to +4.2 |

- A drift-free or regime-free comparison credits a long bias with "edge" in trending samples.
- The engine's regime-split surface (S[r] by HTF bias, 1059-1062, 1287) removes this by construction (present, good).
- Grade: moderate.

**F. Mirror control vs clock-driven miscalibration (`mirror_control.py`, `mirror_seeds.py`).**
- *Setup:* no-skill pickers that only fire in a clock window (random side and distance, 5m data). Window "busy" =
  13:30-16:00 and "quiet" = 00:00-07:00 in the data's timestamps; 16 seeds each.
- *Mirror-controlled residual:* `(y − pBase) − (y_mirror − pBase_mirror)`.

| Set / window | engine-style excess, mean z | mirror-controlled excess, mean z |
|---|---|---|
| ES busy | +3.14 pp, z̄ **+1.02** | −1.16 pp, z̄ −0.25 |
| ES quiet | −2.26 pp, z̄ **−1.20** | −0.64 pp, z̄ −0.19 |
| NQ quiet | −2.02 pp, z̄ **−1.04** | −0.53 pp, z̄ −0.17 |
| GC quiet | −3.34 pp, z̄ **−1.57** | +1.67 pp, z̄ +0.50 |
| 6 symbols × 2 windows, single seed | busy +2.04 pp (z̄ +0.61); quiet −1.97 pp (z̄ −1.10) | busy +0.24 pp (z̄ +0.04); quiet −0.06 pp (z̄ −0.06) |
| **all 12 cells, 16 seeds** | mean \|bias z\| **0.69** | mean \|bias z\| **0.24** |

The spread of z is similar: sd 0.69-1.43 for the mirror vs 0.78-1.27 for the engine style. Grade: moderate.

**G. Multiple testing and power (`mt_power.py`).**
- *One chart, fixed look:* P(z ≥ 2) = 2.3%.
- *Across charts:* 10 charts → 21% (fixed look) or 80% (with peeking at the sibling's 15% per chart). 30 charts → 50% or 99%.
- *Best of k settings:* k = 10 gives E[max z] 1.53 and P ≥ 2 of 20%; k = 45 gives 2.21 and 64%; k = 100 gives 2.51 and 90%.
- *Per-family rows (5 rows, fixed look):* P(any z ≥ 2) = 11%.
- *MDE at 80% power, active-DOL ledger:*

  | SE per 5,000 bars | 5,000 bars: fixed / anytime | 10,000 bars: fixed / anytime | 20,000 bars: fixed / anytime |
  |---|---|---|---|
  | 1.4 pp | 3.9 / 5.5 pp | 2.8 / 3.9 pp | 2.0 / 2.8 pp |
  | 2.4 pp | 6.7 / 9.5 pp | 4.8 / 6.7 pp | 3.4 / 4.7 pp |

- *Candidate (shadow) ledger (SE 0.9-1.9 pp):* anytime MDE 3.5-7.5 pp at 5,000 bars.

---

## 3. Engine gap analysis (`baseline_v2.pine`)

### 3.1 Ledger and statistics audit

| Item | Lines | Verdict | What the engine does / what is wrong |
|---|---|---|---|
| Leak-freeness | 1426-1431 (open at close), 1549-1557 (grade on later bars, `bar_index > t.bar0`, before sweeps delete levels), 1527-1532 (surface from completed windows: `fwdHi = ta.highest(high, H)` ends on this bar, measured from `close[H]`, regime `htfBias[H]`), 2038 (`barstate.isconfirmed` block) | **correct** | No look-ahead found (agrees with sibling calib_ml). MTF reads use `[1]`-offset + `lookahead_on` and `f_tfSafe`. |
| Hit rules | 623-624, 1436 | correct | Strict trade-through for pools, touch for arrays. The surface uses ≥ with linear interpolation (1273-1278): negligible mismatch. |
| Random-level baseline | 1313-1322, 1059-1062, 1284-1300 | **present, good** | Distance-matched, direction × HTF-regime split, prequential, analytic driftless prior (μ = 0 in `f_potBase`). The regime split absorbs trend beta (§2.3 E). |
| Baseline calibration check | — | **missing** | Nothing detects that the baseline itself is off on this chart (−4 to +1 pp on real data, −2 to +3 pp by clock window; §2.3 C, F). No placebo or mirror control. |
| Cluster variance | 1463-1469 (`cluSt`), 2385 | **partial / wrong** | Residuals are uncentred (`y − pBase`), blocks are keyed by *booking* bar, and the 2H width is shorter than a session. Under intraday seasonality: z sd 0.76 under the null (conservative), detection of a +3.3 pp edge 10% vs 30% with centred 8H blocks (§2.3 B). Not anti-conservative at one look. |
| Wilson CI with design effect | 2385-2387 | partial | Kish-style `k/deff, n/deff`. Inherits the variance issue. It is a fixed-time interval, not anytime-valid. |
| Verdict thresholds | 2390-2391 | **wrong** | `z ≥ 2 → ✓ EDGE`, `z ≥ 1 → ~ WEAK`, else `✕ NO EDGE`. Problems: (i) peeking, 10-20% false "✓ EDGE" (sibling calib_ml); (ii) "✕ NO EDGE" is printed for *not measurable* (MDE 5.5-9.5 pp); (iii) no negative verdict distinct from "not proven"; (iv) n ≥ 20 is far too few (n_eff matters). |
| MDE / power | — | **missing** | Users cannot tell "no edge" from "can't tell". |
| Headline hit rate | 2392-2394 | partial | DOL HIT % and the Wilson CI are shown without the expected rate in the same row. EDGE pp is on the next row (good). |
| Rolling L50 | 1478-1480, 2395-2396 | **wrong (base-rate trap)** | The last-50 *raw* hit rate moves with target distance. It should be the last-50 *excess* (y − pBase). |
| BARS→HIT | 1476-1477, 2403-2407 | partial | avg/med over hits only. Acceptable only if labelled "given hit". |
| ETA\|hit in HUD | 2116-2127 | **wrong (survivorship)** | Median bars-to-hit of past hits within ±0.5 ATR: 2-3× too optimistic, never "> H" (§2.3 D). |
| heat | 1481-1483 (`maeHit` only when y = 1), 2404 | **wrong (survivorship)** | p80 adverse excursion of hits: 1.6-2.3 ATR vs 3.2-5.1 ATR over all trials (§2.3 D). `stMae` (1475) accumulates all trials but is never displayed. |
| EV in HUD | 2358-2363, from `f_invalidation` 1343-1364 and `f_raceAdj` 1367-1371 | **wrong** | (i) E[R \| decided] labelled EV: −0.34 to −0.97R for fair far targets (§2.3 A). (ii) Drift `potMu·side` in `f_raceH` adds noise (quant_pot: drift is the largest error source). (iii) Under no drift the model EV ≡ 0, so any nonzero value is bias or drift. |
| WIN≤H | 2362, 1364 | partial | A defined quantity (decided-race win rate), but shown without its geometric expectation b/(a+b), so a 70% WIN on near targets looks like skill. |
| Race R / PF | 1457-1458, 1489-1498, 2419-2425 | **present, under-used** | `rOut` is conservative (target paid at the edge, stop gaps at the open, MTM at H). Under a martingale E[R] ≤ 0, so avg R is a *model-free* edge statistic. But it is shown only in Full view, with no uncertainty, no beta adjustment, no verdict. |
| `f_raceAdj` | 1367-1371 | partial | Shifts toward observed wins relative to the *drift* model p (`pRace` from `f_invalidation`). Its reference should be drift-free geometry. |
| Per-family rows | 2410-2418 | partial | Hit % with no expected rate or interval; 5 rows → 11% chance of a spurious standout at one look. |
| Adaptive calibration `f_calMult` | 1376-1382, 1935-1944 | **wrong** (sibling calib_ml) | Noise-chasing: ≥ 10% off under the null in 47-66% of families; bandit feedback; ignores the design effect. Should be gated by the same honest test. |
| Shown vs graded | 2038 vs 2068 | partial | The ledger grades `activeLv` whether or not the PoT filter shows it. With `minPoT > 0` the accuracy panel includes targets the user never saw. |
| Forward / out-of-sample | — | **missing** | No distinction between history trials (in-sample to the settings) and realtime trials. |
| Swept PoT | 2067 | minor | Shows "95%" after the target is touched. It should read "HIT". |
| Audit trail | 2444 (`DOL Price` plot is data-window only), ghosts off by default (171) | partial | Users cannot visually audit past targets, including the abandoned ones, so cherry-picking from memory is easy. |
| Claims wording | README §intro, "Probability of Touch", 141-142 tooltips | partial | "Most likely drawing to next"; PoT presented as the level's probability (it is a distance/regime probability); `minPoT` presented as quality (it filters by distance). |

### 3.2 Scoring and selection vs the evidence

| Component | Lines | Evidence verdict | Status |
|---|---|---|---|
| Proximity (25): linear + reachability + taper | 662-667 | Geometry *is* the signal; expected reach d·P(d) is the principled form (sibling calib_ml CAL-5). Reach uses the drift `mu·side` | partial |
| Freshness (10): liquidity matures then decays | 668-673 | No evidence either way. S/R memory decays over hours (C16), the opposite of "maturing" | unsupported |
| Confluence (15) | 674-680 | Key/confluent levels hit −0.18 to −0.25 logit *less* than random | contradicted |
| Density: EQ count | 682 | +0.08 / +0.29 logit | weak support |
| Density: source tier (1.2·tier, PW > PD > … > chart) | 506-516, 682 | External pools −0.14 / −0.27 logit | contradicted |
| Density: tests (+0.35 per test, up to 6) | 652-656, 682 | Prior bounces → more bounce, less trade-through in the short run (C16) | contradicted (sign) |
| Density: coil, inducement | 893-903, 683 | No published test | untested |
| Draw (30) + draw-side-first selection + counter-draw ×0.5 | 691-693, 1891-1895, 1975, 2000-2012 | D-first −9 to −12 pp first-touch vs geometry; ER-gated D recovers it (quant_regime) | contradicted as default |
| Killzone affinity ×1.05-1.20 | 597-602, 1941 | Clock-matched null within ±3 pp; one exception (Asia two-sided raid on index futures) | unsupported (fixed) |
| Inner-pool penalty ×0.70 | 684-685 | A design choice: "destination" semantics. Fine if the claim is "destination" | n/a (wording) |
| Origin lockout ×0.25 for fresh arrays | 689-690 | Sensible: price sits on its origin | n/a |
| Volume-profile path cost ×1.10 / ×0.85 | 1945-1947 | Untested here (see sibling orderflow_micro / amt_profile) | untested |
| Adaptive calibration | 1376-1382 | Noise under the null (sibling calib_ml) | wrong |
| PoT drift (`driftW 0.5`) | 916-917, 665, 1304, 1361-1363 | Hurts log-loss 1.2-7.1% in every regime (quant_pot, quant_regime) | wrong |

### 3.3 Concept status summary

| Concept | Status | Where |
|---|---|---|
| Distance-matched random-level baseline | present | 1313-1322 |
| Regime-split baseline (beta control) | present | 1059-1062, 1287 |
| Leak-free prequential ledger | present | 1426-1500, 1549-1557 |
| Overlap-aware variance | partial | 1463-1469 (uncentred, booking-keyed, 2H) |
| Placebo / mirror control of the baseline | missing | — |
| Anytime-valid verdict | missing (wrong) | 2390 |
| Minimum detectable effect | missing | — |
| Survivorship-free time-to-touch | wrong | 2116-2127 |
| Survivorship-free adverse excursion | wrong | 1481-1483, 2404 |
| Martingale-consistent EV | wrong | 2359 |
| Model-free R-expectancy test | partial | 1457-1498, 2419-2425 |
| Geometric reference for WIN% | missing | 2362 |
| Strong naive baselines (nearest / max-reach / trend-side) | missing | — |
| Forward (realtime-only) ledger | missing | — |
| Multiple-comparison discipline | missing | 2410-2418 |
| Audit trail of all past targets | partial | 2444 |
| Honest claims and wording | partial | README, tooltips |
| ICT modifiers as measured, not assumed | wrong (hard-coded) | 597-602, 674-693 |

---

## 4. Proposals (best first; maximum 10)

Common Pine v6 rules for every sketch:
- All state changes run inside the existing `if barstate.isconfirmed and not na(atr) and atr > 0` block (1518), so nothing
  repaints.
- Functions cannot reassign global scalars, so running statistics live in `var array<float>`, as `stN` and `raceSt` do.
- Helpers are declared after the arrays they use (STATE HELPERS, after `f_book` at 1500), and before the panel (2289).
- `H` is the simple int at 305.
- New `Trial` fields go at the end of the type (375-395) with defaults, so existing `Trial.new` calls keep compiling.

Sibling proposals this report endorses without repeating:
- QPOT-01: remove the drift.
- CAL-1: an overlap-aware, gated family multiplier.
- CAL-2: a normal-mixture confidence-sequence verdict. SKEP-2/3/4 supply its variance and its control.
- CAL-3: a candidate ledger. SKEP-5 is its paired league-table extension.
- Quant_regime: ER-gated D.

---

### SKEP-1 (P1, effort S) · Survivorship-free and martingale-consistent readouts

**Why.** Four readouts are biased by construction (§2.3 A, D):
- ETA is 2-3× too optimistic and never "> H";
- heat is about ½ of the real 80th-percentile adverse excursion;
- EV shows −0.3 to −1.0R for fair targets;
- L50 tracks distance.

These are the numbers a trader acts on, so the fix is pure honesty, and cheap.

**Algorithm.**
1. *Time-to-touch histogram by distance bucket.* Every ledger record is followed until it hits or reaches H bars, so there
   is no early censoring and the Kaplan-Meier curve equals the empirical CDF of `min(T, H+1)`. Report the unconditional
   median, or "> H" when P(T ≤ H) < 0.5, together with P(T ≤ H).
2. *Heat over all records.* Keep the hits-only value only as a tooltip.
3. *EV.* Delete the model EV. Under the driftless model it is identically 0, so the old non-zero values came from drift and
   conditioning. Show the ledger's measured average R with its band instead (SKEP-4). Show WIN≤H next to its drift-free
   geometric expectation.
4. *L50* becomes the last-50 excess `Σ(y − pBase)/50`.
5. *Hit row* prints "hit / exp".
6. *Touched target* reads "PoT: HIT", not 95%.

**Pine v6 sketch.**

State (after 1079):
```pine
// time-to-touch counts per distance bucket (0-1, 1-2, 2-3, 3+ ATR); slot H+1 = not touched within H
var array<int>   ttDist = array.new<int>(4 * (H + 2), 0)
var array<float> maeAll = array.new<float>()
var array<float> roll50x = array.new<float>()     // replaces roll50 (int) with residuals
```

In `f_book` (1461-1500), after `int y = …`:
```pine
    int bkt  = math.min(3, int(math.floor(t.d0)))
    int slot = y == 1 ? math.min(t.bars, H) : H + 1
    ttDist.set(bkt * (H + 2) + slot, ttDist.get(bkt * (H + 2) + slot) + 1)
    maeAll.push(t.mae)
    if maeAll.size() > 300
        maeAll.shift()
    roll50x.push(y - t.pBase)
    if roll50x.size() > 50
        roll50x.shift()
```

Helper (after `f_book`):
```pine
// Unconditional time-to-touch for a distance bucket: [median bars (na = beyond H), P(touch ≤ H), n]
f_ttStats(int bkt) =>
    int   base = bkt * (H + 2)
    float n    = 0.0
    for j = 1 to H + 1
        n += ttDist.get(base + j)
    float cum = 0.0
    float med = na
    for j = 1 to H
        cum += ttDist.get(base + j)
        if na(med) and n > 0 and cum >= 0.5 * n
            med := j
    [med, n > 0 ? cum / n : na, n]
```

Rendering:
- Replace the `dHit` loop (2120-2127):
  ```pine
  [eMed, eP, eN] = f_ttStats(math.min(3, int(math.floor(dNow))))
  ```
  HUD text: `eN < 20 ? "ETA —" : na(eMed) ? "ETA >" + str.tostring(H) + "b · " + str.tostring(100 * eP, "0") + "%" : "ETA " + str.tostring(eMed, "0") + "b · " + str.tostring(100 * eP, "0") + "%"`.
- Panel 2404: `float p80Mae = maeAll.size() >= 20 ? maeAll.percentile_linear_interpolation(80) : na`, labelled "heat p80 (all)".
- Hit row 2393: `str.tostring(100.0 * kA / nA, "0.0") + "% / exp " + str.tostring(100.0 * stPE.get(4) / nA, "0.0") + "%"`.
- L50 2395: `roll50x.size() > 0 ? 100.0 * roll50x.sum() / roll50x.size() : na`, shown as `f_signed(x, "0") + "pp L50"`.
- R:R row 2358-2363: drop `tEV`. Show `"WIN≤H " + win% + " · geo " + geo%`, where
  `geo = pW0 / (pW0 + pL0)`, `pW0 = f_raceH(d, risk, sg, 0.0, H)`, `pL0 = f_raceH(risk, d, sg, 0.0, H)`.
  The fourth cell shows SKEP-4's ledger R̄.
- 2067: keep `activePoT := sweptNow ? 1.0 : …` for the filter, and print "HIT" in the label when `sweptNow`.

**Ledger measurability.** The readouts *are* ledger statistics. Validation: the displayed P(T ≤ H) for a bucket must equal
that bucket's hit fraction, and the displayed ETA must agree with `survivorship.py` on the same data (for example ES 1h,
2 ATR: 19 bars).

**Evidence.** Strong (the theory of censoring and optional stopping) and moderate (this study's measurements, 7 datasets).

**Risk.** The numbers look worse, though more truthful: "ETA > 30b" for far targets. Users may perceive a downgrade. The
tooltip should say why.

**Effort.** S (about 40 lines).

---

### SKEP-2 (P1, effort M) · Mirror-controlled EDGE with a baseline check and a minimum detectable edge

**Why.**
- The edge statistic is only as good as the baseline. On real data the baseline is off by −4 to +1 pp per chart and by
  ±2-3 pp per clock window (§2.3 C, F). That is as large as the edges the evidence allows (2-5 pp) and as the ledger's SE.
- A mirror control removes the miscalibration that is common to both sides (clock, volatility regime, roll gaps): bias
  |z| 0.69 → 0.24 in §2.3 F. The regime-split baseline still removes trend beta.
- The test then measures exactly the claim "this choice beats a level at the same distance".

**Algorithm.**
- *Mirror record.* For each DOL trial opened at bar t (step 20), open a *mirror* record: the level at the same ATR distance
  `d0` on the opposite side, with the same hit rule (trade-through if the DOL is liquidity, touch if it is an array), the
  same H and its own `pBase = f_potBase(d, −side)`.
- *Residuals.* `r = y − pBase` for the DOL and `rm = y_m − pBase_m` for its mirror. The paired residual is `Δ = r − rm`.
- *Blocks.* Keyed by the DOL's *open* bar (SKEP-3): `D_g = Σ Δ`, `N_g = count`. The block holding the last H bars is ignored
  until its records resolve.
- *Statistics.*
  - Mirror edge `Δ̄ = ΣD/N`.
  - Variance `V = G/(G−1) Σ_g (D_g − N_g·Δ̄)²`.
  - SE `= √V / N`.
- *Verdict.* Anytime-valid on the sum `S = ΣΔ` with the CAL-2 boundary `b(V) = √((V+ρ)·ln((V+ρ)/(ρα²)))`, ρ = 10, α = 0.05:
  - `S ≥ b` → "✓ BEATS MIRROR";
  - `S ≤ −b` → "✕ WORSE THAN MIRROR";
  - otherwise "~ NOT PROVEN (MDE x pp)", with `MDE = (b(V)/√V + 0.84)·SE`;
  - "CALIBRATING" while `n_eff = N·Σp(1−p)/V < 30`.
- *Baseline check.* The pair average `½ Σ (r + rm) / N` estimates the baseline's own bias, plus half of any pool-specific
  magnet effect. When `|bias| > 2·SE_bias` and `|bias| > 2 pp`, show "⚠ BASELINE OFF x pp (data gaps / rolls?)", and print
  the one-sample EDGE verdict as "UNRELIABLE" (the mirror verdict stays valid).

**Pine v6 sketch.**

Type (375-395): append
```pine
    int   role   = 0      // 0 DOL · 1 mirror
```

State (after 1079):
```pine
int  blkW  = math.max(2 * H, math.min(int(86400.0 / chartS), int(calcBars / 30)))   // SKEP-3 block width
var array<float> blkE = array.new<float>()   // Σ (y − pBase) of DOL records, by open block
var array<float> blkD = array.new<float>()   // Σ (r − rm) paired, by open block
var array<float> blkN = array.new<float>()   // DOL record count, by open block
var array<float> blkP = array.new<float>()   // Σ (r + rm) pair sums (baseline check)
var array<float> blkR = array.new<float>()   // Σ beta-adjusted R (SKEP-4)
```

Helper (STATE HELPERS, before `f_book`):
```pine
f_blk(int b0) =>
    int id = math.max(0, int(math.floor((b0 - math.max(0, last_bar_index - calcBars)) / blkW)))
    while blkN.size() <= id
        blkE.push(0.0)
        blkD.push(0.0)
        blkN.push(0.0)
        blkP.push(0.0)
        blkR.push(0.0)
    id
```

In `f_book` (replacing the `cluSt` block at 1463-1469):
```pine
    int   g = f_blk(t.bar0)
    float r = y - t.pBase
    if t.role == 0
        blkE.set(g, blkE.get(g) + r)
        blkD.set(g, blkD.get(g) + r)
        blkP.set(g, blkP.get(g) + r)
        blkN.set(g, blkN.get(g) + 1.0)
    else
        blkD.set(g, blkD.get(g) - r)
        blkP.set(g, blkP.get(g) + r)
```
Guard the existing stats (`stN/stK/stPE/stPV/stMae`, `roll50`, `ttHit`, `raceSt`) with `if t.role == 0`, so the mirror never
pollutes them.

Opening (step 20, 2044-2045):
```pine
            if not has and openT.size() < math.max(128, 2 * H + 2)
                Trial tD = f_openTrial(activeLv)
                openT.push(tD)
                float dm = tD.d0 * atr
                openT.push(Trial.new(lvId = -activeLv.id - 1, grp = tD.grp, side = -tD.side, edge = close - tD.side * dm,
                  inv = close + tD.side * atr, risk = atr, entry = close, atr0 = atr, bar0 = bar_index,
                  pBase = f_potBase(dm, -tD.side), pRace = 0.5, rr0 = 1.0, d0 = tD.d0, liq = tD.liq, role = 1))
```
`f_step` works unchanged. The mirror's `inv`, `risk` and race fields are unused, because `f_book` skips race stats for role 1.

Centred cluster variance helper:
```pine
// G/(G-1) · Σ_g (X_g − N_g·m)², blocks < gMax only (records resolved)
f_cluVar(array<float> X, int gMax) =>
    float sx = 0.0
    float sn = 0.0
    for g = 0 to math.min(gMax, X.size()) - 1
        sx += X.get(g)
        sn += blkN.get(g)
    float m = sn > 0 ? sx / sn : 0.0
    float v = 0.0
    int   G = 0
    for g = 0 to math.min(gMax, X.size()) - 1
        float ng = blkN.get(g)
        if ng > 0
            v += math.pow(X.get(g) - ng * m, 2)
            G += 1
    [sx, sn, G > 1 ? v * G / (G - 1) : na]
```
Guard the loops with `if X.size() > 0 and gMax > 0`. Pine `for` with an end below the start iterates downward, so the guard
matters.

Panel (2383-2401): `int gMax = f_blk(bar_index - H)`, then
`[sD, nD, vD] = f_cluVar(blkD, gMax)` and `[sP, nP, vP] = f_cluVar(blkP, gMax)`. Then the bound, verdict and MDE as above.
New rows:
- "EDGE·MIRROR +2.1pp ±3.8 · MDE 5.5pp · ~ NOT PROVEN"
- "BASELINE −0.4pp ✓" or "⚠ BASELINE OFF −4.0pp"

**Cost.** It doubles the open records (still ≤ 128; each `f_step` is O(1)). The panel loops are O(G ≤ 333) on the last bar
only.

**Ledger measurability.** This is the measurement layer. Acceptance test: on `mirror_seeds.py`-style clock-timed placebo
pickers, mean |z| stays ≤ 0.3. With the engine's real selections, report the mirror edge per symbol.

**Evidence.** Moderate (this study's real-data tests: 4 symbols × 3 windows × 16 seeds, plus 76 independent 1-minute
segments) and strong (the theory of paired designs and confidence sequences).

**Risk.**
- The mirror is a plain level, so a *real* pool magnet effect is credited as edge. That is intended: it is "beats a level at
  the same distance".
- Side-asymmetric miscalibration (skew) is not cancelled. The regime split handles the trend part.
- The variance is slightly larger than the one-sample test. It is worth it, because the bias otherwise dominates.

**Effort.** M (about 90 lines).

---

### SKEP-3 (P1, effort S) · Correct the overlap variance: open-keyed, centred, session-wide blocks

**Why.**
- `cluSt` (1463-1469) has three problems: residuals are uncentred, blocks are keyed by booking bar, and blocks are 2H wide.
- Under intraday seasonality it overstates the variance (z sd 0.76 under the null). It costs power: a +3.3 pp edge is
  detected 10% of the time vs 30% (§2.3 B).
- It also feeds the Wilson design effect, and sibling CAL-1's n_eff.
- Centred, open-keyed blocks at least a session wide are correctly sized in every scenario tested (sd 0.99-1.06).

**Algorithm.**
- Block width `W = max(2H, min(barsPerDay, calcBars/30))`. This keeps G ≥ 30 blocks and spans the daily seasonality when
  possible:
  - 1-minute: W = 166;
  - 5-minute: 166 (14 h);
  - 1-hour: 60;
  - daily: 2H.
- One-sample EDGE: `S = ΣE_g`, `V = G/(G−1) Σ (E_g − N_g·ē)²`, `deff = V/Σp(1−p)`.
- When SKEP-2 is not adopted, still switch the one-sample test to this V.

**Pine v6 sketch.** Uses `blkW`, `f_blk`, `blkE` and `f_cluVar` from SKEP-2 (the minimal subset if SKEP-2 is deferred).
Remove `cluSt` (1077, 1463-1469). In the panel (2384-2389):
```pine
            int gMax = f_blk(bar_index - H)
            [sE, nE, vE] = f_cluVar(blkE, gMax)
            float vInd = stPV.get(4)
            float vEdge = na(vE) ? vInd : math.max(vE, 0.25 * vInd)   // floor guards tiny G
            float deff  = vInd > 0 ? vEdge / vInd : 1.0
```
Sibling CAL-1's `f_calMult` should use `n/deff` with this deff.

**Ledger measurability.** Rerun `ledger_null.py` with `blkW`. The null z sd must be 0.9-1.1 in all three scenarios.

**Evidence.** Moderate (this study's simulation) and strong (cluster-robust inference theory).

**Risk.** With few blocks (G < 15, very short histories) the variance is noisy. The 0.25·vInd floor and the CALIBRATING gate
handle it.

**Effort.** S (about 25 lines; shared with SKEP-2).

---

### SKEP-4 (P1, effort S) · Model-free R-expectancy test (martingale null), with a beta adjustment

**Why.**
- For a trader the question is "do these targets pay", not "are they touched".
- Under any martingale, every target/stop/time-out rule has E[R] = 0 (optional stopping). The ledger's `rOut` is
  conservative (target paid at the edge, gaps through the stop at the open), so the null is E[R] ≤ 0.
- That makes avg R an edge test with **no baseline model at all**. It is immune to baseline miscalibration and to the
  decided-race conditioning that breaks the HUD EV.
- The only nuisance is drift (beta). Wald's identity removes it: `E[R] = side·μ·E[τ]/risk`.
- The engine already computes `rOut` (1457-1458) but shows it only in Full view, without uncertainty.

**Algorithm.**
- Prequential drift: `μ̂_t` = the running mean of `close − close[1]` over all confirmed bars up to the trial's open.
- For each DOL record: `R_adj = rOut − side·μ̂·τ/risk`, where τ = the bars until the race resolved (or H).
- Per open-block sums `Σ R_adj` go to `blkR`. Then `R̄ = ΣR/N`, `V_R = G/(G−1) Σ (R_g − N_g R̄)²`, and SE.
- Verdict with the same anytime boundary applied to `S = ΣR_adj`, `V = V_R`. This is sub-Gaussian approximate: R is bounded
  below by gaps and above by `rr0`.
- Display, Compact view: "R̄ +0.06R ±0.11 · PF 1.12 · long 62%". The long share discloses directional tilt.
- `WIN≤H` is shown next to the drift-free geometric `pW0/(pW0+pL0)` (SKEP-1).
- `pRace` stored at open becomes drift-free, so `f_raceAdj` shifts relative to geometry, not to a drift model.

**Pine v6 sketch.**
- `Trial`: append `float mu0 = 0.0` and `int rBars = 0`.
- State: `var array<float> driftSt = array.from(0.0, 0.0)` (Σ Δclose, n), updated at the top of the engine block:
  ```pine
  driftSt.set(0, driftSt.get(0) + close - nz(close[1], close))
  driftSt.set(1, driftSt.get(1) + 1.0)
  ```
  `close[1]` is read inside the `if` block. That is fine: history referencing of a built-in series has no consistency issue.
- `f_openTrial` (1426-1431): `mu0 = driftSt.get(1) > 0 ? driftSt.get(0) / driftSt.get(1) : 0.0`, and
  `pRace = f_raceGeo(d, risk)`, where `f_raceGeo` is `f_invalidation`'s race computed with `m = 0`.
- `f_step` (1444-1452): when `t.race` first becomes non-zero, `t.rBars := t.bars`. At expiry with `race == 0`,
  `t.rBars := t.bars`.
- `f_book`, for role 0:
  ```pine
  float rAdj = t.rOut - t.side * t.mu0 * t.rBars / math.max(t.risk, syminfo.mintick)
  blkR.set(g, blkR.get(g) + rAdj)
  ```
- Panel: `[sR, nR, vR] = f_cluVar(blkR, gMax)`, then R̄ and its band. Move the RACE row into Compact view.

**Ledger measurability.** Direct. Acceptance: on synthetic driftless data (adapt `ledger_null.py`), R̄ is within ±2 SE in
95% of runs; on the always-long picker of §2.3 E, R_adj ≈ 0 while the raw R̄ > 0.

**Evidence.**
- Strong: the optional stopping theorem and Wald's identity.
- Moderate: races are near-martingale on real data (sibling quant_pot: b/(a+b) within 0.4-1.2 pp).

**Risk.**
- Intrabar ordering (1440-1441) misclassifies some same-bar target/stop events. It is about 80% accurate and conservative
  on gaps.
- R depends on the invalidation rule (nearest opposing pool), which is a design choice. That is acceptable, because the
  test is about *this* trade definition.

**Effort.** S (about 35 lines).

---

### SKEP-5 (P2, effort M) · Strong-baseline league table: the DOL must beat naive selectors on the same bars

**Why.**
- Beating a *random* level is a low bar. The engine's selection should beat the naive selectors a trader could use without
  it.
- Sibling calib_ml found:
  - every picker's realised hit rate equals its baseline;
  - pickers differ in *what they deliver*: max-reach d·PoT 1.10-1.43 ATR per target, hand score 0.86-1.09, nearest 0.66-0.93.
- Sibling quant_regime found draw-first selection loses 9-12 pp of first-touch accuracy to geometry.
- Without a head-to-head, a "✓ EDGE" over random says nothing about whether the scoring adds value over "take the nearest
  pool".

**Algorithm.** Each time a DOL record opens (step 20), open shadow records on the *same bar* for three naive selectors,
choosing among the current scored pool with `dA ≥ minDistATR` and `dA ≤ maxATR`:
- **NEAREST:** the smallest distance, either side.
- **GEO:** the largest `dA · f_potBase(d, side)`, i.e. the most expected ATR delivered.
- **TREND:** the nearest on the `htfBias` side (skipped when `htfBias == 0`).

Each shadow gets its own invalidation via `f_invalidation` and a mirror (optional). For each role, accumulate per open block:
- excess `Σ(y − pBase)`;
- `Σ R_adj`;
- ATR delivered `Σ y·d0`.

Paired differences `DOL − role` use the same blocks (same open bar) and the SKEP-3 variance, so the comparison is powerful:
shared-path noise cancels.

Full-view rows, for example:
- "vs NEAREST Δexc +0.4pp ±2.1 · ΔR +0.03 ±0.08 · ATR del 1.02 vs 0.81";
- the same for GEO and TREND;
- a "BEST" marker on the role with the highest R̄ (only when it beats the DOL beyond the anytime bound).

**Pine v6 sketch.**
- `Trial.role`: 2 NEAREST, 3 GEO, 4 TREND.
- One pass over `pool` in step 20 (O(pool) once per opening) picks the three indices. Then
  `openT.push(f_openTrial(pool.get(i)))` with `role` set, and `lvId = -1000000 - role` so the `has` check (2040-2043) ignores
  them.
- Cap: `openT.size() < 256`.
- Per-role block arrays: `array<float> blkRole = array.new<float>(3 * 4 * nBlocks)`, or simpler, three extra
  `blkD_k`/`blkR_k` arrays grown in `f_blk`.
- `f_book` routes by role, and skips the main stats for roles ≥ 1.

**Ledger measurability.** Yes. This *is* an A/B harness for any scoring change: run the current score as role 0 and a
candidate score (for example sibling CAL-5's expected-reach objective or the ER-gated D) as a shadow, then switch defaults
only when the shadow wins beyond the bound across many charts.

**Evidence.** Moderate (sibling replicas: picker hit rates equal baselines; nearest vs max-reach delivery gap 0.4-0.5 ATR
per target) and strong (theory of paired comparisons).

**Risk.** CPU: three extra `f_invalidation` calls per opening (about 1 per H bars), which is negligible. The panel gets
longer, so keep it in Full view only. CAL-3 (candidate ledger) overlaps: implement one shared "probe/role" mechanism.

**Effort.** M (about 80 lines).

---

### SKEP-6 (P2, effort S-M) · Null-default modifiers: unsupported ICT multipliers start neutral and must earn weight

**Why.**
- Several hard-coded modifiers assert effects the evidence contradicts or never found (§3.2):
  - killzone affinities ×1.05-1.20 (597-602);
  - tier bonus in density (682);
  - tests counted as magnitude (682);
  - confluence weight 15 (674-680);
  - drift in PoT/reach (665, 1304, 1361-1363);
  - unconditional draw-side-first selection (1975).
- Each one moves scores by more than the 4-point hysteresis, so each is a source of target switches with no measured
  benefit.
- The skeptic's principle: *the default is the null*. A feature gets weight when the ledger, on this chart, shows it helps.

**Algorithm.** Defaults to change, each kept as a user option (so no feature is lost):

| Input / code | Current | Null default | Evidence |
|---|---|---|---|
| `driftW` (146) | 0.5 | **0.0** | quant_pot, quant_regime: drift hurts log-loss 1.2-7.1% |
| `f_kzAff` (1941) | applied | behind a new `useKzAff = false` | session_stats: within ±3 pp of the clock null |
| tests term `0.35·min(tests,6)` (682) | + | **0** (or negative, learned) | Garzarelli 2014; Chung & Bellotti 2021 |
| tier term `1.2·tier` (682) | + | **0.4·tier** | calib_ml: external pools −0.14 / −0.27 logit |
| `wConf` (104) | 15 | **5** | calib_ml: −0.18 / −0.25 logit |
| `wDraw` + D gate (106, 121) | 30, gate 0.35 | 30, **ER-gated** per quant_regime | D-first −9 to −12 pp |

Then measure: SKEP-5 runs the *old* hand score as a shadow role. The release notes report the per-chart league results, and
the defaults stay null unless the old score wins beyond the anytime bound on most charts.

**Pine v6 sketch.**
- Input default edits (lines 104, 146).
- `bool useKzAff = input.bool(false, "Session Affinity (unproven)", group = G_FLOW, tooltip = "…")`, and at 1941
  `lv.mult *= useKzAff ? f_kzAff(kz, lv.src) : 1.0`.
- Two new inputs `wTests = 0.0` and `wTier = 0.4` replacing the literals at 682.
- The ER gate comes from sibling quant_regime's spec: `ER20 ≥ 0.40` and `sign(D) = sign(sER)`, else `dirSide = 0`.
- "Old score" shadow: compute `scoreOld` in `evaluate` alongside `score` (a second weighted sum with the old constants,
  O(1)), and select the role-5 shadow by `scoreOld`.

**Ledger measurability.** Yes, via SKEP-5 (old vs new score as paired roles) and SKEP-2 (mirror edge per variant).

**Evidence.** Moderate (5 sibling studies with consistent signs) and strong (Osler / Garzarelli on S/R memory).

**Risk.**
- It changes which target shows, and the brief says "do not undo decisions without strong evidence" (draw-side first).
  Mitigation: keep draw-side first, but gate it by efficiency, which keeps the trader-facing "draw follows the trend" where
  it is true (quant_regime: geometry already agrees with the trend 76-82% in efficient trends).
- The reference product advertises session confluence. Keep it available as an option.

**Effort.** S-M (about 30 lines plus the shadow role).

---

### SKEP-7 (P2, effort S) · Forward-only sub-ledger and in-sample disclosure

**Why.**
- Every historical trial is in-sample with respect to the settings: the user tuned them looking at this chart, and the
  developer tuned the defaults on charts.
- With 45 tries, the best setting has E[max z] = 2.2 under the null (§2.3 G).
- The only out-of-sample evidence an on-chart ledger can produce is trials opened *after* the script was loaded with fixed
  settings, i.e. on realtime bars. Changing any input recompiles and resets them, which is exactly the right honesty property.

**Algorithm.**
- `fwd = not barstate.ishistory` at trial open. Keep separate `[n, k, Σp, ΣR_adj]` stats for forward DOL records.
- Show "FORWARD n 9 · hit 56% / exp 51% · R̄ +0.2" or "FORWARD — waiting for live bars".
- Count non-default key inputs: "IN-SAMPLE · 6 settings tuned on this history".

**Pine v6 sketch.**
- `Trial`: append `bool fwd = false`. In `f_openTrial`: `fwd = not barstate.ishistory`.
- State: `var array<float> fwSt = array.new<float>(4, 0.0)`.
- `f_book` (role 0): `if t.fwd` → update `fwSt`.
- Tuned counter at global scope (after inputs):
  ```pine
  int nTuned = (wProx != 25.0 ? 1 : 0) + (wFresh != 10.0 ? 1 : 0) + (wConf != 15.0 ? 1 : 0) + (wDens != 20.0 ? 1 : 0) +
     (wDraw != 30.0 ? 1 : 0) + (minScore != 35.0 ? 1 : 0) + (hyst != 4.0 ? 1 : 0) + (maxATR != 10.0 ? 1 : 0) +
     (minDistATR != 0.5 ? 1 : 0) + (halfLife != 150.0 ? 1 : 0) + (potH != 30 ? 1 : 0) + (dGate != 0.35 ? 1 : 0) +
     (pivLen != 5 ? 1 : 0) + (eqTol != 0.10 ? 1 : 0) + (fvgQMin != 0.45 ? 1 : 0) + (obQMin != 0.40 ? 1 : 0)
  ```
  The literals must track the input defaults.
- Panel header tooltip (the ACCURACY row, 2377): "History trials are in-sample: k settings differ from defaults, and the
  defaults were themselves chosen on charts. Only FORWARD trials are out-of-sample."

**Ledger measurability.** Direct (forward hit / expected / R).

**Evidence.** Strong (out-of-sample principle; Sullivan et al. 1999; the Zhang 2026 holdout collapse from Sharpe ≈ 3 to 0.26).

**Risk.** Forward n grows slowly: about 1 trial per H bars. The row mostly says "n small", which is honest. State resets on
reload.

**Effort.** S (about 30 lines).

---

### SKEP-8 (P2, effort S) · Honest claims: PoT, the PoT filter, "destination" and the verdict words

**Why.** Users read words, not methods. Four current claims overstate:
1. "the pool the market is most likely drawing to next". By design, inner pools are taken first (685): the DOL is a
   destination.
2. PoT shown as the level's probability. It is the probability that a level at that *distance* is touched (geometry plus
   regime). Its honest reading is "how far", not "how good".
3. "Minimum PoT to Show DOL" reads as a quality filter. It is a distance filter.
4. "✕ NO EDGE" printed when the edge is merely not measurable (MDE 5.5-9.5 pp).

**Algorithm and text.**
- README intro: "highlights the highest-scoring *destination* for the current leg. Inner pools on the way are usually
  taken first."
- PoT tooltip (label `tooltip`, and the `potModel` tooltip at 142): "PoT = how often price on this symbol travelled this
  distance within H bars in the same HTF regime. It measures distance and volatility, not the quality of this particular
  level. Random levels at 1 / 2 / 3 ATR are touched about 75-80 / 55-60 / 40-45% of the time within 30 bars."
- `minPoT` tooltip: "Filtering by PoT filters by distance: a higher minimum shows nearer targets."
- Verdict words: "✓ BEATS RANDOM" / "~ NOT PROVEN (MDE x pp)" / "✕ WORSE THAN RANDOM", from the anytime bound (SKEP-2).
  Never "NO EDGE".
- Clean style: no verdicts. The label keeps "PoT", and its tooltip adds "random-level touch rate at this distance: x%"
  (equal to PoT under the Empirical model, which itself makes the point).

**Ledger measurability.** Not a statistic. It aligns the words with what the ledger measures.

**Evidence.** Strong (definitions), and §2.3 D for the base rates quoted.

**Risk.** None technical. It may feel less "magical", which is the point.

**Effort.** S (text only, about 15 lines).

---

### SKEP-9 (P3, effort S) · Multiple-comparison discipline in the Full view; gate learning by the same test

**Why.**
- The Full view shows 4 family rows plus RACE: 5 at-a-glance tests. At one look, P(some row "looks significant") is 11%,
  and more with peeking.
- `f_calMult` acts on those same noisy family rates (sibling calib_ml: ≥ 10% off under the null in 47-66% of families).

**Algorithm.**
- One *primary* pre-declared test gets a verdict: the ALL mirror edge (SKEP-2), plus the R-expectancy (SKEP-4).
- Family rows are labelled "exploratory" and print `hit / exp · excess ± anytime band`, in neutral colour.
- `f_calMult` (sibling CAL-1) applies a family's multiplier only when that family's mirror excess passes the anytime bound
  at α = 0.05/4 (Bonferroni across 4 families). Otherwise ×1.0.

**Pine v6 sketch.**
- Per-family block arrays (`blkD_g` for g = 0..3; or one flat array of size 4·nBlocks with index `g*nBlocks + id`) are
  filled in `f_book` alongside ALL.
- Row text: `f_cell(dash, 1, row, str.tostring(100*kg/ng, "0") + "% / " + str.tostring(100*stPE.get(g)/ng, "0") + "%", dim, na)`.
- In `f_calMult(g)`, return 1.0 unless `f_csPass(g, 0.0125)`.

**Ledger measurability.** Yes. The family verdict rate under placebo pickers should be ≤ 5% in total.

**Evidence.** Strong (Holm/Bonferroni; data-snooping literature) and moderate (sibling calib_ml null simulations).

**Risk.** Family multipliers will almost never activate at default depth, which is the honest outcome given the MDE.

**Effort.** S (about 30 lines with SKEP-2's helpers).

---

### SKEP-10 (P3, effort S) · Audit trail: every past target visible, including abandoned ones

**Why.**
- Visual evaluation of an indicator is survivorship-prone. Users remember the targets that were hit.
- The engine draws only the current target. The ghost trail is off by default and capped at 12.
- An optional step line of the DOL price on every bar shows each switch, each abandoned target and each hit. Users can then
  audit the "targets jump around" complaint and the accuracy panel by eye.

**Algorithm.** Plot the active DOL's near edge per bar as a step line with breaks, coloured by side. Optionally add a small
marker on the bar a record resolves (hit ✓ / expired ✕). Default off.

**Pine v6 sketch.**
- Input (G_GHOST, after 172): `bool showAudit = input.bool(false, "Show DOL Audit Trail", group = G_GHOST, tooltip = "Draws every past target (including abandoned ones) as a step line so the record can be checked by eye.")`.
- Data window (2438-2444):
  ```pine
  float dolEdgeOut = na
  int   dolSideOut = 0
  if not na(activeLv)
      dolEdgeOut := activeLv.nearEdge()
      dolSideOut := activeLv.side
  plot(dolEdgeOut, "DOL Price", color = dolSideOut == 1 ? cAbove : cBelow, style = plot.style_steplinebr, linewidth = 2,
    display = showAudit ? display.all : display.data_window)
  ```
- Docs: plot `display` is "input plot_display" and `style` is "input plot_style" (reference/plot.md), so an input-driven
  ternary is allowed.
- The values come from confirmed-bar state, so the line does not repaint.

**Ledger measurability.** Indirect: it lets users check the ledger by eye.

**Evidence.** Weak (UX reasoning) for the value; strong for the survivorship rationale.

**Risk.** Clutter, so it is off by default. The `DOL Price` plot changes from the last `activeLv.price` to the near edge,
which is closer to what the ledger grades. Mention it in the release notes.

**Effort.** S (about 10 lines).

---

## 5. How this fits the other study reports

- **calib_ml** (CAL-1 to CAL-7):
  - SKEP-3 supplies the variance CAL-1 and CAL-2 need.
  - SKEP-2 adds the *control* CAL-2 lacks: its confidence sequence is only as good as `pBase`, and §2.3 C/F shows `pBase` is
    off by −4 to +3 pp.
  - SKEP-5 is CAL-3's role probes, made paired, with R and a TREND role.
  - SKEP-9 gates CAL-1.
- **quant_pot** (QPOT-01 drift removal, QPOT-04 PoT grading): SKEP-6 adopts QPOT-01 as a null default. SKEP-1 removes the
  drift from the race readouts. QPOT-04 (a Brier score for the displayed PoT) is complementary: it grades calibration, while
  SKEP-2/4 grade edge.
- **quant_regime** (ER-gated D): adopted in SKEP-6, measured by SKEP-5.
- **session_stats / ict_time** (learned session effects): SKEP-6 turns the fixed affinities off by default. Their learned
  tables should enter only through the SKEP-5/9 gate.
- **ict_pd / ict_liq** (array prior, sweep learner): every learned modifier must pass the SKEP-2 mirror test and the
  SKEP-9 Bonferroni gate before it changes scores.

---

## 6. Sources

Read directly (paper index passages):
- Taylor, V. (2026). Evaluating the Predictive Validity of ICT's AMD Model on CME E-Mini NASDAQ-100 Futures. arXiv:2610.35887. https://arxiv.org/abs/2610.35887
- Chung, K. & Bellotti, A. (2021). Evidence and Behaviour of Support and Resistance Levels in Financial Time Series. arXiv:2101.07410. https://arxiv.org/abs/2101.07410
- Mesfin, M. (2026). Structural Limits of OHLCV-Based Intraday Momentum Signals in MNQ Futures: A Systematic Falsification Study. arXiv:2605.04004. https://arxiv.org/abs/2605.04004

Confirmed via the paper index or WebSearch (abstract or metadata):
- Garzarelli, F. et al. (2014). Memory effects in stock price dynamics: evidences of technical trading. Sci. Rep. 4:4487, doi:10.1038/srep04487; arXiv:1110.5197.
- Osler, C. (2000). Support for Resistance: Technical Analysis and Intraday Exchange Rates. FRBNY Economic Policy Review 6(2), 53-68. https://www.newyorkfed.org/research/epr/00v06n2/0007osle (random-level bounce rate 56.2% confirmed via a second copy).
- Osler, C. (2003). Currency Orders and Exchange-Rate Dynamics. J. Finance 58(5). FRBNY SR125: https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr125.pdf
- Osler, C. (2005). Stop-loss orders and price cascades in currency markets. JIMF 24(2). FRBNY SR150: https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr150.pdf
- Sullivan, R., Timmermann, A. & White, H. (1999). Data-Snooping, Technical Trading Rule Performance, and the Bootstrap. J. Finance 54(5), 1647-1691. https://econpapers.repec.org/RePEc:bla:jfinan:v:54:y:1999:i:5:p:1647-1691
- Bailey, D., Borwein, J., López de Prado, M. & Zhu, Q. (2014/2015). The Probability of Backtest Overfitting; Pseudo-Mathematics and Financial Charlatanism. https://papers.ssrn.com/abstract=2326253 ; https://carmamaths.org/jon/backtest.pdf
- Harvey, C. & Liu, Y. (2020). False (and Missed) Discoveries in Financial Economics. arXiv:2006.04269.
- Chen, A. & Zimmermann, T. (2022). Publication Bias in Asset Pricing Research. arXiv:2209.13623.
- Coqueret, G. (2023). Forking paths in financial economics. arXiv:2401.08606.
- Howard, S., Ramdas, A., McAuliffe, J. & Sekhon, J. (2021). Time-uniform, nonparametric, nonasymptotic confidence sequences. Ann. Stat.; arXiv:1810.08240.
- Waudby-Smith, I. & Ramdas, A. (2020/2024). Estimating means of bounded random variables by betting. arXiv:2010.09686.
- Gençay, E. (2026). What survives honest evaluation? Leakage-safe, search-aware assessment of LLM-driven trading strategy discovery. arXiv:2608.27734.
- Zhang, H. (2026). Hard to Fool: A Bounded LLM Research Loop for Quantitative Finance. arXiv:2611.06607.
- Sermpinis, G. et al. (2018). Technical Analysis and Discrete False Discovery Rate: Evidence from MSCI Indices. arXiv:1811.06766.
- Wang, S. et al. (2015). Testing the performance of technical trading rules in the Chinese market. arXiv:1504.06397.
- Jung, J. & Lee, K. (2026). Do Round Numbers Hold Prices? arXiv:2610.34787.
- Lallouache, M. & Abergel, F. (2013). Tick Size Reduction and Price Clustering in a FX Order Book. arXiv:1307.5440.
- Probability of touch ≈ 2× probability ITM (reflection principle): https://www.optionsanalysissuite.com/documentation/probability-of-touch-vs-probability-itm
- Open-source TradingView script "Fair Value Gap (FVG) Statistics with Placebo Control" (WebSearch summary: no detectable advantage over size-matched placebo zones in 14 measurements). https://de.tradingview.com/script/Kbq3WncE-Fair-Value-Gap-FVG-Statistics-with-Placebo-Control/

Via sibling reports (not re-fetched here; numbers taken from those reports):
- Nordman Algorithms: Do Fair Value Gaps Work? / Do Order Blocks Work? / ICT Displacement and the MSS. https://www.nordman-algorithms.com/blog/do-fair-value-gaps-work/ , https://www.nordman-algorithms.com/blog/do-order-blocks-work/ , https://www.nordman-algorithms.com/blog/ict-displacement-market-structure-shift/
- Barot, SSRN 7148099 (FVG reactions vs random); SSRN 7359378. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7148099
- Mahadzva, SSRN 7430998 (ICT/SMC rules, G10 FX walk-forward; continuation after sweeps). https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7430998 (a vendor blog summary confirmed the 65/66 figure; the paper itself was not opened).
- Tangirala, SSRN 7483658 (44 SMC detectors, S&P 500). https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7483658 (not confirmed here).
- MarketTrace (BTC FVGs): https://markettrace.ai/blog/fair-value-gap ; Trader Markus (S&P daily FVG/iFVG): https://tradermarkus.com/fair-value-gap/
- tradestar.app Silver Bullet test: https://tradestar.app/blog/i-tested-the-ict-silver-bullet-mechanically
- Andersen & Bollerslev (1997), J. Empirical Finance 4; Gao, Han, Li & Zhou (2018), JFE 129(2); George & Hwang (2004), J. Finance.
- Johari, Pekelis & Walsh (2017), Always valid inference (via calib_ml).

Sibling study reports used (local):
- `study/calib_ml.md`: peeking simulation, `f_calMult` null, feature lifts, pickers, design effects.
- `study/quant_pot.md`: drift error, martingale races, BGK correction, vol clock.
- `study/quant_regime.md`: geometry 0.645-0.706, D-first −9 to −12 pp, ER gate, post-sweep races.
- `study/session_stats.md`: day-bootstrap null for PDH/PDL and session statistics; ADR.
- `study/ict_pd.md`, `study/ict_liq.md`, `study/ict_time.md`, `study/bias_dol.md`, `study/trade_mgmt.md`.

This study's code and outputs: `study/skeptic_tools/*.py`, `study/skeptic_tools/out_*.txt`.
