# x1 · Option-implied volatility, expected move and event-aware sigma (final report)

Lens: forward-looking volatility from options as an input to the engine's Probability of Touch (PoT), its horizon variance and its display.
Scope: VIX-family indices reachable from Pine, IV vs realised volatility, variance-risk-premium (VRP) scaling, index-to-chart mapping, term-structure event detection, event and calendar volatility, expected-move bands, and the options-implied touch probability as a benchmark.

Everything numeric labelled **[T]** is this lens's own out-of-sample test on local data. The scripts and raw outputs are listed in §6, so later agents can re-run or extend them.

---

## 0. Executive summary (read this if nothing else)

1. **Implied vol is a real but second-order PoT input once a good realised forecast exists.**
   - **Against the engine as it is now** (ATR14 unit, flat 50-bar σ): an IV level shaped by a time-of-day clock cuts the H-bar touch log-loss by 2.5-6.8% on ES/NQ/RTY 1H **[T]**.
   - **Against the time-of-day clock with a fast deseasonalised realised level** (the design ict_time TIME-3 already proposes), IV *alone* is **worse**: -1.5 to -6% on ES 1H, NQ 1H, ES 5m, CL and BTC **[T]**.
   - A **geometric blend** `σ² = L^(1-w)·(κ·IV²)^w` with w = 0.25-0.5 adds a small, mostly significant increment over TIME-3: ES 1H +0.5-0.6%, RTY 1H +1.3-1.6%, CL 1H +0.5%, BTC 1H +0.3-0.5%, NQ and ES 5m ±0.2% (n.s.) **[T]**.
   - The first pass of this lens compared IV only against a *slow* realised level and overstated IV's value. This report corrects that.
2. **At daily horizons IV matters more.**
   - 1-day touch on SPX: VIX1D -5.4%, VIX9D -3.4%, VIX -1.3% log-loss vs ATR14 (2022-26) **[T]**.
   - HAR + VIX1D raises the out-of-sample R² of next-day log range-variance from 0.32 to 0.50 **[T]**.
   - This agrees with the literature: IV beat historical models in most of the 93 studies Poon & Granger reviewed; VIX1D beats HAR at 1 day (Albers 2025).
3. **Alignment decides whether IV helps.**
   - `request.security(sym, "D", close[1], lookahead_on)` on an RTH-only index returns **the day-before-yesterday's close** from 16:15 until 09:30 the next day.
   - That staleness costs 1-1.5 pp intraday. On a daily chart it destroys VIX1D's edge (+5.4% falls to +0.9%), while VIX9D survives it (+3.4% to +2.5%) **[T]**.
   - Fix: latch the fresh 16:15 close from an hourly `[close[1], time_close[1]]` request (spec in X1-1).
4. **Raw IV overstates touch probability (the VRP).**
   - Realised daily variance is 0.51-0.66 × VIX² and 0.75 × VIX1D² **[T]**.
   - The best sd scale is about 0.70 for VIX (0.57-0.89 by year) and 0.83 for VIX1D (0.79-0.86 by year) **[T]**.
   - So the "market-implied PoT ≈ 2 × delta" runs high: for 1-day touches the predicted mean is 0.37 against 0.25 observed with VIX, and 0.31 against 0.24 with VIX1D **[T]**.
   - tastylive's 20-year SPY study reports the same.
5. **The VRP scale depends on the term structure.**
   - Contango (VIX/VIX3M < 0.9): sd scale about 0.63. Backwardation (≥ 1): about 0.90. The scale for ATR moves the same way **[T]**.
   - Keying the PoT scale by VIX/VIX3M or VIX9D/VIX improves log-loss out of sample by +0.4 to +1.6%, replicated in 2011-18 and 2022-26 **[T]**.
6. **Events.**
   - The 08:30 CPI/NFP bar carries 3.9× (median 6.7×) the variance of the same hour on other days; the FOMC 14:00 bar 4.8× (median 8×) **[T]**.
   - Day level: event days run about 2× a 22-day RV forecast, but only 1.06-1.15× VIX1D. **VIX1D already prices the event day** **[T]**.
   - Rule **[T]**:
     - with a realised level, *add* event-hour variance (event-window log-loss -7.6%);
     - with a VIX1D level, *redistribute* the day's variance toward the release bar (day total kept);
     - with a blend, redistribute the implied share w.
7. **The term structure as an event detector.**
   - log(VIX1D/VIX) at the prior close separates FOMC/CPI/NFP eves from other days with AUC 0.87 (2022-25).
   - A relative detector (minus its 20-day median, ≥ 0.20) has precision 0.45-0.58 and recall 0.70 (2022-25), but recall falls to 0.45 in 2025-26 **[T]**.
   - It is a **cross-check flag** for the manual calendar (ASSET-5), not a replacement, and must not drive variance on its own (it hurt when it did) **[T]**.
8. **Calendar effects are small and mostly the opposite of the folklore.**
   - Variance on monthly OPEX Fridays ×0.86, triple witching ×0.81, first trading day of the month ×1.31 [1.19, 1.45] **[T]**.
   - No "post-OPEX window of weakness" (weekly range ×0.97) and no max-pain pinning beyond a strike-distance null **[T]**.
9. **Expected-move bands.**
   - SPX ±1σ(VIX) from the prior close: either side touched on 33% of days, close inside 80% (Brownian 68%) **[T]**.
   - With VIX1D: 47% and 73% **[T]**.
   - Weekly ±VIX·√(5/252): touched on 32-37% of weeks, close inside 79-82% **[T]**.
   - They are context lines, not liquidity.

