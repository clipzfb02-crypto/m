# Competitive landscape: final combined study (researcher A + researcher B)

Domain: commercial and free liquidity / draw-on-liquidity (DOL) / target tools on TradingView and other platforms. It covers their public descriptions, target-selection rules, probability displays, alert designs, dashboards, UI conventions, and what users praise or complain about. It then compares them with `brief/baseline_v2.pine` (identical to `indicators/dol_engine.pine`, 2448 lines) and proposes improvements.

**How to read the marks**
- **[A]**: researcher A's finding, re-checked by B and kept.
- **[A, unverified]**: A's finding that B could not re-open. In this pass tradingview.com and luxalgo.com were blocked by the network proxy and the scraping service was out of credits, so B re-checked through web-search summaries only. Treat these as plausible, not confirmed.
- **[B-corr]**: B corrected A (numbers, line refs, grades or conclusions).
- **[B-new]**: added by B.
- Rules respected: public descriptions only, no code or long passages copied, no product branding reused. All line numbers refer to `brief/baseline_v2.pine`.

B's own work products:
- `study/competitors_b_tools/comp_pickers.py`: replication of the published competitor selection rules on the sibling candidate datasets (14 sets, ≈ 14,600 picks per rule). Output in `out_comp_pickers.txt`.
- `study/competitors_b_tools/comp_delivered.py`: paired "ATR delivered" comparison. Output in `out_comp_delivered.txt`.

---

## 0. Executive summary

1. **On substance the engine is already ahead of the DOL selectors surveyed, but "ahead" has to be stated carefully.** [A, B-corr]
   - No surveyed DOL *selector* combines multi-source pools, PD arrays, a multi-pillar score, an empirical PoT and a ledger graded against a distance-matched random level.
   - B-corr: A wrote that no competitor compares against a null. That is wrong for *statistics* scripts. Two open-source scripts grade order blocks and FVGs against matched placebo zones (same height, direction and distance) with z-scores: "Order Block Statistics: Real Win Rate vs Random Levels" and "FVG Statistics with Placebo Control". Both report **no detectable edge**; the FVG script found none in 14 measurements (3 asset classes × 3 timeframes × 2 periods).
   - B-corr: A wrote that no measurement-first tool commits to one target. Two do:
     - "Liquidity Map & Order Blocks [MQLSoftware]" projects the most likely draw and shows a self-calibrating historical hit rate, flagged provisional while the sample is thin;
     - "Liquidity Magnet [LunqFX]" shows a 0–100 Magnet Score, a NEXT TARGET, a probability and a BUY-/SELL-SIDE PULL bias.

     Neither tests against a null.
2. **B replicated the published competitor selection rules (§2.2).** [B-new] The rules tested were nearest pool, nearest pool on the bias side (ICT doctrine), LuxAlgo-style tier ÷ distance, and an engine-like hand score. The data were 13 CME/FX intraday and 1H sets plus S&P 500 daily, with H = 30 bars.
   - **Every rule's realised hit rate equals its distance-matched baseline.** Pooled excess is −1.0 to +0.1 pp, with an SE of about 1.6–1.9 pp per set. Paired differences reach |z| ≥ 2 in only about 4 of 78 rule-set pairs, which is the chance rate. Distance explains the raw hit rates: nearest 72%, tier/dist 65%, engine-like 60%.
   - **The rules differ in what they deliver.** ATR delivered (hit × distance) per target is engine-like 0.94 vs tier/dist 0.87, nearest-on-bias-side 0.86 and nearest 0.80. The engine-like score beats each simple rule with z ≥ 2 on 11–12 of the 14 sets. It loses to an "expected reach" picker (max d·PoT), 1.20, on 13 of 14 sets.
   - Consequence for proposals: a shadow benchmark that compares *edge* will almost always say "tie". It must report **ATR delivered** next to excess hit (COMP-3, downgraded P1 → P2 and merged with SKEP-5 / CAL-3).
3. **Where the engine visibly loses is UX hygiene and honesty of the readout.** [A, B-corr]
   - **Status line:** the engine has **104 inputs**. **76** of them (int, float, string, timeframe, session) print in the legend, because none sets `display`. **76** inputs also lack a tooltip. A counted 95 / 75 / 67.
   - **Clean label:** it shows "PoT: 95.0%" for a target that has already been reached (line 2067). It gives no horizon (reference class), no sample size, and no reason when the chart is blank.
   - **Alerts:** static text, no approach, abandoned or reached-with-result events, and no JSON.
   - B-new: the intrabar "DOL Target Swept" alert (1504, 2084–2085, 2092) also fires for a target that was **never shown or announced**, because it is not gated by `dolShown` or `lastAnnId`. This happens whenever *Minimum PoT* > 0.
   - **Light charts:** the Classic neon palette is unreadable on white (lime 1.36:1; verified).
4. **The best tools converge on six conventions** [A]:
   - one target confirmed at bar close;
   - an explicit balanced / no-draw state;
   - a probability shown with its horizon and sample size;
   - level lifecycle states (rest, swept, broken) with ghosts;
   - distance filtering;
   - few, filterable, JSON-capable alerts.

   B-new: two more.
   - **Score ≠ probability wording.** AGPro: "treat the draw score as a measure of how clearly liquidity leans one way, not as a probability of profit". ForexCracked: "makes no performance claims".
   - **Platform guard rails.** TradingView stops any alert that fires more than 15 times in 3 minutes. Webhooks are sent as `application/json` only when the message parses as JSON. Publishing rules forbid implying that an attempt to reproduce a closed-source script actually reproduces its behaviour.
5. **Communication evidence, corrected** [B-corr, B-new]:
   - Probabilities must name their reference class (Gigerenzer et al. 2005: "30% chance of rain" is read as time, area or days).
   - Probabilistic forecasts improve decisions and trust, while categorical advice alone did not help (Joslyn & LeClerc 2012). This argues for PoT and against an "ACTION" row.
   - Natural frequencies raise Bayesian accuracy (meta-analysis: 4% → 24%, McDowell & Jacobs 2017). Transfer to trading displays is assumed.
   - Precision reads as confidence (Jerez-Fernandez et al. 2014).
   - People abandon an algorithm after seeing it err, even when it beats them (Dietvorst et al. 2015). Outcome stamps must therefore show the expectation (PoT at assertion) next to each result.
   - Clutter and choice-overload effects are weaker than folklore: the choice-overload meta-analysis puts the mean effect at about 0 (Scheibehenne et al. 2010). "Clean" is a user requirement here, not a proven accuracy lever.
