# SMT divergence and intermarket analysis for the DOL engine

Domain: ICT SMT divergence ("crack in correlation"), its relatives (PSP, triad SMT, inverse/DXY SMT, correlation regime), and how a correlated symbol can help predict **which liquidity the chart takes next, when, and how likely**.

Scope note: Firecrawl credits ran out at the start of this study, and the session's network blocks direct page fetches for most hosts (luxalgo.com, mql5.com, gitbook.io, tradingview.com, arxiv.org, ssrn.com). Web evidence therefore comes from (a) search-engine summaries of those pages, (b) public GitHub repositories cloned and read in full, and (c) an **original event study** I ran on 1-minute-to-1-hour CME futures data (ES, NQ, YM, RTY, GC, SI, 6E, 6B, MBT, MET). The event study is the main quantitative evidence here and is fully reproducible (scripts and outputs are listed in section 6).

---

## 0. Executive summary (read this if nothing else)

1. **SMT is not a reversal signal.** In every test I ran, a sweep with SMT (the chart takes its level, the comparison symbol fails to take its twin) reverses no more often than a sweep both symbols confirm:
   - 1-ATR reversal race: 50.5% with SMT vs 50.8% joint, n = 16,258 / 16,187. The 95% CI of the difference (day-cluster bootstrap) is [−2.2, +1.5] pp.
   - The result holds across 4 asset classes, 3 timeframes, pivot lengths 3 and 5, horizons 12 and 30 bars, a 0- or 1-bar decision delay, each killzone, each engine raid class, and at PDH/PDL.
   - Three independent public studies agree:
     - ES/NQ event study, n = 11k–141k: win rates 49.5–51.8%.
     - NQ/ES/YM/RTY 2018–26: "fading the leader's take won 47–51% of 1σ races … 88 tests, none beyond chance".
     - A carefully audited ES/NQ 1-minute SMT+FVG system, n ≈ 600 trades: expectancy −0.10 to −0.17 R, profit factor 0.75–0.85.
2. **What SMT does predict is that the laggard tends to sync.** When the comparison symbol takes its twin while the chart's matching pool is still intact, that pool is hit within H bars more often than a distance- and momentum-matched intact pool:
   - Lift 1.075 [1.057, 1.092] with no delay. Lift 1.054 [1.033, 1.077] with the 1-bar delay a non-repainting Pine feed imposes.
   - For pools more than 1 ATR away, the lift is 1.06–1.18 (1.10 with Pine timing at H = 12), a logit shift of +0.15 to +0.30.
   - The placebo test confirms the effect is real: shifting the comparison symbol 500 bars gives lift 1.017 [0.986, 1.047], which is null.
   - It holds in index, metals, FX and crypto, and on 5m, 15m and 1h.
   - The chart also takes its own pool before the opposite pool more often (70.9% vs 67.0% control). In the placebo that gap is 52.2% vs 51.1%.
3. **Timing of the sync.** After the sister leads, the chart follows within 1 bar 20–22% of the time, within 6 bars 44–51%, within 12 bars 54–61% and within 30 bars 69–73%. It never follows within 300 bars 9–11% of the time. Conditional on a sync, the median is 5 bars (5m/15m) and 7 bars (1h). The hazard decays: about 23%, 14%, 12%, 9% over the first four bars.
4. **Design consequence.** The optional SMT module should:
   - feed a **target-specific "sister-swept" boost** (score multiplier plus PoT logit shift, decaying with a half-life of about 8 bars), learned and verified by a small **sister ledger** against the engine's own distance-matched baseline (`f_potBase`);
   - **not** feed SMT into the draw vector D or the raid classification as reversal evidence by default. An "ICT reversal" reading can be offered only behind a ledger gate that proves it on the user's chart;
   - cost one `request.security` call (`[1]` offset, `lookahead_on`, chart timeframe, time-aligned). Total requests go from 6 to 7 of 40.

---

## 1. Concepts: definitions and parameters

### 1.1 SMT divergence (two-symbol swing SMT)
- **Practitioner definition** (ICT; LuxAlgo concept page; smartmoney gitbook): a non-confirmation between two positively correlated instruments at **matching swing points formed at the same time**.
  - Bearish SMT: A makes a higher high (trades through its prior swing high), and B makes a lower high (fails to trade through its time-matched swing high).
  - Bullish SMT is the mirror at lows.
  - Usual pairs: ES/NQ/YM (RTY), EURUSD/GBPUSD (vs DXY, inverse), gold/silver, BTC/ETH.
  - Practitioners read it as confirmation that the sweep was a "stop run" and expect reversal toward the opposite liquidity. It is "more meaningful in a killzone at a level of interest, less when correlation is drifting". It is "confluence, not a standalone trigger".
- **Algorithmic definition used by the best open implementations.** Synthesised from three sources:
  - the ES/NQ event study `thomas-quant/mss-research`;
  - the walk-back scanner `charisjv19/intermarket-divergence-scanner` v8.5–v8.10;
  - the Pine scripts *GXV SMT*, *Genjutsu Kai* and *Kodexius*.

  The rules:
  1. **Swing on A.** A pivot high at bar T with L left and L right bars (ta.pivothigh semantics), usable from bar T+L.
  2. **Twin on B.** B's extreme in a time window around T: `R_B = max(high_B[T−w .. T+w])`.
     - The scanner audit tightened the window from ±2 to 0 minutes ("exact parallel timestamps").
     - The event study requires the two most recent swings to be within ±1 bar.
     - Range-based variants match whole intervals instead: the same 15m/1H/4H/D candle, matched by open and close time (GXV `f_smt_intervals_match`).
  3. **B twin must be intact at confirmation.** B must not have traded through `R_B` between T+w and T+L. Otherwise the comparison is undefined.
  4. **Sweep test (strict).** A's high > P on bar t (wick break; the scanner switched from body to wick in v8.5). Equal is not a sweep, the same rule the engine uses at L622–624.
  5. **Divergence test.** B's high from T+w+1 through the decision bar has not exceeded `R_B`. GXV uses `XOR(A swept, B swept)`: exactly one market took its corresponding liquidity.
  6. **Grace / persistence.** Genjutsu Kai draws an SMT only after the sister fails for longer than a grace period (default 2 minutes). In its 2018–26 data the sister follows in the first minute 11–20% of the time, about half that in the second minute, and less after.
  7. **Minimum lag.** The leader must be ahead by more than k × σ(1-min return difference, 60 bars), with k = 0.87–1.65 by session. Otherwise it is a "hairline". It "removes clutter; it is not an edge filter".
  8. **Staleness.** The swing that gets swept must be recent and in the same session. The scanner uses 120 minutes on 1m (36 bars on 5m) for the newest swing and 90 minutes between the swept and the newest swing.
  9. **Invalidation.** The SMT is "broken" when the failing asset later trades through its twin (`thomas-quant/SMT` `break_tracker`). This is the same event as the sync below.
- **Parameters seen in the wild:**
  - pivot lookback L = 1 (event study), 3 (LuxAlgo default), 4 (scanner);
  - matching window ±0–2 bars;
  - lookback for the prior swing: 20 bars (event study) or 20 swings same-day (scanner);
  - timeframes: 1m–15m intraday (NY AM, London), 1H–4H for intraday bias, D/W for swing.

