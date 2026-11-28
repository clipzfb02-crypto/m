# Order Flow and Market Microstructure of Liquidity: study for DOL Engine v2

Domain: where stop-loss and take-profit orders actually rest, what happens when they are triggered, how much "liquidity" a pool holds, how pools decay, round numbers, stop hunting, absorption and icebergs, crypto liquidation levels, and delta/footprint signatures of a sweep. The goal is a better **pool-size model** and **sweep definition** for the engine, judged by one question: does it help predict which liquidity is taken next, when, and how likely?

Engine studied: `brief/baseline_v2.pine`. Line numbers refer to it; it is identical to `/home/user/m/indicators/dol_engine.pine`.

Evidence grades:
- **strong**: peer-reviewed, or a large replicated quantitative study.
- **moderate**: published or reproducible statistics with numbers.
- **weak**: practitioner consensus, vendor claims, small samples.
- **none**: folklore.

"[this study]" marks original tests run for this report. Scripts and raw outputs are in `brief/study/orderflow_tools/` (section 7).

---

## 0. Executive summary

1. **Where stops sit is well established.**
   - Stops sit a short distance beyond obvious levels. Take-profit and limit orders sit *at* round numbers.
   - Osler, RBS order book (strong): 14.3% of executed stop-buys sit at 01-10 above a "00", against 6.9% at 90-99 below. Take-profits are 9.3% exactly at 00.
   - Stop-losses are placed a **median 0.43%** from the market. They live a **median 0.46 days** (mean 3.42).
   - Support and resistance coincide with book depth (Kavajecz & Odders-White).
   - The engine's geometry is right: the pool is the extreme, and the stop zone lies beyond it.
2. **How deep a sweep goes, measured on 7 datasets [this study].**
   - Of 5,631 trade-throughs of live pivot pools, 44.5% closed back inside (REJECT).
   - REJECT sweeps penetrate a **median 0.23 ATR**: 0.16-0.19 on daily equities, 0.23-0.27 on hourly FX, NQ and gold. q80 is 0.52 ATR and q90 0.53-0.84.
   - The engine's 0.20 ATR zone is close to the median. Its **0.10 ATR invalidation buffer is beaten by 78.5% of rejected sweeps**.
   - Deeper stops do **not** improve expectancy. In 25,195 simulated races, mean R is −0.004 at a 0.10 ATR buffer and −0.020 at 0.75 ATR. Deeper buffers only trade win rate (41.8% → 44.6%) for smaller R.
3. **Pool "size" features do not predict which pool is taken or what happens after the sweep.**
   - Equal prints, tests, age and prominence move post-sweep odds by at most ±2 pp at 30 bars.
   - Sibling W-tests show the same for reach.
   - The one size proxy with a measurable post-take effect is **prominence**: 10-bar extension beyond the sweep is +0.21 vs +0.06 ATR above the null for high vs low prominence (about 2.3σ).
   - The best pool-size model is therefore a *small* one: source tier, prominence and stacking. Equal-print and test bonuses are zero by default and learned per chart. This matches sibling WYK-1/WYK-2.
4. **Sweep depth carries no directional information at bar resolution [this study].**
   - Across six depth buckets and both close classes, the 30-bar re-take of the sweep extreme and the 1-ATR throwback are within ±2.6 pp of the distance-matched null.
   - Sweep classes such as POKE / REJECT / PROBE / ACCEPT are useful **labels and ledger cells**, not forecasts. This agrees with ICTS-2, BIAS-4 and ICT-2: continuation, not reversal, is the base case.
5. **After any pool is traded through, volatility bursts in both directions for a few bars, then it is over.**
   - Within 3 bars, the sweep extreme is re-taken +4.1 pp and the pool is thrown back by 1 ATR +3.2 pp more often than the null.
   - The further excursion is +0.145 ± 0.018 ATR (+24%).
   - The effect is +9% at 10 bars and gone by 30.
   - This matches Osler's cascades, which are significant for 15 minutes to 2 hours and reverse at 1-2 days, and the 2025 crypto liquidation cascades, where 88% of forced selling landed within 30 minutes.
   - It is a **timing** effect, not a direction effect.
6. **Fresh extremes are liquidity immediately, and the engine misses them.**
   - 60.8% of the wicks of rejected sweeps are re-taken **within 5 bars**, before a `pivLen = 5` pivot could even register them. Only 38.3% ever become pivots.
   - At 3 bars they are re-taken 4.3 ± 1.0 pp more often than distance alone predicts.
   - Proposal OF-1 registers the sweep wick as a pool at once. This also places the invalidation "beyond the sweep high", where traders put it.
7. **Round numbers: the order clustering is real, but at bar resolution they are not magnets [this study].**
   - The round-minus-control 30-bar reach is mixed in sign across 7 datasets, between −4.5 and +10.9 pp.
   - Once price comes within 0.05 ATR, a coarse round number is passed slightly *more* often: 77.3% vs 74.0%, +3.3 pp, 2.8σ.
   - A sweep wick beyond a pool **stops short** of a round number 4-5 pp more often than at an arbitrary price the same distance away. This fits front-running one tick ahead of round clusters (Lallouache & Abergel) and take-profits at 00 (Osler).
   - Jung & Lee (2026): round levels hold more depth but show no extra depth-adjusted stickiness.
   - So: **no score bonus by default; cap zones at the round and place stops beyond it.** This contradicts the zone-extension part of sibling ICT-3.
8. **Thin-volume paths are weak.** Pools behind a thin volume-profile path are taken +1.3 to +3.6 pp more often (unstable across lookbacks). Behind a high-volume "wall" they are **not** taken less (−1.5 to +1.4 pp). The engine's ×0.85 wall penalty is unsupported.
9. **Order-flow tools exist in Pine v6 but have no bar-level evidence.**
   - `request.footprint()` (delta, POC, imbalance rows) exists. A script that calls it can be used **only** on Premium/Ultimate plans, so it must not go into the main engine.
   - A lower-timeframe delta proxy works for everyone.
   - No reproducible statistic shows that absorption or CVD divergence predicts direction at bar scale. One vendor test of millions of trades found no directional edge against random bars.
   - Recommendation: label and log only, with zero default weight.
10. **Crypto liquidation levels are the order-flow analogue of stop pools, but unvalidated.**
    - The mechanics are real: the BitMEX average leverage of liquidated traders was 60×; open interest clears 25-70% in a cascade.
    - No study shows that modelled heatmap clusters are hit more often than random levels, and vendors admit the maps do not tell the sequence.
    - At most an optional, ledger-graded P3 source.

---

## 1. Concepts: definitions and parameters

Each concept lists the definition (algorithmic where possible), how practitioners use it for a target or bias, the evidence pointer (section 2), failure modes, and the engine status (detailed in section 3).

### 1.1 Stop-loss clustering beyond obvious levels (the physical "pool")
- **Definition.** Protective stops of longs rest *below* recent swing lows (sell-side liquidity, SSL). Stops of shorts rest *above* swing highs (buy-side liquidity, BSL). Breakout-entry stops sit at the same places. Each is a market order once triggered.
- **Parameters**:
  - Osler (2005, Table I): stop-loss orders are placed a median 0.43% (mean 0.91%) from the market at placement.
  - They are outstanding a median 0.46 days (mean 3.42 days).
  - Stop orders are larger than take-profits: median $3.24 m vs $2.12 m. The largest stop is about $450 m, more than twice the largest take-profit.
  - More than 62% of the face value of very large stop orders sits within ±10 pips of a "00".
- **Practitioner placement rules (weak).** "1-2 ticks beyond the swing". "Beyond the wick". ATR buffers of 0.1-0.5 ATR. Turtle Soup buys back 5-10 ticks above the old 20-day low (Connors & Raschke, via sibling ict_liq.md).
- **Use for DOL.** The draw is to the price band just beyond the most obvious unswept extremes.
- **Failure modes.**
  - The distribution is a *band*, not a price.
  - Stops are short-lived and refreshed, so "old" levels hold fewer of yesterday's stops than charts suggest.
- **Engine: present.** BSL zone `[price, price + 0.20 ATR]` (1762), SSL mirror (1774). Swept on a strict trade-through (623-624).

### 1.2 Take-profit and limit clustering at round numbers; front-running
- **Definition.** Take-profits and resting limit orders bunch *exactly at* round prices ("00", then "50"). Stops bunch just *beyond* them.
- **Parameters (Osler 2003, via ict_liq E1).**
  - Take-profits: 9.3% exactly at 00, against about 1% if uniform.
  - Stop-buys: 14.4% at 01-10 vs 7.4% at 90-99. Stop-sells mirror.
  - Reversal frequency at round numbers (Osler 2005, Table V.B): DEM 59.3% vs 54.8%, JPY 60.1% vs 57.3%, GBP 58.1% vs 56.6% at arbitrary numbers.
- **Related findings.**
  - Lallouache & Abergel: EBS limit orders keep clustering at old round prices after a tick-size cut. Algos post **one tick ahead** of clusters (last digit 1 / 9).
  - Bhattacharya, Holden & Jacobsen (2012): in more than 100 m NYSE trades, liquidity demanders show excess buying one cent **below** round numbers and excess selling one cent **above**. The size is ordered by roundness: integer > half > quarter > dime.
  - Jung & Lee (2026): round levels attract more resting depth in all 5 Nasdaq stocks studied. Depth-adjusted durations are **not** longer (9 of 10 indices are below 1). In two stocks, departures are biased *away* from the round.
  - Bitcoin: more than 10% of prices end in "00" (Urquhart 2017), with no pattern in returns after them.
  - Gold: round-number barriers in the conditional mean and variance (Aggarwal & Lucey 2007). Lucey & O'Connor (2016) find barriers at 0/00 for gold and none for silver.
- **Use for DOL.**
  - Round numbers just beyond a pool hold the take-profit orders that stop a sweep.
  - Stops beyond the round fuel the run once it is crossed.
