# Pine Script v6 engineering study for DOL Engine v2: combined final report (researcher A + researcher B)

Lens: **PINE SCRIPT v6 ENGINEERING**. Proposal ids use the prefix **PENG-**.

- Line numbers refer to `brief/baseline_v2.pine`, which is byte-identical to `indicators/dol_engine.pine` (checked with `diff`).
- Doc paths are relative to `scratchpad/docsrc/jabez4jc_pinescriptv6/`, the local mirror of the official v6 manual and reference. It is current to the October 2026 release notes.
- Markers:
  - **[A✓]**: A's claim, re-checked by B against the doc or the code and confirmed;
  - **[B-corr]**: B corrected or downgraded A;
  - **[B-new]**: added by B.
- Cross-references: overhaul round 1 findings (`dev-notes/runs/overhaul-r1-findings.md` and `overhaul-r1-journal.jsonl`), `study/competitors.final.md` (COMP-x), `study/calib_ml.final.md`, `study/quant_pot.final.md`.

---

## 0. Summary

1. **The non-repainting core is sound. Do not touch it.** [A✓]
   - Every MTF read is `[1]`-shifted inside the requested function and uses `lookahead_on`: lines 782, 796, 923–925, 939, 981.
   - The engine block is gated on `barstate.isconfirmed` (1518). Rendering runs on `barstate.islast` (2111, 2132).
   - B re-checked two v6 semantics against the code:
     - lazy `and`/`or`: a grep finds no `ta.*` or stateful UDF on the right-hand side of a condition;
     - dynamic `for` bounds: B inspected all 40+ loops; none mutates its own `to_num`, and every `0..size-1` loop is guarded.
   - [B-new] B measured why this matters. On 6 CME futures (1-hour bars, about 1 year, about 33k signals), a daily direction read that leaks the current day lifts a 1-ATR/10-bar first-touch win rate from **49.6% (no edge) to 59.5%**. That is a +10 pp illusory edge, exactly the kind the ledger's EDGE z-score would report as real (§2.2).
2. **Settings hygiene is still the most visible engineering defect (PENG-1, P1).**
   - 76 of the 104 inputs (23 int, 31 float, 9 string, 10 session, 3 timeframe) print in the status line and the Data Window, because their default `display` is `display.all`.
   - The overhaul already carries `display.none` and `active=` patches (TE1, VIS-statusline-inputs, ux-statusline-inputs).
   - What remains:
     - the four colour inline rows (230–237) raise compiler warning **CW10026** four times;
     - [B-corr] three entries of A's `active` map are wrong (`obQMin`, `priorM`, `trackAge`), and so is COMP-1's "four LVN inputs".
3. **[B-new] Reload and alert parity is an unaddressed engineering risk (PENG-10).**
   - The official manual says an alert runs a **mirror image of the script and its inputs on TradingView's servers** (concepts/alerts.md:23).
   - TradingView support says the alert's bar count **only grows after launch**, so its results can diverge from the chart's for scripts that depend on their history.
   - The engine's learned state has unbounded memory:
     - `f_calMult` reads the cumulative `stN/stK/stPE` (1376–1382);
     - `f_raceAdj` reads the cumulative `raceSt` (1367–1371);
     - the ledger starts at `last_bar_index − calcBars` (2038).
   - So a reloaded chart, the running alert and Bar Replay can each pick a different target from the same prices.
   - PENG-10 specifies a parity test and a bounded-memory fix. It is coordinated with calib_ml §1.33.
