# DOL Engine · Draw on Liquidity (TradingView Pine Script v6)

`DOL_Engine.pine` — an original liquidity-mapping indicator: detects BSL/SSL candidates
(swings, EQH/EQL, PDH/PDL, PWH/PWL, PMH/PML, sessions, STF/HTF swings), merges them into zones,
scores them 0–100, and selects the primary Draw on Liquidity with a heuristic PoT read-out.
Also includes FVG → iFVG, order blocks → breakers, market structure (BOS/CHoCH), MTF bias
dashboard, optional LVN, ghost trail, optional confluence signals and alerts.

Usage: TradingView → Pine Editor → paste `DOL_Engine.pine` → Add to chart.
For Forex / Gold / Crypto set Sessions → Timezone to `America/New_York`.
