# E10_volume_vwap: honest volume, VWAP, volume-at-price and delta-proxy features (R4b)

Status: PRE-REGISTRATION written 2026-11-27 before any outcome was computed. Only data inspection was done first (columns, time zones, gaps, zero volume, rolls, contract interleaving: `out/qc_data.txt`). The SHA-256 of section A is stored with a UTC timestamp in `apex/validation/python/experiments/E10_volume_vwap/out/prereg.sha256` before the first outcome run. Results are appended in section B; deviations from this plan are listed in section D.

---

## A. PRE-REGISTRATION (frozen)

### A0. Questions (spec section 7, 13.2, 20.1 item 12, 21 "missing volume")
1. Does relative volume (vs the same clock slot) or a volume percentile tell us anything, out of sample, about follow-through after a liquidity level is traded through, separately for breakouts that close beyond the level (acceptance) and sweeps that close back inside (reclaim)?
2. Does a stretch from session VWAP (in VWAP-sigma or ATR) mean-revert or continue over a fixed horizon, by volatility regime and time of day, and is VWAP any different from a price-only moving reference?
3. From 1-minute data: are naked RTH POCs revisited more than a distance-matched level? Do LVNs get crossed faster than same-width control bands of the same profile?
4. How well do Pine-buildable candle "delta" proxies match a tick-level reference (1-second tick rule) and, on BTC, the true aggressor delta?
5. How do volume features degrade on tick-count volume and single-venue crypto volume, and how should APEX detect a volume-less or corrupt feed?

Prior from the completed study (cited, not repeated): volume as pool size is null (`orderflow_micro.final.md` B6); effort-vs-result splits at swept pools and climaxes are null at daily, 1H and 5m (`wyckoff_sd.final.md` 2.6, 2.7c); relative volume adds at most ~3 pp OOS R² to next-30-bar range at 1H and nothing at 5m (2.7d); naked POCs are reached at the distance-matched random rate (`amt_profile.final.md` 0.1); LVNs are crossed faster (+7-9% at 15 min, A) but LVN rejection is weak (B8); a frozen session VWAP is a weak magnet (+1.5 pp CME) and VWAP bands are null as targets (`classic_levels.final.md` T4); on BTC 1H a lower-TF candle-sign or BVC proxy agrees with the true delta sign 60-66% of the time (`orderflow_micro.final.md` D1). **The prior is therefore null for questions 1 and 3a, positive for 3b, and unknown for 2.**

### A1. Data
| ID | Instrument / TF | Source | Period | Use | Notes |
|---|---|---|---|---|---|
| N1 | NQ 1min → 5m, 1h | `i2/dl/data_src/data/Dataset_NQ_1min_2022_2025.csv` | 2022-12-26 → 2025-12-11 (767 sessions) | PRIMARY for Q1, Q2, Q3 | ET, close-labelled, shifted −1 min. Back-adjusted (E2). Real volume. Our session VWAP reproduces the file's ETH VWAP to 5e-6 pts (QC). |
| C1 | ES, NQ, YM, RTY, CL 1min → 5m | `amt_data/cme/<SYM>/*_1min_*` | 2026-01-20 → 2026-04-15 | Replication (Q1-Q3); after N1 in time, so NQ here is a true later hold-out | UTC → ET. Unadjusted: equity-index roll 2026-03-15 22:00 UTC is a guard; CL guarded by a >1% session-open gap rule. |
| C2 | ES, NQ, YM, RTY, CL 1h | `amt_data/cme/<SYM>/*_1h_*` | 2025-03-21 → 2026-04-15 (CL from 2025-06-01) | Replication (Q1, Q2) | Roll guard from E2 (ROLL_UTC); CL jump/hole guard. |
| B1 | BTC 1h | `classic_tools/btc_1h.csv` | 2016-01-01 → 2025-01-07 | Replication (Q1, Q2); Q5 cross-venue | UTC. |
| B2 | BTCUSDC 1h (Binance) | pinets fixture JSON | 2024-01-01 → 2025-11-20 | Q4 truth (taker-buy volume), Q5 (number of trades, cross-venue) | UTC. True aggressor delta = 2·takerBuy − V. |
| T1 | 6E, 6B, M6E, M6B, MBT, MET 1-second bars | `smt_data/cme/<SYM>/*_tick_*` | 6E/6B/M6x 2026-03-08 → 04-15; MBT/MET 2026-03-08 → 03-27 | Q4 reference, Q5 tick-count | **These are 1-second OHLCV bars, not trades, and carry no aggressor side.** No ES/NQ/GC/RTY tick files exist in the folder. |
| F1 | EURUSD spot 1h with broker tick volume | `bias_data/EURUSD.csv` | 2017-04 → 2018-02 | Q5 (seasonality shape only) | No overlap with 6E. |

