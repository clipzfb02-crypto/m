# 11 · Statistical Mathematics

**Author role:** R5, quantitative mathematics and statistical modelling.
**Covers:** APEX ULTIMATE spec §10 (statistics and quantitative mathematics) and §20.2 (statistical protections), with links to §13 (decision engine), §14.3 (forecast uncertainty), §15 (probability and calibration) and §20.1 (required tests).
**Status:** research knowledge base (Phase 3). No production code was edited.

**Evidence conventions used in this document**
- **[study:key]**: a number taken from a combined study report at `/tmp/claude-0/-home-user-m/7ce60006-3639-59b1-8cd3-87355409d58a/scratchpad/brief/study/<key>.final.md`. I quote it with its sample and dataset. Where the study's researcher B re-checked a source, I say "verified by study".
- **[R5]**: a number I computed in this session. The scripts and raw outputs are in `/tmp/claude-0/-home-user-m/7ce60006-3639-59b1-8cd3-87355409d58a/scratchpad/r5_stats_tools/`: `dist_stats.py` → `out_dist.txt`, `dep_stats.py` → `out_dep.txt`, `regr_check.py` → `out_regr.txt`, `verify_formulas.py` → `out_verify.txt`, `quantile_check.py` → `out_quantile.txt`, `outliers.py` → `out_outliers.txt`. The scratchpad can be cleared, so the lead should copy that folder into `apex/validation/python/` if it is to be kept. R5 was not allowed to write there.
  - Real data used by [R5]:
    - CME ES, NQ, RTY, YM, CL and GC continuous 1-minute bars, 2026-01-20 → 2026-04-15, timestamps in UTC, 66-84k bars per symbol (`study/amt_data/cme/`). I aggregated them to 5, 15 and 60 minutes.
    - BTCUSD 1-hour bars, 2017-01-01 → 2025-01-07, 70,272 returns (`study/session_data/btc_1h.pkl`).
  - [R5] numbers marked **synthetic** are checks of the formulas only. They are not market evidence.
- **[docs]**: the local Pine v6 reference mirror at `/tmp/claude-0/-home-user-m/7ce60006-3639-59b1-8cd3-87355409d58a/scratchpad/docsrc/jabez4jc_pinescriptv6/`, opened in this session. Files used: `reference/ta.md`, `reference/array.md`, `reference/matrix.md`, `reference/math.md`, `language/type_system.md`, `language/execution_model.md`, `writing_scripts/limitations.md`.
- **Unverified**: classic statistical references that I cite from knowledge but could not open in this session. Network access to the publisher, author, Wikipedia and Firecrawl hosts was blocked or out of credit, so the primary texts were not reachable. Each one is marked "(unverified)" in §9. Its formula is standard, and where possible I checked it numerically in `verify_formulas.py`.
- Line numbers in the existing engine refer to the frozen copy `brief/baseline_v2.pine`.

---

## 1. Scope and role in APEX

The specification asks every APEX model to have "a defined target, sample, horizon and validation method" (§10). It also asks for an honest separation of "heuristic score, relative ranking, model confidence, empirically calibrated outcome probability" (§15). This document supplies the mathematics for both: the estimators, their Pine-feasible online forms, their numerical pitfalls, and the statistical protections the validation phase must apply. The model-card template that every APEX model must fill in is in §5.2.

**Module map used in this document.** These are R5's proposed IDs; the architect may rename them.

| ID | Module (spec name) | What this document gives it |
|---|---|---|
| M0 DATA | Data quality and integrity (spec §13.2 "explicit data-quality weights", §21) | Roll-gap and bad-print detection, a κ cue, a zero-return/tick-discreteness check, a missing-volume flag |
| M1 NORM | Feature normalisation (spec §13.1) | Volatility units (ATR, blended unit, forward variance), robust scale (MAD), robust z, percentile rank, bounded transforms |
| M2 REGIME | A. Market Regime Score | Volatility-state statistics with hysteresis; the evidence that trend labels do not persist; regime-conditioned estimates with partial pooling |
| M3 BIAS | B. Directional Bias Score | Shrinkage of drift, the redundancy algebra of the trend descriptors, offset logistic models behind gates |
| M4 DOL | C/D. Buy-side and sell-side Draw Scores, PoT, race | Base rates, the Beta-Binomial and partial pooling machinery, calibration of any probability label |
| M5 SETUP | E. Setup Quality Score | Feature interactions, multiple-testing discipline for setup filters, R-expectancy tests |
| M6 FQ | F. Forecast Quality Score | Proper scoring rules, calibration hierarchy, reliability, sample-size rules |
| M7 FCST | Forward projection (spec §14) | Regression and drift shrinkage, horizon-specific empirical error quantiles, coverage tests |
| M8 CAL | Probability and calibration (spec §15): ledger and self-grading | Shadow ledger statistics, design effect, confidence sequences, gated online Platt scaling, mirror control |
| M9 RISK | Risk and execution (spec §16) | Transaction-cost sensitivity, gross and net R, break-even cost |
| M10 INTER | Intermarket (spec §12) | Correlation estimators and their measured instability |
| MV | Offline validation harness (spec §20, Phase 6, Python) | Walk-forward design, purging and embargo, bootstrap, Monte Carlo, DSR, PBO, Holm/BH |

**Notation (used throughout).**
- Bar t closes at its confirmed close, the `barstate.isconfirmed` tick. O, H, L, C are its prices.
- Log return: r_t = ln(C_t/C_{t−1}).
- TR_t = max(H_t, C_{t−1}) − min(L_t, C_{t−1}). ATR_n is Wilder's RMA of TR, so ATR_t = ATR_{t−1} + (TR_t − ATR_{t−1})/n.
- τ = `syminfo.mintick`. H = forecast or outcome horizon in bars.
- 1{·} is the indicator function. Φ and φ are the standard normal CDF and density. σ(z) = 1/(1 + e^{−z}) and logit(p) = ln(p/(1−p)).
- **Knowable at** means the first bar close at which a value can be computed from data available then. Learning updates happen only at an outcome's **resolution bar**: the first touch, or t + H.

**Five governing facts from the study.** These are not opinions; they set the defaults of this document.
1. **Direction is close to a random walk at chart horizons; volatility is strongly structured.**
   - Trend labels (ER, CHOP, Hurst) have ≈ 0 correlation between consecutive windows: ER −0.04 … +0.01 on 23 series.
   - The volatility state persists: corr of ln(ATR14/ATR100) at a 14-bar lag is 0.49-0.80 [study:quant_regime, 23 series, CME futures, EURUSD and daily indices].
   - [R5]: equity-index futures variance ratios VR(4) and VR(12) have heteroskedasticity-robust |z*| ≤ 1.5 on every series at 1-60 min. Lag-1 ACF of |r| is 0.16-0.42 on all of them (§3.7-3.8).
2. **A random level at the same distance is the baseline that matters.** Base rates are high: a level 1, 2 or 3 ATR away is traded through within 30 bars 75-80%, 54-62% and 39-47% of the time [study:skeptic, CME futures and EURUSD]. This matches Brownian first passage 2Φ(−κd/√H) with κ ≈ 1.39-1.54 [study:skeptic].
3. **Learners do not beat a well-calibrated distance baseline out of sample on clean data.** The distance-matched baseline has calibration slope 0.93-1.04 on 13 clean datasets (76,181 candidate probes) [study:calib_ml].
   - Ungated learners lose log-loss: unregularised online SGD −3.6 … −5.5%.
   - Gated learners cost ≤ 0.26% on clean data and rescue a corrupted base (GC 1-hour with roll gaps) by +5.6 … +10.5% [study:calib_ml].
4. **Drift estimated from recent bars is noise that hurts.** Removing the 50-bar drift improves PoT log-loss by +3.66% (95% CI +2.99 … +4.32%, day-block bootstrap, 326 symbol-days, about 1.2 M rows, 5-min, H = 30) on all 6 CME symbols [study:quant_pot].
5. **Statistics cannot catch look-ahead.** A deliberately leaky oracle with Sharpe 35 survives the deflated Sharpe ratio and PBO [study:skeptic, citing Gençay 2026, abstract re-read by study B]. Construction rules (§3.25) are the only protection.

---

## 2. Classification table

E = established mechanics or exchange documentation; A = academic or statistical evidence; D = discretionary practitioner theory; C = contested or unsupported by tests. The grade measures the evidence for the concept's **role in APEX**, not the mathematical correctness of the estimator, which is a theorem in most cases.

| Concept | Class | Evidence grade | Objectively calculable? | One-line note |
|---|---|---|---|---|
| Welford and EWMA running moments | A | strong | yes | Exact online mean and variance; the infrastructure for every z-score and ledger |
| Standard deviation as volatility scale | A | strong | yes | Efficient under normality, but inflated by jumps: SD/(1.4826·MAD) = 1.5-2.2 on real returns [R5] |
| Median absolute deviation (MAD) | A | strong | yes | Robust scale with 50% breakdown. `ta.dev` is NOT MAD: it is the mean absolute deviation from the SMA [docs] |
| Z-score / robust z-score | A | strong | yes | A normalisation transform, not a probability. Needs bounding (tanh or percentile) |
| Percentile rank / rolling quantiles | A | strong | yes | Scale-free and distribution-free. Built-ins are exact over a lookback [docs] |
| P² streaming quantile | A | moderate | yes | Accurate on stationary data (≤ 1.1% median error, synthetic), 9-12% error on real intraday \|r\| [R5]. Not recommended |
| Fat tails: skewness, kurtosis, L-moments, tail index | A | strong (existence) / weak (as features) | yes | Excess kurtosis is unstable (ES 5-min 343 → 4.9 after trimming 0.1%) [R5]. Use L-kurtosis τ₄ for diagnostics |
| Volatility normalisation (ATR, blended unit, volatility clock) | A | strong | yes | The single most useful transform. ATR14 alone is biased by mean reversion of volatility [study:quant_regime] |
| Return autocorrelation | A | strong (≈ 0 at chart horizons) | yes | A diagnostic, not a signal. \|r\| autocorrelation (volatility clustering) is the real structure |
| Variance ratio (Lo-MacKinlay) | A | strong | yes | Robust z* ≈ 0 for index futures; BTC 1-hour VR(4) = 0.920, z* −4.1 [R5]. A rolling VR or Hurst regime label is noise [study:quant_regime] |
| Hurst-exponent regime labels | C | none (as classifier) | yes | Simulated SD 0.069 at w = 96; labels a random walk "persistent" on 12-16% of bars [study:quant_regime] |
| Pearson / Spearman correlation | A | strong (method) | yes | Rolling correlation dispersion is 2-8.5× its iid sampling noise; sign flips in 28-60% of windows for weakly correlated pairs [R5] |
| Correlation stability gate | A | moderate | yes | Required before any intermarket use (spec §12) |
| OLS linear regression (rolling) | A | strong (method) / weak (as signal) | yes | Its slope is a parabolic-weighted mean return, corr 0.91-0.95 with ROC over the same window (exact identity) [R5] |
| Regression t-statistic / R² as "trend significance" | C | none | yes | On a driftless random walk, \|t\| > 2 in 83% of 50-bar windows and median R² = 0.44 [R5, synthetic]. Never display |
| Huber robust regression (IRLS) | A | moderate | yes | Feasible in Pine. Same slope sign as OLS in 98.2% of ES 5-min windows [R5]: small gain |
| Theil-Sen / repeated-median regression | A | moderate | yes | O(n²) per bar. 95% sign agreement with OLS [R5]. Research only |
| Conditional probability with a distance-matched base rate | A | strong | yes | Every displayed rate must be shown against its base rate [study:skeptic] |
| Beta-Binomial updating with shrinkage | A | strong | yes | The posterior mean (k + m·p₀)/(n + m) is already in the engine (`priorM = 30`) |
| Poisson-Gamma lift shrinkage | A | strong | yes | Replaces the noisy `f_calMult` (α = 2 is far too weak) [study:calib_ml] |
| Empirical-Bayes partial pooling | A | strong | yes | +1.79% log-loss for a volatility-state split; best design is time-of-day rows plus the blended unit [study:quant_pot, quant_regime] |
| Offset logistic / probit models | A | strong (method) / moderate (benefit) | yes | Only behind a prequential gate [study:calib_ml] |
| Unregularised online SGD logistic | C | strong (negative) | yes | −3.6 … −5.5% log-loss on 13 clean sets [study:calib_ml] |
| Gated online Platt scaling (2-parameter ONS) | A | moderate | yes | Costs ≤ 0.23% on clean data, +5.6% on a broken base [study:calib_ml] |
| Feature interactions | A | weak | yes | Need about 4× the data of main effects. Test only pre-registered interactions |
| Regime-conditioned statistics (stratify + pool) | A | moderate | yes | Key on volatility and the clock, not on trend labels [study:quant_regime] |
| Proper scores (Brier, log-loss), reliability, calibration slope | A | strong | yes | The only legitimate basis for a "probability" label (spec §15) |
| Wilson interval | A | strong | yes | Exact coverage 0.957-0.979 where Wald drops to 0.456 (n = 20, p = 0.97) [R5, exact computation] |
| Design effect / overlap-aware variance | A | strong | yes | deff ≈ 4 for every-bar 30-bar touch outcomes on 5-min ES/NQ [R5] |
| Confidence sequences (anytime-valid) | A | strong | yes | Peeking at z ≥ 2 gives 10-20% false "edge" [study:calib_ml]; the boundary fixes it |
| Mirror / placebo paired control | A | moderate | yes | False alarms 13.5% → 0.3-0.7% on 288 real null paths, with more power [study:skeptic] |
| iid bootstrap | A | strong (negative for dependent data) | yes | Understates the SE of overlapping outcomes by about 2× [R5] |
| Block / stationary bootstrap | A | strong | yes (offline) | Matches batch means (deff 4.0 vs 4.2) [R5]. Offline only |
| Monte Carlo (synthetic nulls, sign-flip and mirror series) | A | strong | yes (offline) | The tool used to validate every test in the study |
| Bonferroni / Holm (FWER) | A | strong | yes | FWER 0.046-0.048 vs 0.92 unadjusted, m = 55 [R5, synthetic] |
| Benjamini-Hochberg (FDR) | A | strong | yes | FDR 0.046 with more power than Holm [R5, synthetic] |
| Deflated Sharpe Ratio | A | strong (theory) | yes (offline) | Needs the number of trials. The expected-maximum approximation is within 0.002 of Monte Carlo [R5, synthetic] |
| Probability of Backtest Overfitting (CSCV) | A | strong (theory) | yes (offline) | Noisy in a single study: 0.15-0.72 under a pure null [R5, synthetic] |
| Walk-forward / prequential evaluation | A | strong | yes | Prequential grading is the in-Pine analogue |
| Purging and embargo | A | strong | yes (offline) | Mandatory whenever labels span H bars |
| Look-ahead / leakage / survivorship rules | E/A | strong | yes (by construction) | Not detectable statistically [study:skeptic] |
| Transaction-cost sensitivity | E/A | strong | yes (needs a cost input) | Gross per-trade content of OHLCV signals is 0.07-1.50 index points vs a 2-point friction on MNQ [study:skeptic, citing Mesfin 2026] |
| "PoT capped at 95%", "probability" shown without a base rate | C | none | n/a | Marketing convention; not a model property [study:quant_pot, skeptic] |

---

## 3. Features

