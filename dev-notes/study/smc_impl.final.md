# Open-source SMC / liquidity implementations: combined study (A + B) for the DOL Engine v2

Scope: how widely used open-source scripts and libraries define and code what the engine depends on: swings, internal vs swing structure, BOS/CHoCH confirmation, strong/weak extremes, order blocks and mitigation, equal highs/lows, liquidity pools and sweeps, FVG/iFVG/breakers, killzone pivots, volume-profile nodes, draw-on-liquidity target selection, drawing management. Also the evidence behind them, and what the engine should borrow.

Line numbers refer to `brief/baseline_v2.pine` (identical to `indicators/dol_engine.pine`; B re-checked every line reference used below).

No third-party code is reproduced. Algorithms are paraphrased and all Pine sketches are original.

**Tags.**

| Tag | Meaning |
|---|---|
| [A✓] | Researcher A's claim, re-checked by B against a primary source (code, paper or docs) |
| [A] | A's claim that B could not re-open (host blocked); kept, with the grade it deserves |
| [CORRECTED] | B changed A's claim, number, grade or line reference |
| [B-NEW] | Added by B |
| [B-test] | Number from B's own replication on local CME futures data (Appendix A) |

**B's access this session.** luxalgo.com, tradingview.com, prorealcode.com, ssrn.com, arxiv.org and gist content were blocked by the network policy, and the Firecrawl web-search credits ran out early. B therefore verified through:
- primary code: the `smartmoneyconcepts` package source, the PyIndicators wheel from PyPI, and two Pine-runtime re-implementations (PyneCore, PineTS) on GitHub;
- the research-paper index (arXiv full text);
- the local Pine v6 docs;
- web-search snippets;
- an SMC Pine mirror on GitHub (read through a fetch tool);
- the sibling studies.

---

## 0. Executive summary

1. **The engine already matches or exceeds the open-source conventions; there is no basic feature to copy** [A✓]. It confirms structure on body closes, as LuxAlgo SMC, `smartmoneyconcepts` (`close_break=True`) and the openalgo ports do. Like LuxAlgo's free DOL tool, it removes pools on a strict trade-through. It also matches the open-source set on:
   - touch / CE / full-fill delivery with partial-fill cropping;
   - iFVG on a close through the whole gap;
   - session pivots kept until swept;
   - non-repainting MTF reads.

   **[CORRECTED]** A wrote that the Python library's lookahead "was fixed in PR #65". PR #65 was merged and then **reverted the same day (PR #73, 3 Mar 2025)**. Today's `swing_highs_lows()` still uses a centred window with future bars (`shift(-L)`), and so does `fvg()` (`shift(-1)`). Any public backtest that uses those flags at the swing bar has look-ahead bias. This is one reason open-source "SMC works" backtests should not be trusted. The engine is clean here.

2. **The detectors carry no forecasting edge, so borrow conventions for robustness and looks, not for score weight** [A]. Two 2026 preprints support this; B could not re-open either (SSRN blocked), and the sibling studies quote them consistently.
   - Tangirala: 44 detectors from two popular open-source Pine scripts, 2.2 M events; none beats a matched random entry.
   - Babayans: a pre-registered test found zero timing skill.

   **[B-NEW]** The open-source world now has a placebo-controlled FVG statistics script: real gaps against size-, direction- and distance-matched fake zones. That is the same design as the engine's random-level baseline, and it confirms that the ledger's EDGE test is the right yardstick.

3. **The best idea from open-source DOL tools is an honest, sample-sized probability (SMC-1, P1).**
   - ForexCracked's *Liquidity Draw Probability Map* shows reach "X% of N" per category and prints "building" while n < 20 (verified by `competitors.md`). A's MQLSoftware example is [A] only.
   - The engine's displayed PoT is a random-level model. The ledger's per-family outcomes never reach it.
   - SMC-1 is the same mechanism as `calib_ml` CAL-6, which already merges SMC-1, QPOT-04 and TIME-2. **[CORRECTED]** It now ships with CAL-6's gate (calibrate only when the prequential Brier score improves).
   - **[CORRECTED]** The Clean label keeps the reference look. The provisional "~" and the n go into the tooltip and the Terminal panel only.

4. **[B-NEW] The iFVG layer floods the chart and the alert stream (SMC-6, now P2 with measured numbers).** B replicated the engine's FVG tracker and inversion rule on ES/NQ/GC 5m and 1H and 6E 1m [B-test].
   - The engine forms **130-158 iFVGs per 1,000 bars** on 5m/1H, and **268 per 1,000 bars on 6E 1m**. "New iFVG Formed" therefore fires about every 4-8 bars.
   - Tracking only gaps whose middle candle passes the engine's own displacement test (`dispUp[1]` / `dispDn[1]`) cuts this 4-5×, to **29-37 per 1,000 bars** (60 on 6E 1m). The other filters: width ≥ 0.25 × slow ATR, middle candle closing beyond candle 1 (the LuxAlgo/PyIndicators rule), one merged zone per side per bar, and a 150-bar watch window.
   - LuxAlgo's current IFVG uses a displacement "Min Candle Size" filter in the same spirit.
   - Visual clutter is controlled separately, by "show last N per side". The cap of 8 and the body-close cleanup keep about 5 boxes alive under either source rule.

5. **[B-NEW] Pine's `ta.pivothigh` tie rule is now known: the newest equal bar wins.** Two independent Pine-runtime re-implementations agree (PineTS changelog, rule established on TradingView test series; PyneCore "keep the NEWEST of equal extremes").
   - A bar on the *left* equal to the candidate does not disqualify it. An equal bar on the *right* does, so the later equal top becomes the pivot.
   - Consequences:
     - (a) A tight double top **never loses its pivot**. **[CORRECTED]** The premise of A's G1 ("one or both pivots suppressed") and of sibling ICTS-9 ("a double top yields no pivot") is wrong.
     - (b) The pool is anchored at the *later* top and gets **no EQ count**. That happens for 12% of pivots on ES 5m and **41% on 6E 1m** (0.6-5.5% on 1H) [B-test].
   - SMC-8 keeps the native pivot, adds the tie count and anchors the zone at the first top.

6. **Targets that jump around: commitment mode (SMC-2, P2).** "Liquidity Draw" (HS_16, verified by `competitors.md`) locks the target until it is reached, its stop breaks, or N bars pass. SMC-2 offers that as an option and adds a switch-rate metric. Changing the input recomputes history, so the ledger can A/B the two modes.

7. **[CORRECTED] "Tests" is not a bug, and its sign problem is already owned by ICT-10.**
   - A called `gap > 0` (654) a bug that drops exact touches. It is not. An exact touch that later prints as a pivot is folded into the pool as an equal high (`f_mergeAt` → `eqCount += 1`), so excluding it from `tests` avoids double counting.
   - The evidence on prior bounces is now stronger: Garzarelli et al. 2014 (*Scientific Reports*, peer-reviewed) and Chung & Bellotti 2021 both find that prior bounces predict another bounce. But the effect sits at the 45-90 s to hours scale. It is insignificant at 180 s in Garzarelli and decays in 6-15 h in Chung & Bellotti.
   - The sibling's own 1H/5m replication found no monotone effect (`ict_liq.final` B3).
   - Hence: a neutral weight (ICT-10) plus a decayed test memory as a ledger feature (SMC-3, P3).

8. **Smaller items (P3).**
   - Exact origin candle for HTF/STF pivots through per-HTF-bar extreme maps, with no history references (SMC-10, B-NEW). Today the zone starts at the HTF bar's *open*, up to 23 one-hour bars early for a daily pivot.
   - Time-anchored persistent drawings (SMC-4 = PENG-8 + PENG-5).
   - A slow-floored ATR for pool geometry (SMC-5) [B-test]: on 5m, ATR(14)/ATR(200) runs from about 0.55 in the quietest hour to about 1.6 in the busiest. **[CORRECTED]** The OB volatility filter is dropped. In the data, tall OBs are not born nearer to price on 5m and are not touched more often at the same distance.
   - LVN troughs (SMC-7, adopted as AMT-5).

Nine proposals, best first, are in section 4.

---

## 1. Concepts: how open-source implementations define them

Notation: `H/L/O/C` = high/low/open/close; `[k]` = k bars back. "LuxAlgo SMC" = *Smart Money Concepts [LuxAlgo]* (v1 2022 and the v2 UDT rewrite). "py-smc" = the MIT `smartmoneyconcepts` package (joshyattridge). "PyInd" = the MIT PyIndicators package (v0.22.0), which ports several free LuxAlgo/UAlgo tools.

### 1.1 Swing points

| Implementation | Rule | Defaults | Edge cases |
|---|---|---|---|
| Pine `ta.pivothigh(len, len)` (engine, TFO, openalgo) | `H[len]` is the extreme of a `2·len+1` window, confirmed `len` bars late | engine `pivLen` 5 (90); MTF `biasLen` 3 (65) | **[B-NEW] Ties: the newest equal bar wins** (see 1.15). A left-side equal does not disqualify; a right-side equal does. A tight double top gives exactly one pivot, at the later top. The v6 reference does not document this (`reference/ta.md`) [A✓ on the docs gap]. |
| LuxAlgo SMC "leg" [A✓] | A bearish leg starts when `H[size] > highest(H, size)`, i.e. higher than the **following** `size` bars. There is **no left-side test**. The swing high is emitted when the leg flips. | swing 50 (min 10), internal 5 (fixed), EQH pivots 3 | Highs and lows alternate by construction. |
| py-smc `swing_highs_lows` [A✓, CORRECTED] | `H == rolling max` of a window of `L-1` older bars, the bar itself and `L` newer bars (centred, uses future bars). Ties are non-strict. Consecutive same-type swings are pruned: the higher high survives, and on an exact tie the **earlier** one is kept. | 50 | Look-ahead **still present**: PR #65 was reverted by PR #73 the same day. |
| PyInd BSL/SSL | `pivothigh(len, 1)` semantics (right strength 1) | 7 | Pools register one bar after the swing. |
| PyInd "pure price action" [A] | Recursive fractal: depth d+1 = extreme of three consecutive depth-d swings | depth 1/2/3 = short/intermediate/long | ICT's STH/ITH/LTH, mechanised (ICT-8). |

