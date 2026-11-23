# Price-action targeting and projections: study for DOL Engine v2

Domain: Al Brooks price action (magnets, measured moves, breakout tests, failed breakouts, trading range vs trend, "always in", second entries, the 20-gap-bar rule, the traders' equation); measured-move and leg-equality targets (AB=CD, "leg 1 = leg 2", Bulkowski's measured move and measure rule); Fibonacci extensions used as targets (127.2 / 161.8 / 200 %, ICT "standard deviation" projections −0.27 / −0.62 / −1 / −2 / −2.5 / −4); swing projection from displacement legs; Elliott and harmonic target heuristics; Dow theory. The question throughout: **does any projection method tell us how far a leg will go, which liquidity is taken next, and how likely, better than a random level at the same distance?**

Line numbers refer to `brief/baseline_v2.pine` (identical to `indicators/dol_engine.pine`). Sibling studies are cited by proposal id where they already cover a topic: `ict_struct.md` (ICTS), `ict_pd.md` (ICTPD), `ict_liq.md` (ICT), `bias_dol.md` (BIAS), `wyckoff_sd.md` (WYK), `quant_pot.md` (QPOT), `quant_regime.md` (REG), `academic_sr.md` (ACAD), `calib_ml.md` (CAL), `competitors.md` (COMP), `ict_time.md` (TIME), `session_stats.md` (SESS), `orderflow_micro.md` (OF).

**Reproduction.** Every number tagged **[this study]** comes from `study/pa_tools/` (run `python3 -I <script> <args>`; outputs `out_*.txt` next to the scripts). Data are the files sibling studies already use:
- **1h set (9 series):** CME ES, NQ, RTY, YM, GC, CL (Mar 2025 to Apr 2026, about 6,200 bars each); BTC 2016-2025 (79,000 bars); EURUSD 2017-18 (5,000); EURUSD 2024-26 (12,300).
- **5m set (6 series):** the six CME 1-minute files (Jan to Apr 2026) resampled to 5 minutes, about 16,800 bars each.
- **Daily set (3 series):** S&P 500 and NASDAQ 1999-2018, GOOG 2004-2013.

Every test is compared with either (a) **martingale geometry** (a driftless race to +a before −b has P = b/(a+b) for any continuous martingale), (b) the **engine's own random-level baseline** (the unconditional K-bar excursion survival at the same ATR distance, the `f_potBase` idea, 1314-1322), or (c) a **bar-shuffled null** (each bar's shape and gap kept, order destroyed).

**Research-access note.** WebFetch could not reach most hosts (thepatternsite, brookstradingcourse, luxalgo, mql5, tradeify, wikipedia and arxiv all failed DNS in this session), and Firecrawl web search ran out of credits. Published numbers below therefore come from search-result summaries (marked "via search summary"), from full-text passages of the paper index (Glattfelder et al.), or from sibling reports. The original tests in this study carry most of the weight.

---

## 0. Executive summary

1. **No projection ratio is special.**
   - Setup: ATR-zigzag legs (threshold k = 2 or 3 ATR), 18 series, 3 timeframes, about 39,000 legs.
   - Ratios of successive legs show **no clustering at any Fibonacci ratio**:
     - retracements at 0.382 / 0.5 / 0.618 / 0.786;
     - same-direction projections at 1.0 (AB=CD) / 1.272 / 1.618 / 2.0 / 2.618.
   - The local "bump index" (density inside ±3% of the ratio over density in the flanking bins) is 0.91-1.02 at the Fibonacci ratios on 14,873 hourly legs. Non-Fibonacci placebo ratios give 0.87-1.13, and the bar-shuffled null gives 0.88-1.13 [this study, T1].
   - This replicates Batchelor & Ramyar's DJIA 1915-2003 bootstrap test ("no evidence"), now on intraday futures, FX and crypto.
2. **The measured move ("leg 1 = leg 2", AB=CD) is reached half the time, exactly as a random walk predicts.**
   - P(leg CD ≥ leg AB) = 0.490 (1h), 0.498 (5m), 0.496 (daily). The shuffled null gives 0.491 / 0.498 / 0.492 [this study, T1].
   - For a symmetric random walk the two legs are i.i.d., so 0.5 is the null. Bulkowski's own measured-move target uses only **60%** of the first leg (via search summary), which is consistent with this.
3. **The quantitative version of "how far will this leg go" is the directional-change overshoot law, and it is a Brownian-motion law.**
   - Setup: once price reverses by δ = k·ATR from an extreme (the leg is "confirmed"), measure the leg's further extension before the next δ reversal (the overshoot OS).
   - OS is close to **Exponential(mean δ)**:
     - mean OS/δ = 1.04-1.10, median 0.63-0.74 (theory 0.693);
     - P(OS ≥ δ) = 0.34-0.39 (theory e⁻¹ = 0.368);
     - P(OS ≥ 2δ) = 0.139-0.160 (theory 0.135);
     - 6 dataset × threshold cells [this study, T1].
   - This is Glattfelder-Dupuis-Olsen's FX overshoot scaling law ("average overshoot ≈ threshold", total move ≈ 2× threshold, 13 FX pairs). It is also the Taylor (1975) / Lehoczky (1977) result for Brownian motion.
   - **The previous leg's size carries no information about the current leg**: corr(log previous same-direction leg, OS) = −0.03 to +0.03, and the top vs bottom tercile of previous leg size gives the same P(OS ≥ δ).
   - This law is the honest replacement for measured-move folklore. It gives a closed-form **"reach before a δ pullback" probability** (proposal PA-3).
4. **Projection levels are reached at random-level rates.**
   - Setup: after a confirmed pullback C (A < C < B), the engine's random-level baseline was compared with every common projection:
     - AB=CD at 0.5-2.0 × leg (MM ratios f);
     - ICT −0.27 / −0.62 / −1 / −2 "SD" extensions of the impulse (= classic 127.2 / 161.8 / 200 / 300 %);
     - 127.2 / 161.8 / 200 % extensions of the pullback.
   - Edges are −0.5 to +2.7 pp. The edge is **flat across ratios** (1h: f = 0.9 +0.5, f = 1.0 +0.4, f = 1.1 +0.8 pp; 5m: +1.9 / +2.7 / +2.2 pp). The small uplift is an event-conditional volatility effect, not a level effect.
   - Once touched, price goes 1 ATR beyond before coming back 1 ATR with probability 0.47-0.50: no stall at the measured move (martingale 0.5) [this study, T2].
   - An independent benchmarked study found the 1.618 extension reached **less** often than a random walk at the same distance: 67% vs 71%, t = −13.5, 26,795 patterns (MQL5 blog, via search summary).
