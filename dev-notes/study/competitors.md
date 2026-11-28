# Competitive landscape: study for DOL Engine v2

Domain: commercial and free liquidity / draw-on-liquidity (DOL) / target tools on TradingView and other platforms. The report covers their public feature descriptions, scoring rules, probability displays, alert designs, dashboards, UI conventions and user praise or complaints. It then compares them with `baseline_v2.pine` and proposes improvements.

This report merges two passes on the same domain:
- the earlier working notes in `study/competitors_notes/notes.md` (marked **[N1]** where a fact was taken from them and not re-checked);
- this pass's notes in `study/competitors_notes/notes_b.md`, with verified re-reads of the key competitor pages (ASXLT, AGPro, ForexCracked, the reference product page, ProEA, LuxAlgo DOL, ICT Order Block Pro, ICTMIKA).

Rules respected: public descriptions only, no code or long passages copied, no product branding reused. All line numbers refer to `brief/baseline_v2.pine`.

---

## 0. Executive summary

1. **The engine is already ahead of almost every competitor on substance.** No surveyed tool combines multi-source pools, PD arrays, a multi-pillar score, an empirical PoT and a self-grading ledger against a distance-matched random baseline. The two "measurement-first" tools come closest: ForexCracked's *Liquidity Draw Probability Map* (2,239 boosts) and Flux Charts' *Liquidity Sweep Profiler*. Both measure per-category reach or edge, but neither commits to one target or tests against a random-level null. Most DOL tools pick the target with a one-line heuristic:
   - nearest opposing pool (ICT Order Block Pro, ICT doctrine);
   - tier weight ÷ ATR distance (LuxAlgo *Draw on Liquidity*: W 4, D 3, session/EQ 2, gaps 1.5, swings 1);
   - a volume-weighted side share of at least 55% (HS_16 *Liquidity Draw*).
2. **Where the engine loses is UX hygiene, not analytics.**
   - **Status line:** the engine's legend shows 75 input values, because no `input.*` call sets `display`. The reference screenshot shows only the script name.
   - **Clean label:** it gives a probability to one decimal with no horizon and no sample size, and it reads "PoT: 95.0%" on a target that has already been reached (line 2067).
   - **Alerts:** they carry static text only, with no approach alert, no "target abandoned" alert and no machine-readable payload.
   - **Light charts:** the Classic neon palette is unreadable on a white chart (lime `#39FF14` on white is 1.36:1).
3. **The best tools converge on six conventions:**
   - one committed target confirmed at bar close;
   - an explicit **balanced / no-draw** state instead of a forced pick (AGPro v1.2);
   - a probability **with its horizon and its sample size** next to it ("reach X% of N", "13 of 15");
   - level lifecycle states (rest → swept → broken) with faded "ghosts";
   - distance filtering, so far levels never clutter or compress the chart;
   - few, deduplicated, filterable alerts, available as JSON for webhooks.
4. **One thing no competitor does, and the engine is well placed to do: benchmark itself against the simple rules competitors ship.**
   - The M4 forecasting competition found that only 17 of 50 submitted methods beat a simple combination benchmark.
   - The engine's ledger can already grade any selector. Running "nearest draw-side pool" and "tier ÷ distance" as *shadow selectors* would show users, and us, whether the multi-pillar score earns its complexity.
   - Every later scoring change could then be A/B-tested the same way.
5. **User voice (Reddit, TradingView comments) asks four things:**
   - which DOL is active, *when* it will be reached, and on which timeframe;
   - where to take profit;
   - consistency ("some weeks perfect, some weeks wrong");
   - a clean chart. One complaint about a liquidity tool was "it shrinks my chart so I cannot see any candles", which is autoscale compression from far drawings.

   Nearly all 259 comments on the reference product are trial requests, so it has no public complaints to learn from.
6. **Proposals (best first; details in §4):**
   - COMP-1 (P1, S): clean status line and input hygiene.
   - COMP-2 (P1, M): alert system (approach, abandoned, reached-at-close, per-event toggles, JSON, `{{plot()}}` placeholders).
   - COMP-3 (P1, M): shadow-selector benchmark in the ledger.
   - COMP-4 (P1, S): honest Clean label (reached state, horizon, natural-frequency tooltip, runner-up).
   - COMP-5 (P2, S): outcome stamps.
   - COMP-6 (P2, S/M): balanced / no-draw state with a coverage metric.
   - COMP-7 (P2, S): price-scale target tag, distance units, autoscale safety.
   - COMP-8 (P2, S/M): automatic light-theme contrast.
   - COMP-9 (P3, M): Pine Screener columns.

   Out of scope because other study reports cover them:
   - ledger-calibrated PoT (SMC-1, TIME-2);
   - target lock mode (SMC-2);
   - clock-time horizon / PoT by session end (TIME-4);
   - honest sweep-outcome alerts (ICT-2);
   - path resistance (ICT-5);
   - "which pool first" (ICTS-3, BIAS-1).

   COMP-2, COMP-4 and COMP-6 are the display and alert layers for those analytics; coordinate with them.

---

## 1. Concepts (definitions and parameters)

### 1.1 How competitors choose the one target (target-selection families)

| Family | Precise rule (as published) | Parameters | Who | Failure modes |
|---|---|---|---|---|
| **Nearest opposing pool** | Target = the closest untapped pool on the bias side, or opposite the setup. ICT doctrine: "the NEAREST significant pool in the direction of the bias – not the most distant", matched to trade duration. | Pool set; bias source; "significant" undefined | ICT Order Block Pro (DivergentTrades, open source, 1.1K boosts): dashed DOL line from a validated OB to the closest opposing BSL/SSL. theinnercircletraders.com DOL guide. | Ignores pool quality. A cluster of tiny swings wins over PDH. Flips whenever price crosses a level. |
| **Tier ÷ distance** | `score = tierWeight / distATR`. The best score on the structure-bias side is the "working draw"; it falls back to the other side when the bias side has no pools. On a sweep it re-anchors to the next objective. | Tiers: weekly 4, daily 3, session and equal extremes 2, gaps 1.5, swings 1. Swing length 10; EQ tolerance 0.1 ATR; minimum gap 0.5 ATR; maximum pool age 500 bars; structure length 50; sessions Asia 18:00–03:00, London 03:00–09:30, NY 09:30–16:00 (NY time). | LuxAlgo *Draw on Liquidity* (free, also on their own charting platform) | Diverges as distance tends to zero, so the nearest level always wins once price is close. No probability. Repaint FAQ: merged EQ pools move the whole line to the outermost swing. |
| **Per-side aggregate with states** | Each side gets a 0–100 score built from pool quality (cluster strength, prior-period status), proximity in ATR, trend "backbone" context and freshness. The four states are below. | Two-Sided Balance Gap input; ATR range for the reference-pool map | Draw On Liquidity Planner (AGProLabs, open source) | Needs a well-chosen gap; trend context is an EMA slope. |
| **Volume-weighted side share + lock** | Liquidity is grouped above and below price on an HTF (15m) and weighted by volume. The side holding at least 55% is chosen. The target is **locked** on a closed candle until it is reached, the stop breaks, or N bars pass. | Minimum liquidity %, PoT horizon, minimum PoT, SL buffer, minimum SL distance, minimum R:R, lock duration, result display duration | Liquidity Draw (HS_16, open source) [N1] | The lock can hold a dead target; built for 1m charts. |
| **PoT × quality × bias, confirmed at close** | Selects on "theoretical Probability of Touch, level quality, market bias and other scoring factors". "Primary target selection is confirmed at candle close to reduce unnecessary intrabar switching." | PoT horizon: 24 chart candles, 24 minutes, 1 hour, 4 hours, custom | ASXLT DOL (invite-only, Oct 2026) | Admits that its PoT "is not an empirically validated prediction". |
| **Learned side probability** | Online logistic regression on 8 features (trend, displacement, premium/discount, recent sweeps, distance to BSL/SSL, structure) gives P(buy-side pool reached before sell-side within N bars). Each confirmed bar is labelled by a pool-to-pool barrier race; unresolved samples are discarded. A UCB bandit tunes the threshold per regime. | N, learning rate, features | AetherEdge Smart Money Flow (open source) [N1] | Overfitting on small samples; opaque to users. |
| **Session-sequence statistic** | P(overnight high vs overnight low is broken first by 11:00 NY), from a 2016-to-present dataset per market (NQ/ES/YM/GC). The table adds midnight-open relation, 09:30 quadrant, sequence and overnight range %. A "Daily Streak" counter tracks consecutive correct first-break calls. | Fixed dataset | P2P 86 Model Probability Map (protected, 4.5K boosts) [N1] | Static dataset; only 4 markets. |
| **Multi-pillar weighted score** | Proximity, freshness, confluence and density pillars (the reference product). The engine adds a fifth pillar, draw vector D, and multipliers. | Weights, gates | Reference product, this engine | Complexity has to justify itself against the simpler rules above (see COMP-3). |
| **Anti-pattern: confidence score called "probability"** | Daily highs and lows not yet revisited are clustered into a 0–100% "probability" with bands (90–100 very high …). It is a heuristic confidence, not a frequency. | | ICT/SMC DOL Detector PRO (NeverWishing) [N1] | Misleads users; TradingView publishing rules require accuracy claims to be substantiated. |

