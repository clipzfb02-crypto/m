# Quant Probability of Touch (PoT): study for DOL Engine v2

Domain: first-passage / barrier-touch probability, race (two-barrier) probability, discrete-monitoring correction,
fat tails and jumps, OHLC volatility estimators, intraday seasonality and volatility time, volatility clustering,
empirical excursion surfaces, Bayesian blending, and calibration of touch probabilities.

Engine audited: `baseline_v2.pine` (line numbers below refer to it; identical to `/home/user/m/indicators/dol_engine.pine`).
Reproducible study code: `study/quant_pot_tools/` (`potlib.py`, `pot_eval.py`, `pot_stack.py`, `pot_vs2.py`,
`eta_race.py`, `verify_formulas.py`, `sim_drift.py`, `seas_profile.py`, `vif.py`; outputs `out_*.txt`).

---

## 0. Key findings (read this first)

1. **The engine's closed-form maths is correct.** `f_pot` (one-barrier reflection formula with drift), `f_race`
   (scale-function race) and `f_raceH` (finite-horizon race by eigen-expansion of the doubly-absorbed BM) were
   ported to Python and matched Monte Carlo within the expected discretisation bias (section 3.1). The overflow-safe
   `f_expPhi` and the Numerical-Recipes `erfc` (|rel err| < 1.2e-7) are sound.
2. **The inputs to that maths are the problem.** The analytic PoT uses `σ = ta.stdev(Δclose, 50)` and
   `μ = 0.5·ta.sma(Δclose, 50)` (lines 915-917). On 6 CME futures (≈1.2 M level-windows per horizon), this
   model is badly over-confident: calibration slope **0.66** (ideal 1.0) at H=30 on 5-min bars, and the drift term is
   the single largest error source. Removing the drift alone cuts log-loss **3.7%** (H=30) and **7.1%** (H=60).
   A pure random-walk simulation shows the same: the 0.5×50-bar drift raises log-loss by 5.4% and drags the
   calibration slope to 0.83 even when the true drift is exactly zero.
3. **The default "Empirical" model is well calibrated but has no resolution beyond distance.** Its ECE is 0.004,
   but its Brier score is no better than an oracle base-rate-per-distance table (BSS −0.4%). It knows *how far*,
   not *when* (time of day) or *in what volatility state*.
4. **Volatility time is the missing variable.** ES 5-min variance at the 09:30 ET bucket is **4.7×** the daily mean
   and **0.20×** at 23:30 ET (24× max/min; 4.9× in σ). A 50-bar σ (≈4 hours) straddles regimes. A range-based,
   seasonal, mean-reverting variance forecast over the next H bars (Andersen–Bollerslev multiplicative model)
   gives the analytic model real resolution: with a 2-parameter calibration it beats the oracle distance table by
   **+1.5% BSS (H=30)** and **+3.6% (H=60)** on 5-min data.
5. **Cheapest robust win: add a volatility-state dimension to the existing empirical surface.** Splitting `sUp/sDn`
   by a tercile of `q = σ_H,forecast / (ATR·√H)` with partial pooling lowered log-loss on **all 6 symbols at all 3
   horizons** (−1.1% / −1.8% / −2.5% at H = 12 / 30 / 60) while staying perfectly calibrated (ECE ≤ 0.004).
   A plain 6-bucket session split gets most of that gain; ATR14/ATR200 alone gets almost none.
6. **Races are martingale races.** On ≈28k decided races per cell, P(up level first) matched the driftless value
   b/(a+b) within 0.4–1.2 percentage points. For any continuous martingale this holds regardless of volatility
   clustering or seasonality (optional stopping). Drift in `f_invalidation` adds noise, not information.
7. **Timing (ETA) needs volatility time.** The constant-σ conditional-median ETA is *negatively* rank-correlated with
   the actual time-to-touch (−0.09); the vol-time ETA is positively correlated (+0.11 / +0.16 / +0.22 at 1 / 2 / 3 ATR).
8. **Close-based events need the BGK correction.** P(a bar *closes* beyond a level within H) is over-stated by the
   continuous formula (0.58 vs 0.45 realised); shifting the barrier by 0.5826·σ_bar (Broadie–Glasserman–Kou) cuts
   the log-loss by 6.3%. Touch events judged on highs/lows need *no* correction (the engine is right there).
9. **The displayed PoT is never graded.** The ledger stores `pBase` (random-level baseline) and `pRace` but not
   the PoT the user sees, so there is no reliability diagram, Brier score or recalibration of the headline number.

---

## 1. Concepts (definitions and parameters)

