# Forecasting the next draw: bias methods. Study for DOL Engine v2

Domain: how practitioners and researchers decide whether the next session, day or week will take **buy-side or sell-side liquidity** (the side choice behind the draw vector **D**), how likely that is, and when. Covered: ICT daily bias, Candle Range Theory (CRT), previous-candle high/low statistics on D/W/4H/1H, weekly-open and midnight-open bias, order-flow/structure bias, dealing-range position, momentum vs mean reversion, sweep-and-reverse vs breakout-continuation, Turtle Soup / Oops / smash day, Crabel contraction.

Line numbers refer to `brief/baseline_v2.pine` (identical to `indicators/dol_engine.pine`). Sibling studies are referenced where they already cover a topic: `ict_liq.md` (liquidity, sweeps, E1-E15), `ict_pd.md` (PD arrays, premium/discount), `ict_time.md` (killzones, sessions, weekly profiles, volatility clock).

Reproduction: every number tagged **[this study]** comes from the scripts in `study/bias_tools/` run on the data in `study/bias_data/`. The scripts are `prevcandle.py`, `race.py`, `cells.py`, `openrel.py`, `turtle.py`, `nr.py` and `sidesel.py`, with outputs in `out_*.txt`. Run them with `python3 -I <script>` from inside `bias_tools/`.

---

## 0. Executive summary

1. **"Which side gets taken first" is mostly geometry.** For the previous candle's high H1 vs low L1, the parameter-free gambler's-ruin rule P(H1 first) = (C − L1)/(H1 − L1) is right **70-81%** of the time. That holds on 17 dataset/reference combinations: S&P 500 and NASDAQ daily 1999-2018, GOOG daily, weekly, EURUSD 1H/4H, and NQ/GC/EURUSD 1H 2024-26. [this study]
2. **The ICT daily-bias rule adds nothing beyond geometry.** The rule is "closed above the prior high → PDH next; swept and closed back inside → opposite side". It is right **69-76%** of the time (bias side first among decided, 3 candles). A volatility-preserving shuffle null, which keeps candle shapes but destroys any sequence information, scores **68-76%**. The difference is −2.2 to +1.9 pp on 13 datasets. Used as a hard rule it is **worse** than geometry: **64-73%**, because it ignores where the close sits inside the range. [this study]
3. **CRT has no edge over geometry.** CRT means candle 2 sweeps candle 1's extreme and closes back inside, and candle 3 targets the opposite extreme. The target is reached before the sweep extreme in only **39-48%** of decided cases, and the null scores the same. An independent 4,200-variation CRT backtest on NQ (2021-2026) found that its surviving variants tied a coin-flip-direction placebo. The AMD/Power-of-3 test on NQ (N = 484 signal days) found **no directional information beyond the daily trend regime**.
4. **Structure, trend and open-relative features add about ±2-4 pp at most, and the sign changes with asset and timescale.**
   - Daily equity indices mean-revert after close-throughs. The raw ruin model is overconfident there: P 0.73 vs 0.83 after an up close-through.
   - NQ and gold intraday are close to geometry: excess within ±2 pp.
   - FX hourly mean-reverts.
   - "Above the weekly open → PWH first" is right 51-64% of the time against geometry's 72-80%, and adds nothing out-of-sample.
   - The pivot-structure bias gets a logistic weight of about 0 in every dataset.
   - The sibling structure study measured the engine's own D at **0.49-0.54** out-of-sample, the same as random-walk controls.
5. **The engine currently chooses the side by D (draw-side first, ×0.5 counter-draw, 30% draw weight), not by geometry.** In an engine-like simulation, choosing the side by a structure vote instead of by first-passage geometry costs **4-10 pp** of which-side-first accuracy and **2-7 pp** of hit-within-H on all 5 datasets tested. [this study, `sidesel.py`]
6. **Design consequence.** D should become a **calibrated probability that the buy-side finalist is reached before the sell-side finalist**. Its prior is pure race geometry, already implemented as `f_race`/`f_raceH`, lines 447-482. Structure, raid, previous-candle and regime features should enter only as **weights learned online on the chart**, judged prequentially against geometry in a new **side ledger** (Brier skill). Where they have no skill, the engine degrades gracefully to geometry, and the panel says so honestly. That gives proposals BIAS-1 and BIAS-2. BIAS-3 adds the trader-facing "daily bias" readout (P(prior high first), P(prior low first), P(neither) per mode timeframe). BIAS-4 removes the unsupported "raid rejected = reversal" sign.

---

## 1. Concepts: precise definitions and parameters

Notation for any timeframe: candle t−2 has high/low H2/L2; candle t−1 (the "previous candle") has open/high/low/close O1/H1/L1/C1; candle t is the one being forecast. "Taken" means **traded through** (strict `>`/`<`), as the engine does for liquidity (`touched`, line 623). The first-touch outcome over K candles is resolved at bar granularity. A bar that trades through both levels is "ambiguous" and excluded from first-touch rates.

### 1.1 The forecasting question as a race (the geometry baseline)

- **Race.** At decision time, with price x, an upper liquidity level U and a lower level D:
  - For a driftless random walk, P(U before D) = (x − D)/(U − D). This is the gambler's ruin.
  - With drift μ and per-bar volatility σ, with k = 2μ/σ²: P = (1 − e^{k·b})/(e^{−k·a} − e^{k·b}), where a = U − x and b = x − D.
  - The engine implements exactly this in `f_race` (447-464). `f_raceH` (466-482) gives the same race truncated to h bars.
- **Previous-candle version.** U = H1, D = L1, x = C1 (decision at the close) or x = Ot (decision at the next open, when the open is inside [L1, H1]). Then P(H1 first) = (C1 − L1)/(H1 − L1), which is the close-location value (CLV) of the previous candle.
- **Why it matters.** Every "bias rule" built from where the previous candle closed carries this geometry. A close above H2 is necessarily near H1. A close back inside after sweeping H2 is necessarily below H1, and often far below it. A rule's raw hit rate therefore says nothing about information until it is compared with geometry or a shape-preserving null.

### 1.2 Previous-candle range states (exhaustive taxonomy used in this study)

| Class | Rule (candle t−1 vs t−2) | Practitioner reading |
|---|---|---|
| close-through up | H1 > H2, L1 ≥ L2, C1 > H2 | bullish continuation, "PDH+ next" (draw = H1) |
| sweep-reject up (bear CRT) | H1 > H2, L1 ≥ L2, C1 ≤ H2 | bearish: "swept PDH, failed to close above"; target L2 (CRT) or L1 |
| close-through down | L1 < L2, H1 ≤ H2, C1 < L2 | bearish continuation (draw = L1) |
| sweep-reject down (bull CRT) | L1 < L2, H1 ≤ H2, C1 ≥ L2 | bullish; target H2 (CRT) or H1 |
| inside | H1 ≤ H2 and L1 ≥ L2 | neutral; "expansion next", both extremes are targets |
| outside, close above H2 / below L2 / inside | H1 > H2 and L1 < L2 | by close: continuation / continuation / neutral |

Edge cases:

- **Equal extremes.** H1 = H2 is not a sweep. This matches the engine's equal-high rule.
- **Day boundary.**
  - Futures use the 18:00 ET exchange day, while ICT uses midnight or 18:00 and edgeful uses the NY session (09:30-16:00 for YM/NQ). Results differ in detail.
  - The engine uses `timeframe.change("D")` (line 945), i.e. the exchange day.
- **Gap opens beyond H1/L1.** The prior extreme is already taken at the open. edgeful calls this an "outside day open". The race is then decided at once, so it must be excluded from first-touch statistics (done in `race.py` with `ref='open'`).

### 1.3 ICT daily bias (community codification) and its weekly version

