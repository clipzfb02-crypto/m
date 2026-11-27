# Skeptical evaluation: which DOL claims hold, and is the engine's ledger honest? (combined final, researchers A + B)

Domain: which ICT/SMC/liquidity claims have empirical support, which are base-rate or geometry artefacts, and which are
folklore. What a naive model already achieves. Survivorship and look-ahead traps in indicator "accuracy". Multiple testing.
An audit of the engine's accuracy ledger, EDGE z-score, random-level baseline and calibration. Proposals that make the
engine's claims honest and make its choices beat *strong* baselines, not just a random level.

Line numbers refer to `/tmp/claude-0/-home-user-m/7ce60006-3639-59b1-8cd3-87355409d58a/scratchpad/brief/baseline_v2.pine`
(identical to `/home/user/m/indicators/dol_engine.pine`, checked with `diff`).

**How to read the tags.**
- `[A✓]`: A's statement, re-checked by B (source re-read, number re-derived, or replicated).
- `[A]`: A's statement that B could not re-open; kept with A's grade or lower.
- `[B-CORRECTED]`: A's statement changed by B; the reason is given in place.
- `[B-NEW]`: added by B.

Study code and raw outputs:
- A: `/tmp/claude-0/-home-user-m/7ce60006-3639-59b1-8cd3-87355409d58a/scratchpad/brief/study/skeptic_tools/`
- B: `/tmp/claude-0/-home-user-m/7ce60006-3639-59b1-8cd3-87355409d58a/scratchpad/brief/study/skeptic_b_tools/`

| Script | Who | Question | Output |
|---|---|---|---|
| `ev_bias.py` | A | Is the HUD "EV" (2245, 2359) an unbiased expected R? | `out_ev_bias.txt` |
| `ledger_null.py` | A | Is the EDGE z-score (1461-1469, 2383-2390) correctly sized? Which variance estimator is right? | `out_ledger_null.txt` |
| `real_placebo.py` | A | What EDGE does a *no-skill* picker show on real CME data? | `out_real_placebo.txt` |
| `survivorship.py` | A | How biased are "ETA\|hit" (2116-2127, 2240) and "heat" (2404-2408)? | `out_survivorship.txt` |
| `beta_trap.py` | A | Does sample-period drift masquerade as directional skill? | `out_beta_trap.txt` |
| `mirror_control.py`, `mirror_seeds.py` | A | Does a mirror-level control remove baseline miscalibration? | `out_mirror_control.txt`, `out_mirror_seeds.txt` |
| `mt_power.py` | A | Multiple testing across charts/settings; minimum detectable edge | `out_mt_power.txt` |
| `anytime_mirror.py` | **B** | Anytime (peeking) false-alarm rate and power of four EDGE verdicts on 288 real null paths and 96 informed paths | `out_anytime_mirror.txt`, `anytime_mirror_rows.csv` |
| `intrabar_order.py` | **B** | How much does the same-bar target/stop ordering rule (1440-1441) bias race WIN% and average R, against 1-minute truth? | `out_intrabar_order.txt` |
| `theory_touch.py` | **B** | Brownian cross-check of A's base rates; "eventually swept" rates within 30/100/300 bars | `out_theory_touch.txt` |
| `kappa_gaps.py` | **B** | A model-free data-integrity signal (ATR / σ ratio, >4-ATR jumps) | `out_kappa_gaps.txt` |

Data: the local CME futures files used by the sibling studies (ES, NQ, CL, GC, RTY, YM: 1-hour Mar/Jun 2025 to Apr 2026;
1-minute Jan to Apr 2026, resampled to 5-minute, 15-minute and 1-hour), EURUSD 1-hour.

**Research note.** Both researchers worked under tool limits. A: Firecrawl web search exhausted on the first call, the
shared WebSearch budget ran out midway, and WebFetch could not resolve most hosts. B: the WebSearch budget for the turn was
already used up and Firecrawl web search was out of credits; WebFetch could not resolve newyorkfed.org, arxiv.org,
ssrn.com, nordman-algorithms.com or other vendor hosts. B therefore verified academic sources through the Firecrawl
**paper index** (full-text passages, quoted below), read open-source study repositories through raw GitHub, and relied on
the sibling `.final.md` reports where their researcher B had re-checked a source. Vendor studies nobody could re-open are
marked "not re-fetched" and graded no higher than moderate. After the Firecrawl daily allowance reset (16:09 UTC), B
re-fetched nine primary pages before the allowance ran out again: Osler 2000 and Osler 2003 (FRBNY PDFs), Nordman's FVG and
OB studies, Trader Markus's S&P FVG test, and the SSRN abstracts of Barot, Tangirala and Mahadzva. Those are now marked
"re-fetched by B". The TradingView placebo script and MarketTrace could not be re-fetched.

---

## 0. Key findings (read this first)

1. **Almost every tested ICT/SMC "magnet" claim reduces to geometry.** [A✓]
   - Pools, FVGs, order blocks, PDH/PDL and session extremes are reached at the rate of a *random level at the same
     distance*: FVG 73.0% vs 72.9%, OB 73.7% vs 73.7%, S&P daily FVG 69% vs 69%, PDH/PDL within ±3 pp of a day-bootstrap
     null. Sibling ict_pd B replicated the FVG/iFVG nulls on its own data (iFVG first retest held 49-50%, n ≈ 25,000).
   - What survives is small and short-lived: reactions of +2.5 to +5 pp at 1-15 minutes, S/R bounces of 60.8% vs 56.2%
     for arbitrary levels (Osler 2000), and the stop-cluster mechanism itself (Osler 2003/2005).
   - Directional ICT claims carry **no information beyond the trend regime or race geometry**. AMD/Power of 3: bullish
     46.9% (coin flip), bearish 39.9% (inverted), trend-aligned 62-71%, trend-opposed 25-30% (Taylor 2026, N = 484,
     re-read by B).
   - [B-NEW] Three further independent nulls: Tangirala (SSRN 7483658; 44 SMC detectors from two open-source Pine scripts,
     496 S&P 500 stocks, 2010-2026, 2.2 M events: none beats random entry at any horizon, and concepts selected on three
     years earn −31 bp out of sample against −35 bp for the average unselected one; abstract re-fetched by B); an open-source 1-minute gold/BTC/ETH test of the "Fibonacci + liquidity sweep" setup, 2019-2026
     (net −0.13 to −0.59 R per trade, no variant positive in both in- and out-of-sample periods); and an ES-futures study in
     which a "price level" feature set added ≈ 0 precision over the base rate (Sokolovsky & Arnaboldi 2020, re-read by B).
2. **Base rates are high, so a raw hit % is meaningless.** [A✓, B cross-checked against theory]
   - A random level 1 / 2 / 3 ATR away is traded through within 30 bars **75-80% / 54-62% / 39-47%** of the time on CME
     futures and EURUSD (A).
   - [B-NEW] This is exactly Brownian first passage. With per-bar σ = ATR/κ and κ = √(8/π) = 1.60 (the mean range of
     Brownian motion over one bar), `2Φ(−dκ/√H)` gives **77% / 56% / 38%**. B measured κ = 1.39-1.54 on clean CME data,
     which moves the 2-ATR value to 57-61%, matching A's 54-62%.
   - "Take the nearer pool" wins the which-side-first race **64.5-70.6%** of the time (gambler's ruin b/(a+b); sibling
     quant_regime).
   - [B-NEW] **"Eventually swept" is almost vacuous.** Random levels at 2 / 3 / 5 ATR are touched within 300 bars
     **87% / 81% / 68%** of the time, and 60-75% of the levels missed within 30 bars are touched by bar 300. A ghost or a
     screenshot that says "SWEPT" without a time limit is not evidence.
3. **The ledger is leak-free and its baseline is the right *kind* of baseline** (distance-matched, side- and
   regime-split, prequential). [A✓, re-checked line by line by B, §3.1]
   - The regime split even absorbs trend beta: an "always long" picker beats its mirror by **+8.3 ± 3.9 pp** on EURUSD 1h
     and **+10.8 ± 6.2 pp** on GC 1h by drift alone (A).
4. **Four trader-facing readouts are biased by construction.** [A✓, B re-derived the first one analytically]
   - **ETA** (HUD 2240, computed 2116-2127): median bars-to-hit of *hits only*, labelled "ETA|hit". It shows 9 bars at 2 ATR
     when the true median time to touch is 19-25 bars, and 12-13 bars at 3 ATR when the true median is "> 30" (A). [B] The
     Brownian values are 8.7 vs 22.4 bars at 2 ATR and 13.4 vs 50 bars at 3 ATR, so this is geometry, not data noise. The
     "|hit" suffix is technically honest but never says "unlikely within H".
   - **heat** (2404-2408, from `maeHit`, 1481-1483): p80 adverse excursion of *hits only*, 1.6-2.3 ATR, against **3.2-5.1
     ATR over all trials** (A).
   - **EV** (2245-2246 in the HUD, 2359 in the panel): built from P(target first | race decided within H). Under a
     driftless martingale the true expectancy is 0, but the readout shows **−0.62R** (target 2R, σ√H = 1R) to **−0.97R**
     (3R) (A, Monte Carlo).
   - **L50** (2395-2396): a raw rolling hit rate that moves with target distance, not skill.
