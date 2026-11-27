export const meta = {
  name: 'apex-p2-empirical-a',
  description: 'APEX Phase 2 empirical research (A): forecast-path methods, signal candidates vs baselines after costs, and the validation statistics library — each re-run by a red-team verifier',
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
- Governing requirements: ${SPEC}. Read sections 0, 13-16, 20, 21 and 25 at least.
- The existing engine is DOL Engine v2 (${SP}/brief/baseline_v2.pine; design in ${REPO}/README.md).
- The completed research study is in ${STUDY}/*.final.md; its replication scripts live in ${STUDY}/*_tools/. Reuse their data loaders.

DATA:
- Real futures OHLCV is in ${STUDY}/amt_data/cme/<SYM>/: a clone of github axb0306/cme-futures-ohlc with NQ, ES, YM, RTY, GC and CL, files like NQ_1h_*.csv and NQ_1min_*.csv. Check the columns and timezones yourself.
- BTC 1h: ${STUDY}/classic_tools/btc_1h.csv.
- A data lab is building standardised data plus a loader at ${CODE}/apexdata.py, with a catalog at ${APEX}/validation/data_catalog.json. Use them if they are ready; otherwise load the raw files yourself.
- The study found the GC 1H file corrupted (two contract months interleaved): exclude it or repair it with evidence.
- Python: use ${SP}/apexvenv if it exists. Otherwise create your own venv under ${SP}/venv_<yourkey> with numpy, pandas and scipy (pip is allowed), or reuse ${STUDY}/x1_tools/pylib.
- Keep CPU use moderate: many agents share 4 CPUs. Use nice -n 10 for long jobs.

RESEARCH STANDARD (non-negotiable):
- Pre-register: write the hypothesis, the exact outcome definition, the horizon, the baseline, the metric and the pass criterion in your report BEFORE looking at the results. Never change definitions after seeing results without reporting both versions.
- No lookahead: features use only bars <= t, decisions happen at bar-t close, fills at the next bar's open. Pivots count only from their confirmation bar.
- Walk-forward or chronological train/test splits. Purge and embargo overlapping horizons. Report in-sample and out-of-sample separately.
- Realistic costs per instrument: commission plus slippage in ticks, e.g. NQ 1-2 ticks per side; state your assumptions.
- Report n, effect sizes, confidence intervals (Wilson for proportions, block bootstrap for means) and the number of variants tried. Apply multiple-testing awareness (Holm/BH, Deflated Sharpe when you compare many variants).
- Compare against meaningful baselines.
- NEVER fabricate or round up results. A null result is a valid, valuable outcome.
- Write code to ${CODE}/experiments/<key>/ (no data files; git-ignored outputs go to ${CODE}/experiments/<key>/out/) and the report to ${EXP}/<key>.md.`

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
  { key: 'E1_forecast_paths', role: 'R8 FORECASTING ENGINEER', task: `QUESTION: which method for APEX's ONE forward path (spec section 14; horizons 20, 60 and 120 bars, default 60) genuinely beats a random-walk baseline out of sample, and how should uncertainty be estimated?
Candidates, each computed only from data <= t:
(a) a zero-drift random walk (the baseline);
(b) rolling linear-regression drift extrapolation;
(c) momentum persistence with exponential decay (half-life estimated online);
(d) volatility-scaled drift with sqrt-time scaling and the time-of-day volatility clock;
(e) a state-dependent drift conditioned on a simple regime/bias state, e.g. confirmed-pivot structure bias and a volatility tercile, with drift = the historical mean forward return in that state (estimated on past data only);
(f) target-aware shaping: a bridge toward the nearest DOL-style liquidity level (prior-day high/low, or recent confirmed swing high/low) on the bias side, weighted by the PAST empirical reach rate for that distance, never assuming the target is hit;
(g) a shrinkage blend of the best components toward zero drift.
Evaluate on NQ, ES, YM, RTY, CL and BTC (GC only if repaired), on 5m and 1h where data allows, walk-forward.
Metrics:
- MAE and RMSE of the price at t+h in ATR units vs the random walk (Diebold-Mariano test with HAC errors);
- directional accuracy at h, with a Wilson CI vs 50% and vs a always-up drift baseline;
- path-shape error: the mean absolute error over all steps 1..h;
- rolling out-of-sample residual quantile bands (e.g. 10/50/90%) and their empirical coverage, by horizon and by volatility regime.
Report honestly. If nothing beats the random walk, say so, and recommend how APEX should present the path: for example, as a scenario with honest bands and the drift shrunk toward zero. Design implications must cover the default method, the parameters, the uncertainty method and the minimum sample size before bands are shown.` },
  { key: 'E2_signals', role: 'R1 + R6 SIGNAL RESEARCHER (systematic strategist)', task: `QUESTION: what BUY/SELL signal logic (spec section 13.3: STRONG BUY / BUY / NEUTRAL / SELL / STRONG SELL; FAST and BALANCED modes; confirmation and persistence; NEUTRAL allowed) adds value after costs vs simple baselines?
First study the earlier FAST/BALANCED design in ${APEX}/legacy/XAUUSD_Fast_Balanced_Pro.pine and the MNQ ORB lessons in ${APEX}/legacy/mnq_orb/README.md.
Pre-register a SMALL family of candidates, for example:
- confirmed-structure bias (BOS/CHoCH from confirmed pivots) plus a momentum factor;
- sweep-and-reclaim of prior-day or session liquidity plus a structure confirm;
- a DOL-direction signal (toward the nearest/most reachable liquidity);
- a composite with persistence: K bars for BALANCED, fewer for FAST.
Baselines:
- time-series momentum / EMA trend (e.g. 20/50);
- always-flat and random-entry with the same holding time;
- buy-and-hold over the same period.
Evaluate: next-open fills; exits at a fixed horizon or by structural invalidation (pre-register one); costs; per instrument and timeframe; walk-forward. Report:
- hit rate, average R, profit factor, Sharpe with a bootstrap CI, maximum drawdown, trades per day, and the percentage of bars NEUTRAL;
- the Deflated Sharpe Ratio given the number of variants tried, and PBO (CSCV) across the variant set.
Be honest if nothing beats the baselines out of sample. Design implications: which signal definition, what FAST vs BALANCED should mean concretely, the persistence parameters, and when to stay NEUTRAL.` },
  { key: 'E5_statslib', role: 'R5 QUANT / VALIDATION LIBRARY ENGINEER', task: `Build the reusable validation statistics library ${CODE}/apexstats.py with unit tests in ${CODE}/test_apexstats.py. Run the tests and report the results.
Functions:
- wilson_ci;
- stationary and circular block bootstrap (mean, Sharpe, any statistic);
- the Diebold-Mariano test with Newey-West HAC errors;
- the Brier score with the Murphy decomposition (reliability, resolution, uncertainty), log loss, a reliability-curve table, ECE;
- precision/recall/FPR;
- Sharpe and the Probabilistic Sharpe Ratio; the Deflated Sharpe Ratio (Bailey & Lopez de Prado 2014: expected maximum Sharpe under N trials, with skew/kurtosis correction);
- PBO via CSCV (Bailey et al. 2017);
- Holm and Benjamini-Hochberg;
- a walk-forward splitter with purge and embargo;
- a simple bar-based backtest engine: signals at close, fills at next open, per-instrument tick-size and cost model, fixed-horizon and stop/target exits, trade log, equity;
- a first-passage "level reached within H bars" labeller (high >= level for buy-side, low <= level for sell-side), with a distance-matched random-level baseline generator.
Test every function against known values or closed forms: e.g. the DSR example from the paper if you can verify it, Wilson against statsmodels, bootstrap coverage on synthetic AR(1) data, and PBO on pure-noise strategies (should be about 0.5 or higher).
The report goes to ${EXP}/E5_statslib.md: the API documentation, test results and validated references.` },
]

const verifyPrompt = (T, out) => `${PRE}\n\nYou are R10 · RED-TEAM VERIFIER. Another agent ran experiment ${T.key}; its structured output is below. Do NOT trust it: reproduce it.
1. Read the report ${EXP}/${T.key}.md and the code.
2. Re-run the key computations yourself, in full or on a representative subset, and confirm the headline numbers.
3. Hunt for:
   - lookahead or leakage: centred windows, future pivots, resampling that uses future bars, normalisation with full-sample statistics, fills at the signal bar's close;
   - overfitting: undisclosed variants, parameter search on test data;
   - wrong cost assumptions; wrong statistics, e.g. i.i.d. CIs on overlapping returns;
   - data errors: roll gaps, timezone, GC corruption;
   - overclaims in the text.
4. For a library: run the tests and add adversarial tests of your own.
Fix errors directly in the code and the report where you can. Append "## Red-team verification (R10)" to the report with what you reproduced, what you corrected and your verdict.

EXPERIMENT OUTPUT (JSON): ${JSON.stringify(out || {}).slice(0, 10000)}`

const res = await pipeline(
  TRACKS,
  (T) => agent(`${PRE}\n\nROLE: ${T.role}. KEY: ${T.key}.\n\n${T.task}`, { label: `exp:${T.key}`, phase: 'Experiment', schema: EXP_OUT }),
  (out, T) => agent(verifyPrompt(T, out), { label: `verify:${T.key}`, phase: 'Verify', schema: VER_OUT }).then(v => ({ key: T.key, out, v })),
)
return res.filter(Boolean).map(r => ({ key: r.key, summary: r.out ? r.out.summary.slice(0, 1500) : 'failed', findings: r.out ? r.out.findings : [], implications: r.out ? r.out.designImplications : [], verify: r.v ? { verdict: r.v.verdict, problems: r.v.problems.slice(0, 6), corrections: r.v.corrections.slice(0, 6) } : null }))