- **Failure modes.**
  - The "roundness" scale depends on the instrument.
  - Minute-scale effects wash out in hourly bars (section 2.2, T2).
- **Engine: missing.** grep finds no round-number logic.

### 1.3 Stop cascades ("running the stops")
- **Definition.** Price crossing a stop cluster converts resting stops into market orders in the same direction, which pushes price further: positive feedback.
- **Parameters.**
  - Osler (2005, Table VI.A): extra move after crossing a round number vs an arbitrary one, in hundredths of a percent:
    - DEM 1.12 (15 min), 0.89 (30 min), 0.57 (1 h), 0.85 (2 h);
    - JPY 1.30 / 1.34 / 1.26 / 2.35;
    - GBP 0.77 / 0.80 / 0.27 / 0.35.
  - At 1-2 days the sign turns negative (DEM −5.23 at 1 d, −2.53 at 2 d).
  - The mean 15-minute move is 0.061% after crossing a round vs 0.054% after an arbitrary level, about +13%.
  - CFTC (Fett & McPhail, E-mini, 10-year, WTI): stop orders execute more often on volatile days and supply liquidity in the direction of the move.
  - Crypto (Garcia Seuma 2026, 7 BTC cascades 2022-2025): 88% of post-onset forced selling landed within 30 minutes; open interest cleared 25-70%.
- **Theory.** Predatory trading (Brunnermeier & Pedersen, J. Finance 2005): traders who know others must liquidate sell first, push price through the trigger, and buy back after the overshoot. The prediction is overshoot, then reversal.
- **Use for DOL.**
  - When the timing is right, the inner pool of a stack accelerates price into the outer pool (the "outermost is the draw" rule).
  - The extension is short-lived.
- **Engine: partial.** Stack logic (1230-1251) and the `liqEvt` raid read (1580-1582). That mapping is disputed by siblings.

### 1.4 Stop-zone depth (how far beyond the level the stops reach)
- **Definition.** For a pool at price P (BSL), penetration `pen = (high_sweep − P) / ATR[1]` on the bar that first trades through.
- **Measured [this study, T1]:**
  - REJECT sweeps (close back inside): median 0.233 ATR, q80 0.518, q90 0.53-0.84.
  - HOLD sweeps (close beyond): median 0.74 ATR, q80 1.52.
- **The "stop band"** is `[P, P + q50]` for the core and `[P, P + q80]` for the outer edge, from REJECT sweeps only. HOLD sweeps measure trend, not stops.
- **Use.**
  - Zone drawing.
  - The invalidation placement (outside the band).
  - The sweep classification (1.7).
- **Engine: partial.**
  - Fixed `zoneATR` 0.20 (93).
  - Invalidation buffer 0.10 ATR (1344), which is inside the band for 78.5% of rejected sweeps.

### 1.5 Pool size: growth with time and touches
- **Microstructure claim.** More participants referencing a level means more stops: higher timeframe, more prominent, more touches, equal prints, older.
- **Evidence (section 2):**
  - Bounces carry memory in the short run. P(bounce) rises with prior bounces (Garzarelli et al. 2014, 45-90 s).
  - That memory decays within hours. EURUSD: a 1-bounce level falls to P = 0.5 after a 350-minute window, a 4-bounce level after 900 minutes. The logit falls by about 0.0018 per minute since the last bounce, at intercept 0.40 for 4 previous bounces (Chung & Bellotti 2021).
  - Stops are refreshed within days (Osler: median life 0.46 days).
  - At bar resolution, equal prints, tests and age do **not** change reach (sibling WYK §2.4). They also do not change post-sweep follow-through [this study, T3].
- **Algorithmic size model (proposed, OF-3).** `size = 1 − e^{−x}`, with `x = 1.2·tier + 0.8·min(1, prom/3) + 0.45·min(stack, 2)`. Equal prints and tests are learned features with zero default weight. Freshness is flat with a slow decay (WYK-2).
- **Engine: wrong.**
  - Density gives `0.9·eqCount + 0.35·min(tests,6)` in `x` (682).
  - Freshness *ramps up* with age ("stops accumulate", 671).

### 1.6 Pool decay after a sweep; residual liquidity; new liquidity at the fresh extreme
- **Definition.**
  - A trade-through fills the stops between P and the wick. Stops deeper than the wick remain (residual).
  - Breakout buyers' stops appear below the breakout. Faders' stops appear above the new wick.
- **Measured [this study, T1 and T6].**
  - Shallow pokes (≤ 0.05 ATR, closed back inside) are re-taken within 30 bars +2.6 ± 1.6 pp above the null (weak residual effect).
  - 60.8% of REJECT wicks are re-taken within 5 bars, before a pivLen-5 pivot exists. At K = 3 they are re-taken +4.3 ± 1.0 pp above the null.
  - At K = 30 the excess is +0.2 pp: plain geometry.
- **Engine.**
  - Binary removal on trade-through: present (1583-1589). That is correct per the decision history.
  - The new extreme is not a pool until the pivot confirms (pivLen bars later): **gap**.

### 1.7 Sweep vs breakout classification
- **Definitions at the sweep bar's close** (BSL; SSL mirrors). `pen` as in 1.4. `q50` and `q80` are the chart's learned REJECT depth quantiles (defaults 0.25 / 0.50 ATR).
  - **POKE**: `close < P` and `pen < 0.05`. A 1-3 tick tag that triggers only the nearest stops.
  - **REJECT (sweep)**: `close < P`.
  - **PROBE**: `P ≤ close < P + q50·ATR`. Closed beyond but inside the stop band.
  - **ACCEPT (breakout)**: `close ≥ P + q50·ATR`. ICT-2's HOLD rule uses 0.25 ATR, the same number.
- **Practitioner refinements (weak).**
  - "Hold 2 bars beyond".
  - Wick ratio of at least 50%.
  - Relative volume of at least 1.5×.
  - Lower-timeframe delta of at least 60% (the Flux "Liquidity Sweep Profiler" filters, via sibling competitors.md).
- **Measured [this study, T1].**
  - The depth bucket does not change the 3-, 10- or 30-bar directional odds beyond the null.
  - Volume does not modulate them either (sibling WYK §2.6).
  - Deeper wicks are simply more likely to close beyond. P(REJECT | pen bucket) is 91%, 85%, 76%, 59%, 44% and 18% for the buckets (0, 0.05], (0.05, 0.10], (0.10, 0.20], (0.20, 0.35], (0.35, 0.60] and > 0.60 ATR.
- **Engine: partial.** HOLD = `close > lv.top`, REJECT = `close < lv.price`, with fixed signs (1580-1582).

### 1.8 Absorption, exhaustion, icebergs (liquidity provision at extremes)
- **Definitions (practitioner, footprint vocabulary).**
  - **Absorption**: heavy aggressive volume at or through a level without price progress. For a BSL sweep: positive delta in the rows beyond P, then a close back inside.
  - **Exhaustion**: a delta spike, then volume dries up at the new extreme.
  - **Delta divergence**: a new price high with a lower bar or cumulative delta (NinjaTrader guide).
  - **Iceberg**: displayed size is refilled at one price.
- **Evidence.**
  - Frey & Sandås (Xetra; QJF 2017): when icebergs are detected, traders send *matching* market orders. The larger the executed fraction, the smaller the price impact, consistent with liquidity trading, not information.
  - Order-flow imbalance has a linear contemporaneous price impact with slope ∝ 1/depth (Cont, Kukanov & Stoikov). That is contemporaneous, not predictive at bar scale.
  - Short-term reversal is driven by temporary liquidity imbalances lasting less than an hour (Heston, Korajczyk & Sadka).
  - Crypto: 15-minute directional reversal in 90% of 183 Binance pairs. It concentrates after aggressive taker-driven moves, but the gross edge is 1.3 bp (Kitron & Wengrowicz 2026).
  - A vendor-reported test of CVD divergence found no directional edge against random bars (unverified).
- **Pine v6.**
  - `request.footprint(ticks_per_row, va_percent, imbalance_percent)` gives `footprint.delta()`, `footprint.get_row_by_price()`, `volume_row.delta()` and imbalance flags.
  - Only **one** call is allowed per script, and only Premium/Ultimate users can use a script that calls it (`reference/request.md:168`).
  - `request.security_lower_tf` with signed intrabar volume is a universal proxy.
- **Engine: missing.**

### 1.9 Liquidity holes and thin paths
- **Definition.** Large price changes happen when the book has gaps next to the best price (Farmer et al. 2004). Bar-level proxy: a low-volume region of the volume profile between price and target.
- **Measured [this study, T5].**
  - Thin path (vf < 0.6): +1.3 to +3.6 pp reach.
  - Thick path (vf > 1.4): −1.5 to +1.4 pp.
- **Engine: present** (1945-1947, ×1.10 thin / ×0.85 thick). The thick penalty is unsupported.

### 1.10 Crypto liquidation levels
- **Definition.** A leveraged position is liquidated at roughly:
  - longs: `LP ≈ entry·(1 − 1/L + mmr)`;
  - shorts: `LP ≈ entry·(1 + 1/L − mmr)`;
  - mmr is the maintenance-margin rate, about 0.4-1% for the first tiers. See Binance's formula: maintenance margin = notional·MMR − maintenance amount.
- **Heatmap model** (vendor, reconstructed from public descriptions):
  - New positions are estimated from ΔOI > 0 at each bar's typical price, split long/short (for example 60/40 by candle direction).
  - Each is projected to leverage tiers 5/10/25/50/100× with weights, then accumulated into price bins with time decay.
  - Bins are removed when crossed.
  - Observed alternative: Hyperliquid's on-chain open positions (CoinMarketCap; Glassnode covers about 90% of liquidatable BTC OI there).
