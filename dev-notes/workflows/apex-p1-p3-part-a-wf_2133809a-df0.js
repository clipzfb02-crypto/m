export const meta = {
  name: 'apex-p1-p3-part-a',
  description: 'APEX ULTIMATE Phases 1-3 (part A): workspace inspection, then knowledge-atlas docs 01-08,16,17 by specialist roles with red-team fact-check, plus the validation data lab',
  phases: [
    { title: 'Inspect', detail: 'Phase 1: inventory of all earlier projects and the DOL Engine v2 lineage' },
    { title: 'Research', detail: 'Phase 2-3: specialist writers produce atlas documents' },
    { title: 'Red-team', detail: 'R10 fact-checks, math-checks and corrects every document' },
  ],
}

const SP = '/tmp/claude-0/-home-user-m/7ce60006-3639-59b1-8cd3-87355409d58a/scratchpad'
const REPO = '/home/user/m'
const APEX = `${REPO}/apex`
const KB = `${APEX}/MARKET_KNOWLEDGE_BASE`
const RES = `${APEX}/research`
const STUDY = `${SP}/brief/study`
const SPEC = `${REPO}/dev-notes/brief/APEX_ULTIMATE_SPEC.md`
const DOCS = `${SP}/docsrc/jabez4jc_pinescriptv6 and ${SP}/docsrc/mmmy_pine-script-doc-v6`
const DATA = `${APEX}/validation/data`

const PRE = `PROJECT. You are one specialist on the APEX ULTIMATE team. The team is building an honest, evidence-based, universal Draw-on-Liquidity (DOL) and quantitative market-intelligence indicator for TradingView in Pine Script v6.
- GOVERNING REQUIREMENTS: ${SPEC}. Read it in full first: sections 0-2, your domain's sections, and 20-25.
- EXISTING PRODUCT (preserve what is valuable): DOL Engine v2 at ${REPO}/indicators/dol_engine.pine. Its frozen copy is ${SP}/brief/baseline_v2.pine; a separate bug-fix pass may be editing the live file, so cite line numbers from the frozen copy. Also read the user-facing design in ${REPO}/README.md and the brief in ${SP}/brief/CONTEXT.md.
- EARLIER PROJECTS by the same user: ${APEX}/legacy/ (see its README.md). If ${RES}/WORKSPACE_INSPECTION.md exists, read it.
- COMPLETED RESEARCH STUDY: combined per-domain reports in ${STUDY}/<key>.final.md. Many contain replications on real futures and crypto data, with test scripts in ${STUDY}/<key>*_tools/. Keys: ict_liq, ict_pd, ict_time, ict_struct, bias_dol, smc_impl, competitors, wyckoff_sd, amt_profile, orderflow_micro, academic_sr, quant_pot, quant_regime, calib_ml, session_stats, classic_levels, price_action, smt_inter, asset_specific, trade_mgmt, pine_eng, ux_design, skeptic, and the gap lenses x1_positioning, x1_internals, x1_tv_validation, x1_retail_schools, x1_behavioral, x1_implied_vol (some x1 reports may still be in progress; use what exists). ${SP}/brief/STUDY.md is the synthesis, if present.
- Pine v6 docs mirrors: ${DOCS}.`

const HONESTY = `HONESTY RULES (non-negotiable):
- Never fabricate sources, statistics, backtest results, order-flow data or institutional intent.
  - Cite only sources you opened in this session or that a study report verified; say which.
  - Mark anything you could not verify as "unverified".
  - Quote study replication numbers with their sample size and dataset.
- Classify every concept as:
  - E = established market mechanics or exchange documentation;
  - A = academic or statistical evidence;
  - D = discretionary practitioner theory;
  - C = contested or unsupported by tests.
  Give an evidence grade: strong, moderate, weak or none.
- Scores are not probabilities. Never call anything a probability unless it is an empirically calibrated outcome frequency with a defined target, sample and horizon.
- Web access may be rate-limited. Prefer the study reports, the local docs mirror and primary sources you can fetch. Search queries must be generic: never include the user's name, email or repository, or any product name.
- Concepts only: never copy any proprietary indicator's code or branding.
- Do NOT edit production code (${REPO}/indicators/*, ${APEX}/APEX_ULTIMATE.pine). Write only the files assigned to you.`

