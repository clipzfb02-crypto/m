# E4 · Volatility regime, trend regime and probability calibration (R6 + R8)

Key: `E4_regime_calibration`. Code: `apex/validation/python/experiments/E4_regime_calibration/`. Outputs: `.../out/` (git-ignored).

Status: PRE-REGISTRATION written 2026-11-27 ~09:55 UTC, before any result of this experiment was computed. The results section is appended below it later; nothing in this section is edited after the results are seen (any later change is listed in "Deviations from the pre-registration").

Status update 2026-11-28: the first attempt was interrupted by a usage limit after its scripts had run once. On resume the code was audited, two data defects were handled, the unregistered R4 changes were listed, the missing pre-registered pieces were added (R4 cross-market prior and grid design, Holm tables, OOS persistence), and everything was re-run. Sections 2-7 below hold the deviations, the results and the design implications. Section 1 is unchanged.

**One-paragraph summary.**
- Volatility states are real, persistent states. ATR-percentile states last 1.6-3.9× longer than in shuffled data.
- Bollinger-bandwidth "compression" is barely more persistent than chance.
- The states carry only small out-of-sample information about the absolute next-20-bar range (R² ≤ 0.085), and none at 60 bars.
- Conditioning the hit-probability surface on the volatility state removes a ±4-8 pp state-specific bias and lowers log loss by 0.4-1.5%. It fails the pre-registered "marginal reliability falls" leg, because that metric cannot see state-specific bias, so R2 is **mixed**.
- A single surface in a blended volatility unit, sqrt(ATR14·ATR100), does as well as or better than regime rows on 1h and BTC, and is simpler.
- Compression breakouts do not behave differently from expansion extensions in failure rate or follow-through (R3 **not supported**).
- On-chart calibration is feasible only with a shipped prior: per-bucket frequencies need about 100-200 resolved outcomes for ±10 pp, and sample size must be counted in bars, not probes.
- Trend/range labels are no more persistent than on direction-randomised data, and do not set the sign of momentum vs reversion on CME. BTC ER is a near-miss after Holm (R5 **not supported**).

---

## 1. Pre-registration (frozen before results)

### 1.0 Common setup

Data (raw files; `apexdata.py` did not exist when this started):

- `1h` family: ES, NQ, RTY, YM 1-hour bars, 2025-03-21 to 2026-04-15, UTC timestamps (the daily halt is the missing 21:00/22:00 UTC hour).
  - GC 1H is excluded (the study found it corrupted).
  - CL 1H is included only if its roll-jump count passes the integrity check below; otherwise it is excluded and the check result is reported.
- `5m` family: ES, NQ, RTY, YM, CL, GC 1-minute bars (2026-01-20 to 2026-04-15) resampled to 5-minute bars, subject to the same integrity check.
- `btc` family: BTC 1-hour bars, 2016-2025.
- Integrity check: the count of bars with |open − previous close| > 4 × ATR14 or |close − previous close| > 6 × ATR14. A file with > 0.5% of bars flagged, or with any single jump > 15 × ATR14, is reported and excluded from that family.
- Time of day: the America/New_York clock (exact DST via zoneinfo) for CME, and UTC for BTC.

Indicators (all use bars ≤ t only):

