# Scoring, online learning and calibration: study for DOL Engine v2

Domain: how the engine should combine its scoring pillars, learn from its own accuracy ledger, and calibrate the
Probability of Touch (PoT) without look-ahead or overfitting. Line numbers refer to
`/tmp/claude-0/-home-user-m/7ce60006-3639-59b1-8cd3-87355409d58a/scratchpad/brief/baseline_v2.pine`
(identical to `indicators/dol_engine.pine`).

Reproducible study code and raw outputs:
`/tmp/claude-0/-home-user-m/7ce60006-3639-59b1-8cd3-87355409d58a/scratchpad/brief/study/calib_ml_tools/`
(`cand_learn.py`, `analyze.py`, `pooled_lift.py`, `lodo.py`, `pickers.py`, `calmult_null.py`, `peek_sim.py`, `out_*.txt`).

Research note: the Firecrawl credit allowance ran out partway through. The remaining literature was checked with WebSearch. WebFetch could not resolve
bashtage.github.io, fmg.ac.uk or core.ac.uk, so the exact out-of-sample p-values of Sullivan, Timmermann and White (1999) are
cited at the design level only.

---

## 0. Key findings (read this first)

1. **The distance-matched baseline is already an excellent probability forecaster.** In an engine-like replica (pivot
   liquidity, external pools / previous-day high-low, FVG near edges; strict trade-through for pools, touch for FVGs; the engine's
   own empirical excursion surface with the analytic prior, `f_potBase` 1313-1322), the random-level probability had a
   calibration slope of **0.93-1.04** on 13 of 14 datasets (6 CME futures on 5-min and 1-hour bars, EURUSD 1-hour, S&P 500 daily; 76,181 candidate probes).
   The one exception, GC 1-hour, has corrupted data: roll gaps, as the quant_pot study also found.
2. **No learner beat that baseline out of sample on clean data.** Prequential (predict at open, learn at resolution)
   log-loss change versus the baseline, on 13 clean datasets:
   - Bayesian online probit (adPredictor-style), prior sd 0.15, tempered updates: **−0.15% to −0.79%**.
   - Unregularised online logistic SGD: **−3.6% to −5.5%**. Never ship this.
   - Naive-Bayes multiplicative feature lifts (the ICT-1 design): **−0.6% to −2.1%**.
   - Engine-style family multiplier (`f_calMult`, learned from selected targets): **−0.2% to −1.8%**.
   - Empirical-Bayes family multiplier: **−0.1% to −1.3%**.

   Only on the broken GC 1-hour base did learning help, by **+8.8% to +11%**.
3. **A *safe* learner is possible: gate it, or mix it, on prequential log-loss.** Both variants keep the GC 1-hour gain and cost almost nothing elsewhere:
   - A gate that applies the learner only once its running log-loss beats the baseline: **0.00% to −0.26%** on the 13 clean sets, **+8.8%** on GC 1-hour.
   - A two-expert exponential-weights mixture (η = 0.25, fixed share 0.005): **−0.32% to +0.01%** on the 13 clean sets, **+10.5%** on GC 1-hour.

   So the learner's real job is to **protect** the forecast against a broken or mis-specified base, and to **measure**. It is not a source of hidden alpha.
4. **`f_calMult` (1376-1382) is mostly noise.** Under a true null (every family lift = 1, with overlap clustering), the engine formula
   `((k+2)/(e+2)) / ((K+2)/(E+2))`, clamped to [0.8, 1.2] after n ≥ 10, deviates from 1 by ≥ 10% in:
   - **66%** of families at n = 10,
   - **47%** at n = 40,
   - **33%** at n = 80.

   It sits at the clamp **38%** of the time at n = 10. Because it multiplies the whole score, a 10% swing moves a score of 50 by
   5 points, which is more than the 4-point switch hysteresis (147). It also learns only from *selected* targets, which is bandit
   feedback: a down-weighted family is selected less and cannot recover. An overlap-aware empirical-Bayes posterior that only applies
   once a time-uniform test is passed removes this noise.
5. **The EDGE verdict is subject to "peeking".** `zEdge ≥ 2 → ✓ EDGE` (2390) is re-evaluated after every booked trial. Under the null, the
   chance of ever showing "✓ EDGE" is:
   - **10%** within 100 trials,
   - **15%** within 300,
   - **20%** within 1,000.

   The chance of ever showing "~ WEAK" is 45-65%. A fixed single look gives 2.1-2.6%. A two-sided normal-mixture confidence sequence (Howard et al. 2021, eq. 14) keeps
   the ever-crossing rate at ≤ 1.4%.
6. **Feature lifts exist, but they are small, unstable and do not transfer between symbols.** Pooled offset-logistic over 70k probes, cluster-robust (5-min / 1-hour):
   - External pools (HTF pivots, previous-day H/L): **−0.14 / −0.27** logit (t −1.1 / −2.9).
   - Confluence with PDH/PDL/day open/day EQ: **−0.25 / −0.18** (t −2.7 / −1.7).
   - Equal highs/lows: **+0.08 / +0.29** (t +0.7 / +3.6).
   - Draw alignment: **−0.03 / −0.11** (t −1.1 / −2.4).

   Two of these contradict the hand-set pillars: the confluence pillar (weight 15) and the source tier in density both assume these levels are *more* likely to be hit.
   But a cross-market prior fitted leave-one-dataset-out *hurt* held-out log-loss by **−1.17%** on average. Lifts must be measured per chart, with
   shrinkage. They must not be hard-coded.
7. **Target choice is a utility decision, not an information edge.** Because PoT is essentially geometry, every picker's realised hit
   rate equalled its baseline (calibrated within ±2 pp, except GC 1-hour). The pickers differ only in *what* they deliver:
   - Max expected reach `d·PoT(d)`: **1.10-1.43 ATR per target** at 36-47% hit rates.
   - The engine-like hand score: 0.86-1.09 ATR at 55-68%.
   - Nearest pool: 0.66-0.93 ATR.

   These ranges are for the 13 intraday and 1-hour sets.

   For driftless Brownian motion, `d·2Φ(−d/s)` peaks at **d = 0.75·σ√H**, where the touch probability is **45%**.
8. **The single most valuable infrastructure is a candidate (shadow) ledger.** It grades every candidate once per H window, not just the
   active DOL. That turns bandit feedback into full information and gives about 2,500-3,500 probes per 5,000 bars (design effect 1.4-2.8).
   The standard error of an excess hit rate is then **0.9-1.9 pp**, against 1.4-2.4 pp for the active-only ledger (in our replica, which opens *more* active trials than
   the engine). It also enables baselines (nearest, random candidate) and an "ATR delivered" metric.

---

## 1. Concepts (definitions and parameters)

Notation: candidate level i at bar t, distance `d` (ATR), side ±1, horizon H bars. The outcome is `y = 1` if the level is touched
within bars t+1..t+H. Pools require a trade-through (`high > edge` / `low < edge`, matching `touched`, 623). Arrays count a touch (`≥`/`≤`).
`p0 = pBase` is the distance-matched random-level probability (`f_potBase`). `logit(p) = ln(p/(1−p))`, Φ is the normal CDF.

### A. Targets, baselines and labels

**1.1 Distance-matched random-level baseline (offset).**
`p0(d, side, regime) = P(a random level d ATR away on that side is touched within H)`. The engine estimates it from its empirical
excursion surface (`sUp/sDn`, 3 HTF regimes × 61 bins of 0.25 ATR, 1059-1062). It blends in the driftless analytic first-passage prior
with `priorM = 30` pseudo-observations and `nEff = n/(0.6H)` (1303-1322).
- DOL role: this is the *null model*. Anything a liquidity concept adds must show up as `y` exceeding `p0`.
- Parameters: the bin step `bStep = max(maxATR·ejectMult, 10)/60` (307), the gate `nMin = max(150, 20H)` (1289), and the regime split.
- Failure modes: the near-target cap bias (quant_pot W3), discrete grid, overlap, regime dependence, and bad data (roll gaps).

**1.2 Offset model.** Every learner below predicts *relative to* p0:
`logit P(y=1|x) = logit(p0) + βᵀx` (logistic), or `P = Φ(Φ⁻¹(p0) + μᵀx)` (probit).
β = 0 reproduces the baseline exactly. That makes "no information" the default and makes every learned coefficient a *lift* beyond distance.
This is the formal version of the engine's "edge over a random level" idea.

**1.3 Label choices.**
- (a) *Touch within H*: the engine's ledger (`f_step` 1434-1459).
- (b) *Race*: target before invalidation (`raceSt`, 1079).
- (c) *Which pool first*: nearest BSL vs nearest SSL.
- (d) *Terminal pool*: the farthest pool reached before reversal.

Key geometric fact: on the same side of price, the **nearest** level is always touched before any farther one, because paths are
continuous. "Which liquidity is taken next" is therefore only a non-trivial question *across* sides (label c, the race). Within a side, the
real question is *how far* the move extends (d).

**1.4 Baselines for selection.** Each is a comparison rule the DOL must beat:
- (i) random level at the same distance (present);
- (ii) nearest candidate pool;
- (iii) nearest pool on the draw side;
- (iv) random candidate from the pool;
- (v) the runner-up by score;
- (vi) the opposite-side nearest pool (for the race).

Only (i) exists in the engine (1313-1322, 1463-1469).

### B. Proper scoring and calibration

**1.5 Proper scoring rules.**
- Brier score `B = mean (p−y)²`.
- Log-loss `LL = −mean[y ln p + (1−y) ln(1−p)]`.

Both are strictly proper: they are minimised in expectation only by the true probability (Gneiting & Raftery 2007). Brier skill score versus a
reference: `BSS = 1 − B/B_ref`. For PoT, use the distance-matched p0 as the reference. Climatology (the overall hit rate) is
too easy, because any model that knows distance beats it.

**1.6 Murphy decomposition and reliability diagram.**
- `B = REL − RES + UNC`, with `REL = Σ_k (n_k/N)(p̄_k − ȳ_k)²` (miscalibration), `RES = Σ_k (n_k/N)(ȳ_k − ȳ)²` (discrimination) and `UNC = ȳ(1−ȳ)` (Murphy 1973).
- Reliability diagram: 5-10 bins of forecast, mean forecast against observed rate, with consistency bars from resampling (Bröcker & Smith 2007).
- ECE: `ECE = Σ (n_k/N)|p̄_k − ȳ_k|`.
- Calibration slope: the logistic regression `y ~ a + b·logit(p)`. b < 1 means over-confident.