const TEMPLATE = `DOCUMENT FORMAT (Markdown). Use these sections:
# <NN> · <Title>
1. Scope and role in APEX: which APEX module(s) this feeds.
2. Classification table: concept | E/A/D/C | evidence grade | objectively calculable? (yes / proxy / no) | one-line note.
3. Features: one entry per feature or concept, using EXACTLY these fields:
   ### <Feature>
   - **Classification:** E/A/D/C; evidence grade.
   - **Definition:**
   - **Market mechanism:** why it could matter; who is on the other side.
   - **Mathematical implementation:** exact formulas or algorithm, all symbols defined. Normalise with ticks, ATR, percentiles or bounded transforms. Give parameters with defaults and justification. State WHEN the value becomes knowable in real time (the confirmation bar), so nothing is backdated.
   - **Required data:**
   - **Pine v6 availability:** built-ins, request.* calls, cost, feasibility (feasible / partial / infeasible).
   - **Proxy limitations:** what an OHLCV proxy cannot know; label proxies as proxies.
   - **Useful when:**
   - **Fails when:**
   - **Validation experiment:** pre-registered hypothesis, outcome definition, sample, horizon, baseline, metric, statistical test and pass criterion.
   - **Existing evidence:** study replications with numbers and n; literature.
   - **APEX recommendation:** pick one of INCLUDE-CORE, INCLUDE-OPTIONAL (off by default), RESEARCH-ONLY or EXCLUDE, with the reason. Add redundancy notes saying what it overlaps with.
   - **Sources:**
4. Interactions and redundancy: correlated features and how to consolidate them, so the same evidence is never counted twice.
5. Data requirements and assumptions.
6. Limitations and failure modes, including asset-class differences (futures, FX, equities, ETFs, crypto spot and perpetuals) and session or DST issues.
7. Recommendations for APEX, ranked, each mapped to a module.
8. Open questions and Phase 6 experiments.
9. Sources.
Be thorough and concrete. Depth and correctness matter more than length. Each document should typically be 25-70 KB.`

const ROLE_OUT = {
  type: 'object',
  properties: {
    files: { type: 'array', items: { type: 'string' } },
    summary: { type: 'string' },
    recommendations: { type: 'array', items: { type: 'object', properties: {
      id: { type: 'string' }, feature: { type: 'string' },
      decision: { type: 'string', enum: ['INCLUDE-CORE', 'INCLUDE-OPTIONAL', 'RESEARCH-ONLY', 'EXCLUDE'] },
      module: { type: 'string' }, rationale: { type: 'string' }, evidence: { type: 'string' } },
      required: ['id', 'feature', 'decision', 'module', 'rationale', 'evidence'] } },
    experiments: { type: 'array', items: { type: 'object', properties: {
      id: { type: 'string' }, hypothesis: { type: 'string' }, outcome: { type: 'string' }, horizon: { type: 'string' },
      baseline: { type: 'string' }, metric: { type: 'string' }, passCriterion: { type: 'string' }, data: { type: 'string' } },
      required: ['id', 'hypothesis', 'outcome', 'horizon', 'baseline', 'metric', 'passCriterion', 'data'] } },
    dataNeeds: { type: 'array', items: { type: 'string' } },
    openIssues: { type: 'array', items: { type: 'string' } },
  },
  required: ['files', 'summary', 'recommendations', 'experiments', 'dataNeeds', 'openIssues'],
}

const REVIEW_OUT = {
  type: 'object',
  properties: {
    verdict: { type: 'string', enum: ['pass', 'pass_with_fixes', 'major_issues'] },
    changes: { type: 'array', items: { type: 'string' } },
    residualConcerns: { type: 'array', items: { type: 'string' } },
    checked: { type: 'integer' }, corrected: { type: 'integer' }, unverifiable: { type: 'integer' },
    summary: { type: 'string' },
  },
  required: ['verdict', 'changes', 'residualConcerns', 'checked', 'corrected', 'unverifiable', 'summary'],
}

