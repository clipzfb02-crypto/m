# E12_tradeability: when is a move worth trading? (R4a execution / transaction costs)

Status: PRE-REGISTRATION written 2026-11-27 09:57 UTC, before any outcome was computed. Before writing it I inspected the data for format and quality only (columns, time zones, tick fit, holes, contract interleaving). No move, stop or trade statistic had been computed. The SHA-256 of section A is stored with a timestamp in `apex/validation/python/experiments/E12_tradeability/results/prereg.sha256` before the first run. Results are appended below it, and any deviation is listed in section D.

Spec coverage: section 16 (risk and execution intelligence), 13.1 (normalisation), 15 (outcomes), 20 (costs, OOS, CIs), 21 (gaps, thin sessions, roll gaps, DST) and 25 ("when there is no good trade").

---

## A. PRE-REGISTRATION (frozen)

### A0. Questions
1. For each instrument, timeframe and time of day, how large is the move that is available over H bars, compared with a realistic round-trip cost? Output: a cost-to-move ratio table.
2. How far away is a structural invalidation in ticks and ATR, and is a net reward-to-risk of 1 or more toward the nearest DOL target feasible?
3. Does a precisely defined TRADEABILITY metric flag poor outcomes out of sample?
4. How often do session-open gaps and scheduled events occur, how large are they, and what do they do to stops?

Prior expectation, stated before testing, from `trade_mgmt.final.md` 1.17-1.18 and `skeptic.final.md` 1.31:
- under a near-martingale, bracket geometry carries no gross edge (optional stopping), so E[R_gross] is about 0 for any stop/target mesh;
- costs are first-order on 1-5 minute charts and small on 1h;
- any out-of-sample power of a tradeability metric should therefore come mostly through the cost channel (cost / risk), not through reward/risk geometry.

### A1. Data (inspected for format only)
| ID | Series | Source file | Period | Use | Notes |
|---|---|---|---|---|---|
| NQL | NQ 1m, back-adjusted | `$SP/i2/dl/data_src/data/Dataset_NQ_1min_2022_2025.csv` | 2022-12-26 → 2025-12-11 | NQ and MNQ at 1m/5m/15m/1h | ET, close-labelled, shifted −1 min to open time (as in E2). No roll jumps |
| C1M | CME 1m: NQ, ES, YM, RTY, GC, CL | `amt_data/cme/<SYM>/<SYM>_1min_*.csv` | 2026-01-20 → 2026-04-15 | 1m/5m/15m (and 1h for GC, CL) | UTC → ET. Unadjusted: roll guard (A6) |
| C1H | CME 1h: ES, YM, RTY, NQ, CL | `amt_data/cme/<SYM>/<SYM>_1h_*.csv` | 2025-03-21 → 2026-04-15 (CL from 2025-06-01) | 1h for ES/MES, YM, RTY; NQ cross-check | Roll guard as in E2 A6. CL has holes of up to 23 days: hole guard |
| BTC1H | BTC spot 1h | `classic_tools/btc_1h.csv` | 2016-01-01 → 2025-01-07 | BTC 1h | UTC, converted to ET for time-of-day buckets. No gaps |
| MBT1M | CME Micro Bitcoin 1m | `smt_data/cme/MBT/MBT_1min_*.csv` | 2026-02-22 → 2026-03-27 | BTC 1m/5m/15m (prices only) | Only about 5 weeks; LOW SAMPLE. Price grid $5 |

- MNQ and MES are priced on the same index as NQ and ES. They share the price series and differ only in cost (A3).
- **GC de-interleave.** The GC 1m file interleaves two contract months: isolated bars sit about 0.75% away and revert on the next bar. Rule: keep a bar only if |open/last kept close − 1| < 0.4%. If 30 consecutive bars are rejected, accept the new level (roll) and flag that bar as a guard bar. GC is then resampled from the cleaned 1m. The GC 1h file is not used. GC is labelled LOW QUALITY throughout.
- Resampling: left-labelled on the clock in ET. The session day is the ET date of (ts + 6 h) for futures (Globex opens at 18:00 ET), and the ET date for BTC.

