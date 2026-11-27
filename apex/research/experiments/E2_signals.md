# E2_signals: BUY/SELL signal logic vs simple baselines after costs (R1 + R6)

Status: PRE-REGISTRATION written 2026-11-27 ~10:05 UTC, before any signal result was computed. Data inspection only, no outcomes, was done before writing it: columns, time zones, gaps and roll jumps. The SHA-256 of this section is stored in `apex/validation/python/experiments/E2_signals/out/prereg.sha256` with a timestamp, before the first run.
Results are appended below the pre-registration. Any deviation from it is listed in section D ("Deviations").

---

## A. PRE-REGISTRATION (frozen)

### A0. Question
Which BUY/SELL signal logic adds value after costs, out of sample, against simple baselines? The logic covers spec 13.3: STRONG BUY / BUY / NEUTRAL / SELL / STRONG SELL, FAST and BALANCED modes, confirmation and persistence, with NEUTRAL allowed.

Prior expectation, stated before testing, from the completed study (`ict_struct.final.md`, `ict_liq.final.md`, `academic_sr.final.md` S20 / Mesfin 2026, and the MNQ ORB lessons):
- confirmed structure carries ~0 directional information;
- sweeps that close back inside lean slightly toward continuation, not reversal;
- OHLCV intraday momentum families fail after costs on MNQ (0 of 14).

So the prior is that **no candidate passes**. A null result is an acceptable outcome.

### A1. Data (inspected for format only)
| ID | Instrument / TF | Source | Period | Notes |
|---|---|---|---|---|
| D1 | NQ 5m | `i2/dl/data_src/data/Dataset_NQ_1min_2022_2025.csv` resampled | 2022-12-26 → 2025-12-11 | ET, bar-close-labelled (first bar 18:01, last 17:00), so shifted −1 min to open time. Back-adjusted continuous: no roll jumps, checked against the CME 1h file, whose stepped offsets of 217/232 pts sit at the CME file's rolls. |
| D2 | NQ 15m | same | same | |
| D3 | NQ 1h | same | same | |
| D4 | ES 1h | `amt_data/cme/ES` | 2025-03-21 → 2026-04-15 | UTC → America/New_York. Unadjusted: roll guard (A6). |
| D5 | YM 1h | `amt_data/cme/YM` | same | roll guard |
| D6 | RTY 1h | `amt_data/cme/RTY` | same | roll guard |
| D7 | CL 1h | `amt_data/cme/CL` | 2025-06-01 → 2026-04-15 | Monthly rolls not identifiable, and the data has multi-day holes (one of 23 days). Jump/gap guard. LOW QUALITY. |
| D8 | BTC 1h | `classic_tools/btc_1h.csv` | 2016-01-01 → 2025-01-07 | UTC spot. No rolls. |

GC is excluded: the study found its 1H file interleaves two contract months.

Bars are resampled left-labelled on the clock in local time: ET for futures, UTC for BTC. The session day is the ET date of (ts + 6 h) for futures, because Globex opens at 18:00 ET, and the UTC date for BTC.

### A2. Features (all computed at the close of bar t from bars ≤ t)
- `ATR14`: Wilder ATR(14) of the chart TF.
- **Confirmed pivots**, p = 3: bar i is a swing high if H_i > max(H_{i−3..i−1}) and H_i ≥ max(H_{i+1..i+3}). It becomes usable only at bar i+3, its confirmation bar. Swing lows mirror this.
- **Structure state `struct_t` ∈ {−1, 0, +1}**:
  - bullish break when C_t > the most recent confirmed swing high that is not yet broken;
  - bearish break when C_t < the most recent confirmed, unbroken swing low;
  - `struct` = direction of the last break. A break with the current bias is a BOS, against it a CHoCH. Both set `struct`. It starts at 0.
