# Regime detection for the DOL engine: trend vs range vs breakout, and what it changes about which liquidity is taken

Domain: market-regime classification (Kaufman efficiency ratio, ADX/DMI, Choppiness Index, Hurst exponent, variance ratio,
volatility compression and expansion (NR4/NR7, Bollinger/TTM squeeze, ATR ratios), realised vs implied volatility,
time-series momentum and short-term reversal), and exactly how a regime should modulate the engine's draw vector D,
PoT drift, counter-draw logic and pool scoring.

Engine audited: `brief/baseline_v2.pine` (line numbers below; identical to `indicators/dol_engine.pine`).
Reproducible study code and outputs: `study/quant_regime_tools/` (section 6). Every number tagged **[this study]** comes from it.
Sibling studies referenced, not repeated: `quant_pot.md` (QPOT-01..09), `bias_dol.md` (BIAS-1..7), `wyckoff_sd.md` (WYK-1..5),
`ict_struct.md`, `ict_time.md` (TIME-1..9), `orderflow_micro.md` (OF-1..8).

---

## 0. Key findings (read this first)

1. **Trend/range regime labels are not a persistent state at the DOL horizons.**
   - ER(20), CHOP(14) and a rolling Hurst exponent measured on one window have about zero correlation with the same measure on the next non-overlapping window.
     - ER: −0.04 to +0.01 on real data, −0.03 to +0.03 on a sign-flip null.
     - CHOP: −0.13 to −0.00 real, about +0.02 null.
     - Hurst: −0.08 to +0.01 real.
     - Tested on 5m, 15m, 1H and daily, 23 series.
   - The classic thresholds fire about as often on a direction-free random walk as on real prices:
     - ER20 ≥ 0.40: 17-22% real vs 18-22% null (intraday; 14% daily).
     - ADX ≥ 25: 42-50% real vs 35-49% null.
     - CHOP ≤ 38.2: 14-20% real vs 14-18% null.
     - Hurst > 0.55: 8-19% real vs 14-22% null. **[this study]**
   - **Volatility state is persistent:** corr(ln ATR14/ATR100 at t, at t+14) = 0.49-0.80, and corr of the 20-bar log range with the next 20 bars = 0.58-0.80.
   - **Implication: a trend/range label describes the window that just ended. A volatility label forecasts the next one.**
2. **The trend regime does not change WHICH side is taken beyond race geometry.**
   - Setup: the nearest unswept pivot pool above vs below, within 0.25-4 ATR, first pass within K bars (K = 30 intraday, 10 daily).
   - Adding signed ER, ER×direction, Safari–Schmidhuber trend strength φ and φ³, EMA distance or +DI−−DI to the gambler's-ruin logit **never improves out-of-sample log-loss beyond ±0.25%**. It is worse by 0.2-1.0% in most cells (8,027 / 13,231 / 6,107 / 3,027 decided races on 1H / 5m / 15m / D).
   - The sign-flip null gives the same picture. **[this study]**
3. **"In a trend the draw continues" is mostly geometry.**
   - In an efficient trend (ER20 ≥ 0.40) price sits near the trend's leading edge, so ruin geometry already points to the with-trend pool **76-82%** of the time. The mean P(with-trend first) is 0.62-0.65.
   - The sign-flip null gives the same (78-83%). The folklore is right about the outcome and wrong about the cause. **[this study]**
4. **An engine-like structure-vote D used to choose the side costs 9-12 pp of first-touch accuracy intraday, and 5 pp daily.**
   - Geometry scores 0.645-0.706. D-first scores 0.550-0.652. Hit within K drops 5-8 pp intraday and 3 pp daily.
   - **Gating D by efficiency (use D only when ER20 ≥ 0.40 and D agrees with the ER direction) recovers geometry to within 0.2 pp.**
   - Gating by ADX ≥ 25 still loses 2.5-3.5 pp. **[this study, `regime_dgate.py`]**
5. **PoT drift hurts in every regime, including efficient trends.**
   - Setup: the analytic touch probability with the engine's drift (0.5 × SMA50 of Δclose, line 917) vs zero drift.
   - Log-loss ER≥0.40: 1H 0.614 vs 0.590, 5m 0.694 vs 0.669, 15m 0.686 vs 0.653, D 0.504 vs 0.503 (tie).
   - All bars: +1.2-4.0% worse with drift. Turning drift on only in "trend regime" does not rescue it. This independently confirms QPOT-01. **[this study]**
6. **Ranges do not make both sides more likely to be raided. Volatility compression does.**
   - Distance-matched P(both pools taken within K) does not rise with low ER or high CHOP.
     - 1H: high-CHOP 0.436 vs low-CHOP 0.540, the opposite of the folklore.
     - 5m: flat.
     - 15m: replicated by the null.
     - D: high-CHOP 0.28 ± 0.06 vs low 0.13 ± 0.04 (n = 139 each), yet adding CHOP to the full logit worsens OOS log-loss by 3.2%. Inconclusive.
   - Compressed volatility (ATR5/ATR100 low, or a low Bollinger-width percentile) raises P(both) and ATR-scaled reach on 15m and 1H.
     - OOS log-loss for P(both): −0.97% (1H), −2.95% (15m).
     - Reach ≥ 3 ATR: 0.50 → 0.39 from compressed to expanded tercile on 1H, 0.46 → 0.33 on 15m.
     - The effect is **absent on 5m**, where session seasonality dominates (see QPOT-02/03, TIME-1).
   - The direction-free null reproduces the effect. It is vol clustering plus mean reversion measured in ATR(14) units: real, robust, and direction-free. **[this study]**
7. **Sweeps: no regime makes "raid holds → continuation, raid rejects → reversal" true.**
   - After a pool is traded through, the symmetric ±1 ATR race from the close is 0.497-0.510 for hold and reject alike on 5m/15m/1H. The engine's `liqEvt` (1579-1582) encodes the rule anyway (BIAS-4 agrees).
   - Daily is the only exception: continuation 0.539 ± 0.016 vs null 0.497.
   - 5m sweeps aligned with an efficient trend continue more: 0.538 ± 0.014 vs null 0.487 ± 0.010. That does not replicate on 15m (0.542 vs 0.538 null) or 1H (0.521 vs 0.514). Weak. **[this study]**
8. **Counter-trend pools in efficient trends are touched a little less than a random level at the same distance**, a weak effect.
   - 1H: −6.7 ± 2.7 pp vs null −1.5. D: −6.7 ± 4.1 vs null −1.7. 15m and 5m: about 0.
   - That supports at most a mild, regime-scoped counter-draw penalty (about ×0.85), not the current ×0.50 applied whenever |D| ≥ 0.35. **[this study]**
9. **Rolling Hurst / variance-ratio classifiers are noise at chartable windows.**
   - With q = 4 and 96 bars, the Lo–MacKinlay asymptotic SE of VR is about 0.19, so the implied Hurst SE is about 0.07.
   - A random walk is labelled "persistent" (H > 0.55) 20-22% of the time and "anti-persistent" (H < 0.45) 35-38% of the time.
   - The literature agrees: R/S is biased in short samples (Kristoufek 2012), and VR tests cannot reject a random walk for FX, commodities or crypto (arXiv 2606.29591, 2610.11028).
10. **External evidence points the same way at intraday horizons.** Short-term trend-following died after 2009 on small-tick contracts (equity index and FX futures; ~100 futures, Sharpe 0.84 → 0.12 for the fastest signal; Kurth, Eisler, Rej, Bouchaud 2026). Zero of 160 foundation-model cells beat a no-change forecast at 5-120 min on ES/NQ (arXiv 2611.12141). Zero of 14 OHLCV intraday-momentum families pass walk-forward on MNQ (arXiv 2605.04004). Trends persist on average from about 30 minutes to a few years, but the coefficients are small and strong trends revert (Safari & Schmidhuber 2025). Time-series momentum is strong at 1-12 months (Moskowitz, Ooi & Pedersen 2012), which is outside the DOL horizon.

**Design consequence.**
- A cheap two-axis classifier is worth having:
  - an **E axis** (signed efficiency, for gating and honest reporting);
  - a **V axis** (volatility compression/expansion, for probability).
- It should *gate* the draw vector, *scope* the counter-draw penalty, *key* the empirical PoT surface on volatility instead of HTF bias, and *split* the ledger so the user sees per-regime accuracy.
- It must not re-introduce drift, ADX/Hurst thresholds, or range bonuses for pools.

---

## 1. Concepts (precise definitions and parameters)

