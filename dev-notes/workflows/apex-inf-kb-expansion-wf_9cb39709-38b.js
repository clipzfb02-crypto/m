export const meta = {
  name: 'apex-inf-kb-expansion',
  description: 'APEX ∞ knowledge-base expansion: 8 research tracks for topics APEX ∞ adds (econometrics/time series, information theory, ML theory, asset classes, macro/news, exchange mechanics/price discovery/participants, risk mathematics, signal engineering/backtesting/data engineering), each with real-data checks where possible and an independent red-team review',
  phases: [
    { title: 'Research', detail: 'specialists research, test and write A-K template documents' },
    { title: 'Red-team', detail: 'R10 fact-checks, re-derives the maths, re-runs the tests and corrects' },
  ],
}
const SP = '/tmp/claude-0/-home-user-m/7ce60006-3639-59b1-8cd3-87355409d58a/scratchpad'
const REPO = '/home/user/m'
const APEX = `${REPO}/apex`
const KB = `${APEX}/APEX_KNOWLEDGE_BASE`
const STUDY = `${SP}/brief/study`
const SPEC = `${REPO}/dev-notes/brief/APEX_INFINITY_SPEC.md`
const CODE = `${APEX}/validation/python`

const PRE = `PROJECT. You are a specialist on the APEX ∞ research team. The team is building the most rigorous, honest, universal trading-intelligence indicator (Draw-on-Liquidity core) that the available data, mathematics and TradingView Pine Script v6 can support.
- GOVERNING SPEC: ${SPEC}. Read Part I (evidence hierarchy 1.3), your domain's parts, Part XXIII 31.1 (the A-K template) and Part XXVII (prohibitions).
- The knowledge base lives in ${KB}/ (40 folders).
- Related work already exists; read it and build on it rather than duplicating it:
  - knowledge-atlas docs in ${APEX}/MARKET_KNOWLEDGE_BASE/ (some still being written);
  - the DOL research study in ${STUDY}/*.final.md;
  - experiments in ${APEX}/research/experiments/;
  - the inspection in ${APEX}/research/WORKSPACE_INSPECTION.md;
  - the existing engine at ${SP}/brief/baseline_v2.pine.
- Real data for checks:
  - ${STUDY}/amt_data/cme/<SYM>/: NQ, ES, YM, RTY, GC and CL, 1h and 1min (GC 1H is known to be corrupted);
  - ${STUDY}/smt_data/cme (ticks); ${STUDY}/classic_tools/btc_1h.csv;
  - loader ${CODE}/apexdata.py if present.
- Python: ${SP}/apexvenv if it exists, else your own venv under ${SP}/venv_<key> (pip allowed). Use nice -n 10.`

const RULES = `HONESTY AND QUALITY RULES (non-negotiable):
- Never fabricate sources, statistics or test results.
  - Cite only sources you actually opened, or that a study report verified; say which.
  - Label each source type: peer-reviewed, official documentation, educational, or practitioner hypothesis.
  - Mark unverifiable claims "unverified".
- Tag every concept with its evidence level from Part I 1.3:
  - L1 observed;
  - L2 derived measurement;
  - L3 objectively defined event;
  - L4 model interpretation;
  - L5 discretionary hypothesis, never presented as fact.
- Derive the maths and verify it: dimensions, edge cases, and numeric checks in Python where feasible.
- Where a claim can be tested on the available data, TEST it, with pre-registered definitions, no lookahead, chronological splits, n and CIs. Put the code in ${CODE}/kb/<key>/ and report the actual results. Untested claims must say "not tested here".
- Search queries must be generic: never include the user's name, email or repository, or any product name. Concepts only; never copy proprietary code.
- Use the A-K template for every major topic: A Concept, B Foundation, C Mechanism, D Mathematics, E Data, F Implementation (Pine v6 feasibility + an offline research form), G Reliability, H Failure, I Validation (a pre-registered experiment), J APEX integration (which of the 26 modules in Part XIII, and INCLUDE-CORE / INCLUDE-OPTIONAL / RESEARCH-ONLY / EXCLUDE), K Sources.
- Substance over length. No filler. Typical size: 30-80 KB per document.
- Do NOT edit production code (${REPO}/indicators/*, ${APEX}/APEX_ULTIMATE.pine).
RESUME NOTE: if a partial draft exists at your output path from an interrupted attempt, read it, verify it, and complete or replace it.`

