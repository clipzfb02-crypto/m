# E6 · Liquidity lifecycle and sweep taxonomy, parameterised from data (R2)

Role: R2 Liquidity engineer. Key: `E6_sweep_lifecycle`. Spec: §4.5 (lifecycle), §4.6 (sweep intelligence), §20, §21, §25.
Code: `apex/validation/python/experiments/E6_sweep_lifecycle/` (outputs in `out/`, git-ignored).

## Part A · Pre-registration (frozen 2026-11-27 ~10:05 UTC, BEFORE any outcome of this experiment was computed)

Only data-structure QC (E3's `out/qc_data.txt`, timestamps / gaps / jumps) had been looked at when this part was written.
No reach rate, reclaim rate, race, penetration quantile or placebo comparison had been computed in this experiment.
Any later change is listed in Part C with both versions. The SHA-256 of this Part A is stored in `out/prereg.sha256`.

### A.0 What is already known (the prior; cited, not re-tested)

- Distance and volatility explain "which pool is reached"; labels add ≈ 0 (`ict_liq` B1: +0.1 ± 0.4 pp 1H, +0.8 ± 0.6 pp 5m).
- No reversal edge after a same-bar REJECT; at most a 0-2 pp continuation lean (`ict_liq` B7, `ict_struct`, `skeptic` C4).
- Multi-bar RECLAIM(1-3) leans reversal by −1.5 ± 0.7 pp, sign-unstable (`orderflow_micro` §1.8, 9 datasets).
- Shares of sweeps: same-bar REJECT 36-50%, RECLAIM +1/+2/+3 = 12-15 / 4.5-9.7 / 2.4-6.3%, still beyond after 3 bars 27-37%.
- REJECT penetration q50 0.23-0.28 ATR, q80 0.51-0.64 ATR (`ict_liq` B10, `orderflow_micro` T1).
- Stale pools: reached 5-14 pp less than a random level beyond ~24-72 h (1m/5m) and beyond ~72 h (1H) (`academic_sr` §2.3).
- DOL v2 `liqEvt` adds `±tier` for EVERY pool hit on a bar (baseline lines 1580-1582) (`ict_liq` §0.8b).
- E3 (parallel track) tests the formal hypothesis "confirmed sweep-and-reclaim improves reversal" with N = 3. E6 does NOT
  re-test that pass criterion; it calibrates thresholds, measures frequencies / outcome distributions / times, and compares
  real levels with matched placebo levels.

### A.1 Data

| TF | Datasets | Source | Span |
|---|---|---|---|
| 1h | ES, NQ, YM, RTY, CL | `amt_data/cme/<SYM>/<SYM>_1h_*.csv` (UTC, bar-open) | Mar 2025 (CL Jun 2025) - Apr 2026 |
| 1h | NQL | `i2/dl/data_src/data/Dataset_NQ_1min_2022_2025.csv` (ET bar-END stamps −1 min) resampled | Dec 2022 - Dec 2025 |
| 1h | BTC | `classic_tools/btc_1h.csv` (UTC) | 2016 - Jan 2025 |
| 15m | NQL; ES, NQ, YM, RTY, CL | 1-minute files resampled | NQL 3 y; others Jan 20 - Apr 15 2026 |
| 5m | NQL; ES, NQ, YM, RTY, CL; 6E, 6B | 1-minute files resampled (6E/6B from `smt_data/cme`) | NQL 3 y; CME 2026 Q1; 6E/6B Mar 8 - Apr 15 2026 |

- **GC is excluded** on all TFs: E3's QC shows GC 1h 173 open gaps > 4 ATR (80 jump-and-back) and GC 1min 221 (101);
  `ict_liq` found two contract months interleaved. No repair is attempted (repair would need the contract calendar).
- Holes: a step > 80 h (CME) / 3 h (BTC) starts a new segment; no level or outcome window crosses a segment boundary.
- Gap bars: `|open − close[t−1]| > 2·ATR[t−1]`. A first trade-through on a bar whose OPEN is already beyond the level is a
  **gap-through** (its own class, excluded from the sweep taxonomy and counted).
- Trading day: CME Globex day from 18:00 ET; BTC UTC day. Sessions (ET, bar-open time, engine defaults):
  Asia [20:00, 24:00), London [02:00, 05:00), NY AM [09:30, 12:00).
- 1-minute paths (intrabar analysis) come from the same 1-minute files.

### A.2 Common definitions

- ATR = Wilder RMA(14) of the chart-TF true range (engine `atrLen` 14). Every normalisation at bar t uses ATR[t−1] (known at
  the bar open), written A.
- **Liquidity levels (engine-faithful, Day-Trading mode):**
  - chart swings: pivot with 5 bars each side (left strict, right ≥), available at the confirmation bar (pivot + 5);
  - STF swings: 4H bars, 3 each side; HTF swings: D bars, 3 each side; available at the chart bar that completes the
    confirming HTF bar (only completed HTF bars; skipped when the chart TF ≥ that HTF);
  - PDH/PDL, PWH/PWL: completed prior day / week; Asia, London, NY-AM session high/low: available at the window's last bar.
  - Tier (engine `f_tierW`): chart 0.25, STF 0.45, HTF 0.65, Asia 0.55, London 0.60, NY 0.60, PD 0.80, PW 0.92.
  - Merge: a new level within 0.10·A of a live same-side level is merged into it (tier = max), as the engine does.
  - A level is live from the bar after `avail` until its first strict trade-through (`high > P` for BSL, `low < P` for
    SSL), its ejection (chart swings only: distance > 15 ATR at a close, engine `ejectD`), 2,000 bars, or segment end.
- **Matched placebo level (the random-level baseline for event outcomes).** For each real sweep at bar t with offset
  `a = (P − close[t−1])/A` (BSL; mirrored for SSL) and penetration `pen0 = (high[t] − P)/A`, draw up to 3 bars t′ from the
  same dataset, same split, same side and same session bucket (Asia / London / NY / other; BTC: 8-hour UTC bucket) such
  that the phantom level `P′ = close[t′−1] + a·A′` satisfies (i) `max(high[t′−10..t′−1]) < P′` (untouched 10 bars, like
  a real level, which is restricted to levels whose origin is ≥ 10 bars before t) and (ii) `(high[t′] − P′)/A′` falls in
  the same penetration bin (0.05 ATR wide up to 1 ATR, 0.25 wide to 2 ATR, then one bin), and `open[t′] ≤ P′`.
  The placebo is then run through exactly the same lifecycle code. A real-vs-placebo difference is a "level effect".
- **Distance-matched reach baseline S(d)** (for approach / expiry): over all bars of the dataset's split,
  `S_up(d, H) = P(max(high[t+1..t+H]) − close[t] > d·ATR[t])`, mirrored for SSL (the `ict_liq` / engine `f_potBase` idea).

### A.3 Sweep subtypes (formal; BSL shown, SSL mirrored). `ts` = first trade-through bar, A = ATR[ts−1]

| Code | Subtype | Rule | Classification bar |
|---|---|---|---|
| UNC | unconfirmed sweep | the CURRENT bar is beyond intrabar and not closed (measured on 1-minute paths) | live |
| GAP | gap-through | `open[ts] > P` | ts |
| WP | wick probe | first close ≤ P within N bars (k = 0..N−1), max penetration over ts..reclaim < p | reclaim bar |
| SR | sweep and reclaim | as WP but max penetration ≥ p | reclaim bar |
| BA | breakout and acceptance | K consecutive closes > P starting at ts (variant BA2: `close[ts] > P` and `low[ts+1] > P`) | ts+K−1 |
| UR | unresolved | neither (only possible when K > N) | ts+N−1 |
| FB | failed breakout | BA, then a close ≤ P within M bars after the acceptance bar | failure bar |
| AH | accepted and held | BA without failure in M bars (the level is consumed) | ts+K−1+M |
| CONT / REV | sweep then continuation / reversal | from the classification bar, the path reaches U = P + X·A first (CONT) or the opposite-side liquidity O first (REV) | resolution bar |

- O = the nearest live opposite-side level (any source) at least 0.25·A beyond the classification close; if none within
  6·A, O = P − 3·A. X = 1 (primary), 0.5 and 2 (secondary). Race horizon 60 bars; both barriers on one bar = tie
  (excluded, counted); if the classification close is already ≥ U, it is CONT at time 0.
- Driftless geometry per event: `g = (close_td − O)/(U − O)` clipped to [0, 1]. Reported: P(CONT), mean g, excess = P − g,
  and the real-minus-placebo difference.
- Time to resolution = bars from ts to the classification bar, and from the classification bar to the race resolution.

### A.4 Calibration estimands (each: IS estimate, OOS estimate, 95% CI, IS-vs-OOS stability)

1. **p (wick-probe depth)**, primary: the IS median of the max penetration (ATR) of sweeps reclaimed within N bars
   (equal-frequency split of reclaims into WP / SR). Secondary: p50x = the penetration at which P(same-bar close ≤ P)
   = 0.5 (isotonic fit). Also reported: penetration q25/q50/q80/q90 for all sweeps and for same-bar rejects.
   Behavioural test: does WP differ from SR in CONT excess (vs geometry and vs placebo)? If not, p is a cosmetic boundary.
2. **N (reclaim window)**, primary: the q80 of time-to-first-close-inside (bars after ts, k = 0 is the sweep bar) among
   sweeps reclaimed within 20 bars, as a count of bars (N = q80 + 1). Secondary: the excess reclaim hazard (real − placebo)
   per k = 0..10.
3. **K (acceptance)**, primary: the k ∈ {1..6} maximising Youden J = TPR − FPR of the rule "c0 ≥ k" (c0 = consecutive
   closes beyond starting at ts) for the target Z = `close[ts+20] > P` (still beyond 20 bars later). Compared rules:
   BA2 (close + next bar holds) and distance rules (`close[ts+j] ≥ P + a·A` for some j ≤ 2, a ∈ {0.10, 0.25, 0.50}).
   Reported also for the placebo; K is "level-specific" only if J_real − J_placebo has a CI excluding 0.
4. **M (failed-breakout window)**, primary: the q80 of time-to-failure (bars after the acceptance bar) among accepted
   events that fail within 20 bars (M = q80 + 1). Also the failure hazard per bar for real and placebo.
5. **Approaching band**: for live levels sampled every 5 bars at distances 0-6 ATR, P(reach within H | d) in 0.1-ATR
   bins (isotonic decreasing fit). d50(H) = the distance where it crosses 0.5, d80(H) where it crosses 0.8, for
   H ∈ {3, 5, 10, 20}; compared with the S(d) version. Scaling: fit `d50 = c·H^β`; the √H law holds if the β CI ∋ 0.5.
6. **Expiry**: (a) reach edge = hit within H = 20 minus S(d), pools 0.25-4 ATR, sampled every 5 bars, by age in sessions
   untouched since `avail` (0, 1, 2, 3-4, 5-9, ≥ 10 trading days) and by age in bars; expiry age (reach) = the first
   bucket from which the edge is ≤ −2 pp with the 95% CI below 0 in BOTH IS and OOS (on the pooled TF family).
   (b) reaction: the real-minus-placebo difference in same-bar reclaim and in reclaim within N, by the same age buckets;
   expiry age (reaction) = the first bucket where a difference that is significant in the youngest bucket is no longer
   significant. If no bucket shows a level effect, the report says so and expiry falls back to (a).

### A.5 Double counting (spec §4.5 "prevent consumed pools from being counted repeatedly")

- Per bar, the number of live levels traded through (all sources, after the 0.10-ATR merge). Reported: share of raid bars
  with ≥ 2 and ≥ 3 pools, the share of multi-hits whose pools lie within 0.25 ATR of each other.
- `liqEvt` replay with the engine's own mapping (HOLD: close > P + 0.20·A_creation → +1; REJECT: close < P → −1;
  else 0; × tier; decay half-life 24; clamp ±1) under (i) the engine sum over every hit pool and (ii) one event per side
  per bar using the strongest tier (ICT-9's de-duplication). Reported: over-count ratio Σ|Δ_sum| / Σ|Δ_dedup| on raid
  bars, the share of raid bars where they differ, clamp-saturation share, single-bar sign flips of liqEvt, and the
  induced change in D (= 0.30·Δ liqEvt with the default weights 0.5 / 0.2 / 0.3).

### A.6 Splits and statistics

- Chronological 60/40 on trading days per dataset; events assigned by ts; IS events whose 60-bar race reaches OOS are
  purged; the first 2 OOS days are embargoed. Calibration is done on IS; OOS reports the same estimand to check stability.
- CIs: Wilson for single proportions; moving-block bootstrap over trading days (pooled TF families cluster by calendar
  day across symbols), 1,000 reps, block 2 days (1h/15m) or 1 day (5m); percentile CIs for quantiles and argmax estimands.
- Multiple testing: Holm within each family (real-vs-placebo by subtype; WP-vs-SR; expiry buckets), BH across all.
- Primary families are pooled per TF; per-dataset results are reported for heterogeneity (sign counts).

### A.7 Declared variants (counted in the report)

X ∈ {0.5, 1, 2}; K ∈ {1..6} + BA2 + 3 distance rules; H ∈ {3, 5, 10, 20} for d50; 2 age axes for expiry; 3 TFs;
15 datasets. Anything added later is flagged EXPLORATORY.

### A.8 Pass / decision rules (decided now)

- A calibrated threshold is reported as **stable** if its OOS point estimate lies inside its IS 95% CI on the pooled TF
  family, and as **universal** if per-TF estimates differ by less than the width of their CIs (otherwise per-TF values).
- A subtype is said to **carry directional information** only if its CONT excess vs placebo has |Δ| ≥ 2 pp,
  Holm-adjusted p < 0.05 on OOS, the same sign IS, on at least one TF. Otherwise it is a label, not a signal.
- The state table uses the stable, data-derived values; unstable ones are flagged with both values.

---
