# Pine Script v6 engineering study for DOL Engine v2

Lens: **PINE SCRIPT v6 ENGINEERING**. Proposal ids use the prefix **PENG-**.

All line numbers refer to `brief/baseline_v2.pine`, which is identical to `indicators/dol_engine.pine`.

Doc paths are relative to `scratchpad/docsrc/jabez4jc_pinescriptv6/`, the local mirror of the official v6 manual and reference, current to the October 2026 release notes.

## 0. Summary

1. **The core non-repainting design is sound and fully doc-compliant.** Do not touch it:
   - HTF/MTF reads use the `[1]` offset with `lookahead_on` (lines 782, 796, 923–925, 939, 981).
   - The engine runs only when `barstate.isconfirmed` (line 1518).
   - Rendering happens on `barstate.islast` (lines 2111, 2132).
   - Lazy `and`/`or` cannot break any `ta.*` state, because every stateful call is global and unconditional (lines 874–950).
   - v6 dynamic `for` bounds are safe: no loop mutates its own bound.
   - Rollback reverts `var` objects on realtime ticks, so the live sweep (line 1504) is consistent.
   - The global `max_bars_back = 500` plus `max_bars_back(time, 5000)` prevents the up to 8x re-executions caused by buffer restarts.
   - Budgets are comfortable: 6 of 40 unique requests, 52 of 127 tuple elements, 9 of 64 plot counts, and roughly 150 of 500 drawings.
2. **The biggest visible engineering defect is settings hygiene.**
   - 76 of the 104 inputs are `int`/`float`/`string`/`session`/`timeframe`. Their default `display` is `display.all`, so all 76 values print in the status line and the Data Window. The reference legend shows only the script name.
   - The four inline colour rows (lines 230–237) put a title on both inputs. This triggers compiler warning **CW10026** and misaligns the settings tab.
   - `active =` (added July 2025) is never used to grey out irrelevant inputs.
   - This is the same finding as competitors.md COMP-1. PENG-1 merges and extends it.
3. **Runtime is probably within limits on default settings, but it has never been measured and has no safety valve.**
   - Limits: a 500 ms per-bar loop limit, and a total budget of 20 s on Basic and 40 s on other plans (older official docs; current docs defer to the pricing page).
   - Chart history ranges from 5k bars (Basic) to 40k bars (Ultimate).
   - The engine runs its level-tracking pipeline on every historical bar. Only scoring is gated by *Calculation Depth*.
   - PENG-2 adds `calc_bars_count` (an official "Calculated bars" input) and merges the two HTF requests into one tuple (the docs measure this kind of merge at -33% request time). It also defers iFVG drawing creation to the tail, gates Terminal-only per-tick work in Clean style, and sets a Profiler protocol.
4. **Live-display and robustness gaps that make targets *look* wrong:**
   - The `minPoT` show/hide filter is evaluated on live ticks, so the zone can flicker on and off intrabar (PENG-4).
   - The label is deleted and recreated on every tick, which churns objects and can close its hover tooltip (PENG-5).
   - On Heikin Ashi, Renko and other non-standard charts, all chart levels *and* the MTF requests use synthetic prices, and the ledger grades against synthetic highs and lows. The fix is `chart.is_standard` plus `ticker.new(syminfo.prefix, syminfo.ticker, syminfo.session)` (official FAQ pattern) (PENG-3).
5. **Measurement tooling is the main lever for WHERE, WHEN and HOW LIKELY.**
   - Export one data-window plot record per forecast (Download chart data CSV) and add an opt-in `log.info` decision trail (PENG-6).
   - Run an offline v6 runtime (LuxAlgo PineTS 0.14, released 2026-11-13, AGPL) as a smoke-test, repaint-regression and ledger-replay harness (PENG-7).
   - Calibration scoring of the displayed PoT (Brier, reliability) is already specified in calib_ml.md and quant_pot.md. It is not repeated here.

What this study could not do:
- Firecrawl was out of credits.
- WebFetch could not resolve tradingview.com or luxalgo.com from this sandbox.
- `npm install pinets` was denied by the session's permission policy.

So no offline run of the engine was possible. Every compile-relevant claim below is grounded in the local official-doc mirror. Web evidence came through WebSearch summaries and the GitHub CLI.

---

## 1. Concepts (definitions and parameters)

Each concept states the exact rule, its parameters and limits, what it means for the DOL forecast (where, when, how likely, and whether the ledger is honest), and its failure modes.

### 1.1 Non-repainting higher-timeframe reads (`[1]` + `lookahead_on`)
- **Definition.** `request.security(sym, tf, expr[1], lookahead = barmerge.lookahead_on)` returns the last **confirmed** HTF value from the first chart bar of each new HTF period. Behaviour is identical on historical and realtime bars.
  - Docs (concepts/other_timeframes_and_data.md:1398): "The most reliable approach to achieve non-repainting results is to use an `expression` argument that only references past bars (e.g., `close[1]`) while using `barmerge.lookahead_on` as the `lookahead` value."
  - Docs (:202–209): lookahead is acceptable when "the `expression` argument … includes a historical offset (e.g., `close[1]`)", or for the same timeframe, or for intrabar requests.
- **Parameters.** Offset ≥ 1 *inside* the requested expression, so the tuple is shifted inside the function (lines 782 and 796). Never request below the chart timeframe; `f_tfSafe`, line 564, enforces this.
- **DOL role.** The MTF bias, HTF pivots and HTF FVGs feed the draw vector D, the registry and selection. If any of them leaked future data, historical selections and the ledger's hit rate would be inflated. That makes this the precondition for an honest HOW LIKELY.
- **Failure modes:**
  - `lookahead_on` without an offset leaks the future.
  - `lookahead_off` repaints on realtime bars.
  - Requesting a timeframe below the chart's repaints (feed differences, intrabar order).
  - A chart timeframe above the execution timeframe silently mislabels rows; the engine warns about this (line 1017).

### 1.2 Bar states, realtime rollback and `varip`
- **Definition.** `barstate.isconfirmed` is true on all historical bars and on the closing update of a realtime bar (concepts/bar_states.md:91). Before every realtime re-execution, rollback restores the committed state:
  - "for objects of built-in or user-defined types with references assigned to `var` variables, the rollback process reverts any changes to those objects that occur on the open bar" (language/execution_model.md:407);
  - objects created on the open bar and not held in `varip` are deleted (:403);
  - `varip` variables and fields, Pine Logs and alert logs survive rollback (:411–416).
- **DOL role:**
  - WHEN: structural events, selection and ledger outcomes are committed only at bar close, so targets never change intrabar.
  - Live PoT and the sweep alert are deliberately tick-level.
  - Anything that decides *visibility* from live data reintroduces intrabar instability (section 3, PENG-4).
- **Failure modes:**
  - `barstate.isconfirmed` "will not work when used in a `request.security()` call" (bar_states.md:102).
  - `varip` state cannot be reproduced after a reload, which is repainting (execution_model.md:139).

