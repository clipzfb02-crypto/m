# 10 · Trend and Momentum

Author role: R6, volatility, momentum and regime specialist. Spec coverage: APEX_ULTIMATE_SPEC section 8 (and the parts of sections 10, 13, 14 and 25 about redundant features, drift and "supporting features, not independent votes").

**Evidence tags** (same conventions as `09_volatility.md`):
- **[R6-Tn]**: a test I ran in this session. Code and raw outputs: `/tmp/claude-0/-home-user-m/7ce60006-3639-59b1-8cd3-87355409d58a/scratchpad/r6_tools/` (`mom_redund.py` T4 → `out_mom_{5m,5m_H48,1h,btc,eur,d}.txt`; `mom_factors.py` T5 → `out_factors_*.txt`; `kernels.py` T6 → `out_kernels.txt`).
- **[study: key]**: a number from a combined study report, replicated by its researcher B unless stated.
- **[verified]**: I opened the source (abstract or publisher page via search) in this session; **[study-verified]**: a study report re-opened it; **[unverified]**: neither.

**Datasets for R6-T4..T6:** CME ES, NQ, RTY, YM, CL, GC 5-minute (2026-01-20 → 2026-04-15, about 16,500 bars each); CME ES, NQ, RTY, YM, CL 1-hour (2025-03 → 2026-04, 4,500-6,270 bars); BTCUSD 1-hour (2017-2025, 70,273 bars); EURUSD 1-hour (2017-18, 5,000 bars); S&P 500 and NASDAQ daily (1999-2018, 5,031 bars). Each paired with a sign-flip null (bar shapes, gaps and volatility kept, direction destroyed).

**Main metric in R6-T4/T5:** the information coefficient IC = Spearman correlation between a feature at the close of bar t and the forward return over H bars divided by ATR14_t/C_t·√H (a volatility-normalised return). Standard errors use non-overlapping blocks of max(H, bars per day). Caution: for slow features (EMA200-based) the block is shorter than the feature's memory, so the SE is too small; the null's spread is the better yardstick there. An IC of 0.03 corresponds to explaining about 0.1% of the variance of forward returns.

Line numbers refer to the frozen DOL Engine v2 copy `brief/baseline_v2.pine`.

---

## 1. Scope and role in APEX

Spec section 8 lists EMA 20/50/100/200, EMA slope, EMA separation, RSI, MACD, ROC, DMI, ADX, VWAP, regression slope, acceleration, deceleration, divergence, persistence, trend strength and mean-reversion conditions, and says they are "supporting features, not independent votes by default" and that correlation and redundancy must be detected.

This document shows three things:
1. **Almost all of them are the same few numbers.** Every signed trend or momentum indicator in the list is (exactly or nearly) a weighted sum of past price changes, differing only in the shape and length of the weighting kernel and in normalisation. Their mutual correlations follow from kernel overlap, and the theory predicts the measured correlations within ±0.04 on futures, crypto and equity indices [R6-T6]. Three principal components carry 88-92% of the variance of 15 indicators [R6-T4].
2. **Their directional information at intraday horizons is close to zero.** ICs are within ±0.03 on 5-minute futures, negative on one year of 1H index futures, and small positive on daily indices, consistent with the study's finding that direction is close to a random walk at DOL horizons and with the academic split between daily-to-monthly time-series momentum and intraday noise.
3. **A small orthogonal set is enough:** a trend-level factor T, a momentum-change factor M, and a stretch (mean-reversion) factor S residualised on T and M. After residualisation their pairwise correlations are |ρ| ≤ 0.02 on every family [R6-T5].

**Modules fed:**
- **BIAS** (Directional Bias Score B): T, M, S⊥ as *candidate* features of a per-chart learned model with zero prior weight; never as fixed votes.
- **REG** (Market Regime Score A): direction-free trend strength (efficiency) for display and ledger stratification (defined in 09_volatility.md).
- **FCST** (forecast path): drift is zero unless a shrunk, chart-validated drift beats zero; momentum decay sets nothing by default.
- **SETUP** (Setup Quality E): stretch as a location descriptor ("extended", "near mean"), not a trigger.
- **CAL**: grading of every momentum feature by proper scores and against the sign-flip null.
- **UI**: optional EMA200 line, optional oscillator diagnostics in the debug dashboard only (spec 17: no forest of EMA lines, no oscillator panels by default).

---

## 2. Classification table

| Concept | Class | Evidence grade | Objectively calculable? | One-line note |
|---|---|---|---|---|
| EMA 20/50/100/200 and the EMA stack | D (as signals); E (definition) | weak intraday; moderate daily (via TSMOM) | yes | The stack is a discretised slow trend; corr 0.84-0.93 with EMA50−200 separation and price−EMA200 distance. |
| EMA slope | D | weak | yes | Identity: the 1-bar EMA change is α × (price − EMA). Same information as distance. |
| EMA separation / price-to-EMA distance | D | weak | yes | Hump- and exponential-kernel sums of past returns. |
| MACD line | D | weak | yes | An EMA separation (12/26); corr 0.95-0.96 with the 50-EMA slope. |
| MACD histogram | D | weak (small positive IC at 4 h on 5m, BTC) | yes | An exponentially weighted *change* of the MACD line: the acceleration factor. |
| Rate of change (volatility-normalised) | A (as TSMOM at daily-monthly) | strong daily-monthly; none intraday | yes | A box kernel; corr 0.99 with the signed efficiency ratio. |
| RSI | D | weak | yes | Identity: (RSI − 50)/50 = RMA(Δ)/RMA(|Δ|), an exponentially weighted signed efficiency ratio. |
| DMI (+DI vs −DI) | D | weak | yes | A high/low-based efficiency ratio; corr 0.92-0.94 with RSI. |
| ADX | D | none as a switch | yes | Smoothed |DMI ratio|; direction-free; ≥ 25 on 38% of random-walk bars. |
| VWAP as trend context | E (definition); D (as a signal) | weak | yes (needs volume) | Its redundancy partner changes with the timeframe. |
| Regression slope t-statistic | A (as a trend statistic) | moderate (concept); weak (signal) | yes | A parabolic kernel; |t| is monotone in R². |
| Acceleration / deceleration | D | weak | yes | The only cluster nearly orthogonal to the trend level (corr −0.05 to −0.14). |
| Divergence (confirmed pivots) | D | none | yes | No consistent edge over confirming pivots or the null [R6-T4]. |
| Persistence: variance ratio, Hurst | A | strong (method); weak (rolling use) | yes | Useful on long samples; noise at chart windows. |
| Persistence: runs test, autocorrelation | A | strong (method) | yes | Diagnostic of mean reversion vs trend at short lags. |
| Trend strength (direction-free) | D | weak | yes | ER, ADX, |t|, R² all measure efficiency; use one. |
| Mean-reversion conditions (stretch) | A (short-horizon reversal exists in some markets); C (as universal) | weak; asset-specific | yes | Negative IC on BTC 1H after residualising; ≈ 0 on 5m futures. |
| Time-series momentum (daily-monthly) | A | strong | yes | Moskowitz et al.; decayed for fast signals on small-tick contracts since 2009. |
| Intraday momentum (session effect) | A | moderate (existence); none (tradable with OHLCV) | partial | A time-of-day effect, not an oscillator signal. |
| Consolidated factors T, M, S⊥ | A (statistical construction) | strong (orthogonality), weak (predictive value) | yes | The recommended representation. |

---

## 3. Features

Notation: Δ_t = C_t − C_{t−1} (price change); r_t = ln(C_t/C_{t−1}); EMA_n with α_n = 2/(n+1); RMA_n with α = 1/n; u = the VOL unit from 09_volatility.md (ATR14 on display, u_H for forecasting); "knowable at close t" means final on the confirmed bar t.

### EMA 20/50/100/200 and the EMA stack
- **Classification:** D as signals (E as a definition); weak intraday, moderate on daily charts through the time-series momentum literature.
- **Definition:** Exponential moving averages of the close. The "stack" is bullish when EMA20 > EMA50 > EMA100 > EMA200 and bearish in the reverse order.
- **Market mechanism:** A moving average is a smoothed price; price above a rising average means recent returns were positive. Time-series momentum (Moskowitz, Ooi & Pedersen 2012) is the academic version: positive past returns predict positive future returns at 1-12 month horizons across futures, linked to slow information diffusion and hedging demand. Who is on the other side: liquidity providers and value traders who fade moves.
- **Mathematical implementation:**
  - EMA_n,t = EMA_n,t−1 + α_n(C_t − EMA_n,t−1). Mean age (centre of mass) (n − 1)/2 bars: 9.5 (EMA20), 24.5 (EMA50), 49.5 (EMA100), 99.5 (EMA200). The seed's weight after k bars is (1 − α)^k: EMA200 needs about 600 bars to forget its seed to 0.25%.
  - Stack score: K_t = (1/3)[sgn(E20 − E50) + sgn(E50 − E100) + sgn(E100 − E200)] ∈ {−1, −⅓, ⅓, 1}.
  - Knowable at close t (live during the bar; use confirmed values).
