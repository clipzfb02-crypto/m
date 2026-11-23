# Wyckoff Method and Supply/Demand: study for the DOL Engine v2

Domain: the Wyckoff method (trading ranges, accumulation/distribution schematics, PS/PSY, SC/BC, AR, ST, spring/shakeout, UT/UTAD, test, SOS/SOW, LPS/LPSY, JAC/BUEC, composite operator, cause and effect with point-and-figure counts, effort vs result) and supply/demand zone trading (rally-base-drop zones, departure strength, time at level, fresh vs tested). The question throughout: does any of it help predict **which liquidity price takes next, when, and how likely**?

Line numbers refer to `brief/baseline_v2.pine` (identical to `indicators/dol_engine.pine`). Sibling studies are cited by proposal id where they already cover a topic: `ict_liq.md` (E1-E15, ICT-1..8), `ict_pd.md` (ICTPD-1..10), `ict_struct.md` (ICTS-1..7), `bias_dol.md` (BIAS-1..7), `smc_impl.md` (SMC-1..7), `ict_time.md` (TIME-1..9).

Reproduction: every number tagged **[this study]** comes from the scripts in `study/wyckoff_tools/` run on the data sibling studies already used (`study/bias_data/`: S&P 500 and NASDAQ daily 1999-2018 with volume, GOOG daily 2004-2013 with volume, EURUSD 1H 2017-18 with tick volume; `sim/data/`: NQ, GC, EURUSD 1H 2024-26, about 11,400-12,300 bars each, no volume). Run `python3 -I <script> [args]`. Outputs are in `out_*.txt` next to the scripts.

