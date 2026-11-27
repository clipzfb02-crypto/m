# I1 · DOL lineage inspection: DOL Engine v2, the early DOL Engine, Liquidity Flow Pro

Phase 1 workspace inspection, assignment I1. Written 2026-11-27. Read-only: no source file was modified.

---

## 0. Scope, sources and honesty notes

**Files read in full this session (every line):**
- `/home/user/m/apex/legacy/dol_engine_v2_00a405a.pine` (2448 lines).
  - `diff -q` shows it is byte-identical to the frozen baseline `<scratchpad>/brief/baseline_v2.pine`. All v2 line numbers below are therefore valid for both files.
  - The live `/home/user/m/indicators/dol_engine.pine` is also 2448 lines today. I did not use it, because a bug-fix pass may be editing it.
- `/home/user/m/apex/legacy/DOL_Engine_early.pine` (2548 lines) and `DOL_Engine_early.README.md`.
- `/home/user/m/apex/legacy/liquidity-flow-pro.pine` (1615 lines), `liquidity-flow-pro.README.md` and `liquidity_model_sim.py` (645 lines).
- `/home/user/m/dev-notes/HANDOFF.md`, `/home/user/m/dev-notes/runs/overhaul-r1-findings.md`, `/home/user/m/dev-notes/brief/APEX_ULTIMATE_SPEC.md`, `CONTEXT.md`, `tradeaxis_description.md`, `/home/user/m/README.md` and `/home/user/m/apex/legacy/README.md`.
- `/home/user/m/dev-notes/brief/reference_look.png` (viewed). It shows Gold futures 5m on COMEX, a "Timeframe | Bias" table (D BULLISH, 4H BULLISH, 1H BEARISH), one dashed green zone with a glowing core line, a dashed tether to a dark "Target: BEFVG / PoT: 70.1%" label, and two dark-green iFVG boxes.

**Study reports read (executive summaries plus the sections cited):** `bias_dol`, `ict_liq`, `quant_pot`, `calib_ml`, `skeptic`, `ict_struct`, `smc_impl`, `ict_pd`, `pine_eng`, `ux_design`, `ict_time` and `amt_profile` (`<scratchpad>/brief/study/*.final.md`).
- `STUDY.md` and `ROADMAP.md` do not exist yet.
- `/home/user/m/apex/research/WORKSPACE_INSPECTION.md` does not exist.
- Every study number below is quoted as the report states it, with its sample and dataset. I did not re-run the study's replications.

**What I ran:**
- `python3 -I liquidity_model_sim.py`: 15/15 scenario checks pass, and the random-walk statistics reproduce the README (§4.9).
- A declared-but-unused identifier scan over the three `.pine` files (`<scratchpad>/i1/unused.py`). Hits on UDT fields were false positives (they are accessed as `.field`) and are excluded.
- `grep` counts of inputs, request calls, alerts and loops.

**What I could not verify (marked "unverified" where used):**
- **Compile status.** None of the three files was compiled on TradingView: no compiler is available. So compile status is unverified for all three.
  - The early README says "0 errors and 0 warnings on TradingView's own Pine v6 compiler".
  - `CONTEXT.md` lists constructs "already verified as compiling" from earlier sessions.
  - Both are reported claims.
- **The early engine's research is not reproducible from the repository.**
  - Its origin branch, `origin/claude/quirky-volta-vgbrq5`, contains only `DOL_Engine.pine`, `README.md` and agent config files. No Python replica, data or results.
  - Every early-engine number below is therefore labelled "README claim, scripts absent, not re-run".
- I did not run the pynescript syntax checker; my role does not call for it.

**Evidence classes:**
- **E**: established market mechanics or exchange or platform documentation.
- **A**: academic or statistical evidence.
- **D**: discretionary practitioner theory.
- **C**: contested or unsupported by tests.

Grades are strong, moderate, weak or none. A score is never a probability.

---

## 1. Executive verdict

1. **v2 is the right base, by a wide margin.** It has the most complete liquidity map and the cleanest non-repaint engineering. Its probability mathematics is verified correct by the study:
   - `f_pot`, `f_race` and `f_raceH` match Monte Carlo;
   - the reflection identity holds on real CME bars (`quant_pot`).
   
   Its accuracy ledger uses the right kind of baseline: distance-matched, leak-free and prequential (`skeptic`). Its weak part is the *scoring and selection layer*. Almost every lever there is either unsupported by tests or wrong-signed.
2. **The early engine (README "DOL Engine v6") is where the data spoke first, and the data said no.** Its own README reports (scripts absent, not re-run):
   - liquidity type, HTF bias, sweeps, premium/discount, confluence and the DOL score had no out-of-sample value for touch probability or side;
   - the DOL side was taken first 59.3% of the time, exactly the distance-only value;
   - no execution mode was reliably profitable after costs. Sweep Reversal: 1,350 trades, 38% win, −0.06R per trade. With the order-flow filter: 357 trades, +0.09R, positive in one data window only.
   
   The later study replicated every one of these conclusions independently, on its own data. That convergence is the most important lesson of the lineage.
3. **Liquidity Flow Pro (LFP) is not a DOL engine.** It turns a pool map into a buy-side/sell-side share.
   - Its Video style presents that share as "▲ UP xx% / ▼ DOWN yy%" and tells the user that the bigger number is "the more likely direction". No test supports this. On driftless random walks the reading flips side about every 68 bars and reads "EXTREME" on 7.35% of bars (sim re-run, §4.9).
   - Its *lifecycle primitives* are the best of the three. Keep:
     - the three-way commit outcome: sweep (trade beyond and close back), taken (close beyond) or test (approach);
     - bounded-span equal-level clustering with identifiable members;
     - discarding the first partial calendar period;
     - gating calendar levels by chart timeframe;
     - volume-quality detection;
     - a LOW-DATA shrink to neutral.
4. **The strongest liquidity and target logic for APEX is a hybrid. No single engine supplies it.**
   - From v2: the source set, the external registry, exact anchoring, the probability maths, the empirical surface and the ledger.
   - From LFP: the lifecycle and clustering primitives and the data-quality handling.
   - From the early engine: PMH/PML, auto timeframe selection, time-anchored drawings, the intraday volatility clock, the Brier-skill scorecard, commitment ("lock until hit") as an option, and cost-aware tradeability.
   - Geometry is the backbone of target selection: distance, volatility and the clock. Every ICT feature starts neutral and must earn weight on the user's chart (`skeptic`, `calib_ml`, `ict_liq`).
5. **v2 maps to APEX spec sections 3-18 as follows:**
   - **strong:** §4 liquidity mapping and §10 statistics;
   - **partial:** §3 structure, §5 ICT zones, §11 MTF, §15 calibration, §16 risk, §17 clean chart and §18 alerts;
   - **missing:** §4.8 (destination vs reversal), §6 Wyckoff/AMT, §7 VWAP/RVOL, §8 trend/momentum, §9 regime classification with hysteresis, §12 intermarket, §13 the decision engine and BUY/SELL states, and §14 the forward forecast path.
   
   See §7.
6. **Defect load of v2:**
   - The overhaul audit's **49 findings** are 18 P1 and 31 P2. Only 3 are verified and 46 are unverified. They collapse to about 35 distinct defects (§2.9).
   - The study adds about 12 defects the audit missed. Examples: the raid→reversal sign (line 1581); the volume-profile path cost that is wrong-signed; self-confluence; a breaker definition that reproduces 11-24% of template breakers; and biased ETA, heat and EV readouts.

---

## 2. DOL Engine v2 (`dol_engine_v2_00a405a.pine`, 2448 lines): full inventory

### 2.1 Purpose and design
- An original Pine v6 overlay that implements the *feature set* of the invite-only "TradeAxis DOL" (`tradeaxis_description.md`) without its code or branding.
- It pools liquidity targets, scores each one 0-100 on confirmed bars, and tracks the best one as the active Draw on Liquidity (DOL) zone.
- **Pool contents:**
  - chart, STF and HTF swings;
  - PDH/PDL and PWH/PWL;
  - Asia, London and NY-AM session highs and lows;
  - chart and HTF FVGs, order blocks and breakers.
- **Displays:**
  - a live Probability of Touch (PoT);
  - a "Timeframe | Bias" table;
  - iFVG boxes;
  - an accuracy ledger that grades its own picks against a distance-matched random level.
- **Two display styles:**
  - **Clean** (default) reproduces the reference screenshot;
  - **Terminal** is a full HUD and accuracy panel.

### 2.2 Architecture and section map

| Lines | Section | Contents |
|---|---|---|
| 1-37 | Header | `indicator(..., max_bars_back = 500, max_boxes/lines/labels = 500)`, `max_bars_back(time, 5000)` (37) |
| 42-237 | Inputs | 16 groups, 104 inputs (§2.5) |
| 240-309 | Theme and derived constants | Six themes; Classic is the default. `NB = 60` bins, `wSum`, `H = min(potH, 450)`, `delivAt`, `bStep`, `clean` |
| 317-395 | Types | `Level` (317), `Zone` (351), `Ext` (365), `Trial` (375) |
| 400-609 | Pure helpers | Maths, naming, timeframe helpers, table cells (§2.4.1) |
| 615-696 | Level methods | Geometry, touch rule, bookkeeping, `evaluate` (the score) |
| 708-869 | Series-state functions | `f_structure`, `f_htfFvg`, session and period trackers |
| 874-1017 | Series | ATR, pivots, coil/inducement, displacement, FVG raw, PoT inputs, 6 request calls, key levels, anchors, killzones, 1H volume feed |
| 1022-1079 | State | Pool, registry, trackers, selection state, VP cache, empirical surface, ledger stats |
| 1084-1499 | State helpers | Merging, anchoring, registry, stacking, ghosts, empirical PoT, invalidation, calibration, profile, ledger |
| 1504-1513 | Live sweep | Intrabar check against the committed target |
| 1518-2057 | Engine | Runs on confirmed bars only. Steps 0-20 (§2.4.6) |
| 2062-2074 | Live readouts | `activePoT`, `dolShown`, announcement gating |
| 2079-2093 | Alerts | 4 `alert()` calls and 4 `alertcondition`s |
| 2098-2286 | Rendering | On the last bar, redrawn every tick |
| 2291-2433 | Panel | Clean table and Terminal panel |
| 2438-2448 | Data window | 5 plots with `display.data_window` |

### 2.3 Types
- **`Level` (317-348).**
  - `kind`: 0 BSL, 1 SSL, 2/3 bull/bear FVG, 4/5 OB, 6/7 breaker.
  - `side`: +1 above price, −1 below.
  - `src`: 0 chart, 1 STF, 2 HTF, 3 Asia, 4 London, 5 NY AM, 6 PD, 7 PW.
  - Geometry: `price`, `top`, `bottom` and the original `oTop`/`oBot`.
  - Times: `anchorBar`, `bornBar`, `createdBar`.
  - Bookkeeping: `hlMult`, `eqCount`, `tests`, `lastTest`, `stack`, `inner`, `prom`, `qual`, `fill`, `coil`, `induce`, `maxAway`.
  - Cached pillars: `prox`, `fresh`, `conf`, `dens`, `draw`, `mult`, `score`.
- **`Zone` (351-361).** FVG/OB trackers and active iFVGs: `top`, `bottom`, `dir`, ages, `closesIn`, `qual`, `tookLiq`, and the drawing handles `bx` and `ce`.
- **`Ext` (365-372).** The external registry: price, side, `src`, anchor, born, prominence, `hlMult`.
- **`Trial` (375-395).** One ledger record: target edge, invalidation, risk, entry, ATR, bar, baseline `pBase`, race `pRace`, R:R, distance, MAE, bars, race outcome, status, R outcome.

### 2.4 Calculation inventory

#### 2.4.1 Pure helpers (400-609)

| Lines | Function | Computes |
|---|---|---|
| 400 | `f_clamp` | Clamp |
| 404 | `f_x` | Clamps a past x-coordinate to `bar_index − 4999` (inside the time buffer) |
| 408-418 | `f_erfcLog`, `f_erfc`, `f_phi` | Numerical Recipes erfc (fractional error < 1.2e-7) and the normal CDF |
| 421 | `f_expPhi` | e^e·Φ(b) in log space, to prevent overflow in the reflection term |
| 434 | `f_pot(dist, sig, mu, h)` | One-barrier first passage with drift: Φ((μh − d)/σ√h) + e^{2μd/σ²}·Φ((−μh − d)/σ√h), capped at 0.95 |
| 447 | `f_race(a, b, sig, mu)` | Infinite-horizon two-barrier race. Gambler's ruin b/(a+b) when driftless, closed form with drift |
| 466 | `f_raceH(a, b, sig, mu, h)` | P(+a first AND within h): `f_race` minus the eigen-expansion flux after h, with up to 400 terms |
| 484-489 | `f_logit`, `f_sigm` | Logit and sigmoid |
| 492 | `f_wilson` | Wilson 95% interval |
| 506 | `f_tierW(src)` | Source tier: chart .25, STF .45, HTF .65, Asia .55, London/NY .60, PD .80, PW .92 |
| 518-549 | `f_levelName`, `f_shortName`, `f_grpName` | Labels: PDH, ASIA H, HTF BSL, BEFVG, BUOB, … |
| 551-560 | `f_meter`, `f_signed`, `f_tfLabel` | Formatting |
| 564 | `f_tfSafe(tf)` | Returns the chart timeframe when the requested timeframe is lower, so nothing is requested below the chart |
| 567 | `f_tfRatio` | HTF seconds ÷ chart seconds |
| 570 | `f_row` | Price → profile row, clamped. The clamp causes the path-cost bug, §2.9 |
| 573-594 | `f_pos`, `f_biasTxt`, `f_biasCol`, `f_kzName` | UI |
| 597 | `f_kzAff(k, src)` | Killzone affinity: London ×1.20 on Asia pools and ×1.10 on PD; NY AM ×1.20 on London, ×1.15 on PD and ×1.05 on Asia; NY PM ×1.15 on NY and ×1.10 on PD |
| 604-608 | `f_cell`, `f_cellC` | Table cell writers (Terminal and Clean) |

