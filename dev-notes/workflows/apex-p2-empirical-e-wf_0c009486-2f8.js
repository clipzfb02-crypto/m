export const meta = {
  name: 'apex-p2-empirical-e',
  description: 'APEX Phase 2 research (E): tradeability and costs, a red-team stress-data suite, and isolated Pine module prototypes (forecast path drawing, residual-quantile bands, online calibration, hysteresis regime, alert dedupe) — each verified',
  phases: [
    { title: 'Experiment', detail: 'tradeability study, stress suite, Pine prototypes' },
    { title: 'Verify', detail: 'R10 re-runs and attacks each deliverable' },
  ],
}
const SP = '/tmp/claude-0/-home-user-m/7ce60006-3639-59b1-8cd3-87355409d58a/scratchpad'
const REPO = '/home/user/m'
const APEX = `${REPO}/apex`
const STUDY = `${SP}/brief/study`
const SPEC = `${REPO}/dev-notes/brief/APEX_ULTIMATE_SPEC.md`
const EXP = `${APEX}/research/experiments`
const CODE = `${APEX}/validation/python`
const HARN = `${SP}/pine_harness`

const PRE = `PROJECT. You are a specialist on the APEX ULTIMATE team. The team is building an honest, evidence-based Draw-on-Liquidity and quantitative market-intelligence indicator in Pine Script v6.
- Governing requirements: ${SPEC}. Read it in full, especially sections 14-21 and 25.
- The existing engine is DOL Engine v2 (${SP}/brief/baseline_v2.pine; design in ${REPO}/README.md).
- The completed research study is in ${STUDY}/*.final.md (pine_eng.final.md matters for the Pine work).

DATA:
- Real futures OHLCV is in ${STUDY}/amt_data/cme/<SYM>/: NQ, ES, YM, RTY, GC and CL, as 1h and 1min files. BTC 1h: ${STUDY}/classic_tools/btc_1h.csv.
- The loader ${CODE}/apexdata.py may be ready.
- Python: ${SP}/apexvenv if it exists, else your own venv under ${SP}/venv_<key>.

OFFLINE PINE TOOLS in ${HARN} (node 22):
- pinets 0.13.1 (an offline Pine runtime; v6 support is experimental);
- pinescript-v6-validator 0.4.3 (static checker; usage: see ${APEX}/legacy/mnq_orb/validate.cjs);
- pynescript syntax parser: bash ${SP}/tools/pine_parse.sh FILE;
- Another agent is building generic harness scripts in ${APEX}/validation/pine/; use them if present.
- The Pine v6 docs mirror is in ${SP}/docsrc/.

STANDARD: never fabricate results; pre-register definitions; no lookahead; report n and CIs; mark untestable items NOT RUN. Use nice -n 10 for long jobs.`

const EXP_OUT = { type: 'object', properties: {
  report: { type: 'string' }, code: { type: 'array', items: { type: 'string' } }, summary: { type: 'string' },
  findings: { type: 'array', items: { type: 'object', properties: { id: { type: 'string' }, hypothesis: { type: 'string' }, result: { type: 'string' }, n: { type: 'string' }, effect: { type: 'string' }, ci: { type: 'string' }, verdict: { type: 'string', enum: ['supported', 'not supported', 'mixed', 'inconclusive'] } }, required: ['id', 'hypothesis', 'result', 'n', 'effect', 'ci', 'verdict'] } },
  designImplications: { type: 'array', items: { type: 'string' } }, caveats: { type: 'array', items: { type: 'string' } } },
  required: ['report', 'code', 'summary', 'findings', 'designImplications', 'caveats'] }
const VER_OUT = { type: 'object', properties: {
  verdict: { type: 'string', enum: ['confirmed', 'confirmed_with_corrections', 'refuted', 'could_not_reproduce'] },
  reproduced: { type: 'array', items: { type: 'string' } }, problems: { type: 'array', items: { type: 'string' } }, corrections: { type: 'array', items: { type: 'string' } }, summary: { type: 'string' } },
  required: ['verdict', 'reproduced', 'problems', 'corrections', 'summary'] }

