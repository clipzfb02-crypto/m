# I2 · Signal and backtest lineage (Phase 1 workspace inspection)

Inspector: I2 (signal and backtest lineage). Date: 2026-11-27.
Scope: three earlier projects by the same user that produced BUY/SELL signals or backtests:

| Project | Files inspected (read in full) | Origin commit |
|---|---|---|
| A. XAUUSD Fast/Balanced Pro | `apex/legacy/XAUUSD_Fast_Balanced_Pro.pine` (1,248 lines), its README (4 bytes: `# m`) | `b2741c2`, branch `arena/01a08150-m` |
| B. Buy/Sell Indicator | `apex/legacy/buy_sell_indicator.pine` (117 lines), its README (100 lines) | `0f261a2`, branch `claude/tradingview-buy-sell-indicator-u0m9ke` |
| C. MNQ 5m ORB | `apex/legacy/mnq_orb/`: indicator (306), strategy (149), README (159), `backtest.py`, `bt.py`, `final_ref.py`, `ind_ref.py`, `prepare_data.py`, `fetch_data.sh`, `verify.py`, `validate.cjs`, `run_pinets.mjs` | `99f7390`, branch `claude/jolly-cerf-5bmcgk` (history: `1ea6cfe` → `095139f` → `9e0b0ce` → `99f7390`) |

Provenance check: every legacy copy is byte-identical to its origin commit (`git show <commit>:<path> | diff`). The copy omits three files that exist on the origin branch; I read them with `git show`: `research/verify_pinets/package.json` (pins `pinescript-v6-validator 0.4.3` and `pinets 0.10.0`), `research/.gitignore` and `research/verify_pinets/.gitignore`.

No source file was modified. All runs used copies in my own scratch directory.

**Evidence labels used below.** Concept class: **E** = established market mechanics or exchange documentation; **A** = academic or statistical evidence; **D** = discretionary practitioner theory; **C** = contested or unsupported by tests. Evidence grade: strong / moderate / weak / none.
- "[ran]" means I executed it in this session.
- "[doc]" means checked against the local Pine v6 docs mirrors.
- "[study]" means taken from a verified study report.
- "[claim]" means the legacy README says so, but the code that produced it was never committed.

---

## 0. Executive summary

1. **FAST and BALANCED, as the user first defined them (project A), are threshold presets on one shared engine.** No logic changes between modes. BALANCED raises the minimum score (42 → 58) and the alignment count (1 → 2), doubles the cooldowns (3 → 6, 2 → 4), tightens the chop and chase vetoes (85 → 68, 85 → 62), and adds an extreme-volatility veto. That idea is worth keeping. The thresholds were never tested (§2.5).
2. **Project A does not compile on TradingView.** `f_killLines()` (lines 731-746) reassigns global variables inside a function, which the v6 manual says "causes a compilation error" [doc]. The static validator and PineTS both missed it [ran].
3. Project A has four more correctness defects:
   - v6 lazy `and`/`or` starves `ta.crossover` of history in engines I and J (lines 458-459, 475-476).
   - `ta.highest`/`ta.lowest` are called inside `if` (lines 345-346).
   - The "calendar day" session VWAP never resets on a 24-hour session string (lines 99, 245) [doc-reasoned].
   - Its HTF pattern (`expr[1]` + `lookahead_off`, lines 360-364) updates at different times on historical and realtime bars [doc].
4. **Project A is a forced-signal design.** Ten engines are joined with OR, and a FAST score of 42 is enough to fire. The score adds correlated trend features as if they were independent. Five of its ten engines are ideas that the user's own later NQ testing (project C) or the study rejected (§2.6).
5. **Project B is not worth carrying forward.**
   - It is Pine v5 and has a compile error: `label.style_label_lower` does not exist [ran, doc].
   - Its "Show RSI signals" toggle hides all signals, and two inputs are dead.
   - Its 2-of-3 vote ANDs a state with events. On NQ 2023-2025, `min_signals = 3` never fired on 1H or 4H (0 bars), and the RSI + MA pair never co-occurred [ran].
6. **Project C is the only project with real test evidence, and I reproduced all of it.**
   - The unmodified `backtest.py` reproduced every README number exactly: 729 trades, 85.7% win rate, profit factor 1.24, +$4,548 [ran].
   - The unmodified PineTS harness printed `ALL CHECKS PASSED`: identical signals, trades, wins and net on every year and with the sweep filter on and off, with liquidity levels identical on every bar [ran].
7. **Project C's 85.7% win rate is almost entirely mechanical.**
   - With a 0.2R target and a 1R stop, a driftless random walk wins 83.3%. The cost-adjusted break-even is 84.6% [ran].
   - Random trade direction on the same days with the same geometry gives a median 83.3% win rate and PF 0.98 (2,000 draws).
   - The breakout direction does carry in-sample information: it beat 99.55% of the random-direction draws. However, the bootstrap 95% CI for mean P&L per trade is **−$0.52 to +$12.60** (t = 1.87).
   - The 2026 data contradicts the rule on the MNQ file (PF 0.74, 41 trades).
8. **Project C's holdout was spent.**
   - The original 0.5R rule lost on both 2026 files (−$224 NQ, −$1,674 MNQ). The default was then changed to 0.2R *after* seeing 2026, and the README honestly says so.
   - The chosen cell (15-minute range, 0.8 strength) is the best of the 0.2R design grid. Five of its eight neighbouring cells have PF below 1 in at least one period [ran].
9. **The PineTS harness is a good template, but it proves less than it appears to.**
   - It proves agreement between two implementations written by the same author, on the constructs the script uses.
   - It does not prove TradingView compiles the script. It has no realtime or rollback test, and it does not exercise `request.security`.
   - It does not assert the strategy-level results: those are only printed.
   - PineTS also diverged from documented TradingView semantics on the XAUUSD VWAP: VWAP equalled hlc3 on every bar [ran].
   - §5 specifies exactly how it works and the layers APEX must add.
10. **Lessons the data supports.** Use next-bar-open fills, stop-first resolution of same-bar ambiguity, explicit cost stress, design/validation/holdout splits and neighbour-grid robustness. Always report win rate beside its geometric break-even. Ideas rejected by data in this lineage:
    - sweep fades;
    - EMA-pullback + VWAP;
    - RSI(2) mean reversion;
    - HTF, VWAP, ADX, volume, gap and OR-size filters;
    - limit retest entries;
    - the sweep-first filter (failed out of sample).

---

## 1. What I ran in this session (test evidence)

Environment:
- Data and tools sit in my own scratch tree, `/tmp/claude-0/-home-user-m/7ce60006-3639-59b1-8cd3-87355409d58a/scratchpad/i2/`. It is session-specific and may be cleared; Appendix A has the commands to rebuild it.
- Python 3.13.18 venv: numba 0.68.1, pandas 3.1.1, numpy 2.5.5.
- Node v22.23.5 with the originally pinned `pinets 0.10.0` and `pinescript-v6-validator 0.4.3`.
- I left the other team member's PineTS 0.13.1 install in `scratchpad/pine_harness/` untouched.

Data: the public repository named in `fetch_data.sh`, fetched exactly as that script does. It is at HEAD `0ee4392`, dated 2026-07-05, which predates the original 2026-09-30 run, so it is very likely the same files. SHA-256 of each file:
- `Dataset_NQ_1min_2022_2025.csv`: `1577e60a…b60b`. NQ 1-minute, 2022-12-26 18:01 to 2025-12-11 20:52 ET. It has exactly 1,048,576 lines, Excel's row limit, so the file was probably truncated. Late December 2025 is missing; 2025 has 244 RTH days.
- `NQ_5min.csv`: `426e04d2…6aac`. 2026-02-17 to 2026-04-28.
- `mnq_2026_1min.csv`: `5eb2bd28…6835`. UTC. Rows before 2026-03-04 17:00 are off the 0.25 tick grid (synthetic) and are dropped by `prepare_data.py`.
- After resampling, NQ 2023-2025 has 209,752 5-minute bars. The NQ 2026 set has 13,767 and the MNQ 2026 set has 11,487.

| # | Test | Result |
|---|---|---|
| T1 | `prepare_data.py` + `backtest.py`, unmodified | **Every README table reproduced exactly**: per-year, holdout, sweep filter, indicator semantics, TP trade-off, neighbour grid, cost stress, 26/36 profitable months, median stop 89.8 pts, p90 169.0 pts. Output: `scratchpad/i2/backtest_output.txt`. |
| T2 | `verify.py` PineTS harness, unmodified, pinned versions | **ALL CHECKS PASSED** in 4 min 41 s. Indicator signals identical on 2023/2024/2025 (251/248/230 signals), with trades, wins and net equal to 1e-6. PDH/PDL/ONH/ONL and sweep flags identical on every bar. Strategy signals identical. Strategy winning trades: Python 212/213/201 vs PineTS 211/212/201 (printed, not asserted). PineTS net after costs: $832.00 / $1,975.00 / $2,004.50. Output: `scratchpad/i2/verify_output.txt`. |
| T3 | Static validator on all four legacy scripts | ORB indicator and strategy: 0 errors, 0 warnings. XAUUSD: 0 errors, 6 warnings (4 real, 2 false positives; see §2.11). Buy/sell: 1 error (`label.style_label_lower`) and 5 warnings. Output: `scratchpad/i2/validator_output.txt`. |
| T4 | My baseline analysis of the ORB rule (`orb_baselines.py`, Appendix B) | Mechanical win rate, geometry-matched random direction (2,000 draws), fade, bootstrap (10,000 resamples). See §4.10. |
| T5 | Buy/sell 2-of-3 firing counts on NQ 1H and 4H, 2023-2025 (`buysell_counts.py`, Appendix B) | See §3.5. |
| T6 | PineTS smoke run of the XAUUSD script on 6,000 NQ 5-minute bars | It ran with no error in 36 s, although TradingView would reject the script (§2.11 D1). VWAP output equals hlc3 on every bar, a PineTS divergence (§5.4). Signal counts cannot be interpreted, because the signal gate depends on `strategy.position_size`. |

