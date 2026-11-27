export const meta = {
  name: 'apex-p2-empirical-d',
  description: 'APEX Phase 2 empirical research (D): momentum/trend factor redundancy, volume and VWAP features, MTF alignment and intermarket — each re-run by a red-team verifier',
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
- Governing requirements: ${SPEC}. Read sections 0, your domain's sections, 13, 20, 21 and 25.
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
- Use meaningful baselines.
- NEVER fabricate or round up results; null results are valuable.
- Code goes to ${CODE}/experiments/<key>/ (outputs in its out/ subfolder, git-ignored); the report to ${EXP}/<key>.md.`

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
  { key: 'E9_momentum_factors', role: 'R6 MOMENTUM / TREND RESEARCHER', task: `Spec section 8 says the trend and momentum features are supporting evidence and must not be counted as independent votes. Quantify that.
(1) Compute, without lookahead, on several instruments and timeframes:
- EMA20/50/100/200 stack score, EMA slopes (ATR-normalised), EMA separations;
- RSI14, MACD histogram (ATR-normalised), ROC, DMI+/- and ADX;
- the regression-slope t-stat, VWAP deviation in ATR units;
- acceleration (the change of slope), persistence (variance ratio, efficiency ratio).
(2) Measure the redundancy: Spearman correlation matrix, PCA/explained variance, and hierarchical clustering. Propose a minimal orthogonal set (e.g. TREND, MOMENTUM-CHANGE, STRETCH) with exact construction formulas.
(3) Predictive value out of sample:
- the information coefficient (Spearman IC) of each raw feature and each consolidated factor vs the forward H-bar return (in ATR), by regime;
- the incremental value over a trend-only baseline;
- the effect of counting redundant features as separate votes (the vote-inflation demonstration).
(4) Divergence: a formal confirmed-pivot RSI divergence. Does it predict reversal at H beyond the base rate?
Deliver the consolidated factor definitions, their sign and strength by regime, and the recommended weights (or "neutral" where there is no value).` },
  { key: 'E10_volume_vwap', role: 'R4b MICROSTRUCTURE / VOLUME RESEARCHER', task: `Spec section 7 asks for honest volume features. Test them:
(1) Relative volume (vs the same time-of-day average) and volume percentile: is it informative for follow-through after breakouts of liquidity levels, and after sweeps (reclaim vs acceptance)? Measure it out of sample against the base rates.
(2) Session VWAP deviation (in sigma or ATR): does a stretch from VWAP mean-revert or continue at H, by regime and time of day?
(3) Volume-at-price: build session profiles from 1-minute data (POC, VAH/VAL at 70%). Do naked/virgin POCs get revisited more than a distance-matched random level? Do LVNs speed up travel (the bars needed to cross)?
(4) Proxy quality: for instruments with tick data (${STUDY}/smt_data), compare intrabar up/down volume proxies (the tick rule, bulk volume classification, close-location) against the true aggressor-side delta where the tick data has the side, or against the tick rule as a reference. Report the correlation and say honestly what a candle-based "delta" can and cannot tell you.
(5) Missing or bad volume: how do features degrade on FX tick volume or BTC exchange volume, and how should APEX detect a volume-less feed and down-weight (syminfo.volumetype, zero-volume runs)?
Deliver the volume features worth including, their data-quality gating, and those to exclude.` },
  { key: 'E11_mtf_intermarket', role: 'R7 MTF / INTERMARKET RESEARCHER', task: `(1) MTF alignment: structure bias on D, 4H and 1H (and 1H/15m/5m for scalping), each from COMPLETED HTF bars only.
- Do agreement levels (all aligned / mixed / opposed) change the H-bar direction accuracy, or the hit rate of DOL targets in the bias direction, beyond the chart-TF signal alone? Measure out of sample with CIs.
- Quantify the leakage when PROVISIONAL (incomplete) HTF bars are used instead of confirmed ones: the inflated accuracy that is a backtest artefact.
(2) Intermarket:
- rolling return correlations NQ-ES-YM-RTY, ES-GC, ES-CL, GC-CL, and BTC-NQ where the times align. Measure the correlation stability (rolling-window dispersion, Fisher-z CIs, regime breaks).
- Does a reference-symbol signal add out-of-sample predictive value? For example, NQ leading ES, or an SMT divergence at liquidity sweeps (the study smt_inter found what? Extend it).
- How often are reference data misaligned or missing (session differences)?
(3) Design implications: how confidence should be reduced when timeframes disagree (the formula); whether intermarket context deserves a weight or should be display-only; and the default reference symbols.` },
]
const verifyPrompt = (T, out) => `${PRE}\n\nYou are R10 · RED-TEAM VERIFIER. Another agent ran experiment ${T.key}. Do NOT trust it: reproduce it.
- Read ${EXP}/${T.key}.md and the code. Re-run the key computations, in full or on a representative subset, and confirm the headline numbers.
- Hunt for: lookahead or leakage (future pivots, centred windows, incomplete HTF bars, full-sample normalisation); undisclosed variants; i.i.d. CIs on overlapping samples; timezone errors; roll gaps; GC corruption; overclaims.
- Fix the code and the report where you can. Append "## Red-team verification (R10)" with what you reproduced, what you corrected and your verdict.

EXPERIMENT OUTPUT (JSON): ${JSON.stringify(out || {}).slice(0, 10000)}`
const res = await pipeline(TRACKS,
  (T) => agent(`${PRE}\n\nROLE: ${T.role}. KEY: ${T.key}.\n\n${T.task}`, { label: `exp:${T.key}`, phase: 'Experiment', schema: EXP_OUT }),
  (out, T) => agent(verifyPrompt(T, out), { label: `verify:${T.key}`, phase: 'Verify', schema: VER_OUT }).then(v => ({ key: T.key, out, v })))
return res.filter(Boolean).map(r => ({ key: r.key, summary: r.out ? r.out.summary.slice(0, 1500) : 'failed', findings: r.out ? r.out.findings : [], implications: r.out ? r.out.designImplications : [], verify: r.v ? { verdict: r.v.verdict, problems: r.v.problems.slice(0, 6) } : null }))
