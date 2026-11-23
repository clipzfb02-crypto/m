export const meta = {
  name: 'dol-engine-study',
  description: 'Exhaustive study of every trading concept relevant to forecasting the next draw on liquidity: 22 domain lenses x 2 researchers (research, then verify+extend+combine), completeness-critic loop, synthesis into a knowledge base, 3-judge panel and a ranked roadmap',
  phases: [
    { title: 'Study', detail: '22 domain lenses, 2 agents each: researcher A, then researcher B verifies, fills gaps and combines' },
    { title: 'Gaps', detail: 'completeness critic finds uncovered domains; extra lenses until dry (max 2 rounds)' },
    { title: 'Synthesis', detail: 'merge into STUDY.md knowledge base + consolidated proposals' },
    { title: 'Judge', detail: 'trader / quant / engineer panel scores every proposal' },
    { title: 'Roadmap', detail: 'ranked, spec-level ROADMAP.md for implementation' },
  ],
}

const SP = '/tmp/claude-0/-home-user-m/7ce60006-3639-59b1-8cd3-87355409d58a/scratchpad'
const FILE = '/home/user/m/indicators/dol_engine.pine'
const BASE = `${SP}/brief/baseline_v2.pine`
const OUT = `${SP}/brief/study`

const ENGINE_MAP = `Engine map (line numbers in ${BASE}, identical to ${FILE}): header 1-29; INPUTS 40-310; TYPES 312-396; PURE HELPERS 398-610 (f_raceH first-passage, f_meter, ...); LEVEL METHODS 612-697; SERIES-STATE FUNCTIONS 699-870 (f_structure BOS/CHoCH, f_htfFvg, f_sessOpen, f_rangeTrack, f_sessTrack); SERIES 872-1018 (request.security MTF reads, ATR, killzones, volume profile feed); STATE 1020-1080; STATE HELPERS 1082-1500 (f_newLevel, f_mergeAt/f_mergeLiq EQH/EQL, f_anchorScan, f_pushExt registry, f_stackSide, f_ghost, f_bump/f_surv/f_empPoT/f_potModel empirical PoT, f_reachD, f_invalidation, f_raceAdj, f_calMult, f_profile, f_pathVol, f_openTrial/f_step/f_book ledger); LIVE SWEEP 1502-1514; ENGINE (confirmed bars) 1516-2058 (pivots, pools, FVG/OB/breaker, iFVG, registry, scoring pillars proximity/freshness/confluence/density/draw, multipliers, selection with hysteresis, ledger); LIVE READOUTS 2060-2076; ALERTS 2077-2094; RENDERING 2096-2287 (Clean + Terminal styles); TERMINAL PANEL 2289-2434; DATA WINDOW 2436+.`

const PRE = `CONTEXT. You are helping build the best open-source "Draw on Liquidity" (DOL) indicator for TradingView in Pine Script v6. Read ${SP}/brief/CONTEXT.md first (project brief, hard constraints, decision history) and ${SP}/brief/tradeaxis_description.md (the feature spec of the commercial product we match in features; never copy its branding). The current engine is ${BASE}. ${ENGINE_MAP} README with the user-facing description of what the engine does: /home/user/m/README.md (read it: it is the fastest way to learn the current design).

What the indicator does: it finds liquidity pools (BSL/SSL from swings, EQH/EQL, PDH/PDL, PWH/PWL, Asia/London/NY session highs/lows, STF/HTF pivots) and PD arrays (FVG, iFVG, order blocks, breakers, HTF FVG), scores each candidate (proximity, freshness, confluence, density, draw-vector alignment, multipliers), and selects ONE target the market is most likely to draw to next, with a Probability of Touch (PoT %), an accuracy ledger that measures its own hit rate against a random-level baseline, a multi-timeframe bias table, iFVG zones, LVN zones from a 1H volume profile, and a ghost trail. The core forecasting problem: "which liquidity will price reach next, and how likely within H bars?"`

const RULES = `RULES.
- READ-ONLY for ${FILE} and ${BASE}. Write files only under ${OUT}/.
- Web research tools: load them with ToolSearch, e.g. query "select:mcp__Firecrawl__firecrawl_search,mcp__Firecrawl__firecrawl_scrape". For academic papers (arXiv q-fin, SSRN mirrors) also try "select:mcp__Firecrawl__firecrawl_research_search_papers,mcp__Firecrawl__firecrawl_research_read_paper" and "WebSearch". tradingview.com is usually blocked by the proxy: use other sources (GitHub, blogs, books, papers, forum write-ups, YouTube transcript summaries).
- PRIVACY: search queries must be generic topic queries. Never put any personal information, repository names, or our product name into an external request.
- COPYRIGHT: learn concepts and algorithms from other people's scripts and writing; never copy their code or long passages verbatim.
- Be honest about evidence. Grade it: 'strong' (peer-reviewed or large replicated quantitative study), 'moderate' (published statistics/backtests with numbers, reproducible), 'weak' (practitioner consensus, anecdotal), 'none' (folklore/unfalsifiable). Quote numbers and give source URLs.
- Pine v6 feasibility matters: anything proposed must work within TradingView limits (no forward refs, request limits, loop time, drawing limits, max_bars_back) and keep the engine non-repainting (structural logic on barstate.isconfirmed; request.security with [1] offset + lookahead_on).
- Depth over breadth INSIDE your domain. Aim for roughly 15-40 searches/page reads. Prefer precise algorithmic definitions (parameters, edge cases, exact candle rules) over vague descriptions.`

