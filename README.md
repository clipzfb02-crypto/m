# DOL Engine v2 · Draw on Liquidity

An open-source TradingView indicator (Pine Script v6) that finds, scores and tracks liquidity, then highlights the pool the market is most likely drawing to next: the **Draw on Liquidity (DOL)**. The indicator also records how its own past picks played out on the chart you're viewing.

> This is an independent implementation written from a public feature description. It shares no code with any commercial script.

## Install

1. Open TradingView → **Pine Editor**.
2. Paste the contents of [`indicators/dol_engine.pine`](indicators/dol_engine.pine).
3. Click **Add to chart**.

Keep the chart timeframe **at or below the Execution TF** of the selected Trading Mode. The panel shows a warning when it is higher.

## What it looks at

| Source | Details |
|---|---|
| **Chart swings** | BSL above swing highs, SSL below swing lows. Equal highs and lows fold into one pool, which moves to the **outermost** print. |
| **STF / HTF swings** | Confirmed pivots from the sub-structure and structure timeframes, kept only if they are still unswept on their own timeframe. |
| **Key liquidity** | PDH/PDL, PWH/PWL, and Asia, London and NY-AM session highs and lows. Each zone is anchored to the exact candle that printed it. |
| **Imbalances** | Chart FVGs with a displacement quality gate, plus HTF FVGs (non-repainting `request.security`). |
| **Blocks** | Order blocks from the leg that broke structure. Quality depends on imbalance in the leg, liquidity taken at the origin, and leg size. A block that was already revisited is skipped. **Breakers** only come from blocks that swept liquidity. |

External pools (STF/HTF swings and key levels) live in a **registry**. When price drifts too far they leave the scoring pool, and they come back once price returns within range.

## How a level is scored

`score = 100 × mult × Σ(weight × pillar) / Σ weights`

| Pillar | Default weight | Measures |
|---|---|---|
| **Proximity** | 25 | ATR distance blended with first-passage *reachability*. It tapers below *Min Target Distance*, because a zone price is sitting on is being delivered, not drawn to. It is 0 beyond *Max ATR Distance*. |
| **Freshness** | 10 | Liquidity *matures* (stops build up for a while), then slowly goes stale. Imbalances decay with a half-life. Higher-timeframe levels age in their own timeframe. |
| **Confluence** | 15 | Overlap with PDH/PDL, PWH/PWL, the midnight / London / NY opens, the daily EQ and the HTF dealing-range EQ. |
| **Density** | 20 | For liquidity, the *magnitude* of the pool: equal highs/lows, stacked pools, tests, swing prominence, and source tier (PW > PD > session > HTF > STF > chart). It also counts coiling and inducement. For imbalances it is displacement quality. |
| **Draw** | 30 | Alignment with the order-flow vector **D** ∈ [-1, 1]. D combines MTF swing structure, recent displacement, and the outcome of recent liquidity raids: a raid that holds means continuation, a raid that rejects means reversal. |

`mult` adjusts the score:
- *Origin lockout*: a fresh FVG, OB or breaker is the origin of the move, not its target, until price has left it.
- *Inner-pool* penalty: the outermost pool in a stack is the draw.
- *Counter-draw* penalty.
- *Partial mitigation*.
- *Killzone affinity*: London raids Asia; NY raids London and the previous day.
- *Volume-profile path cost*: thin-volume paths score higher than high-volume walls.
- *Adaptive calibration* from the accuracy ledger.

**Selection** first considers levels on the side D points to. If none qualifies, it shows a `⚠ COUNTER-DRAW` target. A challenger must beat the current DOL by the hysteresis (double that to flip sides) on **two consecutive bars**. Outside killzones the hysteresis widens. A target whose side no longer matches the draw is ghosted as `⊘ INVALIDATED`.

## On the chart

- **DOL zone**: opacity follows the score. It has a neon core line, a tether from price, and a terminal HUD showing:
  - type and tags (`EQx2 · STK1 · T3`), the score meter, and PoT % with its reach class (`CORE`, `EXTENDED` or `STRETCH`);
  - typical bars to hit, the draw vector, the current killzone, distance and age;
  - **R:R · WIN % · EV** against an **invalidation** placed just beyond the nearest opposing pool.
- **HTF Objective**: the strongest pool on the draw side, ranked without proximity.
- **Secondary targets**, the optional **candidate pool**, and optional **reach bands**: the empirical median and 80th-percentile move over the PoT horizon.
- **iFVG** zones with a CE line, removed after too many body closes inside them.
- **LVN** zones from the 1H volume profile. They are off by default.
- **Ghost trail** of targets marked `✕ SWEPT`, `⊘ EJECTED` or `⊘ INVALIDATED`.
- **Themes**: Neon, Matrix, Ice, Mono or Custom.

## Terminal panel

- **Bias by timeframe**: swing bias and internal bias for the HTF, STF and Execution timeframes, plus where price sits in each dealing range (premium or discount, as a %).
- **Draw**: the order-flow draw vector with a meter.
- **Target**: score, PoT, reach class and distance, then R:R, race WIN % and EV.
- **Pool**: the scoring pool, external registry and iFVG counts.
- **Accuracy**:
  - **DOL HIT %** with its Wilson 95% interval and the rolling last-50 rate.
  - **EDGE**: hits above what a *random level at the same distance* would get, with a z-score and a verdict (`✓ EDGE`, `~ WEAK` or `✕ NO EDGE`).
  - **BARS→HIT**: average and median bars to hit, plus *heat*, the 80th-percentile adverse excursion in ATR.
  - The Full view adds per-family hit rates and race stats (win %, average R, profit factor).

## Probability of Touch

- **Analytic**: first-passage probability for a random walk with drift, using recent bar volatility.
- **Empirical** (the default): blends in how often price on this symbol actually travelled that far within the horizon, split by HTF regime and learned bar by bar from closed history. The analytic model acts as a Bayesian prior.

Both models are capped at 95%. The readout is deliberately live and updates every tick.

## Alerts

| Alert | Fires when |
|---|---|
| New DOL Target Active | the engine commits to a new target that passes the PoT filter (bar close) |
| New iFVG Formed | an FVG inverts (bar close) |
| DOL Target Swept | real-time price touches the active DOL zone (intrabar) |
| Draw Direction Flip | the order-flow draw flips side (bar close) |

Each event also calls `alert()` with a detailed message. Use **Any alert() function call** to receive it.

## Repainting

- Pool updates, scoring, selection, the ledger, iFVG and breaker logic only run when `barstate.isconfirmed` is true.
- Every `request.security()` call reads `[1]`-offset series with `barmerge.lookahead_on`, and never at a timeframe below the chart's.
- On charts above 1H, the volume profile uses `request.security_lower_tf` on closed bars.
- The **PoT readout** and the **DOL Target Swept** alert are deliberately live.

## Performance

Levels are tracked on every bar. Scoring, selection and the ledger run on the last *Calculation Depth* bars (default 5000). Raise that setting for longer accuracy statistics, or lower it for faster loading.

## Disclaimer

This is for education only. It is not financial advice. The accuracy panel describes the indicator's past behaviour on the loaded history. It does not guarantee future results.