Notation: bar t has O, H, L, C. TR_t = max(H_t, C_{t−1}) − min(L_t, C_{t−1}). RMA = Wilder smoothing (α = 1/n). Every regime measure is computed on closed bars (≤ t) and used at the close of t.

### 1.1 Kaufman efficiency ratio (ER)
- **Definition.** ER_n = |C_t − C_{t−n}| / Σ_{i=t−n+1..t} |C_i − C_{i−1}|, in [0, 1]. Signed version: sER_n = (C_t − C_{t−n}) / Σ|ΔC| ∈ [−1, 1]. Kaufman's adaptive moving average uses n = 10 and maps ER into a smoothing constant between fast = 2 and slow = 30 (Kaufman, *Trading Systems and Methods*).
- **Practitioner use.**
  - ER ≥ 0.4-0.6 counts as "trending" and ER < 0.2-0.3 as "choppy".
  - Some scripts rank ER against its own history (above the median = gate open, bottom quartile = strong chop) rather than using absolute cutoffs.
- **Random-walk behaviour** (derived; Gaussian i.i.d. increments): E|ΔC| = σ√(2/π) and |ΣΔC| = σ√n|Z|, so ER_n ≈ |Z|·√(π/(2n)).
  - For n = 20, ER ≈ 0.280|Z|, the mean is about 0.22, and P(ER ≥ 0.40) ≈ P(|Z| ≥ 1.43) ≈ 15%.
  - With fat tails and vol clustering, the sign-flip null gives 18-22% on 5m/15m/1H. An "ER ≥ 0.4 trend" label therefore fires on about 1 bar in 5 of pure noise.
- **Edge cases.**
  - The path sum is 0 on flat data. Guard the division.
  - Gaps count in the path; use close-to-close, not open-to-close.
  - ER is direction-free; use sER for direction.

### 1.2 ADX / DMI (Wilder 1978)
- **Definition.**
  - +DM = H_t − H_{t−1} if that move is greater than L_{t−1} − L_t and greater than 0, else 0.
  - −DM is the mirror image.
  - +DI = 100·RMA(+DM, 14)/RMA(TR, 14), and −DI likewise.
  - DX = 100·|+DI − −DI| / (+DI + −DI).
  - ADX = RMA(DX, 14).
- **Use.** ADX > 25 = trend and ADX < 20 = no trend; +DI > −DI gives the direction. Often used as a filter on breakout systems.
- **Facts.**
  - ADX's double RMA gives it about 27 bars of memory: corr(ADX_t, ADX_{t+28}) ≈ 0.2 on real and null data alike.
  - On a direction-free null with real bar ranges, ADX ≥ 25 holds on 35-49% of bars **[this study]**, so the "25" threshold is mostly a noise threshold at n = 14.
- **Evidence for filtering.**
  - One Donchian trend-following test found the ADX filter added no value (oxfordstrat).
  - A 22-ticker blog test found gains came from skipping choppy periods, not from better trades inside trends (algolab 2026).
  - The "ADX > 40 → 73% continuation" claims circulating online could not be traced to a primary source.

### 1.3 Choppiness Index (E. W. Dreiss)
- **Definition.** CHOP_n = 100 · log10( Σ_{n} TR / (HH_n − LL_n) ) / log10(n), with n = 14 by default.
  - Above 61.8 = choppy/range. Below 38.2 = trending. These are Fibonacci conventions, not statistics.
- **Random-walk value** (derived). The expected bar range and the expected n-bar range of Brownian motion scale with the same constant (≈1.596σ√Δt), so ΣTR/(HH−LL) ≈ √n and **CHOP ≈ 50 for a random walk**, exactly between the bands.
- **Engine relation.** The engine's `coilScore` (886-891) is a CHOP-like overlap ratio: Σ range over 20 bars / 20-bar range, mapped as (x − 2)/4.

### 1.4 Hurst exponent and variance ratio
- **Hurst H.** Var(r_q) ∝ q^{2H}. H = 0.5 is a random walk, H > 0.5 is persistent (trending), H < 0.5 is anti-persistent (mean-reverting).
  - Estimators: rescaled range R/S, DFA, generalised Hurst, and the aggregated-variance / variance-ratio slope.
- **Variance ratio (Lo & MacKinlay 1988).**
  - VR(q) = Var(q-bar returns) / (q · Var(1-bar returns)). For a random walk VR = 1, and VR(q) ≈ q^{2H−1}, so H ≈ 0.5 + ln VR / (2 ln q).
  - Under a homoskedastic null, the asymptotic Var(VR) = 2(2q−1)(q−1)/(3qT). For q = 4, T = 96 the SE is ≈ 0.19, so the Hurst SE is ≈ 0.07.
  - The heteroskedasticity-robust z* should be used.
- **Behaviour in this study.**
  - The rolling VR-Hurst (q = 4, w = 96) averages 0.47-0.48 on real and null data alike, a small-sample downward bias.
  - It labels a random walk H > 0.55 20-22% of the time and H < 0.45 35-38% of the time.
  - Its next-window correlation is about 0.
- **Literature.**
  - R/S is biased upward for short-range-dependent series (Kristoufek 2012).
  - The generalised-Hurst estimator has the lowest variance (Barunik & Kristoufek 2012).
  - A local Hurst exponent is strongly time-scale-dependent in futures (Bartolozzi et al. 2007).

### 1.5 Volatility compression → expansion
- **NR4/NR7 (Crabel 1990).** Today's range H − L is the smallest of the last 4/7 bars. An inside bar is H_t ≤ H_{t−1} and L_t ≥ L_{t−1}. Trade the break of the narrow bar's extreme.
- **Bollinger squeeze.** BandWidth = 4σ_20/SMA_20 at a 6-month (≈120-bar) low, or in a low percentile of its own history.
- **TTM Squeeze (J. Carter).** "On" when BB(20, 2σ) lies inside the Keltner channel (20, 1.5×ATR20). With a common basis this is 2σ_20 < 1.5·ATR_20. "Fires" when the bands move back outside. A momentum histogram supplies the direction. The Pro variant uses KC 1.0 / 1.5 / 2.0 to grade compression.
- **ATR ratio.** volr = ATR(5)/ATR(100), or ln(ATR_fast/ATR_slow) z-scored against its own EWMA.
- **What is true.**
  - Volatility clusters and mean-reverts (the HAR model of Corsi 2009 captures it with daily, weekly and monthly lags).
  - So after compression, the *absolute* next range is smaller than average (sibling `bias_dol.md` 2.8: NR7 next range > median only 26-45%), but the next H bars travel *more ATR(14) units* than average.
  - Expansion is the mirror image.
- **What is not supported.** Any directional content of the squeeze. Squeeze/NR states add nothing to which-side-first [this study, O1].

### 1.6 Realised vs implied volatility (variance risk premium)
- **Definition.** VRP = IV² − E[RV²], e.g. VIX² vs realised 5-min variance. The ratio RV/IV > 1 marks stress regimes.
- **Evidence.** The VRP predicts equity index returns at monthly-quarterly horizons (Bollerslev, Tauchen & Zhou 2009). It is not documented at DOL (intraday) horizons.
- **Pine.** Needs an implied-vol symbol (CBOE:VIX for SPX/ES/NQ only). It is not generic and needs one more `request.security`.

### 1.7 Time-series momentum and short-term reversal
- **TSMOM (Moskowitz, Ooi & Pedersen 2012, JFE 104(2)).**
  - sign(past 12-month excess return) predicts the next month across 58 liquid futures.
  - It persists for 1-12 months and partially reverses beyond a year.
- **Fast trend after 2009 (Kurth, Eisler, Rej & Bouchaud 2026, arXiv 2607.01550).**
  - Fast trend signals (EWMA 5/20 to 50/200 days) had Sharpe 0.84-0.70 in 1995-2009 and 0.12-0.40 in 2009-2025.
  - On small-tick contracts (equity indices, FX) post-2008 trend PnL "completely degraded", while large-tick contracts (bonds, most commodities) kept Sharpe 1.0-1.2.
  - Trends are more profitable in low-volatility periods (the LeBaron effect).
- **Trend strength by scale (Safari & Schmidhuber 2025, arXiv 2501.16772; 14 years of futures tick data, 30 years daily).**
  - Below about 15-30 minutes, weak trends revert (tick-size reversion plus more).
  - From about 30 minutes to a few hours the linear term turns positive. Above a few hours it beats tick-size reversion.
  - From a few hours to years, weak trends persist and strong trends revert (linear b > 0, cubic c < 0). The coefficients are "small".
  - Trend strength φ_T is the weighted sum of normalised returns with Σw² = 1, so φ is in units of standard deviations.
