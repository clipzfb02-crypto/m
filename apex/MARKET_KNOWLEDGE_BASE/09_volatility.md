# 09 · Volatility and Regime Intelligence

Author role: R6, volatility, momentum and regime specialist. Spec coverage: APEX_ULTIMATE_SPEC section 9 (and the parts of sections 10, 13.1, 14.3 and 16 that depend on volatility).

**How to read the evidence tags**
- **[R6-Tn]** is a test run by the R6 role in this workflow session on the study's local data. The scripts and raw outputs are in `/tmp/claude-0/-home-user-m/7ce60006-3639-59b1-8cd3-87355409d58a/scratchpad/r6_tools/` (`vol_est.py` T1, `vol_regime.py` T2/T3, `mom_redund.py` T4, `mom_factors.py` T5, `kernels.py` T6, `gapfill_t7.py` T7; outputs `out_*.txt`). Every number is quoted with its dataset and sample size.
- **Resume pass.** T1-T6 were written by an earlier, interrupted R6 pass. In the resume pass I re-read every script and checked every quoted number against the raw output files. The pass found that T2/T3 had tested simpler versions of three recommended constructs: the raw (not deseasonalised) volatility state, ER thresholds of 0.40/0.32 without the 2-bar confirmation, and a linear (not log, not deseasonalised) shock z. **T7** (`gapfill_t7.py` → `out_t7_{5m,1h,btc,eur,d,rw}.txt`) tests the documented forms directly and fully causally, with the clock learned from past bars only. Where T7 changes a conclusion, the entry says so.
- **[study: key]** is a number from a combined study report (`brief/study/<key>.final.md`). It was replicated by the study's researcher B unless the tag says "as reported by A".
- **[verified]** means the source record (abstract or publisher/RePEc page) was opened in this workflow session; the resume pass re-opened Patton (2011), Bollerslev (1986), Engle (1982) and Levine & Pedersen (2016). **[study-verified]** means a study report says it re-opened the source. **[unverified]** means neither.

**Datasets used by R6-T1..T6**
- CME futures, 5-minute bars resampled from 1-minute: ES, NQ, RTY, YM, CL, GC, 2026-01-20 → 2026-04-15, about 16,500 bars each (GC 13,900).
- CME futures, 1-hour bars: ES, NQ, RTY, YM (2025-03-21 → 2026-04-15, about 6,270 bars each) and CL (2025-06 → 2026-04, 4,520 bars). GC 1H is excluded because it splices two contract months (study: academic_sr, ict_liq).
- BTCUSD 1-hour, 2017-01 → 2025-01, 70,273 bars.
- EURUSD 1-hour, 2017-04 → 2018, 5,000 bars.
- S&P 500 and NASDAQ Composite daily, 1999-2018, 5,031 bars each.
- A Gaussian random walk (60,000 bars, 20 intrabar steps) as a reference.
- Every real series is paired with a **sign-flip null**: each bar is rebuilt from the previous synthetic close with its own gap, range and body, mirrored with probability ½. It keeps ranges, timing and volatility clustering and destroys direction. A volatility effect should survive in the null. A directional effect must beat it.

Line numbers refer to the frozen DOL Engine v2 copy `brief/baseline_v2.pine`.

---

## 1. Scope and role in APEX

Volatility is the one market property that the study found to be **persistent and forecastable** at chart horizons. Direction is close to a random walk at those horizons (study: quant_regime finding 1 and Le 2026; R6-T3 and R6-T4 below). Volatility therefore does three jobs in APEX:

1. **It is the measuring unit.** Every distance (to a pool, a stop, a forecast band) is expressed in units of *expected movement over the horizon*. A biased unit biases every downstream number. The study measured the DOL Engine's ATR14 unit as miscalibrated by up to −8.2 pp in expanded volatility and by −17 to +11 pp by hour of day (study: quant_regime 2.6; ict_time E17).
2. **It is the regime axis that actually persists.** A volatility state (compressed / normal / expanded) forecasts the next window. A trend/range label only describes the window that just ended.
3. **It sizes uncertainty and tradeability.** The forecast cone, the expected-move check against costs, and abnormal-move or thin-market warnings all come from the forward variance.

**Modules fed** (APEX names follow spec section 13):
- **VOL** (volatility engine): true range, the per-bar variance proxy, the intraday clock, forward variance V(H), the horizon unit u_H, the shock flag. Every other module consumes it.
- **REG** (Market Regime Score A): the two-axis classifier (efficiency × volatility) with adaptive thresholds, hysteresis and dwell, plus clock and liquidity context.
- **DOL** (Buy-side and Sell-side Draw Scores C/D): distance in u_H units, touch probabilities from V(H).
- **FCST** (forecast path and uncertainty, spec 14): cone width, horizon-specific error scaling.
- **FQ** (Forecast Quality Score F): lowered in shock, thin, event and data-quality states.
- **RISK** (spec 16): expected move vs cost, gap risk, event risk.
- **CAL** (calibration and ledger): regime-split and volatility-split grading.
- **UI / ALERT**: optional regime row, expansion alert, shock and event flags.

---

## 2. Classification table

E = established mechanics or exchange documentation; A = academic or statistical evidence; D = discretionary practitioner theory; C = contested or unsupported by tests.

| Concept | Class | Evidence grade | Objectively calculable? | One-line note |
|---|---|---|---|---|
| True range (gap-aware) | E | strong | yes | Definition (Wilder). Includes the gap from the prior close. |
| ATR, RMA smoothing | E | strong | yes | Pine `ta.atr` = RMA of TR. Mean age n−1 bars. |
| ATR, SMA smoothing | E | strong (definition) | yes | Mean age (n−1)/2. Intraday it forecasts 4-29% worse than RMA [R6-T1]. |
| ATR percentile (raw) | D | weak | yes | Intraday it measures the time of day unless deseasonalised [R6-T3, R6-T7]. |
| Close-to-close realised vol | A | strong | yes | Unbiased but noisiest. Worst forecaster in every family [R6-T1]. |
| Parkinson estimator | A | strong (theory), moderate (practice) | yes | Efficiency ≈5.2 in theory, 1.2-5 in practice. Breaks on gappy or thin data. |
| Garman-Klass estimator | A | strong (theory), moderate (practice) | yes | Efficiency ≈7.4 in theory. Same gap problem; fix with the gap term. |
| Rogers-Satchell estimator | A | strong (theory), moderate (practice) | yes | Drift-independent; ignores gaps. |
| Yang-Zhang estimator | A | strong (theory), weak (bar-level use) | yes | Gap- and drift-robust but needs a window; noisy at n = 20 [R6-T1]. |
| GK + gap per-bar proxy | A | moderate | yes | The input of the study's volatility clock (TIME-3). |
| Horizon-matched unit (HAR/GARCH logic) | A | strong (concept), moderate (test) | yes | √(ATR14·ATR100) or the clock-based V(H). |
| Range percentile | D | weak | yes | Context only. ADR-remaining caps are refuted (study: session_stats). |
| Volatility expansion / contraction state | A | strong (persistence) | yes | Must be deseasonalised intraday. Deseasonalised state: kappa +0.24 to +0.55 at lag 12; raw state on 1H: −0.05 to −0.20 [R6-T3, R6-T7]. |
| Volatility clustering (EWMA, GARCH, CARR) | A | strong | yes (fixed-parameter forms) | GARCH maximum likelihood is not feasible in Pine; EWMA pairs are. |
| Volatility of volatility | A | moderate (finance), none (for DOL) | yes (proxy) | Untested for this engine. |
| NR7 / NR4 / inside bar | D | none (direction), weak (magnitude) | yes | Breaks do not continue (study: quant_regime T5). |
| Bollinger bandwidth percentile | D | none (direction) | yes | Mixes trend and volatility (close dispersion). |
| TTM-squeeze proxy (BB inside KC) | D | none (direction) | yes | Equivalent to σ_close/ATR < 0.75; partly an efficiency measure. |
| Breakout from compression vs extension in expansion | C (direction), A (magnitude) | none (direction), weak-moderate (magnitude) | yes | The difference is a volatility-path and unit difference, not a directional one. Much of it is estimator noise: a constant-volatility random walk gives a 1.13× ratio [R6-T2, R6-T7]. |
| Gaps (session, weekend, roll) | E | strong (mechanics) | yes | Variance and gap-through are real; magnet effects are contested. |
| Abnormal move (robust z of TR) | A | moderate (magnitude); none (direction, except one BTC cell) | yes | Fat tails. Linear z: P(z ≥ 5) is 0.9-4.0% of bars vs 0.15% on a random walk. Deseasonalised log z: P(z ≥ 3) is 0.5-1.3% vs 0.10% [R6-T2, R6-T7]. |
| Trend / range / transition regime (efficiency axis) | C (as a forecast), E (as a description) | weak | yes | No next-window persistence beyond a random walk [study; R6-T3]. |
| ADX / CHOP / Hurst / VR as regime switches | C | none | yes | Fire on 7-38% of random-walk bars (study: quant_regime). |
| Hidden-Markov / Markov-switching regime | A (in sample) | weak (out of sample, intraday) | partial | The states that persist are volatility states. |
| Hysteresis and minimum dwell | E (engineering) | strong (display stability) | yes | Cuts flips 2.4× (tested 0.40/0.32 rule) to 3.1× (documented 0.46/0.36 rule with 2-bar confirmation). Label information stays at random-walk level [R6-T3, R6-T7]. |
| Intraday volatility clock | A | strong | yes | The largest measured improvement to touch probability in the study. |
| Scheduled-event variance | A | strong (mechanism), moderate (multiples) | partial (manual input) | Pine has no calendar. |
| Low-liquidity periods | E (existence) | moderate | proxy | No bid/ask in Pine; clock, volume and time-gap proxies only. |
| Implied volatility (VIX family) | A | strong (daily), moderate (intraday) | yes, for mapped symbols | Optional; small gain once the clock exists (study: x1_implied_vol). |

---

## 3. Features

Notation used throughout:
- Bar t has open O_t, high H_t, low L_t, close C_t, volume V_t and open time τ_t. C_{t−1} is the previous close.
- `tick` = `syminfo.mintick`. `chartS` = chart timeframe in seconds.
- RMA_n(x): Wilder smoothing, x̄_t = x̄_{t−1} + (x_t − x̄_{t−1})/n, seeded with an SMA (Pine docs, `ta.rma`).
- EMA_n(x): α = 2/(n+1).
- A_n = ATR over n bars (RMA unless stated). H = forecast horizon in bars (APEX default 60, range 20-120 per spec 14).
- "Knowable at close t" means the value is final once bar t is confirmed (`barstate.isconfirmed`) and is used for signals from that close onward. Live (intrabar) values are display-only unless stated.

### True range (gap-aware)
- **Classification:** E; strong.
- **Definition:** The full price excursion of a bar including any gap from the previous close.
- **Market mechanism:** A gap is real price risk that the bar's high-low range omits. For a trader the gap is movement that happened while the market was closed or thin. Nobody is "on the other side" of a definition; it is a measurement.
- **Mathematical implementation:**
  - TR_t = max(H_t, C_{t−1}) − min(L_t, C_{t−1}). For the first bar, TR = H − L.
  - Log form for variance work: TRℓ_t = ln(max(H_t, C_{t−1}) / min(L_t, C_{t−1})).
  - Gap bar (from study: asset_specific 1.4): (τ_t − τ_{t−1}) ≥ max(2·chartS, 1800 s).
  - Knowable at close t (TR is live intrabar; use only confirmed values for state).
- **Required data:** OHLC, time.
- **Pine v6 availability:** `ta.tr` (variable, `handle_na = false`), `ta.tr(true)` (docs: `math.max(high - low, math.abs(high - close[1]), math.abs(low - close[1]))`). O(1). Feasible.
- **Proxy limitations:** None for exchange-traded futures. On spot FX and CFDs the chart prints bid or mid prices from one data vendor, so TR depends on the feed. At the FX rollover hour, bid-plotted charts can print wicks that never traded at mid (study: asset_specific 1.4).
- **Useful when:** always. It is the base of ATR and of the shock detector.
- **Fails when:** a continuous-futures roll creates an artificial gap (ES about +35-55 points, NQ about +150-250 points per quarter at 2025-26 carry; study: asset_specific). Roll bars must be excluded from every volatility estimator (study: calib_ml CAL-10 gap filter at 4 ATR; asset_specific ASSET-4 roll detection with `ticker.modify(..., backadjustment = backadjustment.on)`).
- **Validation experiment:** Unit test, not a hypothesis: on 1,000 random bars per asset class compare Pine `ta.tr` with the formula; the pass criterion is exact equality to floating tolerance. Roll guard: on unadjusted continuous ES/NQ/CL, every roll bar detected by the back-adjusted request must be flagged; pass = 100% recall, ≤ 1% false flags.
- **Existing evidence:** Definition (Wilder 1978 via the study). GOOG daily: the overnight return carries 38% of daily return variance (study: asset_specific).
- **APEX recommendation:** **INCLUDE-CORE** (VOL). Use TR, never H − L, in every range-based quantity. Redundancy: it is the input of ATR, the shock z and the GK+gap proxy, not a separate vote.
- **Sources:** Pine v6 reference `ta.tr` (local mirror, opened this session). Wilder (1978), *New Concepts in Technical Trading Systems* [study-verified definition]. Study: asset_specific 1.4.

### ATR: RMA vs SMA smoothing
- **Classification:** E (definition); strong. The forecast comparison is A; moderate.
- **Definition:** Average true range over n bars. Wilder's original and Pine's `ta.atr` use RMA. Some platforms use an SMA.
- **Market mechanism:** Volatility clusters, so a recent average of TR forecasts the next bars' TR. The smoother's memory decides how fast it reacts and how badly it is fooled by intraday seasonality.
- **Mathematical implementation:**
  - RMA: A_t = A_{t−1} + (TR_t − A_{t−1})/n. Weights w_k = (1/n)(1 − 1/n)^k. Mean age (centre of mass) = n − 1 bars (13 for n = 14). Half-life = ln 2 / (−ln(1 − 1/n)) ≈ 9.4 bars for n = 14. Equivalent EMA span = 2n − 1 (27 for n = 14).
  - SMA: A_t = (1/n) Σ_{k=0}^{n−1} TR_{t−k}. Mean age (n − 1)/2 = 6.5 bars. A large bar leaves the window abruptly n bars later (a "drop-off" step unrelated to current conditions).
  - Defaults: n = 14 for the user-facing distance unit (familiar, already in DOL Engine v2 line 87). The forecast unit is u_H (see "Horizon-matched volatility forecast"), not raw ATR14.
  - Knowable at close t.