Not run, and not possible offline: TradingView compilation, the TradingView Strategy Tester, Bar Replay and realtime behaviour, for all three projects.

---

## 2. Project A · XAUUSD Fast/Balanced Pro (`XAUUSD_Fast_Balanced_Pro.pine`)

### 2.1 Purpose and design
- A Pine v6 **strategy** (not an indicator), lines 51-65.
- It is a self-contained buy/sell system: it generates signals, places orders with a three-target partial-exit bracket, and shows the Strategy Tester's statistics on a dashboard.
- Header: "Optimised defaults: XAUUSD, 3-minute chart. Works on any symbol." No optimisation evidence exists anywhere: the README is just `# m`, and the branch holds only this file.
- Architecture comment (lines 7-29): regime → features → **10 independent setup engines joined by OR** → score 0-100 plus grade → FAST/BALANCED thresholds → anti-chop, anti-chase, duplicate, cooldown and session filters → entry with SL and TP1-3 → dashboard and alerts. It also says: "THERE IS NO GIANT 'AND' CONDITION ... any single one of them can open a trade."
- Non-repaint statement (lines 32-48): signals on closed bars, fills on the next bar, HTF via `expr[1]` with `lookahead_off`, pivots confirmed with a fixed delay.

### 2.2 Section map

| Lines | Section |
|---|---|
| 51-65 | `strategy()`: capital 10,000; fixed qty 1 (overridden by risk sizing); commission 0.07 cash per contract; slippage 3 ticks; pyramiding 4; `calc_on_every_tick = false`; `process_orders_on_close = false`; `max_bars_back = 1000` |
| 70-196 | Inputs, 11 groups |
| 201-259 | Core data: EMAs, momentum composite, ATR and BB compression, candle anatomy, session VWAP |
| 267-355 | Structure: manual pivots, BOS/CHoCH, range breakout, break-and-retest, compression box, one-bar sweep |
| 360-371 | HTF (5 `request.security` calls on 2 timeframes) |
| 376-445 | Regime: trend state, chop score, chase score, volatility state, regime label |
| 450-479 | 10 buy engines and 10 mirrored sell engines |
| 486-646 | Functions: SL, grade, buy and sell scores, table helpers |
| 651-694 | Mode thresholds, counters, partial-exit sizes, filter chain |
| 699-763 | Trade state (19 parallel arrays), line objects, `f_killLines`, `f_finalizeLines` |
| 768-889 | Trade management: TP1 partial + break-even, TP2 partial + trailing, bracket re-issue, close detection, array cleanup |
| 894-1057 | Signal execution: SL, plan, sizing, direction gate, `strategy.entry`/`exit`, label, lines, alert |
| 1063-1067 | Label housekeeping |
| 1072-1080 | Plots: EMA 21/55/200, VWAP, triangles, bar colour |
| 1085-1157 | Dashboard: signal panel plus real Strategy Tester stats |
| 1162-1248 | Debug table: why a raw setup was blocked |

### 2.3 Calculation inventory