const TASK = (key) => `YOUR DELIVERABLES.
1. Research your domain exhaustively: every concept and strategy in it that bears on WHERE price will go next (which liquidity gets taken), WHEN (timing), and HOW LIKELY. For each: a precise algorithmic definition (parameters, candle rules, edge cases), how practitioners use it to choose a target or bias, empirical evidence with numbers and URLs, and failure modes.
2. Gap analysis vs the engine: grep/read the relevant parts of ${BASE} and classify each concept as present / partial / missing / wrong (cite line numbers and what the engine does differently).
3. Proposals: concrete improvements to the engine from your domain (new level sources, better scoring/selection, better bias, better probability, UX, alerts). Each with an algorithm + Pine v6 implementation sketch (inputs, state, where in the code), expected value to a trader, evidence grade, risk, effort. Prefer improvements whose value the engine's own accuracy ledger can measure. Maximum 10 proposals, best first. Do not propose things the engine already does well.
4. Write a detailed markdown report to ${OUT}/${key}.md (sections: Concepts (definitions + parameters), Evidence (numbers + sources), Engine gap analysis (line refs), Proposals (spec-level), Sources). Make it self-contained: later agents will read it instead of redoing your research.
5. Return the structured output (it must agree with the report).`

const STUDY = {
  type: 'object',
  properties: {
    summary: { type: 'string', description: '5-12 sentences: the most important insights for the forecasting problem' },
    report: { type: 'string', description: 'path of the markdown report you wrote' },
    concepts: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          name: { type: 'string' },
          definition: { type: 'string', description: 'precise, algorithmic' },
          dolRole: { type: 'string', description: 'how it helps predict which liquidity is taken next / timing / probability' },
          evidence: { type: 'string', enum: ['strong', 'moderate', 'weak', 'none'] },
          evidenceNotes: { type: 'string' },
          engineStatus: { type: 'string', enum: ['present', 'partial', 'missing', 'wrong', 'n/a'] },
          engineNotes: { type: 'string', description: 'line refs + what differs' },
        },
        required: ['name', 'definition', 'dolRole', 'evidence', 'engineStatus'],
      },
    },
    proposals: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          id: { type: 'string', description: 'prefixed with the lens key' },
          title: { type: 'string' },
          category: { type: 'string', enum: ['target-selection', 'scoring', 'level-source', 'bias', 'probability', 'statistics-ledger', 'visual-ux', 'alerts', 'performance', 'robustness', 'other'] },
          priority: { type: 'string', enum: ['P1', 'P2', 'P3'] },
          rationale: { type: 'string' },
          evidence: { type: 'string', enum: ['strong', 'moderate', 'weak', 'none'] },
          spec: { type: 'string', description: 'algorithm, parameters, inputs, state, where in the code, Pine v6 approach' },
          risk: { type: 'string' },
          effort: { type: 'string', enum: ['S', 'M', 'L'] },
        },
        required: ['id', 'title', 'category', 'priority', 'rationale', 'evidence', 'spec', 'risk', 'effort'],
      },
    },
  },
  required: ['summary', 'report', 'concepts', 'proposals'],
}