### 1.2 Range / time-interval SMT ("candle SMT", SSMT, quarterly)
- Compare the **previous interval's high/low** on both symbols: the previous 30m, 1H, 90m, 4H, D or W candle, or the session or quarterly-theory cycle.
- SMT when exactly one symbol trades through its previous-interval extreme during the current interval.
- GXV SMT Lite implements 13 interval ranks (15m … 12M), each matched by exact open/close times.
- Genjutsu Kai uses 30-minute ranges, hourly ranges on the :30 and the opening range, and tracks each SMT to **sync** or **hold** by the end of its window.
- For the engine this maps directly onto key pools that already exist: PDH/PDL, PWH/PWL, Asia/London/NY session highs and lows, HTF/STF pivots.

### 1.3 "Sick sister" / sync / laggard catch-up
- The market that fails is the "sick sister".
- **Sync**: the sister takes its twin later, so the move continues on both.
- **Hold**: it never takes it within the window.
- Genjutsu Kai estimates **sync odds**: a recalibrated random-walk hitting probability, `p = logistic(A + B·logit(2Φ(−gap/(κ·σ·√t_left))) + kind + session)`.
  - It was fitted on 2018–24 and tested on a locked 2025–26 set: **AUC 0.85**, with calibration within 6 points ("3→3%, 20→18%, 40→39%, 59→63%, 77→82%, 96→93%").
  - "53–64% of 30m SMTs held in every session but the post-close hour."
  - "It forecasts the sister's reach, not the direction after the window: held and synced SMTs were both coin flips afterwards."
- **DOL relevance.** This is the single most useful intermarket idea for a liquidity engine. If B has taken its twin and A has not, A's twin is a target with elevated probability of touch. My own study (section 2.3) confirms this with a placebo control.

### 1.4 Inverse-correlation SMT (DXY vs EURUSD/GBPUSD; also yields vs bonds)
- **Definition.** Replace B by its mirror. A higher high on EURUSD is compared with a lower low on DXY. Formally, use `high_B' = −low_B` and `low_B' = −high_B`, then apply the positive-correlation logic unchanged. GXV does this with its "normalized once into main-domain high/low" swap (`f_smt_build_sweeps`). Kodexius and Larper offer an "Inverse" toggle.
- **Facts.**
  - ICE USDX weights: EUR 57.6%, JPY 13.6%, GBP 11.9%, CAD 9.1%, SEK 4.2%, CHF 3.6%.
  - `USDX = 50.14348112 × EURUSD^−0.576 × USDJPY^0.136 × GBPUSD^−0.119 × USDCAD^0.091 × USDSEK^0.042 × USDCHF^0.036`.
  - So EURUSD and DXY are mechanically, strongly inverse. Forex.com quotes ρ = −0.97. Other vendors quote −0.915 to −0.93 on daily returns.
- **Pitfall.** Because EUR is 57.6% of DXY, EURUSD-vs-DXY SMT partly compares EURUSD with itself. GBPUSD or USDCHF carry more independent information.

### 1.5 Correlation regime (gate)
- SMT presumes a stable positive (or negative) correlation. Practitioners say a divergence "means less when the pair's correlation has visibly been drifting".
- **Measured return correlations** (log returns, this study's data; rolling-100 10th percentile in brackets):

  | Pair | 5m | 15m | 1h |
  |---|---|---|---|
  | ES–NQ | 0.96 (p10 0.92) | 0.96 | 0.97 (p10 0.88) |
  | ES–YM | 0.91 (0.75) | 0.92 | 0.90 (0.64) |
  | NQ–YM | 0.81 (0.53) | 0.82 | 0.81 (0.37) |
  | ES–RTY | 0.89 (0.70) | | 0.86 (0.54) |
  | GC–SI | 0.78 (0.63) | 0.80 | 0.22 * |
  | 6E–6B | 0.86 (0.76) | 0.89 | 0.90 |
  | MBT–MET | 0.82 (0.69) | 0.87 | 0.90 |

  \* The GC/SI 1h series in this dataset is nearly uncorrelated through 2025 at every lag (0.07–0.19), against 0.69–0.83 from Dec 2025. That looks like a continuous-contract data problem. GC/SI 1h results are therefore excluded from the headline numbers.
- **Algorithm.** `ρ = ta.correlation(rA, rB, 100)` on aligned 1-bar log returns.
  - If |ρ| < ρmin (0.5), SMT is off (state frozen).
  - If ρ < −ρmin, the pair is inverse in Auto mode.

### 1.6 PSP: precision swing point (candle-colour divergence)
- **Definition** (TradingFinder "Quarterly Theory ICT 03", cephxs/fadi PSP, Larper): at a swing (often a 3-candle pivot), the correlated assets' candles **close in opposite directions**. For example, ES closes bullish while NQ closes bearish at the high, read as a bearish PSP. Some versions require a pin bar. Implementations disagree on whether a doji counts as bullish.
- **Evidence (this study).** At the chart's sweep bar, PSP (B's candle closes the opposite colour) vs no PSP:
  - 1-ATR reversal race 50.4% vs 49.8%, n = 6,039 / 41,481; CI of the difference [−1.4, +2.7] pp.
  - Within SMT events: 49.8% vs 49.6%.
  - Grade: none.

### 1.7 Triad SMT (one versus two sisters)
- **Definition.** Three correlated indices (ES/NQ/YM). The divergence is stronger when one market disagrees with the other two.
- **Evidence (this study, ES/NQ/YM, 5m/15m/1h, 1-bar delay).**
  - The chart lags and one sister has taken its twin: lift 1.046 [1.010, 1.081], n = 4,286.
  - The chart lags and both sisters have taken their twins: lift 1.062 [1.018, 1.108], n = 1,757.
  - The CIs overlap, so the second sister adds little.

### 1.8 SMT at key levels and in killzones
- **ICT claim.** SMT matters most at HTF key levels (PDH/PDL, session highs/lows, ERL/IRL) inside killzones. A "2-stage crack in correlation" script argues that one crack is insufficient to establish a reversal.
- **Evidence (this study).**
  - PDH/PDL sweeps, 14 pair orientations, 5m/15m, Jan–Apr 2026, 922 events:
    - 1-ATR reversal: SMT 44.0% vs joint 44.8% (CI of difference [−15, +14] pp).
    - 2-ATR reversal: SMT 41.6% vs joint 59.2% at g = 0; 46.9% vs 50.3% at g = 1; 46.1% vs 52.7% at g = 3. If anything, SMT sweeps reversed less.
  - By killzone (5m/15m swing sweeps, 1-bar delay), 1-ATR reversal SMT vs joint:

    | Killzone | SMT | Joint | CI of difference |
    |---|---|---|---|
    | NY AM | 44.3% | 48.4% | [−8.6, +0.1] |
    | London | 51.0% | 48.4% | [−1.2, +6.7] |
    | Asia | 49.7% | 50.7% | |
    | NY PM | 52.2% | 51.1% | |

  - Grade: none for the reversal claim. Conditioning on key level or killzone does not rescue it.