AGPro's four states:
- **Buy-Side Draw** and **Sell-Side Draw**: one side dominates with a qualifying score.
- **Two-Sided**: "both sides are roughly balanced", meaning the score gap is below the *Two-Sided Balance Gap*.
- **No Draw**: "no qualifying untapped pool is currently in range".
- In v1.2 the runway, target, invalidation and right-edge tags show only for qualified one-sided draws, "so balanced or low-score conditions no longer force a directional plan".

**How practitioners use the target.** Every DOL tool presents the target as the take-profit or objective, with entries taken from a PD array toward it ("The DOL is where price is going. The PD array is where you get in."). Users explicitly ask for it: "What I have problems with, is where to set a take profit" (r/Daytrading, 147 upvotes).

### 1.2 Target commitment and stability

- **Confirm at close** (ASXLT, AGPro, reference product, engine): target changes only on confirmed bars; the PoT text may update live.
- **Lock until resolved** (HS_16): no challenger can replace the target until it is hit, stopped, or N bars pass. Covered by SMC-2 in `smc_impl.md`.
- **Hysteresis with a challenger streak** (engine): the challenger must beat the incumbent by `hyst` points (twice that across sides) for 2 consecutive bars (lines 2011–2020). The off-killzone multiplier is `kzHx` (line 976).
- **Event-label cooldown** (AGPro): flip and sweep markers are throttled. The default cooldown went from 20 to 52 bars in v1.2, and draw changes take priority over same-bar sweeps.
- **Failure mode the user may have seen:** the target "jumps around". The engine has the strongest anti-jump logic surveyed apart from a hard lock. It does not *report* its own switch rate, though; SMC-2 proposes a switch-rate metric.

### 1.3 Probability displays: definitions and conventions

| Display | Definition | Example | Notes |
|---|---|---|---|
| **Theoretical PoT (first passage)** | P(max over the horizon ≥ level) for a random walk, from log-return volatility, distance and horizon. With no drift the reflection principle gives P(touch) = 2·P(end beyond), the options rule of thumb "PoT ≈ 2 × P(ITM)". | ASXLT; thinkorswim "Probability of Touching"; tastytrade | The horizon is always explicit: expiry in options, "24 minutes / 1 h / 4 h" in ASXLT. |
| **Empirical PoT** | Fraction of past windows of length L in which price exceeded mark + level (in points, % or σ). | `probability_of_touch` (taylor_o, open source, 1.3K boosts): start/end date filters; a debug "X" marks the periods that touched. | Precedent for the engine's empirical surface (`f_empPoT`, line 1284). |
| **Measured reach frequency by category, with n** | For each pool category × birth distance (ATR bucket): reached within 50 bars (horizon capped at 60); touches split into **rejected** (close ≥ 1 ATR back inside within 20 bars), **cut through** (close ≥ 0.5 ATR beyond) and **stall**. A figure prints only when n ≥ 20; below that the label reads "building" with the count. Labels read "reach X% of N", "cut Y% of T touches". Line thickness and solidity rise with the category's reach frequency. | ForexCracked *Liquidity Draw Probability Map* (2,239 boosts; updated Oct 2026) | Version fixes: reach counted only after the window has elapsed (right-censoring); PD/PW read from the just-closed period on every bar (history vs live mismatch); pools already traded through at birth are not added; highs and lows counted separately. |
| **Conditional on open location** | Touch probability per pivot level, conditioned on where the session opens; source data is session-specific. Advice: "focus only on levels with strong probabilities (50%+) and hide the rest". | edgeful pivot report and "What's in Play" dashboard [N1]: 6-month lookback, threshold slider (60–65% recommended), "view details" shows n and k (e.g. 13 of 15 = 87%) | Natural frequencies shown on demand. |
| **Averaged price *and time*** | Historical average manipulation and distribution levels per session, plus the **average time** each phase completes. A table shows how many past sessions are averaged. | toodegrees *Session Statistical Mapping* (Pro+) | Values change with chart timeframe (stated limitation). |
| **Cap** | PoT is capped at 95% (reference product, engine). | | Avoids certainty language. |

Display precision matters:
- Precise numbers are read as a signal of confidence: answers with more digits were judged more confident, and precise advisors were preferred (Jerez-Fernandez, Angulo & Oppenheimer 2014).
- Weather services publish probability of precipitation in 10% steps (Environment Canada) or 5% steps (UK Met Office). NWS wording bands: 20% "slight chance", 30–50% "chance", 60–70% "likely".

The reference look shows "PoT: 70.1%". Keep that format for fidelity, but put the calibration evidence next to it (COMP-4).

### 1.4 Level lifecycle states

| State | Rule (best published definition) | Display |
|---|---|---|
| **Rest** | Untouched since birth. Born when the defining period or candle closes. | Solid line or zone |
| **Swept** | A wick trades through **and** the bar closes back on the original side, within a confirmation window. Flux: window W bars, where 0 = same bar. ProEA: decided on the closed candle. | Stays on chart, marked (ProEA ⚡, ICTMIKA "LG" liquidity grab) |
| **Broken** | Close beyond the level, or the confirmation window expires without a close back (Flux "broken, not a sweep"). A swept level that later gets a close beyond becomes broken (ProEA). | Line ends at that candle, faded |
| **Ghosted** | Swept or invalidated levels kept at low opacity. ICT Order Block Pro drops the line and text to 25% opacity "the exact moment a candle sweeps". LuxAlgo "Keep Swept Pools" and "Draw History Path" are off by default. The reference product has a "Ghost Trail". | Faded |
| **Past window** | Untouched after the reach window; it no longer borrows category statistics (ForexCracked). | Faded, tagged "past window" |

ProEA read the code of the 15 most-boosted PDH/PDL scripts (31 Oct 2026). None of the 15 tells a sweep from a break, and several leak or lag:
- sbtnc, 6,172 boosts: `lookahead_on` without `[1]`, so on a live chart a new day keeps its first candle's high and low until reload;
- Bankulov and ceyhun: `[1]` with lookahead off, so history runs one day late.

The engine:
- removes a liquidity pool on a strict trade-through (`touched`, line 623);
- folds the raid outcome (hold vs reject) into D (lines 1580–1582);
- ghosts the target as "✕ SWEPT", "⊘ EJECTED" or "⊘ INVALIDATED" (lines 1586, 2023), off by default.

It does not show swept-vs-broken to the user. That logic belongs to ICT-2 (`ict_liq.md`), so this report proposes only the display side (COMP-5).

### 1.5 Self-measurement ("keeps score")

| Tool | What is measured | Rules | Display |
|---|---|---|---|
| ForexCracked map | Reach %, median bars to reach, reject / cut / stall split per category and distance | See §1.3; minimum sample 20 | Sample size printed next to every figure; dashboard lists nearest pool above and below (type, ATR distance, reach %, median bars, n), Net Draw Bias, last purge and its resolution, totals |
| Flux Charts *Liquidity Sweep Profiler* (open source, 4.9K boosts) [N1] | After each sweep, the maximum recovery and maximum breach in ATR within a 20-bar watch window; **Edge = average recovery ÷ average breach** per level type | Minimum 5 samples; edge cell green ≥ 1.5, neutral 1–1.5, red < 1. Quality filters: relative volume ≥ 1.5×, wick ≥ 50%, LTF delta ≥ 60% | "Best-edge" banner; Active Sweep Tracker label (bars x/Y, live recovery/breach vs baseline); unit ATR / Price / Pips / Ticks; alert "high-edge sweep" (edge ≥ threshold, n ≥ 5) |
| P2P 86 Model [N1] | Daily first-break call | — | "Daily Streak" counter |
| Strong FU Candle [ProjectSyndicate] [N1] | Per-side leaderboard | — | Win rate, PoT, average win/loss bars, R:R, n, EV |
| ProEA desk [N1] | Base rates | — | Banner "BASE RATES ON THIS CHART · DESCRIPTIVE, NOT PREDICTIVE" |
| **This engine** | Hit rate of every asserted DOL over H bars vs a **distance-matched random-level baseline**; Wilson 95% interval; cluster-robust z; rolling last-50 hit rate; bars to hit; heat (p80 MAE); first-touch race vs invalidation; per-family rates; adaptive calibration | Lines 1426–1500 (trials), 2376–2430 (panel) | Terminal only. Clean users see none of it. |

No competitor compares against a null, and none compares its own selector against the simple rules other tools use. The engine already does the first; COMP-3 adds the second.

### 1.6 Dashboards