**DOL relevance.** Swings are the pools. Alternation matters for *structure*, not *liquidity*: every unswept high is buy-side liquidity, so the engine correctly does not enforce alternation for pools (1753-1776) [A✓]. The 5-bar confirmation lag hides most raids of 3-candle swings. `ict_struct.final` showed this is geometry (equal to random walks), not lost information. No proposal.

### 1.2 Internal vs swing structure, BOS/CHoCH confirmation

- **LuxAlgo SMC** [A✓ via the GitHub mirror]:
  - internal size 5, swing size 50;
  - a break is the first close crossing the pivot, and each pivot breaks once;
  - CHoCH if against the prior trend, else BOS;
  - internal breaks are skipped when the internal level equals the swing level;
  - the optional internal "confluence filter" compares the upper wick with `min(close, open − low)`, an operator-precedence slip for `min(close, open) − low`.
- **py-smc `bos_choch`** [A✓]:
  - patterns over the last 4 alternating swings;
  - bullish BOS `[-4] < [-2] < [-3] < [-1]`; bullish CHoCH `[-1] > [-3] > [-4] > [-2]`;
  - confirmation by close (`close_break=True`, default) or by the high/low;
  - unbroken patterns are deleted, and so is an earlier one whose break comes after a later break. This is also hindsight logic, not usable live.
- **PyInd `market_structure_break`** [B-NEW]: close beyond the last pivot (length 7) **and** a momentum z-score ≥ 0.5.
- **openalgo** [A]: close by default, wick optional.
- **Reference product**: "requiring true candle-body breaks of established structural nodes".
- **Engine** (`f_structure` 708-782):
  - `ibias` flips on a close through the last pivot (747-754);
  - swing bias re-arms the protected extreme on a BOS, and a CHoCH needs a close through the protected level (755-774);
  - chart BOS for OBs: `close > obSwingH` (1542-1547), then the level is cleared;
  - this matches the consensus [A✓].
- **Evidence.**
  - The direction of structure is about a coin flip for which side is taken first (`ict_struct` 2.2).
  - Body vs wick confirmation has no published comparison (B searched; none found). The choice is convention.

### 1.3 Strong / weak extremes and premium/discount (LuxAlgo SMC) [A✓]

- **Trailing extremes.** `top = max(top, H)` since the last swing high, updated every bar. It is "Strong High" if the swing trend is bearish, else "Weak High"; lows mirror this.
- **Zones** (U = trailing high, D = trailing low):
  - premium `[0.95U + 0.05D, U]`;
  - equilibrium `[0.525D + 0.475U, 0.525U + 0.475D]`;
  - discount `[D, 0.95D + 0.05U]`.
- **PyInd** port (from RUDYINDICATOR, [B-NEW]): strong/weak by trend at formation, with volume at the extreme.
- **Engine.** Tracks `legH/legL` and `protH/protL` (713-774) but does not expose the weak extreme. That belongs to ICTS-4/5/7.

### 1.4 Order blocks

| Implementation | Which candle | Filters | Mitigation / removal |
|---|---|---|---|
| LuxAlgo SMC [A✓] | On a structure break, scan back from the break bar to the broken pivot. Bullish OB = the **lowest-low** bar; bearish = the highest-high bar. | Bars with range ≥ 2 × ATR(200) (default) or 2 × cumulative mean range are excluded. In v2 their parsed high/low are swapped so they cannot be the extreme. | Mitigated on a tap (highlight); removed on a close beyond (v1). v2 offers Close or High/Low [A]. |
| py-smc `ob` [A✓] | Lowest-low candle between the last swing high and the break candle; **latest on ties** | none (volume "strength" = min/max of 2 volume sums) | Wick (default) or body through the bottom → **every** broken OB becomes a breaker. The breaker is reset when price trades back above its top. |
| LuxAlgo *Order Blocks & Breaker Blocks* [B-NEW, web snippet] | Swing-lookback OBs; "use candle body" option | none | **Every mitigated OB becomes a breaker** (dashed). An optional "historical polarity changes" label is **backpainted**. |
| LuxAlgo *Order Block Detector* [B-NEW, web snippet] | OBs from **volume pivots** (length 5) | n/a | Wick or Close |
| PyInd `order_blocks` [B-NEW] | swing length 10, body option, at most 3 per side | — | breaker columns |
| openalgo Smart Money Radar [A] | Last opposite candle within 50 bars | max age | Removed at first touch |
| ICT (sibling) | Last down-close candle(s) before the displacement that breaks structure | n/a | Mean threshold (50%) |
| **Engine** | Last down-close candle at, or up to 5 bars before, the leg low inside `obLook` 20 (1669-1680) | quality = 0.4·(FVG in leg) + 0.3·(took a 20-bar low) + 0.3·(leg / 3 ATR) ≥ 0.40; skipped if the midpoint was revisited (1692-1701) | As a target: touch / CE / full (`delivIn` 123, 1566-1577) |

**[B-test] OB geometry, which motivates dropping A's OB volatility filter.** Engine OB replica, 6 datasets:
- Height is a median 0.85-1.07 ATR(14). 11-21% of OBs are taller than 1.5 ATR, and 6-13% come from a candle with range ≥ 2 × ATR(200) (LuxAlgo would exclude those).
- On 5m, tall OBs are **not** born closer to price: the median near-edge distance is 2.1 vs 2.1 ATR (ES), 1.7 vs 2.0 (NQ), 2.2 vs 2.2 (GC). On 6E 1m and on 1H they are somewhat closer (2.4 vs 2.7; 1.6 vs 2.2-2.35 ATR).
- Touch-within-30-bars rates at the same near-edge distance show no consistent difference (small n).
- A's "a capitulation candle makes a multi-ATR zone whose near edge sits almost at price" is **not typical**. [CORRECTED]

### 1.5 Equal highs/lows and liquidity pools

| Implementation | Rule | Tolerance | Pool level |
|---|---|---|---|
| LuxAlgo SMC [A✓] | Separate pivots of length 3; compare each new one with the **previous** EQ pivot only | `0.1 × ATR(200)` (range 0-0.5) | Line between the two |
| PyInd `equal_highs_lows` (UAlgo method) [B-NEW] | Pivot length 4; compare with the previous pivot only | `0.10 × ATR(200)` | Both flagged |
| LuxAlgo *Buyside & Sellside Liquidity* (PyInd port) [A✓] | Pivots `(7, 1)`. On a new pivot, scan older same-side swings newest-first, stop at the first one beyond the band, count swings inside it; a pool needs **≥ 3** | Band = `10 / 6.9 × ATR(10)` ≈ 1.45 ATR (the port documents "divisor"); breach zone × 2.3; voids use ATR(200) | Mid of the cluster ± band |
| py-smc `liquidity` [A✓] | Group swing highs within `range_percent` (1%) of the **whole dataset's** range (non-causal); > 1 member | 1% of full range | Average; swept when a later high ≥ level + tolerance |
| PyInd internal/external zones [A] | equal-H/L mode on internal pivots | `0.25 × ATR(14)` | active → swept (wick) → broken (close) |
| openalgo Radar [A] | Compare each new swing with the 5 before it | input | Swept when traded through by more than the tolerance |
| LuxAlgo *Draw on Liquidity* (free) [A✓ via `competitors.md`] | Swings merged into an EQ pool; the pool moves to the outermost swing | `0.1 × ATR` | Purged when price trades into it |
| PyInd *Liquidity Pools* [A✓] | Wick contacts beyond a body level ≥ 2 times, ≥ 5 bars apart, confirmed after 10 bars | contact count 2 | Mitigated after two consecutive closes through |
| **Engine** | A new chart pivot within tolerance of an existing same-kind pool merges into it (`f_findLiq`/`f_mergeAt` 1090-1137): `eqCount += 1`, the level moves to the outermost print, open ledger records move with it. External pools merge without counting EQ. | `eqTol 0.10 × ATR(14)` (95, 1522) | Strict trade-through = swept (623-624) |

**Convention summary [B-NEW].** Three independent open-source EQ detectors use 0.1 × **ATR(200)**: LuxAlgo SMC, UAlgo (via PyInd) and LuxAlgo DOL (ATR length unstated). The engine's 0.1 × **ATR(14)** is the outlier. On 5m CME data the median ATR(14)/ATR(200) by hour ranges from 0.53-0.71 in the quietest hour to 1.34-1.72 in the busiest; on 1H, 0.84-1.12 [B-test]. The engine's tolerance therefore varies about 3× through the day on intraday charts (SMC-5).

### 1.6 Liquidity "visits" (LuxAlgo *Liquidity Swings*) [A✓ via snippets; lookback 14 is A]

- The swing **area** is either "Wick Extremity" (wick to the nearer of open/close) or "Full Range".
- Each later visit adds to a **count** and accumulates **volume** (intrabar precision optional).
- Areas can be filtered by minimum count or volume.
- The visit count is a display of *interest*. No open-source tool publishes it as a break predictor.
- **Engine analogue.** `tests`: a bar within `testATR` (0.30 ATR) without trading through, at most once per 3 bars (650-658). +0.35 per test (max 6) is added to magnitude (682), with no decay.
- **[CORRECTED] Exact touches are not lost.** `gap > 0` (654) excludes them from `tests`. But a bar that prints *exactly* the pool price and is then confirmed as a pivot merges into the pool with `eqCount += 1`:
  - `f_mergeAt` 1112-1115: `samePx` is true but `inBar` is false for a different bar.
  - So the README's "an exact equal high or low adds to the resting liquidity instead" holds, with a `pivLen`-bar delay.
  - Two cases collapse into one pivot with no EQ count: exact touches inside one pivot window (the newest-wins tie rule, 1.15), and a second touch within `pivLen` bars of the pool's own pivot.

### 1.7 Sweeps [A✓]

