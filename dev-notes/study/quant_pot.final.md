# Quant Probability of Touch (PoT) · combined final study (researcher A + researcher B)

Domain: first-passage (touch) probability, two-barrier races (finite and infinite horizon), discrete-monitoring
correction, fat tails and jumps, OHLC volatility estimators, intraday seasonality and volatility time, volatility
clustering, empirical excursion surfaces, Bayesian blending and partial pooling, and calibration of touch probabilities.

Engine audited: `brief/baseline_v2.pine` (identical to `/home/user/m/indicators/dol_engine.pine`). Every line
reference below was re-checked by B against that file.

Provenance tags used throughout:
- **[A]** researcher A's original finding, kept as written.
- **[A✓]** A's finding that B re-checked (source re-opened, number re-computed, or bootstrap CI added).
- **[B]** new material from researcher B.
- **[B-fix]** A's statement that B corrected, downgraded or re-scoped (the old text is quoted where it matters).

Reproducible code:
- A: `study/quant_pot_tools/` (`potlib.py`, `pot_eval.py`, `pot_stack.py`, `pot_vs2.py`, `eta_race.py`,
  `verify_formulas.py`, `sim_drift.py`, `seas_profile.py`, `vif.py`; outputs `out_*.txt`; walk-forward rows `rows_*.pkl`).
- B: `study/quant_pot_b_tools/`:
  - `b_boot.py` / `b_boot_day.py`: day-block bootstrap of A's key log-loss comparisons (`out_boot.txt`, `out_boot_day.txt`);
  - `b_race_h.py` + `b_race_boot.py` / `b_race_boot_day.py`: calibration of the engine's finite-horizon race "WIN≤H" (`out_race_h.txt`, `out_race_boot*.txt`);
  - `b_ratio.py`: the reflection identity on real bars and a Monte Carlo check of the BGK shift (`out_ratio.txt`).

Data (both researchers): CME ES, NQ, CL, GC, RTY, YM from `study/amt_data/cme/` (timestamps are UTC; B checked the
daily 22:00/23:00 UTC maintenance gap). 5-min bars 2026-01-20 → 2026-04-15 (≈16.8k bars per symbol, ≈54 evaluated
trading days after warm-up), 1-hour bars 2025-03 → 2026-04, 1-min ES/NQ/CL. GC 1-hour contains contract-roll gaps.

Sibling studies cross-referenced (they overlap this lens and were reconciled, not duplicated):
`ict_time.final.md` (TIME-2/3/4/6: time-of-day surface, robust volatility clock, PoT scorecard, session-end PoT),
`calib_ml.md` (calibration, gated learners, shadow ledger), `bias_dol.final.md` (REG-1: the HTF-regime key has no side
skill), `quant_regime.md` (key the surface on volatility), `skeptic.md` (ledger leak-freeness, regime split absorbs trend beta).

---

## 0. Key findings (read this first)

1. **The closed-form maths in the engine is correct; its inputs are the problem.** [A✓] `f_pot` (434-444), `f_race`
   (447-462) and `f_raceH` (466-482) match Monte Carlo within the expected discretisation bias. B re-derived the
   `f_raceH` flux series (absorbed BM with drift, flux through +a integrated from h to ∞) and confirmed it term by term.
2. **The 50-bar drift is the single largest error, in PoT *and* in the race.** [A✓, B extended]
   - PoT: removing `potMu` improves log-loss by **+3.66%** (95% CI **+2.99 … +4.32%**, day-block bootstrap over 326
     symbol-days; +2.32 … +4.82% when clustering by calendar day across symbols, the conservative version), on
     **all 6 symbols** (+3.1 … +4.1%) and on 77% of symbol-days (5-min, H = 30). Every interval quoted below has
     a calendar-day version in 2.2-2.3; all of them still exclude zero except the Yang–Zhang one.
   - Race (new, B): the displayed **WIN≤H is badly over-confident**: calibration slope **0.69** with the engine's drift.
     Dropping the drift gives **+3.58%** log-loss (CI +2.74 … +4.41%), positive on all 6 symbols (+3.4 … +3.9%).
3. **The finite-horizon race needs the horizon, and the martingale value b/(a+b) is only right for close barriers.** [B]
   On 479k decided races (5-min, H = 30, 14 barrier pairs), conditioning on "decided within H" moves P(target first)
   by up to 9 pp from b/(a+b) (e.g. target 2 ATR / invalidation 6 ATR: observed 0.813, b/(a+b) 0.750). The engine's
   driftless `f_raceH` gets the direction right but is too extreme with the 50-bar σ (slope 0.89); feeding it the
   forward volatility-time σ_eff = √(V_H/H) gives slope **1.00** and the best log-loss (+0.74% over constant σ, CI
   +0.38 … +1.04%; total +4.29% over the current engine).
4. **The reflection identity holds on real bars: P(touch within H) = 2.00 × P(finish beyond at H).** [B] On 5-min
   (H = 30) and 1-hour (H = 12) CME bars the ratio is 1.99-2.02 at every distance from 0.5 to 4 ATR (2.05-2.20 only at
   4-6 ATR on 1-hour, where counts are small). Consequences: bar highs/lows really do capture the continuous path
   maximum (so touches need no BGK shift), and fat tails act through the terminal distribution: PoT(d) = 2·P(X_H > d)
   for whatever distribution X_H has.
5. **The default Empirical surface is calibrated but blind to *when* and *in what volatility state*.** [A✓] Splitting
   it by a volatility state with partial pooling improves log-loss by **+1.79%** (CI +1.45 … +2.13%) on all 6 symbols;
   the sibling time-of-day version (TIME-2, 8 blocks keyed to the session time zone) improved Brier in all 24
   symbol × setting tests. The same change should also shrink the HTF-regime rows toward the pooled row (that key has
   no side skill: bias_dol REG-1).
6. **Volatility time is real but must be gated as a stand-alone PoT.** [B-fix] A's calibrated vol-time analytic beats
   the engine surface on average (+1.46% LL, CI +0.85 … +2.11%) but **loses on CL (−1.8%) and GC (−1.2%)**; the sibling
   robust clock fails on GC 1-hour (−9.8% Brier). So the forward-variance engine is P1 as an *input* (race σ_eff, ETA,
   close-beyond, vol state), and only scorecard-gated (TIME-4) as the displayed PoT. It must be keyed to the session
   time zone (`tz`, line 219), not UTC as A's spec had it, and must use the real future-bar calendar.
7. **Range-based σ alone buys almost nothing.** [B-fix] Yang–Zhang instead of close-to-close σ: +0.28% LL, CI
   −0.10 … +0.66% (−0.39 … +0.99% by calendar day; not significant; better on 4 of 6 symbols). Published empirical efficiencies on real data are
   1.2-5× close-to-close, far below the 5-14× of theory. The gain in A's results comes from seasonality and clustering,
   not from the estimator.
8. **Close-based events need the BGK shift (or, better, their own empirical surface).** [A✓] Continuous formula 0.583
   vs realised close-beyond 0.453; BGK shift (barrier + 0.5826·σ_bar) cuts log-loss **6.28%** (CI +5.88 … +6.67%).
   B confirmed the constant (= −ζ(½)/√(2π), also the expected overshoot of a driftless Gaussian random walk) and the
   sign by Monte Carlo (z = 1: walk 0.272, BGK 0.269, continuous 0.317).
9. **The headline PoT is never graded, and recalibrating it must be gated.** [A✓ + calib_ml] `Trial` (375-395) has no
   PoT field, so there is no Brier score or reliability check of the number the user sees. Sibling calib_ml found that
   learners trained on *selected* targets do not beat the distance-matched baseline on clean data (−0.2 … −1.8% LL), so
   any recalibration must pass a prequential gate.
10. **The 95% cap, live remaining-time and beyond-grid issues are real but tiny.** [B-fix] A listed them as leaks into
    scoring and the EDGE baseline; B quantified them as ≤ 0.4 pp after warm-up (cap), < 1 pp (remaining time) and
    rare (beyond-grid only when d > 15 × ATR14). Keep them as a P3 hygiene item.

### 0.1 What B changed relative to A
| # | A's statement | B's verdict |
|---|---|---|
| 1 | Drift removal: "LL 0.6115 → 0.5891" | **Confirmed** with a day-block CI (+2.99 … +4.32%), all 6 symbols; **extended** to the race (+3.58%). |
| 2 | f_invalidation: "partial (maths correct; drift should be zero)" | **Upgraded to wrong**: measured slope 0.69, LL penalty 4.3% vs the best driftless race. |
| 3 | "Races match b/(a+b) within 1.2 pp" | **True only for close barriers.** For wider/asymmetric barriers the horizon-conditioned value differs by up to 9 pp; `f_raceH` with vol-time σ_eff is calibrated (slope 1.00). |
| 4 | QPOT-02 vol-time model as a P1 PoT replacement; "+1.5% BSS" | **Re-scoped**: average gain real but loses on CL/GC; use as an input everywhere, as the displayed PoT only behind the TIME-4 scorecard. |
| 5 | QPOT-02 buckets "hour(time, 'UTC')" | **Wrong key**: use `tz` (exchange/NY time). A's own sample straddles the 8 Mar 2026 US DST change; TIME-3's NY-keyed clock beat the UTC one (+3.9% vs +3.5% Brier). |
| 6 | QPOT-02 clock walk "time + j·chartS·1000, skip unseen buckets" | **Would count weekends and the daily halt as trading bars** (time-of-day buckets are always "seen"). A's backtest used the real future bars. Use `time(timeframe.period, "", bars_back = -j)` (docs: expected future bar time, −1 … −500) or TIME-3's open-cell walk. |
| 7 | QPOT-02 multiplicative EWMA, no floors | TIME-3 showed this form zeroes buckets and gains only +0.8-1.0%; adopt the additive, floored, cumulative-mean-warm-start form. |
| 8 | Range estimators "efficiency 5.2-14" as a reason to switch | **Theory only.** Our data: YZ +0.28% (n.s.). Empirical efficiency on index data 1.2-5× (Vințe et al. 2022). |
| 9 | 95% cap "leaks into scoring and the baseline (biased low for near targets)" | **Magnitude negligible**: ≤ 0.4 pp in `f_potBase` once the surface is warm (it learns on all loaded bars, long before the ledger starts); ≤ 5% relative in the reach term. |
| 10 | Live bar should use H − 1 + remaining fraction | **Negligible** (< 1 pp at H = 30); dropped from proposals. |
| 11 | Beyond-grid Gaussian fallback under-states far touches | **Rare**: the grid reaches 15 ATR14 and levels are ejected at 15 × atrE (≥ ATR14); it only bites in quiet sessions on far HTF levels. Kept as a note. |
| 12 | ETA "conditional median" | Kept; B adds conditional and unconditional quantile formulas and **corrects sibling TIME-6**, whose "ETA80 = (d/1.2816)²" is the 20% quantile (the 80% quantile uses 0.2533). |
| 13 | Crypto peak "16-17 UTC, trough ≈05 UTC" (Quantpedia summary) | **Confirmed by the primary source** (Hansen, Kim & Kimbrough, J. Fin. Econometrics 2024): high around 16 UTC, bottom near 5 UTC, spikes at the 00/08/16 UTC funding times; upgraded to strong. |
| 14 | Efron–Morris "17.56 → 5.01" | Consistent: the raw-scale figures are 0.077 → 0.022 (ratio ≈ 3.5). |
| 15 | Andersen–Bollerslev "0.095% → 0.055% → 0.105%" | Not re-verifiable here (full text hosts blocked). The U-shape itself is confirmed by many sources; Hansen et al. (2012, quoted in the 2024 paper): ≈ 75% of daily S&P 500 variance falls in the 6.5 cash hours. |
| 16 | QPOT-08 stacked logistic as a P3 model | Folded into the gated mixture/scorecard (calib_ml, TIME-4); unregularised online logistic lost 3.6-5.5% LL in calib_ml. |