- **Row conventions:**
  - ASXLT: directional bias, HTF context, primary target, PoT, distance, upside/downside route condition (CLEAR / LIQ / BLOCKED / INSIDE), alternative targets, last confirmed sweep (level, price, elapsed time).
  - AGPro: a full-width "analytical question" header, then state, draw score, target, distance, pool type, invalidation, and **ACTION**: concise state-aware instructions for active, balanced, low-score and no-pool conditions.
  - ICTMIKA (bottom-right): BIAS, PHASE (PO3), OPEN (premium/discount vs midnight open), STATUS ("BUY/SELL ZONE" when factors align in a killzone), DOL.
  - LuxAlgo DOL: bias and whether the draw is aligned with it.
  - Reference product: Timeframe | Bias (D / 4H / 1H).
- **Controls:**
  - Flux: 9 positions, 5 text sizes, dark/light.
  - AGPro: font controls up to "Huge".
  - ICT Order Block Pro: global label size Tiny…Huge or Auto; horizontal text alignment so labels do not cover live price at the right edge; "Dynamic" vertical alignment, with bullish text at the bottom and bearish text at the top, to keep labels out of the DOL path.
- **Engine:**
  - Clean table: Timeframe | Bias with a chart-TF warning (lines 2294–2310), fixed `size.small` text (line 609), 5 position options (line 573).
  - Terminal panel: rich (lines 2313–2434).
  - Missing: a text-size option for the table, and cell tooltips, which `table.cell` supports.

### 1.7 Alerts

| Tool | Events | Thresholds / format |
|---|---|---|
| Reference product | New DOL target active; new iFVG formed; DOL target swept | — |
| LuxAlgo DOL | Draw reached (pool purged, re-anchors); draw flips (both directions) | — |
| LuxAlgo Price Action Concepts (paid) [N1] | Every event built in; any `alert()` with message **placeholders** (e.g. `{ticker}`, OB top/bottom, OB volume); Custom Alert Creator with "Match" (AND) and "Step" (sequence) modes, OR operator, alert scripting | alert() messages start with ticker + TF |
| AGPro | Buy-side draw, sell-side draw (with qualifying score), pool swept | — |
| HS_16 [N1] | New target, target hit, invalidation | — |
| ForexCracked | **Approaching** a high-reach pool; pool purged; Net Draw Bias flips | Approach = within **0.25 ATR**, category reach **≥ 70%** with a meaningful sample |
| ProEA desk [N1] | PDH/PDL/PWH/PWL swept (one `alert()` message); "price near a level" | Near = within **0.15 × daily ATR**; **JSON by default**; once per bar close |
| edgeful [N1] | Near a level | Within 10 points |
| Flux sweep profiler [N1] | New sweep; **high-edge** sweep | Edge ≥ threshold and n ≥ 5 |
| ASXLT | Target changes and alerts on confirmed candles | PoT live |

Platform facts:
- **Placeholders:** `alertcondition()` takes a **const string** message (reference/core.md:93). It can embed `{{plot("title")}}` or `{{plot_0}}`…`{{plot_19}}`, and this works for plots with `display.none` (concepts/alerts.md:354–372).
- **Dynamic messages:** `alert()` messages can be built at runtime. The Pine FAQ shows JSON built with `str.tostring()` and recommends "Once Per Bar Close" so realtime ticks do not misfire.
- **Webhooks:** TradersPost's convention is `{"ticker","action","price"}`.
- **Alert budgets** are limited by plan: Basic 0 technical alerts, Essential 20, Plus 100, Premium 400, Ultimate 1000 [N1, TradingView pricing as of 29 Oct 2026]. A single "Any alert() function call" alert that the user can scope by event is therefore valuable.

The engine's alerts (lines 2077–2094):
- four `alert()` calls: new target with tag/price/score/PoT/ticker, new iFVG, live sweep `freq_once_per_bar`, draw flip;
- four `alertcondition()` calls with static text.

The new-target announcement waits until the target passes `minPoT` (line 2071).

Missing:
- approach alert;
- "target abandoned / replaced / ejected" alert;
- a bar-close "target reached" event with result;
- per-event selection for the single `alert()` alert;
- filters (draw-side only, killzone only, minimum PoT for every event) and a cooldown;
- JSON;
- dynamic values in `alertcondition`.

### 1.8 Visual conventions

- **Zone anchored at the origin candle and extended right** (reference: "anchored to the nearest historical candle"; "a sweep is triggered if price touches anywhere within this zone"). Engine: present (lines 2218–2226).
- **Path emphasis:**
  - AGPro "runway" shading from price to target, at high transparency "so it stays subtle and works on both dark and light chart themes";
  - LuxAlgo "magnet gradient";
  - the engine's dashed tether (line 2224).
- **Right-edge tag with the target price** (AGPro). LuxAlgo PAC added price tooltips on previous-period levels (Jul 2025) [N1]. Engine: the label has name and PoT but no price. The price is in the Data Window only (lines 2444–2448) and missing from the tooltip (line 2206).
- **Line style by category:** Flux uses solid for key levels, dashed for sessions, dotted for structure [N1]. ForexCracked encodes reach frequency as thickness and solidity. BigBeluga encodes size as opacity ("more colour = more reaction").
- **Distance filtering and "how many hidden":**
  - ProEA draws only levels within 2 × daily ATR and lists how many are hidden;
  - AGPro shows an ATR-ranged, nearest-first pool map;
  - the Reddit all-in-one tool advertises "distance filtering to keep the chart clean".

  Engine: proximity is 0 beyond `maxATR` (10) and pools are ejected beyond 1.5× that (lines 132–135). The candidate pool is optional (line 2150).
- **Autoscale compression.** TradingView help: "An indicator plots levels far from price and autoscale fits them all"; the fix is "Scale price chart only". An ICT NWOG script recommends that setting. A Reddit user of an all-in-one liquidity tool wrote: "It messes up my chart and just shrinks it down so much so that I cannot see any candles. This is on 1HR TF". Engine exposure:
  - LVN zones span the 120-bar 1H profile (lines 2251–2287) and are not distance-limited;
  - HTF objective (ranked without proximity, but within the pool);
  - reach bands.
- **Light themes.**
  - A user of ICT Order Block Pro complained that the yellow line "I can really [not] see … on my white background".
  - Computed WCAG contrast on white: Classic buy-side `#39FF14` = **1.36:1**, bias green `#00C864` = 2.22:1, LVN `#FFC400` = 1.60:1, sell-side `#FF1744` = 3.85:1. WCAG asks 4.5:1 for text and 3:1 for graphics.
  - Labels with a transparent background and neon text are affected: objective (2166), secondary targets (2189), invalidation (2212), ghost labels (1256), LVN text (2278). So is the white filament core line (2223).
  - The Clean label (`cLblBg`) and the tables use dark backgrounds and stay readable.
- **Event markers.** AGPro: compact markers for flips and sweeps, alternating by side, with ATR offset and cooldown. ICTMIKA: "LG" marker on swept-but-rejected levels.

### 1.9 Legend (status line) and settings hygiene

- Pine `input.*` default `display` is `display.all` for int, float, string, timeframe, session, source, price and enum inputs, and `display.none` for bool and color (reference/input.md:27, 76, 147). Every such input value is printed in the status line next to the script name.
- The engine has **95 inputs; 75 of them print in the legend**, and none sets `display`. The reference screenshot's legend shows only the script name.
- **67 of the 95 inputs have no tooltip.** None of the 10 session inputs has one, and Reddit users ask "from what time to what time are sessions?".
- `active` (input bool) can grey out inputs that do not apply, for example the Custom TFs unless mode is Custom (input.md:28). The engine does not use it.
- Groups are used well (16 groups, lines 42–57).

### 1.10 Repainting and honesty conventions

- **Repainting complaints:** MSS/BOS tags printed on a live candle and deleted when price reverses; alerts fired mid-bar and reversed at close (MQL5 vendor blog). RayAlgo review summary: "signals can lag behind trends, repaint unexpectedly" [N1].
- **What best-practice tools state openly:**
  - which outputs are live (ASXLT and the reference product: "PoT … evaluates unclosed data in real-time");
  - how MTF data is aligned (`[1]` + `lookahead_on`);
  - that probabilities are "theoretical … not independently verified historical success rates" (ASXLT).
- **TradingView publishing rules [N1]:**
  - claims about accuracy must be substantiated;
  - no lookahead;
  - no misleading demos;
  - explain originality;
  - "avoid claims of reverse engineering" of closed-source scripts. The README's wording "independent implementation written from a public feature description" is acceptable; never name the closed product in a published description.

### 1.11 Other platforms

- **Crypto liquidation heatmaps (Coinglass, Hyblock) [N1].** Both estimate liquidation clusters by leverage tier.
  - Coinglass marks KEY LEVELS: the largest cluster above and below within ±1/3/5%, with a side panel of 4 per side and distances, and cumulative "swept if price travels X" curves.
  - It flags *multi-range confluence*: the same price peaking in 2 or more of the 24h/3d/7d/30d ranges.
  - Its own FAQ concedes: "When both sides are bright, it is hard to tell which one price will visit first."

  Lesson: magnitude alone does not predict sequence.