const LENSES = [
  { key: 'ict_liq', title: 'ICT liquidity theory', prompt: `DOMAIN: ICT LIQUIDITY THEORY (Inner Circle Trader). Buy-side / sell-side liquidity; external vs internal range liquidity (ERL/IRL) and the "IRL to ERL / ERL to IRL" delivery cycle; equal highs/lows and RELATIVE equal highs/lows; old highs/lows; trendline liquidity; inducement; stop runs vs true breakouts; liquidity voids / runs; "low-hanging fruit" vs "major" liquidity; how ICT says to choose the draw on liquidity (HTF PD arrays, the weekly/daily candle, "where is price likely to go"); liquidity taken -> reversal vs continuation; how deep beyond a level stops sit; when a pool is "spent".` },
  { key: 'ict_pd', title: 'ICT PD arrays', prompt: `DOMAIN: ICT PD ARRAY MATRIX. Premium/discount and equilibrium; the PD array hierarchy (old highs/lows, rejection block, bearish/bullish order block, FVG (BISI/SIBI), liquidity void, breaker, mitigation block, propulsion block, vacuum block, volume imbalance, opening gaps NWOG/NDOG, balanced price range BPR, consequent encroachment, mean threshold); inversion FVGs; which arrays act as TARGETS vs ENTRY zones; exact candle rules for each; how ICT ranks them for draw; HTF arrays as magnets; how a gap is "filled", "respected" or "disrespected".` },
  { key: 'ict_time', title: 'ICT time and price', prompt: `DOMAIN: ICT TIME & PRICE. Killzones (Asia, London, NY AM, NY lunch, NY PM, London close) in exact NY times; algorithmic macros (e.g. 09:50-10:10, 10:50-11:10, 13:10-13:40, 15:15-15:45); Silver Bullet windows; Power of 3 / AMD (accumulation-manipulation-distribution); Judas swing; midnight open and true day open; NY 8:30 / 9:30 opens; CBDR, Asian range and Flout with standard-deviation projections; daily and weekly profiles (e.g. "Tuesday low of week", "Wednesday reversal"); IPDA data ranges (20/40/60 trading days lookback/lookforward); quarterly shifts; seasonal tendencies. Which of these change the PROBABILITY or TIMING of a level being taken, and how could the engine use them (killzone affinity, time-of-day PoT adjustment, day-of-week priors, IPDA range levels as targets).` },
  { key: 'ict_struct', title: 'ICT structure and execution models', prompt: `DOMAIN: ICT MARKET STRUCTURE AND MODELS. Swing points (3-candle vs N-candle fractals); short/intermediate/long-term highs and lows (ICT's STH/ITH/LTH); market structure shift (MSS) vs BOS vs CHoCH; displacement (definitions: body size vs ATR, FVG creation); dealing range definition and its premium/discount; market maker buy/sell models (original consolidation, smart money reversal, re-accumulation); turtle soup; OTE (62-79%); the "2022 mentorship model" (sweep -> displacement/MSS -> FVG -> target opposing liquidity); intermediate-term high/low as targets. How each model implies the NEXT draw on liquidity, and how the engine's bias and draw vector should reflect it.` },
  { key: 'bias_dol', title: 'Bias and next-draw forecasting methods', prompt: `DOMAIN: FORECASTING THE NEXT DRAW (bias methods). This is the core forecasting problem. Survey every method practitioners and researchers use to decide whether the next session/day/week will take buy-side or sell-side liquidity: ICT daily bias (previous day closed above/below a PD array, "close through PDH -> PDH+ next"), Candle Range Theory (CRT: candle 1 range, candle 2 sweeps and closes back inside -> candle 3 targets the opposite side), previous-candle high/low "taken next candle" statistics on D/W/4H, weekly profile templates, order-flow based bias (HTF closes, displacement direction), dealing-range position, open-relative bias (price vs midnight open / weekly open), momentum vs mean reversion, liquidity-sweep-then-reverse vs breakout-continuation statistics. Find any published hit-rate statistics (e.g. "PDH or PDL is taken X% of days", "both taken Y%", "inside day Z%", "previous candle high taken after close above it"). Translate the best ones into an engine design for the draw vector D and the selection's side choice.` },
  { key: 'smc_impl', title: 'Open-source SMC implementations', prompt: `DOMAIN: OPEN-SOURCE SMC / LIQUIDITY PINE IMPLEMENTATIONS. Study how well-known open-source scripts and libraries define and code these things (find their source on GitHub mirrors or descriptions): Smart Money Concepts (internal vs swing structure, strong/weak highs, OB detection and mitigation methods, EQH/EQL thresholds), liquidity swings / liquidity sweeps indicators, buyside/sellside liquidity indicators, ICT killzones & pivots indicators, FVG indicators with mitigation modes, iFVG indicators, breaker indicators, volume profile/LVN scripts, market-structure (BOS/CHoCH) scripts with body vs wick confirmation. Extract the best ALGORITHMIC conventions and parameter defaults, edge-case handling, drawing-management tricks, and performance patterns. Compare with our engine and propose concrete improvements. Never copy code.` },
  { key: 'competitors', title: 'Competitive landscape of DOL/liquidity tools', prompt: `DOMAIN: COMPETITIVE LANDSCAPE. Survey commercial and free TradingView (and other platform) tools around liquidity / draw on liquidity / targets: their public descriptions, feature lists, UI conventions, what users praise or complain about in reviews/comments/forums (e.g. clutter, repainting, lag, wrong targets), alert designs, dashboards, probability displays. Identify features that "best in the world" tools have and we lack, and UI/UX conventions traders expect (legend cleanliness, tooltips, colors, labels, toggles). Propose the most valuable additions. Use public descriptions only; never copy branding or code.` },
  { key: 'wyckoff_sd', title: 'Wyckoff and supply/demand', prompt: `DOMAIN: WYCKOFF METHOD AND SUPPLY/DEMAND. Accumulation/distribution schematics (PS, SC/BC, AR, ST, Spring/UTAD, test, SOS/SOW, LPS/LPSY), springs and upthrusts as liquidity grabs, composite operator, cause and effect (point-and-figure count targets), effort vs result (volume), trading-range liquidity; supply/demand zones (fresh vs tested, departure strength, time at level). Which parts help predict the next draw (e.g. spring -> target the opposite side of the range; failed breakout statistics) and how to detect them algorithmically in Pine.` },
  { key: 'amt_profile', title: 'Auction market theory and profiles', prompt: `DOMAIN: AUCTION MARKET THEORY, MARKET PROFILE, VOLUME PROFILE. Value area (VAH/VAL), POC, naked/virgin POCs as magnets, HVN/LVN behaviour (price moves fast through LVNs, stalls at HVNs), single prints, poor highs/lows and unfinished auctions (strong magnets), excess, initial balance and IB extension statistics, open types (Dalton: open-drive, open-test-drive, open-rejection-reverse, open-auction), 80% rule, balance vs imbalance, composite profiles, developing value migration. Find statistics (e.g. how often naked POCs get revisited, poor highs repaired, IB broken). Propose how the engine should use them (new level sources such as poor highs/lows and naked POCs; LVN path cost; value-area-based bias), feasible with request.security_lower_tf and limited arrays.` },
  { key: 'orderflow_micro', title: 'Order flow and microstructure of stops', prompt: `DOMAIN: ORDER FLOW AND MARKET MICROSTRUCTURE OF LIQUIDITY. Where stop-loss and take-profit orders cluster (Osler's work on FX stop/limit clustering at round numbers and beyond prior highs/lows; price cascades when stops trigger), stop-hunting evidence, liquidity provision and absorption, iceberg/limit liquidity at extremes, the distance beyond a swing where stops sit (ticks vs ATR), how pool size grows with time and number of touches, how pools decay after being swept, crypto liquidation levels (leverage-implied liquidation clusters, liquidation heatmaps), delta/footprint signatures of a sweep (absorption, exhaustion). Turn this into a better pool-SIZE model and sweep definition for the engine (depth of the zone beyond the level, round-number bonus, touch-count growth, sweep vs breakout classification).` },
  { key: 'academic_sr', title: 'Academic evidence on support/resistance and levels', prompt: `DOMAIN: ACADEMIC EVIDENCE ON PRICE LEVELS. Find and summarise peer-reviewed / arXiv / SSRN studies on: support and resistance (e.g. Osler "Support for resistance"; Garzarelli et al. "Memory effects in stock price dynamics: evidence of technical trading"; Chung & Bellotti on S/R in time series), round-number effects, prior-high/low breakouts, 52-week high anchoring, stop-loss cascades, intraday high/low timing (when the daily high/low forms), probability that previous day's high/low is exceeded, breakout vs bounce probabilities as a function of number of touches and time since formation. Extract quantified effects usable as PRIORS in the engine's scoring (e.g. bounce vs penetration probability vs touches; level memory decay). Propose how to encode them.` },
  { key: 'quant_pot', title: 'Probability of touch and volatility modelling', prompt: `DOMAIN: QUANT PROBABILITY OF TOUCH. First-passage/barrier-hit probability for Brownian motion with drift (closed form, reflection principle), two-barrier (race) probabilities, discrete-monitoring corrections (Broadie-Glasserman-Kou continuity correction shift 0.5826*sigma*sqrt(dt)), fat tails and jump effects, volatility estimators from OHLC (Parkinson, Garman-Klass, Rogers-Satchell, Yang-Zhang) and their efficiency, intraday volatility seasonality (U-shape) and how to scale the horizon in "volatility time", volatility clustering (EWMA/GARCH-lite in Pine), empirical MFE/MAE distributions, Bayesian blending of model and empirical rates, calibration of touch probabilities. Audit the engine's PoT (f_raceH, f_bump/f_surv/f_empPoT/f_potModel, the 95% cap) for mathematical correctness and propose concrete upgrades with formulas.` },
  { key: 'quant_regime', title: 'Regime detection: trend vs mean reversion', prompt: `DOMAIN: REGIME DETECTION. Trend vs range vs breakout regimes and how they change WHICH liquidity is taken (in trends, opposite-side liquidity holds and the draw continues; in ranges, both sides get raided). Methods: Hurst exponent, variance ratio, Kaufman efficiency ratio, ADX/DMI, choppiness index, realised vs implied vol ratio, volatility compression (NR4/NR7, Bollinger squeeze) before expansion, time-series momentum (Moskowitz et al.) and short-term reversal evidence across asset classes and horizons. Propose a robust, cheap regime classifier for Pine and exactly how it should modulate the draw vector, PoT drift, counter-draw logic and the EQ/pool scoring.` },
  { key: 'calib_ml', title: 'Scoring, online learning and calibration', prompt: `DOMAIN: SCORING, ONLINE LEARNING AND CALIBRATION. The engine combines pillars with hand-set weights and an adaptive calibration from its ledger. Study: online logistic regression / SGD, naive Bayes, Bayesian updating with Beta priors, Elo/Glicko-like ranking, kNN approaches used in Pine (e.g. Lorentzian-distance classifiers), learning-to-rank for "which candidate is hit first", proper scoring rules (Brier, log loss), reliability diagrams, isotonic/Platt calibration, avoiding look-ahead and overfitting in online learning, minimum-sample shrinkage, baselines (random level at same distance, nearest level, opposite level). Design a concrete, leak-free online learner in Pine v6 (arrays/matrices) that learns pillar weights or per-family hit rates from the ledger and calibrates PoT, with shrinkage toward the hand-set prior. Audit f_calMult / the ledger for statistical soundness.` },
  { key: 'session_stats', title: 'Session, day and week statistics', prompt: `DOMAIN: SESSION / DAY / WEEK STATISTICS. Find published or reproducible statistics for major markets (ES/NQ futures, EURUSD/GBPUSD, gold, BTC): probability PDH and/or PDL is taken during the next day; by which session (Asia/London/NY) the daily high/low forms; Asia range breaks and which side; London high/low taken in NY; opening range breakout (Crabel) and initial balance extension rates; day-of-week distribution of the weekly high/low; inside days/NR7 follow-through; average daily range (ADR) completion and its use as a reach cap; gap fill statistics (overnight gaps, weekend gaps). Turn the most robust ones into priors for the engine (e.g. time-of-day dependent PoT, session-level target priors, ADR-remaining cap).` },
  { key: 'classic_levels', title: 'Classic reference levels', prompt: `DOMAIN: CLASSIC REFERENCE LEVELS AS LIQUIDITY. Floor pivots, Camarilla, Fibonacci pivots; round numbers / psychological levels (00/50, quarter levels) per asset; VWAP, anchored VWAP (from session/week/swing) and deviation bands; weekly/monthly/quarterly/yearly opens and previous month/quarter/year highs and lows; all-time / 52-week highs; previous settlement; opening gaps; "naked" levels never revisited. Which have evidence of acting as magnets/targets, and which are worth adding as level sources or confluence anchors in the engine (cost vs value, request budget).` },
  { key: 'price_action', title: 'Price action, magnets and projections', prompt: `DOMAIN: PRICE ACTION TARGETING AND PROJECTIONS. Al Brooks concepts (magnets, measured moves, breakout tests, failed breakouts, trading range vs trend, "always in" direction, second entries), measured-move and leg-equality targets (AB=CD), Fibonacci extensions used as targets (-0.27, -0.618, -1, -2 standard deviations in ICT), swing projection from displacement legs, Elliott/harmonic target heuristics (evaluate honestly), Dow theory. Which projection methods have measurable predictive value for "how far will this leg go" and could inform reachability or add target candidates in the engine.` },
  { key: 'smt_inter', title: 'SMT divergence and intermarket', prompt: `DOMAIN: SMT DIVERGENCE AND INTERMARKET ANALYSIS. ICT SMT divergence (correlated pairs: ES/NQ/YM, EURUSD/GBPUSD vs DXY, gold/silver, BTC/ETH): exact definition (one makes a higher high, the other fails), timeframes, how it signals that a liquidity sweep is a reversal; evidence; inverse correlation handling (DXY). Design an optional SMT module for the engine (user picks the comparison symbol; request.security with [1]/lookahead_on; pivot comparison at sweep time) and how it should feed the draw vector and the sweep-reversal vs continuation classification. Consider request budget and repainting.` },
  { key: 'asset_specific', title: 'Asset-class specifics, sessions and events', prompt: `DOMAIN: ASSET-CLASS SPECIFICS. Session definitions and time zones for index futures (CME RTH/ETH, 18:00 NY day start), FX (Sunday open, 17:00 NY rollover), gold, crypto (24/7, weekends, UTC daily close, funding times), equities (RTH, pre/post market, gaps), holidays and half days. How the engine's PDH/PDL, PWH/PWL, session tracking, killzones and "midnight open" should adapt per asset (syminfo.type, syminfo.session, syminfo.timezone, session.extended), and what breaks today on these assets (e.g. daily chart behaviour, weekend gaps, crypto weeks). High-impact news times (8:30 NY data, FOMC 14:00) and their effect on liquidity runs. Propose robust handling.` },
  { key: 'trade_mgmt', title: 'How traders use a DOL in trades', prompt: `DOMAIN: TRADE EXECUTION AROUND A DRAW ON LIQUIDITY. Entry models that target a DOL (sweep of opposing liquidity -> MSS -> FVG/OB entry -> target DOL; iFVG continuation; breaker retest), where to place invalidation (beyond the sweep extreme, beyond the opposing pool), partials at intermediate liquidity, R:R and expectancy computation, MFE/MAE, time stops. What information a trader needs on the chart at decision time (target, probability, invalidation, R:R, ETA, intermediate obstacles), what alerts are actionable. Audit the engine's invalidation, R:R, WIN<=H race, EV and ETA logic, and propose improvements (e.g. "next obstacle" levels between price and target, entry-zone highlighting, alert payloads).` },
  { key: 'pine_eng', title: 'Pine v6 engineering excellence', prompt: `DOMAIN: PINE SCRIPT v6 ENGINEERING. Use the local docs (${SP}/docsrc/jabez4jc_pinescriptv6/ and ${SP}/docsrc/mmmy_pine-script-doc-v6/) plus web sources. Topics: v6 changes (dynamic requests, enums, strict bools, text formatting, input display/active parameters), performance (profiling, var vs varip, array/map/matrix costs, loops, drawing reuse vs recreate, polylines), request.security / security_lower_tf pitfalls and the [1]+lookahead_on idiom, max_bars_back, historical vs realtime execution and rollback, barstate.* semantics, drawing limits, table performance, alert() vs alertcondition, input organisation (group, inline, tooltip, display = display.none to keep the status line clean, active = to grey out unused inputs). Audit the engine for engineering issues and opportunities; propose concrete improvements (with doc quotes for compile-relevant claims).` },
  { key: 'ux_design', title: 'Premium indicator UX and visual design', prompt: `DOMAIN: PREMIUM INDICATOR UX / VISUAL DESIGN on TradingView. What makes an overlay indicator look premium and readable: legend/status-line cleanliness, minimal but informative labels, typography sizes, contrast on dark AND light chart themes (chart.bg_color / chart.fg_color), colour semantics (buy-side vs sell-side), glow effects with layered lines, box transparency, avoiding clutter (number of objects), label collision with price, right-edge offsets, tooltips for detail, table design, sensible defaults, input UX (groups, tooltips, inline). Open ${SP}/brief/reference_look.png with the Read tool and compare with the engine's Clean style rendering code (RENDERING section). Propose concrete visual/UX improvements that keep the Clean style matching the reference.` },
  { key: 'skeptic', title: 'Evidence skeptic and evaluation design', prompt: `DOMAIN: SKEPTICAL EVALUATION. Which ICT/SMC/liquidity claims have empirical support and which are folklore or unfalsifiable? Review any quantitative tests of ICT/SMC concepts (FVG fill rates, order block reaction rates, liquidity sweep reversal rates, killzone effects), the base rates a naive model achieves (e.g. nearest level is touched first most of the time; random-walk touch probabilities), survivorship and look-ahead traps in indicator "accuracy" claims, multiple-testing/overfitting in adaptive weights. Audit the engine's ledger, EDGE z-score, random-level baseline and calibration for honesty and statistical validity. Propose evaluation and design changes so the engine's claims are honest and its choices beat strong baselines (not just random).` },
]