- **Evidence.**
  - Cheng et al. (BitMEX): daily forced liquidations are 3.51% (long) and 1.89% (short) of outstanding contracts; the average leverage of liquidated traders is 60×.
  - Oct 10, 2025: about $19 bn liquidated; $2.1 bn closed by auto-deleveraging in 12 minutes (Chitra 2025).
  - **No published hit-rate or magnet test** of heatmap clusters exists. Coinglass: "when both sides are bright, it is hard to tell which one price will visit first" (sibling competitors.md).
- **Engine: missing.**

### 1.11 Stop hunting as a strategy
- **Definition.** Deliberately pushing price through a known stop cluster to fill size against the triggered orders.
- **Evidence.**
  - Mechanism: strong (Osler cascades; predatory-trading theory).
  - Deliberate intent: none (CFTC and Osler test cascades, not intent).
- **Use for DOL.** Identical to "draw to the obvious pool". Already the engine's premise.

### 1.12 Timing of stop runs
- **Definition and findings.**
  - Cascades last from minutes to about 2 hours (FX), and about 30 minutes for crypto liquidations.
  - At bar resolution [this study, T1]: the post-sweep volatility burst lasts 3-10 bars.
  - Stop executions concentrate on volatile days (CFTC).
  - Killzone timing belongs to the TIME study.
- **Engine: partial.** Killzone affinity (597-602). No post-event volatility state.

### 1.13 Equal highs/lows as pooled stops
- **Definition.** Two or more highs within a tolerance. Stops rest beyond the **outermost** print.
- **Evidence.**
  - Kavajecz & Odders-White define support as "the lowest bid reached at least twice", and it coincides with book depth.
  - Reach and post-sweep odds are not larger [this study, T3: eq ≥ 1 re-take −1.4 ± 1.9 pp; sibling E6, W12].
- **Engine: present and correct.** Merge to the outermost print (1104-1131).

### 1.14 Tests (touches without a take)
- **Definition (engine).** A bar within 0.30 ATR of the pool without taking it, at least 3 bars after the previous test (650-658).
- **Evidence.**
  - The short-run bounce memory decays in hours (1.5).
  - At bar resolution, tests ≥ 2 give +2.0 ± 1.2 pp re-take after the sweep (n.s.) and no reach effect (sibling WYK §2.4).
- **Engine: wrong-signed weight.** `0.35·min(tests,6)` magnitude (682).

---

## 2. Evidence

### 2.1 Literature

| # | Claim | Data | Result | Grade |
|---|---|---|---|---|
| L1 | Stops cluster just beyond round numbers; take-profits at them | Osler 2003 (J. Finance 58(5); FRBNY SR125). RBS, 9,667 orders, 1999-2000 | Take-profits at 00: 9.3% (uniform ≈ 1%). Stop-buys: 14.4% at 01-10 vs 7.4% at 90-99 (p = 0.029) | strong |
| L2 | Cascades after crossing stop clusters | Osler 2005 (JIMF; FRBNY SR150). 9,655 orders ($55 bn), quotes 1996-98 | Extra move after crossing a round vs an arbitrary level, in 1/100 %: DEM 1.12 / 0.89 / 0.57 / 0.85 at 15m / 30m / 1h / 2h. JPY 1.30 / 1.34 / 1.26 / 2.35. GBP 0.77 / 0.80 / 0.27 / 0.35. At 1 d: DEM −5.23, JPY +1.27, GBP −2.60. Reversal at rounds 58-60% vs 55-57% arbitrary | strong |
| L3 | Stop placement distance and life | Osler 2005, Table I | Stop-loss distance to market: median 0.43%, mean 0.91%. Take-profit 0.68% / 0.93%. Days open: stop median 0.46, mean 3.42; take-profit 0.59 / 4.05 | strong |
| L4 | Published S/R predicts intraday trend interruptions | Osler 2000, FRBNY EPR. 6 firms, 1996-98, 1-min quotes, vs 10,000 random level sets | Published levels beat chance. Arbitrary levels "bounce" 56.2% on average. The effect lasts at least 5 business days. Firms could not rank level strength | strong |
| L5 | S/R = book depth | Kavajecz & Odders-White, RFS 2004 (sibling ict_liq E3) | Support = "lowest bid reached at least twice". 84% of level/depth series are cointegrated | strong |
| L6 | Buy/sell imbalance flips at round numbers | Bhattacharya, Holden & Jacobsen, Mgmt Sci 2012. More than 100 m NYSE trades | Excess buying 1¢ below, excess selling 1¢ above round numbers. Size ordered by roundness. Little imbalance when price merely crosses | strong |
| L7 | Front-running round clusters | Lallouache & Abergel, arXiv 1307.5440 (EBS) | Orders stay at old round grids after a 10× tick cut. Algos post one tick ahead (last digit 1/9) | moderate |
| L8 | Round levels: more depth, no extra stickiness | Jung & Lee, arXiv 2610.34787 (5 Nasdaq stocks, 2025 LOB) | More resting depth at round levels in 5/5 stocks. Depth-adjusted duration index < 1 in 9/10 cases; significant ones are 0.93-0.94 (shorter). Intel/SoFi: 54% vs 46% of departures are away from the round | moderate |
| L9 | Prior bounces predict bounces, then decay | Garzarelli et al., Sci. Rep. 2014; Chung & Bellotti, arXiv 2101.07410 | p(b \| b_prev) rises with b_prev (HF). EURUSD: decays to 0.5 at about 350 min (1 bounce) and about 900 min (4 bounces). Micro-decay logit slope about −0.0018 per minute (b_prev = 4) | strong (HF) / moderate |
| L10 | Large price changes come from book gaps | Farmer et al., arXiv cond-mat/0312703 (LSE) | Large changes reflect gaps next to the best price, not large orders | strong |
| L11 | Order-flow imbalance drives price (contemporaneous) | Cont, Kukanov & Stoikov, arXiv 1011.6402 (TAQ, 50 stocks) | Linear relation, slope ∝ 1/depth. The volume-to-price relation is noisy | strong |
| L12 | Short-term reversal = temporary liquidity imbalance | Heston, Korajczyk & Sadka, arXiv 1005.3535 | Reversal is driven by imbalances lasting less than 1 hour, plus bid-ask bounce | strong |
| L13 | Crypto: taker-driven pushes revert | Kitron & Wengrowicz, arXiv 2608.21888 | 15-min directional reversal in 90% of 183 Binance pairs vs 2.7% of 187 US stocks. Concentrated after aggressive taker flow. Gross 1.3 bp | moderate |
| L14 | Icebergs | Frey & Sandås (QJF 2017; CFR WP 09-06) | Detected icebergs attract matching market orders. Price impact falls with the executed fraction | moderate |
| L15 | Stop orders in futures | CFTC, Fett & McPhail, "Stop Orders in Select Futures Markets" (summary only) | Stops execute more on volatile days and supply liquidity in the direction of the move. Slippage can be significant; exchange protections cap it | moderate (summary) |
| L16 | Crypto liquidation mechanics | Cheng et al., arXiv 2102.04591 (BitMEX) | Daily forced liquidations 3.51% (long) / 1.89% (short) of OI. Average leverage of the liquidated: 60× | moderate |
| L17 | Liquidation cascades | Garcia Seuma, arXiv 2608.03616 / 2607.27070; Chitra, arXiv 2512.01112 | 88% of forced selling within 30 min. OI clears 25-70%. Oct 10, 2025: about $19 bn; $2.1 bn ADL in 12 min. No early-warning variable is event-invariant | moderate |
| L18 | Heatmap clusters as magnets | Glassnode, CoinMarketCap, vendor scripts | No hit-rate test found. Vendors admit no sequence information | weak / none |
| L19 | Price clustering in BTC | Urquhart, Econ. Letters 2017 | More than 10% of prices end in "00". No return pattern after them | moderate |
| L20 | Gold psychological barriers | Aggarwal & Lucey, RFE 2007; Lucey & O'Connor, FRL 2016 | Barriers affect the conditional mean and variance (gold 0/00); none for silver | moderate |
| L21 | Absorption / CVD divergence | NinjaTrader guide; vendor TradingView scripts | Definitions only. One vendor test claims no directional edge for CVD divergence vs random bars | weak / none |
| L22 | Predatory trading | Brunnermeier & Pedersen, J. Finance 60(4) 2005 (theory) | Predators sell ahead of forced sellers: overshoot, then reversal | strong (theory) |

### 2.2 This study: tests on 7 datasets

**Data.** The sibling Wyckoff loader (raw prices):
- S&P 500 daily 1999-2019 and NASDAQ daily 1999-2019 (with volume);
- GOOG daily 2004-2013 (with volume);
- EURUSD 1H 2017-18 (5,000 bars, tick volume);
- NQ 1H, gold (GC) 1H and EURUSD 1H 2024-26 (11-12k bars each, no volume).

**Engine definitions.**
- ATR(14) Wilder.
- pivLen-5 pivots; a pool is live from confirmation to its first strict trade-through.
- Equal prints within 0.10 ATR merge to the outermost print.
- Tests: within 0.30 ATR, at least 3 bars apart.

**Null.** The distance-matched survival `S(d)`: the share of all bars on that chart whose next-K-bar excursion exceeds d ATR. This is the engine's `f_potBase` logic. "Edge" = observed − S(d). Standard errors are cluster-robust over 2K-bar blocks.

**T1. Sweep anatomy** (`sweep_depth.py`; 5,631 sweeps, 44.5% REJECT).

Penetration on the sweep bar, ATR of the bar before:

| Dataset | REJECT q25 / q50 / q80 / q90 | HOLD q50 / q80 |
|---|---|---|
| S&P 500 D | 0.08 / 0.19 / 0.42 / 0.58 | 0.52 / 0.88 |
| NASDAQ D | 0.07 / 0.16 / 0.40 / 0.53 | 0.47 / 0.93 |
| GOOG D | 0.07 / 0.18 / 0.39 / 0.54 | 0.62 / 1.14 |
| EURUSD 1H 17-18 | 0.12 / 0.27 / 0.60 / 0.84 | 0.95 / 1.80 |
| NQ 1H | 0.10 / 0.23 / 0.52 / 0.73 | 0.80 / 1.70 |
| GC 1H | 0.12 / 0.26 / 0.56 / 0.78 | 0.77 / 1.67 |
| EURUSD 1H 24-26 | 0.15 / 0.27 / 0.60 / 0.84 | 0.88 / 1.71 |

Pooled REJECT: median 0.233 and q80 0.518. P(pen > 0.05 / 0.10 / 0.20 / 0.25 / 0.50 ATR) = 0.895 / 0.785 / 0.553 / 0.479 / 0.210.

In % of price, the REJECT median is 0.024-0.030% on EURUSD hourly (about 2.5-3 pips), 0.07% on NQ, 0.10% on gold and 0.24-0.48% on daily equities.

Outcomes, pooled, edge vs null (± cluster SE):

| Horizon K | All: re-take sweep extreme | All: throwback 1 ATR through pool | Excursion beyond sweep extreme, vs G(d) |
|---|---|---|---|
| 3 | **+0.041 ± 0.006** | **+0.032 ± 0.006** | **+0.145 ± 0.018 ATR** (0.74 vs 0.60) |
| 10 | +0.019 ± 0.006 | +0.015 ± 0.007 | +0.130 ± 0.034 (1.53 vs 1.40) |
| 30 | +0.004 ± 0.005 | −0.004 ± 0.007 | +0.112 ± 0.071 (2.94 vs 2.83) |

The burst is **symmetric**: both continuation and throwback are elevated, so it is volatility, not direction. It fades by 30 bars.

By depth (REJECT, K = 30), re-take edges per bucket:

| Bucket (ATR) | Edge |
|---|---|
| (0, 0.05] | +0.026 ± 0.016 |
| (0.05, 0.10] | −0.016 |
| (0.10, 0.20] | +0.003 |
| (0.20, 0.35] | +0.001 |
| (0.35, 0.60] | +0.013 |
| > 0.60 | −0.013 |

HOLD buckets are within ±0.014. **No depth bucket carries directional information.**

**T3. Pool-size features vs post-sweep path** (same file):

| Feature | K30 re-take edge | K10 excursion excess (ATR) | Median REJECT pen |
|---|---|---|---|
| eq = 0 / eq ≥ 1 | +0.005 / −0.014 ± 0.019 | +0.127 / +0.190 ± 0.127 | 0.232 / 0.272 |
| tests 0 / 1 / ≥ 2 | +0.002 / +0.002 / +0.020 ± 0.012 | +0.158 / +0.086 / +0.118 | 0.244 / 0.226 (tests ≥ 1) |
| age ≤ 20 / 21-100 / 101-300 / > 300 bars | +0.012 ± 0.005 / 0.000 / −0.021 ± 0.016 / −0.002 | +0.179 ± 0.035 / +0.061 / +0.082 / +0.139 | 0.233 (≤ 20) / 0.214 (> 100) |
| prominence low / mid / high tercile | +0.006 / −0.002 / +0.008 | **+0.061 ± 0.044 / +0.115 / +0.214 ± 0.051** | — |

Reading:
- Only prominence relates monotonically to the size of the post-take run (high − low = +0.15 ATR, about 2.3σ).
- Young pools show a slightly larger burst, consistent with short stop lives (L3), but the age effect is not monotone.
- Equal prints and tests show nothing.

**T2. Round numbers** (`roundnum.py`; grids of step S vs 8 control offsets of the same grid).

Approach test:
- Event: a fresh approach to within 0.05 ATR, after 5 bars that did not reach.
- PASS: price trades 0.25 ATR beyond first (the approach bar counts if it already broke through).
- REVERSE: price falls back 0.5 ATR first, within 10 bars. Ties are dropped.

| Step rank (per dataset) | Round PASS | Control PASS | Difference |
|---|---|---|---|
| 0: coarsest (S&P 100, NASDAQ 1000, GOOG 100, EURUSD 0.01, NQ 1000, GC 100) | 0.773 ± 0.011 (n 1,500) | 0.740 ± 0.004 (n 12,194) | **+3.3 pp** |
| 1: next (50 / 500 / 50 / 0.005 / 500 / 50) | 0.760 ± 0.008 | 0.734 ± 0.003 | **+2.6 pp** |
| 2: finer (10 / 100 / 10 / 0.001 / 100 / 10) | 0.737 ± 0.004 | 0.738 ± 0.001 | 0 |
| 3: (NASDAQ 50, NQ 50) | 0.749 | 0.750 | 0 |

- Per dataset at the coarsest step, 5 of 7 are positive: GC +6.0, S&P +4.3, EURUSD 17-18 +4.2, NQ +2.3, EURUSD 24-26 +1.9, GOOG −0.7, NASDAQ −4.6 pp.
- Extension after a PASS: no difference (K10 2.58 vs 2.52 ATR).

Magnet test (nearest grid level 0.25-3 ATR away, taken within 30 bars, edge vs S(d)), round minus control, coarsest step:

| Dataset | Round − control |
|---|---|
| S&P | +0.021 |
| NASDAQ | +0.055 |
| GOOG | +0.109 |
| EURUSD 17-18 | −0.045 |
| NQ | −0.015 |
| GC | −0.026 |
| EURUSD 24-26 | +0.031 |

At the next step the mean is −0.002. **Mixed sign: round numbers are not magnets at bar resolution.**

**T2d. Does a sweep overshoot a round number just beyond the pool?** (`roundpen.py`; coarse-ish grids: S&P 50, NASDAQ 500, GOOG 50, EURUSD 0.005, NQ 500, GC 50).

P(the sweep extreme passes the next level beyond the pool), by that level's distance beyond the pool:

| Distance (ATR) | Round | Control (same distance) | REJECT only: round vs control |
|---|---|---|---|
| (0, 0.15] | 0.874 ± 0.022 | 0.916 ± 0.007 | 0.753 vs 0.849 |
| (0.15, 0.30] | 0.679 ± 0.031 | 0.716 ± 0.011 | 0.491 vs 0.516 |
| (0.30, 0.50] | 0.498 ± 0.031 | 0.551 ± 0.010 | 0.263 vs 0.308 |
| (0.50, 0.80] | 0.318 ± 0.023 | 0.359 ± 0.008 | 0.104 vs 0.155 |

- The weighted mean difference is about −4.2 pp (SE about 1.4, about 3σ).
- It is unchanged when "reaching within 0.03 ATR" counts as passing (−2.0 / −3.0 / −4.0 / −4.5 pp), so it is not only exact prints at the round.
- **The wick tends to stop short of a round number.**
- Combined with T2: price is less likely to *reach* a round beyond a pool, but once it is right at a coarse round, it more often goes through. This is the front-running / take-profit barrier followed by the stop-cluster pass-through that L1, L2, L6 and L7 describe.

**T4. Invalidation buffer** (`invbuf.py`; 25,195 simulated races).

Setup:
- Every 3rd bar, both sides.
- Target: the nearest live pool at ≥ 0.5 ATR. Invalidation: the nearest opposing pool ∓ buffer. Both within 6 ATR.
- H = 30. Same-bar ties count as a loss.

| Buffer (ATR) | Win | Loss | Open at H | Mean R | Losses that later hit the target |
|---|---|---|---|---|---|
| 0.10 (engine) | 0.418 | 0.428 | 0.154 | −0.004 ± 0.007 | 0.163 |
| 0.25 | 0.425 | 0.411 | 0.164 | −0.012 | 0.153 |
| 0.50 | 0.437 | 0.381 | 0.182 | −0.015 | 0.134 |
| 0.75 | 0.446 | 0.355 | 0.199 | −0.020 ± 0.006 | 0.119 |

The expectancy is invariant: a martingale, plus a slight drag. A deeper stop "beyond the stop hunt" buys win rate with R; it does not create edge. The ledger's EV readout will show exactly that.

**T5. Volume-profile path** (`pathvol.py`; datasets with volume).

Method:
- Profile of the last N bars, built like the engine's `f_profile` (24 rows).
- vf = mean profile volume between close and the nearest pool / profile mean.
- Outcome: taken within 30 bars, edge vs S(d).

| N | vf < 0.6 | 0.6-1.4 | vf > 1.4 |
|---|---|---|---|
| 60 | +0.015 | −0.012 | +0.013 |
| 120 | +0.036 (n 2,138) | −0.020 | +0.014 |
| 240 | +0.013 | −0.001 | −0.015 |

A thin path helps a little and unstably. A thick "wall" does not reliably hurt.

**T6. Sweep-wick lag** (`wicklag.py`; REJECT sweeps).

| Dataset | Wick re-taken within 5 bars |
|---|---|
| S&P 500 D | 67.7% |
| NASDAQ D | 71.8% |
| GOOG D | 81.8% |
| EURUSD 1H 17-18 | 57.5% |
| NQ 1H | 62.2% |
| GC 1H | 58.3% |
| EURUSD 1H 24-26 | 52.3% |
| Pooled | **60.8%** |

Only 38.3% of the wicks ever become pivLen-5 pivots, so the engine never offers the rest as targets.

### 2.3 Net reading for the forecasting problem
- **Which liquidity.**
  - Distance and the source's obviousness (tier, prominence) are the drivers. Microstructure "size" proxies (equal prints, touches, age, round numbers) do not move reach at hourly/daily resolution.
  - The engine should not add points for them. It should *learn* them per chart if at all (ICT-1 candidate ledger).
  - The one structural gap is **fresh extremes**: stops form beyond a new wick at once, and 61% of rejected-sweep wicks are re-taken before the engine knows they exist.
- **When.**
  - Right after a pool is taken, both nearby sides become more reachable for 3-10 bars (about +24% excursion at 3 bars).
  - Cascades are short (Osler 15 min to 2 h; crypto about 30 min) and reverse over days.
