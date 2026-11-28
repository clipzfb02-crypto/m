# E7 · Market-structure rules: pivots, BOS/CHoCH, displacement, ranges, premium/discount (R1)

Role: R1 market-structure analyst. Key: `E7_structure_rules`. Spec: sections 3, 20, 21, 25.
Code: `apex/validation/python/experiments/E7_structure_rules/` (outputs in `out/`, git-ignored).

Status: PRE-REGISTRATION written 2026-11-27 ~10:00 UTC, before any outcome was computed. Only format checks had been run (row counts, date ranges, guard counts through the E2 loader). The SHA-256 of section A is stored in `out/prereg.sha256` with a UTC timestamp before the first outcome run. Results follow in section B. Deviations are listed in section D.

---

## A. PRE-REGISTRATION (frozen)

### A0. What the study already found (the prior)
- `ict_struct.final.md` §0, §2.3 (8 markets + 8 random walks, 1H, ±1.5 ATR / 30 bars first-touch label):
  - the engine draw vector `D` called the first-touched side 47.4-52.7% (random walks 48.4-52.1%);
  - internal CHoCH 50.1% (n 2,467), swing (protected) CHoCH 53.7% (n 1,016; random walk 50.1%), chosen after looking;
  - all displacement bars 51.3% continuation (n 4,347; random walk 50.6%);
  - ICT premium/discount rule 49.5% / 49.1%;
  - weak-before-protected race = gambler's-ruin geometry (65.3% vs 65.8%, n 12,148).
- `ict_pd.final.md` §2.6: a small reversion at the pivot-range scale on CME 1H, momentum at the 20-day (IPDA20) scale.
- `bias_dol.final.md` §1.10: continuation vs reversal after a level cross is asset/timescale dependent.
- E4 (parallel) tests Donchian-channel breakouts by volatility state; E2 (parallel) tests structure+momentum signals after costs. E7 does not repeat them: E7 tests structure-defined objects (pivots, protected levels, range boxes) and their rule choices.

**Prior expectation (stated before testing):** no structure rule predicts direction beyond drift and geometry. Close-confirmed breaks should have fewer false breaks than wick breaks by construction, but neither should show follow-through. Location in the dealing range should not predict reversion. A null result is an acceptable outcome.

### A1. Data
Loaded with the E2 loader (`E2_signals/e2data.py`, reused unchanged; `apexdata.py` did not exist).

| ID | Data | Period | Bars | Notes |
|---|---|---|---|---|
| NQ_1h | NQ 1-min (back-adjusted continuous) resampled | 2022-12-26 → 2025-12-11 | 17,488 | ET, open-labelled |
| ES_1h, YM_1h, RTY_1h | CME 1h | 2025-03-21 → 2026-04-15 | 6,270 each | roll guard (4 roll bars) |
| CL_1h | CME 1h | 2025-06-01 → 2026-04-15 | 4,520 | jump/hole guard; LOW QUALITY, reported but flagged |
| BTC_1h | spot | 2016-01-01 → 2025-01-07 | 79,057 | UTC |
| NQ_5m, NQ_15m | NQ 1-min resampled | 2022-12-26 → 2025-12-11 | 209,752 / 69,920 | timeframe-robustness family |

GC is excluded: its 1H file interleaves two contract months (E1/E3 QC: 747 jumps > 1.5%, 290 jump-and-back). No repair attempted.

**Families.** The primary family is `1h` = {NQ_1h, ES_1h, YM_1h, RTY_1h, CL_1h, BTC_1h}. The secondary family is `intraday` = {NQ_5m, NQ_15m} (the same instrument as NQ_1h, so it is a timeframe check, not independent evidence). The index futures overlap in time and are correlated, so the effective number of independent markets is below 6.

