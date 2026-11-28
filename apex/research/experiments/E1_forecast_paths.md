# E1 · Forecast paths: which forward-path method beats a random walk, and how should uncertainty be shown?

Role: R8 forecasting engineer. Key: `E1_forecast_paths`. Code: `apex/validation/python/experiments/E1_forecast_paths/`.
Spec: section 14 (one forward path, horizons 20-120 bars, default 60), sections 15, 20 and 25.

---

## 1. Pre-registration (written 2026-11-27 09:49 UTC, before any forecast result was computed)

Only data checks had been run when this section was written: timezone, duplicates, gaps and jumps.
Nothing in this section was changed after results were seen. Any later deviation is listed in section 9 with both versions.

### 1.1 Data
- **CME futures** (clone of axb0306/cme-futures-ohlc). Timestamps are UTC: the missing hour is 17:00 New York (the CME maintenance break) in both EST and EDT. There are no duplicates, no non-monotonic stamps and no bad OHLC rows.
  - **5m:** resampled from the 1-minute files (UTC 5-minute bins, left-labelled, empty bins skipped). NQ, ES, YM, RTY, CL and GC, 2026-01-20 → 2026-04-15.
    - GC 1-minute is clean (0 jump-and-back events), so GC 5m is included.
    - CL has genuine March-2026 shock bars. Volume is normal, they are not contract interleaving, and they are kept.
  - **1h:** NQ, ES, YM and RTY 2025-03-21 → 2026-04-15; CL from 2025-06-01.
    - **GC 1h is excluded.** It interleaves two contract months: 747 bar-to-bar jumps over 1.5%, 290 of them jump-and-back, and the off-month bars have volumes of 1-6. A repair is possible but was not attempted.
- **BTC 1h:** 2016-01-01 → 2025-01-07, 79,057 bars, no gaps.

### 1.2 Common definitions
- Decision at the close of bar t. Every feature uses bars ≤ t. Pivots count only from their confirmation bar (pivot length 5, so the confirmation bar is p+5).
- ATR = Wilder ATR(14) at t.
- Horizons H ∈ {20, 60, 120} bars; **primary H = 60**.
- Forecast object: a path P̂(t,k), k = 1..H, for the close at t+k.
- Origins: every bar after the warmup with t+120 inside the data. The origin set is the same for every method and horizon.
- **Walk-forward, expanding window.**
  - First fit at T0 = 2000 bars (5m), 1500 (CME 1h) or 3000 (BTC 1h).
  - Refit every R = 500 bars (5m), 250 (CME 1h) or 2000 (BTC 1h).
  - Training origins at refit T are s ≤ T − 121. This is the purge: every training outcome, up to s+120, is realized before T.
- **Development / holdout.** The walk-forward range [T0, n−121] is split chronologically at its midpoint.
  - **Holdout = second half. It is the headline result.**
  - The first half is reported as "WF-dev".
  - An in-sample (IS) diagnostic fits once on the dev half and evaluates on the same dev half.

### 1.3 Methods (each computed only from data ≤ t; parameters only from purged training origins)
| id | Method | Path P̂(t,k) − C_t |
|---|---|---|
| a | Zero-drift random walk (**baseline**) | 0 |
| a2 | Historical mean drift (baseline) | μ̂·k·ATR_t. μ̂ is the training mean of (C_{s+1} − C_s)/ATR_s. |
| b50, b100, b200 | Rolling OLS drift, anchored at the last close | β_L·k. β_L is the OLS slope of close on bar index over the last L bars. |
| bL100 | Rolling OLS, anchored at the line end | (ŷ_t − C_t) + β_100·k |
| c0 | Naive momentum (engine-style, not fitted) | ATR_t·m_t·Σ_{j≤k} 0.5^{(j−1)/12}. m_t = EMA_20 of x, where x_t = ΔC_t/ATR_{t−1}. |
| c | Momentum persistence, decay fitted online | ATR_t·b̂·m_t·Σ_{j≤k} φ̂^{j−1}. c_k = Σ m_s·y_{s,k}/Σ m_s², with y_{s,k} = (C_{s+k} − C_{s+k−1})/ATR_s for k = 1..120. (b̂, φ̂) fit c_k = b·φ^{k−1} by least squares, half-life on the grid {1, 2, 3, 5, 8, 12, 20, 30, 50, 80, 120, 200, 500, ∞}. |
| d | Volatility-scaled drift, √time, time-of-day clock | κ̂·clip(z_t, ±3)·σclk(t,k). z_t = (C_t − C_{t−100})/(C_t·√ℓ_t·√100). See the note below the table for σclk. κ̂ is the least-squares fit through the origin of (C_{s+60} − C_s)/σclk(s,60) on clip(z_s). |
| e | State-dependent drift | ATR_t·M_state(k). M is the training mean of (C_{s+k} − C_s)/ATR_s within the state. A state with fewer than 300 training origins gets 0. |
| f | Target-aware bridge | p̂(bucket,H)·(L − C_t)·min(1, k/k̂*(bucket)). See the note below the table. |
| g | Shrinkage blend | (1/5)·Σ_m β̂_{m,H}·(P̂_m(k) − C_t) over m ∈ {b100, c, d, e, f}. See the note below the table. |

- **σclk (method d):** σclk(t,k) = C_t·√(ℓ_t·Σ_{j=1..k} v(slot_{t+j})).
  - v is the training time-of-day variance factor of squared returns. Buckets are 30 minutes of NY time for 5m, the NY hour for CME 1h and the UTC hour for BTC.
  - Future slots follow the sequence of active slots (slots present on at least 50% of days in the first 2000 bars), so the maintenance break and weekends are skipped.
  - ℓ_t is an EWMA of squared return / v(slot), with half-life 288 bars (5m) or 120 bars (1h).