- **PyInd/LuxAlgo *Liquidity Sweeps*** (swing length 5, mode "wicks" default):
  - wick sweep = wick beyond and close back inside, once per level;
  - outbreak & retest = a close beyond, then a later wick back through with a close on the original side;
  - in wick-only mode a level is retired on a close through it.
- **PyInd "pure price action" sweeps** [A]: a wick through a recursive-fractal pivot without a close beyond; max age 2,000 bars.
- **Engine.** Any trade-through removes the pool (1564-1589). HOLD/REJECT go into `liqEvt` (1580-1582); the mapping is disputed and fixed by ICT-9/ICTS-2.

### 1.8 Fair value gaps

| Implementation | Detection | Filter | Mitigation |
|---|---|---|---|
| LuxAlgo SMC [A✓] | `L > H[2]` **and** `C[1] > H[2]` | "Auto": the bar's percent change > 2 × cumulative mean of absolute percent changes | Deleted on a full fill by wick |
| PyInd `fair_value_gap` [B-NEW] | `L > H[2]` **and** `C[1] > H[2]` | optional % threshold | — |
| py-smc `fvg` [A✓] | Gap around the middle candle; its colour must match the direction | none; `join_consecutive` merges runs | First **touch** (`L ≤ top`); detection uses `shift(-1)` (future bar) |
| TradingFinder *FVG Detector* [A] | Standard | Four aggressiveness levels (very aggressive → very defensive) | Proximal / 50% / distal |
| LuxAlgo IFVG, current [B-NEW, snippet] | Standard | **"Min Candle Size (%)"**: the creating candle must be a displacement move | (see 1.9) |
| openalgo [A] | Standard | none | Greyed at first entry |
| **Engine** | `L > H[2]`, size ≥ `0.15 × ATR(14)` (907-908) | Pool entry: quality ≥ 0.45 (displacement, body ratio, size, BOS within 3 bars; halved if candle 2 has the wrong colour) (1868-1887). **The iFVG tracker gets every gap ≥ 0.15 ATR, unfiltered** (1877, 1887). | Touch / CE / full with partial-fill cropping (1566-1577) |

**Fill-rate statistics [B-NEW].** These are weak: no controls, or results not readable.
- A vendor blog reports about 82% of daily FVGs mitigated within 20 candles vs about 60% on 15m, with no control group.
- An open-source TradingView script compares real FVGs with **placebo zones matched in height, direction and distance**. Its headline is real minus placebo. B could read only its design; its numbers were not accessible.
- The design-level lesson matches Nordman's controlled study (E3): raw fill rates are uninformative without a matched null.

### 1.9 Inversion FVG

- **LuxAlgo IFVG** [A✓ partly]:
  - forms when price **closes through the whole gap** against its direction;
  - "Show Last" = the last N bullish/bearish pairs (up to 100);
  - retest signals by wick or close ("Signal Preference");
  - a failed zone (close back through) is removed.
  - The current version filters the creating candle by "Min Candle Size (%)" (displacement). **[CORRECTED]** A's "ATR Multiplier" width filter could not be confirmed; it may be an older version.
- **Engine** (1598-1644):
  - inversion on `close < bottom` / `close > top` (1603);
  - cleaned after more than `ifvgMaxIn` = 2 body closes inside, or a close through the far side (1634-1640);
  - at most 8 kept (198, 1620);
  - watched for `trackAge` = 500 bars (1626);
  - no source filter, no per-side display limit, no retest event.
- **[B-test] Formation rate** (engine replica, iFVGs per 1,000 bars):

  | Data | Engine now | + engine displacement gate on candle 2 | + width ≥ 0.25 × atrE, `C[1]` beyond, same-bar merge, 150-bar watch |
  |---|---|---|---|
  | ES 5m | 133.8 | 44.2 | **29.7** |
  | NQ 5m | 130.2 | 41.9 | **28.6** |
  | GC 5m | 158.4 | 40.3 | **31.9** |
  | 6E 1m | 267.8 | 76.4 | **60.1** |
  | ES 1H | 135.5 | 49.4 | **37.2** |
  | NQ 1H | 136.1 | 46.7 | **35.6** |

  - On 11-50 bars per 1,000, several gaps invert on the same bar, each drawing its own box and counting as its own event.
  - The engine's own *quality* gate (fvgQMin 0.45, without the BOS bonus) only cuts formations by 30%.
  - The average number of live boxes stays at about 5 under every rule, because of the cap and the cleanup. Visual clutter needs "show last N per side".

### 1.10 Breaker blocks: three open-source conventions [A✓ + B-NEW]

1. **Every broken OB becomes a breaker**: py-smc (wick or body through the far edge) and LuxAlgo *Order Blocks & Breaker Blocks* (mitigated OB → breaker).
2. **MSS template** (LuxAlgo *Breaker Blocks with Signals*, PyInd port, swing length 5):
   - zigzag older low C, high D, newer low E with `E < C` (old low taken), then a close above D;
   - the breaker candle is the first up-close candle scanning from D back to C (full range or body);
   - "cancelled" by a close past the centre line before an entry; mitigated by a close through the far side.
3. **Engine**: only OBs whose own origin swept a 20-bar extreme (`tookL`, 1691/1706/1734/1747). This is the strictest, and it reproduces only 11-24% of template breakers (`ict_pd.final` 2.2).

`ict_pd.final` ICTPD-2 adopts convention 1 for BOS-born OBs plus a stop-run path (close to 2). B agrees, and the open-source split supports it. Naming is inconsistent across libraries: PyInd's "mitigation block" is the *first same-direction* candle of the impulse, while ICT's mitigation block is a failure-swing OB. Labels must state the definition.

### 1.11 Killzones and session pivots (TFO *ICT Killzones & Pivots*) [A]

- **Defaults per A** (NY time): Asia 20:00-00:00, London 02:00-05:00, NY AM 09:30-11:00, NY Lunch 12:00-13:00, NY PM 13:30-16:00. Session high/low pivots extend until mitigated, and only the most recent of each type is shown. B confirmed that the times are configurable, the five-window design and the MPL-2.0 licence, but could not read the defaults.
- **Engine.** Sessions are Asia 20:00-00:00, London 02:00-05:00, NY AM 09:30-12:00 (107-109). Killzones are London 02-05, NY AM 07-10, NY PM 13:30-16 (223-226). Pools stay in the registry until swept (1591-1596). Window choices belong to TIME-1/TIME-3 in `ict_time.final`.

### 1.12 Volume profile, LVN/HVN

- **LuxAlgo *Volume Profile with Node Detection*** [A✓ via snippets]:
  - a peak is a row higher than the N rows on each side; a trough is the mirror;
  - N is set as a percentage of rows, separately for peaks and troughs;
  - an optional threshold (% of the largest row) ignores tiny nodes.
- **LuxAlgo *Liquidity Levels/Voids*** (PyInd port) [A]: profile between consecutive swings (length 47, 27 rows); a row < 21% of max is a void, filled at its midpoint.
- **Engine.**
  - Rolling 120 one-hour bars; 60% of each hour's volume over its range, 40% over its body; 48 rows; 1-2-1 smoothing (1384-1414).
  - LVN = a contiguous run below 0.30 × peak, tails excluded (2250-2286).
  - Path cost: 1416-1424, 1945-1947. Its sign is wrong per `amt_profile` AMT-1.

### 1.13 Draw-on-liquidity target selection in open-source tools

| Tool | Inventory | Scoring | Choice | Anti-churn / probability |
|---|---|---|---|---|
| LuxAlgo *Draw on Liquidity* (free) [A✓ via `competitors`] | PWH/L, PDH/L, sessions (Asia 18-03, London 03-09:30, NY 09:30-16), EQ (0.1 ATR), swings (len 10), gaps ≥ 0.5 ATR; minor pools expire after 500 bars | **tier ÷ ATR distance**: W 4, D 3, session/EQ 2, gap 1.5, swing 1 | Structure-bias side first, else the other side | none |
| AGPro *DOL Planner* [A✓ via `competitors`] | Swings, prior-period H/L, equal levels | 0-100 per side from quality, proximity, trend, freshness | Higher side, or **"balanced"** when close | Event cooldown 52 bars |
| *Liquidity Draw* (HS_16) [A✓ via `competitors`] | 15m BSL/SSL, FVGs, merged equals | Volume-weighted side share ≥ **55%** | Best on that side | **Locked on bar close until reached, stop broken or N bars** |
| ForexCracked *Liquidity Draw Probability Map* [B-NEW, via `competitors`] | Pool categories × birth-distance buckets | Reach within 50 bars, rejected / cut / stall | (map, not one target) | **"reach X% of N"; prints only when n ≥ 20, else "building"** |
| MQLSoftware *Liquidity Map* [A, not re-verified] | ATR-clustered pivots | touches, age, relative volume, wick depth | most likely draw | empirical hit rate per bucket, "~NN% (n …)" |
| Zeiierman *SMC Probability (Expo)* [B-NEW, snippet] | CHoCH / SMS / BMS events | +/− score per event outcome | — | % chance that the next break is up vs down, from past event outcomes (method not published) |
| **Engine** | Chart/STF/HTF swings, PD/PW, three sessions, FVG/OB/breaker, HTF FVG; registry for far pools | 5 pillars × multipliers | Draw side first, counter-draw fallback | 2-bar challenger lead, hysteresis (×2 to flip side, ×2 off killzone); ledger with a random-level baseline |

### 1.14 Drawing management and performance conventions

- **Anchoring** [A✓].
  - LuxAlgo anchors OB boxes and PDH lines with `xloc.bar_time`.
  - The engine uses bar indices, a 5,000-bar `time` buffer (37) and a 4,999-bar clamp (404-405).
  - Docs: "Drawings using `xloc.bar_index` can be positioned a maximum of 10,000 bars in the past" (`writing_scripts/limitations.md` 377; `visuals/lines_and_boxes.md` 1252), and `max_bars_back` "The largest possible argument is 5000" (`reference/core.md` 265).
  - **[B-NEW]** The same limitations page says built-in `time`/OHLC buffers "can reference up to 10,000 bars" (373). The engine's explicit `max_bars_back(time, 5000)` is the binding limit, not the platform.