**1.7 Platt scaling / intercept recalibration.**
- Full form: `p' = σ(a + b·logit p)`, fitted by maximum likelihood with smoothed targets `y+ = (N+ + 1)/(N+ + 2)`, `y− = 1/(N− + 2)` (Platt 1999).
- One-parameter version (intercept only, with a prior of m pseudo-trials at the model mean `P̄`): `δ = logit((K + m P̄)/(N + m)) − logit(P̄)`, `p' = σ(logit p + δ)`. The engine
  uses exactly this for races (`f_raceAdj`, 1367-1371, m = 20).
- Calibration helps miscalibrated models, but "is not beneficial, and actually hurts performance when the calibration sets are small" for
  models that are already well calibrated (Niculescu-Mizil & Caruana 2005).

**1.8 Isotonic regression / Venn-Abers.** Isotonic regression fits a monotone step function by pool-adjacent-violators. It beats Platt above about 1,000
calibration points and overfits below that (Niculescu-Mizil & Caruana 2005). Venn-Abers predictors (Vovk & Petej 2014) run isotonic
regression twice (with the test point labelled 0 and 1) to output an interval `[p0, p1]` that is guaranteed to be calibrated in the online exchangeable setting. Merged as
`p = p1/(1 − p0 + p1)`. Not recommended here: ledger sizes are small, outcomes overlap (not exchangeable), and the cost in Pine would be O(n) per bar.

**1.9 Beta / logistic calibration variants.** Beta calibration `logit p' = a ln p − b ln(1−p) + c` (Kull et al. 2017) and temperature scaling
(Guo et al. 2017) are 2-3-parameter families. They add nothing here over Platt at ledger scale.

### C. Shrinkage and small samples

**1.10 Beta-binomial posterior.** With a prior `Beta(m·p_prior, m·(1−p_prior))`, the posterior mean after k hits in n trials is `(k + m p_prior)/(n + m)`.
m is the prior strength in pseudo-trials. Wilson's score interval (`f_wilson`, 491-503) is the frequentist counterpart.

**1.11 Poisson-gamma lift shrinkage (the right form for "hits vs expected").** Let `k` = hits and `e = Σ p0` = expected hits. Model
`k ~ Poisson(λ·e)` with prior `λ ~ Gamma(α, α/λ0)`; the posterior mean is `(k + α λ0)/(e + α)`.
The engine's `(k+2)/(e+2)` is this with α = 2 and λ0 = 1: a prior worth only two expected hits, so it barely shrinks.
- Choosing α from the believed spread of true lifts: prior sd of λ = λ0/√α. A ±10% spread gives α ≈ 100; ±13% gives α ≈ 60.
- Overlapping trials: divide k and e by the design effect `deff` before combining.

**1.12 Empirical Bayes / James-Stein partial pooling.** Shrink each family's estimate toward the pooled mean by `B_g = s_g²/(s_g² + τ²)`, where
τ² is the between-family variance net of sampling noise: `τ̂² = max(0, Var_between − mean s_g²)` (Efron & Morris 1975, where total
squared error fell from 17.56 to 5.01 in the baseball example). With only 4 families, τ² is poorly estimated. A fixed α (1.11) plus a significance gate (1.21) is
more robust.

**1.13 Minimum-sample rules.** Until `n_eff = n/deff` reaches about 30, show a provisional marker ("~", as the MQLSoftware Liquidity Map does)
and do not let estimates drive the score. Replace hard cliffs such as `n ≥ 10 → full effect` (1382) with continuous weights `n_eff/(n_eff + m)`.

### D. Online learners

**1.14 Online logistic regression (SGD / AdaGrad / FTRL).** Per sample: `w ← w + η(y − p)x − ηλ(w − w0)`.
- AdaGrad uses per-coordinate `η_j = η0/√(Σ g_j²)` (Duchi et al. 2011).
- FTRL-Proximal adds L1/L2 terms and per-coordinate rates (McMahan et al. 2013).
- Weakness: the fixed step size never stops adapting to noise. A constant η of 0.05 cost 3.6-5.5% log-loss in our test.

**1.15 Bayesian online probit (adPredictor; Graepel et al. 2010).** Each weight has a Gaussian posterior `N(μ_j, v_j)`. The prediction is
`P(y=1|x) = Φ((o + μᵀx)/Σ)`, with `Σ² = 1 + Σ_j x_j² v_j` and offset `o = Φ⁻¹(p0)`. For a resolved sample with `t = ±1`, let
`z = t(o + μᵀx)/Σ`, `v(z) = φ(z)/Φ(z)` and `w(z) = v(z)(v(z) + z)`. Then:
- `μ_j ← μ_j + t·x_j·(v_j/Σ)·v(z)`
- `v_j ← v_j·[1 − x_j²·(v_j/Σ²)·w(z)]`
- Dynamics toward the prior with rate ε: `v_j' = v0·v_j/((1−ε)v0 + ε v_j)` and `μ_j' = v_j'·((1−ε)μ_j/v_j + ε μ0/v0)`.

Shrinkage toward the prior mean μ0 is automatic: the step size is proportional to the remaining uncertainty `v_j`.
- Graepel et al. report relative information gain of 61.2% for adPredictor against **−41.5%** for uncalibrated naive Bayes (33.9% after calibration) on Bing click-through prediction.
- Overlapping samples break the independence assumption. Temper each update by ω < 1 (we use ω = 0.25).

**1.16 Bayesian logistic with diagonal Laplace (Chapelle & Li 2011).** Batch MAP with prior `N(m_i, 1/q_i)`, then
`q_i ← q_i + Σ_j x_ij² p_j(1−p_j)`. This is the logistic analogue of 1.15, and it gives Thompson sampling for free. It needs an inner
optimisation, so 1.15 is simpler in Pine.

**1.17 Naive Bayes / multiplicative lifts.** `P ∝ p0·Π_b L_b` over active feature bits. This assumes conditional independence, so correlated features
are double-counted. Naive Bayes reaches its (higher) asymptotic error with O(log n) samples, against O(n) for logistic regression (Ng & Jordan 2002), and is poorly calibrated
(Domingos & Pazzani 1997; Graepel et al. 2010 numbers above). ICT-1 (`ict_liq.md`) and the `f_ctxMult` helper (`ict_pd.md`) are of
this type. They cost 0.6-2.1% log-loss in our test.

**1.18 Elo / Glicko / Bradley-Terry.** Elo's update `R ← R + K(S − E)`, with `E = σ((R_a − R_b)/s)`, is SGD on the Bradley-Terry log-likelihood.
K is the learning rate (Király & Qian 2017). Glicko adds a rating deviation, which makes it an approximate Bayesian filter like 1.15. TrueSkill is the full
message-passing version. Chatbot Arena moved from Elo to batch/online Bradley-Terry for stability. For the DOL, "families or levels competing in races" is just
1.15 with a pairwise design, so it brings nothing new.

**1.19 kNN / Lorentzian classifiers in Pine.** The best-known example is "Machine Learning: Lorentzian Classification" (inspected from
its public port; concepts only).
- Features: 5 oscillators (RSI, WaveTrend, CCI, ADX).
- Distance: `Σ ln(1 + |x_i − y_i|)`.
- Neighbour search: loops over up to 2,000 past bars and skips indices divisible by 4. It keeps a candidate when its distance is **≥** a running
  threshold, which is reset to the 75th-percentile slot of an 8-item list. So it does not return the k *nearest* neighbours.
- Label: `src[4] < src[0] ? short : long`. That is the (negated) *past* 4-bar move of the same bar whose features are stored, not a future move.
  So the model maps current features to the contemporaneous reversal sign. That is not look-ahead, but it is not the forecast it is described as.
- Cost: O(2000·F) per bar.

For PoT the principled kNN-like estimator is the engine's own histogram surface. That is a kernel estimator on 1-2 dimensions (distance, regime),
and it is fine. Beyond 2-3 conditioning dimensions, histogram/kNN estimators suffer from the curse of dimensionality and overlap. Use partial pooling
(quant_pot QPOT-03) instead.

**1.20 Safe aggregation (prediction with expert advice).** Weights `w_e ∝ w_e·p_e(y)^η` over experts e (base, learned model). Under log-loss the
Bayes mixture (η = 1) has regret ≤ ln N against the best expert on *any* sequence (Cesa-Bianchi & Lugosi 2006). Tempering η < 1
multiplies the bound by 1/η. "Fixed share" mixes in α/N of uniform weight each step, so it can track a best expert that changes over time
(Herbster & Warmuth 1998). A gate is the hard-threshold variant: use the model only while its cumulative log-loss is below the base's.

### E. Ranking and decision

**1.21 Learning to rank.** There are three families:
- Pointwise: regress or classify each item.
- Pairwise: RankNet, `P(i ≻ j) = σ(s_i − s_j)` (Burges et al. 2005).
- Listwise: ListNet, a softmax "top-one" probability with Plackett-Luce cross-entropy (Cao et al. 2007); McFadden's conditional logit is the econometric twin.

Listwise and pairwise losses pay off when the utility is position-based (for example NDCG). The DOL utility *decomposes per candidate*: the value of
showing candidate i depends only on i's own outcome. Bayes decision theory then says to rank by expected utility,
`argmax_i E[U_i] = argmax_i P_i·u_i`, which needs *calibrated pointwise* probabilities and an explicit utility u_i. So the correct
"learning to rank" for the DOL is 1.2 plus 1.22.

**1.22 Expected reach (utility of a target).**
- If the trader's value from a target is the distance captured when it is hit: `E[U] = d·P(hit within H | d)`.
- For driftless Brownian motion with horizon scale s = σ√H: `d·2Φ(−d/s)` is maximised at **d* = 0.752 s**, where P = 0.452 and E = 0.340 s (computed numerically, see §2.2).
- With the empirical surface: `d* = argmax_j (j·bStep)·S_j/n`.

Under a martingale *no* target choice changes the expected P&L of a trade (optional stopping). So this is a preference over hit rate and distance, not an edge.
The engine's current proximity pillar (linear blend + reach + taper below `minDistATR`, 662-667) is an ad-hoc version of the same trade-off.

