# Academic evidence on price levels: combined study (researchers A + B)

**Domain.** Peer-reviewed, arXiv and SSRN evidence on:
- support and resistance (S/R), level memory and decay;
- bounce vs penetration as a function of touches and time since formation;
- round numbers, prior-high/low and N-period breakouts, and 52-week-high anchoring;
- stop-loss cascades, the timing of daily highs and lows, and the probability that a previous extreme is exceeded.

**Aim.** Quantified priors the engine can use to answer "which liquidity is reached next, how likely, and when".

**Line numbers** refer to `brief/baseline_v2.pine`, which is identical to `indicators/dol_engine.pine` (checked with `diff`). Sibling studies in `brief/study/` are cited by proposal ID (ICT-1, ICT-10, SMC-3, WYK-2, ICTS-2, BIAS-4, ICTPD-5, TIME-1, TIME-8 and so on).

**Markers.**
- `[A✓]`: claim by A, re-checked by B against the source or the raw output.
- `[CORRECTED]`: A's claim changed by B.
- `[NEW-B]`: added by B.
- `[this study]`: an original test. A's scripts are in `brief/study/academic_tools/`; B's are in `brief/study/academic_b_tools/` (Appendix A).

**Data.**
- 1-minute CME futures: ES, NQ, RTY, YM, GC, CL; 2026-01-20 to 2026-04-15; 67-84k bars each.
- 1-hour CME bars: 2025-03 to 2026-04, in `brief/study/amt_data/cme/`.
- B also used clean 1H NQ, GC and EURUSD series (11-12k bars, `sim/data/`), as sibling ict_liq did.
- **Data-quality correction [NEW-B]:**
  - `amt_data/cme/GC/GC_1h_*.csv` interleaves two contract months: 692 bar-to-bar gaps over 1.5%, 281 of them jump-and-back. Sibling ict_liq found the same. Every A result that used the 1H file set includes it.
  - B's scan found no such defect in any of the 1-minute files. CL 1H has 9 gaps over 1.5%, consistent with contract rolls.

**Tool note.** Firecrawl web-search credits ran out during B's pass, and direct fetches of newyorkfed.org and upenn.edu were blocked by the session's network allowlist. Osler (2000) and Kavajecz & Odders-White (2004) numbers are therefore as A read them. Garzarelli, Chung & Bellotti, Safari & Schmidhuber, Jung & Lee, Taylor and Mesfin were re-read in full text or abstract via the paper index.

---

## 0. Executive summary (combined, corrected)

1. **Levels as barriers exist in tick and FX data, but at bar resolution the "memory" is small and confined to 1-minute charts.** `[CORRECTED]`
   - **Literature:**
     - Published FX levels interrupted intraday trends 60.8% of the time, against 56.2% for 10,000 sets of arbitrary levels (Osler 2000).
     - Bounce probability rises with prior bounces at 45-90 s sampling (Garzarelli et al. 2014) and at 1 minute (Chung & Bellotti 2021).
   - **A's 1-minute replication** found an excess bounce of +4.9 to +7.5 pp over a null that shuffles bars within each day.
   - **B re-ran it against a stricter null.** It keeps the bar order, and with it the exact volatility path, intraday seasonality and clustering. Each bar is mirrored about its open at random, which destroys direction (hence level memory).
     - 1m: the excess shrinks to **+1.5 to +3.0 pp** (+2.7 pp when the last bounce was under 15 minutes ago, z 10).
     - 5m: it is **≈ 0** (+0.1 pp), with no rise in b_prev.
     - 15m: it is **≈ 0** (−0.6 pp).
   - About two thirds of A's effect was volatility clustering that the day shuffle destroyed.
   - The raw "a level that held more often holds again" pattern rises by about 14 pp from b_prev 1 to 5+ **even in the memoryless null**: survivorship selection, not memory.
   - The published studies' shuffled-return nulls share this weakness. They tested anti-persistence (fBm, AR(1)) but not volatility clustering, so their magnitudes may also be overstated (not re-tested on their data).
2. **Stale levels.** Levels price returns to after a long absence break slightly more often than chance: −2 pp at 1m and −2.5 pp at 5m against the strict null, with the same sign in 6 of 6 symbols at 1m. This is consistent with hour-scale trend persistence (Safari & Schmidhuber 2025) and with Chung & Bellotti, who attribute their below-0.5 decay to 2018 bear trends. `[CORRECTED from −3 to −8 pp]`
3. **The most consistent level effect for "which pool is reached" is staleness of the pool itself.** `[NEW-B]`
   - Chart-swing pools that have survived about 1 day or more (intraday charts) or about 3 days or more (1H) are reached **8-14 pp less often** than a random level at the same distance and trend:
     - 1m: −6.9 pp at 12-24 h, −10.4 at 24-72 h;
     - 5m: −9.9 at 24-72 h, −13.6 beyond 72 h;
     - 1H CME: −9.4 beyond 72 h;
     - 1H NQ/GC/EUR: −4.6 beyond 72 h.
   - Very young pools (under 1 h) are reached about 1 pp less. The engine's maturation ramp points the right way but is about 10× too strong (agrees with sibling WYK B).
   - The engine's decay is in **bars** (600-bar half-life). That is 10 h on 1m and 25 days on 1H, while the effect sits at roughly 1-3 days of trading time on every timeframe.
4. **Path crowding is mostly a staleness proxy and is heterogeneous across markets.** `[CORRECTED]` A's crowding gradient (pools with nIn same-side unswept pools between price and target are reached less often) reproduces on clean 1m data: −1.3 / −1.8 / −3.9 / −6.4 pp.
   - A's 1H numbers (−6 / −10 / −29 pp) were driven by the corrupted GC file.
   - **With the engine's own 15-ATR ejection, the 1m/5m effect almost vanishes:**
     - 1m: −1.0 / −0.8 / −2.4 / −2.8;
     - 5m: −0.5 / +0.7 / +1.1 / −2.8.
   - At 5m without ejection, all of the negative effect sits in pools older than 24 h. Pools younger than 4 h show **positive** crowding (+1.6 / +4.8 / +2.3), consistent with stop cascades through the inner pools.
   - On clean 1H it is moderately negative (CME −2.6 / −3.3 / −12.1; NQ/GC/EUR −1.9 / −5.8 / −6.6). The sibling found it positive in BTC 1H (+2.2 / +4.9 / +8.0).
   - A random level with the same pools in front is barely penalized (1m: −0.2 / 0.0 / −2.3), so it is not "every pool is a barrier".
   - **Verdict:** neither the engine's "outermost is the draw" rule (inner ×0.70, `+0.45·stack`) nor A's hard-coded crowding penalty is justified. Use neutral defaults and learn per chart.
5. **The engine's test bonus is unsupported.** Neither the literature nor the replications support `+0.35·min(tests,6)` (682). Reach does not rise with tests (A: 0 / 1 / 2 / ≥3 tests −2.0 / −1.9 / −2.1 / −7.3 ± 3.6 pp), and the raw hold-rate rise is selection (point 1). `[A✓]`
6. **Stop cascades exist but are small at bar resolution.** `[A✓, grade lowered for the age split]`
   - Osler (2005): +0.27 to +2.35 hundredths of a percent extra move for 15 minutes to 2 hours after crossing FX round numbers, gone at 1-2 days.
   - Crypto: 88% of forced selling in the Oct-2025 cascade landed within 30 minutes of onset (arXiv:2608.03616). `[NEW-B]`
   - A's bar test: +1.1 pp more often still beyond a swing level than beyond a grid level (z ≈ 2). A's "+5.1 pp for 4-12 h-old pools" is one significant bucket of 8, non-monotone (1-4 h: −0.1): weak.
7. **Round numbers.** Barriers in some markets, with acceleration after crossing; **not magnets** (Osler 2003; De Grauwe & Decupere 1992; Aggarwal & Lucey 2007; Bhattacharya et al. 2012; Jung & Lee 2026). Siblings ICT-3 and OF-4 own this. `[A✓]`
8. **52-week and all-time highs.** These are the best-documented anchors (George & Hwang 2004; Li & Yu 2012; Huddart et al. 2009; Driessen et al. 2013; Bhootra & Hur 2013), at daily to monthly horizons in stocks. Their intraday reach value is untested, and the sibling found 20/40/60-day extremes reached at baseline. `[A✓]`
9. **Magnets need a mechanism.**
   - Option pinning is documented (Ni, Pearson & Poteshman 2005; Golez & Jackwerth 2012).
   - The **price-limit magnet is mixed** `[CORRECTED]`: Cho et al. (2003) found it in Taiwan; Wan et al. (2015) found a cooling-off effect, not a magnet, in China A-shares.
   - Generic S/R, round numbers, prior highs and gaps are not magnets. Gap-fill folklore is contradicted on US indices (Plastun et al.) `[NEW-B]`.
10. **Timing and previous extremes are geometry plus the volatility clock** (arcsine law, Andersen & Bollerslev; siblings TIME-1, BIAS-3). `[A✓]`
11. **What to build** (§4, best first):
    - ACAD-1: neutral stack and touch terms;
    - ACAD-2: stale-pool reach ratio in trading time, applied to reach and PoT, learned per chart;
    - ACAD-3: two-stage ARRIVE / THROUGH-given-ARRIVE ledger with feature buckets;
    - ACAD-4: learned (not prior) path-crowding ratio;
    - ACAD-5: clock-time half-life for raid events;
    - ACAD-6: 52-week / ATH anchors on a shared N-day buffer.
    - **Dropped:** A's hard-coded S/R-memory barrier PoT (A-ACAD-3) and the pool-age raid weighting in A-ACAD-4.

