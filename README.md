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

## Reading the chart (v6.2)
Blue and red appear only on real trades. Everything else is white, grey or amber.

| Banner | Meaning |
|---|---|
| Solid blue **BUY NOW** / solid red **SELL NOW** | A new trade passed every filter, the Edge Gate and the daily limit. It shows contracts for your $ risk, entry, stop and target. |
| Blue / red text, **RUNNING · too late to enter** | A trade is already open. Do not chase it. Stop and target are shown for anyone already in. |
| Amber **EXIT** | The trade just closed (target, stop, time stop or the 15:55 New York close). Close it if you are still in. |
| Grey **NO TRADE** / **WAIT** | Do not trade. The banner says why. |

- **One trade at a time.** A signal is only taken when no trade is open, so a triangle, an alert and the banner always describe the same trade.
- **Day close.** An open trade is closed at 15:55 New York and nothing is carried overnight. This applies when Signal Hours are not Any Time.
- **Alerts.** Entry alerts include entry, stop, target and size. There is also an exit alert.

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

### Target Win Rate mode (default 90%)
The virtual trades use the signal's stop and a take-profit sized for the chosen win rate. After every closed
trade the take-profit distance is nudged: shorter after a loss, slightly longer after a win. This lets each
chart's real win rate settle at the target.
- **Fills:** they follow TradingView's broker emulator. Gaps fill at the open. When the stop and the target are
  both inside one bar, the side nearer the open is hit first.
- **Test:** 12 markets (BTC, ETH, ES, NQ, QQQ, SPY, TSLA, Gold, Crude, EURUSD, GBPUSD, USDJPY) on 5m, 15m, 1h and 1D.
  Each chart ran one trade at a time with no look-ahead.

| Target | Real win rate | Per market |
|---|---|---|
| 85% | 84.9% | 84–87% |
| 90% | 89.6% | 10 of 12 exactly 90%; EURUSD 88% (1-pip data), ETH 92% |
| 95% | 93.7% | 93–96%; EURUSD 89% (1-pip data) |

A high win rate here comes from a small target (≈0.09R at 90%), not from predicting direction. The average trade
was about 0R before costs. Enter your real round-trip cost, because small targets are very sensitive to it.
Judge the setup by EDGE (expectancy), not by WIN alone.

### MNQ / MES 1-minute research (real-money settings)
- **Data:** about 3.7 years of 1-minute Nasdaq-100 and S&P 500 index data (Dukascopy). About 420 full New York
  sessions per market were available.
- **Costs:** 1.0 point round trip on NQ, which is 4 MNQ ticks, and 0.5 point on the S&P, which is 2 MES ticks.

**What we tested:**
- **Strategy families:** each was tuned on 2023 through March 2025 and scored on April 2025 through September 2026.
  - Opening-range breakout.
  - Noise-boundary intraday momentum.
  - First-half-hour intraday momentum.
  - ICT-style sweep reversals of the prior-day and overnight highs/lows.
- **Models:** linear and gradient-boosted models on about 20 price features, walk-forward over 2024, 2025 and 2026.
- **Result:** none gave a reliable profit after costs.

**Where the losses come from:**
- The execution signal is about break-even before costs. Costs cause most of the loss: −0.08R per trade on NQ
  and −0.17R on the S&P.
- Overnight and after-hours signals, and signals with tight stops, lose 3–5× more.
- v6.1 adds two filters: Core New York hours, and skipping signals whose cost is over 3% of the stop.

| Replay, simplified signal | NQ trades | NQ total | S&P trades | S&P total |
|---|---|---|---|---|
| Old: no filters, 90% target | 20,031 (89.8% win) | −1,655R | 19,038 (84.7% win) | −3,245R |
| New filters, 90% target | 2,460 (90.0% win) | −75R | 537 (89.4% win) | −26R |
| New filters, 1R target | 1,903 | −36R | 457 | +7.5R |
| Filters + Edge Gate + daily limit | 10 | −2R | 70 | −8R |

The filters remove most of the cost damage. The Edge Gate stays closed when a chart has no proven edge, so it
barely trades. **Nothing tested here is reliably profitable on its own.** The Risk group adds tools that limit
damage: position size for a fixed $ risk, a daily loss limit and a maximum number of signals per day.

With the v6 logic and TradingView's default 5,000-bar window, the average across the 26 datasets was:
- SKILL +20.3%
- DOL HIT 74%

## Usage
TradingView → Pine Editor → paste `DOL_Engine.pine` → Add to chart. Leave Trading Mode on **Auto**.
PoT, FIRST and reach bands are probabilities, not guarantees. Judge the signals only by the chart's own
WIN and EDGE rows, with a realistic round-trip cost.