- **edgeful [N1]:** 140+ statistical reports; "What's in Play" dashboard with In Play / Forming / Completed; examples: YM 81% green when PDH breaks, ES PDH break → session closed green 78%.
- **MT5 market vendors:** non-repainting claims, minimalist dots and arrows instead of text badges, a "HUD card", 3-bar vs 5-bar swing debates.
- **NinjaTrader:** ICT drawing tools such as FVG/OB/rejection-block auto-drawers. No DOL selector was found in that ecosystem. TradingView is where DOL selectors compete.

### 1.12 User voice (what traders praise, complain about, ask for)

| Source | Gist |
|---|---|
| r/InnerCircleTraders 1pp1q6y | "how to see what DOL is active and **when** and how will price target that and **what time frame**" |
| r/InnerCircleTraders 1pl85os | "Some weeks I'll have the perfect draw on liquidity the whole week and some other weeks I won't get the draw right a single time." Reply: DOL "is discretionary, but only until displacement gives you the answer." |
| r/InnerCircleTraders 1rgrsic [N1] | "so much trouble finding my DOL … I need like a checklist" |
| r/Trading 1wm8xe2 | No bias, so "taking setups on both sides … chopped up" (argues for an explicit no-draw state) |
| r/Daytrading 1tlvv19 (147 upvotes) | "What I have problems with, is where to set a take profit" |
| r/ICTMentorship 1wfdm14 | All-in-one levels tool; requests RTH gap and NWOG/NDOG "with number of days"; "can't figure out session times"; "shrinks [the chart] … cannot see any candles" |
| r/InnerCircleTraders 1rdau4w [N1] | Wants HTF (15m+) pools on a 1m chart (ITH/ITL, EQH/EQL, PDH/PDL, session H/L, unfilled HTF FVG "most important"). Reply: "why fill the chart with lines? you need one specific DOL" |
| r/Daytrading 1tqju9m | "Many similar scripts but free are already there"; a builder's design notes: ATR-normalised zones, confirmed pivots, invalidate on a decisive **close** through, not a wick |
| r/Daytrading 1kci9y1 | "Just draw them yourselves people. It takes 5 minutes." (Indicators must add something beyond marking levels.) |
| ICT Order Block Pro comments | Text and line colour requests; light-background visibility |
| AGPro comments | "Which timeframe gives the best result to mark DOL?" |
| Trustpilot (LuxAlgo) [N1] | "felt very basic and didn't provide much beyond what's already freely available" |
| Reference product (3.4K boosts, 259 comments) | Almost all "3-day trial" requests; no public complaints. Release notes show its priorities: visuals, PoT (cap 95, live), stricter body-break bias, MTF `[1]` + `lookahead_on`, zones + anchoring, a minimum-PoT filter, LVN off by default. |

---

## 2. Evidence (numbers and sources)

| Claim | Numbers | Grade | Source |
|---|---|---|---|
| Natural frequencies beat probabilities for reasoning | Correct Bayesian inferences 7% (probability format) vs 45% (natural frequencies), Study 1 N = 64. Study 2 complex tasks: 18–22% → 73–81% with frequency training. | **strong** (replicated since Gigerenzer & Hoffrage 1995) | Hoffrage, Krauss, Martignon, Gigerenzer 2015, *Front. Psychol.* 6:1473, pmc.ncbi.nlm.nih.gov/articles/PMC4604268 |
| Precision is read as a signal of confidence | More decimal digits → judged more confident; precise advisors preferred (2 studies) | **moderate** | Jerez-Fernandez, Angulo, Oppenheimer 2014, *Psychological Science* 25(2):633–635; psychologicalscience.org summary |
| Complex forecasters often fail to beat simple benchmarks | M4: only 17 of 50 submitted methods beat the Comb benchmark; the six ML methods ranked 23, 37, 38, 48, 54, 57 of 60 | **strong** | Makridakis, Spiliotis, Assimakopoulos 2018, *IJF* 34(4):802–808; 2020 *IJF* M4 paper |
| Alert fatigue: most alerts get overridden | Meta-analysis of drug-interaction alerts: override prevalence 90% (95% CI 85.6–95.0%), 570,776 prescriptions; review: 49–96% of safety alerts overridden; duplicate alerts up to 98% [N1] | **moderate** (strong in its domain; transfer to trading is an assumption) | journals.sagepub.com/doi/10.1177/14604582241263242 |
| Abstaining improves accuracy at reduced coverage | Selective classification: e.g. top-5 ImageNet error 2% guaranteed with probability 99.9% at about 60% coverage [N1] | **moderate** (ML; mechanism transfers) | Geifman & El-Yaniv 2017, arXiv:1705.08500 |
| Probability of touch vs probability of finishing beyond | PoT ≈ 2 × P(ITM) under driftless Brownian motion (reflection principle) | **moderate** (exact for the model; real prices deviate) | Schwab options probability guide; Option Alpha "probability of profit vs probability of touch"; tastylive episodes |
| Probability wording bands | NWS PoP: 20% slight chance, 30–50% chance, 60–70% likely; Canada rounds to 10%, UK Met Office to 5% | **weak** (convention) | weather.gov forecast-terms pages; Wikipedia "Probability of precipitation" |
| Far levels compress the chart | TradingView help: "My chart looks compressed … enable Scale price chart only" | **strong** (platform documentation of the mechanism) | tradingview.com/support/solutions/43000762934 |
| Text and graphic contrast | WCAG 2.x: text ≥ 4.5:1, graphics ≥ 3:1. Classic `#39FF14` on white 1.36:1 (on `#131722` 13.20:1); `#FFC400` 1.60:1; `#00C864` 2.22:1; `#FF1744` 3.85:1 (computed here) | **strong** (standard) + computed | W3C WCAG 2.1 §1.4.3, §1.4.11 |
| Popular PDH/PDL scripts leak or lag | 15 most-boosted read: none tells a sweep from a break; sbtnc (6,172 boosts) uses `lookahead_on` without `[1]`; `[1]` with lookahead off runs a day late | **moderate** (one code-read, reproducible) | proea.app/en/blog/best-previous-day-high-low-indicator-tradingview |
| Measurement-first tools gain traction | ForexCracked map 2,239 boosts (Oct 2026); Flux sweep profiler 4.9K [N1]; P2P 86 model 4.5K [N1]; reference 3.4K | **weak** (popularity is not accuracy) | TradingView script pages |
| DOL heuristics in shipped tools | Tier/distance (W4 D3 S/EQ2 gaps1.5 swings1); nearest opposing pool; ≥ 55% side share [N1] | **none** (no published accuracy for any of them) | LuxAlgo DOL page; ICT OB Pro page; HS_16 page [N1] |
| Liquidity heatmaps don't tell sequence | Coinglass FAQ: "When both sides are bright, it is hard to tell which one price will visit first" [N1] | **weak** (vendor admission) | coinglass.com/pro/futures/LiquidationHeatMap |
| Statistic examples from vendors | YM 81% green when PDH breaks, 63% red when PDL breaks; ES PDH break → close green 78% [N1] | **weak** (vendor; sample sizes not shown) | edgeful blog |

The forecasting value of every *UX* feature in this report is evidence grade **none** for the forecast itself. These features change how traders read and trust the forecast, not the forecast. The proposals are written so that the engine's ledger measures whatever *can* be measured: approach→hit conversion, shadow-selector edge, coverage vs edge, and PoT reliability.

---

## 3. Engine gap analysis (`baseline_v2.pine`)