6. **Proposals (best first, §4):**

   | ID | Priority, effort | Proposal |
   |---|---|---|
   | COMP-1 | P1, S | Status line and settings hygiene (shared with UX-1 and PENG-1) |
   | COMP-2 | P1, M | Alert system v2: correctness fixes first, then reached / approaching / abandoned, toggles, JSON, `{{plot()}}` |
   | COMP-4 | P1, S | Honest Clean label: reached state, horizon as reference class, k-of-n, expected reach, "why blank" hint (coordinate with UX-3) |
   | COMP-3 | P2, M | Competitor rules as roles in the shared shadow ledger, reporting ATR delivered |
   | COMP-7 | P2, S | Price-scale tag, distance units, LVN distance cap |
   | COMP-5 | P2, S | Outcome stamps showing PoT at assertion |
   | COMP-8 | P2, S | Light-theme contrast (adopt UX-2's two-role version) |
   | COMP-12 | P3, S | Same-side target ladder (TP1/TP2) [B-new] |
   | COMP-9 | P3, M | Output contract plus Pine Screener (needs the two HTF requests merged) |
   | COMP-11 | P3, S | Wording honesty: placebo language, score vs probability, publishing rules [B-new] |
   | COMP-6 | P3, S/M | Balanced / no-draw ledger split and coverage (downgraded; display moved into COMP-4) |

---

## 1. Concepts (definitions and parameters)

### 1.1 How competitors choose the one target

| Family | Rule as published | Parameters | Who | Failure modes / notes |
|---|---|---|---|---|
| **Nearest opposing pool** | Target = closest untapped pool on the bias side, or opposite the setup. ICT doctrine: the nearest significant pool in the bias direction, matched to trade duration. | Pool set; bias source; "significant" undefined | ICT Order Block Pro (dashed DOL line from a validated OB to the closest opposing BSL/SSL) [A, unverified]; ICT DOL guides | B replication: hit 66–72%, realised = baseline, **lowest ATR delivered** (0.80–0.86 per target) [B-new] |
| **Tier ÷ distance** | `score = tierWeight / distATR`. The best score on the structure-bias side is the "working draw"; it falls back to the other side when the bias side has none. On a sweep it re-anchors to the next objective. | Tiers: weekly 4, daily 3, session and equal extremes 2, gaps 1.5, swings 1 (verified via search). Structure length 50 (verified). Swing length 10, EQ tolerance 0.1 ATR, minimum gap 0.5 ATR, maximum age 500 bars, sessions [A, unverified]. | LuxAlgo *Draw on Liquidity* (free) | Diverges as distance → 0, so the nearest level wins once price is close. B replication: realised = baseline; ATR delivered 0.87, below the engine-like score's 0.94 (z ≥ 2 on 11/14 sets) [B-new] |
| **Per-side aggregate with states** | Each side gets a 0–100 score (pool quality, ATR proximity, trend backbone, freshness). States: Buy-Side Draw, Sell-Side Draw, Two-Sided (score gap < *Two-Sided Balance Gap*), No Draw ("no qualifying untapped pool is currently in range", verified). *Max Draw Distance* input (verified). v1.2 suppresses runway, target and invalidation in balanced or low-score states [A, unverified]. | Balance gap, max draw distance | Draw On Liquidity Planner [AGPro] (open source) | Says its score is "not a probability of profit" (verified) |
| **Volume-weighted side share + lock** | Liquidity above vs below price, weighted by volume. The side holding ≥ 55% (default) is chosen; the target is locked on a closed candle until reached, stopped, or N bars pass. PoT = random-walk touch chance "within the horizon … not a prediction of direction". | Minimum liquidity %, PoT horizon, minimum PoT, SL buffer, minimum SL distance, minimum R:R, lock duration | "Liquidity Draw" (open source, built for 1-minute charts; verified via search) | A lock can hold a dead target |
| **Magnet score + NEXT TARGET** [B-new] | Swing and EQH/EQL pools scored 0–100 ("Magnet Score"); the strongest is the NEXT TARGET. Dashboard: next target, probability, distance, BUY-/SELL-SIDE PULL bias, pool counts. Tight distance = "immediate objective"; large = "swing objective". | Weights not published | Liquidity Magnet [LunqFX] (open source) | No null; formula not public |
| **Most likely draw + self-calibrating hit rate** [B-new] | Projects the most likely draw. Its hit rate is "self-calibrating", from how often similar pools were reached in the loaded history, and is **marked provisional while the sample is thin**. | Bucketed history | Liquidity Map & Order Blocks [MQLSoftware] (open source) | Raw hit rate, no null |
| **PoT × quality × bias, confirmed at close** | Selects on theoretical PoT, level quality and bias. "Confirmed at candle close to reduce intrabar switching." Clock-time horizons (24 candles, 24 min, 1 h, 4 h, custom). Route states CLEAR / LIQ / BLOCKED / INSIDE. | — | ASXLT DOL (invite-only) [A, unverified]; B's searches could not find the page | Admits its PoT is not empirically validated [A] |
| **Learned side probability** | Online logistic regression on 8 features: P(buy-side pool before sell-side within N bars), labelled by a barrier race. A UCB bandit tunes the threshold. | — | AetherEdge Smart Money Flow [A, unverified] | Opaque; overfits small samples |
| **Session-sequence statistic** | P(overnight high vs low broken first by 11:00 NY) from a 2016+ dataset; a "Daily Streak" counter. | — | P2P 86 Model [A, unverified] | Static dataset, 4 markets. A streak counter invites the gambler's fallacy [B-new] |
| **Multi-pillar weighted score** | Proximity, freshness, confluence, density (reference product); the engine adds draw vector D and multipliers. | Weights, gates | Reference product, this engine | Must justify itself against the simple rules (§2.2, COMP-3) |
| **Anti-pattern: confidence score called "probability"** | Heuristic 0–100 "probability" bands with no frequency behind them | — | ICT/SMC DOL Detector PRO [A, unverified] | Misleads; TradingView rules require substantiated claims |

**How practitioners use the target** [A]: as take-profit or objective, with entries from a PD array toward it. Users ask where to take profit (r/Daytrading, 147 upvotes). Invite-only tools sell TP1/TP2/TP3 ladders; for example "Liquidity Radar PRO" also lists 19 alert conditions [B-new, vendor description].

**Geometric fact behind the ladder** [B-new; strong, it follows from path continuity]: on the same side of price, a nearer level is always touched before a farther one. The probability of touching a farther same-side level is therefore at most the probability of touching the nearer one, and the ordering of a target ladder is deterministic (sibling `calib_ml.md`).

### 1.2 Target commitment and stability [A]

- **Confirm at close** (ASXLT, AGPro, the reference product, the engine): targets change only on confirmed bars; the PoT text may update live.
- **Lock until resolved** ("Liquidity Draw"): hit, stop or N bars. SMC-2 covers it.
- **Hysteresis with a challenger streak** (engine, lines 2011–2020): the challenger must lead by `hyst` points (twice that across sides) for 2 consecutive bars. Off-killzone the hysteresis is multiplied by `kzHx` (976).
- **Event cooldowns** (AGPro: flip and sweep markers throttled; default 52 bars in v1.2) [A, unverified].
- **Display modes as anti-clutter** [B-new]:
  - LuxAlgo SMC "Historical" (all past structures) vs "Present" (active only);
  - TFO Killzones "Until Mitigated" (line ends when traded through) vs "Past Mitigation".

  Both are display filters and do not change the calculation.

### 1.3 Probability displays

| Display | Definition | Example | Notes |
|---|---|---|---|
| **Theoretical PoT (first passage)** | P(max over horizon ≥ level) for a random walk. Driftless reflection gives PoT ≈ 2 × P(end beyond). | "Liquidity Draw" ("statistical estimate, not a prediction of direction"; verified); ASXLT; options platforms | Horizon always explicit (expiry, "within the horizon") |
| **Empirical PoT** | Fraction of past windows of length L in which price travelled ≥ the distance | `probability_of_touch` (taylor_o, open source; verified: "touch = price exceeding the level at some point within the time frame") | Precedent for `f_empPoT` (1284) |
| **Measured reach frequency by category, with n** | Category × birth distance; reached within 50 bars (capped at 60); touches split into rejected / cut / stall; prints only when n ≥ 20 ("building" otherwise) [A, unverified for numbers]. Dashboard: nearest pool above and below with ATR distance, reach frequency, median bars, **sample size** (verified). "Makes no performance claims" (verified). | ForexCracked *Liquidity Draw Probability Map* (open source) | A's boost count (2,239) conflicts with A's own notes (115 boosts) and could not be re-checked, so it is dropped [B-corr] |
| **Placebo-controlled statistic** [B-new] | For each real OB or FVG, control zones of the same height, direction and distance from price, at bars without the event. Edge = real − control; z ≈ 2 treated as a first sign; replication required. | OB Statistics vs Random Levels; FVG Statistics with Placebo Control | FVG: no detectable advantage in 14 measurements; OB: no reliable gap. Same idea as the engine's `f_potBase` null |
| **Conditional on open location** | Touch probability per level given where the session opens; threshold slider; "view details" shows k of n | edgeful [A, unverified] | Natural frequencies on demand |
| **Averaged price and time** | Average phase levels and average completion **time** per session, with the number of sessions averaged | toodegrees Session Statistical Mapping [A, unverified] | |
| **Cap** | PoT capped at 95% | Reference product, engine | |

Display precision:
- **Precision reads as confidence.** Experts giving more digits were judged more confident; precise advisors were preferred (Jerez-Fernandez, Angulo & Oppenheimer 2014; samples about 187 and 163). This concerns perceived confidence, not accuracy. [A, verified]
- **Reference class** [B-new]. "A 30% chance of rain" was read as time, area or days. Only in New York did a majority give the meteorological meaning (Gigerenzer et al. 2005, five cities). A PoT must say "touch within the next 30 bars (≈ 2 h 30 m)". The bare "PoT: 70.1%" does not.
- **Uncertainty helps decisions** [B-new]. Forecasts with uncertainty information improved precautionary decisions and trust, and softened the trust loss after forecast errors. Categorical advice alone did no better than a deterministic forecast (Joslyn & LeClerc 2012, *J Exp Psych: Applied* 18:126–140).
- Weather probability-of-precipitation conventions (10% / 5% steps; NWS wording bands) [A].

### 1.4 Level lifecycle states [A]

| State | Best published rule | Display |
|---|---|---|
| Rest | Untouched since birth | Solid |
| Swept | Wick through, then a close back within a confirmation window (Flux: 0 = same bar; verified that the window exists) | Kept, marked |
| Broken | Close beyond, or the window expires without a close back; a swept level later closed beyond becomes broken | Line ends, faded |
| Ghosted | Swept or invalidated levels kept at low opacity (ICT OB Pro 25% [A, unverified]; LuxAlgo "Keep Swept Pools"; reference product "Ghost Trail") | Faded |
| Past window | Untouched after the reach window (ForexCracked) | Faded |
| Mitigated (TFO) [B-new] | Line ends once price trades through ("Until Mitigated"), with an option to extend it | Alert "broken pivots" |

ProEA's read of 15 popular PDH/PDL scripts: none tells a sweep from a break, and some leak or lag (`lookahead_on` without `[1]`). [A, unverified; B's searches could not find the article]

Engine:
- strict trade-through removal (`touched`, 623);
- raid outcome folded into D (1580–1582);
- ghosts "✕ SWEPT", "⊘ EJECTED" (1586) and "⊘ INVALIDATED" (2023), off by default (`showGhost`, 210).

The swept vs broken logic belongs to ICT-2; display hooks are in COMP-5.

### 1.5 Self-measurement ("keeps score")

| Tool | What is measured | Null? | Display |
|---|---|---|---|
| ForexCracked map | Reach %, median bars, reject / cut / stall per category | No | n beside every figure (verified for the dashboard) |
| Flux Liquidity Sweep Profiler | Recovery vs breach magnitudes over a watch window; Edge = average recovery ÷ average breach per type (verified) | No | Units ATR / price / pips / ticks (verified) |
| MQLSoftware map [B-new] | Hit rate of the projected draw | No | "provisional" while thin |
| OB / FVG placebo scripts [B-new] | Real − matched-placebo hit rate, z | **Yes** | Edge and z; replication required |
| P2P 86 [A, unverified] | First-break call | No | Daily streak |
| **This engine** | Hit of every asserted DOL over H vs a distance-matched random level; Wilson CI; cluster-robust z; L50; bars to hit; heat; race; per-family rates; calibration | **Yes** | Terminal only (2376–2430). Clean users see none of it. |

B-corr: the engine is not unique in using a null. It is unique among **DOL selectors** in grading its own committed target against one. The placebo scripts' finding (no edge for FVG and OB) matches the sibling replications in `ict_pd.final.md` and `calib_ml.md`.

### 1.6 Dashboards [A]

| Tool | Rows / layout |
|---|---|
| ASXLT | Bias, HTF context, target, PoT, distance, route states, alternatives, last sweep |
| AGPro | Analytical-question header, state, score, target, distance, pool type, invalidation, ACTION |
| ICTMIKA | BIAS / PHASE / OPEN / STATUS / DOL |
| LunqFX [B-new] | Next target, probability, distance, bias, pool counts |
| Reference product | Timeframe \| Bias (D / 4H / 1H) |

Controls in the field: 9 table positions, 5 text sizes, dark/light (Flux); font up to "Huge" (AGPro); label alignment so labels do not cover live price (ICT OB Pro) [A, unverified].