- **Required data:** closes.
- **Pine v6 availability:** `ta.ema(source, length)` (simple int length); O(1). Feasible. Plotting four EMAs is against spec 17's default; compute without plotting.
- **Proxy limitations:** none (pure price).
- **Useful when:** daily and weekly charts (slow trend context); display of a single EMA200 if the user wants it.
- **Fails when:** intraday as a direction signal; as several "confirmations" (it counts one slow factor up to three times).
- **Validation experiment:** MOM-X2 (section 8).
- **Existing evidence:** [R6-T4] Spearman corr of K with EMA50−200 separation 0.84-0.85 and with price−EMA200 distance 0.86-0.88 (5m, 1H, daily). IC (forward H, volatility-normalised): 5m H = 12 −0.003 (6 series, −0.031 to +0.020); 5m H = 48 −0.018; 1H H = 12 −0.066 (null −0.027); BTC 1H +0.027 ± 0.011 (null +0.011); daily H = 10 +0.068 ± 0.026 (2 highly correlated series; null +0.030). Legacy `buy_sell_indicator.pine` and `XAUUSD_Fast_Balanced_Pro.pine` use EMA crossovers as votes next to MACD and RSI (all in the same clusters; section 4).
- **APEX recommendation:** **INCLUDE-OPTIONAL**: EMA200 (or the stack) only as slow-trend context on daily and higher charts and as an optional line, off by default. Not a separate vote. Redundancy: member of the slow-trend cluster (stack, EMA50−200, price−EMA200); represented at most once.
- **Sources:** Pine v6 reference `ta.ema` (opened). Moskowitz, Ooi & Pedersen (2012), *JFE* 104(2) [study-verified]. R6-T4.

### EMA slope
- **Classification:** D; weak.
- **Definition:** The change of an EMA over k bars, scaled by volatility.
- **Market mechanism:** A rising average is taken as evidence of an uptrend.
- **Mathematical implementation:**
  - Slope_n,k = (E_n,t − E_n,t−k)/(k·u_t) (units of u per bar).
  - **Identity:** E_t − E_{t−1} = α(C_t − E_{t−1}). So the one-bar EMA slope is exactly α times the price-to-EMA distance, and the k-bar slope is α Σ_{i=0}^{k−1}(C_{t−i} − E_{t−i−1}), a k-bar sum of distances. EMA slope carries no information beyond the distance series.
  - Knowable at close t.
- **Required data:** closes.
- **Pine v6 availability:** `ta.ema`, `ta.change(x, k)`. O(1). Feasible.
- **Proxy limitations:** none.
- **Useful when:** never as a separate feature; as a readable description of T ("50-EMA rising").
- **Fails when:** counted next to separation or MACD.
- **Validation experiment:** MOM-X1 (kernel redundancy replication).
- **Existing evidence:** [R6-T4/T6] corr(50-EMA 10-bar slope, EMA20−50 separation) 0.97-0.98 on every family; theory under iid increments 0.97. corr(50-EMA slope, MACD 12/26) 0.95-0.96; theory 0.96.
- **APEX recommendation:** **EXCLUDE** as a feature (it is T). Redundancy: medium-trend cluster.
- **Sources:** Pine v6 reference `ta.ema` (opened). R6-T4, R6-T6.

### EMA separation and price-to-EMA distance
- **Classification:** D; weak.
- **Definition:** Separation: the gap between a fast and a slow EMA in volatility units. Distance: price minus an EMA in volatility units.
- **Market mechanism:** As for moving averages.
- **Mathematical implementation:**
  - Separation: (E_f − E_s)/u. Distance: (C − E_n)/u.
  - **Return-kernel identities** (derivation: write C_{t−k} = C_t − Σ_{i<k} Δ_{t−i}, use that EMA weights sum to 1):
    - C_t − E_n,t = Σ_{i≥0} (1 − α_n)^{i+1} Δ_{t−i} (an exponential kernel on past changes).
    - E_f,t − E_s,t = Σ_{i≥0} [(1 − α_s)^{i+1} − (1 − α_f)^{i+1}] Δ_{t−i} (a hump-shaped kernel, zero at lag 0, peaking at lag i* = ln(ln b / ln a)/ln(a/b) − 1 with a = 1 − α_s, b = 1 − α_f; i* ≈ 7.6 bars for 12/26 and ≈ 14 bars for 20/50).
  - Levine & Pedersen (2016) show the same equivalence between moving-average crossovers and time-series momentum in general form.
  - Knowable at close t.
