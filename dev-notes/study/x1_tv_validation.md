# TradingView-native validation and evaluation at scale (lens x1_tv_validation)

Lens key: **TVV**. Proposal ids use the prefix **TVV-**.

- Line numbers refer to `brief/baseline_v2.pine` (identical to `indicators/dol_engine.pine`).
- Doc paths are relative to `scratchpad/docsrc/jabez4jc_pinescriptv6/` (local mirror of the official v6 manual and reference, current to the October 2026 release notes). Every compile- or platform-relevant claim quotes it.
- Sibling reports this builds on (read them for the statistics; this report does not redo them): `skeptic.final.md` (SKEP-x: mirror control, three-way verdict, power/MDE, overlap variance), `calib_ml.final.md` (CAL-x: shadow ledger, baseline suite), `pine_eng.final.md` (PENG-x: telemetry export, PineTS harness, parity, request budget), `trade_mgmt.final.md` (TM-x: race economics, hit-rule asymmetry, costs), `quant_pot.final.md` (QPOT-x).
- New measurements in this report: `study/x1_tvv_tools/` (`protocols.py`, `magnifier.py`, `pooling.py`, `make_synth.py`, `eval_pool.py`; outputs `out_*.txt`). Data: the local CME 1-minute / 5-minute / 1-hour files in `study/amt_data/cme` (ES, NQ, RTY, YM, CL, GC; 1h from 2025-03 to 2026-04, 1m and 5m from 2026-01-20 to 2026-04-15).
- Web access in this session: TradingView pages could not be fetched (proxy). Help-centre facts below come from web-search summaries of those pages and are graded accordingly; everything that matters for compiling comes from the local docs mirror.

---

## 0. Summary (read this first)

1. **The in-script ledger cannot settle the forecasting question on one chart; TradingView can, if we use its strategy machinery the right way.** Per-chart samples give an anytime-valid MDE of 5.5-9.5 pp per 5,000 bars (skeptic §0.7), while the effects worth detecting are 2-5 pp. TradingView offers three ways to reach far more data: Deep Backtesting (strategies only; up to about 2 M bars and 1 M trades per run, Premium and higher), running the same strategy across many symbols, and a forward test on live alerts. All three require the forecast to exist as **strategy trades**, so the core of the harness is a strategy version of the engine.
2. **"Strategy mode" cannot be a toggle in the indicator.** The declaration statement is compile-time and the two script types differ: strategies "cannot create alert triggers using the `alertcondition()` function" (language/declaration_statements.md:356) and "execute strictly once per closed bar" by default (concepts/strategies.md:1591). So the strategy must be a **second file**. The recommended way to keep it identical to the indicator is a **build script that generates the strategy twin from the single indicator source** (swap the declaration, strip the four `alertcondition()` lines, append an evaluation block). A Pine library is the textbook route, but it is the wrong one now: exported functions "cannot include statements, variables, or expressions that depend on `input.*()` calls or on global objects of any reference type" (concepts/libraries.md:361), and almost every engine helper reads both (for example `f_potModel` 1303 reads the inputs `potModel` and `priorM` and the global `var` arrays `sUp`/`sDn`; `f_invalidation` 1343 reads the global `pool`). A library would also break the user's one-file paste-and-go install.
3. **A strategy grades a different event than the ledger unless the fill contract is matched.** Five mappings decide parity:
   - **Hit rule.** The ledger needs a strict trade-through for liquidity targets (`high > edge`, 1436) but a limit order fills "when the market price reaches a limit order's value" (concepts/strategies.md:392). Measured gap (touch minus trade-through, tick grid): **+0.05 to +0.82 pp** of hit rate (ES 5m 0.82, 1h symbols 0.05-0.34). Fix: take-profit at `edge + side·syminfo.mintick` for liquidity targets, or `backtest_fill_limits_assumption = 1` (strategies.md:2009).
   - **Entry reference.** The ledger enters at the selection bar's close (1430). `process_orders_on_close = true` fills a close-time order "immediately, on the same tick" (strategies.md:1816), which matches exactly. With the default delay the fill is the next open: hit outcomes for fixed-price barriers do not change, but R does (mean |ΔR| 0.03-0.06 R on clean CME data, p95 0.09-0.12 R; **0.50 R on GC 1h** because of session and roll gaps).
   - **Touch vs race.** The ledger's hit is "target touched within H", graded even after the stop was touched (`f_step` 1434-1458; the race is tracked separately). A strategy trade closes at its stop, so a bracket with a stop measures the **race**, not the touch. The twin needs two bracket modes, each scored against its own baseline: touch mode (target + time stop) against `pBase`, and race mode (target + stop + time stop) against the driftless race probability. Mixing them makes every picker look 15-25 pp worse than its baseline (measured in `eval_pool.py` before the fix).
   - **Same-bar rule.** On a 15-minute chart (10,799 engine-like trials, 6 CME futures, 1-minute truth) the deciding bar touched both barriers in **1.03%** of trials. Outcome disagreement with the 1-minute truth: TradingView's default emulator **0.19%**, the engine's colour rule **0.14%**, Bar Magnifier (2-minute intrabars) **0.02%**. Effect on WIN|decided ≤ 0.05 pp. The magnifier is harmless but not needed.
   - **Time stop.** `strategy.close(id, comment = "TIME", immediately = true)` (strategies.md:1870) at bar `bar0 + H` reproduces the ledger's `t.bars >= H` expiry (1452).
4. **The decision clock must be a fixed grid, not "whenever flat".** A strategy holds one net position, so the DOL and its mirror (opposite sides) cannot be open together, and overlapping same-symbol trials cannot exist on both sides. The clean protocol is a **non-overlapping grid**: decide every `G = H + 1` bars, trade the role's target with a time stop of H bars, and run each role (DOL, MIRROR, NEAREST, GEO, TREND, RANDOM CANDIDATE) as a separate run on identical bars. Every run then trades at exactly the same timestamps, so outcomes pair one-to-one (a Diebold-Mariano-style paired comparison that cancels the shared price path).
5. **What the grid buys and what it costs (measured).**
   - Paired residual `D = y − y_mirror`: sd ≈ **0.77** per pair, grid design effect ≈ **1.06**. That gives SE **0.80 pp at 10,000 pairs**, an MDE of **2.2 pp** at a fixed look and 3.1 pp anytime, and **0.7 / 1.0 pp at 100,000 pairs**.
   - The grid wastes about H× the records of the every-bar ledger. Per 1,000 bars of history the SE is 11.8-15.1 pp (grid) vs 2.1-3.1 pp (every-bar records with a random side). So the strategy's advantage is **length** (Deep Backtesting) **and pooling**, not efficiency per bar. The in-script ledger stays the efficient instrument on the loaded chart.
   - Pooling correlated symbols helps less than the symbol count suggests. For a trend-side picker the paired residual correlates ES-NQ 0.71 and ES-YM 0.52; the four equity-index futures count as **1.9 effective symbols**, and the six CME futures as **3.1**. Pool across asset classes, and cluster standard errors by calendar week across symbols.
6. **Strategy Tester headline metrics are the wrong statistics for this engine.**
   - "Percent profitable" is not the hit rate, because time-stop exits can be profitable.
   - The default order size of 100% of equity compounds, and currency P&L depends on point value and FX.
   - Sharpe and Sortino use monthly returns with a 2% risk-free rate.
   - The trade list keeps only the last 9,000 trades outside Deep Backtesting (strategies.md:183).
   - The right outputs are **exit-tagged trades with metadata in the order comments** (`comment`, `comment_profit`, `comment_loss`), exported as CSV or XLSX ("Download data as XLSX", strategies.md:67; the CSV "contains data for *all* available columns", :182), then analysed offline.
   - In Deep Backtesting, "trade markers, plots, alerts, and Pine Logs are calculated using only the available chart data" (strategies.md:2419), so **no in-script table can report deep-range statistics**. The export is the only channel.
7. **Several TradingView features do not work as evaluation tools for this engine:**
   - **Pine Screener:** Premium and higher; last 500 bars only; at most 5 `request.*()` calls, where the engine has **6** (923, 924, 925, 939, 981, 982); inputs reset to defaults.
   - **In-script multi-symbol pooling through `request.security`:** a requested UDF's scope may contain only requestable types (other_timeframes_and_data.md:811), and `Zone` carries `box`/`line` fields. Nested requests multiply the engine's 6 calls per symbol against the 40/64 cap (limitations.md:204), and execution time scales with the symbol count.
   - **`calc_on_every_tick`, `calc_on_every_history_tick`:** both re-introduce historical-vs-realtime differences (strategies.md:1597).
   - **Pine Logs as a canonical record:** "Only *personal* scripts can generate Pine Logs" (writing_scripts/debugging.md:95), the pane keeps 10,000 historical logs (:183), and no export is documented.
8. **Forward testing is the only out-of-sample evidence, and TradingView already provides an immutable recorder.** A server-side alert runs "a mirror image of the script and its inputs" from its creation (concepts/alerts.md:23), so `alert()` messages emitted when a realtime trial opens and when it resolves form a timestamped, pre-registered, append-only record. The constraint is at most 15 alerts in 3 minutes (faq/alerts.md:201).
9. **Honest public statistics are possible within the House Rules if they are reproducible and comparative.** The official manual asks strategy authors for realistic capital, commission, slippage and sizing, and "ideally *100 or more*" trades (writing_scripts/publishing.md:135-140). The Script Publishing Rules (web summary) require that any claim about "signal accuracy, or statistical reliability" be substantiated, and say future performance cannot be substantiated. The engine should therefore publish **method, base rate, interval, sample, date range and a settings fingerprint**, never a bare hit rate. This also makes the panel's numbers reproducible by any user.

**Harness in one paragraph.**
- Indicator (unchanged UX, plus hidden evaluation hooks).
- Generated strategy twin: grid decision clock, a role switch, touch and race bracket modes, the ledger-faithful fill contract, and metadata in the order comments.
- Deep Backtesting runs per symbol, role, date split and settings fingerprint, exported as XLSX/CSV.
- Offline pooled analyzer (prototype in `x1_tvv_tools/eval_pool.py`): excess over the random-level baseline, paired DOL-minus-mirror and DOL-minus-nearest with week-clustered SE, three-way verdicts, Holm, split-half stability.
- Forward test from server alerts, analysed with the anytime-valid boundary.

Proposals TVV-1 to TVV-8 (§4) specify it.

---

## 1. Concepts (definitions and parameters)

### 1.1 Triple-barrier trial (the unit of evaluation)
- **Definition.** From a decision bar t with entry price E (here the close), place an upper and a lower horizontal barrier and a vertical barrier at t + H. The label is the first barrier touched (López de Prado 2018, *Advances in Financial Machine Learning* ch. 3).
  - Conventions differ for the vertical barrier: some implementations label it 0, others use the sign of the final return (secondary sources: Hudson & Thames; quantt.co.uk; alm0stsurely 2026).
