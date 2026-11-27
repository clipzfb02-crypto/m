export const meta = {
  name: 'apex-p2-p3-part-b',
  description: 'APEX ULTIMATE Phases 2-3 (part B): knowledge-atlas docs 09-15,18 + methodology objectivity matrix + offline Pine toolchain, each red-teamed',
  phases: [
    { title: 'Research', detail: 'specialist writers produce atlas documents and the toolchain' },
    { title: 'Red-team', detail: 'R10 fact-checks, math-checks and corrects every deliverable' },
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

const WRITERS = [
  { key: 'R5_stats', role: 'R5 · QUANTITATIVE MATHEMATICS AND STATISTICAL MODELLING specialist (quant researcher + statistical modeller)', doc: true,
    files: [`${KB}/11_statistical_mathematics.md`], keys: 'quant_pot, quant_regime, calib_ml, academic_sr, skeptic, x1_tv_validation, x1_behavioral',
    task: `Write 11_statistical_mathematics.md covering spec sections 10 and 20.2:
- linear, rolling and robust regression (Theil-Sen, Huber, and which are feasible in Pine); standard deviation vs MAD; z-scores and robust z; percentile ranks; autocorrelation and the variance ratio; return distributions, fat tails, skewness and kurtosis (with typical values for futures and crypto at intraday horizons, from the literature or the study);
- correlation and its instability; volatility normalisation; Bayesian updating (Beta-Binomial for hit rates, with shrinkage toward a baseline); conditional probability; logistic models (online SGD-feasible forms); feature interactions; regime-conditioned statistics;
- bootstrap (stationary/block bootstrap for dependent data) and Monte Carlo; confidence intervals (Wilson for proportions); calibration curves; significance and multiple testing (Bonferroni/Holm, BH-FDR);
- the Deflated Sharpe Ratio (exact formula, Bailey & López de Prado), the Probability of Backtest Overfitting (CSCV), walk-forward design, purging and embargo for overlapping horizons, lookahead/leakage/survivorship protections, transaction-cost sensitivity.
For each item give the exact formulas, an online/incremental Pine-feasible form where possible (Welford, EWMA, P² quantiles or a bounded ring buffer), its numerical pitfalls, and its role in APEX. Every model in APEX must have a defined target, sample, horizon and validation method: write the template for that.` },
  { key: 'R6_vol_mom', role: 'R6 · VOLATILITY, MOMENTUM AND REGIME specialist (volatility researcher + systematic strategist)', doc: true,
    files: [`${KB}/09_volatility.md`, `${KB}/10_momentum.md`], keys: 'quant_regime, ict_time, x1_implied_vol, academic_sr, price_action, quant_pot',
    task: `Write TWO documents.
- 09_volatility.md covers spec section 9:
  - ATR (RMA vs SMA), ATR percentile, true range;
  - realised-volatility estimators (close-to-close, Parkinson, Garman-Klass, Rogers-Satchell, Yang-Zhang), with formulas and the efficiency and bias of each;
  - range percentile; expansion and contraction; clustering (GARCH intuition, EWMA RiskMetrics); vol-of-vol;
  - compression (NR7, Bollinger bandwidth percentile, TTM-squeeze proxy) and breakout expansion; gaps; abnormal moves (robust z of TR);
  - trend, range and transition regimes, with ADAPTIVE thresholds and HYSTERESIS (enter/exit bands, minimum dwell);
  - the intraday volatility clock (time-of-day seasonality) from the study, which affects every horizon calculation; low-liquidity periods; implied vol (VIX/VXN) as optional context.
  Spell out mathematically how "breakout from compression" differs from "extension in an expanded market".
- 10_momentum.md covers spec section 8:
  - EMA 20/50/100/200, slope, separation; RSI, MACD, ROC, DMI/ADX; VWAP as trend context; regression slope (normalised t-stat); acceleration and deceleration; divergence (formal, confirmed-pivot based); persistence (Hurst/variance ratio, run tests); trend strength; mean-reversion conditions.
  - REDUNDANCY ANALYSIS: which of these are near-duplicates (EMA stack vs slope vs separation vs MACD vs ROC). Propose a consolidated small set of orthogonal factors (for example, one trend factor, one momentum-change factor, one stretch/mean-reversion factor), with the math to orthogonalise or group them. Use evidence from academic time-series momentum and intraday momentum literature and the study.` },
  { key: 'R7_mtf_inter', role: 'R7 · MULTI-TIMEFRAME AND INTERMARKET specialist', doc: true,
    files: [`${KB}/14_multi_timeframe.md`, `${KB}/15_intermarket.md`], keys: 'bias_dol, smt_inter, pine_eng, x1_internals, quant_regime, ict_struct',
    task: `Write TWO documents.
- 14_multi_timeframe.md covers spec section 11:
  - the execution / confirmation / primary-context / HTF-structure hierarchy, with the Scalping, Day Trading, Swing and Custom templates;
  - SAFE request.security patterns (the [1] offset + lookahead_on for confirmed HTF values; provisional vs confirmed values; never requesting below the chart TF; the request.security_lower_tf uses);
  - repaint failure modes, with exact examples from the docs mirror; how disagreement between timeframes should reduce confidence (the math of aggregation with agreement weights).
  - Study evidence: does HTF bias improve target-hit or direction forecasts? Use the bias_dol replications.
- 15_intermarket.md covers spec section 12:
  - DXY, yields (US10Y/ZN), gold, silver, crude, equity indices, sector ETFs, breadth (ADD, TICK, VOLD, TRIN availability on TradingView), BTC, and configurable references;
  - rolling correlation of returns (never of price levels) and correlation stability (Fisher-z CI, rolling-window dispersion); lead-lag; SMT divergence (the study's evidence);
  - what happens when a symbol is unavailable (graceful degradation); manual event windows; why news cannot be detected without a calendar.
  - Never claim causation.` },
  { key: 'R8_forecast_calib', role: 'R8 · FORECASTING AND PROBABILITY CALIBRATION specialist (mathematical forecasting engineer)', doc: true,
    files: [`${KB}/12_forecasting.md`, `${KB}/13_probability_calibration.md`], keys: 'quant_pot, calib_ml, quant_regime, skeptic, ict_time, academic_sr, x1_tv_validation',
    task: `Write TWO documents. They are central to APEX's primary feature: one forward path, 20-120 bars, default 60.
- 12_forecasting.md covers spec section 14:
  - Candidate methods for a CONDITIONAL forward path with exact math: regression-based drift; momentum persistence with decay (e.g. an AR(1)/OU-style drift decay, half-life estimation); volatility-scaled movement (sqrt-time scaling with the vol clock); state-dependent drift by regime and bias state; target-aware trajectory shaping (a bridge toward the DOL target, weighted by the empirically estimated reach rate, and NEVER assuming the target is reached); barrier effects from opposing liquidity and FVGs; regime-conditioned scenarios; and a simple random-walk/zero-drift baseline the path must beat.
  - How to construct ONE path (an expected or median path) and how to draw it in Pine (polyline or line segments, colour by direction).
  - Forecast uncertainty from ROLLING OUT-OF-SAMPLE RESIDUALS: store forecasts made H bars ago and compare them with realised prices. These are horizon-specific empirical quantiles that are regime-conditioned when sample sizes allow, and they give honest prediction intervals.
  - Online evaluation metrics: MAE/RMSE vs the random-walk baseline, directional hit rate with a Wilson CI, interval coverage.
  - What could invalidate the scenario (a structural invalidation level).
  - Make it non-repainting: the path is recomputed each confirmed bar; historical paths are never altered.
- 13_probability_calibration.md covers spec section 15:
  - Heuristic score vs relative ranking vs model confidence vs calibrated probability.
  - Outcome definitions: target within H; stop before target; neither; direction after H; pool reached within H.
  - Calibration methods feasible online: binned reliability, isotonic (PAV in a bounded buffer), Platt/logistic, Beta-Binomial shrinkage.
  - Metrics: Brier (with the Murphy decomposition), log loss, reliability diagrams, ECE, precision/recall/FPR, and skill vs baselines (climatology and the distance-matched random-level baseline from DOL Engine v2's ledger).
  - The minimum sample-size rules before a "probability" label may be shown (e.g. n ≥ N with a CI width ≤ W), and how DOL Engine v2's PoT, ledger and EDGE should be preserved or reworked under these rules.` },
  { key: 'R9_pine', role: 'R9 · PINE SCRIPT v6 ENGINEERING specialist (senior Pine developer)', doc: true,
    files: [`${KB}/18_pine_v6_implementation.md`], keys: 'pine_eng, ux_design, competitors, smc_impl',
    task: `Write 18_pine_v6_implementation.md covering spec section 19 entirely, grounded in the docs mirror (quote doc file paths):
- v6 language rules that bite: types, qualifiers, the na rules (no implicit bool na, int/float na handling), lazy and/or evaluation, tuples, UDTs/methods/maps/matrices/arrays, var vs varip, history referencing and max_bars_back, loops and their limits, the := rules for globals in functions, and the no-forward-reference rule;
- request.security semantics (the lookahead/[1] pattern, calc on HTF, limits on the number of request calls, tuple requests to save calls, request.security_lower_tf);
- drawings (line/box/label/polyline/table limits, the max_*_count declarations, object lifecycle and deletion, efficient update-in-place);
- alerts (alert() vs alertcondition(), frequency settings, avoiding duplicates);
- barstate handling (isconfirmed, isrealtime, islast, isnew, rollback semantics in real time);
- execution time limits and profiling; compiled-size and token limits; input limits; plot-count limits.
- A repaint checklist and an engineering checklist for APEX.
- Recommended module organisation within one file: section layout and naming conventions.
- How to make every calculation instrument-agnostic (syminfo.mintick, pointvalue, session, timezone).
- How DOL Engine v2 does these things and what to keep.
Be exact: include limit numbers only when the docs mirror states them, and cite the doc file.` },
  { key: 'R5b_methods', role: 'R5b · SYSTEMATIC-METHODOLOGY AUDITOR (quantitative systematic trading)', doc: false,
    files: [`${KB}/00_METHODOLOGY_OBJECTIVITY_MATRIX.md`], keys: 'all study reports (skim each .final.md; deep-read skeptic, x1_retail_schools, academic_sr, competitors)',
    task: `Write 00_METHODOLOGY_OBJECTIVITY_MATRIX.md fulfilling spec section 2.2. Cover every methodology: ICT, Smart Money Concepts, Wyckoff, Auction Market Theory, Market Profile, Volume Profile, price action, trend following, mean reversion, momentum, breakout, swing trading, scalping, statistical-arbitrage concepts, quantitative systematic trading, market microstructure, liquidity-based trading, volatility-based trading.
For each methodology:
- core claims;
- which concepts can be objectively calculated (with the formal definition source in the atlas), which only through proxies, and which remain subjective;
- the strength of the evidence for and against, citing study replications with n and the academic literature;
- typical failure regimes;
- the incompatibilities when combined with other methodologies (spec: "Do not combine methodologies indiscriminately"), e.g. trend following vs mean reversion in the same regime;
- what APEX should take from it.
End with a cross-methodology table and a list of concepts that appear under different names in several schools (the same evidence, so not independent confluence), e.g. "order block", "demand zone" and "last opposing candle".` },
  { key: 'R9b_toolchain', role: 'R9b · OFFLINE PINE TOOLCHAIN ENGINEER (Pine engineering + QA)', doc: false,
    files: [`${RES}/OFFLINE_TOOLCHAIN.md`, `${APEX}/validation/pine/validate.cjs`, `${APEX}/validation/pine/run_pinets.mjs`, `${APEX}/validation/pine/repaint_test.mjs`, `${APEX}/validation/pine/README.md`], keys: 'pine_eng (sections on PineTS and PENG-7)',
    task: `Build and characterise the OFFLINE Pine toolchain. There is no TradingView compiler here, and tradingview.com is blocked.
Already installed in ${SP}/pine_harness (node 22): pinets 0.13.1 (an offline Pine runtime) and pinescript-v6-validator 0.4.3 (an independent static checker). There is also the pynescript-based syntax parser ${SP}/tools/pine_parse.sh (venv ${SP}/venv). A previous project's harness is in ${APEX}/legacy/mnq_orb/ (validate.cjs, run_pinets.mjs, verify.py); study it.
1. Run the validator on ${SP}/brief/baseline_v2.pine and on each legacy .pine; record the results.
2. Try to EXECUTE DOL Engine v2 (the baseline) in PineTS on real data. Use ${STUDY}/amt_data/cme (NQ, ES or GC; find the 5m or 1h files) converted to the candle JSON format the harness uses ({open, high, low, close, volume, openTime, closeTime} in ms). Record exactly what runs and what fails. Then write small probe scripts to establish PineTS support for each construct APEX may need:
   - UDTs, methods, arrays, maps and matrices;
   - request.security with [1] + lookahead_on, and request.security_lower_tf;
   - ta.pivothigh/pivotlow, ta.atr/rma/ema/rsi/dmi/linreg/percentrank;
   - session/time functions with a timezone;
   - var/varip; barstate.isconfirmed in historical runs;
   - line/box/label/polyline/table, plotshape, alert() and alertcondition().
   Write a support matrix: supported / partial / unsupported, with evidence from your probes.
3. Write reusable harness files in ${APEX}/validation/pine/:
   - validate.cjs (validator wrapper);
   - run_pinets.mjs (generic: script, data JSON, symbol-info JSON, timeframe; exports all plot series to JSON);
   - repaint_test.mjs: run the same script on prefixes of the data (e.g. N-500, N-250, N bars) and assert that plotted signal series are identical on the overlapping confirmed bars. This is a direct no-repaint and start-point-parity test.
   - README.md with usage.
   Do NOT commit node_modules (git-ignored); give npm install instructions.
4. Write ${RES}/OFFLINE_TOOLCHAIN.md. Cover what this toolchain can and cannot prove, honestly:
   - it is not TradingView's compiler;
   - PineTS v6 support is experimental;
   - Bar Replay and true real-time tick behaviour cannot be reproduced exactly, so mark those spec tests as NOT RUN unless an approximation is justified;
   - how Phase 5 and Phase 6 should use it.
Return the structured output; experiments = the harness tests Phase 6 should run.` },
]

const reviewPrompt = (W, out) => `${PRE}\n\n${HONESTY}\n\nYou are R10 · INDEPENDENT RED TEAM AND QUALITY ASSURANCE. You did not write these files. Try to break them.
Files to review: ${W.files.join(', ')} (written by ${W.role}).
For each document:
1. COMPLETENESS against the required format (for knowledge-atlas documents: every feature needs all 12 fields) and against the spec items for this domain. List what is missing, and add it if you can do so correctly.
2. FACT-CHECK every non-trivial claim against the study reports (${STUDY}/*.final.md) and the cited sources; open them. Correct anything wrong, and downgrade overstated evidence grades. Mark unverifiable items "unverified".
3. MATHS: check every formula for units and dimensions, normalisation (instrument-agnostic?), edge cases (na, zero division, empty arrays, insufficient history), real-time knowability (no backdating, no lookahead) and statistical validity (no normality assumption without a check; no scores called probabilities). Recompute at least two worked examples numerically, e.g. with Python.
4. HONESTY: remove or soften overclaims ("institutions", "proves", "smart money did X", probability labels on heuristics). Check that the E/A/D/C classification is right.
5. PINE FEASIBILITY claims: verify them against the docs mirror (${DOCS}).
For a toolchain deliverable, re-run the harness commands yourself and confirm that the support matrix matches reality.
Edit the files IN PLACE to fix the errors you find, keeping the author's structure. Then append a section "## Red-team review (R10)" listing each change and the residual concerns.
Return the verdict.

AUTHOR'S STRUCTURED OUTPUT (JSON): ${JSON.stringify(out || {}).slice(0, 12000)}`

phase('Research')
const results = await pipeline(
  WRITERS,
  (W) => agent(`${PRE}\n\n${HONESTY}\n\n${W.doc ? TEMPLATE : ''}\n\nYOUR ROLE: ${W.role}.\nStudy reports most relevant to you (read them fully; read others as needed): ${W.keys}.\n\nASSIGNMENT:\n${W.task}\n\nOutput files: ${W.files.join(', ')}. Return the structured output; its recommendations and experiments feed the architecture and the pre-registered validation plan.`, { label: `write:${W.key}`, phase: 'Research', schema: ROLE_OUT }),
  (out, W) => agent(reviewPrompt(W, out), { label: `redteam:${W.key}`, phase: 'Red-team', schema: REVIEW_OUT }).then(rv => ({ key: W.key, files: W.files, out, review: rv })),
)

return {
  research: results.filter(Boolean).map(r => ({ key: r.key, files: r.files, summary: r.out ? r.out.summary.slice(0, 1500) : 'writer failed',
    nRec: r.out ? r.out.recommendations.length : 0, nExp: r.out ? r.out.experiments.length : 0,
    review: r.review ? { verdict: r.review.verdict, corrected: r.review.corrected, unverifiable: r.review.unverifiable, concerns: r.review.residualConcerns.slice(0, 6) } : null })),
}