#### 2.4.2 Level methods and the score (615-696)
- **`nearEdge`, `distance`, `isLiquidity`, `isArray`, `tier`, `grp`, `tag` (615-646).** Geometry and labels.
- **`touched` (623).** Pools are swept only on a strict trade-through (`hi > bottom` / `lo < top`). Arrays count as reached on a touch (`>=`, `<=`).
- **`track` (650).** Updates `maxAway` (how far price has left the zone, in ATR). It counts a *test* when a bar comes within `testATR` (0.30) of a pool without taking it, at most once per 3 bars, and resets `mult`.
- **`evaluate` (661-696), the score.** It is `score = clamp(100 × raw × mult, 0, 100)`, with `raw = (25·prox + 10·fresh + 15·conf + 20·dens + 30·draw) / Σw`. The pillars:
  - **prox (662-667).** Zero beyond `maxATR` (10). Otherwise it is (0.5·lin + 0.5·reach) × (0.30 + 0.70·taper), where:
    - lin = 1 − dATR/maxATR;
    - reach = `f_pot(dist, σ, μ·side, potH)`/0.95. *It includes the 50-bar drift*;
    - taper = min(1, dATR/0.5).
  - **fresh (668-673).** age = (bar − bornBar)/hlMult.
    - Pools: (0.35 + 0.65·(1 − e^(−age/(0.25·HL)))) × 0.5^(age/(4·HL)), so pools "mature, then decay".
    - Arrays: 0.5^(age/HL). HL is 150.
  - **conf (674-680).** min(1, 0.35 × the number of anchors inside the zone ± 0.35 ATR). The anchors are PDH, PDL, PWH, PWL, daily EQ, the midnight, London and NY opens, and the HTF EQ.
  - **dens for pools (681-685).** x = 0.9·eq + 0.45·stack + 0.35·min(tests, 6) + 0.8·min(1, prom/3) + 1.2·tier, then dens = 0.60·(1 − e^(−x)) + 0.25·coil + 0.15·induce. Inner pools of a stack get `mult ×0.70`.
  - **dens for arrays (686-690).** min(1, 0.5·qual + 0.3·coil + 0.2·induce + 0.2·[HTF]). Also `mult × (1 − 0.5·fill)`. Origin lockout: `mult ×0.25` while age < 3 bars or `maxAway` < 1 ATR, and *only for src 0*.
  - **draw (691-693).** 0.5 + 0.5·D·side. When D·side ≤ −0.35, `mult ×0.50` (the counter-draw penalty).
- **Multipliers folded in at step 17 (1940-1948):** killzone affinity, the per-family calibration `f_calMult` (0.8-1.2), and the volume path ×1.10 (thin) or ×0.85 (thick).

#### 2.4.3 Series-state functions (708-869)
- **`f_structure(len)` (708-782).** Runs inside `request.security` on HTF, STF and EXE. It returns, all `[1]`-shifted:
  - `bias`: swing structure. A BOS re-arms the protected extreme, and a CHoCH needs a body close through the protected level;
  - `ibias`: internal structure. It flips on any body close through the last swing;
  - the dealing range `rngH/rngL`, the last pivots and their print times, `hValid/lValid` (the pivot is unswept on its own timeframe), and `protH/protL`.
- **`f_htfFvg` (785-796).** The FVG completed on the last *closed* HTF bar: direction, top, bottom, quality and the HTF time. There is no middle-candle direction check and no quality gate (PD-5).
- **`f_sessOpen` (798).** The session's first open.
- **`f_rangeTrack(isNew)` (807).** The previous calendar period's high and low and their exact print bars. It has no partial-period guard (rp-partial-pwh).
- **`f_sessTrack` (835).** Session high and low, emitted on the first bar after the session ends. Membership is tested at bar *open*.
- **`f_changed` (865).** Unused. **`f_changedT` (868).** Used.

#### 2.4.4 Series (874-1017)
- **Volatility:** `atr` (14), `atrSlow` (200) and `atrE = max(atr, atrSlow)` (878), used for the eject and range gates.
- **Swings:** chart pivots `ph`/`pl` (`pivLen` 5). Range extremes for prominence (881-884).
- **Coil (888-891):** `overlap = Σrange/range` over 20 bars, mapped to [0, 1] between overlaps of 2 and 6. **Inducement (892-895):** wick through a 5-bar extreme that closes back inside, counted over 20 bars ÷ 3.
- **Displacement (898-904):** body ≥ 1.2 ATR with a body ratio ≥ 0.6, or a two-candle leg ≥ 1.8 ATR.
- **Chart FVG raw (907-912):** gap ≥ 0.15 ATR, plus a base quality term from the middle candle.
- **PoT inputs (915-920):** σ = stdev(Δclose, 50); μ = 0.5·SMA(Δclose, 50), *live*. Forward-window highest and lowest over H.
- **MTF (923-936):** three `f_structure` calls (HTF, STF, EXE), then booleans for new HTF/STF pivots.
- **HTF FVG (939-942):** enabled only when the chart is below the HTF.
- **Key levels (945-961):** day and week trackers and the session trackers. Sessions are enabled only on intraday charts at or below 1H.
- **Anchors (964-968).** **Killzones (971-976):** `kz` index; `hystEff = hyst × 2` outside killzones.
- **1H volume feed (979-1015):** `request.security("60", [o, h, l, c, v, t][1])` on charts at or below 1H; `request.security_lower_tf("60")` on closed bars above 1H. A rolling 120-hour store. `tfWarn` (1017).

#### 2.4.5 State helpers (1084-1499)

| Lines | Function | Computes |
|---|---|---|
| 1084 | `f_newLevel` | Builds a Level; side from kind |
| 1090 | `f_findLiq` | Nearest same-kind pool within the tolerance |
| 1111 | `f_mergeAt` | Folds a print into a pool. Counts an EQ unless it is the same print; moves the level outward and carries open ledger records with it; upgrades the tier |
| 1133 | `f_mergeLiq` | find + merge |
| 1141 | `f_anchorScan` | The nearest candle that printed the level, and whether a later candle already traded through it |
| 1165-1187 | `tfOpenBar` map, `f_recOpen` | Chart bar on which each HTF/STF bar opened (up to 4000 entries) |
| 1191 | `f_barAtTime` | Chart bar containing time t: map lookup, else binary search over up to `anchorMax` bars, else a clock estimate |
| 1211 | `f_pushExt` | Adds an external level only if price is still on its side; dedupes and upgrades the tier |
| 1230 | `f_stackSide` | Sorts one side by price. Pools within 0.75 ATR form a stack: the outermost is the draw, the inner ones are flagged `inner` |
| 1253 | `f_ghost` | Dotted ghost box and label, up to 12 |
| 1265-1278 | `f_bump`, `f_surv` | Survival counts of H-bar excursions in 0.25-ATR bins up to 15 ATR. `f_bump` can overflow `int` (pot-bump-floor-guard) |
| 1284 | `f_empPoT` | Empirical P(reach d ATR within H) by side and HTF regime. Needs n ≥ max(150, 20H), otherwise pools across regimes. Beyond the grid it falls back to analytic |
| 1303 | `f_potModel` | Displayed PoT. Analytic with drift; when Empirical, a blend with nEff = n/(0.6H) against `priorM` (30) pseudo-observations; capped at 0.95 |
| 1314 | `f_potBase` | The ledger baseline: the same blend, driftless, clamped to 0.01-0.99 |
| 1325-1338 | `f_reachD`, `f_reachClass` | Distance at which the empirical reach falls to q; CORE, EXTENDED or STRETCH |
| 1343 | `f_invalidation` | Invalidation beyond the nearest opposing pool, else the EXE swing, else 1.5 ATR. Risk is at least 0.25 ATR. R:R, and a finite-horizon race P(target first) *with drift* |
| 1367 | `f_raceAdj` | Shifts the race on the logit scale toward the ledger's observed first-touch rate, with 20 pseudo-observations. Ungated |
| 1376 | `f_calMult` | Per-family multiplier ((k+2)/(e+2)) ÷ ((K+2)/(E+2)), clamped to 0.8-1.2 once n ≥ 10 |
| 1384 | `f_profile` | 1H volume profile: 60% of volume spread over the range and 40% over the body, via a difference array, then [1, 2, 1] smoothing |
| 1417 | `f_pathVol` | Mean profile volume between two prices ÷ the profile mean |
| 1426 | `f_openTrial` | Opens a ledger record: edge, invalidation, risk, `pBase`, `pRace`, R:R, distance |
| 1434 | `f_step` | One bar of a record: hit (strict for pools, touch for arrays), stop, open-gap handling, bar-path order by candle colour, MAE, expiry at H, R outcome |
| 1461 | `f_book` | Books a record: residuals in 2H blocks (cluster variance), per-family and ALL counts, rolling 50, hits-only time-to-hit and MAE, race stats |

#### 2.4.6 Engine steps (confirmed bars only, 1518-2057)

| Step | Lines | What it does |
|---|---|---|
| 0 | 1527-1532 | Empirical surface: the H-bar window that began H bars ago is complete, so bump the up and down excursions under that bar's HTF regime |
| 1 | 1534-1547 | Decays `liqEvt`, records displacement and chart BOS bars |
| 2 | 1549-1556 | Grades open ledger records *before* sweeps delete their levels |
| 3 | 1558-1589 | Pool upkeep: `track`, sweeps, partial fills of non-active arrays (cropping at CE by default), ejection beyond 15 slow ATR. **Raid event (1580-1582):** a held raid counts +1 and a rejected raid −1, scaled by tier, added to `liqEvt` |
| 4 | 1591-1596 | The registry drops raided externals |
| 5 | 1598-1627 | FVG → iFVG on a close through the whole gap. Clean box, Terminal box with a CE line, capped at 8 |
| 6 | 1629-1644 | iFVG upkeep: deleted after more than 2 body closes inside, or on a close back through |
| 7 | 1646-1661 | OB → breaker: a close through a tracked OB *that took liquidity* creates a breaker Level |
| 8 | 1663-1750 | Order blocks on a chart-swing BOS: leg extreme within 20 bars, the last opposite candle within 5 bars, quality 0.4·legFVG + 0.3·tookL + 0.3·leg size, skipped if already revisited, pushed if q ≥ 0.40; breaker tracker if `tookL` |
| 9 | 1752-1776 | Chart swing pools: merged as EQ within 0.10 ATR, otherwise a new pool anchored by `f_anchorScan` |
| 10 | 1778-1822 | Externals → registry: HTF/STF pivots if unswept, PDH/PDL, PWH/PWL, session H/L. Prominence and `hlMult` = √(TF ratio). Eviction above 60 by tier × slow decay |
| 11 | 1824-1852 | Registry → pool when within 10 slow-ATR, merging into an existing pool or creating one. Runs on new entries or every 5 bars |
| 12 | 1854-1865 | HTF FVG → pool, only if price is outside it and within 15 slow-ATR (PD-1) |
| 13 | 1867-1889 | Chart FVGs: quality = base + gap size + BOS within 3 bars, halved for a wrong-colour middle candle. Pool if q ≥ 0.45. Every FVG goes to the inversion tracker |
| 14 | 1891-1898 | **Draw vector D** = (0.5·S + 0.2·M + 0.3·L)/1.0, with S = 0.5·htfBias + 0.3·stfBias + 0.2·exeIB, M = decayed displacement and L = `liqEvt`. `dirSide` uses gate 0.35. Flip event |
| 15 | 1900-1909 | Volume-profile cache rebuild with a prefix sum |
| 16 | 1912-1927 | Stack flags reset and recomputed per side |
| 17 | 1929-1948 | Score every level: anchors, family multipliers, killzone affinity, VP path, `evaluate` |
| 18 | 1950-1962 | Pool cap (40): drop the lowest score + 10·[external], never the active one |
| 19 | 1964-2035 | **Selection.** Draw-side first; counter-draw fallback if nothing on the draw side reaches `minScore` (35); counter-draw hold; challenger must lead by `hystEff` (×2 to flip sides) for 2 bars; HTF objective; ghosts; announcement pending until the PoT filter passes |
| 20 | 2037-2045 | Ledger: open one Trial per active target id after a 300-bar warm-up inside the calculation window |
| else | 2046-2057 | Before the calculation window: trim by distance − 3·tier − 0.5·EQ |

#### 2.4.7 Readouts, alerts, rendering, panel (2059-2448)
- **Live readouts.** `activePoT` (2066-2067) is `f_potModel` at the live close, forced to 0.95 after a live sweep. `dolShown` applies the PoT filter. `annNow` is evaluated at bar close.
- **Alerts.**
  - New target: bar close, 2079.
  - New iFVG: bar close, 2082.
  - Target swept: `freq_once_per_bar`, *intrabar*, 2084.
  - Draw flip: bar close, 2086.
  - Plus 4 `alertcondition`s (2090-2093).
- **Last-bar analytics (2111-2130).** Reach distances, median time-to-hit, the ETA scan, invalidation and `f_raceAdj`. They run every realtime tick, even in Clean (perf-1).
- **Rendering (2132-2286).** Deletes and recreates every drawing each tick. The pieces:
  - iFVG right edges;
  - candidate pool, HTF objective, secondary targets and reach bands;
  - the **Clean DOL** (2214-2226): a dashed box, a five-layer glow (widths 10, 7, 4, 2 and 1; white core at transparency 15), a dashed tether, and a "Target: CODE / PoT: x.x%" label with a pillar tooltip;
  - the **Terminal HUD** (2227-2248);
  - LVN zones (2251-2286).
- **Panel (2291-2433).**
  - **Clean:** "Timeframe | Bias", showing the swing bias, or the internal bias while the swing is 0, plus a timeframe warning row.
  - **Terminal:** bias, internal bias and premium/discount per timeframe; DRAW; TARGET; PoT; R:R, WIN≤H and EV; POOL; ACCURACY (hit %, Wilson interval, L50, EDGE z and verdict, bars-to-hit, heat, per-family rates, race stats).
- **Data window (2438-2448):** DOL price, score, PoT %, D, ledger hit %.