**Proposals (best first):**
- X1-1: IV level blended into the forward variance (feed, root mapping, fresh alignment, unit-preserving κ, w gated by the ledger's proper scores).
- X1-2: event-aware horizon variance (add vs redistribute rule).
- X1-3: term-structure state for PoT calibration.
- X1-4: options-implied event-detector flag.
- X1-5: expected-move band display.
- X1-6: options-implied PoT graded as a benchmark.
- X1-7: calendar variance cells.
- X1-8: earnings-aware variance for stocks.

---

## 1. Concepts (definitions and parameters)

### 1.1 Implied-volatility indices reachable from Pine

All are requested with `request.security`. Values are annualised % σ. Daily σ = IV/100/√252 (√365 for 24/7 crypto indices).

| Index | TradingView ticker | Measures | Horizon | Session / history | Notes |
|---|---|---|---|---|---|
| VIX | `CBOE:VIX` | SPX 30-day variance-swap IV | 30 calendar days | RTH 09:30-16:15 ET (Cboe also disseminates extended-hours values; whether TV's daily bars include them is unverified). Cboe history from 1990 | The reference index |
| VIX1D | `CBOE:VIX1D` | SPX same-day, from 0DTE + 1DTE SPXW options | 1 trading day | **RTH only**. TV history from 2023-04-24 (launch); Cboe backfill from 2022-05-13 (OHLC flat, close-only, until 2023-03-31 in Cboe's file) | Strong intraday artefact: rises in RTH, falls overnight (§1.8). Use the **daily close only** |
| VIX9D | `CBOE:VIX9D` | SPX 9-day IV | 9 calendar days | RTH; from 2011-01 | Most robust to a 1-day lag (§2.4) |
| VIX3M | `CBOE:VIX3M` (formerly VXV) | SPX 3-month IV | 93 days | RTH; Cboe file from 2009-09 | Term-structure denominator |
| VIX6M | `CBOE:VIX6M` | 6-month | | | not tested |
| VVIX | `CBOE:VVIX` | Vol of VIX | 30 days | from 2006-03 | not used (untested as a tail state) |
| VXN | `CBOE:VXN` | Nasdaq-100 IV | 30 days | RTH | **Not tested here** (Cboe CDN blocked by policy in this session); VIX used as a proxy for NQ |
| RVX | `CBOE:RVX` | Russell 2000 IV | 30 days | RTH | proxy-tested with VIX |
| VXD | `CBOE:VXD` | DJIA IV | 30 days | RTH | proxy-tested with VIX |
| OVX | `CBOE:OVX` | USO options (crude oil) IV | 30 days | RTH; Cboe file from 2009-09 | Tested on CL |
| GVZ | `CBOE:GVZ` | GLD options (gold) IV | 30 days | RTH; Cboe file from 2009-09 | GC test void (bad local data, §2.3) |
| MOVE | `TVC:MOVE` | ICE BofA Treasury normal (bp) yield vol | 1 month | daily | **Unit mismatch** (bp yield vol, not % price vol); do not map to ZN/ZB without a duration conversion |
| BTC DVOL | `DERIBIT:DVOL` | Deribit BTC 30-day IV (VIX-style) | 30 days | 24/7; from 2021-03 | Daily σ ≈ DVOL/19.1 (√365) |
| ETH DVOL | `DERIBIT:ETHDVOL` (unverified) | | | | user override |
| Volmex | `VOLMEX:BVIV`, `VOLMEX:EVIV` | BTC/ETH 30-day IV | | 24/7 | alternatives seen in TV ideas |
| CME CVOL | none found on TradingView | | | | not available → fallback |
| FX vol (EVZ etc.) | status unclear | | | | fallback to realised |

- **Data plan.** TradingView carries Cboe indices for everyone with a delay; real-time is a paid exchange add-on (TradingView blog, Mar 2023; Cboe's public pages are delayed ≥ 15 min). Using the 16:15 daily close is unaffected. Hourly `[1]` values are at most about 15 min late in real time.
- **Request budget.** 40 unique `request.*()` calls per script (Functions.md: "no more than 40 unique request.*() function calls"); the engine uses 6 (lines 923-925, 939, 981-982). v6 requests are dynamic by default, so `symbol` may be a computed (simple/series) string. `ignore_invalid_symbol = true` returns na instead of halting (reference: "if true, the function will return na and execution will continue").

### 1.2 IV as a volatility forecast; Mincer-Zarnowitz and encompassing tests
- **Mincer-Zarnowitz (MZ).** Regress realised (log) variance on forecast (log) variance. Slope 1 and intercept 0 mean unbiased; R² measures information.
- **Encompassing.** Add past RV (or HAR terms) next to IV. A significant IV coefficient with insignificant RV terms means IV "subsumes" history.
- **HAR** (Corsi 2009): `log RV_{t+1} = b0 + b1 log RV_d + b2 log RV_w(5) + b3 log RV_m(22) [+ b4 log IV²]` (HAR-IV, Busch, Christensen & Nielsen 2011).
- **Edge cases.**
  - Overlapping monthly windows bias the tests (Christensen & Prabhala 1998 use non-overlapping data).
  - The 1987 crash is a regime break.
  - IV is risk-neutral, so its level is biased upward by the VRP (§1.3).

### 1.3 Variance risk premium (VRP) and the unbiased-σ scaling
- VRP = E^Q[RV] - E^P[RV] > 0 for index options. The variance-swap rate exceeds subsequent realised variance on average (Carr & Wu 2009, "strongly negative" premiums for SPX/OEX/DJIA).
- **Scaling to an unbiased σ:** `σ_P = s·IV`. The touch-calibrated `s` also absorbs discreteness and fat tails.
  - **[T]** realised daily variance / IV² = 0.556 (VIX 1999-2018), 0.508 (VIX 2011-18), 0.626 (VIX 2022-26), 0.660 (VIX9D), 0.747 (VIX1D).
  - **[T]** best touch sd scale: VIX 0.67-0.74, VIX9D 0.69-0.76, VIX1D 0.83-0.84.
  - **[T]** by calendar year: VIX 0.57-0.89, VIX1D 0.79-0.86. VIX1D's premium is the most stable.
- **The scale is state-dependent** (§2.6): low in contango, near 0.9 in backwardation. Johnson (2017, JFQA) finds the VIX term-structure slope carries information about the *price of variance risk*, not expected VIX changes. That is the mechanism.
- **Engine-friendly form.** Learn κ online as a slow EWMA of `L/IV²`, where L is the realised level, so the IV term enters in the realised model's own units ("unit-preserving"). Never hard-code a VRP constant.

### 1.4 Mapping an index IV onto the chart symbol (root / type / base currency)
- **Direct roots** (`syminfo.root` for futures, `syminfo.ticker` otherwise; `syminfo.basecurrency` for crypto):
  - ES, MES, SPX, SPY, US500 → VIX1D (horizon ≤ about 1 day, intraday), VIX9D (≤ 9 days), VIX (longer);
  - NQ, MNQ, NDX, QQQ, US100 → VXN;
  - RTY, M2K, RUT, IWM → RVX;
  - YM, MYM, DJI, DIA, US30 → VXD;
  - CL, MCL, USO, WTI/USOIL → OVX;
  - GC, MGC, GLD, XAUUSD → GVZ;
  - base currency BTC → DERIBIT:DVOL (annualise with 365, no RTH latch).
- **Beta mapping (stocks, FX, others): not recommended.**
  - Stock variance = β²σ_m² + σ_idio². The idiosyncratic share is large and time-varying.
  - The ratio-modulation version `ATR14·√(VIX/EMA60(VIX))` was **worse** than plain ATR on ES 1H (-0.9 to -1.0%), NQ (-0.9%), ES 5m (-0.4%) and BTC (-0.2%) **[T]**.
  - So the fallback for unmapped symbols is **no IV** (w = 0), not a beta-scaled VIX.
- **Proxy mapping** (an index IV on a related market, e.g. VIX on NQ, RTY, YM) works because the blend learns the level ratio through κ: NQ +0.1% (n.s.), RTY +0.9 to +1.6% over TIME-3 **[T]**. Prefer the native index when available.
- **User override:** `input.symbol` for any custom IV ticker.

### 1.5 Term structure: VIX1D/VIX, VIX9D/VIX, VIX/VIX3M
- **Contango** (short < long) is the calm norm. VIX/VIX3M averages about 0.90-0.95 (practitioner convention); in our 2011-26 data the ratio was < 0.90 on about 60% of days.
- **Backwardation** (≥ 1) marks stress. Realised vol is rising; trailing estimators lag; the VRP shrinks.
- **Event inversion:** before a scheduled macro release, the 1-day tenor (VIX1D) jumps relative to 30-day VIX because the event variance is concentrated in one day.
  - **[T]** log(VIX1D/VIX) at the close before FOMC +0.09, CPI +0.10, NFP +0.04, vs -0.21 on other days (2022-05..2025-09).
  - **[T]** the day-before change in log VIX1D is +0.31 vs -0.05.
- **Event variance extraction (concept):** with two tenors T1 < T2 straddling a known event, the event's variance ≈ T1·σ1² - (T1 - 1)·σ_base². This is the term-structure method behind Dubinsky, Johannes, Kaeck & Seeger (2019) for earnings. VIX1D does this for free on SPX.

### 1.6 Scheduled-event volatility (FOMC, CPI, NFP, earnings)
- Release minutes carry most of the day's news variance. Ederington & Lee (1993): announcements drive time-of-day and weekday patterns. Lee (2012, RFS): jumps follow FOMC, NFP and claims.
- **IV crush:** implied vol falls after the release as uncertainty resolves (Ederington & Lee 1996). The VIX decline is gradual, over about 45 minutes after FOMC (intraday study cited in search). The FRBSF 2019 working paper finds monetary-policy uncertainty falls on announcement and rebuilds over 2 weeks.
- **Earnings:** an expected jump on a known date (Dubinsky et al. 2019: the anticipated uncertainty is "quantitatively large, varies across time, and is informative about future volatility").
  - Practitioner data (ORATS): actual/implied earnings move ≈ 0.85 on average, but not reliably for any one stock.
  - Pine has `earnings.future_time` ("expected time of the next earnings report, or na"; series int; next report only, so live use) and `request.earnings` for history.

### 1.7 Calendar volatility events
- **OPEX:** third Friday; quarterly = triple witching. SPX AM settlement (SOQ).
  - Pinning to the ATM strike on serial S&P futures-option expiries 1992-2009 (Golez & Jackwerth 2012).
  - Whelan (AEA 2025) finds the pinning tests fail and proposes a charm-hedging channel confined to the AM settlement window.
- **"Window of weakness" folklore:** the week after OPEX has larger ranges because dealer hedges unwind (SpotGamma-style commentary).
- **Turn of month (TOM):** returns literature (Ariel 1987; Lakonishok & Smidt 1988). The ISM manufacturing release (10:00 ET, first business day) and flows add variance.
- **Month-end and quarter-end rebalancing; Russell reconstitution** (last Friday of June).
- **[T]** effects on SPX daily variance: §2.8.

### 1.8 Intraday IV dynamics
- VIX1D is built from 0DTE + 1DTE options to hold about a 1-day horizon. Its methodology produces a **consistent rise during RTH and a decline outside RTH**, with no change in real risk ("The daily rise and fall of the VIX1D", via a paper summary).
- **[T]** non-event days, log(open/prev close) = -0.19 and log(close/open) = +0.21. Caveat: Cboe's OHLC is close-only before 2023-04, which dilutes the averages.
- **Consequence:** never use intraday VIX1D prints as a level. Use the 16:15 close, which prices the next session.
- VIX intraday is much flatter. IV falls after scheduled releases (§1.6).

### 1.9 Expected move (EM) bands
- **Definition (market convention):** EM_1σ = S·IV·√(t/252). The straddle price ≈ 0.8·EM_1σ (√(2/π)). Vendors that quote "straddle = expected move" draw a band 20% narrower, which explains why some report about 57% containment for SPX weeks (tastytrade 2024) while ±1σ(IV) contains about 80% **[T]**.
- **Anchors:** the prior close (when the IV was measured) or the session open (noise-area geometry).
- **Related bands:**
  - ADR (open ± k·ADR14);
  - ATR;
  - the Zarattini-Aziz-Barbon (2024) **noise area**: open ± the 14-day mean |move from the open| at the same minute, gap-adjusted (session_stats §2.4).
- **Engine analogue:** the empirical **reach bands** (median / 80th-percentile excursion over H, lines 2112-2115), which are historical, not forward-looking.

### 1.10 Options-implied probability of touch (≈ 2 × delta)
- **Reflection principle (driftless Brownian):** P(touch K within T) = 2·P(S_T beyond K) = 2Φ(-d/(σ√T)) ≈ 2·|Δ|.
- **Biases:**
  - IV includes the VRP, so the touch probability is too high;
  - skew inflates put-side IV, so put touches occur at about half the theoretical rate while call touches are about on target (tastylive);
  - fat tails make the far-OTM touch probability too low relative to near-OTM (Perelló et al. 2011, quant_pot).
- **Use here:** an external benchmark the engine's PoT should beat in log-loss, not a displayed probability.

### 1.11 Realised benchmarks referenced (for the comparisons)
- `atr14`: the engine's surface unit.
- `aU = √(ATR14·ATR100)`: REG-2.
- `potSig`: 50-bar stdev of close changes, the engine's analytic σ.
- `clkRV`: clock shape × slow daily EWMA of RV.
- **`clkL50`**: clock shape × fast deseasonalised level, an EWMA (span 50 bars) of Garman-Klass-plus-gap variance divided by the bucket's expected share. This is the TIME-3 analogue and **the right realised competitor**.
- Clock shares are learned on the other time fold (out of sample).

---

## 2. Evidence (numbers and sources)

### 2.1 Literature

| Claim | Numbers / finding | Grade | Source |
|---|---|---|---|
| IV beats historical vol as a forecast | 93-study review: option-implied vol more accurate than time-series models in most studies | strong | Poon & Granger 2003 (JEL 41(2)); Poon & Granger 2005 (FAJ) |
| IV subsumes past vol (OEX, monthly, non-overlapping, 1983-95) | IV outperforms past vol and "even subsumes" it in some specifications; earlier bias attributed to overlapping data and the 1987 regime shift. Exact coefficients not retrieved (publisher blocked) | strong | Christensen & Prabhala 1998, JFE 50(2) |
| VIX vs intraday RV for 1-20 day S&P 100 forecasts | VIX most accurate at all horizons and measures OOS; intraday returns add insignificant information | strong | Blair, Poon & Taylor 2001, J. Econometrics 105 |
| HAR-IV | IV has incremental information beyond continuous and jump RV components (FX, stocks, bonds); unbiased in FX and stocks | strong | Busch, Christensen & Nielsen 2011, J. Econometrics 160(1) |
| Counter-evidence | IV adds nothing beyond model-based forecasts' persistence (S&P) | moderate | Becker, Clements & White 2007, JBF 31(8) |
| VIX1D at 1 day | VIX1D overestimates S&P vol (VRP); the adjusted VIX1D beats HAR and HAR-VIX1D | moderate | Albers 2025, J. Futures Markets 45(11) |
| VIX1D in HAR | Much better than VIX at 1 day; its edge decays faster with horizon | moderate | Zhang, Ruan & Zhang 2023, FRL 58 |
| VRP sign and size | Index variance risk premiums strongly negative (swap rate > realised) | strong | Carr & Wu 2009, RFS 22(3) |
| Term-structure slope = price of variance risk | Slope predicts variance-swap, VIX-futures and straddle returns; rejects the expectations hypothesis | strong | Johnson 2017, JFQA 52(6) |
| Event resolution lowers IV | Scheduled news resolves uncertainty; VIX falls after FOMC over about 45 min | strong (mechanism) | Ederington & Lee 1996; FRBSF WP 2019-12 |
| Earnings jump priced in options | Large, time-varying, informative about future vol | strong | Dubinsky, Johannes, Kaeck & Seeger 2019, RFS 32(2) |
| Earnings actual/implied move | ≈ 0.85 on average; varies by name and regime | weak-moderate | ORATS blog |
| Touch ≈ 2× ITM; IV overstates | 20-year SPY 1σ strangles: touch ≈ 2× expiry-ITM; IV overstated both | moderate | tastylive "Testing probability of touch" |
| Weekly EM containment | ±EM contained 57% of SPX weeks (straddle-based EM) | weak | tastytrade 2024 segment |
| 0DTE EM containment | 10:00 ET implied move contained the close 71.0% (68.3% if fair); realised about 13% below implied (193 SPY sessions, 2022-26) | weak-moderate | FlashAlpha study |
| Pinning | S&P futures pinned on serial expiries 1992-2009; recent work disputes pinning | moderate, decaying | Golez & Jackwerth 2012 JFE; Whelan AEA 2025 |
| VIX1D intraday artefact | Rise in RTH, decline overnight, from the methodology | moderate | "The daily rise and fall of the VIX1D" (paper summary) |

### 2.2 Daily SPX tests [T] (`x1_daily.py`, `x1_daily2.py`; 2-fold time OOS; one scale parameter fitted per fold; day-block bootstrap 95% CI)
Setup:
- Touch within h days of levels at k ∈ {0.25, 0.5, 1, 1.5, 2} × ATR14 from the close, both sides.
- PoT = 2Φ(-d/(s·σ_m·√h)).
- Log-loss gain vs ATR14 (positive = better).
- IV known at the 16:15 close of the forecast day ("same close") unless "lag".

| Sample | h | rv50 (engine-like σ) | HAR | VIX | VIX9D | VIX1D | best blend |
|---|---|---|---|---|---|---|---|
| 1999-2018 (N 49,780; base 0.248) | 1 | -3.72% | +0.60% | +0.84% [0.26, 1.49] | | | HAR+IV in log-HAR +1.63% |
| 2011-2018 (N 20,090) | 1 | -4.32% | +1.23% | +2.21% | +3.67% | | har^0.25·iv9^0.75 +3.78% |
| 2022-05..2026-11 (N 11,200; base 0.242) | 1 | -4.72% | +0.37% | +1.33% [0.02, 2.41] | +3.37% | **+5.33% [3.85, 7.05]** | har^0.25·iv1^0.75 +5.16% |
| 2022-26 | 5 | -2.83% | -0.74% | -0.17% | +1.44% | +1.36% | atr^0.25·iv1^0.75 +1.67% |

- **MZ (log next-day range variance).**
  - 1999-2018 R²: rv50 0.41, ATR14 0.50, EWMA 0.47, VIX 0.56.
  - 2022-26 R²: rv50 0.17, ATR 0.29, VIX 0.41, VIX9D 0.45, VIX1D 0.51.
  - The VIX slope is above 1 (1.25-1.41) in logs.
- **log-HAR out-of-sample R²:** 0.519 → 0.560 with VIX (1999-2018); 0.318 → 0.502 with VIX1D (2022-26).
- **Lagged IV**, which is what `[1]`+lookahead gives a daily chart (2022-26, h=1):
  - VIX +1.32% → +0.51%;
  - VIX9D +3.37% → **+2.51%**;
  - VIX1D +5.36% → **+0.91%** (n.s.).
  - At h=5: VIX9D +1.52% → +1.23%; VIX1D +1.39% → +0.23%.
  - On daily charts, use VIX9D.
- **Raw IV PoT calibration** (no VRP scaling, 1-day):
  - VIX mean 0.37 vs 0.25 observed;
  - VIX1D mean 0.31 vs 0.24 observed;
  - by bin with VIX1D: predicted 0.71 → observed 0.58; 0.50 → 0.39; 0.29 → 0.21.
  - Raw log-loss is 3% (VIX1D) to 10% (VIX) worse than calibrated.

### 2.3 Intraday H-bar touch tests [T] (`x1_intraday.py`, `x1_ext.py`; 1H bars 2025-03-21..2026-04-15; ES 5m 2026-01-20..04-15; BTC 1H 2021-03..2025-01)
- Levels at k ∈ {0.5, 1, 2, 3} × ATR14 from the close, both sides; touch within H bars.
- Each model's sd = its level × √(clock share of the next H bars), with the share learned on the other fold.
- IV alignments:
  - `ivr`: exact TV `"D"`+`[1]`+lookahead for an RTH-only daily index (stale 16:15 → 09:30);
  - `ivc`: ET calendar date - 1;
  - `ivf`: fresh, from 16:15.

Gain vs the TIME-3-like fast level `clkL50` (positive = better), with 95% day-block CI:

| Market (IV) | H | atr14 (engine unit) | IV alone, fresh | IV alone, TV "D"[1] | L50^0.75·ivr^0.25 | L50^0.5·ivf^0.5 |
|---|---|---|---|---|---|---|
| ES 1H (VIX1D) | 6 | -8.19% | -0.82% | -3.72% | -0.10% | **+0.53% [0.07, 0.96]** |
| ES 1H (VIX1D) | 12 | -5.07% | -0.28% | -2.72% | -0.02% | **+0.62% [0.25, 1.04]** |
| ES 1H (VIX1D) | 24 | -0.22% | +0.06% | -1.59% | +0.07% | **+0.57% [0.16, 1.01]** |
| ES 1H (VIX9D) | 24 | | -0.05% | -0.93% | +0.32% | +0.63% [0.19, 1.05] |
| ES 1H (VIX) | 12 | | -2.82% | -4.07% | +0.07% | -0.08% |
| NQ 1H (VIX proxy) | 12 | -5.67% | -2.40% | -3.48% | +0.14% (n.s.) | +0.01% |
| RTY 1H (VIX proxy) | 12 | -6.28% | +1.00% | +0.12% | +0.90% [0.56, 1.29] | **+1.62% [0.98, 2.32]** |
| CL 1H (OVX, roll-adjusted) | 12 | -1.83% | -1.59% | -2.39% | **+0.51% [0.13, 0.87]** | +0.59% (n.s.) |
| ES 5m (VIX1D) | 30 | -1.44% | -3.26% | -5.71% | +0.13% (n.s.) | -0.19% |
| ES 5m (VIX) | 30 | | -2.90% | -3.97% | +0.23% (n.s.) | -0.05% |
| BTC 1H (DVOL) | 12 | -0.57% | -5.87% | -6.13% | **+0.31% [0.10, 0.51]** | -0.50% |
| BTC 1H (DVOL) | 24 | -0.26% | -3.72% | -3.90% | **+0.49% [0.33, 0.68]** | +0.13% |

- **Against the current engine (vs ATR14), the first pass found:**
  - ES 1H IV×clock (fresh VIX1D): +6.8% (H6), +4.6% (H12), +0.3% (H24);
  - NQ +3.1 to +4.0%; RTY +6.9%;
  - ES 5m -1.1 to -1.5%; BTC DVOL -5.3%.
  - Without any clock, the cheap blend `aU^0.5·IV^0.5` (stale) gains vs ATR14: ES 1H +4.5 to +5.0% (H6), +2.9 to +3.2% (H12); NQ +3.4%; RTY +5.4%; CL +1.3%; ES 5m +0.4 to +0.8%; BTC -0.3%.
- **GC void:** 519 bar-to-bar gaps > 3% in a year of hourly GC point to spliced contracts. Its numbers (also the first-pass GVZ rows) are not evidence. CL needed roll back-adjustment (6 gaps).
- **Reading:**
  - (a) The clock with a fast level does most of the work.
  - (b) IV adds level information the fast level lacks, mainly on index futures with the matching daily index (VIX1D/VIX9D) and on RTY.
  - (c) The right weight is 0.25 for 30-day indices on intraday horizons and 0.5 for VIX1D/VIX9D with fresh alignment.
  - (d) Stale alignment erases the gain.
  - (e) No positive effect is shown on ES 5m or NQ.

### 2.4 Alignment: the exact `[1]` + lookahead behaviour [T]
- For a chart bar at time t, `request.security(ivSym, "D", close[1], lookahead_on)` returns the close of the daily bar *before* the one containing t. An RTH-only index's daily bar opens at 09:30 ET, so:
  - from 16:15 on day D to 09:30 on D+1, the value is close(D-1), i.e. VIX1D's forecast for the day that just ended;
  - over a weekend, Thursday's close holds until Monday 09:30.
- **Costs [T]:**
  - ES 1H H6: VIX1D -3.7% (stale) vs -0.8% (fresh) relative to clkL50; vs ATR, +4.1% vs +6.8%.
  - Daily chart: VIX1D's 1-day edge falls from +5.4% to +0.9%.
- **Fix (X1-1):** request `[close[1], time_close[1]]` at `f_tfSafe("60")`. Latch the value when the closed bar's New York close time is 16:00-16:30, which is the session's last bar, i.e. the official close. This is non-repainting: confirmed history only, and `[1]` with lookahead.
- On daily charts the same call returns the prior daily bar (stale), hence VIX9D there.

### 2.5 VRP scale stability [T]
- Touch-fitted sd scale by year:
  - VIX: 1999 0.66, 2000 0.82, 2001 0.71, 2002 0.77, 2003-06 0.65-0.71, 2008 0.89, 2009-16 0.65-0.72, 2017 0.57, 2018 0.78, 2022 0.81, 2023-26 0.65-0.71;
  - VIX1D: 2022 0.85, 2023 0.79, 2024 0.86, 2025 0.82, 2026 0.85.
- **Intraday:** raw clock×IV PoT means 0.45-0.65 vs observed 0.38-0.52 (ES 1H). Fitted sd scales: VIX 0.68-0.72, VIX9D 0.73-0.77, VIX1D 0.84-0.88; NQ (VIX proxy) 0.90-0.94; BTC DVOL 0.73.
- So κ must be learned per symbol and IV source.

### 2.6 Term-structure state and calibration [T] (`x1_daily2.py` (c), `x1_regime.py`)

| Sample | VIX/VIX3M state | n rows | base rate | VIX sd scale | ATR sd scale |
|---|---|---|---|---|---|
| 2011-18 | < 0.90 | 12,150 | 0.225 | 0.62 | 0.64 |
| 2011-18 | 0.90-1.00 | 6,270 | 0.268 | 0.74 | 0.74 |
| 2011-18 | ≥ 1.00 | 1,680 | 0.329 | 0.87 | 0.91 |
| 2022-26 | < 0.90 | 6,410 | 0.220 | 0.64 | 0.62 |
| 2022-26 | 0.90-1.00 | 4,260 | 0.266 | 0.76 | 0.72 |
| 2022-26 | ≥ 1.00 | 540 | 0.326 | 0.93 | 0.92 |

- In backwardation both IV and trailing ATR under-forecast by about 1.4× in sd relative to contango.
- **OOS gain of a state-keyed scale** (2-fold, day-block CI), keying by VIX/VIX3M or VIX9D/VIX:
  - ATR model: +1.2% [0.6, 1.8] (2011-18, h1), +0.5-0.6% (2022-26, h1), +0.4-0.9% (h5);
  - IV model: +0.8-0.9% (2011-18, h1), +0.7% (VIX/VIX3M) to +1.6% [0.9, 2.5] (VIX9D/VIX) (2022-26, h1), +0.5-1.2% (h5).
- This is the only IV-family *state* signal that survived **[T]**.

### 2.7 Events [T] (`x1_events.py`, `x1_ext.py` B, `x1_evredis.py`, `x1_daily2.py` (d), (f))
- **Event dates:** typed from the public Fed/BLS calendars. FOMC 2022-26; CPI and NFP 2022-01..2025-09 (the 2025-26 shutdown-shifted dates are excluded).
- **Detector AUC** (2022-05..2025-09, n = 103 event eves): log(VIX1D/VIX) 0.870 (FOMC 0.855, CPI 0.840, NFP 0.829); log(VIX9D/VIX) 0.664; day-before change in log VIX1D 0.877.
- **Thresholds:**

| Rule (known at the prior close) | Period | flags | precision* | recall |
|---|---|---|---|---|
| raw log(VIX1D/VIX) ≥ 0 | 2022-05..2025-09 | 154 | 0.46 | 0.69 |
| raw ≥ 0 | 2022-06..2023-12 / 2024-01..2025-09 | 82 / 71 | 0.45 / 0.46 | 0.79 / **0.60** |
| z = log ratio - median20 ≥ 0.20 | 2022-06..2023-12 / 2024-01..2025-09 | 57 / 87 | 0.58 / 0.45 | 0.70 / 0.71 |
| z ≥ 0.10 | 2022-05..2025-09 | 243 | 0.35 | 0.83 |
| raw ≥ 0, ES-1H window 2025-03..2026-03 | 259 days | 32 | | **6/20** |
| z ≥ 0.10 / ≥ 0.20, same window | 259 days | 78 / 48 | | 13/20 / 9/20 |

  \*Precision counts only FOMC/CPI/NFP. Flags on PPI, retail sales, GDP, PCE, ISM, mega-cap earnings and tariff dates count as "false", so the true precision for "some catalyst" is higher.
- **Day-level variance on event days** (SPX, log ratio realised/forecast, event vs normal):
  - FOMC ×2.16 vs 22-day RV (σ ×1.47), ×1.98 vs VIX, **×1.08 vs VIX1D**;
  - CPI ×2.05 / ×1.97 / **×1.06**;
  - NFP ×2.04 / ×1.89 / **×1.15**.
- **EM band on event days** (1-day, prior close ± IV):
  - VIX band touched on 57% of event days vs 31% of other days (close beyond 38% vs 19%);
  - VIX1D band 52% vs 46% (close beyond 31% vs 28%). VIX1D is event-aware; VIX is not.
- **Hourly concentration (ES 1H, 2025-03..2026-04):** 08:30 CPI/NFP bar variance ×3.87 vs the same hour on non-event days (median ×6.7, n = 12); FOMC 14:00 bar ×4.75 (median ×8.0, n = 8).
- **Event-hour multiplier m (variance) on the release bar:** log-loss on rows whose forward window contains the release.

| Level | Rule | H=6 event window | H=6 rest of event day | H=6 all | H=12 event window |
|---|---|---|---|---|---|
| L50 (realised) | none | 0.6504 | 0.4911 | 0.5104 | 0.6145 |
| L50 | add m=4 / m=7 | 0.6138 / **0.6009** | 0.4912 / 0.4912 | 0.5096 / 0.5094 | 0.5959 / **0.5875** |
| L50 | redistribute m=7 | 0.6052 | 0.5008 (worse) | 0.5099 | 0.5918 |
| VIX1D fresh | none | 0.5809 | 0.5389 | 0.5143 | 0.5682 |
| VIX1D fresh | add m=4 | 0.5711 | 0.5388 | 0.5142 | 0.5640 |
| VIX1D fresh | **redistribute m=7** | 0.5712 | **0.5293** | **0.5132** | **0.5621** |
| L50^0.5·VIX1D^0.5 | add m=7 / redistribute m=7 | 0.5786 / 0.5787 | 0.5042 / 0.5033 | 0.5072 / **0.5068** | 0.5682 / 0.5681 |

- **Detector-driven bumps** (applied at 08:30 on detector days, no calendar):
  - with L50 they hurt (rows on detector days without a true event: 0.5395 → 0.5503 at m=4);
  - with IV levels they helped a little, likely because the "false" flags are real but unlisted 08:30 releases.

### 2.8 Calendar effects [T] (`x1_events.py` §4: SPX 1999-2018 + 2022-26; `opex_cycle.py`: SPX and Nasdaq weekly 1999-2018)
- **Daily variance vs a 22-day RV forecast (×, 95% CI):**

| Day type | Result | n |
|---|---|---|
| Monthly OPEX Friday | ×0.86 [0.76, 0.99] | 194 |
| Triple witching | ×0.81 [0.69, 0.94] | 97 |
| First trading day of the month | **×1.31 [1.19, 1.45]** | 299 |
| Second trading day | ×0.98 | |
| Month-end | ×0.98 | |
| Quarter-end | ×0.92 [0.78, 1.08] | |
| Monday | ×0.89 [0.84, 0.94] | |
| Non-OPEX Friday | ×1.00 | |
| Russell reconstitution Friday | ×1.25 [0.90, 1.80] | 25 |
| Monday after OPEX | ×0.93 [0.84, 1.03] | |

  Versus VIX the factors are nearly identical, so VIX does not price these.
- **Weekly (opex_cycle):**
  - weekly range / 20-week mean: OPEX week 1.06 (t +0.3); the week after a monthly OPEX 0.97 (t -1.9). No "window of weakness";
  - OPEX Friday daily range 0.93 vs 1.01 on other Fridays (SPX, t -2.5) and 0.89 vs 0.99 (Nasdaq, t -3.1);
  - P(the prior week's high is taken first): no OPEX effect (±4-6 pp CIs).
- **Max-pain null:** the Friday close lands within 0.5% of the 25-point strike nearest Monday's open on 20.0% of OPEX weeks vs 20.3% of other weeks (SPX); 16.2% vs 14.1% (Nasdaq, 50-point strikes). There is no open-interest data, so this only bounds crude pinning claims.

### 2.9 Expected-move bands vs ADR and the noise area [T]

| Band (SPX) | Either side touched | Close beyond (either) | Close inside |
|---|---|---|---|
| 1-day ±σ(VIX), prior close, 1999-2018 | 0.327 (up 0.148, down 0.181, both 0.002) | 0.203 | 0.797 |
| 1-day ±σ(VIX), 2022-26 | 0.326 | 0.197 | 0.803 |
| 1-day ±σ(VIX9D), 2022-26 | 0.377 | 0.218 | 0.782 |
| 1-day ±σ(VIX1D), 2022-26 | 0.474 | 0.271 | 0.729 |
| same, open-anchored: VIX / VIX9D / VIX1D (2022-26) | 0.194 / 0.227 / 0.319 | | |
| open ± 1.0 × ADR14 (1999-2018 / 2022-26) | 0.293 / 0.257 | | |
| open ± 0.5 × ADR14 | 0.759 / 0.748 | | |
| open ± 1.0 × noise14 (mean \|C-O\|) | 0.683 / 0.722 | | |
| weekly ±VIX·√(5/252), Friday close (1999-2018 / 2022-26) | 0.319 / 0.366 | 0.178 / 0.207 | 0.82 / 0.79 |
| Brownian with exact σ | ≈ 0.63 (either), 0.317 one side | 0.317 | 0.683 |

- **Reading:**
  - ±1σ(IV) bands are touched on one side on about 15-24% of days. They are wider than a fair 1σ (VRP) and comparable to a full ADR band.
  - The noise area is much tighter: it is the "normal day" box, not a stretch boundary.
  - session_stats §2.7 already refuted ADR-remaining caps. EM bands are context, not caps.

### 2.10 Status of the sibling claims on this topic
- **quant_regime** ("index-specific, monthly horizon; not generic"): **corrected.**
  - The effect is real at 1-day horizons (+3 to +5% with VIX1D/VIX9D) and on intraday index futures.
  - It is small (+0.3 to +1.6%) once TIME-3's clock and fast level exist.
  - It is generic enough through root mapping (indices, oil, BTC). Unmapped symbols fall back cleanly.
- **quant_pot** ("IV-based touch odds run high"): **confirmed and quantified** (§2.2, §2.5).
- **ict_time TIME-8 / asset_specific ASSET-5** (σ ×2 at events; manual lists): **supported.**
  - Variance ×4 is conservative against the measured ×3.9-4.8 mean and ×6.7-8 median; m=7 was best in the grid.
  - The add/redistribute rule (§2.7) is needed once an implied level is used.

---

## 3. Engine gap analysis (line refs in baseline_v2.pine)

| # | Concept | Status | Lines | What the engine does / what differs |
|---|---|---|---|---|
| G1 | Implied-vol feed | **missing** | 923-925, 939, 981-982 (the only requests) | No IV request. Budget: 6 of 40 used |
| G2 | Forward σ for PoT | **partial / wrong form** | 916 `potSig = ta.stdev(chg, potLen)`; 917 `potMu`; 432-445 `f_pot`; 1303-1311 `f_potModel`; 1314-1322 `f_potBase`; 1343-1364 race; 661-667 `evaluate` reach (σ passed at 1948); 2066-2067 live PoT | Trailing 50-bar σ of price changes: time-blind, horizon-blind and backward-looking. It was the worst model in every test (§2.2: -3.7 to -4.7% vs ATR14 at daily; §2.3: rv-type σ -1.2 to -3.7% vs ATR14 intraday) |
| G3 | Empirical surface unit | **partial** | 1284-1300 `f_empPoT`; bump 1527-1532 (`/ aH`, aH = `atr[H]`); query `d / atr` 1307, 1318 | ATR14 unit, rows by htfBias. No clock, no IV, no term-structure state |
| G4 | Horizon | **partial** | 183 `potH`, 305 `H` | Fixed bars. Variance per bar assumed constant; no event or calendar awareness |
| G5 | VRP scaling | **n/a → missing with G1** | none | |
| G6 | Term-structure state | **missing** | none | §2.6 shows +0.4 to +1.6% |
| G7 | Scheduled events | **missing** | none (no calendar, no flag) | TIME-8 / ASSET-5 propose manual lists; no implied cross-check |
| G8 | Event-day variance premium | **missing** | none | Event windows' log-loss is 5-8% worse than with event-aware variance (§2.7) |
| G9 | Expected-move band | **missing** (partial analogue) | 173 `showReach`; 2112-2115 reach bands (`f_reachD`, 1325-1338) | Reach bands are the historical median/80th-percentile excursion in ATR units, not forward-looking |
| G10 | Options-implied PoT benchmark | **missing** | Trial 375-395 stores `pBase` only; `f_openTrial` 1426-1431 | No graded displayed PoT (QPOT-04 adds `pPot`) and no external benchmark |
| G11 | Proper-score gating | **missing** | `f_calMult` 1376-1384 (hit/expected ratio, not a proper score); `f_raceAdj` 1367-1371 | No log-loss/Brier per model. TIME-4 probes and QPOT-04 add them; X1-1's w must be gated by them |
| G12 | Calendar variance (OPEX, TOM) | **missing** | none | Small effects (§2.8); belongs in TIME-3's day factors |
| G13 | Earnings | **missing** | none | Stocks only (`earnings.future_time`) |
| G14 | Option pinning / max pain as a target | **missing (correctly)** | none | Null (§2.8); do not add |
| G15 | Killzone hysteresis as a time proxy | **partial** | 976 `hystEff` | Binary off-killzone widening; TIME-5 replaces it with forward variance. X1-2's event-aware variance feeds the same quantity |
| G16 | Cap | present | 444 `math.min(0.95, …)` | Raw IV PoT would breach it; irrelevant once scaled |

---

## 4. Proposals (spec level; best first)

Shared notation:
- `L` is TIME-3's fast level (`clkLf`, per-bar variance at an average bucket); `v(h)` is TIME-3's clock-share walk (`f_fwdVar` before the level).
- Every number shown to users stays confirmed-bar and non-repainting. The IV values enter only through `[1]`-offset requests with `lookahead_on`.

### X1-1 (P1, M) · Implied-level blend in the forward variance: root mapping, fresh alignment, unit-preserving κ, and w gated by the ledger's proper scores

**Why.**
- Gains vs the TIME-3 level: ES 1H +0.5-0.6%, RTY 1H +1.3-1.6%, CL 1H +0.5%, BTC 1H +0.3-0.5% (all CIs exclude 0).
- Gains vs the current engine: 1H index futures +2.5 to +6.8%; at daily horizons +2.5 to +5.4% vs ATR14.
- The evidence is strong at daily horizons and moderate intraday.
- With no IV for the symbol, it is a clean no-op.

**Inputs** (G_POT, after line 188, `display = display.none`):
```pine
string ivMode = input.string("Auto", "Implied Vol Feed", options = ["Auto", "Custom", "Off"], group = G_POT, display = display.none,
  tooltip = "Auto maps index futures/ETFs/cash indices, crude, gold and BTC to their options-implied volatility index (VIX1D / VIX9D / VIX, VXN, RVX, VXD, OVX, GVZ, DVOL). Blended into PoT only where it scores better than the realised model on this chart.")
string ivCust = input.symbol("", "Custom IV Symbol", group = G_POT, display = display.none)
string ivWIn  = input.string("Auto", "Implied Weight", options = ["Auto", "0", "0.25", "0.5"], group = G_POT, display = display.none)
```

**Mapping** (PURE HELPERS, before 610). It returns simple values because `syminfo.*` and H are simple:
```pine
f_ivMap(float hDays) =>
    string r = syminfo.root, string t = syminfo.ticker, string bc = syminfo.basecurrency
    bool spx = r == "ES" or r == "MES" or t == "SPX" or t == "SPY" or t == "US500" or t == "SPX500USD"
    string s = spx ? (timeframe.isintraday and hDays <= 1.5 ? "CBOE:VIX1D" : hDays <= 9.0 ? "CBOE:VIX9D" : "CBOE:VIX") :
       (r == "NQ" or r == "MNQ" or t == "NDX" or t == "QQQ" or t == "US100" or t == "NAS100USD") ? "CBOE:VXN" :
       (r == "RTY" or r == "M2K" or t == "RUT" or t == "IWM" or t == "US2000") ? "CBOE:RVX" :
       (r == "YM" or r == "MYM" or t == "DJI" or t == "DIA" or t == "US30") ? "CBOE:VXD" :
       (r == "CL" or r == "MCL" or t == "USO" or t == "USOIL" or t == "WTI") ? "CBOE:OVX" :
       (r == "GC" or r == "MGC" or t == "GLD" or t == "XAUUSD") ? "CBOE:GVZ" :
       bc == "BTC" ? "DERIBIT:DVOL" : ""
    [s, bc == "BTC" ? 365.0 : 252.0, bc != "BTC"]   // [symbol, annualisation, RTH-latched?]
```
- The comma-separated declarations above are shorthand. Write one declaration per line in the real code.
- `hDays = H * chartS / 86400.0`.
- Daily-and-above charts never get VIX1D: on those charts the latched value is one day stale (§2.4), and VIX9D tolerates that.

**Series** (after 939; one request, deduplicated with X1-3/X1-4 when they ask for the same symbol):
```pine
[ivMapS, ivAnn, ivRth] = f_ivMap(H * chartS / 86400.0)
string ivSym = ivMode == "Off" ? "" : ivMode == "Custom" ? ivCust : ivMapS
bool   ivOn  = ivSym != ""
[ivC1, ivTc1] = request.security(ivOn ? ivSym : syminfo.tickerid, f_tfSafe("60"), [close[1], time_close[1]],
     lookahead = barmerge.lookahead_on, ignore_invalid_symbol = true)
var float ivDay = na
if ivOn and not na(ivC1) and ivC1 > 0 and not na(ivTc1)
    int mc = hour(ivTc1, "America/New_York") * 60 + minute(ivTc1, "America/New_York")
    if not ivRth or (mc >= 960 and mc <= 990)    // RTH index: latch only the session's last bar (official 16:15 close)
        ivDay := ivC1
float ivVar = ivOn and not na(ivDay) ? math.pow(ivDay / 100.0, 2) / ivAnn : na   // per-day variance
```
- The latch updates as soon as the 16:00-16:15 IV bar is confirmed. That is the "fresh" alignment tested in §2.3-2.4.
- Never use intraday VIX1D prints (§1.8): the latch ignores them by construction.

**Unit-preserving κ and the blend** (inside TIME-3's learning block, once per new `ivDay`):
```pine
var float ivK = na     // slow EWMA of L·bpd / ivVar, half-life ≈ 250 trading days, cumulative-mean warm start
var int   ivN = 0
if ivOn and not na(ivVar) and ivVar > 0 and ta.change(ivDay) != 0 and not na(clkLf)
    ivN += 1
    float rK = clkLf * bpdEst / ivVar          // bpdEst: learned bars per trading day (TIME-3 open-cell count / clkDy)
    ivK := na(ivK) ? rK : ivK + math.max(1.0 / ivN, 1.0 - math.pow(0.5, 1.0 / 250.0)) * (rK - ivK)
float wIv  = not ivOn or na(ivK) ? 0.0 : ivWIn == "Auto" ? ivWAuto : str.tonumber(ivWIn)
float Liv  = na(ivK) ? na : ivK * ivVar / bpdEst                          // IV in per-bar realised units
float Lb   = wIv > 0 and not na(Liv) ? math.pow(clkLf, 1.0 - wIv) * math.pow(Liv, wIv) : clkLf
// TIME-3: fwdV = v(H) · Lb   (replaces v(H) · clkLf); fwdSd / sigH as in TIME-3 / QPOT-02
```
- `ivK` is learned from confirmed bars only.
- The blend never changes the mean level, so the empirical z-surface and the analytic prior keep their calibration.

**Without TIME-3** (fallback; cheaper; tested in §2.3):
- Surface unit = `aU^(1-w)·(κa·close·√(ivVar/bpdEst))^w`, with κa a slow EWMA of `aU/(close·√(ivVar/bpdEst))`.
- Queries in `f_potModel` (1307) and `f_potBase` (1318) use `d / unit`.
- Step 0 (1527-1532) bumps with `unit[H]`.
- Analytic σ (1304, 1360) = `unit/√…` is consistent.

**Gating by proper scores** (`ivWAuto`):
- Add the candidates w ∈ {0, 0.25, 0.5} to TIME-4's probe scorecard: 6 probes per bar at k = 1, 2, 3 ATR × side, PoT under each model, resolved after H bars, 2H-block clustered log-loss differences.
- Daily selection: the lowest log-loss among candidates with ≥ 2,000 resolved probe bars and z ≤ -2 vs w = 0; otherwise 0. Hold the choice at least 5 days.
- If TIME-4 is not built, run the same probe loop with just these 3 candidates. Memory is (H+1)·6·3 floats.
- Ledger: QPOT-04's `pPot` grading then shows the displayed-PoT effect on real DOL trials.

**Display:**
- Terminal PoT row: `PoT 61% · σ CLOCK+IV(VIX1D .25)`.
- Clean style: tooltip line `σ: realised + implied (VIX1D, w .25)`.

**Risk:**
- **Holidays:** RTH-close latch on half days at 13:15. Add a second latch window 13:00-13:30 when no 16:15 bar exists that day; otherwise the value stays stale one day, which is harmless.
- **CBOE data permissions:** delayed data is fine; with an invalid symbol, `ignore_invalid_symbol` makes w = 0.
- **NQ/ES 5m show no gain:** the gate will keep w = 0 there.
- **Proxy-only evidence:** VXN, RVX and VXD were not tested natively.

**Effort:** M (the mapping and latch are S; wiring into TIME-3/REG-2 and the scorecard is M).

### X1-2 (P1, S) · Event-aware horizon variance: release-bar multipliers with the add vs redistribute rule

**Why.**
- Event windows' touch log-loss improves by 4.8-7.6% (§2.7).
- Without this, an implied level double-counts: VIX1D already holds the event day's variance.

**Builds on** TIME-8 (manual event plus NFP rule) and ASSET-5 (asset-aware lists, σ multipliers). This proposal fixes the variance algebra; their lists and UI stay.

**Spec** (inside TIME-3's `f_fwdVar` walk). For each future bucket j with projected start time t_j and share s_j:
- If an event time `evT ∈ [t_j, t_j + bucket)`: factor `m` (variance).
  - Defaults: tier-1 08:30 (CPI/NFP) and FOMC 14:00 m = 4.0 (σ ×2, ASSET-5's value). Allowed range 1-8.
  - Evidence: measured mean ×3.9/×4.8 and median ×6.7/×8.0; m = 7 best in the grid.
- If t_j is on the event's trading day but not in the release bucket: factor `1 - wIv·(m - 1)·s_e/(S_day - s_e)`, clipped to [0.2, 1].
  - s_e is the release bucket's share; S_day the day's total share (both from clkA·clkD, computed once per bar when an event day is inside the horizon).
  - wIv = 0 (realised level): pure *add*.
  - wIv = 1 (pure implied level): pure *redistribute*, preserving the day total.
  - In between: blend.
- **Charts ≤ 15m:** spread the release-bucket factor over `[evT, evT + evMin)` as in TIME-8, total extra variance `(m-1)·s_hour`.
- **Post-event decay** (optional): after the release, the remaining event-day buckets are not reduced further. The IV latch refreshes at the next close.

**Pine notes:**
- O(number of walk steps); no new request.
- Event timestamps come from ASSET-5's parsed arrays (`fomcT`, `evT`).

**Ledger:** ASSET-5's `t.news` split shows event-window HIT/EDGE. TIME-4 probes falling in event windows can be scored separately (`PoT CAL news`).

**Evidence:** strong (mechanism: Ederington & Lee; Lee 2012); moderate (magnitudes, ES n = 20).

**Risk:**
- Wrong or stale dates (ASSET-5's lists must be user-maintained).
- Small n behind m.
- The rule assumes the learned clock already contains average event days (true for TIME-3).

**Effort:** S on top of TIME-3/TIME-8.

### X1-3 (P2, S-M) · Term-structure state for PoT calibration (VIX9D/VIX or VIX/VIX3M)

**Why.**
- +0.4 to +1.6% log-loss out of sample for both ATR-unit and IV-unit models, replicated in two disjoint periods (§2.6).
- Backwardation days are where trailing σ and IV both under-reach (sd scale ×1.4).

**Spec:**
- Two extra requests (deduplicated with X1-1/X1-4), same latch as X1-1: `CBOE:VIX` and `CBOE:VIX9D`, or `CBOE:VIX3M`.
- `tsR = vix9Day / vixDay`, states `0: < 0.95`, `1: 0.95-1.05`, `2: ≥ 1.05`. For VIX/VIX3M use 0.90 / 1.00.
- Offer it as a state key in QPOT-03's surface (`potKey` option "Term structure"): 3 rows plus the pooled row, partial pooling `w = n/(n + 40)` toward the pooled surface (the same code path as QPOT-03's "Vol state").
- The bump uses `tsState[H]` (a series, so the `[H]` history is valid).
- **Simpler alternative:** a per-state σ multiplier learned from TIME-4 probes, `c_s = √(EWMA over resolved probes of z²_realised / z²_forecast)`, clipped to [0.8, 1.6].
- Applies to US-index-linked symbols by default. For other symbols it is offered to the scorecard only (untested).

**Display:** Terminal regime row `TERM ▲ BACKWARDATION` (red) / `CONTANGO`.

**Evidence:** moderate (own OOS; mechanism: Johnson 2017).

**Risk:**
- Backwardation is rare (5-8% of days), so those cells are thin and need pooling.
- Index-specific.
- Two extra requests (total 9-10 of 40).

**Effort:** S-M.

### X1-4 (P2, S) · Options-implied event flag (cross-check for the manual calendar)

**Why.**
- The calendar is fragile: shutdown shifts, Fed revisions (asset_specific H2).
- The options market prices tomorrow's event at the 16:15 close: AUC 0.87.
- A relative detector catches 70% (2022-25), but only 45-65% in 2025-26. It is a check, not a source.

**Spec:**
- On each new latched VIX1D and VIX close (X1-1 latch; requests deduplicated), push `lr = math.log(v1d/vix)` into `array<float> tsHist` (size 21).
- `zEv = lr - array.median(prior 20)`; `evLikely = zEv >= 0.20`.
- If `evLikely` and no ASSET-5 entry falls in the next session:
  - HUD and Clean tooltip: `⚑ Options price an event next session (VIX1D/VIX +0.31 vs norm)`;
  - optional `alert()` "Implied event not in calendar".
- If an entry exists and `zEv < 0`: tooltip note `calendar event, options calm`.
- **No variance change** from the detector alone: detector-driven bumps hurt with realised levels (§2.7). With an implied level the day variance is already in VIX1D.
- Available for all USD-linked symbols; it uses SPX options as the macro barometer.

**Evidence:** moderate.

**Risk:** regime-dependent recall; false flags on unlisted releases (which are useful anyway).

**Effort:** S.

### X1-5 (P2, S) · Expected-move band (display)

**Why.**
- Traders reason with "expected move".
- A forward-looking companion to the historical reach bands, with honest measured coverage in the tooltip.
- It is not a target source: EM edges are not liquidity.

**Inputs:** `emShow = input.string("Off", "Expected Move Band", options = ["Off", "Day", "Week"], group = G_DOL, display = display.none)`.

**Spec:**
- On each new latched `ivDay` (Day mode): `emAnchor := close` (the chart close at the latch bar, i.e. at the IV measurement) and `emBar := bar_index`.
- `em = emAnchor * ivDay/100 / math.sqrt(ivAnn)`. This is raw, by market convention.
- Week mode: on the Friday latch, VIX/VXN/… (30-day index, not VIX1D) × √5.
- Two dotted lines from `emBar` to `bar_index + extBars` at `emAnchor ± em`, plus a tiny right label `EM ±0.9%`.
- Delete the previous pair (2 lines, 1 label).
- Tooltip: `±1σ options-implied move (not a target). SPX history: one side touched ~15-24% of days, close beyond ~20-27%.`
- Clean style: hidden unless enabled, so the reference look is untouched.

**Evidence:** moderate (§2.9).

**Risk:** clutter (default Off); misread as targets (the tooltip states otherwise).

**Effort:** S.

### X1-6 (P3, S) · Options-implied PoT graded as an external benchmark

**Why.**
- It gives users an external yardstick: "the options market says 48%".
- It shows on their own chart that raw options odds overstate touches (§2.2), and whether the engine beats them.

**Spec:**
- `pIV = f_erfc(d / (math.sqrt(2.0) * close * math.sqrt(v(H) * ivVar / bpdEst)))`, raw (no κ). The `v(H)` clock share comes from TIME-3, or `H·chartS/86400`-based without it.
- Trial gets `float pIV = na`, set in `f_openTrial` (1426).
- `f_book` (1461) adds Σ log-loss for `pIV` next to QPOT-04's `pPot`.
- Panel (Full): `PoT vs OPTIONS  LL .58 vs .63 · opt. mean 47% vs obs 33% (n 140)`.
- Tooltip: `options-implied touch ≈ 48% (raw, typically high)`.

**Evidence:** moderate. **Risk:** users mistaking it for the engine's PoT (label clearly). **Effort:** S (needs QPOT-04).

### X1-7 (P3, S) · Calendar variance cells in the clock (turn of month, OPEX Friday)

**Why.**
- Small but reliable daily-variance shifts that VIX does not price: first trading day of the month ×1.31 [1.19, 1.45] (σ ×1.14), monthly OPEX Friday ×0.86, triple witching ×0.81 (σ ×0.93 / ×0.90).
- They also dispel the OPEX folklore: no post-OPEX range expansion, no pinning signal (§2.8).

**Spec:**
- In TIME-3's day factor add `clkT[3]` (normal / TOM1 / OPEX-Fri), learned like `clkD` (additive EWMA, cumulative-mean warm start, floors), using `time_tradingday`:
  - `tom1 = month(time_tradingday, tz) != month(time_tradingday[1], tz)` on the first bar of a trading day;
  - `int dom = dayofmonth(time_tradingday, tz)`, then `opex = dayofweek(time_tradingday, tz) == dayofweek.friday and dom >= 15 and dom <= 21`.
- Shrink toward 1 with `n/(n + 20)` days.
- Index-linked symbols by default; the scorecard decides elsewhere.

**Evidence:** moderate (n = 97-299 days, two eras). **Risk:** thin cells; the ISM 10:00 release confounds TOM (harmless for variance). **Effort:** S.

### X1-8 (P3, M) · Earnings-aware variance for stocks

**Why.**
- Earnings sessions carry several times normal variance (Dubinsky et al. 2019).
- A stock DOL taken "through" earnings is a news gap, not a raid.
- Options price about 1/0.85 of the realised move (ORATS).

**Spec:**
- Live: `ne = earnings.future_time`. If `ne` falls inside the horizon, the reaction session (the next session if the report is after the close) gets variance factor `mE` in the walk (X1-2's add rule; no IV for stocks).
- `mE` is learned per symbol from history: `request.earnings(syminfo.tickerid, earnings.actual, barmerge.gaps_on, barmerge.lookahead_on)` marks past report bars (one request).
- At each report, take the ratio (reaction-session range²)/(median range² of the prior 20 sessions). EWMA over the last 8 reports, floored at 1, capped at 25.
- HUD `⚑ EARNINGS in 2d`.
- Ledger: `t.news` (ASSET-5) for trials whose horizon spans a report.

**Evidence:** strong for the existence of the effect; size per symbol learned. **Risk:** report-timing (BMO/AMC) ambiguity; one extra request. **Effort:** M.

### Not proposed (and why)
- **IV percentile or VIX level as a draw/bias input:** monthly-horizon return predictability (VRP, Bollerslev et al.) has no tested link to which pool is taken next.
- **VVIX as a tail state:** untested here.
- **Max pain or option walls as targets:** no open-interest data in Pine; the crude null shows nothing (§2.8).
- **Beta-scaled VIX for stocks:** ratio modulation lost (§1.4).
- **MOVE for Treasury futures:** unit mismatch.
- **Replacing the calendar with the detector:** recall is 45-71%.
- **ADR-remaining caps from the EM:** refuted in session_stats §2.7.

---

## 5. Recommended build order and interactions
1. TIME-3 (clock + fast level). It is the bigger win; IV is an add-on.
2. TIME-4 / QPOT-04 scoring (needed to gate w).
3. **X1-1** (feed, latch, κ, w candidates); **X1-2** with TIME-8/ASSET-5.
4. **X1-3** (state key, with QPOT-03), **X1-4** (flag), **X1-5** (band).
5. X1-6, X1-7, X1-8.

Without TIME-3, X1-1's fallback (aU × IV blend) still gives +2 to +5% on 1H index futures vs today's ATR unit, gated the same way.

Request budget after all: 6 now, plus 1 (IV feed), plus up to 2 (VIX, VIX9D/VIX3M), plus 1 (VIX1D for the detector when the chart is not SPX-linked), plus 1 (earnings): ≤ 11 of 40.

---

## 6. Test inventory (all under study/x1_tools; run with `run.sh <script>`, which uses an isolated Python with the local wheels in `x1_tools/pylib`)

| Script | Output | What |
|---|---|---|
| `x1_common.py` | | loaders, `pot2` (driftless touch), log-loss, 2-fold OOS scale fit, day-block bootstrap |
| `x1_daily.py` | `out_daily.txt` | SPX daily: MZ, HAR/HAR-IV, touch panels h = 1, 5 (VIX, VIX9D, VIX3M, VIX1D), raw IV calibration, EM bands |
| `x1_daily2.py` | `out_daily2.txt` | lagged-IV cost on daily charts, VRP scale by year, scale by term-structure state, EM band on event days, weekly EM band, relative detector by period |
| `x1_regime.py` | `out_regime.txt` | OOS gain of a term-structure-keyed scale; detector on the ES-1H window |
| `x1_intraday.py` | `out_intraday_1h/5m/btc/cl/extra.txt` | first pass: IV × clock vs ATR / slow RV on CME 1H, 5m, BTC (GC rows void) |
| `x1_ext.py` | `out_ext_A.txt`, `out_ext_B.txt`, `out_ext_btc.txt` | second pass: IV vs TIME-3-like fast level with three alignments; event-bar variance and multipliers |
| `x1_evredis.py` | `out_evredis.txt` | add vs redistribute event variance by level type |
| `x1_events.py` | `out_events.txt` | term-structure detector AUC, event-day variance vs RV/VIX/VIX1D, VIX1D shape, calendar effects |
| `opex_cycle.py` | `out_opex_cycle.txt` | OPEX weekly cycle, P(PWH first), max-pain null (SPX and Nasdaq 1999-2018) |

Data:
- `x1_iv_data/` (Cboe daily history CSVs: VIX, VIX1D, VIX9D, VIX3M, VVIX, SKEW, OVX, GVZ; Deribit DVOL; SPX 2021-26 `spx1/spx3`, cross-checked to 1e-8; `spx2`/`spx4` unused, `spx4` looks wrong);
- `bias_data/sp500.csv`, `nasdaq.csv` (1999-2018);
- `amt_data/cme/*` (1H/5m CME; GC unreliable);
- `session_data/btc_1h.pkl`.
- The Cboe CDN is now blocked by the session's network policy (403), so VXN, RVX and VXD could not be added.

---

## 7. Sources
- Poon, S.-H., Granger, C. (2003). Forecasting Volatility in Financial Markets: A Review. JEL 41(2), 478-539. https://econpapers.repec.org/RePEc:aea:jeclit:v:41:y:2003:i:2:p:478-539 ; Practical issues in forecasting volatility, FAJ 2005: https://rpc.cfainstitute.org/research/financial-analysts-journal/2005/practical-issues-in-forecasting-volatility
- Christensen, B. J., Prabhala, N. R. (1998). The relation between implied and realized volatility. JFE 50(2), 125-150. https://www.researchgate.net/publication/222305915_The_relation_between_implied_and_realized_volatility
- Blair, B., Poon, S.-H., Taylor, S. (2001). Forecasting S&P 100 volatility: the incremental information content of implied volatilities and high-frequency index returns. J. Econometrics 105, 5-26. https://research.manchester.ac.uk/en/publications/forecasting-sampp-100-volatility-the-incremental-information-cont/
- Busch, T., Christensen, B. J., Nielsen, M. Ø. (2011). The role of implied volatility in forecasting future realized volatility and jumps in foreign exchange, stock, and bond markets. J. Econometrics 160(1), 48-57. https://econpapers.repec.org/article/eeeeconom/v_3a160_3ay_3a2011_3ai_3a1_3ap_3a48-57.htm
- Becker, R., Clements, A., White, S. (2007). Does implied volatility provide any information beyond that captured in model-based volatility forecasts? JBF 31(8), 2535-2549. https://ideas.repec.org/a/eee/jbfina/v31y2007i8p2535-2549.html
- Corsi, F. (2009). A simple approximate long-memory model of realized volatility. J. Fin. Econometrics 7(2).
- Albers, S. (2025). A New Star Is Born: Does the VIX1D Render Common Volatility Forecasting Models for the US Equity Market Obsolete? J. Futures Markets 45(11), 2092-2108. https://onlinelibrary.wiley.com/doi/full/10.1002/fut.70023
- Zhang, Ruan, Zhang (2023). Do short-term market swings improve realized volatility forecasts? FRL 58, 104629. https://scholar.xjtlu.edu.cn/en/publications/do-short-term-market-swings-improve-realized-volatility-forecasts/
- The daily rise and fall of the VIX1D: causes and solutions of its overnight bias (summary): https://github.com/chanmainvest/paper_library/blob/main/papers/the-daily-rise-and-fall-of-the-vix1d-causes-and-solutions-of-its-overnight-bias/index.md
- Cboe, What the VIX and VIX1D indices attempt to measure: https://www.cboe.com/insights/posts/what-the-vix-and-vix-1-d-indices-attempt-to-measure-and-how-they-differ ; VIX1D vs VIX in 11 charts: https://www.cboe.com/insights/posts/how-the-vix-1-d-index-performance-compares-to-the-vix-index-and-other-volatility-indices-in-11-charts
- Carr, P., Wu, L. (2009). Variance risk premiums. RFS 22(3), 1311-1341. https://engineering.nyu.edu/sites/default/files/2019-01/CarrReviewofFinStudiesMarch2009-a.pdf
- Johnson, T. L. (2017). Risk premia and the VIX term structure. JFQA 52(6), 2461-2490. https://www.cambridge.org/core/journals/journal-of-financial-and-quantitative-analysis/article/abs/risk-premia-and-the-vix-term-structure/56572D1F060448571BD8F597C732D9C3
- Dubinsky, A., Johannes, M., Kaeck, A., Seeger, N. (2019). Option pricing of earnings announcement risks. RFS 32(2), 646-687. https://econpapers.repec.org/RePEc:oup:rfinst:v:32:y:2019:i:2:p:646-687.
- Ederington, L., Lee, J. H. (1993). How markets process information: news releases and volatility. J. Finance 48(4); (1996) The creation and resolution of market uncertainty: the impact of information releases on implied volatility. JFQA 31(4).
- Lee, S. S. (2012). Jumps and information flow in financial markets. RFS 25(2).
- FRBSF WP 2019-12 (monetary policy uncertainty around FOMC): https://www.frbsf.org/wp-content/uploads/wp2019-12.pdf
- Golez, B., Jackwerth, J. (2012). Pinning in the S&P 500 futures. JFE 106(3). Whelan (AEA 2025): https://www.aeaweb.org/conference/2025/program/paper/N7rsBN2N
- tastylive: Testing probability of touch (11/22/2016): https://www.tastylive.com/shows/options-jive/episodes/testing-probability-of-touch-11-22-2016 ; Probability of touch, realistic expectations: https://tastylive.com/shows/market-measures/episodes/probability-of-touch-realistic-expectations-04-08-2016 ; put vs call POT: https://www.tastylive.com/news-insights/probability-touch-pot-put-vs-call-options ; weekly expected move (06/10/2024): https://tastylive.com/shows/market-measures/episodes/what-does-the-weekly-expected-move-tell-us-06-10-2024
- FlashAlpha, 0DTE straddles, 193 SPY sessions: https://flashalpha.com/articles/are-0dte-straddles-overpriced-193-spy-sessions-data-study
- ORATS, earnings moves (actual/implied ≈ 85%): https://orats.com/blog/the-wildest-earnings-week-on-record ; https://orats.com/blog/earnings-volatility-drop-knowable-in-advance
- TradingView symbols: CBOE:VIX1D https://www.tradingview.com/symbols/CBOE-VIX1D ; TVC:MOVE https://www.tradingview.com/symbols/TVC-MOVE ; DERIBIT:DVOL https://www.tradingview.com/chart/DVOL ; Cboe data on TradingView (delayed for all, real-time paid): https://www.tradingview.com/blog/en/improved-cboe-data-37524
- Deribit DVOL methodology: https://medium.com/deribitofficial/dvol-deribit-implied-volatility-index-72bda8b22ce6
- Cboe Global Indices Feed (real-time vs delayed): https://www.cboe.com/us/indices/accessing-index-data
- Zarattini, Aziz, Barbon (2024), noise area (via session_stats.final.md): https://www.cxoadvisory.com/momentum-investing/complex-intraday-time-series-momentum-strategy-applied-to-spy/
- Pine v6 reference (local mirror): request.security (series string `symbol`, `ignore_invalid_symbol`, 40-call limit), dynamic requests (other-timeframes-and-data.md §Dynamic requests), `earnings.future_time` (Variables.md).
- Sibling studies used: ict_time.final.md (TIME-3, -4, -5, -8), quant_pot.final.md (QPOT-02, -03, -04, -05), quant_regime.final.md (REG-2, §1.7), asset_specific.final.md (ASSET-5, E2, H2), session_stats.final.md (§2.6, §2.7, noise area).
