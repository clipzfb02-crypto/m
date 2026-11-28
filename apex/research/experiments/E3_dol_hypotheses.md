# E3 · DOL hypotheses H1-H6 (spec §20): pre-registered tests

Role: R2 Liquidity / DOL researcher. Key: `E3_dol_hypotheses`.
Code: `apex/validation/python/experiments/E3_dol_hypotheses/` (outputs in `out/`, git-ignored).

## Part A · Pre-registration (written 2026-11-27, BEFORE any outcome was computed)

Only data-structure QC (timestamps, gaps, price jumps) was run before this section was written. No hit rate, race, or
model result had been computed in this experiment when this section was fixed. Any later deviation is listed in Part C
with both versions.

### A.0 Data, splits and common definitions

**Datasets.**

| TF | Datasets | Source | Span |
|---|---|---|---|
| 1h | NQ, ES, YM, RTY, CL | `amt_data/cme/<SYM>/<SYM>_1h_*.csv` (UTC stamps, bar-open labels) | ES/NQ/YM/RTY Mar 2025-Apr 2026; CL Jun 2025-Apr 2026 |
| 1h | BTC | `classic_tools/btc_1h.csv` (UTC) | Jan 2016-Jan 2025 |
| 5m | NQL | `i2/dl/data_src/data/Dataset_NQ_1min_2022_2025.csv` (ET bar-END stamps, shifted -1 min), resampled to 5m | Dec 2022-Dec 2025 |
| 5m | NQ, ES, YM, RTY, CL | `amt_data/cme/<SYM>/<SYM>_1min_*.csv` resampled to 5m | Jan 20-Apr 15 2026 |

- **GC is excluded on both timeframes.** QC (`out/qc_data.txt`): GC 1h has 173 open gaps > 4 ATR, 80 of them
  jump-and-back; GC 1min has 221 and 101. That is the signature of two contract months interleaved. No repair was attempted.
- **Holes.** A step > 80 h (CME) or > 3 h (BTC) starts a new segment. No outcome window may cross a segment boundary.
  CL 1h has two multi-week holes (Jun 20-Jul 13 and Jul 31-Aug 10 2025).
- **Trading day.** CME: Globex day starting 18:00 ET. BTC: UTC calendar day. **Week:** CME weeks start at Sunday 18:00 ET; BTC weeks start Monday 00:00 UTC.
- **Sessions** (ET clock, by bar open): ASIA [18:00, 02:00), LON [02:00, 08:00), NY [08:00, 18:00).
- **ATR** = Wilder RMA(14) of true range on the chart TF. `lvr = ln(ATR14/ATR100)` is the volatility regime.
- **Split.** Chronological on trading days: in-sample (IS) = first 60% of days, out-of-sample (OOS) = the rest.
  - Embargo: the first `ceil(H in days)+1` OOS days are dropped.
  - Purge: IS decision bars whose outcome window reaches the OOS start are dropped.
  - Baselines and models are fitted on IS only and evaluated on OOS.
  - IS and OOS are reported separately.
- **Pool trade-through** is strict: `high > level` for highs, `low < level` for lows, on the tick grid. An exact touch is not a hit.
- **Distance-matched random-level baseline (RaceSurface).**
  - Take random IS start bars (up to 6,000 per dataset, seed 0). Measure the running max up and down excursion in ticks over the next H bars.
  - A phantom level at distance d (in ATR at the start bar) sits at `round(d*ATR/tick)` ticks and is hit when the excursion exceeds it: the same strict rule as real pools.
  - This gives, for any (d_up, d_dn):
    - P(up level first | resolved);
    - P(neither within H);
    - single-level P(reach within H).
- **CIs.**
  - Wilson 95% for proportions.
  - Moving-block bootstrap over trading days for means and differences: 2,000 reps; block = ceil(H in days)+1 days.
  - Holm within each hypothesis' primary family, and BH over all primary tests.
  - Every variant tried is counted and listed.

**Level definitions** (each has an `avail` bar: the bar at whose close it is first known).

| Kind | Rank | Definition | Life |
|---|---|---|---|
| SW | internal | Confirmed pivot, L = R = 5. `avail` = pivot + 5. | 500 bars |
| SES | 1 | High and low of each completed ASIA / LON / NY session instance. `avail` = last bar of the session. | 2 trading days |
| PD | 2 | Prior trading-day high and low. `avail` = last bar of the day. | The next trading day only |
| PW | 3 | Prior trading-week high and low. | The next week only |
| FVG | n/a | 3-bar gap of size ≥ 0.10 ATR. A bullish FVG is a downside target with near edge = top; a bearish FVG is an upside target with near edge = bottom. "Untouched" until price re-enters the near edge; "filled" when price trades to the far edge. | 500 bars |

A pool is active at decision bar t if `avail ≤ t`, it has not been traded through on bars `avail+1..t`, and t is before expiry.