- **States (method e):** 9 states = structure bias × volatility tercile.
  - Structure bias is the direction of the last break of structure: the close crosses the latest confirmed swing high (bull) or swing low (bear). Pivot length 5.
  - The volatility tercile comes from the percentile rank of ATR_t/C_t in the trailing 500 bars, with cuts at 1/3 and 2/3.
- **Target (method f):** L is the nearest level on the bias side.
  - Candidates: the untaken prior-day high or low (the CME day starts at 18:00 NY; BTC uses the UTC day), and the unbroken confirmed swing highs or lows.
  - Distance buckets, in ATR: [0, 0.5, 1, 1.5, 2, 3, 4, 6, 10, ∞).
  - p̂ = the training reach rate within H in that bucket. k̂* = the training median bars-to-hit among hits within 120 bars.
  - A bucket with fewer than 50 training origins gets 0. The target is never assumed to be hit.
- **Shrinkage weights (method g):** β̂ = the least-squares slope through the origin of the realized H-move on that component's walk-forward forecast, clipped to [0,1]. It needs at least 1000 such origins; otherwise it is 0.
- **Variant count:** 11 non-baseline variants (a2, b50, b100, b200, bL100, c0, c, d, e, f, g) × 3 horizons = **33 tests per pool**. There are 3 pools: CME 5m, CME 1h and BTC 1h.

### 1.4 Metrics
1. **Terminal error.** e = (P̂(t,H) − C_{t+H})/ATR_t; report MAE (primary) and RMSE, each as a ratio to the random walk.
   - Diebold-Mariano test on the loss differential, one-sided (H1: the method beats the RW). Newey-West HAC with Bartlett lag H, plus the Harvey-Leybourne-Newbold correction.
   - Pooled test per pool: the cross-sectional mean of the per-timestamp loss differential across symbols, which keeps the cross-symbol correlation, then HAC-DM on that series.
   - Holm and BH corrections over the 33 tests.
   - 95% CI of the MAE ratio by circular block bootstrap (block 2H, 1000 replications).
2. **Directional accuracy at H.** The sign of P̂(t,H) − C_t against the sign of C_{t+H} − C_t; zero forecasts and zero moves are excluded and counted.
   - Wilson 95% CI on the **non-overlapping** subsample (every H-th origin), per symbol.
   - Pooled: block-bootstrap CI on timestamps.
   - Compared with 50% and with an always-up baseline (paired difference, block bootstrap).
3. **Path-shape error.** PMAE_H = mean over k = 1..H of |P̂(t,k) − C_{t+k}|/ATR_t; report the ratio to the RW and the HAC-DM test.
4. **Uncertainty bands.** Rolling out-of-sample residual quantiles (10/50/90), using only residuals already realized at t (origin s ≤ t − k).
   - U0: per-horizon empirical quantiles of resid/ATR_t.
   - U1: √k scaling. The quantiles of resid/(ATR_t·√j) for j ∈ {10, 20, 40, 60, 90, 120}, averaged across j.
   - U2: as U1, with σclk(t,j) as the scale.
   - U3: U0 estimated within the current volatility tercile.
   - U4: Gaussian ±1.2816·σclk, uncalibrated.
   - Primary window: the last W = 2000 realized origins. Sensitivity: W ∈ {100, 250, 500, 1000, 2000, 4000, expanding}.
   - Report coverage of [q10, q90] (nominal 80%), both tail rates (nominal 10% each), the q50 exceedance (nominal 50%), the mean width and the interval score (α = 0.2). Break these down by k ∈ {20, 60, 120} and by volatility tercile.
5. **Economic check (secondary).** On non-overlapping origins: trade in the forecast's direction, enter at O_{t+1}, exit at O_{t+H+1}.
   - Cost per side, commission included: NQ 2 ticks, ES 1.25, YM 2, RTY 2, CL 1.25, GC 1.25; BTC 5 bp.
   - Report the mean net P&L per trade in ATR units and in ticks, a block-bootstrap CI and the Deflated Sharpe Ratio over the 33 trials.

### 1.5 Pass criteria
- **A method "genuinely beats the RW"** on a pool at horizon H only if all of these hold on the **holdout**:
  - (a) the pooled MAE ratio is below 1 with one-sided DM p_Holm < 0.05 over the 33 tests;
  - (b) the MAE ratio is below 1 in at least 2/3 of that pool's symbols;
  - (c) the MAE ratio is below 1 in WF-dev as well.
- **Practically meaningful** means an MAE reduction of at least 2%. Anything smaller is reported as negligible, even if it is significant.
- **Directional edge:** the per-symbol non-overlapping Wilson lower bound is above 50%, and the method beats always-up with a bootstrap CI that excludes 0.
- **Calibrated band:** holdout coverage of [q10, q90] within ±5 pp of 80% at every k, and within ±8 pp in every volatility tercile.
- **Minimum band sample:** the smallest W at which pooled holdout coverage is within ±3 pp of 80% and the interval score is within 2% of the best W.
- **Expected outcome (prior, stated before the run).** The study found direction ≈ random walk and volatility structured. My prior: no drift method passes. If any passes, it will be small (< 2%). Volatility-clock bands should calibrate better than ATR·√k.

---

## 2. Resume audit: what was inherited, what was checked (2026-11-28)

An earlier attempt was interrupted by a usage limit. It left section 1, `e1_run.py`, a complete set of forecast files in `out/`, and an `e1_eval.py` that died during its first stage, so no results existed.