### 1.9 Lead-lag and relative strength
- **Academic.** Cross-market lead-lag between index futures exists at the millisecond-to-second scale:
  - Dobrev & Schaumburg 2018 (Atlanta Fed conference): one market usually leads, e.g. DAX futures lead the E-mini.
  - The E-mini leads SPY with a price-change ratio of about 6.26 (Hayashi-Koike wavelet lead-lag literature).
  - At the 1-minute-plus bars Pine sees, this survives only as the **sync hazard** (section 1.3 / 2.4). It is not a tradable directional lead.
- **Practitioner use.** Trade the strongest index for longs and the weakest for shorts, i.e. pick which symbol's liquidity is the draw. No quantitative support was found. My laggard result points the other way from the folk reading: the *laggard's* untaken pool is the higher-probability target, not a sign of weakness that will fail.

### 1.10 Background theory
- **Dow Theory "confirmation"** (industrials and transports must confirm each other) is the ancestor of SMT. Brown, Goetzmann & Kumar (1998, *Journal of Finance* 53(4):1311–1333) found that Hamilton's Dow-theory timing produced positive risk-adjusted returns from 1902 to 1929. The paper does not isolate the confirmation rule. Grade: moderate for "Dow timing worked historically"; none for the intraday SMT analogue.
- **Pairs-trading convergence.** Gatev, Goetzmann & Rouwenhorst (2006, *RFS* 19(3):797–827): matched pairs whose normalised prices diverge by more than 2σ re-converge often enough to earn up to about 11% annualised excess return (1962–2002). Divergences between correlated assets tend to close, but the literature does not say *which leg* moves. My data says that at sweep time the laggard catching up (continuation) is more likely than chance. The leader reverting (reversal) is not.

---

## 2. Evidence: numbers and sources

### 2.1 Published or public quantitative studies

| Study | Data | Definition | Result | Grade |
|---|---|---|---|---|
| `thomas-quant/mss-research` (README, Sep 2026, after removing a look-ahead) | ES/NQ 1m, 5m, 15m; 141,382 / 30,819 / 11,078 SMT rows | k = 1 swings, twin within ±1 bar, lookback 20; labelled on the sweeping asset | Win % (5/15/30/60 bars): 1m 51.8/51.4/51.0/50.8; 5m 50.6/50.2/50.1/49.8; 15m 50.5/49.7/50.3/49.5. Mean aligned return −0.93 to +0.19 bp. The author: "no event family shows a visibly stable above-50% pattern … unresolved, not a negative result" (no intervals). | moderate (large n, public code; no CIs, overlapping events) |
| *Genjutsu Kai* v4 (`unclehk2000/genjutsu-kai`, README and Pine tooltips) | NQ–ES, NQ–YM, ES–YM, RTY–ES 1m, 2018–26, RTH and ETH; locked test 2025–26 | 30m/1H/opening-range interval SMT, 2-minute grace, auto minimum lag | "Fading the leader's take won 47–51% of 1σ races in every pair and session (88 tests, none beyond chance against matched controls)." "53–64% of 30m SMTs held." Sync-odds model AUC 0.85, calibrated within 6 pp. Roll-week fade 54% vs 49% (one fished head of 635; 58% on 30 test days) | moderate (large data, locked test; code public, data not) |
| `charisjv19/intermarket-divergence-scanner`, `backtesting_toolkit/entry_variants.md` | MES/MNQ 1m, six TradingView windows, live-achievable fills | Walk-back wick-break SMT, exact parallel timestamps, 15m bias, 5m confluence, FVG entry | v8.7: n = 675, E = −0.095 R, PF 0.852. v8.8: n = 597, E = −0.172 R, PF 0.754. v8.9: n = 596, E = −0.162 R, PF 0.767 | moderate (careful audit; small n) |
| MQL5 blog "SMT divergence tested: gold and silver, BTC and ETH, 216 tests" | XAU/XAG, BTC/ETH | n/a (page not fetchable) | The snippet warns that "9 out of 108 is not far from 5", i.e. hits at the false-positive rate | weak (summary only) |
| Vendor claims (Volity "70%+ in London–NY overlap", various) | undisclosed | undisclosed | The Right Trader and Velotrade both state that **no verified win rate exists** | none |

### 2.2 This study, Q1: does SMT at a sweep predict reversal or the next liquidity taken?
- **Data.** CME futures OHLC from github.com/axb0306/cme-futures-ohlc:
  - 1h, Mar 2025–Apr 2026: ES, NQ, YM, RTY, GC, SI;
  - 5m and 15m, Jan–Apr 2026: the same symbols;
  - 6E/6B, Mar–Apr 2026;
  - MBT/MET (micro BTC/ETH), Feb–Mar 2026.

  14 orientations: ES/NQ, NQ/ES, ES/YM, YM/ES, NQ/YM, YM/NQ, ES/RTY, RTY/ES, GC/SI, SI/GC, 6E/6B, 6B/6E, MBT/MET, MET/MBT.
- **Method.**
  - Bars of A and B are inner-joined.
  - A's pivots use L = 3 or 5. The twin is B's extreme within ±2 bars, and must be intact at confirmation.
  - A sweep is A's first strict trade-through within 300 bars.
  - Decision bar = sweep bar + g. g = 1 also delays B's data by 1 bar, which is what Pine can do without repainting.
  - Event types:
    - **smt**: B has not taken its twin by the decision bar;
    - **joint**: B took its twin on the same or a later bar, up to the decision bar;
    - **blead_then_a**: B took its twin before A.
  - Outcomes, measured from the decision close:
    - *race1*: −1 ATR (reversal) vs +1 ATR (continuation), whichever comes first within 4H;
    - *nextLiq*: the nearest live opposite pivot pool vs the next live pool beyond the sweep extreme, whichever is taken first within 5H;
    - the sign of the H-bar forward return.
  - CIs: Wilson for rates; day-cluster bootstrap for differences.

| Config | SMT race1 (rev) | Joint race1 | Δ CI (pp) | SMT nextLiq (opp first) | Joint | Δ CI (pp) |
|---|---|---|---|---|---|---|
| L3 H12 g0 | 50.5% (n 16,258) | 50.8% (16,187) | [−2.2, +1.5] | 39.0% | 37.0% | [−0.2, +4.0] |
| L3 H12 g1 + 1-bar delay | 49.7% (12,951) | 50.7% (19,835) | [−2.8, +0.7] | 46.2% | 42.9% | [+1.2, +5.3] |
| L5 H12 g0 | 50.1% (9,878) | 50.8% (8,486) | [−3.5, +2.0] | 35.4% | 34.8% | [−2.2, +3.0] |
| L5 H30 g0 | 50.1% | 50.8% | [−3.4, +2.0] | 36.6% | 36.5% | [−2.9, +2.6] |
| L5 H30 g1 + delay | 50.1% (8,112) | 51.0% (10,466) | [−2.9, +1.0] | 42.8% | 40.6% | [−0.7, +5.2] |
| Placebo (B shifted 500 bars) | 51.2% | 54.7% | — | 39.4% | 40.4% | — |

