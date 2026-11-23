# ICT Liquidity Theory: study for the DOL Engine v2

Domain: ICT (Inner Circle Trader) liquidity theory. That covers buy-side and sell-side liquidity, IRL/ERL, equal and relative equal highs/lows, old-high hierarchy, trendline liquidity, inducement, sweep vs run, turtle soup, low-hanging fruit vs major liquidity, how ICT picks the draw, and when a pool is spent. Plus all the hard evidence I could find on where stops actually sit and what price does after they are taken.

Engine studied: `brief/baseline_v2.pine` (line numbers below refer to it; identical to `/home/user/m/indicators/dol_engine.pine`).

Evidence grades: **strong** (peer-reviewed or large replicated quant study), **moderate** (published numbers, reproducible), **weak** (practitioner consensus / small or vendor samples), **none** (folklore).

---

## 0. Executive summary (what matters for "which liquidity is taken next, when, how likely")

1. **Distance dominates; ICT labels are small modifiers.** On two years of hourly data across EURUSD, GBPUSD, USDJPY, gold, NQ, ES, BTC and ETH, equal highs/lows were taken within 24 bars 63-82% of the time and ordinary swings at the same distance 68-76%. Knowing a level is "equal" improved the odds by **less than 1 percentage point** beyond distance alone (open-source distance-matched test, moderate). FVGs react about 5 pp above a distance-matched random level (about 40,000 events, SSRN, moderate). The engine's architecture is the right one: first-passage/empirical PoT, plus a distance-matched baseline in the ledger, plus bounded multipliers. ICT features should stay **bounded multipliers, learned per chart**, not big fixed weights.
2. **After liquidity is taken, continuation is more common than reversal.**
   - A G10-FX walk-forward study: three independent sweep mechanisms (EQH/EQL, order blocks, Asian range) agreed in **65 of 66 fold-selections** that a swept level predicts **continuation, not the textbook reversal**.
   - The distance-matched EQ test: reversal after the sweep was only 39-44%.
   - YM: a PDH break gave a green session 67% (open-close) or 81% (close-close) of the time.
   - Osler: price moves faster after crossing documented stop clusters, for up to about 2 hours.
   - The engine hard-codes "close back inside = reversal" (line 1581). It should **learn the sign** per chart.
3. **Stops sit just beyond obvious levels, and limit orders sit at them** (strong).
   - Osler, using RBS order data (9,655 orders, $55 bn), found 14.3-14.4% of stop-loss buy orders in the 01-10 band just above a "00" level, against 6.9-7.4% in 90-99 just below.
   - 9.3% of take-profit orders sit exactly at 00, against about 1% if prices were uniform.
   - Rates bounce 4.6 pp more often at round numbers.
   - Support/resistance levels coincide with order-book depth peaks (Kavajecz & Odders-White, RFS 2004). Their support level is literally "a low reached at least twice", i.e. equal lows.
   - **The engine has no round-number awareness.**
4. **Repeated tests make the next approach more likely to bounce, not to break, in the short run** (strong at high frequency; moderate intraday). This effect decays over hours. The engine counts tests as extra liquidity magnitude (line 682), which may be the wrong sign for a horizon of H bars.
5. **ICT's own selection rules are precise enough to code, but none is independently validated:**
   - low-hanging fruit first;
   - the IRL↔ERL alternation;
   - turtle soup conditioned on premium/discount;
   - high- vs low-resistance liquidity runs;
   - "priming" of relative equal highs;
   - a purge counts only if price moves away;
   - an MSS counts only after a purge;
   - the PDH/PDL close rules for daily bias.

   Implement them as small, ledger-calibrated features.
6. **Best single improvement: a candidate (shadow) ledger.** It grades every candidate level against the distance-matched baseline and learns a bounded lift per ICT feature (EQ, tests, tier, inner/outer, session, round number, ERL/IRL, phase, daily-bias alignment, path resistance). The chart then tells the trader which ICT claims hold on this symbol. The engine re-weights itself, and the "selection edge" over the average candidate becomes measurable.

---

## 1. Concepts: precise definitions and parameters

ICT primary-source quotes are timestamped in the Quarter Sequence study pages (they link each quote to the lecture timestamp) and in the 2022 Mentorship notes (Tanja, Forex Factory attachment). "Ep." = 2022 Mentorship episode.

### 1.1 Buy-side / sell-side liquidity (BSL / SSL)
- **Definition (ICT).** "Liquidity is buy orders and sell orders"; "the open interest of buyers and sellers ... at or near specific price levels". Buy-side liquidity sits **above old highs**: short sellers' protective buy stops plus breakout buy orders. Sell-side liquidity sits **below old lows**. "A single point of reference" (one old high) is enough to form a pool (Liquidity Purge & Revert lecture, 2020, 5:09). You need no order book: "where would my protective buy stop be if I were short?" (Core Content M04 Liquidity Pools, 4:48).
- **Algorithm.** Pool = unswept swing extreme. BSL price = swing high; zone = [high, high + depth]. Swept when `high > level` (a strict trade-through; ICT: "it does not need to close above that", Ep. 3, 13:47).
- **Draw use.** "Algorithms are looking to draw the market to those stops" (Ep. 2). Price is drawn to the obvious, unswept pools.

### 1.2 Equal highs/lows and *relative* equal highs/lows
- **Definition (ICT).** "Multiple candles or levels that look very close to one another in height or depth". "It doesn't make a difference if it's exactly or off by one or two pips ... if it looks close enough" (2017, 8:08). ICT gives no numeric tolerance. Practitioner settings: 0.05-0.1% of price, a few ticks, or 0.10-0.15 ATR.
- **Reading.** Equal highs are **liquidity, not resistance**: "smooth edges like to be made jagged" (2023, 2:33:47). Each test adds stops (shorts sell the second touch with a stop just above).
- **"Priming" (ICT 2024 Mentorship L1, 1:15:22).** When the **left** of two relative equal highs is slightly **higher** than the right, ICT rates it "very very high probability" that price takes them (not necessarily this session). Mirror for lows: left slightly lower. The idea is that the lower second high reassures shorts, who put stops just above the pair.
- **Algorithm.** Merge a new pivot into an existing same-kind unswept pool when `|p_new - p_pool| <= tol` (tol = 0.10-0.15 ATR). The pool price moves to the outermost print. `eqCount++`. Priming flag: for BSL, `p_new < p_pool` (the second print is lower); for SSL, `p_new > p_pool`.

### 1.3 Old highs/lows hierarchy: STH → ITH → LTH (ICT 2022 Ep. 8 and Ep. 12)
- **Short-term high (STH).** The 3-candle swing: a middle candle with a lower high on each side. It is confirmed when the candle after it closes.
- **Intermediate-term high (ITH).** A STH with a lower STH on each side, or a high made when price trades back up to rebalance an imbalance ("the main one").
- **Long-term high (LTH).** An ITH with a lower ITH on each side. It is "generally going to be linked to a higher time frame, daily chart" (Ep. 12, 29:39).
- **Use.** Breaks of ITH/ITL are "a significant break in market structure". The higher the order of the swing, the bigger the pool and the more important the draw.
- **Algorithm.**
  - `sth = ta.pivothigh(high, 1, 1)`.
  - Keep the last three STHs. If `sth[-2] > sth[-3]` and `sth[-2] > sth[-1]`, then `sth[-2]` is an ITH.
  - Apply the same test on the ITH sequence to get an LTH.