---

## 1. Concepts: definitions and parameters

### 1.1 Support/resistance as a barrier: bounce vs penetration `[A✓]`
- **Osler (2000)**, the canonical test with published levels.
  - Levels: daily S/R levels from 6 firms, for DEM, JPY and GBP, 1996-98.
  - **Hit:** the bid (ask) comes within **0.01%** of support (resistance); 0.00% and 0.02% were also tested.
  - **Bounce:** the rate is still on the near side 15 minutes after the hit (30 minutes also tested).
  - **Control:** 10,000 sets of arbitrary levels.
- **Garzarelli, Cristelli, Pompa, Zaccaria & Pietronero (2014)**.
  - Price is sampled every τ = 45, 60, 90 or 180 s.
  - Level: a local max or min. **Stripe** width δ(τ) = the mean absolute increment at scale τ.
  - **Bounce:** price enters the stripe and leaves on the same side. b_prev is the number of previous bounces.
  - Estimator: `E[p] = (n+1)/(N+2)`. Compared with shuffled returns.
  - They also simulated a fractional random walk with the stocks' mean Hurst exponent (0.42-0.48). p(b|b_prev) was "very close to 0.5 although above" and flat, so anti-persistence is "not the main source".
  - `[CORRECTED]` At 180 s, what loses significance (χ² p = 0.077 resistance, 0.318 support) is the **dependence of p on b_prev**, not the bounce excess itself.
- **Chung & Bellotti (2021)**.
  - Rolling window of i = 30-1,440 minutes.
  - Support = window minimum with zone `[min, min+γ]`; resistance = window maximum with zone `[max−γ, max]`. γ = mean |Δx|.
  - Bounces = half the zone-boundary crossings.
  - `[NEW-B]` Their AR(1) section shows that **stationary AR(1) series (ρ = 0.95, 0.9) raise p(b|b_prev) above the shuffled baseline**. Mean reversion alone mimics memory. The authors argue real series are not fully explained by AR(1).
- **Engine equivalent.**
  - A pool is "hit" only on a strict trade-through (`touched`, 623-625; BSL zone `[ph, ph+wPx]`, touched when `high > ph`, 1762). A bounce at the level is a miss.
  - The test counter (`track`, 650-658) is a crude bounce counter: within `testATR` = 0.30 ATR, `gap > 0`, at least 3 bars apart.

### 1.2 Level memory and decay `[A✓ for the literature; CORRECTED for magnitudes]`
- **Macro decay** (Chung & Bellotti): p(b|b_prev) falls as the discovery window lengthens.
  - EURUSD: a 1-bounce level reaches 0.5 at about a 350-minute window; a 4-bounce level at about 900 minutes.
  - BRENT: a 1-bounce level drops below 0.5 beyond about 300 minutes.
  - The authors attribute the sub-0.5 values to the 2018 bear trends in EURUSD and BRENT. `[NEW-B]`
- **Micro decay** (Chung & Bellotti, 600-minute window): `logit p = a + b·X`, X = minutes since the last bounce.
  - EURUSD b_prev = 4: a = 0.402***, b = −0.00179*. That implies p = 0.5 at about 225 minutes.
  - EURUSD b_prev = 5: a = 0.403**, b = −0.00273*.
  - Most other b coefficients are not significant. BRENT signs are inconsistent.
- **Duration of published levels** (Osler): at least 5 business days.
- **Recurrence** (Garzarelli): the return time to the stripe is power-law distributed and identical in real and shuffled series. Memory shows in what happens at the level, not in how often price returns.
- **Null-model hierarchy `[NEW-B]`.** What counts as "memory" depends on the null:
  1. shuffled returns (Garzarelli, Chung): destroys direction **and** volatility clustering and intraday seasonality;
  2. within-day bar shuffle (A): keeps each day's volatility level and net move;
  3. **bar mirroring in place (B): keeps the exact bar-range sequence**, destroys direction.
  - Bounce vs penetration with a fixed stripe depends non-linearly on bar size relative to the stripe, so nulls 1 and 2 overstate the excess. Only what survives null 3 is directional dependence: level memory plus short-horizon reversal plus trend.

### 1.3 Depth: why levels hold (mechanism) `[A✓, numbers not re-opened]`
- **Kavajecz & Odders-White (2004, RFS)**: support is "the lowest bid reached at least twice" (equal lows).
  - S/R coincides with peaks in book depth: 84% of level-depth series cointegrated at 5%; significant for 49-73% of stocks.
  - No new limit-order clustering at the levels afterwards. Technical analysis **locates** existing depth.
- **Jung & Lee (2026, arXiv:2610.34787)**, 5 Nasdaq stocks, 2025: round levels attract more resting liquidity but do not show longer depth-adjusted durations. Intel and SoFi departures are biased away from round levels. (Verified to exist.)

### 1.4 Stop-loss clustering and cascades `[A✓]`
- **Osler (2003, J. Finance)**, about 9,700 RBS orders:
  - take-profits cluster at round numbers (9.3% exactly at 00);
  - stop-buys sit just above (14.4% in 01-10 vs 7.4% in 90-99) and stop-sells just below;
  - reversals at rounds are 4.6 pp more frequent.
- **Osler (2005, JIMF)**: the extra move after crossing a round number vs an arbitrary number is +0.27 to +2.35 hundredths of a percent from 15 minutes to 2 hours. It is not significant at 1-2 days, with negative signs.
- **Crypto liquidation cascades `[NEW-B]`** (Garcia Seuma 2026, arXiv:2608.03616), 7 BTC cascades 2022-25:
  - in the October-2025 event, 88% of post-onset forced selling landed within 30 minutes, and 63% was absorbed off-book by the venue backstop;
  - the measured branching ratio was deeply subcritical (λ ≈ 0.1-0.2).
  - So cascades are short and shock-driven: again a minutes-to-hours window.

### 1.5 Round numbers ("psychological barriers") `[A✓]`
- **Barrier tests:** frequencies near M-digits and conditional mean and variance shifts (Donaldson & Kim 1993; De Grauwe & Decupere 1992).
- **Results:**
  - USD/JPY barriers yes, USD/DEM weak; acceleration after crossing.
  - Gold yes (Aggarwal & Lucey 2007); silver no.
  - NYSE buy-sell imbalance ordered by roundness (Bhattacharya, Holden & Jacobsen 2012).
  - EBS algorithms post one tick ahead of clusters (Lallouache & Abergel 2014).
- **Siblings' bar tests (OF-4):** not magnets; sweep wicks stop short of a round number just beyond a pool (−4.2 pp).

### 1.6 Prior-high/low (trading-range) breakouts `[A✓]`
- **Trading-range break** (Brock, Lakonishok & LeBaron 1992): buy when price exceeds the max of the previous n = 50/150/200 days (0% or 1% band). DJIA 1897-1986 significant.
- **Data snooping:** no out-of-sample advantage after 1986 (Sullivan, Timmermann & White 1999).
- **Intraday opening-range breakout:**
  - crude-oil futures profitable mainly in the last decade (Holmberg et al. 2013);
  - MNQ 2021-25, 14 signal families, none passes 5 criteria; ORB long T = 0.88, year-unstable (Mesfin 2026, arXiv:2605.04004, verified).
- **ICT AMD on NQ** (Taylor 2026, arXiv:2610.35887, verified): N = 484 signal days on 15-minute data, 2022-26. No directional information beyond the daily trend regime: right 62-71% with the trend and 25-30% against it, Benjamini-Hochberg-corrected.
- **Zapranis & Tsinaslanidis (2012, AFE 22(19))** `[A✓, detail NEW-B]`: rule-based horizontal S/R from historical local extremes on daily NYSE/NASDAQ closes over about two decades. Support levels predict trend interruptions better than resistance, but no excess return over buy-and-hold.
- **Lo, Mamaysky & Wang (2000, J. Finance 55(4))** `[NEW-B]`: kernel-smoothed extrema and automated detection of rectangles and double tops/bottoms. Several patterns change the conditional return distribution ("incremental information"), but are not stand-alone profitable.
  - The rectangle rule (5 extrema, tops and bottoms each within 0.75% of their mean) is from B's recollection of the paper; it could not be re-opened here.

### 1.7 52-week high/low and anchoring `[A✓]`
- **George & Hwang (2004):** nearness = P / 52-week high. Winner-minus-loser 0.45%/month (t = 2.00) to 1.23%/month (t = 7.06).
- **Li & Yu (2012):** the Dow's nearness to its 52-week high predicts higher returns; nearness to its historical high predicts lower returns (G7-robust).
- **Huddart, Lang & Yetman (2009):** volume spikes when price crosses either extreme, then stays elevated for weeks.
- **Driessen, Lin & Van Hemert (2013):** implied volatility and beta fall on the approach; implied volatility rises by more than 1 vol point after a breakthrough.
- **Bhootra & Hur (2013):** recency of the 52-week high is worth about 0.70%/month.
- **For DOL:** barrier on approach, continuation once broken. Daily to monthly horizons, mostly stocks.

