# SMT divergence and intermarket analysis: final combined report (A + B)

Domain: ICT SMT divergence ("crack in correlation") and its relatives: PSP, hidden (close-based) SMT, FVG SMT, triad SMT, inverse/DXY SMT, the correlation regime, and lead-lag. The question for the DOL engine: can a correlated symbol help predict **which liquidity the chart takes next, when, and how likely**?

How to read the marks:
- **[A✓]**: researcher A's claim, re-checked by B against the source or the data.
- **[B-corrected]**: A's claim changed by B. The reason is given.
- **[B-new]**: added by B.

Scope note. Firecrawl web credits were exhausted for both researchers, and the proxy blocks most hosts. Only github.com, raw.githubusercontent.com, PyPI, WebSearch summaries and the Firecrawl paper index were reachable.
- A's evidence base: search summaries, seven public GitHub repositories read in full, and an original event study on CME futures (ES, NQ, YM, RTY, GC, SI, 6E, 6B, MBT, MET).
- B's evidence base:
  - re-read the repositories and checked every quoted number;
  - pulled academic papers through the paper index;
  - re-ran A's data with **independent code and a different design** (a pooled logistic panel with own-path controls, a placebo, and a decay curve);
  - added a 20-year daily S&P 500 / Nasdaq Composite sample (1999–2018).

---

## 0. Executive summary

1. **SMT is not a reversal signal [A✓, strengthened].** When the chart sweeps a level and the comparison symbol fails to take its twin, a 1-ATR race reverses no more often than after a joint sweep:
   - 50.5% vs 50.8%, n = 16,258 / 16,187, difference CI [−2.2, +1.5] pp. With Pine's 1-bar delay: 49.7% vs 50.7%, CI [−2.8, +0.7].
   - Three public studies agree: ES/NQ 49.5–51.8%; NQ/ES/YM/RTY 47–51% over 88 tests, none beyond chance; an audited ES/NQ SMT+FVG system at −0.10 to −0.17 R.
   - **[B-new]** A found a small tilt toward "the opposite pool is taken first" (+1.2 to +5.3 pp). It is **geometric**: A's overshoot past the level is 0.60 ATR in SMT events vs 1.06 ATR in joint ones. With overshoot and raid class controlled, the SMT coefficient drops from +0.140 to +0.016 [−0.064, +0.096] logit.