### A2. Instruments × timeframes
- 9 instruments: NQ, MNQ, ES, MES, YM, RTY, GC, CL, BTC.
- 4 timeframes: 1m, 5m, 15m, 1h.
- Primary source per cell:
  - NQ/MNQ: NQL at every TF;
  - ES/MES, YM, RTY: C1M at 1m-15m and C1H at 1h;
  - GC, CL: C1M at every TF;
  - BTC: MBT1M at 1m-15m and BTC1H at 1h.
- Each table states the source and n.

### A3. Cost model (round trip, RT)
RT cost in ticks = spread_RT + 2 × slip_side + 2 × commission_side / tick_value. "Spread_RT" is one full bid-ask spread, paid once over a round trip of two marketable orders (relative to mid). Slippage is the extra shortfall beyond the touch on market or stop orders.

| Instrument | Tick | Tick value | Commission all-in per side (USD) | Spread RT (ticks) | Slip per side (ticks) | **BASE RT (ticks)** | BASE RT (price) |
|---|---|---|---|---|---|---|---|
| ES | 0.25 | $12.50 | 2.88 | 1.0 | 0.5 | **2.46** | 0.615 |
| MES | 0.25 | $1.25 | 0.91 | 1.0 | 0.5 | **3.46** | 0.864 |
| NQ | 0.25 | $5.00 | 2.88 | 1.5 | 0.5 | **3.65** | 0.913 |
| MNQ | 0.25 | $0.50 | 0.91 | 1.5 | 0.5 | **6.14** | 1.535 |
| YM | 1.0 | $5.00 | 2.88 | 1.0 | 0.5 | **3.15** | 3.15 |
| RTY | 0.10 | $5.00 | 2.88 | 1.25 | 0.5 | **3.40** | 0.340 |
| GC | 0.10 | $10.00 | 3.15 | 1.5 | 0.5 | **3.13** | 0.313 |
| CL | 0.01 | $10.00 | 3.00 | 1.0 | 0.5 | **2.60** | 0.026 |
| BTC | % model | n/a | 0.05% taker per side | 0.5 bp | 1 bp | **12.5 bp** | 0.125% of price |

Scenarios:
- **LOW**: limit entry and limit exit, commission only. This understates real cost: it ignores non-fills and adverse selection.
- **BASE**: as in the table.
- **STRESS**: spread × 2, slip 1.5 ticks per side (BTC: 3 bp per side).

Sources are in section E.

### A4. Part 1: available move vs cost
- ATR = Wilder ATR(14) of the chart TF.
- For each bar t (with t ≥ 100), with a forward window t+1..t+H:
  - AM = |C_{t+H} − C_t|;
  - MFE+ = max H_{t+1..t+H} − C_t and MFE− = C_t − min L_{t+1..t+H}. MFE_dir is the pooled sample of both, i.e. the favourable excursion of a randomly directed trade.
- H ∈ {3, 12, 60} bars; **H = 12 is primary**.
- **Valid window:** no bar inside the window follows a time gap of more than 4 h (weekend, holiday or data hole; the daily 1-hour halt is allowed), and no guard bar.
- Cost-to-move ratios:
  - **CMR_AM = c_RT / median(AM)**;
  - CMR_MFE = c_RT / median(MFE_dir);
  - both in the same units (ticks; bp for BTC).
- Time of day uses the ET hour of bar t's open. Sessions:
  - ASIA [18, 02);
  - LONDON [02, 08);
  - NY_AM [08, 12);
  - NY_PM [12, 16);
  - THIN [16, 18).

  Reported per hour (CSV) and per session (report).