function lensPrompt(l) {
  return `${PRE}\n\n${RULES}\n\n${l.prompt}\n\n${TASK(l.key)}`
}

function deepenPrompt(l, a) {
  return `${PRE}\n\n${RULES}\n\n${l.prompt}\n\nYOU ARE RESEARCHER B (the second agent on this domain). Researcher A already studied it and wrote ${OUT}/${l.key}.md; A's structured result is below. Your job is to make this domain's study as complete and correct as humanly possible, then COMBINE both into one final report:\n1. VERIFY A: re-check A's definitions, parameters, numbers and sources (open the sources; search again). Correct anything wrong or overstated; downgrade evidence grades that are not supported.\n2. FILL GAPS: research independently from a different angle (other schools/authors, primary sources, academic papers, open-source implementations, statistics/backtests with numbers). Add every important concept, edge case, statistic and source A missed.\n3. RE-CHECK the engine gap analysis against ${BASE} (line refs) and fix mistakes.\n4. IMPROVE PROPOSALS: sharpen specs (exact algorithms, defaults, Pine v6 approach, where in the code), drop weak ones, add better ones (max 12, best first).\n5. Write the COMBINED final report to ${OUT}/${l.key}.final.md (A + B merged and corrected, self-contained; same section layout: Concepts, Evidence, Engine gap analysis, Proposals, Sources; mark what you corrected). Return the combined structured output (same schema; report = the .final.md path).\n\nRESEARCHER A RESULT (JSON):\n${JSON.stringify(a)}`
}

