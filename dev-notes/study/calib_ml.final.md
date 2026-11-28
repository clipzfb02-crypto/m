# Scoring, online learning and calibration: combined final study (A + B) for DOL Engine v2

Domain: how the engine should combine its scoring pillars, learn from its own accuracy ledger, and calibrate the
Probability of Touch (PoT) without look-ahead or overfitting. All line numbers refer to
`/tmp/claude-0/-home-user-m/7ce60006-3639-59b1-8cd3-87355409d58a/scratchpad/brief/baseline_v2.pine`
(identical to `indicators/dol_engine.pine`; B re-checked every reference).

Markers used throughout:
- **[A✓]** A's content, re-checked by B and kept.
- **[B-fix]** A's content corrected, re-graded or narrowed by B.
- **[B]** new in B's pass.

Reproducible code and raw outputs:
- A: `study/calib_ml_tools/` (`cand_learn.py`, `analyze.py`, `pooled_lift.py`, `lodo.py`, `pickers.py`, `calmult_null.py`,
  `peek_sim.py`, `out_*.txt`, `res_*.pkl` = every candidate probe with its features and stored forecasts).
- B: `study/calib_ml_b_tools/` (`ops_test.py` + `out_ops*.txt`: prequential online Platt scaling, calibeating,
  intercept-only and mixture tests on A's stored probes; `holm_lifts.py` + `out_holm.txt`: multiplicity check;
  `ext_lc/`, `ext_lr/`: third-party Pine sources inspected for concepts only, nothing reused).

Research note (B): the Firecrawl page-scrape allowance was exhausted and WebFetch could not resolve icml.cc, cornell.edu,
mcgill.ca or arxiv.org from this session. arXiv papers were read through the research-paper index instead; non-arXiv PDFs
(Graepel 2010, Niculescu-Mizil & Caruana 2005, Efron & Morris 1975) could not be re-opened, so their exact figures are
marked "not re-verified" below.

---

## 0. Key findings (read this first)

1. **The distance-matched baseline is already a well-calibrated touch probability.** [A✓, B re-tested]
   - A's engine-like replica (14 datasets: 6 CME futures at 5-min and 1-hour, EURUSD 1-hour, S&P 500 daily;
     76,181 candidate probes): calibration slope **0.93-1.04** on all 13 clean sets.
   - B added calibration-in-the-large: observed minus forecast hit rate **−1.4 to +2.0 pp** on the 13 clean sets,
     **−4.25 pp** on GC 1-hour (roll gaps). Spiegelhalter z (independence-assuming) −1.1 to +2.8.
   - Corroborated independently by quant_pot.final (engine surface on 1.2 M 5-min rows: slope 0.99, ECE 0.004).
2. **No learner beats that baseline out of sample on clean data; a gated learner costs almost nothing and protects a
   broken base.** [A✓ + B] Prequential log-loss change versus the baseline (predict at open, learn at resolution):

   | Learner | 13 clean sets | GC 1-hour (broken base) | Source |
   |---|---|---|---|
   | Unregularised online logistic SGD | −3.6 … −5.5% | +9.1% | A |
   | Naive-Bayes multiplicative lifts | −0.6 … −2.1% | +2.2% | A |
   | Engine-style `f_calMult` (as a probability) | −0.2 … −1.8% | +2.1% | A |
   | Bayesian online probit, 12 features (adPredictor) | −0.15 … −0.79% | +8.8% | A |
   | Online Platt scaling (2-D Online Newton Step, defaults γ 0.1 ρ 100) | −0.6 … −1.8% | +5.6% | **B** |
   | Online Platt, conservative (γ 1, ρ 1000) | −0.06 … +0.15% | +0.7% | **B** |
   | Calibeating / tracking (10 bins over OPS) | −1.4 … −3.1% | +4.7% | **B** |
   | Intercept-only shift (m = 100 pseudo-trials) | −0.11 … +0.12% | +2.05% | **B** |
   | **Gate** on the probit (model used only after 200 probes while its running LL is lower) | 0.00 … −0.26% | +8.8% | A |
   | **Gate** on online Platt | 0.00 … −0.23% (mean −0.02%) | +5.6% | **B** |
   | Exponential-weights mixture base + probit (η 0.25, fixed share 0.005) | −0.32 … +0.01% | +10.5% | A |
   | Exponential-weights mixture base + online Platt | −0.57 … −0.12% | +6.5% | **B** |

   The learner's job is therefore **protection and honest measurement, not hidden edge**. [A✓] B adds that the
   protection matters in practice: **TradingView continuous futures are not back-adjusted by default** (TradingView help
   centre: "By default, back-adjustment is disabled"), so roll-gap-corrupted surfaces like GC 1-hour are a realistic user
   situation. [B]
3. **The cheapest safe calibrator is a 2-parameter online Platt map behind a prequential gate.** [B] It needs a 2×2
   matrix and no feature vectors, keeps 64% of the probit's rescue on the broken base (+5.6% vs +8.8%), and costs
   ≤ 0.23% on clean data. The 12-feature probit is still the best *measurement* tool (pillar lifts) and the best rescuer,
   so it is kept as a second tier (CAL-9), not the first thing to build.