- **DOL mapping.** Upper/lower = target edge and invalidation (`f_invalidation`, 1343-1365), vertical = `H = min(potH, 450)` (305). The engine's ledger already implements it (`Trial` 375-396, `f_openTrial` 1426, `f_step` 1434, `f_book` 1461) with three outcomes:
  - `status` 1 = target touched within H, regardless of the stop;
  - `status` 3 = expiry;
  - `race` ±1 = which barrier came first.
- **Two distinct events.**
  - (a) **Touch**: P(target touched by t+H), baseline `pBase = f_potBase(d, side)` (1314).
  - (b) **Race**: P(target before stop and by t+H), baseline the driftless finite-horizon race `f_raceH(d, risk, σ, 0, H)` (466).
  - A strategy trade with a stop can only observe (b). A strategy trade without a stop (target + time stop) observes (a).
- **Parameters.** H (bars), the hit rule (touch `>=` for arrays, strict `>` for liquidity, 1436), the stop rule (touch, 1437), gap settlement at the open (1438-1442), and the entry reference (close).

### 1.2 Strategy twin and "strategy mode"
- **Constraint.** A script is an indicator, a strategy or a library by its declaration statement (language/declaration_statements.md:7). Strategies:
  - cannot use `alertcondition()` (declaration_statements.md:356, strategies.md:2348);
  - cannot run on another timeframe (:355);
  - execute once per closed bar unless the Script-execution settings say otherwise (strategies.md:1591);
  - have plots that other scripts cannot read as sources (:357).
  - Indicator plots *can* be read by other scripts' source inputs (:35).
- **Options:**
  1. A **generated twin**: the same source, transformed by a build script. Drawings, tables, `request.*` and `alert()` all work in strategies.
  2. A **library** shared by both.
  3. An **external-source bridge**: the indicator plots signals, and a small strategy reads them with `input.source()`.
- **Edge cases for the twin:**
  - remove `alertcondition()` lines (2091-2094);
  - the live sweep alert and live PoT become bar-close only;
  - drawings and plots are not shown in Deep Backtesting, and large reports can fail with "response is too large" (TradingView help 43000672421, web summary: reduce plots and drawings).

### 1.3 Strategy Tester report and its pitfalls when the strategy is an evaluator
- **What it reports** (strategies.md:56-153): net and gross P&L, max drawdown, profitable trades / closed trades, profit factor, buy-and-hold benchmark, Sharpe/Sortino, the returns distribution, average bars per trade, run-ups/drawdowns, capital efficiency, and the Trades tab with entry/exit, signal (ID or comment), price, size, return, MFE/MAE, cumulative P&L and duration.
  - Download: XLSX (all tabs, :67) and CSV of the trade list (all columns, :182).
  - Help-centre Sharpe: monthly returns, risk-free rate 2% (`risk_free_rate` default 2, reference/strategy.md:370). A community library notes the tester falls back to daily returns when trades span less than two months (web summary).
- **Pitfalls for an evaluator:**
  1. **Net position.** A long and a short cannot coexist. `strategy.entry` in the opposite direction *reverses* the position (reference/strategy.md:1338). So DOL and mirror need separate runs.
  2. **Default sizing.** `default_qty_type` defaults to percent of equity at 100 (reference/strategy.md:354-355), which compounds. Use `strategy.fixed`, qty 1, and compute R from prices.
  3. **"Percent profitable" ≠ hit rate.** Classify exits by comment (TGT / STOP / TIME) instead.
  4. **Currency P&L** depends on `syminfo.pointvalue` and account-currency conversion (`currency` uses "the previous daily value of a corresponding currency pair", reference/strategy.md:357). Use R and hit indicators instead.
  5. **9,000-trade cap** outside Deep Backtesting (strategies.md:2415). Deep Backtesting: 1,000,000 orders (limitations.md:426).
  6. **Deep Backtesting shows only the report** (strategies.md:2419). In-script tables cannot summarise the deep range.
  7. **Non-standard charts** fill at synthetic prices (strategies.md:52; reference/strategy.md:386).
  8. **Margin.** The default `margin_long/short = 100` can reject orders if qty × price > equity (reference/strategy.md:363-364). Set 0 for an evaluator, or use a large `initial_capital`.
  9. **Selection bias and overfitting** across symbols, ranges and settings (strategies.md:2403-2411).
  10. **Publishing a strategy publishes a performance report.** House Rules apply (§1.15).

### 1.4 Deep Backtesting
- **Definition.** A strategy-report mode that computes a strategy over a user-chosen date range from TradingView's full storage instead of the loaded chart. Selecting any non-default "Testing period" activates it (strategies.md:106).
- **Limits** (help centre, web summaries; grade moderate):
  - Premium and higher plans;
  - up to **2,000,000 bars per calculation** (if the period is longer, only the most recent 2 M bars run);
  - up to **1,000,000 trades/orders** (limitations.md:426 confirms 1,000,000 orders).
  - Intraday depth depends on the symbol (third party: ES 1-minute about 5-6 years).
  - Continuous futures have extra restrictions; for second-based timeframes the depth is N×3 months.
  - A separate "Calculation takes too long to execute" limit applies, with an undocumented budget.
- **What changes:** report only; "trade markers, plots, alerts, and Pine Logs are calculated using only the available chart data" (strategies.md:2419); no scroll-to-trade (strategies.md:106, :164).
- **Engine implication.** The ledger and scoring run only on the last `calcBars` bars (1519, 2038), and `last_bar_index` in a deep run is the last bar of the range. Without an "all bars" option the twin would trade only the final 5,000 bars of any deep range.

### 1.5 Bar Magnifier / "Bar detalization"
- **Definition.** "If a strategy enables high historical detail, the broker emulator retrieves open, high, low, and close prices from the bars on a suitable *lower timeframe*" (strategies.md:215).
  - `use_bar_magnifier` sets the default (reference/strategy.md:371). It is available to Premium and Ultimate plans only (strategies.md:213; declaration_statements.md:631).
  - July 2026: the "Bar Magnifier" checkbox became the "Bar detalization" menu (release_notes.md:144).
- **Intrabar timeframe per chart timeframe.** Measured against TradingView exports by an open-source parity engine (PineForge docs, `docs/pages/magnifier.md`), consistent with the help-centre table (partially seen):

  | Chart | 1m | 5m | 10m | 15m | 30m | 1h | 4h | 1D | 3D | 1W+ |
  |---|---|---|---|---|---|---|---|---|---|---|
  | Intrabar | 10s | 30s | 1m | 2m | 5m | 10m | 30m | 1h | 4h | 1D |

  Each intrabar is walked "open, its nearer extreme, its other extreme, its close": the emulator's open-proximity rule, applied per intrabar.
- **Coverage limit.** "Scripts can request a maximum of 200,000 bars from any lower timeframe … the broker emulator uses its default assumptions when filling orders on bars that do not have intrabar data" (strategies.md:309). The plan limits are 100K / 125K / 200K intrabars (limitations.md:263-267).
  - Coverage in chart bars = intrabar limit ÷ intrabars per bar. A 15m chart has 7.5 per bar, so 13.3k (Premium) to 26.7k (Ultimate) bars are magnified. A 1h chart has 6, so 16.7k-33k.
  - A 200k-bar deep run on 15m is therefore at most 13% magnified.

### 1.6 Same-bar convention (intrabar path)
- **Broker emulator default:** "If the opening price of a bar is closer to the high than it is to the low … open → high → low → close" (strategies.md:204-207). Gaps settle at the next open; no gaps inside a bar.
- **Engine `f_step`:** bull bar O-L-H-C, bear bar O-H-L-C (the shortest-path rule, trade_mgmt §1.13), with gaps settled at the open (1438-1442).
- **Accuracy:**
  - ordering of a bar's extremes: colour rule 88.1-88.7% vs emulator 80.6% (pine_eng §2.1, trade_mgmt §1.13);
  - outcome disagreement in engine-like races on a 15m chart, measured here: **colour 0.14%, emulator 0.19%, magnifier 0.02%** of trials vs 1-minute truth (§2.2).

### 1.7 Hit-rule asymmetry and limit-fill mapping
- **Ledger:** liquidity target hit = strict trade-through; array target hit = touch; stop = touch (1436-1437). trade_mgmt §2.4 rates this "present, correct" and costs about 0.6 pp of race, absorbed by `f_raceAdj`.
- **Strategy:**
  - a take-profit limit fills on touch: "When the market price reaches a limit order's value, or crosses it in the favorable direction" (strategies.md:392);
  - stops fill at the stop price or worse (reference/strategy.md:1451 `stop`);
  - `backtest_fill_limits_assumption` (const int) fills a limit "only if the market price exceeds the order's limit level by the specified number of ticks" (reference/strategy.md:353), at the limit price (strategies.md:2053 notice). The UI offers "reaches level" or "one tick beyond" (strategies.md:2009 note).
- **Mapping:**
  - liquidity target: TP at `edge + side·syminfo.mintick`, or global assumption = 1 (payout at the edge, exactly like the ledger, 1456);
  - array target: TP at the edge with assumption 0.
  - Mixed families in one run therefore use the per-trade tick offset.
  - The empirical baseline surface counts excursions with `>=` (1531-1532), a touch, so the residual is biased by the trade-through gap (§2.1). A mirror control cancels it (SKEP-2).

### 1.8 Fill timing: `process_orders_on_close`, `calc_on_every_tick`, history ticks
- **Default:** orders created at a bar's close fill at the next bar's open (strategies.md:343).
- **`process_orders_on_close = true`:** "the broker emulator can fill orders created on a bar's close immediately, on the same tick" (:1816). This is the forecast-faithful setting: the ledger enters at the selection close. The tradeable check uses the default.
- **`calc_on_every_tick`:** "can also cause the strategy to behave *differently* across historical and realtime bars" (:1603). Keep it false.
- **`calc_on_every_history_tick`:** Premium and higher, standard charts only; it raises a runtime error if enabled by default on an incompatible plan (:1729). Not needed, since the engine logic is confirmed-bar.
- **`strategy.close(..., immediately = true)`** fills on the same tick (:1870). It implements the time stop at the H-th bar's close.

### 1.9 Commission, slippage and cost in R
- **Settings:**
  - `commission_type` / `commission_value` (reference/strategy.md:359-360);
  - `slippage` in ticks, applied to market and stop fills only, "to make the fill price less favorable" (reference/strategy.md:358);
  - excessive slippage can fill outside the bar (strategies.md:2007).
