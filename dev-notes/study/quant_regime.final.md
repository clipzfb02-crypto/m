# Regime detection for the DOL engine: trend vs range vs breakout, and what it changes about which liquidity is taken (final, A + B combined)

Domain: market-regime classification (Kaufman efficiency ratio, ADX/DMI, Choppiness Index, Hurst exponent, variance ratio, volatility compression and expansion (NR4/NR7, Bollinger/TTM squeeze, ATR ratios), realised vs implied volatility, time-series momentum and short-term reversal), and exactly how a regime should modulate the engine's draw vector D, PoT drift, counter-draw logic and pool scoring.

Engine audited: `brief/baseline_v2.pine` (line numbers below; identical to `indicators/dol_engine.pine`).

**Authorship markers used throughout.**
- **[A✓]** researcher A's claim, re-checked by B (source re-opened, code re-read, or result replicated).
- **[A, CORRECTED]** A's claim with a factual, numeric or spec error fixed by B. The correction is stated.
- **[A, DOWNGRADED]** evidence grade lowered by B.
- **[A, not re-opened]** A's citation that B could not re-open (see the note under section 7). Treat its numbers as A's reading.
- **[B-NEW]** concept, test, statistic, source or proposal added by researcher B.

**Study code.** A: `study/quant_regime_tools/` (outputs `out_*.txt`). B: `study/quant_regime_b_tools/` (`blib.py`, `b_surface.py`, `b_side.py`, `b_rwrates.py`, outputs `out_surface_a05_<fam>.txt`, `out_surface_<fam>.txt`, `out_side_<fam>.txt`, `out_rwrates.txt`). Every number tagged **[A-test]** or **[B-test]** comes from them.

**Sibling studies referenced, not repeated:** `quant_pot.md` (QPOT-01..09), `bias_dol.final.md` (BIAS-1..8), `wyckoff_sd.final.md` (WYK-1..4), `ict_struct.final.md` (ICTS-1, B6), `ict_time.final.md` (TIME-1..8), `orderflow_micro.final.md` (OF-1..7), `amt_profile.final.md` (B7), `price_action.md` (PA).

---

## 0. Key findings (read this first)