### 3.1 Running moments: mean, variance and standard deviation (Welford, EWMA, ring buffer)
- **Classification:** A; strong (method). This is infrastructure.
- **Definition:** Sample mean x̄ = (1/n)Σx_i; unbiased variance s² = Σ(x_i − x̄)²/(n − 1); biased (population) variance Σ(x_i − x̄)²/n. Pine `ta.stdev` and `ta.variance` default to `biased = true` [docs].
- **Market mechanism:** None in itself. It is the scale against which moves are judged. Returns are heteroskedastic, so any fixed-window SD lags regime changes. An exponentially weighted SD adapts faster but is noisier.
- **Mathematical implementation:**
  - **Welford (expanding), exact and stable:** n ← n + 1; δ = x − m; m ← m + δ/n; M₂ ← M₂ + δ·(x − m); s² = M₂/(n − 1).
  - **Windowed (ring buffer of length W):** on removal of x_old, n ← n − 1; δ = x_old − m; m ← m − δ/n; M₂ ← M₂ − δ·(x_old − m).
    - Removal accumulates rounding error. Recompute two-pass from the buffer every W bars, and floor M₂ at 0.
  - **EWMA (incremental, West-type):** δ = x − m; m ← m + αδ; v ← (1 − α)(v + αδ²). Here α = 1 − 0.5^{1/h} for a half-life of h bars.
    - Warm start: α_t = max(α, 1/t), which gives the cumulative mean for the first 1/α bars.
    - RiskMetrics uses λ = 1 − α = 0.94 on daily data [study:quant_pot, citing RiskMetrics 1996].
  - **Defaults.** Returns: W = 50 (matches the engine's `potLen`, line 916) or an EWMA half-life of about one session. Ledger accumulators: expanding Welford.
  - **Knowable at:** bar t close. With `ta.*` on the realtime bar, the value includes the unclosed bar. Confirmed logic must read `[1]`, or run only when `barstate.isconfirmed`.
- **Required data:** close (or any series). No volume.
- **Pine v6 availability:** feasible.
  - `ta.sma`, `ta.stdev(src, len, biased)`, `ta.variance`, `ta.ema`, `ta.rma`, `math.sum` and `array.stdev/variance/avg` [docs].
  - Welford and EWMA need `var float` state or a `var array<float>`. The `var` state rolls back on each realtime tick and commits at close [docs: execution_model.md, "rollback"].
- **Proxy limitations / numerical pitfalls:**
  1. Pine floats have "internal precision of 1e-16", and **comparison operators round float operands to nine fractional digits** [docs: type_system.md]. Therefore `if sigma > 0` is false for σ < 5e-10. That is realistic for a price-unit SD on sub-micro-priced crypto tokens. Compute scale on log returns or in ATR units, never in raw price units, before comparing.
  2. The reference's "Pine equivalent" of `ta.stdev` snaps |x − mean| ≤ 1e-10 to 0 [docs: ta.md]. The same sub-micro-price hazard applies.
  3. Running sums Σx² − (Σx)²/n: [R5] on ES and NQ 1-minute prices (W = 50) the relative error is median 1e-10, max 3e-8. At ×1000 scale it is median 7e-7, max 6e-4. In float64 this is acceptable at futures price scales, but worse for large or near-constant series (volume², cumulative sums over 100k bars). Use Welford, or shift the data by a reference value. Welford vs two-pass on 83,860 ES 1-minute returns: relative difference 3.7e-15 [R5].
  4. `ta.stdev` ignores `na`s and uses the last `length` non-na values [docs]. After a data gap, the window spans the gap silently.
- **Useful when:** always, as a component.
- **Fails when:**
  - jumps dominate the window: one news bar inflates SD for W bars;
  - the series is non-stationary across sessions: the overnight and RTH mix.
  Use robust scale (§3.2) or deseasonalised returns (§3.6).
- **Validation experiment:** unit tests in MV.
  - H₀: the Pine port equals a two-pass float64 reference within 1e-9 relative error on 10 symbols × 3 timeframes, including a sub-micro-priced crypto symbol.
  - Metric: maximum relative error. Pass: ≤ 1e-9, with no negative variances.
  - Also: the EWMA half-life recovers the theoretical lag on a synthetic step change (pass within ±1 bar).
- **Existing evidence:** standard theory. Numerical results: [R5] above.
- **APEX recommendation:** INCLUDE-CORE (M1 NORM, M8 CAL). Use EWMA for adaptivity and Welford for ledgers. Overlaps with §3.2 (robust scale) and §3.6 (volatility units). One scale estimator per role.
- **Sources:** [docs] ta.md (`ta.stdev`, `ta.variance`), type_system.md (precision, comparison rounding), execution_model.md (rollback); Welford 1962 (unverified); West 1979 (unverified); RiskMetrics 1996 via [study:quant_pot].

### 3.2 Median absolute deviation (MAD) and robust scale
- **Classification:** A; strong.
- **Definition:** MAD = median_i |x_i − median(x)|. The consistent normal-scale estimator is σ̂_MAD = 1.4826·MAD (1.4826 = 1/Φ⁻¹(0.75)). Its breakdown point is 50% (vs 0% for SD).
- **Market mechanism:** Intraday returns mix a calm bulk with rare jumps: news, rolls, bad prints, thin-session spikes.
  - [R5]: on 2026-03-23 11:05 UTC all six CME futures jumped in the same minute (ES +180 bp, z ≈ 60; CL −458 bp).
  - YM printed ±66 bp jump-and-back bars on 2–29 contracts at 06:59-07:00 UTC on 2026-03-18 (`out_outliers.txt`).
  - A robust scale measures the bulk without being captured by such bars.
- **Mathematical implementation:**
  - Exact rolling MAD over W bars: keep a ring buffer b of the last W values; m = `array.median(b)`; fill d_i = |b_i − m|; MAD = `array.median(d)`. Cost O(W log W) per confirmed bar.
  - Cheap lagged variant: MAD* = `ta.median(math.abs(x − ta.median(x, W)), W)`. It uses deviations from the median at each value's own time; it is biased slightly upward in trends.
  - **Floors:** σ̂ = max(1.4826·MAD, IQR/1.349, k_τ·τ/C), with k_τ = 0.5. This guards against tick discreteness: [R5] the share of exactly-zero 1-minute returns is ES 9.5%, CL 10.1%, RTY 6.5%, YM 5.9%, NQ 2.0% and GC 2.3%. If more than 50% of values are equal, MAD = 0.
  - Ratio diagnostic ρ_tail = SD/σ̂_MAD: 1 for normal data, 1.5-2.2 on CME and BTC returns at 1-60 min [R5].
  - **Knowable at:** bar t close (W values up to and including t).
- **Required data:** any series.
- **Pine v6 availability:** feasible.
  - `ta.median(src, len)` ignores `na` [docs]. `array.median`, `array.percentile_linear_interpolation` (for the IQR) and `array.sort` are available.
  - **Pitfall: `ta.dev` is the mean absolute deviation from the SMA**, per its documented Pine equivalent [docs]. It is not robust: for normal data it equals 0.798σ.
- **Proxy limitations:** none beyond the floor issue. Rousseeuw-Croux Qn/Sn are more efficient (82%/58% vs 37% for MAD) but O(W²) (unverified); not needed.
- **Useful when:** you are standardising a feature that has occasional spikes, such as volume, range or returns, for z-scores or thresholds.
- **Fails when:** the data are discrete or the window is mostly flat (MAD = 0, hence the floors). It also fails in very short windows (W < 20: high variance).
- **Validation experiment:** pre-registered in MV.
  - H: robust-z thresholds (|z_r| > 3) have a more stable exceedance rate across volatility terciles than SD-z thresholds.
  - Outcome: the exceedance share per tercile. Sample: 6 CME futures, 5-min and 1-hour, plus BTC 1-hour; walk-forward by month.
  - Metric: the max/min ratio of exceedance rates across terciles. Test: block bootstrap CI of the ratio difference.
  - Pass: the robust ratio is lower, with the CI excluding 0.
- **Existing evidence:** [R5] SD/σ̂_MAD = 1.51-2.22 across 24 CME series and 2.02 (BTC 1-hour). The excess kurtosis trimmed at 0.1% falls by one to two orders of magnitude (§3.5).
- **APEX recommendation:** INCLUDE-CORE (M1 NORM, M0 DATA as a spike detector). Never use `ta.dev` as a robust scale. Overlaps with SD (§3.1) and ATR (§3.6): use ATR for distances, MAD for standardising features.
- **Sources:** [docs] ta.md (`ta.dev`, `ta.median`), array.md; Hampel 1974 and Rousseeuw & Croux 1993 (unverified).

### 3.3 Z-score and robust z-score (bounded)
- **Classification:** A; strong as a transform. It is never a probability.
- **Definition:** z_t = (x_t − μ̂_t)/σ̂_t, and robust z_t = (x_t − med_t)/(1.4826·MAD_t).
- **Market mechanism:** It puts features on a common scale, as spec §13.1 requires. A z-score does **not** map to a tail probability through Φ, because returns are fat-tailed (§3.5). A "3σ" move is far commoner than 0.27%.
- **Mathematical implementation:**
  - Use statistics estimated **before** x_t enters: z_t = (x_t − μ̂_{t−1})/σ̂_{t−1}. Otherwise a spike shrinks its own z (masking).
  - Bounded transform for scoring: b_t = tanh(z_t/c), c = 2, so |b| < 1 and z = 2 maps to 0.76. Alternatively use the percentile rank (§3.4).
  - Winsorise inputs at ±k (k = 5) before they enter running moments, to limit spike contamination.
  - **Knowable at:** bar t close.
- **Required data:** any series plus its scale.
- **Pine v6 availability:** feasible. Use `ta.sma` and `ta.stdev` with `[1]`, or `array.standardize` for one-off arrays [docs]. O(1) with EWMA.
- **Proxy limitations:** z on volume is meaningless when volume is missing or synthetic. FX spot volume on TradingView is tick count or venue-specific; a volume-quality flag from M0 is required.
- **Useful when:** combining heterogeneous features; detecting abnormal bars, as in spec §9 ("abnormal price movement").
- **Fails when:** treated as Φ(z). Also with heavy seasonality: a 09:30 ET bar always has a large z unless deseasonalised (§3.6).
- **Validation experiment:** H: deseasonalised robust z-exceedances (|z| > 3) occur at a stable rate across clock hours.
  - Metric: χ² test of uniformity of the exceedance rate over 8 NY 3-hour blocks, with a block bootstrap for dependence.
  - Pass: no block outside a 2× ratio. Compare with raw z, which is expected to fail.
- **Existing evidence:** [R5] raw excess kurtosis falls from 154-343 to 3.1-6.0 on equity-index 5-min after time-of-day deseasonalisation. That shows how much of the "abnormality" of raw z is the clock (§3.5, table B).
- **APEX recommendation:** INCLUDE-CORE (M1 NORM), as a bounded transform. EXCLUDE any label converting z to a "% chance". It is redundant with the percentile rank (§3.4): choose one transform per feature (§4).
- **Sources:** [docs] array.md (`array.standardize`); [R5] `out_dist.txt`.

### 3.4 Percentile rank and rolling quantiles (exact, P², stochastic approximation)
- **Classification:** A; strong (exact built-ins) / moderate (streaming estimators).
- **Definition:**
  - Percentile rank: PR_t = 100·#{i = 1..L : x_{t−i} ≤ x_t}/L. Pine's `ta.percentrank` uses "how many previous values was less than or equal to the current value" [docs].
  - q-quantile: Q_t(p) = the p-th percentile of the last L values.
- **Market mechanism:** Distribution-free normalisation. "ATR in its 90th percentile" means the same thing on ES and on BTC. It is robust to fat tails because it uses only ranks.
- **Mathematical implementation:**
  - Exact: `ta.percentrank(x, L)`, `ta.percentile_linear_interpolation(x, L, p)` or `ta.percentile_nearest_rank(x, L, p)`.
  - Mid-rank tie correction (needed for discrete series): PR = 100·(#< + ½·#=)/L. Built-ins count ≤, which biases ranks upward under ties.
  - Map to [−1, 1]: 2·PR/100 − 1.
  - Defaults: L = 250 (about a month of 1-hour bars, or one session-week of 5-min bars). For regime percentiles use L ≥ 500 where the history allows.
  - **P² (Jain-Chlamtac), O(1) memory:** five markers with heights q₀..q₄, positions n_i and desired positions n'_i; parabolic or linear adjustment of the interior markers. Implemented and tested in `dep_stats.py`.
  - **Stochastic-approximation tracker (O(1), a windowed analogue):** q ← q + η·s_t·(p − 1{x_t < q})/max(min(p, 1 − p), 0.05), where s_t is an EWMA of |x| (scale) and η = 0.002-0.005.
  - **Knowable at:** bar t close.
- **Required data:** any series.
- **Pine v6 availability:** feasible.
  - The built-ins accept a series-int length. `ta.percentrank` and `ta.percentile_linear_interpolation` return `na` if any value in the window is `na`; `ta.percentile_nearest_rank` ignores `na` [docs]. Guard with `nz` or warm-up logic.
  - `array.percentrank(id, index)` and `array.percentile_*` work on arrays [docs].
  - The cost of the built-ins is not documented. Measure with the Pine Profiler (pine_eng PENG-2).
- **Proxy limitations / numerical pitfalls:**
  - [R5] P² is accurate on stationary streams: median relative error 0.1-1.1% on iid |N|, |t₃| and GARCH-like series (synthetic).
  - On real ES 5-min |r| its error vs the exact expanding quantile is 9-12% (median), because intraday seasonality and volatility regimes make the stream non-stationary. P² converges to a long-run quantile that is not the quantity of interest.
  - The SA tracker with η = 0.002-0.005 follows the exact rolling-500 quantile within about 8-9% (median). That is less than the 11-13% gap between the rolling-500 and rolling-1000 exact quantiles themselves [R5, `out_quantile.txt`]. Larger η is worse (26-34% at η = 0.02-0.05).
- **Useful when:** you need a regime percentile (ATR, range, volume) or a threshold that must work on any instrument (spec §13.1).
- **Fails when:**
  - the lookback straddles a structural change, such as a contract roll or a new session schedule;
  - volume is synthetic;
  - fewer than L bars exist (warm-up: return `na` and give a data-quality weight of 0, as spec §13.2 requires).
- **Validation experiment:** H: percentile-normalised features have stable cross-instrument distributions.
  - Metric: the Kolmogorov-Smirnov distance between instruments' PR distributions, by year. Pass: KS < 0.05 vs > 0.2 for raw ATR in ticks.
  - Plus a cost test: the Profiler time per bar for L = 250 vs 500 on 20k bars.
- **Existing evidence:** [R5] as above. The DOL Engine early version already used `ta.percentrank(atr, 200)` for a volatility filter (`apex/legacy/DOL_Engine_early.pine` line 1022).
- **APEX recommendation:** INCLUDE-CORE (M1 NORM, M2 REGIME), using the exact built-ins. The SA tracker is INCLUDE-OPTIONAL only for windows too long for the built-ins. P²: EXCLUDE. Redundant with the z-score (§3.3) for the same feature.
- **Sources:** [docs] ta.md (`ta.percentrank`, `ta.percentile_*`), array.md; Jain & Chlamtac 1985 (unverified); Robbins & Monro 1951 (unverified); [R5] `out_dep.txt` G, `out_quantile.txt`.

### 3.5 Return distributions, fat tails, skewness and kurtosis
- **Classification:** A; strong for the existence of fat tails. Weak for moments as forecasting features.
- **Definition:**
  - Central moments m_k = (1/n)Σ(r − r̄)^k. Skewness g₁ = m₃/m₂^{3/2}; excess kurtosis g₂ = m₄/m₂² − 3 (normal 0).
  - L-moments (Hosking): with b_k = n⁻¹Σ_{i} [(i−1)…(i−k)]/[(n−1)…(n−k)]·x_(i), λ₂ = 2b₁ − b₀ and λ₄ = 20b₃ − 30b₂ + 12b₁ − b₀. **L-kurtosis τ₄ = λ₄/λ₂** (normal 0.1226; Laplace 0.2357).
  - Moors' octile kurtosis K_M = [(E₇ − E₅) + (E₃ − E₁)]/(E₆ − E₂), where E_j is the j/8 quantile (normal 1.233).
  - Hill tail index α̂ = [(1/k)Σ_{i=1..k} ln(X_(i)/X_(k+1))]⁻¹ over the top k = 2.5% of |r|. If α̂ < 4, the population kurtosis is infinite and the sample kurtosis does not converge.
- **Market mechanism:** Fat tails come from four sources:
  1. jumps (news, events, liquidations);
  2. volatility clustering (a mixture of variances);
  3. intraday seasonality (a mixture again);
  4. microstructure (tick discreteness, bad prints, roll gaps).

  Stop-loss cascades once a level is crossed are a mechanism for jumps exactly at liquidity [study:quant_pot, academic_sr, citing Osler 2005, verified by study].
- **Mathematical implementation (descriptive; not for signals):**
  - Report τ₄ and the SD/σ̂_MAD ratio rather than g₂.
  - For the forecast cone (M7), use empirical H-bar return quantiles in volatility units, not Gaussian ±kσ√H.
  - For first-passage maths, the reflection identity P(touch within H) = 2·P(X_H beyond d) holds on real bars: ratio 1.99-2.02 at 0.5-4 ATR on 5-min (H = 30) and 1-hour (H = 12) CME bars [study:quant_pot]. So fat tails enter only through the terminal distribution. An empirical excursion surface captures them automatically.
  - **Knowable at:** descriptive statistics over a closed window.
- **Required data:** OHLC.
- **Pine v6 availability:** feasible, with caveats. g₁ and g₂ via `math.sum` of powers (O(1) rolling); τ₄ via a sorted ring buffer (O(W log W)); no incomplete-gamma or beta functions exist. Kurtosis on a HUD is not recommended.
- **Typical values.** [R5], intra-session log returns, CME 1-minute source Jan-Apr 2026, BTC 2017-2025.

| Series (n) | skew | excess kurt | excess kurt, 0.1% trimmed | τ₄ (N = 0.123) | SD/σ̂_MAD | Hill α̂ | zero returns |
|---|---|---|---|---|---|---|---|
| ES 1-min (83,860) | +3.63 | 194 | 6.3 | 0.296 | 1.82 | 3.06 | 9.5% |
| ES 5-min (16,723) | +7.20 | 343 | 4.9 | 0.285 | 1.75 | 3.32 | 4.3% |
| ES 60-min (1,338) | +0.69 | 7.9 | 3.3 | 0.266 | 1.53 | 3.83 | 1.3% |
| NQ 5-min (16,724) | +4.04 | 154 | 5.1 | 0.282 | 1.64 | 3.47 | 0.9% |
| RTY 5-min (16,710) | +4.46 | 175 | 7.7 | 0.314 | 1.86 | 2.99 | 3.1% |
| YM 5-min (16,721) | +5.70 | 257 | 7.0 | 0.315 | 1.89 | 3.12 | 2.6% |
| CL 5-min (16,544) | −4.91 | 229 | 14.5 | 0.340 | 2.15 | 2.39 | 4.7% |
| CL 60-min (1,324) | −1.81 | 20.8 | 8.1 | 0.327 | 1.92 | 2.42 | 1.7% |
| GC 5-min (13,586) | −0.53 | 20.0 | 8.7 | 0.332 | 1.86 | 2.84 | 1.0% |
| GC 60-min (1,174) | −1.55 | 14.0 | 5.2 | 0.304 | 1.71 | 4.03 | 0.1% |
| BTC 1-hour (70,272) | −0.31 | 31.8 | 9.5 | 0.345 | 2.02 | 2.90 | 0.2% |
| BTC 4-hour (17,568) | −0.35 | 13.8 | 6.6 | 0.329 | 1.93 | 3.30 | 0.1% |
| BTC 1-day (2,928) | −0.75 | 12.5 | 3.1 | 0.274 | 1.58 | 4.28 | 0.0% |

  **Kurtosis decomposition** [R5, table B in `out_dist.txt`]. Columns: raw → deseasonalised by NY time-of-day RMS (in-sample, descriptive) → divided by a causal EWMA σ with a half-life of one session-day.

| Series | excess kurtosis | τ₄ |
|---|---|---|
| ES 5-min | 343 → 3.7 → 2.7 | 0.285 → 0.224 → 0.203 |
| NQ 5-min | 154 → 3.1 → 2.5 | 0.282 → 0.216 → 0.200 |
| CL 5-min | 229 → 8.8 → 5.9 | 0.340 → 0.313 → 0.227 |
| GC 5-min | 20.0 → 6.9 → 5.3 | 0.332 → 0.311 → 0.244 |
| BTC 1-hour | 31.8 → 30.7 → **204** | 0.345 → 0.343 → 0.273 |

  Reading:
  1. The skew and kurtosis of a three-month intraday sample are set by a handful of bars. Trimming 0.1% takes ES 5-min from 343 to 4.9, and the sign of skew is set by the biggest event (+ for the indices, − for CL in this sample).
  2. Hill α̂ ≈ 2.4-4.6 means the fourth moment may not exist, so the sample kurtosis is not a stable statistic.
  3. On CME data, the clock plus volatility clustering explain most of the kurtosis. The conditional (vol-standardised) excess kurtosis is still 1.8-5.9.
  4. **On BTC, volatility standardisation makes the conditional tails fatter.** Jumps arrive out of calm states: 2019-04-02 04:00 UTC was +11.2% in one hour against an EWMA σ of 18.5 bp, z ≈ 60. A volatility model cannot anticipate these.
  5. BTC 1-hour excess kurtosis by calendar year ranges from 7.5 (2024) to 115 (2020) [R5]: unstable across samples.
- **Proxy limitations:** OHLC bars cannot separate a genuine jump from a bad print. A cross-instrument simultaneity check helps: the 2026-03-23 jump appeared in all six futures. Continuous-futures roll gaps inflate kurtosis unless back-adjusted, and back-adjustment is off by default on TradingView [study:calib_ml, citing the TradingView help centre via search summary].
- **Useful when:** choosing estimators (robust over moment-based), sizing forecast bands (empirical quantiles), stress-testing (spec §21 "news-like spikes").
- **Fails when:** used as a signal ("high kurtosis → reversal"). No evidence was found for that, and the study did not test it. Moments over short windows are dominated by the largest bar.
- **Validation experiment:** H: Gaussian ±1.645σ√H forecast bands under-cover the 90% interval, while empirical-quantile bands in volatility units are within ±2 pp.
  - Outcome: whether the realised H-bar return falls inside the band. Sample: 6 CME futures (5-min, 1-hour) and BTC 1-hour, walk-forward.
  - Metric: coverage, with a Kupiec unconditional-coverage likelihood-ratio test using block clustering.
  - Pass: empirical bands have coverage within [88%, 92%] and Kupiec p > 0.05 on ≥ 5 of 7 series.
- **Existing evidence:** [R5] tables above. [study:quant_pot]: Perelló et al. 2011 (paper read by study A) found the Wiener model under-estimates first passage for x ≳ v_t and over-estimates it for x ≲ 0.1·v_t. An analytic σ₅₀ PoT at 6 ATR gives 0.118 vs realised 0.150 (5-min, H = 30). [study:x1_implied_vol] has the option-implied view; not used here.
- **APEX recommendation:** RESEARCH-ONLY for moments as features or displays. INCLUDE-CORE for the *consequence*: robust estimators (§3.2), empirical-quantile forecast bands (M7) and the empirical PoT surface (M4). The τ₄ diagnostic may go in the debug dashboard, off by default.
- **Sources:** [R5] `out_dist.txt`, `out_outliers.txt`; [study:quant_pot] §1.1, §1.6; Hosking 1990 (L-moments), Moors 1988, Hill 1975, Cont 2001 (stylised facts) and Gopikrishnan et al. 1999 (cubic law) are all unverified.

### 3.6 Volatility normalisation (ATR units, ticks, blended unit, volatility clock)
- **Classification:** A; strong.
- **Definition:** Express every distance and move in units of expected movement: d_ATR = d/ATR14, d_tick = d/τ, d_u = d/u. The blended unit is **u = ATR14^a·ATR100^{1−a}** (a = 0.5). The forward-variance unit is σ_eff = √(V_H/H), where V_H is the forecast integrated variance of the next H bars.
- **Market mechanism:**
  - Volatility clusters and mean-reverts (HAR logic). So ATR14 over-forecasts the next H bars' movement after an expansion and under-forecasts it after a compression.
  - Intraday seasonality is large: ES 5-min variance at 09:30 ET is 4.67× the day mean, and 0.20× at 23:30 ET [study:quant_pot, CME Jan-Apr 2026].
- **Mathematical implementation:**
  - Tick units: for execution maths (costs, stop distances), d_tick = round(d/τ).
  - ATR units: for user-facing distance semantics. κ = ATR14/σ_bar ≈ √(8/π) = 1.60 for Brownian motion; measured 1.39-1.54 on clean CME data; GC 1-hour 0.86 with roll gaps [study:skeptic].
  - Blended unit (intraday only; ATR14 on daily and above).
    - Measured OOS log-loss change of the empirical reach surface: −0.40% (5-min), −2.79% (15-min), −0.45% (1-hour), −1.21% (BTC 1-hour).
    - With NY 3-hour time-of-day rows: −3.04%, −5.82%, −0.65% and −1.23% [study:quant_regime, 2-fold time split, 81k/26k/28k/63k pool-touch events].
  - Forward variance:
    - V(j) = Σ_{i=1..j} s²(bucket(t_i))·[L_s + φ^i(L_f − L_s)], with φ = 0.5^{1/30}.
    - L_f and L_s are fast and slow EWMA levels of a deseasonalised range-based variance proxy, x = max(0, ½ln(H/L)² − (2ln2 − 1)ln(C/O)²) + ln(O/C₋₁)², winsorised at 25× the slow level.
    - s² are seasonal factors by exchange-time bucket. t_i is the i-th *future* bar's time, from `time(timeframe.period, "", bars_back = −i)` for i ≤ 500 [study:quant_pot QPOT-05; docs: reference/time.md, as cited by the study].
  - **Knowable at:** bar t close. Use `aU[H]` (the unit at a window's start) when learning the outcome of a window that started H bars ago.
- **Required data:** OHLC; the session time zone (`syminfo.timezone` or a user `tz`); future bar times.
- **Pine v6 availability:** feasible. `ta.atr`, `ta.tr`, `math.log`, `time(..., bars_back = −i)` [study:quant_pot citing docs]. The forward-variance loop is ≤ H iterations on scoring bars.
- **Proxy limitations:**
  - Holidays and early closes are unknown to the future-bar calendar, so V is overstated; label clock outputs "≈".
  - Range estimators are biased down by tick discreteness and up by bid-ask bounce [study:quant_pot].
  - Yang-Zhang vs close-to-close σ alone: +0.28% log-loss, CI −0.10 … +0.66% (not significant) [study:quant_pot].
- **Useful when:** always; every score and threshold must be instrument-agnostic (spec §2.1, §13.1).
- **Fails when:**
  - daily charts (the blend hurt there, +0.66%);
  - jump-prone series: GC 1-hour, where the vol clock lost 9.8% Brier [study:quant_pot citing ict_time];
  - corrupted data (roll gaps).
  Gate the clock per chart with a prequential scorecard (TIME-4).
- **Validation experiment:** pre-registered in quant_regime (REG-1) and quant_pot (QPOT-05).
  - Repeat on the APEX build's own ledger: H: the blended unit plus time-of-day rows lowers OOS log-loss of the touch surface vs ATR14 pooled.
  - Outcome: pool touch within H. Sample: 6 CME futures × 5-min/15-min/1-hour, plus BTC 1-hour, 2-fold time split.
  - Metric: ΔLL with a day-block bootstrap CI. Pass: CI excludes 0 on ≥ 4 of 7 sets, and no set is worse than −1%.
- **Existing evidence:**
  - [study:quant_regime] above; the volatility-tercile calibration bias of the ATR14 surface is +3.7/+1.7/−8.2 pp (15-min).
  - [study:quant_pot] vol-state split +1.79% LL (CI +1.45 … +2.13%).
  - [R5] the kurtosis decomposition (§3.5) shows that vol normalisation removes most non-jump tail mass on CME data.
  - [study:smt_inter] (read this session): short-horizon volatility matters beyond ATR14. Across about 430,000 pool-bars, pools are hit at 1.13× the distance-matched rate when the 3-bar mean true range exceeds 1.25 × ATR14 (15% of bars), and at 0.93× when it is below 0.8 (35% of bars), at H = 12. A fast-vs-slow volatility term in the unit or the clock should capture this. Test it as part of REG-1/QPOT-05; do not add it as a separate vote.
- **APEX recommendation:** INCLUDE-CORE (M1 NORM): ATR14 for display distances, ticks for costs, the blended unit for the probability surfaces, and the forward-variance clock behind a per-chart gate. Redundancy: ATR, SD, range estimators and MAD are all scale estimates. Use one per role (§4).
- **Sources:** [study:quant_regime] §1.6, §2.6; [study:quant_pot] §1.7-1.9, QPOT-05; [study:skeptic] §1.13; Andersen & Bollerslev 1997, Corsi 2009 and Engle & Sokalska 2012, all via [study:quant_pot] (verified there or marked).

### 3.7 Autocorrelation of returns and of absolute returns
- **Classification:** A; strong. Returns have ≈ 0 autocorrelation at chart horizons; |r| clusters.
- **Definition:** ρ̂_k = Σ_{t>k}(x_t − x̄)(x_{t−k} − x̄)/Σ_t(x_t − x̄)².
- **Market mechanism:**
  - Negative lag-1 autocorrelation of returns at the shortest horizons comes from bid-ask bounce and temporary price impact [study:quant_regime citing Heston, Korajczyk & Sadka 2010].
  - Positive |r| autocorrelation comes from volatility clustering: information arrival and herding (standard; Cont 2001, unverified).
- **Mathematical implementation:**
  - Heteroskedasticity-robust SE of ρ̂_k for demeaned x: SE_k = √(Σx_t²x_{t−k}²)/Σx_t². The iid SE 1/√n over-rejects under volatility clustering.
  - Online EWMA version: c_k ← c_k + α(x_t·x_{t−k} − c_k), v ← v + α(x_t² − v), ρ̂_k = c_k/v. The mean is assumed ≈ 0 for returns.
  - **Knowable at:** bar t close.
- **Required data:** close.
- **Pine v6 availability:** feasible. `ta.correlation(x, x[k], L)` gives a rolling Pearson ACF [docs]. EWMA via `var`.
- **Proxy limitations:** not a proxy; but intraday ACF mixes sessions. Compute it intra-session or on deseasonalised returns.
- **Typical values.** [R5] lag-1 ACF of returns:
  - within ±0.045 on all 24 CME series (1-60 min);
  - −0.033 (BTC 1-hour), −0.051 (BTC daily);
  - the exception is GC 1-min at −0.164. It is −0.247 in January (n = 11,479) and ≈ 0 in February-March (n ≈ 27k each). That is non-stationary or a data artefact, unexplained.

  Lag-1 ACF of |r|: 0.16-0.42 (CME) and 0.30 (BTC 1-hour). Deseasonalised log-range ACF on ES 5-min: 0.63 (lag 1), 0.49 (1 h), 0.34 (6.5 h), 0.27 (1 day) [study:quant_pot].
- **Useful when:** diagnosing data quality (a large negative ACF suggests jump-and-back prints or interleaved contracts), choosing block lengths for inference (§3.19), and justifying volatility forecasting (|r| ACF).
- **Fails when:** used as a directional signal. A whole-sample ACF can come from one sub-period, as the GC example shows.
- **Validation experiment:** M0 DATA check.
  - H: a rolling 1,000-bar lag-1 ACF below −0.15 flags data defects (interleaved months, bad prints) better than chance.
  - Outcome: defects confirmed by a jump-and-back scan. Sample: CME 1-hour (GC 1-hour has 692 jumps > 1.5%, 281 jump-and-back [study:academic_sr]).
  - Metric: precision and recall. Pass: precision ≥ 0.7.
- **Existing evidence:** [R5] `out_dist.txt`; [study:quant_regime] §1.8 (SPY daily ρ(1) = −0.081 is magnitude-driven; sign test p = 0.11; citing Portnaya 2026).
- **APEX recommendation:** RESEARCH-ONLY as a feature; INCLUDE-OPTIONAL as an M0 data-quality cue. |r| clustering is used implicitly through the volatility models (§3.6).
- **Sources:** [R5]; [study:quant_pot] §1.9; [study:quant_regime] §1.8; Cont 2001 (unverified).

### 3.8 Variance ratio (and why rolling Hurst labels are excluded)
- **Classification:** A; strong as a test. C (none) as a rolling regime classifier.
- **Definition:**
  - VR(q) = Var(q-bar return)/(q·Var(1-bar return)) ≈ 1 + 2Σ_{j=1}^{q−1}(1 − j/q)ρ_j. VR = 1 for a random walk, > 1 for momentum, < 1 for mean reversion.
  - Hurst: VR(q) ≈ q^{2H−1}.
- **Market mechanism:** Persistence or reversion of order flow. The study's evidence says it is negligible at chart horizons for index futures.
- **Mathematical implementation (Lo-MacKinlay):**
  - With demeaned r̃: σ̂₁² = Σr̃²/T. With overlapping q-sums R_q, σ̂_q² = ΣR_q²/m, where m = q(T − q + 1)(1 − q/T). Then VR = σ̂_q²/σ̂₁².
  - Heteroskedasticity-consistent statistic: z*(q) = √T·(VR − 1)/√θ̂, θ̂ = Σ_{j=1}^{q−1}[2(q − j)/q]²·δ̂_j, δ̂_j = T·Σ_t r̃_t²r̃_{t−j}²/(Σr̃_t²)².
  - The homoskedastic z over-rejects at 10-12% under GARCH [study:quant_regime citing Portnaya 2026].
  - SE of VR(4) on 96 bars ≈ 0.19 [study:quant_regime].
  - **Knowable at:** closed window.
- **Required data:** close.
- **Pine v6 availability:** feasible, O(q) per bar with rolling sums. Not recommended live.
- **Proxy limitations:** none, but the power is tiny at chart windows.
- **Typical values.** [R5], robust z* in parentheses:
  - ES/NQ/RTY/YM VR(4) and VR(12) = 0.857-1.033 at 1-60 min, every |z*| ≤ 1.43.
  - CL 1-min VR(4) 1.077 (+2.38).
  - GC 1-min 0.738 (−10.0): the January artefact of §3.7.
  - **BTC 1-hour VR(4) 0.920 (−4.09), VR(12) 0.878 (−3.38):** significant short-horizon mean reversion over 2017-2025. BTC 4-hour and daily are not significant.
  - [study:quant_pot] VR at q = 30-60: ES 0.96, NQ 1.02-1.05, CL 1.00-1.03, GC 0.84-0.87, YM 0.91-0.94. The √H scaling is acceptable.
  - Random-walk noise floor of the rolling VR-Hurst (q = 4, w = 96): mean 0.48, SD 0.069; > 0.55 on 12-16% of random-walk bars [study:quant_regime].
- **Useful when:** offline, to justify √H scaling per instrument; as a per-instrument check that the PoT surface does not need a drift or reversion term.
- **Fails when:** used as a live regime switch. The next-window correlation of rolling Hurst is ≈ 0 (−0.08 … +0.01, 23 series) [study:quant_regime].
- **Validation experiment:** MV.
  - H: per-instrument VR(H) deviates from 1 by less than the surface's calibration tolerance (±3%).
  - Metric: VR(H) with a stationary-bootstrap CI. Pass: CI within [0.9, 1.1] for index futures.
  - For BTC 1-hour, test whether a reversion-adjusted surface beats the standard one by ≥ 0.5% LL OOS. The empirical surface may already absorb it.
- **Existing evidence:** above.
- **APEX recommendation:** RESEARCH-ONLY (MV). EXCLUDE rolling Hurst, VR, ADX or CHOP thresholds as regime labels; in the display they may appear only with base-rate disclosure (REG-2 tooltips).
- **Sources:** [R5] `out_dist.txt`; [study:quant_regime] §1.4, §2.2; [study:quant_pot] §1.11; Lo & MacKinlay 1988 (via study; unverified here).

### 3.9 Correlation and its instability
- **Classification:** A; strong (method), strong (instability as a fact).
- **Definition:**
  - Pearson ρ = Cov(x, y)/(σ_xσ_y). Spearman ρ_s is Pearson on ranks.
  - Fisher transform z = atanh(ρ̂), with SE ≈ 1/√(n − 3) for iid bivariate-normal samples.
- **Market mechanism:**
  - Correlations between instruments change with the macro regime and with risk-on/risk-off episodes. Equity-index futures share a common factor.
  - [study:smt_inter] (executive summary read this session): SMT divergence is not a reversal signal (50.5% vs 50.8% race reversal, n = 16,258 / 16,187). A small, persistent cross-asset effect remains on pool hits (lift 1.035-1.042, about +1.5 to +1.9 pp, placebo 1.006). That is a modest PoT modifier, not a directional vote.
  - Correlation is not causation (spec §12).
- **Mathematical implementation:**
  - Rolling: `ta.correlation(x, y, L)` (`na` values ignored [docs]).
  - EWMA:
    - c_xy ← c_xy + α(x̃ỹ − c_xy) with x̃ = x − m_x, and the same for the variances;
    - ρ_t = c_xy/√(c_xx·c_yy).
  - **Stability statistic:**
    - over K non-overlapping windows of length w, z̄ = mean(atanh ρ̂_k) and s_z = sd(atanh ρ̂_k);
    - the instability ratio IR = s_z·√(w − 3), which is 1 for a stable correlation;
    - and the sign-flip share.
  - **Gate for use:**
    - |tanh(z̄)| ≥ 0.3;
    - |z̄|/s_z ≥ 2;
    - a sign-flip share ≤ 10%;
    - otherwise the intermarket term contributes 0 and its data-quality weight is 0.
  - Defaults: w = 100 bars of the chart TF; K = 10.
  - Use returns, never price levels: levels of trending series show spurious correlation.
  - **Knowable at:** bar t close. With `request.security`, use the [1]-offset pattern.
- **Required data:** synchronised returns of two symbols (`request.security`). Timestamps must align, including session differences.
- **Pine v6 availability:** feasible. `ta.correlation`, `request.security` (≤ 40 unique requests; pine_eng), EWMA via `var`.
- **Proxy limitations:**
  - Asynchronous trading (CL settles differently; crypto trades 24/7 while futures halt) biases correlation toward 0 (the Epps effect; unverified).
  - Different holiday calendars insert stale prices.
- **Typical values.** [R5], CME common timestamps, Jan-Apr 2026, 15-min (n = 4,762) and 60-min (n = 1,261).

| Pair | Full-sample ρ (15-min) | Range of 100-bar ρ̂ (15-min) | IR (100 bars) | Sign-flip share |
|---|---|---|---|---|
| ES-NQ | +0.96 | +0.89 … +0.99 | 2.8 | 0 |
| ES-RTY | +0.90 | +0.21 … +0.99 | 4.1 | 0 |
| ES-YM | +0.91 | +0.40 … +1.00 | 5.3 | 0 |
| ES-GC | +0.36 | −0.33 … +0.83 | 2.9 | 0.13 |
| ES-CL | −0.49 (Spearman −0.24) | −0.90 … +0.41 | 4.6 | 0.40 |
| CL-GC | −0.12 | −0.76 … +0.68 | 3.4 | 0.49 |

  The rolling correlation varies 2-8.5× more than iid sampling noise on every pair and every window (50, 100, 250). Even the tightest pair (ES-NQ) is not stable in the Fisher scale.
  - Pearson and Spearman disagree strongly on ES-CL (−0.49 vs −0.24). A few joint jump bars (2026-03-23) drive the Pearson value.
  - [x1_tv_validation tool outputs, report in progress; I read `x1_tvv_tools/out_pooling.txt` directly]: the paired DOL-vs-mirror residual of a trend picker on CME 1-hour has a mean off-diagonal cross-symbol correlation of 0.18. The 6 symbols are worth **3.13 effective symbols**; the equity-index block is worth 1.91 of 4. Pooling evidence across correlated symbols must use n_eff = k/(1 + (k − 1)ρ̄).
- **Useful when:** you are configuring intermarket context with an explicit stability gate; or computing effective sample sizes when pooling symbols.
- **Fails when:**
  - a single full-sample ρ is treated as structural;
  - Pearson is used under joint jumps (prefer Spearman or a winsorised Pearson);
  - the windows are short (n < 50).
- **Validation experiment:** pre-registered.
  - H: an intermarket feature that passes the stability gate improves OOS log-loss of the direction-at-H model over geometry by ≥ 0.25%.
  - Sample: ES/NQ/RTY/YM/CL/GC plus DXY and yields where available; walk-forward by month.
  - Metric: ΔLL with a block bootstrap. Pass: CI excludes 0 and the sign is stable across halves.
  - Expected result given the study: fail. The feature then stays display-only.
- **Existing evidence:** [R5] above; [study:quant_regime] direction ≈ random walk; [study:smt_inter] SMT not a reversal signal, small persistent pool-hit lift 1.035-1.042.
- **APEX recommendation:** INCLUDE-OPTIONAL (M10 INTER, off by default), as context with the stability gate and Spearman as the default estimator. EXCLUDE as a scoring vote unless the experiment passes. The cross-symbol effective n is INCLUDE-CORE in MV for pooled statistics.
- **Sources:** [docs] ta.md (`ta.correlation`); [R5] `out_dep.txt` D; x1_tvv_tools/out_pooling.txt; Fisher 1921 and Epps 1979 (unverified).

### 3.10 Linear and rolling regression (OLS)
- **Classification:** A; strong (method). Weak as a directional signal. C for "regression significance" read off price-on-time fits.
- **Definition:** Fit y_t = a + b·t + e_t over the last n bars, with t = 0..n−1.
  - b = [nΣty − ΣtΣy]/[nΣt² − (Σt)²], with Σt = n(n−1)/2 and Σt² = (n−1)n(2n−1)/6. Intercept a = ȳ − b·t̄.
  - Pine `ta.linreg(src, n, offset)` returns a + b·(n − 1 − offset) [docs], so b = `ta.linreg(src, n, 0) − ta.linreg(src, n, 1)`.
- **Market mechanism:** None beyond describing recent drift. Intraday predictability is small: R² is 1.6% in sample and 1.2% out of sample for SPY's first half-hour predicting the last [study:quant_pot, quant_regime, citing Gao, Han, Li & Zhou 2018, verified by study].
- **Mathematical implementation:**
  - **Exact identity [R5, derived and checked by Monte Carlo].** With returns Δy_j = y_j − y_{j−1}:
    - b = Σ_{j=1}^{n−1} w_j·Δy_j, where w_j = 6j(n − j)/(n(n² − 1)) and Σw_j = 1.
    - So the OLS slope is a **parabolic-weighted mean return**, peaking mid-window.
    - Under iid returns, corr(b, ROC_n) = √(5n(n + 1)/(6(n² + 1))): 0.953 (n = 10), 0.934 (20), 0.922 (50), → 0.913 as n grows. Monte Carlo (20,000 windows) gives 0.952 / 0.936 / 0.922 / 0.917 at n = 10 / 20 / 50 / 100 (`regr_check.py` → `out_regr.txt`).
    - Regression slope, ROC and EMA slope are therefore one measurement, not three confirmations (spec §8).
  - O(1) rolling update when the window slides by one bar, where y_old is the dropped value (index 0) and y_new enters at index n − 1:
    - S_y' = S_y − y_old + y_new;
    - S_ty' = S_ty − (S_y − y_old) + (n − 1)·y_new.
    - Recompute exactly every n bars to stop rounding drift.
  - Normalise: slope per bar in ATR, b_ATR = b/ATR14; or over the horizon, b·H/(ATR·√H).
  - **Drift use (M7 forecast):** never use b as a forecast drift unshrunk.
    - Positive-part James-Stein shrinkage: μ_eff = μ̂·max(0, 1 − (σ²/n)/μ̂²). This is zero unless |t| > 1 [study:quant_pot §1.10].
    - With weight w and n = 50, the standardised barrier noise is 0.39·Z at H = 30 [study:quant_pot].
  - **Prediction intervals:** the textbook OLS interval ŷ ± t·s·√(1 + 1/n + (x₀ − x̄)²/S_xx) assumes iid residuals around a true line. Price is closer to a random walk, so its residuals are strongly autocorrelated and the interval is far too narrow beyond the window. Use horizon-specific empirical error quantiles instead (M7, §3.17).
  - **Knowable at:** bar t close.
- **Required data:** close (or hlc3).
- **Pine v6 availability:** feasible. `ta.linreg` (na inside the window → na [docs]), `math.sum`, `var` state. `matrix.inv`/`matrix.pinv` give multivariate OLS on small designs [docs]; use them only on `barstate.islast` or confirmed bars because of the cost.
- **Proxy limitations / pitfalls:**
  - **Spurious significance.** On a driftless Gaussian random walk, the iid-SE t-statistic of the price-on-time slope exceeds 2 in absolute value in 71.7% (n = 20), 82.8% (n = 50), 87.4% (n = 100) and 91.5% (n = 200) of windows. The median trend R² is 0.43-0.45 [R5, synthetic, 20,000 windows each].
  - Regression channels, "trend R²" and t-stat filters are therefore noise detectors.
  - The correct test of drift is the t-statistic of the mean *return* with a HAC SE.
- **Useful when:** describing the local direction for the forecast path's shape (after shrinkage) and for the trend descriptor of the Bias module. Use one slope family, not three.
- **Fails when:** treated as significance, extrapolated as a drift, or combined with ROC/EMA-slope as independent votes.
- **Validation experiment:** pre-registered.
  - H: adding shrunk regression drift μ_eff to the forecast path does not improve the H-bar directional log-loss over zero drift.
  - Sample: 6 CME futures × 5-min/1-hour, plus BTC 1-hour; walk-forward by month.
  - Metric: ΔLL of P(r_H > 0) with a block bootstrap. Pass criterion for INCLUDING drift: CI > 0 on ≥ 5 of 7 sets.
  - Expected result: fail, per QPOT-01 and quant_regime §2.5 (drift worsens LL in every regime).
- **Existing evidence:** [R5] identity and spurious-t results; [study:quant_pot] drift removal +3.66% LL; [study:quant_regime] §2.5 drift hurts in ER ≥ 0.4 trends too (e.g. 1-hour 0.6136 with drift vs 0.5902 without).
- **APEX recommendation:** INCLUDE-CORE as a *descriptor* (M3 BIAS trend family, M7 FCST shape), in ATR units, with drift shrunk to 0 by default. EXCLUDE the t-stat or R² display. Consolidate with ROC and EMA slope into one "trend" factor (§4).
- **Sources:** [docs] ta.md (`ta.linreg`), matrix.md; [R5] `out_regr.txt`, identity check; [study:quant_pot] §1.10; Granger & Newbold 1974 and Phillips 1986 (spurious regression; unverified).

### 3.11 Robust regression: Huber IRLS, Theil-Sen, repeated median
- **Classification:** A; moderate. They are robust to bad prints and spikes, and add little on clean futures data.
- **Definition:**
  - Huber M-estimation minimises Σρ_c(e_i/s), with ρ_c(u) = u²/2 for |u| ≤ c and c|u| − c²/2 otherwise.
  - Theil-Sen: b = median_{i<j} (y_j − y_i)/(j − i); breakdown 29.3%.
  - Siegel's repeated median: b = med_i med_{j≠i} slopes; breakdown 50%.
- **Market mechanism:** Same as §3.10. Robustness matters when single prints are unreliable: thin sessions, YM ±66 bp jump-and-back on 2-29 contracts [R5], roll gaps.
- **Mathematical implementation:**
  - **Huber IRLS** (c = 1.345, about 95% Gaussian efficiency; unverified figure):
    - start from OLS;
    - repeat 3-5 times: e = y − Xb; s = 1.4826·MAD(e); w_i = min(1, c·s/|e_i|); solve the 2×2 weighted normal equations in closed form.
    - The closed form is b = (S_w·S_wty − S_wt·S_wy)/(S_w·S_wtt − S_wt²), with S_w = Σw, S_wt = Σwt, etc.
    - Cost O(k·n).
  - **Theil-Sen in Pine:** fill an array with n(n−1)/2 pairwise slopes and take `array.median`. n = 20 gives 190 values, n = 50 gives 1,225 per confirmed bar.
  - **Knowable at:** bar t close.
- **Required data:** close.
- **Pine v6 availability:** Huber feasible (loops, ≤ 250 ops for n = 50, k = 5). Theil-Sen partial: O(n²) memory and time per bar, and the cost is unmeasured (500 ms per-loop limit and total-time limit [docs: limitations.md]).
- **Proxy limitations:** none specific.
- **Evidence.** [R5] ES 5-min, 50-bar windows:
  - Huber vs OLS slope: same sign in 98.2% of 3,348 windows, median relative difference 3%.
  - Theil-Sen vs OLS: same sign in 95.1-95.6% (ES and CL, n = 20 and 50, about 5,500 windows each), median relative difference 8%.
- **Useful when:** the data contain spikes: crypto alt-coins, thin sessions, illiquid equities.
- **Fails when:** the cost is unjustified on clean, liquid futures. Theil-Sen also has lower efficiency on clean Gaussian data.
- **Validation experiment:**
  - H: on thin-session and illiquid series, Huber slopes produce fewer forecast-direction flips per 100 bars than OLS at equal OOS directional log-loss.
  - Metric: flips per 100 bars, and ΔLL. Pass: ≥ 20% fewer flips and |ΔLL| < 0.1%.
- **Existing evidence:** [R5] above.
- **APEX recommendation:** Huber INCLUDE-OPTIONAL (M7 FCST "robust slope" toggle, off). Theil-Sen and repeated median RESEARCH-ONLY. Redundant with OLS (§3.10).
- **Sources:** [R5] `out_dep.txt` H, `out_regr.txt`; Huber 1964, Theil 1950, Sen 1968 and Siegel 1982 (unverified).

### 3.12 Conditional probability and base rates
- **Classification:** A; strong.
- **Definition:**
  - P(Y | X) = P(X | Y)P(Y)/P(X).
  - Lift L = P(Y | X, d)/p₀(d), where p₀(d) is the distance-matched base rate: the probability that a random level at the same distance, side, horizon and volatility state is reached.
  - Excess = P(Y | X, d) − p₀(d).
- **Market mechanism:** Most DOL claims reduce to geometry.
  - FVGs are reached 73.0% vs 72.9% for random levels (38,114 FVG returns vs 380,599 random).
  - Order blocks 73.7% vs 73.7% [study:skeptic, citing Nordman and Trader Markus, re-fetched by study B].
  - Equal highs/lows are the only pool feature surviving Holm: +0.29 logit on 1-hour, Holm p = 0.007 [study:calib_ml].
  - A conditional rate without its base rate is meaningless.
- **Mathematical implementation:**
  - p₀(d, side, state) comes from the empirical excursion surface, blended with the driftless analytic prior 2Φ(−d/(σ√H)) (or vol-time √V_H), weight m = 30 effective windows. n_eff = n/(0.6H) handles window overlap [study:quant_pot §1.12-1.14].
  - Cell estimate with shrinkage to the base rate: P̂(Y | X) = (k + m·p₀)/(n + m) (§3.13).
  - **Traps to avoid** [study:skeptic]:
    - conditioning on hits only (ETA|hit shows 9 bars where the true median time is 19-25 bars at 2 ATR);
    - conditioning on decided races (the "EV" readout shows −0.62R where the true expectancy is 0);
    - conditioning on eventual outcome ("eventually swept": random levels at 2 ATR are touched within 300 bars 87% of the time).
  - **Knowable at:** the prediction at bar t close; the outcome at the resolution bar.
- **Required data:** OHLC; the engine's level set; the ledger.
- **Pine v6 availability:** feasible. The surfaces live in `var array<int>` (the engine already has them).
- **Proxy limitations:** the baseline is itself a model. Its miscalibration of ±2-3 pp by clock window, +3 to −8 pp by volatility state, and −4 pp with roll gaps shifts every excess [study:skeptic]. The mirror control removes the direction-free part (§3.27).
- **Useful when:** grading any target, setup or forecast, and labelling any rate on screen ("hit 56% / exp 51%").
- **Fails when:** the baseline is broken (roll gaps) or the state key is wrong (a trend key carries no information [study:quant_regime M12]).
- **Validation experiment:** the shadow-ledger test (CAL-3).
  - H: the selected DOL's touch rate within H exceeds p₀ by more than δ = 2 pp.
  - Outcome: strict trade-through within H. Sample: all candidate probes, 6 CME futures + EURUSD + BTC, 5-min and 1-hour.
  - Metric: excess with a centred, open-keyed block variance. Test: mirror-paired confidence sequence at α = 0.025.
  - Pass: lower bound > 0 ("beats baseline"). Materiality: report REFUTED if upper bound < δ.
- **Existing evidence:** [study:skeptic] claims ledger C1-C25; [study:calib_ml] §2.2.
- **APEX recommendation:** INCLUDE-CORE (M4 DOL, M8 CAL, every readout). Every probability or rate is displayed with its base rate.
- **Sources:** [study:skeptic] §1.13-1.19, §2.1; [study:calib_ml] §1.1-1.4; [study:quant_pot] §1.12-1.14.

### 3.13 Bayesian updating: Beta-Binomial hit rates with shrinkage, Poisson-Gamma lifts, partial pooling
- **Classification:** A; strong.
- **Definition:**
  - **Beta-Binomial.** Prior θ ~ Beta(m·p₀, m·(1 − p₀)). With k successes in n trials the posterior is Beta(k + m·p₀, n − k + m(1 − p₀)), with mean (k + m·p₀)/(n + m) and variance θ̄(1 − θ̄)/(n + m + 1).
  - **Poisson-Gamma** (hits vs expected hits). k ~ Poisson(λ·e) with e = Σp₀ and prior λ ~ Gamma(α, α/λ₀); posterior mean λ̂ = (k + αλ₀)/(e + α). The prior SD of λ is λ₀/√α.
  - **Partial pooling** of a cell toward its parent: p_cell = (n_E·p̂_c + m·p_parent)/(n_E + m), applied level by level (global → regime → cell).
- **Market mechanism:** Small samples per cell (per family, per regime, per hour) are noisy. Shrinkage trades a little bias for a large cut in variance; it is the empirical-Bayes cure for the winner's curse.
- **Mathematical implementation:**
  - **Overlap:** use k_eff = k/deff and n_eff = n/deff before updating (Kish). deff comes from block variance (§3.18).
  - **Prior strength m:**
    - Fixed: m = 30 effective windows for surfaces [study:quant_pot]; α = 60 expected hits (prior SD ≈ 13%) for family lifts [study:calib_ml].
    - Or empirical Bayes: τ² = max(0, Var_between − mean s²_within) and m = p̄(1 − p̄)/τ² − 1. Unstable with fewer than about 8 groups, so prefer a fixed m.
  - **Posterior tail without an incomplete beta function:** P(θ > p₀ | data) ≈ Φ((logit θ̄ − logit p₀)/s), with s² ≈ 1/(θ̄(1 − θ̄)(n_eff + m)).
  - **Gate:** apply a learned multiplier only when its residual passes the confidence-sequence boundary (§3.18). Clamp it to [0.85, 1.15].
  - **Knowable at:** posteriors update at resolution bars; readers use the last confirmed state.
- **Required data:** the ledger.
- **Pine v6 availability:** feasible, O(1) per booking (`var array<float>` accumulators).
- **Proxy limitations:** shrinkage toward a miscalibrated parent inherits its bias.
- **Useful when:** any rate is displayed or used with n < a few hundred: per family, per regime cell, per hour.
- **Fails when:** the prior is too weak. The engine's `f_calMult` uses α = 2 with a hard n ≥ 10 cliff. Under the null it sits ≥ 10% off 1 in 66% / 47% / 33% of families at n = 10 / 40 / 80. An EB version with α = 60 and deff has a lower RMSE everywhere [study:calib_ml, simulation].
- **Validation experiment:** prequential.
  - H: pooled cell estimates (m = 30) beat raw cell rates in log-loss.
  - Sample: candidate probes split by NY 3-hour block × volatility tercile.
  - Metric: ΔLL with a day-block bootstrap. Pass: CI > 0 on ≥ 5 of 6 symbols.
  - Already supported in a sibling design: vol-state split +1.79% LL, CI +1.45 … +2.13% [study:quant_pot].
- **Existing evidence:**
  - [study:quant_pot] §1.13-1.14, §2.2.
  - [study:calib_ml] §1.11-1.14, §2.2(d).
  - Efron-Morris shrinkage cut total squared error about 3.5-fold in the baseball example (figures not re-verified by calib_ml B; ratio consistent).
- **APEX recommendation:** INCLUDE-CORE (M4 DOL surfaces, M8 CAL family and regime readouts, M2 REGIME conditioned rates). Replace any cliff-gated multiplier with continuous weights n_eff/(n_eff + m).
- **Sources:** [study:quant_pot] QPOT-03; [study:calib_ml] CAL-1; Efron & Morris 1975 (via study; figures unverified).

### 3.14 Logistic models: offset logistic, online SGD, online Platt scaling, Bayesian probit
- **Classification:**
  - A; strong (method), moderate (benefit, gated only).
  - C for unregularised online SGD (measured harmful).
- **Definition:**
  - **Offset logistic:** logit P(y = 1 | x) = logit(p₀) + βᵀx. β = 0 reproduces the baseline, so every coefficient is a lift beyond distance.
  - **Platt-on-logit:** p' = σ(a + b·logit p). It contains the identity map (a = 0, b = 1) [study:calib_ml B-fix].
  - **Bayesian online probit (adPredictor):** P = Φ((o + μᵀx)/Σ), with Σ² = 1 + Σx_j²v_j and o = Φ⁻¹(p₀) [study:calib_ml §1.17].
- **Market mechanism:** Combines evidence additively on the log-odds scale, the natural scale for "evidence weighting" (spec §13.2). It double-counts correlated features less than naive-Bayes multiplication.
- **Mathematical implementation:**
  - **Online SGD with L2 toward a prior:** β ← β + η_t[(y − p)x − λ(β − β₀)].
    - AdaGrad step: η_{t,j} = η₀/√(ε + Σg_j²).
    - Temper updates with ω = 1/deff for overlapping samples.
    - Clamp p to [0.005, 0.995] before the log-loss (as `f_logit`, lines 484-486, does).
    - Standardise features (M1).
  - **Online Platt by Online Newton Step** (Gupta & Ramdas 2023, verified by study):
    - z = logit p; r = σ(a + bz) − y; g = r·(1, z);
    - A ← A + ggᵀ, with A₀ = 100·I;
    - θ ← θ − (1/γ)A⁻¹g, with γ = 0.1;
    - start (a, b) = (0, 1); box a ∈ [−1, 1], b ∈ [0.5, 1.5].
    - It needs a 2×2 inverse in closed form: det = a₁₁a₂₂ − a₁₂².
  - **Gate:**
    - use the calibrated value only after 200 probes, and only while its prequential cumulative log-loss is lower than the raw one by a margin (1 nat);
    - or mix with exponential weights (η = 0.25, fixed share 0.005).
  - **Knowable at:** predictions frozen at the open bar; updates at the resolution bar inside `barstate.isconfirmed`; realtime ticks read the parameters only.
- **Required data:** the shadow ledger (≈ 2,500-3,500 probes per 5,000 bars) [study:calib_ml].
- **Pine v6 availability:** feasible. `var array<float>` parameters; a closed-form 2×2 solve; `matrix.*` for larger probit vectors. adPredictor needs Φ⁻¹: the Acklam rational approximation in the A report, |rel err| < 1.2e-9 [study:calib_ml].
- **Proxy limitations:** features are proxies of the ICT concepts. Lifts are mostly null after multiplicity: only EQ survives Holm [study:calib_ml].
- **Evidence:** prequential ΔLL vs the distance-matched baseline [study:calib_ml, 13 clean sets + GC 1-hour broken base, 76,181 probes].

| Learner | 13 clean sets | GC 1-hour (broken base) |
|---|---|---|
| Unregularised online SGD (η = 0.05) | −3.6 … −5.5% | +9.1% |
| Naive-Bayes lifts | −0.6 … −2.1% | +2.2% |
| Online Platt, default step | −0.6 … −1.8% | +5.6% |
| Gated online Platt | 0.00 … −0.23% (mean −0.02%) | +5.6% |
| Gated probit (12 features) | 0.00 … −0.26% | +8.8% |
| Mixture base + probit | −0.32 … +0.01% | +10.5% |

  The cross-market prior fitted leave-one-dataset-out *hurt* held-out log-loss by −1.17% (12 of 13 worse) [study:calib_ml].
- **Useful when:** protecting against a broken baseline, and measuring per-chart feature lifts.
- **Fails when:**
  - ungated, unregularised or not prequential;
  - learning from selected targets only (bandit feedback; it learns only about what it already prefers);
  - popular Pine "ML" scripts: the inspected "logistic regression" never feeds the gradient back, and the Lorentzian kNN labels the *past* 4-bar move [study:calib_ml, code read by study B].
- **Validation experiment:** prequential ledger test (CAL-4).
  - H: gated OPS costs ≤ 0.3% LL on clean charts and gains ≥ 2% on charts with roll gaps.
  - Sample: TradingView continuous futures with back-adjustment off and on. Metric: ΔLL. Pass: both conditions hold.
- **Existing evidence:** above.
- **APEX recommendation:**
  - Gated online Platt: INCLUDE-CORE (M8 CAL; applies to any displayed probability).
  - Offset probit lifts: RESEARCH-ONLY (measure-only readout; optional "apply to PoT when proven").
  - Unregularised SGD and naive-Bayes multipliers: EXCLUDE.
- **Sources:** [study:calib_ml] §1.7-1.23, §2.2-2.3, CAL-4, CAL-9; Gupta & Ramdas 2023 (verified by study); Graepel et al. 2010 (method verified by study, figures not); Duchi et al. 2011 (unverified).

### 3.15 Feature interactions
- **Classification:** A (method); weak (evidence of useful interactions in this domain).
- **Definition:** An effect of x₁ that depends on x₂: logit P = logit p₀ + β₁x₁ + β₂x₂ + β₁₂x₁x₂. Equivalently, stratified lifts that differ across cells.
- **Market mechanism:** Practitioners claim conditional effects ("a sweep matters only in the killzone", "proximity plus HTF alignment"). Spec §20 lists "target proximity combined with HTF alignment" as a hypothesis.
- **Mathematical implementation:**
  - Pre-register each interaction.
  - Estimate it as a difference of shrunk cell excesses: Δ = (e₁₁ − e₁₀) − (e₀₁ − e₀₀), with each e = cell excess over p₀.
  - Var(Δ) = Σ Var(e_cell), using block variance. Shrink Δ toward 0 with a prior SD of half the main-effect prior.
  - **Sample size:** to detect a cell excess Δ vs a known baseline at p ≈ 0.5 with α = 0.05 (two-sided) and 80% power, n ≈ (1.96 + 0.84)²·p(1 − p)/Δ² × deff.
    - Δ = 5 pp, deff = 2: n ≈ 1,568 per cell.
    - An interaction (a difference of differences) needs about 4× the per-cell n of a main effect.
  - **Knowable at:** features at open; outcome at resolution.
- **Required data:** the shadow ledger, with feature bits frozen at open.
- **Pine v6 availability:** feasible as stratified accumulators (CAL-7 style tertile readouts).
- **Proxy limitations:** the many possible pairs create a multiple-testing explosion (§3.20).
- **Useful when:** testing 1-3 pre-registered hypotheses.
- **Fails when:** data-mining all pairs. Forking paths: each extra degree of freedom widens the range of t-statistics by at least 30% [study:skeptic, citing Coqueret 2023, abstract re-read by study B].
- **Validation experiment:** spec §20 "proximity × HTF alignment".
  - H: among candidate pools at 0.5-3 ATR, the touch excess of HTF-aligned pools exceeds that of non-aligned pools by ≥ 3 pp, beyond distance.
  - Sample: shadow ledger, 6 CME futures + BTC, 5-min and 1-hour.
  - Test: block-variance z with Holm across the pre-registered set. Pass: Holm p < 0.05 and the same sign in both halves.
  - Prior expectation: fail. The HTF-trend key has no side skill [study:bias_dol REG-1, quant_regime M12].
- **Existing evidence:** none positive in the study. [study:quant_regime] trend-state × surface interactions: −0.02 … +0.41% LL (none help).
- **APEX recommendation:** RESEARCH-ONLY (MV and the CAL-7 measure-only readout). No interaction terms enter any score by default.
- **Sources:** [study:skeptic] §1.25; [study:quant_regime] §2.6.

### 3.16 Regime-conditioned statistics (stratification, partial pooling, hysteresis)
- **Classification:** A; moderate.
- **Definition:** Estimate a statistic separately per regime cell s ∈ S, with partial pooling toward the parent, and assign the regime by a rule with hysteresis.
- **Market mechanism:**
  - Volatility states persist (corr 0.49-0.80); trend labels do not (≈ 0) [study:quant_regime].
  - The time of day carries strong variance structure.
  - So condition on the volatility state and the clock, not on trend labels.
- **Mathematical implementation:**
  - **State variable:** v_t = ln(ATR5/ATR100). z_v = (v − μ_v)/σ_v, with EWMA α = 2/2001.
  - **Hysteresis:** enter "compressed" at z ≤ −0.43 and leave at z > −0.30; enter "expanded" at z ≥ +0.43 and leave at z < +0.30 (REG-2). The values ±0.43 are normal terciles.
  - **Clock key:** the NY 3-hour block, `hour(time, tz)/3` (QPOT-03, TIME-2).
  - **Pooling:** use the three-level formula of §3.13 with m = 30. Cells are read only after count ≥ max(150, 20H).
  - **Ledger split:** report hit/expected per cell, with Wilson intervals and n ≥ 20 (REG-2).
  - Disclose base rates: ER ≥ 0.40 on 15.7% and ADX ≥ 25 on 38% of random-walk bars [study:quant_regime].
  - **Knowable at:** bar t close. Learning uses the state at the window's start (`state[H]`).
- **Required data:** OHLC; the session time zone.
- **Pine v6 availability:** feasible (`var` arrays; the engine already has a regime-keyed surface).
- **Proxy limitations:** DST shifts London-session cells for about 4 weeks a year; 3-hour blocks absorb most of it [study:quant_pot].
- **Useful when:** calibrating PoT and forecast bands, and reporting accuracy by regime.
- **Fails when:**
  - the key carries no information: the `htfBias` key, M12 trend rows −0.02 … +0.41% [study:quant_regime];
  - cells are too thin;
  - volatility rows are stacked on time-of-day rows: that **hurts** (15-min −2.38% vs −4.06%) by diluting samples [study:quant_regime].
- **Validation experiment:** as QPOT-03/REG-1 (§3.6), plus a regime-split accuracy audit.
  - H: the PoT calibration gap in the expanded tercile is within ±2 pp after the unit fix.
  - Metric: CITL per tercile with a block CI. Pass: all three CIs include 0.
- **Existing evidence:** [study:quant_regime] §2.6 table (M8 best); [study:quant_pot] §2.2.
- **APEX recommendation:** INCLUDE-CORE (M2 REGIME state with hysteresis, for display and stratification only; M4 surfaces keyed by time of day plus the blended unit). EXCLUDE trend-state keys for probability surfaces.
- **Sources:** [study:quant_regime] REG-1, REG-2; [study:quant_pot] QPOT-03.

### 3.17 Proper scoring rules, calibration curves and the calibration hierarchy
- **Classification:** A; strong.
- **Definition:**
  - Brier B = mean(p − y)². Log-loss LL = −mean[y ln p + (1 − y) ln(1 − p)]. Both are strictly proper.
  - Brier skill vs a reference: BSS = 1 − B/B_ref, with the reference = distance-matched p₀ (climatology is too easy).
  - Murphy decomposition: B = REL − RES + UNC.
  - Calibration slope and intercept: logistic regression of y on logit p (slope < 1 = over-confident).
  - CITL = mean(y) − mean(p).
  - Spiegelhalter z = Σ(y − p)(1 − 2p)/√Σ(1 − 2p)²p(1 − p).
  - ECE = Σ_b (n_b/n)|ȳ_b − p̄_b|.
  - For continuous forecasts: pinball loss for quantiles, ρ_τ(u) = u(τ − 1{u < 0}); CRPS for distributions. The CRPS of the survival ladder is the sum of Brier scores over thresholds [study:calib_ml].
- **Market mechanism:** none. This is the measurement standard that spec §15 requires before any "probability" label.
- **Mathematical implementation (online):**
  - Accumulate [n, Σ(p − y)², Σ(p₀ − y)², ΣLL, Σp, Σy] in `var` arrays.
  - Reliability: 10 equal-width or (better) equal-mass bins of [n_b, Σp_b, Σy_b]. Show a bin only with n_eff ≥ 30.
  - Calibration slope: 3 Newton steps on the binned sufficient statistics, or read b from online Platt.
  - **Calibration hierarchy** (Van Calster et al. 2016, verified by study):
    - *mean* (CITL);
    - *weak* (intercept 0, slope 1);
    - *moderate* (the reliability curve);
    - *strong* ("unrealistic").
    - Show only the level the sample supports.
  - **Sample-size rule:** ≥ 100 events and ≥ 100 non-events (ideally 200), divided by deff, before showing a slope (Collins et al. 2016, verified by study).
  - Grade the **uncapped** forecast. A 95% display cap makes the score improper near d = 0 [study:calib_ml].
  - **Knowable at:** at resolution; the display reads the last confirmed state.
- **Required data:** a forecast frozen at open plus the outcome.
- **Pine v6 availability:** feasible, O(1) per booking.
- **Proxy limitations:** the plug-in ECE is biased upward at small n (Roelofs 2020, Kumar 2019, verified by study). Spiegelhalter z is weak against an intercept shift: GC 1-hour CITL −4.25 pp gives z only 2.45, and about 0.9 after deff 7.7 [study:calib_ml].
- **Useful when:** grading PoT, the race, forecast direction, forecast bands and signal states (spec §15 list). Also for the Forecast Quality Score (M6), which should be built from these scores, not from feature agreement.
- **Fails when:** computed on selected targets only (bandit feedback), on capped values, or without the design effect.
- **Validation experiment:**
  - H: the engine's displayed PoT has calibration slope in [0.9, 1.1] and |CITL| ≤ 2 pp on clean charts.
  - Sample: shadow ledger, 6 CME futures + EURUSD + BTC. Metric: slope and CITL with block CIs. Pass: as stated.
  - Already met by the default surface in a replica: slope 0.99, ECE 0.004 on 1.2 M rows [study:quant_pot]. Not met by the drift analytic: slope 0.66.
- **Existing evidence:** [study:quant_pot] §2.2; [study:calib_ml] §1.5-1.10, §2.3 B2.
- **APEX recommendation:** INCLUDE-CORE (M8 CAL; M6 FQ derives from it). Labels follow the hierarchy: "score" → "relative rank" → "calibrated frequency (n, horizon)".
- **Sources:** [study:calib_ml] CAL-6; [study:quant_pot] QPOT-04; Gneiting & Raftery 2007 and Murphy 1973 (unverified here; cited by study).

### 3.18 Confidence intervals: Wilson, design effect, and anytime-valid confidence sequences
- **Classification:** A; strong.
- **Definition:**
  - **Wilson score interval:** center c = (p̂ + z²/(2n))/(1 + z²/n), half-width h = z·√(p̂(1 − p̂)/n + z²/(4n²))/(1 + z²/n). The engine's `f_wilson` (baseline lines 492-503) implements exactly this, with z = 1.96.
  - **Design effect:** deff = V_cluster/V_independent, where V_independent = Σp(1 − p).
  - **Normal-mixture confidence sequence** (two-sided): P(∀t: |S_t| < u(V_t)) ≥ 1 − α, with u(v) = √((v + ρ)·ln((v + ρ)/(ρα²))) (Howard et al. 2021 eq. 14, verified by study).
- **Market mechanism:** none. Overlapping H-bar outcomes share one price path, so naive SEs are far too small. Re-checking a fixed-α test after every booking inflates false positives (peeking).
- **Mathematical implementation:**
  - **Block variance:**
    - blocks keyed by the record's *open* bar;
    - width W = max(2H, min(max(4H, bars per day), calcBars/25));
    - centred: V = G/(G − 1)·Σ_g(E_g − N_g·ē)², where E_g is a block's residual sum;
    - require G ≥ 20 blocks before any verdict [study:skeptic SKEP-3; calib_ml CAL-2].
  - Wilson with deff: apply it to (k/deff, n/deff).
  - **Confidence sequence:**
    - S = Σ(y − p₀), V = cG·vBlock, ρ = 10 (tightest near V ≈ 82; boundary z ≈ 3.0-3.7 for V = 10-250);
    - verdict three-way with materiality δ: BEATS if S > u, NO MATERIAL EDGE if the upper bound < δ·n, INCONCLUSIVE otherwise [study:skeptic, Darmanin 2026 verified by study].
  - **Knowable at:** after each closed block.
- **Required data:** the ledger.
- **Pine v6 availability:** feasible (`f_wilson` exists; `f_csBound` is a one-liner [study:calib_ml CAL-1 sketch]).
- **Proxy limitations:** with an estimated variance the confidence sequence is asymptotic. For mirror-paired residuals (conditionally symmetric) the self-normalised version is non-asymptotic [study:skeptic §1.30].
- **Evidence:**
  - **Wilson vs Wald, exact coverage** of nominal 95% intervals [R5, exact binomial sums]:
    - n = 20: p = 0.9 Wald 0.876 vs Wilson 0.957; p = 0.97 Wald 0.456 vs Wilson 0.979.
    - n = 50: p = 0.97 Wald 0.781 vs Wilson 0.937.
    - n = 300: both 0.94-0.96.
  - **Design effect** [R5]: every-bar random levels 2 ATR away, strict trade-through within H:
    - ES 5-min H = 30 (n = 16,736): iid SE 0.38 pp vs batch-means (W = 2H) 0.79 pp, **deff 4.2**; stationary bootstrap 0.77 pp, deff 4.0;
    - NQ 5-min: deff 3.4-4.8;
    - ES and CL 1-hour, H = 12: deff 1.7-2.7.
    - Candidate probes (one per level per H bars): deff 1.4-2.8 [study:calib_ml].
    - x1_tv_validation tools (in progress; `out_protocols.txt`): on a non-overlapping grid (one record per H bars) deff ≈ 1.06.
  - **Peeking:** re-checking z ≥ 2 after every trial gives a false "✓ EDGE" ever shown 10/15/20% within 100/300/1,000 trials vs 0.1/0.5/1.4% with the confidence sequence [study:calib_ml, simulation]. On 288 real null paths: 13.5% (z ≥ 2), 4.5% (CS), 0.7% (mirror CS), 0.3% (self-normalised mirror) [study:skeptic].
- **Useful when:** every displayed rate and every verdict.
- **Fails when:** few blocks (G < 20: cluster variance biased down; Cameron, Gelbach & Miller 2008, cited by study), or a miscalibrated baseline (use the mirror).
- **Validation experiment:** MV null-placebo test.
  - H: under random-side, random-distance placebo pickers on real data, the APEX verdict shows a false "BEATS" ≤ 2.5% (upper) over the full history with peeking after every block.
  - Sample: 6 CME futures × 5-min/1-hour × 3 clock windows × 8 seeds. Pass: ≤ 2.5% overall and ≤ 5% in the worst cell.
- **Existing evidence:** above.
- **APEX recommendation:** INCLUDE-CORE (M8 CAL). Wilson for fixed-time rates; confidence sequences for verdicts; deff everywhere; replace the engine's `zEdge ≥ 2` rule (baseline line 2390).
- **Sources:** [study:calib_ml] §1.28-1.30, CAL-2; [study:skeptic] §1.21-1.30, SKEP-2/3; [R5] `out_verify.txt` §4, `out_dep.txt` E; Wilson 1927, Brown-Cai-DasGupta 2001 and Kish 1965 (unverified).

### 3.19 Bootstrap (iid, block, stationary) and Monte Carlo
- **Classification:** A; strong.
- **Definition:**
  - The bootstrap resamples the observed data to approximate a statistic's sampling distribution.
  - **Moving-block bootstrap:** resample contiguous blocks of length ℓ.
  - **Stationary bootstrap** (Politis-Romano): blocks of geometric length with mean ℓ = 1/p, wrapping circularly. It keeps the dependence within blocks and yields a stationary resample.
  - **Monte Carlo:** simulate from a specified null or model.
- **Market mechanism:** Outcomes overlap (H-bar windows), volatility clusters and calendar days cluster across symbols. The iid bootstrap ignores all three.
- **Mathematical implementation:**
  - **Stationary bootstrap index generator:** i₁ ~ U{1..n}; for each t > 1, with probability p jump to a new uniform index, otherwise i_t = i_{t−1} + 1 (mod n). Choose ℓ ≈ 2H-4H for H-bar outcomes, or one trading day for day-clustered statistics. Use B = 1,000-2,000 resamples.
  - **Day-block bootstrap:** resample symbol-days or calendar days. The calendar-day version is conservative because ES/NQ/RTY/YM move together [study:quant_pot].
  - **Synthetic nulls for Monte Carlo:**
    1. Driftless Gaussian random walk with intrabar steps.
    2. **Sign-flip / mirror series:** each bar rebuilt from the previous synthetic close with its own range and body, mirrored with probability ½. It keeps ranges, timing and volatility clustering and destroys direction [study:quant_regime, academic_sr].
    3. Bar-mirroring in place.

    A *directional* claim must beat these nulls. A *volatility or clock* effect should survive them.
  - **Knowable at:** offline (MV).
- **Required data:** exported ledgers or bar data (Python harness).
- **Pine v6 availability:** partial. `math.random(min, max, seed)` exists, and a seed makes the sequence repeatable [docs]. But B resamples × n per bar is wasted CPU within the 500 ms per-loop limit [docs: limitations.md]. In Pine use batch means (§3.18); keep bootstrap and Monte Carlo in MV. Do not draw Monte Carlo path fans on the chart (spec §17 forbids "random extra forecast lines").
- **Proxy limitations:** the block bootstrap assumes stationarity within the sample. Regime breaks (2020 crypto) violate it. Report sub-period results.
- **Evidence:**
  - [R5] ES 5-min H = 30: the iid SE understates the overlap-aware SE by a factor of 2.0 (deff 4.0). The stationary bootstrap (ℓ = 60) and batch means (W = 60-120) agree within 0.02 pp.
  - With W = 8H the batch estimate fell to deff 2.1. Too few blocks make batch means noisy too.
  - [study:quant_pot] 2,000 day-block resamples gave CIs for every log-loss comparison.
  - [study:skeptic] 288 + 96 real paths with placebo pickers validated the verdicts.
- **Useful when:** computing a CI of any ledger metric offline, or validating every in-Pine test (placebo, mirror, sign-flip).
- **Fails when:** the iid bootstrap is used on overlapping data, ℓ is too short relative to H, or there are only a few independent days (short samples: report it).
- **Validation experiment:** MV self-test.
  - H: stationary-bootstrap 95% CIs of a touch-rate excess cover the true value in 93-97% of synthetic replications.
  - Sample: GARCH-like synthetic paths with seasonality. Pass: coverage within [93%, 97%], against an expected ≈ 75% for the iid bootstrap.
- **Existing evidence:** above.
- **APEX recommendation:** INCLUDE-CORE in MV (BACKTEST_REPORT and VALIDATION_REPORT CIs). Pine: EXCLUDE resampling; use batch means. Monte Carlo nulls: INCLUDE-CORE in MV.
- **Sources:** [R5] `out_dep.txt` E; [study:quant_pot] §2.2; [study:skeptic] §2.4; [docs] math.md (`math.random`), limitations.md; Efron 1979, Künsch 1989, Politis & Romano 1994 (unverified).

### 3.20 Significance and multiple testing (Bonferroni, Holm, Benjamini-Hochberg, α budgets)
- **Classification:** A; strong.
- **Definition:**
  - **Bonferroni:** reject H_i if p_i ≤ α/m (controls FWER).
  - **Holm:** sort p₍₁₎ ≤ … ≤ p₍m₎; reject while p₍i₎ ≤ α/(m − i + 1); stop at the first failure (FWER, uniformly more powerful than Bonferroni).
  - **Benjamini-Hochberg (BH):** find the largest i with p₍i₎ ≤ q·i/m and reject 1..i (FDR under independence or positive dependence).
  - **Benjamini-Yekutieli (BY):** use q/(i·Σ_{k=1}^m 1/k) for arbitrary dependence.
  - **Anytime α budget:** give claim k a confidence sequence at level α·w_k with Σw_k ≤ 1. The weighted Ville bound keeps P(ever a false claim) ≤ α under any dependence and any peeking [study:skeptic citing Benhamou et al. 2026, abstract read by study B].
- **Market mechanism:** Users scan many symbols, timeframes and settings; developers scan many features. The best of k null configurations looks significant.
- **Mathematical implementation:**
  - Under the null, E[max z] over k configurations is 1.53 (k = 10, P(max ≥ 2) = 20%), 2.21 (k = 45, 64%) and 2.51 (k = 100, 90%).
  - Flipping through 10 symbols at one look: 21% chance of at least one false "✓ EDGE"; 80% with peeking [study:skeptic, simulation].
  - In-panel budget: the primary verdicts (mirror edge, R-expectancy) get α = 0.025 each. Family and league rows are "exploratory", with bands at α/k and no verdict words (SKEP-9).
  - Offline (MV): Holm across pre-registered hypotheses (§8). BH, at q = 0.05, only for exploratory screens labelled as such.
  - **t-hurdle** for new factors: t > 3 [study:skeptic citing Harvey-Liu 2020 and Chen-Zimmermann 2022, verified by study].
  - **Knowable at:** offline; in Pine, at each closed block.
- **Required data:** p-values or confidence sequences per hypothesis.
- **Pine v6 availability:** feasible: a fixed α split; Holm needs `array.sort`.
- **Evidence:**
  - [R5, synthetic] m = 55 tests (50 null, 5 true at z = 3.5), 4,000 replications:

    | Method | FWER | mean true positives | FDR |
    |---|---|---|---|
    | raw p < 0.05 | 0.922 | 4.70/5 | 0.323 |
    | Bonferroni | 0.046 | 2.89/5 | 0.013 |
    | Holm | 0.048 | 2.91/5 | 0.014 |
    | BH | 0.201 | 3.64/5 | 0.046 |

  - [study:calib_ml] Holm over 22 feature tests: only EQ (1-hour, p = 0.007) and age (opposite signs by timeframe) survive. Confluence, tier and draw become "unsupported", not "harmful".
- **Useful when:** any report with more than one comparison; the in-chart accuracy panel.
- **Fails when:** the family of tests is defined after seeing the data (forking paths). Pre-register (§8).
- **Validation experiment:** placebo panel test.
  - H: with the α budget, the APEX accuracy panel's total false-verdict rate under placebo pickers is ≤ 5% over a full history with peeking.
  - Pass: ≤ 5%.
- **Existing evidence:** above.
- **APEX recommendation:** INCLUDE-CORE (M8 CAL α budget; MV Holm for confirmatory tests, BH for exploratory screens).
- **Sources:** [R5] `out_verify.txt` §6; [study:skeptic] §1.25, §2.3 G, SKEP-9; [study:calib_ml] §2.2(b), `holm_lifts.py`; Holm 1979, Benjamini-Hochberg 1995 and Benjamini-Yekutieli 2001 (unverified).

### 3.21 Sharpe ratio, Probabilistic Sharpe Ratio and the Deflated Sharpe Ratio
- **Classification:** A; strong (theory); offline only.
- **Definition** (per-observation, non-annualised):
  - SR̂ = mean(R)/sd(R), over T observations (per trade in R units, or per bar).
  - γ̂₃ = sample skewness; γ̂₄ = sample **raw** kurtosis (normal = 3).
  - **PSR(SR*)** = Φ[(SR̂ − SR*)·√(T − 1) / √(1 − γ̂₃·SR̂ + ((γ̂₄ − 1)/4)·SR̂²)].
  - **Expected maximum Sharpe of N trials under the null:** SR₀ = √(V[SR̂_n])·[(1 − γ)·Φ⁻¹(1 − 1/N) + γ·Φ⁻¹(1 − 1/(N·e))], with γ = 0.5772156649 (Euler-Mascheroni) and V[SR̂_n] the variance of the Sharpe estimates across the N trials.
  - **DSR** = PSR(SR₀): the probability that the true Sharpe exceeds the best-of-N null.
  - Bailey & López de Prado (2014), J. Portfolio Management 40(5). Primary text **not opened** (host blocked). The structure (γ-blend, N, cross-trial SD of SR, non-normality term, T) was corroborated by a web-search summary of secondary sources this session.
- **Market mechanism:** Selection inflation. Many configurations are tried and the best is reported. Non-normal (negatively skewed, fat-tailed) returns make a given Sharpe less reliable.
- **Mathematical implementation and checks** [R5, synthetic]:
  - **Expected maximum.** With T = 500 iid N(0, 1) returns per strategy, the Monte Carlo mean of max SR vs the SR₀ formula (V = 1/(T − 1)):

    | N | Monte Carlo | formula |
    |---|---|---|
    | 2 | 0.0248 | 0.0233 |
    | 10 | 0.0683 | 0.0705 |
    | 45 | 0.0989 | 0.1001 |
    | 100 | 0.1121 | 0.1133 |
    | 1,000 | 0.1467 | 0.1457 |

    The approximation holds within 0.002.
  - **PSR(0) under a true zero Sharpe** should be Uniform(0, 1). Shares below 0.05 / above 0.95 (T = 250, 20,000 replications):
    - normal returns: 0.051 / 0.051;
    - t(4): 0.057 / 0.053;
    - negatively skewed lognormal: 0.058 / 0.054 with the non-normal term, vs 0.032 / 0.079 when normality is assumed.
    - So the γ₃/γ₄ correction matters under skew.
  - **Worked example:** SR̂ = 0.10 per trade, T = 500, γ₃ = −0.5, γ₄ = 5. PSR(0) = 0.985.
    - N = 10 trials: SR₀ = 0.0705, DSR = 0.739.
    - N = 45: SR₀ = 0.1001, **DSR = 0.499** (a coin flip).
    - If the trials are correlated so that V[SR̂_n] is half the iid value: DSR = 0.737.
  - **MinBTL:** (E[max of N standard normals])² / SR² years. For N = 45 and an annual SR of 1 this gives 5.00 years [R5]. That matches "about 45 configurations exhaust 5 years" [study:skeptic citing Bailey et al. 2014].
  - **Inputs to fix before computing:** N = the number of *effective* independent configurations tried (cluster correlated trials; count the developer's and the user's searches); T = n_eff if returns overlap (trades opened every bar on H-bar holds); R net of costs (§3.26).
  - **Knowable at:** offline, at the end of a fixed sample.
- **Required data:** per-trade or per-period returns of the selected configuration, plus the Sharpe estimates of all trials.
- **Pine v6 availability:** infeasible in a meaningful way. Pine cannot know how many configurations the user tried. A PSR readout of the ledger's R series is possible but must say "N = 1 assumed".
- **Proxy limitations:** a DSR cannot detect look-ahead. A leaky oracle with Sharpe 35 survives DSR and PBO [study:skeptic citing Gençay 2026]. The best SMC sweep results in Mahadzva (SSRN 7430998) fail DSR at every defensible trial count [study:skeptic, abstract re-fetched by study B].
- **Useful when:** reporting any strategy-like result in BACKTEST_REPORT.md (spec §24.8).
- **Fails when:** N is under-counted, T is not deflated for overlap, or the returns are gross of costs.
- **Validation experiment:** MV reporting rule.
  - Every strategy-style result reports SR̂, T, n_eff, γ₃, γ₄, N_eff (with the derivation), PSR(0) and DSR.
  - A claim of "edge" requires DSR ≥ 0.95 net of costs, plus a forward-only confirmation (§3.23).
- **Existing evidence:** above.
- **APEX recommendation:** INCLUDE-CORE in MV and BACKTEST_REPORT. EXCLUDE from the indicator UI.
- **Sources:** [R5] `out_verify.txt` §1-3; [study:skeptic] §1.25, §2.2; web-search summary this session (secondary: "Deflated Sharpe ratio" encyclopedia entry, the quantstrat `deflated.Sharpe.R` listing); Bailey & López de Prado 2012 (PSR) and 2014 (DSR); Mertens 2002 and Lo 2002 (all unverified).

### 3.22 Probability of Backtest Overfitting (PBO) by combinatorially symmetric cross-validation (CSCV)
- **Classification:** A; strong (theory); offline only.
- **Definition:** The probability that the configuration selected as best in-sample ranks below the median out-of-sample.
- **Market mechanism:** As §3.21. Parameter searches overfit noise.
- **Mathematical implementation** (Bailey, Borwein, López de Prado & Zhu):
  1. Build M (T × N): the per-period performance of N configurations on the same bars.
  2. Split the rows into S contiguous blocks of equal size (S even; S = 16 gives C(16, 8) = 12,870 combinations).
  3. For each combination c of S/2 blocks: train = union of the blocks in c; test = the complement. Let n* = argmax of the train Sharpe. Let ω̄_c = rank of n* in test/(N + 1) and λ_c = ln(ω̄_c/(1 − ω̄_c)).
  4. **PBO** = #{c : λ_c ≤ 0}/C.
  5. Also report the performance degradation (the slope of test SR on train SR across c) and the probability of an OOS loss.
  - With H-bar labels, purge H bars at every block boundary (§3.24).
  - **Knowable at:** offline.
- **Required data:** M for all tried configurations (the parameter grid of APEX's free inputs).
- **Pine v6 availability:** infeasible (a full grid of configurations is needed).
- **Proxy limitations:** blocks must be long relative to H and to volatility regimes. PBO is noisy for a single study.
- **Evidence** [R5, synthetic, T = 1,600, N = 50, S = 16, 5 replications each]:
  - all-null: PBO = 0.52, 0.43, 0.64, 0.15, 0.72 (average ≈ 0.5, but very dispersed);
  - one skilled configuration (SR 0.1 per bar): 0.10, 0.15, 0.02, 0.00, 0.00;
  - one weakly skilled configuration (SR 0.03 per bar): 0.42, 0.48, 0.73, 0.43, 0.37 (indistinguishable from null).
  - A single PBO number from one dataset is weak evidence. Report it with its bootstrap spread (resample blocks).
- **Useful when:** choosing defaults for APEX inputs (FAST vs BALANCED thresholds, horizon, minimum score) in Phase 6.
- **Fails when:** few configurations are highly correlated (it overstates independence), or the series is short.
- **Validation experiment:** MV.
  - H: the selected APEX default configuration has PBO ≤ 0.2 across 6 CME futures + BTC, with the bootstrap 90% upper bound ≤ 0.35.
  - If it fails, choose the simpler default (spec §25 "prefer the simpler model").
- **Existing evidence:** [study:skeptic] cites PBO via CSCV and MinBTL (strong theory).
- **APEX recommendation:** INCLUDE-CORE in MV for every tuned default. EXCLUDE from the indicator.
- **Sources:** [R5] `out_verify.txt` §5; [study:skeptic] §2.2; Bailey, Borwein, López de Prado & Zhu 2014/2017 (unverified here).

### 3.23 Walk-forward design and prequential evaluation
- **Classification:** A; strong.
- **Definition:**
  - **Walk-forward:** repeatedly fit (or select) on a training window, then evaluate on the next untouched window. Variants: rolling or anchored.
  - **Prequential** (Dawid 1984, cited by study): forecast with the state before the outcome is known, score at resolution, learn only from resolved outcomes. It is the online equivalent of walk-forward.
- **Market mechanism:** Non-stationarity. A model fitted on all data cannot be evaluated on that data.
- **Mathematical implementation:**
  - **Offline (MV):** folds k = 1..K with train [t₀, t_k), a purge gap of H bars, then test [t_k + H, t_k + H + L_test). Use an embargo after each test block when the test is reused for training later (§3.24).
    - Defaults: training ≥ 6 months intraday (≥ 2,000 H-windows), test 1 month, K ≥ 6.
    - Aggregate OOS metrics over folds only.
    - Report per-fold results and a split-half stability check: "one strong period masking weak ones" is the commonest failure [study:skeptic citing Mesfin 2026].
  - **In Pine:** the ledger is prequential by construction (open at bar close, grade at resolution).
    - **Forward-only sub-ledger:** records opened on realtime bars (`not barstate.ishistory`) after the settings were fixed. These are the only true OOS records on a chart (SKEP-7).
    - The learning window depends on `last_bar_index`, which changes between loads [study:calib_ml §1.33]. So disclose it, and keep learners neutral until proven.
  - **Knowable at:** fold boundaries / resolution bars.
- **Required data:** bar data with timestamps; ledger exports.
- **Pine v6 availability:** feasible for prequential grading and forward-only flags. Offline WF is in MV.
- **Proxy limitations:** a chart's history is always in-sample to the developer's defaults and to the user's tuning.
- **Useful when:** every reported number in VALIDATION_REPORT.
- **Fails when:** folds leak (no purge), or folds are chosen after the results are seen.
- **Validation experiment:** the MV protocol itself. H: OOS results of each pre-registered hypothesis (§8) have the same sign in ≥ 5 of 6 folds and in both halves.
- **Existing evidence:** [study:skeptic] Zhang 2026: an LLM-found strategy with Sharpe ≈ 3 in discovery and validation fell to 0.26 on its holdout. [study:calib_ml] prequential tests throughout.
- **APEX recommendation:** INCLUDE-CORE (MV; M8 CAL forward-only sub-ledger).
- **Sources:** [study:skeptic] §1.29, SKEP-7; [study:calib_ml] §1.27, §1.33.

### 3.24 Purging and embargo for overlapping horizons
- **Classification:** A; strong.
- **Definition:**
  - Each label i spans [t_i⁰, t_i¹], from its open bar to its resolution bar (≤ t_i⁰ + H).
  - **Purging:** remove from the training set every sample whose span overlaps any test sample's span.
  - **Embargo:** also remove training samples that start within h_e bars after a test block ends, because of serial dependence in features (López de Prado 2018 ch. 7, cited by study).
- **Market mechanism:** Overlapping labels share price paths. A training label that resolves inside the test period leaks the test outcome.
- **Mathematical implementation:**
  - Purge condition: t_i⁰ < t_test_end and t_i¹ > t_test_start.
  - Embargo h_e = max(H, 0.01·T).
  - For the dependent-data variance use HAC with lag H − 1 (Hansen-Hodrick 1980, cited by study) or block variance (§3.18).
  - **Uniqueness weights:** u_i = mean over t ∈ [t_i⁰, t_i¹] of 1/c_t, where c_t = the number of labels active at t. Use them as sample weights.
  - **Knowable at:** offline.
- **Required data:** label start and end times (ledger export).
- **Pine v6 availability:** n/a. In Pine the analogue is "learn only at resolution, predict with the state before open", which is already the case in the ledger [study:calib_ml §3.1].
- **Useful when:** any cross-validated or walk-forward fit in MV (PBO blocks, threshold tuning).
- **Fails when:** H is variable and not recorded. Store the resolution bar.
- **Validation experiment:** MV leakage test.
  - H: removing the purge raises in-sample-looking OOS performance on a deliberately leaky feature (a future-close proxy), and the purge removes it.
  - Pass: the leaky feature's OOS lift is ≤ 0.2% LL with the purge.
- **Existing evidence:** [study:calib_ml] §1.28 (overlap remedies); [study:skeptic] §1.21.
- **APEX recommendation:** INCLUDE-CORE (MV).
- **Sources:** [study:calib_ml] §1.28; López de Prado 2018 chs. 4, 7 and Hansen & Hodrick 1980 (cited by study; unverified here).

### 3.25 Look-ahead, leakage and survivorship protections
- **Classification:** E/A; strong. Enforced by construction; not detectable statistically [study:skeptic].
- **Definition:**
  - Look-ahead: using information not available at decision time.
  - Leakage: the outcome's information entering features or labels.
  - Survivorship: conditioning the sample on success. This covers delisted symbols, hits-only statistics and visual ghosts.
- **Market mechanism:** none. These are evaluation artefacts that make noise look like skill.
- **Mathematical implementation (rules for APEX):**
  1. Structural state, scores, selection and learning run only when `barstate.isconfirmed`. `var` state rolls back on realtime ticks [docs].
  2. HTF data come from `request.security(sym, tf, expr[1], lookahead = barmerge.lookahead_on)`, never below the chart TF (CONTEXT.md).
  3. Pivots are confirmed at bar t + L and recorded with that knowable bar. Drawings anchored in the past must also record the selection bar (`activeSince`) [study:skeptic §1.20].
  4. Ledger records freeze their inputs and forecasts at open. Scores use uncapped values.
  5. No statistic is computed over hits only. ETA uses time-to-event with censoring: with a fixed horizon, the KM median = the median of min(T, H + 1). Adverse excursion uses all trials [study:skeptic §1.18].
  6. Ghosts are kept for every outcome, including targets replaced by a challenger [study:skeptic SKEP-10].
  7. Offline symbol universes include expired contracts and the continuous-contract construction actually available on TradingView (not back-adjusted by default [study:calib_ml]). Crypto universes include delisted coins where the data allow.
  8. The intrabar order of high and low is unknown. The engine's bar-colour rule is right on 88.1-88.7% of bars vs 80.6-80.7% for the TradingView broker-emulator rule; ambiguous bars are ≤ 1.7% of trials, with an R bias ≤ +0.02 [study:skeptic, trade_mgmt]. Magnifier tools resolve them [x1_tvv_tools/out_magnifier.txt: pooled disagreement with 1-minute truth 0.19% (TV), 0.14% (colour), 0.02% (magnifier), n = 10,799].
  - **Knowable at:** by definition.
- **Required data:** n/a.
- **Pine v6 availability:** feasible (these are coding rules).
- **Useful when:** always.
- **Fails when:** live-preview features leak into confirmed alerts (spec §19.1).
- **Validation experiment:** REPAINT_AUDIT.
  - H: every confirmed signal and ledger record is identical between a full historical load and a bar-replay run.
  - Metric: diffs of exported records. Pass: zero diffs.
  - Plus the leaky-oracle canary: inject a feature equal to the sign of the next close. The audit must detect it by construction review, not by statistics.
- **Existing evidence:** [study:skeptic] §1.18-1.20, SKEP-1, SKEP-10.
- **APEX recommendation:** INCLUDE-CORE (all modules; REPAINT_AUDIT).
- **Sources:** [study:skeptic]; [docs] execution_model.md; x1_tvv_tools/out_magnifier.txt (tool output, report in progress).

### 3.26 Transaction-cost sensitivity
- **Classification:** E/A; strong.
- **Definition:**
  - Net R = gross R − c/risk, where c = spread + commission + slippage (in price units; ticks × τ) and risk = the stop distance.
  - Break-even cost c* is the value of c at which the net metric is 0.
- **Market mechanism:** Liquidity providers earn the spread. Takers pay the spread and impact. On short timeframes the cost is a large fraction of a typical move.
- **Mathematical implementation:**
  - Evaluate every trade-like metric (R̄, profit factor, DSR) at c ∈ {0, 0.5, 1, 2, 4} ticks per side (instrument-specific), and report the curve plus c*.
  - Filter diagnostic: the share of trades with c/risk > 10%. Much of the apparent edge on short timeframes disappears when they are removed [study:skeptic citing an open-source sweep backtest].
  - **Tradeability gate (M9):** expected move E|ΔP_H| (from forward variance, ≈ √(2/π)·√V_H for Gaussian, or empirical) must exceed k·c with k = 5 by default; otherwise the label is "poor location / insufficient movement".
  - **Knowable at:** at entry (cost input) and at resolution (R).
- **Required data:** a user cost input in ticks (Pine cannot observe spread or commission), `syminfo.mintick`, `syminfo.pointvalue`.
- **Pine v6 availability:** feasible (an input plus arithmetic). No bid/ask data on standard charts (see the orderflow study).
- **Proxy limitations:** real slippage depends on size, time and volatility, so a constant-cost assumption is optimistic in fast markets. Stops on coarse bars are filled at the stop price even when 1-minute prints gapped through, which is optimistic by +0.002-0.02 R [study:skeptic].
- **Useful when:** any R, EV or signal-quality readout (spec §16).
- **Fails when:** costs are omitted, which is the default in most indicator backtests.
- **Validation experiment:**
  - H: APEX signal states (STRONG BUY ... STRONG SELL) have a net R̄ lower confidence bound > 0 at a realistic cost (e.g. ES 1 tick per side + commission).
  - Sample: walk-forward OOS, 6 CME futures + BTC perpetual, 5-min and 1-hour. Pass: the lower bound > 0 in ≥ 4 of 7 sets after Holm.
  - Report NOT RUN if the data are lacking.
- **Existing evidence:** [study:skeptic] C21: 14 OHLCV signal families on MNQ 5-min 2021-2025 carry 0.07-1.50 points of gross content vs a 2-point friction; none passes walk-forward (Mesfin 2026, re-read by study B). C6/C8: FVG and OB reaction edges are "in the red after costs" (Nordman, re-fetched by study B).
- **APEX recommendation:** INCLUDE-CORE (M9 RISK cost input and gate; MV cost curves). Readouts say "gross" or "net".
- **Sources:** [study:skeptic] §1.31, C6, C8, C21, SKEP-4.

### 3.27 Paired mirror/placebo controls and the model-free R-expectancy test
- **Classification:** A; moderate (measured on real nulls).
- **Definition:**
  - **Mirror residual:** D = (y − p₀) − (y_m − p₀,m), where y_m is the outcome of the level at the same distance on the opposite side, on the same bar, under the same rule.
  - **R-expectancy:** under any martingale, every bounded target/stop/time-out rule has E[R] = 0 (optional stopping). With drift μ, Wald's identity gives E[R] = side·μ·E[τ]/risk [study:skeptic §1.15].
- **Market mechanism:** Baseline miscalibration by clock, volatility state or roll gaps is direction-free, so the mirror cancels it. Side skill moves D up twice as much (the DOL up, the mirror down).
- **Mathematical implementation:**
  - S = ΣD over closed blocks and V = ΣD_g² (self-normalised). The verdict uses the confidence-sequence boundary at α = 0.025 (§3.18).
  - R_adj = R_out − side·μ̂·τ/risk − c/risk, where μ̂ is the prequential mean of ΔC up to the record's open. Then block-centred variance and a confidence sequence.
  - **Knowable at:** at resolution.
- **Required data:** the ledger, with stored mirror outcomes.
- **Pine v6 availability:** feasible (SKEP-2/SKEP-4 sketches in the study).
- **Proxy limitations:**
  - The sharp null (exchangeability of DOL and mirror) fails on gappy instruments with tight stops, where the null is E[R] ≤ 0: GC 5-min with tight stops −0.149 ± 0.036 R [study:skeptic].
  - Synthetic export pipelines (`x1_tvv_tools/synth_trades.csv`) were built only to test the harness; their outputs are not evidence.
- **Evidence:**
  - On 288 real no-skill paths, false "✓" rates: z ≥ 2, 13.5%; one-sample CS, 4.5% (23% in busy-hour 5-min); mirror CS, 0.7%; self-normalised mirror, 0.3%.
  - Power for an informed picker rose from 19% / 44% to 23% / 71% (1-hour / 5-min) [study:skeptic].
  - Null paired-difference SD is about 0.77 per pair on a non-overlapping grid. MDE (anytime) is 9.9 pp at 1,000 pairs and 3.1 pp at 10,000 pairs [x1_tvv_tools/out_protocols.txt, real CME data, tool output of an in-progress report].
- **Useful when:** any edge verdict on a chart, or offline.
- **Fails when:** the picker's side skill is tiny relative to the MDE. The best-supported ICT effects are 2-5 pp vs an active-ledger MDE of 5.5-9.5 pp (anytime) [study:skeptic]. INCONCLUSIVE is then the honest output.
- **Validation experiment:** as §3.18 (placebo false-alarm rate ≤ 2.5%), plus power on informed pickers ≥ 50% at a +5 pp side-excess with n ≈ 2,000 records.
- **Existing evidence:** above.
- **APEX recommendation:** INCLUDE-CORE (M8 CAL primary verdicts; MV).
- **Sources:** [study:skeptic] SKEP-2, SKEP-4, §2.4 A; x1_tvv_tools outputs (read this session).

---

## 4. Interactions and redundancy

Never count the same evidence twice. Each group below measures one underlying quantity; APEX keeps **one representative per role** and treats the rest as diagnostics.

| Group | Members | Why they are one measurement | Keep |
|---|---|---|---|
| Scale | SD, EWMA σ, ATR, Parkinson/GK/RS/YZ, MAD, `ta.dev` | All estimate volatility. ATR/σ = κ ≈ 1.39-1.54 on clean CME data [study:skeptic]. Range estimators add +0.28% LL alone (n.s.) [study:quant_pot] | ATR14 for display distances; blended unit or forward variance for probability surfaces; MAD for robust feature scaling |
| Normalising transform | z, robust z, percentile rank, tanh(z/c) | Monotone transforms of the same rank information | One transform per feature: percentile rank for regime-type features, robust z (bounded) for spike-type features |
| Trend / momentum | OLS slope, ROC, EMA slope, EMA separation, EMA stack, MACD, signed ER, +DI−−DI | The OLS slope is a parabolic-weighted mean return with corr 0.91-0.95 with ROC over the same window (exact) [R5]. EMA-based measures are exponentially weighted sums of the same returns. None adds side skill beyond geometry (≤ 0.25% LL) [study:quant_regime] | One trend factor (e.g. ROC or OLS slope in ATR units), descriptive, drift shrunk to 0 by default (spec §8) |
| Regime labels | ER, CHOP, ADX, Hurst, VR | All describe the last window; ≈ 0 persistence; noise floors 16-38% on a random walk [study:quant_regime] | Volatility state (persistent) plus at most one efficiency label for display, with base-rate disclosure |
| Probability of the same event | analytic PoT, empirical surface, vol-clock PoT, calibrated PoT | Same target and horizon. Combine by a gated mixture, never by summing scores | Empirical surface (time-of-day rows, blended unit) → gated OPS calibration → display |
| Location-at-a-level features | confluence count, key-level tier, "self-confluence" of PDH/PDL with its own anchor | The engine double-counts a key level with its own anchor (+5.25 points) [study:calib_ml CAL-5] | One source-tier attribute; count distinct prices only once |
| Correlated instruments | ES, NQ, RTY, YM | Cross-symbol correlation 0.90-0.97 (returns) [R5]. 6 CME symbols are worth 3.13 effective symbols for paired residuals [x1_tvv tools] | Pool with n_eff = k/(1 + (k − 1)ρ̄) |
| Overlapping outcomes | every-bar H-window records | deff ≈ 4 at H = 30 on 5-min [R5] | Block variance, n_eff = n/deff, one probe per level per H bars |

**Consolidation rules for the decision engine (spec §13.2).**
1. **Additive on the log-odds scale, relative to the distance baseline.** Each module contributes a lift ℓ_k with its own shrinkage. The combined evidence is logit p₀ + Σw_k·ℓ_k. Correlated modules receive a joint weight estimated from their covariance, never independent weights. If the covariance is unknown, use the maximum of a correlated group, not the sum.
2. **A module with missing or unreliable data contributes ℓ = 0 and weight 0**, never a neutral-looking normal score (spec §13.2). M0 DATA supplies the flags: warm-up incomplete, volume missing or synthetic, roll gap in window, >4-ATR close jumps above about 1% of bars (κ cue [study:skeptic §2.4 D]), intermarket symbol unavailable.
3. **Scores stay scores.** The Draw Score ranks; only a graded, gated map turns it into a "calibrated frequency" (§3.17). Selection is a utility decision: rank by E[U] = P·u, e.g. expected reach d·P(d), which peaks at d ≈ 0.75σ√H with P ≈ 0.45. The study measured 1.10-1.43 ATR delivered vs 0.86-1.09 for the hand score [study:calib_ml].

---

## 5. Data requirements and assumptions

### 5.1 Data and assumptions
- **Inputs available in Pine:** OHLC, volume (quality varies), `time`, `syminfo.*` (mintick, pointvalue, type, timezone), `request.security` for HTF and other symbols (≤ 40 unique requests), future bar times up to 500 bars ahead [study:quant_pot citing docs].
- **Not available:** bid/ask, depth, true aggressor volume, holiday calendars, news calendars, trial counts, other users' searches.
- **Assumptions behind the formulas:**
  - Local stationarity within windows (violated at rolls, regime breaks and 2020-style crises).
  - Conditional independence of non-overlapping blocks (approximately true at block width ≥ 2H, G ≥ 20).
  - Driftless martingale as the null for direction (supported: VR z* ≈ 0 for index futures [R5]; races within 0.4-1.2 pp of b/(a + b) [study:quant_pot]).
  - Continuous-path reflection for touches (ratio 1.99-2.02 [study:quant_pot]).
- **Platform limits that shape the estimators:**
  - 500 ms per loop per bar.
  - A total execution-time limit that depends on the plan.
  - Collections ≤ 100,000 elements.
  - Historical buffer 5,000 bars for most series (10,000 for OHLC and time).
  - Float precision 1e-16, with comparisons rounded to 9 decimals.
  - Compilation ≤ 2 minutes [docs: limitations.md, type_system.md].

### 5.2 Model-card template (mandatory for every APEX model, spec §10)

Every scoring, probability or forecast component must ship with a filled card in MATHEMATICAL_SPECIFICATION.md. If a field cannot be filled, the component may not carry a probability label and defaults to "score".

| Field | Content required |
|---|---|
| ID / module | e.g. M4-PoT |
| Question | the plain-language question answered |
| Output type | heuristic score / relative rank / model confidence / calibrated frequency (spec §15). Only the last may say "%" as a probability |
| Target (event) | exact definition: level price, strict trade-through vs touch, side, tie rule for same-bar double touch |
| Horizon | H bars of the chart TF (and clock-time equivalent), plus the resolution rule (first touch or t + H) |
| Unit of analysis and sampling | what spawns a record (every candidate level once per H bars; every signal; every bar) and the de-duplication rule |
| Knowable-at bar | when the prediction is frozen (confirmed close of bar t) and when the outcome is known |
| Inputs | feature list with normalisation (M1), all frozen at open; data-quality flags used |
| Baseline(s) | distance-matched random level; mirror; nearest pool; zero-drift random walk; simple trend rule (spec §20 "simple trend baseline") |
| Model and learning rule | formula; prequential update; prior and shrinkage strength m; gate rule |
| Metrics | primary proper score (LL or Brier; pinball/CRPS for bands; net R̄ for trade rules); calibration slope and CITL; hit/expected; ATR delivered |
| Dependence handling | block width W, minimum blocks G ≥ 20, deff reporting, cross-symbol n_eff |
| Inference | confidence sequence at the allocated α (budget), three-way verdict with materiality δ |
| Sample | symbols, timeframes, dates, n records, n_eff, events/non-events (≥ 100 each for slopes); walk-forward folds; forward-only n |
| Pass / fail | pre-registered criterion (§8), including the cost assumption |
| Failure modes | known (roll gaps, DST, missing volume, thin sessions) |
| Display wording | exact label and tooltip, including the base rate |
| Version | change log of definition changes (a definition change resets the evidence) |

**Example cards (abridged).**
- **M4-PoT.**
  - Target: the level is traded through (strict) within H = 30 bars. Output: calibrated frequency, only after gated OPS passes; otherwise "model PoT (uncalibrated)".
  - Baseline: distance-matched surface. Metric: LL, slope and CITL on the candidate ledger.
  - Pass: slope in [0.9, 1.1], |CITL| ≤ 2 pp, ≥ 100 events and non-events / deff.
- **M4-Draw Score.**
  - Output: relative rank. Target for grading: the selected target's touch within H vs p₀, plus ATR delivered.
  - Baselines: nearest, random candidate, runner-up, mirror.
  - Pass to claim "beats nearest": mirror-paired CS lower bound > 0 at α = 0.025.
- **M7-Forecast path.**
  - Output: scenario plus empirical band. Targets: sign(r_H) (Brier vs 0.5 and vs the drift-free baseline), the terminal error in ATR (pinball loss at the 10/50/90% quantiles), and band coverage (Kupiec).
  - Baselines: zero drift; EMA extension.
  - Pass to show the band as "x% band": coverage within ±2 pp OOS.
- **M5/M3-Signal states.**
  - Output: categorical signal. Target: net R̄ of a fixed bracket (target, stop, time-out H) after costs, and the hit rate vs the gambler's-ruin base rate 1/(1 + RR).
  - Baselines: always-long with drift adjustment; random entry; simple trend rule.
  - Pass: drift-adjusted net R̄ lower bound > 0, Holm across states, DSR ≥ 0.95 with honest N.

---

## 6. Limitations and failure modes (asset classes, sessions, DST)

- **Futures (continuous contracts):**
  - Roll gaps unless back-adjustment is enabled; it is off by default on TradingView [study:calib_ml].
  - Roll gaps corrupt surfaces (GC 1-hour CITL −4.25 pp, deff 7.7), κ (0.86 vs 1.4-1.5) and kurtosis.
  - Detect with the M0 κ cue and the >4-ATR jump count. Exclude windows containing gaps from learning (CAL-10).
  - The daily maintenance halt (22:00/23:00 UTC) inserts gap returns; compute intra-session returns or include the gap² term in variance.
- **FX:** no centralised volume (tick volume is not traded volume); weekend gaps; liquidity follows the London/NY clock; the DST mismatch between London and New York for about 3 weeks a year shifts session cells.
- **Equities and ETFs:**
  - Overnight gaps dominate the variance of daily bars.
  - RTH and extended hours must be distinguished (session settings change the series).
  - Splits and dividends need adjusted data.
  - Intraday zero-return share and tick discreteness are higher for low-priced stocks, so MAD can be 0 (floors, §3.2).
- **Crypto spot and perpetuals:**
  - 24/7, so there is no session open; seasonality peaks around 16 UTC and bottoms near 5 UTC, with spikes at the 00/08/16 UTC funding times [study:quant_pot, Hansen-Kim-Kimbrough 2024, verified by study].
  - Exchange-specific feeds differ.
  - Jumps arrive from calm states: vol-standardised excess kurtosis rises to 204 on BTC 1-hour [R5].
  - Significant 1-hour mean reversion (VR(4) 0.920, z* −4.1, 2017-2025) [R5].
  - Moments are unstable by year (excess kurtosis 7.5-115) [R5].
  - Sub-micro-priced tokens hit Pine's 9-decimal comparison rounding and the `ta.stdev` ε-snapping, so work in log returns.
- **DST and time keys:** key time-of-day statistics to the exchange time zone, not UTC. TIME-3 measured +3.9% (NY-keyed) vs +3.5% (UTC-keyed) Brier [study:quant_pot]. Use 3-hour blocks to absorb residual DST effects.
- **Thin sessions:** jump-and-back prints on tiny volume (YM 2026-03-18, 2-29 contracts, ±66 bp) [R5]. Use robust scale and treat them as data events, not signals.
- **Event jumps:** a single cross-asset event (2026-03-23 11:05 UTC) dominates three-month moments [R5]. Stress tests must include such days (spec §21).
- **Small samples and long horizons:** G blocks = (calcBars − warm-up)/(2H) gives 78 at H = 30 and 5 at H = 450 [study:calib_ml], so verdicts must say "H too long for the window".
- **Learning-window path dependence:** results differ between loads because the start depends on `last_bar_index` [study:calib_ml §1.33].
- **What statistics cannot do:** detect look-ahead or code bugs. An order-block detector bug passed every statistical gate and was caught by eye [study:skeptic citing Mahadzva]. Only construction review and the repaint audit can.

---

## 7. Recommendations for APEX (ranked)

| Rank | Recommendation | Module | Decision |
|---|---|---|---|
| 1 | Every probability label requires a model card (§5.2), a proper-score grade, a calibration slope and CITL on the candidate (shadow) ledger, and a gate. Otherwise call it a score | M8 CAL, M4 DOL, M6 FQ | INCLUDE-CORE |
| 2 | Zero drift by default in every probability, race and forecast path. Any drift must pass a prequential gate (James-Stein shrinkage at most) | M4, M7 | INCLUDE-CORE |
| 3 | Volatility normalisation layer: ATR14 (display), ticks (costs), blended unit √(ATR14·ATR100) or the forward-variance clock (probabilities, intraday), exchange-time keys | M1 NORM | INCLUDE-CORE |
| 4 | Distance-matched base rate shown next to every rate; mirror-paired, anytime-valid three-way verdicts with an α budget (0.025 + 0.025) and a G ≥ 20 guard | M8 CAL | INCLUDE-CORE |
| 5 | Overlap-aware inference everywhere: open-keyed centred blocks (W ≥ 2H, prefer 4H), deff, n_eff; Wilson for fixed-time rates | M8 CAL, MV | INCLUDE-CORE |
| 6 | Beta-Binomial / Poisson-Gamma shrinkage and partial pooling for every cell rate (m = 30 surfaces; α = 60 lifts); no cliff gates | M4, M8, M2 | INCLUDE-CORE |
| 7 | Gated online Platt scaling (2-parameter ONS) as the only default learner; unregularised SGD and naive-Bayes multipliers excluded | M8 CAL | INCLUDE-CORE |
| 8 | Robust statistics: MAD-based scale with floors (never `ta.dev`); exact percentile ranks; bounded transforms; empirical-quantile forecast bands | M1 NORM, M7 FCST | INCLUDE-CORE |
| 9 | Volatility state with hysteresis for display and stratification; no trend-label keys in probability surfaces; time-of-day rows | M2 REGIME | INCLUDE-CORE |
| 10 | Consolidate trend descriptors into one factor (the OLS slope/ROC identity); never display regression t or R² | M3 BIAS, M7 | INCLUDE-CORE |
| 11 | Cost input and tradeability gate; all R readouts labelled gross or net; break-even cost in reports | M9 RISK | INCLUDE-CORE |
| 12 | Offline validation harness: walk-forward with purge and embargo; stationary/day-block bootstrap CIs; Holm (confirmatory) and BH (exploratory); DSR with honest N; PBO for every tuned default; forward-only results | MV | INCLUDE-CORE |
| 13 | Data-quality module: roll-gap and jump count, κ cue, zero-return share, missing-volume flag → weights set to 0 | M0 DATA | INCLUDE-CORE |
| 14 | Intermarket correlation with a stability gate (Spearman, Fisher-z dispersion, sign-flip share), display-only until a pre-registered test passes | M10 INTER | INCLUDE-OPTIONAL |
| 15 | Huber robust slope toggle; SA quantile tracker for long windows; τ₄ / tail diagnostics in the debug dashboard | M7, M1, debug | INCLUDE-OPTIONAL |
| 16 | Offset probit pillar lifts and stratified interaction readouts (measure-only) | M8 CAL | RESEARCH-ONLY |
| 17 | Variance ratio, ACF, Theil-Sen, P², moments as features | MV | RESEARCH-ONLY |
| 18 | Rolling Hurst/VR/ADX/CHOP regime switches; regression t-stat or R² as significance; z → Φ(z) probability labels; Monte Carlo path fans on chart; PSR/DSR in the UI | — | EXCLUDE |

---

## 8. Open questions and Phase 6 experiments (pre-registered)

The general protocol for all experiments:
- Data: 6 CME futures (ES, NQ, RTY, YM, CL, GC; 1-minute source aggregated to 5-min, 15-min and 1-hour), BTC 1-hour, EURUSD 1-hour and the S&P 500 daily where relevant.
- Walk-forward by month with an H-bar purge. Block variance (W = max(2H, 4H where possible), G ≥ 20). Day-block bootstrap CIs (2,000 resamples).
- Holm across this list for confirmatory claims. Costs as in §3.26.
- Report NOT RUN where the data are missing.

| ID | Hypothesis | Outcome | Horizon | Baseline | Metric / test | Pass criterion |
|---|---|---|---|---|---|---|
| S1 | The drift-free empirical PoT (time-of-day rows, blended unit, gated OPS) is calibrated | strict trade-through | H = 30 (5-min), 12 (1-hour) | distance-matched surface | calibration slope, CITL, LL with block CIs | slope in [0.9, 1.1], \|CITL\| ≤ 2 pp, ≥ 100 events and non-events / deff, on ≥ 6 of 8 sets |
| S2 | Adding shrunk regression drift to the forecast does not improve direction | sign(r_H) | H = 30 / 12 | zero drift | ΔLL, block bootstrap | include drift only if CI > 0 on ≥ 5 of 7 sets |
| S3 | Empirical-quantile forecast bands in vol units cover nominal 80/90% | r_H inside the band | H = 20-120 | Gaussian ±zσ√H bands | coverage, Kupiec LR with clustering | coverage within ±2 pp and Kupiec p > 0.05 on ≥ 5 of 7 series |
| S4 | The mirror-paired anytime verdict is correctly sized | false "BEATS" | full history, peeking each block | — | placebo pickers, 288 paths | ≤ 2.5% overall, ≤ 5% worst cell |
| S5 | The mirror verdict has power | detection | n ≈ 2,000 records | one-sample CS | informed picker at +5 pp | power ≥ 50% |
| S6 | Gated OPS protects broken bases at negligible cost | LL | per probe | uncalibrated surface | ΔLL clean vs roll-gap charts | ≥ −0.3% clean, ≥ +2% roll-gap |
| S7 | Robust-z thresholds have more stable exceedance across vol terciles than SD-z | \|z\| > 3 share | per bar | SD-z | max/min tercile ratio, bootstrap | robust ratio lower, CI excludes 0 |
| S8 | A stability-gated intermarket feature improves direction OOS | sign(r_H) | H = 12 (1-hour) | geometry | ΔLL, block bootstrap | CI > 0 and stable sign in halves (expected to fail) |
| S9 | Pre-registered interaction: proximity × HTF alignment | touch excess | H = 30 / 12 | distance baseline | difference of shrunk excesses, Holm | Holm p < 0.05, same sign in halves (expected to fail) |
| S10 | Tuned APEX defaults are not overfit | OOS rank of the selected default | per fold | median configuration | PBO via CSCV (S = 16) with bootstrap | PBO ≤ 0.2, 90% upper bound ≤ 0.35 |
| S11 | Signal states pay after costs | net R̄ (drift-adjusted) | bracket with time-out H | random entry; always-long; simple trend rule | CS on net R̄; Holm; DSR with honest N | lower bound > 0 in ≥ 4 of 7 sets, DSR ≥ 0.95 |
| S12 | Repaint and leakage audit | record diffs | — | — | historical load vs bar replay; leaky-oracle canary | zero diffs; canary caught by review |
| S13 | Pine ports equal the Python references | numeric equality | — | float64 two-pass | max relative error | ≤ 1e-9; no negative variance; sub-micro-price symbol included |
| S14 | BTC 1-hour mean reversion (VR(4) 0.92) is already absorbed by the empirical surface | touch | H = 30 | surface without reversion term | ΔLL | reversion term adds < 0.5% LL (keep it out) |

**Open questions.**
1. The cost of `ta.percentile_*` and `array.sort` at L = 250-500 per bar on TradingView (Profiler). This determines whether the exact MAD and percentiles fit the time budget at 20k bars.
2. Whether the forward-variance clock or the blended unit wins per chart. This needs TIME-4's per-chart scorecard inside APEX.
3. GC 1-minute January autocorrelation (−0.25): data artefact or market behaviour? Check against a second data source before using GC 1-minute in Phase 6.
4. The honest trial count N for the DSR of APEX defaults. It must include the study's and the architecture's design iterations; propose N_eff from clustering of the configuration grid's return correlations.
5. The x1_behavioral report and the final x1_tv_validation report were not available when this was written. Their findings on harness design (strategy twin, magnifier, export protocol) may refine §3.23-3.27.
6. Whether the confidence-sequence ρ should be 5 (tightest near 190 trials) or 10 (near 370 trials) for APEX's typical ledger sizes [study:calib_ml]. Decide from the expected records per 5,000 bars at default settings.

---

## 9. Sources

**Opened in this session**
- Pine v6 reference mirror (`docsrc/jabez4jc_pinescriptv6/`):
  - `reference/ta.md`: `ta.stdev` (biased default, ε-snapping Pine equivalent), `ta.variance`, `ta.dev` (mean absolute deviation from the SMA), `ta.median`, `ta.linreg`, `ta.correlation`, `ta.percentrank`, `ta.percentile_linear_interpolation`, `ta.percentile_nearest_rank`, and their `na` handling.
  - `reference/array.md`: `array.median`, `percentrank`, `percentile_*`, `stdev`, `covariance`, `standardize`.
  - `reference/matrix.md`: `matrix.inv` (LU), `matrix.pinv` (SVD).
  - `reference/math.md`: `math.random` (seeded repeatability), `math.sum`.
  - `language/type_system.md`: float precision 1e-16; comparisons round to nine fractional digits.
  - `language/execution_model.md`: rollback, `varip`.
  - `writing_scripts/limitations.md`: 500 ms per loop; collections ≤ 100,000; history buffer 5,000/10,000; 2-minute compile limit.
- Study reports (combined A + B): `quant_pot.final.md`, `calib_ml.final.md`, `quant_regime.final.md`, `academic_sr.final.md`, `skeptic.final.md`. Read in full or in the relevant sections; numbers are quoted with their samples. Sibling references to `ict_time`, `bias_dol`, `smt_inter`, `trade_mgmt` and `x1_implied_vol` are as cited by those reports.
- x1_tv_validation tool outputs (report not yet written): `study/x1_tvv_tools/out_protocols.txt`, `out_pooling.txt` and `out_magnifier.txt` (real CME data). `out_eval_pool.txt` was **not** used as evidence: it is built from a synthetic export (`make_synth.py`).
- Engine code: `brief/baseline_v2.pine`: `f_erfc` 411, `f_pot` 434, `f_race` 447, `f_raceH` 466, `f_logit` 484, `f_sigm` 488, `f_wilson` 492-503, `potSig` 916, `potMu` 917, `cluSt` 1077 and 1463-1469, `f_calMult` 1376, EDGE z-test 2383-2391. Legacy: `apex/legacy/DOL_Engine_early.pine` (line 1022, `ta.percentrank` volatility filter); `apex/legacy/liquidity-flow-pro.pine` ("model confidence, NOT a probability" labelling, line 1081).
- Web search (this session, secondary summary only): a query on the deflated Sharpe ratio returned an encyclopedia entry "Deflated Sharpe ratio", gmarti.gitlab.io, 5x5x5x5.github.io, endgame-ml docs, and the quantstrat `deflated.Sharpe.R` listing. Only the search summary was read; the pages themselves were blocked (host not allowed).
- R5 computations (this session): scripts and outputs in `/tmp/claude-0/-home-user-m/7ce60006-3639-59b1-8cd3-87355409d58a/scratchpad/r5_stats_tools/`.

**Verified by the study reports (cited through them)**
Howard, Ramdas, McAuliffe & Sekhon 2021 (confidence sequences); Johari, Pekelis & Walsh 2017 (peeking); Gupta & Ramdas 2023 (online Platt scaling); Van Calster et al. 2016 (calibration hierarchy); Collins, Ogundimu & Altman 2016 (≥ 100 events); Roelofs et al. 2020 and Kumar et al. 2019 (ECE bias); Efron 2011 (Tweedie); Perelló, Gutiérrez-Roig & Masoliver 2011; Broadie, Glasserman & Kou 1997; Chang & Peres 1997; Hansen, Kim & Kimbrough 2024; Engle & Sokalska 2012; Gao, Han, Li & Zhou 2018; Kurth, Eisler, Rej & Bouchaud 2026; Safari & Schmidhuber 2025; Le 2026; Portnaya 2026; Mesfin 2026; Tangirala (SSRN 7483658); Darmanin 2026; Benhamou et al. 2026; Coqueret 2023; Chen & Zimmermann 2022; Harvey & Liu 2020; Gençay 2026; Osler 2000/2003/2005; Garzarelli et al. 2014; Chung & Bellotti 2021; TradingView help centre on back-adjustment (via search summary).

**Standard references cited from knowledge: unverified in this session (primary texts not opened)**
Welford 1962 (running variance); West 1979 (weighted incremental variance); Jain & Chlamtac 1985 (P² quantiles); Robbins & Monro 1951 (stochastic approximation); Hampel 1974 and Rousseeuw & Croux 1993 (robust scale, Qn/Sn); Hosking 1990 (L-moments); Moors 1988 (octile kurtosis); Hill 1975 (tail index); Cont 2001 (stylised facts); Gopikrishnan et al. 1999 (cubic law); Lo & MacKinlay 1988 (variance ratio; also cited by the study); Fisher 1921 (z-transform); Epps 1979 (asynchronous correlation); Granger & Newbold 1974 and Phillips 1986 (spurious regression); Huber 1964; Theil 1950; Sen 1968; Siegel 1982; Wilson 1927; Brown, Cai & DasGupta 2001; Kish 1965 (design effect); Efron 1979; Künsch 1989; Politis & Romano 1994; Holm 1979; Benjamini & Hochberg 1995; Benjamini & Yekutieli 2001; Bailey & López de Prado 2012 (PSR) and 2014 (DSR, J. Portfolio Management 40(5)); Bailey, Borwein, López de Prado & Zhu 2014/2017 (PBO, MinBTL); Mertens 2002 and Lo 2002 (Sharpe-ratio standard errors); López de Prado 2018 (purging, embargo, uniqueness; also cited by the study); Hansen & Hodrick 1980 (overlapping-horizon HAC; cited by the study); Dawid 1984 (prequential; cited by the study); Gneiting & Raftery 2007 and Murphy 1973 (proper scores; cited by the study); Kupiec 1995 (coverage test); Cameron, Gelbach & Miller 2008 (few clusters; cited by the study); Duchi, Hazan & Singer 2011 (AdaGrad); Graepel et al. 2010 (adPredictor; method verified by the study, figures not).

**Access note:** in this session the Firecrawl credits were exhausted, and the hosts davidhbailey.com and en.wikipedia.org did not resolve (not on the session's network allowlist). GitHub API access to third-party repositories was not enabled. Formulas from those sources were therefore checked numerically (`verify_formulas.py`) instead of against the primary text.
