# Price-action targeting and projections: combined final study (researcher A + researcher B)

Domain: Al Brooks price action (magnets, measured moves, breakout tests, failed breakouts, trading range vs trend, "always in", second entries, the 20-gap-bar rule, the traders' equation); measured-move and leg-equality targets (AB=CD, "leg 1 = leg 2", Bulkowski's measured move and measure rule); Fibonacci extensions used as targets (127.2 / 161.8 / 200 %, ICT "standard deviation" projections −0.27 / −0.62 / −1 / −2 / −2.5 / −4); swing projection from displacement legs; Elliott and harmonic target heuristics; Dow theory.

The question throughout: **does any projection method tell us how far a leg will go, which liquidity is taken next, and how likely, better than a random level at the same distance?**

**How to read the tags.**
- **[A✓]**: researcher A's material, re-checked by B (source re-opened or searched again, raw output re-read, or code re-read).
- **[CORRECTED]**: B changed a number, a definition, an evidence grade, a line reference or a spec. The reason is given.
- **[NEW-B]**: added by researcher B (new source, new test, new proposal detail).

**Line numbers** refer to `brief/baseline_v2.pine` (byte-identical to `indicators/dol_engine.pine`; B checked with `cmp`).

**Sibling studies** are cited by proposal id, using their `.final.md` versions where they exist: `ict_struct.final.md` (ICTS), `ict_pd.final.md` (ICTPD), `ict_liq.final.md` (ICT), `bias_dol.final.md` (BIAS), `wyckoff_sd.final.md` (WYK), `quant_pot.final.md` (QPOT), `quant_regime.final.md` (REG), `academic_sr.final.md` (ACAD), `calib_ml.final.md` (CAL), `competitors.final.md` (COMP), `ict_time.final.md` (TIME), `session_stats.final.md` (SESS), `orderflow_micro.final.md` (OF), `classic_levels.md` (CL).

**Reproduction.**
- A's tests (T1-T6): `study/pa_tools/` (`palib.py`, `t1_legs.py` … `t6_blind.py`; outputs `out_t*.txt`).
- B's tests (B1-B3): `study/pa_b_tools/` (`b1_legreach.py`, `b1_legreach_noGC.py`, `b2_legside.py`, `b2_legside_noGC.py`, `b2_series.py`, `b3_failbo.py`; outputs `out_b*.txt`). They reuse A's loaders, ATR and zigzag from `palib.py`.
- Run every script with `python3 -I <script> <args>`.

**Data** (shared with sibling studies):
- **1h set (9 series):** CME ES, NQ, RTY, YM, GC, CL (Mar 2025-Apr 2026, about 6,200 bars each); BTC 2016-2025 (79,000 bars); EURUSD 2017-18 (5,000); EURUSD 2024-26 (12,300).
- **5m set (6 series):** the six CME 1-minute files (Jan-Apr 2026) resampled to 5 minutes, about 16,800 bars each.
- **Daily set (3 series):** S&P 500 and NASDAQ 1999-2018, GOOG 2004-2013.
- **[NEW-B] Data defect: the CME GC 1h file is contaminated.**
  - 1,429 of its 6,067 bars have volume ≤ 10, 441 bars have zero range, and there are open-to-prior-close jumps of 70-120 ATR (for example 2025-08-05/06).
  - It looks like a thin back-month contract interleaved with the front month.
  - It distorts GC-specific results (A's GC overshoot mean 0.776; B2's GC leg-side effect −23.9 pp). B re-ran the 1h tests without GC; the GC-free numbers are reported wherever they matter.
  - Pooled conclusions do not change. **Anyone re-using `amt_data/cme/GC/GC_1h_*.csv` for verification should filter `volume > 10`, or drop the file.**

**Baselines.**
- (a) **Martingale geometry:** a driftless race to +a before −b has P = b/(a+b) for any continuous martingale.
- (b) **The engine's random-level baseline:** the unconditional K-bar excursion survival at the same ATR distance (the `f_potBase` idea, 1314-1322).
- (c) **A bar-shuffled null:** each bar's shape and gap kept, order destroyed.

**Research access.**
- A: WebFetch could not reach most hosts, and Firecrawl web search had no credits. A's published numbers came from search summaries, from full-text passages of the paper index (Glattfelder et al.), or from sibling reports.
- B: Firecrawl scraping was again out of credits, and WebFetch resolves none of thepatternsite.com, brookstradingcourse.com, mql5.com, arxiv.org or openaccess.city.ac.uk from this session. B therefore:
  - re-verified through WebSearch summaries (marked "via search summary") and through the paper index's full text (Glattfelder et al. 2011; Glattfelder & Golub 2022; Filimonov & Sornette 2011);
  - re-read A's raw outputs and code;
  - ran three new tests.

---

## 0. Executive summary

1. **No projection ratio is special. [A✓]**
   - **Setup.** ATR-zigzag legs (k = 2 or 3 ATR), 18 series, three timeframes, about 39,000 legs.
   - **Ratios.** Successive leg ratios show no clustering at any Fibonacci ratio:
     - retracements 0.382 / 0.5 / 0.618 / 0.786;
     - same-direction projections 1.0 / 1.272 / 1.618 / 2.0 / 2.618.
   - **Bump index.** It is 0.85-1.11 at the Fibonacci ratios, 0.85-1.23 at placebo ratios, and 0.88-1.13 in the bar-shuffled null.
   - **Replication.** This replicates Batchelor & Ramyar's DJIA 1914/15-2002/03 block-bootstrap test: "a few significant ratios … no more than would be expected by chance".
2. **"Leg 1 = leg 2" (AB=CD) is reached half the time, the random-walk value. [A✓ + NEW-B corroboration]**
   - P(leg CD ≥ leg AB) = 0.490 (1h), 0.498 (5m), 0.496 (daily); the shuffled null gives 0.491 / 0.498 / 0.492.
   - **[CORRECTED]** A wrote that Bulkowski's target is "corrective low + 60% of the first leg". Bulkowski's pages report instead:
     - a 60% success rate for the measured move up in bull markets, and 43% for the measured move down;
     - a current target of **half** the first leg added to the corrective low;
     - and he says the full-height target "only works 45% to 56% of the time" (via search summaries).
   - Bulkowski's own full-leg figure therefore matches the 49-50% random-walk value.
3. **The honest answer to "how far will this leg go" is the directional-change overshoot law, but its scale is not universal. [A, CORRECTED + NEW-B]**
   - **The law.** Once a k·ATR reversal confirms a leg, the leg's further extension before the next k·ATR reversal is approximately exponential with mean θ·δ:
     - pooled θ ≈ 1.05-1.10;
     - P(≥ 1δ) 0.34-0.39 vs e⁻¹ = 0.368;
     - Glattfelder, Dupuis & Olsen 2011, 13 FX pairs: E ≈ 1.04, C ≈ 1.06 (B verified this in the full text);
     - Brownian-motion theory: Taylor 1975, Lehoczky 1977, Golub et al. 2016.
     - The previous leg's size carries no information (correlation −0.03 to +0.03).
   - **[CORRECTED] A omitted the comparison with its own shuffled null.** At k = 2 the bar-shuffled null overshoots more than real data:
     - 1h: θ 1.205 vs 1.055 (GC-free: 1.164 vs 1.076);
     - 5m: 1.172 vs 1.095;
     - daily: 1.167 vs 1.078;
     - at k = 3 the two agree (1.05 vs 1.05).
     - Real legs are therefore 7-13% **shorter** than i.i.d. bars would make them at the 2-ATR scale. That is mild short-horizon mean reversion.
   - **[NEW-B] The scale varies.**
     - By instrument: θ 0.96-1.41 across clean series (GC 0.78 on contaminated data).
     - Fairly stable over time: across-series correlation of first-half vs second-half θ is +0.77.
     - Most of all **by session hour** on CME 1h: P(OS ≥ 1δ) is 0.33 for legs confirmed in Asia vs 0.44-0.45 for legs confirmed 05:00-12:00 ET. That is the intraday volatility clock (TIME, QPOT).
4. **[NEW-B] The leg-reach readout (PA-3) is already calibrated without tuning.**
   - **The readout:** P(target before a δ pullback) = ((δ − u)/δ)·e^(−y/δ), where y is the distance beyond the running extreme and u the current pullback.
   - Over about 40,000 sampled in-leg bars per set, predicted vs observed was:
     - random levels: 0.151 vs 0.150 (1h), 0.158 vs 0.162 (5m);
     - liquidity pools: 0.297 vs 0.278 (1h, GC-free), 0.310 vs 0.305 (5m).
   - A per-chart θ, a distance offset and a with-trend/counter-trend θ split each change the Brier score by under 0.001. **Keep θ = 1.**
5. **[NEW-B] At leg scale, liquidity pools are neither magnets nor reversal points.**
   - **Reach.** Within the same leg and pullback state, the nearest unswept 5-bar pivot beyond the running extreme is reached slightly **less** often than a random level at the same distance: −0.8 to −2.6 pp in 4 of 6 distance bins on 1h (null ≈ 0). That is consistent with Osler (2000): S/R interrupts trends.
   - **Endings.** Legs that take a pool end within 0.5δ beyond it no more often than legs that pass a random level: 0.343 vs 0.361 on 1h, 0.363 vs 0.384 on 5m. There is no "stop run, then reverse" signature in leg lengths.
6. **Projection levels are reached at random-level rates. [A✓]**
   - **Tested levels:** AB=CD 0.5-2.0×, ICT −0.27 / −0.62 / −1 / −2 SD (= classic 127.2 / 161.8 / 200 / 300 %), and BC extensions.
   - **Result:** edges −0.5 to +2.7 pp, **flat across ratios**, so it is an event-volatility effect, not a level effect.
   - **No stall at the level:** P(1 ATR beyond before 1 ATR back) = 0.47-0.50.
   - **[CORRECTED]** The MQL5 benchmark (26,795 double tops/bottoms) is a target-vs-stop race against martingale geometry:
     - the 1.618 target won 67% vs 71% geometry (t −13.5);
     - but the 2.0 target sat at geometry (35.5% vs 34.8%, t +1.8);
     - and its null has no volatility structure.
     - Grade lowered from moderate to **weak-moderate**.
7. **Brooks's headline probabilities are geometry. [A✓ + NEW-B corroboration]**
   - **"60% measured move after a strong breakout."**
     - Reproduced only with a follow-through bar (0.66), which geometry also predicts (0.66), because follow-through moves the entry.
     - A Brooks-forum member's own backtest gives 50-52% for "every good breakout to the MM target" (via search summary). That matches T3's 0.52-0.55.
   - **Little or no information:**
     - H2/L2, the 20-gap-bar rule and the Always-In direction carry none (Always-In +0.2 ± 0.5 pp, n 10,169).
     - Only ≥ 2 ATR range-breaking bars show a weak, inconsistent +2.5 to +3.4 pp.
     - **[NEW-B]** The speed of the reversal (fast displacement-like vs slow directional change) does not predict how far the new leg runs; the sign flips between timeframes.
8. **[NEW-B] The current leg's direction does not say which pool goes first.**
   - From any bar, the nearest pool on the leg's side is taken first at the geometry rate: 1h −0.3 ± 0.4 pp GC-free, 5m 0.0 ± 0.5.
   - At a fresh 1h leg extreme (u < 0.15δ) the leg-side pool is taken first **less** often than geometry: −2.8 ± 0.9 pp (k = 2), −4.3 ± 1.1 pp (k = 3); null +0.2 / +0.8.
   - Not on 5m (−0.3) or daily (−0.6).
   - So chasing the leg at its extreme is not supported. This agrees with REG-3 / ICTS: momentum-type side votes carry no information.
9. **[NEW-B] "A failed breakout goes to the other side of the range" (Brooks) is geometry.**
   - After a close back inside a 2-8 ATR, 20-bar range within 5 bars, the opposite edge is reached before the failed extreme is traded through at the geometry rate:
     - 1h +1.8 ± 0.8 pp (null +0.2);
     - 5m −1.7 ± 0.8 (null −1.3);
     - daily +0.7 ± 1.9.
   - **[A✓]** Brooks's "80% of breakout attempts fail" mixes two events. Attempts that never close beyond the range are a different event from close-based breakouts. Close-based breakouts come back inside within 5 bars 53-62% of the time (null 48-53%), which is close to Brooks's other figure ("actual breakouts fail about 50%").
10. **One Brooks/ICT magnet has measured support: the prior RTH close (gap fill, ICT ORG, settlement). [A✓ + CORRECTED spec + convergent siblings]**
    - **A's test.** At 10:00 ET on CME futures, n = 968, the edge is +3.4 ± 1.3 pp over a clock-matched random level, concentrated at 0.5-2 ATR distance (+4.2 / +4.8 pp). Under 0.5 ATR it is −5.3 ± 3.1 pp.
    - **Sibling tests:**
      - classic-levels study: settlement +3.46 pp (z 3.7) from the Globex open;
      - ICTPD study: gaps ≥ 0.5 ATR fill +7.4 pp (z 2.2) on CME and +7.9 pp (z 4.5) on NDX cash.
    - **[CORRECTED]** A's PA-2 put the level in the external registry. The registry turns it into a strict trade-through BSL/SSL pool (step 11, 1834-1851), whereas the measured effect is a touch.
      - It must instead be ICTPD-6's gap-fill object (kind 8/9, src 13, touch semantics), gap-gated.
      - Its session-time capture is still needed, because TradingView treats ETH as the regular session for futures.
