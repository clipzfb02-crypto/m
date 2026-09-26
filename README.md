# DOL Engine v3 · Draw on Liquidity (TradingView Pine Script v6)

`DOL_Engine.pine` is an original, self-calibrating Draw on Liquidity indicator. It compiles
with 0 errors and 0 warnings on TradingView's own Pine v6 compiler.

- **Clean default chart:** one DOL zone anchored to its origin candle, with a glow line and a
  label (`DOL ▲ BSL 87 / PoT 72.4%`), a faint ghost trail of former targets, and a bias table
  (HTF / STF / EXEC, ALIGN, DOL, PoT, and the measured HIT rate).
- **Target pool:** BSL/SSL pools (swings with equal-level density and reaction strength,
  PDH/PDL, PWH/PWL, PMH/PML, sessions, STF/HTF swings whose liquidity hasn't been wicked out yet)
  plus FVG, iFVG, OB and Breaker zones.
- **Ranking:** score (0–100 from proximity, freshness, confluence, density, structure and HTF)
  blended with calibrated PoT, with hysteresis and a minimum distance for new targets.
- **PoT:** the first-passage probability of a drifting random walk (Garman-Klass volatility,
  EWMA drift), corrected by this chart's own resolved predictions. Capped at 95%.
- **Non-repaint:** the engine runs on confirmed bars only, uses confirmed pivots, every
  `request.security` call uses `[1]` + `lookahead_on`, and calibration only uses resolved outcomes.

Usage: TradingView → Pine Editor → paste `DOL_Engine.pine` → Add to chart.