async function runStudy(lenses, phaseName) {
  // Researcher A per lens (unchanged prompts so earlier finished calls stay cached)
  const firstPass = await parallel(lenses.map(l => () =>
    agent(lensPrompt(l), { label: `study:${l.key}`, phase: phaseName, schema: STUDY })
      .then(r => r ? { key: l.key, title: l.title, ...r } : null)))
  // Researcher B per lens: verify, fill gaps, combine A+B into <key>.final.md
  const second = await parallel(lenses.map((l, i) => () => {
    const a = firstPass[i]
    if (!a) return agent(lensPrompt(l).replace(`${OUT}/${l.key}.md`, `${OUT}/${l.key}.final.md`), { label: `study2:${l.key}`, phase: phaseName, schema: STUDY })
      .then(r => r ? { key: l.key, title: l.title, ...r } : null)
    return agent(deepenPrompt(l, a), { label: `deepen:${l.key}`, phase: phaseName, schema: STUDY })
      .then(r => r ? { key: l.key, title: l.title, ...r } : a)
  }))
  return second.map((r, i) => r || firstPass[i]).filter(Boolean)
}

phase('Study')
log(`Launching ${LENSES.length} study lenses`)
const studies = await runStudy(LENSES, 'Study')
log(`${studies.length}/${LENSES.length} lenses returned; ${studies.reduce((a, s) => a + s.concepts.length, 0)} concepts, ${studies.reduce((a, s) => a + s.proposals.length, 0)} proposals`)