4. **`f_calMult` (1376-1382) is mostly noise.** [A✓, B-fix on the mechanism]
   - Under a true null its `((k+2)/(e+2)) / ((K+2)/(E+2))`, clamped to [0.8, 1.2] after n ≥ 10, sits ≥ 10% off 1 in
     **66% / 47% / 33%** of families at n = 10 / 40 / 80 (A's simulation, re-run by B: identical).
   - It learns only from *selected* targets (bandit feedback) and ignores the design effect.
   - [B-fix] A described the harm as "noise turns into target switches". More precisely: each booking moves the
     multiplier by only ~1-3%, so the damage is a **persistent family tilt** of up to ±20% of the score (±10 points at a
     score of 50), larger than the 4-point hysteresis (147). Which family wins a close contest is partly decided by ledger
     noise, and a booking that nudges the multiplier across that boundary produces a switch.
5. **The EDGE verdict suffers from peeking.** [A✓] `zEdge ≥ 2 → ✓ EDGE` (2390) is re-evaluated after every booking.
   Under the null: false "✓ EDGE" ever shown **10% / 15% / 20%** within 100 / 300 / 1,000 trials, false "~ WEAK"
   45-65%. The two-sided normal-mixture confidence sequence (Howard et al. 2021, eq. 14, **verified by B**) keeps this
   ≤ 1.4%.
   - [B] Two extra conditions: (i) with an *estimated* (cluster-robust) variance, the guarantee becomes an *asymptotic*
     confidence sequence (Waudby-Smith et al. 2021; dependent data: Ge & Liu 2026); (ii) the 2H-bar blocks become **few
     clusters at long horizons** (5000/(2·450) ≈ 5 blocks at H = 450), where cluster-robust variances are biased
     down (Cameron, Gelbach & Miller 2008). The verdict needs a block-count guard.
6. **Feature lifts are small, unstable, and mostly not significant once multiplicity is counted.** [B-fix]
   A reported EQ +0.29 logit (t +3.6, 1-hour), external −0.27 (t −2.9), confluence −0.25 (t −2.7, 5-min),
   draw −0.11 (t −2.4) and called the confluence and tier pillars "contradicted".
   - B applied Holm's correction to A's 22 tests (11 features × 2 timeframe groups). Only **EQ (1-hour, Holm p 0.007)**
     and **age** survive, and age has opposite signs on 5-min (+3.6) and 1-hour (−4.2), so it is not a stable feature.
   - External (Holm p 0.07), confluence (0.11) and draw (0.23) do **not** survive. Pooled over all 14 sets, confluence
     is −0.04 (t −0.7).
   - Correct wording: the confluence, tier and draw pillars are **unsupported** (no positive lift beyond distance), not
     proven harmful. A's other conclusion stands: a cross-market prior fitted leave-one-dataset-out *hurt* held-out
     log-loss by **−1.17%** (worse on 12 of 13 sets), so lifts must be measured per chart with shrinkage.
7. **The optimizer's curse is weak for this engine.** [B-fix] A argued the selected target's PoT is biased upward.
   In A's own replica the hand-score top-1 pick's excess over its baseline has **mixed signs** on clean sets
   (+2.6, +3.0, −0.7, −0.9, +0.7, +0.5 on 5-min; +1.7, −1.9, −0.5, −3.4, +0.3, −5.9 on 1-hour; ±2-4 SE). The PoT is not a
   noisy per-candidate estimate being maximised: every candidate at the same distance gets the same PoT. The real
   selection-related bias channels are different (see 3.1): (a) the *displayed* PoT uses `f_potModel` with a 50-bar drift
   (2067) while the baseline is driftless, and the proximity pillar favours the same drift side; (b) the selection rule may
   correlate with features the PoT model ignores. Both are handled by grading and a *gated* selected-target intercept.
8. **Target choice is a utility decision.** [A✓] Every picker's hit rate matched its baseline. Max expected reach
   `d·PoT(d)` delivered **1.10-1.43 ATR per target** against 0.86-1.09 for the hand score and 0.66-0.93 for nearest
   (13 intraday/1-hour sets). Driftless Brownian motion: `d·2Φ(−d/s)` peaks at **d = 0.752·σ√H, P = 0.452** (B re-derived:
   the first-order condition is Φ(−x) = x·φ(x)).
   - [B-fix] A wrote "within ±3 pp" for every picker on clean data. EURUSD 1-hour hand score is −6 pp (0.58 vs 0.64),
     about 2 SE.
9. **The single most valuable infrastructure is a candidate (shadow) ledger.** [A✓] About 2,500-3,500 probes per
   5,000 bars, design effect 1.4-2.8, SE of an excess hit rate 0.9-1.4 pp (selected-only: 1.4-1.7 pp in a replica that
   opens *more* trials than the engine). [B] It is also the only way to reach the sample sizes that calibration
   assessment needs: **≥ 100 events and ≥ 100 non-events, ideally 200** (Collins, Ogundimu & Altman 2016). The active
   ledger takes about 250 trials to get there, which many charts never reach.
10. **New engine finding: self-confluence.** [B] PDH/PDL/PWH/PWL pools are pushed at exactly `pdH/pdL/pwH/pwL`
    (1793-1799), and the same prices are confluence anchors (`aPDH…aPWL`, 957-960, 1931). `evaluate` (676-680) does not
    exclude a level's own anchor, so every key-level pool gets `conf ≥ 0.35` (≈ +5 score points at the default weights)
    for coinciding with itself. Tier already rewards these levels inside density (682). This double count favours exactly
    the levels whose measured lift is ≤ 0.
11. **Popular Pine "machine-learning" scripts are not statistical learners.** [A✓ + B]
    - The Lorentzian kNN (A, verified by B in the public v2 port, lines 335 and 394-413): its label is the negated
      *past* 4-bar move of the same bar, and it accepts neighbours whose distance is ≥ a running threshold. [B] Its
      `predictions`/`distances` arrays are also `var`, so the "neighbours" are a FIFO accumulated across bars.
    - [B] A widely copied Pine "logistic regression" (capissimo, v4, lines 89-97 and 115-121) evaluates the hypothesis
      with weight 0.0 inside the training loop, so the gradient never feeds back. Its "labels" are a deterministic
      transform of the input series. The output is a fixed function of the last few prices.

### 0.1 What B changed relative to A

| # | Change | Why |
|---|---|---|
| 1 | New tier-1 calibrator: gated **online Platt scaling** (CAL-4) | B's test: same safety as A's gated probit at a fraction of the code; theory from Gupta & Ramdas 2023 |
| 2 | A's CAL-4 (probit) demoted to CAL-9 ("measure first; apply to PoT only") | Its value on clean data is the readout, not the forecast; applying feature lifts to the score is not validated by log-loss |
| 3 | A's CAL-6 split: calibration moved into CAL-4, grading kept as CAL-6 and aligned with quant_pot QPOT-04 | Avoid two calibrators; selected-only data is too small for slope estimation |
| 4 | Feature-lift evidence re-graded after Holm correction | Only EQ (1-hour) survives |
| 5 | Optimizer's-curse relevance downgraded; drift channel added | A's own top-1 data shows mixed signs |
| 6 | Displayed-PoT gap corrected: it is `f_potModel` with drift (2067), not the random-level model | A's §3.1 said "the shown PoT is the random-level model" |
| 7 | CAL-2 gains a few-clusters guard and ρ tuning; CS validity conditions stated | Long H gives few 2H blocks; estimated variance gives only asymptotic validity |
| 8 | New CAL-5 (self-confluence), CAL-10 (base-integrity guard), CAL-11 (gate `f_raceAdj`) | Engine findings |
| 9 | CAL-3 gains a mirror role (SKEP-2) and stores the displayed-model PoT | Grade what the user sees; mirror cancels shared miscalibration |
| 10 | Line refs fixed: tier term is on 682 (not 683); `Trial` is 375-395 | Re-check |
| 11 | Literature figures A could not source are flagged "not re-verified"; the Optimizely "20% → under 5%" figure is practitioner-reported; Johari et al. themselves say Type I error "can easily increase fivefold" | Verification |
| 12 | Cross-sibling correction: Platt on **logit p**, σ(a + b·logit p), *does* contain the identity (a = 0, b = 1) | quant_pot.final §1.15 says Platt "excludes the identity"; that is true only for Platt on raw scores (Kull et al. 2017) |

---

## 1. Concepts (definitions and parameters)

Notation: candidate level i at bar t, distance `d` (ATR), side ±1, horizon H bars. The outcome is `y = 1` if the level is
touched within bars t+1..t+H. Pools need a trade-through (`high > edge` / `low < edge`, `touched` 623-626); arrays count a
touch (`≥` / `≤`). `p0 = pBase` is the distance-matched random-level probability (`f_potBase`, 1313-1322).
`logit(p) = ln(p/(1−p))`; Φ, φ are the normal CDF and density.

### A. Targets, baselines and labels

**1.1 Distance-matched random-level baseline (offset).** [A✓]
- Definition: `p0(d, side, regime) = P(a random level d ATR away on that side is touched within H)`.
- Engine estimate: the empirical excursion surface (`sUp/sDn`, 3 HTF regimes × 61 bins of `bStep`, 1059-1062; bumped
  from completed windows only, 1527-1532), blended with the driftless analytic first-passage prior,
  `(nEff·pE + priorM·pA)/(nEff + priorM)`, `priorM = 30`, `nEff = n/(0.6H)` (1284-1322). Clamped to [0.01, 0.99].
- Gate: `nMin = max(150, 20H)` windows per regime row, else pooled rows, else analytic (1289-1300).
- DOL role: the *null model*. A liquidity concept has value only if `y` exceeds `p0`.
- [B] Note: the regime rows mean p0 already contains the HTF-direction effect. "Edge over p0" is edge *beyond distance
  and HTF regime*, a strict test.
- Failure modes: the 0.95 cap inside `f_pot` feeds the prior (small, quant_pot B: ≤ 0.4 pp), the discrete grid, overlap,
  regime-row thinning, and corrupted data (roll gaps).

**1.2 Offset model.** [A✓] Every learner predicts relative to p0: `logit P(y=1|x) = logit(p0) + βᵀx` (logistic) or
`P = Φ(Φ⁻¹(p0) + μᵀx)` (probit). β = 0 reproduces the baseline exactly, so "no information" is the default and every
learned coefficient is a lift beyond distance.

**1.3 Label choices.** [A✓]
- (a) *Touch within H*: the ledger (`f_step` 1434-1459).
- (b) *Race*: target before invalidation (`raceSt`, 1079).
- (c) *Which pool first*: nearest BSL vs nearest SSL.
- (d) *Terminal pool*: the farthest pool reached before reversal.
- Geometric fact: on one side of price the nearest level is always touched before any farther one (continuous paths). So
  "which liquidity is taken next" is non-trivial only *across* sides (c, the race). Within a side, the question is *how far*
  the move extends (d).
- [B] Scoring (d): the probes of all candidates on one side at one bar form a survival-curve forecast of the maximum
  excursion. The sum of their Brier scores is a discretised **CRPS** of that forecast (threshold decomposition;
  Gneiting & Raftery 2007; Hersbach 2000). So the candidate ledger (CAL-3) grades the whole ladder, not just one level.
  For an ordinal "terminal pool" label, the ranked probability score (Epstein 1969) is the matching proper score.

**1.4 Baselines for selection.** [A✓ + B] Each is a rule the DOL must beat:
- (i) random level at the same distance (present: 1313-1322, 1463-1469);
- (ii) nearest candidate pool; (iii) nearest pool on the draw side; (iv) random candidate; (v) runner-up by score;
- (vi) opposite-side nearest pool (for the race);
- [B] (vii) **mirror level**: the same ATR distance on the opposite side, same bar, same rule (skeptic SKEP-2). The paired
  residual `(y − p0) − (y_m − p0_m)` cancels miscalibration that is common to both sides (clock, volatility regime, roll
  gaps).

### B. Proper scoring and calibration

**1.5 Proper scoring rules.** [A✓] Brier `B = mean (p−y)²`; log-loss `LL = −mean[y ln p + (1−y) ln(1−p)]`. Both strictly
proper (Gneiting & Raftery 2007). Brier skill `BSS = 1 − B/B_ref`, with the distance-matched p0 as the reference
(climatology is too easy). Grade the **uncapped** PoT: the 95% display cap makes a capped forecast improper near d ≈ 0.

**1.6 Murphy decomposition, reliability diagram, ECE, slope.** [A✓ + B]
- `B = REL − RES + UNC` (Murphy 1973). Reliability diagram: 5-10 forecast bins with consistency bars (Bröcker & Smith 2007).
- [B] Plug-in ECE with equal-width bins is biased upward at small n. Prefer equal-mass bins or the debiased estimator
  (Bröcker 2012; Ferro & Fricker 2012), as recommended by Roelofs et al. 2020 and Kumar et al. 2019. On a chart ledger,
  show calibration-in-the-large and the slope first (1.7b); show bins only when each has ≥ 30 effective samples.
- Calibration slope: logistic regression `y ~ a + b·logit p` (Cox 1958); b < 1 means over-confident.

**1.7 Platt / intercept recalibration.** [A✓ + B-fix]
- Full form `p' = σ(a + b·logit p)`, smoothed targets `y+ = (N+ + 1)/(N+ + 2)`, `y− = 1/(N− + 2)` (Platt 1999).
- Intercept-only with m pseudo-trials at the model mean P̄: `δ = logit((K + m·P̄)/(N + m)) − logit(P̄)`. The engine uses
  this for races (`f_raceAdj` 1367-1371, m = 20).
- [B-fix] Platt applied to **logit p** contains the identity (a = 0, b = 1), so it can leave a calibrated model untouched.
  Kull et al.'s objection (2017) applies to Platt on *raw scores* σ(a·s + b). Beta calibration
  `σ(a·ln p − b·ln(1−p) + c)` is a 3-parameter generalisation; the 2-parameter Platt-on-logit is enough here.
- Recalibration "hurts" an already calibrated model on small sets (A cited Niculescu-Mizil & Caruana 2005; the
  exact quote is not re-verified). B's replica agrees: every ungated map lost log-loss on the clean sets.

**1.7b Calibration hierarchy and minimum samples.** [B]
- Van Calster et al. 2016 define four increasingly strict levels:
  - *mean* (calibration-in-the-large: observed rate = mean forecast);
  - *weak* (Cox intercept 0 and slope 1);
  - *moderate* (forecast = observed rate at every forecast level, i.e. the reliability curve);
  - *strong* (correct for every covariate pattern; "unrealistic").
  They prove that moderate calibration guarantees non-harmful decisions. The ledger should report the levels in this
  order and stop at the level its sample supports.
- Minimum sample for assessing calibration: **≥ 100 events, ideally ≥ 200** (Collins, Ogundimu & Altman 2016,
  resampling study). For a binary ledger, require both events and non-events ≥ 100 before showing a slope. Divide by
  the design effect for overlapping windows.
- **Spiegelhalter z** (fixed-time, unbinned): `Z = Σ(y−p)(1−2p) / √Σ(1−2p)²p(1−p)`. It is weak against a pure
  intercept shift: GC 1-hour has CITL −4.25 pp but Z only 2.45, and Z/√deff ≈ 0.9 at deff 7.7. Use the cluster-robust
  excess test (CITL) as the primary check and Z as a secondary one.

**1.8 Isotonic regression / Venn-Abers.** [A✓] PAV isotonic fits overfit small calibration sets (A cites the
≈1,000-point crossover from Niculescu-Mizil & Caruana 2005; not re-verified, but consistent with the scikit-learn guidance
"isotonic … for large calibration sets"). Histogram-type calibration needs O(B/ε²) samples against O(1/ε²) for
scaling methods (Kumar et al. 2019). Venn-Abers (Vovk & Petej 2014) gives a calibrated interval under exchangeability,
which overlapping windows violate. Not recommended at ledger sizes.

**1.9 Online Platt scaling (OPS) and calibeating.** [B]
- OPS (Gupta & Ramdas, ICML 2023): Platt scaling is a 2-D logistic regression on the pseudo-feature `logit p`, so it can
  be learned online with regret guarantees against the best fixed Platt map in hindsight, for any (even adversarial or
  drifting) sequence.
- Algorithm: **Online Newton Step** (Hazan 2016, Alg. 12), verbatim defaults **γ = 0.1, ρ = 100**, `A₀ = ρI₂`,
  start `(a, b) = (0, 1)` (identity), feasible set ‖(a, b)‖ ≤ 100:
  `∇ₜ = (σ(θᵀz) − y)·z`, `Aₜ = Aₜ₋₁ + ∇ₜ∇ₜᵀ`, `θ ← Π_K(θ − (1/γ)·Aₜ⁻¹∇ₜ)`. Theorem 2.1 assumes `p ∈ [0.01, 0.99]`,
  exactly the clamp of `f_potBase`.
- Calibeating (Foster & Hart 2023): bin the expert's forecasts and replace each by the running outcome average of its bin
  ("tracking"); a hedged variant (HOPS) is calibrated even for adversarial sequences. Gupta & Ramdas found tracking + OPS
  (TOPS) had the lowest calibration error in their experiments (ε = 0.1, 10 bins).
- B's replica result: OPS behind a gate is the cheapest safe calibrator. Tracking/binning adds variance at ledger sizes
  (TOPS −1.4 … −3.1% ungated on clean data), so it is not recommended.

**1.10 Beta / temperature calibration.** [A✓] Beta calibration (Kull et al. 2017) and temperature scaling (Guo et al. 2017)
add nothing over Platt-on-logit at ledger scale.

### C. Shrinkage and small samples

**1.11 Beta-binomial posterior.** [A✓] With prior `Beta(m·p_prior, m·(1−p_prior))`, the posterior mean is
`(k + m·p_prior)/(n + m)`. Wilson's interval (`f_wilson`, 491-503) is the frequentist counterpart.

**1.12 Poisson-gamma lift shrinkage (hits vs expected).** [A✓]
- With `k` hits and `e = Σ p0` expected hits, `k ~ Poisson(λ·e)`, prior `λ ~ Gamma(α, α/λ0)`, the posterior mean is
  `(k + α·λ0)/(e + α)`.
- The engine's `(k+2)/(e+2)` is α = 2, λ0 = 1: a prior worth two expected hits.
- Prior sd of λ is `λ0/√α`: ±13% gives α ≈ 60, ±10% gives α ≈ 100. With overlapping trials, divide k and e by `deff`.

**1.13 Empirical Bayes / James-Stein.** [A✓, figures flagged] Shrink each family toward the pooled mean by
`s²/(s² + τ²)`, with `τ² = max(0, Var_between − mean s²)`. In Efron & Morris's baseball example the shrinkage estimator
cut total squared error about 3.5-fold (A quotes 17.56 → 5.01; not re-verified, ratio consistent). With 4 families τ² is
unstable, so use a fixed α plus a significance gate.

**1.14 Minimum-sample rules.** [A✓ + B] Until `n_eff = n/deff ≥ 30`, show a provisional state and do not let estimates
drive the score. Replace cliffs (`n ≥ 10 →` full effect, 1382) with continuous weights `n_eff/(n_eff + m)`. For calibration
slopes use 1.7b (≥ 100 events and non-events).

**1.15 Selection bias / Tweedie.** [B] For many noisy estimates `z_i ~ N(μ_i, σ²)`, Tweedie's formula
`E[μ|z] = z + σ²·d/dz log f(z)` (Robbins 1956; Efron 2011, JASA 106) de-biases the largest ones. This is the
empirical-Bayes cure for the winner's curse (1.24). Relevant to per-family or per-pillar readouts (CAL-7, CAL-9: report
shrunk lifts), not to the PoT itself.

### D. Online learners

**1.16 Online logistic regression (SGD / AdaGrad / FTRL).** [A✓] `w ← w + η(y − p)x − ηλ(w − w0)`. AdaGrad uses
per-coordinate `η_j = η0/√Σg_j²` (Duchi et al. 2011); FTRL-Proximal adds L1/L2 (McMahan et al. 2013). A constant
η = 0.05 without a prior cost 3.6-5.5% log-loss. Online Newton Step (1.9) is the second-order member that suits 2-3
parameters.

**1.17 Bayesian online probit (adPredictor; Graepel et al. 2010).** [A✓, numbers flagged]
- Each weight has a Gaussian posterior `N(μ_j, v_j)`. Prediction `P = Φ((o + μᵀx)/Σ)`, with `Σ² = 1 + Σ_j x_j² v_j` and
  offset `o = Φ⁻¹(p0)`.
- Update for `t = ±1`: `z = t(o + μᵀx)/Σ`, `v(z) = φ(z)/Φ(z)`, `w(z) = v(z)(v(z) + z)`;
  `μ_j += t·x_j·(v_j/Σ)·v(z)`; `v_j *= 1 − x_j²(v_j/Σ²)·w(z)`.
- Dynamics toward the prior with rate ε: `v' = v0·v/((1−ε)v0 + ε·v)`, `μ' = v'·((1−ε)μ/v + ε·μ0/v0)`.
- Step size ∝ remaining uncertainty, so shrinkage to the prior mean is automatic. Temper updates by ω < 1 for overlapping
  samples (A: ω = 0.25; ω ≈ 1/deff is the principled choice).
- A quoted relative information gain 61.24% vs −41.54% for uncalibrated naive Bayes; B could not re-open the paper, and
  web summaries confirm only that adPredictor beat a calibrated naive Bayes in the live system.