### A.1 H1 · Prior-day extremes and directional travel

**Decision points.** Two per trading day, provided PDH and PDL are both still untaken and the close is inside (PDL, PDH):
- E_open: close of the first bar of the trading day;
- E_ny: close of the bar that contains 09:30 ET.

`d_up = (PDH-close)/ATR` and `d_dn = (close-PDL)/ATR`.

**H1a (race).**
- Hypothesis: the nearer prior-day extreme is reached first more often than a distance-matched random pair of levels implies.
- Outcome: which of PDH or PDL is traded through first within H_race = 2 trading days (46 bars on CME 1h, 48 on BTC 1h, 552 on 5m). Ties (both on one bar) and unresolved cases are reported, then excluded from the race rate.
- Baselines:
  - (i) RaceSurface P(near first | d_up, d_dn), from IS random starts with the same H_race;
  - (ii) driftless Brownian geometry, `d_far/(d_up+d_dn)`;
  - (iii) 0.5.
- Metric: OOS edge = observed near-first rate minus the mean baseline probability, with a block-bootstrap CI; plus the Brier score of P(PDH first) for the surface, geometry and 0.5.
- Pass: the pooled OOS edge vs the RaceSurface is > 0 with the 95% CI excluding 0 on BOTH timeframes, and the sign is consistent in at least 4 of 6 datasets per timeframe.

**H1b (directional travel).**
- Hypothesis: the direction toward the nearer prior-day extreme predicts the sign of the close-to-close move better than naive baselines.
- Outcome: the sign of (last close of the trading day minus the decision close), excluding zero.
- Baselines:
  - (i) 50%;
  - (ii) the prior-day candle direction (sign of PD close minus PD open).
- Metric: OOS accuracy, with a Wilson CI and a paired block-bootstrap difference vs (ii).
- Pass: accuracy > 50% with the CI excluding 50%, AND accuracy > baseline (ii) with the paired-difference CI excluding 0, pooled per timeframe.
- Note: toward-nearest is the exact opposite of "toward the prior-day mid", so its complement tests the mid-reversion reading.

**H1c (single-level reach).**
- Hypothesis: PDH/PDL are reached within H_race more often than a distance-matched random level.
- Metric: OOS mean of (hit minus RaceSurface single-level P(reach)), with a block-bootstrap CI.
- Pass: CI excludes 0 and the edge is positive.

**Primary family (Holm):** H1a at E_open on both TFs, plus H1a at E_ny on both TFs: 4 tests.

### A.2 H2 · Confirmed sweep-and-reclaim and reversal

**Pools.** PD, PW, SES and SW (not FVG).

**Event.** The first bar t on which a pool is traded through by at least k: k = 1 tick (primary) or k = 0.10 ATR (variant).

**Classes, by decision bar** (N = 3 bars):

| Class | Name | Rule | Decision bar |
|---|---|---|---|
| W | wick-only / unconfirmed sweep | Every event, whatever the close | t |
| R0 | same-bar reclaim | `close[t]` back inside the level | t |
| R3 | confirmed sweep-and-reclaim | The first close back inside within bars t..t+3 | That reclaim bar j |
| ACC | acceptance | `close` beyond the level on every bar t..t+3 | t+3 |
| R3M | reclaim + MSS | R3, then within 12 bars of j a close beyond the most recent confirmed opposite swing (the CHoCH/MSS idea) | That close |

**Outcome race from the decision bar** (H_race = 60 bars):
- REV: the opposite-side liquidity is traded through first. It is the nearest active opposite-side pool (PD/PW/SES/SW) at decision time, 0.25-8 ATR away; events with none in that band are dropped.
- CONT: a new extreme beyond the event extreme (max high or min low over t..decision bar) comes first.
- Ties and unresolved cases are reported separately.

**Baseline.** RaceSurface P(opposite first | d_opp, d_ext) for the same distances in the same direction. Also compared:
- wick-only (W) vs R3, as a difference in edges;
- unconditional random starts (the baseline itself).

**Metric.** OOS REV-rate edge vs the RaceSurface, with a block-bootstrap CI, for each class. CONT is reported too (CONT = 1 − REV among resolved non-ties).

**Pass for "confirmed sweep-and-reclaim improves reversal".**
- R3 edge > 0 with the CI excluding 0 pooled on both TFs;
- AND R3 edge − W edge > 0 (bootstrap CI excludes 0) on at least one TF with the same sign on the other.

**Secondary (exploratory, flagged).** R3 split by the event's relation to HTF bias (with / against).

**Primary family (Holm):** R3 edge on 1h and 5m, plus (R3 − W) on 1h and 5m: 4 tests.

### A.3 H3 · Target proximity × HTF alignment

**Rows.** Every 4th bar on 1h and every 12th bar on 5m, with each active pool (PD/PW/SES/SW) at distance 0.25-6 ATR.

