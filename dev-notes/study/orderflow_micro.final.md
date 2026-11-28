# Order flow and market microstructure of liquidity: combined final study (researcher A + researcher B)

Domain: where stop-loss and take-profit orders rest, what happens when they trigger, how much "liquidity" a pool holds, how pools decay, round numbers, stop hunting, absorption and icebergs, delta signatures of a sweep, and crypto liquidation levels. The aim is a better **pool-size model** and **sweep definition** for DOL Engine v2, judged by one question: does it help predict which liquidity is taken next, when, and how likely?

Engine: `brief/baseline_v2.pine` (identical to `indicators/dol_engine.pine`). All line numbers refer to it.

How to read the tags:
- **[A]**: researcher A's content, kept.
- **[A✓]**: A's claim re-checked by B against the source, A's raw outputs or the engine.
- **[CORRECTED]**: B found A's claim wrong or overstated and fixed it.
- **[NEW-B]**: added by B (new literature, new tests, new engine findings).

Evidence grades:
- **strong**: peer-reviewed, or a large replicated quantitative study.
- **moderate**: published or reproducible statistics with numbers.
- **weak**: practitioner consensus, vendor claims, small samples.
- **none**: folklore.

Original tests are marked [A-test] (scripts in `brief/study/orderflow_tools/`) or [B-test] (scripts in `brief/study/orderflow_b_tools/`). Section 7 lists them.

Access notes for this pass:
- newyorkfed.org and fraser.stlouisfed.org did not resolve from this session, and the Firecrawl scrape credits were exhausted. So B could not reopen the Osler PDFs. A read Osler SR150's tables through Firecrawl in its own pass.
- B verified the rest through the paper-index reader (full-text passages), web search, and A's raw outputs.
- Where a number depends on A's reading alone, it is marked as such.

---

## 0. Executive summary (combined, corrected)

1. **Where stops sit.** The geometry the engine uses is supported, but the evidence grade has to be split.
   - **Round numbers: strong.** On the RBS order book (Osler 2003), stop-buys sit at 01-10 above a "00" 14.4% of the time vs 7.4% at 90-99 below (p = 0.029). Take-profits sit at "00" 9.3% of the time.
   - **Swing extremes: moderate and indirect [CORRECTED].**
     - Support/resistance coincides with resting *limit*-order depth (Kavajecz & Odders-White 2004).
     - Published S/R levels predict intraday trend interruptions (Osler 2000).
     - No study B found measures stop orders clustering beyond swing highs/lows directly. A graded the whole concept "strong".
   - Osler (2005): stops are placed a median 0.43% from the market and live a median 0.46 days. [A-read]
2. **The engine's stop is not where A said it was [CORRECTED, NEW-B].**
   - `f_invalidation` puts the stop at `lv.bottom − 0.10·ATR` (1352). For the opposing SSL pool, `lv.bottom` is already `P − 0.20·ATR` (zone, 1774).
   - So the stop sits about **0.30 ATR** beyond the pool, not 0.10.
   - It is beaten by **41.0%** of rejected sweeps: 30-47% by dataset, 46-57% on BTC. A reported 78.5%.
   - A's T4 "engine" row (buffer 0.10) is therefore mislabelled: the engine sits between A's 0.25 and 0.50 rows.
   - A's OF-2 "Beyond Stop Band" spec would have added q80 *on top of* the zone. That is fixed here.
3. **Stop band depth must be learned per chart.**
   - Rejected sweeps penetrate a median 0.16-0.19 ATR on daily equities, 0.23-0.27 on hourly FX/NQ/gold, and **0.26-0.36 on BTC** [B-test].
   - q80 is about 2.2 × q50 everywhere (0.39-0.82 ATR).
   - Normalising by ATR is right. Across 11 datasets the median spans ×2.2 in ATR units, but ×20 in % of price (0.024% EURUSD hourly to 0.48% daily equities). Fixed tick or percent buffers would be wrong.
4. **Pool "size" proxies do not predict which pool is reached** [A-test + B-test + siblings].
   - Equal prints, tests, age, prominence (negative at 1H in `ict_liq` B4), pivot-bar relative volume and volume traded in the zone since birth (the open-source "Liquidity Swings" idea) are all within about ±1.5 pp of a distance-matched random level when pooled.
   - Signs are mixed by market for the volume measures: daily equities +, BTC −.
   - The engine's density term `0.9·eqCount + 0.45·stack + 0.35·tests` (682) has no support. The pool-size model collapses to **source tier** for reach (ICT-10 "Evidence").
   - Prominence matters only for the *size of the run after the take* (+0.21 vs +0.06 ATR at 10 bars, about 2.3σ).
5. **Sweep depth and close class carry almost no directional information.** This includes the multi-bar class that matters most to traders [A-test + B-test].
   - Depth buckets are within ±2.6 pp of the null.
   - **[NEW-B]** A sweep that closes *beyond* and then closes back inside within 1-3 bars (failed breakout, the "outbreak & retest" family) happens on 21-29% of sweeps. Scored as a race against driftless geometry it leans reversal by only **−1.5 ± 0.7 pp** (n 4,253, 9 datasets, signs mixed). A same-bar REJECT is +0.5 ± 0.6.
   - What traders see as "reversal after a reclaim" is mostly geometry: after a reclaim price sits closer to the throwback barrier (P(continuation first) 0.333 vs geometry 0.348).
   - Classes are labels and ledger cells, not forecasts.
6. **After any pool is traded through, volatility bursts in both directions.** This is a timing effect and the strongest signal in this domain.
   - A: +4.1 pp re-take and +3.2 pp 1-ATR throwback at 3 bars; +0.145 ATR extra excursion. [A✓]
   - **[NEW-B]** It is **not** explained by a fast volatility ratio. After matching on ATR5/ATR50 deciles, the next-3-bar range is **+15-23%** on all six intraday series (FX, NQ, gold, BTC), +8-15% at 10 bars and +4-10% at 30 bars. Daily equities show **no** burst (0.96-0.99).
   - On BTC it is larger and longer: excursion +0.23-0.36 ATR at 3 bars, still +0.3-0.5 ATR at 30.
   - It matches Osler's 15-minute-to-2-hour cascades and the 30-minute crypto liquidation cascades.
   - **[NEW-B] Ledger consequence.** The engine opens a new trial right after its previous target is swept. On BTC a random level 1-3 ATR away is reached +2.1 to +3.4 pp more often from a sweep bar than the unconditional baseline says. The other series show −1.1 to +1.0 pp, except GOOG D (+3.4 ± 2.0, n 350). The EDGE readout is slightly flattered on crypto unless the baseline is volatility-conditioned too (OF-6).
7. **Fresh extremes are liquidity at once, and the engine misses them** [A-test, replicated on BTC].
   - 60.8% of rejected-sweep wicks are re-taken within 5 bars (BTC 48-54%; next bar 27-30%), before a pivLen-5 pivot can register them. Only 38% ever become pivots.
   - The engine therefore has no pool at the most obvious level on the chart and cannot place the invalidation "beyond the sweep high". → OF-1.
8. **Round numbers act as geometry, not as magnets** [A-test + B-test + literature].
   - They are not magnets at bar resolution: the round-minus-control 30-bar reach changes sign across datasets.
   - A sweep wick beyond a pool **stops short** of a round number. A measured −4.2 pp (3σ) on one grid. **[NEW-B]** The effect holds at half that grid (−3.7 ± 0.9 pp), fades at one fifth (−1.2 ± 0.7), and is larger on BTC: −7.4 ± 1.3 at 2,500, −6.0 ± 0.6 at 500, −4.1 ± 0.8 at 1,000.
   - Once a coarse round is reached, it is passed +3.3 pp more often. This matches Donaldson & Kim (1993, DJIA: restrained at multiples of 100, larger moves after breaking through) and Cyree et al. (1999, 8 indices: higher conditional means and variance effects at barrier crossings).
   - → OF-4: cap zones at the round on the "00/50" grid. No score bonus.
9. **Order-flow (delta) signatures of sweeps fail on true aggressor data [NEW-B].** This was tested on Binance BTC 1H with taker-buy volume.
   - "Absorption" (aggressive flow *into* the pool on a bar that closes back inside) is the **norm**: 68.6% of rejected sweeps.
   - The clearly absorbed ones (|Δ| > 0.1·V) lean **continuation**, not reversal: wick re-taken +4.7 ± 2.2 pp at 30 bars, throwback +0.0.
   - The candle-sign lower-timeframe proxy that Pine can build agrees with the true delta sign only **60-66%** of the time (corr 0.22-0.33). Bulk-volume classification is no better (61-66%).
   - `request.footprint()` is Premium/Ultimate-only and limited to one call per script (docs).
   - → OF-7 is downgraded to an opt-in context label. No "ABSORBED → reversal" claim.
10. **Crypto liquidation levels are real mechanics with no forecasting evidence.**
    - Mechanics: 60× average leverage of the liquidated (BitMEX); 88% of forced selling within 30 minutes; open interest cleared 25-70%; $2.1 bn auto-deleveraged in 12 minutes on Oct 10, 2025. [A✓]
    - **[NEW-B]** A vendor-style heatmap built from true taker flow (25/50/100× tiers, decay, deletion on cross) was tested on BTC 1H. Its heaviest bin is reached **+0.7 ± 0.8 pp** vs a distance-matched random level (n 10,792): no magnet.
    - A's OF-8 is dropped.
11. **Stop hunting is documented, not just theory [CORRECTED].**
    - The UK FCA's Nov 2014 final notices (five banks, £1.1 bn of fines) and the May 2015 Barclays notice record G10 FX traders who "attempted to trigger clients' stop loss orders" for their own benefit.
    - Intent therefore exists in the record. How often it happens is unknown. For the engine this changes nothing: "draw to the obvious pool" already is the premise.
12. **Proposals.** 7 proposals plus coordination notes. A's OF-8 is dropped, OF-6 is upgraded to P2, and OF-7 is downgraded.
    - **P1:** OF-1 (instant wick pools; `wickTgt` off by default); OF-2 (learned stop band with corrected invalidation, sweep classes including RECLAIM).
    - **P2:** OF-6 (post-sweep volatility state for both the model *and* the baseline); OF-4 (round cap on the 00/50 grid); OF-3 (one `evaluate()` edit: adopt ICT-10/WYK-1/WYK-2, no new size terms); OF-5 (drop the ×0.85 HVN penalty).
    - **P3:** OF-7 (opt-in delta context label).

---

## 1. Concepts: definitions and parameters

### 1.1 Stop-loss clustering beyond obvious levels (the physical pool) [A, evidence CORRECTED]
- **Definition.**
  - Protective stops of longs rest *below* recent swing lows (sell-side liquidity, SSL). Stops of shorts rest *above* swing highs (buy-side liquidity, BSL).
  - Breakout-entry stops sit at the same places.
  - Each becomes a market order once triggered.
- **Parameters [A-read, Osler 2005 Table I].**
  - Stop-loss distance from the market at placement: median 0.43%, mean 0.91%.
  - Time outstanding: median 0.46 days, mean 3.42.
  - Stops are larger than take-profits: median $3.24 m vs $2.12 m.
  - More than 62% of the face value of very large stops sits within ±10 pips of a "00".