- **How likely.**
  - Calibrated geometry (`f_pot`, `f_raceH`, the empirical surface) stays the backbone.
  - Microstructure mainly fixes **geometry**: zone depth, invalidation band, round caps. It also gives honest labels (sweep classes).
  - Directional reads from sweep depth, volume or delta have no bar-level evidence.

---

## 3. Engine gap analysis (`baseline_v2.pine`)

| Concept | Status | Lines | What the engine does / what differs |
|---|---|---|---|
| Stops beyond swings (BSL/SSL) | present | 1753-1776, 623-624 | Pool = pivot price; zone `[P, P+0.20 ATR]`; swept on a strict trade-through. Matches L1/L3 |
| Stop-zone depth | partial | 93 (`zoneATR` 0.20), 1520 (`wPx`), 1762, 1774, 1848 | Fixed. The measured REJECT median is 0.16-0.27 ATR by market (daily lower, hourly higher). Not learned per chart, no outer band |
| Invalidation buffer | partial (honesty) | 1343-1364 (`f_invalidation`, `buf = 0.10*atr` at 1344) | 78.5% of rejected sweeps go deeper than 0.10 ATR. The EV is unaffected (T4), but the R:R / WIN readout does not show the stop-hunt exposure, and no "beyond band" option exists |
| Round numbers (take-profit at, stops beyond, front-running) | missing | — | No round grid. The evidence says: no score bonus, but cap zones at rounds and place stops beyond them (T2, T2d) |
| Stop cascades / stacked pools | present | 1230-1251 (`f_stackSide`), 684-685 (inner ×0.70) | The outermost is the draw. Consistent with cascade mechanics |
| Post-sweep volatility burst (timing) | missing | 1535 (`liqEvt` decay only), 915-916 (`potSig` 50-bar stdev) | No event-conditioned volatility. The PoT readout and race use the slow `potSig` |
| Sweep classification | partial / wrong sign | 1579-1582 | HOLD = `close > lv.top` (beyond 0.20 ATR), REJECT = `close < lv.price`; fixed ±tier into D. Depth is not used. The sign is disputed (ICTS-2, BIAS-4); T1 shows depth carries no direction |
| Fresh-extreme liquidity (sweep wick) | missing | 1753-1776 (pools only from `ta.pivothigh/low`, pivLen 5) | The wick of a rejected sweep is not a pool for 5 bars; 60.8% are re-taken in that time. After a BSL rejection, `f_invalidation` for a sell-side target skips the wick and uses the next BSL out or the execution swing (1346-1356) |
| Pool removal after sweep | present | 1583-1589, 1592-1596 | Binary, per the decision history. Residual liquidity after pokes is weak (+2.6 ± 1.6 pp); not worth a rule |
| Pool size: equal prints | present but over-weighted | 682 (`0.9*eqCount`), 1104-1131 | Merge to the outermost print is correct. The weight is not supported (T3, sibling W-tests) |
| Pool size: tests | wrong-signed weight | 650-658, 682 (`0.35*min(tests,6)`) | No support at bar resolution. HF memory says tests make a *bounce* more likely in the short run (L9) |
| Pool size: age | wrong shape | 668-671 (maturation ramp) | Stops have short lives (L3). Age has no reach effect (WYK). A ramp penalizes fresh pools by about 4 points (= `hyst`) |
| Pool size: prominence / tier | present | 682 (`0.8*min(1,prom/3) + 1.2*tier`), 506-516 | Supported (prominence relates to post-take extension, T3). Keep |
| Volume-profile path cost | partial | 1945-1947 (×1.10 / ×0.85), 1386-1424 | The thin bonus is weakly supported; the thick penalty is not (T5) |
| Absorption / delta / footprint | missing | — (volume is used only in the 1H profile, 978-1009) | No order-flow data. `request.footprint` would lock the script to Premium users |
| Crypto liquidation levels | missing | — | No OI-based source |
| Killzone timing of raids | present | 597-602, 971-976 | Fixed multipliers. TIME study domain |
| Sweep alerts | partial | 1502-1514 (live), 2088 | Live touch only. No bar-close class (REJECT/ACCEPT, depth), no post-sweep odds |
| Accuracy ledger | present | 1426-1499 | Strong base for measuring every proposal below. It has no per-feature or per-source sub-ledger beyond 4 families (`stN` size 5) |

---

## 4. Proposals (best first; maximum 10)

General Pine v6 notes:
- New state is declared in STATE (1020-1080), before any function that reads it (no forward references).
- Updates happen inside `if barstate.isconfirmed` (ENGINE, 1518).
- `array.percentile_linear_interpolation(id, percentage)` exists (`reference/array.md:1085`).
- There is no `request.*` budget concern: the engine has 6 unique requests out of 40 (`writing_scripts/limitations.md:206`).

### OF-1 (P1, S) · Instant sweep-wick pools: a fresh extreme is liquidity now, not 5 bars later

**Why.**
- Stops are placed beyond every fresh extreme at once: breakout buyers' stops below, faders' stops above the wick. Stops are short-lived (L3: median life 0.46 days).
- After a rejected sweep, the engine has *no pool* at the new wick until a pivLen-5 pivot confirms. By then 60.8% of wicks are already re-taken (T6), at above-null rates in the first bars (K3 +4.3 ± 1.0 pp; K30 +0.2 pp, plain geometry).
- Two visible symptoms:
  - The liquidity map misses the most obvious level on the chart.
  - The invalidation for a counter-target skips "beyond the sweep high", the most common trader stop.

**Algorithm.**
1. Inputs (G_LIQ, after 99):
   ```pine
   bool useWick = input.bool(true, "BSL / SSL · Sweep Wicks (instant)", group = G_LIQ,
     tooltip = "When a bar trades through a pool and closes back inside, its wick becomes a pool at once (stops rest beyond every fresh extreme). A swing pivot would register it only pivLen bars later.")
   ```
2. Types:
   - `Level` gets `bool wick = false` (after `induce`, 340).
   - `Trial` gets `bool wick = false` (after `liq`, 389).
3. State: `var array<float> wkSt = array.from(0.0, 0.0, 0.0)`. It holds n, hits and ΣpBase for wick picks, so the ledger can grade them.
4. Engine, step 3 (1564-1589): before the loop declare `bool wkH = false` and `bool wkL = false`. Inside `if hit and lv.isLiquidity()` (1580):
   ```pine
   if useWick and (lv.side == 1 ? close < lv.price : close > lv.price)
       if lv.side == 1
           wkH := true
       else
           wkL := true
   ```
5. New step 4b, after the registry drop (1597). Never push into `pool` while step 3 iterates it.
   ```pine
   if wkH
       if not f_mergeLiq(pool, 0, high, 0, eqPx, (high - llR) / atr, 1.0, false, bar_index, -1, -1)
           nextId += 1
           Level nw = f_newLevel(nextId, 0, 0, high + wPx, high, high, bar_index, bar_index, coilScore, indScore)
           nw.prom := (high - llR) / atr
           nw.wick := true
           pool.push(nw)
   // mirror for wkL with kind 1, low, (hhR - low) / atr, zone [low - wPx, low]
   ```
   - The bar itself is the anchor, so no `f_anchorScan` is needed.
   - When the pivot confirms pivLen bars later, step 9 calls `f_mergeLiq(..., countEq = true, pivBar = bar_index - pivLen, ...)`. `f_mergeAt` sees `samePx and inBar` (`pivBar == lv.bornBar`) and does **not** count an equal print (1112-1114). No duplicate, no fake EQ.
6. Tag: in `tag()` (638-648) add `if this.wick → t += " · WICK"`. Clean labels keep `BSL`/`SSL`.
7. Ledger:
   - `f_openTrial` (1426-1431) passes `wick = lv.wick`.
   - In `f_book` (1461) add:
     ```pine
     if t.wick
         wkSt.set(0, wkSt.get(0) + 1)
         wkSt.set(1, wkSt.get(1) + y)
         wkSt.set(2, wkSt.get(2) + t.pBase)
     ```
   - Full accuracy view: one row `WICK POOLS hit 64% · base 61% (n 37)`.
   - It also counts in family 0 automatically.

**Pine notes.**
- `high`, `low`, `llR`, `hhR` and `coilScore` are global series (876-892).
- `f_mergeLiq` signature: 1133.
- An outside bar that rejects both sides creates both pools, which is correct.

**Value to a trader.**
- The map shows the level everyone just watched print.
- The nearest opposing pool for `f_invalidation` becomes the sweep wick, so the R:R uses the classic "stop above the sweep high".
- With hysteresis (2-bar lead), the wick is chosen as DOL only when it scores best for 2 bars. Mostly it acts as a stack member: the outermost of a stack is the draw (1230-1251). It also fills secondary targets.

**Ledger measurement.**
- Toggle `useWick`. Compare the family-0 EDGE and the overall EDGE row.
- `wkSt` gives the wick pools' own hit vs distance-matched base. Expected: about +0 at H = 30, i.e. as good as other pools and available 5 bars earlier.
- Race stats (`raceSt`) show how the invalidation change affects WIN / EV.

**Evidence.** Moderate: T6 on 7 datasets (n = 2,504), T1 at K = 3, and the L1/L3 mechanism.

**Risk.**
- More near-price candidates. The proximity taper below `minDistATR` (664) and the hysteresis contain churn.
- Pool capacity (40) is unchanged; evictions are by score.

**Effort.** S.

### OF-2 (P1, S) · Measured stop band: learned zone depth, sweep classes, honest invalidation option (absorbs ICT-7)