### 1.4 Internal vs external range liquidity (IRL / ERL) and the delivery cycle
- **Dealing range.** From an old (swing) low to an old (swing) high, i.e. one leg.
- **ERL.** The stops beyond the range high and below the range low.
- **IRL.** ICT, Ep. 3 (35:04): "short-term lows or short-term highs inside a price leg that we're retracing back into ... or an imbalance in that same range of price action". So IRL is the FVGs, OBs **and** the short-term swing pools inside the leg.
- **Cycle (community codification of ICT).**
  - After price reaches ERL (sweeps an external high), it is drawn back to IRL (an FVG/OB/STL inside the leg).
  - After IRL is reached (rebalanced), it is drawn to the next ERL.
  - ICT uses it to manage trades: "partials, internal range, external range, your trade" (Ep. 6, 45:49): partials at the FVG or 50% of the range, the full target at ERL (Ep. 4).
- **Algorithm.**
  - Dealing range = the STF (or execution) swing range `[rngL, rngH]` (`f_structure` already returns it).
  - ERL = liquidity at or beyond `rngH - tol` / `rngL + tol`. IRL = arrays and pools strictly inside.
  - Phase state:
    - `ERL_TAKEN(side s)` when an ERL pool is swept;
    - `IRL_TAKEN(side s)` when an IRL array is reached (its CE is touched).
  - Next-draw preference:
    - after `ERL_TAKEN(s)`: IRL on side −s;
    - after `IRL_TAKEN(s)`: ERL on side −s, in the dealing-range trend direction.

### 1.5 Premium / discount
- **Definition.** Premium = above 50% of the dealing range; discount = below it (Ep. 2). ICT also says "any time the market trades above an old high it's a short-term premium; into an old low, a discount" (Ep. 14).
- **Use for the draw.**
  - A run below an old low **while in discount** "is probably going to be a turtle soup buy"; above an old high in premium, a turtle soup sell (Core Content M1 Equilibrium vs Premium, 7:14; vs Discount, 40:16).
  - Buy in discount and target premium ERL (and the mirror for sells).
  - This is ICT's rule for "will it keep going or reverse after taking the low".
- **Algorithm.** `pos = (close - rngL) / (rngH - rngL)`. Use it to condition (a) the post-sweep read and (b) the IRL/ERL preference.

### 1.6 Low-hanging fruit vs major liquidity
- **ICT.** "Look for low hanging fruit, aim for the easiest target to get to, aka the next spot where previous stops are waiting" (Ep. 3). "Pick the lowest hanging fruit and be happy when it hits that" (Ep. 14). Partials at the first target (Ep. 14), move the stop to breakeven at 75% of the expected range (Ep. 41). The major draw (HTF ERL) is the "objective".
- **Algorithm.** Low-hanging fruit = the nearest unswept pool on the draw side. Major = the strongest draw-side HTF pool, ranked without proximity (the engine already computes this "HTF objective").

### 1.7 High-resistance vs low-resistance liquidity runs (Core Content M1 "Liquidity Runs", 7:26 and 19:25)
- **High-resistance run.** A move back to an old high that sits behind every lower high since (counter-trend, with a lot of price action in the way). ICT calls it "the least probable trading condition to look for longs". It generally needs news (NFP, FOMC) to knock through.
- **Low-resistance run.** In the trend direction, each new low has little in the way: "like a hot knife through butter".
- **Algorithm.** Path resistance to target T = Σ over unmitigated **opposing** PD arrays (e.g. bearish FVG/OB/breakers for a BSL target) and **counter-trend swing points** that lie between price and T, weighted by quality and timeframe. Low resistance = no opposing arrays in the path.

### 1.8 Sweep vs run; purge; market structure shift
- **ICT names.**
  - Run = a liquidity run, raid or stop run.
  - Sweep (Ep. 23 per notes) = a **shallow run through liquidity that reverses**.
  - Run = goes through and **continues**.
  - Purge (2020) = run plus revert. The stops count as purged "only if we start to move away from it" (21:31).
  - An MSS is counted "only on the basis of a liquidity purge" (22:02).
- **MSS (Ep. 6, 20:52).** After price runs above an old high, it "breaks below ... and takes out a short-term low prior to that run". A wick is enough to take liquidity. For the MSS ICT wants a **body close** beyond the short-term swing ("a wick that pokes through and comes back is not all that convincing", Ep. 6, 19:39) and **displacement** (not "a little lethargic little move").
- **Codeable classification of a BSL sweep at bar close** (mirror for SSL):
  - HOLD: `close >= level + k*ATR` (k about 0.25; practitioner breakout rule: close beyond by 0.25 ATR and hold 2 bars).
  - REJECT: `close < level` (back inside).
  - NEUTRAL: otherwise.
  - REJECT+MSS: REJECT, then within N (about 5-10) bars a displacement body close below the last short-term swing low that existed before the sweep.

### 1.9 Turtle soup (ICT's borrowed name for a false breakout)
- **Original (Connors & Raschke, *Street Smarts*, 1995), long side:**
  1. Today makes a new 20-day low.
  2. The prior 20-day low was made **at least 4 sessions earlier**.
  3. Buy stop 5-10 ticks above the prior 20-day low, good for today only.
  4. Stop 1 tick under today's low.
- "Plus One" variant: the prior low is at least 3 bars old, day one closes at or below the old low, and entry is the next day.
- The age rule removes trend continuation, where most new lows break a low made a day or two before.
- **ICT version.** "A fake break below an old low and rally higher" (Ep. 7, 25:28). It is context-dependent (discount), requires an aggressive response and a later MSS, and need not even make a lower low (M04 Rejection Block, 13:56).

### 1.10 Trendline liquidity ("phantom trend line")
- **Definition.** Stops resting just beyond an obvious diagonal: below a rising line with three or more touches. ICT's term is the "phantom trend line" (2023). He also says "everybody's going to have a different diagonal trend line" (2024, 2:23:52) and that the only trendline he likes is the horizontal line across equal highs/lows (2017, 7:56).
- **Algorithm (if ever built).** Take the last three or more ascending pivot lows with collinearity residual below 0.15 ATR. The SSL level is `line(t)`, updated each bar. Swept when `low < line(t)`.
- **Recommendation.** Not worth building. Evidence is none and the definition is not unique.

### 1.11 Inducement (IDM): a retail SMC term, not ICT's
- ICT uses "induce" only as an ordinary verb. SMC definition (the most codeable version):
  1. After a BOS, take the first candle whose low is below the previous candle's low.
  2. Follow the lower lows until a candle makes none. That low is the **IDM**, fixed when the candle closes.
  3. It is **taken** when a later candle trades below it (a wick counts).
  4. A POI (OB/FVG) further back is "valid" only after its IDM is taken.
  5. If a new BOS comes first, the IDM moves to the new break's first pullback.