- **Momentum**: z_t = (C_t − C_{t−20}) / (ATR14_t·√20); `mom_t` = tanh(z_t).
- **Trend / HTF proxy**: EMA20 and EMA50 of close. `htf_t` = sign(EMA80_t − EMA80_{t−4}), where EMA80 on the chart TF stands in for EMA20 on a 4× higher TF. This avoids HTF request lookahead.
- **Prior-day liquidity**: PDH and PDL = high and low of the previous complete session day.
- **Sweep-and-reclaim event (bullish)** at bar t:
  - the low of bar t, or of one of the 2 preceding bars in the same session day, is below PDL;
  - C_t > PDL;
  - it is the first bullish event of that session day.

  The bearish event mirrors this with PDH.
- **DOL levels**:
  - buy-side candidates above price: PDH, the prior session-week high PWH (ISO week of the session day), and the 5 most recent confirmed swing highs not yet traded through;
  - sell-side candidates mirror these;
  - d_up = (nearest level above − C)/ATR and d_dn = (C − nearest level below)/ATR, each capped at 10. A side with no level gets 10;
  - `dol_t` = (d_dn − d_up)/(d_dn + d_up) ∈ (−1, 1). Positive means upside liquidity is nearer, i.e. "more reachable".

### A3. Candidate family (raw state r_t ∈ {−2, −1, 0, +1, +2})
| ID | Name | Score / rule | BUY (+1) | STRONG BUY (+2) |
|---|---|---|---|---|
| C1 | STRUCT_MOM: confirmed-structure bias + momentum | S = 0.5·struct + 0.5·mom | S > 0.5 (struct = +1 and mom > 0) | S ≥ 0.75 (struct = +1 and mom ≥ 0.5) |
| C2 | SWEEP_RECLAIM: PDH/PDL sweep-and-reclaim + structure confirm | A bullish event within the last W = 12 bars, plus a bullish structure break at a bar ≥ the event bar, with struct still +1. Both sides active → 0. | event + confirm | + mom ≥ 0.5 |
| C3 | DOL_DIR: toward the nearer (more reachable) liquidity | S = dol | S ≥ 0.33 (upside level ≤ ½ as far) | S ≥ 0.6 (≤ ¼ as far) |
| C4 | COMPOSITE | S = (struct + mom + dol)/3 | S ≥ 0.4 | S ≥ 0.7 |
SELL and STRONG SELL mirror these. Everything else is NEUTRAL (0).

**Modes**:
- **FAST**: the emitted state s_t = r_t. Persistence K = 1, no HTF requirement.
- **BALANCED**: s_t = the sign of r_t only if r has had that same sign on each of the last K = 3 bars (t−2..t) AND `htf_t` agrees. Otherwise NEUTRAL. The level is STRONG if r_t = ±2.

That gives 4 candidates × 2 modes = **8 candidate variants**. No parameter is tuned on outcome data.

### A4. Baselines
- **B1 EMA trend**: state = sign(EMA20 − EMA50), always in the market.
- **B2 TSMOM**: state = sign(C_t − C_{t−48}).
- **B3 Random entry**: the same number of long and short entries as the candidate, at uniformly random eligible bars, with the same H and costs. 2,000 draws. One-sided permutation p = share of random means ≥ the candidate's mean.
- **B4 Always flat**: return 0 and Sharpe 0. A candidate must have a positive net mean.
- **B5 Buy and hold** over the same segment, with costs charged once.

### A5. Trade engines
- **Primary (pass/fail): onset + fixed horizon.**
  - Enter at bar-t close when, while flat, s_t turns to direction d ≠ 0 from a state that was not d (an onset).
  - Fill at O_{t+1}. Exit at O_{t+1+H}, with **H = 12 bars**.
  - While a trade is open, signals are ignored: no pyramiding, no reversal.
  - Net PnL = d·(exit − entry) − round-trip cost. Return = PnL/entry. R = PnL/ATR14_t; the ATR is only a risk unit, no stop is executed.
- Secondary horizons: H = 6 and H = 24.
- **Secondary engine: state-held.** Position p_t = sign(s_t), held from O_{t+1} to O_{t+2}, with costs charged per unit of position change. The always-in EMA and TSMOM baselines use the same engine.