### A5. Part 2: structural stops and R:R
- **Pivots:** p = 3 is primary, p = 5 secondary. Bar i is a swing high if H_i > max(H_{i−p..i−1}) and H_i ≥ max(H_{i+1..i+p}). It becomes usable at bar i+p. Swing lows mirror this.
- **Swing stop (long):** take the most recent confirmed swing low with price < C_t among the last 10 confirmed lows. Stop = SwL − buf.
  - Primary buf = max(2 ticks, 0.10·ATR). Secondary buf = 0.30·ATR (beyond the typical sweep depth, `orderflow_micro.final.md`).
  - Short mirrors with swing highs. With no qualifying swing, the stop is "none" and counted as INCOMPLETE.
- **Swept-level stop:** on E2 sweep-and-reclaim events (E2 A2 definition), stop = the extreme of the bars t−2..t of that session day that traded beyond PDL (or PDH) ± buf.
- **DOL target:** E2 A2 candidates: PDH and PWH, plus the 5 most recent confirmed swing highs (p = 3) not yet traded through. The target is the nearest one above C_t for longs; shorts mirror. If there is none, the target is "none" (INCOMPLETE).
- Measures:
  - S = |C_t − stop| and D = |target − C_t|, in ticks and ATR;
  - RR_gross = D/S;
  - **RR_net = (D − c)/(S + c)**;
  - CRR = c/S;
  - shares with RR_net ≥ 1, RR_net ≥ 2, CRR ≥ 0.10 and CRR ≥ 0.25.
- Taken over all eligible bars, both directions, and at E2-C1/C2 signal bars.

### A6. Data guards
- C1M/C1H index futures: guard bars are the reopen bars at the quarterly rolls:
  - 2025-06-08 22:00, 2025-09-01 00:00, 2025-12-14 23:00 and 2026-03-15 22:00 UTC (1h, from E2);
  - in 1m data, the first bar at or after those times.
- CL: a bar whose open gap exceeds 10 robust σ of 1m open-close returns, or which follows a hole longer than 50 h.
- GC: de-interleave guards (A1).
- Windows and trades that span a guard bar are dropped.
- In gap statistics (A8), guard bars are reported separately and never counted as market gaps.

### A7. Part 3: the TRADEABILITY metric and its out-of-sample test
**Definition**, at the close of bar t, for direction d:
- c = BASE RT cost (price units).
- EM_H(t) = ATR_t × m_h. Here m_h is the in-sample median of MFE_dir/ATR at ET hour h, for that dataset and H, frozen from the IS segment. In Pine it is a rolling per-hour median of completed windows only.
- Reward Rw = min(D, EM_H). With no target, Rw = EM_H and the trade is flagged INCOMPLETE (no target).
- Risk S = primary swing-stop distance.
- **TQ = (Rw − c) / (S + c)**.
- Components: **CMR = c / EM_H** (cost-to-move) and **CRR = c / S** (cost-to-risk).

**Signal proxies** (no E2 result is used; the definitions are copied from the E2 pre-registration):
- P0: random direction, seed 12, non-overlapping entries every H bars from the first eligible bar.
- P1: E2-C1 STRUCT_MOM, FAST mode, onsets.
- P2: E2-C2 SWEEP_RECLAIM, FAST mode, onsets.
- While a trade is open, further signals are ignored.

**Trade engine:**
- Entry at O_{t+1}. Stop and target prices are fixed at bar t.
- Skip (and count) the trade if O_{t+1} is already beyond the stop or the target.
- Bracket over bars t+1..t+H:
  - stop and target both inside one bar → the shortest-path rule (bullish bar O-L-H-C, otherwise O-H-L-C) is primary; stop-first is the sensitivity case;
  - a bar that opens beyond the stop fills at its open (gap risk);
  - time exit at C_{t+H}.
- With no target, there is only a stop and a time exit.
- Outcomes:
  - R_gross = d(exit − entry)/S_e;
  - **R_net = (d(exit − entry) − c)/(S_e + c)**;
  - PnL_net in ticks;

  where S_e = |entry − stop|.