- Definitions disagree (first pullback before vs after the break).
- **DOL relevance.** The IDM is literally the first liquidity met on the retrace (low-hanging fruit) in front of the POI.

### 1.12 Liquidity voids / runs, opening gaps (out of scope; PD-array domain)
Liquidity void = a multi-candle one-directional run (stacked FVGs), expected to rebalance. NWOG/NDOG = Friday close → Sunday open gap; its CE acts as a magnet. Only noted here; the FVG/gap study should cover them.

### 1.13 When is a pool "spent"?
- ICT: "Once price has traded through a pool, its orders are filled, so the next untouched high or low becomes the one to watch." A wick is enough.
- Evidence (Osler) shows stop orders are spread over a band beyond the level, roughly 1-10 pips beyond a round number on FX, not at one price. A 1-tick poke triggers only the nearest stops.
- Practitioner observation: stops placed just beyond the sweep wick get "re-swept" often; stops beyond the swing itself cost 1.5-2x the risk but are re-swept less (Quantzee SFP page, NIFTY; weak).
- So "spent" is really a gradient. Penetration depth matters, and the empirical depth distribution can be learned per chart.

### 1.14 How ICT chooses the draw on liquidity (DOL)
1. Top-down: start on the daily chart (Ep. 14). Weekly → daily → 4H/1H give the bias and the draw (the 2022 model: "name the higher timeframe draw ... that sets the bias").
2. The draw is the **unswept** obvious pool or the unfilled imbalance in the direction the HTF is delivering: "Algos reach for liquidity or to fill imbalances" (Ep. 14). Example: long bias because "relative equal highs were left untapped on NQ" (Ep. 29).
3. Premium/discount and IRL/ERL phase decide whether the next leg is a retracement (to IRL) or an expansion (to ERL).
4. Time: raids are expected in the killzones (London 2-5 am NY, NY 7-10 am, Asia 7-9 pm in notes; 8:30-11 sweet spot). No trades 12-1 pm. PM session from 1:30 pm.
5. "If you can very easily communicate a bullish stance and it is a hard stretch to sell it bearish, that's high probability. If it can go either way, you will regret it" (Ep. 8).

