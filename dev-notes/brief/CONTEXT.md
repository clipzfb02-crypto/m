# DOL Engine v2: shared brief for every agent

## The project
- Main file: /home/user/m/indicators/dol_engine.pine (Pine Script v6, a TradingView indicator, about 2448 lines). README: /home/user/m/README.md.
- Frozen copy of the version being improved: /tmp/claude-0/-home-user-m/7ce60006-3639-59b1-8cd3-87355409d58a/scratchpad/brief/baseline_v2.pine. Line numbers in all prompts refer to this file.
- It is an original, independent indicator. It implements the *feature set* of a commercial invite-only script ("TradeAxis DOL"), described in /tmp/claude-0/-home-user-m/7ce60006-3639-59b1-8cd3-87355409d58a/scratchpad/brief/tradeaxis_description.md. Never copy that product's name or branding. Our indicator is "DOL Engine v2".
- The user wants the chart to LOOK like the reference screenshot /tmp/claude-0/-home-user-m/7ce60006-3639-59b1-8cd3-87355409d58a/scratchpad/brief/reference_look.png (open it with the Read tool). It shows:
  - a compact top-right table: "Timeframe | Bias" with rows D / 4H / 1H and values BULLISH (green) / BEARISH (red);
  - ONE active target zone: a dashed-border translucent box with a bright neon glow centre line, anchored left at the candle that formed it and extended about 20 bars right of the last candle;
  - a dashed tether line from the last candle to a dark label reading "Target: BEFVG" / "PoT: 70.1%";
  - dark-green iFVG boxes ending on the same right edge.
- The user is a trader. They have said "SO BAD ... 100000X BETTER". They want a dramatically better indicator: correct, robust, accurate DOL targets, and a premium, clean look. They tried an earlier version on TradingView. We do not know exactly what they disliked. Treat "it does not compile/run", "it is slow or times out", "the targets look wrong or jump around", "it looks cluttered or ugly" and "missing features" all as plausible complaints.

## Hard constraints (never violate)
- It must COMPILE in TradingView Pine v6. No compiler is available offline, so be doc-grounded. Docs (mirror of the official v6 reference and manual):
  - /tmp/claude-0/-home-user-m/7ce60006-3639-59b1-8cd3-87355409d58a/scratchpad/docsrc/jabez4jc_pinescriptv6/reference/*.md: built-ins by namespace (INDEX.md lists them), with exact signatures and qualifiers.
  - /tmp/claude-0/-home-user-m/7ce60006-3639-59b1-8cd3-87355409d58a/scratchpad/docsrc/jabez4jc_pinescriptv6/language/*.md: type system, execution model, loops, methods, objects, arrays, maps, UDFs.
  - /tmp/claude-0/-home-user-m/7ce60006-3639-59b1-8cd3-87355409d58a/scratchpad/docsrc/jabez4jc_pinescriptv6/writing_scripts/: includes the LIMITATIONS page (execution time, loops, drawing counts, max_bars_back, request limits).
  - /tmp/claude-0/-home-user-m/7ce60006-3639-59b1-8cd3-87355409d58a/scratchpad/docsrc/jabez4jc_pinescriptv6/errors/: error codes.
  - /tmp/claude-0/-home-user-m/7ce60006-3639-59b1-8cd3-87355409d58a/scratchpad/docsrc/jabez4jc_pinescriptv6/concepts/: other-timeframes / repainting / sessions etc.
  - A second mirror: /tmp/claude-0/-home-user-m/7ce60006-3639-59b1-8cd3-87355409d58a/scratchpad/docsrc/mmmy_pine-script-doc-v6/.
  - Use grep. Quote the doc text for any compile claim.
- Non-repainting:
  - Structure, scoring, selection, ledger, iFVG and breaker logic run only when barstate.isconfirmed.
  - request.security uses [1]-offset expressions with lookahead_on, and is never requested below the chart TF (f_tfSafe).
  - The PoT readout and the sweep alert are deliberately live.
- Pine has no forward references. Functions must be declared before use, and globals before the functions that reference them.
- Keep the Clean style (the default) visually matching the reference screenshot. Terminal style is the alternative full-HUD view.
- Syntax checker (pynescript; it only checks SYNTAX, not types): `/tmp/claude-0/-home-user-m/7ce60006-3639-59b1-8cd3-87355409d58a/scratchpad/tools/pine_parse.sh <file> [<baseline_file>]`.
  - With a baseline it parses only the top-level statements that changed.
  - It takes about 1 to 10 minutes. The big engine `if` block is slow.
  - Prints one OK/FAIL line per changed statement.
  - Only run it if your role says so.

## Constructs already verified as compiling (do NOT re-report them as errors unless you have a doc quote proving otherwise)
- box.new(..., border_style = line.style_dashed); color.from_gradient at global scope; label.new textalign/tooltip;
  table.cell without text_font_family; string switch with default branch; `for [i, x] in array`; methods on UDTs;
  `var Level activeLv = na`; tuple returns via request.security with lookahead_on; map<int,int> contains/get/put/remove;
  request.security_lower_tf with ignore_invalid_timeframe; max_bars_back(time, 5000); f_tfSafe(simple string tf).
- Earlier audits produced several plausible-but-wrong compile claims. Be rigorous.

## History of decisions (do not undo without strong evidence)
- A liquidity pool is swept only when price trades THROUGH it (strict >, <). Arrays (FVG/OB) count as reached on a touch.
- Selection is draw-side first with a counter-draw fallback. A challenger must lead for 2 bars, and a side flip needs 2x hysteresis.
- Day Trading mode is D / 4H / 1H, as in the screenshot.
- Classic theme: buy-side #39FF14, sell-side #FF1744, bias green #00C864, bias red #E63C3C, panel black.