- **Cost in R** (trade_mgmt TM-8): `c = (2·commission per side / pointvalue + slippage_ticks·mintick·(entry + stop legs)) / risk`.
  - ES 5m engine stop: median 0.027 R (p90 0.11 R) at $4.50 round turn + 1 tick (trade_mgmt §0.7).
- **Touch statistics are cost-free. Every R statistic must say gross or net.**

### 1.10 `strategy.closedtrades.*` and the trade list
- **Built-ins** (strategies.md:2239; reference/strategy.md):
  - `strategy.closedtrades.entry_price/exit_price/entry_time/exit_time/entry_bar_index/exit_bar_index/profit/commission/max_runup/max_drawdown/size`;
  - `entry_comment` (594), `exit_comment` (808), `entry_id/exit_id`;
  - `strategy.closedtrades.first_index` (71) after trimming.
- **Comments carry metadata into the report and export:**
  - `strategy.entry(..., comment)` "the Strategy Tester and the chart show this text for the order instead of the specified `id`" (reference/strategy.md:1353);
  - `strategy.exit(..., comment_profit, comment_loss)` label TP and SL fills separately (reference/strategy.md:1457-1458).
- **Per-trade R offline:** `R = side·(exit − entry)/risk`, with risk carried in the entry comment.

### 1.11 Non-overlapping grid protocol and pairing
- **Definition.** Decision bars `t ≡ 0 (mod G)` with `G = H + 1`. At each decision bar with an eligible target, the role opens one trade, which closes by H bars later at the latest. No two trades of a run overlap, and every role run trades on the same bars.
- **Why.**
  - It keeps one position at a time, as the net-position constraint requires.
  - It gives identical timestamps across role runs, so each pair (DOL, role) shares the price path (Diebold & Mariano 1995 logic; SKEP-5).
  - Records are almost independent: design effect 1.06 measured (§2.3).
- **Alternative "event" protocol:** trade each new DOL commitment when flat. This is closer to a trader's use, but it is unpaired across roles because trade durations differ. Use it for trader-facing expectancy only.

### 1.12 Pooled multi-symbol evaluation
- **TradingView-native routes:**
  1. Run the same strategy on each symbol of a watchlist. The strategy report recomputes per symbol, and each is exported.
  2. Request several symbols inside one script with `request.security(sym, tf, expr)`. Up to 40 unique calls, 64 on Ultimate (limitations.md:204); library calls count even if duplicated (:221); 127 tuple elements in total (:275).
  3. The Pine Screener (indicators only; §1.13).
- **Statistics.** Symbols that trade the same underlying risk are correlated. Measured: for a trend-side picker the paired residual correlates ES-NQ 0.71, and the equity-index block counts as 1.9 effective of 4 (§2.4). So:
  - cluster by calendar week *across* symbols (one-way; absorbs cross-sectional and within-week serial correlation);
  - use two-way clustering (Cameron, Gelbach & Miller 2011) only when both dimensions have about 20 or more clusters;
  - report effective symbols;
  - diversify asset classes.
- **In-script pooling feasibility.**
  - "`request.security()` can request the results of user-defined functions … whose scopes consist of any types outlined throughout this page's Requestable data section" (other_timeframes_and_data.md:811). That excludes drawing types: the engine's `Zone` has `box bx` and `line ce` (352-363) and `f_ghost` draws.
  - Nested requests inside a requested expression are evaluated in that context (:428-472) and count toward the cap. That means 6 per symbol, so at most 6 symbols on non-Ultimate plans before any other call.
  - Execution time multiplies by N.
  - Verdict: only a reduced, drawing-free "evaluation core" could be pooled in-script. Not recommended for the full engine.

### 1.13 Pine Screener
- **Constraints:**
  - indicators only, with at least one `plot*()` or `alertcondition()` (release_notes.md:123; declaration_statements.md:36);
  - plots become columns (`display.pine_screener`, reference/constants.md:125);
  - index sources up to 4,000 symbols (release_notes.md:123).
  - Help centre (web summary; pine_eng §1.22): Premium and higher, **last 500 bars only**, **≤ 5 `request.*()` calls**, input values ignored (defaults used).
- **Engine:** 6 request calls (923, 924, 925, 939, 981, 982) means it cannot run. Even after PENG-2's merge to 5, 500 bars is below the ledger warm-up (300) plus the empirical-surface gate (`max(150, 20·H)` windows = 600 at H = 30, 1290). Usable at most for current-state columns, never for evaluation.

### 1.14 Sharing the engine core through a Pine library
- **Exportable:** functions, methods, UDTs, enums, `const` variables of fundamental types (concepts/libraries.md:93-101).
- **Rules:**
  - every parameter needs a type, and none can be `const` (:108-109);
  - the body cannot depend on inputs or global reference-type objects (:110, :361);
  - `request.*()` in exported functions needs `dynamic_requests`, and their expression cannot depend on parameters (:477-478);
  - requests inside library functions count toward the importer's limit even if duplicated (limitations.md:221);
  - each call site has its own `var` state (libraries.md:117);
  - published scripts that import a library cannot display its logs (:452);
  - libraries are always open source, with no protected/invite-only option (:787);
  - "Public open-source scripts can import only public libraries" (:813);
  - imports pin a version, "The version number is required" (:842), and every fix needs a republish plus an import bump in every importer.
- **Not exportable:** global `var` state (the pool, registry, ledger arrays), inputs, global drawing objects. Functions may create and return drawings, but the engine's rendering reads global state.
- **Engine helpers by exportability:**

  | Exportable as-is (pure) | Blocked (inputs or global reference state) |
  |---|---|
  | `f_clamp` 400, `f_erfcLog` 408, `f_erfc` 411, `f_phi` 417, `f_expPhi` 421, `f_pot` 434, `f_race` 447, `f_raceH` 466, `f_logit` 484, `f_sigm` 488, `f_wilson` 492 | `f_empPoT` 1284 (`sUp`/`sDn`, `H`, `bStep`); `f_potModel` 1303 (inputs `potModel`, `priorM`); `f_potBase` 1314; `f_invalidation` 1343 (`pool`, input `maxATR`, `exeRL/exeRH`); `f_raceAdj` 1367 (`raceSt`); `f_calMult` 1376 (`stN/stK/stPE`); `f_openTrial`/`f_step`/`f_book` (globals); every scoring method that reads weights or tolerances (inputs) |

### 1.15 House Rules and honest statistics
- **Official manual** (writing_scripts/publishing.md:127-139). For strategies:
  - realistic `initial_capital`, commission, slippage and margin;
  - risk "more than 10% of equity on a single trade is *not* typically considered sustainable";
  - "ideally *100 or more*" trades;
  - explain the defaults; resolve report warnings.
  - Publications that break the rules are hidden (:262).
- **Script Publishing Rules** (support 43000590599; web summary, moderate):
  - "any claim about trading performance, signal accuracy, or statistical reliability must be substantiated";
  - "it is impossible to substantiate claims about your script's future performance".
- **Vendor Requirements** (43000549951): win rate in isolation is "useless without a thorough analysis of other metrics". Strategy publishing rules (43000764681): results must be honest, transparent and realistic.
- **Implication for the indicator:**
  - published text and panel numbers must be comparative (hit vs distance-matched expectation), carry an interval, the sample, the date range and the settings;
  - in-sample and forward must be separated;
  - no "highly probable" language (SKEP-8).

### 1.16 Forward testing on TradingView
- **Server alerts.** When an alert is created, TradingView "saves a mirror image of the script and its inputs, along with the chart's main symbol and timeframe to run the alert on its servers" (concepts/alerts.md:23). "Alerts only trigger in the realtime bar" (:22). The script cannot create alerts itself (:21).
  - `runtime.calculation.mode` returns `"alert"` when running as an alert (reference/runtime.md:7-13), so messages can be tagged.
  - Throttle: "If more than 15 alerts occur within three minutes, the system automatically *halts* further alerts" (faq/alerts.md:201). A runtime error stops alerts (:205).
- **Alert log.** Web sources conflict on whether a native CSV export exists. One says the export uses UTC timestamps; another recommends a webhook to a sheet. Grade weak: verify in the UI.
  - Alerts expire on lower plans (third party: 1 month Basic, 2 months Essential/Plus). Active-alert caps vary by plan.
- **Pine Logs.** Personal scripts only (debugging.md:95). The pasted open-source engine is a personal script, so it can log. 10,000 historical logs, then realtime logs appended (:183, :205). Logs survive rollback (pine_eng §1.15). No documented export.
- **Bar Replay** stepping forward executes the script in realtime mode (pine_eng §1.21). Intraday replay depth depends on the plan (help centre: Essential 6 months of 1m, Premium all time-based data; web summary). It is useful for repaint and parity checks, **not** out-of-sample: the data was available when settings were tuned.
- **The out-of-sample rule:** only trials opened on realtime bars after the settings were frozen are out-of-sample (SKEP-7; Sullivan, Timmermann & White 1999).

### 1.17 Download chart data (CSV telemetry)
- "Download chart data…" saves what the chart shows, including indicator plots as columns (help 43000537255, web summary). Inclusion of `display.data_window`-only plots is unverified (pine_eng §1.15). It is a manual snapshot of the loaded bars.
- Use it as the per-bar telemetry channel for the indicator (PENG-6), complementary to the strategy export.

### 1.18 Offline Pine v6 runtimes (outside TradingView, for completeness)
- **PineTS 0.14.0** (LuxAlgo, AGPL; v6 "experimental"): pine_eng PENG-7.
- [new] **PineForge** (C++17 engine Apache-2.0; v6→C++ codegen under the PineForge Source License 1.2, free for personal and noncommercial use).
  - It grades its output against TradingView's own trade lists: 7,993 probes, 6,961 excellent + 410 strong (2026-11-26 scoreboard), 4.78 M TradingView trades graded.
  - Arrays, UDTs, string-key maps and drawings-as-data are supported. Plots, tables and alerts are parsed and skipped; `request.security_lower_tf` takes numeric arrays only.
- [new] **OpenPineScript** (GPL-3.0; v1-v6 transpiled to JS): conformance "112 columns × 2,474 bars"; Python wrapper on PyPI (0.2.1).
- **Relevance.** Pine compilers now exist that can run a strategy twin offline over decades of local data at C++ speed. None was run here: a package install was refused in this session (permission system). The engine's `map<int,int>` and method-on-UDT use may hit their codegen boundaries. This belongs to PENG-7's scope; noted so a later session with permission can try PineForge or OpenPineScript before PineTS.