**1.18 Bayesian logistic with diagonal Laplace.** [A✓] Chapelle & Li 2011: batch MAP with prior `N(m_i, 1/q_i)`, then
`q_i += Σ x_ij² p_j(1−p_j)`. Needs an inner optimisation, so 1.17 is simpler in Pine.

**1.19 Naive Bayes / multiplicative lifts.** [A✓] `P ∝ p0·Π L_b` assumes conditional independence and double-counts
correlated features. It reaches its higher asymptotic error faster (Ng & Jordan 2002) and is poorly calibrated. The ICT-1
and `f_ctxMult` designs are of this type and cost 0.6-2.1% log-loss in A's test.

**1.20 Elo / Glicko / Bradley-Terry.** [A✓] Elo is SGD on the Bradley-Terry likelihood with K as learning rate
(Király & Qian 2017); Glicko adds a rating deviation (approximate Bayes, like 1.17). For "families competing in races"
this brings nothing beyond 1.17.

**1.21 kNN / Lorentzian classifiers in Pine.** [A✓ + B] Verified in the public v2 port:
- Features: up to 5 oscillators. Distance `Σ ln(1 + |Δ|)`. Loop over up to `maxBarsBack` (2,000), skipping `i % 4 == 0`.
- A neighbour is accepted when `d >= lastDistance`; after k entries `lastDistance` is reset to the slot at `k·3/4`
  (lines 394-413). So it does not return the k *nearest* neighbours.
- Label (335, 344): `src[4] < src[0] ? short : long`, pushed on the same bar as the features. That is the negated *past*
  4-bar move: contemporaneous, not a forecast (no look-ahead either).
- [B] `predictions` and `distances` are `var` arrays, so the neighbour list carries over between bars as a FIFO.
- Cost O(2000·F) per bar.
- The engine's histogram surface is the principled kNN-like estimator. Beyond 2-3 conditioning dimensions, use partial
  pooling (quant_pot QPOT-03).

**1.22 Pine "logistic regression" practitioner scripts.** [B] Inspected capissimo's v4 script (lines 89-97, 115-121):
the training loop computes `sigmoid(dot(X, 0.0, p))` (weight fixed at 0), so the "hypothesis" is always 0.5. The labels
`Y = log|X² − 1| + 0.5` are a deterministic transform of X, not outcomes. The data come from `security()` without a
lookahead/offset policy. Evidence value of such scripts: none. Lesson: any learner shipped here must be prequential, offset
by a baseline, and graded.

**1.23 Safe aggregation (gate / exponential weights / fixed share).** [A✓] Weights `w_e ∝ w_e·p_e(y)^η`. The Bayes mixture
(η = 1) has log-loss regret ≤ ln N on any sequence (Cesa-Bianchi & Lugosi 2006); tempering multiplies the bound by 1/η.
Fixed share mixes in α/N of uniform weight each step so the leader can change (Herbster & Warmuth 1998). The gate is the
hard version: use the model only while its cumulative log-loss is below the base's ("follow the leader" on two experts).

### E. Ranking and decision

**1.24 Learning to rank.** [A✓] Pointwise, pairwise (RankNet, Burges et al. 2005) and listwise (ListNet / Plackett-Luce,
Cao et al. 2007). Listwise or pairwise losses pay off for position-based utilities. The DOL utility decomposes per
candidate, so Bayes decision theory says: rank by `E[U_i] = P_i·u_i`, which needs calibrated pointwise `P_i` and an explicit
`u_i`.

**1.25 Expected reach.** [A✓] `E[U] = d·P(hit within H | d)`. Driftless BM, `s = σ√H`: `d·2Φ(−d/s)` peaks at
`d* = 0.752 s`, where `P = 0.452` and `E = 0.340 s`. Empirical: `d* = argmax_j (j·bStep)·S_j/n`. Under a martingale no
target choice changes the expected P&L of a trade (optional stopping), so this is a preference between hit rate and
distance, not an edge. [B] If the trader's unit is R (target vs invalidation), the analogous utility is
`d·P(target before invalidation)` from the race model; same caveat.

**1.26 Optimizer's / winner's curse.** [A✓ theory, B-fix relevance] The argmax of noisy unbiased estimates disappoints
on average (Smith & Winkler 2006); shrink before the argmax (1.13, 1.15). For the PoT the curse needs idiosyncratic
estimation noise across candidates, which a shared distance surface does not have. A's top-1 data show no systematic
negative excess (finding 7). Relevance: per-family / per-pillar statistics (shrink them) and the drift channel (3.1).

### F. Validity: leakage, overlap, snooping, peeking

**1.27 Prequential evaluation (Dawid 1984).** [A✓] Forecast with the state *before* the outcome is known, score after
resolution, learn only from resolved outcomes. The online equivalent of walk-forward testing.

**1.28 Overlapping labels.** [A✓ + B]
- H-bar windows share a path. Remedies:
  - cluster-robust variance in blocks of about 2H bars (engine `cluSt`, 1077, 1463-1469), with `deff = V_cluster/V_indep`;
  - uniqueness weights (López de Prado 2018, ch. 4);
  - [B] HAC/Newey-West with lag H−1, the classical treatment of overlapping forecast horizons (Hansen & Hodrick 1980).
- [B] Few clusters: with G < about 20-40 blocks, cluster-robust variances are biased downward and t-tests over-reject
  (Cameron, Gelbach & Miller 2008). Engine: G ≈ (calcBars − warmup)/(2H) = 78 at H = 30, 23 at H = 100, 5 at H = 450.
  Apply the `G/(G−1)` correction and require G ≥ 20 before showing a verdict.
- Purged/embargoed CV (López de Prado ch. 7) is the batch analogue. Prequentially, respect the open→resolution delay.

**1.29 Data snooping and multiplicity.** [A✓ + B] White's Reality Check (White 2000; Sullivan, Timmermann & White
1999). For per-chart readouts with several comparisons, use Holm or Bonferroni, or run the confidence sequence at α/m. B's
Holm check of A's lifts is in finding 6.

**1.30 Peeking / confidence sequences.** [A✓, formula verified]
- Re-testing `z ≥ 2` after each sample eventually produces a false positive; Johari, Pekelis & Walsh say Type I error
  "can easily increase fivefold" even at 10,000 samples. (The "Optimizely over 20% → under 5%" figure A quoted is a
  practitioner write-up, not the paper.)
- Two-sided normal-mixture boundary (Howard et al. 2021, eq. 14 / Prop. 5, l₀ = 1): `P(∀t: |S_t| < u(V_t)) ≥ 1 − α`,
  `u(v) = √((v + ρ)·ln((v + ρ)/(ρ·α²)))`, for S and −S sub-Gaussian with variance process V.
- [B] Tuning: `u(v)/√v` is smallest at `v = m` with `m/ρ = −W₋₁(−α²/e) − 1` (Howard Prop. 3). For α = 0.05 this is
  m ≈ 8.2ρ. So ρ = 10 is tightest near V ≈ 82 (about 370 trials at p ≈ 0.6), and ρ = 5 near V ≈ 41 (about 190 trials).
  Boundary in z units at ρ = 10: 3.66 / 3.18 / 3.06 / 3.04 / 3.10 at V = 10 / 25 / 50 / 100 / 250 (A).
- [B] Validity: centred Bernoulli residuals are sub-Bernoulli. A sub-Gaussian boundary is valid for them only after
  inflating V (Howard Fig. 2 / Prop. 11), or one can use the tighter beta-binomial boundary (Prop. 7). With the engine's
  estimated cluster variance, the result is an **asymptotic** CS (Waudby-Smith et al. 2021), and Ge & Liu (2026) extend
  that to serially dependent data with HAC variances. Adobe deployed asymptotic CSs in production A/B testing
  (Maharaj et al. 2023).

**1.31 Bandit feedback / selection bias.** [A✓] Grading only chosen targets conditions statistics on the policy; a
down-weighted family is chosen less and stops updating. Off-policy evaluation needs propensities (Li et al. 2011). The
simpler fix here is full information: grade every candidate (shadow probes).

**1.32 Concept drift.** [A✓] Forgetting (adPredictor ε, fixed share, exponential discounting). In A's test ε = 10⁻³ was
worse on 10/14 sets and better on 4 (≤ 0.2 pp, plus GC 1-hour). Variance dominates drift at these sizes. OPS adapts to drift
by construction (regret against the best fixed map) without a forgetting parameter.

**1.33 Learning-window path dependence.** [B] The ledger starts at `max(0, last_bar_index − calcBars) + warmup` (2038).
The Pine reference says `last_bar_index` "will change when new real-time bars appear" and that using it "can cause
indicator repainting". After a reload with more bars, every learned quantity (today `f_calMult`) is rebuilt from a
different start, so past target choices can differ. This is not look-ahead, but history is not reproducible across reloads.
Gated learners keep that effect near zero because their outputs stay at the neutral value until proven.

---

## 2. Evidence

### 2.1 Literature (numbers, grade, verification status)

| Claim | Numbers | Grade | Source | Verified by B |
|---|---|---|---|---|
| Two-sided normal-mixture CS | `u(v) = √((v+ρ)ln(l₀²(v+ρ)/(α²ρ)))`, l₀ = 1; optimum at m/ρ = −W₋₁(−α²/e) − 1 | strong (theory) | Howard, Ramdas, McAuliffe, Sekhon 2021, Ann. Stat., arXiv 1810.08240, eq. 14, Props 3, 5 | yes (paper text) |
| Peeking inflates Type I error | "can easily increase fivefold" even with 10,000 samples; mSPRT always-valid p-values deployed | strong | Johari, Pekelis, Walsh, arXiv 1512.04922 (Oper. Res. 2022) | yes |
| Asymptotic CSs with estimated variance; deployment | time-uniform CLT; Adobe production platform | strong / moderate | Waudby-Smith et al. arXiv 2103.06476; Maharaj et al. arXiv 2302.10108 | yes (abstracts) |
| Dependent-data asymptotic CS with HAC | near-optimal invariance principle under functional dependence | moderate (2026 preprint) | Ge & Liu, arXiv 2610.29288 | yes (abstract) |
| Online Platt scaling | ONS, γ 0.1, ρ 100, start (1, 0) as (b, a); O(log T) regret vs best Platt map; TOPS lowest calibration error | strong (theory + experiments) | Gupta & Ramdas, ICML 2023, arXiv 2305.00070 | yes (paper text) |
| Calibeating | Brier = refinement + calibration; binning on an expert's forecasts calibrates without losing refinement | strong (theory) | Foster & Hart, Theoretical Economics 2023, arXiv 2209.04892 | yes (abstract) |
| Calibration hierarchy | mean, weak, moderate, strong; moderate ⇒ non-harmful decisions | strong | Van Calster et al. 2016, J Clin Epidemiol 74:167-176 | yes (abstract) |
| Sample size to assess calibration | ≥ 100 events, ideally ≥ 200 | strong (large resampling study) | Collins, Ogundimu, Altman 2016, Stat Med 35:214-226 | yes (abstract) |
| Spiegelhalter z | `Σ(y−p)(1−2p)/√Σ(1−2p)²p(1−p)` | strong (classic) | Spiegelhalter 1986, Stat Med 5 | yes (formula, secondary) |
| ECE plug-in bias; debiased estimator | equal-mass bins and debiased estimator less biased | strong | Roelofs et al. arXiv 2012.08668; Kumar, Liang, Ma arXiv 1909.10155 | yes (abstracts) |
| Few clusters bias cluster-robust inference | over-rejection with few clusters | strong | Cameron, Gelbach, Miller 2008, REStat 90(3) | from knowledge |
| Overlapping horizons | MA(H−1) errors, HAC | strong | Hansen & Hodrick 1980, JPE 88 | from knowledge |
| Tweedie / selection bias | `E[μ|z] = z + σ²(log f)'(z)` | strong | Efron 2011, JASA 106:1602-1614 | yes (metadata) |
| Bayesian online probit | RIG 61.24% vs NB −41.54% (A) | strong (method); figures | Graepel et al. 2010, ICML | method yes; **figures not re-verified** |
| Platt vs isotonic; calibration can hurt calibrated models | crossover ≈ 1,000 points (A) | strong (method) | Niculescu-Mizil & Caruana 2005, ICML | **wording not re-verified**; direction consistent with scikit-learn docs |
| Platt smoothed targets | `(N+ +1)/(N+ +2)`, `1/(N− +2)` | strong | Platt 1999 | from A |
| NB vs logistic | NB reaches its higher asymptotic error faster | strong | Ng & Jordan 2002 | from A |
| Optimizer's curse | chosen alternative disappoints on average | strong (theory) | Smith & Winkler 2006 | from A |
| Mixture regret | Bayes mixture ≤ ln N; fixed share tracks switches | strong (theory) | Cesa-Bianchi & Lugosi 2006; Herbster & Warmuth 1998 | from A |
| Partial pooling | about 3.5× lower total squared error (A: 17.56 → 5.01) | strong (method) | Efron & Morris 1975, JASA 70 | **figures not re-verified** |
| Elo = SGD on Bradley-Terry | K = learning rate | strong | Király & Qian 2017, arXiv 1701.08055 | from A |
| Venn-Abers | calibrated interval, exchangeability | moderate-strong | Vovk & Petej 2014 | from A |
| Data snooping | Reality Check on the BLL rule universe | strong | Sullivan, Timmermann, White 1999; White 2000 | from A |
| TradingView continuous futures | back-adjustment disabled by default (B-ADJ button / "Adjust for contract changes") | strong (vendor documentation) | TradingView help centre 43000685266 (via search summary) | yes (search) |
| Pine kNN classifier mechanics | label `src[4] < src[0] ? short : long`; `d >= lastDistance`; `i % 4 != 0`; `var` FIFO | code inspection | public v2 port (MPL-2.0), lines 335, 339-344, 394-413 | yes (B read the source) |
| Pine "logistic regression" mechanics | weight fixed at 0 inside the loop; synthetic labels | code inspection | capissimo Pinescript-Laboratory v4, lines 89-97, 115-121 | yes (B read the source) |
| Sibling: engine surface calibration | slope 0.99, ECE 0.004 (1.2 M 5-min rows); analytic+drift slope 0.66 | moderate | quant_pot.final §2.2 | yes (report) |
| Sibling: draw vector has no skill | 49.9-51.6% for "which side first" | moderate | ict_struct, bias_dol | from A |