- **Future x with time** [A✓]. `time(timeframe, bars_back = -1 … -500)` "calculates the expected timestamp" N bars ahead (`concepts/time.md` 735, 861; `reference/time.md` 298). It is unreliable on non-standard charts. `chart.is_standard` detects those (`reference/chart.md` 75).
- **Object reuse** [A]. LuxAlgo pre-creates "show last N" objects and only updates them with `set_*`. The engine deletes and recreates all DOL objects each last-bar tick (2132-2141). PENG-5/UX-7 own this.
- **HTF anchors** [B-NEW]. The engine anchors MTF pivots at the chart bar where the HTF bar *opened* (`f_barAtTime(htfPvHT, …)`, 1783-1789, via `tfOpenBar` 1165-1176), not at the candle that printed the extreme. For a D pivot on a 1H chart that is up to 23 bars early. No open-source script reviewed solves this cheaply; SMC-10 does.
- **Backpainting** [B-NEW]. Open-source scripts often backpaint optional labels; LuxAlgo states this for "historical polarity changes". The engine has no backpainted objects: ghosts and iFVGs are created at confirmation time.

### 1.15 [B-NEW] Pine's pivot tie rule, from Pine-runtime re-implementations

- **PineTS changelog.** "TradingView's pivot rule is asymmetric — a bar on the *left* equal to the candidate does not disqualify it (only a strictly higher one does), while an equal bar on the *right* does, so the later equal bar becomes the pivot."
  - It was established "on a hand-built periodic series evaluated on TradingView (left tie, right tie, both, (1,1) and (2,2) windows)". Previously mismatching bars on BINANCE:BTCUSDT 60 then matched.
  - The same entry says `ta.highestbars` returns the **oldest** bar on ties.
- **PyneCore.** `ta.pivothigh` = "highest with `_check_eq`", i.e. "keep the NEWEST of equal extremes (pivot detection)". The pivot is reported only if that newest extreme sits at offset `rightbars`.
- **PineTS na rule.** The pivot scan stops at the first `na` on either side.
- **[B-test] Effect**, pivLen 5 (Pine rule / strictly-both-sides rule / leftmost-wins rule):

  | Data | Pivots (Pine / strict / leftmost) | Pine pivots with an exact older tie in the left window |
  |---|---|---|
  | ES 5m | 1011 / 890 / 1022 | 121 (12.0%) |
  | NQ 5m | 1018 / 994 / 1019 | 24 (2.4%) |
  | GC 5m | 825 / 792 / 827 | 33 (4.0%) |
  | 6E 1m | 2300 / 1366 / 2252 | 934 (40.6%) |
  | ES 1H | 361 / 341 / 365 | 20 (5.5%) |
  | NQ 1H | 363 / 361 / 361 | 2 (0.6%) |

- **Reading.**
  - Pine already finds about as many pivots as a leftmost-wins rule. The "strict" premise behind ICTS-9 would lose 12-41% of pivots on coarse-tick 5m/1m data, but Pine does not use it.
  - What Pine does lose is the **EQ count and the first-print anchor** of tight double tops: 12-41% of pivots on ES 5m / 6E 1m.

### 1.16 [B-NEW] Open-source lookahead pitfalls (a checklist for any external backtest or port)