- **Required data:** closes.
- **Pine v6 availability:** `ta.ema`. O(1). Feasible.
- **Proxy limitations:** none.
- **Useful when:** separation as the readable form of T on charts where traders expect it.
- **Fails when:** treated as independent of slope, MACD or the stack.
- **Validation experiment:** MOM-X1.
- **Existing evidence:** [R6-T6] theory vs measured Spearman correlation (ES 5m / NQ 5m / ES 1H / BTC 1H / SPX daily): EMA20−50 vs MACD 0.89 vs 0.87-0.90; price−EMA20 vs EMA20−50 0.56 vs 0.55-0.58; price−EMA200 vs EMA50−200 0.90 vs 0.89-0.93. [R6-T4] separation and distance ICs are within ±0.03 on 5m, −0.06 to −0.07 on 1H (index futures, one year), +0.04 to +0.06 on daily.
- **APEX recommendation:** **INCLUDE-CORE** only as one member of the averaged T factor (EMA20−50 separation); price−EMA20 distance goes into S (stretch). Redundancy: medium-trend cluster (separation, slope, MACD line, 50-bar regression t) and fast cluster (distance, RSI, DMI, ROC).
- **Sources:** Levine, A. & Pedersen, L. H. (2016), "Which Trend Is Your Friend?", *Financial Analysts Journal* 72(3), 51-66 [verified: abstract via search, https://ideas.repec.org/a/taf/ufajxx/v72y2016i3p51-66.html]. Pine v6 reference `ta.ema` (opened). R6-T4, R6-T6.

### MACD (line, signal, histogram)
- **Classification:** D; weak.
- **Definition:** MACD line = EMA12 − EMA26; signal = EMA9(MACD); histogram = MACD − signal (Appel).
- **Market mechanism:** The line is a trend filter; the histogram shows whether that trend filter is accelerating or decelerating.
- **Mathematical implementation:**
  - Line: L_t = E12 − E26 (a separation; hump kernel peaking at lag ≈ 7.6 bars). Normalise: L_t/u.
  - Histogram: Hh_t = L_t − EMA9(L)_t = Σ_{i≥0} (1 − α_9)^{i+1} ΔL_{t−i}: by the same identity as price-to-EMA distance, it is an exponentially weighted sum of recent **changes** of the line, i.e. an acceleration measure. Normalise: Hh_t/u.
  - Crossovers of L and the signal = sign changes of Hh.
  - Knowable at close t.
- **Required data:** closes.
- **Pine v6 availability:** `ta.macd(source, 12, 26, 9)` returns [line, signal, hist] (docs). O(1). Feasible.
- **Proxy limitations:** none.
- **Useful when:** the histogram as the M factor; the line as part of T.
- **Fails when:** counted as a separate confirmation of a moving-average crossover (corr 0.87-0.90) or of the 50-EMA slope (0.95-0.96).
- **Validation experiment:** MOM-X3 (M factor replication).
- **Existing evidence:** [R6-T4] histogram IC: 5m H = 12 +0.006 (−0.050 to +0.026; CL negative), 5m H = 48 **+0.031 ± 0.009** (5 of 6 series positive; null −0.009), 1H H = 12 −0.030, BTC 1H **+0.037 ± 0.009** (null +0.009), daily −0.014. corr(histogram, 5-bar change of the 20-bar t-stat) 0.72-0.76; corr(histogram, medium-trend cluster) −0.10 to +0.12. These are among 16 features × 6 settings tested, so single cells near 2-3 SE are weak evidence.
- **APEX recommendation:** **INCLUDE-CORE** the histogram/u as a member of M (candidate feature, zero prior weight). The line is absorbed into T. Redundancy: line = medium trend; histogram = acceleration cluster.
- **Sources:** Pine v6 reference `ta.macd` (opened). R6-T4, R6-T6.

### Rate of change (volatility-normalised)
- **Classification:** A as time-series momentum at daily-monthly horizons (strong); none intraday.
- **Definition:** The return over the last n bars, here scaled by volatility.
- **Market mechanism:** As time-series momentum.
- **Mathematical implementation:**
  - ROC_n = 100·(C_t − C_{t−n})/C_{t−n} (Pine `ta.roc`). Volatility-normalised: R_n = ln(C_t/C_{t−n}) / (σ_bar·√n), with σ_bar = u/C or the per-bar σ from VOL.
  - Kernel: a box Σ_{i<n} Δ_{t−i}.
  - Relation to the signed efficiency ratio: sER_n = Σ_{i<n}Δ / Σ_{i<n}|Δ|. For Gaussian increments E|Δ| = σ√(2/π), so R_n ≈ sER_n·√(2n/π).
  - Knowable at close t.
- **Required data:** closes.
- **Pine v6 availability:** `ta.roc`, `ta.change`. O(1). Feasible.
- **Proxy limitations:** none.
- **Useful when:** daily and higher as a slow-trend input to a learned model.
- **Fails when:** intraday as a direction signal; next to sER (corr 0.99).
- **Validation experiment:** MOM-X2.
- **Existing evidence:** [R6-T4] corr(R_20, sER_20) 0.99 on every family; corr(R_20, 20-bar regression t) 0.87-0.90 (theory 0.91). IC: 5m +0.006, 1H −0.059, BTC +0.004, daily +0.014. Literature: TSMOM (1-12 months, 58 futures; Moskowitz et al. 2012). Fast trend signals (EWM τ = 5-50 days) lost most of their Sharpe after 2009 on small-tick contracts (equity index, FX): τ = 5 days 0.84 → 0.12; large-tick contracts 1.0-1.2 (Kurth et al. 2026, study-verified).
- **APEX recommendation:** **EXCLUDE** as a separate feature (it is sER and part of the fast cluster). Redundancy: fast cluster.
- **Sources:** Pine v6 reference `ta.roc` (opened). Moskowitz et al. (2012) [study-verified]; Kurth, Eisler, Rej & Bouchaud (2026) arXiv:2607.01550 [study-verified]. R6-T4, R6-T6.

### RSI
- **Classification:** D; weak.
- **Definition:** Wilder's Relative Strength Index, 0-100.
- **Market mechanism:** Overbought/oversold (mean reversion) or strength (momentum), depending on the school.
- **Mathematical implementation:**
  - RSI = 100·U/(U + D), U = RMA_n(Δ⁺), D = RMA_n(Δ⁻) (Pine docs: `ta.rsi` uses `ta.rma`).
  - **Identity:** since Δ = Δ⁺ − Δ⁻ and |Δ| = Δ⁺ + Δ⁻ and RMA is linear, (RSI − 50)/50 = (U − D)/(U + D) = **RMA_n(Δ)/RMA_n(|Δ|)**. RSI is an exponentially weighted signed efficiency ratio. That is why it correlates 0.98 with price-to-EMA20 distance (both exponential kernels on Δ) and 0.89 with sER_20.
  - Edge case: D = 0 → RSI = 100 (Pine).
  - Knowable at close t.
- **Required data:** closes.
- **Pine v6 availability:** `ta.rsi(source, length)`. O(1). Feasible.
- **Proxy limitations:** none.
- **Useful when:** as one member of S (stretch) together with price-to-EMA20 distance.
- **Fails when:** as a stand-alone reversal trigger at 70/30, or as a confirmation next to DMI, ROC or distance.
- **Validation experiment:** MOM-X4 (S⊥ mean reversion).
- **Existing evidence:** [R6-T4] corr(RSI14, price−EMA20) 0.98; with DMI ratio 0.92-0.94; with sER 0.89. IC: 5m +0.015, 1H −0.062, BTC +0.009, daily +0.004. Legacy `XAUUSD_Fast_Balanced_Pro.pine` averages RSI, an RSI of the MACD histogram and the DMI ratio into one "momentum composite": three members of the same cluster.
- **APEX recommendation:** **INCLUDE-CORE** only as a member of S (averaged with price−EMA20 distance, then residualised). Optional display in the debug dashboard. Redundancy: fast cluster.
- **Sources:** Pine v6 reference `ta.rsi`, `ta.rma` (opened). Wilder (1978) [study-verified definitions]. R6-T4.

### DMI (+DI and −DI)
- **Classification:** D; weak.
- **Definition:** Wilder's directional indicators from up-moves of highs and down-moves of lows.
- **Market mechanism:** Whether new highs or new lows dominate recent bars.
- **Mathematical implementation:**
  - +DM = H_t − H_{t−1} if it exceeds L_{t−1} − L_t and is > 0, else 0; −DM mirrors it. ±DI = 100·RMA_n(±DM)/RMA_n(TR).
  - Signed ratio: P_t = (+DI − −DI)/(+DI + −DI) = (RMA(+DM) − RMA(−DM))/(RMA(+DM) + RMA(−DM)): a high/low-based exponentially weighted efficiency ratio, the bar-extreme analogue of the RSI identity.
  - Guard +DI + −DI = 0.
  - Knowable at close t.
- **Required data:** OHLC.
- **Pine v6 availability:** `ta.dmi(diLength, adxSmoothing)` returns [+DI, −DI, ADX] (docs). O(1). Feasible.
- **Proxy limitations:** none.
- **Useful when:** as an alternative member of S if a high/low-based measure is preferred.
- **Fails when:** counted next to RSI (0.92-0.94).
- **Validation experiment:** MOM-X1, MOM-X4.
- **Existing evidence:** [R6-T4] IC: 5m H = 12 **+0.027 ± 0.010** (indices +0.031 to +0.050, CL +0.003, GC −0.011), 5m H = 48 +0.040 ± 0.015, 1H −0.062, BTC +0.014, daily +0.007. The 5m cells are the largest intraday fast-cluster ICs in the test, but they are within one cluster of nearly identical features and 16 features were tested.
- **APEX recommendation:** **RESEARCH-ONLY** (a candidate to replace RSI inside S if Phase 6 shows it consistently better). Redundancy: fast cluster.
- **Sources:** Pine v6 reference `ta.dmi` (opened). Wilder (1978) [study-verified]. R6-T4.

### ADX
- **Classification:** D; none as a regime switch.
- **Definition:** The average directional index, a direction-free trend-strength measure (Wilder).
- **Market mechanism:** High ADX = one side dominating recent bar extremes.
- **Mathematical implementation:**
  - DX = 100·|+DI − −DI|/(+DI + −DI) = 100·|P_t|; ADX = RMA_m(DX). ADX is a smoothed absolute DMI ratio, i.e. a smoothed |efficiency|.
  - Conventional thresholds 25 (trend) and 20 (no trend) are conventions, not calibrated.
  - Knowable at close t (double smoothing lags by roughly n + m bars).
- **Required data:** OHLC.
- **Pine v6 availability:** `ta.dmi`. O(1). Feasible.
- **Proxy limitations:** none.
- **Useful when:** display only, if at all.
- **Fails when:** as a filter. Random walk: ADX ≥ 25 on 38% of bars, mean 24.1, and ADX keeps corr ≈ 0.22 over 28 bars on a random walk because of double smoothing (persistence without information); ADX ≥ 25 as a gate on the draw vector costs 2.5-3.5 pp (study: quant_regime).
- **Validation experiment:** none; rejected on existing evidence.
- **Existing evidence:** As above. [R6-T5] ADX vs |sER20| 0.32-0.44, vs |20-bar t| 0.30-0.41, vs |50-bar t| 0.36-0.52 (it is a noisy strength measure). ADX vs every signed feature −0.21 to +0.01 (direction-free by construction). Practitioner tests: Donchian + ADX filter adds no value; ADX + Parabolic SAR on USD pairs had "a high proportion of negative returns" (Gurrib 2018; study-verified via search).
- **APEX recommendation:** **EXCLUDE** as an input; the efficiency ratio is the single strength measure (09_volatility.md). Redundancy: strength cluster (ER, |t|, R², ADX, CHOP).
- **Sources:** Pine v6 reference `ta.dmi` (opened). Study: quant_regime 1.2, 2.2. R6-T5.

### VWAP as trend context
- **Classification:** E (definition); D as a signal; weak.
- **Definition:** Volume-weighted average price since an anchor (session open by default), and price's deviation from it.
- **Market mechanism:** VWAP is an execution benchmark for institutions; trading above session VWAP means the average buyer since the open is in profit. The other side: benchmark-tracking execution algorithms trade around it.
- **Mathematical implementation:**
  - VWAP_t = Σ_{k=a}^{t} p_k V_k / Σ_{k=a}^{t} V_k, p = hlc3 (Pine default), a = anchor bar (`timeframe.change("1D")` by default; for CME the 18:00 ET Globex open).
  - Deviation: D_t = (C_t − VWAP_t)/u; optional bands with `stdev_mult`.
  - Its kernel depends on how many bars the session holds: on 5m (≈ 276 bars per Globex session) it behaves like a slow anchor; on 1H (≈ 23 bars) like a short one.
  - Knowable at close t.
- **Required data:** OHLC and **volume**.
- **Pine v6 availability:** `ta.vwap(source, anchor, stdev_mult)` (docs). O(1). Feasible where volume exists.
- **Proxy limitations:** spot FX has only tick volume from one venue; multi-venue crypto volume differs by exchange; continuous futures volume around rolls is split between contracts.
- **Useful when:** context and display ("above session VWAP"); the volume specialist's VWAP features.
- **Fails when:** no volume; counted as an extra trend vote.
- **Validation experiment:** covered by MOM-X1 (cluster membership) and the volume module's experiments.
- **Existing evidence:** [R6-T4] corr(VWAP deviation, EMA20−50 separation) 0.82 on 5m; on 1H corr with price−EMA20 0.72 and with the MACD histogram 0.61. IC: 5m +0.013 (n.s.), 1H −0.040 ± 0.013 (null +0.019), EUR +0.037 ± 0.028.
- **APEX recommendation:** **INCLUDE-OPTIONAL** as context and display only. Redundancy: member of T on fine charts, of S on coarse charts; never added to them.
- **Sources:** Pine v6 reference `ta.vwap` (opened). R6-T4.

### Regression slope t-statistic (normalised trend strength)
- **Classification:** A (as a trend statistic); moderate as a concept, weak as a signal.
- **Definition:** The t-statistic of the least-squares slope of log price on time over the last n bars.
- **Market mechanism:** It measures trend relative to noise around the trend line. Safari & Schmidhuber (2025) use a trend-strength statistic φ of this kind: on futures, weak trends persist and strong trends revert from a few hours to years, while below about 15-30 minutes weak trends revert; the coefficients are small (study-verified).
- **Mathematical implementation:**
  - y_k = ln C_k, x_k = k over the window. Slope b = S_xy/S_xx with S_xx = n(n² − 1)/12. Residual variance s² = (S_yy − b·S_xy)/(n − 2). t = b/(s/√S_xx). Equivalently |t| = √((n − 2)R²/(1 − R²)), so |t| is monotone in R².
  - **Kernel:** b = Σ_{j=1}^{n−1} w_j Δy_j with w_j = 6j(n − j)/(n(n² − 1)) (a parabolic kernel peaking mid-window; the weights sum to 1).
  - O(1) with rolling sums of y, k·y and y² (as in `r6lib.reg_tstat`); `ta.linreg` gives the fitted endpoint.
  - Bounded transform for scoring: T* = tanh(t/3).
  - Defaults: n = 50 for the T factor, n = 20 inside the fast and acceleration measures.
  - Caution: residuals are autocorrelated, so |t| ≥ 2 does not mean 5% significance.
  - Knowable at close t.
- **Required data:** closes.
- **Pine v6 availability:** `math.sum`, `ta.linreg(source, length, offset)` (docs); O(1). Feasible.
- **Proxy limitations:** none.
- **Useful when:** as the most stable member of T (it uses the whole window, not the latest price).
- **Fails when:** as a stand-alone direction signal.
- **Validation experiment:** MOM-X2.
- **Existing evidence:** [R6-T4] corr(50-bar t, EMA20−50 separation) 0.90-0.92 (theory with the slope kernel 0.94). IC 50-bar t: 5m H = 12 +0.021 ± 0.011 (all 6 series positive, null −0.011), 5m H = 48 −0.004, 1H −0.062, BTC +0.003, daily +0.020. 20-bar t: 5m +0.014, 5m H = 48 +0.028 ± 0.013, BTC +0.021. Study: adding φ and φ³ (24-bar trend t) to the geometry logit never improved out-of-sample log-loss of which side is taken first (+0.08% to +1.00%) (quant_regime 2.3).
- **APEX recommendation:** **INCLUDE-CORE** as the anchor of T (candidate feature, zero prior weight). Redundancy: medium-trend cluster.
- **Sources:** Safari & Schmidhuber (2025) arXiv:2501.16772 [study-verified]. Pine v6 reference `ta.linreg` (opened). R6-T4, R6-T6.

### Acceleration and deceleration (momentum change)
- **Classification:** D; weak.
- **Definition:** The change of a trend measure: positive when the trend strengthens (or a downtrend weakens), negative otherwise.
- **Market mechanism:** Traders read deceleration as exhaustion and acceleration as initiative. Statistically, a change measure is the part of momentum that is not the trend level.
- **Mathematical implementation:**
  - Option A (preferred, cheap): MACD histogram/u (an exponentially weighted change of the 12/26 separation).
  - Option B: Δ_k T: the change of the 20-bar regression t over k = 5 bars.
  - M = average of the z-ranks (or bounded transforms) of A and B.
  - Deceleration flag (descriptive): sgn(T) ≠ sgn(M) with |T| above its noise floor.
  - Knowable at close t.
- **Required data:** closes.
- **Pine v6 availability:** `ta.macd`, `ta.change`. O(1). Feasible.
- **Proxy limitations:** none.
- **Useful when:** as M in a learned model; describing "trend slowing" in reason codes.
- **Fails when:** as an exhaustion trigger. The study found that the speed of a reversal does not predict how far the new leg runs, with the sign flipping between timeframes (price_action finding 7), and that leg-end features seen in hindsight appear identically in random walks (Filimonov & Sornette 2011; study-verified).
- **Validation experiment:** MOM-X3.
- **Existing evidence:** [R6-T5] corr(T, M) −0.05 to −0.14 on every family: M is nearly orthogonal to the trend level without any adjustment. IC of M⊥T: 5m H = 12 +0.009 to +0.032 on ES/NQ/RTY/YM/GC, −0.034 on CL; 1H −0.006 to −0.069; BTC **+0.047 ± 0.009**; daily −0.012 to −0.028. Δ_5 t20 alone: BTC +0.050 ± 0.008 (null +0.005); 5m H = 48 +0.019 ± 0.005.
- **APEX recommendation:** **INCLUDE-CORE** as the M factor (candidate, zero prior weight; learned per chart). Redundancy: acceleration cluster (histogram, Δt).
- **Sources:** Study: price_action findings 7 and 12. R6-T4, R6-T5.

### Divergence (formal, confirmed-pivot based)
- **Classification:** D; none.
- **Definition:** Price makes a higher high (lower low) at a confirmed pivot while an oscillator makes a lower high (higher low) at the same pivots. "Regular bearish/bullish divergence".
- **Market mechanism:** The claim is that weakening momentum precedes reversal.
- **Mathematical implementation:**
  - Pivots: high pivot at bar p with length L = 5 if H_p > max(H_{p−L..p−1}) and H_p ≥ max(H_{p+1..p+L}). It is **knowable only at bar p + L**.
  - Bearish divergence at confirmation bar k = p + L: the previous confirmed high pivot q satisfies 8 ≤ p − q ≤ 60 bars, H_p > H_q and RSI_p < RSI_q − 2 (a minimum oscillator gap of 2 points avoids ties). Bullish divergence mirrors it on lows.
  - Control: a higher high with RSI_p ≥ RSI_q (a "confirming" pivot).
  - The signal is time-stamped at k, never at p (no backdating; spec 3 and 19.1).
  - Knowable at close k = p + L.
- **Required data:** OHLC.
- **Pine v6 availability:** `ta.pivothigh`, `ta.pivotlow`, `ta.valuewhen`, `ta.rsi`. O(1). Feasible.
- **Proxy limitations:** none (OHLCV is enough), but results depend strongly on pivot length and oscillator choice, which invites data snooping.
- **Useful when:** as a descriptive label in the debug dashboard if users want it.
- **Fails when:** as a reversal signal.
- **Validation experiment:** MOM-X5.
- **Existing evidence:** [R6-T4] ±1 ATR race in the divergence direction within H after the confirmation bar (null in brackets):
  - 5m (6 series, H = 12): bearish 0.517 (n 466) vs control 0.518 (n 1,946) [0.503]; bullish 0.527 (n 405) vs control 0.480 (n 1,886) [0.494].
  - 1H (5 series): bearish 0.589 (n 157) vs control 0.529 [0.497]; bullish 0.504 (n 117) vs control 0.468 [0.453].
  - BTC 1H: bearish 0.501 (n 386), bullish 0.490 (n 301) [0.497 / 0.484].
  - Daily SPX + NDX (H = 10): bearish 0.389 (n 72), bullish 0.621 (n 29).
  - Reading: no consistent effect; the one +9 pp cell (1H bearish, SE ≈ 0.04) is 1 of 10 cells and disagrees in sign with the daily bearish cell. Study: breadth (ADD) divergence at new highs/lows was not supported either (x1_internals).
- **APEX recommendation:** **RESEARCH-ONLY**. Not a signal, not a score input; optional debug label only after Phase 6. Redundancy: a divergence is a special case of sgn(T at price scale) ≠ sgn(M); the M factor already carries it.
- **Sources:** Pine v6 reference `ta.pivothigh`, `ta.rsi` (opened). Study: x1_internals finding 3. R6-T4.

### Persistence: variance ratio and Hurst exponent
- **Classification:** A; strong as a method over long samples, weak as a rolling switch.
- **Definition:** Whether returns trend (positive autocorrelation) or revert (negative) over q bars.
- **Market mechanism:** Persistence comes from slow information diffusion and herding; reversal from liquidity provision and bid-ask bounce.
- **Mathematical implementation:**
  - VR(q) = Var(q-bar return) / (q·Var(1-bar return)) ≈ 1 + 2 Σ_{j=1}^{q−1} (1 − j/q)ρ_j (Lo & MacKinlay 1988). Use the heteroskedasticity-robust z*: z* = (VR − 1)/√(θ/T), θ = Σ_{j=1}^{q−1} [2(q − j)/q]² δ_j, δ_j = T·Σ d²_k d²_{k−j} / (Σ d²_k)², d = demeaned returns.
  - Hurst: H ≈ 0.5 + ln VR(q)/(2 ln q).
  - Use over long samples (thousands of bars), not rolling windows of 100.
  - Knowable at close t (over the history to t).
- **Required data:** closes.
- **Pine v6 availability:** rolling sums of q-bar returns and squared returns; O(1) per q; feasible as a diagnostic.
- **Proxy limitations:** none.
- **Useful when:** a once-per-chart diagnostic ("this instrument has mild mean reversion at 1-16 bars") feeding the prior of a learned model.
- **Fails when:** rolling at chart windows. Study: SE of VR(4) on 96 bars ≈ 0.19; rolling VR-Hurst SD 0.069 on a random walk and > 0.55 on 12-16% of random-walk bars, with next-window correlation ≈ 0 (quant_regime 1.4, 2.2).
- **Validation experiment:** MOM-X8.
- **Existing evidence:** [R6-T4] full-sample VR(2, 4, 8, 16) and robust z*:
  - 5m ES/NQ/RTY/YM/CL: 0.96-1.03, all |z*| ≤ 1.0; GC 0.90-0.97 (z* −1.3 to −1.7).
  - 1H ES/NQ: 1.00-1.13 (z* ≤ 1.0); RTY 0.92-0.96; YM, CL ≈ 1.
  - BTC 1H: 0.967 / 0.920 / 0.888 / 0.887 (z* −3.1, −4.1, −3.7, −2.8): significant mean reversion at 1-16 hours.
  - EURUSD 1H: 0.96-0.99 (n.s.).
  - S&P 500 daily 1999-2018: 0.93 / 0.86 / 0.77 / 0.72 (z* −2.8, −2.9, −2.8, −2.3); NASDAQ 0.97-0.84.
  - Study: VR at q = 30-60 on CME 5m: ES 0.96, NQ 1.02-1.05, CL 1.00-1.03, GC 0.84-0.87, YM 0.91-0.94 (quant_pot 1.11). Le (2026): across 61 instruments the VR test cannot reject a random walk for most (study-verified).
- **APEX recommendation:** **RESEARCH-ONLY** for rolling use; **INCLUDE-OPTIONAL** as a once-per-load diagnostic in the debug dashboard. Redundancy: the same information as the autocorrelation/runs diagnostics; the IC of S⊥ measures its forecasting consequence.
- **Sources:** Lo & MacKinlay (1988) *RFS* 1(1) [study-verified]. Study: quant_regime 1.4, 2.2; quant_pot 1.11; Le (2026) arXiv:2610.11028 [study-verified]. R6-T4.

### Persistence: runs test and autocorrelation
- **Classification:** A; strong (method).
- **Definition:** Whether consecutive returns change sign more or less often than chance (runs), and the correlation of returns with their own lags.
- **Market mechanism:** As for the variance ratio; bid-ask bounce produces negative lag-1 autocorrelation in sampled prices.
- **Mathematical implementation:**
  - Lag-1 autocorrelation ρ₁ of r.
  - Wald-Wolfowitz runs: with n₊ up-bars and n₋ down-bars (zeros dropped), runs R; μ = 2n₊n₋/n + 1, Var = 2n₊n₋(2n₊n₋ − n)/(n²(n − 1)); z = (R − μ)/√Var. z > 0 = too many sign changes (reversion); z < 0 = trending.
  - Long-sample diagnostics only.
  - Knowable at close t.
- **Required data:** closes.
- **Pine v6 availability:** running counts; O(1). Feasible.
- **Proxy limitations:** sign tests ignore magnitude. Portnaya (2026): SPY's lag-1 autocorrelation of −0.081 (z −7.39, daily 1993-2026) is magnitude-driven; the sign test gives p = 0.11 (study-verified).
- **Useful when:** with the variance ratio as a chart diagnostic.
- **Fails when:** used bar by bar.
- **Validation experiment:** MOM-X8.
- **Existing evidence:** [R6-T4] ρ₁: 5m −0.034 (GC) to +0.030 (CL); 1H −0.042 (RTY) to +0.010; BTC 1H −0.033; EUR −0.012; SPX daily −0.070; NDX −0.030. Runs z: 5m 0.0 to +2.7; 1H −0.4 to +1.9; **BTC +21.1**; EUR +4.3; SPX +4.3. BTC and SPX daily show reversion at the shortest lags.
- **APEX recommendation:** **INCLUDE-OPTIONAL** (debug diagnostic only), with the variance ratio. Redundancy: variance ratio.
- **Sources:** Portnaya (2026) arXiv:2606.29591 [study-verified]. Heston, Korajczyk & Sadka (2010) *J. Finance* 65(4) [study-verified]. R6-T4.

### Trend strength (direction-free)
- **Classification:** D; weak.
- **Definition:** How directional recent movement was, regardless of direction.
- **Market mechanism:** Traders use it to decide between trend-following and fading.
- **Mathematical implementation:**
  - APEX uses one measure: G_t = |sER_20| (09_volatility.md), with the noise-floor threshold θ_20(α) = z_{1−α/2}·√(π/(2·20)) (0.46 at 10%, 0.55 at 5% false positives on a random walk).
  - Equivalent alternatives (do not add them): |t| of the 20-bar regression, R², ADX, the Choppiness Index.
  - Knowable at close t.
- **Required data:** closes.
- **Pine v6 availability:** O(1). Feasible.
- **Proxy limitations:** none.
- **Useful when:** REG display and ledger stratification (TREND-WITH vs TREND-AGAINST cells let each chart test "trends continue" on its own data; study: REG-2).
- **Fails when:** as a forecast: label persistence at lag H equals a random walk's (kappa +0.04 to +0.09 vs +0.05 to +0.06; R6-T3 in 09_volatility.md).
- **Validation experiment:** VOL-X6 in 09_volatility.md.
- **Existing evidence:** [R6-T5] |sER20| vs |20-bar t| 0.64-0.71; ADX vs |sER20| 0.32-0.44. Study: ER20 ≥ 0.40 on 15.7% of random-walk bars; corr(ER20(t), ER20(t+20)) −0.04 to +0.01 (quant_regime).
- **APEX recommendation:** **INCLUDE-CORE** in REG (descriptive), zero weight in BIAS. Redundancy: strength cluster.
- **Sources:** Study: quant_regime 1.1, 2.2, REG-2. R6-T3, R6-T5.

### Mean-reversion conditions (stretch)
- **Classification:** A for short-horizon reversal in some markets (moderate in the literature); C as a universal rule; weak for this engine.
- **Definition:** Price far from a short-term mean relative to volatility, after accounting for the prevailing trend and momentum.
- **Market mechanism:** Liquidity providers absorb temporary order imbalances and are paid when prices revert; bid-ask bounce and over-reaction produce short-horizon reversal (Heston, Korajczyk & Sadka 2010). Real trend legs are 7-13% shorter than i.i.d. bars would produce at the 2-ATR scale (study: price_action finding 3).
- **Mathematical implementation:**
  - Raw stretch: S_t = average of z-ranks (or bounded transforms) of (C_t − EMA20_t)/u and (RSI14 − 50)/50.
  - Raw S is strongly tied to the trend (corr(T, S) 0.57-0.64) and to M (0.51-0.57), so S alone mostly re-measures trend.
  - **Residual stretch:** S⊥_t = S_t − β_T,t·T_t − β_M,t·M_t, with rolling betas over W = 500 bars. Two regressors, closed form: with c_T = Cov(S,T), c_M = Cov(S,M), v_T = Var T, v_M = Var M, k = Cov(T,M): β_T = (c_T·v_M − c_M·k)/(v_T·v_M − k²), β_M = (c_M·v_T − c_T·k)/(v_T·v_M − k²). Rolling moments via `ta.sma` of products (O(1)).
  - Descriptive flag "EXTENDED" when |(C − EMA20)/u_H| ≥ 2 (no reversal claim).
  - Knowable at close t.
- **Required data:** closes (OHLC for u).
- **Pine v6 availability:** `ta.ema`, `ta.rsi`, `ta.sma`, `ta.correlation`, `ta.stdev`. O(1). Feasible.
- **Proxy limitations:** none.
- **Useful when:** as a learned feature on instruments with measured short-horizon reversal (BTC 1H in our data); as a location descriptor in SETUP.
- **Fails when:** as a fixed fade rule on index futures (no effect) or in trending regimes.
- **Validation experiment:** MOM-X4.
- **Existing evidence:** [R6-T5] IC of S⊥ (H = 12): 5m −0.019 to +0.014 (n.s.); 1H −0.022 to +0.040 (n.s.); **BTC 1H −0.053 ± 0.007** (mean reversion; a single 8-year series); daily −0.003 to −0.023. Consistent with BTC's VR < 1 and runs z +21 [R6-T4]. Study: short-term mean reversion confined to exchange-traded equity baskets and sovereign bonds at daily horizons; credit, commodities, FX and crypto random-walk-like in that sample (Portnaya 2026, study-verified); our BTC 1H result is an intraday-horizon exception that needs replication.
- **APEX recommendation:** **INCLUDE-CORE** as the S⊥ factor (candidate feature, zero prior weight, learned per chart); the "EXTENDED" descriptor in SETUP and UI. Redundancy: fast cluster, after residualisation on T and M.
- **Sources:** Heston, Korajczyk & Sadka (2010) [study-verified]; Portnaya (2026) [study-verified]. Study: price_action finding 3. R6-T4, R6-T5.

### Time-series momentum (academic, daily to monthly)
- **Classification:** A; strong at 1-12 month horizons; decayed for fast signals.
- **Definition:** The sign (or volatility-scaled size) of an instrument's own past return predicts its next return.
- **Market mechanism:** Under-reaction to information, slow-moving capital and hedging demand; the losing side is investors who trade against persistent flows.
- **Mathematical implementation:**
  - Signal: sgn(r_{t−L,t}) or r_{t−L,t}/σ̂_t with L = 1-12 months (Moskowitz et al.); EWMA crossover forms (Kurth et al.: EWM τ vs 4τ).
  - In APEX terms it is the T factor (or a slow T) on daily and weekly charts.
  - Knowable at close t.
- **Required data:** daily closes over months to years.
- **Pine v6 availability:** on intraday charts via one `request.security` of daily data with `[1]` and `lookahead_on`; O(1). Feasible.
- **Proxy limitations:** none.
- **Useful when:** daily and weekly charts; large-tick contracts.
- **Fails when:** at intraday horizons; fast signals on small-tick contracts after 2009.
- **Validation experiment:** MOM-X2 (the daily arm).
- **Existing evidence:** Moskowitz, Ooi & Pedersen (2012): 58 futures, persistence for 1-12 months, partial reversal after a year (study-verified). Kurth et al. (2026), about 100 futures 1995-2025: Sharpe 1995-2009 → 2009-2025 τ = 5 days 0.84 → 0.12, τ = 10 0.83 → 0.22, τ = 20 0.79 → 0.27, τ = 50 0.70 → 0.40; small-tick (equity index, FX) "completely degraded"; large-tick 1.0-1.2; better in low volatility (study-verified). Levine & Pedersen (2016): TSMOM and moving-average crossovers are closely related, generalised trend filters (verified, abstract). [R6-T4] daily slow-trend ICs +0.049 to +0.068 (SPX/NDX 1999-2018, effectively one sample).
- **APEX recommendation:** **INCLUDE-OPTIONAL** as the daily/weekly arm of T in the learned BIAS model (a small positive prior is defensible only on daily and higher charts, still shrunk and validated per chart). Redundancy: it is T at a slow horizon; the HTF structure module supplies most of the higher-timeframe context.
- **Sources:** Moskowitz, Ooi & Pedersen (2012) [study-verified]; Kurth et al. (2026) [study-verified]; Levine & Pedersen (2016) [verified]. R6-T4.

### Intraday momentum (session effect)
- **Classification:** A; moderate for existence, none for a usable OHLCV signal.
- **Definition:** The first half-hour return (or the rest-of-day return) predicts the last half-hour return.
- **Market mechanism:** Option dealers' negative-gamma hedging near the close and late-informed trading (Baltussen et al. 2021).
- **Mathematical implementation:**
  - r_last30 = β·r_first30 (or β·r_open→15:30) + ε, per session.
  - This is a time-of-day feature (the session/time module), not a bar-level oscillator.
  - Knowable at the end of the first half-hour (or at 15:30 ET).
- **Required data:** intraday bars, session times.
- **Pine v6 availability:** session tracking; O(1). Feasible.
- **Proxy limitations:** dealer gamma is not observable in Pine (only via pasted inputs; study: x1_positioning).
- **Useful when:** as a candidate session feature in a learned model on US index products.
- **Fails when:** after costs with OHLCV signals (Mesfin 2026: 0 of 14 families pass on MNQ 5m, 947 days).
- **Validation experiment:** owned by the session-statistics specialist; not repeated here.
- **Existing evidence:** Gao, Han, Li & Zhou (2018): SPY 1993-2013, R² 1.6% in sample, 1.2% out of sample (study-verified). Baltussen, Da, Lammers & Martens (2021): > 60 futures 1974-2020, tied to negative gamma, reverts over the next days (study-verified). Li, Sakkas & Urquhart (2022): 12 of 16 developed markets (study-verified). Mesfin (2026) as above (study-verified).
- **APEX recommendation:** **RESEARCH-ONLY** (a session feature for the learned model). Not part of the momentum block. Redundancy: none with T/M/S (a different clock).
- **Sources:** as listed (all via study: quant_regime §7, ict_time §1.14).

### Consolidated orthogonal factor set: T, M, S⊥
- **Classification:** A (statistical construction); strong for orthogonality, weak for predictive value.
- **Definition:** The recommended replacement for the whole list of section-8 indicators: one trend-level factor, one momentum-change factor and one residual stretch factor.
- **Market mechanism:** None beyond the components; this is a measurement design that stops the same evidence being counted several times (spec 8, 13.2, 25).
- **Mathematical implementation:**
  - **Normalisation:** every raw input is volatility-scaled (divided by u) and passed through a bounded transform before averaging, so instruments and timeframes are comparable: φ(x) = tanh(x/c), with c set to the input's long-run robust scale (1.4826 × its median absolute value over 2,000 bars). Rank-based z-scores are the offline equivalent used in R6-T5.
  - **T (trend level, medium horizon):** T = mean{φ(t₅₀), φ((E20 − E50)/u), φ((E50,t − E50,t−10)/u)}. The three members correlate 0.88-0.98, so T ≈ any one of them; t₅₀ alone is an acceptable cheap form.
  - **M (momentum change):** M = mean{φ(MACD histogram/u), φ(t₂₀,t − t₂₀,t−5)}. corr(T, M) ≈ −0.1, so no residualisation is needed (M⊥ = M − β·T is optional).
  - **S⊥ (residual stretch):** S = mean{φ((C − E20)/u), φ((RSI14 − 50)/50)}; S⊥ = S − β_T·T − β_M·M with 500-bar rolling betas (closed form in the stretch entry).
  - **Optional slow context:** T_slow = φ((E50 − E200)/u) or the daily T via one request; only on daily and higher charts or as HTF context.
  - **Use in BIAS:** b_mom = w_T·T + w_M·M + w_S·S⊥ with weights learned online per chart (L2-shrunk logistic over the geometry baseline, prior 0, prequential scoring), used only if the side-model skill vs geometry is > 0 with z ≥ 2 after n ≥ 200 resolved events; otherwise b_mom = 0 and the panel says "momentum: no measured skill on this chart" (the BIAS-1/REG-6 design in the study).
  - **Use in FCST:** forecast drift μ = 0 by default. If a chart-validated drift exists, shrink it: μ_eff = μ̂·max(0, 1 − 1/t²) (positive-part James-Stein; zero unless |t| > 1; study: quant_pot 1.10).
  - Knowable at close t (all inputs are confirmed-bar values).
- **Required data:** OHLC.
- **Pine v6 availability:** `ta.ema`, `ta.macd`, `ta.rsi`, rolling sums for t-statistics, `ta.sma` of products for betas, `math.tanh` is not a built-in in every version, so use φ(x) = x/√(1 + x²) or 2/(1 + e^{−2x}) − 1 via `math.exp` (built-in). O(1) per bar, about 15 series. Feasible.
- **Proxy limitations:** none.
- **Useful when:** whenever momentum context is wanted without double counting.
- **Fails when:** treated as a signal with fixed weights intraday; the ICs are small and unstable in sign across instruments and years.
- **Validation experiment:** MOM-X1 (orthogonality), MOM-X6 (learned block value).
- **Existing evidence:** [R6-T5] corr(T, M) −0.05 to −0.14; corr(T, S) +0.57 to +0.64; corr(M, S) +0.51 to +0.57; after residualisation corr(T, M⊥) ≈ 0.00, corr(T, S⊥) ≤ +0.02, corr(M⊥, S⊥) ≤ ±0.01 on all 14 series. The endpoint residual of a 20-bar regression is not a clean alternative: corr with t₅₀ −0.15 to −0.21 and with the MACD histogram +0.40 to +0.43 [R6-T6]. Study: an unregularised online logistic lost 3.6-5.5% log-loss; gated learners cost ≤ 0.3% where the base is good (calib_ml via quant_pot 1.15).
- **APEX recommendation:** **INCLUDE-CORE** as the only momentum representation (BIAS candidate features with zero prior weight; FCST zero drift by default; SETUP stretch descriptor; CAL grading). Redundancy: replaces EMA stack, slope, separation, MACD, ROC, RSI, DMI, regression slope and VWAP-as-vote.
- **Sources:** R6-T4, R6-T5, R6-T6. Study: quant_pot 1.10, 1.15; quant_regime REG-3, REG-6; bias_dol BIAS-1/2 (via quant_regime).

---

## 4. Interactions and redundancy

### 4.1 Every signed trend indicator is a kernel on past price changes

For any filter of prices whose weights sum to zero, Σ_k a_k C_{t−k} = Σ_{i≥0} b_i Δ_{t−i} with b_i = Σ_{k≤i} a_k (substitute C_{t−k} = C_t − Σ_{i<k} Δ_{t−i}). The indicators in spec section 8 are, exactly or to first order:

| Indicator | Kernel b_i on Δ_{t−i} | Shape |
|---|---|---|
| ROC_n | 1 for i < n | box |
| Price − EMA_n | (1 − α)^{i+1} | exponential |
| EMA_f − EMA_s (separation, MACD line) | (1 − α_s)^{i+1} − (1 − α_f)^{i+1} | hump, zero at lag 0 |
| EMA_n slope over k bars | α Σ of (price − EMA) over k bars | smoothed exponential |
| OLS slope over n | 6j(n − j)/(n(n² − 1)), j = n − 1 − i | parabola |
| (RSI − 50)/50 | RMA_n(Δ)/RMA_n(|Δ|): exponential kernel divided by an exponential kernel on |Δ| | normalised exponential |
| Signed efficiency ratio sER_n | box / box of |Δ| | normalised box |
| DMI ratio | the RSI form on high/low extensions | normalised exponential |
| MACD histogram | (1 − α₉)^{i+1} on ΔMACD | exponential on the *change* of a hump |

Under independent increments, the correlation of two such features is ρ(a, b) = Σ a_i b_i / √(Σ a_i² · Σ b_i²): it depends only on kernel overlap. [R6-T6] theory vs measured Spearman correlation:

| Pair | Theory (iid) | ES 5m | NQ 5m | ES 1H | BTC 1H | SPX D |
|---|---|---|---|---|---|---|
| ROC20 vs price − EMA20 | 0.86 | 0.86 | 0.86 | 0.85 | 0.86 | 0.85 |
| ROC20 vs 20-bar OLS | 0.91 | 0.89 | 0.89 | 0.87 | 0.87 | 0.89 |
| price − EMA20 vs 20-bar OLS | 0.78 | 0.78 | 0.78 | 0.76 | 0.77 | 0.76 |
| EMA20−50 vs 50-EMA slope (10 bars) | 0.97 | 0.97 | 0.97 | 0.97 | 0.97 | 0.98 |
| EMA20−50 vs MACD 12/26 | 0.89 | 0.87 | 0.87 | 0.88 | 0.88 | 0.90 |
| MACD 12/26 vs 50-EMA slope | 0.96 | 0.95 | 0.95 | 0.96 | 0.95 | 0.96 |
| EMA20−50 vs 50-bar OLS | 0.94 | 0.90 | 0.90 | 0.91 | 0.89 | 0.92 |
| price − EMA200 vs EMA50−200 | 0.90 | 0.91 | 0.92 | 0.89 | 0.91 | 0.93 |
| price − EMA20 vs MACD 12/26 | 0.79 | 0.78 | 0.79 | 0.78 | 0.79 | 0.78 |
| ROC20 vs EMA50−200 | 0.21 | 0.17 | 0.19 | 0.20 | 0.20 | 0.34 |
| price − EMA20 vs EMA20−50 | 0.56 | 0.55 | 0.55 | 0.55 | 0.56 | 0.58 |

(The OLS rows compare the slope kernel with the measured t-statistic, which divides by residual noise; hence the slightly lower measured values.) The agreement on futures, crypto and equity indices shows that the redundancy is **mathematical**: it would hold on any market, and no amount of "confluence" from these indicators adds independent evidence.

### 4.2 Measured clusters (Spearman, averaged over series) [R6-T4]

| Cluster | Members | Within-cluster correlation | Represented in APEX by |
|---|---|---|---|
| Slow trend level | EMA stack, EMA50−200, price−EMA200 | 0.84-0.93 | T_slow (optional, daily/HTF only) |
| Medium trend level | EMA20−50, 50-EMA slope, MACD line, 50-bar regression t | 0.80-0.98 | **T** |
| Fast momentum / stretch | price−EMA20, RSI14, DMI ratio, ROC20, sER20, 20-bar regression t | 0.76-0.99 | **S** (then S⊥) |
| Momentum change | MACD histogram, Δ₅ of the 20-bar t | 0.72-0.76 | **M** |
| Direction-free strength | ADX, |sER|, |t|, R², CHOP | 0.30-0.71 | G = |sER20| (REG only) |
| VWAP deviation | — | 0.82 with medium trend (5m); 0.72 with fast (1H) | not a separate input |

PCA of 15 rank-normalised signed features: PC1 61% / 58% / 61% / 59% / 64%, PC2 20% / 22% / 21% / 22% / 20%, PC3 8% / 8% / 8% / 8% / 7% on 5m / 1H / BTC / EUR / daily; the first three components hold 88-92%. Fifteen indicators carry about three numbers.

### 4.3 How to consolidate so evidence is never counted twice
1. **One representative per cluster** (or an average of members, which is nearly the same number): T, S, M (and T_slow only on daily/HTF).
2. **Gram-Schmidt order T → M → S.** M is already nearly orthogonal to T (−0.05 to −0.14). S is not (0.57-0.64 with T; 0.51-0.57 with M), so S is replaced by S⊥ = S − β_T T − β_M M with rolling betas. After this step all pairwise |ρ| ≤ 0.02 [R6-T5].
3. **Bounded, volatility-scaled inputs** so no single instrument's scale dominates (spec 13.1).
4. **No fixed votes.** The legacy pattern "signal when k of {MA cross, MACD, RSI} agree" (`buy_sell_indicator.pine`) and the averaged RSI+MACD+DMI composite (`XAUUSD_Fast_Balanced_Pro.pine`, lines 206-218) count one or two factors several times. APEX replaces both with T, M, S⊥ and learned weights that start at zero.
5. **Separate the volatility and structure modules.** Displacement bars, breakouts and squeeze fires are volatility events (09_volatility.md); market-structure bias (BOS/CHoCH) belongs to the structure module. Momentum features must not re-enter through those modules: if the structure module already uses a swing-trend state, T is a candidate only if the learned model shows incremental skill over it.
6. **Drift.** No momentum feature sets forecast or probability drift unless the chart's ledger shows that a shrunk drift beats zero (the study measured the engine's 50-bar drift as the single largest probability error: +3.66% log-loss when removed, on all 6 symbols; race calibration slope 0.69 with drift; quant_pot findings 2-3).