### 1.19 Baselines the harness must score against (from the study)
- **Random-level (distance-matched):** `pBase` (1314) for touch; driftless `f_raceH` for race (TM-1 corrected).
- **Mirror:** the same distance on the opposite side, same bar, same rule. It cancels clock, volatility-state and roll miscalibration and the trade-through offset (skeptic §1.22). False "edge" 0.3-0.7% vs 4.5-23% without it (SKEP-2).
- **Nearest pool:** the nearest eligible candidate on either side. The strong selection baseline: gambler's-ruin "nearer first" wins 64.5-70.6% of decided races (skeptic §1.14).
- **Also from SKEP-5 / CAL-3:** GEO (max d·pBase), TREND (nearest on the HTF-bias side), RUNNER-UP, RANDOM CANDIDATE.

---

## 2. Evidence (numbers and sources)

### 2.1 Hit-rule asymmetry (touch vs strict trade-through) on a tick grid [new, `protocols.py`, T1]
Random levels at U(0.5, 4) ATR, random side, on the tick grid, window H = 30.

| Set | n | touch − trade-through (pp of hit rate) |
|---|---|---|
| ES 5m | 16,735 | +0.82 |
| ES 1h | 6,219 | +0.26 |
| NQ 1h | 6,220 | +0.05 |
| RTY 1h | 6,219 | +0.11 |
| YM 1h | 6,219 | +0.29 |
| CL 1h | 4,469 | +0.34 |
| GC 1h | 6,016 | +0.07 |

- The gap is largest where the tick is coarse relative to the range (ES 5m).
- It is the same order as the effects the harness must detect (2-5 pp, skeptic §0.1), so the strategy's take-profit must reproduce the ledger's rule.
- It also explains part of the −0.6 pp race residual in trade_mgmt (B1).

### 2.2 Same-bar double touches on a 15-minute chart: 1-minute truth vs magnifier vs emulator vs colour rule [new, `magnifier.py`]
Design:
- 15m bars built from 1-minute bars; 6 CME futures; every third bar a trial;
- target U(0.5, 3) ATR on a random side, stop U(0.5, 2) ATR on the other, H = 30, both on the tick grid;
- truth = 1-minute bars walked with the colour rule;
- magnifier = 2-minute intrabars (anchored at the 15m open) walked open→nearer→other→close;
- emulator = the 15m bar with the open-proximity rule; colour = engine `f_step`.

| Symbol | n | deciding bar touched both | disagree vs 1m: emulator | colour | magnifier |
|---|---|---|---|---|---|
| ES | 1,849 | 1.03% | 0.32% | 0.16% | 0.00% |
| NQ | 1,849 | 0.76% | 0.11% | 0.05% | 0.00% |
| RTY | 1,847 | 1.68% | 0.38% | 0.49% | 0.11% |
| YM | 1,848 | 1.57% | 0.22% | 0.05% | 0.00% |
| CL | 1,830 | 0.44% | 0.00% | 0.00% | 0.00% |
| GC | 1,576 | 0.63% | 0.13% | 0.06% | 0.00% |
| **Pooled** | **10,799** | **1.03%** | **0.19%** | **0.14%** | **0.02%** |

- Pooled WIN|decided: truth 42.44%, emulator 42.43%, colour 42.47%, magnifier 42.42%. The target-first share of all trials moves by ≤ 0.05 pp.
- **Conclusion:** consistent with skeptic §0.12 (0.6-1.7% double-touch, ≤ 0.3 pp WIN bias) and trade_mgmt §0.8. Intrabar conventions are immaterial for this evaluation.
- The magnifier is near-perfect where it has coverage, but it is not required. The colour rule is marginally better than the emulator default, so the ledger is not the weaker judge.

### 2.3 Overlap, decision clock and power [new, `protocols.py`, T2-T3]
Null picker: random side and distance; paired residual `D = y − y_mirror` (same distance, opposite side, strict trade-through, H = 30). Records opened on every bar vs on a grid every H bars; cluster-robust SE with blocks of 4H, keyed by open bar.

| Set | sd(D) | deff, every-bar | SE per 1k bars, every-bar | deff, grid | SE per 1k bars, grid |
|---|---|---|---|---|---|
| ES 5m | 0.762 | 1.06 | 2.49 pp | 1.00 | 13.3 pp |
| ES 1h | 0.770 | 0.89 | 2.29 pp | 1.22 | 14.2 pp |
| NQ 1h | 0.772 | 1.08 | 2.54 pp | 1.05 | 13.6 pp |
| RTY 1h | 0.766 | 0.92 | 2.33 pp | 0.75 | 11.8 pp |
| YM 1h | 0.765 | 0.75 | 2.09 pp | 0.95 | 13.1 pp |
| CL 1h | 0.789 | 1.56 | 3.12 pp | 1.28 | 15.1 pp |
| GC 1h | 0.796 | 1.32 | 2.90 pp | 1.14 | 14.2 pp |

Pooled power for the paired mirror test on the grid (sd 0.774, deff 1.06; α = 0.05 two-sided, 80% power):

| Grid pairs N | SE | MDE fixed look | MDE anytime (≈ 3.9 SE) |
|---|---|---|---|
| 300 | 4.6 pp | 12.9 pp | 18.1 pp |
| 1,000 | 2.5 pp | 7.1 pp | 9.9 pp |
| 3,000 | 1.45 pp | 4.1 pp | 5.7 pp |
| 10,000 | 0.80 pp | 2.2 pp | 3.1 pp |
| 30,000 | 0.46 pp | 1.3 pp | 1.8 pp |
| 100,000 | 0.25 pp | 0.70 pp | 0.99 pp |

Interpretation:
- **Per bar of history** the grid is about 5× worse in SE (about 28× in variance) than every-bar records, because it discards the overlapping windows. The random side per record keeps the every-bar design effect near 1 here; a real picker that holds one target for many bars has deff 1.4-2.8 (skeptic §2.3).
- **Per study** the grid wins on length. A Deep Backtest of a 15m CME chart over 2 years (about 46k bars) gives about 1,500 grid trades per symbol.
  - 12 symbols across asset classes ≈ 18k pairs, about 9-12k effective → MDE ≈ 2.3-2.6 pp fixed.
  - Compare the per-chart ledger's 5.5-9.5 pp anytime MDE per 5,000 bars (skeptic §0.7).
- Entry at the signal close vs the next open (T4): mean ΔR ≈ 0 (−0.007 to +0.006 R), mean |ΔR| 0.030-0.056 R (p95 0.088-0.121 R) on ES/NQ/RTY/YM/CL; **GC 1h 0.50 R (p95 2.97 R)** from session and roll gaps on the unadjusted continuous contract. Hit outcomes are identical: fixed-price barriers and a window that starts on the next bar either way.

### 2.4 Cross-symbol dependence when pooling [new, `pooling.py`]
Trend-side picker (side = sign of the 50-bar return, distance 1.5 ATR), mirror-paired residual on a common 1h grid (149 common points, H = 30).

|  | ES | NQ | RTY | YM | CL | GC |
|---|---|---|---|---|---|---|
| ES | 1 | 0.71 | 0.21 | 0.52 | 0.05 | 0.15 |
| NQ |  | 1 | 0.12 | 0.36 | 0.07 | 0.09 |
| RTY |  |  | 1 | 0.28 | −0.07 | 0.20 |
| YM |  |  |  | 1 | 0.07 | 0.05 |
| CL |  |  |  |  | 1 | −0.05 |

- Mean off-diagonal 0.18, so **3.1 effective symbols of 6**. Equity-index block mean 0.37, so **1.9 effective of 4**.
- The sample is small (149 points), so treat it as indicative. The direction is unambiguous: pool across asset classes, and cluster by week across symbols.

### 2.5 The analyzer on synthetic exports [new, `make_synth.py`, `eval_pool.py`]
Synthetic grid exports from CME 1h data (6 symbols, about 1,136 grid trades per role, 56 weekly clusters). Roles: DOL stand-in = trend-side level 1.5-3 ATR; MIRROR; NEAREST = nearer of two random levels; RANDSIDE.

| Mode | Role | hit % | exp % | excess pp ± SE | Brier | calib. slope |
|---|---|---|---|---|---|---|
| touch (pb) | DOL stand-in | 53.5 | 54.2 | −0.7 ± 1.9 | 0.244 | 0.84 |
| touch | MIRROR | 62.1 | 54.2 | +7.8 ± 1.7 | 0.236 | 0.98 |
| touch | NEAREST | 66.0 | 65.6 | +0.4 ± 1.3 | 0.202 | 0.94 |
| race (pr) | DOL stand-in | 31.6 | 33.9 | −2.3 ± 1.7 | 0.215 | 0.72 |
| race | NEAREST | 42.1 | 43.8 | −1.7 ± 1.4 | 0.228 | 0.93 |

- Paired DOL − MIRROR (touch): −8.5 pp [−14.8, −2.3], Holm p 0.02, "WORSE". DOL − NEAREST: −1.2 pp [−5.2, +2.9], "INCONCLUSIVE (MDE 5.8 pp)".
- **What it shows:**
  - (a) the driftless closed-form baselines (touch `2Φ(−κd/√H)`; race = `f_raceH` with μ = 0, re-implemented in Python) are near-calibrated for the neutral pickers (NEAREST +0.4 / −1.7 pp);
  - (b) the first version that scored race outcomes against the touch baseline produced spurious −15 to −25 pp excesses, so the bracket mode must carry its own baseline;
  - (c) with about 1,100 pairs the verdict is honestly inconclusive for 2-5 pp effects (MDE 5-6 pp, matching §2.3).
- The stand-in "DOL" here is a toy and says nothing about the engine.

### 2.6 Platform facts (graded)

| Fact | Source | Grade |
|---|---|---|
| Strategy vs indicator capabilities (alertcondition, once per bar, other TF, plots as sources) | declaration_statements.md:35, 355-357; strategies.md:2348 | strong (official docs) |
| Emulator path rule, gap fills, limit fill on reach, `backtest_fill_limits_assumption`, `process_orders_on_close`, `immediately` | strategies.md:204-207, 392, 2009, 2053, 1816, 1870; reference/strategy.md:353 | strong |
| Bar detalization: Premium/Ultimate; 200K/125K/100K intrabar caps; defaults where no intrabars | strategies.md:213-215, 309; limitations.md:263-267 | strong |
| Magnifier intrabar table (1h → 10m, 15m → 2m, …) | PineForge `docs/pages/magnifier.md`, measured vs TradingView exports; help 43000669285 partly seen | moderate |
| Deep Backtesting: Premium+, 2 M bars, 1 M trades; report-only | help 43000666265 / 43000668210 (web summaries); limitations.md:426; strategies.md:2419 | moderate (limits) / strong (report-only) |
| 9,000-trade cap outside Deep | strategies.md:183, 2415; reference/strategy.md:388 | strong |
| XLSX of the whole report; CSV of the trade list with all columns | strategies.md:67, 182 | strong |
| External inputs: up to 10 indicators as sources; work with Deep Backtesting | TradingView blog "more external inputs for scripts" (38014), web summary; faq | moderate |
| Pine Screener: Premium+, 500 bars, ≤ 5 requests, defaults for inputs | help 43000742437 (web summary); release_notes.md:123 | moderate |
| Request caps 40/64; library calls count; 127 tuple elements | limitations.md:204-275 | strong |
| Library export rules | concepts/libraries.md:93-117, 361, 452, 477-478, 787, 813, 842 | strong |
| Server alert = mirror image; realtime only; 15 per 3 min halt | concepts/alerts.md:21-23; faq/alerts.md:201 | strong |
| Pine Logs: personal scripts only; 10,000 historical | debugging.md:95, 183 | strong |
| Alert-log CSV export | conflicting web sources | weak |
| Publishing: realistic properties, ≥ 100 trades, unsubstantiated claims → hidden | publishing.md:127-140, 262; Script Publishing Rules (web) | strong / moderate |
| Offline v6 runtimes with measured TradingView trade-list parity | PineForge README (7,371/7,993 probes excellent or strong); OpenPineScript README | moderate (vendor-reported) |