- **Pre-registration timing.** The report file was last written at 09:50 UTC on 2026-11-27. The first forecast output was written at 09:55 UTC. Section 1 is kept byte-for-byte; its SHA-256 before this section was appended was `fd1e5609…a31`.
- **Checks run in this session** (`e1_verify.py`):
  - **Timezone.** On NQ 1h the missing daily hour is 22:00 UTC in January and 21:00 UTC in July, which is 17:00 New York in both cases. The stamps are UTC, as section 1 says.
  - **GC 1h.** 747 bar-to-bar jumps over 1.5%, 289 of them jump-and-back (section 1 said 290; the difference is the counting rule). The jump-and-back bars have a median volume of 4, against 257 overall. This confirms the two contract months are interleaved, so GC 1h stays **excluded**.
  - **GC 1-minute.** 7 jumps and 0 jump-and-back, so GC 5m is kept.
  - **CL 1h.** 17 jump-and-back bars, 16 of them in March-April 2026. Their median volume is 9,691, against 3,375 overall. These are genuine shock bars and are kept.
  - **Feature truncation test.** Features computed on `data[:N]` equal the full-data features at every bar < N. Tested on NQ 1h (N = 3001), NQ 5m (N = 7777) and BTC 1h (N = 20011). Features checked: ATR, momentum, OLS slopes and line end, structure bias, volatility tercile, target level and distance bucket, squared returns and clock position. No mismatches.
  - **Fit truncation test.** Every walk-forward parameter fitted at refit T is identical whether the data ends at bar T or at the full length. Tested on NQ 1h (T = 2750) and ES 5m (T = 6000). Parameters checked: a2 μ; c b and half-life; d κ and ℓ; the e state means; the f reach rates and median hit times; and the training hit times.
- **Code-review findings** (disclosed in section 9; none changes a conclusion):
  - (i) The active-slot calendar for CME 1h uses the first 2000 bars, which run 500 bars past T0 = 1500.
  - (ii) The f and g paths at non-anchor horizons feed only the U1/U2 bands for those two methods.
  - (iii) Pandas deprecation fixes in `e1_eval.py`, which do not change any number.
- **Rerun.** `e1_run.py` and `e1_eval.py` were both rerun end to end in this session (venv: numpy 2.5.5, pandas 3.1.1, scipy 1.18.1). Every number below comes from that rerun.
- **Data lab.** `apex/validation/python/apexdata.py` and `data_catalog.json` did not exist at run time, so the raw files were loaded directly, as described in section 1.1.

## 3. Samples

| series | bars | WF origins | WF-dev / holdout origins | holdout period (UTC) |
|---|---|---|---|---|
| NQ, ES, YM, RTY 5m | 16,774-16,787 | 14,654-14,667 | ≈7,330 / ≈7,330 each | 2026-03-09 → 2026-04-15 |
| CL 5m | 16,613 | 14,493 | 7,246 / 7,247 | 2026-03-09 → 2026-04-15 |
| GC 5m | 13,892 | 11,772 | 5,886 / 5,886 | 2026-03-02 → 2026-04-15 |
| NQ, ES, YM, RTY 1h | 6,270-6,271 | 4,650-4,651 | 2,325 / 2,325 each | 2025-11-12 → 2026-04-15 |
| CL 1h | 4,520 | 2,900 | 1,450 / 1,450 | 2026-01-08 → 2026-04-15 |
| BTC 1h | 79,057 | 75,937 | 37,968 / 37,969 | 2020-09-03 → 2025-01-07 |

- Holdout origins per pool: CME 5m 42,459; CME 1h 10,751; BTC 1h 37,969.
- The origins overlap, so the number of independent H-bar windows is about origins/H. At H = 60 that is ≈700 (CME 5m), ≈180 (CME 1h) and ≈630 (BTC).
- There is no BTC 5m file, so BTC appears at 1h only.

## 4. Results: point forecasts (terminal error at t+H, holdout = headline)

**Verdict: 0 of 99 pre-registered tests pass (11 variants × 3 horizons × 3 pools).**
- **MAE (primary) and path-MAE.** No test reaches even a nominal one-sided p < 0.05 before correction. The smallest raw p is 0.28 for MAE and 0.29 for path-MAE, and every Holm-adjusted p is 1.
- **RMSE (secondary).** The only nominal wins are g on BTC at all three horizons: RMSE ratio 0.999 / 0.997 / 0.996 at H = 20 / 60 / 120, raw p 0.030 / 0.020 / 0.050, Holm 0.96 / 0.67 / 1.
  - The gain is a 0.1-0.4% RMSE reduction with no MAE gain (MAE ratio 1.000-1.003). It slightly trims large misses during BTC trends, consistent with BTC's positive fitted momentum coefficient.
  - It is 5-20 times smaller than the 2% practical threshold and does not survive correction.
- **Best holdout MAE ratio:** 0.997, for method c on CME 1h at H = 60 (raw p = 0.28, CI [0.987, 1.007]).
- **The in-sample diagnostic (IS) looks far better than out of sample.** IS shows several Holm-significant "wins", for example:
  - g: CME 1h H = 20, MAE 0.989, Holm 0.003;
  - g: BTC H = 20, RMSE 0.996, Holm 0.001.
  - e: CME 1h H = 60 has an IS MAE of 0.939 (raw p 0.019).

  All of these disappear on the holdout. Fitting and testing on the same period would have produced a false positive.

### 4.1 H = 60 (primary)

Column guide: MAE ratio vs RW [95% block-bootstrap CI] · one-sided DM p, raw (Holm) · symbols with ratio < 1 · RMSE ratio · path-MAE ratio · WF-dev MAE ratio · IS MAE ratio.

