# DOL Engine v2 · development handoff (the project "database")

Read this first if you are a new session picking up the work. Everything needed to continue is in `dev-notes/`.

## Goal (from the user)
- Build the best possible open-source Pine Script v6 TradingView indicator, **"DOL Engine v2 · Draw on Liquidity"**, in `indicators/dol_engine.pine`. It implements the feature set of the invite-only "TradeAxis DOL" (spec: `dev-notes/brief/tradeaxis_description.md`). Never copy that product's name or branding.
- The chart must LOOK like the user's screenshot (`dev-notes/brief/reference_look.png`):
  - a "Timeframe | Bias" table (D/4H/1H, BULLISH green, BEARISH red);
  - ONE dashed neon target zone with a glow core line, anchored left;
  - a dashed tether to a "Target: BEFVG / PoT: 70.1%" label;
  - dark-green iFVG boxes.
- The user wants it "100000X better", maximum effort, unlimited agents, and is willing to wait. Latest instructions, in order:
  1. Study every trading strategy and concept there is, with 1-2 agents per topic, then combine all the info.
  2. Go on with verify (resume the killed overhaul workflow).
  3. Implement the improvements, keep auditing until nothing new is found.
  4. **Paste the final script in ONE code block** in chat when done, and also send the .pine file.
- The user writes informally; they are a trader, not a programmer. Keep replies short and plain.

## Hard constraints
See `dev-notes/brief/CONTEXT.md`. In short:
- Must compile in Pine v6. No offline compiler exists, so be doc-grounded.
- Non-repainting: confirmed-bar structural logic; `request.security` with [1] + lookahead_on; never below the chart TF.
- No forward references.
- The Clean style must match the screenshot.
- Privacy: never put the user's email or name into external requests.

## Git rules
- Work only on branch `claude/determined-lovelace-erktyz`. Push with `git push -u origin claude/determined-lovelace-erktyz`.
- Draft PR: https://github.com/clipzfb02-crypto/m/pull/5. Keep its description up to date.
- Commit message trailer:
  ```
  Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
  Claude-Session: https://claude.ai/code/session_01LHSxJrY7ayMCWKn7R95Bj9
  ```
- No model identifiers in commits or PRs.

## Tooling
- Pine syntax checker (syntax only, no types): `dev-notes/tools/pine_parse.sh FILE [BASELINE]`.
  - It needs the pynescript venv: `python3 -m venv $SP/venv && $SP/venv/bin/pip install pynescript`, where SP is the scratchpad. Then fix the paths inside the scripts.
- Pine v6 docs mirrors: `git clone https://github.com/jabez4jc/pinescriptv6` and `https://github.com/mmmy/pine-script-doc-v6`. tradingview.com is blocked by the proxy.
- Workflow concurrency is 2 (4 CPUs).

## Status (2026-11-23)
1. **Shipped so far:** HEAD `00a405a` (2448 lines). It has the Clean style (default) plus Terminal, the Classic theme, and the fixes listed in the PR. The frozen copy of that version is the baseline for the audits.
2. **Overhaul round 1** (`dev-notes/workflows/dol-engine-overhaul-wf_97652ad5-f56.js`) was KILLED during Verify.
   - All 15 audits finished. Their 49 findings are in `dev-notes/runs/overhaul-r1-findings.md`; the raw results and exact patches are in `dev-notes/runs/overhaul-r1-journal.jsonl`.
   - The P1 findings:
     - the near-distance taper swaps the active target just before the hit;
     - out-of-range targets with PoT 0% can still be chosen;
     - the bias table is stale after a confirmed last bar;
     - HTF FVGs are dropped beyond 15 ATR;
     - key levels are demoted by weaker pools stacked beyond them;
     - relative EQ between key levels is missed;
     - swing CHoCH lags;
     - the legend shows 76 inputs (fix: `display = display.none`);
     - on the daily chart every candle becomes a PDH/PDL pool;
     - partial first-period PWH/PWL;
     - 4H/D charts in Day Trading mode show a warning and mislabelled rows.
   - Resume in the same session: `Workflow({scriptPath: <that script>, resumeFromRunId: 'wf_97652ad5-f56'})`. In a new session the cache is gone. Either re-run it, or hand-apply the verified patches from the journal.
3. **Study** (`dev-notes/workflows/dol-engine-study-wf_ff97c5ca-f34.js`, run `wf_ff97c5ca-f34`) is RUNNING.
   - 22 domain lenses, 2 agents each (researcher A, then researcher B verifies, extends and combines into `<key>.final.md`).
   - Then a completeness critic, synthesis into `STUDY.md`, a 3-judge panel (trader, quant, engineer) and `ROADMAP.md`.
   - Outputs are synced into `dev-notes/study/`.

4. **2026-11-23 22:10 UTC:** the study hit the account's 5-hour usage limit after researcher A had finished all 22 lenses plus 4 B passes.
   - It was resumed from cache once the limit reset (run `wf_ff97c5ca-f34`).
   - The usage limit is the main bottleneck. Expect pauses, and resume after the reset.
   - Headline findings so far (researchers B ran their own replications on local CME/BTC/SPX data):
     - **Distance and volatility explain almost all of "which pool is hit next".**
       - EQ, prominence and test counts add about 0 pp.
       - FVG and OB reach is about the same as a random level at the same distance.
     - **The raid → D mapping is wrong** (line ~1581). A rejected sweep shows no reversal edge, only a small continuation lean.
     - **The engine's displacement "quality" is not a positive target signal.** Make the array density pillar neutral.
     - **Breaker definition:** the `tookL` gate is too strict and reproduces only 11-24% of template breakers.
     - **Untouched opposing FVGs between price and a pool** cut reach by 2-3 pp. This is the only ICT path claim with support.
     - **Time:** the intraday and weekly volatility clock is the dominant timing effect, but the engine's σ and PoT are time-blind.
       - Session membership uses `time()` on bar open, which is wrong on 1H for NY AM.
       - The 10:00-11:00 ET hour is classed OFF-KZ.
     - **Midnight open** is the only time anchor with a measured excess revisit rate.
   - These point Round 2 toward: a learned volatility clock for PoT, honest neutral pillars, the shadow-ledger feature grading per chart, the breaker fix, and opposing-FVG path cost.

5. **2026-11-23 23:00 UTC:** the study then hit the account's WEEKLY usage limit, which reset on Nov 25 at 21:00 UTC.
   - At that point 30 of the 48 agent calls had finished: all 22 A passes plus 6 B passes.
   - On 2026-11-26 the user said "Try again" and "continue from exactly where we left". I resumed `wf_ff97c5ca-f34` from cache (task `wlb9fhedu`), so only the remaining B passes, the critic, the synthesis, the judges and the roadmap re-run.

## Next steps (in order)
1. When the study finishes, copy `STUDY.md` and `ROADMAP.md` into `dev-notes/study/` and add a pointer to them in `CONTEXT.md`. Commit and push.
2. Resume or re-run the overhaul (verify → plan → integrate → syntax gate → final review → fix). Then review the diff, run `pine_parse.sh` against the baseline, commit and push.
3. Round 2: implement the ROADMAP "now" items.
   - Proposals carry exact patches against the post-overhaul file; 3 independent verifiers each, kept on a 2-of-3 vote.
   - Integrate sequentially, then a syntax gate and a final review.
4. Loop-until-dry audit rounds: stop after two consecutive rounds find nothing new.
5. Update `README.md` and the PR description. Commit and push.
6. Paste the full final script in ONE code block in chat, and send the file.