### 4.4 What the evidence says about direction
- Intraday ICs are small: on 5m futures every feature is within ±0.03 at H = 12; at H = 48 the change and fast features show +0.02 to +0.04 (macdH +0.031 ± 0.009, 5 of 6 series positive), slow features −0.02 (n.s.).
- On one year of 1H index futures all trend features are negative (−0.05 to −0.07), but the null shows −0.05 for slow features and the four equity index futures count as about 1.9 effective symbols (study: x1_tv_validation), so this is one noisy sample.
- BTC 1H: M⊥ +0.047 ± 0.009 and S⊥ −0.053 ± 0.007 (8 years, one asset): momentum-change continuation with level mean reversion.
- Daily indices 1999-2018: slow trend +0.05 to +0.07, consistent with TSMOM.
- The study's direct test of the question that matters to a DOL engine (which pool is taken first): trend features added to distance geometry never improved out-of-sample log-loss by more than 0.25% on 23 series, including a higher-timeframe trend; choosing the side by an engine-like structure/displacement vote cost 9-12 pp of first-touch accuracy intraday (quant_regime 2.3-2.4). The current leg's direction does not say which pool goes first either (price_action finding 8).

---

## 5. Data requirements and assumptions

- **Data:** OHLC on the chart timeframe; volume only for VWAP; one optional `request.security` for a daily T_slow on intraday charts (with `[1]` and `lookahead_on`, never below the chart timeframe).
- **Warm-up:** EMA200 needs about 600 bars to forget its seed (to 0.25%); rolling betas need 500 bars; the learned model needs ≥ 200 resolved events before any non-zero weight. Until then momentum contributes zero and the panel says so.
- **Units:** every input is divided by the VOL unit u (09_volatility.md), so trend measures are comparable across ES, NQ, gold, FX, stocks and crypto. Using raw price differences or percentage changes without volatility scaling would make thresholds instrument-specific (spec 13.1).
- **Assumptions:**
  - Momentum features are linear or ratio-normalised filters of past returns (exact for EMA, MACD, ROC, OLS; exact identity for RSI; approximate for DMI).
  - Their predictive value, if any, is instrument-, horizon- and period-specific; it must be learned and graded per chart.
  - Returns are fat-tailed and volatility-clustered: bounded transforms and volatility scaling limit the influence of shock bars.