### 2.2 A's experiments (kept; re-checked by B)

**Data.** CME ES, NQ, CL, GC, RTY, YM at 5-min (Jan-Apr 2026, about 16.8k bars each) and 1-hour (Mar 2025-Apr 2026,
about 6k bars each); EURUSD 1-hour (5k bars); S&P 500 daily (1999-2019, 5k bars, H = 10).

**Replica (`cand_learn.py`).**
- Candidate families: chart pivots (L = 5); external (L = 20 pivots, previous-day high/low); FVG near edges (gap ≥ 0.1 ATR).
- EQ merging at 0.1 ATR, tests, coil/inducement, engine-like pillars, candidate range 0.25-10 ATR.
- Probes: one per level per H bars. Selected trials: max hand score on the draw side.
- Learners updated only at resolution bars and predicting at open: strictly prequential.
- [B] Simplifications that matter: no OBs, breakers, iFVGs, killzones, HTF FVGs or VP path cost. The baseline surface has
  **no HTF regime split** (the engine has three, so its cells are thinner). The draw proxy is SMA/return based.

**(a) Prequential log-loss vs the baseline (%, + = better, after 300 probes)** (`out_analyze.txt`; B re-read every cell)

| Dataset | n | BP | SGD | NB | EB family | MIX(BP) | GATE(BP) | Selected excess (pp) | Selected recal |
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

Settings: BP prior N(0, 0.15²) on 12 features, ω = 0.25; SGD η = 0.05; NB with ICT-1 parameters; EB α = 60, deff 3,
±15%; MIX η = 0.25, fixed share 0.005; GATE after ≥ 200 probes with lower cumulative LL; "Selected recal" = intercept
shift m = 20 on earlier selected trials.

The engine-style `f_calMult`, used as `p0·global lift·cm` (learned from selected trials): 5-min ES −0.22, NQ −0.57,
CL −0.52, GC −0.28, RTY −0.89, YM −0.57; 1-hour ES −1.21, NQ −0.68, CL −1.09, GC +2.10, RTY −0.62, YM −1.79;
EURUSD −1.01, S&P 500 −0.63.
- [B-fix] This is a *proxy*. In the engine, `f_calMult` multiplies the score; it never enters a probability. Its harm
  there is family tilt in selection (finding 4), not PoT miscalibration.

**(b) Pooled feature lifts** (`out_pooled_lift.txt`; offset logistic, dataset intercepts, cluster-robust t, 2H clusters)

| Feature | 5-min (6 sets, n 48,870, 1,593 clusters) | 1-hour (7 sets, n 22,135, 633 clusters) | All 14 | Holm p (B, 22 tests) |
|---|---|---|---|---|
| External family | −0.135 (t −1.1) | −0.270 (t −2.9) | −0.190 (t −2.9) | 1.00 / 0.071 |
| FVG family | −0.023 (t −0.2) | −0.029 (t −0.3) | −0.038 (t −0.6) | 1.00 / 1.00 |
| EQ | +0.082 (t +0.7) | **+0.291 (t +3.6)** | +0.164 (t +2.6) | 1.00 / **0.007** |
| Tested ≥ 2 | +0.028 (t +0.2) | −0.428 (t −2.5) | −0.261 (t −2.2) | 1.00 / 0.19 |
| Confluence | −0.249 (t −2.7) | −0.178 (t −1.7) | −0.043 (t −0.7) | 0.11 / 0.98 |
| Draw alignment | −0.031 (t −1.1) | −0.107 (t −2.4) | −0.036 (t −1.6) | 1.00 / 0.23 |
| Inducement | −0.231 (t −2.9) | +0.112 (t +0.9) | −0.149 (t −2.3) | 0.071 / 1.00 |
| Coil | −0.103 (t −1.7) | +0.246 (t +2.9) | +0.023 (t +0.5) | 0.98 / 0.071 |
| Age (log) | **+0.145 (t +3.6)** | **−0.260 (t −4.2)** | −0.028 (t −0.8) | **0.007 / 0.001** (opposite signs) |

- LODO (`out_lodo.txt`): a fixed cross-market prior changed held-out log-loss by **−1.17%** on average (12 of 13 worse).
  The online probit centred on that prior averaged +0.24%, the same as with a zero prior, all from GC 1-hour.
- [B] Reading: one lift (EQ on 1-hour) is solid; the rest are noise-level or sign-unstable. Do not hard-code any of them;
  measure per chart with shrinkage and multiplicity control.

**(c) Top-1 pickers** (`out_pickers.txt`; hit realised/baseline, mean distance ATR, ATR delivered = mean(y·d))

| Dataset | Nearest | Hand score | max d·PoT | hand × d·PoT | Random |
|---|---|---|---|---|---|
| ES 5m | .71/.70, 1.3, 0.81 | .61/.58, 2.0, 1.01 | .40/.40, 3.1, **1.15** | .48/.46, 2.6, 1.12 | .34/.33, 4.4, 0.95 |
| NQ 1h | .75/.75, 1.3, 0.87 | .64/.66, 1.9, 0.99 | .47/.45, 3.2, **1.43** | .51/.52, 2.8, 1.27 | .41/.36, 4.5, 1.18 |
| CL 1h | .74/.74, 1.2, 0.77 | .64/.64, 1.8, 0.92 | .44/.44, 3.0, **1.26** | .48/.48, 2.7, 1.18 | .32/.29, 4.9, 0.97 |
| EURUSD 1h | .74/.73, 1.3, 0.84 | **.58/.64**, 1.9, 0.86 | .39/.42, 3.4, **1.26** | .46/.48, 2.9, 1.21 | .32/.32, 4.6, 0.85 |
| 13 intraday/1h sets | 0.66-0.93 ATR | 0.86-1.09 | **1.10-1.43** | 1.12-1.32 | 0.71-1.18 |
| S&P 500 1D | 0.57 | 0.61 | 0.66 | 0.67 | 0.34 |

[B-fix] Hit rates match the baseline within about ±3 pp except EURUSD hand score (−6 pp) and GC 1-hour.

**(d) `f_calMult` under the null and an alternative** (`out_calmult_null.txt`; 4 families; outcomes clustered in
groups of 3, latent ρ = 0.5)

| n per family | engine mean abs(cm−1) | engine P(≥ 0.10) | engine P(at clamp) | EB (α 60, deff) mean abs(cm−1) | EB P(≥ 0.10) |
|---|---|---|---|---|---|
| 10 | 0.134 | 0.66 | 0.38 | 0.011 | 0.00 |
| 20 | 0.119 | 0.58 | 0.26 | 0.014 | 0.00 |
| 40 | 0.101 | 0.47 | 0.15 | 0.019 | 0.00 |
| 80 | 0.080 | 0.33 | 0.05 | 0.023 | 0.00 |
| 160 | 0.059 | 0.17 | 0.01 | 0.025 | 0.00 |
| 320 | 0.042 | 0.06 | 0.00 | 0.025 | 0.00 |

Alternative (family 0 true lift 1.10, ideal multiplier 1.073): engine RMSE 0.138 / 0.090 / 0.050 at n = 20 / 80 / 320;
EB RMSE 0.070 / 0.060 / 0.041. EB has the lower error everywhere, but reaches only 1.044 at n = 320.
- [B] Caveats: EB's "0%" under the null is partly by construction (α = 60 cannot move 10% at these n). The latent
  ρ = 0.5 corresponds to a smaller binary correlation, so `deff = 2` overstates the overlap slightly. The engine's
  per-family n is roughly 30-150 per 5,000 bars, squarely in the noisy range.

**(e) Peeking** (`out_peek.txt`; null, p ~ U(0.35, 0.9), z re-checked after every trial from n = 20)

| N trials | P(ever z ≥ 2) | P(ever z ≥ 1) | single look at N | normal-mixture CS (α .05, ρ 10) |
|---|---|---|---|---|
| 100 | 0.101 | 0.445 | 0.021 | 0.001 |
| 300 | 0.151 | 0.565 | 0.022 | 0.005 |
| 1000 | 0.200 | 0.647 | 0.026 | 0.014 |

[B] These are one-sided crossings with independent outcomes and known variance. The engine adds an estimated cluster
variance, which makes this an asymptotic statement (1.30).

**(f) Ledger precision** (`out_deff.txt`, per 5,000 bars)
- Candidate probes: 2,477-3,473 per 5,000 bars; deff (2H blocks) 1.4-2.8 on clean sets, 7.7 on GC 1-hour; SE of excess
  0.87-1.38 pp (1.92 on GC 1-hour).
- Selected trials: deff 0.9-1.4; SE 1.41-1.74 pp. The replica opens about 800 trials per 5,000 bars (no hysteresis); the
  engine opens fewer, so its SE is larger.
- Open-bar vs booking-bar cluster keys: deff within ±0.3.
- Per-family SEs are about 2× larger (3-5 pp), above typical lift sizes (2-7 pp).

### 2.3 B's experiments (new)

All use A's stored probes (`res_*.pkl`, learning probes only, sorted by open bar). A probe's prediction uses only probes
resolved strictly **before** its open bar (`rb < i`). Scores exclude the first 300 probes. Code: `calib_ml_b_tools/ops_test.py`.

**B1. Online calibrators** (`out_ops_final.txt`, `out_ops2.txt`, `out_ops3.txt`; LL change vs baseline, %)

| Dataset | OPS (γ .1, ρ 100) | OPS + dres | TOPS (10 bins) | bin-track base | intercept m 100 | **gated OPS** | gated TOPS | MIX(base, OPS) | A's BP | OPS final (a, b) |
|---|---|---|---|---|---|---|---|---|---|---|
| CL 1h | −1.71 | −1.87 | −2.56 | −1.15 | −0.08 | 0.00 | 0.00 | −0.49 | −0.74 | (+0.13, 0.87) |
| CL 5m | −0.99 | −1.07 | −1.54 | −1.07 | −0.07 | 0.00 | 0.00 | −0.31 | −0.28 | (−0.06, 0.97) |
| ES 1h | −1.32 | −1.39 | −2.46 | −1.57 | −0.11 | 0.00 | 0.00 | −0.44 | −0.63 | (−0.04, 1.02) |
| ES 5m | −0.64 | −0.67 | −1.76 | −0.83 | 0.00 | 0.00 | 0.00 | −0.19 | −0.39 | (+0.04, 0.95) |
| EURUSD 1h | −1.30 | −1.22 | −2.60 | −1.08 | −0.03 | 0.00 | 0.00 | −0.36 | −0.51 | (−0.07, 1.11) |
| **GC 1h** | **+5.60** | +5.70 | +4.73 | −0.57 | +2.05 | **+5.60** | +4.73 | **+6.50** | +8.79 | (+0.10, 1.00) |
| GC 5m | −0.62 | −0.81 | −1.49 | −0.99 | 0.00 | 0.00 | 0.00 | −0.15 | −0.40 | (+0.21, 0.85) |
| NQ 1h | −1.24 | −1.27 | −2.54 | −1.06 | −0.09 | 0.00 | 0.00 | −0.37 | −0.52 | (+0.04, 0.88) |
| NQ 5m | −0.63 | −0.64 | −1.46 | −0.96 | 0.00 | −0.03 | 0.00 | −0.15 | −0.40 | (+0.08, 0.90) |
| RTY 1h | −1.21 | −1.22 | −1.71 | −1.38 | −0.02 | 0.00 | 0.00 | −0.30 | −0.53 | (−0.24, 1.10) |
| RTY 5m | −0.69 | −0.73 | −1.44 | −0.54 | +0.12 | 0.00 | 0.00 | −0.12 | −0.15 | (+0.09, 0.94) |
| YM 1h | −1.79 | −1.88 | −3.07 | −1.39 | −0.09 | 0.00 | 0.00 | −0.57 | −0.79 | (−0.12, 1.04) |
| YM 5m | −0.74 | −0.67 | −1.52 | −0.59 | +0.07 | 0.00 | 0.00 | −0.23 | −0.30 | (+0.27, 0.84) |
| S&P 1D | −1.21 | −1.25 | −2.83 | −1.70 | −0.08 | −0.23 | 0.00 | −0.36 | −0.65 | (−0.04, 0.83) |

Step-size sensitivity (ungated OPS on clean sets / GC 1-hour): γ = 0.1, ρ = 100: −0.6 … −1.8% / +5.6%;
γ = 0.5, ρ = 300: −0.26 … +0.14% / +1.5%; γ = 1, ρ = 1000: −0.06 … +0.15% / +0.7%. (γ = 0.02 was worse:
−1.3 … −2.4%; a smaller γ is a *larger* step, 1/γ.)