- H = 12 is primary.

**Splits:** chronological, IS = the first 60% of bars and OOS = the last 40%, with an embargo of H bars.

**Bands:**
- Relative bands: tercile cut points of TQ from the IS trades of the same proxy and dataset.
- Absolute bands: TQ < 0.5 POOR, 0.5-1.0 MARGINAL, ≥ 1.0 OK.

**Datasets:**
- NQ and MNQ at 1m, 5m, 15m and 1h (NQL);
- ES, MES, YM and RTY at 1h (C1H);
- ES, MES, YM, RTY, CL and GC at 5m and 15m (C1M);
- BTC 1h.

**Hypotheses:**
- **H3a (primary).** OOS mean R_net(bottom TQ tercile) − mean R_net(top tercile) < 0, with the 95% block-bootstrap CI excluding 0 (trade level, blocks of 10 consecutive trades, 5,000 reps).
  - Evaluated per dataset × proxy cell, with ≥ 30 OOS trades in each tercile.
  - **Supported** if it holds in ≥ 60% of the evaluable P0 cells AND in ≥ 2 instruments other than NQ/MNQ.
  - BH at q = 0.10 across all evaluable cells (one-sided bootstrap p).
- **H3b (mechanism).** The same difference for R_gross. The expectation is that its CI includes 0. A significant gross difference is reported as a finding.
- **H3c.** OOS mean R_net in the POOR band < 0, with the CI excluding 0.
- **H3d (descriptive).** OOS Spearman ρ(TQ, R_net) vs ρ(−CRR, R_net) and ρ(−CMR, R_net), with bootstrap CIs.
- Cost sensitivity: H3a re-run at the LOW and STRESS costs (descriptive).

### A8. Part 4: gaps and events
**Gaps:**
- Daily reopen gap = O(first bar at or after 18:00 ET following the 17:00-18:00 halt) − C(last bar before the halt).
- Weekend gap = Sunday reopen vs Friday last close. Holiday breaks are reported separately.
- RTH gap = O(09:30 ET bar) − C(last bar before 16:00 ET of the previous session day). This matters for RTH-only charts.
- Size is reported in ticks, in units of the 1h ATR(14) at the pre-gap bar, and as a share of the daily ATR(14).
- Frequency of |gap| ≥ 1 tick, ≥ 0.25, ≥ 0.5 and ≥ 1 ATR1h.

**Effect on stops:**
- For hypothetical long and short positions held through the break with the primary swing stop at the pre-gap bar (1h chart; 5m sensitivity):
  - P(reopen beyond the stop);
  - given a gap-through, the excess loss beyond the stop in R = |O − stop|/S.
- Compared with all non-gap bars.

**Scheduled events:**
- FOMC statement days at 14:00 ET, 2023-2025: 24 dates from the Federal Reserve calendar (section E).
- The 08:30 ET release time on all weekdays (proxy for CPI, NFP, claims, retail sales), and "first Friday" 08:30 as an NFP proxy (labelled proxy).
- Data: NQL 1m (2022-12 → 2025-12) and C1M 1m (2026; no FOMC dates used for 2026).
- Metrics:
  - ratio of mean 1m true range in [release, release + 5 min) on event days vs the same clock window on other days;
  - for 08:30, vs 08:00-08:29 on the same day;
  - P(a primary 5m swing stop set at the bar before the release is hit within 30 min), event vs non-event days at the same clock time;
  - the excess beyond the stop on the breach bar, as an upper bound on stop slippage.

**Event-window input:** a design deliverable, informed by the measured ratios. It is not a pass/fail test.

### A9. What is NOT tested
- Real bid-ask spreads, queue position and fill probability: no quote data. Spread and slippage are documented assumptions with a sensitivity range.
- News events other than FOMC and the 08:30 proxy: there is no verified calendar offline.
- Execution delay: modelled only as entry at the next bar open.
- The 2026 FOMC dates (not verified).

---