11. **Price discovery is where a liquidity engine goes blind. [A✓]**
    - On 5.0% of 1h, 5.8% of 5m and 13.7% of daily bars there is no unswept pool within 10 ATR on the trend side. The engine then shows a `⚠ COUNTER-DRAW` target or nothing.
    - Projections are reached at random-level rates, so a projection there carries an honest PoT without claiming an edge (PA-1).
12. **Dow theory, Elliott, harmonics.**
    - **Dow theory:** a long-horizon effect only (Brown, Goetzmann & Kumar 1998: high Sharpe ratios, positive alphas 1902-29, out-of-sample neural-net replication).
    - **[NEW-B]** Dow "with-trend" legs (an up-leg from a higher low) overshoot a little more than counter-trend legs: +0.06 to +0.14 δ in mean, P(≥ 1δ) +0.5 to +2.1 pp, null −0.02. This is too small to change anything; it is a learner feature (PA-5).
    - **Elliott:** no controlled test exists. **[CORRECTED]** CXO's Prechter score is quoted as 17-22% (vs a 47% guru average) depending on the report, and CXO calls its own confidence in that number "very low".
    - **Harmonics:** small-n blog tests only.
    - **All three:** their target ratios are the Fibonacci ratios that finding 1 rejects.
    - **[NEW-B]** Filimonov & Sornette (2011) show that the volume and volatility "signatures" at trend extremes (Preis et al.) appear identically in a random walk once extremes are selected after the fact. Leg-end features observed in hindsight are not predictive.

**What this domain contributes** (five proposals, section 4; best first):
- **PA-1** (P1): an honest price-discovery projection fallback, re-coded to the shared kind/src map.
- **PA-2** (P2): the session-time ORG capture, corrected to touch semantics and a gap gate, as one object with ICTPD-6 / CL-4.
- **PA-3** (P3): the validated leg-reach readout.
- **PA-4** (P3): Brooks-strength displacement for the legacy draw vector only.
- **PA-5** (P3): measured-move and ICT −1 SD rules as shadow roles in CAL-3's candidate ledger, plus zero-prior leg features.
- A documented do-not-add list (section 5).

---

## 1. Concepts (precise definitions and parameters)