### 1.1 One-barrier first passage (touch) for Brownian motion with drift
Process X_t = μt + σW_t, start 0, barrier d > 0 (distance to the level's near edge), horizon h (bars).

  P(max_{s≤h} X_s ≥ d) = Φ((μh − d)/(σ√h)) + exp(2μd/σ²) · Φ((−μh − d)/(σ√h))

* Driftless: P = 2Φ(−d/(σ√h)) = erfc(d/(σ√(2h))): the "touch ≈ 2 × finish-beyond" rule (reflection principle).
  Practitioners (options desks) use it as "probability of touch ≈ 2 × delta".
* Volatility time: for a deterministic time-varying σ_t, replace σ²h by the integrated variance V = Σ σ_j² over the
  next h bars: P = 2Φ(−d/√V). This is exact for a Gaussian process with deterministic variance (time change).
* Parameters: d (price), σ (price per bar), μ (price per bar toward the level), h (bars).
* Edge cases: d ≤ 0 → 1; σ = 0 → 0 (or 1 if drift reaches d); large positive 2μd/σ² overflows unless computed in
  log space (the engine's `f_expPhi` does this).

### 1.2 Two-barrier race
Upper barrier +a (target), lower barrier −b (invalidation). With k = 2μ/σ²:

  P(+a before −b) = (1 − e^{kb}) / (e^{−ka} − e^{kb});  driftless limit b/(a+b).

* **Martingale invariance**: for *any* continuous martingale (stochastic volatility, seasonality, clustering
  included), optional stopping gives P(+a first) = b/(a+b) exactly. Only drift, mean reversion and jumps
  (overshoot) move it. This makes the race the most model-robust probability the engine can display.
* Finite horizon (P(+a first AND before h)): eigen-expansion of BM absorbed at both ends. Shifting to y = x + b on
  (0, L), L = a+b, the flux through +a after h is
  tail(h) = e^{μa/σ²} Σ_n (σ² nπ/L²)(−1)^{n+1} sin(nπb/L) e^{−(λ_n+ν)h}/(λ_n+ν),
  λ_n = σ²n²π²/(2L²), ν = μ²/(2σ²); P_h = P_∞ − tail(h). Terms needed: n ≈ L/(πσ)·√(80/h) for e^{−40} truncation.

### 1.3 Time to touch (ETA)
First-passage time T of driftless BM to d: P(T ≤ t) = 2Φ(−d/(σ√t)) (Lévy distribution; infinite mean, mode d²/(3σ²)).
With drift: inverse Gaussian density f(t) = d/(σ√(2πt³))·exp(−(d−μt)²/(2σ²t)).
Conditional on touching within h, the median ETA t₅₀ solves 2Φ(−d/(σ√t)) = ½·2Φ(−d/(σ√h)). In volatility time,
replace σ²t by the cumulative forecast variance V(t) and invert on the bar grid.

### 1.4 Discrete monitoring (Broadie–Glasserman–Kou continuity correction)
If a barrier is only *checked at discrete times* spaced Δt (e.g. bar closes), the continuous formula over-states
the hit probability. BGK (1997): price with the continuous formula after shifting the barrier away from the start
by β·σ·√Δt, **β = −ζ(1/2)/√(2π) ≈ 0.5826**. For bars, Δt = 1 bar, so d_close = d + 0.5826·σ_bar.
* Applies to: "close beyond the level" events (body-close BOS, iFVG inversion by close, candle-body breaks).
* Does **not** apply to touches judged with highs and lows: the bar extreme is (approximately) the continuous path
  maximum, so the continuous formula is the right one for liquidity sweeps.

### 1.5 Fat tails, stochastic volatility and jumps
* Volatility mixture: if σ is random, PoT(d) = E_σ[2Φ(−d/(σ√h))]. The function is concave in σ for near levels
  and convex for far ones, so a mixture makes near levels *less* likely and far levels *more* likely than a
  Gaussian with the same average variance. Perelló, Gutiérrez-Roig & Masoliver (2011) found exactly this on
  tick data of six futures: the Wiener model under-estimates first-passage probability for x ≳ σ_t and
  over-estimates it for x ≲ 0.1σ_t, and scaling x by the horizon σ collapses all markets/horizons onto one curve.
* Jumps: overshoot at the barrier; Kou–Wang (2003) solve first passage for double-exponential jump diffusions
  (memoryless overshoot). For touch probability at intraday horizons the vol-mixture effect dominates; jumps matter
  for "how far past the pool" (sweep depth) and gap bars.
* Stop cascades: Osler (2005) shows stop-loss orders produce price cascades once levels are crossed (positive
  feedback), a micro-structural source of the fat tails right at liquidity levels.

### 1.6 OHLC volatility estimators (per bar, price units or log units)
| Estimator | Per-bar variance proxy | Efficiency vs close-to-close | Assumptions |
|---|---|---|---|
| Close-to-close | (C − C₋₁)² | 1 | none |
| Parkinson (1980) | (H − L)² / (4 ln 2) | ≈5.2 (4.9 also quoted) | zero drift, no gaps, continuous |
| Garman–Klass (1980) | ½(H − L)² − (2 ln 2 − 1)(C − O)² | ≈7.4 | zero drift, no gaps |
| Rogers–Satchell (1991) | (H − C)(H − O) + (L − C)(L − O) | ≈6 | drift-independent, no gaps |
| Yang–Zhang (2000) | σ_o² + kσ_c² + (1 − k)σ_RS², k = 0.34/(1.34 + (n+1)/(n−1)) | up to 14 (n = 2), ≈7.2–8.2 at n = 20 | drift- and gap-robust |

Known biases: discreteness (tick size) biases the range down; bid-ask bounce biases it up; drift biases
Parkinson/GK up; gaps (session opens, contract rolls) must be added back (gap² term or YZ). On our data the
mean bar range is 1.39–1.48 × σ_cc versus 1.596 for BM, mainly a Jensen effect of strongly varying σ
(E[σ] < √E[σ²]).

### 1.7 Intraday seasonality and volatility time
Andersen & Bollerslev (1997): r_{t,n} = σ_t · s_n · Z_{t,n} / √N, with s_n a periodic intraday factor (normalised
Σ s_n²/N = 1) estimated by bucket means or a Flexible Fourier Form. S&P 500 futures: average absolute 5-min return
0.095% in the morning → 0.055% at noon → 0.105% at the close (U-shape). FX: overlapping regional U-shapes.
Crypto: activity, volatility and illiquidity peak around 16:00–17:00 UTC, trough near 05:00 UTC.
**Volatility time**: forecast the horizon variance as V_H = Σ_{j=1..H} s²_{b(t+j)} · L_{t+j|t}, where L is the
deseasonalised level forecast. A level H bars away "at the NY open" is far more reachable than the same distance
at 23:30 ET.

### 1.8 Volatility clustering (EWMA / GARCH-lite / HAR)
* EWMA: σ²_t = λσ²_{t−1} + (1−λ)r²_{t−1}; RiskMetrics λ = 0.94 (daily), 0.97 (monthly).
* GARCH-lite term structure: E[σ²_{t+j}] = L̄ + φ^j(σ²_t − L̄) (persistence φ); horizon-average variance
  L̄ + (σ²_t − L̄)(1 − φ^H)/(H(1 − φ)). Implemented here as a fast EWMA level (half-life 30 bars) mean-reverting to a
  slow EWMA (≈5 days).
* HAR-RV (Corsi 2009): next RV ≈ c + β_d RV_d + β_w RV_w + β_m RV_m (1, 5, 22 days); captures long memory.
* Our data: deseasonalised log-range autocorrelation on ES 5-min is 0.63 (lag 1), 0.49 (1 hour), 0.34 (6.5 h),
  0.27 (1 day): strong, long-memory clustering.

### 1.9 Drift and short-horizon predictability
Short-horizon return predictability is tiny: the best-known intraday effect (first half-hour predicts last
half-hour on SPY) has R² = 1.6% (2.6% with the 12th half-hour). The sample mean of n = 50 bar changes has
standard error σ/√50; plugged into an H-bar first-passage formula with weight w the standardised barrier shifts
by w·√(H/50)·Z, i.e. 0.39·Z at the engine defaults (H = 30, w = 0.5) and 0.55·Z at H = 60. That is noise of the
same order as the signal the PoT is meant to carry.

### 1.10 Variance ratio (Lo–MacKinlay 1988)
VR(q) = Var(r_t + … + r_{t−q+1}) / (q·Var(r_t)) ≈ 1 + 2Σ_{j<q}(1 − j/q)ρ_j. VR < 1 means mean reversion (far
levels less reachable than √H scaling implies), VR > 1 trending. Our data at q = 30–60 bars: ES 0.96, NQ 1.02–1.05,
CL 1.00–1.03, GC 0.84–0.87, YM 0.91–0.94: near 1 overall, so √H scaling is acceptable; per-symbol deviation is
absorbed by the empirical surface.

### 1.11 Empirical excursion surfaces (MFE/MAE)
MFE/MAE (Sweeney 1997): the maximum favourable / adverse excursion of a position. The engine's surface is the
unconditional version: for each closed window of H bars, the up-excursion (max high − start close) and
down-excursion, normalised by ATR, bucketed (0.25 ATR steps) and counted per HTF regime. The survival function
S(u) = #windows with excursion ≥ u is the empirical PoT. Overlapping windows are serially dependent: the variance
inflation factor (VIF) of the touch indicator measured on ES/CL 5-min is 6–32, i.e. **0.21–0.83 × H** (higher for far
levels, lower for longer H). The engine's effective-sample divisor 0.6·H sits inside that range.

### 1.12 Bayesian blending and partial pooling
Beta-binomial: with prior mean p₀ and strength m pseudo-observations, posterior mean (k + m·p₀)/(n + m). Partial
pooling (empirical Bayes, Efron–Morris 1975) shrinks sparse cells toward their parent; in the baseball example it
cut total squared prediction error from 17.56 to 5.01. For a hierarchical surface: p_cell = (n_cell·p̂_cell +
m·p_parent)/(n_cell + m), with p_parent blended with the analytic prior in turn.

### 1.13 Calibration and proper scoring
* Brier score B = mean (p − y)²; log-loss LL = −mean[y ln p + (1−y) ln(1−p)]. Both are proper scores.
* Murphy decomposition: B = REL − RES + UNC with REL = Σ(n_k/N)(P_k − ō_k)², RES = Σ(n_k/N)(ō_k − ō)²,
  UNC = ō(1 − ō). REL is the miscalibration; RES is the discrimination.
* Reliability diagram: 10 probability bins, mean forecast vs observed rate. ECE = Σ(n_k/N)|P_k − ō_k|.
* Recalibration: Platt scaling p' = σ(a + b·logit p) (2 parameters, good for < 1000 samples); isotonic regression
  (PAV) is better above ≈1000 samples (Niculescu-Mizil & Caruana 2005). Calibration slope b < 1 means
  over-confident forecasts.
* Brier skill score versus a reference: BSS = 1 − B/B_ref. A meaningful reference for touch probabilities is the
  base rate *per distance bucket* (which every reasonable model already knows).

### 1.14 Liquidity levels versus random levels
* Osler (2003, 2005): stop-loss and take-profit orders cluster at round numbers; take-profits reverse trends,
  stop-losses accelerate them once crossed ("price cascades").
* Garzarelli et al. (2014): bounce probability at detected support/resistance levels is above 0.5 and above
  shuffled-return series, and rises with the number of previous bounces (LSE stocks, 45–90 s scales).
* Chung & Bellotti (2021): on 2018 minute data (EURUSD, LLOY, BRENT) bounce probability rises with prior
  bounces; with 1 prior bounce it decays to 0.5 at ≈350-minute lag windows, with 4 prior bounces at ≈900 minutes.
* Implication for PoT: the engine's PoT is a *random-level* probability at the target's distance. Real pools may
  be hit more often (magnets) or less (rejections). The ledger's EDGE statistic measures exactly that difference,
  but the displayed PoT never uses it.

### 1.15 Volume / transaction clock
Clark (1973) modelled cotton-futures prices as BM subordinated to cumulative volume; Ané & Geman (2000) argued the
trade-count clock restores near-normality. Murphy & Izzeldin's replication disputes the "near-normal" claim. Use:
volume or trade counts can serve as the activity clock where available. The seasonal volatility clock in this
report is the more robust, data-light version of the same idea.

---

## 2. Evidence

### 2.1 Literature (numbers and sources)
| Claim | Number | Grade | Source |
|---|---|---|---|
| BGK correction constant | β = −ζ(½)/√(2π) ≈ 0.5826 | strong | Broadie, Glasserman, Kou (1997) Math. Finance 7(4) |
| Parkinson / GK / RS / YZ efficiency | 5.2 / 7.4 / ≈6 / up to 14 (7.2–8.2 at n=20) | strong | Parkinson 1980; Garman–Klass 1980; Yang–Zhang 2000; summaries in TTR docs, portfoliooptimizer.io, flashalpha |
| Range-based SV estimation is far more efficient; log range ≈ Gaussian | qualitative + large efficiency gains | strong | Alizadeh, Brandt, Diebold (2002) J. Finance 57(3) |
| Intraday U-shape, S&P futures | |r| 0.095% → 0.055% → 0.105% | strong | Andersen & Bollerslev (1997) J. Empirical Finance |
| Nikkei 5-min U/double-U; periodic ACF distortion; FFF filter | |r| 0.11% → ~0.06% → 0.14% | strong | Andersen, Bollerslev, Cai (2000) |
| Crypto intraday peak | 16:00–17:00 UTC peak, ≈05:00 UTC trough | moderate | Quantpedia summary; "The crypto world trades at tea time" (Rev. Quant. Fin. Acc. 2024) |
| EWMA decay | λ = 0.94 daily, 0.97 monthly | strong (industry standard) | RiskMetrics Technical Document (1996) |
| HAR-RV long memory | daily/weekly/monthly cascade | strong | Corsi (2009) J. Fin. Econometrics |
| Intraday predictability is small | R² = 1.6% (2.6% with 12th half-hour) | strong | Gao, Han, Li, Zhou (2018) J. Fin. Econ. 129(2) |
| Wiener model misprices FPT: low for x ≳ σ_t, high for x ≲ 0.1σ_t; σ-scaling collapses markets | qualitative, 6 futures, tick data | strong | Perelló, Gutiérrez-Roig, Masoliver (2011) arXiv:1107.1174 |
| GARCH/Heston fit hitting-time PDFs better than GBM | qualitative | moderate | Valenti, Spagnolo, Bonanno (2006) arXiv:physics/0608201 |
| Stop/take-profit clustering explains S/R reversals and breakouts | ~9,700 orders at a dealing bank | strong | Osler (2003) J. Finance 58(5); Osler (2005) JIMF 24(2) |
| S/R bounce probability rises with prior bounces | p(b) > 0.5 vs ≈0.5 shuffled | moderate | Garzarelli et al. (2014) Sci. Rep.; Chung & Bellotti (2021) arXiv:2101.07410 |
| Calibration methods | Platt better < ~1000 samples; isotonic ≥ 1000 | strong | Niculescu-Mizil & Caruana (2005) ICML |
| Brier decomposition | REL − RES + UNC | strong | Murphy (1973); Siegert (2017) QJRMS |
| Shrinkage | total sq. error 17.56 → 5.01 | strong | Efron & Morris (1975) JASA |
| Variance ratio test | VR(q) definition, heteroskedasticity-robust z* | strong | Lo & MacKinlay (1988) RFS |

### 2.2 Our own tests (moderate evidence: reproducible, 2026 sample, CME futures only)
**Data**: CME ES, NQ, CL, GC, RTY, YM. 5-min bars (resampled from 1-min where needed) 2026-01-20 → 2026-04-15
(≈16.8k bars per symbol); 1-hour bars 2025-03 → 2026-04 (≈6.3k); 1-min ES/NQ/CL (≈84k). Data folder:
`study/amt_data/cme/` (from the AMT study). GC 1-hour contains contract-roll gaps (mean range / σ_cc = 0.44,
VR = 0.2) and is unreliable for any gap-sensitive estimator.

**Design** (`pot_eval.py`): at every bar t (after warm-up), levels at k ∈ {0.5, 1, 1.5, 2, 3, 4, 6} × ATR(14, RMA)
above and below the close; outcome y = 1 if max(high[t+1..t+H]) > close + d (strict, like the engine's liquidity
touch) or the mirror for lows. All model estimates are causal (expanding / rolling / online, using only windows
that had resolved before t). Metrics: Brier, log-loss (LL), ECE (10 bins), calibration intercept/slope (logistic
regression of y on logit p), BSS versus an **in-sample oracle** base rate per (symbol, side, k), which is a
deliberately hard reference.

**Models**
| Code | Model |
|---|---|
| p_eng_an | Engine analytic: f_pot(d, stdev(Δclose,50), 0.5·mean(Δclose,50)), capped 0.95 |
| p_cc0 | Same σ, no drift |
| p_yz / p_gkE | Yang–Zhang (50) / EWMA(hl 25) of GK + gap², driftless |
| p_scc | Seasonal vol-time with close-to-close² as the variance proxy |
| p_ns | Range-based level + mean reversion, **no** seasonality |
| p_cl | Seasonality with a flat long-run level (no clustering) |
| p_srng | Seasonal × clustering vol-time, range-based (GK + gap²): V_H = Σ s²_b(t+j)·[L_slow + φ^j(L_fast − L_slow)] |
| p_srng_cal | p_srng + online Platt recalibration (refit every 250 bars on resolved windows) |
| p_eng_emp | Engine default: ATR-normalised empirical surface blended with p_eng_an (m = 30, nEff = n/(0.6H)), capped 0.95 (no HTF regime split: not available offline) |
| p_emp_std | Empirical surface on σ_H-standardised distance, prior p_srng |
| p_emp_vs | Engine surface + vol-state tercile split (q = √V_H/(ATR√H)), partial pooling to the engine value |
| p_stack | Online logistic stack of logit(p_eng_emp) and logit(p_srng) |

**Results, 5-min, 6 symbols, ≈1.2 M rows per horizon** (oracle base-rate LL: 0.5007 / 0.5621 / 0.5583)

| Model | H=12 LL | H=30 LL | H=30 Brier | H=30 ECE | H=30 slope | H=30 BSS vs oracle | H=60 LL | H=60 BSS |
|---|---|---|---|---|---|---|---|---|
| p_eng_an (engine analytic) | 0.5470 | 0.6115 | 0.2063 | 0.058 | **0.66** | −8.7% | 0.6220 | −11.6% |
| p_cc0 (no drift) | 0.5401 | 0.5891 | 0.1989 | 0.042 | 0.76 | −4.8% | 0.5776 | −3.9% |
| p_yz | 0.5361 | 0.5875 | 0.1990 | 0.048 | 0.79 | −4.8% | 0.5776 | −4.0% |
| p_ns (no seasonality) | 0.5419 | 0.5899 | 0.2011 | 0.081 | 0.87 | −5.9% | 0.5710 | −2.3% |
| p_cl (no clustering) | 0.5616 | 0.6003 | 0.2014 | 0.086 | 0.74 | −6.1% | 0.5734 | −1.3% |
| p_srng (seasonal × clustering) | 0.5142 | 0.5659 | 0.1907 | 0.062 | 0.89 | −0.5% | 0.5533 | +1.8% |
| p_srng_cal | 0.5042 | 0.5557 | 0.1870 | 0.024 | 1.01 | +1.5% | 0.5438 | +3.6% |
| **p_eng_emp (engine default)** | 0.5016 | 0.5639 | 0.1905 | **0.004** | 0.99 | −0.4% | 0.5617 | −0.7% |
| p_emp_std | 0.5031 | 0.5561 | 0.1870 | 0.025 | 0.95 | +1.5% | 0.5455 | +3.4% |
| **p_emp_vs** | **0.4962** | 0.5538 | 0.1866 | **0.003** | 0.98 | +1.7% | 0.5477 | +2.5% |
| p_stack | **0.4947** | **0.5503** | **0.1851** | 0.014 | 1.00 | **+2.5%** | **0.5412** | **+4.1%** |

Per-symbol LL, H=30: engine empirical → p_emp_vs → p_stack: CL 0.5634 → 0.5589 → 0.5597; ES 0.5615 → 0.5513 →
0.5477; GC 0.5546 → 0.5530 → 0.5504; NQ 0.5599 → 0.5487 → 0.5425; RTY 0.5688 → 0.5540 → 0.5509; YM 0.5735 → 0.5570
→ 0.5510. **p_emp_vs improves every symbol at every horizon.**

Which conditioning state carries the gain (`pot_vs2.py`, mean LL over 6 symbols):
| H | engine surface | + vol-time tercile | + ATR14/ATR200 tercile | + 6 × 4-hour UTC session |
|---|---|---|---|---|
| 12 | 0.5015 | **0.4962** | 0.5016 | 0.4961 |
| 30 | 0.5636 | **0.5538** | 0.5622 | 0.5561 |
| 60 | 0.5614 | **0.5478** | 0.5577 | 0.5518 |

The time-of-day component carries most of the gain; ATR14/ATR200 (vol compression/expansion) adds little on its own.

**1-hour bars** (Day-Trading execution TF; GC rows contaminated by roll gaps):
* H=12: engine analytic LL 0.5657, no-drift 0.5527, engine empirical 0.5268, p_emp_vs **0.5086** (ES 0.5210 →
  0.5030), p_stack 0.5077.
* H=30 (30 hours, more than a day): engine empirical 0.5587, p_emp_vs **0.5558** (better on 5 of 6), vol-time
  analytic alone 0.5649 (worse: at > 1 day the seasonal component averages out and the GC gaps hurt), p_stack
  0.5596 (hurt by GC). Robust choice = p_emp_vs.

**1-min bars, H=30 (a 30-minute clock horizon)**: engine analytic 0.5848, no drift 0.5613, engine empirical
**0.5517**, vol-time calibrated 0.5570. At clock horizons well under an hour, ATR(14) already measures the
current level and seasonality hardly changes inside the window: **vol-time pays off when H × timeframe spans a
material part of the daily cycle (≥ ~1–2 hours)**. Drift removal helps at every scale.
The vol-state split of the surface still helps at 1-min (0.5517 → 0.5484, all 3 symbols; see 2.2.1).

**Drift simulation** (`sim_drift.py`, driftless random walk, 20 sub-steps per bar, H = 30, levels at 0.25–2 horizon σ):
| Model | Brier | LL | slope |
|---|---|---|---|
| true σ, no drift | 0.1548 | 0.4742 | 0.99 |
| σ₅₀, no drift | 0.1559 | 0.4785 | 0.95 |
| σ₅₀, drift 0.5·mean₅₀ (engine) | 0.1642 | 0.5041 | 0.83 |
| σ₅₀, drift 1.0·mean₅₀ | 0.1871 | 0.5809 | 0.57 |

**Formula verification** (`verify_formulas.py`; Monte Carlo with 200 sub-steps per unit time, which under-states
continuous hits by ≈0.041σ of barrier shift):
| a, b, σ, μ, h | f_raceH(A) / MC | f_raceH(B) / MC | f_pot(a) / MC |
|---|---|---|---|
| 2, 2, 1, 0, 4 | 0.3146 / 0.3025 | 0.3146 / 0.3111 | 0.3173 / 0.3051 |
| 3, 1.5, 1, 0.1, 9 | 0.3590 / 0.3573 | 0.5136 / 0.5055 | 0.4183 / 0.4102 |
| 1, 4, 1, −0.2, 16 | 0.6101 / 0.5956 | 0.3579 / 0.3675 | 0.6220 / 0.6061 |
| 5, 5, 1, 0, 30 | 0.3551 / 0.3546 | 0.3551 / 0.3514 | 0.3613 / 0.3600 |
| 4, 2, 1, 0.3, 10 | 0.4976 / 0.4942 | 0.2443 / 0.2357 | 0.5239 / 0.5169 |

**Race = martingale** (`eta_race.py`, 5-min, H = 60, 6 symbols, same-bar ties dropped):
| a (ATR) | b (ATR) | n | empirical P(up first) | b/(a+b) |
|---|---|---|---|---|
| 1 | 1 | 28,098 | 0.493 | 0.500 |
| 1 | 2 | 28,160 | 0.658 | 0.667 |
| 1 | 3 | 27,849 | 0.746 | 0.750 |
| 2 | 1 | 28,141 | 0.324 | 0.333 |
| 2 | 2 | 27,546 | 0.488 | 0.500 |
| 3 | 1 | 27,772 | 0.239 | 0.250 |

**ETA** (5-min, H = 60, conditional median of time-to-touch among hits):
| k (ATR) | n hits | share T ≤ t₅₀ const-σ | share T ≤ t₅₀ vol-time | rank corr const-σ | rank corr vol-time | median abs log error const / vol-time |
|---|---|---|---|---|---|---|
| 1 | 23,748 | 0.396 | 0.470 | −0.092 | **+0.108** | 0.915 / 0.847 |
| 2 | 19,230 | 0.438 | 0.446 | −0.090 | **+0.155** | 0.803 / 0.747 |
| 3 | 15,322 | 0.473 | 0.455 | −0.098 | **+0.219** | 0.671 / 0.601 |

**Close-beyond (BGK)**, outcome = a bar *closes* beyond the level within H; model uses σ_bar = √(V_H/H):
| TF, H | realised rate | continuous formula (mean p, LL) | BGK-shifted (mean p, LL) |
|---|---|---|---|
| 5-min, 12 | 0.295 | 0.423, 0.542 | 0.344, **0.495** |
| 5-min, 30 | 0.453 | 0.583, 0.626 | 0.517, **0.586** |
| 5-min, 60 | 0.574 | 0.693, 0.630 | 0.641, **0.598** |
| 1-hour, 12 | 0.314 | 0.445, 0.558 | 0.363, **0.507** |
| 1-min, 30 | 0.462 | 0.578, 0.618 | 0.513, **0.583** |
(The remaining bias is the same upward bias the uncalibrated vol-time touch model has; calibration removes it.)

**Seasonality** (`seas_profile.py`, 5-min Parkinson variance relative to the same day's mean, by 30-min ET bucket):
ES 09:30 = 4.67×, 10:00 = 3.57×, 10:30 = 2.75×; 23:30 = 0.20× (max/min 24×, σ ratio 4.9×). NQ 09:30 = 6.17×.
CL 09:30 = 2.17×, 18:00 (reopen) = 1.94×, min 0.21× (10.5×). GC max/min 6.7×.

**Overlap VIF** (`vif.py`): touch-indicator VIF / H = 0.50–0.71 (H=12), 0.32–0.83 (H=30), 0.21–0.53 (H=60).

#### 2.2.1 1-min vol-state / stack results (H = 30, ES/NQ/CL, 3.37 M rows)
| Model | Brier | LL | ECE | slope | BSS vs oracle |
|---|---|---|---|---|---|
| p_eng_emp (engine) | 0.1854 | 0.5517 | 0.005 | 1.01 | −0.1% |
| p_srng_cal | 0.1875 | 0.5570 | 0.012 | 1.00 | −1.2% |
| p_emp_vs | 0.1842 | 0.5484 | 0.006 | 1.00 | +0.6% |
| p_stack | 0.1837 | 0.5473 | 0.006 | 1.00 | +0.9% |
Per symbol (engine → p_emp_vs): CL 0.5601 → 0.5574, ES 0.5479 → 0.5443, NQ 0.5473 → 0.5437. Even at a 30-minute
clock horizon, where the stand-alone vol-time analytic loses, the vol-state split of the surface still helps every
symbol. Across 5-min (H 12/30/60), 1-hour (H 12/30, 5 of 6 at H=30) and 1-min (H 30), p_emp_vs is the only
variant that never lost to the engine on a clean symbol.

---

## 3. Engine gap analysis (line references in baseline_v2.pine)

### 3.1 Audit of the PoT code
| Item | Lines | Verdict | Notes |
|---|---|---|---|
| `f_erfcLog`/`f_erfc`/`f_phi` | 407-418 | correct | Numerical Recipes erfc, frac. err < 1.2e-7 |
| `f_expPhi` (log-space e^e·Φ(b)) | 420-429 | correct | prevents overflow of the reflection term |
| `f_pot` one-barrier with drift | 434-444 | correct maths; **cap inside** | returns min(0.95, p); the cap then leaks into scoring and the baseline (see W3) |
| `f_race` | 447-462 | correct | scale-function formula and driftless limit b/(a+b) |
| `f_raceH` finite-horizon race | 466-482 | correct (MC-verified) | term count from e^{−40} truncation, cap 400 terms; `exp(min(50, μa/σ² − …))` can clip only with extreme drift (irrelevant once drift is removed) |
| `potSig = ta.stdev(chg, 50)` | 915-916 | **weak** | close-to-close, equal weights, no seasonality, includes the unclosed bar live |
| `potMu = ta.sma(chg, 50)·driftW` | 917 | **wrong (harmful)** | noise ≈0.39 standardised-barrier sd at defaults; worsens LL by 3.7–7.1% on data and 5.4% in simulation |
| Proximity reach uses `f_pot(dist, sig, mu·side, potH)/0.95` | 665 | partial / wrong | inherits drift noise (directional double-counting with the Draw pillar) and the cap; no volatility time |
| Empirical surface `sUp/sDn` (3 regimes × 61 bins) | 1059-1062, 1265-1300, 1526-1532 | present, well calibrated | ATR(14)-normalised at window start; conditions only on HTF regime; no time-of-day / vol state |
| Overlap-adjusted nEff = n/(0.6H) | 1308 | present, OK | measured VIF/H 0.21–0.83; 0.6 is a reasonable conservative constant |
| Bayesian blend with analytic prior (priorM = 30) | 1303-1311 | present | correct beta-binomial form; prior carries the drift noise |
| Beyond-grid fallback (u > NB → analytic) | 1292-1293 | partial | Gaussian analytic under-states far-tail touches (Perelló et al.; our k = 6 rows: 0.118 vs 0.150 realised) |
| `f_potBase` random-level baseline | 1314-1322 | partial | uses capped, drift-free `f_pot` → baseline biased low for very near targets (a near target's true base rate ≈0.97–1.0 but the analytic part is capped at 0.95) |
| `f_reachD` reach bands | 1325-1338 | present | fine; would inherit vol-state conditioning |
| `f_invalidation` race WIN≤H with drift | 1343-1364 | partial | maths correct, but drift should be zero (martingale evidence); vol should be vol-time |
| `f_raceAdj` ledger logit shift for races | 1367-1373 | present, good | the same idea is missing for PoT |
| Ledger `Trial` | 375-391, 1426-1430 | **missing piece** | no `pPot` field → the displayed PoT is never graded (no Brier, reliability, or recalibration) |
| ETA | 2116-2126 | partial | median bars-to-hit of past hits within ±0.5 ATR; ignores time of day and vol state; no quantiles |
| Live PoT | 2065-2067 | partial | live, as intended; uses full H although part of the current bar has elapsed; `sweptNow ? 0.95` fine |
| Close-beyond probability (BGK) | none | missing | needed for body-close breaks / sweep-vs-break split |
| "Which pool is taken next" race | none (only target-vs-invalidation) | missing | nearest BSL vs nearest SSL race is the purest "next liquidity" forecast |
| Strict ">" for liquidity touch vs "≥" in surface counting | 625, 1265-1270 | negligible | grid steps are 0.25 ATR |

### 3.2 Concept status summary
| Concept | Status |
|---|---|
| Reflection-principle PoT with drift | present (maths correct) |
| Two-barrier race, finite horizon | present (maths correct) |
| Martingale (driftless) race | partial (drift added) |
| Discrete-monitoring (BGK) correction | n/a for touches (correctly absent); missing for close-based events |
| Range-based volatility (Parkinson/GK/RS/YZ) | missing (close-to-close stdev) |
| Intraday seasonality / volatility time | missing (killzone multipliers exist for scoring, not for PoT) |
| Volatility clustering forecast (EWMA/GARCH term structure) | missing (flat 50-bar window) |
| Drift estimation | wrong (raw 50-bar mean) |
| Fat tails / stochastic-vol mixture | partial (empirical surface captures it inside the grid; analytic fallback does not) |
| Empirical excursion surface | present |
| Overlap-aware effective sample size | present |
| Bayesian blend of model and empirical | present |
| Partial pooling across conditioning cells | missing (single level of conditioning) |
| Calibration of displayed PoT (Brier/reliability/Platt) | missing |
| Time-to-touch distribution (ETA quantiles) | partial |
| 95% cap | wrong placement (should be display-only) |

---

## 4. Proposals (best first; max 10)

Notation: `chartS` = chart seconds (line 308), `H` (line 305), `atr` (874), `NB/NB1/bStep` (303-307).
All state updates run inside `if barstate.isconfirmed` (non-repainting); live readouts reuse the last confirmed
forecasts. Pine v6 rule to remember: a function cannot `:=` a *global scalar*; keep mutable statistics in `var`
arrays (the engine already does this with `raceSt`, `stN` …).

### QPOT-01 · Remove the raw drift from every analytic probability (P1, effort S)
**Problem.** `potMu = ta.sma(chg, 50)·driftW` (917) enters PoT (1304, 2067, 2184), proximity reach (665) and the
race (1361-1363). The 50-bar mean has SE σ/√50; at defaults it shifts the standardised barrier by ≈0.39·Z.
**Change.** Use μ = 0 in `f_pot`, `f_raceH`, `f_potModel` and `evaluate`. Directional information already reaches
the PoT through the regime-split empirical surface (`htfBias` rows) and reaches selection through the Draw
pillar (weight 30). Keep an optional, *learned* tilt: `f_raceAdj` (ledger) for races, and QPOT-04 for PoT.
If a drift input is kept for experts, default it to 0 and shrink it: μ_eff = μ̂·max(0, 1 − (σ²/n)/μ̂²) (positive-part
James–Stein).
**Pine.** `float potMu = 0.0` (or `driftW` default 0.0, line 185); in `evaluate` call `f_pot(dist, sig, 0.0, potH)`.
**Evidence.** 5-min LL 0.6115 → 0.5891 (H=30), 0.6220 → 0.5776 (H=60); 1-hour 0.6154 → 0.5835 (H=30); 1-min
0.5848 → 0.5613; simulation +5.4% LL from drift on a driftless walk; races match b/(a+b) within ≤1.2 pp.
**Ledger.** EDGE and race Brier should not degrade; PoT calibration slope (QPOT-04) should move toward 1.
**Risk.** Slightly slower reaction in strong trends (handled by the regime surface and Draw pillar).

### QPOT-02 · Volatility-time horizon variance V_H (range-based, seasonal, mean-reverting) (P1, effort M)
**Algorithm.**
1. Per-bar variance proxy (price units): `x = max(0, ½(H−L)² − (2ln2−1)(C−O)²) + (O − C[1])²` (GK + gap),
   winsorised at 25 × slow level (roll gaps, bad prints).
2. Seasonal buckets: `binSec = max(900, chartS)`; seasonality only when `timeframe.isintraday and chartS < 14400`;
   `NBK = 86400 / binSec` (96 on ≤15-min charts, 24 on 1H). Bucket `b = (hour(time,"UTC")·3600 + minute(time,"UTC")·60) / binSec`.
3. Slow level R (EWMA, half-life `hlS = min(2000, 5·86400/chartS)` bars); bucket accumulators `sSum[b] += x/R`,
   `sCnt[b] += 1`; maintain Σ of bucket means and the seen-bucket count incrementally;
   `s²_b = mean_b / mean_of_means` (1.0 if unseen).
4. Deseasonalised levels: `Lf = EWMA(x/s²_b, hl 30)`, `Ls = EWMA(x/s²_b, hlS)`; `φ = 0.5^(1/30)`.
5. Forecast path: walk future bars j = 1..H on the clock (`time + j·chartS·1000`), skip buckets never traded
   (`sCnt = 0`), accumulate `V(j) = Σ s²_b(j) · (Ls + φ^j (Lf − Ls))`; keep the cumulative array (used by QPOT-05/07).
6. Analytic PoT = `2Φ(−d/√V_H)` = `f_erfc(d / math.sqrt(2·V_H))`; proximity reach uses the same (uncapped).
**Pine sketch.**
```
// INPUTS (G_POT)
string volModel = input.string("Vol-time", "PoT Volatility", options = ["Vol-time", "Close-to-close"], group = G_POT)
int    vtHL     = input.int(30, "Vol Level Half-Life (bars)", minval = 5, maxval = 500, group = G_POT)
// derived constants (after line 308)
bool  seasOn = timeframe.isintraday and chartS < 14400
int   binSec = int(math.max(900.0, chartS))
int   NBK    = seasOn ? int(86400 / binSec) : 1
float hlS    = math.min(2000.0, 5.0 * 86400.0 / chartS)
// SERIES (after line 917)
float xVarRaw = math.max(0.0, 0.5 * math.pow(high - low, 2) - (2.0 * math.log(2.0) - 1.0) * math.pow(close - open, 2)) + math.pow(open - nz(close[1], open), 2)
int   bkt     = seasOn ? int((hour(time, "UTC") * 3600 + minute(time, "UTC") * 60) / binSec) % NBK : 0
// STATE (after line 1080): vtSt = [R, Lf, Ls, mSum, mSeen]
var array<float> sSum = array.new<float>(NBK, 0.0)
var array<int>   sCnt = array.new<int>(NBK, 0)
var array<float> vtSt = array.from(na, na, na, 0.0, 0.0)
var array<float> vCum = array.new<float>(H, na)   // cumulative forecast variance, refreshed per confirmed bar
// helpers (STATE HELPERS): f_s2(b), f_vtUpdate(), f_vtPath() → fills vCum; loop bound H + 2·NBK·ceil(binSec/chartS)
```
Cost: one loop of ≤ H + 2·NBK·(binSec/chartS) light iterations per confirmed bar (≤ ~2,000 on 1-min with H = 450;
well inside the 500 ms loop limit). Memory < 1k floats.
**Evidence.** Analytic LL 0.6115 → 0.5659 (5-min, H=30) and BSS vs oracle −8.7% → −0.5% before calibration;
with QPOT-04-style calibration +1.5% (H=30), +3.6% (H=60); 1-hour H=12 +2.7%. Literature: Andersen–Bollerslev
(1997), Alizadeh–Brandt–Diebold (2002), Perelló et al. (2011). Grade: strong (concept) / moderate (our test).
**Caveats.** Gains are largest when H × timeframe ≥ 1–2 hours; at a 30-minute clock horizon (1-min, H=30) the
engine's ATR-based surface is already better. Weekend/holiday buckets are approximated. Keep the close-to-close
option for daily+ charts.

### QPOT-03 · Volatility-state dimension in the empirical surface, with partial pooling (P1, effort M)
**Algorithm.** State `vs ∈ {0,1,2}` from `q = √V_H / (atr·√H)`: maintain an EWMA mean m and sd s of ln q
(half-life ≈ 2000 bars); `vs = ln q < m − 0.43s ? 0 : ln q > m + 0.43s ? 2 : 1` (normal terciles, O(1)).
Fallback without QPOT-02: `vs` = 4-hour UTC session bucket (6 states), which recovered most of the gain.
Rows become `r = regime·3 + vs` (9 rows per side; 2 × 9 × 61 = 1,098 ints). Bump with `vs[H]` (state at window
start) like `htfBias[H]` (1530). Read: cell estimate p_c from row r; parent p_p = pooled over the 3 vs rows of the
regime (today's estimate); `p = (nE_c·p_c + m·p_p)/(nE_c + m)` with nE = n/(0.6H) and m = 30; then the existing
analytic blend.
**Pine.** `var array<int> sUp = array.new<int>(9 * NB1, 0)`; in `f_empPoT` compute both cell and parent sums
(parent = Σ of the three rows' counts, 3 extra `get`s per call). `vsSer` is a series int so `vsSer[H]` is valid.
**Evidence.** LL 0.5015 → 0.4962 (H=12), 0.5636 → 0.5538 (H=30), 0.5614 → 0.5478 (H=60), every one of 6 symbols
improves, ECE stays ≤ 0.004; 1-hour H=12 ES 0.5210 → 0.5030 (all 6 symbols better, mean 0.5268 → 0.5086);
1-min H=30 0.5517 → 0.5484 (all 3 symbols). Grade: moderate.
**Risk.** Slower warm-up per cell (pooling handles it); `nMin` gate should apply to the parent.

### QPOT-04 · Grade and recalibrate the displayed PoT in the ledger (P1, effort M)
**Algorithm.**
* Add `float pPot` to `Trial` (375-391); set it in `f_openTrial` (1426) to the PoT shown at that bar close.
* In `f_book` (1461) accumulate for family g and ALL: Σ(p−y)², Σ log-loss, and 10 reliability bins
  (`rbN`, `rbP`, `rbY` arrays). Brier skill vs `pBase`: BSS = 1 − Σ(p−y)²/Σ(pBase−y)².
* Online Platt (2 params) in a `var array<float> calW = array.from(0.0, 1.0, 0.0)` [a, b, n]:
  `x = logit(p)`, `z = σ(a + b·x)`, `η = 1/(30 + n)`, `a += η(y − z)`, `b += η(y − z)x`, clamp a ∈ [−1.5, 1.5],
  b ∈ [0.5, 1.5]; apply when n ≥ 30. Equivalent intercept-only option (exact, like `f_raceAdj`):
  `δ = logit((K + m·P̄)/(N + m)) − logit(P̄)`, m = 20.
* Display: "PoT 64% (cal 58%)"; Terminal accuracy row "PoT CAL · Brier .201 vs base .215 · slope 0.92 · n 140";
  Full view shows the 10-bin reliability strip.
**Why.** This turns the headline number into a self-checking forecast and folds the engine's measured EDGE (selected
pools versus random levels) into the PoT the trader sees.
**Evidence.** Platt on the vol-time analytic: slope 0.89 → 1.01, ECE 0.062 → 0.024, LL 0.5659 → 0.5557 (5-min,
H=30). Literature: Platt 1999; Niculescu-Mizil & Caruana 2005; Murphy 1973. Grade: strong.
**Risk.** Trials overlap (cluster) → small effective n; use the cluster-robust block idea already in `cluSt` and a
conservative η.

### QPOT-05 · Volatility-time ETA and "PoT this session" (P2, effort M)
**Algorithm.** From `vCum` (QPOT-02): touch CDF `F(j) = 2Φ(−d/√V(j))`; conditional CDF `F(j)/F(H)`;
ETA50 = first j with ratio ≥ 0.5, ETA80 likewise. Clock label `time + ETA50·chartS·1000` (skip closed buckets as
in the path walk). "PoT this session": V to the session end (e.g. 17:00 ET for CME, 00:00 UTC for crypto) →
`2Φ(−d/√V_eod)`. With drift 0 the per-level cost is a binary search over H floats.
**Ledger.** For hits store T and ETA50: coverage = share with T ≤ ETA50 (target 0.50) and rank correlation;
show "ETA cov 48%".
**Evidence.** Rank corr(T, ETA) −0.09 (const σ) vs +0.11 / +0.16 / +0.22 (vol-time) at 1/2/3 ATR; coverage
0.45–0.47 vs 0.40–0.47. Grade: moderate.
**Risk.** Small for hit-conditional ETA; label "≈" because of weekend/holiday buckets.

### QPOT-06 · "Next liquidity taken" race readout (P2, effort S)
**Algorithm.** Nearest unswept liquidity above (distance a) and below (b) in `pool` (kind ≤ 1). Model:
`p_up = f_raceH(a, b, σ_eff, 0, H)/(f_raceH(a,b,…) + f_raceH(b,a,…))`, σ_eff = √(V_H/H), which is ≈ b/(a+b).
Ledger tilt: separate `var array<float> nxSt` [n, upWins, Σp] fed by one open record at a time (opened at bar
close on a new pair, resolved when either pool is swept); logit shift exactly as `f_raceAdj`.
Display: "NEXT ▲ BSL 62% · ▼ SSL 38%" in the Terminal panel; optional alert when one side ≥ 70%.
**Value.** The literal answer to "which liquidity is taken next", model-robust (martingale), and testable: any
deviation from b/(a+b) the ledger finds is genuine liquidity "magnetism" (Osler-type effects) for this symbol.
**Evidence.** Martingale identity (strong theory); data: ≤1.2 pp deviation on random levels (moderate).

### QPOT-07 · BGK close-beyond probability: "sweep vs break" (P2, effort S)
**Algorithm.** `P_close(d) = 2Φ(−(d + 0.5826·σ_bar)/√V_H)`, σ_bar = √(V_H/H). Show for liquidity targets
"PoT 71% · close-thru 52%"; `P_touch − P_close` is the chance of a wick-only raid within H (an upper bound on
sweep-and-reject). Can also drive the expectation for body-close breaks in the bias logic.
**Evidence.** Continuous formula over-states close-beyond (0.583 vs 0.453 realised, 5-min H=30); BGK 0.517, LL
0.626 → 0.586; same pattern on 1-hour (0.558 → 0.507) and 1-min (0.618 → 0.583). BGK (1997). Grade: strong
(theory) / moderate (data).
**Risk.** Inherits the vol-time level bias; calibrate with the same Platt layer.

### QPOT-08 · Adaptive stacked PoT (online logistic of empirical + vol-time) (P3, effort M)
**Algorithm.** Every confirmed bar, for 7 fixed distances × 2 sides, store `[logit p_emp, logit p_vt]` in a ring
buffer of H+1 rows (≤ 451 × 28 floats); when a window resolves, take an AdaGrad step on 3 weights. Display PoT =
σ(w₀ + w₁·logit p_emp + w₂·logit p_vt) once ≥ 3,000 samples, else the surface.
**Evidence.** Best LL in the 5-min test (0.5503 at H=30, 0.5412 at H=60; BSS +2.5% / +4.1%), learned weights favour
vol-time on equity indices (0.66–0.86) and the surface on CL/GC; on corrupted data (GC 1-hour roll gaps) it was
worse than the plain surface. Grade: moderate.
**Risk.** Fragile on bad data; keep as an option behind QPOT-03.

### QPOT-09 · Consistency fixes: cap placement, live remaining time, far-tail fallback (P3, effort S)
* Return uncapped probabilities from `f_pot`/`f_potModel`; apply the 95% cap only when displaying
  (`activePoT`, HUD, alert text, `minPoT` filter). Use the uncapped value in `evaluate` (drop the `/0.95`) and
  `f_potBase` (removes the low bias of the near-target baseline in the EDGE test).
* Live bar: horizon `H − 1 + (time_close − timenow)/(time_close − time)` on realtime bars (bounded to [H−1, H]).
* Beyond the grid (u > NB, line 1292): use a two-component variance mixture
  `p = ½·2Φ(−d/(0.8σ_H)) + ½·2Φ(−d/(1.17σ_H))` (same mean variance, ≈ kurtosis 3.4) or simply widen `bStep`; the
  Gaussian under-states far touches.
* Winsorise the variance proxy (QPOT-02 step 1) so contract rolls do not poison the forecasts.

---

## 5. Sources
* Broadie, M., Glasserman, P., Kou, S. (1997). A continuity correction for discrete barrier options. Mathematical
  Finance 7(4), 325–349. https://www.columbia.edu/~sk75/mfBGK.pdf ; summary: https://almostsuremath.com/2023/07/01/discrete-barrier-approximations/
* Reflection principle / probability of touch: https://quant.stackexchange.com/questions/235/probability-of-touching ;
  https://www.mathfinance.com/wp-content/uploads/2024/11/2023-05-Quick-And-Dirty.pdf ; https://optionstradingiq.com/probability-of-touch/
* First-passage time, inverse Gaussian: https://arxiv.org/html/2306.17656v3 ; https://en.wikipedia.org/wiki/First-hitting-time_model
* Range estimators: https://search.r-project.org/CRAN/refmans/TTR/html/volatility.html ;
  https://portfoliooptimizer.io/blog/range-based-volatility-estimators-overview-and-examples-of-usage/ ;
  https://flashalpha.com/articles/yang-zhang-vs-close-to-close-realized-volatility ;
  https://ocw.mit.edu/courses/18-642-topics-in-mathematics-with-applications-in-finance-fall-2024/mit18_642_f24_lec17_2.pdf
* Alizadeh, Brandt, Diebold (2002). Range-based estimation of stochastic volatility models. J. Finance 57(3).
  https://onlinelibrary.wiley.com/doi/10.1111/1540-6261.00454
* Martens & van Dijk (2007). Measuring volatility with the realized range. J. Econometrics 138(1).
  https://ideas.repec.org/a/eee/econom/v138y2007i1p181-207.html
* Andersen & Bollerslev (1997). Intraday periodicity and volatility persistence. https://finance.martinsewell.com/stylized-facts/volatility/AndersenBollerslev1997b.pdf
* Andersen, Bollerslev, Cai (2000). Intraday and interday volatility in the Japanese stock market. https://public.econ.duke.edu/~boller/Published_Papers/jifmim_00.pdf
* Crypto seasonality: https://quantpedia.com/periodicity-in-cryptocurrencies-recurrent-patterns-in-volatility-and-volume/ ;
  https://link.springer.com/article/10.1007/s11156-024-01304-1 ; https://www.sciencedirect.com/science/article/pii/S1059056024006506
* RiskMetrics Technical Document (1996). https://www.msci.com/documents/10199/5915b101-4206-4ba0-aee2-3449d5c7e95a
* Corsi (2009). HAR-RV. https://statmath.wu.ac.at/~hauser/LVs/FinEtricsQF/References/Corsi2009JFinEtrics_LMmodelRealizedVola.pdf
* Gao, Han, Li, Zhou (2018). Market intraday momentum. J. Fin. Econ. 129(2). https://www.sciencedirect.com/science/article/abs/pii/S0304405X18301351
* Lo & MacKinlay (1988). Variance ratio test. https://rodneywhitecenter.wharton.upenn.edu/wp-content/uploads/2014/04/8729.pdf
* Perelló, Gutiérrez-Roig, Masoliver (2011). Scaling and universality of first-passage probabilities. arXiv:1107.1174
* Valenti, Spagnolo, Bonanno (2006). Hitting time distributions in financial markets. arXiv:physics/0608201
* Kou & Wang (2003). First passage times of a jump diffusion process. http://www.columbia.edu/~sk75/KouWangAAP.pdf
* Osler (2003). Currency orders and exchange-rate dynamics. https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr125.pdf ;
  Osler (2005). Stop-loss orders and price cascades. https://faculty.georgetown.edu/evansm1/New%20Micro/osler1.pdf
* Garzarelli, Cristelli, Zaccaria, Pietronero (2011/2014). Memory effects in stock price dynamics. arXiv:1110.5197
* Chung & Bellotti (2021). Evidence and behaviour of support and resistance levels. arXiv:2101.07410
* Niculescu-Mizil & Caruana (2005). Predicting good probabilities with supervised learning. https://www.cs.cornell.edu/~alexn/papers/calibration.icml05.crc.rev3.pdf ;
  https://scikit-learn.org/stable/modules/calibration.html
* Murphy (1973) decomposition via Siegert (2017). https://ore.exeter.ac.uk/articles/journal_contribution/Simplifying_and_generalising_Murphy_s_Brier_score_decomposition/29748851/1/files/56771708.pdf
* Efron & Morris (1975). Data analysis using Stein's estimator. https://jhanley.biostat.mcgill.ca/bios602/MultilevelData/EfronMorrisJASA1975.pdf
* Overlapping observations: https://quantmemo.com/concepts/overlapping-returns-and-the-hansen-hodrick-correction
* Clark (1973), Ané & Geman (2000) and critique: https://ideas.repec.org/a/bla/jfinan/v55y2000i5p2259-2284.html ; https://www.lancaster.ac.uk/staff/izzeldin/AG.pdf
* MAE/MFE (Sweeney 1997): https://audacity.capital/trading-guides/maximum-adverse-excursion/
* Pine v6 limits (local mirror): `docsrc/jabez4jc_pinescriptv6/writing_scripts/limitations.md` (loop 500 ms per bar;
  collections ≤ 100,000 elements); `reference/time.md` (`hour(time, timezone)`, `minute(time, timezone)`, `time_close`, `timenow`).