### A2. Common definitions
- Decision at the close of bar t. Every feature uses bars ≤ t.
- ATR = Wilder ATR(14) at t. Unit of all moves.
- Warm-up: the first 600 bars of each series are excluded.
- **Split:** chronological per dataset. In-sample (IS) = the first 60% of post-warm-up bars, out-of-sample (OOS) = the last 40%. IS events whose 60-bar horizon reaches into OOS are purged. Any parameter chosen from data is chosen on IS only.
- **Guard:** an event is dropped if its window [t, t+60] contains a guard bar (roll / data hole).
- **Horizons:** H ∈ {5, 20, 60} bars. **Primary H = 20.**
- **Follow-through outcome:** `y_H = dir · (C_{t+H} − C_t)/ATR_t`, dir ∈ {+1, −1}.
- **Random-time baseline (drift control):** for a set of events with direction shares f₊, f₋ in a split, the baseline is `(f₊ − f₋)·μ_H`, where μ_H is the mean of (C_{t+H} − C_t)/ATR_t over all eligible bars of that split. The reported **excess** = mean(y_H) − baseline. The hit-rate analogue uses P(up at H) of the split.
- **Matched baseline (bar-size control), for events defined by the event bar's own move:** the mean y_H of all non-event bars with the same direction and the same decile of the 1-bar signed return in ATR (deciles from IS). Excess_matched = mean(y_H − matched cell mean).
- **Sign-flip null:** 20 synthetic copies per dataset, each bar's close-to-close move and bar shape mirrored with a random sign (keeps volatility clustering, removes direction dependence). The whole event pipeline is re-run; the null band is the 2.5-97.5% range of the pooled OOS statistic.
- **Uncertainty:** circular block bootstrap over calendar session days (pooled families cluster by calendar date across symbols), block length = max(2, ceil(60 / bars-per-session) + 1) days, 2,000 replicates, percentile 95% CI. p-values from the bootstrap SE (normal). Proportions also get Wilson CIs with the effective n = n / design effect (design effect from the bootstrap variance ratio).
- **Multiple testing:** Holm within each question's primary family; Benjamini-Hochberg across all primary tests of E7. Every variant run is reported.
- **Common pass rule:** a primary test passes only if (1) the pooled `1h`-family OOS estimate has a 95% CI excluding 0, (2) the IS estimate has the same sign, (3) the Holm-adjusted OOS p < 0.05, and (4) the OOS estimate lies outside the sign-flip null band.

### A3. Pivot methods (Q1)
| ID | Rule | Confirmation bar |
|---|---|---|
| F2, F3, F5 | Fractal p/p: swing high at i if H_i > max(H_{i−p..i−1}) and H_i ≥ max(H_{i+1..i+p}) (leftmost-wins ties, study ICTS-9); lows mirror | i + p |
| ZA1.5, ZA3 | ATR ZigZag k ∈ {1.5, 3}: in an up-leg track the running max high; a bar that makes a new max cannot confirm; the high pivot is confirmed at the first bar t with L_t ≤ maxH − k·ATR_t; mirror for lows | t |
| ZP1.5, ZP3 | Percentage ZigZag: same, with a constant threshold pct·price, pct = the IS median of k·ATR_t/C_t (k ∈ {1.5, 3}) | t |

Measures (descriptive; no direction claim):
- confirmation lag = confirmation bar − pivot bar (mean, median, p90);
- density = confirmed pivots (highs + lows) per session day;
- alternation violations (two same-type pivots in a row) and mean swing size in ATR;
- **stability (supersede rate)** S_N = share of confirmed swing highs (lows) traded through (H > level, resp. L < level) within N ∈ {5, 10, 20} bars after confirmation. Primary N = 10.
- **distance-matched random level:** for each pivot, d = |level − C_conf|/ATR_conf; the baseline is the probability that a level at d ATR above (below) a random bar's close in the same split is traded through within N bars (20 random bars per pivot). Q1 primary test: S_10 − baseline ≠ 0 (a pivot that "holds" more than geometry gives a negative difference). Holm over 7 methods.

### A4. BOS / CHoCH: close vs wick (Q2)
- **Protected reference:** the most recent swing high (low) confirmed at bar ≤ t−1 and not yet broken under the rule. A break consumes it until a newer swing is confirmed (engine/LuxAlgo convention).
- **Close rule:** C_t > ref (up), C_t < ref (down). **Wick rule:** H_t > ref, L_t < ref. If both sides break on one bar, the bar is skipped.
- **State:** the direction of the last break under the same rule. A break with the state is a **BOS**; against it a **CHoCH**; the first break is unlabelled.
- **Wick-only events:** wick rule breaks whose close is back inside (a failed break / sweep). Reported as a subset.
- **Outcomes:** y_H (primary H = 20); **false5** = a close back on the other side of the level within bars t..t+5 (for close breaks bar t cannot qualify); its mirror null **ext5** = a close ≥ C_t + (C_t − ref) within t+1..t+5 (close breaks only, as in E4 R3); **flip10** = an opposite break under the same rule within 10 bars.
- **Variants:** 5 pivot methods {F2, F3, F5, ZA1.5, ZA3} × 2 rules = 10 primary tests of excess y_20 (Holm over 10). Paired test close − wick on the same pivot method (5 tests).
- **Pass:** common pass rule. "Close better than wick" needs the paired OOS difference CI to exclude 0.