- **Required data:** OHLC.
- **Pine v6 availability:** `ta.atr(length)` (docs: "returns the RMA of true range"); `ta.sma(ta.tr(true), n)` for the SMA version. O(1). Feasible.
- **Proxy limitations:** ATR is a range-based estimate of σ, scaled by an unknown constant (mean bar range / σ_cc was 1.39-1.48 on CME 5-minute data vs 1.596 for Brownian motion; study: quant_pot 1.7). It is not a forecast of the horizon's variance; that is the job of u_H.
- **Useful when:** as a familiar, robust distance unit; daily and higher charts.
- **Fails when:** intraday with short n. The window covers only part of the daily volatility cycle, so it under-forecasts after quiet hours and over-forecasts after busy hours.
- **Validation experiment:** Pre-registered: "RMA ATR14 forecasts next-H realised variance better than SMA ATR14 on intraday charts." Outcome: QLIKE of c·A² · H against RV_fwd = Σ_{k=1..H} r²_{t+k}, c fitted on the training half. Sample: every chart and timeframe in the Phase 6 matrix; 2-fold time split. Baseline: SMA ATR14. Metric: QLIKE difference with block-bootstrap SE (block = max(H, bars per day)). Pass: RMA better on ≥ 80% of intraday series with the pooled 95% CI excluding 0.
- **Existing evidence:** [R6-T1] QLIKE vs ATR14-RMA (positive = SMA worse): 5m H = 12: +3.8% (6 series, −2.3 to +12.3); 1H H = 6: **+25.1%** (5 series, +11.8 to +30.7); 1H H = 24: +29.1%; BTC 1H H = 6: +6.1%; EURUSD 1H H = 6: +26.1%; daily H = 1: −0.1%, H = 5: +1.1%. On daily bars the choice does not matter; intraday the longer memory of RMA wins clearly, because QLIKE penalises under-forecasts after quiet periods.
- **APEX recommendation:** **INCLUDE-CORE** (VOL) with RMA. Do not offer SMA. Redundancy: ATR14, Parkinson, GK and YZ all estimate the same latent σ; APEX keeps ATR14 only as the display unit and u_H as the forecast unit.
- **Sources:** Pine v6 reference `ta.atr`, `ta.rma` (opened this session). Wilder (1978) [study-verified]. R6-T1 (`out_volest_*.txt`).

### ATR percentile and volatility percentile
- **Classification:** D (as used by traders); weak.
- **Definition:** Where the current ATR sits in its own recent history, 0-100.
- **Market mechanism:** Volatility mean-reverts, so a high percentile implies lower volatility later and a low one implies higher (Corsi 2009 HAR). The percentile is a scale-free way to say "high" or "low" across instruments.
- **Mathematical implementation:**
  - Pine's `ta.percentrank(x, N)` = 100 × (number of the previous N values ≤ x_t) / N (docs).
  - Raw ATR in price units trends with the price level, so rank a scale-free quantity: q_t = ln(A14_t / C_t) or, better, the deseasonalised state variable z_V (see "Volatility expansion and contraction state").
  - N = 250 bars default (about one year of daily bars, 2 weeks of 1H futures bars, 1 day of 5m bars). N must cover several full daily cycles intraday.
  - Knowable at close t.
- **Required data:** OHLC.
- **Pine v6 availability:** `ta.percentrank` is O(N) per bar (N = 250 is cheap). `ta.percentile_nearest_rank` and `ta.percentile_linear_interpolation` give thresholds (docs; the nearest-rank method "ignores na"; linear interpolation propagates na). Feasible.
- **Proxy limitations:** On intraday charts the raw percentile mostly measures **time of day**.
  - [R6-T3] On CME 1H, the raw ATR5/ATR100 state has negative label persistence 12 bars later (kappa −0.05 to −0.20 on 5 series), because 12 hours later it is the other half of the day.
  - [R6-T7] On CME 5m the raw state looks persistent at a lag of exactly one day (kappa +0.28 to +0.39 on ES/NQ/RTY/YM/CL) and anti-persistent at half a day (−0.20 to −0.25). That is the clock repeating, not volatility persisting. The deseasonalised state gives +0.02 to +0.13 at one day and +0.06 to +0.11 at half a day.
  - The percentile of a non-stationary series (a trending price level) is also biased.
