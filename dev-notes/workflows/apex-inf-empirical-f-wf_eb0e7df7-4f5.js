export const meta = {
  name: 'apex-inf-empirical-f',
  description: 'APEX ∞ empirical research (F): ML models vs heuristics with ablation (E15), setup taxonomy performance after costs (E16), multi-horizon forecast targets 5-120 bars (E17) — each re-run by a red-team verifier',
  phases: [
    { title: 'Experiment', detail: 'real-data experiments with pre-registered definitions' },
    { title: 'Verify', detail: 'R10 re-runs the code and checks for leakage, overfitting and fabrication' },
  ],
}
const SP = '/tmp/claude-0/-home-user-m/7ce60006-3639-59b1-8cd3-87355409d58a/scratchpad'
const REPO = '/home/user/m'
const APEX = `${REPO}/apex`
const STUDY = `${SP}/brief/study`
const SPEC = `${REPO}/dev-notes/brief/APEX_INFINITY_SPEC.md`
const EXP = `${APEX}/research/experiments`
const CODE = `${APEX}/validation/python`

const PRE = `PROJECT. You are a specialist on the APEX ∞ team. The team is building an honest, evidence-based Draw-on-Liquidity and quantitative market-intelligence indicator in Pine Script v6.
- Governing spec: ${SPEC}. Read Parts VIII, IX, X, XI, XIX, XX and XXVII at least.
- The existing engine is DOL Engine v2 (${SP}/brief/baseline_v2.pine).
- The completed DOL study is in ${STUDY}/*.final.md.
- Other experiments are in ${EXP}/ (E1 forecast paths, E2 signals, E3 DOL hypotheses, E4 regime calibration, E6-E14). Read any that exist, build on them, and do not duplicate.

DATA:
- ${STUDY}/amt_data/cme/<SYM>/: NQ, ES, YM, RTY, GC and CL, 1h and 1min. GC 1H is known to be corrupted: exclude or repair it with evidence.
- ${STUDY}/classic_tools/btc_1h.csv.
- Loader ${CODE}/apexdata.py and stats library ${CODE}/apexstats.py, if present.
- Python: ${SP}/apexvenv if it exists, else your own venv under ${SP}/venv_<key> (pip allowed; scikit-learn and lightgbm are fine). Use nice -n 10.

RESEARCH STANDARD (non-negotiable):
- Pre-register the hypothesis, population, event time, features, outcome, horizon, benchmark, costs, exclusions, test and validation split BEFORE looking at results.
- No lookahead: features use bars <= t; pivots count from their confirmation bar; HTF values come from completed bars; normalisation uses only past data.
- Chronological train / validation / UNTOUCHED test, plus walk-forward, with purging and embargo for overlapping labels. Never shuffle bars.
- Report n, effect sizes, CIs, the number of variants tried, and DSR/PBO where many variants are compared. Report gross and net separately.
- Compare with the baselines of spec 28.2.
- NEVER fabricate or round up results; null results are valuable.
- Code goes to ${CODE}/experiments/<key>/ (outputs in its out/ subfolder, git-ignored); the report to ${EXP}/<key>.md.
RESUME NOTE: if a partial draft or code exists from an interrupted attempt, read it, verify it, and complete or replace it.`

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
  { key: 'E15_ml_models', role: 'R7 QUANTITATIVE MODELLER (ML)', task: `Spec Part X 18-18.2 and 27.3: does machine learning beat simple heuristics OUT OF SAMPLE, and can anything be deployed honestly in Pine?
Targets, each separately:
(a) a liquidity level (PDH/PDL and the nearest confirmed swing high/low) touched within H bars (a first-passage label);
(b) direction at H;
(c) the net outcome of a simple setup proxy after costs.
Features, all causal: returns, ATR and realised vol, efficiency ratio, momentum factors (consolidated), VWAP distance, distance to liquidity in ATR, FVG presence/size, sweep magnitude, structural state, relative volume, session, regime, range position, HTF alignment (completed bars), path resistance (counts of opposing levels/FVGs).
Models: logistic L2 (the baseline ML), shallow decision tree (depth ≤ 3), gradient boosting (sklearn HistGradientBoosting or LightGBM), kNN, and a Gaussian HMM regime model (hmmlearn) if feasible. Compare them with heuristic baselines: distance+volatility first-passage for (a), zero/trend for (b).
Run walk-forward across instruments and timeframes. Measure: Brier, log loss, AUC, calibration (slope/intercept, ECE), and for (c) net expectancy.
FEATURE-GROUP ABLATION (spec 27.3): structure only, liquidity only, trend only, momentum only, volatility only, volume only, and combined.
Permutation importance and stability across folds.
DEPLOYMENT: if and only if a lightweight model (e.g. logistic with ≤ 15 features, optionally per regime) beats the heuristic baseline out of sample on most instruments with stable coefficients, export the frozen coefficients and feature definitions to ${CODE}/experiments/E15_ml_models/deploy_candidate.json and document how Pine would compute them. Otherwise say clearly that no ML model is justified.` },
  { key: 'E16_setups', role: 'R1+R2 SETUP / SIGNAL RESEARCHER', task: `Spec Part XI 19: measure every setup type's historical behaviour.
Setups:
- trend continuation: pullback, breakout continuation, structural retest, momentum continuation;
- reversal: sweep and reclaim, failed breakout/breakdown, exhaustion reversal, structural reversal (CHoCH), divergence-supported reversal;
- range: range rejection, mean reversion to VWAP/value, failed range extension;
- expansion: compression breakout, volatility expansion, opening-range breakout, structural expansion;
- liquidity destination: target approach, target reached → post-target continuation vs reversal.
For EACH setup, give a formal causal definition (context, trigger, confirmation, invalidation, horizon, target). Measure, per instrument, timeframe, regime and session: frequency, hit rate to target before invalidation, MFE/MAE in ATR, net expectancy after realistic costs (next-open fills), and time to outcome. Compare with matched random-entry baselines.
Test ABSTENTION (19.3): does skipping setups under conflicting evidence, unstable regime, poor R:R, insufficient history or volatility anomaly improve net expectancy and drawdown out of sample?
Test FAST vs BALANCED: confirmation depth and persistence trade-offs.
Apply DSR/PBO across the family. Recommend which setups APEX should emit as BUY/SELL, which only as context, and which to drop.` },
  { key: 'E17_horizons_targets', role: 'R8 FORECASTING RESEARCHER', task: `Spec Part VIII 16.1-16.4: forecast behaviour across horizons H ∈ {5, 10, 20, 40, 60, 80, 100, 120} bars for EACH separate target of 16.2:
- directional (close above the reference after H);
- liquidity (the selected pool touched within H);
- first-passage (target before invalidation);
- magnitude (quantiles of |move|/ATR);
- path (mean absolute path error vs the realised path for the best path method from E1 if it exists, else drift-decay vs random walk);
- trade outcome.
For each target and horizon, measure skill vs the appropriate baseline and calibration out of sample, and show how they change with H. Demonstrate the danger of transferring a 5-bar calibration to 60 bars by applying it and measuring the miscalibration.
Test forecast INVALIDATION rules (16.4: a structural break against the scenario, an opposing sweep with displacement, a vol shock, a regime change). Do invalidated scenarios perform worse afterwards, which would justify withdrawing the displayed path?
Test a Kalman local-trend filter and a regime-conditioned drift as path components vs rolling regression.
Deliver recommended defaults per trading style (Scalping, Day, Swing): the horizon range, uncertainty bands by horizon, and invalidation rules.` },
]
const verifyPrompt = (T, out) => `${PRE}\n\nYou are R10 · RED-TEAM VERIFIER. Another agent ran experiment ${T.key}. Do NOT trust it: reproduce it.
- Read ${EXP}/${T.key}.md and the code. Re-run the key computations, in full or on a representative subset, and confirm the headline numbers.
- Hunt for:
  - leakage: future pivots, incomplete HTF bars, full-sample normalisation or scaling, target overlap across folds without purging, feature selection on test data;
  - overfitting: undisclosed hyperparameter search, the untouched test set used for tuning;
  - wrong statistics; cost errors; overclaims.
- For ML: verify that any deploy_candidate.json is genuinely out-of-sample justified, and that the Pine-computation description is feasible.
- Fix the code and the report where you can. Append "## Red-team verification (R10)" with what you reproduced, what you corrected and your verdict.

OUTPUT (JSON): ${JSON.stringify(out || {}).slice(0, 10000)}`
const res = await pipeline(TRACKS,
  (T) => agent(`${PRE}\n\nROLE: ${T.role}. KEY: ${T.key}.\n\n${T.task}`, { label: `exp:${T.key}`, phase: 'Experiment', schema: EXP_OUT }),
  (out, T) => agent(verifyPrompt(T, out), { label: `verify:${T.key}`, phase: 'Verify', schema: VER_OUT }).then(v => ({ key: T.key, out, v })))
return res.filter(Boolean).map(r => ({ key: r.key, summary: r.out ? r.out.summary.slice(0, 1500) : 'failed', findings: r.out ? r.out.findings : [], implications: r.out ? r.out.designImplications : [], verify: r.v ? { verdict: r.v.verdict, problems: r.v.problems.slice(0, 6) } : null }))