Reading:
1. The step size trades protection against noise; the **gate removes that trade-off**: gated default-step OPS costs
   0.00 … −0.23% (mean −0.02%) and keeps +5.6% on the broken base.
2. Binning-based calibeating (TOPS, tracking) is too noisy at ledger sizes.
3. The intercept-only shift (m = 100) is nearly free but recovers only +2.05% on GC 1-hour.
4. A's 12-feature probit rescues more (+8.8%) and its mixture most (+10.5%). The extra comes from distance-curvature and
   family terms that a 2-parameter map cannot represent. That is why CAL-9 stays as an optional second tier.
5. The OPS slope settles at 0.83-1.11: the base is close to the identity on every clean set, consistent with A's slopes.

**B2. Base calibration-in-the-large** (same file): CITL (observed − forecast) −1.43 … +2.02 pp on clean sets, −4.25 pp
on GC 1-hour. Spiegelhalter z −1.06 … +2.84 (independence-assuming; divide by √deff ≈ 1.2-1.7). GC 1-hour has z = 2.45
but only ≈ 0.9 after deff 7.7: the unbinned test is weak against an intercept shift. Use the cluster-robust excess as the
primary calibration check.

**B3. Multiplicity** (`out_holm.txt`): finding 6 and table 2.2(b).

**B4. Optimizer's curse check** (A's `out_5min.txt`, `out_1h.txt`, "TOP-1 picker realised excess"): hand-score top-1
excess over baseline, clean sets: 5-min +2.6, +3.0, −0.7, −0.9, +0.7, +0.5; 1-hour +1.7, −1.9, −0.5, −3.4, +0.3, −5.9
(SE 1.9-3.8 pp). Mean ≈ −0.3 pp: no systematic upward bias of the selected PoT from selection alone.

### 2.4 Caveats

- The replica bounds what *simple* learners can extract from *engine-like* features; it is not the engine. That is why
  every proposal makes the engine measure itself on the user's chart.
- B's OPS test used a Euclidean norm projection (never binding) rather than the A-norm projection of exact ONS, and no
  overlap tempering. The proposed Pine version adds box bounds for UX safety; these were not active in the test range
  (final a ∈ [−0.24, 0.27], b ∈ [0.83, 1.11]).
- The broken-base evidence rests on one dataset (GC 1-hour). Its relevance rests on the TradingView default (no
  back-adjustment), not on a second replication.

---

## 3. Engine gap analysis (line references re-checked by B)

### 3.1 Audit of the ledger, the calibration and the scoring maths

| Item | Lines | Verdict | Detail |
|---|---|---|---|
| Ledger is leak-free | open 2038-2045 (bar close), grade 1549-1557 (`bar_index > t.bar0`), surface 1527-1532 (completed windows), all inside `if barstate.isconfirmed` (1518) | **correct** [A✓] | Trials are graded (step 2) before sweeps delete levels (step 3). `f_calMult` at bar t uses trials booked by bar t's close. On realtime bars `var` state rolls back each tick and commits at close. |
| Hit definitions | 623-626, 1436 | correct [A✓] | Strict for pools, touch for arrays. The surface counts a touch (≥ grid step): negligible over-prediction for pools. |
| `f_calMult` prior | 1376-1382 | **wrong (too weak)** [A✓] | α = 2 Poisson-gamma; the n ≥ 10 cliff and the [0.8, 1.2] clamp do all the regularisation (§2.2 d). |
| `f_calMult` overlap | 1376-1382 | **missing** [A✓] | Raw k, e; the panel's deff (2385-2386) is ignored. |
| `f_calMult` evidence gate | 1382 | **missing** [A✓] | Applied whenever n ≥ 10. |
| `f_calMult` data source | 1461-1474, 2038-2045 | **wrong (bandit feedback)** [A✓] | Selected trials only. |
| `f_calMult` effect on selection | 1935-1944 (applied before `evaluate`, which keeps `mult`), 2012 | **risk** [B-fix] | Persistent family tilt up to ±20% of the score; each booking moves it ~1-3%. Switches happen when a booking pushes a close contest across the 4-point hysteresis (147) or the 8-point side-flip margin. |
| **Displayed PoT vs baseline** | 2067 vs 1313-1322 | **gap** [B-fix] | The label uses `f_potModel(…, potMu·side)`: empirical surface blended with an *analytic prior carrying the 50-bar drift* (weight `priorM/(nEff + priorM)`, about 25% at H = 30 after 5,000 bars), capped at 0.95. The baseline is driftless. quant_pot: the drift is the largest PoT error (+3.66% LL; analytic slope 0.66). The proximity pillar's reach (665) uses the same drift, so selection favours drift-side levels whose displayed PoT is inflated by the same noise: the one real selection-bias channel. Fix: QPOT-01 (drift 0); then grade (CAL-6) and calibrate (CAL-4). |
| `f_raceAdj` | 1367-1371, used at 2130 | present, ungated [B-fix] | Intercept shift m = 20 on decided races of selected targets, applied unconditionally. Same risk as ungated recalibration (A: −0.36 … +0.28% LL on clean data). CAL-11. |
| EDGE z-test | 2383-2391 | **wrong (peeking)** [A✓] | §2.2 e. |
| Cluster blocks: count | 1463-1469, 2385 | **missing guard** [B] | Blocks = floor(bar/(2H)). With calcBars 5000 − warmup 300: G ≈ 78 at H = 30, 23 at H = 100, 11 at H = 200, 5 at H = 450. With few blocks `vEdge` is biased down. No G count, no G/(G−1) correction. |
| Cluster blocks: key | 1463-1469 | partial, low priority [A✓] | Keyed by booking bar; open-bar keying differed by ≤ 0.3 deff. |
| Wilson CI with deff | 2385-2387 | present (fixed-time) [A✓] | Kish `k/deff, n/deff`. Not time-uniform. |
| Per-family display | 2410-2418 | partial [A✓] | Hit % only, no expected %, so near families look better by distance alone. |
| Displayed PoT never graded | `Trial` 375-395 (no PoT field), 1461-1500 | **missing** [A✓] | No Brier, CITL, slope or reliability for the number the user sees (QPOT-04). |
| Baselines beyond the random level | 1313-1322 | **missing** [A✓] | No nearest / random-candidate / runner-up / mirror comparison. |
| Candidate-level grading | 2037-2046 | **missing** [A✓] | Active DOL only. Feature learning is statistically impossible at about 1 trial per H bars. |
| **Self-confluence** | anchors 1930-1933 (`aPDH, aPDL, aPWH, aPWL, …`), key pools pushed at `pdH/pdL/pwH/pwL` 1793-1799, `evaluate` 676-680 | **wrong** [B] | A PDH/PDL/PWH/PWL pool matches its own anchor, so `conf ≥ 0.35` (`wConf·0.35/wSum` = 5.25 points at defaults; 10.5 when PDH = PWH). Tier already rewards these levels in density (1.2·tier, 682). |
| Pillar weights | 141-145, 694 | hand-set; **unsupported** [B-fix] | Confluence (15) and tier in density assume key/external levels are hit more; pooled lifts are negative but not significant after multiplicity (Holm 0.07-0.11). Draw (30): ≤ 0 lift beyond distance (also ict_struct, bias_dol). EQ (0.9·eqCount, 682): supported on 1-hour (+0.29, Holm p 0.007). |
| Proximity pillar | 662-667 | partial [A✓] | Ad-hoc blend of linear, drift-carrying reach/0.95, taper below `minDistATR`. Principled: expected reach (1.25). |
| Score → probability separation | 2063-2068 | correct [A✓] | The displayed PoT does not use the score. Keep it so unless a gated learner shows skill. |
| Learning toggles | 149-150, 2038 | partial [A✓] | `useCal` on by default; no "measure only" mode; the ledger runs whenever `useCal` is on, even with the panel off (cheap). |
| Learning-window path dependence | 2038 | **caveat** [B] | `last_bar_index` changes between loads (Pine reference: "can cause indicator repainting"), so `f_calMult` history depends on chart length. Gated learners (neutral until proven) minimise the effect. |
| Base integrity | 1527-1532 | **missing guard** [B] | Roll gaps (TradingView continuous futures without B-ADJ) and data errors enter the surface unfiltered. GC 1-hour is the replica example: CITL −4.25 pp, deff 7.7. CAL-10. |

### 3.2 Concept status summary

| Concept | Status | Where / what differs |
|---|---|---|
| Distance-matched random-level baseline | present | 1313-1322; well calibrated (slope 0.93-1.04; CITL −1.4 … +2.0 pp) |
| Offset (lift-over-baseline) modelling | partial | implicit in `f_calMult` k/e; no feature-level offset model |
| Proper scoring of the displayed PoT | missing | no PoT field in `Trial` |
| Reliability / ECE / slope / calibration hierarchy | missing | — |
| Minimum-sample rules for calibration (≥ 100 events) | missing | verdict uses n < 20 only (2390) |
| Spiegelhalter / CITL tests | partial | the EDGE test is a CITL test on selected trials |
| Platt / intercept recalibration | partial | races only, ungated (`f_raceAdj` 1367) |
| Online Platt scaling / calibeating | missing | proposal CAL-4 (OPS; no binning) |
| Isotonic / Venn-Abers | n/a | not recommended at ledger sizes |
| Beta-binomial / Poisson-gamma shrinkage | wrong | α = 2, n ≥ 10 cliff, clamp |
| Empirical-Bayes pooling / Tweedie | missing | readouts should report shrunk lifts |
| Online logistic SGD | missing (good) | unregularised SGD is harmful |
| Bayesian online probit | missing | CAL-9 (second tier) |
| Naive-Bayes lifts | n/a | proposed elsewhere (ICT-1, `f_ctxMult`); replace |
| Elo / Glicko / Bradley-Terry | n/a | subsumed |
| kNN / Lorentzian, Pine "logistic regression" scripts | n/a | not learners in the statistical sense |
| Learning to rank (pointwise + utility) | partial | hand score; no explicit utility |
| Expected reach d·P(d) | missing | CAL-8 |
| Optimizer's curse correction | n/a for PoT (weak); missing for readouts | shrink readouts |
| Bandit feedback | wrong | `f_calMult` learns from selected only |
| Overlap / design effect | partial | `cluSt`; not in `f_calMult`; no few-cluster guard |
| Peeking-safe inference | wrong | 2390 |
| Prequential evaluation | partial | ledger prequential; no model-vs-model scoring |
| Safe aggregation (gate / mixture) | missing | CAL-4, CAL-9 |
| Data-snooping / multiplicity control | missing | relevant for CAL-7 |
| Concept drift | partial | `roll50` display only (1478) |
| Selection baselines (nearest, random, runner-up, mirror) | missing | CAL-3 |
| Self-confluence exclusion | wrong | CAL-5 |
| Base-integrity guard | missing | CAL-10 |

---

## 4. Proposals (best first; max 12)

### 4.0 The learner stack (answer to the brief)

The brief asks for "a concrete, leak-free online learner in Pine v6 that learns pillar weights or per-family hit rates
from the ledger and calibrates PoT, with shrinkage toward the hand-set prior". The evidence supports a three-layer design,
built in this order:

| Layer | What it learns | Data | Shrinkage / prior | Gate | Proposal |
|---|---|---|---|---|---|
| 1. Family multiplier | per-family hit rate beyond distance | candidate ledger (selected ledger until CAL-3 lands) | Poisson-gamma toward the global lift, α = 60, deff-scaled | time-uniform CS on the family residual | CAL-1 |
| 2. PoT calibration | 2-parameter Platt map of the displayed PoT; then the selected-target intercept | candidate ledger; active trials | ONS regulariser ρ = 100 starting at the identity; m = 100 pseudo-trials | prequential log-loss (FTL) after 200 probes; CS on the selected residual | CAL-4 |
| 3. Pillar lifts | 11 offset-probit coefficients | candidate ledger | Gaussian prior centred on the hand-set pillar weights (κ = 0.3), sd 0.15 | measure only; apply to PoT behind the mixture | CAL-9 |