| method | CME 5m | CME 1h | BTC 1h |
|---|---|---|---|
| a2 hist. drift | 1.002 [0.993, 1.011] · 0.66 (1) · 1/6 · 1.003 · 1.000 · 1.007 · 1.001 | 1.011 [0.978, 1.042] · 0.74 (1) · 1/5 · 1.015 · 1.008 · 0.948 · 0.952 | 1.002 [0.993, 1.012] · 0.68 (1) · 0/1 · 0.997 · 1.001 · 1.000 · 0.995 |
| b50 OLS | 1.467 [1.359, 1.592] | 1.722 [1.591, 1.863] | 1.434 [1.373, 1.496] |
| b100 OLS | 1.381 [1.257, 1.510] | 1.362 [1.221, 1.506] | 1.268 [1.216, 1.325] |
| b200 OLS | 1.312 [1.184, 1.472] | 1.156 [1.093, 1.229] | 1.182 [1.139, 1.228] |
| bL100 OLS line end | 1.547 [1.393, 1.730] | 1.492 [1.300, 1.701] | 1.402 [1.335, 1.475] |
| c0 engine momentum | 1.121 [1.082, 1.163] | 1.193 [1.133, 1.253] | 1.126 [1.102, 1.150] |
| c fitted momentum decay | 1.002 [1.001, 1.003] · 1 (1) · 1/6 · 1.001 · 1.001 · 1.005 · 1.002 | 0.997 [0.987, 1.007] · 0.28 (1) · 3/5 · 0.997 · 1.001 · 0.999 · 0.995 | 1.006 [1.001, 1.010] · 1 (1) · 0/1 · 0.998 · 1.006 · 1.009 · 1.006 |
| d vol-scaled + clock | 1.006 [1.002, 1.011] · 1 (1) · 0/6 · 1.002 · 1.006 · 1.010 · 1.003 | 0.999 [0.977, 1.024] · 0.47 (1) · 3/5 · 1.004 · 1.001 · 1.004 · 0.995 | 1.008 [0.999, 1.017] · 0.97 (1) · 0/1 · 0.999 · 1.012 · 1.012 · 1.010 |
| e state drift | 1.014 [0.998, 1.030] · 0.97 (1) · 0/6 · 1.010 · 1.012 · 1.018 · 1.006 | 1.021 [0.975, 1.066] · 0.80 (1) · 0/5 · 1.025 · 1.016 · 1.005 · **0.939** | 1.007 [0.996, 1.019] · 0.92 (1) · 0/1 · 0.997 · 1.007 · 1.008 · 0.998 |
| f target bridge | 1.032 [1.013, 1.054] | 1.067 [1.033, 1.104] | 1.031 [1.020, 1.043] |
| g shrinkage blend | 1.000 [0.999, 1.001] · 0.58 (1) · 1/6 · 1.000 · 1.000 · 1.001 · 0.998 | 1.002 [0.996, 1.007] · 0.76 (1) · 3/5 · 1.003 · 1.001 · 0.998 · 0.975 | 1.000 [0.997, 1.004] · 0.56 (1) · 0/1 · 0.997 · 1.002 · 0.999 · 0.998 |

- The b, c0 and f rows show the MAE ratio [CI] only. Each of them has raw p = 1 and Holm p = 1 in every pool.
- Random-walk MAE in ATR units (holdout):
  - CME 5m: 2.68 / 5.10 / 7.93 at H = 20 / 60 / 120;
  - CME 1h: 2.72 / 4.62 / 5.91;
  - BTC: 2.58 / 4.91 / 7.45.

### 4.2 By family, across all horizons (H = 20, 60, 120)

- **b: regression drift extrapolation.** 7% to 118% worse than the RW in every pool and horizon, and in every symbol (0 of 12 symbols below 1 in any cell). It gets worse with a longer horizon and a shorter window: CME 1h H = 120 b50 is 2.176 [1.858, 2.535]. Extending a fitted trend line is the worst choice tested.
- **c0: naive engine-style momentum** (EMA of normalized returns, fixed 12-bar half-life). 6.5% to 23% worse everywhere, with every CI above 1.
- **f: target-aware bridge to the nearest DOL-style level, weighted by the past reach rate.**
  - 2.3% to 6.7% worse, and all 9 pool × horizon CIs exclude 1 on the worse side. Examples: CME 1h H = 60 1.067 [1.033, 1.104]; BTC H = 20 1.042 [1.034, 1.050].
  - It is never better than the RW in any symbol.
  - Shaping the path toward the nearest liquidity level makes the forecast measurably less accurate, even when the shift is discounted by its historical reach rate.
- **e: state-dependent drift** (structure bias × volatility tercile).
  - 0.6% to 4.8% worse out of sample. It is the clearest overfit: on CME 1h at H = 60 it looks 6.1% better in-sample (IS 0.939) and is 2.1% worse on the holdout.
  - The state means are not stable enough to extrapolate.
- **c (fitted decay), d (vol-scaled drift with clock), a2 (historical drift), g (shrinkage).**
  - At H = 60 their MAE ratios are 0.997-1.011, and no difference is significant.
  - Over all horizons and pools they run from 0.997 to 1.022. The only values below 1 are 0.997-0.999 (c and d on CME 1h), and none is significant.
  - The fitted parameters are unstable:
    - The momentum coefficient b of c changes sign by instrument. At 1h it is negative in every NQ and ES block (median −0.20 and −0.27, which is short-term reversal); at 5m its sign is mixed; for BTC it is positive.
    - The κ of d changes sign by instrument: CL 1h −0.34, BTC +0.17, NQ 5m −0.06.
  - **g behaves as designed: it shrinks to almost nothing.** Its fitted weights are 0 in many blocks; YM 5m and GC 5m made exactly zero forecasts on 4,738 and 4,272 holdout origins. The result is a near-RW path with no measurable gain.