- **Fixed-horizon sign:** 49.6–51.6% in every config.
- **Continuous divergence.** Quintiles of (A's overshoot − B's overshoot) in ATR all give 50.2–51.3% race1.
- **Within the engine's raid classes** (sweep-bar close back inside = *reject*, beyond the 0.2-ATR zone = *hold*): SMT minus joint stays within about ±3 pp in every class and config. The class itself separates nextLiq far more:
  - L3 H12 g0: reject 44.9–45.6% vs hold 30.1–31.5% opposite-pool-first;
  - L5 H30 g0: reject 41.8–43.8% vs hold 30.0–31.5%.

  Caveat: part of that class effect is geometric. After a hold close, price sits farther from the opposite pool.
- **Verdict.**
  - SMT carries **no reversal information** for the 1-ATR race.
  - At most it adds a ≤3 pp tilt toward the opposite pool in some configurations, not robust across pivot lengths.
  - The engine's existing raid-close classification (L1578–1582) dominates it.

### 2.3 This study, Q2: the laggard sync ("sister-swept") effect
- **Event.** B trades through its twin while A's pool is still intact. Decision at B's sweep bar + d, with d = 0 or 1 for the Pine delay. A's pool must still be intact at the decision. Distance 0 < d ≤ 4 ATR.
- **Outcome.** A trades through its own pool within H bars.
- **Control.**
  - Intact pools (A and B both untouched) sampled every 3rd bar.
  - Matched on distance bin (0–0.25–0.5–1–1.5–2–3–4 ATR) × 3-bar return quintile × 12-bar return tercile.
  - Lift = Σhits / Σexpected. CI: day-cluster bootstrap.

| Config (metals-1h excluded) | n | Hit | Expected | Lift [95% CI] | Δlogit | Pools > 1 ATR: lift [CI], Δlogit |
|---|---|---|---|---|---|---|
| L3 H12, no delay | 14,831 | 62.9% | 58.6% | 1.075 [1.057, 1.092] | +0.18 | 1.176 [1.134, 1.218], +0.29 |
| **L3 H12, 1-bar delay (Pine)** | 11,422 | 54.0% | 51.2% | **1.054 [1.033, 1.077]** | +0.11 | **1.104 [1.070, 1.140], +0.17** |
| L5 H12, no delay | 8,986 | 60.2% | 55.2% | 1.090 [1.065, 1.116] | +0.20 | 1.182 [1.136, 1.230], +0.30 |
| L5 H30, 1-bar delay | 7,082 | 67.7% | 64.9% | 1.043 [1.022, 1.067] | +0.13 | 1.064 [1.032, 1.098], +0.15 |
| **Placebo** (B shifted 500 bars) | 15,582 | 43.3% | 42.6% | **1.017 [0.986, 1.047]** | +0.03 | 1.009 [0.967, 1.050] |

- **By asset class** (L3 H12, no delay, all TFs): index 1.069 [1.046, 1.089]; metals 1.160; FX 1.104 [1.057, 1.158]; crypto 1.118 [1.047, 1.189].
- **By timeframe:** 5m 1.073, 15m 1.087, 1h 1.121.
- **By distance** (L3 H12, no delay; laggard vs control hit rate):
  - 0–0.25 ATR: 91.1% vs 90.8%;
  - 0.5–1: 73.0% vs 69.7%;
  - 1–1.5: 61.6% vs 54.3%;
  - 1.5–2: 50.2% vs 41.5%;
  - 2–3: 35.5% vs 28.2%;
  - 3–4: 24.5% vs 16.4%.

  The effect lives in pools **more than about 1 ATR away**. Near pools are already close to certain.
- **Race.** The chart takes its own pool before the nearest opposite pool 70.9% of the time vs 67.0% for matched controls (placebo: 52.2% vs 51.1%).
- **Interpretation.** When the sister has already run the matching liquidity, the chart's matching pool is a better-than-distance target, i.e. a **continuation** cue. This is the opposite of the folk "SMT = reversal" reading. It is consistent with Genjutsu Kai's sync odds (AUC 0.85) and with pairs-trading convergence.

### 2.4 This study: sync timing (B leads, chart follows)
L3, all orientations, follow-up up to 300 bars:

| TF | n | ≤1 bar | ≤2 | ≤3 | ≤6 | ≤12 | ≤30 | never (300) | Median bars given sync | Hazard bars 1–4 |
|---|---|---|---|---|---|---|---|---|---|---|
| 5m | 8,394 | 21.2% | 31.1% | 38.0% | 49.4% | 60.9% | 72.9% | 9.3% | 5 | 23, 14, 12, 9% |
| 15m | 2,577 | 22.4% | 32.4% | 39.2% | 50.6% | 60.7% | 73.4% | 8.9% | 5 | 25, 15, 12, 10% |
| 1h | 2,693 | 19.6% | 27.9% | 33.5% | 43.6% | 53.6% | 68.8% | 10.8% | 7 | 22, 12, 9, 7% |

This supports a boost that decays with a half-life of about 6–8 bars, and an ETA readout of about 5 bars (intraday).

### 2.5 Evidence grades used below
- **"SMT is not a reversal signal": moderate.** Four independent quantitative sources agree with large n. None is peer-reviewed.
- **"Laggard sync lift ≈ 1.05–1.10 (Pine timing), larger for far pools": moderate.** One study (mine), placebo-controlled and consistent across 4 asset classes and 3 TFs. Short samples (3 months intraday, 13 months 1h). The finding is directionally consistent with Genjutsu Kai's sync-odds model.
- **PSP, triad increment, killzone or key-level SMT reversal: none / weak.**
- **DXY composition: strong** (ICE methodology).
- **EURUSD–DXY ρ ≈ −0.9 to −0.97: weak to moderate** (vendor statistics).

---

## 3. Engine gap analysis (baseline_v2.pine line refs)