**1.23 Optimizer's curse / winner's curse.** When the alternative with the highest *estimated* value is picked, its realised value is
below its estimate on average, even if every estimate is unbiased (Smith & Winkler 2006). Bayesian shrinkage of each estimate before
the argmax removes this. For the DOL: the selected target's PoT and score are biased upward relative to a random candidate's. The
displayed PoT of the *selected* target should therefore be calibrated on *selected* outcomes (QPOT-04 / SMC-1), but only when it demonstrably helps (1.20).

### F. Validity: leakage, overlap, snooping, peeking

**1.24 Prequential evaluation (Dawid 1984).** Forecast each outcome with the state *before* it is known. Score after resolution. Learn
only from resolved outcomes. This is the online equivalent of a walk-forward test, and it is what makes the ledger leak-free.

**1.25 Overlapping labels / sample uniqueness.** H-bar windows that overlap share one price path. There are two remedies:
- Cluster-robust variance: blocks of about 2H bars, as the engine does in `cluSt` (1077, 1463-1469). The design effect is `deff = V_cluster/V_independent`.
- Weight each sample by its average uniqueness (the mean of 1/concurrency over its window; López de Prado 2018, ch. 4).

Purged and embargoed cross-validation (López de Prado 2018, ch. 7) is the batch analogue. In a prequential online setting there is no
train/test split to purge, but the delay between opening and resolving a probe must be respected.

**1.26 Data snooping.** Searching many rules or features and reporting the best inflates significance. White's Reality Check bootstrap corrects for it
(White 2000; applied by Sullivan, Timmermann & White 1999 to the Brock-Lakonishok-LeBaron technical-rule universe). For an indicator that learns many feature
lifts, use few features, strong priors and a single pre-declared skill test.

**1.27 Peeking / sequential testing.** Re-testing `z ≥ 2` after each new sample makes a false "significant" result eventually certain. Over
realistic horizons it happens 10-20% of the time (our simulation, §2.2). Optimizely reported its false-positive rate fell "from over 20% to under 5%" after adopting
always-valid inference (Johari et al. 2017). The fix is a *confidence sequence*: a boundary that holds uniformly over time. For a sub-Gaussian sum S_t with
variance process V_t, the two-sided normal mixture boundary is `|S_t| < sqrt((V_t + ρ)·ln((V_t + ρ)/(ρ α²)))`. It holds for all t at once
with probability ≥ 1 − α (Howard et al. 2021, eq. 14, from Robbins 1970). ρ tunes where it is tightest. With ρ = 10 and α = 0.05 the
boundary is z ≈ 3.0-3.7 for V between 10 and 250.

**1.28 Bandit feedback / selection bias.** A ledger that only grades the *chosen* target observes one arm per decision. Statistics learned from it
are conditioned on the current policy. A family that gets down-weighted is chosen less, so its estimate stops updating. Off-policy evaluation needs
propensities (Li et al. 2011). The simpler fix in this setting is full information: grade *every* candidate (shadow probes), which is cheap because each
probe is a price comparison.

**1.29 Concept drift.** Exponential forgetting of sufficient statistics (half-life in trials), adPredictor dynamics ε, or fixed share.
In our test, forgetting (ε = 10⁻³) made the Bayesian probit slightly *worse* on 10 of 14 sets, including all six 5-min sets. It was better on 4: ES, CL and RTY 1-hour by ≤ 0.2 pp of log-loss, and the broken GC 1-hour (+11.1% vs +8.8%). At these sample sizes, variance mostly dominates drift.

---

## 2. Evidence

### 2.1 Literature (numbers and sources)

| Claim | Numbers | Grade | Source |
|---|---|---|---|
| Bayesian online probit with Gaussian weights, closed-form updates, prior-centred shrinkage, dynamics toward prior | RIG 61.24% / AUC 95.6% vs naive Bayes −41.54% (33.86% calibrated) / AUC 89.4% | strong (industrial scale, peer-reviewed) | Graepel et al. 2010, ICML |
| Platt vs isotonic; calibration can hurt well-calibrated models on small calibration sets | isotonic ≥ Platt only from ≈1,000 points; for already-calibrated models "calibration is not beneficial, and actually hurts performance when the calibration sets are small" | strong | Niculescu-Mizil & Caruana 2005, ICML |
| Platt smoothed targets | y+ = (N+ + 1)/(N+ + 2), y− = 1/(N− + 2) | strong | Platt 1999 |
| Generative (naive Bayes) vs discriminative (logistic) | NB approaches its higher asymptotic error in O(log n) samples vs O(n) for LR | strong (theory + experiments) | Ng & Jordan 2002, NIPS |
| Optimizer's curse | the chosen alternative disappoints on average even with unbiased estimates; Bayesian shrinkage fixes it | strong | Smith & Winkler 2006, Management Science 52(3) |
| Peeking inflates false positives; always-valid inference | Optimizely false-positive rate "from over 20% to under 5%" after mSPRT | strong | Johari, Pekelis & Walsh 2017/2022; Johari et al. KDD 2017 |
| Normal-mixture confidence sequence | `u(v) = sqrt((v+ρ) ln((v+ρ)/(ρα²)))`, two-sided, time-uniform | strong (theory) | Howard, Ramdas, McAuliffe & Sekhon 2021, Ann. Stat. (arXiv 1810.08240), eq. 14 |
| Mixture of experts, log-loss regret | Bayes mixture regret ≤ ln N on any sequence; fixed share tracks switches | strong (theory) | Cesa-Bianchi & Lugosi 2006; Herbster & Warmuth 1998 |
| Partial pooling | total squared error 17.56 → 5.01 (baseball) | strong | Efron & Morris 1975, JASA |
| Elo = SGD on Bradley-Terry | K = learning rate | strong (theory) | Király & Qian 2017 (arXiv 1701.08055) |
| Venn-Abers | calibrated interval output; merged `p1/(1−p0+p1)`; isotonic more prone to overfit than Platt when data are scarce | moderate-strong | Vovk & Petej 2014 (UAI); Vovk, Petej & Fedorova 2015 (NIPS) |
| Overlapping labels | average uniqueness weights; purging + embargo | moderate (textbook) | López de Prado 2018, chs. 4 and 7 |
| Data snooping in technical rules | Reality Check applied to the BLL rule universe on 100 years of DJIA | strong | Sullivan, Timmermann & White 1999, JF 54(5); White 2000 |
| Pine kNN classifier mechanics | label `src[4] < src[0] ? short : long` (past move); `d ≥ lastDistance` acceptance; skips `i % 4 == 0`; maxBarsBack 2000 | code inspection | public port of "Machine Learning: Lorentzian Classification" (Pine v6 source, lines 335, 395-413) |
| Liquidity-level effects in prior studies | S/R bounce probability rises with prior bounces; decays to 0.5 at about 350 min (1 bounce) / about 900 min (4 bounces) on EURUSD 1-min | moderate | Chung & Bellotti 2021 (arXiv 2101.07410); Garzarelli et al. 2014 (via quant_pot / smc_impl) |
| Sibling studies in this project | the D vector is 49.9-51.6% for "which side first", the same as a random walk; an 11-feature logistic learner is *worse* than a coin out of sample (47.8-49.6%); structure features add ±2-4 pp at most, with signs that flip | moderate | `ict_struct.md` §2.2, `bias_dol.md` §0 |

### 2.2 Our experiments (moderate evidence: reproducible, 14 datasets)

**Data.** CME ES, NQ, CL, GC, RTY and YM: 5-min bars (resampled from 1-min, Jan-Apr 2026, about 16.8k bars each) and 1-hour bars (Mar 2025-Apr 2026,
about 6k bars each). EURUSD 1-hour (5k bars). S&P 500 daily (1999-2019, 5k bars; H = 10). Same files as the other study reports.

**Replica (`cand_learn.py`).**
- Candidate families:
  - fam 0: chart pivots, L = 5;
  - fam 1: external: L = 20 pivots and previous-day high/low;
  - fam 2: FVG near edges with gap ≥ 0.1 ATR.
- Pools: equal highs/lows merge to the outermost print within 0.1 ATR. Tests are counted as in `track` (650-658).
- Coil and inducement as in 888-895.
- Engine-like pillars: fresh, confluence (PDH/PDL/day open/day EQ within 0.35 ATR), density with tier, draw from a structure proxy.
- Candidate range: 0.25-10 ATR.
- Probes: one per level per H bars (non-overlapping per level).
- Selected trials: an engine-like active target (max hand score on the draw side), re-opened as in step 20.
- Baseline `p0`: the engine's surface plus analytic prior (`f_potBase` logic).
- Learners: updated **only at resolution bars**, predictions made **at open** with the state at that time. This is strictly prequential: no outcome is used before its resolution bar.

**(a) Prequential log-loss vs the baseline (%; positive is better; after a 300-probe burn-in)** (`out_analyze.txt`)

| Dataset | n probes | BP (Bayes probit) | SGD (no prior) | NB lifts | EB family | MIX(BP) | GATE(BP) | Selected excess (pp) | Selected recal |
|---|---|---|---|---|---|---|---|---|---|
| ES 5m | 8102 | −0.39 | −4.16 | −1.02 | −0.10 | −0.14 | 0.00 | +0.8 | −0.12 |
| NQ 5m | 8259 | −0.40 | −4.46 | −0.59 | −0.15 | −0.11 | −0.07 | +1.6 | +0.03 |
| CL 5m | 8497 | −0.28 | −4.83 | −0.84 | −0.23 | −0.07 | 0.00 | −0.5 | −0.11 |
| GC 5m | 7369 | −0.40 | −4.11 | −1.25 | −0.18 | −0.11 | −0.26 | −1.0 | −0.05 |
| RTY 5m | 8410 | −0.15 | −4.89 | −1.60 | −0.37 | +0.01 | 0.00 | +2.8 | +0.28 |
| YM 5m | 8233 | −0.30 | −4.92 | −0.77 | −0.21 | −0.10 | −0.04 | +2.5 | +0.15 |
| ES 1h | 3269 | −0.63 | −4.61 | −0.88 | −1.26 | −0.22 | 0.00 | −0.3 | −0.36 |
| NQ 1h | 3228 | −0.52 | −4.78 | −1.66 | −0.74 | −0.18 | 0.00 | −1.0 | −0.35 |
| CL 1h | 2476 | −0.74 | −4.36 | −0.90 | −0.80 | −0.28 | −0.18 | −1.1 | −0.30 |
| GC 1h (roll gaps) | 3915 | **+8.79** | +9.12 | +2.24 | +2.34 | **+10.49** | **+8.79** | −6.9 | **+2.93** |
| RTY 1h | 3436 | −0.53 | −3.63 | −0.58 | −0.13 | −0.15 | 0.00 | −1.8 | −0.08 |
| YM 1h | 3369 | −0.79 | −5.53 | −0.98 | −0.30 | −0.32 | 0.00 | −0.2 | −0.36 |
| EURUSD 1h | 2442 | −0.51 | −4.56 | −1.32 | −0.11 | −0.15 | 0.00 | −3.4 | +0.28 |
| S&P 500 1D (H=10) | 5176 | −0.65 | −4.81 | −2.08 | −0.30 | −0.20 | −0.04 | +1.4 | −0.17 |