### 1.3 v6 semantic changes that can silently alter results
- **Lazy `and`/`or`** (migration_guides/to_pine_version_6.md:777–830): when the left operand decides the result, the right operand is not evaluated. A `ta.*` call or a history-dependent UDF on the right side then misses bars and corrupts its internal history. Fix: hoist such calls to global variables.
- **Dynamic `for` bounds** (release notes, March 2025; to_pine_version_6.md:980): `to_num` is re-evaluated before every iteration. `for…in` uses the updated size if the collection is resized (language/loops.md:563).
- **Strict `bool`**: a bool is never `na`, and `[]` on a bool returns `false` where no history exists.
- **`timeframe.period` always has a multiplier** ("1D", not "D").
- **No `[]` on UDT fields.**
- **DOL role.** These are compile-clean but behaviour-changing. They are the most likely silent source of a forecast that is "subtly wrong".

### 1.4 Historical buffers and `max_bars_back`
- **Definition:**
  - The buffer is sized from references made in the first **244 bars**. Exceeding it later restarts the whole script with a larger buffer, possibly several times (execution_model.md:715–721).
  - The Profiler example shows 162,560 executions on 20,320 bars, i.e. **8x** (writing_scripts/profiling_and_optimization.md:1560ff).
  - Realtime references beyond the buffer raise RE10143 and are never resized.
  - `max_bars_back(var, num)` accepts `num` ≤ **5000** (reference/core.md:265).
  - The declaration parameter sets a minimum for *all* buffers, and larger buffers cost memory (execution_model.md, "Notice").
- **DOL role.** Anchor scans, the empirical PoT window (`close[H]`, `atr[H]`) and OB/FVG back-scans need deep offsets. If buffers are sized wrongly the result is load-time blow-ups or realtime crashes.

### 1.5 Drawing coordinate limits
- **Rules:**
  - `xloc.bar_index` drawings can sit at most **10,000 bars in the past** and **500 bars in the future** (writing_scripts/limitations.md:371–390).
  - Bar indexes are converted through the `time` buffer; the engine reserves 5000 bars (line 37) and clamps with `f_x` (line 404).
  - `time(timeframe, bars_back = -n)` returns the *expected* timestamp of a bar up to 500 bars ahead (reference/time.md:298). This makes fully time-based drawings (`xloc.bar_time`) feasible.
- **DOL role.** The zone must be "anchored left at the candle that formed it". With the clamp, anchors older than 4999 bars (PWH/PDH on 1-minute charts) start at the wrong candle.

### 1.6 Drawing budgets and update strategy
- **Budgets:** at most 500 lines, 500 boxes and 500 labels (set via `max_*_count`), 100 polylines, and 9 tables, one per position (limitations.md:133–200). The garbage collector deletes the oldest objects.
- **"Reducing drawing updates":** historical drawing changes are never visible, so restrict them to the last bar (profiling_and_optimization.md:1120).
- **"Avoiding redrawing":** setters are cheaper than delete plus `*.new`. In the docs' Profiler example, the `box.new()` line costs about **2x** the combined `box.set_lefttop` and `box.set_rightbottom` calls (:1072–1118).
- **DOL role.** This is a UX concern: label tooltips and flicker on liquid symbols. It also matters for performance when objects churn across history.

### 1.7 Request budget and tuple merging
- **Limits:**
  - 40 unique `request.*()` calls, or 64 on Ultimate; identical calls are reused (limitations.md:204–260).
  - At most **127 tuple elements** across all requests (:273).
  - Up to 100k, 125k or 200k intrabars by plan.
  - `calc_bars_count` (simple int) on a request limits the history it loads and computes (profiling_and_optimization.md:1070).
- **Merging:** several expressions from the same context should be merged into one tuple request. In the docs' example, the run went from **340.8 ms to 228.3 ms** (profiling_and_optimization.md:991–1070).
- **Dynamic requests** (the v6 default) allow requests in local scopes, but "a `request.*()` call's evaluated expression **cannot** depend on" loop variables (other_timeframes_and_data.md:390ff).

### 1.8 Whole-script budget: `calc_bars_count`, execution time and the Profiler
- **`calc_bars_count` in `indicator()`** is a const int: "If specified, the script automatically adds a 'Calculated bars' input to the 'Settings/Inputs' tab. If the value is positive and less than the number of historical bars … the script starts its calculations that number of bars before the most recent bar" (reference/core.md:183).
- **Time limits:**
  - Loops: 500 ms per bar (limitations.md:27).
  - Total: "varies with account types" (limitations.md:23). Older official text gives **20 s Basic / 40 s other plans**; a third-party "Plan Limit Timer" library claims 100 s for Ultimate (unverified).
- **Chart bars by plan:** 5,000 (Basic), 10,000 (Essential, Plus), 20,000 (Premium), 25,000 (Expert), 40,000 (Ultimate) (limitations.md:412).
- **Pine Profiler:** per-line and per-block runtime and execution counts. Profile across configurations (profiling_and_optimization.md:723).
- **Official remedies for "Calculation takes too long":** split the script, limit bars (date filter or `calc_bars_count`), and optimise after profiling (TradingView support 43000579793).
- **DOL role.** The script timing out is the most severe possible user complaint ("it does not run").

### 1.9 Inputs: `display`, `active`, `inline`, `group`, `tooltip`, enums
- **`display`:**
  - "The default is `display.all` for all input types except 'bool' and 'color' inputs, which use `display.none` by default" (concepts/inputs.md:112).
  - `display.all` prints the value next to the script title in the status line *and* in the Data Window.
- **`active`** (input bool, July 2025): when false the input is greyed out and cannot be edited. It may depend on other inputs declared earlier (inputs.md:116; reference/input.md:28).
- **`inline` alignment:** the October 2026 rule aligns inline rows only if "the first `input*()` call … includes a non-empty `title` argument" and the others use `""`. Otherwise compiler warning **CW10026** is raised (errors/CW10026.md).
- **`input.enum()`** (June 2024) gives typed dropdowns.
- **DOL role.** No forecasting role. This is the most visible clutter on the chart.

### 1.10 Alerts
- **`alert(message, freq)`:** series-string message; frequencies `freq_once_per_bar`, `freq_once_per_bar_close` and `freq_all`. It fires only on realtime bars (concepts/alerts.md:53–76).
- **`alertcondition()`:** const message. Dynamic values only through placeholders `{{plot_0}}`…`{{plot_19}}` or `{{plot("title")}}`, wrapped in single quotes (alerts.md:336–372). Each call uses one plot count.
- **Repaint-safe alerts** require bar-close evaluation (alerts.md:387–396).
- **DOL role.** WHEN the trader is told. The engine is already correct here; feature gaps are in competitors.md COMP-2.