const OUT = { type: 'object', properties: {
  files: { type: 'array', items: { type: 'string' } }, summary: { type: 'string' },
  tested: { type: 'array', items: { type: 'object', properties: { claim: { type: 'string' }, result: { type: 'string' }, n: { type: 'string' }, verdict: { type: 'string' } }, required: ['claim', 'result', 'n', 'verdict'] } },
  recommendations: { type: 'array', items: { type: 'object', properties: { feature: { type: 'string' }, decision: { type: 'string', enum: ['INCLUDE-CORE', 'INCLUDE-OPTIONAL', 'RESEARCH-ONLY', 'EXCLUDE'] }, module: { type: 'string' }, evidenceLevel: { type: 'string' }, rationale: { type: 'string' } }, required: ['feature', 'decision', 'module', 'evidenceLevel', 'rationale'] } },
  openIssues: { type: 'array', items: { type: 'string' } } },
  required: ['files', 'summary', 'tested', 'recommendations', 'openIssues'] }
const REV = { type: 'object', properties: {
  verdict: { type: 'string', enum: ['pass', 'pass_with_fixes', 'major_issues'] }, changes: { type: 'array', items: { type: 'string' } },
  reproduced: { type: 'array', items: { type: 'string' } }, residualConcerns: { type: 'array', items: { type: 'string' } }, summary: { type: 'string' } },
  required: ['verdict', 'changes', 'reproduced', 'residualConcerns', 'summary'] }