Settings:
- BP: prior N(0, 0.15²) on 12 features (bias, external, FVG, EQ, tested, age, prominence, draw, distance residual, confluence, coil, inducement); ω = 0.25.
- SGD: η = 0.05, no prior.
- NB: ICT-1 parameters (featN0 40, ±0.15 per bit, product clamp [0.75, 1.30]).
- EB: α = 60 pseudo-expected-hits, deff 3, ±15%.
- MIX: exponential weights η = 0.25, fixed share 0.005.
- GATE: model only after ≥ 200 resolved probes with lower cumulative log-loss than the base.
- "Selected recal": SMC-1-style intercept shift with m = 20, learned on earlier selected trials.

The baseline's own calibration slope was 0.93-1.04 on all clean sets.

The engine-style `f_calMult` (learned from selected trials, applied as `p0·global lift·cm`) changed log-loss as follows:
- 5-min: ES −0.22, NQ −0.57, CL −0.52, GC −0.28, RTY −0.89, YM −0.57.
- 1-hour: ES −1.21, NQ −0.68, CL −1.09, GC +2.10, RTY −0.62, YM −1.79.
- EURUSD −1.01, S&P 500 −0.63.

The same formula fed by all candidate probes: −0.20 to −0.57 on 5-min (`out_5min.txt`, `out_1h.txt`).

**(b) Pooled feature lifts (offset-logistic, dataset intercepts, cluster-robust t, 2H-bar clusters)** (`out_pooled_lift.txt`)

| Feature (unit) | 5-min, 6 sets, n = 48,870 | 1-hour, 7 sets, n = 22,135 |
|---|---|---|
| External family (HTF pivots, PDH/PDL) | −0.135 (t −1.1) | **−0.270 (t −2.9)** |
| FVG family | −0.023 (t −0.2) | −0.029 (t −0.3) |
| Equal highs/lows (EQ) | +0.082 (t +0.7) | **+0.291 (t +3.6)** |
| Tested ≥ 2 | +0.028 (t +0.2) | **−0.428 (t −2.5)** |
| Confluence (0-1) | **−0.249 (t −2.7)** | −0.178 (t −1.7) |
| Draw alignment (−1..1) | −0.031 (t −1.1) | **−0.107 (t −2.4)** |
| Inducement density | **−0.231 (t −2.9)** | +0.112 (t +0.9) |
| Coil | −0.103 (t −1.7) | **+0.246 (t +2.9)** |
| Age (log) | **+0.145 (t +3.6)** | **−0.260 (t −4.2)** |

Signs flip between timeframes for age, coil and inducement. The consistent ones are EQ (+), external (−), confluence (−) and draw (≤ 0).
- Leave-one-dataset-out (`out_lodo.txt`): a fixed cross-market prior changed held-out log-loss by **−1.17% on average** (worse on 12 of 13 sets).
- The online probit centred on that prior averaged +0.24%, the same as with a zero prior. All of that gain comes from GC 1-hour.

So: real but heterogeneous effects. Do not hard-code them.

**(c) Top-1 pickers on evaluation bars (every H/3 bars, all live candidates)** (`out_pickers.txt`). Values are hit realised/baseline, mean distance and ATR delivered = mean(y·d).

| Dataset | Nearest | Hand score | max d·PoT | hand × d·PoT | Random |
|---|---|---|---|---|---|
| ES 5m | .71/.70, 1.3, 0.81 | .61/.58, 2.0, 1.01 | .40/.40, 3.1, **1.15** | .48/.46, 2.6, 1.12 | .34/.33, 4.4, 0.95 |
| NQ 1h | .75/.75, 1.3, 0.87 | .64/.66, 1.9, 0.99 | .47/.45, 3.2, **1.43** | .51/.52, 2.8, 1.27 | .41/.36, 4.5, 1.18 |
| CL 1h | .74/.74, 1.2, 0.77 | .64/.64, 1.8, 0.92 | .44/.44, 3.0, **1.26** | .48/.48, 2.7, 1.18 | .32/.29, 4.9, 0.97 |
| EURUSD 1h | .74/.73, 1.3, 0.84 | .58/.64, 1.9, 0.86 | .39/.42, 3.4, **1.26** | .46/.48, 2.9, 1.21 | .32/.32, 4.6, 0.85 |
| all 14 (range) | 0.57-0.93 ATR | 0.61-1.09 | **0.66-1.43** | 0.67-1.32 | 0.34-1.18 |

Realised hit rate equals the baseline within about ±3 pp for every picker on clean data. No picker has an information edge. They differ in the trade-off.
Theory check: argmax of `x·2Φ(−x)` is x = 0.752 (P = 0.452).

**(d) `f_calMult` under the null and an alternative** (`out_calmult_null.txt`). There are 4 families. Outcomes are clustered in groups of 3 with ρ = 0.5, to mimic overlapping windows.

| n per family | engine mean abs(cm−1) | engine P(abs(cm−1) ≥ 0.10) | engine P(at clamp) | EB (α 60, deff) mean abs(cm−1) | EB P(≥ 0.10) |
|---|---|---|---|---|---|
| 10 | 0.134 | 0.66 | 0.38 | 0.011 | 0.00 |
| 20 | 0.119 | 0.58 | 0.26 | 0.014 | 0.00 |
| 40 | 0.101 | 0.47 | 0.15 | 0.019 | 0.00 |
| 80 | 0.080 | 0.33 | 0.05 | 0.023 | 0.00 |
| 160 | 0.059 | 0.17 | 0.01 | 0.025 | 0.00 |
| 320 | 0.042 | 0.06 | 0.00 | 0.025 | 0.00 |

Alternative: family 0 has a true lift of 1.10, so the ideal multiplier is 1.073.

| n per family | engine cm0 mean | engine RMSE | EB cm0 mean | EB RMSE | engine RMSE, other families | EB RMSE, other families |
|---|---|---|---|---|---|---|
| 20 | 1.040 | 0.138 | 1.006 | 0.070 | 0.135 | 0.029 |
| 80 | 1.067 | 0.090 | 1.020 | 0.060 | 0.094 | 0.033 |
| 320 | 1.074 | 0.050 | 1.044 | 0.041 | 0.051 | 0.032 |

EB has lower error everywhere, at the price of being slow to detect a true 7% lift.

**(e) Peeking** (`out_peek.txt`). Null hypothesis, with p_i ~ U(0.35, 0.9) and the z re-checked after every trial from n = 20:

| N trials | P(ever z ≥ 2, "✓ EDGE") | P(ever z ≥ 1, "~ WEAK") | single look at N | normal-mixture CS (α .05, ρ 10) |
|---|---|---|---|---|
| 100 | 0.101 | 0.445 | 0.021 | 0.001 |
| 300 | 0.151 | 0.565 | 0.022 | 0.005 |
| 1000 | 0.200 | 0.647 | 0.026 | 0.014 |

**(f) Precision of the ledgers** (`out_deff.txt`), per 5,000 bars:
- Candidate probes: about 2,500-3,500. deff (2H blocks) is 1.4-2.8 on clean data and 7.7 on GC 1-hour. SE of the excess hit rate is 0.9-1.4 pp (1.9 on GC 1-hour).
- Selected trials: deff about 0.9-1.4, SE 1.4-1.7 pp. Our replica opens about 800 selected trials per 5,000 bars because it has no hysteresis; the engine opens fewer, so its SE is larger.
- Clustering by open bar vs booking bar gave similar deff (within ±0.3), so that detail is minor.
- Per-family SEs are about 2× larger (3-5 pp). That is above the typical lift size (2-7 pp), which is why per-family learning on the active ledger cannot work.

**Caveats.** The replica is simplified: no order blocks, breakers, iFVGs, killzones, HTF FVGs or volume-profile path cost, and an approximate draw
vector. Features are approximations of the engine's pillars. The findings therefore bound what *simple* learners can extract from *engine-like* features. They are not
the engine's exact numbers. That is why every proposal below makes the engine measure itself on the user's chart.

---

## 3. Engine gap analysis (line references)

### 3.1 Audit of the ledger, the calibration and the scoring maths