### 1.11 Non-standard charts and data types
- **`chart.is_standard`** is a simple bool. It is false on Renko, Kagi, Line break, Point & figure, Range and Heikin Ashi (reference/chart.md:71).
- **Real OHLC on a non-standard chart:** the official FAQ says to "use `request.security` function in combination with `ticker.new`", for example `ticker.new(syminfo.prefix, syminfo.ticker)` (faq/general.md:5–28).
- **`ticker.standard()`** also strips the extended session, dividend adjustment and currency conversion (reference/ticker.md:273). That can misalign prices against the chart, so prefer `ticker.new(prefix, ticker, syminfo.session)`.
- **`syminfo.volumetype`** returns "n/a" when the symbol has no volume (reference/syminfo.md:837).
- **DOL role.** On a Heikin Ashi chart every pivot, FVG, ATR and sweep test uses synthetic candles. WHERE is wrong and the ledger is fiction.

### 1.12 Intrabar path conventions (same-bar double touch)
- **TradingView broker emulator:** "If the opening price of a bar is closer to the high than it is to the low … open → high → low → close", otherwise open → low → high → close. Gaps fill at the next open (concepts/strategies.md:204–207). "Bar detalization: High" uses real intrabars on Premium and Ultimate.
- **DOL role.** WIN≤H, R:R expected value and MAE in the ledger depend on which barrier was touched first when one bar spans both.

### 1.13 Diagnostics: Pine Logs, chart-data export, Pine Screener
- **Pine Logs:** `log.info(formatString, args…)` (reference/log.md:58). Logs survive rollback (execution_model.md:414).
- **Download chart data:** CSV of OHLC plus indicator values (TradingView help 43000537255). Inclusion of data-window-only plots is reported by a third-party guide; verify it.
- **Pine Screener:**
  - It accepts indicators with at least one `plot()` or `alertcondition()`, puts the first 10 plots into columns, and runs one indicator per screen (TradingView help 43000742436).
  - It reportedly evaluates only about 500 bars (third-party). The engine's adaptive parts (empirical PoT needs 600 windows; ledger warm-up 300) would not warm up there.
- **DOL role.** These tools audit WHY a target was chosen and replicate HOW LIKELY offline.

### 1.14 Script-size and scope limits
- **Limits:** 100,256 compiled IL tokens, where unused code is discarded before counting (limitations.md:310). 1,000 variables per scope (:346). The 550-scope limit was removed in February 2025. Compilation requests are capped at 5 MB.
- **DOL role.** The 2,450-line engine is large. Every extra feature adds compile risk, but there is no hard evidence that the engine is near the limit.

### 1.15 Offline execution runtimes
- **LuxAlgo PineTS 0.14.0** (2026-11-13, AGPL-3.0 with a commercial licence option; about 969 GitHub stars):
  - It transpiles native v6 to TypeScript and runs it with Pine time-series semantics.
  - It covers the engine's constructs: `request.security`, `request.security_lower_tf`, `box`/`label`/`table`, `map`, `array.sort_indices`, `percentile_linear_interpolation`, `log.info`, `alertcondition`, `ta.pivothigh`, `timeframe.change`.
  - It supports custom OHLCV arrays and providers with automatic timeframe aggregation.
  - Its changelog lists TradingView-parity fixes (late-first-call `ta.*` history, v6 dynamic `for` bounds, rollback, `once`, negative `bars_back`).
  - The README still marks "Native Pine Script v6" as *experimental*.
- **DOL role.** No TradingView-hosted compiler or runtime is available offline. This is the only way to execute the engine in CI.

---

## 2. Evidence (numbers and sources)

| Fact | Number | Grade | Source |
|---|---|---|---|
| Inputs that print in the legend | 76 of 104 (int, float, string, session, timeframe; no `display` set) | strong (code count plus official default) | baseline_v2.pine 59–237; inputs.md:112; input.md:27 |
| Inline rows that trigger CW10026 | 4 (`c1`–`c4`, lines 230–237) | strong | errors/CW10026.md |
| Unique requests used | 6 of 40 (64 on Ultimate) | strong | lines 923–925, 939, 981–982; limitations.md:204 |
| Tuple elements used | 52 of 127 (12×3 + 5 + 6 + 5) | strong | same; limitations.md:273 |
| Plot counts | 5 plots + 4 alertconditions = 9 of 64 | strong | lines 2090–2093, 2444–2448; limitations.md:33 |
| Loop time limit | 500 ms per bar | strong | limitations.md:27 |
| Total execution budget | 20 s Basic / 40 s others (older official text); Ultimate 100 s (third-party, unverified) | moderate | TradingView limitations page (via search); "Plan Limit Timer" library |
| Chart bars by plan | 5k / 10k / 20k / 25k / 40k | strong | limitations.md:412 |
| Tuple merge speed-up | 340.8 → 228.3 ms (-33%), 9 calls to 1 | moderate (vendor demo) | profiling_and_optimization.md:991–1070 |
| Buffer restart cost | 8x executions (162,560 on 20,320 bars) | moderate (vendor demo) | profiling_and_optimization.md:1560ff |
| Setter vs recreate | `box.new` line about 2x the two setter lines | moderate (vendor demo) | profiling_and_optimization.md:1072–1118 |
| Drawing x-limits | 10,000 bars past (bar_index), 500 bars future; `max_bars_back()` ≤ 5000 | strong | limitations.md:371–390; core.md:265 |
| Intrabar request caps | 100k / 125k / 200k by plan | strong | limitations.md:261 |
| Compiled tokens | 100,256 | strong | limitations.md:310 |
| Look-ahead inflation of backtests | qualitatively large; no rigorous magnitude found (an SSRN paper states material improvement without figures) | weak | SSRN doi 10.2139/ssrn.6508779 (summary); dev.to "backtest that showed 400%" (anecdote) |
| Pine Screener scope | first 10 plots as columns; about 500 bars (third-party) | weak | TradingView help 43000742436; secondary blogs |
| PineTS maturity | v0.14.0, 2026-11-13; native v6 "experimental"; parity changelog | weak to moderate | github.com/LuxAlgo/PineTS (README, CHANGELOG, docs/lang-coverage.md) |

Grading note: for *engineering mechanisms*, the official manual is graded **strong** (it is the specification). Measured *magnitudes* come from the vendor's own Profiler demos and are graded **moderate**. User-perception claims are graded **weak**.

---

## 3. Engine gap analysis (line references)

Status key: present (done well, leave it), partial, missing, wrong.

