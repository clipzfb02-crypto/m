# ICT Market Structure and Models: study for the DOL Engine v2

Domain: swing points (3-candle vs N-candle fractals), the STH/ITH/LTH hierarchy, BOS vs CHoCH vs MSS, displacement, CISD, protected (strong) and weak extremes, the dealing range and its premium/discount, the market maker buy/sell models (MMXM), turtle soup, OTE (62-79%), the "2022 mentorship model" (sweep → displacement/MSS → FVG → opposing liquidity), and intermediate-term highs/lows as targets. For each: how it implies the next draw on liquidity, how the engine's bias and draw vector should reflect it, and what the evidence says.

Engine studied: `brief/baseline_v2.pine` (line numbers below; identical to `/home/user/m/indicators/dol_engine.pine`).

Companion studies (read them, this report does not repeat them): `study/ict_liq.md` (liquidity theory: sweep vs run, turtle soup, IRL/ERL, STH/ITH/LTH as ICT-8, sweep learner ICT-2, candidate ledger ICT-1) and `study/ict_pd.md` (PD arrays, dealing range P/D, breakers). This report focuses on **structure and the named models**, and adds **an original empirical test on three markets** (section 2.2) because the published evidence on structure is thin.

Evidence grades: **strong** (peer-reviewed or large replicated quantitative study), **moderate** (published statistics/backtests with numbers, reproducible), **weak** (practitioner consensus, small or vendor samples), **none** (folklore, definitions only).

Reproducible tooling and the full numeric log of the original test: `study/ict_struct_tools/` (`structtest.py`, `skilltest.py`, `dcleg.py`, `agree.py`, `sweephtf.py`, `st.awk`, `mtf.awk`, `results.txt`). Data: Yahoo Finance 60-minute bars, about Nov 2024 to Nov 2026, NQ=F (11,400 bars), GC=F (11,429), EURUSD=X (12,285). The data files are not stored (third-party); re-download 60m/2y bars and save as `data/{nq,gc,eu}.csv` with columns `idx,open,high,low,close`.

---

## 0. Executive summary

1. **Market structure carries almost no directional information about which side's liquidity is taken first.** Across every independent test found, and an original test on three markets:
   - 44 formalised SMC/ICT detectors (from two popular open-source Pine scripts, BOS/CHoCH included) on 496 S&P 500 stocks, 2.2 million events: **none beats random entry at any horizon** (Tangirala 2026, SSRN 7483658).
   - 15,817 ICT market structure shifts on ES/NQ/6E/6A 5-minute charts: edge ratio (MFE/MAE) **0.97-1.13 at every checkpoint; displacement does not improve it** (Nordman Algorithms 2026).
   - The fully mechanised 2022 model (sweep → MSS → FVG entry) on 12 markets, Feb 2021-Aug 2025: **within ±0.05R of zero before costs on every timeframe**, negative after costs (1m: −0.25R over 41,541 trades) (open-source TradingView script by IvanSetuper, 2026).
   - CHoCH confirmed by an FVG retracement on G10 FX: the textbook reversal read **should be faded**; swept levels predict **continuation** in 65 of 66 fold-selections (Mahadzva 2026, SSRN 7430998).
   - ICT's AMD/Power of 3 on NQ: **no directional information beyond the daily trend regime**; aligned with trend 62-71% correct, against trend 25-30% (Taylor 2026, arXiv 2610.35887).
   - **Original test (section 2.2)**: an engine-faithful replica of `f_structure` on 1H, 4H-like and D-like bars, and the engine's draw vector `D`, predict which side (±1.5 ATR) is touched first within 30 bars **49.9% / 51.6% / 50.4%** of the time on NQ / gold / EURUSD. Random-walk controls scatter 47-53%. An 11-feature logistic learner of the side **does worse than a coin out of sample** (48.0% / 47.8% / 49.6%).
2. **The engine's draw pillar is its largest weight (30, line 145), and the counter-draw multiplier halves a target (×0.50, line 162).** Both encode a directional skill that the evidence says is about 50-52%. On charts where `D` has no skill, the engine prefers farther draw-side targets over likelier counter-side ones, and side flips of `D` move the target for no forecasting reason (a plausible cause of "targets jump around"). Best fix: **measure `D`'s skill online and scale its influence by it** (proposal ICTS-1).
3. **The engine's liquidity-event read is mis-signed.** Line 1581 maps "raid closes back inside" (REJECT) to reversal and "closes beyond" (HOLD) to continuation. Pooled over the three markets, REJECT sweeps were followed by **continuation 52.6%** (n = 1,402), never reversal. HOLD sweeps **against the HTF swing bias reversed 56%** (continuation 43.8%, n = 381), while HOLD sweeps with the HTF bias continued 53.2% (n = 423). This matches Mahadzva, Taylor and the liquidity study's E6. Fix the static mapping now (ICTS-2) and let the sweep learner (ICT-2 in `ict_liq.md`) refine it.
4. **ICT's MSS is a with-HTF-trend signal, not a reversal signal.** ICT's own definition starts "if you're bearish and you see price run above an old high, then it breaks below …" (2022 Mentorship Ep. 6, 20:52). The MSS ends a counter-trend retracement. The engine's internal bias flips on any close through the last pivot regardless of HTF (that is a CHoCH, not an MSS). Measured: MSS reversal reads were right 45.6% (n = 171) without displacement and 50.5% (n = 97) with it. No scoring change is justified; an alert with a measured follow-through rate is (ICTS-6).
5. **"Which liquidity is taken first" is answered by geometry, and the engine already has the right math.** The first-passage race between the weak extreme (the target) and the protected extreme (the invalidation) matched the gambler's-ruin prediction to within 2 percentage points on NQ and gold (observed 62.8% vs predicted 64.8%; 62.4% vs 64.6%; random-walk null −0.2 ± 2.5 pp). The engine's `f_race`/`f_raceH` (lines 447-482) are exactly this model. Show the race odds against the opposing pool in the Clean label, because that is the honest answer to the user's core question (ICTS-3).
6. **The dealing range in `f_structure` is the last pivot high and low, not ICT's range.** ICT's range runs from the protected extreme to the weak extreme of the current swing leg. The engine already computes both (`protH/protL`, `legH/legL`) but returns `protH/protL` unused (lines 923-925) and never returns `legH/legL`. A two-line change fixes premium/discount, `htfEQ` and the structural invalidation (ICTS-4, ICTS-5), and the P/D and IRL/ERL proposals in the companion studies depend on it.
7. **Directional-change scaling law.** After a structural turn of size δ, price extends on average about δ beyond the confirmation point before the next turn. This holds for FX across three orders of magnitude (Glattfelder, Dupuis & Olsen 2011). It is also exactly what a driftless random walk produces (the overshoot is exponential with mean δ; simulated P(overshoot ≥ δ) = 0.37, median 0.70δ). Gold (1.39 vs 1.19 ± 0.04 for a matched random walk) and NQ (1.29 vs 1.17 ± 0.06) showed mild trend persistence over this window; EURUSD matched the random walk (1.14 vs 1.11 ± 0.07). The leg direction still predicted the first-touch side only 47-56%. Use the law as a sanity prior, not a signal.
8. **OTE (62-79%), MMXM ladders and the 2022 model add no forecastable edge** (sections 1.10-1.12, 2.1). They should stay out of the score. At most they belong in a display-only narrative.

Seven proposals follow (section 4), best first.

---

## 1. Concepts: definitions, parameters, edge cases

Notation: bar t is the current confirmed bar, `[k]` is k bars back, ATR is ATR(14), "pool" is a liquidity level in the engine's `pool`.

### 1.1 Swing points: 3-candle vs N-candle fractals
- **ICT.** A swing high is three candles whose middle candle has the highest high: a lower high on each side. It is confirmed only when the third candle closes ("forms once this candle closes", 2022 Mentorship Ep. 3, 17:53). Swing low is the mirror. ICT takes these from Larry Williams (Ep. 12, 17:39).
- **N-candle fractal.** A pivot of strength p needs p lower highs on each side and is known p bars late. Williams' fractal is p = 2 (5 candles). Common scripts: LuxAlgo SMC uses 50 (swing) and 5 (internal); LuxAlgo Fractal uses 2; Leviathan 20; TradingFinder 15 left / 30 right for CHoCH and 1 for BOS (ProEA's survey of the 15 most-boosted open-source structure scripts, 2026).
- **Algorithm.** `ph = ta.pivothigh(high, p, p)`; the value refers to bar `t - p`. **Ties:** the Pine reference does not document how equal highs are treated (`reference/ta.md`, `ta.pivothigh`: "returns price of the pivot high point. It returns 'NaN', if there was no pivot high point"). A double top with two identical highs may produce zero, one or two pivots depending on implementation. If exact tie behaviour matters, compute the fractal by hand (`high[p] > high[p-k]` and `high[p] >= high[p+k]`, i.e. strict on one side) so the leftmost of an equal pair wins.
- **Trade-off.** A larger p gives fewer, more significant swings with p bars of lag. On a 1H chart the engine's chart pivots (`pivLen` = 5, line 90) are 5 hours late. A high that is taken within 5 bars of being printed is never a pool, so its sweep never reaches `liqEvt`.
- **DOL role.** Swings are where stops rest (liquidity study, E1-E3). The next unswept swing on each side is the nearest candidate draw.