### 2.5 Inputs and defaults

There are 104 inputs: 20 bool, 8 color, 31 float, 23 int, 10 session, 9 string and 3 timeframe. 76 non-bool, non-color inputs print in the status line because `display.none` is never used (0 occurrences). That is about 411 characters of defaults (`ux_design`).

| Group | Inputs (defaults) |
|---|---|
| Trading Mode | Mode Day Trading (D/4H/1H); Swing W/D/4H; Scalping 1H/15m/5m; Custom 240/60/15; MTF pivot strength 3 |
| Engine | Calculation depth 5000; ATR 14 |
| Liquidity Sources | Pivot length 5; chart swings on; HTF+STF swings on; zone depth 0.20 ATR; EQ tolerance 0.10 ATR; stack window 0.75 ATR; test proximity 0.30 ATR; anchor scan 300 |
| Key Liquidity | PDH/PDL on; PWH/PWL on; sessions on (≤ 1H); Asia 2000-0000, London 0200-0500, NY AM 0930-1200 |
| Imbalances & Blocks | FVG on; HTF FVG on; min FVG 0.15 ATR; min FVG quality 0.45; OB on; OB window 20; min OB quality 0.40; breakers on; delivered at CE 50%; displacement 1.2 ATR |
| Scoring | Pool 40; max distance 10 ATR; eject ×1.5; min target distance 0.5 ATR; origin lockout 3 bars; must leave by 1.0 ATR; half-life 150; confluence tolerance 0.35 ATR; density window 20; weights proximity 25, freshness 10, confluence 15, density 20, draw 30; min score 35; hysteresis 4; adaptive calibration on; VP path cost on |
| Order Flow | D weights 0.50 structure / 0.20 displacement / 0.30 liquidity events; displacement half-life 12; liquidity-event half-life 24; direction gate 0.35; counter-draw ×0.50; off-killzone hysteresis ×2.0 |
| DOL Display | Style Clean; show DOL on; secondary targets 0; HTF objective off; invalidation off; reach bands off; candidate pool off; right extension 20; HUD Normal |
| Probability of Touch | Min PoT 0%; model Empirical; horizon 30; volatility lookback 50; drift weight 0.5; analytic prior 30 |
| Accuracy | Panel Compact; warm-up 300 |
| iFVG | Show on; max closes inside 2; max active 8; tracking window 500 |
| Volume Profile | LVN off; depth 120 1H bars; 48 rows; threshold 0.30 × peak; 2 per side |
| Ghost | Off; max 12 |
| Panel | Show on; Top Right |
| Sessions & Killzones | tz America/New_York; midnight 0000-0100; London open 0200-0300; NY open 0930-1030; killzones Asia 2000-0000, London 0200-0500, NY AM 0700-1000, NY PM 1330-1600 |
| Theme | Classic (others: Neon, Matrix, Ice, Mono, Custom), plus 8 custom colours (CW10026 warning on the four inline colour rows, `pine_eng`) |

### 2.6 Signal logic
v2 issues **no BUY or SELL signals**. Its events are:
- a new DOL target (bar close, after the PoT filter);
- a draw-direction flip (D crosses ±0.35 against the last side);
- a new iFVG (bar close);
- the active target swept (live, intrabar).

The "direction" a user reads is the side of the active DOL and the D readout. Both rest on D, which has no measured skill (§2.11).

### 2.7 Non-repaint status
- **`request.security`: PASS.** All five calls use `[1]`-shifted series computed *inside* the requested function, with `lookahead_on`: lines 782, 796 and 981, called at 923-925, 939 and 981.
  - `f_tfSafe` (564) never requests below the chart.
  - `request.security_lower_tf("60")` (982) is read only on `barstate.isconfirmed` (1000).
  - `pine_eng` re-checked this and calls it "sound. Do not touch". It measured why: a leaking daily read lifts a no-skill 1-ATR/10-bar win rate from 49.6% to 59.5% (6 CME futures, 1H, about 33k signals).
- **Pivots: PASS with a note.**
  - `ta.pivothigh/low` levels enter the pool at confirmation (`createdBar = bar_index`). The *drawing* is anchored left at the print candle (`anchorBar`), which is a visual reference and not a backdated decision.
  - MTF pivots arrive through `[1]` and `lookahead_on` and are anchored through `f_barAtTime`.
  - APEX must document "knowable at createdBar" (spec §3).
- **`barstate`: PASS with known lag.** The engine is gated by `barstate.isconfirmed` (1518). Deliberately live items:
  - the PoT readout (2066), which uses the live `potSig` and `potMu`;
  - the swept alert (2084);
  - the Clean label after a live sweep, which still reads "PoT 95%" (dol-F).
  
  The bias is one HTF candle stale when the last bar is confirmed: weekends, after hours (struct-F2, rp-bias-done). That is lag, not repaint.
- **Reload and alert parity risk (`pine_eng` PENG-10).** Learned state is cumulative over a window that starts at `last_bar_index − calcBars` (2038): `f_calMult`, `f_raceAdj` and the ledger. A reloaded chart, the server-side alert and Bar Replay can therefore pick different targets from the same prices. This is a repaint-like divergence APEX must bound.

### 2.8 Performance risks
- **Request calls: 6** (5 + 1 lower-TF). Three return 12-tuples, and 9 of those values are never read (§2.9).
- **History.** Levels, steps 0-15, are tracked on *every* historical bar. Only scoring, selection and the ledger are limited to the last 5000. On 1-minute charts with long histories this is the dominant cost. The `pine_eng` static estimate is 5-8×10⁷ primitive operations on 20k bars, "a few seconds"; it is unmeasured on TradingView.
- **Loops: 57 `for`, 6 `while`.** The heaviest:
  - `f_raceH`, up to 400 terms, twice per `f_openTrial` and on every realtime tick through `f_invalidation` (perf-1);
  - registry × pool merging every 5 bars, O(60 × 40);
  - `f_bump`, up to 61 per bar per side;
  - the OB and FVG leg scans, ≤ 26 history reads.
- **Per tick.** All DOL drawings and the table are deleted and recreated, and the last-bar analytics run even in Clean (perf-1, verified real).
- **Drawings.** Bounded: iFVG ≤ 8, ghosts ≤ 12, plus about 10 DOL objects per tick. `max_*_count` is 500.
- **Memory.** `max_bars_back(time, 5000)`; the `tfOpenBar` map holds up to 4000 entries.

### 2.9 Broken, duplicated and dead code

**Dead code (from the identifier scan):**
- `f_changed` (865-866) is never called.
- From the `request.security` tuples (923-925): `htfProtH`, `htfProtL`, `stfProtH`, `stfProtL`, `exePvH`, `exePvL`, `exePvHT`, `exePvLT`, `exeHV`, `exeLV`, `exeProtH` and `exeProtL` are destructured and never read.
  - `ict_struct` notes that `protH/protL` are exactly what ICT's dealing range needs (ICTS-4).

**Duplicated logic:**
- `f_potModel` (1303) and `f_potBase` (1314) repeat the empirical/analytic blend and differ only in drift and clamp.
- The iFVG right edge is updated twice: 1641-1644 on `tailBar` and 2145-2149 on `islast`.
- `f_levelName` and `f_shortName` overlap.

**Audited defects** (`overhaul-r1-findings.md`): 49 findings, 18 P1 and 31 P2. Only 3 are VERIFIED real: cs-hvalid-equal-high, cs-mtf-anchor-print-bar and perf-1. The other 46 are "not yet verified". Merged duplicates give about 35 distinct defects:

| Theme | Finding IDs | Lines |
|---|---|---|
| 76 inputs in the status line | VIS-statusline-inputs, TE1, ux-statusline-inputs (P1 ×3) | 60-237 |
| Bias stale at HTF close | rp-bias-done, struct-F2 (P1 ×2) | 782, 926 |
| Swing CHoCH lag | struct-F1 (P1) | 755-774 |
| Table rows below the chart TF are mislabelled; 4H/D charts in Day mode warn | rp-table-below-chart, struct-F3 (P2), TE2 (P1) | 68-82, 2303 |
| Taper evicts the committed target just before the hit | dol-A, TE4 (P1 ×2) | 666-667 |
| Out-of-range targets with PoT about 0% can be chosen or kept | dol-B, TE3 (P1 ×2) | 664-667, 1950-2020 |
| Stack demotes key levels behind weaker pools | LIQ1, dol-D (P1 ×2) | 1230-1251, 684-685 |
| Pool trim deletes fresh arrays and the counter-draw side | dol-C (P1) | 1950-1962 |
| No relative EQ between key levels | LIQ2 (P1) | 1824-1852 |
| Partial first PWH/PWL period | rp-partial-pwh (P1) | 945-946 |
| Daily chart: every candle becomes a PDH/PDL | TE5 (P1) | 945, 1790-1794 |
| HTF FVG dropped beyond 15 ATR | PD-1 (P1) | 1859 |
| HTF FVG has no quality or direction check | PD-5 | 785-796 |
| HTF FVG has no origin lockout | dol-G | 689 |
| Classic breaker never created; liquidity gate checks the wrong extreme | PD-2 | 1691, 1706 |
| OB not moved to the HL/LH retest | PD-3 | 1695 |
| OB quality gate almost always passes | PD-4 | 1688 |
| iFVG far behind never cleaned; cap of 8 clutters the view; overlapping iFVGs | PD-6, TE7, ux-ifvg-overlap-merge | 198, 1609, 1636 |
| MTF pools anchored at the HTF bar open | cs-mtf-anchor-print-bar (verified), LIQ7 | 1223, 1783 |
| Equal MTF pivot marked swept | cs-hvalid-equal-high (verified) | 780 |
| Exact touch counts as neither test nor sweep | LIQ4 | 654 |
| EQ history lost on a slightly-higher second swing | LIQ3 | 1762 |
| Killzone affinity boosts days-old session pools | LIQ6 | 1941 |
| Key extremes start "immature"; `hlMult` slows maturation | LIQ5, dol-E | 668-671 |
| "PoT 95%" after a live sweep; no TF in the label; no "no target" state | dol-F, VIS-swept-label, ux-clean-swept-label, TE6, VIS-no-target-state | 2225, 2305 |
| Displayed PoT never checked against outcomes | pot-ledger-calibration | 2067 |
| `f_bump` int overflow | pot-bump-floor-guard | 1268 |
| Light theme invisible | VIS-light-theme-ink | 2219 |
| Killzones by bar open on 2H/4H charts | rp-kz-above-1h | 975 |
| Last-bar analytics every tick | perf-1 (verified) | 2111 |
| Ghost trail off by default and loud when on | ux-ghost-default | 210 |
| Alert text content | TE8, ux-alert-content | 2083, 2090 |

**Defects found by the study and not by the audit:**
1. **Raid → D mapping is wrong-signed (1581).** REJECT is scored as reversal, but the data show a small continuation lean (`ict_liq` §0.2; `ict_struct` §0.3). One wide bar through a stack moves D by up to 0.75·wL. A 1-tick poke counts as a full REJECT.
2. **Volume-profile path cost (1945-1947) is wrong.** 63-86% of the "thin" class are beyond-range targets clamped onto tail rows by `f_row` (570). For in-range thin paths, the within-bar result is −5.5 pp (CME 120 h, z −2.6). The ×0.85 thick penalty is unsupported (`amt_profile` §0.2).
3. **With zero or na volume the profile features are silently off.** This hits cash indices and many CFDs (997, 1007).
4. **Self-confluence (676-680, 1931).** PDH, PDL, PWH and PWL are their own anchors, so each gets conf ≥ 0.35, about +5 points (`calib_ml` §0.10).
5. **EQ merges are one-sided.** A right-hand print beyond the pool trades through it before the pivot confirms, so the "outer" branch of `f_mergeAt` (1116-1126) is effectively dead for chart pivots (`ict_liq` §0.8a).
6. **Breaker definition.** It reproduces only 11-24% of template breakers. Removing the `tookL` gate reproduces 57-77% (`ict_pd` §0.3).
7. **Session windows on 1H.** The NY AM range is wrong on 76% of days, because membership is tested at bar open (`ict_time` §0.7).
8. **Biased readouts by construction** (`skeptic` §0.4):
   - ETA|hit (2116-2127, 2240);
   - heat over hits only (2404-2408);
   - EV built from a race conditioned on being decided (2245, 2359), which shows −0.62R to −0.97R where the true martingale value is 0;
   - L50 (2395).
9. **The EDGE verdict peeks (2390).** On 288 real no-skill paths, a false "✓" appeared at some point on 13.5% of them (`skeptic` §0.5).
10. **`f_calMult` is noise (1376-1382).** Under a true null it sits ≥ 10% off 1 for 66%, 47% and 33% of families at n = 10, 40 and 80 (`calib_ml` §0.4).
11. **Ghost trail is survivorship-biased.** Targets out-scored on the same side vanish without a ghost (`skeptic` §0.11).
12. **`ta.pivothigh` ties.** The newest equal bar wins, so a tight double top gets no EQ count and is anchored at the later top: 12% of pivots on ES 5m, 41% on 6E 1m (`smc_impl` §0.5).

### 2.10 Test evidence for v2
- **Runtime on TradingView:** none recorded for `00a405a` in the files I read. Unverified.
- **Syntax:** the `pine_parse.sh` tool exists (pynescript; syntax only, no types). I did not run it.
- **Static audits:** 15 overhaul lenses, 49 findings, 3 verified (above).
- **Statistical evidence on v2's components** comes entirely from the study's replicas of v2 logic on local CME, BTC, SPX and FX data (§2.11). No run of v2 itself on TradingView data is recorded.

### 2.11 Study verdicts on v2's components (numbers as reported; sample and dataset in each row)