| Concept | Status | Where / what differs |
|---|---|---|
| Second-symbol data feed | **missing** | All 5 `request.security` calls and the 1 `request.security_lower_tf` call use `syminfo.tickerid` (L923–925 structure, L939 HTF FVG, L981 1H OHLCV, L982 LTF). Budget used: 6 of 40 unique `request.*` calls (limitations.md: "up to 40 unique calls … or 64 … Ultimate plan"). |
| SMT at sweep (A leads, B fails) | **missing** | The sweep handler (L1575–1590) classifies only by the chart's close: `evt = close > lv.top ? +1 : close < lv.price ? −1 : 0`, folded into `liqEvt` by tier (L1579–1582). No twin, no sister state. Evidence says this omission costs nothing for reversal prediction. |
| Raid-close classification (hold = continuation, reject = reversal) | **present** | L1578–1582, decayed by `liqHL` (L1535), weighted `wL` = 0.30 in D (L1894). The study shows it separates next-liquidity side by about 11–15 pp while SMT adds ≤3 pp. Keep it; do not let SMT override it. |
| Sister-swept / laggard sync target | **missing** | No per-level cross-asset state. `Level` (L318–347) and `Ext` (L363–371) have no twin or state fields. Scoring (`evaluate`, L661–697) and the PoT (`f_potModel` L1303–1312, live readout L2066–2067) cannot use it. |
| Strict sweep definition (trade-through) | **present** | `touched()` L623–624. This matches the study's strict `>` / `<` and the scanner's wick-break rule. |
| Key-level twins (PDH/PDL, PWH/PWL, sessions, HTF/STF pivots) | **missing** | Key ranges come from `f_rangeTrack` (L815–840) and `f_sessTrack` (L843–867) on chart data only. MTF pivots are anchored via `f_barAtTime` (L1191–1209). There is no B counterpart. |
| Inverse correlation (DXY) | **missing** | — |
| Correlation regime gate | **missing** | — |
| Killzone affinity | **present** (different topic) | `f_kzAff` L596–601. There is no SMT × killzone interaction, and none should be added (evidence against). |
| Ledger infrastructure able to validate a new cue | **partial** | The Trial ledger (`f_openTrial` / `f_step` / `f_book`, L1426–1500) grades only the *active* DOL. `f_calMult` (L1376–1382) provides bounded per-family calibration and `f_raceAdj` (L1367–1371) a logit correction from observed outcomes. `f_potBase` (L1314–1324) is the distance-matched random-level baseline, exactly the control the sister ledger needs. The engine has no feature-conditional bucket (e.g. sister-swept vs not). |
| Alerts | **present, no SMT** | L2077–2094: four `alertcondition`s plus `alert()` messages. |
| Panel / HUD | **present, no SMT** | Terminal panel L2289–2434; Clean label and tooltip in RENDERING L2096–2287. |
| PSP, triad, continuous lag magnitude | **missing** (and **not recommended**) | Evidence none or weak. |

---

## 4. Proposals (best first; at most 10)

All proposals keep the engine non-repainting. Structural updates run inside `barstate.isconfirmed`. The new request uses `[1]` + `lookahead_on` on the chart timeframe, which the docs list as acceptable: lookahead is fine when "the `expression` argument … includes a *historical offset* (e.g., `close[1]`)" and when "the `timeframe` argument … represents the same timeframe as that of the chart" (concepts/other_timeframes_and_data.md). The module is **off by default**. With it off, the only cost is one inert request on the chart's own ticker.

### P1 · `smt-core`: optional correlated-symbol feed, twins and the sister state machine (P1, effort M, evidence moderate, infrastructure for P2–P6)

**Inputs** (new group `G_SMT = "SMT · Correlated Symbol"`, placed after `G_FLOW`, before L160):
```pine
bool   smtOn    = input.bool(false, "Enable SMT (correlated symbol)", group = G_SMT)
string smtSymIn = input.symbol("", "Compare With (empty = auto pair)", group = G_SMT)
string smtCorr  = input.string("Auto", "Correlation", options = ["Auto", "Positive", "Inverse"], group = G_SMT,
  tooltip = "Inverse mirrors the comparison symbol (e.g. DXY against EURUSD).")
float  smtRhoMin = input.float(0.50, "Min |correlation| (100 bars)", minval = 0.0, maxval = 1.0, step = 0.05, group = G_SMT)
int    smtW     = input.int(2, "Twin Window (± bars)", minval = 0, maxval = 10, group = G_SMT)
```

**Auto pair.** A string switch (string switch with a default branch is already verified to compile); `syminfo.root` is a "simple string":
```pine
f_smtAuto() =>
    switch syminfo.root
        "ES"  => "CME_MINI:NQ1!"
        "NQ"  => "CME_MINI:ES1!"
        "MES" => "CME_MINI:MNQ1!"
        "MNQ" => "CME_MINI:MES1!"
        "YM"  => "CME_MINI:ES1!"
        "MYM" => "CME_MINI:MES1!"
        "RTY" => "CME_MINI:ES1!"
        "M2K" => "CME_MINI:MES1!"
        "GC"  => "COMEX:SI1!"
        "SI"  => "COMEX:GC1!"
        => str.contains(syminfo.tickerid, "BTC") ? str.replace(syminfo.tickerid, "BTC", "ETH") :
           str.contains(syminfo.tickerid, "ETH") ? str.replace(syminfo.tickerid, "ETH", "BTC") :
           syminfo.ticker == "EURUSD" ? str.replace(syminfo.tickerid, "EURUSD", "GBPUSD") :
           syminfo.ticker == "GBPUSD" ? str.replace(syminfo.tickerid, "GBPUSD", "EURUSD") : ""
```
Notes:
- `str.replace(source, target, replacement, occurrence = 0)` and `str.contains` exist in v6 (reference/str.md).
- Exchange prefixes vary (e.g. YM lives on CBOT_MINI). With `ignore_invalid_symbol = true` a bad auto pick returns `na`, and the panel should show "SMT: no data". The user can always override.

**Feed** (SERIES, after L982):
```pine
string smtSym = smtSymIn != "" ? smtSymIn : f_smtAuto()
bool   smtReq = smtOn and smtSym != ""
[bOr, bHr, bLr, bCr, bTr] = request.security(smtReq ? smtSym : syminfo.tickerid, timeframe.period,
  [open[1], high[1], low[1], close[1], time[1]], lookahead = barmerge.lookahead_on, ignore_invalid_symbol = true)
bool  bAl     = smtReq and not na(bHr) and bTr == time[1]             // B's previous bar is the chart's previous bar
float rA      = bAl and bAl[1] ? math.log(close[1] / close[2]) : na
float rB      = bAl and bAl[1] ? math.log(bCr / bCr[1]) : na
float smtRhoV = ta.correlation(rA, rB, 100)                            // ta.correlation ignores na (reference/ta.md)
var int smtSign = 0                                                     // latched sign: +1 positive, -1 inverse
int sgnNow = smtCorr == "Inverse" ? -1 : smtCorr == "Positive" ? 1 : nz(smtRhoV) <= -smtRhoMin ? -1 : nz(smtRhoV) >= smtRhoMin ? 1 : 0
bool smtFlip = sgnNow != 0 and smtSign != 0 and sgnNow != smtSign     // Auto re-latch: invalidate every twin (sis := 0)
if sgnNow != 0
    smtSign := sgnNow
bool  smtLive = bAl and smtSign != 0 and math.abs(nz(smtRhoV)) >= smtRhoMin
float bHn = not bAl ? na : smtSign < 0 ? -bLr : bHr                    // B's previous-bar extremes, sign-normalised
float bLn = not bAl ? na : smtSign < 0 ? -bHr : bLr
```
The tuple has 5 elements, and the unique request count becomes 7 of 40.

Edge cases:
- Session mismatch (FX vs DXY, crypto 24/7 vs CME): unaligned bars give `bAl` = false, which freezes the state.
- Contract rolls: recommend back-adjusted continuous symbols; optionally ignore a B bar whose |log return| exceeds 8 × B's ATR%.

**Types** (TYPES, L318–371):
- Add to `Level`:
  - `float twin = na`
  - `int sis = 0`, where 0 = untracked, 1 = twin intact, 2 = sister swept first (the chart lags), 3 = the chart swept and the sister failed (SMT)
  - `int sisBar = na`
- Add the same three fields, with defaults, to `Ext`. Because they have defaults, the positional `Ext.new` at L1224 is unaffected.

