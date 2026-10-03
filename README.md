# m

## Liquidity Flow Pro [Non-Repaint] — TradingView Pine Script v6

`liquidity-flow-pro.pine` is an overlay indicator. It maps **estimated** resting liquidity and shows how that liquidity splits between the two sides of price:

```
EST. LIQUIDITY FLOW
SELL-SIDE  ███████████░  92%
BUY-SIDE   █░░░░░░░░░░░   8%
TARGET          SELL-SIDE ▼
STRENGTH            EXTREME
MODEL CONF.             81%
KEY POOL   24980.25 · 0.42 ATR
LAST SWEEP  BSL ✕ 25125.50 · 3 bars ago
   EXTREME SELL-SIDE LIQUIDITY
```

**What the percentage means:** it is the share of the currently scored *active* liquidity resting above price (buy-side) versus below price (sell-side). It is **not** a probability of direction. "92% SELL-SIDE" means 92% of the liquidity the model scores sits below price, not that there is a 92% chance price falls. The model uses only chart data: OHLCV, swings, session levels and HTF swings. It does not read an exchange order book.

### Display styles
* **Video** (default): the chart is split at the current price into two zones, matching the reference clip. A red zone above price is labelled `Sellers xx.x%` and a green zone below is labelled `Buyers yy.y%`. Each percentage is that zone's share of the estimated active liquidity, and the two always add up to 100%.
  * The zones run from price to the highest high / lowest low of `Zone Lookback` bars (default 50).
  * The labels can be changed to Buy-side/Sell-side or Above/Below.
  * `Video: also show dashboard & levels` adds the Pro drawings on top.
* **Pro:** the dashboard plus every liquidity pool, sweep and target drawn on the chart.

### Install
In TradingView, open the Pine Editor, paste the whole file and click **Add to chart**.

### Model
| Layer | What it contributes |
|---|---|
| Swing liquidity | Confirmed `ta.pivothigh` / `ta.pivotlow` swings become buy-side (highs) and sell-side (lows) pools. |
| External swings | A swing that also holds over `Swing Length × 3` bars is external-range liquidity. Tag `EXT`, +0.5 structure bonus. |
| Clustering | Swings within `0.15 × ATR` merge into one EQH/EQL pool: 1.0×, 2.25×, 3.5×, then 4.75× (capped). A cluster never scores below the same swings kept separate. |
| Repeated tests | Approaches into the tolerance band that hold add persistence, up to +1.5. |
| Structure | Range-extreme swings, and the protected swing behind each break of structure, get a structure bonus. |
| HTF liquidity | HTF swings come from `request.security(..., expr[1], lookahead_on)`, so only completed HTF bars are used. |
| Session liquidity | Previous day / week / month highs and lows. Optional Asia / London / New York session highs and lows. Completed periods only. |
| Sweep state | A **sweep** is a trade beyond `level + tolerance` followed by a confirmed close back inside; the pool leaves the active score. A close beyond the band means **taken**, and the pool is removed. Anything inside the band is a **test**. |

**Per-pool weight:** `strength × freshness (floor 50%) × 1/(1 + 0.25·w·distanceATR)`. Weights are **aggregated** per side.

**Secondary factors:** structure tilt, market pressure and premium/discount can each multiply a side by **at most 1.25×**, so they can never override the pool map.

**Normalisation:** scores are EMA-smoothed and normalised with a stability prior, so `BUY% + SELL% = 100` exactly. With too little scored liquidity, the reading shrinks continuously to 50/50 and the dashboard shows `LOW DATA`.

### Non-repainting rules
* Pools, sweeps, flips, shifts, signals and alerts commit only on confirmed bars (`barstate.isconfirmed`).
* Swings are registered only after confirmation, at their fixed price.
* HTF data uses the `[1]` + `lookahead_on` idiom, so no future data leaks in.
* Only the dashboard updates live. It also shows a `RAIDING / BREAKING … · LIVE` status while price is inside a pool on the developing candle. Nothing is marked until the bar closes. `Freeze Current-Bar Calculation` holds the dashboard at the last confirmed value.

### Verification
TradingView's compiler can't be reached from the build environment, so the script was checked in two other ways:

1. **Static checks.**
   * The file parses with [`pynescript`](https://pypi.org/project/pynescript/).
   * A custom AST lint checks declare-before-use, Pine's rule that a function only sees globals declared before it, user-function arity, and UDT field names. It reports 0 issues.
   * Every built-in function, argument and constant used was audited against the v6 API.
   * Line-continuation indentation and bracket balance are checked.
2. **Behavioural checks.** `tools/liquidity_model_sim.py` is a line-for-line Python reference model of the engine, scoring and events. Run it with `python3 tools/liquidity_model_sim.py`. It tests the spec scenarios on realistic synthetic bars:

| Scenario | Result |
|---|---|
| A: strong equal highs above, weak lows below | 68.6% BUY-SIDE, buy-side dominant |
| B: mirror of A | 68.6% SELL-SIDE (exactly symmetric) |
| A2: clustering adds liquidity | 58.2% clustered vs 50.3% un-clustered control |
| C/D: sweep of the equal highs/lows | Detected on the confirmed candle. The cluster's score drops to 0 on that bar. |
| E: strong liquidity on both sides | 47/53, BALANCED |
| F: no data / flat market | 50/50, LOW DATA |
| G: giant green candle | Bounded. It consumes buy-side liquidity and does not flip the reading to buy. |
| Random walks (18k bars) | About 1 flip per 68 bars, ~3 signals per 1,000 bars, mean move 1.9 points per bar |

The simulation does not cover HTF and calendar/session levels, because they need multi-timeframe data.

### Main settings
* **Liquidity Detection:** Swing Length (5), External Swings (×3), Equal Tolerance (0.15 ATR), Max Pools (30), Minimum Strength, Max Distance (50 ATR), Liquidity Memory (200 bars, auto-scaled with swing length).
* **Liquidity Calculation:** Distance (1.0), Equal Level (1.5), Volume (1.0), Structure (1.0), HTF (1.0) and Session (1.0) weights. Smoothing (3), Percentage Stability (0.5), Balanced Threshold (8 points), Freeze.
* **Flow Model:** Liquidity Only, Liquidity + Pressure, Liquidity + Structure (default), or Balanced. Optional Premium/Discount.
* **Higher Timeframe:** on, Auto (1m→15m, ≤5m→1H, ≤1H→4H, ≤4H→1D, 1D→1W).
* **Sessions:** PDH/PDL on, PWH/PWL on, PMH/PML off, current session off, Asia/London/NY off (session times and timezone are editable).
* **Sweeps:** Strict / Balanced (default) / Aggressive. Swept levels are kept faded with a ✕ at the exact level, removed from the score, and capped at 20.
* **Dashboard:** position, size, per-side coloured bars, target, strength, confidence, key pool, nearest major pool, last sweep, structure. Wording is BUY-SIDE/SELL-SIDE or ABOVE/BELOW.
* **Visuals:** zones, lines, equal-level and session tags, top N targets (3), flip markers (on), shift markers (off).
* **Signals:** off by default. A signal needs a sweep, then a structure shift, then flow moving toward the new side, and it fires at most once per setup.
* **Alerts:** 12 `alertcondition()`s, plus one detailed `alert()` message per bar (prices, pool tags, sweep depth, current split).
* **Debug:** factor breakdown in the dashboard and raw scores in the Data Window.