| # | Concept | Status | Engine lines | What the engine does / what differs |
|---|---|---|---|---|
| G1 | `[1]` + `lookahead_on` MTF | **present** | 782, 796, 923–925, 939, 981 | Tuples shifted inside the requested function; `f_tfSafe` (564) prevents lower-timeframe requests. |
| G2 | Confirmed-bar engine | **present** | 1518 | Structure, pools, scoring, selection, ledger, iFVG and breakers all run under `barstate.isconfirmed`. |
| G3 | Rollback-safe live sweep | **present** | 1504–1509, 2084–2085 | `activeLv` is a `var` reference; its field changes on an open bar are reverted (execution_model.md:407). |
| G4 | Lazy and/or safety | **present** | 874–920, 923–950, 964–975 | Every `ta.*` and stateful UDF (`f_changed*`, `f_sessOpen`, `f_rangeTrack`, `f_sessTrack`) is evaluated globally and unconditionally. |
| G5 | Dynamic `for` bounds | **present** | 1551, 1560, 1593, 1600, 1631, 1648 (descending to 0); 1816, 1954, 2153, 2176 (no mutation) | No loop mutates its own `to_num`. Every `0 to size-1` loop is guarded against size 0 (Pine counts *down* when `to < from`). |
| G6 | Buffers | **present** | 31 (`max_bars_back = 500`), 37 (`time` 5000) | The deepest offsets are `H` and `anchorMax`, both ≤ 450, so the buffer never restarts. Cost: every series carries 500 values (memory only). |
| G7 | Drawing x-clamp | **partial** | 404–405, 37 | Correct for the ≤ 5000 `max_bars_back()` cap. Zones anchored more than 4999 bars back (PWH/PDH on 1m charts) are clamped to the wrong candle. |
| G8 | Rendering only on the last bar | **present** | 2111, 2132, 2295, 2310; `tailBar` 1525, 1641 | Matches "Reducing drawing updates". |
| G9 | Historical drawing churn | **partial** | 1611–1623 | iFVG boxes and lines are created on *every* historical inversion and deleted when more than `ifvgMax` exist. Only the final 8 are ever visible. |
| G10 | Recreate vs setters | **missing** | 2132–2141, 2216–2248 | Every realtime tick deletes and recreates the zone box, 5 glow lines, the tether and the label (Clean: 8 objects; Terminal: 6; +2 with `showInv`). The tooltip-carrying label gets a new id on every tick. |
| G11 | Table updates | **partial** | 2296, 2311 | Updates only on the last bar (good), but `table.clear` runs over the full 4×22 grid and every cell is rebuilt on each tick. |
| G12 | Request merging | **partial** | 923 and 939 | Two separate `request.security` calls on the **same context** (`f_tfSafe(tfH)`): structure (12 values) and HTF FVG (5 values). In Day mode on charts below 1H, 925 (`tfE = "60"`) and 981 (`"60"`) are also the same context. |
| G13 | `calc_bars_count` | **missing** | 31–32, 85 | *Calculation Depth* (85, 1519) gates only scoring, selection and the ledger. Level tracking, the empirical surface, iFVG/OB trackers and the registry run on all bars, up to 40k on Ultimate. There is no "Calculated bars" safety valve. |
| G14 | Clean-mode dead work | **partial** | 2111–2130 | Every realtime tick computes `f_reachD`×4, `ttHit.median()`, the similar-distance scan and `f_invalidation`, which loops the pool and runs two `f_raceH` with up to 400 terms each. Clean style displays none of it unless `showInv` or `showReach` is on. |
| G15 | Input `display` | **wrong** | 59–237 | 76 values print to the status line and Data Window. The reference legend shows only the name. (= competitors COMP-1) |
| G16 | Input `active` | **missing** | 59–237 | Custom TFs, custom colours, LVN, ghost, HUD, iFVG and accuracy settings stay editable when irrelevant. |
| G17 | Inline alignment | **wrong** (warning) | 230–237 | Two titles per inline row raise CW10026 four times and misalign the colour rows. |
| G18 | Enums | **missing** (minor) | 60, 123, 166, 177, 181, 190, 216, 229 | String options compared as strings (`potModel == "Empirical"` in `f_potModel` on every bar). Typo-prone but cheap. |
| G19 | `behind_chart` | **present** (default) | 31 | Default `true` keeps zones and iFVGs behind candles. The label sits in the future area (`xR`), so nothing hides it. |
| G20 | Alerts | **partial** | 2079–2093 | `alert()` plus `alertcondition()` with correct frequencies. `alertcondition` messages have no `{{plot("DOL Price")}}`, and there are no per-event toggles. (= competitors COMP-2) |
| G21 | Live visibility filter | **partial** | 2066–2068, 2202, 2185 | `dolShown` is computed from the live `activePoT`. With `minPoT > 0` the zone and label (and secondary targets) appear and disappear tick by tick as PoT crosses the threshold. The announcement (2071) is correctly gated on confirmation. |
| G22 | Non-standard charts | **missing** | 874–920 (chart OHLC), 923–982 (`syminfo.tickerid`) | No `chart.is_standard` check. On Heikin Ashi every chart-level computation uses synthetic OHLC, the MTF requests inherit the HA context, and the ledger grades against synthetic highs and lows. |
| G23 | Volume-less symbols | **partial** | 979, 997, 1007, 1417–1424, 1945–1947 | `nz(volume)` keeps the profile at zero, so `vpMean = 0` and `f_pathVol` falls back to 1.0 (neutral). Safe, but the 1H requests still run, and LVN silently shows nothing. `syminfo.volumetype` is not checked. |
| G24 | Same-bar double touch | **partial** (differs) | 1436–1452 | Rule used: bull bar means O-L-H-C, bear bar means O-H-L-C. TradingView's emulator orders by whether the open is nearer the high or the low. They disagree on hammer and shooting-star bars. Ambiguous races are not counted or flagged. |
| G25 | Pine Logs / export | **missing** | 2436–2448 | Five data-window plots (price, score, PoT, D, hit %). No per-forecast record (side, distance, PoT at assertion, pBase) and no decision log. |
| G26 | Reload-dependent window | **partial** | 1519, 2038 | `inCalc` and the ledger window start at `last_bar_index - calcBars`. Every reload shifts the start, so the hysteresis path, `f_calMult` and the panel's hit % change slightly between reloads even without new bars. This is inherent and documented under "Dataset variations" (repainting.md:268–297). |
| G27 | Chart TF above execution TF guard | **present** | 564–565, 1017, 2305–2307, 2431–2433 | `f_tfSafe` plus a panel warning. |
| G28 | Drawing and plot budgets | **present** | 32 | 500/500/500 limits. Peak use is about 50 iFVG objects + 200 ghosts + about 20 render objects + LVN. |
| G29 | Offline execution / CI | **missing** (process) | n/a | Only a syntax parser (pynescript) is available. No runtime test of na-handling, array bounds or repainting. |
| G30 | varip | **n/a** | none | Correctly not used. All committed logic must stay rollback-safe. |

---

## 4. Proposals (spec-level, best first; maximum 10)

Each proposal lists the algorithm, Pine v6 implementation, value, evidence, risk, effort, and what the ledger can measure. Compile-relevant claims cite the local manual.

### PENG-1 (P1, S, visual-ux) · Settings hygiene: `display`, `active`, inline alignment
This is the same as competitors.md COMP-1; merge the two. The additions here are the CW10026 fix and the exact dependency map.