| Component (lines) | Verdict | Evidence |
|---|---|---|
| `f_pot`, `f_race`, `f_raceH` (434-482) | Correct maths (A, strong) | Match Monte Carlo; flux series re-derived term by term. P(touch within H) = 2.00 × P(finish beyond) at 0.5-4 ATR on CME 5-min (H 30) and 1H (H 12) bars (`quant_pot` §0.1, §0.4) |
| 50-bar drift in PoT and race (917, 665, 1361) | Harmful (C) | Removing it improves PoT log-loss by +3.66%, CI +2.99…+4.32, 326 symbol-days, 6 symbols, 5-min, H 30. The WIN≤H calibration slope is 0.69 with drift (`quant_pot` §0.2) |
| Empirical surface (1265-1300, 1527) | Calibrated (A, strong), clock-blind | Slope 0.99, ECE 0.004 on 1.2M 5-min rows (`calib_ml` §0.1). Hour bias up to −17 pp at 08:00 NY and +11 pp at 21:00 (`ict_time` §0.1, about 1.2M level-windows). Vol-state split: +1.79% LL, CI +1.45…+2.13 |
| Distance-matched baseline and ledger (1314, 1426-1499) | Right design (A, strong) | Leak-free, checked line by line (`skeptic` §0.3). Baseline calibration slope 0.93-1.04 on 13 clean sets, 76,181 probes (`calib_ml` §0.1) |
| Candle-colour intrabar order (1441) | Keep (A, strong) | Right 88.1% vs TradingView's open-proximity rule 80.6%, about 140k CME bars against 1-min truth (`pine_eng` §0.4) |
| Pools as magnets beyond distance | Null (C) | +0.1 ± 0.4 pp at 1H (7 datasets, n 52,762); +0.8 ± 0.6 pp at 5m (5 CME, n 30,887) (`ict_liq` §0.1) |
| EQ density (682) | Weak (A, weak) | +0.3 ± 1.8 pp (1H) and −0.1 ± 2.1 pp (5m) (`ict_liq`). EQ at 1H is the only feature surviving Holm: +0.29 logit, p 0.007 (`calib_ml` §0.6) |
| Tests, tier, confluence, prominence (682, 680) | Unsupported (C) | Holm p 0.07-0.23; no consistent effect (`calib_ml` §0.6, `ict_liq` §0.1) |
| Stack: inner ×0.70 and +0.45·stack (684, 682) | Heterogeneous (C) | Crowding at 1H mixed (NQ −3.0/−8.5/−8.6, BTC +2.2/+4.9/+8.0 pp); positive at 5m (`ict_liq` §0.5) |
| Draw vector D, 30% weight, ×0.5 counter-draw, D-first selection (1891-1898, 691-693, 1964-2035) | No skill (C, strong null) | D called the first side right 47.4-52.7% on 8 markets; random walks 48.4-52.1% (`ict_struct` §0.1). D-first selection loses 3.8-8.3 pp of first-touch accuracy on 7 datasets, all bootstrap CIs exclude 0 (`bias_dol` §0.4) |
| Raid hold/reject → D (1581) | Wrong sign (C) | After a sweep: 1H all +1.1 ± 0.5 pp (n 12,550), REJECT +1.5 ± 0.7 (continuation); 5m −0.2 ± 0.7 (n 7,705) (`ict_liq` §0.2). REJECT → continuation 52.6% (n 1,402, `ict_struct`) |
| FVG and OB as targets (907, 1663-1748) | Null (C) | FVG +0.4 pp (z 0.3, n 1,756) CME 1H; −0.6 pp (n 4,950) CME 5m; −1.6 pp BTC 1H (n 3,337). OB −1.8 to +2.4 pp (`ict_pd` §0.1) |
| FVG displacement quality (912, 1870, 687) | Not a target signal (C) | FVGs the engine rejects beat the baseline by +7.0 pp (z 3.3, CME 1H). Top displacement tercile −5.5 pp (z −3.8, BTC 1H) (`ict_pd` §0.2) |
| Breakers (1646-1661) | Wrong definition (D), weak targets (C) | 11-24% template reproduction. Reached −4.9 to −8.3 pp (CME 1H) and −7.5 pp (BTC, z −4.4) vs random (`ict_pd` §0.3) |
| iFVG (1598-1644) | Display only | First retest holds 49.1-50.2%, n ≈ 25,000. 130-158 iFVGs per 1,000 bars on 5m/1H (`smc_impl` §0.4) |
| Opposing FVG in the path | Missing, supported (A, moderate) | −2.8 ± 0.8 pp at 1H (n 4,757); −2.1 ± 1.0 pp at 5m (n 3,387); negative in 11 of 12 datasets (`ict_liq` §0.4) |
| Killzone affinity and hysteresis (597, 976) | Unsupported (C) | Macro windows +0.6 ± 0.5 pp (61k windows); Silver Bullet +0.2 ± 0.6 pp (`ict_time` §0.6). The only real time effect beyond volatility is the US cash-open drive in index futures (+10-15 pp, 60 days, 1-min ES/NQ/YM/RTY) |
| Midnight open anchor (964) | Not special (C) | +0.3 ± 1.1 pp, 1,412 instrument-days (`ict_time` §0.8). This supersedes the HANDOFF note that called it "the only time anchor with excess revisit" |
| VP path cost (1945-1947) | Wrong (C) | See §2.9 item 2 |
| `f_calMult`, EDGE verdict | Noise and peeking (C) | See §2.9 items 9-10 |
| Clean look (2214-2226, 2295-2307) | Matches the reference (E, design) | Within ±1 RGB except the white core: transparency 10 instead of 15 brings ΔE from 6.7 to 0.9 (`ux_design` §0.1). Light chart: contrast 1.04-1.37:1 |

---

## 3. The early engine (`DOL_Engine_early.pine`, 2548 lines; titled "DOL Engine v6 · Draw on Liquidity")

### 3.1 Purpose and design
- A DOL indicator *plus* a trading assistant aimed at MNQ and ES/MES on 1-minute and 5-minute charts ("Tuned for 1m / 5m charts", 2463).
- The core: one unified target queue (`Zn`) holding pools, FVG, iFVG, OB and breakers, a 6-pillar score, and a "self-learning" PoT. That PoT is an empirical excursion surface blended with an analytic first passage, then passed through a logistic layer with hard-coded research weights.
- Around the core:
  - reach bands;
  - a FIRST race readout;
  - a Brier SKILL readout;
  - a News Guard (release windows, an FOMC calendar, a spike detector);
  - order-flow, volatility, hours and cost filters;
  - three trade modes;
  - a virtual-trade tracker with an Edge Gate, risk sizing and a daily loss limit;
  - a BUY/SELL banner.
- Simple View is the default. The README calls it "DOL Engine v6"; the legacy README calls it the early engine. It predates v2: branch date 2026-10-05.

### 3.2 Architecture and section map

| Lines | Section |
|---|---|
| 1-33 | Header and `indicator()`. Drawing caps 120 each |
| 38-73 | Constants: kinds K_BSL..K_BRK; flags F_SW..F_STF; group names |
| 79-149 | Types: `Zn` (unified zone with source flags and cached pillars), `Ghost`, `Pred`, `SEvt` |
| 155-378 | Inputs: 186 in 16 groups (§3.4) |
| 381-388 | Simple View visibility flags |
| 393-722 | Utility functions (§3.3) |
| 727-845 | Timeframe, structure, session and period functions |
| 850-891 | Timeframe resolution: Auto mode, auto-tuned distances and horizons, ladder |
| 896-914 | Volatility (Garman-Klass and close-to-close σ), drift, momentum, volume |
| 919-923 | MTF requests: STF, HTF, Macro and EXE structure; the LVN feed |
| 928-931 | Session trackers |
| 937-969 | Intraday volatility seasonality |
| 974-1048 | News Guard, volatility regime, displacement, RVOL, order flow, killzone, signal hours |
| 1051-1072 | Auto cost, flat-at-close, sizing helpers, D/W/M periods |
| 1077-1152 | Swings, FVG raw, persistent state |
| 1158-1174 | Empirical excursion learning |
| 1179-1668 | Engine (confirmed bars): resolve predictions, structure, PD arrays, pools, lifecycle, scoring, selection, sampling, LVN |
| 1673-1680 | Bias engine |
| 1685-1702 | Confirmed execution signals |
| 1708-1749 | Sweep queue (Sweep Reversal) |
| 1756-2023 | Shadow ledger, virtual-trade tracker, trade modes, Edge Gate |
| 2028-2486 | Visual engine: last bar only, time-anchored; tables, banner, debug |
| 2491-2498 | Markers and data window |
| 2504-2548 | Alerts: 13 `alertcondition`s and 14 `alert()` calls |

### 3.3 Calculation inventory (functions)

| Lines | Function | Computes |
|---|---|---|
| 403 | `f_ncdf` | Normal CDF (Abramowitz-Stegun 26.2.17) |
| 413 | `f_touch` | First-passage touch with drift; the same formula as v2's `f_pot` |
| 425 | `f_potModel` | Blend (nE·pE + kE·pA)/(nE + kE), as a percentage between 0.1 and 99.9 |
| 432-452 | `f_empAdd`, `f_emp` | Empirical excursion store by HTF state × direction (6 groups, 80 bins), with interpolation |
| 456 | `f_potAll` | Full base PoT with the seasonality factor `sf` |
| 466 | `f_bk` | Time-of-day bucket in the session time zone |
| 469-479 | `f_sig`, `f_x1`, `f_lrP` | Logistic layer on [1, logit(base), vol regime, momentum, distance/max] |
| 481-577 | `f_isPool`, `f_kindTxt(K)`, `f_flagW` (unused), `f_flagCount`, `f_structW`, `f_setFlag`, `f_srcList`, `f_tgtName` | Source flags and names. `f_structW` sets a source importance (PM 1.0, PW .85, HTF .8, PD .7, EQ .6, sessions/STF .5, swing .35) and adds +0.08 per extra flag |
| 579 | `f_findId` | Index by id |
| 590 | `f_addPool` | Merges within 0.25 ATR (sets EQ if both are swings within the EQ tolerance), refs+1, moves outward, grows the zone up to a cap. Otherwise evicts the lowest score of that kind and pushes |
| 641 | `f_capKind` | Caps a kind by dropping the oldest |
| 663 | `f_ghost` | Ghost record |
| 672 | `f_resolve` | Resolves predictions (touch or expiry). Updates the Brier statistics and runs online SGD on the logistic weights with an L2 pull toward the prior |
| 700-712 | `f_trigLvl`, `f_tpPick` | Hit level by hit rule; nearest eligible target paying ≥ the minimum reward |
| 715-722 | `f_align`, `f_biasTxt`, `f_biasArrow` | HTF alignment 0..1; text |
| 727-739 | `f_orChart`, `f_ladder`, `f_clampTf`, `f_tfLbl` | Timeframe ladder (never below the chart) |
| 745 | `f_tfState(len)` | Structure state +2/+1/0/−1/−2 (BOS vs first break), last swings and their times, and a wick-taken flag, all `[1]`-shifted |
| 782 | `f_session` | Session H/L with times and bars, ended flag |
| 810 | `f_period` | Previous D/W/M high and low with exact candle. No partial-period guard |
| 1051-1065 | `f_autoCost`, `f_unit`, `f_perC` | Round-trip cost in ticks, by root symbol (MNQ 4, NQ 2, MES 2, ES 1.5, …) or by asset type; $ per contract at the stop |
| 1743 | `f_sqPick` | Nearest untaken level paying ≥ R (Sweep Reversal) |
| 1756-1782 | `f_shFinal`, `f_lcb`, `f_near` | Shadow ledger over 10 target sizes (0.05-3R); lower confidence bound; nearest size |
| 2032-2097 | `f_clearAll`, `f_room`, `f_mkBox`, `f_mkLine`, `f_mkLbl`, `f_pickKind`, `f_pickNext` | Time-anchored drawing helpers with an object budget |
| 2100-2123 | `f_liveDist`, `f_potLive`, `f_reach` | Live distance; live final PoT; bisection for the reach band (25 iterations) |

**Score (1481-1556).** Weights: proximity 30, freshness 15, confluence 20, density 15, structure 10, HTF 10.
- fP = 1/(1 + (d/(0.35·maxDist))²).
- fF = exp(−ln2·age/hl), with hl ×3 for HTF/PW/PM and ×2 for PD.
- fC = min(1, cnt/4), where cnt is the sum of:
  - extra source flags;
  - overlapping other kinds;
  - the last break on the same side;
  - premium/discount;
  - an opposite sweep within 30 bars;
  - momentum > 0.3.
- fD = 0.5·dens + 0.25·(refs − 1), +0.15 per same-kind pool within 1 ATR.
- fS = structure weight.
- fH = 0.45·align(HTF) + 0.25·align(Macro) + 0.30·level-TF.
- Penalties: (1 − 0.6·mitig) × 0.85^touches × 0.7 if the OB is mitigated.
- **PoT** = logistic(lrW · features), with research priors `lrW0` (1098, 1102). **Priority** = 0.65·score + 0.35·PoT (1550).

**Selection (1559-1635).**
- Eligible means: correct side, within `effDist` (4/6/8 ATR by mode), score ≥ 40, PoT ≥ 5, distance ≥ 0.5 ATR. Best by priority.
- Fallback: the best eligible target *ignoring* `minScore` (1584, "never leave the chart without a DOL").
- "Lock DOL Until Hit" is on by default. A new DOL needs 2 bars of confirmation.

### 3.4 Inputs and defaults (186)
There are 70 bool, 38 float, 42 int, 14 string, 9 color, 7 session, 5 timeframe and 1 text area. The main defaults:
- Mode Auto (≤ 5m Scalping, ≤ 1H Day, else Swing); auto-tune on (distance 4/6/8 ATR, horizon 20/30/40, stop lookback 15/20/30, time stop 40/60/80); history depth 20000; Simple View on.
- Min PoT 5%; grey-out below 20%; min score 40; lock on; confirm 2; hysteresis 6; PoT weight in ranking 0.35; max pools 24; max age 1500.
- Hit rule Touch Zone; merge 0.25 ATR; zone 0.10 ATR; EQ tolerance 0.10 ATR; min penetration 0.02 ATR.
- Sessions: Asia 2000-2359, London 0200-0500, NY 0930-1130, America/New_York.
- PD arrays: min FVG 0.20 ATR; OB displacement 1.5 ATR; caps FVG 10, iFVG 6, OB 6, BRK 4; drawings off.
- Trade mode "DOL Direction".
- Filters: volatility "Skip Low"; displacement on (0.5 ATR); order flow on (15 min); signal hours Auto (Core 09:30-11:30 + 13:30-15:45 NY for futures, indices and stocks); max cost 3% of the stop.
- News Guard on (08:25-08:45, 09:55-10:15) with an event calendar pre-filled with 24 FOMC dates for 2025-2027. Those dates are unverified by me.
- Tracker: target mode Balanced; target win rate 90%; Edge Gate on (30 signals, 0.5σ).
- Risk: $100 per trade; daily loss limit 2R; 3 signals per day; flat at 15:55 NY.
- Self-learning PoT on (learning rate 0.002); seasonality on; reach bands 50%.
- Colours: BUY blue #2962FF, SELL #FF4D6D, DOL magenta #E040FB ("Blue and red are used ONLY for real trades").

