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