Engine:
- Clean table at 2294–2310 with fixed `size.small` (608–609) and 5 positions (573);
- Terminal panel at 2313–2434;
- no table text-size option and no cell tooltips, although `table.cell` takes a `tooltip` parameter (reference/table.md:53, 69; verified).

### 1.7 Alerts

| Tool | Events | Thresholds / format |
|---|---|---|
| Reference product | New DOL target, new iFVG, DOL target swept | — |
| LuxAlgo DOL | Draw reached; draw flips (both directions; flip alerting verified) | — |
| LuxAlgo PAC [A, unverified] | Every event; message placeholders; Custom Alert Creator (AND / sequence) | Messages start with ticker + TF |
| AGPro | Buy-side draw, sell-side draw, pool swept | — |
| "Liquidity Draw" | New target, target hit, invalidation (verified) | — |
| ForexCracked | Approaching a high-reach pool; purge; net-bias flip | 0.25 ATR, reach ≥ 70%, meaningful n [A, unverified] |
| ProEA desk [A, unverified] | Level swept; near a level | 0.15 × daily ATR; JSON by default; once per bar close |
| TFO Killzones [B-new] | "Alert broken pivots" | — |

**Platform facts:**
- `alertcondition()` takes a const message, but placeholders `{{plot("title")}}` and `{{plot_0}}`…`{{plot_19}}` (first 20 plots) are allowed, also for `display.none` plots. Single quotes are needed around the message when the placeholder holds double quotes (concepts/alerts.md, verified locally).
- `alertcondition()` counts toward the plot limit; `alert()` does not (reference/core.md:63).
- **Throttle** [B-new]. "If a script alert triggers more than 15 times in 3 minutes, it automatically stops" (TradingView support 43000690939). Never use `alert.freq_all` for these events. On seconds charts, keep the set of enabled events small or add a minimum bar gap.
- **Webhook content type** [B-new]. Valid JSON is sent as `application/json`; anything else is sent as `text/plain`. Webhooks require 2-factor authentication (support 43000529348).
- **Number formatting** [B-new]. `str.format()`'s default numeric pattern uses thousands separators (`#,###.###`), so never build JSON numbers with it. Use `str.tostring(x)` or `str.tostring(x, format.mintick)`, which rounds to the tick and "returns the string with trailing zeros" (reference/constants.md:160).
- **Alert budgets** [B-corr]:
  - Plus 100, Premium 400 and Ultimate 1,000 technical alerts (TradingView pricing pages);
  - Essential 20 (third-party guide; one third-party source says 800 for Ultimate);
  - Basic 0 [A, unverified].

  One "Any alert() function call" alert, scoped by per-event toggles, is the right design.
- **Alert fatigue** [B-corr]: physician override of drug-interaction alerts 90% (95% CI 85–95%, 16 studies, *Health Informatics J* 2024); a 2025 review of 44 studies pooled 79.8% (73.0–86.7%). A's "570,776 prescriptions" could not be verified. This is a medical domain; transfer to trading is assumed.

Engine alerts (2077–2094): four `alert()` calls (new target 2079–2081, iFVG 2082–2083, live sweep 2084–2085 with `freq_once_per_bar`, flip 2086–2088) and four static `alertcondition()` calls (2090–2093). Gaps:
- No approach, abandoned or reached-at-close-with-result events.
- No toggles, filters, JSON or placeholders.
- B-new: `alert()` messages carry `syminfo.ticker` but **no timeframe**.
- B-new: the sweep alert is **not gated to the announced target**.

### 1.8 Visual conventions [A]

- **Zones:** anchored at the origin candle and extended right (engine 2218–2226).
- **Path emphasis:** AGPro runway shading; LuxAlgo magnet gradient; the engine's dashed tether (2224).
- **Right-edge price tag** (AGPro). The engine shows no price in the label or tooltip; it is only in the Data Window (2444).
- **Encoding by category or quality:** line style by category (Flux); thickness by reach frequency (ForexCracked); brightness by score (MQLSoftware density bands [B-new]).
- **Distance filtering and "how many hidden":** ProEA within 2× daily ATR; AGPro ATR-ranged map; AGPro *Max Draw Distance* (verified).
- **Autoscale compression.** Far drawings make autoscale fit them, and the fix is "Scale price chart only" (TradingView help 43000762934). A Reddit user wrote: "shrinks it down so much that I cannot see any candles". `display.none` plots never affect scale. Whether a `display.price_scale`-only plot does is not documented [B-new, test it].
- **Light themes** (verified with the WCAG formula):

  | Colour | On white | On #131722 |
  |---|---|---|
  | `#39FF14` | 1.36:1 | 13.2:1 |
  | `#00C864` | 2.22:1 | — |
  | `#FFC400` | 1.60:1 | — |
  | `#FF1744` | 3.85:1 | — |

  WCAG asks 4.5:1 for text and 3:1 for graphics. Darker variants such as `#0B7A2E` (5.47:1 on white) fall to 3.31:1 on the dark Clean label `#161616`, so two colour roles are needed (UX-2 correction to COMP-8, verified). A user of a competitor tool complained that a yellow line could not be seen on a white background [A, unverified].

### 1.9 Legend (status line) and settings hygiene [B-corr]

- Doc: input `display` defaults to `display.all` for every type except `bool` and `color`, which default to `display.none` (reference/input.md:27, the same on every `input.*` signature; verified).
- Engine counts (B recount by parsing lines 40–226):

  | Input type | Count |
  |---|---|
  | `int` | 23 |
  | `float` | 31 |
  | `string` | 9 |
  | `timeframe` | 3 |
  | `session` | 10 |
  | `bool` | 20 |
  | `color` | 8 |

  That is **104 inputs**. The first five types, **76 inputs**, print in the status line. **76 inputs have no tooltip**, 54 of them among the legend-printing types. No input sets `display` or `active`.
- `active` (input bool, input.md:28) can grey out inputs that do not apply. Groups are already used well (16 groups, 42–57).

### 1.10 Repainting, honesty and publishing rules

- **Repaint complaints** [A]: live MSS/BOS tags deleted on reversal; mid-bar alerts that reverse at close.
- **Lag vs repaint** [B-new]: pivot lag (an element drawn late at its true bar) is not repainting; already-drawn levels changing is.
- **Best practice** [A]: state which outputs are live (PoT), how MTF data is aligned, and that probabilities are model estimates.
- **TradingView publishing rules** [B-corr, verified via search]:
  - an author may publish an attempt to reproduce a closed-source script, but "implicit or explicit claims or demonstrations suggesting that such reverse-engineering attempts reproduce the script's behavior are not allowed";
  - vendors who intentionally mislead face a fast-track ban.

  The README's "independent implementation written from a public feature description" is acceptable. Never name the closed product, and never claim parity of results.

### 1.11 Other platforms