const TRACKS = [
  { key: 'K1_econometrics_ts', role: 'R5 ECONOMETRICIAN / TIME-SERIES ANALYST', files: [`${KB}/16_ECONOMETRICS/ECONOMETRICS.md`, `${KB}/17_TIME_SERIES/TIME_SERIES.md`],
    task: `Spec Part V 8.6-8.7 and Part VII.
- Regression (OLS, WLS, robust, ridge, lasso, elastic net, logistic, quantile) with diagnostics: R², adjusted R², heteroskedasticity (White/BP), multicollinearity (VIF), autocorrelation (Durbin-Watson, Ljung-Box), HAC errors.
- Time series: stationarity, unit roots (ADF, KPSS, PP), differencing, ACF/PACF, AR/MA/ARMA/ARIMA, GARCH(1,1) and EGARCH/GJR, EWMA, exponential smoothing and state-space form, the Kalman filter (local level/trend), structural breaks (Chow, CUSUM, Bai-Perron), regime shifts (Markov switching), seasonality (intraday/weekly).
- TEST ON REAL DATA:
  - ADF/KPSS on prices vs returns;
  - ACF of returns and of absolute returns (volatility clustering) at 5m and 1h;
  - GARCH(1,1) fits for NQ/ES/CL/BTC, with persistence α+β and out-of-sample vol-forecast skill vs EWMA vs ATR;
  - a Kalman local-trend vs rolling-regression slope as a trend estimator (out-of-sample error);
  - structural-break tests on volatility.
- Conclude which tools APEX should use in Pine (feasible online forms) vs research-only.` },
  { key: 'K2_information_theory', role: 'R5b INFORMATION-THEORY RESEARCHER', files: [`${KB}/18_INFORMATION_THEORY/INFORMATION_THEORY.md`],
    task: `Spec Part V 8.8: Shannon entropy, conditional entropy, mutual information, information gain, cross-entropy, surprise, complexity (permutation entropy, sample entropy, Lempel-Ziv), signal-to-noise ratio.
- Proper estimators and their biases: plug-in vs Miller-Madow, binning choices, the KSG estimator for continuous variables.
- TEST ON REAL DATA (pre-registered, chronological):
  - Does rolling permutation entropy or sample entropy of returns add OUT-OF-SAMPLE information about the next-H absolute move or direction, beyond realised volatility and the efficiency ratio? Use MI with bootstrap null distributions and incremental log-loss of a simple model.
  - Estimate the MI between candidate APEX features and the forward outcome as a model-free ranking. Compare it with correlation-based rankings.
- Never interpret high entropy as automatically bullish, bearish or random.
- Conclude what, if anything, APEX should use.` },
  { key: 'K3_machine_learning', role: 'R7 MACHINE-LEARNING THEORIST', files: [`${KB}/19_MACHINE_LEARNING/MACHINE_LEARNING.md`],
    task: `Spec Part X. For EVERY method listed in section 18, document the mathematical basis, data requirements, complexity, interpretability, overfitting risk, temporal-validation needs, inference requirements and deployment limits in Pine v6.
- Methods: linear/logistic, trees, RF, GBM, XGBoost, LightGBM, CatBoost, SVM, kNN, naive Bayes, HMM, GMM, clustering, PCA, autoencoders, NNs, RNN/LSTM/GRU, TCN, transformers, RL.
- What can genuinely run in Pine: fixed-coefficient logistic, small trees as nested ifs, kNN over a bounded buffer (the cost), online SGD logistic (whether feasible within loop/time limits), HMM forward filtering with fixed parameters.
- Evidence from the literature on ML for intraday price prediction, with honest effect sizes and the replication crisis (López de Prado; Gu, Kelly & Xiu for cross-sectional returns, and why it does not transfer to single-instrument intraday).
- Feature-leakage traps specific to trading.
- A deployment protocol: train externally, walk-forward, freeze, export coefficients, monitor on-chart.
- Coordinate with experiment ${APEX}/research/experiments/E15_ml_models.md if it exists. Cite its results; do not duplicate it.` },
  { key: 'K4_asset_classes', role: 'R4a ASSET-CLASS SPECIALIST', files: [`${KB}/24_FOREX/FOREX.md`, `${KB}/25_COMMODITIES/COMMODITIES.md`, `${KB}/26_EQUITIES/EQUITIES.md`, `${KB}/27_CRYPTO/CRYPTO.md`, `${KB}/23_FUTURES/FUTURES.md`],
    task: `Spec 2.1 and 24. Write FIVE documents, one per asset class: futures, forex, commodities, equities and ETFs, crypto spot and perpetuals.
For each class cover:
- instrument mechanics (contract specs, tick size and value, multiplier, expiration, settlement, margin, leverage, basis, funding, carry, contango/backwardation, roll yield, dividends and corporate actions);
- sessions, holidays and data quirks (FX tick volume; fragmented equity volume and its consolidated tape; crypto exchange-specific volume and 24/7 sessions; perpetual funding);
- typical volatility and tick-to-ATR scales (MEASURE on the available data where possible: NQ/ES/YM/RTY/GC/CL/BTC);
- what TradingView exposes in syminfo.* for each (verify against the docs mirror ${SP}/docsrc);
- how each APEX calculation must adapt (no fixed point thresholds; ATR and tick normalisation; session templates; volume-quality gating);
- risks such as roll gaps, limit moves, weekend gaps and funding spikes.
Be explicit about where APEX cannot be validated because no data is available, e.g. equities, ETFs and options.` },
  { key: 'K5_macro_news', role: 'R7b MACRO / INTERMARKET / EVENT-RISK RESEARCHER', files: [`${KB}/29_MACROECONOMICS/MACROECONOMICS.md`],
    task: `Spec Part VII 15 and 15.1.
- Interest rates, inflation, employment, central-bank policy, yields and curves, the dollar, commodity supply/demand, breadth, risk-on/off, cross-asset correlation, basis, volatility indices.
- The documented intraday effects of scheduled releases (CPI, NFP, FOMC, inventory reports, earnings) on futures volatility, with literature effect sizes (e.g. Andersen-Bollerslev announcement effects; Ederington & Lee).
- What a Pine indicator can and cannot know: no calendar feed. Design manual event windows (inputs) and an event-risk exclusion label; never invent timestamps.
- TEST ON REAL DATA: the time-of-day volatility signature around 08:30 ET and 14:00 ET on the CME data. Dates of known releases may be inferred ONLY from public schedules you can actually fetch; otherwise test only the unconditional 08:30/10:00/14:00 ET volatility bumps.
- Rolling correlation stability among the instruments we have, by regime.
- Conclude how APEX treats macro context: display-only, a confidence reducer, or excluded.` },
  { key: 'K6_exchange_discovery', role: 'R1b FINANCIAL MARKET SCIENTIST (exchange mechanics, price discovery, participants)', files: [`${KB}/01_MARKET_FOUNDATIONS/MARKET_PARTICIPANTS_AND_INSTRUMENTS.md`, `${KB}/02_EXCHANGE_MECHANICS/EXCHANGE_MECHANICS.md`, `${KB}/04_PRICE_DISCOVERY/PRICE_DISCOVERY.md`],
    task: `Spec 2.1-2.3 and 4.
- MARKET_PARTICIPANTS_AND_INSTRUMENTS.md: every instrument type in 2.1, including options, fixed income, swaps and CFDs (mechanics and relevance to APEX); every participant group in 2.2, with what is observable vs only inferable (L5). Never invent participant intent.
- EXCHANGE_MECHANICS.md:
  - centralised exchanges vs fragmented equity markets vs OTC/ECNs;
  - matching engines, price-time priority vs pro-rata (CME uses both for different products; cite CME documentation if reachable);
  - continuous double auction; opening and closing auctions; halts, price limits, circuit breakers (CME velocity logic, equity LULD);
  - market-data feeds; why volume differs between providers; and what this implies for TradingView data.
- PRICE_DISCOVERY.md: theory (Hasbrouck information shares, Gonzalo-Granger), futures-leads-spot evidence, discovery around the open, and what OHLCV can reveal. TEST: does ES/NQ lead-lag exist at 1m in our data (cross-correlation of returns, with CIs)?` },
  { key: 'K7_risk_math', role: 'R4c RISK-MATHEMATICS SPECIALIST', files: [`${KB}/21_RISK_MANAGEMENT/RISK_MATHEMATICS.md`],
    task: `Spec Part XII 20-20.3.
- Risk per trade, position sizing (fixed dollar, percent of equity, volatility, fixed fractional, Kelly and fractional Kelly with estimation-error effects, drawdown-aware sizing), stop distance, R:R, EV including costs, win rate vs payoff.
- Drawdown statistics, recovery factor, profit factor, Sharpe/Sortino/Calmar (exact formulas and annualisation pitfalls with intraday data and overlapping trades), VaR and CVaR (historical, parametric, Cornish-Fisher), tail risk, risk of ruin (closed forms and Monte Carlo), exposure, correlated risk.
- TEST: Monte Carlo of risk of ruin and drawdown distributions for representative strategy statistics; demonstrate that "high win rate but negative EV" arises from realistic payoffs and costs.
- APEX's risk panel must be informational, never a promise. Specify exactly what it may display and how it is labelled (incomplete when inputs are missing).` },
  { key: 'K8_signal_bt_data', role: 'R10b SIGNAL / BACKTEST / DATA ENGINEER', files: [`${KB}/31_SIGNAL_ENGINEERING/SIGNAL_ENGINEERING.md`, `${KB}/32_BACKTESTING/BACKTESTING.md`, `${KB}/35_DATA_ENGINEERING/DATA_ENGINEERING.md`],
    task: `Spec Parts XI, XIX and XX.
- SIGNAL_ENGINEERING.md:
  - the setup taxonomy of 19: every setup with its definition, context, trigger, confirmation, invalidation, horizon, target and failure conditions;
  - the 8-stage signal architecture of 19.1 as a formal state machine;
  - persistence, cooldown, hysteresis and duplicate prevention (19.2);
  - abstention rules as first-class outputs (19.3);
  - FAST vs BALANCED semantics.
  Coordinate with experiment ${APEX}/research/experiments/E16_setups.md if it exists, and cite its results.
- BACKTESTING.md:
  - the chronological methodology (train/validation/untouched test, walk-forward, purging and embargo);
  - the baselines of 28.2; the metrics of 28.3 and 28.4 with formulas; the overfitting controls of 28.5 (DSR, PBO, data snooping, White's Reality Check / Hansen SPA);
  - realistic fills (next-open, stop slippage, limit non-fill), gross vs net.
  Reference the stats library ${CODE}/apexstats.py if present.
- DATA_ENGINEERING.md: data sourcing, cleaning, session-aware resampling, roll handling (back-adjusted vs ratio vs unadjusted), timezone/DST, survivorship, corporate actions, and documenting provenance. Reference ${APEX}/research/DATA_CATALOG.md if present.` },
]