**Excluded: GC (1h and 1min).** QC shows two contract months interleaved: 385 (1h) and 200 (1min) immediate full reversals of > 0.5% moves, vs 0 on ES/NQ 1min, with the off-month bars carrying 1-30 lots. A repair would need contract identifiers we do not have.

### A2. Common definitions (no lookahead)
- Session (futures): ETH 18:00 → 17:00 ET; session date = ET date of (ts + 6 h). RTH = 09:30-16:00 ET. BTC: UTC day.
- `A` = Wilder ATR(14) of the chart TF, taken at bar t−1 for event geometry, at t for normalising forward returns.
- **RVOL** = V_t / mean(V at the same clock slot over the previous 20 sessions), min 10 prior sessions. Slot = HH:MM ET (futures), UTC hour (BTC). Uses only completed prior sessions.
- **VPCT** = percentile rank of V_t within the last 100 bars (raw, not clock-adjusted).
- Pre-registered classes: RVOL high ≥ 1.5, low < 0.8; VPCT high ≥ 0.8, low ≤ 0.4. No threshold is tuned.
- Splits: N1 IS = sessions before 2024-07-01, OOS = from 2024-07-01. C2 IS < 2025-11-01 ≤ OOS. B1 IS < 2022-01-01 ≤ OOS. C1 is a single later replication block. Statistics are reported separately for IS and OOS; pass/fail is decided on OOS.
- CIs: 95% block bootstrap (2,000 resamples) with **session-day blocks** for intraday data and **ISO-week blocks** for 1h data, unless stated. Wilson CIs for single proportions.

### A3. Q1: volume at breakouts and sweeps of liquidity levels
- **Levels.** (i) PDH/PDL: prior session high/low. (ii) The most recent confirmed swing high/low with p = 5 (bar i is a swing high if H_i > max of the 5 bars before and ≥ max of the 5 bars after; usable from bar i+5), not yet traded through.
- **Event.** The first bar t (per level; per session for PDH/PDL) whose high strictly exceeds a buy-side level P (low below a sell-side level). Close class at t: **HOLD** (close beyond P: acceptance / breakout) or **REJECT** (close back at or inside P: sweep / reclaim).
- **Outcome (race from bar t+1, horizon H).** U = P + 1·A (continuation side), D = P − 1·A (reversal side), mirrored for sell-side. Events with close_t outside (D, U) are dropped. The outcome is which barrier is touched first within H bars; a bar touching both is a tie (excluded from resolved and reported); none = unresolved (reported).
- **Geometry baseline.** g = (C_t − D)/(U − D), the driftless-martingale probability of U first. **Continuation excess** e = 1[U first] − g on resolved races. Positive = continuation beyond the level.
- **H**: 5m → 24 bars (2 h); 1h → 24 bars.
- **Primary hypotheses (N1 5m OOS, Holm over these 4):**
  - H1.1 HOLD: e(RVOL ≥ 1.5) − e(RVOL < 0.8) ≥ +3 pp (high volume breakouts follow through more).
  - H1.2 REJECT: e(RVOL ≥ 1.5) − e(RVOL < 0.8) ≤ −3 pp (high volume rejections reverse more, "stopping volume").
  - H1.3, H1.4: the same with VPCT ≥ 0.8 vs ≤ 0.4.