| Item | Lines | Verdict | Detail |
|---|---|---|---|
| Ledger is leak-free | 1426-1431 (open at bar close), 1549-1557 (grade on later confirmed bars, `bar_index > t.bar0`), 1527-1532 (surface only from completed windows), 2038 (`barstate.isconfirmed` block) | **correct** | No look-ahead found. Trials are graded before sweeps delete levels (step 2 before step 3). `f_calMult` at bar t uses only trials booked by bar t's close. On realtime bars the `var` state rolls back each tick and commits at close. |
| Hit definitions | 623-626, 1436 | correct | Strict for pools, touch for arrays, consistent with the surface (≥ grid step: negligible). |
| `f_calMult` prior | 1376-1382 | **wrong (too weak)** | `(k+2)/(e+2)` is a Poisson-gamma posterior with α = 2 expected hits. The hard cliff at n ≥ 10 and the clamp [0.8, 1.2] then do all the regularisation. Under the null it sits ≥ 10% off in 47-66% of families at n = 10-40 (§2.2 d). |
| `f_calMult` overlap | 1376-1382 | **missing** | Uses raw k and e. The design effect (already computed for the panel, 2385-2386) is ignored, so effective n is overstated by 1.4-3×. |
| `f_calMult` evidence gate | 1382 | **missing** | Applied whenever n ≥ 10, whether or not the family differs from the global lift significantly. |
| `f_calMult` data source | 1461-1474 | **wrong (bandit feedback)** | Learns only from *selected* DOLs. A family pushed down to 0.8 is selected less, so it gets fewer trials and its estimate barely moves (§1.28). Prequentially, the engine-style multiplier cost 0.2-1.8% log-loss on the 13 clean sets (§2.2 a). |
| `f_calMult` effect on selection | 1935-1944, 2012 | risk | Multiplies the whole score (draw and proximity included). A 10% change moves a score of 50 by 5 points, more than the 4-point hysteresis (147) and half the 8-point side-flip margin. Noise in the multiplier therefore turns into target switches: one plausible source of "targets jump around". |
| `f_raceAdj` | 1367-1371 | present, reasonable | Intercept-only logit shift (m = 20) on decided races. quant_pot found races are near-martingale (≤ 1.2 pp off). The shift is harmless but rarely informative. Could be gated (1.20). |
| EDGE z-test | 2383-2391 | **wrong (peeking)** | `zEdge ≥ 2` is re-evaluated continuously: 10-20% false "✓ EDGE" and 45-65% false "~ WEAK" under the null (§2.2 e). |
| Wilson CI with design effect | 2385-2387 | present (approximate) | Kish effective-n approach: `k/deff`, `n/deff`. Fine as a *fixed-time* interval. It is not time-uniform. |
| Cluster blocks | 1463-1469 | partial | Blocks are keyed by *booking* bar. Keying by *open* bar is the conceptually correct clustering for overlapping windows, but in our data the deff difference was ≤ 0.3. Low priority. |
| Per-family display | 2410-2418 | partial | Shows hit % with no expected % and no interval. A near family (FVG) looks better than a far one (external) purely by distance. ict_pd noted the same. |
| Displayed PoT never graded | 375-396 (no `pShow`), 1461-1500 | **missing** | No Brier score, reliability or skill score for the number the user sees (QPOT-04, SMC-1). |
| Selected-target optimizer's curse | 2066-2067 | **missing** | The shown PoT is the random-level model, not corrected for selection. In our replica, selected targets ran −6.9 to +2.8 pp from baseline. Correction is only worth it when gated (§2.2 a, "Selected recal"). |
| Baselines beyond the random level | 1313-1322 | **missing** | No nearest / random-candidate / runner-up comparison. The user cannot tell whether the scoring beats "nearest pool". |
| Candidate-level grading | 2037-2046 | **missing** | Only the active DOL is graded. Feature or pillar learning is statistically impossible at about 1 trial per H bars (§2.2 f). |
| Pillar weights | 141-145, 694 | hand-set; partly contradicted | Confluence (+15) and tier inside density (1.2·tier, 683) assume key or external levels are *more* likely to be hit. The pooled data say less likely (−0.18 to −0.27 logit, t up to −2.9). Draw (+30) has ≤ 0 lift beyond distance here and in ict_struct and bias_dol. EQ (0.9·eqCount, 683) is supported (+0.29, t +3.6 on 1-hour). |
| Proximity pillar | 662-667 | partial | Ad-hoc blend of a linear term, the drift-carrying reach `f_pot(..., mu·side, potH)/0.95` and a taper below `minDistATR`. A principled form is expected reach `d·P(d)` (1.22), which peaks near 0.75σ√H on its own. |
| Score → probability | 2063-2068 | correct separation | The displayed PoT is independent of the score, which is right: pillars must not inflate the probability unless a gated learner shows skill. |
| Learning toggles | 149-150, 2038 | partial | `useCal` is on by default, has no "measure only" mode, and the ledger runs whenever `useCal` is on even with the panel off. Fine for CPU. |

### 3.2 Concept status summary

| Concept | Status | Where / what differs |
|---|---|---|
| Distance-matched random-level baseline | present | 1313-1322; well calibrated in our replica (slope 0.93-1.04) |
| Offset (lift-over-baseline) modelling | partial | implicit in `f_calMult` ratio k/e; no feature-level offset model |
| Proper scoring (Brier/log-loss) of displayed PoT | missing | no `pShow` in `Trial` |
| Reliability diagram / ECE / calibration slope | missing | – |
| Platt / intercept recalibration | partial | races only (`f_raceAdj` 1367) |
| Isotonic / Venn-Abers | missing (n/a) | not recommended at ledger sizes |
| Beta-binomial / Poisson-gamma shrinkage | wrong | α = 2 in `f_calMult`, n ≥ 10 cliff, clamp |
| Empirical Bayes partial pooling | missing | – |
| Online logistic SGD | missing (good) | unregularised SGD is harmful (−3.6 to −5.5% LL) |
| Bayesian online probit/logistic | missing | proposal CAL-4 |
| Naive Bayes multiplicative lifts | n/a (proposed elsewhere) | ICT-1 / `f_ctxMult` designs cost 0.6-2.1% LL here |
| Elo / Glicko / Bradley-Terry | n/a | equivalent to SGD / Bayesian logistic |
| kNN / Lorentzian classifier | n/a | surface = principled kNN; the popular Pine kNN has misaligned labels and non-nearest neighbours |
| Learning to rank (pointwise + utility) | partial | hand score ranks; no explicit utility |
| Expected-reach utility d·P(d) | missing | prox pillar is ad hoc |
| Optimizer's curse correction | missing | – |
| Bandit feedback / selection bias | wrong | `f_calMult` learns from selected only |
| Overlap / design effect | present (partial) | `cluSt`, booking-bar blocks; not used in `f_calMult` |
| Peeking-safe inference | wrong | z ≥ 2 re-evaluated every bar |
| Prequential evaluation | partial | the ledger is prequential; no model-vs-model scoring |
| Safe aggregation (gate / mixture) | missing | – |
| Data-snooping control | missing (n/a) | relevant once many lifts are learned |
| Concept drift / forgetting | partial | roll50 display only; forgetting not helpful at these sizes |
| Selection baselines (nearest, random candidate) | missing | – |
| Wilson interval with design effect | present | 2385-2387 |

---

## 4. Proposals (best first; max 10)

Common Pine v6 rules for every sketch:
- All state updates run inside the existing `if barstate.isconfirmed and not na(atr) and atr > 0` block (1518). Live readouts reuse the
  last confirmed state.