### A6. Costs (per side; round trip = 2×)
| Instrument | Slippage | Commission + fees | Per side (price units) |
|---|---|---|---|
| NQ | 1 tick (0.25) | $2.50 (0.125 pt at $20/pt) | 0.375 pt |
| ES | 1 tick (0.25) | $2.50 (0.05 pt) | 0.30 pt |
| YM | 1 tick (1.0) | $2.50 (0.5 pt) | 1.5 pt |
| RTY | 1 tick (0.1) | $2.50 (0.05 pt) | 0.15 pt |
| CL | 1 tick (0.01) | $2.50 (0.0025) | 0.0125 |
| BTC | 0.01% | 0.04% taker | 0.05% of price |

A stress test doubles slippage (2 ticks, or 0.02%). It is a sensitivity check, not a trial.

**Data guards**, applied identically to every strategy and baseline:
- **D4-D6 (roll guard):** drop trades whose holding window contains one of the 4 roll bars, identified as coincident NQ/ES/YM/RTY reopen jumps in the quarterly roll windows (2025-06-08 22:00, 2025-09-01 00:00 and 2025-12-14 23:00 UTC; the first two were confirmed against the back-adjusted NQ 1m data), plus 2026-03-15 22:00 UTC. Zero those bars' returns in the state-held and buy-and-hold series.
- **D7:** drop trades that span a data hole over 50 h, or a bar whose open gap is above 8 robust σ.
- **All datasets:** drop trades that span a data gap over 4 days.

### A7. Splits
- **Chronological:** IS = the first 60% of bars, OOS = the last 40%, with an embargo of H bars. IS trades must exit inside IS; OOS entries start H bars after the IS end.
- **Walk-forward selection:**
  - 5 equal chronological folds;
  - for k = 2..5, choose among the 8 candidate variants the one with the highest Sharpe on folds 1..k−1 (expanding window, primary engine, H = 12);
  - trade it on fold k, after an embargo of H bars;
  - concatenate the results as "WF-selected".

### A8. Metrics
- n trades;
- hit rate (net > 0) with a Wilson 95% CI;
- average net R and average net return per trade (bp), with a block-bootstrap CI;
- profit factor;
- annualised Sharpe of the daily series (trade returns booked on the exit session day, zero on days without exits; √252 for futures, √365 for BTC), with a circular block-bootstrap 95% CI (block 10 days, 2,000 reps);
- max drawdown of cumulative daily returns, in % of price;
- trades per session day;
- % of bars NEUTRAL;
- **DSR** (Bailey & López de Prado 2014), with N = all variants tried on the dataset: 8 candidates + 2 baselines, × 3 horizons × 2 engines = **60**;
- **PBO** by CSCV (S = 16 blocks of the daily-return matrix across the 60 variants, full sample).

### A9. Pass criterion (per candidate variant × dataset, OOS segment, primary engine, H = 12, base costs)
All of the following must hold:
- **P1:** n ≥ 30 trades.
- **P2:** OOS Sharpe > 0, with the bootstrap 95% CI lower bound > 0.
- **P3:** OOS Sharpe > max(B1, B2) OOS Sharpe on the same engine and H.
- **P4:** random-entry permutation p < 0.05, AND the test survives Benjamini-Hochberg at q = 0.10 across all 8 × 8 = 64 candidate × dataset tests.
- **P5:** DSR ≥ 0.95 with N = 60.

**"Adds value"** requires passing on ≥ 3 of the 8 datasets, including ≥ 1 non-NQ dataset, with PBO < 0.5 on those datasets.

**"Weak evidence"** means the OOS point Sharpe is > 0 and > the baselines, but P2, P4 or P5 fails.

### A10. Secondary hypotheses (descriptive, reported with CIs, no pass/fail weight)
- **H-STRONG:** trades that enter at STRONG have a higher mean net R than trades entering at plain BUY/SELL, within each candidate (OOS, pooled over datasets).
- **H-BAL:** BALANCED has a higher mean net R per trade than FAST for the same candidate (OOS).
- **H-COST:** a candidate that passes at base costs still has a positive OOS mean at the stress cost.