- **Confirmation timing:** all features are computed on confirmed bars and used from that close. Pivot-based features (divergence) are time-stamped at the confirmation bar p + L, never at the pivot bar.

---

## 6. Limitations and failure modes

**By asset class**
- **Index futures (ES, NQ, RTY, YM):** small-tick contracts on which fast trend-following has decayed since 2009 (Kurth et al.); highly correlated with each other (about 1.9 effective symbols for four contracts), so a result on one is not four confirmations. Roll gaps distort EMA200 and long ROC on unadjusted continuous charts; use back-adjusted data for slow features or exclude roll bars.
- **Commodities (CL, GC):** CL showed opposite-signed ICs to the indices on 5m (M⊥ −0.034); GC 1H data were unusable (spliced contracts). Large-tick contracts retained trend-following Sharpe at daily horizons (Kurth et al.).
- **FX:** tick volume only (VWAP unreliable); small samples in our data (EURUSD 1H n = 5,000: all |IC| ≤ 0.07 with SE 0.04-0.05). The 17:00 New York rollover can print artificial extremes on bid charts.
- **Equities and ETFs:** overnight gaps carry much of the variance; EMA and ROC computed on RTH bars mix overnight and intraday returns. Earnings jumps dominate.
- **Crypto spot and perpetuals:** 24/7; BTC 1H shows short-horizon mean reversion (VR16 0.887, z* −2.8; runs z +21) together with momentum-change continuation. Exchange-specific prints differ; perpetual funding introduces 8-hour patterns (study: x1_positioning, quant_pot).