- **Useful when:** daily charts; deseasonalised intraday; as a display.
- **Fails when:** intraday without deseasonalising; after structural breaks (a 3× volatility regime shift such as GC Jan-Mar 2026 makes the window's history irrelevant; study: ict_time 2.2).
- **Validation experiment:** Hypothesis: "The percentile of the deseasonalised log variance level has positive label persistence at lag H (kappa ≥ 0.2) on every intraday timeframe, while the raw percentile does not on 1H." Outcome: tercile label at t and t+H. Sample: Phase 6 intraday matrix. Baseline: raw ATR percentile. Metric: Cohen's kappa at lag H. Pass: deseasonalised kappa ≥ 0.2 on ≥ 80% of series and above raw kappa on 1H.
- **Existing evidence:**
  - R6-T3 and R6-T7 as above.
  - [R6-T7] Deseasonalised-state kappa at lag 12, with the clock learned causally: 5m +0.46 to +0.55 (6 series); 1H +0.24 to +0.33 (5 series); BTC 1H +0.32; EURUSD 1H +0.21.
  - On the same data this hypothesis already passes. Phase 6 must replicate it on new data.
  - Legacy `DOL_Engine_early.pine` (line 1022) used `ta.percentrank(atr, 200)` with fixed 20/80/95 cut-offs as a trade filter, untested.
- **APEX recommendation:** **INCLUDE-OPTIONAL** as a display of the deseasonalised state only. Do not use the raw ATR percentile anywhere. Redundancy: it duplicates the V-axis z of REG; show one, not both.
- **Sources:** Pine v6 reference `ta.percentrank`, `ta.percentile_*` (opened this session). Corsi (2009) [study-verified]. R6-T3.

### Close-to-close realised volatility
- **Classification:** A; strong (as an unbiased estimator), and the weakest forecaster in practice.
- **Definition:** The standard deviation of close-to-close log returns over a window, or an EWMA of squared returns.
- **Market mechanism:** It is the textbook realised variance at bar sampling. It uses one number per bar and discards the intrabar path, which makes it noisy.
- **Mathematical implementation:**
  - r_t = ln(C_t / C_{t−1}). Rolling: σ̂²_n = (1/(n−1)) Σ (r − r̄)². EWMA: σ̂²_t = λσ̂²_{t−1} + (1−λ)r_t².
  - DOL Engine v2 uses `potSig = ta.stdev(ta.change(close), 50)` (line 916), in price units, which is close-to-close with n = 50.
  - Efficiency 1 by definition (the reference for the others).
  - Knowable at close t.
- **Required data:** closes.
- **Pine v6 availability:** `ta.stdev(source, length, biased)` (docs: biased = true by default, population estimate), `ta.ema`. O(1). Feasible.
- **Proxy limitations:** It ignores intrabar range. The square root of an unbiased variance estimate is biased low for σ (Jensen; study: quant_pot 1.7).
- **Useful when:** as the *target* of forecast evaluation (Σ r² over the horizon is an unbiased if noisy proxy of realised variance; Patton 2011 shows that QLIKE and MSE keep forecast rankings valid under such noisy proxies).
- **Fails when:** used as the forecaster. [R6-T1] QLIKE vs ATR14-RMA: the engine's 50-bar close-to-close σ is +15.0% worse on 5m (H = 12), +2.0% on 1H (H = 6), +22.4% on BTC 1H, +7.0% (H = 1) and +26.3% (H = 5) on daily indices. An EWMA(20) of r² is +13.4%, +10.6%, +16.5% and +14.7% respectively.
- **Validation experiment:** Covered by VOL-X1 (forward-variance unit) in section 8.
- **Existing evidence:** R6-T1 above. The study found that switching the PoT σ from close-to-close to Yang-Zhang gains only +0.28% log-loss (CI −0.10 to +0.66%); the large gains come from seasonality and clustering, not from the estimator (study: quant_pot finding 7).
- **APEX recommendation:** **EXCLUDE** as a forecaster (replace `potSig`). Keep r² as the evaluation target in CAL and in Phase 6. Redundancy: superseded by the GK+gap proxy and u_H.
- **Sources:** Patton, A. (2011), "Volatility forecast comparison using imperfect volatility proxies", *J. Econometrics* 160(1), 246-256 [verified in the resume pass: EconPapers abstract]. Pine v6 reference `ta.stdev` (opened). R6-T1. Study: quant_pot 1.7.

### Range-based estimators: Parkinson, Garman-Klass, Rogers-Satchell, Yang-Zhang (and the GK + gap proxy)
- **Classification:** A; strong in theory, moderate in practice.
- **Definition:** Variance estimators that use the open, high, low and close, not just the close.
- **Market mechanism:** The high and low record how far price travelled within the bar. Under continuous Brownian motion this carries several times more information about σ than the close alone.
- **Mathematical implementation:** With h = ln(H/O), l = ln(L/O), c = ln(C/O), o = ln(O/C_{t−1}):

  | Estimator | Per-bar variance | Theoretical efficiency vs close-to-close | Assumptions and biases |
  |---|---|---|---|
  | Parkinson (1980) | (h − l)² / (4 ln 2) | ≈ 5.2 | Zero drift, continuous trading, no gaps. Biased **low** by discrete sampling and tick rounding, **high** by bid-ask bounce; ignores the gap. |
  | Garman-Klass (1980) | ½(h − l)² − (2 ln 2 − 1)c² | ≈ 7.4 | Zero drift, no gaps. Can be negative on a bar (floor at 0). |
  | Rogers-Satchell (1991) | h(h − c) + l(l − c) | ≈ 6 | Drift-independent; no gaps. |
  | Yang-Zhang (2000) | σ²_o + kσ²_c + (1 − k)σ²_RS over a window of n bars, k = 0.34 / (1.34 + (n+1)/(n−1)) | highest among drift- and gap-robust estimators | Needs a window (σ²_o, σ²_c are sample variances of o and c; σ²_RS the mean RS). k ≈ 0.13-0.14 for usual n. |
  | **GK + gap** (study: ict_time TIME-3 `xVar`) | max(0, GK) + o² | not published | A per-bar proxy usable inside an EWMA; adds the squared gap back. |

  - Theoretical efficiencies from the study's literature table (quant_pot 1.7). Empirical efficiencies on index data are 1.2-5× with no consistent winner (Vințe et al. 2022, via study).
  - Defaults for APEX: per-bar proxy x_t = GK + gap, smoothed by an EWMA or fed to the clock (below).
  - Knowable at close t.
- **Required data:** OHLC, prior close.
- **Pine v6 availability:** `math.log`, `math.max`, `ta.ema`, `ta.variance`/`ta.stdev`. O(1) per bar (YZ O(1) with rolling sums). Feasible.
- **Proxy limitations:** They assume continuous trading inside the bar. Bars with missing minutes, zero range or stale prints break that assumption.
- **Useful when:** daily bars with real opens (small gains); as the input of a deseasonalised, clustered forecast intraday.
- **Fails when:** pure intrabar estimators (no gap term) meet gappy or thin data. [R6-T1] On GC 5-minute bars (1.7% zero-range bars plus missing minutes between bars), Parkinson and GK forecasts collapsed: QLIKE +965% and +2,143% vs ATR14. GK + gap on the same data: −11.4%. Close-to-close drift estimates contaminate Parkinson and GK.
- **Validation experiment:** VOL-X1 (section 8): the GK + gap clock forecast vs ATR14 vs √(ATR14·ATR100) per chart, scored by QLIKE.
- **Existing evidence:** [R6-T1] QLIKE vs ATR14-RMA, negative = better:
  - 5m H = 12 (ES, NQ, RTY, YM): Parkinson +1.3 to +2.0%, GK −0.9 to +4.1%, GK + gap −0.2 to +2.1%; CL: +5.7 to +8.8%; YZ(20) mean +4.3%.
  - 1H H = 6 (5 series): Parkinson +10.3%, GK +12.6%, RS +14.9%, GK + gap +4.4%, YZ +5.2%.
  - BTC 1H H = 6: all within +1.8 to +5.2%.
  - Daily H = 5 (SPX, NDX): GK −2.6%, RS −2.1%, Parkinson +1.3%, YZ +7.4%.
  - Conclusion: on raw bars the choice of estimator changes forecasts by a few percent; the clock changes them by 13-24% intraday (next entries). Study: Yang-Zhang instead of close-to-close σ, +0.28% log-loss, not significant (quant_pot).
- **APEX recommendation:** **INCLUDE-CORE** only the **GK + gap** per-bar proxy, as the input of the VOL clock and level. **RESEARCH-ONLY** for Parkinson, RS and YZ (no reason to ship them). Redundancy: all of them, ATR and close-to-close estimate the same σ; never show or score more than one.
- **Sources:** Parkinson (1980); Garman & Klass (1980); Rogers & Satchell (1991); Yang & Zhang (2000), *J. Business* 73(3) [all study-verified, quant_pot 2.1]; Vințe, Ausloos & Furtună (2022) arXiv:2205.01370 [study-verified]; Shu & Zhang (2006) *J. Futures Markets* 26(3) [study-verified]; Alizadeh, Brandt & Diebold (2002) *J. Finance* 57(3) [study-verified]. R6-T1.

### Horizon-matched volatility forecast (the VOL unit u_H)
- **Classification:** A; strong (concept: volatility mean reversion, HAR, GARCH term structure), moderate (tests on this engine).
- **Definition:** A forecast of the price movement expected over the next H bars, used as the unit for distances, touch probabilities and forecast bands.
- **Market mechanism:** Volatility is persistent but mean-reverting. A 14-bar ATR is a good estimate of the last 14 bars and a biased estimate of the next H bars: too high after an expansion, too low after a compression. The fix is to forecast the horizon, not to describe the past.
- **Mathematical implementation:**
  - **GARCH(1,1) term structure** (Bollerslev 1986): E_t[σ²_{t+j}] = σ̄² + φ^{j−1} (σ²_{t+1} − σ̄²) for j ≥ 1, φ = α + β. Average over the horizon: σ̄²_H = (1/H) Σ_{j=1}^{H} E_t[σ²_{t+j}] = σ̄² + (σ²_{t+1} − σ̄²)·w_H, with w_H = (1 − φ^H) / (H(1 − φ)). Example: a half-life of 30 bars (φ = 0.5^{1/30} ≈ 0.977) and H = 30 give w_H = 0.73.
  - **HAR** (Corsi 2009): ln RV_{t→t+H} = b₀ + b_d ln RV_d + b_w ln RV_w + b_m ln RV_m, with daily, weekly and monthly components.
  - **Cheap Pine form (study: quant_regime REG-1):** u_t = A14_t^a · A100_t^{1−a}, a = 0.5, i.e. u = √(A14 · A100). In logs it shrinks the fast level halfway toward the slow level. Intraday only; on daily charts keep A14.
  - **Clock form (study: ict_time TIME-3; preferred when it wins the per-chart scorecard):** V_t(H) = Σ_{k=1}^{H} s²(τ_{t+k}) · [L_s + φ^k (L_f − L_s)], where s(·) is the seasonal factor, L_f and L_s are fast and slow deseasonalised levels, φ = 0.5^{1/30}. Then u_H = C_t·√V_t(H) (price units) and the per-bar equivalent is σ_eff = u_H/√H.
  - τ_{t+k} must be the time of the k-th **future bar**, which skips halts and weekends: Pine `time(timeframe.period, bars_back = -k)` returns "the expected timestamp ... N bars after the current bar" for −1 to −500 (docs), or TIME-3's open-cell walk.
  - Knowable at close t (uses closed bars only; the expected future timestamps are deterministic).
- **Required data:** OHLC, time, the exchange time zone.
- **Pine v6 availability:** `ta.atr`, `math.pow`, `math.sqrt`; the clock needs `var` arrays (48 buckets × 7 weekdays), `hour(time, tz)`, `dayofweek(time, tz)`, `time(..., bars_back = -k)`. One O(H) walk per bar at global scope (not per level). Feasible.
- **Proxy limitations:** Holidays and early closes are unknown to Pine, so the forward variance is overstated on those days. Scheduled events need manual input.
- **Useful when:** always on intraday charts. It matters most when H × timeframe is shorter than about one day.
- **Fails when:** jump-dominated or spliced series (the clock z-surface failed on GC 1H, −9.8% Brier; study: ict_time 2.2), and right after structural volatility breaks. Hence per-chart selection by a proper-score scorecard (study: TIME-4).
- **Validation experiment:** VOL-X1 and VOL-X2 in section 8.
- **Existing evidence:**
  - Study: blended unit OOS log-loss on pool-touch events −0.40% (5m), **−2.79%** (15m), −0.45% (1H), **−1.21%** (BTC 1H), **+0.66% (daily: worse)**; with time-of-day rows −3.04 / −5.82 / −0.65 / −1.23%. It cut the expanded-volatility calibration bias from −5.5..−8.2 pp to −1.3..−3.2 pp (quant_regime 2.6).
  - Study: clock (clkB) Brier vs the engine +3.86% (5m H = 30), +5.45% (5m H = 60), +3.86% (1H H = 12), −1.05% (1H H = 30); mean absolute hour bias 7.3 → 2.1 pp (ict_time 2.2).
  - Study: race WIN≤H with σ_eff from the forward variance has calibration slope 1.00 vs 0.89 (constant σ) and 0.69 (engine with drift) (quant_pot 2.3).
  - [R6-T1] QLIKE vs ATR14-RMA, blended unit: 5m H = 12 +1.8%, 5m H = 48 −3.1%, 1H H = 6 −3.2%, 1H H = 24 −5.7%, BTC −1.3% / −6.6%, EUR −8.3% / −17.1%, daily +2.3% (H = 1) and +8.7% (H = 5).
  - [R6-T1] **GK + gap EWMA × clock**: 5m H = 12 **−13.3%** (all six series negative, −4.7 to −20.5%); 5m H = 48 −12.0%; 1H H = 6 **−24.0%** (−2.4 to −33.6%); 1H H = 24 +1.6% (the 24-bar window averages the clock out); BTC −0.5% / +2.5%; EURUSD −23.2% at H = 6 but **+7.4% at H = 24**. MZ R² on 1H H = 6 rises from 0.147 (ATR14) to 0.346.
  - Per-series block-bootstrap SEs: about 2.4-3.2 pp on ES, NQ and YM 5m; RTY 5m −4.7% (SE 4.6); CL and GC 5m −14% (SE 11.7-12.8). The CL and GC gains are not individually significant.
  - Caveats on the T1 clock (it is an upper bound on what Pine will get):
    - The bucket factors were learned on the other half of the sample, and one of the two folds trains on later data.
    - The future-bar factors use the realised future timestamps, which know about holidays and halts that Pine's expected timestamps (`time(..., bars_back = -k)`) do not.
    - The fully causal clock of R6-T7 (expanding means over past bars only) is the realistic version; VOL-X1 must score that.
  - [R6-T1] HAR on GK + gap (fitted on the training half) is unstable intraday: 1H family mean +8.8% with one series at +66%. It does better on BTC (−3.0% / −11.2%) and EURUSD (−19.3% / −24.9%), and on daily it is SPX −6.7% and NDX +2.1% at H = 5.
  - [R6-T7] The clock forward-variance unit √V(H) (causal) narrows the gap in forward range between compression and expansion breakouts. On 5m the COMP/EXP ratio is 1.01-1.15 with it vs 1.10-1.18 in ATR14 units (details in the breakout entry). It does not remove the gap.
- **APEX recommendation:** **INCLUDE-CORE** (VOL; consumed by DOL, FCST, RISK, CAL). Ship three candidates {ATR14, √(ATR14·ATR100), clock V(H)} and select per chart by the CAL scorecard (lowest proper score with ≥ 2,000 resolved probes and z ≤ −2 against ATR14; hold ≥ 5 days). Daily and higher: ATR14 (or HAR when Phase 6 confirms it). Redundancy: this replaces potSig, ATR-unit surfaces and volatility-tercile rows.
- **Sources:** Bollerslev (1986), *J. Econometrics* 31(3), 307-327 [verified this session: IDEAS/RePEc record and abstract]; Engle (1982), *Econometrica* 50(4), 987-1007 [verified this session: IDEAS/RePEc record]; Corsi (2009) [study-verified]; Pine v6 reference `time()` bars_back (opened). Study: quant_regime REG-1, ict_time TIME-3/4, quant_pot QPOT-02/05. R6-T1, R6-T7.

### Range percentile
- **Classification:** D; weak.
- **Definition:** The percentile of the current bar's range, or of the session's range so far, against its history (for example "today has used 80% of its average daily range").
- **Market mechanism:** Ranges are bounded on most days, so traders treat "range used up" as a sign that further extension is unlikely.
- **Mathematical implementation:**
  - Bar level: RP_t = percentrank(TR_t / ŝ(τ_t), N), with ŝ the clock factor so that busy hours are not always high.
  - Session level: ρ_t = (session high − session low) / ADR_N, ADR_N = mean daily range over N = 14 days.
  - Knowable at close t (session level is live during the session; use the confirmed value).
- **Required data:** OHLC, session boundaries.
- **Pine v6 availability:** `ta.percentrank`, session tracking with `time(timeframe.period, session, tz)`, or `request.security` for daily ranges. Feasible.
- **Proxy limitations:** The day's range is path-dependent; a bound on range is not a bound on the remaining move.
- **Useful when:** display context; abnormal-bar detection (with deseasonalising).
- **Fails when:** used as a cap. The study refuted "ADR remaining" caps (session_stats §2.7). Expected-move bands from implied vol contain the close 73-80% of days, not 68% (study: x1_implied_vol 2.9); they are context lines, not limits.
- **Validation experiment:** Hypothesis: "When the session range already exceeds 1 ADR, the probability that the session extreme extends by another 0.25 ADR before the close is lower than the clock-matched random-walk value." Outcome: extension by 0.25 ADR before the session close. Sample: 5 CME futures, 2 FX, BTC; all sessions. Baseline: driftless clock-scaled touch probability for 0.25 ADR given the remaining session variance. Metric: observed minus predicted, day-clustered SE. Pass: |difference| > 3 pp with |z| > 2 on ≥ 3 asset classes. (Prior: fails, per session_stats.)
- **Existing evidence:** Study: session_stats §2.7 (ADR-remaining caps refuted); x1_implied_vol 2.9 (EM bands touched on one side 15-24% of days).
- **APEX recommendation:** **INCLUDE-OPTIONAL** (UI context only, off by default). **EXCLUDE** as a target filter or cap. Redundancy: overlaps the shock detector (bar level) and the clock (session level).
- **Sources:** Study: session_stats §2.7, x1_implied_vol §2.9. Pine v6 reference `ta.percentrank` (opened).

### Volatility clustering: EWMA (RiskMetrics), GARCH intuition, CARR
- **Classification:** A; strong.
- **Definition:** Large moves tend to follow large moves and small follow small; volatility has long memory.
- **Market mechanism:** Information arrives in bursts, traders react with lags, and risk-managed participants scale positions to recent volatility, which feeds back into volatility. The other side of any volatility burst is the liquidity provider who widens spreads and reduces depth.
- **Mathematical implementation:**
  - EWMA (RiskMetrics 1996): σ²_t = λσ²_{t−1} + (1 − λ)x_{t−1}, λ = 0.94 for daily data (effective span 2/(1−λ) − 1 ≈ 32 days). Intraday, λ must be restated per bar: λ_bar = λ_day^{1/bpd} would be far too slow for a fast level; use span ≈ 1 day for L_f and ≈ 5-20 days for L_s.
  - GARCH(1,1): σ²_t = ω + αr²_{t−1} + βσ²_{t−1}; persistence φ = α + β; half-life ln 0.5 / ln φ; unconditional σ̄² = ω/(1 − φ).
  - CARR (Chou 2005): λ_t = ω + αR_{t−1} + βλ_{t−1} on the range.
  - APEX form ("GARCH-lite"): fast and slow EWMAs of the deseasonalised proxy x_t/s²(τ_t): L_f (span ≈ potLen = 50 bars), L_s (half-life 5 days), mean reversion φ = 0.5^{1/30} between them in the forward walk (study: TIME-3). This has the GARCH term structure without maximum-likelihood fitting.
  - Knowable at close t.
- **Required data:** OHLC, time.
- **Pine v6 availability:** `ta.ema`, `ta.rma`, recursive `var float`. GARCH maximum-likelihood estimation is **infeasible** in Pine (no optimiser; could be done by grid search but costly and fragile). Fixed-parameter forms are feasible and O(1).
- **Proxy limitations:** OHLC proxies are noisier than intraday realised variance.
- **Useful when:** always; it is why a volatility state forecasts the next window.
- **Fails when:** jumps and breaks (a single roll gap or bad print enters the level unless winsorised; TIME-3 caps the update at 25× the level and 50× the ratio).
- **Validation experiment:** Hypothesis: "The deseasonalised log-range has positive autocorrelation at lags of 1 bar, 1 hour and 1 day on every intraday series, and it is reproduced by the sign-flip null." Metric: ACF with block-bootstrap CI. Pass: ACF > 0.1 at lag 1 day on all series. (A mechanical check that the clustering assumption holds on the user's instrument.)
- **Existing evidence:**
  - Study (researcher A's measurements in quant_pot 1.9): deseasonalised log-range ACF on ES 5m is 0.63 at lag 1, 0.49 at 1 hour, 0.34 at 6.5 hours and 0.27 at 1 day. Log-loss with seasonality and a flat level is 0.6003, vs 0.5659 with seasonality × clustering.
  - Study: corr(ln(ATR14/ATR100) at t and t+14) is 0.49-0.80 on 4 families, identical in the null (quant_regime 2.2).
  - [R6-T3] Label persistence of the **raw** ATR5/ATR100 state at a 1-hour lag on 5m: kappa +0.26 to +0.48 (6 series); BTC 1H +0.19; daily +0.33; random walk +0.007.
  - [R6-T7] **Deseasonalised** state (GK + gap / causal clock, L_f span 20, L_s span 5 days), kappa at lag 12: 5m +0.46 to +0.55; 1H +0.24 to +0.33; BTC +0.32; EURUSD +0.21; daily +0.39 to +0.41 at lag 10.
  - [R6-T7] An iid random walk gives +0.09 for this smoothed state: overlap of the 20-bar EWMA creates some persistence even without clustering. The real-data excess over that baseline (+0.15 to +0.46) is the clustering.
  - [R6-T2] After an abnormal bar (robust z ≥ 4), the next 12 bars' range in units of the previous ATR is 4.6-5.3 vs 3.8-4.1 for all bars on 5m; BTC 4.59 vs 3.98; reproduced by the null (5.1-5.2 on 5m).
- **APEX recommendation:** **INCLUDE-CORE** (VOL), as the fast/slow deseasonalised level pair. **EXCLUDE** GARCH fitting in Pine. Redundancy: the level pair is the same object as the V-axis of REG and the unit u_H; compute once.
- **Sources:** RiskMetrics Technical Document (1996) [study-verified]; Bollerslev (1986) [verified, IDEAS record]; Engle (1982) [verified, IDEAS record]; Chou (2005) *J. Money, Credit and Banking* 37(3) [study-verified]; Corsi (2009) [study-verified]. Study: quant_pot 1.9, quant_regime 2.2. R6-T2, R6-T3.

### Volatility expansion and contraction state (the REG V-axis)
- **Classification:** A; strong (persistence), moderate (as a calibration key).
- **Definition:** Whether recent volatility is below, near or above its own longer-run level, after removing time-of-day effects.
- **Market mechanism:** Mean reversion of volatility. After compression, the next bars tend to move more than recent bars; after expansion, less. This is mechanical, not directional, and it is reproduced by direction-free nulls.
- **Mathematical implementation:**
  - State variable: v_t = ln(L_f,t / L_s,t), the log ratio of the fast and slow deseasonalised levels (VOL).
    - L_f = EWMA of x_t/s(τ_t) with span 20 bars (tested in R6-T7; TIME-3 uses potLen = 50; the scorecard chooses).
    - L_s = EWMA of the same series with span max(5 days of bars, 100).
    - x_t is the GK + gap proxy and s(τ_t) is the clock factor learned from past bars only.
    - Without the clock (daily and higher, or before warm-up): v_t = ln(A5/A100).
  - Standardise with an EWMA of its own mean and variance, α = 2/2001: z_t = (v_t − μ_{t−1}) / σ_{t−1}. Using t−1 statistics keeps the bar from standardising itself.
  - States with hysteresis (Schmitt trigger): enter COMPRESSED at z ≤ −0.43, leave at z > −0.30; enter EXPANDED at z ≥ +0.43, leave at z < +0.30 (±0.43 = the normal terciles; study: quant_regime REG-2). Minimum dwell 3 bars.
  - Knowable at close t.
- **Required data:** OHLC, time (for deseasonalising).
- **Pine v6 availability:** O(1) recursions; `var int` state. Feasible.
- **Proxy limitations:** Without deseasonalising, on charts whose fast window spans a fraction of the day, the state measures the time of day. [R6-T3] raw ATR5/ATR100 state on 1H: kappa at lag 12 −0.05 to −0.20 on all 5 CME series; changes 144-164 per 1,000 bars.
- **Useful when:** calibration auditing (accuracy by volatility class), display, expansion alerts, widening forecast bands.
- **Fails when:** used as a separate key once the unit is fixed. Study: volatility-tercile rows add −0.23 to +0.36 pp over the blended unit and **hurt** on top of time-of-day rows (15m −2.38% vs −4.06%) (quant_regime 2.6).
- **Validation experiment:** VOL-X3 (section 8).
- **Existing evidence:**
  - Persistence as above.
  - [R6-T7] Flips per 1,000 bars, deseasonalised vs raw state: 5m 40-50 vs 66-116; 1H 70-84 vs 144-164; BTC 75 vs 137; random walk 218 vs 313. Median dwell: 11-13 bars on 5m, 8-9 on 1H.
  - [R6-T2], raw state: the forward range in ATR14 units by state depends on the unit.
    - On 1H: compressed 1.17-1.30 × the mean, expanded 0.73-0.87 (largely the clock).
    - On 5m the ATR14 unit is nearly state-neutral (0.95-1.06), while the blended unit over-corrects (compressed 0.75-0.95, expanded 1.09-1.23). This matches the study's −5.1 pp over-correction on 5m.
    - On a random walk the ATR14 unit alone produces 1.06 / 0.94 (measurement noise in the denominator).
- **APEX recommendation:** **INCLUDE-CORE** (REG V-axis; CAL volatility split; UI optional row; ALERT "Volatility Expansion" optional). Not a directional input, and not a separate probability key. Redundancy: replaces ATR percentile, BBW percentile, squeeze and NR7 as the single compression/expansion measure.
- **Sources:** Study: quant_regime REG-2, 2.6; ict_time TIME-3. R6-T2, R6-T3.

### Volatility of volatility
- **Classification:** A (in option pricing and risk); moderate there; none for this engine.
- **Definition:** How variable volatility itself is; the dispersion of changes in the volatility level.
- **Market mechanism:** When volatility is unstable, a single σ understates tail risk. A mixture of volatilities fattens the distribution of H-bar moves: near levels become less likely to be touched and far levels more likely than a Gaussian with the same mean variance predicts (study: quant_pot 1.6; Perelló et al. 2011).
- **Mathematical implementation:**
  - VoV_t = stdev over M bars of Δln L_f (or Δln A14 on daily charts), M = 50 default; normalised as a percentile over N = 500.
  - Implied version for SPX: CBOE:VVIX (study: x1_implied_vol 1.1; untested).
  - Use (proposed, untested): a widening factor for forecast quantiles, q_p ← q_p · (1 + κ·z_VoV⁺), with κ learned so that empirical coverage matches nominal.
  - Knowable at close t.
- **Required data:** OHLC; optional VVIX.
- **Pine v6 availability:** `ta.stdev`, `ta.change`, `ta.percentrank`; VVIX via one `request.security`. Feasible.
- **Proxy limitations:** OHLC-based VoV is very noisy at chart windows.
- **Useful when:** forecast-interval coverage (FCST, FQ), if Phase 6 shows it helps.
- **Fails when:** unknown; it has not been tested on this engine.
- **Validation experiment:** VOL-X9 (section 8): coverage of 80% H-bar move intervals with and without the VoV widening.
- **Existing evidence:** None for DOL targets. VVIX untested (study: x1_implied_vol "Not proposed").
- **APEX recommendation:** **RESEARCH-ONLY**. Redundancy: partly captured by empirical quantile surfaces, which already include fat tails (PoT(d) = 2·P(X_H > d) for whatever distribution X_H has; study: quant_pot finding 4).
- **Sources:** Perelló, Gutiérrez-Roig & Masoliver (2011) arXiv:1107.1174 [study-verified]. Study: quant_pot 1.6, x1_implied_vol 1.1.

### Compression: NR7, NR4 and inside bars
- **Classification:** D; none for direction, weak for magnitude.
- **Definition:** NR7 (Crabel 1990): today's range is the narrowest of the last 7 bars (NR4: of 4). Inside bar: H_t ≤ H_{t−1} and L_t ≥ L_{t−1}.
- **Market mechanism:** A narrow bar marks a pause in activity; volatility mean reversion predicts a wider range later. The claimed direction comes from "trading the break" of the narrow bar.
- **Mathematical implementation:**
  - NR7_t ⇔ (H_t − L_t) ≤ min_{k=1..6}(H_{t−k} − L_{t−k}). Use TR instead of H − L to respect gaps.
  - Knowable at close t. The break is knowable only at the bar that trades or closes beyond the narrow bar's high or low.
- **Required data:** OHLC.
- **Pine v6 availability:** `ta.lowest(ta.tr(true), 6)[1]`; O(1). Feasible.
- **Proxy limitations:** Intraday, NR7 bars cluster in quiet hours, so the "compression" is mostly the clock. [R6-T2] On 1H, the 12-bar forward range after NR7 bars is **0.78-0.84** × the mean in ATR14 units: lower, not higher, because the quiet hours that produce NR7 bars are followed by more quiet hours relative to an ATR that includes busy hours.
- **Useful when:** as a display marker on daily charts.
- **Fails when:** used for direction or continuation.
- **Validation experiment:** Covered by VOL-X4 (breakout from compression).
- **Existing evidence:** Study: after the first trade-through of an NR7 bar's high or low within 10 bars, the symmetric ±1 ATR race in the break direction is 0.482 ± 0.006 (5m; null 0.495; n 6,953), 0.502 (15m; n 2,135), 0.485 ± 0.011 (1H; n 2,328), 0.486 ± 0.008 (BTC; n 4,400), 0.515 (daily; n 681) (quant_regime 2.8). Bulkowski, 1,201 stocks 1990-2013: 46-47% failure in both breakout directions in bull markets (study-verified via search). Adding an NR7 flag to recalibrated volatility rows changes log-loss by −0.19 to +0.15 pp (quant_regime 2.6).
- **APEX recommendation:** **EXCLUDE** as a signal or score input. Optional chart marker at most. Redundancy: a subset of the V-axis compressed state.
- **Sources:** Crabel (1990) [study citation]; Bulkowski NR7 statistics https://thepatternsite.com/nr7.html [study-verified]. Study: quant_regime 1.5, 2.8.

### Compression: Bollinger Bandwidth percentile
- **Classification:** D; none for direction.
- **Definition:** BandWidth = (upper − lower)/middle = 2kσ_n/SMA_n (k = 2 → 4σ_20/SMA_20). A "squeeze" is BandWidth at a low percentile of its history (for example ≤ 20th over 250 bars).
- **Market mechanism:** Low dispersion of closes = quiet market, expected to expand.
- **Mathematical implementation:**
  - BW_t = 4·σ_20(C)/SMA_20(C) (Pine `ta.bbw` returns this × 100; docs).
  - Important property: σ of *close levels* around their mean mixes volatility and trend. A linear trend of slope b per bar over n bars contributes b·√((n² − 1)/12) to σ even with zero noise. A quiet, steady trend can read as "wide"; a choppy, active range can read as "narrow". BandWidth is not a clean volatility measure.
  - Percentile: `ta.percentrank(bbw, 250)`.
  - Knowable at close t.
- **Required data:** closes.
- **Pine v6 availability:** `ta.bbw(series, length, mult)`, `ta.bb`; O(1); percentrank O(N). Feasible.
- **Proxy limitations:** see the trend contamination above; also time-of-day contamination intraday.
- **Useful when:** display.
- **Fails when:** used for direction, or as a volatility forecast competing with the level pair.
- **Validation experiment:** Covered by VOL-X4.
- **Existing evidence:** [R6-T2] Forward 12-bar range after BBW percentile ≤ 20, as a multiple of the mean, ATR14 unit: 5m 1.00-1.11, 1H 1.11-1.22, BTC 1.10, EUR 1.29, daily 1.07; blended unit 0.80-0.97 on 5m and 1.03-1.13 on 1H. Practitioner sources describe the squeeze as direction-neutral; no peer-reviewed directional test was found (study: quant_regime R23).
- **APEX recommendation:** **EXCLUDE** as an input; the V-axis supersedes it. Redundancy: overlaps the compressed state and the efficiency axis (because of trend contamination).
- **Sources:** Pine v6 reference `ta.bbw` (opened). StockCharts Bollinger squeeze page [study citation]. Study: quant_regime 1.5, R23. R6-T2.

### Compression: TTM-squeeze proxy (Bollinger inside Keltner)
- **Classification:** D; none for direction.
- **Definition:** "Squeeze on" when the Bollinger Bands (20, 2σ) lie inside the Keltner Channel (20, 1.5·ATR); "fires" when they leave it. A momentum histogram supplies the direction in the original method (Carter).
- **Market mechanism:** Same as BandWidth.
- **Mathematical implementation:**
  - With a common basis, BB inside KC ⇔ 2σ_20(C) < 1.5·ATR_20 ⇔ **σ_20(C) / ATR_20 < 0.75**. Pine's `ta.bb` uses an SMA basis and `ta.kc` an EMA basis, so compare the widths directly, not the bands.
  - The ratio σ(close levels)/ATR measures how far price wanders relative to bar activity. It is low when bars are active but net displacement is small, i.e. partly an **efficiency** (range-bound) measure, like the Choppiness Index.
  - "Fire" event: squeeze off at close t after ≥ 6 bars on.
  - Knowable at close t.
- **Required data:** OHLC.
- **Pine v6 availability:** `ta.stdev`, `ta.atr` or `ta.kc` (docs: `ta.kc` uses `ta.ema` of TR when useTrueRange = true). O(1). Feasible.
- **Proxy limitations:** as BandWidth; also double-counts the efficiency axis.
- **Useful when:** as the trigger of an optional "volatility expansion" alert whose text says direction is not forecast (study: REG-5).
- **Fails when:** used for direction.
- **Validation experiment:** VOL-X4.
- **Existing evidence:** [R6-T2] Forward range after squeeze-on bars, ATR14 unit: 5m 0.91-1.08, 1H 0.98-1.10, BTC 1.03, daily 1.00-1.08. Direction: see the next entry.
- **APEX recommendation:** **INCLUDE-OPTIONAL** only as an alternative trigger of the expansion alert (off by default). Not a score input. Redundancy: compressed V-state and low efficiency.
- **Sources:** Barchart TTM Squeeze page [study citation]; Pine v6 reference `ta.kc` (opened). R6-T2.

### Breakout from compression vs extension in an expanded market
- **Classification:** C for any directional claim (none), A for the volatility-path difference (moderate).
- **Definition:** Spec 9 requires the engine to "understand that a breakout in a compressed market differs from an extension in an already expanded market". This entry defines both events mathematically and states which differences are supported.
- **Market mechanism:**
  - Compression: quiet tape, thin participation, a fast volatility estimate below the slow one. A break of a reference level is a volatility event; the fast unit under-forecasts what follows.
  - Expansion: active tape, the fast estimate above the slow one, price already far from its mean. Further extension uses a unit that over-forecasts what follows.
  - The other side: in both cases, resting liquidity at the level (stops and breakout orders) is consumed. Whether price continues depends on later order flow, which OHLCV does not reveal.
- **Mathematical implementation:** At the confirmed breakout bar t, with reference level B (a Donchian-N extreme, a liquidity pool or a range edge) and direction δ = +1 (up) or −1:
  - Break: δ(C_t − B) > 0 at close t (close-confirmed), first such close after ≥ 5 bars without a same-side break.
  - Pre-break volatility state: z_{t−1} from the V-axis (deseasonalised fast/slow log ratio).
  - Break-bar size in fast and slow units: m^f_t = TR_t / A14_{t−1}, m^s_t = TR_t / u_{t−1}.
  - Penetration: π_t = δ(C_t − B) / u_H,t.
  - Stretch: S_t = δ(C_t − EMA20_t) / u_H,t.
  - Expected forward range ratio: Q_t = E[R_{t,H}] / (κ·A14_t·√H) ≈ √(V_t(H) / (H·σ²_A14)), where R_{t,H} = max H − min L over t+1..t+H.
  - **Breakout from compression:** z_{t−1} ≤ −0.43 and m^s_t ≥ 1. Then the forecast ratio Q > 1 (V(H) > H·σ²_A14): the forecast is more movement than ATR14 suggests, in **both** directions. Touch probabilities for pools on both sides rise and the cone widens.
  - **Extension in an expanded market:** z_{t−1} ≥ +0.43 and S_t ≥ 2. Then the forecast ratio is Q < 1: less movement than ATR14 suggests. Distances measured in ATR14 look small and overstate reachability; the study measured the engine's touch probability as 5.5-8.2 pp too high in the expanded tercile (quant_regime 2.6).
  - In both cases the operational difference is Q, i.e. which unit converts distance into reachability. The engine should use u_H = √V(H) and not reason from the label.
  - **What the data support** [R6-T7]: the forward range after compression breakouts is larger than after expanded-state breakouts, but by less than the label suggests, and the stretched-extension subgroup is *not* reliably below 1 in ATR14 units (evidence below). Q is a forecast to be scored, not a fact.
  - **What is not implied:** a higher probability of continuation for either event.
  - Knowable at close t (break confirmation); the state uses t−1 values, so nothing is backdated.
- **Required data:** OHLC, time.
- **Pine v6 availability:** O(1) from VOL quantities. Feasible.
- **Proxy limitations:** "Breakout" from OHLC cannot tell initiative order flow from stop cascades.
- **Useful when:** sizing the cone and the touch probabilities after a break; labelling the event honestly ("compression break: range expansion likely, direction not forecast").
- **Fails when:** used as a continuation signal.
- **Validation experiment:** VOL-X4 (section 8).
- **Existing evidence:** [R6-T2] Donchian-20 fresh close breaks, ±1 ATR race in the break direction within H (n-weighted; null in brackets). The T2 groups were defined from proxies: "compression" = BBW percentile ≤ 20 or squeeze on at t−1; "expanded" = raw V-state expanded or ATR percentile ≥ 80 at t−1.
  - 5m (6 series, H = 12): from compression 0.519 (n 1,911) [0.500]; in expanded volatility 0.496 (n 1,121) [0.482]; normal 0.459 (n 1,313) [0.506].
  - 1H (5 series, H = 12): 0.543 (n 504) [0.477]; 0.492 (n 285) [0.521]; 0.500 (n 424) [0.506].
  - BTC 1H: 0.503 (n 1,523) [0.492]; 0.486 (n 562) [0.510]; 0.476 (n 840) [0.505].
  - Daily SPX + NDX (H = 10): 0.503 (n 193) [0.470]; 0.535 (n 120) [0.531]; 0.560 (n 169) [0.469].
  - Random walk: 0.503 / 0.518 / 0.487.
  - Reading: differences of −5 to +7 pp, of mixed sign across families, mostly within 2 SE of the null (SE ≈ 0.011-0.05), with 12 cells tested. No robust directional difference.
  - What is robust in T2: stretch at the break is 1.69-1.88 ATR after compression vs 2.04-2.44 ATR in expanded tape. The 12-bar forward range in ATR14 units is larger after compression breaks (1H 4.65 vs 3.28), and the null reproduces it (4.61 vs 3.49).
  - [R6-T7] **The documented definitions** (deseasonalised z at t−1; EXP-STRETCH adds |C − EMA20| ≥ 2 ATR14), with the forward 12-bar range divided by each unit and relative to its all-bar mean (null in brackets where informative):
    - 5m (6 series, n 280-352 COMP and 150-216 EXP per series). ATR14 unit: COMP 1.08-1.22, EXP 0.95-1.03, EXP-STRETCH 0.99-1.19. Clock unit √V(H): COMP 1.03-1.13, EXP 0.95-1.02. COMP/EXP ratio: 1.10-1.18 (ATR14), 1.01-1.15 (clock). The blended unit reverses the ratio (0.89-0.99) because it over-corrects.
    - 1H (5 series, n 55-104 per group). ATR14: COMP 1.02-1.15, EXP 0.88-1.02, EXP-STRETCH 0.92-1.10. Clock: COMP 1.00-1.05, EXP 0.89-1.01.
    - BTC 1H (n 1,360 / 678 / 435): ATR14 1.14 / 1.03 / 1.14; clock 1.12 / 1.03 / 1.13.
    - Daily SPX/NDX: the ratio reverses (COMP 0.92-0.99, EXP 1.02-1.04).
    - **Constant-volatility random walk** (60,000 bars): ATR14 COMP 1.05, EXP 0.93 (ratio 1.13); clock-form unit 1.07 / 0.92.
    - The sign-flip nulls reproduce the real ratios (5m null COMP 1.07-1.18, EXP 0.96-1.00 in ATR14).
  - Reading of T7:
    - Most of the "compression breaks run further than expansion breaks" effect in ATR14 units comes from estimator noise in short-window units: an underestimated σ looks like compression and is followed by "more than expected" movement. Genuine mean reversion adds a few percent on 5m and 1H.
    - The clock unit removes part of the gap; on daily data the effect reverses.
    - The practical rule stands (score the unit, widen the cone after compression), but the magnitude is small, and "extension in expanded tape → less movement" is not supported in ATR14 units on 5m.
  - [R6-T7] Direction under the documented definitions: race COMP minus null is −2.8 to +1.0 pp on 5m. On 1H, COMP is below the null in all 5 series (real 0.44-0.54 vs null 0.52-0.59; mean −5.4 pp, pooled z ≈ −1.7), the opposite sign to T2's BBW-based +6.6 pp. BTC COMP 0.503 vs 0.502. The sign changes with the definition of "compression": noise.
  - Study: NR7 breaks 0.482-0.515 (above); displacement bars 0.484-0.548 (quant_regime 2.8); MNQ: Asia-session expansion bars *reverse* at the next bar (T = −10.96) and ORB long T = 1.17-1.50 fails walk-forward (Mesfin 2026, study-verified).
- **APEX recommendation:** **INCLUDE-CORE** as a volatility-path classification in VOL/REG. It drives a reason code and an optional label, and it selects nothing by itself: the unit u_H and the cone width come from the forward-variance model, scored per chart (VOL-X1), not from the label. **EXCLUDE** any directional or continuation weight in BIAS, DOL or SETUP. Redundancy: displacement bars, NR7 breaks and squeeze fires are the same event family.
- **Sources:** Study: quant_regime 1.5, 2.6, 2.8, REG-5, REG-7; Mesfin (2026) arXiv:2605.04004 [study-verified]. R6-T2, R6-T7.

### Gaps (session, weekend, overnight, roll)
- **Classification:** E (mechanics); strong. Gap-fill magnetism: C.
- **Definition:** A discontinuity between the previous close and the next open: the CME daily halt (17:00-18:00 ET) and weekend, every RTH open on equity and cash-index charts, spot-FX weekends, and continuous-futures roll jumps.
- **Market mechanism:** News accumulates while trading is closed and is priced at the reopen. Roll gaps are a data artefact (the price of a different contract).
- **Mathematical implementation:**
  - Gap bar: (τ_t − τ_{t−1}) ≥ max(2·chartS, 1800 s), or a session-open bar on RTH-only data.
  - Gap size: g_t = ln(O_t / C_{t−1}); in units: γ_t = (O_t − C_{t−1}) / u_{t−1}.
  - The gap enters TR and the GK + gap proxy; the clock gets an "open" bucket on session-limited charts (study: asset_specific ASSET-9).
  - Roll guard: exclude from learning any bar with |O_t − C_{t−1}| > 4·A14_{t−1} that coincides with a back-adjustment change (study: CAL-10, ASSET-4).
  - Gap-through of a level: open beyond the level's near edge (study: asset_specific).
  - Knowable at the open of t (the gap is known at the first tick; use it at close t for confirmed logic).
- **Required data:** OHLC, time, session; back-adjusted request for roll detection.
- **Pine v6 availability:** `time`, `ta.change(time)`, `ticker.modify(..., backadjustment = backadjustment.on)` with one extra `request.security` (study: asset_specific). Feasible.
- **Proxy limitations:** Pine cannot see the overnight auction or pre-market volume on RTH charts.
- **Useful when:** variance accounting, gap-through handling of levels, risk warnings ("gap risk until the reopen").
- **Fails when:** treated as a magnet.
- **Validation experiment:** Hypothesis (risk, not direction): "Including the squared gap in the per-bar proxy improves QLIKE of the next-day variance forecast on equity, cash-index and CME charts." Metric: QLIKE with vs without the o² term. Pass: improvement on ≥ 80% of gappy series. Partial evidence: R6-T1 (GC 5m −11.4% vs +965% without).
- **Existing evidence:**
  - Variance: GOOG daily, overnight return = 38% of daily return variance (study: asset_specific).
  - Gap-throughs: 38% of PD-level takes on CME Sunday opens are gap-throughs vs about 3% on weekday 18:00 opens (study: asset_specific).
  - Gap fills (contested): S&P cash gaps fill −26.8 pp *below* the mirror level; EURUSD weekend +0.2 pp; BTC CME gap 4-week fill 86.7% vs mirror 89.4% (study: session_stats). Prior RTH close as a target +3.4 ± 1.3 pp (n 968) and gaps ≥ 0.5 ATR fill +7.4 pp (z 2.2) on CME (study: price_action, citing ICTPD). Plastun et al. (US indices 1928-2018): gap-day continuation, against the fill myth (study-verified via search).
- **APEX recommendation:** **INCLUDE-CORE** for variance (TR, GK + gap), gap-through level handling, roll exclusion and RISK warnings. Gap-fill targets belong to the DOL/PD-array specialist, gated by their own evidence; volatility contributes no magnet weight. Redundancy: gap variance is already inside TR; do not add a separate gap volatility term.
- **Sources:** Study: asset_specific 1.4-1.5, session_stats (gaps), price_action finding 10, calib_ml CAL-10. Plastun, Sibande, Gupta & Wohar (2020) [study-verified]. R6-T1.

### Abnormal moves (robust z of true range)
- **Classification:** A; moderate.
- **Definition:** A bar whose true range is extreme relative to the recent distribution, measured robustly so that the extreme does not inflate its own yardstick.
- **Market mechanism:** News, liquidations and stop cascades produce jumps. In crypto, 88% of forced selling in the October 2025 cascade landed within 30 minutes of onset (study: orderflow_micro / academic_sr). Jumps cluster and raise volatility for hours (Ederington & Lee: about 15 minutes well above normal, elevated for hours; study: ict_time).
- **Mathematical implementation:**
  - Deseasonalise first: TR*_t = TR_t / ŝ(τ_t) (clock factor in price units), else every session open is "abnormal".
  - Robust z in logs (TR is right-skewed): z_t = (ln TR*_t − med_N) / (1.4826·MAD_N), with med_N and MAD_N computed over bars t−N..t−1 (N = 100, excluding bar t).
  - Abnormal ⇔ z_t ≥ Z*, where Z* is adaptive: the 99.5th percentile of z over the last 2,000 bars, floored at 3. A fixed threshold is not universal:
    - [R6-T2] For the *linear, not deseasonalised* z of TR, P(z ≥ 5) is 2.1-4.0% on 5m CME, 1.7-3.2% on 1H, 3.0% BTC, 1.5% EUR and 0.9-1.3% daily, vs 0.15% on a Gaussian random walk. P(z ≥ 8) is 0.3-1.75% vs 0.00%.
    - [R6-T7] For the *documented* deseasonalised log-TR z, P(z ≥ 3) is 0.67-1.09% on 5m, 0.86-1.15% on 1H, 1.25% BTC, 1.02% EUR and 0.50-0.61% daily, vs 0.10% on the random walk. P(z ≥ 4) is 0.14-0.37% intraday vs 0.00%.
    - The log scale tames TR's right skew, so the floor of 3 flags roughly the top 1% of intraday bars.
  - Knowable at close t (a live preview may flag intrabar but must not feed confirmed logic).
- **Required data:** OHLC, time.
- **Pine v6 availability:** `ta.median` and a median of absolute deviations are O(N log N) per bar; with N = 100 this is acceptable. Alternatively a running quantile estimator. `ta.percentile_nearest_rank` for Z*. Feasible.
- **Proxy limitations:** OHLC cannot separate a jump inside a bar from a fast continuous move. A spliced-contract or bad-print bar looks like a shock; pair the flag with the roll and data-integrity guard.
- **Useful when:** (1) capping the influence of the bar on learned levels (winsorise: TIME-3 caps updates at 25× the level); (2) widening the forecast cone and lowering Forecast Quality for the next k bars; (3) a "SHOCK" reason code; (4) suppressing breakout alerts on the bar.
- **Fails when:** used for direction.
- **Validation experiment:** VOL-X5 (section 8).
- **Existing evidence:**
  - **Magnitude** [R6-T2]. After linear z ≥ 4, the forward 12-bar range in prior-ATR units is:
    - 5m 4.6-5.3 vs 3.8-4.1 for all bars (+15% to +36%);
    - 1H 4.19-4.61 vs 4.06-4.27 (only +3% to +12%);
    - BTC 4.59 vs 3.98 (+15%);
    - daily 4.46-4.48 vs 3.54-3.59 (+25%).
    - The null reproduces all of these, so the effect is clustering, not direction.
  - **Direction, bounded race** [R6-T2]. ±1 ATR race in the shock direction (sign of C − O):
    - 5m 0.479-0.527 (n 549-898 per series; null 0.463-0.519);
    - 1H 0.446-0.568 (n 119-332);
    - BTC 0.526 ± 0.009 (n 3,204; null 0.500 ± 0.009);
    - EUR 0.466 (n 129); daily 0.482-0.512 (n 82-112).
  - **Direction, mean close-to-close move** [R6-T7]: the move over the next 12 bars in the shock direction (sign of C_t − C_{t−1}), in ATR14_t units, with day-clustered SEs. Pooled across series assuming independence; the index futures are correlated (about 1.9 effective symbols of 4), so the pooled z overstates.
    - 5m, linear z ≥ 4: per series +0.04 to +0.39, pooled **+0.16 ± 0.06** (null +0.03 ± 0.05). Documented z ≥ 3: index futures +0.41 to +0.63 (SE 0.31-0.39), CL −0.32, GC −0.39; pooled +0.22 ± 0.13 (null −0.01 ± 0.12).
    - 1H, linear z ≥ 4: all 5 series negative, −0.11 to −0.49, pooled **−0.27 ± 0.07** (null +0.06 ± 0.08). Documented z ≥ 3: −0.25 to −0.74, pooled −0.50 ± 0.15 (n 36-65 per series).
    - BTC 1H, linear z ≥ 4: **+0.21 ± 0.06** (n 3,196; null −0.01 ± 0.05). Documented z ≥ 3: **+0.35 ± 0.11** (n 870; null −0.19 ± 0.09). Race 0.527 ± 0.009 and 0.546 ± 0.017 (nulls 0.493 and 0.485). This is the only cell where the bounded race and the mean move agree.
    - Daily SPX/NDX: −0.37 and −0.45 (SE 0.25 each; n 75-105). EURUSD: +0.02 ± 0.24.
  - **Reading.** The mean move after shocks is small, has the opposite sign on 5m and 1H index futures in the same months, and mostly does not show up in the bounded race. It is fat-tail-driven and timeframe-specific. No universal directional rule exists. BTC (8 years, one asset, one venue) shows a consistent shock-continuation lean that needs replication on other coins and venues (VOL-X5b).
- **APEX recommendation:** **INCLUDE-CORE** (VOL shock flag → FQ, FCST, CAL winsorising, UI reason code). No directional weight by default. A per-chart learned directional term is allowed only through the BIAS learner with zero prior (10_momentum.md), never as a fixed rule.
  - Cone widening after shocks is gated per timeframe family by VOL-X5: the 1H magnitude effect (+3% to +12%) is too small to justify it on current data.
  - Redundancy: displacement bars (the DOL Engine's `dispUp/dispDn`, lines 902-903 of the frozen copy) are a subset of the same event. Keep displacement only for its structural role (FVG quality), not as volatility or direction.
- **Sources:** Study: ict_time 1.12 (Ederington & Lee), academic_sr finding 6, quant_regime 2.8, x1_tv_validation (effective symbols). R6-T2, R6-T7.

### Trend, range and transition regimes (efficiency axis) with adaptive thresholds and hysteresis
- **Classification:** E as a description of the last window; C as a forecast; weak.
- **Definition:** A label for whether recent price movement was directional (trend), back-and-forth (range), or in between / changing (transition).
- **Market mechanism:** Traders expect different behaviour in trends and ranges. The tests show the label describes the window that just ended and does not forecast which side is taken next beyond distance geometry.
- **Mathematical implementation:**
  - Kaufman efficiency ratio (signed): sER_n = (C_t − C_{t−n}) / Σ_{i=t−n+1}^{t} |C_i − C_{i−1}| ∈ [−1, 1]; ER = |sER|; n = 20. Guard a zero path.
  - **Noise-floor-calibrated threshold (adaptive and universal):** under a driftless random walk ER_n ≈ |Z|·√(π/(2n)) (study: quant_regime 1.1). A threshold with false-positive rate α on a random walk is θ_n(α) = z_{1−α/2}·√(π/(2n)). For n = 20: θ(10%) = 0.46, θ(5%) = 0.55. The study's θ = 0.40 is exceeded on 15.7% of random-walk bars. ER is scale-free, so the same θ works on every instrument and timeframe.
  - Range threshold: ER < 0.15 (40% of random-walk bars, so "range" is the common state).
  - **Hysteresis (Schmitt trigger) and dwell:** enter TREND at ER ≥ θ_in = 0.46 with sign s; stay while ER ≥ θ_out = 0.36 and the sign is unchanged; enter RANGE at ER < 0.15, stay while ER < 0.20; otherwise MIXED. A change is accepted only after the new condition holds for c = 2 consecutive confirmed bars **and** at least D = 5 bars since the last change.
  - **Transition state:** TRANSITION for m = 5 bars after any change of the E-state, or while the V-state moves from COMPRESSED to EXPANDED.
  - Alternative adaptive form (tested): percentile thresholds of |ER| over 500 bars (enter 85th, stay 70th; range ≤ 30th, stay ≤ 45th). By construction it puts a fixed share of bars into each state, so it says nothing about whether this instrument trends more than a random walk. The noise-floor form is preferred.
  - Knowable at close t (the label at t uses bars ≤ t).
- **Required data:** closes.
- **Pine v6 availability:** `math.sum(math.abs(ta.change(close)), n)`, `ta.change(close, n)`, `var int` state. O(1). Feasible.
- **Proxy limitations:** None beyond the bar sampling.
- **Useful when:** display ("REGIME TREND ▲ · ER .52 · VOL CMP"); stratifying the accuracy ledger (REGIME RNG / MIX / TREND-WITH / TREND-AGAINST; study: REG-2), which lets each chart test the "trends continue" claim on its own data; narrowing the counter-draw penalty to efficient trends (study: REG-4, ×0.85).
- **Fails when:** used to steer target choice or drift. Study: D-first selection loses 9-12 pp of first-touch accuracy intraday; drift worsens log-loss in every regime; trend-state rows never help (quant_regime 2.4-2.6).
- **Validation experiment:** VOL-X6 (section 8).
- **Existing evidence:**
  - [R6-T3], with the *tested* rule (enter 0.40, stay 0.32, range < 0.15 / stay < 0.20, dwell 5, no confirmation):
    - Label changes per 1,000 bars: naive thresholds 248-261 (median dwell 2-3 bars); this rule 105-110 (median dwell 7); percentile thresholds 97-111.
    - Persistence at lag H (Cohen's kappa) on 5m/1H/BTC/EUR: naive +0.04 to +0.09, this rule +0.03 to +0.07, percentile +0.01 to +0.06; **random walk +0.05 to +0.06**.
  - [R6-T7], with the *documented* rule (enter 0.46, stay 0.36, 2-bar confirmation, dwell 5):
    - 77-85 changes per 1,000 bars on every series (5m, 1H, BTC, EUR, daily); median dwell 9-11.
    - Kappa at lag H: −0.015 to +0.06 (random walk: 80.5 changes, kappa +0.017).
  - Hysteresis makes the display 2.4-3.1× calmer than naive thresholds. It adds no information, and none was expected, because label persistence is at the random-walk level with any rule.
  - Study: corr(ER20(t), ER20(t+20)) −0.04 to +0.01 on 23 series; the sign-flip null gives the same (quant_regime 2.2). With-HTF-trend excess over geometry: nothing clears 2σ against its null on five families (quant_regime 2.3).
  - Study: in efficient trends the nearer pool is the with-trend pool 76-82% of the time (null 78-83%): "the draw continues" is geometry (quant_regime finding 3).
- **APEX recommendation:** **INCLUDE-CORE** in REG as a descriptive label and a ledger stratifier, with zero directional weight by default. Any directional use must be learned per chart with zero prior weight and shrinkage (study: REG-6). Redundancy: ER, ADX, CHOP, R² of a regression and the TTM squeeze all measure efficiency; use ER only.
- **Sources:** Kaufman, *Trading Systems and Methods*; TA-Lib ER (study-verified). Study: quant_regime 1.1, 2.2-2.6, REG-2/3/4/6. R6-T3.

### Alternative regime classifiers: ADX, Choppiness Index, Hurst and variance ratio, Markov switching
- **Classification:** C; none (as regime switches at chart windows).
- **Definition:** ADX ≥ 25 = trend (Wilder); CHOP ≤ 38.2 = trend, ≥ 61.8 = chop (Dreiss); rolling Hurst > 0.55 = persistent; hidden-Markov or Markov-switching states (Hamilton 1989).
- **Market mechanism:** Same claim as the efficiency axis.
- **Mathematical implementation:**
  - CHOP_n = 100·log₁₀(Σ_n TR / (HH_n − LL_n)) / log₁₀(n).
  - Variance ratio VR(q) = Var(q-bar returns) / (q·Var(1-bar)); Hurst H ≈ 0.5 + ln VR(q) / (2 ln q). Homoskedastic SE of VR(4) on 96 bars ≈ 0.19 (study).
  - ADX: see 10_momentum.md.
  - Knowable at close t.
- **Required data:** OHLC.
- **Pine v6 availability:** `ta.dmi`; CHOP and VR by rolling sums; a 2-state forward filter is feasible but costly to calibrate. Feasible.
- **Proxy limitations:** Estimator noise dominates at chartable windows.
- **Useful when:** never as a switch; VR is useful as a persistence diagnostic over long samples (10_momentum.md).
- **Fails when:** always as a switch. Random-walk noise floors (study: quant_regime 2.2): ADX ≥ 25 on 38% of bars, CHOP ≤ 38.2 on 21%, rolling Hurst > 0.55 on 12-16% (SD 0.069); none has next-window persistence; ADX ≥ 25 as a gate on the draw costs 2.5-3.5 pp.
- **Validation experiment:** None proposed; rejected on existing evidence.
- **Existing evidence:** As above. Statistical jump models with realised-volatility features give persistent states in and out of sample, and those states are volatility states (Nystrup, Kolm & Lindström 2020; study-verified).
- **APEX recommendation:** **EXCLUDE**. Redundancy: duplicates the efficiency axis with more noise.
- **Sources:** Study: quant_regime 1.2-1.4, 1.9, 2.2, section 5. Hamilton (1989) [study citation].

### Intraday volatility clock (time-of-day and weekday seasonality)
- **Classification:** A; strong.
- **Definition:** The deterministic pattern of volatility by time of day and weekday, learned per symbol, which turns bar counts into "business time".
- **Market mechanism:** Scheduled news, exchange opens and closes, and participant geography concentrate trading in known windows. Ederington & Lee (1993) show that scheduled announcements cause most of the time-of-day and day-of-week pattern in rates and FX futures (study: ict_time).
- **Mathematical implementation:**
  - Model (Andersen & Bollerslev 1997; Engle & Sokalska 2012): r_t = σ_day·s(τ_t)·z_t; integrated variance over the horizon V(H) = Σ_{k=1}^{H} σ²_day·s²(τ_{t+k}).
  - Estimation (study: TIME-3, robust form): buckets of max(30 min, chart TF) keyed to the **exchange or New York time zone, never UTC**; weekday factor; additive EWMA of the deseasonalised ratio x_t / L_s with a cumulative-mean warm start (1/n), floors (factor ≥ 0.05, weekday ≥ 0.2), a ratio cap of 50 and a level-update cap of 25×; daily renormalisation so the bar-weighted mean factor is 1; memory 40 days.
  - Forward walk over **future bars**: `time(timeframe.period, bars_back = -k)` (docs: expected timestamp for −1 to −500) or the open-cell walk that skips cells with fewer than 0.3 × the expected count (halts, weekends, closed hours).
  - Horizon gate: the clock matters when H × timeframe is shorter than about one day.
  - 24/7 crypto: 7 × 48 buckets; known spikes at the 00/08/16 UTC funding times (Hansen, Kim & Kimbrough 2024).
  - Knowable at close t.
- **Required data:** OHLC, time, exchange time zone.
- **Pine v6 availability:** `hour(time, tz)`, `minute`, `dayofweek`, `var` arrays (≤ 336 floats + counts), one O(H) walk per bar. No request. Feasible.
- **Proxy limitations:** Pine has no holiday calendar; early closes overstate V. The US/UK DST mismatch weeks (2026: 8-29 March and 25 October-1 November) smear London-keyed buckets for about four weeks a year when keyed to New York time.
- **Useful when:** every intraday horizon calculation: touch probabilities, ETA, race σ_eff, hysteresis scaling (stickier when the coming bars are quiet; study: TIME-5), low-liquidity detection, deseasonalising the V-axis and the shock z.
- **Fails when:** jump-dominated or spliced series (GC 1H −9.8% Brier); hence scorecard gating.
- **Validation experiment:** VOL-X2 (section 8).
- **Existing evidence:**
  - Size (study: quant_pot 1.8, researcher A's measurements): ES 5-minute variance at 09:30 ET = 4.67 × the day mean, at 23:30 = 0.20 ×; NQ 09:30 = 6.17 ×; CL 09:30 2.17 × and 18:00 reopen 1.94 ×; GC max/min 6.7 ×. About 75% of daily S&P 500 variance falls in the 6.5 cash hours (Hansen et al. 2012, via the study).
  - Engine bias without a clock: 5m H = 30 observed touch 68.3% vs predicted 52.4% at 07:00 ET, 42.1% vs 52.3% at 11:00; mean |bias| 7.3 pp; 1H H = 12 8.4 pp (study: ict_time E17).
  - Gains: see "Horizon-matched volatility forecast". Keyed to New York time +3.9% vs UTC-keyed +3.5% Brier on a sample with only 5 post-DST weeks (study: ict_time 1.13).
  - The cash-open drive: ES/NQ/YM/RTY 20-minute windows starting 09:20-09:59 ET take the prior 60-minute high or low +10 to +15 pp more often than the clock predicts (60 days; SE 1.6-3.2 pp); absent in CL/GC (study: ict_time E25). A time-of-day empirical surface learns this; a pure clock cannot.
  - [R6-T1] GK + gap × clock vs ATR14: −13.3% QLIKE on 5m H = 12, −24.0% on 1H H = 6, +1.6% on 1H H = 24. This is an upper bound; see the caveats in the forecast-unit entry.
  - [R6-T7] A fully causal clock (expanding bucket means over past bars, New York-keyed 30/60-minute buckets, no weekday factor) is enough to deseasonalise the V-state. It turns 1H state persistence from negative (−0.05 to −0.20) to +0.24 to +0.33.
- **APEX recommendation:** **INCLUDE-CORE** (VOL) on intraday charts ≤ 4H, scorecard-gated as the probability unit ("Auto"), always used for deseasonalising state variables. Redundancy: it is the quantitative form of killzones, sessions and weekday effects; fixed killzone multipliers on top would double-count (study: TIME-5).
- **Sources:** Andersen & Bollerslev (1997) *J. Empirical Finance* 4 [study-verified shape]; Engle & Sokalska (2012) *J. Fin. Econometrics* 10(1) [study-verified]; Dacorogna et al. (1993) [study-verified]; Ederington & Lee (1993) *J. Finance* 48(4) [study-verified]; Hansen, Kim & Kimbrough (2024) *J. Fin. Econometrics* 22(1) [study-verified]. Pine v6 reference `time()` (opened). Study: ict_time 1.13, 2.2, TIME-3/4/5; quant_pot 1.8. R6-T1.

### Scheduled-event variance
- **Classification:** A; strong (mechanism), moderate (magnitudes).
- **Definition:** Extra variance concentrated in known release bars (CPI, NFP at 08:30 ET; FOMC at 14:00 ET; earnings for stocks).
- **Market mechanism:** Information is released at a known time; most of the price adjustment comes within about a minute, and volatility stays elevated for about 15 minutes and slightly for hours (Ederington & Lee; study).
- **Mathematical implementation:**
  - Manual event input (study: TIME-8): time T_e, window W (default 60 min), volatility multiplier x_e in **σ units** (default 2.0); buckets in [T_e, T_e + W) get variance × x_e² in the forward walk.
  - Add vs redistribute (study: x1_implied_vol X1-2): with a realised level, **add** the event variance; with a VIX1D level, **redistribute** the day's variance toward the release bar (VIX1D already prices the event day).
  - Auto-expiry once `timenow` > T_e + W.
  - Knowable before the event (a deterministic input).
- **Required data:** user input; optional term-structure detector from VIX1D/VIX.
- **Pine v6 availability:** `input.time`, `input.float`; `earnings.future_time` for stocks (study: x1_implied_vol). Feasible.
- **Proxy limitations:** Pine has no calendar. The NFP date rule ("third Friday after the reference week") breaks on holidays and shutdowns (study: ict_time 1.12).
- **Useful when:** event days on intraday charts.
- **Fails when:** stale or mistyped inputs; using the term-structure detector alone to drive variance (it hurt; study: x1_implied_vol 2.7).
- **Validation experiment:** VOL-X8 (section 8).
- **Existing evidence:** ES 1H: the 08:30 CPI/NFP bar carries 3.9 × (median 6.7 ×) the variance of the same hour on other days; FOMC 14:00 bar 4.8 × (median 8 ×) (n = 12 and 8). Adding event-hour variance to a realised level cuts event-window touch log-loss (H = 6) by 5.6% with variance multiplier m = 4 (σ × 2, the APEX default) and by 7.6% with m = 7 (study: x1_implied_vol 2.7: 0.6504 → 0.6138 / 0.6009). Redistributing instead of adding hurts the rest of the event day with a realised level but helps with VIX1D. Event days run about 2 × a 22-day RV forecast but only 1.06-1.15 × VIX1D (same source).
- **APEX recommendation:** **INCLUDE-OPTIONAL** (VOL, off by default; RISK shows "⚑ EVENT" when the window lies inside the horizon). Redundancy: the learned clock already holds the average release-hour variance; the event input adds only the day-specific excess.
- **Sources:** Ederington & Lee (1993, 1996) [study-verified]; Lee (2012) *RFS* 25(2) [study citation]. Study: ict_time TIME-8, x1_implied_vol X1-2, asset_specific ASSET-5.

### Low-liquidity periods
- **Classification:** E (they exist); moderate as measurable proxies.
- **Definition:** Times when few participants trade, spreads widen and prices can print or gap with little volume: the CME daily halt edges, Sunday reopens, the Asia session on US index futures, holidays and half days, the FX rollover window, crypto weekends.
- **Market mechanism:** Fewer liquidity providers means wider spreads and thinner books, so small orders move price and wicks can be unrepresentative. Pine has no bid/ask or depth data, so APEX can only infer thinness.
- **Mathematical implementation:** All of these are proxies and are labelled as such.
  - Clock thinness: λ_t = s²(τ_t) (the learned seasonal variance factor) ≤ 0.3, or the forward-variance ratio V(H)/(H·L_f) ≤ 0.5.
  - Relative volume where volume is reliable (exchange futures and stocks): RV_t = V_t / median(V in the same clock bucket over the last 20 days); thin if RV_t ≤ 0.3. Not for spot FX (tick volume from one venue) and not for multi-venue crypto without a consolidated feed.
  - Stub or holiday day: bars in the session < 35% of the normal count (study: asset_specific).
  - FX rollover window 16:55-17:15 New York; metals reopen 18:00-18:10 (study: asset_specific).
  - Zero-range share: fraction of the last 20 bars with H = L ≥ 0.25.
  - Knowable at close t (stub day only at the session end; use the live count for a provisional flag).
- **Required data:** OHLC, volume (optional), time.
- **Pine v6 availability:** O(1) except the per-bucket volume median (array per bucket); feasible.
- **Proxy limitations:** No spread, no depth, no queue data. Volume definitions differ by feed (spot FX tick volume is not traded volume).
- **Useful when:** widening hysteresis, lowering Forecast Quality, suppressing breakout and sweep alerts on thin bars, warning RISK that costs may exceed the expected move.
- **Fails when:** volume is missing or vendor-specific; holidays not detected until the day is over.
- **Validation experiment:** VOL-X10 (section 8).
- **Existing evidence:** Holiday and half days are compressed (median range/ADR ES 0.76, NQ 0.65), and their extremes are not weaker next-day targets (n = 11) (study: asset_specific). On EURUSD 1H the 17:00 rollover hour breaks a prior 24-bar extreme on 10% of days with a wick-only share 0.43 vs 0.52 median (study: asset_specific). Crypto weekend range taken at the weekday rate once distance is measured correctly (study: asset_specific). Bar-time freshness: TradingView serves CME data 10 minutes delayed without a real-time subscription (study: x1_internals).
- **APEX recommendation:** **INCLUDE-CORE** as a data-quality and tradeability flag (VOL → FQ, RISK, ALERT suppression), not as a score. Redundancy: the clock factor carries most of the information; volume is a confirmation where available.
- **Sources:** Study: asset_specific 1.3-1.5, ASSET-5/8/10; ict_time TIME-5; x1_internals finding 2.

### Implied volatility (VIX, VXN and others) as optional context
- **Classification:** A; strong at daily horizons, moderate intraday.
- **Definition:** The options market's forecast of volatility: VIX (SPX 30-day), VIX1D, VIX9D, VIX3M, VXN (Nasdaq-100), RVX, VXD, OVX (crude), GVZ (gold), Deribit DVOL (BTC).
- **Market mechanism:** Option prices aggregate traders' forecasts, including scheduled events, plus a variance risk premium (implied above realised on average; Carr & Wu 2009).
- **Mathematical implementation:** Follows study x1_implied_vol X1-1.
  - Per-day variance from the index: ivVar = (IV/100)² / A, A = 252 (365 for DVOL).
  - Fresh alignment: request `[close[1], time_close[1]]` on a 60-minute timeframe with `lookahead_on` and latch the value when the closed bar's New York close time is 16:00-16:30 (the official close). A plain daily `close[1]` request is one day stale from 16:15 to 09:30 and destroys VIX1D's edge.
  - Unit-preserving scale: κ = slow EWMA (half-life about 250 days) of L·bpd / ivVar, so the implied term enters in the realised model's units; never a hard-coded VRP constant.
  - Blend: L_b = L_f^{1−w}·(κ·ivVar/bpd)^w, w ∈ {0, 0.25, 0.5} chosen by the CAL scorecard; w = 0 if the symbol is unmapped.
  - Term-structure state VIX/VIX3M (or VIX9D/VIX) as a key for the probability scale.
  - Knowable at close t (confirmed history with `[1]` and lookahead_on).
- **Required data:** one to three extra symbols; CBOE data are delayed for most users (fine for the 16:15 close).
- **Pine v6 availability:** `request.security` with `ignore_invalid_symbol = true` (docs). v6 enables dynamic requests by default, so symbol strings can be series. The budget is 40 unique `request.*()` calls per script, or 64 on the Ultimate plan (docs: limitations, other timeframes and data); APEX must budget for 40. Feasible, partial (only mapped symbols).
- **Proxy limitations:** Mapping by root: ES/SPX/SPY → VIX family; NQ → VXN (untested natively; VIX used as proxy); RTY → RVX; YM → VXD; CL → OVX; GC → GVZ; BTC → DVOL. Beta-scaled VIX for stocks and FX was worse than plain ATR (study). MOVE is bp yield volatility, not price volatility (unit mismatch).
- **Useful when:** daily horizons; SPX-linked and RTY 1H charts; event-day detection cross-check.
- **Fails when:** stale alignment; ES/NQ 5m (no gain); unmapped symbols (clean no-op).
- **Validation experiment:** VOL-X7 (section 8).
- **Existing evidence:** 1-day touch on SPX: VIX1D −5.4%, VIX9D −3.4%, VIX −1.3% log-loss vs ATR14 (2022-26). Over the clock + fast realised level: ES 1H +0.5-0.6%, RTY 1H +1.3-1.6%, CL 1H +0.5%, BTC 1H +0.3-0.5%, NQ and ES 5m ±0.2% (n.s.). Realised daily variance is 0.51-0.66 × VIX² and 0.75 × VIX1D²; the term-structure-keyed scale gains +0.4 to +1.6% out of sample (study: x1_implied_vol). Pine proxies (VIX/VIX3M plus VIX-implied σ in ATR units) recover about 75% of the dealer-gamma range effect on SPX daily (study: x1_positioning).
- **APEX recommendation:** **INCLUDE-OPTIONAL** (VOL, off by default; Auto mapping, Custom symbol, Off). Expected-move bands as optional display context only. Redundancy: a second-order refinement of u_H; never an input to direction (no tested link to which pool is taken).
- **Sources:** Poon & Granger (2003) *JEL* 41(2); Blair, Poon & Taylor (2001); Busch, Christensen & Nielsen (2011); Carr & Wu (2009) *RFS* 22(3); Johnson (2017) *JFQA* 52(6); Albers (2025) *J. Futures Markets* 45(11) [all study-verified, x1_implied_vol §7]. Pine v6 reference `request.security` (opened).

---

## 4. Interactions and redundancy

**One latent quantity, many estimators.** TR, ATR (RMA or SMA), close-to-close σ, Parkinson, Garman-Klass, Rogers-Satchell, Yang-Zhang, GK + gap and implied volatility all estimate the same thing: the scale of price movement. APEX computes it once.

| Role | Single APEX object | What it replaces or absorbs |
|---|---|---|
| Per-bar variance proxy | x_t = GK + gap (log units) | Parkinson, GK, RS, YZ, close-to-close r² (kept only as the evaluation target) |
| Volatility level and clustering | L_f (fast) and L_s (slow) deseasonalised EWMAs | EWMA RiskMetrics, GARCH-lite, CARR |
| Seasonality | the clock s(τ), weekday factor | killzone multipliers, session volatility rules, raw-percentile "time of day" artefacts |
| Forecast unit | u_H = √V(H) (or √(A14·A100), or A14), chosen per chart | potSig, the ATR14 surface unit, volatility-tercile rows |
| Volatility state | V-axis z of ln(L_f/L_s) with hysteresis | ATR percentile, BBW percentile, TTM squeeze, NR7, ATR5/ATR100 |
| Abnormal bar | shock flag from the deseasonalised robust z | displacement-as-volatility, "news spike" detectors |
| Efficiency regime | ER20 with noise-floor thresholds | ADX, CHOP, Hurst/VR switches, R² of a regression, the squeeze's efficiency component |
| Event variance | manual input in σ units (optional IV redistribution) | separate "news volatility" multipliers |

**Known overlaps and how not to double-count them:**
1. **Compression measures overlap each other and the efficiency axis.** BBW mixes trend with volatility (σ of closes includes b·√((n² − 1)/12) from a slope b), and the TTM squeeze is σ_close/ATR < 0.75, which is low when price is range-bound. Both partly measure efficiency. APEX uses only the V-axis for compression and only ER for efficiency.
2. **The clock and time labels.** Killzone affinity multipliers, session-hour volatility rules and the clock all encode the same seasonality. Keep the clock; set fixed killzone multipliers to neutral (study: TIME-5).
3. **Unit and key.** Fixing the unit (u_H) removes most of what volatility-tercile rows captured; adding both dilutes samples and hurt in the study (15m −2.38% vs −4.06%). Use the unit; keep the V-state as an audit split, not a probability key.
4. **Shock and displacement.** A displacement bar (body ≥ 1.2 ATR) is usually a high-z TR bar. Counting it as a volatility shock and again as a directional impulse double-counts one bar; the directional part has no support (study: REG-7).
5. **Implied and realised.** The implied level is blended into the same level, with a weight chosen by proper scores. It must not also enter as a separate "fear" feature.
6. **Gap variance.** It is already inside TR and GK + gap; a separate gap-volatility term would count it twice.
7. **Low liquidity and the clock.** The thin-market flag is derived mostly from the clock factor; it adjusts quality and alerts, not the unit again.

**Volatility vs direction.**
- Every directional claim tied to volatility events tested null, tiny or sign-unstable: NR7 breaks, compression breakouts (the sign flips with the definition of compression), displacement, squeeze fires, and shocks (the mean move after a shock is +0.16 ATR on 5m and −0.27 ATR on 1H index futures over the same months) [R6-T2, R6-T7].
- The one consistent cell is BTC 1H shock continuation, from a single series.
- Volatility therefore enters BIAS with zero weight. Any shock-direction term must be learned per chart with a zero prior.
- Volatility enters DOL, FCST, RISK and FQ through the unit, the cone and quality.

---

## 5. Data requirements and assumptions

- **Always available in Pine:** OHLC, `time`, `time_close`, `syminfo.mintick`, `syminfo.timezone`, `syminfo.session`, `timeframe.*`, the expected future bar times (`time(..., bars_back = -k)`, −1 to −500).
- **Usually available:** volume (exchange futures, stocks). Unreliable or vendor-specific: spot FX (tick volume), CFDs, multi-venue crypto.
- **Optional extra requests:** implied-volatility symbols (1-3 requests), back-adjusted series for roll detection (1 request). The DOL Engine already uses 6 of the 40 unique requests (study: x1_implied_vol §1.1); the volatility module adds at most 4.
- **Not available:** bid/ask, spread, depth, queue position, a holiday calendar, an economic calendar, open interest (except via pasted inputs).
- **Assumptions:**
  - Bar highs and lows capture the continuous path maximum and minimum well enough for touches: the reflection identity P(touch within H) = 2.00 × P(finish beyond at H) holds on CME 5m and 1H bars at 0.5-4 ATR (study: quant_pot finding 4).
  - Volatility is persistent and mean-reverting (supported on every series tested).
  - The seasonal shape changes slowly (40-day memory); breaks are handled by scorecard gating and the slow level.
  - Returns are not Gaussian: robust statistics (median, MAD, percentiles) are used for thresholds; empirical surfaces carry the fat tails.
- **Warm-up:** ATR100 needs 100 bars; the clock needs about 5 days of buckets (study: `clkDy ≥ 5`) and falls back to the blended unit; the V-axis z needs about 500 bars of EWMA history. Until warm, FQ is lowered and the state shows "WARMING".
- **Confirmation timing:** every state variable is computed on `barstate.isconfirmed` bars and used from that close on. Live previews (the current bar's TR, a provisional shock flag) are labelled live and never feed confirmed alerts (spec 19.1).

---

## 6. Limitations and failure modes

**By asset class**
- **CME futures (ES, NQ, RTY, YM, CL, GC, SI).** The default continuous chart is unadjusted: roll gaps (ES +35-55 points, NQ +150-250 points per quarter; CL monthly; GC bi-monthly) must be excluded from learning. The daily halt 17:00-18:00 ET and the Sunday reopen create gap bars (38% of PD-level takes on Sunday opens are gap-throughs). TradingView's "regular" session for futures is the full Globex session; the RTH session is `us_regular` (study: asset_specific). Without a real-time subscription CME data are 10 minutes delayed.
- **Spot FX.** No central volume; tick volume only. The 17:00 New York rollover widens spreads and bid-plotted wicks can mislead the shock detector. Weekend gaps exist (48% of weeks have none). Volatility clock keyed to New York time; London buckets smear during DST mismatch weeks.
- **US equities and ETFs.** Every RTH open gaps; the overnight return carries about 38% of daily variance (GOOG). Earnings create known jumps (`earnings.future_time` gives the next date). Splits and dividends need adjusted data. ETF and cash-index charts have no overnight bars.
- **Cash indices (SPX, NDX).** No volume on many feeds; opens can equal the prior close on some vendors (the Yahoo-style daily index data used in R6-T1 had this quirk, which is one reason GK + gap did worse than GK on NDX daily).
- **Crypto spot and perpetuals.** 24/7: no gaps, so the clock needs 7 × 48 buckets; weekends are compressed (0.46 and 0.72 of a weekend-inclusive ADR on Saturday and Sunday in 2023-25); funding times 00/08/16 UTC add variance spikes; exchange-specific prints and wicks differ by venue. CME crypto futures went 24/7 on 2026-05-29 (study: asset_specific).
- **Thin markets and small caps.** Zero-range bars and missing minutes break pure range estimators (GC 5m example); GK + gap or TR must be used.

**By timeframe**
- **≤ 1 minute:** microstructure noise (bid-ask bounce) inflates range estimators; the clock still helps but the horizon in clock time is short (the study's 1-minute H = 30 showed the vol-time analytic worse than the surface).
- **5-15 minutes:** the clock dominates (−13% QLIKE); the blended unit over-corrects without time-of-day rows.
- **1-4 hours:** the fast window spans part of the day, so every raw state variable is clock-contaminated; deseasonalise. At H ≥ 24 on 1H the clock averages out.
- **Daily and above:** keep ATR14 (the blended unit hurt: +0.66% study, +2.3% to +8.7% R6-T1); GK/RS small gains (−0.6% to −2.6%); implied volatility helps most here.

**Session and DST issues**
- Key the clock and session windows to the exchange or New York time zone with IANA names, so DST is handled by the time functions, never by fixed UTC offsets (study: +3.9% NY-keyed vs +3.5% UTC-keyed Brier).
- Session membership on coarse bars uses the bar **open** time; on 1H futures charts the "09:30-12:00" range was wrong on 76% of days (study: ict_time E19). Volatility buckets must use bar open time consistently and coarse charts must merge buckets (bucket = max(30 min, chart TF)).
- Holidays and half days are not known in advance; the forward variance is overstated on them (a known limitation, shown as lower FQ once the day is detected as a stub).

**Model failure modes**
- Structural breaks (3× regime shifts) make learned clocks and percentiles stale for weeks; the slow level and the scorecard limit the damage.
- Jump-dominated series (GC 1H) defeat a fast-level z-surface; fall back to the ATR surface by scorecard.
- Overlapping horizons make sample sizes look larger than they are; use effective sizes (n/(0.6H), study) and block bootstraps.
- Fixed thresholds do not transfer across instruments (P(z ≥ 5) ranges from 0.9% to 4.0% of bars by series); use noise-floor or own-history thresholds.

---

## 7. Recommendations for APEX (ranked)

| Rank | Recommendation | Decision | Module | Why |
|---|---|---|---|---|
| 1 | Forward-variance unit u_H with per-chart selection among {ATR14, √(ATR14·ATR100), clock V(H)}; replaces `potSig` and ATR-unit surfaces | INCLUDE-CORE | VOL → DOL, FCST, RISK, CAL | Largest measured gains: −13% to −24% QLIKE intraday [R6-T1; offline clock, an upper bound]; Brier +3.9-5.5% and hour bias 7.3 → 2.1 pp (study) |
| 2 | Robust NY/exchange-keyed volatility clock (TIME-3 form) with real future-bar walk | INCLUDE-CORE | VOL | Removes −17..+11 pp hour bias; quantitative form of sessions and killzones |
| 3 | GK + gap per-bar proxy; never pure intrabar estimators; close-to-close only as evaluation target | INCLUDE-CORE | VOL, CAL | Pure Parkinson/GK collapse on gappy data (+965% QLIKE on GC 5m); close-to-close is worst everywhere |
| 4 | Deseasonalised V-axis (ln L_f/L_s z-score) with ±0.43/±0.30 hysteresis and dwell | INCLUDE-CORE | REG, CAL, UI | The only regime state that persists. Deseasonalised kappa at lag 12: +0.46..+0.55 (5m), +0.24..+0.33 (1H), +0.32 (BTC), vs +0.09 on a random walk. The raw state on 1H is the clock (kappa −0.05..−0.20) [R6-T7] |
| 5 | Shock flag from the deseasonalised robust log-TR z with an adaptive threshold | INCLUDE-CORE | VOL → FQ, FCST, CAL, UI | Tails 5-12× a random walk; forward range +15..+36% (5m, BTC, daily) but only +3..+12% (1H); mean direction changes sign by timeframe, so no direction weight [R6-T2, R6-T7] |
| 6 | Breakout-from-compression vs extension classification as a volatility-path label (reason code); the unit and cone come from the scored forward-variance model, not the label; zero directional weight | INCLUDE-CORE | VOL, REG, FCST | Answers spec 9 honestly: the difference is the forecast ratio Q = V(H)/(H·σ²_A14), not continuation. The empirical magnitude is small and partly estimator noise (random walk: 1.13×) [R6-T7] |
| 7 | Efficiency axis (ER20) with noise-floor thresholds (0.46 enter, 0.36 exit, 0.15/0.20 range), confirmation 2, dwell 5, transition window 5 | INCLUDE-CORE (descriptive) | REG, CAL, UI | Calm display: 77-85 flips per 1,000 bars vs 248-261 naive [R6-T7]. Used for ledger stratification only; no forecasting weight |
| 8 | Gap handling: TR everywhere, roll exclusion, gap-through rules, RISK gap warning | INCLUDE-CORE | VOL, RISK | Mechanics; avoids corrupting learned volatility |
| 9 | Low-liquidity proxy flag (clock factor, relative volume, stub day, rollover window) | INCLUDE-CORE (flag only) | VOL → FQ, RISK, ALERT | Honest tradeability; no bid/ask in Pine |
| 10 | Scheduled-event variance input (σ units, add vs redistribute) | INCLUDE-OPTIONAL | VOL, RISK | −7.6% event-window log-loss (study); needs manual input |
| 11 | Implied-volatility blend (mapped symbols, fresh latch, κ, w by scorecard), EM bands as display | INCLUDE-OPTIONAL | VOL, UI | Strong at daily horizons; +0.3 to +1.6% intraday over the clock |
| 12 | TTM-squeeze-off as an alternative trigger of the "Volatility Expansion" alert (direction not forecast) | INCLUDE-OPTIONAL | ALERT | Traders expect it; label honestly |
| 13 | Deseasonalised volatility percentile display; range percentile context | INCLUDE-OPTIONAL | UI | Context only |
| 14 | Volatility of volatility as a cone-widening factor | RESEARCH-ONLY | FCST, FQ | Untested |
| 15 | HAR forecast on daily charts | RESEARCH-ONLY | VOL | Mixed in R6-T1 (−6.7% SPX, +2.1% NDX at H = 5) |
| 16 | NR7, BBW percentile, squeeze, ATR percentile (raw) as inputs; ADX/CHOP/Hurst/HMM switches; ADR caps; GARCH MLE in Pine; SMA ATR | EXCLUDE | — | No directional evidence, clock contamination, noise floors, infeasibility |

---

## 8. Open questions and Phase 6 experiments

All experiments are pre-registered: the hypothesis, outcome, horizon, baseline, metric and pass criterion are fixed before the data are examined. Every test uses a 2-fold or walk-forward time split, block-bootstrap standard errors (block = max(H, bars per day)), the sign-flip null for any directional claim, and a multiple-testing note (Benjamini-Hochberg across the cells of each experiment). The Phase 6 data matrix: CME index futures (ES, NQ, RTY, YM), CL, GC (clean months only), EURUSD and GBPUSD, SPY or a large-cap stock, BTCUSD spot and a BTC perpetual, ETH and SOL spot; timeframes 5m, 15m, 1H, 4H, D.

"Sample" names the slice of the Phase 6 matrix each test uses. "In-sample status" reports what the study data already show for the current form; those data cannot confirm the hypothesis, because they were used to form it. Phase 6 must use data after 2026-04-15 or symbols not used here.

| ID | Hypothesis | Outcome | Sample | Horizon | Baseline | Metric and statistical test | Pass criterion | In-sample status |
|---|---|---|---|---|---|---|---|---|
| VOL-X1 | The per-chart forward-variance unit (best of ATR14, blend, *causal* clock) forecasts next-H realised variance better than ATR14 | RV_fwd = Σ r² over t+1..t+H | All intraday series and D; walk-forward with the scale c refitted on past data only | H = 12, 30, 60 bars | ATR14-RMA (QLIKE-scaled) | QLIKE difference with block bootstrap (block = max(H, bars/day)); MZ R² of log RV | Better on ≥ 80% of intraday series with the pooled 95% CI excluding 0; no worse than +1% on daily | Offline clock −13% (5m), −24% (1H H = 6) [R6-T1], an upper bound |
| VOL-X2 | The clock improves touch-probability calibration when H × TF < 1 day and is neutral beyond | Level at k ∈ {1, 2, 3} u touched within H | Intraday series, all hours | H = 12, 30, 60 | ATR14 empirical surface | Brier and log-loss, day-block bootstrap z; mean absolute hour bias | Brier gain > 1% with z ≤ −2 on ≥ 70% of series with H × TF < 1 day; hour bias ≤ 3 pp | Study: +3.9% to +5.5% Brier, bias 7.3 → 2.1 pp |
| VOL-X3 | The deseasonalised V-state persists at lag H on all intraday TFs; the raw state does not on 1H/4H | Tercile label at t vs t+H | Intraday series; iid random walk as benchmark | H = 12 and 1 day | Raw ATR5/ATR100 state; random-walk kappa | Cohen's kappa; block bootstrap CI | Deseasonalised kappa ≥ 0.2 and ≥ random-walk kappa + 0.1 on ≥ 80% of series, and > raw kappa on 1H/4H | Passes: 5m +0.46..+0.55, 1H +0.24..+0.33, BTC +0.32, EUR +0.21; random walk +0.09 [R6-T7] |
| VOL-X4 | Breakouts from compression and extensions in expanded tape (documented definitions) do not differ in continuation, but differ in forward range in ATR14 units by more than estimator noise | (a) ±1 u race in the break direction; (b) R_{t,H}/A14_t relative to its mean | All series; each paired with its sign-flip null and an iid random walk | H = 12 (intraday), 10 (D) | Sign-flip null; random-walk ratio | (a) race minus null, BH-adjusted across cells; (b) ratio of group means, block bootstrap CI | (a) no-effect outcome if |race − null| < 3 pp in ≥ 80% of cells (a ≥ 3 pp effect with q < 0.05 on ≥ 3 asset classes would be reported as a directional finding); (b) COMP/EXP ratio > random-walk ratio (1.13) with the CI excluding it | (a) holds; (b) 5m 1.10-1.18, i.e. barely above the random walk [R6-T7] |
| VOL-X5 | Shock bars predict higher forward range but no universal direction | (a) R_{t,H}/A14_{t−1} vs all bars; (b) ±1 u race and mean move in the shock direction | All series and nulls | H = 12 (intraday), 10 (D) | All bars; null | (a) ratio with block CI; (b) race − null and mean − null, day-clustered SE, BH-adjusted | (a) ratio ≥ 1.10 on ≥ 80% of the series in a timeframe family, else cone widening off for that family; (b) |race − null| < 3 pp | (a) passes 5m/BTC/D, fails 1H (3 of 5 below 1.10); (b) holds except BTC [R6-T2, R6-T7] |
| VOL-X5b | The BTC shock-continuation lean replicates on other crypto | Mean move and race in the shock direction | ETH, SOL 1H (spot), a BTC perpetual from another venue, 2025-26 | H = 12 | Sign-flip null | Mean − null with day-clustered SE; race − null | Both > 0 with z ≥ 2 on ≥ 2 of 3 series; otherwise treated as a one-series result | BTC 1H +0.21 ± 0.06 ATR, race +3.4 pp [R6-T7] |
| VOL-X6 | Hysteresis + confirmation + dwell cut regime-label flips by ≥ 50% and leave label persistence at or above the random-walk level | Label changes; kappa at lag H | All series; random walk | — | Naive thresholds; random walk | Flips per 1,000 bars; median dwell; kappa | Flips ≤ 50% of naive, median dwell ≥ 7 bars, kappa ≥ random-walk kappa − 0.03 (the label is descriptive; no information gain is expected) | Passes: 77-85 vs 248-261 flips, dwell 9-11 [R6-T7] |
| VOL-X7 | The implied-volatility blend (w by scorecard) improves touch log-loss over the clock + realised level on mapped symbols | Touch within H | ES/SPY, RTY, CL, GC, BTC with mapped IV symbols | H = 6, 12, 24 (1H); 1, 5 (D) | Clock + realised level (w = 0) | Log-loss with day-block CI | CI excludes 0 on SPX-linked 1H and daily; w = 0 chosen automatically where there is no gain | Study: +0.3% to +1.6% intraday, larger daily |
| VOL-X8 | Manual event variance (added to a realised level) improves event-window touch log-loss | Touch within H, for windows containing the release | ES, NQ, ZN-linked charts on CPI/NFP/FOMC days | H = 6, 12 (1H); 12, 30 (5m) | No event input | Log-loss on event windows, event-clustered SE; unchanged elsewhere | Event-window gain ≥ 3% and non-event loss change within ±0.5% | Study, ES 1H 2025-26 (12 CPI/NFP and 8 FOMC release bars): −5.6% (m = 4) and −7.6% (m = 7) |
| VOL-X9 | A volatility-of-volatility widening improves coverage of 80% H-bar move intervals | Close at t+H inside the interval | All series | H = 20, 60, 120 | Empirical quantiles without widening | Coverage error |cov − 0.80| and interval score; block bootstrap | Coverage error reduced by ≥ 25% with the interval score not worse | Untested |
| VOL-X10 | Touch-probability calibration error is larger in flagged low-liquidity periods, and the flag-driven FQ reduction is justified | Touch within H | Intraday series with volume (futures) and without (FX) | H = 12, 30 | Unflagged periods | Expected calibration error by flag, day-block CI | ECE(flagged) − ECE(unflagged) > 1 pp with the CI excluding 0 | Untested |

**Open questions**
1. Does the clock need separate shapes for the RTH and Globex parts of CME futures beyond what 30-minute buckets capture (cash-open drive)? The time-of-day surface learns the drive; the clock does not.
2. What is the best fast-level span per timeframe (study used potLen 50 bars; R6-T1 used EWMA 20)? To be chosen by the scorecard, not hard-coded.
3. Does the deseasonalised V-axis improve the per-chart probability scale enough to be a key on top of the unit? The study said no for raw volatility rows; deseasonalised rows are untested.
4. Can holidays be detected early enough (stub day after the first few bars) to correct the forward variance live?
5. HAR on daily charts: R6-T1 gave −6.7% (SPX) and +2.1% (NDX) at H = 5; more series needed.
6. Is the BTC-specific shock-direction lean real on other crypto pairs and venues (VOL-X5b)? It shows as +3.4 pp in the race and +0.21 ± 0.06 ATR in the mean move (n 3,196), and +0.35 ± 0.11 ATR with the documented z (n 870).
7. Why does the mean move after shocks change sign between 5m (+) and 1H (−) on the same index futures? A plausible mechanism, untested: 5m shocks are mostly scheduled releases with follow-through, while 1H shocks are dominated by overnight and halt-edge bars that mean-revert. A time-of-day split of VOL-X5 answers it.
8. How much of the compression/expansion forward-range gap survives a better unit? R6-T7 shows a random walk already produces 1.13× in ATR14 units. VOL-X4(b) uses that ratio as the benchmark.

---

## 9. Sources

**Opened or verified in this session**
- Pine Script v6 reference, local mirror `docsrc/jabez4jc_pinescriptv6/reference/ta.md` (`ta.tr`, `ta.atr`, `ta.rma`, `ta.stdev`, `ta.bbw`, `ta.kc`, `ta.kcw`, `ta.percentrank`, `ta.percentile_nearest_rank`, `ta.percentile_linear_interpolation`, `ta.linreg`, `ta.dmi`, `ta.rsi`, `ta.roc`, `ta.macd`, `ta.vwap`), `reference/time.md` (`time()` and `time_close()` with negative `bars_back`), `reference/request.md` and `concepts/other_timeframes_and_data.md` (40 unique requests), `writing_scripts/limitations.md` (500 ms per loop; 5,000-bar history buffer).
- Patton, A. J. (2011). Volatility forecast comparison using imperfect volatility proxies. *Journal of Econometrics* 160(1), 246-256. https://econpapers.repec.org/RePEc:eee:econom:v:160:y:2011:i:1:p:246-256 [verified in the resume pass: EconPapers record and abstract opened; the abstract states the robust-loss result used for QLIKE].
- Bollerslev, T. (1986). Generalized autoregressive conditional heteroskedasticity. *Journal of Econometrics* 31(3), 307-327. https://ideas.repec.org/a/eee/econom/v31y1986i3p307-327.html [verified in the resume pass: IDEAS record and abstract opened].
- Engle, R. F. (1982). Autoregressive conditional heteroscedasticity with estimates of the variance of United Kingdom inflation. *Econometrica* 50(4), 987-1007. https://ideas.repec.org/a/ecm/emetrp/v50y1982i4p987-1007.html [verified in the resume pass: IDEAS bibliographic record opened; no abstract available there].

**Verified by the study reports** (see each report's source list for URLs)
- quant_pot.final.md: Parkinson (1980); Garman & Klass (1980); Rogers & Satchell (1991); Yang & Zhang (2000), *J. Business* 73(3); Vințe, Ausloos & Furtună (2022), arXiv:2205.01370; Shu & Zhang (2006), *J. Futures Markets* 26(3); Alizadeh, Brandt & Diebold (2002), *J. Finance* 57(3); Chou (2005), *JMCB* 37(3); Andersen & Bollerslev (1997), *J. Empirical Finance* 4; Engle & Sokalska (2012), *J. Fin. Econometrics* 10(1); Hansen, Kim & Kimbrough (2024), *J. Fin. Econometrics* 22(1); RiskMetrics (1996); Corsi (2009); Perelló, Gutiérrez-Roig & Masoliver (2011), arXiv:1107.1174; Broadie, Glasserman & Kou (1997).
- quant_regime.final.md: Kaufman (efficiency ratio); Wilder (1978); Dreiss (Choppiness Index); Lo & MacKinlay (1988); Hamilton (1989); Nystrup, Kolm & Lindström (2020), *JFDS* 2(3); Crabel (1990); Bulkowski NR7 statistics; Mesfin (2026), arXiv:2605.04004; Safari & Schmidhuber (2025), arXiv:2501.16772; Le (2026), arXiv:2610.11028; Kurth, Eisler, Rej & Bouchaud (2026), arXiv:2607.01550.
- ict_time.final.md: Ederington & Lee (1993), *J. Finance* 48(4); Dacorogna et al. (1993), *JIMF*; Andersen & Bollerslev (1997/1998); Engle & Sokalska (2012); BLS Employment Situation timing.
- x1_implied_vol.md: Poon & Granger (2003); Christensen & Prabhala (1998); Blair, Poon & Taylor (2001); Busch, Christensen & Nielsen (2011); Becker, Clements & White (2007); Carr & Wu (2009); Johnson (2017); Albers (2025); Dubinsky et al. (2019); Ederington & Lee (1996); Cboe and Deribit index pages.
- asset_specific.final.md, session_stats.final.md, price_action.final.md, academic_sr.final.md, calib_ml.final.md, x1_positioning.md, x1_internals.md: asset-class mechanics, gaps, holidays, rolls, gap-fill tests, low-liquidity windows.

**This session's tests** (code and raw outputs in `/tmp/claude-0/-home-user-m/7ce60006-3639-59b1-8cd3-87355409d58a/scratchpad/r6_tools/`)
- R6-T1 `vol_est.py` → `out_volest_{5m,1h,btc,eur,d}.txt`: estimator forecast comparison (QLIKE, MZ R², 2-fold OOS).
- R6-T2 / R6-T3 `vol_regime.py` → `out_volreg_{5m,1h,btc,eur,d,rw}.txt`: compression and expansion magnitudes, breakouts by prior state with nulls, shocks, regime-label stability and kappa (simplified definitions; see the resume-pass note).
- R6-T7 `gapfill_t7.py` → `out_t7_{5m,1h,btc,eur,d,rw}.txt` (resume pass), all with the causal clock:
  - deseasonalised V-state persistence and flips;
  - the documented ER hysteresis rule;
  - shocks under both definitions, with day-clustered SEs for the mean move;
  - breakouts by the documented states, with ATR14, blended and clock units;
  - causal momentum factors for 10_momentum.md.
- Interpreter: the scratchpad virtual environment `venv_E9_momentum_factors` (numpy 2.5.5, pandas 3.1.1).

**Unverified in this session**
- Carter's original TTM Squeeze specification (only the practitioner description via the study's Barchart citation).
- Exact efficiency constants beyond the study's table (the ≈6 for Rogers-Satchell is the study's figure).