- **Bullish**:
  - if C1 > H2 (closed through the prior high: continuation, draw = today's PDH = H1);
  - or if L1 < L2 and C1 > L2 (swept the prior low and closed back inside: draw = H1, the "PDH").
- **Bearish** mirrors this.
- **Otherwise** neutral (inside day, or outside day closing inside).
- **Weekly.** The same on weekly bars for PWH/PWL.
- **TTrades framing** (ttrades.com "Easy daily bias"):
  - a continuation day "opens, trades lower first, respects the equilibrium (50%) of the previous day's range, and then trades up and through the previous day's high";
  - "wick size helps determine whether expansion or limited range is more likely".
  - The published page gives no numbers.
- **Parameters:** none, except the day-boundary choice and optionally a 50% equilibrium filter.
- **Failure modes:**
  - pure geometry (section 2.2);
  - session-definition sensitivity;
  - regime dependence: equity indices mean-revert after down close-throughs (section 2.5).

### 1.4 Candle Range Theory (CRT)

Sources: LuxAlgo library concept page; tradingwyckoff.com CRT guide.

- **Roles.**
  - Candle 1 = the range (high, low, 50% = equilibrium).
  - Candle 2 = manipulation: it trades beyond one extreme of candle 1 and closes back inside. A close beyond the extreme voids the CRT; that is a breakout.
  - Candle 3 = distribution, aimed at the opposite extreme of candle 1. Some teach the 50% level as the first target.
- **Variants.** Strict (one sweep candle that closes inside) vs flexible (extra inside candles allowed, or a later confirmation candle). Commonly paired as an HTF range candle (monthly through 1H) with LTF confirmation (MSS or FVG).
- **Filters.** Practitioners "give most weight to a candle 2 that sweeps into a higher-timeframe key level ... and treat a CRT in open space as weak" (LuxAlgo).
- **Practitioner win-rate claims** (tradingwyckoff, no data shown): "Raw CRT 45-50%", and "CRT + Wyckoff + killzone + key level 60-65%".
- **Failure modes:** the CRT target is usually farther than the sweep extreme (geometry < 50%); after an equity-index up-sweep, the swept high is retaken more often than chance (section 2.3).

### 1.5 Sweep-and-reverse family: Turtle Soup, Oops, smash day, outside-day open

- **Turtle Soup** (Raschke, *Street Smarts*). Price makes a new N-day low (N = 20) where the previous N-day low is at least 4 days old, then trades back above that old low. Enter long, with the stop just under the new low. Mirror for shorts. This is the external-liquidity version of a CRT sweep.
- **Larry Williams "Oops".** The session opens below the prior day's low (a gap), then trades back up to that low, which triggers the long. It needs a real session gap (unedited description, Unger Academy).
- **Smash day** (Williams, tested by RogueQuant). The day closes below the prior day's low (often the lowest close or low of 3-8 days). Buy if the next day trades above the smash-day high; exit at the first profitable open ("bailout").
- **edgeful "outside day" open.** The open is beyond PDH or PDL; measure how often price retraces to tag the prior extreme.

### 1.6 Open-relative bias (midnight open, weekly open, "true day open")

- **Rule.** If price is above the period's opening price, the period is bullish and the period's (or the prior period's) high is the draw; mirror for below. Common variants:
  - the midnight (00:00 NY) open;
  - the 18:00 futures open;
  - the weekly Sunday open;
  - ICT's "true day open" and Power-of-3 framing: the open is the accumulation reference, and the manipulation trades on the wrong side of it before distribution.
- **Parameters.** The anchor time, and the decision time (e.g. at 08:00 or at the London close).
- The engine uses the midnight, London and NY opens only as **confluence anchors** (964-966, 1931).

### 1.7 Weekly profiles (templates)

Covered in depth by `ict_time.md` 1.10. In short, the high or low of the week tends to form early (Mon-Tue) in trending weeks, and "midweek reversal" and "consolidation-Thursday reversal" are named templates. The arcsine law already predicts most of the "high/low forms early" effect. For the side choice, weekly profiles reduce to "which of PWH/PWL is taken first", which section 2.6 tests.

### 1.8 Order-flow / structure bias (what the engine's D is)

- **ICT "institutional order flow".** On the HTF, bullish order flow means down-close candles (bullish OBs) and bullish FVGs are respected: bodies close above their consequent encroachment (50%). Disrespect, meaning a body close through them, flips the flow. The practitioner sources are video lectures with no stated thresholds.
- **SMC structure.** Swing bias from BOS/CHoCH on confirmed pivots (the engine's `f_structure`, 708-782). Internal bias flips on a body close through the last swing.
- **Engine D** (1891-1894):
  - D = clamp((wS·sV + wM·mV + wL·liqEvt)/(wS+wM+wL)), with sV = 0.5·htfBias + 0.3·stfBias + 0.2·exeIB;
  - mV = displacement direction with half-life 12;
  - liqEvt = decayed raid outcomes (HOLD = continuation +1, REJECT = reversal −1, tier-weighted; 1580-1582);
  - side gate |D| ≥ 0.35 (`dGate`).

### 1.9 Dealing-range position, premium/discount, close location

- **Position.** pos = (x − rangeLow)/(rangeHigh − rangeLow).
  - ICT reads it at the HTF dealing range: buy in discount (pos < 0.5) toward the premium draw, sell in premium.
  - The previous-candle version is the CLV of 1.1. It is the single most predictive feature for which prior extreme is taken first, through geometry.
- **Engine.** Shows premium/discount % per timeframe in the Terminal panel only (2324-2333). `htfEQ`/`dayEQ` are confluence anchors (967-968).

### 1.10 Momentum vs mean reversion, breakout-continuation vs sweep-reversal

- **Breakout.** C1 beyond the N-bar extreme (N = 20, Donchian) → continuation expected.
- **Sweep.** A wick beyond the extreme and a close back inside → reversal expected (1.4-1.5).
- **Academic picture:**
  - Time-series momentum at 1-12 months (Moskowitz, Ooi & Pedersen 2012, JFE): strong, but outside our horizon.
  - Markets are in a trending regime from hours to years and a reversion regime at shorter and longer scales; weak trends persist and strong trends revert (Safari & Schmidhuber 2025, arXiv 2501.16772).
  - SPY lag-1 daily autocorrelation is −0.081 (z = −7.4), but it is **magnitude-driven, not directional** (sign test p = 0.11), and mean reversion is "confined to exchange-traded equities and sovereign bonds; credit, commodities, FX and crypto are indistinguishable from random walks" (arXiv 2606.29591).

### 1.11 Contraction then expansion (Crabel)

- **Definitions.** NR4/NR7: the candle's range is the narrowest of the last 4/7. Inside day: as in 1.2.
- **Crabel's premise.** Contraction is followed by expansion. Practitioners trade a break of the inside/NR candle's extreme (often with an opening-range breakout filter).

### 1.12 AMD / Power of 3 (London sweep of Asia → NY delivery)

As operationalized by arXiv 2610.35887:

- Asia range 19:00-00:00 ET.
- London (02:00-05:00 ET) breaches one Asia extreme by δ = 10 NQ points before 04:00 and closes back inside before 05:00.
- NY (09:40-10:30) should deliver to the opposite Asia extreme.
- Bilateral breaches are excluded.

This is the intraday-session version of CRT. Killzone timing itself is in `ict_time.md`.

---

## 2. Evidence (numbers and sources)

### 2.0 Data and method for the [this study] numbers

**Data:**

| Dataset | Source | Coverage | Bars |
|---|---|---|---|
| S&P 500 and NASDAQ Composite daily | `arch` package datasets | 1999-01-04 to 2018-12-31 | 5,031 each |
| GOOG daily | `backtesting` package | 2004-2013 | 2,148 |
| EURUSD 1H, timestamped | `backtesting` package | 2017-04 to 2018-02 | 5,000 |
| NQ, GC, EURUSD 1H | sibling study's Yahoo 60m files | about 2024-11 to 2026-11 | 11,400-12,285 each |

- Weekly bars are aggregated from daily bars.
- "4H" for EURUSD 2017-18 is clock-aligned.
- "4bar" for the sibling hourly files means non-clock-aligned 4-hour blocks; those files carry no timestamps.

**Null 1, the vol-preserving shuffle** (`prevcandle.py`):

- Each bar is represented by (gap, high−open, low−open, close−open) in log terms, divided by a causal EWMA of the log range.
- The normalized shapes are permuted, re-scaled by the original volatility path and chained.
- This keeps the bar-shape distribution and the volatility clustering but destroys any sequential information.
- **real − null** therefore measures information **beyond range geometry**.
- Caveat: on intraday data the null over-produces outside bars because of the intraday volatility clock. Compare intraday **conditional first-touch** rates, not raw "both taken" rates.

**Null 2, the parameter-free ruin model** p = (C1 − L1)/(H1 − L1) (`race.py`, `cells.py`):

- **Excess** = observed P(H1 first) − mean ruin p in the same cell.
- **OOS:** two-fold logistic regression (train on one half, test on the other) for geometry alone vs geometry plus features.

**Caveats:**

- No transaction costs. They are not needed for probability forecasting.
- Samples overlap within K bars, so the binomial SEs shown are optimistic by roughly √K for K-window statistics.
- The daily data ends in 2018, so the post-2019 regime is untested on daily bars. The sibling hourly data covers 2024-26.

### 2.1 Base rates: how often the previous candle's extremes are taken [this study]

| Dataset | P(H1 taken next) | P(L1 taken next) | P(both) | P(inside) | P(≥1 side) |
|---|---|---|---|---|---|
| S&P 500 D | 0.513 | 0.446 | 0.090 | 0.130 | 0.870 |
| NASDAQ D | 0.554 | 0.465 | 0.107 | 0.088 | 0.912 |
| GOOG D | 0.503 | 0.453 | 0.089 | 0.133 | 0.867 |
| S&P 500 W | 0.592 | 0.439 | 0.119 | 0.089 | 0.911 |
| NASDAQ W | 0.601 | 0.447 | 0.121 | 0.074 | 0.926 |
| NQ 1H | 0.511 | 0.461 | 0.116 | 0.145 | 0.855 |
| GC 1H | 0.489 | 0.463 | 0.117 | 0.165 | 0.835 |
| EURUSD 1H (24-26) | 0.432 | 0.440 | 0.079 | 0.206 | 0.794 |

- **Multi-candle reach** (S&P D), i.e. P(prior high taken within k days):
  - prior high: 0.513 (k=1), 0.642 (k=2), 0.709 (k=3), 0.776 (k=5);
  - prior low: 0.446, 0.563, 0.627, 0.694;
  - either: 0.870, 0.970, 0.991, 0.998.
  - Intraday NQ 1H, either: 0.855 (k=1), 0.945 (k=2), 0.970 (k=3), 0.987 (k=5).
- **External agreement:**
  - An Elite Trader user's ES count: PDH or PDL touched on 90.32% of days (168/186).
  - edgeful, NQ opening inside the prior NY session range: one side tagged 75% (6 months).
  - edgeful, SPY June-December 2024 inside-day report: PDH touched 52%, PDL 40%, both 15.28% (72 days).

### 2.2 The previous-candle bias rule vs the shuffle null [this study, `prevcandle.py`]

"Bias side first | decided within 3 candles", for the ICT rule of 1.3 (outside-day close beyond = continuation, inside = no call):

| Dataset | real | null | real−null | n |
|---|---|---|---|---|
| S&P 500 D | 0.688 | 0.710 | −0.022 | 3,799 |
| NASDAQ D | 0.702 | 0.704 | −0.002 | 3,897 |
| GOOG D | 0.697 | 0.678 | +0.019 | 1,586 |
| S&P 500 W | 0.753 | 0.763 | −0.009 | 799 |
| NASDAQ W | 0.763 | 0.758 | +0.005 | 806 |
| EURUSD 1H 17-18 | 0.706 | 0.726 | −0.019 | 3,349 |
| EURUSD 4H 17-18 | 0.712 | 0.714 | −0.002 | 775 |
| NQ 1H | 0.727 | 0.739 | −0.013 | 7,833 |
| NQ 4bar | 0.758 | 0.749 | +0.008 | 1,823 |
| GC 1H | 0.708 | 0.725 | −0.017 | 7,546 |
| GC 4bar | 0.717 | 0.723 | −0.006 | 1,816 |
| EURUSD 1H 24-26 | 0.704 | 0.725 | −0.021 | 8,156 |
| EURUSD 4bar | 0.710 | 0.730 | −0.020 | 1,984 |

- **By class** (next candle, S&P D). Close-through up: P(H1) 0.663 vs null 0.708, and P(bias side | exactly one side taken) 0.763 vs 0.767. The headline "after a close above PDH, PDH is taken next ~2/3 of days" is real, and it is all geometry.
- **Inside candles.** They lean very slightly to the low on the S&P and NASDAQ: P(only L1) +4.2/+3.3 pp vs null. That is about 2 SE, and it does not replicate on intraday data.

### 2.3 CRT and Turtle Soup [this study, `prevcandle.py`, `turtle.py`]

**CRT target first** (opposite extreme of candle 1 before the candle-2 sweep extreme, within 3 candles, among decided):

| Dataset | real | null | n |
|---|---|---|---|
| S&P 500 D | 0.458 | 0.458 | 1,329 |
| NASDAQ D | 0.472 | 0.470 | 1,258 |
| GOOG D | 0.435 | 0.431 | 586 |
| S&P 500 W | 0.480 | 0.465 | 306 |
| NASDAQ W | 0.476 | 0.477 | 288 |
| EURUSD 1H 17-18 | 0.449 | 0.403 | 1,395 |
| EURUSD 4H 17-18 | 0.399 | 0.391 | 283 |
| NQ 1H | 0.430 | 0.411 | 3,111 |
| NQ 4bar | 0.433 | 0.396 | 610 |
| GC 1H | 0.412 | 0.426 | 3,026 |
| GC 4bar | 0.388 | 0.425 | 691 |
| EURUSD 1H 24-26 | 0.456 | 0.441 | 3,129 |

- The mean excess is about +1 pp intraday and 0 on daily and weekly bars.
- The CRT target is reached **at all** within 3 candles 45-62% of the time. That is no better than the null: bear CRT on the S&P D was 0.503 vs 0.548.
- **After an equity-index up-sweep that closed back inside**, the swept high is retaken within 3 days **more** often than the null: S&P D 0.691 vs 0.639; NASDAQ D 0.714 vs 0.650; S&P W 0.743 vs 0.653. This is sweep-continuation, the opposite of the CRT reading. It matches sibling E7 (Mahadzva, SSRN 7430998: swept levels predict continuation in 65/66 fold selections).

**Turtle Soup** (`turtle.py`; N = 20, old extreme at least 4 bars old, close back inside; first touch within 5 bars, excess = expected side first − geometry):

| Dataset | Bull TS excess (n) | Bear TS excess (n) |
|---|---|---|
| S&P D | −0.105 (58) | −0.001 (79) |
| NASDAQ D | −0.017 (59) | −0.129 (53) |
| GOOG D | −0.028 (23) | −0.120 (31) |
| NQ 1H | −0.020 (159) | −0.037 (169) |
| NQ 4bar | −0.061 (32) | −0.048 (41) |
| GC 1H | +0.003 (180) | +0.014 (162) |
| GC 4bar | −0.076 (33) | +0.082 (41) |
| EURUSD 1H | −0.006 (145) | +0.007 (149) |
| EURUSD 4bar | +0.009 (41) | −0.056 (34) |

Turtle Soup is never reliably above geometry.

**External evidence:**

- **"I Backtested 4,200 Variation of Candle Range Theory"** (Strange Labs, YouTube, 2026). NQ 2021-2026; in-sample 2021-24, validation 2025, OOS 2026. 6 timeframe pairs × 10 sweep definitions × 7 stops × TP variants.
  - About 80% of variants had a profit factor near 0.92; about 10% reached PF 1.8-3.
  - Survivors were compared with a "dumb twin" that took the same trades with a coin-flip direction: they "basically tied".
  - Grade: weak to moderate (transparent design, not peer-reviewed).
- **AMD on NQ** (Taylor, arXiv 2610.35887, 15m Databento, January 2022 to July 2026).
  - The manipulation signal fires on 44% of days. On 57% of valid signals the target is delivered before the 09:40 entry.
  - "No directional information beyond the daily trend regime". Regime = daily close vs EMA20 (±0.5%).
  - Trend-aligned signals are correct 61.6% (n = 112) and 70.8% (n = 72). Trend-opposed signals are correct 29.6% (n = 71) and 24.8% (n = 153).
  - "After London sweeps the Asia high in a bull market, price closes above the [Asia] midpoint 75.2% of the time."
  - The result is robust to δ = 5-20 points and EMA 10-50.
  - Grade: moderate (single preprint, careful method, BH-corrected).

### 2.4 Geometry vs bias features, out-of-sample [this study, `race.py`]

Outcome: H1 traded through before L1 within 3 candles (decided cases only). Decision at the close of candle t−1. Columns are OOS accuracy (Brier).

| Dataset | ruin (no fit) | ICT rule (hard) | geometry + ICT + CRT + CLV + colour + 20-bar trend + 5-bar return + pivot bias |
|---|---|---|---|
| S&P 500 D | 0.702 (0.207) | 0.652 (0.220) | 0.703 (0.198) |
| NASDAQ D | 0.719 (0.199) | 0.670 (0.215) | 0.720 (0.189) |
| GOOG D | 0.708 (0.188) | 0.656 (0.218) | 0.710 (0.188) |
| S&P 500 W | 0.771 (0.157) | 0.720 (0.195) | 0.750 (0.166) |
| NASDAQ W | 0.788 (0.145) | 0.729 (0.192) | 0.779 (0.153) |
| EURUSD 1H 17-18 | 0.746 (0.172) | 0.658 (0.216) | 0.743 (0.174) |
| EURUSD 4H 17-18 | 0.719 (0.181) | 0.648 (0.215) | 0.720 (0.182) |
| NQ 1H | 0.761 (0.162) | 0.681 (0.209) | 0.762 (0.162) |
| NQ 4bar | 0.789 (0.149) | 0.690 (0.200) | 0.789 (0.150) |
| GC 1H | 0.747 (0.173) | 0.664 (0.216) | 0.745 (0.174) |
| GC 4bar | 0.758 (0.163) | 0.666 (0.214) | 0.752 (0.163) |
| EURUSD 1H 24-26 | 0.731 (0.185) | 0.661 (0.218) | 0.732 (0.181) |
| EURUSD 4bar | 0.759 (0.171) | 0.663 (0.216) | 0.742 (0.174) |

**Decision at the next open** (open inside [L1, H1]; which extreme is taken first during that candle):

| Dataset | ruin | ICT hard | geometry + all |
|---|---|---|---|
| S&P 500 D | 0.756 | 0.658 | 0.758 |
| NASDAQ D | 0.773 | 0.637 | 0.778 |
| GOOG D | 0.778 | 0.645 | 0.776 |
| S&P 500 W | 0.795 | 0.724 | 0.783 |
| NASDAQ W | 0.811 | 0.695 | 0.792 |

**Reading:**

- Features add **≤ ±2 pp accuracy**. Brier improves only where the raw ruin probability is mis-calibrated: daily equities, where a fitted CLV slope shrinks the extremes.
- Full-sample logistic weights for the pivot-structure bias: −0.12 to +0.05 on 12 of 13 datasets (NASDAQ W +0.26).
- The ICT-class weights are −0.1 to +0.24 and the CRT weights −0.23 to +0.35, with mixed signs across datasets. Both are small and partly offset the CLV term, which carries the geometry.

### 2.5 Excess over geometry by class × trend regime [this study, `cells.py`]

Regime: close vs EMA20, band ±0.5% on daily bars, ±1% weekly, ±0.1% 1H, ±0.2% 4bar. Excess = P(H1 first) − mean ruin p, within 3 candles.

- **Daily equities: the ruin model is overconfident at the extremes.**
  - S&P D close-through up: P 0.73 vs geometry 0.83, excess **−0.099 ± 0.011** (uptrend regime, n = 972).
  - Close-through down: H1 taken first **+7 to +15 pp** more than geometry.
  - Bear CRT: H1 first **+7 to +22 pp** more than geometry.
  - This is daily mean reversion. It matches arXiv 2606.29591 and the smash-day result.
- **Intraday NQ and GC.** Every cell is within ±3 pp except a few small ones. Geometry is well calibrated.
- **EURUSD 1H (24-26).** Close-through up −5 to −7 pp in up and neutral regimes; close-through down +5.5 to +7 pp. Hourly FX mean-reverts.
- **Trend regime overall.**
  - S&P D: uptrend −3.6 pp, downtrend +3.0 pp (mean reversion against the regime).
  - S&P W: uptrend +2.2 pp (weak persistence).
  - NQ 1H: uptrend +1.5, downtrend −1.2 pp (weak momentum).
- **Conclusion.** Regime and class effects are small (±2-4 pp), their sign is asset- and timescale-specific, and they must be **learned per chart, never hard-coded**.

### 2.6 Open-relative bias [this study, `openrel.py`]

Weekly open, S&P and NASDAQ 1999-2018. Decision after 1 or 2 days of the week, PWH and PWL both still untaken; which is taken first in the rest of the week:

| Case | "Above weekly open → PWH first" | ruin geometry | geometry + open sign (OOS Brier vs geometry alone) |
|---|---|---|---|
| S&P, after 1 day | 0.515 | 0.721 | 0.1777 vs 0.1780 |
| S&P, after 2 days | 0.636 | 0.805 | 0.1550 vs 0.1521 |
| NASDAQ, after 1 day | 0.608 | 0.749 | 0.1765 vs 0.1762 |
| NASDAQ, after 2 days | 0.623 | 0.732 | 0.1851 vs 0.1858 |

- The fitted open-sign weight is −0.03 to −0.21. Given geometry, being *below* the open slightly favours the high, which is mean reversion plus equity drift.
- **Midnight open, EURUSD 2017-18.** Samples of 21-92 days are too small to conclude anything. Point estimates show no gain over geometry.

### 2.7 Engine-like side selection [this study, `sidesel.py`]

**Setup:**

- Candidates: the nearest unswept pivot pool above (BSL) and below (SSL) (pivot length 5, both within 3 ATR), sampled every 3 bars.
- D proxy, mirroring line 1892: 0.5·HTF pivot bias (24-bar blocks) + 0.3·STF (4-bar) + 0.2·chart internal bias, with gate 0.35. Below the gate, the rule falls back to geometry, as the engine does when `dirSide == 0`.
- Geometry rule: the side with the higher ruin probability.

| Dataset (horizon) | D-first: first-touch acc / hit≤H | geometry: first-touch acc / hit≤H |
|---|---|---|
| NQ 1H (H=30) | 0.562 / 0.679 | 0.602 / 0.698 |
| GC 1H (H=30) | 0.564 / 0.644 | 0.640 / 0.681 |
| EURUSD 1H (H=30) | 0.551 / 0.648 | 0.638 / 0.705 |
| S&P 500 D (H=10) | 0.521 / 0.443 | 0.620 / 0.514 |
| NASDAQ D (H=10) | 0.544 / 0.462 | 0.635 / 0.518 |

- Geometry wins on all 5 datasets: +4 to +10 pp first-touch, +2 to +7 pp hit-within-H.
- A hybrid that uses D only when the race is within 0.15 of 50% lands in between.
- **Sibling cross-check** (`study/ict_struct_tools/results.txt`, "skill-weighted D"): the engine's D (|D| ≥ gate) has OOS accuracy 0.543 (NQ), 0.488 (GC) and 0.490 (EURUSD), and htfBias alone 0.502-0.522, on symmetric ±1.5 ATR first passage within 30 bars. Random-walk controls give the same numbers.

### 2.8 Contraction (Crabel) [this study, `nr.py`]

| | P(next range > 20-bar median) | P(next bar takes both prior extremes) |
|---|---|---|
| base | 0.48-0.50 | 0.08-0.14 |
| NR7 | 0.26-0.45 (lower than base on every dataset) | 0.16-0.29 |
| inside | 0.32-0.57 | 0.12-0.21 |

- "Contraction → expansion" is **false in absolute terms**: volatility clusters.
- The next candle takes **both** extremes of a narrow candle about twice as often, because they are close. That is geometry again, and relevant for "both sides" risk.

### 2.9 Other external evidence for this domain

| # | Claim | Source and data | Result | Grade |
|---|---|---|---|---|
| X1 | PDH/PDL break → session direction | edgeful blog, YM, 6 months, NY session | PDH broken → green 67% (open→close) / 81% (prior close→close); PDL broken → red 62% / 66% | weak-moderate |
| X2 | Gap beyond PDH/PDL retraces to it | edgeful outside-days report, NQ, 12 months | Retrace to PDH 65%, to PDL 58%. Gap 0.1-0.19% → 93% / 83% retrace; gap 0.6-0.99% → 25% / 0%. The size gradient is pure distance | weak-moderate |
| X3 | Inside-day breakout | edgeful, SPY June-December 2024 | Inside days 22% (16/72) in that window; PDH touched 52%, PDL 40%, both 15.28% | weak (small n) |
| X4 | Smash day (close < PDL → buy above smash high, exit first profitable open) | RogueQuant substack, 15 futures 2014-24 | S&P longs 80% win rate, PF 6.94; index shorts weak; asymmetric by asset | weak-moderate |
| X5 | AMD / Power of 3 | arXiv 2610.35887, NQ 2022-26, N = 484 | Direction = trend regime, not the sweep (2.3) | moderate |
| X6 | CRT placebo | Strange Labs YouTube, NQ 2021-26, 4,200 variants | Survivors tie a coin-flip twin | weak-moderate |
| X7 | Daily equity autocorrelation | arXiv 2606.29591, SPY 1993-2026 and a 21-asset panel | ρ(1) = −0.081, z = −7.4, magnitude-driven (sign p = 0.11); lag-3 directional reversal p = 0.02; FX, commodities and crypto random-walk-like | moderate |
| X8 | Trend vs reversion by timescale | Safari & Schmidhuber, arXiv 2501.16772 (14 years of tick data, 30 years of daily futures) | Trending regime from hours to years; reversion shorter and longer; weak trends persist, strong ones revert | moderate |
| X9 | Intraday OHLCV momentum on MNQ | arXiv 2605.04004, 947 days of 5m data, 2021-25, walk-forward | 0 of 14 signal families pass; ORB long T = 0.88 | moderate (negative) |
| X10 | Apparent skill vs nulls | arXiv 2611.12141, NQ/ES intraday | 0 of 160 foundation-model cells beat no-change; a sign-randomised null reproduces about 95% of the apparent rank-IC | moderate (methodological) |
| X11 | Time-series momentum | Moskowitz, Ooi & Pedersen 2012, JFE 104(2) | 1-12 month horizon, 58 futures | strong (not at DOL horizons) |
| X12 | Sweeps → continuation | Mahadzva SSRN 7430998 (sibling E7) | Continuation in 65/66 fold selections | moderate |
| X13 | Equal highs vs plain swings | sibling E6 | "Equal" adds < 1 pp beyond distance | moderate |

### 2.10 Net reading for the forecasting problem

- **Where (which side).** The best single predictor of which of two opposing pools is taken first is **relative distance**: the race. Every named bias method tested here (the ICT previous-candle rule, CRT, Turtle Soup, open-relative bias, pivot-structure bias, EMA trend regime) adds at most a few percentage points beyond it, with signs that differ by market and timescale. Some of these methods are *worse* than geometry when used as hard rules.
- **How likely.**
  - Calibrated geometry: 70-81% for previous-candle extremes and about 60-64% for the nearest swing pools.
  - Daily equities need shrinkage of the extremes (mean reversion). Intraday NQ and GC are already calibrated.
- **When.**
  - At least one prior extreme is taken within 1 candle 79-93% of the time, and within 2 candles 92-99%.
  - After narrow candles, both sides are taken about twice as often.
  - Session timing is covered in `ict_time.md`.
- **What this means for D.** D's current inputs are measured at coin-flip skill. The engine's side choice should be driven by the race, and D's inputs should only be allowed to move it by weights the chart itself has earned.

---

## 3. Engine gap analysis (baseline_v2.pine)

| Concept | Status | Lines | What the engine does / how it differs |
|---|---|---|---|
| Race geometry between opposing pools | **partial** | `f_race` 447-464, `f_raceH` 466-482, used in `f_invalidation` 1334-1365 | Exists and is correct, but it is used only for the target-vs-invalidation race (R:R, WIN≤H). The **side choice ignores it** |
| Side choice / draw vector D | **wrong (unvalidated prior)** | D 1891-1897; draw pillar 691; counter-draw ×`ctrMult` 692-693; draw-side-first selection 1975, 1998-2005 | D is a hard-coded vote: 0.5/0.2/0.3 weights, sV = 0.5·htf + 0.3·stf + 0.2·exeIB, gate 0.35. Its measured skill is 0.49-0.54. It carries 30% of the score (`wDraw`), halves counter-draw scores, and gates eligibility. Choosing by geometry would raise side accuracy 4-10 pp (2.7) |
| Raid-outcome sign (HOLD = continuation, REJECT = reversal) | **wrong for REJECT** | 1580-1582 | REJECT (close back below a swept BSL) pushes D toward the opposite side. Evidence: CRT/Turtle Soup ≤ geometry; sweep extremes are retaken more than chance on daily equities; AMD direction = trend (2.3) |
| Previous-candle state of HTF/STF/EXE candles | **partial** | `f_rangeTrack` 807-833; PDH/PDL/PWH/PWL 945-961, 1790-1809 | PDH/PDL/PWH/PWL exist as levels with exact print anchors. There is **no class** (close-through / sweep-reject / inside / outside), **no prior close**, **no 4H/1H prior candle**, and **no "which first" probability** |
| ICT daily bias (close through PDH → PDH+ next) | **missing** (correctly; see evidence) | — | Not in D. Evidence says it adds nothing beyond geometry, so it should enter only as a learned feature (BIAS-1) and as an informational class (BIAS-3) |
| CRT | **missing** | — | No detector. Worth showing as an informational event with honest odds (BIAS-7), never as a hard target rule |
| Turtle Soup / Oops / smash day | **partial** | `liqEvt` 1580-1582; `induceBar` 892-895 | Sweeps of any pool feed `liqEvt`, with no age requirement. No evidence that more is needed |
| Open-relative bias (midnight / weekly open) | **present as confluence only (correct)** | 964-966, 1931 | Used only as confluence anchors. Evidence: no directional value beyond geometry, so do **not** add it to D |
| Weekly profile templates | **missing** | — | See `ict_time.md` TIME proposals. As a side predictor they reduce to the PWH/PWL race (2.6) |
| Dealing-range position / premium-discount | **partial** | Panel 2324-2333; `htfEQ`/`dayEQ` 967-968 | Display and confluence only. As geometry it belongs in the race. As an ICT premium/discount prior it should be learned (`ict_pd.md` ICTPD-7) |
| Trend regime (EMA20 ±0.5%) | **missing** | — | Evidence mixed: strong in AMD/NQ 2022-26, ±2-4 pp with variable sign in this study. Learned feature only |
| Momentum vs mean reversion by asset/timescale | **partial** | Empirical PoT surface 1526-1532, `f_empPoT` 1285-1301 (split by `htfBias` regime) | The surface captures drift per htfBias regime. Because htfBias has about zero skill, the 3-way split mostly costs sample size (BIAS-6) |
| Breakout continuation (N-bar close-through) | **missing** | — | Sign is market-specific (2.3): −6 to −9 pp on daily equities and FX 1H, +2 to +5 pp on NQ/GC intraday. Learned feature only |
| Contraction → both sides | **partial** | `coilScore` 886-889 feeds level density | Used as level magnitude, not as a "both sides" or volatility-expansion signal. Evidence says contraction does not predict expansion |
| AMD (London sweep of Asia → NY) | **partial** | `f_kzAff` 597-602 (London ×1.20 on Asia pools) | Timing affinity exists; the direction should follow the regime, not the sweep. Timing is covered by `ict_time.md` |
| Multi-candle reach / timing of prior extremes | **partial** | Empirical surface by ATR distance, 1527-1532 | Generic distance surface; no prior-candle-specific readout (BIAS-3) |
| Side-level accuracy ("which side first") ledger | **missing** | Ledger 1426-1499 grades only "active DOL hit within H" vs a distance-matched baseline | The EDGE metric is distance-matched, so it measures skill beyond distance, which is right. But no metric tests the **side** forecast or D itself |
| Bias table semantics | **present, unmeasured** | Clean 2293-2305; Terminal 2321-2336 | Shows swing (or internal) structure bias, as in the reference product, with no accuracy shown. Evidence: about zero predictive value for the next draw |

---

## 4. Proposals (best first; maximum 10)

General Pine v6 notes for every spec:

- New state updates run inside the confirmed-bar ENGINE block (1518) and on `inCalc` bars where noted.
- No new `request.security` calls; the count stays the same.
- New functions are declared after the helpers they call: `f_race` 447, `f_raceH` 466, `f_logit` 484, `f_sigm` 488.
- Globals are declared in STATE (1020-1080), before STATE HELPERS (1082+).
- Pine has no multiple assignment with commas; write one statement per line.
- UDT fields may hold arrays. Docs, `language/type_system.md`: "Programmers can explicitly define variables, parameters, and fields that accept references to objects of specific collection types".
- `timeframe.change(series string) → series bool` (`reference/timeframe.md`).

### BIAS-1 (P1) · Side ledger with an online-calibrated side model ("P(BSL before SSL)")

**Why.** The core forecasting question is which side is taken first. The engine has no measurement of it, and D's inputs have about zero measured skill (2.4, 2.7). Geometry is the right prior, and anything else must earn its weight on the chart. This turns every bias claim (structure, raids, previous-candle class, premium/discount) into a number the engine reports about itself.

**Algorithm.**

1. **Finalists** (each confirmed `inCalc` bar, before scoring step 17, using the previous bar's scores):
   - For each side s, F_s is the pool level on side s with the highest `lv.scoreND`.
   - `scoreND` is a **new Level field**, the score without the draw pillar and without the counter-draw multiplier, which avoids circularity. In `evaluate` (694-696) add `this.scoreND := f_clamp(100.0 * (raw - wDraw * this.draw / wSum) * mPre, 0.0, 100.0)`, where `mPre` is `this.mult` saved before the ctrMult test at 692.
   - It cannot be recomputed from `lv.mult` at step 14, because `track()` resets `mult` to 1.0 each bar (659) before step 14.
   - Requires `0 < lv.distance(close) ≤ maxATR·atr`.
   - On non-`inCalc` bars, skip 14b and keep the legacy D. Scores are not updated there.
   - `up = F_{+1}.nearEdge()`, `dn = F_{−1}.nearEdge()`. If a side has no finalist, take the nearest `extReg` entry on that side; if there is still none, skip.
2. **Geometry.** `pGeo = f_race(up − close, close − dn, potSig, potMu)`. This is O(1). The within-H conditional version, `pW/(pW+pL)` with `f_raceH`, is optional; the calibration slope absorbs the difference.
3. **Features** (float array, F = 9):
   - `x0 = 1`
   - `x1 = f_logit(pGeo)`
   - `x2 = sV` (legacy structure vote, 1892)
   - `x3 = mV` (displacement, 1893)
   - `x4 = liqHold`
   - `x5 = liqRej` (see BIAS-4)
   - `x6 = prevHTF class rule` (−1/0/+1, from BIAS-3; 0 if not implemented)
   - `x7 = HTF range position` 2·(close − htfRL)/(htfRH − htfRL) − 1, clamped to ±1
   - `x8 = HTF CRT flag` (+1 bull / −1 bear / 0)
4. **Model.**
   - `pMod = f_sigm(Σ w_i·x_i)`, with prior and initial weights `w0 = [0, 1, 0, …, 0]` (pure geometry).
   - Online logistic SGD with shrinkage toward the prior: `w_i += η·((y − p)·x_i − λ·(w_i − w0_i))`, `η = 0.05/√(1 + n/200)`, `λ = 0.01`.
5. **Trials.**
   - Every `sp = max(1, round(H/5))` bars on `inCalc` bars, push `SideTrial(up, dn, pGeo, pMod, x, bar_index)`. The cap is 64; spacing limits the overlap of the H-bar windows.
   - Resolve each later confirmed bar:
     - `u = high > up`, `d = low < dn`;
     - `u xor d` → learn with y = u;
     - `u and d` → discard (ambiguous);
     - neither by H → count as "undecided" and discard.
6. **Prequential scoring.**
   - On each resolution, add `(pMod_at_open − y)²`, `(pGeo − y)²` and accuracy to the stats.
   - Side Skill = 1 − Brier_model/Brier_geo. This is out-of-sample by construction, because the prediction was made before the outcome.
   - Also store the legacy D's Brier using `pD = 0.5 + 0.25·sign(Dlegacy)`, so the panel can show "legacy D skill".

**Pine v6 sketch.**

```pine
// TYPES (after Trial, ~396)
type SideTrial
    float        up
    float        dn
    float        pGeo
    float        pMod
    array<float> x
    int          bar0

// STATE (~1080)
const int SF = 9
var array<float>     sdW   = array.from(0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
var array<float>     sdW0  = array.from(0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
var array<SideTrial> sideT = array.new<SideTrial>()
var array<float>     sdSt  = array.new<float>(7, 0.0)   // n, BrModel, BrGeo, BrLegacyD, accModel, undecided, ambiguous
var float            pUp   = 0.5

// STATE HELPERS (after f_raceAdj, ~1372)
f_dot(array<float> w, array<float> x) =>
    float z = 0.0
    for i = 0 to w.size() - 1
        z += w.get(i) * x.get(i)
    z

f_sideLearn(SideTrial t, int y) =>
    float p  = f_sigm(f_dot(sdW, t.x))
    float n  = sdSt.get(0)
    float lr = 0.05 / math.sqrt(1.0 + n / 200.0)
    for i = 0 to SF - 1
        float wi = sdW.get(i)
        sdW.set(i, wi + lr * ((y - p) * t.x.get(i) - 0.01 * (wi - sdW0.get(i))))
    sdSt.set(0, n + 1.0)
    sdSt.set(1, sdSt.get(1) + math.pow(t.pMod - y, 2))
    sdSt.set(2, sdSt.get(2) + math.pow(t.pGeo - y, 2))
    sdSt.set(3, sdSt.get(3) + math.pow((t.x.get(2) > 0 ? 0.75 : t.x.get(2) < 0 ? 0.25 : 0.5) - y, 2))
    sdSt.set(4, sdSt.get(4) + ((t.pMod >= 0.5) == (y == 1) ? 1.0 : 0.0))
    y

// ENGINE, new step 2b (next to step 2, ~1544): resolve side trials (price-only)
    if sideT.size() > 0
        for i = sideT.size() - 1 to 0
            SideTrial s = sideT.get(i)
            if bar_index > s.bar0
                bool u = high > s.up
                bool d = low < s.dn
                if u != d
                    f_sideLearn(s, u ? 1 : 0)
                    sideT.remove(i)
                else if u and d
                    sdSt.set(6, sdSt.get(6) + 1.0)
                    sideT.remove(i)
                else if bar_index - s.bar0 >= H
                    sdSt.set(5, sdSt.get(5) + 1.0)
                    sideT.remove(i)

// TYPES: Level gets a new field (after `float score`, ~347)
//     float scoreND = 0.0      // score without the draw pillar (set in evaluate)
// LEVEL METHODS, evaluate: save `float mPre = this.mult` just before the counter-draw test (692),
// then after `float raw = ...` (694):
//     this.scoreND := f_clamp(100.0 * (raw - wDraw * this.draw / wSum) * mPre, 0.0, 100.0)
// (mPre excludes ctrMult, so the finalists are chosen free of any draw influence)

// ENGINE, new step 14b (right after sV / mV at 1892-1893; BEFORE drawD / dirSide); inCalc bars only
    float upE = na
    float dnE = na
    float kU  = -1e9
    float kD  = -1e9
    for lv in pool
        float dd = lv.distance(close)
        if inCalc and dd > 0 and dd <= maxATR * atr
            float k0 = lv.scoreND
            if lv.side == 1 and k0 > kU
                kU  := k0
                upE := lv.nearEdge()
            else if lv.side == -1 and k0 > kD
                kD  := k0
                dnE := lv.nearEdge()
    if not na(upE) and not na(dnE)
        float pG = f_race(upE - close, close - dnE, nz(potSig), nz(potMu))
        array<float> xv = array.from(1.0, f_logit(pG), sV, mV, liqHold, liqRej, float(prevHtfRule), htfPos, float(htfCrt))
        pUp := f_sigm(f_dot(sdW, xv))
        int sp = math.max(1, int(math.round(H / 5.0)))
        if inCalc and bar_index % sp == 0 and sideT.size() < 64
            sideT.push(SideTrial.new(upE, dnE, pG, pUp, xv, bar_index))
```

**UX.**

- Terminal panel, new row: `SIDE  BSL 63% · skill +2.1% · n 412`.
- Full view: the learned weights next to their names (e.g. `STRUCT +0.04 · RAID-HOLD +0.11 · CRT −0.02`), plus `legacy D skill −1.3%`.
- Clean style: the tooltip of the target label.

**Expected value.** An honest, calibrated answer to the trader's central question, measured prequentially on the chart. When features have skill on a market (e.g. regime on NQ 2022-26, X5), the model picks it up; when they do not, it stays at geometry.

- **Evidence:** moderate (sections 2.2-2.7; X5, X6, X10).
- **Risk:**
  - SGD noise with few trials. Mitigated by shrinking toward w0 and the decaying η; the panel should show n.
  - Correlated features: logistic regression handles them, unlike additive cell shifts.
  - Overlap between trials makes the effective n smaller (spacing sp).
  - Cost: O(pool) + O(trials·F) per bar, negligible.
- **Effort:** M.

### BIAS-2 (P1) · Draw Source = calibrated side probability (D := 2·pUp − 1)

**Why.** Section 2.7: selecting the side by the structure vote costs 4-10 pp of side accuracy and 2-7 pp of hit-within-H against geometry. The decision history requires "draw-side first with counter-draw fallback". This proposal keeps that architecture and changes **what the draw is**.

**Algorithm.**

- **Input:** `string drawSrc = input.string("Calibrated", "Draw Source", options = ["Calibrated", "Structure Vote"], group = G_FLOW)`.
- **Input:** `float sideGate = input.float(0.10, "Side Gate |P − 50%|", minval = 0.0, maxval = 0.4, step = 0.01, group = G_FLOW)`.
- **INPUTS area:** `float dGateEff = drawSrc == "Calibrated" ? 2.0 * sideGate : dGate`. Replace `dGate` with `dGateEff` at 692 (counter-draw test in `evaluate`) and in the panel (2338).
- **Step 14.** Compute 14b (BIAS-1) first. Then:
  - `drawD := drawSrc == "Calibrated" and not na(upE) and not na(dnE) ? 2.0 * pUp - 1.0 : dLegacy`, where `dLegacy` is the current formula at 1894;
  - `dirSide := drawD >= dGateEff ? 1 : drawD <= -dGateEff ? -1 : 0`.
  - With the prior weights, pUp = pGeo, so the calibrated draw is pure race geometry from the first bar. No warm-up is needed.
- **Draw pillar** (691) is unchanged. With the new D, `0.5 + 0.5·D·side` equals the calibrated P(this side is reached first). The pillar now has a probabilistic meaning.
- **Flip alert** (1896-1897, 2086). Require the new `dirSide` to persist for 2 confirmed bars before `drawFlip`, because geometry moves continuously with price.
- **README.** "D is the calibrated probability that the best buy-side target is reached before the best sell-side target; structure, raids and candle context move it only by the weight they have earned on this chart."

**Expected value.**

- Higher DOL HIT % and fewer "draw points the wrong way" ghosts: +2 to +7 pp hit-within-H on the simulated proxies.
- Directly measurable: the existing ledger (DOL HIT %, EDGE) plus BIAS-1's side skill.
- An A/B is possible by toggling `drawSrc` on the same chart.

**Evidence:** moderate.

**Risk.**

- **Nearer targets.** The selected targets may be nearer on average, because the race favours the near side. The proximity taper below `minDistATR` and the minimum score limit trivially close picks.
- **Selection churn.** Mitigated by the 2-bar challenger rule, 2× side-flip hysteresis (2013-2016) and the persistence rule above.
- **Loss of the legacy look.** "Structure Vote" remains as an option.

**Effort:** S (after BIAS-1).

### BIAS-3 (P2) · Previous-candle module for the three mode timeframes ("daily bias" readout with honest odds)

**Why.** Traders ask "is today a PDH day or a PDL day?" Geometry answers it at 70-81% (2.4). The class labels (close-through, CRT, inside, outside) are what traders look for, and they should come with their measured lift, which is usually about 0. The engine already tracks PDH/PDL but not the class, the prior close, the 4H/1H prior candle, or any probability.

**Algorithm.**

1. **`f_candleTrack(bool isNew)`** (SERIES-STATE FUNCTIONS, after `f_rangeTrack` at 833). It keeps the running high/low of the current period (`h0`, `l0`, `o0`), the previous candle (`h1`, `l1`, `c1 = close[1]` at the period change) and the one before (`h2`, `l2`). It returns `[h1, l1, c1, o0, h0, l0, cls]` with cls coded as:
   - 1 = close-through up; 2 = sweep-reject up (bear CRT);
   - −1 = close-through down; −2 = sweep-reject down (bull CRT);
   - 0 = inside;
   - 3 / −3 / 4 = outside closing above H2 / below L2 / inside.
2. **Calls** at global scope, one per timeframe. Each call site keeps its own `var` state:
   - `[dH1, dL1, dC1, dO0, dH0, dL0, dCls] = f_candleTrack(timeframe.change(tfH))`, and likewise for `tfS` and `tfE`.
   - On a chart whose timeframe equals `tfE`, `timeframe.change(tfE)` is true on every bar, so the "previous candle" is the previous bar. That is correct.
3. **Probabilities.** Each confirmed bar, while both prior extremes are untaken this period (`h0 ≤ h1` and `l0 ≥ l1`):
   - `pU = f_raceH(h1 − close, close − l1, potSig, potMu, hRem)` and `pD = f_raceH(close − l1, h1 − close, potSig, −potMu, hRem)`;
   - `hRem = math.max(1, int((time_close(tf) − time) / (timeframe.in_seconds() * 1000)))`. `time_close(tf)` is known for the current higher-timeframe bar, so this does not repaint;
   - `pNone = 1 − pU − pD`.
   - **Calibration.** Per (timeframe, class): n, k and Σp of "high first | decided", booked at each period end from the first-touch flags tracked during the period, using the prediction made at the period's first bar. Shift with `δ = logit((k + 20·p̄)/(n + 20)) − logit(p̄)`, the same estimator as `f_raceAdj` (1367-1372). That is 3 × 7 × 3 floats.
4. **UX.**
   - Clean table: keep the two columns (reference look) and add a **tooltip** on each Bias cell, e.g. `Prev D: swept high, closed inside (CRT↓) · P(PDH first) 41% · P(PDL first) 47% · neither 12% · class lift +1% (n 212)`.
   - Terminal: a "PREV" row group.
   - Optional (default off): push the STF/EXE prior-candle extremes into `extReg` as new src codes (tier between session and STF), so a 4H CRT target can be a DOL candidate.

**Expected value.** The trader-facing daily-bias answer with real probabilities, and an honest display of the CRT/close-through labels people search for. It also feeds `x6` and `x8` to BIAS-1.

- **Evidence:** moderate (base rates and geometry); weak-to-none for class lift.
- **Risk:**
  - Session-boundary mismatch with the trader's convention: futures 18:00 vs RTH. Make the day source configurable via the existing `tz`/session inputs.
  - Small samples per class (n ≈ 1 per day on D). Shrinkage keeps the numbers at geometry until there is data.
- **Effort:** M.

### BIAS-4 (P2) · Raid outcome: stop treating "rejected" sweeps as reversals

**Why.** At 1581, a sweep that closes back inside (REJECT) adds −side·tier to `liqEvt`, i.e. it votes for reversal. The evidence contradicts this:

- the CRT target is first only 39-48% of the time, equal to the null;
- Turtle Soup is at or below geometry;
- daily equities retake the swept high more than the null (+5 to +9 pp);
- AMD direction follows the trend regime, not the sweep (X5);
- sweeps predict continuation in 65/66 fold selections (X12).

**Algorithm.**

- Split the accumulator into `var float liqHold` and `var float liqRej`, both decayed with `liqHL` at 1535.
- HOLD: `liqHold += side·tier`. REJECT: `liqRej += −side·tier` (same sign convention as now).
- Legacy D: `liqEvt = liqHold + rejW·liqRej`, with `float rejW = input.float(0.0, "D · Raid Rejection Weight", minval = -1.0, maxval = 1.0, step = 0.1, group = G_FLOW, tooltip = "0 = evidence default (rejections carry no direction). 1 = classic ICT reversal reading.")`.
- In the Calibrated draw (BIAS-1), `liqHold` and `liqRej` are separate features whose signs are learned.

**Expected value.** Removes a systematic wrong-way push of D after every rejected sweep. Measurable through BIAS-1's learned weight on `x5` (expected about 0) and through legacy-D skill.

- **Evidence:** moderate.
- **Risk:** on some markets REJECT may carry a reversal signal; the learned weight in BIAS-1 recovers it.
- **Effort:** S. This complements `ict_liq.md` ICT-2, the post-sweep outcome learner. Implement them together.

### BIAS-5 (P2) · Bias table with measured skill (keep the look, add honesty)

**Why.** The Clean table's BULLISH/BEARISH (2297-2305) mirrors the reference product, but the evidence says swing bias has about zero skill for the next draw (sibling D 0.49-0.54; pivot weight about 0). Traders read it as a forecast.

**Algorithm.**

- For each timeframe row, BIAS-3's per-period bookkeeping also records the row's bias at the period's first bar: n, k = "prior high first | decided" when BULLISH (mirror for BEARISH), and Σ pGeo.
- `lift = k/n − p̄_geo`, `se = √(Σp(1−p))/n`.
- Text stays "BULLISH"/"BEARISH" (reference look). The colour alpha follows evidence: full colour if lift > 1.5·se, dimmed (alpha 60) otherwise.
- Tooltip: `Swing bias BULLISH · when bullish, prior high taken first 61% (geometry 58%, n 140)`.
- Terminal: add a `SKILL` column with `+3% (n 140)`.

**Expected value.** The table no longer overstates. Traders see which timeframe's bias actually leads on their market. Measured by construction.

- **Evidence:** moderate (need); weak (UX benefit).
- **Risk:** dimming may look "broken" to users expecting the reference look. Add an input `Bias Skill Shading` (default on) to turn it off.
- **Effort:** S (after BIAS-3).

### BIAS-6 (P3) · Empirical PoT surface: pick the regime key by held-out score (pooled vs htfBias split)

**Why.** `f_bump` (1531-1532) and `f_empPoT` (1285-1301) split the reach surface into 3 rows by `htfBias`. If htfBias carries about zero information (2.4, sibling), the split mostly cuts the sample per row to about a third and makes the PoT noisier. Section 2.5 shows regime effects of ±2-4 pp whose sign is market-specific. They may matter on some charts (X5) and not others.

**Algorithm.** At step 0 (1526), before `f_bump` for the window that just completed:

- for d ∈ {0.5, 1.0, 2.0} ATR and each side, compute the predictions the surface would have given at bar−H:
  - pooled `Σ_r S_r(d)/Σ_r n_r`;
  - split `S_{r*}(d)/n_{r*}`, with r* the row of `htfBias[H]`;
- accumulate the Brier score of each against the realized reach `(fwdHi − close[H])/aH ≥ d`;
- in `f_empPoT`, use the split row only if `BrSplit < BrPool − 0.002` after ≥ 300 windows, otherwise the pooled row.
- Optional: the key may instead be BIAS-3's previous-HTF class (3 groups: up-close/bull-CRT, down-close/bear-CRT, other).

**Expected value.** A less noisy PoT on most charts, with the regime-specific surface kept where it earns its place. Measured by the PoT calibration that `ict_time.md` TIME-2 proposes.

- **Evidence:** weak-moderate.
- **Risk:** a small extra cost per bar (6 interpolations); state is 2 floats per (d, side).
- **Effort:** M.

### BIAS-7 (P3) · HTF candle-close event alerts with calibrated odds (CRT / close-through)

**Why.** CRT and close-through events are what many traders wait for. An honest alert, reporting the event together with the engine's calibrated probabilities, is more useful than a bare pattern alert and avoids the overconfidence that the evidence warns about.

**Algorithm.**

- On `timeframe.change(tfH or tfS)` with cls ∈ {±1, ±2} from BIAS-3, call:
  `alert("DOL Engine ▸ " + tfLabel + " " + clsText + " · P(prior high first) " + pctU + " · P(prior low first) " + pctD + " · class lift " + lift + " (n " + n + ")", alert.freq_once_per_bar_close)`.
- The default is off; enable it via the input `Alert · HTF candle events`.
- Also add an `alertcondition(htfCrtEvent, ...)` for users who build alerts on conditions.

**Expected value.** Workflow value and education. Probabilities are shown, not implied.

- **Evidence:** weak (UX).
- **Risk:** alert spam on 1H. Limit it to `tfH` and `tfS`.
- **Effort:** S.

### Explicitly not recommended (evidence says no)

- Adding the **ICT daily-bias rule**, **CRT**, **open-relative bias** or the **EMA trend regime** to D with **fixed** weights. All are ≤ geometry or vary in sign by market (2.2-2.6). Use them only as learned features (BIAS-1).
- **Crabel "contraction → expansion"** as a volatility prior. It is false in absolute terms (2.8).
- Raising `wDraw` or lowering `ctrMult`. That would amplify an input with no measured skill.

---

## 5. Sources

**This study** (reproducible; scripts and outputs in `study/bias_tools/`, data in `study/bias_data/`):

- `prevcandle.py` → `out_daily.txt`, `out_weekly.txt`, `out_intra.txt`: base rates, class stats, CRT, shuffle null.
- `race.py` → `out_race.txt`: OOS geometry vs features.
- `cells.py` → `out_cells.txt`: class × regime excess over geometry.
- `openrel.py` → `out_openrel.txt`: weekly and midnight open.
- `turtle.py` → `out_turtle.txt`: Turtle Soup and N-bar breakout.
- `nr.py` → `out_nr.txt`: Crabel NR4/NR7/inside; k-bar reach.
- `sidesel.py` → `out_sidesel.txt`: engine-like side selection.
- Data:
  - `arch` 9.0.0 package datasets (S&P 500 and NASDAQ daily OHLC, 1999-2018);
  - `backtesting` 0.6.6 package test data (GOOG daily 2004-13, EURUSD 1H 2017-18);
  - the sibling study's NQ/GC/EURUSD 1H files (`scratchpad/sim/data/`).

**Papers:**

- Taylor, V. (2026). *Evaluating the Predictive Validity of ICT's Accumulation-Manipulation-Distribution (AMD) Model on CME E-Mini NASDAQ-100 Futures*. arXiv:2610.35887. Code: https://github.com/veertaylor19/amd-backtest
- Portnaya, V. (2026). *The Bounce Has No Direction: Sign, Magnitude, and the Microstructure of Equity Return Predictability*. arXiv:2606.29591.
- Safari, S. A., & Schmidhuber, C. (2025). *Trends and Reversion in Financial Markets on Time Scales from Minutes to Decades*. arXiv:2501.16772.
- Schmidhuber, C. (2020). *Trends, Reversion, and Critical Phenomena in Financial Markets*. arXiv:2006.07847.
- Mesfin, M. (2026). *Structural Limits of OHLCV-Based Intraday Momentum Signals in MNQ Futures*. arXiv:2605.04004.
- Upadhyay, R. (2026). *Do Time-Series Foundation Models Forecast Index-Futures Returns?* arXiv:2611.12141.
- Moskowitz, T., Ooi, Y. H., & Pedersen, L. H. (2012). Time series momentum. *Journal of Financial Economics* 104(2), 228-250.
- Chung, K., & Bellotti, A. (2021). *Evidence and Behaviour of Support and Resistance Levels in Financial Time Series*. arXiv:2101.07410 (sibling E5).
- Mahadzva (2026), SSRN 7430998; Tangirala (2026), SSRN 7483658; Barot (2026), SSRN 7359378. All via `ict_liq.md` E7, E8 and E10.

**Practitioner sources:**

- edgeful blog:
  - previous day's range: https://www.edgeful.com/blog/posts/previous-days-range-trading-mistake
  - inside bars: https://www.edgeful.com/blog/posts/inside-bar-pattern-day-trading-strategy
  - outside days: https://www.edgeful.com/blog/posts/trading-bullish-bearish-outside-days
  - NQ setup: https://www.edgeful.com/blog/posts/ultimate-bullish-setup-trading-NQ
- CRT definitions:
  - https://www.luxalgo.com/library/concept/candle-range-theory/
  - https://tradingwyckoff.com/en/crt/
- CRT placebo backtest: https://www.youtube.com/watch?v=HEJV0lnNLJI (Strange Labs, 2026).
- TTrades daily bias: https://ttrades.com/easy-daily-bias-a-mechanical-trading-framework/
- Smash day backtest: https://roguequant.substack.com/p/i-backtested-larry-williams-trading
- Oops pattern: https://ungeracademy.com/blog/we-tested-larry-williams-oops-pattern-the-results-might-surprise-you
- ES PDH/PDL count: https://www.elitetrader.com/et/threads/trading-yesterdays-high-or-low-only.294381/
- Crabel NR7: https://chartschool.stockcharts.com/table-of-contents/trading-strategies-and-models/trading-strategies/narrow-range-day-nr7

**Pine docs** (local mirror):

- `docsrc/jabez4jc_pinescriptv6/language/type_system.md` (collection-type fields);
- `reference/timeframe.md` (`timeframe.change`).