### 1.2 Short-, intermediate- and long-term highs/lows (STH / ITH / LTH)
- **ICT (Ep. 12).** STH = the 3-candle swing. ITH = an STH with a lower STH on each side, *or* "the high made when price trades back up to rebalance an imbalance" ("the main one"). LTH = an ITH with lower ITHs on each side, "generally linked to a higher time frame, daily chart" (29:39).
- **Use.** Breaking an ITL is "a significant break in market structure" (Ep. 12, 31:15), while breaking an STL is only a "shift". In a bullish leg the ITL formed after the first raid of a short-term low is the **protected low** that price "should not exceed" (MMXM notes); the ITH/LTH above is the objective.
- **Algorithm.** See `ict_liq.md` ICT-8: rolling three-element rings of STH prices; promote the middle one when both neighbours are lower.
- **DOL role.** The order of the swing approximates the size of the pool. The engine proxies order by timeframe (`f_tierW`, lines 506-516: chart 0.25, STF 0.45, HTF 0.65).

### 1.3 Break of structure (BOS)
- **SMC definition.** A candle **close** beyond the last swing in the trend direction (continuation). ICT has no separate term for it (Quarter Sequence study page on ICT market structure).
- **Parameters that change the label:** swing strength, wick vs close confirmation, minimum break distance (ticks, points, % or ATR) (Nordman, "BOS vs CHoCH", 2026). Wick confirmation fires earlier and is fooled more often; close confirmation can come several bars later.
- **Engine.** `f_structure` (lines 708-782) on each MTF timeframe: `upBrk = close > swH`, where swH is the last unbroken pivot high of strength `biasLen` (3). On a BOS the leg is re-armed and the protected low becomes the leg's low (lines 755-759). The chart-level BOS for order blocks is `bosUp = close > obSwingH` (lines 1542-1543), with `pivLen` = 5 pivots.

### 1.4 Change of character (CHoCH)
- **SMC definition.** The first close through a swing against the prevailing structure. LuxAlgo-style "swing" CHoCH requires the close to pass the **protected** extreme of the last leg (the strong low in an uptrend); an "internal" CHoCH uses the last minor swing.
- **Engine.** Swing CHoCH = close through `protH`/`protL` (lines 760-773). Internal bias `ibias` flips on any close through the last pivot (lines 750-753). The Clean bias table shows the swing bias and falls back to the internal bias while the swing bias is 0 (lines 2299-2305).
- **Failure modes.** In ranges, small swings flip on every pullback ("reversal trades can become extremely expensive during consolidations", quoted by Nordman). One move can be both a CHoCH on small swings and a BOS on large swings.

### 1.5 Market structure shift (MSS, ICT)
- **ICT definition.** "If you're bearish and you see price run above an old high, then it breaks below the old high and takes out a short-term low prior to that run above" (Ep. 6, 20:52). Three parts:
  1. **The run.** Price trades through an old high (a wick suffices: "it does not need to close above that", Ep. 3, 13:47).
  2. **The break.** It closes below the short-term low that formed **before** the run ("preferably close below"; a wick through is "not all that convincing", Ep. 6, 19:39).
  3. **The force.** The break comes with displacement, usually leaving an FVG.
- **Precondition.** The break is "significant only if this run … has traded into sell stops below an old low" (Ep. 3, 6:56). MSS is "a bias for the day … that's why I'm using the term market structure shift, not market structure break" (Ep. 3, 2:49).
- **Key reading for the engine.** The MSS is defined *inside* an HTF bias ("if you're bearish"). It marks the end of a counter-trend retracement, i.e. a with-trend resumption signal. That matches the evidence: Taylor's AMD trend-aligned cells were 62-71% correct and the counter-trend cells 25-30%.
- **Algorithm (bearish; mirror for bullish).**
  1. Keep `sthLow = ta.pivotlow(low, 1, 1)`, the last 3-candle swing low, updated as they print.
  2. At bar s a BSL pool is swept (`high > level`). Capture `mssLvl` = the last `sthLow` confirmed before s.
  3. Within `mssWin` (8) bars, the first bar with `close < mssLvl` is the MSS. Optional displacement gate: body ≥ 1.2 ATR and body/range ≥ 0.6 on that bar or the one before.
  4. Valid only once. Void if price trades above the sweep extreme first.
- **CHoCH vs MSS in practice.** Many scripts use the words interchangeably. Nordman's MSS indicator labels "a recent swing against the local move" and filters by the number of prior lower highs, without checking a sweep or displacement.

### 1.6 Displacement
- **ICT.** "You want to see an obvious displacement" (Ep. 5, 18:49); "it's got to be energetic, it can't be a little lethargic little move" (Ep. 6, 19:12). ICT gives no size rule.
- **Operational versions:**
  - one candle: body ≥ k·ATR (k 1.0-2.0) and body/range ≥ 0.6-0.7;
  - Nordman's "big candle": body far above the average of the last 20 bodies (their example was 4.5×);
  - "FVG left by the move";
  - LuxAlgo's MSB filter: the close-to-close move > 0.5 standard deviations above its 50-bar average.
- **Engine.** `dispUp/dispDn` (lines 897-904): body ≥ `dispMult` (1.2) × ATR[1] and body ratio ≥ 0.6, or a two-candle leg with both body ratios ≥ 0.5 and combined body ≥ 1.8 ATR. Uses:
  - FVG/OB quality gates (lines 1867-1889, 1666-1681);
  - a 20% weight in `D` with a 12-bar half-life (lines 1892-1894).

### 1.7 Change in state of delivery (CISD)
- **Definition (later ICT lexicon).** Find the last unbroken series of down-close candles into a swept low. The CISD level is the **open of the first candle** of that series. A **body close** above it is the bullish CISD (mirror at highs). It fires earlier than an MSS because it does not need a swing break.
- **DOL role.** None beyond MSS; it is an entry trigger. No statistics exist (grade none). Not recommended for the engine.

### 1.8 Protected (strong) vs weak extremes
- **SMC.** In a bullish swing, "the low that initiated the trend is the Strong Low (protected) and the high is the Weak High (target)" (TradingView script descriptions; LuxAlgo SMC "trailing extremes").
  - A weak extreme is liquidity until taken.
  - A strong extreme stays valid until broken by a structure shift.
  - The draw is toward the weak extreme; invalidation sits beyond the strong one.
- **Engine.** `f_structure` keeps exactly these:
  - `protL`/`protH` are set at each BOS/CHoCH (lines 755-773);
  - `legH`/`legL` are the running extremes of the current leg (lines 729-730, re-armed at each break).

  `protH/protL` are returned (line 782) but **never used** (grep finds them only at lines 923-925). `legH/legL` are not returned.
- **DOL role.** The weak extreme of the HTF leg is the textbook HTF objective. The protected extreme is the structural invalidation.

### 1.9 Dealing range, premium and discount
- **ICT.** The dealing range runs from the swing low to the swing high of the most recent leg that "did something meaningful" (broke structure or swept). Premium is above 50%, discount below. Buy in discount toward premium liquidity. A close beyond either extreme retires the range (see `ict_pd.md` 1.1 for sub-levels).
- **Structure-consistent definition:**
  - bullish swing bias: `[protL, legH]`;
  - bearish swing bias: `[legL, protH]`.
- **Engine.** `rngH`/`rngL` (lines 727-779) = the **last pivot high** and the **last pivot low**, each extended by the running extreme while its swing is broken. After a lower high forms inside an up-leg, `rngH` drops to that lower high, so the "dealing range" becomes the latest internal swing.
  - Used by `htfEQ` (confluence anchor, line 968);
  - the Terminal "PREM/DISC %" (lines 2323-2333);
  - the `f_invalidation` fallback (`exeRL/exeRH`, line 1354);
  - registry prominence (lines 1783-1789).