// Completeness critic, loop until dry (max 2 extra rounds)
const GAPS = {
  type: 'object',
  properties: {
    complete: { type: 'boolean' },
    reasoning: { type: 'string' },
    extraLenses: {
      type: 'array',
      items: {
        type: 'object',
        properties: { key: { type: 'string' }, title: { type: 'string' }, prompt: { type: 'string', description: 'DOMAIN: ... paragraph in the same style as the existing lenses' } },
        required: ['key', 'title', 'prompt'],
      },
    },
  },
  required: ['complete', 'reasoning', 'extraLenses'],
}
phase('Gaps')
const covered = () => studies.map(s => `- ${s.key} (${s.title}): ${s.concepts.map(c => c.name).join('; ')}`).join('\n')
for (let round = 1; round <= 2; round++) {
  const g = await agent(`${PRE}\n\nYou are the COMPLETENESS CRITIC for a research study whose goal is to cover EVERY trading strategy and concept known that could help forecast which liquidity price reaches next, when, and how likely (plus everything needed to present it superbly in a TradingView indicator). The study lenses run so far and the concepts each covered:\n${covered()}\n\nThe reports are in ${OUT}/*.md (skim them as needed). Find important domains, strategies or concepts that are still NOT covered or only superficially covered (think broadly: other trading schools, statistical methods, market microstructure, behavioural finance, options-market positioning such as gamma/max-pain/open-interest levels if feasible from TradingView data, COT, seasonality, news, data-quality issues, multi-asset handling, UX, alerts, etc.). Only propose a lens if it could plausibly change the engine's design or the trader's experience. Return up to 6 extra lenses (keys must be new, snake_case, prefixed 'x${round}_'), or complete=true with an empty list if coverage is sufficient.`, { label: `critic:round${round}`, phase: 'Gaps', schema: GAPS })
  if (!g || g.complete || !g.extraLenses || g.extraLenses.length === 0) { log(`Critic round ${round}: coverage complete`); break }
  const fresh = g.extraLenses.filter(x => !studies.some(s => s.key === x.key)).slice(0, 6)
  log(`Critic round ${round}: ${fresh.length} extra lenses: ${fresh.map(x => x.key).join(', ')}`)
  const extra = await runStudy(fresh, 'Gaps')
  studies.push(...extra)
}

