# DOL Engine v6 · Draw on Liquidity (TradingView Pine Script v6)

`DOL_Engine.pine` is an original Draw on Liquidity indicator. It compiles with 0 errors and 0 warnings on
TradingView's own Pine v6 compiler. It does not repaint: the engine runs on confirmed bars only, pivots are
confirmed, every `request.security` call uses `[1]` + `lookahead_on`, and learning only uses resolved outcomes.

## What it shows
- **DOL:** the highest-ranked liquidity target (BSL/SSL pools, FVG, iFVG, OB, Breaker) with its zone,
  glow line, origin anchor and a `DOL ▲ BSL 78 / PoT 64.2%` label. Former targets leave a ghost trail.
- **PoT:** the calibrated probability that price touches a target within the horizon.
- **Reach bands:** dotted levels above and below price with a 50% chance of being touched within the horizon.
- **Bias table:**
  - HTF / STF / EXE structure, ALIGN, NEWS, VOL, DOL and PoT.
  - **FIRST:** odds that the nearest target above is taken before the nearest below.
  - **SKILL:** measured Brier skill of PoT on this chart.
  - **HIT:** DOL hit rate.
  - **WIN** and **EDGE:** virtual trades on the optional execution signals, with win rate, profit factor,
    expectancy and drawdown.
- **News Guard:**
  - Daily release windows.
  - An event calendar pre-filled with the official FOMC dates for 2025–2027.
  - Detection of news spikes that show both an abnormal range and abnormal volume.
- **Auto mode:** reads the chart timeframe and sets Scalping, Day Trading or Swing timeframes, distances and horizons.

## Research behind v6
A Python replica of the engine was run on 26 datasets: 13 markets on 5m and 1h, about 1.1M bars.
- **Markets:** BTC, ETH, SOL, ES, NQ, GC, CL, EURUSD, GBPUSD, USDJPY, SPY, QQQ and TSLA.
- **Samples:** about 519k resolved targets.
- **Method:** time-ordered 70/30 train/test splits, so every result below is out-of-sample.

| PoT model (test, mean over 26 datasets) | Brier skill |
|---|---|
| Analytic random walk only | ≈ 0.14 |
| Empirical excursion + analytic blend (base) | 0.192 |
| v5 bin calibration on top | 0.194 |
| **v6 learning layer + slow per-chart learning** | **0.201** |
| Online learning with all 20 ICT features | 0.192 (over-fits) |

What the data showed:
- **Distance and volatility regime drive touch probability.** Elevated ATR means fewer touches than the
  random walk predicts, and short-term momentum toward a level mean-reverts.
- **Liquidity type showed no measurable out-of-sample value**, whether for touch probability or for which
  side is taken first. This covers EQH/EQL, sessions, PDH/PDL and HTF levels, as well as HTF bias, sweeps,
  premium/discount, confluence and the DOL score.
- **The DOL side is taken first 59.3% of the time.** That is exactly what distance alone implies (59.3%).
- **Execution setups had no reliable edge.** The setups tested were HTF-aligned breaks with the DOL on the
  same side, plus sweep and displacement filters. With a symmetric 1-ATR stop and target, trading with the
  signal won 48.7% and trading against it won 49.8%.
  v5's tracker almost never traded because its 15-bar stop made the R:R target unreachable. v6 places the stop
  beyond the swept liquidity and targets the nearest liquidity that pays at least 1R.

With the v6 logic and TradingView's default 5,000-bar window, the average across the 26 datasets was:
- SKILL +20.3%
- DOL HIT 74%

## Usage
TradingView → Pine Editor → paste `DOL_Engine.pine` → Add to chart. Leave Trading Mode on **Auto**.
PoT, FIRST and reach bands are probabilities, not guarantees. Judge the signals only by the chart's own
WIN and EDGE rows, with a realistic round-trip cost.