**Twins** (STATE HELPERS, after `f_barAtTime` ~L1209; `bHn` is a global declared earlier, so there is no forward reference):
```pine
// Comparison-symbol extreme over chart bars [b0, b1]. B data is [1]-shifted: B's bar k sits on chart bar k + 1.
f_twinState(int b0, int b1, bool hi) =>
    float tw = na
    int   st = 0
    int   sb = na
    int   lo = math.max(b0, bar_index - 450)
    int   up = math.min(b1, bar_index - 1)
    if smtLive and up >= lo
        for k = lo to up
            float v = hi ? bHn[bar_index - k - 1] : bLn[bar_index - k - 1]
            if not na(v)
                tw := na(tw) ? v : hi ? math.max(tw, v) : math.min(tw, v)
        if not na(tw)
            st := 1
            if up + 1 <= bar_index - 1
                for k = up + 1 to bar_index - 1
                    float v = hi ? bHn[bar_index - k - 1] : bLn[bar_index - k - 1]
                    if not na(v) and (hi ? v > tw : v < tw)
                        st := 2
                        sb := k
                        break
    [tw, st, sb]
```
The offsets are at most 450, within the declared `max_bars_back = 500`. The loops run only at level birth.

Twin window per source:
- **Chart swings (src 0)**, at L1761/L1773 after `f_newLevel`: `[aBH − smtW, aBH + smtW]`.
- **STF/HTF pivots (src 1/2)**, at L1783–1789, passed into `f_pushExt`: `[a − smtW, a + r − 1 + smtW]`, with `a = f_barAtTime(pivT)` and `r = math.round(f_tfRatio(tf))`, i.e. B over the same HTF candle.
- **PDH/PDL, PWH/PWL, sessions (src 3–7):** B's own prior range, from lag-correct trackers fed with the shifted B bar:
  ```pine
  // On the chart bar that opens a new period, the [1]-shifted B bar still belongs to the old period: fold it in, then emit.
  f_rangeLag(bool inPrev, bool emit, float hi, float lo) =>
      var float rh = na
      var float rl = na
      float oh = na
      float ol = na
      if inPrev and not na(hi)
          rh := na(rh) ? hi : math.max(rh, hi)
          rl := na(rl) ? lo : math.min(rl, lo)
      if emit
          oh := rh
          ol := rl
          rh := na
          rl := na
      [oh, ol]
  [bPDH, bPDL] = f_rangeLag(true, pdNew, bHn, bLn)
  [bPWH, bPWL] = f_rangeLag(true, pwNew, bHn, bLn)
  [bAsH, bAsL] = f_rangeLag(inAs[1], asEnd, bHn, bLn)    // inAs = not na(time(timeframe.period, sessAs, tz))
  ```
  Same pattern for London and NY. Pass `(twin, 1, na)` into `f_pushExt`. Extend its signature with `float tw, int st, int sb`; on a duplicate, use `twin := isHigh ? max : min`.

**Merges.** In `f_mergeAt` (L1111) for an outer print, recompute the twin for the new print and keep the outermost: `twin := side == 1 ? math.max(twin, tw2) : math.min(twin, tw2)`. Copy `twin`, `sis` and `sisBar` in registry re-entry (L1846–1851).

**State update** (ENGINE, a new step "3a" inserted before the sweep loop at L1557; step 4 for `extReg`):
```pine
    if smtLive
        for lv in pool
            if lv.isLiquidity() and lv.sis == 1 and (lv.side == 1 ? bHn > lv.twin : bLn < lv.twin)
                lv.sis    := 2
                lv.sisBar := bar_index - 1
                smtLagEvt := true          // P5 alert / mark; P3 ledger record
        for e in extReg
            if e.sis == 1 and (e.isHigh ? bHn > e.twin : bLn < e.twin)
                e.sis    := 2
                e.sisBar := bar_index - 1
    if smtFlip
        // invalidate: sis := 0 for every pool and registry entry
```

**SMT at sweep (A leads).** In the sweep branch (L1578), when `lv.sis == 1`, push a pending record `{side, twin, bar, close, atr}`. On the **next** confirmed bar, when B's sweep-bar data arrives, resolve it:
- B took its twin → *joint* (late sync);
- otherwise → *SMT*.

This one-bar deferral is what keeps it non-repainting.

**Value.** Enables P2–P6. Cost: 1 request; about 100 extra comparisons per bar; 450-step loops only at level birth.
**Risk.** Auto-pair strings may be wrong for some feeds (mitigated by status text and the user override). Off by default.

### P2 · `smt-sync-boost`: sister-swept pools get a bounded score multiplier and a PoT logit shift (P1, effort S given P1, evidence moderate)

**Rationale.** Section 2.3: with Pine timing, lift is 1.054 overall and 1.10 for pools more than 1 ATR away (Δlogit +0.11 / +0.17), and the placebo is null. This is a *target-specific* cue. It changes which pool on the draw side is chosen, which is exactly the DOL question.

**Algorithm:**
- **Score.** In step 17 (L1938–1948), next to `f_kzAff` and `f_calMult`:
  ```pine
  if smtOn and smtMode != "Display only" and lv.isLiquidity() and lv.sis == 2
      float dk = math.pow(0.5, (bar_index - lv.sisBar) / smtHL)     // smtHL default 8 bars (sync hazard, sec. 2.4)
      float dA = math.max(0.0, lv.distance(close)) / atr
      float fa = f_clamp((dA - 0.5) / 1.0, 0.0, 1.0)                // no boost inside 0.5 ATR, full beyond 1.5 ATR
      lv.mult *= 1.0 + (f_sisLift() - 1.0) * dk * fa
  ```
  `f_sisLift()` comes from the P3 ledger and is shrunk toward the prior 1.06 (L3 H12 Pine-timing value, rounded). Bounds are [0.90, 1.25].
- **PoT.** In LIVE READOUTS (after L2067), when `activeLv.sis == 2`:
  ```pine
  float pb = smtSt.get(0) > 0 ? smtSt.get(2) / smtSt.get(0) : 0.4   // mean baseline in the sister ledger
  float dl = f_logit(math.min(0.99, f_sisLift() * pb)) - f_logit(pb)
  activePoT := math.min(0.95, f_sigm(f_logit(activePoT) + dl * dk * fa))
  ```
  `f_logit` and `f_sigm` already exist at L484/L488.
- The boost is **not** added to D. D drives side selection and the flip alert, and the cue is target-specific.

**Value.** Better choice among same-side pools: a pool the sister already ran beats an otherwise similar pool. The PoT is honest: +2 to +8 pp for far pools.
**Measurability.** The P3 ledger reports the realised lift on the user's chart and pair. The Trial ledger can also record `sis` at assertion (add `int sis` to `Trial`) so the DOL hit rate can be split by state.
**Risks:**
- The effect is modest. A 1.10 lift can be swamped by other pillars, which is fine.
- Data-quality pairs (GC/SI 2025 1h) can fake states. The correlation gate catches most of this.
- Double counting with the proximity pillar is avoided by the distance ramp `fa`.

