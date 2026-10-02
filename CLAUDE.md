# Working on DOL_Engine.pine

## The user's setup (always tune for this)
- Trades **MNQ1!** (Micro Nasdaq) and the **S&P 500** (ES1! / MES1!) with real money on a Lucid Trading prop account.
- Charts: **1-minute and 5-minute only**. Session: **New York**.
- Reads the chart on mobile and acts on colour alone: **solid blue = BUY, solid red = SELL**. Blue and red must appear
  only on real trades (banner, entry lines, triangles). Everything else stays white / grey / amber.
- Wants to trade toward the DOL without waiting (Trade Mode default = DOL Direction).

## Rules for every change
- Pine Script v6 **indicator** (not a strategy). No repainting: engine on confirmed bars, `request.security` with `[1]` + `lookahead_on`.
- Must compile with **0 errors and 0 warnings** on TradingView's compiler before it is handed over.
- After each version, paste the **full** script in chat and send the file (the user is on a phone).
- Keep it fast; no long-running loops.
- Be honest about results: research on 3.7 years of 1-minute NQ / S&P data found no reliably profitable setup after costs.