| Concept | Status | Lines | What the engine does / what differs |
|---|---|---|---|
| Single committed DOL with bar-close confirmation | **present** | 1963–2035 | Draw-side first, counter-draw fallback, 2-bar challenger, hysteresis (2× for side flips), wider off-killzone (976). Stronger than ASXLT, LuxAlgo or AGPro; softer than HS_16's lock (SMC-2). |
| Multi-source pools (PD/PW/session/STF/HTF/EQ) + PD arrays | **present** | 84–117, 1084–1250 | Broader than any competitor's pool set. |
| Tier ÷ distance / nearest-pool baselines | **missing** (as a benchmark) | — | Tier enters density (`f_tierW`, 506; 682) and proximity is a pillar, but the engine never measures itself against these simple selectors (COMP-3). |
| Random-level null in the ledger | **present** (ahead of the field) | 1314–1323, 1461–1500, 2376–2430 | Distance-matched base rate, Wilson CI, cluster-robust z, verdict. No competitor does this. |
| PoT with explicit horizon | **partial** | 176–184, 1303–1312, 2225 | First-passage + empirical surface, capped at 95%. Horizon H = 30 *bars* is never shown in the Clean label or tooltip, and bars are not clock time (TIME-4 covers the clock horizon). |
| Sample size / natural frequency next to the probability | **missing** | 2225, 2206 | Clean shows "PoT: 70.1%" alone. `n` appears only in the Terminal accuracy header (2379). No PoT reliability buckets exist; SMC-1 and TIME-2 propose calibration, and COMP-4 proposes its display. |
| Reached state in the Clean label | **wrong** | 2062–2067, 2225 | On a live sweep `activePoT := 0.95`, so Clean prints "PoT: 95.0%" for a target already hit. Terminal correctly prints "✕ SWEPT ▸" (2237). |
| Target price and distance in the label or tooltip | **missing** | 2206–2209 | The tooltip lists pillars and multiplier only. No price, no points/% distance, no runner-up. Distance is in ATR in Terminal only (2243, 2351). |
| Balanced / no-draw state | **partial** | 1895, 1975, 2004, 2342, 2367 | `dirSide = 0` internally; Terminal shows "BALANCED" in the DRAW row and "scanning…" when nothing qualifies. Clean shows nothing at all, so users cannot tell "no target" from "filtered" from "broken". The fallback always forces a counter-draw target when any level clears `minScore` (by design). No coverage metric. |
| Level lifecycle rest/swept/broken shown to the user | **partial** | 623, 1580–1590 | Trade-through removes a pool; the raid outcome feeds D; the ghost label says "✕ SWEPT" without the outcome (ICT-2 covers the logic). |
| Ghost trail | **present** (off by default) | 199–200, 1253–1263 | Dotted box + tiny label, FIFO `ghostMax`. |
| Outcome stamps (hit in N bars / abandoned) | **missing** | — | Trials know `bars`, `mae` and `status` (375–396, 1434–1459), but nothing is drawn on the chart. |
| Alerts: new target / iFVG / sweep / flip | **present** | 2077–2094 | As in the reference. |
| Alerts: approach | **missing** | — | — |
| Alerts: abandoned / replaced / ejected | **missing** | 1584–1590, 2021–2035 | The events exist in code; no alert is raised. |
| Alerts: bar-close "reached" with result | **partial** | 1505–1508, 2087 | Intrabar `freq_once_per_bar` only, without bars-to-hit or MAE. |
| Alerts: per-event selection, filters, cooldown, JSON | **missing** | 2077–2094 | Every `alert()` fires unconditionally; plain text. |
| `alertcondition` dynamic values | **missing** | 2091–2094 | Static text; `{{plot("DOL Price")}}` and `{{plot("DOL PoT %")}}` are available (2444–2446). |
| Status-line hygiene | **wrong** | 40–226 | 75 input values print in the legend (no `display = display.none`). |
| Input tooltips / `active` | **partial** | 40–226 | 67 of 95 inputs have no tooltip, including all sessions; `active` is unused. |
| Table text size / cell tooltips | **missing** | 604–610, 2294–2310 | Fixed `size.small`; `table.cell(... tooltip)` is unused. |
| Price-scale tag for the target | **missing** | 2444 | "DOL Price" plot is `display.data_window` only. |
| Distance units (points / pips / ticks / %) | **partial** | 2243, 2351 | ATR only. |
| Light-theme contrast | **partial** | 226–284, 2166, 2189, 2212, 2223, 1256, 2278 | 6 themes, all tuned for dark charts; no "Auto" from `chart.bg_color`; neon text on transparent label backgrounds is unreadable on white. |
| Autoscale safety | **partial** | 2251–2287, 2159–2168, 2192–2199 | DOL is within 10 ATR. LVN zones are not distance-limited; reach bands and objective are optional. No user guidance about "Scale price chart only". |
| Distance filtering / candidate pool map | **present** | 132–135, 2150–2156 | Ejection + optional faint pool map. |
| Dashboard bias table | **present** | 2294–2310 | Matches the reference. |
| Action / status row | **missing** (by choice) | — | Low priority; advice-like text carries risk. |
| Pine Screener columns | **missing** | 2444–2448 | Plots are `display.data_window` only; 6 `request.security` + 1 `request.security_lower_tf` (923–982). |
| Repaint transparency | **present** | 1–29, README | Live PoT and the sweep alert are disclosed. |

---

## 4. Proposals (best first; maximum 10)

Each proposal states the algorithm, the Pine v6 implementation (inputs, state, where in the code), its value, the evidence grade, risk and effort, and what the ledger can measure. Compile claims are grounded in the local v6 reference mirror.

### COMP-1 (P1, S) · Clean status line and input hygiene

**Problem.** The legend prints about 75 numbers and strings next to "DOL Engine v2", for example "Day Trading 240 60 15 3 5000 14 5 0.2 0.1 0.75 0.3 300 2000-0000 0200-0500 …". The reference screenshot shows only the name. This is the most visible "cluttered / ugly" difference from the reference, and it costs nothing to fix.

**Spec.**
1. Add `display = display.none` to **every** `input.int`, `input.float`, `input.string`, `input.timeframe` and `input.session` call (lines 59–211; 75 calls).
   - Doc: "`display` (const plot_display, optional) … allows one to remove a specific input from the script's status line or the Data Window … The default depends on the type … `display.none` for `bool` and `color` values, `display.all` for everything else" (reference/input.md:27).
   - Write the literal `display.none` in each call. Do not try to store it in a variable: the parameter is `const plot_display` and declaring a variable of that type is not documented.
2. Grey out non-applicable inputs with `active` (input bool, reference/input.md:28). Each dependency is declared before the dependent input, so there is no forward-reference issue.
   - `cHTF`, `cSTF`, `cEXE`: `active = modeIn == "Custom"`.
   - `sessAs`, `sessLo`, `sessNA`: `active = useSess`.
   - `lvnHours`, `lvnRows`, `lvnThr`, `lvnN`: `active = showLVN`.
   - `ghostMax`: `active = showGhost`.
   - `hudSize`: `active = uiStyle == "Terminal"`.
   - `uAbove` … `uText`: `active = theme == "Custom"`.
   - `potLen`, `driftW`, `priorM`: leave active (they are used by both models).
3. Tooltips for the 67 inputs without one. Priorities:
   - Sessions: state the window and that it is read in "Session Timezone"; mention that Asia runs over midnight.
   - `pivLen`, `eqTol`, `poolMax`, `maxATR` (add "levels farther than this are not drawn"), `wS`/`wM`/`wL`.
   - `potH`: "bars; on a 5-min chart 30 bars ≈ 2.5 h".
4. New input `tblSz = input.string("Small", "Panel Text", options = ["Tiny","Small","Normal"], group = G_TABLE, display = display.none)`, mapped to a `size.*` global before `f_cell` and `f_cellC` (lines 604–610). Those functions read globals declared earlier, which is allowed.
5. Optional: show only the Trading Mode in the legend (`modeIn` with `display = display.status_line`). Default: none, to match the reference.

**Value.** Legend parity with the reference; a settings dialog that explains itself; fewer "why is my legend full of numbers" questions.
**Evidence.** Mechanism: **strong** (official reference). Benefit: **weak** (clutter complaints, reference screenshot).
**Risk.** None functionally. Users who want settings in the legend lose that option, because `display.none` removes the value for good. The optional `modeIn` exception keeps the one setting worth seeing there.
**Effort.** S (mechanical edits; the syntax checker covers it).
**Ledger.** Not measurable (pure UX).

### COMP-2 (P1, M) · Alert system: approach, abandoned, reached-at-close, per-event selection, JSON, `{{plot()}}`

**Problem.** The engine raises 4 kinds of events and always fires all of them through `alert()` (lines 2081–2089). It has no approach alert (ForexCracked, ProEA, edgeful), no abandonment alert (HS_16 invalidation, AGPro flips) and no machine-readable payload (ProEA JSON by default). Its alertconditions carry no values. Alert budgets are small (Essential plan: 20), so one well-scoped "Any alert() function call" alert is what most users will create.

**Spec.**
- **Inputs** (new group `G_ALT = "Alerts"`; all `display = display.none`):
  - `alNew` (true), `alHit` (true), `alNear` (true), `alAbd` (false), `alIfvg` (true), `alFlip` (false);
  - `alNearATR` float 0.25 (min 0.05);
  - `alDrawOnly` bool false: suppress events for counter-draw targets;
  - `alKZ` bool false: only inside killzones (`kz > 0`);
  - `alFmt` string "Text" / "JSON".
- **State** (STATE section, about lines 1020–1080):
  - `var int nearAnnId = -1`: one approach alert per target;
  - `var int lastAlertBar = na`;
  - per-bar flags `hitEvt`, `abdEvt` (bool) and `abdWhy` (string), declared next to `newDolEvent` (line 1511).
- **Events, all decided on `barstate.isconfirmed`** (non-repainting; `alert.freq_once_per_bar_close`):
  - **Reached:** in step 3 (lines 1584–1590), when `lv.id == activeId and hit`: `hitEvt := true`. Record `hitBars = bar_index - activeSince` and the MAE from the open Trial with `lvId == activeId`. The intrabar `liveSweep` alert stays as the fast option.
  - **Abandoned:**
    - in step 3 when `lv.id == activeId and ej`: `abdWhy := "ejected"`;
    - in step 19 when `pickId != activeId` and the previous active target is still in the pool: `abdWhy := curElig ? "replaced" : "invalidated"`;
    - at line 2033, read the old `activeId` before reassigning it.
  - **Approaching:** after selection, `not na(activeLv) and activeLv.id != nearAnnId and dolShown and math.max(0.0, activeLv.distance(close)) <= alNearATR * atr`, then `nearAnnId := activeLv.id`.
  - **Filters:** every event goes through `alDrawOnly` (`not activeCtr`), `alKZ` and `minPoT` (already applied to new targets via `dolShown`).