const TRACKS = [
  { key: 'E12_tradeability', role: 'R4a EXECUTION / TRANSACTION-COST SPECIALIST', task: `Spec section 16: when is a move worth trading?
(1) For each instrument (NQ, MNQ, ES, MES, YM, RTY, GC, CL, BTC), each timeframe (1m, 5m, 15m, 1h) and each time of day, measure the distribution of the expected move over H bars (in ticks and ATR) against a realistic round-trip cost (commission + spread + slippage in ticks; document the assumptions per instrument with sources). Output a cost-to-move ratio table.
(2) Structural stops: measure the distribution of distances to a structural invalidation (e.g. beyond the last confirmed swing, or beyond a swept level plus a buffer) in ticks and ATR, and the R:R feasibility toward the nearest DOL target.
(3) Define a TRADEABILITY metric precisely, e.g. (expected favourable excursion to the target, or the forecast move) / (stop distance + cost). Test whether low tradeability flags poor outcomes out of sample using simple signal proxies (cooperate with ${EXP}/E2_signals.md if it exists).
(4) Gaps and events: the frequency and size of session-open gaps and their effect on stops; how a manual event-window input should work.
Deliver the tradeability formula, thresholds as percentiles or ratios, the per-instrument cost defaults (as inputs, never hardcoded to one symbol) and the honest "incomplete estimate" rules.` },
  { key: 'E13_stress_suite', role: 'R10 RED-TEAM STRESS-SUITE BUILDER', task: `Build the reusable STRESS-TEST SUITE that Phase 6 will run against APEX_ULTIMATE.pine, both in PineTS and in the Python reference.
Write ${APEX}/validation/stress/make_stress.py to generate candle datasets, as JSON for PineTS ({open, high, low, close, volume, openTime, closeTime} in ms) and CSV, into ${APEX}/validation/stress/out/ (git-ignored). Cover every scenario in spec section 21:
- very low volatility; extreme volatility; sudden price gaps; news-like spikes; sideways chop; strong trends; reversal days; thin sessions;
- missing volume (all zeros and NaN-like); incomplete history (very short series, e.g. 50 bars); continuous-futures roll gaps;
- overnight sessions; the DST transition weeks (US and EU); tiny and huge tick sizes (0.00001 FX, 0.25 NQ, 1 BTC);
- 1-minute and weekly timeframes; repeated pivot formation at the same price; repeated sweeps of the same level; overlapping zones; long series with many objects (20k bars);
- a real-time update simulation (the same bar replayed with changing close values).
Use real data segments where they exist (e.g. find actual roll gaps and DST weeks in ${STUDY}/amt_data) and synthetic data otherwise. Document each scenario's purpose and the expected-behaviour checks: no runtime error; no NaN in plots that should be defined; no duplicate alerts per bar; no target on the wrong side of price; projection within sane bounds; signals unchanged when the data is extended (the repaint check).
Then RUN the DOL Engine v2 baseline (${SP}/brief/baseline_v2.pine) through PineTS on the suite. If PineTS cannot run it, run what you can and say why. Document its current failure modes; this is the "before" picture for the CHANGELOG.` },
  { key: 'E14_pine_prototypes', role: 'R9 SENIOR PINE v6 ENGINEER', task: `Build small, isolated, independently testable Pine v6 PROTOTYPES, each a separate minimal indicator under ${APEX}/research/prototypes/. Every prototype must pass pinescript-v6-validator with 0 errors and the pynescript parser, and should run in PineTS on real NQ data where PineTS supports it. Each is research only, not production code.
P1. Forward path drawing: ONE dotted or segmented path of 20-120 bars (default 60) drawn into the future, green when bullish and red when bearish. Use polyline.new with chart.point.from_index/from_time and xloc, deleting and recreating it only on the last bar or on change. Check the future-bar indexing limits in the docs, an optional uncertainty band, and object-count discipline.
P2. Rolling out-of-sample residual quantile buffer: store the forecast made at bar t for horizon h; when bar t+h closes, record the realised error in ATR units into a bounded ring buffer per horizon. Compute empirical 10/50/90% quantiles efficiently, with array.percentile_linear_interpolation or a sorted insert.
P3. Online calibration: Beta-Binomial hit-rate tracking per distance bucket, updated only when outcomes resolve (target hit within H, or expiry). Wilson CI. A rule that shows a "probability" label only when n ≥ N_min and the CI half-width ≤ W; otherwise show "Draw Score".
P4. A hysteresis regime state machine: ATR-percentile regime with enter/exit thresholds and a minimum dwell, confirmed-bar only.
P5. Signal/alert discipline: STRONG BUY / BUY / NEUTRAL / SELL / STRONG SELL with persistence (K confirmed bars); alerts once per state transition on confirmed bars only (alert() with alert.freq_once_per_bar_close); no duplicates; labels limited and recycled.
P6. Safe HTF request: a tuple request.security with [1] + lookahead_on and a provisional-vs-confirmed flag; graceful handling when the reference symbol is unavailable (ignore_invalid_symbol).
For each prototype, give the validator output, the parser output, the PineTS run result (or the reason it cannot run) and a repaint check (run on prefixes and compare). Write ${APEX}/research/prototypes/README.md summarising what works, the API constraints you discovered and the recommendations for Phase 5.` },
]
const verifyPrompt = (T, out) => `${PRE}\n\nYou are R10 · RED-TEAM VERIFIER. Another agent produced deliverable ${T.key}. Do NOT trust it: reproduce it.
- Re-run its scripts, validator, parser and PineTS commands. Confirm or refute each claim.
- For Pine prototypes: check v6 correctness against the docs mirror (function signatures, xloc and future-index limits, polyline limits, alert frequency), repaint safety and object lifecycle.
- For the tradeability study: check the cost assumptions and the leakage.
- For the stress suite: check that each scenario really exercises what it claims.
- Fix problems where you can. Append "## Red-team verification (R10)" to the report with what you reproduced, what you corrected and your verdict.

OUTPUT (JSON): ${JSON.stringify(out || {}).slice(0, 10000)}`
const res = await pipeline(TRACKS,
  (T) => agent(`${PRE}\n\nROLE: ${T.role}. KEY: ${T.key}. Report: ${EXP}/${T.key}.md (code paths as described).\n\n${T.task}`, { label: `exp:${T.key}`, phase: 'Experiment', schema: EXP_OUT }),
  (out, T) => agent(verifyPrompt(T, out), { label: `verify:${T.key}`, phase: 'Verify', schema: VER_OUT }).then(v => ({ key: T.key, out, v })))
return res.filter(Boolean).map(r => ({ key: r.key, summary: r.out ? r.out.summary.slice(0, 1500) : 'failed', findings: r.out ? r.out.findings : [], implications: r.out ? r.out.designImplications : [], verify: r.v ? { verdict: r.v.verdict, problems: r.v.problems.slice(0, 6) } : null }))