| Lines | Name | Computes |
|---|---|---|
| 201-203 | `emaFast/emaMid/emaSlow` | EMA 21/55/200 of close |
| 206-208 | RSI, MACD, DMI | `ta.rsi(14)`, `ta.macd(12,26,9)`, `ta.dmi(14,14)` |
| 212-218 | `momBull/momBear` | Mean of three [0,1] terms: RSI mapped (30→0, 70→1); `ta.rsi(macdH,14)/100` (an RSI of the MACD histogram); DI+/(DI+ + DI−). The comment says the oscillators are averaged "so RSI, MACD and DMI cannot triple-count". `momBear ≈ 1 − momBull` inside RSI 30-70. |
| 221-223 | `atrRatio` | ATR(14) / SMA(ATR, 50) |
| 225-229 | `compRat` | BB width (4σ/mid, 20) / its 50-bar SMA |
| 232-242 | Candle anatomy | body ratio, wicks, engulfing (close beyond the prior bar's high/low), rejection (wick > 1.2 × body and > 32% of range) |
| 245-259 | `vwapVal` | Cumulative hlc3 × volume, reset on `newVwapSes`. Falls back to SMA(hlc3, 50) when no volume has been seen this session. |
| 267-283 | `f_pivHigh/f_pivLow` | Manual pivot over L = 4 bars each side, strict `>` so equal highs qualify. Returns the pivot value L bars late. |
| 288-314 | BOS/CHoCH | `ta.crossover(close, lastSwingHigh)`. BOS if `structDir >= 0`, CHoCH if `< 0`. The level is consumed (set to `na`) after a break. |
| 317-320 | Range breakout | Close crosses the prior 20-bar highest/lowest |
| 323-336 | Retest zone | Level and bar of the last breakout. Valid 1-14 bars later. |
| 339-349 | Compression box | When `compRat < 0.70`, store the 20-bar high and low. Active 12 bars. Expansion bar = range > 1 × ATR. |
| 352-355 | Sweep | Low below the prior 15-bar low and close back above it (mirror for highs) |
| 360-371 | HTF | 15m close and EMA21/55; 60m close and EMA21. `htfBull` = close > EMA21 > EMA55. |
| 376-379 | Trend | `bullTrend` = close > EMA21 > EMA55. `strongBull` adds the EMA200 conditions. |
| 382-392 | `chopScore` 0-100 | Points: ADX < 18/22; EMA21-EMA55 gap < 0.35 ATR; ATR ratio < 0.75; EMA-side flips ≥ 6/4 in 20 bars; 20-bar range < 3.5 ATR |
| 395-410 | `chaseB/chaseS` 0-100 | Points: distance from 10-bar low/high > 3/2.2 ATR; distance from EMA21 > 2/1.4 ATR; current bar range > 2.5 ATR |
| 413-415 | Volatility state | low < 0.75; high 1.6-2.8; extreme > 2.8 (ATR ratio) |
| 418-445 | `regimeStr` | Display only. Later assignments override earlier ones. No hysteresis. |
| 450-479 | Engines A-J | See §2.6 |
| 486-504 | `f_slLong/f_slShort` | min(12-bar low, last swing low, bar low) − 0.25 ATR, then the stop distance is clamped to [0.7, 2.4] ATR. A clamp at 2.4 ATR can put the stop *inside* the structure. |
| 507-511 | `f_grade` | A+ ≥ 82, A ≥ 68, B ≥ 55, else C |
| 515-573 / 576-634 | `f_scoreBuy/f_scoreSell` | Additive points plus alignment count (§2.7). Exact mirrors. |
| 671-678 | Partial sizes | TP1 40%, TP2 30%, TP3 = the remainder |
| 768-856 | Trade manager | Per open trade: detect TP1/TP2/TP3/SL from the bar's high and low; TP1 → move to break-even (+0.1R); TP2 → start a 1.2 ATR trail; re-issue the `strategy.exit` brackets; accumulate "model R" |
| 894-939 | Plan and sizing | Risk = 1% of equity / stop distance, floored to 0.01 units, capped at 50. Stop must be ≥ 0.98 × the minimum and TP1 ≥ 0.55 ATR. Direction gate: `canOpen*` allows a new trade only if fewer than `iMaxTrades` are open and the newest one is in the same direction. |
| 1107-1157 | Dashboard | Win rate over the last 250 closed exits; PF; net; expectancy per exit; max DD; average model R |
| 1162-1248 | Debug | The first failing gate for a raw setup: session, chop, chase, strict HTF, extreme vol, alignment, score, cooldown, opposite cooldown, SL/TP size, qty, max trades |

### 2.4 Inputs and defaults (main ones)
- Mode `FAST` (line 83); confirm on bar close `true` (86).
- EMA 21/55/200; swing L = 4; breakout lookback 20; sweep lookback 15; retest window 14 bars, tolerance 0.35 ATR; VWAP session `"0000-0000"` (99).
- RSI 14; MACD 12/26/9; DMI 14/14; ATR 14, ATR average 50; BB 20/50; compression threshold 0.70, window 12; expansion 1.0 ATR.
- All 10 engines ON (119-128).
- HTF confirmation `"15"`; HTF context `"60"`; strict HTF `false` ("HTF is supporting evidence, not a veto"); session filter `false` (`0800-2000`); extreme-volatility ratio 2.8.
- Risk 1%; max size 50; max trades 1; SL lookback 12, buffer 0.25 ATR, distance 0.7-2.4 ATR; minimum TP1 0.55 ATR; TP 1R/2R/3R at 40%/30%/30%; break-even after TP1 at +0.1R; trail 1.2 ATR after TP2.
- Visuals: EMA 21 and 55 shown, EMA 200 hidden, VWAP shown, bias bar colouring ON, arrows ON, labels with levels ON, level lines ON, at most 12 labels.

### 2.5 FAST vs BALANCED: the exact definition

| Setting | FAST | BALANCED | Lines | Note |
|---|---|---|---|---|
| Minimum score (0-100) | **42** | **58** | 131-132, 654, 898 | The practical maximum is about 96 (§2.7) |
| Minimum alignment groups (of 5) | **1** | **2** | 133-135, 655, 693 | Groups: EMA stack, BOS/CHoCH *on this bar*, momentum > 0.5, VWAP side > 0.15 ATR, HTF stack |
| Accept with 1 alignment if score ≥ | 72 | 72 | 136, 693-694 | Labelled "BALANCED" but applies to both; it changes nothing in FAST |
| Same-direction cooldown (bars) | **3** | **6** | 139-140, 656 | |
| Bars since *any* signal | **2** | **4** | 141-142, 657, 898 | Labelled "opposite signals" but compares `barsSinceAny`, so it also gates same-direction signals |
| Chop veto at chopScore ≥ | **85** | **68** | 144-145, 684-685 | Engines D, J and G are exempt |
| Chase veto at chase ≥ | **85** | **62** | 146-147, 686-687 | Engines D and J are exempt |
| Extreme-volatility veto (ATR ratio > 2.8 and score < 72) | off | **on** | 154, 690-691 | Reuses the "align exemption" input as its threshold (dual-use input) |
| Everything else | identical | identical | | Same 10 engines, weights, SL/TP, HTF role, session filter, confirm-on-close |

How to read it:
- The modes are **pure threshold presets**: FAST favours responsiveness and BALANCED demands more score, more agreement and more spacing. This matches APEX spec §13.3 ("FAST should favor responsiveness. BALANCED should require stronger confluence and confirmation").
- No threshold was ever calibrated or tested (no evidence in the repository).
- The alignment count double-counts correlated groups: the EMA stack and the HTF EMA stack, and the momentum composite against the trend.
- The "structure" group is true only on the break bar itself (`bosUp`/`chochUp` are one-bar events), so in practice 4 groups decide on most bars.
- Project A has no STRONG BUY or STRONG SELL state. The A+/A/B/C grade is the closest analogue.

### 2.6 Signal logic: the ten engines (buy side; sell is the mirror, lines 467-476)

| Engine | Line | Rule (on a confirmed bar) | Class, grade | Evidence and weakness |
|---|---|---|---|---|
| A Trend continuation | 450 | bullTrend and close > EMA21 and bull candle and (momBull > 0.45 or ADX > 20 with DI+ > DI−) | D, none | Fires on most bull candles in an uptrend. Only the cooldown and the one-trade gate stop a signal every few bars: a **forced-signal generator**. |
| B Pullback reclaim | 451 | bullTrend and low ≤ EMA21 (or EMA55) with close above it, bull candle, close > prior close, momBull > 0.33 | C, weak | The user's own NQ 5m test found the "EMA 9/21/50 trend pullback with VWAP lost money in 2023-24 in every stop/target combination (PF ~0.9)" [claim, project C README; code not committed] |
| C VWAP reclaim | 452 | Close crosses above VWAP, bull candle, momentum or RSI rising | C, weak | VWAP never resets (§2.11 D3), so the level is wrong. "VWAP side" was a filter that "didn't help consistently" [claim, project C]. |
| D Breakout | 453 | Close crosses the prior 20-bar high, range > 0.7 ATR, body > 40%, ATR ratio > 0.75, extension < 3.5 ATR | C, weak-moderate (negative) | The study grades ORB/breakout direction a coin flip in recent index data: Mesfin 2026, 947 MNQ 5m days, ORB long T 1.17-1.50, short T −1.33/−0.04 [study: session_stats §2.10, quant_regime R5] |
| E Break and retest | 454 | Within 1-14 bars of a breakout, low comes within 0.35 ATR of the level and closes above it | C, weak | "Limit-order retest entries ... lowered the profit factor" [claim, project C] |
| F BOS | 455 | Close crosses the last confirmed swing high while structure is ≥ 0 | D, none | Confirmed pivots, not backdated |
| G Sweep reversal | 456 | Low below the prior 15-bar low, close back above, bull candle, lower wick > 30%, close > prior close | C, moderate (negative) | Project C: "Fading sweeps ... lost money in most versions" [claim]. Study: post-sweep ±1 ATR race 0.497-0.510 whether the raid holds or rejects, and MNQ Asia grabs show no edge after friction [study: skeptic C4]. |
| H CHoCH reversal | 457 | First break against the prior structure, bull candle | D, none | |
| I Momentum shift | 458 | MACD cross, or RSI crosses 50, or DI cross; bull candle; above EMA21 or EMA55; momBull > 0.45 | D, none | **Lazy-evaluation defect** (§2.11 D2) |
| J Compression expansion | 459 | Compression box active, close crosses the box high, bull expansion candle | C, moderate (negative) | The study finds compression breakouts do not continue: NR7 first-break ±1 ATR race 0.482-0.515 against nulls 0.479-0.517 across 5m to D [study: quant_regime]. **Lazy-evaluation defect** (§2.11 D2). |

The name of the first true engine labels the signal (`buyWhich`, line 462).

Design weakness: OR-ing ten weak or contested triggers multiplies false positives. That is the signal-space version of the multiple-testing problem the study warns about: the best of 45 settings has E[max z] = 2.21 under the null [study: skeptic §0.8]. APEX spec §13.3 and §25 say: "Do not force a trade every candle." The only thing that limits signal frequency here is position state (`iMaxTrades = 1`).

### 2.7 Score composition (`f_scoreBuy`, lines 515-573)

| Feature | Points | Alignment +1? |
|---|---|---|
| close > EMA200 | 7 | |
| EMA21 > EMA55 | 7 | yes |
| close > EMA21 | 6 | |
| BOS this bar / CHoCH this bar | 10 / 8 | yes |
| structDir = bull | 6 | |
| 16 × momBull | 0-16 | yes if > 0.5 |
| ATR-ratio band (0.85-1.75 / 1.75-2.6 / < 0.85 / else) | 8 / 4 / 3 / 1 | |
| VWAP distance > 0.15 ATR / within ±0.15 | 8 / 4 | yes (first case) |
| Engulfing / rejection / bull candle | 6 / 5 / 3 | |
| Body > 50% | 4 | |
| Extension from 10-bar low < 1 / 2 / 3 ATR | 6 / 4 / 2 | |
| close > prior 20-bar high | 4 | |
| HTF bull / HTF not bear | 8 / 3 | yes (first case) |
| Chop penalty | −18 × chop/100 | |
| Chase penalty | −14 × chase/100 | |

Findings:
- The positive maximum is 96, so 100 is unreachable, and grade A+ (≥ 82) needs about 85% of the maximum.
- About 38-46 of the 96 points come from correlated trend-family measurements: EMA200 side, EMA stack, close vs EMA21, structDir, HTF EMA stack and range-high side. That is exactly what spec §8 forbids: "EMA stack, EMA slope and EMA separation ... Do not count them as three completely independent confirmations."
- The momentum composite (averaging RSI, MACD and DMI) is the one place where redundancy is handled. **Preserve that idea.**
- The weights are hand-set: no calibration, no documented rationale, no data-quality weighting.
- The score is shown as "SCORE" and "GRADE". It is never called a probability. That is good.

### 2.8 Filter chain (lines 681-694, 898, 920)
- A signal needs all of: raw engine OR; `okEval` (confirmed bar); session; not chop-blocked; not chase-blocked; not HTF-blocked (strict mode only); not volatility-blocked (BALANCED); alignment; minimum score; same-direction cooldown; any-direction spacing; valid SL/TP size; qty ≥ 0.01; direction gate (`canOpen*`).
- The **debug table** (lines 1166-1223) reports the first failing gate. That is a direct precursor of APEX's "reason codes" (spec §4.7) and is worth keeping as a concept.

### 2.9 Trade management and sizing
- Fixed R-multiple targets (1R/2R/3R) with 40/30/30 partial exits, break-even after TP1 and an ATR trail after TP2.
- The study's martingale result applies: before costs, brackets, partials, break-even and trailing stops reshape the outcome distribution but cannot create expectancy [study: trade_mgmt §1.4].
- Sizing floors quantity to 0.01 units. That suits a CFD; it is invalid for futures (whole contracts), so the assumption is instrument-specific.
- Commission of 0.07 per "contract" and 3-tick slippage are undocumented guesses.

### 2.10 Non-repaint status

| Item | Status | Evidence |
|---|---|---|
| Signal evaluation | OK: `okEval = not iConfirmOnly or barstate.isconfirmed` (681); a strategy with `calc_on_every_tick = false` | code |
| Fills | OK: market orders fill at the next bar's open (`process_orders_on_close = false`) | code; docs (strategies.md) |
| Pivots | OK: confirmed L = 4 bars late, never backdated. Events are dated at the confirmation bar. | lines 267-286 |
| HTF requests | **Partial.** `request.security(..., expr[1], lookahead = barmerge.lookahead_off)` (360-364) leaks no future data. However, the docs say a `lookahead_off` series "has a new historical value at the *end* of each HTF period", while on realtime bars it returns the developing bar's evaluation. Historical bars therefore lag one extra HTF bar compared with live. The documented non-repainting pattern is "an `expression` argument that only references past bars (e.g., `close[1]`) while using `barmerge.lookahead_on`". | [doc] concepts/other-timeframes-and-data.md §Lookahead, §Avoiding repainting |
| Cooldown counters | **Risk.** They increment on `barstate.isnew` (665-668). The docs: "on historical bars, barstate.isnew is true on the bar's close, yet in realtime, it is true on the bar's open". Behaviour in a close-only strategy is not documented, so this is unverified. Bar-index arithmetic would be safer. | [doc] concepts/repainting.md:255 |
| Labels | Historical labels are re-texted when a trade closes (865-866). This is intentional annotation, not signal repaint. | code |

### 2.11 Defects (broken, duplicated, dead)

| ID | Severity | Lines | Defect | Evidence |
|---|---|---|---|---|
| D1 | **Blocker** | 731-746 | `f_killLines()` assigns `lnEnt := na` (and the other line variables) to **global** variables inside a function. The manual: "user-defined functions ... *cannot modify* those variables using the reassignment or compound assignment operators", with an example that "causes a compilation error". The script cannot compile on TradingView. | [doc] language/user-defined-functions.md:811-829, :1139-1141; jabez4jc type_system.md:1291. Not caught by the validator or by PineTS [ran]. |
| D2 | High | 297-298, 458-459, 475-476 | Pine v6 evaluates `and`/`or` lazily, so `ta.crossover`/`ta.crossunder` after a varying condition skip bars and corrupt their internal history. The worst case is engine J: `compActive and ta.crossover(close, compBoxHigh)`, where the cross is only evaluated while the box is active, so the first evaluation after a gap compares against a stale bar. Engine I's second and third crosses only run when the earlier ones are false. Lines 297-298 are benign in practice (the first evaluation after a new pivot cannot cross). | [doc] migration_guides/to_pine_version_6.md:777-807 ("interferes with the internal history ... and results in incorrect values"); release_notes.md:616. The validator does not check `and`/`or` operands [ran]. |
| D3 | High | 99, 245 | A VWAP session of `"0000-0000"` is a 7-day, 24-hour session, so `time(timeframe.period, iVwapSes)` is never `na` and `newVwapSes` fires only on the first bar. The VWAP never resets: it accumulates from the chart's first bar, while the tooltip promises "calendar day". | [doc] concepts/sessions.md:41-43 (24-hour session definition). Doc-reasoned, not executed on TradingView. PineTS gave VWAP = hlc3 on every bar instead (§5.4), so the two runtimes disagree and neither shows a daily reset. |
| D4 | Medium | 345-346 (also 395-396) | `ta.highest`/`ta.lowest` are called inside `if isCompress` (and inside ternary branches). Their history has gaps, so the box can come from non-consecutive bars. | validator S2 warnings [ran]; [doc] execution-model.md:886-890 |
| D5 | Medium | 360-364 | HTF timing differs between history and realtime (§2.10) | [doc] |
| D6 | Medium | 801-856 | "AVG R (model)" is optimistic. If TP1 and SL are both touched in one bar, TP1 is credited first and the remainder is booked at the *new* break-even stop (846 uses the updated `st`), not the original stop. TP2 likewise. | code reading |
| D7 | Low | 136, 690-694 | One input (`iAlExmpt`, 72) is both the alignment exemption (labelled BALANCED, applies to both modes) and the extreme-volatility override | code |
| D8 | Low | 141-142, 898 | "Min bars between OPPOSITE signals" actually uses `barsSinceAny` | code |
| D9 | Low | 917, 939, 909-937 | Signals depend on trade state and equity (`canOpen*`, `qty ≥ 0.01`), so a BUY marker is suppressed while any trade is open. The markers therefore depend on path and settings. | code |
| D10 | Low | 862 | `f_finalizeLines()` runs for *any* closed trade, but the lines belong to the newest signal. That is wrong when `iMaxTrades > 1`. | code |
| D11 | Dead | 701, 871, 1003 | Array `tSL0` is written and removed but never read | grep |
| D12 | Duplication | 450-479, 515-634 | Buy and sell engines and scores are written twice as mirrors. One function with a direction argument would do. | code |
| D13 | Doc | 3-4, 94 | The "Optimised defaults: XAUUSD 3-minute" claim has no evidence. Tooltips assume 3m ("4 bars = 12 min"). | repo |

Validator false positives: S3 on `sumR`/`cntR` (lines 867-868). Those accumulators are intentionally persistent.

### 2.12 Performance risks
Low:
- 5 `request.security` calls on 2 contexts. The loops are tiny: pivot L = 4, at most 4 trades.
- 19 parallel arrays of at most 4 elements.
- Labels capped at 12. The dashboard and debug tables update only on `barstate.islast`.
- `max_bars_back = 1000` is generous but harmless.

### 2.13 Test evidence
- **None.** No backtest, Strategy Tester output, README results or test scripts exist. The dashboard shows live Strategy Tester stats on the user's own chart. That is honest ("nothing is fabricated", line 1083), but in-sample.
- My PineTS smoke run (T6) only shows that the code executes in that runtime.

### 2.14 The user's evident preferences (project A)
- Wants **FAST and BALANCED** modes, named exactly like that. The same words reappear in the APEX spec.
- Wants clear **BUY/SELL** markers with **Entry/SL/TP1/TP2/TP3** on the label and in alerts.
- Wants a **grade** (A+/A/B/C), a **regime** readout, and a **dashboard with real stats** (explicitly "nothing is fabricated").
- Wants a **debug "why not" mode**.
- Wants **confirmed-bar signals by default**, with a written non-repaint statement.
- Visual style: dark tables (`#101418`/`#1b2027`), a cyan header `#00e5ff`, buy `#00c853`/`#00e676`, sell `#ff3d00`, small text, triangles, optional bar colouring.
- Treats HTF as supporting evidence, not a veto, by default.

### 2.15 Recommendations

| Component | Verdict | Reason |
|---|---|---|
| FAST/BALANCED as threshold presets on one engine (§2.5) | **REWORK** | Keep the concept: same evidence engine; BALANCED raises the score threshold, the agreement count, the persistence and the spacing. Replace the hand-set numbers with thresholds tied to measured quantities, show them, and add STRONG states with persistence (spec §13.3). Fix the dual-use input (D7) and the "opposite" naming (D8). |
| Confirm-on-close gate + next-bar fills + non-repaint statement (lines 32-48, 86, 681) | **PRESERVE** | Correct and documented. Only the HTF and `barstate.isnew` items need the fixes in §2.10. |
| Momentum composite averaging RSI, MACD and DMI (212-218) | **REWORK** | The redundancy principle is right (spec §8). Use one normalised momentum feature with a documented transform, not three averaged oscillators including an RSI of the MACD histogram. |
| Chop score / chase score (382-410) | **REWORK** | The concepts map to spec §9 (regime) and §16 (poor location). Rebuild as normalised, percentile-based measures with hysteresis. Do not use point tables. |
| ATR-normalised thresholds throughout | **PRESERVE** | Instrument-agnostic (spec §13.1) |
| Manual confirmed pivots + BOS/CHoCH with consumed levels (267-314) | **REWORK** | Sound non-repaint logic, but superseded by the DOL v2 structure engine. Fix the lazy-eval exposure (D2). |
| Debug "blocked by" table (1162-1248) | **PRESERVE (concept)** | Becomes APEX's reason codes and debug dashboard, OFF by default (spec §17) |
| Dashboard of real strategy stats | **REWORK** | An indicator cannot read `strategy.*`. Use a ledger with geometry-matched baselines instead (§4.10, §5.5). |
| 10-engine OR trigger set (450-479) | **DROP** | A forced-signal design. Five engines are contested by data (§2.6). |
| Additive point score (515-634) | **DROP** | Counts redundant features. No calibration, no data-quality weights. |
| 3-target partial-exit trade manager (768-1057) | **DROP** from the indicator | APEX is an indicator, and exits cannot create expectancy [study: trade_mgmt §1.4]. At most, show one invalidation level and the measured R̄. |
| Session VWAP code (245-259) | **DROP** | Broken reset (D3). Use `ta.vwap` with an anchor, or `timeframe.change`. |
| HTF block (360-371) | **DROP** | Superseded by the DOL v2 `[1]` + `lookahead_on` pattern |

---

## 3. Project B · Buy/Sell Indicator (`buy_sell_indicator.pine`)

### 3.1 Purpose and design
A Pine **v5** overlay indicator (line 1). It counts how many of three conditions agree and signals when at least `min_signals` (default 2) do.

### 3.2 Section map and inventory

| Lines | Item |
|---|---|
| 2 | `indicator(..., timeframe = "")`: lets the user run the whole script on another timeframe |
| 9-30 | Inputs: RSI 14 (70/30); fast/slow MA 9/21, EMA or SMA; MACD 12/26/9; `min_signals` 2 (1-3); visual toggles |
| 37 | `rsi = ta.rsi(close, 14)` |
| 40-43 | MA (in a ternary on `ma_type`) and its crossovers |
| 46-48 | MACD and its crossovers |
| 55-62 | Conditions: `rsi < 30` (a **state**) and the MA/MACD crosses (**events**) |
| 65-70 | Vote count and threshold |
| 77-93 | MA lines, triangles, **background fills** on signal bars |
| 99-100 | `alertcondition` for buy and sell |
| 107-117 | Debug label on the last bar |

### 3.3 Signal logic and weaknesses
- It mixes a mean-reversion state (RSI < 30) with trend-following events (crosses). They measure opposite regimes, so they rarely coincide.
- There is no confirmation: signals and `alertcondition` are evaluated intrabar on the realtime bar. An alert set to fire once per bar can trigger on a cross that disappears by the close. That is realtime repaint.
- `timeframe = ""` lets a user pick a higher timeframe. Unconfirmed HTF values then repaint in realtime [doc: other-timeframes-and-data.md §Historical and realtime behavior].
- The README claims "reliable trading signals" and "better accuracy" with no test, and says "Last Updated: September 30, 2024", while the commit is dated 2026-09-30.

### 3.4 Defects

| ID | Lines | Defect | Evidence |
|---|---|---|---|
| B1 | 116 | `label.style_label_lower` does not exist, so the script fails to compile. The valid styles include `label.style_label_down`, `_up`, `_lower_left` and `_lower_right`. | validator error [ran]; no occurrence in either docs mirror, which list the valid constants [doc] |
| B2 | 81, 85 | Both signal plots are gated by `show_rsi`. Turning off "Show RSI Signals" hides **all** signals. | code |
| B3 | 28-29 | `show_ma` and `show_macd` are never used (dead inputs) | code |
| B4 | 113-117 | A new label every realtime bar on `barstate.islast`: old ones are never deleted (default label cap), and `var debug_text` is pointless | code |
| B5 | 1 | v5, not v6 | validator warning [ran] |
| B6 | 89-93 | Background fills, which spec §17 rejects | code |

### 3.5 Test evidence (none in the repository; my count, T5)
NQ 2023-2025, recomputed with the TV-equivalent `ema`/`rsi` from legacy `bt.py`. Counts only, no performance claim:

| Timeframe | Bars | min_signals = 1 (buy/sell) | = 2 (buy/sell) | = 3 | RSI+MA pairs |
|---|---|---|---|---|---|
| 1H | 17,396 | 1,925 / 2,747 | 52 / 99 | **0 / 0** | 0 / 0 |
| 4H | 4,718 | 447 / 844 | 14 / 24 | **0 / 0** | 0 / 0 |

- The README's "3: All 3 indicators must agree (most conservative)" setting **never fired** in 3 years on the timeframes the README recommends.
- `min_signals = 1` fires on every bar with RSI below 30 or above 70, which are long runs of consecutive bars.
- Lesson: never AND a persistent state with a one-bar event in a vote without a persistence window. A vote count does not make conditions independent.

### 3.6 Preferences evident
- Simple green/red triangles.
- A user-selectable strictness ("how many must agree"), the same intuition as FAST/BALANCED.
- Alerts.

### 3.7 Recommendations

| Component | Verdict | Reason |
|---|---|---|
| Whole script | **DROP** | Compile error, v5, contradictory logic, untested marketing claims |
| "How many independent groups must agree" knob | **REWORK** (concept only) | Already carried by project A's alignment count. In APEX it must count *de-correlated* evidence groups with persistence. |

---

## 4. Project C · MNQ 5m ORB (`apex/legacy/mnq_orb/`)

### 4.1 Purpose and design
A v6 indicator plus a matching strategy for **MNQ1!/NQ1! on 5 minutes only**, with a Python research pipeline and a PineTS equivalence harness. Rules (README §"The rules"; indicator lines 6-12):
- **Opening range (OR):** high and low of 09:30-09:44 NY (three 5m bars).
- **BUY:** the first bar between 09:45 and 12:00 NY that closes above the OR high with `(close − low)/range ≥ 0.8`. SELL is the mirror.
- **One signal per day.** A filtered breakout still consumes the day.
- **Stop** at the opposite OR side. **Target** = 0.2 × risk, rounded *down* to a tick. **Flat** at the 15:50 bar.
- **Liquidity add-on** (commit `99f7390`): PDH/PDL (prior 09:30-16:00) and ONH/ONL (18:00-09:30).
  - A level counts as "swept" once today's RTH high or low trades through it, including on the current bar.
  - Signals are tagged LIQ when opposite-side liquidity was swept.
  - An optional "only after sweep" filter is off by default.

### 4.2 Section maps
**Indicator** (`MNQ_5m_ORB_Signals.pine`):
- 27: `indicator()` with `max_lines_count = 500`, `max_labels_count = 500`.
- 30-55: inputs.
- 58-70: NY clock via `hour(time, "America/New_York")`; `isNasdaq` (`syminfo.root == "MNQ" or "NQ"`); `is5m`; `marketOk` lock; `newDay = timeframe.change("D")`.
- 73-84: OR accumulation.
- 90-130: RTH/ON accumulators, PDH/PDL roll, swept flags, sweep-bar markers.
- 133-197: trade tracking and stats replay, run only when `barstate.isconfirmed` and `bar_index > tBar`. The stop is checked before the target; a gap fills at the open; an EOD exit fills at the close; P&L is net of `costPts`.
- 200-223: signal (gated by `barstate.isconfirmed`), target rounding, lines, `alert()`.
- 226-243: plots (OR lines and fill, OR-window background, liquidity lines that fade when swept, ×-markers, BUY/SELL and LIQ labels).
- 245-247: `alertcondition`s.
- 250-306: stats table (status, OR, trades, win rate, PF, net in points and $ via `syminfo.pointvalue`, max DD, levels, cost note).

**Strategy** (`MNQ_5m_ORB_Strategy.pine`):
- 21-26: `strategy()`: commission $1.00 per contract per side, slippage 1 tick, fixed 1 contract, margin 0, close-only.
- 29-44: inputs. 47-59: clock. 62-73: OR. 78-107: liquidity.
- 110-120: signal, gated by `strategy.position_size == 0`.
- 124-132: `strategy.entry` + `strategy.exit(loss = slTicks, profit = tpTicks)`, measured from the **actual fill**.
- 134-135: `strategy.close_all` when out of hours, which fills at the next open (15:55).
- 138-149: plots.

### 4.3 Python inventory

| File · lines | Function | Computes |
|---|---|---|
| `prepare_data.py` 21-22 | `to_5m` | Resample to 5m, labelled by bar open (`label='left', closed='left'`) |
| `prepare_data.py` 25-40 | `main` | NQ 1m (NY time, close-labelled) is shifted −1 min to open labels. NQ 2026 5m is used as given. MNQ 2026 (UTC) is converted to NY, rows before 2026-03-04 17:00 (synthetic, off-grid) are dropped, and the rest resampled. |
| `bt.py` 7-26 | `_ema_seeded`, `ema`, `rma`, `sma` | TV-style EMA/RMA seeded with the SMA of the first n values |
| `bt.py` 28-53 | `rsi`, `true_range`, `atr`, `dmi` | TV-equivalent oscillators (used only by the uncommitted rejected-idea research) |
| `bt.py` 55-61 | `session_vwap` | hlc3 VWAP anchored at 18:00 ET (CME trading day) |
| `bt.py` 63-72 | `htf_ema`, `htf_close_prev` | Emulate `request.security(tf, expr[1], lookahead_on)`: last *completed* HTF value |
| `bt.py` 76-140 | `simulate` (numba) | Broker emulator: the signal decides on the close and fills at the next open; SL/TP distances are taken from the fill; same-bar SL and TP resolve stop-first if `conservative` (else an O-H-L-C path heuristic); gaps fill at the open; EOD exit at the next open after a `flat` bar; optional break-even and max-bars |
| `bt.py` 142-151 | `stats` | n, win%, PF, net, average, closed-trade max DD |
| `final_ref.py` 6-32 | `liquidity_levels` | PDH/PDL/ONH/ONL and running RTH high/low as known at each bar's close; SSL_SWEPT / BSL_SWEPT |
| `final_ref.py` 35-71 | `orb_strategy` | The final rules with Strategy-Tester semantics (CME trading-day reset at 18:00) |
| `ind_ref.py` 5-39 | `indicator_ref` | Indicator semantics (entry at the signal close, exact OR stop, EOD at the close; calendar-day reset) |
| `backtest.py` 17-101 | `row`, `by_year`, `main` | Every README table |
| `verify.py`, `validate.cjs`, `run_pinets.mjs` | harness | §5 |

### 4.4 Inputs and defaults
- OR 15 min; strength 0.8; TP 0.2R; last entry 12:00; flat 15:50; longs and shorts on; max-risk filter off; market lock on; sweep filter off.
- Display: OR, trade lines, table; cost 1.5 points.
- Colours: buy `#089981`, sell `#f23645`, OR `#2962ff`, prior-day `#ff9800`, overnight `#ab47bc`.

### 4.5 Signal logic: classification and weaknesses

| Element | Class, grade | Notes |
|---|---|---|
| Opening range as a reference | D concept; A support as a *unit* (moderate) | The study: "The only robust use of the opening range is as a **unit**" [study: session_stats §2.10] |
| ORB *direction* edge on index futures | **C, weak** | My reproduction: t = 1.87, bootstrap CI spans 0 (§4.10). Study: Mesfin 2026 (arXiv 2605.04004; 947 MNQ 5m days) ORB long T 1.17-1.50, short T −1.33/−0.04, year-unstable; Holmberg et al. 2013 positive on crude oil only [study: session_stats O2/O9, academic_sr S19-S20] |
| Strong-close filter (close location ≥ 0.8) | D, weak | Helped in both the design and validation periods per the README. In my grid reproduction, 0.9 fails at 0.2R (PF 0.87 in 2023-24) and 0.7 is mixed. |
| 0.2R target / 1R stop | E (mathematics), strong | The win rate is set by the geometry (§4.10) |
| PDH/PDL/ONH/ONL levels | E as reference prices; D as "liquidity" | Correct, non-repainting construction, verified bar by bar against Python [ran] |
| "LIQ" sweep tag / sweep-first filter | D; **C, weak** | Improved in-sample, failed on 2026 (§4.8). A "sweep" here is only a trade-through, with no reclaim. |

Weaknesses:
1. **Instrument and session hardcoding.** `syminfo.root == "MNQ"/"NQ"`, `is5m`, 09:30/16:00/18:00 NY constants, and a 0.25 tick in Python. Spec §2.1 says "Never hardcode calculations for XAUUSD or NQ".
2. **Early-close holidays are not handled.** A trade can be exited at the next session's first bar (README caveat).
3. The indicator's stats table replays **in-sample** on loaded bars with entry at the signal close. That is slightly optimistic against the strategy (2023-25 indicator semantics +$4,826 against strategy semantics +$4,548 [ran]). It is labelled "Trades (chart)", which is honest.
4. The tooltip "0.2 = ~86% win rate in testing" reports an in-sample frequency without the geometric baseline. Spec §15 wants base rates and baselines.
5. `sslSwept`/`bslSwept` include the signal bar (indicator 117-126; Python `RH/RL` "including the current bar"). This is consistent across implementations but contradicts the README's "earlier that morning".
6. The strategy's stop is fill ± ticks, not the OR boundary, and it flattens at the 15:55 open against the indicator's 15:50 close. Both differences are documented.

### 4.6 Non-repaint status
- **Clean.**
  - Signals and exits are gated by `barstate.isconfirmed` (indicator 152, 201). The strategy runs close-only.
  - There are no `request.security` calls and no pivots.
  - State is `var`-based, with resets via `timeframe.change("D")` and session-membership edges.
- Liquidity lines and the swept fade update live on the open bar. This is cosmetic and does not feed signals.
- Caveat: if a user switches the strategy to "Recalculate on every tick", `canSignal` (strategy 111) has no `barstate.isconfirmed` guard.

### 4.7 Backtest methodology and costs
- **Data:** a public third-party NQ 1m CSV for 2023-2025, resampled TradingView-style. Two separate 2026 files act as holdouts: NQ 5m (Feb 17 - Apr 28) and MNQ 1m (Mar 5 - May 1).
- **Semantics:**
  - Strategy-Tester semantics: decide on the close, fill at the next bar's open, SL/TP from the fill.
  - Same-bar stop and target resolve **stop first** (pessimistic).
  - Gaps through a level fill at the open.
  - EOD exit at the next open after the 15:50 bar or the last bar of the trading day.
- **Costs:** 1.5 points round-trip (= $3 per MNQ) on every trade. Stress runs at 2.5 and 3.5 points.
  - The Pine strategy instead charges $1 per side plus 1 tick of slippage on market and stop fills: about 1.25 pts on target exits and 1.5 pts on stop exits. Python is therefore slightly more conservative.
- **Splits:** design 2023-2024, validation 2025, holdout 2026 (spent; §4.11).
- **Robustness:** a 3 × 3 × 4 neighbour grid (OR minutes × strength × TP) scored separately on design and validation. Profitable-months count.
- **Max drawdown** is computed on closed-trade cumulative P&L. TradingView's includes open-trade equity, so the two differ.
- Data hygiene that was handled: close-label → open-label shift; synthetic MNQ rows dropped; DST-ambiguous timestamps dropped in the harness.
- Data hygiene that was not handled: the NQ file appears cut at Excel's 1,048,576-row limit (ends 2025-12-11, §1), and contract-roll treatment is unknown (continuous series of unknown construction).

### 4.8 Results (all reproduced exactly by T1; 1 contract, 1.5 pt cost, Strategy-Tester semantics)

| Period (data) | Trades | Win | PF | Net | Max DD |
|---|---:|---:|---:|---:|---:|
| 2023 (NQ) | 251 | 84.1% | 1.13 | +$724 | $1,344 |
| 2024 (NQ) | 248 | 85.9% | 1.34 | +$1,956 | $671 |
| 2025 to Dec 11 (NQ) | 230 | 87.4% | 1.24 | +$1,868 | $1,722 |
| 2023-2025 (NQ) | 729 | 85.7% | 1.24 | +$4,548 | $1,722 |
| 2026 NQ file (Feb 17 - Apr 28), not blind | 50 | 88.0% | 1.23 | +$477 | $1,295 |
| 2026 MNQ file (Mar 5 - May 1), not blind | 41 | 80.5% | **0.74** | **−$600** | $1,284 |

Original blind test of the 0.5R rule (commit `1ea6cfe` README, before retuning): 2026 NQ PF 0.96 (−$224, 50 trades) and 2026 MNQ PF 0.65 (−$1,674, 41 trades).

The bootstrap behind its sentence "about 1 in 4 ... below 3%" was never committed [claim].

Sweep-first filter [ran, matches README]:

| Period | OFF trades / PF | ON trades / PF |
|---|---|---|
| 2023-24 | 499 / 1.24 | 199 / 1.39 |
| 2025 | 230 / 1.24 | 91 / 2.11 |
| 2026 NQ | 50 / 1.23 | 23 / **0.83** |
| 2026 MNQ | 41 / 0.74 | 18 / **0.51** |

Cost stress [ran]: PF 1.24 at 1.5 pts, 1.16 at 2.5 pts, 1.08 at 3.5 pts.

### 4.9 Rejected ideas (what the data rejected)

| Idea | Result reported | Reproducible from the repository? |
|---|---|---|
| EMA 9/21/50 trend pullback + VWAP | Lost in 2023-24 in every stop/target combination, PF ~0.9 | **No** [claim]: `bt.py` has the EMA/VWAP helpers, but the test script was never committed |
| RSI(2) mean reversion | ~65% win rate but PF 0.87-0.97 in every variant: "A high win rate alone is not an edge" | No [claim] |
| 30-minute OR | Worked in 2023-24, failed in 2025 | No [claim] (the committed grid covers 10/15/20 only) |
| Filters: HTF trend, VWAP side, ADX, volume, gap direction, OR size | "didn't help consistently" | No [claim] |
| Extra trades per day; limit-order retest entries | Lowered PF | No [claim] |
| Liquidity-sweep reversal (fade) entries | "lost money in most versions" | No [claim]. Consistent with the study [study: skeptic C4, moderate] |
| Avoid trades with untouched liquidity just ahead | "no consistent effect" | No [claim] |
| Profit-lock (break-even) stops | Did not beat a plain 0.2R target | No [claim]. `simulate` supports `be_pts`, but no call uses it. |
| Targets below 0.2R | 88-92% win rate, "lost clearly on 2026 data" | **Yes** [ran]: 0.1R PF 1.14 IS / 0.58 on 2026 NQ; 0.15R 1.07 / 0.91 |
| Sweep-first filter | IS better, 2026 worse | **Yes** [ran] |

### 4.10 My baseline and uncertainty checks (T4)

**(a) Win rate against geometry** (2023-2025, 729 trades):

| TP (R) | Observed win | Random-walk win 1/(1+r) | Cost-adjusted break-even | EOD exits | PF |
|---|---:|---:|---:|---:|---:|
| 0.10 | 91.9% | 90.9% | 92.2% | 0.7% | 1.14 |
| **0.20** | **85.7%** | **83.3%** | **84.6%** | 1.8% | 1.24 |
| 0.25 | 82.6% | 80.0% | 81.2% | 2.3% | 1.22 |
| 0.50 | 69.1% | 66.7% | 67.6% | 8.8% | 1.23 |
| 1.00 | 55.7% | 50.0% | 50.7% | 24.0% | 1.26 |

- The break-even is `(ΣR + N·c) / ((1 + r)·ΣR)`, valid for trades that end at the full stop or the full target.
- The 0.2R default's edge is **about 1.1 pp of win rate over break-even**. This is the martingale identity BE = 1/(1+RR) [study: trade_mgmt §1.2], and it is why the README's own lesson "a high win rate alone is not an edge" applies to its own default.

**(b) Geometry-matched direction baselines** (same 729 entry bars, same stop and target distances, same exits; 0.2R):
- Rule (breakout direction): win 85.7%, PF 1.24, net +$4,548.
- Fade (opposite direction): win 80.8%, PF 0.80, net −$5,520.
- Random direction, 2,000 draws: median win 83.3% [2.5-97.5%: 81.1-85.3], median PF 0.98 [0.83-1.17], median net −$449 [−$4,512 to +$3,474].
- Share of random draws with net ≥ the rule's: **0.0045**.

This is in-sample, and the rule was picked from a grid, so the p-value is optimistic. Even so, it is the right *kind* of test: it isolates the directional content from the payoff geometry.

**(c) Bootstrap of the 729 trades** (10,000 resamples):
- Mean $6.24 per trade (t = 1.87); 95% CI −$0.52 to +$12.60; P(mean ≤ 0) = 0.034.
- PF 1.24; 95% CI 0.98 to 1.59.

**Verdict:**
- The directional content is real but small in-sample.
- It was not confirmed on the MNQ 2026 file.
- It is consistent with the study's independent result that ORB direction on recent MNQ data is weak and year-unstable [study: session_stats §2.10].
- Class C, grade weak.

### 4.11 Overfitting assessment
1. **The holdout was spent:** the 0.5R rule failed the 2026 blind test, then 0.2R was chosen after seeing it (commit `9e0b0ce`; README lines 93-94 say so). The commit title "Default to a 0.2R target for an ~86% win rate" suggests the target was retuned **to reach a win-rate goal**, not an expectancy goal.
2. **Selection at the edge of a fragile grid:** 15/0.8 is the best 0.2R cell in 2023-24 (PF 1.24). At 0.2R the 0.9 strength row has PF 0.87-0.93 in 2023-24, and the 10-minute row has PF 0.71-0.95 in 2025 [ran]. The README discloses this ("High win rate is more fragile").
3. **Forking paths:** at least 36 grid cells, 8 TP levels, the sweep on/off variants, and at least 8 uncommitted rejected families. That is far beyond the 45-setting example whose null E[max z] is 2.21 [study: skeptic §0.8]. The rule's in-sample t of 1.87 is below that.
4. **Data dependence:** the two 2026 files disagree (NQ PF 1.23 against MNQ PF 0.74 over overlapping dates). The README attributes this to tiny price differences flipping the "top 20%" test, which shows that a hard threshold on close location is brittle.
5. Good practice that should be kept: the README states the in-sample status, the cost stress and the losing 2026 file plainly.

### 4.12 Defects and limitations (Python and harness)
- The rejected-idea scripts and the bootstrap were never committed, so the claims are not reproducible.
- `row()`/`stats()` divide by the gross loss, which gives inf when there are no losses (cosmetic).
- `simulate` supports break-even and max-bars, but neither is used.
- `bt.py` oscillators are unused by any committed caller (dead in this copy).
- The verify harness's paths assume the original layout (`ROOT/pine`, `research/verify_pinets`). In the flattened legacy copy, `verify.py` cannot run until the layout is rebuilt (Appendix A).
- `package.json` is missing from the copy.

### 4.13 The user's evident preferences (project C)
- Plain-language README with a "Read this first" risk box.
- Wants a high win rate (the 0.2R retune).
- Wants honest statistics: per-year tables, cost stress, an explicit "not a blind test any more".
- Wants alerts with entry, stop, target and risk.
- Wants liquidity levels PDH/PDL and ONH/ONL with swept fading and × markers.
- Wants a compact stats table with a status line ("Watching for breakout", "Done for today").
- Asks for verification "three independent ways" because no TradingView compiler is available.

### 4.14 Recommendations

| Component | Verdict | Reason |
|---|---|---|
| Python simulator semantics (`bt.simulate`: next-open fill, stop-first, gap fills, EOD) | **PRESERVE** (as the APEX offline evaluator core) | Matches Strategy-Tester semantics. Reproduced exactly. |
| TV-equivalent indicator helpers (`bt.ema/rma/rsi/atr/dmi/htf_ema`) | **PRESERVE** (offline reference library) | Needed for Pine ↔ Python parity tests. `htf_ema` encodes the correct `[1]` + `lookahead_on` emulation. |
| `liquidity_levels` (PDH/PDL/ONH/ONL as known at the bar close) | **REWORK** | Correct and verified, but NY/CME-hardcoded. Generalise to configurable sessions and instruments. Make "swept" exclude the current bar where the semantics require it. |
| Backtest protocol (design/validation/holdout, neighbour grid, cost stress, per-year, monthly) | **PRESERVE + extend** | Add geometry-matched baselines, bootstrap CIs, a pre-registered holdout that is never retuned, deflated statistics and multi-instrument runs (spec §20). |
| PineTS equivalence harness | **REWORK** (template) | See §5.5 |
| ORB signal rule | **DROP** as an APEX signal | Instrument-hardcoded, weak and contested evidence, spent holdout |
| Opening range | **REWORK** | Keep only as a liquidity source (OR high/low pools, spec §4.1) and a volatility unit [study] |
| Sweep-first filter / LIQ tag | **DROP** as a signal booster | Failed out of sample. In APEX, sweeps describe lifecycle state, not reversal signals (spec §4.8). |
| Stats table on the chart | **REWORK** | Keep the honesty (labelled in-sample, per contract, after costs). Add the geometric break-even and baseline beside the win rate. |
| Clean status line ("Watching for breakout", "Done for today") | **PRESERVE (concept)** | Good UX for a minimal panel |

---

## 5. The PineTS verification harness: exactly how it works

### 5.1 Components and versions (origin `research/verify_pinets/`)
- `package.json`: `pinescript-v6-validator 0.4.3` and `pinets 0.10.0` (pinned exactly).
  - The study reports PineTS 0.14.0 as current [study: pine_eng §1.17].
  - The other team member's scratch install uses 0.13.1.
  - Results must record the version, because parity fixes change between releases.
- `validate.cjs`: static checks.
- `run_pinets.mjs`: the runtime driver.
- `verify.py`: orchestration and comparison.
- Python references: `final_ref.py` (strategy semantics) and `ind_ref.py` (indicator semantics).
- `.gitignore`: `work/`, `node_modules/`, `package-lock.json`.

### 5.2 Data flow, step by step
1. **Static validation** (`verify.py:48` → `validate.cjs`).
   - For each `.pine` file, calls `validatePineScript(src)`.
   - Counts severity 0 (errors), 1 (warnings) and ≥ 2 (info), and prints each with its line.
   - It does **not** fail the run: the output is printed only.
2. **Data export** (`dump`, `verify.py:30-37`).
   - Takes the NQ 5m pickle for one calendar year.
   - Localises the naive NY timestamps to `America/New_York`, **dropping DST-ambiguous and nonexistent stamps** (`ambiguous='NaT', nonexistent='NaT'`).
   - Converts to UTC epoch ms and writes JSON candles `{open, high, low, close, volume, openTime, closeTime = openTime + 299,999}` (a 5m bar width, hardcoded).
   - Returns the *filtered* frame, so the Python reference runs on exactly the same bars.
3. **Instrumentation** (`verify.py:21-27, 56-60`). It does not modify the script's logic; it **appends debug plots** to the end of the unmodified source:
   - Indicator: `nTrades`, `nWins`, `netPts`, the signal (+1/−1/0), `pdh`, `pdl`, `onHi`, `onLo`, `sslSwept`, `bslSwept`.
   - Strategy: the signal, `strategy.position_size`, `strategy.netprofit`, `strategy.wintrades`.
   - Variant: for the sweep-ON run, it string-replaces the input default `input.bool(false, "Only signal after a liquidity sweep"` with `true`, after asserting the exact text exists.
   - This works because the appended `plot()` calls reference **global** variables declared earlier. It needs one plot per series (Pine's plot-count limit applies) and cannot reach local variables.
4. **Execution** (`run`, `verify.py:40-44` → `run_pinets.mjs`).
   - Node loads the script text and the candles.
   - A custom provider object serves `getMarketData()` (the candles) and `getSymbolInfo()`: a hand-written MNQ `syminfo` with root `MNQ`, ticker `MNQ1!`, `mintick 0.25`, `pointvalue 2`, timezone `America/Chicago`, session `1700-1600`.
   - `new PineTS(provider, 'CME_MINI:MNQ1!', '5').run(src)` executes the whole series.
   - Every plot's per-bar values go to `<name>.out.json` (keys starting with `__` are drawing collections and are ignored).
5. **Comparison** (`verify.py:51-81`), per year 2023/2024/2025 × sweep OFF/ON:
   - Indicator: the per-bar signal vector must **equal** `indicator_ref()`'s, and the final `nTrades`, `nWins` and `netPts` must equal the reference trade list (net within 1e-6).
   - Levels (OFF only): PDH, PDL, ONH and ONL must be `allclose` with `equal_nan`, and the sweep flags exactly equal on every bar.
   - Strategy: the per-bar signal vector must equal `orb_strategy()`'s.
   - Winning trades (Python vs PineTS) and PineTS net after costs are **printed only**.
   - `ok` is the AND of the asserted checks. The script prints `ALL CHECKS PASSED` or `MISMATCH FOUND` and exits 0 or 1.

### 5.3 What it proved in my re-run (T2)
- Signals identical on every bar (indicator and strategy, both filter settings, 3 years).
- Indicator trade, win and net totals identical.
- Liquidity levels and sweep flags identical on every bar.
- Strategy wins within 1 per year (2023: 212 vs 211; 2024: 213 vs 212; 2025 equal).
- The README attributes the strategy differences to PineTS needing price to trade *through* a limit, while TradingView fills on a touch, plus slippage shifting brackets and early closes.

### 5.4 What it does **not** prove (blind spots, with evidence)
1. **TradingView compilation.**
   - PineTS executed the XAUUSD script, which the v6 manual says cannot compile (global reassignment in a function) [ran T6, doc].
   - The validator also missed it, and it misses v6 lazy-evaluation hazards in `and`/`or` operands [ran T3].
2. **Runtime parity on every construct.**
   - On XAUUSD, PineTS 0.10.0 returned VWAP = hlc3 on **every** bar, while the documented TradingView semantics for a `"0000-0000"` session imply a VWAP that **never** resets [ran T6, doc].
   - So one construct, probably the session `time(...)` call with history indexing, behaves differently. The ORB scripts avoid it, which is why their parity holds.
   - Parity is per construct, not per runtime.
3. **Common-mode errors.** Python and Pine were written by the same author from the same reading of the rules. Agreement shows the code matches the spec, not that the spec is right or the data is clean.
4. **Realtime and rollback.** `run()` executes history only. There is no streaming update, intrabar rollback, alert timing or Bar Replay test (pine_eng PENG-7 proposes `stream()`/`update()` tests).
5. **`request.security` and HTF.** The ORB scripts make no HTF requests, so HTF aggregation parity is untested.
6. **Start-point dependence.**
   - Each year runs fresh, so warm-up state such as the first day's PDH is lost at every year boundary.
   - The sweep-ON trade count is 90 per-year in 2025 against 91 in the full-history run [ran T1 vs T2].
   - The harness compares like with like, so it passes, but it never tests start-point invariance (pine_eng PENG-10).
7. **Strategy fills.** Strategy statistics are not asserted. PineTS limit-fill semantics differ from TradingView's touch fills.
8. **Bars dropped in the harness.** Bars in the DST fall-back hour are removed (outside RTH, so harmless for ORB). An engine that uses overnight data would be affected.

### 5.5 How APEX should adapt it (template)

| Layer | Check | Tool | Status in the legacy harness |
|---|---|---|---|
| L0 | Syntax | `pynescript` (`dev-notes/tools/pine_parse.sh`) | Done in project C ("both files parse") |
| L1 | Static semantics | `pinescript-v6-validator` (pinned), **plus custom lints**: (a) `:=`/`+=` on globals inside functions; (b) stateful `ta.*`/`request.*` calls inside `and`/`or` operands, ternaries and `if`; (c) `request.security` must use an offset expression with `lookahead_on`; (d) unknown constants | Validator only. Lints (a)-(c) are missing. Make the run fail on errors. |
| L2 | Reference parity | A Python reference per module (levels, structure events, pool lifecycle, signals) on confirmed bars. Debug plots appended to the unmodified source. Exact per-bar equality of integer and boolean outputs; tolerance for floats. | Pattern proven on ORB |
| L3 | Runtime-parity register | A list of constructs with known PineTS ≠ TradingView behaviour: limit-fill touch vs through; session `time()` history (observed); version-specific fixes. Triage every mismatch against the docs. | Partly, in the README prose |
| L4 | Start-point and slice invariance | Run with different start offsets and slice boundaries. After warm-up, confirmed outputs must match. | Missing (boundary effect observed) |
| L5 | Repaint and realtime | PineTS `stream()`/`update()`: history N vs N−k plus k streamed updates must give identical confirmed outputs. In-platform Bar Replay must be marked "not run" if not done. | Missing |
| L6 | Statistical evaluation | The simulator from §4.14 with next-open fills, stop-first, costs and cost stress. **Geometry-matched baselines** (random direction or mirror level, same geometry). Bootstrap CIs. Pre-registered holdout that is never retuned. Neighbour grid. Multi-instrument runs. Reporting of the trial count. | Partly (no baselines, no CIs; holdout spent) |
| L7 | Reproducibility | Record data source commit and SHA-256, tool versions, settings fingerprint and command lines. Commit every script that produces a reported number. | Partly (rejected-idea scripts and the bootstrap missing) |
| L8 | TradingView itself | Compile, Strategy Tester on the strategy twin, Bar Replay, live alert log | Cannot run offline. Must be reported as **not run**. |

Practical notes for APEX:
- Generate the debug-plot block from a manifest. With many outputs, split them across several runs, because of the plot limit.
- Keep the synthetic `syminfo` per instrument class (tick, point value, session, timezone) so the universal engine is tested on futures, FX, crypto and equities.
- Assert, do not print, every metric that a report quotes.

---

## 6. Cross-project lessons (what the data supported or rejected)

| Lesson | Class, grade | Source |
|---|---|---|
| A win rate is set by target/stop geometry: BE = 1/(1+RR). Report WIN − BE (or realised R̄), never a bare win rate. | E, strong | [ran T4]; [study: trade_mgmt §1.2] |
| Exits (partials, break-even, trailing) cannot create expectancy before costs | A, strong (mathematics) | [study: trade_mgmt §1.4] |
| Costs dominate small targets (PF 1.24 → 1.08 as cost goes from 1.5 to 3.5 pts) | E, strong | [ran T1] |
| Next-bar-open fills and stop-first same-bar resolution are the honest defaults | E, strong | `bt.simulate`; docs (strategies.md: market orders fill on the next bar's open) |
| A spent holdout is no longer evidence. Retuning after the holdout (0.5R → 0.2R) turns it into in-sample data. | A, strong | [ran]; README lines 93-94 |
| ORB direction on recent NQ/MNQ | C, weak | [ran T4]; [study: session_stats §2.10] |
| The sweep-first filter improves in-sample, then fails out of sample (23/18 trades) | C, weak | [ran T1] |
| Sweep fade / reversal | C, moderate (negative) | project C [claim]; [study: skeptic C4] |
| EMA pullback + VWAP, RSI(2) MR, and HTF/VWAP/ADX/volume/gap/OR-size filters on NQ 5m | C, weak (negative) | [claim]: scripts not committed |
| Compression → expansion breakouts | C, moderate (negative) | [study: quant_regime] |
| OR-joining many weak triggers produces forced signals | A (multiple testing), moderate | §2.6; [study: skeptic §0.8] |
| ANDing a state with events in a vote yields dead modes (2-of-3 rare, 3-of-3 never) | E (combinatorics), strong | [ran T5] |
| Averaging correlated oscillators into one composite | A (redundancy principle), moderate as design | Project A lines 210-218; spec §8 |
| Threshold presets (FAST/BALANCED) on one engine | D (design), none (untested) | Project A §2.5 |
| PineTS parity is per construct; it is not a compiler | E (tool behaviour), strong | [ran T2, T6]; [doc] |

---

## 7. Consolidated guidance for APEX signal design (from this lineage)

1. **FAST/BALANCED:**
   - Keep the user's mental model: one evidence engine, two presets.
   - BALANCED requires a higher Directional Bias Score threshold, more *de-correlated* evidence groups, longer persistence (N confirmed bars) and wider spacing between signals.
   - FAST relaxes persistence and spacing.
   - Add STRONG BUY/SELL as a higher threshold plus persistence.
   - Never attach win-rate or probability numbers to a mode (spec §13.3).
2. **Neutral by default.**
   - A signal needs regime and bias agreement plus a tradeability check (expected move against costs, spec §16), not any one trigger.
   - Count correlated features once, per spec §8.
3. **Signals must not depend on trade state** (project A's `canOpen*`). Markers come from the evidence state machine. A separate strategy twin handles position simulation for evaluation.
4. **Reason codes and a "blocked by" readout** (project A's debug table), OFF by default.
5. **Non-repaint:**
   - Gate on `barstate.isconfirmed`.
   - Use `[1]` + `lookahead_on` for HTF.
   - Count bars with bar-index arithmetic, not `barstate.isnew` counters.
   - Compute every `ta.*` unconditionally at global scope, never inside `and`/`or`, ternaries or `if`.
   - Never reassign globals inside functions.
6. **Evaluation** (Phase 6):
   - The legacy simulator and harness, extended per §5.5.
   - Every statistic is shown with its geometric break-even, sample size, date range, cost and a geometry-matched baseline.
   - A holdout that is never retuned.
7. **No instrument hardcoding:** derive tick, point value, session and timezone from `syminfo` and inputs (project C's `syminfo.root` lock and NY constants are the counter-example).

---

## 8. Sources

Opened in this session:
- Legacy files listed in the header, plus their origin commits via `git show`/`git log`. Branch commit messages: `1ea6cfe`, `095139f`, `9e0b0ce`, `99f7390`, `b2741c2`, `0f261a2`.
- Pine v6 docs mirror `mmmy_pine-script-doc-v6`:
  - `language/user-defined-functions.md` (lines 805-840, 1139-1141: globals cannot be modified in functions);
  - `concepts/other-timeframes-and-data.md` (lines 202-262 lookahead; 1502-1530 historical vs realtime, avoiding repainting);
  - `concepts/sessions.md` (lines 39-71: `"0000-0000"` = 7-day 24-hour session);
  - `concepts/repainting.md` (line 255: `barstate.isnew` historical vs realtime);
  - `concepts/strategies.md` (line 1603: `calc_on_every_tick`);
  - `language/execution-model.md` (lines 886-890: local-scope history).
- Mirror `jabez4jc_pinescriptv6`:
  - `migration_guides/to_pine_version_6.md` (lines 777-813: lazy evaluation);
  - `release_notes.md:616`;
  - `language/type_system.md:1291`.
- Public dataset repository (`fetch_data.sh` source), HEAD `0ee4392`. Data files only; no code from it was run.
- npm packages `pinets@0.10.0` and `pinescript-v6-validator@0.4.3` (execution only).

Study reports (verified by their B researchers; cited, not re-derived): `trade_mgmt.final.md` §1.2, §1.4, finding 9; `skeptic.final.md` §0.8, C4; `session_stats.final.md` §1.9, §2.10 (O2, O7, O9); `academic_sr.final.md` S19-S20; `quant_regime.final.md` (NR7 race, R5, R22); `pine_eng.final.md` §1.17, PENG-7, PENG-10; `x1_tv_validation.md` (harness overview).

Unverified items, each marked where used:
- The project C README's rejected-idea results and its 0.5R-era bootstrap (scripts never committed).
- TradingView behaviour of the XAUUSD `"0000-0000"` VWAP (doc-reasoned, not executed on TradingView).
- `barstate.isnew` behaviour in a close-only strategy.

---

## Appendix A · Rebuilding the reproduction (commands I ran)

```bash
SP=/tmp/claude-0/-home-user-m/7ce60006-3639-59b1-8cd3-87355409d58a/scratchpad
L=/home/user/m/apex/legacy/mnq_orb; R=$SP/i2/repro
# data, fetched exactly as fetch_data.sh does, into its own empty directory
mkdir -p $SP/i2/dl && cd $SP/i2/dl
git clone --depth 1 --filter=blob:none --no-checkout https://github.com/s-k-28/nq-es-trader-5k-payout data_src
cd data_src && git checkout HEAD -- data/Dataset_NQ_1min_2022_2025.csv data/NQ_5min.csv data/mnq_2026_1min.csv
# tools, pinned as in the origin package.json
mkdir -p $SP/i2/node && cd $SP/i2/node   # package.json: pinescript-v6-validator 0.4.3, pinets 0.10.0
npm install
python3 -m venv $SP/i2/venv && $SP/i2/venv/bin/pip install numba pandas numpy
# rebuild the original repository layout from the legacy copies
mkdir -p $R/pine $R/research/verify_pinets
cp $L/*.pine $R/pine/
cp $L/{backtest,bt,final_ref,ind_ref,prepare_data}.py $R/research/
cp $L/{verify.py,run_pinets.mjs,validate.cjs} $R/research/verify_pinets/
ln -sfn $SP/i2/dl/data_src $R/research/data_src
ln -sfn $SP/i2/node/node_modules $R/research/verify_pinets/node_modules
cd $R/research
$SP/i2/venv/bin/python -I -c "import sys; sys.path.insert(0,'$R/research'); import prepare_data; prepare_data.main()"
$SP/i2/venv/bin/python -I -c "import sys; sys.path.insert(0,'$R/research'); import backtest; backtest.main()"   # T1, about 18 s
cd verify_pinets && $SP/i2/venv/bin/python -I verify.py                                                          # T2, about 4 min 41 s
```

## Appendix B · My analysis scripts

They are stored at `scratchpad/i2/analysis/orb_baselines.py` and `scratchpad/i2/analysis/buysell_counts.py`. Both call the unmodified legacy code and are run as `python -I <script> $R/research`. The core of `orb_baselines.py`:

```python
tr, sig, sl = orb_strategy(nq)                     # legacy rule, Strategy-Tester semantics
tp = where(sig != 0, maximum(1, floor(sl*0.2/0.25 + 1e-6))*0.25, 0)
fade = simulate(..., -sig, sl, tp, flat, ...)      # same bars and geometry, opposite direction
for _ in range(2000):                              # random direction on the same bars
    s = zeros_like(sig); s[idx] = rng.choice([-1, 1], len(idx)); simulate(..., s, sl, tp, ...)
# break-even win rate: (sum(R) + N*cost) / ((1 + r) * sum(R)); random-walk win rate: 1/(1 + r)
# bootstrap: resample the 729 trade P&Ls 10,000 times -> CI of the mean and of the profit factor
```

Seed: `numpy.random.default_rng(20261127)`. Raw outputs: `scratchpad/i2/baselines_output.txt` and `scratchpad/i2/buysell_output.txt`.