- A function cannot reassign a global scalar, so mutable statistics live in `var array<float>` (as `stN`, `raceSt` do).
- Helpers are declared after the arrays and functions they use: PURE HELPERS for maths, STATE HELPERS after `f_potBase` (1322) for ledger helpers.
- UDT fields may be collections (`type_system.md`: "UDTs … can contain an arbitrary number of fields that can be of any supported type,
  including collection types").
- Loops are bounded (≤ 256 probes, ≤ `poolMax` levels). The loop limit is 500 ms per bar (`limitations.md`).

### CAL-1 (P1, S) · Replace `f_calMult` with an overlap-aware, evidence-gated empirical-Bayes multiplier

**Why.**
- At typical ledger sizes the current multiplier is mostly noise (§2.2 d).
- It learns from selected targets only (bandit feedback).
- It multiplies the whole score, and that noise can flip targets through the hysteresis.

**Algorithm.**
1. `gl = (K + 2)/(E + 2)`: the global lift (all families).
2. `deff = max(1, vEdge/vInd)`, using the panel's own cluster variance (2384-2385).
3. Posterior family lift with the prior centred on the global lift:
   `post_g = (k_g/deff + α·gl)/(e_g/deff + α)`, with α = `calPrior` (default 60 expected hits, a prior sd of about 13%).
4. Evidence gate: residual `S_g = k_g − gl·e_g`, variance `V_g = deff·Σ_g p(1−p)` (`stPV`). Apply only if `|S_g| ≥ f_csBound(V_g, 10, 0.10)`.
5. Multiplier: `cm_g = gate ? f_clamp(post_g/gl, 0.85, 1.15) : 1.0`. No n ≥ 10 cliff.
6. If CAL-3 lands, take `k_g, e_g, V_g` from the *candidate* ledger (full information) instead of `stN/stK/stPE`.

**Pine v6 sketch.**
```pine
// PURE HELPERS (after f_wilson, ~503): two-sided normal-mixture confidence-sequence boundary
f_csBound(float v, float rho, float alpha) =>
    math.sqrt((v + rho) * math.log((v + rho) / (rho * alpha * alpha)))

// INPUTS (G_SCORE, replace tooltip of useCal at 149)
float calPrior = input.float(60.0, "Calibration Prior (expected hits)", minval = 5.0, step = 5.0, group = G_SCORE,
  tooltip = "Strength of the shrinkage of each family's hit rate toward the overall rate. A family is only nudged once its difference is statistically proven (time-uniform test).")

// STATE HELPERS (replaces 1376-1382)
f_calMult(int g) =>
    float K    = stK.get(4)
    float E    = stPE.get(4)
    float gl   = (K + 2.0) / (E + 2.0)
    float vInd = stPV.get(4)
    float vCl  = math.max(vInd, cluSt.get(2) + cluSt.get(1) * cluSt.get(1))
    float deff = vInd > 0 ? math.max(1.0, vCl / vInd) : 1.0
    float k    = stK.get(g)
    float e    = stPE.get(g)
    float post = (k / deff + calPrior * gl) / (e / deff + calPrior)
    float S    = k - gl * e
    float V    = deff * stPV.get(g)
    bool  ok   = V > 0 and math.abs(S) >= f_csBound(V, 10.0, 0.10)
    ok ? f_clamp(post / gl, 0.85, 1.15) : 1.0
```

**UX.** In the Full panel's per-family rows (2411-2418), show `hit% · exp% · cm` (e.g. `FVG 71% · exp 69% · ×1.00`). Mark families whose gate is open with `*`.

**Ledger measurability.** Log the per-family multiplier on each `Trial` (new field `cm0`). Compare EDGE with the gate on and off over long histories.
Expected: fewer target switches (count `pickId != activeId` events) with no loss of EDGE.

**Evidence.** Moderate: null and alternative simulation (§2.2 d), prequential log-loss (§2.2 a), and the Poisson-gamma and confidence-sequence theory (Howard et al. 2021).

**Risk.**
- Slow to detect a true family lift. A real 7% lift reaches about 4% only by n ≈ 320.
- Accepted: per-family lifts in our data were below the noise floor anyway.

**Effort.** S (about 20 lines).

---

### CAL-2 (P1, S) · Peeking-safe EDGE verdict and honest ledger readouts

**Why.** The current verdict produces false "✓ EDGE" 10-20% of the time and false "~ WEAK" 45-65% of the time under the null (§2.2 e).
The family rows hide the expected rate.

**Algorithm.**
- `S = k − Σ pBase`, `V = vEdge` (the cluster-robust variance already computed at 2385).
- Always-valid 95% band on the edge in percentage points: `edge ± 100·f_csBound(V, ρ, 0.05)/n`, with ρ = 10, so the band is tightest around V ≈ 10-50 (about 50-250 trials).
- Verdict:
  - `S ≥ bound` → `✓ EDGE`;
  - `S ≤ −bound` → `✕ NEGATIVE`;
  - else `~ UNPROVEN ±x pp`;
  - `n/deff < 30` → `CALIBRATING`.
- Keep the Wilson interval for the hit rate. Its label is a fixed-time interval.
- Optional, low priority: key the cluster blocks by the trial's *open* bar (`floor(t.bar0/(2H))`), using a `map<int, float>` of block residual sums.

**Pine v6 sketch (panel, 2383-2397).**
```pine
float  S       = kA - stPE.get(4)
float  bnd     = f_csBound(vEdge, 10.0, 0.05)
float  nEffA   = nA / math.max(deff, 1.0)
string verdict = nEffA < 30 ? "CALIBRATING" : S >= bnd ? "✓ EDGE" : S <= -bnd ? "✕ NEGATIVE" : "~ UNPROVEN"
string band    = "±" + str.tostring(100.0 * bnd / nA, "0.0") + "pp"
```
Per-family rows: `f_cell(dash, 1, row, hit% + " / exp " + str.tostring(100*stPE.get(g)/ng, "0") + "%", …)`.

**Evidence.** Strong (theory: Robbins 1970; Howard et al. 2021; Johari et al. 2017) and moderate (our simulation).

**Risk.** The band is wider (z ≈ 3.0-3.7). The verdict will say "UNPROVEN" more often, which is honest.

**Effort.** S.

---

### CAL-3 (P1, M) · Candidate (shadow) ledger with baseline suite and "ATR delivered"

**Why.**
- Full-information grading of every candidate removes the bandit-feedback bias (1.28).
- It roughly doubles to triples the effective sample (§2.2 f).
- It answers the question users actually ask: *does the engine's choice beat "nearest pool" or a random candidate?*
- It is the data source for CAL-1, CAL-4 and CAL-7.

ICT-1 (`ict_liq.md`) proposed the same infrastructure. This spec supersedes its mechanics: per-level non-overlap, role probes for baselines,
an offset store for learning, and *no* direct naive-Bayes multipliers in the score.

**Type (after `Trial`, ~396).**
```pine
type Probe
    int   lvId
    int   grp            // 0 chart liq · 1 ext liq · 2 FVG · 3 OB/BRK
    int   side
    bool  liq
    float edge
    int   bar0
    float pb             // f_potBase at open (distance-matched random level)
    float d0             // distance (ATR) at open
    float pM   = na      // learner probability at open (CAL-4)
    float pG   = na      // gated / mixed probability at open (CAL-4)
    int   role = 0       // 0 routine · 1 active DOL · 2 nearest candidate · 3 random candidate · 4 runner-up
    array<float> x       // feature vector at open (CAL-4); na when the learner is off
```
Add `int lastProbe = -100000` to `Level` (317-345).

**State (after 1079).**
```pine
var array<Probe> probes = array.new<Probe>()
const int NPROBE = 256
// candidate stats per family + ALL: [n, k, e, v] blocks of 4
var array<float> cdSt = array.new<float>(5 * 4, 0.0)
// role stats: [n, k, e, v, Σ y·d0] for roles 1..4
var array<float> rlSt = array.new<float>(5 * 5, 0.0)
```

**Snapshot.** Runs in step 17, after `lv.evaluate`, within `inCalc` and past `warmup`:
```pine
for lv in pool
    float dA = math.max(0.0, lv.distance(close)) / atr
    if bar_index - lv.lastProbe >= H and dA >= 0.25 and dA <= maxATR and probes.size() < NPROBE
        probes.push(Probe.new(lv.id, lv.grp(), lv.side, lv.isLiquidity(), lv.nearEdge(), bar_index,
          f_potBase(dA * atr, lv.side), dA, x = f_feat(lv, dA)))      // f_feat: CAL-4, or na
        lv.lastProbe := bar_index
```

**Role probes.** Opened at the moment step 20 pushes a new `Trial` (2045). Add one probe each for:
- the active DOL (role 1);
- the nearest candidate with `dA ≥ minDistATR` (role 2);
- a deterministic pseudo-random candidate, `idx = int(math.abs(math.sin(bar_index * 12.9898) * 43758.5453)) % pool.size()` (role 3);
- the runner-up by score, the second-highest `lv.score` (role 4).

Role probes bypass `lastProbe` and are excluded from learning (CAL-4), so samples are not double-counted.

**Grading (new step 2b, right after 1550-1557, before sweeps delete levels).**
```pine
if probes.size() > 0
    for i = probes.size() - 1 to 0
        Probe p = probes.get(i)
        if bar_index > p.bar0
            bool hit = p.liq ? (p.side == 1 ? high > p.edge : low < p.edge) : (p.side == 1 ? high >= p.edge : low <= p.edge)
            if hit or bar_index - p.bar0 >= H
                f_probeBook(p, hit ? 1 : 0)     // stats by family/role, learner update (CAL-4), prequential sums
                probes.remove(i)
```
`f_probeBook` updates `cdSt` (when role = 0) and `rlSt` (when role > 0) with `n += 1, k += y, e += pb, v += pb(1−pb)`, and `Σ y·d0` for roles.

**UX (Terminal, Accuracy = Full).**
- `CANDIDATES  hit 52% / exp 51%  (+1.0pp ±1.9)`
- `DOL vs NEAREST  +3.1pp · vs RANDOM +4.0pp · vs #2 +0.8pp`, with the CAL-2 band.
- `ATR DELIVERED  DOL 1.12 · nearest 0.81 · random 0.95`.

**Cost.** Up to 256 probes × O(1) per bar, plus O(pool) for snapshots. Negligible next to the existing pool loops.

**Ledger measurability.** This proposal *is* the measurement. Success means the comparison rows are stable over 5,000 bars, with candidate SE ≈ 1-2 pp.

**Evidence.** Moderate: our replica gives 2.5-3.5k probes per 5,000 bars, deff 1.4-2.8 and SE 0.9-1.4 pp. Bandit-feedback theory: Li et al. 2011.

**Risk.**
- Probes on different levels share one price path. That is handled by the cluster variance (key by `bar0` blocks).
- The cap can bind on a huge pool. If so, drop routine probes farthest first.

**Effort.** M (about 80 lines).

---

### CAL-4 (P1, M-L) · Safe online learner: Bayesian probit lift on the candidate ledger, prior = hand-set pillars, gated by prequential log-loss

**Why.**
- This is the leak-free learner the brief asks for. It learns pillar and family lifts *beyond distance*, and it shrinks toward the hand-set prior.
- It is only allowed to touch the score or the PoT once it has beaten the pure-geometry baseline prequentially on *this* chart.
- On clean data it then stays dormant (cost ≤ 0.3% LL). On a broken base it rescues the forecast (+8.8% to +10.5% LL).
- Unregularised SGD, naive-Bayes lifts and cross-market hard-coded lifts all fail (§2.2 a, b).

**Inputs (G_ACC).**
```pine
string lrMode  = input.string("Measure", "Self-Learning", options = ["Off", "Measure", "Apply when proven"], group = G_ACC,
  tooltip = "Measure: learns how each pillar/family changes the hit rate beyond distance, shown in the Full panel. Apply when proven: the learned lift also adjusts scores and PoT, but only while it has out-predicted the plain distance model on this chart.")
float  lrSd    = input.float(0.15, "Learner Prior Width", minval = 0.02, maxval = 1.0, step = 0.01, group = G_ACC)
float  lrOmega = input.float(0.25, "Learner Update Weight", minval = 0.05, maxval = 1.0, step = 0.05, group = G_ACC,
  tooltip = "< 1 because overlapping H-bar windows are not independent.")
```

**Features (F = 11, all ≈ centred, computed at snapshot by `f_feat(lv, dA)`).**

| j | Feature | Definition | Prior mean μ0 |
|---|---|---|---|
| 0 | bias | 1 | 0 |
| 1 | ext | `grp == 1` | 0 |
| 2 | fvg | `grp == 2` | 0 |
| 3 | obk | `grp == 3` | 0 |
| 4 | eq | `eqCount > 0` | 0 |
| 5 | fresh | `fresh − 0.5` | `κ·wFresh/wSum` |
| 6 | conf | `conf` | `κ·wConf/wSum` |
| 7 | dens | `dens − 0.5` | `κ·wDens/wSum` |
| 8 | draw | `draw − 0.5` | `κ·wDraw/wSum` |
| 9 | kz | `f_kzAff(kz, src) > 1` | 0 |
| 10 | dres | `(dA − 2.5)/2.5` | 0 |

- κ = 0.3: the hand-set prior believes a pillar moving from 0 to 1 adds at most about 0.3·w/Σw probit, i.e. ≤ 3.6 pp at p ≈ 0.5 for draw.
- Prior sd `lrSd` for all.
- The `dres` term lets the learner fix distance-curvature errors of the base (the GC 1-hour case).

**State.**
```pine
const int NF = 11
var array<float> lrMu  = array.new<float>(NF, 0.0)     // init on first bar: prior means (see above)
var array<float> lrV   = array.new<float>(NF, 0.0)     // init: lrSd²
var array<float> lrMix = array.from(0.0, 0.0)          // log-weights [base, model]
// prequential sums: [n, LL base, LL model, LL mixed, Brier base, Brier model]
var array<float> pqSt  = array.new<float>(6, 0.0)
```

**Helpers (PURE HELPERS; `f_phi` exists at 418).**
```pine
f_npdf(float z) =>
    math.exp(-0.5 * z * z) / math.sqrt(2.0 * math.pi)

// inverse normal CDF (Acklam rational approximation, |rel err| < 1.2e-9)
f_phinv(float p) =>
    float q = math.max(1e-9, math.min(1.0 - 1e-9, p))
    float r = 0.0
    if q < 0.02425
        float t = math.sqrt(-2.0 * math.log(q))
        r := (((((-7.784894002430293e-03 * t - 3.223964580411365e-01) * t - 2.400758277161838e+00) * t - 2.549732539343734e+00) * t + 4.374664141464968e+00) * t + 2.938163982698783e+00) / ((((7.784695709041462e-03 * t + 3.224671290700398e-01) * t + 2.445134137142996e+00) * t + 3.754408661907416e+00) * t + 1.0)
    else if q > 1.0 - 0.02425
        float t = math.sqrt(-2.0 * math.log(1.0 - q))
        r := -(((((-7.784894002430293e-03 * t - 3.223964580411365e-01) * t - 2.400758277161838e+00) * t - 2.549732539343734e+00) * t + 4.374664141464968e+00) * t + 2.938163982698783e+00) / ((((7.784695709041462e-03 * t + 3.224671290700398e-01) * t + 2.445134137142996e+00) * t + 3.754408661907416e+00) * t + 1.0)
    else
        float u  = q - 0.5
        float s2 = u * u
        r := (((((-3.969683028665376e+01 * s2 + 2.209460984245205e+02) * s2 - 2.759285104469687e+02) * s2 + 1.383577518672690e+02) * s2 - 3.066479806614716e+01) * s2 + 2.506628277459239e+00) * u / (((((-5.447609879822406e+01 * s2 + 1.615858368580409e+02) * s2 - 1.556989798598866e+02) * s2 + 6.680131188771972e+01) * s2 - 1.328068155288572e+01) * s2 + 1.0)
    r
```
(Tested in Python: `cand_learn.py` `Phinv`.)

**Learner (STATE HELPERS, after `f_potBase`).**
```pine
// probit index and total std for a feature vector
f_lrPred(float off, array<float> x) =>
    float m  = off
    float s2 = 1.0
    for j = 0 to NF - 1
        float xj = x.get(j)
        m  += lrMu.get(j) * xj
        s2 += xj * xj * lrV.get(j)
    [m, math.sqrt(s2)]

// adPredictor update (Graepel et al. 2010), tempered by lrOmega for overlapping windows
f_lrUpdate(float off, array<float> x, int y) =>
    [m, s] = f_lrPred(off, x)
    float t  = y == 1 ? 1.0 : -1.0
    float z  = t * m / s
    float Pz = math.max(f_phi(z), 1e-12)
    float vz = f_npdf(z) / Pz
    float wz = vz * (vz + z)
    for j = 0 to NF - 1
        float xj = x.get(j)
        float vj = lrV.get(j)
        lrMu.set(j, lrMu.get(j) + lrOmega * t * xj * vj / s * vz)
        lrV.set(j, vj * math.max(0.05, 1.0 - lrOmega * xj * xj * vj / (s * s) * wz))
    true
```
In `f_probeBook` for role-0 probes with `x` set:
1. Prequential scoring uses `p.pb`, `p.pM` and `p.pG` stored *at open*: `pqSt += [1, LL(pb), LL(pM), LL(pG), (pb−y)², (pM−y)²]`.
2. Mixture weights (η = 0.25, fixed share 0.005):
   `lrMix[0] += 0.25·ln(y ? pb : 1−pb)`, `lrMix[1] += 0.25·ln(y ? pM : 1−pM)`, then normalise and share.
3. `f_lrUpdate(f_phinv(p.pb), p.x, y)`.

At snapshot (CAL-3), set `pM = f_phi(m/s)` from `f_lrPred` and `pG = π·pM + (1−π)·pb`, with `π = softmax(lrMix)[1]`.

**Apply (only `lrMode == "Apply when proven"` and `pqSt[0] ≥ 200` and `pqSt[2] < pqSt[1]`).** Gate form; the mixture π can replace the gate.
- **Score** (step 17 multiplier loop, 1940-1947):
  - `L_i = Σ_j μ_j x_ij` (lift in probit units), and `L̄` = pool mean of `L_i`.
  - `lv.mult *= f_clamp(math.exp(π · (L_i − L̄)), 0.85, 1.20)`.
  - This *replaces* `f_calMult` when on, because family effects are columns 1-3.
- **PoT** (2066-2067): `activePoT := π·f_phi((f_phinv(pModel) + L_act)/s) + (1−π)·pModel`. Cap at 95% for display only.

**UX (Full).**
- `LEARN  ΔLL −0.21% vs distance · π 0.03 · n 2140  (dormant)`.
- `LIFT  EQ +.09±.04 · CONF −.12±.05 · DRAW +.01±.03 · EXT −.08±.05`: the four largest |μ − μ0| with posterior sd `√v`.
- Clean style: nothing (tooltip only).

**Leak-freedom.**
- Features and predictions are stored on the probe at open.
- The update happens only at the resolution bar, inside the confirmed-bar block.
- The gate uses only resolved probes.
- No state reads future bars.

**Evidence.**
- Moderate, from our replica (§2.2 a): raw Bayesian probit −0.15 to −0.79% on clean sets; GATE 0.00 to −0.26%; MIX −0.32 to +0.01%; GC 1-hour +8.8% / +10.5%. SGD without a prior −3.6 to −5.5%. NB −0.6 to −2.1%.
- Strong, from the literature: Graepel 2010; Cesa-Bianchi & Lugosi 2006; Ng & Jordan 2002.

**Risk.**
- Complexity.
- On clean data it does nothing visible apart from the LIFT readout. That is the honest outcome, and the readout itself is the trader-facing value (which ICT claims hold on this symbol).
- Must not run when `lrMode == "Off"`, to save CPU.

**Effort.** M-L (about 120 lines).

---

### CAL-5 (P2, S-M) · Expected-reach proximity pillar and an explicit "Target Objective"

**Why.**
- Probability is geometry, so choosing among candidates is a *utility* trade-off between hit rate and distance (§1.22, §2.2 c).
- The current proximity pillar (662-667) encodes that trade-off with arbitrary pieces: a linear term, a drift-carrying reach divided by 0.95, and a taper below `minDistATR`.
- Expected reach `d·P(d)` encodes it from first principles and from the chart's own surface. It peaks near 0.75σ√H, where the touch probability is about 45%.
- In the replica, max-`d·PoT` targets delivered **+20% to +45% more ATR per target** than the hand-score pick, and the hit rate still matched its forecast.

**Algorithm.**
- `P(d) = f_potBase(dist, side)`. Drift-free; empirical surface plus analytic prior.
- `ER(d) = dAtr · P(d)`.
- `ERmax`: once per bar (`tailBar` or each confirmed bar), `max_j (j·bStep)·S_j/n` over the regime row, or `0.34·σ√H/atr` analytically while warming up.
- `prox = dAtr ≥ maxATR ? 0 : f_clamp(ER/ERmax, 0, 1)`. The near taper comes for free, because ER → 0 as d → 0.
- Input `string tgtObj = input.string("Balanced", "Target Objective", options = ["Hit Rate", "Balanced", "Reach"])`:
  - Hit Rate = legacy prox;
  - Reach = ER prox;
  - Balanced = `math.sqrt(legacyProx · erProx)`.
- Ledger: add `Σ y·d0` ("ATR delivered") per family and in the CAL-3 role rows, plus a data-window plot.

**Pine v6 sketch.** In `evaluate` (661-667), replace the `this.prox :=` line:
```pine
// new parameters of evaluate: float pR (= f_potBase(dist, side), computed at the call site 1948), float erMax
float er    = dAtr * pR
float erN   = f_clamp(er / math.max(erMax, 1e-6), 0.0, 1.0)
float legacy = (0.5 * lin + 0.5 * reach) * (0.30 + 0.70 * taper)
this.prox  := dAtr >= maxATR ? 0.0 : tgtObj == "Reach" ? erN : tgtObj == "Balanced" ? math.sqrt(legacy * erN) : legacy
```
Ordering note: `evaluate` (661) is declared before the STATE section, so it cannot call `f_potBase` (1314), which reads global `var` arrays.
Pass `pR` in as a parameter: compute `f_potBase(dist, lv.side)` at the call site (1948) and add a `float pR` argument to `evaluate`.
Likewise pass `erMax`, computed once per bar in step 17 from `sUp/sDn`.

**Ledger measurability.** ATR delivered (DOL vs nearest vs random), hit rate and EDGE. The expected shift is lower hit %, higher ATR delivered, and EDGE unchanged.

**Evidence.**
- Strong for the theory (decision theory; the first-passage optimum computed numerically).
- Moderate for the replica (§2.2 c: 1.10-1.43 vs 0.86-1.09 ATR).
- Weak for "traders prefer it". Hence the selectable objective.

**Risk.** The headline DOL HIT % falls (e.g. 60% → 45%). Users may read that as worse. Default "Balanced". Show both metrics.

**Effort.** S-M.

---

### CAL-6 (P2, M) · One gated PoT-calibration layer for the selected target (optimizer's curse) with a prequential scorecard

**Why.**
- The selected target is an argmax, so its forecast suffers the optimizer's curse (Smith & Winkler 2006).
- The displayed PoT is never graded.
- Three sibling proposals (QPOT-04, SMC-1, TIME-2) each add a calibration. This spec merges them into one implementation and adds the missing safeguard.
- Recalibration on a calibrated base cost up to 0.36% LL in our test. It only gained on a broken base (+2.9%), so it must be *gated*.

**Algorithm.**
- `Trial` gains `float pShow` (the PoT shown at open, uncapped) and `float pCal`.
- Intercept shift learned on resolved active trials: `δ = logit((K + 20·P̄)/(N + 20)) − logit(P̄)` (P̄ = mean pShow). This is the `f_raceAdj` pattern.
- Optional slope (Platt, b ∈ [0.7, 1.3]) once N ≥ 150. Fit by 3 Newton steps on 10-bin sufficient statistics `[n_b, Σlogit_b, Σy_b]`: deterministic, no learning rate.
- Gate: a two-expert log-loss mixture (raw vs calibrated) on active trials, with fixed share. Displayed PoT = mixture.
- Scorecard arrays: `[n, Σ(pShow−y)², Σ(pBase−y)², Σ LL(pShow), Σ LL(pBase)]` plus 5 reliability bins `[n_b, Σp_b, Σy_b]`.

**UX.**
- Terminal Full: `PoT CAL  Brier .201 vs base .215 (BSS +6%) · slope 0.92 · gate OFF · n 140`, plus a 5-cell reliability strip (`40→38 · 55→57 · …`).
- Clean: tooltip only.

**Evidence.**
- Strong (Platt 1999; Niculescu-Mizil & Caruana 2005; Smith & Winkler 2006).
- Moderate (§2.2 a "Selected recal" column).

**Risk.** Few active trials. The gate keeps it at the raw PoT until the evidence is in.

**Effort.** M.

---

### CAL-7 (P2, S) · Pillar information readout ("which pillars carry information on this chart")

**Why.**
- Lifts are real but heterogeneous across symbols (§2.2 b, LODO −1.17%).
- Traders want to know *which ICT claims hold on this chart* (EQ, confluence, draw, freshness), even when the learner stays dormant.
- A non-parametric readout from the candidate ledger needs no model and cannot overfit the score, because it is measurement only.

**Algorithm.**
- At snapshot, record pillar tertiles `tq_j ∈ {0, 1, 2}` for j ∈ {fresh, conf, dens, draw} and bits {EQ, EXT, KZ}.
- At resolution, book `[n, k, e, v]` per (pillar, tertile).
- Readout: `excess(top) − excess(bottom)` in pp, with a CAL-2 confidence-sequence band and `*` when significant.
- State: `var array<float> pilSt = array.new<float>(7 * 3 * 4, 0.0)`.

**UX (Full).**
`PILLARS  dens +1.2 · conf −3.4* · draw +0.4 · fresh −0.8 · EQ +4.1* (pp, top vs bottom third)`.

**Evidence.** Moderate. The pooled replica found significant but heterogeneous effects: EQ +0.29, external −0.27, confluence −0.25, draw −0.11 logit.

**Risk.** Multiple comparisons: 7 readouts. Use α = 0.05/7 in the band, or the same CS boundary with α = 0.01.

**Effort.** S (reuses CAL-3).

---

## 5. How this fits the other study reports

| Their proposal | Relationship |
|---|---|
| quant_pot **QPOT-04** (grade and recalibrate the displayed PoT), smc_impl **SMC-1** (ledger-calibrated PoT) | Merged into **CAL-6**, with a gate added. Ungated recalibration was neutral to slightly harmful on calibrated bases in our test. |
| quant_pot **QPOT-08** (stacked online logistic of PoT models) | Same family as CAL-4. Use the same gate or mixture. QPOT-08 reported a failure on GC 1-hour roll-gap data, the opposite of our protective effect, because its stack had no baseline expert to fall back to. |
| ict_liq **ICT-1** (candidate ledger + feature lifts) | Infrastructure = **CAL-3**. Replace its multiplicative naive-Bayes lifts with CAL-4: NB lifts cost 0.6-2.1% LL in our test. |
| ict_pd `f_ctxMult` context helper | Same naive-Bayes issue. Prefer CAL-4 columns, or CAL-1-style gated EB per context. |
| bias_dol **BIAS-1/2** (side learner with prior = geometry, prequential Brier skill) | Same philosophy as CAL-4: offset = race geometry, learned features, prequential skill. Reuse `f_phinv` and the adPredictor update, and add the gate. |
| ict_struct (D has no skill) | Consistent with our draw coefficient (−0.03 / −0.11) and with CAL-5's argument that selection is utility, not information. |

---

## 6. Sources

Literature:
- Graepel, Candela, Borchert, Herbrich (2010). Web-Scale Bayesian Click-Through Rate Prediction for Sponsored Search Advertising in Microsoft's Bing Search Engine. ICML. https://icml.cc/Conferences/2010/papers/901.pdf
- Niculescu-Mizil, Caruana (2005). Predicting Good Probabilities With Supervised Learning. ICML. https://www.cs.cornell.edu/~alexn/papers/calibration.icml05.crc.rev3.pdf
- Platt (1999). Probabilistic outputs for support vector machines and comparisons to regularized likelihood methods. (Targets as quoted in Niculescu-Mizil & Caruana.) https://ams.confex.com/ams/pdfpapers/88928.pdf
- Ng, Jordan (2002). On Discriminative vs. Generative Classifiers: A comparison of logistic regression and naive Bayes. NIPS. https://papers.nips.cc/paper/2020-on-discriminative-vs-generative-classifiers-a-comparison-of-logistic-regression-and-naive-bayes
- Smith, Winkler (2006). The Optimizer's Curse: Skepticism and Postdecision Surprise in Decision Analysis. Management Science 52(3):311-322. https://jimsmith.host.dartmouth.edu/wp-content/uploads/2022/04/The_Optimizers_Curse.pdf
- Johari, Pekelis, Walsh (2017/2022). Always Valid Inference: Continuous Monitoring of A/B Tests. Operations Research 70(3). https://arxiv.org/abs/1512.04922
- Johari, Koomen, Pekelis, Walsh (2017). Peeking at A/B Tests. KDD. https://dl.acm.org/doi/pdf/10.1145/3097983.3097992
- Practitioner summary of the peeking problem (quotes the Optimizely "over 20% to under 5%" figure). https://atticusli.com/replication-crisis/ab-testing-peeking-problem/
- Howard, Ramdas, McAuliffe, Sekhon (2021). Time-uniform, nonparametric, nonasymptotic confidence sequences. Annals of Statistics. https://arxiv.org/abs/1810.08240 (eq. 14, Prop. 3)
- Waudby-Smith et al. (2021). Time-uniform central limit theory and asymptotic confidence sequences. https://arxiv.org/abs/2103.06476
- Chapelle, Li (2011). An Empirical Evaluation of Thompson Sampling. NIPS. https://proceedings.nips.cc/paper_files/paper/2011/file/e53a0a2978c28872a4505bdb51db06dc-Paper.pdf
- Vovk, Petej (2014). Venn-Abers predictors. UAI. https://arxiv.org/abs/1211.0025 ; Vovk, Petej, Fedorova (2015). Large-scale probabilistic predictors with and without guarantees of validity. NIPS. https://arxiv.org/abs/1511.00213
- Király, Qian (2017). Modelling Competitive Sports: Bradley-Terry-Élő Models for Supervised and On-Line Learning of Paired Competition Outcomes. https://arxiv.org/abs/1701.08055
- Cao, Qin, Liu, Tsai, Li (2007). Learning to Rank: From Pairwise Approach to Listwise Approach. ICML. https://www.microsoft.com/en-us/research/?p=153086 ; Burges et al. (2005). Learning to rank using gradient descent. ICML.
- Cesa-Bianchi, Lugosi (2006). Prediction, Learning, and Games. Cambridge UP. Bayes-mixture log-loss regret ln N: lecture notes https://www.cs.princeton.edu/courses/archive/spring18/cos511/scribe_notes/0425.pdf ; fixed share: Herbster, Warmuth (1998), Tracking the best expert, Machine Learning 32; Koolen, de Rooij, Universal Codes from Switching Strategies https://arxiv.org/abs/1311.6536
- Gneiting, Raftery (2007). Strictly Proper Scoring Rules, Prediction, and Estimation. JASA 102:359-378.
- Murphy (1973). A new vector partition of the probability score. J. Applied Meteorology 12.
- Bröcker, Smith (2007). Increasing the reliability of reliability diagrams. Weather and Forecasting 22.
- Kull, Silva Filho, Flach (2017). Beta calibration. AISTATS. Guo, Pleiss, Sun, Weinberger (2017). On calibration of modern neural networks. ICML.
- Efron, Morris (1975). Data analysis using Stein's estimator and its generalizations. JASA 70.
- Duchi, Hazan, Singer (2011). Adaptive Subgradient Methods (AdaGrad). JMLR. McMahan et al. (2013). Ad Click Prediction: a View from the Trenches (FTRL-Proximal). KDD.
- Dawid (1984). Statistical theory: the prequential approach. JRSS A 147.
- López de Prado (2018). Advances in Financial Machine Learning, chs. 4 (sample uniqueness) and 7 (purged/embargoed CV). Summaries: https://en.wikipedia.org/wiki/Purged_cross-validation ; https://www.mql5.com/en/articles/19850
- Sullivan, Timmermann, White (1999). Data-Snooping, Technical Trading Rule Performance, and the Bootstrap. Journal of Finance 54(5):1647-1691. https://econpapers.repec.org/RePEc:bla:jfinan:v:54:y:1999:i:5:p:1647-1691 ; White (2000). A Reality Check for Data Snooping. Econometrica 68.
- Li, Chu, Langford, Wang (2011). Unbiased offline evaluation of contextual-bandit-based news article recommendation algorithms. WSDM.
- Domingos, Pazzani (1997). On the optimality of the simple Bayesian classifier under zero-one loss. Machine Learning 29.
- Chung, Bellotti (2021). Evidence and behaviour of support and resistance levels in financial time series. https://arxiv.org/abs/2101.07410

Practitioner / code:
- "Machine Learning: Lorentzian Classification" (TradingView, public). Algorithm inspected from the public multi-language port https://github.com/artificial-intelligence-edge/lorentzian-classification (Pine v6 source `ports/pinescript/lorentzian-classification-v2.pine`, lines 335-413). Concepts only; no code reused.
- MQLSoftware Liquidity Map and AetherEdge Smart Money Flow (open-source draw-probability displays), via `competitors.md` and `smc_impl.md`.

Project-internal:
- `quant_pot.md`, `ict_liq.md`, `ict_pd.md`, `ict_struct.md`, `bias_dol.md`, `smc_impl.md`, `competitors.md` in the same `study/` folder.
- Pine docs mirror: `docsrc/jabez4jc_pinescriptv6/writing_scripts/limitations.md` (500 ms loop limit, 100,000-element collections) and `language/type_system.md` (UDT fields may be collections).

Our study code and outputs: `study/calib_ml_tools/` (see the header of this report).