### 1.10 Optimal trade entry (OTE, 62-79%)
- **Definition.** After a displacement leg (A → B), the entry band is the 62%-79% retracement of the leg (the 70.5% midpoint is ICT's "sweet spot"). Usually it is required to sit in discount (longs) and to overlap an FVG/OB.
- **DOL role.** An entry location, not a target. A pullback into OTE says nothing about which liquidity is taken next, except through geometry. The deeper the retracement, the farther the old high and the nearer the protected low.
- **Evidence.**
  - No academic test of OTE exists.
  - Tradeify's ES/NQ daily swing study (Oct 2024-Nov 2026, 100 legs; 163 legs on AAPL/MSFT/NVDA) found continuation odds fall **monotonically with retracement depth**: 33.3% after a 23.6% pullback, about 1 in 5 after 61.8%, 13.5% after 78.6%. There was "no bump at 61.8% or anywhere else", and the median depth of continuing legs was 60.4% (middle half 49.7-81.0%). That is the gambler's-ruin geometry of a random walk.
  - Grade: weak (small sample), and it argues against a special OTE level.

### 1.11 Market maker buy/sell models (MMXM)
- **Definition (ICT; LuxAlgo summary).** In an MMBM:
  1. price leaves an **original consolidation**;
  2. it steps down through smaller consolidations ("engineering liquidity", each leg taking SSL under prior lows) to a sell-side objective, often an HTF PD array;
  3. the **smart money reversal** (SMR) is a final sweep plus an MSS/CISD;
  4. the buy side of the curve **retraces the whole path**: the interior consolidations and short-term highs left on the way down become **targets in order, nearest first**, ending at the original consolidation;
  5. targets beyond it come from standard-deviation projections of the manipulation leg (−2 to −2.5, −4).

  Invalidation: a close back through the swept extreme, or failure to displace through the first interior consolidation. MMSM is the mirror.
- **Algorithm sketch.** After an SMR (sweep + MSS) at extreme X, the ladder = the unswept STHs/consolidation highs between X and the leg origin O, sorted by distance. O's range is the final objective.
- **Engine.** Implicitly present: those lower highs are already BSL pools, and the nearest draw-side pool is what proximity picks after `D` flips. The SMR detector (sweep + MSS) is missing.
- **Evidence.** None. No published test; LuxAlgo notes "real charts rarely deliver the textbook symmetry". Its core (sweep → MSS reversal) tested at about coin-flip (2.1).

### 1.12 The "2022 mentorship model"
- **Sequence.**
  1. Bias and the draw from HTF (D/4H/1H).
  2. Wait for a raid of an obvious pool (Asia/London/PDH-PDL, equal highs/lows), ideally in a killzone.
  3. Displacement closes through the STH/STL that led into the raid (the MSS).
  4. Enter on the retrace into the FVG of the displacement leg.
  5. Stop beyond the raid extreme.
  6. Target the **opposite liquidity pool**, with partials at the nearest swing ("low-hanging fruit").
- **Mechanised test (IvanSetuper, open-source script, 2026).** Swings = 3-bar fractals on the chart and two HTFs plus session/PD levels. A sweep must happen inside an HTF FVG. The MSS is the first close through the latest swing. The FVG must form within 5 bars. Targets 1R/2R (3R on range-expansion days). Window 09:30-14:00 NY. Twelve markets, Feb 2021-Aug 2025, retail costs:
  - 1m: −0.25R (41,541 trades, 28% winners; costs 0.21R);
  - 5m: −0.08R (14,009, 37%);
  - 15m: −0.04R (7,069, 44%);
  - 30m/1h: −0.02R / −0.05R.
  - "Before costs every timeframe came out within 0.05R of zero… the setup did not predict direction." NQ/ES May-Nov 2026: −0.06R (1m), 0.00R (5m). Time windows, a filter by the direction of the day, HTF-gap entries and "every condition of the lectures" did not show a profit distinguishable from chance.
- **DOL role.** The target rule ("opposite pool") is the engine's selection with `D` flipped by the raid. Its value is in structuring a trade (defined stop/target), not in forecasting.

### 1.13 Turtle soup
Covered in `ict_liq.md` 1.9 (Connors-Raschke rules: new 20-day low, prior low ≥ 4 sessions old, buy stop above the old low). In ICT's version context comes from premium/discount. Original data here: REJECT sweeps of 5-bar-pivot pools were followed by **continuation**, not reversal (2.2). The age filter was not tested.

### 1.14 Intermediate-term highs/lows as targets
- **ICT.** Once an ITL forms after the first raid of an STL in a bullish leg, the ITH/LTH above is the target and the ITL is protected. In practice: weak extreme = target, protected extreme = invalidation (1.8).
- **Engine.** STF/HTF pivots enter the external registry only when confirmed and unswept (lines 1779-1789; `hValid/lValid`, lines 780-781). The trailing HTF extreme of the current leg is not a level until it becomes an HTF pivot, which takes `biasLen` (3) HTF bars plus the `[1]` shift (4 days on D).

### 1.15 How the models imply the next draw (summary)
| Model | Next draw it implies | Engine equivalent | Evidence for the implied draw |
|---|---|---|---|
| HTF trend / swing bias | weak extreme / next old high in trend direction | `htfBias` in `sV` (line 1892), PoT regime split (line 1531) | weak-moderate: trend regime 52-56% on our data; Taylor 62-71% at day scale; time-series momentum strong at 1-12 months |
| BOS | continuation to the next swing pool | same as above | none: BOS detectors ≈ random (Tangirala) |
| CHoCH / MSS | reversal to opposing liquidity (ICT: with-HTF resumption) | `ibias`, `liqEvt` reject = reversal | none / negative: 45.6-50.5% (ours), Nordman ≈1.0, Mahadzva "fade" |
| Sweep that holds | continuation | `liqEvt` +1 | mixed: 53% with HTF, **44% (reverses) against HTF** (ours) |
| Sweep that rejects | reversal | `liqEvt` −1 | negative: continuation 52.6% (ours); 65/66 folds continuation (Mahadzva) |
| Displacement | continuation | `mV` (20% of D) | none: 48.3-50.8% (ours), Nordman |
| MMXM | interior consolidations nearest first, then original consolidation | nearest draw-side pool | none |
| 2022 model | opposite pool after sweep + MSS | selection after `D` flips | none (≈0R before costs, 12 markets) |
| OTE / P-D | from discount, the premium old high | not used | weak, geometry only |
| DC overshoot | about δ beyond the confirmation, exponential tail | not used | strong as a law, and identical to a random walk |

---

## 2. Evidence (numbers and sources)

### 2.1 Published evidence

| # | Claim tested | Data | Result | Grade |
|---|---|---|---|---|
| S1 | SMC/ICT event detectors predict returns | Tangirala, SSRN 7483658 (2026). 44 detectors translated from two popular open-source Pine scripts; 496 S&P 500 stocks, daily, Jan 2010-Jun 2026; 2.20 m events, 17.6 m simulated trades, 8 horizons; ticker-matched null, Newey-West, Benjamini-Hochberg over 352 tests | Against a zero-return null 38/44 look significant; against the matched null **none beats random entry at any horizon** and none is significantly worse. Largest estimates 11-12 bp over 10 days (both liquidity-sweep detectors), p ≥ 0.23. Concepts selected in-sample earn −31 bp out of sample. The median concept's minimum detectable edge is 47 bp | moderate (preprint, rigorous method) |
| S2 | ICT/SMC rules on G10 FX | Mahadzva, SSRN 7430998 (2026). EURUSD/GBPUSD/AUDUSD/USDJPY intraday; walk-forward, bootstrap, permutation, holdout | "No evidence ICT/SMC concepts work as literally taught." Three independent sweep mechanisms agree in **65/66** fold-selections that a swept level predicts **continuation**. CHoCH + FVG retracement: the reversal read **should be faded**. EURUSD H1 faded: p = 0.0192, holdout +19.3%, 60 trades, PF 1.50. AUDUSD H1: p = 0.0074 but fragile (WFE 2.08). Both fail the Deflated Sharpe gate | moderate (single preprint) |
| S3 | Displacement improves the MSS | Nordman Algorithms (Nov 2026). 15,817 MSS signals (swing strength 5, close beyond the last swing, ≥ 1 lower high before), ES/NQ/6E/6A 5m, Oct 2023-Sep 2026; edge ratio = mean MFE / mean MAE | Edge ratio with/without displacement at 5m/15m/1h/1d: big candle 1.08/1.03, 1.04/1.04, 1.00/1.00, 0.99/1.00; FVG 1.05/1.04, 1.06/1.00, 1.02/0.97, 1.00/1.01; both 1.13/1.03, 1.08/1.03, 1.02/1.00, 0.99/1.00. "Price went about as far against the trade as in its favour." Repeated on 15m and strength 3: every version failed | moderate (vendor, large sample, pre-declared rule) |
| S4 | Mechanised 2022 model | IvanSetuper, open-source TradingView script "ICT 2022 Model - Liquidity Sweep, MSS & FVG Entry" (2026). 12 markets (NQ, ES, DAX, ESTX50, EURUSD, GBPUSD, USDJPY, gold, oil, BTC, ETH, SOL), Feb 2021-Aug 2025, retail costs | Per trade after costs: 1m −0.25R (41,541, 28% winners), 5m −0.08R (14,009, 37%), 15m −0.04R (7,069, 44%), 30m −0.02R, 1h −0.05R. Before costs all within ±0.05R. NQ/ES May-Nov 2026: −0.06R (1m), 0.00R (5m). Time windows, day-direction filter, HTF-gap entries and the full lecture checklist: no profit distinguishable from chance | moderate (individual, open code, large sample) |
| S5 | AMD / Power of 3 (Asia accumulation, London false break, NY delivery to the opposite Asia extreme) | Taylor, arXiv 2610.35887 (2026). NQ 15m, Jan 2022-Jul 2026, N = 484 signal days; regime = daily EMA20 ±0.5% | Signal fires on 44% of days. 57% of valid signals reach the target **before** the 9:40 NY entry. Bullish (low swept) 46.9% correct, bearish 39.9% (inverted). By regime: aligned 61.6% / 70.8%, against 29.6% / 24.8%, ranging n.s. "No directional information beyond the daily trend regime." After a London sweep of the Asia high in an uptrend, the close is above the Asia midpoint 75.2% of the time | moderate (preprint, BH-corrected) |
| S6 | Trend persistence across scales | Schmidhuber (2021, *Physica A*; arXiv 2006.07847) and Safari & Schmidhuber, arXiv 2501.16772 (2025). Futures tick data 14 y, daily 30 y, monthly since 1692 | Weak trends persist and strong trends revert for horizons from about 30 min to about 1-2 years. Below about 15-30 min weak trends revert, beyond tick-size reversion. Coefficients are small but universal across asset classes | strong |
| S7 | Time-series momentum | Moskowitz, Ooi & Pedersen, *J. Financial Economics* 104 (2012). 58 futures/forwards, 25+ years | The past 12-month excess return predicts the next month for **every** contract (52 of 58 significant). The effect persists about a year and partially reverses after. HTF trend is informative at monthly horizons | strong |
| S8 | Directional-change scaling laws | Glattfelder, Dupuis & Olsen, *Quantitative Finance* 11(4) (2011); Glattfelder, "The Theory of Intrinsic Time", arXiv 2406.07354 | 12 scaling laws over about three orders of magnitude, 13 FX pairs. The average overshoot after a directional change of threshold δ is about δ. "Most occurring overshoots are small, with some disproportionately large ones." Own simulation: a driftless random walk gives the same law (overshoot ≈ Exp(mean δ): mean 1.01-1.12δ, median 0.70δ, P(≥ δ) = 0.37-0.40, P(≥ 3δ) = 0.06-0.08) | strong (law), none (as an edge) |
| S9 | Head-and-shoulders (a CHoCH-type pattern) | Chang & Osler, *Economic Journal* 109 (1999) / FRBNY SR4 (1995): daily FX 1973-1994, bootstrap vs random walk. Savin, Weller & Zvingelis, *J. Financial Econometrics* (2007): Lo-Mamaysky-Wang kernel detection, S&P 500 and Russell 2000, 1990-1999 | FX: profitable for 2 of 6 currencies (DM, JPY) and dominated by simple filter rules. US stocks: risk-adjusted excess return 5-7% per year, "in part on its identification of negative momentum stocks" | strong (peer-reviewed; old samples) |
| S10 | Fibonacci / OTE retracement levels | Tradeify (2026), ES/NQ daily Oct 2024-Nov 2026 (100 legs) and AAPL/MSFT/NVDA (163 legs) | 64% of legs fully retraced first. Median depth of continuing legs 60.4%. Continuation odds fall monotonically: 33.3% after 23.6%, about 20% after 61.8%, 13.5% after 78.6%. No bump at any Fibonacci level | weak (small sample) |
| S11 | ICT definitions | Quarter Sequence study page (ICT quotes with lecture timestamps); LuxAlgo concept library (MMXM, Model 2022, CISD, displacement); ProEA survey of 15 open-source structure scripts | Definitions and parameter conventions only | none (as evidence) |

### 2.2 Original test: does structure predict which side is taken first? (NQ, gold, EURUSD hourly)

**Design** (code in `study/ict_struct_tools/`):
- **Label.** At bar i, which of `close ± K·ATR14` is touched first within `HZ` bars. Rows touched on both sides in one bar, or untouched, are dropped. Defaults K = 1.5, HZ = 30 (the engine's default PoT horizon). Robustness: K = 3/HZ = 120 and K = 1/HZ = 12. The label is symmetric, so a coin scores 50% and distance plays no part: it measures direction only, which is exactly what `D` claims to know.
- **Sampling.** Every 6th bar from bar 600 (about 1,770 per market). Labels overlap, so the effective n is about n/5 and the standard error about ±2.7 pp per market.
- **Null.** The same code on 8 random walks with matched bar volatility: per-feature means 0.49-0.52, sd 1.2-5.7 pp.
- **Features.** All are engine replicas, computed with no look-ahead:
  - `f_structure` (len 3) on 1H, on 4-bar aggregates (≈4H, used one aggregate late) and on 24-bar aggregates (≈D, one late);
  - `sV = 0.5·htfBias + 0.3·stfBias + 0.2·exeIB`;
  - displacement momentum `mV` (body ≥ 1.2 ATR, ratio ≥ 0.6, half-life 12);
  - `liqEvt` with the engine's sign convention over 5-bar-pivot pools (tier 0.25, half-life 24);
  - `D` = the engine blend (`wS` 0.5 / `wM` 0.2 / `wL` 0.3);
  - EMA(460 h) ±0.5% regime (≈ daily EMA20, Taylor's rule);
  - 24 h / 120 h normalised returns and a cubic term (Schmidhuber).

**Directional accuracy (K = 1.5, HZ = 30):**

| Feature | NQ | Gold | EURUSD | Random walks |
|---|---|---|---|---|
| Engine `sV` (structure) | 0.505 | 0.519 | 0.506 | 0.489-0.516 |
| HTF swing bias (≈D) | 0.508 | 0.524 | 0.515 | 0.49-0.52 |
| STF swing bias (≈4H) | 0.501 | 0.505 | 0.510 | 0.50 |
| Exec internal bias (1H) | 0.502 | 0.499 | **0.462** | 0.49-0.51 |
| EMA regime | 0.521 | 0.516 | 0.474 | 0.47-0.48 |
| Displacement momentum | 0.508 | 0.495 | 0.483 | 0.50 |
| `liqEvt` (engine signs) | 0.501 | 0.485 | 0.504 | 0.47-0.48 |
| Engine `D` | 0.499 | 0.516 | 0.504 | 0.497-0.506 |
| Engine `D`, only when \|D\| ≥ `dGate` (`dirSide` ≠ 0) | 0.520 (n 740) | 0.504 (n 809) | 0.502 (n 779) | 0.48-0.52 |
| Logistic learner, 11 features, train first half / test second half | **0.480** | **0.478** | **0.496** | 0.526-0.537 |
| Skill-weighted D (weights from train-half accuracy), OOS | 0.499 | 0.516 | 0.502 | |
| HTF bias alone, OOS second half | 0.512 | 0.522 | 0.502 | |

- **Longer horizon (K = 3, HZ = 120).** Gold shows the only consistent signal: regime 0.553, `sV` 0.544, HTF bias 0.537, z120 0.555 (gold rose about 40% over the window). NQ 0.50-0.52; EURUSD 0.46-0.51.
- **Shorter horizon (K = 1, HZ = 12).** All 0.49-0.52.
- **HTF bias with or without the EMA regime agreeing.** Pooled 0.517 vs 0.521 (30 bars); 0.533 vs 0.483 (120 bars). Random walks swing ±6 pp, so this is indistinguishable from noise.

**Event outcomes** (pooled over the three markets; label from the event bar's close; SE ≈ 0.5/√n):

| Event | Outcome measured | n | Result |
|---|---|---|---|
| Sweep of a 5-bar pivot pool, close back inside (REJECT) | continuation | 1,402 | **0.526** (NQ 0.533, gold 0.557, EU 0.473) |
| Sweep, close ≥ 0.25 ATR beyond (HOLD) | continuation | 805 | 0.487 |
| HOLD **with** HTF swing bias | continuation | 423 | 0.532 |
| HOLD **against** HTF swing bias | continuation | 381 | **0.438**, i.e. 56% reversal (120 bars: 0.504) |
| HOLD with / against the EMA regime | continuation | 468 / 155 | 0.526 / **0.381** |
| REJECT with / against HTF swing bias | continuation | 689 / 706 | 0.522 / 0.528 |
| ICT MSS (REJECT sweep → close through the prior 3-bar swing within 8 bars) | reversal | 171 | **0.456** |
| Same with a displacement bar | reversal | 97 | 0.505 |
| MSS aligned with the EMA regime: displacement / plain | reversal | 36 / 60 | 0.556 / 0.467 |

**Structure geometry and persistence:**

| Test | NQ | Gold | EURUSD | Random-walk null |
|---|---|---|---|---|
| Race: weak extreme (`legH`) before protected extreme (`protL`), exec structure; observed vs gambler's-ruin prediction `(C − prot)/(weak − prot)` | 0.628 vs 0.648 (n 1,551) | 0.624 vs 0.646 (n 1,595) | not run | diff −0.002 ± 0.025 |
| DC overshoot / δ, δ = 1% (EU 0.4%), matched RW | 1.29 vs 1.17 ± 0.06 | **1.39 vs 1.19 ± 0.04** | 1.14 vs 1.11 ± 0.07 | |
| P(overshoot ≥ δ), δ = 1% | 0.43 | 0.46 | 0.40 (0.4%) | 0.40-0.42 |
| Current DC-leg direction predicts first touch | 0.510-0.517 | 0.495-0.562 | 0.468-0.499 | 0.467-0.513 |

**Reading.**
- On three liquid markets over two years, nothing in the structure family predicts the next side beyond about 1-3 pp, and a learner fitted to all of it loses out of sample. Gold's persistent trend gave a little at 120 bars.
- Two event findings are stable across horizons:
  - REJECT sweeps lean slightly toward **continuation** (51-53%);
  - **breakouts that hold against the HTF swing bias tend to fail** (continuation 38-46% depending on the regime definition).
- Race odds follow geometry. Trending instruments overshoot a little more than a random walk.
- **Limits.** One window (Nov 2024-Nov 2026), hourly bars only, Yahoo data, one label definition, overlapping samples, about 1,000-1,400 events per class. Grade **moderate** as an original reproducible test. It agrees in direction with S1-S5.

---

## 3. Engine gap analysis (`baseline_v2.pine`)

| # | Concept | Status | Where | What the engine does / differs |
|---|---|---|---|---|
| 1 | Swing points | **partial** | 879-882 (`pivLen` 5), 709-710 (`biasLen` 3 on MTF), 1752-1776 | 11-bar fractals on the chart, 7-bar on HTF/STF/EXE; no 3-candle STH. Pine's tie handling for `ta.pivothigh` is undocumented. A swing taken within `pivLen` bars of printing never becomes a pool or a sweep event |
| 2 | STH/ITH/LTH hierarchy | **partial** | 506-516 (`f_tierW`), 1779-1789 | Order proxied by timeframe tier; no nested ITH/LTH (see ICT-8 in `ict_liq.md`) |
| 3 | BOS | **present** | 746-759 (`f_structure`), 1542-1547 (chart BOS for OBs) | Close-based; the protected low re-arms at each BOS (correct SMC semantics) |
| 4 | CHoCH (swing) | **present** | 760-773 | Close through `protH`/`protL`. Internal `ibias` flips on any close through the last pivot (750-753) |
| 5 | MSS (ICT: sweep first, close through the pre-run STL, displacement) | **missing** | — | No sweep → MSS sequence; sweeps (1579-1582) and structure (708-782) are independent. Evidence says the MSS has no edge as a reversal signal (S2-S4, 2.2), so only an alert/readout is justified |
| 6 | Displacement | **present / overweighted** | 897-904; `wM` 0.20 in D (156, 1893) | Good as an FVG/OB quality gate. As a `D` component it measured 48.3-50.8% (2.2), and S3 finds no added value. Its weight should be set by measured skill (ICTS-1) |
| 7 | Protected / weak extremes | **partial (computed, unused)** | 755-773; returned 782; unused after 923-925 | `protH/protL` returned but never read; `legH/legL` not returned. Not used for invalidation (1343-1365), the HTF objective (1984-1989) or the panel |
| 8 | Dealing range / premium-discount | **wrong (definition)** | 727-779 (`rngH`/`rngL`), 968 (`htfEQ`), 2323-2333, 1354 | The range is the last pivot high to the last pivot low, not `[protected, weak]` of the current leg, so P/D % and `htfEQ` refer to an internal swing after any lower high/higher low |
| 9 | Structure → draw vector | **wrong (calibration)** | 1892-1898, `wDraw` 30 (145), `ctrMult` 0.50 (162), selection 1964-2035 | Fixed weights assume structure has directional skill. Measured skill of `D`: 49.9-51.6% (2.2). Draw is the largest pillar, side-first selection plus ×0.5 for counter-draw targets moves targets to the farther side without forecasting benefit |
| 10 | Sweep outcome read (HOLD = continuation, REJECT = reversal) | **wrong (sign)** | 1579-1582 | Pooled: REJECT → continuation 52.6% (n 1,402); HOLD against the HTF bias → reversal 56% (n 381); HOLD with the HTF bias → continuation 53.2%. S2: 65/66 folds continuation. The fixed REJECT = −1 adds noise of the wrong sign |
| 11 | ICT 2022 model sequence | **partial (pieces), rejected for scoring** | 1579-1582, 1897-1899, 1964-2035 | Pieces exist (raid → `D` flip → opposite-side target). S4: ≈0R before costs on 12 markets |
| 12 | MMXM (SMR, interior-consolidation ladder) | **missing (implicit via proximity)** | 661-667 | Lower highs on the way down are BSL pools anyway; the nearest draw-side pool is chosen after `D` flips. No evidence for the symmetric return |
| 13 | Turtle soup | **partial** | 1579-1582 | See `ict_liq.md` |
| 14 | OTE | **n/a (by design)** | — | Entry concept; no evidence for Fibonacci levels (S10); a target engine needs none |
| 15 | CISD | **n/a** | — | Entry trigger; no statistics |
| 16 | ITH/LTH and HTF weak extreme as targets | **partial** | 1779-1789, 780-781 | HTF/STF pivots join the registry only after `biasLen` HTF bars plus `[1]` (about 4 days on D); the current HTF leg's weak extreme is invisible until then except as a chart pivot (tier 0.25) or a PDH/PWH coincidence |
| 17 | HTF trend regime in probability | **present** | 1527-1531 (`f_bump` by `htfBias[H]`), 1286 (`f_empPoT` regime index) | Good: the empirical PoT is conditioned on the HTF swing regime, so any real trend persistence is learned in probability, not hard-coded |
| 18 | First-passage race (target vs opposing pool) | **present (Terminal only)** | 447-482, 1343-1365, 2127-2130 | The math matches the measured geometry (2.2). Not shown in the Clean style, which is what the user sees |
| 19 | Bias table | **present** | 2294-2309 | Swing bias, internal bias as fallback. Measured: per-TF bias is ≈ 50-52% informative |
| 20 | Structure-shift alerts | **missing** | 2077-2094 | Alerts exist for new DOL, iFVG, sweep and draw flip only |
| 21 | Directional-change scaling | **missing (not needed)** | — | A random-walk law; the engine's empirical PoT surface already captures excursion distributions per regime |

---

## 4. Proposals (best first; max 10)

Common Pine notes:
- New structural state is updated inside `if barstate.isconfirmed` (ENGINE, line 1518).
- Functions must be declared before first use, and globals they read must be declared before them.
- `request.*` tuple budget: "All the `request.*()` function calls in a script taken together cannot return more than 127 tuple elements" (`docsrc/jabez4jc_pinescriptv6/writing_scripts/limitations.md`, line 275). The current script uses about 52 (3×12 + 5 + 6 + 5), so there is room.
- No new `request.security` call is needed by any proposal below.

### ICTS-1 (P1) · Draw-skill gate: measure the draw vector online and scale its influence by its measured skill

**Why.** The draw pillar (`wDraw` 30) is the heaviest weight, `ctrMult` halves counter-draw targets, and selection is draw-side first with a 2× hysteresis to flip sides. All of that assumes `D` knows the direction. Every external test (S1-S5) and the engine replica (2.2: 49.9-51.6%) say it barely does on typical charts, while gold's trend shows it sometimes does (53-55% at long horizons). A fixed weight is wrong on both kinds of chart. Measure it, and let the chart decide.

**Inputs** (G_FLOW, after line 166):
```pine
bool  dSkill   = input.bool(true, "Scale Draw by Measured Skill", group = G_FLOW,
  tooltip = "Measures how often the draw direction called the side that was touched first (±Probe ATR within the PoT horizon) and scales the Draw pillar, the counter-draw penalty and side-first selection by that skill.")
float dSkK     = input.float(1.5, "Skill Probe Distance (ATR)", minval = 0.5, step = 0.25, group = G_FLOW)
int   dSkEvery = input.int(5, "Skill Probe Every N Bars", minval = 1, maxval = 50, group = G_FLOW)
float dSkFull  = input.float(0.56, "Accuracy for Full Draw Weight", minval = 0.51, maxval = 0.75, step = 0.01, group = G_FLOW)
float dSkPrior = input.float(60.0, "Skill Prior (pseudo-probes at 50%)", minval = 0.0, step = 10.0, group = G_FLOW)
float dFloor   = input.float(0.25, "Draw Weight Floor", minval = 0.0, maxval = 1.0, step = 0.05, group = G_FLOW,
  tooltip = "Minimum share of the draw kept even with no measured skill (keeps the ICT draw logic visible).")
```

**Type** (TYPES, after `Trial`, line 396):
```pine
// Draw-skill probe: which side of close ± k·ATR is touched first, and what each draw component said
type DProbe
    float up
    float dn
    int   bar0
    int   dS      // dirSide at open (-1/0/+1)
    int   sS      // sign of the structure component sV
    int   mS      // sign of the displacement component mV
    int   lS      // sign of liqEvt
    int   hS      // htfBias
```

**State** (STATE, after line 1079): `var array<DProbe> dq = array.new<DProbe>()`, `var array<float> skN = array.new<float>(5, 0.0)`, `var array<float> skK = array.new<float>(5, 0.0)` (index 0 D, 1 structure, 2 displacement, 3 liquidity events, 4 HTF bias), `var float drawRho = 1.0`.

**Helper** (STATE HELPERS, after the state):
```pine
f_skill(int c) =>
    (skK.get(c) + 0.5 * dSkPrior) / (skN.get(c) + dSkPrior)

f_skBook(int c, int s, int y) =>
    if s != 0
        skN.set(c, skN.get(c) + 1.0)
        skK.set(c, skK.get(c) + (s == y ? 1.0 : 0.0))
    s
```

**Resolve** (ENGINE, new step 2b right after the Trial loop, about line 1557; needs only `high`/`low`):
```pine
if dq.size() > 0
    for i = dq.size() - 1 to 0
        DProbe q = dq.get(i)
        if bar_index > q.bar0
            bool u = high >= q.up
            bool d = low <= q.dn
            if u != d
                int y = u ? 1 : -1
                f_skBook(0, q.dS, y)
                f_skBook(1, q.sS, y)
                f_skBook(2, q.mS, y)
                f_skBook(3, q.lS, y)
                f_skBook(4, q.hS, y)
                dq.remove(i)
            else if u and d or bar_index - q.bar0 >= H
                dq.remove(i)      // ambiguous bar or undecided within H: not booked
```

**Open and apply** (ENGINE step 14, right after `dirSide`, line 1895; `sV` and `mV` are in scope there):
```pine
if bar_index % dSkEvery == 0 and dq.size() < 128
    dq.push(DProbe.new(close + dSkK * atr, close - dSkK * atr, bar_index, dirSide,
      int(math.sign(sV)), int(math.sign(mV)), int(math.sign(liqEvt)), htfBias))
drawRho := dSkill ? math.max(dFloor, f_clamp((f_skill(0) - 0.5) / math.max(dSkFull - 0.5, 1e-6), 0.0, 1.0)) : 1.0
int dirSel = drawRho >= 0.5 ? dirSide : 0     // side-first selection only when D has shown skill
```

**Use:**
- Step 17 (line 1948): pass `drawD * drawRho` to `lv.evaluate(...)` in place of `drawD`. The draw pillar shrinks toward 0.5, and the counter-draw multiplier (`dirD * side <= -dGate`, line 692) only fires when the scaled D is strong.
- Step 19 (lines 1975-2035): replace `dirSide` with `dirSel` in `elig`, `useCtr`/`ctrHold`/`curElig`, `activeCtr` and the "⊘ INVALIDATED" ghost condition.
  - With low skill, selection becomes the global best: no `⚠ COUNTER-DRAW` label, and no ghosting just because `D` wobbled.
  - The HTF objective keeps `dirSide`, because it is display-only.
- `drawFlip` (line 1897): keep the event but add `and drawRho >= 0.5`. Append the skill to the alert text.

**UX:**
- Terminal DRAW row (line 2339): `▲ +0.42 · skill 51% (n 812) ×0.25`.
- Full accuracy view: `D-SKILL  STRUCT 51% · DISP 49% · LIQ 50% · HTF 52%`. Each component's own `f_skill(c)` tells the trader which part of the draw logic works on this symbol.
- Data window: `plot(drawRho * 100, "Draw weight %", display = display.data_window)`.

**Cost.** At most 128 probes, O(1) each per confirmed bar.

**Expected value.**
- Targets stop being pushed to the farther side by a coin-flip `D` and stop flipping sides with `D` noise (fewer "jumps").
- On charts where `D` has skill (trending gold-like regimes) it is used fully.
- The ledger's `EDGE` (hits vs distance-matched random, lines 1461-1499) and the probe skill both measure the change, so before/after can be compared on the same chart.

**Evidence.** Moderate. S1-S5 plus the original test agree that structure-derived direction is ≈ 50-52% on most instruments. The calibration method (Beta-binomial shrinkage toward 50%) is standard.

**Risk.**
- The label is a symmetric ±k ATR first touch, not the engine's actual targets, so it is a direction-skill proxy. The ledger still measures the target-level effect.
- With `dSkPrior` 60 and one probe per 5 bars, about 300 bars are needed before the gate moves. The 5,000-bar history provides about 900 probes.
- The product spec features "Draw Direction" prominently. The floor (0.25) keeps it visible and partially active.

**Effort.** M.

### ICTS-2 (P1) · Correct the sweep-outcome mapping in `liqEvt` (HOLD against the HTF swing = failed breakout; REJECT ≠ reversal)

**Why.** Line 1581 assigns +1 (continuation) to HOLD and −1 (reversal) to REJECT, weighted by tier.
- Measured on three markets (2.2):
  - REJECT → continuation 52.6% (n 1,402), 51.2% at 120 bars, 53.3% at 12 bars: never a reversal edge;
  - HOLD against the HTF swing bias → reversal 56.2% (n 381); against the EMA regime → reversal 61.9% (n 155);
  - HOLD with the HTF bias → continuation 53.2% (n 423).
- External: S2 (sweeps predict continuation, 65/66 folds; reversal reads should be faded), S5 (London sweeps: the trend decides; against-trend reads correct only 25-30%), and `ict_liq.md` E6 (reversal after EQ sweeps 39-44%).
- The current mapping injects a wrong-signed signal into 30% of `D`.

**Inputs** (G_FLOW):
```pine
float swHoldW = input.float(0.5, "Sweep · Holds With HTF (continuation)", minval = -1.0, maxval = 1.0, step = 0.05, group = G_FLOW)
float swFailW = input.float(0.5, "Sweep · Holds Against HTF (failed breakout)", minval = -1.0, maxval = 1.0, step = 0.05, group = G_FLOW)
float swRejW  = input.float(0.0, "Sweep · Closes Back Inside", minval = -1.0, maxval = 1.0, step = 0.05, group = G_FLOW,
  tooltip = "+ = continuation, − = reversal. Measured on NQ / gold / EURUSD 1H: slight continuation (52-53%). The old fixed value was −1.")
```

**Code** (replaces lines 1579-1582):
```pine
// sweep read: + continuation / − reversal of the raid, then signed by side
if hit and lv.isLiquidity()
    bool  hold = lv.side == 1 ? close > lv.top : close < lv.bottom
    bool  rej  = lv.side == 1 ? close < lv.price : close > lv.price
    float c    = hold ? (htfBias == lv.side ? swHoldW : htfBias == -lv.side ? -swFailW : 0.0) : rej ? swRejW : 0.0
    liqEvt := f_clamp(liqEvt + c * lv.side * lv.tier(), -1.0, 1.0)
```

**Interaction.** This is the static prior that `ict_liq.md` ICT-2 (a per-chart learner over HOLD/REJECT/NEUTRAL × context) should start from. When ICT-2 lands, add the HTF-alignment dimension to its cells: `cls*2 + ctx` becomes `cls*3 + align` with align ∈ {with, against, none}. ICTS-1's component skill `f_skill(3)` shows whether `liqEvt` helps on the chart.

**Evidence.** Moderate (original pooled test plus S2, S5, E6). **Risk.** Low. The weights are inputs, and the effect is bounded by `wL` and the tier. **Effort.** S.

### ICTS-3 (P2) · "Which pool first": show the first-touch race against the opposing pool in the Clean label

**Why.** The user's core question is "which liquidity will price reach next". Direction from structure is ≈ coin-flip (2.2), but the race between two pools is predictable from geometry and drift. The engine's `f_race`/`f_raceH` (lines 447-482) compute it, and `f_raceAdj` (1367-1371) corrects it with the ledger's observed first-touch outcomes. Measured calibration of the geometric race: within 2 pp on NQ and gold (2.2). Today this number appears only in the Terminal HUD (WIN≤H%).

**Change:**
- `f_invalidation` (1343-1365) also returns the opposing level's index:
  - track `int oppI = -1` in the loop and set `oppI := i` when `best` updates;
  - return `[inv, d / risk, p, oppI]`.
- Update both destructurings:
  - line 1428 `[inv, rr, pR, oI0] = f_invalidation(lv)`;
  - line 2127 `[i0, i1, i2, i3] = f_invalidation(activeLv)`.

  Pine requires every tuple element to be named; do not use `_`.
- Input (G_DOL): `bool showRace = input.bool(true, "Show First-Touch Odds", group = G_DOL)`.
- Clean label (line 2225): append `"\n1st: " + str.tostring(invWin * 100.0, "0") + "% vs " + oppTag`, where `oppTag = i3 >= 0 ? f_shortName(pool.get(i3).kind, pool.get(i3).src) : "−1.5 ATR"`.
- Optional: one dotted thin line at the opposing pool's near edge from the last bar to `xR`, in the opposing side colour at 70% transparency. This adds 1 line object.
- Tooltip: "Probability the target is touched before the opposing pool, among races decided within the PoT horizon; corrected by this chart's observed first touches."

**Expected value.** It answers "BSL or SSL first?" with a calibrated number the ledger already grades (race stats, line 1080 `raceSt`). It also makes it obvious when a target with a high PoT is likely to be beaten by the opposite pool.

**Evidence.** Strong for the math (first-passage of Brownian motion with drift) and moderate for the calibration (2.2 race test; the engine's own `raceSt`).

**Risk.** Label clutter: it is one extra line, toggleable. When no opposing pool is within `maxATR` the fallback is 1.5 ATR, so show the tag `−1.5 ATR` honestly.

**Effort.** S.

### ICTS-4 (P2) · Return ICT's dealing range from `f_structure`: [protected extreme, weak extreme] of the current leg

**Why.** `rngH`/`rngL` are the last pivot high and low, so after any internal lower high the "range" shrinks to a sub-swing (1.9). The engine already computes the correct pair. This fixes:
- the Terminal P/D % (2323-2333);
- the `htfEQ` confluence anchor (968, used in the confluence pillar, 1931);
- the `f_invalidation` fallback (`exeRL`/`exeRH`, 1354), which becomes the protected swing in trend;
- every dealing-range proposal in the companion studies (ICT-4 IRL/ERL, ICTPD-4/7).

**Code** (in `f_structure`, after the bias update, before the `rngH/rngL` extension at 776-779). Keep the old values as the neutral-state fallback:
```pine
float drH = bias == 1 ? legH : bias == -1 ? protH : rngH
float drL = bias == 1 ? protL : bias == -1 ? legL : rngL
```
Return `drH[1], drL[1]` in place of `rngH[1], rngL[1]` (line 782). The tuple shape is unchanged, so no other call site changes.

**Semantics.**
- Bull leg: `legH` is the running high since the last BOS (re-armed at the break, line 758), the **weak high**. `protL` is the **strong low**.
- Bear leg: mirror.

The P/D readout then answers ICT's question: is price in discount of the bullish leg?

**Check.**
- At the first BOS from bias 0, `protL := legL` is defined.
- `legH >= high >= close`, so the range always contains price until a CHoCH re-arms it. There are no `na` holes because the bias-0 state falls back to the old range.
- Registry prominence uses `htfRL/htfRH`/`stfRL/stfRH` only as a magnitude (1783-1789), so that is fine.

**Expected value.** Correct ICT semantics in every place that reads "range". Measurable indirectly: the confluence-anchor hit lift via the candidate ledger (ICT-1).

**Evidence.** None for edge; this is a definitional correctness fix.

**Risk.** Changes `htfEQ` values, and therefore some confluence scores. The P/D % will look different (more "premium" right after breaks).

**Effort.** S.

### ICTS-5 (P3) · Structural anchors: protected-swing invalidation option and weak-extreme objective tag

**Why.** ICT/SMC traders place risk beyond the protected low and aim at the weak high (1.8, 1.14). `f_invalidation` uses the nearest opposing pool, which is often an inner pool, so the Terminal R:R/WIN% describe a different trade from the one an ICT trader takes. The race test shows the weak-before-protected odds follow geometry (2.2). The aim is semantic alignment, not edge.

**Changes:**
1. Expose the protected levels: with ICTS-4 in place, `exeRL`/`exeRH` already equal `protL`/`protH` during trends. Otherwise read `exeProtL`/`exeProtH` (already returned, 925).
2. Input `string invMode = input.string("Nearest Opposing Pool", "Invalidation", options = ["Nearest Opposing Pool", "Protected Swing (Exec)", "Protected Swing (STF)"], group = G_DOL)`.
3. In `f_invalidation`, when the mode is protected and the target side equals that TF's swing bias, take:
   ```pine
   float sw = tgt.side == 1 ? nz(exeProtL) : nz(exeProtH)   // or stfProtL / stfProtH
   inv := not na(sw) and (tgt.side == 1 ? sw < close : sw > close) and math.abs(close - sw) / atr <= maxATR ? sw - tgt.side * buf : inv
   ```
   Fall back to the current rule otherwise.
4. Objective tag: in step 19 (1984-1989), if the HTF objective is within `eqTol·atr` of the HTF weak extreme (`htfRH` when `htfBias == 1` after ICTS-4), append `· WEAK H` (`WEAK L`) to its label.
5. Terminal: a thin dotted "PROT" line at the execution protected level (1 line).

**Expected value.** The R:R/EV readout matches the ICT trade. The ledger's race stats (`raceSt`) then grade the trader's actual stop logic.

**Evidence.** None (definitions; geometry-only per 2.2). **Risk.** Wider stops show lower R:R, which is honest. **Effort.** S.

### ICTS-6 (P3) · Structure-shift alerts with a measured follow-through rate

**Why.** Traders using ICT models want an alert when the HTF swing bias flips and when an execution-TF MSS (sweep → close through the pre-run STL) prints. The evidence says MSS reversal reads are a coin flip (45.6-50.5%, S3, S4), so each alert should carry the chart's own measured follow-through, not a promise.

**State and series** (global scope; non-repainting, confirmed bars only):
```pine
float stlP = ta.pivotlow(low, 1, 1)       // 3-candle swing low, known 1 bar later
float sthP = ta.pivothigh(high, 1, 1)
var float lastStl = na
var float lastSth = na
var int   mssDir  = 0
var float mssLvl  = na
var int   mssTill = na
var int   mssEvt  = 0                     // +1 / -1 on the bar an MSS prints
```

**Engine:**
- In step 3, on `hit and lv.isLiquidity()` with REJECT: arm `mssDir := -lv.side`, `mssLvl := lv.side == 1 ? lastStl : lastSth`, `mssTill := bar_index + mssWin` (input, 8).
- Each confirmed bar:
  - update `lastStl`/`lastSth` from `stlP`/`sthP`;
  - `mssEvt := 0`; if `bar_index <= mssTill` and `mssDir == -1 ? close < mssLvl : close > mssLvl`, then `mssEvt := mssDir` and `mssDir := 0`.
- Follow-through: add component index 5 to ICTS-1's probes, the sign of the last MSS while it is younger than H bars.

**HTF flip.** `bool htfShift = barstate.isconfirmed and htfBias != htfBias[1] and htfBias[1] != 0`. `htfBias` comes from a `[1]` + `lookahead_on` request, so it changes once per HTF close and does not repaint.

**Alerts** (after line 2094):
```pine
alertcondition(htfShift, "HTF Structure Shift", "DOL Engine: higher-timeframe swing structure flipped on {{ticker}} ({{interval}})")
alertcondition(mssEvt != 0, "Execution MSS", "DOL Engine: market structure shift after a liquidity sweep on {{ticker}} ({{interval}})")
```
Each event also gets an `alert()` with the text `MSS ▼ after BSL sweep · follow-through on this chart 46% (n 171)`.

**UX.** A Terminal row `STRUCT  MSS ▼ 3 bars ago · FT 46% (n 171)`.

**Evidence.** None for edge (S3, S4, 2.2); value is UX and transparency. **Risk.** Alert noise on low timeframes; `mssWin` and a displacement gate reduce it. **Effort.** S.

### ICTS-7 (P3) · Register the HTF/STF weak extreme before pivot confirmation

**Why.** The current HTF leg's extreme, the textbook HTF objective, enters the registry only after `biasLen` HTF bars plus the `[1]` shift (about 4 days on D, about 16 hours on 4H). Until then it is at best a chart pivot at tier 0.25. Evidence says tier labels add little beyond distance (`ict_liq.md` E6), so this is mainly correct labelling and the HTF freshness/tier treatment of the obvious target.

**Code:**
- `f_structure` also returns `legH[1], legL[1], legHT[1], legLT[1]`, where `legHT`/`legLT` are the `time` values updated when `legH`/`legL` set a new extreme. Each tuple grows by 4, to 16 elements × 3 calls = 48 + 16 others ≈ 64 of 127.
- In step 10 (1779-1789), on confirmed bars, for HTF and STF:
  - if `htfBias == 1` and `htfLegH` is unswept on the chart (`high <= htfLegH` since `legHT`; use the registry's own raid check, step 4) and `(htfLegH - close) / atr >= minDistATR`, call `f_pushExt(extReg, htfLegH, true, 2, f_barAtTime(htfLegHT, anchorMax), …)`;
  - mirror for `htfBias == -1` and `htfLegL`.
- `f_pushExt` already dedups by price and upgrades the tier, and `f_mergeLiq` folds it into an existing chart pool (upgrading `src`).

**Edge cases.**
- The trailing extreme moves while the leg extends. Only register it once price has left it by `minDistATR`.
- If a higher high prints later, the old entry is swept by the step-4 raid check, and the new one registers when price leaves again.

**Evidence.** Weak (ICT doctrine; tier effects small). **Risk.** More registry churn; duplicates are handled by dedup. **Effort.** M.

### Considered and rejected
- **MSS / CHoCH / CISD as scoring or `D` inputs.** Reversal reads measured 45.6-50.5% (2.2). Nordman's edge ratio is ≈ 1.0 with or without displacement (S3). Mahadzva: fade the CHoCH (S2). They are kept only as alerts with measured follow-through (ICTS-6).
- **The 2022 model or MMXM as a target engine** (sweep → MSS → FVG → opposite pool; interior-consolidation ladder). Mechanised, it is ≈ 0R before costs on 12 markets (S4). The engine already selects the nearest draw-side pool after `D` flips. A display-only narrative is possible but adds clutter without forecast value.
- **OTE / Fibonacci 62-79% as levels or scoring.** No level-specific effect; continuation odds fall smoothly with depth (S10). For a target engine it is geometry already captured by the race model.
- **A multi-feature learned `D` (logistic or online SGD).** Out of sample it was worse than a coin on all three markets (2.2). The per-component skill readout in ICTS-1 gives the same insight without overfitting.
- **"Regime-confirmed" bias table (show BULLISH only when HTF swing and EMA regime agree).** Pooled accuracy agree 51.7% vs disagree 52.1% at 30 bars (0.533 vs 0.483 at 120). That is inside the random-walk band of ±6 pp. Not worth a UX change.
- **Trend-strength / exhaustion term (Schmidhuber cubic) in `D`.** Coefficients are universal but tiny (S6), and the z120³ sign was inconsistent across markets (2.2).
- **Directional-change leg as the PoT regime index.** Leg direction 47-56% (2.2), no better than the HTF swing bias the empirical surface already uses (line 1531).
- **3-candle STH pools.** They add near, trivially reachable targets; distance dominates (E6 in `ict_liq.md`). The ITH variant is ICT-8 there.

---

## 5. Notes for implementers
- **Order of work.** Do ICTS-2 (one block at 1579-1582) and ICTS-4 (two lines in `f_structure`) first; both are small and independent. ICTS-1 next: it changes selection behaviour, so check the ledger `EDGE` and the probe skill before and after on a few symbols (NQ, ES, EURUSD, XAU, BTC; 15m and 1H). ICTS-3 and ICTS-5 touch `f_invalidation`'s signature: update both destructurings (1428, 2127) in the same edit.
- **Non-repainting.** Every new state change sits in the confirmed-bar ENGINE block. ICTS-6's `htfShift` uses the `[1]`-offset `htfBias`, and ICTS-7 uses the `[1]`-offset trailing extremes. No live (unclosed) value enters scoring.
- **Pine specifics.**
  - `math.sign()` returns a float; wrap it in `int()` for the `DProbe` fields.
  - Destructured tuple names must all be distinct identifiers.
  - Keep `DProbe` declared in TYPES before STATE uses it.
  - `f_skill`/`f_skBook` read the global arrays, so declare them after STATE (Pine has no forward references).
- **Measurement.** With ICTS-1 in place the Full accuracy panel shows component skills. If a component sits at ≤ 50% on most symbols for long histories, set its weight input default to 0 (`wM` for displacement is the likely first candidate, then `wL`).

---

## 6. Sources
- Quarter Sequence, "ICT Market Structure: Swing Points, BOS and MSS Explained" (ICT quotes with lecture timestamps: 2022 Mentorship Ep. 3, 5, 6, 12; "Market Structure Is Not It", 2021). https://quartersequence.com/the-study/ict-market-structure/
- Nordman Algorithms, "ICT Displacement and the Market Structure Shift: We Tested 15,817 Signals" (Nov 2026). https://www.nordman-algorithms.com/blog/ict-displacement-market-structure-shift/
- Nordman Algorithms, "BOS vs CHoCH: Why the Same Move Gets Two Labels" (Oct 2026). https://www.nordman-algorithms.com/blog/bos-vs-choch/
- Tangirala, K. H. (2026). *Do Smart Money Concepts Predict Returns? Evidence from 44 Formalised Detectors on S&P 500 Daily Bars, 2010-2026.* SSRN 7483658. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7483658
- Mahadzva, S. (2026). *Smart Money or Costly Folklore? A Systematic Evaluation of ICT/Smart-Money-Concepts Trading Rules in G10 FX.* SSRN 7430998. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7430998
- Taylor, V. (2026). *Evaluating the Predictive Validity of ICT's Accumulation-Manipulation-Distribution (AMD) Model on CME E-Mini NASDAQ-100 Futures.* arXiv 2610.35887. https://arxiv.org/abs/2610.35887 (code: https://github.com/veertaylor19/amd-backtest)
- IvanSetuper, "ICT 2022 Model - Liquidity Sweep, MSS & FVG Entry" (open-source TradingView script with a 12-market test, 2026). https://www.tradingview.com/script/Doc312Ae-ICT-2022-Model-Liquidity-Sweep-MSS-FVG-Entry/
- Schmidhuber, C. (2021). *Trends, Reversion, and Critical Phenomena in Financial Markets.* Physica A; arXiv 2006.07847. https://arxiv.org/abs/2006.07847 · Safari, S. A. & Schmidhuber, C. (2025). *Trends and Reversion in Financial Markets on Time Scales from Minutes to Decades.* arXiv 2501.16772. https://arxiv.org/abs/2501.16772
- Moskowitz, T., Ooi, Y. H. & Pedersen, L. H. (2012). *Time Series Momentum.* J. Financial Economics 104(2). https://www.sciencedirect.com/science/article/pii/S0304405X11002613 · http://docs.lhpedersen.com/TimeSeriesMomentum.pdf
- Glattfelder, J. B., Dupuis, A. & Olsen, R. B. (2011). *Patterns in high-frequency FX data: discovery of 12 empirical scaling laws.* Quantitative Finance 11(4). Summary in Glattfelder, *The Theory of Intrinsic Time*, arXiv 2406.07354. https://arxiv.org/html/2406.07354v1 · Dupuis & Olsen (2012), *High Frequency Finance: Using Scaling Laws to Build Trading Models*. http://olsendata.com/data_products/client_papers/papers/201206-DupuisOlsen-HFFinScaLawTraMod.pdf
- Osler, C. L. & Chang, P. H. K. (1995). *Head and Shoulders: Not Just a Flaky Pattern.* FRBNY Staff Report 4. https://www.newyorkfed.org/research/staff_reports/sr4.html · Chang & Osler (1999), *Methodical Madness*, Economic Journal 109. https://www.jstor.org/stable/2565638
- Savin, G., Weller, P. & Zvingelis, J. (2007). *The Predictive Power of "Head-and-Shoulders" Price Patterns in the U.S. Stock Market.* J. Financial Econometrics. https://www.biz.uiowa.edu/faculty/gsavin/papers/hsrevision_paw_10%2019%2006.pdf
- Tradeify, "Fibonacci Retracements and Extensions Put to the Test" (2026). https://tradeify.co/education/fibonacci-retracements-and-extensions
- LuxAlgo concept library: Market Maker Models https://www.luxalgo.com/library/concept/market-maker-models/ · Model 2022 https://www.luxalgo.com/library/concept/model-2022/ · Change in State of Delivery https://www.luxalgo.com/library/concept/change-in-state-of-delivery/ · Displacement https://www.luxalgo.com/library/concept/displacement/
- ProEA, "BOS CHoCH & MSS Market Structure Indicators for TradingView" (survey of 15 open-source scripts' swing/break rules, Oct 2026). https://proea.app/en/blog/best-bos-choch-indicator-tradingview
- TMGM Academy, "Market Maker Model (MMXM)". https://www.tmgm.com/en/academy/trading-academy/market-maker-model
- Turtle soup rules: https://proea.app/en/blog/turtle-soup
- Pine v6 docs used: `docsrc/jabez4jc_pinescriptv6/reference/ta.md` (`ta.pivothigh`, ties undocumented); `docsrc/jabez4jc_pinescriptv6/writing_scripts/limitations.md` line 275 (127 tuple-element limit across all `request.*()` calls).
- Data for the original test: Yahoo Finance 60-minute bars (NQ=F, GC=F, EURUSD=X), retrieved Nov 2026 through a data-provider API; code and full results in `study/ict_struct_tools/`.
