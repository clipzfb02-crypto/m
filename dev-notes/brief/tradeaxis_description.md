# Reference product description (TradeAxis DOL, invite-only). Feature spec only; do not copy its branding.
(Reconstructed from the user's paste; these passages are verbatim.)

The TradeAxis DOL (Draw on Liquidity) is an advanced technical indicator designed to identify, score, and visually track institutional liquidity levels in real-time. Rather than merely plotting every swing point or order block on the chart, this script utilizes a complex array-based ranking algorithm aiming to isolate a highly probable "Draw on Liquidity" target at any given moment.

By analyzing historical price action, multi-timeframe structural bias, and 1H volume data, the script builds a smart queue of target levels (BSL, SSL, FVGs, Order Blocks, and Breakers) and evaluates them on a continuous, confirmed-bar basis.

Core Logic: The Scoring Algorithm. This script limits the "noise" of standard liquidity indicators by maintaining a constrained array of targets. Each is scored out of 100 on:
* Proximity weight: distance from current price (ATR-based); levels beyond a maximum distance are ejected.
* Freshness: older levels decay.
* Confluence Weight: Evaluates spatial overlap. Levels score higher if they align with key structural anchors such as Previous Day High/Low (PDH/PDL), Session Opens, equilibrium points, or Higher Timeframe (HTF) directional bias.
* Density: Analyzes candlestick coiling and "inducement" sweeps. A level scores significantly higher if the algorithm detects a build-up of equal highs/lows or range-bound density prior to the level's creation.
The level with the highest aggregate score is actively targeted by the primary DOL line.

Key Features & Modules
* Dynamic Trading Modes: The script features an adaptive multi-timeframe engine. Users can select "Swing," "Day Trading," or "Scalping." The engine automatically adjusts the HTF structure, STF (Sub-structure), and execution timeframes accordingly to fit the user's methodology.
* Inversion Fair Value Gaps (iFVG): Monitors unmitigated Fair Value Gaps and tracks them for inversion. If price closes completely through a gap, it dynamically flips into an iFVG, acting as a new support/resistance zone. These zones track subsequent body closes and are cleaned when invalidated.
* LVN zones from 1H volume profile (low-volume nodes).
* Ghost Trail: when a target is swept or ejected due to price moving too far away, it leaves a "Ghost Trail." This helps traders visualize historical targets that were recently respected or invalidated without cluttering real-time analysis.
* Real-Time Bias Table: A visual dashboard displayed on the chart that calculates the structural market bias (Bullish/Bearish/Neutral) across three distinct timeframes concurrently, relying strictly on confirmed pivot data.

How to Use in Trading
* Target Identification: Use the active primary DOL line as an objective level of interest. Because the algorithm dynamically scores levels based on current price proximity and momentum, it highlights where the market may seek liquidity next.
* Directional Alignment: Reference the Multi-TF Bias Table. Traders can look for execution signals when the Execution TF bias aligns with the HTF bias.
* iFVG Continuation: Monitor the dynamic iFVG boxes. When price invalidates a traditional FVG and the box flips color, traders can look for retests of this zone for potential trend continuation towards the active DOL target.

Alerts Included: New DOL Target Active; New iFVG Formed; DOL Target Swept.

Anti-Repainting: barstate.isconfirmed for all structural logic and array ranking. MTF request.security() calls are shifted [1].
Note: ensure the chart timeframe is equal to or lower than the "Trading Mode" Execution Timeframe.

Release notes (Mar 6 to May 1):
- Visual Update: brand new look; DOL drawn as zones anchored left to the origin candle.
- Probability of Touch (PoT%) metric, capped at 95.0%, with a "Minimum PoT to Show DOL" filter. To provide tick-by-tick updates, the PoT text evaluates unclosed data in real-time.
- Bias Table Logic Upgrade: refined market structure tracking. This removes lagging "Neutral" states by requiring true candle-body breaks of established structural nodes, providing a stricter directional bias.
- MTF Data Alignment Fix: all historical request.security calls (excluding the live PoT feed) use lookahead_on with offset series data ([1]). This removes the standard 1-bar historical lag.
- Draw Direction / order-flow awareness; key liquidity (PDH/PDL, sessions); scoring refinements; ghost trail.