5. **Brooks's headline probabilities are geometry.**
   - "A strong breakout has about a 60% chance of a measured move" (measured from the breakout bar's low): measured races match martingale geometry within ±1.5 pp for breakout bars of ≥ 1 and ≥ 1.5 ATR body.
     - With a follow-through bar, the win rate rises to 0.59-0.67. Geometry rises to the same values: the follow-through bar simply moves the entry closer to the target and away from the stop.
     - Only very large bars (body ≥ 2 ATR, closing in the outer quarter, beyond the 20-bar extreme) beat geometry: 1h +2.5 ± 1.2 pp, 5m +3.4 ± 1.8 pp. That is inconsistent across series (6 of 9 hourly series positive, BTC-driven; 4 of 6 5-minute series positive), so the grade is weak [this study, T3].
   - **H2/L2 second entries** race the trend extreme against the pullback low at geometry: −1.1 ± 2.0 pp (1h), +3.8 ± 2.9 (5m), +1.9 ± 4.4 (daily).
   - The **20-gap-bar first moving-average touch** does not retest the trend extreme more than a random level at that distance: −1.4 ± 1.5 pp (1h), +1.3 ± 1.7 (5m). Brooks's forum figure is 70-75%; the raw intraday rate within 30 bars is 48-52% [this study, T3].
   - The **"Always In" direction** (latest strong two-bar breakout) has **no information** about which side's nearest pool is taken first: +0.2 ± 0.5 pp (n = 10,169, 1h), +0.1 ± 0.6 (5m) [this study, T4]. This corroborates REG and ICTS: a structure or momentum direction vote does not pick the side.
6. **"80% of trading-range breakout attempts fail" is overstated, but the direction is right.**
   - A close beyond a 20-bar range is followed by a close back inside within 5 bars **53-62%** of the time, vs **48-53%** on the shuffled null (+3 to +7 pp).
   - Breakouts from 4-8 ATR ranges then reach the range-height measured move before the opposite edge 2.6-3.1 pp more often than geometry (1h, 5m, daily). That matches Wyckoff's +0.03 ± 0.02 [this study, T4].
   - Both effects are small. They support the siblings' fix of `liqEvt` ("a raid that holds = continuation" is unreliable; BIAS-4, ICTS-2), not new level sources.
7. **One Brooks magnet the engine lacks has measurable support: the prior RTH close (gap-fill / ICT "opening range gap").**
   - At 10:00 ET on CME futures (n = 968 instrument-days), the untouched prior 16:00 close is reached within the session **+3.4 ± 1.3 pp** more often than a random level at the same distance and the same hour of day (+3.5 ± 1.4 pp within 30 bars). At 1-2 ATR the edge is +4.8 / +7.1 pp [this study, T5].
   - Against an all-hours baseline the edge looks like +12.7 pp, which shows how much the time-of-day confound inflates naive gap-fill statistics (QPOT-02, TIME-1).
   - On default 23-hour ETH futures charts this level is invisible to a time-gap detector: TradingView treats ETH as the regular session for futures. It needs a session-time capture (PA-2).
8. **Price discovery is where a liquidity engine goes blind, and where projections have a legitimate job.**
   - On 5.0% of hourly bars, 5.8% of 5-minute bars and 13.7% of daily bars there is no unswept pivot pool within 10 ATR on the EMA50-trend side [this study, T6].
   - The engine then falls back to a counter-draw target or to nothing (1999-2005).
   - Because projections are reached at random-level rates (finding 4), a projection there carries an honest, already-calibrated PoT. It fills the gap without claiming an edge (PA-1).
9. **Dow theory.**
   - Hamilton's Dow-theory timing had positive alpha 1902-1929, and a neural-net replication beat buy-and-hold by 4.4 pp a year 1930-1997 (Brown, Goetzmann & Kumar 1998).
   - That is a **long-horizon trend** result. At the engine's horizons, structure-based side votes test at coin-flip (ICTS §2.2, REG finding 2). The engine's `f_structure` (708-782) is already a sound Dow/ICT implementation, so nothing more is needed from this domain.
10. **Elliott and harmonic patterns.** No independent test shows forecasting skill.
    - CXO rated Prechter's accuracy 21% vs a 47% guru average.
    - Harmonic backtests are small-n student projects, and their claims are inflated by researcher degrees of freedom.
    - Their target ratios are Fibonacci ratios, which finding 1 rejects. **Do not implement.**

**What this domain contributes to the engine** (five proposals, section 4):
- an honest **price-discovery projection fallback** (PA-1, P1);
- the **prior-RTH-close / ORG level** captured by session time (PA-2);
- the **leg-reach-before-pullback probability** from the overshoot law, graded by the ledger (PA-3);
- a stricter **Brooks-strength definition of displacement** for D (PA-4);
- **measured-move shadow baselines and breakout-context features** for the candidate ledger (PA-5);
- plus a documented "do not add" list (section 5), so nobody spends effort on Fibonacci, harmonic, Elliott, H2 or 20-gap-bar logic.

---

## 1. Concepts (precise definitions and parameters)

Notation: A = ATR(14) (Wilder RMA, as `ta.atr`). "Taken" = strict trade-through for liquidity (the engine's `touched`, 623-624); "touched" = ≥ / ≤ for projections and arrays. "Geometry" = the driftless race probability b/(a+b).

### 1.1 Swing / leg definitions used for projections
- **Pivot swing (engine).** `ta.pivothigh(high, len, len)` with len = 5 (`pivLen`, 90). It is confirmed len bars after the extreme. Successive pivots need not alternate (two highs can occur in a row).
- **ATR zigzag (directional change, DC).** This is the definition used in this study and in Elliott, harmonic and Brooks leg counting.
  - Mode up: track the running maximum M (and its bar). A **directional change** is confirmed on the first bar whose low ≤ M − k·A, which makes M a swing high.
  - The new running minimum starts from the lowest low after M.
  - A bar that makes a new extreme and also retraces k·A in the same bar is not used to confirm (intrabar order is unknown).
  - Parameters: k = 2 (≈ Brooks "leg"), k = 3 (≈ swing). Pivots alternate by construction.
  - Edge cases: ATR warm-up; gaps (the confirmation can happen on a gap bar).
- **Leg** = |p(i+1) − p(i)| between successive zigzag pivots. **Retracement ratio** R = L(i+1)/L(i). **Projection ratio** E = L(i+2)/L(i) (same-direction legs: AB vs CD).
- **Overshoot (Glattfelder et al.).** After the DC that confirms pivot i, the DC price is p(i) ∓ δ (δ = k·A at confirmation). The overshoot OS is the further distance from the DC price to the next pivot.

### 1.2 Measured moves (Brooks, Bulkowski)
- **Leg 1 = Leg 2 / AB=CD.** For a bull move, A (low) → B (high) → C (higher low, A < C < B); target D = C + (B − A). Brooks says a pullback "usually has a second leg that is often about the same size as the first" and that traders take profits at the measured move (Brooks Trading Course analysis pages, via search summary).
  - Variants: D = C + f·(B − A) with f = 0.618 / 1.272 / 1.618 (harmonic "AB=CD extensions").
- **Breakout-bar measured move (Brooks).** Measure the breakout bar or bars (open-to-close, or low-to-high) and project it from the close or high. Stop: below the breakout bar's low.
  - Claimed probability: "about 60%" for a strong breakout, and higher with follow-through (Brooks forum and flashcard material, via search summary; one deck says 70%).
  - A strong breakout bar, in Brooks's words: a large trend bar, small tails, closing near its extreme, ideally beyond prior structure, often "two or more consecutive big trend bars". Brooks gives no numeric threshold; this study uses body ≥ m·ATR (m = 1, 1.5, 2), body/range ≥ 0.6, close in the outer 25% of the bar, close beyond the 20-bar extreme.
- **Follow-through bar.** The next bar is a trend bar in the same direction closing beyond the breakout close.
- **Measuring gap (Brooks).** The gap between the breakout point and the first pullback (an FVG in ICT language) often marks the middle of the move. Target = gap midpoint + (gap midpoint − leg origin).
- **Range-height measured move (Bulkowski "measure rule", Wyckoff "cause and effect").** Target = breakout edge ± range height.
- **Bulkowski measured move up (MMU).** First leg up, a corrective phase retracing part of it, then a second leg. His target formula is **corrective low + 60% of the first leg** (via search summary). He reports that deeper corrections make a full second leg more likely (31,000+ MMU samples; table not retrievable). "Percentage meeting price target: 60%" in bull markets refers to the 60% target, not the full leg.

### 1.3 Fibonacci extensions and ICT "standard deviation" projections
- **Classic extension of an impulse A→B.** Levels A + r·(B − A) for r = 1.272, 1.618, 2.0, 2.618; equivalently B + (r − 1)·(B − A).
- **ICT Fibonacci "SD" projections.** Fib tool anchored 1 at A and 0 at B; targets at −0.27, −0.62, −1, −2, −2.5, −4, i.e. B + g·(B − A).
  - Therefore **ICT −0.27 = classic 127.2%**, **−0.62 = 161.8%**, **−1 = 200%** and −2 = 300%.
  - Practitioner sources agree on the values but not on the anchor leg: the "manipulation leg", the displacement leg that broke structure, or the dealing range (backtrex, innercircletrader.net; via search summary). The CBDR/Asian-range "SD" version is covered in `ict_time.md` 1.8.
- **Pullback extension.** B + h·(B − C) for h = 0.272, 0.618, 1.0 (Elliott wave-3 / harmonic "BC projection").
- **Retracements (0.382 / 0.5 / 0.618 / 0.705 / 0.786, OTE).** These are entry locations, not targets; see ICTS 1.10 and the Tradeify evidence there (continuation odds fall monotonically with depth, with no bump at any Fibonacci level).

### 1.4 Elliott wave and harmonic heuristics
- **Elliott target rules (practitioner).**
  - Wave 3 = 1.618 × wave 1 from the wave-2 low.
  - Wave 5 = wave 1, or 0.618 × (waves 1-3).
  - Wave C = wave A (AB=CD).
  - Wave 2 retraces 0.5-0.618, wave 4 retraces 0.382.
  - Counts are subjective and re-labelled after the fact (Prechter's own vendor claims are unverifiable).
- **Harmonic patterns.** X-A-B-C-D with ratio windows. Examples:
  - Gartley: B = 0.618 XA, D = 0.786 XA, CD = 1.272-1.618 BC.
  - Bat: B 0.382-0.5, D 0.886 XA.
  - Butterfly: D = 1.272-1.618 XA.
  - Crab: D = 1.618 XA.
  - D is a reversal zone; targets are retracements of AD.
  - They are reversal-entry patterns built from the same Fibonacci ratios tested in T1.

### 1.5 Brooks bias and context concepts
- **Always In (AI).** "If you had to be in the market now, long or short?" It flips on a strong breakout: consecutive big trend bars closing beyond prior structure (via search summary). Algorithmic proxy used here: the sign of the most recent two-bar breakout (both bars body/range ≥ 0.5, combined body ≥ 2 ATR, closing beyond the prior 20-bar extreme), held for 100 bars.
- **Trading range vs trend.**
  - "80% of breakout attempts in a trading range fail" (Brooks, MoneyShow column, via search summary). Elsewhere he says the first strong breakout fails about 50% of the time.
  - A successful breakout "usually has at least two consecutive big trend bars closing beyond the range".
  - The range is "a magnet ... an area of agreement".
  - Algorithmic proxy: a close beyond the prior 20-bar high or low; range width in ATR; failure = a close back inside within 5 bars.
- **Breakout test / breakout pullback.** After a breakout, price returns to test the breakout point. Wyckoff tested throwbacks and found them at random-level rates (WYK §2.5: 0.870 vs 0.872).
- **Second entries (H1/H2, L1/L2).** In a bull trend's pullback, an "H" event is a bar whose high exceeds the prior bar's high. After H1 the pullback must make a lower low (a second leg) before H2 counts. Brooks: "High/Low 2 entries are the best", and a failed H2 means you are misreading the market.
  - Algorithm used here: trend context = close > EMA20 and EMA20 rising over 5 bars at the trend high; then H1 → new low below the H1 bar's low → H2. Entry = H2 bar close. Race: trend high traded through vs pullback low traded through.
- **20 gap bars / moving-average gap bar.** After ≥ 20 consecutive bars entirely beyond the EMA20, the first touch of the average is "a high-probability scalp for a test of the trend's extreme" (Brooks, *Trading Price Action: Trends* ch. 13). A forum estimate puts it at 70-75%.
- **Magnets (Brooks).** Prior highs and lows, yesterday's high, low and close, the open of the day, measured-move targets, the moving average, trend-channel lines, the breakout point, the middle of a trading range.
- **Final flag.** A late pause in a trend whose breakout fails; it is known only after the fact (no forecasting definition).
- **Traders' equation.** Probability × reward > (1 − probability) × risk. In the engine this is the R:R · WIN≤H · EV readout (`f_invalidation`, 1343-1364).

### 1.6 Dow theory
- **Primary trend.** Successive higher highs and higher lows (or lower lows and lower highs). A trend persists until a definite reversal signal: a failure to make a new high followed by a break of the prior low.
- **Phases.** Accumulation, public participation, distribution.
- **Confirmation.** Industrials and transports (two related averages) must confirm each other. The modern intraday analogue is SMT divergence, which needs a second symbol and is out of scope (ICT note).
- **Engine analogue.** `f_structure` (708-782): internal bias flips on a body close through the last swing; swing bias uses BOS / CHoCH with protected extremes.

### 1.7 Gap fill / prior close
- **Prior RTH close (PDC, ICT "opening range gap" ORG).** The previous regular-session close (16:00 ET for US index futures; ICT's ORG references the cash-session close).
- **Gap fill.** The current session trades back to that close.
- **Practitioner statistics.** Fill odds depend strongly on gap size and are front-loaded into the first 30-60 minutes (TradingView "Gap Fill Probability Statistics ES NQ", 2014-2024; via search summary). SPY large down-gaps fill completely only about 17% of the time (Market Chameleon, via search summary). ICTPD 2.3 gives further base rates (SPY 1%+ up-gaps fill same-day 26%).

### 1.8 Price discovery
- **Definition used here.** On the trend side (close vs EMA50) there is no unswept liquidity (pivot pool) within the engine's `maxATR` (10 ATR). This is the condition at all-time highs or lows and after a cascade has cleared all pools.
- **Practitioner targeting in that state.** Measured moves, Fibonacci extensions, round numbers, ATR/ADR projections. Siblings: round numbers OF-4 / ICT-3; ADR projections rejected by SESS (§2.7, sign reversed).

### 1.9 Leg-reach before a pullback (overshoot law), derived
For Brownian motion with zero drift, the maximum gain M* before a drawdown of δ from the running maximum is **Exponential with mean δ** (Taylor 1975; Lehoczky 1977; exponential for every δ iff μ/σ² is constant, Mayerhofer 2019). For a leg currently at running extreme M, price p, pullback so far u = side·(M − p) < δ, and a target T:
- **T beyond M** (y = side·(T − M) > 0): P(T before a δ pullback) = ((δ − u)/δ) · exp(−y/δ). The first factor is the race back to M; the second is the exponential law.
- **T between p and M**: a plain race against M − side·δ: P = (δ − u)/((δ − u) + side·(T − p)).

These hold for any continuous martingale for the race part (optional stopping) and for Brownian motion for the exponential part. T1 shows the exponential part holds on real data within about 2 pp.

---

## 2. Evidence

### 2.1 Published evidence (numbers and sources)

| # | Claim | Source | Numbers | Grade |
|---|---|---|---|---|
| L1 | Fibonacci or round-fraction ratios in trend lengths and durations | Batchelor & Ramyar (2006), "Magic Numbers in the Dow", City Univ. London; DJIA daily 1915-2003, block bootstrap of turning points | Ratio frequencies not different from chance; "the idea that round fractions and Fibonacci ratios occur in the Dow can be dismissed"; no evidence that markets reverse at 0.618 / 1.618 (via search summary) | strong (peer-reviewed working paper, rigorous null) |
| L2 | Fibonacci 1.618 extension as a target | MQL5 statistics blog (28 Sep 2026), 26,795 mechanical double bottoms/tops, DAX/FTSE/NQ/Dow 2015-26, 24-hour horizon | 1.618 hit **67% vs 71%** for a random walk at the same distance (t = −13.5); DAX 67 vs 71, FTSE 66 vs 70; no parameter search; no out-of-sample split (via search summary) | moderate |
| L3 | Fibonacci retracement depth | Tradeify (2026), ES/NQ daily + 3 stocks, 263 legs (via ICTS S10) | 64% of legs fully retraced first; continuation odds fall smoothly with depth; no bump at any Fibonacci level | weak (small n) |
| L4 | Fibonacci retracement trading system | Gurrib, Nourani & Bhaskaran (2022), *Financial Innovation*, energy stocks and crypto, daily 2017-20 | Beat buy-and-hold in a falling-oil sample; no random-level control | weak |
| L5 | DC overshoot ≈ threshold | Glattfelder, Dupuis & Olsen (2011), *Quantitative Finance* 11(4); 13 FX pairs, tick data Dec 2002-Dec 2007 | ⟨\|Δx_os\|⟩ ≈ Δx_dc (E ≈ 1.04, C ≈ 1.06); total move ≈ 2 Δx_dc (E ≈ 0.99, C ≈ 0.51); overshoot takes about 2× the time of the DC section; a Gaussian random walk shows the same averages; the paper derives the 2× via a binomial tree (Σ i·0.5^i → 2) | strong |
| L6 | Max before drawdown is exponential | Taylor (1975); Lehoczky (1977); Mayerhofer (2019) "Three essays on stopping" (arXiv 1909.13050) | Exponential law for BM with drift; exponential for all δ iff μ/σ² constant | strong (theory) |
| L7 | Intrinsic time as a memoryless hazard | Houweling (2025), arXiv 2511.14408 | The share of DCs among events stabilises near 1 − 1/e = 0.632 | weak (single author) |
| L8 | Dow theory timing | Brown, Goetzmann & Kumar (1998), *J. Finance* 53: 1311-1333 | Hamilton's calls 1902-29: high Sharpe, positive alpha; 110 right, 74 wrong; neural-net replication beat buy-and-hold by 4.4 pp/yr 1930-97 | strong (long horizon only) |
| L9 | Elliott wave forecasting | Hulbert Financial Digest via CXO Advisory | CXO guru accuracy for Prechter **21%** vs a 47% average; newsletter portfolio slightly below the market since 1980 (via search summary) | weak (no controlled test exists) |
| L10 | Harmonic patterns | HKUST student study (US stocks, FX, crypto); 2026 blog (ES 15m 2020-24, 7-29 trades/pattern); "researcher degrees of freedom" critique | Patterns rare, total profitability low; profit factor 1.37 on 29 trades; "70% success" claims not meaningful (via search summary) | none-weak |
| L11 | Brooks breakout measured move | Brooks Trading Course forum, flashcards, *Trading Price Action: Trends* ch. 2 | "about 60%" (one source 70%) for a strong breakout; higher with follow-through; volume 10-20× average raises follow-through (via search summary) | weak (no published test) |
| L12 | Brooks 80% rule | Brooks, MoneyShow column; Brooks forum | "80% of breakout attempts in a trading range will fail"; elsewhere "first breakout fails about 50% after 20 bars of range" (via search summary) | weak |
| L13 | Brooks 20-gap-bar | *Trading Price Action: Trends* ch. 13; forum | First MA touch after ≥ 20 gap bars → test of the trend extreme; forum estimate 70-75%; "nothing magical about 20" (via search summary) | weak |
| L14 | Bulkowski measured move up | thepatternsite.com/mmu.html, /measure.html, /MMRetrace.html | Target = corrective low + 60% of leg 1; 60% meet that target (bull market); larger retrace → second leg more often ≥ first (31,000+ samples). Third-party claims of 70% continuation and a second leg about 93% of the first are unverified (via search summary) | moderate (large n, no random baseline) |
| L15 | Range-height measured move | Bulkowski rectangles (WYK §1.8) | 79% / 55% meet target for up / down breakouts (daily stocks, bull markets) | moderate (no random baseline); geometry-level when tested (WYK §2.5) |
| L16 | Gap fill | TradingView ES/NQ gap statistics (2014-24); Market Chameleon SPY; ICTPD 2.3 | Fill odds size-dependent and front-loaded into the first 30-60 min; SPY large down-gaps fill fully about 17% (via search summary) | weak |
| L17 | S/R levels interrupt trends but do not attract | Osler (2000), Kavajecz & Odders-White (2004) (ACAD S1, S4) | Published levels stop trends 60.8% vs 56.2% for arbitrary levels | strong (sibling) |

### 2.2 This study

#### T1 · Leg ratios and overshoot (`t1_legs.py`; outputs `out_t1_<set>_k<k>.txt`)

Bump index = n(ratio within ±3% of f) / (½ · n(flanking bins f·[0.91, 0.97) ∪ (1.03, 1.09])). It is about 1 with no clustering; the Poisson SE at these counts is about 0.06-0.08.

| Set, k | legs | P(E≥1) real / null | P(E≥1.618) | Fib bumps, E (projection) | Fib bumps, R (retracement) | Placebo range |
|---|---|---|---|---|---|---|
| 1h, 2 | 14,873 | 0.490 / 0.491 | 0.222 | 1.0: 0.97 · 1.272: 0.95 · 1.618: 1.01 · 2.0: 0.99 | 0.382: 0.99 · 0.5: 0.99 · 0.618: 0.95 · 0.786: 0.99 | 0.87-1.13 |
| 1h, 3 | 7,029 | 0.490 / 0.496 | 0.236 | 1.0: 1.02 · 1.272: 0.88 · 1.618: 0.91 · 2.0: 1.13 | 0.618: 0.94 | 0.85-1.23 |
| 5m, 2 | 10,524 | 0.498 / 0.498 | 0.233 | 1.0: 0.94 · 1.272: 0.92 · 1.618: 1.11 · 2.0: 0.99 | 0.618: 1.02 · 0.786: 1.11 | 0.88-1.15 |
| 5m, 3 | 5,032 | 0.503 / 0.503 | 0.265 | 1.0: 0.85 · 1.272: 0.96 · 1.618: 1.05 | 0.618: 0.87 | 0.85-1.16 |
| D, 2 | 1,401 | 0.496 / 0.492 | 0.228 | 1.0: 0.90 · 1.618: 0.97 | 0.618: 0.83 | 0.61-1.28 (small n) |

The shuffled null shows the same dispersion: 1h k = 2, E 1.0: 1.03, 1.272: 1.04, 1.618: 0.97; R 0.618: 1.13. **No Fibonacci ratio stands out in any cell.**

**Overshoot after a directional change** (OS/δ). The Brownian-motion Exp(1) reference is mean 1.000, median 0.693, P(≥ 0.5) 0.607, P(≥ 1) 0.368, P(≥ 2) 0.135.

| Set, k | mean | median | P≥0.5 | P≥1 | P≥2 | corr(log prev same-dir leg, OS) | P(OS≥1) prev-leg low / high tercile |
|---|---|---|---|---|---|---|---|
| 1h, 2 | 1.055 | 0.667 | 0.596 | 0.356 | 0.146 | +0.009 | 0.354 / 0.354 |
| 1h, 3 | 1.051 | 0.625 | 0.571 | 0.339 | 0.139 | −0.003 | 0.339 / 0.332 |
| 5m, 2 | 1.095 | 0.711 | 0.619 | 0.380 | 0.146 | +0.009 | 0.378 / 0.389 |
| 5m, 3 | 1.080 | 0.658 | 0.594 | 0.352 | 0.149 | +0.002 | 0.338 / 0.343 |
| D, 2 | 1.078 | 0.738 | 0.630 | 0.391 | 0.151 | −0.034 | 0.418 / 0.383 |
| D, 3 | 1.038 | 0.680 | 0.600 | 0.380 | 0.160 | +0.026 | 0.390 / 0.385 |

- Successive overshoots are uncorrelated: −0.07 to +0.02.
- **Conclusion.** A confirmed leg's remaining extension is Exp(δ), with slightly fat tails (P ≥ 2δ is 0.14-0.16 vs 0.135). The size of the previous leg, the core input of every measured-move rule, carries no information. "How far will this leg go" has an honest closed-form answer (1.9) and no pattern-based answer.

#### T2 · Projection levels as DOL candidates (`t2_proj.py`; outputs `out_t2_*.txt`)

- **Setup.** Event = zigzag pivot C confirmed with A < C < B (bull; mirror for bear). Entry at the confirmation close. hit = touched within K bars; base = the engine-style random-level probability at the same ATR distance.
- **Edge SE.** The SE is clustered in 2K-bar blocks: about 0.005-0.007 intraday and 0.012-0.017 daily.
- **React.** React = P(price goes 1 ATR beyond the touched level before coming back 1 ATR); a martingale gives 0.5.

| Level | 1h k2 K30: dist / hit / base / **edge** / react | 1h k3 K30 edge | 5m k2 K30 edge / react | D k2 K10 edge |
|---|---|---|---|---|
| B (prior swing, the engine's pool) | 1.15 / 0.684 / 0.700 / **−0.015** / 0.527 | +0.001 | +0.003 / 0.528 | +0.022 |
| MM 0.618 | 1.36 / 0.653 / 0.657 / **−0.003** / 0.506 | +0.003 | +0.013 / 0.497 | −0.004 |
| MM 0.9 | 2.37 / 0.502 / 0.497 / **+0.005** / 0.501 | +0.023 | +0.019 / 0.490 | +0.029 |
| **MM 1.0 (AB=CD)** | 2.76 / 0.451 / 0.448 / **+0.004** / 0.486 | +0.018 | +0.027 / 0.468 | +0.025 |
| MM 1.1 | 3.18 / 0.408 / 0.401 / **+0.008** / 0.483 | +0.017 | +0.022 / 0.472 | +0.028 |
| MM 1.272 | 3.93 / 0.338 / 0.330 / **+0.007** / 0.490 | +0.008 | +0.021 / 0.498 | +0.033 |
| MM 1.618 | 5.49 / 0.226 / 0.223 / **+0.003** / 0.500 | +0.006 | +0.018 / 0.497 | +0.011 |
| MM 2.0 | 7.24 / 0.150 / 0.145 / **+0.005** / 0.491 | +0.009 | +0.019 / 0.487 | −0.001 |
| EXT −0.27 (127.2%) | 2.30 / 0.506 / 0.510 / **−0.005** / 0.493 | +0.015 | +0.022 / 0.481 | +0.031 |
| EXT −0.62 (161.8%) | 3.90 / 0.330 / 0.323 / **+0.007** / 0.493 | +0.010 | +0.021 / 0.492 | +0.028 |
| EXT −1 (200%) | 5.63 / 0.206 / 0.201 / **+0.005** / 0.492 | +0.011 | +0.022 / 0.476 | −0.001 |
| EXT −2 (300%) | 10.30 / 0.071 / 0.066 / **+0.006** / 0.519 | +0.005 | +0.009 / 0.519 | +0.008 |
| BCX 127.2% | 1.76 / 0.586 / 0.586 / **−0.000** / 0.485 | +0.021 | +0.017 / 0.478 | +0.042 |
| BCX 161.8% | 2.66 / 0.448 / 0.451 / **−0.003** / 0.501 | +0.006 | +0.014 / 0.485 | +0.027 |

- About 7,600 events (1h k2), 3,700 (1h k3), 5,300 (5m) and 690 (daily).
- **Reading.**
  - Every projection behaves like a random level at its distance. The small positive edges on 5m, 1h k3 and daily are the same at every ratio (MM 0.8 to 2.0 and all EXT levels), so they come from the event, not the level.
  - The event is a fresh k·ATR reversal, after which realised volatility runs above ATR (vol clustering; QPOT-03 / REG-1 key the surface on vol state for this reason).
  - There is no stall at the measured move: react 0.47-0.50 vs placebo ratios 0.47-0.50.
  - The engine's own swing pool B is also reached at random-level rates: −1.5 to +2.2 pp, as WYK and ICTPD found for other level families.

#### T3 · Brooks claims (`t3_brooks.py`; outputs `out_t3_*.txt`, with shuffled nulls)

Race = target touched before a trade-through of the stop, horizon 4K bars; geometry = (entry − stop)/(target − stop). "diff" = win − geometry (SE ≈ 0.008-0.02).

| Setup | 1h: n / win / geom / **diff** | 5m: n / win / geom / **diff** | D: diff | null 1h / 5m diff |
|---|---|---|---|---|
| 1 bar, body ≥ 1 ATR, MM open→close | 4,419 / 0.521 / 0.524 / **−0.003** | 3,394 / 0.538 / 0.523 / **+0.015** | −0.002 | +0.007 / +0.001 |
| … + follow-through bar | 1,481 / **0.664** / 0.663 / **+0.000** | 1,179 / **0.662** / 0.679 / **−0.017** | +0.003 | +0.005 / +0.005 |
| 1 bar, body ≥ 1.5 ATR, MM o→c | 2,752 / 0.524 / 0.520 / **+0.004** | 1,534 / 0.546 / 0.519 / **+0.026** | +0.023 | +0.003 / +0.003 |
| 1 bar, body ≥ 2 ATR, MM o→c | 1,608 / 0.542 / 0.517 / **+0.025** | 740 / 0.551 / 0.518 / **+0.034** | −0.034 (n 61) | −0.006 / +0.002 |
| 1 bar, body ≥ 2 ATR, MM low→high | 1,589 / 0.478 / 0.452 / **+0.027** | 728 / 0.497 / 0.456 / **+0.041** | −0.023 | −0.005 / −0.004 |
| 2 consecutive trend bars (Σbody ≥ 2 ATR) | 2,082 / 0.535 / 0.514 / **+0.021** | 1,501 / 0.528 / 0.514 / **+0.013** | +0.021 | −0.012 / +0.004 |
| H2 / L2 (trend high vs pullback low) | 451 / 0.379 / 0.391 / **−0.011** | 231 / 0.420 / 0.382 / **+0.038** | +0.019 | +0.043 / −0.043 |
| 20-gap-bar 1st EMA touch: hit ≤ K vs random level | 1,028: 0.483 vs 0.497 (**−0.014**) | 781: 0.524 vs 0.511 (**+0.013**) | 120: 0.383 vs 0.318 (+0.065 ± 0.040) | +0.010 / −0.004 |

- **Per-series sign check, body ≥ 2 ATR.**
  - 1h: ES −5.0, NQ −8.4, RTY +0.1, YM +4.4, GC +4.8, CL −0.3, BTC +4.2 (n = 976 of 1,608), EU17 +4.7, EU25 +1.5 pp.
  - 5m: ES +6.8, NQ +9.1, RTY +7.4, YM +0.3, GC −1.0, CL −4.0 pp.
- **Conclusions.**
  - Brooks's "60%" is reproduced only with a follow-through bar, and geometry predicts that same 60-67% because follow-through moves the entry.
  - The only residual is a small, inconsistent continuation after very large breakout bars. **Grade: weak.**
  - H2 and the 20-gap-bar rule add nothing measurable intraday.

#### T4 · Trading range, Always In, measuring gap, time symmetry (`t4_misc.py`; outputs `out_t4_*.txt`)

| Test | 1h | 5m | D | Shuffled null (1h / 5m) |
|---|---|---|---|---|
| (1) close back inside within 5 bars after a 20-bar-range breakout by close: narrow (≤ 4 ATR) / mid (4-8) / wide | 0.531 / 0.551 / 0.624 | 0.580 / 0.568 / 0.552 | 0.564 / 0.607 / 0.636 | 0.501 / 0.501 / 0.484 · 0.532 / 0.509 / 0.525 |
| (1b) range-height MM before the opposite edge, minus geometry (mid ranges) | +0.026 (n 6,306) | +0.031 (n 5,665) | +0.027 (n 832) | −0.008 / +0.005 |
| (1b) same, narrow ranges | −0.028 | −0.009 | −0.031 | −0.028 / −0.025 (detector artefact; real − null ≈ 0 / +0.016) |
| (2) Always-In side's nearest pool (0.25-4 ATR) taken first, minus geometry | **+0.002 ± 0.005** (n 10,169) | **+0.001 ± 0.006** (n 7,032) | −0.013 ± 0.020 | −0.000 / −0.020 |
| (3) measuring-gap target (2·FVG mid − origin) hit ≤ K, minus random level | −0.000 ± 0.006 | +0.034 ± 0.007 | +0.038 ± 0.017 | −0.012 / −0.008 |
| (3) race to that target vs the FVG's far edge, minus geometry | +0.017 | +0.016 | +0.018 | +0.006 / +0.012 |
| (4) AB=CD time symmetry: Spearman(bars A→B, bars C→D) | +0.241 | +0.315 | +0.424 | **+0.285 / +0.286** |

- Breakout events overlap (consecutive closes beyond the range), so SEs are understated by up to about 2×.
- **Reading.**
  - (1) Brooks's 80% is about 55-60%, but that is above the null's 50%. The "range-height MM" effect (+3 pp) is small and matches WYK.
  - (2) **Always In has no side information.**
  - (3) The 5m measuring-gap edge is most likely the time-of-day confound: displacement FVGs cluster at the open, while the unconditional baseline averages quiet hours (QPOT §4 reports 24× variance max/min on ES 5m).
  - (4) Time symmetry is fully reproduced by the shuffled null, so it carries no ETA information.

#### T5 · Prior RTH close / gap fill (`t5_pdc.py`; outputs `out_t5_pdc_K6.txt`, `out_t5_pdc_K30.txt`)

- **Setup.** CME ES, NQ, RTY, YM, GC, CL 1h. Level = close of the 15:00-16:00 ET bar. A sample is live from the close of the 09:00-10:00 ET bar if no bar from 09:00 on touched the level; it continues until the 15:00 bar.
- **Baselines.** "base" = unconditional random level; "baseH" = random level estimated only from start bars at the same ET hour.

| Sample | n | median dist (ATR) | hit | base | baseH | **edge vs baseH** |
|---|---|---|---|---|---|---|
| 10:00 ET, one per day, K = 6 (rest of session) | 968 | 2.22 | 0.381 | 0.254 | 0.347 | **+0.034 ± 0.013** |
| 10:00 ET, K = 30 | 968 | 2.22 | 0.603 | 0.545 | 0.568 | **+0.035 ± 0.014** |
| all live RTH bars, K = 6 | 5,210 | 2.70 | 0.245 | 0.215 | 0.223 | +0.022 ± 0.005 |
| all live RTH bars, K = 30 | 5,179 | 2.69 | 0.511 | 0.494 | 0.478 | +0.034 ± 0.006 |
| distance 1-2 ATR, K = 6 / K = 30 | 1,178 | 1.50 | 0.413 / 0.744 | — | 0.364 / 0.672 | +0.048 / +0.071 |
| distance 0-0.5 ATR, K = 6 | 184 | 0.35 | 0.707 | — | 0.759 | −0.053 ± 0.031 |

- The six instruments are correlated (four equity indices), so the effective n is roughly half.
- **Grade: weak-moderate.** One year, one market family. The direction agrees with Brooks's "yesterday's close" magnet and ICT's ORG.
- **Method lesson.** Against the all-hours baseline the 10:00 edge looks like +12.7 pp. Any gap-fill or session-level statistic must use a clock-matched baseline (TIME-2).

#### T6 · How often is the draw side blind (`t6_blind.py`; outputs `out_t6_*.txt`)
- Unswept 5-bar pivot pools within 10 ATR:
  - **no pool above** on 5.0% (1h), 4.4% (5m), 11.5% (D) of bars;
  - **no pool below** on 1.6%, 3.9%, 5.1%;
  - blind on the EMA50-trend side on 5.0%, 5.8%, 13.7%.
- The K-bar excursion toward the blind trend side (1h, K = 30) has median 2.46 ATR, P(≥ 2 ATR) = 0.578, P(≥ 3) = 0.424. That is about 2-3 pp above the unconditional rate: no special drift in price discovery, so a distance-based PoT is honest there.

### 2.3 Evidence summary for the engine
- **Projection geometry (Fibonacci, AB=CD, ICT SD, Elliott and harmonic ratios).** No level-specific effect. **Grade: strong** (L1, L2, T1, T2 across 18 series).
- **Overshoot law.** Leg extension ≈ Exp(δ), with no memory of the previous leg. **Grade: strong** (L5, L6, T1).
- **Brooks probabilities.** They are geometry; large-bar continuation is weak; Always In, H2 and 20-gap-bar carry no information. **Grade: moderate** (T3, T4: this study's nulls, large n, three timeframes).
- **Prior RTH close.** +3.5 pp over a clock-matched random level. **Grade: weak-moderate** (T5).
- **Price discovery.** 5-14% of bars have no draw-side pool. **Grade: moderate** (T6).

---

## 3. Engine gap analysis (`baseline_v2.pine`)

| Concept | Status | Lines | What the engine does / what differs |
|---|---|---|---|
| Liquidity magnets: prior swing highs/lows | present | 1753-1776 (chart pivots), 1779-1789 (STF/HTF registry) | Brooks's "prior highs/lows are magnets". Reached at random-level rates (T2 row B; WYK). Fine as the DOL universe |
| Magnets: PDH/PDL, PWH/PWL | present | 944-961, 1790-1799 | Brooks "yesterday's high/low" |
| Magnet: prior RTH close (gap fill / ICT ORG) | **missing** | — | No PDC level. ICTPD-6 proposes opening gaps via a time-break detector, which on 23-hour CME ETH charts only sees the 17:00-18:00 halt (NDOG), never the 16:00 → 09:30 RTH gap. Docs: "For futures, the 'Electronic trading hours' session *is* the regular session" (`concepts/sessions.md`, `session.isfirstbar_regular`). T5: +3.5 pp over a clock-matched baseline → PA-2 |
| Magnet: open of the day | partial | 964-966, 1931 | Midnight / London / NY opens are confluence anchors only (TIME-6 proposes the midnight open as a target) |
| Magnet: middle of the trading range | present (as confluence) | 967-968 (`dayEQ`, `htfEQ`), 1931 | Brooks's "middle of the range". As a scored target it is not supported (TR edges and mids reached at random rates; WYK) |
| Magnet: moving average / 20-gap-bar | missing (correct) | — | A moving target by construction. T3: first EMA touch → extreme retest at random-level rate. Do not add |
| Measured move / AB=CD / leg 1 = leg 2 | missing | — | Correct as a scored source (T2: random-level rate, no stall). Missing as a **price-discovery fallback** (T6) → PA-1 |
| Fibonacci extensions / ICT SD projections | missing (correct) | — | T1/T2, L1/L2: no level effect; 1.618 reached *less* than a random walk in L2. Do not add as targets or confluence anchors (`anchors`, 1931) |
| Fibonacci retracements / OTE | missing (correct) | — | Entry concept; ICTS 1.10 |
| Elliott / harmonic targets | missing (correct) | — | No evidence (L9, L10); ratios rejected by T1 |
| Breakout-bar measured move (Brooks 60%) | n/a | — | Geometry (T3). Nothing to add as a level |
| Displacement / strong breakout as a draw vote | partial | 897-904 (`dispUp/dispDn`, `twoLeg`), 1536-1541, 1893 (`mV`, weight `wM` 0.20) | Threshold 1.2 ATR body (or two-leg Σ ≥ 1.8 ATR), no requirement to close beyond prior structure or near the bar's extreme. T3: at ≥ 1 and ≥ 1.5 ATR the continuation is geometry (0 to +1.5 pp); only ≥ 2 ATR range-breaking bars show +2.5 to +3.4 pp, inconsistently. The engine's vote fires mostly in the no-information zone → PA-4 |
| Follow-through bar | missing (correct) | — | Adds geometry only (T3) |
| Failed breakouts / Brooks 80% rule | partial / **wrong sign of certainty** | 1580-1582 (`liqEvt`: close beyond = hold = continuation; close back = reversal) | T4: breakouts by close come back inside within 5 bars 53-62% (null 48-53%), so a single close beyond is weak evidence of "hold". The rule is unreliable in both directions (REG finding 7, BIAS-4, ICTS-2 own the fix) |
| Trading range vs trend regime | missing | — | Brooks's central context. Sibling WYK-3 / REG-2 cover it; regime labels do not persist (REG finding 1) |
| Always In direction | partial | 1891-1895 (`drawD` from structure, displacement, raids; `dirSide` gate 1975) | D is an always-in-like vote. T4: the Always-In proxy has zero side information (+0.2 ± 0.5 pp), corroborating REG-3 / ICTS-1 (gate or measure D) |
| Second entries H2/L2 | missing (correct) | — | T3: geometry |
| Breakout test / throwback to the breakout point | missing (correct) | — | WYK §2.5: random-level rate |
| Measuring gap (FVG-midpoint projection) | missing (correct) | — | T4: random-level rate on 1h. The 5m uplift is a clock confound. FVGs themselves are present (1868-1887) |
| Range-height measured move | missing (correct as a level) | — | T4 (1b) and WYK: +3 pp race effect; not a level effect |
| Dow theory trend (HH/HL, BOS, CHoCH) | present | 708-782 (`f_structure`), 923-931 | A sound implementation. Long-horizon evidence only (L8); intraday side selection is a coin flip (ICTS §2.2) |
| Dow "confirmation" (two averages) | missing | — | SMT; needs a second symbol (ICT note); out of scope |
| How far will the leg go (reach) | present (good) | 1059-1062, 1265-1336 (`f_bump`, `f_surv`, `f_empPoT`, `f_reachD`), 1338-1339 (reach class), 2102-2115, 2192-2199 (reach bands) | The empirical H-bar excursion surface is the right tool and better than measured-move heuristics (T1: leg size carries no information, so no leg conditioning is needed). It is keyed on HTF bias; QPOT-03 / REG-1 propose a vol-state key |
| Leg reach before a pullback (overshoot law) | **missing** | — | No readout answers "will this leg get there without a k-ATR pullback?" Closed form (1.9), validated by T1 → PA-3 |
| Traders' equation / R:R race | present | 1343-1364 (`f_invalidation`, `f_raceH`), HUD 2236-2245 | WIN≤H vs the opposing pool. Races are martingale races (QPOT finding 6); drift adds noise (QPOT-01) |
| Time projection (leg 2 lasts as long as leg 1) | missing (correct) | — | T4: the null reproduces the correlation. ETA belongs to vol-time (QPOT-05, TIME-4) |
| Price-discovery targets | **missing** | 1964-2005 (selection: `useCtr` when no draw-side level qualifies) | At new highs with D up there is no buy-side candidate, so the engine shows a counter-draw SSL or nothing. T6: 5-14% of bars → PA-1 |

---

## 4. Proposals (spec-level, best first)

Shared building block for PA-1, PA-3 and PA-5: an **O(1) ATR zigzag** on confirmed bars. It is the detector every test in this study used. Place the state in STATE (after 1050) and the update in ENGINE step 9 (after 1776):

```pine
// STATE
var int          zzMode = 0          // +1 tracking a high, -1 tracking a low
var float        zzExt  = na         // running extreme of the current leg
var int          zzExtB = na
var float        zzOpp  = na         // opposite extreme since zzExt was set
var int          zzOppB = na
var array<float> zzPx   = array.new<float>()   // last confirmed pivots, oldest first (max 3)
var array<int>   zzTy   = array.new<int>()     // +1 high · -1 low
// INPUT (G_LIQ)
float zzK = input.float(2.0, "Leg Size (ATR)", minval = 0.5, step = 0.25, group = G_LIQ,
  tooltip = "A leg ends when price retraces this many ATR from its extreme. Used for projection targets and the leg-reach readout.")

// ENGINE step 9b (confirmed bars, every bar, not only inCalc)
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
            zzMode := 1
            zzExt  := zzOpp
            zzExtB := zzOppB
            zzOpp  := na
while zzPx.size() > 3
    zzPx.shift()
    zzTy.shift()
```

- A bar that sets a new extreme never confirms, matching `palib.zigzag`.
- Cost: a few float operations per bar, no loops. It is non-repainting (confirmed bars only).

### PA-1 (P1, M) · Price-discovery projection targets: an honest fallback when the draw side has no liquidity

**Problem.**
- At new highs or lows (5.0% of hourly, 5.8% of 5-minute and 13.7% of daily bars on the trend side, T6) the pool holds no draw-side level within `maxATR`.
- Selection (1999-2005) then takes `useCtr` and shows a `⚠ COUNTER-DRAW` sell-side target while price trends up, or shows nothing.
- That is a prime candidate for the user's "targets look wrong".

**Why projections are legitimate here.** They are reached at random-level rates (T2: −0.5 to +2.7 pp, flat across ratios; L2), so the engine's existing PoT is already calibrated for them. They give the trader a named, conventional objective (measured move / ICT −1 SD) without claiming an edge.

**Algorithm.**
1. **Ladder** from the zigzag, bull case. When `zzTy` = [−1, +1, −1] (A low, B high, C low), `zzMode == 1`, and A < C < B:
   - `MM1 = C + (B − A)` (AB=CD, Brooks "leg 1 = leg 2");
   - `EX1 = B + (B − A)` (ICT −1 SD = 200% extension);
   - `MM16 = C + 1.618·(B − A)`.
   - Bear case mirrored.
2. **Pick the rung:** the nearest ladder price ≥ `close + minDistATR·atr` on the draw side. All rungs are equivalent in evidence; the nearest has the highest PoT.
3. **Activation** (new step 16b, before step 17 scoring, inside `inCalc`): `useProj and dirSide != 0`, and no level of kinds 0-7 on `dirSide` with `0 <= lv.distance(close) <= maxATR*atr`. Compute that flag with one pass over `pool`.
4. **Level.**
   - New kinds: 8 = projection above (side +1), 9 = projection below (side −1).
   - `src` = 8 (MM 1.0), 9 (EXT 1.0), 10 (MM 1.618).
   - Zone: thin, `[MM, MM + wPx]` above or `[MM − wPx, MM]` below.
   - `qual = 0.5`, `coil = induce = 0`.
   - At most one per side: update its price in place when the rung changes (if it is in `openT`, move `t.edge` as `f_mergeAt` does, 1124-1126).
   - Delete it (with a `⊘ REPLACED` ghost if it was active) as soon as real draw-side liquidity appears within `maxATR`.
5. **Code touch points.**
   - `f_newLevel` side map (1085): add `or kind == 8`.
   - `isArray()` (629) stays `kind >= 2`, so `touched` (623-624) uses touch semantics: a projection is not liquidity, consistent with the decision history.
   - Step 3 partial fill (1566): add `and lv.kind <= 7`.
   - Origin lockout (689): not triggered (`src != 0`).
   - `evaluate` non-liquidity branch (686-690): no change needed.
   - `grp()` (636): `kind >= 8 ? 4 : …`. Ledger arrays grow from 5 to 6 with ALL moved to index 5: `stN/stK/stBars/stPE/stPV/stMae` (1066-1071), `f_calMult` (1380-1381), `f_book` (1470: `array.from(t.grp, 5)`), panel reads (2375-2443), `f_grpName` (543-549: 4 → "PROJ"). Minimal alternative: count PROJ in family 1 plus a 3-float `projSt` counter.
   - `f_tierW` (506-516): src 8-10 → 0.20.
   - `f_levelName` / `f_shortName` (518-541): kinds 8/9 → "MM 1.0" / "EXT 1.0" / "MM 1.618" by src.
   - `f_kzAff` default 1.0.
   - Step 18 trimming keeps it via `src >= 1`.
   - Stacks and the registry ignore kinds ≥ 2.
6. **Label tooltip (Clean).** "Projection, not liquidity: on this symbol price reaches it like a random level at this distance." The Terminal HUD tag is `PROJ`.

**Ledger.** Family PROJ hit rate vs `pBase`. The expected edge is ≈ 0: the value is **coverage** (COMP-6's coverage metric rises) and calibrated PoT in the blind state, not edge. If PROJ shows a negative edge on a chart, `f_calMult` (or CAL-1) damps it automatically.

**Value.** The engine always has an honest draw-side objective in trends at new extremes, instead of a contradictory counter-draw target.

**Evidence.** Moderate: T2 (about 17,000 intraday events + 690 daily), T6, L1, L2.

**Risk.**
- Users may over-read Fibonacci or measured-move labels as "magic". The tooltip states the measured rate.
- The rung changes when a new pivot confirms (at most once per leg). The existing hysteresis and the two-bar challenger rule (2012-2018) prevent flicker.
- If a sibling replaces D-first selection with geometry-first (REG-3), the activation test should use the trend side (close vs EMA50, or the efficiency direction) instead of `dirSide`.

**Effort.** M (about 60 lines, plus the ledger array resize).

### PA-2 (P2, S) · Prior RTH close ("ORG" / gap-fill level) captured by session time, for futures and stocks

**Problem.**
- Brooks's "yesterday's close" magnet and ICT's opening range gap are missing.
- ICTPD-6's time-break detector cannot see the RTH gap on default 23-hour CME ETH charts, because TradingView treats ETH as the regular session for futures: "For futures, the 'Electronic trading hours' session *is* the regular session" (`docsrc/.../concepts/sessions.md`, `session.isfirstbar_regular` row). So `session.islastbar_regular` marks 17:00 ET, not 16:00.

**Inputs (G_KEY).**
```pine
bool   useRTHC = input.bool(true, "Prior RTH Close (gap fill)", group = G_KEY,
  tooltip = "Previous regular-session close as a target from the next RTH open (futures, stocks, indices). Uses the RTH session below, so it works on 23-hour futures charts.")
string sessRTH = input.session("0930-1600", "RTH Session", group = G_KEY)
```

**Series (SERIES section, global scope, next to 948-950).**
```pine
f_rthClose(string sess, string zone) =>
    bool inS = not na(time(timeframe.period, sess, zone))
    var float c  = na
    var int   cb = na
    if inS[1] and not inS
        c  := close[1]
        cb := bar_index - 1
    [inS and not inS[1], c, cb]
[rthOpen, rthC, rthCB] = f_rthClose(sessRTH, tz)
bool rthOK = useRTHC and intraOK and (syminfo.type == "futures" or syminfo.type == "stock" or syminfo.type == "index" or syminfo.type == "fund" or syminfo.type == "dr")
```

**Engine (step 10, after 1809).**
```pine
if rthOK and rthOpen and not na(rthC) and not (low <= rthC and high >= rthC)
    // replace yesterday's entry, then register today's (guard: `for i = -1 to 0` would run on an empty array)
    if extReg.size() > 0
        for i = extReg.size() - 1 to 0
            if extReg.get(i).src == 8
                extReg.remove(i)
    regNew := f_pushExt(extReg, rthC, rthC > close, 8, rthCB, math.abs(open - rthC) / atr, 1.0) or regNew
```
- `src` 8 needs `f_tierW` (0.55, like the session pools) and names `"RTH C"`. If PA-1 lands too, renumber PA-1's src to 9-11.
- The registry already drops it on trade-through (step 4, 1592-1596).
- Gap fill is a touch: a touch without trade-through leaves it live, which is acceptable and conservative.
- `syminfo.type` values per `reference/syminfo.md`: "stock", "fund", "dr", "index", "futures", ….

**Ledger.** Family 1 (EXT LIQ) by default. SESS-3's learned key-level multiplier, or a src split, tests it per chart; the clock-matched baseline of TIME-2 is required (T5 shows the naive baseline overstates the edge about 3×).

**Value.** Adds the one Brooks magnet with measurable support: +3.4 ± 1.3 pp at 10:00 ET over a clock-matched random level, n = 968 instrument-days.

**Evidence.** Weak-moderate (T5; L16; Brooks; ICT ORG).

**Risk.**
- Symbols whose RTH differs from 09:30-16:00 ET (CL, GC pits, non-US indices) need the input changed.
- Crypto and FX are excluded by the type guard.
- If ICTPD-6 is implemented, keep both: NDOG = the 17:00 → 18:00 gap; ORG = this level, 16:00 → 09:30.

**Effort.** S (about 25 lines).

### PA-3 (P2, S) · Leg-reach probability: "reaches the target before a k-ATR pullback", graded by the ledger

**Why.**
- This is the question measured-move, Elliott and Brooks traders actually ask ("will this leg get there?"). The honest, validated answer is the overshoot law (1.9): P(OS ≥ x·δ) = e^(−x), with the measured values in T1 within about 2 pp across 18 series.
- The engine's PoT answers a different question (touch within H bars, ignoring pullbacks). The two together tell the trader whether a target needs a pullback first.

**Function (PURE HELPERS).**
```pine
// P(target before a pullback of dl from the leg's running extreme M); price p; side +1 = up-leg.
f_legReach(float tgt, int side, float M, float p, float dl) =>
    float u = math.max(0.0, side * (M - p))
    float q = math.max(0.0, dl - u)
    float y = side * (tgt - M)
    float r = na
    if dl > 0
        r := y > 0 ? (q / dl) * math.exp(-y / dl) : q / math.max(q + side * (tgt - p), 1e-9)
    r
```

**Use.**
- When `zzMode == activeLv.side` (the leg points at the target), call `pLeg = f_legReach(activeLv.nearEdge(), activeLv.side, zzExt, close, zzK * atr)`.
- Otherwise the leg toward the target has not started, and the readout shows "—".
- Terminal HUD (after the PoT row, 2238): `LEG   41% before a 2.0-ATR pullback`. Clean: add it to the label tooltip only.

**Ledger.**
- Add to `Trial`: `float pLeg = na`, `float lgExt = na`, `float lgDl = na`, `int lgY = -1`.
- `f_step` (1434), while `lgY == -1`: update `lgExt` with the favourable extreme. `lgY := 1` on hit; `lgY := 0` when `side*(lgExt - (side>0 ? low : high)) >= lgDl` first. Use the existing O-L-H-C path rule (1441) for the same-bar order.
- `f_book`: accumulate `[n, Σp, Σy, Σ(p−y)²]` in a 4-float `legSt`.
- Terminal accuracy row: `LEG  pred 41% · obs 39% · Brier 0.21 (n 87)`.

**Value.** A calibrated "will this leg reach it" answer, with its own reliability check, replacing measured-move folklore. It also shows users that leg-size rules do not predict.

**Evidence.** Strong (L5, L6; T1, 6 cells, about 39,000 legs).

**Risk.**
- The exponential factor assumes zero drift. Keep drift out, consistent with QPOT-01.
- Fat tails make P(≥ 2δ) about 1-2 pp higher than e⁻². The ledger will show whether that matters per chart.
- Under REG-1, δ could be taken from the vol-state ATR.

**Effort.** S (about 30 lines; reuses the zigzag).

### PA-4 (P3, S) · Displacement vote in D = Brooks-strength breakout only

**Problem.** `dispUp/dispDn` (902-904) fire on a 1.2-ATR body (or a two-leg Σ ≥ 1.8 ATR) with no requirement to close near the extreme or beyond prior structure. T3 shows that bars of this size carry no continuation beyond geometry (−0.3 ± 0.8 pp at ≥ 1 ATR on 1h, +0.4 at ≥ 1.5). Only range-breaking bars of ≥ 2 ATR show a residual (+2.5 to +3.4 pp, inconsistent).

**Spec.**
```pine
float brkMult = input.float(2.0, "D · Breakout Body (x ATR)", minval = 0.5, step = 0.25, group = G_FLOW,
  tooltip = "Displacement votes in the draw vector only for a range-breaking trend bar: body >= this x ATR, closing in its outer quarter, beyond the prior 20-bar extreme.")
float hh20p = ta.highest(high, 20)[1]
float ll20p = ta.lowest(low, 20)[1]
bool  brkUp = close > open and bodyB >= brkMult * atrP and bRat >= 0.6 and close >= high - 0.25 * rngB and close > hh20p
bool  brkDn = close < open and bodyB >= brkMult * atrP and bRat >= 0.6 and close <= low + 0.25 * rngB and close < ll20p
```
- Replace `dispUp/dispDn` with `brkUp/brkDn` in step 1 (1536-1541).
- Keep `dispMult` for FVG quality (912), where it is used separately.
- Optionally lower the default `wM` from 0.20 to 0.10.

**Measurement.** ICTS-1's draw-skill gate or REG-3's efficiency gate measures D's side skill. A/B on the ledger: `drawFlip` count and edge by D component.

**Value.** Fewer spurious D flips from mid-size candles; D's displacement term then fires only where the data show any residual.

**Evidence.** Weak (T3, with per-series inconsistency).

**Risk.** Fewer displacement events. If REG-3 gates D anyway, this is a small refinement.

**Effort.** S.

### PA-5 (P3, S/M) · Measured-move shadow baselines and breakout-context features for the candidate ledger

**Why.** Users trained on Brooks, Bulkowski or ICT will ask "does the engine beat just aiming at the measured move?" The engine's random-level baseline answers "better than chance?" but not "better than the rule I already use?". COMP-3 proposes shadow selectors; add the projection rules to them. The small T3/T4 effects (0 to +3 pp) belong in a learner with zero prior weight, not in hand-set multipliers.

**Spec.**
1. **Shadow selectors** (COMP-3 infrastructure). Each bar the engine opens a DOL trial, also open shadow trials (not displayed) for:
   - (a) MM 1.0 of the current zigzag leg (the PA-1 ladder);
   - (b) the nearest draw-side pool (a "nearest pool" rule);
   - (c) ICT −1 SD.
   - Grade them like DOL trials (hit within H vs `pBase`).
   - Panel row: `vs MM-rule +4.1 pp · vs nearest −0.8 pp`.
2. **Candidate-ledger features** (CAL-3 / CAL-4 feature vector `x`, prior weight 0), measured on every candidate:
   - the last breakout bar's body/ATR and close location;
   - range-break flag and 20-bar range width in ATR;
   - bars since the last range breakout and whether it closed back inside within 5 bars (T4 (1));
   - zigzag leg progress `u/δ` and `y/δ` for the candidate (1.9);
   - "candidate within 0.1 ATR of MM 1.0 / EXT −0.27 / −0.62 / −1" (a per-chart test of the Fibonacci-confluence claim that T1/T2 reject on average).

**Value.** Every popular projection claim becomes a per-chart measurement instead of a debate, and the engine can show its margin over the rule the trader already uses.

**Evidence.** Weak for the features themselves; the infrastructure value is moderate (CAL).

**Risk.** More state per candidate. Cap it as CAL-3 does (256 probes).

**Effort.** S (shadow selectors once COMP-3 exists); M (features once CAL-4 exists).

---

## 5. Considered and rejected (do not implement)

| Idea | Why not | Numbers |
|---|---|---|
| Fibonacci extensions (127.2 / 161.8 / 200 / 261.8 %) or ICT −0.27 / −0.62 / −1 / −2 / −2.5 / −4 SD as scored targets or confluence anchors (`anchors`, 1931) | No level effect; the edge is the same at non-Fibonacci ratios; L2 finds 1.618 reached less than a random walk | T1 bumps 0.85-1.11 vs placebo 0.85-1.23; T2 edges flat; L1; L2 (67% vs 71%, t −13.5) |
| AB=CD / leg 1 = leg 2 as a scored source outside price discovery | Random-level rate; no stall at the level; P(leg 2 ≥ leg 1) = 0.49-0.50 = null | T1, T2 |
| Fibonacci retracement / OTE levels | Entry concept; continuation odds fall smoothly with depth | ICTS 1.10, L3, T1 retracement bumps |
| Elliott wave counts and targets | Subjective counts; no controlled test; ratios rejected | L9, T1 |
| Harmonic patterns (Gartley / Bat / Butterfly / Crab) | Rare, small-n, researcher degrees of freedom; Fibonacci ratios rejected | L10, T1 |
| "Measured move from the breakout bar" as a target or a probability bonus | Geometry | T3 |
| Requiring a follow-through bar before trusting a breakout | Raises the win rate only through geometry | T3 (0.664 vs 0.663 geometry) |
| H2 / L2 second-entry bias | Geometry | T3 |
| 20-gap-bar / moving-average magnet | Random-level rate intraday; the moving average is a moving target | T3 |
| "Always In" direction as a bias row or D component | Zero side information | T4 (2): +0.2 ± 0.5 pp, n 10,169 |
| Measuring-gap (FVG-midpoint) projection targets | Random-level rate on 1h; the 5m uplift is a clock confound | T4 (3) |
| Range-height measured move as a level | +3 pp race effect only; WYK agrees | T4 (1b), WYK §2.5 |
| ETA from leg-time symmetry | Reproduced by the shuffled null | T4 (4) |
| Conditioning reach or PoT on the previous leg's size | No memory between legs | T1 (corr −0.03 to +0.03) |
| ADR / ATR projection caps on targets | Sign reversed in data | SESS §2.7 |
| Dow "confirmation" (SMT) | Needs a second symbol | ICT note |

---

## 6. Notes for implementers
- PA-1, PA-3 and PA-5 share the zigzag. Implement it once (section 4 preamble) and test it against `pa_tools/palib.py: zigzag` on exported bars.
- `src` code collisions: PA-1 (8-10), PA-2 (8), ACAD-5 (8-9) and OF-8 propose overlapping new `src` codes. Assign them centrally:
  - 8 = RTH close;
  - 9 = 52-week;
  - 10 = ATH/ATL;
  - 11-13 = projections.
  - Update `f_tierW`, `f_levelName`, `f_shortName` and `f_kzAff` together.
- Kinds 8/9 (PA-1) must not collide with ICTPD-6's proposed kinds 8/9 (gaps). Use 8/9 = gaps and 10/11 = projections if both land, and update the `f_newLevel` side map (1085) accordingly.
- Every new readout or level must be graded with a **clock-matched** baseline when it is session-anchored (T5 lesson), and with the plain random-level baseline otherwise.
- Pine constraints respected: no new `request.*` calls (PA-2 uses `time()` with a session string, as 971-974 already do); O(1) state; no forward references (helpers in PURE HELPERS, state in STATE, updates inside the confirmed-bar engine block); `math.exp` and `math.max` only.

---

## 7. Sources

Published (URLs as found; most were read through search-result summaries because the hosts were unreachable from this session):
- Batchelor, R., Ramyar, R. (2006). Magic numbers in the Dow. City University London. https://openaccess.city.ac.uk/id/eprint/16276/ · https://www.researchgate.net/publication/228713810_Magic_numbers_in_the_Dow
- Glattfelder, J. B., Dupuis, A., Olsen, R. B. (2011). Patterns in high-frequency FX data: discovery of 12 empirical scaling laws. *Quantitative Finance* 11(4). arXiv:0809.1040 https://arxiv.org/abs/0809.1040 (full-text passages read via the paper index)
- Glattfelder, J. B., Olsen, R. B. (2024). The Theory of Intrinsic Time: A Primer. arXiv:2406.07354 https://arxiv.org/abs/2406.07354
- Glattfelder, J. B., Golub, A. (2022). Bridging the Gap: Decoding the Intrinsic Nature of Time in Market Data. arXiv:2204.02682
- Houweling, T. (2025). The Hidden Constant of Market Rhythms: How 1−1/e Defines Scaling in Intrinsic Time. arXiv:2511.14408
- Mayerhofer, E. (2019). Three essays on stopping (Taylor 1975, Lehoczky 1977). arXiv:1909.13050 https://arxiv.org/abs/1909.13050
- Brown, S., Goetzmann, W., Kumar, A. (1998). The Dow Theory: William Peter Hamilton's Track Record Reconsidered. *J. Finance* 53: 1311-1333. https://onlinelibrary.wiley.com/doi/10.1111/0022-1082.00054 · NYU Stern news (4.4 pp/yr): https://www.stern.nyu.edu/experience-stern/news/prof-stephen-brown-s-research-dow-theory-featured
- MQL5 statistics blog (2026). Fibonacci extensions reach 1.618 less often than a random walk: 26,795 double bottoms. https://www.mql5.com/en/blogs/post/776239
- Tradeify (2026). Fibonacci Retracements and Extensions Put to the Test. https://tradeify.co/education/fibonacci-retracements-and-extensions
- Gurrib, I., Nourani, M., Bhaskaran, R. K. (2022). Energy crypto currencies and leading U.S. energy stock prices: are Fibonacci retracements profitable? *Financial Innovation* 8. doi:10.1186/s40854-021-00311-8
- CXO Advisory, Robert Prechter guru grade. https://www.cxoadvisory.com/individual-gurus/robert-prechter/
- HKUST independent study, Trading harmonic patterns. https://cse.hkust.edu.hk/~rossiter/independent_studies_projects/trading_harmonic_patterns/trading_harmonic_patterns.pdf
- Researcher degrees of freedom, Gartley patterns. https://aaronmams.github.io/Researcher-Degrees-of-Freedom,-Gartley-Patterns,-and-Porn
- Bulkowski, T. Measured move up; measure rule; measured move retrace study. https://thepatternsite.com/mmu.html · https://thepatternsite.com/measure.html · https://www.thepatternsite.com/MMRetrace.html
- Brooks, A. *Trading Price Action: Trends* (Wiley 2012), ch. 2 (breakouts) and ch. 13 (20 gap bars). https://www.oreilly.com/library/view/trading-price-action/9781118172339/OEBPS/9781118172339_epub_c_02.htm · https://www.oreilly.com/library/view/trading-price-action/9781118172339/OEBPS/9781118172339_epub_c_13.htm
- Brooks, A. 80% rule (MoneyShow). https://www.moneyshow.com/articles/tradingidea-48940
- Brooks Trading Course forum and analysis pages: measured move https://www.brookstradingcourse.com/support-forum/general-trading-discussion/measued-move/ · 2nd-leg measurement https://brookstradingcourse.com/support-forum/18-trading-ranges/2nd-leg-measurement-and-starting-point · 20-gap-bar https://www.brookstradingcourse.com/support-forum/general-trading-discussion/20-gap-bar-buy-and-ema-gap-bar-buy/ · breakout fail https://www.brookstradingcourse.com/support-forum/12-market-cycle/breakout-fail/ · "Emini bulls want measured move up and bears want Leg 1 = Leg 2 down" https://www.brookstradingcourse.com/analysis/emini-bulls-want-measured-move-up-bears-want-leg-1-leg-2-down/ · acronyms https://www.brookspriceaction.com/acronyms.php
- ICT Fibonacci / SD projections (practitioner): https://backtrex.com/en/blog/ict-standard-deviation-projection-price-targets · https://innercircletrader.net/tutorials/ict-fibonacci-levels/
- Gap-fill statistics (practitioner): https://www.tradingview.com/script/32pGGSWx-Gap-Fill-Probability-Statistics-ES-NQ/ · https://marketchameleon.com/Instructional-Stock-and-Options-Trading-Videos/446/Analyzing-SPY-Large-Opening-Gaps-Using-Market-Chameleon
- Pine Script v6 docs (local mirror): `docsrc/jabez4jc_pinescriptv6/concepts/sessions.md` (session.isfirstbar_regular / islastbar_regular; futures ETH = regular session), `reference/syminfo.md` (syminfo.type values), `reference/time.md` (time(timeframe, session, timezone)).

Sibling reports used for cross-reference: `ict_struct.md` (S10 Tradeify, §2.2 structure test), `wyckoff_sd.md` (§2.5 measured move and throwback), `quant_pot.md` (findings 2-7), `quant_regime.md` (findings 1-7), `academic_sr.md` (Osler, Kavajecz), `ict_pd.md` (ICTPD-6 gaps), `calib_ml.md` (CAL-3/4), `competitors.md` (COMP-3/6), `session_stats.md` (§2.7 ADR).

This study's code: `study/pa_tools/palib.py` (loaders, ATR, zigzag, survival baseline, races), `t1_legs.py`, `t2_proj.py`, `t3_brooks.py`, `t4_misc.py`, `t5_pdc.py`, `t6_blind.py`; outputs `out_t1_*`, `out_t2_*`, `out_t3_*`, `out_t4_*`, `out_t5_*`, `out_t6_*`.