const INSPECT_OUT = {
  type: 'object',
  properties: {
    file: { type: 'string' },
    summary: { type: 'string' },
    preserve: { type: 'array', items: { type: 'string' } },
    rework: { type: 'array', items: { type: 'string' } },
    drop: { type: 'array', items: { type: 'string' } },
    defects: { type: 'array', items: { type: 'string' } },
    userPreferences: { type: 'array', items: { type: 'string' } },
    lessonsFromTesting: { type: 'array', items: { type: 'string' } },
  },
  required: ['file', 'summary', 'preserve', 'rework', 'drop', 'defects', 'userPreferences', 'lessonsFromTesting'],
}

// ---------------- Phase 1: workspace inspection ----------------
phase('Inspect')
const INSPECT_RULES = `You are the PHASE 1 WORKSPACE INSPECTOR. Inspect the real files and never assume a file exists. Read the code, do not skim it.
For each project:
- purpose and design;
- architecture and section map;
- inventory of calculations: every function, with line references and what it computes;
- inputs, settings and defaults;
- signal logic;
- non-repaint status: check request.security usage, pivot confirmation and barstate handling;
- performance risks;
- broken, duplicated or dead functions;
- test evidence: what was actually tested, on what data, with what result;
- the user's evident preferences (visual style, modes, wording).
For each valuable component, recommend PRESERVE (carry into APEX as is), REWORK (keep the idea, fix it) or DROP, with reasons and line references. Where a README or test reports results, record the lessons: which ideas the data rejected or supported.
Write your report to the assigned file. Do not modify any source file.`

const INSPECTORS = [
  { key: 'dol', file: `${RES}/inspection/I1_dol_lineage.md`, prompt: `ASSIGNMENT I1: the DOL lineage.
- ${APEX}/legacy/dol_engine_v2_00a405a.pine: the current flagship, 2448 lines. Inventory it fully.
- ${APEX}/legacy/DOL_Engine_early.pine and DOL_Engine_early.README.md: the earlier engine, with "Sweep Reversal mode and its test results".
- ${APEX}/legacy/liquidity-flow-pro.pine, liquidity-flow-pro.README.md and liquidity_model_sim.py.
Also read ${REPO}/dev-notes/HANDOFF.md (user preferences and history), ${REPO}/dev-notes/runs/overhaul-r1-findings.md (49 audited defects in v2) and ${REPO}/dev-notes/brief/reference_look.png (the user's reference screenshot; open it with Read).
Compare the three engines: which liquidity and target logic is strongest, and what the early engine's tested results say. Map v2's components to the APEX spec's modules (spec sections 3-18): what exists, what is partial, what is missing.` },
  { key: 'sig', file: `${RES}/inspection/I2_signal_lineage.md`, prompt: `ASSIGNMENT I2: the signal and backtest lineage.
- ${APEX}/legacy/XAUUSD_Fast_Balanced_Pro.pine and its README: an earlier FAST/BALANCED buy/sell system. The APEX spec asks for FAST and BALANCED modes, so study exactly how they were defined.
- ${APEX}/legacy/buy_sell_indicator.pine and its README.
- ${APEX}/legacy/mnq_orb/: the MNQ 5m ORB indicator and strategy, the Python backtest (backtest.py, bt.py, ind_ref.py, final_ref.py, prepare_data.py, fetch_data.sh), the PineTS verification harness (verify.py, validate.cjs, run_pinets.mjs) and the README with its results.
Extract:
- the backtest methodology and its costs, in-sample and out-of-sample results, and rejected ideas;
- how the Pine code was verified offline. This harness is the template for APEX validation, so explain exactly how it works.
- signal designs and their weaknesses (overfitting risk, instrument hardcoding, repainting, forced signals).` },
]
const inspections = await parallel(INSPECTORS.map(I => () =>
  agent(`${PRE}\n\n${HONESTY}\n\n${INSPECT_RULES}\n\n${I.prompt}\n\nWrite the report to ${I.file}. Return the structured summary.`, { label: `inspect:${I.key}`, phase: 'Inspect', schema: INSPECT_OUT })))