- ATR14 = Wilder RMA of the true range. ATR100 is the same with length 100.
- RV20 = population std of 20 log close-to-close returns.
- BBW = 4·stdev(C, 20)/SMA(C, 20).
- Percentile rank uses the Pine `ta.percentrank` convention: 100 × (# of the previous W values ≤ current)/W, with **W = 500**.
- TOD-deseasonalised ATR (intraday families only, the 4th definition): TR_t / mean(TR at the same TOD bucket over the trailing 20 sessions, excluding t), smoothed by RMA 14, then percentile-ranked. The buckets are 30 minutes (5m) or 1 hour (1h).

Hysteresis classifier (3 states: C = compressed, N = normal, E = expanded) on a percentile series p:

- Raw (no hysteresis): C if p < 20, E if p > 80, else N.
- Hys-A (the default, pre-registered as the APEX candidate): enter C at p ≤ 20, leave C at p > 30; enter E at p ≥ 80, leave E at p < 70; minimum dwell 5 bars.
- Hys-B (wide): enter 15/85, exit 35/65, dwell 10.

Splits:

- Chronological: in-sample (IS) is the first 60% of each series after a 600-bar warm-up; out-of-sample (OOS) is the remaining 40%.
- IS samples whose horizon reaches into OOS are purged (embargo H bars).
- All model fitting uses IS only. All headline numbers are OOS; IS numbers are reported separately.

Horizons: **H = 20 and H = 60 bars** for every family (spec 14: 20-120 bars, default 60).

Uncertainty:

- Moving-block bootstrap over calendar-day blocks for intraday CME (pooled CME families cluster by calendar day across symbols, the conservative choice), and over 24-bar blocks for BTC. Block length is at least H. 2,000 replicates; 95% percentile CIs.
- Wilson CIs for proportions.
- Holm correction within each research question's primary family of tests.

Random-walk nulls:

- Sign-flip null: random signs on close-to-close returns, bar shapes kept. It keeps volatility clustering and destroys direction.
- Shuffle null: bars permuted. It destroys both.

### R1 · Volatility-regime classification

- Hypothesis R1: all three volatility definitions (ATR-pct, RV-pct, BBW-pct; plus TOD-deseasonalised ATR-pct intraday) give persistent states that carry OOS information about the next-H realised range, and hysteresis cuts switching with little information loss.
- Outcomes:
  - Y = log(FwdRange_H / ATR14_t), primary (engine units).
  - Ya = log(FwdRange_H / ATR100_t), secondary (absolute level).
  - FwdRange_H = max(High[t+1..t+H]) − min(Low[t+1..t+H]).
- Metrics:
  - Persistence: mean dwell (bars), switches per 1,000 bars, P(state_{t+H} = state_t).
  - Information: OOS R² = 1 − MSE(state-mean model)/MSE(pooled IS mean), with means fitted IS. A continuous comparator is a linear fit on the raw percentile.
  - Persistence and information are compared with the shuffle null.
- Baseline: the pooled IS mean.
- Pass: OOS R² > 0 with the 95% block-bootstrap CI excluding 0 (Holm over the 3-4 definitions × 2 horizons per family). Hysteresis "costs little" if Hys-A keeps ≥ 80% of the Raw R² while cutting switches by ≥ 50%.
- Variants: 4 definitions × 3 classifiers × 2 horizons × 2 outcomes per family.

### R2 · Does the volatility regime improve calibration of "level reached within H"?

- Probes: at every bar t (stride 1 for 1h and BTC, stride 2 for 5m), levels at d ∈ {0.5, 1, 1.5, 2, 3, 4, 6} × ATR14_t above and below C_t.
  - Outcome y = 1 if max(High[t+1..t+H]) ≥ C_t + d·ATR14_t (up), or min(Low) ≤ C_t − d·ATR14_t (down).
  - Sides are pooled (direction-free).
- Models (empirical first-passage surfaces fitted IS):
  - P0 pooled: survival of the normalised excursion e = excursion/ATR14_t.
  - P1 regime: one survival per Hys-A ATR-pct state, partially pooled toward P0 with m = 200 bar-equivalents.
  - P2 regime + TOD clock: as P1, with distances in clock-scaled units d/s_t.
    - s_t = sqrt(mean_{j=1..H} c[b(t+j)] / mean_{j=0..13} c[b(t−j)]).
    - c[b] = (IS mean of TR/ATR100_{t−1} in bucket b)², normalised to an IS mean of 1. Future bucket times are the real next bar timestamps, which Pine knows via `time(..., bars_back = -j)`.
  - Exploratory comparators: P1b (TOD clock alone), P3 (blended unit u = sqrt(ATR14·ATR100), the study's best non-clock design), P4 (blended + TOD).
- Metrics (OOS):
  - Brier score.
  - Log loss.
  - ECE (10 equal-width bins).
  - Reliability slope and intercept (logistic fit of y on logit p).
  - Murphy decomposition BS = REL − RES + UNC (10 bins).
  - ΔLL% and ΔBrier vs P0 with block-bootstrap CIs.
- Baseline: P0 (itself the study's distance-matched baseline, which is already near-calibrated).
- Pass:
  - P1 "improves calibration" if the pooled-family OOS ΔLL < 0 with the CI excluding 0 in ≥ 2 of 3 families at both horizons, AND the REL component falls.
  - The same rule applies to P2 vs P0 and P2 vs P1.
  - Holm over 3 comparisons × 3 families × 2 horizons.

### R3 · Breakout from compression vs extension in an expanded regime (spec 9)

- Event: the first close beyond the 20-bar Donchian channel.
  - Up break: C_t > max(High[t−20..t−1]) while C_{t−1} ≤ max(High[t−21..t−2]). Down breaks mirror this.
  - The state is the Hys-A ATR-pct state at t−1.
  - Secondary: a 50-bar channel.
- Outcomes (in the break direction):
  - fail5: a close back inside the channel (beyond the broken level) within 5 bars. Its distance-matched mirror null, ext5, is a close ≥ C_t + (C_t − level) within 5 bars, which is equally likely under a symmetric random walk.
  - failH: re-entry within H.
  - asym = (MFE_dir − MFE_opp)/u over H, with null 0.
  - net = dir·(C_{t+H} − C_t)/u.
  - u = ATR14_{t−1} (primary); u = sqrt(ATR14·ATR100) (secondary).
- Hypotheses:
  - R3a: fail5 differs between C and E states.
  - R3b: asym differs between C and E states.
  - R3c: in either state, fail5 − ext5 ≠ 0 (no edge = 0).
- Horizons: H = 20 primary, H = 60 secondary. IS and OOS reported separately.
- Pass: the C − E difference with the 95% CI excluding 0 in OOS for the pooled family, the same sign in IS, Holm over 3 families × 2 primary outcomes.

### R4 · Online calibration feasibility for Pine

- Stream simulation:
  - Independent streams of 3,000 bars (1h CME, 5m CME) or 5,000 bars (BTC), started at non-overlapping offsets.
  - Each bar issues probes at the R2 distance grid (sides pooled; one probe per side per bucket per bar, as an on-chart ledger would).
  - The forecast is made at t. The outcome resolves at the touch bar (hit) or at t+H (miss), and is applied only then.
- Pipelines:
  - (a) Beta-Binomial per distance bucket. Prior Beta(m0·p0(d), m0·(1 − p0(d))) with the Brownian reflection prior p0(d) = 2Φ(−d/(0.625·√H)) (σ_bar = ATR/1.6, the Brownian range constant). m0 ∈ {0 (raw, 0.5 until data), 10, 50}.
  - (b) The pooled surface from OTHER symbols of the same family (cross-market prior), then online binned recalibration (10 bins) or isotonic (PAV) in a bounded buffer of the last N = 1,000 resolved probes, applied once the buffer holds ≥ 200.
- Truth: the leave-stream-out hit rate per bucket (same symbol excluded period, plus same-family other symbols).
- Metrics vs the resolved-sample count n:
  - CE_truth(n) = the probe-weighted mean |p_model − p_truth| over buckets.
  - The prequential ECE.
  - The empirical 95% half-width of the per-bucket estimate across streams (1.96 × SD) vs the nominal Beta half-width.
- Readouts:
  - The n at which the median and the 90th-percentile CE_truth < 5 pp.
  - The n at which the empirical half-width < 10 pp.
  - The design effect.
- Recommendation: minimum-n rules for showing "probability" vs "Draw Score".

### R5 · Trend / range / transition classification

- Measures:
  - ER20 (Kaufman).
  - ADX14.
  - VR(q = 4, w = 96), with the Hurst proxy h = 0.5 + ln(VR)/(2 ln 4).
  - Each is percentile-ranked (W = 500). TREND: enter > 70, exit < 60. RANGE: enter < 30, exit > 40. Otherwise TRANSITION. Dwell 5. A Raw variant has no hysteresis.
  - Secondary: the absolute thresholds ER ≥ 0.40 and ADX ≥ 25.
- Stability: dwell, switches per 1,000 bars, P(same at t+H), each vs the sign-flip null.
- Outcome: y_h = sign(C_t − C_{t−20}) · (C_{t+h} − C_t)/ATR14_t. Positive is momentum; negative is mean reversion. h = 20 primary, h = 60 secondary.
- Hypothesis R5: E[y | TREND] − E[y | RANGE] > 0 OOS.
- Pass: the OOS difference > 0 with the CI excluding 0 in the pooled family, the same sign IS, and beyond the sign-flip null band (20 seeds). Holm over 3 measures × 3 families × 2 horizons.

### Number of variants (declared)

- R1: 4 × 3 × 2 × 2 per family.
- R2: 6 models × 2 horizons.
- R3: 3 states × 2 channels × 2 horizons × 2 units.
- R4: 3 priors + 2 recalibrators.
- R5: 3 measures × 2 classifiers (+ 2 absolute) × 2 horizons.
- All are reported; none is dropped for its result.

---