const reviewPrompt = (T, out) => `${PRE}\n\n${RULES}\n\nYou are R10 · INDEPENDENT RED TEAM. You did not write these files: ${T.files.join(', ')} (by ${T.role}). Try to break them.
1. Completeness: the A-K template; every spec item for the domain.
2. Fact-check against the sources; open them. Mark unverifiable claims.
3. Re-derive the maths and recompute at least two numeric examples.
4. RE-RUN the author's tests (code in ${CODE}/kb/${T.key}/) and confirm the numbers. Check for lookahead and leakage.
5. Check the evidence levels (L1-L5) and the source-type labels. Remove overclaims.
6. Check Pine-feasibility claims against the docs mirror ${SP}/docsrc.
Fix the files in place. Append "## Red-team review (R10)" listing the changes, what you reproduced and the residual concerns.

AUTHOR OUTPUT (JSON): ${JSON.stringify(out || {}).slice(0, 9000)}`

const res = await pipeline(TRACKS,
  (T) => agent(`${PRE}\n\n${RULES}\n\nROLE: ${T.role}. KEY: ${T.key}. OUTPUT FILES: ${T.files.join(', ')}.\n\n${T.task}`, { label: `kb:${T.key}`, phase: 'Research', schema: OUT }),
  (out, T) => agent(reviewPrompt(T, out), { label: `redteam:${T.key}`, phase: 'Red-team', schema: REV }).then(r => ({ key: T.key, out, r })))
return res.filter(Boolean).map(x => ({ key: x.key, summary: x.out ? x.out.summary.slice(0, 1200) : 'failed', tested: x.out ? x.out.tested.length : 0, review: x.r ? { verdict: x.r.verdict, concerns: x.r.residualConcerns.slice(0, 5) } : null }))