const merged = await agent(`${PRE}\n\n${HONESTY}\n\nYou are the LEAD INSPECTOR. Merge the two Phase 1 reports into ${RES}/WORKSPACE_INSPECTION.md, the official Phase 1 deliverable. Read ${RES}/inspection/I1_dol_lineage.md and ${RES}/inspection/I2_signal_lineage.md, and spot-check their key claims against the sources.
Required sections:
1. Inventory of every file found: what it is, its origin branch and commit (see ${APEX}/legacy/README.md), and its size.
2. What each project does.
3. The PRESERVE / REWORK / DROP table for APEX, consolidated across projects, with reasons and line references.
4. Broken or duplicated functions and known defects. Include the 49 audited v2 findings in summary form.
5. Settings and user preferences. Include the visual reference: the "Timeframe | Bias" table, ONE dashed neon target zone with a glow core, a tether label "Target: <type> / PoT: x%", dark-green iFVG boxes.
6. CONFLICTS between those earlier preferences and the APEX spec, with a recommended resolution for each. For example, the spec's clean default (BUY/SELL markers + one forward path + minimal DOL info; tables optional and off) vs the old bias table, and "PoT %" vs the spec's "Draw Score until calibrated" rule.
7. Lessons learned from earlier tests: which ideas the data rejected or supported.
8. What APEX must build new. Map against the spec's sections 3-18.
Return the structured summary.

INSPECTOR SUMMARIES (JSON): ${JSON.stringify(inspections)}`, { label: 'inspect:merge', phase: 'Inspect', schema: INSPECT_OUT })

