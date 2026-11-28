export const meta = {
  name: 'apex-p2-empirical-c',
  description: 'APEX Phase 2 empirical research (C): sweep taxonomy and liquidity lifecycle parameters, structure-engine rules, session/time liquidity — each re-run by a red-team verifier',
  phases: [
    { title: 'Experiment', detail: 'real-data experiments with pre-registered definitions' },
    { title: 'Verify', detail: 'R10 re-runs the code and checks for leakage, overfitting and fabrication' },
  ],
}
const SP = '/tmp/claude-0/-home-user-m/7ce60006-3639-59b1-8cd3-87355409d58a/scratchpad'
const REPO = '/home/user/m'
const APEX = `${REPO}/apex`
const STUDY = `${SP}/brief/study`
const SPEC = `${REPO}/dev-notes/brief/APEX_ULTIMATE_SPEC.md`
const EXP = `${APEX}/research/experiments`
const CODE = `${APEX}/validation/python`

const PRE = `PROJECT. You are a specialist on the APEX ULTIMATE team. The team is building an honest, evidence-based Draw-on-Liquidity and quantitative market-intelligence indicator in Pine Script v6.
- Governing requirements: ${SPEC}. Read sections 0, your domain's sections, 20, 21 and 25.
- The existing engine is DOL Engine v2 (${SP}/brief/baseline_v2.pine; design in ${REPO}/README.md).
- The completed research study is in ${STUDY}/*.final.md; its replication scripts live in ${STUDY}/*_tools/. Reuse loaders, do NOT merely repeat: extend, and cite what the study already found.
- Other experiment tracks run in parallel and write to ${EXP}/. Read any that exist to avoid duplicated work.

DATA:
- Real futures OHLCV is in ${STUDY}/amt_data/cme/<SYM>/: a clone of github axb0306/cme-futures-ohlc with NQ, ES, YM, RTY, GC and CL, as 1h and 1min files. Check the columns and timezones yourself.
- Tick data for 6B, 6E, ES, GC, NQ and RTY: ${STUDY}/smt_data/cme. BTC 1h: ${STUDY}/classic_tools/btc_1h.csv.
- The standardised loader ${CODE}/apexdata.py and the statistics library ${CODE}/apexstats.py may be ready; use them if present.
- The GC 1H file is known to be corrupted: exclude it or repair it with evidence.
- Python: ${SP}/apexvenv if it exists, else your own venv under ${SP}/venv_<key> (pip allowed). Use nice -n 10 for long jobs.

RESEARCH STANDARD (non-negotiable):
- Pre-register the hypothesis, outcome, horizon, baseline, metric and pass criterion BEFORE looking at the results.
- No lookahead: features use bars <= t; pivots count only from their confirmation bar; HTF values come from COMPLETED HTF bars.
- Chronological splits, purged where horizons overlap; report in-sample and out-of-sample separately.
- Report n, effect sizes, Wilson or block-bootstrap CIs, the number of variants tried, and Holm/BH corrections.
- Use meaningful baselines, e.g. a distance-matched random level.
- NEVER fabricate or round up results; null results are valuable.
- Code goes to ${CODE}/experiments/<key>/ (outputs in its out/ subfolder, git-ignored); the report to ${EXP}/<key>.md.`