**By timeframe**
- **≤ 5 minutes:** bid-ask bounce and tick-size reversion dominate the shortest lags (Safari & Schmidhuber: reversion below about 15-30 minutes for weak trends).
- **1H:** a 50-bar window spans about two days; the intraday clock affects u, so normalise with the deseasonalised unit.
- **Daily and higher:** the only setting with literature support for trend (TSMOM), still decayed for fast signals.

**Session and DST issues**
- EMA and regression windows count bars, not clock time; across the CME daily halt or weekends, a 50-bar window covers very different amounts of trading. Keep windows in bars (stable estimates) but scale by the clock-aware unit.
- Session VWAP must reset at the exchange's session start in the exchange time zone (CME 18:00 ET), which Pine's default daily anchor may not match on futures; DST is handled by IANA time zones.

**Statistical failure modes**
- **Data snooping:** 16 features × 6 settings × several horizons were examined in R6-T4; isolated cells at 2-3 SE are expected by chance. Only effects that replicate out of sample and across instruments count.
- **Overlap:** forward returns over H bars overlap; use block bootstraps and effective sample sizes.
- **Non-stationarity:** the sign of intraday ICs changes between instruments and years (5m indices positive, 1H indices negative in our samples).
- **Look-ahead:** pivot-based divergence and "trend start" labels are easy to backdate; enforce p + L time-stamping.