- **Message builder** `f_msg(string ev, Level lv, float pot) =>`, placed after the LEVEL METHODS so `lv.tag()` is available.
  - Text mode: `"DOL ▸ " + ev + " · " + lv.tag() + " @ " + str.tostring(lv.price, format.mintick) + " · PoT " + ...`.
  - JSON mode: `'{"event":"' + ev + '","symbol":"' + syminfo.tickerid + '","tf":"' + timeframe.period + '","side":"' + (lv.side == 1 ? "buy" : "sell") + '","type":"' + f_shortName(lv.kind, lv.src) + '","price":' + str.tostring(lv.price, format.mintick) + ',"top":' + ... + ',"bottom":' + ... + ',"score":' + str.tostring(lv.score, "0.0") + ',"pot":' + str.tostring(pot * 100, "0.0") + ',"horizon_bars":' + str.tostring(H) + ',"counter":' + (activeCtr ? "true" : "false") + ',"time":' + str.tostring(time_close) + '}'`.
  - The `abandoned` payload adds `"reason"`; `reached` adds `"bars"` and `"mae_atr"`.
  - The Pine FAQ shows exactly this pattern: build JSON with `str.tostring()` and send it from `alert(msg, alert.freq_once_per_bar_close)`.
- **`alertcondition` upgrade** (messages must be const; use single quotes so the placeholder can carry double quotes):
  - `alertcondition(annNow, "New DOL Target Active", 'DOL: new target on {{ticker}} ({{interval}}) at {{plot("DOL Price")}}, PoT {{plot("DOL PoT %")}}%')`;
  - add `alertcondition(nearEvt, "DOL Target Approaching", ...)` and `alertcondition(abdEvt, "DOL Target Abandoned", ...)`;
  - keep the existing four titles unchanged so users' saved alerts keep working;
  - doc: concepts/alerts.md:362–372.
- **Ledger:**
  - keep `near` and `hit` counters (`var float nearN, nearK`); when a target that triggered an approach alert is hit, count it;
  - show "NEAR→HIT k/n" in the Full accuracy view, which tells users how often an approach alert was followed by the target being reached;
  - also count abandoned targets by reason.

**Value.** Users can trade from alerts without staring at the chart; webhook and bot users get structured data; a single alert slot covers what they care about.
**Evidence.** Alert fatigue: **moderate** (90% override prevalence in medicine), which argues for defaults that are few and deduplicated. Approach thresholds 0.15–0.25 ATR: **weak** (vendor conventions).
**Risk.** More alerts mean more noise, so `alAbd` and `alFlip` default to off. JSON strings must be valid; test with a validator. `format.mintick` output has no thousands separator (verify on a 5-digit price).
**Effort.** M.

### COMP-3 (P1, M) · Shadow-selector benchmark: does the engine beat the rules competitors ship?