4. **[B-corr] Do NOT switch the ledger's same-bar rule to TradingView's broker-emulator convention (A's PENG-9).**
   - B measured both rules on about 140k CME bars, using 1-minute data as ground truth (§2.1).
   - The engine's candle-colour rule (bull bar = O-L-H-C) orders the bar's high and low correctly **88.1%** of the time. TradingView's open-proximity rule manages **80.6%**.
   - In asymmetric target/stop races the colour rule wins **70–87% vs 53–79%** across all 15 configurations.
   - PENG-9 is therefore rewritten: keep the rule, count the ambiguous races, and optionally resolve them with lower-timeframe data.
5. **Runtime risk is probably low but unmeasured (PENG-2, P2).**
   - [B-corr] The "20 s Basic / 40 s others / 100 s Ultimate" budget is not in the current official docs. limitations.md defers to the pricing page, and the 100 s figure comes from a third-party library, so the grade is **weak**.
   - The overhaul's static estimate is 5–8×10⁷ primitive operations on 20k 1-minute bars, "a few seconds".
   - [B-corr] A's "−33% from merging" is the docs' **9→1** merge demo (340.8 → 228.3 ms). The engine's possible merge is **2→1** (923 + 939), so the gain is smaller and unquantified.
   - [B-new] The merge also brings the engine to 5 request calls, the Pine Screener's cap.
   - Two of A's sub-items are dropped as separate work:
     - lazy iFVG drawing: low value, as the overhaul also concluded;
     - Clean-mode gating: the overhaul's perf-1 patch already covers it.
   - `calc_bars_count` and targeted `max_bars_back()` become conditional levers, used only if the Profiler shows a need.
6. **Measurement tooling is the main engineering lever for WHERE, WHEN and HOW LIKELY.**
   - PENG-6: a per-forecast export record plus an opt-in `log.info` decision trail. [B-new] Pine Logs keeps 10,000 historical messages.
   - PENG-7: the offline PineTS harness, extended with start-point parity and Bar Replay checks. [A✓] B confirmed PineTS 0.14.0 (2026-11-13) and its "experimental" v6 status from the cloned repository.
7. **Display robustness:**
   - PENG-3, the Heikin Ashi and non-standard chart guard. [B-corr] It covers **six** request calls, not five. B also adds a futures back-adjustment caveat.
   - PENG-4: confirmed-bar visibility for the PoT filter.
   - PENG-5: persistent render objects. [B-corr] Downgraded to P3: the absolute per-tick saving is tiny, and the tooltip benefit is unverified.
   - PENG-8: far anchors. [B-corr] Downgraded: the clamp sits 5,000 bars back, which is invisible on screen in practice.
8. **Endorsed overhaul fixes, re-validated by B:**
   - bias freshness at HTF close (struct-F2 / rp-bias-done): `barstate.isconfirmed and time_close == time_close(tf)` gating is non-repainting;
   - the `f_bump` int-overflow guard (pot-bump-floor-guard);
   - Clean-mode last-bar gating (perf-1).

---

## 1. Concepts (definitions and parameters)

### 1.1 Non-repainting higher-timeframe reads (`[1]` + `lookahead_on`) [A✓]
- **Definition.** `request.security(sym, tf, expr[1], lookahead = barmerge.lookahead_on)` returns the last **confirmed** HTF value from the first chart bar of each new HTF period. It behaves the same on historical and realtime bars.
  - Docs, concepts/other_timeframes_and_data.md:1398: "The most reliable approach to achieve non-repainting results is to use an `expression` argument that only references past bars (e.g., `close[1]`) while using `barmerge.lookahead_on`".
- **Parameters.** The offset of at least 1 goes *inside* the requested expression (lines 782 and 796 shift the whole tuple). Never request below the chart timeframe; `f_tfSafe` (564) enforces this.
- **[B-new] Freshness cost.** The final state of HTF bar N first appears on the first chart bar of HTF bar N+1. When the market is closed (nights, weekends) the table and `drawD` therefore lag one HTF candle.
  - A non-repainting fix: read the *unshifted* value only when `barstate.isconfirmed and time_close == time_close(tf)`, i.e. on the chart bar that closes the HTF bar. That value is final there, on historical bars and on the realtime closing tick alike. This is the overhaul's struct-F2 / rp-bias-done design; §5 has B's validation.
- **[B-new] Stakes, measured (§2.2).** A leaked daily read turns a no-edge signal into a 59.5% "hit rate" (+10 pp). The ledger's edge test exists to catch exactly that kind of inflation, so the `[1]` idiom is a precondition for an honest HOW LIKELY.
- **Failure modes:**
  - `lookahead_on` without an offset leaks the future;
  - `lookahead_off` without an offset repaints on realtime bars;
  - a request below the chart timeframe repaints;
  - a chart timeframe above the execution timeframe mislabels rows (warning at 1017; overhaul struct-F3 / TE2).

### 1.2 Bar states, realtime rollback and `varip` [A✓, B-new details]
- `barstate.isconfirmed` is true on every historical bar and on the closing update of a realtime bar (concepts/bar_states.md:91). It "will not work when used in a `request.security()` call" (:102).
- Rollback (language/execution_model.md:375–416):
  - `var` variables revert to the last committed state;
  - objects created on the open bar are removed;
  - "for objects … with references assigned to `var` variables, the rollback process reverts any changes to those objects that occur on the open bar".
  - Exceptions: `varip`, Pine Logs, alert logs and runtime errors.
- [B-new] Consequence for rendering. The current delete-all-and-recreate pattern (2132–2141) is functionally correct: each tick, rollback restores the committed drawings, and the script deletes and recreates them. A setter-based design (PENG-5) is also consistent: setter changes are reverted and then re-applied.
- `barstate.islastconfirmedhistory` is true on the dataset's last bar when the market is closed, or on the bar before the realtime bar. The docs suggest it for postponing heavy last-bar work (bar_states.md).
- DOL role (WHEN): targets, sweeps at close and ledger outcomes change only at bar close. The PoT readout and the sweep alert are deliberately live.

### 1.3 v6 semantic changes that can silently change results [A✓]
- **Lazy `and`/`or`** (migration_guides/to_pine_version_6.md:777): the right operand is skipped when the left one decides the result. A stateful call on the right then misses bars.
  - Verified for the engine: no `ta.*`, `f_changed*`, `f_sessOpen`, `f_rangeTrack`, `f_sessTrack`, `math.sum` or `request.*` appears after `and`, `or` or `?` (grep). All of them are global and unconditional (874–975).
- **Dynamic `for` bounds** (release notes, March 2025; loops.md): `to_num` is re-evaluated before every iteration.
  - Verified: the descending removal loops (1551, 1560, 1593, 1600, 1631, 1648) end at the constant 0.
  - Every ascending `0..size−1` loop is guarded (1095, 1002, 1393, 1816, 1954, 1973, 2051, 2153, 2161, 2176, 2260, 2274).
  - The loop at 1839 iterates `ixs`; the array is pushed to only after that loop ends (1852).
- **Strict bool**: never `na`; `[1]` on a bool returns `false` where there is no history. This is safe in the tuples at 782.
- **`timeframe.period` always has a multiplier** ("1D").
- **Fractional division of ints** (to_pine_version_6.md:330). [B-new] B checked the engine: every division that should be an integer uses `math.floor`, `math.round` or float operands.
- **`CW10003`** (errors/CW10003.md): history-dependent calls inside conditional or loop scopes may give inconsistent history.
  - [B-new] The engine's local-scope history readers (`f_anchorScan`: `high[i]`; `f_barAtTime`: `time[mid]`; the OB scans: `low[k]`, `coilScore[obI+1]`) read only *global* series, so their semantics are correct. Any warnings would be cosmetic.

### 1.4 Historical buffers and `max_bars_back` [A✓ with B-corr]
- Buffers are sized from references made in the **first 244 bars**. Exceeding them later restarts the script with larger buffers, repeatedly. The docs' example used 162,560 executions on 20,320 bars, i.e. **8x** (writing_scripts/profiling_and_optimization.md:1560ff).
- On realtime bars buffers are never resized: an overrun raises **RE10143** (errors/RE10143.md).
- `max_bars_back(var, num)` accepts `num` up to **5000** (reference/core.md:259–270).
- **[B-corr] The reference discourages the global parameter.**
  - core.md:273: "setting each buffer to the same size can substantially increase memory use. Therefore, unless most or all series in a script actually require buffers of the same size, using the `max_bars_back()` function … is typically more optimal".
  - RE10143.md: "Buffers that are larger than what a script requires can significantly impact the script's performance".
  - A treated the global `max_bars_back = 500` (line 31) as cost-free apart from memory. The docs say it can also cost runtime performance.
- [B-new] The engine's real dynamic offsets:
  - `atr[H]`, `close[H]`, `htfBias[H]`: H ≤ 450;
  - OB back-scans `high/low/open/close[k]`: ≤ obLook + 6 = 66;
  - `coilScore/indScore[obI+1]`: ≤ 67;
  - `ll20/hh20[loI+1]`: ≤ 61;
  - `f_anchorScan` `high/low[i]`: ≤ pivLen + 2 = 32, since it is only ever called with `pivLen + 2` (1759, 1771);
  - `sOpenB/hOpenB[pivLen]`: ≤ 30;
  - `time[lim]` in `f_barAtTime`: ≤ anchorMax = 450.
- So 500 covers every offset. Whether a targeted set of `max_bars_back()` calls is measurably faster is unknown; the Profiler A/B is in PENG-2. The overhaul's audit also chose to keep the global value, because removing it risks restarts.
- [B-new] limitations.md: "Some built-in series like `open`, `high`, `low`, `close`, and `time` have larger historical buffers that can reference up to 10,000 bars". The 5000-bar limit applies to "most series".

### 1.5 Drawing coordinate limits [A✓, B-new nuance]
- `xloc.bar_index` drawings can sit at most **10,000 bars** in the past and **500 bars** in the future (limitations.md, "Maximum bars back/forward").
- All drawings convert x-coordinates to timestamps through the `time` series. On realtime bars this needs a `time` buffer as deep as the oldest anchor (RE10143.md, "Historical buffer errors in realtime drawings"). That is why the engine has `max_bars_back(time, 5000)` (37) and clamps x with `f_x` (404–405).
- `time(timeframe, bars_back = -n)` gives the *expected* future bar time for n from 1 to 500 (reference/time.md:298), so drawings can also be placed with `xloc.bar_time`.
- [B-new] Visibility check. The clamp misplaces only anchors more than 4,999 bars back, for example a PWH on a 1-minute chart. The box's left edge would then sit about 3.5 days back instead of about 7, both far off screen. The defect is real but almost never visible, so PENG-8 is P3.

### 1.6 Drawing budgets and update strategy [A✓, B-corr magnitude]
- **Budgets:** 500 lines, 500 boxes, 500 labels, 100 polylines, and 9 tables (one per position). A drawing whose properties are `na` still counts (limitations.md).
- **"Reducing drawing updates":** historical updates are never visible, so restrict them to the last bar.
- **"Avoiding redrawing":** setters are cheaper than delete plus `*.new`. In the docs' Profiler demo, the `box.new()` line takes "close to **double** the combined time" of `box.set_lefttop` + `box.set_rightbottom` (profiling_and_optimization.md:1072–1118).
- [B-corr] The engine recreates 6–10 objects per realtime tick (Clean: box, 5 glow lines, tether and label = 8; Terminal = 6; +2 with `showInv`). The absolute saving from setters is therefore tiny. The remaining argument for setters is UX, and it is unverified: a stable label object keeps its hover tooltip.

### 1.7 Request budget, tuple merging and dynamic requests [A✓ with B-corr]
- **Limits:**
  - 40 unique `request.*()` calls, or 64 on Ultimate; identical calls are reused;
  - **127 tuple elements** across all calls;
  - 100k / 125k / 200k intrabars by plan;
  - the `calc_bars_count` argument of a request (simple int) limits the history it loads (limitations.md).
- **Engine usage:** 6 calls (923, 924, 925, 939, 981, 982) with 52 tuple elements (12×3 + 5 + 6 + 5). The overhaul's struct-F2 patch raises the total to 58.
- **Merging:** "condense them into a single `request.*()` call that uses a tuple … improve the runtime … reduce the script's memory usage and compiled size" (profiling_and_optimization.md:997).
  - [B-corr] The quoted 340.8 → 228.3 ms (−33%) result merged **nine** calls into one. 923 and 939 share one context (`syminfo.tickerid`, `f_tfSafe(tfH)`, `lookahead_on`), so the engine's merge is 2→1, with a smaller and unquantified gain.
  - In Day mode on charts below 1H, 925 and 981 also share the "60" context. Merging them would need mode-dependent code, so it is not proposed.
- **Dynamic requests** (the v6 default) can run in local scopes. The requested expression "**cannot** depend on" loop variables (other_timeframes_and_data.md:390). Otherwise, "there are insignificant differences in the behavior of dynamic and non-dynamic requests" (:261).
- **[B-new] Pine Screener cap.** TradingView help 43000742437 lists Premium or higher, the last **500 bars** only, the first 10 plots as columns, and **at most 5 `request.*` calls**. With 6 calls the engine cannot run in the screener at all. The 923 + 939 merge brings it to 5 (also COMP-9).

### 1.8 Whole-script budget: execution time, chart bars, `calc_bars_count`, Profiler [A✓ with B-corr grades]
- **Execution time:**
  - Loops are limited to 500 ms per bar (limitations.md:27).
  - [B-corr] Total time "varies with account types. See the 'Compare plans' section of the pricing page" (limitations.md:25). The current official docs give **no numbers**.
  - The "20 s Basic / 40 s others / 100 s Ultimate" figures come from older docs and a third-party "Plan Limit Timer" library. Grade: **weak**.
- **Chart bars:** 5k (Basic), 10k (Essential/Plus), 20k (Premium), 25k (Expert), 40k (Ultimate) (limitations.md:412).
- **`calc_bars_count`** in `indicator()` is a const int: "If specified, the script automatically adds a 'Calculated bars' input … the script starts its calculations that number of bars before the most recent bar … default 0" (core.md:183).
- **Pine Profiler:**
  - It reports per-line and per-block runtime and execution counts;
  - profile across configurations (profiling_and_optimization.md:723);
  - its overhead can push a script that is near the limit over it, so profile on fewer bars (:1680).
- **[B-new] Compile limits:**
  - compilation is limited to **2 minutes**, and after three consecutive warnings compiling is **banned for one hour** (limitations.md, "Script compilation");
  - compiled tokens ≤ 100,256 (unused code is discarded first);
  - 1,000 variables per scope (the engine's global scope has about 300 declarations plus about 80 tuple names);
  - the compilation request is ≤ 5 MB.
- [B-new] The overhaul's static cost estimate is 5–8×10⁷ primitive operations on 20k 1-minute bars with defaults. The heaviest all-bar loops are:
  - registry re-entry every 5 bars (1825–1852);
  - `f_bump` (1265–1271);
  - the pool, tracker and registry passes.
  - Only extreme inputs reach about 5–10x that: poolMax 80, calcBars 20000 and potH 450 together.
- DOL role: a timeout would be the most severe complaint possible ("it doesn't run"). With the current evidence the risk is low, but it is unmeasured.

### 1.9 Inputs: `display`, `active`, `inline`, `group`, `tooltip`, enums [A✓ with B-corr]
- `display`: "The default is `display.all` for all input types except 'bool' and 'color' inputs, which use `display.none` by default" (concepts/inputs.md:112). Every `input.*()` signature has `display` and `active` (reference/input.md).
- `active` (July 2025) takes an "input bool". When false, the input is greyed out.
- **CW10026:** "the updated alignment rules apply only if all inputs except for the first one on each line have an *empty title*". Fix: the first input carries the title, the rest use `""` (errors/CW10026.md; October 2026 release note).
- [B-corr] **Correct `active` map.** Each entry was checked against where the input is actually read:
  - `obQMin` is read only in `useOB and oq >= obQMin` (1701, 1742), so it takes `active = useOB`, not `useOB or useBRK`.
  - `priorM` is also read by `f_potBase` (1321), the ledger's random-level baseline, in either PoT model. So: `active = potModel == "Empirical" or accView != "Off" or useCal`.
  - `trackAge` also bounds `fvgTrk`, which drives the "New iFVG" alert even when `showIFVG` is off (1624–1627). Keep it always active.
  - `accView` also switches the ledger (2038) in Clean style when `useCal` is off. Keep it always active.
  - `lvnHours` and `lvnRows` feed the path cost (`f_pathVol`), so they take `showLVN or usePathVP`. COMP-1's "four LVN inputs: showLVN" is wrong for these two.
- Enums (`input.enum`): typed dropdowns. They are optional (§5).

### 1.10 Alerts [A✓, B-new server semantics]
- `alert(series message, freq)` fires on realtime bars only. `freq_once_per_bar_close` triggers "when the realtime bar closes" (concepts/alerts.md:70).
- `alertcondition()` takes a const message. Dynamic values come only through `{{plot_0..19}}` or `{{plot("title")}}` placeholders. Each call uses one plot count.
- **[B-new] Server execution.**
  - "TradingView saves a mirror image of the script and its inputs … to run the alert on its servers. Subsequent changes to your script's inputs or the chart will thus not affect running alerts" (alerts.md:23).
  - TradingView support 43000773984 (via search summary): the alert is calculated continuously, "after the alert is launched, the number of bars involved in its calculation only increases", so its results "may not match the results of the script's calculation on the chart".
- **[B-new] Alert-dialog repaint warning.** The yellow "may repaint" mark is a conservative static heuristic. Practitioners report it on scripts that correctly use `[1]` + `lookahead_on` (TradingView support 43000478429; PineCoders). Document it in the README.

### 1.11 Live visibility filter stability [A✓, weak]
- A show/hide decision taken from a live metric toggles visuals intrabar. Take it on confirmed bars with a hysteresis band instead; the text can still show live numbers.
- Engine: `dolShown` (2068) is computed from the live `activePoT`. It matters only when `minPoT > 0`, and the default is 0.

### 1.12 Non-standard charts and data feeds [A✓ with B-corr]
- `chart.is_standard` (simple bool) is false on Renko, Kagi, Line break, Point & figure, Range and Heikin Ashi (reference/chart.md:71).
- `syminfo.tickerid` "can also include information about data modifications such as dividend adjustment, **non-standard chart type**" (syminfo.md:809). Requests that use it therefore inherit the HA context.
- Real OHLC on such charts, per the official FAQ (faq/general.md:5–28): `request.security(ticker.new(syminfo.prefix, syminfo.ticker), …)`.
- `ticker.new(prefix, ticker, session, adjustment, backadjustment, settlement_as_close)` (ticker.md:167–178):
  - when `adjustment` is omitted, "default adjustment value is used (can be different depending on particular instrument)";
  - `backadjustment` and `settlement_as_close` default to *inherit the symbol's default*, not the user's chart setting.
- `ticker.standard()` also strips the extended session, dividend adjustment and currency conversion (ticker.md:273).
- [B-corr] Severity wording. On HA charts, wick extremes are only approximately real (HA high = max(high, haOpen, haClose)). The **close-based** rules are the most distorted, because HA close = (O+H+L+C)/4:
  - BOS / CHoCH: 747–748, 760, 770;
  - raid hold or reject: 1581;
  - iFVG inversion: 1603;
  - breaker flip: 1651.
  - "Distorted", not "fiction".

### 1.13 Volume-less symbols [A✓]
- `syminfo.volumetype` is "n/a when there is no volume or its type is not specified" (syminfo.md:839).
- The engine falls back to a neutral path cost (1417–1424), but LVN silently shows nothing.

### 1.14 Same-bar double touch (intrabar path convention) [B-corr: measured]
- **TradingView broker emulator:** "If the opening price of a bar is closer to the high than it is to the low … open → high → low → close", otherwise O-L-H-C (concepts/strategies.md:204–205). This is a *platform convention*, not a measured truth.
- **Engine `f_step`** (1440–1441): bull bar = O-L-H-C, bear bar = O-H-L-C. A bar that gaps through a barrier settles at the open.
- **[B-new] Measurement** (§2.1, 6 CME futures, 1-minute ground truth, about 140k bars):
  - which extreme printed first: colour rule **88.1–88.6%** correct vs TradingView's rule **80.5–81.8%**;
  - where the two rules disagree (about 15% of bars), colour is right **72–78%** of the time;
  - asymmetric two-level races: colour **70–87%**, TradingView **53–79%**, nearest-to-open **70–79%**;
  - the colour rule is best or tied in 14 of 15 configurations.
- **Conclusion:** the engine's rule is the better heuristic. Keep it.

### 1.15 Diagnostics: Pine Logs and chart-data export [A✓, B-new limits]
- `log.info(formatString, args…)` (reference/log.md) accepts series int, float, bool, string and arrays of them.
- Logs survive rollback (execution_model.md:414). [B-new] The pane shows "the most recent **10,000** logs for historical bars", then appends realtime logs (writing_scripts/debugging.md:183, 205).
- "Download chart data" exports OHLC plus indicator values to CSV (TradingView help 43000537255). Whether `display.data_window`-only plots are included is **not documented** (weak). Verify once.

### 1.16 Reload-dependent calculation window and path dependence [A✓, extended by B]
- The dataset's starting point depends on the plan and on alignment rules (minute charts align to a week, 15–29 minute charts to a month, and so on; repainting.md:268–297). So path-dependent state differs between loads.
- [B-new] Three contexts compute the same script from different starts:
  1. the chart after a reload;
  2. the running server alert, whose history only grows from creation;
  3. Bar Replay.
- Path-dependent engine state:
  - `inCalc` and the ledger start (1519, 2038);
  - cumulative calibration (`f_calMult`, 1376) and race adjustment (`f_raceAdj`, 1367);
  - the 2-bar challenger hysteresis (2014);
  - pool contents, which before `inCalc` are trimmed by distance and tier (2048) rather than by score.
- These differences are not look-ahead. But they can show the user a target that differs from the one the alert announces (PENG-10).

### 1.17 Offline v6 runtime (PineTS) [A✓]
- LuxAlgo **PineTS 0.14.0** (2026-11-13; AGPL-3.0 plus a commercial licence). B verified this from the cloned repository's `package.json` and `CHANGELOG.md`.
- It transpiles native v6 (README: "*(experimental)*") and runs it with Pine time-series semantics.
- The 0.14.0 parity list touches constructs the engine uses:
  - `ta.*` history starts at the first call;
  - v6 `for` re-reads `to` every iteration;
  - rollback of variables on discarded ticks;
  - `barstate.isrealtime` is false when the market is closed;
  - negative `bars_back`, `timeframe_bars_back`;
  - `request.security_lower_tf` edge cases;
  - `alertcondition` placeholders.
- It has not been run on the engine: `npm install` was denied in this session.

### 1.18 Script size and scope limits [A✓]
- 100,256 IL tokens; 1,000 variables per scope; scope-count limit removed (Feb 2025); 5 MB compilation request; 2-minute compile time (§1.8).
- Collections hold at most 100,000 elements. debugging.md:1429 says "across all instances of each collection type". The engine's peak is far below: the `lv*` arrays ≤ 5×1000, `tfOpenBar` ≤ 4000 pairs.

### 1.19 `behind_chart` and z-order [A✓]
- `behind_chart` (default true) draws plots and drawings behind the candles when `overlay = true` (core.md:192). The engine's default is right.

### 1.20 [B-new] Chart-timeframe vs HTF bar-close alignment (`time_close(tf)`)
- `time_close(timeframe)` returns the close time of the `timeframe` bar that contains the current chart bar (time.md:383–392).
- `time_close == time_close(tf)` is true exactly on the chart bar that closes the HTF bar. It fails closed (stays false) on holidays, data gaps and na.
- This lets a non-repainting read of the just-completed HTF bar happen on its final chart bar, without waiting for the next bar (§1.1, §5).

### 1.21 [B-new] Test instruments inside TradingView
- **Bar Replay:** stepping forward executes the script in realtime mode. RE10143.md uses "Forward" to reproduce realtime-only errors. It is the official way to exercise rollback and the closing-tick logic offline.
- **Pine Profiler** (§1.8).
- **Alerts log:** a realtime ground truth for WHEN.

### 1.22 [B-new] Pine Screener constraints
- Premium plan or higher; the last 500 bars only; the first 10 plots become columns (`display.pine_screener`, constants.md:125); at most 5 request calls; `input.timeframe` values are ignored (TradingView help 43000742437; COMP-9).
- The empirical PoT needs at least 600 windows and the ledger at least 300 warm-up bars, so neither warms up there.

---

## 2. Evidence

### 2.1 [B-new] Same-bar ordering heuristics, measured on 1-minute ground truth

- **Data:** CME ES, NQ, YM, RTY, GC and CL 1-minute bars, 2026-01-20 to 2026-04-15. Local copies in `study/amt_data/cme/`.
- **Method:**
  - Resample to 5, 15, 60 and 240 minutes.
  - The first 1-minute bar printing the bar's high (low) gives the time of the high (low).
  - Bars where both extremes print in the same 1-minute bar are ambiguous and excluded: 3.9% at 5m, 0.5% at 15m, ≤ 0.1% at 1H and above.
- Scripts and outputs: `study/pine_eng_b_tools/intrabar_order.py`, `intrabar_race.py`, `intrabar_race2.py`, plus the matching `*_out.txt` files.

**(a) Which extreme came first.** Pooled, bar-weighted:

| TF | Bars | Colour rule (engine) | TradingView rule | Bars where the rules disagree | Colour right when they disagree |
|---|---|---|---|---|---|
| 5m | 97,230 | **0.881** | 0.806 | 15.4% | 0.745 |
| 15m | 32,373 | **0.881** | 0.806 | 15.5% | 0.743 |
| 1H | 8,092 | **0.886** | 0.805 | 14.5% | 0.778 |
| 4H | 2,110 | **0.886** | 0.818 | 15.1% | 0.724 |

Per symbol the colour rule wins in all 24 symbol × timeframe cells, by 4–12 pp.

**(b) Two-level race.**
- Setup: an upper level at fraction u of the bar range and a lower level at v, both touched in the bar, with the open between them. Which was touched first?

| TF | (u, v) | n | Colour | TradingView | Nearest-to-open |
|---|---|---|---|---|---|
| 5m | (0.9, 0.1) | 63,247 | **0.834** | 0.753 | 0.752 |
| 5m | (0.9, 0.5) | 23,587 | **0.713** | 0.528 | 0.704 |
| 15m | (0.95, 0.3) | 18,306 | **0.794** | 0.743 | 0.760 |
| 15m | (0.9, 0.5) | 10,538 | 0.704 | 0.564 | **0.732** |
| 1H | (0.6, 0.05) | 4,019 | **0.744** | 0.693 | **0.744** |
| 1H | (0.9, 0.1) | 5,848 | **0.852** | 0.779 | 0.779 |

- All 15 configurations are in `intrabar_race2_out.txt`. The colour rule is best or tied in 14 of 15.
- In the symmetric mid-range case (u, v) = (0.6, 0.4), TradingView's rule wins on 15m and 1H (0.69–0.71 vs 0.65–0.67).
- **Grade: moderate.** These are B's own replications: 6 liquid futures, one quarter, all on 1-minute data. Crypto and FX are not tested.

### 2.2 [B-new] Illusory edge from a leaked HTF read
- **Setup:**
  - 1-hour CME bars, 2025-03 to 2026-04, about 33k signals in total.
  - Signal: the sign of the daily candle's direction.
  - Outcome: from each 1H close, is +1 ATR(14) in the signal direction touched before −1 ATR against it within 10 bars? A same-bar double touch counts as a loss.
- **Result:**

| Read | Win rate (mean of 6 symbols) | Range |
|---|---|---|
| Honest (previous day = `[1]` + lookahead_on) | **0.496** | 0.476–0.513 |
| Leaked (current day = lookahead_on without offset) | **0.595** | 0.586–0.608 |

- Script: `study/pine_eng_b_tools/lookahead_leak.py`, output `lookahead_leak_out.txt`.
- **Grade: moderate.** Own replication with a deliberately simple signal. It shows the size of the error class, not the engine's exposure, which is zero today.

### 2.3 Evidence table (A + B)

| Fact | Number | Grade | Source |
|---|---|---|---|
| Inputs printing in the legend | 76 of 104 (23 int, 31 float, 9 string, 10 session, 3 timeframe) [A✓ by grep] | strong | 59–237; inputs.md:112; input.md |
| CW10026 inline rows | 4 (230–237) | strong | errors/CW10026.md |
| Unique requests | 6 of 40/64 (923, 924, 925, 939, 981, 982) | strong | limitations.md |
| Tuple elements | 52 of 127 (58 after overhaul struct-F2) | strong | limitations.md |
| Plot counts | 5 plots + 4 alertconditions = 9 of 64 (plot colours are simple, so 1 count each) | strong | 2090–2093, 2444–2448; limitations.md |
| Loop limit | 500 ms per bar | strong | limitations.md:27 |
| Total execution budget | not stated officially; 20 s / 40 s / 100 s per older docs and a third-party library | **weak** [B-corr from moderate] | limitations.md:25; "Plan Limit Timer" library |
| Chart bars by plan | 5k / 10k / 20k / 25k / 40k | strong | limitations.md:412 |
| Tuple merge gain | 340.8 → 228.3 ms for **9→1**; 2→1 unquantified | moderate (vendor demo) [B-corr scope] | profiling_and_optimization.md:991–1070 |
| Buffer restart cost | 8x executions in the demo | moderate | profiling_and_optimization.md:1560ff |
| Global `max_bars_back` cost | "can substantially increase memory use"; "can negatively impact … runtime performance" | strong (official statement; magnitude unknown) [B-new] | core.md:273; RE10143.md |
| Setter vs recreate | `box.new` line about 2x the two setter lines | moderate (vendor demo) | profiling_and_optimization.md:1072–1118 |
| Drawing x-limits | 10,000 bars past, 500 future; `max_bars_back()` ≤ 5000; OHLC and `time` can reference 10,000 | strong | limitations.md; core.md |
| Intrabars | 100k / 125k / 200k | strong | limitations.md |
| Pine Logs | 10,000 historical messages shown | strong [B-new] | debugging.md:183 |
| Compile time | 2 min; one-hour ban after 3 consecutive warnings | strong [B-new] | limitations.md |
| Alert = server mirror image of script and inputs | — | strong [B-new] | alerts.md:23 |
| Alert history grows from launch, so it can diverge from the chart | — | moderate (official help via search summary) [B-new] | TradingView support 43000773984 |
| Pine Screener | Premium+; 500 bars; ≤ 5 requests; first 10 plots | moderate (official help via search summary) [B-new] | TradingView help 43000742437 |
| Same-bar ordering | colour 88% vs TradingView 81% (§2.1) | moderate (own replication) [B-new] | §2.1 |
| Leaked HTF read | +10 pp illusory win rate (§2.2) | moderate (own replication) [B-new] | §2.2 |
| Static cost estimate | 5–8×10⁷ primitive operations on 20k 1m bars | weak (code count, not measured) [B-new] | overhaul journal, perf audit |
| PineTS | 0.14.0 (2026-11-13), native v6 "experimental" | weak to moderate [A✓] | cloned repository: `package.json`, `CHANGELOG.md`, README |
| CSV export of `data_window` plots | unknown | weak | TradingView help 43000537255; third-party guides |

Grading note: the official manual is graded **strong** for mechanisms, because it is the specification. Vendor Profiler demos are **moderate** for magnitudes. B's replications are **moderate**: real data, but narrow coverage. User-perception claims are **weak**.

---

## 3. Engine gap analysis (line references)

Status key: present (done well, leave it), partial, missing, wrong.

| # | Concept | Status | Engine lines | What the engine does / what differs |
|---|---|---|---|---|
| G1 | `[1]` + `lookahead_on` MTF | **present** [A✓] | 782, 796, 923–925, 939, 981 | Correct. `f_tfSafe` (564) prevents lower-timeframe requests. |
| G2 | Confirmed-bar engine | **present** [A✓] | 1518 | Structure, pools, scoring, selection, ledger, iFVG and breakers. |
| G3 | Rollback-safe live sweep | **present** [A✓] | 1504–1509, 2084–2085 | `activeLv` is a `var` reference and the sweep only reads it. |
| G4 | Lazy and/or safety | **present** [A✓, re-grepped] | 874–975 | No stateful call on the right-hand side. |
| G5 | Dynamic `for` bounds | **present** [A✓, all loops re-checked] | §1.3 | No loop mutates its own bound; size-0 guards everywhere. |
| G6 | Historical buffers | **partial** [B-corr from present] | 31, 37 | Works: all offsets ≤ 450 < 500, so no restarts. But the global 500 is the pattern the reference discourages; cost unmeasured (PENG-2 A/B). |
| G7 | Drawing x-clamp | **partial** [A✓] | 404–405, 37 | Correct for the 5000 cap. Anchors more than 4,999 bars back are clamped; almost never visible (§1.5). |
| G8 | Rendering on the last bar only | **present** [A✓] | 2111, 2132, 2295, 2310; `tailBar` 1525, 1641 | — |
| G9 | Historical iFVG drawing churn | **partial, low value** [B-corr] | 1611–1623 | About 1k create/delete pairs per load. The overhaul judged this not worth changing; B agrees. |
| G10 | Recreate vs setters | **partial** [B-corr from missing] | 2132–2141, 2216–2248 | Functionally correct under rollback. Costs 8 objects per tick; tooltip stability unverified. |
| G11 | Table updates | **partial** [A✓] | 2296, 2311 | Last bar only (good). Full `table.clear` plus a rebuild every tick (small cost). |
| G12 | Request merging | **partial** [A✓] | 923 + 939 | Same context, two calls. The merge also unlocks the Pine Screener's 5-call cap. |
| G13 | `calc_bars_count` | **missing (low priority)** [B-corr] | 31, 85, 1519 | Only scoring, selection and the ledger are depth-limited. Static estimate says no timeout risk; measure first. |
| G14 | Clean-mode dead work | **partial → overhaul perf-1 patch** | 2111–2130 | `f_raceH` uses 12–70 terms in practice (the 400 cap is unreachable inside maxATR). Covered by the overhaul. |
| G15 | Input `display` | **wrong → overhaul patch** | 59–237 | TE1 / VIS-statusline-inputs / ux-statusline-inputs carry the 76 edits. Make sure they land. |
| G16 | Input `active` | **missing → overhaul patch (map needs fixes)** | 59–237 | Fix `obQMin`, `priorM`, `trackAge`, `accView` and the LVN pair (§1.9). |
| G17 | Inline alignment | **wrong (warning)** [A✓] | 230–237 | 4× CW10026. **Not** in the overhaul patches. |
| G18 | Enums | **missing (minor)** [A✓] | 60, 123, 166, 177, 181, 190, 216, 229 | String compares; cheap; optional. |
| G19 | `behind_chart` | **present** [A✓] | 31 | — |
| G20 | Alerts | **partial** [A✓] | 2079–2093 | Correct frequencies. Content, toggles and placeholders: COMP-2 and overhaul ux-alert-content. |
| G21 | Live visibility filter | **partial** [A✓] | 2066–2068, 2202, 2185, 2349 | Only when `minPoT > 0` (default 0). |
| G22 | Non-standard charts | **missing** [A✓] | 874–920, 923–982 | No `chart.is_standard` check; all six requests inherit the HA context. |
| G23 | Volume-less symbols | **partial** [A✓] | 979, 1417–1424, 2251 | Neutral fallback; LVN is silently empty. |
| G24 | Same-bar double touch | **present (better than TradingView)** [B-corr from partial] | 1440–1441 | The colour rule beats TradingView's emulator rule (§2.1). Missing: an ambiguity count. |
| G25 | Pine Logs / export | **missing** [A✓] | 2436–2448 | 5 data-window plots, no per-forecast record, no decision log. |
| G26 | Reload/alert path dependence | **partial** [A✓, B-extended] | 1376–1382, 1367–1371, 1519, 2038, 2014 | Cumulative learned state, so chart, alert and replay can diverge. Not measured. |
| G27 | Chart TF above execution TF guard | **present** [A✓] | 564–565, 1017, 2305–2307, 2431–2433 | Overhaul TE2 / struct-F3 improve the labelling. |
| G28 | Drawing and plot budgets | **present** [A✓] | 32 | Worst case about 163 boxes, 150 lines and 108 labels (overhaul audit). |
| G29 | Offline execution / CI | **missing** [A✓] | — | Only a syntax parser (pynescript). |
| G30 | varip | **n/a** [A✓] | — | Correctly unused. |
| G31 | [B-new] Bias freshness at HTF close | **wrong → overhaul struct-F2 / rp-bias-done** | 782, 926–931, 2299–2304 | One HTF candle stale whenever the last chart bar is confirmed. B validated the fix (§5). |
| G32 | [B-new] Pine Screener compatibility | **missing** | 923–982 | 6 request calls exceed the screener's cap of 5. |
| G33 | [B-new] `f_bump` int overflow when ATR collapses | **wrong → overhaul pot-bump-floor-guard** | 1268 | Floor before clamp; a negative loop bound can crash. |
| G34 | [B-new] HTF FVG/structure on futures with settlement-as-close | **n/a (documented behaviour)** | 923–939 | `syminfo.tickerid` carries the chart's futures settings, so D-context closes follow the chart setting. The `ticker.new` fallback in PENG-3 inherits the *symbol default* instead (ticker.md:177–178). |
| G35 | [B-new] Run IDs as identities | **note** | 1030, 1655 ff. | `nextId` depends on the start bar, so any cross-run comparison must key on (kind, price, anchor time), not `id` (PENG-6, PENG-10). |

---

## 4. Proposals (best first; 11)

Each proposal gives the algorithm, the Pine v6 implementation, value, evidence, risk, effort and what the ledger can measure. Compile-relevant claims cite the local manual.

### PENG-1 (P1, S, visual-ux) · Settings hygiene: land the overhaul's `display`/`active` patches, fix the `active` map, remove the CW10026 warnings
*Merges with COMP-1 and the overhaul's TE1 / VIS-statusline-inputs / ux-statusline-inputs.*

1. **`display = display.none`** as a literal on the 76 int, float, string, session and timeframe inputs (60–226). The patch exists in the overhaul journal; verify it applies in full: `grep -c "display = display.none"` must return 76. Doc: input.md ("The default is `display.all`").
2. **`active` map, corrected [B-corr].** Every controlling input is declared earlier, so there are no forward references.

   | Inputs | `active =` |
   |---|---|
   | `cHTF`, `cSTF`, `cEXE` (62–64) | `modeIn == "Custom"` |
   | `sessAs`, `sessLo`, `sessNA` (107–109) | `useSess` |
   | `fvgQMin` (115) | `useFVG` |
   | `obQMin` (119) | `useOB` (breakers never read it, 1701/1742) |
   | `obLook` (118) | `useOB or useBRK` |
   | `delivIn` (123) [B-new] | `useFVG or useOB or useBRK or useHTFFVG` |
   | `ifvgMaxIn`, `ifvgMax` (196–198) | `showIFVG` |
   | `trackAge` (199) | always active (it feeds the iFVG alert, 1624–1627) |
   | `lvnThr`, `lvnN` (206–207) | `showLVN` |
   | `lvnHours`, `lvnRows` (204–205) | `showLVN or usePathVP` |
   | `ghostMax` (211) | `showGhost` |
   | `hudSize` (177) | `uiStyle == "Terminal"` |
   | `accView` (190) | always active (it also switches the ledger, 2038) |
   | `warmup` (192) | `accView != "Off" or useCal` |
   | `priorM` (186) | `potModel == "Empirical" or accView != "Off" or useCal` (`f_potBase` reads it, 1321) |
   | `tablePosIn` (216) | `showTable` |
   | `uAbove` … `uText` (230–237) | `theme == "Custom"` |

3. **CW10026 [A✓, not in the overhaul].** Keep the title only on the first input of each inline row and pass `""` on the second:
   - `"Custom · Buy / Sell-side"`, `"Custom · Bull / Bear"`, `"Custom · LVN / Ghost"`, `"Custom · Panel / Text"`;
   - add a tooltip naming both fields;
   - doc: errors/CW10026.md steps 1–2.

- **Value.** Removes the largest visible "cluttered" difference from the reference, clears 4 compiler warnings, and greys out irrelevant settings.
- **Evidence.** Mechanism strong; benefit weak.
- **Risk.** None functionally.
- **Effort.** S.
- **Ledger.** Not measurable.

### PENG-10 (P2, M, robustness) [B-new] · Reload and alert parity: a start-point invariance test and bounded-memory learned state
- **Problem** (G26, §1.16). Three contexts compute the engine from different starting points:
  - the chart after a reload;
  - the server-side alert, a "mirror image" whose bar count only grows from launch;
  - Bar Replay.
- Unbounded-memory state makes their target choices diverge: `f_calMult` reads the cumulative `stN/stK/stPE` with a ±20% multiplier, and `f_raceAdj` reads the cumulative `raceSt`. The trader then gets an alert naming a target the reloaded chart does not show, which looks like "the targets jump around".
- **Step 1: parity test.** Use the PENG-6 export.
  1. Load the same chart twice: "Calculated bars" (or Bar Replay start) at N and at N − 1000.
  2. Over the last 1,000 confirmed bars, compare the active target per bar by **(kind, price, anchor time)**. `id`s are not comparable across runs (G35).
  3. **Acceptance:** at least 98% of bars agree, and the first disagreement after the common start dies out within 2·H bars.
  4. Run it with `useCal` on and off. The difference isolates the calibration's contribution.
- **Step 2: if the test fails, bound the memory.**
  - Keep the displayed accuracy stats cumulative (`stN/stK/...`).
  - Feed the learners from decayed sums. Add `var array<float> cuN, cuK, cuE` (size 5) and `var array<float> rcN, rcW, rcP` (size 3).
  - In `f_book` (1461), for `g in [t.grp, 4]`: `cuN[g] := λ·cuN[g] + 1`, `cuK[g] := λ·cuK[g] + y`, `cuE[g] := λ·cuE[g] + t.pBase`, with `λ = 0.99` (an effective memory of about 100 trials; const).
  - The race sums work the same way.
  - `f_calMult` (1376) and `f_raceAdj` (1367) read the decayed sums. The `n ≥ 10` gate uses `cuN`.
  - With λ < 1, two runs that started at different points converge geometrically once they share about 3/(1−λ) = 300 trials.
- **Coordination.** calib_ml §1.33 makes the same point and proposes gated learners. Whichever learner is adopted must pass Step 1. This proposal sets the engineering acceptance test and gives the fallback.
- **README.** Document that alerts must be recreated after any input change ("mirror image", alerts.md:23), and that the accuracy panel depends on the loaded history.
- **Value.** Alerts and chart agree. Reloads stop silently changing past and present targets.
- **Evidence.** Mechanism strong (alerts.md:23; repainting.md "Dataset variations"); alert-history growth moderate (support 43000773984); magnitude for this engine **none** until Step 1 runs. Overall moderate.
- **Risk.** Low. λ trades drift adaptation against noise; calib_ml found forgetting neutral to slightly negative for accuracy at these sizes, so use the gentlest λ that passes Step 1.
- **Effort.** M (S for Step 1 once PENG-6 exists).
- **Ledger.** Parity agreement % is the metric.

### PENG-6 (P2, M, statistics-ledger) · Forecast telemetry: per-forecast export record and opt-in decision log [A✓, B-extended]
1. **Inputs.** New group "Diagnostics" with `dbgExport` and `dbgLog`, both false and `display = display.none`.
2. **Export record.** On the bar where `f_openTrial` runs (2045), set per-bar variables and plot them **after** the existing 5 plots, so `{{plot_0..4}}` keep their meaning.
   - Fields:
     - `xPx`: the target price [B-new, for run-independent identity];
     - `xKind`: kind·10 + src [B-new];
     - `xAnchorT`: `time[bar_index − anchorBar]`, exact because `f_x` keeps anchors inside the 5000-bar `time` buffer (line 37) [B-new];
     - `xSide`, `xEdge`, `xInv`;
     - `xD0`: distance in ATR;
     - `xPoT`: the model PoT at assertion;
     - `xBase`: `pBase`;
     - `xGrp`, `xScore`.
   - All use `display = display.data_window` and are na elsewhere or when disabled. That is 11 plots, for a total of 20 of 64.
   - Outcomes are recomputed offline from the CSV's OHLC, which avoids several trials resolving on the same bar.
   - CSV inclusion of data-window-only plots is undocumented: verify once. The fallback is `display.all` with fully transparent colour.
3. **Decision log.** When `dbgLog and inCalc`, on each confirmed change of `activeId` (2030):
   - `log.info("{0} DOL {1}→{2} {3} score {4,number,0.0} chall {5} side {6} D {7,number,0.00} why {8}", str.format_time(time), prevId, pickId, f_shortName(activeLv.kind, activeLv.src), activeLv.score, challN, dirSide, drawD, reason)`;
   - `reason` ∈ {sweep, eject, invalid, lead2, counter, none};
   - also log sweeps and ejections (step 3) and ledger bookings (step 2);
   - [B-new] the pane keeps only the last 10,000 historical logs (debugging.md:183), so limit logging to `inCalc` plus an optional "last N bars" input.
- **Value.** Shows why the target changed. It enables offline reliability, Brier and per-family analysis on the forecasts the user actually saw, and it is the data source for PENG-10's parity test.
- **Evidence.** Logs strong; CSV export of plots moderate; data-window-only inclusion weak.
- **Risk.** Low. Plot order must stay stable for alert placeholders (COMP-2 / COMP-9 output contract).
- **Effort.** M.

### PENG-7 (P2, M, robustness) · Offline execution harness (PineTS): smoke, repaint regression, start-point parity, ledger replay [A✓, B-extended]
- **Tool.** PineTS 0.14.0, dev-only (AGPL; never shipped). `npm install` needs the user's approval: it was denied in this session.
- **Data.** A custom provider extending `BaseProvider`:
  - the local CME 1-minute and 1-hour CSVs (`study/amt_data/cme`), as used in §2.1;
  - synthetic GBM bars for deterministic tests;
  - HTFs through PineTS's aggregation.
- **Tests:**
  1. **Smoke.** Every Trading Mode × both styles × `accView = Full` over 20k bars: no runtime errors, and non-na DOL plots after warm-up.
  2. **Repaint regression.** `run()` on N bars vs N − k bars followed by `k` streamed updates (`stream()` / `update()`). On every confirmed bar, the DOL price, score, (kind, price) identity and ledger plots must be identical.
  3. **[B-new] Start-point parity.** The PENG-10 Step 1 test, automated over 20 symbols.
  4. **Ledger replay.** A/B other studies' proposals by toggling inputs over 20–50 symbols, reading hit %, edge z and race win %.
  5. **Performance proxy.** Wall time per 10k bars, per commit.
- **In-platform complement [B-new]:**
  - Bar Replay "Forward" over 200 bars, comparing the replayed targets with a fresh load (official realtime-reproduction method, RE10143.md);
  - one live alert whose log is compared with the chart after a reload.
- **Evidence.** Weak to moderate: PineTS lists TradingView-parity fixes for exactly these constructs, but native v6 is "experimental".
- **Risk.** False alarms from runtime differences; triage them against TradingView.
- **Effort.** M.

### PENG-2 (P2, S–M, performance) · Measure first: merged HTF request, Profiler and Replay protocol, conditional levers [A✓, B-corr scope]
1. **Merge 923 + 939 into one request** [A✓; B-corr on the gain]. After `f_htfFvg` (about line 797):
   ```
   f_htfPack(int len, float minAtr, float dm) =>
       [b, ib, rh, rl, pvh, pvl, pht, plt, hv, lv, prh, prl] = f_structure(len)
       [fd, ft, fb, fq, fT] = f_htfFvg(minAtr, dm)
       [b, ib, rh, rl, pvh, pvl, pht, plt, hv, lv, prh, prl, fd, ft, fb, fq, fT]
   ```
   - Replace 923 and 939 with one `request.security(syminfo.tickerid, f_tfSafe(tfH), f_htfPack(biasLen, fvgMin, dispMult), lookahead = barmerge.lookahead_on)`.
   - Both inner functions are already `[1]`-shifted, so non-repainting is unchanged.
   - Requests drop from 6 to 5 (the Pine Screener cap); tuple elements are unchanged at 52, or 58 with struct-F2's two extra values per TF.
   - Gain: smaller than the docs' 9→1 demo and unquantified.
   - Regression: the ledger's n, hit % and edge must match before and after on the same chart.
2. **Profiler protocol** (profiling_and_optimization.md:17–760):
   - Cases: BTCUSD 1m (20k bars, Scalping); ES 5m (Day); EURUSD 1h (Day, no volume); SPY 4h (Swing, lower-TF path active).
   - Run each in Clean and in Terminal-Full, with `calcBars` at 5000 and at 20000, three runs each (docs: resources fluctuate).
   - Record total ms, global execution count (= bars means no buffer restarts), and the top-5 lines.
   - [B-new] Add a Bar Replay pass to time realtime ticks.
3. **Conditional levers.** Apply only if the Profiler shows a need, for example a total above about 50% of the slowest plan's budget on a 40k-bar chart:
   - `indicator(..., calc_bars_count = 20000)`: an official "Calculated bars" input; const int (core.md:183);
   - replace the global `max_bars_back = 500` with targeted calls (core.md:273):
     - `max_bars_back(high, 500)`, `max_bars_back(low, 500)`, `max_bars_back(close, 500)`, `max_bars_back(open, 70)`, `max_bars_back(atr, 460)`, `max_bars_back(htfBias, 460)`;
     - `max_bars_back(coilScore, 70)`, `max_bars_back(indScore, 70)`, `max_bars_back(ll20, 70)`, `max_bars_back(hh20, 70)`;
     - keep `max_bars_back(time, 5000)`;
     - check that the Profiler's execution count still equals the bar count;
   - throttle registry re-entry (1825) to `regNew or bar_index % 10 == 0` outside `inCalc`;
   - cache `f_pathVol` per profile rebuild.
4. **Dropped from A's pack** [B-corr]:
   - lazy iFVG drawing: about 1k pairs per load, negligible (overhaul agrees);
   - Clean-mode gating: already the overhaul's perf-1 patch.
- **Value.** Replaces "probably fine" with a number, and enables the screener.
- **Evidence.** Mechanisms strong; magnitudes moderate (vendor demos); engine-specific total unknown.
- **Risk.** Low (tuple order).
- **Effort.** S (merge) / M (protocol).

### PENG-3 (P2, S, robustness) · Non-standard chart and data guard [A✓ with B-corr]
1. `bool stdChart = chart.is_standard` after line 309 (simple bool, chart.md:71).
2. `string tkr = stdChart ? syminfo.tickerid : ticker.new(syminfo.prefix, syminfo.ticker, syminfo.session)` (FAQ pattern; ticker.md:167).
   - Use `tkr` in **all six** requests: 923, 924, 925, 939, 981, 982 [B-corr: A said five].
   - Do not use `ticker.standard()`: it also drops the extended session and adjustments.
   - [B-new] Caveat: `ticker.new` without `adjustment` uses the instrument default. Its `backadjustment` and `settlement_as_close` follow the symbol default, not the user's chart setting (ticker.md:177–178). Exposure is small because this applies only on non-standard charts. Document it.
3. Warning row in both styles, mirroring `tfWarn` (2305–2307, 2431–2433): "⚠ NON-STANDARD CHART | levels use synthetic candles". `ledgerOK = stdChart` is ANDed into the trial-open condition (2038), and the Terminal shows "LEDGER OFF · use candles".
4. `needVP := (showLVN or usePathVP) and syminfo.volumetype != "n/a"` (syminfo.md:839), plus an LVN tooltip: "needs volume data".
5. Optional (M–L): drive the engine from real same-TF OHLC on Heikin Ashi charts. Invasive: `ta.atr` and `ta.tr` read the chart's own OHLC internally, so TR would have to be rebuilt by hand. The default is to warn.
- **Value.** Prevents distorted targets and an invalid accuracy panel on HA charts. The close-based rules are the most affected (§1.12).
- **Evidence.** Mechanism strong; prevalence unknown.
- **Risk.** Low.
- **Effort.** S.

### PENG-9 (P3, S, statistics-ledger) · Same-bar double touch: KEEP the colour rule; count and expose ambiguous races [B-corr: A's switch reversed]
- **Do not** adopt TradingView's open-proximity rule. On 1-minute ground truth it is 5–18 pp less accurate than the engine's rule in 14 of 15 race configurations (§2.1).
- **Ambiguity counter:**
  - `raceSt` becomes `array.new<float>(8, 0.0)` (1079); add a Trial field `bool amb = false`;
  - in `f_step` (1444–1446), when `t.race == 0 and hit and stp and not tgtOpn and not stpOpn`, set `t.amb := true` before applying the colour rule;
  - in `f_book`, `if t.amb` add 1 to `raceSt[7]`;
  - the Full view's RACE row shows `AMBIG x%` = `raceSt[7] / raceSt[0]`.
- **Optional exact resolution (M):**
  - only if AMBIG exceeds about 5%;
  - `request.security_lower_tf(tkr, timeframe.from_seconds(math.max(60, timeframe.in_seconds() / 10)), [high, low], ignore_invalid_timeframe = true)`, read when `hit and stp`;
  - costs: one more request (screener cap) and intrabar budget.
- **Value.** Users see how much of WIN≤H rests on an assumption, and the assumption in use is the better one.
- **Evidence.** Moderate (B's replication).
- **Risk.** None.
- **Effort.** S.

### PENG-4 (P3, S, visual-ux) · Confirmed-bar visibility with hysteresis for the Minimum-PoT filter [A✓]
- STATE: `var bool showC = false` and `var int showId = -1`.
- After line 2067, on `barstate.isconfirmed`, with `pp = nz(activePoT) * 100`:
  - if `na(activeLv)`: `showC := false`;
  - else if `activeLv.id != showId`: `showC := pp >= minPoT` and `showId := activeLv.id`;
  - else: `showC := showC ? pp >= minPoT − 2.0 : pp >= minPoT`.
- Rendering (2202), the Terminal "FILTERED" cell (2349) and `annNow` (2071) use `showC`. The label text keeps the live PoT.
- Secondary targets (2185) use their PoT cached at bar close.
- Only active when `minPoT > 0` (default 0), hence P3.
- **Evidence.** Mechanism strong (rollback docs); perception weak.
- **Effort.** S.

### PENG-12 (P3, S, alerts) [B-new] · Alert and README engineering notes
1. README, "Alerts" section:
   - "Alerts run a server copy of the script with the inputs at creation time; after changing settings, delete and recreate the alert" (alerts.md:23);
   - "The alert dialog's 'may repaint' mark is a generic heuristic. The PoT readout and DOL Target Swept are intentionally live; everything else is computed on bar close";
   - the "Any alert() function call" condition bundles all four `alert()` events. Use COMP-2's per-event toggles to filter them.
2. Keep the `alertcondition` titles and plot order stable. Once COMP-2 lands, add `'{{plot("DOL Price")}}'` and `'{{plot("DOL PoT %")}}'` in single quotes (alerts.md:362–372).
3. README note: "Heikin Ashi or Renko charts: levels and accuracy use synthetic candles" (pairs with PENG-3).
- **Value.** Prevents "the alert disagrees with my chart" and "it says it repaints" support complaints.
- **Evidence.** Strong (official docs); perception weak.
- **Effort.** S.

### PENG-5 (P3, M, visual-ux) · Persistent render objects updated with setters [A✓, B-corr priority]
- Declare once:
  - `var box rZone = box.new(na, na, na, na, border_style = line.style_dashed)`;
  - `var array<line> rGlow`, filled with 5 lines on `barstate.isfirst`;
  - `var line rTeth` and `var label rLab`.
- On `barstate.islast`:
  - when shown: update with `box.set_lefttop`/`set_rightbottom`/`set_bgcolor`/`set_border_color`, `line.set_xy1`/`set_xy2`/`set_color`/`set_width`, and `label.set_xy`/`set_text`/`set_textcolor`/`set_tooltip`/`set_size`;
  - when hidden: one hide path with na coordinates or transparent colours (verify once).
- Keep the `dB`/`dLn`/`dLb` pools for variable-count objects.
- Table: overwrite cells with `table.cell` instead of `table.clear` every tick, and clear only rows past the previous row count (`var int lastRows`).
- [B-corr] P3: the absolute per-tick saving is tiny (§1.6), and tooltip persistence is unverified.
- **Risk.** Moderate: stale-object bugs on style switches.
- **Effort.** M.

### PENG-8 (P3, S→M, robustness) · Far anchors [A✓, B-corr value; B-new cheap variant]
1. **Cheap variant (verify once in the editor).** The limitations page says the `time` series "can reference up to 10,000 bars", but `max_bars_back()` is capped at 5000.
   - Replace line 37 with an early-bar reference that sizes the buffer (RE10143.md, "Use the larger historical reference on early bars"): `int tBuf = time[barstate.isfirst ? 9999 : 0]`.
   - Raise `f_x` to `bar_index − 9999`.
   - If the editor raises an error, revert.
2. **Full variant (M).** A's time-anchoring with `int anchorT` on `Level`/`Ext`/`Zone`, `xloc.bar_time` drawings, and `time(timeframe.period, bars_back = -extBars)` for the right edge (time.md:298).
- [B-corr] Low visible value: the clamp affects only anchors more than 4,999 bars back, which are off screen (§1.5).
- **Evidence.** Mechanism strong; value weak.

---

## 5. Endorsed fixes from the overhaul and sibling studies (engineering-validated by B)

- **struct-F2 / rp-bias-done (bias at HTF close, P1 in the overhaul).**
  - The patch appends the unshifted `bias, ibias` to each structure tuple and reads them only when `barstate.isconfirmed and time_close == time_close(f_tfSafe(tf))`.
  - B's validation:
    1. On historical bars, `lookahead_on` without an offset returns the HTF bar's *final* value on every chart bar of that period. Reading it only on the chart bar that closes the HTF bar is legitimate, because the HTF bar is complete at that close.
    2. In realtime, the closing tick of that chart bar carries the final HTF value. Non-closing ticks keep the `[1]` value, so nothing flickers.
    3. The `==` comparison returns false on na (type_system.md), so holidays and gaps fall back to `[1]`.
  - Tuple total: 52 → 58 ≤ 127. **Non-repainting is preserved.**
  - Recommendation: apply it to the table *and* `drawD`. The overhaul's rp-bias-done variant does both.
- **pot-bump-floor-guard:** `k := math.floor(math.min(float(NB), math.max(0.0, x) / bStep))`. A correct clamp-before-floor that removes a theoretical negative loop bound.
- **perf-1:** Clean-mode last-bar gating. It supersedes A's PENG-2 step 4.
- **COMP-2 (alerts v2) and COMP-9 (output contract plus screener).** Engineering notes:
  - keep the 5 existing plots first;
  - each `alertcondition` uses one plot count;
  - the screener needs the PENG-2 merge (≤ 5 requests).
- **calib_ml / quant_pot (Brier and reliability of the displayed PoT).** They need `xPoT` per trial; PENG-6 exports it.

### Considered and not proposed
- **Switching to TradingView's same-bar rule** (A's PENG-9 core). Measured worse (§2.1).
- **Lazy iFVG drawing.** Negligible gain (G9).
- **`input.enum()` for the eight string dropdowns.** Typo safety only; do it inside the PENG-1 edit if convenient. Enum declarations must precede their inputs.
- **Wrapping the 1H request (981–982) in `if needVP`.** `usePathVP` is on by default, so needVP is usually true. Whether a never-executed dynamic request skips its data load is undocumented.
- **`behind_chart = false`.** The default is correct.
- **`varip` live-touch latches.** They would break reload parity (repainting.md, varip).
- **Pine Screener outputs** beyond COMP-9.
- **`once`, UDT `sort_field`, `text_formatting`, integer text sizes, tables in the bottom panel (Sept 2026).** Available, with no forecasting gain. Integer label sizes could fine-tune the Clean label.

---

## 6. Compile-safety notes for implementers (doc-grounded)
- `display` is `const plot_display`: write the literal `display.none` in each call. `active` takes an input bool (input.md:27–28).
- `calc_bars_count` is a const int in `indicator()` and a simple int in `request.*()` (core.md:183).
- `max_bars_back(var, num)`: `num` is a const int ≤ 5000 (core.md:259–270). The declaration's `max_bars_back` is a const int from 0 to 5000.
- `chart.is_standard` is a simple bool. `ticker.new(prefix, ticker, session)` returns a simple string when its arguments are simple (ticker.md:167).
- `time(timeframe, bars_back = -n)` takes n from 1 to 500. `time_close(timeframe)` is valid with one argument (time.md:290–392).
- `log.info(formatString, args…)` takes series int, float, bool, string and arrays of them (log.md).
- Tuple elements across all requests ≤ 127; unique requests ≤ 40, or 64 on Ultimate; the Pine Screener allows ≤ 5 requests.
- Lazy `and`/`or`: never put `ta.*` or a history-dependent UDF on the right-hand side of a condition; hoist it.
- Loops: `to_num` is re-evaluated every iteration. Guard `0 .. size − 1` loops, and never mutate the iterated collection inside `for…in`.
- Plot counts: a plot whose `color` is a *series* uses 2 counts (limitations.md). Keep new plot colours simple: `cAbove` is simple.
- Pine Logs: 10,000 historical messages. Gate `log.*` calls.

---

## 7. Sources

**Official (local mirror `scratchpad/docsrc/jabez4jc_pinescriptv6/`, mirrored from tradingview.com/pine-script-docs):**
- Limitations: https://www.tradingview.com/pine-script-docs/writing/limitations/ (writing_scripts/limitations.md)
- Profiling and optimization: https://www.tradingview.com/pine-script-docs/writing/profiling-and-optimization/
- Debugging (Pine Logs limits): https://www.tradingview.com/pine-script-docs/writing/debugging/
- Other timeframes and data: https://www.tradingview.com/pine-script-docs/concepts/other-timeframes-and-data/
- Execution model: https://www.tradingview.com/pine-script-docs/language/execution-model/
- Bar states: concepts/bar_states.md. Repainting (dataset variations): https://www.tradingview.com/pine-script-docs/concepts/repainting/
- Inputs: https://www.tradingview.com/pine-script-docs/concepts/inputs/; reference/input.md
- Alerts (mirror image, frequencies, placeholders): https://www.tradingview.com/pine-script-docs/concepts/alerts/
- Strategies, broker emulator: concepts/strategies.md
- Non-standard charts data: concepts/non_standard_charts_data.md. FAQ, real OHLC on HA: https://www.tradingview.com/pine-script-docs/faq/general/
- Migration to v6: https://www.tradingview.com/pine-script-docs/migration-guides/to-pine-version-6/
- Release notes (Oct 2026 inline alignment; Sept 2026 bottom-panel tables; Aug 2026 `once`; Oct 2025 `timeframe_bars_back`; Jul 2025 `active`; Mar 2025 dynamic `for`; Feb 2025 scope limit; Nov 2024 v6; Oct 2024 `behind_chart`; Aug 2024 `ticker.new` backadjustment/settlement; May 2024 `calc_bars_count` and Profiler; Mar 2024 `time()` `bars_back`): https://www.tradingview.com/pine-script-docs/release-notes/
- Error pages: CW10026, CW10003, RE10143, RE10139 (errors/)
- Reference: core.md (`indicator`, `max_bars_back`), chart.md, ticker.md, time.md, syminfo.md, log.md, constants.md (`display.pine_screener`), input.md

**TradingView help (via WebSearch summaries; direct fetch is blocked by the session's network policy):**
- The impact of data repainting on alert calculation: https://cn.tradingview.com/support/solutions/43000773984
- Script gives different results after refreshing (repainting): https://tradingview.com/support/solutions/43000478429-script-or-strategy-gives-different-results-after-refreshing-the-page-repainting
- Calculation takes too long to execute: https://in.tradingview.com/support/solutions/43000579793
- Pine Screener requirements and limitations: https://in.tradingview.com/support/solutions/43000742437 and https://in.tradingview.com/support/solutions/43000742436
- How to export chart data: https://www.tradingview.com/support/solutions/43000537255-how-to-export-chart-data/
- "Plan Limit Timer" library (third-party plan time limits): https://www.tradingview.com/script/lX5FPZPe-Plan-Limit-Timer/

**Third-party:**
- LuxAlgo PineTS (README, CHANGELOG 0.14.0, docs): https://github.com/LuxAlgo/PineTS; local clone at `study/pine_eng_tools/pinets`
- MultiCharts, intra-bar price movement assumptions (the same open-proximity convention): https://www.multicharts.com/trading-software/index.php/Intra-bar_Price_Movement_Assumptions
- PineCoders FAQ, avoiding repainting with security: https://www.tradingview.com/script/cyPWY96u-How-to-avoid-repainting-when-using-security-PineCoders-FAQ/
- Pineify, chart data export: https://pineify.app/tradingview/workflows/export-chart-data
- LuxAlgo blog, slow Pine scripts: https://www.luxalgo.com/blog/5-causes-of-slow-pine-scripts-on-tradingview/
- Look-ahead anecdote: https://dev.to/guardlabs_team/the-backtest-that-showed-400-how-look-ahead-bias-lies-5f13

**Own replications [B-new]:**
- `study/pine_eng_b_tools/intrabar_order.py` and `intrabar_order_out.txt` (§2.1a)
- `study/pine_eng_b_tools/intrabar_race.py`, `intrabar_race2.py` and the matching `*_out.txt` files (§2.1b)
- `study/pine_eng_b_tools/lookahead_leak.py` and `lookahead_leak_out.txt` (§2.2)
- Data: `study/amt_data/cme/{ES,NQ,YM,RTY,GC,CL}` 1-minute (2026-01-20 to 2026-04-15) and 1-hour (2025-03 to 2026-04)

**Project cross-references:**
- `dev-notes/runs/overhaul-r1-findings.md` and `overhaul-r1-journal.jsonl` (TE1, VIS-statusline-inputs, ux-statusline-inputs, perf-1, struct-F2, rp-bias-done, pot-bump-floor-guard, struct-F3, TE2)
- `study/competitors.final.md` (COMP-1, COMP-2, COMP-9), `study/calib_ml.final.md` (§1.32–1.33), `study/quant_pot.final.md`

---

## Appendix A: corrections log (B vs A)

| # | A's claim | B's finding | Effect |
|---|---|---|---|
| 1 | PENG-9: adopt TradingView's open-proximity rule in `f_step` | Measured: the colour rule is right 88% vs 81% (extremes) and wins 14 of 15 race configurations (§2.1) | PENG-9 rewritten: keep the rule, add an AMBIG counter |
| 2 | Tuple merge "−33%" | That figure is the docs' 9→1 demo; the engine's merge is 2→1 | Gain unquantified; the merge is still worth it for the screener cap |
| 3 | Total budget "20 s / 40 s (older official text)", graded moderate | Current docs give no numbers; the source is third-party | Graded weak |
| 4 | Keep the global `max_bars_back = 500`; "saves memory only" | The reference says it "can substantially increase memory use" and hurt performance, and recommends targeted calls | G6 present → partial; Profiler A/B lever in PENG-2 |
| 5 | `active` map: `obQMin ← useOB or useBRK`; `priorM ← Empirical`; `trackAge ← showIFVG or useBRK`; `accView ← Terminal` | `obQMin` is read only for OBs; `priorM` feeds `f_potBase` (the ledger); `trackAge` feeds the iFVG alert; `accView` gates the ledger | Corrected map in PENG-1 |
| 6 | PENG-3 uses `tkr` "in all five requests" | There are six request calls (923, 924, 925, 939, 981, 982) | Corrected |
| 7 | HA ledger "grades fiction" | Wicks are approximately real; the close-based rules are strongly distorted | Wording: "distorted" |
| 8 | PENG-2 steps 3–4 (lazy iFVG, Clean gating) | Lazy iFVG saves about 1k pairs per load (negligible); Clean gating is already the overhaul's perf-1 | Dropped or merged |
| 9 | PENG-5 at P2 on cost grounds | 8 objects per tick is a tiny absolute cost; the tooltip claim is unverified | P3 |
| 10 | PENG-8 at P3 with no cheap path | The clamp is invisible in practice; a cheap 10k `time` buffer variant exists (verify) | P3, cheap variant first |
| 11 | `f_raceH` "up to 400 terms" per tick | 12–70 terms inside maxATR (overhaul audit) | Wording |
| 12 | G10 "missing" | Delete-and-recreate is functionally correct under rollback | missing → partial |
| 13 | Not covered | Server-side alert divergence and path dependence, the Pine Screener cap, Pine Logs cap, compile-time ban, `ticker.new` futures defaults, bias freshness at HTF close, run-dependent ids | New concepts 1.20–1.22, G31–G35, PENG-10, PENG-12 |
| 14 | COMP-1 (sibling): "the four LVN inputs: `active = showLVN`" | `lvnHours` and `lvnRows` also feed `f_pathVol` | Use `showLVN or usePathVP` for those two |

## Appendix B: replication commands
```
python3 -I study/pine_eng_b_tools/intrabar_order.py study/amt_data/cme
python3 -I study/pine_eng_b_tools/intrabar_race2.py study/amt_data/cme
python3 -I study/pine_eng_b_tools/lookahead_leak.py study/amt_data/cme
```
(Paths are relative to `scratchpad/brief/`. pandas 3.0.5 and numpy 2.5.3. The `lookahead_leak` day boundary is an 18:00 offset applied to the file's timestamps; the leak comparison does not depend on it.)