| Script | What it tests | Output files |
|---|---|---|
| `wyck.py N K kmax` | first-passage races after range events (spring, upthrust, failed breakout by close, spring+SOS, upthrust+SOW, partial rise/decline, first edge of a new range, climax → automatic rally) vs gambler's-ruin geometry and vs bar-shuffled nulls | `out_N30_K30.txt`, `out_N20_K30_k6.txt`, `out_N30_K30_k8.txt`, `out_N50_K30_k8.txt`, `out_N30_K60_k8.txt` |
| `magnet.py N K` | is a Wyckoff level traded through within K bars more often than a random level at the same ATR distance (the engine's own ledger baseline)? | `out_magnet_N30_K30.txt`, `out_magnet_N20_K30.txt` |
| `density.py K` | the engine's `coilScore` / `indScore` (886-895) at pivot birth vs later reach | `out_density_K30.txt` |
| `agetest.py K` | freshness (pool age) and engine-defined "tests" vs reach | `out_age_K30.txt` |
| `eqtest.py K` | equal highs/lows (engine merge rule, `eqTol` 0.10 ATR) vs reach | `out_eq_K30.txt` |
| `breakout.py N K` | cause and effect (range duration/width), measured move, throwback | `out_breakout_N30_K30.txt` |
| `effort.py K` | distribution of the engine's density inputs; volume at swept pools (effort vs result) | `out_effort_K30.txt` |
| `induce2.py` | de-saturated inducement and percentile coil definitions vs reach | `out_induce2.txt` |

---

## 0. Executive summary

1. **Wyckoff range events carry no "which side next" information beyond race geometry.** On seven datasets (daily equity indices and GOOG; hourly EURUSD, NQ, gold), across four range-detector settings:
   - After a **spring**, the opposite range edge is taken before the spring low only **12-37%** of the time. Gambler's-ruin geometry predicts **16-26%**. Pooled excess over a bar-shuffled null is **−0.075 to +0.016** (SE about 0.04) [this study].
   - **Upthrusts** score −0.034 to +0.037. **Spring + SOS** scores −0.145 to −0.006. **Partial rise/decline** (Bulkowski's 74-91% "success") is geometry; the excess is inconsistent in sign (−0.135 to +0.080).
   - The textbook Wyckoff reading "spring → target the opposite side of the range" is **not supported**. Price behaves as if the spring were not there.
2. **Wyckoff levels are reached at random-level rates.** Range highs and lows (2+ touches), spring targets, upthrust targets, spring/UT extremes and the 50% automatic-rally level after a climax are all traded through within 30 bars at the same rate as a random level at the same ATR distance (the engine's ledger baseline). Edges are **−0.07 to +0.02**, mostly ±0.02 with n = 140-970 [this study]. **More touches on a range edge do not make it a bigger magnet**: 2 touches +0.000, 3 touches −0.031, 4+ −0.084 (small n).
3. **Two of the engine's density inputs carry no information.**
   - **`indScore` is saturated.** It is ≥ 2/3 on **86-97%** of bars and exactly 1 on **64-90%**. In practice it is a constant.
   - **`coilScore`** varies, but pivots born from high coil are reached slightly **less** often than other pivots (edge −0.019 vs −0.008).
   - De-saturated versions (a real 20-bar sweep by ≥ 0.10 ATR; coil as a 500-bar percentile) are also flat or slightly negative [this study].
   - **Equal highs/lows** (engine rule) are reached slightly less than single pivots: −0.028 ± 0.013 vs −0.007 ± 0.003. That corroborates sibling E6 (< 1 pp). The density pillar's `0.9 × eqCount`, `0.35 × tests`, `0.25 × coil` and `0.15 × induce` (682-683) together reward properties that do not raise reach within H bars.
4. **"Stops accumulate with age" is not supported.** Pool age has no effect on reach: ≤ 30 bars −0.011, 31-150 −0.007, 151-500 −0.018, > 500 −0.001 (36,724 samples, 4,783 pools, cluster-robust SEs about 0.005). Yet the engine's liquidity freshness gives a brand-new pool about 0.43 and a 100-200-bar pool about 0.85 (671). That costs fresh pools about **4 score points**, the size of the switch hysteresis, with no evidential basis. Older pools within 1 ATR are reached somewhat *less* (−0.075 vs −0.003), consistent with S/R memory (Chung & Bellotti, sibling E5).
5. **Cause and effect is not supported in a testable form.**
   - The measured move (range height projected from the breakout edge) is reached before the opposite edge at geometry rates: 0.571 vs 0.565; null-adjusted +0.03 ± 0.02.
   - Longer or wider ranges do not produce more extension (+0.015 vs −0.003).
   - Throwbacks to the broken edge happen at random-level rates (0.870 vs 0.872) [this study].
   - Point-and-figure count accuracy has **no published test at all**. A leading Wyckoff educator states there are no public quantitative backtests.
6. **Effort vs result (volume) adds nothing measurable at 1H/daily.** At swept pools (n = 1,823), continuation 1 ATR beyond the sweep extreme does not depend on sweep-bar volume. **Rejected** sweeps (spring-like) are followed by *continuation* slightly more than a random level: +0.039 ± 0.016. That is the opposite of the engine's "raid rejects = reversal" vote (1581), and it corroborates sibling BIAS-4 / ICTS-2 and E7 (Mahadzva, 65/66 folds favour continuation).
   - Strong published evidence that high-volume extreme moves partly reverse exists only at **minute scale**: Campbell-Grossman-Wang 1993; the drift-burst studies (≥ 65% reversals, R² 25-40% at 5 min); Zawadowski et al. (14-25% of a 60-minute shock reverts within an hour). That is the Wyckoff "automatic rally" in microstructure form, but it is too short-lived for an H = 30-bar target on 15m-1H charts.
7. **Supply/demand zone "odds enhancers" have no quantitative support.** Sam Seiden's odds enhancers (strength of departure, time at base, freshness) have no published statistics. One practitioner site states it outright: "Most guides prefer fresh zones, but that's an assumption, not a measured result". Sibling studies found arrays are reached at random-level rates. Departure size *reduces* near-term fill (ICTPD-1), and fresh order blocks *react* slightly more (Nordman: +7.5% vs +4.0% edge ratio at 1 min). Freshness therefore matters for reaction, not for reach.
8. **What this domain does contribute.**
   - **Honest subtraction.** Remove or neutralise the density and freshness terms that reward nothing (WYK-1, WYK-2).
   - **Regime structure.** A trading-range state lets the engine stop trusting the draw vector D inside ranges, where it has no information. It can then fall back to race geometry and measure in-range vs trending accuracy separately (WYK-3).
   - **Trader-facing vocabulary.** Spring, UTAD, failed breakout and range edges can be labels and alerts carrying zero forecast weight, each shown with its measured per-chart rate against geometry (WYK-4).
   - Volume features belong in a learned candidate ledger with zero default weight (WYK-5).
9. **Grades.**
   - Wyckoff schematic claims as forecasts: **none to weak** (practitioner consensus; no public backtests).
   - Rectangle/range statistics: **moderate** (Bulkowski, large n, no random baseline) and **strong** for "rectangle-conditioned return distributions differ from unconditional" (Lo-Mamaysky-Wang 2000). Note that this is shape, not direction.
   - Climax → partial reversal: **strong** at minute scale, **none** at 1H/daily [this study].
   - This study's own nulls: **moderate** (seven datasets, two independent baselines, shuffled nulls, multiple parameterisations; daily and hourly bars only).

---

## 1. Concepts: precise definitions and parameters

Notation: `A` = ATR(14) (the engine's `atr`; `atrE` = max(ATR14, ATR200) for range gates). "Taken" = strict trade-through, matching the engine's liquidity rule (`touched`, 623-624). All detection is on confirmed bars.

### 1.1 Trading range (TR), creek and ice, phases A-E
- **Definition (Wyckoff Analytics, Pruden/Fraser school).**
  - A TR is where "the previous trend has been halted and there is relative equilibrium between supply and demand".
  - The TR is bounded by the SC low (plus ST lows) and the AR high in accumulation; mirror for distribution.
  - "Creek" is the resistance line of an accumulation range (AR high plus Phase B highs). "Ice" is the support line of a distribution range.
- **Phases.**
  - A: stopping the prior trend (PS, SC, AR, ST).
  - B: building the cause, with multiple STs and upthrust-like actions at the top. Volume on down-swings should shrink.
  - C: the test, either a spring/shakeout or, in schematic #2, a higher-low test with no spring.
  - D: SOS/LPS. "During Phase D, the price will move at least to the top of the TR."
  - E: markup outside the range.
  - Re-accumulation ranges are shorter and smaller, and Phase A looks like distribution.
- **Algorithm (Pine-feasible, causal, used in this study's `wyck.tr_box`).**
  1. At confirmed bar `t`, `hi = highest(high, N)[1]` and `lo = lowest(low, N)[1]` over bars t−N..t−1.
  2. Qualify if `kmin·A ≤ hi − lo ≤ kmax·A` and each edge has at least `touch` touches. A touch is a bar whose high is within `tol·A` of `hi` (low within `tol·A` of `lo`), at least 3 bars after the previous counted touch.
  3. Freeze the box on the first qualifying bar. It lives while closes stay inside.
- **Parameters seen in implementations.**
  - This study: N = 20/30/50, kmin 1.5, kmax 6-8, tol 0.25, touch 2.
  - FibAlgo "Wyckoff Spring & Upthrust": lookback 50, min TR width 20 bars, ranges > 8 ATR filtered out as trends.
  - trendcraft `wyckoffPhases`: swing 5, minRangeBars 20, tolerance 0.5 ATR, volume MA 20.
  - MQL5 article 22628: 15 bars of prior trend, range 10-60 bars, 20-400 pips tall.
  - Lo-Mamaysky-Wang rectangle: 5 alternating extrema, tops within 0.75% of their mean, bottoms within 0.75%, lowest top > highest bottom.
- **Edge cases.**
  - The box must be frozen: a rolling Donchian box swallows springs.
  - A spring does not end the range. A close outside for ≥ 2 bars does.
  - Ranges taller than about 8 ATR are trends.
  - Use the slow ATR for the width gate, so a quiet session does not disqualify a range.
- **Use for DOL (practitioner).** Range edges are the two obvious pools. Phase D "at least to the top of the TR" means the opposite edge is the target once the test is done.

### 1.2 Preliminary support/supply (PS/PSY), selling/buying climax (SC/BC), automatic rally/reaction (AR)
- **SC (Wyckoff Analytics).** "Widening spread and selling pressure usually climaxes, as heavy or panicky selling by the public is being absorbed … Often price will close well off the low." BC mirrors it and often coincides with good news.
- **AR.** The rebound after selling pressure dries up. Its high defines the TR top.
- **PS.** The first substantial buying after a prolonged decline, with expanding volume and spread.
- **Algorithm** (implementations converge on this; used in `wyck.py`):
  - SC at bar t: `low[t]` is the lowest low of 20 bars; `high − low ≥ 1.5·A[1]`; `volume ≥ 2·sma(volume,20)[1]` where volume exists; close location `(C−L)/(H−L) ≥ 0.5` (closes off the low); and a prior leg `highest(high,21) − low ≥ 4·A`.
  - AR target: the 50% retracement of that leg.
  - Mirror everything for BC.
  - StockSharp "Volume Climax Reversal" uses volume > 2× SMA20; fis_wse uses "Climax vol multiplier … volume must exceed MA × this".
- **Use for DOL (practitioner).** After an SC, the AR's high is the first upside draw and the SC low is re-tested (ST). After a BC, the reverse.

### 1.3 Secondary test (ST) and tests in general
- **ST.** Price revisits the SC area on "significantly diminished" volume and spread, "generally stopping at or above the same price level as the SC". "If the ST goes lower than that of the SC, one can anticipate either new lows or prolonged consolidation."
- **Test (general).** "Large operators always test the market for supply throughout a TR … a successful test … typically makes a higher low on lesser volume."
- **Algorithm.** Within an active TR, a swing low at or above `lo − 0.25·A` with volume < 1.0× SMA20 and range < 1.0·A. In this study, "tests" of a pool follow the engine's own rule (650-656): a bar within 0.30·A of the pool that does not take it, ≥ 3 bars after the last test.
- **Use for DOL.** A successful ST/test says the low will hold, so target the top. A failed ST (lower low) means the low is the draw again.

### 1.4 Spring / shakeout and upthrust / UTAD
- **Spring.** "A price move below the support level of the TR (established in Phases A and B) that quickly reverses and moves back into the TR … a bear trap." It is "not required": schematic #2 has none.
- **Upthrust (UT).** The mirror at resistance. **UTAD** = an upthrust after distribution, late in the range; FibAlgo defines it as an upthrust that exceeds a previous upthrust high.
- **Types** (Robert Evans via Fraser and Villahermosa):
  - **#1 / terminal shakeout**: "wholesale breakdowns below support on volume that is much larger than that of prior downswings". It needs a later test.
  - **#2**: deeper penetration with some volume expansion. It needs a test.
  - **#3**: "a modest penetration of support … accompanied by volume that is relatively light". The classic entry.
  - Villahermosa adds that "volume is secondary information: what defines the quality of the shakeout is how price behaves after the breakout".
- **Algorithm** (this study; FibAlgo and fis_wse are equivalent):
  - Spring at bar t (frozen box): `low[t] < lo` (strict), `lo < close[t] < hi`, depth `(lo − low[t]) / A ≤ 1.5`.
  - Volume class by `vr = volume[t] / sma(volume,20)[1]`: ≤ 0.8 → #3, 0.8-1.5 → #2, > 1.5 → #1/SO. fis_wse caps spring volume at 0.7× MA.
  - FibAlgo allows recovery within 3 bars (a previous bar broke, the current bar closes back inside) and watches 15 bars for a test.
- **Close-based variant** ("failed breakout", Bulkowski's "bust"): a **close** below `lo`, then a close back inside within 3 bars. The extreme becomes the stop reference.
- **Use for DOL (the Wyckoff claim under test).** After a spring, the draw is the opposite edge (creek). After a UTAD, it is the range low (ice). The spring low is the invalidation.

### 1.5 Test of the spring, SOS/SOW, JAC/BUEC, LPS/LPSY
- **SOS.** "A price advance on increasing spread and relatively higher volume. Often a SOS takes place after a spring, validating the analyst's interpretation." **JAC** (jump across the creek) = the SOS that breaks the creek. **BUEC** (back-up to the edge of the creek) = the retest of the broken creek.
- **LPS.** "The low point of a reaction or pullback after a SOS … a pullback to support that was formerly resistance, on diminished spread and volume."
- **SOW / LPSY.** Mirror images. "The evidence that supply is clearly dominant increases … with a decline below the midpoint of the TR after a UT or UTAD."
- **Algorithm** (this study): spring + SOS = within 10 bars of a spring, a close above the range midpoint before the spring low is broken. Then race the range high against the spring low. Mirror for UT + SOW.
- **Use for DOL.** After a JAC the target becomes the next pool above the range. The BUEC/LPS is the entry, not the target.

### 1.6 Partial rise / partial decline (Wyckoff schematic #2's "test without a spring")
- **Bulkowski.** A partial decline is a move off the top trendline that turns "before coming close to the bottom trendline", in an established rectangle. It "predicts an immediate upward breakout". Partial rise is the mirror.
- **Algorithm** (this study): a 3-bar fractal low inside the box at more than `lo + 0.33·(hi − lo)`, with the previous N/3 bars having touched the top within tol. Race top vs bottom from the confirmation close.

### 1.7 Composite operator (composite man)
"All the fluctuations in the market … should be studied as if they were the result of one man's operations." This is an interpretive stance, not an observable, and it is unfalsifiable. No algorithmic content beyond what 1.1-1.6 already operationalise.

### 1.8 Cause and effect: point-and-figure horizontal count, measured move
- **Wyckoff law.** "The horizontal P&F count within a trading range represents the cause, while the subsequent price movement represents the effect."
- **Count procedure.**
  1. Count columns across the TR from the LPS (or spring) leftward, by whole "phases".
  2. Target = count × box size × reversal (usually 3) added to the low (or the LPS).
  3. "When the LPS occurs at [PS or SC levels], this tends to validate the count."
- **Pine feasibility.** Possible: build P&F columns from closes with box = k·ATR and reversal 3, as a stateful array on confirmed bars. Ambiguous phase selection makes it non-unique.
- **Measured move (Bulkowski rectangles).** Target = breakout edge ± range height. "Percentage meeting price target for up/down breakouts: 79%/55%" (rectangle bottoms) and 78%/54% (tops), on daily stocks in bull markets.
- **Use for DOL.** Cause sizes how far the next leg should reach. That is a magnitude target, not a liquidity pool.

### 1.9 Effort vs result; VSA; Weis waves; shortening of the thrust
- **Law.** Effort is volume; result is the price spread and close location. Heavy volume with little progress is absorption, meaning reversal risk. A big result on no volume is suspect.
- **VSA bars.**
  - No demand: a narrow up-bar on volume below the previous two bars.
  - No supply: the mirror.
  - Stopping volume: heavy volume on a down bar that closes off the low.
- **Weis wave.** Volume summed per swing, so successive waves can be compared. **Shortening of the thrust (SOT)**: successive pushes gain less distance; LuxAlgo says to look for it "after 3-4 up or down waves". LuxAlgo also calls Weis wave "descriptive", not predictive.
- **Algorithm.**
  - `vr = volume / sma(volume,20)[1]`, `sr = (high − low) / A`, close location `clv = (close − low) / (high − low)`.
  - Absorption bar: `vr ≥ 2` and `sr ≤ 0.8`.
  - Weis wave: accumulate volume between zig-zag pivots.
  - SOT: wave extension_k < wave extension_{k−1} < wave extension_{k−2}.
  - Guard symbols without volume: `ta.cum(nz(volume)) == 0`.

### 1.10 Supply/demand zones (Seiden school)
- **Zone types.**
  - Continuation: rally-base-rally (RBR) and drop-base-drop (DBD).
  - Reversal: drop-base-rally (DBR, demand) and rally-base-drop (RBD, supply).
  - The **base** is 1-6 small candles. The zone is drawn from the base's bodies or wicks to its extreme.
- **"Odds enhancers"** (Seiden, as commonly listed):
  1. Strength of the move out (departure).
  2. Time at the base: fewer candles is better.
  3. Freshness: untested is better; "first touch is always highest probability".
  4. Reward-to-risk.
  5. Overlap with a higher-timeframe zone.
- **Relation to the engine.** An OB is a 1-candle base at the leg origin (1663-1748). FVG/OB "quality" is departure strength (912, 1692). "Mitigated" OBs are skipped (1693-1700), which is freshness.
- **Algorithm (Pine-feasible).**
  1. Base = k ∈ [1, 6] consecutive bars with body ≤ 0.5·A and combined range ≤ 1.0·A.
  2. Departure = the next 1-3 bars with body sum ≥ 1.5·A in one direction.
  3. Zone = [min low, max of the base candles' bodies] (demand).
  4. Fresh until the first touch. Strength = departure / A.
- **Use for DOL.** Unfilled, fresh zones are the "draw" of a retracement. Tested zones are weaker and expected to break.

### 1.11 How practitioners map events to targets (the claims tested in §2)

| Event | Claimed next draw | Invalidation | Test in §2 |
|---|---|---|---|
| Spring (#3, low volume) | opposite range edge (creek) | spring low | `spring` race, `spring_tgt_hi` magnet |
| Spring + SOS | opposite edge, then beyond | spring low | `spring_sos` |
| UT / UTAD | range low (ice) | UT high | `upthrust`, `ut_tgt_lo` |
| Failed breakout by close | opposite edge | breakout extreme | `spring_cl`, `upthr_cl` |
| Partial decline / rise | top / bottom edge | — | `part_dec`, `part_rise` |
| SC / BC | AR (50% of the leg), then ST of the climax extreme | climax extreme | `climax_dn/up`, `sc_ar50`, `sc_low_retest` |
| New TR | either edge; "the more-tested edge breaks" (liquidity view) or "holds" (S/R view) | — | `tr_first`, touch splits, `tr_edge_t*` |
| Range breakout | measured move; throwback to the broken edge; longer cause → bigger effect | opposite edge | `breakout.py` |
| Coiling / inducement before a pool forms | that pool is a bigger draw (TradeAxis "density") | — | `density.py`, `induce2.py` |
| Equal highs/lows, tests, age | bigger, "matured" stop pools | — | `eqtest.py`, `agetest.py` |
| High-volume sweep (effort) vs low-volume sweep | effort without result means reversal | — | `effort.py` |

---

## 2. Evidence (numbers and sources)

Grades: **strong** = peer-reviewed or large replicated quantitative study; **moderate** = published, reproducible statistics or backtests with numbers; **weak** = practitioner consensus or anecdote; **none** = folklore or unfalsifiable.

### 2.0 Method of this study's tests
- **Data.** The seven series listed at the top, all converted to log prices. ATR is Wilder's ATR(14).
- **Race outcome.**
  - The first trade-through of target T (above) or stop S (below), resolved bar by bar from the next bar for up to K bars (K = 30, also 60).
  - A bar that crosses both is "ambiguous" and dropped. "Neither" is dropped.
  - The statistic is `hit − geo`, where `geo = (C − S)/(T − S)` is the gambler's-ruin probability.
- **Null.**
  - Bar-shuffled surrogates (6-8 per dataset). Each bar keeps its gap, high/low/close offsets from its open, and its volume; the sequence is destroyed.
  - The same detector runs on the surrogate.
  - **Excess** = `(hit − geo)_real − (hit − geo)_null`. This removes the bias of discrete bars and of the detector's own selection.
- **Magnet outcome.**
  - The level is traded through within K bars.
  - Baseline = the series' empirical excursion survival `S(d) = P(max(high[t+1..t+K]) − close[t] > d·ATR)` at the level's distance d. This is the engine's `f_empPoT` surface without the regime split, i.e. the same "random level at the same distance" baseline the engine's ledger uses for EDGE.
  - Nulls are computed the same way.
- **Checkpoint samples** (age, tests, EQ). Every 10 bars, every live unswept pivot within 10 ATR. SEs are cluster-robust by pool.
- **Limits.** Daily and hourly bars only (no minute data); volume only on four series; several Wyckoff events are rare (n = 30-200 per pooled cell); the four range configurations share data, so they are robustness checks, not independent replications.

### 2.1 Published evidence

| # | Claim | Source and design | Numbers | Grade |
|---|---|---|---|---|
| W1 | Rectangle (TR) patterns carry information | Lo, Mamaysky & Wang (2000), *J. Finance* 55:1705-1765. Kernel-smoothed extrema; RTOP/RBOT = 5 alternating extrema, tops and bottoms each within 0.75% of their mean, lowest top > highest bottom. NYSE/AMEX and Nasdaq stocks, 1962-96 | NYSE/AMEX: RTOP n = 1,482, RBOT n = 1,616; Nasdaq 1,134 / 1,320. Conditional vs unconditional 1-day return distributions: KS p = 0.002 (RTOP) and 0.000 (RBOT) on NYSE/AMEX; 0.000 / 0.001 on Nasdaq. A declining volume trend adds significance on NYSE/AMEX (RBOT p = 0.004); increasing vs decreasing volume is insignificant; on Nasdaq "volume trend provides little incremental information" | strong (distribution *shape*, not direction or targets) |
| W2 | Rectangle breakout statistics | Bulkowski, *Encyclopedia of Chart Patterns*; thepatternsite.com (rectangle bottoms > 900 and tops > 1,000 "perfect trades", daily US stocks, bull markets) | Bottoms: breakout up 59%; break-even failure 15% up / 24% down; throwback/pullback 64% / 66%; measured-move target met 79% up / 55% down. Tops: up 63%; failure 15% / 34%; throwback 66% / 64%; target 78% / 54%. Volume trend down in at least 71% of rectangle bottoms | moderate (large n, no random baseline) |
| W3 | Partial rise/decline predicts the breakout side | Bulkowski, partial declines/rises pages; 5,959 patterns 1989-2013 | A partial decline correctly predicts an up-breakout in 80% (rectangle bottoms) and 91% (tops). A partial rise predicts a down-breakout in 74% (bottoms) and 57% (tops) | weak as an edge: no geometry baseline. This study: the excess over geometry is inconsistent (§2.2) |
| W4 | Busted (failed) rectangles move far the other way | Bulkowski, busted rectangles (updated 2020) | 51% of rectangle tops with down-breakouts bust upward. Single-busted average rise 71% vs 51% for non-busted. Busted = moves ≤ 10%, then closes beyond the opposite side | weak to moderate (no baseline) |
| W5 | High breakout volume → more failures and throwbacks | Bulkowski, Volume Study | Above- vs below-average breakout volume: 10% failure 14% vs 5% (up), 28% vs 11% (down). Throwbacks 57% vs 18%, pullbacks 47% vs 17%. Gain 37.6% vs 35.8% | moderate (no baseline) |
| W6 | Cause and effect: bigger bases, bigger moves | Bulkowski, Study of Studies; "Predicting the breakout" (1,070 rectangle tops, 359 stocks, 1995-2023) | Wide patterns outperform narrow in 91% (up) / 85% (down) of pattern types. Tall patterns outperform in 89% / 100%. But "there's no relationship between the rise leading to the rectangle and when a breakout will occur" | weak (pattern-type vote counts) |
| W7 | High-volume price changes reverse | Campbell, Grossman & Wang (1993), *QJE*; NBER w4193 | Index daily returns: the volume × lagged-return interaction is negative (e.g. −0.233, s.e. 0.079, with volatility controls; linear −0.23 ± 0.08); R² 0.4-4.6% by subperiod | strong (daily index level; small R²) |
| W8 | Explosive moves (climaxes) mostly revert, more with high volume | Christensen, Oomen & Renò, "The drift burst hypothesis" (*J. Econometrics*; arXiv 2601.08974); futures across asset classes | Reversal fraction "rarely drops below 65%". Regression R² 25-40% at a 5-min horizon. ES negative bursts: −37.39 bps in 5 min followed by +8.01 bps over the next 55 min (positive bursts +36.41 then −5.44); serial correlation −0.80 (−0.26 for positive bursts); "most pronounced in drops … accompanied by high trading volume" | strong (5-minute scale) |
| W9 | Extreme intraday moves partly reverse | Zawadowski, Andor & Kertész (2006), *Quant. Finance*; arXiv cond-mat/0406696; NYSE and Nasdaq, 60-min moves > 4% and > 8× normal volatility | NYSE: −0.725% in the 10 min after a +3.09% 60-min shock (t = 6.7); significant for 2-6% and 6-10× filters (n = 94-628). Rebound/drop slope −0.139 ± 0.046 (NYSE), −0.249 ± 0.042 (Nasdaq). Volume and volatility decay as power laws over days | strong (minutes to 1 hour) |
| W10 | More prior bounces → more likely to bounce again, decaying over hours | Garzarelli et al. (2014), *Sci. Rep.*; Chung & Bellotti (2021), arXiv 2101.07410 (sibling E4, E5) | Bounce probability > 0.5 and rising with prior bounces. EURUSD: decays to 0.5 at about 350-900 min | strong (high frequency) / moderate (intraday) |
| W11 | Swept levels → continuation | Mahadzva, SSRN 7430998 (sibling E7) | 65/66 fold selections favour continuation (EQH/EQL, OB and Asia-range sweeps) | moderate |
| W12 | Equal highs/lows are barely bigger draws | Open-source distance-matched test (sibling E6) | EQ taken 63-82% vs ordinary swings 68-76% at the same distance; "< 1%" improvement | moderate |
| W13 | Wyckoff accumulation signals profitable | Reddit r/Daytrading "13,000 Wyckoff accumulation signals over 20 years" (method not available) | 65.1% win at 40 days, +9.06% / −6.64% average, "p < 0.001". No baseline: stocks rise over 40 days more than half the time in bull samples | weak |
| W14 | Wyckoff is hard to backtest | Villahermosa (tradingwyckoff.com), "Limitations" | "Lack of public quantitative backtests: … Wyckoff is interpretive, which makes rigorous backtests difficult." "Volume is secondary information" | n/a (candid practitioner statement) |
| W15 | Spring-type rules | Fraser (financial-spread-betting.com); Villahermosa; FibAlgo; fis_wse | #3 = modest penetration on light volume; #2 deeper with more volume; #1 = "wholesale breakdown" on much larger volume. Implementations: vol ≤ 0.8×, 0.8-1.5×, > 1.5× MA20; test/spring max vol 0.7× MA; recovery ≤ 3 bars | none (definitions, no statistics) |
| W16 | Supply/demand odds enhancers | Seiden (FXStreet webinar, Online Trading Academy); tradingwithrayner; ProEA ("Most guides prefer fresh zones, but that's an assumption, not a measured result") | No quantitative tests found. Sibling ict_pd: order blocks returned to 73.7% vs 73.7% random; fresh OBs react more (20-bar life +7.5% vs +4.0% at 1 min); departure size *reduces* fill (BTC 1D size terciles 78.7 / 61.7 / 46.0% full fill in 7 days) | weak (freshness for reaction); none (for reach) |
| W17 | Wyckoff regimes as a statistical object | Srivastava & Bhattacharya (2018), arXiv 1812.02527: Markov-switching regimes "loosely modeled on" accumulation, distribution, advance, decline | Regime-tailored strategy allocation. No event-level target tests | weak for this question |
| W18 | Deep-learning Wyckoff detection | Pal (2024), arXiv 2403.18839 | Trained on synthetic swing/filler points; no out-of-sample trading or target statistics | none |
| W19 | AMD (the ICT re-statement of Wyckoff accumulation → manipulation → distribution) | Taylor, arXiv 2610.35887 (sibling X5); NQ 15m, n = 484 | "No directional information beyond the daily trend regime." 62-71% with trend vs 25-30% against | moderate |

### 2.2 This study: race tests after range events (`wyck.py`)

Excess over the null, `(hit−geo)_real − (hit−geo)_null`, pooled over seven datasets. Four detector settings, given as N (range length) / K (horizon) / kmax (max width in ATR). SE ≈ √(0.22/n).

| Event (expected side) | N20/K30/6 | N30/K30/8 | N50/K30/8 | N30/K60/8 |
|---|---|---|---|---|
| `tr_first` (P(top edge first) at range birth) | −0.002 ± 0.020 (n 537) | +0.022 ± 0.022 (441) | −0.056 ± 0.030 (244) | +0.020 ± 0.022 (475) |
| `spring` → top edge before spring low | +0.016 ± 0.039 (143) | −0.044 ± 0.041 (132) | −0.075 ± 0.054 (76) | −0.013 ± 0.040 (138) |
| `spring_cl` (close below, close back in ≤ 3 bars) | −0.048 ± 0.053 (79) | −0.043 ± 0.057 (67) | −0.045 ± 0.075 (39) | +0.010 ± 0.055 (74) |
| `spring_sos` (spring, then close > mid) | −0.006 ± 0.072 (42) | −0.035 ± 0.084 (31) | −0.145 ± 0.177 (7) | −0.012 ± 0.084 (31) |
| `upthrust` → bottom edge before UT high | +0.037 ± 0.034 (186) | −0.002 ± 0.039 (144) | −0.034 ± 0.053 (79) | +0.008 ± 0.039 (148) |
| `upthr_cl` (close above, close back in ≤ 3 bars) | +0.090 ± 0.047 (100) | +0.145 ± 0.053 (77) | +0.096 ± 0.075 (39) | +0.163 ± 0.051 (83) |
| `upthr_sow` | −0.039 ± 0.068 (48) | −0.088 ± 0.108 (19) | −0.027 ± 0.166 (8) | −0.051 ± 0.105 (20) |
| `part_dec` → top first | +0.010 ± 0.040 (141) | −0.020 ± 0.035 (183) | −0.135 ± 0.038 (152) | −0.038 ± 0.034 (196) |
| `part_rise` → bottom first | −0.051 ± 0.043 (118) | +0.011 ± 0.039 (147) | +0.080 ± 0.041 (128) | +0.008 ± 0.037 (158) |
| `climax_dn` (SC) → 50% AR before SC low | +0.023 ± 0.022 (452) | same | same | +0.021 ± 0.022 (454) |
| `climax_up` (BC) → 50% AR before BC high | −0.047 ± 0.026 (315) | same | same | −0.050 ± 0.026 (316) |

Raw rates, to make the geometry visible (N30/K30/6, per dataset):
- After a spring, the top edge is taken first in 0.12-0.38 of decided cases, against geometry of 0.16-0.26. Examples: NQ 0.174 vs 0.259; GC 0.143 vs 0.248; EURUSD 1H 0.120 vs 0.199; S&P D 0.312 vs 0.226.
- Partial declines "work" 0.70-0.93 of the time, but geometry already says 0.71-0.81. That explains most of Bulkowski's 80-91%.

Readings:
- No range event beats geometry consistently.
- The only cell that is positive in all four settings is the **close-based failed upside breakout** (`upthr_cl`: range low first more than geometry, +0.09 to +0.16, about 2-3σ each). But:
  - the settings share data;
  - per dataset the sign is mixed (N30/K30/6: S&P −0.14, n 7; NASDAQ +0.32, n 6; NQ +0.25, n 15; GC +0.16, n 14; EURUSD 1H 24-26 +0.05, n 7; EURUSD 17-18 −0.09, n 7);
  - the mirror (`spring_cl`) is negative.
- Treat `upthr_cl` as a **hypothesis for the per-chart ledger**, not a rule (weak).
- After a buying climax, the BC high is re-taken *more* than the null: continuation, the opposite of the Wyckoff reading.

Spring and UT extremes retested within K (traded through again) vs a distance-matched control:
- Spring lows: −0.19 to +0.04 by dataset; pooled magnet edge +0.018 ± 0.033 (N30) and −0.026 ± 0.034 (N20).
- UT highs: −0.12 to +0.09; pooled −0.018 ± 0.028 and −0.014 ± 0.025.
- The spring extreme is neither a stronger "protected" low nor a stronger magnet.

### 2.3 This study: are Wyckoff levels magnets? (`magnet.py`, K = 30)

Edge = hit within 30 bars − S(d) (random level at the same ATR distance), pooled over seven datasets.

| Level | N = 30 edge (n) | N = 20 edge (n) | Null edge (N30 / N20) |
|---|---|---|---|
| Range high at range birth | +0.001 ± 0.019 (479) | +0.004 ± 0.017 (578) | +0.012 / −0.005 |
| Range low at range birth | −0.012 ± 0.020 (479) | +0.001 ± 0.019 (578) | +0.008 / +0.008 |
| Range edge with 2 touches | +0.000 ± 0.015 (808) | +0.003 ± 0.014 (972) | +0.018 / +0.004 |
| … 3 touches | −0.031 ± 0.038 (125) | +0.017 ± 0.035 (154) | −0.049 / −0.018 |
| … 4+ touches | −0.084 ± 0.095 (25) | −0.084 ± 0.085 (30) | +0.053 / −0.001 |
| Opposite edge after a spring | −0.036 ± 0.038 (141) | −0.037 ± 0.040 (153) | −0.002 / −0.008 |
| Spring low (retaken) | +0.018 ± 0.033 (141) | −0.026 ± 0.034 (153) | +0.003 / +0.005 |
| Range low after an upthrust | −0.073 ± 0.032 (153) | −0.013 ± 0.034 (198) | +0.033 / −0.016 |
| UT high (retaken) | −0.018 ± 0.028 (153) | −0.014 ± 0.025 (198) | −0.016 / +0.031 |
| 50% AR after an SC | +0.007 ± 0.016 (589) | same | −0.019 |
| 50% AR after a BC | −0.018 ± 0.022 (380) | same | −0.004 |

Reading: **every Wyckoff level is a random-distance level** for "reached within H bars". The engine's existing proximity/empirical-PoT machinery already prices these levels correctly. A range-edge bonus would be noise.

### 2.4 This study: the engine's density and freshness inputs (`density.py`, `effort.py`, `induce2.py`, `agetest.py`, `eqtest.py`)

**Input distributions per bar** (engine definitions, 886-895):

| Series | coilScore P(= 0) | coilScore median | coilScore P(> 0.5) | indScore P(= 1) | indScore P(≥ 2/3) | indScore P(= 0) |
|---|---|---|---|---|---|---|
| S&P 500 D | 0.004 | 0.54 | 0.550 | 0.881 | 0.964 | 0.005 |
| NASDAQ D | 0.015 | 0.42 | 0.375 | 0.873 | 0.970 | 0.004 |
| GOOG D | 0.043 | 0.39 | 0.336 | 0.836 | 0.954 | 0.005 |
| EURUSD 1H 17-18 | 0.003 | 0.55 | 0.578 | 0.884 | 0.968 | 0.006 |
| NQ 1H | 0.012 | 0.50 | 0.506 | 0.902 | 0.974 | 0.003 |
| GC 1H | 0.001 | 0.59 | 0.607 | 0.894 | 0.969 | 0.004 |
| EURUSD 1H 24-26 | 0.010 | 0.50 | 0.498 | 0.641 | 0.863 | 0.023 |

`induceBar` fires on any wick through a 5-bar extreme that closes back inside, which happens almost every few bars. `min(1, count/3)` over 20 bars is therefore about 1 always. **The inducement term is a constant**: +0.15 density for every liquidity pool and +0.13 to 0.20 for every array.

**Reach of chart pivots** (pivLen 5, n = 6,246, K = 30) vs a random level:
- All pivots: −0.014 ± 0.006. The null gives +0.001 ± 0.004, so pivots are slightly "sticky", consistent with W10.
- By coil at birth: coil > 0.5 −0.019 ± 0.008 (n 3,266); coil in (0, 0.5] −0.008 ± 0.008 (n 2,927).
- By inducement: indScore ≥ 2/3 −0.013 ± 0.006 (93.9% of pivots); = 0 n = 55.
- **De-saturated definitions** (`induce2.py`, n = 5,821): a real 20-bar sweep by ≥ 0.10 ATR closing back inside has count 0/1/≥2 on 15-24% / 30-37% / 39-53% of bars. By count: 0 → −0.022 ± 0.013; 1 → −0.008 ± 0.010; ≥ 2 → −0.013 ± 0.009.
- Coil as a 500-bar percentile, by tercile: −0.013, +0.002, −0.028 (± 0.010).
- **Neither definition carries a positive signal.**

**Freshness and tests** (36,724 checkpoint samples, 4,783 pools, cluster-robust):
- By age: ≤ 30 bars −0.011 ± 0.006; 31-150 −0.007 ± 0.005; 151-500 −0.018 ± 0.006; > 500 −0.001 ± 0.006.
- Within 1 ATR: age > 150 gives −0.075 against −0.003 for age ≤ 30 ("defended" levels; weak).
- By tests (engine rule): 0 → −0.010 ± 0.003; 1 → −0.011 ± 0.008; 2 → +0.003 ± 0.020; ≥ 3 → +0.027 ± 0.044. No effect in either direction at K = 30 on 1H/daily bars.

**Equal highs/lows** (engine merge rule, `eqTol` 0.10 ATR, outermost print; 34,868 samples):
- eqCount 0: −0.007 ± 0.003 (4,566 pools).
- eqCount 1: −0.028 ± 0.013 (189 pools).
- eqCount ≥ 2: −0.049 ± 0.043 (7 pools).
- At 2-4 ATR: −0.060 ± 0.027 vs +0.001 ± 0.007.
- Equal pools are *not* bigger magnets within 30 bars; if anything they hold slightly longer (consistent with W10, W12).

What the engine does with these:
- Liquidity density: `x = 0.9·eqCount + 0.45·stack + 0.35·min(tests,6) + 0.8·min(1,prom/3) + 1.2·tier`, and `dens = 0.60·(1−e^{−x}) + 0.25·coil + 0.15·induce` (682-683).
- Freshness: `fresh = (0.35 + 0.65·(1−e^{−age/37.5}))·0.5^{age/600}` (671, halfLife 150).
- For a new pool (age = pivLen = 5), fresh ≈ 0.43. At age 30 it is about 0.69; at 150 about 0.83; at 500 about 0.56.
- With wFresh = 10 of 100, a fresh pool loses about 4 score points against a 100-200-bar pool. That equals the default hysteresis (`hyst` 4).

### 2.5 This study: cause and effect, measured move, throwback (`breakout.py`, N = 30, K = 30)

Frozen range episodes; breakout = the first close outside. Pooled n = 617 breakouts (548 decided):

| Subset | MM-first | Geometry | Diff | Throwback | Random level | Diff |
|---|---|---|---|---|---|---|
| All (real) | 0.571 | 0.565 | +0.006 | 0.870 | 0.872 | −0.001 |
| All (null) | 0.546 | 0.571 | −0.025 | 0.883 | 0.883 | +0.000 |
| Up / down | 0.589 / 0.549 | 0.561 / 0.571 | +0.028 / −0.022 | 0.848 / 0.900 | 0.870 / 0.874 | −0.022 / +0.026 |
| Short cause (≤ 38 bars) / long cause | 0.561 / 0.582 | 0.564 / 0.566 | −0.003 / +0.015 | 0.906 / 0.833 | 0.880 / 0.863 | +0.026 / −0.030 |
| Narrow (≤ 4.9 ATR) / wide | 0.577 / 0.564 | 0.586 / 0.540 | −0.009 / +0.024 | 0.874 / 0.867 | 0.858 / 0.885 | +0.016 / −0.018 |

- Null-adjusted MM excess is about +0.03 ± 0.02.
- A longer or wider cause does not produce a measurably bigger effect.
- Throwbacks are as frequent as a random level at that distance predicts. Bulkowski's 64-66% throwback rate is mostly proximity.

### 2.6 This study: effort vs result at swept pools (`effort.py`; S&P, NASDAQ, GOOG daily and EURUSD 1H 2017-18 with tick volume)

Outcome: continuation, i.e. price extends 1 ATR beyond the sweep bar's extreme within 30 bars, vs a random level at that distance. n = 1,823 sweeps of live pivots.

| Subset | n | Continuation edge | HOLD: throwback through the pool, edge |
|---|---|---|---|
| All | 1,823 | +0.021 ± 0.010 | +0.003 ± 0.009 (n 1,021) |
| HOLD (closed beyond) | 1,021 | +0.008 ± 0.013 | — |
| HOLD, volume < 0.8× / 0.8-1.5× / > 1.5× | 55 / 694 / 272 | −0.024 / +0.008 / +0.013 | +0.033 / +0.014 / −0.031 (± 0.022-0.026) |
| REJECT (closed back inside, the spring/UT shape) | 802 | **+0.039 ± 0.016** | — |
| REJECT, volume < 0.8× / 0.8-1.5× / > 1.5× | 60 / 520 / 222 | −0.010 / +0.047 / +0.033 | — |

Reading:
- A rejected sweep is followed by *more* continuation through the sweep extreme than a random level. That is consistent with W11 and with sibling BIAS-4 / ICTS-2.
- Volume does not modulate the outcome at these timeframes, in contrast to the minute-scale evidence in W8 and W9.
- High-volume holds are, if anything, *less* likely to throw back (−0.031), the opposite of W5's direction. Not significant.

### 2.7 Net reading for the forecasting problem
- **Where (which liquidity).** Distance, plus the empirical PoT the engine already has, explains reach. Wyckoff/S&D labels do not move the odds by more than about ±2-4 pp in any replicated cell. The engine should not *add* points for spring context, range edges, touches, equal prints, coil, inducement or pool maturity.
- **When.** Range episodes do not change the time to break either edge beyond the null. Breakout extension is unrelated to range duration. Timing belongs to the volatility clock (sibling TIME-1).
- **How likely.** Calibrated geometry (the engine's `f_pot`/`f_raceH`, plus the empirical surface) is the right prior. The Wyckoff vocabulary is useful as **labels** and as **per-chart hypotheses for the ledger**, not as fixed weights.

---

## 3. Engine gap analysis (`baseline_v2.pine`)

| Concept | Status | Line refs | What the engine does / what differs |
|---|---|---|---|
| Trading range (TR) detection, frozen box, creek/ice | **partial** | 708-782 (`f_structure` rolling dealing range `rngH`/`rngL` that follows the leg), 1111-1137 (EQ merge at 0.10 ATR), 1230-1251 (stacks within 0.75 ATR, outermost = draw) | There is no horizontal multi-touch range state. Range edges appear as several stacked pivots; the stack logic marks inner prints and the outermost becomes the draw. Touches 0.10-0.25 ATR apart stay separate pools (cluttered candidate pool, several "BSL" labels for one edge). No regime flag (in-range vs trending) for selection or for the ledger |
| Spring / UT / UTAD (wick through, close back inside) | **wrong (as a direction signal)** | 1579-1582 (`liqEvt`: a close back inside a swept pool votes reversal, `−side·tier`); 892-895 (`induceBar` counts mini-springs as density) | The engine treats every rejected raid as a reversal vote into D (weight `wL` 0.30, half-life 24). Evidence: no reversal edge in range context (§2.2) and continuation after rejections (§2.6, W11). Same conclusion as BIAS-4 / ICTS-2; this study adds range-specific data |
| Failed breakout by close (bust) | **partial** | 1747-1748 (breakers only from OBs that took liquidity); 1599-1627 (iFVG on a close through an FVG) | No range-level "bust" state. Evidence is weak and mixed (`upthr_cl` +0.09 to +0.16, `spring_cl` ≈ 0) → ledger hypothesis only |
| SC / BC climax, AR, ST | **missing** | none (bar volume unused outside the volume profile, 978-1015, 1945-1947) | No climax events. Evidence: no reach edge at 1H/daily (§2.2-2.3); a minute-scale reversal edge (W8, W9) is too short-lived for H = 30. **Leave missing** (optional labels only) |
| Tests of a pool | **present, unsupported weight** | 650-656 (`track`: within 0.30 ATR, ≥ 3 bars apart, `gap > 0`), 682 (`0.35·min(tests,6)`) | Up to +2.1 to x. Evidence: no effect at K = 30 (§2.4), bounce memory at intraday scale (W10). Neutral weight recommended, as SMC-3 |
| Equal highs/lows ("build-up") | **present, overweighted** | 1111-1137, 682 (`0.9·eqCount`) | The largest single magnitude term. Evidence: EQ pools reach slightly *less* (−0.028 vs −0.007, §2.4; W12 < 1 pp) |
| Coiling / range-bound density (TradeAxis "density") | **present, non-predictive** | 886-891 (`coilScore`), 683 (`0.25·coil`), 687 (`0.30·coil` for arrays); births at 1703, 1744, 1762, 1774, 1848, 1862, 1874, 1884 | High coil at birth → slightly lower reach (−0.019 vs −0.008). **Bug:** registry re-entries (1848) and HTF FVGs (1862) take the *current* bar's `coilScore`/`indScore`, not the value at the level's birth |
| Inducement sweeps | **wrong (saturated)** | 892-895, 683 (`0.15·induce`), 687 (`0.20·induce`) | `indScore` is ≥ 2/3 on 86-97% of bars, so it is a constant (§2.4). De-saturated forms are also flat |
| Freshness / maturation of liquidity | **wrong (shape)** | 668-671 | Ramp from 0.35 to 1 with τ = 0.25·halfLife, then slow decay. Evidence: age has no effect on reach; old pools near price are slightly *less* likely (§2.4) |
| Freshness of S/D zones (arrays) | present | 673 (half-life), 1566-1577 (partial-fill crop), 1693-1700 / 1736-1741 (skip mitigated OBs), 1626 / 1660 (`trackAge`) | Consistent with the S/D "fresh zone" rule. Evidence: freshness matters for reaction (W16), not reach. Keep |
| Departure strength (S/D) | present | 912, 1870-1871, 1880-1881 (FVG quality), 1692, 1735 (OB quality), 687 (`0.5·qual`) | A strong departure raises the array's density. Evidence (W16 via sibling): larger displacement → *lower* fill probability. ICTPD-1 proposes the fix; not duplicated here |
| Time at level / base length (S/D) | missing | — | OBs are single candles. No evidence either way; **leave missing** |
| Partial rise / decline | missing | — | Bulkowski's rates are geometry (§2.2). **Leave missing** |
| SOS / SOW, JAC, LPS / LPSY, BUEC | partial | 1542-1547 (`bosUp/bosDn` body close through the last swing), 897-904 (displacement), 1663-1748 (OB from the BOS leg ≈ LPS zone) | The engine's BOS + OB is the SMC restatement of SOS + LPS. No range-midpoint rule. No evidence the SOS/SOW refinement helps (`spring_sos` ≤ 0). Fine as is |
| Composite operator | n/a | — | Unfalsifiable |
| Cause and effect (P&F count), measured move | missing | — | No evidence (§2.5, W6, W14). **Leave missing** |
| Effort vs result (volume, spread, Weis wave) | missing | volume only in the volume profile path cost (1945-1947) and LVNs (2250+) | No bar-level volume features. Evidence null at 1H/daily (§2.6). Candidate-ledger feature only (WYK-5) |
| Throwback to a broken edge | missing | swept pools are deleted (1583-1589) | Throwbacks happen at random-level rates (§2.5). No special handling needed |
| Range-context selection | missing | 1891-1895 (D), 1964-2035 (selection uses `dirSide` from D) | Inside ranges, D (structure, displacement, raid votes) carries no information (§2.2 `tr_first`; sibling ICTS-1 finds D skill 0.49-0.54 everywhere). The selection still gates on D |

---

## 4. Proposals (best first; maximum 10)

Selection rule: only changes this domain's evidence supports and the engine's own ledger can measure. Pure subtraction comes first, because it improves forecasts at near-zero risk. Proposals that would add Wyckoff targets were rejected on evidence (see "Considered and rejected").

### WYK-1 (P1) · Density pillar evidence audit: neutralise saturated or non-predictive inputs, fix the birth-value bug

**Why.**
- `indScore` is a constant (≥ 2/3 on 86-97% of bars).
- `coilScore`, `eqCount` and `tests` show no positive relation to reach within H; coil and EQ are slightly negative (§2.4, W10, W12).
- Together they hold 0.25 + 0.15 of the liquidity density, plus most of the `x` term, under a 20%-weight pillar. They push the engine toward EQ pools, tested pools and coiled pools, which are not more likely to be taken.
- Registry re-entries (1848) and HTF FVGs (1862) use the current bar's coil and inducement, an outright bug.

**Algorithm.**
1. Add a model switch so the change is measurable and the classic look stays available. In INPUTS, G_SCORE, after 140:
   ```pine
   string densModel = input.string("Evidence", "Density Model", options = ["Evidence", "Classic"], group = G_SCORE,
     tooltip = "Evidence: magnitude from source tier, swing prominence and stacking only; equal prints, tests, coiling and inducement carry no weight unless the ledger learns one. Classic: the original blend.")
   ```
2. In `evaluate` (681-687):
   ```pine
   bool ev = densModel == "Evidence"
   if this.isLiquidity()
       float x = (ev ? 0.25 * math.min(this.eqCount, 2) : 0.9 * this.eqCount) + 0.45 * this.stack
             + (ev ? 0.0 : 0.35 * math.min(this.tests, 6)) + 0.8 * math.min(1.0, this.prom / 3.0) + 1.2 * this.tier()
       this.dens := ev ? (1.0 - math.exp(-x)) : 0.60 * (1.0 - math.exp(-x)) + 0.25 * this.coil + 0.15 * this.induce
   else
       this.dens := ev ? math.min(1.0, 0.70 * this.qual + (this.src == 2 ? 0.20 : 0.0))
                       : math.min(1.0, 0.50 * this.qual + 0.30 * this.coil + 0.20 * this.induce + (this.src == 2 ? 0.20 : 0.0))
   ```
   For arrays, coordinate with ICTPD-1, which re-signs `qual`. If ICTPD-1 lands, use its array density and simply drop the coil/induce terms.
3. **De-saturate the inputs** so a learner (ICT-1's candidate ledger) has variance to work with, while the HUD still reports them for spec parity ("coiling and inducement sweeps"). Replace 888-895 with:
   ```pine
   float overlap   = rngN > 0 ? sumRng / rngN : 0.0
   float coilScore = nz(ta.percentrank(overlap, 500)) / 100.0          // uniform 0..1 by construction
   float hh20i     = ta.highest(high, densLen)[1]
   float ll20i     = ta.lowest(low, densLen)[1]
   bool  induceBar = (high > hh20i + 0.10 * nz(atr[1], atr) and close < hh20i) or (low < ll20i - 0.10 * nz(atr[1], atr) and close > ll20i)
   float indScore  = math.min(1.0, math.sum(induceBar ? 1.0 : 0.0, densLen) / 2.0)
   ```
   On the seven datasets the new count is 0 on 15-24%, 1 on 30-37% and ≥ 2 on 39-53% of bars (`induce2.py`). Note `ta.percentrank` takes a series int length per the v6 reference; 500 fits the script's `max_bars_back = 500`.
4. **Birth-value fix.**
   - Add `float coil` and `float ind` to `type Ext` (365-372). Fill them in `f_pushExt` (1211-1225) with the values at the anchor bar: `coilScore[math.min(bar_index - nz(aBar, bar_index), 450)]`, and the same for `indScore`.
   - Use `e.coil` / `e.ind` at 1848 instead of the current `coilScore`, `indScore`.
   - For HTF FVGs (1862) use the values at `aHF`, with the same clamped offset.
   - A dynamic history offset is legal (`[]` accepts a series int). Clamp it inside 500 to honour `max_bars_back = 500`.

**Ledger measurement.** Switch Density Model and compare the overall EDGE row (hit vs distance-matched baseline, z and verdict; 2385-2402) and, in the Full view, the per-family hit rates of CHART LIQ and EXT LIQ (2410-2418). The family rows show hit % and n only; a per-family EDGE (k − ΣpBase from `stK`/`stPE`, already accumulated in `f_book` 1470-1475) is a one-line addition worth making for every A/B in this report. If ICT-1 exists, register `eqCount>0`, `tests`, `coilScore` and `indScore` as candidate features. The learned bounded lifts then replace fixed weights (expected ≈ 0 or slightly negative).

**Expected value.**
- Removes about 5-15 score points of systematic, evidence-free bias toward EQ, tested and coiled pools.
- Proximity, tier and draw then decide, which the evidence supports (sibling E6, §2.3).
- Fewer "wrong" targets where a stacked equal-high pool 3 ATR away outranks the nearer clean swing.
- Fixes a real bug.

**Evidence.** Moderate: own null-controlled tests on seven datasets (n = 6,246 pivots; 36,724 checkpoint samples), consistent with W10 and W12.

**Risk.**
- On instruments where EQ pools *are* bigger draws (very liquid FX majors at minute scale, per ICT claims), the Evidence model under-weights them. The `Classic` option and the learned ledger lift recover that.
- The TradeAxis feature spec lists coiling and inducement as density inputs. They stay computed, shown in the HUD tooltip, and selectable.

**Effort.** S.

### WYK-2 (P2) · Liquidity freshness without the "stops accumulate" ramp

**Why.** The ramp (671) gives a pool born 5 bars ago fresh ≈ 0.43 and a 100-200-bar pool ≈ 0.85, worth about 4 points at `wFresh = 10`. That equals `hyst` and delays switching to a new, closer pool. Age has no effect on reach (≤ 30: −0.011; 31-150: −0.007; 151-500: −0.018; > 500: −0.001, §2.4). Old pools very near price are slightly *less* likely to be taken (−0.075 vs −0.003 within 1 ATR; weak), the opposite of maturation.

**Algorithm.**
- Input after 138:
  ```pine
  string freshLiq = input.string("Flat", "Liquidity Freshness", options = ["Flat", "Maturing"], group = G_SCORE,
    tooltip = "Flat: a pool keeps full freshness and fades slowly with age (evidence: age does not change how often pools are taken). Maturing: the original ramp.")
  ```
- In `evaluate` (669-671):
  ```pine
  if this.isLiquidity()
      this.fresh := freshLiq == "Flat" ? math.pow(0.5, age / (4.0 * halfLife))
                                       : (0.35 + 0.65 * (1.0 - math.exp(-age / (0.25 * halfLife)))) * math.pow(0.5, age / (4.0 * halfLife))
  ```
- Optional hypothesis, off by default and only via ICT-1's candidate ledger: a "defended" flag, `age > 150` and `distance ≤ 1 ATR` and `tests ≥ 1`. Do not hard-code a penalty.

**Ledger measurement.** Flat vs Maturing A/B on overall DOL HIT % vs baseline and BARS→HIT. With SMC-2 (commitment mode), also the switch rate.

**Expected value.** New swing pools near price compete on proximity and tier instead of waiting about 30-40 bars to "mature". Small but systematic, and it lowers target lag after structure changes.

**Evidence.** Moderate (§2.4, cluster-robust, seven datasets). No contrary quantitative evidence exists; maturation is folklore.

**Risk.** Very low. If both freshness forms are flat in practice, wFresh just becomes a slow staleness filter.

**Effort.** S.

### WYK-3 (P2) · Trading-range regime: one pool per range edge, draw-neutral selection inside ranges, regime-split ledger

**Why.**
- Inside a qualified range, which edge goes first is pure geometry (`tr_first` excess −0.056 to +0.022 ± 0.02-0.03). Springs, UTs, partial rises and declines add nothing (§2.2).
- The draw vector D has no measured skill anywhere (ICTS-1), and its raid votes are mis-signed (BIAS-4). Inside ranges, D is noise that can still gate selection through `dirSide` (1895, 1975) and flip targets between the two edges as D wobbles.
- Range edges with touches 0.10-0.25 ATR apart become 2-4 separate pools. They are visually noisy, though the stack logic already picks the outermost.
- Traders read ranges in Wyckoff terms. A `RANGE H / RANGE L` target code, plus measured in-range vs trend accuracy, is both clearer and honest.

**Algorithm.**

*Inputs* (new group "Trading Range", G_TR):
```pine
bool  useTR   = input.bool(true, "Detect Trading Ranges", group = G_TR)
int   trLen   = input.int(30, "Range Length (bars)", minval = 10, maxval = 100, group = G_TR)
float trMaxW  = input.float(8.0, "Max Range Height (slow ATR)", minval = 2.0, step = 0.5, group = G_TR)
float trMinW  = input.float(1.5, "Min Range Height (slow ATR)", minval = 0.5, step = 0.25, group = G_TR)
float trTol   = input.float(0.25, "Edge Touch Tolerance (ATR)", minval = 0.05, step = 0.05, group = G_TR)
int   trTouch = input.int(2, "Min Touches per Edge", minval = 1, maxval = 5, group = G_TR)
float trDK    = input.float(0.0, "Draw Weight Inside Range", minval = 0.0, maxval = 1.0, step = 0.1, group = G_TR,
  tooltip = "0 = inside a range the draw vector is ignored and the nearer / likelier edge wins on geometry (evidence default). 1 = no change.")
bool  showTR  = input.bool(false, "Show Range Box", group = G_TR)
```

*Series* (global, after 884):
```pine
float trH0 = ta.highest(high, trLen)[1]
float trL0 = ta.lowest(low, trLen)[1]
```

*State* (after 1050):
```pine
var bool  inTR = false
var float trHi = na
var float trLo = na
var int   trStart = na
var int   trOut = 0
```

*Engine, confirmed bars* (a new step 9b, after the chart BSL/SSL at 1752-1776, so pivots exist):
- If `useTR and not inTR` and the width check `trMinW*atrE <= trH0 - trL0 <= trMaxW*atrE` passes, count touches:
  - `for k = 1 to trLen` count `high[k] >= trH0 - trTol*atr` with ≥ 3-bar spacing (same for lows).
  - That is ≤ 100 iterations on a single confirmed bar, well inside the 500 ms per-loop limit ("The execution time for any loop on any single bar is limited to 500 milliseconds", writing_scripts limitations).
- On qualification:
  - Set `inTR := true`, `trHi := trH0`, `trLo := trL0`, `trStart := bar_index - trLen`.
  - Merge edges: find the BSL nearest `trHi` with `f_findLiq(pool, 0, trHi, trTol*atr)`. Set `rngEdge := true` on it. Mark every other BSL in `[trHi - trTol*atr, trHi]` `inner := true` (they become inducement). Same for SSL at `trLo`.
  - The new `Level` field is `bool rngEdge = false`. Name it in `f_levelName` (518-530): `kind == 0 and rngEdge ? "RANGE H"`.
- While `inTR`:
  - `trOut := close > trHi or close < trLo ? trOut + 1 : 0`; end the range when `trOut >= 2` or after `5*trLen` bars.
  - Springs and UTs (wick through, close back inside) **do not** end it, and the box stays fixed (Wyckoff boundaries are the SC/AR levels).

*Selection* (1891-1895, 1948):
```pine
bool  inBox = inTR and close <= trHi and close >= trLo
float dSel  = inBox ? drawD * trDK : drawD
int dirSide = dSel >= dGate ? 1 : dSel <= -dGate ? -1 : 0
...
lv.evaluate(close, atr, anchors, confTol, dSel, nz(potSig), nz(potMu))
```
- Keep `drawD` for the panel and the Draw Flip alert, labelled "(range: neutral)" when `inBox`.
- If BIAS-1/BIAS-2 (calibrated side probability) land, `dSel` is already geometry-based. WYK-3 then contributes only the regime flag, the edge merge and the ledger split.

*Ledger* (1375-1499):
- Add `int reg` to `Trial` (0 = trend, 1 = in range), set in `f_openTrial` from `inBox`.
- Add `var array<int> rgN = array.new<int>(2, 0)`, `rgK`, and `var array<float> rgPE = array.new<float>(2, 0.0)`; update them in `f_book` alongside `stN/stK/stPE`.
- Full view: one row `RANGE  hit 41% · edge +2.1  |  TREND  hit 47% · edge +3.4` using the existing Wilson/z helpers.

*Clean visuals* (keep the reference look): when `showTR` (off by default), one dashed `box` from `trStart` to `bar_index + extBars` at 85-90% transparency, no text; it is redrawn on `tailBar` like the iFVG boxes. Terminal style: the HUD shows `RANGE 2.8 ATR · 37 bars`.

**Ledger measurement.**
- A/B `trDK` 0 vs 1: in-range EDGE z and DOL HIT % from the regime split.
- With SMC-2: the target switch rate inside ranges.

**Expected value.**
- Fewer flip-flops between range edges.
- One clean `RANGE H/L` pool instead of a ladder of near-equal BSL/SSL labels.
- Honest per-regime accuracy (traders can see that the engine is weaker in ranges, or not).
- The selection inside ranges follows what the data says decides the race.

**Evidence.** Moderate: geometry dominance inside ranges (§2.2) plus D's lack of skill (ICTS-1). The UX value is weak/subjective.

**Risk.**
- Range detection lags by up to `trLen` bars, and a rolling `highest/lowest` box can qualify late in a range. That is acceptable for a regime flag.
- Not repainting: confirmed bars only, `[1]` history.
- Drawing budget: one box.
- Interaction: `inner` marking reuses the 0.70 inner multiplier (684-685).

**Effort.** M.

### WYK-4 (P3) · Wyckoff event layer (labels and alerts) with zero forecast weight and per-chart honesty stats

**Why.** Traders look for springs, UTADs and failed breakouts. The evidence says these events do not predict the next draw (§2.2-2.3, §2.6). Two things follow:
- The engine must not feed them into D. The current `liqEvt` mapping at 1581 does (fix shared with BIAS-4 / ICTS-2).
- If they are shown, each should carry its *measured* rate on the user's chart against geometry. That turns a folklore signal into an honest statistic, and it makes the indicator stand out from competitors that only paint "SPRING ✓".

**Algorithm** (requires WYK-3's `inTR`, `trHi`, `trLo`; confirmed bars).
- **Events.**
  - `SPRING`: `low < trLo and close > trLo and close < trHi and (trLo - low) <= 1.5*atr`.
  - `UTAD`: the mirror at `trHi`.
  - `FAILED BO`: a close outside, then a close back inside within 3 bars (keep a 3-bar pending slot per side).
  - Volume class where volume exists (`bool hasVol = ta.cum(nz(volume)) > 0`): `vr = volume / ta.sma(volume, 20)[1]` gives `#3` (≤ 0.8), `#2` (0.8-1.5), `SO` (> 1.5).
- **D.** Inside `inBox`, raid events at the range edges add **0** to `liqEvt` (1581-1582). Outside ranges, follow BIAS-4's `rejW` (default 0).
- **Honesty ledger.** For each event, open a light race record: target = the opposite edge, stop = the event extreme, horizon H, `p0 = (close - stop)/(target - stop)`.
  - Resolve it with the bar-path logic of `f_step` (1434-1459), reusing `Trial` with a new `grp = 5` and excluding group 5 from `stN[4]` so DOL accuracy is unaffected.
  - Accumulate n, k and Σp per event type, in three small arrays of length 3.
- **Display (Terminal style only).** A tiny label at the event bar, `SPRING #3 · 31% vs 26% (n 14)` (the event's opposite-edge-first rate on this chart vs geometry). Cap at 10 labels in a ring buffer, like the ghosts (1253-1263). Clean style: none.
- **Alerts.** `alert("DOL Engine ▸ SPRING at RANGE L … · opposite edge first 31% here (geometry 26%, n 14) · " + syminfo.ticker, alert.freq_once_per_bar_close)` and the same for UTAD and FAILED BO. Add one `alertcondition` "Range Spring / UTAD".

**Ledger measurement.** It is a ledger: the rates are the measurement. If, on some chart, an event type shows a stable excess over geometry, it can be promoted into ICT-1's candidate ledger as a learned feature.

**Expected value.** Trader-facing vocabulary and alerts with truthful statistics. No accuracy cost, because the forecast weight is zero. It removes the one place where the engine currently acts on the Wyckoff reading (the reversal vote).

**Evidence.** Moderate for "no edge" (§2.2, §2.6, W11). Weak for the UX value.

**Risk.**
- Label clutter, which is why it is Terminal-only.
- Users may misread a small-n rate; show n and grey it out below 20.

**Effort.** M.

### WYK-5 (P3) · Effort-vs-result volume features as learned, zero-default candidate features

**Why.**
- Volume is the core Wyckoff input, and the engine uses bar volume only for the volume profile.
- At 1H/daily, sweep-bar volume does not modulate continuation, throwback or reversal (§2.6).
- At minute scale, high-volume extreme moves partly revert with strong evidence (W7-W9). Users on 1-5 minute charts may get a real but short-lived effect.
- The right design is per-chart learning, not a fixed weight.

**Algorithm** (only if ICT-1's candidate ledger exists; otherwise skip).
- Features at selection time for the active target:
  1. `vrLast`: the volume ratio of the bar that last swept a same-side pool, from `liqEvt` events (1579-1582).
  2. `climax`: within the last 10 bars, a bar with `vr ≥ 2`, `range ≥ 1.5·atr`, a new 20-bar extreme and a close location ≥ 0.5 off the extreme (§1.2), signed toward the target.
  3. `absorb`: within 5 bars and 0.5 ATR of the target's near edge, a bar with `vr ≥ 2` and `range ≤ 0.8·atr`.
- Guard with `hasVol`. Initial weight 0, bounded learned lift (as ICT-1).
- No drawing, no new `request.*` calls. All are global `ta.sma(volume, 20)` series.

**Ledger measurement.** The candidate ledger's per-feature lift and z, by itself.

**Expected value.** Lets volume help where it actually helps (low timeframes, high-volume futures and crypto) without hurting where it does not.

**Evidence.** Weak to moderate (literature at minute scale; null at 1H/daily here).

**Risk.** Feature-count creep in ICT-1. Keep to these three.

**Effort.** S, given ICT-1.

### Considered and rejected (evidence says no, or the engine already handles it)
- **"Spring → target the opposite range edge"** as a selection rule or score bonus. The opposite edge comes first at geometry rates (12-37% vs 16-26%) and its magnet edge is −0.036 ± 0.038 (§2.2-2.3).
- **Range-edge magnitude bonus** ("more touches = more stops") and **"the more-tested edge breaks first"**. Edges with 2, 3 or 4+ touches show +0.000 / −0.031 / −0.084, and the touch asymmetry has no consistent sign.
- **Climax → automatic-rally target, and SC/BC extremes as ST magnets.** The 50% AR shows +0.007 ± 0.016 (SC) and −0.018 ± 0.022 (BC); after a BC the high is re-taken more than the null (−0.047 ± 0.026 for the AR-first race). The minute-scale reversal (W8, W9) decays well inside an hour.
- **Point-and-figure count targets and measured-move targets as candidate levels.** No published test (W14). The measured move comes first at geometry rates, and cause length/width has no effect (§2.5). They also have no liquidity behind them, so they do not fit a draw-on-liquidity engine.
- **Throwback / BUEC targets after a breakout.** These occur at random-level rates (0.870 vs 0.872).
- **Partial rise / decline as a side predictor.** Bulkowski's 74-91% is geometry; the excess is inconsistent in sign.
- **S/D "time at base" and multi-candle base zones.** No evidence, and arrays are reached at random-level rates anyway (sibling ict_pd 2.1).
- **A "busted range" (failed close breakout) bonus.** The only consistently positive cell (`upthr_cl`) is asymmetric, mixed in sign per dataset, and shares data across settings. It is left to WYK-4's per-chart ledger.
- **Phase A-E labelling.** Labels are provisional "until markup confirms them" (LuxAlgo); no measurable forecast content.

---

## 5. Notes for implementers
- **Order.** WYK-1 and WYK-2 are independent S-sized edits in `evaluate` (661-696) plus inputs. Implement them first and A/B them through the ledger. WYK-3 adds one state block, one `Level` field, one `Trial` field and the ledger split. WYK-4 needs WYK-3. WYK-5 needs ICT-1.
- **Sibling overlaps (do not double-implement).**
  - `tests`: SMC-3 (neutral weight, decay, exact-touch fix) and WYK-1's Evidence model both remove the 0.35·tests term. If SMC-3 lands, WYK-1 keeps SMC-3's `wTest` input instead of its own zero.
  - `liqEvt` sign: BIAS-4 and ICTS-2. WYK-4 only adds "zero inside ranges".
  - EQ weight: ict_liq flagged 0.9·eqCount as large (gap table, line 199). WYK-1 implements the reduction.
  - Array density / displacement sign: ICTPD-1.
  - A geometry-based side model: BIAS-1/BIAS-2. WYK-3's `trDK` becomes redundant once those land.
- **Compile notes** (doc-grounded):
  - `ta.percentrank(source, length)` and `ta.highest(source, length)` take a series int length (`reference/ta.md`: "`length` (series int)").
  - A history offset with a series int inside `[]` is legal. Keep offsets ≤ 500 because of `max_bars_back = 500` in `indicator()` (line 31).
  - All new `ta.*` calls must sit at global scope in SERIES (they are), not inside the `if barstate.isconfirmed` block, so they run on every bar.
  - The loop budget is "500 milliseconds" per loop per bar. WYK-3's touch count is ≤ 100 iterations, only while no range is active.
- **Non-repainting.** Every proposal runs on confirmed bars with `[1]`-referenced boxes. None adds a `request.*` call.
- **Measuring.** The engine's EDGE baseline (`f_potBase`, 1314-1322; panel row 2385-2402) is the same distance-matched baseline used in this study. That makes the A/B results directly comparable to the numbers in §2.3-2.4.

---

## 6. Sources

Wyckoff method (definitions):
- Wyckoff Analytics, "Wyckoff Method" (Pruden/Fraser school: events, phases, schematics, P&F count guide, nine tests): https://www.wyckoffanalytics.com/wyckoff-method/
- Villahermosa, R., "Wyckoff Method 2026: Complete Guide" and "Spring/Shakeout" (spring types, limitations): https://tradingwyckoff.com/en/wyckoff-method/ · https://tradingwyckoff.com/en/spring-shakeout/ · https://tradingwyckoff.com/en/cause-and-effect/
- Fraser/Evans spring #1/#2/#3 rules: https://www.financial-spread-betting.com/trading/wyckoff-spings-upthrusts.html
- LuxAlgo Library, Wyckoff accumulation schematic; Wyckoff wave and volume studies; volume spread analysis: https://www.luxalgo.com/library/concept/wyckoff-accumulation-schematic/ · https://www.luxalgo.com/library/concept/wyckoff-wave-and-volume-studies/ · https://www.luxalgo.com/library/concept/volume-spread-analysis/
- CMC Markets, Wyckoff method explained: https://www.cmcmarkets.com/en-gb/trading-strategy/what-is-wyckoff-method
- ATAS, Weis waves (shortening of the thrust): https://atas.net/blog/how-to-use-the-weis-waves-indicator/

Algorithmic implementations (parameters learned, no code copied):
- FibAlgo, "Wyckoff Spring & Upthrust" (TR lookback 50, recovery 3 bars, volume classes, 8-ATR trend filter): https://www.tradingview.com/script/H3zpGMiK-Wyckoff-Spring-Upthrust-FibAlgo/
- fis_wse, "Wyckoff Phase Classifier" (pivot 3/2, climax multiplier, test/spring ≤ 0.7× volume MA): https://www.tradingview.com/script/9ap94IDt-Wyckoff-Phase-Classifier/
- trendcraft `wyckoffPhases` API (swing 5, minRangeBars 20, tolerance 0.5 ATR): https://github.com/sawapi/trendcraft/blob/97586812ba94ce071dd5390b739c5986ab16e010/packages/core/docs/API.md
- MQL5 article 22628, "Automating Classic Market Methods in MQL5 (Part 1): Wyckoff Accumulation and Distribution": https://www.mql5.com/en/articles/22628
- StockSharp, Volume Climax Reversal (2× volume MA): https://doc.stocksharp.com/en/api-examples/0115_Volume_Climax_Reversal
- ta4j Wyckoff package (structure tracker, volume profile): https://github.com/ta4j/ta4j-wiki/blob/64256353c2402d60dc438d23ef36d9c17f8440cb/VWAP-Support-Resistance-and-Wyckoff.md

Quantitative evidence:
- Lo, A., Mamaysky, H., Wang, J. (2000). "Foundations of Technical Analysis." *Journal of Finance* 55(4):1705-1765. NBER w7613: https://www.nber.org/system/files/working_papers/w7613/w7613.pdf
- Bulkowski, T., thepatternsite.com: rectangle bottoms https://thepatternsite.com/rectbots.html · rectangle tops https://thepatternsite.com/recttops.html · partial declines https://thepatternsite.com/partdecline.html · partial rises https://thepatternsite.com/partrises.html · busted rectangles https://thepatternsite.com/BustRectangles.html · busted patterns https://thepatternsite.com/Busted.html · volume https://thepatternsite.com/Volume.html · volume study https://thepatternsite.com/VolumeStudy.html · study of studies https://thepatternsite.com/studystudy.html · predicting the breakout https://thepatternsite.com/TsversusWidth.html
- Campbell, J., Grossman, S., Wang, J. (1993). "Trading Volume and Serial Correlation in Stock Returns." *QJE* 108(4). NBER w4193: https://www.nber.org/system/files/working_papers/w4193/w4193.pdf
- Christensen, K., Oomen, R., Renò, R. "The drift burst hypothesis." *Journal of Econometrics*; arXiv 2601.08974: https://arxiv.org/abs/2601.08974
- Zawadowski, A., Andor, G., Kertész, J. (2006). "Short-term market reaction after extreme price changes of liquid stocks." *Quantitative Finance*; arXiv cond-mat/0406696: https://arxiv.org/abs/cond-mat/0406696
- Garzarelli, F. et al. (2014). "Memory effects in stock price dynamics: evidences of technical trading." *Sci. Rep.* 4:4487: https://arxiv.org/abs/1110.5197
- Chung, K., Bellotti, A. (2021). "Evidence and Behaviour of Support and Resistance Levels in Financial Time Series." arXiv 2101.07410: https://arxiv.org/abs/2101.07410
- Srivastava, S., Bhattacharya, R. (2018). "Evaluating the Building Blocks of a Dynamically Adaptive Systematic Trading Strategy" (Wyckoff-like regimes). arXiv 1812.02527: https://arxiv.org/abs/1812.02527
- Pal, J. (2024). "Long Short-Term Memory Pattern Recognition in Currency Trading" (Wyckoff phases, synthetic data). arXiv 2403.18839: https://arxiv.org/abs/2403.18839
- Taylor, V. (2026). "Evaluating the Predictive Validity of ICT's AMD Model on NQ." arXiv 2610.35887: https://arxiv.org/abs/2610.35887
- Reddit r/Daytrading, "I analyzed 13000 Wyckoff accumulation signals over 20 years" (method not accessible): https://www.reddit.com/r/Daytrading/comments/1rqpcrw/i_analyzed_13000_wyckoff_accumulation_signals/

Supply/demand zones:
- Sam Seiden, "Breaking In Supply/Demand Zones" (FXStreet webinar): https://www.youtube.com/watch?v=uX6TUrTxD7U
- Rayner Teo, "How To Draw Supply And Demand Zones": https://www.tradingwithrayner.com/supply-and-demand-zones/
- ProEA, "Supply and Demand Zones" (freshness "an assumption, not a measured result"): https://proea.app/en/blog/supply-and-demand-zones
- Sibling evidence on PD arrays and freshness (Nordman OB/FVG studies, MarketTrace, Barot SSRN 7148099): `study/ict_pd.md` §2.1-2.2.

Sibling studies referenced: `study/ict_liq.md` (E4-E7, ICT-1, ICT-2), `study/ict_pd.md` (ICTPD-1), `study/ict_struct.md` (ICTS-1, ICTS-2), `study/bias_dol.md` (BIAS-1, BIAS-2, BIAS-4), `study/smc_impl.md` (SMC-2, SMC-3), `study/ict_time.md` (TIME-1).