### P3 · `smt-ledger`: live sister ledger (sync lift vs distance-matched baseline) plus an SMT-vs-joint reversal race (P1, effort M, evidence moderate)

**What it measures on the user's chart and pair.** These are the two questions this study answered:
- **Sync ledger.** Each pool (in the pool or the registry) that turns `sis = 2` while intact, with 0 < d ≤ maxATR, opens a light record `{side, edge = nearEdge, bar0, pBase = f_potBase(d, side)}`.
  - Each confirmed bar: if hit (`side == 1 ? high > edge : low < edge`), book K += 1, E += pBase, n += 1. If `bar_index − bar0 ≥ H`, book E += pBase, n += 1.
  - Cap 64 open records.
  - Show **SYNC ×(K+2)/(E+2)** with n, and a z-score `(K − E)/sqrt(Σp(1−p))`.
- **Reversal race.** Each resolved A-led sweep of a tracked pool (SMT or joint, from P1's pending list) opens a 1-ATR race from the decision close: reversal = −1 ATR first. Book wins and n separately for SMT and joint. Show **SMT-REV 49% (n 120) vs JOINT 51% (n 180)**.
- Storage: `var array<float> smtSt = array.new<float>(8, 0.0)`, a small `type SisT` and `type RaceT`, placed after `f_book` (~L1500) because they call `f_potBase` (L1314).

**Use:**
- `f_sisLift() = f_clamp((K + 20.0 * 1.06) / (E + 20.0), 0.90, 1.25)` feeds P2. The prior is worth 20 expected hits.
- The race z gates P4.

**Value.** It turns a contested ICT claim into a number the user sees for their own symbols, which matches the engine's existing "accuracy ledger against a random-level baseline" philosophy (README L87–91).
**Risk.** Small n on higher timeframes, hence the shrinkage prior. Overlapping records share price paths; reuse the 2H-block cluster variance from `f_book` (L1463–1469) for the z-score.

### P4 · `smt-no-reversal-default`: keep SMT out of D and the raid classification; offer a ledger-gated "ICT reversal" reading (P2, effort S, evidence moderate)

**Default ("Sync" reading).**
- An A-led SMT at a raid does **not** change `liqEvt` (L1579–1582) or D (L1892–1895).
- Evidence: SMT minus joint 1-ATR race CI [−2.8, +0.7] pp with Pine timing; no class or killzone rescues it; three external studies agree.

**Optional "Reversal (ledger-gated)" reading** for ICT purists:
- If the P3 race shows SMT-REV − JOINT-REV > 0 with z ≥ 2 and n ≥ 50 per arm, an A-led SMT at a liquidity raid adds `evt = −side × tier × 0.5` to `liqEvt`. That is half the weight of a reject.
- Until then it is display-only, and the panel says so: "ICT reversal: not supported on this chart (z = 0.4)".

**Value.** Prevents a popular but unsupported rule from degrading the draw vector, while giving users a transparent path to turn it on when their own data supports it.
**Risk.** Users expect "SMT = reversal". The tooltip and panel must explain the reason in one line.

### P5 · `smt-alerts-ux`: alerts, marks and panel rows (P2, effort S, evidence n/a: UX)

**Alerts** (two new `alertcondition`s at L2093, plus `alert()` messages, all bar close):
- **"SMT · Sister Took Liquidity"**: fires when a pool on the draw side (or the active DOL) turns `sis = 2`. Message: `"DOL Engine ▸ NQ1! took its BSL; ES lagging · BSL @ x · sync odds y% · ETA ~5 bars"`.
- **"SMT · Divergence at Sweep"**: fires when P1 resolves a pending sweep as SMT. Message: `"…chart swept BSL, NQ1! failed (SMT) · ledger: SMT-REV 49% vs 51%"`.

**Clean style:**
- Suffix the target label with `· SMT↻` when the active DOL is sister-swept.
- Tooltip: "NQ1! took its matching high 3 bars ago; this pool is the laggard. Sync odds +6 pp."
- No new table rows, keeping the reference look.

**Terminal style:**
- Row `SMT  NQ1! ρ .96  ▲LAG BSL 1.2ATR · sync ETA 5b`.
- Accuracy row `SYNC ×1.07 (n 212) · SMT-REV 49/51%`.
- Optional marks: a dashed line from the swept pivot to the sweep extreme, labelled `SMT` (chart led) or `↻` (sister led). Keep at most 12 with a FIFO like `f_ghost` (L1253). Respect the 500-line and 500-label caps.

**Risk.** Clutter. Marks are off by default in Clean.

### P6 · `smt-sync-eta`: sync ETA and boost decay learned from the live hazard (P3, effort S, evidence moderate)

- Record `bars from sis = 2 to the chart's sweep` for synced pools: an array of at most 300 values, like `ttHit` (L1067).
- Show the median as the ETA for a sister-swept target. Prior: 5 bars intraday, 7 bars on 1h (section 2.4).
- Set the P2 decay half-life to `max(3, median)` when n ≥ 30.

**Value.** Timing for the "when" question.
**Risk.** Minimal.

### P7 · `smt-key-range-mode`: interval SMT on the engine's key ranges, with exact interval matching (P3, effort S given P1, evidence weak)

- For PDH/PDL, PWH/PWL and session pools, P1 already uses B's own range extremes (`f_rangeLag`).
- Add an option to require **exact interval alignment**: B's day or session open and close times equal the chart's. Request `time` and `time_close` of B's daily bar in the same tuple, or compare session flags. This follows GXV's matching.
- It improves correctness when the pair has different trading hours (FX vs DXY, crypto vs CME).
- The PDH/PDL study shows no reversal edge (section 1.8), so the value is in correct **sync** states for the highest-tier pools, not in new signals.
- Risk: complexity. Most users of CME index pairs do not need it.

### P8 · `smt-triad`: optional second sister (P3, effort M, evidence weak)

- A second comparison symbol is one more request (8 of 40).
- A pool is "fully lagging" when both sisters took their twins. Lift 1.062 [1.018, 1.108] vs 1.046 [1.010, 1.081] for one sister. The difference is not significant.
- Use `max` of the per-sister lifts, or a 1.15 cap.
- Recommend only after P3 shows the single-sister lift is robust on the user's pair.
- Risk: more state per level, marginal gain.

**Not proposed (evidence none or against):**
- PSP candle-colour divergence (race CI [−1.4, +2.7] pp).
- SMT × killzone reversal weighting (NY AM SMT 44.3% vs joint 48.4%).
- Continuous lag-magnitude scoring (flat across quintiles).
- Roll-week fade (one fished head, 30 test days).

---

## 5. Pine v6 feasibility checklist (doc-grounded)
- **Request budget.** "A script can use up to 40 *unique* calls to the functions in the `request.*()` namespace, or up to 64 … Ultimate plan" (writing_scripts/limitations.md, around L206). The engine has 6; P1 adds 1 and P8 adds 1 more.
- **Non-repainting.** "The most reliable approach to achieve non-repainting results is to use an `expression` argument that only references past bars (e.g., `close[1]`) while using `barmerge.lookahead_on`" (concepts/other_timeframes_and_data.md, around L1398). The same page lists the chart's own timeframe as an acceptable case for lookahead. A `[1]`-shifted chart-TF request of another symbol is therefore safe. The cost is a 1-bar delay, and section 2.3 shows the lift survives it (1.075 → 1.054).
- **`ignore_invalid_symbol`** (input bool): "if `true`, the function will return `na` and execution will continue" (reference/request.md). `gaps` defaults to `gaps_off`, so alignment must be checked with `time[1]` (`bAl`).
- **`input.symbol(defval, title, …) → input string`** (reference/input.md L415–420). `syminfo.root` is a "simple string" (reference/syminfo.md L467–471).
- **`ta.correlation(source1, source2, length)`**: "`na` values in the `source` series are ignored" (reference/ta.md L491–510).
- **Dynamic history offsets** (`bHn[bar_index − k − 1]`) are bounded by `max_bars_back = 500` (indicator declaration, L31). Clamp the loops to 450.
- **No forward references.** Place the feed in SERIES (after L982), `f_twinState` and `f_rangeLag` in STATE HELPERS (after L1209), and the ledger helpers after `f_book` (L1500).
- **Drawing caps.** SMT marks are capped at 12 within the 500-line and 500-label limits.

---

## 6. Reproducibility (files)
- Data: `study/smt_data/cme/` (sparse clone of github.com/axb0306/cme-futures-ohlc: 1h, 15m and 5m for ES, NQ, YM, RTY, GC, SI; all files for 6E, 6B, MBT, MET, M6E, M6B).
- Scripts: `study/smt_tools/`
  - `smt_study.py`: Q1/Q2 event builder. Args: L H g dly shiftB.
  - `smt_report.py`: tables, Wilson CIs, day-cluster bootstrap.
  - `smt_keylevel.py`: PDH/PDL SMT.
  - `smt_strat.py`: killzone and PSP.
  - `smt_timing.py`: sync hazard.
  - `smt_triad.py`.
- Outputs: `study/smt_tools/`
  - `out_L3_H12_g0_d0_s0.txt`, `out_L3_H12_g1_d1_s0.txt`, `out_L5_H12_g0_d0_s0.txt`, `out_L5_H30_g0_d0_s0.txt`, `out_L5_H30_g1_d1_s0.txt`;
  - `out_L3_H12_g0_d0_s500.txt` (placebo);
  - `out_headline.txt`, `out_keylevel.txt`, `out_strat.txt`, `out_timing.txt`, `out_triad.txt`.
- Public code read (concepts only; no code copied): see Sources.
- **Limitations:**
  - Intraday samples are about 3 months (5m/15m) and 5 weeks (FX), about 1 month for crypto, and 13 months on 1h.
  - Both orientations of each pair are pooled. They share days, which the day clusters handle, but the effective n is about half the nominal.
  - Outcomes ignore costs.
  - The pool definition is a plain pivot (L = 3 or 5), not the engine's full pool logic (EQH merging, registry). Expect the same direction of effect, not the same magnitude.

---

## 7. Sources
- ICT SMT definitions (practitioner):
  - LuxAlgo concept page, https://www.luxalgo.com/library/concept/smart-money-technique-divergence.md (search summary)
  - Smart Money Concepts gitbook, https://smartmoney.gitbook.io/smart-money-concepts/strategy/ict-smt-divergence (search summary)
  - LuxAlgo SMT Divergences, https://www.luxalgo.com/library/indicator/SMT-Divergences-LuxAlgo/ and TradingView script ecEI56ff (swing lookback 3, ES/YM defaults, stats dashboard; search summary)
  - Kodexius SMT, https://it.tradingview.com/script/XEfw1eR7-SMT-Divergence-Kodexius (timestamp matching, inverse logic; search summary)
  - OutOfOptions, https://my.tradingview.com/script/WMgV6HcH-SMT-Divergences-OutOfOptions
  - 2-stage crack in correlation, https://it.tradingview.com/script/O74a2z84/
- PSP:
  - TradingFinder Quarterly Theory ICT 03, https://in.tradingview.com/script/EEKVmlUm-Quarterly-Theory-ICT-03-TradingFinder-Precision-Swing-Points/
  - cephxs/fadi HTF PSP, https://jp.tradingview.com/script/YoCpWBxb-cephxs-fadi-HTF-PSP/
- Quantitative SMT studies:
  - https://github.com/thomas-quant/mss-research (README: SMT win rates, labelling fixes)
  - https://github.com/thomas-quant/SMT (micro, swing and FVG SMT; break tracker)
  - https://github.com/unclehk2000/genjutsu-kai (README and Pine tooltips: 88 tests, 47–51%; sync-odds AUC 0.85; held 53–64%; grace hazard; minimum-lag k)
  - https://github.com/charisjv19/intermarket-divergence-scanner (README v8.5–v8.10 algorithm; `backtesting_toolkit/entry_variants.md`: n = 597–675, E −0.095 to −0.172 R, PF 0.75–0.85)
  - https://www.mql5.com/en/blogs/post/780472 (216 tests; snippet only)
  - No verified win rate: https://therighttrader.com/learn/smart-money-concepts/smt-divergence and https://velotrade.com/blog/smt-divergence
- Pine SMT implementations read for algorithms:
  - https://github.com/Gregorius-XV/GXV-SMT-Divergences (interval matching, XOR sweep, inverse normalisation)
  - https://github.com/samuelharting/bandz-smt-ssmt-divergence
  - https://github.com/DeolinNaidoo/TradingView-Larper-Indicator (inverse mode, PSP, SSMT)
- DXY:
  - ICE USDX brochure, https://www.ice.com/publicdocs/ICE_USDX_Brochure.pdf
  - USDX formula, https://wikipedia.com/wiki/USD_Index
  - EURUSD–DXY ρ −0.97, https://www.forex.com/ie/news-and-analysis/so-you-want-to-trade-the-dxy-eurusd-usdchf/
- Academic:
  - Brown, Goetzmann & Kumar (1998), "The Dow Theory: William Peter Hamilton's Track Record Reconsidered", *J. Finance* 53(4):1311–1333, https://econpapers.repec.org/RePEc:ysm:wpaper:ysm85
  - Gatev, Goetzmann & Rouwenhorst (2006), "Pairs Trading: Performance of a Relative-Value Arbitrage Rule", *RFS* 19(3):797–827, https://econpapers.repec.org/RePEc:oup:rfinst:v:19:y:2006:i:3:p:797-827 (NBER w7032)
  - Dobrev & Schaumburg (2018), "High-Frequency Cross-Market Trading", https://www.atlantafed.org/-/media/documents/news/conferences/2018/1018-financial-stability-implications-of-new-technology/papers/dobrev-schaumburg_high-frequency-cross-market-trading.pdf
  - Wavelet lead-lag, https://arxiv.org/pdf/1612.01232
- Data: https://github.com/axb0306/cme-futures-ohlc
- Pine docs (local mirror):
  - writing_scripts/limitations.md (request limits)
  - concepts/other_timeframes_and_data.md (lookahead, avoiding repainting)
  - concepts/repainting.md
  - reference/request.md, reference/input.md, reference/ta.md, reference/str.md, reference/syminfo.md