- **Best per pool and horizon** (holdout MAE ratio, Holm p):
  - CME 5m: H = 20 a2 1.000 (1); H = 60 g 1.000 (1); H = 120 g 1.000 (1).
  - CME 1h: H = 20 d 0.999 (1); H = 60 c 0.997 (1); H = 120 c 1.004 (1).
  - BTC: H = 20 a2 1.001 (1); H = 60 g 1.000 (1); H = 120 g 1.003 (1).

### 4.3 Power

The CI half-widths of the near-zero methods are:
- ±0.1% for g on CME 5m;
- ±1.0% for c on CME 1h;
- ±2.4% for d on CME 1h;
- ±0.4-1.0% on BTC.

The pre-registered "practically meaningful" threshold is a 2% MAE reduction. An effect of that size would have been detected on CME 5m and BTC. On CME 1h, detection is borderline for the noisiest method (d). The null is therefore informative, not just underpowered.

## 5. Results: directional accuracy at H (holdout)

**No method shows a directional edge**, under either reading of the criterion (Wilson lower bound > 50% in at least 2/3 of symbols, or in every symbol, plus beating always-up with a CI that excludes 0).

- **H = 60, pooled accuracy and always-up rate:**

  | pool | accuracy range of the 11 methods | always-up |
  |---|---|---|
  | CME 5m | 0.482-0.513 | 0.502 |
  | CME 1h | 0.411-0.554 | 0.537 |
  | BTC | 0.497-0.529 | 0.529 |

  - No method beats always-up with a CI excluding 0.
  - On CME 1h several methods are significantly **worse** than always-up:

    | method | diff vs always-up [95% CI] |
    |---|---|
    | b50 | −0.126 [−0.200, −0.044] |
    | f | −0.110 [−0.192, −0.021] |
    | c0 | −0.081 [−0.149, −0.014] |
    | a2 | −0.034 [−0.061, −0.009] |
    | e | −0.025 [−0.050, −0.002] |

- **Per-symbol non-overlapping Wilson intervals with a lower bound above 50%** (only 2 cells out of all methods × symbols at H = 60):
  - CME 1h, method c, YM: 0.744 [0.589, 0.854], n = 39.
  - BTC, method e: 0.540 [0.501, 0.579], n = 633. It does not beat always-up: −0.004 [−0.011, 0.005].
  - Method c on CME 1h was below always-up in WF-dev (0.515 vs 0.588). Both cells are what chance alone produces across this many cells.
- **The always-up rate is not skill.** The 50-54% always-up rates reflect each window's drift. APEX should never present "direction correct x%" for the path.

## 6. Results: path-shape error (MAE over steps 1..H)

- The best path-MAE ratio is 1.000-1.002 in every pool and horizon (g, c or a2). The smallest raw p is 0.29, and every Holm p = 1.
- Across all horizons, the b family is 5-84% worse along the whole path, c0 is 11-21% worse and f is 4-8% worse.
- **No method draws a better path than the flat line at the last close.**

## 7. Results: economic check (secondary; holdout, non-overlapping, after costs)

Costs are round trips in ATR units:
- 5m: NQ 0.045, ES 0.13, YM 0.10-0.13, RTY 0.15, CL 0.065, GC 0.03.
- CME 1h: 0.013-0.05.
- BTC: 0.15.

These costs are small next to the typical absolute move over H, which the RW MAE puts at 2.6-7.9 ATR. Costs are not what blocks an edge.

Of 99 trials, 38 have a positive mean. Three have a CI lower bound above 0; about 2.5 are expected by chance at a 2.5% one-sided tail.

| pool | H | method | mean net / trade (ATR) [95% CI] | trades | DSR |
|---|---|---|---|---|---|
| CME 1h | 60 | c | +1.52 [0.14, 3.15] | 180 | 0.555 |
| BTC 1h | 120 | a2 | +1.37 [0.15, 2.68] | 316 | 0.296 |
| BTC 1h | 60 | e | +0.58 [0.04, 1.21] | 633 | 0.210 |

- **The maximum DSR is 0.555, far below 0.95.** None survives deflation for 33 trials per pool.
- The CME 1h c result rests on 39 trades per symbol over five months. Its MAE ratio is not significant (p = 0.28), and its WF-dev direction was below always-up.
- The BTC a2 result is long-the-historical-drift, which is buy-and-hold in a 2020-2025 bull market.

## 8. Results: uncertainty bands

### 8.1 Pre-registered schemes (holdout, window W = 2000, random-walk centre)

Each cell shows the coverage of [q10, q90] at k = 20 / 60 / 120 (nominal 0.80) · the low / mid / high volatility-tercile coverage at k = 60 · the interval score at k = 60 (ATR units).

| scheme | CME 5m | CME 1h | BTC 1h |
|---|---|---|---|
| U0 empirical per horizon | 0.793 / 0.786 / 0.766 · 0.728 / 0.782 / 0.858 · 26.97 | 0.797 / 0.782 / 0.805 · 0.625 / 0.779 / 0.890 · 22.20 | 0.794 / 0.786 / 0.767 · 0.686 / 0.810 / 0.879 · 27.51 |
| U1 ATR·√k pooled | 0.819 / 0.780 / 0.739 · 0.718 / 0.779 / 0.854 · 26.77 | 0.787 / 0.787 / 0.833 · 0.637 / 0.782 / 0.891 · 21.92 | 0.802 / 0.780 / 0.754 · 0.679 / 0.805 / 0.875 · 27.31 |
| U2 time-of-day clock pooled | 0.822 / 0.794 / 0.779 · 0.830 / 0.803 / 0.745 · 27.08 | 0.746 / 0.768 / 0.813 · 0.764 / 0.776 / 0.763 · 21.49 | 0.800 / 0.783 / 0.759 · 0.757 / 0.792 / 0.806 · 26.31 |
| **U3 per horizon within vol tercile** | 0.786 / 0.777 / 0.757 · 0.788 / 0.768 / 0.771 · 27.25 | 0.786 / 0.778 / 0.794 · 0.741 / 0.801 / 0.785 · 21.29 | 0.789 / 0.768 / 0.744 · 0.766 / 0.772 / 0.768 · 27.64 |
| U4 Gaussian ±1.28·σclk | 0.868 / 0.841 / 0.834 · 0.874 / 0.842 / 0.802 · 26.75 | 0.805 / 0.843 / 0.882 · 0.843 / 0.843 / 0.844 · 21.29 | 0.834 / 0.814 / 0.789 · 0.804 / 0.813 / 0.826 · 25.78 |