### 3.5 Signal logic
Three trade modes (`tradeModeIn`, 265):
- **DOL Direction (default, 1923-1935).** Enter toward the DOL as soon as it is placed. One trade per DOL. Blocked if PoT < 20%, outside hours or news, or if order flow is against. Target = the DOL; the stop sits beyond the nearest swept liquidity or the swing, widened so cost ≤ 3% of risk.
- **Sweep Reversal (1704-1749, 1936-1945, 1951-1952, 1980-1983).**
  - Queue: chart pivots plus PDH/PDL.
  - A sweep is high > level + 0.02 ATR and close < level (mirrored for lows).
  - Entry at the close; stop beyond the wick (+0.1 ATR, widened to the minimum cost stop).
  - Target: the nearest untaken opposite level paying ≥ 1R.
  - Filters: order flow, hours, news.
- **Confirmed Signals (1685-1702).**
  - Requires all of: a chart pivot break in the HTF direction; DOL on the same side; score ≥ 55; PoT ≥ 30; an opposite sweep within 20 bars; displacement; the filters; a 15-bar cooldown.
  - Subject to the Edge Gate (lower confidence bound of the shadow-ledger R > 0 after ≥ 30 signals).

One virtual trade runs at a time, with gap-at-open fills, intrabar order by open proximity, a time stop, a daily limit and flat at 15:55. Markers: BUY and SELL triangles, skipped crosses, exit diamonds.

### 3.6 Non-repaint status
- **`request.security`: PASS.** `f_tfState` returns `[1]` values (779) and the LVN feed uses `[1]` (923), all with `lookahead_on`. Timeframes come from `f_ladder`, which is never below the chart, or `f_clampTf`, which falls back to the chart.
- **`request.security_lower_tf(…, "1")` (1034) is CAUTION.**
  - It is a 1-minute request *below* the chart timeframe, inside an `if` (a v6 dynamic request).
  - It is consumed only in confirmed-bar logic, so it is not a repaint. But it breaks v2's "never below the chart TF" rule, and intrabar history depth is limited.
- **Engine, signals, sweeps and tracker: PASS.** All are gated by `barstate.isconfirmed` (1179, 1687, 1712, 1827). The displayed PoT is the bar-close value (`primPot`). Reach bands are computed on the confirmed last bar.
- **Parity risk.** The same as v2, and larger: online weights, decayed surfaces and the shadow ledger all depend on history start (`inWin`, 891).

### 3.7 Performance risks
- **The seasonality block (945-969) runs every bar *and every realtime tick*.** It loops 20 past buckets plus `effHor` future buckets (up to 200 when manual), with `hour()` and `minute()` calls.
- **The scoring pair loop is O(n²)** over about 50 zones on every confirmed bar (1516-1527), plus a PoT and a logistic call per zone.
- **Up to 800 pending predictions** (`preds`, `accs`, 400 each) are resolved every bar.
- Reach bisection: 25 × `f_potLive` on the last bar.
- History depth defaults to 20000.
- 186 inputs: status-line clutter and an input-tab burden.

### 3.8 Broken, duplicated and dead code
- **Dead:** `f_flagW` (490). The EXE tuple values `xSH`, `xSHT`, `xSHW`, `xSL`, `xSLT`, `xSLW` (922). `rH` and `rD` (1187), returned and unused.
- **Duplicated:** `f_kindTxt`/`f_kindTxtK` (484-488); `f_tpPick`/`f_sqPick` (704, 1743); `f_potAll`/`f_potLive` (456, 2109) repeat the PoT pipeline.
- **Logic problems:**
  1. **Confluence counts the *names* of one price as independent confluence** (`f_flagCount − 1`, 1505; +0.08 per flag in `f_structW`, 517). The APEX spec forbids this (§5).
  2. **The "never leave the chart without a DOL" fallback (1583-1585)** ignores `minScore`. Neutral is legitimate under the APEX spec (§13.3).
  3. **Priority mixes a heuristic score with a probability** (1550).
  4. **`lrW0` are hard-coded "research" weights** whose fit cannot be reproduced (scripts absent).
  5. **The seasonality future calendar `time + i·barMs` (964) ignores session gaps and weekends.** The study requires the real future-bar calendar (QPOT-05).
  6. **STF/HTF pools are anchored at the HTF bar open** (`stSHT`, 1339), the same issue as v2.
  7. **`f_autoCost` hard-codes NQ, MNQ, ES and MES by root (1053).** The APEX spec says never to hard-code calculations for NQ (§2.1).
  8. **The pre-filled FOMC dates are unverified**, and dated events go stale.
  9. **"Target Win Rate" mode produces high win rates from tiny targets** (≈ 0.09R at 90%). It is honest in its tooltip but misleading as a headline number.

### 3.9 Test evidence and results (README claims; scripts absent; not re-run)

**PoT research.**
- Scope: a Python replica, 13 markets (BTC, ETH, SOL, ES, NQ, GC, CL, EURUSD, GBPUSD, USDJPY, SPY, QQQ, TSLA), 5m and 1h. That is 26 datasets, about 1.1M bars and about 519k resolved targets, with a time-ordered 70/30 split.
- Brier skill on the test split:

| PoT model | Brier skill |
|---|---|
| Analytic random walk only | ≈ 0.14 |
| Empirical + analytic blend | 0.192 |
| v5 bin calibration on top | 0.194 |
| v6 learning layer + slow per-chart learning | 0.201 |
| Online learning with all 20 ICT features | 0.192 (over-fits) |

- With the v6 logic and a 5,000-bar window, the average over the 26 datasets was SKILL +20.3% and DOL HIT 74%.

**Findings stated in the README:**
- **Supported by the data:** distance and the volatility regime drive touch probability. Elevated ATR means fewer touches than a random walk predicts, and short-term momentum toward a level mean-reverts.
- **Rejected by the data:**
  - **Liquidity type** (EQH/EQL, sessions, PDH/PDL, HTF levels), HTF bias, sweeps, premium/discount, confluence and the DOL score: no measurable out-of-sample value, for touch or for side.
  - **DOL side:** taken first 59.3% of the time, exactly what distance alone implies (59.3%).
  - **Execution setups:** HTF-aligned breaks with the DOL on the same side, plus sweep and displacement filters, have no reliable edge. With a symmetric 1-ATR stop and target, trading *with* the signal won 48.7% and trading *against* it won 49.8%.

**Sweep Reversal and order-flow tests.**
- Data: MNQ/NQ and S&P on 1m and 5m, costs included. 4 weeks of 1-minute and 10 weeks of 5-minute CME data, plus 6 weeks of 1-minute index data (March-April 2025).

| Mode | Trades | Win | R per trade | Note |
|---|---|---|---|---|
| Sweep Reversal, no order-flow filter | 1,350 | 38% | −0.06R | |
| Sweep Reversal + order-flow filter | 357 | 49% | +0.09R | Positive only in March-April 2025; negative on the recent CME data, so the README says "not proven" |
| DOL Direction + order flow | 1,235 | 53% | −0.02R | Same data |

- **Order-flow filter alone** (19 days of 1-minute and 49 days of 5-minute CME data, plus 42 days of 1-minute index data): a 10-20 minute window lost about 0.05R less per trade with about half the trades. A 30-minute window was worse. Not significant, and still negative after costs.

**Target Win Rate controller** (12 markets on 5m, 15m, 1h and 1D):
- target 85% → 84.9% realised (per market 84-87%);
- target 90% → 89.6% (10 of 12 markets exactly 90%);
- target 95% → 93.7%.
- The average trade was about 0R before costs. The controller works; the edge is nil.

**MNQ/MES 1-minute research.**
- Data: about 3.7 years of Dukascopy 1-minute Nasdaq-100 and S&P 500 index data, about 420 full NY sessions per market. Costs: 1.0 point round trip on NQ, 0.5 on the S&P.
- Tested: opening-range breakout, noise-boundary momentum, first-half-hour momentum, and ICT sweep reversals of the prior-day and overnight highs/lows. Linear and gradient-boosted models on about 20 features, walk-forward over 2024-2026.
- **Result: none was reliably profitable after costs.**
  - Costs cause most of the loss: −0.08R per trade on NQ and −0.17R on the S&P.
  - Overnight and tight-stop signals lose 3-5× more.
  - Filter table:

| Replay (simplified signal) | NQ trades | NQ total | S&P trades | S&P total |
|---|---|---|---|---|
| No filters, 90% target | 20,031 | −1,655R | 19,038 | −3,245R |
| Filters, 90% target | 2,460 | −75R | 537 | −26R |
| Filters, 1R target | 1,903 | −36R | 457 | +7.5R |
| + Edge Gate + daily limit | 10 | −2R | 70 | −8R |

**Lessons (the data supported vs rejected).** These match the later study's independent replications:
- **Supported:**
  - distance and volatility as the touch backbone (study: `ict_liq` §0.1, `calib_ml` §0.1);
  - empirical + analytic blending (study: surface slope 0.99);
  - costs dominating short-horizon futures signals;
  - a cost-vs-stop filter and core-hours filter reducing damage.
- **Rejected:**
  - liquidity type, HTF bias, sweeps, premium/discount, confluence and the score as predictors (study: same);
  - the DOL side beyond distance (study: geometry 67-75%, D 47-54%);
  - sweep-reversal and DOL-direction trading (study: REJECT → continuation lean; Turtle Soup ≤ geometry on 9 datasets; MSS 49.4%, n 4,032);
  - a high-capacity feature learner (over-fits; study: ungated learners lose to the baseline on clean data).

### 3.10 User preferences visible here
- Simple View by default.
- Blue and red only for real trades; magenta DOL.
- A BUY NOW / SELL NOW banner with contract counts at a $ risk.
- Daily loss limit; one trade at a time; NY core hours; flat at 15:55; MNQ/MES on 1m/5m.
- Auto mode.
- An honest "This chart: N trades · win % · R/trade ($)" line.
- Tooltips that say "not proven" and "a filter, not a guarantee".

---

## 4. Liquidity Flow Pro (`liquidity-flow-pro.pine`, 1615 lines), README and `liquidity_model_sim.py`

### 4.1 Purpose and design
An "estimated liquidity-concentration model". From confirmed swings, external swings, equal-level clusters, tests, HTF swings, D/W/M and session levels and the sweep state, it scores active pools. It then reports:
- BUY-SIDE% = the share of scored active liquidity above price, and SELL-SIDE% the share below;
- a target side, strength, model confidence, key pool and last sweep;
- optional signals.

There is no single DOL target and no PoT. Two styles:
- **Video** (default): two big zones split at price, labelled "▲ UP xx%" and "▼ DOWN yy%";
- **Pro:** a dashboard plus every pool drawn.

### 4.2 Section map

| Lines | Section |
|---|---|
| 1-34 | Header (explicitly "NOT a probability", 12-17). Caps 500 |
| 39-222 | Inputs (96) |
| 184-194 | Effective visibility (Video hides the Pro drawings) |
| 228-291 | Types `Pool` (owns its box, line and label) and `Period`; state |
| 296-308 | Core series: ATR, volume quality, relative volume at the pivot, scaled lengths |
| 313-631 | Helpers (§4.3) |
| 636-685 | Data collection: pivots, external pivots, range, HTF request, periods, sessions |
| 690-871 | Engine (confirmed bars): swings → pools; external; HTF; sessions; sweep/taken/test; structure; cap |
| 876-1091 | Scoring (every tick): pressure, bounded tilts, aggregation, live raid, swept, current session, normalisation, key pool, confidence |
| 1096-1182 | Flow events and signals (confirmed bars) |
| 1188-1293 | Pool styling, ranks, current-session lines |
| 1300-1341 | Video zones |
| 1348-1547 | Dashboard |
| 1552-1566 | Markers and debug plots |
| 1573-1615 | Alerts: one rich `alert()` per bar and 12 `alertcondition`s |

### 4.3 Calculation inventory

| Lines | Function | Computes |
|---|---|---|
| 318 | `f_timeFactor` | 0.5 + 0.5·e^(−age/mem): freshness floored at 50% |
| 322 | `f_distW` | 1/(1 + 0.25·w·dATR) |
| 327-344 | `f_components`, `f_intrinsic` | strength = base(1 + session bonus .20/.25/.50/.75) × cluster(1 + 1.25·min(members − 1, 3)) + tests(0.3 each, ≤ 1.5) + volume(≤ 1 at RVOL 3) + structure(1 + 0.5 external) + HTF(1) |
| 347-366 | `f_tier`, `f_tierName`, `f_strengthName`, `f_tag` | Minor, Moderate, Major, Extreme; EQH ×n, HTF, EXT, STRUCT tags |
| 392-455 | `f_zoneBounds`, `f_newDrawings`, `f_syncDrawings`, `f_deleteDrawings`, `f_fadeSwept` | Object ownership per pool; on a sweep the zone is faded and ✕ marks the exact level, with the depth in the tooltip |
| 461 | `f_addLevel` | Clusters into a same-side pool if the distance ≤ tol *and* the combined span ≤ 2·tol (no chain drift); tracks members, hi and lo; a same-point HTF/session print is not an extra member; otherwise creates a pool |
| 506 | `f_announce` | Fires once when a pool first reaches the MAJOR tier |
| 517-533 | `f_remember`, `f_recall` | Swing bar → pool map, so an external pivot finds its pool |
| 536 | `f_enforceCap` | Removes the lowest intrinsic × freshness × distance weight |
| 554 | `f_period` | **Discards the first partial period** (`count > 0`) |
| 590 | `f_session` | **Skips a session already running at chart start** |
| 627 | `f_htfSwings` | HTF pivots `[1]` with the HTF time |

