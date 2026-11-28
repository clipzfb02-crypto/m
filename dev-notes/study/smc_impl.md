# Open-source SMC / liquidity Pine implementations: study for the DOL Engine v2

Scope: how widely used open-source scripts and libraries define and code the things the engine depends on (swings, internal vs swing structure, BOS/CHoCH confirmation, strong/weak extremes, order blocks and their mitigation, equal highs/lows, liquidity pools and sweeps, FVG/iFVG/breakers, killzone pivots, volume-profile nodes, draw-on-liquidity target selection), the evidence behind them, and what the engine should borrow.

Line numbers refer to `brief/baseline_v2.pine` (identical to `indicators/dol_engine.pine`).

Companion studies already cover ICT theory (`ict_liq.md`, `ict_pd.md`, `ict_struct.md`, `ict_time.md`). This report does not repeat their proposals. Where an implementation convention found here is the concrete template for one of their proposals, it says so (section 5).

No third-party code is reproduced here. Algorithms are paraphrased, and all Pine sketches are original.

---

## 0. Executive summary

1. **The engine already implements, and in most places exceeds, the conventions of the popular open-source SMC scripts.** It confirms structure on body closes (the default in LuxAlgo SMC, the `smartmoneyconcepts` Python library and the openalgo ports). It removes pools on a strict trade-through, like LuxAlgo's free DOL tool. It has touch, CE and full-fill mitigation modes like TFlab/TradingFinder. It crops partially filled gaps (LuxAlgo's "dynamic" FVG), inverts FVGs on a close through the whole gap (LuxAlgo IFVG), and keeps session pivots until swept (TFO Killzones & Pivots). It is non-repainting (better than several popular scripts and libraries; the Python library had a lookahead bug fixed in PR #65). There is no "missing basic" to copy.

2. **The open-source detectors themselves have no forecasting edge, measured on very large samples.** A 2026 SSRN study translated two widely used open-source Pine SMC scripts into 44 detectors. Tested on 496 S&P 500 stocks (2.20 M events, 17.6 M simulated trades), **none beat a matched random entry at any horizon** after multiple-testing control (Tangirala, SSRN 7483658). A pre-registered study of a production SMC indicator on 1-minute gold, 2012-2026, found **the timing component is zero**: a 0.01 R/trade effect at 1 h is rejected. Two price feeds gave "almost entirely different signals but the same aggregate returns" (Babayans, SSRN 7608245). Implication for the engine: copy conventions for *robustness and looks*, not for *scoring weight*. Forecast value must come from distance/volatility geometry plus the ledger. The engine is built this way.

3. **The best idea to take from open-source DOL tools is an honest, sample-sized probability.** Of the four open-source "draw on liquidity" tools reviewed, one (MQLSoftware Liquidity Map) shows its draw probability as a *self-calibrating empirical hit rate per bucket*, marked provisional ("~NN% (n …)") while the sample is thin. The engine's PoT is a random-level model (`f_potModel`, 1303-1311). The ledger knows how *selected* targets of each family actually did (`stN/stK`, 1066-1067), but this never reaches the displayed number. It only nudges the score (`f_calMult`, 1376) and the race (`f_raceAdj`, 1367). The time study measured raw PoT errors of up to 2× by hour of day. **Proposal SMC-1** calibrates the displayed PoT on the ledger, out of sample, with the `f_raceAdj` pattern already in the code.

4. **Open-source DOL tools commit to a target; the engine re-ranks every bar.**
   - "Liquidity Draw" locks the target on a bar close until it is reached, its stop breaks, or N bars pass.
   - AGPro's planner reports "balanced" instead of forcing a side.
   - LuxAlgo's free DOL tool uses `tier ÷ ATR distance`, bias side first, with a fallback.

   The engine's hysteresis (2-bar lead, 2× for side flips, wider off-killzone) limits churn but does not give a *plan* the trader can hold for the PoT horizon. **SMC-2** adds an optional commitment mode and a switch-rate metric. The ledger can A/B the two modes on the same chart, because changing the input recomputes history.

5. **One engine feature probably has the wrong sign, per published evidence: "tests".** The engine treats near-misses of a pool as extra resting liquidity (`tests`, 650-658), adding up to +2.1 to the magnitude term (682). The open-source "Liquidity Swings" convention counts these visits too, but as *interest*, not as a break predictor. The only quantitative study found (Chung & Bellotti 2021, about 9,000 level entries on EURUSD, LLOY and BRENT minute data) shows that **more prior bounces raise the probability of another bounce**, with decay over hours. Because the engine counts a pool as hit only when price trades *through* it, a positive weight pushes it toward levels that are less likely to be taken within H. The test also skips exact touches (`gap > 0`, 654), which contradicts the README. **SMC-3** neutralises the weight and decays it.

6. **Drawing management: the open-source pattern beats the engine's for the reference look.** LuxAlgo scripts anchor boxes with `xloc.bar_time` and re-use pre-allocated objects. The engine uses `xloc.bar_index`, which is limited to 10,000 bars back and needs the `time` buffer that `max_bars_back` caps at 5000. It therefore clamps anchors to 4,999 bars back (`f_x`, 404-405). On 1-minute charts a PWH printed early in the week can sit about 5,000-7,000 bars back, so the zone loses the "anchored to its origin candle" look. Pine v6's `time(timeframe.period, bars_back = -N)` returns session-aware *future* timestamps (documented, -1 to -500). Time-anchored zones are therefore fully feasible (**SMC-4**).

7. **Smaller borrowings** (P3):
   - Slow-ATR geometry for tolerances. LuxAlgo uses ATR(200) for EQH, OBs and IFVG; the engine uses ATR(14), which shrinks in quiet sessions.
   - LuxAlgo's high-volatility-candle exclusion for OBs.
   - An iFVG significance filter with "show last N per side" against clutter.
   - LVNs as profile *troughs* (local minima against neighbouring rows, as in LuxAlgo's node detection) instead of an absolute 30%-of-peak cut.

Seven proposals, best first, are in section 4.

---

## 1. Concepts: how open-source implementations define them

Notation: `H/L/O/C` = high/low/open/close; `[k]` = k bars back; ATR(n) as named. "LuxAlgo SMC" means the free *Smart Money Concepts [LuxAlgo]* script, versions 1 (2022) and 2 (the UDT rewrite). "py-smc" means the MIT-licensed `smartmoneyconcepts` Python package (joshyattridge). "PyInd" means the MIT-licensed PyIndicators package, which ports several free LuxAlgo tools.

### 1.1 Swing points

| Implementation | Rule | Defaults | Edge cases |
|---|---|---|---|
| Pine `ta.pivothigh(len, len)` (engine, TFO, openalgo) | `H[len]` is the extreme of a symmetric `2·len+1` window; confirmed `len` bars late | engine `pivLen` 5 (90); MTF `biasLen` 3 (65) | The tie rule is **not documented** in the v6 reference (`reference/ta.md`, 1206-1231). Two equal tops inside one window can suppress one or both pivots. |
| LuxAlgo SMC "leg" | A new bearish leg starts when `H[size] > highest(H, size)` (higher than the *following* `size` bars); a bullish leg when `L[size] < lowest(L, size)`. The swing high is emitted when the leg flips to bearish. | swing 50, internal 5, EQH 3 | Highs and lows **alternate** by construction. Only right-side bars are compared. |
| py-smc `swing_highs_lows` | Symmetric window of `2·len`; consecutive highs are reduced to the higher one (and lows to the lower one) until highs and lows alternate | 50 | The original version used future bars (lookahead). PR #65 removed it. |
| PyInd "pure price action" | Recursive fractal: a 3-point fractal at depth d is promoted to depth d+1 if it is the extreme of three consecutive depth-d swings | depth 1/2/3 = short/intermediate/long | This is ICT's STH/ITH/LTH, mechanised (see ICT-8 in `ict_liq.md`). |
| PyInd breaker / BSL-SSL zigzag | Pivot (left-strength test), pushed to a zigzag. A same-direction pivot replaces the head if it is more extreme | 5-7 | Alternation is enforced. |

**DOL relevance.** Swings are the pools. Alternation matters for *structure*, not for *liquidity*: every unswept high is buy-side liquidity, so the engine correctly does not enforce alternation for pools (1753-1776).

### 1.2 Internal vs swing structure, BOS/CHoCH confirmation

- **LuxAlgo SMC.**
  - Internal structure uses `size` 5 and swing structure uses 50, both on the chart timeframe.
  - A break is the *first* close beyond the pivot: `crossover(close, level)` and the pivot is not yet crossed. Each pivot breaks at most once.
  - The label is CHoCH if the previous trend was the other way, else BOS.
  - Internal breaks are **skipped when the internal level equals the swing level**, so one event is not counted twice.
  - An optional "confluence filter" accepts an internal bullish break only if the upper wick exceeds the lower wick (and the reverse for bearish). As written, the expression has an operator-precedence quirk.
- **py-smc `bos_choch`.**
  - Pattern-based on the last 4 alternating swings.
  - Bullish BOS: L < H, HL above the prior L, HH above the prior H (with `[-4] < [-2] < [-3] < [-1]`).
  - Bullish CHoCH: the newest high breaks the prior high after a lower low (`[-1] > [-3] > [-4] > [-2]`).
  - Confirmation: `close_break=True` (close) by default, else the wick.
  - A BOS/CHoCH that is never broken is discarded. An earlier one whose break comes after a later break is also removed.
- **openalgo "SMC Structures & FVG".** A close beyond the level by default ("with the body option off a wick is enough"). The first break on a chart is always a CHoCH.
- **Reference product.** "requiring true candle-body breaks of established structural nodes" (`tradeaxis_description.md`).
- **Engine.** `f_structure` (708-782) runs per HTF, STF and execution timeframe.
  - Internal bias `ibias` flips on a close through the last pivot (747-754).
  - Swing bias uses the leg's protected extreme: a BOS re-arms `protL/protH`, and a CHoCH needs a close through the protected level (755-774).
  - Chart-timeframe BOS (for order blocks) is `close > obSwingH` (1542-1547), then the level is cleared.
  - This matches the open-source consensus: body close, one break per level.

### 1.3 Strong / weak extremes and premium/discount (LuxAlgo SMC)

- **Trailing extremes.**
  - `top = max(top, H)` since the last swing high; `bottom` likewise.
  - The label is "Strong High" if the swing trend is bearish (the high that started the down-leg is protected), otherwise "Weak High" (the likely target). The mirror applies to lows.
  - The extreme updates *every bar*, before any pivot confirms.
- **Premium/discount zones** from the trailing extremes:
  - premium = [0.95·top + 0.05·bottom, top];
  - equilibrium band = [0.525·bottom + 0.475·top, 0.525·top + 0.475·bottom];
  - discount = [bottom, 0.95·bottom + 0.05·top].
- **DOL relevance.** The weak extreme is the open-source "next target" on the trend side. The engine tracks `legH/legL` and `protH/protL` (713-774) but does not expose the weak extreme as a pool (ICTS-4/5/7 in `ict_struct.md`).

### 1.4 Order blocks

| Implementation | Which candle | Filters | Mitigation / removal |
|---|---|---|---|
| LuxAlgo SMC v1 | On a structure break, scan from the broken pivot to the break bar. Bullish OB = the bar with the **lowest low** (bearish: highest high) among bars whose range is < 2 × ATR(200) (or 2 × cumulative mean range). | Volatility filter | Removed when **close** goes beyond the far edge (v1) |
| LuxAlgo SMC v2 | Same idea. Each bar stores a "parsed" high/low that is **swapped** if the bar is high-volatility (range ≥ 2 × ATR(200) or the cumulative mean TR), so such bars cannot be the extreme. Up to 100 stored. | ATR or cumulative mean range | Input "Close" or "High/Low" (default **High/Low**, i.e. a wick through the far edge) |
| py-smc `ob` | Lowest-low candle between the last swing high and the break candle (latest on ties) | none | Wick (default) or body through the bottom → becomes a **breaker**. A breaker is reset when price trades back above its top. |
| openalgo "Smart Money Radar" | Last opposite-colour candle within 50 bars before the break | max age | Removed (or faded) at **first touch** |
| ICT (sibling study) | Last down-close candle(s) before the displacement that breaks structure | n/a | Mean threshold (50%) |
| **Engine** | Last down-close candle at, or up to 5 bars before, the leg low inside `obLook` = 20 (1669-1680) | quality = 0.4·(FVG in leg) + 0.3·(took a 20-bar low) + 0.3·(leg size / 3 ATR) ≥ 0.40; skipped if MT already revisited (1692-1701) | As a target: touch / CE / full (`delivIn`, 123, 1566-1577) |

### 1.5 Equal highs/lows and liquidity pools

| Implementation | Rule | Tolerance | Pool level |
|---|---|---|---|
| LuxAlgo SMC | A separate short pivot (len 3). Compare each new pivot high with the **previous** EQ-pivot high only | `0.1 × ATR(200)` | Line between the two |
| LuxAlgo "Buyside & Sellside Liquidity" (PyInd port) | Zigzag of pivots (len 7). On a new pivot, scan older same-side swings **from newest to oldest**, stopping at the first swing that lies beyond `ph + band`. Count swings inside ±band. A pool needs **≥ 3** swings. | Band is ATR(10)-scaled. The port computes `10/margin × ATR` with margin 6.9 (≈ 1.45 ATR). Whether the original divides or multiplies is unverified. | Mid of the cluster's min/max, ± band; breach zone ×2.3 |
| py-smc `liquidity` | Group swing highs within `range_percent` (1%) of the **whole dataset's** range (non-causal). Needs > 1 member. | 1% of full range | Average of the group. Swept when a later high reaches level + tolerance. |
| PyInd internal/external zones | Internal pivots (3) inside the external range (10). "equal_hl" mode: consecutive pivots within tolerance | `0.25 × ATR(14)`; zone half-height `0.40 × ATR` | States: active → swept (wick) → broken (close) |
| openalgo Smart Money Radar | Compare each new swing with the **5** before it, within tolerance and lookback | input | Marked swept when traded through by more than the tolerance |
| LuxAlgo "Draw on Liquidity" (free) | Swings merged into an EQ pool; the **whole pool moves to the outermost** merged swing | `0.1 × ATR` | Purged when price trades into it |
| PyInd "Liquidity Pools" | A wick beyond a body-level ≥ 2 times without a close beyond; contacts ≥ 5 bars apart; confirmed after 10 bars away | contact count 2 | Mitigated after **two consecutive closes** through |
| **Engine** | Any new chart pivot within tolerance of an existing same-kind pool merges into it (`f_findLiq`/`f_mergeAt`, 1090-1137). `eqCount` += 1, the level moves to the outermost print, and open ledger records move with it. External pools merge without counting EQ. | `eqTol 0.10 × ATR(14)` (95, 1522) | Strictly *through* = swept (623-624). An exact equal print is not a sweep. |

### 1.6 Liquidity "visits" (LuxAlgo "Liquidity Swings")

- Pivot lookback 14.
- The swing **area** is either "Wick Extremity" (for a high: from `H` down to `max(O, C)` of the pivot bar) or "Full Range".
- Each later bar whose range overlaps the area adds 1 to the **count** and adds its **volume** (optionally from intrabars), until a **close** goes beyond the area's outer edge ("crossed").
- Areas can be filtered by minimum count or volume (ProRealTime port: filter value 2).
- The engine's analogue is `tests`. A bar that comes within `testATR` (0.30 ATR) of the pool without trading through adds 1, at most once every 3 bars (650-658). Exact touches (`gap == 0`) are excluded (654). No volume is counted and there is no decay.

### 1.7 Sweeps

- **PyInd "Liquidity Sweeps"** (a LuxAlgo port):
  - "wick" sweep: `H > level and C < level` for a high, once per level;
  - "outbreak & retest": a close beyond the level, then a later wick back through it with a close on the original side;
  - in wick-only mode a level is retired on a close through it.
- **PyInd "Pure PA sweeps".** A wick through a recursive-fractal pivot without a close beyond it. Levels are retired on a close through them, or after 2,000 bars.
- **Engine.** Any trade-through removes the pool (1564-1589). It then classifies HOLD (close beyond the zone top) or REJECT (close back below the pool price) into `liqEvt` (1580-1582). The mapping is disputed; see ICTS-2 and ICT-2.

### 1.8 Fair value gaps

| Implementation | Detection | Filter | Mitigation |
|---|---|---|---|
| LuxAlgo SMC | `L > H[2]` **and** `C[1] > H[2]` (the middle candle closes above candle 1's high) | "Auto": the middle bar's body % must exceed 2 × the cumulative mean of absolute body % | Deleted when `L < bottom` (full fill by wick) |
| py-smc `fvg` | Centred on the middle candle; its colour must match the direction | none; optional `join_consecutive` merges runs | Mitigated at first **touch** (`L ≤ top`) |
| TradingFinder "FVG Detector" (open source) | Standard 3-candle gap | Very aggressive: candle 3 must extend beyond candle 2's extreme. Aggressive: also candle 2 "not small". Defensive: also candle 2 large and mostly body, candles 2-3 in the gap's direction. Very defensive: also candles 1 and 3 not dojis. | Proximal / 50% / distal level options (per the vendor's SMC suite) |
| openalgo | Standard | none | Greys out the first time price trades in |
| **Engine** | `L > H[2]` and size ≥ `0.15 × ATR(14)` (907-908) | quality = displacement of candle 2 (body vs 1.2 ATR, body ratio) + gap size + a BOS within 3 bars, halved if candle 2's colour is opposite; ≥ 0.45 (1868-1887) | Touch / CE / full fill with partial-fill cropping (1566-1577) |

### 1.9 Inversion FVG (LuxAlgo "Inversion Fair Value Gaps")

- Forms when price **closes through the entire gap** against its original direction.
- Filters gaps by width against an ATR-scaled threshold ("ATR Multiplier").
- Shows the last N bullish/bearish inversion pairs (up to 100).
- Retest **signals**: price returns to the zone and exits through its far side, judged by wicks or closes (selectable).
- A zone is **cleared once it is itself mitigated**.
- Engine (1598-1644):
  - inversion on `close < bottom` / `close > top` (1603);
  - cleaned after more than `ifvgMaxIn` = 2 body closes inside, or a close through the far side (1634-1640);
  - at most 8 kept (198);
  - no width filter beyond the FVG minimum (0.15 ATR(14));
  - no retest event.

### 1.10 Breaker blocks (LuxAlgo "Breaker Blocks with Signals", PyInd port)

- **Zigzag of pivots** (length 5). A bullish breaker needs three swings: an older low **C**, a swing high **D**, and a newer low **E** with `E < C` (the old low is taken). Then a **close above D**, i.e. an MSS.
- **Breaker candle.** Scan from D back to C for the first **up-close** candle. Its high-low (or body, optionally plus the previous same-colour candle) is the bullish breaker. Bearish is the mirror.
- **Lifecycle.**
  - Mitigated by a **close below the bottom**.
  - "Cancelled" by a close between the centre line and the bottom before any entry signal.
  - Entry signal: open between centre and top, close above top.
- This is the concrete template for ICT's breaker (old low violated by the leg *away* from the block, then MSS). The engine's breaker (1646-1661) requires the OB's *own origin* to have swept a 20-bar extreme (`tookL`, 1691). See ICTPD-2; section 5 gives the mapping.

### 1.11 Killzones and session pivots (TFO "ICT Killzones & Pivots", MQ5 port)

- **Default windows** (New York time): Asia 20:00-00:00, London 02:00-05:00, NY AM 09:30-11:00, NY Lunch 12:00-13:00, NY PM 13:30-16:00.
- **Session high/low pivots** extend **until mitigated** (swept) by default. "Extend past mitigation" is optional. Only the most recent of each type is shown by default.
- **Opening-price lines** (off by default): 00:00 ("true day open"), 06:00, 10:00, 14:00.
- **Engine.**
  - Session ranges are Asia 20:00-00:00, London 02:00-05:00 and NY AM **09:30-12:00** (107-109).
  - Killzones are London 02:00-05:00, NY AM **07:00-10:00** and NY PM 13:30-16:00 (223-226).
  - Session pools stay in the registry until swept (1591-1596).
  - No NY Lunch or PM session pools. Window choices are studied in `ict_time.md` (TIME-3).

### 1.12 Volume profile, LVN/HVN

- **LuxAlgo "Volume Profile with Node Detection."**
  - A **peak** is a row whose volume exceeds the N rows on *each side*; a **trough** is the mirror case.
  - N is set as a percentage of the row count, separately for peaks and troughs.
  - A separate threshold (% of the largest row) ignores tiny nodes. Peaks group into clusters.
- **LuxAlgo "Liquidity Levels/Voids (VP)"** (PyInd port).
  - Builds a profile **between consecutive swing points** (detection length 47) with 27 rows.
  - A row below **21%** of the profile's maximum is a *void*.
  - A void is *filled* when price crosses its midpoint.
- **Practitioner consensus** (NinjaTrader, Quantower, LuxAlgo concept page). HVNs slow price; LVNs are traversed quickly and usually sit *between* two HVNs. Quantower adds that an LVN can become accepted.
- **Engine.**
  - Rolling 120 one-hour bars (204). Each hour spreads 60% of its volume over its range and 40% over its body (1384-1414). 48 rows, 1-2-1 smoothing.
  - An LVN is a contiguous run of rows below **0.30 × peak**; runs that touch the profile tails are excluded (2250-2286). Display is off by default.
  - Path cost: the mean profile volume between price and target, relative to the profile mean, sets the multiplier (×1.10 if < 0.6, ×0.85 if > 1.4) (1416-1424, 1945-1947).

### 1.13 Draw-on-liquidity target selection in open-source tools

| Tool | Inventory | Scoring | Choice | Anti-churn |
|---|---|---|---|---|
| LuxAlgo "Draw on Liquidity" (free, 2026) | PWH/L, PDH/L, sessions (Asia 18:00-03:00, London 03:00-09:30, NY 09:30-16:00), EQH/EQL (0.1 ATR), swings (len 10), unfilled gaps (≥ 0.5 ATR); minor pools expire after 500 bars | **tier ÷ ATR distance**, tiers W 4, D 3, session and EQ 2, gap 1.5, swing 1 | Best on the structure-bias side (structure length 50), else the other side | None stated. A merged pool moves to its outermost swing. |
| AGPro "Draw On Liquidity Planner" | Swings, prior-period H/L, equal levels by ATR | Per side 0-100 from pool quality, ATR proximity, trend context and freshness (weighted towards quality and proximity) | Higher-scoring side; **"balanced" when the two sides are close** | Event-label cooldown 52 bars |
| "Liquidity Draw" (HS_16) | HTF (15m) BSL/SSL, untouched FVGs, merged equals | **Volume-weighted liquidity above vs below**; side needs ≥ **55%** | Best target on that side | **Locked on bar close until reached, the stop breaks, or N bars pass** |
| MQLSoftware "Liquidity Map" | ATR-scaled clustering of pivots (right bars 3) into density bands | Score from saturating touch count, age decay, pivot relative volume, rejection-wick depth | Most likely draw | Probability shown as an **empirical hit rate of past draws in the same bucket** (score × distance × alignment), "~NN% (n …)" while provisional |
| **Engine** | Chart, STF and HTF swings, PD/PW, three sessions, FVG/OB/breaker, HTF FVG; registry for far pools | 5 pillars × multipliers (calibrated per family) | Draw side first, counter-draw fallback | 2-bar challenger lead, hysteresis (×2 to flip side, ×2 off killzone) |

### 1.14 Drawing-management and performance conventions

- **Anchoring.** LuxAlgo SMC anchors OB boxes and PDH lines with `xloc.bar_time` (pivot time). The engine uses bar indices with a 5,000-bar `time` buffer and clamps anchors to 4,999 bars back (37, 404-405). Documented limits: `xloc.bar_index` objects reach at most **10,000 bars into the past and 500 into the future** (`visuals/lines_and_boxes.md`, 1252). `max_bars_back(num)` is at most **5000** (`reference/core.md`, 265).
- **Future x with time.** `time(timeframe, session, bars_back)` with `bars_back` from -1 to -500 "calculates the expected timestamp" of the bar N bars ahead (`concepts/time.md`, 735 and 861). This is session-aware on time-based charts and unreliable on non-standard charts (740). `chart.is_standard` identifies those (`reference/chart.md`, 71-75).
- **Object reuse.** LuxAlgo pre-creates "show last N" boxes at `barstate.isfirst` and only `set_*`s their coordinates on `barstate.islast`. The engine deletes and recreates all DOL objects on every last-bar tick (2132-2141): one box, six lines and one label in the Clean style, more with options.
- **"Present" mode.** Older structure labels are deleted when new ones print, to limit clutter.

---

## 2. Evidence (numbers and sources)

| # | Claim | Source | Numbers | Grade |
|---|---|---|---|---|
| E1 | Detectors from popular open-source Pine SMC scripts do not predict returns | Tangirala 2026, *Do Smart Money Concepts Predict Returns?*, SSRN 7483658 | 2 open-source Pine implementations → **44 detectors**; 496 S&P 500 stocks, daily, Jan 2010-Jun 2026; **2.20 M events, 17.6 M trades**, 8 horizons. Against a zero-return null, 38/44 look significant. Against a **matched null** with BH control over 352 tests, **none beats random entry and none is significantly worse**. An earlier version's "28 of 42 beat random" was wrong (27 had lost). | moderate-strong (very large, careful re-analysis; preprint) |
| E2 | A production SMC indicator has zero timing skill intraday | Babayans 2026, SSRN 7608245 (pre-registered) | Spot gold, 1-minute bars, 2012-2026. Each signal is paired with random entries that share its side, stop and target. Timing contribution ≈ 0 under every filter; **+0.01 R/trade at 1 h is rejected**. Returns come from the trend filter and the exit rule. **Two feeds: almost entirely different signals, same aggregate returns.** A symmetric random-entry benchmark is **biased upward by 0.06-0.23 R/trade** for trend-gated strategies. | moderate |
| E3 | FVGs and OBs are revisited about as often as random zones at the same distance | Nordman Algorithms 2026 (via `ict_pd.md` 2.1) | FVG returns 73.0% vs 72.9% (38,114 real vs 380,599 fakes); OB 73.7% vs 73.7% (10,986 touches) | moderate |
| E4 | More prior bounces at a level → higher chance of another bounce, decaying with time | Chung & Bellotti 2021, arXiv 2101.07410 | EURUSD, LLOY, BRENT 1-minute 2018 (372,607 / 127,606 / 307,678 bars). `p(bounce \| b_prev)` rises with `b_prev` and is above a shuffled-returns control (permutation test Λ ≈ 1.0 for b_prev 1-6). EURUSD: the 1-bounce effect decays to 0.5 at about a **350-min** lag window; 4-bounce levels at about **900 min**. Micro-decay logistic slopes are negative (EURUSD b_prev = 4: a = 0.402***, b = −0.00179*, N = 505; b_prev = 1: N = 3,391). | moderate |
| E5 | Equal-high/low labels add < 1 pp beyond distance | `ict_liq.md` E6 (distance-matched, 8 markets, 2 years hourly) | EQ taken within 24 bars 63-82% vs ordinary swings 68-76% at the same distance | moderate |
| E6 | Structure direction ≈ coin flip | `ict_struct.md` 2.2 | First-touch side 49.9 / 51.6 / 50.4% (NQ / gold / EURUSD) | moderate |
| E7 | Raw PoT is miscalibrated by time of day | `ict_time.md` E18 (`pot_error.py`) | A displayed 20% is really 30% at 02:00, 55% at 08:30, 9% at 15:00. A displayed 50% is really 37-75%. | derived from strong premises |
| E8 | Naked (unrevisited) daily POCs are usually revisited | TradingView author post "Naked POCs Explained" (2026) | Gold 84%, ES 87%, BTC 87% revisited within 5 days (n ≈ 962-1,034). By distance: < 0.5 ADR 82%, 0.5-1 ADR 59%, 1-2 ADR 32%. **No random-level baseline; distance-confounded.** | weak |
| E9 | LVNs are traversed fast; HVNs stall price | NinjaTrader, Quantower, Velotrade practitioner guides | No statistics. Quantower shows an LVN later becoming accepted. | weak |
| E10 | Open-source code itself can carry lookahead | py-smc PR #65 | `fvg()` and `swing_highs_lows()` used future bars; fixed ("removed sneaky lookahead in fractal. it had suspiciously good returns") | n/a (code fact) |

**Reading of the evidence for this engine.**
- (a) Conventions from open-source scripts are useful for *definitions, robustness and looks*. None carries forecasting power on its own (E1-E3, E5, E6).
- (b) What does forecast reach is geometry (distance, volatility, time of day) and the engine's own measured outcomes. That is why SMC-1 (outcome calibration) ranks first.
- (c) The one level feature with a published *sign* is touches (E4), and its sign is the opposite of the engine's.
- (d) E2's warning about biased random baselines for trend-gated rules applies to the ledger. `pBase` (1314-1322) is already regime-conditioned (HTF bias split of the empirical surface), which mitigates it. It is not time-conditioned (TIME-2).

---

## 3. Engine gap analysis (line refs to `baseline_v2.pine`)

| # | Concept | Status | Lines | Notes vs the open-source conventions |
|---|---|---|---|---|
| G1 | Swing detection | present | 879-880, 709-710 | Symmetric `ta.pivothigh`. No alternation; correct for liquidity. Tie rule undocumented: two equal tops inside one `2·pivLen+1` window give one pivot, so a tight double top gets no `EQx2` (cosmetic; E5 says EQ adds < 1 pp). |
| G2 | Internal vs swing structure | present (MTF form) | 708-782, 923-931 | The engine computes `bias` (protected-level swing) and `ibias` (internal) per timeframe instead of LuxAlgo's 5/50 on one timeframe. No "internal equals swing" de-duplication is needed because they are separate series. |
| G3 | BOS/CHoCH body-close confirmation | present | 747-774, 1542-1547 | Close through, one break per level. Matches LuxAlgo, py-smc (`close_break=True`), openalgo and the reference product. |
| G4 | Strong/weak extreme | partial | 713-774 (`legH/legL`, `protH/protL`), returned 782, unused | LuxAlgo exposes the weak extreme as the target line. See ICTS-4/5/7. |
| G5 | Premium/discount | partial (display) | 2327-2332, 967-968 | LuxAlgo uses 95/5 bands and a 47.5-52.5% EQ band; the engine shows %. See ICTPD-7. |
| G6 | EQH/EQL detection | present, fast ATR | 95, 1090-1137, 1522 | Merges into any same-kind pool within `0.10 × ATR(14)`, moves to the outermost print (like LuxAlgo DOL), counts `eqCount`. Open-source scripts use **ATR(200)** (LuxAlgo SMC, IFVG) or a cumulative mean range, which is stable across quiet sessions. The engine's ATR(14) tolerance shrinks in Asia (SMC-5). |
| G7 | Cluster / stacked pools | present | 1230-1251, 1912-1927 | Outermost = draw, inner = inducement. Consistent with the BSL/SSL cluster scan, which stops at the first swing beyond the band. |
| G8 | Sweep rule | present | 623-624, 1564-1589, 1595 | Strict trade-through, matching LuxAlgo DOL ("trading into the pool purges it") and PyInd wick mode. Liquidity Swings retires on a *close*; for a "was the liquidity taken" forecast the engine's rule is right. |
| G9 | Sweep classification | partial / disputed | 1580-1582 | Open-source scripts distinguish wick sweeps from outbreak-and-retest; none supplies outcome statistics. See ICTS-2 and ICT-2. |
| G10 | Visits/touches ("tests") | **wrong sign (likely); edge bug** | 650-658, 682 | +0.35 per test (max 6) adds to magnitude, so the engine prefers levels that E4 says are *more likely to bounce* (= not hit under the strict sweep rule). No decay, although E4 shows decay over hours. `gap > 0` (654) excludes exact touches, contrary to README line 66 ("an exact equal high or low adds to the resting liquidity"). SMC-3. |
| G11 | OB candle choice | present (ICT variant) | 1663-1748 | Last down-close at or before the leg low (ICT). LuxAlgo and py-smc take the leg's extreme candle; LuxAlgo also excludes high-volatility bars (range ≥ 2 × ATR(200)). The engine has **no volatility exclusion and no height cap**, so a capitulation candle can become a multi-ATR OB whose near edge sits almost at price. SMC-5. |
| G12 | OB mitigation | present (as a target) | 123, 1566-1577 | Touch / CE / full. Open-source "Close vs High/Low" is about zone *validity*, which the engine handles through `obTrk` breaks (1651). |
| G13 | Breaker | **wrong** | 1646-1661, 1691, 1706, 1734, 1747 | The open-source template (C-D-E zigzag, `E < C`, close > D, first up-close candle D→C) matches ICT; the engine's `tookL` filter does not. See ICTPD-2; mapping in section 5. |
| G14 | FVG detection and filter | present (stricter) | 907-913, 1868-1887 | Quality-gated like TradingFinder "Defensive". LuxAlgo additionally requires `C[1] > H[2]`; the engine instead halves quality when candle 2's colour is opposite (1871). |
| G15 | FVG mitigation modes | present | 123, 306, 1566-1577 | Touch / CE / full plus dynamic crop. Matches the union of LuxAlgo, py-smc and TFlab options. |
| G16 | iFVG inversion and cleanup | present | 1598-1644 | Same core as LuxAlgo IFVG. Missing: a **width filter on slow ATR** and **show-last-N-per-side**. Every FVG ≥ 0.15 × ATR(14) is tracked (1877, 1887), so lower-timeframe charts can fill the 8 slots with tiny inversions (Clean clutter). SMC-6. No retest event (ICTPD-8). |
| G17 | HTF FVG | present | 785-796, 939-942, 1855-1865 | `[1]` + lookahead_on, non-repainting. |
| G18 | Session pivots until mitigated | present | 835-863, 1800-1809, 1591-1596 | Same as TFO. Windows differ (see 1.11 and TIME-3). |
| G19 | PDH/PDL, PWH/PWL | present | 945-961, 1790-1799 | Computed on the chart (exact print bar), better than the common `request.security('D', high)` pattern. |
| G20 | Volume profile and LVN | partial | 978-1015, 1384-1424, 2250-2286 | Rolling 1H composite with an absolute threshold of 0.30 × peak. Open-source node detection uses **local troughs against N neighbouring rows** (LuxAlgo) or swing-anchored profiles (LuxAlgo VP voids, 21% threshold). The absolute cut marks broad thin shoulders, not the LVN between two HVNs. SMC-7. |
| G21 | Liquidity voids (large low-overlap candles) | missing | n/a | LuxAlgo BSL/SSL "voids" (gap wider than ATR(200)). Covered in spirit by ICTPD-10 (merging consecutive FVGs). |
| G22 | DOL selection | present (richer) | 1964-2035 | Missing: a **commitment mode** (Liquidity Draw lock) and an explicit **balanced** state (AGPro); ICTS-3 covers race display. SMC-2. |
| G23 | Displayed probability | partial | 1303-1311, 2066-2068, 2184 | Random-level model with an empirical surface. The ledger's per-family outcomes never reach the displayed PoT. MQLSoftware shows a bucketed empirical hit rate with n. SMC-1. |
| G24 | Drawing anchors | partial | 37, 404-405, 1254, 1613, 2205, 2216-2226 | `xloc.bar_index` with a 4,999-bar clamp. On 1-minute charts, PW/HTF anchors beyond 5,000 bars are clamped, so the zone no longer starts at its origin candle. LuxAlgo uses `xloc.bar_time`. SMC-4. |
| G25 | Drawing churn | partial | 2132-2248 | All DOL drawings are deleted and recreated on every last-bar tick. The LuxAlgo pattern reuses pre-allocated objects. SMC-4. |
| G26 | Non-repainting | present (strong) | 26-29, 922-942, 1518 | Better than several popular open-source scripts (E10; LuxAlgo v1 PDH used `lookahead_on` on unshifted `high`). |
| G27 | Recursive fractal hierarchy | missing | n/a | ICT-8 (`ict_liq.md`). |
| G28 | Naked POC as target | missing | n/a | E8 is distance-confounded with no baseline. Rejected for now (section 4, "considered and rejected"). |

---

## 4. Proposals (best first; maximum 10)

Common principle: each proposal either improves *measured* forecasting (the ledger can show it) or fixes a robustness or visual defect. Nothing here adds unvalidated weight to the score.

### SMC-1 (P1) · Ledger-calibrated PoT: the displayed probability learns from the engine's own past targets

**Why.**
- The number in the Clean label ("PoT: 70.1%") is `f_potModel` (1303-1311), a distance/volatility model for a *random* level, blended with an empirical surface pooled by HTF regime.
- The ledger already knows, per family, how often *selected* targets were actually hit (`stN/stK`, 1066-1067). It uses that only to nudge scores (`f_calMult`, 1376-1382) and race odds (`f_raceAdj`, 1367-1371).
- E7 shows raw PoT is off by up to 2× by hour.
- The open-source precedent (MQLSoftware) shows a per-bucket empirical hit rate with its n, marked provisional while thin.
- Calibrating on outcomes corrects *all* residual biases at once (time of day, level family, selection effect, drift), whatever their cause. It complements TIME-1 (which fixes the main cause) and TIME-2 (which measures).

**Inputs (G_POT, after 187).**
```pine
bool  potCal = input.bool(true, "Calibrate PoT on Ledger", group = G_POT,
  tooltip = "Shifts the displayed PoT by how often this chart's past DOL targets of the same family were actually hit, vs what the model predicted. Out of sample. Needs 10 graded targets.")
float potK   = input.float(20.0, "Calibration Prior (trials)", minval = 1.0, step = 5.0, group = G_POT)
```

**Type `Trial` (375-395).** Add `float pShow = na` (raw model PoT at open) and `float pCal = na` (calibrated PoT at open, computed only from trials booked *before* this one). If TIME-2 lands first, `pShow` is its `pMod`; reuse it.

**State (after 1079).**
```pine
var array<float> stPS = array.new<float>(5, 0.0)   // Σ pShow per [grp 0..3, ALL]
var array<float> brSt = array.new<float>(3, 0.0)   // [n, Σ(y - pShow)², Σ(y - pCal)²]
```

**Helper (STATE HELPERS, after `f_raceAdj`, 1371; it needs `stN/stK/stPS`, `f_logit`, `f_sigm`).**
```pine
f_potCal(float p, int g) =>
    int   gg  = stN.get(g) >= 10 ? g : 4
    float n   = stN.get(gg)
    float out = p
    if potCal and n >= 10 and not na(p)
        float pb = stPS.get(gg) / n
        float dl = f_logit((stK.get(gg) + potK * pb) / (n + potK)) - f_logit(pb)
        out := math.min(0.95, f_sigm(f_logit(p) + dl))
    out
```

**Ordering.**
- `f_openTrial` (1426) must sit after `f_potCal`. It already does if the helper goes at 1372.
- In `f_openTrial`, compute `float pS = f_potModel(d, lv.side, potMu * lv.side)` and set `pShow = pS, pCal = f_potCal(pS, lv.grp())`.

**Booking (`f_book`, 1461).**
- Inside `for g in array.from(t.grp, 4)`: `stPS.set(g, stPS.get(g) + nz(t.pShow, t.pBase))`.
- After the loop: `brSt.set(0, brSt.get(0) + 1)`, `brSt.set(1, brSt.get(1) + math.pow(y - nz(t.pShow, t.pBase), 2))`, `brSt.set(2, brSt.get(2) + math.pow(y - nz(t.pCal, t.pShow), 2))`.

**Use.**
- Line 2067: `activePoT := sweptNow ? 0.95 : f_potCal(f_potModel(...), activeLv.grp())`.
- Line 2184 (secondary targets): the same.
- The `minPoT` filter (2068) and the announcement gate (2071) then use the calibrated value.

**Display.**
- **Clean label** (2225) keeps "PoT: 61.2%". While `stN.get(gg) < 30` show "PoT: ~61%": the tilde marks it as provisional.
- **Tooltip** (`tip`, 2206): add `"\nPoT model " + raw% + " → calibrated on " + n + " past " + f_grpName(gg) + " targets"`.
- **Terminal** PoT row (2353-2356): column 2 shows `"cal n" + str.tostring(n, "#")`.
- **Full view** row: `PoT CAL  Brier raw .231 → cal .214 · n 180`, with green if calibration helps.

**Ledger-measurable.** Yes, directly. The Brier score of `pCal` vs `pShow` on the same trials is prequential: each `pCal` uses only earlier outcomes. No feedback loop, because trials open whenever a DOL is asserted (2038-2045), independent of `minPoT`.

**Value to a trader.** The headline number becomes an honest "how often targets like this were hit within H on this chart", not a model guess.

**Evidence.** Moderate. The method is standard logit-offset calibration with Beta shrinkage, the same as `f_raceAdj`. The need is shown by E7, and the UX has open-source precedent.

**Risk.**
- Per-family n ≈ 50-150 on 5,000 bars, so the offset is noisy early (shrinkage κ = 20 and the ALL fallback handle this).
- Calibration lags when settings change. This is acceptable because history is recomputed on any input change.
- Stays capped at 95%.

**Effort.** S.

### SMC-2 (P2) · Target commitment mode ("Locked until resolved") with a switch-rate metric

**Why.**
- Open-source DOL tools commit: "Liquidity Draw" locks on a bar close until the target is reached, the stop breaks or N bars pass.
- The engine re-ranks every confirmed bar (1964-2035). Hysteresis limits churn, but a trader using the DOL as a plan for the PoT horizon H sees it change. "Targets jump around" is a plausible complaint (CONTEXT.md).
- Locking also makes the displayed target identical to the graded ledger trial, which opens when a DOL is asserted and runs for H bars (2037-2045, 1455).

**Input (G_SCORE, after 148).**
```pine
string commitIn = input.string("Adaptive", "Target Commitment", options = ["Adaptive", "Locked"], group = G_SCORE,
  tooltip = "Adaptive: re-ranked every bar with hysteresis.\nLocked: once committed, the DOL is held until it is reached, ejected, invalidated by a close beyond its invalidation level, or the PoT horizon expires.")
```

**State (after 1050).** `var float lockInv = na`, `var int nSw = 0`, `var int nSwBars = 0`.

**Selection (19, at 2016-2020).** Replace the pick block with:
```pine
bool locked = commitIn == "Locked" and curI >= 0 and bar_index - activeSince < H and not na(lockInv) and
  (curSide == 1 ? close >= lockInv : close <= lockInv)
int pick = -1
if locked
    pick := curI
else if curOk and not (leads and challN >= 2)
    pick := curI
else if bI >= 0 and bS >= minScore
    pick := bI
```
- With `pick == curI`, the "INVALIDATED" ghost (2021) does not fire while locked.
- On release by an invalidation close, the existing ghost path applies, because `curElig` decides it. Optionally add a reason `"⌛ EXPIRED"` when `bar_index - activeSince >= H`.

**On commit** (the `pickId != activeId` block, 2030-2035):
- `if pickId >= 0` → `[lkInv, lkRR, lkP] = f_invalidation(activeLv)`, `lockInv := lkInv`.
- `if activeId >= 0 and pickId >= 0 and inCalc` → `nSw += 1`.
- Every `inCalc` bar: `nSwBars += 1`.
- **Re-arm.** If `commitIn == "Locked"`, `pick == curI` and `bar_index - activeSince >= H`, set `activeSince := bar_index` and recompute `lockInv`. A target still best after expiry is re-committed. The ledger opens a new trial for it, because the old one booked at H (1455).

**Display.**
- Terminal Full view: `SWITCH 2.4 /100b`.
- Clean tooltip: `"locked · 12/30 bars"`.

**Ledger-measurable.** Changing the input recomputes all history, so HIT %, EDGE and SWITCH per 100 bars can be compared between modes on the same chart and the same bars. That is a clean A/B.

**Value.** A stable plan for H bars; fewer "it moved" moments; the displayed target is exactly what is graded.

**Evidence.** Weak: a practitioner convention in open-source DOL tools. Its value is measured, not assumed.

**Risk.**
- A locked target can go stale after a strong opposite move. It is released by the invalidation close, so the stale period is bounded.
- The default stays "Adaptive".

**Effort.** S.

### SMC-3 (P2) · "Tests" with the right sign: count exact touches, decay with recency, neutral default weight

**Why.**
- The engine adds `0.35 × min(tests, 6)` to pool magnitude (682), up to about 7 score points.
- E4 (Chung & Bellotti) shows more prior bounces raise the chance of *another bounce*, with decay over hours (about 350-900 minutes on EURUSD).
- Under the engine's strict sweep rule (a bounce is not a hit), the positive weight favours levels less likely to be taken within H.
- "Liquidity Swings" counts visits as *interest* (count and volume), not as a break predictor.
- Bug: `gap > 0` (654) skips exact touches, which the README says add to resting liquidity.

**Inputs (G_LIQ, after 99).**
```pine
float wTest = input.float(0.0, "Tests → Pool Magnitude", minval = -0.35, maxval = 0.35, step = 0.05, group = G_LIQ,
  tooltip = "Weight of recent near-misses in the density pillar. Evidence: levels with more recent bounces tend to bounce again short-term. Default neutral; the accuracy ledger (per family) measures the effect.")
float tauT  = input.float(60.0, "Test Memory (bars)", minval = 5.0, step = 5.0, group = G_LIQ)
```

**Type `Level` (317-348).** Add `float testW = 0.0`.

**`track` (650-658).**
```pine
if this.isLiquidity() and bar_index - this.lastTest >= 3
    float gap = this.side == 1 ? this.price - hi : lo - this.price
    if gap >= 0 and gap <= testATR * atrV          // exact touch counts (strict-through sweep rule)
        this.testW  := this.testW * math.exp(-(bar_index - this.lastTest) / tauT) + 1.0
        this.tests  += 1
        this.lastTest := bar_index
```
`lastTest` starts at 0, which gives the first visit an exp(-large) ≈ 0 carry. That is correct.

**`evaluate` (682).**
- Replace `0.35 * math.min(this.tests, 6)` with `wTest * math.min(this.testW * math.exp(-(bar_index - this.lastTest) / tauT), 6.0)`.
- Wrap the sum as `math.max(0.0, x)`.
- Keep the `T3` tag (`tests`) for display.

**If ICT-1 (candidate ledger) is implemented,** register `testsEff` as one of its features. The learned bounded lift then replaces `wTest`.

**Ledger-measurable.** Toggle `wTest` (−0.2 / 0 / +0.35) and compare the CHART LIQ and EXT LIQ family EDGE in the Full view (2410-2418). ICT-1 would measure it continuously.

**Value.** Removes a likely wrong-sign bias toward bounce-prone levels, and fixes the README contradiction.

**Evidence.** Moderate for the sign and decay (E4: three assets, minute data, permutation-tested). The default of 0 is conservative.

**Risk.** On instruments where tests precede breaks (stop accumulation, Osler), the neutral default under-weights them until measured. The input allows a positive weight.

**Effort.** S.

### SMC-4 (P2) · Time-anchored, persistent drawings (`xloc.bar_time` + session-aware future edge)

**Why.**
- The reference look anchors each zone at the candle that formed it. With `xloc.bar_index`, the engine must clamp anchors to 4,999 bars back (`f_x`, 404-405), because of the `time` buffer (37), and `max_bars_back` cannot exceed 5000 (`reference/core.md`, 265). Bar-index objects are capped at 10,000 bars into the past (`lines_and_boxes.md`, 1252).
- On 1-minute charts, a PWH from Monday (about 5,000-7,000 bars back) or an older HTF FVG is drawn from a wrong left edge.
- LuxAlgo anchors with `xloc.bar_time`.
- Pine v6 `time(timeframe.period, bars_back = -N)` returns the expected, session-aware timestamp N bars ahead (-1 to -500; `concepts/time.md`, 735 and 861). So the right edge (`extBars` ≤ 100) can also be time-based, with no weekend or session drift on time-based charts.
- Separately, the engine deletes and recreates every DOL drawing on each last-bar tick (2132-2141). Re-using objects (the LuxAlgo pattern) reduces churn.

**Data.**
- Add `int anchorT` to `Level`, `Ext` and `Zone`. Set it where the anchor is known:
  - chart pivots: `time[bar_index - aBH]`, or return time from `f_anchorScan` as a third tuple element (`time[anchor]`);
  - FVG: `time[1]`;
  - OB: `time[obI]` / `time[obJ]`;
  - HTF FVG: `hfT`;
  - MTF pivots: `htfPvHT` / `stfPvHT`. This is the HTF bar's open time, the same resolution as today's `f_barAtTime`.
  - PD/PW/session: extend `f_rangeTrack` and `f_sessTrack` (807-863) to also track `hiT/loT` (`time` when `hiB/loB` is set) and return them.
- Pass `anchorT` through `f_pushExt` (1211) and `f_newLevel` (1084).

**Rendering.**
- Compute at global scope on every bar: `int rT = time(timeframe.period, bars_back = -extBars)` (used only on the last bar).
- Use `xloc = xloc.bar_time` with `left = activeLv.anchorT` and `right = rT` for the DOL box, glow lines and core line (2216-2223), the tether (`x1 = time`, 2224), the label (`x = rT`, 2225), iFVG boxes (1613; update with `box.set_right(z.bx, rT)` at 2147), ghosts (1254-1256) and LVN boxes (2277, 2284; left = time of `lvB.first()`).
- Every object that must end on the shared right edge uses the same `rT`, so the reference look ("iFVG boxes ending on the same right edge") is preserved.

**Fallback.** `bool useTimeX = chart.is_standard` (simple bool; false on Renko, Kagi, line break, P&F, range and Heikin Ashi). If false, keep the current bar-index path, because future time is unreliable on non-standard charts (`time.md`, 740).

**Persistence.**
- Declare `var box dolBx = box.new(na, na, na, na, xloc = xloc.bar_time)`, `var array<line> dolGlow` (5 lines created once), `var line dolTeth` and `var label dolLbl`.
- On `barstate.islast`, update them with `box.set_lefttop/set_rightbottom`, `line.set_xy1/set_xy2/set_color`, `label.set_xy/set_text/set_textcolor/set_tooltip`.
- When there is no DOL, hide them (set colours to fully transparent).
- Keep the delete/recreate path only for variable-count extras (secondary targets, pool lines).
- Then `max_bars_back(time, 5000)` (37) can be removed if nothing else uses `bar_index` anchors far back. Keep it while the fallback path exists.

**Optional exact HTF anchor.** When an HTF pivot is pushed (1782-1789), scan chart bars from `f_barAtTime(htfPvHT)` forward to the end of that HTF bar for the bar whose `high == px`. This is a bounded loop of at most `f_tfRatio(tfH)` bars, capped at `anchorMax`. Set `anchorT` to that bar's time. The zone then starts at the exact candle, not at the HTF bar open.

**Measurability.** Visual (n/a for the ledger).

**Value.** The signature look stays correct on every timeframe and age, and realtime rendering is smoother (no per-tick object churn).

**Evidence.** n/a (engineering; doc-grounded).

**Risk.**
- Touches all drawing code, so there is regression risk (alignment of label and tether).
- `time(..., bars_back = -N)` on a symbol whose session schedule changes inside the next N bars (holiday) can misplace the right edge by a bar. This is cosmetic.

**Effort.** M.

### SMC-5 (P3) · Slow-ATR pool geometry and an order-block volatility filter (open-source robustness conventions)

**Why.**
- LuxAlgo SMC uses ATR(200) (or a cumulative mean range) for EQH tolerance, OB filtering and IFVG width.
- The engine uses ATR(14) for `eqPx` (1522), `wPx` (1520), the test band (654), `clusATR` (1926) and `fvgMin` (907). These shrink about 2-3× in quiet sessions (Asia), so equal lows printed in Asia stop merging exactly where Asia-range liquidity forms. The engine already uses `atrE = max(ATR14, ATR200)` for ejection (878), which is the right compromise.
- **OB volatility filter.** LuxAlgo stops range ≥ 2 × ATR(200) candles from defining an OB. The engine can pick a capitulation candle as the OB (1677-1680, 1720-1723), creating a multi-ATR zone whose near edge sits almost at price. That inflates proximity and drives a near-instant "touch".

**Inputs.**
```pine
string geomIn = input.string("Max (14/200)", "Pool Geometry ATR", options = ["Fast (14)", "Max (14/200)"], group = G_LIQ)
float  obMaxH = input.float(1.5, "Max OB Height (ATR)", minval = 0.3, step = 0.1, group = G_ARR)
```

**Spec.**
- `float atrG = geomIn == "Fast (14)" ? atr : atrE` (global, after 878).
- Use `atrG` in place of `atr` at 1520 (`wPx`), 1522 (`eqPx`), 1926-1927 (stack window), and pass `atrG` to `lv.track(high, low, atrG)` at 1562. That last change alters `maxAway` scaling too; keep `maxAway` on `atr` by passing both values.
- **OB candidate loop (1677):** `if close[k] < open[k] and (high[k] - low[k]) < 2.0 * nz(atrSlow[k], atr)`. If no candidate is found, fall back to the current rule. Mirror at 1720.
- **Height cap:** if `obT - obB > obMaxH * atr`, use the candle body (`obT := math.max(open[obI], close[obI])`, `obB := math.min(...)`; mirror for bearish). This is the body option of the open-source OB/breaker scripts.

**Ledger-measurable.** Compare the OB/BRK and CHART LIQ family EDGE in the Full view with the setting toggled.

**Value.** Session-stable equal-level detection; realistic OB zones.

**Evidence.** Weak (convention); E3 says OBs are near-random as magnets, so the gain is geometric honesty, not edge.

**Risk.** "Max" never shrinks a tolerance below today's value. In quiet sessions tolerances are wider than now, so slightly more EQ merges and stack memberships. Accepted; measurable by the toggle.

**Effort.** S.

### SMC-6 (P3) · iFVG significance filter and "show last N per side" (Clean clutter control)

**Why.**
- Every FVG ≥ 0.15 × ATR(14) enters `fvgTrk` (1877, 1887), and each inversion draws a box. Up to 8 are kept (198, 1620).
- On 1-3-minute charts this fills the Clean view with tiny zones. The reference look shows a few dark-green iFVG boxes.
- LuxAlgo IFVG filters by width with an ATR multiplier and shows only the last N per side.
- The evidence (E3; `ict_pd.md`: iFVG retests 38% vs 38% random) says iFVGs carry no edge, so this is purely visual.

**Inputs (G_IFVG).**
```pine
float ifvgMinW = input.float(0.25, "Min iFVG Width (slow ATR)", minval = 0.0, step = 0.05, group = G_IFVG)
int   ifvgShow = input.int(2, "Show Last iFVGs per Side", minval = 1, maxval = 10, group = G_IFVG)
```

**Spec.**
- **Creation (1603).** `bool inverted = (...) and (z.top - z.bottom) >= ifvgMinW * atrE`. A narrower inverted FVG is removed from `fvgTrk` without creating an iFVG or firing the alert.
- **Rendering (2145-2149).** Walk `ifvgs` from newest to oldest. Keep the first `ifvgShow` per `dir` visible. Set the others' `bgcolor` and border to transparency 100. They stay tracked and are cleaned normally.

**Measurability.** n/a (visual). The "New iFVG Formed" alert count drops.

**Value.** A cleaner, closer match to the reference look.

**Evidence.** None for edge; convention only.

**Risk.** Some users want all inversions. The input allows up to 10.

**Effort.** S.

### SMC-7 (P3) · LVNs as profile troughs (local minima against neighbouring rows) instead of an absolute 30%-of-peak cut

**Why.**
- The engine marks any contiguous run of rows below 0.30 × peak as an LVN (2260-2269). In a skewed profile that is a broad shoulder, not the thin node between two acceptance areas.
- Open-source node detection (LuxAlgo) defines a trough as a row lower than N rows on *each* side. The practitioner definition is "an LVN usually sits between two HVNs".

**Inputs (G_LVN).**
```pine
float lvnNbr  = input.float(8.0, "Trough Neighbourhood (% rows)", minval = 2.0, maxval = 25.0, step = 1.0, group = G_LVN)
float lvnProm = input.float(0.15, "Min Trough Depth (x Peak)", minval = 0.02, maxval = 0.8, step = 0.01, group = G_LVN)
```

**Spec (replace 2257-2269).**
- `int N = math.max(1, math.round(rows * lvnNbr / 100.0))`.
- For `r = N` to `rows - 1 - N`, let `v = vpSm.get(r)`. Compute `lMax = max(vpSm[r-N .. r-1])` and `rMax = max(vpSm[r+1 .. r+N])` with an inner loop of at most 2N ≈ 8.
- A trough requires `v < min of both neighbourhoods` (strict local minimum) and `math.min(lMax, rMax) - v >= lvnProm * peak` (depth).
- **Zone.** Grow from r while neighbouring rows are `≤ v + 0.35 × (min(lMax, rMax) - v)`.
- Keep the existing tail exclusion and `lvnN` per side.
- The path-cost multiplier (1945-1947) is unchanged. A trough-aware variant (count of HVN shelves crossed) belongs to the structural path-resistance proposal ICT-5.

**Measurability.** n/a (display). If ICT-5 reuses the trough/peak map, the ledger measures its path-cost effect via the `usePathVP` toggle A/B.

**Value.** LVN boxes where traders expect them; fewer false shoulders.

**Evidence.** Weak (E9).

**Risk.** None to selection.

**Effort.** S.

### Considered and rejected

- **Naked POC as a level source.** E8: 84-87% are revisited within 5 days, but there is no random baseline and the effect is strongly distance-dependent (82% → 32% from < 0.5 to 1-2 ADR). Arrays with the same profile proved ≈ random (E3). If ICT-1's candidate ledger lands, a POC source could be added and measured there.
- **Liquidity-mass side imbalance as a D component** (Liquidity Draw's 55% rule). There is no evidence, and D already has ≈ no skill (E6, ICTS-1). It would add noise to the largest pillar.
- **LuxAlgo-style leg pivots, or py-smc alternation, replacing `ta.pivothigh`.** No forecasting gain; it would change pool timing everywhere.
- **Internal-structure confluence filter (wick comparison).** Structure has no measured skill (E6); the filter has a precedence quirk in its source.
- **Swing (HTF) order blocks.** E3: OBs ≈ random zones; more array families dilute selection.
- **iFVG retest alert.** It needs ICTPD-8's honesty statistics first; E3/`ict_pd.md` measure 38% vs 38%.

---

## 5. Notes for implementers

1. **ICTPD-2 (breaker) template from the open-source breaker script** (PyInd port of LuxAlgo "Breaker Blocks with Signals"):
   - Keep a small zigzag (direction, bar, price; about 10 entries) updated at chart pivots (1753-1776 already visit them). A same-direction pivot replaces the head if it is more extreme.
   - **Bullish breaker** on a confirmed bar when, with the newest three swings being low E, high D, low C (newest first):
     - `E < C` (the old low was taken);
     - `close > D`, the first close above D (use a "crossed" flag per D).
   - **Candle.** Scan from D's bar back to C's bar for the first `close > open`. The zone is its high/low (or body). Optionally widen with the previous up-close candle.
   - **Push** a `Level` kind 6 (bull breaker; `f_newLevel` side −1, demand). Mirror for bearish (kind 7).
   - **Lifecycle:** remove on a close below the bottom (mitigated).
   - This replaces the `tookL/tookH` filter (1691, 1706, 1734, 1747) as ICTPD-2 recommends.
2. **SMC-1 and TIME-2 share the `Trial` fields** (`pShow` = `pMod`). Implement TIME-2's Brier block once and let SMC-1 add `pCal` and `f_potCal`.
3. **SMC-3 and ICT-1.** If the candidate ledger is built, feed `testsEff` to it and drop the `wTest` input.
4. **SMC-4 ordering.** `f_rangeTrack` and `f_sessTrack` (807-863) are global-scope series functions; adding `hiT/loT` state there is safe. `time(timeframe.period, bars_back = -extBars)` is a function call. To avoid any local-scope consistency warning, compute it at global scope on every bar (cheap) and use it only on the last bar.
5. **Pine v6 facts quoted.**
   - "Objects positioned using `xloc.bar_index` can contain x-coordinates no further than 500 bars into the future or 10,000 bars into the past." (`visuals/lines_and_boxes.md`, 1252)
   - `max_bars_back` "num (const int) … The largest possible argument is 5000." (`reference/core.md`, 265)
   - `time()` `bars_back`: "If the value is a negative number from -1 to -500, the function calculates the expected timestamp of the `timeframe` bar corresponding to N bars after the current bar on the main timeframe." (`concepts/time.md`, 735)
   - `chart.is_standard`: "Returns `true` if the chart type is not one of the following: Renko, Kagi, Line break, Point & figure, Range, Heikin Ashi." (`reference/chart.md`, 75)
   - `box.new` `xloc`: "If xloc = `xloc.bar_time`, the arguments must be a UNIX time." (`reference/box.md`, 171)

---

## 6. Sources

**Implementations studied** (definitions paraphrased; no code reproduced):
- Smart Money Concepts [LuxAlgo], v1 mirror on GitHub (swings, OB coordinates, EQH, FVG auto threshold, premium/discount): https://github.com/iamc1oud/Tradingview-Scripts/blob/master/smart-money-concept-with-trendlines.pine
- Smart Money Concepts [LuxAlgo] v2 (leg detection, parsed highs/lows, OB storage and mitigation, EQH threshold, FVG, trailing extremes): https://www.scribd.com/document/846054813/ict-code-indicator and the leg definition snippets at https://www.scribd.com/document/912653451/Indicator-Smart-Moving-Concepts-for-TradingView
- LuxAlgo SMC library page: https://www.luxalgo.com/library/indicator/smart-money-concepts-smc/
- `smartmoneyconcepts` Python package (MIT): https://github.com/joshyattridge/smart-money-concepts (`smartmoneyconcepts/smc.py`); lookahead fix PR #65: https://github.com/joshyattridge/smart-money-concepts/issues/65
- PyIndicators (MIT; ports of LuxAlgo BSL/SSL liquidity, liquidity sweeps, pure price action sweeps, breaker blocks, liquidity pools, liquidity levels/voids, internal/external zones): https://github.com/coding-kitties/PyIndicators
- Liquidity Swings [LuxAlgo]: https://www.tradingview.com/script/1S2VOnJP-Liquidity-Swings-LuxAlgo/ ; ProRealTime port with explicit rules: https://www.prorealcode.com/prorealtime-indicators/liquidity-swings/
- Buyside & Sellside Liquidity [LuxAlgo]: https://www.luxalgo.com/library/indicator/buyside-sellside-liquidity/
- Inversion Fair Value Gaps (IFVG) [LuxAlgo]: https://www.luxalgo.com/library/indicator/inversion-fair-value-gaps-ifvg/
- Draw on Liquidity [LuxAlgo] (free): https://www.luxalgo.com/library/indicator/draw-on-liquidity.md
- Volume Profile with Node Detection [LuxAlgo]: https://www.luxalgo.com/library/indicator/volume-profile-with-node-detection.md
- Liquidity Levels/Voids (VP) [LuxAlgo]: https://www.luxalgo.com/library/indicator/liquidity-levels-voids-vp.md
- FVG Detector [TradingFinder] (open source): https://www.tradingview.com/script/7RyvovXb-FVG-Detector-TradingFinder-Fair-Value-Gap-Imbalance-Mitigated/
- ICT Killzones & Pivots [TFO], MQ5 port with defaults: https://makeea.com/indicators/ict-killzones-pivots-tfo-mq5-free-download-for-metatrader-5 ; xJMacD derivative: https://www.tradingview.com/script/F6U0aVqL-ICT-Killzones-Pivots/
- openalgo SMC Structures and FVG: https://openalgo.in/script/library/smc-structures-and-fvg ; Smart Money Radar: https://openalgo.in/script/library/smart-money-radar
- Draw On Liquidity Planner [AGPro Series]: https://www.tradingview.com/script/skYKmBdk-Draw-On-Liquidity-Planner-AGPro-Series/
- Liquidity Draw (HS_16): https://www.tradingview.com/script/nmEliXkz-Liquidity-Draw/
- Liquidity Map & Order Blocks [MQLSoftware]: https://www.tradingview.com/script/qBesPbpE-Liquidity-Map-Order-Blocks-MQLSoftware/
- Breaker Blocks with Signals [LuxAlgo] (via the PyIndicators port, `breaker_blocks.py`): https://github.com/coding-kitties/PyIndicators

**Evidence:**
- Tangirala, K. H. (2026). *Do Smart Money Concepts Predict Returns? Evidence from 44 Formalised Detectors on S&P 500 Daily Bars, 2010-2026.* SSRN 7483658. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7483658
- Babayans, K. (2026). *Is There Timing in Smart Money? A Pre-Registered Decomposition of Structure-Based Intraday Trading Returns.* SSRN 7608245. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7608245
- Chung, K., & Bellotti, A. (2021). *Evidence and Behaviour of Support and Resistance Levels in Financial Time Series.* arXiv 2101.07410. https://arxiv.org/abs/2101.07410
- Mahadzva, S. (2026). *Smart Money or Costly Folklore?* SSRN 7430998. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7430998 (via `ict_struct.md`)
- Nordman Algorithms (2026), FVG and OB controlled studies (via `ict_pd.md` 2.1)
- Naked POC revisit statistics (TradingView author post): https://www.tradingview.com/chart/XAUUSD/G1M0dKF0-Naked-POCs-Explained-Why-Price-Keeps-Coming-Back-to-Them/
- Volume-profile practitioner references: https://ninjatrader.com/futures/blogs/how-to-trade-futures-use-volume-profile-to-reveal-significant-price-level/ ; https://www.quantower.com/blog/how-to-read-volume-profile ; https://www.luxalgo.com/library/concept/high-low-volume-nodes/

**Companion studies:** `study/ict_liq.md` (E6, ICT-1, ICT-2, ICT-5, ICT-8), `study/ict_pd.md` (2.1, ICTPD-2, ICTPD-7, ICTPD-8, ICTPD-10), `study/ict_struct.md` (2.2, ICTS-1 to ICTS-7), `study/ict_time.md` (E18, TIME-1, TIME-2, TIME-3).

**Pine v6 docs:** `docsrc/jabez4jc_pinescriptv6/visuals/lines_and_boxes.md`, `reference/core.md`, `reference/box.md`, `reference/chart.md`, `reference/ta.md`, `concepts/time.md`.