- **Price-only control.** Volume is correlated with bar range, so the primary statistic is the **range-stratified** difference: the high-minus-low difference computed within terciles of range_t/A (tercile cut points from IS) and averaged with weights n_high·n_low/(n_high+n_low). The raw difference is also reported.
- **Pass:** OOS stratified difference in the stated direction with magnitude ≥ 3 pp, 95% CI excluding 0, Holm-adjusted p < 0.05, and the same sign in IS. Replications (C1 5m, C2 1h, N1 1h, B1 1h) are reported with BH correction; a feature is recommended only if the sign also holds in the majority of replications.
- **Base rates** reported: e for all HOLD and all REJECT events (no volume split).

### A4. Q2: session VWAP deviation
- VWAP_t = Σ(hlc3·V)/ΣV from the session anchor (ETH 18:00 ET; BTC 00:00 UTC). σ_t = sqrt(Σ V·hlc3²/ΣV − VWAP²) (the `ta.vwap(..., stdev_mult)` band width). Needs ≥ 6 bars since the anchor and σ > 0.
- z_t = (C_t − VWAP_t)/σ_t; a_t = (C_t − VWAP_t)/A_t.
- **Outcome:** y = sign(z_t)·(C_{t+H} − C_t)/A_t. Negative = reversion toward VWAP, positive = continuation. H = 12 bars on 5m (1 h; primary), 6 bars secondary; H = 6 on 1h. Forward windows that cross a roll/guard bar are dropped.
- **Price-only baselines.** TWAP (equal-weight session mean of hlc3) and EMA(20) of close: a_twap, a_ema in ATR units.
- **Primary hypotheses (N1 5m OOS, Holm over these 3):**
  - H2.1 mean y for |z| ≥ 2 ≠ 0 (two-sided; direction not pre-judged).
  - H2.2 VWAP adds beyond price-only references: in OLS y ~ a_vwap + a_twap + a_ema (each winsorised at ±10 ATR), the a_vwap coefficient has a CI excluding 0 OOS.
  - H2.3 regime dependence: mean y(|z| ≥ 2) differs between the low and high tercile of ATR14/ATR100 (IS cut points).
- **Pass:** CI excludes 0 OOS, same sign IS, and for H2.1 |mean y| ≥ 0.05 ATR (about one round-trip cost at 5m NQ). Time-of-day buckets (Asia 18-03, London 03-09:30, RTH open 09:30-11, RTH mid 11-14, RTH late 14-16, post 16-17) and |z| buckets [0,1), [1,2), [2,3), ≥ 3 are descriptive with BH correction. Replications: C1 5m, C2 1h, N1 1h, B1 1h.

