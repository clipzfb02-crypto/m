# Academic evidence on price levels: study for DOL Engine v2

Domain: peer-reviewed, arXiv and SSRN evidence on support and resistance (S/R), level memory and decay, bounce vs penetration as a function of touches and time, round numbers, prior-high/low and N-period-high breakouts, 52-week-high anchoring, stop-loss cascades, the timing of daily highs and lows, and the probability that a previous extreme is exceeded. The aim is quantified priors the engine can use to answer "which liquidity is reached next, how likely, and when".

Line numbers refer to `brief/baseline_v2.pine`, which is identical to `indicators/dol_engine.pine`. Sibling studies in `brief/study/` are cited by proposal ID (ICT-1, SMC-3, WYK-2, OF-4, TIME-1, BIAS-3 and so on) wherever they already cover a topic. This report does not repeat their tests.

`[this study]` marks original tests. Scripts and raw outputs are in `brief/study/academic_tools/` (see Appendix A). Data: the 1-minute CME futures (ES, NQ, RTY, YM, GC, CL; 2026-01-20 to 2026-04-15, about 67-84k bars each) and 1-hour bars (2025-03 to 2026-04) that the AMT sibling downloaded to `brief/study/amt_data/cme/`.

---

## 0. Executive summary

1. **S/R memory is real, but it is a short-timescale effect.** Published FX levels stopped intraday trends 60.8% of the time, against 56.2% for 10,000 sets of arbitrary levels (Osler 2000, about 62,000 hits). Bounce probability rises with the number of prior bounces (Garzarelli et al. 2014; Chung & Bellotti 2021). The effect decays over hours.
   - **[this study]** 1-minute futures, about 80,000 approach episodes against a bar-shuffled no-memory null:
     - excess bounce on arrival of **+4.9 / +6.8 / +6.8 / +7.3 / +7.5 pp** for 1 / 2 / 3 / 4 / 5+ prior bounces (z 7-19);
     - the excess is positive in **6 of 6 symbols** and robust to stripe width and close vs high/low definitions.
   - On **1-hour** bars the effect is mixed and asset-specific: GC +17.7 pp, while ES, NQ and YM are −3 to −7 pp. Garzarelli also found no dependence at the 180-second scale.
2. **The memory decays, and then flips sign.** [this study]
   - Excess bounce is **+7 to +9 pp** when the last bounce was under 15 minutes ago, +3 to +5 pp at 1-4 h, and **negative** beyond about 4 h: **−3 to −5.5 pp in all 6 symbols**, and −7 to −15 pp at more than 12 h for multi-bounce levels.
   - Fresh levels are barriers. Levels that price comes back to after a long absence are penetrated **more** often than chance.
   - The crossover is about 4 h (≈250 one-minute bars), close to Chung & Bellotti's EURUSD figure of a 1-bounce level decaying to p = 0.5 at about a 350-minute window.
   - A compact fit for the excess: `E(b, Δt) ≈ (7 + 0.75·min(b−1, 4))·e^{−Δt/400} − 8·(1 − e^{−Δt/400})` pp, with Δt in bars on a 1-minute chart.
3. **In the engine's own terms (strict trade-through within H = 30 bars, against a distance-matched random level), pools are slightly sticky.** [this study, 1-minute]
   - All pools: −2.0 ± 0.3 pp.
   - The engine's test count adds nothing: 0 / 1 / 2 tests give −2.0 / −1.9 / −2.1 pp, and ≥3 tests give **−7.3 ± 3.6**.
   - Stale pools are reached less often: −7.5 pp when untouched for more than 12 h.
   - The density bonus `0.35·min(tests,6)` (682) and the freshness "maturation" ramp (671) have no support. Siblings SMC-3, WYK-1 and WYK-2 reached the same conclusion on 1H/daily bars.
4. **New, robust finding: path crowding.** [this study] A pool is reached less often, relative to its distance, for each unswept same-side pool between price and it.
   - 1-minute: 0 / 1 / 2 / ≥3 intermediate pools give −1.2 / −1.5 / −3.5 / **−6.1** pp.
   - 1-hour: −0.1 / −6.0 / −10.3 / **−29.3** pp.
   - It holds **inside** the engine's 0.75-ATR stack window too: the outer pool of a stack is reached 2-5 pp (1-minute) and 6-21 pp (1-hour) less often than its distance implies.
   - The engine does the opposite. Inner pools get ×0.70 (684-685), and the outer pool gets a density bonus of `+0.45·stack` (682).
   - This is consistent with the academic view that levels carry resting depth (Kavajecz & Odders-White 2004) and interrupt trends (Osler 2000). It is also consistent with ICT's "high-resistance liquidity run".
5. **Stop cascades exist, but they are small at bar resolution.**
   - Osler (2005): after crossing a round number, FX moves further than after crossing arbitrary levels, by 0.27-2.35 hundredths of a percent, for 15 minutes to 2 hours. The sign reverses at 1-2 days.
   - **[this study]** After a swing pool's trade-through, price is still beyond the level 30 and 120 minutes later in **+1.1 pp** more cases than after crossing an arbitrary grid level (z ≈ 2). The median 120-minute move is +0.25 ATR against −0.01.
   - Pools 4-12 h old show the largest effect: +5.1 pp at 120 minutes (z 3.3).
6. **Round numbers are barriers in some markets and not others, with pass-through acceleration.**
   - Evidence: USD/JPY yes and USD/DEM weak (De Grauwe & Decupere 1992); gold yes (Aggarwal & Lucey 2007); a buy-sell imbalance ordered by roundness (Bhattacharya, Holden & Jacobsen 2012); no longer depth-adjusted durations at round levels (Jung & Lee 2026).
   - The siblings' bar-level tests found round numbers are **not magnets**, and sweep wicks stop short of them (ICT-3, OF-4). This report adds no new round-number proposal.
7. **The 52-week high is the strongest anchoring evidence in finance, at monthly horizons and in stocks.**
   - George & Hwang (2004); Li & Yu (2012); Bhootra & Hur (2013): a more recent 52-week high adds about 0.70%/month.
   - Huddart, Lang & Yetman (2009): volume spikes when the 52-week extreme is crossed. Driessen, Lin & Van Hemert (2013): implied volatility falls on the approach and rises by more than 1 vol point after a breakthrough.
   - So these anchors are barriers that become continuation once broken. The engine has no 52-week or all-time extreme. Its value at intraday DOL horizons is untested.
8. **Prior-range breakouts.**
   - Daily trading-range-break rules were profitable on the DJIA from 1897 to 1986 (Brock, Lakonishok & LeBaron 1992). The edge did not survive out of sample after 1986 (Sullivan, Timmermann & White 1999).
   - Intraday opening-range breakouts are profitable only in some samples and decades (Holmberg et al. 2013). A 2026 MNQ walk-forward found that no OHLCV momentum or ORB family passes realistic costs.
   - A 2026 NQ test of ICT's AMD found no information beyond the daily trend regime: right 62-71% of the time with the trend, 25-30% against it.
   - Trend persistence lives at roughly 30 minutes to about 1-2 years. Below about 30 minutes markets mean-revert (Safari & Schmidhuber 2025). That is the same boundary where S/R bounce memory lives.
9. **Timing and previous extremes are mostly geometry.** Siblings covered these: arcsine law, volatility clock and previous-candle base rates (TIME-1, BIAS-1, BIAS-3). This report only adds the academic framing.
10. **What to build** (section 4), best first:
    - path crowding plus a neutral stack rule (ACAD-1);
    - an arrival vs through-given-arrival ledger that learns each chart's S/R memory (ACAD-2);
    - an S/R memory state and a last-mile barrier PoT (ACAD-3);
    - stale-pool raid weighting with clock-time decay (ACAD-4);
    - 52-week and all-time anchors (ACAD-5).

---

## 1. Concepts: definitions and parameters

### 1.1 Support/resistance as a barrier: bounce vs penetration
- **Osler (2000)**, the canonical test with published levels.
  - Levels: daily S/R levels published by 6 trading firms for DEM, JPY and GBP, 1996-98.
  - **Hit**: the bid (ask) comes within **0.01%** of a support (resistance) level. Robustness checks used 0.00% and 0.02%.
  - **Bounce / trend interruption**: 15 minutes after the hit, the rate is still on the near side of the level. 30 minutes was also tested.
  - **Control**: 10,000 sets of arbitrary levels.
- **Garzarelli, Cristelli, Pompa, Zaccaria & Pietronero (2014)**.
  - Price is sampled every τ ticks, at τ = 45, 60, 90 and 180 seconds of trading.
  - The level is a local max or min. Its **stripe** has width δ(τ), the mean absolute price increment at scale τ: the investors' "tolerance".
  - **Bounce**: price enters the stripe and leaves it on the same side, without crossing.
  - **b_prev**: the number of previous bounces on the level.
  - Estimator: `E[p(b|b_prev)] = (n+1)/(N+2)` (Beta posterior), compared with shuffled-return series.