5. **The EDGE verdict is wrong in two separate ways, and anytime-validity alone fixes only one.** [B-NEW, `anytime_mirror.py`]
   - On 288 real *no-skill* paths (6 CME symbols × 5m/1h × busy/quiet/all clock windows × 8 seeds), re-checking z ≥ 2
     after every closed block produced a false "✓" at some point on **13.5%** of paths and |z| ≥ 2 on **36%**.
   - Replacing the z ≥ 2 rule by a proper anytime-valid confidence-sequence boundary (sibling CAL-2) still gave a false
     "✓" on **4.5%** of paths and **23%** of busy-hours 5-minute paths. The boundary is not at fault: it correctly detects
     that the *baseline* is off for that clock window (miscalibration, A §2.3 C/F; sibling quant_regime: ±3-8 pp by
     volatility state).
   - **A mirror control plus the same boundary** (A's SKEP-2) cut false alarms to **0.7%** (upper) / **1.4%** (any). The
     self-normalised mirror variant cut them to **0.3%**.
   - It also had **more power**, not less: on an informed picker with a realised +2.3 to +3.1 pp excess, detection rose
     from 19% / 44% (one-sample, 1h / 5m) to **23% / 71%** (mirror). Side skill moves the DOL residual up and the mirror
     residual down, so the paired difference doubles the signal.
6. **The variance estimator is conservative under seasonality and loses power.** [A✓] `cluSt` (1463-1469) is
   uncentred, keyed by *booking* bar and uses 2H blocks: z sd 0.76 under a seasonal null, and a real +3.3 pp edge is
   flagged 10% of the time vs 30% with centred, open-keyed 8H blocks (A's simulation).
7. **The ledger cannot see small edges.** [A✓] With the active ledger's SE of 1.4-2.4 pp per 5,000 bars, the minimum
   detectable edge at 80% power is 3.9-6.7 pp at a fixed look and **5.5-9.5 pp** anytime-valid. The best-supported ICT
   effects are 2-5 pp.
   - [B-CORRECTED] So "✕ NO EDGE" (2390) is the wrong word on two counts. Not measurable is not "no edge", and a proper
     negative verdict needs an equivalence-style test: the upper confidence bound must fall *below a materiality threshold*
     (Darmanin 2026: SUPPORTED / REFUTED / INCONCLUSIVE).
8. **Multiple testing is the user's real enemy.** [A✓] Flipping through 10 symbols at one fixed look gives a 21% chance
   of at least one false "✓ EDGE"; with peeking, 80%. The best of 45 settings has E[max z] = 2.21 under the null. Every
   on-chart ledger is in-sample until bars arrive after the settings were fixed.
   - [B-NEW] Practitioner backtests show the pattern in the wild: an open-source NQ test ranks time-window × news-day cells
     by win rate and headlines the best ones (71-75%) from an overall 50.4% over 409 trades, without per-cell counts or
     any correction for the number of cells searched.
9. **The scoring pillars are mostly unsupported beyond geometry.** [B-CORRECTED grades, from sibling calib_ml B's Holm
   correction]
   - Only **EQH/EQL (1-hour)** survives multiplicity correction (+0.29 logit, Holm p 0.007).
   - External/key-level tier (Holm p 0.07), confluence (0.11), draw (0.23) and "tested ≥ 2" (1-hour −0.43 logit, t −2.5;
     Holm p 0.19) do **not** survive. They are *unsupported* (no lift beyond distance), not proven harmful. A called the
     confluence, tier and tests pillars "contradicted"; that overstated the evidence.
   - D-first *selection* is different: it loses 9-12 pp of first-touch accuracy intraday versus geometry (quant_regime,
     a direct test).
   - Drift in PoT hurts log-loss by 1.2-7.1% (quant_pot, quant_regime).
10. **"Draw on liquidity" is a destination, not "the next liquidity taken".** [A✓] The engine deliberately targets the
    outermost pool (inner-pool penalty ×0.70, line 685), so the inner pools are taken first by construction. The ledger's
    "touched within H" is the right metric for a destination; the README's "most likely drawing to next" is the wrong claim
    for it.
11. **[B-NEW] The visual record is survivorship-biased in a way A did not spot.** Ghosts are drawn for a target that is
    swept (`✕ SWEPT`, 1586), ejected (1586) or ruled out by a side flip (`⊘ INVALIDATED`, 2023). A target that is simply
    **out-scored by a same-side challenger disappears without a ghost** (2014-2023), and a SWEPT ghost carries no time to
    hit. With 87% of 2-ATR levels touched within 300 bars (finding 2), the ghost trail over-represents successes.
12. **[B-NEW] Intrabar ordering is not a material risk.** A listed the same-bar target/stop rule as a risk for the R test.
    Against 1-minute truth, only **0.6-1.7%** of engine-like trials resolve on a bar that touches both barriers. The
    engine's bar-colour rule is right on 80-88% of those (sibling trade_mgmt: 88% on all bars; TradingView's
    open-proximity rule 72-78%). The bias in average R is **+0.002 to +0.018 R** per trial, mostly from coarse-bar stop
    fills rather than ordering, and the WIN% bias is ≤ 0.3 pp.

**Bottom line for design.** The defensible product claim is "a calibrated touch probability for a sensibly chosen
destination", not "a predictive edge". The honest DOL engine:
- treats geometry (distance, volatility, clock) as the backbone and every ICT feature as a modifier that must *earn* its
  weight on the user's chart;
- grades itself with survivorship-free readouts, a mirror-controlled anytime-valid edge test with a three-way verdict, a
  model-free R-expectancy test, a league table against strong naive selectors, and a forward-only sub-ledger;
- shows an honest visual record (every target, including replaced ones, with its time to hit).

The ten proposals in §4 do that. Each is measurable by the engine's own ledger.

### 0.1 What B changed relative to A

| # | Change | Why |
|---|---|---|
| 1 | Anytime-validity alone does not stop false "✓ EDGE": measured 4.5% overall and 23% for busy-hour pickers with a valid boundary; the mirror cuts it to 0.3-0.7% and raises power | B's `anytime_mirror.py` on 288 + 96 real paths |
| 2 | SKEP-2 verdict: three-way (BEATS / NO MATERIAL EDGE / INCONCLUSIVE) with a materiality threshold; self-normalised variant documented; G ≥ 20 guard; data-integrity cue | Darmanin 2026; de la Peña 1999 / Howard et al. 2020 Lemma 3(d); calib_ml CAL-2; `kappa_gaps.py` |
| 3 | Evidence grades for confluence, tier and tests lowered from "contradicted" to "unsupported"; only EQ survives Holm | calib_ml B (Holm over 22 tests) |
| 4 | Garzarelli/Chung-Bellotti scope: memory effects are significant at 45-90 s, not at 180 s; bounce is defined against a tolerance stripe with no time limit, so the sign for a strict trade-through within H is indirect | Papers re-read by B (passages quoted in §2.1) |
| 5 | Mesfin numbers: the T = −10.96 and T = −14.12 statistics are on returns *net* of a 2-point friction; gross content was −0.27 and ±0.2-0.8 points. Two positive-control signals exist (the author's own regime signals) | Paper re-read by B |
| 6 | Osler figures corrected: take-profits 9.3% exactly at "00" (A's "8.7% of all orders" is not in the paper); the stop-sell asymmetry at "00" is marginal (p 0.064); 1-day cascade signs are mixed, not "not significant" | SR125 re-fetched by B; ict_liq B |
| 7 | Johari et al.: the paper says peeking can raise Type I error "fivefold" at 10,000 samples; the "over 20% to under 5%" figure is vendor-reported | Paper re-read by B; calib_ml B |
| 8 | Intrabar ordering removed as a material risk (0.6-1.7% of trials, ≤ 0.02 R bias); the engine's rule is better than TradingView's | B's `intrabar_order.py`; trade_mgmt |
| 9 | New engine finding: replaced targets leave no ghost; SWEPT ghosts carry no time; left-anchored zones back-date the selection | Code re-read (1584-1586, 2014-2023) |
| 10 | SKEP-1: race shown as the unconditional triple (target first / stop first / neither within H) instead of WIN\|decided; ETA falls back to the Brownian median | Theory; B's Brownian check |
| 11 | SKEP-4: optional cost in ticks; split-half stability added to SKEP-7; SKEP-10 promoted to P2 and extended to honest ghosts | Mesfin, Alonso (open-source), Darmanin |
| 12 | SKEP-9: α split across families through a weighted-Ville argument, valid under peeking and dependence | Benhamou et al. 2026 (PROMOTE) |
| 13 | Line references fixed: ghost inputs are 210-211 (A: 171); heat cell 2408; HUD EV 2245-2246 and HUD ETA 2240 were missing; SKEP-3's block width is 2.8 h on 1-minute charts, not a session | Code re-read |
| 14 | Mahadzva (SSRN 7430998): abstract re-fetched; graded weak-moderate (single-author preprint, DSR fails, a detector bug found by eye) | SSRN abstract re-fetched by B |
| 15 | Vendor and SSRN figures A took from siblings were re-fetched and confirmed (Osler 2000, Nordman FVG/OB, Trader Markus, Barot, Tangirala); Nordman's edge ratio is now defined (average MFE ÷ average MAE after a fill) and its after-cost numbers added | Firecrawl, after the daily reset |
| 16 | Five 2026 preprints added on evaluation honesty: exposure vs selection skill, preregistered nulls that "look like skill", zero-edge win-rate controls, three-way verdicts, anytime multiplicity | Paper index |

---

## 1. Concepts (definitions and parameters)

### A. The claims under test

Each entry gives the testable definition used in the quantitative studies, the practitioner use for "where / when / how
likely", and the null hypothesis it must beat.

**1.1 Liquidity pools as magnets (BSL/SSL).** [A✓]
- *Definition:* resting stop orders sit just beyond swing highs/lows. Engine version: a pivot high with `pivLen = 5`
  (`ta.pivothigh(high, 5, 5)`, confirmed 5 bars late), with a zone of `zoneATR = 0.20` ATR beyond it.
- *"Swept"* means trade-through: strict `high > level` (`touched`, 623-624).
- *Practitioner use:* the unswept pool on the bias side is the target, and the outermost pool of a stack is the real draw.
- *Null:* a random level at the same distance (and side and regime), touched with the same rule within H bars.
- *Mechanism vs magnet:* Osler's order data prove the *mechanism* (stops cluster beyond extremes and round numbers;
  crossing them accelerates price). The *magnet* claim (pools are reached more often than geometry predicts) is a different,
  much stronger claim.

**1.2 Equal highs/lows (EQH/EQL, "relative equal").** [A✓] Two or more pivots within `eqTol = 0.10` ATR (engine
`f_mergeAt`), folded into one pool. *Use:* "double tops are engineered liquidity". *Null:* an ordinary swing pool at the
same distance.

**1.3 Sweep → reversal (turtle soup, "raid then reverse", Judas swing).** [A✓]
- *Definition:* price trades through a pool, then closes back inside within k bars (k = 1-2). The claim is that it then
  runs to the opposite pool.
- *Null:* the symmetric ±x ATR race from the post-sweep close is 50/50 (martingale).
- *Engine:* `liqEvt` (1579-1582) adds `+tier` when a raid holds (continuation) and `−tier` when it rejects (reversal) into D.

**1.4 Fair value gaps (FVG), consequent encroachment (CE), inversion (iFVG).** [A✓]
- *Definition (3-candle):* bull FVG when `low > high[2]`, plus the engine's size gate `fvgMin = 0.15` ATR and quality gate.
- *Claims:* (a) price returns to fill; (b) the gap is a reaction level (CE = 50% midpoint); (c) once closed through, it
  inverts (iFVG) and holds as the opposite S/R.
- *Null:* a same-size zone at the same distance and time with no gap (placebo zone).

**1.5 Order blocks (OB), breakers, mitigation/rejection/propulsion blocks.** [A✓] OB = the last opposite-colour candle
before the displacement leg that broke structure. Breaker = a failed OB that swept liquidity. *Null:* a random zone at the
same distance.

**1.6 Killzones and session raids.** [A✓]
- *Definition (ET):* Asia 20:00-00:00, London 02:00-05:00, NY AM 07:00-10:00, NY PM 13:30-16:00 (engine inputs).
- *Claims:* "London raids Asia, NY raids London and the prior day" (engine `f_kzAff`, 597-602: ×1.05 to ×1.20, applied at
  1941). Raids are more productive inside killzones.
- *Null:* a clock-matched random path (the day bootstrap with the same volatility clock).

**1.7 AMD / Power of 3 / Judas swing.** [A✓, B-CORRECTED detail]
- *Definition (Taylor 2026):* a 15-minute candle breaches one side of the Asia range (19:00-00:00 ET) by δ = 10 NQ points
  before 04:00 ET and a later candle closes back inside before 05:00 ET; days with both sides breached are excluded.
- *Outcome actually tested:* the 16:00 ET close relative to the Asia midpoint. [B] It is a coarse proxy, acknowledged in the
  paper, not "delivery to the opposite Asia extreme".
- *Null:* 50/50, or the daily trend regime (20-EMA, ±0.5%).

**1.8 Market structure (BOS/CHoCH) and the draw direction.** [A✓]
- *Definition:* a close beyond the protected swing (BOS), or the first break against the prevailing swing sequence (CHoCH).
- *Engine:* `sV = 0.5·htfBias + 0.3·stfBias + 0.2·exeIB` (1892); `D` blends sV with displacement and `liqEvt` (1893-1894);
  `dirSide` from the gate `dGate = 0.35` (1895). Selection is draw-side first (1975) with 2× hysteresis to flip sides (2012).
- *Null:* which-side-first by geometry, b/(a+b).

**1.9 Premium/discount and the dealing range.** [A✓] Above 50% of the dealing range is premium (sell), below is discount
(buy). *Null:* none in ICT. The academic analogue is the 52-week-high effect (George & Hwang 2004), which predicts
*continuation* near highs.

**1.10 Key levels: PDH/PDL, PWH/PWL, session highs/lows, midnight open.** [A✓] *Claims:* they are taken (frequent,
obvious); they are taken in a characteristic session; the opposite side follows (Judas). *Null:* the day-bootstrap path
with the same clock.

**1.11 S/R tests ("the more touches, the weaker the level").** [A✓, B-CORRECTED scope]
- *Literature definition:* the number of prior bounces b_prev on a level, where a bounce or a cross is decided when price
  leaves a tolerance stripe around the level, **with no time limit** (Garzarelli et al. 2014; Chung & Bellotti 2021).
- *Engine definition:* `tests` counts approaches within `testATR = 0.30` ATR that did not take the pool, at most one per 3
  bars (`track`, 652-656); each test *adds* density (`+0.35·min(tests, 6)`, 682).
- [B] The two are not the same event. The engine's hit is a strict trade-through by any amount within H; the literature's
  "bounce" can include a one-tick poke inside the stripe. The direction of the effect on the engine's target is therefore an
  empirical question (measured directly by calib_ml: §2.1 C16).

**1.12 Round numbers and stop clusters.** [A✓] Prices ending in 00/50. Take-profits cluster *at* them (reversals); stops
cluster just *beyond* them (cascades).

### B. Base rates and naive models (what any DOL engine must beat)

**1.13 Random-walk touch probability.** [A✓, B-NEW conversion]
- For driftless Brownian motion with per-bar σ and horizon H: `P(touch d) = 2Φ(−d/(σ√H))` (reflection principle; engine
  `f_pot`, 434-444). It is about twice the probability of *finishing* beyond d (the options rule "probability of touch ≈ 2×
  probability ITM").
- [B-NEW] **ATR units.** The mean high-low range of Brownian motion over one bar is `√(8/π)·σ ≈ 1.60σ` (Feller 1951;
  Parkinson 1980). So a level d ATR away sits at `x = κ·d` bar-σ, with κ ≈ 1.6 in theory and **κ = 1.39-1.54** measured on
  clean CME data (median ATR14 / σ50 of close changes; `kappa_gaps.py`, `theory_touch.py`). Then:
  - `P(T ≤ H) = 2Φ(−κd/√H)`;
  - unconditional median time to touch `T50 = (κd / 0.6745)²` bars;
  - median time *given* a touch within H solves `2Φ(−κd/√t) = ½·P(T ≤ H)`.

  | d (ATR) | P(T ≤ 30), κ = 1.6 | A's empirical (7 sets) | T50 (bars) | T50 \| T ≤ 30 (bars) | A's ETA\|hit / true median |
  |---|---|---|---|---|---|
  | 1 | 0.77 | 0.75-0.80 | 5.6 | 3.4 | 5 / 7 |
  | 2 | 0.56 | 0.54-0.62 | 22.4 | 8.7 | 9-10 / 19-25 |
  | 3 | 0.38 | 0.39-0.47 | 50.4 | 13.4 | 12-13 / > 30 |

  The match means the survivorship bias in ETA|hit is a property of first-passage times, not of the sample.
- Using highs and lows makes the continuous formula appropriate. A close-based event needs the Broadie-Glasserman-Kou
  shift (sibling quant_pot).
- [B-NEW] **Recurrence.** A one-dimensional random walk touches every level eventually. Measured on CME data, random levels
  at 2 / 3 / 5 ATR are touched within 30 / 100 / 300 bars with probability 0.58 / 0.77 / 0.87, 0.42 / 0.65 / 0.81 and
  0.20 / 0.47 / 0.68 (§2.4 C). "It got there in the end" is not a forecast.

**1.14 Gambler's ruin: nearest-first.** [A✓]
- For levels a above and b below, `P(up first) = b/(a+b)` for any continuous martingale (optional stopping), whatever the
  volatility clustering or seasonality.
- Sibling quant_pot found real races within 0.4-1.2 pp of it on about 28k races per cell. The naive "nearer pool first"
  rule scores **0.645-0.706** among decided races (sibling quant_regime: 1H / 5m / 15m / D).
- This is the *strong* baseline for "which side is taken next".
- [B-NEW] **Finite-horizon race triple.** Within H bars a race has three outcomes: target first, stop first, neither.
  `f_raceH(a, b, σ, 0, H)` (465-482) gives the first; swapping a and b gives the second; the rest is "neither". The
  engine's WIN≤H is the first divided by the first two, which hides the third and drives the biased EV (1.19).

**1.15 Martingale expectancy (optional stopping / Wald).** [A✓]
- For any bounded exit rule (target, stop, time-out at H), `E[X_τ − X_0] = μ·E[τ]`. With no drift, the expected R of
  *every* target/stop choice is exactly 0.
- So the race's average R is a model-free edge statistic. The only nuisance term is drift (beta), and it is removable:
  `E[R] = side·μ·E[τ]/risk`.
- [B-NEW] Booking details matter only at the second decimal: the engine pays a target at its edge even when price gaps
  through it (conservative), and fills stops at the stop price on coarse bars even when 1-minute prints gapped through it
  (optimistic, +0.002 to +0.02 R per trial, §2.4 B).

**1.16 Arcsine law (timing).** [A✓] The time of a Brownian path's maximum on [0, T] has density `1/(π√(t(T−t)))`;
window edges are over-represented. "The HOD forms in the first hour" and "the weekly low forms Mon/Tue" are largely this
arithmetic (sibling ict_time; random-walk weekday baseline Mon 29.5 / Tue 14.1 / Wed 12.8 / Thu 14.1 / Fri 29.5%).

### C. Evaluation traps (how indicator "accuracy" goes wrong)

**1.17 Base-rate trap.** [A✓] A hit rate with no expected rate. The fix is to always print "hit / expected", where
expected is the distance-matched baseline.

**1.18 Survivorship (conditioning on success).** [A✓, B-extended]
- Statistics computed over hits only: time to hit, adverse excursion, R of winners. The fixes are time-to-event with
  censoring (with a fixed horizon and no early censoring, the Kaplan-Meier curve equals the empirical CDF of `min(T, H+1)`)
  and excursions over *all* trials.
- [B-NEW] **Visual survivorship.** Users judge indicators by scrolling history. Anything that keeps successes on the chart
  and lets failures vanish biases that judgement: here, ghosts for swept targets but none for out-scored ones (§3.1).

**1.19 Conditioning on decided races.** [A✓] `P(target first | decided by H)` is a legitimate quantity. An "EV" built
from it ignores the undecided mass, whose mean R is not zero when target and stop are asymmetric (§2.3 A).

**1.20 Look-ahead and repainting.** [A✓, B-CORRECTED one figure]
- Pivots need `pivLen` future bars; drawing them at the pivot bar repaints.
- `request.security(..., lookahead_on)` without a `[1]` offset leaks the current HTF bar.
- Intrabar order is unknown on OHLC bars. The engine assumes O-L-H-C for bull bars and O-H-L-C for bear bars (1440-1441).
  [B-CORRECTED] That rule is the better one: 88.1-88.7% correct ordering on all bars vs 80.6-80.7% for TradingView's
  broker-emulator rule (sibling trade_mgmt), and 80-88% vs 72-78% on the double-touch bars of engine-like trials (B). A
  quoted the 80.6% figure as the engine's accuracy.
- Exits evaluated on coarse bars can inflate results: Barot's apparently profitable FVG construction (PF ≈ 2.4) fell to
  PF ≈ 1.0 on 1-minute data (Barot SSRN 7148099, abstract re-fetched by B). For *this* engine the effect is small (§2.4 B).
- A deliberately leaky oracle with Sharpe 35 *survives* deflated-Sharpe and PBO tests (Gençay 2026, abstract re-read by B).
  Statistics cannot catch look-ahead; only construction can.
- [B-NEW] **Visual back-dating.** The DOL zone is drawn from the candle that formed the level, not from the bar the engine
  selected it (`activeSince`). On a historical chart the target looks as if it was known since its origin.

**1.21 Overlap and dependence.** [A✓, B-refined]
- H-bar windows that overlap share one price path. The design effect is `deff = V_cluster / V_independent`.
- Clusters must be keyed by the window's *open* bar, centred, and wide enough to span the dependence. Intraday
  seasonality creates positive short-lag and negative long-lag correlation of residuals, so the right block width is at
  least a session where the window allows (A's simulation, §2.3 B).
- [B-NEW] Batch-means arithmetic, under the simplest overlap model (one record per bar, residual autocovariance falling
  linearly to 0 at lag H): the covariance between neighbouring block sums is `H/(6W) / (1 − H/(3W))` of a block's own
  variance, about 10% at W = 2H and 4.5% at W = 4H. A batch-means estimator that ignores it understates the variance by
  about 17% / 8% (z inflated by about 9% / 4%). A's simulation found the 2H open-keyed estimator correctly sized under a
  constant-volatility null (sd 1.00), so the real effect is smaller, but the direction argues for W ≥ 4H when the window
  allows, and never fewer than about 20 blocks (Cameron, Gelbach & Miller 2008: few clusters bias cluster-robust variances
  down).

**1.22 Baseline miscalibration.** [A✓, B-extended]
- The baseline is a model. If it is off by b pp for the picker's mix of distances, hours, volatility states and sides, the
  excess is shifted by b, whatever the skill.
- Known sources on real data: clock window ±2-3 pp (A), volatility state +3 to −8 pp (sibling quant_regime: compressed /
  normal / expanded tercile +3.7 / +1.7 / −8.2 pp on 15m), roll gaps −4 pp (GC 1h; A and calib_ml).
- [B-NEW] All three are **direction-free**: they affect a level above and a level below at the same distance alike. That is
  why a mirror control removes them.
- *Placebo control:* grade a no-skill comparator on the same bars and subtract. *Mirror control:* the level at the same
  distance on the opposite side, same bar, same rule.

**1.23 Beta masquerading as skill.** [A✓] In a trending sample any picker biased to the trend side looks skilled. The
fixes: a regime-split baseline (engine) or a drift term in the R test (Wald).

**1.24 Peeking (optional stopping of the *analyst*).** [A✓, B-CORRECTED source wording]
- A fixed-α test re-evaluated after every sample eventually rejects. Johari et al. (2017): "Even with 10,000 samples …
  Type I error can easily increase fivefold" (passage re-read by B). The "over 20% to under 5%" figure A attributed to them
  is vendor-reported, not in the paper.
- The fixes: confidence sequences / e-processes (Robbins 1970; Howard et al. 2021; Waudby-Smith & Ramdas 2020-2024;
  Johari et al. 2017).
- [B-NEW] Two-sided normal-mixture boundary: `|S_t| < u(V_t) = √((V_t+ρ)·ln((V_t+ρ)/(ρα²)))`. With a Gaussian mixing
  distribution, the mixture martingale is `√(ρ/(V+ρ))·exp(S²/(2(V+ρ)))`, and Ville's inequality at 1/α gives exactly this
  boundary (B re-derived it; calib_ml B checked it against Howard et al. eq. 14). `u(v)/√v` is smallest near `v ≈ 8.2ρ`
  for α = 0.05; in z units it is 3.66 / 3.18 / 3.06 / 3.04 / 3.10 at V = 10 / 25 / 50 / 100 / 250 (ρ = 10).

**1.25 Multiple testing and forking paths.** [A✓]
- Many charts × many families × many settings. Corrections: Bonferroni/Holm/BH, White's Reality Check, Hansen's SPA,
  deflated Sharpe, PBO.
- Hurdles: t > 3 (Harvey-Liu-Zhu; Chen & Zimmermann 2022); bootstrap 4.5 vs forking paths ≥ 8.2 (Coqueret 2023, abstract
  re-read by B: "each additional degree of freedom … expands the average range of t-statistics by at least 30%").
- MinBTL `≈ (E[max of N standard normals])² / SR²` years: about 45 configurations exhaust 5 years of data for a target
  annual Sharpe of 1 (Bailey, Borwein, López de Prado & Zhu 2014).
- [B-NEW] **Anytime multiplicity.** If each of k hypotheses gets its own e-process or confidence sequence at level α·w_k with
  Σw_k ≤ 1, a weighted Ville argument bounds the chance of *ever* a false claim by α under any dependence and any peeking
  (Benhamou et al. 2026, "PROMOTE": repeated unadjusted tests crossed on 94.5% of null paths, the funded gate on 0.0%).

**1.26 Bandit feedback / selection.** [A✓] A ledger that grades only the chosen target learns only about what it already
prefers. Full-information shadow probes fix it (sibling calib_ml CAL-3).

**1.27 Destination vs "next".** [A✓] "Which liquidity is taken *next*" is a first-passage question over *all* pools; the
nearest pool on each side always comes first on its side. A *destination* (outermost pool) is never "next" while inner pools
exist. Its correct metrics are "touched within H" and "before the invalidation".

**1.28 Power, minimum detectable effect and materiality.** [A✓, B-extended]
- `MDE ≈ (z_crit + z_power)·SE`. A verdict without its MDE turns "not measurable" into "no edge".
- [B-NEW] **Three-way verdict** (Darmanin 2026, re-read by B): with a predeclared materiality threshold δ and a confidence
  interval [L, U], SUPPORTED if L > δ (or > 0 for "beats"), REFUTED if U < δ ("no *material* edge"; "significantly negative"
  if U < 0), INCONCLUSIVE if the interval straddles δ. Non-significance is never reported as proof of absence.

**1.29 In-sample vs forward.** [A✓] A prequential ledger is leak-free per trial, but the settings (and the developer's
defaults) were chosen on the same history. Only trials opened after the settings were fixed (realtime bars) are truly
out-of-sample.
- [B-NEW] **Stability across sub-periods.** The commonest failure mode in recent falsification studies is "one strong
  period masking weak or negative ones" (Mesfin 2026: year stability; the open-source sweep test: a variant at +0.81 R out
  of sample and −0.03 R in sample was "reported, not adopted"). A split-half check of the ledger is a cheap disclosure.

**1.30 [B-NEW] The sharp null for a paired mirror test.** "The engine's choice of side carries no information beyond the
baseline" means the DOL and its mirror are exchangeable, so the paired residual D = r − r_mirror is symmetric about 0.
For conditionally symmetric increments, `S_t = ΣD` is sub-Gaussian with the *observed* variance process `V_t = ΣD²`, with
no moment assumptions (de la Peña 1999; Howard, Ramdas, McAuliffe & Sekhon 2020, Lemma 3(d), passage re-read by B). The
normal-mixture boundary with `V = ΣD_g²` over closed blocks is then a non-asymptotic test. Overlap between neighbouring
blocks makes it approximate. The one-sample excess `y − pBase` has no such symmetry, so its confidence sequence is only
asymptotically valid (calib_ml B).

**1.31 [B-NEW] Costs.** Touch statistics are cost-free, but R and EV are trade claims. Recent falsification studies find
the gross per-trade content of OHLCV signals on liquid index futures at 0.07-1.50 points against a 2-point round-trip
friction (Mesfin 2026), and the open-source sweep test found that "most of the apparent edge in short-timeframe versions
disappears once trades whose cost exceeds 10% of the risk are removed". Any R readout must say whether it is gross or net.

**1.32 [B-NEW] Marketing claims are not falsifiable as written.** The reference product's "highly probable DOL target" and
"PoT capped at 95%" (brief) make no comparison with a base rate. A displayed PoT under an empirical distance model is, by
construction, the random-level touch rate at that distance (plus any drift term). Our engine should not adopt such
wording; it should show the base rate next to every probability.

---

## 2. Evidence

Grades: **strong** = peer-reviewed or large replicated quantitative study; **moderate** = published, reproducible
statistics or backtests with numbers; **weak** = practitioner consensus, a single unverified preprint, or anecdote;
**none** = folklore or unfalsifiable. "[this study]" = `skeptic_tools/` (A) or `skeptic_b_tools/` (B). "[sibling X]" =
another report in this folder; where that report's researcher B re-checked a source, it is said so.

### 2.1 Claims ledger (verdict per claim)

Verdict classes: **Supported** (survives a proper null) · **Geometry** (true, but fully explained by distance, volatility
or the clock) · **Small/short** (real, a few pp, minutes to hours) · **Contradicted** (the measured effect has the opposite
sign) · **Unsupported** (tested, no effect) · **Untested / unfalsifiable** (as typically stated).

| # | Claim | Verdict | Key numbers | Grade | Sources and check status |
|---|---|---|---|---|---|
| C1 | Stops cluster beyond extremes/round numbers; crossing them accelerates price | **Supported** (mechanism) | RBS orders, almost 9,700, 1 Sep 1999 - 11 Apr 2000: take-profits 9.3% exactly at "00" (stop-losses 4.4%; uniform ≈ 1%); stop-buys 14.4% in 01-10 vs 7.4% in 90-99 (p = 0.029; around "50" p = 0.002); stop-sells 10.0% in 90-99 vs 5.1% in 01-10 (p = 0.064; around "50" p = 0.004). Extra move after crossing a round number vs an arbitrary one: +0.27 to +2.35 hundredths of a percent from 15 min to 2 h; mixed signs at 1 day (DEM −5.23, GBP −2.60, JPY +1.27) | strong | Osler 2003 JF / FRBNY SR125 (**re-fetched by B**); Osler 2005 JIMF / SR150 (via ict_liq B). **[B-CORRECTED]** A's "8.7% of all orders at 00" is not in the paper; the stop-sell asymmetry at "00" is only marginal (p 0.064); 1-day signs are "mixed", not "not significant" |
| C2 | Pools are reached more often than a random level at the same distance (magnet) | **Geometry** | External pools vs random: −0.14 / −0.27 logit (t −1.1 / −2.9, 5m / 1h), Holm p 0.07. PDH/PDL take rates within ±3 pp of a day-bootstrap null on 7 markets (ES PDH 58.8% vs 57.0%) | moderate | [sibling calib_ml B], [sibling session_stats]. **[B-CORRECTED]** "unsupported", not "less than random": the negative lift does not survive Holm |
| C3 | Equal highs/lows are taken more than single swings | **Small** | +0.08 / +0.29 logit (t +0.7 / +3.6, 5m / 1h); the only pool feature surviving Holm (1h, p 0.007). An open-source distance-matched test: < 1% better odds | moderate | [sibling calib_ml B], [sibling ict_liq] |
| C4 | Sweep → reversal (turtle soup) | **Unsupported / contradicted** | Post-sweep ±1 ATR race 0.497-0.510 whether the raid "holds" or "rejects" (5m/15m/1h; no regime rescues it). MNQ Asia-session grabs (6,442 events): gross directional content 0.2-0.8 points either way, below a 2-point friction (fade net −2.20, T −14.12; continuation net −1.80, T −13.24). Open-source 1-minute test of "Fibonacci + sweep" on gold/BTC/ETH 2019-2026: base setup −0.19/−0.13 R (gold, in/out of sample), −0.51/−0.59 (BTC), −0.49/−0.43 (ETH), net of costs | moderate | [sibling quant_regime A✓B]; Mesfin 2026 arXiv 2605.04004 (re-read by B); ivanalonso-dev/fib-liquidity-sweep-backtester (README read by B). **[B-CORRECTED]** Mesfin's T statistics are net of friction, so they show "too small to trade", not "reversal fails". Mahadzva SSRN 7430998 (abstract **re-fetched by B**): three independently built sweep mechanisms (equal highs/lows, order blocks, Asia ranges) on EURUSD/GBPUSD/AUDUSD/USDJPY intraday agree in 65 of 66 walk-forward fold-selections that a swept level predicts *continuation*; the textbook CHoCH + FVG reversal "should be faded". Its best results fail the deflated Sharpe ratio at every defensible trial count, and an order-block detector bug was caught "only by a human looking at a chart". Graded **weak-moderate** (single-author preprint) |
| C5 | FVGs get filled / are magnets | **Geometry** | Return to 73.0% of FVGs vs 72.9% of random levels (38,114 FVG returns vs 380,599 fakes; ES/NQ/6E/6A, 5m and 15m charts, Oct 2023-Sep 2026). S&P 500 daily 2000-2026 (1,337 bullish, 887 bearish gaps): bullish 69% vs 69% within 20 days; bearish 81% vs 72% (the one positive cell; the side-matching of its control is not described). BTC 1h full fill 75.6% vs 72.4% (+3.2 pp). A TradingView placebo-control script: no advantage over size-matched placebo zones in 14 measurements | moderate | Nordman and Trader Markus (**re-fetched by B**); MarketTrace (via ict_pd; not re-fetched); placebo script (A, WebSearch summary only). Sibling ict_pd B replicated the null on its own data (CE and full fill −0.2 to −2.5 pp vs distance baseline) |
| C6 | FVG/CE is a reaction level | **Small/short** | Reaction about 5 pp above random (≈ 40,000 FVGs, 4 futures, 3 TFs, 7 years), "no tradeable edge"; the apparently profitable version (PF ≈ 2.4) fell to PF ≈ 1.0 on 1-minute data. Edge ratio (average MFE ÷ average MAE after a fill) real vs random: +3.7% at 5 min and +2.5% at 15 min (4 of 4 markets), −0.2% at 1 h, −0.9% at 1 day; every market in the red after costs | moderate | Barot SSRN 7148099 and Nordman (both **re-fetched by B**) |
| C7 | iFVG holds as flipped S/R | **Unsupported** | S&P daily: broken bullish gaps held as resistance 38% vs 38% random; bearish 47% vs 47%. [B-NEW] Sibling ict_pd B: first retest held 49.1-50.2% (n ≈ 25,000), the same as random | moderate | Trader Markus (**re-fetched by B**); [sibling ict_pd B replication]. **[B-CORRECTED]** no longer single-source |
| C8 | Order blocks attract and hold price | **Geometry** (reach), **small/short** (reaction) | Revisited 73.7% vs 73.7% random (10,986 touches, ES/NQ/6E/6A, Oct 2023-Sep 2026). Edge ratio +4.8% at 1 min, +3.3% at 5 min; fresher blocks react more. After costs at 5 min: −$24 (ES), −$17 (6E), −$15 (6A) per trade, NQ ≈ +$0.82 | moderate | Nordman (**re-fetched by B**) |
| C9 | Breakers, mitigation/rejection/propulsion blocks, CE/MT, PD-array ordering, IRL/ERL alternation | **Untested** | No audited statistics found by any sibling | none-weak | [sibling ict_pd] |
| C10 | Volatility is concentrated in killzones (timing) | **Supported** | ES 5m variance at 09:30 is 4.7× the daily mean and 0.20× at 23:30. Peak/quiet hourly range 2.1-4.0× across 10 instruments | strong | Andersen & Bollerslev 1997; [sibling quant_pot], [sibling ict_time] |
| C11 | Sessions raid specific liquidity ("London raids Asia") beyond the clock | **Geometry** (one exception) | Session take rates within ±3 pp of the clock-matched null. Exception: the opposite Asia-range side is taken +3.5 to +6.2 pp more on ES/NQ/YM/RTY (≈ 3 SE), not on CL/EURUSD/BTC | moderate | [sibling session_stats] |
| C12 | AMD / Power of 3 / Judas | **Unsupported** (trend explains) | NQ 15m, Jan 2022-Jul 2026, N = 484 signal days: bullish 46.9% (CI 40.5-53.4), bearish 39.9% (inverted, BH p 0.002). Trend-aligned 61.6% / 70.8%, trend-opposed 29.6% / 24.8% (BH-significant). 57% of targets delivered *before* the 09:40 entry; 6 valid trades in 4 years | moderate (one preprint, code public) | Taylor 2026 arXiv 2610.35887 (**re-read by B**, tables 5-6); code: github.com/veertaylor19/amd-backtest |
| C13 | Silver Bullet | **Unsupported** | 108 trades, 38.9% win rate at 1:1, net loss | weak (negative) | tradestar.app (via ict_time) |
| C14 | Structure/draw vector picks the side taken first | **Contradicted** (as a selector) | D-proxy 49.9-51.6% for which side first. D-first selection 0.550-0.652 vs geometry 0.645-0.706 (−9 to −12 pp intraday). The efficiency gate "recovers" geometry only because the gated D disagrees with geometry on 0.4-0.5% of races. Displacement and NR7 breaks: symmetric ±1 ATR race 0.48-0.52 | moderate | [sibling quant_regime A✓B], [sibling bias_dol] |
| C15 | Premium → sell, discount → buy | **Contradicted** at monthly horizons; **untested** intraday | Nearness to the 52-week high predicts continuation | strong (equities, monthly) | George & Hwang 2004 (via ict_pd) |
| C16 | Prior bounces make a level *weaker* (folk), or (engine) tests add magnitude | **Folk claim contradicted** at seconds-to-minutes; **engine use unsupported** | LSE tick data 2002, 9 stocks: p(bounce \| b_prev) > 0.5 and rising with b_prev; independence rejected p < 0.0001 at 45, 60 and 90 s, **not at 180 s** (p 0.077 / 0.318). EURUSD/LLOY/BRENT 1-minute 2018: same pattern; EURUSD 1-bounce levels decay to 0.5 at ≈ 350-minute lag windows, 4-bounce at ≈ 900 min; BRENT 1-bounce levels fall *below* 0.5 (trend). Direct engine-style test: "tested ≥ 2" vs touch within H: 5m +0.03 logit (t +0.2), 1h −0.43 (t −2.5), Holm p 1.00 / 0.19 | strong (memory exists, HF) / weak (sign for the engine's target) | Garzarelli et al. 2014 Sci. Rep. (arXiv 1110.5197) and Chung & Bellotti 2021 (arXiv 2101.07410), both **re-read by B**; [sibling calib_ml B]. **[B-CORRECTED]** A graded "tests should lower trade-through" strong; the literature measures bounce vs cross against a tolerance stripe with no time limit, so for a strict trade-through within H the support is weak |
| C17 | S/R levels interrupt trends more than random levels | **Supported, small** | Published FX levels (6 firms, DEM/JPY/GBP 1996-98): bounce 60.8% vs 56.2% for 10,000 sets of arbitrary levels; per currency +1.7 to +9.2 pp; lasts ≥ 5 business days; the firms' strength ratings had no value | strong | Osler 2000 FRBNY EPR 6(2) (**re-fetched by B**: 60.8% vs 56.2%, 10,000 artificial level sets per day, Jan 1996 - Mar 1998, six firms, DEM/JPY/GBP, ≥ 5 business days, strength ratings "do not seem to be useful") |
| C18 | Round numbers act as price barriers (holding) | **Mixed** | Round levels attract more limit liquidity but do not show longer depth-adjusted durations (5 Nasdaq stocks, 2025); Intel and SoFi show departures biased *away* from round levels | moderate | Jung & Lee 2026 arXiv 2610.34787 (**abstract re-read by B**); Lallouache & Abergel arXiv 1307.5440 |
| C19 | ADR is "exhausted" after a full ADR | **Contradicted** | After ≥ 1 ADR used, real extension exceeds the null by +4 to +10 pp | moderate | [sibling session_stats] |
| C20 | "HOD forms in the first hour"; "weekly low Mon/Tue" | **Geometry** (arcsine) | Weekday of weekly extreme Mon/Fri 23-34%, Tue-Thu 12-18%, equal to a day-order shuffle | strong (null) | [sibling session_stats], [sibling ict_time] |
| C21 | Intraday OHLCV signals (ORB, gap, volume, Asia expansion, grabs) | **Unsupported after costs** | 14 families on MNQ 5m 2021-2025: gross 0.07-1.50 points vs a 2-point friction floor; none passes walk-forward. The commonest failure: one strong year masking others. Two positive controls (the author's own GMM-regime signals, developed in a separate programme) pass | moderate | Mesfin 2026 (**re-read by B**). **[B-CORRECTED]** A's "Asia expansion T = −10.96 (wrong sign)": that T is on *net* returns; gross was −0.27 points |
| C22 | Technical trading rules in general | **Mostly data-snooped** | BLL rules on 100 years of DJIA with Reality Check; 21,000 rules on MSCI with FDR; 7,000+ rules with SPA on Chinese indices: significance concentrated in less-efficient periods, gone after costs or later. [B-NEW] Five promoted retail families (trend, oscillator, candlestick, volume, calendar), exposure-matched benchmarks, BY control and equivalence tests: 4 REFUTED, 2 INCONCLUSIVE, 0 SUPPORTED | strong | Sullivan, Timmermann & White 1999; Sermpinis et al. 2018 (arXiv 1811.06766); Wang et al. 2015 (arXiv 1504.06397); Darmanin 2026 (arXiv 2607.20093, **re-read by B**) |
| C23 | [B-NEW] SMC detectors as return predictors | **Unsupported** | 44 detectors from two open-source Pine scripts, 496 S&P 500 stocks, daily 2010-2026, 2.2 M events: none beats random; liquidity-sweep detectors 11-12 bp over 10 days, p ≥ 0.23; in-sample picks −31 bp out of sample | moderate (null) | Tangirala SSRN 7483658 (abstract **re-fetched by B**; 17.6 M simulated trades over eight horizons; none significantly worse than random either) |
| C24 | [B-NEW] Price levels (local extrema) as rebound points, ES ticks | **Small / unsupported** | ES futures 2017-2019: rebound labels occur 15-21% of the time; a level-feature classifier's precision 0.15-0.25 vs the always-positive base rate 0.15-0.21; the price-level feature set alone ≈ base rate; effect sizes not significant after Bonferroni | moderate | Sokolovsky & Arnaboldi 2020/2022 (arXiv 2009.09993, **re-read by B**) |
| C25 | [B-NEW] "A target that was eventually swept was a good target" | **Geometry** (recurrence) | Random levels at 2 / 3 / 5 ATR are touched within 300 bars 87% / 81% / 68% of the time (CME 1h and 5m) | strong (theory) / moderate (measured) | [this study, B `theory_touch.py`] |

### 2.2 Literature on evaluation, overfitting and honest inference

| Topic | Numbers | Grade | Source (check status) |
|---|---|---|---|
| Random-level baseline is the established control for S/R claims | 10,000 artificial level sets per day as the null | strong | Osler 2000 (re-fetched by B) |
| Shuffled returns / fractional RW as the null for S/R memory | p(b \| b_prev) ≈ 0.5 for shuffled returns; a fractional RW with H = 0.44 gives a constant p slightly above 0.5, so memory is not anti-persistence | moderate | Garzarelli et al. 2014; Chung & Bellotti 2021 (both re-read by B) |
| Data snooping in technical rules | Reality Check bootstrap | strong | Sullivan, Timmermann & White 1999, JF 54(5) |
| False-discovery hurdles | t-hurdles above 3.0 | strong | Chen & Zimmermann 2022 (arXiv 2209.13623); Harvey & Liu 2020 (arXiv 2006.04269) |
| Forking paths | Each extra degree of freedom widens the t-stat range by ≥ 30%; 5% threshold 4.5 (bootstrap) vs ≥ 8.2 (paths) | moderate-strong | Coqueret 2023 (arXiv 2401.08606, abstract re-read by B) |
| Backtest overfitting | PBO via CSCV; MinBTL; about 45 trials fake a Sharpe-1 backtest on 5 years | strong (theory) | Bailey, Borwein, López de Prado & Zhu 2014/2015 |
| Statistics cannot detect look-ahead or bugs | A leaky oracle with Sharpe 35 survives DSR and PBO; every LLM-discovered strategy rejected out of sample (Gençay). An order-block detector bug passed every statistical gate and was caught only by eye (Mahadzva) | moderate | Gençay 2026 (arXiv 2608.27734, abstract re-read by B); Mahadzva SSRN 7430998 (abstract re-fetched by B) |
| Holdout discipline | An LLM-found survivor with Sharpe ≈ 3 in discovery and validation fell to 0.26 on its single holdout | moderate | Zhang 2026 (arXiv 2611.06607) (A) |
| Peeking | "Type I error can easily increase fivefold" at 10,000 samples. Re-testing z ≥ 2 each trial: 10/15/20% false "EDGE" at 100/300/1,000 trials (calib_ml); 13.5% false "✓" and 36% \|z\| ≥ 2 on 288 real null paths (B) | strong / moderate | Johari, Pekelis & Walsh 2017 (arXiv 1512.04922, **re-read by B**); [sibling calib_ml]; [this study, B] |
| Anytime-valid inference | Two-sided normal-mixture CS `|S| < √((V+ρ)ln((V+ρ)/(ρα²)))`: boundary z ≈ 3.0-3.7 for V = 10-250 (ρ = 10) | strong (theory) | Howard et al. 2021 (arXiv 1810.08240); Waudby-Smith & Ramdas (arXiv 2010.09686) |
| Self-normalised bounds | Conditionally symmetric increments: sub-Gaussian with V = Σ(ΔY)², no moments needed | strong (theory) | de la Peña 1999; Howard et al. 2020 (arXiv 1808.03204, Lemma 3(d), **re-read by B**) |
| Anytime multiplicity | Weighted Ville over candidates (allocations sum ≤ 1): false family crossing 0.0% vs 94.5% for repeated unadjusted tests on 3,000 null paths | moderate (preprint) | Benhamou et al. 2026 "PROMOTE" (arXiv 2611.03384, abstract read by B) |
| Three-way verdicts with materiality | REFUTED only if the bound excludes the declared effect; INCONCLUSIVE "must not be read as a null finding"; a positive control is never falsely refuted | moderate (preprint) | Darmanin 2026 (arXiv 2607.20093, **re-read by B**) |
| Gates need a random-admission control and excess (not absolute) returns | "criteria computed on absolute rather than excess returns silently reject every candidate, including true signals" | moderate (preprint) | Zheng 2026 (arXiv 2610.07701, abstract read by B) |
| Optional stopping (martingale expectancy) | E[X_τ] = X_0 for bounded τ; Wald: E[X_τ − X_0] = μE[τ] | strong (theory) | standard; races ≈ b/(a+b) within 0.4-1.2 pp on real data [sibling quant_pot] |
| Direction vs volatility | Across 61 instruments, the direction sector of a multi-timescale coherence measure never beats its random-walk null; the volatility sector beats every null | moderate | Le 2026 (via sibling quant_regime B) |
| [B-NEW] Exposure masquerading as selection skill | A zero-centred paired test credits passive exposure as skill in 11.6% of no-skill replications; a composition-matched random reassignment brings it to 5.3% (the same logic as the mirror and the regime split) | moderate (preprint, simulation + replay) | Chen et al. 2026, Agent Policy-Value Audit (arXiv 2610.04040, abstract read by B) |
| [B-NEW] Standard metrics that "suggest skill" under a null | 0 of 160 model cells beat a no-change forecast (SPA p = 1.000), yet price-level correlation > 0.9996 and within-day RankIC +0.35; a sign-randomised null reproduces about 95% of the RankIC | moderate (preregistered preprint) | Upadhyay 2026 (arXiv 2611.12141, abstract read by B) |
| [B-NEW] Win-rate base rate at a fixed R:R | Break-even 40.5-41.5% win rate at 1:1.5 net of costs against a driftless 40.0% (= 1/(1+1.5), gambler's ruin); every result reported against a zero-edge control | moderate (preprint) | Hall 2026 (arXiv 2609.14859, abstract read by B) |

### 2.3 Researcher A's experiments (kept; B's checks noted)

**A. The HUD "EV" is conditioned on decided races (`ev_bias.py`).** Driftless Brownian motion with 20 sub-steps per bar,
H = 30, risk b = 1, 40,000 paths per cell. The formulas are ported from `f_race` / `f_raceH` (447-482). "EV shown" is
`win·rr − (1 − win)` with `win = pW/(pW + pL)`, as at 2245 and 2359.

| Target a (R) | σ√H (R) | P(decided ≤ H) | WIN\|dec model / MC | **EV shown** | E[R \| decided] MC | **E[R] all** MC |
|---|---|---|---|---|---|---|
| 0.5 | 1 | 0.86 | 0.690 / 0.686 | +0.03 | +0.03 | −0.01 |
| 2 | 1 | 0.34 | 0.125 / 0.118 | **−0.62** | −0.65 | **+0.00** |
| 3 | 1 | 0.31 | 0.008 / 0.008 | **−0.97** | −0.97 | +0.01 |
| 3 | 2 | 0.72 | 0.164 / 0.163 | **−0.34** | −0.35 | +0.01 |
| 5 | 2 | 0.61 | 0.019 / 0.018 | **−0.89** | −0.89 | +0.03 |
| 5 | 4 | 0.92 | 0.141 / 0.147 | −0.15 | −0.12 | +0.05 |

`f_raceH` matches Monte Carlo, so the maths is right; the *label* is wrong. [A✓: B confirmed the engine computes `ev` exactly
this way in both places, 2245 and 2359.] Grade: strong (theory plus simulation).

**B. Is the EDGE z correctly sized? (`ledger_null.py`, 400 synthetic replications per scenario).** Engine-like ledger: a
random-side, random-distance (0.5-4 ATR) "DOL" switching with probability 0.08 per bar; one trial per active level;
trade-through within H = 30; 300-bar warm-up; 5,000 bars; pBase = an engine-style online surface blended with the
driftless analytic prior (priorM = 30). Estimators: **ind** Σp(1−p); **eng** the engine's uncentred, booking-keyed 2H
blocks; **open** open-keyed, centred 2H; **hac** open + lag-1; **wide** open-keyed, centred 8H.

| Scenario | sd of z: ind / **eng** / open / hac / **wide** | P(z ≥ 2) eng / wide | deff eng / wide |
|---|---|---|---|
| NULL const | 1.02 / **0.96** / 1.00 / 0.97 / 1.06 | 0.003 / 0.007 | 1.13 / 1.07 |
| NULL sv (seasonal) | 1.05 / **0.76** / 0.79 / 0.76 / **1.00** | 0.018 / 0.072 | 1.93 / 1.30 |
| NULL sv_slow | 0.99 / **0.90** / 0.93 / 0.90 / 0.99 | 0.007 / 0.013 | 1.21 / 1.13 |
| ALT sv, +3.3 pp informed picker | mean z 1.70 / **1.21** / 1.29 / 1.23 / **1.59** | **0.100** / **0.302** | 1.97 / 1.23 |

At one look the engine's z is not anti-conservative; under seasonality it is too conservative (sd 0.76). Centred,
open-keyed blocks at least a session wide are correctly sized (sd 0.99-1.06) with 3× the power. Grade: moderate.
[B note: the engine floors `vEdge` at `vInd` (2385), so `deff ≥ 1` always; that floor is kept in SKEP-3 as `0.25·vInd`
only as a guard for tiny G.]

**C. A no-skill picker on real data (`real_placebo.py`).** Random side, random distance, same ledger; 12 seeds per
dataset on 1h and 5m (shared path), plus 76 *independent* 6,000-bar 1-minute segments.

| Set | Placebo excess (pp) | mean z_eng | P(z ≥ 2) | P(z ≤ −2) |
|---|---|---|---|---|
| GC 1h | **−4.00** | −1.82 | 0 | **0.25** |
| CL 1h | +1.02 | +0.49 | 0 | 0 |
| RTY 1m | −1.94 | −1.00 | 0 | 0.15 |
| YM 1m | −1.79 | −0.88 | 0 | 0.23 |
| NQ 5m | +0.66 | +0.53 | 0.08 | 0 |
| YM 5m | +0.97 | +0.73 | 0.08 | 0 |
| other 13 sets | −1.2 to +0.7 | −0.6 to +0.3 | 0 | ≤ 0.08 |
| **1-min pooled, 76 independent segments** | **−1.11 (sd 1.87)** | sd 0.91 | 0 | P(\|z\| ≥ 2) 0.079 |
| 1-min paired placebo (picker − second picker) | — | **sd 0.96** | — | **P(\|z\| ≥ 2) 0.026** |

The baseline is off by −4 to +1 pp per dataset; GC 1h has roll gaps (the same corruption quant_pot and calib_ml found). A
paired placebo restores the nominal size. Grade: moderate.

**D. Survivorship in ETA and heat (`survivorship.py`).** Random levels at 1/2/3 ATR, both sides, every 3rd bar, H = 30,
strict trade-through. The KM median is the unconditional median of min(T, H+1).

| Set | d (ATR) | P(touch ≤ 30) | **ETA \| hit** (engine) | **true median** | **heat \| hit** (engine) | heat all | heat misses |
|---|---|---|---|---|---|---|---|
| ES 1h | 1 | 0.80 | 5 | 7 | 1.81 | 3.57 | 7.36 |
| ES 1h | 2 | 0.62 | 9 | 19 | 2.18 | 4.68 | 6.79 |
| ES 1h | 3 | 0.45 | 12 | **> 30** | 2.25 | 5.09 | 6.36 |
| ES 5m | 2 | 0.54 | 9 | 25 | 1.87 | 4.26 | 6.40 |
| ES 5m | 3 | 0.39 | 13 | **> 30** | 2.02 | 4.62 | 5.92 |
| NQ 1h | 2 | 0.62 | 9 | 19 | 2.17 | 4.69 | 6.88 |
| CL 5m | 2 | 0.56 | 9 | 23 | 1.90 | 4.49 | 6.72 |
| EURUSD 1h | 2 | 0.59 | 10 | 20 | 1.95 | 4.66 | 6.87 |
| EURUSD 1h | 3 | 0.43 | 13 | **> 30** | 1.90 | 4.97 | 6.35 |

[B] The Brownian values in 1.13 (8.7 vs 22.4 bars at 2 ATR) reproduce these, so the bias is structural. Grade: moderate
(measurement) to strong (theory).

**E. Beta trap (`beta_trap.py`).** Touch rate at 2 ATR within 30 bars for an "always long" picker minus its mirror (same
distance, opposite side, same bar), SE with 8H blocks: GC 1h **+10.8 ± 6.2 pp**, EURUSD 1h **+8.3 ± 3.9** (z ≈ 2.1), CL 1h
+5.4 ± 5.0, RTY 1h +4.4 ± 3.8, ES 1h +3.5 ± 4.2, 5m sets −3.7 to +4.2. A drift-free or regime-free comparison credits a long
bias with "edge"; the engine's regime-split surface (`sUp/sDn` by `htfBias`, 1059-1062, 1284-1300) removes it by
construction. Grade: moderate.

**F. Mirror control vs clock-driven miscalibration (`mirror_control.py`, `mirror_seeds.py`).** No-skill pickers that fire
only in a clock window (random side and distance, 5m data; "busy" = 13:30-16:00 and "quiet" = 00:00-07:00 in the data's
timestamps), 16 seeds each. Mirror-controlled residual `(y − pBase) − (y_mirror − pBase_mirror)`.

| Set / window | engine-style excess, mean z | mirror-controlled excess, mean z |
|---|---|---|
| ES busy | +3.14 pp, z̄ **+1.02** | −1.16 pp, z̄ −0.25 |
| ES quiet | −2.26 pp, z̄ **−1.20** | −0.64 pp, z̄ −0.19 |
| NQ quiet | −2.02 pp, z̄ **−1.04** | −0.53 pp, z̄ −0.17 |
| GC quiet | −3.34 pp, z̄ **−1.57** | +1.67 pp, z̄ +0.50 |
| 6 symbols × 2 windows, single seed | busy +2.04 pp (z̄ +0.61); quiet −1.97 pp (z̄ −1.10) | busy +0.24 pp (z̄ +0.04); quiet −0.06 pp (z̄ −0.06) |
| **all 12 cells, 16 seeds** | mean \|bias z\| **0.69** | mean \|bias z\| **0.24** |

Grade: moderate.

**G. Multiple testing and power (`mt_power.py`).** One chart, fixed look: P(z ≥ 2) = 2.3%. Across charts: 10 → 21% (fixed
look) or 80% (with peeking); 30 → 50% or 99%. Best of k settings: k = 10 E[max z] 1.53 (P ≥ 2 = 20%); k = 45 2.21 (64%);
k = 100 2.51 (90%). Five per-family rows at one look: 11%. MDE at 80% power for the active-DOL ledger:

| SE per 5,000 bars | 5,000 bars: fixed / anytime | 10,000 bars: fixed / anytime | 20,000 bars: fixed / anytime |
|---|---|---|---|
| 1.4 pp | 3.9 / 5.5 pp | 2.8 / 3.9 pp | 2.0 / 2.8 pp |
| 2.4 pp | 6.7 / 9.5 pp | 4.8 / 6.7 pp | 3.4 / 4.7 pp |

Candidate (shadow) ledger (SE 0.9-1.9 pp): anytime MDE 3.5-7.5 pp at 5,000 bars.

### 2.4 Researcher B's experiments [B-NEW]

**A. Anytime false alarms and power of four EDGE verdicts on real paths (`anytime_mirror.py`).**
- *Setup.* A's real-data ledger mechanics (`mirror_control.py`): no-skill picker, random side, distance U(0.5, 4) ATR, fires
  with probability 0.3 per eligible bar, at most one record per 5 bars; engine-style prequential surface baseline. 6 CME
  symbols × {5m, 1h} × {busy 13:30-16:00, quiet 00:00-07:00, all hours} × 8 seeds = **288 null paths**, plus 96
  "informed" paths where, with probability 0.10, the picker peeks at which side is touched (when exactly one is).
- Blocks keyed by the record's *open* bar, width `W = max(2H, min(bars per day, n/30))`; a block counts only once all its
  records have resolved; verdicts re-checked after every closed block once ≥ 20 blocks exist (the CAL-2 guard).
- *Verdicts:* `one_z2` one-sample excess, centred variance, z ≥ 2; `one_cs` the same with the normal-mixture boundary
  (ρ = 10, α = 0.05); `mir_z2` / `mir_cs` the mirror-paired residual with z ≥ 2 / the boundary; `mir_sn` the paired residual
  with the self-normalised `V = ΣD_g²`.

| Null paths (n = 288) | one_z2 | one_cs | mir_z2 | mir_cs | mir_sn |
|---|---|---|---|---|---|
| P(ever a false "✓", upper crossing) | **0.135** | **0.045** | 0.083 | **0.007** | **0.003** |
| P(ever any crossing) | 0.361 | 0.132 | 0.208 | 0.014 | 0.003 |
| worst cell: 5m busy hours, P(ever "✓") | 0.542 | **0.229** | 0.062 | 0.000 | 0.000 |
| worst cell: 1h quiet hours, P(ever any) | 0.375 | 0.146 | 0.229 | 0.042 | 0.021 |

| Informed paths (eps 0.10) | realised one-sample excess | mirror difference | detect one_cs | detect mir_cs | detect mir_sn |
|---|---|---|---|---|---|
| 1h (n ≈ 750 records) | +2.3 pp | +5.3 pp | 0.19 | **0.23** | 0.17 |
| 5m (n ≈ 2,160 records) | +3.1 pp | +6.3 pp | 0.44 | **0.71** | 0.63 |

Reading:
- An anytime-valid boundary is necessary (z ≥ 2 with peeking: 13.5% false "✓") but not sufficient. Baseline
  miscalibration by clock window still produces a false "✓" on 23% of busy-hour 5m paths, because the boundary correctly
  detects that `y − pBase` does not average 0.
- The mirror makes the verdict both honest and *more* powerful for side skill. The self-normalised variant is the most
  conservative; the centred one keeps more power.
- Grade: moderate (real data, 384 paths, one picker design).

**B. Same-bar ordering and coarse-bar fills vs 1-minute truth (`intrabar_order.py`).**
- *Setup.* 6 CME symbols, Jan-Apr 2026 1-minute data resampled to 5m / 15m / 1h. Engine-like race trials every 3rd bar (every
  bar on 1h): random side, target U(0.5, 4) ATR as a strict trade-through, stop U(0.25, 2.0) ATR (or a tight U(0.25, 0.75)),
  H = 30, `f_step` logic including open-gap fills. Truth: the same race on the 1-minute bars.

| TF × stop | trials | double-touch share | engine rule correct | TV rule correct | R bias engine / TV / MTM-at-open | WIN% truth / engine |
|---|---|---|---|---|---|---|
| 5m, 0.25-2 ATR | 32,386 | 0.6% | 87.8% | 75.8% | +0.008 / +0.007 / +0.007 R | 34.7 / 34.7 |
| 5m, tight | 32,386 | 0.9% | 88.3% | 75.7% | +0.017 / +0.016 / +0.017 R | 21.2 / 21.2 |
| 15m, 0.25-2 ATR | 10,739 | 0.9% | 86.3% | 78.1% | +0.008 / +0.005 / +0.006 R | 34.0 / 34.1 |
| 15m, tight | 10,739 | 1.5% | 87.8% | 74.4% | +0.018 / +0.009 / +0.017 R | 21.6 / 21.8 |
| 1h, 0.25-2 ATR | 7,769 | 0.9% | 81.9% | 73.8% | +0.002 / +0.004 / +0.005 R | 35.7 / 35.6 |
| 1h, tight | 7,769 | 1.7% | 80.0% | 71.5% | +0.012 / +0.005 / +0.007 R | 21.8 / 21.9 |

Reading:
- The engine's bar-colour rule beats the broker-emulator rule by 8-13 pp on the bars where it matters, and those bars are
  ≤ 1.7% of trials. Booking the ambiguous bar at its open (the gambler's-ruin credit) changes nothing material either.
- The residual +0.01-0.02 R comes from stops filled at the stop price on coarse bars while 1-minute prints gapped through
  (GC and YM show the most). It is about 0.3 SE per 1,000 trials: worth a footnote, not a fix.
- Random-picker mean R on 1-minute truth: timeframe averages −0.03 to +0.03 R; the 36 symbol cells span −0.15 to +0.10 R
  (SE 0.02-0.07), with 33 of 36 within 2 SE of 0. All three exceptions are GC and negative (5m −0.054 ± 0.025 and, with tight
  stops, −0.149 ± 0.036; 15m −0.095 ± 0.039): stop fills through 1-minute gaps on a jumpy contract. This is consistent with the martingale null that SKEP-4 relies on, and it
  shows the null is "E[R] ≤ 0" on gappy instruments with tight stops.
- Grade: moderate (direct measurement, 6 symbols, 3 timeframes).

**C. Brownian cross-check and "eventually swept" (`theory_touch.py`).**
- Brownian values with κ = 1.60 (table in 1.13) match A's empirical touch rates and ETA medians.
- Empirical κ = median ATR14 / σ50: ES/NQ/CL 1h 1.39-1.43, 5m 1.50-1.54; **GC 1h 0.86** (roll gaps inflate σ).
- Touch within 30 / 100 / 300 bars, random levels, probes every 5th bar, both sides, CME 1h and 5m (8 sets):

  | d (ATR) | ≤ 30 bars | ≤ 100 bars | ≤ 300 bars | touched by 300 given missed by 30 | median bars |
  |---|---|---|---|---|---|
  | 2 | 0.58 | 0.77 | 0.87 | 0.70 | 18-25 |
  | 3 | 0.42 | 0.65 | 0.81 | 0.67 | 35-56 |
  | 5 | 0.20 | 0.47 | 0.68 | 0.61 | 91-207 |

- Grade: strong (theory) / moderate (measurement).

**D. A model-free data-integrity cue (`kappa_gaps.py`).** On clean 1h CME data, bars whose close-to-close change exceeds
4 ATR number 18-29 per ~6,000 bars (0.3-0.5%), and κ < 1 on 6-14% of bars. On GC 1h (roll gaps, not back-adjusted) the
counts are **132 (2.2%)** and **58%**. TradingView continuous futures are not back-adjusted by default (sibling calib_ml
B, quoting the help centre), so this corruption is a realistic user situation. A count of > 4-ATR close jumps above ~1% of
the calc window is a cheap warning that the baseline (and every PoT) is unreliable on this chart. Grade: moderate (one
corrupt and five clean datasets).

---

## 3. Engine gap analysis (`baseline_v2.pine`, line references re-checked by B)

### 3.1 Ledger, readouts and statistics

| Item | Lines | Verdict | What the engine does / what is wrong |
|---|---|---|---|
| Leak-freeness | 1426-1431 (open at the confirmed close), 1549-1557 (grade on later bars, `bar_index > t.bar0`, before sweeps delete levels), 1527-1532 (surface from completed windows: `fwdHi = ta.highest(high, H)` ends on this bar, measured from `close[H]` with `atr[H]` and regime `htfBias[H]`), 2038 (`barstate.isconfirmed` block) | **correct** [A✓] | No look-ahead (agrees with calib_ml). The surface's window start, ATR unit and regime key match what `f_potBase` uses at a trial's open. MTM reads use `[1]` + `lookahead_on` and `f_tfSafe`. |
| Hit rules | 623-624, 1436 | correct [A✓] | Strict trade-through for pools, touch for arrays. The surface counts "reached at least" with linear interpolation (1265-1278): negligible mismatch. |
| Trial capacity | 2044 (`openT.size() < math.max(64, H + 1)`) | correct [B-NEW] | At most one record opens per bar and each lives ≤ H bars, so the cap never binds for H ≤ 63. A mirror (SKEP-2) and roles (SKEP-5) need it raised. |
| Persistent targets | 2038-2045 | correct, worth stating [B-NEW] | A target that stays active and unhit gets a fresh record every H bars, each graded against its own distance. That is the honest unit ("each H-bar window in which a DOL was asserted"); targets held for long are weighted by how long they were asserted. |
| Random-level baseline | 1313-1322, 1059-1062, 1284-1300 | **present, good** [A✓] | Distance-matched, direction × HTF-regime split, prequential, analytic driftless prior (μ = 0 in `f_potBase`). The regime split absorbs trend beta (§2.3 E). |
| Baseline calibration check | — | **missing** [A✓] | Nothing detects that the baseline itself is off on this chart: −4 to +1 pp per dataset, ±2-3 pp per clock window, +3 to −8 pp by volatility state (quant_regime). No placebo, mirror or data-integrity cue. |
| Cluster variance | 1463-1469 (`cluSt`), 2384-2385 | **partial / wrong** [A✓] | Uncentred, keyed by *booking* bar (`bar_index` in `f_book`, so one window's records can land in different blocks), 2H wide. Under seasonality z sd 0.76 (conservative) and 3× less power on a real edge (§2.3 B). No block-count guard: at H = 450 and 5,000 bars there are about 5 blocks (calib_ml). |
| Wilson CI with design effect | 2385-2387 | partial [A✓] | Kish-style `k/deff, n/deff`; `deff ≥ 1` by the `math.max(vInd, …)` floor. Fixed-time interval, not anytime-valid. |
| Verdict thresholds | 2390-2391 | **wrong** [A✓, B-extended] | `z ≥ 2 → ✓ EDGE`, `z ≥ 1 → ~ WEAK`, else `✕ NO EDGE`. (i) Peeking: 13.5% false "✓" on real null paths (B), 10-20% in simulation (calib_ml). (ii) Baseline bias: even with a valid boundary, 4.5% overall and 23% for busy-hour pickers (B). (iii) "✕ NO EDGE" is printed for *not measurable* (MDE 5.5-9.5 pp) and is not an equivalence test. (iv) `nA ≥ 20` is far too few; n_eff and the block count matter. |
| MDE / power | — | **missing** [A✓] | Users cannot tell "no edge" from "cannot tell". |
| Headline hit rate | 2392-2394 | partial [A✓] | DOL HIT % and its Wilson CI without the expected rate in the same row. |
| Rolling L50 | 1478-1480, 2395-2396 | **wrong (base-rate trap)** [A✓] | The last-50 *raw* hit rate moves with target distance. It should be the last-50 *excess* (y − pBase). |
| BARS→HIT | 1476-1477, 2403-2407 | partial [A✓] | avg/med over hits only. Acceptable only if labelled "given hit". |
| ETA in the HUD | 2116-2127 (computed), **2240** (shown as "ETA\|hit ~Nb") | **misleading (survivorship)** [A✓, B-CORRECTED grade] | Median bars-to-hit of past *hits* within ±0.5 ATR. The "\|hit" label is literally correct, but the number is 2-3× shorter than the unconditional median and can never say "> H" (Brownian: 8.7 vs 22.4 bars at 2 ATR). |
| heat | 1481-1483 (`maeHit` pushed only when y = 1), 2404, **2408** | **wrong (survivorship)** [A✓] | p80 adverse excursion of hits: 1.6-2.3 ATR vs 3.2-5.1 ATR over all trials. `stMae` (1475) accumulates all trials but is never shown. |
| EV | **2245-2246 (HUD)**, 2358-2363 (panel), from `f_invalidation` 1343-1364 and `f_raceAdj` 1367-1371 | **wrong** [A✓, B added the HUD copy] | (i) E[R \| decided] labelled EV: −0.34 to −0.97R for fair far targets. (ii) The drift `potMu·side` in `f_raceH` adds noise. (iii) Under no drift the true EV ≡ 0, so any non-zero value is bias or drift. |
| WIN≤H | 2246, 2362, 1364 | partial [A✓, B-extended] | A defined quantity (decided-race win rate), shown without its geometric expectation and without the "neither" share. The unconditional triple (target first / stop first / neither within H) is the honest readout. |
| Race R / PF | 1457-1458, 1489-1498, 2419-2425 | **present, under-used** [A✓] | `rOut` pays the target at its edge, the stop at −1 or at a gapped open, MTM at H. E[R] ≈ 0 under a martingale (B: 33/36 random-picker cells within 2 SE of 0). Shown only in Full view, with no uncertainty, no drift adjustment, no cost, no verdict. |
| Same-bar ordering | 1440-1441 | **correct, near-optimal** [B-CORRECTED] | Bar-colour rule right on 80-88% of double-touch bars (TradingView's rule 72-78%); double touches are 0.6-1.7% of trials; R bias ≤ +0.02 R (§2.4 B). A listed it as a risk. |
| `f_raceAdj` | 1367-1371 | partial [A✓] | Shifts toward observed wins relative to the *drift* model p (`pRace`). Its reference should be drift-free geometry; calib_ml CAL-11 gates it. |
| Per-family rows | 2410-2418 | partial [A✓] | Hit % with no expected rate or interval; 5 rows → 11% chance of a spurious standout at one look. |
| Adaptive calibration `f_calMult` | 1376-1382, 1935-1944 | **wrong** [A✓] | Noise: ≥ 10% off under the null in 66% / 47% / 33% of families at n = 10 / 40 / 80 (calib_ml); bandit feedback; ignores the design effect. A persistent ±20% family tilt, larger than the 4-point hysteresis. |
| Shown vs graded | 2038-2045 vs 2068 | partial [A✓] | The ledger grades `activeLv` whether or not the PoT filter shows it. With `minPoT > 0` the panel includes targets the user never saw. |
| Forward / out-of-sample | — | **missing** [A✓] | No distinction between history trials (in-sample to the settings) and realtime trials. |
| Swept PoT | 2067 | minor [A✓] | Shows 95% after the target is touched; it should read "HIT". |
| Ghost trail | 1584-1586 (SWEPT / EJECTED), 2021-2023 (INVALIDATED), 1253-1262 (`f_ghost`), inputs **210-211** (off by default, max 12) | **survivorship-biased** [B-NEW] | (i) A target replaced by a same-side challenger (`pick != curI` with `curElig` true, 2014-2020) leaves **no ghost**: failures vanish, successes stay. (ii) "✕ SWEPT" carries no time to hit, and 87% of 2-ATR levels are touched within 300 bars. (iii) Ghost boxes start at `lv.anchorBar` (1254), the level's origin, not at the bar the engine committed. |
| DOL zone anchor | 2205 (`aX = f_x(activeLv.anchorBar)`), 2216/2229 | visual back-dating [B-NEW] | The zone starts at the origin candle, as the reference look requires, but the Clean style never says when the engine selected it. The Terminal HUD shows `AGE` (2243); the Clean tooltip does not. |
| Audit trail | 2444 (`DOL Price` plot, data window only) | partial [A✓] | Users cannot see past targets, including abandoned ones, so cherry-picking from memory is easy. |
| Costs | — | **missing** [B-NEW] | R and EV are gross. On 1-5 minute charts friction can exceed the gross content of a signal (Mesfin 2026). |
| Data integrity | — | **missing** [B-NEW] | Roll gaps (TradingView continuous futures are not back-adjusted by default) corrupt the surface, `potSig` and every PoT; nothing warns (§2.4 D). |
| Claims wording | README intro and "Probability of Touch"; tooltips 180-181 (`minPoT`, `potModel`) | partial [A✓, line refs corrected] | "Most likely drawing to next"; PoT presented as the level's probability (it is a distance/regime probability); `minPoT` reads as a quality filter (it filters by distance). |

### 3.2 Scoring and selection vs the evidence

| Component | Lines | Evidence verdict | Status |
|---|---|---|---|
| Proximity (25): linear + reachability + taper | 662-667 | Geometry *is* the signal; expected reach d·P(d) is the principled form (calib_ml CAL-8: max-reach delivers 1.10-1.43 ATR per target vs 0.86-1.09 for the hand score). Reach uses the drift `mu·side` | partial |
| Freshness (10): liquidity matures then decays | 668-673 | No evidence either way. S/R memory decays over hours (C16), the opposite of "maturing" | unsupported |
| Confluence (15) | 674-680 | No lift beyond distance (Holm p 0.11; pooled −0.04, t −0.7). [B, from calib_ml CAL-5] key-level pools are pushed at exactly their own anchors (1793-1799 vs 1931), so every PDH/PDL/PWH/PWL pool earns `conf ≥ 0.35` for coinciding with itself | **unsupported** [B-CORRECTED from "contradicted"]; self-confluence is a bug |
| Density: EQ count (0.9 per merge) | 682 | +0.29 logit on 1h, the only pool feature surviving Holm | small support |
| Density: source tier (1.2·tier, PW > PD > … > chart) | 506-516, 682 | External/key pools −0.14 / −0.27 logit, Holm p 0.07 | **unsupported** [B-CORRECTED from "contradicted"] |
| Density: tests (+0.35 per test, up to 6) | 652-656, 682 | Direct test: 5m +0.03, 1h −0.43 logit (Holm p 1.00 / 0.19). The literature's bounce memory (C16) points the same way at seconds-to-minutes | **unsupported**, sign weakly negative [B-CORRECTED from "contradicted (strong)"] |
| Density: coil, inducement | 893-903, 683 | No published test | untested |
| Draw (30) + draw-side-first selection + counter-draw ×0.5 | 691-693, 1892-1895, 1975, 2000-2012 | D-first −9 to −12 pp first-touch vs geometry; the gated D agrees with geometry on 99.5% of races (quant_regime) | **contradicted as a selector** |
| `liqEvt`: raid holds → +, rejects → − | 1579-1582 | Post-sweep races 0.497-0.510 for both | contradicted |
| Killzone affinity ×1.05-1.20 | 597-602, 1941 | Clock-matched null within ±3 pp; one exception (Asia two-sided raid on index futures) | unsupported (fixed) |
| Inner-pool penalty ×0.70 | 684-685 | A design choice: "destination" semantics. Fine if the claim is "destination" | n/a (wording) |
| Origin lockout ×0.25 for fresh arrays | 689-690 | Sensible: price sits on its origin | n/a |
| Volume-profile path cost ×1.10 / ×0.85 | 1945-1947 | Untested here (see orderflow_micro / amt_profile) | untested |
| Adaptive calibration | 1376-1382, 1942-1944 | Noise under the null (calib_ml) | wrong |
| PoT drift (`driftW 0.5`) | 185, 916-917, 665, 1304, 1361-1363, 2067 | Hurts log-loss 1.2-7.1% in every regime (quant_pot, quant_regime) | wrong |

### 3.3 Concept status summary

| Concept | Status | Where |
|---|---|---|
| Distance-matched random-level baseline | present | 1313-1322 |
| Regime-split baseline (beta control) | present | 1059-1062, 1287 |
| Leak-free prequential ledger | present | 1426-1500, 1549-1557 |
| Near-optimal same-bar ordering | present [B] | 1440-1441 |
| Overlap-aware variance | partial | 1463-1469 (uncentred, booking-keyed, 2H, no block guard) |
| Placebo / mirror control of the baseline | missing | — |
| Data-integrity warning | missing [B] | — |
| Anytime-valid, three-way verdict | missing (wrong) | 2390 |
| Minimum detectable effect | missing | — |
| Survivorship-free time to touch | wrong (misleading) | 2116-2127, 2240 |
| Survivorship-free adverse excursion | wrong | 1481-1483, 2404-2408 |
| Martingale-consistent EV / race readout | wrong | 2245-2246, 2359 |
| Model-free R-expectancy test | partial | 1457-1498, 2419-2425 |
| Costs in R | missing [B] | — |
| Strong naive baselines (nearest / max-reach / trend-side / runner-up) | missing | — |
| Forward (realtime-only) ledger, split-half stability | missing | — |
| Multiple-comparison discipline | missing | 2410-2418 |
| Honest visual record (audit line, replaced/expired ghosts, selection bar) | partial / biased [B] | 1584-1586, 2014-2023, 2205, 2444 |
| Honest claims and wording | partial | README, tooltips 180-181 |
| ICT modifiers as measured, not assumed | wrong (hard-coded) | 597-602, 674-693, 1579-1582 |

---

## 4. Proposals (best first; 10)

Common Pine v6 rules for every sketch [A✓, B-extended]:
- All state changes run inside the existing `if barstate.isconfirmed and not na(atr) and atr > 0` block (1518), so nothing
  repaints. Panel code runs on `barstate.islast` only.
- Functions cannot reassign global scalars, so running statistics live in `var array<…>` (as `stN` and `raceSt` do), and
  UDT fields are changed with `:=` inside functions (as `f_step` does).
- No forward references: new globals go in STATE (after 1079); helpers go in STATE HELPERS after the arrays they use;
  `f_blk` must precede `f_book` (1461), `f_cluVar`/`f_csBound`/`f_ttStats` may follow it; everything precedes the panel
  (2289).
- `H` is the simple int at 305; `chartS` (307) and `calcBars` (85) are available for a global `blkW` placed after 307.
- New `Trial` fields go at the end of the type (375-395) with defaults, so the existing `Trial.new` call (1428-1431) keeps
  compiling.
- A `for` loop whose end is below its start runs *downward* in Pine, so every loop over a possibly empty range is guarded.
- `plot()` takes `display` as "input plot_display" and `style` as "input plot_style" (reference/plot.md, verified by B), so
  an input-driven ternary is allowed there.

Sibling proposals this report relies on or endorses without repeating: QPOT-01 (remove the drift), CAL-2 (confidence
sequence with a block guard), CAL-3 (candidate ledger and roles), CAL-5 (self-confluence), CAL-10 (base integrity),
CAL-11 (gate `f_raceAdj`), REG-3 (draw vector does not steer selection without measured skill; hard efficiency gate as the
legacy option).

---

### SKEP-1 (P1, effort S) · Survivorship-free and martingale-consistent readouts [A✓, B-refined]

**Why.** Four numbers a trader acts on are biased by construction (§2.3 A, D; §2.4 C): ETA is 2-3× too optimistic and
never "> H"; heat is about half the real p80 adverse excursion; EV shows −0.3 to −1.0R for fair targets; L50 tracks
distance. The fix is pure honesty and cheap.

**Algorithm.**
1. *Time-to-touch histogram by distance bucket.* Every record is followed until it hits or reaches H bars, so there is no
   early censoring and the Kaplan-Meier curve equals the empirical CDF of `min(T, H+1)`. Report the unconditional median,
   or "> H" when P(T ≤ H) < 0.5, together with P(T ≤ H). [B] Until a bucket has 20 records, fall back to the Brownian median
   `T50 = (d / (0.6745·σ))²` with `σ = potSig` (labelled "model").
2. *Heat over all records.* Keep the hits-only value only as a tooltip.
3. *Race readout.* [B-CORRECTED] Replace "WIN≤H · EV" by the unconditional drift-free triple for the current target:
   `T = f_raceH(d, risk, σ, 0, H)`, `S = f_raceH(risk, d, σ, 0, H)`, `N = 1 − T − S`. Under a martingale the expectancy is 0
   for every target/stop choice, so no EV is shown; the measured average R (SKEP-4) replaces it.
4. *L50* becomes the last-50 excess `Σ(y − pBase)/50`.
5. *Hit row* prints "hit / exp".
6. *Touched target* reads "PoT: HIT", not 95%.

**Pine v6 sketch.**

State (after 1079):
```pine
// time-to-touch counts per distance bucket (0-1, 1-2, 2-3, 3+ ATR); slot 1..H = hit on that bar, H+1 = not hit
var array<int>   ttDist  = array.new<int>(4 * (H + 2), 0)
var array<float> maeAll  = array.new<float>()   // adverse excursion of every record (last 300)
var array<float> roll50x = array.new<float>()   // last 50 residuals y − pBase (replaces roll50)
```

In `f_book` (1461-1500), after `int y = …` (role 0 only once SKEP-2 lands):
```pine
    int bkt  = math.min(3, int(math.floor(t.d0)))
    int slot = y == 1 ? math.max(1, math.min(t.bars, H)) : H + 1
    ttDist.set(bkt * (H + 2) + slot, ttDist.get(bkt * (H + 2) + slot) + 1)
    maeAll.push(t.mae)
    if maeAll.size() > 300
        maeAll.shift()
    roll50x.push(y - t.pBase)
    if roll50x.size() > 50
        roll50x.shift()
```

Helper (after `f_book`):
```pine
// Unconditional time to touch for a distance bucket: [median bars (na = beyond H), P(touch ≤ H), n]
f_ttStats(int bkt) =>
    int   base = bkt * (H + 2)
    float n    = 0.0
    for j = 1 to H + 1
        n += ttDist.get(base + j)
    float cum = 0.0
    float med = na
    for j = 1 to H
        cum += ttDist.get(base + j)
        if na(med) and n > 0 and cum >= 0.5 * n
            med := j
    [med, n > 0 ? cum / n : na, n]
```

Rendering:
- Replace the `dHit` loop (2118-2127) by `[eMed, eP, eN] = f_ttStats(math.min(3, int(math.floor(dNow))))` and, when
  `eN < 20`, `tMod = nz(potSig) > 0 ? math.pow(dNow * atr / (0.6745 * potSig), 2) : na`. HUD text at 2240:
  `eN >= 20 ? (na(eMed) ? "ETA >" + str.tostring(H) + "b" : "ETA " + str.tostring(eMed, "0") + "b") + " · " + str.tostring(100 * eP, "0") + "% ≤H" : na(tMod) ? "" : tMod > H ? "ETA >" + str.tostring(H) + "b (model)" : "ETA ~" + str.tostring(tMod, "0") + "b (model)"`.
- Race line, HUD 2245-2246 and panel 2358-2363 (replacing `ev`/`tEV`):
  ```pine
  float dT = math.max(0.0, activeLv.distance(close))
  float rk = math.abs(close - invL)
  float pT = f_raceH(dT, rk, nz(potSig), 0.0, H)
  float pS = f_raceH(rk, dT, nz(potSig), 0.0, H)
  // "≤H  target 18% · stop 52% · neither 30%"
  ```
  The ledger's observed triple needs no new state: target first `raceSt[1]/raceSt[4]`, stop first
  `(raceSt[0] − raceSt[1])/raceSt[4]`, neither `1 − raceSt[0]/raceSt[4]` (Full view RACE row).
- Panel 2404-2408: `p80Mae = maeAll.size() >= 20 ? maeAll.percentile_linear_interpolation(80) : na`, labelled
  "heat p80 (all)".
- Hit row 2393: `str.tostring(100.0 * kA / nA, "0.0") + "% / exp " + str.tostring(100.0 * stPE.get(4) / nA, "0.0") + "%"`.
- L50 2395-2396: `roll50x.size() > 0 ? 100.0 * roll50x.sum() / roll50x.size() : na`, shown as `f_signed(x, "0") + "pp L50"`.
- 2067: keep `activePoT := sweptNow ? 0.95 : …` for the filter, and print "HIT" wherever the PoT is formatted when
  `sweptNow`.

**Ledger measurability.** The readouts *are* ledger statistics. Acceptance: the shown P(T ≤ H) per bucket equals that
bucket's hit fraction; on ES 1h the 2-ATR ETA reads about 19 bars (A) and the model fallback 17-22 bars (κ = 1.4-1.6,
B).

**Evidence.** Strong (censoring theory, optional stopping, Brownian first passage) and moderate (7-dataset measurements).

**Risk.** The numbers look worse but are true ("ETA > 30b" for far targets). The tooltip must say why. No compile risk
beyond new arrays and one helper declared after `f_book`.

**Effort.** S (about 45 lines).

---

### SKEP-2 (P1, effort M) · Mirror-controlled, anytime-valid EDGE with a three-way verdict, a baseline check and a data-integrity cue [A✓, B-extended and measured]

**Why.**
- The one-sample EDGE is shifted by baseline miscalibration: −4 to +1 pp per dataset, ±2-3 pp per clock window, +3 to
  −8 pp by volatility state. Those errors are direction-free.
- B measured on 288 real null paths (§2.4 A): an anytime-valid boundary alone still shows a false "✓" on 4.5% of paths and
  on 23% of busy-hour paths. With the mirror: **0.7%** (centred) / **0.3%** (self-normalised). Power on side skill rises
  (5m: 44% → 71%).
- The mirror test answers the exact claim "this choice beats a level at the same distance on the other side". The
  regime-split baseline still removes beta.

**Algorithm.**
- *Mirror record.* For each DOL record opened at bar t (step 20), open a mirror: the level at the same ATR distance `d0` on
  the opposite side, same hit rule (`liq`), same H, its own `pBase = f_potBase(d, −side)`.
- *Residuals.* `r = y − pBase` (DOL), `rm = y_m − pBase_m` (mirror), paired `D = r − rm`, pair sum `P = r + rm`.
- *Blocks* keyed by the DOL's *open* bar (SKEP-3); a block enters the statistics only when all its records have resolved
  (`g < gMax = f_blk(bar_index − H)`).
- *Statistics.* `S = ΣD_g`, `N` = pairs, mirror edge `Δ̄ = S/N`, centred variance `V = G/(G−1)·Σ(D_g − N_g·Δ̄)²`.
- *Anytime band.* `b(V) = √((V+ρ)·ln((V+ρ)/(ρα²)))`, ρ = 10, α = 0.05 (0.025 once SKEP-9's α budget lands); half-width
  `hw = b(V)/N`; MDE (80% power) `= (b(V) + 0.84·√V)/N`. ρ = 10 is tightest near V ≈ 82; typical 5,000-bar ledgers reach
  V ≈ 100-300, where the boundary is within 3% of its optimum (z ≈ 3.04-3.12), so one ρ fits all charts.
- *Three-way verdict* (Darmanin 2026) with a materiality threshold `δ` (input, default 2 pp on the paired scale):
  - `G < 20` or `n_eff = N·V_ind/V < 30` → "CALIBRATING" ("H too long for the window" when G binds);
  - `Δ̄ − hw > 0` → "✓ BEATS MIRROR";
  - `Δ̄ + hw < 0` → "✕ WORSE THAN MIRROR";
  - `Δ̄ + hw < δ` → "✕ NO MATERIAL EDGE (< δ pp)";
  - otherwise "~ INCONCLUSIVE (MDE x pp)". Never "NO EDGE".
- *Rigorous variant* (documented, optional). Under the sharp null "the side label carries no information", D is
  symmetric, so `S` with the self-normalised `V_sn = ΣD_g²` is a non-asymptotic test (1.30). It is the most conservative
  choice (0.3% false alarms) at some cost in power (5m 63% vs 71%).
- *Baseline check.* `bias = ΣP/(2N)` estimates the baseline's own error (plus half of any genuine pool-magnet effect). If
  `|bias| > 2·SE` and `|bias| > 2 pp`: "⚠ BASELINE OFF x pp", and the one-sample EDGE row is marked "UNRELIABLE".
- *Data-integrity cue* [B-NEW]. Count confirmed bars in the calc window whose close-to-close change exceeds 4 ATR. Above 1%
  of bars (clean CME 0.3-0.5%, roll-gapped GC 2.2%): "⚠ DATA GAPS: use back-adjusted continuous data".

**Pine v6 sketch.**

Type (append to `Trial`, 375-395):
```pine
    int   role   = 0      // 0 DOL · 1 mirror · 2-6 league roles (SKEP-5)
```

Inputs (G_ACC, after 192):
```pine
float matPP = input.float(2.0, "Material Edge (pp)", minval = 0.0, step = 0.5, group = G_ACC,
  tooltip = "Smallest edge over the mirror level that would matter. The panel says NO MATERIAL EDGE only when the anytime interval rules out an edge this large.")
```

Global (after 307) and state (after 1079):
```pine
int blkW = math.max(2 * H, math.min(math.max(4 * H, int(86400.0 / chartS)), int(calcBars / 25)))   // SKEP-3
var array<float> blkE = array.new<float>()   // Σ(y − pBase), DOL records, by open block
var array<float> blkD = array.new<float>()   // Σ(r − rm)
var array<float> blkP = array.new<float>()   // Σ(r + rm)
var array<float> blkN = array.new<float>()   // DOL record count
var array<float> blkV = array.new<float>()   // Σ p(1 − p) of DOL and mirror records (independent variance of D, for n_eff)
var array<float> blkR = array.new<float>()   // Σ R_adj (SKEP-4)
var int jumpN = 0                            // bars with |Δclose| > 4 ATR in the calc window
var int barN  = 0
```

Helpers (STATE HELPERS, before `f_book`):
```pine
f_blk(int b0) =>
    int id = math.max(0, int(math.floor((b0 - math.max(0, last_bar_index - calcBars)) / blkW)))
    while blkN.size() <= id
        blkE.push(0.0)
        blkD.push(0.0)
        blkP.push(0.0)
        blkN.push(0.0)
        blkV.push(0.0)
        blkR.push(0.0)
    id

f_csBound(float v, float rho, float alpha) =>
    float vv = math.max(v, 0.0) + rho
    math.sqrt(vv * math.log(vv / (rho * alpha * alpha)))
```
(`f_blk` must precede `f_book`; `f_csBound` is the same as calib_ml CAL-2's, so declare it once.)

`f_book` (replacing the `cluSt` block 1463-1469; existing stats guarded by `if t.role == 0`):
```pine
    int   g = f_blk(t.bar0)
    float r = y - t.pBase
    if t.role == 0
        blkE.set(g, blkE.get(g) + r)
        blkD.set(g, blkD.get(g) + r)
        blkP.set(g, blkP.get(g) + r)
        blkN.set(g, blkN.get(g) + 1.0)
        blkV.set(g, blkV.get(g) + t.pBase * (1.0 - t.pBase))
    else if t.role == 1
        blkD.set(g, blkD.get(g) - r)
        blkP.set(g, blkP.get(g) + r)
        blkV.set(g, blkV.get(g) + t.pBase * (1.0 - t.pBase))
```

Opening (step 20, 2039-2045):
```pine
            if not has and openT.size() < math.max(160, 4 * H + 4)
                Trial tD = f_openTrial(activeLv)
                openT.push(tD)
                float dm = tD.d0 * atr
                openT.push(Trial.new(lvId = -activeLv.id - 1, grp = tD.grp, side = -tD.side, edge = close - tD.side * dm,
                  inv = close + tD.side * atr, risk = atr, entry = close, atr0 = atr, bar0 = bar_index,
                  pBase = f_potBase(dm, -tD.side), pRace = 0.5, rr0 = 1.0, d0 = tD.d0, liq = tD.liq, role = 1))
```
`f_step` works unchanged; the mirror's race fields are unused because `f_book` skips race stats for role ≠ 0.

Data-integrity counter (engine block, step 0):
```pine
    if inCalc
        barN += 1
        if math.abs(close - nz(close[1], close)) > 4.0 * nz(atr[1], atr)
            jumpN += 1
```

Centred block statistics (after `f_book`):
```pine
// over closed blocks g < gMax: [Σ X, Σ N, centred G/(G−1)·Σ(X_g − N_g·m)², G]
f_cluVar(array<float> X, int gMax) =>
    float sx = 0.0
    float sn = 0.0
    float v  = 0.0
    int   G  = 0
    int   gE = math.min(gMax, X.size())
    if gE > 0
        for g = 0 to gE - 1
            sx += X.get(g)
            sn += blkN.get(g)
        float m = sn > 0 ? sx / sn : 0.0
        for g = 0 to gE - 1
            float ng = blkN.get(g)
            if ng > 0
                v += math.pow(X.get(g) - ng * m, 2)
                G += 1
    [sx, sn, G > 1 ? v * G / (G - 1) : na, G]
```

Panel (2383-2401, last bar):
```pine
int gMax = f_blk(bar_index - H)
[sD, nD, vD, gD] = f_cluVar(blkD, gMax)
[sP, nP, vP, gP] = f_cluVar(blkP, gMax)
float vI = 0.0
if gMax > 0
    for g = 0 to math.min(gMax, blkV.size()) - 1
        vI += blkV.get(g)
float bD   = na(vD) ? na : f_csBound(vD, 10.0, 0.05)
float mD   = nD > 0 ? 100.0 * sD / nD : na
float hwD  = nD > 0 and not na(bD) ? 100.0 * bD / nD : na
float mdeD = nD > 0 and not na(vD) ? 100.0 * (bD + 0.84 * math.sqrt(vD)) / nD : na
float nEff = not na(vD) and vD > 0 ? nD * vI / vD : 0.0   // effective number of independent pairs
string vMir = gD < 20 or nEff < 30 ? "CALIBRATING" : mD - hwD > 0 ? "✓ BEATS MIRROR" : mD + hwD < 0 ? "✕ WORSE THAN MIRROR" :
  mD + hwD < matPP ? "✕ NO MATERIAL EDGE" : "~ INCONCLUSIVE"
float bias   = nP > 0 ? 100.0 * sP / (2.0 * nP) : na
float seBias = nP > 0 and not na(vP) ? 100.0 * math.sqrt(vP) / (2.0 * nP) : na
bool  baseOff = not na(seBias) and math.abs(bias) > 2.0 * seBias and math.abs(bias) > 2.0
bool  gaps    = barN > 0 and jumpN >= 10 and jumpN > 0.01 * barN
```
Rows (Compact):
- `EDGE·MIRROR  +2.1pp ±3.8  ~ INCONCLUSIVE (MDE 5.5)`
- `BASELINE  −0.4pp ✓` or `⚠ BASELINE OFF −4.0pp` or `⚠ DATA GAPS`
- the old one-sample row becomes `vs RANDOM +x pp` (no verdict word), marked "UNRELIABLE" when `baseOff or gaps`.

**Cost.** Doubles the open records (O(1) each per bar); the panel loops are O(G ≤ 200) on the last bar only.

**Ledger measurability.** This is the measurement layer. Acceptance: on `anytime_mirror.py`-style clock-timed placebo
pickers, P(ever "✓") ≤ 2%; on the informed picker, detection ≥ the one-sample test's.

**Evidence.** Moderate (A: 4 symbols × 3 windows × 16 seeds + 76 independent 1-minute segments; B: 288 null + 96 informed
real paths) and strong (theory of paired designs, confidence sequences, self-normalised martingales).

**Risk.**
- A genuine pool-magnet effect is credited as edge (intended: "beats a level at the same distance").
- Side-asymmetric miscalibration (skew, crash asymmetry) is not cancelled; the side-split surface handles most of it.
- With very long H the block count binds (CALIBRATING with a reason).

**Effort.** M (about 100 lines).

---

### SKEP-3 (P1, effort S) · Correct the overlap variance: open-keyed, centred, wide blocks with a block-count guard [A✓, B-refined]

**Why.** `cluSt` (1463-1469) is uncentred, keyed by *booking* bar and 2H wide. Under intraday seasonality it is
conservative (z sd 0.76) and costs power (a +3.3 pp edge flagged 10% vs 30%; §2.3 B). It has no guard against few blocks
(about 5 at H = 450). It also feeds the Wilson design effect and calib_ml CAL-1/CAL-2.

**Algorithm.**
- [B-CORRECTED width] `blkW = max(2H, min(max(4H, barsPerDay), calcBars/25))`. A's `min(barsPerDay, calcBars/30)` gave 166
  bars on 1-minute charts (2.8 hours, not a session) and 2H on 1h/daily. B's version keeps G ≥ 25 and uses at least 4H
  where the window allows (1.21): with calcBars 5,000 and H 30 it gives 200 bars on 1m/5m, 120 on 15m/1h/4h/D.
- One-sample EDGE: `S = ΣE_g`, `V = G/(G−1)·Σ(E_g − N_g·ē)²`, `deff = V/Σp(1−p)` (floor `0.25·Σp(1−p)` only as a tiny-G guard).
- `CALIBRATING` while G < 20 (calib_ml CAL-2).

**Pine v6 sketch.** Uses `blkW`, `f_blk`, `blkE`, `blkV` and `f_cluVar` from SKEP-2 (the minimal subset if SKEP-2 is deferred).
Remove `cluSt` (1077, 1463-1469). Panel (2384-2389):
```pine
            int gMax = f_blk(bar_index - H)
            [sE, nE, vE, gE] = f_cluVar(blkE, gMax)
            float vInd  = stPV.get(4)
            float vEdge = na(vE) ? vInd : math.max(vE, 0.25 * vInd)
            float deff  = vInd > 0 ? vEdge / vInd : 1.0
```

**Ledger measurability.** Re-run `ledger_null.py` with `blkW`: null z sd 0.9-1.1 in all three scenarios.

**Evidence.** Moderate (A's simulation; B's batch-means arithmetic) and strong (cluster-robust inference; few-clusters
bias, Cameron, Gelbach & Miller 2008).

**Risk.** Noisy with few blocks; the G ≥ 20 gate and the floor handle it.

**Effort.** S (about 25 lines; shared with SKEP-2).

---

### SKEP-4 (P1, effort S) · Model-free R-expectancy test with a drift (beta) adjustment and an optional cost [A✓, B-extended]

**Why.**
- For a trader the question is "do these targets pay", not "are they touched".
- Under any martingale every target/stop/time-out rule has E[R] = 0 (optional stopping). The ledger's `rOut` is near
  martingale-consistent: [B] on 1-minute truth, random pickers average −0.03 to +0.03 R, and the coarse-bar booking bias is
  ≤ +0.02 R (§2.4 B). So average R is an edge test that needs **no baseline model**: immune to baseline miscalibration and
  to the decided-race conditioning that breaks the EV.
- The only nuisance is drift (beta), removed by Wald's identity `E[R] = side·μ·E[τ]/risk`.
- [B-NEW] Costs: on 1-5 minute charts friction can exceed a signal's gross content (Mesfin 2026; the open-source sweep test).
  The readout must say "gross" or "net".

**Algorithm.**
- Prequential drift `μ̂_t` = running mean of `close − close[1]` over confirmed bars up to the record's open.
- For each DOL record: `R_adj = rOut − side·μ̂·τ/risk − cost/risk`, τ = bars until the race resolved (or H), `cost =
  costTicks·syminfo.mintick`.
- Per open-block sums go to `blkR`; `R̄ = ΣR/N`, `V_R` centred (SKEP-3), anytime band `±b(V_R)/N`.
- Verdict words: "✓ PAYS" (lower bound > 0), "✕ LOSES" (upper bound < 0), "~ INCONCLUSIVE".
- Compact row: `R̄ +0.06R ±0.11 (gross) · PF 1.12 · long 62%`. The long share discloses directional tilt.
- `pRace` stored at open becomes drift-free (QPOT-01), so `f_raceAdj` shifts relative to geometry (and is gated, CAL-11).

**Pine v6 sketch.**
- `Trial`: append `float mu0 = 0.0` and `int rBars = 0`.
- Input (G_ACC): `float costTk = input.float(0.0, "Cost per Trade (ticks)", minval = 0.0, step = 0.5, group = G_ACC, tooltip = "Round-trip spread, commission and slippage. 0 shows gross R.")`.
- State: `var array<float> driftSt = array.from(0.0, 0.0)` (Σ Δclose, n) and `var array<float> sideSt = array.from(0.0, 0.0)`
  (long records, all records). Update at the top of the engine block:
  ```pine
  driftSt.set(0, driftSt.get(0) + close - nz(close[1], close))
  driftSt.set(1, driftSt.get(1) + 1.0)
  ```
- `f_openTrial` (1426-1431): add `mu0 = driftSt.get(1) > 0 ? driftSt.get(0) / driftSt.get(1) : 0.0`.
- `f_step` (1434-1459), after the `if t.race == 0` block: `if t.race != 0 and t.rBars == 0` → `t.rBars := t.bars`.
- `f_book`, role 0:
  ```pine
  int   tau  = t.rBars > 0 ? t.rBars : t.bars
  float rAdj = t.rOut - t.side * t.mu0 * tau / math.max(t.risk, syminfo.mintick) - costTk * syminfo.mintick / math.max(t.risk, syminfo.mintick)
  blkR.set(g, blkR.get(g) + rAdj)
  sideSt.set(0, sideSt.get(0) + (t.side == 1 ? 1.0 : 0.0))
  sideSt.set(1, sideSt.get(1) + 1.0)
  ```
- Panel: `[sR, nR, vR, gR] = f_cluVar(blkR, gMax)`, then R̄, its band and the verdict. Move the RACE row into Compact.

**Ledger measurability.** Direct. Acceptance: on driftless synthetic data R̄ is within its band in ≥ 95% of runs; on A's
always-long picker (§2.3 E) `R_adj ≈ 0` while the raw R̄ > 0.

**Evidence.** Strong (optional stopping, Wald) and moderate (races near-martingale on real data, quant_pot; B's 1-minute
truth).

**Risk.**
- [B-CORRECTED] Intrabar ordering is *not* a material risk (≤ 1.7% of trials, ≤ 0.02 R).
- On gappy contracts with tight stops the null is "E[R] ≤ 0" (GC 5m tight: −0.15 R), so the test loses power there.
- R depends on the invalidation rule (nearest opposing pool), a design choice; the test is about *this* trade definition.

**Effort.** S (about 40 lines).

---

### SKEP-6 (P2, effort S) · Null-default modifiers: unsupported ICT multipliers start neutral and must earn weight [A✓, B-regraded]

**Why.** Hard-coded modifiers assert effects the evidence does not show (§3.2). Each moves scores by more than the
4-point hysteresis (147), so each is a source of target switches with no measured benefit. The skeptic's principle: *the
default is the null*; a feature gets weight when the ledger, on this chart, shows it helps.

**Defaults to change** (each kept as a user option, so no feature is lost):

| Input / code | Current | Null default | Evidence (corrected grade) |
|---|---|---|---|
| `driftW` (185) | 0.5 | **0.0** | quant_pot, quant_regime: drift hurts log-loss 1.2-7.1% in every regime (moderate) |
| `f_kzAff` (applied 1941) | always | behind `useKzAff = false` | session_stats: within ±3 pp of the clock null (moderate) |
| tests term `0.35·min(tests, 6)` (682) | + | **0** | calib_ml: 5m +0.03, 1h −0.43 logit, not Holm-significant (weak, sign negative) |
| tier term `1.2·tier` (682) | + | **0.4·tier** | calib_ml: −0.14 / −0.27 logit, Holm p 0.07 (unsupported) |
| `wConf` (143) | 15 | **5**, plus CAL-5 (no self-confluence) | calib_ml: no lift, Holm p 0.11; self-confluence bug (unsupported) |
| `liqEvt` raid → D (1579-1582) | hold +, reject − | `wL` (157) **0** | quant_regime: 0.497-0.510 either way (moderate) |
| `wDraw` + draw-side-first (145, 1975) | 30, gate 0.35 | REG-3: D does not steer selection unless it passes the ledger; hard ER20 ≥ 0.40 gate as the legacy option | quant_regime: D-first −9 to −12 pp (moderate) |

Then measure: SKEP-5 runs the *old* hand score as a shadow role. Release notes report the per-chart league results, and
the defaults stay null unless the old score wins beyond the anytime bound on most charts.

**Pine v6 sketch.**
- Input default edits (143, 145, 157, 185).
- `bool useKzAff = input.bool(false, "Session Affinity (unproven)", group = G_FLOW, tooltip = "London raids Asia, NY raids London and the previous day. Off by default: session take rates match a clock-matched random path within ±3 pp.")`; at 1941 `lv.mult *= useKzAff ? f_kzAff(kz, lv.src) : 1.0`.
- `float wTests = input.float(0.0, …)` and `float wTier = input.float(0.4, …)` (G_SCORE) replacing the literals 0.35 and
  1.2 at 682.
- Old-score shadow: compute `scoreOld` in `evaluate` alongside `score` (a second weighted sum with the old constants,
  O(1)) and pick the role-6 shadow by it (SKEP-5).

**Ledger measurability.** Yes, via SKEP-5 (old vs new score as paired roles) and SKEP-2 (mirror edge per variant).

**Evidence.** Moderate (five sibling studies with consistent signs; only EQ survives multiplicity) and strong (Osler,
Garzarelli on the mechanism side).

**Risk.** It changes which target shows, and the brief says not to undo decisions without strong evidence (draw-side
first). Mitigation: the option stays, and REG-3's hard gate keeps "the draw follows an efficient trend" where geometry
already agrees (76-82% of the time). The reference product advertises session confluence; keep it as an option.

**Effort.** S (about 30 lines plus the shadow role).

---

### SKEP-10 (P2, effort S) · Honest visual record: audit line, ghosts for every outcome, selection time [A, B-extended and promoted from P3]

**Why.**
- Users judge an indicator by scrolling history. Today the record is survivorship-biased (§3.1): a target out-scored by a
  same-side challenger vanishes without a ghost (2014-2023); "✕ SWEPT" carries no time to hit although 87% of 2-ATR levels
  are touched within 300 bars; ghost boxes start at the level's origin, not at the bar the engine committed.
- An optional step line of the DOL's near edge shows every switch, abandonment and hit, so users can audit the ledger and
  the "targets jump around" complaint by eye.

**Algorithm and Pine v6 sketch.**
1. *Audit line* (input `showAudit = false`, G_GHOST after 211). Data window block (2438-2444):
   ```pine
   float dolEdgeOut = na
   int   dolSideOut = 0
   if not na(activeLv)
       dolEdgeOut := activeLv.nearEdge()
       dolSideOut := activeLv.side
   plot(dolEdgeOut, "DOL Price", color = dolSideOut == 1 ? cAbove : cBelow, style = plot.style_steplinebr, linewidth = 2,
     display = showAudit ? display.all : display.data_window)
   ```
   Values come from confirmed-bar state, so the line does not repaint.
2. *Time-stamped SWEPT ghosts* (1586):
   ```pine
   int    held = bar_index - activeSince
   string why  = hit ? "✕ SWEPT " + str.tostring(held) + "b" + (held <= H ? " ≤H" : " >H") : "⊘ EJECTED"
   f_ghost(lv, why, ghostB, ghostL, ghostMax, lv.side == 1 ? cAbove : cBelow, cGhost)
   ```
3. *REPLACED / DROPPED ghosts* (after 2021-2023):
   ```pine
        if showGhost and curI >= 0 and curElig and pick != curI
            Level old = pool.get(curI)
            f_ghost(old, (pick >= 0 ? "↷ REPLACED " : "⊘ DROPPED ") + str.tostring(bar_index - activeSince) + "b", ghostB, ghostL,
              ghostMax, old.side == 1 ? cAbove : cBelow, cGhost)
   ```
4. *Commit-anchored ghosts.* Give `f_ghost` (1253) an `int fromBar` parameter and pass `activeSince`, so a ghost box spans
   exactly the bars the engine asserted the target (`box.new(f_x(fromBar), …)`).
5. *Clean tooltip* (2206): append `"\nselected " + str.tostring(bar_index - activeSince) + " bars ago"`.

**Ledger measurability.** Indirect: it lets users check the ledger by eye. Count check: ghosts by reason should match the
ledger's resolved records over the same span.

**Evidence.** Strong for the rationale (survivorship, recurrence: §2.4 C); weak (UX reasoning) for the value.

**Risk.** Clutter (both features default off; ghosts are capped by `ghostMax`). The `DOL Price` data-window value changes
from `price` to the near edge (what the ledger grades); note it in the release notes. Box count stays within the existing
ghost cap.

**Effort.** S (about 25 lines).

---

### SKEP-5 (P2, effort M) · Strong-baseline league table: DOL vs NEAREST, GEO, TREND, RUNNER-UP and OLD-SCORE on the same bars [A✓, B-sharpened]

**Why.**
- Beating a *random* level is a low bar. Every picker's hit rate matches its baseline, and pickers differ in what they
  deliver: max-reach d·PoT 1.10-1.43 ATR per target, hand score 0.86-1.09, nearest 0.66-0.93 (calib_ml).
- D-first selection loses 9-12 pp of first-touch accuracy to geometry (quant_regime).
- Without a head-to-head, a "✓" over random says nothing about whether the scoring adds value over "take the nearest pool".
- A paired comparison on identical bars is a Diebold-Mariano-type test (Diebold & Mariano 1995): shared-path noise cancels,
  so it is far more powerful than comparing two separate hit rates.

**Algorithm.** Each time a DOL record opens (step 20), open role records on the *same bar*, chosen in one O(pool) pass over
levels with `minDistATR ≤ dA ≤ maxATR`:
- **NEAREST** (role 2): the smallest distance, either side.
- **GEO** (3): the largest `dA·f_potBase(d, side)`, the most expected ATR delivered (calib_ml CAL-8).
- **TREND** (4): the nearest on the `htfBias` side (skipped when `htfBias == 0`).
- **RUNNER-UP** (5): the second-highest score.
- **OLD-SCORE** (6): the top level under the pre-SKEP-6 constants (only when SKEP-6 lands).

A role record is opened even when it picks the same level as the DOL (its paired difference is then 0), so pairs stay
aligned. Each role gets its own invalidation via `f_invalidation`, so R is comparable. Per open block and role: excess
`Σ(y − pBase)`, `Σ R_adj`, ATR delivered `Σ y·d0`. Paired differences DOL − role use the SKEP-3 variance and the SKEP-2
boundary.

Full-view rows, for example:
- `vs NEAREST  Δexc +0.4pp ±3.1 · ΔR +0.03 ±0.09 · ATR 1.02 vs 0.81`
- the same for GEO, TREND, RUNNER-UP, OLD-SCORE; a "BEST" marker on any role that beats the DOL beyond the bound.

**Pine v6 sketch.**
- Roles 2-6 in `Trial.role`; `lvId = −1000000 − role` so the `has` check (2040-2043) ignores them.
- One flat array per statistic indexed `g * 8 + role` (`blkE8`, `blkR8`, `blkY8`), grown by 8 slots per block in `f_blk`.
- `f_book` routes by role and skips the main stats for roles ≥ 1.
- Cap `openT.size() < 512`; when full, role records are skipped and the panel says "league paused" (H ≥ 60).
- Prefer implementing this on CAL-3's `Probe` mechanism if CAL-3 lands first (its roles 1-5 already include nearest,
  random, runner-up and mirror); add GEO, TREND and OLD-SCORE there, plus R via a per-role invalidation.

**Ledger measurability.** Yes; it *is* an A/B harness for any scoring change (switch defaults only when a shadow wins beyond
the bound on most charts).

**Evidence.** Moderate (sibling replicas) and strong (theory of paired comparisons).

**Risk.** CPU: up to five extra `f_invalidation` calls per opening (about one opening per few bars): negligible. A longer
panel (Full view only). Overlaps CAL-3, so build one shared role mechanism.

**Effort.** M (about 90 lines).

---

### SKEP-8 (P2, effort S) · Honest claims: PoT, the PoT filter, "destination" and the words of every verdict [A✓]

**Why.** Users read words, not methods. Four current claims overstate:
1. "the pool the market is most likely drawing to next": by design inner pools are taken first (685); the DOL is a
   destination.
2. PoT shown as the level's probability: it is the probability that a level at that *distance* is touched (geometry plus
   regime); "how far", not "how good".
3. "Minimum PoT to Show DOL" reads as a quality filter: it is a distance filter.
4. "✕ NO EDGE" printed when the edge is merely not measurable.

**Text.**
- README intro: "highlights the highest-scoring *destination* for the current leg. Inner pools on the way are usually taken
  first."
- PoT tooltip (label `tooltip`, and `potModel` at 181-182): "PoT = how often price on this symbol travelled this distance
  within H bars in the same HTF regime. It measures distance and volatility, not the quality of this particular level.
  Random levels 1 / 2 / 3 ATR away are touched about 75-80 / 55-60 / 40-45% of the time within 30 bars."
- `minPoT` tooltip (180): "Filtering by PoT filters by distance: a higher minimum shows nearer targets."
- Every verdict uses the three-way words of SKEP-2/SKEP-4 ("BEATS", "NO MATERIAL EDGE", "INCONCLUSIVE (MDE x)"), never
  "NO EDGE"; the Clean style shows no verdicts.
- Accuracy-panel tooltip: "Hit rates are not skill: a random level at the same distance would score the 'exp' figure."
- Do not adopt the reference product's unfalsifiable phrasing ("highly probable target").

**Ledger measurability.** Aligns the words with what the ledger measures.

**Evidence.** Strong (definitions) and §2.3 D / §2.4 C for the base rates quoted.

**Risk.** None technical. It may feel less "magical", which is the point.

**Effort.** S (text only, about 15 lines).

---

### SKEP-7 (P2, effort S) · Forward-only sub-ledger, split-half stability and in-sample disclosure [A✓, B-extended]

**Why.**
- Every historical record is in-sample to the settings: the user tuned them on this chart and the developer tuned the
  defaults on charts. The best of 45 settings has E[max z] = 2.2 under the null (§2.3 G).
- The only out-of-sample evidence an on-chart ledger can produce is records opened *after* the script was loaded with
  fixed settings (realtime bars). Changing any input recompiles and resets them, which is the right property.
- [B-NEW] The commonest failure in recent falsification studies is one strong sub-period masking weak ones (Mesfin 2026;
  the open-source sweep test). A split-half check is a cheap disclosure.

**Algorithm and Pine v6 sketch.**
- `Trial`: append `bool fwd = false`; `f_openTrial` sets `fwd = not barstate.ishistory`.
- State: `var array<float> fwSt = array.new<float>(4, 0.0)` = [n, k, Σp, ΣR_adj], updated in `f_book` for role 0 when `t.fwd`.
  Row: `FORWARD n 9 · hit 56% / exp 51% · R̄ +0.2` or `FORWARD — waiting for live bars`.
- Split-half (panel): with `gMax` from SKEP-2, `[s1, n1, …] = f_cluVar` over blocks `< gMax/2` and the rest (or two simple
  loops over `blkD`), row: `HALVES  +1.8pp / −0.6pp  ✕ unstable` (✓ when both halves have the same sign).
- Tuned-input counter at global scope (after the inputs):
  ```pine
  int nTuned = (wProx != 25.0 ? 1 : 0) + (wFresh != 10.0 ? 1 : 0) + (wConf != 15.0 ? 1 : 0) + (wDens != 20.0 ? 1 : 0) +
     (wDraw != 30.0 ? 1 : 0) + (minScore != 35.0 ? 1 : 0) + (hyst != 4.0 ? 1 : 0) + (maxATR != 10.0 ? 1 : 0) +
     (minDistATR != 0.5 ? 1 : 0) + (halfLife != 150.0 ? 1 : 0) + (potH != 30 ? 1 : 0) + (dGate != 0.35 ? 1 : 0) +
     (pivLen != 5 ? 1 : 0) + (eqTol != 0.10 ? 1 : 0) + (fvgQMin != 0.45 ? 1 : 0) + (obQMin != 0.40 ? 1 : 0)
  ```
  The literals must track the input defaults (they change if SKEP-6 lands).
- ACCURACY header tooltip (2377): "History records are in-sample: k settings differ from defaults, and the defaults were
  chosen on charts. Only FORWARD records are out-of-sample."

**Ledger measurability.** Direct.

**Evidence.** Strong (out-of-sample principle; Sullivan et al. 1999; Zhang 2026: Sharpe ≈ 3 → 0.26 on the holdout).

**Risk.** Forward n grows slowly (about 1 record per few bars) and resets on reload; the row mostly says "n small", which is
honest.

**Effort.** S (about 35 lines).

---

### SKEP-9 (P3, effort S) · Multiple-comparison discipline: an α budget for the panel, exploratory family rows, gated learning [A✓, B-reframed]

**Why.**
- The Full view shows 4 family rows plus RACE (5 at-a-glance tests: 11% chance of a spurious standout at one look, more
  with peeking); the league adds 5 more.
- `f_calMult` acts on the same noisy family rates (≥ 10% off under the null in 47-66% of families).
- [B-NEW] With confidence sequences, multiplicity is handled by splitting α: if each claim gets level `α·w_k` with
  `Σw_k ≤ 1`, the chance of *ever* a false claim on the panel is ≤ α under any dependence and any peeking (weighted Ville;
  Benhamou et al. 2026).

**Algorithm.**
- Declared α budget (0.05 total): mirror edge (SKEP-2) 0.025, R̄ (SKEP-4) 0.025. These are the only rows with verdict words.
- Family rows and league rows are "exploratory": `hit / exp · excess ± band` in neutral colour, bands at α/k.
- `f_calMult(g)` (calib_ml CAL-1) applies a family multiplier only when that family's mirror excess passes its band at
  α = 0.05/4.

**Pine v6 sketch.**
- Per-family block arrays (one flat array of size `4·nBlocks`, index `g * 4 + fam`, grown in `f_blk`), filled in `f_book`.
- `f_csBound(v, 10.0, 0.025)` for the two primaries; `f_csBound(v, 10.0, 0.0125)` per family.
- Row text: `f_cell(dash, 1, row, str.tostring(100*kg/ng, "0") + "% / " + str.tostring(100*stPE.get(g)/ng, "0") + "%", dim, na)`.
- In `f_calMult(g)`: `return 1.0` unless the family passes.

**Ledger measurability.** Yes: under placebo pickers the panel's total false-verdict rate stays ≤ 5%.

**Evidence.** Strong (Bonferroni/Holm, data-snooping literature, Ville's inequality) and moderate (calib_ml null simulations;
PROMOTE's replay).

**Risk.** Family multipliers will rarely activate at default depth, which is the honest outcome given the MDE.

**Effort.** S (about 30 lines with SKEP-2's helpers).

---

## 5. How this fits the other study reports

- **calib_ml** (CAL-1 … CAL-11): SKEP-3 supplies the variance CAL-1/CAL-2 need and adds the block-width rule; SKEP-2 adds
  the *control* CAL-2 lacks (B measured that CAL-2's boundary alone still gives 4.5-23% false "✓" under clock-window
  miscalibration); SKEP-5 is CAL-3's role probes made paired, with R, GEO, TREND and OLD-SCORE; SKEP-9 gates CAL-1; CAL-5
  (self-confluence) is endorsed in SKEP-6; CAL-10's base-integrity guard gets SKEP-2's jump counter as a model-free cue.
- **quant_pot** (QPOT-01 drift removal, QPOT-02 finite-horizon race, QPOT-04 PoT grading): SKEP-6 adopts QPOT-01 as a null
  default; SKEP-1's race triple uses the same `f_raceH` with μ = 0 that QPOT-02 calibrates; QPOT-04 grades calibration,
  while SKEP-2/4 grade edge.
- **quant_regime** (REG-1 horizon-matched unit, REG-3 draw gate): REG-1 reduces the volatility-state bias of `pBase` that
  SKEP-2's mirror otherwise has to cancel; REG-3 is adopted in SKEP-6 and measured by SKEP-5.
- **session_stats / ict_time** (learned session effects): SKEP-6 turns the fixed affinities off by default; learned tables
  enter only through the SKEP-5/9 gate.
- **ict_pd / ict_liq** (array prior, sweep learner): every learned modifier must pass the SKEP-2 mirror test and the SKEP-9
  α budget before it changes scores.
- **trade_mgmt**: confirms the intrabar rule; SKEP-4's R test grades the same trade definition trade_mgmt manages.

---

## 6. Sources

Read directly by B (paper index full-text passages or abstracts):
- Taylor, V. (2026). Evaluating the Predictive Validity of ICT's AMD Model on CME E-Mini NASDAQ-100 Futures. arXiv:2610.35887. https://arxiv.org/abs/2610.35887 (tables 1, 2, 4-7 read). Code: https://github.com/veertaylor19/amd-backtest
- Mesfin, M. (2026). Structural Limits of OHLCV-Based Intraday Momentum Signals in MNQ Futures. arXiv:2605.04004. https://arxiv.org/abs/2605.04004 (sections 4.1-4.7, 5, 6 read)
- Garzarelli, F., Cristelli, M., Zaccaria, A. & Pietronero, L. (2014). Memory effects in stock price dynamics: evidences of technical trading. Sci. Rep. 4:4487; arXiv:1110.5197 (table 1, sections 3-5 read)
- Chung, K. & Bellotti, A. (2021). Evidence and Behaviour of Support and Resistance Levels in Financial Time Series. arXiv:2101.07410 (sections 3-4 read)
- Johari, R., Pekelis, L. & Walsh, D. (2017/2019). Always Valid Inference: Continuous Monitoring of A/B Tests. arXiv:1512.04922 (introduction read)
- Howard, S., Ramdas, A., McAuliffe, J. & Sekhon, J. (2020). Time-uniform Chernoff bounds via nonnegative supermartingales. Probability Surveys; arXiv:1808.03204 (Lemma 3, Fact 1, §4.3 read)
- Darmanin, A. (2026). Retail Trader's Ruin: An Anatomy of Popular Signal Failure. arXiv:2607.20093 (sections 1, 3, 5 read)
- Sokolovsky, A. & Arnaboldi, L. (2020/2022). A Generic Methodology for the Statistically Uniform & Comparable Evaluation of Automated Trading Platform Components. arXiv:2009.09993 (§4.2 and tables S2-S3 read)
- Gençay, E. (2026). What survives honest evaluation? arXiv:2608.27734 (abstract)
- Coqueret, G. (2023). Forking paths in financial economics. arXiv:2401.08606 (abstract)
- Jung, J. & Lee, K. (2026). Do Round Numbers Hold Prices? arXiv:2610.34787 (abstract)
- Benhamou, E. et al. (2026). Can We Stop the Backtest Yet? Anytime-Valid Promotion Tests for Adaptive Financial Research Agents. arXiv:2611.03384 (abstract)
- Zheng, T. (2026). On the Boundary of Admission Gates. arXiv:2610.07701 (abstract)
- Chen, M. et al. (2026). Agent Policy-Value Audit: Separating Transition Composition from Event Selection in Financial LLM Agents. arXiv:2610.04040 (abstract)
- Upadhyay, R. (2026). Do Time-Series Foundation Models Forecast Index-Futures Returns? A Preregistered Evaluation. arXiv:2611.12141 (abstract)
- Hall, N. (2026). Gate Design and Stage-Dependent Incentives in Retail Proprietary-Trading Evaluations. arXiv:2609.14859 (abstract)
- Open-source study repositories (README results read via raw GitHub): ivanalonso-dev/fib-liquidity-sweep-backtester (1-minute gold/BTC/ETH, IS/OOS); JamesRPowell/LiquiditySweep (60 days of 5-minute data, long-only; an example of a too-small, beta-exposed sample); sarahleesoffice/Macro_Liquidity_Sweep-_Backtester (time-window × news-day combinations ranked by win rate; an example of forking paths).

Read directly by A (paper index passages; not re-opened by B unless listed above):
- Zhang, H. (2026). Hard to Fool: A Bounded LLM Research Loop for Quantitative Finance. arXiv:2611.06607.
- Sermpinis, G. et al. (2018). Technical Analysis and Discrete False Discovery Rate. arXiv:1811.06766.
- Wang, S. et al. (2015). Testing the performance of technical trading rules in the Chinese market. arXiv:1504.06397.
- Harvey, C. & Liu, Y. (2020). False (and Missed) Discoveries in Financial Economics. arXiv:2006.04269.
- Chen, A. & Zimmermann, T. (2022). Publication Bias in Asset Pricing Research. arXiv:2209.13623.
- Howard, S., Ramdas, A., McAuliffe, J. & Sekhon, J. (2021). Time-uniform, nonparametric, nonasymptotic confidence sequences. Ann. Stat.; arXiv:1810.08240.
- Waudby-Smith, I. & Ramdas, A. (2020/2024). Estimating means of bounded random variables by betting. arXiv:2010.09686.
- Lallouache, M. & Abergel, F. (2013). Tick Size Reduction and Price Clustering in a FX Order Book. arXiv:1307.5440.
- Osler, C. (2000). Support for Resistance: Technical Analysis and Intraday Exchange Rates. FRBNY Economic Policy Review 6(2), 53-68. https://www.newyorkfed.org/medialibrary/media/research/epr/00v06n2/0007osle.pdf (re-fetched by B)
- Osler, C. (2003). Currency Orders and Exchange-Rate Dynamics. J. Finance 58(5):1791-1819. FRBNY SR125: https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr125.pdf (re-fetched by B)
- Osler, C. (2005). Stop-loss orders and price cascades in currency markets. JIMF 24(2). FRBNY SR150: https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr150.pdf (figures as re-checked by sibling ict_liq B)
- Sullivan, R., Timmermann, A. & White, H. (1999). Data-Snooping, Technical Trading Rule Performance, and the Bootstrap. J. Finance 54(5), 1647-1691.
- Bailey, D., Borwein, J., López de Prado, M. & Zhu, Q. (2014/2015). The Probability of Backtest Overfitting; Pseudo-Mathematics and Financial Charlatanism. https://papers.ssrn.com/abstract=2326253
- Probability of touch ≈ 2× probability ITM: https://www.optionsanalysissuite.com/documentation/probability-of-touch-vs-probability-itm
- TradingView script "Fair Value Gap (FVG) Statistics with Placebo Control" (WebSearch summary only): https://de.tradingview.com/script/Kbq3WncE-Fair-Value-Gap-FVG-Statistics-with-Placebo-Control/

Standard references cited for theory (not fetched): Feller (1951) and Parkinson (1980) on the range of Brownian motion;
de la Peña (1999), A general class of exponential inequalities for martingales and ratios, Ann. Probab.; Diebold & Mariano
(1995), Comparing predictive accuracy, JBES 13(3); Cameron, Gelbach & Miller (2008), Bootstrap-based improvements for
inference with clustered errors, REStat; Robbins (1970); Andersen & Bollerslev (1997); George & Hwang (2004); Wald (1945).

Vendor, SSRN and sibling-cited sources (status given per line; "re-fetched by B" = page or abstract read by B via Firecrawl):
- Nordman Algorithms (Kuntysh, A., 2026). Do Fair Value Gaps Work? 38,114 FVG Returns Tested. https://www.nordman-algorithms.com/blog/do-fair-value-gaps-work/ (re-fetched by B)
- Nordman Algorithms (Kuntysh, A., 2026). Do Order Blocks Work? 10,986 Touches Tested Against Random Levels. https://www.nordman-algorithms.com/blog/do-order-blocks-work/ (re-fetched by B)
- Nordman Algorithms. ICT Displacement and the MSS. https://www.nordman-algorithms.com/blog/ict-displacement-market-structure-shift/ (via ict_pd; not re-fetched)
- Barot, D. (2026). Fair Value Gaps Work — Until You Try to Trade Them. SSRN 7148099. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7148099 (abstract re-fetched by B); SSRN 7359378 (via ict_liq)
- Mahadzva, S. (2026). Smart Money or Costly Folklore? A Systematic Evaluation of ICT/SMC Trading Rules in G10 FX. SSRN 7430998. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7430998 (abstract re-fetched by B)
- Tangirala, K. H. (2026). Do Smart Money Concepts Predict Returns? Evidence from 44 Formalised Detectors on S&P 500 Daily Bars, 2010-2026. SSRN 7483658. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7483658 (abstract re-fetched by B)
- Trader Markus (2026). Fair value gap: a test on 26 years of S&P 500 data. https://tradermarkus.com/fair-value-gap/ (re-fetched by B)
- MarketTrace (BTC FVGs): https://markettrace.ai/blog/fair-value-gap (via ict_pd; not re-fetched)
- tradestar.app Silver Bullet test: https://tradestar.app/blog/i-tested-the-ict-silver-bullet-mechanically
- Le (2026), direction vs volatility coherence (via quant_regime B).

Sibling study reports used (local): `study/calib_ml.final.md`, `study/quant_pot.final.md`, `study/quant_regime.final.md`,
`study/session_stats.final.md`, `study/ict_pd.final.md`, `study/ict_liq.final.md`, `study/ict_time.final.md`,
`study/bias_dol.final.md`, `study/trade_mgmt.final.md`, `study/academic_sr.final.md`.

This study's code and outputs: `study/skeptic_tools/*.py` + `out_*.txt` (A); `study/skeptic_b_tools/*.py` + `out_*.txt` (B).