**Outcome.** Traded through within H = 60 bars (the spec's default horizon). H = 20 is secondary.

**HTF bias.**
- HTF = trading day for 1h charts, clock hour for 5m charts.
- HTF pivots use L = R = 2.
- Bias = +1 after an HTF close above the last confirmed HTF swing high, −1 after a close below the last confirmed HTF swing low.
- It is taken from the last HTF bar completed before the current HTF bar (Pine `[1]` + `lookahead_on`).
- Alignment = side × bias: aligned, counter, or none.
- Secondary: the HTF close vs HTF EMA20, on the same completed-bar basis.

**Model.**
- Pooled logistic regression per TF: `hit ~ natural spline(log d, 4 df) + lvr + side + dataset intercepts` (the BASE model) + alignment dummies.
- Fit on IS; OOS skill vs BASE: Brier skill score, Δlog-loss, ΔAUC, with day-block bootstrap CIs.
- IS coefficients with day-clustered SEs.

**Pass.** OOS ΔBrier > 0 with the CI excluding 0 on both TFs, AND the aligned coefficient > 0 in IS with p < 0.05 (Holm over the 2 TFs).

### A.4 H4 · FVGs beyond structure

**(a) As targets.**
- Near-edge touch rate of untouched FVGs within H = 60 bars vs the RaceSurface single-level baseline (edge in pp), from the same row sampling as H3.
- Split: FVGs within 0.25 ATR of an active pool (overlapping structure) vs isolated.
- Also compared with swing pools in the same distance band, through a logistic `hit ~ BASE + is_FVG`.
- Pass: isolated FVG edge > 0 with the CI excluding 0 on both TFs.

**(b) As barriers.** On pool-target rows (H3 rows):
- the count of untouched opposing FVGs whose near edge lies between price and the target;
- added to BASE + momentum (12-bar return toward the target, in ATR) + the stack count of intermediate same-side pools;
- control: the count of already-touched opposing FVGs in the same path, formed within 500 bars.
- Pass: the untouched-barrier coefficient < 0 in IS (p < 0.05), with OOS ΔBrier > 0 (CI excluding 0) on both TFs, and still < 0 with the control in the model.

**(c)** The distance-matched comparison is part of (a).

### A.5 H5 · Lifecycle: repeated touches

- **Touch.** An episode start where the bar extreme comes within 0.10 ATR of the pool without trading through. Episodes are separated by more than 3 bars.
- **(i) Reach model** on H3 rows:
  - BASE + touch-count dummies (0, 1, 2, 3+) + log age;
  - pass = an OOS ΔBrier CI excluding 0 on both TFs, with a monotone sign.
- **(ii) Conditional break.**
  - Unit: the k-th touch episode of a pool (SW/PD/PW/SES).
  - Outcome: the pool is traded through within 12 bars after the touch bar.
  - Model: logistic `break ~ touch_k dummies + log age + lvr + kind + dataset`; IS coefficients plus OOS check.
  - Hypothesis direction is not assumed (two-sided).
  - Pass = the coefficient for 3+ vs 1 is significant after Holm, with the same sign IS and OOS on both TFs.

### A.6 H6 · Ranking factors

**Rows.** H3 rows plus FVG rows.

**BASE.** `spline(log d) + lvr + side + dataset`.

**Candidate factors, each added alone to BASE:**
- kind hierarchy (SES / PD / PW / SW / FVG dummies);
- log age;
- freshness (log bars since the last touch, or age if never touched);
- touch count;
- prior sweeps (same-side pools traded in the last 24 bars);
- opposing untouched FVG barriers in the path;
- intermediate same-side pools (stack);
- volatility regime beyond BASE (lvr²);
- time of day (session of the decision bar);
- momentum toward the target (12-bar return in ATR);
- HTF alignment.

Then ALL factors together.

**Metric.** OOS (fitted IS) Brier skill score vs BASE, ΔAUC, and Δlog-loss per TF, with day-block bootstrap CIs (500 reps for AUC and 2,000 for Brier).

**Pass for a factor.** OOS ΔBrier CI excluding 0 on BOTH TFs after Holm across the 11 factors × 2 TFs.

**Reported regardless:** BASE's own OOS calibration (reliability by decile) and Brier skill vs the climatological hit rate.

### A.7 Variant count (declared up front)

| Test | Variants |
|---|---|
| H1 | 2 TFs × 6 datasets × 2 decision points × 3 outcomes |
| H2 | 2 TFs × 6 datasets × 5 classes × 2 penetration rules |
| H3 | 2 TFs × 2 HTF definitions × 2 horizons |
| H4 | 2 TFs × 3 sub-tests |
| H5 | 2 TFs × 2 sub-tests |
| H6 | 2 TFs × 12 models |

Only the primary families above decide pass or fail. Everything else is descriptive.

## Part B · Results

(filled in after the runs; see below)

## Part C · Deviations from the pre-registration

(none yet)