### 1.8 Conditional magnets `[CORRECTED grade]`
- **Option pinning on expiration days** (Ni, Pearson & Poteshman 2005; Golez & Jackwerth 2012): strong but conditional, and it needs open-interest data.
- **Price-limit magnet:**
  - Cho, Russell, Tiao & Tsay (2003), Taiwan: acceleration toward the limit;
  - **Wan et al. (2015, PLoS ONE 10(4))** `[NEW-B]`, all China A-shares 2000-11: a **cooling-off** effect "(object to the magnet effect)", with next-day continuation after limit hits.
  - So: **mixed**.

### 1.9 Timing of daily highs and lows `[A✓]`
- **Arcsine law:** the density of the time of the max is `1/(π√(t(T−t)))`.
- In business time (U-shaped volatility; Andersen & Bollerslev 1997/98) the open gets even more mass.
- **ES 1998-2004:** the 09:30 15-minute segment holds 17.2% of highs of day vs a uniform 3.7%, reproduced by an arcsine-plus-clock random walk (sibling ict_time).
- This is the volatility clock (TIME-1), not a level property.

### 1.10 Probability the previous day's high or low is exceeded `[A✓]`
- **Driftless geometry:** P(H1 before L1) = (C − L1)/(H1 − L1).
- **Base rates** (sibling bias_dol): next-day PDH taken S&P 51.3% / NASDAQ 55.4%; PDL 44.6% / 46.5%; either 87-91%.
- Daily H/L are cointegrated and the range has long memory (Caporin, Ranaldo & Santucci de Magistris 2013).
- **Gaps / prior close `[NEW-B]`:** Plastun, Sibande, Gupta & Wohar (US indices 1928-2018) report gap-day continuation and contradict the "gaps get filled" myth. Caporale & Plastun (2017) cover stocks, FX and commodities.
  - Numbers not re-read: graded weak, used only as "no magnet".

### 1.11 Trend vs reversion timescales `[A✓, wording CORRECTED]`
- **Safari & Schmidhuber (2025, arXiv:2501.16772)**: 14 years of futures tick data, 30 years of daily data, 330 years of monthly data.
  - Tick-size reversion at the shortest horizons.
  - After removing it, weak trends **revert up to about 15-30 minutes**.
  - From about 30 minutes to a few hours, weak trends **persist** and overcome tick reversion "at scales of a few hours".
  - The trending regime spans "a few hours to a few years". Strong trends revert.
- **Reading:** minute-scale bounces at levels and multi-hour continuation are the same market at two scales. Stale-level penetration and stale-pool under-reach (§2.3) are consistent with hour-to-day trend persistence.

### 1.12 Bounce vs breakout as a function of touches and time (synthesis) `[CORRECTED]`

| Condition | Next approach: bounce vs penetration (excess vs strict null) | Source |
|---|---|---|
| Raw hold rate rises with prior holds | Yes, by about 15 pp from 1 to 5+ holds, but **about 14 pp of it appears in a memoryless null** (selection) | [this study B]; vendor gold 1H data: 56 → 62.5 → 66 → 70% (weak) |
| Fresh level (< 15 min), 1m | +2.7 pp (z 10); 6/6 symbols positive | [B] |
| Fresh level, 5m / 15m | ≈ 0 | [B] |
| Stale level (> 4-12 h), 1m / 5m | −2 / −2.5 pp (z ≈ −2); 6/6 symbols negative at 1m | [B]; Chung & Bellotti (BRENT) |
| Hourly bars | No universal sign. A's "GC 1H +17.7 pp" came from the corrupted file | [B correction] |
| "Each touch weakens the level" | No support | — |

### 1.13 Path crowding `[CORRECTED]`
- **Definition:** for a pool target T on side s at distance d, `nIn` = live, unswept same-side pools strictly between price and T's near edge (0.1-ATR margin).
- **Observed:** reach within H falls with nIn on 1m and on clean 1H CME/FX data, when pools are kept alive indefinitely.
- **The effect is confounded with pool age.** Old surviving pools sit behind staircases. With the engine's 15-ATR ejection, or within pools younger than 4 h, the 1m/5m gradient is ≈ 0 or positive.
- **Mechanisms with opposite signs:**
  - barrier depth (Kavajecz) and survivorship push it negative;
  - stop cascades through inner pools (Osler 2005) push it positive (BTC 1H, young 5m pools).
- **Not a path-barrier effect for arbitrary levels:** a random level with the same nIn in front is barely penalized below 1H.

### 1.14 Pool staleness (survivorship) `[NEW-B]`
- **Definition:** age of a chart-swing pool = trading time since its pivot bar. A stale pool is one that has survived for about a day or more (intraday) or about 3 days or more (1H) without being taken.
- **Observation:** stale pools are reached 5-14 pp less often than a random level at the same distance, after conditioning on the recent trend (§2.3).
- **Interpretation:** an old, untaken extreme lies in the direction price has trended away from. Trend persists at hour-to-day scales (§1.11), and the 4-hour trend control does not absorb multi-day trends.

---

## 2. Evidence (numbers and sources)

### 2.1 Literature table

| # | Claim | Source and sample | Numbers | Grade |
|---|---|---|---|---|
| S1 | Published S/R levels interrupt intraday trends more often than arbitrary levels | Osler 2000, FRBNY EPR 6(2); 6 firms, DEM/JPY/GBP 1996-98 | Bounce 15 min after a hit: **60.8%** vs arbitrary **56.2%**. DEM arbitrary 54.9 vs firms 56.6-62.0; JPY 57.3 vs 60.7-66.5; GBP 56.3 vs 58.8-63.0. 1,039-8,111 hits per firm-currency. Lasts **≥ 5 business days**. Strength ratings had **no** value. 95.5% of levels end in 0 or 5 [A read; B could not re-open] | strong |
| S2 | Bounce probability rises with prior bounces (HF) | Garzarelli et al. 2014, Sci. Rep. 4:4487; 9 LSE stocks, 2002 | p(b\|b_prev) > 0.5 and rising at τ = 45/60/90 s (χ² p < 0.0001); at 180 s the rise is not significant (0.077 / 0.318). Shuffled ≈ 0.5 and flat. An fBm with H ≈ 0.45 gives ≈ 0.5 and flat [A✓ B] | strong (HF) |
| S3 | Same at 1 minute, with macro and micro decay | Chung & Bellotti 2021, arXiv:2101.07410; EURUSD, LLOY, BRENT 1-minute 2018 | Permutation Λ > 0.95 for most b_prev ≤ 6. EURUSD 1-bounce reaches 0.5 at a ~350-min window, 4-bounce at ~900. BRENT below 0.5 beyond ~300 min (bear-trend attribution). Micro decay b = −0.0018/min (b_prev 4). AR(1) ρ < 1 raises p [A✓ B] | moderate |
| S4 | S/R = book depth | Kavajecz & Odders-White 2004, RFS 17(4) | 84% cointegrated at 5%; significant for 49-73% of stocks | strong (mechanism) |
| S5 | Stops beyond, take-profits at round numbers | Osler 2003, J. Finance 58(5) | TP 9.3% at 00; stop-buys 14.4% in 01-10 vs 7.4% in 90-99 | strong |
| S6 | Cascades after crossing stop clusters | Osler 2005, JIMF 24(2) | +0.27 to +2.35 hundredths of a percent at 15 min-2 h; gone at 1-2 days | strong (FX) |
| S7 | FX psychological barriers | De Grauwe & Decupere 1992, CEPR DP621 | USD/JPY significant; USD/DEM weak; acceleration after crossing | moderate |
| S8 | Gold barriers at 00 | Aggarwal & Lucey 2007, RFE 16 | Conditional mean and variance effects | moderate |
| S9 | Round-number trading imbalance | Bhattacharya, Holden & Jacobsen 2012, Mgmt Sci 58(2) | Buy 1¢ below, sell above; ordered by roundness | strong |
| S10 | Round levels: more depth, not longer holding | Jung & Lee 2026, arXiv:2610.34787 [verified] | No longer depth-adjusted durations | moderate |
| S11 | 52-week high predicts continuation | George & Hwang 2004, J. Finance 59(5) | WML 0.45-1.23%/month (t 2.00-7.06) | strong |
| S12 | 52-week high (+) vs historical high (−) | Li & Yu 2012, JFE 104(2) | Signs as stated, G7 | strong |
| S13 | Crossing a 52-week extreme → volume burst | Huddart, Lang & Yetman 2009, Mgmt Sci 55(1) | Volume up sharply; elevated for weeks | strong |
| S14 | Approach compresses volatility, breakthrough expands it | Driessen, Lin & Van Hemert 2013, RoF 17(1) | IV falls on approach; ≥ +1 vol point after a break | strong |
| S15 | Recency of the 52-week high | Bhootra & Hur 2013, JBF 37(10) | About 0.70%/month | moderate-strong |
| S16 | Round numbers at bar resolution | sibling orderflow_micro T2/T2d | Not magnets; sweep wicks stop short (−4.2 pp) | moderate |
| S17 | Trading-range-break rules | Brock, Lakonishok & LeBaron 1992 | Significant 1897-1986 | strong (historical) |
| S18 | ... snooped / decayed | Sullivan, Timmermann & White 1999 | No out-of-sample advantage 1987-96 | strong |
| S19 | Intraday ORB | Holmberg, Lönnbark & Lundström 2013, FRL 10(1) | Profitable mainly in the last decade (crude) | moderate |
| S20 | ORB / momentum after costs | Mesfin 2026, arXiv:2605.04004 [verified]; 947 days of MNQ 5m | 0 of 14 families pass; ORB long T = 0.88 | moderate |
| S21 | Trend vs reversion timescales | Safari & Schmidhuber 2025, arXiv:2501.16772 [verified] | Revert ≤ ~30 min after tick effects; weak trends persist from a few hours to a few years | strong |
| S22 | Option pinning | Ni, Pearson & Poteshman 2005; Golez & Jackwerth 2012 | Clustering at strikes on expiry | strong (conditional) |
| S23 | Price-limit magnet | Cho et al. 2003 (Taiwan) **vs Wan et al. 2015 (China: cooling-off)** [NEW-B] | Opposite findings | **mixed** [CORRECTED] |
| S24 | ICT AMD on NQ | Taylor 2026, arXiv:2610.35887 [verified] | No information beyond the trend regime: 62-71% with, 25-30% against | moderate |
| S25 | High/low/range forecastable | Caporin, Ranaldo & Santucci de Magistris 2013, JBF 37(12) | FVECM | strong |
| S26 | Timing of HOD/LOD | sibling ict_time; Andersen & Bollerslev | ES 09:30 HOD 17.2% vs 3.7% uniform; arcsine plus clock | strong (null) |
| S27 | Previous-extreme base rates | sibling bias_dol §2.1 | PDH next day 51-55%; either 87-91% | moderate (descriptive) |
| S28 | Hitting times deviate from GBM | Valenti, Spagnolo & Bonanno 2006 | Heston fits better | moderate |
| S29 | Horizontal S/R on daily stocks | Zapranis & Tsinaslanidis 2012, AFE 22(19) | Support beats resistance at interrupting trends; no excess return | moderate [NEW-B detail] |
| S30 | Patterns carry incremental information | Lo, Mamaysky & Wang 2000, J. Finance 55(4) | Conditional distributions differ for several patterns; not stand-alone profitable | moderate [NEW-B] |
| S31 | Crypto liquidation cascades are short | Garcia Seuma 2026, arXiv:2608.03616 | 88% of forced selling within 30 min; subcritical branching | moderate [NEW-B] |
| S32 | Raw hold rate rises with prior holds (gold 1H, 22 years, 19,302 tests) | vendor blog (MQL5, 2026) | 56 → 62.5 → 66 → 70% for 0/1/3/5 holds; the author notes random points also "react" | weak [NEW-B] |
| S33 | Gaps are not reliably filled | Plastun, Sibande, Gupta & Wohar (US indices 1928-2018); Caporale & Plastun 2017 | Gap-day continuation; "fill" myth contradicted | weak (not re-read) [NEW-B] |

