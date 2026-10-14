# DOL Engine · Draw on Liquidity

An open-source TradingView indicator (Pine Script v6) that finds, scores and tracks liquidity levels, then highlights the one most likely to be the market's next **Draw on Liquidity (DOL)**.

It does not plot every swing and gap. It keeps a small pool of candidate levels, scores each out of 100 on every confirmed bar and draws only the winner as a target zone. A few secondary targets can be shown too.

> This is an independent implementation written from a public feature description. It shares no code with any commercial script.

## Install

1. Open TradingView → **Pine Editor**.
2. Paste the contents of [`indicators/dol_engine.pine`](indicators/dol_engine.pine).
3. Click **Add to chart**.

Keep the chart timeframe **at or below the Execution TF** of the selected Trading Mode. The bias table shows a warning if it is higher.

## How a level is scored

Every level in the pool gets four pillar scores between 0 and 1. These are blended with user weights into a score out of 100:

| Pillar | What it measures | Default weight |
|---|---|---|
| **Proximity** | ATR-normalised distance from price: `1 − dist / MaxATR`, and 0 beyond *Max ATR Distance*. Beyond *Max ATR × Eject Multiplier* the level is ejected from the pool. | 35 |
| **Freshness** | Exponential decay: `0.5 ^ (age / half-life)` | 20 |
| **Confluence** | Overlap (within *Confluence Tolerance*) with PDH, PDL, daily EQ, the Midnight / London / NY opens and the HTF range EQ. HTF and STF swing levels get extra hits. The level also gets a bonus when it sits on the side the HTF bias points to. | 25 |
| **Density** | For BSL/SSL: equal highs or lows folded into the level, candle *coiling* (overlap ratio) and *inducement sweeps* before the level formed. For gaps and blocks: coiling and inducement. | 20 |

The highest score becomes the active DOL, as long as it clears *Min Score for DOL*. A challenger has to beat the current target by *Switch Hysteresis* points to take over, which stops the target from flickering.

### Level sources

* **BSL / SSL**: confirmed chart swing highs and lows, plus swings from the HTF and STF structure. Equal highs and lows within tolerance merge into a single level and raise its density.
* **Fair Value Gaps**: three-candle imbalances above a minimum ATR size.
* **Order Blocks**: when a candle body closes through the last swing, the last opposite-close candle at the origin of the leg.
* **Breakers**: order blocks that price later closed through. Their polarity flips.

The pool is capped at *Pool Size*. When it overflows, the weakest level that isn't the active target is dropped.

## Modules

* **Trading Modes**: sets the HTF, STF and Execution timeframes.

  | Mode | HTF | STF | Execution |
  |---|---|---|---|
  | Swing | W | D | 4H |
  | Day Trading | 4H | 1H | 15m |
  | Scalping | 1H | 15m | 5m |
  | Custom | your choice | your choice | your choice |

* **DOL zones**: the target is drawn as a zone, not a line. It stretches left to the nearest historical candle that printed the level. A touch anywhere on the zone's near edge counts as a sweep. The terminal-style readout shows the level type, score meter, PoT and ATR distance. Hover over it to see the four pillar scores.
* **Probability of Touch (PoT%)**: the chance that price touches the zone within *PoT Horizon* bars. It uses a first-passage (reflection principle) model with recent bar volatility and an optional drift term, and is capped at 95%. *Minimum PoT to Show DOL* hides targets below a threshold.
* **iFVG**: unmitigated FVGs are watched. When a candle closes fully through one, it flips into an inversion zone with the opposite polarity. Once more than *Max Body Closes Inside* candles close inside it, or price closes back through it, the zone is removed.
* **LVN (Low Volume Nodes)**: 1H OHLCV bars build a background volume profile. 60% of each bar's volume is spread across its range and 40% across its body. The nearest low-volume runs above and below price are drawn. This module is off by default.
* **Ghost Trail**: when the active DOL is swept or ejected, a faded copy stays on the chart, marked `SWEPT` or `EJECTED`.
* **Bias Table**: shows bias for HTF, STF and Execution. Bias flips only when a candle **body** closes through the last confirmed swing node. The table also shows premium or discount against each timeframe's range EQ, plus the active target, PoT and pool status.

## Alerts

| Alert | Fires when |
|---|---|
| New DOL Target Active | the engine switches to a new highest-scoring level (on bar close) |
| New iFVG Formed | an FVG inverts (on bar close) |
| DOL Target Swept | real-time price touches the active DOL zone (intrabar) |

Each event also calls `alert()` with a detailed message. Use **Any alert() function call** to get the level type, price and score.

## Repainting

* Pool updates, scoring, target selection, iFVG and breaker logic only run when `barstate.isconfirmed` is true.
* Every `request.security()` call reads `[1]`-offset series with `barmerge.lookahead_on`. Historical bars only see higher-timeframe bars that had already closed.
* The **PoT readout** and the **DOL Target Swept** alert are deliberately live. They update every tick from the unclosed bar.

## Disclaimer

This is for education only. It is not financial advice.