**Engine (715-871).**
- Pools are created from pivots. A pool is STRUCTURAL if the pivot is a range extreme; HH/LH and HL/LL typing is recorded.
- External pivots (pivot length × 3) mark EXT; HTF pivots mark HTF.
- D/W/M levels are gated by chart TF (674-676); sessions are optional.
- **Commit outcome (784-837), per pool:**
  - **taken:** close beyond level + band, so the pool is removed;
  - **sweep:** high beyond level + band and a close back inside, plus a rejecting candle in Strict mode;
  - **test:** an approach into the band.
  - The band is the EQ tolerance (0 in Aggressive mode).
- **BOS (853-868):** a close beyond the last swing + band. The opposite swing becomes STRUCTURAL.

**Scoring (876-1059).**
- Pressure = EMA of (CLV + body/ATR + ROC + DMI balance [+ volume imbalance]).
- Tilts by structure, pressure and premium/discount, each ≤ ×1.25.
- Sum of strength × freshness × distance weight per side.
- EMA smoothing, then a stability prior (+0.5 each side).
- `dataFrac` shrinks the reading toward 50/50 when scored liquidity is < 0.6.
- `domNow` requires a separation ≥ 8 points.

**Confidence (1082-1091):** 0.35·separation + 0.15·count + 0.15·clustering + 0.20·structure agreement + 0.15·HTF agreement, × a data factor. It is labelled "not a probability".

**Signals (1163-1182):** an opposite-side sweep, then a structure shift after it, then the flow toward the new side ≥ 55% and above its pre-sweep value. At most once per anchor. Off by default.

### 4.4 Inputs (96)
44 bool, 17 float, 15 int, 9 string, 8 color, 3 session. Main defaults:
- Style Video; zone lookback 50; zone labels "Direction (▲ UP / ▼ DOWN)".
- Swing length 5; EQ tolerance 0.15 ATR; max pools 30; max distance 50 ATR; memory 200; external ×3; auto-scale.
- Weights: distance 1, EQ 1.5, volume 1, structure 1, HTF 1, session 1. Smoothing 3; stability 0.5; balanced threshold 8.
- Flow mode "Liquidity + Structure".
- HTF Auto (1m→15m, ≤ 5m→1H, ≤ 1H→4H, ≤ 4H→D, D→W).
- PDH/PDL and PWH/PWL on; PMH/PML off; sessions off (Asia 1800-0300, London 0300-0830, NY 0830-1600).
- Sweeps Balanced; signals off.

### 4.5 Signal logic
The events are:
- dominance change and flip (BUY ↔ SELL);
- a shift (≥ 10 points in 5 bars);
- a new key target;
- a new MAJOR pool;
- sweeps;
- optional BUY/SELL setups.

All commit at bar close.

### 4.6 Non-repaint status
- **PASS.** There is one `request.security` (660), `[1]` with `lookahead_on`, valid only if the HTF is above the chart. Structure, sweeps, flips, signals and alerts commit on `barstate.isconfirmed`.
- **Live by design.** The percentages, the Video zones and the dashboard update every tick. A "Freeze Current-Bar Calculation" option holds the confirmed value. A "RAIDING / BREAKING … LIVE" status is display-only.

### 4.7 Performance
Light: ≤ 30 active pools and ≤ 20 swept, an O(pools) score per tick, 13 `for` loops. Each pool owns up to 3 drawings, within the 500 caps.

### 4.8 Broken, duplicated and dead code
- **Dead:** `adxVal` (885).
- **Duplicated:** `f_intrinsic` and the inline `s = base·cluster + …` (952-953).
- **Logic problems:**
  1. **The Video tooltip and README make a directional claim.** They say "Price tends to be drawn toward the side holding more liquidity, so the bigger number … is the more likely direction" (README line 24; tooltip 55, 61). That contradicts the header (12-17). No test supports it.
  2. **"Sellers / Buyers" wording (1320)** labels the upper zone "Sellers", which mislabels a liquidity share as participant control.
  3. **The zone tooltip says "If price runs this zone's liquidity and closes back out of it (a sweep), the pull is used up and price often turns"** (1324). The study contradicts it: no reversal edge after sweeps, and a small continuation lean.
  4. **HTF pools are anchored at the HTF bar's time** (`htfPT`) and `b = bar_index` (758), so not at the wick candle.
  5. **Tests add strength** (0.3 each). The APEX spec says repeated touches must not automatically add strength (§4.4), and the study finds no effect.

### 4.9 Test evidence (re-run by me)
- `python3 -I liquidity_model_sim.py` → **15/15 scenario checks pass**:
  - A: equal highs above give BUY 68.6%;
  - B: the mirror gives SELL 68.6%;
  - the model is exactly symmetric;
  - A2: clustered 58.2% vs a 50.3% control;
  - C/D: the sweep is detected on the confirmed candle, and raw buy falls from 3.71 to 0.00;
  - E: 47.1/52.9;
  - F/F′: LOW DATA reads 50/50;
  - G: one giant candle stays bounded.
- **Random walks** (6 seeds × 3000 bars, driftless):
  - extreme readings on 7.35% of bars, balanced on 16.12%;
  - 14.77 flips per 1,000 bars (about one per 68 bars), matching the README;
  - 3.28 signals per 1,000 bars;
  - mean step 1.91 points.
- **What this proves:** the code behaves as designed on synthetic paths (unit tests). It does **not** test predictive value.
  - No real-data outcome test exists.
  - The random-walk figures show the reading flips and goes "EXTREME" on paths that have no direction by construction.
  - HTF and calendar levels are not simulated (README).
  - TradingView compile: unverified ("TradingView's compiler can't be reached", README).

### 4.10 User preferences visible here
- Video style with large percentage labels (from a "reference clip"); wording options.
- BUY-SIDE/SELL-SIDE terminology.
- Signals off by default.
- Heavy emphasis on non-repainting and on "not a probability" disclaimers.

---

## 5. Comparison of the three engines

### 5.1 Liquidity sources

| Source | v2 | Early | LFP |
|---|---|---|---|
| Chart swings | Yes; EQ within 0.10 ATR, one-sided | Yes; pre-formation tests and coil | Yes; bounded clusters |
| External / higher swings | STF + HTF through a registry with re-entry, unswept check | STF + HTF + Macro, wick-taken filter | External ×3 length; one HTF |
| PDH/PDL, PWH/PWL | Yes (no partial guard; daily-chart bug TE5) | Yes (chart-TF gated) | Yes (partial guard + chart-TF gate) |
| PMH/PML | **No** | Yes | Yes (off by default) |
| Sessions | Asia, London, NY AM (bar-open membership) | Asia, London, NY | Asia, London, NY (off) + current session |
| FVG / iFVG | Chart + HTF FVG; iFVG display | FVG → iFVG in the same object | No |
| OB / breaker | Yes (gated breaker, 11-24% template) | Yes (any OB closed through becomes a breaker) | No |
| Exact anchoring | Print candle (chart) / HTF bar open (MTF) | Time-anchored; HTF bar open | Time-anchored; HTF bar time |
| Data-quality handling | None (zero volume silently disables VP) | `hasVol` for the OB volume test | `volOK`, LOW DATA shrink |

### 5.2 Lifecycle and sweep handling
- **v2:** strict trade-through removes the pool. Hold or reject is collapsed into `liqEvt`, with the wrong sign. Arrays have touch/CE/full delivery and partial crop. Ejection beyond 15 slow-ATR. The registry keeps far pools for re-entry. There are no explicit states.
- **Early:** HIT, SWEPT (wick through and close back), BROKEN (close through), EXPIRED, EJECTED, FADED and INVALID as ghost reasons. FVG→iFVG and OB→BRK transitions happen in place. There is a mitigation fraction.
- **LFP:** the clearest commit taxonomy: **sweep** (trade beyond the band, close back inside), **taken** (close beyond the band, removed), **test** (approach). Swept pools are kept faded with depth.
- **Best for APEX §4.5/4.6:** LFP's taxonomy plus v2's registry and array delivery, extended to the spec's 10 states. The band should come from the measured wick depths (median 0.23-0.28 ATR, p80 0.51-0.64 ATR; `ict_liq` §0.6).

### 5.3 Target selection and probability
- **v2:**
  - A 5-pillar heuristic score with D-first selection.
  - The best PoT and race mathematics: drift aside, it is correct.
  - A distance-matched ledger.
  - No per-chart grading of the displayed PoT.
- **Early:**
  - A 6-pillar score blended with PoT into a priority.
  - A logistic PoT layer with unverifiable fixed weights.
  - Seasonality.
  - A Brier SKILL readout: per-chart grading, the one v2 lacks.
  - Lock-until-hit.
- **LFP:** no selection. An aggregate side share and a strongest pool.
- **Study verdict on selection:**
  - Which pool is touched first is a two-barrier race (geometry 65.3% vs 65.8% predicted, n 12,148, 8 markets; `ict_struct` §0.5).
  - The best utility objective is expected reach d·PoT(d). It delivered 1.10-1.43 ATR per target, against 0.86-1.09 for the hand score and 0.66-0.93 for "nearest" (13 intraday/1H sets; `calib_ml` §0.8).
  - Every ICT feature starts neutral, is measured on a candidate shadow ledger, and earns weight only behind a prequential gate.

### 5.4 Which is strongest?
- **Liquidity mapping:** v2, completed with LFP's lifecycle and data-quality primitives and the early engine's PMH/PML and chart-TF gating.
- **Probability machinery:** v2 (`f_pot`, `f_race`, `f_raceH`, the empirical surface, the distance-matched ledger), plus the early engine's seasonality concept and SKILL scorecard. Both must be gated and drift-free.
- **Target logic:** none of the three as written. Every scoring layer is mostly unsupported beyond distance (§2.11, §3.9). The best *stabilising* mechanisms are v2's 2-bar challenger with hysteresis and the early engine's optional lock-until-hit.
- **Tested results:** the early engine is the only one with outcome tests. Every one of its tests, plus the later study, says the same thing: **geometry is the signal; ICT labels and sweep reversals are not; costs dominate short-horizon trading.**

---

## 6. PRESERVE / REWORK / DROP recommendations

Columns: what, lines, class/grade, reason. "Preserve" means carrying the logic into APEX essentially unchanged (it may be re-wrapped into modules).

### 6.1 From v2

**PRESERVE**

| ID | Component (lines) | Class / grade | Reason |
|---|---|---|---|
| P-v2-1 | `f_erfcLog`, `f_erfc`, `f_phi`, `f_expPhi`, `f_pot` (408-444) | A strong | Verified first-passage maths; reflection identity holds on CME bars. Call with μ = 0 |
| P-v2-2 | `f_race`, `f_raceH` (447-482) | A strong | Verified race; geometry is the "which side first" backbone. Feed σ_eff = √(V_H/H) (slope 1.00, `quant_pot` §0.3) |
| P-v2-3 | `f_clamp`, `f_wilson`, `f_logit`, `f_sigm` (400-503) | A strong | Standard |
| P-v2-4 | Non-repaint MTF pattern: `[1]` inside the requested function + `lookahead_on`, and `f_tfSafe` (564, 782, 796, 923-925, 939, 981) | E strong | `pine_eng`: "do not touch". The leak demo shows the cost of getting it wrong (49.6% → 59.5%) |
| P-v2-5 | Confirmed-bar engine gate (1518); last-bar render arrays with delete/recreate (2098-2149) | E strong | Correct execution model; add Clean-mode gating of analytics (perf-1) |
| P-v2-6 | Empirical excursion surface (1061-1062, 1265-1300, 1527-1532, 1325) | A strong | Calibrated (slope 0.99, ECE 0.004). Re-key by volatility state and time of day with partial pooling; overflow guard in `f_bump` |
| P-v2-7 | Distance-matched baseline `f_potBase` (1314) and ledger record mechanics `f_openTrial`, `f_step` (1426-1459), including the candle-colour order (1441) | A strong | Leak-free; right baseline; colour order 88.1% vs 80.6% |
| P-v2-8 | Exact anchoring `f_anchorScan` (1141), `tfOpenBar` map + `f_barAtTime` (1165-1209), `f_x` + `max_bars_back(time, 5000)` (37, 404) | E (engineering) | Anchors zones on the printing candle, which the user's reference asks for. Extend to the exact MTF wick bar (SMC-10) |
| P-v2-9 | External registry with eviction and re-entry (`Ext` 365, `f_pushExt` 1211, 1591-1596, 1813-1852) | E (engineering) | Lets far HTF/key pools come back in range without bloating the pool |
| P-v2-10 | Sweep rule: strict trade-through for pools, touch for arrays (`touched` 623) | E/D definition | Matches open-source conventions (`smc_impl` §0.1). Add exact touch = test (LIQ4) |
| P-v2-11 | Clean DOL render (2214-2226), Classic palette (240-299), Clean bias table (2295-2307), Clean iFVG box (1611-1615) | Design (user preference) | Matches the reference within ±1 RGB; white core transparency 10. Add a light-chart ink variant |
| P-v2-12 | 2-bar challenger + hysteresis, ×2 to flip sides (2011-2020) | D weak (stability) | Prevents "targets jump around"; drop the killzone multiplier on it |
| P-v2-13 | Origin lockout / must-leave rule (`track` 650, 689-690) | D weak | Sound guard against "picking the zone price sits in". Extend to HTF arrays (dol-G) |
| P-v2-14 | FVG detection (907-908) and CE/full delivery with partial crop (1566-1577) | E/D definition | Objective formation and mitigation rules (spec §5). Quality is a clutter control only |
| P-v2-15 | iFVG inversion and body-close upkeep (1598-1644) | D (display) | Keep as display and alert only (first retest holds 49-50%, n ≈ 25,000). Add the SMC-6 density filter, cap 3 and overlap merge |
| P-v2-16 | Live sweep check against the committed target (1504-1509) | E | Honest live event; label it provisional and keep it out of confirmed alerts by default (spec §19.1) |