2. **[B-corrected] Most of A's "laggard sync lift" comes from the chart's own price path, not from the sister.** A measured a lift of 1.054 with Pine timing (B's independent code reproduces it at 1.051). The control matched only close-based distance and close-to-close momentum.
   - At the moment the sister sweeps, the chart's own wick has typically just come about 35% closer to its pool than the controls' wicks. For example, at 1–1.5 ATR the median wick gap is 0.47 vs 0.74 ATR.
   - It is also in a range burst (mean true range of the last 3 bars well above ATR14).
   - Adding those two own-path terms removes the fresh effect. In the first 0–1 bars after the sister's sweep is known, Δlogit goes from +0.129 [+0.073, +0.186] to −0.007 [−0.062, +0.048]. Event lift: 0.995.
3. **[B-new] A small, real cross-asset effect remains, and it is persistent, not front-loaded.** While the sister state persists (sister swept 2–31 bars ago, chart pool still intact), the chart's pool is hit a little more often than own-path-matched controls:
   - Δlogit +0.078 [+0.023, +0.133] (L3, H12) and +0.085 [+0.007, +0.163] (L5, H30, the engine's default pivot length and horizon).
   - That is a lift of 1.035–1.042 (about +1.5 to +1.9 pp); for pools more than 1 ATR away, 1.039–1.052.
   - The placebo (comparison symbol shifted 500 bars) gives +0.014 [−0.066, +0.095] and a lift of 1.006.
   - It is positive in all four asset classes: metals 1.09–1.11, crypto 1.05–1.07, FX 1.01–1.05, index 1.03. It fades after about 32 bars.
   - On daily S&P/Nasdaq it is mixed: L5 any-age +0.30 [+0.15, +0.44]; L3 +0.02 (not significant).
4. **[B-new] The biggest forecasting gain this study found needs no second symbol. It is the range burst.**
   - Across about 430,000 pool-bars, pools are hit at 1.13× the distance-matched rate when the 3-bar mean true range exceeds 1.25 × ATR14 (15% of bars), and at 0.93× when it is below 0.8 (35% of bars). At H = 30 the figures are 1.075× and 0.94×.
   - For example, at 1.5–2 ATR, H = 12: 47.2% vs 38.7% hit.
   - The engine's PoT uses a 50-bar close-to-close σ and an ATR-based empirical surface, so it cannot see this.
5. **[B-corrected] The engine's raid-close classification is not a reversal signal either.** A called it the "primary sweep-reversal signal, evidence moderate, keep". In A's own events, the geometry-neutral race gives about 50% for every class: reject 50.3–50.4%, hold 49.5–50.3%, mid 49.2–50.5%. The 11–15 pp next-liquidity gap A reported is geometric. This agrees with `ict_liq.final.md` ICT-9 (neutral REJECT).
6. **Design consequences.**
   - (a) First implement the own-path range-burst conditioning of the empirical PoT surface (no request, every chart).
   - (b) Then, optionally, add the SMT module: one `request.security` call with `ticker.inherit` + `[1]` + `lookahead_on`, giving 7 of 40 requests. It assigns each pool a twin on the comparison symbol and tracks a sister state.
   - (c) The sister state feeds only a **small persistent PoT logit shift**: prior +0.08 at ages 2–31, calibrated live against the engine's own PoT. It does **not** feed D or the raid classification.
   - (d) A ledger shows users whether the ICT reversal reading holds on their own pair.

---

## 1. Concepts: definitions and parameters

### 1.1 Two-symbol swing SMT [A✓]
- **Practitioner definition** (ICT; LuxAlgo concept page; Smart Money gitbook):
  - **Bearish SMT:** A trades through its prior swing high (a higher high) while the positively correlated B fails to trade through its **time-matched** swing high.
  - **Bullish SMT:** the mirror at lows.
  - **Usual pairs:** ES/NQ/YM (RTY), EURUSD/GBPUSD (vs DXY, inverse), gold/silver, BTC/ETH.
  - **Claimed reading:** the sweep was a stop run, so expect a reversal toward the opposite liquidity. Practitioners say it is "confluence, not a standalone trigger" and "more meaningful in a killzone at a level of interest".
  - **[B-new] ICT nuance:** the same rule is applied at a retracement low inside an uptrend ("SMT at discount"). There, "reversal of the sweep leg" means **continuation** of the higher-timeframe trend. Measuring reversal of the sweep direction, as A and B do, covers both uses.
- **Algorithmic definition.** Synthesised from `thomas-quant/mss-research`, `charisjv19/intermarket-divergence-scanner` v8.5–v8.10, `thomas-quant/SMT`, and the Pine scripts GXV SMT, Genjutsu Kai and Kodexius; all re-read by B.
  1. **Swing on A.** A pivot at bar T with L left and L right bars (`ta.pivothigh` semantics). It is usable from bar T+L.
  2. **Twin on B.** `R_B = max(high_B[T−w .. T+w])`, with w = 0–2.
     - The scanner tightened w to 0 ("exact parallel timestamps").
     - mss-research matches the two swings within ±1 bar.
     - Interval variants match whole candles by their open and close times (GXV).
  3. **B intact at confirmation.** B must not trade through `R_B` in (T+w, T+L]. Otherwise the comparison is undefined.
  4. **Sweep (strict).** `high_A > P`, a wick trade-through; the scanner switched from bodies to wicks in v8.5. This is the engine's `touched()` rule (L623–624).
  5. **Divergence.** B has not exceeded `R_B` by the decision bar. GXV uses `XOR(A swept, B swept)`.
  6. **Grace.** Genjutsu Kai waits 2 minutes before calling an SMT. The sister's chance of following is highest in the first minute (11–20%), about half that in the second, then decays slowly [A✓, README].
  7. **Minimum lag.** The leader must be ahead by more than k × σ of the 1-minute return difference over 60 bars. k by session: Asia 0.92, Asia→London 0.88, London 1.14, London→NY 1.19, NY 1.34, post-close 0.87; opening ranges 1.16 / 1.30 / 1.65. It cuts about 1 SMT in 9. "It removes clutter; it is not an edge filter." "Hairlines synced more (held 37–43% vs 49–61%)." [A✓, Pine tooltip L55]
  8. **Staleness.** The scanner requires the newest swing within 120 minutes on 1m and 90 minutes between the swept and the newest swing.
  9. **Invalidation ("broken").** The failing asset later crosses its reference level (`thomas-quant/SMT`: invalidation asset = failing asset, level = its reference) [A✓]. This is the same event as the "sync" in 1.3.
- **[B-new] Backtest hygiene: the pivot-confirmation look-ahead.**
  - mss-research first fired divergence events on the swing bar. A k = 1 swing is only confirmed one bar later, and the confirming bar moves in the signal direction by construction. Divergences therefore plotted at **55–62%** win rates.
  - Moved to the confirmation bar, they fell to **49.4–50.8%**, with means of −1.1 to +0.3 bp. "Every earlier divergence result was an artifact of the look-ahead."
  - Vendor claims such as "SMT wins 70%+" have no disclosed method, and the classic way to produce them is exactly this. Any SMT statistic the engine shows must be computed at the confirmation or decision bar, as the proposed ledger does.
- **Parameters in the wild:**
  - pivot L = 1 (mss-research), 3 (LuxAlgo default), 4 (scanner); the engine's `pivLen` defaults to 5 (L90);
  - twin window ±0–2 bars;
  - timeframes from 1m–15m (NY AM, London) to 1H–4H for intraday bias, and D/W for swing.

### 1.2 Range / interval SMT ("candle SMT", SSMT, quarterly) [A✓]
- **Definition.** Compare the previous interval's high and low on both symbols: the previous 30m, 1H, 90m, 4H, D or W candle, or a session or quarterly-theory cycle. It is an SMT when exactly one symbol trades through its previous-interval extreme during the current interval.
- **Implementations:**
  - GXV SMT Lite: 13 interval ranks (15m … 12M), each matched by exact open and close times.
  - Genjutsu Kai: 30-minute ranges, hourly ranges on the :30, and the opening range. Each SMT is followed to **sync** or **hold**.
- **Engine mapping.** This maps onto key pools that already exist: PDH/PDL, PWH/PWL, Asia/London/NY session ranges, HTF/STF pivots.

### 1.3 Sick sister, sync and hold [A✓, role corrected by B]
- **Terms.** The failing market is the "sick sister". **Sync:** it later takes its twin. **Hold:** it never does within the window.
- **Genjutsu Kai "HYDRA" sync odds.** Verified in the Pine source, L144–157:
  - Formula: `p = logistic(A + B·logit(2Φ(−gap/(κ·σ1·√minutes_left))) + kind + session)`.
  - Fitted values: A = −0.0797, B = 0.7466, κ = 0.89 (30m) / 0.95 (60m) / 0.965 (OR). Session terms: Asia −0.366, post-close −1.406.
  - Fitted on NQ–ES, NQ–YM, ES–YM and RTY–ES 1-minute data 2018–24. On the locked 2025–26 test: AUC 0.85, calibration 3→3%, 20→18%, 40→39%, 59→63%, 77→82%, 96→93%.
  - "53–64% of 30m SMTs held in every session but the post-close hour" (Pine tooltip L36). NQ–YM 64% held, NQ–ES 54%.
- **[B-new] What the formula means.** It is a random-walk first-passage probability with B < 1. Far levels sync more often than the random walk predicts, and near levels less often. Structurally it is the engine's own PoT, recalibrated. The authors state that it "forecasts the sister's reach, not the direction after the window: held and synced SMTs were both coin flips afterwards".
- **[B-corrected] DOL relevance.** A treated the laggard's untaken twin as a pool with markedly higher PoT, strongest right after the sister's sweep. B's own-path-controlled panel (section 2.3) shows:
  - the fresh effect is explained by the chart's own wick proximity and range burst;
  - a small **persistent** state effect remains for ages 2–31 bars (Δlogit ≈ +0.08).

### 1.4 Inverse-correlation SMT (DXY vs EURUSD/GBPUSD; yields vs bonds) [A✓ with one correction]
- **Definition.** Mirror B with `high_B' = −low_B` and `low_B' = −high_B`, then apply the positive-correlation logic unchanged (GXV "normalised once" swap; Kodexius and Larper "Inverse" toggles).
- **ICE USDX weights [A✓, strong].** EUR 57.6%, JPY 13.6%, GBP 11.9%, CAD 9.1%, SEK 4.2%, CHF 3.6%. `USDX = 50.14348112 × EURUSD^−0.576 × USDJPY^0.136 × GBPUSD^−0.119 × USDCAD^0.091 × USDSEK^0.042 × USDCHF^0.036`.
- **[B-corrected] Correlation numbers.**
  - A's "−0.915 to −0.93 on daily returns from other vendors": the −0.932 figure (CONVEX) is EURUSD vs the **Broad Trade-Weighted Dollar**, not DXY. By year: 2024 −0.82, 2025 −0.905, 2026 −0.918.
  - Forex.com's −0.97 for EURUSD vs DXY remains a vendor figure (weak).
  - **[B-new]** EURUSD–GBPUSD mean 60-day correlation 0.79 (FXStreet, Sep 2026). A measured 6E–6B intraday ρ at 0.86–0.90.
- **Pitfall [A✓].** EUR is 57.6% of DXY, so EURUSD vs DXY largely compares EURUSD with itself. GBPUSD or USDCHF carry more independent information.
- **[B-new] Trading-hours pitfall.** DXY (ICE futures, or a computed index) and spot FX keep different hours and sessions. Unaligned bars must freeze the state (`bAl`, section 4).

### 1.5 Correlation regime gate [A✓, extended]
- **Algorithm.** `ρ = ta.correlation(rA, rB, 100)` on time-aligned 1-bar log returns. When |ρ| < 0.5, the state is frozen; when ρ < −0.5 in Auto mode, the pair is treated as inverse.
- **A's measured ρ** (5m / 15m / 1h, rolling-100 10th percentile in brackets):
  - ES–NQ 0.96 (0.92) / 0.96 / 0.97 (0.88);
  - ES–YM 0.91 (0.75) / 0.92 / 0.90 (0.64);
  - NQ–YM 0.81 (0.53) / 0.82 / 0.81 (0.37);
  - ES–RTY 0.89 (0.70) / – / 0.86 (0.54);
  - GC–SI 0.78 (0.63) / 0.80 / 0.22* (the 1h file is broken through 2025);
  - 6E–6B 0.86 (0.76) / 0.89 / 0.90;
  - MBT–MET 0.82 (0.69) / 0.87 / 0.90.
- **[B-new] Why the gate matters: correlations move with the market.**
  - Karami, Benichou, Benzaquen & Bouchaud (2019; 84 futures 2009–19): past up-trends reduce instantaneous correlations and past down-trends increase them.
  - Tóth & Kertész (2005): cross-correlations and lead-lag between stocks have drifted over decades as markets became more efficient.
  - A fixed |ρ| gate on a rolling window is the minimum; showing ρ in the panel lets the user see a decoupled pair, such as NQ–YM in a tech-led rally.

### 1.6 PSP: precision swing point (candle-colour divergence) [A✓]
- **Definition.** At a swing or sweep bar, the correlated assets close in opposite colours; some versions also require a pin bar. Implementations differ on how a doji counts.
- **Evidence (A).** 1-ATR race 50.4% (PSP) vs 49.8% (no PSP), n = 6,039 / 41,481, CI of the difference [−1.4, +2.7] pp. Within SMT events: 49.8% vs 49.6%. Grade: none.

### 1.7 [B-new] Hidden SMT (close-based)
- **Definition** (TradingFinder "Hidden SMT Divergence ICT 01"): the same as 1.1, but on **closing** prices. Bearish: A's closes make a higher high while B's closes make a lower high.
- **Evidence.** None found; this is a vendor's construct, not ICT's own material.
- **B's reasoning.** In A's study the engine's raid-close classes (close back inside vs close beyond, section 1.13) carry no reversal information, and neither does wick SMT. A close-based variant has no evidence of doing better. Not recommended.

### 1.8 [B-new] FVG SMT ("SMT-Fill")
- **Definitions:**
  - `thomas-quant/SMT` `check_fvg_smt`: one asset enters its FVG while the pair fails to.
  - "SMT-Fill [Oracle]": FVGs that form at the same time on correlated assets. It flags when one asset touches or fills its gap and the other does not, with "touch", "full fill" and further variants, and an auto triad. It is described as a narrative tool, not a signal.
  - "SMT Fill by DukeSong" reads the non-filling asset as a "strong sign of trend continuation".
- **Evidence.** None (no statistics published).
- **Engine relevance.** It is the PD-array analogue of the sister state (twin FVGs). The same twin machinery could carry it later. Not proposed until the pool-level effect is confirmed by the ledger.

### 1.9 Triad SMT [A✓ numbers, B-corrected grade]
- **Definition.** ES/NQ/YM: one market disagrees with the other two.
- **A's numbers.** These are the A-style fresh-event lifts without own-path controls: one sister swept 1.046 [1.010, 1.081], n = 4,286; both swept 1.062 [1.018, 1.108], n = 1,757. The CIs overlap.
- **B's grade.** The fresh effect of a single sister disappears under own-path controls (section 2.3). The triad increment is therefore unproven. Grade lowered from weak to **none**, and the proposal is dropped.

### 1.10 SMT at key levels and in killzones [A✓]
- **PDH/PDL sweeps** (922 events, Jan–Apr 2026):
  - 1-ATR reversal: SMT 44.0% vs joint 44.8% (CI [−15, +14] pp).
  - 2-ATR reversal: SMT 41.6% vs joint 59.2% at g = 0; 46.9% vs 50.3% at g = 1; 46.1% vs 52.7% at g = 3. If anything, SMT sweeps reverse less.
- **By killzone** (1-ATR reversal, SMT vs joint):

  | Killzone | SMT | Joint | CI of difference |
  |---|---|---|---|
  | NY AM | 44.3% | 48.4% | [−8.6, +0.1] |
  | London | 51.0% | 48.4% | [−1.2, +6.7] |
  | Asia | 49.7% | 50.7% | [−5.6, +3.5] |
  | NY PM | 52.2% | 51.1% | [−5.1, +5.9] |
  | Off-killzone | 50.1% | 51.6% | [−4.1, +1.7] |

- **"Two-stage crack in correlation"** (one crack is insufficient): no data.
- Grade: none.

### 1.11 Lead-lag and relative strength [A✓, extended]
- **Academic, microstructure scale:**
  - Huth & Abergel (2014, *Quantitative Finance*; arXiv 1111.7103): strongly asymmetric tick-level cross-correlations; the liquid future leads stocks.
    - Forecasting the lagger's next mid-quote move from the leader's past is right **60.3% / 63.6%** of the time, against 56.7% / 59% using the lagger's own autocorrelation.
    - All profit is lost to the spread (−2.73 / −3.44 bp per trade), and accuracy decays as the time scale grows.
    - **Lead-lag is stronger for larger leader moves** (thresholded cross-correlation roughly doubles from θ = 0.5 to 3 ticks).
  - Dobrev & Schaumburg (2018): cross-market leadership at milliseconds.
  - Li, Chen & Liu (2025, arXiv 2501.03171): a "lead-lag spread" between near and far CFFEX index futures predicts the leader's own returns through negative feedback (tick scale).
  - Basnarkov et al. (2019, arXiv 1906.10388): 1-minute FX lead-lag is mostly absent, with a few significant pairs.
  - Maier-Paape & Platen (2015, arXiv 1504.06235): the timing of matched swing extremes, a direct geometric analogue of SMT twins, is synchronous for most strongly correlated FX, commodity and index pairs. A few pairs show a significant non-zero phase shift.
- **[B-new] At 1-minute-plus bars, the cross-asset content that survives is small.**
  - B's continuous pair residual (B's 12-bar move minus A's, in own-ATR units, signed toward the pool) adds +0.014 [−0.004, +0.031] logit. That is not significant.
  - B's overshoot beyond its twin adds +0.044 [−0.025, +0.114].
- **Practitioner relative-strength rule** ("long the strongest, short the weakest"): no quantitative support [A✓]. B's data shows that a laggard's untaken twin is slightly **more** likely to be hit (persistent state), not a sign of weakness that will fail.

### 1.12 Background theory [B-corrected grades]
- **Dow Theory "confirmation"** (industrials and transports must confirm each other) is SMT's ancestor.
  - Cowles (1934) judged Hamilton's record harshly.
  - Brown, Goetzmann & Kumar (1998, *J. Finance* 53(4):1311–1333) re-analysed it: Hamilton's calls over 1902–29 yielded positive risk-adjusted returns, with a significant 40-day mean-return difference after bull vs bear calls.
  - This tests Hamilton's editorial calls, **not** the confirmation rule in isolation. No peer-reviewed isolated test of non-confirmation was found. Recent informal backtests find little short-term information in transports.
  - Grade: **weak** for the confirmation rule. A graded the concept strong.
- **Pairs-trading convergence.**
  - Gatev, Goetzmann & Rouwenhorst (2006, *RFS* 19(3):797–827): up to about 11% annualised excess returns, 1962–2002, daily equity pairs.
  - Do & Faff (2010, *FAJ* 66(4):83–95): profitability kept falling to 2009; up to 70% of the decline is due to worsening arbitrage risks. It is still strong in prolonged turbulence.
  - Divergences between matched assets tend to close at daily-to-monthly horizons, but the literature does not say which leg moves.
  - Grade: strong for the daily equity-pair phenomenon; **n/a** for intraday SMT.

### 1.13 Raid-close classification (hold = continuation, reject = reversal) [B-corrected]
- **Engine rule** (L1579–1582): `evt = close > lv.top ? +1 : close < lv.price ? −1 : 0` for BSL (mirrored for SSL), weighted by tier, decayed by `liqHL` (L1535), with `wL = 0.30` in D (L1894).
- **A's claim:** the primary sweep-reversal signal, separating the next-liquidity side by 11–15 pp. Keep it.
- **[B-corrected]** That 11–15 pp gap is in the "nearest opposite pool vs next pool beyond" race, which depends on where the close sits. In the geometry-neutral 1-ATR race, A's own events give:
  - L3 H12 g0: reject 50.3%, hold 50.3%, mid 50.5%;
  - L3 H12 g1: 50.4%, 49.5%, 49.4%;
  - L5 H30 g1: 50.2%, 50.1%, 49.2%.
  - Logit reject-vs-mid +0.038 [−0.038, +0.113].
- The class carries no reversal information. This agrees with `ict_liq.final.md` §1 (B7, X2, X3) and its proposal ICT-9: neutral REJECT, HTF-conditioned HOLD.
- Grade: moderate (against the reversal reading).

### 1.14 [B-new] Own-path reach features: range burst and wick proximity
Not SMT, but this is what A's "sync lift" was mostly measuring.
- **Range burst:** `vr = mean(TR[0..2]) / ATR14`.
  - Distribution on intraday pool-bars: p10 0.59, median 0.90, p90 1.36.
  - Bursts (vr > 1.25, 15% of bars) lift hit rates 1.13× at H12 and 1.075× at H30; calm bars (vr < 0.8, 35%) give 0.93× / 0.94×, distance × timeframe matched.
  - The effect is monotone in every distance bin. At 2–3 ATR, H12: 24.5% calm, 28.4% normal, 32.6% burst.
  - Logistic coefficient +0.16 to +0.35 per unit of vr, depending on the distance specification.
- **Wick proximity:** how close the last 3 bars' extreme came to the pool, relative to the close distance. +0.09 [+0.04, +0.15] logit per ATR with continuous distance terms.
- **Mechanism.** ATR14 and the engine's 50-bar close-to-close σ (`potSig`, L916) lag a burst, so near-term reach in ATR units is understated during bursts and overstated in calm.
- **Relation to other lenses.** This complements the time-of-day volatility clock that `quant_pot.final.md` and `ict_time.final.md` (G1) propose; bursts partly cluster at opens.

---

## 2. Evidence: numbers and sources

### 2.1 Public quantitative studies (all re-read by B)

| Study | Data | Definition | Result | Grade |
|---|---|---|---|---|
| `thomas-quant/mss-research` README (figures regenerated 2026-09-29, after two labelling fixes) [A✓] | ES/NQ 1m, 5m, 15m: 141,382 / 30,819 / 11,078 SMT rows | k = 1 swings; forward return labelled on the sweeping asset; flat outcomes excluded | Win % at 5/15/30/60 bars: 1m 51.8/51.4/51.0/50.8; 5m 50.6/50.2/50.1/49.8; 15m 50.5/49.7/50.3/49.5; mean −0.93 to +0.19 bp. The author: no intervals; nominal n overstates the information; "unresolved, not a negative result". **[B-new]** The same README documents the 55–62% → 49–51% look-ahead artifact for divergences. | moderate |
| Genjutsu Kai v4 README and Pine tooltips [A✓, all quotes found] | NQ–ES, NQ–YM, ES–YM, RTY–ES 1m, 2018–26; locked test 2025–26 | 30m, 1H and opening-range interval SMT; 2-minute grace; auto minimum lag | "Fading the leader's take won 47–51% of 1σ races in every pair and session (88 tests, none beyond chance against matched controls)". 53–64% held; sync-odds AUC 0.85 (0.81–0.90 by session). Roll-week fade 54% vs 49% (2018–24) and 58% on 30 test days: "one head out of 635 fished", a candidate, not a rule. | moderate |
| `charisjv19/intermarket-divergence-scanner` `backtesting_toolkit/entry_variants.md` [A✓] | MES/MNQ 1m, six windows, live-achievable fills | Walk-back wick-break SMT, 15m bias, FVG entry | v8.7 n = 675, E −0.095 R, PF 0.852; v8.8 n = 597, E −0.172 R, PF 0.754; v8.9 n = 596, E −0.162 R, PF 0.767. Paired day-block CIs on the limit-fill variants contain 0. | moderate |
| MQL5 blog "SMT divergence tested: gold and silver, BTC and ETH, 216 tests" | XAU/XAG, BTC/ETH | n/a (page unreachable to both researchers) | Snippet: "9 out of 108 is not far from 5", i.e. hits at the false-positive rate | weak |
| Vendor claims ("70%+") | undisclosed | undisclosed | The Right Trader and Velotrade state that no verified win rate exists; WebSearch also found none | none |

### 2.2 Q1: does SMT at a sweep predict reversal or the next liquidity? (A's study, re-analysed by B)
- **Data.** CME futures OHLC (github.com/axb0306/cme-futures-ohlc):
  - 1h Mar 2025–Apr 2026: ES, NQ, YM, RTY, GC, SI;
  - 5m and 15m Jan–Apr 2026: the same symbols;
  - 6E/6B Mar–Apr 2026; MBT/MET Feb–Mar 2026;
  - 14 orientations in all.
- **Method.**
  - Pivots L = 3 or 5. The twin is B's extreme within ±2 bars and must be intact at confirmation.
  - Sweep = first strict trade-through within 300 bars. Decision bar = sweep + g; g = 1 also delays B by one bar (Pine).
  - Event types: **smt** (B has not taken its twin), **joint** (B took it on the same or a later bar), **blead_then_a** (B took it first).
  - Outcomes from the decision close:
    - race1: −1 ATR vs +1 ATR first, within 4H;
    - nextLiq: the nearest live opposite pivot pool vs the next live pool beyond the sweep extreme, within 5H.
  - CIs: Wilson for rates; day-cluster bootstrap for differences.

| Config | SMT race1 (rev) | Joint race1 | Δ CI (pp) | SMT nextLiq (opp first) | Joint | Δ CI (pp) |
|---|---|---|---|---|---|---|
| L3 H12 g0 | 50.5% (n 16,258) | 50.8% (16,187) | [−2.2, +1.5] | 39.0% | 37.0% | [−0.2, +4.0] |
| L3 H12 g1 + delay | 49.7% (12,951) | 50.7% (19,835) | [−2.8, +0.7] | 46.2% | 42.9% | [+1.2, +5.3] |
| L5 H12 g0 | 50.1% (9,878) | 50.8% (8,486) | [−3.5, +2.0] | 35.4% | 34.8% | [−2.2, +3.0] |
| L5 H30 g0 | 50.1% | 50.8% | [−3.4, +2.0] | 36.6% | 36.5% | [−2.9, +2.6] |
| L5 H30 g1 + delay | 50.1% (8,112) | 51.0% (10,466) | [−2.9, +1.0] | 42.8% | 40.6% | [−0.7, +5.2] |
| Placebo (B shifted 500 bars) | 51.2% | 54.7% | — | 39.4% | 40.4% | — |

- Fixed-horizon sign: 49.6–51.6% in every config. Divergence-magnitude quintiles: 50.2–51.3% race1.
- **[B-new] Is the nextLiq tilt real?** B ran a logistic regression on A's event files with day-cluster SEs. The SMT coefficient for "opposite pool first":
  - L3 H12 g1: raw +0.140 [+0.060, +0.220]. Adding A's overshoot (exA: SMT 0.60 vs joint 1.06 ATR) and the raid class gives **+0.016 [−0.064, +0.096]**. Adding pool-age quintiles too gives +0.085 [−0.006, +0.175] (about +2 pp).
  - L3 H12 g0: raw +0.088 → −0.004 [−0.086, +0.078].
  - L5 H30 g1: raw +0.093 → +0.009 [−0.111, +0.129].
  - Race1 with the same controls: −0.050 [−0.122, +0.021].
  - **Verdict:** no robust reversal or next-liquidity information. At most about +2 pp, and its CI includes 0.
- **Subgroup noise.** FX race1 SMT 46.6% vs joint 54.8%, CI [−13.0, −3.8] (SMT continues more). Crypto nextLiq CI [+5.7, +14.1]. These are opposite signs in small subgroups out of many tests; treat them as noise. Genjutsu ran 88 tests with none significant.

### 2.3 Q2: the "sister-swept" (laggard sync) effect. A's study and B's independent re-test

**A's design and result.**
- Event: B trades through its twin while A's pool is intact. Decision at B's sweep + d (d = 0 or 1), with 0 < distance ≤ 4 ATR.
- Outcome: A takes its pool within H bars.
- Control: intact pools sampled every 3rd bar, matched on distance bin × 3-bar return quintile × 12-bar return tercile (all close-based).

| Config (A; metals 1h excluded) | n | Hit | Expected | Lift [95% CI] | Pools > 1 ATR |
|---|---|---|---|---|---|
| L3 H12, no delay | 14,831 | 62.9% | 58.6% | 1.075 [1.057, 1.092] | 1.176 [1.134, 1.218] |
| L3 H12, 1-bar delay (Pine) | 11,422 | 54.0% | 51.2% | 1.054 [1.033, 1.077] | 1.104 [1.070, 1.140] |
| L5 H12, no delay | 8,986 | 60.2% | 55.2% | 1.090 [1.065, 1.116] | 1.182 [1.136, 1.230] |
| L5 H30, 1-bar delay | 7,082 | 67.7% | 64.9% | 1.043 [1.022, 1.067] | 1.064 [1.032, 1.098] |
| Placebo (B shifted 500) | 15,582 | 43.3% | 42.6% | 1.017 [0.986, 1.047] | 1.009 [0.967, 1.050] |

**[B-new] B's re-test** (`study/smt_b_tools/b_sync.py`, `b_fit*.py`).
- **Data.** The same CME data, written independently, plus daily S&P 500 / Nasdaq Composite 1999–2018 (both orientations).
- **Panel.** Every intact pool-bar (step 2, pool age ≤ 300, 0 < d ≤ 4 ATR): about 428,000 rows at L3 H12 and 287,000 at L5 H30.
- **Sister state.** Known with Pine's 1-bar delay, split by age since the sister's sweep.
- **Controls:**
  - distance bin × timeframe (plus continuous d, d², log d in a robustness run), asset class, ret3, ret12 (A's controls);
  - **plus own-path terms:** `vr` (3-bar mean TR / ATR14) and `nm` (the 3-bar wick extreme's gap to the pool).
- **Errors:** logit with symbol-day clustered SEs.

Δlogit of the sister state, intraday:

| Controls | Fresh (age 0–1) | Persistent (age 2–31) | Old (32+) |
|---|---|---|---|
| L3 H12, A-like | **+0.129 [+0.073, +0.186]** | +0.081 [+0.026, +0.136] | +0.045 [−0.045, +0.136] |
| + range burst (vr) | +0.062 [+0.007, +0.118] | +0.080 [+0.025, +0.135] | +0.026 |
| + wick proximity (nm) | +0.001 [−0.054, +0.056] | +0.078 [+0.023, +0.133] | +0.043 |
| + both | **−0.007 [−0.062, +0.048]** | **+0.078 [+0.023, +0.133]** | +0.035 [−0.057, +0.127] |
| + both, continuous d terms | +0.018 [−0.035, +0.071] | +0.073 [+0.020, +0.126] | — |
| L5 H30, A-like | +0.130 [+0.054, +0.206] | +0.094 [+0.015, +0.172] | −0.046 |
| L5 H30, + both | −0.004 [−0.082, +0.073] | **+0.085 [+0.007, +0.163]** | −0.055 [−0.179, +0.068] |
| **Placebo** L3 H12, + both | −0.007 [−0.081, +0.066] | +0.014 [−0.066, +0.095] | +0.010 |

- **Reproduction of A.** The fresh-event lift under A-like controls is 1.051 (A: 1.054) at L3 H12 and 1.037–1.038 at L5 H30 (A: 1.043).
- **Under own-path controls:**
  - fresh events: lift 0.995 (L3 H12) / 0.998 (L5 H30);
  - persistent state: lift **1.042** (L3 H12, n = 52,355 pool-bars; pools > 1 ATR 1.052) and **1.035** (L5 H30; > 1 ATR 1.039);
  - placebo: 1.006 / 1.000.
- **Finer age bins** (L3 H12, own-path, all data): 0–1 −0.014; 2–3 +0.053; 4–7 +0.071 [+0.007, +0.135]; 8–15 **+0.115 [+0.033, +0.197]**; 16–31 +0.062; 32+ +0.033. The effect builds after the sweep and fades after about 30 bars. There is no front-loaded decay.
- **Persistent lift by asset class** (L3 H12 / L5 H30): metals 1.106 / 1.085; crypto 1.066 / 1.052; FX 1.053 / 1.009; index 1.026 / 1.026. By timeframe (fresh, own-path): 5m 1.015, 15m 1.033, 1h 0.911.
- **Daily S&P 500 / Nasdaq Composite, 1999–2018:**
  - L3 H10: any-age +0.018 [−0.105, +0.141]; fresh −0.047.
  - L5 H20: any-age **+0.297 [+0.149, +0.444]**; fresh −0.306 [−0.605, −0.006].
  - The two pivot lengths disagree, so this is suggestive, not established.
- **Continuous alternatives add nothing:** pair residual +0.014 [−0.004, +0.031]; B's overshoot beyond its twin +0.044 [−0.025, +0.114].
- **Interpretation.**
  - The large "fresh" sister effect is a proxy for the chart's own approach. On the bar the sister sweeps, the chart's wick has just come close to its pool, in a volatility burst. The engine can see both without a second symbol.
  - What the sister adds is a small, persistent tilt: while the sister has taken its matching liquidity and the chart has not, the chart's pool is about 1.5–2 pp more likely to be hit within H bars over the following 2–30 bars. That is consistent with pairs convergence (1.12).
  - Grade: **weak**. The effect is small, the CI lower bounds are close to 0, the samples are 1–13 months (plus a mixed daily result), and it is one dataset.

### 2.4 Sync timing (B leads, chart follows) [A✓; descriptive]

| TF | n | ≤1 bar | ≤2 | ≤3 | ≤6 | ≤12 | ≤30 | Never (300) | Median given sync | Hazard bars 1–4 |
|---|---|---|---|---|---|---|---|---|---|---|
| 5m | 8,394 | 21.2% | 31.1% | 38.0% | 49.4% | 60.9% | 72.9% | 9.3% | 5 (p75 20) | 23, 14, 12, 9% |
| 15m | 2,577 | 22.4% | 32.4% | 39.2% | 50.6% | 60.7% | 73.4% | 8.9% | 5 (p75 22) | 25, 15, 12, 10% |
| 1h | 2,693 | 19.6% | 27.9% | 33.5% | 43.6% | 53.6% | 68.8% | 10.8% | 7 (p75 26) | 22, 12, 9, 7% |

Median lag distance at the sister's sweep: 1.06 ATR (5m), 1.07 (15m), 1.41 (1h).

**[B-corrected]** A used this hazard to set an 8-bar half-life for the boost. The hazard describes when syncs happen. It is not the decay of the *incremental* lift, which section 2.3 measures directly (about 0 at 0–1 bars, a plateau over 2–31). Use the hazard only for an ETA readout.

### 2.5 Evidence grades

| Claim | Grade | Basis |
|---|---|---|
| SMT at a sweep predicts reversal | **against, moderate** | Four independent quantitative sources plus B's geometry controls; none peer-reviewed |
| SMT predicts which pool is taken next | **none** (≤2 pp, CI includes 0) | B's re-analysis |
| Fresh sister sweep raises the chart pool's PoT beyond own-path information | **none** (moderate against) | Own-path controls remove it in both configs |
| Persistent sister state (2–31 bars) raises PoT | **weak**, Δlogit ≈ +0.08 | B's panel, placebo null, consistent sign across classes |
| Range burst / wick proximity raise PoT | **moderate** | Large n, monotone, two horizons, needs only the chart's own data |
| Raid-close class predicts reversal | **against, moderate** | A's events (geometry-neutral race), agreeing with ict_liq |
| PSP; hidden SMT; triad increment; killzone or key-level SMT | none | — |
| DXY composition | strong | ICE methodology |
| EURUSD–DXY ρ ≈ −0.97 | weak | Vendor figure |
| Tick-scale lead-lag exists but is not tradable | strong | Huth & Abergel, peer-reviewed |
| Dow confirmation rule | weak | Tests Hamilton's calls, not the rule |

---

## 3. Engine gap analysis (baseline_v2.pine line refs; checked by B)

| Concept | Status | Where / what differs |
|---|---|---|
| Second-symbol feed | **missing** | All 5 `request.security` calls and the 1 `request.security_lower_tf` call use `syminfo.tickerid`: L923–925 (structure), L939 (HTF FVG), L981 (1H OHLCV), L982 (LTF). 6 of 40 unique `request.*` calls (limitations.md L206). [A✓] |
| Session / back-adjust inheritance for a second symbol | **missing [B-new]** | Not needed today. Without `ticker.inherit`, an ETH-session chart would compare against an RTH or unadjusted sister, misaligning bars and faking sweeps at rolls. |
| SMT at sweep (A leads, B fails) | **missing** | The step 3 sweep loop (L1558–1590) classifies by the chart's close only. Evidence says this costs nothing. [A✓] |
| Raid-close classification → D | **wrong [B-corrected]** | L1579–1582, decay L1535, `wL = 0.30` (L157), D at L1894. REJECT → −1 has no reversal support, even in A's own SMT events (2.2, 1.13). Fix via `ict_liq.final.md` ICT-9; the SMT module must not lean on it. |
| Sister state per pool | **missing** | `Level` (L317–347) and `Ext` (L365–373) have no twin or state fields. `evaluate` (L661–697), `f_potModel` (L1303–1312) and the live PoT (L2063–2067) cannot use it. [A✓; line refs corrected] |
| Twin anchors for key ranges | **missing** | `f_rangeTrack` (L807–833) and `f_sessTrack` (L835–859) track chart data only. MTF pivots are anchored via `f_barAtTime` (L1191–1209). |
| Own-path burst / wick terms in PoT | **missing [B-new]** | `potSig = ta.stdev(chg, potLen)` (L916, potLen 50) and the empirical surface `sUp`/`sDn` (L1061–1062, rows = HTF bias only; bumped at L1531–1532; read by `f_empPoT` L1284–1300) are blind to the last 3 bars' range. The proximity reach (L665) uses the same σ. |
| Inverse correlation (DXY) | missing | — |
| Correlation gate | missing | — |
| Strict sweep (trade-through) | **present** | `touched()` L623–624. [A✓] |
| Killzone affinity | present (other topic) | `f_kzAff` L597. Add no SMT × killzone term (evidence against). |
| Ledger infrastructure | **partial** | The Trial ledger (`f_openTrial` / `f_step` / `f_book`, L1426–1500) grades only the active DOL. `f_raceAdj` (L1367–1371) is the right shrinkage pattern (logit of shrunk hits minus logit of the baseline, prior weight 20). `f_potBase` (L1314–1322) is driftless. **[B-corrected]** A proposed calibrating the sister shift against `f_potBase`. The shift modifies `f_potModel`'s output, so it must be calibrated against `f_potModel` (the model it corrects); otherwise drift and regime credit leak into the SMT shift. |
| Alerts | present, no SMT | L2077–2094: four `alertcondition` plus `alert()` calls. |
| Panel / HUD | present, no SMT | Terminal panel L2289–2434; Clean label L2225; HUD text L2240. |
| PSP, hidden SMT, triad, lag magnitude, FVG SMT | missing; **not recommended** | Evidence none. |

---

## 4. Proposals (best first; 8)

All proposals keep the engine non-repainting:
- structural updates inside `barstate.isconfirmed`;
- the new request reads `[1]` with `lookahead_on` at `timeframe.period`. The docs list both conditions as safe: "includes a *historical offset* (e.g., `close[1]`)" and "represents the same timeframe as that of the chart" (concepts/other_timeframes_and_data.md L204–205, L1398).

### SMT-1 · `smt-ownpath-burst`: condition the empirical PoT surface on the 3-bar range burst [B-new] (P1, effort S, evidence moderate)
- **Why.** This is the part of the "laggard sync" signal that needs no second symbol, and it is much larger than any cross-asset effect:
  - bursts (vr > 1.25) give 1.13× / 1.075× hit rates (H12 / H30); calm bars (vr < 0.8) give 0.93× / 0.94×;
  - it is monotone in every distance bin;
  - it applies on every chart, with no request.
- **Spec.**
  - SERIES, after L917: `float vr = ta.sma(ta.tr(true), 3) / nz(atr, 1e-9)`, and `int vrS = vr < 0.8 ? 0 : vr <= 1.25 ? 1 : 2` (thresholds = the study's terciles of practical interest).
  - STATE, L1061–1062: `sUp`/`sDn` become `array.new<int>(9 * NB1, 0)`; row = `biasRow * 3 + vrS`.
  - ENGINE step 0 (L1527–1532): `int vH = vrS[H]` (state at the window start); `f_bump(sUp, (bH + 1) * 3 + vH, …)`, `f_bump(sDn, (1 - bH) * 3 + vH, …)`.
  - `f_empPoT` (L1284): three-level fallback.
    1. Use row `r*3 + vrS` if `n ≥ nMin`.
    2. Else pool the three burst rows of the same bias, **scaled by the burst ratio**. Pooled surface `p_bias`, and per-burst-state hit ratios `k_v` from the bias-pooled counts at the same u. Simplest version: `p = p_bias × clamp(kv, 0.85, 1.20)`, with `kv` prior [0.93, 1.00, 1.10] when data are thin.
    3. Else all rows.
  - Analytic fallback and proximity reach (L665, L1304): scale σ by `math.pow(clamp(vr, 0.5, 2.0), 0.35)`. The exponent is a prior, refit once the surface has data.
  - Memory: 9 × 61 ints per side.
- **Coordinate with** the time-of-day volatility clock (`ict_time.final.md` G1; `quant_pot.final.md`). Bursts cluster at opens, so if both are adopted, condition on burst *within* the clock (a 3 × clock-state surface, or the clock-scaled σ plus the burst ratio).
- **Risk.** Thinner rows during warm-up, handled by the fallback. Bursts are partly the time of day, so there is some double counting if both features are added naively.
- **Measurable** through the existing EDGE / Brier readouts.

### SMT-2 · `smt-core`: optional correlated-symbol feed, twins and sister state machine (P2, effort M, evidence weak; infrastructure for SMT-3 to SMT-8) [A, revised by B]
**Inputs** (new `const string G_SMT = "SMT · Correlated Symbol"`; every input `display = display.none`, per the overhaul's legend finding):
```pine
bool   smtOn     = input.bool(false, "Enable SMT (correlated symbol)", group = G_SMT, display = display.none)
string smtSymIn  = input.symbol("", "Compare With (blank = auto pair)", group = G_SMT, display = display.none)
string smtCorr   = input.string("Auto", "Correlation", options = ["Auto", "Positive", "Inverse"], group = G_SMT, display = display.none)
float  smtRhoMin = input.float(0.50, "Min |correlation| (100 bars)", minval = 0.0, maxval = 1.0, step = 0.05, group = G_SMT, display = display.none)
int    smtW      = input.int(2, "Twin Window (± bars)", minval = 0, maxval = 3, group = G_SMT, display = display.none)
string smtMode   = input.string("Sync", "SMT Use", options = ["Sync", "Display only", "Reversal (ledger-gated)"], group = G_SMT, display = display.none)
```
`input.symbol("", …)` is verified to compile: Genjutsu Kai L33, an open-source v6 script.

**Auto pair [B-corrected].** A's map hard-coded `CME_MINI:` for MES, MNQ, MYM and M2K. Those trade on `CME:` / `CBOT:` on TradingView, so the auto pick would silently return `na`. A's map also broke single-contract charts (ESZ2026). Fix: keep the chart's own prefix and contract suffix, swap the exchange only for CBOT-listed Dow contracts, and use string replacement for spot pairs:
```pine
f_smtRoot(string r) =>
    switch r
        "ES"  => "NQ"
        "NQ"  => "ES"
        "YM"  => "ES"
        "RTY" => "ES"
        "MES" => "MNQ"
        "MNQ" => "MES"
        "MYM" => "MES"
        "M2K" => "MES"
        "GC"  => "SI"
        "SI"  => "GC"
        "6E"  => "6B"
        "6B"  => "6E"
        => ""
string smtRt  = f_smtRoot(syminfo.root)
string smtPfx = (syminfo.root == "YM" or syminfo.root == "MYM") ? str.replace(syminfo.prefix, "CBOT", "CME") : syminfo.prefix
string smtAut = smtRt != "" ? smtPfx + ":" + smtRt + str.replace(syminfo.ticker, syminfo.root, "") :
  str.contains(syminfo.tickerid, "BTC") ? str.replace(syminfo.tickerid, "BTC", "ETH") :
  str.contains(syminfo.tickerid, "ETH") ? str.replace(syminfo.tickerid, "ETH", "BTC") :
  str.contains(syminfo.tickerid, "EURUSD") ? str.replace(syminfo.tickerid, "EURUSD", "GBPUSD") :
  str.contains(syminfo.tickerid, "GBPUSD") ? str.replace(syminfo.tickerid, "GBPUSD", "EURUSD") : ""
string smtSym = smtSymIn != "" ? smtSymIn : smtAut
```
- `syminfo.prefix` and `syminfo.root` are simple strings (reference/syminfo.md L148, L467).
- `str.replace(source, target, replacement, occurrence = 0)` (reference/str.md L349–364).
- `syminfo.root` returns the ticker for non-futures.

**Feed [B-corrected: `ticker.inherit`, no `open`, chart symbol when off]:**
```pine
bool   smtReq = smtOn and smtSym != ""
// inherit the chart's session (RTH/ETH), back-adjustment and settlement-as-close, so bars align and rolls match
string smtTk  = smtReq ? ticker.inherit(syminfo.tickerid, smtSym) : ""
[bHr, bLr, bCr, bTr] = request.security(smtTk, timeframe.period, [high[1], low[1], close[1], time[1]],
  lookahead = barmerge.lookahead_on, ignore_invalid_symbol = true)
bool  bAl  = smtReq and not na(bTr) and bTr == time[1]        // B's previous bar is the chart's previous bar
float rA   = bAl and bAl[1] ? math.log(close[1] / close[2]) : na
float rB   = bAl and bAl[1] ? math.log(bCr / bCr[1]) : na
float smtRho = ta.correlation(rA, rB, 100)                  // na values are ignored (reference/ta.md L491-510)
var int smtSign = 0
int  sgnNow  = smtCorr == "Inverse" ? -1 : smtCorr == "Positive" ? 1 : nz(smtRho) <= -smtRhoMin ? -1 : nz(smtRho) >= smtRhoMin ? 1 : 0
bool smtFlip = sgnNow != 0 and smtSign != 0 and sgnNow != smtSign
if sgnNow != 0
    smtSign := sgnNow
bool  smtLive = bAl and smtSign != 0 and math.abs(nz(smtRho)) >= smtRhoMin
float bHn = not bAl ? na : smtSign < 0 ? -bLr : bHr         // B's previous-bar extremes, sign-normalised
float bLn = not bAl ? na : smtSign < 0 ? -bHr : bLr
```
- `ticker.inherit(from_tickerid, symbol) → simple string` "including extended session, dividend adjustment, … back-adjustment, settlement-as-close" (reference/ticker.md L34–40).
- `request.security`: "Use an empty string or `syminfo.tickerid` to request data using the chart's symbol" (reference/request.md L212). With the module off, the request is inert.
- The tuple has 4 elements; the unique request count becomes 7 of 40.

**Types.** Append defaulted fields, so the positional `Ext.new` at L1224 stays valid:
- `Level` (after L347): `float twin = na`, `int sis = 0`, `int sisBar = na`. `sis` values: 0 untracked, 1 twin intact, 2 sister swept first (the chart lags), 3 chart swept and the sister failed (SMT).
- `Ext` (after L373): the same three fields.

**Twins for chart swings, O(1) [B-new; replaces A's 450-step loop for this source].** The pivot bar is T = `bar_index − pivLen`. B's bar k sits on chart bar k+1. B's bars [T−w, T+w] therefore end at chart offset `pivLen − smtW − 1`, which needs `smtW ≤ pivLen − 1`. Global scope, every bar:
```pine
int   smtWE  = math.min(smtW, pivLen - 2)                    // keeps one post-window bar
int   twLen  = 2 * smtWE + 1
int   twOff  = pivLen - smtWE - 1
float twHi   = ta.highest(bAl ? bHn : -1e10, twLen)[twOff]
float twLo   = ta.lowest(bAl ? bLn : 1e10, twLen)[twOff]
bool  twOk   = math.sum(bAl ? 1 : 0, twLen)[twOff] == twLen   // every twin bar aligned
float postHi = ta.highest(bAl ? bHn : -1e10, twOff)          // B bars after the window (twOff >= 1)
float postLo = ta.lowest(bAl ? bLn : 1e10, twOff)
```
- At L1761 (new BSL): `nh.twin := smtLive and twOk ? twHi : na`; `nh.sis := na(nh.twin) ? 0 : postHi > twHi ? 2 : 1`; `nh.sisBar := nh.sis == 2 ? bar_index - 1 : na`.
- Mirror at L1773 for SSL.
- `math.sum` exists (reference/math.md L412). History references on built-in results (`ta.highest(...)[k]`) are standard.
- The ±1e10 sentinels never reach a twin, because `twOk` gates them.

**Twins for STF/HTF pivots and key ranges** [A, kept]:
- `f_twinState(b0, b1, hi)` loops over chart bars `[b0, b1]`, reading `bHn[bar_index − k − 1]`, capped at 450 back (max_bars_back = 500, L31), and only at level birth.
- Windows:
  - STF/HTF pivots: `[a − smtW, a + r − 1 + smtW]`, with `a = f_barAtTime(pivT, anchorMax)` and `r = math.round(f_tfRatio(tf))`.
  - PDH/PDL, PWH/PWL, sessions: `f_rangeLag(inPrev, emit, bHn, bLn)`. It folds the `[1]`-shifted B bar into the old period before emitting, because on the first bar of a new period the shifted B bar still belongs to the old one.
- Extend `f_pushExt` (L1211) with `float tw, int st, int sb`; on a duplicate, keep the outermost twin.
- Copy `twin` / `sis` / `sisBar` on registry re-entry (L1846–1851).
- In `f_mergeAt` (L1111), on an outer print, keep the outermost twin. Note that `ict_liq.final` found the outer branch nearly dead for chart pivots.

**State update.** A new step "3a", inside `barstate.isconfirmed`, before the step 3 loop (L1558). Repeat for `extReg` at step 4:
```pine
    if smtLive
        for lv in pool
            if lv.isLiquidity() and lv.sis == 1 and (lv.side == 1 ? bHn > lv.twin : bLn < lv.twin)
                lv.sis    := 2
                lv.sisBar := bar_index - 1      // B's sweep bar
    if smtFlip
        // the sign re-latched (Auto): every twin is in the wrong space, so untrack (sis := 0) pools and registry
```

**Chart-led sweep (SMT vs joint) [A, kept].**
- In the step 3 sweep branch (L1579): if `lv.sis == 1`, push `Pend{side, twin, bar, close, atr}`.
- On the next confirmed bar, B's sweep-bar data has arrived. If B took its twin, the record is **joint**; otherwise it is **SMT**.
- This one-bar deferral is what keeps it non-repainting. Pending records feed only the ledger (SMT-3) and alerts (SMT-6).

**Cost.** One request; about 2 × pool-size comparisons per confirmed bar; loops only at the birth of MTF and key levels.

**Risks.**
- Auto pairs can still miss on exotic feeds. The panel then shows "SMT: no data", and the user can override.
- Pairs with different hours freeze the state (`bAl` false). This is correct behaviour, but it should be visible in the panel as an aligned-bar %.

### SMT-3 · `smt-ledger`: calibrate the sister shift against the engine's own PoT; SMT-vs-joint reversal race (P2, effort M, evidence weak) [A, revised by B]
- **Records (sister):**
  - When a pool or registry entry is intact with 0.25 < d ≤ maxATR, it opens `SisT{lvId, side, edge, bar0, pM, bkt}`:
    - at sister age 0 (bucket F, fresh);
    - and again at age 2 (bucket P, persistent).
  - `pM = f_potModel(d, side, potMu·side)` is the engine's PoT **before** any SMT shift [B-corrected; A used `f_potBase`].
  - Resolve as hit (`side == 1 ? high > edge : low < edge`) or expired at `bar_index − bar0 ≥ H`.
  - Book `n_b += 1`, `K_b += hit`, `P_b += pM`. Cap 64 open records.
- **Learned shift per bucket** (the `f_raceAdj` pattern, shrunk toward a prior rather than 0):
```pine
f_sisBeta(int b, float prior) =>
    float n  = smtSt.get(3 * b)
    float pb = n > 0 ? smtSt.get(3 * b + 2) / n : 0.5
    float pp = f_sigm(f_logit(f_clamp(pb, 0.02, 0.98)) + prior)            // prior-implied hit rate
    n > 0 ? f_clamp(f_logit(f_clamp((smtSt.get(3 * b + 1) + 50.0 * pp) / (n + 50.0), 0.02, 0.98)) - f_logit(f_clamp(pb, 0.02, 0.98)), -0.2, 0.3) : prior
```
  - Priors: P bucket **+0.08** (sections 2.3 and 2.5). F bucket **0.0** when SMT-1 is on, **+0.10** when it is off. The SMT-1-off value is the A-like fresh effect, which is own-path information the engine would otherwise miss.
  - The prior weight of 50 records reflects the small effect.
- **Race records (reversal):**
  - Each resolved Pend (SMT or joint) starts a 1-ATR race from the decision close; reversal = −1 ATR first.
  - Book per arm. The z-score uses the 2H-block cluster variance from `f_book` (L1463–1469).
- **Storage and placement.** `var array<float> smtSt = array.new<float>(12, 0.0)` plus small `SisT` / `RaceT` types. Place them after `f_book` (~L1500), after `f_potModel` (L1303).
- **Panel:** `SYNC P Δ+0.08 (n 212, z 1.1) · SMT-REV 49% (n 120) vs JOINT 51% (n 180)`.
- **Risk.** Small n on higher timeframes; overlapping records share price paths (hence the cluster variance and the prior).

### SMT-4 · `smt-state-shift`: small persistent PoT logit shift for sister-swept pools (P2, effort S, evidence weak) [A's "sync boost", re-shaped by B]
- **Window [B-corrected].** A used decay from the sweep bar with an 8-bar half-life. B's measured age curve gives a plateau:
```pine
f_sisW(int age) =>
    age < 2 ? 1.0 : age <= 31 ? 1.0 : age <= 47 ? (47.0 - age) / 16.0 : 0.0
// bucket: age < 2 uses f_sisBeta(0, smtFreshPrior), else f_sisBeta(1, 0.08)
```
- **PoT** (LIVE READOUTS, after L2067):
  - `if smtOn and smtMode != "Display only" and not na(activeLv) and activeLv.sis == 2 and not sweptNow`, compute `age = bar_index - activeLv.sisBar`.
  - Then `activePoT := math.min(0.95, f_sigm(f_logit(f_clamp(activePoT, 0.01, 0.99)) + beta * f_sisW(age)))`.
  - Uses the existing `f_logit` / `f_sigm` (L484 / L488).
- **Score** (step 17, L1938–1948, next to `f_kzAff` / `f_calMult`):
  - `if lv.isLiquidity() and lv.sis == 2`: `lv.mult *= f_clamp(1.0 + 0.5 * beta * f_sisW(bar_index - lv.sisBar), 0.95, 1.10)`.
  - At β = 0.08 that is ×1.04: it breaks near-ties only, matching the measured +1.5 to +2 pp.
- **Nothing is added to D.** D drives side selection and the flip alert, and the cue is target-specific.
- **Risk.** The effect is close to the noise floor. The ledger can shrink it to 0 on charts where it does not hold.

### SMT-5 · `smt-no-reversal-default`: keep SMT out of D and the raid classification; ledger-gated reversal reading (P2, effort S, evidence moderate) [A, tightened by B]
- **Sync mode (default).** A chart-led SMT never touches `liqEvt` (L1579–1582) or D (L1892–1895).
- **Coordinate with ICT-9** (`ict_liq.final.md`): REJECT becomes neutral there. The ICT "SMT = reversal" reading is then absent from D entirely, which is what both lenses' evidence supports.
- **"Reversal (ledger-gated)" mode** [B-tightened thresholds]:
  - Add `evt = −side × tier × 0.5` at Pend resolution **only** when all of these hold:
    - SMT-3's race shows SMT-REV − JOINT-REV > 0 with **z ≥ 2.5**;
    - **n ≥ 100 per arm**;
    - the sign is the same in both halves of the record history.
  - The stricter z reflects the number of SMT variants users can try. Genjutsu found 0 of 88 tests beyond chance.
  - Otherwise the panel says: "ICT reversal: not supported on this chart (z = 0.4, n 63/91)".

### SMT-6 · `smt-alerts-ux`: alerts, Clean tag, Terminal rows, marks (P3, effort S, evidence none: UX) [A, wording corrected]
- **Alerts.** Two `alertcondition`s after L2093, plus `alert()` calls at bar close.
  - **"SMT · Sister Took Liquidity"**: a pool on the draw side, or the active DOL, turns `sis = 2`. Message: `"DOL Engine ▸ NQ1! took its BSL; ES1! lagging · BSL @ x · sync ETA ~5 bars · PoT +2 pp"`.
  - **"SMT · Divergence at Sweep"**: a Pend resolves as SMT. Message: `"…chart swept BSL, NQ1! failed (SMT) · this chart: SMT-REV 49% vs JOINT 51%"`.
- **Honest wording [B].** Never "reversal expected".
- **Clean style.** Suffix `· SMT↻` on the DOL label when `activeLv.sis == 2`. Tooltip: "NQ1! took its matching high 6 bars ago; this pool is the laggard (PoT +2 pp)". No new table rows, so the reference look is kept.
- **Terminal style.**
  - Row: `SMT  NQ1! ρ .96 · 98% bars aligned · ▲LAG BSL 1.2ATR · ETA 5b`.
  - Accuracy row from SMT-3.
- **Optional marks.** A dashed line from the swept pivot to the sweep extreme, labelled `SMT` or `↻`. At most 12, FIFO like `f_ghost` (L1253). Off by default in Clean.

### SMT-7 · `smt-key-range`: exact interval matching for key-range twins (P3, effort S, evidence weak) [A, kept]
- Optional. Emit a B range twin (PDH/PDL, PWH/PWL, sessions) only when B's interval boundaries equal the chart's. Add B's `time` and `time_close` to the SMT-2 tuple (still one request), or compare session flags.
- Otherwise leave the twin `na` (`sis = 0`).
- It matters for FX vs DXY and crypto vs CME. The value is correct sister states on the highest-tier pools; there is no new signal (section 1.10).

### SMT-8 · `smt-sync-eta`: sync ETA readout from the live hazard (P3, effort S, evidence moderate as a description) [A, role corrected]
- Record the bars from `sisBar` to the chart's own sweep for synced pools, in an array capped at 300 (like `ttHit`, L1072).
- Show the median as `sync ETA ~5b`. Prior: 5 bars on 5m/15m, 7 bars on 1h (section 2.4).
- **[B-corrected]** Do not use it to set the boost's decay; SMT-4 uses the measured age window.
- Right-censoring biases the ETA short, which is acceptable for an indicative readout.

**Dropped or not proposed** (evidence none, or against):
- triad SMT (A's P8: its increment is the A-like fresh effect, which own-path controls remove);
- PSP;
- hidden (close-based) SMT;
- FVG SMT;
- SMT × killzone reversal weighting;
- divergence-magnitude scoring;
- continuous pair-residual drift (+0.014, not significant);
- the roll-week fade (one fished head out of 635).

---

## 5. Pine v6 feasibility checklist (doc-grounded)
- **Request budget.** "A script can use up to 40 *unique* calls to the functions in the `request.*()` namespace, or up to 64 … Ultimate plan" (writing_scripts/limitations.md L206). The engine has 6; SMT-2 adds 1.
- **Non-repainting.** "The most reliable approach to achieve non-repainting results is to use an `expression` argument that only references past bars (e.g., `close[1]`) while using `barmerge.lookahead_on`" (concepts/other_timeframes_and_data.md L1398). Same-timeframe requests are listed as a safe lookahead case (L205).
  - The sister state therefore updates one bar late (`sisBar := bar_index − 1`).
  - Pend resolution waits one bar.
  - All of it runs inside `barstate.isconfirmed`.
- **`ticker.inherit(from_tickerid, symbol)`** returns simple or series string; it inherits extended session and back-adjustment (reference/ticker.md L34–45). Inapplicable modifiers are ignored.
- **`request.security` with `""`** requests the chart symbol (reference/request.md L212). `ignore_invalid_symbol = true` returns `na` instead of halting (request.md L46, the same wording for every `request.*`).
- **`input.symbol(defval, …) → input string`** (reference/input.md L420). An empty default is used by the open-source v6 script Genjutsu Kai (L33).
- **`ta.correlation`**: "`na` values in the `source` series are ignored" (reference/ta.md L491–510).
- **`math.sum`** (reference/math.md L412) and `ta.highest` / `ta.lowest` with a `series int` length. Dynamic history offsets in `f_twinState` are bounded by `max_bars_back = 500` (L31); loops are clamped to 450.
- **No forward references:**
  - feed and twin series in SERIES, after L982;
  - `f_twinState` / `f_rangeLag` in STATE HELPERS, after L1209;
  - ledger helpers after `f_book` (L1500), which follows `f_potModel` (L1303);
  - SMT-1's `vr` before the ENGINE block.
- **Drawing caps.** SMT marks are capped at 12, within the 500 line / 500 label limits.

---

## 6. Reproducibility
- **Data:**
  - `study/smt_data/cme/` (A: sparse clone of github.com/axb0306/cme-futures-ohlc);
  - `study/bias_data/sp500.csv` and `nasdaq.csv` (daily 1999–2018; used by B).
- **A's scripts and outputs** (`study/smt_tools/`):
  - scripts: `smt_study.py`, `smt_report.py`, `smt_keylevel.py`, `smt_strat.py`, `smt_timing.py`, `smt_triad.py`;
  - outputs: `out_*.txt`, event pickles `E_*.pkl`, pool pickles `Q_*.pkl`.
- **B's scripts and outputs** (`study/smt_b_tools/`):
  - `b_sync.py`: pooled pool-bar panel builder. Args: dly, shiftB, L, H. Outputs `panel_d{dly}_s{shift}[_L5_H30].pkl`.
  - `b_fit.py` / `b_fit2.py`: logistic models with own-path controls, age bins, residual and overshoot terms. Outputs `fit_L3H12_d1_full.txt`, `fit2_d1_s0_L5_H30.txt`, `fit2_d1_s500.txt`.
  - `b_fit3.py`: decomposition by control set, with persistent-state lifts. Outputs `fit3_L3H12.txt`, `fit3_L5H30.txt`, `fit3_L3H12_s500.txt`.
  - `b_fit4.py`: continuous-distance robustness run.
  - `out_B_extra.txt`: fit4 output, the range-burst tables, the nextLiq geometry re-analysis and the raid-class race.
  - Run with `smt_b_tools/venv/bin/python -I` (numpy, pandas, statsmodels).
- **Limitations:**
  - Intraday samples are 1–3 months (13 months on 1h).
  - Both orientations of each pair are pooled; symbol-day clusters handle the shared days.
  - Pools are plain pivots, not the engine's full pool logic.
  - Panel rows overlap within a pool (step 2), which the clustered SEs absorb.
  - The daily results disagree between L3 and L5.

---

## 7. Sources
**ICT / practitioner definitions**
- LuxAlgo concept page: https://www.luxalgo.com/library/concept/smart-money-technique-divergence.md
- Smart Money gitbook: https://smartmoney.gitbook.io/smart-money-concepts/strategy/ict-smt-divergence
- LuxAlgo SMT Divergences: https://www.luxalgo.com/library/indicator/smt-divergences.md
- Kodexius: https://it.tradingview.com/script/XEfw1eR7-SMT-Divergence-Kodexius
- OutOfOptions: https://my.tradingview.com/script/WMgV6HcH-SMT-Divergences-OutOfOptions
- Two-stage crack: https://it.tradingview.com/script/O74a2z84/
- PSP:
  - https://in.tradingview.com/script/EEKVmlUm-Quarterly-Theory-ICT-03-TradingFinder-Precision-Swing-Points/
  - https://jp.tradingview.com/script/YoCpWBxb-cephxs-fadi-HTF-PSP/
- [B] Hidden SMT: https://in.tradingview.com/script/L1i7v7tR-Hidden-SMT-Divergence-ICT-01-TradingFinder-HSMT-SMC-Technique
- [B] SMT-Fill: https://de.tradingview.com/script/oPaPzqEG-SMT-Fill-Oracle/ and https://in.tradingview.com/script/hMuxcT35-SMT-Fill-by-DukeSong (search summaries)
- No verified win rate:
  - https://therighttrader.com/learn/smart-money-concepts/smt-divergence
  - https://velotrade.com/blog/smt-divergence
  - https://www.eltraderfinanciado.com/en/blog/smt-divergence

**Quantitative SMT studies and code** (read in full by A and re-read by B; concepts only, no code copied)
- https://github.com/thomas-quant/mss-research (README: SMT win rates; the look-ahead and flat-outcome fixes)
- https://github.com/thomas-quant/SMT (micro, swing and FVG SMT; invalidation = failing asset crosses its reference)
- https://github.com/unclehk2000/genjutsu-kai (README; Pine L33, L36, L55, L75, L76, L144–157: 88 tests at 47–51%, held 53–64%, sync-odds coefficients, AUC 0.85, grace, minimum lag, roll week)
- https://github.com/charisjv19/intermarket-divergence-scanner (`backtesting_toolkit/entry_variants.md` L35–37, L55)
- https://github.com/Gregorius-XV/GXV-SMT-Divergences
- https://github.com/samuelharting/bandz-smt-ssmt-divergence
- https://github.com/DeolinNaidoo/TradingView-Larper-Indicator
- https://www.mql5.com/en/blogs/post/780472 (snippet only)

**DXY / FX**
- ICE USDX: https://www.ice.com/publicdocs/ICE_USDX_Brochure.pdf
- Formula: https://en.wikipedia.org/wiki/U.S._Dollar_Index
- Forex.com: https://www.forex.com/ie/news-and-analysis/so-you-want-to-trade-the-dxy-eurusd-usdchf/
- [B] CONVEX (EURUSD vs Broad TWD): https://convextrade.com/compare/eurusd-vs-dxy/correlation
- [B] FXStreet (EURUSD–GBPUSD 0.79): https://www.fxstreet.com/analysis/five-market-relationships-traders-rely-on-which-ones-still-work-202609091047

**Academic**
- Brown, Goetzmann & Kumar (1998), *J. Finance* 53(4):1311–1333: https://viking.som.yale.edu/?p=86 and https://econpapers.repec.org/RePEc:ysm:somwrk:ysm30 (Cowles 1934 critique summarised there)
- Gatev, Goetzmann & Rouwenhorst (2006), *RFS* 19(3):797–827: https://econpapers.repec.org/RePEc:oup:rfinst:v:19:y:2006:i:3:p:797-827
- [B] Do & Faff (2010), "Does simple pairs trading still work?", *FAJ* 66(4):83–95: https://econpapers.repec.org/RePEc:taf:ufajxx:v:66:y:2010:i:4:p:83-95
- [B] Huth & Abergel, "High frequency lead/lag relationships: empirical facts", arXiv 1111.7103 (*Quantitative Finance* 2014)
- [B] Li, Chen & Liu (2025), lead-lag spread in CFFEX index futures, arXiv 2501.03171
- [B] Basnarkov, Stojkoski, Utkovski & Kocarev (2019), FX lead-lag, arXiv 1906.10388
- [B] Maier-Paape & Platen (2015), lead-lag of matched local extrema, arXiv 1504.06235
- [B] Karami, Benichou, Benzaquen & Bouchaud (2019), conditional correlations in futures, arXiv 1912.12354
- [B] Tóth & Kertész (2005), evolution of cross-correlations, arXiv physics/0506071
- Dobrev & Schaumburg (2018): https://www.atlantafed.org/-/media/documents/news/conferences/2018/1018-financial-stability-implications-of-new-technology/papers/dobrev-schaumburg_high-frequency-cross-market-trading.pdf
- Hayashi & Koike, wavelet / multi-scale lead-lag: arXiv 1612.01232 and 1708.03992

**Pine docs (local mirror, jabez4jc_pinescriptv6)**
- writing_scripts/limitations.md L206
- concepts/other_timeframes_and_data.md L204–205, L1398
- reference/request.md L46, L212
- reference/ticker.md L34–45
- reference/input.md L420
- reference/ta.md L491–510, L696–716
- reference/math.md L412
- reference/str.md L349–364
- reference/syminfo.md L148, L467

**Cross-lens references**
- `study/ict_liq.final.md` (ICT-9: raid mapping)
- `study/bias_dol.final.md` (BIAS-4)
- `study/quant_pot.final.md` (σ / PoT)
- `study/ict_time.final.md` (G1: volatility clock)