---

## 7. Recommendations for APEX (ranked)

| Rank | Recommendation | Decision | Module | Why |
|---|---|---|---|---|
| 1 | Replace all section-8 indicators by the consolidated set T (trend level), M (momentum change), S⊥ (residual stretch), volatility-scaled and bounded | INCLUDE-CORE | BIAS (candidates), SETUP, CAL | 15 indicators ≈ 3 factors (PC1-3 = 88-92%); theory matches measured correlations within ±0.04; residual correlations ≤ 0.02 |
| 2 | Momentum weights in BIAS start at zero and are learned per chart (shrunk online logistic over geometry, prequential gate: skill > 0 with z ≥ 2 after ≥ 200 events) | INCLUDE-CORE | BIAS, CAL | Intraday ICs ≈ 0 and unstable in sign; study: trend adds ≤ 0.25% to side choice; ungated learners lose 3.6-5.5% |
| 3 | Zero forecast drift by default; only a shrunk, chart-validated drift (James-Stein) may enter FCST | INCLUDE-CORE | FCST, DOL | The engine's drift was the largest single probability error (+3.66% log-loss) |
| 4 | Direction-free strength = |sER20| with noise-floor thresholds, for REG display and ledger stratification only | INCLUDE-CORE | REG, CAL | Efficiency labels persist no more than a random walk's; useful for honest description and per-chart testing |
| 5 | Stretch descriptor "EXTENDED" (|price − EMA20| ≥ 2 u_H) in SETUP/UI, with no reversal claim | INCLUDE-CORE (descriptor) | SETUP, UI | Location context traders expect; S⊥ carries any measured reversal |
| 6 | Slow trend arm (daily T or EMA50−200) on daily/weekly charts or as HTF context | INCLUDE-OPTIONAL | BIAS (learned), UI | Consistent with TSMOM; daily IC +0.05 to +0.07 on one sample |
| 7 | VWAP deviation as context/display | INCLUDE-OPTIONAL | UI (volume module owns VWAP) | Changes cluster with timeframe; never an extra vote |
| 8 | One optional EMA line (EMA200) on the chart; oscillator values only in the debug dashboard | INCLUDE-OPTIONAL | UI | Spec 17: no forest of lines or oscillator panels by default |
| 9 | Variance ratio, autocorrelation and runs diagnostics, computed once per load | INCLUDE-OPTIONAL | UI (debug), CAL prior | Explains whether the instrument is mean-reverting at short lags |
| 10 | DMI ratio as an alternative member of S; divergence labels; intraday session momentum | RESEARCH-ONLY | CAL | No consistent edge; possible session feature for the learned model |
| 11 | EMA stack, EMA slope, MACD line, ROC, RSI, DMI, ADX, regression slope as **separate** inputs or votes; ADX ≥ 25 filters; RSI 70/30 reversal triggers; divergence signals; "k of n indicators agree" logic | EXCLUDE | — | Mathematical duplicates of T/M/S; no tested edge; random-walk noise floors |