// Synthesis
phase('Synthesis')
const allProposals = studies.flatMap(s => s.proposals.map(p => ({ ...p, lens: s.key })))
const CONSOLIDATED = {
  type: 'object',
  properties: {
    studyFile: { type: 'string' },
    proposals: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          id: { type: 'string', description: 'C01, C02, ...' },
          title: { type: 'string' },
          category: { type: 'string' },
          mergedFrom: { type: 'array', items: { type: 'string' } },
          description: { type: 'string', description: 'what and why, with the evidence' },
          spec: { type: 'string', description: 'merged algorithm + Pine approach + where in code' },
          evidence: { type: 'string', enum: ['strong', 'moderate', 'weak', 'none'] },
          effort: { type: 'string', enum: ['S', 'M', 'L'] },
          conflicts: { type: 'string', description: 'conflicts with other proposals or with the decision history, if any' },
        },
        required: ['id', 'title', 'category', 'mergedFrom', 'description', 'spec', 'evidence', 'effort'],
      },
    },
  },
  required: ['studyFile', 'proposals'],
}
const synth = await agent(`${PRE}\n\nYou are the SYNTHESIZER. ${studies.length} research lenses were each studied by TWO agents (researcher A wrote ${OUT}/<key>.md; researcher B verified, extended and combined both into ${OUT}/<key>.final.md). Keys: ${studies.map(s => s.key).join(', ')}. Read ALL the .final.md reports (fall back to <key>.md where no .final.md exists), and consult the A reports where the final one is thin.\n\nTask 1: write ${SP}/brief/STUDY.md, the definitive knowledge base for every later agent working on this indicator. Organise by theme (Liquidity & pools; PD arrays; Structure & bias; Time & sessions; Auction/volume; Microstructure; Probability & volatility; Regime; Statistics & calibration; Classic levels; Intermarket; Asset specifics; Execution; Pine engineering; UX; Evidence & honesty). For every concept: precise algorithmic definition with parameters, its role in forecasting the draw, evidence grade with key numbers + source, and the engine's status (present/partial/missing/wrong + line refs). Then a section "Key quantitative priors" (all usable numbers in one table) and "Top insights". Be dense and precise, 40-90 KB.\n\nTask 2: consolidate the ${allProposals.length} raw proposals below into a deduplicated list (merge overlapping ones, keep the best spec details from each, note conflicts with each other or with the decision history in CONTEXT.md). Drop proposals the engine already does well.\n\nRAW PROPOSALS (JSON):\n${JSON.stringify(allProposals)}`, { label: 'synthesize', phase: 'Synthesis', schema: CONSOLIDATED })
if (!synth) return { error: 'synthesis failed', studies: studies.map(s => ({ key: s.key, summary: s.summary })) }
log(`Synthesis: ${synth.proposals.length} consolidated proposals`)