1. **Status line.** Add `display = display.none` as a literal to all 76 `input.int`, `input.float`, `input.string`, `input.session` and `input.timeframe` calls (lines 60–226). Doc: reference/input.md:27 ("The default depends on the type of the value passed to `defval`: `display.none` for `bool` and `color` values, `display.all` for everything else"). This also removes them from the Data Window, leaving only the five DOL plots.
2. **`active` map.** `active` is an input bool; every dependency below is declared earlier, so there are no forward-reference problems.

   | Inputs | `active =` |
   |---|---|
   | `cHTF`, `cSTF`, `cEXE` (62–64) | `modeIn == "Custom"` |
   | `sessAs`, `sessLo`, `sessNA` (107–109) | `useSess` |
   | `obLook`, `obQMin` (118–119) | `useOB or useBRK` |
   | `fvgQMin` (115) | `useFVG` |
   | `fvgMin` | leave active: it also drives the iFVG tracker and HTF FVGs |
   | `ifvgMaxIn`, `ifvgMax` (196–198) | `showIFVG` |
   | `trackAge` | `showIFVG or useBRK` |
   | `lvnThr`, `lvnN` (206–207) | `showLVN` |
   | `lvnHours`, `lvnRows` | `showLVN or usePathVP`: they also feed the path cost |
   | `ghostMax` (211) | `showGhost` |
   | `hudSize` (177) | `uiStyle == "Terminal"` |
   | `accView` (190) | `uiStyle == "Terminal"` (the accuracy panel is Terminal-only) |
   | `warmup` (192) | `accView != "Off" or useCal` |
   | `priorM` (186) | `potModel == "Empirical"` |
   | `tablePosIn` (216) | `showTable` |
   | `uAbove` … `uText` (230–237) | `theme == "Custom"` |

3. **CW10026.** Retitle each inline pair so only the first input carries a title, for example `input.color(#00E5FF, "Custom · Buy / Sell-side", group = G_COL, inline = "c1")` followed by `input.color(#FF2BD6, "", group = G_COL, inline = "c1")`. Repeat for c2, c3 and c4 with tooltips naming both fields (errors/CW10026.md).
4. **Optional.** Give `modeIn` `display = display.status_line` behind a constant switch. Default: none, to match the reference.

- **Value.** Removes the single largest "cluttered or ugly" difference from the reference (about 75 tokens of numbers in the legend), clears four compiler warnings, and lets the settings dialog explain itself.
- **Evidence.** Mechanism strong (official reference). Benefit weak (screenshot and clutter complaints).
- **Risk.** None functionally. Users can no longer see settings in the legend.
- **Effort.** S. Mechanical; the syntax checker covers it.
- **Ledger.** Not measurable.

### PENG-2 (P1, M, performance) · Runtime budget pack: `calc_bars_count`, merged HTF request, lazy iFVG drawing, Clean-mode gating, Profiler protocol
1. **Safety valve.** Change the declaration (line 31) to `indicator("DOL Engine v2 · Draw on Liquidity", ..., calc_bars_count = 20000)`.
   - Per reference/core.md:183 this is a const int and adds a "Calculated bars" input under the Calculation section.
   - It changes nothing for Basic through Premium (5k–20k bars). On Expert and Ultimate it halves the work while keeping 20k bars, which is more than *Calculation Depth*'s maximum (line 85) and ample for the empirical surface: about 20,000 windows, against `nMin = max(150, 20·H) = 600`.
   - Document in the tooltip of *Calculation Depth*: "Calculated bars (Settings → Inputs → Calculation) limits the whole script; Calculation Depth limits scoring and the ledger inside it."
2. **One HTF request instead of two** (G12). After `f_htfFvg` (about line 797), add:
   ```
   f_htfPack(int len, float minAtr, float dm) =>
       [b, ib, rh, rl, pvh, pvl, pht, plt, hv, lv, prh, prl] = f_structure(len)
       [fd, ft, fb, fq, fT] = f_htfFvg(minAtr, dm)
       [b, ib, rh, rl, pvh, pvl, pht, plt, hv, lv, prh, prl, fd, ft, fb, fq, fT]
   ```
   Then replace lines 923 and 939 with one call: `[htfBiasR, …, htfProtL, hfDir, hfTop, hfBot, hfQ, hfT] = request.security(syminfo.tickerid, f_tfSafe(tfH), f_htfPack(biasLen, fvgMin, dispMult), lookahead = barmerge.lookahead_on)`.
   - The tuple total stays at 52 of 127, and unique requests drop from 6 to 5.
   - Both inner functions already return `[1]`-shifted values, so non-repainting is unchanged.
   - Doc: "condense them into a single `request.*()` call that uses a tuple … improve the runtime … reduce the script's memory usage and compiled size" (profiling_and_optimization.md:997).
3. **Lazy iFVG drawing** (G9). In step 5 (lines 1611–1619), create the box and CE line only when `tailBar`. Otherwise push the `Zone` with `bx = na` and `ce = na`. In the RENDERING block (line 2145), loop `for z in ifvgs` and, when `na(z.bx) and showIFVG`, create the same box and line with the stored coordinates (`z.createdBar` and `z.bornBar` are already on the object). The existing upkeep (1637–1640) already handles `na` drawings, since `box.delete(na)` is a no-op. This removes about 2 object creations and deletions per historical inversion; only the at most `ifvgMax` survivors are ever drawn.
4. **Clean-mode gating** (G14). Add `bool needInv = showInv or not clean` and `bool needReach = showReach or not clean`. Wrap lines 2112–2115 in `if needReach` and lines 2116–2130 in `if needInv`. The Clean-style label uses none of them.
5. **Profiler protocol** (process; profiling_and_optimization.md:17–760):

   | Case | Chart | Settings |
   |---|---|---|
   | A | BTCUSD 1m, 20k bars | Scalping |
   | B | ES1! 5m | Day |
   | C | EURUSD 1h | Day; no volume |
   | D | SPY 4h | Swing; lower-TF path active |

   - Run each case in Clean and in Terminal-Full, with `calcBars` at 5000 and at 20000.
   - Record total ms and the five heaviest lines.
   - Acceptance: under 10 s on case A (50% of the 20 s Basic budget), and under 5 ms per realtime tick.
   - If step 3 (the pool loop), step 11 (registry merge) or `f_profile` dominate, the next levers are:
     - run the registry merge only when `regNew` or every 10 bars;
     - cache `f_pathVol` per level per profile rebuild.