**Pass criterion:** coverage within ±5 pp of 80% at every k, and within ±8 pp in every volatility tercile.

| scheme | passes on | notes |
|---|---|---|
| U3 | CME 5m, CME 1h | Fails BTC: k = 120 coverage 0.744. |
| U2 | CME 5m, BTC | Fails CME 1h: k = 20 coverage 0.746, tercile spread 11.8 pp. |
| U4 | BTC only | Over-covers CME by up to 8 pp (0.83-0.88 everywhere except CME 1h k = 20, which is 0.805). Fat tails make ±1.28σ wider than the empirical 80%. |
| U0, U1 | none | Every pool fails on terciles: the worst tercile deviation for the RW centre is 11.5-17.5 pp. |

- **Why unconditional bands fail.** They under-cover in low volatility (0.63-0.73 at k = 60) and over-cover in high volatility (0.85-0.89). Volatility mean-reverts, so ATR-normalized moves are larger after quiet periods and smaller after loud ones.
- **What conditioning on the volatility tercile does.** It removes that bias. The tercile coverage spread at k = 60 falls from 13-27 pp (U0) to 1-6 pp (U3).
- **No scheme passes all three pools.**
- **The centre hardly matters.** Bands around g, c or d have coverage within 1.3 pp of the RW-centred bands in every cell, because those centres are nearly flat.
- **Median.** The q50 exceedance is 0.50-0.51 on CME 5m and BTC for U0/U3. On CME 1h at k = 120 it is 0.41-0.43: the median of past 120-bar moves, taken from the dev period's strong rally, overstated the holdout's moves.

### 8.2 Pre-registered minimum sample (RW, common origins)

The rule is the smallest W with pooled coverage within ±3 pp of 80% and an interval score within 2% of the best W.

| scheme | k = 20 | k = 60 | k = 120 |
|---|---|---|---|
| U0 | 1000 (all pools) | 4000 (CME 5m, BTC), 2000 (CME 1h) | 4000 (CME 5m, BTC), expanding (CME 1h) |
| U1 | 1000 (CME 1h), 2000 (CME 5m), 4000 (BTC) | 2000 (CME 5m, CME 1h), 4000 (BTC) | never qualifies: at W ≥ 1000, coverage is 0.73-0.76 on CME 5m and BTC and 0.81-0.84 on CME 1h |

At W = 100 the coverage is 0.68-0.71 at k = 20 and 0.34-0.41 at k = 120.

### 8.3 Post-hoc sensitivity (NOT pre-registered; exploratory, on an already-seen holdout)

The minimum-W result points to effective sample size. Overlapping k-step residuals are strongly autocorrelated, so a window of W origins holds only about c = W/k independent outcomes. `e1_bands_posthoc.py` re-ran U0 and U3 for the RW centre with W = c·k (per tercile for U3), with c ∈ {5, 10, 17, 25, 33, 50}: 36 cells per pool. On CME 1h the larger c values exceed the history, so they were not testable there.

Each cell gives the range of pooled holdout coverage across the pools where that c was testable. The tercile columns give the range over all terciles, k values and pools.

| c = W/k | U0c coverage (k = 20 / 60 / 120) | U0c tercile range | U3c coverage (k = 20 / 60 / 120) | U3c tercile range |
|---|---|---|---|---|
| 5 | 0.682-0.712 / 0.698-0.700 / 0.700-0.725 | 0.576-0.812 | 0.710-0.718 / 0.731-0.755 / 0.742-0.787 | 0.692-0.814 |
| 10 | 0.742-0.751 / 0.752-0.759 / 0.751-0.761 | 0.613-0.865 | 0.745-0.756 / 0.766-0.776 / 0.762-0.772 | 0.709-0.791 |
| 17 | 0.767-0.771 / 0.764-0.775 / 0.766-0.803 | 0.624-0.886 | 0.769-0.776 / 0.779-0.792 / 0.771-0.775 | 0.742-0.813 |
| 25 | 0.777-0.779 / 0.782-0.786 / 0.776-0.785 | 0.636-0.883 | 0.779-0.784 / 0.782-0.797 / 0.779 | 0.763-0.820 |
| 33 | 0.783-0.788 / 0.783-0.785 / 0.779-0.780 | 0.628-0.889 | 0.785-0.789 / 0.785-0.799 / 0.778 | 0.758-0.830 |
| 50 | 0.787-0.790 / 0.790-0.796 / 0.781-0.787 | 0.676-0.885 | 0.790-0.791 / 0.786 / 0.781 | 0.773-0.801 |