### 2.2 S/R memory on bars: A's replication and B's strict-null correction

**Method (A, `srmem.py`).**
- Levels: pivotLen-5 swing highs and lows, live until the first trade-through.
- Stripe g = k × mean|ΔClose| (k = 1 ≈ 0.6-0.76 ATR; k = 0.5 ≈ the engine's 0.30-ATR `testATR`).
- Bar variant: penetration = `high > P`; bounce = leaving the stripe on the near side first.
- b_prev counts the formation as the first bounce.
- About 80k 1-minute episodes on 6 symbols.

**Null used by each column:**
- **shuf:** whole bars permuted within each Globex day (A's null).
- **flip:** bar order kept, each bar mirrored about its open with probability ½ (B's null; keeps the exact volatility path).

**Excess bounce over the null, pp (bar variant, k = 1; B's `srmem_b.py`, 5 null replicas):**

| TF | Null | Overall | b = 1 | b = 2 | b = 3 | b = 4 | b ≥ 5 | < 15 min | 15-60 | 60-240 | 240-720 | > 720 min |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1m | shuf (A's) | **+6.5** | +5.1 | +6.6 | +7.5 | +8.0 | +7.4 | +8.4 | +6.9 | +4.5 | −1.7 | −7.7 |
| 1m | **flip** | **+1.9** | +1.5 (z 5.7) | +1.6 | +2.0 | +2.7 | +3.0 | **+2.7** (z 10) | +2.1 | +1.0 | **−2.3** (z −2.6) | **−1.7** (z −2.1) |
| 5m | shuf | +2.8 | +3.2 | +0.9 | +3.5 | +1.8 | +0.8 | +3.9 | +4.5 | +6.1 | +0.7 | −8.8 |
| 5m | **flip** | **+0.1** | +1.2 | −2.4 | +0.6 | −2.1 | −2.7 | −0.1 | +0.6 | +2.5 | −1.3 | **−2.5** (z −2.1) |
| 15m | shuf | +0.4 | +0.8 | +0.9 | −0.9 | −9.3 | +2.3 | — | +2.1 | +2.3 | +0.1 | −3.7 |
| 15m | **flip** | **−0.6** | −0.6 | −0.9 | +1.8 | −6.6 | +2.1 | — | 0.0 | +0.6 | −1.5 | −1.4 |

**Per symbol, 1m flip** (< 60 / 60-240 / ≥ 240 min):

| Symbol | < 60 min | 60-240 min | ≥ 240 min |
|---|---|---|---|
| ES | +0.8 | +0.5 | −1.3 |
| NQ | +2.3 | 0.0 | −2.4 |
| RTY | +2.9 | +1.1 | −1.3 |
| YM | +2.7 | +1.8 | −1.9 |
| GC | +4.0 | +3.8 | −2.0 |
| CL | +3.0 | −1.1 | −2.5 |

Fresh is positive in 6 of 6 symbols and stale is negative in 6 of 6.

**Selection in the raw rates.** The flip null's own bounce rate rises from 0.384 (b = 1) to 0.524 (b ≥ 5); the real series rises from 0.399 to 0.555. About 90% of the raw "more holds → more likely to hold" pattern is survivorship.

**Lag-1 autocorrelation of 1m close changes:** ES −0.004, NQ −0.012, RTY −0.026, YM −0.024, GC −0.156 (tick-size bounce), CL +0.031. Anti-persistence is small except in GC.

**A's original numbers (reproduced by B with the shuf null):**
- +4.9 / +6.8 / +6.8 / +7.3 / +7.5 pp for b_prev 1-5+ (z 7-19).
- Decay +7.0 / +5.8 / +3.3 / −1.1 / −8.6 pp (b = 1) by time since the last bounce.
- A's parametric prior `E(b,Δt) = (7 + 0.75·min(b−1,4))·e^(−Δt/400) − 8·(1 − e^(−Δt/400))` is **withdrawn** `[CORRECTED]`. It was fit against the inadequate null and does not transfer to 5m or above.

**Hourly bars.** A's pooled 1H result (+0.4 / +3.8 / +1.3 / +12.2 / +18.9; "GC +17.7") included the corrupted GC 1H file. **Withdrawn.** No hourly prior.

**Reading.**
- At bar resolution the conditional barrier effect is **≤ 3 pp and only on 1m charts**. Engine charts are mostly 5m and up, where it is zero.
- Stale levels break about 2 pp more often than chance at 1m and 5m: small, but consistent in sign.
- The useful information lies in **survivorship and age** (§2.3), not in counted bounces.

### 2.3 Reach in the engine's terms: tests, age, staleness

**A (`reach.py`, 1m; edge = hit within H = 30 minus S(d) from all bars):**
- all pools −2.0 ± 0.3 pp (n 81,209);
- tests 0 / 1 / 2 / ≥ 3: −2.0 / −1.9 / −2.1 / **−7.3 ± 3.6**;
- since the last test (or birth): < 15 min −1.6, 15-60 −0.5, 1-4 h −2.4, 4-12 h −3.3, > 12 h **−7.5 ± 1.1**. `[A✓ against out_reach_H30.txt]`

**B (`crowd_b.py`; chart pivots 1-4 ATR away; edge vs the hit rate of random levels drawn at the same checkpoints, in the same 0.25-ATR distance bin and the same 240/48/24-bar trend tercile; cluster SE by symbol-day). Pool age = time since the pivot:**

| Age | 1m CME (6) | 5m CME (6) | 1H CME clean (5), eject 15 ATR | 1H NQ/GC/EUR clean, eject 15 ATR |
|---|---|---|---|---|
| < 1 h | −1.1 ± 0.3 | −1.4 ± 0.5 | — | — |
| 1-4 h | −1.9 ± 0.6 | +0.8 ± 0.7 | — | — |
| 4-12 h | −3.0 ± 1.1 | +0.4 ± 1.2 | −3.7 ± 0.9 | −2.0 ± 0.8 |
| 12-24 h | −6.9 ± 1.7 | −1.5 ± 2.0 | +1.4 ± 1.1 | +0.2 ± 1.0 |
| 24-72 h | **−10.4 ± 1.7** | **−9.9 ± 1.9** | 0.0 ± 1.4 | −2.1 ± 1.2 |
| > 72 h | **−8.1 ± 2.1** | **−13.6 ± 2.1** | **−9.4 ± 2.3** | **−4.6 ± 2.0** |

- The 1m/5m columns have no ejection. With the engine's 15-ATR ejection almost no 1m pool survives past 4 h, and few 5m pools past 24 h; the engine's external registry still carries old HTF/STF pools.
- Using the unconditional instead of the trend-conditional baseline changes the edges by ≤ 1 pp (1m, 5m) and ≤ 1.2 pp (1H). **The engine's unconditional `f_potBase` baseline is therefore adequate.** `[NEW-B]`
- **As reach ratios vs a random level** (hit / baseline), used as priors in ACAD-2:
  - 1m: 0.98 / 0.96 / 0.94 / 0.85 / 0.78 / 0.83;
  - 5m: 0.97 / 1.02 / 1.01 / 0.97 / 0.79 / 0.70;
  - 1H: 0.93-0.96 at 4-12 h; ≈ 1.0 at 12-72 h; 0.85-0.91 beyond 72 h.
- **Consistency with siblings:** WYK B found young pools (5-10 bars) 0.6-1.9 pp below and intraday pools older than ~300-500 bars 3-8 pp below a random level. WYK-2 keeps the decay and drops the ramp.

### 2.4 Path crowding: A's test and B's controls `[CORRECTED]`

**Edge in pp by nIn = 0 / 1 / 2 / ≥ 3 (pool targets 1-4 ATR, H = 30):**

| Data | Design | nIn 0 | 1 | 2 | ≥ 3 |
|---|---|---|---|---|---|
| 1m CME (A) | no ejection, S(d) all bars | −1.2 | −1.5 | −3.5 | −6.1 |
| 1m CME (B) | no ejection, trend-conditional random-level baseline | −1.3 | −1.8 | −3.9 | −6.4 |
| 1m CME (B) | **15-ATR ejection (engine)** | −1.0 | −0.8 | −2.4 | −2.8 |
| 5m CME (B) | no ejection | −0.8 | −1.3 | −2.1 | −10.6 |
| 5m CME (B) | **15-ATR ejection** | −0.5 | +0.7 | +1.1 | −2.8 ± 3.0 |
| 5m CME (B), pools < 4 h old | no ejection | −0.6 | **+1.6** | **+4.8** | +2.3 |
| 5m CME (B), pools > 24 h old | no ejection | −7.2 | −11.1 | −8.9 | −18.3 |
| 1H CME, 6 files incl. corrupted GC (A) | no ejection | −0.1 | −6.0 | −10.3 | −29.3 **[invalid]** |
| 1H CME clean, 5 (B) | 15-ATR ejection | −1.4 | −2.6 | −3.3 | −12.1 ± 4.1 |
| 1H NQ/GC/EUR clean (B) | 15-ATR ejection | −1.1 | −1.9 | −5.8 | −6.6 ± 3.3 |
| 5m CME (sibling ict_liq, engine-like merge/eject, no opposing FVG) | — | +0.7 | +4.0 | +4.3 | +5.1 |
| 1H BTC (sibling) | — | 0.0 | +2.2 | +4.9 | +8.0 |

**Random levels with the same nIn in front** (B, trend-conditional, no ejection):
- 1m: +0.3 / −0.2 / 0.0 / −2.3
- 5m: +0.2 / −0.2 / +1.5 / −4.1
- 1H clean: +0.6 / −1.1 / +0.4 / −5.0

Intermediate pools are not general barriers on the path, except weakly at ≥ 3.

**Trend terciles (1m, no ejection; against / flat / toward):** the pool gradient persists in all three (−3.5 / −8.4 / −4.2 at nIn ≥ 3). It is not a pure trend effect, but it is strongly age-linked.

**Verdict.**
- Crowding is real but small in the engine's pool universe at ≤ 5m.
- It is moderately negative on CME/FX 1H and positive on BTC 1H and on young 5m pools.
- **Learn it per chart** (ACAD-4); do not hard-code it.
- **The engine's opposite rule (inner ×0.70, `+0.45·stack`, 682-685) is also unsupported.** It is about 10× larger than any measured effect in either direction (agrees with ICT-10).

### 2.5 Cascade after a pool's trade-through (A, `cascade.py`) `[A✓; grading CORRECTED]`
- **Events:** swing pivots (n = 56,750) vs random-phase grid levels (n = 54,544) on 1m bars. Outcome = still beyond the level k minutes later.
- **Results:**
  - +1.1 pp at 30 minutes (z 2.1) and at 120 minutes (z 2.0);
  - median 120-minute return +0.25 vs −0.01 ATR;
  - by age at 120 minutes: < 60 min +0.9, 1-4 h −0.1, **4-12 h +5.1 (z 3.3)**, > 12 h +1.8 (z 0.9).
- **B's reading:** the age split is non-monotone, and a single z = 3.3 bucket out of 8 age × horizon cells does not survive a multiple-comparison correction (Bonferroni α = 0.006 needs z ≈ 2.7, so it passes alone, but with no monotone support). Graded **weak**. The overall +1.1 pp continuation is consistent with S6 and sibling T1 (symmetric burst plus a small drift).

### 2.6 Limitations
- One 3-month 1m window (2026Q1) on 6 CME futures; 5m and 15m are resampled from it; 13 months of 1H CME; 1H NQ/GC/EUR over about 2 years. No crypto in B's own tests (sibling BTC results quoted).
- **Overlap:** checkpoints overlap; cluster SEs by symbol-day partly correct for it.
- **Unmodelled engine features:** B's crowding and age tests use plain pivot pools, not the engine's EQ merging, `zoneATR` or registry. The sibling's engine-like design gives the opposite crowding sign at 5m, which is why everything here is learned rather than fixed.
- **The flip null destroys all direction**, including hour-scale trends. "Stale level breaks more" therefore mixes level memory and trend persistence; for forecasting the distinction does not matter.

### 2.7 Priors for the engine (corrected summary)

| Quantity | Prior | Scope | Evidence |
|---|---|---|---|
| Bounce memory on arrival (excess vs volatility-path null) | **0** (≤ +2.7 pp only on 1m, fresh) | all TFs | moderate (null result) [CORRECTED] |
| Stale level on arrival | −2 to −2.5 pp bounce (breaks slightly more) | 1m-5m | weak |
| Pool reach vs random level, all pools | −1 to −2 pp | all TFs (sibling 1H/daily −1.4) | strong |
| Test count | **0** (no bonus) | all | moderate |
| Pool age, reach ratio | ≤ 15m charts: 0.98 / 0.91 / 0.80 / 0.77 for < 12 h / 12-24 h / 24-72 h / > 72 h. ≥ 30m charts: 0.95 / 1.00 / 0.98 / 0.87 | chart swings | moderate [NEW-B] |
| Young pool (< 1 h) | 0.97-0.98 | 1m-5m | moderate (agrees with WYK) |
| Path crowding ratio | **1.0** prior, learned (range seen: 0.75-1.08 at nIn ≥ 3) | all | weak, heterogeneous [CORRECTED] |
| Post-sweep continuation | +1 pp hold beyond the level for 15 min-2 h | 1m | weak-moderate |
| Raid/cascade half-life | 30-120 minutes, clock time | all | moderate (S6, S31) |
| Published-level life | ≥ 5 business days | PDH/PWH class | strong |

---

## 3. Engine gap analysis (`baseline_v2.pine`) `[A✓ line refs, CORRECTED statuses]`

| Concept | Status | Lines | What the engine does / what differs |
|---|---|---|---|
| Strict sweep = trade-through; touch ≠ sweep | present | 623-625; BSL zone `[ph, ph+wPx]` 1762; SSL 1774; `f_step` 1434-1459 | Consistent with Osler (stops just beyond, take-profits at the level). Keep |
| S/R barrier on arrival | not needed [CORRECTED from "missing"] | PoT: `f_pot` 434-445, `f_empPoT` 1284-1301, `f_potModel` 1303-1311, readout 2067 | PoT is level-agnostic (distance + volatility). Against a volatility-path null, memory adds ≤ 3 pp at 1m and 0 at 5m+, so a level-agnostic PoT is right. Measure in the ledger (ACAD-3) |
| Test count | **wrong** | `track` 650-658; density 682 | `+0.35·min(tests,6)` rewards an unsupported claim. Remove (ACAD-1) |
| Pool freshness / age | **wrong (units, shape)** | 668-673 (`age = (bar − bornBar)/hlMult`; ramp e-fold `0.25·halfLife` = 37.5 bars; decay half-life `4·halfLife` = 600 bars; peak at about 100 bars); registry key 1818 uses the same bar decay | The ramp is about 10× too strong. Decay in bars means 10 h on 1m and 25 days on 1H, while the measured staleness sits at ~1-3 days of trading time on every TF. The fresh pillar (weight 10) is not a reach probability, so the PoT readout ignores age entirely (ACAD-2) |
| Stack inner vs outer | **wrong (magnitude, sign heterogeneous)** | `f_stackSide` 1230-1251, step 16 1912-1927, inner ×0.70 684-685, `+0.45·stack` 682 | Hard-coded "outermost is the draw". Data: small and mixed (§2.4). The inner pool is what is reached next by geometry. Neutral default (ACAD-1 = ICT-10) |
| Path crowding | missing (learn only) | step 17 1929-1948; only the VP path cost 1946-1947 | No `nIn`. Add as a learned ratio (ACAD-4), not a prior |
| Stop cascade after a sweep | partial | raid 1578-1582; `liqHL` 159 (bars); decay 1535 | Decay in bars: 24 bars = 24 min on 1m, 4 days on 4H. Evidence: 15 min-2 h of clock time. The sign mapping is handled by ICTS-2 / BIAS-4; units by ACAD-5 |
| Round numbers | missing | — | ICT-3 / OF-4 |
| PDH/PDL/PWH/PWL, sessions | present | 944-961, 1797-1822; `f_tierW` 506-516 | Hand-set tiers; Osler: strength ratings useless → ledger-calibrated (ICT-1) |
| N-period extremes (20/40/60-day, 52-week, ATH) | missing | — | ACAD-6 with ICTPD-5 / TIME-8 (one N-day buffer). `ta.max()` documented ("all-time high value of `source` from the beginning of the chart", reference/ta.md:973-978) |
| Timing of highs/lows | partial | killzones 970-976; `f_kzAff` 597-602 | TIME-1 / TIME-5 |
| PDH/PDL exceed probability | present (via PoT) | `f_potModel` 1303 | BIAS-3 for display |
| Trend vs reversion timescale | partial | D vector 1891-1895 (`sV = 0.5·htfBias + …` at 1892) | D works on the trend scale. Correct |
| Local volatility in PoT | present | `potSig = ta.stdev(chg, potLen = 50)` 916; empirical surface ATR-normalised 1527-1532 | The B null-model result shows bounce/penetration depends on the local volatility path. The engine's σ is local. OK |
| Random-level baseline for grading | present (adequate) | `f_potBase` 1314-1322; `f_book` 1461-1499 | Osler-style. B: a trend-conditional baseline changes edges by ≤ 1 pp, so no change needed. Missing: ARRIVE vs THROUGH split and feature buckets (ACAD-3) |
| Level-state calibration | missing | `f_calMult` 1376-1382 (4 families, clamp 0.8-1.2) | No conditioning on age, nIn or bounce state (ACAD-2/3/4; ICT-1 probes) |
| Derived constant `chartS` | present | **308** [CORRECTED from 307] | Used by ACAD-2 and ACAD-5 |

---

## 4. Proposals (best first)

**Shared constraints for all proposals.** They keep the decision history:
- strict trade-through sweeps;
- draw-side-first selection, the 2-bar challenger and 2× flip hysteresis;
- Day Trading mode = D / 4H / 1H.

They follow the engine's conventions:
- all logic on `barstate.isconfirmed`;
- inputs declared in INPUTS (before any function), with `display = display.none` (the overhaul's legend fix);
- multipliers computed in step 17 **before** `lv.evaluate`, because `track` resets `mult` at 657 and the ledger arrays (STATE, ≥ 1020) are declared after `evaluate` (661), so `evaluate` cannot read them (no forward references);
- no new lower-timeframe requests.

**Dropped from A `[CORRECTED]`:**
- A-ACAD-3, the S/R-memory barrier PoT with the `E(b,Δt)` prior: its effect is ≤ 3 pp at 1m only once the volatility path is preserved. The bounce state survives only as a ledger bucket in ACAD-3.
- The pool-age raid weighting in A-ACAD-4: one non-monotone bucket.

### ACAD-1 (P1, S) · Neutral stack and touch terms (amends A-ACAD-1; same change as ICT-10, aligns with SMC-3 / WYK-2 / SKEP-6)

**Why.** The engine hard-codes three effects that are unsupported or mixed in every dataset:
- "outermost is the draw" (inner ×0.70 at 684-685, `+0.45·stack` at 682);
- "tests make a pool denser" (`+0.35·min(tests,6)`, 682).

Measured effects are ±0-3 pp at ≤ 5m and mixed in sign across markets (§2.4, §2.2). A 30% score cut on the inner pool is worth far more than that, and the inner pool is the one geometry reaches first.

**Inputs** (G_SCORE, after 152):
```pine
string stackMode = input.string("Neutral", "Stacked Pools", options = ["Neutral", "Outermost (ICT)"], group = G_SCORE, display = display.none,
  tooltip = "Neutral: no inner-pool penalty or stack bonus (measured effects are small and change sign by market). Outermost: classic ICT rule.")
```

**`evaluate`, 682-685.**
```pine
bool  ictStack = stackMode == "Outermost (ICT)"
float x = 0.9 * this.eqCount + (ictStack ? 0.45 * this.stack : 0.0) + 0.8 * math.min(1.0, this.prom / 3.0) + 1.2 * this.tier()
...
if this.inner and ictStack
    this.mult *= 0.70
```
- The tests term is removed in both modes.
- `stackMode` is a global input declared before `evaluate`, so there is no forward reference.
- Keep the `STK` / `T` tags (`tag`, 638-646). The HTF objective (oKey, 1986) still names the strongest draw-side pool, so ICT's "objective" stays visible while the DOL becomes the "next" pool.
- The `eqCount` term is ICT-10's domain; siblings measured about 0 pp for EQ.

**README:** replace "the outermost pool in a stack is the draw" and any "tests strengthen a pool" wording.

**Ledger measurement:** A/B the two modes on EDGE and BARS→HIT; ICT-1 probes with a `stack > 0` / `inner` bit.

**Evidence:** moderate (null and mixed results across 1m, 5m and 1H; CME, FX and BTC; A, B, ict_liq).

**Risk:** changes a visible ICT convention. The option preserves it. Selection may switch to the inner pool more often; hysteresis (2-bar challenger) limits flicker.

**Effort:** S.

### ACAD-2 (P1, S) · Stale-pool reach ratio in trading time, applied to reach and the PoT readout, learned per chart `[NEW-B]`

**Why.** The most consistent level effect found:
- chart-swing pools that have survived about a day or more (≤ 15m charts) or about 3 days or more (≥ 30m) are reached **8-14 pp less** than a random level at the same distance and trend;
- shown on 1m, 5m, 1H CME and 1H NQ/GC/EUR (§2.3), and agreeing with sibling WYK B.

The engine's freshness decays in bars (10 h on 1m, 25 days on 1H), and the displayed PoT ignores age.

**Inputs** (G_SCORE):
```pine
bool  useAge   = input.bool(true, "Stale-Pool Reach Prior", group = G_SCORE, display = display.none,
  tooltip = "Chart-swing pools that survive about 1 day (intraday) / 3 days (1H+) are reached 8-14% less often than their distance implies. Learned per chart by the ledger.")
float freshHLh = input.float(72.0, "Freshness Half-Life (trading hours)", minval = 1.0, step = 1.0, group = G_SCORE, display = display.none)
```

**`Level` (317-348):** add `float rAdj = 1.0`.

**`Trial` (375-395):** add `int ab = -1` (age bucket, chart pools only).

**PURE HELPERS** (before 612):
```pine
// trading hours since the pool's pivot bar (bars x bar length; sessions without bars do not age the pool)
f_ageH(int bornBar) =>
    float(bar_index - bornBar) * chartS / 3600.0
f_ageB(float h) =>
    h < 12.0 ? 0 : h < 24.0 ? 1 : h < 72.0 ? 2 : 3
f_agePrior(int b) =>
    bool fast = timeframe.in_seconds() <= 900
    b == 0 ? (fast ? 0.98 : 0.95) : b == 1 ? (fast ? 0.91 : 1.00) : b == 2 ? (fast ? 0.80 : 0.98) : (fast ? 0.77 : 0.87)
```
- `chartS` (308) is a global derived constant declared before these helpers.

**Fresh pillar** (671, liquidity branch): drop the ramp and use trading time:
```pine
this.fresh := useAge ? math.pow(0.5, f_ageH(this.bornBar) / math.max(this.hlMult, 1.0) / freshHLh) : <current expression>
```

**Reach term** (665): `float reach = ... f_pot(dist, sig, mu * this.side, potH) / 0.95 * this.rAdj ...`, capped at 1.0. `rAdj` is a field, so there is no forward reference.

**STATE** (next to `stN`, 1066): `var array<float> agK = array.new<float>(4, 0.0)` and `var array<float> agE = array.new<float>(4, 0.0)`.

**STATE HELPERS** (after the arrays, before the ENGINE block):
```pine
f_ageMult(int b) =>          // learned reach ratio (hits / random-level expectation), shrunk to the prior with n0 = 30 expected hits
    f_clamp((agK.get(b) + 30.0 * f_agePrior(b)) / (agE.get(b) + 30.0), 0.6, 1.15)
```

**`f_openTrial`** (1426): `ab = lv.isLiquidity() and lv.src == 0 ? f_ageB(f_ageH(lv.bornBar)) : -1`.

**`f_book`** (1461): `if t.ab >= 0` then `agK.set(t.ab, agK.get(t.ab) + y)` and `agE.set(t.ab, agE.get(t.ab) + t.pBase)`.

**Step 17** (inside `for lv in pool`, before `lv.evaluate`):
```pine
lv.rAdj := useAge and lv.isLiquidity() and lv.src == 0 ? f_ageMult(f_ageB(f_ageH(lv.bornBar))) : 1.0
```

**Live PoT** (2067), after `f_potModel`: `activePoT := sweptNow ? 0.95 : math.min(0.95, pMod * activeLv.rAdj)`. The ratio is defined on probabilities, so the product is the literal application.

**UX:** append the age to the tooltip ("age 1.6 d · stale −15%") when `rAdj < 0.95`.

**Scope.** Chart-swing pools only (src 0), which is what was tested. PDH/PWH and sessions have known ages by construction, and HTF/STF registry pools were not tested. Extend to them through the ledger later (ICT-1 probes).

**Ledger measurement:** a Full-view row "AGE <12h/12-24/24-72/>72h edge"; Brier score of PoT with vs without `useAge`.

**Evidence:** moderate (4 data groups, 3 timeframes, trend-conditional, cluster-robust; WYK agrees; mechanism = survivorship plus hour-to-day trend persistence, S21).

**Risk.**
- Only the active DOL is graded, so old-pool buckets fill slowly and the prior dominates for a long time.
- On ≥ 30m charts the 12-72 h prior is ≈ 1, so the only bite there is beyond 72 h.
- Interaction with the draw vector (D already leans away from counter-trend old pools) is handled by learning the residual.

**Effort:** S.

### ACAD-3 (P2, M) · Two-stage ledger: ARRIVE vs THROUGH-given-ARRIVE, with feature buckets (A-ACAD-2, refocused)

**Why.**
- S/R research measures what happens at the level; the engine records only "hit within H".
- Splitting the outcome separates **arrival skill** (does the engine pick places price goes?) from **barrier behaviour** ("got there but it held").
- It is also where per-chart bounce memory, age and crowding get measured honestly. The 1H evidence is heterogeneous, so per-chart learning is the only defensible way to use them.

**Inputs** (G_ACC): `float arrGam = input.float(0.35, "Arrival Stripe (ATR)", minval = 0.05, maxval = 1.0, step = 0.05, group = G_ACC, display = display.none)`. Default 0.35 ATR ≈ 0.5 × mean|ΔC| (A's Appendix A.2).

**`Trial`:** add
- `bool arr = false`, `float gam = 0.0`, `float pArrB = na`, `float pThrB = na`;
- `int mb = 0`: memory bucket = `(tests ≥ 2 ? 2 : tests) * 2 + (bar_index − lastTest < 15 ? 0 : 1)` from existing fields;
- `int cb = 0`: the nIn bucket from ACAD-4.

**`f_openTrial`** (1426):
```pine
float g  = arrGam * atr
float dA = math.max(0.0, d - g)
pArrB := f_potBase(dA, lv.side)                                             // random level: P(reach the stripe)
pThrB := f_clamp(f_potBase(d, lv.side) / math.max(pArrB, 1e-6), 0.01, 0.99)  // random level: P(through | arrive) = S(d)/S(d−g)
```
This is the exact random-level analogue of Osler's arbitrary levels; no new state.

**`f_step`** (1434), before `hit`:
```pine
t.arr := t.arr or (t.side == 1 ? high >= t.edge - t.gam : low <= t.edge + t.gam)
```

**`f_book`** (1461): accumulate
- `arN`, `arK`, `arE` (Σ pArrB);
- for arrived trials, `thN`, `thK`, `thE` (Σ pThrB) per memory bucket (6 cells), per age bucket (4) and per crowd bucket (4).
- Use `var array<float>` in STATE.

**Display** (Terminal Full view): `ARRIVE 71% (rand 66%) · THRU|ARR 58% (rand 74%)`. Cells only at n ≥ 20.

**Evidence:** strong for the framework (S1-S3). Its purpose is measurement. It does not change selection.

**Risk:** slow cell fill (about 1 trial per H bars). ICT-1 candidate probes would speed it up 10-30×.

**Effort:** M.

### ACAD-4 (P3, S) · Learned path-crowding ratio, neutral prior (replaces A-ACAD-1's fixed prior)

**Why.**
- `nIn` predicts reach on 1m and on CME/FX 1H when old pools are kept (§2.4), but the sign flips for young 5m pools and in BTC.
- Much of it is age, which ACAD-2 handles.
- What remains is chart-specific. Learn it; do not assume it.

**`Level`:** add `int nIn = 0`.

**Step 16** (after 1927; O(n²) with n ≤ `poolMax` = 40, `inCalc` bars only):
```pine
for lv in pool
    int k = 0
    if lv.isLiquidity()
        float e = lv.nearEdge()
        for o in pool
            if o.isLiquidity() and o.side == lv.side and o.id != lv.id
                float oe = o.nearEdge()
                if lv.side == 1 ? (oe > close and oe < e - 0.1 * atr) : (oe < close and oe > e + 0.1 * atr)
                    k += 1
    lv.nIn := k
```

**STATE:** `crK`, `crE` (size 4). **`f_openTrial`:** `cb = math.min(lv.nIn, 3)` for liquidity trials. **`f_book`:** accumulate as in ACAD-2.

**`f_crowdMult(b)`:**
```pine
f_crowdMult(int b) =>
    float r0 = (crK.get(0) + 40.0) / (crE.get(0) + 40.0)
    f_clamp(((crK.get(b) + 40.0) / (crE.get(b) + 40.0)) / math.max(r0, 1e-9), 0.8, 1.1)
```
- The prior is 1.0 (no effect until data arrive).

**Step 17:** `lv.rAdj *= f_crowdMult(math.min(lv.nIn, 3))` for liquidity pools.

**Display:** Full-view row "CROWD 0/1/2/3+ edge".

**Evidence:** weak and heterogeneous (§2.4).

**Risk:** slow learning; a small effect at ≤ 5m.

**Effort:** S.

### ACAD-5 (P3, S) · Clock-time half-life for raid events (units fix only; A-ACAD-4 without the age weighting)

**Why.**
- `liqEvt` decays with `liqHL` = 24 **bars** (159, 1535): 24 minutes on 1m, 4 days on 4H.
- Stop-cascade evidence is 15 minutes to 2 hours of clock time:
  - Osler 2005;
  - crypto: 88% of forced selling within 30 minutes (S31);
  - A's 1m test: +1.1 pp continuation at 30-120 minutes.
- The sign of the raid → D mapping is fixed elsewhere (ICTS-2 / BIAS-4).

**Spec:**
- Input `float liqHLm = input.float(60.0, "Liquidity-Event Half-Life (minutes)", minval = 5.0, group = G_FLOW, display = display.none)`.
- Replace 1535 with `liqEvt *= math.pow(0.5, chartS / 60.0 / liqHLm)`.
- Keep the `+evt·tier` update at 1582 (or the sibling's corrected mapping).

**Ledger:** side hit-rate A/B through the BIAS-1 side ledger or the ICTS-1 draw-skill gate.

**Evidence:** weak-moderate (S6 strong in FX at round numbers; bar-level effect small).

**Risk:** on 4H and above the term vanishes within a bar and D leans on structure, which is intended (no effect at 1-2 days, S6).

**Effort:** S.

### ACAD-6 (P3, S) · 52-week and all-time extremes as anchor pools, on the shared N-day buffer (A-ACAD-5, aligned with ICTPD-5 / TIME-8)

**Why.**
- These are the best-documented anchors in finance (S11-S15): barriers on approach, continuation after a break.
- They are natural Swing-mode objectives.
- The sibling found 20/40/60-day extremes reached at baseline rates, so the value is **naming and objectives**, not a score boost.

**Series** (one request; the engine has 6 `request.*` calls today):
```pine
[h52, l52, ath, atl] = request.security(syminfo.tickerid, f_tfSafe("D"),
  [ta.highest(high, 252)[1], ta.lowest(low, 252)[1], ta.max(high)[1], ta.min(low)[1]], lookahead = barmerge.lookahead_on)
```
- `[1]` with `lookahead_on` does not repaint.
- `ta.max` is the max since the first bar of the requested dataset (reference/ta.md:973-978), so on short histories "ATH" means "highest in the loaded data". Label it so.
- Use 365 instead of 252 when `syminfo.type == "crypto"`.
- If ICTPD-5 / TIME-8 build the N-day ring buffer, compute these from it instead of a new request.

**Registry** (step 10, 1797-1822):
- `src` 8 = 52W, 9 = ATH/ATL;
- `f_tierW` 0.80 (same as PDH; Osler: hand-set strength ratings carry no information);
- names "52W H/L", "ATH", "ATL";
- push via `f_pushExt` when `f_changed(h52)` (865) and so on; anchor with `f_anchorScan` (1141), falling back to `bar_index − anchorMax`.

**Measurement:** family EDGE for `src ≥ 8`.

**Evidence:** strong at daily to monthly horizons in stocks; none for intraday reach.

**Risk:** low; usually outside `maxATR` on intraday charts.

**Effort:** S.

### Considered and not proposed
- **S/R-memory barrier PoT** (A-ACAD-3, `E(b,Δt)` prior): the effect is ≤ 3 pp at 1m and 0 at 5m+ against a volatility-path null (§2.2). It is not worth a model term; keep it as a ledger bucket (ACAD-3).
- **Fixed path-crowding prior [1, .97, .92, .82]** (A-ACAD-1): the 1H basis was corrupted data, and the 1m/5m effect vanishes in the engine's ejected pool universe (§2.4).
- **Round-number pools:** ICT-3 / OF-4.
- **"Each touch weakens the level":** no support.
- **Previous-day-high or gap "magnet":** geometry and S33.
- **Time-of-day priors:** TIME-1.
- **Option-strike pinning:** needs open interest.
- **Range-break signals:** decayed (S18), fail after costs (S20).

---

## 5. Sources

**Read or verified in this pass (B).**
- Garzarelli, F., Cristelli, M., Pompa, G., Zaccaria, A., Pietronero, L. (2014). Memory effects in stock price dynamics: evidences of technical trading. Sci. Rep. 4:4487. https://arxiv.org/abs/1110.5197 (full text: Table 1, fBm test).
- Chung, K., Bellotti, A. (2021). Evidence and Behaviour of Support and Resistance Levels in Financial Time Series. https://arxiv.org/abs/2101.07410 (full text: Tables 3.1, 4.1-4.3; AR(1) §5).
- Safari, S., Schmidhuber, C. (2025). Trends and Reversion in Financial Markets on Time Scales from Minutes to Decades. https://arxiv.org/abs/2501.16772 (full text §3.4, §5).
- Jung, J., Lee, K. (2026). Do Round Numbers Hold Prices? https://arxiv.org/abs/2610.34787 (abstract).
- Taylor, V. (2026). Evaluating the Predictive Validity of ICT's AMD Model on CME E-Mini NASDAQ-100 Futures. https://arxiv.org/abs/2610.35887 (abstract).
- Mesfin, M. (2026). Structural Limits of OHLCV-Based Intraday Momentum Signals in MNQ Futures. https://arxiv.org/abs/2605.04004 (abstract).
- Garcia Seuma, R. M. (2026). Measuring the engine of a liquidation cascade: subcritical branching inside a first-order transition. https://arxiv.org/abs/2608.03616 (abstract).
- Wan, Y.-L., Xie, W.-J., Gu, G.-F., Jiang, Z.-Q., Chen, W., Xiong, X., Zhang, W., Zhou, W.-X. (2015). Statistical properties and pre-hit dynamics of price limit hits in the Chinese stock markets. PLoS ONE 10(4): e0120312. https://doi.org/10.1371/journal.pone.0120312
- Zapranis, A., Tsinaslanidis, P. (2012). Identifying and evaluating horizontal support and resistance levels: an empirical study on US stock markets. Applied Financial Economics 22(19): 1571-1585. https://ideas.repec.org/a/taf/apfiec/v22y2012i19p1571-1585.html
- Lo, A., Mamaysky, H., Wang, J. (2000). Foundations of Technical Analysis. J. Finance 55(4): 1705-1765. https://www.nber.org/papers/w7613
- Plastun, A., Sibande, X., Gupta, R., Wohar, M. Price gap anomaly in the US stock market: the whole story (via summaries). https://econpapers.repec.org/RePEc:pre:wpaper:201963 · Caporale, G. M., Plastun, A. (2017). Price gaps: another market anomaly? Investment Analysts Journal.
- Vendor study, gold swing-level tests (MQL5 blog, 2026; weak, commercial). https://www.mql5.com/en/blogs/post/780740
- Pine v6 reference, `ta.max()` / `ta.min()`: `docsrc/jabez4jc_pinescriptv6/reference/ta.md:973-978, 1048`.

**From A (numbers as A read them; B could not re-open the first two).**
- Osler, C. (2000). Support for Resistance. FRBNY EPR 6(2): 53-68. https://www.newyorkfed.org/medialibrary/media/research/epr/00v06n2/0007osle.html
- Kavajecz, K., Odders-White, E. (2004). Technical Analysis and Liquidity Provision. RFS 17(4). https://papers.ssrn.com/sol3/papers.cfm?abstract_id=315660
- Osler, C. (2003). Currency Orders and Exchange-Rate Dynamics. J. Finance 58(5). https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr125.pdf
- Osler, C. (2005). Stop-loss orders and price cascades in currency markets. JIMF 24(2). https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr150.pdf
- Lallouache, M., Abergel, F. (2014). Tick Size Reduction and Price Clustering in a FX Order Book. https://arxiv.org/abs/1307.5440
- De Grauwe, P., Decupere, D. (1992). CEPR DP621. https://ideas.repec.org/p/cpr/ceprdp/621.html
- Donaldson, R. G., Kim, H. Y. (1993). JFQA 28(3). https://ideas.repec.org/a/cup/jfinqa/v28y1993i03p313-330_00.html
- Aggarwal, R., Lucey, B. (2007). RFE 16. https://ideas.repec.org/a/eee/revfin/v16y2007i2p217-230.html
- Bhattacharya, U., Holden, C., Jacobsen, S. (2012). Mgmt Sci 58(2). https://host.kelley.iu.edu/cholden/Bhattacharya%20Holden%20and%20Jacobsen%20(2012).pdf
- George, T., Hwang, C.-Y. (2004). J. Finance 59(5). https://www.bauer.uh.edu/tgeorge/papers/gh4-paper.pdf
- Li, J., Yu, J. (2012). JFE 104(2). https://econpapers.repec.org/RePEc:eee:jfinec:v:104:y:2012:i:2:p:401-419
- Huddart, S., Lang, M., Yetman, M. (2009). Mgmt Sci 55(1). https://ideas.repec.org/a/inm/ormnsc/v55y2009i1p16-31.html
- Driessen, J., Lin, T.-C., Van Hemert, O. (2013). RoF 17(1). https://ideas.repec.org/a/oup/revfin/v17y2013i1p369-401.html
- Bhootra, A., Hur, J. (2013). JBF 37(10). https://ideas.repec.org/a/eee/jbfina/v37y2013i10p3773-3782.html
- Brock, W., Lakonishok, J., LeBaron, B. (1992). J. Finance 47(5). https://ideas.repec.org/a/bla/jfinan/v47y1992i5p1731-64.html
- Sullivan, R., Timmermann, A., White, H. (1999). J. Finance 54(5).
- Holmberg, U., Lönnbark, C., Lundström, C. (2013). FRL 10(1). https://ideas.repec.org/a/eee/finlet/v10y2013i1p27-33.html
- Ni, S. X., Pearson, N., Poteshman, A. (2005). JFE 78(1). https://ideas.repec.org/a/eee/jfinec/v78y2005i1p49-87.html
- Golez, B., Jackwerth, J. (2012). JFE 106(3).
- Cho, D., Russell, J., Tiao, G., Tsay, R. (2003). J. Empirical Finance 10.
- Caporin, M., Ranaldo, A., Santucci de Magistris, P. (2013). JBF 37(12). https://econpapers.repec.org/RePEc:eee:jbfina:v:37:y:2013:i:12:p:5132-5146
- Valenti, D., Spagnolo, B., Bonanno, G. (2006). https://arxiv.org/abs/physics/0608201
- Bouchaud, J.-P., Farmer, J. D., Lillo, F. (2008). https://arxiv.org/abs/0809.0822 · Benzaquen, M., Bouchaud, J.-P. (2017). https://arxiv.org/abs/1710.03734
- Andersen, T., Bollerslev, T. (1997, 1998), via sibling ict_time.

**Siblings:** `ict_liq.final.md` (ICT-1, ICT-3, ICT-10; B11 data correction), `ict_pd.final.md` (ICTPD-5), `ict_time.final.md` (TIME-1, TIME-8), `bias_dol.final.md` (BIAS-1/3/4), `ict_struct.final.md` (ICTS-1/2), `wyckoff_sd.final.md` (WYK-2; age correction), `smc_impl.final.md` (SMC-3), `orderflow_micro.md` (OF-4).

---

## Appendix A. Reproduction

Data:
- `brief/study/amt_data/cme/<SYM>/<SYM>_{1min,1h}_*.csv`;
- clean 1H NQ/GC/EUR in `sim/data/{nq,gc,eu}.csv`.

Run with `python3 -I` from the tools folder. Each run takes 5-60 s.

**A (`brief/study/academic_tools/`):**

| Command | Output |
|---|---|
| `srmem.py ../amt_data/cme bar 1.0 3` | `out_srmem_bar_g1.txt` (A's §2.2, shuf null) |
| `srmem.py ../amt_data/cme {close 1.0 / bar 0.5 / bar 2.0} 3` | robustness tables |
| `srmem.py ../amt_data/cme bar 1.0 5 1h` | `out_srmem_bar_g1_1h.txt` (**contains corrupted GC 1H**) |
| `reach.py ../amt_data/cme 30 15` | `out_reach_H30.txt` |
| `barrier.py ../amt_data/cme 30 60 0.5 [1h]` | `out_barrier[_1h].txt` (**1h contains corrupted GC**) |
| `cascade.py ../amt_data/cme 2` | `out_cascade.txt` |

**B (`brief/study/academic_b_tools/`):**

| Command | Output |
|---|---|
| `srmem_b.py ../amt_data/cme 1 flip 1.0 3` | `out_1m_flip.txt` (strict null, 1m) |
| `srmem_b.py ../amt_data/cme {1,5,15} {shuf,flip} 1.0 5` | `out_{1,5,15}m_{shuf,flip}.txt` |
| `crowd_b.py ../amt_data/cme 30 1min` | `out_crowd_1m.txt` (crowding + random-level + trend controls) |
| `crowd_b.py ../amt_data/cme 30 1h` | `out_crowd_1h.txt` (**includes corrupted GC; superseded**) |
| `crowd_b.py ../amt_data/cme 30 1h ES,NQ,RTY,YM,CL [EJ]` | `out_crowd_1h_clean*.txt`, `out_crowd_1h_ej15.txt` |
| `crowd_b.py ../amt_data/cme 30 5min [SYMS] [EJ]` | `out_crowd_5m.txt`, `out_crowd_5min_ej*.txt` |
| `crowd_b.py ../amt_data/cme 30 {1min,5min,1h} <SYMS> {1e9,15}` | `out_age_*_ej*.txt` (age tables, §2.3) |
| `crowd_b.py <scratchpad>/sim/data 30 sim1h nq,gc,eu 15` | `out_crowd_sim1h_ej15.txt` |

**Data scan (B):** an inline pandas check of bar-to-bar log gaps over 1.5% and jump-and-back pairs. Result: GC 1H 692 / 281; all other files ≤ 9 / 0.

## Appendix A.2. Stripe width vs ATR (median ATR(14)) `[A✓]`

| Symbol | 1m: mean\|ΔC\| / ATR | 1H: mean\|ΔC\| / ATR |
|---|---|---|
| ES | 0.61 | 0.59 |
| NQ | 0.61 | 0.57 |
| GC | 0.76 | 0.91 (corrupted file) |
| CL | 0.74 | 0.84 |

So k = 0.5 ≈ 0.30-0.38 ATR, which is the engine's `testATR` (0.30) and ACAD-3's default arrival stripe of 0.35 ATR.