**Why.**
- The zone is drawn where stops rest. On these data that is `[P, P + 0.23 ATR]` (median REJECT penetration) for the core, with an outer edge at q80 ≈ 0.5 ATR. Depth differs by market and timeframe (0.16-0.19 daily equities, 0.23-0.27 hourly FX/NQ/GC).
- The engine uses a fixed 0.20.
- Its 0.10 ATR invalidation buffer is beaten by 78.5% of *rejected* sweeps. Traders call that "my stop got hunted". T4 shows it is an R/win-rate trade-off, not an edge, so the honest fix is to **show** the band and offer the choice.
- A depth-aware sweep class also gives ICT-2/ICTS-2 a data-driven HOLD threshold (q50 ≈ 0.25 ATR, matching ICT-2's 0.25).

**Algorithm.**
1. Inputs:
   - Change `zoneATR` to default **0.25**; it is now the prior.
   - Add:
     ```pine
     bool   zoneLearn = input.bool(true, "Learn Zone Depth From Sweeps", group = G_LIQ,
       tooltip = "Zone depth = median depth of sweeps on this chart that closed back inside (needs 30). Liquidity Zone Depth is the prior.")
     string invBufM   = input.string("Tight", "Invalidation Buffer", options = ["Tight", "Beyond Stop Band"], group = G_DOL,
       tooltip = "Tight: 0.10 ATR beyond the opposing pool. Beyond Stop Band: past the 80th-percentile sweep depth. Wins more often, smaller R; expectancy is the same in tests.")
     ```
2. State (STATE, before 1082, so `f_invalidation` can read it):
   ```pine
   var array<float> penRej = array.new<float>()
   var float bandQ50 = na
   var float bandQ80 = na
   var int   swCls   = -1   // last sweep class of the active target: 0 POKE 1 REJECT 2 PROBE 3 ACCEPT
   ```
3. Step 3, in the `hit and lv.isLiquidity()` branch (1580):
   ```pine
   float pen = (lv.side == 1 ? high - lv.price : lv.price - low) / nz(atr[1], atr)
   bool  rej = lv.side == 1 ? close < lv.price : close > lv.price
   if rej
       penRej.push(pen)
       if penRej.size() > 300
           penRej.shift()
   float q50 = nz(bandQ50, zoneATR)
   int   cls = rej ? (pen < 0.05 ? 0 : 1) : ((lv.side == 1 ? close - lv.price : lv.price - close) / atr < q50 ? 2 : 3)
   if lv.id == activeId
       swCls := cls
   ```
4. Start of the engine block, replacing `wPx` at 1520:
   ```pine
   bool  bandOK = zoneLearn and penRej.size() >= 30
   bandQ50 := bandOK ? penRej.percentile_linear_interpolation(50) : zoneATR
   bandQ80 := bandOK ? penRej.percentile_linear_interpolation(80) : 2.0 * zoneATR
   float wPx = f_clamp(bandQ50, 0.05, 0.60) * atr
   ```
   Existing pools keep their geometry; new pools use the learned depth.
5. In `f_invalidation` (1344):
   ```pine
   float buf = invBufM == "Tight" ? 0.10 * atr : f_clamp(nz(bandQ80, 0.5), 0.10, 1.0) * atr
   ```
6. Alerts. Add a bar-close message when the active target was hit on this bar (in the `lv.id == activeId` branch, 1585), for example:
   - `"DOL target swept · REJECT 0.31 ATR (back inside)"`
   - `"... · ACCEPT (closed 0.42 ATR beyond)"`

   Keep the live touch alert (1502) unchanged; the decision history keeps it intrabar.
7. Terminal HUD: one line, `STOP BAND q50 0.23 · q80 0.52 ATR (n 214)`.
8. ICT-2 / ICTS-2: use `bandQ50` as `holdATR`. Do **not** split learner cells by depth: T1 shows no directional difference, and the cells stay dense.

**Ledger measurement.**
- Self-check of coverage: the share of REJECT sweeps with `pen ≤ bandQ80` should be about 80% (`penRej` holds them).
- `invBufM` A/B on race WIN %, average R and profit factor (`raceSt`, 1488-1499). Expect WIN up 2-3 pp, R:R down, EV within noise (T4).

**Value.** Zones look right on each market. The trader sees the stop-hunt band and chooses knowingly. Alerts say *what kind* of sweep happened.

**Evidence.** Moderate: T1/T4, plus L1/L3 for the band concept.

**Risk.**
- Survivorship: HOLD sweeps are excluded by design.
- Thin charts fall back to the prior until n = 30.

**Effort.** S.

### OF-3 (P2, S) · Evidence-based pool-size model (magnitude): tier, prominence, stack; equal prints and tests learned, not assumed

**Why.**
- The brief asks for a better pool-size model. Microstructure says pool size is the number of stops that reference a level. It grows with how many participants watch it (timeframe tier, prominence) and with nearby open positions.
- It does **not** grow with touches at bar scale: bounce memory decays in hours (L9), and stops are refreshed within days (L3).
- On the data, equal prints, tests and age change neither reach (sibling WYK §2.4) nor the post-sweep path (T3).
- Prominence is the only size proxy with a measurable effect: a larger post-take run (+0.21 vs +0.06 ATR at K10).
- The current density term (682) adds `0.9·eqCount + 0.35·min(tests, 6)`, and freshness *ramps up* with age (671). Both push selection toward pools that are not more likely to be taken.

**Algorithm.** Same structure as sibling WYK-1 "Evidence"; implement once. In `evaluate` (681-683):
```pine
if this.isLiquidity()
    float x = 1.2 * this.tier() + 0.8 * math.min(1.0, this.prom / 3.0) + 0.45 * math.min(this.stack, 2)
          + eqW * math.min(this.eqCount, 2) + tstW * math.min(this.tests, 3)
    this.dens := 1.0 - math.exp(-x)
```

Inputs, G_SCORE:
```pine
float eqW  = input.float(0.0, "Size · Equal-Print Weight", minval = 0.0, maxval = 1.0, step = 0.05, group = G_SCORE,
  tooltip = "0 = evidence default (equal highs/lows are not taken more often). Raise it only if the ledger shows otherwise on this chart.")
float tstW = input.float(0.0, "Size · Test Weight", minval = 0.0, maxval = 1.0, step = 0.05, group = G_SCORE)
```
- Freshness: adopt WYK-2's "Flat", i.e. `math.pow(0.5, age / (4 * halfLife))`.
- Round numbers add nothing to size (OF-4).
- Display: keep `EQx2 · T3` in the tag. These are facts, not weights.

**Ledger measurement.**
- A/B against the "Classic" density on the overall EDGE and the CHART LIQ / EXT LIQ family rows.
- With ICT-1's candidate ledger, `eqCount > 0` and `tests` become learned features. They are expected at about 0 (T3, W-tests).

**Value.** Removes systematic, evidence-free bias toward equal-print and tested pools (5-15 score points). Proximity, tier and draw decide.

**Evidence.** Moderate: T3 plus sibling W-tests, consistent with L3/L9.

**Risk.**
- Markets where tests *do* precede breaks lose that weight until the user or the ledger raises it.
- Overlaps WYK-1: implement one, not both.

**Effort.** S.

### OF-4 (P2, S) · Round-number layer, evidence-calibrated: cap zones and place stops beyond rounds; no score bonus by default (amends ICT-3)

**Why.**
- The order clustering at round numbers is the strongest-documented fact in this domain (L1, L2, L6, L7).
- On bars it shows up as geometry, not as a draw:
  - rounds are not magnets (T2: mixed sign);
  - sweep wicks stop short of a round number beyond a pool (−4.2 pp, about 3σ; T2d);
  - once price is right at a coarse round, it more often passes (+3.3 pp; T2).
- Sibling ICT-3 proposes a confluence bonus and **extending** zones past round numbers. T2d says the opposite for the zone edge, and T2 says the bonus has no reach basis.

**Algorithm.**
1. Inputs (G_LIQ):
   ```pine
   string rnMode = input.string("Auto", "Round Numbers", options = ["Off", "Auto", "Manual"], group = G_LIQ)
   float  rnMan  = input.float(0.0, "Round Step (Manual)", minval = 0.0, group = G_LIQ)
   bool   rnConf = input.bool(false, "Round Numbers as Confluence", group = G_SCORE,
     tooltip = "Off = evidence default: round numbers are not reached more often than other prices on hourly/daily bars.")
   ```
2. Step, once per day (global scope, before the engine):
   - `float atrD = nz(atrSlow) * math.sqrt(math.max(1.0, 86400.0 / chartS))`, as in ICT-3.
   - Then:
     ```pine
     bool newDayRN = timeframe.change("D")
     var float rnStep = na
     if rnMode != "Off" and (na(rnStep) or newDayRN) and atrD > 0
         float e = math.pow(10, math.floor(math.log10(atrD)))
         float m = atrD / e
         rnStep := rnMode == "Manual" and rnMan > 0 ? rnMan : m <= 1.0 ? e : m <= 5.0 ? 5.0 * e : 10.0 * e
     ```
   - This picks the smallest {1, 5}×10^k at or above one daily ATR, matching the "coarse" steps that showed effects in T2:
     - EURUSD (daily ATR about 0.007) → 0.01;
     - NQ (about 350) → 500;
     - gold (about 60) → 100;
     - S&P (about 17 in the sample years) → 50;
     - BTC (about 2,500) → 5,000.
   - Compute `timeframe.change` on every bar at global scope (v6 `and`/`or` short-circuit).
3. **Zone cap** where BSL/SSL zones are built (1762, 1774, 1848, OF-1 wick pools):
   ```pine
   float R = math.ceil(ph / rnStep) * rnStep
   float top = ph + wPx
   if not na(rnStep) and R > ph and R < top
       top := R
   ```
   Mirror with `math.floor` for SSL. The hit rule (trade-through of `price`) is unchanged.
4. **Stop beyond the round** (`f_invalidation`, 1346-1356):
   - If the opposing pool's outer edge lies within `bandQ80·atr` of a round number R beyond it, use `inv := R ∓ 0.05*atr`, i.e. just past the round.
   - T2d: a wick passes a round 0.15-0.30 ATR beyond the pool 67.9% of the time, against 71.6% for an arbitrary level at the same distance.
5. **Confluence** only if `rnConf`: push `math.ceil(close/rnStep)*rnStep` and `math.floor(close/rnStep)*rnStep` into `anchors` (1931).
6. **Feature for learning.** `Trial.rn = true` when the target pool lies within 0.35 ATR inside a round number. Add a per-feature stat (`rnSt` = n, hits, ΣpBase), shown in the Full accuracy view.

**Ledger measurement.**
- `rnSt` edge of round-adjacent targets vs the base.
- With `rnConf` on vs off: the overall EDGE.
- Race WIN with stops beyond rounds.

**Value.**
- Zones and stops align with where orders really sit.
- No unearned bonus, so selection is not pulled toward round prices.

**Evidence.**
- Strong for order placement (L1-L8).
- Moderate (own, 7 datasets, mixed) for the bar-level geometry.
- Moderate *negative* for the magnet claim.

**Risk.**
- The auto step can be off on exotic symbols; the Manual override covers that.
- Coordinate with ICT-3, which must drop the "extend past the round" rule and keep this cap.

**Effort.** S.

### OF-5 (P2, S) · Volume-profile path cost: keep a small thin-path bonus, drop the HVN-wall penalty

**Why.**
- T5: a thin path gives +1.3 to +3.6 pp (lookback-dependent). A thick path gives −1.5 to +1.4 pp.
- The engine multiplies by 1.10 (thin) and **0.85** (thick, 1947). The 0.85 is worth about 4-6 score points against unsupported evidence and can flip a selection.
- Mechanism (L10): gaps speed price up. High *traded* volume is not resting liquidity in the way.

**Algorithm.**
```pine
lv.mult *= vf < 0.6 ? vpThin : vf > 1.4 ? vpThick : 1.0
```
Inputs:
```pine
float vpThin  = input.float(1.05, "Path · Thin Bonus", minval = 1.0, maxval = 1.3, step = 0.01, group = G_SCORE)
float vpThick = input.float(1.00, "Path · HVN Penalty", minval = 0.7, maxval = 1.0, step = 0.01, group = G_SCORE,
  tooltip = "1.00 = evidence default (targets behind high-volume areas were not reached less often in tests).")
```

**Ledger measurement.** A/B on the overall EDGE. Optionally a feature stat for targets with `vf < 0.6`.

**Evidence.** Weak-to-moderate (T5; L10 for the mechanism).

**Risk.** Negligible.

**Effort.** S.

### OF-6 (P3, S) · Post-sweep volatility state for short-horizon readouts (ETA, PoT by session end, race)

**Why.**
- For 3-10 bars after any pool trade-through, both sides are more reachable: K3 excursion +24%, K10 +9% (T1). This matches L2/L15/L17: cascades last minutes to hours.
- The analytic PoT and race use the 50-bar `potSig` (916), which misses this.
- At H = 30 the effect on PoT is small (about +2% on σ·√H). Short-horizon features (sibling TIME-4 "PoT by session end", ETA, the post-sweep alert) feel it more.

**Algorithm.**
- State:
  ```pine
  var int   lastSwp = na
  var float vbIn    = 1.0
  var float vbAll   = 1.0
  ```
- In step 3, set `lastSwp := bar_index` on any liquidity hit.
- Every confirmed bar:
  ```pine
  float r = (high - low) / nz(atr[1], atr)
  vbAll := 0.995 * vbAll + 0.005 * r
  if not na(lastSwp) and bar_index - lastSwp >= 1 and bar_index - lastSwp <= 3
      vbIn := 0.98 * vbIn + 0.02 * r
  float vbF = f_clamp(vbIn / math.max(vbAll, 1e-9), 1.0, 1.6)
  ```
- Effective σ for short-horizon readouts:
  ```pine
  sigEff = potSig * (1 + (vbF - 1) * math.pow(0.5, (bar_index - nz(lastSwp, -1000)) / 3.0))
  ```
- Use `sigEff` in `f_pot` and `f_raceH` calls only when the horizon is 10 bars or less (TIME-4 / ETA). Leave the H = 30 PoT unchanged unless the ledger shows miscalibration in post-sweep trials.

**Ledger measurement.** Calibration of `pBase` for trials opened within 3 bars of a sweep vs all others: observed minus predicted.

**Evidence.** Moderate (T1 at 8σ for K = 3; L2, L15, L17).

**Risk.** Low. It is bounded and decays fast.

**Effort.** S.

### OF-7 (P3, M) · Order-flow tags at sweeps: lower-timeframe delta proxy for everyone (zero default weight, logged and graded)

**Why.**
- Traders ask for absorption and delta confirmation of a sweep, and competitors filter sweeps by LTF delta.
- There is no reproducible bar-level evidence that it predicts direction (L21; volume did not modulate outcomes in WYK §2.6).
- So add it as a **label plus a ledger cell**, not a weight.
- Do **not** call `request.footprint()` in the main engine: only Premium/Ultimate users can use a script that calls it (`reference/request.md:168`). Offer it, if ever, as a separate companion script.

**Algorithm.**
```pine
bool   useDelta = input.bool(false, "Sweep Order-Flow Tags (lower-TF delta)", group = G_FLOW)
string ltfD     = timeframe.from_seconds(math.max(60, int(timeframe.in_seconds() / 12)))   // simple string (reference/timeframe.md:132)
[ltO, ltC, ltV] = request.security_lower_tf(syminfo.tickerid, ltfD, [open, close, volume], ignore_invalid_timeframe = true)
```
Then, on a confirmed bar where a liquidity pool was hit (step 3), loop the intrabars:
```pine
float dAll = 0.0
float dBey = 0.0
float vAll = 0.0
for j = 0 to ltC.size() - 1
    float s = ltC.get(j) > ltO.get(j) ? 1.0 : ltC.get(j) < ltO.get(j) ? -1.0 : 0.0
    dAll += s * ltV.get(j)
    vAll += ltV.get(j)
    if lv.side == 1 ? ltC.get(j) > lv.price : ltC.get(j) < lv.price
        dBey += s * ltV.get(j)
```
Tags:
- `ABSORBED`: REJECT and `dBey * side > 0.2 * vAll`. Aggressive flow beyond the level, then back inside.
- `EXHAUSTED`: `|dAll| < 0.1 * vAll` on a sweep bar with a range above 1.5 ATR.
- `DRIVEN`: ACCEPT and `dAll * side > 0.3 * vAll`.

Put the tag in the bar-close sweep alert (OF-2) and in the sweep cells of ICT-2's learner, as a feature with prior weight 0.

**Pine notes.**
- Intrabar limit: 100k-200k intrabars by plan (`limitations.md:263`). With 12 intrabars per chart bar, that covers 8,000+ bars.
- The calculation is local and only runs on sweep bars (cheap).
- `ignore_invalid_timeframe` matches the existing call (982).

**Ledger measurement.** Per-tag post-sweep outcome vs the distance-matched base (ICT-2 cells).

**Evidence.** Weak: mechanisms L11/L13/L14, no bar-level validation.

**Risk.**
- Intrabar volume is not true aggressor delta; it is a sign proxy.
- FX has tick volume only.
- Users may over-trust the tags; keep the tooltip honest.

**Effort.** M.

### OF-8 (P3, L) · Crypto estimated liquidation levels as an optional, ledger-graded registry source

**Why.**
- For leveraged crypto perps, forced liquidations are the largest mechanical stop pools (L16, L17).
- No study shows that modelled clusters are hit more often than random levels (L18), and the sibling competitors study set this aside. So: off by default, measured by the ledger, no fixed weight.

**Algorithm.**
1. Inputs (G_KEY):
   ```pine
   bool useLiqMap = input.bool(false, "Crypto · Estimated Liquidation Levels", group = G_KEY)
   string oiSym   = input.symbol("", "Open-Interest Symbol", group = G_KEY,
     tooltip = "Leave empty to try <ticker>_OI. Use symbol search to find the open-interest series of your perpetual.")
   ```
2. Feed:
   ```pine
   float oi = request.security(oiSym == "" ? syminfo.tickerid + "_OI" : oiSym, timeframe.period, close[1],
     lookahead = barmerge.lookahead_on, ignore_invalid_symbol = true)
   ```
   - The `[1]` + `lookahead_on` pattern matches the engine's non-repainting rule.
   - Treat `na` as "no data" and disable the module silently.
3. State:
   - `var map<int, float> lqB` and `var map<int, float> lqS`: masses by bin `k = math.round(px / bin)`, with `bin = 0.25 * atrSlow` fixed at first use.
   - `var array<int> lqK` caps the key set at 400.
4. Each confirmed bar:
   - If `oi > oi[1]`, then `dOI = oi - oi[1]`, `px = hlc3`, `wL = close > open ? 0.6 : 0.4`. For each `(L, w)` in `[(10, .35), (25, .30), (50, .20), (100, .15)]`, with `mmr = 0.005`:
     - add `dOI·wL·w` at `px·(1 − 1/L + mmr)` to `lqS`;
     - add `dOI·(1 − wL)·w` at `px·(1 + 1/L − mmr)` to `lqB`.
   - If `oi < oi[1]`, scale all masses by `oi/oi[1]`.
   - Decay all masses by `0.5^(1/hl)`, where hl is about 3 days in bars.
   - Delete bins traded through this bar (they are liquidated).
5. Every 5 bars:
   - Local maxima with mass ≥ the 90th percentile and within `maxATR` become `f_pushExt(extReg, binPx, isHigh, 8, bar_index, mass/meanMass, 1.0)`.
   - Extend `f_tierW` (8 → 0.50), `f_levelName` (`LIQ H` / `LIQ L`) and `f_kzAff`'s default.
   - Note: Ext records use `bornBar = bar_index`. Anchor at the bar that contributed the most mass (track the argmax per bin).
6. Ledger: they fall in family 1. Add a per-source stat (src 8) to the Full view.

**Pine notes.**
- One more unique request (7 of 40).
- Map loops of at most 400 keys per bar are fine within loop-time limits.
- The `_OI` ticker format varies by exchange (community scripts use `_OI` and `.P_OI` variants). A symbol input is mandatory.

**Evidence.** Weak (mechanism moderate; magnet claim none).

**Risk.**
- Model error (leverage mix and long/short split are unknown).
- Single-exchange OI.
- Extra complexity. Ship only if the ledger shows an edge on users' charts.

**Effort.** L.

### Considered and not proposed
- **"Residual liquidity" after shallow pokes (keep the pool alive when pen < 0.05 ATR).** The evidence is +2.6 ± 1.6 pp, and it would contradict the trade-through decision. Leave it to the learner as a POKE cell (OF-2 classes).
- **Depth-based reversal reads (deep sweep = exhausted stops = reversal).** No directional difference by depth at K = 3, 10 or 30 (T1).
- **Bigger post-sweep "cascade target" from pool size.** The prominence effect (+0.15 ATR at K10) is too small to drive target selection. At most a note for the reach bands.
- **`request.footprint()` in the main script.** It locks out non-Premium users (OF-7).
- **Iceberg detection.** Not observable from TradingView data (no order-book feed).

---

## 5. Notes for implementers (coordination with sibling studies)

- **ICT-3 (round numbers):** keep its auto-step idea and Manual override. Replace "extend the zone to `R + 0.10·step`" with OF-4's **cap at R**. Make the confluence bonus opt-in (`rnConf = false`). The evidence for both changes is in T2/T2d.
- **ICT-7 (learned stop depth):** merged into OF-2. Use the median for the zone and q80 for the band. OF-2 adds the invalidation *option* plus T4's finding that expectancy is unchanged, so the default can stay "Tight" if the integrator prefers the reference look.
- **ICT-2 / ICTS-2 / BIAS-4 (sweep outcome):** use `bandQ50` as the HOLD threshold. Do not split cells by depth. OF-7 tags may become extra cells later.
- **WYK-1 / WYK-2:** OF-3 is the same density change with the microstructure rationale and T3 numbers. Implement once. Prominence stays the strongest size proxy.
- **TIME-1 / TIME-4:** OF-6's post-sweep factor multiplies on top of the volatility clock. Apply it only to horizons of 10 bars or less unless the ledger says otherwise.
- **COMP-2 (alerts):** OF-2's bar-close sweep class ("REJECT 0.31 ATR") belongs in the same alert redesign.
- Every proposal above is measurable with the existing ledger (`stN/stK/stPE`, `raceSt`) plus at most one small per-feature array. None changes the hit rule (strict trade-through for pools), the non-repainting contract, or the Clean look.

---

## 6. Sources

Literature and documentation:
- Osler, C. (2005), "Stop-loss orders and price cascades in currency markets", JIMF; FRBNY Staff Report 150. https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr150.pdf (Tables I, V.B, VI.A read for this report).
- Osler, C. (2003), "Currency orders and exchange rate dynamics", J. Finance 58(5); FRBNY SR125. https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr125.pdf (numbers via sibling ict_liq.md E1).
- Osler, C. (2000), "Support for resistance: technical analysis and intraday exchange rates", FRBNY EPR 6(2). https://www.newyorkfed.org/research/epr/00v06n2/0007osle
- Kavajecz, K. & Odders-White, E. (2004), RFS 17(4) (via sibling ict_liq.md E3).
- Bhattacharya, U., Holden, C. & Jacobsen, S. (2012), "Penny wise, dollar foolish: buy-sell imbalances on and around round numbers", Management Science 58(2). https://papers.ssrn.com/ab_id=1569922
- Lallouache, M. & Abergel, F., "Tick size reduction and price clustering in a FX order book". https://arxiv.org/abs/1307.5440
- Jung, J. & Lee, K. (2026), "Do round numbers hold prices? Occupation densities and depth-conditioned hazards in the limit order book". https://arxiv.org/abs/2610.34787
- Garzarelli, F. et al. (2014), "Memory effects in stock price dynamics: evidences of technical trading", Sci. Rep. 4:4487 (via sibling ict_liq.md E4).
- Chung, K. & Bellotti, A. (2021), "Evidence and behaviour of support and resistance levels in financial time series". https://arxiv.org/abs/2101.07410
- Farmer, J. D. et al. (2004), "What really causes large price changes?" https://arxiv.org/abs/cond-mat/0312703
- Cont, R., Kukanov, A. & Stoikov, S., "The price impact of order book events". https://arxiv.org/abs/1011.6402
- Heston, S., Korajczyk, R. & Sadka, R., "Intraday patterns in the cross-section of stock returns". https://arxiv.org/abs/1005.3535
- Kitron, N. & Wengrowicz, J. (2026), "Short-horizon mean reversion in cryptocurrency markets". https://arxiv.org/abs/2608.21888
- Frey, S. & Sandås, P., "The impact of iceberg orders in limit order books" (QJF 2017). https://www.cfr-cologne.de/download/workingpaper/cfr-09-06.pdf
- CFTC Office of the Chief Economist, Fett, N. & McPhail, L., "Stop Orders in Select Futures Markets" (research paper listing; summary only). https://www.cftc.gov/About/EconomicAnalysis/ResearchPapers/index.htm
- Cheng, Z., Deng, J., Wang, T. & Yu, M., "Liquidation, leverage and optimal margin in bitcoin futures markets". https://arxiv.org/abs/2102.04591
- Garcia Seuma, R. M. (2026), "Measuring the engine of a liquidation cascade". https://arxiv.org/abs/2608.03616 ; "Where does the criticality live?" https://arxiv.org/abs/2607.27070
- Chitra, T. (2025), "Autodeleveraging: impossibilities and optimization". https://arxiv.org/abs/2512.01112
- Brunnermeier, M. & Pedersen, L. (2005), "Predatory trading", J. Finance 60(4), 1825-1863 (theory; cited from the published literature).
- Urquhart, A. (2017), "Price clustering in Bitcoin", Economics Letters 159, 145-148. https://ideas.repec.org/a/eee/ecolet/v159y2017icp145-148.html
- Aggarwal, R. & Lucey, B. (2007), "Psychological barriers in gold prices?", RFE 16(2). https://ideas.repec.org/a/wly/revfec/v16y2007i2p217-230.html ; Lucey & O'Connor (2016), FRL, via https://research.ucc.ie/en/publications/mind-the-gap-psychological-barriers-in-gold-and-silver-prices/
- Kaminski, K. & Lo, A., "When do stop-loss rules stop losses?" https://dspace.mit.edu/bitstream/handle/1721.1/114876/Lo_When%20Do%20Stop-Loss.pdf
- Binance, liquidation price and maintenance margin FAQ. https://www.binance.com/en/support/faq/b3c689c1f50a44cabb3a84e663b81d93
- Liquidation heatmap methods: Glassnode https://research.glassnode.com/liquidation-heatmaps/ ; CoinMarketCap (Hyperliquid on-chain) https://coinmarketcap.com/charts/liquidation-heatmap/
- Tradeciety, OANDA order-book clustering at round numbers (practitioner). https://tradeciety.com/the-order-clustering-effect-around-round-numbers
- NinjaTrader, footprint chart guide (absorption, exhaustion, delta divergence definitions). https://ninjatrader.com/futures/blogs/footprint-charts-guide/
- Vendor CVD divergence test claim (unverified). https://www.tradingview.com/script/AQUKlq8S-RCV-CVD/
- Pine v6 docs (local mirror):
  - `docsrc/jabez4jc_pinescriptv6/concepts/other_timeframes_and_data.md` (`request.footprint`, line 2617);
  - `reference/footprint.md`;
  - `reference/request.md:168` (Premium/Ultimate restriction);
  - `writing_scripts/limitations.md:202-221` (request limits) and `:263` (intrabars);
  - `reference/array.md:1085` (percentile).

Sibling studies used for context and cross-checks (`brief/study/`): `ict_liq.md` (E1-E15, ICT-2/3/7), `wyckoff_sd.md` (§2.4, §2.6, WYK-1/2), `ict_struct.md` (ICTS-2), `bias_dol.md` (BIAS-4), `smc_impl.md` (§1.5-1.7), `competitors.md` (liquidation heatmaps, Flux sweep profiler).

---

## 7. Reproducibility

Scripts are in `brief/study/orderflow_tools/` (run with `python3 -I <script>`). They load data through `wyckoff_tools/wyck.py`.

| Script | Test | Output |
|---|---|---|
| `sweep_depth.py [K]` | T1, T3 | `out_sweep_K3.txt`, `out_sweep_K10.txt`, `out_sweep_K30.txt` |
| `penstats.py` | pooled depth exceedances | `out_penstats.txt` |
| `roundnum.py` | T2 | `out_roundnum2.txt` (`out_roundnum.txt` is a superseded run whose race start counted the approach bar's own low) |
| `roundpen.py [tol]` | T2d | `out_roundpen.txt`, `out_roundpen_tol.txt` |
| `invbuf.py [H]` | T4 | `out_invbuf.txt` |
| `pathvol.py [N]` | T5 | `out_pathvol.txt`, `out_pathvol_N.txt` |
| `wicklag.py` | T6 | `out_wicklag.txt` |

Network notes:
- Exchange APIs (Binance, Bybit, OKX) were unreachable from this session, so no crypto liquidation or open-interest test was possible.
- Several hosts (newyorkfed.org, kelley.iu.edu, glassnode.com) were unreachable through WebFetch. The Osler SR150 tables were read through the Firecrawl scraper instead.
- Firecrawl reported that this account's credits are running low (daily MCP credits refresh in about 23 h).