- **Coverage depends on c, not on W.** Coverage reaches 0.776-0.799 once c ≥ 25.
- **At c = 5 an "80%" band covers only 0.68-0.79**, and U0c only 0.68-0.73.
- **A residual 1-2 pp under-coverage at k = 120 persists** even at c = 50 (0.781-0.787). Past quantiles do not foresee future volatility shifts.
- **Tercile balance holds at large c.** U3c keeps every tercile within 0.74-0.83 for c ≥ 17, and within 0.76-0.83 for c ≥ 25. U0c stays at 0.61-0.89 for c ≥ 10.
- Treat these numbers as design guidance, not as confirmed results.

## 9. Deviations and disclosures

1. **Active-slot calendar.** Section 1 defines the active slots (used by method d and by bands U2/U4) from "the first 2000 bars". For CME 1h, T0 = 1500, so origins 1500-1999 (WF-dev only) used a calendar built partly from later bars. It records only which hours have bars, never prices, and it does not touch the holdout.
2. **Band inputs for f and g.** For f and g, the path at the U1/U2 pooling horizons {10, 40, 90} is taken from the smallest pre-registered H that contains them. The H-specific reach rate (f) and weights (g) therefore differ slightly from the terminal-horizon path. This affects only the U1/U2 bands of f and g, and none of the headline rows.
3. **U3 window.** U3 uses W/3 = 667 per tercile at W = 2000; section 1 did not fix this window. It is the cause of U3's BTC k = 120 under-coverage (c ≈ 5.6; see 8.3).
4. **Directional criterion.** "Per-symbol Wilson lower bound > 50%" was evaluated two ways: in ≥ 2/3 of symbols, and in every symbol. Both fail for every method.
5. **Pooled series.** Pooled DM and directional series use timestamps where at least half the pool's symbols have a value.
6. **Data loading.** The raw files were used because the data-lab loader did not exist. GC 1h is excluded; GC 5m comes from the clean 1-minute file.
7. **Rerun.** The interrupted evaluation was rerun from the same code. The only edit was replacing the pandas `sum(1)`/`mean(1)` positional-argument calls with `axis=1`, which changes no value.
8. **Section 8.3 is post-hoc.** It reuses the holdout and was added after section 8.1 was seen. It is reported as exploratory.
9. **Test counts.**
   - Confirmatory point tests: 99 (MAE primary; RMSE and path-MAE secondary, 99 each).
   - Directional cells: 99. Economic trials: 99.
   - Band cells: 405 (5 schemes × 9 centres × 3 k × 3 pools, descriptive).
   - Minimum-sample grid: 2 schemes × 2 centres × 3 k × 7 W × 3 pools.
   - Post-hoc band cells: 108.

## 10. Answer to the question

- **No candidate path method beats a zero-drift random walk out of sample.** The pre-registered 99 tests cover NQ, ES, YM, RTY, CL and GC at 5m, NQ, ES, YM, RTY and CL at 1h, and BTC at 1h, at horizons of 20, 60 and 120 bars.
- **That holds on every error measure.**
  - Terminal MAE: the best is 0.997, p = 0.28.
  - RMSE: the best is 0.995. The only nominal wins, g on BTC at 0.996-0.999, are not significant after correction (Holm ≥ 0.67) and are negligible in size.
  - Path-shape error: the best is 1.000.
- **Direction and economics show no edge.**
  - Direction at H: no method beats 50% or always-up.
  - After costs: the maximum DSR is 0.555.
- **Methods that are worse than the RW:**

  | method | how much worse | significance |
  |---|---|---|
  | Regression extrapolation (b family) | 7-118% | significant |
  | The engine's current momentum style (c0) | 6-23% | significant |
  | The target-aware bridge toward the nearest liquidity level (f) | 2-7% | significant in all 9 cells |
  | State-dependent drift (e) | 1-5% out of sample | not stated; it looked 6% better in-sample |

- **The prior in section 1 held.** It predicted "no drift method passes".
- **Part of the prior did not hold.** It predicted the volatility-clock bands would calibrate best. In fact, conditioning the empirical quantiles on the volatility tercile (U3) gives the most consistent calibration across volatility regimes, and the clock version (U2) fails on CME 1h.
- **Uncertainty is the part that can be estimated honestly.** Use rolling, horizon-specific empirical residual quantiles, conditioned on the volatility tercile. Coverage is within about 2-3 pp of nominal once the window holds at least about 25 independent horizons, with a small residual under-coverage at the longest horizon.

## 11. Design implications for APEX (spec §14, §15, §25)

1. **Default path method: zero drift, a flat median at the last close.**
   - Nothing tested improves on it.
   - The shrinkage blend g converges to it anyway, and spec §25 says to prefer the simpler model.
   - Do **not** ship:
     - regression-line extension (b*);
     - the EMA-momentum projection with a fixed decay (c0, the current engine style);
     - a path bent toward the DOL target (f);
     - state-mean drift (e).

   Each of these made the path measurably worse out of sample.
2. **What the "one forward path" shows: a scenario cone, not a prediction.**
   - Draw the centre line at the band median. Empirically this is almost exactly the last close; the rolling q50 offset can be used, and it is ≈ 0.
   - Draw the q10-q90 cone for k = 1..H around it.
   - Colour the cone green or red by the current **bias state** from the structure/DOL modules. The label must say what the colour means, for example "Bias: bullish (structure) · drift forecast: none detected · 80% range".
   - **The cone carries the visual weight required by spec §14.** At H = 60 the 80% band spans about 14-16 ATR (±7-8 ATR), so it is large and visible without inventing drift.
3. **The DOL target as a separate overlay.**
   - It may be drawn as a labelled conditional scenario ("if bias holds → target X"), never as the expected path.
   - Optionally state where the target sits inside the cone, e.g. "target at the 78th percentile of 60-bar outcomes". This is an end-of-horizon quantile. A touch or reach probability must come from a separately calibrated model (spec §15), not from this cone.