---

## 1. Concepts (definitions and parameters)

### 1.1 One-barrier first passage (touch) for Brownian motion with drift [A✓]
Process X_t = μt + σW_t, start 0, barrier d > 0 (distance to the level's near edge), horizon h bars:

  P(max_{s≤h} X_s ≥ d) = Φ((μh − d)/(σ√h)) + exp(2μd/σ²) · Φ((−μh − d)/(σ√h))

- Driftless: P = 2Φ(−d/(σ√h)) = erfc(d/(σ√(2h))), the reflection principle: **touch = 2 × finish-beyond**.
- **Real-bar check [B]:** on CME 5-min bars (H = 30) the ratio P(touch)/P(close at H beyond) is 2.00, 2.00, 2.02,
  2.01, 2.01, 1.99 at 0.5, 1, 2, 3, 4, 6 ATR; on 1-hour bars (H = 12) 2.00, 2.00, 2.01, 2.00, 2.05, 2.20. The reflection
  identity needs only path continuity and symmetry of increments after the hitting time, not Gaussian tails, so it
  survives fat tails and volatility clustering. Practitioner studies of option "probability of touch" (tastylive, SPY
  strangles over ≈20 years) report the same ≈2× ratio, with implied-vol-based PoT too high because IV exceeds
  realised vol (weak evidence; promotional studies).
- Volatility time: for a deterministic time-varying variance, replace σ²h by the integrated variance V over the next h
  bars: P = 2Φ(−d/√V) (exact time change).
- Edge cases: d ≤ 0 → 1; σ = 0 → 0; compute exp(2μd/σ²)·Φ(·) in log space (`f_expPhi`, 421-429).

### 1.2 Two-barrier race, infinite horizon (martingale race) [A✓]
Upper barrier +a (target), lower −b (invalidation), k = 2μ/σ²:

  P(+a before −b) = (1 − e^{kb}) / (e^{−ka} − e^{kb});  driftless limit b/(a+b).

For any continuous martingale (stochastic and seasonal volatility included) optional stopping gives b/(a+b) exactly,
provided the race is eventually decided. A's data: within 0.4-1.2 pp for barrier pairs up to 3 ATR; B reproduced it
(1/1: 0.495, 1/2: 0.662, 2/1: 0.321, 1/3: 0.755, 3/1: 0.225).

### 1.3 Two-barrier race, finite horizon, conditioned on "decided within H" [B]
What the engine displays as WIN≤H (`f_invalidation`, 1343-1364; ledger `raceSt`, 1487-1492) is
P(target first | one of the two is hit within H) = P_W(h)/(P_W(h) + P_L(h)), with
P_W(h) = P(+a first and before h) = P_∞ − tail(h), and (shifting y = x + b on (0, L), L = a + b)

  tail(h) = e^{μa/σ²} Σ_n (σ²nπ/L²)(−1)^{n+1} sin(nπb/L) e^{−(λ_n+ν)h}/(λ_n+ν),  λ_n = σ²n²π²/(2L²), ν = μ²/(2σ²).

- B re-derived it: the absorbed density is e^{μ(y−y₀)/σ² − νt}·(2/L)Σ sin(nπy₀/L) sin(nπy/L) e^{−λ_n t}; the flux at L is
  −(σ²/2)∂p/∂y; integrating from h to ∞ gives the expression above, which is exactly the engine's loop
  (`c·λ/(λ+ν)·exp(μa/σ² − (λ+ν)h)`, with c = 2/(nπ)(−1)^{n+1} sin(nπb/L)).
- **This is not invariant to volatility.** Conditioning on "decided within H" favours the nearer barrier, because it
  is decided earlier. The size of the effect depends on the horizon variance, so the race needs the *forward*
  variance over H, not the trailing 50-bar σ.
- Measured (5-min, H = 30, B): observed P(target first | decided) vs model, for target a / invalidation b in ATR:

  | a / b | observed | b/(a+b) | f_raceH σ₅₀, μ = 0 | f_raceH σ₅₀, engine drift | f_raceH vol-time σ_eff |
  |---|---|---|---|---|---|
  | 2 / 4 | 0.692 | 0.667 | 0.712 | 0.701 | 0.697 |
  | 2 / 6 | 0.813 | 0.750 | 0.865 | 0.846 | 0.822 |
  | 4 / 2 | 0.281 | 0.333 | 0.288 | 0.310 | 0.303 |
  | 6 / 2 | 0.160 | 0.250 | 0.136 | 0.167 | 0.177 |
  | 6 / 3 | 0.231 | 0.333 | 0.189 | 0.235 | 0.247 |

  Overall (479,485 decided races): slope 1.20 (b/(a+b), too timid), 0.89 (σ₅₀), **0.69 (engine)**, **1.00 (vol-time)**.
- P(decided within H) itself is over-predicted by Brownian motion (mean 0.84-0.87 vs 0.80 observed; e.g. 4/4 ATR:
  0.529 observed vs 0.548-0.658), so do not display the unconditional finite-horizon win probability without
  empirical calibration.

### 1.4 Discrete monitoring: Broadie–Glasserman–Kou correction and expected overshoot [A✓, B added the link]
If a barrier is only checked at bar closes (spacing Δt = 1 bar), price the event with the continuous formula after
shifting the barrier away from the start by β·σ_bar, **β = −ζ(½)/√(2π) ≈ 0.5826** (ζ = Riemann zeta). Error falls from
O(1/√m) to o(1/√m) (BGK 1997).
- Why this constant [B]: it is the limiting expected **overshoot** of a driftless Gaussian random walk over a far barrier
  (Chang & Peres 1997; Janssen & van Leeuwaarden: E[max] of the zero-drift Gaussian walk carries the term
  ζ(½)/√(2π)·σ). A close-checked barrier is crossed on average 0.5826σ "late".
- Applies to: body-close breaks, BOS by close, iFVG inversion by close. Does **not** apply to touches judged with highs and
  lows (B's reflection check, 1.1, shows bar extremes behave like the continuous maximum).
- MC check [B] (Gaussian walk, 30 steps, 200k paths), P(any close ≥ z·√30): z = 0.5: 0.547 vs BGK 0.544 vs continuous
  0.617; z = 1: 0.272 / 0.269 / 0.317; z = 2: 0.036 / 0.035 / 0.046.

### 1.5 Time to touch (ETA) and its quantiles [A, B added quantiles and a sibling correction]
- Driftless first-passage time T to distance d in volatility time: F(τ) = P(T ≤ τ) = 2Φ(−d/√V(τ)), V(τ) = cumulative
  forecast variance (σ²τ for constant σ: the Lévy distribution; infinite mean; mode d²/(3σ²)).
- **Unconditional q-quantile:** first τ with √V(τ) ≥ d / Φ⁻¹(1 − q/2). Median: Φ⁻¹(0.75) = 0.6745. 80%: Φ⁻¹(0.60) =
  **0.2533**, so the unconditional 80% time is (0.6745/0.2533)² ≈ 7.1 × the median in variance units: heavy-tailed and
  rarely useful on a HUD. **[B-fix, sibling]** TIME-6's "ETA80: (d/1.2816)²" is the **20%** quantile.
- **Conditional on a touch within H** (the useful readout next to PoT): q-quantile = first τ with F(τ) ≥ q·F(H), i.e.
  √V(τ) ≥ d / Φ⁻¹(1 − q·F(H)/2). A tested the conditional median.
- With drift: inverse Gaussian density f(t) = d/(σ√(2πt³))·exp(−(d − μt)²/(2σ²t)) (not needed once μ = 0).
- Arcsine law (sibling ict_time 1.15): the time of the maximum on [0, T] has density 1/(π√(t(T − t))); in variance time
  the high-variance edges carry more mass.

### 1.6 Fat tails, stochastic-volatility mixture and jumps [A✓]
- Mixture: PoT(d) = E_σ[2Φ(−d/(σ√h))]. Relative to a Gaussian with the same mean variance, near levels become less
  likely and far levels more likely.
- Perelló, Gutiérrez-Roig & Masoliver (2011; transaction data on six futures: EURUSD, USDM, S&P 500, DJI, IBEX, DAX):
  the Wiener model **under-estimates** first-passage probability for x ≳ v_t and **over-estimates** it for x ≲ 0.1·v_t
  (v_t = empirical sd at horizon t); scaling x by v_t collapses all markets and horizons (1-120 min) up to x ≈ 10·v_t;
  Weibull fits small targets, Student-t the tail, crossover near 5·v_t; survival decays as t^(−1/2) (Sparre-Andersen).
- Reconciliation with 1.1 [B]: the reflection identity holds, so fat tails enter only through the H-bar terminal
  distribution: PoT(d) = 2·P(X_H > d). An empirical surface (or a Student-t terminal law scaled to √V_H) captures both.
- Jumps: overshoot at the barrier; Kou & Wang (2003) give exact first passage for double-exponential jumps. Osler (2005):
  stop-loss cascades once a level is crossed (positive feedback right at liquidity).
- Our data [A]: analytic σ₅₀ at 6 ATR 0.118 vs realised 0.150 (5-min, H = 30); at H = 12 0.024 vs 0.041, while it
  over-predicts at 1-2 ATR by 3-4 pp.

### 1.7 OHLC volatility estimators [A, B-fix on practical value]
| Estimator | Per-bar variance proxy | Theoretical efficiency vs close-to-close | Assumptions |
|---|---|---|---|
| Close-to-close | (C − C₋₁)² | 1 | none |
| Parkinson (1980) | (H − L)²/(4 ln 2) | ≈5.2 | zero drift, no gaps, continuous trading |
| Garman–Klass (1980) | ½(H − L)² − (2 ln 2 − 1)(C − O)² | ≈7.4 | zero drift, no gaps |
| Rogers–Satchell (1991) | (H − C)(H − O) + (L − C)(L − O) | ≈6 | drift-independent, no gaps |
| Yang–Zhang (2000) | σ_o² + kσ_c² + (1 − k)σ_RS², k = 0.34/(1.34 + (n+1)/(n−1)) (≈0.13-0.14 for usual n) | highest among drift- and gap-robust estimators | drift-independent, handles opening jumps |

- **Practical efficiency is much lower [B].** Vințe et al. (2022, daily index data) measured efficiencies of 1.2-5× for
  all four estimators over most windows, with no estimator consistently best; Shu & Zhang (2006, J. Futures Markets):
  range estimators are close to integrated variance on S&P 500 data, but differ when there are opening jumps or large
  drift; Alizadeh–Brandt–Diebold (2002): range estimators are robust to microstructure noise. Square roots of unbiased
  variance estimators are biased low for σ (Jensen; Molnár). On our 5-min data YZ vs close-to-close: +0.28% LL, CI
  −0.10 … +0.66% (not significant).
- Biases: tick discreteness biases the range down, bid-ask bounce up; drift biases Parkinson/GK up; session gaps and
  contract rolls must be added back (gap² term) and winsorised. Mean bar range / σ_cc on our data 1.39-1.48 (BM: 1.596),
  mainly a Jensen effect of varying σ.
- Use: range proxies matter as the input of a **seasonal and clustered** forecast (1.8, 1.9), not as a drop-in σ.

### 1.8 Intraday seasonality and volatility (business) time [A✓, B-fix on keying]
- Multiplicative component model: r_{t,n} = σ_day · s(τ_n) · q_{t,n} · z (Andersen–Bollerslev 1997/1998; Engle & Sokalska
  2012: daily × diurnal × stochastic intraday, applied to 10-minute returns of 2,500 US stocks, two-stage estimation,
  intraday residual as unit GARCH(1,1)). Dacorogna et al. (1993): integrating the seasonal activity gives a business
  time ("ϑ-time") free of daily/weekly seasonality.
- Size: ES 5-min variance at 09:30 ET = 4.67× the day mean, 23:30 ET = 0.20× (24× range; NQ 09:30 = 6.17×) [A]; ≈75%
  of daily S&P 500 variance falls in the 6.5 cash hours (Hansen et al. 2012, quoted by Hansen–Kim–Kimbrough) [B];
  crypto: high around 16 UTC, bottom near 5 UTC, spikes at 00/08/16 UTC funding times, first minute of each hour most
  volatile (Hansen, Kim & Kimbrough 2024) [B].
- **Key to exchange/session time, not UTC** [B-fix]: the US cash open sits at a fixed NY time across DST. A's sample
  straddles the 8 Mar 2026 DST change; TIME-3 measured +3.9% (NY-keyed) vs +3.5% (UTC-keyed) Brier.
- **Forward variance:** V(j) = Σ_{i=1..j} s²(τ_{t+i})·[L_s + φ^i(L_f − L_s)], L_f/L_s fast/slow deseasonalised levels,
  φ = 0.5^(1/30). τ_{t+i} must be the time of the i-th *future bar* (weekends, the daily halt and the session schedule
  matter). Pine v6: `time(timeframe.period, "", bars_back = -i)` returns "the expected timestamp of the bar N bars after
  the current bar" for −1 … −500 (local docs, reference/time.md); holidays are not known.
- Horizon gate (A + ict_time): gains appear when H × timeframe spans a material part of the daily cycle (≥ 1-2 h) and
  is shorter than about a day (1-hour H = 30 averages out).

### 1.9 Volatility clustering forecast [A, B added CARR]
- EWMA σ²_t = λσ²_{t−1} + (1 − λ)r²_t (RiskMetrics λ = 0.94 daily); GARCH term structure E[σ²_{t+j}] = L̄ + φ^j(σ²_t − L̄);
  HAR-RV (Corsi 2009); CARR (Chou 2005): a GARCH-type recursion on the range, λ_t = ω + αR_{t−1} + βλ_{t−1}, with sharper
  out-of-sample forecasts than GARCH on S&P 500 data. The fast/slow EWMA pair above is a CARR/GARCH-lite in Pine.
- Our data [A]: deseasonalised log-range ACF on ES 5-min 0.63 (lag 1), 0.49 (1 h), 0.34 (6.5 h), 0.27 (1 day).
  Ablation: seasonality with a flat level LL 0.6003 vs seasonality × clustering 0.5659 (H = 30).

### 1.10 Drift estimation and short-horizon predictability [A✓]
μ̂ from n = 50 bars has SE σ/√50; with weight w in an H-bar first-passage formula the standardised barrier moves by
w·√(H/n)·Z: 0.39·Z at H = 30, w = 0.5 (0.55·Z at H = 60). Intraday predictability is small (Gao, Han, Li & Zhou 2018:
R² 1.6% in sample, 1.2% out of sample, verified by ict_time B2). If any drift is kept, shrink it (positive-part
James–Stein: μ_eff = μ̂·max(0, 1 − (σ²/n)/μ̂²), i.e. zero unless |t| > 1).

### 1.11 Variance ratio [A]
VR(q) = Var(q-bar return)/(q·Var(1-bar)) ≈ 1 + 2Σ(1 − j/q)ρ_j (Lo–MacKinlay 1988). Our data at q = 30-60: ES 0.96,
NQ 1.02-1.05, CL 1.00-1.03, GC 0.84-0.87, YM 0.91-0.94: √H scaling is acceptable; residual deviations are absorbed by
the empirical surface. No engine change.

### 1.12 Empirical excursion surface with overlap-aware sample size [A✓]
For each completed H-bar window, up and down maximum excursion from the start close in ATR (at the window start),
counted on a 0.25-ATR grid to 15 ATR (`bStep` = max(maxATR·ejectMult, 10)/60 = 0.25 at defaults, line 307). The survival
count S(u) gives the empirical PoT. Overlapping windows: touch-indicator VIF/H measured 0.21-0.83 (A), so the engine's
nEff = n/(0.6H) is a reasonable conservative constant. The surface learns on **all** loaded confirmed bars (step 0 is
outside the `inCalc` gate), so it is warm long before the ledger starts.

### 1.13 State conditioning with partial pooling [A✓, B merged siblings]
- Cell estimate shrunk to its parent: p_cell = (nE_c·p̂_c + m·p_parent)/(nE_c + m), nE = n/(0.6H), m = 30 (Efron–Morris
  1975: James–Stein beat the raw averages by a factor ≈ 3.5 in total squared error, 0.077 vs 0.022).
- Useful states: (a) volatility state = tercile of q = √V_H/(ATR·√H) (A: +1.79% LL, all 6 symbols); (b) time-of-day block
  in `tz` (TIME-2: 8 × 3-hour blocks, +0.1 … +5.9% Brier in 24/24 tests); (c) ATR14/ATR200 alone: almost nothing
  (A: 0.5636 → 0.5622).
- The existing HTF-regime key has no side skill (bias_dol) but absorbs trend beta in the EDGE baseline (skeptic). Partial
  pooling keeps both properties: a regime row only departs from the pooled row as far as its own data justify.

### 1.14 Bayesian blending of model and empirical rates [A✓]
Beta-binomial posterior mean (k + m·p₀)/(n + m) with the analytic model as a prior worth m = `priorM` = 30 effective
windows (`f_potModel` 1303-1311). Correct form. At typical history (n ≈ 5-20k windows, nEff ≈ 300-1,100 at H = 30) the
prior keeps 3-10% weight, so its drift noise and 95% cap leak in only slightly; at the gate (n = nMin = 600) it has ≈ 48%.

### 1.15 Calibration and proper scoring [A✓, B added gating and beta calibration]
- Brier, log-loss, Murphy decomposition B = REL − RES + UNC, 10-bin reliability and ECE, calibration slope (logistic
  regression of y on logit p; slope < 1 = over-confident). BSS = 1 − B/B_ref with the distance-matched base rate as
  the reference.
- Recalibration maps: Platt σ(a + b·logit p); isotonic above ≈1,000 points (Niculescu-Mizil & Caruana 2005); beta
  calibration (Kull, Silva Filho & Flach 2017) contains the identity map, so it cannot "un-calibrate" an already
  calibrated model and is preferred on small sets, unlike Platt whose logistic family excludes the identity.
- **Gate it [calib_ml]:** on 13 clean datasets no learner trained on selected targets beat the distance-matched
  baseline (−0.15 … −5.5% LL); a prequential gate or a two-expert exponential-weights mixture (η = 0.25, fixed share
  0.005) costs ≤ 0.3% where the base is good and recovers +8.8 … +10.5% where it is broken (GC 1-hour).

### 1.16 Liquidity levels versus random levels [A✓]
Osler (2003, 2005): stop-loss and take-profit orders cluster at salient levels; take-profits reverse trends, stops
accelerate them once crossed. Chung & Bellotti (2021; EURUSD, LLOY, BRENT 1-minute data, 2018): bounce probability
rises with the number of prior bounces; with 1 prior bounce it decays to 0.5 at ≈350-minute lag windows, with 4 at
≈900 minutes (verified in the paper). Garzarelli et al. (2014): bounce probability above shuffled-return controls.
Sibling calib_ml: on engine-like pools the realised hit rate equals the distance-matched random-level baseline within
±2 pp. So the engine's PoT can be a random-level probability; the ledger measures any departure.

### 1.17 Expected reach d·PoT(d) [B, from calib_ml, maths checked]
For driftless BM, d·2Φ(−d/s) (s = σ√H) is maximised where Φ(−z) = z·φ(z), z = d/s ≈ **0.75** (Φ(−0.75) = 0.2266,
0.75·φ(0.75) = 0.2259), where PoT ≈ **45%**. This is the principled shape for a proximity/reach pillar (deliver distance
× probability), and calib_ml measured 1.10-1.43 ATR delivered per target for a max-d·PoT picker vs 0.86-1.09 for the
engine-like hand score.

### 1.18 The 95% cap [A, B-fix on impact]
A display convention of the reference product, not a model property: a near level's true PoT approaches 1. Inside the
engine it sits in `f_pot` (444) and `f_potModel` (1310), and `evaluate` divides by 0.95 (665). Measured impact is
negligible (0.4), but the clean design is: uncapped maths, cap only in text, plots and the `minPoT` filter.

---

## 2. Evidence

### 2.1 Literature (numbers, grade, verification status)
| Claim | Number | Grade | Source | Status |
|---|---|---|---|---|
| BGK constant | β = −ζ(½)/√(2π) ≈ 0.5826; error O(1/√m) → o(1/√m) | strong | Broadie, Glasserman & Kou 1997, Math. Finance 7(4) | A✓ (abstract and summaries) |
| Same constant = expected overshoot of the driftless Gaussian walk | −ζ(½)/√(2π)·σ | strong | Chang & Peres 1997, Ann. Probab. 25(2); Janssen & van Leeuwaarden | B |
| Reflection principle on real bars | touch/finish = 1.99-2.02 at 0.5-4 ATR | moderate (our data) | b_ratio.py | B |
| Wiener model misprices first passage: low for x ≳ v_t, high for x ≲ 0.1v_t; collapse to 10·v_t; Student tail beyond ≈5·v_t | qualitative; 6 futures, transaction data, 1-120 min | strong | Perelló, Gutiérrez-Roig & Masoliver 2011, arXiv:1107.1174 | A✓ (paper read) |
| Range estimator theory | Parkinson ≈5.2, GK ≈7.4, RS ≈6, YZ highest of drift/gap-robust | strong (theory) | Parkinson 1980; Garman–Klass 1980; Rogers–Satchell 1991; Yang–Zhang 2000 J. Business 73(3) | A (k formula B✓) |
| Range estimators' realised efficiency | 1.2-5× typical on index data, no consistent winner | moderate | Vințe et al. 2022, arXiv:2205.01370 | B |
| Range estimators track integrated variance; robust to microstructure | qualitative | moderate | Shu & Zhang 2006 J. Futures Markets 26(3); Alizadeh, Brandt & Diebold 2002 J. Finance 57(3) | B |
| Intraday U-shape, S&P futures | \|r\| 0.095% → 0.055% → 0.105% | strong (shape) / not re-verified (numbers) | Andersen & Bollerslev 1997 J. Empirical Finance 4 | A (hosts blocked for B) |
| Share of S&P 500 daily variance in RTH | ≈75% | strong | Hansen et al. 2012, quoted in Hansen, Kim & Kimbrough | B |
| Crypto periodicity | high ≈16 UTC, low ≈5 UTC, spikes 00/08/16 UTC | strong | Hansen, Kim & Kimbrough 2024 J. Fin. Econometrics 22(1), arXiv:2109.12142 | B (upgraded A's moderate) |
| Daily × diurnal × intraday GARCH | 10-minute returns, 2,500 US stocks; pooled estimation beats per-stock | strong | Engle & Sokalska 2012 J. Fin. Econometrics 10(1) | B |
| CARR range model beats GARCH out of sample | S&P 500 | moderate | Chou 2005 J. Money Credit Banking 37(3) | B |
| EWMA decay | λ = 0.94 daily | strong | RiskMetrics 1996 | A |
| HAR-RV | daily/weekly/monthly cascade | strong | Corsi 2009 | A |
| Intraday predictability small | R² 1.6% in sample, 1.2% OOS | strong | Gao, Han, Li & Zhou 2018 JFE 129(2) | A✓ (via ict_time B2) |
| Stop/take-profit clustering | ≈9,700 orders at a dealing bank | strong | Osler 2003 J. Finance; Osler 2005 JIMF | A |
| S/R bounce memory and decay | 0.5 reached at ≈350 min (1 prior bounce), ≈900 min (4) on EURUSD 2018 | moderate | Chung & Bellotti 2021, arXiv:2101.07410 | A✓ (paper read) |
| Calibration methods | isotonic ≥ ≈1,000 points; Platt below | strong | Niculescu-Mizil & Caruana 2005 | A |
| Beta calibration contains identity, better on small sets | qualitative | strong | Kull, Silva Filho & Flach 2017 AISTATS; EJS 11(2) | B |
| Shrinkage | ratio ≈3.5 in total squared error | strong | Efron & Morris 1975 JASA 70 | A✓ |
| Variance ratio | definition, robust z | strong | Lo & MacKinlay 1988 | A |
| Touch ≈ 2× expiring-ITM in option practice; IV-based PoT too high | ≈20-year SPY strangle studies | weak | tastylive "Testing probability of touch", "Probability of touch: realistic expectations" | B |

### 2.2 A's walk-forward test (kept) with B's confidence intervals
Design [A]: at every bar after warm-up, random levels at k ∈ {0.5, 1, 1.5, 2, 3, 4, 6} × ATR(14) above and below the
close; y = 1 if the level is traded through (strict, like the engine's liquidity touch) within H bars. Every model is
causal (expanding or online, using only windows resolved before t). Reference: an in-sample oracle base rate per
(symbol, side, k), a deliberately hard benchmark.

5-min, 6 symbols, ≈1.2 M rows per horizon (oracle LL 0.5007 / 0.5621 / 0.5583) [A]:

| Model | H=12 LL | H=30 LL | H=30 Brier | H=30 ECE | H=30 slope | H=60 LL |
|---|---|---|---|---|---|---|
| p_eng_an (engine analytic: σ₅₀, 0.5·drift₅₀, cap) | 0.5470 | 0.6115 | 0.2063 | 0.058 | **0.66** | 0.6220 |
| p_cc0 (no drift) | 0.5401 | 0.5891 | 0.1989 | 0.042 | 0.76 | 0.5776 |
| p_yz (Yang–Zhang σ, no drift) | 0.5361 | 0.5875 | 0.1990 | 0.048 | 0.79 | 0.5776 |
| p_ns (range level + clustering, no seasonality) | 0.5419 | 0.5899 | 0.2011 | 0.081 | 0.87 | 0.5710 |
| p_cl (seasonality, flat level) | 0.5616 | 0.6003 | 0.2014 | 0.086 | 0.74 | 0.5734 |
| p_srng (seasonal × clustering vol time) | 0.5142 | 0.5659 | 0.1907 | 0.062 | 0.89 | 0.5533 |
| p_srng_cal (+ online Platt) | 0.5042 | 0.5557 | 0.1870 | 0.024 | 1.01 | 0.5438 |
| **p_eng_emp (engine default surface)** | 0.5016 | 0.5639 | 0.1905 | **0.004** | 0.99 | 0.5617 |
| p_emp_std (surface in vol-time units) | 0.5031 | 0.5561 | 0.1870 | 0.025 | 0.95 | 0.5455 |
| **p_emp_vs (surface + vol-state tercile, pooled)** | **0.4962** | 0.5538 | 0.1866 | **0.003** | 0.98 | 0.5477 |
| p_stack (online logistic of surface + vol time) | **0.4947** | **0.5503** | **0.1851** | 0.014 | 1.00 | **0.5412** |

**Day-block bootstrap (B, 5-min H = 30; 2,000 resamples of symbol-days; ≥ 0 = second model better):**

| Comparison | LL gain | 95% CI (symbol-day blocks) | 95% CI (calendar-day blocks) | per symbol CL / ES / GC / NQ / RTY / YM | days improved |
|---|---|---|---|---|---|
| engine analytic → no drift | **+3.66%** | +2.99 … +4.32 | +2.32 … +4.82 | +3.05 / +3.70 / +4.07 / +3.49 / +3.73 / +4.00 | 77% |
| no drift (σ_cc) → Yang–Zhang σ | +0.28% | −0.10 … +0.66 | −0.39 … +0.99 | +0.45 / +0.86 / +0.19 / +1.00 / −0.42 / −0.41 | 51% |
| engine surface → + vol-state split | **+1.79%** | +1.45 … +2.13 | +1.14 … +2.44 | +0.81 / +1.82 / +0.30 / +2.00 / +2.59 / +2.88 | 72% |
| engine surface → calibrated vol-time analytic | +1.46% | +0.85 … +2.11 | +0.36 … +2.65 | **−1.78** / +1.88 / **−1.16** / +2.78 / +2.73 / +3.72 | 60% |
| engine surface → surface in vol-time units | +1.38% | +0.66 … +2.13 | +0.14 … +2.58 | −1.96 / +1.82 / −1.35 / +2.68 / +2.78 / +3.65 | 58% |
| close-beyond: continuous → BGK shift | **+6.28%** | +5.88 … +6.67 | +5.69 … +6.85 | — | — |

Reading: drift removal and the vol-state split are robust (every symbol, tight CIs); the stand-alone vol-time models
win on the equity indices and lose on CL and GC, which is why they need the per-chart scorecard. The calendar-day CI
clusters ES/NQ/RTY/YM together (they move together), so it is the conservative one.

Other A results kept:
- 1-hour H = 12: engine analytic 0.5657, no drift 0.5527, engine surface 0.5268, p_emp_vs **0.5086** (all 6 better).
  H = 30 (30 hours): p_emp_vs 0.5558 vs 0.5587 (5 of 6); vol-time analytic worse (0.5649).
- 1-min H = 30 (30-minute clock horizon): engine surface 0.5517, p_emp_vs 0.5484 (all 3), calibrated vol-time 0.5570
  (worse): vol time pays only when H × timeframe covers a material part of the daily cycle.
- Driftless random-walk simulation: σ₅₀ no drift LL 0.4785 (slope 0.95); with 0.5·drift₅₀ 0.5041 (slope 0.83); with
  1.0·drift₅₀ 0.5809 (slope 0.57).
- Seasonality (5-min Parkinson variance / day mean): ES 09:30 ET 4.67×, 10:00 3.57×, 10:30 2.75×, 23:30 0.20×; NQ
  09:30 6.17×; CL 09:30 2.17×, 18:00 reopen 1.94×, min 0.21×; GC max/min 6.7×.
- ETA (5-min, H = 60, conditional median): rank correlation (actual T, predicted) constant-σ −0.09 vs vol-time +0.11 /
  +0.16 / +0.22 at 1 / 2 / 3 ATR; share of hits at or before the predicted median 0.45-0.47 (vol time).
- Close-beyond (BGK): 5-min H = 12 / 30 / 60 realised 0.295 / 0.453 / 0.574; continuous 0.423 / 0.583 / 0.693; BGK
  0.344 / 0.517 / 0.641; 1-hour H = 12: LL 0.558 → 0.507; 1-min H = 30: 0.618 → 0.583.
- Overlap VIF/H: 0.50-0.71 (H = 12), 0.32-0.83 (H = 30), 0.21-0.53 (H = 60).

### 2.3 B's new tests
**(a) Finite-horizon race = the engine's WIN≤H** (`b_race_h.py`). 5-min, 6 symbols, every 2nd bar after 2,000 bars of
warm-up, H = 30; barrier pairs (a, b) ATR ∈ {1/1, 1/2, 2/1, 1/3, 3/1, 2/2, 3/2, 2/3, 4/2, 2/4, 6/2, 2/6, 4/4, 6/3};
first touch by strict high/low trade-through; same-bar ties resolved by the engine's bar-path rule (gap at the open
decides; bull bar O-L-H-C, bear bar O-H-L-C; `f_step` 1434-1459). 598,178 races, 479,485 decided within H (80.2%).

| Model of P(target first \| decided) | LL | Brier | slope |
|---|---|---|---|
| b/(a+b) | 0.6119 | 0.2111 | 1.20 |
| f_raceH, σ₅₀, μ = 0 | 0.6131 | 0.2108 | 0.89 |
| **f_raceH, σ₅₀, engine drift (current WIN≤H before `f_raceAdj`)** | **0.6359** | 0.2186 | **0.69** |
| f_raceH, vol-time σ_eff = √(V_H/H), μ = 0 | **0.6086** | **0.2094** | **1.00** |

Day-block bootstrap: engine → no drift **+3.58%** (CI +2.74 … +4.41; every symbol +3.4 … +3.9%); σ₅₀ → σ_eff
**+0.74%** (CI +0.38 … +1.04; CL +0.13, ES +1.30, GC −0.05, NQ +0.97, RTY +0.89, YM +1.08); engine → σ_eff **+4.29%**
(CI +3.38 … +5.11). Calendar-day clustering (55 days, the conservative version): engine → no drift +1.98 … +5.02%; σ₅₀ → σ_eff +0.23 … +1.18%; engine → σ_eff +2.69 … +5.85%.

**(b) Reflection identity** (`b_ratio.py`): see 1.1. Implication for the engine: the touch surface and the analytic
formula are consistent with the bar data; no correction for intrabar monitoring is needed for touches.

**(c) BGK Monte Carlo** (`b_ratio.py`): see 1.4.

### 2.4 Sibling cross-checks used here
- ict_time §2.2 (B/B2, `clock_sim2.py`): robust NY-keyed clock + z-unit surface (clkB) Brier vs engine: +3.86% (5-min
  H = 30), +5.45% (H = 60), +3.86% (1-hour H = 12), −1.05% (1-hour H = 30); per symbol 1-hour H = 30 GC **−9.8%**.
  Time-of-day surface tod8: +2.18% / +2.15% / +3.75% / +0.38%, never negative per symbol. Engine PoT hour bias: mean
  |pred − obs| 7.3 pp (5-min H = 30) with −12 … −17 pp at 07-09 ET; clkB 2.1 pp.
- calib_ml §0: distance-matched baseline slope 0.93-1.04 on 13/14 datasets; learners on selected targets lose
  0.15-5.5% LL; gated learner 0.00 … −0.26% on clean sets, +8.8% on GC 1-hour; candidate (shadow) ledger gives
  ≈2,500-3,500 probes per 5,000 bars.

---

## 3. Engine gap analysis (baseline_v2.pine; all line numbers re-checked by B)

### 3.1 Audit of the PoT and race code
| Item | Lines | Verdict | Notes |
|---|---|---|---|
| `f_erfcLog` / `f_erfc` / `f_phi` | 408-419 | correct [A✓] | Numerical Recipes erfc, fractional error < 1.2e-7. |
| `f_expPhi` | 421-429 | correct [A✓] | log-space e^e·Φ(b); avoids overflow of the reflection term. |
| `f_pot` | 434-444 | correct maths; cap inside | `math.min(0.95, …)` at 444; impact tiny (B-fix). |
| `f_race` | 447-462 | correct [A✓] | scale-function race; driftless limit b/(a+b) when \|k(a+b)\| < 1e-6. |
| `f_raceH` | 466-482 | correct [A✓, B re-derived] | term count from e^{−40} truncation, cap 400 (needs L > 500 ATR at H = 30 to bind); exp clipped at 50 (irrelevant at μ = 0). |
| `potSig = ta.stdev(chg, potLen)` | 916 | weak | trailing, time-blind, close-to-close; includes the unclosed bar live. Range-based alone does not fix it (B). |
| `potMu = ta.sma(chg, potLen) * driftW` (`driftW` default 0.5, line 185) | 917 | **wrong** [A✓] | −3.66% LL in PoT, −3.58% in the race; used at 665 (via 1948), 1304 (via 2067, 2184), 1361-1363. |
| Proximity reach `f_pot(dist, sig, mu·side, potH)/0.95` | 665, called at 1948 | partial | drift noise enters selection through the proximity pillar (weight 25, half of it reach); time-blind σ; ad-hoc lin+reach blend instead of expected reach d·PoT (1.17). |
| Empirical surface `sUp/sDn` (3 HTF regimes × 61 bins) | 1058-1062, 1265-1300, 1527-1532 | present, calibrated | no time-of-day or volatility state; regime rows not shrunk to the pooled row (only a fallback below `nMin`, 1292-1299); `htfBias` has no side skill (bias_dol). |
| Surface update scope | 1527-1532 | good (B) | runs on every confirmed bar of the loaded history, outside `inCalc`, with `htfBias[H]` and `atr[H]` at the window start (leak-free: skeptic). No forgetting of old windows (minor). |
| nEff = n/(0.6H) | 1308, 1319 | present, OK [A✓] | measured VIF/H 0.21-0.83. |
| Bayesian blend, `priorM` = 30 | 1303-1311 | present | correct form; prior carries the drift and cap (3-10% weight at normal history). |
| Beyond-grid fallback (u > NB → analytic) | 1292-1293 | minor (B-fix) | only for d > 15 × ATR14 (possible when ATR14 < ATR200 because ejection uses atrE). |
| `f_potBase` random-level baseline | 1314-1322 | present, time-blind | driftless (good); cap bias ≤ 0.4 pp (B-fix); inherits the time-of-day bias (ict_time G16: ±2-3 pp per clock window). |
| `f_reachD` reach bands | 1325-1338, 2112-2115 | present | would inherit state conditioning. |
| `f_invalidation` race (WIN≤H) | 1343-1364 | **wrong** (B upgrade from "partial") | drift `potMu·side` (1361-1363) → slope 0.69; σ₅₀ instead of forward variance. Conditional-on-decided form itself is right. |
| `f_raceAdj` | 1367-1373 | present | intercept-only logit shift (m = 20); cannot repair a slope of 0.69. |
| `f_calMult` | 1376-1382 | noisy (calib_ml) | not a PoT item; noted because it multiplies scores using `pBase`. |
| `Trial` / `f_openTrial` / `f_book` | 375-395, 1426-1431, 1461-1499 | **missing piece** [A✓] | no `pPot`; the displayed PoT is never graded. Trials open whenever the active DOL has no open trial (2037-2045). |
| ETA | 2116-2126 | partial [A✓] | median bars-to-hit of past DOL hits within ±0.5 ATR of the current distance; time-blind; no clock label or quantiles. |
| Live PoT | 2060-2068 | OK | deliberately live; `sweptNow ? 0.95`; full H although part of the bar elapsed (< 1 pp, B-fix). |
| Secondary targets' PoT | 2184 | inherits | same `f_potModel` with drift. |
| Data window plot | 2446 | OK | "DOL PoT %". |
| Close-beyond probability | none | missing [A✓] | sweep-vs-break needs it. |
| "Next pool taken" race | none | missing [A] | only target-vs-invalidation exists. |
| Session time zone available | 219 (`tz`) | available (B) | the clock and any time-of-day key must use it. |

### 3.2 Concept status summary
| Concept | Status |
|---|---|
| Reflection-principle PoT | present (maths correct; validated on bars by B) |
| Martingale race (infinite horizon) | present as limit |
| Finite-horizon conditional race | present but **wrong inputs** (drift, trailing σ) |
| BGK discrete monitoring | correctly absent for touches; missing for close events |
| Time-to-touch quantiles | partial (bar-count median of past hits) |
| Range-based σ | missing (low value alone) |
| Seasonality / volatility time (tz-keyed, future-bar calendar) | missing |
| Volatility clustering forecast | missing |
| Drift | **wrong** |
| Fat tails | partial (surface inside the grid) |
| Empirical excursion surface + overlap-aware n | present |
| State conditioning + partial pooling | missing (single, unshrunk HTF key) |
| Bayesian blend | present |
| Grading / gated recalibration of displayed PoT | missing |
| Expected-reach proximity | partial (ad-hoc) |
| 95% cap placement | cosmetic (display-only preferred) |

---

## 4. Proposals (best first; max 12)

Conventions: line numbers from baseline_v2.pine; `H` (305), `chartS` (308), `atr` (874), `NB/NB1` (302-303), `bStep` (307), `tz`
(219). All learning runs inside `if barstate.isconfirmed` (non-repainting); live readouts reuse the last confirmed
statistics. A function cannot `:=` a global scalar, so mutable statistics live in `var` arrays (as `raceSt`, `stN` do).
New inputs use `display = display.none` (the overhaul's legend fix). Order respects Pine's no-forward-reference rule:
inputs → derived constants → series → state → helpers → engine.

### QPOT-01 · Remove the 50-bar drift from every probability (P1, effort S) [A✓, extended by B]
- **Why.** Largest single error: PoT log-loss +3.66% (CI +2.99 … +4.32%, all 6 symbols), race +3.58% (CI +2.74 … +4.41%,
  all 6), driftless simulation +5.4%. The drift also double-counts the Draw pillar inside the proximity pillar.
- **Change.**
  - Line 185: `driftW` default **0.0**; keep the input only for experts (`display = display.none`), or delete it and set
    line 917 to `float potMu = 0.0`.
  - If kept non-zero, shrink the raw mean before weighting it: `float muRaw = ta.sma(chg, potLen)`,
    `float tD = muRaw / math.max(potSig / math.sqrt(potLen), 1e-12)`,
    `float potMu = driftW * muRaw * math.max(0.0, 1.0 - 1.0 / math.max(tD * tD, 1e-12))` (positive-part James–Stein:
    zero unless |t| > 1).
  - Call sites then carry zero drift: `evaluate` via 1948, `f_potModel` via 2067 and 2184, `f_invalidation` 1361-1363.
- **Ledger check.** Race slope (QPOT-02) and PoT slope (QPOT-04) should move toward 1; EDGE unaffected (`f_potBase` is
  already driftless).
- **Risk.** Selection changes slightly (proximity becomes side-symmetric). Directional information still flows through
  the Draw pillar and the regime rows of the surface.

### QPOT-02 · Make WIN≤H a calibrated finite-horizon race (P1, effort S) [B]
- **Why.** The displayed "WIN≤H" (target before invalidation, among races decided within H) has slope 0.69 today.
  Driftless `f_raceH` with forward variance is calibrated (slope 1.00) and +4.29% better in log-loss (CI +3.38 … +5.11%);
  driftless with σ₅₀ already gets +3.58%.
- **Change (f_invalidation 1343-1364).**
  ```
  float sg = clkUse ? close * math.sqrt(fwdV / H) : nz(potSig)   // fwdV: forward log-variance over H bars (QPOT-05); else σ₅₀
  float pW = f_raceH(d, risk, sg, 0.0, H)
  float pL = f_raceH(risk, d, sg, 0.0, H)
  [inv, d / risk, pW + pL > 1e-9 ? pW / (pW + pL) : d + risk > 0 ? risk / (d + risk) : 0.5]
  ```
  Keep `f_raceAdj` (it now corrects a calibrated model, so its intercept stays near 0).
- **Display.** Unchanged label ("WIN≤H"). Do not show the unconditional P(decided within H): Brownian motion over-predicts
  it by 3-7 pp at mid distances (2.3 a). If wanted, show "undecided ≈ x%" from the ledger's own race counts
  (`raceSt[4] − raceSt[0]` over `raceSt[4]`).
- **Ledger.** Add Σ(p − y)² for decided races to `raceSt` (one more slot) so the Full panel can show the race Brier and
  slope; target slope ≈ 1.
- **Risk.** None beyond QPOT-01; σ_eff needs QPOT-05 for the last +0.7%.

### QPOT-03 · State-conditioned empirical surface with partial pooling (P1, effort M) [A✓ + TIME-2 + REG-1 merged]
- **Why.** The default surface is calibrated but has no time or volatility resolution: vol-state split +1.79% LL (CI
  +1.45 … +2.13%, all 6 symbols, ECE ≤ 0.004); TIME-2's time-of-day split improved Brier in 24/24 tests and cut the
  hour bias by a third to a half. The HTF-regime rows are currently used unshrunk once they pass `nMin`, although
  `htfBias` has no side skill.
- **Inputs (G_POT).**
  ```
  string potKey = input.string("Time block", "PoT Surface State", options = ["Off", "Time block", "Vol state"], group = G_POT,
    display = display.none, tooltip = "Learns how far price travels within the horizon separately per New York 3-hour block (or per forecast volatility state). A cell borrows from the pooled surface until it has enough history.")
  ```
- **Derived (after 308).** `const int NS = 8`, `const int NS1 = 9` (index 8 = state-pooled row), `const float POOLM = 30.0`.
- **Series (after 917).**
  ```
  int stNow = potKey == "Time block" and timeframe.isintraday and chartS <= 3600 ? int(hour(time, tz) / 3) :
       potKey == "Vol state" and not na(vsNow) ? vsNow : NS          // NS = no state (pooled only)
  ```
  `vsNow` (only with QPOT-05): ln q, q = √fwdV / (atr/close · √H); EWMA mean m and sd s of ln q with α = 1 − 0.5^(1/2000)
  in a `var` array; `vsNow = lnq < m − 0.43s ? 0 : lnq > m + 0.43s ? 2 : 1` (normal terciles, O(1)).
- **State (replace 1061-1062).** `var array<int> sUp = array.new<int>(3 * NS1 * NB1, 0)` (same for `sDn`; 1,647 ints
  each). Row index = `regime * NS1 + state`.
- **Step 0 (1528-1532).**
  ```
  int   bH = htfBias[H]
  int   sH = stNow[H]
  float xu = (fwdHi - close[H]) / aH
  float xd = (close[H] - fwdLo) / aH
  f_bump(sUp, (bH + 1) * NS1 + NS, xu)
  f_bump(sDn, (1 - bH) * NS1 + NS, xd)
  if sH < NS
      f_bump(sUp, (bH + 1) * NS1 + sH, xu)
      f_bump(sDn, (1 - bH) * NS1 + sH, xd)
  ```
- **Read (`f_empPoT`, 1284), three-level pooling.**
  ```
  f_empPoT(float dAtr, int side, int bias, int st) =>
      array<int> S  = side == 1 ? sUp : sDn
      int   r  = side == 1 ? bias + 1 : 1 - bias
      float u  = math.max(0.0, dAtr) / bStep
      float dv = math.max(1.0, 0.6 * H)
      float n0 = 0.0
      float k0 = 0.0
      for g = 0 to 2                                   // global parent = the three regimes' pooled rows
          n0 += S.get((g * NS1 + NS) * NB1)
          k0 += u > NB ? 0.0 : f_surv(S, g * NS1 + NS, u)
      float p = na
      if u <= NB and n0 >= math.max(150.0, 20.0 * H)
          float p0 = k0 / n0
          float nR = S.get((r * NS1 + NS) * NB1)
          float pR = nR > 0 ? (nR / dv * (f_surv(S, r * NS1 + NS, u) / nR) + POOLM * p0) / (nR / dv + POOLM) : p0
          p := pR
          if st < NS
              float nC = S.get((r * NS1 + st) * NB1)
              p := nC > 0 ? (nC / dv * (f_surv(S, r * NS1 + st, u) / nC) + POOLM * pR) / (nC / dv + POOLM) : pR
      [p, u > NB ? 0.0 : n0]
  ```
  Callers: `f_potModel` (1307) and `f_potBase` (1318) pass `stNow` (live bar's state for the live PoT); `f_reachD`
  (2112-2115) reads the state cell when its count ≥ `max(150, 20H)`, else the regime row.
- **Cost.** Three O(NB) bumps per side per bar; 6 extra `get`s per query. Memory 3.3k ints.
- **Gate.** TIME-4's probe scorecard picks "Off / Time block / Vol state" per chart (no per-symbol hard-coding).
- **Risk.** Slower per-cell warm-up (pooling handles it). DST mismatch of the London open (≈4 weeks a year) is absorbed by
  3-hour blocks.

### QPOT-04 · Grade the displayed PoT; recalibrate only behind a prequential gate (P1, effort M) [A✓ + calib_ml]
- **Why.** The number in the label ("PoT: 70.1%") is never checked. Grading is cheap and makes the product
  self-auditing; blind recalibration on selected targets hurts on clean data (calib_ml), so it must be gated.
- **Trial (375-395).** Add `float pPot = na` (model PoT at open, uncapped). In `f_openTrial` (1426-1431):
  `pPot = f_potModel(d, lv.side, 0.0)`, the same call that produced the label at that bar close.
- **Accumulators (STATE, after 1080).**
  ```
  // [n, Σ(p−y)², Σ(pBase−y)², ΣLL, Σp, Σy, prequential ΣLL(raw) − ΣLL(cal), K_cal, P_cal]
  var array<float> potSt = array.new<float>(9, 0.0)
  var array<float> rbN   = array.new<float>(10, 0.0)   // reliability bins
  var array<float> rbP   = array.new<float>(10, 0.0)
  var array<float> rbY   = array.new<float>(10, 0.0)
  ```
- **f_book (1461).** With `p = f_clamp(t.pPot, 0.005, 0.995)`, `y`:
  1. calibrated value computed *before* using this outcome: `δ = n ≥ 30 ? f_logit((K + 20·P̄)/(n + 20)) − f_logit(P̄) : 0`,
     `pc = f_sigm(f_logit(p) + δ)` (the `f_raceAdj` form; P̄ = mean p);
  2. `potSt[6] += LL(p, y) − LL(pc, y)` (prequential evidence for the calibrator);
  3. then update n, Σ(p−y)², Σ(pBase−y)², ΣLL, Σp, Σy and bin `int(p·10)`.
- **Use.** Display the calibrated value only when `n ≥ 50 and potSt[6] > 2.0` (calibrator has out-predicted the raw
  model by more than 2 nats prequentially); otherwise show the model value. Optional upgrade: replace the intercept with
  beta calibration (contains the identity) once n ≥ 300.
- **Panel (Terminal, Accuracy = Full).** `PoT CAL  pred 44% · obs 46% · Brier .201 vs base .215 · n 212` and a 10-cell
  reliability strip. Clean style unchanged (tooltip only).
- **Evidence.** Methods strong (Murphy 1973; Platt 1999; Niculescu-Mizil & Caruana 2005; Kull et al. 2017); need moderate
  (calib_ml: selected targets −6.9 … +2.8 pp from baseline).
- **Risk.** Overlapping trials → small effective n: keep the gate conservative; use 2H-bar blocks (as `cluSt`) for any
  z-score shown.

### QPOT-05 · Forward-variance engine: robust tz-keyed clock with the real future-bar calendar (P1 as an input, effort M-L) [A re-scoped by B; spec = TIME-3]
- **Why.** Every time-aware piece (race σ_eff in QPOT-02, vol state in QPOT-03, ETA and session PoT in QPOT-06,
  close-beyond in QPOT-07) needs V(j), the forecast variance of the next j bars. As a stand-alone displayed PoT it is
  better on average (+1.46% LL) but loses on CL/GC and on GC 1-hour, so its *display* use is scorecard-gated (TIME-4).
- **Model (use TIME-3's robust code; B's corrections to A's version in bold).**
  - Variance proxy (log units): `xVar = max(0, ½·ln(H/L)² − (2ln2 − 1)·ln(C/O)²) + ln(O/C[1])²`, **winsorised** at 25×
    the slow level (rolls, bad prints).
  - Seasonal factor by **`tz`** time-of-day bucket (bucket = max(15/30 min, chart TF)) × weekday factor; **additive EWMA
    of the deseasonalised ratio, cumulative-mean warm start (1/n), floors 0.05 (bucket) / 0.2 (weekday)**; daily
    renormalisation (mean factor = 1).
  - Levels: fast L_f (EWMA span ≈ potLen) and slow L_s (≈5 days), both of xVar/s², floored L_f ≥ 0.2·L_s;
    φ = 0.5^(1/30).
  - **Forward path over the real calendar:** V(j) = Σ_{i≤j} s²(bucket(t_i), weekday(t_i))·[L_s + φ^i(L_f − L_s)], with
    t_i the open time of the i-th future bar. Two Pine options:
    1. TIME-3's open-cell grid walk (a cell is open when it held bars on ≥ 30% of past days; skips the daily halt and
       weekends; ≈H/bpb iterations): use on every scoring bar;
    2. exact: `int ti = time(timeframe.period, "", bars_back = -i)` for i = 1 … min(H, 500) (docs: "expected timestamp of
       the bar … N bars after the current bar"; session-aware, no holidays): use on `barstate.islast` for clock labels
       and as a check of option 1.
  - Store `var array<float> vCum` (length H) on the last bar for ETA; on scoring bars only `fwdV = V(H)` (a series,
    so `fwdV[H]` exists for the z-surface and `vsNow`).
- **Outputs.** `fwdV`, `vCum`, `clkUse` (true when the clock is warm, ≥ 5 days, and the chart is intraday ≤ 4H).
- **Evidence.** Concept strong (Andersen–Bollerslev; Engle–Sokalska; Dacorogna); data moderate (A: seasonal × clustering
  needed, each alone fails; TIME-3: +3.9 / +5.5 / +3.9% Brier where it works, −9.8% on GC 1-hour).
- **Risk.** Holidays and early closes overstate V (label clock outputs "≈"); jump-prone series (GC 1-hour) → gate.

### QPOT-06 · ETA quantiles in volatility time and "PoT to session end" (P2, effort M) [A + TIME-6, formulas corrected by B]
- **Why.** Traders ask *when*. The current ETA ignores the clock and ranks time-to-touch wrongly (−0.09); vol-time ranks
  it correctly (+0.11 / +0.16 / +0.22).
- **Formulas (μ = 0).** F(j) = 2Φ(−d/√V(j)) with V(j) = `vCum[j−1]` (log variance × close² for price units).
  - Conditional ETA_q (shown next to PoT): first j with F(j) ≥ q·F(H) ⇔ √V(j) ≥ d / Φ⁻¹(1 − q·F(H)/2). Show q = 0.5
    and 0.8. Inverting Φ: Acklam's rational approximation, or a binary search on j over `vCum` (≤ 9 steps for H ≤ 450).
  - Unconditional median, if ever shown: V(j) ≥ (d/0.6745)²; unconditional 80%: (d/0.2533)² (**not 1.2816**).
  - Clock label: `str.format_time(time(timeframe.period, "", bars_back = -j), "HH:mm", tz)` (j ≤ 500).
  - PoT to session end: count future bars to the end minute with the docs' `time_close(timeframe.period, sess, bars_back
    = -i)` loop (stop at `na`, ≤ 500), then PoT_S = surface at z = d/√V(j_end) (or 2Φ(−z) before warm-up).
- **Display.** Terminal HUD: `PoT 30b 64% · →16:00 71% · ETA ≈10:35 (80% by 11:20)`; Clean: tooltip only.
- **Ledger.** For hits store T and ETA50/ETA80: coverage shares (targets 50% / 80%) in the Full panel.
- **Risk.** Holiday calendars unknown; requires QPOT-05 (fallback: current bar-count ETA).

### QPOT-07 · Close-beyond probability: an empirical close surface with a BGK prior ("sweep vs break") (P2, effort S) [A's BGK + B's surface]
- **Why.** Raids are wick events; breaks are close events. The continuous formula over-states close-beyond by 13 pp; the
  BGK shift fixes most of it (+6.28% LL), and an empirical close-excursion surface removes the remaining level bias at
  almost no cost.
- **Pine.**
  ```
  // SERIES (after 921)
  float fwdHiC = ta.highest(close, H)
  float fwdLoC = ta.lowest(close, H)
  // STATE
  var array<int> cUp = array.new<int>(NB1, 0)
  var array<int> cDn = array.new<int>(NB1, 0)
  // step 0 (inside the same guard as 1528)
  f_bump(cUp, 0, (fwdHiC - close[H]) / aH)
  f_bump(cDn, 0, (close[H] - fwdLoC) / aH)
  // read
  f_closePoT(float d, int side) =>
      array<int> S = side == 1 ? cUp : cDn
      float u  = math.max(0.0, d / atr) / bStep
      float sb = clkUse ? close * math.sqrt(fwdV / H) : nz(potSig)
      float pA = sb > 0 ? f_erfc((d + 0.5826 * sb) / (sb * math.sqrt(2.0 * H))) : 0.0   // BGK prior; V_H ≈ sb²·H
      float n  = S.get(0)
      float nE = n / math.max(1.0, 0.6 * H)
      u <= NB and n > 0 ? (nE * f_surv(S, 0, u) / n + priorM * pA) / (nE + priorM) : pA
  ```
  (With QPOT-05, use `pA = f_erfc((d + 0.5826*sb) / math.sqrt(2.0 * close*close*fwdV))`.)
- **Display.** Liquidity targets: `PoT 71% · close-thru 52%` (Terminal HUD, Clean tooltip). `PoT − close-thru` = chance of a
  wick-only raid within H (an upper bound on "sweep and reject").
- **Evidence.** BGK strong (theory; MC-confirmed); data moderate (5-min H = 30: realised 0.453, continuous 0.583, BGK
  0.517; LL CI +5.88 … +6.67%; same on 1-hour and 1-min).
- **Risk.** One more HUD field; the close surface warms with the touch surface (same windows).

### QPOT-08 · "Next liquidity taken" race readout (P2, effort S) [A, re-specified by B]
- **Why.** The literal DOL question ("which pool goes first?") is a two-barrier race; with QPOT-02's model it is
  calibrated, and the ledger's deviation from it is a direct, per-chart measure of liquidity "magnetism".
- **Pine.** On confirmed bars (and the last bar for display): nearest unswept liquidity (`kind ≤ 1`) above (distance a)
  and below (b) from `pool`; require a, b ≥ `minDistATR`·atr.
  `pUp = f_raceH(a, b, sg, 0.0, H) / (f_raceH(a, b, sg, 0.0, H) + f_raceH(b, a, sg, 0.0, H))`, `sg` as in QPOT-02.
  Ledger `var array<float> nxSt = array.new<float>(4, 0.0)` [n, up wins, Σp, Σ(p−y)²]: one open record per new pair
  (ids stored in a small `var` array), resolved when either pool is swept (strict trade-through, ties by the bar-path
  rule) or dropped after H bars (undecided). Logit shift exactly as `f_raceAdj`, applied only when n ≥ 30.
- **Display.** Terminal panel row `NEXT ▲ BSL 62% · ▼ SSL 38%` (+ "n 140 · obs 64%" in Full). Optional `alert()` when one
  side ≥ 70% at bar close.
- **Evidence.** Theory strong (1.2-1.3); calibration of the model moderate (2.3 a).
- **Risk.** Pools very near price resolve in 1-2 bars (hence the minDist gate).

### QPOT-09 · Display-only cap and small hygiene items (P3, effort S) [A, impact re-measured by B]
- `f_pot` (444) and `f_potModel` (1310) return uncapped values; apply `math.min(0.95, p)` only to `activePoT` text, the
  label (2225), HUD (2240), panel (2354), alert text (2081), the data-window plot (2446) and the `minPoT` comparison
  (2068, 2185). `evaluate` (665): `reach = f_pot(dist, sig, 0.0, potH)` without `/0.95`.
- `f_potBase` (1314-1322) uncapped.
- Beyond-grid fallback (1292-1293): use the reflection identity with a fat-tailed terminal law, e.g. a two-component
  variance mixture `p = 0.5·f_erfc(d/(0.8·sH·√2)) + 0.5·f_erfc(d/(1.17·sH·√2))` (same mean variance, kurtosis ≈ 3.4),
  sH = σ√H; or simply widen `bStep` so the grid always covers the eject distance in ATR14 units.
- Evidence: weak (consistency); impact ≤ 0.4 pp.

### QPOT-10 · Model mixture instead of a fixed stack (P3, effort M) [A's QPOT-08, re-specified]
- **Why.** A's online logistic stack had the best pooled log-loss (H = 30: 0.5503; H = 60: 0.5412) but was fragile on bad
  data, and calib_ml found unregularised online logistic loses 3.6-5.5% elsewhere. A two-expert exponential-weights
  mixture keeps most of the upside and cannot do much worse than the better expert.
- **Spec.** Experts: e1 = QPOT-03 surface, e2 = QPOT-05 clock z-surface (TIME-3 phase B). Weights w_i ∝ exp(−η·L_i) with
  η = 0.25 and fixed share 0.005, where L_i is the probe log-loss accumulated by TIME-4's probes (6 per bar); PoT =
  w1·p1 + w2·p2. Show "PoT MODEL mix 0.7/0.3" in Full.
- **Evidence.** moderate (A's stack; calib_ml's mixture results). **Risk.** Extra state (TIME-4's probe ring buffer).

### Dropped or merged
- ID map from A's report: A-01 → 01, A-02 → 05 (re-specified), A-03 → 03, A-04 → 04, A-05 → 06, A-06 → 08, A-07 → 07,
  A-08 → 10, A-09 → 09. QPOT-02 (race) is new from B.
- A's "live remaining time" (H − 1 + fraction): < 1 pp, dropped.
- A's QPOT-02 as written (UTC buckets, clock-time walk, multiplicative update): replaced by QPOT-05 (TIME-3 spec).
- Range-based σ as a stand-alone switch: not significant (+0.28%); only as the clock's proxy.

### Dependencies and suggested order
QPOT-01 → QPOT-02 (σ₅₀ form) → QPOT-04 (grading) → QPOT-03 ("Time block") → QPOT-05 → QPOT-02 (σ_eff), QPOT-03
("Vol state"), QPOT-06, QPOT-07 → QPOT-08 → TIME-4 scorecard → QPOT-10. QPOT-09 any time.

---

## 5. Sources
Primary / academic
- Broadie, M., Glasserman, P., Kou, S. (1997). A continuity correction for discrete barrier options. Mathematical Finance 7(4), 325-349. https://ideas.repec.org/a/bla/mathfi/v7y1997i4p325-349.html ; summary https://almostsuremath.com/2023/07/01/discrete-barrier-approximations/ ; extensions: Howison & Steinberg https://people.maths.ox.ac.uk/howison/papers/discbarrier.pdf
- Chang, J. T., Peres, Y. (1997). Ladder heights, Gaussian random walks and the Riemann zeta function. Ann. Probab. 25(2), 787-802. https://www.projecteuclid.org/euclid.aop/1024404419 ; Janssen & van Leeuwaarden, moments of the maximum of the Gaussian random walk: https://www.eurandom.tue.nl/oldevents/workshops/2006/Queues/Leeuwaarden.pdf ; arXiv:2007.13991
- Asmussen, Glynn, Pitman (1995). Discretization error in simulation of one-dimensional reflecting Brownian motion. Ann. Appl. Probab. 5(4). https://web.stanford.edu/~glynn/papers/1995/AGP95.html
- Perelló, J., Gutiérrez-Roig, M., Masoliver, J. (2011). Scaling properties and universality of first-passage time probabilities in financial markets. arXiv:1107.1174 (read via the research index)
- Kou, S., Wang, H. (2003). First passage times of a jump diffusion process. http://www.columbia.edu/~sk75/KouWangAAP.pdf
- Parkinson (1980); Garman & Klass (1980); Rogers & Satchell (1991); Yang, D., Zhang, Q. (2000). Drift-independent volatility estimation based on high, low, open, and close prices. J. Business 73(3), 477-491. https://econpapers.repec.org/RePEc:ucp:jnlbus:v:73:y:2000:i:3:p:477-91
- Vințe, C., Ausloos, M., Furtună, T. F. (2022). A volatility estimator of stock market indices based on the intrinsic entropy model. arXiv:2205.01370 (empirical efficiency tables)
- Shu, J., Zhang, J. E. (2006). Testing range estimators of historical volatility. J. Futures Markets 26(3), 297-313. https://ideas.repec.org/a/wly/jfutmk/v26y2006i3p297-313.html
- Alizadeh, Brandt, Diebold (2002). Range-based estimation of stochastic volatility models. J. Finance 57(3). https://onlinelibrary.wiley.com/doi/10.1111/1540-6261.00454
- Martens & van Dijk (2007). Measuring volatility with the realized range. J. Econometrics 138(1). https://ideas.repec.org/a/eee/econom/v138y2007i1p181-207.html
- Chou, R. Y. (2005). Forecasting financial volatilities with extreme values: the CARR model. J. Money, Credit and Banking 37(3), 561-582. https://ideas.repec.org/a/mcb/jmoncb/v37y2005i3p561-82.html
- Andersen, T., Bollerslev, T. (1997). Intraday periodicity and volatility persistence in financial markets. J. Empirical Finance 4(2-3), 115-158. https://ideas.repec.org/a/eee/empfin/v4y1997i2-3p115-158.html
- Andersen, Bollerslev, Cai (2000). Intraday and interday volatility in the Japanese stock market. https://public.econ.duke.edu/~boller/Published_Papers/jifmim_00.pdf
- Engle, R., Sokalska, M. (2012). Forecasting intraday volatility in the US equity market: multiplicative component GARCH. J. Fin. Econometrics 10(1), 54-83. https://ideas.repec.org/a/oup/jfinec/v10yi1p54-83.html
- Hansen, P. R., Kim, C., Kimbrough, W. (2024). Periodicity in cryptocurrency volatility and liquidity. J. Fin. Econometrics 22(1), 224-251; arXiv:2109.12142
- RiskMetrics Technical Document (1996). Corsi, F. (2009). A simple approximate long-memory model of realized volatility. J. Fin. Econometrics.
- Gao, L., Han, Y., Li, S. Z., Zhou, G. (2018). Market intraday momentum. J. Fin. Econ. 129(2). https://www.sciencedirect.com/science/article/abs/pii/S0304405X18301351
- Lo, A., MacKinlay, C. (1988). Stock market prices do not follow random walks: evidence from a simple specification test. RFS.
- Osler, C. (2003). Currency orders and exchange-rate dynamics. J. Finance 58(5). https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr125.pdf ; Osler (2005). Stop-loss orders and price cascades. JIMF 24(2).
- Garzarelli, F., Cristelli, M., Zaccaria, A., Pietronero, L. (2014). Memory effects in stock price dynamics. Sci. Rep.; arXiv:1110.5197
- Chung, B., Bellotti, A. (2021). Evidence and behaviour of support and resistance levels in financial time series. arXiv:2101.07410 (read via the research index)
- Niculescu-Mizil, A., Caruana, R. (2005). Predicting good probabilities with supervised learning. ICML. https://www.cs.cornell.edu/~alexn/papers/calibration.icml05.crc.rev3.pdf
- Kull, M., Silva Filho, T., Flach, P. (2017). Beta calibration. AISTATS, PMLR 54. https://proceedings.mlr.press/v54/kull17a.html ; Beyond sigmoids, EJS 11(2). https://projecteuclid.org/euclid.ejs/1513306867
- Murphy (1973) decomposition via Siegert (2017). https://ore.exeter.ac.uk/articles/journal_contribution/Simplifying_and_generalising_Murphy_s_Brier_score_decomposition/29748851/1/files/56771708.pdf
- Efron, B., Morris, C. (1975). Data analysis using Stein's estimator and its generalizations. JASA 70, 311-319. https://www.medicine.mcgill.ca/epidemiology/hanley/bios602/MultilevelData/EfronMorrisJASA1975.pdf
- Dacorogna, Müller, Nagler, Olsen, Pictet (1993). A geographical model for the daily and weekly seasonal volatility in the FX market. JIMF (via ict_time).

Practitioner (weak evidence)
- tastylive: "Testing probability of touch" (2016) https://www.tastylive.com/shows/options-jive/episodes/testing-probability-of-touch-11-22-2016 ; "Probability of touch: realistic expectations" https://tastylive.com/shows/market-measures/episodes/probability-of-touch-realistic-expectations-04-08-2016 ; puts vs calls https://www.tastylive.com/news-insights/probability-touch-pot-put-vs-call-options
- Reflection / probability of touch Q&A: https://quant.stackexchange.com/questions/235/probability-of-touching
- MAE/MFE (Sweeney 1997): https://audacity.capital/trading-guides/maximum-adverse-excursion/

Pine v6 (local mirror)
- `docsrc/jabez4jc_pinescriptv6/reference/time.md`: `time()` / `time_close()` with negative `bars_back` (−1 … −500) return expected future bar times; `hour(time, timezone)`, `dayofweek`, `str.format_time`.
- `docsrc/jabez4jc_pinescriptv6/concepts/sessions.md`: loop over `time_close(timeframe.period, session, bars_back = -i)` to find the session end.
- `docsrc/jabez4jc_pinescriptv6/writing_scripts/limitations.md`: 500 ms per loop per bar; total execution time; collections ≤ 100,000 elements.

Sibling studies: `study/ict_time.final.md` (TIME-2/3/4/6), `study/calib_ml.md`, `study/bias_dol.final.md` (REG-1),
`study/quant_regime.md`, `study/skeptic.md`.

Access notes: several publisher and course hosts (ocw.mit.edu, portfoliooptimizer.io, nber.org, sinica.edu.tw) were not
reachable from this session, and the Firecrawl web-search credits ran out mid-study; the affected claims are marked
"not re-verified" above.
