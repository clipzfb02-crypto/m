# m

## Liquidity Flow Pro [Non-Repaint] — TradingView Pine Script v6

`liquidity-flow-pro.pine` is an overlay indicator that maps **estimated** resting liquidity and shows how it is split between the two sides of price:

```
EST. LIQUIDITY FLOW
SELL-SIDE        92%
██████████████████░░
BUY-SIDE          8%
TARGET     SELL-SIDE ▼
STRENGTH       EXTREME
MODEL CONF.        81%
KEY POOL  25125.50 · 0.42 ATR
```

**What the percentage means:** the share of the currently scored *active* liquidity that rests above price (buy-side) versus below price (sell-side). It is **not** a probability of direction. "92% SELL-SIDE" means 92% of the liquidity the model scores sits below price. It does not mean a 92% chance that price falls. The model uses only chart data (OHLCV, swings, session levels, HTF swings). It does not read an exchange order book.

### Install
TradingView → Pine Editor → paste the whole file → **Add to chart**.

### Model architecture
| Layer | What it contributes |
|---|---|
| 1. Swing liquidity | Confirmed `ta.pivothigh` / `ta.pivotlow` → buy-side (highs) and sell-side (lows) pools |
| 2. Clustering | Swings within `Equal High/Low Tolerance × ATR` merge into one EQH/EQL pool (1.0× / 1.5× / 2.0× / 2.5× cap) |
| 3. Repeated tests | Approaches into the tolerance band that hold add persistence (up to +1.5) |
| 4. Structure | Range-extreme swings and the protected swing behind each BOS get a structural bonus |
| 5. HTF liquidity | HTF swings via `request.security(..., expr[1], lookahead_on)`: completed HTF bars only |
| 6. Session liquidity | Previous day / week / month highs and lows from completed periods only |
| 7. Sweep state | Wick beyond the level + confirmed close back inside = **sweep** (pool leaves the active score). Close beyond = **taken** (pool removed) |

Per pool: `strength × freshness (floor 50%) × 1/(1 + 0.25·w·distanceATR)`. Pool weights are **aggregated** per side. Secondary factors (structure tilt, market pressure, premium/discount) can each multiply a side by **at most 1.25×**, so they never override the pool map. Scores are EMA-smoothed and normalised with a stability prior, so `BUY% + SELL% = 100` exactly and tiny differences cannot print 99/1.

### Non-repainting rules
* Pools, sweeps, flips, shifts, signals and alerts commit only on confirmed bars (`barstate.isconfirmed`).
* Swings are registered only after confirmation, at their fixed price.
* HTF data uses the `[1]` + `lookahead_on` idiom, so it carries no future leakage.
* Only the dashboard percentages update live. `Freeze Current-Bar Calculation` holds them at the last confirmed value.

### Main settings
* **Liquidity Detection:** Swing Length (5), Equal Tolerance (0.15 ATR), Max Pools (30), Minimum Pool Strength, Max Distance, Liquidity Memory.
* **Liquidity Calculation:** Distance / Equal Level / Volume / Structure / HTF / Session weights, Smoothing (3), Percentage Stability, Balanced Threshold (8 pts), Freeze.
* **Flow Model:** Liquidity Only, Liquidity + Pressure, Liquidity + Structure (default), or Balanced. Optional Premium/Discount.
* **Higher Timeframe:** on, Auto (1m→15m, ≤5m→1H, ≤1H→4H, ≤4H→1D, 1D→1W).
* **Sessions:** PDH/PDL on, PWH/PWL on, PMH/PML off, current session off.
* **Sweeps:** Strict / Balanced (default) / Aggressive. Keep swept levels faded. Remove swept levels from the score.
* **Dashboard / Visuals:** position, size, rows, wording (BUY-SIDE/SELL-SIDE or ABOVE/BELOW), Top N targets (3), flip/shift markers.
* **Signals:** off by default. When on, a signal needs sweep + structure shift + flow agreement, and fires at most once per setup.
* **Alerts:** buy-side or sell-side becomes dominant, flip, shift up/down, buy-side/sell-side sweep, major pool, new target, BUY/SELL setup.
* **Debug:** factor breakdown in the dashboard and raw scores in the Data Window.
