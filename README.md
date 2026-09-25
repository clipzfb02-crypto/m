# DOL Engine v2 · Draw on Liquidity (TradingView Pine Script v6)

`DOL_Engine.pine` is an original Draw on Liquidity indicator with a clean, terminal-style display.

- **Default chart:** one DOL zone anchored to its origin candle, with a glow key line and a
  label (`DOL ▲ BSL 87 / PoT 72.4%`), a faint ghost trail of former targets, and a compact
  HTF / STF / EXEC bias table with alignment.
- **Target pool:** BSL/SSL pools (swings, EQH/EQL with pre-formation density, PDH/PDL,
  PWH/PWL, PMH/PML, sessions, STF/HTF swings) plus FVG, iFVG, OB and Breaker zones.
- **Score:** 0–100 from proximity, freshness, confluence, density, structure and HTF alignment.
  Weights are normalised.
- **Non-repaint:** the engine runs on confirmed bars only, uses confirmed pivots, and every
  `request.security` call uses `[1]` + `lookahead_on`.
- **PoT:** a heuristic touch estimate, capped at 95.0%. It is not a guaranteed probability.

Usage: TradingView → Pine Editor → paste `DOL_Engine.pine` → Add to chart.
For Forex / Gold / Crypto set Sessions → Timezone to `America/New_York`.