**What to preserve from earlier projects**
- DOL Engine v2 has no oscillators (good: nothing to remove); its displacement term in the draw vector should go to zero weight (study: REG-7).
- `XAUUSD_Fast_Balanced_Pro.pine` already normalised RSI, MACD and DMI into one composite (lines 206-218), a correct instinct about redundancy; APEX keeps the idea of one composite per cluster and drops the fixed weights and fixed chop scores. Its HTF EMAs use `[1]` with `lookahead_off`, which adds one extra HTF bar of lag; APEX uses `[1]` with `lookahead_on` (study and CONTEXT rule).
- `DOL_Engine_early.pine` shrank and capped its drift (0.5 × EWMA, ±0.5σ); APEX goes further (zero by default, James-Stein if validated).

---

## 8. Open questions and Phase 6 experiments

Pre-registered as in 09_volatility.md: 2-fold or walk-forward time splits, block bootstraps (block = max(H, bars per day)), the sign-flip null for every directional claim, Benjamini-Hochberg control across cells, and the Phase 6 data matrix (CME ES, NQ, RTY, YM, CL, GC clean months; EURUSD, GBPUSD; SPY or a large-cap stock; BTCUSD spot and a BTC perpetual, plus ETH; 5m, 15m, 1H, 4H, D).

| ID | Hypothesis | Outcome | Horizon | Baseline | Metric | Pass criterion |
|---|---|---|---|---|---|---|
| MOM-X1 | The kernel identity predicts the correlation of every indicator pair within ±0.05, and T, M⊥, S⊥ have pairwise |ρ| ≤ 0.05 out of sample | Pairwise Spearman correlations | — | Theory ρ(a, b) under iid increments | Max |measured − theory| and max |ρ| among T, M⊥, S⊥ | ≤ 0.05 on ≥ 90% of pairs × series; residual |ρ| ≤ 0.05 on all series |
| MOM-X2 | Intraday, T has no directional information (|IC| < 0.02); on daily charts T has IC > 0 | Volatility-normalised forward return | H = 12, 48 (intraday); 5, 20 (D) | Sign-flip null IC distribution | Spearman IC with block SE; BH-adjusted | Intraday: pooled |IC| < 0.02 (confirms zero prior); daily: IC > 0 with BH q < 0.05 on ≥ 3 asset classes |
| MOM-X3 | M⊥ (MACD histogram/Δt) has positive IC at about 4 hours on 5m futures and at 12 h on crypto, out of sample (data after 2026-04-15 and new symbols) | Volatility-normalised forward return | H = 48 (5m), 12 (1H) | Null; IC = 0 | IC with block SE | IC > 0 with z ≥ 2 on ≥ 70% of out-of-sample series; otherwise M keeps zero prior |
| MOM-X4 | S⊥ shows mean reversion on crypto 1H (BTC, ETH, SOL) and not on index futures | Volatility-normalised forward return | H = 12 | Null; IC = 0 | IC with block SE | Crypto IC < 0 with z ≤ −2 on ≥ 2 of 3 coins; index |IC| < 0.02 |
| MOM-X5 | Confirmed-pivot RSI divergence does not beat confirming pivots or the null | ±1 u race in the divergence direction | H = 12 (intraday), 10 (D) | Confirming-pivot control; null | Race difference with SE; BH-adjusted | Expected outcome: |div − control| < 3 pp on ≥ 80% of cells (keeps RESEARCH-ONLY); an effect ≥ 3 pp with q < 0.05 on ≥ 3 asset classes would promote it to a learned feature |
| MOM-X6 | The learned momentum block (T, M⊥, S⊥) improves the prequential log-loss of the BIAS side model over distance geometry | Which of the two nearest pools is taken first | until decided, ≤ H | Geometry b/(a+b) | Prequential log-loss difference, cluster-robust z | Improvement ≥ 0.5% with z ≥ 2 on a chart → weights switch on for that chart; report the share of charts where it happens |
| MOM-X7 | A shrunk T-based drift does not improve the forecast-direction Brier score intraday over zero drift | Sign of C_{t+H} − C_t | H = 20, 60, 120 | Zero drift | Brier score and calibration slope | Expected: no improvement intraday (keeps μ = 0); daily improvement ≥ 0.5% with z ≥ 2 would allow a daily drift |
| MOM-X8 | Full-sample variance ratios are stable in sign between halves of the sample per instrument | VR(q) for q = 2, 4, 8, 16 | — | VR = 1 | Robust z* in each half; sign agreement | Same sign and |z*| ≥ 2 in both halves before the diagnostic is shown as "mean-reverting" or "trending" |

**Open questions**
1. Is the BTC 1H pattern (M⊥ positive, S⊥ negative) a crypto-wide microstructure effect (funding, liquidations) or one asset's history?
2. Does the 5m positive IC of change and fast features at H = 48 survive costs? (The study's MNQ result says OHLCV intraday signals do not.)
3. Should T's horizon follow the forecast horizon H (kernel peak near H/2), or stay fixed at 50 bars? To be decided by MOM-X6.
4. How much of any T skill is already in the market-structure module's swing bias? The learned model must test T's increment over structure, not over geometry alone.
5. Does volatility-state conditioning change the sign of momentum ICs (LeBaron effect: serial correlation falls with predictable volatility; intraday session momentum rises with volatility)? A two-way split by the V-axis in MOM-X2/X3 answers it.

---

## 9. Sources

**Opened or verified in this session**
- Pine Script v6 reference (local mirror `docsrc/jabez4jc_pinescriptv6/reference/ta.md`): `ta.ema`, `ta.rma`, `ta.rsi` (uses `ta.rma` of up and down changes), `ta.macd`, `ta.roc` (100·change/src[length]), `ta.dmi` ([+DI, −DI, ADX]), `ta.linreg`, `ta.vwap` (hlc3 default, anchor, stdev_mult), `ta.stdev`, `ta.percentrank`, `ta.pivothigh`/`ta.pivotlow`; `reference/request.md` (40 unique requests).
- Levine, A. & Pedersen, L. H. (2016). Which Trend Is Your Friend? *Financial Analysts Journal* 72(3), 51-66. https://ideas.repec.org/a/taf/ufajxx/v72y2016i3p51-66.html ; https://rpc.cfainstitute.org/research/financial-analysts-journal/2016/which-trend-is-your-friend [verified: abstract via search; full text paywalled].
- Patton, A. J. (2011). *J. Econometrics* 160(1), 246-256 (robust loss for noisy volatility proxies; used for the volatility unit in R6-T1) [verified: abstract via search].

**Verified by the study reports**
- quant_regime.final.md: Moskowitz, Ooi & Pedersen (2012), *JFE* 104(2); Kurth, Eisler, Rej & Bouchaud (2026), arXiv:2607.01550; Safari & Schmidhuber (2025), arXiv:2501.16772; Gao, Han, Li & Zhou (2018), *JFE* 129(2); Baltussen, Da, Lammers & Martens (2021), *JFE* 142(1); Li, Sakkas & Urquhart (2022), *J. Financial Markets* 57; Heston, Korajczyk & Sadka (2010), *J. Finance* 65(4); Lo & MacKinlay (1988), *RFS* 1(1); Portnaya (2026), arXiv:2606.29591; Le (2026), arXiv:2610.11028; Mesfin (2026), arXiv:2605.04004; LeBaron (1992), *J. Business* 65(2); Campbell, Grossman & Wang (1993), *QJE* 108(4); Wilder (1978); Gurrib (2018), *Banks and Bank Systems* 13(3); Kaufman (efficiency ratio).
- quant_pot.final.md: James-Stein shrinkage of drift; Efron & Morris (1975); calibration and gating (with calib_ml).
- price_action.final.md: Filimonov & Sornette (2011); leg-length overshoot law; Brooks and Dow claims tested.
- x1_internals.md, x1_tv_validation.md, x1_positioning.md: breadth divergence tests; effective number of correlated futures; dealer gamma and intraday momentum.

**This session's tests** (code and raw outputs in `/tmp/claude-0/-home-user-m/7ce60006-3639-59b1-8cd3-87355409d58a/scratchpad/r6_tools/`)
- R6-T4 `mom_redund.py` → `out_mom_{5m,5m_H48,1h,btc,eur,d}.txt`: correlation matrices, PCA, ICs vs null, divergence, variance ratios, runs tests.
- R6-T5 `mom_factors.py` → `out_factors_{5m,1h,btc,d}.txt`: the T, M, S trio, residualisation, strength correlations, trio ICs.
- R6-T6 `kernels.py` → `out_kernels.txt`: kernel theory vs measured correlations; regression-residual check.

**Unverified in this session**
- Appel's original MACD specification (the formula used is Pine's documented `ta.macd`).
- Any claim that a specific RSI or MACD threshold is optimal; none was tested or is recommended.