**Notation.**
- A = ATR(14), Wilder RMA as `ta.atr`.
- "Taken" = strict trade-through for liquidity (the engine's `touched`, 623-624).
- "Touched" = ≥ / ≤, for projections, arrays and gap-fill levels.
- "Geometry" = the driftless race probability b/(a+b).
- δ = k·A, the directional-change threshold.

### 1.1 Swing and leg definitions used for projections [A✓]
- **Pivot swing (engine).** `ta.pivothigh(high, len, len)` with len = 5 (`pivLen`, 90). It is confirmed len bars after the extreme. Successive pivots need not alternate.
- **ATR zigzag (directional change, DC).**
  - Up mode: track the running maximum M and its bar.
  - A DC is confirmed on the first bar whose low ≤ M − k·A(t), which makes M a swing high.
  - The new running minimum is the lowest low after M, including the confirming bar.
  - A bar that sets a new extreme never confirms (intrabar order unknown).
  - k = 2 ≈ a Brooks "leg"; k = 3 ≈ a swing. Pivots alternate by construction.
  - Edge cases: ATR warm-up; a confirmation can happen on a gap bar; δ varies bar by bar with A(t).
- **Leg** = |p(i+1) − p(i)|. Retracement ratio R = L(i+1)/L(i). Same-direction projection ratio E = L(i+2)/L(i), i.e. AB vs CD.
- **Overshoot (Glattfelder et al.).** After the DC that confirms pivot i, the DC price is p(i) ∓ δ. OS is the further distance from the DC price to the next pivot. **[NEW-B]** Glattfelder et al. measure it this way, and by construction ⟨|Δx_dc|⟩ = Δx_dc. B verified this in the paper.

### 1.2 Measured moves (Brooks, Bulkowski)
- **Leg 1 = Leg 2 / AB=CD [A✓].**
  - Bull case: A (low) → B (high) → C (higher low, A < C < B); target D = C + (B − A).
  - Brooks: a measured move is "a swing that is equal in size to a prior swing in the same direction" (Brooks, *Trading Price Action: Trading Ranges*, Part II "Magnets", ch. "Measured moves based on the size of the first leg"; via search summary).
  - Variants: D = C + f·(B − A) with f = 0.618 / 1.272 / 1.618 (harmonic AB=CD extensions).
- **Breakout-bar measured move (Brooks) [A✓ + NEW-B context].**
  - **Measurement.** Measure the breakout (one bar, or "from the low of the first bar to the close of the last bar of the breakout") and project it from the close or the high.
  - **Brooks's own framing.** "After a significant breakout there is a 60% chance of a measured move up of the size of the breakout", i.e. the market moves n up before n down (forum, via search summary).
  - **The numbers.** Flashcard sources give 60% and "at least 70%". Brooks calls such numbers rough estimates ("40-60 rule"; "70% or higher, but the stop is then far away").
  - **Strong breakout bar.** Brooks gives no numeric threshold. Operational proxy (A): body ≥ m·ATR (m = 1, 1.5, 2), body/range ≥ 0.6, close in the outer 25% of the bar, close beyond the 20-bar extreme.
- **Follow-through bar [A✓].** The next bar is a same-direction trend bar closing beyond the breakout close.
- **Measuring gap (Brooks) [A✓].** The gap between the breakout point and the first pullback (an FVG in ICT language) "often marks the middle of the move". Target = 2·(gap midpoint) − leg origin.
- **Range-height measured move (Bulkowski "measure rule", Wyckoff "cause and effect") [A✓].** Target = breakout edge ± range height.
  - **[NEW-B]** Bulkowski now multiplies the height by his per-pattern "percentage meeting price target" figure, because the plain full-height rule "works poorly" (thepatternsite measure-rule page, via search summary).
- **Bulkowski measured move up (MMU) [CORRECTED].**
  - **Pattern.** First leg up, a corrective phase (B-to-C), then a second leg.
  - **Success rates.** 60% in bull markets for MMU; 43% for MMD (thepatternsite mmu.html / mmd.html, via search summary).
  - **Target.** Half the first leg (AB/2) added to the corrective low C (Pattern Review 5, via search summary). The full first-leg target "only works 45% to 56% of the time" (secondary article quoting Bulkowski).
  - **Retrace depth.** A deeper corrective retrace makes a full second leg more likely (about 31,000 MMU and 21,000 MMD samples, bull markets; MMRetrace page).
  - **Selection bias.** MMU/MMD are identified only once the pattern is complete, so the published rates condition on a second leg having started.

### 1.3 Fibonacci extensions and ICT "standard deviation" projections [A✓ + NEW-B]
- **Classic extension of an impulse A→B.** A + r·(B − A) for r = 1.272, 1.618, 2.0, 2.618; equivalently B + (r − 1)·(B − A).
- **ICT "SD" projections.** Targets at −0.27, −0.62, −1, −2, −2.5, −4, i.e. B + g·(B − A). Hence ICT −0.27 = 127.2%, −0.62 = 161.8%, −1 = 200%, −2 = 300%.
  - **[NEW-B]** "Despite the name, nothing statistical is computed: one 'standard deviation' equals the height of the anchor range, laddered outward in whole and half multiples" (LuxAlgo concept page, via search summary).
  - **Anchors vary:** the CBDR, the Asian range, an opening range, or the session's manipulation (Judas) leg. ICT's own rule: do not use CBDR projections when the CBDR is wider than 40 pips.
  - The −2 to −2.5 band is the "commonly watched zone", but "no band is owed a touch".
  - **No published hit rates** were found for any SD level.
  - The CBDR/Asian-range version is covered in TIME §1.8.
- **Pullback extension.** B + h·(B − C) for h = 0.272, 0.618, 1.0.
- **Retracements (0.382 / 0.5 / 0.618 / 0.705 / 0.786, OTE).** These are entry locations, not targets (ICTS 1.10).

### 1.4 Elliott wave and harmonic heuristics [A✓]
- **Elliott target rules (practitioner).**
  - Wave 3 = 1.618 × wave 1.
  - Wave 5 = wave 1, or 0.618 × (waves 1-3).
  - C = A.
  - Wave 2 retraces 0.5-0.618; wave 4 retraces 0.382.
  - Counts are subjective and re-labelled after the fact.
- **Harmonics.** XABCD with ratio windows:
  - Gartley: B = 0.618 XA, D = 0.786 XA.
  - Bat: B 0.382-0.5, D 0.886 XA.
  - Butterfly: D = 1.272-1.618 XA.
  - Crab: D = 1.618 XA.
  - D is a reversal zone; the targets are retracements of AD.

### 1.5 Brooks bias and context concepts [A✓, details CORRECTED]
- **Always In (AI).** "If you had to be in the market now, long or short?"
  - It flips on a strong breakout. Brooks's own wording is notoriously loose (Brooks forum "always in confusion"; via search summary).
  - Algorithmic proxy (A): the sign of the latest two-bar breakout (each body/range ≥ 0.5, combined body ≥ 2 ATR, closing beyond the prior 20-bar extreme), held for 100 bars.
- **Trading range vs trend.**
  - **[CORRECTED]** Brooks's "80% of breakout attempts fail" refers to attempts, including probes that never close beyond the range. Separately, "a real breakout fails about 50%" (forum interpretations, via search summary).
  - The range is "a magnet, an area of agreement".
  - Proxy: a close beyond the prior 20-bar high/low; failure = a close back inside within 5 bars.
- **Failed breakout → test of the other side [NEW-B].** Brooks: a failed breakout of a trading range tends to lead to a test of the opposite side.
  - Proxy: after a failure (as above), race the opposite range edge (touch) against a trade-through of the failed extreme.
- **Breakout test / breakout pullback.** Price returns to test the breakout point. WYK §2.5: throwback reached at random-level rates (0.870 vs 0.872).
- **Second entries (H1/H2, L1/L2).**
  - In a bull pullback, H1 = the first bar whose high exceeds the prior bar's high. After a lower low, the next such bar is H2.
  - Proxy: trend = close > EMA20 with EMA20 rising over 5 bars at the trend high. Race: trend high vs pullback low.
- **20 gap bars.** ≥ 20 consecutive bars entirely beyond the EMA20; the first EMA touch is expected to retest the trend extreme. Forum estimate: 70-75%.
- **Magnets (Brooks) [CORRECTED].** Brooks's book has a part "Magnets: Support and Resistance" covering:
  - measured moves based on the first leg (the spike);
  - measured moves based on gaps and trading ranges;
  - "Other magnets": swing highs/lows of recent bars or days, breakout points, and "gaps of any kind, including moving average gaps".
  - The day's open and the prior day's high, low and close are Brooks magnets from his daily commentary.
  - The moving average itself is **not confirmed** as a standalone magnet in that chapter (via search summary). A had listed it.
- **Final flag.** A late pause in a trend whose breakout fails; it is only known after the fact.
- **Traders' equation.** Probability × reward > (1 − probability) × risk. In the engine this is R:R · WIN≤H · EV (`f_invalidation` 1343-1364, using `f_raceH` 466).

### 1.6 Dow theory [A✓]
- **Primary trend.** HH/HL (LL/LH) until a failure swing breaks the prior low/high.
- **Phases.** Accumulation, public participation, distribution.
- **Confirmation.** Two related averages must confirm each other. The modern analogue is SMT, which needs a second symbol.
- **Engine analogue.** `f_structure` (708-782).
- **[NEW-B] Leg-level operationalisation.** A "with-trend" leg is an up-leg starting from a higher low (zigzag p(i) > p(i−2)) or a down-leg from a lower high. A "counter-trend" leg starts from a lower low or a higher high.

### 1.7 Gap fill / prior close / settlement [A✓ + NEW-B convergence]
- **Prior RTH close.** The 16:00 ET close for US index futures; or the CME settlement (VWAP of 14:59:30-15:00:00 CT since 2020; CL §1.10). It is what ICT calls the "opening range gap" (ORG) reference.
- **Gap fill.** The next session trades back to that close (a touch).
- **Practitioner statistics.** Fill odds are size-dependent and front-loaded into the first 30-60 minutes.
  - SPY 0.10-0.25% gaps fill 77-85%; 0.5-1% gaps fill 33-42% (CL P12).
  - ES prior close touched on 1,048 of 1,803 days, 58.1% (SESS; no baseline).
- **ETH charts.** On 23-hour CME futures charts the RTH gap is not a chart gap. Pine docs: "For futures, the 'Electronic trading hours' session *is* the regular session" (`concepts/sessions.md`, `session.isfirstbar_regular` row). B re-read it in the local mirror.
- **[NEW-B] Pine session semantics** (`reference/time.md`, `concepts/sessions.md`):
  - `time(tf, sess, tz)` is non-na when the bar's **open** time is in the session.
  - `time_close(tf, sess, tz)` is non-na when the bar's **close** time is in the session.
  - On a 1H chart with "0930-1600", the 09:00 bar is therefore *not* in the session by `time()` (it opens at 09:00), but it *is* by `time_close()` (it closes at 10:00).

### 1.8 Price discovery [A✓]
- **Definition.** On the trend side there is no unswept liquidity within the engine's `maxATR` (10 ATR): new highs/lows, or after a cascade.
- **Practitioner targets in that state.** Measured moves, Fibonacci extensions, round numbers, ATR/ADR projections.
  - Round numbers are covered by OF-4 / ICT-3: they act as geometry, not as magnets. Sweep wicks stop short of round numbers (−4 pp).
  - ADR caps are rejected by SESS §2.7 (the sign is reversed).

### 1.9 Leg reach before a pullback (overshoot law), derived [A✓, calibration CORRECTED/NEW-B]
- **Theory.** For driftless Brownian motion, the maximum gain before a drawdown of δ from the running maximum is **Exponential with mean δ** (Taylor 1975; Lehoczky 1977). It is exponential for every δ iff μ/σ² is constant (Mayerhofer 2019). For BM, overshoots satisfy ω(δ) ~ Exp(δ), E = δ, Var = δ² (Golub et al. 2016, as restated in Glattfelder & Golub 2022; B read the passage).
- **The readout.** For a leg at running extreme M, price p, pullback so far u = side·(M − p) < δ, and a target T:
  - **T beyond M** (y = side·(T − M) > 0): P(T before a δ pullback) = ((δ − u)/δ)·exp(−y/(θδ)), with θ = 1. The first factor is the martingale race back to M; the second is the exponential law.
  - **T between p and M:** a plain race against M − side·δ, P = (δ − u)/((δ − u) + side·(T − p)).
- **[NEW-B] Empirical status.**
  - **Pooled.** θ = 1 is calibrated within 0.5 pp for random levels and within 0.5-2.8 pp for pools on 1h and 5m (B1, §2.3).
  - **By instrument.** Per-instrument θ ranges 0.96-1.41 and is fairly stable (half-vs-half correlation across series +0.77). But an online per-chart θ does not improve the Brier score (B1 (e)).
  - **By hour.** The scale depends strongly on the **session hour** on intraday futures: P(OS ≥ 1δ) is 0.33 (Asia) vs 0.45 (London morning / NY AM). The readout is miscalibrated by about −4 to +9 pp per session bucket (0.327-0.452 vs a pooled 0.365) until δ is expressed on a volatility clock (QPOT-03 / TIME-2).
  - **Versus i.i.d. bars.** At k = 2, real legs are 7-13% shorter than in the bar-shuffled null (θ 1.08 vs 1.16 GC-free 1h). That is mild mean reversion at the 2-ATR scale, not visible at k = 3.
  - **Information content.** The law is memoryless. It is informationally equivalent to distance from the running extreme plus pullback depth, and it adds no targeting skill.

### 1.10 [NEW-B] Liquidity in leg terms
- **Question.** For an in-progress leg, the "pool target" is the nearest unswept 5-bar pivot beyond the running extreme. The test (B1) asks two things:
  - (a) is it reached before a δ pullback more often than a random level at the same y in the same leg state?
  - (b) does a leg that takes it end just beyond it (stop run, then reversal) more often than a leg that passes a random level?
- **Result.** Neither: (a) −1 to −2 pp; (b) −2 pp. See 2.3.
- **Context.** This is the leg-scale version of the ACAD / ICTPD finding that pools are reached at random-level rates or slightly less, and that they act as barriers on approach (Osler 2000: S/R levels interrupt trends 60.8% vs 56.2% at arbitrary levels).

### 1.11 [NEW-B] Order clustering and where trends stop (Osler)
- **Osler (2003, *J. Finance* 58(5)), RBS order book.**
  - Take-profit orders cluster at round numbers, which explains why trends tend to reverse at S/R.
  - Stop-loss orders cluster just beyond round numbers, which explains why trends accelerate after crossing them.
  - OF quantifies it: stop-buys at 01-10 above a "00" 14.4% vs 7.4% at 90-99 below.
- **Role.** This is the only documented *mechanism* for "where a leg stops". It is at round numbers and known S/R, not at Fibonacci or measured-move levels. The engine handles round numbers via OF-4.

---

## 2. Evidence

### 2.1 Published evidence (numbers, sources, B's verification)

| # | Claim | Source | Numbers | Grade | B's check |
|---|---|---|---|---|---|
| L1 | Fibonacci / round-fraction ratios in trend lengths | Batchelor & Ramyar (2006), Cass/City Univ. London; DJIA 1914-2002 (abstract) / 1915-2003 (A); Politis-Romano stationary block bootstrap | "A few significant ratios … no more than would be expected by chance given the large number of tests"; the Economist (Buttonwood) summary: "no sign that the ratios work" | strong (rigorous null; working paper / PhD chapter) | **[A✓]** abstract and thesis TOC via search summary |
| L2 | 1.618 extension as a target | MQL5 statistics blog (28 Sep 2026): 26,795 mechanical double bottoms/tops; DAX, FTSE, NQ, Dow 2015-26; 24 h; target vs stop race; geometry p = d(stop)/(d(stop)+d(target)) | 1.618: **67% vs 71%** (t −13.5), short about 4 pp on each market; **2.0: 35.5% vs 34.8% (t +1.8, n.s.)**; fixed definition, no parameter search, no out-of-sample split, no volatility structure in the null | **weak-moderate [CORRECTED from moderate]** | **[CORRECTED]** It is a race, and the 2.0 target is at geometry (via search summary) |
| L3 | Fibonacci retracement depth | Tradeify (2026), 263 legs (via ICTS S10) | 64% fully retraced first; continuation falls smoothly with depth; no Fibonacci bump | weak (small n) | [A, not re-fetched] |
| L4 | Fibonacci retracement system | Gurrib, Nourani & Bhaskaran (2022), *Financial Innovation* 8 | Beats buy-and-hold in a falling-oil sample; no random-level control | weak | **[A✓]** paper index abstract |
| L5 | DC overshoot ≈ threshold | Glattfelder, Dupuis & Olsen (2011), *Quant. Finance* 11(4): 599-614; 13 FX pairs, ticks Dec 2002-Dec 2007 | ⟨\|Δx_os\|⟩ ≈ Δx_dc (E ≈ 1.04, C ≈ 1.06); total move ≈ 2Δx_dc (E ≈ 0.99, C ≈ 0.51); overshoot takes about 2× the DC time and ticks; GRW "strikingly close" on averages; EUR-CHF deviates | strong (law), none (edge) | **[A✓]** full text (paper index) |
| L6 | Max before drawdown is exponential | Taylor (1975); Lehoczky (1977); Mayerhofer (2019), arXiv 1909.13050; Golub et al. (2016) via Glattfelder & Golub (2022), arXiv 2204.02682 | ω(δ) ~ Exp(δ), E = δ, Var = δ² for BM | strong (theory) | **[NEW-B]** Glattfelder & Golub passage read |
| L6b | [NEW-B] Overshoot length depends on market and liquidity | Golub, Chliamovitch, Dupuis & Chopard (2016), *Algorithmic Finance* 5; Glattfelder & Golub (2022) | "Longer overshoots correspond to more illiquid markets"; fiat FX deviates and needs a scaling factor λ ≠ 1 | moderate | paper index |
| L7 | Intrinsic time as a memoryless hazard | Houweling (2025), arXiv 2511.14408 | DC share of events ≈ 1 − 1/e = 0.632 | weak (single author) | **[A✓]** abstract |
| L8 | Dow theory timing | Brown, Goetzmann & Kumar (1998), *J. Finance* 53: 1311-1333 | Hamilton's calls 1902-29: high Sharpe ratios, positive alphas; neural-net extraction tested out of sample; +4.4 pp/yr 1930-97 (NYU Stern news, per A) | strong (long horizon only) | **[A✓]** abstract; the 4.4 pp figure is not re-verified |
| L9 | Elliott wave forecasting | CXO Advisory Guru Grades (2005-2012); Kiplinger; WealthManagement | Prechter **17-22%** (vs 47% average), depending on the report; CXO: "sample very small … confidence … very low" | weak (no controlled test) | **[CORRECTED]** range and caveat (via search summary) |
| L9b | [NEW-B] Elliott autocycles in crypto/NFT | Westland (2024), *Sci. Rep.* 14 (PMC10891072) | "Did not support the existence of Elliott Wave behaviour"; fractal fits "not consistent or stable over time" | weak (one market type) | paper index abstract |
| L10 | Harmonic patterns | HKUST student study; 2026 blog (ES 15m, 7-29 trades per pattern); researcher-degrees-of-freedom critique | Rare; low total profitability; PF 1.37 on 29 trades | none-weak | **[A✓]** no peer-reviewed test found by B either |
| L11 | Brooks breakout measured move | Brooks forum, flashcards, *Trading Price Action: Trends* ch. 2 | "60%" (one source 70%); **[NEW-B]** a forum member's own backtest: "about 50-52%" for every good breakout to the MM | weak | **[A✓ + NEW-B]** via search summary |
| L12 | Brooks 80% rule | Brooks, MoneyShow; Brooks forum | 80% of *attempts* fail; actual breakouts fail about 50% | weak | **[CORRECTED]** two different events |
| L13 | Brooks 20-gap-bar | *Trading Price Action: Trends* ch. 13; forum | First EMA touch after ≥ 20 gap bars → test of the extreme; 70-75% (forum) | weak | [A] |
| L14 | Bulkowski measured move | thepatternsite mmu.html, mmd.html, MMRetrace.html, Pattern Review 5 | MMU 60% (bull), MMD 43%; target = corrective low + **half** of leg 1; the full leg works 45-56%; deeper retrace → second leg ≥ first more often (31,000 MMU / 21,000 MMD) | moderate (large n, no random baseline, completed-pattern selection) | **[CORRECTED]** "60% of leg 1" was wrong |
| L15 | Range-height measured move | Bulkowski rectangles (WYK §1.8); measure-rule page | 79% / 55% meet target up / down (daily stocks, bull); Bulkowski scales the height by a per-pattern percentage because the plain rule "works poorly" | moderate (no random baseline) | **[A✓ + NEW-B]** |
| L16 | Gap fill | TradingView ES/NQ gap statistics; Market Chameleon SPY; CL P12; SESS (Linnsoft 58.1%) | Size-dependent, front-loaded; SPY 0.5-1% gaps 33-42% | weak | [A] + siblings |
| L17 | S/R interrupts trends, does not attract | Osler (2000); Kavajecz & Odders-White (2004) (ACAD S1, S4) | Published levels stop trends 60.8% vs 56.2% for arbitrary levels | strong | sibling |
| L18 | [NEW-B] Order clustering at round numbers | Osler (2003), *J. Finance* 58(5): 1791-1819; NY Fed SR125/SR150 | Take-profits at round numbers → reversals; stops just beyond → acceleration (RBS order book) | strong (mechanism) | via search summary; OF quantifies it |
| L19 | [NEW-B] Features at trend extremes are selection artefacts | Filimonov & Sornette (2011), arXiv 1112.3868 (comment on Preis, Schneider & Stanley, *PNAS* 2011) | Power-law volume and volatility peaks "around switching points" reproduce exactly in a Gaussian random walk; "an artifact of their statistical analysis" | strong (null reproduces the claim) | full text (paper index) |
| L20 | [NEW-B] Trends revert at a critical significance | Schmidhuber (2021), arXiv 2006.07847 (ICTS S6) | Universal across asset classes from days to years; small coefficients; no effect at the engine's horizon | strong (law), none (intraday) | paper index |
| L21 | [NEW-B] Overshoot-length forecasting (ML) | Adegboye & Kampouridis (2021), *ESWA* 173; Adegboye, Kampouridis & Otero (2021), *IJIS*; Kampouridis & Otero (2017) | Classifiers and symbolic regression for "will a DC have an overshoot / how long"; reported trading improvements on FX; no random-level calibration benchmark | weak (in-sample-heavy, trading-PnL framing) | abstracts via search summary |
| L22 | [NEW-B] ICT SD levels | LuxAlgo concept page; backtrex; ICT CBDR notes | Range-height multiples; anchors vary; "−2 to −2.5 commonly watched"; no published hit rates | none (definitions only) | via search summary |

### 2.2 A's original tests [A✓: B re-read the code and every output file; the numbers below match the raw outputs]

#### T1 · Leg ratios and overshoot (`t1_legs.py`)

Bump index = n(ratio within ±3% of f) / (½·n(flanking bins f·[0.91, 0.97) ∪ (1.03, 1.09])). It is about 1 with no clustering; the Poisson SE is about 0.06-0.08.

| Set, k | legs | P(E≥1) real / null | P(E≥1.618) | Fib bumps, E | Fib bumps, R | Placebo range |
|---|---|---|---|---|---|---|
| 1h, 2 | 14,873 | 0.490 / 0.491 | 0.222 | 1.0: 0.97 · 1.272: 0.95 · 1.618: 1.01 · 2.0: 0.99 | 0.382: 0.99 · 0.5: 0.99 · 0.618: 0.95 · 0.786: 0.99 | 0.87-1.13 |
| 1h, 3 | 7,029 | 0.490 / 0.496 | 0.236 | 1.0: 1.02 · 1.272: 0.88 · 1.618: 0.91 · 2.0: 1.13 | 0.618: 0.94 | 0.85-1.23 |
| 5m, 2 | 10,524 | 0.498 / 0.498 | 0.233 | 1.0: 0.94 · 1.272: 0.92 · 1.618: 1.11 · 2.0: 0.99 | 0.618: 1.02 · 0.786: 1.11 | 0.88-1.15 |
| 5m, 3 | 5,032 | 0.503 / 0.503 | 0.265 | 1.0: 0.85 · 1.272: 0.96 · 1.618: 1.05 | 0.618: 0.87 | 0.85-1.16 |
| D, 2 | 1,401 | 0.496 / 0.492 | 0.228 | 1.0: 0.90 · 1.618: 0.97 | 0.618: 0.83 | 0.61-1.28 (small n) |

**Overshoot after a DC, OS/δ. [CORRECTED: B added the shuffled-null rows A's outputs contained but the report omitted.]**

| Set, k | real mean / median | real P≥1 / P≥2 | **null mean / P≥1 / P≥2** | corr(log prev same-dir leg, OS) |
|---|---|---|---|---|
| 1h, 2 | 1.055 / 0.667 | 0.356 / 0.146 | **1.205 / 0.423 / 0.179** | +0.009 |
| 1h, 2, GC-free [NEW-B] | 1.076 | 0.365 / 0.151 | **1.164 / 0.413 / 0.171** | — |
| 1h, 3 | 1.051 / 0.625 | 0.339 / 0.139 | 1.065 / 0.367 / 0.150 | −0.003 |
| 5m, 2 | 1.095 / 0.711 | 0.380 / 0.146 | **1.172 / 0.420 / 0.171** | +0.009 |
| 5m, 3 | 1.080 / 0.658 | 0.352 / 0.149 | 1.052 / 0.372 / 0.148 | +0.002 |
| D, 2 | 1.078 / 0.738 | 0.391 / 0.151 | 1.167 / 0.411 / 0.169 | −0.034 |
| D, 3 | 1.038 / 0.680 | 0.380 / 0.160 | 1.047 / 0.372 / 0.141 | +0.026 |

- Brownian Exp(1) reference: mean 1.000, median 0.693, P(≥ 0.5) 0.607, P(≥ 1) 0.368, P(≥ 2) 0.135.
- **Reading.**
  - The exponential shape and the absence of leg memory hold [A✓].
  - The discrete-bar null overshoots about 0.07-0.15δ more than real data at k = 2, because each bar's range adds a discrete jump past the threshold. Real data are slightly mean-reverting at that scale, which partly cancels the jump.
  - Pooled real values land close to Exp(1) by this partial cancellation, not because markets are Brownian bar by bar.
- **Per series (1h, k = 2), θ.** ES 1.04, NQ 1.13, RTY 1.17, YM 1.14, CL 1.09, BTC 1.06, EU17 1.11, EU25 1.08 (GC 0.78, contaminated). 5m: 1.06-1.18. Daily: SPX 1.03, NDX 1.05, GOOG 1.29.

#### T2 · Projection levels as DOL candidates (`t2_proj.py`) [A✓]

- **Setup.**
  - Event = zigzag pivot C confirmed with A < C < B (bull; mirror for bear). Entry at the confirmation close.
  - hit = touched within K bars; base = the engine-style random-level probability at the same distance.
  - SE is clustered in 2K-bar blocks.
  - React = P(1 ATR beyond the touched level before 1 ATR back); a martingale gives 0.5.

| Level | 1h k2 K30: dist / hit / base / **edge** / react | 1h k3 edge | 5m k2 edge / react | D k2 K10 edge |
|---|---|---|---|---|
| B (prior swing) | 1.15 / 0.684 / 0.700 / **−0.015** / 0.527 | +0.001 | +0.003 / 0.528 | +0.022 |
| MM 0.618 | 1.36 / 0.653 / 0.657 / **−0.003** / 0.506 | +0.003 | +0.013 / 0.497 | −0.004 |
| MM 1.0 (AB=CD) | 2.76 / 0.451 / 0.448 / **+0.004** / 0.486 | +0.018 | +0.027 / 0.468 | +0.025 |
| MM 1.272 | 3.93 / 0.338 / 0.330 / **+0.007** / 0.490 | +0.008 | +0.021 / 0.498 | +0.033 |
| MM 1.618 | 5.49 / 0.226 / 0.223 / **+0.003** / 0.500 | +0.006 | +0.018 / 0.497 | +0.011 |
| MM 2.0 | 7.24 / 0.150 / 0.145 / **+0.005** / 0.491 | +0.009 | +0.019 / 0.487 | −0.001 |
| EXT −0.27 | 2.30 / 0.506 / 0.510 / **−0.005** / 0.493 | +0.015 | +0.022 / 0.481 | +0.031 |
| EXT −0.62 | 3.90 / 0.330 / 0.323 / **+0.007** / 0.493 | +0.010 | +0.021 / 0.492 | +0.028 |
| EXT −1 | 5.63 / 0.206 / 0.201 / **+0.005** / 0.492 | +0.011 | +0.022 / 0.476 | −0.001 |
| EXT −2 | 10.30 / 0.071 / 0.066 / **+0.006** / 0.519 | +0.005 | +0.009 / 0.519 | +0.008 |
| BCX 127.2% | 1.76 / 0.586 / 0.586 / **−0.000** / 0.485 | +0.021 | +0.017 / 0.478 | +0.042 |
| BCX 161.8% | 2.66 / 0.448 / 0.451 / **−0.003** / 0.501 | +0.006 | +0.014 / 0.485 | +0.027 |

- About 7,600 events (1h k2), 3,700 (1h k3), 5,300 (5m), 690 (daily).
- **Reading.**
  - The edge is the same at every ratio, so it is event volatility after a fresh reversal (volatility clustering), not a level effect.
  - There is no stall at the measured move.
  - The engine's own pool B is reached at −1.5 to +2.2 pp.

#### T3 · Brooks claims (`t3_brooks.py`, with shuffled nulls) [A✓]

Race = target touched before a trade-through of the stop, horizon 4K bars; diff = win − geometry.

| Setup | 1h: n / win / geom / **diff** | 5m: n / win / geom / **diff** | D: diff | null 1h / 5m diff |
|---|---|---|---|---|
| 1 bar, body ≥ 1 ATR, MM open→close | 4,419 / 0.521 / 0.524 / **−0.003** | 3,394 / 0.538 / 0.523 / **+0.015** | −0.002 | +0.007 / +0.001 |
| … + follow-through bar | 1,481 / **0.664** / 0.663 / **+0.000** | 1,179 / **0.662** / 0.679 / **−0.017** | +0.003 | +0.005 / +0.005 |
| 1 bar, body ≥ 1.5 ATR | 2,752 / 0.524 / 0.520 / **+0.004** | 1,534 / 0.546 / 0.519 / **+0.026** | +0.023 | +0.003 / +0.003 |
| 1 bar, body ≥ 2 ATR | 1,608 / 0.542 / 0.517 / **+0.025** | 740 / 0.551 / 0.518 / **+0.034** | −0.034 (n 61) | −0.006 / +0.002 |
| 1 bar, body ≥ 2 ATR, MM low→high | 1,589 / 0.478 / 0.452 / **+0.027** | 728 / 0.497 / 0.456 / **+0.041** | −0.023 | −0.005 / −0.004 |
| 2 consecutive trend bars (Σbody ≥ 2 ATR) | 2,082 / 0.535 / 0.514 / **+0.021** | 1,501 / 0.528 / 0.514 / **+0.013** | +0.021 | −0.012 / +0.004 |
| H2 / L2 | 451 / 0.379 / 0.391 / **−0.011** | 231 / 0.420 / 0.382 / **+0.038** | +0.019 | +0.043 / −0.043 |
| 20-gap-bar first EMA touch: hit ≤ K vs random level | 1,028: 0.483 vs 0.497 (**−0.014**) | 781: 0.524 vs 0.511 (**+0.013**) | 120: +0.065 ± 0.040 | +0.010 / −0.004 |

- **Per series, body ≥ 2 ATR:**
  - 1h: ES −5.0, NQ −8.4, RTY +0.1, YM +4.4, GC +4.8, CL −0.3, BTC +4.2 (n 976 of 1,608), EU17 +4.7, EU25 +1.5 pp.
  - 5m: ES +6.8, NQ +9.1, RTY +7.4, YM +0.3, GC −1.0, CL −4.0 pp.
- **Grade:** weak for the large-bar residual; moderate for "the Brooks probabilities are geometry".

#### T4 · Range, Always In, measuring gap, time symmetry (`t4_misc.py`) [A✓]

| Test | 1h | 5m | D | Shuffled null (1h / 5m) |
|---|---|---|---|---|
| (1) close back inside within 5 bars after a 20-bar-range breakout by close: narrow (≤ 4 ATR) / mid / wide | 0.531 / 0.551 / 0.624 | 0.580 / 0.568 / 0.552 | 0.564 / 0.607 / 0.636 | 0.501 / 0.501 / 0.484 · 0.532 / 0.509 / 0.525 |
| (1b) range-height MM before the opposite edge, minus geometry (mid ranges) | +0.026 (n 6,306) | +0.031 (n 5,665) | +0.027 (n 832) | −0.008 / +0.005 |
| (2) Always-In side's nearest pool taken first, minus geometry | **+0.002 ± 0.005** (n 10,169) | **+0.001 ± 0.006** | −0.013 ± 0.020 | −0.000 / −0.020 |
| (3) measuring-gap target hit ≤ K minus random level | −0.000 ± 0.006 | +0.034 ± 0.007 | +0.038 ± 0.017 | −0.012 / −0.008 |
| (4) AB=CD time symmetry: Spearman(bars A→B, bars C→D) | +0.241 | +0.315 | +0.424 | **+0.285 / +0.286** |

- Breakout events overlap, so the SEs are understated by up to about 2×.
- The 5m measuring-gap edge is most likely the time-of-day confound.

#### T5 · Prior RTH close (`t5_pdc.py`) [A✓; spec consequences CORRECTED in PA-2]

| Sample | n | median dist (ATR) | hit | base | baseH (clock-matched) | **edge vs baseH** |
|---|---|---|---|---|---|---|
| 10:00 ET, one per day, K = 6 | 968 | 2.22 | 0.381 | 0.254 | 0.347 | **+0.034 ± 0.013** |
| 10:00 ET, K = 30 | 968 | 2.22 | 0.603 | 0.545 | 0.568 | **+0.035 ± 0.014** |
| all live RTH bars, K = 6 | 5,210 | 2.70 | 0.245 | 0.215 | 0.223 | +0.022 ± 0.005 |
| dist 0-0.5 ATR | 184 | 0.35 | 0.707 | 0.757 | 0.759 | **−0.053 ± 0.031** |
| dist 0.5-1 | 439 | 0.75 | 0.622 | 0.556 | 0.580 | +0.042 ± 0.023 |
| dist 1-2 | 1,178 | 1.50 | 0.413 | 0.340 | 0.364 | +0.048 ± 0.014 |
| dist 2-4 | 2,136 | 2.92 | 0.161 | 0.135 | 0.140 | +0.021 ± 0.007 |
| dist > 4 | 1,273 | 4.91 | 0.037 | 0.035 | 0.032 | +0.005 ± 0.005 |

- **Semantics.** Hit = **touch** (≥/≤), `t5_pdc.py` line 56. **[NEW-B]** This matters for the spec (PA-2).
- **Naive baseline.** Against the all-hours baseline the 10:00 edge looks like +12.7 pp. Every session-anchored statistic needs a clock-matched baseline.
- **Caveat.** The six instruments are correlated; GC is in the sample (contaminated).
- **[NEW-B] Convergence.**
  - The classic-levels study, with its own code on the same CME data, finds settlement +3.46 pp (z 3.7) from the Globex open.
  - ICTPD finds that gaps ≥ 0.5 ATR fill +7.4 pp (z 2.2), and NDX cash (different data) +7.9 pp (z 4.5). Small gaps show no excess.
  - CL also finds the prior-day mid (CPR BC = `dayEQ`) +3.95 pp and PD VWAP +2.76 pp. The magnet may be "prior-day value" in general, not the close specifically.
  - **Grade raised from weak-moderate to moderate:** three implementations, one partly independent dataset.

#### T6 · How often is the draw side blind (`t6_blind.py`) [A✓]
- **Frequency.** Unswept 5-bar pivot pools within 10 ATR:
  - no pool above on 5.0% (1h), 4.4% (5m), 11.5% (daily) of bars;
  - blind on the EMA50-trend side on 5.0%, 5.8%, 13.7%.
- **Reach toward the blind trend side.** The K-bar excursion has median 2.46 ATR (1h, K 30), P(≥ 2 ATR) 0.578. That is a few pp above the unconditional rate, so a distance-based PoT is honest there.

### 2.3 B's original tests [NEW-B]

#### B1 · Leg reach before a δ pullback: calibration, pools vs random, conditional overshoot (`b1_legreach.py`, `b1_legreach_noGC.py`)

- **Sampling.** Every third bar inside a zigzag leg (u < δ).
- **Targets.**
  - (POOL) the nearest unswept 5-bar pivot beyond the running extreme, 0 < y ≤ 4δ;
  - (RANDOM matched) a random level at y ~ U(0, 4]δ, drawn only on bars that also have a pool;
  - (RANDOM all) the same on every bar.
- **Outcome.** The leg's final extreme passes the target (strict >), i.e. the target is reached before the δ reversal.
- **Prediction.** PA-3's formula with θ = 1, and an online θ (mean OS of the last 50 completed legs).
- **Nulls.** Shuffled bars. Samples are heavily overlapping: the "naive SE" understates the true SE by about 2-3×.

**(c) Calibration of the PA-3 readout (θ = 1), predicted → observed, mean over samples:**

| Set | POOL (n) | RANDOM matched (n) | Brier POOL: θ=1 / online θ / constant | top bin (pred 0.8-1.0) POOL / RANDOM |
|---|---|---|---|---|
| 1h k2, GC-free | 0.297 → 0.278 (38,498) | 0.150 → 0.151 (39,466) | 0.1566 / 0.1577 / 0.2006 | 0.87 → 0.85 / 0.86 → 0.87 |
| 1h k2 (all) | 0.303 → 0.275 (40,286) | 0.151 → 0.150 (41,301) | 0.1611 / 0.1599 / 0.1996 | 0.87 → 0.74 / 0.87 → 0.77 |
| 1h k3 | 0.360 → 0.332 (40,663) | 0.151 → 0.154 (41,013) | 0.1775 / 0.1776 / 0.2216 | 0.87 → 0.79 / 0.87 → 0.83 |
| 5m k2 | 0.310 → 0.305 (29,622) | 0.158 → 0.162 (31,356) | 0.1606 / 0.1622 / 0.2120 | 0.86 → 0.85 / 0.86 → 0.85 |
| 1h k2 null | 0.296 → 0.325 | 0.155 → 0.184 | — | — |

- **(e) Variants** (1h GC-free, 5m), Brier changes:
  - an offset y + c, c ∈ {0.05, 0.10}: best c differs by set, gain ≤ 0.0004;
  - with-trend θ 1.08 / counter-trend θ 0.95: gain ≤ 0.0001;
  - online per-chart θ: +0.0012 better on 1h with GC, but −0.0011 worse on 1h GC-free and −0.0016 worse on 5m.
- Most of the top-bin over-prediction on 1h came from the contaminated GC file: GC-free, the top bin is 0.87 → 0.85 for pools and 0.86 → 0.87 for random levels.
- **Verdict:** θ = 1 with no tuning. The readout is calibrated for random levels and slightly optimistic (0.5-2.8 pp) for pools.

**(c2) Pool vs matched random level at the same y, in the same leg state (u < 0.25δ), hit rates:**

| y (δ) | 1h k2 GC-free: pool − random | 1h k3 | 5m k2 | 1h k2 null (GC-free) |
|---|---|---|---|---|
| 0-0.25 | −0.008 | −0.014 | −0.012 | +0.010 |
| 0.25-0.5 | +0.014 | −0.008 | −0.021 | −0.012 |
| 0.5-1.0 | −0.012 | −0.006 | +0.020 | +0.012 |
| 1.0-1.5 | −0.017 | **−0.055** | **−0.033** | +0.011 |
| 1.5-2.5 | **−0.026** | −0.009 | −0.004 | −0.005 |
| 2.5-4.0 | −0.012 | +0.008 | −0.004 | +0.013 |

- Naive SE ±0.007-0.02 per cell.
- Real cells are negative in 14 of 18; null cells are positive in 4 of 6.
- **Reading:** liquidity pools beyond the running extreme are reached about 1-2 pp *less* often than random levels at the same distance. Grade **weak-moderate** (consistent sign, small size, overlapping samples).

**(d) Sweep-and-reverse:** among legs that reach the target, the share that end within 0.5δ beyond it:
- 1h GC-free: POOL 0.343 vs RANDOM 0.361;
- 1h k3: 0.352 vs 0.341;
- 5m: 0.363 vs 0.384;
- null: 0.346 vs 0.337.

There is **no excess "stop run then reversal" at pools** in leg terms.

**(b) Conditional overshoot, pooled 1h k2 GC-free (n 13,823), mean OS/δ and P(OS ≥ 1δ):**

| Condition | real mean / P≥1 | null mean / P≥1 | real − null in the contrast |
|---|---|---|---|
| with-trend leg (HL→up, LH→down) | 1.107 / 0.373 | 1.153 / 0.409 | — |
| counter-trend leg | 1.044 / 0.356 | 1.176 / 0.418 | **+0.086δ mean; +2.6 pp P≥1** |
| fast DC (≤ 2 bars) / slow (≥ 4) | 1.085 / 1.066 | 1.208 / 1.144 | the sign flips across sets (1h k3: 0.969 vs 1.146; 5m: 1.127 vs 1.080) → none |
| vol regime ATR14/ATR100 < 0.85 / 0.85-1.15 / > 1.15 | 1.114 / 1.081 / 1.036 | 1.173 / 1.155 / 1.183 | the sign flips on 5m → none |
| CME confirmation hour (UTC): 00-06 / 06-09 / 09-12 / 12-16 / 16-24 | P≥1 0.327 / 0.335 / **0.452** / **0.444** / 0.363 | — | **the session volatility clock** |

- With-trend vs counter-trend P(OS ≥ 1δ): 1h k3 0.349 vs 0.328; 5m 0.382 vs 0.377.
- The CME file clock is UTC: B inferred it from the 21-22 UTC halt hour and the peak range at 14 UTC.
- UTC 09-12 = 05:00-08:00 ET (London morning, summer); 12-16 = 08:00-12:00 ET (NY AM).

#### B2 · Does the current leg's direction say which pool goes first? (`b2_legside*.py`, `b2_series.py`)

- **Setup.** Every 4th bar with an unswept 5-bar pivot pool both above and below within 0.25-4 ATR. Race (strict trade-through, ≤ 200 bars). The "leg side" is the zigzag leg's direction.
- **Measure.** win = the leg-side pool first; diff = win − geometry. Cluster SE in blocks of 50.

| Set | all | at the extreme (u < 0.15δ) | shallow (0.15-0.5δ) | deep (0.5-1δ) | null at the extreme |
|---|---|---|---|---|---|
| 1h k2 GC-free | −0.003 ± 0.004 (n 16,442) | **−0.028 ± 0.009** (n 2,532) | −0.008 ± 0.005 | +0.014 ± 0.007 | +0.002 ± 0.010 |
| 1h k3 GC-free | −0.008 ± 0.005 | **−0.043 ± 0.011** | −0.005 | −0.001 | +0.008 ± 0.010 (with GC) |
| 5m k2 | −0.000 ± 0.005 | −0.003 ± 0.009 | +0.006 | −0.009 | −0.008 ± 0.011 |
| 5m k3 | +0.003 ± 0.005 | −0.002 ± 0.010 | +0.000 | +0.008 | — |
| D k2 | −0.019 ± 0.011 | −0.006 ± 0.020 | −0.022 | −0.030 | — |

- **Per series, 1h k2 at the extreme:** ES −2.7, NQ −1.7, RTY −7.6, YM −1.3, CL +2.7, BTC −3.1 (n 1,490), EU17 −0.1, EU25 −3.0, GC −23.9 (contaminated).
- **Reading:**
  - The leg direction carries no side information beyond geometry.
  - At a fresh 1h extreme there is mild reversion (−3 to −4 pp), absent on 5m and daily.
  - **Grade weak:** one timeframe, BTC-weighted.

#### B3 · Failed range breakout → opposite edge (`b3_failbo.py`, GC 1h excluded)

- **Setup.**
  - Range = prior 20 bars, width 2-8 ATR. Breakout = a close beyond the range.
  - Failure = a close back inside within 5 bars.
  - Race from the failure close: the opposite edge (touch) vs a trade-through of the failed extreme.
  - One event per episode.

| Set | n | opposite edge first | geometry | **diff** | null diff |
|---|---|---|---|---|---|
| 1h | 3,198 | 0.334 | 0.317 | **+0.018 ± 0.008** | +0.002 ± 0.008 |
| 1h, W 2-4 / 4-8 | 1,738 / 1,460 | 0.411 / 0.243 | 0.379 / 0.243 | +0.032 / +0.000 | −0.005 / +0.006 |
| 5m | 3,065 | 0.277 | 0.293 | **−0.017 ± 0.008** | −0.013 ± 0.009 |
| D | 480 | 0.267 | 0.260 | +0.007 ± 0.019 | — |

**Reading:** a failed breakout reaches the other side at the geometry rate. Brooks's claim adds nothing beyond distance. **Grade moderate (null).**

### 2.4 Evidence summary for the engine
- **Projection geometry (Fibonacci, AB=CD, ICT SD, Elliott and harmonic ratios).** No level-specific effect. **Strong** (L1, T1, T2 over 18 series; L2 weak-moderate).
- **Overshoot law.** The exponential, memoryless form holds: **strong** (L5, L6, T1). θ = 1 calibration for a readout: **moderate** (B1: within 0.5-2.8 pp pooled; −4 to +9 pp by session hour on CME 1h).
- **Brooks probabilities** (breakout MM, follow-through, H2, 20-gap-bar, Always In, failed breakout → other side). Geometry: **moderate** (T3, T4, B3; nulls, large n, three timeframes).
- **Leg direction / displacement speed as side or reach information.** None: **moderate** (B1 (b), B2).
- **Liquidity pools in leg terms.** Slightly harder to reach (−1 to −2 pp), no sweep-and-reverse signature: **weak-moderate** (B1).
- **Prior RTH close / settlement / large-gap fill.** **Moderate**: +3.4 to +3.5 pp clock-matched; +4 to +8 pp at 0.5-2 ATR or ≥ 0.5-ATR gaps; −5 pp under 0.5 ATR. (T5, CL, ICTPD.)
- **Price discovery.** 5-14% of bars: **moderate** (T6).
- **Dow with-trend legs.** +2.6 pp P(OS ≥ 1δ) vs null: **weak**; long-horizon Dow timing: strong (L8).

---

## 3. Engine gap analysis (`baseline_v2.pine`) [A's table re-checked line by line; corrections marked]

| Concept | Status | Lines | What the engine does / what differs |
|---|---|---|---|
| Liquidity magnets: prior swing highs/lows | present | 1753-1776 (chart pivots), 1779-1789 (STF/HTF registry), 1824-1851 (registry → pool as kind 0/1) | Reached at random-level rates (T2 row B) and **[NEW-B]** slightly below random in leg terms (B1 c2). Fine as the DOL universe; PoT slightly optimistic for pools (CAL-4 calibrates it) |
| Magnets: PDH/PDL, PWH/PWL | present | 944-961, 1790-1799 | Brooks's "yesterday's high/low" |
| Magnet: prior RTH close / settlement (ORG) | **missing** | — | No such level. ICTPD-6's time-break detector cannot see the 16:00 → 09:30 RTH gap on ETH futures charts (docs quote, 1.7). **[CORRECTED]** Do not push it into `extReg` (A's PA-2): step 11 (1834-1851) would turn it into a strict trade-through BSL/SSL with a liquidity zone beyond the price, merge it with swing pools within `eqPx`, and score it with liquidity density. T5 measured touches. → PA-2 (ICTPD-6 object) |
| Magnet: open of the day | partial | 964-966, 1931 | Midnight / London / NY opens are confluence anchors only (TIME-6 proposes the midnight open as a target) |
| Magnet: middle of the range | present (as confluence) | 967-968 (`dayEQ`, `htfEQ`), 1931 | CL finds `dayEQ` +3.95 pp as a target (prior-day value); CL owns it |
| Moving average / 20-gap-bar | missing (correct) | — | T3: random-level rate. Not even a Brooks standalone magnet (1.5) |
| Measured move / AB=CD | missing | — | Correct as a scored source (T2). Missing as a **price-discovery fallback** (T6) → PA-1 |
| Fibonacci extensions / ICT SD | missing (correct) | — | Do not add as targets or as confluence anchors (`anchors`, 1931) |
| Fibonacci retracements / OTE | missing (correct) | — | ICTS 1.10 |
| Elliott / harmonic targets | missing (correct) | — | L9, L9b, L10, T1 |
| Breakout-bar MM (Brooks 60%) | n/a | — | Geometry (T3, L11) |
| Displacement as a draw vote | partial | 897-904 (`bodyB`, `bRat`, `atrP`, `twoLeg`, `dispUp/dispDn`), 1536-1541 (step 1), 1893 (`mV`), 156 (`wM` 0.20) | 1.2-ATR bodies or a two-leg Σ ≥ 1.8 ATR; no close-location or structure requirement. T3: geometry below 2 ATR; **[NEW-B]** B1/B2: reversal speed and leg direction carry no information. REG-3 gates D anyway → PA-4 (legacy only) |
| Follow-through bar | missing (correct) | — | T3 |
| Failed breakouts / 80% rule | partial / wrong certainty | 1579-1582 (`liqEvt`: close beyond = hold = continuation) | T4 (1): a close beyond comes back inside 53-62%; **[NEW-B]** B3: a failure does not predict the other side. The sign mapping is owned by BIAS-4 / ICTS-2 / REG-3 |
| Trading range vs trend | missing | — | WYK / REG-2 cover it; labels do not persist |
| Always In | partial | 1891-1895 (`sV`, `mV`, `drawD`, `dirSide`), 1975 (`elig`) | D is an always-in-like vote. T4: zero side information; REG-3 gates it |
| Second entries H2/L2 | missing (correct) | — | T3 |
| Breakout test / throwback | missing (correct) | — | WYK §2.5 |
| Measuring gap | missing (correct) | — | T4 (3). FVGs present (1868-1887) |
| Range-height MM | missing (correct as a level) | — | T4 (1b): +3 pp race effect; PA-5 feature |
| Dow trend (HH/HL, BOS, CHoCH) | present | 708-782 (`f_structure`), 925-930 (bias ints) | Sound. Intraday side choice is a coin flip (ICTS §2.2); **[NEW-B]** leg-level with-trend overshoot +2.6 pp (weak) |
| Dow confirmation (SMT) | missing | — | Second symbol; out of scope |
| How far will the leg go (H-bar reach) | present (good) | 1059-1062 (`sUp/sDn`), 1265-1336 (`f_bump`, `f_surv`, `f_empPoT`, `f_potModel`, `f_potBase`, `f_reachD`), 1338-1339 (`f_reachClass`), 2102-2115 (reach quantiles), 2192-2199 (reach bands) | The empirical H-bar excursion surface is the right tool; no leg conditioning is needed (T1). QPOT-03 / REG-1 propose a vol-state / clock key |
| Leg reach before a pullback | **missing** | — | No readout for "will this leg get there without a k-ATR pullback?" → PA-3 (B1: calibrated) |
| Traders' equation / R:R race | present | 1343-1364 (`f_invalidation`), 466 (`f_raceH`), HUD 2240-2246 | **[CORRECTED]** A gave `f_raceH` as 1343-1364; it is defined at 466 and called at 1362-1363. Races are martingale races; drift adds noise (QPOT-01) |
| Leg-time symmetry | missing (correct) | — | T4 (4): the null reproduces it |
| Price-discovery targets | **missing** | 1964-2005 (step 19: `useCtr` when `aI < 0` → global best, usually counter-draw) | 5-14% of bars → PA-1 |
| Ledger family slots | rigid | 1066-1071 (arrays of 5), 1380-1381, 1470, 2375-2376, 2384, 2388-2389, 2403, 2411 (`for g = 0 to 3`), 2443 (data window) | **[NEW-B]** ALL is hard-coded as index 4 in 12 places, and step 17 (1935-1944) applies `cm0`..`cm3` only. Any new family (PA-1 PROJ, CL-4 SETT) needs the `NFAM` refactor in PA-1 step 5 |
| Kind/src code space | crowded | 312-316 (comment), 506-541, 597-602 (`f_kzAff`), 628-636 | **[NEW-B]** Siblings have claimed kinds 8/9 (gaps, ICTPD-6) and src 8-10 (N-day extremes, ICTPD-5) and 11-13 (NDOG/NWOG/ORG). PA-1 must use kinds 10/11 and src 14-16 |

---

## 4. Proposals (spec-level, best first)

### Shared building block: an O(1) ATR zigzag on confirmed bars [A✓, extended by B: pivot bars, leg-state outputs]

Used by PA-1, PA-3 and PA-5, and available to `smc_impl` (zigzag breaker template) and ICTPD. **Implement it once.**

- **Placement.** State goes in STATE (after 1080); the update goes in ENGINE as step **9b**, right after step 9 (after 1776).
- **Runs on every confirmed bar** (not only `inCalc`), so leg state is warm when scoring starts.

```pine
// INPUT (G_LIQ)
float zzK = input.float(2.0, "Leg Size (ATR)", minval = 0.5, step = 0.25, group = G_LIQ, display = display.none,
  tooltip = "A leg ends when price retraces this many ATR from its extreme. Used for projection targets and the leg-reach readout.")
// STATE
var int          zzMode = 0          // +1 tracking a high, -1 tracking a low
var float        zzExt  = na         // running extreme of the current leg
var int          zzExtB = na
var float        zzOpp  = na         // opposite extreme since zzExt was set (includes the confirming bar)
var int          zzOppB = na
var array<float> zzPx   = array.new<float>()   // last confirmed pivots, oldest first (max 3)
var array<int>   zzTy   = array.new<int>()     // +1 high · -1 low
var array<int>   zzBr   = array.new<int>()     // [NEW-B] bar of each pivot (anchors the projection zone)
// ENGINE step 9b
if zzMode == 0
    zzMode := 1
    zzExt  := high
    zzExtB := bar_index
else if zzMode == 1
    if high > zzExt
        zzExt  := high
        zzExtB := bar_index
        zzOpp  := na
    else
        if na(zzOpp) or low < zzOpp
            zzOpp  := low
            zzOppB := bar_index
        if low <= zzExt - zzK * atr
            zzPx.push(zzExt)
            zzTy.push(1)
            zzBr.push(zzExtB)
            zzMode := -1
            zzExt  := zzOpp
            zzExtB := zzOppB
            zzOpp  := na
else
    if low < zzExt
        zzExt  := low
        zzExtB := bar_index
        zzOpp  := na
    else
        if na(zzOpp) or high > zzOpp
            zzOpp  := high
            zzOppB := bar_index
        if high >= zzExt + zzK * atr
            zzPx.push(zzExt)
            zzTy.push(-1)
            zzBr.push(zzExtB)
            zzMode := 1
            zzExt  := zzOpp
            zzExtB := zzOppB
            zzOpp  := na
while zzPx.size() > 3
    zzPx.shift()
    zzTy.shift()
    zzBr.shift()
```

- **Behaviour.** It matches `pa_tools/palib.py: zigzag`: a bar that sets a new extreme never confirms, and δ = zzK·ATR(t).
- **Cost.** A few float operations per bar, no loops. Confirmed bars only, so it does not repaint.
- **Pine notes.**
  - `atr > 0` is guaranteed inside the engine block (1518).
  - Array pushes and shifts on `var` arrays are standard.
  - `display = display.none` follows the overhaul's legend fix.

### PA-1 (P1, M) · Price-discovery projection targets: an honest draw-side objective when no liquidity exists [A, CORRECTED codes, activation and ledger; priority kept with a changed rationale]

**Problem.**
- At new highs or lows (5.0% of 1h, 5.8% of 5m and 13.7% of daily bars on the trend side, T6) the pool holds no draw-side level within `maxATR`.
- Step 19 (1999-2005) then takes `useCtr` and shows a `⚠ COUNTER-DRAW` target against a running trend, or nothing.
- This persists after REG-3: its gate opens precisely in efficient trends, which is where price discovery happens.
- It is the most visible "targets look wrong" state.

**Why P1 with zero edge.**
- **[CORRECTED rationale]** It is a correctness and UX fix for a frequent, conspicuous state, not a forecasting gain.
- Projections are reached at random-level rates (T2: −0.5 to +2.7 pp, flat across ratios), so the existing PoT is already honest for them. B1 confirms the leg-reach form too.

**Algorithm.**
1. **Ladder** (bull case; mirror for bear). Applies when `zzTy` = [−1, +1, −1] (A, B, C), `zzMode == 1` and A < C < B:
   - `MM1 = C + (B − A)` (AB=CD, Brooks's "leg 1 = leg 2");
   - `EX1 = B + (B − A)` (ICT −1 SD = 200%);
   - `MM16 = C + 1.618·(B − A)`.
   - **[NEW-B] Fallback rung** when there is no valid A < C < B triplet (V-reversal to new highs): `LEG1 = zzExt + zzK·atr`. This is the mean overshoot (Glattfelder: total move ≈ 2δ), labelled `LEG +1δ`.
2. **Pick the rung.** The lowest rung (bull) that is ≥ `close + minDistATR·atr`. All rungs are equivalent in evidence; the nearest has the highest PoT.
3. **Activation.** New step **16b**, inside `inCalc`, after step 16 and before step 17.
   - Condition: `useProj and dirSide != 0 and zzMode == dirSide`, and no level with `kind <= 9` on `dirSide` with `0 <= lv.distance(close) <= maxATR*atr`.
   - One pass over `pool`. Ignore kinds 10/11 themselves.
   - `dirSide` is the **gated** side once REG-3 lands (dSel). With `dirSide == 0` no projection is shown: the engine is then in score-first mode and a below-side pool is a legitimate pick.
4. **Level.**
   - New kinds **10** = projection above (side +1) and **11** = projection below (side −1).
   - `src` **14** = MM 1.0, **15** = EXT −1 (200%), **16** = MM 1.618, **17** = LEG +1δ.
   - Zone: thin, `[P, P + wPx]` above or `[P − wPx, P]` below.
   - `qual = 0.5`, `coil = induce = 0`, `anchorBar = zzBr.get(2)` (C), `bornBar = bar_index`.
   - **At most one per side, updated in place** when the rung changes (at most once per leg). If it is in `openT`, move `t.edge` as `f_mergeAt` does at 1124-1126.
   - Delete it as soon as real draw-side liquidity enters within `maxATR`. Ghost it as `⊘ REPLACED` if it was active.
5. **Code touch points.**
   - `f_newLevel` side map (1085): `kind == 0 or kind == 3 or kind == 5 or kind == 7 or kind == 8 or kind == 10 ? 1 : -1`. Kind 8 is ICTPD-6's gap above; include it if ICTPD-6 lands first.
   - `touched` (623-624): `isArray()` stays `kind >= 2`, so a projection uses touch semantics (not liquidity), consistent with the decision history.
   - Step 3 partial fill (1566): add `and lv.kind <= 7`, so no CE "delivery" for projections or gaps.
   - `evaluate` (686-690): the origin lockout needs `src == 0`, so it never applies. The density is 0.5·qual = 0.25 (low by design).
   - `f_tierW` (506-516): `src 14-17 => 0.20`.
   - `f_levelName` / `f_shortName` (518-541): kinds 10/11 → `"MM 1.0"`, `"EXT -1"`, `"MM 1.618"`, `"LEG +1δ"` by src. Clean label: `Target: MM 1.0`.
   - `f_kzAff` (597-602): the default 1.0 applies.
   - Step 18 trimming keeps it (`src >= 1` gets +10).
   - Stacks (step 16) and the registry ignore kinds ≥ 2.
   - **Ledger families [NEW-B refactor].** Add `const int NFAM = 5` (0 chart liq · 1 ext liq · 2 FVG/gaps · 3 OB/BRK · 4 PROJ) and `ALL = NFAM`. Then:
     - size `stN/stK/stBars/stPE/stPV/stMae` to `NFAM + 1` (1066-1071);
     - replace the literal 4 by `ALL` at 1380-1381, 1470, 2375-2376, 2384, 2388-2389, 2403, 2443;
     - change the loop at 2411 to `for g = 0 to NFAM - 1`;
     - add `cm4 = f_calMult(4)` in step 17 (1935-1944);
     - `grp()` (635-636): `kind >= 10 ? 4 : kind <= 1 ? (src == 0 ? 0 : 1) : kind <= 3 or kind == 8 or kind == 9 ? 2 : 3`;
     - `f_grpName` (543-549): `4 => "PROJ"`.
     - If CL-4's own SETT family is also adopted, it becomes family 4 and PROJ family 5, with `NFAM = 6`. That is one constant to change.
6. **Display.**
   - Terminal head `◈ PROJ ▸ MM 1.0`.
   - Clean tooltip: "Price discovery: no liquidity above within 10 ATR. Projection, not liquidity: on this symbol price reaches it like a random level at this distance."
   - An optional `PRICE DISCOVERY` tag in the bias table footer when active.

**Ledger.**
- The PROJ family hit rate is measured vs `pBase`. Expected edge ≈ 0.
- The value is **coverage**: the fraction of bars with a draw-side objective rises, which COMP-6 measures.
- If PROJ shows a negative edge on a chart, `f_calMult(4)` (or CAL-1) damps it automatically.

**Evidence.** Moderate: T2 (about 17,000 intraday and 690 daily events), T6, L1, L2, B1.

**Risk.**
- Users may over-read Fibonacci or measured-move labels; the tooltip states the measured rate.
- The rung changes at most once per leg; the two-bar challenger rule and the hysteresis (2012-2018) prevent flicker.
- The kind/src map must be applied centrally (section 6).

**Effort.** M: about 70 lines, plus the `NFAM` refactor (about 15 edits).

### PA-2 (P2, S) · Prior RTH close / settlement (ORG) captured by session time, as ICTPD-6's gap-fill object [A, CORRECTED semantics, timing and gate; merged with ICTPD-6 / CL-4]

**Problem.**
- Brooks's "yesterday's close" and ICT's ORG are missing.
- On 23-hour futures charts no chart gap exists (1.7), so ICTPD-6's time-break detector never creates the ORG.
- A's registry implementation would give it trade-through liquidity semantics (step 11 makes kind 0/1 with a zone beyond the price), but every supporting test measured a **touch**.

**Inputs** (`G_KEY`, shared with ICTPD-6 / CL-4 when they land):

```pine
bool   useORG  = input.bool(true, "Prior RTH Close (ORG / gap fill)", group = G_KEY, display = display.none,
  tooltip = "Previous regular-session close as a fill target from the next RTH open, only after a real gap. Works on 23-hour futures charts.")
string sessRTH = input.session("0930-1600", "RTH Session", group = G_KEY, display = display.none)
```

**SERIES** (global scope, next to 948-950; called on every bar):

```pine
// close captured from the last bar that OPENS inside RTH; RTH start detected on the first bar that CLOSES inside RTH
// (time() tests the bar's open time, time_close() its close time: on 1H the 09:00 bar is the first RTH bar)
f_rthClose(string sess, string zone) =>
    bool inO = not na(time(timeframe.period, sess, zone))
    bool inC = not na(time_close(timeframe.period, sess, zone))
    var float c  = na
    var int   cb = na
    if inO[1] and not inO
        c  := close[1]
        cb := bar_index - 1
    [inC and not inC[1], c, cb]
[rthOpen, rthC, rthCB] = f_rthClose(sessRTH, tz)
bool orgOK = useORG and intraOK and (syminfo.type == "futures" or syminfo.type == "stock" or syminfo.type == "index" or syminfo.type == "fund" or syminfo.type == "dr")
```

**ENGINE** (new step 12c, after ICTPD-6's step 12b, or after 1866 if ICTPD-6 is not built):

```pine
if orgOK and rthOpen and not na(rthC) and not na(aPDH) and not na(aPDL)
    // one ORG at a time: drop yesterday's
    if pool.size() > 0
        for i = pool.size() - 1 to 0
            Level q = pool.get(i)
            if (q.kind == 8 or q.kind == 9) and q.src == 13 and q.id != activeId
                pool.remove(i)
    float gSz = math.abs(close - rthC)
    bool  up  = rthC > close
    if gSz >= math.max(gapMinD * (aPDH - aPDL), 0.5 * atr) and (up ? high < rthC : low > rthC)
        float hw = 0.05 * atr
        nextId += 1
        Level og = f_newLevel(nextId, up ? 8 : 9, 13, rthC + hw, rthC - hw, rthC, f_x(rthCB), bar_index, coilScore, indScore)
        og.hlMult := math.sqrt(math.max(1.0, 86400.0 / chartS))
        pool.push(og)
```

- **Gap gate [NEW-B].**
  - T5: −5.3 pp under 0.5 ATR, +4.2 to +4.8 pp at 0.5-2 ATR.
  - ICTPD-6: gaps ≥ 0.10 × the prior-day range fill +7.4 pp; small gaps nothing.
  - The gate uses ICTPD-6's `gapMinD` (0.10 × prior-day range, TF-independent), floored at 0.5 chart ATR.
- **Kinds.** 8 (above) / 9 (below) with src 13, exactly as ICTPD-6 specifies:
  - names `src == 13 ? "ORG"`;
  - touch semantics through `isArray()`;
  - exempt from CE partial fill (PA-1 step 5 adds `kind <= 7` at 1566);
  - exempt from the origin lockout;
  - grp() → family 2 (or CL-4's SETT family).
- **Life.** It lives until touched (step 3 removes it), or until the next RTH open replaces it. T5 measured "rest of session" (K = 6 on 1h) and K = 30 bars; both are positive.
- **Settlement vs last trade.** On TradingView futures, the daily bar may use the settlement as the close. The RTH last-trade close captured here differs by a tick or two. CL-4 prefers the settlement; the measured effects are the same within noise.

**Ledger.**
- Family 2 (or SETT). It **must** be graded against a clock-matched baseline (TIME-2 / QPOT-03): the naive baseline overstates the edge about 3× (T5).
- Until that lands, the family edge will read optimistic. The tooltip says so.

**Evidence.** Moderate (T5; CL settlement +3.46 pp z 3.7; ICTPD gaps +7.4 pp z 2.2; NDX cash +7.9 pp z 4.5).

**Risk.**
- Symbols whose RTH is not 09:30-16:00 ET need the input changed.
- Crypto and FX are excluded by the `syminfo.type` guard.
- The effect may be "prior-day value" in general (CL: `dayEQ` +3.95 pp), so CL's proposals and this one should share a ledger family to measure the overlap.
- `time_close()` on the realtime bar of tick/range charts returns `na` (docs, `reference/time.md`). The engine runs on time-based charts only; `intraOK` already excludes others.

**Effort.** S: about 30 lines, on top of ICTPD-6's kinds.

### PA-3 (P3, S) · Leg-reach readout: "reaches the target before a k-ATR pullback", graded by the ledger [A, validated by B; simplified; priority lowered]

**Why.**
- This is the honest answer to "will this leg get there?". B1 shows it is calibrated without tuning (random levels within 0.5 pp; pools 0.5-2.8 pp optimistic).
- It answers a different question from the H-bar PoT: it accounts for a pullback, not for time.
- **[CORRECTED priority]** P3, not P2. It changes no target choice. It is informationally equivalent to distance plus pullback depth. And on intraday futures it is miscalibrated by session hour (P(OS ≥ 1δ) 0.33-0.45) until δ is on a volatility clock.

**Function** (PURE HELPERS; θ fixed at 1 per B1 (e)):

```pine
// P(target before a pullback of dl from the leg's running extreme M); price p; side +1 = up-leg.
f_legReach(float tgt, int side, float M, float p, float dl) =>
    float r = na
    if dl > 0
        float u = math.max(0.0, side * (M - p))
        float q = math.max(0.0, dl - u)
        float y = side * (tgt - M)
        r := y > 0 ? (q / dl) * math.exp(-y / dl) : q / math.max(q + side * (tgt - p), 1e-9)
    r
```

**Use.**
- When `zzMode == activeLv.side`: `pLeg = f_legReach(activeLv.nearEdge(), activeLv.side, zzExt, close, zzK * atr)`. Otherwise the readout shows "—" (the leg toward the target has not started).
- Terminal HUD, after the PoT line (2240): `LEG   41% before a 2.0-ATR pullback`.
- Clean: tooltip only.
- **[NEW-B]** Once QPOT-03 / TIME-2 provide a volatility-clock multiplier `vc(t)` (expected next-hours volatility ÷ ATR), use `dl = zzK * atr * vc`. That fixes the session-hour bias.

**Ledger.**
- `Trial` gains `float pLeg = na`, `float lgExt = na`, `float lgDl = na`, `int lgY = -1`.
- `f_step` (1434-1459), while `lgY == -1`:
  - update `lgExt` with the favourable extreme;
  - `lgY := 1` on hit;
  - `lgY := 0` when `t.side * (lgExt - (t.side > 0 ? low : high)) >= lgDl` first;
  - same-bar order follows the existing O-L-H-C rule (`advFirst`, 1441).
- `f_book`: accumulate `[n, Σp, Σy, Σ(p−y)²]` in a 4-float `legSt`.
- Panel row (Full view): `LEG  pred 41% · obs 39% · Brier 0.21 (n 87)`.

**Evidence.** Strong for the law (L5, L6, T1); moderate for this readout's calibration (B1: about 40,000 samples per set, 1h and 5m).

**Risk.**
- Pools read 1-3 pp optimistic (B1 c2). The ledger row shows it.
- The session-hour bias stands until the vol clock lands.
- It adds HUD length, so it is Terminal only.

**Effort.** S: about 30 lines; reuses the zigzag.

### PA-4 (P3, S) · Displacement in the legacy draw vector: Brooks-strength, range-breaking bars only [A✓, scoped to legacy D]

**Problem.**
- `dispUp/dispDn` (902-904) fire on 1.2-ATR bodies with no close-location or structure requirement.
- T3: geometry below 2 ATR. **[NEW-B]** B1/B2: reversal speed and leg direction carry no side or reach information.
- REG-3 gates D in its default mode, so this matters only when a user switches the gate off (legacy behaviour) or when BIAS-2 / ICTS-1 keep D.

**Spec.**

```pine
float brkMult = input.float(2.0, "D · Breakout Body (x ATR)", minval = 0.5, step = 0.25, group = G_FLOW, display = display.none,
  tooltip = "Displacement votes in the draw vector only for a range-breaking trend bar: body >= this x ATR, closing in its outer quarter, beyond the prior 20-bar extreme.")
// reuse hh20 / ll20 (883-884) instead of new ta calls: [1] excludes the current bar
bool brkUp = close > open and bodyB >= brkMult * atrP and bRat >= 0.6 and close >= high - 0.25 * rngB and close > hh20[1]
bool brkDn = close < open and bodyB >= brkMult * atrP and bRat >= 0.6 and close <= low + 0.25 * rngB and close < ll20[1]
```

- **[NEW-B]** It reuses the existing `hh20` / `ll20` series (883-884) with `[1]` instead of two new `ta.highest/lowest` calls.
- Replace `dispUp/dispDn` with `brkUp/brkDn` in step 1 (1536-1541). Keep `dispMult` for FVG quality (912) and the HTF FVG request (939).
- Lower the `wM` default (156) from 0.20 to 0.10.

**Measurement.** Use ICTS-1's skill gate or REG-2's ledger split: count `drawFlip` events and edge by D component.

**Evidence.** Weak (T3 per-series inconsistency; B1, B2 nulls).

**Risk.** Fewer displacement events. Almost no effect when REG-3's gate is on.

**Effort.** S.

### PA-5 (P3, M) · Measured-move and ICT −1 SD rules as shadow roles in the candidate ledger, plus zero-prior leg features [A, re-mapped onto CAL-3's final design]

**Why.**
- Users trained on Brooks, Bulkowski or ICT ask: "does the engine beat just aiming at the measured move?".
- The random-level baseline answers "better than chance", not "better than my rule".
- The small T3/T4/B1/B2 effects belong in a learner with zero prior weight, not in hand-set multipliers.

**Spec.**
1. **Roles** (CAL-3 `Probe.role`, final numbering 0-5). Add:
   - **6 = "MM rule"**: MM 1.0 of the current zigzag leg (PA-1 ladder, even when price is not in discovery);
   - **7 = "ICT −1 SD"**: EX1.
   - Open them with the same cadence and grading as role 2 ("nearest") and role 3 ("random candidate").
   - `rlSt` grows from 6×5 to 8×5.
   - Panel: `vs MM-rule +x pp · vs ICT −1SD +y pp · vs nearest +z pp`.
2. **Features** for the CAL-9 vector `x` (prior weight 0), measured per candidate:
   - last breakout bar body/ATR and close location; 20-bar range-break flag and range width in ATR (T4 1, 1b);
   - bars since the last range breakout, and whether it closed back inside within 5 bars (T4 1, B3);
   - zigzag leg progress `u/δ` and the candidate's `y/δ` (1.9; B2 at the extreme);
   - **[NEW-B]** leg is with-trend (HL→up / LH→down) flag (B1 b: +2.6 pp vs null);
   - **[NEW-B]** candidate is a pool beyond the running extreme vs elsewhere (B1 c2: −1 to −2 pp);
   - "within 0.1 ATR of MM 1.0 / EXT −0.27 / −0.62 / −1": a per-chart test of the Fibonacci-confluence claim that T1/T2 reject on average.

**Evidence.** Weak for the features; moderate for the infrastructure (CAL).

**Risk.** More state per probe; CAL-3's `NPROBE = 256` cap applies. Depends on CAL-3 / CAL-9.

**Effort.** M: S for the roles once CAL-3 exists, M for the features.

---

## 5. Considered and rejected (do not implement)

| Idea | Why not | Numbers |
|---|---|---|
| Fibonacci extensions or ICT −0.27 / −0.62 / −1 / −2 / −2.5 / −4 SD as scored targets or confluence anchors (`anchors`, 1931) | No level effect; flat across ratios; ICT SD is just range multiples | T1, T2, L1, L2 (weak-moderate), L22 |
| AB=CD / leg 1 = leg 2 as a scored source outside price discovery | Random-level rate; no stall; P(leg 2 ≥ leg 1) = null | T1, T2; Bulkowski full leg 45-56% |
| Fibonacci retracement / OTE levels | Entry concept; continuation falls smoothly with depth | ICTS 1.10, L3, T1 |
| Elliott counts and targets | Subjective; no controlled test; ratios rejected | L9, L9b, T1 |
| Harmonic patterns | Rare, small n, researcher degrees of freedom | L10, T1 |
| Breakout-bar measured move as a target or a probability bonus | Geometry; forum backtest 50-52% | T3, L11 |
| Requiring a follow-through bar | Raises the win rate only through geometry | T3 |
| H2 / L2 second-entry bias | Geometry | T3 |
| 20-gap-bar / moving-average magnet | Random-level rate; not a Brooks standalone magnet | T3, 1.5 |
| Always-In direction as a bias row or D component | Zero side information | T4 (2) |
| **[NEW-B]** Zigzag leg direction or "price is at the leg extreme" as a side vote | Geometry; at the 1h extreme slightly *against* the leg | B2 |
| **[NEW-B]** "Failed breakout → other side of the range" as a target bonus | Geometry | B3 |
| **[NEW-B]** Expecting legs to end just beyond a swept pool (sweep-and-reverse length rule) | No excess vs random levels | B1 (d) |
| **[NEW-B]** Volume or volatility "climax" at a leg end as a predictor | Selection artefact; a random walk reproduces it | L19 |
| **[NEW-B]** Per-chart learned overshoot scale θ, offsets, or trend-split θ in PA-3 | No Brier gain | B1 (e) |
| Measuring-gap projection targets | Random-level rate on 1h; 5m clock confound | T4 (3) |
| Range-height measured move as a level | Small race effect only | T4 (1b), WYK §2.5 |
| ETA from leg-time symmetry | The null reproduces the correlation | T4 (4) |
| Conditioning reach or PoT on the previous leg's size | No leg memory | T1 |
| ADR / ATR projection caps | Sign reversed | SESS §2.7 |
| Dow confirmation (SMT) | Second symbol | ICT note |

---

## 6. Notes for implementers

- **Shared zigzag.** PA-1, PA-3 and PA-5 use one zigzag (section 4 preamble). Test it against `pa_tools/palib.py: zigzag` on exported bars.
- **Central kind/src map** (from ICTPD-6 final, extended by B):
  - kinds: 0-7 as now; 8/9 = gap-fill above/below (ICTPD-6, includes ORG); **10/11 = projections above/below (PA-1)**;
  - src: 0-7 as now; 8/9/10 = 20/40/60-day extremes (ICTPD-5); 11 = NDOG, 12 = NWOG, 13 = ORG/settlement (ICTPD-6 + CL-4 + PA-2); **14-17 = MM 1.0 / EXT −1 / MM 1.618 / LEG +1δ (PA-1)**;
  - update `f_newLevel` (1085), `f_tierW` (506-516), `f_levelName` / `f_shortName` (518-541), `f_kzAff` (597-602), `grp()` (635-636) and `f_grpName` (543-549) together.
- **Ledger families.** Introduce `NFAM` / `ALL` once (PA-1 step 5) before any proposal adds a family.
- **Clock-matched baselines.** Every session-anchored level (PA-2, ICTPD-6, CL-4, TIME-6) must be graded with a clock-matched baseline (T5 lesson: naive baselines overstate about 3×). Everything else uses the plain random-level baseline.
- **Pine constraints.**
  - No new `request.*` calls: PA-2 uses `time()` / `time_close()` with a session string, as 971-974 do.
  - O(1) state.
  - No forward references: helpers in PURE HELPERS, state in STATE, updates inside the confirmed-bar engine block, the session series at global scope.
  - Only `math.exp` and `math.max`.
- **Test-data hygiene [NEW-B].** `amt_data/cme/GC/GC_1h_*.csv` mixes contracts (1,429 bars with volume ≤ 10, 70-120 ATR jumps). Filter `volume > 10`, or exclude GC 1h, before using it for any verification.

---

## 7. Sources

**Published** (most hosts were unreachable from both sessions; "via search summary" = WebSearch result text; "full text" = read through the paper index):
- Batchelor, R., Ramyar, R. (2006). Magic numbers in the Dow. Cass Business School, City University London (via search summary).
  - https://openaccess.city.ac.uk/id/eprint/16276/
  - https://www.researchgate.net/publication/228713810_Magic_numbers_in_the_Dow
- Glattfelder, J. B., Dupuis, A., Olsen, R. B. (2011). Patterns in high-frequency FX data: discovery of 12 empirical scaling laws. *Quantitative Finance* 11(4): 599-614. arXiv:0809.1040 (full text). https://arxiv.org/abs/0809.1040
- Glattfelder, J. B., Golub, A. (2022). Bridging the Gap: Decoding the Intrinsic Nature of Time in Market Data. arXiv:2204.02682 (full text). https://arxiv.org/abs/2204.02682
- Golub, A., Chliamovitch, G., Dupuis, A., Chopard, B. (2016). Multi-scale representation of high frequency market liquidity. *Algorithmic Finance* 5(1-2): 3-19. arXiv:1402.2198. https://arxiv.org/abs/1402.2198
- Glattfelder, J. B., Olsen, R. B. (2024). The Theory of Intrinsic Time: A Primer. arXiv:2406.07354. https://arxiv.org/abs/2406.07354
- Houweling, T. (2025). The Hidden Constant of Market Rhythms: How 1−1/e Defines Scaling in Intrinsic Time. arXiv:2511.14408. https://arxiv.org/abs/2511.14408
- Mayerhofer, E. (2019). Three essays on stopping (Taylor 1975, Lehoczky 1977). arXiv:1909.13050. https://arxiv.org/abs/1909.13050
- Filimonov, V., Sornette, D. (2011). Spurious trend switching phenomena in financial markets. arXiv:1112.3868 (full text). https://arxiv.org/abs/1112.3868
- Preis, T., Schneider, J. J., Stanley, H. E. (2011). Switching processes in financial markets. *PNAS* 108(19): 7674-7678. doi:10.1073/pnas.1019484108
- Schmidhuber, C. (2021). Trends, reversion, and critical phenomena in financial markets. arXiv:2006.07847. https://arxiv.org/abs/2006.07847
- Adegboye, A., Kampouridis, M. (2021). Machine learning classification and regression models for predicting directional changes trend reversal in FX markets. *Expert Systems with Applications* 173: 114645. https://repository.essex.ac.uk/30788/
- Adegboye, A., Kampouridis, M., Otero, F. (2021). Improving trend reversal estimation in forex markets under a directional changes paradigm with classification algorithms. *Int. J. Intelligent Systems*. https://kar.kent.ac.uk/89886
- Brown, S., Goetzmann, W., Kumar, A. (1998). The Dow Theory: William Peter Hamilton's Track Record Reconsidered. *J. Finance* 53: 1311-1333.
  - https://onlinelibrary.wiley.com/doi/10.1111/0022-1082.00054
  - https://viking.som.yale.edu/?p=86
  - NYU Stern news (4.4 pp/yr, per A): https://www.stern.nyu.edu/experience-stern/news/prof-stephen-brown-s-research-dow-theory-featured
- Osler, C. L. (2003). Currency orders and exchange rate dynamics: an explanation for the predictive success of technical analysis. *J. Finance* 58(5): 1791-1819.
  - https://ideas.repec.org/a/bla/jfinan/v58y2003i5p1791-1819.html
  - NY Fed SR125: https://www.newyorkfed.org/research/staff_reports/sr125.html
- Osler, C. L. (2000). Support for resistance: technical analysis and intraday exchange rates. FRBNY *Economic Policy Review* (via ACAD).
- Westland, J. C. (2024). Periodicity, Elliott waves, and fractals in the NFT market. *Scientific Reports* 14. PMC10891072. doi:10.1038/s41598-024-55011-x
- MQL5 statistics blog (28 Sep 2026). Fibonacci extensions reach 1.618 less often than a random walk: 26,795 double bottoms (via search summary). https://www.mql5.com/en/blogs/post/776239
- Tradeify (2026). Fibonacci Retracements and Extensions Put to the Test. https://tradeify.co/education/fibonacci-retracements-and-extensions
- Gurrib, I., Nourani, M., Bhaskaran, R. K. (2022). Energy crypto currencies and leading U.S. energy stock prices: are Fibonacci retracements profitable? *Financial Innovation* 8. doi:10.1186/s40854-021-00311-8
- CXO Advisory, Guru Grades, Robert Prechter (via search summary):
  - https://www.cxoadvisory.com/individual-gurus/robert-prechter/
  - https://www.cxoadvisory.com/gurus/
  - Kiplinger: https://www.kiplinger.com/article/investing/T038-C000-S002-which-market-gurus-get-it-right-the-most.html
- HKUST independent study, Trading harmonic patterns. https://cse.hkust.edu.hk/~rossiter/independent_studies_projects/trading_harmonic_patterns/trading_harmonic_patterns.pdf
- Researcher degrees of freedom, Gartley patterns. https://aaronmams.github.io/Researcher-Degrees-of-Freedom,-Gartley-Patterns,-and-Porn
- Bulkowski, T. (via search summary):
  - measured move up: https://thepatternsite.com/mmu.html
  - measured move down: https://thepatternsite.com/mmd.html
  - measured move retrace: https://www.thepatternsite.com/MMRetrace.html
  - measure rule: https://www.thepatternsite.com/measure.html
  - Pattern Review 5: https://thepatternsite.com/PatternReview5.html
- Brooks, A. *Trading Price Action: Trends*; *Trading Price Action: Trading Ranges* (Wiley 2012), Part II "Magnets: Support and Resistance".
  - https://www.oreilly.com/library/view/trading-price-action/9781118172339/OEBPS/9781118172339_epub_c_02.htm
  - https://www.oreilly.com/library/view/trading-price-action/9781118172339/OEBPS/9781118172339_epub_c_07.htm
  - https://www.oreilly.com/library/view/trading-price-action/9781118172339/OEBPS/9781118172339_epub_c_10.htm
  - https://www.oreilly.com/library/view/trading-price-action/9781118172339/OEBPS/9781118172339_epub_c_13.htm
- Brooks Trading Course forum and analysis pages (via search summary):
  - BO 60% "is it really": https://www.brookstradingcourse.com/support-forum/41-trading-breakouts/bo-has-60-probability-of-reaching-mm-target-but-is-it-really/
  - measured move: https://www.brookstradingcourse.com/support-forum/general-trading-discussion/measued-move/
  - breakout fail: https://www.brookstradingcourse.com/support-forum/12-market-cycle/breakout-fail/
  - always in confusion: https://brookstradingcourse.com/support-forum/13-always-in/always-in-confusion
  - magnets: https://www.brookstradingcourse.com/support-forum/19-support-and-resistance/magnets/
  - 20-gap-bar: https://www.brookstradingcourse.com/support-forum/general-trading-discussion/20-gap-bar-buy-and-ema-gap-bar-buy/
  - MoneyShow 80% rule: https://www.moneyshow.com/articles/tradingidea-48940
- ICT SD projections (practitioner; via search summary):
  - https://www.luxalgo.com/library/concept/standard-deviation-projections/
  - https://backtrex.com/en/blog/ict-standard-deviation-projection-price-targets
  - https://innercircletrader.net/tutorials/ict-fibonacci-levels/
- Gap-fill statistics (practitioner):
  - https://www.tradingview.com/script/32pGGSWx-Gap-Fill-Probability-Statistics-ES-NQ/
  - https://marketchameleon.com/Instructional-Stock-and-Options-Trading-Videos/446/Analyzing-SPY-Large-Opening-Gaps-Using-Market-Chameleon
  - https://linnsoft.com/homework

**Pine Script v6 docs** (local mirror `docsrc/jabez4jc_pinescriptv6/`):
- `concepts/sessions.md`: futures ETH = the "regular" session; `session.isfirstbar_regular` row; the time()/time_close() session-membership example.
- `reference/time.md`: `time(timeframe, session, timezone)` and `time_close(...)` return na outside the session.
- `reference/syminfo.md`: `syminfo.type` values.

**Sibling reports used** (`brief/study/`):
- `ict_struct.final.md` (S6, S8, S10, §2.2, ICTS-1);
- `ict_pd.final.md` (ICTPD-5, ICTPD-6, kind/src map);
- `classic_levels.md` (CL-4, settlement +3.46 pp, `dayEQ` +3.95 pp, P12);
- `quant_regime.final.md` (REG-2, REG-3);
- `calib_ml.final.md` (CAL-3 Probe roles, CAL-9);
- `quant_pot.final.md` (QPOT-01, QPOT-03);
- `ict_time.final.md` (TIME-2, TIME-6);
- `orderflow_micro.final.md` (OF-4, Osler quantified);
- `wyckoff_sd.final.md` (§2.5);
- `academic_sr.final.md` (Osler 2000, Kavajecz);
- `session_stats.final.md` (§2.7, Linnsoft);
- `competitors.final.md` (COMP-3/6).

**Study code.**
- A: `study/pa_tools/palib.py`, `t1_legs.py`, `t2_proj.py`, `t3_brooks.py`, `t4_misc.py`, `t5_pdc.py`, `t6_blind.py`.
- B: `study/pa_b_tools/b1_legreach.py`, `b1_legreach_noGC.py`, `b2_legside.py`, `b2_legside_noGC.py`, `b2_series.py`, `b3_failbo.py`.
- Outputs: `out_t*` and `out_b*` next to the scripts.