**Problem.** The ledger proves the engine beats a *random* level at the same distance. It cannot say whether the multi-pillar score beats the **nearest draw-side pool** (ICT doctrine, ICT Order Block Pro) or **tier ÷ distance** (LuxAlgo's free DOL). If it does not, the complexity is not earning its keep. In forecasting, complex methods often lose to simple benchmarks: only 17 of 50 beat Comb in M4.

**Algorithm.** On each confirmed bar in the calculation window, after scoring (step 19, line 1963 loop), compute two shadow picks from the same `pool`:
- **S1, Nearest:** among `lv.isLiquidity()` with `side == dirSide` (or either side if `dirSide == 0`) and `distance ≥ minDistATR · atr`, pick the minimum distance.
- **S2, Tier/Distance:** `key = tw / math.max(dAtr, 0.25)` over all levels with `dAtr ≤ maxATR`.
  - `tw`: PW 4, PD 3, sessions (src 3–5) 2, any level with `eqCount > 0` 2, FVG/HTF FVG 1.5, swings (src 0–2) 1, OB/BRK 1.
  - Side = the structure side (`htfBias`, else `dirSide`). If the bias side holds no level, fall back to the other side, as LuxAlgo does.
- No hysteresis for shadows: they commit on their pick each bar, which is how those tools behave. Optional: the same 2-bar rule, for fairness.
- Open a Trial for the shadow's pick under the same rules as the engine's: one open trial per (selector, lvId), cap 64 per selector, booked by the same `f_step`.

**Implementation.**
- **Types:** add `int sel = 0` to `Trial` (line 375) and a `sel` parameter to `f_openTrial`.
- **State:** the per-family arrays (`stN`, `stK`, `stPE`, `stPV`) gain two extra overall slots, for example indices 5 and 6, or new `shN`, `shK`, `shPE`, `shPV` arrays of size 3. Add cluster accumulators per selector (`cluSt` ×3).
- **`f_book`:** when `t.sel > 0`, update only the shadow slots; skip the per-family and calibration arrays, so shadows never change the engine's adaptive calibration.
- **Ledger loop** (lines 1550–1556): unchanged. `openT` holds all trials (≤ 192), each O(1) per bar.
- **Panel** (Full view, after the RACE row at line 2422), two rows:
  - "VS NEAREST": shadow edge (pp) and z; Δ = engine edge − shadow edge; SE ≈ sqrt(vE/nE² + vS/nS²). The picks overlap, so ignoring their positive correlation makes this conservative.
  - "VS TIER/DIST": the same.
  - Verdict: "✓ BEATS" (Δ/SE ≥ 2), "≈ TIE", "✕ LOSES".
- **Data Window plots:** "Edge vs Nearest pp" and "Edge vs TierDist pp".

**Interpretation rule (must be in the tooltip).** Compare **edge over the distance-matched baseline**, never raw hit rate. The nearest-pool selector trivially has the highest raw hit rate because its targets are closest.

**Value.**
- An honest answer to "is this better than the free tools?", which is the user's own question ("100000X BETTER").
- An A/B harness for every future change: a shadow can be "the engine with pillar X off".
- If a shadow beats the engine on a symbol, that is the evidence to retune.

**Evidence.** Principle: **strong** (M4). The specific competitor rules' accuracy: **none** published, which is why measuring it is valuable.
**Risk.**
- Loop time: two extra passes over ≤ 40 pool levels per bar, plus up to 128 extra trials. Small, but test on 20,000-bar calculation depth.
- Readers may misread raw hit rates (mitigated by showing edge only).
- Adds ledger complexity.
**Effort.** M.

### COMP-4 (P1, S) · Honest, explanatory Clean label: reached state, horizon, natural frequencies, runner-up

**Problems.**
1. After a live sweep the Clean label shows "PoT: 95.0%" (lines 2067, 2225), which is a reached target displayed as a probability.
2. The probability carries no horizon.
3. No sample size is shown.
4. The tooltip (line 2206) has neither price, distance nor the reason this target beat the next one.

**Spec.**
1. **Reached state.** In the Clean branch (line 2225): `string potTxt = sweptNow ? "✓ REACHED" : "PoT: " + str.tostring(activePoT * 100.0, potFmt) + "%"`.
2. **Precision input.** `potFmt` comes from `input.string("0.1%", "PoT Precision", options = ["0.1%", "1%", "5%"], group = G_POT, display = display.none)`. The default keeps the reference look ("70.1%"). "5%" rounds with `math.round(p * 20) / 20`. Tooltip: "precise numbers look more certain than they are".
3. **Tooltip**, built only at `barstate.islast`, inside the existing `if showDOL …` block:
   ```
   PDH · EQx2 · score 72.4 (draw-side ▲ D +0.52)
   Price 5,123.0 · 24.0 pts · 0.47% · 2.3 ATR away
   PoT 70% within 30 bars (≈ 2 h 30 m) · Empirical model
   Similar past targets: 41 of 63 reached (65%)          ← calibration bucket
   Runner-up: PWH 65.1 (−7.3 pts) · target held 14 bars
   Proximity 62 · Freshness 80 · Confluence 35 · Density 71 · Draw 90 · ×1.10
   ```
   - **Clock horizon:** `f_dur(int secs)` turns `H * timeframe.in_seconds()` into "45 m", "2 h 30 m" or "6 d". Label it "≈" because session gaps make bars ≠ clock time; TIME-4 refines this.
   - **Natural frequency:** add `float pShow` to `Trial`, set in `f_openTrial` to `f_potModel(d, lv.side, potMu * lv.side)` (the displayed model). Add `var array<float> calN = array.new<float>(5, 0.0)` and `calK`. In `f_book`, `int b = math.min(4, int(t.pShow * 5.0))`, then update `calN` and `calK` for that bucket. Show the bucket of the current `activePoT` when `calN.get(b) >= 10`, else "calibrating (n x)".
   - This is the display half of SMC-1 / TIME-2. If those land, read their arrays instead of duplicating.
   - **Runner-up:** in step 19, keep the second-best eligible score (`aS2`, `aI2`) alongside `aS`/`aI` (lines 1964–1985). Store `var float runS`, `var string runName` at commit time.
4. **Bias table cell tooltips.** `f_cellC` gains a `tip` argument passed to `table.cell(..., tooltip = tip)` (documented in reference/table.md:53, 69). Per row: "Swing bias (confirmed pivots, body break) · internal: BEAR · price at 62% of dealing range (premium)". The values already exist: `htfIB`, `htfRH`, `htfRL` and the others. This keeps the reference look and gives the depth on hover.

**Value.** Removes a misleading readout (95% on a hit target). It answers "when?" with a horizon and "can I trust 70%?" with counts, and "why this one?" with the runner-up. Users asked exactly these questions.
**Evidence.** Natural frequencies: **strong**. Precision as a confidence cue: **moderate**. Horizon explicitness (options, weather): **weak** (convention).
**Risk.** Tooltip length (keep 6 lines or fewer). The calibration bucket must use the PoT shown at assertion time, not the live tick.
**Effort.** S.
**Ledger.** The buckets *are* a reliability measurement: per-bucket hit rate vs bucket midpoint, so the panel can print a mean calibration gap.

### COMP-5 (P2, S) · Outcome stamps: put the ledger on the chart

**Problem.** The ledger knows every target's fate, but a Clean user sees the target vanish and a new one appear. Competitors make results visible:
- HS_16 "result display duration" [N1];
- Flux "Active Sweep Tracker";
- ForexCracked purge circle + resolution;
- P2P "Daily Streak".

Vendors advise testing in bar replay (toodegrees), and stamps make replay testing instant.

**Spec.**
- **Inputs:** `stampOn` bool (default: on in Terminal, off in Clean; implement as `input.string("Terminal only", "Outcome Stamps", options = ["Off", "Terminal only", "Always"])`) and `stampMax` int 8.
- **Reached:** in step 3, when `lv.id == activeId and hit`, call `label.new(bar_index, lv.side == 1 ? lv.top : lv.bottom, "✓ " + str.tostring(bar_index - activeSince) + "b", style = lv.side == 1 ? label.style_label_down : label.style_label_up, color = color.new(cPanel, 100), textcolor = color.new(c, 10), size = size.tiny)`. Optionally append the PoT at assertion "(70%)" so calibration is visible.
- **Abandoned:** "⊘ replaced" or "⊘ ejected" in the ghost colour at the old level (the same hook as COMP-2).
- **Expired** (Trial status 3 while the target is still active): no stamp, because the target is still live.
- **Storage:** `var array<label> stampL`, FIFO capped at `stampMax`. Create stamps only when `inCalc`, to limit object churn on deep history. The 500-label budget is shared with ghosts and HUD; 8 stamps + 12 ghosts + about 6 HUD labels fits.

**Value.** Users see right on the chart that the engine hit 5 of the last 8 and how fast. This builds earned trust, and when the engine has no edge on a symbol the chart shows that too.
**Evidence.** **weak** (convention, trust argument).
**Risk.** Clutter if overused; that is why it is FIFO-capped and off in Clean by default.
**Effort.** S.

### COMP-6 (P2, S/M) · Balanced / no-draw state with a coverage metric (selective prediction)

**Problem.**
- With `dirSide == 0` the engine still picks a target. With nothing above `minScore`, Clean shows nothing and gives no reason.
- AGPro v1.2 stopped forcing "a directional plan" in balanced conditions. Users report being "chopped up" by taking both sides.
- Selective-prediction theory says accuracy rises when a forecaster may abstain on its least confident cases, *and* that coverage must be reported alongside accuracy.

**Spec (keeps the decision-history default "draw-side first, counter-draw fallback").**
- **Classify each confirmed bar:**
  - `NONE`: no level ≥ `minScore`;
  - `BALANCED`: `dirSide == 0` and the best buy-side and best sell-side scores are both ≥ `minScore` with `|ΔS| < balGap` (new input, default 5 points);
  - `CLEAR`: everything else.
- **Inputs:** `balGap` float 5.0; `balMode` = "Show best" (default, current behaviour) / "Show both" / "Hide target".
  - "Show both" draws the second target as a thinner zone (re-use the secondary-target drawing, lines 2172–2190).
  - "Hide target" suppresses `dolShown` and the new-target announcement.
- **Display:**
  - Clean: when the state is `NONE` or `BALANCED` and no target is drawn, show a dim label at `bar_index + extBars`, `close`: "No clear draw" or "Balanced: BSL 61 / SSL 58" (size small, `cGhost`).
  - Bias table: optional 5th row "DOL | BALANCED".
  - Terminal: extend the DRAW row (2338–2343).
- **Ledger:**
  - `covN` counts bars in the window and `covK` counts bars with an asserted DOL, giving **coverage %**;
  - tag each Trial with `bal` (bool), so edge is reported separately for CLEAR and BALANCED picks: "CLEAR edge +8.1 pp (n 140) · BAL +0.4 pp (n 60)";
  - this tells the user whether balanced picks are coin flips on their symbol.

**Value.** Makes "no edge right now" an answer instead of a silent gap, and gives the user a measured reason to skip balanced conditions.
**Evidence.** **moderate** (selective classification) + **weak** (AGPro convention, Reddit).
**Risk.** If "Hide target" became the default it would contradict the decision history, so leave the default at "Show best". The ΔS threshold is arbitrary; the ledger split shows whether it matters.
**Effort.** S/M.

### COMP-7 (P2, S) · Price-scale target tag, distance units, autoscale safety

**Spec.**
1. **Price-scale tag.**
   - Code: `plot(dolShown ? activeLv.price : na, "DOL Price", color = sideCol, display = tagOn ? display.data_window + display.price_scale : display.data_window)`.
   - Qualifiers: `display` is "input plot_display" (reference/plot.md, `plot()` arguments), so a ternary on an input bool is valid. `color` is a series color.
   - This gives the right-axis tag that AGPro, LuxAlgo PAC and many level tools show, and keeps the series name for `{{plot("DOL Price")}}`.
   - Input `tagOn` bool true. The value is `na` when the target is filtered.
2. **Distance unit.** `distUnit = input.string("ATR", "Distance Unit", options = ["ATR", "Points", "Ticks", "Pips", "%"])`.
   - Pips = `syminfo.mintick * 10` on FX (5-digit); otherwise equal to ticks.
   - Used in the HUD DIST line (2243), the panel PoT row (2351) and the COMP-4 tooltip.
3. **Autoscale safety.**
   - Skip LVN zones whose near edge is more than `maxATR` ATR from `close` (in the LVN loops at 2274–2287).
   - Skip the HTF objective and reach bands if they lie beyond `maxATR * ejectMult`.
   - Add a tooltip line on `extBars`/`showLVN`: "If candles look squashed, right-click the price scale → Scale price chart only".
   - Doc: TradingView help 43000762934.

**Value.** Price visible at a glance; distances in the units traders use; no squashed charts.
**Evidence.** Autoscale mechanism: **strong** (platform doc). Benefit: **weak**.
**Risk.** A price-scale tag can crowd the axis when many indicators are loaded, hence the toggle.
**Effort.** S.

### COMP-8 (P2, S/M) · Automatic light-theme contrast

**Problem.** Measured on a white chart, Classic lime is 1.36:1, LVN yellow 1.60:1 and bias green 2.22:1. WCAG requires 4.5:1 for text and 3:1 for graphics. Labels with a transparent background (objective, secondary targets, invalidation, ghosts, LVN text) and the white filament core line become illegible on light charts. A competitor user complained about exactly this.

**Spec.**
- **Light-aware themes.** Keep "Classic" as the default for fidelity with the reference, but make it (and the other built-in themes) switch to light variants automatically:
  - `float bgL = (0.2126 * color.r(chart.bg_color) + 0.7152 * color.g(chart.bg_color) + 0.0722 * color.b(chart.bg_color)) / 255.0`;
  - `bool lightBg = bgL > 0.5`;
  - `chart.bg_color` is `input color` (reference/chart.md), so these are input-qualified and usable in the theme `switch` (lines 228–275).
- **Light variants** (computed contrast on white): buy-side `#0B7A2E` (5.47:1), sell-side `#C8102E` (5.88:1), LVN `#9A6B00` (4.69:1), ghost `#5F6B7A` (5.43:1). Bias green and red use the same pair.
- **Filament core** (line 2223): `lightBg ? c : color.new(color.white, 15)`.
- **Transparent-background labels:** their `textcolor` already uses the side colour, so it inherits the light variant automatically.
- **Dark-backed elements** (the Clean label `cLblBg` and the tables) stay as they are; they read well on both themes.

**Value.** The indicator becomes legible on light-background charts, and avoids a complaint competitors have already received.
**Evidence.** **strong** (WCAG standard + computed ratios) for legibility; **weak** for the user-base share.
**Risk.** `chart.bg_color` returns the gradient midpoint for gradient backgrounds (doc). The test is coarse but adequate.
**Effort.** S/M.

### COMP-9 (P3, M) · Pine Screener columns ("which of my symbols has a strong draw right now?")

**Spec.** Add data-window plots with `display = display.data_window + display.pine_screener` (constant documented in reference/constants.md:125):
- "DOL Side" (+1, −1 or 0);
- "DOL PoT %";
- "DOL Dist ATR";
- "DOL Score";
- "Draw D";
- "HTF Bias";
- "Bars Since Target".

A user can then filter a watchlist, for example `DOL PoT % ≥ 65 AND DOL Side == HTF Bias`. No surveyed DOL competitor offers this.

Screener constraints [N1, TradingView Help 43000742436]:
- only the **last 500 bars** are calculated;
- inputs of type `input.timeframe` use their defaults;
- only listed timeframes are supported;
- there is a limit on `request.*` calls (Help says ≤ 40, a third-party blog says 5; **verify**). The engine makes 6 + 1.

Effects inside the screener:
- the empirical PoT needs ≥ max(150, 20·H) = 600 samples, so it falls back to the analytic model;
- the ledger is empty;
- document both.

**Value.** Multi-symbol scanning is a capability the field lacks.
**Evidence.** **none** (novel).
**Risk.** May hit request or time limits and not run at all, so this needs a live test first. The screener uses default settings only.
**Effort.** M (mostly verification).

### Considered and not proposed here

- **Target lock mode** (HS_16): SMC-2 covers it.
- **PoT by session end / clock horizon** (ASXLT clock horizons, toodegrees phase times): TIME-4.
- **Route analysis CLEAR / BLOCKED** (ASXLT): ICT-5 structural path resistance.
- **Sweep vs break learner and honest sweep alerts:** ICT-2. COMP-2 and COMP-5 provide the alert and stamp hooks.
- **Per-category reach table with n** (ForexCracked, Flux): ICT-1 candidate ledger.
- **"Which side first" probability** (P2P, AetherEdge): BIAS-1, ICTS-3.
- **ACTION / STATUS row** (AGPro, ICTMIKA): plain-language trade instructions read as advice and invite over-trust. The COMP-4 tooltip covers the "why". Not recommended.
- **Liquidation heatmaps:** crypto-derivatives specific, and they need open-interest or leverage data Pine cannot see reliably. Coinglass itself admits they do not tell sequence.

---

## 5. Sources

**Competitor tools (public descriptions)**
- Reference product page (release notes, comments): https://www.tradingview.com/script/ByeifG90/
- ASXLT DOL: https://www.tradingview.com/script/xgF57cH4-ASXLT-DOL-Draw-on-Liquidity/
- LuxAlgo Draw on Liquidity (tiers, settings, repaint FAQ): https://www.luxalgo.com/library/indicator/draw-on-liquidity/ ; concept page https://www.luxalgo.com/library/concept/draw-on-liquidity/
- Draw On Liquidity Planner (AGProLabs): https://www.tradingview.com/script/skYKmBdk-Draw-On-Liquidity-Planner-AGPro-Series/
- Liquidity Draw Probability Map (ForexCracked): https://www.tradingview.com/script/l4nMbqY8-Liquidity-Draw-Probability-Map-ForexCracked/ ; blog https://www.forexcracked.com/forex-indicator/liquidity-indicator-tradingview/
- ICT Order Block Pro (DivergentTrades): https://www.tradingview.com/script/oObsuObl-ICT-Order-Block-Pro/
- ICTMIKA Institutional Liquidity Engine: https://www.tradingview.com/script/DCZoWd3a-ICTMIKA-Institutional-Liquidity-Engine/
- probability_of_touch (taylor_o): https://www.tradingview.com/script/IgAKPrYh-probability-of-touch/
- Liquidity Heatmap (BigBeluga): https://www.tradingview.com/script/6NDgpGap/
- Daily Liquidity Statistics PDH/PDL (Montosca): https://www.tradingview.com/script/exLCeWqh-Daily-Liquidity-Statistics-PDH-PDL-Montosca/
- [N1] Liquidity Draw (HS_16): https://www.tradingview.com/script/nmEliXkz-Liquidity-Draw/
- [N1] AetherEdge Smart Money Flow: https://www.tradingview.com/script/jkgBMcNr
- [N1] P2P 86 Model Probability Map: https://www.tradingview.com/script/20ARUMK8-P2P-86-Model-Probability-Map/
- [N1] ICT/SMC DOL Detector PRO: https://www.tradingview.com/script/B3tYa8yh-ICT-SMC-DOL-Detector-PRO-Final/
- [N1] Flux Charts Liquidity Sweep Profiler: https://www.tradingview.com/script/LM4xxgfj
- [N1] LuxAlgo Price Action Concepts docs: https://docs.luxalgo.com/platform/algos/price-action-concepts/liquidity ; script https://www.tradingview.com/script/ZGl2xWym
- toodegrees Session Statistical Mapping: https://www.toodegrees.trade/indicators/session-statistical-mapping ; insight article https://www.toodegrees.trade/insights/best-ict-tradingview-indicator
- edgeful pivot points: https://www.edgeful.com/blog/posts/pivot-points-indicator-tradingview ; [N1] https://www.edgeful.com/blog/posts/whats-in-play-dashboard-update-2026
- ProEA PDH/PDL code-read: https://proea.app/en/blog/best-previous-day-high-low-indicator-tradingview
- [N1] Coinglass heatmap: https://www.coinglass.com/pro/futures/LiquidationHeatMap ; Hyblock: https://academy.hyblockcapital.com/tools/liquidation-levels-1
- MQL5 vendor blog on repainting: https://www.mql5.com/en/blogs/post/779521
- ICT DOL doctrine summary: https://www.theinnercircletraders.com/ict-draw-on-liquidity/

**User voice**
- Reddit, via a public-data provider: r/ICTMentorship 1wfdm14; r/InnerCircleTraders 1pl85os, 1pp1q6y, 1rgrsic, 1rdau4w; r/Daytrading 1tlvv19, 1tqju9m, 1kci9y1; r/Trading 1wm8xe2 (URLs: https://www.reddit.com/r/<sub>/comments/<id>/)

**Platform documentation**
- Pine v6 reference mirror (local): reference/input.md:27–28, 76, 147; reference/constants.md:125–127; reference/plot.md (`plot()` display, color); reference/table.md:53, 69; reference/chart.md (`chart.bg_color`); reference/core.md:81–93 (`alertcondition`); concepts/alerts.md:296–372
- Pine FAQ alerts (JSON): https://www.tradingview.com/pine-script-docs/faq/alerts/
- TradingView "My chart looks compressed": https://www.tradingview.com/support/solutions/43000762934-my-chart-looks-compressed/
- [N1] Pine Screener: https://www.tradingview.com/support/solutions/43000742436/ ; Script publishing rules: https://www.tradingview.com/support/solutions/43000590599/
- TradersPost TradingView JSON: https://docs.traderspost.io/docs/learn/signal-sources/tradingview

**Evidence**
- Hoffrage, Krauss, Martignon, Gigerenzer (2015). Natural frequencies improve Bayesian reasoning in simple and complex inference tasks. *Front. Psychol.* 6:1473. https://pmc.ncbi.nlm.nih.gov/articles/PMC4604268/
- Jerez-Fernandez, Angulo, Oppenheimer (2014). Show me the numbers: precision as a cue to others' confidence. *Psychological Science* 25(2):633–635. https://www.psychologicalscience.org/news/were-only-human/precisely-right-no-doubt-trust-me.html
- Makridakis, Spiliotis, Assimakopoulos (2018). The M4 Competition: results, findings, conclusion and way forward. *IJF* 34(4):802–808. https://ideas.repec.org/a/eee/intfor/v34y2018i4p802-808.html ; 2020 paper https://www.sciencedirect.com/science/article/pii/S0169207019301128
- [N1] Drug-drug-interaction alert override meta-analysis: https://journals.sagepub.com/doi/10.1177/14604582241263242
- [N1] Geifman & El-Yaniv (2017). Selective classification for deep neural networks. arXiv:1705.08500
- Options PoT conventions: https://www.schwab.com/learn/story/options-delta-probability-and-other-risk-analytics ; https://optionalpha.com/lessons/probability-of-profit-vs-probability-of-touch
- Probability of precipitation conventions: https://en.wikipedia.org/wiki/Probability_of_precipitation ; https://www.weather.gov/ppg/forecast_terms
- WCAG 2.1 contrast (§1.4.3 text 4.5:1, §1.4.11 non-text 3:1): https://www.w3.org/TR/WCAG21/ (contrast ratios in §1.8 and COMP-8 computed with the WCAG relative-luminance formula)