1. **Trend/range regime labels are not a persistent state at DOL horizons.** [A✓]
   - ER(20), CHOP(14) and a rolling Hurst exponent on one window have about zero correlation with the same measure on the next non-overlapping window (ER −0.04..+0.01, CHOP −0.13..0.00, Hurst −0.08..+0.01 on 23 series; the sign-flip null gives the same). [A-test]
   - **[B-NEW] Exact noise floors on a driftless Gaussian random walk** (200,000 bars, 20 intrabar steps, with and without volatility clustering) [B-test, `out_rwrates.txt`]:
     - ER20 ≥ 0.40 on **15.7%** of bars (A's analytic ≈15% confirmed; mean ER20 = 0.225; ER20 ≥ 0.30 on 29%; ER20 < 0.15 on 40%).
     - ADX14 ≥ 25 on **38%** of bars (mean ADX 24.1; ≥ 20 on 59%; ≥ 40 on 7.5%).
     - CHOP14 mean **46.9** (A said "≈ 50"; corrected), ≤ 38.2 ("trending") on 21%, ≥ 61.8 ("choppy") on 7%.
     - VR-implied Hurst (q = 4, w = 96): mean 0.48, **SD 0.069**; > 0.55 on 12-16% of bars.
   - **Volatility state is persistent** (corr 0.49-0.80 between consecutive windows). [A✓]
   - Implication: a trend/range label describes the window that just ended. A volatility label forecasts the next one.
2. **The trend regime does not change WHICH side is taken beyond race geometry.** [A✓, extended]
   - A: adding signed ER, φ, φ³, EMA distance or +DI−−DI to the gambler's-ruin logit never improves out-of-sample (OOS) log-loss by more than 0.25%. [A-test]
   - **[B-NEW] The same holds for a higher-timeframe regime** (ER10 on completed HTF blocks: 1H for 5m, 4H for 15m, D for 1H/BTC, W for D). With-HTF-trend excess over geometry in HTF-efficient trends: 5m +0.7 ± 1.2 pp (null +2.7), 15m +2.3 ± 2.4 (null −3.3), 1H −2.4 ± 2.5 (null +1.7), BTC 1H +2.9 ± 1.4 (null +0.6), D +4.1 ± 3.5 (null −4.7). Nothing clears 2σ against its null. [B-test]
3. **"In a trend the draw continues" is mostly geometry.** In efficient trends (ER20 ≥ 0.40) price sits near the leading edge, so the nearer pool is the with-trend pool 76-82% of the time (null 78-83%). [A✓]
4. **Choosing the side by the engine-like structure vote D costs 9-12 pp of first-touch accuracy intraday and 5 pp daily.** [A✓, CORRECTED interpretation]
   - Geometry 0.645-0.706 vs D-first 0.550-0.652; hit within K drops 5-8 pp intraday, 3 pp daily. [A-test]
   - **Correction:** A wrote that an efficiency gate "recovers geometry within 0.2 pp". True, but the reason is that the gated D **disagrees with geometry on only 0.4-0.5% of races** (`out_dgate.txt`). The gate is, in practice, "D switched off". It does not show that D has skill in trends.
   - A's soft gate (D × g_E), which A's REG-3 spec used, is 0.2-0.8 pp *worse* than the hard gate (1H 0.635 vs 0.643). The final REG-3 uses the hard gate.
   - **[B-NEW] The other two D components are also null.** Displacement bars (engine rule, body ≥ 1.2 ATR, body/range ≥ 0.6) are followed by a symmetric ±1 ATR race in the displacement direction at 0.500 (5m), 0.484 (15m), 0.516 (BTC), 0.506 (D), with nulls 0.49-0.52. Only CME 1H shows 0.548 ± 0.015 vs null 0.509 (≈2σ, one cell of five). Sibling ICTS B6 found 51.3% (n 4,347). [B-test]
5. **PoT drift hurts in every regime, including efficient trends** (log-loss +1.2-4.0% with the engine's drift; drift only in "trend regime" does not rescue it). [A✓; agrees with QPOT-01 and BIAS-8]
6. **[A, CORRECTED] Volatility matters for reach, but the right fix is the distance unit, not volatility rows.** [B-test, `b_surface.py`, pool-touch events, 2-fold time split, partial pooling as in QPOT-03]
   - **The engine's ATR14-unit surface is miscalibrated by volatility state.** Hit minus predicted touch probability, compressed / normal / expanded tercile: 15m +3.7 / +1.7 / **−8.2 pp**; 1H +3.3 / −0.2 / **−5.5**; BTC 1H +3.0 / −0.7 / **−6.2**; 5m +0.8 / +0.4 / −2.0. This replicates sibling amt B7 (±6-8 pp). The displayed PoT and the EDGE baseline `pBase` share this bias.
   - **A horizon-matched unit fixes most of it.** Measuring surface distances in u = √(ATR14 · ATR100), a cheap forecast of volatility over the coming horizon (fast ATR mean-reverts toward slow), gives OOS log-loss −0.40% (5m), **−2.79% (15m)**, −0.45% (1H), **−1.21% (BTC)**. The expanded-tercile bias falls to −1.3..−3.2 pp.
   - **With NY time-of-day rows** (sibling TIME-2) the blended unit gives **−3.04% (5m), −5.82% (15m), −0.65% (1H), −1.23% (BTC)**, the best of 13 surface designs tested.
   - **Volatility-tercile rows (A's REG-1)** give only +0.27% (5m, worse), −0.64% (15m), −0.11% (1H), −0.50% (BTC), +0.12% (D). On top of the blended unit they add −0.23 to +0.36 pp (no consistent gain), and on top of time-of-day rows they **hurt** (15m −2.38% vs −4.06%).
   - **Trend-state rows** (ER sign, the analogue of the engine's `htfBias` key) never help: −0.02% to +0.41%.
   - Daily charts: nothing helps (vol rows +0.12%, blended unit +0.66%). Keep ATR14 and pooled rows there.
   - These effects are direction-free, so the sign-flip null reproduces them, as it should.
7. **Ranges do not make both sides more likely to be raided; volatility compression does** (distance-matched P(both) does not rise with low ER or high CHOP; compression raises it on 15m/1H). [A✓] In the engine this belongs in the surface (finding 6), not in a range bonus.
8. **Sweeps: no regime makes "raid holds → continuation, raid rejects → reversal" true** (0.497-0.510 intraday for both). [A✓]
   - **[B-NEW] Breakouts from compression do not continue either.** After the first trade-through of an NR7 bar's high or low (within 10 bars), the symmetric ±1 ATR race in the break direction is 0.482 ± 0.006 (5m; null 0.495), 0.502 (15m; null 0.479), 0.485 ± 0.011 (1H; null 0.509), 0.486 ± 0.008 (BTC; null 0.496), 0.515 (D; null 0.517). If anything, intraday NR7 breaks slightly fail. This agrees with the MNQ falsification study (Asia expansion bars reverse at the next bar, T = −10.96; ORB long T ≤ 1.50).
9. **[A, DOWNGRADED] The counter-trend pool handicap is weak and definition-dependent.**
   - A (chart-TF ER ≥ 0.40): counter-trend pools touched −6.7 ± 2.7 pp below a random level on 1H (null −1.5) and −6.7 ± 4.1 on D (null −1.7); 5m/15m ≈ 0. [A-test]
   - **[B-NEW]** With an HTF trend definition the effect does not replicate: 1H +2.0 ± 2.5 (null +2.2), 15m −2.2 ± 2.1 (null +4.4), 5m −0.3 ± 1.3 (null −3.2), BTC −3.9 ± 1.3 (null −1.2), D −1.2 ± 2.7 (null +4.0). [B-test]
   - That supports at most a mild multiplier (×0.85), scoped to efficient trends, and measured per chart. It does not support the current ×0.50 applied whenever |D| ≥ 0.35.
10. **Rolling Hurst / variance-ratio classifiers are noise at chartable windows** (SE of VR(4) on 96 bars ≈ 0.19, Hurst SD 0.069). [A✓ + B-test]
11. **External evidence points the same way at intraday horizons.** [A✓ with corrections; B-NEW additions]
    - Fast trend-following has collapsed since 2009 on small-tick contracts (equity index and FX futures), across ~100 futures; it survives on large-tick ones. These are *daily* signals (τ = 5-50 days). [A✓, verified: Kurth, Eisler, Rej, Bouchaud 2026, Table 1]
    - Trend vs reversion depends on time scale. **[A, CORRECTED]** The paper's abstract places the trending regime at "a few hours to a few years", not from 30 minutes: the linear term turns positive near 30 minutes but only beats tick-size reversion at a few hours. Below about 15-30 minutes *weak* trends revert while *strong* ones persist. Trends "tend to revert before they become statistically significant", which is exactly when a chart label such as ER ≥ 0.4 would switch on. (Safari & Schmidhuber 2025)
    - **[B-NEW]** Across five asset classes and 61 instruments, the *direction* sector of a multi-timescale coherence measure never exceeds its random-walk null in any instrument, while the *volatility* sector exceeds every null in every instrument (Le 2026). This is the cleanest external statement of this study's thesis: direction ≈ random walk, volatility structured.
    - **[B-NEW]** Intraday momentum is real but narrow: the last half-hour is predicted by the rest of the day across >60 futures 1974-2020, strongest when option dealers are short gamma, and it reverts over the next days (Baltussen, Da, Lammers, Martens 2021). The first half-hour predicts the last in 12 of 16 developed markets, more so when volatility is high and liquidity low (Li, Sakkas, Urquhart 2022). This is a session-timing effect (sibling TIME-9), not a trend regime.
    - **[B-NEW]** Serial correlation falls as trading volume rises (Campbell, Grossman, Wang 1993) and as predictable volatility rises (LeBaron 1992). Regime-conditional autocorrelation exists in the literature but is small, and it is not stable in sign across horizons: daily-scale trend profits are better in low volatility (Kurth et al.), while intraday session momentum is stronger on high-volatility days (Gao et al.; Li et al.).

**Design consequence (revised by B).**
- Fix the probability engine with the volatility *unit* and the clock, not with regime rows: a horizon-matched unit plus time-of-day rows (REG-1, built together with TIME-2; TIME-3's volatility clock supersedes the unit when it wins the per-chart scorecard).
- Stop letting D steer target choice without measured skill: hard efficiency gate as a legacy option, zero drift (REG-3, behind BIAS-2/ICTS-1).
- Keep a cheap two-axis classifier (efficiency, volatility) for honest display, the regime-split ledger and calibration auditing (REG-2), not as a forecasting input.
- Scope and soften the counter-draw penalty (REG-4); add a stop-run readout and an expansion alert (REG-5); treat breakouts and displacement as volatility events, not draw votes (REG-7).
- Do not add ADX/Hurst/CHOP thresholds, trend-regime drift, range bonuses, or breakout-continuation logic.

---

## 1. Concepts (precise definitions and parameters)

Notation: bar t has O, H, L, C. TR_t = max(H_t, C_{t−1}) − min(L_t, C_{t−1}). RMA = Wilder smoothing (α = 1/n). Every regime measure is computed on closed bars (≤ t) and used at the close of t.

### 1.1 Kaufman efficiency ratio (ER) [A✓]
- **Definition.** ER_n = |C_t − C_{t−n}| / Σ_{i=t−n+1..t} |C_i − C_{i−1}| ∈ [0, 1]. Signed: sER_n = (C_t − C_{t−n}) / Σ|ΔC| ∈ [−1, 1]. KAMA uses n = 10 and maps ER into a smoothing constant between fast = 2 and slow = 30 (Kaufman, *Trading Systems and Methods*; TA-Lib `ER`).
- **Thresholds are conventions, not Kaufman rules.** [B-NEW] Practitioners use ER ≥ 0.3 to 0.6 for "trend" and < 0.2-0.3 for "chop". B found no source in Kaufman giving a fixed cutoff; secondary sources state that baselines differ by market and timeframe and recommend reading ER against its own history.
- **Random-walk behaviour.** E|ΔC| = σ√(2/π) and |ΣΔC| = σ√n|Z|, so ER_n ≈ |Z|·√(π/(2n)). For n = 20: mean ≈ 0.22, P(ER ≥ 0.40) ≈ P(|Z| ≥ 1.43) ≈ 15%. [A✓] Simulation: mean 0.225, P ≥ 0.40 = 15.7%, P ≥ 0.30 = 29%, P ≥ 0.60 = 2.7%, P < 0.15 = 40%. Volatility clustering barely changes this (15.1%). The sign-flip null on real bar shapes gives 18-22% intraday. [B-test, A-test]
- **Edge cases.** Guard a zero path (flat data). Use close-to-close changes so gaps count. ER is direction-free; use sER for direction.

### 1.2 ADX / DMI (Wilder 1978) [A✓]
- **Definition.** +DM = H_t − H_{t−1} if that is > L_{t−1} − L_t and > 0, else 0; −DM mirrors it. ±DI = 100·RMA(±DM, 14)/RMA(TR, 14). DX = 100·|+DI − −DI|/(+DI + −DI). ADX = RMA(DX, 14). ADX > 25 = trend, < 20 = no trend; +DI > −DI gives the direction.
- **Noise floor.** [B-NEW] ADX ≥ 25 on 38% of pure random-walk bars (mean 24.1). ADX retains corr ≈ 0.22 over 28 bars even on a random walk: its double smoothing creates persistence that is not information.
- **Evidence for filtering.**
  - Donchian + ADX filter adds no value (oxfordstrat) [A, not re-opened].
  - Gains from skipping chop, not from better trades in trends (algolab 2026 blog) [A, not re-opened].
  - [B-NEW] Gurrib (2018, *Banks and Bank Systems*): an ADX + Parabolic SAR system on USD currency pairs, weekly and monthly 2000-2018, had "a high proportion of negative returns" with low Sharpe and Sortino ratios; weak.

### 1.3 Choppiness Index (E. W. Dreiss) [A, CORRECTED]
- **Definition.** CHOP_n = 100·log10(Σ_n TR / (HH_n − LL_n)) / log10(n), n = 14. > 61.8 = choppy, < 38.2 = trending (Fibonacci conventions).
- **Random-walk value.** For continuous Brownian motion ΣTR/(HH−LL) ≈ √n, so CHOP ≈ 50. **Correction:** on discrete bars the simulated mean is 46.9, and 21% of random-walk bars read "trending" (≤ 38.2) while 7% read "choppy" (≥ 61.8). [B-test]
- **Engine relation.** `coilScore` (886-891) is a CHOP-like overlap ratio Σrange_20 / range_20, mapped as (x − 2)/4, feeding the density pillar (683, 687).

### 1.4 Hurst exponent and variance ratio [A✓]
- **Hurst H.** Var(r_q) ∝ q^{2H}. H = 0.5 random walk, > 0.5 persistent, < 0.5 anti-persistent. Estimators: R/S, DFA, generalised Hurst, aggregated variance / VR slope.
- **Variance ratio (Lo & MacKinlay 1988).** VR(q) = Var(q-bar returns)/(q·Var(1-bar)). VR(q) ≈ q^{2H−1}, so H ≈ 0.5 + ln VR/(2 ln q). Homoskedastic asymptotic Var(VR) = 2(2q−1)(q−1)/(3qT): for q = 4, T = 96 the SE ≈ 0.19 (arithmetic re-checked), Hurst SE ≈ 0.07 (simulated SD 0.069). Use the heteroskedasticity-robust z*; the homoskedastic z over-rejects at 10-12% under GARCH (Portnaya 2026). [B-NEW detail]
- **Behaviour.** The rolling VR-Hurst averages 0.47-0.48 on real and null data, labels a random walk H > 0.55 on 12-22% of bars, and has next-window correlation ≈ 0. [A-test, B-test]

### 1.5 Volatility compression → expansion [A✓, extended]
- **NR4/NR7 (Crabel 1990).** Today's range is the smallest of the last 4/7 bars. Inside bar: H_t ≤ H_{t−1} and L_t ≥ L_{t−1}. Trade the break of the narrow bar.
- **Bollinger squeeze.** BandWidth = 4σ_20/SMA_20 at a ~120-bar low or low percentile.
- **TTM Squeeze (Carter).** "On" when BB(20, 2σ) is inside KC(20, 1.5·ATR) ⇔ 2σ_20 < 1.5·ATR_20 with a common basis. "Fires" when it exits. A momentum histogram supplies direction.
- **ATR ratio.** volr = ATR(5)/ATR(100), or ln(ATR_fast/ATR_slow) z-scored against its own EWMA.
- **What is true.** Volatility clusters and mean-reverts (HAR, Corsi 2009). After compression the *absolute* next range is smaller than average, but the next H bars travel more *ATR(14) units* than average; expansion is the mirror image. [A✓]
- **What is not supported.** Any directional content: squeeze/NR states add nothing to which-side-first [A-test]; NR7 breaks do not continue [B-test]; no peer-reviewed or out-of-sample study of squeeze direction was found [B-NEW]; Bulkowski's NR7 statistics on 1,201 stocks (1990-2013) show a 46-47% failure rate in bull markets for both breakout directions [B-NEW].

### 1.6 Horizon-matched volatility unit (HAR logic) [B-NEW]
- **Problem.** The empirical surface stores excursions over H bars divided by ATR14 at the window start (line 1528). ATR14 is a 14-bar measure. Volatility mean-reverts, so ATR14 is a biased forecast of the average bar range over the next H = 30 bars: too high after expansion and too low after compression. Every distance "in ATR" inherits that bias. This is the mechanism behind the volatility-state effect that A measured.
- **Fix.** Use a forecast of forward volatility as the unit. The HAR model (Corsi 2009) forecasts realised volatility as a sum of daily, weekly and monthly components. A two-component geometric blend is the cheapest version: u = ATR14^a · ATR100^(1−a). With a = 0.5, u = √(ATR14 · ATR100).
- **Measured** [B-test]: the fixed a = 0.5 is robust intraday; the in-sample best a varies (≈0 on 15m, 0.25-0.75 on 1H/BTC, 0.75 on 5m). On daily bars the blend hurts (+0.66%) and ATR14 stays.
- **Relation to siblings.** QPOT-02 (vol-time horizon variance) and TIME-3 (NY-keyed volatility clock) are the principled versions of the same idea. The blended unit is the effort-S stand-in until they land.

### 1.7 Realised vs implied volatility (variance risk premium) [A✓]
- VRP = IV² − E[RV²]; RV/IV > 1 marks stress. Predicts index returns at monthly-quarterly horizons (Bollerslev, Tauchen & Zhou 2009). Not documented at intraday horizons. Pine needs an index-specific implied-vol symbol (CBOE:VIX), so it is not generic.

### 1.8 Time-series momentum and short-term reversal [A✓ with corrections]
- **TSMOM (Moskowitz, Ooi & Pedersen 2012).** sign(past 12-month excess return) predicts the next month across 58 futures; persists 1-12 months, partly reverses after a year.
- **Fast trend after 2009 (Kurth et al. 2026).** EWM-τ-4τ daily signals, ~100 futures, 1995-2025. Sharpe 1995-2009 → 2009-2025: τ = 5: 0.84 ± 0.27 → 0.12 ± 0.24; τ = 10: 0.83 → 0.22; τ = 20: 0.79 → 0.27; τ = 50: 0.70 → 0.40. Small-tick (equity index, FX) "completely degraded"; large-tick Sharpe 1.0-1.2. Trends are more profitable in low-volatility periods (LeBaron effect), and the break is a phenomenon of large-return days only. [verified]
- **Trend strength by scale (Safari & Schmidhuber 2025).** φ_T = trend t-statistic. Next return ≈ a + bφ + cφ³ (plus a quintic term and a tick-size discontinuity below 1 hour). [A, CORRECTED]: below ~15-30 min weak trends revert *and strong ones persist* (b < 0, c > 0); from ~30 min the linear term turns positive; from a few hours to years weak trends persist and strong ones revert (b > 0, c < 0). Coefficients are small (Table 6: b = +0.132% ± 0.046, c = −0.039% ± 0.014 for longer intraday horizons). [verified]
- **Intraday momentum.** [A✓] Gao, Han, Li, Zhou (2018): SPY first half-hour → last half-hour, R² 1.6% in-sample, 1.2% OOS; stronger on volatile, high-volume, recession days. [B-NEW] Baltussen et al. (2021): >60 futures 1974-2020; tied to negative-gamma hedging; reverts over the next days. Li, Sakkas & Urquhart (2022): 12 of 16 developed markets; stronger with high volatility and low liquidity.
- **Practical limit.** [A, CORRECTED numbers] On MNQ 5-minute RTH bars (947 days, Dec 2021-Aug 2025), 0 of 14 OHLCV signal families pass walk-forward criteria. ORB long T = 1.17 (bar+1) and 1.50 (bar+15), not 0.88. **[B-NEW]** The "volatility-regime-conditioned classifier" family also failed, and Asia-session expansion bars *reverse* (T = −10.96 at bar+1) (Mesfin 2026).
- **Short-term reversal.** Sub-hour reversal from bid-ask bounce and temporary imbalance (Heston, Korajczyk & Sadka 2010). [A, CORRECTED] SPY's lag-1 autocorrelation of −0.081 (z = −7.39) is magnitude-driven (sign test p = 0.11) in **daily** data 1993-2026, not intraday; mean reversion is confined to exchange-traded equity baskets and sovereign bonds; credit, commodities, FX and crypto are random-walk-like (Portnaya 2026).
- **Volume and volatility conditioning.** [B-NEW] Daily autocorrelation declines with volume (Campbell, Grossman & Wang 1993). Serial correlation is lower when volatility is high (LeBaron 1992); intraday, predictable volatility lowers it and unexpected volatility raises it (Bianco, Corsi & Renò 2008).

### 1.9 Statistical regime models [A✓, extended]
- **Markov switching (Hamilton 1989).** Latent states with their own mean, variance and transition matrix. Extensions: volatility MSR + adaptive MA for four trend × volatility states (Pomorski & Gorse 2022) [A, not re-opened].
- **[B-NEW] Statistical jump models.** Nystrup, Kolm & Lindström (2020, *J. Financial Data Science* 2(3)) classify persistent states online with a jump penalty, using realised intraday *volatility* features. The states that persist are volatility states. This agrees with finding 1.
- **Evidence.** In-sample segmentations convince; no documented out-of-sample intraday directional value. A 2-state forward filter is feasible in Pine but adds nothing over a volatility z-score and ER.

### 1.10 Displacement and expansion bars as continuation signals [B-NEW]
- **Engine definition** (897-904): `dispUp` = bull bar with body ≥ 1.2·ATR[1] and body/range ≥ 0.6, or a two-bar leg. The direction decays with half-life 12 into `mV`, 20% of D (1893-1894).
- **Claim.** A displacement bar starts a move that continues in its direction (a "breakout regime").
- **Test result.** Symmetric ±1 ATR race in the displacement direction: 0.484-0.516 on 4 of 5 families, matching the null; CME 1H 0.548 ± 0.015 vs null 0.509 (one cell). [B-test] ICTS B6: 51.3% (n 4,347). MNQ Asia expansion bars reverse next bar.

### 1.11 The DOL-specific regime claims (what traders say) [A✓]
- **C1.** "In trends, opposite-side liquidity holds and the draw continues." The engine encodes this as D-first selection, the Draw pillar (weight 30) and the ×0.5 counter-draw penalty.
- **C2.** "In ranges, both sides get raided."
- **C3.** "Compression precedes expansion; trade the break."
- **C4.** "A raid that holds is continuation; a raid that rejects is reversal" (`liqEvt`, 1579-1582).
- **C5 [B-NEW].** "A displacement / expansion bar starts a draw in its direction" (`mV`, 1893).

---

## 2. Evidence

### 2.1 Data and method

| Family | A's series | B's series | Horizon K |
|---|---|---|---|
| 1H | ES, RTY, YM, CL (CME 2025-03 → 2026-04); NQ, GC, EURUSD (sibling hourly ≈2024-11 → 2026-11); EURUSD 1H 2017-18 | ES, NQ, GC, CL, RTY, YM CME 1H (2025-03 → 2026-04, ≈6k bars each) | 30 |
| BTC 1H [B-NEW] | — | BTCUSD 1H 2017-01 → 2025-01 (70,273 bars) | 30 |
| 15m / 5m | six CME futures resampled from 1-minute, 2026-01-20 → 2026-04-15 | same | 30 |
| D | S&P 500, NASDAQ (1999-2018), GOOG (2004-2013) | same | 10 |

- **Pools.** Nearest unswept confirmed 5-bar pivot above and below, swept on a strict trade-through as in the engine (`touched`, 623). A: within 0.25-4 ATR. B's surface test: 0.25-6 ATR.
- **Geometry.** P(up first) = b/(a+b), the driftless gambler's ruin (`f_race`, 447-464).
- **Null.** Sign-flip series (`rlib.null_series`): each bar is rebuilt from the previous synthetic close with its own range and body, mirrored with probability ½. It keeps bar ranges, timing and volatility clustering, and destroys directional dependence. A *directional* effect must exceed the null. A *volatility or clock* effect should be reproduced by the null.
- **OOS.** A: 2-fold time split, logit-geometry baseline vs + regime feature. B (surface): survival surfaces fitted on one half, scored on the other half's pool-touch events, both folds; cells shrunk toward the pooled surface with nE = n/(0.6K) and m = 30, as the engine and QPOT-03 do.
- **SEs.** Cluster-robust by 100-bar block × series.

### 2.2 Regime labels are not persistent states (A: `regime_persist.py`) [A✓]

| Measure | 5m real / null | 15m | 1H | D |
|---|---|---|---|---|
| P(ER20 ≥ 0.40) | 0.170 / 0.183 | 0.198 / 0.188 | 0.215 / 0.219 | 0.187 / 0.137 |
| P(ADX ≥ 25) | 0.456 / 0.433 | 0.495 / 0.433 | 0.499 / 0.485 | 0.418 / 0.352 |
| P(CHOP ≤ 38.2) | 0.144 / 0.152 | 0.156 / 0.148 | 0.193 / 0.184 | 0.198 / 0.142 |
| P(Hurst > 0.55) | 0.186 / 0.212 | 0.188 / 0.219 | 0.188 / 0.205 | 0.084 / 0.136 |
| corr ER20(t), ER20(t+20) | −0.011 / +0.012 | +0.006 / −0.028 | −0.022 / +0.025 | −0.044 / +0.010 |
| corr CHOP(t), CHOP(t+14) | −0.002 / +0.049 | −0.047 / +0.022 | −0.023 / +0.016 | −0.132 / +0.011 |
| corr Hurst(t), Hurst(t+96) | −0.014 / −0.020 | −0.082 / −0.044 | +0.014 / −0.006 | −0.041 / −0.080 |
| corr ln(ATR14/ATR100)(t, t+14) | 0.80 / 0.80 | 0.60 / 0.62 | 0.49 / 0.48 | 0.76 / 0.77 |

**[B-NEW] Random-walk noise floors** (Gaussian, 200k bars, 20 intrabar steps; second number with GARCH-like clustering):

| Statistic | Gaussian RW | RW + vol clustering |
|---|---|---|
| ER20 mean / P(≥ .30) / P(≥ .40) / P(≥ .60) / P(< .15) | 0.225 / 0.292 / 0.157 / 0.027 / 0.399 | 0.224 / 0.287 / 0.151 / 0.027 / 0.397 |
| ADX14 mean / P(≥ 20) / P(≥ 25) / P(≥ 40) | 24.1 / 0.594 / 0.380 / 0.075 | 24.0 / 0.596 / 0.380 / 0.071 |
| CHOP14 mean / P(≤ 38.2) / P(≥ 61.8) | 46.9 / 0.207 / 0.070 | 47.1 / 0.203 / 0.073 |
| VR-Hurst (q 4, w 96) mean / SD / P(> .55) | 0.482 / 0.069 / 0.121 | 0.481 / 0.069 / 0.160 |
| corr ER20(t, t+20) / corr ADX(t, t+28) | 0.003 / 0.223 | −0.002 / 0.213 |

### 2.3 Which side is taken first (A: `regime_study.py`) [A✓]

OOS log-loss change vs logit(geometry); negative = helps.

| Feature added | 1H | 5m | 15m | D |
|---|---|---|---|---|
| sER20 | +0.60% | +0.01% | +0.66% | +0.34% |
| φ24, φ24³ | +0.21% | +0.08% | +0.26% | +1.00% |
| EMA50 distance | +0.23% | −0.10% | +0.33% | −0.13% |
| (+DI − −DI)/50 | +0.30% | −0.24% | −0.25% | −0.11% |
| same features on the null | −0.06..+0.03% | −0.00..+0.02% | −0.06..+0.03% | −0.28..+0.09% |

With-trend excess (y − p_geo)·sign(sER20) by chart-TF gate: only 1H ER ≥ 0.4 clears 2σ (+0.061 ± 0.025 vs null −0.004), out of ~20 gates × 4 families.

**[B-NEW] HTF efficiency regime** (`b_side.py` T3; ER10 on the last completed HTF block):

| | 5m (HTF = 1H) | 15m (4H) | 1H (D) | BTC 1H (D) | D (W) |
|---|---|---|---|---|---|
| with-HTF-trend excess, HTF ER ≥ 0.4 (real / null) | +0.007 ± 0.012 / +0.027 | +0.023 ± 0.024 / −0.033 | −0.024 ± 0.025 / +0.017 | +0.029 ± 0.014 / +0.006 | +0.041 ± 0.035 / −0.047 |
| same, HTF not efficient | +0.003 / +0.012 | +0.012 / +0.040 | −0.003 / −0.021 | −0.002 / −0.004 | +0.007 / −0.012 |
| n (efficient) | 7,145 | 2,234 | 1,776 | 6,295 | 486 |

### 2.4 Engine-like side selection (A: `regime_dgate.py`) [A✓, CORRECTED reading]

D proxy = 0.5·HTF + 0.3·STF + 0.2·chart internal pivot bias (engine `sV`, 1892), gate 0.35.

| Rule | 5m acc / hit≤K | 15m | 1H | D | differs from geometry on |
|---|---|---|---|---|---|
| Geometry | **0.672 / 0.661** | **0.666 / 0.643** | **0.645 / 0.655** | **0.706 / 0.486** | — |
| D-first (engine today) | 0.556 / 0.585 | 0.580 / 0.589 | 0.550 / 0.590 | 0.652 / 0.452 | 19-38% |
| D only if ER20 ≥ 0.40 and agrees (hard gate) | 0.671 / 0.661 | 0.665 / 0.642 | 0.643 / 0.654 | 0.706 / 0.486 | **0.3-0.5%** |
| D × soft gate g_E | 0.668 / 0.659 | 0.663 / 0.642 | 0.635 / 0.648 | 0.705 / 0.486 | 1.1-2.1% |
| D only if ADX ≥ 25 | 0.637 / 0.640 | 0.640 / 0.632 | 0.615 / 0.635 | 0.700 / 0.482 | 6-12% |

- [B] **Reading correction.** The hard gate matches geometry *because it almost never acts*. Where it does act, it is no better than geometry. It is a safe legacy option, not evidence that D has skill in trends.
- The null gives the same ordering (geometry 0.657-0.701; D-first 0.520-0.592). The loss is mechanical: D-first chooses the farther pool.

### 2.5 PoT drift by regime (A: `regime_engine.py` (b)) [A✓]

| Family | All bars: LL drift / none | ER ≥ 0.40: drift / none | ER < 0.15: drift / none |
|---|---|---|---|
| 5m | 0.6693 / **0.6544** | 0.6943 / **0.6689** | 0.6708 / **0.6576** |
| 15m | 0.6826 / **0.6691** | 0.6862 / **0.6527** | 0.6661 / **0.6601** |
| 1H | 0.6641 / **0.6389** | 0.6136 / **0.5902** | 0.6613 / **0.6435** |
| D | 0.5698 / **0.5631** | 0.5036 / 0.5033 | 0.5859 / **0.5822** |

### 2.6 How the empirical reach surface should be keyed and scaled [B-NEW] (`b_surface.py`, fixed a = 0.5)

OOS log-loss change vs the pooled ATR14 surface (M0 = the engine with an uninformative key). Pool-touch events: 81k (5m), 26k (15m), 28k (1H), 63k (BTC), 9k (D).

| Model | 5m | 15m | 1H | BTC 1H | D |
|---|---|---|---|---|---|
| M1 vol-tercile rows (A's REG-1) | +0.27% | −0.64% | −0.11% | −0.50% | +0.12% |
| M2 deseasonalised vol rows | −0.04% | +0.30% | +0.29% | −0.45% | — |
| **M3 blended unit √(ATR14·ATR100)** | −0.40% | **−2.79%** | −0.45% | **−1.21%** | +0.66% |
| M5 NY 3-hour time-of-day rows (TIME-2) | −2.27% | −4.06% | −0.48% | −0.04% | — |
| M6 tod × vol rows | −1.83% | −2.38% | −0.30% | −0.51% | — |
| **M8 blended unit + tod rows** | **−3.04%** | **−5.82%** | **−0.65%** | **−1.23%** | — |
| M10 blended unit + vol rows | −0.63% | −2.61% | −0.09% | −1.11% | −0.09% |
| M11 blended unit + tod × vol | −2.48% | −4.37% | −0.45% | −1.17% | — |
| M12 trend-state rows (ER sign; the `htfBias` analogue) | −0.01% | −0.02% | +0.41% | +0.02% | −0.00% |
| M9n vol rows recalibrated + NR7 flag (vs recalibrated without) | −0.03 pp | −0.19 pp | −0.05 pp | −0.02 pp | +0.15 pp |

Null (same models): M3 −0.14 / −2.90 / −0.80 / −0.73 / +1.11%; M5 −2.55 / −4.65 / −0.73 / −0.04%; M8 −3.17 / −6.51 / −1.21 / −0.76%. These effects are direction-free, so the null reproduces them.

Calibration by volatility tercile (hit minus predicted, pp; compressed / normal / expanded):

| Model | 5m | 15m | 1H | BTC 1H |
|---|---|---|---|---|
| M0 engine-like ATR14 pooled | +0.8 / +0.4 / −2.0 | +3.7 / +1.7 / **−8.2** | +3.3 / −0.2 / **−5.5** | +3.0 / −0.7 / **−6.2** |
| M1 vol rows | +0.0 / −0.5 / −0.3 | +1.0 / +0.6 / −4.1 | +0.3 / +0.2 / −2.4 | −1.0 / −0.9 / −1.6 |
| M3 blended unit | −5.1 / +0.5 / +3.8 | −1.0 / +1.2 / −3.2 | −0.5 / −0.3 / −1.3 | −1.0 / −1.1 / −2.3 |
| M8 blended unit + tod | −2.3 / −0.5 / +1.1 | −0.8 / +0.2 / −3.1 | −0.9 / −0.3 / −0.8 | −1.1 / −1.1 / −2.2 |

Reading:
- The bias A and amt B7 found is real and large in the engine as built (up to −8 pp in expanded volatility).
- The blended unit removes most of it on 15m/1H/BTC. On 5m it over-corrects without time-of-day rows (compressed −5.1 pp), so it should ship with TIME-2's rows and QPOT-04's recalibration.
- Vol rows calibrate the tercile means by construction but lose on log-loss to the unit, and they dilute samples when combined with time-of-day rows.
- The in-sample best exponent a varied by family (15m ≈ 0, 5m ≈ 0.75); a = 0.5 is the robust default. This is a stand-in for QPOT-02 / TIME-3.

### 2.7 Both sides, reach and pool magnetism by regime (A: O2, O4, (c)) [A✓]

P(both pools taken within K), OOS log-loss change from one regime feature:

| Feature | 1H real / null | 5m | 15m | D |
|---|---|---|---|---|
| ER20 | −0.00% / +0.00% | −0.01% / +0.00% | +0.00% / +0.03% | +1.25% / −0.05% |
| CHOP | −0.24% / −0.01% | +0.01% / +0.04% | −0.05% / −0.20% | +3.15% / +0.17% |
| ATR5/ATR100 | **−0.97% / −1.05%** | +0.06% / −0.15% | **−2.95% / −1.54%** | +0.20% / +0.63% |

- Reach ≥ 3 ATR within K by ATR5/ATR100 tercile: 1H 0.50 / 0.43 / 0.39; 15m 0.46 / 0.45 / 0.33; 5m flat. ER, CHOP, ADX, Hurst flat (|ΔLL| ≤ 0.17%).
- Pool touch minus random level: CHOP ≥ 61.8 gives no range magnetism (−0.005 / −0.019 / −0.023 / +0.015 vs null similar). Pools printed in coiled windows: −0.005..−0.018 (null −0.002..−0.020); no support for `coilScore` (agrees with WYK-1).
- Counter-trend pools in chart-TF efficient trends: 1H −0.067 ± 0.027 (null −0.015), D −0.067 ± 0.041 (null −0.017), 5m/15m ≈ 0. **[B-NEW]** With the HTF-trend definition: 5m −0.003 ± 0.013 (null −0.032), 15m −0.022 ± 0.021 (null +0.044), 1H +0.020 ± 0.025 (null +0.022), BTC −0.039 ± 0.013 (null −0.012), D −0.012 ± 0.027 (null +0.040).

### 2.8 After a sweep, a displacement, or a compression break (A: O3; B: T4, T5)

Symmetric ±1 ATR race (martingale = 0.5); real (null):

| Event | 5m | 15m | 1H | BTC 1H | D |
|---|---|---|---|---|---|
| sweep, hold (close beyond) [A] | 0.507 | 0.508 | 0.497 | — | 0.556 |
| sweep, reject (close back inside) [A] | 0.510 | 0.510 | 0.509 | — | 0.516 |
| sweep aligned with efficient trend [A] | 0.538 ± 0.014 (0.487) | 0.542 (0.538) | 0.521 (0.514) | — | 0.465 (0.472) |
| **displacement bar, in its direction [B]** | 0.500 ± 0.009 (0.490) | 0.484 ± 0.016 (0.506) | 0.548 ± 0.015 (0.509) | 0.516 ± 0.011 (0.516) | 0.506 ± 0.023 (0.499) |
| displacement, nearest-pool excess over geometry [B] | −0.012 (−0.011) | +0.018 (+0.039) | +0.008 (+0.030) | +0.016 (+0.004) | +0.091 ± 0.039 (+0.014), n 105 |
| **NR7 break, in the break direction [B]** | 0.482 ± 0.006 (0.495) | 0.502 ± 0.012 (0.479) | 0.485 ± 0.011 (0.509) | 0.486 ± 0.008 (0.496) | 0.515 ± 0.018 (0.517) |
| n (displacement / NR7) | 2,983 / 6,953 | 971 / 2,135 | 1,113 / 2,328 | 2,025 / 4,400 | 439 / 681 |

### 2.9 External evidence table

| # | Claim | Source / data | Result | Grade | Status |
|---|---|---|---|---|---|
| R1 | Trend vs reversion by scale | Safari & Schmidhuber 2025, arXiv 2501.16772; 14 y futures ticks, 30 y daily, monthly since 1692 | Reversion below ~15-30 min (strong trends persist there); trending regime from a few hours to a few years; weak persist, strong revert; small coefficients; trends revert before becoming significant | moderate (large data, tiny effects) | A✓, time-scale wording CORRECTED |
| R2 | Death of short-term trend on small-tick contracts | Kurth, Eisler, Rej, Bouchaud 2026, arXiv 2607.01550; ~100 futures 1995-2025 | Sharpe 0.84/0.83/0.79/0.70 → 0.12/0.22/0.27/0.40 (τ 5/10/20/50 d); small-tick ≈ 0; large-tick 1.0-1.2; better in low vol | strong (daily signals) | A✓ verified |
| R3 | TSMOM | Moskowitz, Ooi, Pedersen 2012, JFE 104(2); 58 futures | 1-12 month persistence | strong (outside horizon) | A✓ |
| R4 | Intraday momentum, SPY | Gao, Han, Li, Zhou 2018, JFE 129(2) | R² 1.6% IS, 1.2% OOS; stronger on volatile, high-volume days | moderate | A✓ verified |
| R5 | OHLCV intraday signals fail on MNQ | Mesfin 2026, arXiv 2605.04004; 947 RTH days 5-min | 0/14 families pass; ORB long T 1.17-1.50; vol-regime classifier family fails; Asia expansion bars reverse (T −10.96) | moderate | A, CORRECTED (T) + B-NEW details |
| R6 | Foundation-model forecasts at 5-120 min | Upadhyay 2026, arXiv 2611.12141; ES/NQ, preregistered | 0/160 cells beat no-change; sign-randomised null reproduces ~95% of within-day RankIC; the authors say an economic edge cannot be ruled out | moderate (about TSFMs + ridge, not regime rules) | A, scope CORRECTED |
| R7 | Lag-1 reversal is magnitude, not sign | Portnaya 2026, arXiv 2606.29591; SPY daily 1993-2026 + 21 assets | ρ(1) = −0.0806 (z −7.39), sign test p 0.11; commodities, FX, crypto random-walk-like | moderate (daily/weekly, not intraday) | A, horizon CORRECTED |
| R8 | Direction vs volatility structure | Le 2026, arXiv 2610.11028; 61 instruments, 5 asset classes | VR test cannot reject RW for most; direction sector never exceeds RW null; volatility sector exceeds every null in every instrument | moderate | A✓, B-NEW emphasis |
| R9 | LeBaron effect | LeBaron 1992, J. Business 65(2); Bianco, Corsi, Renò 2008, arXiv 0810.4912 | serial correlation falls with (predictable) volatility | moderate | A✓ + B-NEW |
| R10 | Weekly index autocorrelation | Lo & MacKinlay 1988, RFS | equal-weighted weekly AC 0.30 (1962-85) | strong (historical, weekly) | A |
| R11 | Hurst estimation bias / variance | Kristoufek 2012; Barunik & Kristoufek 2012; Bartolozzi et al. 2007 | R/S biased; estimator variance large; local H scale-dependent | strong (methodological) | A, not re-opened; B's simulation agrees (SD 0.069) |
| R12 | ADX filter | oxfordstrat; algolab 2026; **Gurrib 2018** | no added value / gains only from skipping chop / high share of negative returns | weak | A, not re-opened + B-NEW |
| R13 | VVG regime days (MNQ) | arXiv 2605.11423 | 4.4% of sessions; 77.6% reverse from intraday peak | weak-moderate | A, not re-opened |
| R14 | AMD direction = daily trend | Taylor 2026 via `ict_struct.md` | aligned 62-71% (NQ 15m, N 484) | moderate; part may be geometry | A, not re-opened |
| R15 | Volatility persistence | Corsi 2009 HAR; rough-HAR 2026 | strong persistence across horizons | strong | A✓ |
| R16 | NR7 | sibling `bias_dol` 2.8; **Bulkowski (thepatternsite), 1,201 stocks 1990-2013** | next range > median only 26-45%; 46-47% failure both directions in bull markets | moderate (magnitude), none (direction) | A + B-NEW |
| R17 | Vol-state split of the PoT surface | QPOT-03 | lower LL on 6/6 symbols | moderate | A; **B: superseded by the unit fix (2.6)** |
| R18 | Intraday momentum, >60 futures, gamma | **Baltussen, Da, Lammers, Martens 2021, JFE 142(1)** | last 30 min predicted by rest of day; present when dealer gamma negative; reverts over next days | strong (session effect) | B-NEW |
| R19 | Intraday TSMOM, 16 markets | **Li, Sakkas, Urquhart 2022, J. Financial Markets 57** | significant in 12/16; stronger with high vol, low liquidity | moderate-strong | B-NEW |
| R20 | Volume and serial correlation | **Campbell, Grossman, Wang 1993, QJE 108(4)** | daily autocorrelation declines with volume | strong (daily) | B-NEW |
| R21 | Persistent online regime classification | **Nystrup, Kolm, Lindström 2020, JFDS 2(3)** | jump models with volatility features give persistent states in and out of sample | moderate (volatility states) | B-NEW |
| R22 | ORB on crude oil | **Holmberg, Lönnbark, Lundström 2013, FRL 10(1)** | ORB returns significantly above zero, success rate above a fair game | weak-moderate (one market, older sample) | B-NEW |
| R23 | Bollinger squeeze direction | practitioner sources (StockCharts, LuxAlgo) | direction-neutral by design; no peer-reviewed directional test found | none (direction) | B-NEW |

---

## 3. Engine gap analysis (baseline_v2.pine, line refs re-checked by B)

| Concept | Status | Where | What the engine does / what differs |
|---|---|---|---|
| Explicit regime classifier | **missing** [A✓] | — | No ER, ADX, CHOP, Hurst or squeeze state. The only "regime" is `htfBias` (−1/0/+1), used as the surface row (1060-1062, 1284-1301, 1530-1532). |
| Empirical PoT surface **key** | **partial / wrong key** [A✓] | 1060-1062; `f_empPoT` 1284-1301 (`r = side==1 ? bias+1 : 1−bias`); calls 1307, 1318; `f_reachD` calls 2112-2115 | Trend key carries no information (M12: −0.02..+0.41%). Time of day does (M5, TIME-2). Vol rows add little once the unit is fixed (2.6). |
| Empirical PoT surface **unit** [B-NEW] | **present, biased** | step 0: `aH = atr[H]` 1528, bumps 1531-1532; queries `d / atr` 1307, 1318; reach bands `reachU50 * atr` 2195-2199; reach class `dAtr` 2236, `dA` 2352 | ATR14 at the window start is a biased forecast of forward volatility. Displayed PoT and `pBase` are off by up to −8 pp in expanded volatility (2.6; amt B7). |
| EDGE baseline `pBase` [B-NEW] | **biased** | `f_potBase` 1314-1322; `f_openTrial` 1426-1431 | Uses the same surface, so EDGE inherits the volatility bias: picks made in compressed tape look like edge, picks in expanded tape look like no edge. |
| Proximity "reach" | **partial** [A✓] | 665 (`f_pot(dist, sig, mu * this.side, potH)`); `evaluate` called at 1948 with `nz(potMu)` | Analytic with drift; ignores the empirical surface. **[B: A's REG-1 fix as written is a forward reference]**: `evaluate` is declared at 661, `f_potModel` at 1303 and `sUp/sDn` at 1061. The method cannot call `f_potModel`. Pass the value in (REG-1 spec). |
| PoT drift | **present, wrong** [A✓] | `potMu` 917 (`driftW` 0.5, 185); 665; `f_invalidation` 1361-1363; 2067; 2184 | Drift worsens log-loss in every regime (2.5). |
| Draw vector D | **present, wrong use** [A✓] | 1891-1895 (`sV` 0.5·HTF + 0.3·STF + 0.2·exe internal; `mV`; `liqEvt`); weights 155-157 | D gates selection (`dirSide` 1895 → `elig` 1975), sets the Draw pillar (`this.draw` 691, weight 30 at 145) and the counter multiplier (692-693), whenever \|D\| ≥ 0.35 in any regime. D-first loses 9-12 pp (2.4). |
| Displacement term `mV` [B-NEW] | **present, null** | 897-904 (`dispUp/dispDn`), 1536-1541, 1893 (`wM` 0.20, 156) | Displacement continuation ≈ 0.50 on 4 of 5 families (2.8); ICTS B6 51.3%. |
| Raid sign `liqEvt` | **present, wrong** [A✓] | 1579-1582 | Hold vs reject identical intraday (2.8). Owned by BIAS-4 / ICT-9. |
| Counter-draw penalty | **present, mis-scoped** [A✓] | 692-693 (`ctrMult` 0.50, 162); `activeCtr` 2029; "⚠ COUNTER-DRAW" 2237; `ctrHold` 2001 | Applied whenever \|D\| ≥ dGate. Evidence for any counter-trend handicap is weak and definition-dependent (2.7). |
| Draw Flip alert | present | flip logic 1896-1898; alert 2086-2093 | **[B]** If `dirSide` is re-derived from a gated D (REG-3), the flip alert changes meaning unless it keeps its own raw side. A's spec said "unchanged"; corrected in REG-3. |
| Panel DRAW row | present | 2338-2340 recomputes the side from `drawD` | **[B]** A gated selection draw is local to the engine block; the panel needs a `var` copy (REG-3). |
| Coiling in density | **present, unsupported** [A✓] | `coilScore` 886-891; 683, 687 | No magnetism (2.7). Owned by WYK-1. |
| Range regime ("both sides raided") | **missing (no bonus needed)** [A✓] | — | Ranges do not raise P(both); compression does, via the surface (2.6, 2.7). |
| Volatility compression / expansion | **partial** [A✓] | `atrE` = max(ATR14, ATR200) 878 (ejection gates 1578, 1654, 1834, 1859) | Used only for ejection. Not used for PoT unit, reach, both-sides risk, the ledger, or display. |
| Squeeze / NR7 / breakout continuation | **missing (correctly)** [A✓ + B] | — | No directional evidence (2.3, 2.8). |
| Hurst / VR / ADX | **missing (correctly)** [A✓] | — | Noise at chartable windows (2.2). |
| Per-regime accuracy | **missing** [A✓] | ledger: `Trial` 375-395, `f_openTrial` 1426, `f_book` 1461-1499; `stN/stK/stPE/stPV` 1066-1070 | Split by family only. |
| Killzone hysteresis | n/a (time regime) | `hystEff` 976 | Owned by TIME-5. |

---

## 4. Proposals (spec-level, best first)

Conventions: new globals go in SERIES after line 878 unless stated; state after line 1080; engine changes run inside the confirmed-bar block (1518+). Everything uses closed-bar values, adds no `request.*` call, and is O(1) per bar unless stated. Pine has no forward references: every function below is declared after the globals it reads and before its first caller.

### REG-1 (P1, M) · Horizon-matched unit and an informative key for the empirical PoT surface [A, CORRECTED and REPLACED; supersedes QPOT-03's 9-row key and BIAS-6]

**Why.**
- The surface is keyed on `htfBias`, which carries no reach information (M12: −0.02..+0.41% on five families). That key only splits the sample three ways.
- The surface is scaled by ATR14 at the window start. That unit is biased by volatility mean reversion: hit minus PoT is −5.5..−8.2 pp in expanded volatility on 15m/1H/BTC (2.6; amt B7 ±6-8 pp). The bias reaches the headline PoT, proximity reach, reach bands, reach classes and the EDGE baseline.
- A's REG-1 (vol-tercile rows) treats the symptom. B's tests show the unit fix dominates it everywhere intraday, and vol rows dilute time-of-day rows.

**Change (three parts).**
1. **Unit.** On intraday charts, measure every surface distance in `aU = √(ATR14 · ATR100)`. Keep ATR14 on daily and above (the blend hurt there, +0.66%).
2. **Key.** Remove the `htfBias` rows. The row is TIME-2's NY 3-hour block on charts ≤ 1H (pooled row otherwise), with TIME-2's partial pooling.
3. **Optional sub-key.** "Volatility" (3 tercile rows from REG-2's `vState`) is offered as an option and as a candidate in TIME-4's per-chart PoT scorecard, default off.
- When TIME-3's volatility clock is built and wins TIME-4's scorecard, it replaces `aU` (same idea, better forecast).

**Pine sketch.**
```pine
// INPUTS (G_POT)
string surfUnit = input.string("Blended", "Reach Surface Unit", options = ["Blended", "ATR"], group = G_POT, display = display.none,
  tooltip = "Blended: distances on the empirical reach surface use √(ATR14 × ATR100), a cheap forecast of volatility over the horizon (fast ATR drifts back toward slow). ATR: the classic ATR14 unit. Daily and higher charts always use ATR.")
// SERIES (after 878)
float atr100 = ta.atr(100)
float aU     = surfUnit == "Blended" and timeframe.isintraday and not na(atr) and not na(atr100) ? math.sqrt(atr * atr100) : atr
// STATE (1061-1062): rows = TIME-2's NQ1 time-of-day rows (or 1 pooled row); the htfBias dimension is gone
// step 0 (1527-1532)
float aH = aU[H]
if bar_index > H and not na(aH) and aH > 0 and not na(close[H])
    int qH = todQ[H]                              // TIME-2 block of the window's first bar (NQ = pooled)
    f_bump(sUp, NQ, (fwdHi - close[H]) / aH)      // pooled row always
    f_bump(sDn, NQ, (close[H] - fwdLo) / aH)
    if qH < NQ
        f_bump(sUp, qH, (fwdHi - close[H]) / aH)
        f_bump(sDn, qH, (close[H] - fwdLo) / aH)
```
- `f_empPoT(float dU, int side, int q)` reads cell row `q` and pooled row `NQ` and blends them as TIME-2 specifies; the `bias` argument and the `r = bias + 1 / 1 − bias` mapping (1286) go away.
- Callers pass the unit-scaled distance: `f_potModel` 1307 and `f_potBase` 1318 use `d / aU` (guard `nz(aU) > 0`). The analytic prior is unchanged; it works in price units through `potSig`.
- `f_reachD(S, q, p)` returns u-units. Reach bands (2195-2199) multiply by `aU` instead of `atr`. Reach classes compare `dist / aU` (2236 `dAtr`, 2352 `dA`).
- **Proximity reach (665), compile-safe.** `evaluate` (661) cannot call `f_potModel` (1303; it reads `sUp`/`sDn` declared at 1061). Add a parameter: `method evaluate(..., float mu, float reachP)` and in the body `float reach = dAtr >= maxATR ? 0.0 : not na(reachP) ? math.min(1.0, reachP / 0.95) : sig > 0 ? f_pot(dist, sig, 0.0, potH) / 0.95 : lin`. At the call site (1948, step 17, after 1303): `lv.evaluate(close, atr, anchors, confTol, dSel, nz(potSig), 0.0, f_potModel(math.max(0.0, lv.distance(close)), lv.side, 0.0))`. Cost: one O(1) surface lookup per pool level (≤ `poolMax` 40) per confirmed bar.
- The `lin` half of proximity and `maxATR`/ejection keep ATR14 (user-facing distance semantics unchanged).
- `aU` is a global series, so `aU[H]` is valid. It changes only with closed-bar ATRs in step 0; the live PoT readout stays live as designed.

**Expected value** [B-test, OOS]: log-loss −3.0% (5m), −5.8% (15m), −0.65% (1H), −1.2% (BTC 1H) with time-of-day rows; unit alone −0.4 / −2.8 / −0.45 / −1.2%. Expanded-tercile calibration bias from −5.5..−8.2 pp to −0.8..−3.1 pp. A volatility-neutral EDGE baseline, so the accuracy panel stops crediting compressed-tape picks.

**Evidence.** Moderate: B's 2-fold OOS on 6 CME futures × 3 timeframes + BTC + daily indices; consistent with QPOT-02/03, TIME-2/3 and amt B7 on other data. The concept (volatility mean reversion, HAR) is strong.

**Risk.**
- On 5m the unit alone over-corrects (compressed −5.1 pp). Ship with TIME-2's rows (−2.3 pp) and QPOT-04's recalibration.
- ATR100 needs 100 bars (falls back to ATR14 via the `na` guard).
- Old surfaces change meaning; the surface is rebuilt from history on load, so this is harmless.
- The best exponent varies by timeframe (15m ≈ 0, 5m ≈ 0.75). 0.5 is a robust default; TIME-4's scorecard can choose among {ATR, Blended, Clock}.

**Effort.** M (most edits are call-site unit swaps). Coordinate with TIME-2 (same arrays) and OF-6 (its σ factor multiplies on top).

### REG-3 (P1, S) · The draw vector does not steer target choice without measured skill; hard efficiency gate as the legacy option; zero drift everywhere [A, CORRECTED]

**Why.**
- D-first selection loses 9-12 pp first-touch and 5-8 pp hit-within-H intraday (5 / 3 pp daily) against geometry, on 23 series and the null (2.4).
- All three D components test null: structure (2.3, 2.4; ICTS: 47.4-52.7% on 11 markets), displacement (2.8; ICTS B6 51.3%), raid sign (2.8; BIAS-4).
- The hard ER gate matches geometry because it acts on only 0.3-0.5% of races. A's soft gate is 0.2-0.8 pp worse.
- Drift adds error in every regime (2.5).
- Siblings own the default: BIAS-2 (calibrated D) or ICTS-1 (evidence-gated D). REG-3 is the "Structure (gated)" option and the minimal fallback if neither is built.

**Algorithm (step 14, after 1894).**
1. Keep `drawD` for the panel, the data window and the Draw Flip alert.
2. Selection draw with a **hard** gate: `dSel = regGate and erA >= erTrend and math.sign(drawD) == math.sign(erS) ? drawD : regGate ? 0.0 : drawD`.
3. `dirSide` (1895) from `dSel`. Keep a separate `rawSide` from `drawD` for the flip logic (1896-1898), so the "Draw Direction Flip" alert keeps its meaning.
4. `lv.evaluate(..., dSel, nz(potSig), 0.0, ...)` (1948): Draw pillar and `ctrMult` follow `dSel`, and drift is 0. With `dSel = 0` every level's Draw pillar is 0.5 (neutral) and selection is by score among both sides.
5. `driftW` default 0.0 (QPOT-01, BIAS-8). Tooltip: "Drift was tested in trend and range regimes and lowered accuracy in every one."
6. Store `drawSel := dSel` in a `var float` so the panel (2338) can show `DRAW ▲ +0.62 (gated: no efficient trend)` when `|drawD| ≥ dGate` but `dSel = 0`.

**Pine sketch.**
```pine
bool regGate = input.bool(true, "Gate Draw by Efficiency", group = G_FLOW, display = display.none,
  tooltip = "On: the draw vector steers target choice only in an efficient trend that agrees with it (rare). Elsewhere the nearer, likelier pool wins. Off: classic behaviour.")
var float drawSel = 0.0
// step 14, after drawD (1894)
float dSel = regGate ? (erA >= erTrend and math.sign(drawD) == math.sign(erS) ? drawD : 0.0) : drawD
drawSel := dSel
int rawSide = drawD >= dGate ? 1 : drawD <= -dGate ? -1 : 0
int dirSide = dSel >= dGate ? 1 : dSel <= -dGate ? -1 : 0
if rawSide != 0 and rawSide != lastDirSide
    drawFlip := lastDirSide != 0 and inCalc
    lastDirSide := rawSide
```
`erA`, `erS`, `erTrend` come from REG-2 (declared in SERIES/INPUTS, before 1518). `math.sign` returns a float; equality of −1/0/1 floats is exact.

**Expected value.** On the simulation, +9-12 pp first-touch and +5-8 pp hit-within-H of the chosen side intraday (+5 / +3 pp daily); far fewer "⚠ COUNTER-DRAW" flips in chop.

**Evidence.** Moderate (engine-proxy simulation on 23 series + null; siblings ICTS, BIAS, PA agree).

**Risk.** A far with-trend pool that a trader expects is not chosen unless it is also the best-scoring level. The data back that. The legacy behaviour stays one toggle away.

**Effort.** S.

### REG-2 (P1, M) · Two-axis regime classifier, regime-split ledger and a calibration-by-volatility audit [A✓, sharpened]

**Why.** Traders expect regime awareness. The honest version labels the regime and *measures*, per chart, whether it matters, instead of assuming it. It is also the reporting layer for REG-1/3/4/5, and its TREND-AGAINST cell tests claim C1 on the user's own chart. **[B-NEW]** Its volatility split also detects the B7-type PoT bias on the user's chart (before and after REG-1).

**Classifier** (chart timeframe; no request).
- **E axis.** `erLen` 20, `erTrend` 0.40, `erRange` 0.15.
  - `erPath = math.sum(math.abs(ta.change(close)), erLen)`; `erS = erPath > 0 ? (close - close[erLen]) / erPath : 0.0`; `erA = math.abs(erS)`.
  - `eState` (`var int`, confirmed bars): `erA >= erTrend ? int(math.sign(erS)) : erA < erRange ? 0 : (eState != 0 and erA >= erTrend - 0.08 ? eState : 0)`.
  - Labels TREND ▲ / TREND ▼ / RANGE / MIXED.
- **V axis.** `vState` ∈ {0 compressed, 1 normal, 2 expanded} from `vLn = math.log(atr5 / atr100)` (guard `na`): EWMA mean and variance with α = 2/2001, z = (vLn − μ)/σ, enter at ±0.43, leave at ±0.30. Display, ledger and alerts only (not a PoT key by default; see REG-1).
- **Base-rate disclosure** [B-NEW numbers]. Tooltips: "On a random walk, Efficiency ≥ 0.40 appears on about 16% of bars (ADX ≥ 25 on 38%), and the label describes the last N bars, not the next ones."

**Ledger split** (extends 375-395, 1426-1431, 1461-1499).
- `Trial` gains `int eCls`, `int vCls`, `float pPot` (the PoT shown at open, shared with QPOT-04).
- In `f_openTrial`: `eCls = erA < erRange ? 0 : erA < erTrend ? 1 : (int(math.sign(erS)) == lv.side ? 2 : 3)` (RANGE / MIXED / TREND-WITH / TREND-AGAINST); `vCls = vState`.
- Arrays `rgN`, `rgK` (int[7]), `rgPE`, `rgPV`, `rgPP` (float[7]). In `f_book`, update index `eCls` and `4 + vCls` beside `stN/stK/stPE/stPV`; `rgPP` accumulates `pPot`.
- Full accuracy view, shown once a cell has n ≥ 20, with Wilson intervals:
  - `REGIME  RNG 44% +1.2 · MIX 47% +3.0 · TR+ 52% +4.1 · TR− 38% −6.0` (hit %, EDGE pp = (K − ΣpBase)/n, z = (K − ΣpBase)/√ΣpV).
  - `VOL     CMP 55% (PoT 51) · NRM 47% (48) · EXP 39% (45)`: hit % against mean shown PoT per volatility class. A persistent gap in EXP is the B7 bias.
- Terminal row: `REGIME  TREND ▲ · ER .52 · VOL CMP`. Clean: optional 4th table row `Regime | TREND ▲`, off by default. Data window: `plot(erS, "Efficiency (signed)", display = display.data_window)`, `plot(vState, "Vol State", display = display.data_window)`.

**Evidence.** Strong for the measurement design (a stratified version of the existing distance-matched ledger). Weak that any trend regime matters (2.3).

**Risk.** Thin cells (minimum n, Wilson intervals). Users may over-read labels; tooltips disclose the base rates. CPU negligible.

**Effort.** M.

### REG-4 (P2, S) · Scope and soften the counter-draw penalty [A, DOWNGRADED evidence]

**Why.** `ctrMult` 0.50 halves every level opposite D whenever |D| ≥ 0.35. The only support for a counter-trend handicap is A's chart-TF efficient-trend cells on 1H/D (−6.7 pp vs null −1.5/−1.7); with an HTF trend definition it does not replicate (2.7). On a ~50% base, a −5 pp effect is about ×0.85-0.90, not ×0.50.

**Change.**
- Default `ctrMult` 0.85 (162).
- With REG-3, `dirD = dSel` already confines the penalty to gated trends.
- Label: `activeCtr := not na(activeLv) and dirSide != 0 and activeLv.side != dirSide and eState != 0` (2029); the "⚠ COUNTER-DRAW" head (2237) follows. Hold and eviction (2001-2007) unchanged.
- Under BIAS-2 ("Calibrated" draw source), 0.85 is the value to A/B test.

**Measurement.** REG-2's TREND-AGAINST EDGE. If it stays ≤ −1σ on a chart, the user can lower `ctrMult`.

**Evidence.** Weak. **Risk.** Low. **Effort.** S.

### REG-5 (P2, M) · Stop-run readout and an expansion alert (claim C2 done right) [A, simplified]

**Why.** "Both sides get raided" is true in compressed volatility, not in ranges (2.7). The race `WIN≤H` (`f_invalidation`, 1343-1366) says which barrier is hit first; it does not say how likely the stop beyond the opposing pool is to be traded at all within H. Traders ask exactly that.

**Readout** (Terminal HUD and the Clean label tooltip).
- `STOP-RUN ≈ p%`, p = `f_potModel(risk, -activeLv.side, 0.0)`: the empirical probability of reaching the invalidation distance on the opposite side within H, from the REG-1 surface. One O(1) call at the HUD (global scope, after 1303).
- Tag `SQZ` / `EXP` from `vState`.

**Grading** (P3 part, optional).
- On booking a trial whose target hit before H, push the invalidation price, side, end bar (`bar0 + H`) and p to `srInv/srSide/srEnd/srP` (≤ H + 64 entries).
- Each confirmed bar, loop once: resolve a stop touch (`side == 1 ? low <= inv : high >= inv`) or expiry; accumulate Brier; remove. O(H) per bar, far below the per-loop limit.
- Full view: `STOP-RUN cal · Brier .21 · n 120`.

**Alert.** Optional "Volatility Expansion": `vState` moves 0 → 2 within ≤ 10 bars, or `2·ta.stdev(close, 20) < 1.5·ta.atr(20)` turns false after ≥ 6 bars true; once per state; on bar close via `alert()`. The message says: "range expansion likely in ATR terms; direction not forecast".

**Evidence.** Moderate for the volatility effect (mechanical, reproduced by the null and by QPOT-03/amt B7); none for direction, and it is labelled so.

**Risk.** One more HUD line; alert noise if the transition rule is loose (latch it).

**Effort.** M (S without grading).

### REG-7 (P2, S) · Breakouts and displacement are volatility events, not draw votes [B-NEW]

**Why.**
- Displacement bars do not continue in their direction on 4 of 5 families (0.484-0.516; null 0.49-0.52). CME 1H shows 0.548 vs null 0.509 in one cell (2.8). ICTS B6: 51.3% (n 4,347).
- NR7 breaks do not continue (0.482-0.515; slight intraday failure). Mesfin: Asia expansion bars reverse (T −10.96); ORB fails walk-forward.
- Yet `mV` gives displacement 20% of D (1893), and D steers selection.

**Change.**
- Default `wM` (156) 0.20 → 0.0 for the selection draw. Displacement stays where it has a mechanical role: FVG quality (`fvgQBase` 907-912), OB leg quality, origin lockout.
- Do not add squeeze-direction, NR7-break or ORB-continuation logic to D or to scoring.
- If ICTS-1's component-skill gate is built, it decides `wM` per chart instead; this default is the evidence-based starting point (ICTS already names `wM` the "first candidate" for 0).

**Measurement.** ICTS-1's per-component skill on the user's chart; REG-2's ledger.

**Evidence.** Moderate (B: ~8,000 displacement events and ~18,000 NR7 breaks across five families with nulls; ICTS B6; MNQ study).

**Risk.** Removes a trader-intuitive input from D. The panel can still show the last displacement as context.

**Effort.** S (one default).

### REG-6 (P3, S) · Regime features for the learned side model (only with BIAS-1) [A✓, extended]

**Why.** Weak, timeframe-specific signals exist and none replicates across timeframes:
- 1H with-trend excess in chart-TF efficient trends (+6.1 ± 2.5 pp);
- 5m continuation of trend-aligned sweeps (+5 pp vs null);
- BTC 1H with-HTF-trend excess (+2.9 ± 1.4 pp, null +0.6) [B-NEW];
- 1H displacement continuation (0.548 vs 0.509) [B-NEW].
They belong in a per-chart learned model with zero prior weight, not in fixed rules.

**Features** (oriented toward the buy-side candidate, each in [−1, 1]):
- `x1 = gE · sign(erS)` with `gE = clamp((erA − 0.25)/0.20, 0, 1)`;
- `x2 = x1 · [last bar swept a pool on that side]`;
- `x3 = sign(htfErS) · [htfErA ≥ 0.4]`, HTF ER10 on the structure timeframe (one more element in the existing HTF `request.security` tuple, `[1]`-offset, lookahead on);
- `x4 = mV` (displacement direction, decayed);
- `x5 = clip(vz, −2, 2)/2` (direction-free, should learn ≈ 0).

**Learner.** BIAS-1's online logistic over the geometry logit, L2 shrinkage toward 0, prequential scoring. Full view: learned weights ± SE; "regime: no skill on this chart" if the side-ledger Brier skill vs geometry is ≤ 0 after n ≥ 200.

**Evidence.** Weak. **Risk.** Overfitting, controlled by shrinkage and prequential scoring. **Effort.** S given BIAS-1.

---

## 5. What NOT to do (tested and rejected)

- **ADX ≥ 25, CHOP < 38.2 / > 61.8, Hurst > 0.55 or VR as a trend/range switch.** They fire on 7-38% of random-walk bars, have no next-window persistence, and an ADX gate on D costs 2.5-3.5 pp. [A✓ + B]
- **A trend-regime drift in PoT or races.** Worse in every regime. [A✓]
- **Volatility-tercile rows as the PoT key (A's original REG-1).** Small and inconsistent once the unit is fixed; they dilute time-of-day rows. Use the horizon-matched unit instead. [B]
- **A higher-timeframe trend regime as a side selector.** No side information beyond geometry on five families. [B]
- **A range bonus for EQ/range-edge pools, or "both sides get raided in ranges".** Not supported. Use WYK's draw-neutral range handling. [A✓]
- **Squeeze / NR7 / ORB / displacement direction as a draw input.** No continuation (2.8). [A✓ + B]
- **Keeping `liqEvt`'s hold/reject sign** (1579-1582). [A✓]
- **Rewarding pools printed during coiling** (`coilScore`, 683/687). [A✓]
- **A Markov-switching/HMM classifier in Pine.** Feasible, but the states that persist are volatility states, which the O(1) z-score and the unit fix already cover. [A✓ + B]
- **Realised/implied volatility ratios.** Index-specific symbol, monthly-horizon evidence. [A✓]

---

## 6. Reproduction

**A** (`study/quant_regime_tools/`, run `python3 -I <script> [5m|15m|1h|d]`): `rlib.py` (loaders, causal indicators, pivot pools, first passage, sign-flip null, logistic, block SE); `regime_study.py` (O1-O5); `regime_persist.py`; `regime_engine.py`; `regime_dgate.py`; `regime_form.py`.

**B** (`study/quant_regime_b_tools/`, run `python3 -I <script> [5m|15m|1h|btc|d]`; imports A's `rlib`):

| Script | Output | Content |
|---|---|---|
| `blib.py` | — | loaders with UTC timestamps (CME, BTC), NY hour, forward excursions, survival surfaces |
| `b_rwrates.py` | `out_rwrates.txt` | random-walk noise floors for ER, ADX, CHOP, VR-Hurst (B-T1) |
| `b_surface.py` | `out_surface_<fam>.txt` (in-sample exponent), `out_surface_a05_<fam>.txt` (fixed a = 0.5; `FIXA=0.5`) | 13 surface designs on pool-touch events, 2-fold OOS, partial pooling, null, calibration by volatility tercile (B-T2) |
| `b_side.py` | `out_side_<fam>.txt` | HTF efficiency regime (T3), displacement continuation (T4), NR7 break continuation (T5), each vs null |

**Limitations.**
- About one year of 1H and three months of 1-minute data for six CME futures (one volatility regime, 2025-26); BTC 1H 2017-2025; daily equities 1999-2018. No single stocks intraday.
- Pools are 5-bar pivots, not the engine's full source mix (PDH/PDL, sessions, HTF swings). REG-2's ledger measures the user's chart.
- Multiple comparisons: A ~20 gates × 4 families × 3 statistics; B 13 surface designs × 5 families and 5 directional tests × 5 families. Single 2σ cells are treated as weak.
- B's 2-fold split on one-year CME series puts the April 2025 volatility spike in one fold; this penalises any key whose cell estimates drift with the volatility level, which is the realistic case for a chart.

---

## 7. Sources

**Verification note (B).** B re-opened R1, R2, R5, R6, R7, R8 in full text, and checked R4, R9, R12 (Gurrib), R16 (Bulkowski), R18-R22 via search-engine summaries of the publisher or repository pages. B's full-text paper tool ran out of credits mid-study and direct page fetches were blocked for most hosts in this session, so citations marked "[A, not re-opened]" carry A's reading.

- Safari, S. A. & Schmidhuber, C. (2025). *Trends and Reversion in Financial Markets on Time Scales from Minutes to Decades.* arXiv:2501.16772. https://arxiv.org/abs/2501.16772 [verified]
- Schmidhuber, C. (2021). *Trends, Reversion, and Critical Phenomena in Financial Markets.* arXiv:2006.07847. https://arxiv.org/abs/2006.07847
- Kurth, J. G., Eisler, Z., Rej, A., Bouchaud, J.-P. (2026). *Is Trend Still Your Friend? A Microstructural Account of the Demise of Short-Term Trend-Following.* arXiv:2607.01550. https://arxiv.org/abs/2607.01550 [verified]
- Moskowitz, T., Ooi, Y. H., Pedersen, L. H. (2012). *Time Series Momentum.* JFE 104(2), 228-250. https://papers.ssrn.com/abstract=2089463
- Gao, L., Han, Y., Li, S. Z., Zhou, G. (2018). *Market Intraday Momentum.* JFE 129(2), 394-414. https://econpapers.repec.org/RePEc:eee:jfinec:v:129:y:2018:i:2:p:394-414 · working paper: https://c.mql5.com/forextsd/forum/173/intraday_momentum_-_the_first_half-hour_return_predicts_the_last_half-hour_return.pdf [verified via search]
- **[B-NEW]** Baltussen, G., Da, Z., Lammers, S., Martens, M. (2021). *Hedging Demand and Market Intraday Momentum.* JFE 142(1), 377-403. https://econpapers.repec.org/RePEc:eee:jfinec:v:142:y:2021:i:1:p:377-403 · https://pure.eur.nl/en/publications/hedging-demand-and-market-intraday-momentum/
- **[B-NEW]** Li, Z., Sakkas, A., Urquhart, A. (2022). *Intraday Time Series Momentum: Global Evidence and Links to Market Characteristics.* J. Financial Markets 57, 100619. https://ideas.repec.org/a/eee/finmar/v57y2022ics138641812100001x.html · https://centaur.reading.ac.uk/95566
- Heston, S. L., Korajczyk, R. A., Sadka, R. (2010). *Intraday Patterns in the Cross-section of Stock Returns.* J. Finance 65(4). arXiv:1005.3535. https://arxiv.org/abs/1005.3535
- Lo, A. W., MacKinlay, A. C. (1988). *Stock Market Prices Do Not Follow Random Walks.* RFS 1(1). https://www.nber.org/system/files/working_papers/w2795/w2795.pdf
- Portnaya, V. (2026). *The Bounce Has No Direction.* arXiv:2606.29591. https://arxiv.org/abs/2606.29591 [verified; daily/weekly data]
- Le, N. H. (2026). *Synchronization Reveals Market Structure That Classical Randomness Tests Cannot Detect.* arXiv:2610.11028. https://arxiv.org/abs/2610.11028 [verified]
- Upadhyay, R. (2026). *Do Time-Series Foundation Models Forecast Index-Futures Returns?* arXiv:2611.12141. https://arxiv.org/abs/2611.12141 [verified]
- Mesfin, M. (2026). *Structural Limits of OHLCV-Based Intraday Signals in MNQ Futures.* arXiv:2605.04004. https://arxiv.org/abs/2605.04004 [verified] · *A Validated Volatility-Volume-Gap Classifier…* arXiv:2605.11423 [A, not re-opened]
- **[B-NEW]** LeBaron, B. (1992). *Some Relations between Volatility and Serial Correlations in Stock Market Returns.* J. Business 65(2), 199-219. https://ideas.repec.org/a/ucp/jnlbus/v65y1992i2p199-219.html
- Bianco, S., Corsi, F., Renò, R. (2008). *Serial correlation and heterogeneous volatility in financial markets: beyond the LeBaron effect.* arXiv:0810.4912. https://arxiv.org/abs/0810.4912
- **[B-NEW]** Campbell, J. Y., Grossman, S. J., Wang, J. (1993). *Trading Volume and Serial Correlation in Stock Returns.* QJE 108(4), 905-939. https://www.nber.org/papers/w4193 · https://dash.harvard.edu/bitstream/1/3128710/2/campbell_trading.pdf
- Kristoufek, L. (2012). arXiv:1201.3511 · Barunik, J., Kristoufek, L. (2012). arXiv:1201.4786 · Bartolozzi, M. et al. (2007). arXiv:0707.3321 [A, not re-opened]
- Corsi, F. (2009). *A Simple Approximate Long-Memory Model of Realized Volatility* (HAR). J. Financial Econometrics 7(2), 174-196. https://statmath.wu.ac.at/~hauser/LVs/FinEtricsQF/References/Corsi2009JFinEtrics_LMmodelRealizedVola.pdf
- Bollerslev, T., Tauchen, G., Zhou, H. (2009). *Expected Stock Returns and Variance Risk Premia.* RFS 22(11).
- Hamilton, J. D. (1989). Econometrica 57(2) · Pomorski & Gorse (2022) arXiv:2208.11574 · Srivastava & Bhattacharya (2018) arXiv:1812.02527 [A, not re-opened]
- **[B-NEW]** Nystrup, P., Kolm, P. N., Lindström, E. (2020). *Greedy Online Classification of Persistent Market States Using Realized Intraday Volatility Features.* J. Financial Data Science 2(3), 25-39. https://orbit.dtu.dk/en/publications/greedy-online-classification-of-persistent-market-states-using-re/
- Wilder, J. W. (1978). *New Concepts in Technical Trading Systems.* ADX filter tests: https://oxfordstrat.com/trading-strategies/average-directional-index/ · https://algolab.co.kr/blog/adx-filter-trend-breakout-backtest-2026 [A, not re-opened] · **[B-NEW]** Gurrib, I. (2018). *Performance of the Average Directional Index as a market timing tool for the most actively traded USD based currency pairs.* Banks and Bank Systems 13(3). https://doaj.org/article/c9e4205156864d86b906f30a229930b9
- Kaufman, P. J. *Trading Systems and Methods* (efficiency ratio, KAMA). https://ta-lib.org/functions/er.html · https://www.luxalgo.com/library/concept/kaufman-efficiency-ratio.md
- Dreiss, E. W., Choppiness Index: https://www.barchart.com/education/technical-indicators/choppiness_index
- Carter, J., TTM Squeeze: https://www.barchart.com/education/technical-indicators/ttm_squeeze · Bollinger squeeze (direction-neutral): https://chartschool.stockcharts.com/table-of-contents/trading-strategies-and-models/trading-strategies/bollinger-band-squeeze
- Crabel, T. (1990). *Day Trading with Short Term Price Patterns and Opening Range Breakout.* **[B-NEW]** Bulkowski, T., NR7 statistics: https://thepatternsite.com/nr7.html
- **[B-NEW]** Holmberg, U., Lönnbark, C., Lundström, C. (2013). *Assessing the profitability of intraday opening range breakout strategies.* Finance Research Letters 10(1), 27-33. https://ideas.repec.org/a/eee/finlet/v10y2013i1p27-33.html
- Sibling studies: `study/quant_pot.md` (QPOT-01..09), `study/bias_dol.final.md` (BIAS-1..8), `study/ict_struct.final.md` (ICTS-1, B6), `study/ict_time.final.md` (TIME-1..8), `study/wyckoff_sd.final.md` (WYK-1..4), `study/orderflow_micro.final.md` (OF-6), `study/amt_profile.final.md` (B7), `study/price_action.md`.