- **Evidence, split by claim [CORRECTED].**
  - *Stops just beyond round numbers*: **strong** (Osler 2003 and 2005; bank order book).
  - *Stops just beyond swing highs/lows*: **moderate, indirect**.
    - S/R levels locate resting limit-order depth (Kavajecz & Odders-White 2004).
    - Published S/R predicts intraday trend interruptions (Osler 2000).
    - Every source that claims "stops sit just beyond recent highs and lows" is practitioner material (e.g., BabyPips, which cites Osler's *round-number* results).
    - B found no study measuring stop orders at swing extremes directly.
    - At bar level the geometry is consistent: penetration quantiles (1.4) show where trade-throughs reverse.
- **Practitioner placement rules (weak).**
  - "1-2 ticks beyond the swing"; "beyond the wick".
  - ATR buffers of 0.1-0.5.
  - Turtle Soup buys back 5-10 ticks above the old 20-day low (Connors & Raschke).
- **Use for DOL.** The draw is to the band just beyond the most obvious unswept extremes.
- **Engine: present.** BSL zone `[P, P + zoneATR·ATR]` (1762); SSL mirror (1774); registry pools (1848). Swept on a strict trade-through (623-624).

### 1.2 Take-profit and limit clustering at round numbers; front-running [A✓ + NEW-B]
- **Definition.** Take-profits and resting limits bunch *exactly at* round prices ("00", then "50"). Stops bunch just *beyond* them.
- **Parameters.**
  - Osler 2003 (via sibling `ict_liq` E1; B could not reopen the PDF):
    - take-profits at 00: 9.3% (≈ 1% if uniform);
    - stop-buys at 01-10 vs 90-99: 14.4% vs 7.4%;
    - stop-sells at 90-99 vs 01-10: 10.0% vs 5.1%.
  - **[CORRECTED]** A's summary quoted "14.3% vs 6.9%". Its own table and the sibling report give 14.4% vs 7.4%, used here.
- **Front-running.** Algos post one tick ahead of round clusters, so the last digit is 1 for buys and 9 for sells (Lallouache & Abergel, EBS) [A✓, abstract].
- **Order imbalance.** Excess buying 1¢ below and excess selling 1¢ above round numbers on NYSE, scaled by roundness (Bhattacharya, Holden & Jacobsen 2012) [A].
- **Depth vs stickiness.** Round levels hold more depth but show no longer depth-adjusted durations in 5 Nasdaq stocks, 2025. Intel and SoFi depart *away* from the round (Jung & Lee 2026) [A✓, abstract].
- **[NEW-B] Index barriers.**
  - Donaldson & Kim (JFQA 1993): the DJIA is restrained at multiples of 100, but after breaking through it moves by more than otherwise warranted.
  - Cyree, Domian, Louton & Yobaccio (RFE 1999): in 5 of 8 world indices the conditional mean is higher after an upward barrier crossing, and 7 of 8 show variance effects at crossings.
  - Later work on smaller markets is mixed.
- **Use for DOL.**
  - A round number just beyond a pool caps the sweep wick (take-profit and front-running wall).
  - Stops beyond the round feed the move once it gives way.
- **Engine: missing** (grep: no round-number logic).

### 1.3 Stop cascades ("running the stops") [A✓]
- **Definition.** Crossing a stop cluster turns stops into same-direction market orders, which accelerate price (positive feedback).
- **Parameters [A-read, Osler 2005 Table VI.A].** Extra move after crossing a round vs an arbitrary level, in 1/100 %:
  - DEM 1.12 / 0.89 / 0.57 / 0.85 at 15m / 30m / 1h / 2h;
  - JPY 1.30 / 1.34 / 1.26 / 2.35;
  - GBP 0.77 / 0.80 / 0.27 / 0.35;
  - negative at 1-2 days (DEM −5.23 at 1 d).
- **CFTC (summary only).** Stops execute more on volatile days and supply liquidity in the direction of the move.
- **Crypto.** 88% of post-onset forced selling landed within 30 minutes; open interest cleared 25-70%. **[NEW-B detail]** 63% of the Oct 2025 forced selling was absorbed off-book by the venue's backstop (Garcia Seuma 2026, abstract).
- **Theory.** Predatory trading (Brunnermeier & Pedersen 2005): overshoot, then reversal.
- **Use for DOL.** Timing: the next pools become reachable sooner for a few bars (1.9). It is not a fixed "outermost is the draw" rule; stacking evidence is heterogeneous (`ict_liq` §1.6).
- **Engine: partial.** Stack logic (1230-1251, inner ×0.70 at 684-685). The raid read (1580-1582) has the wrong sign; see ICT-9.

### 1.4 Stop-zone depth: the stop band, and ticks vs ATR [A + NEW-B]
- **Definition.** For a BSL pool at P, `pen = (high_sweep − P) / ATR[1]` on the bar that first trades through. SSL mirrors.
  - **Core band**: `[P, P + q50]`; **outer edge**: `P + q80`.
  - Both are learned from **REJECT** sweeps only (close back inside). HOLD sweeps measure trend, not stops.
- **Measured [A-test, 7 datasets; B-test, BTC]:**

| Dataset | REJECT q25 / q50 / q80 / q90 (ATR) | HOLD q50 / q80 |
|---|---|---|
| S&P 500 D | 0.08 / 0.19 / 0.42 / 0.58 | 0.52 / 0.88 |
| NASDAQ D | 0.07 / 0.16 / 0.40 / 0.53 | 0.47 / 0.93 |
| GOOG D | 0.07 / 0.18 / 0.39 / 0.54 | 0.62 / 1.14 |
| EURUSD 1H 17-18 | 0.12 / 0.27 / 0.60 / 0.84 | 0.95 / 1.80 |
| NQ 1H | 0.10 / 0.23 / 0.52 / 0.73 | 0.80 / 1.70 |
| GC 1H | 0.12 / 0.26 / 0.56 / 0.78 | 0.77 / 1.67 |
| EURUSD 1H 24-26 | 0.15 / 0.27 / 0.60 / 0.84 | 0.88 / 1.71 |
| **[NEW-B] BTC 1H 24-25** | 0.12 / 0.29 / 0.65 / 1.02 | 0.95 / 1.77 |
| **[NEW-B] BTC 4H 24-25** | 0.10 / 0.26 / 0.56 / 0.85 | 0.92 / 1.45 |
| **[NEW-B] BTC 1H 20-23** | 0.16 / 0.36 / 0.80 / 1.25 | 1.04 / 2.06 |
| **[NEW-B] BTC 15m 20-23** | 0.13 / 0.33 / 0.82 / 1.36 | 1.06 / 2.16 |

- **Pooled (A's 7 datasets).**
  - REJECT q50 0.233, q80 0.518.
  - P(pen > 0.10 / 0.20 / 0.30 / 0.52 / 1.00) = 0.785 / 0.553 / **0.410** / 0.199 / 0.049 ([B-test] for 0.30 and 1.00).
  - REJECT share of sweeps: 44.5% (A); 48-50% on BTC.
  - The q80/q50 ratio is about 2.2 everywhere (2.15-2.48). That makes it a usable prior when a chart has few samples.
- **Ticks vs ATR [NEW-B].**
  - The REJECT median spans 0.16-0.36 ATR across 11 series (×2.2).
  - In % of price it spans about 0.024-0.03% (EURUSD 1H) to 0.24-0.48% (daily equities), a factor of about 20.
  - Tick rules ("1-2 ticks beyond") only make sense on one instrument and timeframe. ATR is the right unit, learned per chart.
- **Use.** Zone drawing, invalidation placement and the sweep class threshold (1.8).
- **Engine: partial.** Fixed `zoneATR` 0.20 (93), used at 1520 (`wPx`), 1762, 1774, 1848.

### 1.5 The engine's actual stop distance [NEW-B, CORRECTS A]
- `f_invalidation` (1343-1364) takes the nearest opposing pool and sets `inv := tgt.side == 1 ? lv.bottom − buf : lv.top + buf` with `buf = 0.10·atr` (1344, 1352).
  - For a buy-side target the opposing pool is SSL. Its zone is `[P − wPx, P]` (1774), so `lv.bottom = P − 0.20·ATR(birth)`.
  - The stop is therefore at **`P − (0.20·ATR_birth + 0.10·ATR_now)` ≈ 0.30 ATR beyond the pool**.
  - The execution-swing fallback (1356) has no zone, so it uses 0.10 ATR.
- **Exposure: rejected sweeps deeper than 0.30 ATR [B-test, `enginestop.py`].**

| Data | Share |
|---|---|
| S&P D | 30.2% |
| NASDAQ D | 35.4% |
| GOOG D | 30.7% |
| EURUSD 17-18 | 47.2% |
| NQ | 39.8% |
| GC | 44.1% |
| EURUSD 24-26 | 44.4% |
| **Pooled** | **41.0%** |
| BTC | 46.1-57.3% |

  - Counting HOLD sweeps too, 63.9% of all trade-throughs go deeper.
  - A's "78.5% beat the 0.10 buffer" measured a stop the engine does not use.
- **What a deeper stop buys [A-test T4, relabelled].**
  - The engine sits between A's 0.25 and 0.50 rows: win 42.5-43.7%, loss 41.1-38.1%, mean R −0.012 to −0.015.
  - A stop beyond the q80 band (≈ 0.55-0.60 ATR) sits near the 0.50-0.75 rows: win about 44-44.6%, loss about 36-38%.
  - Expectancy is unchanged within noise: a martingale. The change is honest risk display, not edge.

### 1.6 Pool size: growth with time, touches and volume [A + NEW-B]
- **Microstructure claim.** More participants referencing a level means more stops: higher timeframe, more prominent, more touches, equal prints, older, more volume traded there.
- **Evidence.**
  - **HF bounce memory decays in hours [A✓ via full text].** EURUSD 2018 1-minute data: a level's bounce probability after 1 prior bounce falls to 0.5 at about a 350-minute lag window, after 4 bounces at about 900 minutes.
    - LLOY shows little decay. For BRENT, one bounce even predicts *penetration* beyond 300 minutes (Chung & Bellotti 2021).
    - Garzarelli et al. (2014) find memory in tick data.
  - **Stops are refreshed within days** (median life 0.46 days).
  - **Bar-level tests.**
    - Equal prints: post-sweep path unchanged (+0.6 ± 2.3 pp at 10 bars) [A-test T3]. Reach +0.3 ± 1.8 pp [`ict_liq` B2].
    - Tests: no monotone effect [A-test T3; `ict_liq` §1.16].
    - Age: young pools about 1 pp less reach, old intraday pools 3-8 pp less; nothing monotone in between [`wyckoff_sd` WYK-2].
    - Prominence: *lower* 1H reach [`ict_liq` B4] but a larger post-take run (+0.21 vs +0.06 ATR at 10 bars) [A-test T3].
  - **[NEW-B] Volume as size** (the open-source "Liquidity Swings" model: revisit count plus volume accumulated in the swing area; `poolvol.py`; 6 datasets with volume; nearest pool per side 0.5-4 ATR away; H = 30; edge vs S(d)):

    | Feature | Tercile 1 | Tercile 2 | Tercile 3 | High − low |
    |---|---|---|---|---|
    | Pivot-bar relative volume | +0.1 ± 0.9 | +0.2 ± 0.8 | −1.4 ± 0.9 pp | **−1.5 pp** |
    | Zone volume since birth | +0.1 | −0.9 | −0.4 pp | **−0.5 pp** |

    The sign differs by market: daily equities show zone-volume high − low +4.2 to +8.9 pp; BTC shows −0.7 to −3.6 pp.
- **Verdict.**
  - "Size" does not predict *which pool is reached next* at bar resolution. For reach the only robust size term is the **source tier** (HTF / key level vs chart swing), which is how many participants watch it.
  - Prominence belongs to the *after-take* magnitude, not to reach.
  - Everything else is display plus learned ledger bits.
- **Engine: wrong (magnitude).**
  - Density `x = 0.9·eqCount + 0.45·stack + 0.35·min(tests,6) + 0.8·min(1, prom/3) + 1.2·tier` (682).
  - Freshness ramps up with age, "stops accumulate" (668-671).

### 1.7 Pool decay after a sweep; liquidity at the fresh extreme [A + NEW-B]
- **Definition.**
  - A trade-through fills the stops between P and the wick. Stops deeper than the wick remain (residual).
  - New stops appear at once beyond the new wick (faders) and below the old level (breakout buyers).
- **Measured.**
  - Shallow pokes (≤ 0.05 ATR, closed back inside) are re-taken +2.6 ± 1.6 pp above null within 30 bars (weak residual) [A-test].
  - REJECT wicks re-taken within 5 bars [A-test T6, `wicklag_btc.py`]:
    - pooled 60.8% (52-82% by dataset);
    - **[NEW-B] BTC 1H 54.3%, BTC 15m 51.9%, BTC 1H 20-23 48.1%; next bar 27-30%**.
  - Only 38.3% of wicks ever become pivLen-5 pivots.
  - Edge vs distance-matched null at 3 bars: +4.3 ± 1.0 pp (A); BTC REJECT +4.6 to +5.7 pp [B]. At 30 bars about 0 (geometry).
- **Engine.**
  - Binary removal on a trade-through (1583-1589): present and correct per the decision history.
  - The new extreme is not a pool until `ta.pivothigh/low` confirms it pivLen bars later (1753-1776): **gap** → OF-1.

### 1.8 Sweep vs breakout classification, including the multi-bar reclaim [A + NEW-B]
- **Bar-close classes (BSL; SSL mirrors).** `pen` as in 1.4; `cl = (close − P)/ATR[1]`; `q50` = the chart's learned REJECT median (prior 0.25).
  - **POKE**: `cl < 0` and `pen ≤ 0.05`. Triggers only the nearest stops; `ict_liq` ICT-9 calls it "micro".
  - **REJECT**: `cl < 0`.
  - **PROBE**: `0 ≤ cl < q50`. Closed beyond, inside the stop band.
  - **ACCEPT**: `cl ≥ q50`. Breakout.
  - **[NEW-B] RECLAIM(n)**: a PROBE or ACCEPT whose close returns inside (`close < P`) within n = 1-3 bars. This is the failed breakout and the "outbreak & retest" mode of open-source sweep tools. Turtle Soup's next-day re-entry is the daily version.
- **Frequencies [B-test, `reclaim.py`; 9 datasets]:**

| Class | Share of sweeps |
|---|---|
| Same-bar REJECT | 36-50% |
| RECLAIM at bar +1 | 12-15% |
| RECLAIM at bar +2 | 4.5-9.7% |
| RECLAIM at bar +3 | 2.4-6.3% |
| Still beyond after 3 bars | 27-37% |

- **Direction, scored as a first-passage race from the classification bar.** Continuation barrier = the sweep extreme; reversal barrier = pool ∓ 1 ATR. Compared with driftless gambler's-ruin geometry (`reclaim_race.py`):

| Class | n | P(continuation first) | Geometry | Excess |
|---|---|---|---|---|
| Same-bar REJECT | 7,645 | 0.475 | 0.470 | +0.5 ± 0.6 pp |
| RECLAIM +1 | 2,518 | 0.363 | 0.371 | −0.8 ± 1.0 |
| RECLAIM +2 | 1,079 | 0.293 | 0.322 | −2.9 ± 1.4 |
| RECLAIM +3 | 656 | 0.280 | 0.299 | −1.9 ± 1.8 |
| **Any RECLAIM** | 4,253 | 0.333 | 0.348 | **−1.5 ± 0.7** |
| Still beyond after 3 bars | 5,778 | 0.719 | 0.725 | −0.6 ± 0.8 |

  - Per-dataset RECLAIM excess ranges from +4.4 (S&P D) to −6.2 pp (EURUSD 24-26).
- **Depth [A-test T1].** No depth bucket changes the 3-, 10- or 30-bar odds beyond ±2.6 pp. P(REJECT | depth bucket) is 91 / 85 / 76 / 59 / 44 / 18% for the buckets ≤ 0.05 / ≤ 0.10 / ≤ 0.20 / ≤ 0.35 / ≤ 0.60 / > 0.60 ATR.
- **Context.** Siblings agree there is no reversal edge after REJECT, and only a HOLD against the HTF trend leans reversal (`ict_liq` ICT-9, `ict_struct`, `bias_dol`).
- **Verdict.** Classes are honest **labels, alerts and ledger cells**. The reclaim's reversal lean is ≤ 2 pp and sign-unstable, so it gets no D weight.
- **Engine: partial.**
  - HOLD = `close > lv.top`, REJECT = `close < lv.price` with fixed ±tier into D (1580-1582).
  - HOLD depends on the *display* input `zoneATR`.
  - No depth, no reclaim.

### 1.9 Post-sweep volatility burst (timing of stop runs) [A + NEW-B]
- **Definition.** For a few bars after any pool trade-through, excursions in *both* directions exceed the distance-matched null.
- **A [A✓ against raw output].** Pooled, K = 3:
  - re-take +4.1 ± 0.6 pp;
  - throwback +3.2 ± 0.6;
  - excursion +0.145 ± 0.018 ATR (0.74 vs 0.60);
  - K = 10 +0.130; K = 30 +0.112 ± 0.071 (n.s.).
- **[NEW-B] BTC (`sweep_btc.py`).**

| K | Re-take edge | Throwback edge | Excursion excess |
|---|---|---|---|
| 3 | +4.9 to +7.3 pp | +1.0 to +6.2 | +0.23-0.36 ATR |
| 10 | — | — | +0.22-0.44 ATR |
| 30 | about 0 | +3.2 to +5.3 (HOLD) | +0.3-0.5 ATR |

- **[NEW-B] Is it just volatility clustering? (`burst_vs_vol.py`)** Future two-sided range / ATR on sweep bars ÷ the same on all bars, within ATR5/ATR50 deciles:

| Horizon | EURUSD 17-18 | NQ | GC | EURUSD 24-26 | BTC 1H | BTC 15m | S&P D | NASDAQ D | GOOG D |
|---|---|---|---|---|---|---|---|---|---|
| 3 bars | 1.19 | 1.23 | 1.16 | 1.15 | 1.20 | 1.20 | 0.97 | 0.98 | 0.99 |
| 10 bars | 1.15 | 1.15 | 1.08 | 1.14 | 1.14 | 1.13 | 0.99 | 0.97 | 0.96 |
| 30 bars | 1.09 | 1.04 | 1.04 | 1.06 | 1.10 | 1.09 | 0.98 | 0.96 | 1.02 |

  The burst survives the fast-volatility control on every intraday series and is absent on daily equity bars. That is consistent with cascades lasting minutes to hours.
- **[NEW-B] Ledger baseline bias (`ledgerbias.py`).** A random level 1-3 ATR away, reached within 30 bars from a sweep bar, vs the unconditional S(d):

| Data | Edge |
|---|---|
| BTC 1H | +3.4 ± 0.8 pp |
| BTC 15m | +2.1 ± 0.3 pp |
| GOOG D | +3.4 ± 2.0 pp |
| Other 6 series | −1.1 to +1.0 pp |

  The engine opens trials right after the previous target is swept. On crypto the EDGE readout is therefore flattered by about 2-3 pp unless the baseline is conditioned too.
- **Use.** WHEN: short-horizon PoT, ETA and race readouts; ledger fairness. Not which side.
- **Engine: missing.** PoT and race use the 50-bar `potSig` (916) and an unconditional empirical surface (1302-1322).

### 1.10 Absorption, exhaustion, delta divergence [A + NEW-B]
- **Definitions (footprint vocabulary).**
  - **Absorption**: heavy aggressive volume through a level without progress, then a close back inside.
  - **Exhaustion**: a delta spike, then volume dries up.
  - **Delta divergence**: a new price high with lower bar or cumulative delta.
- **Literature [A].**
  - Order-flow imbalance moves price contemporaneously (Cont, Kukanov & Stoikov).
  - Short-term reversal comes from imbalances lasting < 1 hour (Heston, Korajczyk & Sadka).
  - Crypto: 15-minute reversal in 90% of 183 Binance pairs, concentrated after taker-driven moves, 1.3 bp gross (Kitron & Wengrowicz 2026) [A✓].
  - **[NEW-B]** Opening order imbalance at quarter-hour marks predicts crypto perpetual returns over 4-12 hours (Kim & Hansen 2026, 6 Binance contracts). Some flow information survives to hours, but it is not tied to sweeps.
- **[NEW-B] True-delta test at sweep bars.** BTC 1H 2024-25, Binance taker-buy volume, delta = 2·takerBuy − V, signed toward the raided side (`sweep_btc.py`):

| REJECT subset | n | Re-take K3 | Re-take K10 | Re-take K30 | Throwback K30 |
|---|---|---|---|---|---|
| Δ into pool > +0.1·V ("absorbed") | 305 | +5.4 ± 2.8 | +3.9 ± 3.0 | **+4.7 ± 2.2** | +0.0 ± 2.1 |
| Δ flat | 538 | +5.2 ± 2.3 | −0.2 ± 2.3 | −3.4 ± 2.0 | +2.0 ± 1.3 |
| Δ away < −0.1·V | 103 | +7.1 ± 5.5 | +11.5 ± 5.4 | +11.3 ± 3.1 | +3.7 ± 2.3 |

  - 68.6% of REJECT bars (68.4% at 4H) carry delta *into* the pool. "Absorption" is what a rejection bar usually looks like, not a rare signal.
  - The absorbed subset leans *continuation* (the wick gets re-taken), the opposite of the practitioner reading.
  - At 4H (n 55) nothing is significant.
- **[NEW-B] Can Pine see delta? (`deltaproxy.py`, BTC 1H with true taker delta).**

| Chart bar (intrabars) | Candle-sign proxy: corr / sign agreement | BVC: corr / agreement | Chart-bar sign only |
|---|---|---|---|
| 1H (itself) | 0.33 / 66.0% | 0.34 / 66.0% | same |
| 4H (4 × 1H) | 0.27 / 62.0% | 0.29 / 63.5% | 0.27 / 63.0% |
| 1D (24 × 1H) | 0.22 / 60.6% | 0.24 / 61.2% | 0.19 / 60.1% |

  - A lower-TF candle-sign proxy is barely better than the chart bar's own colour.
  - Literature agrees that bar-level classification is weak: BVC loses to the tick rule and Lee-Ready (Chakrabarty, Pascual & Shkilko 2015). On a 1.2-billion-trade ground-truth tape, tick rule and BVC score 49.8% / 50.5% (Qin & Yang 2026, prediction markets).
- **Pine.**
  - `request.footprint()` exists, but "only accounts with Premium or Ultimate plans can use scripts that call this function", and "a single script cannot include more than one" (`reference/request.md` 168-170).
  - `request.security_lower_tf` is universal: 100K intrabars on non-Ultimate plans, 200K on Ultimate (`limitations.md` 263-267).
  - `syminfo.volumetype` returns "n/a" for symbols without volume.
- **Verdict.** Weak, and partly *contradicting* at bar level. At most an opt-in context label (OF-7).
- **Engine: missing** (volume used only in the 1H profile, 978-1009).

### 1.11 Icebergs and hidden liquidity [A + NEW-B]
- **Definition.** Displayed size is refilled at one price.
  - CME native icebergs keep their order ID across refills and trade larger than the displayed size. They are detectable only from market-by-order data.
  - Synthetic icebergs show up as new limits arriving just after fills.
- **Numbers [NEW-B].** ES futures, one week of June 2019 (Zotikov & Antonov 2019):
  - native icebergs are 0.06% of orders by number but about **4% of traded volume**;
  - most tranches refill in under one second;
  - more than half of synthetic icebergs are cancelled.
- **Behaviour [A].** Detected icebergs attract *matching* market orders (Frey & Sandås 2017).
- **Engine / Pine.** Not observable from TradingView data: no MBO feed, refills faster than any bar. Not buildable.

### 1.12 Liquidity holes and thin paths [A]
- **Definition.** Large price changes happen when the book has gaps next to the best price (Farmer et al. 2004) [A✓, abstract].
- **Bar proxy.** `vf` = mean volume-profile volume between price and target / profile mean.
- **Measured [A-test T5].**
  - Thin path (vf < 0.6): +1.3 to +3.6 pp reach, depending on lookback.
  - Thick path (vf > 1.4): −1.5 to +1.4 pp.
- **Engine: partial.** ×1.10 thin / **×0.85** thick (1947). The thick penalty is unsupported.

### 1.13 Crypto liquidation levels [A + NEW-B]
- **Definition.** Long liquidation price ≈ `entry·(1 − 1/L + mmr)`; short ≈ `entry·(1 + 1/L − mmr)`.
  - Vendor heatmaps add estimated new positions (ΔOI) at each bar's price, split long/short, projected to leverage tiers with weights, decayed, and deleted when crossed.
- **Mechanics [A✓ via abstracts].**
  - BitMEX: daily forced liquidations are 3.51% (long) / 1.89% (short) of open interest; the liquidated averaged 60× leverage (Cheng et al. 2021).
  - Oct 10, 2025: about $19 bn liquidated; $2.1 bn auto-deleveraged in 12 minutes on Hyperliquid (Chitra 2025).
  - Open interest is misquoted by some large exchanges (Giagkiozis & Said 2023), a problem for any OI-based map.
- **[NEW-B] Test (`liqmap.py`, BTC 1H 2024-25).**
  - The heatmap used *true taker flow* in place of ΔOI: long mass = max(0, Δ), short mass = max(0, −Δ) at hlc3; tiers 25/50/100× weighted .40/.35/.25; mmr 0.005; $100 bins; 72-bar half-life; deleted on cross.
  - Heaviest bin 0.5-4 ATR away: reached 46.1% vs S(d) 45.4%, **edge +0.7 ± 0.8 pp** (n 10,792).
  - A random live bin in the same band: −0.1 ± 0.6.
  - **No magnet.** The test uses a proxy for ΔOI, so it does not refute OI-based maps outright. No published validation of them exists either.
- **Verdict.** Weak (mechanics real; magnet claim untested in the literature and null in B's proxy test). A's OF-8 is dropped.

### 1.14 Equal highs/lows as pooled stops [A✓ + NEW-B]
- **Definition.** Two or more prints within a tolerance form one pool, and the stops rest beyond the **outermost** print.
- **Engine.** `f_mergeAt` moves the pool to the outermost print and skips same-candle prints (1104-1131). This is correct.
  - Per `ict_liq` §1.2 the merge is effectively one-sided: a right-hand print beyond the stored pool sweeps it first (ICT-11). OF-1 closes this gap (§4).
- **[NEW-B] Open-source contrast.**
  - The `smartmoneyconcepts` Python library groups ≥ 2 swing highs within `range_percent` × the *whole-dataset* high-low range. That is look-ahead, and it repaints.
  - It sets the level to the **average** of the group and calls it "swept" only when price trades beyond level + band.
  - Osler's mechanism says stops sit beyond the *outermost* print, so the engine's outermost rule is the better one.
- **Evidence.** Equal pools are not reached more often (+0.3 ± 1.8 pp, `ict_liq` B2) and show no different post-sweep path (A-test T3).

### 1.15 Tests (touches without a take) [A✓]
- **Engine definition.** A bar within 0.30 ATR of the pool that does not trade through, at least 3 bars after the previous test (650-658).
- **Evidence.** HF memory says a bounce is more likely right after prior bounces, decaying in hours (1.6). At bar level there is no monotone effect (A-test T3; `ict_liq` §1.16).
- **Engine: wrong (monotone reward)** `0.35·min(tests,6)` (682).

### 1.16 Stop hunting and predatory trading [A, evidence CORRECTED]
- **Definition.** Deliberately pushing price through a known stop cluster to fill size against the triggered orders.
- **Evidence.**
  - Mechanism: strong (Osler cascades; Brunnermeier & Pedersen theory).
  - **[CORRECTED] Intent is documented.** The UK FCA's Nov 2014 final notices against Citi, HSBC, JPMorgan, RBS and UBS (£1.1 bn of fines), and the May 2015 Barclays notice (£284 m), record G10 spot FX traders who attempted to trigger clients' stop-loss orders for their own benefit, coordinated in chat rooms. Citi's and Barclays' notices state it explicitly; B did not read the other four in full.
  - Frequency is unknown. Grade: moderate (documented cases).
- **Use for DOL.** Identical to "draw to the obvious pool", which is already the engine's premise. No change.

### 1.17 Magnet effects near forced-order triggers [NEW-B]
- **Claim.** Price accelerates toward a level where forced orders will trigger, such as price limits or option strikes at expiry.
- **Evidence is mixed.**
  - Chinese A-shares, 2000-2011 high-frequency data: a **cooling-off** effect, not a magnet, before limit hits; continuation the next day (Wan et al. 2015, 2018).
  - ChiNext's 2020 limit change: no magnet (Qi 2023).
  - Option-strike pinning on expiry days is a known literature (e.g., Ni, Pearson & Poteshman 2005, cited from the literature, not re-read). The hedging explanation for single cases is disputed (Bar-Yam et al. 2014, AAPL $500).
- **Use for DOL.** None at bar level. It supports the "no round-number magnet" reading (1.2, T2). Engine: n/a.

### 1.18 How open-source tools define pools and sweeps [NEW-B]
- **"Liquidity Swings" (open-source TradingView script).**
  - Zone = the swing candle's **wick extremity** (wick to the nearer of open/close) or its full range.
  - Shows the **count** of revisits and the **volume** accumulated in the zone, optionally intrabar.
  - Filters zones by count or volume. A broken swing high is read as bullish.
  - B6 tests this volume-as-size idea: null (1.6).
- **"Liquidity Sweeps" (same author).** Two modes:
  - "wick": a wick pierces a level and the bar closes back inside;
  - "outbreak & retest": price closes through, retests, then prints an opposite wick.
  - The second is the RECLAIM family tested in 1.8.
- **`smartmoneyconcepts` (Python).** See 1.14. Uses a global range (look-ahead), an average level, and swept = beyond level + band.
- **Engine comparison.**
  - The engine's zone lies *beyond* the extreme, not inside the wick. That is right for the stop location.
  - Its sweep rule is the strict trade-through (decision history).
  - OF-2 adds the classes; OF-1 adds the fresh wick.

---

## 2. Evidence

### 2.1 Literature, re-checked and extended

| # | Claim | Source and sample | Result | Grade | B's check |
|---|---|---|---|---|---|
| L1 | Stops just beyond round numbers; take-profits at them | Osler 2003 (J. Finance 58(5); FRBNY SR125); RBS, about 9,700 orders, 1999-2000 | TP 9.3% at 00 (uniform ≈ 1%); stop-buys 14.4% at 01-10 vs 7.4% at 90-99 (p = 0.029) | strong | Abstract confirmed (web); numbers via `ict_liq` E1; PDF host unreachable. **[CORRECTED]** A's summary "14.3/6.9" |
| L2 | Cascades after crossing stop clusters | Osler 2005 (JIMF; SR150) | Extra move after crossing rounds, 15 min-2 h; negative at 1-2 days | strong | A-read; abstract summary confirms |
| L3 | Stop distance and life | Osler 2005 Table I | Median 0.43% from market; median life 0.46 days | strong | A-read |
| L4 | Published S/R predicts intraday interruptions | Osler 2000, FRBNY EPR | Beats chance; effect lasts ≥ 5 days | strong | A |
| L5 | S/R = book depth | Kavajecz & Odders-White, RFS 2004 | Support = lowest bid reached ≥ 2×; coincides with depth | strong (for *limit* depth); indirect for stops | **[CORRECTED scope]** |
| L6 | Imbalance flips at round numbers | Bhattacharya, Holden & Jacobsen, Mgmt Sci 2012 | Excess buying 1¢ below, selling 1¢ above | strong | A |
| L7 | Front-running round clusters | Lallouache & Abergel (arXiv 1307.5440) | Orders stay on old round grid; algos one tick ahead (digits 1/9) | moderate | A✓ abstract |
| L8 | Round levels: depth, not stickiness | Jung & Lee (arXiv 2610.34787), 5 Nasdaq stocks 2025 | More depth; no longer depth-adjusted durations; INTC/SOFI depart away | moderate | A✓ abstract |
| L9 | Bounce memory decays | Garzarelli 2014; Chung & Bellotti (arXiv 2101.07410) | EURUSD 0.5 at about 350 min (1 bounce) / 900 min (4); LLOY slow; BRENT 1-bounce → penetration | strong (HF) / moderate | A✓ full text |
| L10 | Large moves from book gaps | Farmer et al. (cond-mat/0312703) | Gaps next to best price drive large changes | strong | A✓ abstract |
| L11 | OFI contemporaneous impact | Cont, Kukanov & Stoikov (1011.6402) | Linear, slope ∝ 1/depth | strong | A✓ abstract |
| L12 | Reversal = temporary imbalance | Heston, Korajczyk & Sadka (JF 2010) | Imbalances < 1 h + bid-ask bounce | strong | A |
| L13 | Crypto taker-driven reversal | Kitron & Wengrowicz (2608.21888) | 90% of 183 pairs; 1.3 bp gross vs 5 bp cost | moderate | A✓ abstract |
| L14 | Icebergs attract matching flow | Frey & Sandås (QJF 2017) | Matching market orders; lower impact | moderate | A |
| L15 | Stop orders in futures | CFTC, Fett & McPhail | Execute more on volatile days | moderate (summary) | A |
| L16 | Crypto liquidation mechanics | Cheng et al. (2102.04591) | 3.51% / 1.89% of OI per day; 60× | moderate | A✓ abstract |
| L17 | Liquidation cascades | Garcia Seuma (2608.03616, 2607.27070); Chitra (2512.01112) | 88% within 30 min; OI −25-70%; 63% absorbed by backstop; $2.1 bn ADL in 12 min; no event-invariant early warning | moderate | A✓ abstracts |
| L18 | Heatmap clusters as magnets | Vendors | No hit-rate test | none | **[NEW-B]** B9 proxy test null |
| L19 | BTC price clustering | Urquhart 2017 | > 10% end in 00; no return pattern | moderate | A |
| L20 | Gold barriers | Aggarwal & Lucey 2007; Lucey & O'Connor 2016 | Barriers at 0/00 for gold, none for silver | moderate | A |
| L21 | Absorption / CVD divergence | Practitioner guides; vendor claim | No validation | weak/none | **[NEW-B]** B3 contradicts at bar level |
| L22 | Predatory trading | Brunnermeier & Pedersen 2005 | Overshoot then reversal (theory) | strong (theory) | A |
| **L23** | Documented stop hunting | UK FCA final notices: Citi et al. Nov 2014 (£1.1 bn, 5 banks); Barclays May 2015 (£284 m) | Traders "attempted to trigger clients' stop loss orders" | moderate (documented cases) | **[NEW-B]** web search of FCA pages |
| **L24** | Index round-number barriers | Donaldson & Kim, JFQA 28(3) 1993 | DJIA restrained at multiples of 100; larger moves after breaking | strong | **[NEW-B]** abstract |
| **L25** | Barriers in conditional moments | Cyree, Domian, Louton & Yobaccio, RFE 1999 | Higher mean after up-crossing in 5/8 indices; variance effects 7/8 | moderate | **[NEW-B]** abstract |
| **L26** | CME iceberg size | Zotikov & Antonov (arXiv 1909.09495), ES, 1 week | Native icebergs 0.06% of orders, about 4% of volume; refills < 1 s | moderate | **[NEW-B]** full text |
| **L27** | Trade classification accuracy | Chakrabarty, Pascual & Shkilko, JFM 25 (2015); Easley, López de Prado & O'Hara, JFE 2016; Qin & Yang (2606.04217) | BVC < tick rule / Lee-Ready; ground truth: tick 49.8%, BVC 50.5% (prediction markets) | moderate | **[NEW-B]** |
| **L28** | Order imbalance predicts hours ahead (crypto) | Kim & Hansen (2607.09426) | Quarter-hour opening imbalance predicts 4-12 h returns | moderate | **[NEW-B]** abstract |
| **L29** | Price-limit magnet vs cooling-off | Wan et al. (1503.03548, 1803.09422); Qi, PLoS One 2023 | Cooling-off, not magnet (China); no magnet (ChiNext) | moderate | **[NEW-B]** abstracts |
| **L30** | OI data quality | Giagkiozis & Said (2310.14973) | Some large exchanges misquote OI | moderate | **[NEW-B]** abstract |
| **L31** | Open-source pool/sweep definitions | smartmoneyconcepts `smc.py`; "Liquidity Swings"/"Liquidity Sweeps" (TradingView open-source; descriptions) | §1.18 | n/a (definitions) | **[NEW-B]** code read / descriptions |

### 2.2 A's tests (7 datasets), re-checked [A-test, A✓ against raw outputs]

**Data and definitions.**
- S&P 500 D and NASDAQ D 1999-2019; GOOG D 2004-13; EURUSD 1H 2017-18; NQ, GC and EURUSD 1H 2024-26.
- pivLen-5 pivots; strict trade-through; equal prints within 0.10 ATR merge to the outermost; tests within 0.30 ATR, ≥ 3 bars apart.
- **Null**: distance-matched survival `S(d)` of the chart's own excursions, the engine's `f_potBase` idea.
- SEs are cluster-robust over 2K-bar blocks.

| Test | Result | Status |
|---|---|---|
| T1 sweep depth | Table 1.4; P(REJECT) 44.5%; no directional info by depth | A✓ |
| T1 burst | K3 +4.1 / +3.2 pp, +0.145 ATR; fades by K30 | A✓; extended in B2/B10 |
| T2 round magnet | Round − control reach: −4.5 to +10.9 pp across datasets (mixed) | A |
| T2 pass-through | Coarsest step: 77.3% vs 74.0% (+3.3 pp); finer steps 0 | A |
| T2d wick stops short | Weighted −4.2 ± 1.4 pp | A✓ raw; extended in B7 |
| T3 size features | Equal prints, tests, age: nothing. Prominence: K10 excursion +0.21 vs +0.06 ATR | A✓ raw |
| T4 invalidation buffer | Buffer from the **pool price**: 0.10 / 0.25 / 0.50 / 0.75 → win 41.8 / 42.5 / 43.7 / 44.6%, mean R −0.004 / −0.012 / −0.015 / −0.020 | A✓ raw. **[CORRECTED]** the engine is about the 0.30 row, not 0.10 (1.5) |
| T5 VP path | Thin +1.3 to +3.6 pp; thick −1.5 to +1.4 | A✓ raw |
| T6 wick lag | 60.8% re-taken within 5 bars; 38.3% become pivots | A✓ raw |

### 2.3 B's tests [B-test]

Additional data:
- Binance **BTCUSDC 1H** and **4H**, 2024-01 to 2025-11 (16,560 / 4,140 bars) with **taker-buy volume**, i.e. true aggressor delta per bar;
- **BTCUSDC 15m** 2020-01 to 2023-06 (105,000 bars, no taker field), also aggregated to 1H.

These are local copies of public exchange klines (test fixtures of an open-source Pine runtime). All pool and sweep detection reuses A's `sweep_depth.run` unchanged.

| ID | Question | Result |
|---|---|---|
| B1 | Real engine stop exposure (`enginestop.py`) | The stop is about 0.30 ATR beyond the pool. REJECT sweeps deeper: 41.0% pooled (30-47%); BTC 46-57%; all sweeps 63.9% |
| B2 | Sweep anatomy on BTC (`sweep_btc.py`) | Depth table 1.4; REJECT share 48-50%; burst K3 re-take +4.9 to +7.3 pp, throwback +1.0 to +6.2, excursion +0.23-0.36 ATR |
| B3 | True delta at sweep bars (`sweep_btc.py`) | 68.6% of REJECT bars have Δ into the pool; absorbed REJECT → continuation +4.7 ± 2.2 pp at K30; throwback 0 |
| B4 | Multi-bar classes (`reclaim.py`, `reclaim_race.py`) | RECLAIM 21-29% of sweeps; race excess −1.5 ± 0.7 pp (any), REJECT +0.5 ± 0.6, HOLD −0.6 ± 0.8 |
| B6 | Volume as pool size (`poolvol.py`) | Pivot RV high − low −1.5 pp; zone volume −0.5 pp; sign differs by market |
| B7 | Round wick-cap at other grids (`roundpen_steps.py`, `roundpen_btc.py`) | A's grid ×0.2 / ×0.5 / ×1 / ×2: −1.2 ± 0.7 / −3.7 ± 0.9 / −4.0 ± 1.3 / −3.7 ± 1.9 pp. BTC 500 / 1,000 / 2,500 / 5,000: −6.0 ± 0.6 / −4.1 ± 0.8 / −7.4 ± 1.3 / −2.3 ± 1.9 |
| B8 | Wick lag on BTC (`wicklag_btc.py`) | Re-taken within 5 bars: 54.3% (1H), 51.9% (15m), 48.1% (1H 20-23); next bar 27-30% |
| B9 | Liquidation heatmap proxy (`liqmap.py`) | Heaviest bin +0.7 ± 0.8 pp; random bin −0.1 ± 0.6 |
| B10 | Burst vs fast volatility (`burst_vs_vol.py`) | After ATR5/ATR50 decile match: intraday ×1.15-1.23 (K3), ×1.08-1.15 (K10), ×1.04-1.10 (K30); daily equities ×0.96-0.99 |
| B11 | Ledger baseline bias (`ledgerbias.py`) | Random 1-3 ATR level from sweep bars: BTC +2.1 to +3.4 pp; other intraday −0.6 to +1.0; daily −1.1 to +3.4 (GOOG, n 350) |
| D1 | Delta proxies vs truth (`deltaproxy.py`) | Sign agreement 60-66%; corr 0.19-0.34 |

Caveats:
- B7's BTC 15m and BTC 1H 2020-23 series cover the same period, so the BTC SEs are somewhat understated.
- Control-grid SEs in A's T2d treat the 8 offsets as independent. The round-side SE dominates anyway.
- Overlapping 30-bar windows are handled by cluster SEs.

### 2.4 Net reading for the forecasting problem
- **Which liquidity.**
  - Distance and volatility decide. For "size", only the source tier (how many participants watch the level) survives.
  - Equal prints, tests, age, volume and prominence do not move reach. Round numbers are not magnets.
  - The structural gap is **fresh extremes** (OF-1).
- **When.** The post-sweep burst is the one robust microstructure timing effect: intraday only, per-chart size, strongest on crypto (OF-6). It also biases the ledger's baseline on crypto.
- **How likely.**
  - Calibrated geometry (`f_pot`, `f_raceH`, the empirical surface) stays the backbone.
  - Microstructure fixes **geometry and honesty**: the learned stop band, the correct stop distance, round caps, and sweep classes as labels.
  - Directional reads from depth, reclaim, volume or delta are within ±2 pp, or contradicted.

---

## 3. Engine gap analysis (`baseline_v2.pine`, corrected)

| Concept | Status | Lines | What the engine does / what differs |
|---|---|---|---|
| Stops beyond swings (BSL/SSL) | present | 1753-1776; 623-624 | Pool = pivot price; zone `[P, P+0.20 ATR]`; strict trade-through. Matches L1/L3 (round) and L4/L5 (S/R) |
| Stop-zone depth | partial | 93; 1520 (`wPx`); 1762, 1774, 1848 | Fixed 0.20. Measured REJECT median 0.16-0.36 ATR by market (crypto deepest); no per-chart learning; no outer band |
| **Effective stop distance [CORRECTED]** | partial (honesty) | `f_invalidation` 1343-1356 (`buf` 1344; `lv.bottom − buf` 1352; swing fallback 1356) | About 0.30 ATR beyond the opposing pool (zone + buffer). Beaten by 41% of REJECT sweeps (BTC 46-57%). EV-neutral (T4) but no "beyond band" option |
| Zone depth leaks into scoring [NEW-B] | side effect | confluence window 675-676 (`this.bottom − confTol`, `this.top + confTol`); HOLD read 1581 (`close > lv.top`) | Deeper zones raise the confluence pillar and move the raid HOLD threshold. Any learned depth (OF-2) must decouple both (ICT-9 already decouples HOLD) |
| Round numbers | missing | — | Cap zones at the 00/50 grid; no bonus (OF-4) |
| Stacked pools | present (fixed rule) | 1230-1251; 684-685; 682 | Outermost-is-the-draw and +0.45·stack are unsupported magnitudes (ICT-10) |
| Post-sweep volatility burst | missing | 916 (`potSig` 50-bar stdev); 1302-1322 (model/baseline); 1360-1363 (race) | Intraday +15-23% range at 3 bars beyond what a fast-vol ratio predicts. Not in PoT, race or ETA. Baseline unconditional → crypto EDGE inflated by about 2-3 pp after sweeps |
| Sweep classification | partial / wrong sign | 1579-1582 | HOLD/REJECT only; ±tier into D; HOLD threshold = display input. No POKE/PROBE/ACCEPT/RECLAIM labels, no bar-close class alert (only the live touch alert at 1504-1509, 2087-2088) |
| Fresh-extreme liquidity (sweep wick) | missing | 1753-1776 | Wick is not a pool for pivLen bars (49-61% re-taken meanwhile). `f_invalidation` cannot use "beyond the sweep high" |
| Relative-equal asymmetry | partial | 1111-1131 | A right-hand print beyond the pool is booked as a raid plus a fresh single pool (`ict_liq` ICT-11). OF-1 fixes it naturally (§4) |
| Pool removal after sweep | present | 1583-1596 | Binary; matches the decision history. Residual after pokes is weak (+2.6 ± 1.6 pp) |
| Pool size: eq / tests / stack / prominence | wrong (magnitude) | 682; 650-658 | Unsupported rewards up to 5-15 points (ICT-10 / OF-3) |
| Pool size: age | wrong (shape) | 668-671 | Maturation ramp about 4 points for about 1 pp (WYK-2) |
| Pool size: volume [NEW-B] | absent (correctly) | — | Null and sign-unstable (B6). Do not add |
| VP path cost | partial | 1945-1947 | Thin ×1.10 weakly supported; thick ×0.85 unsupported (OF-5). Same line as ICT-5's opposing-FVG cost |
| Absorption / delta / footprint | missing (correctly for scoring) | 978-1009 (volume only in VP) | True-delta test contradicts the reversal reading; LTF proxy 60-66% accurate (OF-7 label only) |
| Icebergs | n/a | — | Not observable in TradingView data |
| Crypto liquidation levels | missing (correctly) | — | Proxy heatmap null (B9); OF-8 dropped |
| Killzone timing of raids | present | 597-602 | TIME study domain |
| Accuracy ledger | present | 1426-1499; `raceSt` 1079 | Strong base for every proposal. No sweep-class, wick or post-sweep cells. Baseline not vol-conditioned (B11) |

---

## 4. Proposals (best first; 7 kept)

General Pine v6 notes (doc-checked):
- New state goes in STATE (1020-1080), before any function that reads it. Pine has no forward references.
- Engine updates go inside `if barstate.isconfirmed` (1518).
- `array.percentile_linear_interpolation(id, percentage)` exists (`reference/array.md` 1085-1091; method form `a.percentile_linear_interpolation(50)`).
- `timeframe.change()`, `math.log10()`, `math.ceil()` and `timeframe.in_seconds()` exist (`reference/timeframe.md` 109, 166; `reference/math.md` 96, 189).
- `syminfo.volumetype` / `syminfo.type` are simple strings (`reference/syminfo.md` 829-843).
- New inputs use `display = display.none` (overhaul legend fix).
- The decision history is kept: strict trade-through for pools, draw-side-first selection, 2-bar challenger, 2× flip hysteresis.

### OF-1 (P1, S) · Instant sweep-wick pools: a fresh extreme is liquidity now, not pivLen bars later [A, sharpened]

**Why.**
- After a rejected sweep, the engine has no pool at the new wick until a pivot confirms it. By then 61% (A) and 48-54% (BTC) of wicks are already re-taken, at +4 to +6 pp above null in the first 3 bars.
- The liquidity map misses the most obvious level.
- `f_invalidation` cannot put a counter-target's stop "beyond the sweep high", which is where traders put it.
- It also fixes the relative-equal asymmetry: a 1-tick poke of a pool now leaves an EQ pool at the new print instead of nothing (ICT-11).

**Spec.**
1. Inputs (G_LIQ, after 99):
   ```pine
   bool useWick = input.bool(true, "BSL / SSL · Sweep Wicks (instant)", group = G_LIQ, display = display.none,
     tooltip = "A bar that trades through a pool and closes back inside leaves a pool at its wick at once (stops rest beyond every fresh extreme).")
   bool wickTgt = input.bool(false, "Sweep Wicks Can Be the DOL at Once", group = G_LIQ, display = display.none,
     tooltip = "Off: wick pools are drawn, stack and set stops at once, but become eligible as the DOL only after Swing Pivot Length bars, like a swing pivot.")
   ```
2. Types:
   - `Level`: `bool wick = false` (after `induce`, 340).
   - `Trial`: `bool wick = false` (after `liq`, 389).
3. Step 3 (1563-1589).
   - Before the loop:
     ```pine
     float wkH = na
     float wkL = na
     int   wkEqH = 0
     int   wkEqL = 0
     ```
   - Inside `if hit and lv.isLiquidity()` (1580), before the existing `liqEvt` lines:
     ```pine
     bool back = lv.side == 1 ? close < lv.price : close > lv.price
     if useWick and back
         float pk = (lv.side == 1 ? high - lv.price : lv.price - low) / atr
         if lv.side == 1
             wkH   := high
             wkEqH := pk <= eqTol ? math.max(wkEqH, lv.eqCount + 1) : wkEqH   // relative-equal poke (ICT-11)
         else
             wkL   := low
             wkEqL := pk <= eqTol ? math.max(wkEqL, lv.eqCount + 1) : wkEqL
     ```
4. New step 4b, after the registry drop (after 1596). Never push into `pool` while step 3 iterates it.
   ```pine
   if not na(wkH)
       float prW = (high - llR) / atr
       if not f_mergeLiq(pool, 0, high, 0, eqPx, prW, 1.0, false, bar_index, -1, -1)
           nextId += 1
           Level nw = f_newLevel(nextId, 0, 0, high + wPx, high, high, bar_index, bar_index, coilScore, indScore)
           nw.prom    := prW
           nw.wick    := true
           nw.eqCount := wkEqH
           pool.push(nw)
   // mirror for wkL: kind 1, zone [low - wPx, low], prom (hhR - low) / atr, eqCount wkEqL
   ```
   - When the pivot confirms pivLen bars later, step 9 calls `f_mergeLiq(..., countEq = true, pivBar = bar_index − pivLen)`. `f_mergeAt` sees `samePx and inBar`, because pivBar equals the wick pool's `bornBar`, so it adds no equal print (1112-1114). No duplicate, no fake EQ.
   - `llR`, `hhR`, `coilScore` and `indScore` are global series (881-895). With WYK-1, pass `COIL0` / `IND0`.
5. Eligibility in selection (step 19, 1971-1983):
   ```pine
   bool canT = wickTgt or not lv.wick or bar_index - lv.bornBar >= pivLen
   bool elig = (dirSide == 0 or lv.side == dirSide) and canT
   if canT and lv.score > gS
   ```
   Also add `canT` to the objective test (1980). `f_invalidation` (1346-1352) iterates `pool` unfiltered, so wick pools set stops at once with no change.
6. `tag()` (638-648): `if this.wick → t += " · WICK"`.
7. Ledger.
   - `f_openTrial` passes `wick = lv.wick and bar_index - lv.bornBar < pivLen`.
   - `var array<float> wkSt = array.from(0.0, 0.0, 0.0)` holds n, hits, ΣpBase, booked in `f_book` (1461).
   - Full view row: `WICK POOLS hit x% · base y% (n)`. It only fills when `wickTgt` is on.

**Measurement.**
- `useWick` A/B on race WIN / avg R (`raceSt`), because stops now use wick pools.
- Overall EDGE.
- Target switch rate (SMC-2).
- Expected: EDGE about the same; switch rate unchanged with `wickTgt` off.

**Evidence.** Moderate: T6 on 7 datasets plus BTC replication (B8); T1/B2 at K = 3; the L1/L3 mechanism.

**Risk.**
- More near-price pools, contained by `poolMax` eviction (1951) and by `wickTgt` off.
- Outside bars that reject both sides create both pools, which is correct.

**Effort.** S.

### OF-2 (P1, S) · Learned stop band, correct stop placement, and sweep classes including RECLAIM (absorbs ICT-7) [A, CORRECTED and extended]

**Why.**
- Stop depth differs by market (REJECT q50 0.16-0.36 ATR; BTC deepest). The fixed 0.20 is right only for some charts.
- The engine's real stop is about 0.30 ATR beyond the pool and is beaten by 41% of rejected sweeps (46-57% on BTC). A deeper stop buys win rate with R, not edge (T4). So show the band and offer the choice.
- **[CORRECTED]** A's spec `buf = clamp(bandQ80, ...)` was applied *beyond the zone edge*, so it would have stacked q80 on top of q50 (about 0.77 ATR).
- Classes (POKE / REJECT / PROBE / ACCEPT / RECLAIM) give the alerts and the ICT-2/ICT-9 cells a data-driven threshold.

**Spec.**
1. Inputs.
   - `zoneATR` keeps its default 0.20 and becomes the **prior**. Tooltip: "Measured medians: daily equities ~0.18, hourly FX/indices/metals ~0.25, crypto ~0.30."
   - Add:
     ```pine
     bool   zoneLearn = input.bool(true, "Learn Zone Depth From Sweeps", group = G_LIQ, display = display.none,
       tooltip = "Zone depth = median depth of sweeps on this chart that closed back inside (after 30 of them).")
     string invBufM   = input.string("Tight", "Stop Placement", options = ["Tight", "Beyond Stop Band"], group = G_DOL, display = display.none,
       tooltip = "Tight: just past the opposing pool's zone (about 0.3 ATR). Beyond Stop Band: past the 80th-percentile sweep depth on this chart. Wins more often with a smaller R; expectancy was the same in tests.")
     ```
2. State (STATE, before `f_invalidation` at 1343):
   ```pine
   var array<float> penRej  = array.new<float>()
   var float        bandQ50 = na
   var float        bandQ80 = na
   var array<float> rcPx    = array.new<float>()   // pending PROBE/ACCEPT sweeps, for RECLAIM
   var array<int>   rcSd    = array.new<int>()
   var array<int>   rcBr    = array.new<int>()
   var array<int>   rcAct   = array.new<int>()     // 1 if it was the active target
   ```
3. Engine start (1520). Replace `float wPx = zoneATR * atr` with:
   ```pine
   bool bandOK = zoneLearn and penRej.size() >= 30
   bandQ50 := bandOK ? penRej.percentile_linear_interpolation(50) : zoneATR
   bandQ80 := bandOK ? penRej.percentile_linear_interpolation(80) : 2.2 * zoneATR   // q80/q50 ≈ 2.2 on 11 series
   float wPx = zoneATR <= 0 ? 0.0 : f_clamp(bandQ50, 0.05, 0.60) * atr
   float a1  = nz(atr[1], atr)
   ```
   Existing pools keep their geometry; new pools use the learned depth.
4. RECLAIM check (start of step 3, before the pool loop):
   ```pine
   if rcPx.size() > 0
       for i = rcPx.size() - 1 to 0
           int  age = bar_index - rcBr.get(i)
           bool rc  = rcSd.get(i) == 1 ? close < rcPx.get(i) : close > rcPx.get(i)
           if rc and age <= 3
               swAlert := "DOL Engine ▸ failed break · reclaimed after " + str.tostring(age) + " bar(s) @ " + str.tostring(rcPx.get(i), format.mintick) + " · " + syminfo.ticker
           if rc or age >= 3
               rcPx.remove(i)
               rcSd.remove(i)
               rcBr.remove(i)
               rcAct.remove(i)
   ```
   Declare `string swAlert = ""` next to `newDolEvent` (1510), non-`var` so it resets each bar.
5. Step 3, in `if hit and lv.isLiquidity()` (1580):
   ```pine
   float pen = (lv.side == 1 ? high - lv.price : lv.price - low) / a1
   float clB = lv.side * (close - lv.price) / a1
   int   cls = clB < 0 ? (pen <= 0.05 ? 0 : 1) : clB < bandQ50 ? 2 : 3      // 0 POKE 1 REJECT 2 PROBE 3 ACCEPT
   if clB < 0
       penRej.push(pen)
       if penRej.size() > 300
           penRej.shift()
   else if rcPx.size() < 8
       rcPx.push(lv.price)
       rcSd.push(lv.side)
       rcBr.push(bar_index)
       rcAct.push(lv.id == activeId ? 1 : 0)
   if lv.id == activeId
       swAlert := "DOL Engine ▸ target swept · " + (cls == 0 ? "POKE" : cls == 1 ? "REJECT" : cls == 2 ? "PROBE" : "ACCEPT") +
         " · " + str.tostring(pen, "0.00") + " ATR deep · " + syminfo.ticker
   ```
6. `f_invalidation` (1343-1356): the stop is the *farther* of the current rule and the band edge.
   ```pine
   float buf  = 0.10 * atr
   bool  deep = invBufM == "Beyond Stop Band"
   ...
           if dd >= 0 and dd < best and dd / atr <= maxATR
               best := dd
               float far = tgt.side == 1 ? lv.bottom - buf : lv.top + buf
               float bnd = lv.price - tgt.side * (nz(bandQ80, 0.5) + 0.05) * atr
               inv := not deep ? far : tgt.side == 1 ? math.min(far, bnd) : math.max(far, bnd)
   ```
   The swing fallback (1356) uses `buf` as before, or `(bandQ80 + 0.05)·atr` when `deep`.
7. ALERTS section (after 2088): `if swAlert != "" → alert(swAlert, alert.freq_once_per_bar_close)`. The live intrabar touch alert (2087) stays, per the decision history.
8. Terminal line (TERMINAL PANEL 2289+): `STOP BAND q50 0.27 · q80 0.61 ATR (n 214) · stop 0.30 ATR beyond`.
9. Decouple the zone from scoring (2 lines).
   - Confluence window for liquidity: `aLo = this.price − confTol − (this.side == -1 ? zoneATR * atrV : 0)` and `aHi = this.price + confTol + (this.side == 1 ? zoneATR * atrV : 0)` (675-676). The pillar then keeps today's reach whatever depth is learned.
   - ICT-9's HOLD uses `holdATR` (or `nz(bandQ50, holdATR)`), never `lv.top`.
10. Ledger cells.
    - Feed `cls` and RECLAIM as ICT-2 learner cells (prior weight 0).
    - Coverage self-check: the share of `penRej` ≤ `bandQ80` should be about 80%.

**Measurement.**
- `invBufM` A/B on `raceSt`: WIN %, avg R, PF. Expect WIN +1-2 pp, R:R lower, EV within noise (T4).
- `zoneLearn` A/B on overall EDGE: expected neutral, given the confluence decoupling.

**Value.**
- Zones fit each market.
- The trader sees the stop-hunt band and chooses knowingly.
- Alerts say what kind of sweep happened, including failed breakouts.

**Evidence.** Moderate (A-T1/T4; B1, B2, B4).

**Risk.**
- Thin histories fall back to the prior until n = 30.
- A deeper stop lowers the displayed R:R, which is honest.

**Effort.** S.

### OF-6 (P2, S) · Post-sweep volatility state for PoT, race, ETA and the ledger baseline [A, UPGRADED from P3, spec revised]

**Why.**
- Intraday, the next 3 bars after any pool trade-through range +15-23% more than bars with the same ATR5/ATR50 ratio; still +4-10% at 30 bars (B10).
- On BTC the excursion excess is +0.23-0.36 ATR at 3 bars (B2).
- Daily equities show none, so the factor must be learned per chart.
- The engine's σ (`potSig`, 50-bar stdev, 916) and its empirical surface are unconditional. So:
  - short-horizon PoT, race and ETA are under-dispersed right after sweeps;
  - **the ledger baseline is too low exactly when trials open** (after the old target is swept): about +2-3 pp on BTC (B11).

**Spec.**
1. State (STATE):
   ```pine
   var int   lastSwp = -100000
   var float vb3     = 1.0
   var float vb10    = 1.0
   var float vbAll   = 1.0
   ```
   In step 3, on any liquidity hit: `lastSwp := bar_index`.
2. Every confirmed bar (engine block, after step 3):
   ```pine
   float rB  = (high - low) / a1
   vbAll := 0.995 * vbAll + 0.005 * rB
   int sAge = bar_index - lastSwp
   if sAge >= 1 and sAge <= 3
       vb3 := 0.97 * vb3 + 0.03 * rB
   else if sAge >= 4 and sAge <= 10
       vb10 := 0.98 * vb10 + 0.02 * rB
   ```
   Measure the bars after a sweep, not the sweep bar itself, so the triggering bar's own range is excluded.
3. Helper (STATE HELPERS, before `f_potModel` at 1302). It reads globals only:
   ```pine
   f_sigEff(int h) =>
       float f3  = f_clamp(vb3  / math.max(vbAll, 1e-9), 0.8, 1.6)
       float f10 = f_clamp(vb10 / math.max(vbAll, 1e-9), 0.8, 1.4)
       float s2  = 0.0
       for k = 1 to h
           int a = bar_index - lastSwp + k
           float f = a >= 1 and a <= 3 ? f3 : a >= 4 and a <= 10 ? f10 : 1.0
           s2 += f * f
       nz(potSig) * math.sqrt(s2 / math.max(h, 1))
   ```
   This is the variance sum over the horizon: the effect fades naturally at H = 30.
4. Use it consistently in the model **and** the baseline. Compute `float sigH = f_sigEff(H)` once per bar at the top of the engine block (a global `var float sigH`, assigned there).
   - In `f_potModel` (1304) and `f_potBase` (1315), use `sigH` in place of `nz(potSig)`. Query the empirical surface at `d / (atr * sigH / math.max(nz(potSig), 1e-9))`, i.e. distance in "effective ATR" (1307, 1318).
   - In `f_invalidation` (1360), use `sigH`.
   - In `evaluate`, pass `sigH` instead of `nz(potSig)` (call at 1948).
   - TIME-4's session-end PoT and the ETA use `f_sigEff(h)` with their own h.
5. Ledger check.
   - `Trial.swAge` = `bar_index − lastSwp` at open.
   - `var array<float> swCal = array.from(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)` holds [n, hits, ΣpBase] for trials opened ≤ 3 bars after a sweep, and the same for others.
   - Full view: `POST-SWEEP trials hit 41% vs base 40% (n 88) · others 38% vs 38%`.

**Pine notes.**
- At most a 30-iteration loop once per bar.
- No new `request.*`.
- `f_sigEff` must be declared after the state and before its first caller (`f_potModel` 1302). `potSig` is a global series declared at 916.

**Measurement.** Calibration of `pBase` and `pModel` for post-sweep vs other trials. Before the fix, post-sweep trials should beat `pBase` on crypto; after it, both groups should be calibrated.

**Evidence.** Moderate-strong for existence intraday (A-T1 8σ at K3; B2; B10 survives the vol control on 6 intraday series); per-chart size.

**Risk.** Low. Bounded factors with clamps, learned per chart, decaying. It must be coordinated with REG-1 / TIME-1 volatility clocks, which multiply the same σ (keep the factors multiplicative).

**Effort.** S.

### OF-4 (P2, S) · Round-number layer: cap zones on the 00/50 grid, optional stop snap, no score bonus (amends ICT-3) [A, CORRECTED grid]

**Why.**
- Order clustering at round numbers is the best-documented fact in the domain (L1, L2, L6, L7, L24, L25).
- On bars it is geometry:
  - not a magnet (T2: mixed sign);
  - the sweep wick stops short of a round beyond a pool (T2d −4.2 pp; B7: −3.7 ± 0.9 pp at half of A's grid, −7.4 ± 1.3 on BTC at 2,500);
  - once a coarse round is reached, it is passed +3.3 pp more often (T2; Donaldson & Kim).
- **[CORRECTED]** A capped only at the major step M. B7 shows the effect at M/2, i.e. "00 and 50" of the major figure (BTC 2,500 when M = 5,000; S&P 25; EURUSD 0.005). It fades at M/5 on A's datasets.

**Spec.**
1. Inputs (G_LIQ):
   ```pine
   string rnMode = input.string("Auto", "Round Numbers", options = ["Off", "Auto", "Manual"], group = G_LIQ, display = display.none)
   float  rnMan  = input.float(0.0, "Round Step (Manual)", minval = 0.0, group = G_LIQ, display = display.none)
   bool   rnConf = input.bool(false, "Round Numbers as Confluence", group = G_SCORE, display = display.none,
     tooltip = "Off = evidence default: round numbers are not reached more often than other prices on hourly/daily bars.")
   ```
2. Step (SERIES, global scope):
   ```pine
   bool  newDayRN = timeframe.change("D")
   float atrD     = nz(atrSlow) * math.sqrt(math.max(1.0, 86400.0 / chartS))
   var float rnStep = na
   if rnMode != "Off" and (na(rnStep) or newDayRN) and atrD > 0
       float e = math.pow(10, math.floor(math.log10(atrD)))
       float m = atrD / e
       rnStep := rnMode == "Manual" and rnMan > 0 ? rnMan : m <= 1.0 ? e : m <= 5.0 ? 5.0 * e : 10.0 * e
   float rnG = rnMode == "Off" ? na : rnStep / 2.0     // cap grid = 00 and 50 of the major figure
   ```
   Daily ATR scaled from the 200-bar ATR (875, 308).
3. **Zone cap** where BSL/SSL zones are built (1762, 1774, 1848, OF-1 step 4b):
   - BSL: `float R = math.ceil(ph / rnG) * rnG`; if `not na(rnG) and R > ph and R < ph + wPx` then the zone top = R.
   - SSL mirrors with `math.floor`.
   - The hit rule (trade-through of `price`) is unchanged.
4. **Stop snap** (`f_invalidation`, after the OF-2 computation). If a grid level R lies beyond the opposing pool within ±0.15 ATR of the computed stop, move the stop to `R ∓ 0.03·atr` (just past the round).
   - T2d: at 0.15-0.30 ATR beyond a pool, the wick passes a round 67.9% vs 71.6% for an arbitrary level.
   - This is weak-to-moderate; measure it with `raceSt`.
5. **Confluence** only if `rnConf`: push `math.ceil(close / rnG) * rnG` and `math.floor(close / rnG) * rnG` into `anchors` (1931).
6. **Ledger bit** `RN`: the target lies within 0.35 ATR inside a grid level. `rnSt = [n, hits, ΣpBase]`, shown in the Full view.

**Evidence.** Strong for placement; moderate for the bar geometry (A-T2/T2d, B7 on 9 datasets); moderate *negative* for the magnet.

**Risk.**
- Exotic symbols get an odd auto step; Manual covers that.
- ICT-3 must use this cap, not "extend past the round".

**Effort.** S.

### OF-3 (P2, S) · Pool-size model: one `evaluate()` edit that adopts ICT-10 + WYK-1 + WYK-2; no new size terms [A, CORRECTED]

**Why.**
- Every size proxy is null for reach at bar resolution: equal prints, tests, age, stack, volume (B6), and prominence (negative at 1H).
- The density term (682) gives up to 5-15 unsupported points; the freshness ramp (671) about 4.
- **[CORRECTED]** A's OF-3 formula conflicted with its siblings:
  - `dens = 1 − e^−x` with `0.45·min(stack,2)` and `0.8·prom`;
  - it dropped the coil/inducement terms, which shifts the liquidity-vs-array balance (`wyckoff_sd` WYK-1);
  - it kept stack and prominence rewards that `ict_liq` B4 / ICT-10 show to be null or negative for reach.
  - It is withdrawn in favour of one canonical line.

**Spec.** Implement once, in `evaluate` (661-696):
```pine
bool  ev = magModel == "Evidence"                                    // ICT-10 input, default "Evidence"
float cz = densIn == "Classic" ? this.coil   : COIL0                 // WYK-1
float iz = densIn == "Classic" ? this.induce : IND0
if this.isLiquidity()
    float dec  = math.pow(0.5, age / (4.0 * halfLife))               // WYK-2 "Flat"
    this.fresh := freshLiq == "Flat" ? dec : (0.35 + 0.65 * (1.0 - math.exp(-age / (0.25 * halfLife)))) * dec
...
    float x = ev ? 1.2 * this.tier() + 0.4 * math.min(1.0, this.prom / 3.0)
                 : 0.9 * this.eqCount + 0.45 * this.stack + 0.35 * math.min(this.tests, 6) + 0.8 * math.min(1.0, this.prom / 3.0) + 1.2 * this.tier()
    this.dens := 0.60 * (1.0 - math.exp(-x)) + 0.25 * cz + 0.15 * iz
    if this.inner and not ev
        this.mult *= 0.70
```
- **No volume term.** B6 is null and sign-unstable.
- **Display-only size.** Keep `EQx · STK · T` in `tag()`. Add to the HUD tooltip `size: tier HTF · prom 2.1 ATR · zone vol 1.8×` (facts, not weights).
- Equal prints, tests and `YOUNG`/`STALE` become ICT-1 ledger bits with zero prior.

**Measurement.** Evidence vs Classic A/B on overall EDGE, the CHART LIQ / EXT LIQ rows, and the switch rate.

**Evidence.** Moderate (A-T3, B6, `ict_liq` B2-B4, `wyckoff_sd` §2.4).

**Risk.** The README line "outermost pool in a stack is the draw" must change, or "ICT Classic" stays as the default if the user prefers the old behaviour.

**Effort.** S, shared with ICT-10 / WYK-1 / WYK-2.

### OF-5 (P2, S) · Volume-profile path cost: small thin-path bonus, drop the HVN-wall penalty [A✓]

**Why.**
- A thin path gives +1.3 to +3.6 pp, unstably. A thick path gives −1.5 to +1.4 pp (T5).
- ×0.85 is worth about 4-6 score points and can flip a selection on no evidence.
- Mechanism: gaps speed price up (L10). Traded volume is not resting liquidity in the path.

**Spec.** At 1947, in one edit together with ICT-5's opposing-FVG path cost:
```pine
lv.mult *= vf < 0.6 ? vpThin : vf > 1.4 ? vpThick : 1.0
```
- `vpThin = input.float(1.05, ...)`; `vpThick = input.float(1.00, ...)`; both G_SCORE with `display.none` and an evidence tooltip.

**Measurement.** A/B on overall EDGE.

**Evidence.** Weak (T5; L10 for the mechanism).

**Risk / effort.** Negligible / S.

### OF-7 (P3, M) · Opt-in delta context at sweeps (no "absorption → reversal" claim) [A, DOWNGRADED and re-specified]

**Why.**
- Traders ask for delta confirmation, and competitors offer it.
- B3: absorption is the norm on rejection bars (68.6%) and leans *continuation* (+4.7 ± 2.2 pp re-take at K30).
- D1: a lower-TF candle-sign or BVC proxy matches the true delta sign only 60-66% of the time.
- So A's tags (`ABSORBED`, `EXHAUSTED`, `DRIVEN`) would mislabel often and imply a reversal edge that does not exist. Offer neutral context only, graded by the ledger.

**Spec.**
1. Input `useDelta` (false), G_FLOW. Disabled when `syminfo.volumetype == "n/a"`.
2. Intrabar request:
   ```pine
   ltfD = timeframe.from_seconds(math.max(60, int(timeframe.in_seconds() / 24)))
   [ltO, ltC, ltV] = request.security_lower_tf(syminfo.tickerid, ltfD, [open, close, volume], ignore_invalid_timeframe = true)
   ```
   - This is one extra unique request.
   - Use ≥ 24 intrabars; D1 shows that 4-24 coarse intrabars add nothing. 100K intrabars ÷ 24 covers about 4,000 chart bars (`limitations.md` 263-271).
3. On a confirmed sweep bar only, compute BVC delta: `Δ = Σ V_i·(2·Φ(ΔP_i/σ_ltf) − 1)`, with Φ from the existing logistic or normal helper.
4. Label `Δ into pool 34% of vol` or `Δ away`, with a tooltip showing this chart's base rate ("68% of rejections show Δ into the pool") and the ledger outcome of each cell (ICT-2, prior weight 0).
5. Never feed D or the score.

**Evidence.** Weak; the bar-level reading is contradicted (B3, D1, L21, L27).

**Risk.**
- Users over-trust delta; the honest tooltip is mandatory.
- FX has tick volume only.

**Effort.** M.

### Considered and not proposed (with reasons)

| Item | Reason |
|---|---|
| A's OF-8: crypto estimated liquidation levels as a registry source | No published validation. B9 proxy heatmap edge +0.7 ± 0.8 pp (null). OI quality problems (L30). One extra request, map upkeep, and a contested `src` code (8 is taken by PA-1/PA-2/ACAD-5) |
| `request.footprint()` in the main script | Premium/Ultimate only and one call per script (docs). Would lock out most users |
| Absorption/exhaustion as a reversal signal or D input | Contradicted at bar level (B3) |
| RECLAIM / failed breakout as a D input | −1.5 ± 0.7 pp vs geometry, sign varies by dataset (B4). Label and cell only (OF-2) |
| Residual liquidity after shallow pokes (keep the pool alive) | +2.6 ± 1.6 pp; would break the trade-through decision. Covered by ICT-9's micro rule and OF-1's EQ carry-over |
| Pool-size terms from volume (pivot volume, zone volume) | Null and sign-unstable (B6) |
| Iceberg detection | Needs market-by-order data; refills < 1 s (L26) |
| Depth-based reversal reads | Null by depth bucket (T1) |
| Round-number score bonus or zone extension past the round | Not a magnet (T2); wick stops short (T2d, B7) |
| Bigger cascade target from pool size | Prominence effect +0.15 ATR at K10, too small to drive selection. At most a reach-band note |

---

## 5. Notes for implementers (coordination)

- **One `evaluate()` edit.** OF-3 = ICT-10 (`magModel`) + WYK-1 (`COIL0`/`IND0`) + WYK-2 (`freshLiq`), plus OF-2's confluence-window decoupling (675-676). Ship together.
- **Step 3 is shared** by OF-1 (wick flags), OF-2 (classes, `penRej`, RECLAIM queue), OF-6 (`lastSwp`), ICT-9 (per-side raid events) and ICT-11.
  - Compute `pen`, `clB` and `back` once per hit.
  - OF-1's `wkEq` carry-over implements ICT-11's relative-equal fix. Drop ICT-11's separate `ms*` arrays if OF-1 lands.
- **ICT-9 / ICT-2.** HOLD threshold = `holdATR` (or OF-2's `bandQ50`), never `lv.top`. POKE = ICT-9's `micro`. RECLAIM and the four classes are ICT-2 cells with prior 0.
- **ICT-3.** Use OF-4's cap on the M/2 grid. No extension past the round; confluence opt-in.
- **REG-1 / TIME-1 / TIME-4.** OF-6's factor multiplies σ on top of the volatility clock. Apply it to *both* `f_potModel` and `f_potBase`, or the EDGE baseline becomes biased in the other direction.
- **ICT-5.** The VP-path line (1945-1947) is edited by OF-5 and ICT-5 together.
- **`src` codes.** OF-8 is dropped, so no new code is requested here.
- Every proposal is measurable with the existing ledger (`stN/stK/stPE`, `raceSt`, `cluSt`) plus at most a 3-6-element feature array. None changes the hit rule, the non-repainting contract or the Clean look.

---

## 6. Sources

Literature and regulatory documents:
- Osler, C. (2003), "Currency orders and exchange rate dynamics: an explanation for the predictive success of technical analysis", J. Finance 58(5) 1791-1819; FRBNY SR125. https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr125.pdf ; https://ideas.repec.org/a/bla/jfinan/v58y2003i5p1791-1819.html
- Osler, C. (2005), "Stop-loss orders and price cascades in currency markets", JIMF; FRBNY SR150. https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr150.pdf (Tables I, V.B and VI.A read by A)
- Osler, C. (2000), "Support for resistance", FRBNY EPR 6(2). https://www.newyorkfed.org/research/epr/00v06n2/0007osle
- Kavajecz, K. & Odders-White, E. (2004), RFS 17(4) (via sibling `ict_liq`).
- Bhattacharya, U., Holden, C. & Jacobsen, S. (2012), Management Science 58(2). https://papers.ssrn.com/abstract=1569922
- Lallouache, M. & Abergel, F., arXiv 1307.5440. https://arxiv.org/abs/1307.5440
- Jung, J. & Lee, K. (2026), arXiv 2610.34787. https://arxiv.org/abs/2610.34787
- Garzarelli, F. et al. (2014), Sci. Rep. 4:4487; Chung, K. & Bellotti, A. (2021), arXiv 2101.07410. https://arxiv.org/abs/2101.07410
- Farmer, J. D. et al. (2004), arXiv cond-mat/0312703. https://arxiv.org/abs/cond-mat/0312703
- Cont, R., Kukanov, A. & Stoikov, S., arXiv 1011.6402. https://arxiv.org/abs/1011.6402
- Heston, S., Korajczyk, R. & Sadka, R. (2010), "Intraday patterns in the cross-section of stock returns", J. Finance. https://arxiv.org/abs/1005.3535
- Kitron, N. & Wengrowicz, J. (2026), arXiv 2608.21888. https://arxiv.org/abs/2608.21888
- Frey, S. & Sandås, P. (2017), QJF; CFR WP 09-06. https://www.cfr-cologne.de/download/workingpaper/cfr-09-06.pdf
- CFTC, Fett, N. & McPhail, L., "Stop Orders in Select Futures Markets" (summary). https://www.cftc.gov/About/EconomicAnalysis/ResearchPapers/index.htm
- Cheng, Z., Deng, J., Wang, T. & Yu, M. (2021), arXiv 2102.04591. https://arxiv.org/abs/2102.04591
- Garcia Seuma, R. M. (2026), arXiv 2608.03616 and 2607.27070. https://arxiv.org/abs/2608.03616 ; https://arxiv.org/abs/2607.27070
- Chitra, T. (2025), arXiv 2512.01112. https://arxiv.org/abs/2512.01112
- Brunnermeier, M. & Pedersen, L. (2005), "Predatory trading", J. Finance 60(4).
- Urquhart, A. (2017), Economics Letters 159. https://ideas.repec.org/a/eee/ecolet/v159y2017icp145-148.html
- Aggarwal, R. & Lucey, B. (2007), RFE 16(2); Lucey & O'Connor (2016), FRL.
- **[NEW-B]** UK FCA, "FCA fines five banks £1.1 billion for FX failings" (Nov 2014). https://www.fca.org.uk/news/press-releases/fca-fines-five-banks-%C2%A311-billion-fx-failings-and-announces-industry-wide-remediation-programme ; Citibank N.A. final notice https://fca.org.uk/your-fca/documents/final-notices/2014/citibank-na ; Barclays (May 2015) https://www.fca.org.uk/news/press-releases/fca-fines-barclays-284432000-forex-failings
- **[NEW-B]** Donaldson, R. G. & Kim, H. Y. (1993), "Price barriers in the Dow Jones Industrial Average", JFQA 28(3) 313-330. https://ideas.repec.org/a/cup/jfinqa/v28y1993i03p313-330_00.html
- **[NEW-B]** Cyree, K., Domian, D., Louton, D. & Yobaccio, E. (1999), "Evidence of psychological barriers in the conditional moments of major world stock indices", Review of Financial Economics 8.
- **[NEW-B]** Zotikov, D. & Antonov, A. (2019), "CME iceberg order detection and prediction", arXiv 1909.09495. https://arxiv.org/abs/1909.09495
- **[NEW-B]** Chakrabarty, B., Pascual, R. & Shkilko, A. (2015), J. Financial Markets 25, 52-79. https://papers.ssrn.com/abstract=2182819 ; Easley, D., López de Prado, M. & O'Hara, M. (2016), "Discerning information from trade data", JFE 120(2). https://papers.ssrn.com/abstract=1989555
- **[NEW-B]** Qin, B. & Yang, R. (2026), "Polymarket-v1 Database", arXiv 2606.04217. https://arxiv.org/abs/2606.04217
- **[NEW-B]** Kim, C. & Hansen, P. R. (2026), "The quarter-hour effect", arXiv 2607.09426. https://arxiv.org/abs/2607.09426
- **[NEW-B]** Wan, Y.-L. et al. (2015), arXiv 1503.03548; Wan et al. (2018), arXiv 1803.09422; Qi, B. (2023), PLoS One 10.1371/journal.pone.0287548.
- **[NEW-B]** Bar-Yam, Y., de Aguiar, M. & Bar-Yam, Y. (2014), "The 500.00 AAPL close", arXiv 1402.0910.
- **[NEW-B]** Giagkiozis, I. & Said, E. (2023), "Reconciling open interest with traded volume in perpetual swaps", arXiv 2310.14973.
- Kaminski, K. & Lo, A., "When do stop-loss rules stop losses?" https://dspace.mit.edu/bitstream/handle/1721.1/114876/Lo_When%20Do%20Stop-Loss.pdf
- Binance liquidation/maintenance-margin FAQ. https://www.binance.com/en/support/faq/b3c689c1f50a44cabb3a84e663b81d93
- Liquidation heatmap methods: https://research.glassnode.com/liquidation-heatmaps/ ; https://coinmarketcap.com/charts/liquidation-heatmap/
- Practitioner: BabyPips "Is forex rigged" (stop placement beyond highs/lows; cites Osler and the FCA). https://www.babypips.com/learn/forex/is-forex-rigged ; NinjaTrader footprint guide https://ninjatrader.com/futures/blogs/footprint-charts-guide/

Open-source implementations (concepts only; no code copied):
- `smartmoneyconcepts` (Python), `liquidity()`: https://github.com/joshyattridge/smart-money-concepts
- "Liquidity Swings" and "Liquidity Sweeps" (open-source TradingView scripts; descriptions via their library pages): https://www.luxalgo.com/library/indicator/liquidity-swings/ ; https://www.luxalgo.com/library/indicator/liquidity-sweeps

Pine v6 documentation (local mirror `docsrc/jabez4jc_pinescriptv6/`):
- `reference/request.md` 160-170 (`request.footprint`: Premium/Ultimate only; one call per script); 284+ (`request.security_lower_tf`);
- `writing_scripts/limitations.md` 202-221 (request limits; footprint note) and 263-271 (intrabars);
- `reference/array.md` 1085-1091; `reference/timeframe.md` 109-120, 132-138, 166; `reference/math.md` 96, 189; `reference/syminfo.md` 829-843.

Sibling studies used (`brief/study/`): `ict_liq.final.md` (E1, B2-B4, ICT-1/2/3/5/7/9/10/11), `wyckoff_sd.final.md` (§2.4, WYK-1/2), `ict_struct`, `bias_dol.final.md`, `academic_sr.md`, `session_stats.md` (TIME-4 / OF-6 link), `price_action.md` (src codes), `competitors.final.md`.

---

## 7. Reproducibility

A's scripts: `brief/study/orderflow_tools/` (run with `python3 -I <script>`; data through `wyckoff_tools/wyck.py`).

| Script | Test | Output |
|---|---|---|
| `sweep_depth.py [K]` | T1, T3 | `out_sweep_K{3,10,30}.txt` |
| `penstats.py` | pooled depth exceedances | `out_penstats.txt` |
| `roundnum.py` | T2 | `out_roundnum2.txt` |
| `roundpen.py [tol]` | T2d | `out_roundpen.txt`, `out_roundpen_tol.txt` |
| `invbuf.py [H]` | T4 (buffer measured from the **pool price**) | `out_invbuf.txt` |
| `pathvol.py [N]` | T5 | `out_pathvol*.txt` |
| `wicklag.py` | T6 | `out_wicklag.txt` |

B's scripts: `brief/study/orderflow_b_tools/` (reuse A's `sweep_depth.run` unchanged; BTC loader `btcload.py` reads local Binance kline JSON fixtures).

| Script | Test | Output |
|---|---|---|
| `enginestop.py` | B1 real stop exposure | `out_enginestop.txt` |
| `sweep_btc.py [K]` | B2 BTC anatomy and burst; B3 true delta at sweeps | `out_sweep_btc_K{3,10,30}.txt` |
| `reclaim.py [K]`, `reclaim_race.py` | B4 multi-bar classes (edges; race vs geometry) | `out_reclaim_K{10,30}.txt`, `out_reclaim_race.txt` |
| `poolvol.py` | B6 volume as pool size | `out_poolvol.txt` |
| `roundpen_steps.py`, `roundpen_btc.py [steps]` | B7 round wick-cap by grid | `out_roundpen_steps.txt`, `out_roundpen_btc.txt` |
| `wicklag_btc.py` | B8 wick lag on BTC | `out_wicklag_btc.txt` |
| `liqmap.py` | B9 liquidation-heatmap proxy | `out_liqmap.txt` |
| `burst_vs_vol.py` | B10 burst vs ATR5/ATR50 | `out_burst_vs_vol.txt` |
| `ledgerbias.py` | B11 ledger baseline after sweeps | `out_ledgerbias.txt` |
| `deltaproxy.py` | D1 delta proxies vs true taker delta | `out_deltaproxy.txt` |

Network notes:
- Exchange APIs, newyorkfed.org and fraser.stlouisfed.org were unreachable; the Firecrawl scrape credits were exhausted in this pass.
- Literature checks used the paper index (abstracts and full-text passages) and web search.
- No crypto open-interest data was available, so B9 uses taker flow as the ΔOI proxy.