// Judge panel
phase('Judge')
const SCORES = {
  type: 'object',
  properties: {
    scores: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          id: { type: 'string' },
          value: { type: 'integer', description: '0-10 benefit from this judge\'s perspective' },
          risk: { type: 'integer', description: '0-10 risk/cost from this judge\'s perspective (10 = very risky)' },
          verdict: { type: 'string', enum: ['now', 'later', 'reject'] },
          note: { type: 'string' },
        },
        required: ['id', 'value', 'risk', 'verdict', 'note'],
      },
    },
    topPicks: { type: 'array', items: { type: 'string' } },
  },
  required: ['scores', 'topPicks'],
}
const JUDGES = [
  { key: 'trader', lens: 'an elite discretionary ICT/SMC trader who uses this indicator live on futures, FX, gold and crypto. Judge: does it make the target more correct and more useful in real decisions, does it reduce noise and jumping, does it look premium, would you pay for it' },
  { key: 'quant', lens: 'a quantitative researcher. Judge: evidence quality, statistical soundness, measurability by the engine\'s ledger, overfitting/look-ahead risk, whether it beats strong baselines' },
  { key: 'engineer', lens: 'a senior Pine Script v6 engineer responsible for shipping it. Judge: compile risk, repaint risk, runtime limits (loop time, request count, drawings), interaction with existing code, effort, maintainability' },
]
const judged = await parallel(JUDGES.map(j => () =>
  agent(`${PRE}\n\nYou are a JUDGE: ${j.lens}. Read ${SP}/brief/STUDY.md (knowledge base) and look at the engine where needed. Score EVERY consolidated proposal below (value 0-10, risk 0-10, verdict now/later/reject, one-line note). 'now' means: implement in the next round. Then list your top picks in order.\n\nPROPOSALS (JSON):\n${JSON.stringify(synth.proposals)}`, { label: `judge:${j.key}`, phase: 'Judge', schema: SCORES })
    .then(r => r ? { judge: j.key, ...r } : null)))
const judges = judged.filter(Boolean)

// Roadmap
phase('Roadmap')
const ROADMAP = {
  type: 'object',
  properties: {
    roadmapFile: { type: 'string' },
    now: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          rank: { type: 'integer' },
          id: { type: 'string' },
          title: { type: 'string' },
          spec: { type: 'string', description: 'implementation-ready: algorithm, parameters/defaults, new inputs (with groups/tooltips), state, exact code areas (line ranges), interactions, how to verify' },
          acceptance: { type: 'string' },
        },
        required: ['rank', 'id', 'title', 'spec', 'acceptance'],
      },
    },
    later: { type: 'array', items: { type: 'string' } },
    rejected: { type: 'array', items: { type: 'string' } },
    summary: { type: 'string' },
  },
  required: ['roadmapFile', 'now', 'later', 'rejected', 'summary'],
}
const roadmap = await agent(`${PRE}\n\nYou are the ROADMAP ARCHITECT. Inputs: the knowledge base ${SP}/brief/STUDY.md, the consolidated proposals and the three judges' scores below. Build the implementation roadmap for the next round. Rank by (trader value x evidence) / risk, honouring hard vetoes (any judge 'reject' with risk >= 8 needs a strong reason to keep). Pick the 'now' set so that together they make the indicator dramatically better while staying compile-safe and fast: typically 12-25 items, ordered so foundational changes come first. For each 'now' item write an implementation-ready spec grounded in the actual code (read ${BASE}; give line ranges, exact functions to change, new inputs with defaults/groups/tooltips, state, edge cases, and how to verify). Note that a separate bug-fix overhaul (findings listed in ${SP}/brief/CONTEXT.md decision history and the earlier audit) runs before this roadmap, so avoid duplicating pure bug fixes; focus on capability and quality upgrades. Write ${SP}/brief/ROADMAP.md (full specs, plus 'later' and 'rejected' with reasons) and return the structured output.\n\nCONSOLIDATED PROPOSALS (JSON):\n${JSON.stringify(synth.proposals)}\n\nJUDGE SCORES (JSON):\n${JSON.stringify(judges)}`, { label: 'roadmap', phase: 'Roadmap', schema: ROADMAP })

return {
  lenses: studies.map(s => ({ key: s.key, title: s.title, summary: s.summary, nConcepts: s.concepts.length, nProposals: s.proposals.length })),
  consolidated: synth.proposals.map(p => `${p.id} [${p.category}/${p.evidence}/${p.effort}] ${p.title}`),
  judges: judges.map(j => ({ judge: j.judge, topPicks: j.topPicks })),
  roadmap,
}
