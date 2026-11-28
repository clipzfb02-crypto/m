# E9_momentum_factors: trend / momentum redundancy, consolidated factors, out-of-sample value, RSI divergence (R6)

Key: `E9_momentum_factors`. Code: `apex/validation/python/experiments/E9_momentum_factors/`. Outputs: `.../out/` (git-ignored).

Status: PRE-REGISTRATION written 2026-11-27 ~09:56 UTC, before any feature or outcome of this experiment was computed. Only data formats were inspected: columns, time zones, row counts, gaps and roll candidates. The SHA-256 of section A is stored in `out/prereg.sha256` with a UTC timestamp before the first run. Results are appended in section B. Any change from section A is listed in section C ("Deviations").

Prior knowledge used to write this (not re-tested here, cited):
- `quant_regime.final.md` (study): trend/range labels are not persistent states at DOL horizons; ER20 ≥ 0.40 fires on ~16% and ADX ≥ 25 on ~38% of random-walk bars; ADX keeps corr ≈ 0.22 at 28 bars even on a random walk; signed ER, EMA distance and +DI−−DI never improve OOS log-loss by more than 0.25%; rolling VR/Hurst are noise at chartable windows (SE of VR(4) on 96 bars ≈ 0.19).
- `bias_dol.final.md`: the engine's hard-coded structure/momentum side vote has coin-flip skill and costs 3.8-8.3 pp of first-touch accuracy versus first-passage geometry.
- `price_action.final.md`: chasing a leg at its extreme is not supported; momentum-type side votes carry no information.
- Literature in the study: trend vs reversion depends on time scale, with small coefficients (Safari & Schmidhuber 2025); intraday momentum is a session-timing effect (Gao et al. 2018; Baltussen et al. 2021).
- E2 (`E2_signals.md`) pre-registers trading tests of a STRUCT+MOM composite with costs; E4 (`E4_regime_calibration.md`) pre-registers regime persistence (ER20, ADX, VR) and their trend/range outcome. **E9 does not repeat those**: it measures redundancy between the trend/momentum features themselves, the information coefficient of each feature and of consolidated factors, the incremental value over a trend-only baseline, the vote-inflation effect, and RSI divergence. E9 reuses E4's regime classifier definitions so the results line up.

Prior expectation, written down before testing: the features are highly redundant (2-3 effective dimensions); OOS ICs are small (|IC| < 0.03) and unstable in sign across instruments; counting redundant features as votes inflates apparent confidence without adding information; RSI divergence does not beat the same-type non-divergent pivot. A null result is an acceptable outcome.

---

## A. PRE-REGISTRATION (frozen)

### A1. Data (15 datasets, 3 asset groups)

| ID | Group | Source | Period | Notes |
|---|---|---|---|---|
| NQ_L5m, NQ_L15m, NQ_L1h | CME index | `i2/dl/data_src/data/Dataset_NQ_1min_2022_2025.csv` resampled | 2022-12-26 → 2025-12-11 | ET wall-clock, bar-close-labelled, shifted −1 min to open time (as E2). Back-adjusted continuous; 1,048,575 rows (Excel cap), months complete through 2025-11. |
| NQ_5m26, ES_5m, YM_5m, RTY_5m | CME index | `amt_data/cme/<SYM>/<SYM>_1min_*.csv` → 5m | 2026-01-20 → 2026-04-15 | UTC. Panama-adjusted at the roll bar 2026-03-15 22:00 UTC (E2 A6 list). |
| ES_1h, YM_1h, RTY_1h | CME index | `amt_data/cme/<SYM>/<SYM>_1h_*.csv` | 2025-03-21 → 2026-04-15 | UTC. Panama-adjusted (full reopen gap subtracted from all earlier prices) at the 4 roll bars identified in E2 A6: 2025-06-08 22:00, 2025-09-01 00:00, 2025-12-14 23:00, 2026-03-15 22:00 UTC. NQ 1h CME file not used (NQ_L1h covers NQ 1h with a back-adjusted source). |
| 6E_5m, 6B_5m | FX futures | `smt_data/cme/<SYM>/<SYM>_5min_*.csv` | 2026-03-08 → 2026-04-15 | UTC. No roll jump visible (largest non-weekend gap < 5 ATR5m). Short sample: low power, flagged. |
| BTC_1h, BTC_4h, BTC_1d | Crypto | `classic_tools/btc_1h.csv` (4h, 1d resampled UTC) | 2016-01-01 → 2025-01-07 | UTC spot. |

