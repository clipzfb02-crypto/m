export const meta = {
  name: 'apex-p2-empirical-b',
  description: 'APEX Phase 2 empirical research (B): DOL target and sweep hypotheses from spec section 20, and volatility-regime / calibration experiments — each re-run by a red-team verifier',
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
- Governing requirements: ${SPEC}. Read sections 0, 4, 9, 13-15, 20, 21 and 25 at least.
- The existing engine is DOL Engine v2 (${SP}/brief/baseline_v2.pine; design in ${REPO}/README.md).
- The completed research study is in ${STUDY}/*.final.md; its replication scripts live in ${STUDY}/*_tools/. Reuse their loaders, and do not merely repeat their tests: extend them.

DATA:
- Real futures OHLCV is in ${STUDY}/amt_data/cme/<SYM>/: a clone of github axb0306/cme-futures-ohlc with NQ, ES, YM, RTY, GC and CL, files like NQ_1h_*.csv and NQ_1min_*.csv. Check the columns and timezones yourself.
- BTC 1h: ${STUDY}/classic_tools/btc_1h.csv.
- A data lab is building standardised data plus a loader at ${CODE}/apexdata.py. Use it if it is ready; otherwise load the raw files yourself.
- The study found the GC 1H file corrupted: exclude it or repair it with evidence.
- Python: use ${SP}/apexvenv if it exists. Otherwise create your own venv under ${SP}/venv_<yourkey> (pip is allowed), or reuse ${STUDY}/x1_tools/pylib.
- Keep CPU use moderate: many agents share 4 CPUs. Use nice -n 10 for long jobs.

RESEARCH STANDARD (non-negotiable):
- Pre-register: write the hypothesis, the exact outcome definition, the horizon, the baseline, the metric and the pass criterion in your report BEFORE looking at the results. Never change definitions after seeing results without reporting both versions.
- No lookahead: features use only bars <= t. Pivots count only from their confirmation bar. HTF values must be the last COMPLETED HTF bar.
- Chronological splits. Purge and embargo overlapping horizons. Report in-sample and out-of-sample separately.
- Report n, effect sizes, Wilson CIs for proportions, block-bootstrap CIs for means, and the number of variants tried. Apply multiple-testing awareness (Holm/BH).
- Compare against a distance-matched random-level baseline or another meaningful one.
- NEVER fabricate or round up results. A null result is a valid, valuable outcome.
- Write code to ${CODE}/experiments/<key>/ (outputs go to ${CODE}/experiments/<key>/out/, git-ignored) and the report to ${EXP}/<key>.md.`

const EXP_OUT = {
  type: 'object',
  properties: {
    report: { type: 'string' },
    code: { type: 'array', items: { type: 'string' } },
    summary: { type: 'string' },
    findings: { type: 'array', items: { type: 'object', properties: {
      id: { type: 'string' }, hypothesis: { type: 'string' }, result: { type: 'string' }, n: { type: 'string' },
      effect: { type: 'string' }, ci: { type: 'string' }, verdict: { type: 'string', enum: ['supported', 'not supported', 'mixed', 'inconclusive'] } },
      required: ['id', 'hypothesis', 'result', 'n', 'effect', 'ci', 'verdict'] } },
    designImplications: { type: 'array', items: { type: 'string' } },
    caveats: { type: 'array', items: { type: 'string' } },
  },
  required: ['report', 'code', 'summary', 'findings', 'designImplications', 'caveats'],
}
const VER_OUT = {
  type: 'object',
  properties: {
    verdict: { type: 'string', enum: ['confirmed', 'confirmed_with_corrections', 'refuted', 'could_not_reproduce'] },
    reproduced: { type: 'array', items: { type: 'string' } },
    problems: { type: 'array', items: { type: 'string' } },
    corrections: { type: 'array', items: { type: 'string' } },
    summary: { type: 'string' },
  },
  required: ['verdict', 'reproduced', 'problems', 'corrections', 'summary'],
}

const TRACKS = [
  { key: 'E3_dol_hypotheses', role: 'R2 LIQUIDITY / DOL RESEARCHER', task: `Test the spec section 20 DOL hypotheses independently, each pre-registered, across instruments (NQ, ES, YM, RTY, CL, BTC; GC only if repaired) and timeframes (5m and 1h where possible):
H1. Do prior-day high/low targets predict DIRECTIONAL TRAVEL better than a naive baseline? Is the next prior-day extreme reached matched by a distance-matched random level and a nearest-level-first rule?
H2. Does a CONFIRMED sweep-and-reclaim improve reversal outcomes? Define the sweep (wick beyond the level by ≥ k ticks or ≥ x ATR) and the reclaim (close back inside within N bars). Compare reaching the opposite-side liquidity before a new extreme against unconditional and wick-only baselines. Separate continuation vs reversal (spec 4.8).
H3. Does target proximity combined with HTF alignment (confirmed HTF structure bias from the last completed HTF bar) improve target-hit rates beyond distance alone? Use logistic regression with distance/ATR as a control.
H4. Do FVGs carry information beyond their overlap with structure: as targets, as barriers in the path, and in a distance-matched comparison?
H5. Lifecycle: do repeated touches strengthen or weaken levels? Hit or break rate by touch count, controlling for distance and age.
H6. Which ranking factors (distance/ATR, level type hierarchy (session < day < week), age, freshness, prior sweeps, opposing barriers, volatility regime, time of day) add out-of-sample skill to a "reached within H bars" model beyond distance+volatility alone? Report the incremental Brier skill / AUC with block-bootstrap CIs.
Design implications: which Draw Score factors and weights are justified, the factors that must be neutral, and how the target-reach model should be defined so it can earn a probability label.` },
  { key: 'E4_regime_calibration', role: 'R6 + R8 VOLATILITY-REGIME AND CALIBRATION RESEARCHER', task: `Pre-register and test:
R1. Volatility regime classification: compare ATR-percentile, realised-vol-percentile and Bollinger-bandwidth compression definitions with hysteresis (enter/exit bands plus minimum dwell). Measure regime persistence, switch frequency and the information about the next-H realised range, out of sample.
R2. Does the volatility regime improve CALIBRATION of "level reached within H bars" probabilities? Compare an empirical first-passage model pooled vs regime-conditioned vs regime + time-of-day volatility clock, by Brier score, log loss and reliability, out of sample, with Murphy-decomposition and bootstrap CIs.
R3. Breakout from compression vs extension in an expanded regime (spec section 9): conditional on a range/level break, compare the follow-through distance and the failure (re-entry) rate across compressed vs expanded states.
R4. Online calibration feasibility for Pine: simulate the online pipeline APEX would run on-chart.
  - A Beta-Binomial shrinkage of the hit rate per distance bucket, updated only after outcomes resolve. Then isotonic or binned recalibration in a bounded buffer.
  - Measure how many resolved samples are needed before calibration error (ECE) drops below 5 pp and the CI half-width falls below 10 pp.
  - Recommend minimum-sample rules for showing a "probability" label vs a "Draw Score".
R5. Trend/range/transition regime classification (ADX, efficiency ratio, variance ratio, Hurst-proxy) with hysteresis: measure stability and whether it conditions the sign of momentum vs mean-reversion returns out of sample.
Design implications: the regime definitions, thresholds (as percentiles), hysteresis parameters, the calibration method and minimum-n rules for APEX.` },
]

const verifyPrompt = (T, out) => `${PRE}\n\nYou are R10 · RED-TEAM VERIFIER. Another agent ran experiment ${T.key}; its structured output is below. Do NOT trust it: reproduce it.
1. Read the report ${EXP}/${T.key}.md and the code.
2. Re-run the key computations yourself, in full or on a representative subset, and confirm the headline numbers.
3. Hunt for:
   - lookahead or leakage: centred windows, future pivots, HTF bars not yet completed, normalisation with full-sample statistics, outcome windows overlapping the feature window;
   - overfitting and undisclosed variants;
   - wrong statistics, e.g. i.i.d. CIs on overlapping samples;
   - data errors: roll gaps, timezone, GC corruption;
   - overclaims in the text.
Fix errors directly in the code and the report where you can. Append "## Red-team verification (R10)" to the report with what you reproduced, what you corrected and your verdict.

EXPERIMENT OUTPUT (JSON): ${JSON.stringify(out || {}).slice(0, 10000)}`

const res = await pipeline(
  TRACKS,
  (T) => agent(`${PRE}\n\nROLE: ${T.role}. KEY: ${T.key}.\n\n${T.task}`, { label: `exp:${T.key}`, phase: 'Experiment', schema: EXP_OUT }),
  (out, T) => agent(verifyPrompt(T, out), { label: `verify:${T.key}`, phase: 'Verify', schema: VER_OUT }).then(v => ({ key: T.key, out, v })),
)
return res.filter(Boolean).map(r => ({ key: r.key, summary: r.out ? r.out.summary.slice(0, 1500) : 'failed', findings: r.out ? r.out.findings : [], implications: r.out ? r.out.designImplications : [], verify: r.v ? { verdict: r.v.verdict, problems: r.v.problems.slice(0, 6), corrections: r.v.corrections.slice(0, 6) } : null }))