- **Intraday momentum (Gao, Han, Li & Zhou 2018, JFE 129(2)).**
  - SPY's first half-hour return predicts the last half-hour: R² 1.6% in-sample, 1.2% out-of-sample, stronger on high-volatility and high-volume days.
  - Practical tests on MNQ 2021-25 find no OHLCV momentum family that survives costs and year-stability (arXiv 2605.04004; ORB long T = 0.88).
- **Short-term reversal.**
  - Sub-hour reversal is bid-ask bounce and temporary imbalance (Heston, Korajczyk & Sadka 2010).
  - SPY's lag-1 daily autocorrelation of −0.081 is magnitude-driven, not directional. Mean reversion is confined to equities and sovereign bonds. FX, commodities and crypto are indistinguishable from random walks (arXiv 2606.29591).
- **LeBaron effect.** Serial correlation is lower when *predictable* volatility is high and higher with *unexpected* volatility (Bianco, Corsi & Renò 2008, S&P futures intraday).

### 1.8 Statistical regime models
- **Markov switching (Hamilton 1989).** Latent states with their own mean and variance and a transition matrix.
- **Extensions.** Two-state MSR on volatility plus an adaptive MA for trend gives four states (Pomorski & Gorse 2022, arXiv 2208.11574). Wyckoff-like 4-state MS-AR (Srivastava & Bhattacharya 2018).
- **Evidence.** In-sample segmentations are convincing. Out-of-sample intraday directional value is not documented. A 2-state online filter in Pine is feasible (two Gaussians and a forward recursion) but buys nothing over the V axis below.

### 1.9 The DOL-specific regime claims (what traders say)
- **C1. "In trends, opposite-side liquidity holds and the draw continues."**
  - Used to prefer with-trend pools and penalise counter-trend ones. The engine's ×0.5 counter-draw penalty does this.
  - Test: O1/(c2)/(a) below.
- **C2. "In ranges, both sides get raided."** Used to expect stop runs at both range edges and to trade the edges. Test: O2/(c).
- **C3. "Compression precedes expansion; trade the break."** Test: O1/O2/O4 by volatility state.
- **C4. "A raid that holds is continuation; a raid that rejects is reversal"** (engine `liqEvt`, lines 1579-1582). Test: O3.

---

## 2. Evidence

### 2.1 Data and method [this study]

| Family | Series | Bars | Horizon K | Sampling |
|---|---|---|---|---|
| 1H | ES, RTY, YM (CME, 2025-03 → 2026-04), CL (2025-06 → 2026-04), NQ / GC / EURUSD (sibling hourly, ≈2024-11 → 2026-11), EURUSD 1H (2017-04 → 2018-02) | 4.5k-12.3k each, 63k total | 30 bars | every 3rd bar |
| 15m | ES, NQ, GC, CL, RTY, YM, resampled from CME 1-min, 2026-01-20 → 2026-04-15 | 4.8k-5.6k each | 30 | every 2nd |
| 5m | same six, resampled | ≈17k each | 30 | every 3rd |
| D | S&P 500, NASDAQ (1999-2018), GOOG (2004-2013) | 2.1k-5.0k | 10 | every bar |

- **Pools.** The nearest unswept confirmed pivot (length 5) above and below, swept on a strict trade-through as in the engine (`touched`, 623), both within 0.25-4 ATR(14).
- **Outcomes.**
  - First pass within K. A bar that takes both is "ambiguous" and dropped from first-touch rates.
  - Touch within K per side.
  - Max excursion in ATR.
- **Geometry.** P(up first) = b/(a+b), the driftless gambler's ruin. The engine has it as `f_race`, 447-464.
- **Null.** A sign-flip series (`rlib.null_series`): each real bar is rebuilt from the previous synthetic close with its own range and body, mirrored with probability ½. It keeps bar ranges, bodies and volatility clustering exactly and destroys any directional dependence. **Every regime effect must exceed the null to count.** Several naive with-trend statistics are non-zero on the null (e.g. daily ER/ADX "with-trend excess" +4-5 pp) from pivot and window mechanics.
- **Out-of-sample.** 2-fold time split (first half / second half per series); log-loss of the logit-geometry baseline vs baseline + regime feature(s).
- **SEs.** Cluster-robust by 100-bar block × series.

### 2.2 Regime labels are not persistent states (O0, `regime_persist.py`)

| Measure | 5m real / null | 15m real / null | 1H real / null | D real / null |
|---|---|---|---|---|
| P(ER20 ≥ 0.40) | 0.170 / 0.183 | 0.198 / 0.188 | 0.215 / 0.219 | 0.187 / 0.137 |
| P(ER20 < 0.15) | 0.379 / 0.372 | 0.353 / 0.362 | 0.346 / 0.342 | 0.350 / 0.421 |
| P(ADX ≥ 25) | 0.456 / 0.433 | 0.495 / 0.433 | 0.499 / 0.485 | 0.418 / 0.352 |
| P(CHOP ≤ 38.2) | 0.144 / 0.152 | 0.156 / 0.148 | 0.193 / 0.184 | 0.198 / 0.142 |
| P(CHOP ≥ 61.8) | 0.096 / 0.108 | 0.087 / 0.097 | 0.067 / 0.072 | 0.052 / 0.084 |
| P(Hurst > 0.55) | 0.186 / 0.212 | 0.188 / 0.219 | 0.188 / 0.205 | 0.084 / 0.136 |
| corr ER20(t), ER20(t+20) | −0.011 / +0.012 | +0.006 / −0.028 | −0.022 / +0.025 | −0.044 / +0.010 |
| corr sER20(t), sER20(t+20) | −0.000 / +0.009 | −0.009 / −0.008 | −0.034 / +0.002 | +0.014 / −0.071 |
| corr CHOP(t), CHOP(t+14) | −0.002 / +0.049 | −0.047 / +0.022 | −0.023 / +0.016 | −0.132 / +0.011 |
| corr Hurst(t), Hurst(t+96) | −0.014 / −0.020 | −0.082 / −0.044 | +0.014 / −0.006 | −0.041 / −0.080 |
| corr ln(ATR14/ATR100)(t, t+14) | 0.80 / 0.80 | 0.60 / 0.62 | 0.49 / 0.48 | 0.76 / 0.77 |
| corr ln Σrange20 (t, t+20) | 0.80 | 0.58 | 0.76 | 0.78 |

- **Reading.** Trend/range measures behave like those of a random walk with the same bar ranges. Daily equities show slightly more "trend" labels (index drift) and some CHOP anti-persistence (−0.13).
- Volatility persistence is preserved in the null *by construction* (same ranges). The point is its size (0.5-0.8) against ≈0 for trend measures.

### 2.3 Which side is taken first (O1, `regime_study.py`)

Out-of-sample log-loss change vs logit(geometry). Negative = the regime feature helps.

| Feature added | 1H | 5m | 15m | D |
|---|---|---|---|---|
| sER20 | +0.60% | +0.01% | +0.66% | +0.34% |
| sER20, sER20·ER20 | +0.59% | +0.01% | +0.66% | +0.35% |
| φ24, φ24³ (Safari–Schmidhuber form) | +0.21% | +0.08% | +0.26% | +1.00% |
| EMA50 distance (ATR) | +0.23% | −0.10% | +0.33% | −0.13% |
| (+DI − −DI)/50 | +0.30% | −0.24% | −0.25% | −0.11% |
| same features on the null | −0.06…+0.03% | −0.00…+0.02% | −0.06…+0.03% | −0.28…+0.09% |

- Geometry accuracy among decided races: 0.646 (1H), 0.673 (5m), 0.667 (15m), 0.706 (D).
- "With-trend excess" by regime gate. Excess = (y − p) × sign(sER20), real vs null:

| Gate | 1H real / null | 5m | 15m | D |
|---|---|---|---|---|
| ER20 ≥ 0.40 | **+0.061±0.025** / −0.004 | +0.006 / +0.011 | +0.052 / +0.058 | +0.105±0.060 / +0.054 |
| ER20 < 0.15 | +0.006 / +0.002 | −0.002 / −0.008 | +0.007 / −0.005 | +0.010 / +0.013 |
| ADX ≥ 25 | +0.003 / +0.002 | +0.023±0.010 / +0.003 | +0.001 / +0.012 | +0.065 / +0.045 |
| CHOP ≥ 61.8 | +0.025 / +0.010 | +0.007 / −0.014 | +0.024 / −0.025 | −0.006 / +0.020 |
| Hurst > 0.55 | +0.023 / +0.004 | +0.009 / +0.008 | +0.028 / +0.019 | −0.002 / +0.014 |