### 2.7 Statistical method evidence (from siblings, re-used)
- **Mirror-controlled anytime boundary:** false "✓" 0.3-0.7% vs 4.5% (23% busy-hour) one-sample; power on side skill 23% / 71% vs 19% / 44% (skeptic §0.5, 288 real null paths). Strong for the method, moderate for magnitude.
- **Few-cluster bias of cluster-robust variances:** Cameron, Gelbach & Miller (2008, REStat). Two-way clustering: Cameron, Gelbach & Miller (2011, JBES). Strong.
- **Paired forecast comparison:** Diebold & Mariano (1995, JBES). Strong.
- **Multiple testing:** Holm (1979); White (2000) Reality Check; Harvey, Liu & Zhu (2016); the best-of-45-settings E[max z] = 2.2 (skeptic §0.8). Strong.
- **Out-of-sample principle:** Sullivan, Timmermann & White (1999); TradingView's own "Notes on testing strategies" (strategies.md:2385-2411). Strong.

---

## 3. Engine gap analysis (line references in `baseline_v2.pine`)

| # | Concept | Status | Where | What the engine does / what is missing |
|---|---|---|---|---|
| G1 | Triple-barrier trial | **present** | `Trial` 375-396; `f_openTrial` 1426-1431; `f_step` 1434-1458; `f_book` 1461-1500 | Touch outcome (status 1) and race (race ±1) recorded per trial; entry at close; strict trade-through for liquidity (1436); gap settlement (1438-1442). Correct, and the reference the twin must match. |
| G2 | Strategy twin / strategy mode | **missing** | 31 `indicator(...)`; 2091-2094 `alertcondition()` | No strategy version exists. The four `alertcondition()` calls must be removed in a strategy. No build tool. |
| G3 | Deep Backtesting readiness | **missing** | 85 `calcBars` (minval 500, maxval 20000); 1519 `inCalc`; 2038 ledger gate | Scoring, selection and the ledger run only on the last `calcBars` bars before `last_bar_index`. In a deep run the twin would trade only the final ≤ 20k bars. No "all bars" option, no date-range inputs. |
| G4 | Ledger-faithful fill contract | **n/a → missing in twin** | 1436-1442 | The ledger's rules (strict trade-through, entry at close, colour path, gap at open, time stop at H) have no strategy mapping yet: TP + 1 tick, `process_orders_on_close`, `strategy.close(immediately)`. |
| G5 | Touch vs race brackets with matching baselines | **partial** | `pBase` 1430 (touch baseline); `pRace` 1430 from `f_invalidation` 1362-1365 (**with drift** `m = potMu·side`) | The ledger has both outcomes. Its race baseline includes drift (TM-1: should be driftless), and no driftless race baseline is stored. A strategy needs separate touch and race modes. |
| G6 | Same-bar convention | **present (better than the platform default)** | 1438-1442 | Colour rule: 0.14% outcome disagreement vs 1-minute truth, vs 0.19% for the emulator, 0.02% for the magnifier (§2.2). Keep. |
| G7 | Paired decision clock (grid) | **missing** | 2038-2045 (trial opened when the DOL changes or after expiry) | Event-driven, overlapping trials. Correct for the in-script ledger, but not pairable across roles in strategies. |
| G8 | Baseline roles (mirror, nearest, GEO, trend, random candidate) | **missing** | — | Only the analytic/empirical `pBase` exists. SKEP-5 and CAL-3 propose in-script roles; the twin needs the same role pickers to be selectable. |
| G9 | Per-trade metadata export | **partial** | 2443-2447 (5 data-window plots: DOL price, score, PoT, D, ledger hit %) | No per-trial record (PENG-6 proposes one). No order comments (no strategy). |
| G10 | Cost model in R | **missing** | `rOut` 1456-1457 (gross R) | No commission or slippage anywhere (TM-8). The twin can use the platform's commission and slippage. |
| G11 | Pooled multi-symbol evaluation | **missing** | — | Single-chart ledger only. No offline analyzer. No cross-symbol clustering. |
| G12 | Pine Screener compatibility | **not viable** | 923, 924, 925, 939, 981, 982 (6 requests) | Exceeds the 5-request cap. 500 bars < warm-up 300 + surface gate 600 (1290). |
| G13 | Library sharing | **missing (by design)** | 1284-1383, 1426-1500 depend on inputs and global `var` arrays | Only the pure math helpers (400-503) are exportable as-is (§1.14). |
| G14 | Forward-test record | **missing** | alerts 2077-2089 | Alerts announce a new target (bar close) and a live sweep (intrabar). No trial OPEN/RESOLVE message with id, barriers, baselines and outcome; no settings fingerprint; no realtime-only flag (SKEP-7's `fwd` absent from `Trial`). |
| G15 | Pine Logs decision trail | **missing** | no `log.*` call in the file | PENG-6 covers it. Personal scripts only. |
| G16 | Reproducibility fingerprint | **missing** | — | Nothing in the panel or exports identifies the settings and engine version. The accuracy rows cannot be reproduced or audited for multiple testing. |
| G17 | Honest-statistics wording | **wrong in places** | 2390 verdict "✕ NO EDGE"; README "most likely drawing to next" | SKEP-8 / SKEP-2 cover the words. This lens adds the reproducibility stamp and publication rules (§1.15). |
| G18 | Random draws | **n/a** | — | No randomness today. Role "random candidate" needs a start-point-independent generator: `math.random(seed)` gives a "repeatable sequence" only from the same first call (reference/math.md:296), which differs between date ranges, so use a time-keyed hash. |

---

## 4. Proposals (best first; 8)

### TVV-1 (P1, effort M, statistics-ledger) · Strategy twin generated from the single indicator source, with a ledger-faithful fill contract and Deep-Backtesting hooks

**Why.** Every large-scale TradingView route (Deep Backtesting, watchlist runs, report export) needs strategy trades (§0.1-0.2). A generated twin keeps one source of truth and the user's one-file install. The fill contract makes the strategy grade the same event as the ledger (§1.7-1.8).

**Files.**
- `dev-notes/tools/make_eval_strategy.py` (build script, about 80 lines), which writes `indicators/dol_engine_eval.pine`. Never hand-edit the output. CI rule: regenerate and `git diff --exit-code`.
- The transform, all string-level and checked:
  1. Replace the `indicator(...)` declaration (31-32) with:
     ```pine
     strategy("DOL Engine v2 · Evaluator", shorttitle = "DOL Eval", overlay = true, max_bars_back = 500,
       max_boxes_count = 500, max_lines_count = 500, max_labels_count = 500,
       process_orders_on_close = true, pyramiding = 0,
       default_qty_type = strategy.fixed, default_qty_value = 1, initial_capital = 1000000,
       margin_long = 0, margin_short = 0, commission_type = strategy.commission.cash_per_contract,
       commission_value = 0, slippage = 0, calc_on_every_tick = false)
     ```
     - Every parameter name is in the signature (reference/strategy.md:338).
     - `margin_* = 0` means "the strategy does not enforce any limits on position size" (reference/strategy.md:363).
     - `use_bar_magnifier` stays at its default `false`: §2.2 shows it does not matter, and lower plans "cannot use it" (declaration_statements.md:631).
  2. Delete the lines matching `^alertcondition\(` (2091-2094). Strategies "cannot create alert triggers using the `alertcondition()` function" (declaration_statements.md:356). Keep the `alert()` calls: they work in strategies at bar close (alerts.md:165).
  3. Flip render defaults so deep reports stay small (help 43000672421: plots and drawings are not shown in Deep mode, and large reports fail): `showDOL`, `showTable` and `showIFVG` default to `false` in the twin, by literal replacement of their `input.bool(true, …` defaults.
  4. Append the evaluation block (TVV-2) after the DATA WINDOW section.

**Engine hooks** (these go into the indicator itself so both files stay identical apart from the transform):
- **H1 · all-bars mode.** Change `calcBars` to allow 0 = all bars: `minval = 0`, tooltip "0 = all loaded bars (slow; for evaluation)". Then:
  - 1519: `bool inCalc = calcBars == 0 or bar_index >= last_bar_index - calcBars`;
  - 2038: `… and bar_index >= (calcBars == 0 ? 0 : math.max(0, last_bar_index - calcBars)) + warmup`.
  - UX: none unless the user sets 0.
- **H2 · decision record.** After step 19 (2034), and only when `activeLv` is non-na, store per-bar globals:
  - `evSide`, `evEdge = activeLv.nearEdge()`, `evLiq = activeLv.isLiquidity()`;
  - `[evInv, evRR, evPR] = f_invalidation(activeLv)`;
  - `evD = math.max(0.0, activeLv.distance(close))`, `evPB = f_potBase(evD, evSide)`;
  - `evPRace0 = f_raceH(evD, math.abs(close - evInv), nz(potSig), 0.0, H)` (driftless; TM-1);
  - `evGrp = activeLv.grp()`, `evKind = activeLv.kind`, `evSrc = activeLv.src`.
  - Declare them as `var` globals in STATE (1020-1080) so nothing is referenced forward.
  - `f_invalidation` is O(pool), so call it once per bar, and only when `evalOn` or the HUD needs it (the HUD already calls it at 2127).
- **H3 · date window inputs** `evFrom`/`evTo` (`input.time`, group "Evaluation", `display = display.none`). They gate trading only, so splits (in-sample to 2024-12-31, out-of-sample from 2025-01-01) are runs on identical engine state.

**Fill contract (in the twin's block):**

| Ledger rule (line) | Strategy implementation |
|---|---|
| Entry at the selection bar's close (1430) | `process_orders_on_close = true` (strategies.md:1816) |
| Liquidity target: strict trade-through (1436) | `limit = evEdge + evSide * syminfo.mintick` (fills on reach, strategies.md:392); payout one tick better than the ledger's, which is negligible. Alternative: global `backtest_fill_limits_assumption = 1` with `limit = evEdge`. |
| Array target: touch (1436) | `limit = evEdge` |
| Stop on touch, gap at open (1437, 1449-1450) | `stop = evInv`; emulator fills at the stop or the gap open (strategies.md:207) |
| Expiry after H bars, R at close (1452, 1457) | `strategy.close(eid, comment = "TIME", immediately = true)` when `bar_index - evBar >= H` |
| Same-bar order: colour rule (1441) | Emulator rule: 0.05 pp WIN difference (§2.2). Optional Bar detalization High for Premium. |

**Pine v6 notes (compile-relevant):**
- `strategy.exit(id, from_entry, …, limit, stop, …, comment_profit, comment_loss)` (reference/strategy.md:1439). An exit placed before the entry fills "waits and does not create the exit orders until after the entry order executes" (:1436).
- `strategy.close(id, comment, qty, qty_percent, alert_message, immediately, disable_alert)` (:460).
- `strategy.entry(id, direction, qty, limit, stop, oca_name, oca_type, comment, alert_message, disable_alert)` (reference/strategy.md:1341).
- `input.time(timestamp("01 Jan 2000 00:00"), …)` uses the date format shown in strategies.md:181.

**Value.** It unlocks Deep Backtesting (about 2 M bars per run) and per-symbol runs with exact platform fills and exportable trade lists. Per-study MDE falls from 5.5-9.5 pp (one chart, anytime) to about 2-3 pp (12 symbols × 2 years of 15m; §2.3).

**Risk.**
- Execution time on long deep ranges (budget undocumented): run date chunks of ≤ about 100-200k bars, or a higher TF.
- Path dependence: each chunk has its own warm-up, so discard the first `warmup + 20·H` bars of every chunk.
- The generated file doubles maintenance unless the CI diff check is enforced.

**Effort.** M (build script about 80 lines; hooks about 25 lines; contract block in TVV-2).

**Ledger-measurable.** Yes. TVV-7's parity test checks that the twin reproduces the ledger's outcomes.

---

### TVV-2 (P1, effort M, statistics-ledger) · Paired grid decision clock, role switch and touch/race bracket modes, with metadata in order comments

**Why.**
- The net-position constraint forbids holding the DOL and its mirror together (reference/strategy.md:1338). A fixed grid gives identical decision timestamps in every role run, so each pair shares the price path.
- The touch and race outcomes need their own baselines (§2.5).

**Inputs** (group "Evaluation (strategy twin)", all `display = display.none`):
- `evOn` (bool, default true in the twin, false in the indicator; in the indicator the block is inert because `strategy.*` cannot be called there; see "Placement" below);
- `evRole` ∈ {"DOL", "MIRROR", "NEAREST", "GEO", "TREND", "RANDOM CANDIDATE"};
- `evClock` ∈ {"Grid", "Event"};
- `evBracket` ∈ {"Touch (target + time)", "Race (target + stop + time)"};
- `evShownOnly` (bool, default true: trade only when `dolShown`, i.e. what the user sees).

**Placement.** The block is appended **only by the build script** (indicators cannot call `strategy.*`: declaration_statements.md:34). The role pickers and H2's decision record live in the shared source, so SKEP-5 and CAL-3 can reuse them in-script.

**Decision clock.**
- Grid: `G = H + 1`; `bool evDecide = barstate.isconfirmed and bar_index % G == 0 and time >= evFrom and time <= evTo and na(evEid)`.
- Since a trade lives at most H bars, every run is flat at every grid bar, so all role runs trade the same bars.
- Event: `evDecide = barstate.isconfirmed and newDolEvent and na(evEid)` (`newDolEvent` at 2033).

**Role pickers** (pure functions over `pool` in the shared source; each returns `[side, edge, inv, isLiq, d]` or na):
- DOL: H2's record.
- MIRROR: `side = -evSide`, `edge = 2*close - evEdge`, `inv = 2*close - evInv`, `isLiq = evLiq`. Same distance, reflected barriers; a synthetic level with the same hit rule.
- NEAREST: the eligible level (`minDistATR ≤ d/atr ≤ maxATR`, excluding the active one's mirror) with minimum `distance(close)`; `inv` from `f_invalidation(lv)`.
- GEO: the eligible level maximising `d/atr · f_potBase(d, side)` (CAL-8).
- TREND: the nearest eligible level with `side == htfBias`; skip when `htfBias == 0`.
- RANDOM CANDIDATE: the eligible level at index `int(f_u01(time) * n)`, with
  ```pine
  f_u01(int t) =>
      float x = math.sin(t / 1000.0 * 12.9898 + 78.233) * 43758.5453
      x - math.floor(x)
  ```
  This is time-keyed, so the same bar gets the same draw in any date range (unlike `math.random`'s call-order sequence, reference/math.md:296). Not cryptographic.

**Trade block (sketch):**
```pine
var string evEid = na
var int    evBar = na
if evOn and evDecide and not na(rSide) and (not evShownOnly or dolShown)
    string eid  = "E" + str.tostring(bar_index)
    float  tp   = rLiq ? rEdge + rSide * syminfo.mintick : rEdge
    float  risk = math.abs(close - rInv)
    string meta = evRole + "|" + str.tostring(evGrp) + "|" + str.tostring(evKind * 10 + evSrc) + "|" + str.tostring(rSide) + "|" +
      str.tostring(rD / atr, "0.000") + "|" + str.tostring(rPB, "0.0000") + "|" + str.tostring(activePoT, "0.0000") + "|" +
      str.tostring(risk, format.mintick) + "|" + str.tostring(rPR0, "0.0000") + "|" + fpStr
    strategy.entry(eid, rSide == 1 ? strategy.long : strategy.short, qty = 1, comment = meta)
    if evBracket == "Touch (target + time)"
        strategy.exit("X" + eid, eid, limit = tp, comment_profit = "TGT")
    else
        strategy.exit("X" + eid, eid, limit = tp, stop = rInv, comment_profit = "TGT", comment_loss = "STOP")
    evEid := eid
    evBar := bar_index
if not na(evEid) and bar_index - evBar >= H
    strategy.close(evEid, comment = "TIME", immediately = true)
    evEid := na
```
- `rPB` = touch baseline (`f_potBase`). `rPR0` = driftless race baseline (`f_raceH(d, risk, potSig, 0.0, H)`). `fpStr` = TVV-5 fingerprint.
- In touch mode, R is not meaningful; report touch statistics only.
- The grid guarantees `evEid` is na at the next decision bar (G = H + 1).
- The `TIME` close on an already-closed trade has no effect.

**Value.**
- It scores the engine against the three study baselines at scale: random-level (excess over `rPB` / `rPR0`), nearest-pool (paired D) and mirror (paired D).
- The role switch doubles as the A/B harness for every ROADMAP scoring change: run fingerprint A vs B on the same grid.

**Evidence.** Paired comparison and mirror control: strong (Diebold-Mariano; SKEP-2 measurements). Grid power numbers: moderate (§2.3).

**Risk.**
- Six roles × symbols × chunks means many runs. Script them as a checklist (TVV-3) and keep the role set small (DOL, MIRROR, NEAREST by default).
- A "chart TF" vs "decision" mismatch if the user changes H between runs: the fingerprint guards it.

**Effort.** M (about 120 lines: pickers about 60, block about 40, inputs about 10).

---

### TVV-3 (P1, effort M, statistics-ledger) · Offline pooled analyzer and a pre-registered run protocol (the scoring side of the harness)

**Why.**
- Deep Backtesting shows no in-script statistics (strategies.md:2419). The trade export is the only channel.
- Pooling correlated symbols needs week-clustered SEs (§2.4).
- Many symbols × roles × settings need multiple-testing control (skeptic §0.8).

**Tool.** `dev-notes/tools/eval_pool.py` (dev-only, never shipped). A working prototype is in `study/x1_tvv_tools/eval_pool.py`.
- Input: one CSV per (symbol, role, fingerprint, chunk), exported from Strategy report → List of trades → Download.
- `parse_tv_list()` pairs the entry and exit rows by "Trade #" and splits the entry comment `role|grp|kindsrc|side|dATR|pb|pm|risk|pr0|fp`. Verify column names on the first real export: grade weak until then.

**Metrics** (all per role, plus paired against DOL):
1. **Excess over the random-level baseline:** touch `mean(y − pb)`, race `mean(y − pr0)`. SE clustered by ISO week pooled across symbols. Report n, effective symbols, cluster count G (verdict requires G ≥ 20).
2. **Paired DOL − role** on identical (symbol, entry_time): `D = (y − b) − (y_role − b_role)`.
   - Mean, 95% CI, MDE (2.80·SE), Holm-adjusted p across roles.
   - Three-way verdict with a predeclared δ = 2 pp: **BEATS** (lower bound > 0); **WORSE** (upper bound < 0); **NO MATERIAL EDGE** (upper bound < δ); **INCONCLUSIVE (MDE x pp)**. Never "no edge" (Darmanin 2026; SKEP-2).
3. **Calibration of `pb` and of the displayed PoT `pm`:** Brier, log-loss, calibration-in-the-large, logistic slope. QPOT-04 and CAL-6 define the targets.
4. **R statistics (race mode):**
   - gross and net R̄ with week-clustered SE;
   - net uses `c = (2·comm/pointvalue + slip·mintick·2)/risk` from the run's properties (TM-8);
   - drift (beta) shown as the long-only and short-only split (SKEP-4).
5. **Stability:** split-half by date (sign agreement), per calendar year, per asset class.
6. **Exit mix and time-to-target** from durations (Kaplan-Meier = empirical CDF of min(T, H+1); SKEP-1).

**Pre-registered run protocol** (file `dev-notes/eval/PROTOCOL.md`, written before any run):
- **Symbols:** at least 4 asset classes, about 12 symbols. For example ES, NQ, CL, GC, ZN (futures, back-adjusted continuous where available, to avoid roll gaps; calib_ml B: TradingView continuous futures are unadjusted by default), EURUSD, USDJPY, GBPUSD (FX), BTCUSD, ETHUSD (crypto), plus two large-cap stocks.
- **Timeframes:** 15m (Day Trading execution TF) and 1h.
- **Date splits:** in-sample to 2024-12-31; out-of-sample 2025-01-01 to the run date; forward from TVV-4.
- **Roles:** DOL, MIRROR, NEAREST (+ GEO and TREND exploratory, flagged as such).
- **Settings:** defaults only (fingerprint recorded). Any other fingerprint counts as a new hypothesis in the α budget (SKEP-9).
- **Adoption rule for engine changes:** a ROADMAP change ships as default only if its paired D (new − old, same grid) is BEATS on the pooled out-of-sample set, and not WORSE beyond its bound in any asset class.

**Value.** It turns hundreds of thousands of exported bars into one honest scorecard per role, with intervals that account for correlation. It is the measurement backbone for ROADMAP round 2.

**Evidence.** Clustering and Holm: strong (Cameron, Gelbach & Miller 2008/2011; Holm 1979). Power and cross-symbol numbers: moderate (§2.3-2.4). The prototype runs on synthetic exports (§2.5).

**Risk.**
- The export format can change. Keep the parser tolerant and fail loudly.
- Manual export effort: about 12 symbols × 3 roles × 2 TFs × 2-3 chunks ≈ 150-200 downloads. Mitigate by running roles DOL and MIRROR first, and NEAREST only if DOL beats the mirror.

**Effort.** M (analyzer about 250 lines from the prototype; protocol doc).

---

### TVV-4 (P2, effort S, alerts) · Forward-test record: realtime trial OPEN/RESOLVE alerts with a fingerprint, the server alert as the immutable log

**Why.** Only trials opened on realtime bars after the settings were frozen are out-of-sample (SKEP-7). A server alert runs a frozen "mirror image of the script and its inputs" (alerts.md:23) and emits only on realtime bars (:22). That makes it a timestamped, append-only recorder that neither the developer nor the user can retro-edit.

**Spec** (indicator; also works in the twin at bar close):
- In `f_openTrial` (1426): set a new `Trial` field `bool fwd = not barstate.ishistory` (shared with SKEP-7). Give each record a run-independent id: `tid = str.tostring(time) + "-" + str.tostring(lv.kind * 10 + lv.src)`.
- On opening a realtime trial (step 20, 2045): `alert("DOL▸OPEN|" + tid + "|" + syminfo.tickerid + "|" + timeframe.period + "|" + side + "|" + edge + "|" + inv + "|" + dATR + "|" + pBase + "|" + pm + "|H" + H + "|" + fpStr + "|" + runtime.calculation.mode, alert.freq_once_per_bar_close)`.
- In step 2 (1546-1553), when a `fwd` trial is booked: `alert("DOL▸RESOLVE|" + tid + "|" + (status == 1 ? "TGT" : "EXP") + "|race " + race + "|bars " + bars + "|R " + rOut, alert.freq_once_per_bar_close)`.
- Budget: at most one OPEN and a few RESOLVE messages per bar, far under "15 alerts within three minutes" (faq/alerts.md:201) for charts at 1 minute or slower. One `alert()` call per event keeps the "Any alert() function call" condition usable.
- User procedure (README "Forward test"):
  1. Freeze the settings; note the fingerprint shown in the panel tooltip (TVV-5).
  2. Create one alert per symbol on "Any alert() function call", "Once per bar close".
  3. Export the alert log monthly (or use a webhook to the user's own sheet; this is the user's choice, and the user decides which personal endpoint, if any, receives the messages).
  4. Run `eval_pool.py --forward` on the log. Forward data is checked continuously, so it uses the **anytime-valid** mirror boundary (SKEP-2), not a fixed-look test.
- Renew alerts before plan expiry (lower plans: 1-2 months, third-party summary). Recreate after any input change (alerts.md:23); the fingerprint changes visibly.

**Value.** The only evidence immune to tuning on history, collected at no extra cost while the user trades. It also verifies alert/chart parity (PENG-10): the logged target must equal the chart's target for the same bar.

**Evidence.** The out-of-sample principle is strong. Platform mechanics are strong (docs). The alert-log export is weak (conflicting sources).

**Risk.** Small samples (about 1 record per few bars per symbol), so the verdict is mostly "INCONCLUSIVE" for months, which is honest. The alert message is limited to `alert()`'s series string; keep it under a few hundred characters.

**Effort.** S (about 25 lines).

---

### TVV-5 (P2, effort S, statistics-ledger) · Reproducibility stamp and House-Rules-safe statistics presentation

**Why.** Any accuracy number shown or published must be reproducible (same symbol, TF, data window, settings, engine version) and comparative. The Script Publishing Rules require substantiation of "signal accuracy, or statistical reliability" claims, and the manual's strategy rules require realistic properties and 100+ trades (publishing.md:135-140). The fingerprint also feeds SKEP-9's multiple-testing count.

**Spec.**
- `const string ENGINE_VER = "2.x.y"` (bumped by the build).
- **Fingerprint:** Pine has no string hash, so hash the numeric inputs and option indices:
  ```pine
  f_fpMix(float h, float x) => (h * 31.0 + math.round(x * 1000.0)) % 2147483647.0
  float fp = 7.0
  fp := f_fpMix(fp, wProx), fp := f_fpMix(fp, wFresh), …   // every numeric input
  fp := f_fpMix(fp, modeIn == "Swing" ? 1 : modeIn == "Day Trading" ? 2 : modeIn == "Scalping" ? 3 : 4)
  string fpStr = ENGINE_VER + "-" + str.tostring(fp, "0")
  ```
  It is computed once at global scope; all operands are simple, so cost is nil. The comma-separated `:=` list is illustrative: implement it as one line per input.
- **Panel** (Terminal style, ACCURACY header tooltip, 2377): `"<fpStr> · <syminfo.tickerid> <timeframe.period> · bars <first time>→<last time> · n <nA> (n_eff <…>) · hit <x>% vs expected <y>% · 95% [lo, hi] · MDE <m> pp · in-sample (k inputs differ from defaults) · forward n <…>"`. The Clean style shows none of it (SKEP-8).
- **README and publication text template:**
  - method (distance-matched baseline, mirror control);
  - "statistics describe the loaded history of the chart you are viewing and are in-sample";
  - never a bare hit rate, never "highly probable", no future claims;
  - if a pooled study is cited: symbols, TFs, date range, n, effective symbols, intervals, fingerprint, and a link to the protocol file and analyzer in the repository, so anyone can rerun it.
- **If the twin is ever published as a strategy:** realistic `commission_*` and `slippage` defaults for the chart symbol, qty sized ≤ 10% equity risk, a dataset with ≥ 100 trades, and the defaults explained (publishing.md:135-140). Recommendation: keep the twin as a repository tool and do not publish it, so no performance report is attached to the public indicator.

**Value.** Users and moderators can audit every number. Selecting settings after the fact becomes visible.

**Evidence.** Moderate (official publishing docs; Script Publishing Rules via web summary).

**Risk.** Fingerprint collisions are possible but harmless (bookkeeping). Tooltip length.

**Effort.** S (about 30 lines + README text).

---

### TVV-6 (P2, effort S, other) · External-source bridge evaluator (no duplication; fallback when the twin is not wanted)

**Why.**
- Indicator plots can feed other scripts' source inputs (declaration_statements.md:35; inputs.md:458).
- TradingView's blog says external inputs can come from up to ten indicators and work with Deep Backtesting (web summary, moderate).
- A tiny generic strategy can therefore grade the unmodified indicator.

**Spec.**
- **Indicator:** four data-window plots after the existing five, so `{{plot_0..4}}` keep their meaning (PENG-6 rule):
  - `EV signal` = `±1` on the bar a grid decision has an eligible DOL, else 0;
  - `EV target` = the TP price (with the +1-tick rule already applied for liquidity);
  - `EV stop` = `evInv`;
  - `EV meta` = `evPB` (touch baseline).
  - `display = display.data_window` (verify the plots are selectable as sources; fallback `display.all` with a transparent colour). They share H2's record, so no new logic is added.
- **Strategy** `indicators/dol_bridge_eval.pine` (about 100 lines, written once): four `input.source()` calls that the user wires to the four plots, plus the TVV-2 trade block (DOL role only; MIRROR by reflecting around close; NEAREST impossible because the pool is not visible).

**Value.** It evaluates any version of the indicator without rebuilding a twin, and it adds no strategy code to the indicator.

**Limits.**
- Only DOL and MIRROR roles.
- The user must wire four inputs.
- The indicator's `calcBars` window still applies (hook H1 needed).
- Sources must come from indicators, not strategies (blog).
- Grade moderate until a Deep Backtest run confirms the bridge on a real account.

**Effort.** S.

---

### TVV-7 (P3, effort S, robustness) · Ledger↔strategy parity test and an in-twin chart-range sanity table

**Why.** Before trusting deep results, show that the twin grades exactly what the ledger grades on the same bars. This is the acceptance test of TVV-1's fill contract.

**Spec.**
- **Parity test** (manual, once per engine release):
  1. On one chart (for example ES 15m, 20k bars), add the indicator with `accView = Full` and a ledger restricted to grid trials (a debug switch `dbgGridLedger` that opens trials only on `bar_index % G == 0`; about 5 lines at 2038).
  2. Add the twin with role DOL, touch mode, then race mode.
  3. Compare n, the touch hit count (ledger `stK[4]` vs twin TGT exits) and the race wins.
  4. **Acceptance:** outcome agreement ≥ 99.5% of trials. Expected disagreements come only from same-bar double touches (≤ 0.2%, §2.2) and one-tick payout differences.
- **Sanity table in the twin** (`barstate.islast`, chart range only, since Deep mode hides it):
  - one incremental pass over `strategy.closedtrades` from a `var int` cursor (`strategy.closedtrades.first_index` …);
  - counts by `strategy.closedtrades.exit_comment(i)` ∈ {TGT, STOP, TIME};
  - mean baseline parsed from `entry_comment(i)` (`str.split(c, "|")`);
  - rows: `n · TGT x% vs exp y% · STOP z% · TIME w% · R̄ gross`.

**Value.** It catches contract drift (for example a future change to the hit rule in `f_step` that the twin does not follow). It gives Basic-plan users a usable chart-range evaluation without exports.

**Evidence.** Moderate (§2.1-2.2 bound the expected disagreement).

**Effort.** S (about 40 lines).

---

### TVV-8 (P3, effort L, performance) · Library extraction: defer, and if ever done, export only the pure math core

**Why not now.**
- (a) Almost every engine helper reads inputs or global `var` state, which exported functions cannot do (libraries.md:361; §1.14). Extraction means threading `Cfg` and `State` UDTs through about 60 functions: an L-sized refactor with high regression risk on a file that cannot be compiled offline.
- (b) User experience: the indicator would need `import <author>/DOLCore/<n>`. The library must be published publicly ("Public open-source scripts can import only public libraries", :813), pass moderation, and be republished with an import bump in every importer for each fix (:842). That ends the one-file paste-and-go install that suits a non-programmer trader.
- (c) Requests inside library functions count against the importer's limit even if duplicated (limitations.md:221).
- (d) Published importers cannot show the library's logs (:452).

**If a second consumer appears** (for example the bridge, other authors): a `DOLMath` library exporting only the pure helpers `f_erfc`, `f_phi`, `f_expPhi`, `f_pot`, `f_race`, `f_raceH`, `f_wilson`, `f_logit`, `f_sigm`, `f_clamp` (400-503), plus the SKEP-2 boundary `u(V)`. All have typed parameters and no globals, so they export as-is. Keep the stateful engine in the single file.

**Evidence.** Strong for the constraints (docs). The UX cost is weak but obvious.

**Effort.** L if the full core is attempted; S for the math-only library.

---

### Considered and not proposed
- **Pine Screener harness:** 6 requests > 5-request cap; 500 bars < warm-up; inputs forced to defaults (§1.13). At most a current-state screener after PENG-2's merge; it has no evaluation value.
- **In-script multi-symbol pooling via `request.security`:** drawing-type fields in requested scopes, 6 nested requests per symbol, time × N (§1.12). Pool offline instead (TVV-3).
- **Bar Magnifier as a requirement:** immaterial here (0.02% vs 0.14-0.19% outcome disagreement; ≤ 0.05 pp WIN), Premium-only, and partial coverage on deep ranges (§1.5, §2.2). Mention it as optional in the README.
- **`calc_on_every_tick` / `calc_on_every_history_tick` / `calc_on_order_fills`:** they add historical-vs-realtime differences (strategies.md:1597) to a confirmed-bar engine, for no benefit.
- **Pine Logs as the forward record:** personal-scripts only, 10,000 historical cap, no documented export (§1.16). It is PENG-6's debug trail, not the canonical log.
- **Strategy Tester headline metrics (percent profitable, profit factor, Sharpe) as the score:** wrong statistics for a forecast (§1.3). Replaced by TVV-3's metrics.
- **Offline runtimes (PineForge, OpenPineScript):** promising for decade-long local tests with measured TradingView parity, but outside TradingView-native scope and blocked by package-install permission in this session. Hand to PENG-7 as alternatives to PineTS.

### Engine refactors the harness needs, and how they change the user's experience

| Refactor | Lines | User-visible change |
|---|---|---|
| H1 · `calcBars = 0` means all bars | 85, 1519, 2038 | One more value in an existing input (tooltip warns about speed). Nothing else. |
| H2 · per-bar decision record + role pickers | STATE 1020-1080 (new `var`s); after 2034 | None (internal). Also used by SKEP-5/CAL-3 in-script roles. |
| H3 · evaluation date window | INPUTS (new group, `display.none`) | A collapsed "Evaluation" group; inert in the indicator unless the bridge is used. |
| Fingerprint (TVV-5) | global after inputs; panel tooltip 2377 | Fingerprint in the Terminal accuracy tooltip; Clean unchanged. |
| Forward alerts (TVV-4) | 1426, 1546-1553, 2045 | Two new `alert()` messages for realtime trials (only if the user creates an "Any alert() function call" alert). |
| Bridge plots (TVV-6, optional) | after 2447 | Four extra Data Window rows. |
| Generated twin (TVV-1/2) | new file + build script | A second, optional script for people who want to verify the engine. The indicator install stays one paste. |
| Library | — | Not done (TVV-8). |

---

## 5. How this fits the other study reports
- **SKEP-2 / SKEP-3 / SKEP-5 / CAL-3:** the in-script mirror, roles and variance fixes keep the per-chart ledger honest. TVV-2 reuses the same role definitions in the twin, and TVV-3 applies the same three-way verdict at pooled scale. Build one role-picker set (H2) for both.
- **SKEP-7 / TVV-4:** the same `fwd` flag. SKEP-7 shows the forward row in the panel; TVV-4 exports it through server alerts.
- **PENG-6 / TVV-6:** telemetry plots and bridge plots share H2's record; keep plot order stable after the existing five.
- **PENG-7:** offline execution, which can now consider PineForge and OpenPineScript (§1.18).
- **PENG-10:** alert/chart parity, measurable from TVV-4's log.
- **TM-1 / TM-8:** the driftless race baseline and costs in R define the race mode's baseline and the net R in TVV-3.
- **QPOT-04 / CAL-6:** calibration scorecards, computed at scale by TVV-3 for both `pb` and the displayed PoT `pm`.

---

## 6. Sources

**Local official documentation mirror** (`scratchpad/docsrc/jabez4jc_pinescriptv6/`):
- concepts/strategies.md: lines 56-153 (report), 67 (XLSX), 106 and 164 (Deep scroll), 185-196 (Properties), 182-183 (CSV, 9,000 trades), 204-207 (emulator path), 213-215 (bar detail), 309 (200K intrabars), 343 (next-tick fills), 392 (limit fills), 1591-1603 (execution behaviour), 1729-1733 (history ticks), 1816 (orders on close), 1870 (`immediately`), 1947-2053 (slippage, `backtest_fill_limits_assumption`), 2129-2260 (strategy information), 2344-2348 (strategy alerts), 2385-2419 (testing notes, trade limit, Deep note).
- reference/strategy.md: 338-394 (`strategy()` parameters and remarks), 460 (`strategy.close`), 594 / 808 (entry and exit comments), 1330-1353 (`strategy.entry`), 1426-1458 (`strategy.exit`).
- language/declaration_statements.md: 25-36 (indicator), 345-357 (strategy), 627-631 (`use_bar_magnifier`), 639-654 (library).
- concepts/libraries.md: 93-117, 171-175, 361, 410-478, 512-530, 787-842.
- concepts/other_timeframes_and_data.md: 251-472 (dynamic and nested requests), 523, 617-625, 807-811, 903-1024.
- writing_scripts/limitations.md: 23-27, 202-275, 365-426.
- writing_scripts/publishing.md: 127-139, 212-236, 258-286.
- writing_scripts/debugging.md: 95, 183, 205.
- concepts/alerts.md: 21-35, 73-75, 163-205.
- faq/alerts.md: 201-205, 266-312.
- reference/runtime.md: 7-15. reference/math.md: 294-308. reference/syminfo.md: 110-132. reference/constants.md: 125.
- release_notes.md: 117-125 (Pine Screener), 136-148 (July 2026 strategy changes).

**TradingView help centre and blog** (fetched only as web-search summaries; the proxy blocked direct reads):
- How Deep Backtesting works: https://www.tradingview.com/support/solutions/43000666265-how-deep-backtesting-works/
- How much data is available for Deep Backtesting: https://tr.tradingview.com/support/solutions/43000668210/
- Deep Backtesting on continuous futures: https://www.tradingview.com/support/solutions/43000730038-what-restrictions-apply-while-using-the-deep-backtesting-mode-on-continuous-futures/
- "Response is too large" (Deep): https://www.tradingview.com/support/solutions/43000672421-i-see-failed-to-recalculate-study-because-response-is-too-large-error/
- "Calculation takes too long": https://in.tradingview.com/support/solutions/43000579793
- Bar Magnifier backtesting mode: https://br.tradingview.com/support/solutions/43000669285/ ; Bar detalization: https://www.tradingview.com/support/solutions/43000786180-bar-detalization/ ; blog: https://www.tradingview.com/blog/en/accurate-backtesting-with-bar-magnifier-31746
- Sharpe ratio (strategy report): https://www.tradingview.com/support/solutions/43000681694-sharpe-ratio/
- Pine Screener requirements and limitations: https://in.tradingview.com/support/solutions/43000742437 ; key features: https://in.tradingview.com/support/solutions/43000742436
- More external inputs for scripts (10 indicators; Deep Backtesting): https://www.tradingview.com/blog/en/more-external-inputs-for-scripts-38014
- Export chart data: https://www.tradingview.com/support/solutions/43000537255-how-to-export-chart-data/
- Bar Replay data depth: https://www.tradingview.com/support/solutions/43000692816
- Script publishing rules: https://www.tradingview.com/support/solutions/43000590599-script-publishing-rules/ ; Strategy publishing rules: https://www.tradingview.com/support/solutions/43000764681-strategy-publishing-rules/ ; Vendor requirements: https://www.tradingview.com/support/solutions/43000549951-vendor-requirements/
- Active alerts per plan: https://in.tradingview.com/support/solutions/43000690941 ; Watchlist alerts: https://in.tradingview.com/support/solutions/43000739708-watchlist-alerts
- Alert-log export (conflicting): https://blog.pickmytrade.trade/pickmytrade-logs-download-trace-alerts-and-orders/ ; https://supa.is/article/tradingview-alert-log-history-export-csv-workaround-2026

**Offline runtimes** (READMEs read from raw.githubusercontent.com):
- PineForge engine: https://github.com/pineforge-4pass/pineforge-engine (README scoreboard 2026-11-26; `docs/coverage.md`; `docs/pages/magnifier.md`). Codegen licence: https://pypi.org/project/pineforge-codegen/ (PineForge Source License 1.2).
- OpenPineScript: https://github.com/be-thomas/OpenPineScript ; PyPI https://pypi.org/project/openpinescript/ (0.2.1).
- Pinebench (PineTS-based local runner): https://github.com/n0n1m0us/pinebench

**Statistics and labelling** (strong; standard references):
- López de Prado, M. (2018). *Advances in Financial Machine Learning*, ch. 3 (triple-barrier labelling). Secondary: https://hudsonthames.org/does-meta-labeling-add-to-signal-efficacy/ ; https://www.quantt.co.uk/resources/triple-barrier-method
- Diebold, F. & Mariano, R. (1995). Comparing predictive accuracy. *JBES* 13(3).
- Cameron, A. C., Gelbach, J. & Miller, D. (2008). Bootstrap-based improvements for inference with clustered errors. *REStat* 90(3). (2011) Robust inference with multiway clustering. *JBES* 29(2).
- Holm, S. (1979). A simple sequentially rejective multiple test procedure. *Scand. J. Statist.* 6.
- Sullivan, R., Timmermann, A. & White, H. (1999). Data-snooping, technical trading rule performance, and the bootstrap. *J. Finance* 54(5).
- Howard, S., Ramdas, A., McAuliffe, J. & Sekhon, J. (2021). Time-uniform, nonparametric, nonasymptotic confidence sequences. *Ann. Statist.* 49(2) (via skeptic/calib_ml).

**Study files** (this repository's knowledge base): `skeptic.final.md`, `calib_ml.final.md`, `pine_eng.final.md`, `trade_mgmt.final.md`, `quant_pot.final.md`.

**New experiment code and outputs:** `study/x1_tvv_tools/protocols.py` → `out_protocols.txt`; `magnifier.py` → `out_magnifier.txt`; `pooling.py` → `out_pooling.txt`; `make_synth.py` + `eval_pool.py` → `out_eval_pool.txt`.