// ---------------- Phase 2-3: specialist research + red team ----------------
const WRITERS = [
  { key: 'R1_structure', role: 'R1 · MARKET STRUCTURE AND PRICE ACTION specialist (professional futures trader + structure analyst)',
    files: [`${KB}/04_market_structure.md`], keys: 'ict_struct, price_action, bias_dol, smc_impl, skeptic',
    task: `Write 04_market_structure.md covering everything in spec section 3, each item with a FORMAL rule:
- swing highs and lows: fractal, ATR-ZigZag and percentage ZigZag pivots; developing vs confirmed pivots and the confirmation lag; internal vs external structure;
- HH, HL, LH, LL; BOS, CHoCH and MSS: exact break rules (close vs wick, body-close options) and protected levels;
- structural displacement: a formal definition in ATR and range units; failed breakouts and breakdowns;
- trend continuation and exhaustion; consolidation, compression and expansion; range formation; structural transitions;
- premium/discount, equilibrium and dealing ranges.
Also cover the core price-action methodologies (trend following, mean reversion, breakout, swing and scalping) as they relate to structure.
For each rule state exactly when it becomes knowable in real time, so no signal is backdated.
Use the study evidence; for example, structure does not predict which side is taken first (ict_struct). Review how DOL Engine v2's f_structure works and say what to keep.` },
  { key: 'R2_liquidity', role: 'R2 · LIQUIDITY ENGINEERING AND DOL specialist',
    files: [`${KB}/03_liquidity_theory.md`], keys: 'ict_liq, bias_dol, classic_levels, session_stats, quant_pot, skeptic, x1_positioning, x1_behavioral',
    task: `Write 03_liquidity_theory.md covering spec section 4 completely:
- buy-side, sell-side and internal liquidity sources (all items in 4.1-4.3);
- clustering with normalised tolerances (tick, ATR, local volatility, percentage), with identifiable constituents and every tracked attribute in 4.4;
- whether repeated touches strengthen or weaken each level type, using study evidence;
- the full 10-state lifecycle with EXACT transition rules (4.5) and prevention of double counting;
- sweep taxonomy (4.6) with formal rules: wick probe, sweep and reclaim, breakout and acceptance, failed breakout, sweep then continuation, sweep then reversal, unconfirmed sweep;
- the destination-ranking engine (4.7) with every listed factor, and the required outputs per target;
- the destination-versus-reversal separation (4.8) as two separate statistical processes.
Ground everything in the study's replications: distance and volatility dominate; EQ adds ~0; REJECT is not a reversal edge; opposing FVGs cut reach by 2-3 pp. Review DOL Engine v2's pool model, registry, PoT and ledger, and say what to preserve.` },
  { key: 'R3_ict', role: 'R3a · ICT / SMC / PRICE-IMBALANCE specialist',
    files: [`${KB}/05_ict_smc.md`], keys: 'ict_pd, ict_time, smc_impl, competitors, ict_liq, x1_retail_schools',
    task: `Write 05_ict_smc.md covering spec section 5:
- FVG, iFVG, order blocks, breaker blocks, mitigation blocks, BPR, liquidity voids, displacement, retracement, premium/discount, OTE, inducement hypotheses, consequent encroachment, repricing, imbalance mitigation;
- ICT time concepts: killzones, macros, Silver Bullet, Power of 3/AMD, IPDA, midnight open.
For every zone give the formation, boundaries, confirmation, invalidation and mitigation rules; age; size in ATR; freshness; how to measure the subsequent reaction; the expiry rule.
Explain how to avoid counting overlapping names for the same price region as independent confluence (region de-duplication).
Separate what is objectively calculable from what is subjective. Use the study's null results honestly: FVG/OB reach ≈ a distance-matched random level; breakers are weak; macros and Silver Bullet are null; the time effects are volatility-clock effects.` },
  { key: 'R3_wyckoff_amt', role: 'R3b · WYCKOFF AND AUCTION MARKET THEORY specialist (auction-market specialist)',
    files: [`${KB}/06_wyckoff.md`, `${KB}/07_auction_market_theory.md`], keys: 'wyckoff_sd, amt_profile, price_action, session_stats, x1_internals',
    task: `Write TWO documents covering spec section 6.
- 06_wyckoff.md: accumulation, distribution, reaccumulation, redistribution, spring, upthrust, SOS, SOW, test, shakeout; objective proxies only; what cannot be known from candles.
- 07_auction_market_theory.md: balance and imbalance; acceptance and rejection; initiative vs responsive activity; failed auctions; value migration; range extension; rotation; trend-day behaviour; opening auction behaviour and open types; Market Profile (TPO) and Volume Profile concepts (VA, POC, HVN, LVN, single prints, poor highs and lows, IB), as proxies feasible in Pine.
Never claim institutional accumulation or distribution from candle shapes.` },
  { key: 'R4_mech_exec', role: 'R4a · MARKET MECHANICS, FUTURES EXECUTION AND TRANSACTION COSTS specialist (professional futures trader + exchange-rules expert)',
    files: [`${KB}/01_market_mechanics.md`, `${KB}/16_futures_execution.md`, `${KB}/17_risk_transaction_costs.md`], keys: 'asset_specific, trade_mgmt, orderflow_micro, session_stats, x1_positioning',
    task: `Write THREE documents.
- 01_market_mechanics.md covers spec section 2.1 asset classes and the mechanics that differ by class:
  - NQ/MNQ, ES/MES, YM/MYM, RTY/M2K, GC/SI, CL and other commodities; FX spot and futures; equities; ETFs; crypto spot and perpetuals (funding, 24/7 sessions);
  - tick size and tick value, contract specifications, trading hours and session templates (CME Globex, the daily maintenance break, holiday schedules), DST effects;
  - continuous-contract roll gaps and back-adjustment, settlement, opening and closing auctions;
  - volume quality by feed type (centralised futures volume vs FX tick volume vs fragmented equity volume vs crypto exchange volume).
  For every APEX calculation that depends on these, say how to make it instrument-agnostic (syminfo.mintick, syminfo.pointvalue, session.*, timezone handling).
- 16_futures_execution.md: order types, fills, execution delay, slippage models, gap risk, limit vs market entries at liquidity levels, queue priority, and what can and cannot be modelled from bars.
- 17_risk_transaction_costs.md (spec section 16): spread, slippage, commissions and fees by asset class, realistic cost assumptions for backtests, stop distance, reward-to-risk, available movement vs costs, a "tradeability" metric (expected move in ATR vs round-trip cost in ticks), news and event risk without a calendar (manual windows), and labelling estimates as incomplete when inputs are missing.` },
  { key: 'R4_micro_vol', role: 'R4b · MARKET MICROSTRUCTURE AND ORDER-FLOW DATA specialist (institutional microstructure researcher)',
    files: [`${KB}/02_market_microstructure.md`, `${KB}/08_volume_vwap.md`], keys: 'orderflow_micro, amt_profile, x1_internals, academic_sr, asset_specific',
    task: `Write TWO documents covering spec section 7.
- 02_market_microstructure.md:
  - concepts: bid/ask, spread, market vs limit orders, depth, impact (square-root law, Kyle's lambda), liquidity provision vs taking, aggressor side, queue priority, adverse selection, volume imbalance, cumulative delta;
  - for each concept, exactly what TradingView/Pine can observe (request.security_lower_tf with intrabar up/down volume, the built-in footprint and volume-delta requests if documented in the mirror, tick-rule and bulk-volume-classification proxies) vs what is impossible (order-book depth, queue);
  - how to label proxies honestly. Never manufacture order-book data.
- 08_volume_vwap.md:
  - relative volume, volume percentiles, expansion and contraction; session, anchored and rolling VWAP with deviation bands (the math, including the variance-weighted bands); volume-at-price approximations, POC and value-area estimates from lower-TF data, with their limits;
  - volume behaviour around breakouts and sweeps, with study evidence;
  - feed limitations: FX tick volume, crypto exchange-specific volume, missing volume.` },
  { key: 'D1_datalab', role: 'R5-DATA · VALIDATION DATA ENGINEER (part of the quantitative team)',
    files: [`${RES}/DATA_CATALOG.md`, `${APEX}/validation/python/apexdata.py`, `${APEX}/validation/fetch_data.sh`, `${APEX}/validation/data_catalog.json`], keys: 'quant_pot, ict_time, smt_inter, amt_profile, classic_levels',
    task: `Build the honest DATA LAB that Phase 6 validation will use.
1. Find every real market dataset already on disk:
   - ${STUDY}/amt_data/cme: a clone of github.com/axb0306/cme-futures-ohlc with CL, ES, GC, NQ, RTY, YM; check which timeframes;
   - ${STUDY}/smt_data/cme: tick data for 6B, 6E, ES, GC, NQ, RTY and micros;
   - ${STUDY}/classic_tools/btc_1h.csv;
   - any other datasets the study tools used. Grep the *_tools/*.py files for read_csv/paths.
   Also fetch NQ 1-minute 2022-2025 from github.com/s-k-28/nq-es-trader-5k-payout, as ${APEX}/legacy/mnq_orb/fetch_data.sh does with a sparse git checkout, if the network allows it.
2. Standardise everything into ${DATA}/ as compressed CSV: UTC epoch-ms 'time' plus open, high, low, close, volume. Use one file per symbol and timeframe, resampling session-aware from the finest available data to 5m, 15m, 1h, 4h and 1D where possible. This directory is git-ignored, so never commit data.
3. Run QUALITY CHECKS per dataset: duplicates, ordering, OHLC consistency, zero or negative prices, missing bars vs the session template, large gaps, continuous-contract roll jumps (detect and record dates and sizes), zero-volume runs, timezone sanity.
   - The study found the GC 1H file corrupted, with two contract months interleaved. Detect that and fix or exclude it with evidence.
4. Write ${APEX}/validation/python/apexdata.py, a loader API with load(symbol, tf) -> DataFrame and the metadata (tick size, point value, asset class, session template, timezone, roll notes).
   Write ${APEX}/validation/data_catalog.json and ${APEX}/validation/fetch_data.sh, which reproduces all the downloads.
   Write ${RES}/DATA_CATALOG.md: every dataset with source URL, licence if known, period, bars, quality findings, known biases (survivorship, roll handling, missing sessions) and which spec tests (20.1 items 1-15) each dataset can or cannot support. Be honest about gaps: there may be no equities, ETFs or crypto perpetuals.
5. Python: create a venv at ${SP}/apexvenv with numpy, pandas, scipy, statsmodels and pyarrow (pip is allowed). Record the exact versions in DATA_CATALOG.md. If pip fails, reuse ${STUDY}/x1_tools/pylib or ${STUDY}/smt_b_tools/venv and record that.
Keep CPU use reasonable, because other agents are running.
Return the structured output: recommendations may be empty; experiments should list which hypothesis tests the data supports.` },
]