- Only one cell (1H, ER ≥ 0.4, n = 360) clears 2σ against its null, out of about 20 gates × 4 families. That is consistent with chance.

### 2.4 Engine-like side selection by regime (`regime_dgate.py`, `regime_engine.py`)

D proxy = 0.5·HTF + 0.3·STF + 0.2·chart internal pivot bias (the engine's sV, line 1892, with ×24/×4 blocks on 1H, ×48/×12 on 5m, ×16/×4 on 15m), gate 0.35. Below the gate, geometry decides.

| Rule | 5m acc / hit≤K | 15m | 1H | D |
|---|---|---|---|---|
| Geometry (nearer by ruin odds) | **0.672 / 0.661** | **0.666 / 0.643** | **0.645 / 0.655** | **0.706 / 0.486** |
| D-first (engine today) | 0.556 / 0.585 | 0.580 / 0.589 | 0.550 / 0.590 | 0.652 / 0.452 |
| D only if ER20 ≥ 0.40 and sign(D) = sign(sER20) | 0.671 / 0.661 | 0.665 / 0.642 | 0.643 / 0.654 | 0.706 / 0.486 |
| D only if ER20 ≥ 0.25 and agrees | 0.670 / 0.660 | 0.666 / 0.642 | 0.640 / 0.653 | 0.703 / 0.484 |
| D × soft gate g_E = clip((ER−0.25)/0.20) | 0.668 / 0.659 | 0.663 / 0.642 | 0.635 / 0.648 | 0.705 / 0.486 |
| D only if ADX ≥ 25 | 0.637 / 0.640 | 0.640 / 0.632 | 0.615 / 0.635 | 0.700 / 0.482 |
| Trend-first, sign(sER20), always | 0.580 / 0.598 | 0.587 / 0.593 | 0.576 / 0.603 | 0.613 / 0.426 |

- The null gives the same ordering (geometry 0.657-0.701; D-first 0.520-0.592). The loss is mechanical: choosing the farther pool.
- In efficient trends geometry already agrees with the trend 76-82% (null 78-83%) [`regime_form.py`]. That is why the ER gate costs almost nothing.

### 2.5 PoT drift by regime (`regime_engine.py` (b))

Analytic first-passage touch within K for both nearest pools, σ = stdev(Δclose, 50); engine drift μ = 0.5·SMA(Δclose, 50).

| Family | All bars: LL drift / no drift | ER ≥ 0.40: drift / none | ER < 0.15: drift / none |
|---|---|---|---|
| 5m | 0.6693 / **0.6544** | 0.6943 / **0.6689** | 0.6708 / **0.6576** |
| 15m | 0.6826 / **0.6691** | 0.6862 / **0.6527** | 0.6661 / **0.6601** |
| 1H | 0.6641 / **0.6389** | 0.6136 / **0.5902** | 0.6613 / **0.6435** |
| D | 0.5698 / **0.5631** | 0.5036 / 0.5033 | 0.5859 / **0.5822** |

- The sign(trend) × forward K-bar return (ATR) is not significant in any regime. ER ≥ 0.4: +0.31 ± 0.29 (1H), +0.05 ± 0.22 (5m), +0.24 ± 0.40 (15m, null +0.26), +0.46 ± 0.23 (D, null +0.23).

### 2.6 Both sides, reach and pool magnetism by regime (O2, O4, (c))

P(both pools taken within K), OOS log-loss change from adding one standardised regime feature to a distance logit:

| Feature | 1H real / null | 5m | 15m | D |
|---|---|---|---|---|
| ER20 | −0.00% / +0.00% | −0.01% / +0.00% | +0.00% / +0.03% | +1.25% / −0.05% |
| CHOP | −0.24% / −0.01% | +0.01% / +0.04% | −0.05% / −0.20% | +3.15% / +0.17% |
| ATR5/ATR100 | **−0.97% / −1.05%** | +0.06% / −0.15% | **−2.95% / −1.54%** | +0.20% / +0.63% |
| BB-width pct | −0.53% / −0.88% | +0.19% / +0.02% | −1.46% / −1.92% | −1.65% / +1.75% |

Reach ≥ d ATR within K (either direction), by tercile low/mid/high, with the OOS log-loss change of the tercile split:

| | 1H d=2 | 1H d=3 | 15m d=2 | 15m d=3 | 5m d=3 | D d=3 |
|---|---|---|---|---|---|---|
| ATR5/ATR100 | .64/.59/.55 (−0.32%) | .50/.43/.39 (−0.53%) | .60/.58/.48 (−0.81%) | .46/.45/.33 (−0.92%) | .40/.42/.38 (0.00%) | .22/.18/.19 (−0.09%) |
| ER20 | .60/.60/.59 (+0.01%) | .45/.45/.42 (−0.02%) | .55/.55/.55 | .41/.42/.41 | .41/.40/.39 | .22/.19/.19 (+0.16%) |

CHOP, ADX and Hurst are flat (|ΔLL| ≤ 0.17%) on every family.

Pool touch minus a random level at the same ATR distance (family excursion distribution):
- All regimes: −0.007 to +0.002.
- CHOP ≥ 61.8: −0.005 / −0.019 / −0.023 / +0.015 (5m / 15m / 1H / D) vs null +0.011 / +0.019 / −0.017 / −0.002. No range magnetism.
- Compressed (volr < 0.8): +0.002 / +0.032 / +0.035 / +0.032. Expanded (> 1.25): −0.036 / −0.104 / −0.064 / 0.000. The null is similar, which confirms a volatility effect.

Pool printed in a coiled vs an efficient window (engine `coilScore` and ER20 at the pivot bar, `regime_form.py`):
- High-coil tercile: −0.005 / −0.013 / −0.012 / −0.018. Null: −0.002 / −0.016 / −0.005 / −0.020. **No support for the coil term** in the density pillar (agrees with WYK-1).

With-trend vs counter-trend pool excess in efficient trends (ER ≥ 0.40):

| | 5m | 15m | 1H | D |
|---|---|---|---|---|
| with-trend real / null | −0.006 / +0.002 | +0.042 / −0.060 | +0.018 / +0.040 | +0.034 / +0.007 |
| counter-trend real / null | −0.002 / +0.002 | −0.018 / −0.007 | **−0.067±0.027 / −0.015** | **−0.067±0.041 / −0.017** |

### 2.7 After a sweep (O3)

Symmetric race ±1 ATR from the close of the sweep bar (martingale = 0.5):

| | 5m | 15m | 1H | D |
|---|---|---|---|---|
| all | 0.508 (null 0.500) | 0.509 (0.508) | 0.503 (0.494) | **0.539±0.016 (0.497)** |
| hold (close beyond) | 0.507 | 0.508 | 0.497 | 0.556 |
| reject (close back inside) | 0.510 | 0.510 | 0.509 | 0.516 |
| aligned with trend, ER ≥ 0.40 | **0.538±0.014 (null 0.487)** | 0.542 (0.538) | 0.521 (0.514) | 0.465 (0.472) |
| range (ER < 0.15) | 0.507 | 0.498 | 0.497 | 0.558 |

- Next same-side pool first vs ruin geometry: real excess +0.015 to +0.030 intraday vs null +0.010 to +0.024. Daily +0.066 vs +0.072. This is mostly mechanics.

### 2.8 External evidence table

| # | Claim | Source / data | Result | Grade |
|---|---|---|---|---|
| R1 | Trend vs reversion by time scale | Safari & Schmidhuber 2025, arXiv 2501.16772; 14 years futures tick, 30 years daily, monthly since 1692 | Reversion below about 15-30 min; trending from about 30 min (beats tick-size reversion above a few hours) to a few years; weak trends persist, strong revert; small coefficients | moderate-strong (large data, small effects) |
| R2 | Death of short-term trend on small-tick contracts | Kurth, Eisler, Rej, Bouchaud 2026, arXiv 2607.01550; ~100 futures 1995-2025 | EWM-τ-4τ Sharpe 0.84/0.83/0.79/0.70 → 0.12/0.22/0.27/0.40 (τ = 5/10/20/50 d); small-tick (equity index, FX) about 0 post-2008; large-tick 1.0-1.2; trends better in low vol | strong |
| R3 | TSMOM | Moskowitz, Ooi, Pedersen 2012, JFE 104(2); 58 futures | 1-12 month persistence, partial reversal after 1 year | strong (outside DOL horizon) |
| R4 | Intraday momentum | Gao, Han, Li, Zhou 2018, JFE 129(2); SPY 1993-2013 | first half-hour → last half-hour R² 1.6% IS / 1.2% OOS; stronger on high-vol, high-volume days | moderate |
| R5 | OHLCV intraday momentum fails on MNQ | arXiv 2605.04004; 947 days 5-min 2021-25, walk-forward | 0 of 14 families pass; ORB long T = 0.88 | moderate |
| R6 | No forecast skill at 5-120 min | arXiv 2611.12141; ES/NQ, preregistered | 0 of 160 cells beat no-change; a sign-randomised null reproduces about 95% of within-day RankIC | moderate |
| R7 | Reversal is magnitude, not sign | arXiv 2606.29591; SPY 1993-2026 + 21 assets | ρ(1) = −0.081 (z −7.4), sign test p = 0.11; FX, commodities, crypto random-walk-like | moderate |
| R8 | VR tests rarely reject RW intraday panel | arXiv 2610.11028; 61 instruments | VR test cannot reject RW for most; coherence measure adds almost nothing out-of-sample | moderate |
| R9 | LeBaron effect intraday | Bianco, Corsi, Renò 2008 (arXiv 0810.4912); S&P futures 1993-2001, < 20 min | predictable vol → lower serial correlation; unexpected vol → higher | moderate |
| R10 | Weekly equity index autocorrelation | Lo & MacKinlay 1988, RFS; CRSP 1962-85, 1,216 weeks | equal-weighted first-order AC = 0.30; RW rejected | strong (historical, weekly, not DOL) |
| R11 | Hurst estimation in short samples | Kristoufek 2012 (arXiv 1201.3511); Barunik & Kristoufek 2012 (1201.4786) | R/S biased upward with short memory; estimator variance large; GHE best | strong (methodological) |
| R12 | ADX filter | oxfordstrat Donchian+ADX; algolab 2026 blog (22 tickers) | no added value / gains only from skipping chop | weak |
| R13 | VVG regime days (MNQ) | arXiv 2605.11423; 947 days | 4.4% of sessions; 77.6% reverse from intraday peak; no directional rule passes year-stability | weak-moderate |
| R14 | AMD direction = daily trend regime | Taylor 2026, arXiv 2610.35887 (sibling `ict_struct.md` S5) | aligned with trend 62-71%, against 25-30% (NQ 15m, N = 484) | moderate; part may be geometry (2.4) |
| R15 | Volatility persistence | Corsi 2009 HAR; Bennedsen et al. 2026 rough HAR (arXiv 2609.21587) | daily, weekly and monthly RV components capture strong persistence | strong |
| R16 | Crabel contraction | sibling `bias_dol.md` 2.8 | NR7: next range > median only 26-45%; both extremes taken about 2× more often (closeness) | moderate |
| R17 | Vol-state split of the PoT surface | sibling `quant_pot.md` QPOT-03 | lower log-loss on 6/6 symbols at H = 12/30/60, ECE ≤ 0.004 | moderate |

---

## 3. Engine gap analysis (baseline_v2.pine)

| Concept | Status | Where | What the engine does / what differs |
|---|---|---|---|
| Explicit regime classifier (trend/range/vol) | **missing** | — | No ER, ADX, CHOP, Hurst or squeeze state. The only "regime" is `htfBias` (−1/0/+1) used as the empirical-surface row (1060, 1284-1301, 1530-1532). |
| Empirical PoT regime key | **partial / wrong key** | 1060-1062, 1284-1301 (`r = side==1 ? bias+1 : 1−bias`), 1307, 1318, 1530-1532, 2112-2115 | The key is trend direction (htfBias). Trend measures carry no reach information (2.6, ER/CHOP/ADX/Hurst \|ΔLL\| ≤ 0.17%; htfBias ≈ no skill per `ict_struct.md`). Volatility state does (2.6, QPOT-03). |
| Proximity "reach" | **partial** | 665 | Uses the analytic `f_pot` with drift, not the empirical surface, so it ignores volatility state. |
| PoT drift | **present, wrong** | 917 (`potMu`), 665, 1304-1305, 1361-1363, 2067, 2184 | Drift worsens log-loss in every regime incl. ER ≥ 0.4 (2.5). QPOT-01 already proposes μ = 0. A regime switch does not rescue it. |
| Draw vector D (structure 0.5·HTF + 0.3·STF + 0.2·exe) | **present, wrong use** | 1891-1895 | D gates selection (`dirSide`, 1895, 1975) whenever \|D\| ≥ 0.35, regardless of regime. D-first loses 9-12 pp first-touch intraday (2.4). An ER gate recovers geometry. |
| Counter-draw penalty | **present, mis-scoped** | 692-693 (`ctrMult` 0.50), 2029 (`activeCtr`), 2237 (⚠ label) | Applied whenever \|D\| ≥ dGate. Evidence for a counter-trend handicap exists only in efficient trends at 1H/D (−5 pp vs null, weak). |
| Raid outcome sign ("holds = continuation, rejects = reversal") | **present, wrong** | 1579-1582 (`liqEvt`) | Hold vs reject races are identical (0.497-0.510) in every regime intraday (2.7). BIAS-4 already proposes removal. |
| Coiling (CHOP-like) in density | **present, unsupported** | 886-891 (`coilScore`), 683, 687 | Pools printed in coiled windows are no more magnetic (2.6). WYK-1 proposes neutralising it. |
| Range regime ("both sides raided") | **missing (no need for a bonus)** | — | Ranges do not raise P(both) or magnetism (2.6). WYK-3's range-edge merge and draw-neutral selection fit the data; a range *bonus* would not. |
| Volatility compression / expansion | **partial** | 874-878 (`atrE` = max(ATR14, ATR200) for ejection), 886-891 | Used only for ejection gates. Not used for PoT, reach, both-sides risk or the ledger. |
| Squeeze / NR7 directional breakout | **missing (correctly)** | — | No directional evidence (2.3). |
| Hurst / VR / ADX | **missing (correctly)** | — | Noise at chartable windows (0.9, 2.2). |
| Per-regime accuracy | **missing** | ledger 1375-1499 (`Trial` 375-395, `f_openTrial` 1426, `f_book` 1461) | The ledger splits by level family only. The user cannot see whether picks work in trends vs ranges, or in compression vs expansion. |
| Killzone hysteresis | n/a (time regime) | 980 (`hystEff`) | Time-of-day regime belongs to `ict_time.md` (TIME-5). |

---

## 4. Proposals (spec-level, best first; max 10)

Notation for Pine: new globals sit in SERIES after line 895 unless stated. State goes after line 1080. Engine changes run inside the confirmed-bar block (1518+). Everything uses closed-bar values, adds no new `request.*` call, and has O(1) cost per bar except where noted.

### REG-1 (P1, M) · Volatility state replaces HTF bias as the regime key of the empirical PoT surface, and proximity reach uses it
**Why.**
- Trend keys (htfBias, ER, CHOP, ADX, Hurst) carry no information about how far price travels in ATR units: |ΔLL| ≤ 0.17% (2.6).
- Volatility state does: reach ≥ 3 ATR 0.50 → 0.39 (1H) and 0.46 → 0.33 (15m) from the compressed to the expanded tercile, with OOS ΔLL −0.5% to −0.9%. QPOT-03 independently finds lower log-loss on 6/6 symbols.
- Volatility state is persistent (corr 0.5-0.8; 2.2). Trend state is not.
- Splitting the surface by an uninformative key only divides the sample by 3.

This merges QPOT-03 (vol-state rows) with BIAS-6 (drop the htfBias key unless it earns its place) into one change. It is also the regime-aware "EQ/pool scoring" change the data supports.

**Algorithm.**
1. Volatility state `vState ∈ {0 compressed, 1 normal, 2 expanded}`.
   - Preferred input: QPOT-02's q = √V_H/(ATR·√H) when implemented.
   - Fallback (this study): x = ln(ATR(5)/ATR(100)).
   - z-score it against an EWMA mean/variance with half-life 2000 bars.
   - Normal terciles ±0.43 with hysteresis: enter at ±0.43, leave at ±0.30.
2. Surface rows = vState only (3 rows per side, same array size `3*NB1` as today).
   - Bump with `vState[H]`, the state at the start of the window, exactly as `htfBias[H]` is used now.
3. `f_empPoT` receives the side's row from `f_rows` (sketch below) instead of `htfBias`. `f_potModel`, `f_potBase` (1307, 1318) and `f_reachD` (2112-2115) pass the current `vState`.
4. Proximity reach (665) uses the same blended PoT as the HUD: `f_potModel(dist, side, 0.0) / 0.95`, so a compressed regime lifts far pools and an expanded one lowers them. This is O(1) per level.
5. On 5m and lower, the plain ATR ratio carries little (2.6, 5m ΔLL 0.00%). Use QPOT-02's vol-time q there, or QPOT-03's session-bucket fallback.

**Pine sketch.**
```pine
// INPUTS (G_POT)
string vsKey = input.string("Volatility", "PoT Regime Key", options = ["Volatility", "HTF Bias", "None"], group = G_POT,
  tooltip = "Rows of the empirical reach surface. Volatility: compressed / normal / expanded (ATR5 vs ATR100). HTF Bias: the classic split.")
// SERIES (after 895)
float vLn = math.log(nz(ta.atr(5) / ta.atr(100), 1.0))
// STATE (after 1080)
var float vMu = na
var float vVar = 0.04
var int   vState = 1
// ENGINE step 0 (before 1526), confirmed bars
float aV = 2.0 / 2001.0
float dv = vLn - nz(vMu, vLn)
vMu  := nz(vMu, vLn) + aV * dv
vVar := (1.0 - aV) * (vVar + aV * dv * dv)
float vz = (vLn - vMu) / math.sqrt(math.max(vVar, 1e-6))
vState := vState == 0 ? (vz > -0.30 ? 1 : 0) : vState == 2 ? (vz < 0.30 ? 1 : 2) : (vz < -0.43 ? 0 : vz > 0.43 ? 2 : 1)
// rows per side: Volatility -> both sides use the vol row; HTF Bias -> the classic with/against mapping
f_rows(int bias, int vs) =>
    int rU = bias + 1
    int rD = 1 - bias
    if vsKey == "Volatility"
        rU := vs
        rD := vs
    else if vsKey == "None"
        rU := 1
        rD := 1
    [rU, rD]
// step 0 bump (replaces 1530-1532)
[rU, rD] = f_rows(htfBias[H], vState[H])
f_bump(sUp, rU, (fwdHi - close[H]) / aH)
f_bump(sDn, rD, (close[H] - fwdLo) / aH)
```
- `f_empPoT(dAtr, side, rU, rD)` picks `r = side == 1 ? rU : rD` from `f_rows(htfBias, vState)`, the current state, so all three keys share one code path. Declare `f_rows` after the `vsKey` input (Pine has no forward references) and as a global function, not inside the `if` block. The function returns a plain two-int tuple from its last line.
- `vState` is a `var int`, so `vState[H]` is a valid history reference. It only changes on confirmed bars and never repaints.
- `math.log` of `na` is guarded with `nz(..., 1.0)`.

**Ledger measurement.** QPOT-04's PoT reliability/Brier (graded on trials), A/B with `vsKey`. Also the `pBase` edge baseline: a vol-matched baseline removes spurious "edge" in compressed regimes.

**Expected value.**
- PoT that is right in both quiet and violent tapes (a 30-bar 2-3 ATR target is about 1.2-1.4× likelier after compression than after expansion on 15m/1H).
- Proximity stops over-scoring far pools in expansion.
- Evidence: **strong** for persistence and clustering, **moderate** for the PoT gain (this study + QPOT-03).

**Risk.**
- The EWMA needs about 500 bars to settle. Until then `vz` ≈ 0 → `vState = 1`, which is the pooled row.
- Changing the key resets the meaning of existing rows, which is harmless because the surface is rebuilt from history on load.

**Effort.** M.

### REG-2 (P1, M) · Two-axis regime classifier and a regime-split ledger ("does the engine work in trends, ranges, squeezes?")
**Why.**
- The user asked for a regime-aware engine. The honest version measures, per chart, whether regime matters, instead of assuming it.
- It is also the infrastructure the gates in REG-3/REG-4 and the readout in REG-5 report through.

**Classifier.** It runs on the chart timeframe, which keeps it cheap and needs no extra request.
- **E axis (efficiency)**, with `erLen = 20` and thresholds `erTrend = 0.40` and `erRange = 0.15`:
  - `erS = (close − close[erLen]) / math.sum(math.abs(ta.change(close)), erLen)`; `erA = |erS|`.
  - `eState = erA ≥ erTrend ? sign(erS) : erA < erRange ? 0 : eState[1] (hold) when erA ≥ erTrend − 0.08, else 0`.
  - Labels: TREND ▲ / TREND ▼ / RANGE / MIXED. Also `gE = clamp((erA − 0.25)/0.20, 0, 1)`.
- **V axis.** `vState` from REG-1, labels COMPRESSED / NORMAL / EXPANDED. Optional TTM-style squeeze flag `sqz = 2*ta.stdev(close,20) < 1.5*ta.atr(20)` as a display synonym.
- **Base-rate disclosure.** The tooltip states that on random data "TREND" fires on about 1 bar in 5 and that the label describes the last `erLen` bars.

**Ledger split** (extends 375-395, 1426-1431, 1461-1499).
- `Trial` gains `int eCls` and `int vCls`, set in `f_openTrial`:
  - `eCls = erA < erRange ? 0 : erA < erTrend ? 1 : (math.sign(erS) == lv.side ? 2 : 3)`, i.e. RANGE / MIXED / TREND-WITH (target on the trend side) / TREND-AGAINST;
  - `vCls = vState`.
- New arrays `rgN`, `rgK` (int, size 7) and `rgPE`, `rgPV` (float, size 7). Index `eCls` (0-3) and `4 + vCls` (4-6) are updated in `f_book` next to `stN/stK/stPE/stPV`.
- Full accuracy view, two rows using the existing Wilson/z helpers. EDGE = (K − ΣpBase)/n in pp, z = (K − ΣpBase)/√ΣpV:
  - `REGIME  RNG 44% +1.2 · MIX 47% +3.0 · TR+ 52% +4.1 · TR− 38% −6.0`
  - `VOL     CMP 55% +2.0 · NRM 47% +1.1 · EXP 39% −0.4`
- TREND-AGAINST vs TREND-WITH directly measures the trader's claim C1 ("opposite liquidity holds in trends") on *this* chart.

**Panel / Clean look.**
- Terminal: one row `REGIME  TREND ▲ · ER .52 · VOL CMP`, coloured with the bias colours (neutral grey for RANGE/MIXED).
- Clean: unchanged by default. An optional 4th row `Regime | TREND ▲` uses the same table style as the reference look.
- Data window: `plot(erS, "Efficiency (signed)", display = display.data_window)` and `plot(vState, "Vol State", display = display.data_window)`.

**Pine sketch.**
```pine
const string G_REG = "Regime"
int   erLen   = input.int(20, "Efficiency Length", minval = 5, maxval = 200, group = G_REG)
float erTrend = input.float(0.40, "Trend if Efficiency ≥", minval = 0.10, maxval = 0.95, step = 0.05, group = G_REG,
  tooltip = "Kaufman efficiency ratio: net move / path length. It describes the last N bars; on random data about 1 bar in 5 reads as 'trend'.")
float erRange = input.float(0.15, "Range if Efficiency <", minval = 0.0, maxval = 0.5, step = 0.05, group = G_REG)
float erPath  = math.sum(math.abs(ta.change(close)), erLen)
float erS     = erPath > 0 ? (close - close[erLen]) / erPath : 0.0
float erA     = math.abs(erS)
var int eState = 0          // updated on confirmed bars (engine step 0)
```
- `math.sum` takes a series int length (reference: "`length` (series int)"). `ta.atr` takes a simple int; 5 and 100 are literals.

**Ledger measurement.** This is the measurement. Per-regime EDGE z becomes visible after about 100 graded trials.

**Expected value.**
- Traders learn *on their own chart* whether the DOL is reliable in trends vs ranges vs compression.
- It gives REG-3/4 a place to show their effect (TR− EDGE should stop being negative once counter-draw targets are scoped).
- Evidence for the measurement design: strong (it is a stratified version of the existing ledger). Evidence that any regime matters: weak (2.3).

**Risk.**
- Thin cells, hence Wilson intervals and a minimum n = 20 before showing a number.
- The extra 7-element arrays are negligible.

**Effort.** M.

### REG-3 (P1, S) · Efficiency-gated draw: D affects selection only in an efficient trend that agrees with it; drift stays zero in every regime
**Why.**
- Choosing the side by the engine's structure vote D loses 9-12 pp of first-touch accuracy and 5-8 pp of hit-within-K intraday (5 pp / 3 pp daily) against geometry (2.4).
- Gating D by `ER20 ≥ 0.40 and sign(D) = sign(sER)` recovers geometry within 0.2 pp everywhere. ADX gating does not (−2.5 to −3.5 pp).
- In efficient trends geometry already points with the trend 76-82% of the time, so the gate keeps the trader-facing "draw follows the trend" behaviour where it is true.
- Drift adds error in every regime (2.5), so no "trend regime → turn on drift" shortcut.
- This is the minimum-change fallback for BIAS-1/BIAS-2 (calibrated side probability). If those land, feed `gE·sign(erS)` to them as a learned feature (REG-6) instead.

**Algorithm.**
1. Step 14 (1891-1895): keep `drawD` for the panel, the Draw Flip alert and the data window. Compute a selection draw:
   - `agree = math.sign(drawD) == math.sign(erS)`;
   - `dSel = drawD * (1 − regGate + regGate * (agree ? gE : 0))`, with `gE = f_clamp((erA − 0.25)/0.20, 0, 1)`.
   - `regGate` is an input with default 1.0 (evidence); 0 = classic.
2. `dirSide` (1895) uses `dSel`. `lv.evaluate(…, dSel, nz(potSig), 0.0)` (1948) uses `dSel` for the Draw pillar and **0 drift**. `activeCtr` (2029) follows from `dirSide`.
3. PoT drift: `potMu` stays computed for nothing else. Default `driftW = 0.0` (QPOT-01). The tooltip says why: "trend-regime drift was tested and lowers accuracy".
4. Panel: show `DRAW ▲ +0.62 (gated: RANGE)` when `dSel ≈ 0` and `|drawD| ≥ dGate`, so the user sees why the draw is not steering.

**Pine sketch.**
```pine
float regGate = input.float(1.0, "Gate Draw by Efficiency", minval = 0.0, maxval = 1.0, step = 0.1, group = G_REG,
  tooltip = "1 = the draw vector steers target choice only in an efficient trend that agrees with it; elsewhere the nearer, likelier pool wins. 0 = classic.")
// step 14 (after 1894)
float gE   = f_clamp((erA - 0.25) / 0.20, 0.0, 1.0)
bool  agr  = math.sign(drawD) == math.sign(erS)
float dSel = drawD * (1.0 - regGate + regGate * (agr ? gE : 0.0))
int dirSide = dSel >= dGate ? 1 : dSel <= -dGate ? -1 : 0
```
`math.sign` returns a float; comparing two floats for equality is fine (values −1, 0, 1).

**Ledger measurement.**
- DOL HIT% and EDGE z overall.
- REG-2's TR−/TR+ cells.
- The side ledger (BIAS-1) Brier when present.
- A/B with `regGate` 0 vs 1.

**Expected value.**
- On the simulation, +9-12 pp first-touch and +5-8 pp hit-within-H of the chosen side intraday (+5 / +3 pp daily).
- Fewer "⚠ COUNTER-DRAW" flips in chop.
- Targets that track geometry, which is the strongest single predictor (`bias_dol.md`).
- Evidence: **moderate** (engine-proxy simulation on 23 series + null; sibling sidesel).

**Risk.**
- In a genuinely trending market with a far with-trend pool the gate defers to the nearer pool, as the data say it should.
- The look and alerts are unchanged.

**Effort.** S.

### REG-4 (P2, S) · Scope and soften the counter-draw penalty
**Why.**
- `ctrMult = 0.50` (162, 692-693) halves the score of every level opposite D whenever |D| ≥ 0.35.
- The only support for a counter-trend handicap is in efficient trends at 1H/D: counter-trend pools are touched about 5 pp less than the null (2.6), on a base of about 50%. That corresponds to a multiplier of about 0.85-0.90, not 0.50.
- In RANGE/MIXED there is no side preference at all (2.3, 2.6).

**Change.**
- With REG-3, `dirD = dSel` already confines the penalty to gated trends.
- In addition, default `ctrMult = 0.85`, and require `eState != 0` before `activeCtr` labels a target "⚠ COUNTER-DRAW" (2029, 2237).
- Hold logic (2006-2007) is unchanged.

**Pine.** Change the input default to `0.85`. `activeCtr := not na(activeLv) and dirSide != 0 and activeLv.side != dirSide and eState != 0`.

**Ledger measurement.** REG-2's TREND-AGAINST cell EDGE. If it stays ≤ −1σ on a chart, the user can lower `ctrMult`.

**Expected value.** Fewer good near targets thrown away for a far "draw" target. Evidence: **weak** (direction of effect consistent at 1H/D, not significant individually).

**Risk.** Low.

**Effort.** S.

### REG-5 (P2, M) · Compression / expansion readout: "stop-run risk" and an expansion alert (claim C2 done right)
**Why.**
- "Both sides get raided" is true in *compressed volatility*, not in ranges.
- P(both pools within K) rises with compression: OOS ΔLL −0.97% (1H), −2.95% (15m). Reach in ATR is higher on both sides (2.6).
- The trader needs to know when the stop beyond the opposing pool is likely to be run before or around the target. The engine's race WIN≤H (`f_invalidation`, 1352-1366) is a martingale race and is blind to this.

**Readout (Terminal HUD and tooltip of the Clean label).**
- `STOP-RUN ≈ p%` = the empirical P(price reaches the invalidation distance on the opposite side within H) from the REG-1 surface: `f_potModel(risk, -side, 0.0)`. That is one O(1) call.
- A `SQZ` / `EXP` tag from `vState`.

**Grading.**
- `Trial` gains `bool stpH = false`.
- A tiny side array `srInv/srSide/srEnd` keeps the invalidation price for H bars after the trial is booked, so a stop touch after the target counts.
- Per closed record: Brier of `pStopRun` vs `stpH`, shown in the Full view as `STOP-RUN cal 0.31→0.29 (n 120)`.

**Alert.** Optional `Volatility Expansion`: `vState` goes from 0 to 2 within ≤ 10 bars, or a TTM-style squeeze releases. Fired on bar close via `alert()`. The message states: "range expansion likely in ATR terms; direction not forecast".

**Pine sketch.**
```pine
var array<float> srInv  = array.new<float>()
var array<int>   srSide = array.new<int>()
var array<int>   srEnd  = array.new<int>()
var array<float> srP    = array.new<float>()
// on booking a trial whose target hit before H: push inv, side, bar0 + H, pStopRun
// each confirmed bar: for i = size-1 to 0 -> if (side == 1 ? low <= inv : high >= inv) or bar_index >= end -> grade, remove
```
- The arrays stay ≤ H + 64 entries, so the loop is O(H) per confirmed bar, far below the "500 milliseconds" per-loop limit (writing_scripts/limitations).

**Expected value.**
- A concrete, graded answer to "will they run my stop first?", conditioned on the regime that actually matters.
- Evidence: **moderate** for the vol-state effect (mechanical, replicated in the null and in QPOT-03). Directional content: none, and it is labelled so.

**Risk.**
- One more HUD line (Terminal only).
- Alert noise if thresholds are too loose; a ≤ 10-bar transition rule and a once-per-state latch control it.

**Effort.** M.

### REG-6 (P3, S) · Regime features for the learned side model (only if BIAS-1 is implemented)
**Why.**
- Weak but plausible signals exist:
  - 1H with-trend excess in efficient trends (+6.1 ± 2.5 pp, 2.3);
  - 5m continuation of sweeps aligned with an efficient trend (+5 pp vs null, 2.7);
  - the counter-trend pool handicap at 1H/D (2.6).
- None replicates across all timeframes. They belong in a per-chart learned model with zero prior weight, not in fixed rules.

**Features** (all ∈ [−1, 1], oriented toward the buy-side candidate):
- `gE·sign(erS)`;
- `gE·sign(erS)·[last bar swept a pool on that side]`;
- `vz` (clipped ±2)/2, a vol state that is direction-free and should learn ≈ 0;
- `sign(erS)·[ER ≥ 0.4]·[d_with > d_against]`, the trend-with-far-target case.

**Learner.** BIAS-1's online logistic over the geometry logit with L2 shrinkage toward 0. Report the learned weights in the Full view ("regime weight +0.04 ± 0.06").

**Ledger measurement.** Side-ledger Brier skill vs geometry. If ≤ 0 after n ≥ 200, the panel shows "regime: no skill on this chart".

**Evidence.** **Weak.**

**Risk.** Overfitting, controlled by shrinkage and the prequential score.

**Effort.** S (given BIAS-1).

---

## 5. What NOT to do (tested and rejected here)

- **ADX ≥ 25, CHOP < 38.2 / > 61.8, Hurst > 0.55, or VR as a trend/range switch.** They fire on 15-49% of random-walk bars, have no next-window persistence (2.2), and an ADX gate on D costs 2.5-3.5 pp (2.4).
- **A trend-regime drift in PoT or races.** It is worse in every regime (2.5); the race is a martingale race (QPOT §0.6).
- **A range bonus for EQ/range-edge pools, or an expectation that "both sides get raided" in ranges.** Not supported (2.6). Use WYK-3's edge merge and draw-neutral selection instead; that change is consistent with this study.
- **The squeeze/NR7 direction** (momentum histogram, break of the narrow bar) as a draw input. There is no which-side information (2.3).
- **Keeping `liqEvt`'s hold/reject sign** (1579-1582). Hold vs reject races are identical in every regime intraday (2.7; BIAS-4).
- **Rewarding pools printed during coiling** (`coilScore` in density, 683/687). There is no magnetism effect (2.6; WYK-1).
- **A Markov-switching/HMM classifier in Pine.** It is feasible, but nothing in this study suggests it would add to an O(1) vol z-score plus ER.

---

## 6. Reproduction

All scripts are in `study/quant_regime_tools/` and run with `python3 -I <script> [family]`, where family is `5m`, `15m`, `1h` or `d`. They need only numpy and take seconds.

| Script | Output | Content |
|---|---|---|
| `rlib.py` | — | loaders, causal indicators (ATR, ER/sER, ADX/DI, CHOP, VR-Hurst, BB-width pct, ATR5/ATR100, NR7, EMA distance, φ_n), pivot pools with strict-through sweeps, first passage, sign-flip null, logistic fit, block SE |
| `regime_study.py` | `out_1h.txt`, `out_5m.txt`, `out_15m.txt`, `out_d.txt` | O1 side race vs geometry (bins, regime gates, OOS logit); O2 both sides; O4 reach by regime; O5 drift sign; O3 post-sweep continuation; each also on the null |
| `regime_persist.py` | `out_persist.txt` | label base rates and next-window persistence, real vs null |
| `regime_engine.py` | `out_engine_<fam>.txt` | (a) side rules, (b) PoT drift by regime, (c) pool magnetism by regime, (c2) with/counter-trend pools |
| `regime_dgate.py` | `out_dgate.txt` | engine-like structure D vs geometry, with ER / ADX / soft gates |
| `regime_form.py` | `out_form.txt` | coil/ER at pool formation; geometry–trend agreement in efficient trends |

**Limitations.**
- About one year of 1H data and three months of 1-min data for six CME futures (one volatility regime, 2025-26). Older daily equities (1999-2018); two FX hourly sets.
- No crypto or single stocks intraday.
- Pools are 5-bar pivots, not the engine's full source mix (PDH/PDL, sessions, HTF swings). Effects on external pools could differ; REG-2's ledger split measures that on the user's chart.
- Multiple comparisons: about 20 gates × 4 families × 3 statistics. Single 2-3σ cells are treated as weak.

---

## 7. Sources

- Safari, S. A. & Schmidhuber, C. (2025). *Trends and Reversion in Financial Markets on Time Scales from Minutes to Decades.* arXiv:2501.16772. https://arxiv.org/abs/2501.16772
- Schmidhuber, C. (2020/21). *Trends, Reversion, and Critical Phenomena in Financial Markets.* arXiv:2006.07847. https://arxiv.org/abs/2006.07847
- Kurth, J. G., Eisler, Z., Rej, A., Bouchaud, J.-P. (2026). *Is Trend Still Your Friend? A Microstructural Account of the Demise of Short-Term Trend-Following.* arXiv:2607.01550. https://arxiv.org/abs/2607.01550
- Moskowitz, T., Ooi, Y. H., Pedersen, L. H. (2012). *Time Series Momentum.* JFE 104(2), 228-250. https://papers.ssrn.com/abstract=2089463 · https://www.aqr.com/Insights/Datasets/Time-Series-Momentum-Original-Paper-Data
- Gao, L., Han, Y., Li, S. Z., Zhou, G. (2018). *Market Intraday Momentum.* JFE 129(2), 394-414. https://econpapers.repec.org/RePEc:eee:jfinec:v:129:y:2018:i:2:p:394-414 · working paper: https://c.mql5.com/forextsd/forum/173/intraday_momentum_-_the_first_half-hour_return_predicts_the_last_half-hour_return.pdf
- Heston, S. L., Korajczyk, R. A., Sadka, R. (2010). *Intraday Patterns in the Cross-section of Stock Returns.* arXiv:1005.3535. https://arxiv.org/abs/1005.3535
- Lo, A. W., MacKinlay, A. C. (1988). *Stock Market Prices Do Not Follow Random Walks.* RFS 1(1). https://web.mit.edu/~alo/www/Papers/lo-mackinlay-88.html · https://nber.org/system/files/working_papers/w2795/w2795.pdf
- Portnaya, V. (2026). *The Bounce Has No Direction.* arXiv:2606.29591. https://arxiv.org/abs/2606.29591
- Le, N. H. (2026). *Synchronization Reveals Market Structure That Classical Randomness Tests Cannot Detect.* arXiv:2610.11028. https://arxiv.org/abs/2610.11028
- Upadhyay, R. (2026). *Do Time-Series Foundation Models Forecast Index-Futures Returns?* arXiv:2611.12141. https://arxiv.org/abs/2611.12141
- Mesfin, M. (2026). *Structural Limits of OHLCV-Based Intraday Momentum Signals in MNQ Futures.* arXiv:2605.04004. https://arxiv.org/abs/2605.04004 · *A Validated Volatility-Volume-Gap Classifier for Regime Identification in MNQ Intraday Data.* arXiv:2605.11423. https://arxiv.org/abs/2605.11423
- Bianco, S., Corsi, F., Renò, R. (2008). *Serial correlation and heterogeneous volatility: beyond the LeBaron effect.* arXiv:0810.4912. https://arxiv.org/abs/0810.4912 · Bianco & Renò (2006) arXiv:physics/0610023
- Kristoufek, L. (2012). *How are rescaled range analyses affected by different memory and distributional properties?* arXiv:1201.3511. https://arxiv.org/abs/1201.3511
- Barunik, J., Kristoufek, L. (2012). *On Hurst exponent estimation under heavy-tailed distributions.* arXiv:1201.4786. https://arxiv.org/abs/1201.4786
- Bartolozzi, M., Mellen, C., Di Matteo, T., Aste, T. (2007). *Multi-scale correlations in different futures markets.* arXiv:0707.3321. https://arxiv.org/abs/0707.3321
- Corsi, F. (2009). *A Simple Approximate Long-Memory Model of Realized Volatility* (HAR). J. Financial Econometrics 7(2). Context: Bennedsen et al. (2026) arXiv:2609.21587. https://arxiv.org/abs/2609.21587
- Bollerslev, T., Tauchen, G., Zhou, H. (2009). *Expected Stock Returns and Variance Risk Premia.* RFS 22(11).
- Hamilton, J. D. (1989). *A New Approach to the Economic Analysis of Nonstationary Time Series and the Business Cycle.* Econometrica 57(2). Pomorski & Gorse (2022) arXiv:2208.11574 https://arxiv.org/abs/2208.11574 · Srivastava & Bhattacharya (2018) arXiv:1812.02527 https://arxiv.org/abs/1812.02527
- Wilder, J. W. (1978). *New Concepts in Technical Trading Systems* (ADX/DMI). ADX filter tests: https://oxfordstrat.com/trading-strategies/average-directional-index/ · https://algolab.co.kr/blog/adx-filter-trend-breakout-backtest-2026 · https://www.oreilly.com/library/view/mechanical-trading-systems/9780471730972/chapter03-sec012.html
- Kaufman, P. J. *Trading Systems and Methods* / *Smarter Trading* (efficiency ratio, KAMA). Concept summary: https://www.luxalgo.com/library/concept/kaufman-efficiency-ratio.md
- Dreiss, E. W., Choppiness Index: https://www.tradingview.com/wiki/Choppiness_Index_(CHOP) · https://www.barchart.com/education/technical-indicators/choppiness_index
- Carter, J., TTM Squeeze: https://www.barchart.com/education/technical-indicators/ttm_squeeze · https://toslc.thinkorswim.com/center/reference/Tech-Indicators/studies-library/T-U/TTM-Squeeze
- Crabel, T. (1990). *Day Trading with Short Term Price Patterns and Opening Range Breakout* (NR4/NR7). Sibling test: `study/bias_dol.md` 2.8.
- Taylor (2026), AMD on NQ, arXiv:2610.35887 (via sibling `study/ict_struct.md`).
- Sibling studies: `study/quant_pot.md` (QPOT-01..09), `study/bias_dol.md` (BIAS-1..7), `study/wyckoff_sd.md` (WYK-1, WYK-3), `study/ict_struct.md`, `study/ict_time.md`, `study/orderflow_micro.md`.