- **Value.** Prevents the worst possible complaint ("does not load or times out") and gives a measured performance baseline.
- **Evidence.** Mechanisms strong (docs). Magnitudes moderate (-33% on the merged request, 2x on setters, from the docs' demos). The engine-specific total gain is unknown until profiled.
- **Risk.** Low.
  - The merged request must keep tuple order exactly.
  - `calc_bars_count` changes the first bar, so early-history state differs; that is acceptable, since dataset starting points already vary (repainting.md:268).
  - Regression check: on the same chart, the ledger's n, hit % and edge before and after the merge must be identical.
- **Effort.** M.
- **Ledger.** Must be unchanged (regression test). Time-to-load is measured with the Profiler.

### PENG-3 (P2, S, robustness) · Non-standard-chart and data guard
1. **Detection.** After line 309, add `bool stdChart = chart.is_standard` (simple bool, reference/chart.md:71).
2. **Real-price requests.** Add `string tkr = stdChart ? syminfo.tickerid : ticker.new(syminfo.prefix, syminfo.ticker, syminfo.session)` (simple string; reference/ticker.md:167; official FAQ pattern, faq/general.md:18–25). Use `tkr` instead of `syminfo.tickerid` in all five requests (lines 923–925, 939, 981–982). The bias table, HTF/STF pools and HTF FVGs then come from real prices even on Heikin Ashi. Do not use `ticker.standard()`, which also drops the extended session and dividend adjustment (ticker.md:273) and can shift prices against the chart.
3. **Warn and stop grading.** Show a warning row in both styles, mirroring `tfWarn` at lines 2305–2307 and 2431–2433: "⚠ NON-STANDARD CHART | levels use synthetic candles". Add `bool ledgerOK = stdChart` and AND it into the trial-opening condition (line 2038). The Terminal ledger then shows "LEDGER OFF · use candles", because hits graded against Heikin Ashi highs and lows are not real.
4. **Volume guard.** Set `needVP := (showLVN or usePathVP) and syminfo.volumetype != "n/a"` (syminfo.md:837), and add an LVN tooltip: "needs volume data".
5. **Optional (M–L).** Drive the whole engine from real OHLC on time-based non-standard charts (Heikin Ashi) with one same-timeframe request, `[rO, rH, rL, rC] = request.security(tkr, timeframe.period, [open, high, low, close])`. This is invasive: every `open/high/low/close` reference and the `ta.*` inputs would need replacing. The default recommendation is to warn instead. Renko, Range and other non-time-based charts cannot be aligned at all, so they get the warning only.

- **Value.** Prevents silently wrong targets and fictitious accuracy numbers on Heikin Ashi charts, which retail users favour. It also fixes the MTF bias table on those charts.
- **Evidence.** Mechanism strong (official FAQ and reference). Prevalence of Heikin Ashi use among this audience unknown (weak).
- **Risk.**
  - `ticker.new` without an `adjustment` argument may differ from the chart's dividend adjustment on stocks. Since it is applied only on non-standard charts, the exposure is small; document it.
  - The extended-session nuance is handled by `syminfo.session`.
- **Effort.** S (steps 1–4).
- **Ledger.** It stops recording invalid trials. The "LEDGER OFF" state is observable.

### PENG-4 (P2, S, visual-ux) · Confirmed-bar visibility with hysteresis for the PoT filter
- **Problem** (G21). `dolShown = activePoT*100 >= minPoT` (line 2068) is live. When PoT hovers near `minPoT`, the zone, glow, tether and label vanish and reappear between ticks. This reads as "the target jumps around". The same happens for secondary targets (line 2185).
- **Spec:**
  - Add `var bool showC = false` and `var int showId = -1` (STATE section).
  - After `activePoT` (line 2067), on `barstate.isconfirmed`:
    ```
    float pp = nz(activePoT) * 100.0
    if na(activeLv)
        showC := false
    else if activeLv.id != showId
        showC  := pp >= minPoT
        showId := activeLv.id
    else
        showC := showC ? pp >= minPoT - 2.0 : pp >= minPoT
    ```
    The 2.0 pp is a const band; it could be exposed as an input with `active = minPoT > 0`.
  - Rendering (2202) and the Terminal "FILTERED" cell (2349) use `showC`. The label *text* still shows the live PoT, the deliberate behaviour from the reference.
  - `annNow` (2071) switches to `showC`, which is already confirmed.
  - Secondary targets: apply the same filter using their bar-close PoT cached at selection.
- **Value.** Stable display. The target and its visibility change only at bar close, matching the engine's confirmed-bar contract.
- **Evidence.** Mechanism strong (rollback and realtime docs, execution_model.md:375–407). User perception weak.
- **Risk.** A target whose PoT drops below the filter intrabar stays visible until the close. That is intended.
- **Effort.** S.
- **Ledger.** Not affected, because the ledger grades committed targets regardless of display. Optionally count "filtered bars" to report how often the filter hides the DOL.

### PENG-5 (P2, M, visual-ux) · Persistent render objects updated with setters
- **Problem** (G10, G11).
  - Every realtime tick deletes and recreates 6–10 drawings and clears the whole table.
  - The label with the score-breakdown tooltip gets a new object every tick, so the tooltip can close while the user hovers on liquid symbols. This is weak evidence (an inference from rollback semantics plus practitioner advice to use `label.set_*`).
  - The docs measure setters at about half the cost of `box.new` (profiling_and_optimization.md:1072–1118).
- **Spec:**
  - Before the RENDERING block, declare a render kit once:
    - `var box rZone = box.new(na, na, na, na, border_style = line.style_dashed)`;
    - `var array<line> rGlow = array.new<line>()`, filled on `barstate.isfirst` with 5 `line.new(na, na, na, na)`;
    - `var line rTeth = line.new(na, na, na, na, style = line.style_dashed)`;
    - `var label rLab = label.new(na, na, "", style = label.style_label_left)`.
  - On `barstate.islast`:
    - if `showDOL and not na(activeLv) and showC`, call `box.set_lefttop` / `box.set_rightbottom` / `box.set_border_color` / `box.set_bgcolor`, `line.set_xy1` / `line.set_xy2` / `line.set_color` / `line.set_width` for each glow layer, and `label.set_xy` / `label.set_text` / `label.set_textcolor` / `label.set_tooltip` / `label.set_size`;
    - otherwise hide them with `box.set_lefttop(rZone, na, na)`, or by setting a fully transparent colour if `na` coordinates are not accepted (verify once in the editor).
  - Per-style geometry differs (Clean has 5 glow layers, Terminal 3). Unused layers are set transparent.
  - Keep the `dB`/`dLn`/`dLb` pools only for variable-count objects (pool lines, secondary targets, LVN).
  - Table: instead of `table.clear(dash, 0, 0, 3, 21)` on every tick, track `var int lastRows`, write every row with `table.cell` (which overwrites), and clear only the rows from `row` to `lastRows - 1` when the count shrinks.
  - All setters used exist in reference/label.md, box.md, line.md and table.md (`label.set_tooltip`, `box.set_lefttop`, `table.cell_set_text`, and others).
- **Value.** A stable hover tooltip, less flicker, and lower per-tick CPU.
- **Evidence.** Moderate for cost (vendor demo). Weak for tooltip persistence.
- **Risk.** Moderate. Stale-object bugs when switching style or when a target disappears; there must be one code path that hides everything. Rollback reverts setter changes on open bars (execution_model.md:407), which is consistent.
- **Effort.** M.
- **Ledger.** Not measurable.

### PENG-6 (P2, M, statistics-ledger) · Forecast telemetry: per-trial export record and decision log
This is complementary to calib_ml CAL-x and quant_pot QPOT-04, which add in-script Brier and reliability scores. This proposal makes every forecast auditable offline.
1. **Inputs** (new group "Diagnostics", all `display = display.none`): `dbgExport` (false) and `dbgLog` (false).
2. **Export record.** On the bar where `f_openTrial` runs (line 2045), set per-bar variables and plot them after the existing five plots, so `{{plot_0..4}}` keep their meaning:
   - `xId` (Trial `lvId`), `xSide` (±1), `xEdge` (target edge price), `xInv` (invalidation), `xD0` (distance in ATR), `xPoT` (model PoT at assertion, i.e. `f_potModel` for the active level), `xBase` (`pBase`), `xGrp` (family), `xScore`;
   - all are `na` on other bars and when `dbgExport` is off;
   - each uses `plot(..., display = display.data_window)`. This is 9 more plots (total 18 of 64).
   - Outcomes are not exported: hit within H bars, first touch and MAE are recomputed offline from the CSV's OHLC, because the horizon `H` and the edge price are known. That avoids multiple trials resolving on one bar.
   - Path: Download chart data (TradingView help 43000537255; data-window-only columns per secondary sources, so verify once).
3. **Decision log.** When `dbgLog and inCalc`, on each confirmed change of `activeId` (line 2030):
   ```
   log.info("{0} DOL {1}→{2} {3} score {4,number,0.0} chall {5} side {6} D {7,number,0.00} why {8}", str.format_time(time), prevId, pickId, f_shortName(...), activeLv.score, challN, dirSide, drawD, reason)
   ```
   - `reason` is one of `sweep`, `eject`, `invalid`, `lead2`, `counter`, `none`.
   - Also log sweeps and ejections (step 3) and ledger bookings (step 2), with `y` and the bar count.
   - Doc: log.md:58. Logs persist through rollback (execution_model.md:414).
   - Cap the volume with an `inCalc` guard and, optionally, a log only in the last N bars.
- **Value.**
  - Answers "why did the target jump?" with evidence.
  - Lets later agents run offline reliability diagrams, Brier decomposition and per-session or per-family breakdowns on many symbols without TradingView, directly on the forecast the user saw.
  - Lets the in-script ledger be cross-checked.
- **Evidence.** CSV export of indicator values: moderate (official help). Data-window plot inclusion: weak (verify). Logs: strong (docs).
- **Risk.** Low. Hidden plots are `na` unless enabled. Keep plot order stable for alert placeholders.
- **Effort.** M.
- **Ledger.** This is the ledger, made exportable.

### PENG-7 (P2, M, robustness) · Offline execution harness (PineTS) for smoke tests, repaint regression and ledger replay
- **Tool.** LuxAlgo PineTS 0.14.0 (github.com/LuxAlgo/PineTS; AGPL-3.0, or a commercial licence). Use it only as a developer tool, never shipped with the indicator.
- **Data.** A custom provider extending `BaseProvider` (docs/data-providers.md "Custom Providers"):
  - Synthetic 1-minute bars (GBM with a session volatility profile and weekends) for deterministic tests.
  - Real CSVs for replay.
  - Higher timeframes ("5", "15", "60", "240", "D", "W") come from automatic aggregation.
- **Test 1 · Smoke.** Run every Trading Mode, both styles and `accView = Full` with toggles on, over 20k bars. Pass when there are no runtime errors (array index, na arithmetic, buffer) and the DOL plots are non-na on most bars after warm-up.
- **Test 2 · Repaint regression.** Run `run()` on N bars, then on N − k bars followed by `k` streamed updates (`stream()` / `update()` API). For every confirmed bar, `DOL Price`, `DOL Score`, the target id (exported per PENG-6) and the ledger plots must be identical.
- **Test 3 · Ledger replay.** Collect hit %, edge z and the race win % across 20–50 symbols and timeframes. This gives the strongest possible evidence for the other studies' proposals (A/B by toggling inputs).
- **Test 4 · Performance proxy.** Wall time per 10k bars, to compare commits.
- **Status in this study.** `npm install` was **denied** by the session's permission policy, so nothing was executed. Running it requires the user's permission.
- **Value.** The only way to catch runtime bugs and repainting regressions before the user does, and to A/B forecasting changes offline.
- **Evidence.** Weak to moderate. PineTS is actively maintained with a TradingView-parity changelog, but native v6 is still labelled experimental, so parity is not guaranteed and its failures need triage.
- **Risk.** False alarms from runtime differences. AGPL obligations apply only if PineTS is redistributed.
- **Effort.** M.
- **Ledger.** Enables offline, multi-symbol measurement of the ledger itself.

### PENG-8 (P3, M, robustness) · Time-based anchoring (`xloc.bar_time`) for exact far anchors
- **Spec:**
  - Add `int anchorT` to `Level`, `Ext` and `Zone`.
  - Set it at creation:
    - chart pivots: `time[bar_index - aBH]` (the offset is ≤ `pivLen + 2`);
    - MTF pivots: `htfPvHT` and `stfPvHT` directly (exact);
    - PD/PW and session levels: record `hiT := time` and `loT := time` inside `f_rangeTrack` and `f_sessTrack` (lines 807–863);
    - OB, FVG and breakers: `time[obI]` and similar.
  - Draw every zone, glow, ghost and iFVG with `xloc = xloc.bar_time`:
    - left `x = anchorT`;
    - right `x = time(timeframe.period, bars_back = -extBars)` (expected future bar time, valid from -1 to -500; reference/time.md:298);
    - tether from `time` to the right edge.
  - This removes `f_x` and the need for `max_bars_back(time, 5000)` for drawings. Keep the bar-index logic for scoring.
- **Value.** Zones are exactly "anchored left at the candle that formed it", even when it printed more than 5000 bars ago (1m charts: one week is 10,080 bars at 24/7, or about 6,900 for futures).
- **Evidence.** Strong (docs: the 10,000-bar `xloc.bar_index` limit, the ≤ 5000 `max_bars_back()` cap, `time()` with negative `bars_back`).
- **Risk.** Moderate. Every drawing call must pass `xloc`, and mixed-xloc bugs are easy to introduce. Future times on session gaps are handled by `time()`'s expected-bar computation.
- **Effort.** M.
- **Ledger.** Not measurable (visual accuracy).

### PENG-9 (P3, S, statistics-ledger) · Same-bar double-touch convention and ambiguity counter
- **Spec:**
  - In `f_step` (lines 1436–1452), replace the bull/bear rule with TradingView's emulator rule (concepts/strategies.md:204–205):
    ```
    bool hiFirst = math.abs(high - open) < math.abs(open - low)
    advFirst := not tgtOpn and (stpOpn or (t.side == 1 ? not hiFirst : hiFirst))
    ```
    For a long target, the high is the target side, so "high first" means the target is first.
  - Add `raceSt[7]`, a count of races decided by the heuristic (`hit and stp` on the same bar with neither barrier gapped through at the open), and show "AMBIG k%" in the Full view's RACE row.
  - Optional (M): resolve ambiguous bars exactly with `request.security_lower_tf(tkr, tfLow, [high, low], ignore_invalid_timeframe = true)` read inside `if hit and stp`. Dynamic requests allow local scope, but the dataset is still requested, so the load cost is paid on every chart. Use `tfLow = timeframe.from_seconds(math.max(60, timeframe.in_seconds() / 10))`.
- **Value.** WIN≤H, R:R expected value and MAE become consistent with what Strategy Tester users see, and users learn how much of the race statistic rests on an assumption.
- **Evidence.** The convention is strong as a platform standard. Its accuracy versus the current rule: none (unmeasured).
- **Risk.** Low.
- **Effort.** S (M with the exact resolution).
- **Ledger.** The AMBIG share is directly observable. The change in race win % before and after is measurable.

### Endorsed from other studies (engineering-verified, not repeated as separate proposals)
- **competitors.md COMP-2 (alerts).**
  - Per-event toggles, approach, abandoned and reached alerts, and JSON `alert()` payloads.
  - `alertcondition` messages with `'{{plot("DOL Price")}}'` and `'{{plot("DOL PoT %")}}'` in single quotes (alerts.md:362–372).
  - Engineering notes:
    - keep the five existing plots first so `{{plot_0..4}}` stay stable;
    - each new `alertcondition` uses one plot count;
    - `freq_once_per_bar` triggers at most once per realtime bar (alerts.md:69).
- **calib_ml.md and quant_pot.md (Brier and reliability of the displayed PoT).** They need a `pShow` field on `Trial`, which PENG-6's `xPoT` export mirrors.

### Considered and not proposed
- **`input.enum()` for the eight string dropdowns.** Typo-safety and integer compares; the value to traders is negligible. Do it as part of the PENG-1 edit only if convenient (enum declarations must precede their inputs).
- **Pine Screener outputs.** The screener reportedly computes about 500 bars, so the empirical PoT and ledger would not warm up. Only analytic outputs would be meaningful.
- **`behind_chart = false`.** The default `true` already keeps zones behind candles, and the label sits in the empty future area.
- **`varip` live-touch latches.** Not needed; they would break reload parity.
- **Lowering the global `max_bars_back = 500`.** Saves memory only, and risks restarts. Keep it.
- **`once` (Aug 2026), UDT `sort_field` (Apr 2026), `text_formatting` / integer text sizes (v6).** Available, but no forecasting or UX gain was identified. An integer text size such as `size = 11` could fine-tune the Clean label to the reference.

---

## 5. Compile-safety notes for implementers (doc-grounded)
- `display` is `const plot_display`: write the literal `display.none` in each call; do not store it in a variable. `active` accepts `input bool` expressions (reference/input.md:27–28).
- `calc_bars_count` is a **const int** in `indicator()` and a **simple int** in `request.*()` (core.md:183; language/type_system.md:230–242).
- `chart.is_standard` is a simple bool. `ticker.new(prefix, ticker, session)` returns a simple string when its arguments are simple, so it is valid for `request.security`'s symbol (ticker.md:167; chart.md:71).
- `time(timeframe, bars_back = -n)` accepts -1 to -500 (time.md:298).
- `log.info(formatString, args…)` accepts series int, float, bool and string arguments (log.md:58).
- `max_bars_back(var, num)`: `num` ≤ 5000 (core.md:265).
- Tuple elements across all requests ≤ 127. Unique requests ≤ 40 (limitations.md:204, 273).
- Lazy `and`/`or`: never put `ta.*` or history-dependent UDF calls on the right-hand side of a condition. Hoist them (to_pine_version_6.md:777).
- Loops: in v6 `to_num` is re-evaluated every iteration. Guard `0 to size - 1` loops against size 0 (Pine counts down when `to < from`).

---

## 6. Sources

Official (local mirror: `scratchpad/docsrc/jabez4jc_pinescriptv6/`, mirrored from tradingview.com/pine-script-docs):
- Limitations: https://www.tradingview.com/pine-script-docs/writing/limitations/ (writing_scripts/limitations.md)
- Profiling and optimization: https://www.tradingview.com/pine-script-docs/writing/profiling-and-optimization/ (writing_scripts/profiling_and_optimization.md)
- Other timeframes and data: https://www.tradingview.com/pine-script-docs/concepts/other-timeframes-and-data/ (concepts/other_timeframes_and_data.md)
- Execution model: https://www.tradingview.com/pine-script-docs/language/execution-model/ (language/execution_model.md)
- Inputs: https://www.tradingview.com/pine-script-docs/concepts/inputs/ (concepts/inputs.md; reference/input.md)
- Release notes: https://www.tradingview.com/pine-script-docs/release-notes/ (release_notes.md: Oct 2026 input alignment, Jul 2025 `active`, Mar 2025 dynamic `for`, Feb 2025 scope limit removed, Nov 2024 v6, Oct 2024 `behind_chart`, May 2024 `calc_bars_count` and Profiler, Mar 2024 `time()` `bars_back`)
- Migration to v6: https://www.tradingview.com/pine-script-docs/migration-guides/to-pine-version-6/ (migration_guides/to_pine_version_6.md)
- Alerts: https://www.tradingview.com/pine-script-docs/concepts/alerts/ (concepts/alerts.md)
- Bar states: concepts/bar_states.md. Repainting: concepts/repainting.md
- FAQ, real OHLC on Heikin Ashi: https://www.tradingview.com/pine-script-docs/faq/general/ (faq/general.md)
- CW10026 warning: errors/CW10026.md
- Strategies, broker emulator: concepts/strategies.md
- Reference: core.md (`indicator`, `max_bars_back`), chart.md, ticker.md, time.md, syminfo.md, log.md, label.md, box.md, line.md, table.md, array.md

TradingView help and support (via WebSearch summaries; direct fetch blocked):
- "I see 'Calculation takes too long to execute' error": https://in.tradingview.com/support/solutions/43000579793
- "How to export chart data": https://www.tradingview.com/support/solutions/43000537255-how-to-export-chart-data/
- "Pine Screener: key features and requirements": https://in.tradingview.com/support/solutions/43000742436
- "Plan Limit Timer" library (third-party plan time limits): https://www.tradingview.com/script/lX5FPZPe-Plan-Limit-Timer/
- "Tooltips added to Pine labels" (label setters): https://www.tradingview.com/blog/en/tooltips-added-to-pine-labels-19036

Third-party:
- LuxAlgo PineTS (README, CHANGELOG 0.14.0, docs/lang-coverage.md, docs/data-providers.md, docs/api-coverage/): https://github.com/LuxAlgo/PineTS
- Pineify, chart data export workflow: https://pineify.app/tradingview/workflows/export-chart-data
- LuxAlgo blog, "5 causes of slow Pine scripts" (search summary only): https://www.luxalgo.com/blog/5-causes-of-slow-pine-scripts-on-tradingview/
- Look-ahead bias anecdote: https://dev.to/guardlabs_team/the-backtest-that-showed-400-how-look-ahead-bias-lies-5f13
- SSRN, decision-time information boundaries (no magnitudes available): doi 10.2139/ssrn.6508779

Sibling studies cross-referenced: `study/competitors.md` (COMP-1, COMP-2), `study/calib_ml.md`, `study/quant_pot.md`.