1. **Centred windows.** Swing and FVG flags placed at the pivot/middle bar but computed with future bars: py-smc today (PR #65 reverted by #73).
2. **Whole-dataset normalisation.** py-smc `liquidity` uses 1% of the full-history range.
3. **Unshifted HTF requests with `lookahead_on`.** A GitHub mirror of LuxAlgo SMC requests `[high, low]` of D/W/M with `lookahead_on` and no `[1]`, which leaks the period's final extremes on history [A✓ for that mirror; version unknown].
4. **Hindsight pruning.** py-smc `bos_choch` deletes patterns that are never broken, or broken out of order.
5. **Backpainted labels.**

The engine avoids all five (G26).

---

## 2. Evidence (numbers and sources)

| # | Claim | Source | Numbers | Grade | Status |
|---|---|---|---|---|---|
| E1 | Detectors from popular open-source Pine SMC scripts do not predict returns | Tangirala 2026, SSRN 7483658 | 44 detectors from 2 open-source Pine scripts; 496 S&P 500 stocks, daily, 2010-2026; 2.20 M events, 17.6 M trades. Against a matched null with BH over 352 tests, none beats random entry. Liquidity-sweep detectors are the largest at 11-12 bp/10 d, p ≥ 0.23. | **moderate** (null; preprint) | [A] [CORRECTED grade from "moderate-strong"]: B could not open SSRN. Numbers are quoted consistently by `ict_liq.final` and `ict_struct.final`, both from A's reading. |
| E2 | A production SMC indicator has zero timing skill intraday | Babayans 2026, SSRN 7608245 (pre-registered) | Spot gold 1m, 2012-2026; random entries sharing side, stop and target; +0.01 R/trade at 1 h rejected; two feeds gave different signals but the same returns; symmetric random benchmarks biased up 0.06-0.23 R/trade for trend-gated rules | **moderate** (single preprint) | [A], not re-verified |
| E3 | FVGs and OBs are revisited about as often as random zones at the same distance | Nordman 2026 (via `ict_pd.final` 2.1) | FVG 73.0% vs 72.9% (38,114 real vs 380,599 fakes); OB 73.7% vs 73.7% (10,986) | moderate | [A] |
| E4 | More prior bounces → higher chance of another bounce, decaying with time | Chung & Bellotti 2021, arXiv 2101.07410 | EURUSD/LLOY/BRENT 1m, 2018 (372,607 / 127,606 / 307,678 bars). Λ (P[original > shuffled]) ≈ 1.0 for b_prev 1-5 on most series. EURUSD 1-bounce levels decay to p = 0.5 at about a 350-min lag window, 4-bounce at about 900 min. Micro-decay logits (600-min window): b_prev 4 a = 0.402***, b = −0.00179* (N 505); b_prev 1-3 intercepts not significant (a 0.005-0.072, N 3,391-1,051). BRENT 1-bounce levels predict *penetration* at long lags. | moderate | [A✓] (full text read via the paper index); [B] nuance added |
| E5 | Equal-high/low labels add < 1 pp beyond distance | `ict_liq.final` E6 | EQ taken in 24 bars 63-82% vs ordinary swings 68-76% at the same distance (8 markets) | moderate | [A] (sibling); `calib_ml` reports +0.29 (t 3.6) on 1H, so it is contested |
| E6 | Structure direction ≈ coin flip | `ict_struct.final` 2.2 | First-touch side 49.9 / 51.6 / 50.4% (NQ / gold / EURUSD) | moderate | [A] |
| E7 | Raw PoT is miscalibrated by time of day | `ict_time.final` E18 | A displayed 20% is really 30% at 02:00, 55% at 08:30, 9% at 15:00 | moderate (derived) | [A] |
| E8 | Naked daily POCs are usually revisited | TradingView author post (2026) | 84-87% within 5 days (n ≈ 962-1,034); by distance 82% / 59% / 32%; no random baseline | weak | [A] |
| E9 | LVNs traversed fast, HVNs stall | NinjaTrader, Quantower guides | no statistics | weak | [A] |
| E10 | Open-source code carries lookahead | py-smc PR #65 / #73 | PR #65 "Remove LookAhead Bias" (fvg, swing_highs_lows) merged 3 Mar 2025, **reverted by #73 the same day**; current master still uses `shift(-L)` / `shift(-1)` | n/a (code fact) | **[CORRECTED]**: A said it was fixed |
| E11 | Prior bounces raise bounce probability (stocks, tick data) | Garzarelli, Cristelli, Pompa, Zaccaria, Pietronero 2014, *Sci. Rep.* 4:4487 (arXiv 1110.5197) | 9 LSE stocks, 2002 tick data; stripe = mean absolute increment at scale τ. p(b \| b_prev) > 0.5 and rising with b_prev, vs shuffled ≈ 0.5. χ² independence rejected at 45/60/90 s (p < 0.0001), **not at 180 s** (p 0.077 / 0.318). Antipersistent fractional random walks (H ≈ 0.44) do not reproduce it. | strong (peer-reviewed) for existence at seconds scale; weak transfer to the engine's 5m-1H scale | [B-NEW] |
| E12 | Pine's `ta.pivothigh` resolves ties to the newest bar | PineTS changelog and `pivotWindow.ts`; PyneCore `lib/ta.py` | Left-equal allowed, right-equal disqualifies; `highestbars` ties → oldest; validated on TradingView test series and BTCUSDT 60 | moderate (two independent re-implementations; not in official docs) | [B-NEW] |
| E13 | Tight equal highs are common, and Pine gives them one pivot and no EQ | [B-test] | Pine pivots with an exact older tie: ES 5m 12.0%, 6E 1m 40.6%, GC 5m 4.0%, NQ 5m 2.4%, ES 1H 5.5%, NQ 1H 0.6% | moderate (descriptive) | [B-NEW] |
| E14 | The engine's iFVG layer fires very often; displacement gating cuts it 4-5× | [B-test] | 130-158 / 1,000 bars (5m, 1H), 268 (6E 1m) → 29-37 (60 on 6E 1m) with the SMC-6 filters | moderate (descriptive) | [B-NEW] |
| E15 | ATR(14) swings about 3× through the session relative to ATR(200) | [B-test] | 5m CME median ATR14/ATR200 by hour: 0.53-0.71 (quietest) to 1.34-1.72 (busiest); 1H 0.84-1.12 | moderate (descriptive) | [B-NEW] |
| E16 | Tall OBs are not systematically born nearer to price | [B-test] | 11-21% of engine OBs > 1.5 ATR; near-edge distance ≈ equal on 5m, 2.4 vs 2.7 on 6E 1m, 1.6 vs 2.2-2.35 ATR on 1H; touch rates at matched distance ≈ equal (small n) | weak (small n) | [B-NEW] |
| E17 | Fill rates without controls mislead; a placebo design is the fix | Vendor blog (fxnx); open-source placebo-control FVG script | 82% (D) vs 60% (15m) mitigated in 20 candles, no control; the placebo script matches height, direction, distance | weak | [B-NEW] |

**Reading of the evidence for this engine.**
- (a) Open-source conventions are useful for *definitions, robustness and looks*. None carries forecasting power on its own (E1-E3, E5, E6).
- (b) What forecasts reach is geometry (distance, volatility, time of day) plus the engine's own measured outcomes. Hence SMC-1 ranks first.
- (c) The only level feature with a published sign is prior bounces (E4, E11). The effect is strongest at very short scales and decays within hours. Neutral at the engine's scale is the defensible default (ICT-10), with a decayed memory left to the ledger (SMC-3).
- (d) E2's warning about biased random baselines for trend-gated rules applies to the ledger. `pBase` (1314-1322) is split by HTF regime, which mitigates it; it is not time-conditioned (TIME-2).
- (e) E12-E16 are implementation facts and descriptive counts. They justify robustness and UX changes, not score weights.

---

## 3. Engine gap analysis (line refs to `baseline_v2.pine`, re-checked by B)

| # | Concept | Status | Lines | Notes vs the open-source conventions |
|---|---|---|---|---|
| G1 | Swing detection | present | 879-880, 709-710 | Native `ta.pivothigh`, no alternation (correct for liquidity). **[CORRECTED]** Ties: the newest equal bar wins (E12), so a tight double top gives **one** pivot at the later top, never zero. The pool gets no `EQx2` and is anchored at the second top. This affects 12-41% of pivots on ES 5m / 6E 1m (E13). → SMC-8 (amends ICTS-9) |
| G2 | Internal vs swing structure | present (MTF form) | 708-782, 923-931 | Separate series per timeframe; no "internal equals swing" de-duplication needed [A✓] |
| G3 | BOS/CHoCH body-close confirmation | present | 747-774, 1542-1547 | Matches LuxAlgo, py-smc, openalgo and the reference product [A✓] |
| G4 | Strong/weak extreme | partial | 713-774, returned 782 | Weak extreme not exposed → ICTS-4/5/7 |
| G5 | Premium/discount | partial (display) | 2327-2332, 967-968 | → ICTPD-7 / ICT-4 |
| G6 | EQH/EQL tolerance | present, fast ATR | 95, 1090-1137, 1522 | Open-source consensus is 0.1 × ATR(200) (3 tools). ATR(14) swings about 3× intraday (E15). → SMC-5 |
| G7 | Cluster / stacked pools | present | 1230-1251, 1912-1927 | Consistent with the BSL/SSL cluster scan; weight neutralised by ICT-10 |
| G8 | Sweep rule | present | 623-624, 1564-1589, 1595 | Strict trade-through, like LuxAlgo DOL and PyInd wick mode [A✓] |
| G9 | Sweep classification | partial / disputed | 1580-1582 | → ICT-9 / ICTS-2 |
| G10 | Visits/touches ("tests") | **unsupported weight; no bug** [CORRECTED] | 650-658, 682 | +0.35 per test is a monotone reward that E4/E11 contradict at short scales and `ict_liq.final` B3 finds null at 1H/5m. No decay. `gap > 0` is **by design**: exact touches reach `eqCount` via the pivot merge path (1112-1115); only touches inside one pivot window are lost (G1). → ICT-10 (weight), SMC-3 (decayed feature) |
| G11 | OB candle choice | present (ICT variant) | 1663-1748 | Last down-close at or before the leg low (ICT). LuxAlgo/py-smc take the leg extreme; LuxAlgo excludes high-volatility bars. **[CORRECTED]** The missing filter is not a measurable problem (E16); dropped from SMC-5 |
| G12 | OB mitigation | present (as a target) | 123, 1566-1577, 1651 | [A✓] |
| G13 | Breaker | **wrong** | 1646-1661, 1691, 1706, 1734, 1747 | The strictest of three open-source conventions (1.10) → ICTPD-2 |
| G14 | FVG detection (targets) | present (stricter) | 907-913, 1868-1887 | Quality-gated; LuxAlgo/PyInd additionally require `C[1]` beyond candle 1's extreme; the engine halves quality on colour instead (1871/1881) |
| G15 | FVG delivery modes | present | 123, 306, 1566-1577 | Union of LuxAlgo, py-smc and TFlab options [A✓] |
| G16 | iFVG source and display | **partial (noisy)** [CORRECTED/extended] | 1603, 1620, 1626, 1877, 1887, 2145-2149 | Every gap ≥ 0.15 ATR(14) is watched for 500 bars → 130-268 inversions per 1,000 bars (E14); same-bar multi-inversions draw duplicate boxes; no per-side display limit. → SMC-6 |
| G17 | HTF FVG | present | 785-796, 939-942, 1855-1865 | `[1]` + lookahead_on; anchored at the middle candle's HTF open bar |
| G18 | Session pivots until mitigated | present | 835-863, 1800-1809, 1591-1596 | Same as TFO; windows → TIME-1/3 |
| G19 | PDH/PDL, PWH/PWL | present | 945-961, 1790-1799 | Exact print bar on the chart, better than the common `request.security` pattern [A✓] |
| G20 | Volume profile and LVN | partial | 978-1015, 1384-1424, 2250-2286 | Absolute 0.30 × peak cut, not troughs → SMC-7 = AMT-5; path-cost sign → AMT-1 |
| G21 | Liquidity voids | missing | n/a | → ICTPD-10 (merge consecutive FVGs) |
| G22 | DOL selection | present (richer) | 1964-2035 | No commitment mode and no switch-rate readout → SMC-2; "balanced" state → COMP-6 |
| G23 | Displayed probability | partial | 1303-1311, 2066-2068, 2184 | The ledger's per-family outcomes never reach the PoT → SMC-1 = CAL-6 |
| G24 | Drawing anchors (far) | partial | 37, 404-405, 1254, 1613, 2205, 2216-2226 | 4,999-bar clamp; matters on 1-3m charts (one week ≈ 6,900-10,080 bars) → SMC-4 = PENG-8 |
| G25 | Drawing churn | partial | 2131-2248 | Delete/recreate each tick → PENG-5 / UX-7 |
| G26 | Non-repainting | present (strong) | 26-29, 922-942, 1518 | Avoids all five pitfalls of 1.16 [A✓ + B] |
| G27 | Recursive fractal hierarchy | missing | n/a | → ICT-8 |
| G28 | Naked POC as target | missing | n/a | Rejected for now (E8) |
| G29 | **[B-NEW] MTF pivot anchor** | partial | 1165-1176, 1783-1789 | Anchored at the HTF bar's open chart bar, not the candle that printed the extreme (up to 23 bars early for D on 1H, 47 for 4H on 5m) → SMC-10 |
| G30 | **[B-NEW] iFVG watch window** | partial | 199, 1626, 1660 | One `trackAge` (500) serves both iFVG watching and OB → breaker watching; iFVG needs a much shorter window → SMC-6 |

---

## 4. Proposals (best first)

Common principle: each proposal either improves *measured* forecasting (the ledger can show it) or fixes a robustness, alert or visual defect. Nothing adds unvalidated weight to the score. Merges with sibling proposals are stated so that ROADMAP does not implement one idea twice.

### SMC-1 (P1, probability, M) · Ledger-calibrated, gated PoT with its sample size [A, CORRECTED: merged with CAL-6, gate added, Clean look preserved]

**Why.**
- The Clean label's PoT is `f_potModel` (1303-1311): a distance/volatility model for a *random* level, blended with an empirical surface by HTF regime.
- The ledger knows how often *selected* targets of each family were hit (`stN/stK`, 1066-1067). That knowledge only nudges scores (`f_calMult` 1376) and race odds (`f_raceAdj` 1367).
- Raw PoT is off by up to 2× by hour (E7).
- Open-source precedent: ForexCracked prints "reach X% of N", and "building" while n < 20.
- `calib_ml` CAL-6 merges this proposal with QPOT-04 and TIME-2, and shows recalibration *hurts* on an already calibrated base (−0.36% log-loss). Hence the gate.

**Inputs (G_POT, after 187).** `bool potCal = input.bool(true, "Calibrate PoT on Ledger", …)`; `float potK = input.float(20.0, "Calibration Prior (trials)", minval = 1.0, step = 5.0, …)`.

**Trial (375-395).** Add `float pShow = na` (raw model PoT at open) and `float pCal = na` (ungated calibrated PoT at open, using only earlier outcomes). If TIME-2 lands first, `pShow` is its `pMod`.

**State (after 1079).** `var array<float> stPS = array.new<float>(5, 0.0)` (Σ pShow per [grp 0..3, ALL]); `var array<float> brSt = array.new<float>(3, 0.0)` ([n, Σ(y − pShow)², Σ(y − pCal)²]).

**Helpers (after `f_raceAdj`, 1371; before `f_openTrial`, 1426).**
```pine
// Ledger offset for a model PoT: shrink the family's hit rate toward its mean prediction.
f_potCalRaw(float p, int g) =>
    int   gg  = stN.get(g) >= 10 ? g : 4
    float n   = stN.get(gg)
    float out = p
    if n >= 10 and not na(p)
        float pb = stPS.get(gg) / n
        float dl = f_logit((stK.get(gg) + potK * pb) / (n + potK)) - f_logit(pb)
        out := math.min(0.95, f_sigm(f_logit(p) + dl))
    out
// Shown value: calibrated only once it has beaten the raw model prequentially.
f_potShow(float p, int g) =>
    bool on = potCal and brSt.get(0) >= 30 and brSt.get(2) < brSt.get(1)
    on ? f_potCalRaw(p, g) : p
```

**Ledger.**
- `f_openTrial`: `float pS = f_potModel(d, lv.side, potMu * lv.side)`; set `pShow = pS, pCal = f_potCalRaw(pS, lv.grp())`.
- `f_book`, inside the group loop: `stPS.set(g, stPS.get(g) + nz(t.pShow, t.pBase))`.
- After the loop, accumulate `brSt` with `y` and `nz(t.pCal, t.pShow)`.

**Use.**
- 2067: `activePoT := sweptNow ? 0.95 : f_potShow(f_potModel(…), activeLv.grp())`.
- 2184: the same for secondary targets.
- The `minPoT` filter and the announcement gate inherit it.
- No feedback loop: trials open whenever a DOL is asserted (2038-2045), independent of `minPoT`.

**Display.**
- **Clean label unchanged**, to keep the reference look.
- Tooltip (`tip`, 2206): `"PoT 61% · model 55% · from 84 past CHART LIQ targets (hit 52, expected 46)"`, or `"· building (n 7)"` while n < 20.
- Terminal PoT row: `cal n84` / `raw` / `building`.
- Full view: `PoT CAL Brier .231 → .214 · n 180 · ON`.

**Evidence.** Moderate. Standard logit-offset calibration with Beta shrinkage (the existing `f_raceAdj` pattern); the need shown by E7; the gate from CAL-6.

**Risk.**
- Few trials per family early on: the ALL fallback, κ = 20 and the 30-trial gate handle it.
- Calibration lags setting changes, but history is recomputed on any input change.

**Effort.** M (S without the gate).

### SMC-6 (P2, visual-ux / alerts, S) · iFVG from displacement gaps only, one zone per side per bar, a short watch window, and "show last N per side" [A, extended with B-test numbers]

**Why.**
- E14: the engine forms 130-158 iFVGs per 1,000 bars on 5m/1H and 268 on 6E 1m. "New iFVG Formed" fires every 4-8 bars. On 11-50 bars per 1,000, several gaps invert at once and each draws a box.
- The reference description says the product "monitors unmitigated Fair Value Gaps" and the reference look shows a few dark-green boxes.
- LuxAlgo's current IFVG filters the creating candle by displacement and shows the last N pairs.
- iFVG retests carry no edge (38% vs 38%, `ict_pd.final`), so filtering costs no forecasting value.

**Inputs (G_IFVG).**
```pine
string ifvgSrc  = input.string("Displacement gaps", "iFVG Source", options = ["Displacement gaps", "All gaps"], group = G_IFVG,
  tooltip = "Displacement gaps: only gaps left by a displacement candle can invert (about 30 per 1,000 bars on 5m futures instead of 130+).")
float  ifvgMinW = input.float(0.25, "Min iFVG Width (slow ATR)", minval = 0.0, step = 0.05, group = G_IFVG)
int    ifvgAge  = input.int(150, "iFVG Watch Window (bars)", minval = 10, maxval = 1000, group = G_IFVG)
int    ifvgShow = input.int(2, "Show Last iFVGs per Side", minval = 1, maxval = 10, group = G_IFVG)
```

**Spec.**
1. **Source (1877, 1887).**
   - Push the bullish zone only if `ifvgSrc == "All gaps" or (dispUp[1] and close[1] > high[2])`.
   - Bearish: `dispDn[1] and close[1] < low[2]`.
   - `dispUp`/`dispDn` are global series (903-904), so `[1]` is valid inside the `if`.
2. **Width (1603).** `bool inverted = (z.dir == 1 ? close < z.bottom : close > z.top) and (z.top - z.bottom) >= ifvgMinW * atrE`. A narrower gap that is closed through is removed from `fvgTrk` with no iFVG.
3. **Same-bar merge (step 5).**
   - In the loop, collect inverted zones per new direction into locals (`float mTop`, `mBot`, `int mBorn` per side; union of top/bottom, oldest `bornBar`).
   - After the loop, create **one** `Zone` (and one box) per side.
   - `newIfvgEvent` already fires once per bar.
4. **Watch window (1626).** `else if bar_index - z.bornBar > ifvgAge`. `trackAge` stays for `obTrk` (1660).
5. **Display (2145-2149).**
   - Walk `ifvgs` from newest to oldest with per-side counters. The first `ifvgShow` per side get their normal colours (recomputed with the creation expression at 1607-1613). The rest get `color.new(…, 100)` for background and border.
   - Hidden zones are still cleaned normally and become visible again when newer ones are removed.

**Measured effect (E14).** 29.7 / 28.6 / 31.9 per 1,000 bars on ES/NQ/GC 5m, 37.2 / 35.6 on ES/NQ 1H, 60.1 on 6E 1m. At most `2 × ifvgShow` boxes are visible.

**Risk.**
- Users who want every inversion choose "All gaps" (today's behaviour).
- The zone union can be taller than any single gap; that is intended (one structure).

**Evidence.** Moderate (own descriptive replication; convention from LuxAlgo IFVG); none for edge.

### SMC-2 (P2, target-selection, S) · Optional commitment mode ("Locked until resolved") and a switch-rate metric [A, refined]

**Why.**
- HS_16 *Liquidity Draw* locks on a bar close until the target is reached, its stop breaks or N bars pass. AGPro reports "balanced" instead of forcing a side. Both are verified by `competitors.md`.
- The engine re-ranks every confirmed bar with hysteresis, so a trader using the DOL as an H-bar plan can see it move. "Targets jump around" is a plausible complaint (CONTEXT.md).
- Locking also makes the displayed target identical to the graded ledger trial.

**Input (G_SCORE, after 148).** `string commitIn = input.string("Adaptive", "Target Commitment", options = ["Adaptive", "Locked"], …)`.

**State (after 1050).** `var float lockInv = na`, `var int nSw = 0`, `var int nSwBars = 0`.

**Selection (19, 2016-2020).**
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
- While locked, `pick == curI`, so the INVALIDATED ghost (2021-2023) does not fire.
- A lock released by a close through `lockInv` follows the existing ghost path. The ghost reason is `"⊘ INVALIDATED"`, or `"⌛ EXPIRED"` when `bar_index - activeSince >= H`.

**On commit (2030-2035).**
- `if pickId >= 0`: `[lkI, lkRR, lkP] = f_invalidation(activeLv)` and `lockInv := lkI`.
- `if activeId >= 0 and pickId >= 0 and inCalc`: `nSw += 1`.
- Every `inCalc` bar: `nSwBars += 1`.
- **Re-arm.** In "Locked" mode, if the expired target is still `pick`, set `activeSince := bar_index` and recompute `lockInv`. The ledger opens a fresh trial, because the old one booked at H (1455).

**Display.**
- Full view: `SWITCH 2.4 /100b`. Computed in both modes, it is also the diagnostic for "targets jump around".
- Clean tooltip: `locked · 12/30 bars`.

**Ledger-measurable.** Toggling the input recomputes all history, so HIT %, EDGE and SWITCH can be compared on identical bars.

**Evidence.** Weak (practitioner convention). Its value is measured, not assumed.

**Risk.** A stale lock after a sharp opposite move is bounded by the invalidation close and the H expiry. The default stays "Adaptive".

### SMC-8 (P2, robustness, S) · Pine pivot tie semantics: keep `ta.pivothigh`, add the tie count and the first-print anchor (amends ICTS-9) [B-NEW]

**Why.**
- E12: TradingView resolves pivot ties to the newest equal bar, so the premise of ICTS-9 ("a double top inside the window yields no pivot") is wrong. Replacing the native pivot with a hand-coded leftmost-wins helper would only move the pivot to the first top and confirm it k bars earlier, with timing changes everywhere.
- What is really lost:
  - the EQ count of tight double tops (12% of pivots on ES 5m, 41% on 6E 1m; E13);
  - the "anchored at the candle that formed it" look, because the zone starts at the *second* top.
- EQ's forecasting weight is contested (E5 vs `calib_ml`), and ICT-10 sets it neutral by default. The correct EQ bit still matters for the candidate ledger (ICT-1) and for the `EQx2` tag ICT users expect.

**Spec (SERIES, after 880).**
```pine
// Equal prints of the pivot among the p older bars: Pine keeps the newest equal bar as
// the pivot, so these never become pivots of their own. Returns [count, offset of the oldest].
f_pivTies(float pv, bool isHigh, int p) =>
    int ties = 0
    int old  = p
    if not na(pv)
        for k = p + 1 to 2 * p
            float v = isHigh ? high[k] : low[k]
            if math.abs(v - pv) <= syminfo.mintick * 0.5
                ties += 1
                old  := k
    [ties, old]
[phTies, phOld] = f_pivTies(ph, true, pivLen)
[plTies, plOld] = f_pivTies(pl, false, pivLen)
```

**Use (step 9).**
- New-pool path (1761-1763 / 1773-1775): `nh.eqCount := phTies`. If `phTies > 0`, use `anchorBar = bar_index - phOld` and `bornBar = bar_index - phOld` (the pool existed from the first print). Mirror for lows.
- Merge path: leave as is. The merge already counts this print, and earlier ties were never pools.
- `f_structure` (MTF): unchanged. Structure semantics are correct.

**Cost.** At most `pivLen` (≤ 30) history reads per bar, at global scope.

**ICTS-9 note for ROADMAP.** Replace its "why" with E12/E13. Implement this spec instead of its `f_pivHi/f_pivLo`. If earlier confirmation of the first top is wanted, measure it with the ledger first.

**Evidence.** Moderate (E12, E13). **Risk.** None to selection when ICT-10's "Evidence" magnitude model is active. Under "ICT Classic", tight double tops gain density, which is the documented intent of that mode.

### SMC-3 (P3, scoring, S) · Tests: no bug, neutral weight (ICT-10), and a decayed test memory as a ledger feature [A, CORRECTED]

**Why.**
- The sign problem is real but owned by ICT-10 ("Evidence" magnitude model drops `0.35·min(tests, 6)`).
- The literature says the bounce memory is strongest at very short scales and decays:
  - Garzarelli: significant at 45-90 s, not at 180 s;
  - Chung & Bellotti: decays to 0.5 in about 6 h (1 prior bounce) to 15 h (4 prior bounces).
- A raw, never-decaying count is therefore the wrong feature even for the learner.
- **[CORRECTED]** `gap > 0` (654) is correct and stays (exact touches reach EQ via 1112-1115). README line 66 needs only a clause: "…once the touching candle is confirmed as a swing".

**Spec.**
- `Level`: add `float testW = 0.0`.
- In `track` (650-658), keep the gate and add `this.testW := this.testW * math.exp(-(bar_index - this.lastTest) * chartS / 60.0 / tauM) + 1.0` before `lastTest` is updated.
- Input `tauM = input.float(360.0, "Test Memory (minutes)", …)`: clock time, so the decay is timeframe-independent.
- Effective value for scoring or learning: `testsEff = testW * exp(-(bar_index - lastTest) * chartS / 60 / tauM)`.
- With ICT-1/CAL-3, register `testsEff ≥ 1` as feature bit TESTED_RECENT, replacing the raw `tests ≥ 1` bit.
- Under "ICT Classic", replace the raw count in 682 with `math.min(testsEff, 6.0)`.

**Evidence.** Moderate (E4, E11, `ict_liq.final` B3). **Risk.** None under the neutral default.

### SMC-10 (P3, visual-ux, S) · Exact origin candle for HTF/STF pivots via per-HTF-bar extreme maps [B-NEW]

**Why.**
- G29: MTF pivots are anchored at the chart bar where their HTF bar *opened* (`tfOpenBar`, 1165-1176; 1783-1789). The zone starts up to 23 bars early for a daily pivot on 1H, or 47 for a 4H pivot on 5m.
- The user wants zones "anchored left at the candle that formed it".
- Scanning history for the exact candle would need `high[k]` beyond the 500-bar buffer (`indicator(max_bars_back = 500)`). Recording the extreme *as it happens* needs no history at all.

**Spec (SERIES, next to the `tfOpenBar` block).**
```pine
// First chart bar that printed the high / low of each HTF bar, emitted when that bar ends.
f_tfExt(int t) =>
    var int   curT = na
    var float rH   = na
    var int   rHB  = na
    var float rL   = na
    var int   rLB  = na
    int dT = na
    int dH = na
    int dL = na
    if not na(t) and t != curT
        if not na(curT)
            dT := curT
            dH := rHB
            dL := rLB
        curT := t
        rH   := high
        rHB  := bar_index
        rL   := low
        rLB  := bar_index
    else if not na(t)
        if high > rH
            rH  := high
            rHB := bar_index
        if low < rL
            rL  := low
            rLB := bar_index
    [dT, dH, dL]
var map<int, int> hHiB = map.new<int, int>()
var map<int, int> hLoB = map.new<int, int>()
var map<int, int> sHiB = map.new<int, int>()
var map<int, int> sLoB = map.new<int, int>()
bool belowH = timeframe.in_seconds() < timeframe.in_seconds(tfH)
bool belowS = timeframe.in_seconds() < timeframe.in_seconds(tfS)
[hT, hHB, hLB] = f_tfExt(belowH ? time(tfH) : na)
[sT, sHB, sLB] = f_tfExt(belowS ? time(tfS) : na)
if not na(hT)
    hHiB.put(hT, hHB)
    hLoB.put(hT, hLB)
if not na(sT)
    sHiB.put(sT, sHB)
    sLoB.put(sT, sLB)
// cap: drop keys older than the tfOpenQ horizon, as f_recOpen does (or one shared queue of 2000 keys)
```
- **Use (1783-1789).** `int aBar = hHiB.contains(htfPvHT) ? hHiB.get(htfPvHT) : f_barAtTime(htfPvHT, anchorMax)`; likewise `hLoB` for lows and `sHiB`/`sLoB` for STF pivots. Then `f_pushExt(..., aBar, ...)` as now; `f_x` still clamps.
- **Ties.** Strict `>` keeps the *first* print in the HTF bar (origin candle).
- **Data mismatch** (for example, an HTF bar built from a different session than the chart). The map still holds the chart's own extreme bar inside that HTF period, which is the best visual anchor anyway.
- **Realtime.** On the open bar the call runs every tick. `var` state rolls back per tick, so the result is consistent.

**Evidence.** None (engineering; visual fidelity). **Risk.** Low; the fallback is today's path.

### SMC-4 (P3, visual-ux, M) · Time-anchored, persistent drawings [A✓; merged with PENG-8 + PENG-5 / UX-7]

**Why.**
- The 4,999-bar clamp (404-405, 37) moves left edges on 1-3m charts (a week ≈ 6,900-10,080 one-minute bars).
- `xloc.bar_index` cannot go beyond 10,000 bars in any case (limitations.md 377).
- LuxAlgo uses `xloc.bar_time`.
- Every DOL object is recreated each tick (2132-2141).

**Spec.** As PENG-8 (anchors) and PENG-5 (setters). B's additions:
1. `anchorT` sources:
   - chart pivots: `time[bar_index - aBH]` (or `time[phOld]` with SMC-8);
   - FVG: `time[1]`;
   - OB: `time[obI]` / `time[obJ]`;
   - HTF FVG: `hfT`;
   - MTF pivots: `time[bar_index - aBar]` from SMC-10 when the offset ≤ 450, else the HTF open time;
   - PD/PW/session: add `hiT/loT` to `f_rangeTrack`/`f_sessTrack` (807-863).
2. One global `int rT = time(timeframe.period, bars_back = -extBars)`, computed every bar (cheap) and used on the last bar. All right edges (DOL box, glow, label, iFVG, LVN, ghosts) use it, so they align as in the reference look.
3. Use the bar-index path when `not chart.is_standard`.

**Evidence.** None (doc-grounded engineering). **Risk.** Touches all drawing code. Implement after SMC-6/SMC-10 so the anchors are already final.

### SMC-5 (P3, robustness, S) · Slow-floored ATR for pool geometry [A, CORRECTED: OB filter dropped]

**Why.**
- E15: ATR(14) runs from about 0.55× to 1.6× ATR(200) through the 5m session.
- EQ merges, stack windows, test bands and zone depth therefore change meaning by the hour: Asia equal lows stop merging, and tags flicker between sessions.
- Three open-source EQ detectors use 0.1 × ATR(200).
- The engine already uses `atrE = max(ATR14, ATR200)` for ejection (878).

**Spec.**
- `string geomIn = input.string("Slow-floored", "Pool Geometry ATR", options = ["Fast (14)", "Slow-floored"], group = G_LIQ)`; `float atrG = geomIn == "Fast (14)" ? atr : atrE` (after 878).
- Use `atrG` at 1520 (`wPx`), 1522 (`eqPx`) and 1926-1927 (stack window).
- Pass it as a fourth argument to `track` for the test band only; `maxAway` stays on `atr`.

**Dropped from A's version.** The OB volatility filter and height cap (E16: no measurable geometric problem on 5m; OBs ≈ random magnets, E3).

**Ledger-measurable.** Toggle and compare the CHART LIQ and EXT LIQ family EDGE.

**Evidence.** Weak (convention plus descriptive E15). **Risk.** Wider quiet-session tolerances, so a few more EQ merges.

### SMC-7 (P3, level-source, S) · LVNs as profile troughs [A✓; adopted by `amt_profile` AMT-5]

- The definition was verified (LuxAlgo node detection: lower than the N rows on each side, plus a minimum-volume threshold).
- Spec (A, unchanged, replacing 2257-2269):
  - `N = max(1, round(rows · lvnNbr / 100))`, `lvnNbr` 8;
  - a strict local minimum against both N-row neighbourhoods, with depth `min(lMax, rMax) − v ≥ lvnProm · peak` (`lvnProm` 0.15);
  - grow the zone while rows ≤ `v + 0.35 · (min(lMax, rMax) − v)`;
  - keep tail exclusion and `lvnN`.
- AMT-5 adds the barrier feature and the invalidation use. Implement once, there.
- Evidence weak (E9); display only unless AMT-5's feature is adopted.

### Considered and rejected

- **OB volatility filter / height cap** (A's SMC-5 part). Not a measurable problem (E16).
- **Naked POC as a level source.** E8 is distance-confounded with no baseline; it could be measured later as a candidate-ledger source.
- **Liquidity-mass side share as a D component** (HS_16's 55% rule). No evidence, and D already has about zero skill (E6).
- **LuxAlgo leg pivots or py-smc alternation instead of `ta.pivothigh`.** No forecasting gain, and timing would change everywhere.
- **Asymmetric pivots (right strength 1-2, as in the LuxAlgo BSL/SSL port) to register pools sooner.** `ict_struct.final` showed the lag is pure geometry (equal to random walks). Fresher, nearer pools would only add distance-driven "hits".
- **Internal-structure wick confluence filter.** Structure has no measured skill, and the source formula has a precedence slip.
- **Swing (HTF) order blocks; volume-pivot OBs (LuxAlgo OB Detector).** OBs are near-random magnets (E3), and more families dilute selection.
- **iFVG retest alert.** Needs ICTPD-8's statistics first (38% vs 38%).
- **Registry recency cap ("most recent only", TFO).** Covered by ACAD-4 (stale-pool weighting with clock-time decay) in `academic_sr.md`.

---

## 5. Notes for implementers

1. **Merge map** (implement once):

   | This report | Implement as |
   |---|---|
   | SMC-1 | CAL-6 (with SMC-1's display rules) |
   | SMC-3 | ICT-10 for the weight, ICT-1 for the feature |
   | SMC-4 | PENG-8 + PENG-5 / UX-7 |
   | SMC-7 | AMT-5 |
   | SMC-8 | Replaces ICTS-9's helper |
   | ICTPD-2 | Breaker fix (the open-source conventions in 1.10 support it) |

2. **Order.** SMC-6 and SMC-8/SMC-10 (anchor sources) come before SMC-4 (time anchoring). SMC-1 needs the `Trial` fields that TIME-2 also adds.
3. **History buffer.** `indicator(max_bars_back = 500)` (31) limits every series history reference to 500 bars.
   - SMC-8 reads at most `2·pivLen` ≤ 60 bars.
   - SMC-10 needs no history.
   - Never use loops over `high[k]` beyond 450 (the `anchorMax` cap exists for this reason).
4. **Pine v6 facts quoted.**
   - "Drawings using `xloc.bar_index` can be positioned a maximum of 10,000 bars in the past." (`writing_scripts/limitations.md` 377)
   - "Some built-in series like `open`, `high`, `low`, `close`, and `time` have larger historical buffers that can reference up to 10,000 bars." (same page, 373)
   - `max_bars_back`: "The largest possible argument is 5000." (`reference/core.md` 265)
   - `time()` `bars_back`: "If the value is a negative number from -1 to -500, the function calculates the expected timestamp of the `timeframe` bar corresponding to N bars after the current bar on the main timeframe." (`reference/time.md` 298; `concepts/time.md` 735)
   - `chart.is_standard`: "Returns `true` if the chart type is not one of the following: Renko, Kagi, Line break, Point & figure, Range, Heikin Ashi." (`reference/chart.md` 75)
   - `ta.pivothigh`: no tie rule in the reference. The newest-wins rule comes from E12, so a one-line TradingView check is still worth doing before shipping SMC-8: plot `ta.pivothigh(high, 2, 2)` on a series with a planted double top.
5. **Copy policy.** All specs above are original. The open-source scripts were read for definitions only (MIT for py-smc and PyIndicators; MPL-2.0 for TFO; CC BY-NC-SA for LuxAlgo, so no code reuse).

---

## 6. Sources

**Implementations** (definitions paraphrased; no code reproduced):
- `smartmoneyconcepts` (py-smc), `smc.py` (current master, read in full by B): https://github.com/joshyattridge/smart-money-concepts ; PR #65 "Remove LookAhead Bias": https://github.com/joshyattridge/smart-money-concepts/issues/65 ; revert PR #73: https://github.com/joshyattridge/smart-money-concepts/pull/73
- PyIndicators 0.22.0 (wheel from PyPI, read by B): https://pypi.org/project/pyindicators/ ; https://github.com/coding-kitties/PyIndicators. Modules: `buyside_sellside_liquidity`, `equal_highs_lows`, `liquidity_sweeps`, `breaker_blocks`, `mitigation_blocks`, `order_blocks`, `fair_value_gap`, `market_structure`, `strong_weak_high_low`, `liquidity_pools`.
- PineTS (Pine runtime in TypeScript): `src/namespaces/ta/utils/pivotWindow.ts` and `CHANGELOG.md` (tie and na rules): https://github.com/QuantForgeOrg/PineTS
- PyneCore (Pine runtime in Python): `src/pynecore/lib/ta.py` (`pivothigh`, window extreme `_check_eq`): https://github.com/PyneSys/pynecore
- Smart Money Concepts [LuxAlgo], GitHub mirror (read through a fetch tool): https://gist.github.com/deeppanara/93863bafe965047b9ac36cb01e7c397f ; v2 copy [A]: https://www.scribd.com/document/846054813/ict-code-indicator ; listing: https://www.tradingview.com/script/CnB3fSph-Smart-Money-Concepts-LUX/
- Liquidity Swings [LuxAlgo]: https://www.tradingview.com/script/1S2VOnJP-Liquidity-Swings-LuxAlgo/ ; library: https://www.luxalgo.com/library/indicator/liquidity-swings.md
- Inversion Fair Value Gaps [LuxAlgo]: https://www.tradingview.com/script/8FHucjY6-Inversion-Fair-Value-Gaps-IFVG-LuxAlgo ; https://www.luxalgo.com/library/indicator/inversion-fair-value-gaps-ifvg.md
- Order Blocks & Breaker Blocks [LuxAlgo]: https://www.tradingview.com/script/piIbWMpY-Order-Blocks-Breaker-Blocks-LuxAlgo ; Breaker Blocks with Signals: https://in.tradingview.com/script/1owp3WD0-Breaker-Blocks-with-Signals-LuxAlgo ; Order Block Detector: https://tradingview.com/script/KvGhxGxY-Order-Block-Detector-LuxAlgo
- Volume Profile with Node Detection [LuxAlgo]: https://tradingview.com/script/zVCsx5DL-Volume-Profile-with-Node-Detection-LuxAlgo ; Liquidity Levels/Voids [A]: https://www.luxalgo.com/library/indicator/liquidity-levels-voids-vp.md
- Buyside & Sellside Liquidity [LuxAlgo] [A]: https://www.luxalgo.com/library/indicator/buyside-sellside-liquidity/ ; Draw on Liquidity [LuxAlgo] [A✓ via competitors]: https://www.luxalgo.com/library/indicator/draw-on-liquidity.md
- ICT Killzones & Pivots [TFO]: https://www.tradingview.com/script/nW5oGfdO-ICT-Killzones-Pivots-TFO
- FVG Detector [TradingFinder] [A]: https://www.tradingview.com/script/7RyvovXb-FVG-Detector-TradingFinder-Fair-Value-Gap-Imbalance-Mitigated/
- openalgo [A]: https://openalgo.in/script/library/smc-structures-and-fvg ; https://openalgo.in/script/library/smart-money-radar
- DOL tools: AGPro https://www.tradingview.com/script/skYKmBdk-Draw-On-Liquidity-Planner-AGPro-Series/ ; HS_16 https://www.tradingview.com/script/nmEliXkz-Liquidity-Draw/ ; MQLSoftware [A] https://www.tradingview.com/script/qBesPbpE-Liquidity-Map-Order-Blocks-MQLSoftware/ ; ForexCracked (via `competitors.md`) ; Zeiierman SMC Probability (Expo): https://www.tradingview.com/script/mBINsJlf-Smart-Money-Concepts-Probability-Expo
- FVG statistics: placebo-control script https://de.tradingview.com/script/Kbq3WncE-Fair-Value-Gap-FVG-Statistics-with-Placebo-Control/ ; vendor fill-rate blog https://fxnx.com/en/blog/fair-value-gap-fill-rate-measured-across-thousands-gaps

**Evidence:**
- Garzarelli, F., Cristelli, M., Pompa, G., Zaccaria, A., Pietronero, L. (2014). Memory effects in stock price dynamics: evidences of technical trading. *Scientific Reports* 4:4487. doi:10.1038/srep04487 ; arXiv:1110.5197
- Chung, K., Bellotti, A. (2021). Evidence and Behaviour of Support and Resistance Levels in Financial Time Series. arXiv:2101.07410
- Tangirala, K. H. (2026). SSRN 7483658 [A]. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7483658
- Babayans, K. (2026). SSRN 7608245 [A]. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7608245
- Nordman Algorithms (2026), via `ict_pd.final.md` 2.1 [A]
- Naked POC post [A]: https://www.tradingview.com/chart/XAUUSD/G1M0dKF0-Naked-POCs-Explained-Why-Price-Keeps-Coming-Back-to-Them/
- Volume-profile practitioner references [A]: https://ninjatrader.com/futures/blogs/how-to-trade-futures-use-volume-profile-to-reveal-significant-price-level/ ; https://www.quantower.com/blog/how-to-read-volume-profile

**Companion studies:**
- `ict_liq.final.md` (E6, B3, ICT-1, ICT-9, ICT-10);
- `ict_pd.final.md` (2.1, 2.2, ICTPD-2, ICTPD-8, ICTPD-10);
- `ict_struct.final.md` (1.1, 2.2, ICTS-4/5/7/9);
- `ict_time.final.md` (E18, TIME-1/2/3);
- `calib_ml.md` (CAL-3, CAL-6);
- `amt_profile.md` (AMT-1, AMT-5);
- `pine_eng.md` (PENG-5, PENG-8);
- `ux_design.md` (UX-7);
- `competitors.md` (1.x tables, COMP-6);
- `academic_sr.md` (ACAD-4).

**Pine v6 docs:** `docsrc/jabez4jc_pinescriptv6/writing_scripts/limitations.md`, `visuals/lines_and_boxes.md`, `reference/core.md`, `reference/time.md`, `reference/chart.md`, `reference/ta.md`, `concepts/time.md`.

---

## Appendix A. B's replication (reproducible)

- **Code** (original; numpy only): `study/smc_b_tools/smc_b_tests.py`.
  - (A) pivot tie rules;
  - (D) ATR(14)/ATR(200) by hour;
  - (B) iFVG formation-rate replica of engine steps 5/6/13;
  - (C) OB replica of step 8 (BOS from pivLen-5 Pine-rule pivots, OB candle, quality ≥ 0.40, midpoint-revisit skip; height, ≥ 2 × ATR(200) range, near-edge distance, touch within 30 bars).
- **Variants:** `smc_b_ifvg_variants.py` (width/age/simple displacement), `smc_b_ifvg_qgate.py` (engine quality gate without the BOS bonus), `smc_b_ifvg_disp.py` (the engine's own `dispUp/dispDn` definition on candle 2).
- **Run:** `python3 -I <script> <csv> <label>`.
- **Outputs:** `out_tests.txt`, `out_ifvg_variants.txt`, `out_ifvg_qgate.txt`, `out_ifvg_disp.txt`.
- **Data.** CME futures from the sibling download (`study/smt_data/cme`): ES/NQ/GC 5m (Jan-Apr 2026), 6E 1m (Mar-Apr 2026), ES/NQ 1H (Mar 2025-Apr 2026). Wilder ATR.
- **Pivot rule used everywhere.** Older equal allowed, newer equal disqualifies (E12).
- **Limits.**
  - About 3 months of intraday data per market.
  - Descriptive counts, not forecasting tests (none of these proposals adds score weight).
  - The OB touch comparison has small n per bucket.
  - The iFVG replica omits the engine's `bar_index > createdBar` subtleties on the creation bar, which are immaterial to the rates.
- **Downloaded sources** (untrusted, read only, never executed): `smc_b_tools/dl_pysmc` (smc.py), `dl_pyind` (PyIndicators wheel), `dl_pyne` (PyneCore `ta.py`), `dl_pinets` (PineTS pivot sources and changelog).