Leak-freedom, for every layer:
- inputs are frozen on the probe or trial at its open bar (the engine's confirmed close);
- updates run only at the resolution bar, inside the confirmed-bar block;
- gates use only resolved outcomes;
- realtime ticks only read the parameters.

What not to build (measured): unregularised SGD (−3.6 … −5.5%), naive-Bayes lifts (−0.6 … −2.1%), hard-coded
cross-market lifts (−1.17%), binning/tracking calibration (−1.4 … −3.1%), Lorentzian kNN, isotonic/Venn-Abers.

Common Pine v6 rules for every sketch:
- All state updates run inside the existing `if barstate.isconfirmed and not na(atr) and atr > 0` block (1518). Live
  readouts reuse the last confirmed state.
- A function cannot reassign a global scalar, so mutable statistics live in `var array<float>` (as `stN`, `raceSt` do);
  `.set()` on a global array inside a function is allowed.
- Helpers are declared after what they use: PURE HELPERS for maths (after `f_sigm`, 489); STATE HELPERS after `f_potBase`
  (1322) for ledger helpers; inputs at the top.
- UDT fields may be collections ("UDTs … can contain … fields that can be of any supported type, including collection
  types", `type_system.md`). Collections ≤ 100,000 elements; any loop ≤ 500 ms per bar (`limitations.md`).
- `for [k, a] in anchors` is a verified construct (CONTEXT.md).

---

### CAL-1 (P1, S) · Neutralise `f_calMult`: overlap-aware, evidence-gated empirical-Bayes family multiplier [A✓, refined]

**Why.** Mostly noise at real ledger sizes (§2.2 d); bandit feedback; no overlap correction; it tilts selection between
families by more than the hysteresis (finding 4).

**Algorithm.**
1. `gl = (K + 2)/(E + 2)`: the global lift (all families).
2. `deff = max(1, vCl/vInd)` from the panel's cluster variance (2384-2386).
3. Posterior family lift, prior centred on the global lift: `post_g = (k_g/deff + α·gl)/(e_g/deff + α)`, α = `calPrior`
   (default 60 expected hits, prior sd ≈ 13%).
4. Evidence gate: residual `S_g = k_g − gl·e_g`, variance `V_g = deff·Σ_g p(1−p)` (`stPV`). Apply only if
   `|S_g| ≥ f_csBound(V_g, 10, 0.10)`.
5. `cm_g = gate ? clamp(post_g/gl, 0.85, 1.15) : 1.0`. No n ≥ 10 cliff.
6. Once CAL-3 exists, take `k_g, e_g, V_g` and deff from the **candidate** ledger (full information). Per-family n then
   rises from about 30-150 to about 600-900 per 5,000 bars, enough to detect lifts of about 10%.

**Pine v6 sketch.**
```pine
// PURE HELPERS (after f_sigm, ~489): two-sided normal-mixture CS radius (Howard et al. 2021, eq. 14, l0 = 1)
f_csBound(float v, float rho, float alpha) =>
    float vv = math.max(v, 0.0) + rho
    math.sqrt(vv * math.log(vv / (rho * alpha * alpha)))

// INPUTS (G_SCORE, next to useCal at 149; tooltip of useCal updated accordingly)
float calPrior = input.float(60.0, "Calibration Prior (expected hits)", minval = 5.0, step = 5.0, group = G_SCORE,
  tooltip = "How strongly each family's hit rate is pulled toward the overall rate. A family is only nudged once its difference is proven by a test that stays valid however often you look.")

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
(`stK` is `array<int>`; assigning its element to a `float` variable is an implicit int→float cast.)

**UX.** Full panel family rows (2411-2418): `FVG 71% · exp 69% · ×1.00`, with `*` when the gate is open.

**Ledger check.** Count target switches (`pickId != activeId` events) with the old and new multiplier. Expected: fewer
switches, EDGE unchanged.

**Evidence.** Moderate (§2.2 d; Poisson-gamma and CS theory strong).

**Risk.** Slow to detect a real family lift on the selected ledger (true 7% → 4.4% at n = 320). Acceptable: measured lifts
are below the noise floor; CAL-3 fixes the sample size.

**Effort.** S (about 20 lines).

---

### CAL-2 (P1, S) · Peeking-safe EDGE verdict with a few-clusters guard and expected rates [A✓ + B]

**Why.** False "✓ EDGE" 10-20% and false "~ WEAK" 45-65% under the null (§2.2 e). Family rows hide the expected rate.
[B] At long horizons the block variance rests on too few blocks (3.1).

**Algorithm.**
- [B] `cluSt` gains a 4th slot: the number of closed blocks G (incremented in `f_book` when `blk` changes and the old
  block id ≥ 0). Small-sample factor `cG = G ≥ 2 ? G/(G−1) : 1`.
- `S = kA − ΣpBase`, `V = cG·vEdge`. Always-valid band in pp: `±100·f_csBound(V, ρ, 0.05)/nA`.
- ρ: 10 (tightest near 370 trials) or [B] 5 (near 190 trials), closer to typical active-ledger sizes. Use the same ρ
  everywhere for consistency.
- Verdict:
  - `nA/deff < 30` or `G < 20` → `CALIBRATING` (with "H too long for the window" when G is the binding limit);
  - `S ≥ bnd` → `✓ EDGE`;
  - `S ≤ −bnd` → `✕ NEGATIVE`;
  - else `~ UNPROVEN ±x pp`.
- Keep Wilson as the fixed-time interval for the hit rate.
- Family rows: `hit% / exp%` with `exp% = 100·stPE[g]/stN[g]`.

**Pine v6 sketch (panel 2383-2397; `f_book` 1463-1468).**
```pine
// STATE (1077): [block id, open-block Σresidual, Σ closed-block residual², closed blocks]
var array<float> cluSt = array.from(-1.0, 0.0, 0.0, 0.0)
// f_book, inside `if blk != cluSt.get(0)`, before resetting:
if cluSt.get(0) >= 0
    cluSt.set(3, cluSt.get(3) + 1.0)
// panel
float  G       = cluSt.get(3)
float  cG      = G >= 2 ? G / (G - 1.0) : 1.0
float  V       = cG * vEdge
float  S       = kA - stPE.get(4)
float  bnd     = f_csBound(V, 10.0, 0.05)
float  nEffA   = nA / math.max(deff, 1.0)
string verdict = nEffA < 30 or G < 20 ? "CALIBRATING" : S >= bnd ? "✓ EDGE" : S <= -bnd ? "✕ NEGATIVE" : "~ UNPROVEN"
string band    = "±" + str.tostring(100.0 * bnd / nA, "0.0") + "pp"
```

**Evidence.** Strong (Howard et al. 2021; Johari et al.; Cameron et al. 2008) and moderate (A's simulation).

**Risk.** The band is wider (z ≈ 3.0-3.7), so the verdict says UNPROVEN more often, which is honest. With the
mirror control of SKEP-2 the same boundary applies to the paired residual.

**Effort.** S.

---

### CAL-3 (P1, M) · Candidate (shadow) ledger with a baseline suite, mirror role and "ATR delivered" [A✓ + B]

**Why.**
- Full-information grading removes the bandit-feedback bias (1.31).
- It raises the effective sample 2-3× (§2.2 f) and is the only route to the ≥ 100 events + non-events that calibration
  needs (1.7b).
- It answers the user's question: does the engine's choice beat "nearest pool", a random candidate, the runner-up or the
  mirror?
- It is the data source for CAL-1, CAL-4, CAL-6, CAL-7 and CAL-9, and supersedes ICT-1's mechanics.

**Type (after `Trial`, ~396).**
```pine
type Probe
    int   lvId
    int   grp            // 0 chart liq · 1 ext liq · 2 FVG · 3 OB/BRK
    int   side
    bool  liq
    float edge
    int   bar0
    float pb             // f_potBase at open (distance-matched random level, driftless)
    float pm             // [B] displayed-model PoT at open, before the 95% display cap (= pb once QPOT-01 lands)
    float d0             // distance (ATR) at open
    float pO   = na      // [B] CAL-4 calibrated PoT at open
    float pM   = na      // CAL-9 learner probability at open
    float pG   = na      // CAL-9 mixed probability at open
    int   role = 0       // 0 routine · 1 active DOL · 2 nearest · 3 random candidate · 4 runner-up · 5 mirror [B]
    array<float> x       // CAL-9 feature vector at open; na when the learner is off
```
Add `int lastProbe = -100000` to `Level` (317-345).

**State (after 1080).**
```pine
var array<Probe> probes = array.new<Probe>()
const int NPROBE = 256
// routine-probe stats per family + ALL: [n, k, Σpb, Σpb(1-pb)] in blocks of 4
var array<float> cdSt = array.new<float>(5 * 4, 0.0)
// role stats for roles 1..5: [n, k, Σpb, Σpb(1-pb), Σ y·d0]
var array<float> rlSt = array.new<float>(6 * 5, 0.0)
// candidate cluster variance (2H blocks keyed by bar0 block): [block id, open Σres, Σ closed res², blocks]
var array<float> cdClu = array.from(-1.0, 0.0, 0.0, 0.0)
```

**Snapshot** (step 17, after `lv.evaluate`, within `inCalc` and past `warmup`):
```pine
for lv in pool
    float dA = math.max(0.0, lv.distance(close)) / atr
    if bar_index - lv.lastProbe >= H and dA >= 0.25 and dA <= maxATR and probes.size() < NPROBE
        float dP = dA * atr
        probes.push(Probe.new(lv.id, lv.grp(), lv.side, lv.isLiquidity(), lv.nearEdge(), bar_index,
          f_potBase(dP, lv.side), f_potBase(dP, lv.side), dA))   // pm: swap in the uncapped f_potModel when it exists
        lv.lastProbe := bar_index
```
Fill `pO` (CAL-4) and `x`, `pM`, `pG` (CAL-9) on the new probe when those layers are on.

**Role probes.** Opened when step 20 pushes a new `Trial` (2045); they bypass `lastProbe` and never feed learning:
- active DOL (1);
- nearest candidate with `dA ≥ minDistATR` (2);
- deterministic pseudo-random candidate, `idx = int(math.abs(math.sin(bar_index * 12.9898) * 43758.5453)) % pool.size()`
  (3);
- runner-up by score (4);
- [B] mirror (5): a virtual level at `close − side·(edge − close)` with the same `liq` rule and `pb` for the opposite
  side. It needs no pool level; `lvId = −1`.

**Grading** (new step 2b right after 1550-1557, before sweeps delete levels):
```pine
if probes.size() > 0
    for i = probes.size() - 1 to 0
        Probe p = probes.get(i)
        if bar_index > p.bar0
            bool hit = p.liq ? (p.side == 1 ? high > p.edge : low < p.edge) : (p.side == 1 ? high >= p.edge : low <= p.edge)
            if hit or bar_index - p.bar0 >= H
                f_probeBook(p, hit ? 1 : 0)
                probes.remove(i)
```
`f_probeBook` (STATE HELPERS, after `f_potBase`):
- role 0 → `cdSt` for its family and ALL (`n += 1, k += y, e += pb, v += pb(1−pb)`); `cdClu` residual `y − pb` keyed by
  `floor(p.bar0/(2H))`; CAL-4 and CAL-9 updates;
- role > 0 → `rlSt` (also `Σ y·d0`).

**UX (Terminal, Accuracy = Full).**
- `CANDIDATES  hit 52% / exp 51%  (+1.0pp ±1.9)`
- `DOL vs NEAREST +3.1pp · RANDOM +4.0pp · #2 +0.8pp · MIRROR +1.2pp`, with the CAL-2 band on each paired residual.
- `ATR DELIVERED  DOL 1.12 · nearest 0.81 · random 0.95`.

**Cost.** ≤ 256 probes × O(1) per bar plus O(pool) snapshots. At most one open routine probe per level (the next opens H
bars after the previous one), so about poolMax + 5 open probes in practice.

**Evidence.** Moderate (A's replica: 2.5-3.5k probes per 5,000 bars, deff 1.4-2.8, SE 0.9-1.4 pp; Li et al. 2011;
SKEP-2 for the mirror).

**Risk.** Shared paths across probes (handled by `cdClu`); the cap can bind on huge pools (drop the farthest routine probes
first).

**Effort.** M (about 90 lines).

---

### CAL-4 (P1, M) · Gated online Platt scaling of the displayed PoT on the candidate ledger, plus a gated selected-target intercept [B; replaces A's CAL-6 calibration part]

**Why.**
- The displayed PoT is never graded or corrected. The base is well calibrated on clean data, but realistically broken on
  roll-gap futures charts (TradingView default) and possibly on other data artefacts.
- Gated OPS (Gupta & Ramdas 2023) cost 0.00 … −0.23% LL on 13 clean sets and gained +5.6% on the broken base (§2.3 B1).
- It is far simpler than the probit: two parameters, a 2×2 matrix, no feature vectors.
- Calibrating on the candidate ledger gives about 10× the data of the active ledger. The selected-target intercept then
  corrects only what is specific to the selection rule, behind its own test.

**Inputs (G_ACC).**
```pine
string calPot = input.string("Auto (when proven)", "PoT Self-Calibration", options = ["Off", "Measure", "Auto (when proven)"], group = G_ACC,
  tooltip = "Measure: grades how well PoT matched reality on this chart. Auto: also corrects PoT, but only while the correction has out-predicted the raw PoT on this chart.")
```

**State (after 1080).**
```pine
var array<float> opsTh = array.from(0.0, 1.0)            // Platt map on logit p: [a, b], starts at the identity
var array<float> opsA  = array.from(100.0, 0.0, 100.0)   // ONS matrix A = ρ·I (ρ = 100), stored [a11, a12, a22]
// prequential sums on routine probes: [n, ΣLL raw, ΣLL ops, Σ(pm-y)², Σ(pO-y)², Σpm, Σy]
var array<float> opsSt = array.new<float>(7, 0.0)
// selected-target stage on active trials: [n, Σy, ΣpShow, ΣpShow(1-pShow)]
var array<float> selSt = array.new<float>(4, 0.0)
```

**Helpers (STATE HELPERS, after `f_potBase`; `f_logit` clamps to [0.005, 0.995], 484-486).**
```pine
f_opsMap(float p) =>
    f_sigm(opsTh.get(0) + opsTh.get(1) * f_logit(p))

f_ll(float p, int y) =>
    float q = f_clamp(p, 0.001, 0.999)
    y == 1 ? -math.log(q) : -math.log(1.0 - q)

// Online Newton Step for the 2-D Platt problem (Gupta & Ramdas 2023, Alg. 1: gamma 0.1, rho 100; 1/gamma = 10)
f_opsUpdate(float p, int y) =>
    float z   = f_logit(p)
    float r   = f_opsMap(p) - y
    float g1  = r * z
    float a11 = opsA.get(0) + r * r
    float a12 = opsA.get(1) + r * g1
    float a22 = opsA.get(2) + g1 * g1
    opsA.set(0, a11)
    opsA.set(1, a12)
    opsA.set(2, a22)
    float det = math.max(a11 * a22 - a12 * a12, 1e-12)
    // UX safety box instead of the norm ball; inactive in the tested range (a -0.24..0.27, b 0.83..1.11)
    opsTh.set(0, f_clamp(opsTh.get(0) - 10.0 * (a22 * r - a12 * g1) / det, -1.0, 1.0))
    opsTh.set(1, f_clamp(opsTh.get(1) - 10.0 * (a11 * g1 - a12 * r) / det, 0.5, 1.5))
    true

f_opsOn() =>
    calPot == "Auto (when proven)" and opsSt.get(0) >= 200 and opsSt.get(2) < opsSt.get(1) - 1.0
```

**Data flow.**
1. Snapshot (CAL-3): for role-0 probes set `p.pO := f_opsMap(p.pm)`, using the state before any outcome of this probe.
2. `f_probeBook`, role 0, when `calPot != "Off"`:
   - `opsSt += [1, LL(pm), LL(pO), (pm−y)², (pO−y)², pm, y]`;
   - then `f_opsUpdate(p.pm, y)`.
   The order (score with the stored open-bar forecasts, then learn) keeps it prequential.
3. Live readout (2067):
   ```pine
   float pRaw = f_potModel(math.max(0.0, activeLv.distance(close)), activeLv.side, potMu * activeLv.side)
   float pCal = f_opsOn() ? f_opsMap(pRaw) : pRaw
   activePoT := sweptNow ? 0.95 : math.min(0.95, f_sigm(f_logit(pCal) + selDelta))
   ```
   With `selDelta` from step 4 (0 until proven). The 95% cap stays display-only (QPOT-09). [Note: `f_potModel` caps at
   0.95 internally today; grading should use the uncapped value once QPOT-09 splits it.]
4. Selected-target stage. `Trial` gains `float pShow` (`pCal` at open, uncapped). In `f_book`:
   `selSt += [1, y, pShow, pShow(1−pShow)]`. Once per confirmed bar:
   ```pine
   float nS  = selSt.get(0)
   float pS  = nS > 0 ? selSt.get(2) / nS : 0.5
   float res = selSt.get(1) - selSt.get(2)
   bool  okS = calPot == "Auto (when proven)" and nS / math.max(deff, 1.0) >= 30 and math.abs(res) >= f_csBound(deff * selSt.get(3), 10.0, 0.05)
   selDelta := okS ? f_logit((selSt.get(1) + 100.0 * pS) / (nS + 100.0)) - f_logit(pS) : 0.0
   ```
   Here `selDelta` is a `var float` and `deff` is the active ledger's design effect from CAL-2.

**UX.**
- Terminal Full: `PoT CAL  ✓ on · a +0.04 b 0.97 · ΔLL +0.8% · n 2,140` or `off (raw is better)`, and
  `SEL ADJ  +0.0 (unproven)`.
- Clean: the label shows the (possibly calibrated) PoT. Tooltip: "self-calibrated on this chart" when on.
- Data window: "PoT raw %" and "PoT shown %".

**Leak-freedom.** As in 4.0: forecasts frozen at open, updates at resolution, gates on resolved data, ticks read-only.

**Evidence.** Strong theory (Gupta & Ramdas 2023 regret bound; Cesa-Bianchi & Lugosi 2006 for gating). Moderate
empirics (§2.3 B1). The selected-stage gate follows A's finding that ungated recalibration of selected targets is
−0.36 … +0.28% on clean data.

**Risk.**
- One broken-base dataset in the evidence.
- Gate flicker (a 1-nat margin is used; the replica used 0).
- Depends on CAL-3. Without CAL-3, run OPS on active trials only; it will rarely pass the gate (few samples), which is
  safe.

**Effort.** M (about 60 lines on top of CAL-3).

---

### CAL-5 (P2, S) · Remove self-confluence from the confluence pillar [B]

**Why.** Key-level pools (src 6/7) are created at exactly the anchor prices `aPDH/aPDL/aPWH/aPWL` (957-960, 1793-1799),
so `evaluate` (676-680) counts each as confluent with itself: +5.25 points at default weights (10.5 when PDH = PWH).
Density already rewards them through tier (682). The measured confluence lift is ≤ 0 (not significant), so this is a
systematic tilt with no support.

**Change.**
- Step 17 (1930-1933): keep fixed anchor slots, `na` allowed, so the index identifies the anchor:
  `array<float> anchors = array.from(aPDH, aPDL, aPWH, aPWL, dayEQ, midOpen, ldnOpen, nyOpen, htfEQ)`.
- `evaluate` (676-680):
  ```pine
  for [k, a] in anchors
      bool own = this.src >= 6 and k <= 3 and math.abs(a - this.price) <= syminfo.mintick
      if not na(a) and not own and a >= aLo and a <= aHi
          hits += 1
  ```
  This drops a key pool's match with its own print, and with another key anchor at the identical price (the same print
  counted twice). A PDH that is merely *near* PWH keeps its confluence.
- The HTF-objective key (`oKey`, 1986) uses `lv.conf` and is fixed automatically.

**Ledger check.** Share of DOLs that are PDH/PDL/PWH/PWL before and after; EDGE and CAL-7's confluence readout.

**Evidence.** Code inspection (certain); effect size from the pillar arithmetic. Moderate that removing it is neutral to
positive (confluence lift ≤ 0).

**Risk.** Key levels lose about 5 points, so they become DOL slightly less often. That is the intended correction.
Users who like key levels keep tier and EQ.

**Effort.** S (about 6 lines).

---

### CAL-6 (P2, S) · One PoT scorecard (QPOT-04) plus a candidate scorecard, displayed by the calibration hierarchy [A's CAL-6 grading part + B]

**Why.** The displayed PoT must be graded. QPOT-04 already specifies the active-trial scorecard (`Trial.pPot`,
`potSt`, reliability bins). Build it once, add the candidate-ledger version (CAL-3/CAL-4 sums), and show only what the
sample supports.

**Display rules (calibration hierarchy, 1.7b).**
1. **Mean** (CITL): `obs − pred` in pp with the CAL-2 band. Shown when `n_eff ≥ 30`.
2. **Weak**: slope = the OPS slope `b` (CAL-4) on candidates. On active trials, 3 Newton steps on 10-bin sufficient
   statistics `[n_b, Σlogit_b, Σy_b]`. Shown only when events and non-events are each ≥ 100 (Collins 2016), divided by
   deff.
3. **Moderate**: 5-bin strip (equal-mass bins preferred; equal-width acceptable) showing only bins with ≥ 30 effective
   samples, as `pred→obs` per bin.
4. Brier, BSS vs the distance-matched base, and LL. Spiegelhalter z as a secondary check (divided by √deff).

**UX (Full).** `PoT GRADE  mean −0.8pp ±2.1 · slope 0.97 · BSS +0.3% · n 2,140 cand / 212 DOL` plus the strip
`35→33 · 48→50 · 62→61 · 76→74`.

**Evidence.** Strong (Murphy 1973; Van Calster 2016; Collins 2016; Roelofs 2020).

**Risk.** Panel width; keep it in Full only.

**Effort.** S on top of QPOT-04 and CAL-3.

---

### CAL-7 (P2, S) · Pillar information readout ("which pillars carry information on this chart") [A✓, multiplicity tightened]

**Why.** Traders want to know which ICT claims hold on their symbol. Lifts are heterogeneous and mostly small (§2.2 b).
A measurement-only readout cannot overfit the score.

**Algorithm.**
- At snapshot (CAL-3), record pillar tertiles `tq_j ∈ {0, 1, 2}` for `fresh`, `conf`, `dens`, `draw` (tertile cut-points
  from running means of the previous 500 probes, or fixed thirds of [0, 1]) and bits EQ, EXT, KZ.
- At resolution, book `[n, k, e, v]` per (pillar, tertile) into `pilSt = array.new<float>(7 * 3 * 4, 0.0)`.
- Readout: `excess(top) − excess(bottom)` in pp. Significance by the CAL-2 boundary at **α = 0.05/7** (Bonferroni over 7
  readouts), marked `*`.
- [B] Report the shrunk value: `diff·V_prior/(V_prior + V)` with a prior sd of 3 pp. This is the Tweedie/James-Stein guard
  against the winner's curse when the user reads the biggest number.

**UX (Full).** `PILLARS  dens +1.2 · conf −3.4* · draw +0.4 · fresh −0.8 · EQ +4.1*` (pp, top vs bottom third, shrunk).

**Evidence.** Moderate (A's pooled lifts; B's Holm check shows only EQ survives pooled, so expect few stars).

**Risk.** Users may over-read single stars; the shrinkage and α/7 keep false stars rare.

**Effort.** S (reuses CAL-3).

---

### CAL-8 (P2, S) · Expected-reach proximity pillar and a "Target Objective" input [A✓]

**Why.** PoT is geometry, so choosing among candidates trades hit rate against distance. `d·P(d)` encodes that trade
from first principles and from the chart's own surface. It peaks near 0.75σ√H at about 45% PoT. Replica: +20-45% more ATR
delivered per target than the hand-score pick, with the hit rate still matching its forecast.

**Algorithm.**
- `P(d) = f_potBase(dist, side)`; `ER = dAtr·P(d)`.
- `ERmax` once per confirmed bar: `max_j (j·bStep)·S_j/n` over the current regime row, or `0.34·σ√H/atr` while warming up.
- `erN = clamp(ER/ERmax, 0, 1)` (the near taper comes for free because ER → 0 as d → 0).
- Input `tgtObj` = "Hit Rate" (legacy prox) / "Balanced" (`√(legacy·erN)`, default) / "Reach" (`erN`).
- Ledger: `Σ y·d0` per family and per CAL-3 role, plus a data-window plot.

**Pine v6 note.** `evaluate` (661) is declared before STATE, so it cannot call `f_potBase` (1314), which reads `var`
arrays. Compute `pR = f_potBase(dist, lv.side)` at the call site (1948) and pass `pR` and `erMax` as new `evaluate`
parameters:
```pine
float er     = dAtr * pR
float erN    = f_clamp(er / math.max(erMax, 1e-6), 0.0, 1.0)
float legacy = (0.5 * lin + 0.5 * reach) * (0.30 + 0.70 * taper)
this.prox   := dAtr >= maxATR ? 0.0 : tgtObj == "Reach" ? erN : tgtObj == "Balanced" ? math.sqrt(legacy * erN) : legacy
```

**Evidence.** Strong theory (decision theory, first-passage optimum); moderate replica (§2.2 c); weak that traders prefer
it, hence the input.

**Risk.** The headline hit % falls (e.g. 60% → 45%). Default "Balanced" and show ATR delivered next to the hit rate.
With QPOT-01 (drift 0), `reach` inside `legacy` also becomes driftless.

**Effort.** S.

---

### CAL-9 (P2, L) · Second-tier learner: Bayesian online probit lifts with a hand-set prior, measure-first [A's CAL-4, demoted and narrowed by B]

**Why.** This is the learner that learns *pillar weights* with shrinkage to the hand-set prior. On clean data it adds no
forecast skill (−0.15 … −0.79% ungated; gate 0.00 … −0.26%), but it is the best rescuer of a broken base
(+8.8% / +10.5% mixed). Its posterior means and sds are the most informative per-chart pillar readout.
[B] Applying learned lifts to the *score* is not validated by log-loss (selection is a utility decision), so "Apply" acts
on the PoT only.

**Inputs (G_ACC).** `lrMode` = Off (default unless `accView == "Full"`) / Measure / Apply to PoT when proven;
`lrSd` 0.15; `lrOmega` 0.25 (or `1/deff` from `cdClu`).

**Features (F = 11, computed at snapshot by `f_feat(lv, dA)`).**

| j | Feature | Definition | Prior mean μ0 |
|---|---|---|---|
| 0 | bias | 1 | 0 |
| 1 | ext | `grp == 1` | 0 |
| 2 | fvg | `grp == 2` | 0 |
| 3 | obk | `grp == 3` | 0 |
| 4 | eq | `eqCount > 0` | 0 |
| 5 | fresh | `fresh − 0.5` | `κ·wFresh/wSum` |
| 6 | conf | `conf` (after CAL-5) | `κ·wConf/wSum` |
| 7 | dens | `dens − 0.5` | `κ·wDens/wSum` |
| 8 | draw | `draw − 0.5` | `κ·wDraw/wSum` |
| 9 | kz | `f_kzAff(kz, src) > 1` | 0 |
| 10 | dres | `(dA − 2.5)/2.5` | 0 |

κ = 0.3 (a pillar moving 0 → 1 adds ≤ 0.3·w/Σw probit; ≤ 3.6 pp at p ≈ 0.5 for draw). Prior sd `lrSd` for all.

**State.** `var array<float> lrMu`, `lrV` (NF each, initialised on the first bar to μ0 and `lrSd²`),
`lrMix = array.from(0.0, 0.0)` (log-weights [base-or-OPS, model]), `pqSt` (n, LL base, LL model, LL mix).

**Helpers.** `f_npdf`, `f_phinv` (Acklam rational approximation, |rel err| < 1.2e-9; A's sketch and Python test kept in
`calib_ml.md` §4 CAL-4 and `cand_learn.py`), `f_lrPred(off, x) → [m, s]`, `f_lrUpdate(off, x, y)` with the adPredictor
update tempered by ω and a floor `v_j ≥ 0.05·v_j`.

**Flow.**
- At snapshot: `[m, s] = f_lrPred(f_phinv(pRef), x)`, `pM = f_phi(m/s)`, `pG = π·pM + (1−π)·pRef`, with `pRef` = the
  CAL-4 output `pO` (B: mix against the best simple forecaster, not the raw base) and `π = softmax(lrMix)[1]`.
- At resolution (role 0 only): prequential sums, mixture update (η 0.25, fixed share 0.005), then `f_lrUpdate`.
- Apply (PoT only): `activePoT = π·Φ((Φ⁻¹(pCal) + L_act)/s) + (1−π)·pCal` while `pqSt.n ≥ 200` and
  LL model < LL reference.

**UX (Full).** `LEARN ΔLL −0.21% vs CAL · π 0.03 · n 2,140 (dormant)` and
`LIFT EQ +.09±.04 · CONF −.12±.05 · DRAW +.01±.03 · EXT −.08±.05` (largest |μ − μ0| with posterior sd).

**Evidence.** Moderate (A's replica); strong method (Graepel 2010 method; Cesa-Bianchi & Lugosi 2006).

**Risk.** About 120 lines; CPU of 11-feature updates on ≤ 256 probes per bar is small, but must be skipped entirely when
Off. Overlaps CAL-7: ship CAL-7 first, and build CAL-9 only if CAL-7 shows stars on real charts.

**Effort.** L.

---

### CAL-10 (P2, S) · Base-integrity guard: keep roll gaps and bad prints out of the excursion surface [B; coordinate with quant_pot]

**Why.** The only place a learner beat the baseline is a corrupted base (GC 1-hour: CITL −4.25 pp, deff 7.7).
TradingView continuous futures are not back-adjusted by default, so every quarterly or bi-monthly roll injects an
artificial jump into H windows of the surface and into the ATR. Fixing the input is better than learning around it.

**Change.**
- SERIES (near 919): `bool gapBar = math.abs(open - close[1]) > gapK * nz(atr[1], atr)` with
  `gapK = input.float(4.0, "Gap Filter (x ATR)", group = G_POT, display = display.none)`;
  `var int lastGap = -100000`; `if gapBar` then `lastGap := bar_index`.
- Step 0 (1527-1532): skip `f_bump` when `lastGap > bar_index - H` (the window that just completed contains a gap).
- Optional notice row in Terminal: `⚠ ROLL GAPS — enable B-ADJ` when `syminfo.type == "futures"` and a gap was seen in the
  last 2,000 bars.

**Evidence.** Moderate (A's GC 1-hour; TradingView help centre on back-adjustment). The threshold needs a sibling check:
weekend and session gaps on equities and FX are real price behaviour and should not all be removed. That is why the
default is 4 ATR and the input is exposed.

**Risk.** Removes genuine gap windows on gap-prone symbols (fewer surface samples, slightly lower PoT for far targets).

**Effort.** S.

---

### CAL-11 (P3, S) · Gate `f_raceAdj` behind the same prequential test [B]

**Why.** `f_raceAdj` (1367-1371, used at 2130) applies an m = 20 intercept shift unconditionally. Ungated recalibration
of calibrated bases loses log-loss (A, §2.2 a).

**Change.** `raceSt` gains `[ΣLL raw, ΣLL adj]` booked in `f_book` with the raw and adjusted race probability stored at
open (new `Trial.pRaceA`). Apply the shift only while `ΣLL adj < ΣLL raw − 1` and decided races ≥ 100. Coordinate with
quant_pot QPOT-02 (finite-horizon race).

**Evidence.** Moderate (same logic as CAL-4).

**Effort.** S.

---

### Dropped or merged

- A's CAL-6 (selected-target calibration) is merged: its calibration lives in CAL-4 (candidate OPS + gated selected
  intercept) and its scorecard in CAL-6 (with QPOT-04).
- Tracking/binning calibeating (TOPS, HOPS): dropped. Too noisy at ledger sizes (§2.3 B1).
- Venn-Abers / isotonic: dropped (n/a).
- Forgetting (ε dynamics): not proposed; OPS handles drift and the gate handles mismatch.
- Applying learned feature lifts to the *score*: dropped from A's CAL-4 (not validated by a proper score).

### Dependencies and suggested order

1. Independent, S effort: **CAL-1, CAL-2, CAL-5**; then QPOT-01 (drift 0, quant_pot), which makes `pm = pb`.
2. **CAL-3** (the infrastructure), then **CAL-4** and **CAL-6** on top of it.
3. **CAL-7**, then CAL-9 only if CAL-7 shows real stars on users' charts.
4. **CAL-8** any time (needs `Σ y·d0` from CAL-3 for its readout).
5. **CAL-10** with quant_pot; **CAL-11** with QPOT-02.

---

## 5. How this fits the other study reports

| Their proposal | Relationship |
|---|---|
| quant_pot **QPOT-01** (drift 0) | Prerequisite for honest grading. It removes the drift channel of selection bias (3.1). |
| quant_pot **QPOT-04** (grade the displayed PoT, gated recalibration) | Scorecard reused in CAL-6. Its intercept calibrator is superseded by CAL-4 (candidate OPS + gated selected intercept). B-fix to its §1.15: Platt on logit p contains the identity. |
| quant_pot **QPOT-08 / QPOT-10** (stacked / mixture PoT models) | Same family as CAL-4/CAL-9. Include the baseline (or CAL-4) as an expert so the mixture can fall back. |
| quant_pot **QPOT-09** (display-only cap) | CAL-3/4/6 grade the uncapped value. |
| skeptic **SKEP-2** (mirror-controlled EDGE) | Mirror implemented as CAL-3 role 5; verdict uses the CAL-2 boundary. |
| ict_liq **ICT-1** (candidate ledger + feature lifts) | Infrastructure = CAL-3. Its naive-Bayes lifts are replaced by CAL-7 readouts and the CAL-9 probit. |
| ict_pd `f_ctxMult` | Same naive-Bayes issue; use CAL-1-style gated EB per context. |
| smc_impl **SMC-1** (ledger-calibrated PoT) | Merged into CAL-4. |
| bias_dol **BIAS-1/2** (side learner with geometry prior, prequential skill) | Same philosophy; reuse `f_phinv`, `f_csBound` and the gate. |
| ict_struct (D has no skill) | Consistent with the draw coefficient (≤ 0, not significant) and with CAL-8's "selection is utility". |

---

## 6. Sources

Verified by B in this pass (paper text or abstract read through the research index, code read directly, or vendor
documentation via search):
- Howard, Ramdas, McAuliffe, Sekhon (2021). Time-uniform, nonparametric, nonasymptotic confidence sequences. Annals of
  Statistics. https://arxiv.org/abs/1810.08240 (eq. 14; Props 3, 5, 7, 11)
- Johari, Pekelis, Walsh (2015/2022). Always Valid Inference: Bringing Sequential Analysis to A/B Testing.
  https://arxiv.org/abs/1512.04922
- Waudby-Smith, Arbour, Sinha, Kennedy, Ramdas (2021). Time-uniform central limit theory and asymptotic confidence
  sequences. https://arxiv.org/abs/2103.06476
- Maharaj et al. (2023). Anytime-Valid Confidence Sequences in an Enterprise A/B Testing Platform.
  https://arxiv.org/abs/2302.10108
- Ge, Liu (2026). Time-Uniform Dependent Central Limit Theory. https://arxiv.org/abs/2610.29288
- Gupta, Ramdas (2023). Online Platt Scaling with Calibeating. ICML, PMLR 202:12182-12204.
  https://proceedings.mlr.press/v202/gupta23c.html ; https://arxiv.org/abs/2305.00070
- Foster, Hart (2023). "Calibeating": Beating Forecasters at Their Own Game. Theoretical Economics.
  https://arxiv.org/abs/2209.04892 ; https://math.huji.ac.il/~hart/abs/calib-beat.html
- Van Calster et al. (2016). A calibration hierarchy for risk models was defined: from utopia to empirical data. J Clin
  Epidemiol 74:167-176. https://lirias.kuleuven.be/retrieve/577522 ; summary
  https://simonsteiger.github.io/kepipedia/content/articles/vancalster2016/index.html
- Collins, Ogundimu, Altman (2016). Sample size considerations for the external validation of a multivariable prognostic
  model: a resampling study. Stat Med 35(2):214-226. https://pmc.ncbi.nlm.nih.gov/articles/PMC4738418 ;
  https://dro.dur.ac.uk/34196
- Spiegelhalter (1986). Probabilistic prediction in patient management and clinical trials. Stat Med 5. Formula as
  tabulated in https://pmc.ncbi.nlm.nih.gov/articles/PMC8299436/table/T1
- Kumar, Liang, Ma (2019). Verified Uncertainty Calibration. https://arxiv.org/abs/1909.10155
- Roelofs, Cain, Shlens, Mozer (2020/2022). Mitigating Bias in Calibration Error Estimation.
  https://arxiv.org/abs/2012.08668
- Efron (2011). Tweedie's Formula and Selection Bias. JASA 106(496):1602-1614. doi:10.1198/jasa.2011.tm11181
- TradingView help centre: "How can I enable backadjustment for continuous futures?"
  https://www.tradingview.com/support/solutions/43000685266 (read through a search summary; tradingview.com itself is
  blocked here)
- Public Pine v2 port of "Machine Learning: Lorentzian Classification" (MPL-2.0), file
  `ports/pinescript/lorentzian-classification-v2.pine`, lines 335, 339-344, 394-413:
  https://github.com/artificial-intelligence-edge/lorentzian-classification (concepts only; nothing reused)
- capissimo, Pinescript-Laboratory, `scripts/114-ML-Logistic-Regression-(v4).pine`, lines 89-97, 115-121:
  https://github.com/capissimo/Pinescript-Laboratory (concepts only)
- Pine v6 reference mirror (`docsrc/jabez4jc_pinescriptv6`): `reference/bar_variables.md` (last_bar_index remarks),
  `writing_scripts/limitations.md` (500 ms loops, 100,000-element collections), `reference/matrix.md`,
  `language/type_system.md`.

From A, cited at the method level (B could not re-open the PDFs; figures marked "not re-verified" in §2.1):
- Graepel, Quiñonero Candela, Borchert, Herbrich (2010). Web-Scale Bayesian Click-Through Rate Prediction for Sponsored
  Search Advertising in Microsoft's Bing Search Engine. ICML.
  https://www.microsoft.com/en-us/research/wp-content/uploads/2010/06/AdPredictor-ICML-2010-final.pdf
- Niculescu-Mizil, Caruana (2005). Predicting Good Probabilities With Supervised Learning. ICML.
  https://www.cs.cornell.edu/~alexn/papers/calibration.icml05.crc.rev3.pdf ; scikit-learn calibration guide
  https://scikit-learn.org/0.22/modules/calibration.html
- Efron, Morris (1975). Data Analysis Using Stein's Estimator and its Generalizations. JASA 70(350):311-319.
- Platt (1999); Ng & Jordan (2002, NIPS); Smith & Winkler (2006, Management Science 52(3)); Gneiting & Raftery (2007,
  JASA 102); Murphy (1973); Bröcker & Smith (2007); Kull, Silva Filho, Flach (2017, AISTATS); Guo et al. (2017, ICML);
  Duchi, Hazan, Singer (2011); McMahan et al. (2013); Hazan (2016, Introduction to Online Convex Optimization, Alg. 12);
  Dawid (1984); López de Prado (2018, chs. 4, 7); Sullivan, Timmermann, White (1999, JF 54(5)); White (2000,
  Econometrica 68); Li, Chu, Langford, Wang (2011, WSDM); Domingos & Pazzani (1997); Chapelle & Li (2011, NIPS);
  Vovk & Petej (2014, UAI; https://arxiv.org/abs/1211.0025); Király & Qian (2017, https://arxiv.org/abs/1701.08055);
  Cao et al. (2007, ICML); Burges et al. (2005, ICML); Cesa-Bianchi & Lugosi (2006); Herbster & Warmuth (1998);
  Chung & Bellotti (2021, https://arxiv.org/abs/2101.07410).
- Practitioner summary of peeking (Optimizely figure): https://atticusli.com/replication-crisis/ab-testing-peeking-problem/

Standard references used from knowledge (not fetched): Cameron, Gelbach, Miller (2008), Bootstrap-based improvements for
inference with clustered errors, REStat 90(3):414-427; Hansen, Hodrick (1980), JPE 88(5); Hersbach (2000), Weather and
Forecasting 15; Epstein (1969), J. Applied Meteorology 8; Robbins (1956); Cox (1958), Biometrika 45.

Project-internal: `quant_pot.final.md` (§1.15, §2.2, QPOT-01/04/08/09/10), `skeptic.md` (SKEP-2), `ict_liq.final.md`
(ICT-1), `ict_pd.final.md`, `smc_impl.final.md`, `bias_dol.final.md`, `ict_struct.final.md`; A's report `calib_ml.md`
(kept unchanged as the A record, including the full `f_phinv` and adPredictor Pine sketches); study code in
`calib_ml_tools/` (A) and `calib_ml_b_tools/` (B).