const reviewPrompt = (W, out) => `${PRE}\n\n${HONESTY}\n\nYou are R10 · INDEPENDENT RED TEAM AND QUALITY ASSURANCE. You did not write these files. Try to break them.
Files to review: ${W.files.join(', ')} (written by ${W.role}).
For each document:
1. COMPLETENESS against the required format (for knowledge-atlas documents: every feature needs all 12 fields) and against the spec items for this domain. List what is missing, and add it if you can do so correctly.
2. FACT-CHECK every non-trivial claim against the study reports (${STUDY}/*.final.md) and the cited sources; open them. Correct anything wrong, and downgrade overstated evidence grades. Mark unverifiable items "unverified".
3. MATHS: check every formula for units and dimensions, normalisation (instrument-agnostic?), edge cases (na, zero division, empty arrays, insufficient history), real-time knowability (no backdating, no lookahead) and statistical validity (no normality assumption without a check; no scores called probabilities). Recompute at least two worked examples numerically.
4. HONESTY: remove or soften overclaims ("institutions", "proves", "smart money did X", probability labels on heuristics). Check that the E/A/D/C classification is right.
5. PINE FEASIBILITY claims: verify them against the docs mirror (${DOCS}).
For a data lab or toolchain deliverable, re-run a sample of the quality checks or commands yourself and confirm the numbers.
Edit the files IN PLACE to fix the errors you find, keeping the author's structure. Then append a section "## Red-team review (R10)" listing each change and the residual concerns.
Return the verdict.

AUTHOR'S STRUCTURED OUTPUT (JSON): ${JSON.stringify(out || {}).slice(0, 12000)}`