### A5. Q3: volume at price from 1-minute data
- **Profiles.** For each RTH session, each 1-min bar's volume is spread uniformly over the rows its [low, high] covers. Row size: NQ 5.0, ES 1.0, YM 10, RTY 0.5, CL 0.05 points. POC = max row (ties: nearest the session mid); value area = 70%, grown from the POC by adding the larger adjacent row one row at a time.
- **H3.1 naked POC.** A session's POC is naked from 16:00 ET until a later 1-min bar's [low, high] contains it. At each later RTH open (09:30) every naked POC aged 1-10 sessions with |d| ≤ 2, d = (POC − open)/ATR_D (ATR_D = Wilder 14 of ETH session ranges, prior sessions only), is an observation. Outcome: touched during that RTH session (09:30-16:00). **Baseline S(d | side, vol tercile):** the empirical survival of the RTH session's maximum excursion from the open beyond |d| on that side, over all sessions of the same split, within terciles of ATR_D/ATR_D(60) (IS cut points). Excess = hit − S. Also reported for VAH/VAL. Pass: OOS excess ≥ +3 pp with session-cluster bootstrap CI excluding 0 and the same sign IS.
- **H3.2 LVN speed.** Rows smoothed 1-2-1. An LVN band = a maximal run of 1-6 rows strictly inside the session range (not touching the top or bottom 2 rows) with smoothed volume ≤ 0.30 × POC row volume. Control bands = runs of the same width with smoothed volume in [0.5, 1.0] × POC volume, non-overlapping any LVN, up to 3 per LVN chosen with a fixed seed. Over the next 5 sessions (all ETH minutes), an entry = the first 1-min bar whose range meets the band while the previous close is outside it. Outcomes: crossed (far edge touched) within 15 min of entry (primary), and crossed before retreating one row beyond the near edge (secondary). Primary statistic: LVN − control difference in cross-within-15 stratified by terciles of width/ATR_1m(14) at entry (IS cut points) and by hour bucket. Pass: OOS ≥ +3 pp, CI excluding 0, same sign IS.
- Replication: C1 1-min (ES, NQ, YM, RTY, CL), with roll guards.

### A6. Q4: delta proxies vs reference
- **Reference (CME, T1):** the tick rule on 1-second closes: s_i = sign(C_i − C_{i−1}), carried forward when zero; reference delta of a chart bar = Σ s_i·V_i. It is itself a proxy for true aggressor flow (unknown accuracy); results are labelled "agreement with the 1-second tick rule", not "accuracy".
- **Truth (BTC, B2):** Binance taker-buy delta.
- Chart TFs: 1m, 5m, 15m, 1h built from the 1-second bars (CME); 1h, 4h, 1d from 1h (BTC).
- **Proxies (all Pine-buildable):** P1 bar sign V·sign(C−O); P2 close location V·(2C−H−L)/(H−L); P3 BVC V·(2Φ(ΔC/σ)−1), σ = std of ΔC over the previous 100 bars; P4-P7 the same three plus the tick rule summed over 1-minute intrabars (CME) or 1h intrabars (BTC).
- **Metrics** on δ/V: Pearson r, sign agreement (reference ≠ 0), and the **partial correlation given the bar's own return** (C−O)/A. Descriptive thresholds stated in advance: "sign-usable" ≥ 75% agreement; "adds information beyond price" if partial r ≥ 0.2.
- **What delta can predict:** on 6E/6B 5m (reference) and BTC 1h (truth), OLS r_{t+1} ~ r_t + δ_t/V_t, first half fit, second half R²; reported, no pass criterion.

### A7. Q5: missing, tick and single-venue volume
- (a) Tick count vs real volume in the same instrument and period (T1, 5m and 1h): tick count = number of 1-second bars whose close differs from the previous one; also active seconds. BTC: Binance number of trades vs base volume. Metrics: correlation of logs, Spearman of RVOL, Cohen's κ of RVOL ≥ 1.5. **Decision rule (pre-stated):** tick count is accepted as a substitute for RVOL features if Spearman ≥ 0.8 and κ ≥ 0.6.
- (b) Cross-venue BTC (B1 vs B2 overlap): the same metrics, plus the share of Q1 events whose RVOL class differs between venues.
- (c) Intraday seasonality shape: correlation of the mean log-volume clock profile of EURUSD spot tick volume vs 6E real volume (different years).
- (d) Detection rules evaluated on all datasets and on synthetic degradations (20% zeros, constant volume, a no-volume feed): na(volume), rolling share of zero-volume bars, constant volume, and the interleave signature found in GC.

### A8. Multiple testing
Primary family: 4 (Q1) + 3 (Q2) + 2 (Q3) = 9 hypotheses on the primary OOS block, Holm within each question and also reported Holm over all 9. Every other cell is descriptive with BH. The total number of variants run is counted and reported.