- **Crypto liquidation heatmaps** (Coinglass, Hyblock): estimated liquidation clusters by leverage tier. Coinglass's FAQ: when both sides are bright, it is hard to tell which side is visited first [A, unverified]. Magnitude does not tell sequence.
- **Order-book heatmaps** (Bookmap, ATAS) [B-new]:
  - they show *displayed limit orders*, which can be pulled as price approaches;
  - stop orders never appear in the book;
  - icebergs understate size and spoofing overstates it;
  - Bookmap's own blog concedes that seeing large orders pulled is of little value after the fact.

  Swing-inferred stop pools (the engine's approach) are an inference about orders no platform can see. Tools should say so.
- **NinjaTrader** [A + B-new]: B found no NinjaTrader 8 add-on that computes a DOL probability, only killzone and session-level tools (free NT8 killzone/PDH sweep marker) and ICT drawing suites. TradingView is where DOL selectors compete.
- **edgeful** [A, unverified]: 140+ statistical reports; "What's in Play" dashboard; vendor statistics without visible n.

### 1.12 User voice [A]

| Source | Gist |
|---|---|
| r/InnerCircleTraders | "how to see what DOL is active and **when** … what time frame"; "some weeks perfect … some weeks not a single time"; "I need like a checklist" |
| r/Trading | No bias, so "taking setups on both sides … chopped up" |
| r/Daytrading (147 upvotes) | "where to set a take profit" |
| r/ICTMentorship | Session times unclear; "shrinks [the chart] … cannot see any candles"; requests for RTH gap / NWOG / NDOG |
| r/Daytrading | "Many similar scripts but free"; "Just draw them yourselves" (a tool must add more than levels) |
| Competitor comments | Colour requests; white-background visibility; "which timeframe is best?" |
| Reference product | 259 comments, nearly all trial requests [A, unverified] |

B could not re-open these threads; the quotes are carried from A.

### 1.13 Trust: what helps and what backfires [B-new]

- **Algorithm aversion.** After seeing an algorithm err, people chose it less often than an inferior human, even when they had seen it outperform (Dietvorst, Simmons & Massey 2015, *JEP: General* 144:114–126).
  - Giving people even slight control over the algorithm reduces the aversion (Dietvorst et al. 2018).
  - The first unit of error feels largest (Dietvorst & Bharti 2020).
  - Implication: on-chart results (COMP-5) must show the expectation next to the outcome, for example "✕ missed · PoT was 40%". A lock or override option (SMC-2) is the "slight control" lever.
- **Uncertainty communication.** Showing probability with the forecast raised trust and attenuated the trust loss after errors (Joslyn & LeClerc 2012). Categorical advice alone did no better than a deterministic forecast, which supports the decision not to add an ACTION row.
- **Streak counters** (P2P "Daily Streak") invite hot-hand / gambler's-fallacy reading. Not recommended.
- **Clutter.** Choice-overload meta-analysis: 63 conditions, N = 5,036, mean effect "virtually zero" with large variance (Scheibehenne, Greifeneder & Todd 2010). Clutter effects on decisions are task-dependent; one study of financial risk judgments did find clutter effects. "Fewer drawings" is justified by the reference look and user complaints, not by a proven accuracy gain.

---

## 2. Evidence

### 2.1 Literature, platform and vendor evidence

| Claim | Numbers | Grade | Source / status |
|---|---|---|---|
| Probabilities must state the reference class | 30% rain read as time, area or days; only New York's majority gave the standard meaning; 5 cities | **strong** (peer-reviewed survey) for the communication problem; transfer assumed | Gigerenzer, Hertwig, van den Broek, Fasolo, Katsikopoulos 2005, *Risk Analysis* 25(3):623–629 [B-new] |
| Uncertainty information improves decisions and trust | Better precautionary decisions and trust; error effects attenuated; categorical advice alone no better | **strong** (peer-reviewed experiments) | Joslyn & LeClerc 2012, *JEP: Applied* 18:126–140 [B-new] |
| Natural frequencies help Bayesian reasoning | Meta-analysis 4% → 24% correct; Hoffrage et al. 2015 Study 1: +37 pp average across 4 complex task conditions | **strong** for Bayesian tasks; **moderate** for our use (display of k-of-n is not a Bayesian task) | McDowell & Jacobs 2017 *Psych Bull* (via Weber, Binder & Krauss 2018); Hoffrage, Krauss, Martignon & Gigerenzer 2015 *Front Psychol* 6:1473 [B-corr: A's "7% vs 45%" not verified] |
| Precision reads as confidence | More digits judged more confident; precise advisors preferred | **moderate** (2 small studies) | Jerez-Fernandez, Angulo & Oppenheimer 2014, *Psych Sci* 25(2):633–635 [A, verified] |
| Algorithm aversion after seeing errors | Lower choice of the algorithm after seeing it err, even when it beat humans | **strong** (replicated) | Dietvorst, Simmons & Massey 2015 [B-new] |
| Complex forecasters often fail to beat simple benchmarks | M4: 12 of the 17 most accurate methods were combinations; none of the six pure ML methods beat the Comb benchmark, and only one beat Naïve2; a 2020 review says only 17 methods beat the benchmark suite | **strong** (principle) | Makridakis, Spiliotis & Assimakopoulos 2018 *IJF* 34(4):802–808; 2020 *IJF* 36(1):54–74 [B-corr: "17 of 50" rephrased] |
| Abstention improves accuracy at reduced coverage | 2% top-5 ImageNet error with 99.9% probability at about 60% coverage | **moderate** (ML; needs a selector *with* information) | Geifman & El-Yaniv 2017, arXiv:1705.08500 [A, verified]. B's replication found no precision gain from abstaining here (§2.2) |
| Alert fatigue | 90% override (95% CI 85–95%, 16 studies); 79.8% (73.0–86.7%, 44 studies) | **moderate** (strong in medicine, transfer assumed) | *Health Informatics J* 2024 (PMID 38899788); O'Sullivan et al. 2025 preprint [B-corr] |
| TradingView alert throttle | >15 triggers in 3 minutes stops the alert | **strong** (platform documentation) | Support 43000690939 [B-new] |
| Webhook content type | Valid JSON → `application/json`; else `text/plain`; 2FA required | **strong** (platform documentation) | Support 43000529348 [B-new] |
| Pine Screener limits | Last 500 bars; `input.timeframe`/`symbol`/`time` ignored (defaults used); listed timeframes only; Premium+; at most **5** `request.*` calls per one regional help page (vs 40 general) | **moderate** (help pages disagree on the request count) | Support 43000742437 / 43000742436 [B-corr] |
| Far levels compress the chart | "Scale price chart only" fix | **strong** (platform documentation of the mechanism) | Support 43000762934 [A] |
| Contrast thresholds | Text 4.5:1, graphics 3:1; palette ratios in §1.8 | **strong** + computed (B recomputed) | WCAG 2.1 §1.4.3 / §1.4.11 [A, verified] |
| Choice overload | Mean effect "virtually zero", 63 conditions, N = 5,036 | **strong** (meta-analysis) against "less is always better" | Scheibehenne et al. 2010, *J Consumer Research* 37:409–425 [B-new] |
| FVG / OB vs matched placebo | FVG: no detectable advantage in 14 measurements; OB: no reliable gap | **moderate** (published method, author-run, reproducible in principle) | TradingView: FVG Statistics with Placebo Control; OB Statistics vs Random Levels [B-new] |
| DOL rules in shipped tools | Tier/distance; nearest; ≥ 55% side share; magnet score | **none** published; **moderate** now via B's replication (§2.2) | Vendor pages; §2.2 [B-corr] |
| Popularity of measurement-first tools | Boost counts | **none** for accuracy; counts unverifiable (A's own figures conflict: 2,239 vs 115) | Dropped [B-corr] |

### 2.2 B's replication: the competitor selection rules on 14 datasets [B-new]

**Setup.** Sibling candidate datasets `calib_ml_tools/res_*.pkl`:
- engine-like generator: chart pivots L = 5, external pivots L = 20 + PDH/PDL, FVG near edges;
- liquidity hit = strict trade-through, FVG hit = touch;
- H = 30 bars; evaluation bars every 10 bars; candidates 0.25–10 ATR;
- `pb` = engine-style distance-matched random-level baseline.

**Data.** ES, NQ, YM, RTY, CL, GC at 5m and 1h; EURUSD 1h; S&P 500 daily. About 1,040 evaluation picks per rule per set.

**Rules:**
- *Nearest*: either side.
- *Nearest bias-side*: ICT doctrine / OB-Pro style, falling back to the other side.
- *Tier/dist*: LuxAlgo tiers, with external = 2 or 3 and EQ = 2.
- *Engine-like hand score*: draw-side first, as step 19.
- *Max d·PoT*: the expected-reach picker from sibling CAL.
- *Random*.

The bias proxy D = 0.5·sign(C − SMA200) + 0.3·sign(C − SMA50) + 0.2·sign(20-bar return), gate 0.35. SE is block-clustered over 2H-bar blocks.

| Rule (pooled mean of 14 sets) | Hit | Baseline | Excess pp (SE) | Mean distance ATR | **ATR delivered** | Paired Δ delivered, engine-like − rule (sets with \|z\| ≥ 2) |
|---|---|---|---|---|---|---|
| Nearest (any side) | 0.720 | 0.719 | +0.1 (1.6) | 1.28 | 0.80 | +0.14 (12/14) |
| Nearest bias-side (ICT doctrine) | 0.661 | 0.671 | −1.0 (1.7) | 1.57 | 0.86 | +0.08 (12/14) |
| Tier/dist (LuxAlgo-like, ext = 2) | 0.647 | 0.655 | −0.8 (1.7) | 1.68 | 0.87 | +0.07 (11/14) |
| Tier/dist (ext = 3) | 0.626 | 0.635 | −1.0 (1.7) | 1.82 | 0.87 | — |
| **Engine-like hand score, draw-first** | 0.602 | 0.611 | −0.9 (1.9) | 1.93 | **0.94** | — |
| Max d·PoT (expected reach) | 0.411 | 0.424 | −1.3 (2.1) | 3.14 | **1.20** | −0.26 (13/14) |
| Random candidate | 0.333 | 0.335 | −0.2 (1.5) | 4.44 | 0.90 | +0.04 (2/14) |
| Engine-like pick, "clear" bars (\|D\| ≥ 0.35) | 0.593 | 0.604 | −1.1 (2.1) | 1.98 | 0.94 | — |
| Engine-like pick, "balanced" bars | 0.633 | 0.634 | −0.1 (3.7) | 1.75 | 0.94 | — |

Reading:
1. **No rule has an information edge.** Realised hit equals the baseline within about ±1 pp pooled; per-set excess ranges from −10.5 to +6.6 pp, consistent with noise. Paired excess differences vs the engine-like score reach |z| ≥ 2 in about 4 of 78 rule-set pairs, the chance rate. Raw hit rates rank purely by distance.
2. **Rules differ in utility.**
   - The engine-like multi-pillar score picks farther targets than the free rules and delivers 8–17% more ATR per target, consistently (11–12 of 14 sets at z ≥ 2).
   - An expected-reach objective (d·PoT) delivers another 27% (13/14 sets).
   - Theory check (sibling): for driftless motion `d·2Φ(−d/s)` peaks at d = 0.75·σ√H, where PoT = 45%.
3. **"Balanced" abstention shows no precision gain** (excess −0.1 pp balanced vs −1.1 pp clear, overlapping SEs). There is nothing to gain by abstaining when no selector has information. COMP-6 is downgraded accordingly.
4. **Caveats.**
   - The generator is simplified: no MTF structure, an SMA-based D, and an approximate tier map for external pools.
   - Evaluation bars overlap (block-clustered SE).
   - The engine's own ledger has far fewer trials (about 150–400 per 5,000 bars). In the panel, excess differences will read "tie", and ATR-delivered differences of about 0.1 ATR will reach z of only about 1.5–2.
   - Grade: **moderate** (reproducible, 14 datasets, consistent direction).

---

## 3. Engine gap analysis (`baseline_v2.pine`)

| Concept | Status | Lines | What the engine does / what differs |
|---|---|---|---|
| Single committed DOL, bar-close confirmed | **present** | 1964–2036 | Draw-side first, counter-draw fallback, 2-bar challenger, 2× hysteresis across sides, off-killzone multiplier (976). Stronger than ASXLT, LuxAlgo or AGPro; softer than a lock (SMC-2). |
| Multi-source pools + PD arrays | **present** | 84–117, 1084–1250 | Broader than any surveyed competitor. |
| Random-level null in the ledger | **present** | 1314–1323, 1461–1500, 2376–2430 | B-corr: not unique overall (placebo scripts exist), but unique among DOL selectors. |
| Benchmark vs simple competitor rules | **missing** | — | B's replication predicts "tie" on excess and "engine ahead" on ATR delivered (§2.2). COMP-3 adds both metrics via the shared shadow mechanism (SKEP-5 / CAL-3). |
| PoT with explicit horizon / reference class | **partial** | 176–184, 1303–1312, 2225 | H = 30 bars is never shown in Clean (2225) or the tooltip (2206). Bars are not clock time (TIME-4). |
| Sample size (k of n) next to PoT | **missing** | 2206, 2225, 2379 | n appears only in the Terminal accuracy header (2379). No PoT reliability buckets (SMC-1 / TIME-2 compute; COMP-4 displays). |
| Reached state in the Clean label | **wrong** | 2062–2067, 2225 | `activePoT := 0.95` on a live sweep, so the label shows "PoT: 95.0%" for a hit target. The "DOL PoT %" plot (2446) also reads 95. Terminal shows "✕ SWEPT ▸" (2237). |
| Why the chart is blank | **missing** [B-new] | 2203, 2068 | Clean draws nothing in three different cases: no level ≥ `minScore`; target filtered by `minPoT` (`dolShown` false); `showDOL` off. The user cannot tell them apart. |
| Target price / distance / runner-up / expected reach in the tooltip | **missing** | 2206–2209 | The tooltip lists the tag, pillars and multiplier only. |
| Balanced / no-draw state | **partial** | 1895, 2342, 2367 | Terminal shows "BALANCED" and "scanning…". Clean shows nothing. B's replication found no accuracy reason to abstain (§2.2). |
| Lifecycle (rest / swept / broken) shown | **partial** | 623, 1580–1590 | ICT-2 covers the logic. |
| Ghost trail | **present** (off by default) | 210–211, 1253–1263 | FIFO `ghostMax`. |
| Outcome stamps | **missing** | 375–396, 1426–1500 | Trials know `bars`, `mae` and `status`; nothing is drawn. |
| Alerts: new / iFVG / sweep / flip | **present** | 2077–2094 | As in the reference product. |
| Sweep alert gated to the shown and announced target | **wrong** [B-new] | 1504–1509, 2084–2085, 2092 | `liveSweep` tests `activeLv` with no `dolShown` or `lastAnnId` check. With *Minimum PoT* > 0, users get "target swept" for targets never shown or announced. |
| Timeframe in `alert()` text | **missing** [B-new] | 2079–2088 | `syminfo.ticker` only; ambiguous when the indicator runs on several charts. |
| Alerts: approach / abandoned / reached-with-result | **missing / partial** | 1584–1590, 2021–2036 | The events exist in code; no alert is raised. The sweep alert is intrabar and carries no result. |
| Alerts: toggles, filters, JSON, placeholders | **missing** | 2077–2094 | Every `alert()` fires unconditionally; plain text; `alertcondition`s are static although "DOL Price" and "DOL PoT %" plots exist (2444, 2446). |
| Plot output contract | **partial** [B-new] | 2436–2448 | "DOL Price" plots `activeLv.price` even when the target is filtered (`dolShown` false), so a `{{plot()}}` webhook would expose a hidden target. No side or state series. |
| Status-line hygiene | **wrong** [B-corr] | 40–226 | **76** of **104** inputs print in the legend. |
| Tooltips / `active` | **partial** [B-corr] | 40–226 | **76** of 104 inputs lack a tooltip, including all 10 session inputs; `active` unused. |
| Table text size / cell tooltips | **missing** | 604–610, 2294–2310 | Fixed `size.small`; `table.cell(..., tooltip)` unused. |
| Price-scale target tag | **missing** | 2444 | Data Window only. |
| Distance units | **partial** | 2243, 2351 | ATR only. |
| Light-theme contrast | **partial** | 226–284, 2166, 2189, 2212, 2223, 1256, 2278 | Dark-tuned themes; neon text on transparent labels and the white core fail on white. |
| Autoscale safety | **partial** | 2250–2287 | LVN zones are the nearest `lvnN` per side within the 120-hour profile, with no ATR cap (2275, 2282). The DOL is bounded by the pool ejection distance. |
| Request budget | **present** [B-corr] | 923–925, 939, 981, 982 | 5 `request.security` + 1 `request.security_lower_tf` = **6** (A: 6 + 1). Two calls share `tfH` (923, 939) and can be merged (PENG-2), which matters for the Pine Screener's 5-call limit. |
| Pine Screener | **missing** | 2444–2448 | No `display.pine_screener` plots. |
| Repaint transparency | **present** | 1–29, README | Live PoT and sweep alert disclosed; the README avoids reproduction claims. |
| ACTION row | **not proposed** | — | Joslyn & LeClerc: categorical advice alone did not help decisions. |

---

## 4. Proposals (best first; 11)

Overlap map: COMP-1 = UX-1 = PENG-1 (same fix, implement once). COMP-4 ↔ UX-3 (state grammar) and SMC-1 / TIME-2 (calibration data). COMP-3 ↔ SKEP-5 / CAL-3 (shared role mechanism). COMP-8 → UX-2. COMP-9 ↔ PENG-2 (request merge). COMP-2 and COMP-5 provide the alert and stamp hooks for ICT-2 and SMC-2.

### COMP-1 (P1, S) · Status line and settings hygiene [A, B-corr counts]

**Problem.** 76 values print next to "DOL Engine v2"; the reference shows the name only. 76 inputs have no tooltip; `active` is unused.

**Spec.**
1. Add `display = display.none` to all 76 `input.int`, `input.float`, `input.string`, `input.timeframe` and `input.session` calls (59–211).
   - Write the literal in each call (the parameter is `const plot_display`, input.md:27).
   - Optional: keep `modeIn` with `display = display.status_line` behind no input; default `display.none` to match the reference.
2. `active` (input bool, input.md:28):
   - `cHTF`, `cSTF`, `cEXE`: `active = modeIn == "Custom"`;
   - `sessAs`, `sessLo`, `sessNA`: `active = useSess`;
   - the four LVN inputs: `active = showLVN`;
   - `ghostMax`: `active = showGhost`;
   - `hudSize`: `active = uiStyle == "Terminal"`;
   - `uAbove`…`uText`: `active = theme == "Custom"`.

   All are declared before their dependants, so there are no forward references.
3. Tooltips, priority order:
   - session inputs: window, "read in Session Timezone", "Asia crosses midnight";
   - `pivLen`, `eqTol`, `poolMax`, `maxATR`, `wS`/`wM`/`wL`;
   - `potH`: "bars; on a 5-minute chart 30 bars ≈ 2.5 h".
4. `tblSz = input.string("Small", "Panel Text", options = ["Tiny", "Small", "Normal"], group = G_TABLE, display = display.none)`. Map it to a global `string tblTx` declared before `f_cell` / `f_cellC` (604–610), which read the global.

**Evidence.** Mechanism **strong** (official reference); benefit **weak** (reference look, user complaints; clutter evidence is mixed, §1.13).
**Risk.** None functionally. **Effort.** S. **Ledger.** Not measurable.

### COMP-2 (P1, M) · Alert system v2: correctness first, then events, toggles, JSON, placeholders [A, B-corr, B-new]

**Part A: correctness (ship first, S).** [B-new]
1. Gate the sweep alert to the target the user was told about, without changing the label logic (`sweptNow` stays as is):
   - `bool sweepAlert = liveSweep and not na(activeLv) and activeLv.id == lastAnnId`;
   - use `sweepAlert` in `alert()` (2084) and in `alertcondition` (2092).
2. Put the timeframe in every `alert()` message: `" · " + syminfo.ticker + " " + timeframe.period`.
3. Output consistency:
   - `dolPriceOut := dolShown ? activeLv.price : na` (2441);
   - the "DOL PoT %" plot gives `na` while `sweptNow` (2446), after COMP-4's reached state.

**Part B: events.** All decided on `barstate.isconfirmed` and sent with `alert.freq_once_per_bar_close`. The intrabar sweep stays `freq_once_per_bar`. Never `alert.freq_all` (15-in-3-minutes stop rule).

- **Inputs** (new `const string G_ALT = "Alerts"` in 42–57; numeric and string inputs get `display = display.none`):
  - `alNew` (true), `alHit` (true), `alNear` (true), `alAbd` (false), `alIfvg` (true), `alFlip` (false), `alLive` (true);
  - `alNearATR` float 0.25 (min 0.05);
  - `alDrawOnly` bool false;
  - `alFmt` "Text" / "JSON";
  - `alGap` int 0: minimum bars between any two `alert()` calls (for seconds charts).
- **State** (STATE, after 1039): `var int nearAnnId = -1`, `var int lastAlertBar = -100000`, `var float nearN = 0.0`, `var float nearK = 0.0`.
- **Per-bar** (next to `newDolEvent`, 1511): `bool hitEvt = false`, `bool abdEvt = false`, `string abdWhy = ""`, `string evName = ""`, `float evPx = na`, `int evSide = 0`, `int evBars = 0`, `float evMae = na`.
- **Reached.**
  - Step 2 (1549–1556): when a booked trial has `t.lvId == activeId and t.status == 1`, set `evMae := t.mae`.
  - Step 3 (1584–1590): inside `if lv.id == activeId`, when `lv.id == lastAnnId`: set `hitEvt := hit`, `abdEvt := not hit`, `abdWhy := "ejected"`, `evName := f_shortName(lv.kind, lv.src)`, `evPx := lv.price`, `evSide := lv.side`, `evBars := bar_index - activeSince`.
  - If `lv.id == nearAnnId`, also `nearK += 1`.
- **Abandoned.** In step 19, before `activeId := pickId` (2034): when `pickId != activeId and curI >= 0 and activeId == lastAnnId`, set `abdEvt := true` and `abdWhy := curElig ? "replaced" : "invalidated"`, and fill `evName`/`evPx`/`evSide` from `pool.get(curI)`.
- **Approaching** (ALERTS section, global scope, after `annNow` has updated `lastAnnId`):
  - `float gapX = na(activeLv) ? na : activeLv.side == 1 ? activeLv.bottom - high : low - activeLv.top`;
  - `bool nearEvt = barstate.isconfirmed and not na(activeLv) and activeLv.id == lastAnnId and activeLv.id != nearAnnId and gapX > 0 and gapX <= alNearATR * atr`;
  - `if nearEvt` → `nearAnnId := activeLv.id` and `nearN += 1`.
  - It uses the bar's extreme, so a near-miss counts; a bar that also hit fires "reached" instead.
- **Filters:**
  - `bool okSide = not alDrawOnly or not activeCtr`;
  - `bool okGap = bar_index - lastAlertBar >= alGap`;
  - each `alert()` checks its own toggle plus `okSide and okGap`, then sets `lastAlertBar := bar_index`.

**Part C: message builder.** `f_msg(string ev, string nm, int side, float px, float pot, string extra) =>`, declared after the LEVEL METHODS (~698) so it can use only globals declared earlier: `alFmt`, `H`.
- **Text:** `"DOL ▸ " + ev + " · " + nm + " @ " + str.tostring(px, format.mintick) + (na(pot) ? "" : " · PoT " + str.tostring(pot * 100, "0") + "% in " + str.tostring(H) + " bars") + extra + " · " + syminfo.ticker + " " + timeframe.period`.
- **JSON** (numbers via `str.tostring`, never `str.format`):
  ```
  {"event":"reached","symbol":"<syminfo.tickerid>","tf":"<timeframe.period>","side":"buy","type":"PDH",
   "price":5123.25,"pot":70.1,"horizon_bars":30,"bars":14,"mae_atr":0.62,"counter":false,"time":<time_close>}
  ```
  `abandoned` adds `"reason"`.
- Validate the output once with a JSON parser: TradingView only sends `application/json` when it parses.

**Part D: `alertcondition`s** (const messages; single quotes around placeholders).
- Keep the four titles and upgrade their messages:
  - `'DOL Engine: new target on {{ticker}} ({{interval}}) at {{plot("DOL Price")}}, PoT {{plot("DOL PoT %")}}%'`;
  - the swept condition uses `sweepAlert`.
- Add "DOL Target Approaching" (`nearEvt`), "DOL Target Reached (close)" (`hitEvt`) and "DOL Target Abandoned" (`abdEvt`). That makes 9 plots + 7 conditions, far below the limit.

**Part E: ledger.** Full view row "NEAR→HIT k/n" from `nearK` / `nearN` (how often an approach alert was followed by the hit), and abandonment counts by reason.

**Value.** Users can trade from one alert slot. Bots get structured data. No phantom "swept" messages.
**Evidence.** **moderate**: the alert-fatigue meta-analyses argue for few, deduplicated defaults; the platform throttle and content type are documented. Approach thresholds are vendor conventions (**weak**).
**Risk.** Noise, so abandoned and flip alerts default to off. JSON validity. Abandoned-on-replace depends on the overhaul fix to the near-distance taper; otherwise replacements cluster just before hits.
**Effort.** M (Part A alone: S).

### COMP-4 (P1, S) · Honest, explanatory Clean label [A, B-new additions]

Coordinate with UX-3, which owns the state grammar; the spec below adopts its wording.

**Spec.**
1. **Reached.** In the Clean branch (2225): `string potTxt = sweptNow ? "✓ Reached" : "PoT: " + str.tostring(activePoT * 100.0, potFmt) + "%"`. Line 1 stays "Target: X", so the reference look is unchanged.
2. **Precision input.** `potFmt` from "0.1%" (default, reference look), "1%" or "5%". The 5% option uses `math.round(p * 20) / 20` before formatting.
3. **"Why blank" hint** [B-new; absorbs COMP-6's display]. When `showDOL and barstate.islast and (na(activeLv) or not dolShown)`, draw one dim label at (`bar_index + extBars`, `close`) reading "No target", with `color.new(cGhost, 30)` text and a transparent background. Its tooltip gives the reason:
   - "Nothing within Max ATR Distance scores ≥ Min Score (35)";
   - "PDH filtered: PoT 12% < Minimum PoT 20%";
   - when `dirSide == 0` and the best buy-side and sell-side scores are within 5 points: "Balanced: BSL 61 / SSL 58".

   Input `hintOn` bool true. It never shows while a target is displayed, so the reference look is preserved.
4. **Tooltip** (built at `barstate.islast` inside the existing block; ≤ 7 lines):
   ```
   PDH · EQx2 — score 72.4 · draw-side (D +0.52)
   Price 5123.25 · 24.0 pts · 0.47% · 2.3 ATR away
   PoT 70% = chance of a touch within the next 30 bars (≈ 2 h 30 m) · Empirical model
   Past targets shown at 60–80%: 41 of 63 reached        (or "calibrating, n = 7")
   Expected reach if aimed here: 0.70 × 2.3 = 1.6 ATR     [B-new]
   Runner-up: PWH 65.1 (−7.3) · this target held 14 bars
   Proximity 62 · Freshness 80 · Confluence 35 · Density 71 · Draw 90 · ×1.10
   ```
   - **Clock text.** `f_dur(int secs)` turns `H * timeframe.in_seconds()` into "45 m", "2 h 30 m" or "6 d". Prefix "≈": session gaps break the mapping; TIME-4 refines it. This line fixes the reference-class problem.
   - **k of n.**
     - Add `float pShow = na` to `Trial` (375–396), set in `f_openTrial` (1426) to `f_potModel(d, lv.side, potMu * lv.side)` (declared at 1303, so no forward reference).
     - Add `var array<float> calN = array.new<float>(5, 0.0)` and `calK` (STATE).
     - In `f_book` (1461): bucket `b = math.min(4, int(t.pShow * 5.0))`; increment `calN[b]`, and `calK[b]` when y = 1.
     - Print when `calN[b] >= 10`. If SMC-1 / TIME-2 land, read their arrays instead.
   - **Expected reach** = `activePoT × dAtr`. B's replication shows this is the quantity that separates pickers (§2.2). It answers "where to take profit" in expectation, without advice.
   - **Runner-up.** In step 19 keep the second-best eligible score and index next to `aS`/`aI` (1965–1990). At commit, store `var float runS`, `var string runName`.
5. **Bias table cell tooltips.** Add a `tip` argument to `f_cellC`, passed to `table.cell(..., tooltip = tip)` (table.md:53, 69), for example "Swing: BULL (confirmed pivots, body break) · internal: BEAR · price at 62% of the dealing range (premium)". Built from `htfIB`/`htfRH`/`htfRL` etc. (UX-5 adds an alignment cue.)

**Value.** Removes a misleading readout. Answers when (horizon), how sure (k of n), how much (expected reach), why this one (runner-up) and why nothing (hint).
**Evidence.** **moderate**: reference class (Gigerenzer 2005) and uncertainty communication (Joslyn & LeClerc 2012) are strong in their domains; natural frequencies moderate for this use; transfer to trading assumed.
**Risk.** Tooltip length. k-of-n must use the PoT at assertion, not the live tick.
**Effort.** S.
**Ledger.** The buckets are a reliability diagram. Print the mean |bucket hit − bucket midpoint| as the calibration gap.

### COMP-3 (P2, M) · Competitor rules as roles in the shared shadow ledger, judged on ATR delivered as well as edge [A, B-corr]

**Why changed.** A proposed comparing *edge* deltas and grading the result "✓ BEATS / ≈ TIE / ✕ LOSES". B's replication (§2.2) shows every rule's edge ≈ 0, so that verdict would read TIE almost always (paired |z| ≥ 2 in about 4 of 78 pairs). The comparison that does separate rules is **ATR delivered per target**: the engine-like score is +0.07 to +0.14 ATR ahead of the free rules on 11–12 of 14 sets, and −0.26 behind an expected-reach picker. Users asked "is this better than the free tools?" The honest answer is "same hit rate vs chance, more distance delivered", which the panel can show.

**Spec.** Implement inside the single role/probe mechanism of SKEP-5 (`Trial.role`) or CAL-3 (`Probe.role`); do not build a second one.
- **Roles.**
  - NEAREST (either side) and TREND/NEAREST-BIAS (nearest on the `htfBias` side): already in SKEP-5.
  - New **TIER/DIST** (LuxAlgo-like): over candidates with `minDistATR ≤ dAtr ≤ maxATR`, `key = tw / math.max(dAtr, 0.25)`:
    - `tw` = 4 for src 7 (PW), 3 for src 6 (PD), 2 for src 3–5 (sessions) or `eqCount > 0` (take the max), 1.5 for kinds 2–3 (FVG), 1 otherwise;
    - side: `htfBias` if ≠ 0, else `dirSide`, falling back to the other side when the bias side is empty.
- **Opening.** Same bar as an engine trial opening (step 20, 2037–2045). Shadow `lvId` offset (`-1000000 - role`) so the `has` check ignores shadows. Same `f_step`. `f_book` routes by role and never touches the per-family, calibration or main stats.
- **Metrics per role.** n; hit %; excess Σ(y − pBase)/n with block SE; **ATR delivered** Σ(y·d0)/n; paired Δ vs the DOL on shared blocks (shared-path noise cancels).
- **Panel** (Full view, after RACE, 2422): `vs NEAREST  hit 72/60% · Δexc +0.4±3.1pp · ATR del 0.80/0.94`, the same for TIER/DIST, and optionally MAX-REACH (sibling CAL-5).
- **Verdict wording:**
  - "same accuracy vs chance" when |Δexc| < 2 SE;
  - "delivers more / less per target" when |Δdel| ≥ 2 SE;
  - never a raw-hit comparison.
- **Data Window** plots: "Δ ATR del vs Nearest", "Δ ATR del vs Tier/Dist".

**Value.** An honest, measured differentiator. It is also the A/B harness for every scoring change, for example promoting d·PoT if it keeps winning.
**Evidence.** **moderate** (B replication on 14 datasets; the M4 principle is strong).
**Risk.**
- CPU: one extra pass over ≤ 40 levels per opening, plus ≤ 2× trials.
- Low per-chart power at about 150–400 trials: show ± bands, not verdict glyphs.
- Readers may confuse hit with value, so the tooltip explains ATR delivered.

**Effort.** M (about 60 lines on top of SKEP-5 / CAL-3).

### COMP-7 (P2, S) · Price-scale target tag, distance units, autoscale safety [A, B-corr risk]

**Spec.**
1. **Tag.** `plot(dolShown ? activeLv.price : na, "DOL Price", color = activeLv.side == 1 ? cAbove : cBelow, display = tagOn ? display.data_window + display.price_scale : display.data_window)`.
   - `display` is `input plot_display` (plot.md:243), so a ternary on an input bool is valid; `tagOn` is an input bool, default true.
   - The tag adds no new autoscale range in Clean, because the DOL box already spans the target price.
   - If testing shows that `display.price_scale`-only plots enter autoscale, nothing changes: the box already does.
   - Keep the title, which `{{plot("DOL Price")}}` uses.
2. **Distance unit.** `distUnit` = ATR / Points / Ticks / Pips / %. Pips = `syminfo.mintick * 10` when `syminfo.type == "forex"`, else ticks. Used in the HUD DIST line (2243), the panel PoT row (2351) and the COMP-4 tooltip.
3. **Autoscale safety.**
   - LVN loops (2275, 2282): add `and math.abs((zTop.get(q) + zBot.get(q)) / 2.0 - close) <= maxATR * atr`.
   - Objective and reach bands: skip beyond `maxATR * ejectMult`.
   - Add a tooltip line to `extBars`: "Squashed candles? Right-click the price scale → Scale price chart only".

**Evidence.** **weak** (benefit); the mechanism is **strong** (help 43000762934).
**Effort.** S.

### COMP-5 (P2, S) · Outcome stamps that show expectation next to result [A, B-new framing]

**Why the framing changed.** Algorithm aversion: a bare "✕ missed" erodes trust even when the engine is well calibrated (Dietvorst et al. 2015). Showing the PoT at assertion makes misses look like what they are, the 30% that was expected.

**Spec.**
- `stampMode` = Off / Terminal only (default) / Always; `stampMax` int 8.
- **Reached** (in the COMP-2 hook, step 3 when `lv.id == activeId and hit`): `label.new(bar_index, lv.side == 1 ? lv.top : lv.bottom, "✓ " + str.tostring(evBars) + "b · " + str.tostring(pAssert * 100, "0") + "%", style = lv.side == 1 ? label.style_label_down : label.style_label_up, color = color.new(cPanel, 100), textcolor = color.new(c, 10), size = size.tiny)`.
  - `pAssert` = `pShow` of the booked trial (COMP-4), captured in step 2 like `evMae`.
- **Abandoned:** "⊘ replaced · 55%" or "⊘ ejected" in the ghost colour at the old level.
- **Expired while live:** no stamp. UX-3's "· late" state covers it.
- Storage: `var array<label> stampL`, FIFO. Create stamps only when `inCalc`.
- Label budget: 8 stamps + 12 ghosts + about 8 HUD/hint labels, far below 500.

**Evidence.** **weak** (convention); trust mechanism **strong** (both directions).
**Risk.** Clutter, hence off in Clean by default (reference look).
**Effort.** S.

### COMP-8 (P2, S) · Light-theme contrast: adopt UX-2 [A, B-corr]

A's spec gave single light variants. UX-2 showed, and B verified, that a single swap breaks the dark Clean label: `#0B7A2E` reads 3.31:1 on `#161616`. Implement UX-2 instead.
- **Detection.** `bool lightBg = (0.2126*color.r(chart.bg_color) + 0.7152*color.g(chart.bg_color) + 0.0722*color.b(chart.bg_color)) / 255 > 0.5` (`chart.bg_color` is `input color`; gradients return the midpoint).
- **Graphics role** (on the chart background: zone border and fill, glow, core, tether, transparent-background label text, LVN, ghosts): light variants on light charts, for example buy `#0B7A2E` (5.47:1 on white), sell `#C8102E` (5.88:1), LVN `#9A6B00` (4.69:1), ghost `#5F6B7A` (5.43:1). Core line: `lightBg ? c : color.new(color.white, 15)`.
- **Text-on-panel role** (Clean label, tables): keep the neon colours.

**Evidence.** **strong** (WCAG + computed). **Effort.** S.

### COMP-12 (P3, S) · Same-side target ladder (TP1 / TP2) [B-new]

**Problem.** Users ask where to take profit, and vendors sell TP1/TP2/TP3 ladders. The engine's secondary targets (2170–2190) are the next-best *scores* on either side, so they do not form an ordered path.

**Spec.**
- Input `secMode = input.string("By score", "Secondary Targets Mode", options = ["By score", "Ladder (same side)"], group = G_DOL, display = display.none)`.
- In Ladder mode, among pool levels with `side == activeLv.side`, liquidity or arrays, `distance > activeLv.distance(close)` and `dAtr ≤ maxATR`, take the `secN` nearest by distance.
- Labels: `"TP2 · PDH · 41%"` (PoT from `f_potModel`, already computed at 2184), plus `" · 2.1R"` when `showInv` and the invalidation exist.
- By geometry the PoTs decrease monotonically along the ladder. Show them as given, without resorting.

**Value.** A take-profit ladder whose ordering is a theorem, not a heuristic, with a PoT per rung.
**Evidence.** Ordering **strong** (path continuity); benefit **weak**.
**Risk.** None for the default (By score). **Effort.** S.

### COMP-9 (P3, M) · Output contract plus Pine Screener [A, B-corr]

**Spec.**
1. **Output contract.** Keep the first 20 plots stable for `{{plot_n}}`:
   - "DOL Price" (`na` when not shown);
   - "DOL Side" (+1 / −1 / 0);
   - "DOL State" (0 none, 1 draw-side, 2 counter, 3 reached, 4 filtered);
   - "DOL PoT %" (`na` when reached);
   - "DOL Dist ATR", "DOL Score", "Draw D", "HTF Bias", "Bars Since Target".

   All `display.data_window`, with `display.pine_screener` added (constants.md:125).
2. **Screener feasibility** [B-corr]:
   - The screener's help page lists **at most 5 `request.*` calls**; the engine has **6** (923, 924, 925, 939, 981, 982). Merge the two `tfH` calls (923 and 939) into one tuple request through a wrapper `f_htfAll()` returning the 12 + 5 values (PENG-2), which brings it to 5.
   - Only the last 500 bars are calculated, so the empirical PoT (needs ≥ 600 samples) falls back to the analytic model and the ledger is empty. Document both.
   - `input.timeframe` values are ignored (Custom TFs fall back to defaults); other inputs work.
   - Premium plan and above only.

**Evidence.** **none** (novel). **Risk.** May still exceed time limits, so test live first. **Effort.** M.

### COMP-11 (P3, S) · Wording honesty: placebo language, score vs probability, publishing rules [B-new]

**Spec.**
1. In the README and any published description, describe EDGE as "hit rate minus the hit rate of a matched random level at the same distance (a placebo)", the vocabulary of the placebo-statistics scripts.
2. Say plainly that PoT is mostly distance and volatility, that any level that far is touched about as often, and that the engine's value is *which* level and *how far* (§2.2). This pre-empts the "✕ NO EDGE" surprise.
3. Rename the Terminal verdict "✕ NO EDGE" to "≈ RANDOM" (z < 1), keeping "~ WEAK" and "✓ EDGE", to match how the placebo scripts word null results ("no detectable advantage").
4. Never call a score a probability (AGPro convention). Keep the 95% cap.
5. Publishing rules: no claims or demos implying the engine reproduces a closed-source script; keep "independent implementation … from a public feature description"; never name the closed product.

**Evidence.** **weak** (convention); the rule text is **strong** (platform rules). **Effort.** S.

### COMP-6 (P3, S/M) · Balanced / no-draw ledger split and coverage (downgraded) [A, B-corr]

**Why downgraded.** Abstention only raises precision when the selector has information. B's replication found the engine-like pick's excess was −0.1 pp on balanced bars vs −1.1 pp on clear bars, with overlapping SEs: no gain. The display half moved into COMP-4 (hint label).

**Remaining spec.**
- Ledger `covN` / `covK`: bars in the window and bars with an asserted DOL, giving coverage %.
- `bool bal` on `Trial` (set when `dirSide == 0` and the buy-side and sell-side best scores are within `balGap` = 5) to report CLEAR vs BALANCED excess and ATR delivered separately in the Full view.
- Optional `balMode` "Show both" draws the other side's best as a thin secondary. The default stays "Show best", per the decision history.

**Evidence.** **weak**. **Effort.** S/M.

### Considered and not proposed [A, B]

- Target lock mode: SMC-2. A lock is also the "slight control" lever against algorithm aversion (§1.13).
- Clock-time horizon and PoT by session end: TIME-4.
- Route CLEAR / BLOCKED: ICT-5.
- Sweep vs break learner: ICT-2.
- Per-category reach table: ICT-1 / CAL-3.
- Which side first: BIAS-1 / ICTS-3.
- **ACTION / STATUS row:** rejected. Joslyn & LeClerc found categorical advice alone did not help, and an ACTION row reads as advice.
- **Streak counters:** rejected (gambler's-fallacy framing).
- **Liquidation and order-book heatmaps:** data not visible to Pine; magnitude does not tell sequence.

---

## 5. Sources

**Competitor tools (public descriptions; tradingview.com pages were read by A, and by B only through search summaries)**
- Reference product page: https://www.tradingview.com/script/ByeifG90-TradeAxis-DOL-Draw-on-Liquidity/ (named here only as a source; never in published text)
- LuxAlgo Draw on Liquidity: https://www.luxalgo.com/library/indicator/draw-on-liquidity/ ; https://www.luxalgo.com/library/concept/draw-on-liquidity/
- Draw On Liquidity Planner [AGPro]: https://www.tradingview.com/script/skYKmBdk-Draw-On-Liquidity-Planner-AGPro-Series/
- Liquidity Draw Probability Map [ForexCracked]: https://www.tradingview.com/script/l4nMbqY8-Liquidity-Draw-Probability-Map-ForexCracked/ ; https://www.forexcracked.com/?p=219435
- Liquidity Draw (target lock, 55% side share): https://www.tradingview.com/script/nmEliXkz-Liquidity-Draw/
- [B-new] Liquidity Magnet [LunqFX]: https://www.tradingview.com/script/w8DHUZp8-Liquidity-Magnet-ICT-Liquidity-Sweeps-LunqFX/
- [B-new] Liquidity Map & Order Blocks [MQLSoftware]: https://www.tradingview.com/script/qBesPbpE/
- [B-new] Order Block Statistics: Real Win Rate vs Random Levels: https://cn.tradingview.com/script/yFmy3VBi-Order-Block-OB-Statistics-Real-Win-Rate-vs-Random-Levels/
- [B-new] FVG Statistics with Placebo Control: https://de.tradingview.com/script/Kbq3WncE-Fair-Value-Gap-FVG-Statistics-with-Placebo-Control/
- [B-new] M-Alpha Fair Value Gaps (fill rate, no control): https://www.tradingview.com/script/KDRll5dY/
- [B-new] ICT Killzones & Pivots [TFO]: https://www.tradingview.com/script/nW5oGfdO-ICT-Killzones-Pivots-TFO
- [B-new] Smart Money Concepts [LuxAlgo] (Historical / Present): https://www.tradingview.com/script/CnB3fSph-Smart-Money-Concepts-LUX/
- [B-new] Liquidity Radar variants (incl. PRO with TP1–TP3, 19 alerts): https://in.tradingview.com/script/WJuCUyMH/ ; https://www.tradingview.com/script/RNkucdnJ/
- [B-new] Draw on Liquidity [PhenLabs]: https://www.tradingview.com/script/b66E7VZK-Draw-on-Liquidity-PhenLabs
- Flux Charts Liquidity Sweep Profiler: https://www.tradingview.com/script/LM4xxgfj
- probability_of_touch: https://www.tradingview.com/script/IgAKPrYh-probability-of-touch/
- [A, unverified by B] ASXLT DOL https://www.tradingview.com/script/xgF57cH4-ASXLT-DOL-Draw-on-Liquidity/ ; ICT Order Block Pro https://www.tradingview.com/script/oObsuObl-ICT-Order-Block-Pro/ ; ICTMIKA https://www.tradingview.com/script/DCZoWd3a ; AetherEdge https://www.tradingview.com/script/jkgBMcNr ; P2P 86 https://www.tradingview.com/script/20ARUMK8 ; DOL Detector PRO https://www.tradingview.com/script/B3tYa8yh ; LuxAlgo PAC docs https://docs.luxalgo.com/platform/algos/price-action-concepts/liquidity ; ProEA https://proea.app/en/blog/best-previous-day-high-low-indicator-tradingview ; toodegrees https://www.toodegrees.trade/indicators/session-statistical-mapping ; edgeful https://www.edgeful.com/blog/posts/pivot-points-indicator-tradingview ; Coinglass https://www.coinglass.com/pro/futures/LiquidationHeatMap ; Hyblock https://academy.hyblockcapital.com/tools/liquidation-levels-1 ; MQL5 repaint blog https://www.mql5.com/en/blogs/post/779521
- [B-new] Bookmap on pulled liquidity and spoofing: https://bookmap.com/blog/how-price-reacts-around-fake-liquidity-bait-walls-and-phantom-size ; https://bookmap.com/blog/what-is-spoofing-in-trading
- [B-new] NT8 killzones / session levels: https://www.eltraderfinanciado.com/en/trading-tools/ninjatrader-indicators/session-levels-killzones

**User voice** [A]: Reddit r/ICTMentorship 1wfdm14; r/InnerCircleTraders 1pl85os, 1pp1q6y, 1rgrsic, 1rdau4w; r/Daytrading 1tlvv19, 1tqju9m, 1kci9y1; r/Trading 1wm8xe2 (https://www.reddit.com/r/<sub>/comments/<id>/).

**Platform documentation**
- Local Pine v6 mirror: reference/input.md:27–28; reference/plot.md:243; reference/constants.md:13, 125–126, 160; reference/table.md:53, 69; reference/chart.md:7–12; reference/core.md:57, 63; concepts/alerts.md (placeholders section); concepts/strings.md:463–489 (`str.format` grouping)
- [B-new] Alert triggered too often and stopped: https://www.tradingview.com/support/solutions/43000690939-alert-was-triggered-too-often-and-stopped/
- [B-new] Webhooks (content type, 2FA): https://www.tradingview.com/support/solutions/43000529348-how-to-configure-webhook-alerts/
- [B-corr] Pine Screener requirements and limitations: https://in.tradingview.com/support/solutions/43000742437 ; key features: https://ru.tradingview.com/support/solutions/43000742436/
- Script publishing rules: https://www.tradingview.com/support/solutions/43000590599-script-publishing-rules/
- Chart compressed: https://www.tradingview.com/support/solutions/43000762934-my-chart-looks-compressed/
- Plans (alerts): https://www.tradingview.com/pricing/ ; https://in.tradingview.com/scripts/subscriptions ; https://www.techbloat.com/which-tradingview-plan-should-you-choose-a-practical-buying-guide.html
- Pine FAQ alerts: https://www.tradingview.com/pine-script-docs/faq/alerts/

**Evidence**
- [B-new] Gigerenzer, Hertwig, van den Broek, Fasolo, Katsikopoulos (2005). "A 30% chance of rain tomorrow". *Risk Analysis* 25(3):623–629. https://ideas.repec.org/a/wly/riskan/v25y2005i3p623-629.html
- [B-new] Joslyn & LeClerc (2012). Uncertainty forecasts improve weather-related decisions and attenuate the effects of forecast error. *JEP: Applied* 18:126–140. https://www.sci.utah.edu/~kpotter/Library/Papers/joslyn:2012:UFID/index.html
- [B-new] Dietvorst, Simmons & Massey (2015). Algorithm aversion. *JEP: General* 144(1):114–126. https://faculty.wharton.upenn.edu/wp-content/uploads/2016/11/20-Dietvorst-Simmons-Massey-2015.pdf ; Dietvorst, Simmons & Massey (2018) Overcoming algorithm aversion: https://marketing.wharton.upenn.edu/wp-content/uploads/2020/07/Dietvorst-Overcoming-Algorithm-Aversion.pdf
- [B-new] Scheibehenne, Greifeneder & Todd (2010). Can there ever be too many options? *J Consumer Research* 37:409–425. https://ideas.repec.org/a/oup/jconrs/v37y2010i3p409-425.html
- [B-new] McDowell & Jacobs (2017), meta-analysis via Weber, Binder & Krauss (2018) *Front Psychol* 9:1833: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6194348/
- Hoffrage, Krauss, Martignon & Gigerenzer (2015). *Front Psychol* 6:1473. https://pmc.ncbi.nlm.nih.gov/articles/PMC4604268/
- Jerez-Fernandez, Angulo & Oppenheimer (2014). *Psych Sci* 25(2):633–635. https://www.psychologicalscience.org/news/were-only-human/precisely-right-no-doubt-trust-me.html
- Makridakis, Spiliotis & Assimakopoulos (2018) *IJF* 34(4):802–808 https://ideas.repec.org/a/eee/intfor/v34y2018i4p802-808.html ; (2020) *IJF* 36(1):54–74 https://econpapers.repec.org/RePEc:eee:intfor:v:36:y:2020:i:1:p:54-74 ; SAS commentary https://blogs.sas.com/content/forecasting/2020/01/08/m4-forecasting-competition-results-and-commentary
- Geifman & El-Yaniv (2017). arXiv:1705.08500. https://arxiv.org/abs/1705.08500
- [B-corr] Alert override meta-analysis (*Health Informatics J* 2024, PMID 38899788): https://journals.sagepub.com/doi/10.1177/14604582241263242 ; O'Sullivan et al. 2025 preprint: https://preprints.jmir.org/preprint/88578
- WCAG 2.1: https://www.w3.org/TR/WCAG21/ (ratios recomputed by B)
- Options PoT conventions: https://www.schwab.com/learn/story/options-delta-probability-and-other-risk-analytics ; https://optionalpha.com/lessons/probability-of-profit-vs-probability-of-touch
- Sibling studies: `calib_ml.md` (pickers, CAL-3/CAL-5), `skeptic.md` (SKEP-5), `ux_design.md` (UX-1/2/3/5), `pine_eng.md` (PENG-1/2), `ict_pd.final.md` (FVG/OB vs random)

---

## Appendix: corrections log (B vs A)

| # | A said | B found | Effect |
|---|---|---|---|
| 1 | 95 inputs, 75 in the legend, 67 without a tooltip | 104, 76, 76 (54 among legend types) | COMP-1 counts |
| 2 | 6 `request.security` + 1 lower-TF | 5 + 1 = 6; two share `tfH` | COMP-9 feasibility (5-call screener limit) |
| 3 | No competitor compares against a null | Two placebo-controlled stats scripts do (OB, FVG); both find no edge | §1.5, COMP-11 |
| 4 | Measurement-first tools don't commit to a target | MQLSoftware and LunqFX commit to one draw; no null | §1.1 |
| 5 | Natural frequencies 7% → 45% (strong) | Not verified; meta-analysis 4% → 24%; grade moderate for our use | COMP-4 evidence |
| 6 | M4: 17 of 50 beat Comb | Rephrased to the verified statements | Evidence table |
| 7 | Alert override 90% (85.6–95.0), 570,776 prescriptions | 90% (85–95), 16 studies; 79.8% (44 studies); count unverified | COMP-2 evidence |
| 8 | ForexCracked 2,239 boosts | Conflicts with A's notes (115); dropped | Evidence |
| 9 | COMP-3 compares edge; P1 | All rules' edge ≈ 0 (§2.2); compare ATR delivered; P2; merge with SKEP-5 / CAL-3 | COMP-3 |
| 10 | COMP-6 abstention raises precision | No gain in replication; P3; display moved to COMP-4 | COMP-6 |
| 11 | COMP-8 single light variants | Breaks dark label text (3.3:1); adopt UX-2 two roles | COMP-8 |
| 12 | Screener uses default inputs | Only `input.timeframe`/`symbol`/`time` are ignored | COMP-9 |
| 13 | (not found) | Sweep alert fires for never-shown targets; no TF in `alert()` text; "DOL Price" plot leaks filtered targets | COMP-2 Part A |
| 14 | (not covered) | 15-in-3-minutes alert stop; JSON content type; `str.format` thousands separators | COMP-2 |
| 15 | (not covered) | Reference class, uncertainty-decision, algorithm-aversion and choice-overload evidence | COMP-4, COMP-5, §1.13 |