phase('Research')
const results = await pipeline(
  WRITERS,
  (W) => agent(`${PRE}\n\n${HONESTY}\n\n${W.files[0].endsWith('.md') && W.key !== 'D1_datalab' ? TEMPLATE : ''}\n\nYOUR ROLE: ${W.role}.\nStudy reports most relevant to you (read them fully; read others as needed): ${W.keys}.\n\nASSIGNMENT:\n${W.task}\n\nOutput files: ${W.files.join(', ')}. Return the structured output; its recommendations and experiments feed the architecture and the pre-registered validation plan.`, { label: `write:${W.key}`, phase: 'Research', schema: ROLE_OUT }),
  (out, W) => agent(reviewPrompt(W, out), { label: `redteam:${W.key}`, phase: 'Red-team', schema: REVIEW_OUT }).then(rv => ({ key: W.key, files: W.files, out, review: rv })),
)

return {
  inspection: merged ? { summary: merged.summary, conflicts: merged.userPreferences } : null,
  research: results.filter(Boolean).map(r => ({ key: r.key, files: r.files, summary: r.out ? r.out.summary.slice(0, 1500) : 'writer failed',
    nRec: r.out ? r.out.recommendations.length : 0, nExp: r.out ? r.out.experiments.length : 0,
    review: r.review ? { verdict: r.review.verdict, corrected: r.review.corrected, unverifiable: r.review.unverifiable, concerns: r.review.residualConcerns.slice(0, 6) } : null })),
}