const RESUME_NOTE = `RESUME NOTE: an earlier attempt at this assignment was interrupted by a usage limit. Partial outputs may already exist at your output paths, and code may exist under your experiment folder. Read them first and verify them; do not trust them blindly. Keep what is correct and complete or replace the rest. Do not start from scratch if a sound partial draft exists, and do not leave the draft's unfinished parts in place.`
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
  { key: 'E6_sweep_lifecycle', role: 'R2 LIQUIDITY ENGINEER', task: `Parameterise the liquidity LIFECYCLE state machine (spec 4.5) and the SWEEP TAXONOMY (spec 4.6) from data.
(1) Define each sweep subtype formally:
- wick probe: a high beyond the level by < p ATR, closing back inside;
- sweep and reclaim: beyond by ≥ p, closing back inside within N bars;
- breakout and acceptance: K consecutive closes beyond, or a close beyond with the next bar holding;
- failed breakout: acceptance, then a close back inside within M bars;
- sweep then continuation / sweep then reversal: the post-event path reaching +X ATR beyond vs the opposite-side liquidity first;
- unconfirmed sweep: the current bar is beyond but not yet closed.
Measure the frequency and the outcome distributions of each subtype per instrument and timeframe, and the time to resolution.
(2) Calibrate the transition thresholds from data, as robust percentiles in ATR units rather than magic numbers:
- the "approaching" distance band: at what distance/ATR does the reach rate within H climb steeply?
- the acceptance rule: how many closes beyond best separate continuation from failure?
- the reclaim window N;
- expiry: after what age, and how many sessions untouched, does a level stop behaving differently from a random level?
(3) Double counting: quantify how often one bar sweeps several pools, and how DOL Engine v2's liqEvt sum over-counts (study ict_liq).
Deliver a concrete state-transition table with parameter values and their CIs.` },
  { key: 'E7_structure_rules', role: 'R1 MARKET-STRUCTURE ANALYST', task: `Turn spec section 3 into data-grounded formal rules.
(1) Pivot methods: fractal L/R pivots (2/2, 3/3, 5/5), ATR-ZigZag (1.5 ATR and 3 ATR) and percentage ZigZag. Measure the confirmation lag in bars, pivot density per session, and stability (how often a pivot is superseded within N bars).
(2) BOS and CHoCH: compare a close beyond vs a wick beyond the protected pivot. Measure the follow-through (the next H-bar move in ATR in the break direction vs a random-time baseline) and the false-break rate.
(3) Displacement: candidate definitions (body/ATR ≥ k, range percentile ≥ q, close-location). Measure the follow-through and the definition's base rate.
(4) Compression/expansion and range formation: the NR-n/bandwidth-percentile range detector with hysteresis; how often ranges break, in which direction, with what follow-through.
(5) Premium/discount within the dealing range (the last confirmed swing high to low): does location predict the direction or reversal at H, out of sample? (The study suggests momentum rather than reversion; extend it.)
(6) "Structure does not predict which side is taken first" (study ict_struct): replicate briefly, and test whether it predicts the DIRECTION of the H-bar move instead.
Deliver the recommended structure-engine rule set with parameters.` },
  { key: 'E8_session_time', role: 'R4a MARKET-MECHANICS / SESSION SPECIALIST', task: `Session and time liquidity, instrument-agnostic.
(1) For every level type in spec 4.1/4.2: PDH/PDL, PWH/PWL, PMH/PML, Asia/London/NY session highs and lows, opening-range (first 15/30 min of the RTH session) highs and lows, ONH/ONL, and confirmed swing highs and lows.
- Measure the reach rate within H vs a distance-matched random level, by instrument and timeframe.
- Measure the "reached first among the nearest pair" rates.
- Grade the level-type hierarchy empirically. Does PWH beat PDH beat a session high at equal distance?
(2) Session membership correctness: quantify the error of bar-open time() membership vs exact membership for each timeframe (1m, 5m, 15m, 1h, 4h) and each session (Asia, London, NY AM/PM), including DST weeks (US/EU DST mismatch weeks). Recommend the exact algorithm, e.g. using lower-TF data or bar-overlap logic.
(3) Verify the study's US cash-open drive effect (09:20-09:59 ET) on ES, NQ, YM and RTY over more data, and check whether there is an analogue for CL and GC at their own key opens.
(4) Recommend a session-template design that works for CME futures, FX (Sydney/Tokyo/London/NY), crypto (24/7, UTC days) and equities (RTH only), with the DST rules.` },
]
const verifyPrompt = (T, out) => `${PRE}\n\nYou are R10 · RED-TEAM VERIFIER. Another agent ran experiment ${T.key}. Do NOT trust it: reproduce it.
- Read ${EXP}/${T.key}.md and the code. Re-run the key computations, in full or on a representative subset, and confirm the headline numbers.
- Hunt for: lookahead or leakage (future pivots, centred windows, incomplete HTF bars, full-sample normalisation); undisclosed variants; i.i.d. CIs on overlapping samples; timezone and DST errors; roll gaps; GC corruption; overclaims.
- Fix the code and the report where you can. Append "## Red-team verification (R10)" with what you reproduced, what you corrected and your verdict.

EXPERIMENT OUTPUT (JSON): ${JSON.stringify(out || {}).slice(0, 10000)}`
const res = await pipeline(TRACKS,
  (T) => agent(`${PRE}\n\nROLE: ${T.role}. KEY: ${T.key}.\n\n${T.task}\n\n${RESUME_NOTE}`, { label: `exp:${T.key}`, phase: 'Experiment', schema: EXP_OUT }),
  (out, T) => agent(verifyPrompt(T, out), { label: `verify:${T.key}`, phase: 'Verify', schema: VER_OUT }).then(v => ({ key: T.key, out, v })))
return res.filter(Boolean).map(r => ({ key: r.key, summary: r.out ? r.out.summary.slice(0, 1500) : 'failed', findings: r.out ? r.out.findings : [], implications: r.out ? r.out.designImplications : [], verify: r.v ? { verdict: r.v.verdict, problems: r.v.problems.slice(0, 6) } : null }))