4. **Uncertainty method (default): U3 conditional empirical quantiles.**
   - At each anchor horizon j, store the realized z = (C_{s+j} − C_s)/ATR14_s, tagged with the volatility tercile at origin s. Store it only once it is realized, at bar s + j ≤ t.
   - Tercile: the percentile rank of ATR14/close over the trailing 500 bars, with cuts at 1/3 and 2/3.
   - Band at k = C_t + ATR14_t × quantile_{10,50,90}(z_k | the current tercile).
   - Default window per tercile: W_g = 33·H realized origins (1,980 for H = 60). Implement it with a ring buffer and `array.percentile_linear_interpolation`, evaluated on the last bar only.
   - For a continuous cone, use anchors at, say, k ∈ {H/6, H/3, H/2, 2H/3, 5H/6, H} and interpolate linearly in √k between them. **This interpolation was NOT RUN, so it needs a check.**
   - Fallback when per-tercile history is too short: U0 (unconditional, W = 33·H), labelled "not regime-adjusted". At W = 2000 its coverage is 2-18 pp too low in the low-volatility tercile and 4-9 pp too high in the high-volatility tercile.
   - Do not use Gaussian ±1.28σ or plain ATR·√k bands as the default (U4 and U1 fail, see 8.1). The time-of-day clock (U2) is an optional future refinement only. It fails on CME 1h and needs a learned slot table.
5. **Minimum sample before bands are shown: count independent horizons, n_eff = W/H.**
   - **n_eff ≥ 25** in the current tercile (W_g ≥ 25·H): show the cone normally.
     - H = 60 needs ≥ 1,500 realized origins per tercile, roughly 4,500 + 500 + H bars of history.
     - H = 120 needs ≥ 3,000 per tercile, roughly 9,000+ bars.
   - **10 ≤ n_eff < 25:** show it dashed and labelled "provisional". Expected coverage is about 0.74-0.80.
   - **n_eff < 10:** do not draw a band. Expected coverage is 0.68-0.79, typically 0.70-0.75, and calling such a band "80%" would be misleading. Show only a "not enough history for a range" note.
   - With the U0 fallback the same thresholds apply to the total window, without the per-tercile split.
6. **Horizon defaults.**
   - Keep H = 60 as the default; drift is equally absent at 20, 60 and 120.
   - Expect H = 120 cones to run about 1-2 pp narrow even with long history. One option is to widen the k ≥ 90 quantiles by a small documented factor after live validation. Otherwise label the cone "≈78% at the longest horizon".
7. **Live self-check (spec §15 honesty).**
   - The indicator should keep its own ledger of past cones and display realized coverage, e.g. "last 200 cones: 77% inside the 80% band".
   - This lets the user see calibration on their own symbol and timeframe.
   - **The Forecast Quality Score (spec §13 F) should be built from n_eff and this live coverage.** It must not be built from directional agreement: directional skill at H was not detected.
8. **Never label path direction with a probability or accuracy figure.** The measured direction-at-H accuracy is 50% ± noise. A bias label is a description of structure, not a forecast of the next H bars.
9. **Promotion rule for future drift ideas.** A new drift component (for example from E3, E7 or E9) may replace zero drift only if it passes section 1.5 on this harness. That means: Holm-corrected pooled DM on the holdout, a majority of symbols better, the same sign in WF-dev, and at least a 2% MAE gain to be called meaningful.

## 12. Caveats

- **Short CME history.** The 5m data covers about 12 weeks, of which the holdout is about 5.5 weeks. It includes the March 2026 oil shock and the related volatility. The 1h data covers about 13 months. BTC covers 9 years but is a single asset. Each instrument has one chronological holdout, so the result belongs to one regime per instrument.
- **Unknown roll method.** The roll construction of the continuous futures in the source clone is not documented. Roll jumps, if present, are dampened by ATR normalization but not removed.
- **Approximate DM variance.** DM with Bartlett HAC at lag H only approximates the variance for overlapping forecasts and can be slightly anti-conservative. That does not matter here: no test is near significance.
- **Fixed structure parameters.** Structure and target parameters were fixed: pivot length 5, the target candidate set, and the distance buckets. Other definitions could behave differently. However, every family failed in the same direction, and the study's broader finding ("direction ≈ random walk, volatility structured") predicts this.
- **Post-hoc band evidence.** The band-window rule (8.3) and the U3 recommendation lean on post-hoc analysis of a seen holdout. They should be confirmed by APEX's live self-check (implication 7) and in the Phase-6 validation.
- **NOT RUN:**
  - interpolation of the cone between anchor horizons;
  - bands for BTC at 5m (no data);
  - GC 1h (corrupted, not repaired);
  - a cross-check of the Pine implementation against this Python reference.

## 13. Reproduction

All scripts are in `apex/validation/python/experiments/E1_forecast_paths/`. Outputs go to `out/`, which is git-ignored.

```
V=<venv with numpy 2.5.5, pandas 3.1.1, scipy 1.18.1>/bin/python
nice -n 10 $V -I e1_verify.py         # data, timezone, GC integrity, truncation (no-lookahead) tests
nice -n 10 $V -I e1_run.py            # walk-forward forecasts for 12 series   (~25 s)
nice -n 10 $V -I e1_eval.py           # metrics -> out/results.json, out/tables.md  (~80 s)
$V -I e1_summary.py                   # pre-registered verdicts -> out/summary.md
nice -n 10 $V -I e1_bands_posthoc.py  # exploratory band-window sensitivity -> out/bands_posthoc.json
```

Data paths are set at the top of `e1_run.py`: the CME clone and BTC 1h in the session scratchpad. The bootstrap RNG seed is 20261127.