### A5. Displacement (Q3)
Direction = sign(C − O).
| ID | Rule |
|---|---|
| DB1.0, DB1.5, DB2.0 | |C−O| ≥ k·ATR_{t−1} and |C−O|/(H−L) ≥ 0.6 |
| DR90, DR95 | range (H−L) percentile rank vs the previous 100 bars ≥ q, and close location in the direction ≥ 0.75 ((C−L)/(H−L) for up) |
| DCL | close location in the direction ≥ 0.85 and H−L ≥ ATR_{t−1} |
| DENG | the engine's rule: body ≥ 1.2·ATR_{t−1} with ratio ≥ 0.6, or two same-direction candles with both ratios ≥ 0.5 and combined body ≥ 1.8·ATR_{t−1} |

- Measures: base rate (share of bars, events per session), y_H vs random-time baseline (primary), vs matched baseline (does bar quality add anything beyond the bar's own return?), sign-flip band.
- Secondary: split by the F3 close-rule structure state (with / against).
- 7 primary tests, Holm over 7.

### A6. Compression and range formation (Q4)
- Bandwidth BBW = 4·stdev(C,20)/SMA(C,20); percentile rank vs the previous 500 values (Pine `ta.percentrank` convention, as E4).
- **Detector BW:** a range starts when BBW pct ≤ 20 and no range is active. **Detector NR7:** a range starts on an NR7 bar (the smallest H−L of the last 7) when no range is active.
- **Box:** at the start bar t0 the box is [min L, max H] of bars t0−9..t0. While the detector stays on (hysteresis: BW pct ≤ 35; NR7: within 7 bars of the latest NR7 bar) the box extends to include each non-breaking bar; then it freezes.
- **Break:** C_t > top_{t−1} (up) or C_t < bot_{t−1} (down). A range with no break within 100 bars expires.
- Measures: number of ranges, duration, break rate within 20 / 50 / 100 bars, P(up break), P(break in the direction of the 20-bar trend before t0), P(break at the edge nearer to C_t0) vs the geometric expectation, y_H after the break, false5 vs ext5, and the post-break 20-bar realised range / ATR vs random bars.
- Primary tests (2 detectors × 2): **H4a** P(break with the prior 20-bar trend) − 0.5; **H4b** excess y_20 after the break. Holm over 4. Secondary H4c: false5 − ext5.

### A7. Premium / discount in the dealing range (Q5)
pos = (C_t − L)/(Hi − L) for a range [L, Hi] known at t; primary analysis on bars with 0 ≤ pos ≤ 1.
| ID | Range |
|---|---|
| PD_F3, PD_F5 | the last confirmed swing high and the last confirmed swing low (fractal p = 3, 5) |
| PD_ICT | ICT [protected, weak] of the current leg from the F3 close-rule state machine: bull [protL, legH], bear [legL, protH] |
| PD_ZA3 | the last confirmed ATR-ZigZag(3) high and low |
| PD_N20 | IPDA-style rolling range: max H / min L of the last 20 sessions' bars (20 × bars-per-session) |

- Outcome: up-frame R_20 = (C_{t+20} − C_t)/ATR_t, demeaned by the split mean. Statistic: the OLS slope of R_20 on (pos − 0.5) (positive = momentum, negative = reversion). Secondary: the slope controlling for z20 = (C_t − C_{t−20})/(ATR_t·√20); quintile means; H = 60.
- 5 primary tests (H = 20), Holm over 5.

### A8. Which side first vs direction (Q6)
- State s_t from the Q2 state machine (primary F3 close rule; secondary F5, ZA3, and the HTF state = F3 close-rule state on 4×-aggregated bars, mapped only from completed HTF bars).
- **Replication:** first touch of C_t ± 1.5·ATR_t within 30 bars (both on one bar, or neither: dropped). Accuracy = P(first side = s_t) vs the drift baseline f₊·p_up + f₋·(1 − p_up).
- **Direction:** excess y_20 of s_t (state as a direction call every bar), and the hit rate P(sign R_20 = s_t) vs its drift baseline.
- Primary: 4 direction tests (F3, F5, ZA3, HTF-F3), Holm over 4; the replication is 1 test (F3).

### A9. Declared variants
Q1 7 methods × 3 N; Q2 10 primary + 5 paired + subsets; Q3 7; Q4 2 detectors × 4 outcomes; Q5 5 ranges × 2 horizons × 2 models; Q6 4 + 1. Primary tests: 7 + 10 + 7 + 4 + 5 + 5 = 38. All are reported; none is dropped for its result.

### A10. Recommendation rule (decided before results)
- A structure rule enters the APEX score only if it passes. Otherwise it is kept as a **descriptive / geometric** object (drawn, labelled, used for invalidation and target geometry) with zero directional weight.
- Pivot methods are chosen for the engine by lag and density (Q1) and by Q2 false-break rates, not by follow-through unless one passes.
- Close vs wick: the default confirmation rule is the one with the lower false5 rate unless the paired follow-through test favours the other.