- **Chung & Bellotti (2021)**.
  - Rolling window of length i minutes (the "lag window", 30-1,440 minutes).
  - Support = window minimum, with zone `[min, min + γ]`. Resistance = window maximum, with zone `[max − γ, max]`.
  - γ = the series' mean |Δx| (gives p ≈ 0.5 on random walks). The number of bounces is half the number of zone-boundary crossings in the window.
  - Discovery pauses while price is inside a zone. Outcome = bounce or penetration, with no time limit.
- **Engine equivalent.**
  - A liquidity pool is "hit" only on a strict trade-through (`touched`, 623-625), so a bounce at the level is a miss.
  - The test counter (`track`, 650-658) is a crude bounce counter: a bar within `testATR` = 0.30 ATR that does not take the pool, at least 3 bars after the last test. Its width matches Garzarelli's stripe at γ ≈ 0.5 × mean|ΔC| (0.30-0.38 ATR on 1-minute futures; see A.2).

### 1.2 Level memory and decay
- **Macro decay** (Chung & Bellotti): `p(b|b_prev)` falls as the discovery lag window lengthens. EURUSD: a 1-bounce level reaches 0.5 at about 350 minutes and a 4-bounce level at about 900 minutes. BRENT: a 1-bounce level drops **below 0.5** beyond about 300 minutes, so it predicts penetration.
- **Micro decay** (Chung & Bellotti): `logit p = a + b·X`, X = minutes since the last bounce, 600-minute window. EURUSD b_prev = 4: a = 0.402***, b = −0.00179*. b_prev = 5: a = 0.403**, b = −0.00273*. LLOY: all a > 0 and all b < 0. Most individual b coefficients are not significant.
- **Duration of published levels** (Osler 2000): predictive power lasts **at least five business days**.
- **Recurrence** (Garzarelli): the time between leaving and re-entering the stripe is power-law distributed, the same for real and shuffled series. Memory shows up in *what happens at the level*, not in how often price returns.
- **Mechanism.** Latent liquidity models (Bouchaud, Farmer & Lillo 2008; Benzaquen & Bouchaud 2017) store traded prices as slowly decaying latent order density. That gives multi-timescale memory without a single half-life.
- **[this study]** On 1-minute futures the memory crosses zero at about 4 h. In bars that is about 250 bars at a 1-minute resolution (§2.2). On 1-hour bars the picture is asset-specific.

### 1.3 Depth: why levels hold (mechanism)
- **Kavajecz & Odders-White (2004)**, NYSE SuperDOT.
  - Support is "the lowest bid reached **at least twice**" in the window, i.e. equal lows.
  - S/R levels coincide with peaks in limit-order-book depth. 84% of the technical-level vs depth series are cointegrated at 5%.
  - Limit orders do **not** cluster at the levels afterwards. Technical analysis *locates* existing depth.
- **Jung & Lee (2026, arXiv:2610.34787)**, Nasdaq LOB 2025: round levels attract more resting liquidity, but **do not** show longer depth-adjusted durations.

### 1.4 Stop-loss clustering and cascades
- **Osler (2003, J. Finance; RBS order book, about 9,700 orders):**
  - take-profits cluster **at** round numbers (9.3% exactly at "00");
  - stop-loss buys cluster **just above**: 14.4% in 01-10 vs 7.4% in 90-99;
  - stop-loss sells cluster just below.
  - Rates reverse at round numbers 4.6 pp more often than at arbitrary numbers.
- **Osler (2005, J. Int. Money & Finance; "Stop-loss orders and price cascades"):**
  - after a round number is crossed, the move is larger than after an arbitrary number is crossed: MVCR − MVRV = +0.27 to +2.35 hundredths of a percent at 15 minutes to 2 hours;
  - the effect is significant for at least 2 h, **not** at 1-2 days, where the signs turn negative.
- These numbers are documented in sibling ict_liq E1/E2 and orderflow_micro L1/L2. They are quoted here as priors.

### 1.5 Round numbers ("psychological barriers")
- **Test design.** Barrier tests (Donaldson & Kim 1993 on the DJIA; De Grauwe & Decupere 1992 on FX) look at:
  - the frequency of prices near M-digits (a barrier → fewer observations just below or above);
  - conditional mean and variance shifts as price approaches and after it crosses.