**REWORK**

| ID | Component (lines) | Class / grade | What to fix |
|---|---|---|---|
| R-v2-1 | `f_structure` (708-782) | D definition; C as predictor | Swing CHoCH lag (struct-F1); stale at HTF close (struct-F2); equal-pivot `hValid` (780); use `protH/protL` for ICT's dealing range (ICTS-4); emit BOS/CHoCH/MSS events with a knowable-at bar; HH/HL/LH/LL typing (from LFP) |
| R-v2-2 | `evaluate` → "Draw Score" (661-696) | C (pillars unsupported) | Neutralise the draw, density, tier and confluence levers. Taper for *new* picks only (TE4). Zero beyond max distance (TE3). Remove self-confluence (CAL-5). Remove drift from reach (665). Add the opposing-FVG path cost (ICT-5, A moderate). Objective d·PoT(d) (CAL-8). Reason codes per pillar |
| R-v2-3 | Selection (1964-2035) | D | Output the best buy-side *and* best sell-side target (spec §4.7). Side choice by a zero-drift finite-horizon race, then a gated calibrated side model (BIAS-1/2). Keep hysteresis. Neutral when nothing qualifies |
| R-v2-4 | D and `liqEvt` (1535, 1580-1582, 1891-1898) | C (no skill; wrong sign) | Neutral REJECT; HOLD against HTF as the only static lean; one event per bar per side (ICT-9). Record hold/reject as ledger features (spec §4.8: destination vs reversal are separate processes) |
| R-v2-5 | Stacks (`f_stackSide` 1230-1251, 684-685, 1912-1927) | C heterogeneous | Keep the stack count as an attribute; no inner ×0.70 and no fixed "outermost is the draw" (ICT-10, LIQ1) |
| R-v2-6 | EQ merging (`f_findLiq` 1090, `f_mergeAt` 1111-1131) | D; EQ A weak | Two-sided EQ (relative equal), EQ across key levels (LIQ2, LIQ3), pivot ties (SMC-8). Adopt LFP's bounded-span cluster |
| R-v2-7 | Calendar trackers `f_rangeTrack` (807-832, 945-961) | E | Partial-period guard (rp-partial-pwh); chart-TF gating (TE5); add PMH/PML |
| R-v2-8 | Sessions and killzones (`f_sessTrack` 835, `f_sessOpen` 798, 971-976) | E definition | Membership by time interval, not bar open (NY AM wrong on 76% of 1H days); killzones only ≤ 1H |
| R-v2-9 | Displayed PoT (`f_potModel` 1303, `potMu` 917, 2063-2068) | A strong (model); per chart: ungraded | Zero drift (+3.66% LL); volatility-state and clock keys; grade on the chart (Brier, reliability); gated online Platt (CAL-4). Label policy in §8 |
| R-v2-10 | `f_invalidation` (1343-1364), `f_raceAdj` (1367) | A (race); C (EV) | Zero drift, σ_eff; structural invalidation; R:R kept; gate `f_raceAdj` (CAL-11) |
| R-v2-11 | Ledger verdict and variance (`f_book` 1461-1499, `cluSt` 1077, 2374-2430) | A strong (method), C (verdict) | Mirror-controlled anytime-valid three-way verdict (SKEP-2: false alarms 0.7%); centred open-keyed blocks (SKEP-3); candidate shadow ledger (CAL-3); grade the PoT |
| R-v2-12 | `f_calMult` (1376-1382), `useCal` | C (noise) | Neutral by default; overlap-aware empirical Bayes; evidence-gated (CAL-1) |
| R-v2-13 | Order blocks (1663-1748) | D definition; C as target | Retest candle (PD-3); a real quality gate (PD-4); neutral target weight |
| R-v2-14 | Breakers (1646-1661, 1691, 1706, 1734, 1747) | D definition; C target | Template definition (old extreme taken, close through the swing), wick raids, dedupe; target weight < 1 (ICTPD-2) |
| R-v2-15 | HTF FVG (785-796, 938-942, 1854-1865) | D | Keep far HTF FVGs in the registry (PD-1); quality and direction check (PD-5); lockout (dol-G); no +0.20 HTF bonus |
| R-v2-16 | Volume profile (978-1015, `f_profile` 1384, `f_pathVol` 1417, LVN 2251-2286) | A weak (LVN faster-through); C (path cost) | Path multiplier neutral (AMT-1); zero-volume detection with a data-quality flag; feeds spec §7 POC/VA *estimates* labelled as proxies; LVN display only |
| R-v2-17 | Inputs (60-237) | E (platform) | `display = display.none` on all non-plot inputs; `active =` dependencies; fix the colour rows (CW10026); auto-fit timeframes to the chart (TE2, using the early engine's `f_ladder`) |
| R-v2-18 | Ghost trail (`f_ghost` 1253, 1585, 2021-2023) | A (survivorship) | Ghost every outcome, including replaced targets, with time-to-hit (SKEP-10); faint by default |
| R-v2-19 | Clean label states (2225, 2305) | Design | "Swept ✓" after a live sweep; timeframe in the code ("D BSL"); a "no target / filtered" state |
| R-v2-20 | Pool trim at capacity (1950-1962) | D | Protect fresh and counter-side levels by intrinsic quality (dol-C) |
| R-v2-21 | Terminal HUD and panel (2227-2248, 2309-2433) | Design | Becomes the optional debug dashboard (spec §17), without the dropped readouts |
| R-v2-22 | Alerts (2079-2093) | E | Richer content (TE8); no sweep alert for unannounced targets; add the spec §18 set |
| R-v2-23 | Theme set (229-291) | Design | Keep Classic + Custom + automatic light/dark ink; Neon, Matrix, Ice and Mono are optional at best |

**DROP**

| ID | Component (lines) | Class / grade | Reason |
|---|---|---|---|
| X-v2-1 | `f_changed` (865-866) | — | Unused |
| X-v2-2 | Unused tuple outputs (923-925): `htfProtH/L`, `stfProtH/L`, `exePv*`, `exeHV/LV`, `exeProtH/L` | — | Unused (wire `protH/L` into R-v2-1 instead) |
| X-v2-3 | ETA\|hit (2116-2127, 2240) | C | Biased by construction: about 9 bars shown at 2 ATR where the true median is 19-25 |
| X-v2-4 | "heat" p80 MAE of hits (2404-2408) | C | Hits only: 1.6-2.3 ATR vs 3.2-5.1 ATR over all trials |
| X-v2-5 | EV readout (2245-2246, 2359-2363) | C | Shows −0.62R to −0.97R where the martingale truth is 0 |
| X-v2-6 | L50 rolling hit % (2395-2396) | C | Moves with target distance, not skill |
| X-v2-7 | Killzone affinity `f_kzAff` (597-602, 1941) and off-KZ hysteresis `kzHx` (163, 976) | C | Time windows null beyond the volatility clock (+0.2 to +0.6 pp) |
| X-v2-8 | Fixed draw levers: `wDraw` 30, counter-draw ×0.5, `dGate` (145, 155-162, 691-693, 1975) | C strong null | D at 47-54%; D-first costs 3.8-8.3 pp. Replaced by R-v2-3/4 |
| X-v2-9 | VP path multipliers ×1.10/×0.85 (1945-1947) | C | Wrong-signed or null |
| X-v2-10 | HTF Objective ranked without proximity (170-171, 1984-1992, 2160-2168) | C (no test) | Unsupported. Spec §4.7 is covered by the best buy-side and sell-side outputs |
| X-v2-11 | "✕ NO EDGE" and "✓ EDGE" wording (2390) | C | Peeking; "not measurable" is not "no edge" |
| X-v2-12 | Midnight-open anchor as special (220, 964) | C | +0.3 ± 1.1 pp (1,412 instrument-days); keep at most as a plain level |

### 6.2 From the early engine

**PRESERVE**

| ID | Component (lines) | Class / grade | Reason |
|---|---|---|---|
| P-e-1 | Time-anchored drawings with an object budget (`f_mkBox`, `f_mkLine`, `f_mkLbl`, `f_room`, `f_clearAll`, 2032-2060) | E | Avoids far `bar_index` anchors; bounded objects |
| P-e-2 | Auto mode and timeframe ladder never below the chart (`f_ladder` 731, `f_clampTf` 734, 852-873) | E | Fixes v2's TE2 (4H/D charts in Day mode) |
| P-e-3 | PD/PW/PM chart-TF gating (886-888) and the PMH/PML source (1330-1334) | E | Missing in v2; spec §4.1-4.2 |
| P-e-4 | Prediction sampling with overlap weights + Brier skill score (1637-1646; `f_resolve` statistics part 684-688; SKILL 2375-2386) | A strong (proper scoring) | Exactly the per-chart PoT scorecard v2 lacks (QPOT-04, CAL-6); spec §15 |
| P-e-5 | Lock-until-hit + N-bar confirmation (180-181, 1586-1618) | D weak | User-visible stability. Offer as an optional commitment mode with a switch-rate metric (SMC-2) |
| P-e-6 | FIRST race readout (2355-2374), as a concept | A strong (geometry) | Re-implement with zero-drift `f_raceH` |
| P-e-7 | Honest self-reporting: a "This chart" track record after costs; "not proven" tooltips (2431, 2397) | Process | Matches the APEX honesty rules; the user accepted negative results |

**REWORK**

| ID | Component (lines) | Class / grade | What to fix |
|---|---|---|---|
| R-e-1 | Intraday volatility seasonality `sfNow` (937-969) | A strong (the clock is real); gated per chart | Real future-bar calendar; computed once per bar, not per tick; per-chart scorecard gate (fails GC 1H −9.8%, `ict_time` §0.3) |
| R-e-2 | Volatility regime `atrPct` and filter (1022-1025, 276) | A moderate (vol state ±3-8 pp) | Add hysteresis and a compression/expansion state (spec §9) |
| R-e-3 | Cost and tradeability: `f_autoCost` (1051), max-cost-%-of-stop filter (286, 1693-1695), minimum cost stop (1954-1964), sizing `f_perC` (1064, 2408-2412) | A weak (README only: cost < 3% of stop lost about 4× less; not re-run) | Instrument-agnostic: user cost input in ticks, tick size and point value from `syminfo`; mark "incomplete" when the cost is unknown (spec §16). No hard-coded roots |
| R-e-4 | Event calendar (`text_area` 303-306, parse 981-1011) and release windows (291-298) | E (manual windows) | Spec §12 allows manual event windows. Ship without unverified pre-filled dates (or with a verified list); never call it news detection |
| R-e-5 | Spike detector: range ≥ 2.5 ATR AND volume ≥ 3× (1012-1019) | D weak | Rename to "abnormal move" regime flag; not news |
| R-e-6 | Order-flow proxy: sign(close − open) × 1-minute volume via a lower-TF request (1031-1042) | D proxy; A weak (≈ 0.05R, not significant) | Optional, labelled "volume-delta proxy (no bid/ask)", data-quality weighted, never default (spec §7) |
| R-e-7 | Signal hours, flat at 15:55 NY (283, 1046-1048, 331, 1058) | E (sessions) | Configurable session close and core hours per instrument (spec §2.1) |
| R-e-8 | Sweep queue (1708-1740) | D definition | Keep as a sweep *event* detector feeding the lifecycle (spec §4.6), not a reversal entry |
| R-e-9 | Garman-Klass + close-to-close σ (896-911); drift `mu` (909-910) | A weak (+0.28% LL, n.s.) | Optional σ; drift → 0 |
| R-e-10 | Empirical store with decay (432-452, 1158-1174) | A | Merge the forgetting-factor idea into v2's surface; overlap-aware n |
| R-e-11 | Table rows ALIGN, NEWS, VOL (2316-2421) | Design | Move to the debug dashboard |
| R-e-12 | OB → breaker on any close through (1432-1455) | D | Closer to the template than v2's gate; merge with R-v2-14 |

**DROP**

| ID | Component (lines) | Class / grade | Reason |
|---|---|---|---|
| X-e-1 | Logistic PoT layer with hard-coded weights `lrW0`, online SGD (478, 672-697, 1098-1103, 1549) | C (unverifiable fit; ungated) | Weights cannot be reproduced. The study finds ungated learners lose to the baseline on clean data. Replace with gated Platt |
| X-e-2 | Priority = 0.65·score + 0.35·PoT (185, 1550) | C | Mixes a heuristic score with a probability |
| X-e-3 | "Never leave the chart without a DOL" (1583-1585) | C | Neutral is a legitimate output (spec §13.3, §25) |
| X-e-4 | Target Win Rate mode, `kAdj` (314-316, 1900-1901, 1984-1987) | A (controller works) / no edge | The high win % comes from tiny targets; about 0R before costs |
| X-e-5 | Edge Gate and 10-size shadow replay (320-322, 1754-1799, 1966-1999) | C | Picks the best of 10 sizes in-sample. Reported: 10 trades −2R (NQ), 70 trades −8R (S&P) |
| X-e-6 | DOL Direction and Sweep Reversal trade modes as signals (265-266, 1918-1945, 1975-1983) | C (tested) | −0.02R (n 1,235); −0.06R (n 1,350); the +0.09R variant (n 357) is window-specific |
| X-e-7 | Default "BUY NOW / SELL NOW" banner with contract counts (2423-2464) | Design / C | Encourages trading on a signal that tested negative (spec §16). At most an optional tradeability panel |
| X-e-8 | Confluence from counting source names; +0.08 per extra flag (493-520, 1505, 1527-1531) | C | Double-counts one price region (spec §5) |
| X-e-9 | 0.85^touches and mitigation penalties (199, 1541) | C (no evidence) | Untested fixed levers |
| X-e-10 | Unused `f_flagW` (490), `xSH..xSLW` (922), `rH/rD` (1187) | — | Dead |
| X-e-11 | Magenta DOL colour (353) | Preference conflict | The later preference (v2, screenshot) is neon green/red |

### 6.3 From Liquidity Flow Pro

**PRESERVE**

| ID | Component (lines) | Class / grade | Reason |
|---|---|---|---|
| P-l-1 | Three-way commit outcome sweep / taken / test with a penetration band; Strict, Balanced and Aggressive modes (784-837, 139-140) | D definition; wick-depth stats A moderate | The clearest lifecycle primitive (spec §4.5-4.6). Calibrate the band to the measured wick depths |
| P-l-2 | Bounded-span clustering with members, hi/lo and same-point dedupe (`f_addLevel` 461-503) | D/E | Identifiable constituents, no chain drift (spec §4.4) |
| P-l-3 | First-partial-period discard (`f_period` 554-585, `f_session` 590-623) | E | Fixes v2's rp-partial-pwh |
| P-l-4 | Chart-TF gating of D/W/M levels (674-676) | E | Fixes v2's TE5 |
| P-l-5 | Volume-quality detection `volOK`, auto-ignore of volume terms (299-302, 337, 891) | E | Spec §13.2 data-quality weights; v2 silently fails on zero volume |
| P-l-6 | LOW DATA shrink to neutral (1045-1051) | E/A principle | Spec §25: "when data is missing, reduce confidence" |
| P-l-7 | Freeze current-bar option (104-105, 876-878) | E | Spec §19.1: provisional vs confirmed |
| P-l-8 | Display-only live "RAIDING / BREAKING … LIVE" status (994-1004, 1507-1511) | E | Honest provisional state |
| P-l-9 | Pool-owned drawings with fade on sweep (239-265, 397-455) | E | Object lifecycle hygiene (spec §19) |
| P-l-10 | HH/LH and HL/LL typing; protected swing → structural (694-695, 723, 733, 853-868) | D definition | Spec §3 |
| P-l-11 | "Not a probability" wording of the header and tooltips (12-17, 1425, 1456) | Process | Matches the APEX rules |

**REWORK**

| ID | Component (lines) | Class / grade | What to fix |
|---|---|---|---|
| R-l-1 | External swings at 3× length (741-752) | D | Internal/external structure (spec §3) without a score bonus |
| R-l-2 | Bounded tilts ≤ 1.25× (896-919) | Principle E; tilts C | Keep the cap principle for any secondary factor; tilts neutral until measured |
| R-l-3 | Model confidence (1082-1091) | D, no validation | Rework into a documented data/forecast-quality indicator (spec §13 F); never shown as % certainty |
| R-l-4 | Faded swept pools with depth (432-455) | E | Add time-to-sweep; feeds the honest ghost trail |
| R-l-5 | Session defaults (132-135) | E | Unify with v2's configurable sessions; fix 1H bar-open membership |

**DROP**

| ID | Component (lines) | Class / grade | Reason |
|---|---|---|---|
| X-l-1 | Side-share % as a directional forecast; Video "▲ UP / ▼ DOWN" zones (54-65, 1300-1341; README 23-24) | C, none | No predictive test. On random walks it flips about every 68 bars and is "EXTREME" on 7.35% of bars. Also large background fills (spec §17) |
| X-l-2 | "Sellers / Buyers" wording (59-61, 1320-1321) | — | Mislabels |
| X-l-3 | Tests strength bonus (336) and the fixed cluster multiplier 1/2.25/3.5/4.75 (335) | C / A weak | Tests show about 0 effect; EQ is weak; spec §4.4 |
| X-l-4 | Sweep + shift + flow signals (1163-1182) | C (untested; analogue MSS 49.4%, n 4,032) | No outcome evidence |
| X-l-5 | "the pull is used up and price often turns" tooltip (1324) | C | Contradicted: no reversal edge after sweeps |
| X-l-6 | `adxVal` (885) | — | Unused |

---

## 7. Map of v2 onto APEX spec modules (sections 3-18)

Status: **EXISTS** (meets the spec in substance), **PARTIAL**, **MISSING**. "Better legacy source" names where a legacy engine already has a usable piece.

| Spec § | Requirement | v2 status | v2 lines | Better legacy source | Gap notes |
|---|---|---|---|---|---|
| 3 | Swings, internal/external, HH/HL/LH/LL, BOS/CHoCH/MSS, displacement, failed breaks, compression/expansion, premium/discount, dealing ranges, knowable-at | PARTIAL | 708-782, 898-904, 888-891, 2329-2332 | LFP HH/LL typing and external swings; early BOS/CHoCH events (`SEvt` 144, 1201-1216) | No explicit events or labels; CHoCH lag; ties; no failed breakout/breakdown; P/D in Terminal only; no knowable-at timestamps |
| 4.1-4.2 | BSL/SSL: PD/PW/**PM**, sessions, swings, EQ, relative EQ, clusters, range, **opening range**, historical extremes | PARTIAL | 945-961, 1752-1822 | Early/LFP: PMH/PML | Missing PM, opening range, IPDA-style extremes, relative EQ across key levels; NY PM session |
| 4.3 | Internal liquidity: FVG boundaries, displacement origins | PARTIAL | 907, 1663-1748 | — | No retracement liquidity |
| 4.4 | Clustering with tick/ATR tolerance, constituents, touches, age, time between touches, freshness, prior sweeps, reactions, acceptance, status | PARTIAL | 1090-1131, 1230-1251, 650-658 | LFP `f_addLevel` | No constituent list; no reactions or acceptance; the test bonus contradicts "touches must not add strength" |
| 4.5 | 10-state lifecycle | PARTIAL (implicit) | 1558-1596, 1566-1577 | LFP sweep/taken/test; early ghost reasons | States not stored: no Approaching, Reclaimed, Rejected or Accepted |
| 4.6 | Sweep intelligence (probe vs reclaim vs acceptance vs failed break; follow-through) | PARTIAL, wrong use | 1580-1582, 1504 | LFP 784-837 | Wrong-signed D mapping; no follow-through measurement |
| 4.7 | Ranking with path barriers; best buy-side AND sell-side; ticks, ATR, score, reason codes, state; "Draw Score" naming | PARTIAL | 661-696, 1964-2035 | — | One target only; no ticks; reason codes only in the tooltip; FVG path barrier missing; called "score" next to a "PoT" label |
| 4.8 | Destination vs post-target reversal as separate processes | MISSING | — | — | v2 conflates them through `liqEvt` |
| 5 | FVG, iFVG, OB, breaker, mitigation block, BPR, void, displacement, OTE, CE, invalidation, expiry, no double-counting | PARTIAL | 907-912, 1598-1748, 785-796 | Early in-place transitions | Missing mitigation blocks, BPR, voids, OTE; breaker definition wrong; self-confluence double count |
| 6 | Wyckoff/AMT proxies (balance, acceptance, value migration, IB, opening auction) | MISSING (VP only) | 1384-1424 | — | Study: AMT bias rules carry no information beyond distance (`amt_profile` §0.4), so build them as labelled proxies at most |
| 7 | RVOL, volume percentiles, VWAP (session, anchored, rolling), VAP, POC/VA estimates, volume around sweeps | MISSING (VAP partial) | 978-1015, 1384 | LFP RVOL/`volOK`; early RVOL | No VWAP or RVOL; zero-volume handling missing |
| 8 | EMA/RSI/MACD/ROC/DMI/ADX/regression, redundancy handling | MISSING | — | LFP pressure (CLV, ROC, DMI); early momentum | Spec treats these as supporting features with redundancy control |
| 9 | ATR percentile, realized vol, regimes with hysteresis, compression/expansion | PARTIAL (weak) | 874-878, 888-891 | Early `atrPct` regime (1022-1025) | No regime classifier and no hysteresis |
| 10 | Statistics toolbox | EXISTS (strong core) | 400-503, 1265-1336, 1461-1499 | — | Add robust stats, calibration curves, Brier/log-loss scorecard |
| 11 | MTF hierarchy, modes, safe requests, provisional vs confirmed, disagreement → neutral | PARTIAL (strong core) | 60-82, 564, 923-936 | Early Auto mode + ladder | Auto-fit to chart TF; a provisional HTF state; no confidence reduction on disagreement |
| 12 | Intermarket, rolling correlation, manual event windows | MISSING | — | Early manual event windows | Optional reference symbols must fail soft |
| 13 | Regime, bias, buy-side, sell-side, setup quality and forecast quality scores; STRONG BUY..STRONG SELL; FAST/BALANCED; data-quality weights | MISSING (only D and per-level scores) | 1891-1898 | LFP side aggregation and LOW DATA | D has no skill; no signal states |
| 14 | One conditional forward path (20-120 bars, default 60), green/red, uncertainty | MISSING | — | v2/early reach bands are a seed for the uncertainty band only | Nothing resembling a path exists |
| 15 | Calibrated probabilities, Brier, log-loss, calibration, baselines | PARTIAL | 1303-1322, 1426-1499, 2374-2430 | Early SKILL scorecard | PoT never graded; verdict peeks; biased readouts |
| 16 | Costs, slippage, tick size, stop vs costs, R:R, insufficient-move detection | PARTIAL | 1343-1364 | Early cost/stop/sizing | No costs anywhere in v2 |
| 17 | Clean default with BUY/SELL markers + one path; diagnostics off | PARTIAL | 2214-2226, 2295-2307 | — | Look matches the reference but has no markers or path; 76 inputs in the legend; iFVG clutter |
| 18 | Alerts: BUY, SELL, STRONG, neutral transition, new target, target reached, sweep, reclaim, forecast changed/invalidated; no duplicates | PARTIAL | 2079-2093 | Early 13 alertconditions; LFP rich `alert()` | Has new target, sweep (live), iFVG, flip. Missing signal states, reclaim, forecast alerts |

---

## 8. The user's evident preferences, and conflicts with the APEX spec

**Preferences (sources: HANDOFF, CONTEXT, the reference image, the three READMEs, input defaults):**
- **Look.** Dark chart, neon Classic palette (buy-side #39FF14, sell-side #FF1744, bias green #00C864, bias red #E63C3C), black panels. One dashed target zone with a glow core anchored at its origin candle, a dashed tether, and a dark "Target: CODE / PoT: x.x%" label. A compact "Timeframe | Bias" table (D/4H/1H; BULLISH/BEARISH). Dark-green iFVG boxes. Uncluttered: "Simple View" and "Clean" are the defaults in two products.
- **Modes.** Scalping, Day Trading (the default), Swing and Custom; Auto from the chart timeframe in the early engine.
- **Instruments.** Gold futures 5m (the screenshot), MNQ/MES/NQ/ES on 1m/5m (early), and XAUUSD (another legacy file name).
- **Wording.** Plain trader terms: Target, PoT, BSL/SSL, BUY-SIDE/SELL-SIDE, BULLISH/BEARISH, short codes (BEFVG, BUOB). Tooltips carry the detail. The user writes informally, is a trader rather than a programmer, wants short plain replies, and wants the final script pasted in one code block plus the file.
- **Trading workflow (early).** BUY/SELL with entry, stop and target; $-risk sizing; a daily loss limit; one trade at a time; core NY hours.
- **Honesty.** Every product title says "Non-Repaint" or describes non-repainting. The READMEs report losing results plainly ("Nothing tested here is reliably profitable on its own") and carry "not a probability" and "not a guarantee" disclaimers.
- **Intensity.** "SO BAD … 100000X BETTER", maximum effort, willing to wait.

**Conflicts the architect must resolve:**
1. **"PoT: 70.1%" vs spec §4.7/§15.**
   - The reference label shows a probability; the spec allows that only for an empirically calibrated outcome frequency with a defined target, sample and horizon.
   - The PoT has a defined target (touch of the near edge) and horizon (H bars), and its model class is well calibrated in aggregate on study data (slope 0.93-1.04, 13 clean sets, 76,181 probes). But it is ungraded per chart, carries the drift bias, and is hour-biased by up to ±17 pp on 5m.
   - **Recommendation:** keep the label slot (user preference), but show the value as a probability only after the per-chart scorecard passes. Otherwise mark it as a model value (for example "PoT (model)"), with H and n in the tooltip.
2. **Default display.** The spec requires BUY/SELL markers plus one green/red forward path. The reference has neither, but has the zone, label and table. They can coexist: the path colours match the Classic palette. Keep the table (it is in the reference) despite "no unnecessary tables".
3. **The early engine's BUY NOW banner, blue/red-for-trades and magenta DOL** conflict with the later neon green/red choice and with spec §16 ("should not encourage trading simply because a directional signal exists").
4. **LFP's directional percentages and large Video zones** conflict with spec §17 (no large background fills) and with the scores-are-not-probabilities rule.
5. **Instrument specificity** (early: root-symbol cost table, NY hours, 15:55 flat, "tuned for 1m/5m") conflicts with spec §2.1 (universal, no NQ-specific calculations).

---

## 9. Open questions and unverified items for the architect

1. **Compile status** of `00a405a`, the early engine and LFP on TradingView is unverified. HANDOFF says the user tried "an earlier version" and reacted "SO BAD"; it is not recorded which file or whether it compiled.
2. **The early engine's research scripts and data are absent.** Its numbers (26 datasets; 3.7-year MNQ/MES) are README claims only. They agree with the study, which strengthens them, but they cannot be re-run.
3. **The 24 pre-filled FOMC dates** in the early engine are unverified; I did not fetch the Federal Reserve calendar.
4. **46 of 49 overhaul findings are "not yet verified".** Their exact patches live in `dev-notes/runs/overhaul-r1-journal.jsonl`, which I did not read.
5. **HANDOFF's "midnight open is the only time anchor with excess revisit"** is superseded by the final `ict_time` report (+0.3 ± 1.1 pp, 1,412 instrument-days).
6. **Runtime budget on 20k-bar 1-minute charts** is unmeasured for all three (`pine_eng` PENG-2: "probably low").
7. **Spec §14 (forward path) and §13 (signal states)** have no implementation in any legacy engine. No test anywhere supports a directional edge that such a path could draw on. Given the tested nulls, the path must be built as an honest conditional scenario with uncertainty, defaulting to neutral when evidence is weak (spec §25).