### 1.15 Daily bias from the previous day's range (community codification; edgeful / TTrades-style)
Let H2/L2 be the high/low of day t−2, H1/L1/C1 the high/low/close of day t−1 (yesterday).
- **Bullish** if `C1 > H2` (closed above the prior high: continuation, draw = H1, i.e. today's PDH). Also bullish if `L1 < L2 and C1 > L2` (swept the prior low and closed back inside: draw = H1).
- **Bearish** mirrors: `C1 < L2`, or `H1 > H2 and C1 < H2`.
- **Neutral/inside** otherwise.
- Same rule on weekly bars for PWH/PWL.

---

## 2. Evidence (numbers and sources)

| # | Claim tested | Data | Result | Grade |
|---|---|---|---|---|
| E1 | Stops cluster just beyond round numbers; take-profits at them | Osler, FRBNY SR125 / J. Finance 58(5) 2003; RBS order book, Sep 1999-Apr 2000; 9,667 conditional orders (avg $5.8 m), USD/JPY, GBP/USD, EUR/USD | About 8.7% of orders at prices ending "00" vs about 1% uniform. Take-profit: 9.3% exactly at 00; stop-loss: 4.4%. Stop-loss **buy**: 14.4% at 01-10 above 00 vs 7.4% at 90-99 below (p = 0.029). Stop-loss **sell**: 10.0% at 90-99 vs 5.1% at 01-10. Take-profit orders: no asymmetry. Rates bounce 4.6 pp more often at round numbers (actual FX) | strong |
| E2 | Crossing stop clusters accelerates price (cascade) | Osler, "Stop-loss orders and price cascades", FRBNY SR150 / JIMF 2005; 9,655 orders ($55 bn); quotes 1996-98 | Executed stop buys: 14.3% in [01, 10] vs 6.9% in [90, 99]. Around 50: stop buys 18.1% in [51-60] vs 6.3% in [40-49]; stop sells 16.3% in [40-49] vs 8.0% in [51-60]. After crossing a round number, extra move vs reversal (MVCR − MVRV): +0.27 to +2.35 hundredths of a percent at 15 min to 2 h (DEM 15 min 1.12, JPY 2 h 2.35). Significant for at least 2 h, **not** at 1-2 days (signs turn negative). Example: once below ¥129.80, USD/JPY fell "within seconds" to ¥129.40 | strong |
| E3 | S/R = depth on the book | Kavajecz & Odders-White, RFS 17(4) 2004; NYSE SuperDOT | Support = "lowest bid reached **at least twice**" in the window (i.e. equal lows). 84% of the technical-level vs depth series are cointegrated at 5%. S/R significant for 49-73% of stocks with the book mode as the dependent variable. Technical levels **locate** existing depth; limit orders do not cluster at them afterwards (7.6% / 9.2% within $0.25) | strong |
| E4 | Prior bounces raise the next bounce probability | Garzarelli et al., Sci. Rep. 4:4487 (2014); 9 LSE stocks, 2002 tick data, 45-180 s scales | p(bounce \| b_prev) > 0.5 and **increases** with b_prev. Independence rejected p < 0.0001 at 45/60/90 s; not significant at 180 s. Shuffled series ≈ 0.5 | strong (HF only) |
| E5 | Same, intraday, with decay | Chung & Bellotti, arXiv 2101.07410 (2021); EURUSD, LLOY, Brent 1-min 2018 | Bounce probability rises with b_prev. **Decay**: EURUSD, a 1-bounce level decays to 0.5 at about a 350-min window, a 4-bounce level at about 900 min. Brent: a 1-bounce level drops **below** 0.5 beyond about 300 min (predicts penetration) | moderate |
| E6 | Equal highs/lows taken more than single swings? | Open-source TradingView script "Equal Highs & Lows Odds" (distance-matched); 2 years of 1H on EURUSD, GBPUSD, USDJPY, XAU, NQ, ES, BTC, ETH; tolerance 0.15 ATR; taken = trade-through within 24 bars at 0.5-1.5 ATR | EQ taken 63-82% vs ordinary swings 68-76% at the same distance. Reversal after the sweep 39-44% for both. "Equal" improves the odds by **< 1%** vs distance alone. USDJPY 15m example: 70% vs 70%, reversal 44% vs 45% | moderate |
| E7 | Sweeps → reversal (textbook) vs continuation | Mahadzva, SSRN 7430998 (2026), G10 FX intraday, walk-forward | "No evidence ICT/SMC works as literally taught." Three independent sweep mechanisms (EQH/EQL, OB, Asian range) agree in **65/66** fold-selections that a swept level predicts **continuation**. CHoCH+FVG retracement "reversal read should be faded". AUDUSD H1 p = 0.0074 but fragile (WFE 2.08) | moderate (single preprint) |
| E8 | SMC detectors predict returns | Tangirala, SSRN 7483658 (2026); S&P 500 daily 2010-2026; 44 detectors | Largest estimates: 11-12 bp over 10 days, both **liquidity-sweep** detectors, p ≥ 0.23. Concepts selected in-sample earn −31 bp OOS | moderate (negative) |
| E9 | PDH/PDL break → session direction | edgeful blog (YM, last 6 months, NY session 9:30-16:00 only) | PDH broken → session green 67% (open→close) / 81% (prior close→close). PDL broken → red 62% / 66%. Close beyond the broken level 56% / 56%. Friday 89% / 77%, Thursday 64% / 67% | weak-moderate (small, vendor) |
| E10 | Lower high → next-day PDL visit | Barot, SSRN 7359378 (2026), daily bars, 6 markets | A Friday lower-high is followed by a Monday visit of Friday's low more often than a higher-high Friday, in all 6 markets. Against a random Friday the lift is smaller but positive in all 6. About half the NQ/ES tags happen at the 17:00 CT Sunday open. The gap is **absent in 2024-25** on index futures. Buying the tag has no edge | moderate |
| E11 | FVGs as reaction levels | Barot, SSRN 7148099; 4 futures, 3 TFs, 7 yrs, about 40,000 FVGs | Reaction about **5 pp above a distance-matched random level**; not tradeable | moderate |
| E12 | Killzone filter for EQ sweeps | Backtrex blog (EURUSD + XAUUSD H1, 2019-24; sweep ≥ 3 pips, 70%-body confirmation within 2 bars, stop 5 pips beyond, target = opposite EQ) | Killzones only: 1,247 trades, 53.2% WR, PF 1.68. 24 h: 3,891 trades, 47.1% WR, PF 1.21 | weak (vendor) |
| E13 | Sweep significance across TFs | Quantzee (600+ annotated setups, NIFTY / FX) | 60-70% of 5-min sweep signals were not significant on the 1H chart of the same session. Retail stop padding of 0.15-0.3% moves risk outside the densest cluster | weak |
| E14 | Order-book clustering at round prices | Lallouache & Abergel, arXiv 1307.5440 (EBS EUR/USD, USD/JPY) | Limit orders still cluster at "old" round prices after a 10x tick reduction, creating barriers. Algos front-run clusters by one tick (digit 1/9) | moderate |
| E15 | ICT definitions | ICT lectures (2017-2024) via Quarter Sequence study pages; 2022 Mentorship notes | Definitions only: STH/ITH/LTH, IRL/ERL, sweep vs run, priming, high/low-resistance runs, turtle soup context. **No quantitative validation by ICT** | none (as evidence) |

**Net reading for the forecasting problem**
- **Where.** The obvious unswept pools are where stops are (E1-E3 strong). But the "equal" label adds almost nothing beyond distance (E6), and HTF/tier effects are untested. A distance/volatility model is the backbone. ICT features are small modifiers that must be **measured per chart**.
- **When.** Cascades after crossing last hours, not days (E2). Raids are more productive in killzones (E12, weak). Sweep effects on 5m charts are often noise on 1H (E13).
- **What next.** Continuation is the base case after a sweep (E2, E6, E7, E9). Reversal reads need context and confirmation, and even then may fade (E7).
- **Tests.** More prior bounces → more likely bounce on the next approach in the short run (E4, E5), decaying within hours. That argues against rewarding "tests" as extra magnitude for an H-bar touch target. This is the opposite of the folk "more touches = weaker level".

---

## 3. Engine gap analysis (line refs to baseline_v2.pine)

| Concept | Status | Where | What the engine does / differs |
|---|---|---|---|
| BSL/SSL from swings | present | 1753-1776 (pools), 623-624 (`touched`: strict `>`/`<` for liquidity) | Chart pivots `pivLen` = 5 each side (an ITH-like order, 5-bar lag). Zone depth `zoneATR` 0.20 ATR (93). Swept on trade-through. Matches ICT |
| Relative equal highs/lows | present | 95 (`eqTol` 0.10 ATR), 1104-1131 (`f_mergeAt`: outermost print, `eqCount++`, same-candle guard) | Good. No "priming" flag. Density weight `0.9*eqCount` (682) is large relative to evidence (E6: < 1%) |
| STH/ITH/LTH hierarchy | partial | 879-884, 923-925, 1779-1789, 506-516 (`f_tierW`) | Hierarchy proxied by timeframe (chart 0.25 / STF 0.45 / HTF 0.65) and prominence; no nested-pivot ITH/LTH on the chart TF |
| PDH/PDL, PWH/PWL, Asia/London/NY H/L | present | 945-961, 948-950, 1790-1809 | Exact print anchors; registry re-entry (1824-1852). Good |
| Stacked pools / inner = inducement | present | 1230-1251, 684-685 (`inner` ×0.70) | Outermost is the draw. Consistent with Osler cascades (crossing the inner cluster accelerates price into the outer one). ICT's "low-hanging fruit" would favour the inner one; leave it to calibration |
| IRL / ERL classification and cycle | missing | — | `htfEQ` and `dayEQ` are only confluence anchors (967-968, 1931). No range-relative class, no phase state |
| Premium / discount in the draw | partial | 2324-2333 (Terminal panel display only), 968 | Shown, not used in D, scoring or the post-sweep read |
| Low-hanging fruit vs major | partial | 661-667 (proximity + reach), 1984-1989 (HTF objective) | Both exist; the inner penalty leans "major". Acceptable |
| Sweep vs run (reversal vs continuation) | partial (likely miscalibrated) | 1580-1582 | Fixed: HOLD (`close > lv.top`) → +1, REJECT (`close < lv.price`) → −1, weighted by tier, half-life `liqHL` 24 (1535). Evidence E6/E7/E9 says continuation dominates; the REJECT = reversal sign is unvalidated and fixed |
| Purge + MSS confirmation | missing | 708-782 (bias), 1542-1547 (BOS) | MSS/CHoCH and sweeps are independent. No "MSS only after purge" logic and no purge alert |
| Turtle soup (age ≥ 4 bars, context) | partial | 1580-1582 | Sweeps are read, but with no level-age requirement and no premium/discount context |
| Inducement (IDM) | partial | 892-895 (`induceBar`: wick through 5-bar extreme, close back), 1230-1251 | Density feature plus inner pools. No IDM level (first pullback after BOS) |
| High / low resistance runs | partial | 1945-1947 (volume-profile path cost), 684 | Path cost uses volume only. No structural count of opposing arrays in the path |
| Trendline liquidity | missing | — | Not recommended (no evidence, ill-defined) |
| Tests (prior bounces) | present, questionable sign | 650-658 (test = within 0.30 ATR without taking, ≥ 3 bars apart), 682 (`0.35*min(tests,6)` adds magnitude) | E4/E5: more bounces → next approach bounces more (short-run), decaying over hours. For a strict trade-through hit within H bars, tests may lower the hit odds. Should be learned |
| When a pool is spent | present (binary) | 1583-1589 (removed on any trade-through), 1592-1596 (registry) | No depth gradient. Matches the decision history (hit = trade-through) |
| Stop depth beyond the level | partial | 93 (fixed 0.20 ATR), 1344 (invalidation buffer 0.10 ATR) | Not learned, not round-number aware |
| Round numbers | missing | grep finds none | Strongest-evidence stop locations (E1, E2, E14) are absent |
| Killzone timing of raids | present | 597-602 (`f_kzAff`), 971-976 (off-KZ hysteresis) | London raids Asia ×1.20 etc. Fixed multipliers; ledger-calibratable |
| ICT daily bias (PDH/PDL close rules) | missing | 1891-1894 (D = MTF structure, displacement, liqEvt) | No previous-day close-vs-range rule |
| DOL chosen top-down (HTF) | present | 1892 (`sV = 0.5*htfBias + 0.3*stfBias + 0.2*exeIB`), 1964-2035 | Draw-side-first selection with hysteresis. Good |
| Freshness / age decay | present | 668-673 | Matures then decays (half-life 4×150 bars). Consistent with E5 decay in spirit |
| Self-measurement | present (active DOL only) | 1426-1499, 1376-1382 (`f_calMult`, 4 families, distance-matched) | Excellent base. Only about 1 trial per H window, so per-feature learning is impossible. No candidate-level grading |
| SMT divergence | missing | — | Needs a second symbol; outside this domain |
| Liquidity void, NWOG/NDOG | missing | — | Belongs to the PD-array study |

---

## 4. Proposals (best first; max 10)

General Pine v6 notes for all specs:
- Pine has **no bitwise operators**. Operator classes are arithmetic, comparison, logical, ternary and history (`language/operators.md`). Encode feature sets as an int mask and decode with `int(math.floor(mask / math.pow(2, b))) % 2 == 1`, or use separate bool fields.
- Every new state update runs inside `if barstate.isconfirmed` (the ENGINE block, 1518).
- Every new function is declared before its first use. Globals it reads must be declared above it.
- No new `request.security` calls are needed except where noted. Current count is about 6 of 40.

### ICT-1 (P1): Candidate ledger with feature-level lift ("which ICT claims hold on this chart")
- **Why.** The ledger grades only the active DOL (about one trial per H bars), so it can calibrate 4 families at most (1376-1382). E6 shows ICT labels add little beyond distance on average, and that varies by market. Grade all candidates against the same distance-matched baseline (`f_potBase`, 1314-1322) and learn a bounded lift per feature. This is the measurement backbone for ICT-2 through ICT-8. It also shows the trader a "selection edge" (the DOL's lift over the average candidate's lift), which is the honest answer to "does the scoring help".
- **Inputs (G_ACC).**
  - `bool useFeat = input.bool(true, "Feature Calibration (ICT features)")`
  - `int featN0 = input.int(40, "Feature Prior Strength (n)", minval = 5)`
  - `float featB = input.float(0.15, "Feature Bound ±", minval = 0.0, maxval = 0.4, step = 0.01)`
- **Type** (after `Trial`, around 396). Add `int lastProbe = -100000` to `Level`.
  ```
  type Probe
      int   lvId
      int   side
      bool  liq
      float edge
      int   bar0
      float pBase
      int   mask
  ```
- **State** (STATE, around 1080): `var array<Probe> probes`. `const int NF = 14`. `var array<int> fN = array.new<int>(NF + 1, 0)`, `fK` likewise, `var array<float> fE = array.new<float>(NF + 1, 0.0)`. Index NF holds all probes.
- **Feature bits.** All are computed at snapshot from the Level plus engine state.

  | Bit | Feature | Rule |
  |---|---|---|
  | 0 | EQ | `eqCount > 0` |
  | 1 | PRIMED | EQ and second print inside; set in `f_mergeAt` when `not outer and countEq` |
  | 2 | TESTED | `tests >= 2` |
  | 3 | INNER | `inner` |
  | 4 | KEY | `src >= 6` |
  | 5 | SESSION | `src 3-5` |
  | 6 | MTF | `src 1-2` |
  | 7 | DRAW | `side == dirSide` |
  | 8 | KZ | `f_kzAff(kz, src) > 1` |
  | 9 | RN | ICT-3 |
  | 10 | ERL | ICT-4 |
  | 11 | PHASE | ICT-4 |
  | 12 | DBIAS | ICT-6 |
  | 13 | LOWRES | ICT-5 |

- **Snapshot** (in step 17, after `lv.evaluate`, inside `inCalc` and past `warmup`). For each `lv` in the pool with `bar_index - lv.lastProbe >= H` and `0 < dist/atr <= maxATR` and `probes.size() < 256`:
  - push `Probe.new(lv.id, lv.side, lv.isLiquidity(), lv.nearEdge(), bar_index, f_potBase(dist, lv.side), f_mask(lv))`;
  - set `lv.lastProbe := bar_index`.

  One probe per level per H window keeps each level's records non-overlapping.
- **Grading** (new step 2b, right after the Trial loop at 1550-1557, before sweeps delete levels). For each probe with `bar_index > bar0`:
  - `hit = liq ? (side == 1 ? high > edge : low < edge) : (side == 1 ? high >= edge : low <= edge)`;
  - if `hit` or `bar_index - bar0 >= H`, book it: `y = hit ? 1 : 0`; for each set bit b, and for NF: `fN[b] += 1; fK[b] += y; fE[b] += pBase`;
  - remove the probe.
- **Lift.**
  - `lift_b = ((fK[b] + 2) / (fE[b] + 2)) / ((fK[NF] + 2) / (fE[NF] + 2))`.
  - Shrink with `w = fN[b] / (fN[b] + featN0)`: `m_b = f_clamp(1 + w*(lift_b - 1), 1 - featB, 1 + featB)`.
- **Apply** (step 17 multiplier loop, 1940-1947): `lv.mult *= f_clamp(Π_{b ∈ mask(lv)} m_b, 0.75, 1.30)`.
- **UX** (Terminal, Accuracy = Full). A "FEATURE LIFT" block, e.g. `EQ ×1.02 (n 214) · KEY ×1.09 · TESTED ×0.93 · DRAW ×1.11`. A "CANDIDATES" row with the all-candidate hit % vs baseline. A "SELECTION EDGE" row with the DOL's lift divided by the candidate lift.
- **Cost.** At most 256 probes × O(1) per bar, booking O(NF). Negligible.
- **Evidence.** Moderate: the method is standard distance-matched lift; motivated by E4-E6 and E11.
- **Risk.**
  - Overlapping probes on different levels share one price path, so variance is understated. Shrinkage and bounds mitigate this. A block-cluster variance like `f_book` (1463-1469) could be reused.
  - Feedback loop: lifts change scores, which change which levels exist. Grade all candidates regardless of score to avoid selection bias.
- **Effort.** M.

### ICT-2 (P1): Post-sweep outcome learner (sweep vs run), purge+MSS event, honest sweep alert
- **Why.** `liqEvt` (1580-1582) assumes REJECT = reversal and HOLD = continuation, fixed. E6/E7/E9 say continuation dominates, and E2 says crossing stop clusters accelerates price for hours. ICT himself conditions the read on premium/discount and a subsequent MSS. Learn the conditional probability per chart and feed it into D.
- **Inputs (G_FLOW).**
  - `bool swLearn = input.bool(true, "Learn Sweep Outcomes")`
  - `int swWin = input.int(8, "MSS Window After Sweep (bars)", minval = 2, maxval = 30)`
  - `float holdATR = input.float(0.25, "Hold Distance (ATR)", step = 0.05)`
- **Type.**
  ```
  type SweepRec
      int   side      // +1 BSL swept, -1 SSL swept
      int   cls       // 0 HOLD, 1 REJECT, 2 NEUTRAL, 3 REJECT+MSS
      int   ctx       // 1 if swept at the "turtle soup" extreme (BSL in premium / SSL in discount), else 0
      float lvl
      float cTgt
      float rTgt
      float mss       // opposite short-term swing captured at sweep time
      float pModel    // model P(continuation first)
      float pen       // penetration beyond lvl in ATR (also used by ICT-7)
      int   bar0
      float tier
  ```
- **State.** `var array<SweepRec> swRecs` (cap 64). `var array<float> swN = array.new<float>(8, 0.0)`, `swC`, `swP` (index `cls*2 + ctx`). `var int purgeSide = 0`.
- **Creation** (inside 1580, where `hit and lv.isLiquidity()`):
  - `cls`: HOLD if `side == 1 ? close >= lv.price + holdATR*atr : close <= lv.price - holdATR*atr`; REJECT if `side == 1 ? close < lv.price : close > lv.price`; else NEUTRAL.
  - `ctx` from `pos = (close - stfRL) / (stfRH - stfRL)`: BSL → `pos >= 0.5`; SSL → `pos <= 0.5`.
  - `cTgt` = nearest same-side pool beyond `lv` (scan the pool for the same kind and the next price beyond `lv.price`), else `lv.price + side*1.0*atr`.
  - `rTgt` = nearest opposite-side pool, else `close - side*1.0*atr`.
  - `pModel = f_race(|cTgt - close|, |rTgt - close|, potSig, 0)`, so the learner measures excess continuation over the distance-implied odds.
  - `mss = side == 1 ? nz(obSwingL, exeRL) : nz(obSwingH, exeRH)` (capture now; `obSwing*` is reset to `na` on a BOS at 1667/1710, so fall back to the execution-TF swing).
  - `pen = (side == 1 ? high - lv.price : lv.price - low) / atr`.
- **Per-bar update** (step 2c):
  - Upgrade REJECT → REJECT+MSS if within `swWin` bars `(side == 1 ? close < mss and dispDn : close > mss and dispUp)`. On upgrade, set `purgeSide := -side` and raise the purge alert.
  - Resolve the race: continuation if `side == 1 ? high > cTgt : low < cTgt`; reversal if `side == 1 ? low < rTgt : high > rTgt`. If both happen on the same bar, use the bar-path rule from `f_step` (1441). Expire undecided after H bars (not booked).
  - Book: `swN[i] += 1; swC[i] += cont ? 1 : 0; swP[i] += pModel`.
- **Use in D.** Replace the fixed `evt` at 1581 with `pC = f_sigm(f_logit(pModel) + prior[cls] + dl[i])`, where `dl[i] = f_logit((swC[i] + κ*p̄) / (swN[i] + κ)) - f_logit(p̄)`, `p̄ = swP[i] / swN[i]`, κ = 20 (the same pattern as `f_raceAdj`, 1367-1371). Priors (logit): HOLD +0.4, REJECT −0.2, NEUTRAL 0, REJECT+MSS −0.4. Then `liqEvt := f_clamp(liqEvt + lv.side * (2*pC - 1) * lv.tier(), -1, 1)`. On an MSS upgrade, add the difference between the new and old `pC` contribution.
- **UX and alerts.**
  - Terminal row: `SWEEP→ REJ: rev 58% (n 41) · HOLD: cont 66% (n 33) · PURGE+MSS: rev 61% (n 12)`.
  - Add `P(cont)` to the existing sweep alert text.
  - New `alertcondition(purgeEvt, "Liquidity Purge + MSS", ...)`.
- **Evidence.** Moderate (E2, E6, E7, E9). ICT conditioning (premium/discount, MSS) has none.
- **Risk.**
  - Sparse cells: 8 cells; most charts reach n ≥ 30 in 2-3 cells within 5,000 bars. Fall back to priors via κ.
  - D-flip churn if `liqEvt` swings. Keep the existing half-life and hysteresis.
- **Effort.** M.

### ICT-3 (P1): Round-number stop clusters (confluence + stop-depth extension)
- **Why.** The strongest evidence in the whole domain (E1, E2, E14) is that stops sit **just beyond** round numbers, take-profits sit **at** them, and crossings cascade. The engine has no round-number concept.
- **Inputs (G_LIQ).**
  - `string rnMode = input.string("Auto", "Round Numbers", options = ["Off", "Auto", "Manual"])`
  - `float rnMan = input.float(0.0, "Round Step (Manual)", minval = 0.0)`
  - `bool rnDepth = input.bool(true, "Extend Pools Past Nearby Round Numbers")`
- **Series** (no `request.security`). Daily ATR proxy `atrD = nz(atrSlow) * math.sqrt(math.max(1.0, 86400.0 / chartS))`, then:
  ```
  bool newDayRN = timeframe.change("D")   // evaluated on every bar at global scope (v6 `or`/`and` short-circuit, so never call it inside a condition)
  var float rnStep = na
  if rnMode != "Off" and (na(rnStep) or newDayRN)
      rnStep := rnMode == "Manual" and rnMan > 0 ? rnMan : math.pow(10, math.floor(math.log10(math.max(2.0 * atrD, syminfo.mintick * 10))))
  ```
  Spot checks: EURUSD daily ATR ≈ 0.007 → 0.01 (the "big figure"). USDJPY ≈ 1 → 1.00. ES ≈ 60 → 100. NQ ≈ 300 → 100. XAU ≈ 40 → 10. BTC ≈ 2,500 → 1,000. Half step = `rnStep / 2` (Osler's "50" levels).
- **Confluence** (step 17 anchors, 1930-1933). Push `math.ceil(close/hs)*hs` and `math.floor(close/hs)*hs` for `hs = rnStep/2`, and the same for `rnStep`.
- **Stop depth** (where BSL/SSL zones are built: 1762, 1774, 1848). For BSL: `R = math.ceil(price / hs) * hs`. If `R - price <= 0.35*atr`, then `top := math.min(price + 0.6*atr, math.max(top, R + 0.10*hs))`. Osler: stop buys cluster in the first 10% of the step above the round number. Mirror for SSL with floor. The hit rule is unchanged (still a trade-through of `price`), so the decision history is respected. The zone is drawn where stops actually rest.
- **Feature bit RN** (ICT-1): the pool lies within 0.35 ATR inside a round number, so it is measured.
- **Evidence.** Strong.
- **Risk.**
  - The auto step can be off by 10x on exotic symbols (Manual override).
  - Zones look deeper. The 0.6 ATR cap prevents bloat.
  - It is a confluence-domain overlap: coordinate with the confluence study to avoid double counting.
- **Effort.** S.

### ICT-4 (P2): IRL/ERL delivery cycle plus dealing-range premium/discount
- **Why.** This is ICT's core rule for "next draw" (1.4, 1.5). The engine has no notion of where a level sits in the dealing range, or of what was delivered last.
- **Inputs (G_FLOW).**
  - `string drSrc = input.string("STF", "Dealing Range", options = ["HTF", "STF", "Execution"])`
  - `float kPhase = input.float(0.12, "IRL/ERL Phase Weight", step = 0.01)`
  - `float kPD = input.float(0.10, "Premium/Discount Weight", step = 0.01)`
- **State.** `var int phase = 0` (1 ERL taken, 2 IRL tagged), `var int phaseSide = 0`, `var int phaseBar = na`. `rngH`/`rngL` come from the selected `f_structure` output (`stfRH`/`stfRL`, etc.).
- **Classify** (helper before `evaluate`): `f_isERL(Level lv) => lv.isLiquidity() and (lv.side == 1 ? lv.price >= rngH - 0.1*atr : lv.price <= rngL + 0.1*atr)`. Everything else (arrays, inner pools) is IRL.
- **Transitions** (step 3):
  - When a liquidity hit is ERL: `phase := 1; phaseSide := lv.side; phaseBar := bar_index`.
  - When an array (`kind >= 2`) inside the range reaches `fill >= 0.5` or is hit: `phase := 2; phaseSide := lv.side`.
  - The phase expires after H bars.
- **Multipliers** (step 17, bounded):
  - `phase == 1`: IRL levels with `side == -phaseSide` get ×(1 + kPhase). ERL with `side == phaseSide` gets ×(1 − kPhase/2), **unless** the sweep was classified HOLD by ICT-2 (a run, not a sweep).
  - `phase == 2`: ERL with `side == -phaseSide` gets ×(1 + kPhase).
  - Premium/discount, with `pos = (close - rngL) / (rngH - rngL)`:
    - if `htfBias == 1` and `pos < 0.5`: BSL ERL ×(1 + kPD*(0.5 - pos)*2);
    - if `htfBias == 1` and `pos > 0.5`: IRL arrays below ×(1 + kPD*(pos - 0.5)*2);
    - mirror for bearish.
- **Feature bits** ERL and PHASE (consistent with the phase) feed ICT-1, so the fixed k values get replaced by learned lifts.
- **UX.** Tag the target `ERL`/`IRL` in the HUD. Panel row `DELIVERY: ERL ▲ taken → IRL`.
- **Evidence.** None/weak (ICT teaching only). Fully ledger-measurable.
- **Risk.**
  - Overlap with D (both encode trend). Keep k small.
  - The range definition matters: STF swings update late. Use the confirmed `[1]` values the engine already has.
- **Effort.** M.

### ICT-5 (P2): Structural path resistance (ICT high- vs low-resistance liquidity runs)
- **Why.** ICT says a counter-trend run to an old high behind lower highs and opposing arrays is the least probable. The engine's path cost uses only volume (1945-1947).
- **Algorithm** (step 17, before `evaluate`). For each candidate `lv` with side s and near edge e:
  - `res = Σ over pool levels o` with `o.isArray()` and `o.side == s` and the opposite direction. For s = +1, o is a bearish array (kinds 3, 5, 7): bear FVG/OB/BRK above price. Count those whose near edge lies strictly between `close` and `e`.
  - Weight: `w = o.qual * (o.src == 2 ? 1.5 : 1.0)`.
  - Add 0.5 for each **counter-trend** swing pool of the same side between price and e when `htfBias == -s`, i.e. the lower highs in a downtrend.
  - Multiplier `lv.mult *= f_clamp(1.0 / (1.0 + 0.12*res), 0.70, 1.0)`.
  - Set feature bit LOWRES when `res == 0 and dist > 1 ATR`.
- **Cost.** O(n²), n ≤ 40 → ≤ 1,600 compares per `inCalc` bar. Acceptable. Can be sped up by pre-sorting near edges per side.
- **Evidence.** Weak (ICT; analogous to the volume path cost).
- **Risk.** Double-penalising counter-draw targets, which are already ×`ctrMult`. Calibration via LOWRES mitigates this.
- **Effort.** S.

### ICT-6 (P2): ICT daily (and weekly) bias from previous-range closes
- **Why.** This is the most common codeable ICT/derivative "daily bias", and the engine's D has no previous-range term. Evidence: E9 (continuation after PDH/PDL break) and E10 (a lower high → next-day PDL visit lift, small, regime-dependent).
- **Algorithm** (next to 956-961; capture the old values before overwriting):
  ```
  var float pPDH = na
  var float pPDL = na
  var int   dBias = 0
  if pdNew
      if not na(aPDH) and not na(aPDL)
          float c1 = close[1]
          dBias := c1 > aPDH ? 1 : c1 < aPDL ? -1 : (pdL < aPDL and c1 > aPDL) ? 1 : (pdH > aPDH and c1 < aPDH) ? -1 : 0
      pPDH := aPDH
      pPDL := aPDL
  // then the existing: aPDH := pdH / aPDL := pdL
  ```
  At the first bar of day t, `aPDH`/`aPDL` still hold day t−2's range, `pdH`/`pdL` are day t−1's, and `close[1]` is day t−1's close. All are confirmed history, so it does not repaint. Do the same with W for `wBias`.
- **Use.**
  - Add `wDB * dBias` (input, default 0.15) to `sV` (1892).
  - Key-level multiplier: `src == 6 and side == dBias` → ×1.08; opposite → ×0.95.
  - Feature bit DBIAS feeds ICT-1.
  - Show `DAY ▲ (C > PDH)` in the Terminal panel.
- **Evidence.** Weak-moderate.
- **Risk.**
  - The 24 h day boundary vs session-based definitions (edgeful uses the NY session only). Make the session optional.
  - Regime decay (E10: absent in 2024-25). Calibration handles that.
- **Effort.** S.

### ICT-7 (P3): Learned stop depth (zone depth and invalidation buffer from observed sweep penetration)
- **Why.** "How deep do stops sit?" is answerable per chart. Osler (E1/E2) shows stops are spread over a band beyond levels. The engine uses fixed 0.20 ATR zones (93) and a 0.10 ATR invalidation buffer (1344).
- **Algorithm.** From ICT-2, push `pen` (in ATR) of every REJECT sweep into `var array<float> penArr` (cap 300). When `penArr.size() >= 30`:
  - `q50 = penArr.percentile_linear_interpolation(50)`, `q80 = ...(80)`;
  - new pools use `wPx = f_clamp(q50, 0.05, 0.6) * atr`;
  - `f_invalidation` uses `buf = f_clamp(q80, 0.05, 0.8) * atr`, so the stop sits beyond the typical stop-hunt depth.
  - Terminal: `SWEEP DEPTH q50 0.14 · q80 0.31 ATR`.
- Optional, off by default: a "tagged" state for pools swept shallower than 0.5·q50 that close back inside. Keep them as non-DOL-eligible context for H bars instead of deleting them. The hit definition is unchanged.
- **Evidence.** Moderate (concept, E1/E2); weak (parameters).
- **Risk.**
  - Survivorship: only REJECT sweeps measure depth, while HOLD sweeps go arbitrarily far. Use REJECT only.
  - Deeper buffers lower R:R readouts (honest).
- **Effort.** S.

### ICT-8 (P3): ICT swing hierarchy (STH → ITH → LTH) on the chart timeframe
- **Why.** It gives ICT's own pool-ordering inside the chart TF without extra requests, and an earlier ITH confirmation than `pivLen` = 5 in fast legs.
- **Algorithm.**
  - `sth = ta.pivothigh(high, 1, 1)` / `stl = ta.pivotlow(low, 1, 1)`.
  - Keep three-element rolling arrays of STH prices and bars. When a new STH arrives and the middle one is above both neighbours, it is an ITH. Push it into the ITH ring; when the middle ITH is above both neighbours, it is an LTH.
  - Create or merge a chart pool at ITH/LTH prices through `f_mergeLiq` (1133). Set `Level.ord` (new int field) to 2 or 3. STHs do not become pools (too noisy).
  - `f_tierW` gets the ord: chart ITH 0.30, LTH 0.40.
  - Feature bits ITH/LTH feed ICT-1.
- **Evidence.** None.
- **Risk.**
  - More merges and duplicates with `pivLen` pools. Rely on `f_findLiq` tolerance.
  - The ITH confirmation lag is variable.
- **Effort.** M.

**Considered and rejected.**
- Trendline/phantom-trendline pools: no evidence, and ICT says they are subjective.
- IDM as a separate level source: it overlaps with the inner pools, and the definition disputes are unresolved.
- SMT divergence: needs a second symbol and belongs to another domain.

---

## 5. Sources

- Osler, C. (2001/2003). *Currency Orders and Exchange-Rate Dynamics: Explaining the Success of Technical Analysis.* FRBNY Staff Report 125; *Journal of Finance* 58(5):1791-1819. https://fraser.stlouisfed.org/files/docs/publications/frbnysr/frbny_sr125.pdf · https://ideas.repec.org/a/bla/jfinan/v58y2003i5p1791-1819.html
- Osler, C. (2002/2005). *Stop-Loss Orders and Price Cascades in Currency Markets.* FRBNY SR150; *J. Int. Money & Finance* 24(2). https://icmaif.soc.uoc.gr/Year/8conf/docs/Osler-Price%20Cascades-03-03.doc (the newyorkfed.org host was unreachable from this session; the SR150 PDF lives at https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr150.pdf)
- Kavajecz, K. & Odders-White, E. (2004). *Technical Analysis and Liquidity Provision.* RFS 17(4):1043-1071. http://www.chesler.us/resources/academia/tech_anal_and_liquidity.pdf · https://papers.ssrn.com/sol3/papers.cfm?abstract_id=315660
- Garzarelli, F., Cristelli, M., Pompa, G., Zaccaria, A., Pietronero, L. (2014). *Memory effects in stock price dynamics: evidences of technical trading.* Sci. Rep. 4:4487. https://arxiv.org/abs/1110.5197
- Chung, K. & Bellotti, A. (2021). *Evidence and Behaviour of Support and Resistance Levels in Financial Time Series.* https://arxiv.org/abs/2101.07410
- Lallouache, M. & Abergel, F. (2013). *Tick Size Reduction and Price Clustering in a FX Order Book.* https://arxiv.org/abs/1307.5440
- Mahadzva, S. (2026). *Smart Money or Costly Folklore? A Systematic Evaluation of ICT/SMC Trading Rules in G10 FX.* SSRN 7430998. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7430998
- Tangirala, K. H. (2026). *Do Smart Money Concepts Predict Returns? Evidence from 44 Formalised Detectors on S&P 500 Daily Bars, 2010-2026.* SSRN 7483658. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7483658
- Barot, D. (2026). *Do Lower Highs Increase the Chance of a Previous-Day Low Visit? Evidence From 6 Markets.* SSRN 7359378. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7359378
- Barot, D. *Fair Value Gaps Work, Until You Try to Trade Them.* SSRN 7148099. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7148099
- "Equal Highs & Lows Odds: Are They Really Liquidity?" (open-source TradingView script, distance-matched test). https://www.tradingview.com/script/NvqGg3bD-Nambou-Equal-Highs-Lows-Odds-Are-They-Really-Liquidity/
- edgeful: *Why most traders get previous day's range levels completely wrong* (YM statistics). https://www.edgeful.com/blog/posts/previous-days-range-trading-mistake
- Quarter Sequence study pages (ICT quotes with lecture timestamps): https://quartersequence.com/the-study/ict-liquidity/ · https://quartersequence.com/the-study/ict-market-structure/ · https://quartersequence.com/the-study/ict-fair-value-gap/
- ICT 2022 Mentorship notes (Tanja): https://www.forexfactory.com/attachment/file/4435106?d=1681044827
- TradingFinder, ICT IRL/ERL: https://tradingfinder.com/education/forex/ict-internal-and-external-range-liquidity
- R2F, ICT 2022 model (low-hanging fruit first): https://www.r2ftrading.com/learn/ict-2022-model-explained
- Turtle soup rules: https://proea.app/en/blog/turtle-soup · https://audacity.capital/trading-guides/turtle-soup-trading/
- Inducement (SMC): https://proea.app/en/blog/inducement · https://www.theinnercircletraders.com/ict-inducement-idm/
- Quantzee: https://quantzee.com/anatomy-of-a-liquidity-sweep-the-four-bar-sequence-that-sepa/ · https://quantzee.com/what-is-a-breakout-in-trading-confirmation-rule/ · https://quantzee.com/swing-failure-pattern-bar-count-deadline/ · https://quantzee.com/smart-money-concepts-ict-trading-guide/
- Backtrex: *Liquidity Sweep Strategy: 5-Year Backtest Results.* https://backtrex.com/en/blog/liquidity-sweep-strategy-backtest-results
- LuxAlgo concept pages (EQH/EQL, trendline liquidity): https://www.luxalgo.com/library/concept/equal-highs-lows-as-liquidity/ · https://www.luxalgo.com/library/concept/trendline-liquidity/
- Pine v6 docs used: `docsrc/jabez4jc_pinescriptv6/language/operators.md` (operator classes: arithmetic, comparison, logical, ternary, history; no bitwise) and `reference/array.md` (`array.percentile_linear_interpolation(id, percentage)`).