- **Results:**
  - USD/JPY: significant barriers at 10-yen levels; USD/DEM: unclear. After crossing, rates **accelerate away** (De Grauwe & Decupere).
  - Gold: barriers at the "00" level in conditional mean and variance (Aggarwal & Lucey 2007). Silver: none (Lucey & O'Connor 2016).
  - NYSE: excess liquidity-demander buying 1 cent below round numbers and selling above, ordered integer > half > quarter > dime (Bhattacharya, Holden & Jacobsen 2012).
  - EBS: algorithms front-run clusters by one tick (Lallouache & Abergel 2014).
- Siblings' bar-level tests (OF-4 T2) are summarised in §2.1 (S16).

### 1.6 Prior-high/low (trading-range) breakouts
- **Trading-range break** (Brock, Lakonishok & LeBaron 1992).
  - Buy when price exceeds the maximum of the previous n = 50, 150 or 200 days (with a 0% or 1% band). Sell on a break of the minimum.
  - DJIA 1897-1986: buy-signal returns were higher and less volatile than sell-signal returns, and random walk, AR(1), GARCH-M and EGARCH nulls do not explain them.
- **Data snooping** (Sullivan, Timmermann & White 1999). The best rule survives the reality check in sample, but its advantage **does not persist after 1986**.
- **Intraday opening-range breakout**:
  - crude oil futures 1983-2011, profitable mainly in the last decade (Holmberg, Lönnbark & Lundström 2013);
  - QQQ "stocks in play" variants (Zarattini & Aziz 2023, SSRN);
  - MNQ 2021-25 walk-forward: the ORB long fails stability (T = 0.88); no OHLCV momentum family passes all five criteria (arXiv:2605.04004).
- **Practitioner reading.** The prior high/low is a liquidity pool. Breaking it in the direction of the higher-timeframe trend is the continuation case; breaking it against the trend usually fails. See the AMD/NQ result in §2.1 (S24).

### 1.7 52-week high/low and anchoring
- **George & Hwang (2004).** Nearness = P / 52-week high. It dominates past returns in predicting momentum: the 52-week-high winner-minus-loser spread is about 0.45%/month (t = 2.00) to 1.23%/month (t = 7.06).
- **Li & Yu (2012).** Nearness of the Dow to its **52-week high predicts higher** market returns; nearness to its **historical high predicts lower** returns, across the G7.
- **Huddart, Lang & Yetman (2009).** Sample: 2,000 stocks, weekly, 1982-2006, above the 52-week high 13.4% of weeks and below the low 9.1%.
  - Volume rises sharply when price crosses either extreme and stays elevated for weeks.
  - Returns after crossing are positive for highs.
- **Driessen, Lin & Van Hemert (2013).** Implied volatility and beta **fall** as price approaches the 52-week high or low. Implied volatility **rises by more than 1 vol point after a breakthrough**: anchoring followed by attention.
- **Bhootra & Hur (2013).** Recency of the 52-week high adds about 0.70%/month between the top and bottom deciles.
- **Reading for DOL.** Widely watched extremes behave as barriers on approach (compressed volatility) and as continuation triggers once broken. The evidence is daily to monthly and mostly in stocks.

### 1.8 Conditional magnets
- **Option-strike pinning on expiration days.** Optionable stocks cluster at strikes (Ni, Pearson & Poteshman 2005). The S&P 500 futures are pinned toward strikes (Golez & Jackwerth 2012).
- **Price-limit magnet effect.** Prices accelerate toward the upper limit (Cho, Russell, Tiao & Tsay 2003, Taiwan).
- These are the only well-documented cases where a known level **attracts** price, and both need a hedging or limit mechanism. Generic S/R and round levels do not attract price (siblings' magnet tests; Jung & Lee 2026).

### 1.9 Timing of daily highs and lows
- **Arcsine law.** For Brownian motion on [0, T], the time of the maximum has density `1/(π√(t(T−t)))`, so first and last slices are over-represented.
- **In business time** (the intraday U-shaped volatility clock; Andersen & Bollerslev 1997, 1998), the open gets even more mass.
- **ES data** (mypivots, 1998-2004, 15-minute segments): the 09:30 segment holds 17.2% of highs of day and 16.7% of lows of day, against a uniform 3.7%. This is reproduced by an arcsine-plus-clock random walk (sibling ict_time §2.2-2.3).
- **For the engine.** Timing is a variance-clock problem (TIME-1, TIME-4), not a level property.

### 1.10 Probability that the previous day's (bar's) high or low is exceeded
- **Geometry.** For a driftless walk, P(H1 before L1) = (C − L1)/(H1 − L1), which is right 70-81% of the time (bias_dol §1.1, §2.4).
- **Base rates** (bias_dol §2.1):
  - next-day PDH taken: S&P 51.3%, NASDAQ 55.4%;
  - PDL taken: 44.6% / 46.5%;
  - either: 87-91%; within 3 days: 99.1% (S&P);
  - NQ 1H previous-bar extreme: either side 85.5%.
- **Forecastability.** Daily highs and lows are cointegrated and their range has long memory, so the high, low and range are partly forecastable (Caporin, Ranaldo & Santucci de Magistris 2013, FVECM). That supports the engine's volatility-scaled PoT rather than any "previous-day magnet".

### 1.11 Trend vs reversion timescales
- **Safari & Schmidhuber (2025)**: futures tick data plus centuries of daily and monthly data.
  - **Reversion regime below about 30 minutes.**
  - Weak trends **persist** from about 30 minutes, overcoming the tick-size reversion at a few hours, up to about 1-2 years. Strong trends revert.
  - The trend coefficient peaks at 3-12 months and has decayed over the decades.
- **Reading.** Bounces at levels (minutes) and breakouts that continue (hours) are the same market seen at two scales. The engine's draw vector (HTF structure) works on the trending scale. Level stickiness works on the reverting scale.

### 1.12 Bounce vs breakout as a function of touches and time since formation (synthesis)
| Condition | Next approach: bounce vs penetration | Source |
|---|---|---|
| More prior bounces, recent | Bounce more likely, by about +1 pp per extra bounce on top of about +5-7 pp | Garzarelli (HF); Chung & Bellotti (1-minute); [this study] |
| Last bounce more than about 4 h ago (1-minute scale) | **Penetration** more likely than chance, by −3 to −5.5 pp bounce; −7 to −15 pp at more than 12 h for multi-bounce levels | Chung & Bellotti (BRENT); [this study] |
| Hourly bars | Asset-specific; no universal sign | Garzarelli (no dependence at 180 s); [this study, 1H] |
| Vendor claim "hold rate flat with touch count" | 75.3 / 73.4 / 76.0 / 78.7% for touches 1-4 (unverified commercial PDF) | none |
| Practitioner claim "each touch weakens a level" | No quantitative support found | none |

### 1.13 Path crowding (new; [this study])
- **Definition.** For a target pool T on side s at distance d, `nIn` = the number of live (unswept) same-side pools strictly between price and T's near edge, with a 0.1-ATR margin.
- **Prediction.** Reach within H falls monotonically with `nIn`, beyond what distance explains.
- **Interpretation.**
  - Every intermediate pool is a small barrier: S/R depth (Kavajecz & Odders-White), trend interruption (Osler 2000).
  - A long staircase of unswept same-side swings marks a counter-trend target. This is ICT's high-resistance run and the "lower highs in a downtrend" picture.
  - The two causes are not separated here. For a forecaster both are useful.

---

## 2. Evidence (numbers and sources)

### 2.1 Literature table
| # | Claim | Source and sample | Numbers | Grade |
|---|---|---|---|---|
| S1 | Published S/R levels interrupt intraday trends more often than arbitrary levels | Osler 2000, FRBNY EPR 6(2); 6 firms, DEM/JPY/GBP, 1996-98, 1-minute quotes | Bounce 15 minutes after a hit: published **60.8%** vs arbitrary **56.2%** on average. DEM: arbitrary 54.9 vs firms 56.6-62.0. JPY: 57.3 vs 60.7-66.5. GBP: 56.3 vs 58.8-63.0. 1,039-8,111 hits per firm-currency pair. Lasts **≥ 5 business days**. Firms' strength ratings had **no** predictive value (the 3 significant differences were negative). 95.5% of levels end in 0 or 5 | strong |
| S2 | Bounce probability rises with prior bounces | Garzarelli et al. 2014, Sci. Rep. 4:4487; 9 LSE stocks, 2002 tick data | p(b\|b_prev) > 0.5 and rising in b_prev at τ = 45/60/90 s (χ² independence p < 0.0001). At 180 s: p = 0.077 (resistance) and 0.318 (support), not significant. Shuffled ≈ 0.5 and flat. Antipersistence (H ≈ 0.42-0.48) does not explain it | strong (HF only) |
| S3 | Same at 1 minute, with macro and micro decay | Chung & Bellotti 2021, arXiv:2101.07410; EURUSD, LLOY, BRENT 1-minute 2018 | Permutation Λ > 0.95 for most b_prev ≤ 6. EURUSD 1-bounce reaches 0.5 at about a 350-minute window, 4-bounce at about 900 minutes. BRENT 1-bounce falls below 0.5 beyond about 300 minutes. Micro decay EURUSD b_prev = 4: logit a = 0.40, slope −0.0018/minute | moderate |
| S4 | S/R = book depth | Kavajecz & Odders-White 2004, RFS 17(4) | 84% cointegrated at 5%; S/R significant for 49-73% of stocks. No new clustering of limit orders at the levels afterwards | strong (mechanism) |
| S5 | Stops beyond and take-profits at round numbers | Osler 2003, J. Finance 58(5) | TP 9.3% at 00; stop-buys 14.4% in 01-10 vs 7.4% in 90-99 (p = 0.029); reversals +4.6 pp at rounds | strong |
| S6 | Cascades after crossing stop clusters | Osler 2005, JIMF 24(2) | Extra move +0.27 to +2.35 hundredths of a percent at 15 minutes-2 h; gone or reversed at 1-2 days | strong |
| S7 | FX psychological barriers | De Grauwe & Decupere 1992, CEPR DP621 | USD/JPY significant; USD/DEM weak; acceleration after crossing | moderate |
| S8 | Gold barriers at 00 | Aggarwal & Lucey 2007, RFE 16 | Barriers in conditional mean and variance near 100s | moderate |
| S9 | Round-number trading imbalance | Bhattacharya, Holden & Jacobsen 2012, Mgmt Sci 58(2); > 100 m NYSE trades | Buy 1¢ below, sell 1¢ above; size ordered by roundness; about $1 bn per year cost | strong |
| S10 | Round levels: more depth, not longer holding | Jung & Lee 2026, arXiv:2610.34787; 5 Nasdaq stocks 2025 | No longer depth-adjusted durations; some departures biased away from round levels | moderate |
| S11 | 52-week high predicts continuation | George & Hwang 2004, J. Finance 59(5) | WML 0.45%/month (t = 2.00) to 1.23%/month (t = 7.06) | strong |
| S12 | 52-week high (+) vs historical high (−), index level | Li & Yu 2012, JFE 104(2) | Signs as stated; robust across G7 | strong |
| S13 | Crossing the 52-week extreme → volume burst | Huddart, Lang & Yetman 2009, Mgmt Sci 55(1); 2,000 stocks 1982-2006 | Volume up sharply when the extreme is crossed (abstract). Per a secondary summary: elevated for weeks; above the 52-week high 13.4% of weeks, below the low 9.1% | strong |
| S14 | Approach compresses volatility, breakthrough expands it | Driessen, Lin & Van Hemert 2013, Rev. Finance 17(1) | IV and beta fall on the approach (abstract); IV +1 vol point or more after a breakthrough (2011 working-paper figure) | strong |
| S15 | Recency of the 52-week high | Bhootra & Hur 2013, JBF 37(10) | About 0.70%/month top vs bottom recency decile | moderate-strong |
| S16 | Round numbers at bar resolution (siblings) | orderflow_micro T2 / T2d; 7 datasets | PASS at a coarse round +3.3 pp. Magnet test mixed sign. Sweep wick passes a round just beyond a pool −4.2 pp (≈ 3σ): it stops short | moderate |
| S17 | Trading-range-break rules | Brock, Lakonishok & LeBaron 1992, J. Finance 47(5); DJIA 1897-1986 | Buy-minus-sell returns significant; not explained by RW/AR/GARCH nulls | strong (historical) |
| S18 | ... but snooped / decayed | Sullivan, Timmermann & White 1999, J. Finance 54(5) | No out-of-sample advantage 1987-96 | strong |
| S19 | Intraday ORB | Holmberg, Lönnbark & Lundström 2013, FRL 10(1); crude oil futures 1983-2011 | Profitable, mainly in the last decade | moderate |
| S20 | ORB / momentum after costs (MNQ) | arXiv:2605.04004 (2026); 947 days of 5-minute data | No family passes all 5 criteria; ORB long T = 0.88, unstable by year | moderate |
| S21 | Trend vs reversion timescales | Safari & Schmidhuber 2025, arXiv:2501.16772 | Reversion below about 30 minutes; weak trends persist from 30 minutes to about 1-2 years | strong |
| S22 | Option pinning (conditional magnet) | Ni, Pearson & Poteshman 2005, JFE 78(1); Golez & Jackwerth 2012, JFE 106(3) | Clustering at strikes on expiration dates | strong (conditional) |
| S23 | Price-limit magnet | Cho, Russell, Tiao & Tsay 2003, J. Empirical Finance 10 | Acceleration toward the upper limit | strong (conditional) |
| S24 | ICT AMD on NQ | arXiv:2610.35887 (2026); 484 signal days | No information beyond the daily trend regime: with trend 62-71%, against 25-30% | moderate |
| S25 | High/low/range forecastable | Caporin, Ranaldo & Santucci de Magistris 2013, JBF 37(12) | FVECM: cointegrated H/L and long-memory range | strong |
| S26 | Timing of HOD/LOD; arcsine | ict_time E4/E5/E15; Andersen & Bollerslev 1997/98 | ES 09:30 segment HOD 17.2% vs 3.7% uniform, reproduced by an arcsine-plus-clock random walk | strong (null) |
| S27 | Previous-extreme base rates | bias_dol §2.1 | PDH taken next day S&P 51.3%, NASDAQ 55.4%; either 87-91% | moderate (descriptive) |
| S28 | Hitting times deviate from GBM | Valenti, Spagnolo & Bonanno 2006, arXiv:physics/0608201 | Empirical hitting-time PDFs fit Heston better than GBM | moderate |

### 2.2 [this study] S/R memory on 1-minute futures (`srmem.py`)

**Method** (a replication of S2/S3 in the engine's vocabulary).
- Levels: pivotLen-5 swing highs and lows (the engine's chart swings), live from confirmation to the first trade-through.
- Stripe g = k × mean|ΔClose|, with k = 0.5, 1 or 2. That is k = 1 ≈ 0.6-0.76 ATR(14) and k = 0.5 ≈ 0.30-0.38 ATR, about the engine's `testATR`.
- Episodes:
  - **bar** variant: an episode starts when the high reaches `P − g`. It is a penetration when `high > P` (the engine's sweep rule) and a bounce when the bar leaves the stripe downward first;
  - **close** variant: Chung & Bellotti's definition on closes.
- `b_prev` counts the pivot's own formation as the first bounce.
- Null: 3 replicas of the same series with whole bars (gap, high − open, low − open, close − open) permuted within each Globex day. This keeps the day's volatility and net move and destroys memory.
- Samples per run (n): about 80k real episodes; 6 symbols, 2026-01-20 to 2026-04-15.

**p(bounce | b_prev), real vs null (bar variant, k = 1):**

| b_prev | real (n) | null | excess | z |
|---|---|---|---|---|
| 1 | 0.399 (45,876) | 0.350 | **+4.9 pp** | 18.7 |
| 2 | 0.448 (18,042) | 0.380 | **+6.8** | 15.8 |
| 3 | 0.481 (7,981) | 0.413 | **+6.8** | 10.2 |
| 4 | 0.514 (3,788) | 0.441 | **+7.3** | 7.3 |
| 5+ | 0.555 (4,237) | 0.480 | **+7.5** | 7.6 |

The raw bounce rate rises with b_prev in the null as well (selection: levels that survive several bounces are in quieter places). The **excess** over the null still rises, from +4.9 to +7.5.

**Robustness (excess in pp for b_prev = 1 / 2 / 3 / 4 / 5+):**

| Variant | Excess (pp) |
|---|---|
| close, k = 1 | +6.9 / +8.9 / +8.6 / +9.8 / +10.9 |
| bar, k = 0.5 | +4.6 / +6.9 / +8.4 / +10.4 / +8.4 |
| bar, k = 2 | +4.2 / +4.7 / +5.6 / +4.8 / +5.5 |

Per symbol (bar, k = 1), all b_prev: ES +5.0, NQ +6.6, RTY +8.0, YM +8.5, GC +6.1, CL +4.0. **6 of 6 positive.**

**Decay: excess bounce by minutes since the last bounce (bar, k = 1):**

| Minutes | b_prev = 1 | b_prev ≥ 2 | b_prev ≥ 3 |
|---|---|---|---|
| < 15 | **+7.0** (n 25,131) | **+9.0** | **+9.3** |
| 15-60 | +5.8 | +7.3 | +7.1 |
| 60-240 | +3.3 | +4.7 | +3.4 |
| 240-720 | −1.1 | −2.3 | −4.1 |
| > 720 | **−8.6** (n 2,755) | **−6.6** | **−6.6** |

| Variant | b_prev ≥ 2 at < 15 min | b_prev ≥ 2 at > 12 h |
|---|---|---|
| close, k = 1 | +10.9 | −7.5 |
| bar, k = 0.5 | +10.1 | −8.4 |
| bar, k = 2 | +7.2 | −13.1 (b_prev ≥ 3: −15.3) |

**Per symbol (bar, k = 1), excess by minutes since the last bounce:**

| Symbol | < 60 min | 60-240 min | ≥ 240 min |
|---|---|---|---|
| ES | +6.2 | +3.7 | **−3.6** |
| NQ | +8.1 | +4.1 | **−3.0** |
| RTY | +10.0 | +4.9 | **−5.0** |
| YM | +10.3 | +6.9 | **−5.5** |
| GC | +7.5 | +5.2 | **−5.5** |
| CL | +5.5 | +0.1 | **−4.9** |

Every symbol shows the same pattern: a barrier when fresh and penetrable when stale.

**Parametric prior** (fit to the bar, k = 1 table; Δt in minutes = bars on 1-minute data):

```
E(b, Δt) [pp of bounce] = A(b)·e^(−Δt/τ) − c·(1 − e^(−Δt/τ))
A(b) = 7 + 0.75·min(b − 1, 4),  c = 8,  τ ≈ 400
```

- The zero crossing is at Δt ≈ 0.64·τ ≈ 260.
- The fit reproduces the table within about 1-2 pp except at 4-12 h, where it is about 1-2 pp too high for b = 1.

**Hourly bars** (`out_srmem_bar_g1_1h.txt`; 13 months, 5 null replicas).
- Pooled excess: +0.4 / +3.8 / +1.3 / +12.2 / +18.9 pp for b_prev 1 / 2 / 3 / 4 / 5+.
- Per symbol: GC **+17.7**, CL +0.5, RTY −0.1, YM −3.1, ES **−5.9**, NQ **−7.3**.
- Hourly S/R memory is asset-specific (it was a trending year in index futures). No universal prior is justified at 1H and above. This agrees with Garzarelli's null result at 180 s and with the siblings' 1H/daily tests (WYK §2.4).

### 2.3 [this study] Reach in the engine's terms (`reach.py`)

**Method.**
- Samples: every 15 bars, each live pivot pool 0.25-4 ATR from the close (81,209 samples).
- Outcome: strict trade-through within H = 30 bars.
- **Edge** = outcome − S(d). S(d) is the share of *all* bars whose 30-bar excursion toward that side exceeds d ATR (the `f_potBase` idea).
- Cluster SE by symbol-day.
- Tests use the engine's rule (0.30 ATR, ≥ 3 bars apart; `track`, 650-658).

**Results:**

| Slice | Edge (pp) | Hit % | n |
|---|---|---|---|
| All pools | **−2.0 ± 0.3** | 49.6 | 81,209 |
| tests 0 / 1 / 2 / ≥ 3 | −2.0 / −1.9 / −2.1 / **−7.3 ± 3.6** | — | 65,217 / 12,440 / 2,764 / 788 |
| since last test (or birth): < 15 minutes | −1.6 ± 0.3 | 56.8 | 27,864 |
| 15-60 minutes | −0.5 ± 0.3 | 48.6 | 26,420 |
| 1-4 h | −2.4 ± 0.6 | 45.0 | 14,000 |
| 4-12 h | −3.3 ± 1.2 | 43.6 | 6,153 |
| > 12 h | **−7.5 ± 1.1** | 39.3 | 6,772 |
| d 1-2 ATR, recent (< 60 minutes) vs stale (≥ 240 minutes) | −1.8 vs **−6.4** | — | — |
| d 2-4 ATR, recent vs stale | −0.5 vs **−5.3** | — | — |

**Reading.**
- Within a 30-bar horizon, the **conditional** memory (barrier when fresh) is diluted: price that bounces often comes back within H.
- What remains is that stale pools are reached less often than their distance implies. Old surviving pools sit in places price has been trending away from.
- Combined with §2.2: stale pools are **hard to reach**, but **once price arrives they break more easily**.
- The engine's test bonus is unsupported (≥ 3 tests is negative). Its freshness ramp, which gives pools 30-150 bars old the most points, is unsupported.

### 2.4 [this study] Path crowding (`barrier.py`)

**Method.**
- Same pools and outcome as §2.3.
- At each checkpoint, every live pool 1-4 ATR away is classified by the live same-side pools strictly between price and it (with a 0.1-ATR margin).
- Fresh = the intermediate pool formed or bounced within 60 minutes (stripe 0.5 × mean|ΔC|).

| Intermediate same-side pools (`nIn`) | 1-minute edge (pp), d 1-4 ATR | n | 1-hour edge (pp), d 1-4 ATR | n |
|---|---|---|---|---|
| 0 | −1.2 ± 0.2 | 39,503 | −0.1 ± 0.9 | 2,524 |
| 1 | −1.5 ± 0.3 | 19,604 | **−6.0 ± 1.9** | 1,339 |
| 2 | **−3.5 ± 0.6** | 8,492 | **−10.3 ± 4.7** | 600 |
| ≥ 3 | **−6.1 ± 1.3** | 6,157 | **−29.3 ± 5.5** | 555 |

**Within the engine's stack window** (the gap from target to the nearest inner pool < 0.75 ATR = `clusATR`):

| Inner pools | 1-minute edge (pp) | 1-hour edge (pp) |
|---|---|---|
| 1 | −2.0 ± 0.5 | −6.1 ± 2.5 |
| ≥ 2 | **−5.2 ± 0.9** | **−20.6 ± 6.5** |

When the gap is ≥ 0.75 ATR: −1.0 / −3.5 (1-minute) and −6.0 / −17.1 (1-hour).

- The **outermost** pool of a stack is reached **less** often than its distance implies. That is the opposite of the engine's rule, which multiplies the inner pool by ×0.70 (684-685) and gives the outer pool `+0.45·stack` (682).
- Fresh vs stale intermediates: at 1-minute, a stale intermediate is a slightly *stronger* barrier (−4.2 ± 1.1) than a fresh one (−1.8 to −2.8 pp). So in reach terms what matters is the *count*, not the bounce recency.
- Caveats:
  - The checkpoints overlap.
  - Trend confounding is likely: a staircase of lower highs in a downtrend.
  - At 1H, n is small.
  - The engine's draw vector already absorbs part of the trend effect. The ledger must measure the residual.

### 2.5 [this study] Cascade after a pool's trade-through (`cascade.py`)

**Method.**
- **PIVOT events**: the first trade-through of a pivotLen-5 swing (n = 56,750).
- **GRID events** (Osler's arbitrary-level control): the first cross of a level on a random-phase grid with a step of 2 × median ATR, after ≥ 10 bars on one side (n = 54,544).
- Outcomes at k = 5-120 minutes, in ATR(14) of the bar before the cross:
  - **hold** = the share of events where the close k bars later is still beyond the level;
  - median return from the level.
- Cluster SE by symbol-day.

**Results:**

| Horizon | Pivot hold | Grid hold | Difference | Median ret, pivot vs grid (ATR) |
|---|---|---|---|---|
| 30 minutes | 0.500 | 0.489 | **+1.1 pp (z 2.1)** | +0.02 vs −0.11 |
| 120 minutes | 0.510 | 0.499 | **+1.1 pp (z 2.0)** | +0.25 vs −0.01 |

By pool age at the break, 120 minutes:

| Pool age | Hold difference | Median ret (ATR) |
|---|---|---|
| < 60 minutes | +0.9 (z 1.9) | — |
| 1-4 h | −0.1 | — |
| **4-12 h** | **+5.1 pp (z 3.3)** | **+1.1** |
| > 12 h | +1.8 (z 0.9) | — |

- Means are dominated by heavy tails: the per-symbol pivot-minus-grid 30-minute mean is −0.53 ATR for CL and +0.44 for GC. Medians and hold shares are therefore reported.
- **Reading:**
  - Osler's continuation after crossing stop clusters is visible but small at bar resolution.
  - It is larger for old pools: those that were stale before the break are the ones where §2.2 found penetration more likely.
  - The siblings' T1 found the immediate post-sweep burst symmetric (volatility, not direction) over 3-10 bars. Both results can hold: a symmetric burst plus a small directional drift for old pools.

### 2.6 Limitations
- **1-minute:** one 3-month window (2026Q1) on 6 CME futures.
- **1-hour:** 13 months.
- **No FX or crypto** in the original tests. Osler, Chung and the siblings cover FX.
- **Shuffle null.** It keeps intraday volatility level and daily drift but destroys intraday trend persistence. Part of the "stale = penetrable" effect may be hour-scale trend persistence (S21) rather than level memory. For forecasting, the distinction does not matter.
- **Overlap.** Checkpoints overlap. Cluster SEs by symbol-day partly correct for it.
- **No transfer test to 5m and 15m charts.** The effect sizes there are assumed to lie between the 1-minute and 1-hour results.

### 2.7 Priors for the engine (summary)

| Quantity | Prior | Scope / timeframe | Strength of evidence |
|---|---|---|---|
| P(bounce \| arrival), excess over a no-memory level | `E(b, Δt)` from §2.2 (fresh +7 to +10 pp, stale −3 to −8 pp) | ≤ 5m charts; Δt in chart bars | strong (6/6 symbols + S2, S3) |
| Same, ≥ 15m charts | 0 (learn per chart) | 1H heterogeneous | — |
| Reach edge of a swing pool vs a random level | −2 pp | all timeframes (siblings: −1.4 pp at 1H/daily) | strong |
| Test count | 0 (≥ 3 tests: −7 ± 4 pp, weak) | — | moderate |
| Staleness (no interaction for > 4 h at 1m) | −3 to −7.5 pp reach | 1m; siblings: no age effect at 1H/daily | moderate |
| Path crowding per intermediate pool | −0.3 / −2.3 / −4.9 pp (1, 2, ≥ 3 vs 0) at 1m; −6 / −10 / −29 at 1H | all | moderate-strong |
| Post-sweep continuation (hold beyond the level) | +1 pp; +5 pp for pools 4-12 h old (120 minutes) | 1m | weak-moderate |
| Published-level life | ≥ 5 business days (Osler) | PDH/PDL/PWH class | strong |

---

## 3. Engine gap analysis (`baseline_v2.pine`)

| Concept | Status | Lines | What the engine does / what differs |
|---|---|---|---|
| Strict sweep = trade-through; touch ≠ sweep | present | 623-625, 1502-1505, `f_step` 1434-1459 | Consistent with Osler's stops just beyond and take-profits at the level. Keep it (decision history) |
| S/R barrier on arrival (bounce vs penetration) | **missing** | PoT: `f_pot` 434-445, `f_empPoT` 1284-1301, `f_potModel` 1303-1311, live readout 2067 | PoT is level-agnostic: distance and volatility only. At the level the readout tends to 95%, even for a pool that bounced price three times in the last 15 minutes (§2.2: P(through) is about 7-10 pp lower than a memory-free level) |
| Bounce count and recency (memory state) | **wrong** | `track` 650-658 (tests, ≥ 3 bars, 0.30 ATR, `gap > 0`), density 682 | Tests are counted and **rewarded monotonically** (`0.35·min(tests,6)`). Evidence: reach unchanged or negative with tests (§2.3). The conditional sign depends on recency (§2.2). No bounce timestamp is kept, only `lastTest` as a bar index |
| Memory decay / freshness | **wrong** | 671-673 (`fresh` ramp, half-life 150 bars), 1817 (registry eviction) | Pools "mature" for about 37 bars, then decay with a 600-bar half-life. Evidence: no maturation; stale pools at 1m are reached less often; memory decays on the level's own timescale (WYK-2 agrees) |
| Stacked pools / inner vs outer | **wrong (evidence-opposite)** | `f_stackSide` 1230-1251, 1912-1927, inner ×0.70 684-685, `+0.45·stack` 682 | Prefers the outermost pool. Evidence: the outer pool is reached 2-5 pp (1m) and 6-21 pp (1H) less often than its distance implies (§2.4) |
| Path crowding (unswept pools between price and target) | **missing** | step 17 (1929-1948) | Only the VP path cost (1945-1947). ICT-5 proposes array counts with weak evidence; §2.4 gives strong monotone numbers for same-side pools |
| Stop cascade after a sweep | partial | raid outcome 1580-1582, `liqHL` 159 (bars), `liqEvt` decay 1535 | A raid that holds → continuation, weighted by tier only, decay in bars (24 bars = 24 min on 1m, 4 days on 4H). Evidence: continuation is small, larger for old pools, effective 15 minutes-2 h (Osler) |
| Round numbers | missing | — | Covered by ICT-3 / OF-4 (barrier plus pass-through, not a magnet) |
| Prior-high/low breakouts (PDH/PDL/PWH/PWL, sessions) | present | 944-961, 1797-1822 | Registry sources with tiers (`f_tierW` 506-516). The hand-set tier ranks are not graded per chart. Osler: firms' "strength" ratings were useless, so learned weights are preferable (ICT-1) |
| N-period extremes (20/40/60-day, 52-week, ATH) | **missing** | — | No 52-week or all-time anchor. ICTPD-5 / TIME-8 propose 20/40/60-day extremes; 52-week and ATH have the strongest anchoring literature (S11-S15) |
| Timing of highs/lows | partial | killzones 970-976, `f_kzAff` 597-602 | Fixed affinities. Timing is arcsine plus clock (TIME-1, TIME-5) |
| PDH/PDL exceed probability | present (via PoT) | `f_potModel` 1303 | Geometry-consistent. Base rates are not displayed (BIAS-3) |
| Trend vs reversion timescale | partial | D vector 1891-1899 | D uses HTF structure (trend scale, correct). Level stickiness (reversion scale) is not modelled |
| Arbitrary-level baseline for grading | present | `f_potBase` 1314-1322, `f_book` 1461-1499 | Osler-style "random level at the same distance". Only the active DOL is graded, and only "hit within H". No arrival vs through-given-arrival split |
| Level-state calibration | missing | `f_calMult` 1376-1382 (4 families) | No conditioning on b, recency or `nIn`. The ICT-1 candidate ledger would provide it |

---

## 4. Proposals (best first; maximum 10)

All proposals keep the decision history: strict trade-through sweeps, draw-side-first selection, two-bar challenger and 2× flip hysteresis, Day Trading mode = D / 4H / 1H. Logic runs on `barstate.isconfirmed`. There are no new lower-timeframe requests.

### ACAD-1 (P1, S) · Path-crowding prior and a neutral stack rule

**Why.**
- The strongest, most robust level effect found here is path crowding (§2.4): monotone in `nIn` on 6 futures at 1m and 1H, and present inside the engine's own stack window.
- The engine currently pushes selection the wrong way: it prefers the outermost pool of a stack and penalises the inner pool, which must be reached first.

**Inputs** (G_SCORE, after 152):
```pine
string stackMode = input.string("Neutral", "Stacked Pools", options = ["Neutral", "Outermost (ICT)"], group = G_SCORE,
  tooltip = "Neutral: no inner-pool penalty and no stack bonus (evidence: the outer pool of a stack is reached less often than its distance implies). Outermost: the original ICT rule.")
float crowdW = input.float(1.0, "Path Crowding Strength", minval = 0.0, maxval = 2.0, step = 0.1, group = G_SCORE,
  tooltip = "Each unswept same-side pool between price and a target lowers its reach. 0 = off. Learned per chart by the ledger.")
```

**Type `Level` (317-348).** Add `int nIn = 0`.

**Step 16** (after `f_stackSide`, 1927). An O(n²) count; n ≤ 40, so at most 1,600 compares on `inCalc` bars only:
```pine
for lv in pool
    int   k = 0
    float e = lv.nearEdge()
    for o in pool
        if o.isLiquidity() and o.side == lv.side and o.id != lv.id
            float oe = o.nearEdge()
            if lv.side == 1 ? (oe > close and oe < e - 0.1 * atr) : (oe < close and oe > e + 0.1 * atr)
                k += 1
    lv.nIn := k
```

**Multiplier** (step 17, before `evaluate`; `track` resets `mult` at 657, so this composes like the killzone and VP multipliers).
- The prior ratios are the conservative midpoint of the 1m and 1H results, as reach relative to `nIn = 0`.
- `crK`, `crE` are `var array<float>` (size 4) declared in STATE. They hold hits and the Σ`pBase` of graded trials per bucket.
- `f_book` fills them from a new `Trial` field `nIn0`, set in `f_openTrial`.
- `f_crowdMult` goes in STATE HELPERS, after the state arrays.

```pine
f_crowdPrior(int k) =>
    k <= 0 ? 1.00 : k == 1 ? 0.97 : k == 2 ? 0.92 : 0.82

// learned reach ratio of bucket k vs bucket 0 (observed/expected), shrunk toward the prior with n0 pseudo-trials
f_crowdMult(int k) =>
    float n0 = 20.0
    float rk = (crK.get(k) + n0 * f_crowdPrior(k)) / (crE.get(k) + n0)
    float r0 = (crK.get(0) + n0) / (crE.get(0) + n0)
    f_clamp(rk / math.max(r0, 1e-9), 0.6, 1.1)

// step 17, inside the scoring loop, before lv.evaluate(...)
lv.mult *= math.pow(f_crowdMult(math.min(lv.nIn, 3)), crowdW)
```
- If ICT-1's candidate probes exist, register `nIn` as a probe feature instead. Probes learn about 30× faster than the active-DOL ledger.

**Stack.** In `evaluate` (682-685), when `stackMode == "Neutral"`:
- drop `0.45 * this.stack` from `x`;
- skip `this.mult *= 0.70`.

Keep the `STK` tag for display. ICT purists can select "Outermost (ICT)".

**PoT.** Apply the same ratio to the displayed PoT, in logit space, for the active target: `activePoT := f_sigm(f_logit(pot) + math.log(f_crowdMult(...)))`, capped at 0.95.

**Ledger measurement.**
- Per-`nIn` bucket hit rate vs `pBase` (new Full-view row "CROWD 0/1/2/3+ edge").
- A/B of `stackMode` on overall EDGE and BARS→HIT.

**Value.**
- Fewer far "outermost" targets that sit behind a staircase of unswept pools. These are the targets that look wrong and jump around when price stalls at the first pool.
- More targets that price actually takes next.

**Evidence.** Moderate-strong: original, 6 symbols × 2 timeframes, monotone, cluster-robust. Consistent with S1, S2 and S4. Confounded with trend; the ledger isolates the residual.

**Risk.**
- It changes a visible ICT convention (the outer pool as the draw). That is mitigated by the option and by the ledger A/B.
- Double counting with the counter-draw penalty when the crowding comes from a counter-trend staircase. Learning the ratio rather than fixing it handles that.

**Effort.** S.

### ACAD-2 (P1, M) · Two-stage ledger: ARRIVE vs THROUGH-given-ARRIVE, with a memory table per chart

**Why.**
- S/R research measures *what happens at the level* (Osler, Garzarelli, Chung & Bellotti). The engine's ledger only records "hit within H".
- Splitting the outcome tells the trader two different things:
  - whether the engine picks places price actually goes (arrival skill);
  - whether those places get taken once reached (barrier strength).
- It also learns this chart's S/R memory table, which is needed because the 1H evidence is asset-specific (§2.2).

**Inputs** (G_ACC): `float arrGam = input.float(0.35, "Arrival Stripe (ATR)", minval = 0.05, maxval = 1.0, step = 0.05, group = G_ACC)`. The default 0.35 ATR equals the 0.5 × mean|ΔC| stripe of §2.2.

**`Trial` (375-395).** Add:
- `bool arr = false`, `float gam = 0.0`, `float pArrB = na`, `float pThrB = na`;
- `int mb = 0`: a memory bucket, 0-8. It is `(nB ≥ 3 ? 2 : nB ≥ 2 ? 1 : 0) * 3 + (Δt < τ/4 ? 0 : Δt < τ ? 1 : 2)`, using ACAD-3's state. Without ACAD-3, use `tests` and `lastTest`.

**`f_openTrial` (1426-1432):**
```pine
float g  = arrGam * atr
float dA = math.max(0.0, d - g)
pArrB := f_potBase(dA, lv.side)                                  // random level: P(reach the stripe)
pThrB := f_clamp(f_potBase(d, lv.side) / math.max(pArrB, 1e-6), 0.01, 0.99)   // random level: P(through | arrive) = S(d)/S(d-g)
```
- It reuses the empirical excursion surface. There is no new state for the baseline.
- `S(d)/S(d−g)` is the exact random-level analogue of Osler's arbitrary-level control.

**`f_step` (1434-1459):** `t.arr := t.arr or (t.side == 1 ? high >= t.edge - t.gam : low <= t.edge + t.gam)`, set before `hit`.

**`f_book` (1461-1499):** accumulate:
- `arN`, `arK` (arrived), `arE` (Σ pArrB);
- for arrived trials: `thN[mb]`, `thK[mb]` (hit), `thE[mb]` (Σ pThrB), with 9 buckets.

**Display (Terminal Full view, after BARS→HIT).**
- `ARRIVE 71% (rand 66%)`
- `THRU|ARR 58% (rand 74%)`
- The memory cell for the active target: `MEM fresh B3: −11 pp`

**Ledger-measurable by design.** This proposal *is* the measurement. ACAD-3 consumes its table.

**Value.**
- Honest decomposition of misses, for example "price got there but it held", which is a bounce, not a wrong target.
- The per-chart S/R memory replaces hard-coded priors once n ≥ 30 per cell.

**Evidence.** Strong for the framework (S1-S3). The method's baseline is exact.

**Risk.** Cells fill slowly because only the active DOL is graded (about 1 trial per H bars). With ICT-1 probes, fill time drops by 10-30×. Show cells only at n ≥ 20.

**Effort.** M.

### ACAD-3 (P2, S/M) · S/R memory state per pool and a last-mile barrier PoT

**Why.**
- At the level the live PoT tends to 95% (`f_pot` with dist → 0, 434-445), whatever the level's recent behaviour.
- On ≤ 5m charts the probability that a fresh, multi-bounce pool is taken on this approach is about 7-11 pp lower than for a memory-free level. A pool approached after a long absence is about 3-8 pp *more* likely to break (§2.2, 6/6 symbols).
- This also replaces the wrong-signed test bonus. It amends SMC-3 with quantified, recency-signed priors.

**Inputs** (G_LIQ, after 99):
```pine
float memTau = input.float(400.0, "S/R Memory Decay (bars)", minval = 20.0, step = 20.0, group = G_LIQ,
  tooltip = "Bounce memory fades with this time constant (in chart bars). Fresh bounces make a pool a barrier; pools re-approached after about 0.65x this long break more easily than chance.")
float memW   = input.float(-1.0, "S/R Memory Prior Weight (-1 = auto)", minval = -1.0, maxval = 1.0, step = 0.1, group = G_LIQ,
  tooltip = "Auto: 1 on charts of 5m or less, 0 above (evidence: strong at 1m, asset-specific at 1H). The ledger's own table (two-stage ledger) takes over as it fills.")
```

**`Level` fields:** `int nB = 1` (the formation counts as bounce #1, as in §2.2), `int lastB` (bar of the last interaction; set to `bornBar` at creation), `bool inZ`, `bool form`.
- At creation (steps 9 and 11) set `inZ := distance(close) <= arrGam * atr` and `form := inZ`. A pool created while price is still in its stripe is in its formation episode.

**`track` (650-658):** replace the test block for liquidity pools:
```pine
float g      = arrGam * atrV
bool  inside = this.side == 1 ? hi >= this.price - g : lo <= this.price + g
if this.isLiquidity()
    if not this.inZ and inside
        this.inZ := true                      // an approach starts
    else if this.inZ and not inside
        if not this.form
            this.nB += 1                      // left the stripe on the near side: a bounce
        this.form  := false
        this.inZ   := false
        this.lastB := bar_index
        this.tests := this.nB - 1             // keep the T-tag semantics: re-tests that held
```
- Trade-through still removes the pool in step 3, so a penetration never counts as a bounce.

**Helper (PURE HELPERS):**
```pine
f_memE(int b, float dt) =>      // excess bounce probability on arrival, as a probability
    float e = math.exp(-dt / memTau)
    ((7.0 + 0.75 * math.min(b - 1, 4)) * e - 8.0 * (1.0 - e)) / 100.0
```

**Last-mile PoT** (LIVE READOUTS, 2064-2068 only).
- `f_potModel` and `f_potBase` are declared at 1303-1322, after `evaluate` (660). A call from `evaluate` would be a forward reference, which Pine does not allow, so the score's `reach` term stays unchanged.

```pine
if not na(activeLv) and nz(atr) > 0 and activeLv.isLiquidity() and not sweptNow
    float d     = math.max(0.0, activeLv.distance(close))
    float g     = arrGam * atr
    float pMod  = f_potModel(d, activeLv.side, potMu * activeLv.side)
    float pArr  = f_potModel(math.max(0.0, d - g), activeLv.side, potMu * activeLv.side)
    float pThrR = f_clamp(f_potBase(d, activeLv.side) / math.max(f_potBase(math.max(0.0, d - g), activeLv.side), 1e-6), 0.05, 0.99)
    float w     = memW >= 0 ? memW : (timeframe.in_seconds() <= 300 ? 1.0 : 0.0)
    float eMem  = w * f_memE(activeLv.nB, bar_index - activeLv.lastB)   // blended with the ACAD-2 cell when n >= 20
    float pThr  = f_clamp(pThrR - eMem, 0.02, 0.99)
    activePoT  := math.min(0.95, f_sigm(f_logit(pMod) + pArr * (f_logit(pThr) - f_logit(pThrR))))
```
- When `eMem = 0` the shift is 0 and the readout equals today's `f_potModel`.
- The shift is weighted by `pArr`: the barrier only matters if price gets to the stripe within H.
- `f_sigm` and `f_logit` (484-490) clamp their inputs.

**Score.**
- Remove `0.35 * min(tests, 6)` from density `x` (682).
- Add nothing in its place: §2.3 shows reach within H is barely affected by fresh memory. The memory acts on PoT, where the arrival is conditional.

**UX.**
- Tooltip adds `B3 · last 12 bars · barrier −9 pp` or `STALE · breaks +5 pp`.
- Optional alert `"Approaching fresh barrier"`, fired on a confirmed bar when `pArr > 0.8` and `eMem > 0.06`. Use `alert.freq_once_per_bar_close`.

**Ledger measurement.**
- With ACAD-2: memory-bucket THRU|ARR vs the random baseline.
- With SMC-1 / TIME-2: Brier score of displayed PoT for trials opened within 1 ATR, with vs without `eMem` (an A/B input).

**Value.** On scalping charts the PoT stops shouting 90%+ at a level that has just held three times. It says when an old level is more likely to break.

**Evidence.** Strong at ≤ 5m (S2, S3 and §2.2: 6/6 symbols, z up to 19, robust to the stripe definition). The default weight is 0 above 5m, because the hourly evidence is mixed.

**Risk.**
- Bars vs minutes: τ was calibrated on 1-minute bars, and timeframes between 5m and 1H are untested. That is why the prior is off above 5m and the ledger learns.
- The cost is small: O(1) per pool per bar.

**Effort.** S/M.

### ACAD-4 (P3, S) · Stale-pool raids: continuation weight by pool age, decay in clock time

**Why.**
- The engine maps a raid's close to continuation or reversal, weights it by tier, and decays it with `liqHL` = 24 bars (159, 1535, 1580-1582). That is 24 minutes on 1m and 4 days on 4H.
- Osler's cascades are a 15-minute to 2-hour phenomenon.
- §2.5 finds post-break continuation concentrated in pools that were **4-12 h old**: +5.1 pp hold at 120 minutes (z 3.3), median +1.1 ATR. Young pools are near zero.
- This amends ICTS-2 and BIAS-4. Those fix the sign mapping; this fixes the weighting and the clock.

**Algorithm.**
- `liqHLm = input.int(90, "Liquidity-Event Half-Life (minutes)", minval = 5)`.
- Each confirmed bar: `liqEvt *= math.pow(0.5, chartS / 60.0 / liqHLm)` (`chartS` is defined at 307).
- Raid weight: `evt * lv.tier() * f_clamp(0.5 + 0.5 * (bar_index - nz(lv.lastB, lv.bornBar)) * chartS / 60.0 / 240.0, 0.5, 1.5)`. Stale pools (more than 4 h since the last interaction) weigh up to 1.5×.

**Ledger measurement.** The ICTS-1 draw-skill gate, or the BIAS-1 side ledger: A/B of the side hit rate.

**Evidence.** Weak-moderate (§2.5 single window; S6 strong in FX at round numbers).

**Risk.** On 4H and above, a 90-minute half-life makes the event term almost vanish within a bar. That is intended (S6: no effect at 1-2 days), but D then leans on structure.

**Effort.** S.

### ACAD-5 (P3, S) · 52-week and all-time extremes as anchor pools

**Why.**
- The best-documented anchors in finance (S11-S15) are absent from the engine.
- They are barriers on approach (implied volatility falls) and continuation triggers when broken (volume burst, momentum).
- For Swing mode (W / D / 4H) they are natural HTF objectives. ICTPD-5 and TIME-8 cover 20/40/60-day extremes but not these.

**Series** (one extra request; the engine stays far below 40):
```pine
[h52, l52, ath, atl] = request.security(syminfo.tickerid, f_tfSafe("D"),
  [ta.highest(high, 252)[1], ta.lowest(low, 252)[1], ta.max(high)[1], ta.min(low)[1]], lookahead = barmerge.lookahead_on)
```
- `ta.max(source)`: "Returns the all-time high value of `source` from the beginning of the chart up to the current bar" (reference/ta.md:973-978).
- Values are `[1]`-offset with `lookahead_on`, so they do not repaint.

**Registry** (step 10, 1797-1822).
- New `src` codes: 8 = 52-week, 9 = ATH/ATL. `f_tierW`: 8 → 0.95, 9 → 1.0. Names "52W H" / "52W L" / "ATH" / "ATL".
- Push with `f_pushExt` when the value changes: `f_changed(h52)` (865) and so on.
- Anchor with `f_anchorScan(px, isHigh, anchorMax)` (1141). If the print is older than `anchorMax`, fall back to `bar_index - anchorMax`; the daily request carries no print time.
- Use 365 sessions instead of 252 for 24/7 symbols (`syminfo.type == "crypto"`).
- The registry keeps the pools until they are raided. The HTF objective (2159) picks them up automatically.

**Approach state (optional, ledger-gated).** Within 1 ATR of an anchor, scale `potSig` by 0.9: the Driessen volatility compression. After a close beyond the anchor, add `+0.2` to D on the break side, decaying with `liqHL`.

**Ledger measurement.** Family EDGE for `src ≥ 8`. Only meaningful on D / 4H charts.

**Evidence.** Strong that these anchors matter at daily to monthly horizons in stocks. Unknown for intraday DOL reach.

**Risk.** Low. On intraday charts they are usually outside `maxATR` and stay dormant in the registry.

**Effort.** S.

### Considered and not proposed
- **Round-number pools or bonuses.** S5-S10 and S16 support barriers, pass-through and "stop short" but no magnet. ICT-3 and OF-4 already specify the evidence-calibrated version.
- **"Each touch weakens the level" (more tests → more likely to break).** No quantitative support. §2.3 finds ≥ 3 tests *lower* reach. §2.2 finds the opposite of weakening while the level is fresh.
- **A previous-day-high "magnet".** It is geometry (S25, S27). The engine's PoT already handles it; BIAS-3 covers the readout.
- **Time-of-day priors for where highs and lows form.** Arcsine plus volatility clock (S26). This is TIME-1's domain.
- **Option-strike pinning.** It is a real magnet (S22) but needs open-interest data that Pine does not have, and applies only on expiration days.
- **Trading-range-break signals as a DOL input.** The edge decayed after publication (S18), and modern intraday ORB fails costs (S20).

---

## 5. Sources

- Osler, C. (2000). Support for Resistance: Technical Analysis and Intraday Exchange Rates. FRBNY Economic Policy Review 6(2): 53-68. https://www.newyorkfed.org/medialibrary/media/research/epr/00v06n2/0007osle.html (numbers read from this page in this study).
- Osler, C. (2003). Currency Orders and Exchange-Rate Dynamics: Explaining the Success of Technical Analysis. J. Finance 58(5). FRBNY SR125: https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr125.pdf
- Osler, C. (2005). Stop-loss orders and price cascades in currency markets. J. Int. Money & Finance 24(2). FRBNY SR150: https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr150.pdf
- Garzarelli, F., Cristelli, M., Pompa, G., Zaccaria, A., Pietronero, L. (2014). Memory effects in stock price dynamics: evidences of technical trading. Sci. Rep. 4:4487. https://arxiv.org/abs/1110.5197 · https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3967202/
- Chung, K., Bellotti, A. (2021). Evidence and Behaviour of Support and Resistance Levels in Financial Time Series. https://arxiv.org/abs/2101.07410
- Kavajecz, K., Odders-White, E. (2004). Technical Analysis and Liquidity Provision. RFS 17(4): 1043-1071. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=315660
- Jung, J., Lee, K. (2026). Do Round Numbers Hold Prices? Occupation Densities and Depth-Conditioned Hazards in the Limit Order Book. https://arxiv.org/abs/2610.34787
- Lallouache, M., Abergel, F. (2014). Tick Size Reduction and Price Clustering in a FX Order Book. https://arxiv.org/abs/1307.5440
- De Grauwe, P., Decupere, D. (1992). Psychological Barriers in the Foreign Exchange Market. CEPR DP621. https://ideas.repec.org/p/cpr/ceprdp/621.html
- Donaldson, R. G., Kim, H. Y. (1993). Price Barriers in the Dow Jones Industrial Average. JFQA 28(3): 313-330. https://ideas.repec.org/a/cup/jfinqa/v28y1993i03p313-330_00.html
- Aggarwal, R., Lucey, B. (2007). Psychological barriers in gold prices? Review of Financial Economics 16: 217-230. https://ideas.repec.org/a/eee/revfin/v16y2007i2p217-230.html
- Bhattacharya, U., Holden, C., Jacobsen, S. (2012). Penny Wise, Dollar Foolish: Buy-Sell Imbalances On and Around Round Numbers. Management Science 58(2): 413-431. https://host.kelley.iu.edu/cholden/Bhattacharya%20Holden%20and%20Jacobsen%20(2012).pdf
- George, T., Hwang, C.-Y. (2004). The 52-Week High and Momentum Investing. J. Finance 59(5). https://www.bauer.uh.edu/tgeorge/papers/gh4-paper.pdf
- Li, J., Yu, J. (2012). Investor attention, psychological anchors, and stock return predictability. JFE 104(2): 401-419. https://econpapers.repec.org/RePEc:eee:jfinec:v:104:y:2012:i:2:p:401-419
- Huddart, S., Lang, M., Yetman, M. (2009). Volume and Price Patterns Around a Stock's 52-Week Highs and Lows: Theory and Evidence. Management Science 55(1): 16-31. https://ideas.repec.org/a/inm/ormnsc/v55y2009i1p16-31.html
- Driessen, J., Lin, T.-C., Van Hemert, O. (2013). How the 52-week high and low affect option-implied volatilities and stock return moments. Review of Finance 17(1): 369-401. https://ideas.repec.org/a/oup/revfin/v17y2013i1p369-401.html
- Bhootra, A., Hur, J. (2013). The timing of 52-week high price and momentum. JBF 37(10): 3773-3782. https://ideas.repec.org/a/eee/jbfina/v37y2013i10p3773-3782.html
- Brock, W., Lakonishok, J., LeBaron, B. (1992). Simple Technical Trading Rules and the Stochastic Properties of Stock Returns. J. Finance 47(5): 1731-1764. https://ideas.repec.org/a/bla/jfinan/v47y1992i5p1731-64.html
- Sullivan, R., Timmermann, A., White, H. (1999). Data-Snooping, Technical Trading Rule Performance, and the Bootstrap. J. Finance 54(5).
- Holmberg, U., Lönnbark, C., Lundström, C. (2013). Assessing the profitability of intraday opening range breakout strategies. Finance Research Letters 10(1): 27-33. https://ideas.repec.org/a/eee/finlet/v10y2013i1p27-33.html
- Zapranis, A., Tsinaslanidis, P. (2012). Identifying and evaluating horizontal support and resistance levels: an empirical study on US stock markets. Applied Financial Economics 22(19). https://ideas.repec.org/a/taf/apfiec/v22y2012i19p1571-1585.html (support outperforms resistance at predicting trend interruptions; no excess return over buy-and-hold).
- Safari, S., Schmidhuber, C. (2025). Trends and Reversion in Financial Markets on Time Scales from Minutes to Decades. https://arxiv.org/abs/2501.16772
- Mesfin, M. (2026). Structural Limits of OHLCV-Based Intraday Momentum Signals in MNQ Futures. https://arxiv.org/abs/2605.04004
- Taylor, V. (2026). Evaluating the Predictive Validity of ICT's AMD Model on CME E-Mini NASDAQ-100 Futures. https://arxiv.org/abs/2610.35887
- Ni, S. X., Pearson, N., Poteshman, A. (2005). Stock price clustering on option expiration dates. JFE 78(1): 49-87. https://ideas.repec.org/a/eee/jfinec/v78y2005i1p49-87.html
- Golez, B., Jackwerth, J. (2012). Pinning in the S&P 500 futures. JFE 106(3).
- Cho, D., Russell, J., Tiao, G., Tsay, R. (2003). The magnet effect of price limits: evidence from high-frequency data on Taiwan Stock Exchange. J. Empirical Finance 10.
- Caporin, M., Ranaldo, A., Santucci de Magistris, P. (2013). On the predictability of stock prices: a case for high and low prices. JBF 37(12): 5132-5146. https://econpapers.repec.org/RePEc:eee:jbfina:v:37:y:2013:i:12:p:5132-5146
- Valenti, D., Spagnolo, B., Bonanno, G. (2006). Hitting Time Distributions in Financial Markets. https://arxiv.org/abs/physics/0608201
- Bouchaud, J.-P., Farmer, J. D., Lillo, F. (2008). How markets slowly digest changes in supply and demand. https://arxiv.org/abs/0809.0822 · Benzaquen, M., Bouchaud, J.-P. (2017). Market impact with multi-timescale liquidity. https://arxiv.org/abs/1710.03734
- Andersen, T., Bollerslev, T. (1997, 1998): intraday periodicity (via sibling ict_time).
- Sibling studies: `ict_liq.md`, `ict_pd.md`, `ict_time.md`, `bias_dol.md`, `orderflow_micro.md`, `wyckoff_sd.md`, `smc_impl.md`, `amt_profile.md` (same folder).

---

## Appendix A. Reproduction

Scripts are in `brief/study/academic_tools/`. Data comes from `brief/study/amt_data/cme/<SYM>/<SYM>_{1min,1h}_*.csv`. Run from `academic_tools/` with `python3 -I`:

| Command | Output |
|---|---|
| `srmem.py ../amt_data/cme bar 1.0 3` | `out_srmem_bar_g1.txt` (main §2.2 table, per-symbol decay) |
| `srmem.py ../amt_data/cme close 1.0 3` | `out_srmem_close_g1.txt` |
| `srmem.py ../amt_data/cme bar 0.5 3` | `out_srmem_bar_g05.txt` |
| `srmem.py ../amt_data/cme bar 2.0 3` | `out_srmem_bar_g2.txt` |
| `srmem.py ../amt_data/cme bar 1.0 5 1h` | `out_srmem_bar_g1_1h.txt` |
| `reach.py ../amt_data/cme 30 15` | `out_reach_H30.txt` (§2.3) |
| `barrier.py ../amt_data/cme 30 60 0.5` | `out_barrier.txt` (§2.4, 1m) |
| `barrier.py ../amt_data/cme 30 60 0.5 1h` | `out_barrier_1h.txt` (§2.4, 1H) |
| `cascade.py ../amt_data/cme 2` | `out_cascade.txt` (§2.5) |

Each run takes 3-15 s.

## Appendix A.2. Stripe width vs ATR (median ATR(14))

| Symbol | 1m: mean\|ΔC\| / ATR | 1H: mean\|ΔC\| / ATR |
|---|---|---|
| ES | 0.61 | 0.59 |
| NQ | 0.61 | 0.57 |
| GC | 0.76 | 0.91 |
| CL | 0.74 | 0.84 |

So k = 0.5 ≈ 0.30-0.38 ATR, which is the engine's `testATR` (0.30) and ACAD-2's default stripe of 0.35 ATR.