Excluded: GC (1h and 1min interleave two contract months: E4 data_check 2.1% flagged bars, E3 qc 80-101 jump-and-back bars); CL (1h has 7-23-day holes; monthly rolls not identifiable in 1min). Resampling is left-labelled on the clock, in ET for the NQ_L family and in UTC for the others (1h buckets in UTC equal ET buckets except for DST-free offsets; immaterial for 5m).

Session day (VWAP anchor and RTH flag): CME and FX = the ET date of (bar open + 6 h) (Globex opens 18:00 ET); BTC = UTC date. For BTC_1d the VWAP anchor is the ISO week instead of the day. RTH = bar open in [09:30, 16:00) ET (CME index only).

Warm-up: the first 600 bars of every dataset are dropped from all statistics.

### A2. Features at the close of bar t, from bars ≤ t only

A_t = Wilder ATR(14) (RMA of true range). E_k = EMA(close, k), α = 2/(k+1). RMA = Wilder smoothing. All `/A` divisions use A_t of the same bar.

Directional (signed) features, 22:
| # | Name | Formula |
|---|---|---|
| 1 | stack | sign(C−E20) + sign(E20−E50) + sign(E50−E100) + sign(E100−E200) ∈ {−4..4} |
| 2-5 | slope20, slope50, slope100, slope200 | (E_k,t − E_k,t−5) / (5·A_t) |
| 6 | sep20_50 | (E20 − E50)/A |
| 7 | sep50_200 | (E50 − E200)/A |
| 8 | dist20 | (C − E20)/A |
| 9 | dist200 | (C − E200)/A |
| 10 | rsi | RSI(14, Wilder) − 50 |
| 11 | macd | (EMA12 − EMA26)/A |
| 12 | macdh | (MACD − EMA9(MACD))/A, with MACD = EMA12 − EMA26 in price units |
| 13 | roc10 | (C_t − C_t−10)/A |
| 14 | roc40 | (C_t − C_t−40)/A |
| 15 | didiff | +DI14 − −DI14 (Wilder DMI) |
| 16 | tstat20 | OLS t-statistic of the slope of C on bar index over the last 20 bars |
| 17 | tstat50 | the same over 50 bars |
| 18 | vwapdev | (C − VWAP)/A; VWAP = Σ hlc3·vol / Σ vol since the session anchor (equal weights if the anchor's volume sum is 0) |
| 19 | ser20 | (C_t − C_t−20) / Σ_{j=t−19..t} |C_j − C_j−1| (signed Kaufman efficiency) |
| 20 | acc20 | slope20_t − slope20_t−5 |
| 21 | accroc | roc10_t − roc10_t−10 |
| 22 | dmacdh | macdh_t − macdh_t−5 |

Unsigned (strength / persistence), 3: `adx` = ADX14 (Wilder); `er20` = |ser20|; `vr` = VR(q = 4, w = 96) as in E4 (`vr_hurst`).

Non-momentum comparator (for the vote-inflation demonstration): `dol` as in E2 A2, simplified to swing levels: confirmed pivots with p = 3 (bar i is a swing high if H_i > max(H_i−3..i−1) and H_i ≥ max(H_i+1..i+3), usable from bar i+3); buy-side candidates = the 5 most recent confirmed swing highs not yet traded through (H ≥ level removes it); d_up = (nearest candidate above − C)/A, capped at 10 (10 if none); d_dn mirrors with swing lows; dol = (d_dn − d_up)/(d_dn + d_up).

Normalisation for factors: n(x) = clip(x / sqrt(SMA(x², 500)), −3, 3) (causal rolling RMS scale, sign preserved, no centring).

### A3. Outcomes
- y_H = (C_t+H − C_t)/A_t, **H = 20 bars (primary)** and H = 60 (secondary).
- For unsigned features: y_cont,H = sign(C_t − C_t−20)·y_H (continuation of the 20-bar move).
- Robustness only: entry at O_t+1 instead of C_t (H = 20).

### A4. Splits
IS = bars [600, cut − H), OOS = [cut, n − H), cut = 600 + ⌊0.6·(n − 600)⌋ (purge of H bars at the boundary, as E4). Everything fitted (β, OLS weights, cluster definitions, PCA loadings) uses IS only. All headline predictive numbers are OOS; IS is reported beside them.

### A5. Regimes (causal, E4 definitions)
- Volatility: E4 Hys-A on the 500-bar percentile rank of ATR14 (enter C at ≤ 20, leave at > 30; enter E at ≥ 80, leave at < 70; dwell 5) → C / N / E.
- Trend: E4 R5 on the 500-bar percentile rank of ER20 (TREND enter > 70, exit < 60; RANGE enter < 30, exit > 40; dwell 5) → RANGE / TRANS / TREND.
- Session (CME index only): RTH vs ETH by the bar-open time.

### A6. Redundancy analysis (IS only) — question Q1
1. Spearman correlation matrix of the 22 directional features per dataset (IS), plus the 3 unsigned features against |·| of the directional ones. Report the median across datasets and the min-max range.
2. PCA of each dataset's Spearman matrix: explained-variance ratios, number of components for 80% and 90%, participation ratio N_eff = (Σλ)²/Σλ².
3. Average-linkage hierarchical clustering on distance 1 − |median ρ|; clusters at cut 0.3 (members correlate ≥ ~0.7) and 0.5.
- **"Redundant pair"**: median IS |ρ| ≥ 0.7 with |ρ| ≥ 0.5 in every dataset.
- Expected (not a pass/fail): the EMA stack, slopes and separations fall in one or two clusters.

### A7. Consolidated factors — question Q2
A-set (a priori, the recommendation candidates):
- **TREND** = mean(n(stack), n(sep50_200), n(slope50), n(tstat50), n(roc40)).
- **MOMCHG** = mean(n(acc20), n(accroc), n(dmacdh)).
- **STRETCH** = mean(n(dist20), n(rsi), n(vwapdev)) − β_S·TREND, with β_S = OLS slope of the bracket on TREND fitted on the pooled IS of all 15 datasets (equal weight per dataset), then frozen.
- "Orthogonal enough": median IS |Spearman ρ| between A-set factors ≤ 0.3.

B-set (data-driven, IS only, for comparison): (i) cluster-mean factors from the cut-0.3 clustering (mean of n(member), members sign-aligned to the cluster's first member); (ii) the first 3 principal components of the pooled IS correlation matrix of n(x), applied as fixed loadings.

### A8. Predictive value — question Q3 (OOS, per dataset)
- **T1**: Spearman IC of each of the 22 directional features, the trend-only baseline sign(E20 − E50) (= E2 B1) and dol vs y_H; of the 3 unsigned features vs y_cont,H.
- **T2**: IC of each A-set and B-set factor vs y_H.
- **T3**: IC of TREND, MOMCHG, STRETCH within each volatility regime, trend regime and session (descriptive; Holm within each factor × dataset over its regime cells).
- **T4 incremental value over a trend-only baseline**: in IS, fit OLS of y_H (winsorised at the IS 0.5%/99.5% quantiles, fitting only) on (a) TREND alone = baseline, (b) TREND + MOMCHG + STRETCH, (c) TREND + each single raw directional feature (22 models), (d) all 22 features (ridge, λ = 1 on standardised IS columns). OOS ΔIC = IC(model) − IC(baseline) with a paired bootstrap CI (same resamples).
- **T5 vote-inflation demonstration**: V10 = {stack, slope20, slope50, sep20_50, sep50_200, dist20, rsi, macdh, roc10, didiff}; vote_i = sign(feature_i); S = Σ vote_i ∈ [−10, 10].
  - (a) mean pairwise correlation ρ̄ of the votes and N_eff = 10/(1 + 9ρ̄); eigen participation ratio.
  - (b) naive independence: with per-vote OOS accuracy a_i = P(vote_i = sign y_H), the naive-Bayes "probability" for the observed agreement pattern, versus the realised OOS hit rate P(sign S = sign y_H) per |S| bucket (Wilson CIs).
  - (c) IC(S) vs IC(best single vote) vs IC(TREND).
  - (d) drowning: C_k = (n(dol) + Σ_{i≤k} vote_i)/(k + 1), k = 0..10 (V10 order as listed): report ρ(C_k, dol), ρ(C_k, TREND) and OOS IC(C_k).
- **Uncertainty (T1-T5)**: non-overlapping block bootstrap of the OOS segment, block length B = max(2H, bars per session day), 2,000 replicates, Pearson correlation of the segment's ranks resampled (Spearman approximation), 95% percentile CI. Wilson CIs for proportions.

**Pass criteria (Q3)**
- **P-IC** (a feature/factor × dataset at H): OOS CI excludes 0, same sign as IS IC, and survives Benjamini-Hochberg at q = 0.10 across all T1+T2 OOS tests at that H (signals × datasets; p from the bootstrap, two-sided).
- **"Useful"** signal: P-IC with the same sign in ≥ 3 datasets spanning ≥ 2 of the 3 groups, no dataset P-IC with the opposite sign, and median OOS |IC| ≥ 0.02.
- **Weights**: a useful A-set factor gets weight ∝ its median OOS IC (sign as found), normalised to Σ|w| = 1 across useful factors; a factor that is not useful is **neutral (weight 0)**. Regime-specific weights only where T3 shows a Holm-significant regime difference in ≥ 2 groups.
- **Incremental value**: OOS ΔIC > 0 with CI excluding 0 in ≥ 3 datasets in ≥ 2 groups.
- **Vote inflation is demonstrated** if N_eff ≤ 4 in the median dataset AND the naive-Bayes probability at |S| ≥ 8 exceeds the realised hit rate's Wilson upper bound in ≥ 2/3 of datasets.

### A9. RSI divergence — question Q4
- Confirmed pivots, p ∈ {3, 5} (definition as in A2), usable at t = i + p.
- **Bearish regular divergence** at t (confirmation of pivot high i2): previous confirmed pivot high i1 with 5 ≤ i2 − i1 ≤ 60, H_i2 > H_i1 and RSI14_i2 < RSI14_i1. **Bullish** mirrors with lows (L_i2 < L_i1, RSI_i2 > RSI_i1).
- Same-type baseline: confirmations with the same price pattern (higher high / lower low within 5-60 bars) and no RSI divergence. Secondary references: all pivot confirmations of that side; all bars.
- Outcomes from bar t: y_rev,H = (C_t − C_t+H)/A_t for bearish and (C_t+H − C_t)/A_t for bullish; first-passage reversal r = 1 if price reaches C_t ∓ 1·A_t (reversal side) before C_t ± 1·A_t within H (ties and undecided excluded from r).
- H ∈ {20, 60}. Nothing is fitted, so the **primary sample is the full sample** (after warm-up), with the chronological IS/OOS halves reported; the pass also requires the same sign in both halves.
- Pass (per group, sides pooled): mean y_rev(div) − mean y_rev(same-type, no div) > 0 with a 95% CI excluding 0 (block bootstrap over event-time blocks, B as in A8), AND P(r = 1 | div) − P(r = 1 | no div) > 0 with CI excluding 0; Holm over 3 groups × 2 p × 2 H = 12 tests.

### A10. Number of variants (declared)
- T1: (22 + 1 + 1 + 3) = 27 signals; T2: 3 A-set + ≤ 11 B-set; × 15 datasets × 2 H.
- T3: 3 factors × (3 + 3 + 2) regime cells × 15 × 2.
- T4: 25 models × 15 × 2. T5: 1 design × 15 × 2.
- Q4: 12 primary + sides separately + IS/OOS halves (descriptive).
- All variants are reported; none is dropped for its result.

---
