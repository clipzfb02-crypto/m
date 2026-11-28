# Auction Market Theory, Market Profile and Volume Profile: combined final study (A + B) for DOL Engine v2

Scope: every AMT / Market Profile (TPO) / Volume Profile concept that bears on WHERE price goes next (which liquidity is taken), WHEN, and HOW LIKELY. Engine studied: `brief/baseline_v2.pine` (line numbers refer to it; identical to `/home/user/m/indicators/dol_engine.pine`, checked with `diff`).

This file merges researcher A's study (`study/amt_profile.md`) with researcher B's verification, replications and extensions. Markers:
- **[A✓]**: A's statement, re-checked by B (source re-opened or result replicated), unchanged.
- **[CORRECTED]**: A's statement changed by B. The reason is given in place.
- **[B-NEW]**: added by B.

Companion studies (referenced, not repeated):
- `ict_liq.final.md` ICT-1 and `calib_ml.md` CAL-3 / CAL-4: the candidate (shadow) ledger. AMT-2 here amends its lift estimator.
- `quant_regime.md` REG-1 and `quant_pot.md` QPOT-03: a volatility-state key for the PoT surface. B7 here adds independent evidence for it.
- `ict_time.final.md` TIME-2 / TIME-3: the clock dimension of the PoT surface. A's E-OWN-0 is independent evidence for it.
- `smc_impl.final.md` SMC-7: LVN troughs. `competitors.final.md`: the LVN distance limit.
- `classic_levels.md`: VWAP (not repeated here).

Reproducibility:
- A's scripts: `study/amt_tools/` (`amtlib.py`, `s1_npoc.py` … `s7_bounce.py`, outputs `out_*.txt`).
- B's scripts:
  - `study/amt_b_tools/`: `blib.py`, `b_path.py` (B1), `b_within.py` (B2), `b_events.py` (B3), `b_within2.py` (B4), `b_btc_levels.py` (B5), `b_lift.py` (B6), with outputs `out_b_*.txt`.
  - `study/amt_b2_tools/`: `b7_volratio.py` (B7) and `b8_bounce.py` (B8), with outputs.
  - All of B's code is an independent re-implementation. It does not import A's library.
- Data:
  - Public CME continuous OHLCV (github.com/axb0306/cme-futures-ohlc), in `study/amt_data/cme/`. 1-hour bars 2025-03-21 → 2026-04-15 for ES, NQ, RTY and YM; CL from 2025-06-01. 1-minute bars 2026-01-20 → 2026-04-15.
  - BTC 1-hour bars 2017-2025 (`study/classic_tools/btc_1h.csv`), added by B for an out-of-asset-class replication.
- B's inference uses **week-clustered** standard errors (about 260 clusters for CME, 418 for BTC). A used day clusters (about 1,200). H = 30 hourly windows overlap across adjacent days, so day clusters understate the standard errors. B's z-scores are therefore smaller and more honest.

---

## 0. Executive summary (read this first)

1. **Volume-profile levels are reached at the random-level rate. [A✓, now independently replicated]**
   - Prior-session POC, VAH, VAL, older naked POCs, IB extremes and overnight extremes all hit at the rate of a random price at the same ATR distance once the baseline is matched on clock time.
   - A, CME: prior POC within 5 sessions 83.6% vs 84.7% random; naked POCs aged ≥ 2 sessions 38.7% vs 43.4%.
   - **[B-NEW] BTC (B5):** naked POCs aged ≥ 2 days hit −2.7 pp (z −5.8) at 24 h and −6.1 pp (z −5.3) at 120 h. The prior day's POC is +2.2 pp at 24 h (z 2.5) but −0.3 pp at 120 h.
   - **[B-NEW] Independent replication with a distance-matched baseline (ULTIMA "Volume & Time" lessons, 721 sessions, QQQ and SPY):**
     - naked POCs revisited 85% vs 84% for random prices at the same distance (+1.9 pp, CI [−0.5, +4.3]);
     - the prior POC holds after a touch 19% of the time, the same as random (−0.3 pp);
     - a public NQ practitioner study finds +3.8 pp [−1.0, +8.6] (n = 863), not significant.
   - The folklore "84-87% of naked POCs get revisited" is true and **is a distance artifact**.
   - **Do not add naked POCs or VA edges as DOL level sources.**
2. **The engine's volume-profile path cost is wrong. [A, CORRECTED in magnitude and mechanism]**
   - The ×1.10 "thin path" bonus (line 1947) is wrong-signed or null on every dataset.
   - **63-86% of the engine's "thin" class are targets *beyond* the composite's price range.** They land there only because `f_row` (570-571) clamps them onto the thin tail rows.
   - Targets truly inside the range behind a thin path:
     - pooled: −3.5 pp (CME 120 h, z −1.8 week-clustered) and −0.7 pp (BTC, z −0.6);
     - ranked *against the other candidates at the same bar* (B2, the comparison that matters for selection): −5.5 pp (CME 120 h, z −2.6), −5.7 (240 h, z −2.5), −2.9 (48 h, n.s.), +0.6 (BTC, n.s.).
   - The ×0.85 "thick wall" penalty is unsupported. Pooled, thick paths do *better* than random: +2.3 (CME 120 h), +5.4 (48 h, z 3.7), +2.5 (BTC, z 3.2). Within-bar the sign flips with depth: +5.0 / −1.2 / −3.8 pp.
   - **[CORRECTED] Beyond-range targets.** A proposed a penalty (×0.95) because pooled hit rates are 2.5-3.3 pp below random. Two B tests show this is a *bar-level regime*, not a property that ranks candidates:
     - Within the same bar, beyond-range targets are not worse: the within-snapshot lift is 0.99-1.06 (B6).
     - Pooled, the deficit is absorbed by the volatility ratio ATR14/ATR120 (B7). On BTC the beyond coefficient goes from −0.12 to +0.06 (n.s.). On CME it shrinks but survives (−0.22, z −2.4).
   - The fix is therefore: no path multiplier for beyond-range targets (×1.00), a mild thin penalty (×0.97), and neutral thick (×1.00). Then let the ledger learn (AMT-1, AMT-2).
3. **[B-NEW] The dominant bar-level effect is volatility state, not profile structure (B7).**
   - Ranked by ATR14 / mean TR over 120 bars, targets at a given ATR distance are hit vs a clock-matched random level:
     - **+2.9 / −1.7 / −5.3 pp** on CME (low / mid / high tercile; z 3.5 / −2.7 / −6.7);
     - **+6.1 / −1.9 / −7.7 pp** on BTC (z 10.7 / −4.1 / −12.0).
   - The composite range width in ATR (`logRng`) looked predictive. It is fully absorbed by the volatility ratio (BTC +0.07, n.s.; CME −0.21, n.s.).
   - This independently supports REG-1 / QPOT-03: vol state as the PoT surface key, also used in `f_potBase`.
   - It also shows why pooled per-feature lifts (as ICT-1 specifies them) mix regime with ranking power. AMT-2 fixes that with cohort-demeaned lifts.
4. **AMT bias rules carry no information beyond distance. [A✓]**
   - Value migration: χ² = 1.05, df 2.
   - Close vs POC: χ² = 0.17.
   - Close vs VA: χ² = 5.6, with mean-reverting signs.
   - The 80% rule:
     - A's own test: 61.9% vs a 54.0% matched baseline (n = 42, n.s.);
     - tradeify: 25.0% / 28.1% vs a 28.7% / 27.2% base rate (hourly 2-period version; the 30-minute version has n = 5 and n = 8).
   - **[B-NEW] Composite "look above/below and fail" (B3)** does not send price to the far VA edge either: CME −2.9 / +3.4 pp (n.s.); BTC −4.0 / −11.1 pp (z −2.1 / −5.6).
5. **"Acceptance outside value" does not mean continuation. [A, CORRECTED: not robust across asset classes]**
   - A found an exhaustion lean on CME: targets further from value hit 3.8-6.0 pp less after ≥ 3 hourly closes beyond the VA.
   - B's within-bar test confirms the CME sign: −4.3 pp (z −2.0) at 120 h, −3.2 at 240 h, −2.7 at 48 h.
   - It **reverses on BTC: +2.3 pp (z +1.6)**.
   - So it is not a default multiplier, only a ledger bit.
6. **Poor (flat) extremes are not reliably repaired more often. [A, CORRECTED: weak → none]**
   - CME hourly proxy +1.6 pp (z 1.1, A).
   - BTC: flat PDH/PDL −2.2 pp vs plain −1.8 pp; the touch count is not monotonic (B5).
   - External: NQ practitioner study +1.0 pp [−2.8, +4.8] vs tailed extremes; ULTIMA QQQ/SPY "no better than random prices at the same distance".
   - A wrote that no statistic exists (X9). That is outdated.
   - Drop A's eqCount injection (AMT-6). ICT-10 neutralises EQ density anyway.
7. **LVN rejection is weak, not moderate. [A, CORRECTED]**
   - Re-run with week clusters and a *distance-matched* random baseline (B8):
     - A's LVN definition: +2.5 pp (CME, z 2.0) and +1.6 pp (BTC, z 1.7);
     - the SMC-7 trough definition, which A's AMT-5 relies on: +1.7 pp (CME, z 1.2) and +0.0 pp (BTC).
   - External: "reject-or-run at LVN edges" −0.3 pp [−5.0, +4.4] (NQ, n = 863).
   - The "LVN as invalidation anchor" proposal is dropped. The faster-through-LVN effect is confirmed: A +7-9% at 15 minutes; NQ practitioner +7.9 pp [+0.5, +15.8] (n = 794). HVN "pull" is null (n = 10,908).
8. **Measurement traps.**
   - (a) An unmatched clock baseline manufactures −6 to −11 pp "edges" (A, E-OWN-0).
   - (b) **[B-NEW]** An unmatched volatility state manufactures ±6-8 pp (B7).
   - (c) **[B-NEW]** Pooled lifts confound bar-level regime with candidate ranking (B6). Example: the LVN_BAR pooled lift is 0.60 on BTC, but 0.83 within the same snapshot.
   - The engine's `pBase` (1314-1322, 1430) and any future candidate-ledger lift inherit all three.

Net: AMT's value to this engine is mostly **negative knowledge** (what *not* to add) plus:
- one concrete bug fix: the path-cost sign, magnitude and out-of-range clamp (AMT-1);
- one methodological fix that matters for every feature in the shadow ledger: cohort-demeaned lifts (AMT-2);
- small UX items for AMT traders that carry no score weight (AMT-3, AMT-4, AMT-5).

---

## 1. Concepts (definitions and parameters)

### 1.1 Auction Market Theory (AMT): balance, imbalance, acceptance, rejection [A✓]
- **Premise (Steidlmayer, CBOT 1985; Dalton, *Mind Over Markets* 1990).**
  - The market is a two-way auction that facilitates trade.
  - **Balance**: two-sided rotation around a fair price; a bell-shaped ("D") profile.
  - **Imbalance**: a one-sided, directional search for new value; an elongated profile with thin areas.
- **Acceptance** = time and volume build at new prices. Operational definitions:
  - ≥ 2 consecutive 30-minute TPO periods beyond a reference;
  - or ≥ 1 hour of trade there;
  - or the developing POC migrates there.
- **Rejection** = prices visited only briefly: tails, single prints, LVNs.
- **Initiative vs responsive.** Buying above value is initiative; buying below value is responsive (and the mirror for selling). Responsive activity at the value edges keeps balance; initiative activity beyond value starts an imbalance.
- **OTF** (other-timeframe participants) drive imbalance; the day timeframe rotates within balance.
- **DOL role (theory).**
  - Balance: targets inside value (rotation) are favoured.
  - Imbalance with acceptance: targets beyond value (continuation) are favoured.
  - After rejection: price returns to value.
- **Measured.** Only weak, asset-dependent support:
  - Rotation to the POC from inside the VA is slightly favoured: +1.9 pp (CME, z 1.5) and +2.0 pp (BTC, z 2.4) (A and B3).
  - Continuation after acceptance is not favoured (§2.5, B4).
  - **[B-NEW]** The tradeify write-up (verified) frames the same point well: "market profile is a strong way to organise a session and a weak way to predict one."

### 1.2 TPO profile (Market Profile) [A✓]
- **Session.** For index futures, RTH 09:30-16:00 ET: 13 periods of 30 minutes, lettered A-M.
- **Row (bracket).**
  - Each period prints its letter on every row its high-low range touched.
  - Typical sizes: ES 2.5 points, NQ 10 points (tradeify).
  - TradingView "Auto" targets about 80 rows over the last 300 bars.
- **TPO count per row** = the number of periods that traded there.
- **Parameters that move every derived level:** session window, period length, row size, VA %.
  - Switching the VA from 70% to 80% moved the ES VAH on 31 of 49 sessions.
  - Switching the tie rule moved it on 10 of 49 (tradeify, verified).
- **[B-NEW] Time-at-price as a volume substitute.** Where no volume exists (cash indices, many CFDs), a TPO-style profile weights every bar equally. This is the Market Profile original, and the engine's fallback in AMT-5.

### 1.3 Volume profile [A✓]
- Traded volume per price row.
- OHLCV approximations:
  - uniform spread over each bar's range;
  - TradingView builds it from lower-timeframe bars;
  - this engine (1384-1414): 60% of each hourly bar's volume flat over its range, 40% over its body, then 1-2-1 smoothing.
- **Composite profiles.**
  - Fixed session composites (daily, weekly).
  - Rolling N-bar composites, as in the engine: the last `lvnHours` = 120 hourly bars, 48 rows (204-205, 1900-1909).
- **[B-NEW] Pine limits.**
  - `request.security_lower_tf` can return up to 100K intrabars on non-professional plans (`writing_scripts/limitations.md` §Intrabars). The engine's hourly request on charts above 1H is far below this.
  - `request.footprint()` returns per-bar footprint POC / VA rows, but "only users who have a Premium or Ultimate plan can use scripts that call it" and "a script can execute only *one* unique call". It must not go into the main engine; this agrees with `orderflow_micro.md`.

### 1.4 Point of Control (POC) [CORRECTED: tie rules were conflated]
- **Definition.** The row with the most TPOs (TPO-POC) or the most volume (VPOC).
- **POC ties.** A common rule (CQG) picks the tied row closest to the range midpoint.
  - A's text attributed a "closest to POC" tie rule to TradingView's POC. That rule is TradingView's **value-area expansion** tie rule (§1.5), not a POC rule.
- **Developing POC (dPOC).** The POC of the session so far.
  - **[B-NEW]** In a public NQ practitioner study, the dPOC's direction over the first two hours does not point to the close: −0.5 pp [−3.0, +2.1], n = 1,482.

### 1.5 Value area (VAH / VAL) [A✓, algorithm verified against tradeify's worked example]
- The band around the POC holding about 70% of TPOs or volume. Quantower describes it as "about 68% to 70%". The CBOT material frames it as roughly ±1 σ.
- **One-row expansion** (most platforms):
  1. Total T; target 0.70·T.
  2. Start with the POC row.
  3. Compare the next row above with the next row below, and add the larger.
  4. Repeat until the accumulated total ≥ target.
  5. VAH = top of the highest included row; VAL = bottom of the lowest included row.
- **Tie rule.**
  - TradingView's documented rule: the row closer to the POC, then the higher row.
  - Many tutorials: the upper row wins.
- **Sierra Chart "count 2 levels at a time".** Compares *pairs* of rows (the CBOT variant). A's `amtlib.value_area()` uses this variant; B's `blib.va_one_row()` uses the one-row rule proposed for Pine.
- **Edge cases:**
  - a POC at the profile edge expands on one side only;
  - a flat profile defaults to the upper side;
  - VA % below 50% or above 90% is unusual.

### 1.6 Two-day value relationships (value migration) [A✓]
| Relationship | Rule | Dalton's reading |
|---|---|---|
| Higher | VAL₁ > VAH₀ | bullish |
| Overlapping-higher | VAH₁ > VAH₀, VAL₁ ≥ VAL₀, overlap | moderately bullish |
| Inside | VAH₁ ≤ VAH₀, VAL₁ ≥ VAL₀ | balance / breakout pending |
| Outside | VAH₁ > VAH₀, VAL₁ < VAL₀ | balance |
| Overlapping-lower | VAL₁ < VAL₀, VAH₁ ≤ VAH₀, overlap | moderately bearish |
| Lower | VAH₁ < VAL₀ | bearish |

- **[B-NEW] Value moves routinely.** On ES and NQ the VA did not overlap the prior VA on 41.7% / 42.0% of 588 sessions (tradeify, verified). So "yesterday's value as a fence" fails about two days in five.

### 1.7 Naked (virgin) POC [A✓]
- The POC of a *completed* session that no later bar's range has touched. It retires on the first touch (bar high ≥ POC ≥ bar low); some traders require a trade-through.
- **Proper estimator:** a survival model of the fill hazard by age, with censoring, **plus a distance-matched baseline**. None of the published magnet claims has the baseline. The two studies that have one (A's own and ULTIMA's) both find no edge.

### 1.8 HVN / LVN [A✓; evidence CORRECTED in §2]
- **HVN** = a local maximum (peak) of the profile. **LVN** = a local minimum (trough), typically between two HVNs.
- **Detection:**
  1. **Trough / peak test.** Compare each row with N neighbours on each side and require a prominence (depth) threshold (SMC-7: strict minimum over ±8% of the rows, depth ≥ 0.15·peak).
  2. **Absolute threshold vs the peak.** The engine (2250-2269) marks runs of rows < 0.30·peak, tails excluded. These are broad shoulders, not troughs.
  3. **A's local-minimum definition (B8):** row ≤ min(±2 rows) and < 0.3·peak.
  4. **ViperQ (2026):** "V < 0.5·mean".
- **Claims:**
  - "price moves fast through LVNs" (true, weak: +7-9%);
  - "LVNs reject" (weak to null);
  - "HVNs stall / pull" (null);
  - "HVNs are magnets" (not robust).

### 1.9 Single prints, tails (excess) [A✓, definitions verified]
- **Single print zone (tradingstats).**
  - Rows with exactly one TPO, at **tick resolution**, forming a zone ≥ 2 ticks.
  - Excludes the day's extremes (those are tails).
  - Sandwiched by multi-TPO areas on both sides.
  - 30-minute periods, 09:30-16:00 ET.
  - "Filled" = a later day's range covers the whole zone.
- **Tail / excess:** ≥ 2 single-print rows at the session high or low.
  - Dalton: the auction ended properly through aggressive opposite activity.
- **Edge cases:**
  - Row size dominates the counts: at 80 rows per range almost every extreme has a 2-row tail.
  - Single prints in the final period.
  - Gaps between RTH and ETH.

### 1.10 Poor highs / poor lows (unfinished auction) [A✓ definition; evidence CORRECTED]
- **TPO definition.** ≥ 2 TPOs at the extreme row: a flat top or bottom with no tail.
- **Variants:**
  - "weak": ≥ 2 TPOs within 1-2 ticks;
  - "AB poor high": an extreme made by the A and B periods (marketcalls keeps these for up to two months).
- **Bar proxy.** ≥ 2 separated bars within tol·ATR of the session extreme, i.e. an equal high or low at the extreme.
- **[B-NEW] Same geometry, two doctrines.** LuxAlgo notes that "the same flat-extreme geometry appears … as the equal highs that liquidity-based traders read as engineered stop pools". The engine's EQ logic is the natural home. ICT-10 has already measured EQ as about 0 pp.

### 1.11 Initial Balance (IB) and range extension; day types [A✓, with a CORRECTION on tradeify's IB]
- **IB** = the first RTH hour, 09:30-10:30 ET (periods A + B). Range extension = trade beyond the IB. Extension levels at IB ± k·IB.
- **[CORRECTED]** tradeify's 589-session test used hourly bars over 09:00-15:59 ET. Its "IB" is the **first two hourly periods (09:00-11:00)**, a 2-hour IB. That explains its lower break rate (93.6% / 89.8%) against tradingstats' 1-hour IB (97.8% / 96.2%).
- **Day types** (TradingView docs via tradeify):

  | Type | Rule |
  |---|---|
  | Normal | about 85% of the range inside the IB |
  | Normal variation | range extension up to 2× IB |
  | Trend | extension > 2× IB, close near the extreme |
  | Neutral | extension on both sides |
  | Double distribution | two separate value areas |
  | Non-trend | no extension |

### 1.12 Open location and open types (Dalton) [A✓]
- **Open location:** inside value / outside value but inside the range / outside the range.
- **Open types:** OD, OTD, ORR, OA (definitions as in A).
- **[B-NEW]** A second search again found **no published hold-rate statistic** for any open type. One TradingView script ("Open Type with Measured Outcomes") embeds its own numbers, which are not public. RTH-specific; rejected.

### 1.13 The 80% rule [A✓; origin attribution unverified]
- **Rule.** Open outside the prior VA, then two consecutive 30-minute periods back inside → "80%" chance of reaching the opposite edge.
- **[B-NEW] Composite generalisation (B3):** "look above / below and fail" = 1-3 hourly closes beyond the composite VA, then a close back inside.
- The attribution to Dalton Capital "Profile Reports" (1987-91) could not be verified; the claim is folklore either way.

### 1.14 Overnight inventory / overnight high-low [A✓]
- The engine's Asia / London session highs and lows (948-950) already cover the overnight extremes. `ict_time.final.md` TIME-7 proposes overnight (Globex) H/L pools separately.

### 1.15 Profile shapes [A✓]
- P, b, D shapes and double distribution. These describe the past; no predictive evidence.
- **[B-NEW] "Balanced target"** (from the open-source `py-market-profile`): the POC mirrored by the longer side of the profile. Tested in B3: −2.4 pp (CME, z −2.0) and −1.9 pp (BTC, z −2.6). Rejected.

### 1.16 [B-NEW] Volatility state as the confound of every "level" test
- ATR-normalised reach depends strongly on whether ATR14 is high or low relative to longer-run volatility (vol clustering plus mean reversion). The same ATR distance is "far" right after a volatility spike and "near" in a compressed market.
- Any profile feature correlated with the volatility state looks predictive in pooled tests unless the baseline is conditioned on it. Examples: beyond-range, wide vs narrow composite, acceptance outside value.
- Operational variable: x = ln(ATR_fast / ATR_slow), as in REG-1 (ATR5/ATR100). B7 used ATR14 / mean TR over 120 bars.

### 1.17 [B-NEW] Pooled vs within-snapshot (ranking) effects
- **Pooled lift:** hits / expected over all probes carrying a feature. It mixes "this feature ranks candidates" with "this feature appears more often in bars where every candidate under- or over-performs its baseline".
- **Within-snapshot lift:** residuals (hit − pBase) are centred by the mean residual of all candidates snapped at the same bar before they are summed per feature.
- The engine's multiplier `lv.mult` only changes the **ranking** at a bar (it never touches PoT; see 657, 693-695 and 1303-1311). Ranking effects are therefore what a multiplier should be fitted to.
- Pooled effects matter only for the displayed PoT. They belong in the PoT surface key (REG-1, TIME-2) or in CAL-6's calibration.

---

## 2. Evidence (numbers and sources)

Grades:
- **strong**: peer-reviewed or large replicated quantitative study;
- **moderate**: published or reproducible statistics with a proper baseline;
- **weak**: statistics without a baseline, or small, mixed or non-replicating samples;
- **none**: folklore.

### 2.1 External evidence (each re-opened by B unless marked)

| ID | Claim | Source | Numbers (verified) | Grade |
|---|---|---|---|---|
| X1 | Prior POC "magnet" [A✓] | tradeify, 589 sessions each of ES and NQ; Yahoo hourly bars, 2024-04-24 → 2026-09-15 | Prior POC traded again within 5 sessions: ES 450/584 (77.05%), NQ 459/584 (78.60%); **median 1 session**. No VA overlap with the prior session on 41.67% / 42.01%. "The 'magnet' story is not proven by this number." | moderate (against folklore) |
| X2 | Naked POCs get revisited | TradingView author post (via `smc_impl.md` E8; tradingview.com is blocked here, not re-opened) | Gold 84%, ES 87%, BTC 87% within 5 days; by distance < 0.5 ADR 82%, 0.5-1 ADR 59%, 1-2 ADR 32%. No baseline. | weak |
| X3 | 80% rule [A✓] | tradeify | Hourly version (two **1-hour** periods inside): reached the far edge 9/36 (25.00%) ES and 9/32 (28.13%) NQ, vs base rates of 28.65% / 27.17%. Rerun: 27.27% vs 29.22% (ES), 25.93% vs 27.27% (NQ). 30-minute version: ES 2/5 (base 20.0%), NQ 0/8 (base 21.2%). | moderate (against folklore) |
| X4 | 80% rule | Elite Trader thread; a TradeStation user quoted at 62% (via search summary) | "not anywhere close to 80%"; 62% | weak |
| X5 | IB breaks almost every day [A✓] | tradingstats.net, 1-minute data, Jan 2015 - Dec 2025, 2,686 ES / 2,833 NQ days | ≥ 1 break: 97.8% / 96.2%. Median extension 63.6% / 55.6% of IB. ES up by close: 52.0% reach +25%, 18.8% reach +100%, 4.4% reach +200%. Narrow IB (< 0.5 × **daily** ATR14; 66% of ES days): 98.7% break, median extension 74.8%. Extreme IB: 66.7% / 76.9% break (n = 6 / 13). C-period close beyond the IB: 45.5% reach 100% (ES up), 50.0% (ES down). First break failed: 34.0%. 65% of first breaks in C, > 80% by 11:30. **[B-NEW]** IB high formed first → single *down* break 44.8% vs single up 24.0% (ES); no baseline, and partly geometry (price sits nearer the IB low at 10:30). | moderate (descriptive) |
| X6 | IB breaks, range vs IB **[CORRECTED: 2-hour IB]** | tradeify | **IB = the first two hourly periods (09:00-11:00 ET).** Broken 93.55% / 89.81%; both ways 16.64% / 11.54%; closed back inside the IB 43.46% / 49.07%. Median session range 1.52× / 1.39× IB; ≥ 3× IB 4.92% / 3.06%. | moderate (descriptive) |
| X7 | Single prints get filled [A✓] | tradingstats.net, NQ / ES / YM / RTY, Feb 2014 - Mar 2026, 3,847 zones | Form on 37-53% of days. Full reversal of the single-print day 6-10%. Full fill D+1 32-39%, D+5 63-67%, D+10 74-76%; never within 30 days 14-17%. Small zones (2-10% of the day's range) 64-70% by D+5; large zones (18-25%) 47-50%. After 7 days unfilled, P(ever) < 50%. **No baseline.** | weak for "magnet"; moderate for "full reversal is rare" |
| X8 | Shallow extremes fade, deep ones hold **[CORRECTED: moderate → weak]** | tradingstats.net, 1-minute data 2019-2026, about 14,300 extremes per market | 58-59% of running extremes "fade" (retrace 50% of the move from the session open before the session ends); ~0.25 ATR extremes ~85%, > 1 ATR ~20%; lows fade more (NQ 61% vs 55%); walk-forward AUC ≈ 0.82. **The retrace target is half the extreme's own distance from the open, so it shrinks with depth: most of the gradient is mechanical. No baseline.** | weak |
| X9 | Poor highs/lows get repaired **[CORRECTED: "no statistic exists" → two null tests]** | ULTIMA "Volume & Time" M2.09 (fetched by B) | Public NQ practitioner study: poor extremes revisited **+1.0 pp [−2.8, +4.8]** vs tailed extremes (next session). ULTIMA's own QQQ / SPY test: "no better than random prices at the same distance". | weak (null) |
| X10 | Published S/R levels interrupt intraday trends [A✓] | Osler 2000, FRBNY *Economic Policy Review* 6(2), pp. 53-68 | Six firms' daily levels, DM / JPY / GBP, Jan 1996 - Mar 1998. Bounce frequency at published levels 60.8% vs 56.2% for 10,000 arbitrary level sets (+4.0 to +5.6 pp by currency). Significant at 5% for 13 of 16 firm-currency pairs. Lasts ≥ 5 business days. Firms' own strength ratings carry **no** information (the differences are mostly negative). Footnote: arbitrary levels bounce > 50% because of negative first-order autocorrelation and the bounce definition. | strong (for "levels stop trends"; says nothing about attraction) |
| X11 | S/R lines up with order-book depth [A✓] | Kavajecz & Odders-White 2004, *RFS* 17(4) 1043-1071; a Taiwan SE replication on reconstructed books (via search) | S/R levels coincide with peaks in limit-order-book depth; moving averages carry information about where the depth sits | strong (mechanism) |
| X12 | Bounce probability rises with prior bounces, decays with time [A✓] | Chung & Bellotti 2021, arXiv:2101.07410; predecessor **[B-NEW]** Garzarelli, Cristelli, Pompa, Zaccaria & Pietronero 2014, *Scientific Reports* 4:4487 | C&B: 1-minute EURUSD / LLOY / BRENT, 2018. p(b \| b_prev) rises with b_prev (permutation tests; shuffled-returns benchmark ≈ 0.5). EURUSD 1-bounce levels decay to 0.5 at a ~350-minute window, 4-bounce levels at ~900 minutes. Garzarelli: LSE stocks, 45-90 s scales; bounce probability above the shuffled series and rising with b_prev; a fractional random walk with H = 0.44 cannot explain it. Note: the result depends on the zone-width γ ("a higher γ would inflate p(b)"). | moderate |
| X13 | Round numbers / deep queues [A✓] | Jung & Lee 2026, arXiv:2610.34787 | Five Nasdaq stocks, 2025: round levels attract more liquidity but show no longer depth-adjusted durations | moderate |
| X14 | Technical rules in futures after a data-snooping control | Park & Irwin (farmdoc) | Generally not profitable in US futures 1985-2004 (not re-opened by B) | strong (context) |
| X15 **[B-NEW]** | Profile claims vs distance-matched random prices | ULTIMA "Volume & Time" lessons M2.01 / M2.03 / M2.09 (fetched by B; methods summarised on the pages) | Naked POCs revisited **85% vs 84%** random at the same distance (+1.9 pp [−0.5, +4.3]; 721 sessions, QQQ / SPY). Prior POC holds after a touch 19% = random (−0.3 pp [−3.0, +2.6], 794 touches). NQ practitioner: prior POC +3.8 pp [−1.0, +8.6] (n 863); dPOC direction −0.5 pp [−3.0, +2.1] (n 1,482); LVN reject-or-run −0.3 pp [−5.0, +4.4] (n 863); **price crosses LVNs faster than HVNs +7.9 [+0.5, +15.8] (n 794)**; HVNs pull price back +0.8 [−0.1, +1.7] (n 10,908). | moderate (independent replication of A's nulls; secondary write-up) |
| X16 **[B-NEW]** | Large price changes happen at gaps in the book | Farmer, Gillemot, Lillo, Mike & Sen 2004, *Quantitative Finance* 4(4) (via `orderflow_micro.md`) | Large returns are driven by gaps next to the best price, not by large orders | strong (mechanism at book scale; the bar-level LVN is only a proxy) |
| X17 **[B-NEW]** | AMT features in an RL trader | ViperQ, arXiv:2609.13825 (2026) | +163.6% ROI on TSLA and +116.5% on NVDA, long-only, held-out year. VPOC is "approximated by a one-hour rolling VWAP"; LVN flag = V < 0.5·mean; **no ablation of the AMT features** in the passages read | none (for AMT features) |

### 2.2 A's own tests (summarised; see `amt_profile.md` for the full tables) [A✓ unless marked]

- **E-OWN-0. Clock matching.** Against an all-hours baseline, session-anchored levels show spurious edges: PDH −11.6 pp (z −9.3), POC −7.5, nPOC_old −11.0. Clock-matched: −3.2 / −1.5 / −2.3 pp.
- **E-OWN-1. Prior-session levels at H = 30** (CME 1H, 40-row session profiles).
  - POC −1.5 pp (n 879); VAH 0.0; VAL −2.8; PDH −3.2; PDL −1.2.
  - Naked POCs aged ≥ 2 sessions: −2.3 pp (H = 30) and −4.7 pp (H = 115).
  - At H = 115, POC 83.6% vs 84.7% random.
- **E-OWN-2. Fine 1-minute RTH profiles.** POC −1.3, VAH −3.0, VAL −1.8, MID −4.0 pp (n 285 each, n.s.).
- **E-OWN-3. IB and overnight extremes as same-session targets.** IBH −0.4, IBL +2.2, ONH +0.9, ONL +1.9 pp (n.s.).
  - Descriptive: any IB break 97.5%; both sides 22.8%; P(≥ 1.5× IB) 11%.
- **E-OWN-4. 80% rule.** 61.9% vs 54.0% (n 42, z 1.2).
- **E-OWN-5. Poor vs tailed extremes.**
  - TPO version: +1.4 to +5.8 pp (n 39-109, n.s.).
  - Hourly proxy: +1.6 pp (n 851, z 1.1); by touch count 1→−2.1, 2→+1.1, 3→+2.4, 4+→+4.4.
  - **[CORRECTED]** The BTC replication (B5) and both external tests (X9) are null, so the monotonic touch-count pattern does not replicate.
- **E-OWN-6. Mid-profile single prints** (n 98). Full fill 53.1% vs 63.9% (−10.8 pp); near-edge touch −7.8 pp.
- **E-OWN-7. Path volume.** Replaced by B1 / B2 / B6 / B7 (§2.3). **[CORRECTED]**
  - A's "< 0.6 (×1.10) −3.7 pp" row mixes in-range thin paths with beyond-range targets that the clamp put there: 75% of that class at 120 h.
  - A's day-clustered z-scores are too large.
- **E-OWN-8. Speed.** Next-bar |Δclose| / ATR is equal at 1H (0.566 vs 0.568). At 15 minutes, LVN rows are 7-9% more volatile. Independently confirmed: +7.9 pp, X15.
- **E-OWN-9. Bounce.** LVN +3.2 pp (z 2.9) vs a uniform-random level, day clusters. **[CORRECTED]** by B8, §2.4.
- **E-OWN-10. Which prior-day extreme is taken first** (1,273 sessions). Logit on log distance ratio, z 16.5.
  - Value migration χ² 1.05; close vs POC 0.17; close vs VA 5.58 with mean-reverting signs.
- **E-OWN-11. Composite value state** (120 h).
  - POC from inside the VA: +2.1 pp (z 2.0).
  - Full rotation after ≥ 2 closes outside: −3.2 to −4.9 pp.
  - Targets further from value after ≥ 3 closes: −3.8 / −5.3 pp (120 h). **[CORRECTED]** BTC reverses the sign (B4).
- **E-OWN-12. Target inside the composite VA or at an HVN row.** +2.5 / +4.5 pp at 120 h, not robust across 48 / 240 h.

### 2.3 B's replications and extensions: the path cost (B1, B2, B6, B7) [B-NEW]

Design (B1):
- Engine-identical rolling composite: 48 rows, 60/40 range/body, 1-2-1 smoothing, engine `f_row` clamp.
- Targets: unswept 5/5 pivots, strict trade-through, 0.5-10 ATR away, H = 30.
- Baseline: clock-hour-matched empirical surface.
- Week-clustered standard errors.
- The engine's classes are split so that beyond-range targets are separate.

**B1. Pooled, by engine class** (edge pp vs random; z_clu by week)

| Class | CME 48 h | CME 120 h | CME 240 h | BTC 120 h |
|---|---|---|---|---|
| Beyond the composite range | −2.5 (z −3.5), n 41,265 | −3.3 (z −3.8), n 28,141 | −2.9 (z −2.8), n 18,679 | −2.5 (z −4.5), n 56,632 |
| Thin, in range (vf < 0.6) | −3.8 (z −1.8), n 1,793 | −3.5 (z −1.8), n 3,089 | −3.5 (z −2.1), n 4,817 | −0.7 (z −0.6), n 4,043 |
| Mid | −0.2 | −0.6 | −0.7 | −1.5 (z −3.4) |
| Thick, in range (vf > 1.4) | +5.4 (z 3.7) | +2.3 (z 1.7) | −0.9 | +2.5 (z 3.2) |
| Share of the engine's thin class that is beyond range (clamped) | **86%** | **75%** | **63%** | **82%** |
| Share of all candidates beyond range | 63% | 43% | 28% | 41% |

**B2. Within-bar (fixed effects).** Candidates competing at the same bar; linear probability on hit − pBase; week clusters. This is the test that matches what the multiplier does.

| Feature (vs mid, in range) | CME 48 h | CME 120 h | CME 240 h | BTC 120 h |
|---|---|---|---|---|
| Thin path | −2.4 (z −0.95) | **−5.8 (z −2.6)** | **−6.8 (z −3.0)** | +1.1 (z 0.8) |
| Thick path | **+5.2 (z 3.1)** | +0.9 | **−2.8 (z −1.8)** | −0.5 |
| Beyond range | −0.6 | −0.8 | −0.2 | **+2.5 (z 3.3)** |
| Full model: ≥ 2 LVN troughs in the path | −0.1 | **−5.7 (z −2.5)** | +0.2 | **−3.5 (z −2.8)** |
| Full model: target 0.25-1 ATR inside the composite edge | −1.3 | **−4.9 (z −2.6)** | **−6.0 (z −3.3)** | +0.1 |

**B6. Pooled lift (the estimator in ICT-1) vs within-snapshot lift, on the same probes.**

| Bit | CME 48 h | CME 120 h | CME 240 h | BTC 120 h |
|---|---|---|---|---|
| VP_OUT (beyond range) | 0.917 / 0.990 | 0.854 / 0.990 | 0.875 / 1.036 | 0.893 / 1.063 |
| PATH_THIN (in range) | 0.989 / 0.952 | 0.984 / 0.921 | 0.979 / 0.923 | 1.032 / 1.005 |
| PATH_THICK (in range) | 1.158 / 1.061 | 1.111 / 1.021 | 1.033 / 0.973 | 1.111 / 0.979 |
| LVN_BAR (≥ 2 troughs) | 1.029 / 1.026 | 0.782 / 0.900 | 0.745 / 1.043 | **0.598 / 0.826** |
| NEAR_EDGE (≤ 1 ATR inside the edge) | 1.043 / 0.996 | 0.941 / 0.939 | 0.877 / 0.921 | 0.972 / 0.976 |
| IN_VALUE | 1.065 / 1.013 | 1.117 / 1.034 | 1.044 / 1.016 | 1.055 / 0.968 |
| EXT_FROM_VALUE (≥ 3 closes, away) | 0.917 / 0.971 | 0.917 / 0.950 | 0.963 / 0.960 | 0.964 / 1.030 |

Pooled lifts overstate every effect, or invert it. The ICT-1 estimator would learn ×0.85-0.92 for VP_OUT, which has no ranking power (0.99-1.06).

**B7. The volatility-ratio confound (pooled logit with offset logit(pBase), week clusters; vr = ATR14 / mean TR over 120 bars).**

| Model term | CME 120 h | BTC 120 h |
|---|---|---|
| log vr alone | −0.85 (z −9.9) | −1.32 (z −20.1) |
| log composite range in ATR, alone | +0.47 (z 6.4) | +0.88 (z 15.6) |
| both: log range | −0.21 (n.s.) | +0.07 (n.s.) |
| both: log vr | −1.05 (z −6.6) | −1.26 (z −12.3) |
| beyond, with vr | −0.22 (z −2.4) | +0.06 (n.s.) |
| thin in range, with vr and all controls | −0.20 (z −2.0) | +0.06 (n.s.) |
| hit vs base by vr tercile (low / mid / high) | +2.9 / −1.7 / −5.3 pp | +6.1 / −1.9 / −7.7 pp |

Conclusions:
- The "composite range" story is the volatility ratio.
- The pooled beyond-range deficit is mostly volatility state (BTC entirely, CME partly).
- Thin-in-range survives only on CME.

**Robustness of A's thin-path claim by instrument** (120 h, pooled, A's mixed class): CL −0.5, ES −3.5, NQ −4.6, RTY −4.5, YM −4.5 pp. Those figures include clamped beyond-range targets. B did not re-split them by instrument.

### 2.4 B's replications: rejection at profile levels (B8) [B-NEW; corrects E-OWN-9]

Osler-style test:
- At the first touch within 30 bars, "bounce" = price moves X·ATR back before X·ATR through, resolved within 24 bars.
- Baseline: random levels inside the composite, **in the same distance band from the close** (0.3-0.75 / 0.75-1.5 / 1.5-2.5 / 2.5-4 ATR).
- Week clusters.

| Level | CME, X = 1.0 | CME, X = 0.5 | BTC, X = 1.0 |
|---|---|---|---|
| Random (base bounce %) | 61.2 | 51.4 | 63.0 |
| LVN, A's definition (local min ±2 rows, < 0.3·peak) | +2.5 pp (z 2.0), n 7,212 | +2.9 (z 2.4) | +1.6 (z 1.7), n 8,307 |
| LVN, SMC-7 trough (strict ±8% rows, depth ≥ 0.15·peak) | +1.7 (z 1.2), n 4,718 | +2.5 (z 1.9) | **+0.05 (z 0.0)**, n 5,197 |
| HVN (> 0.7·peak, local max) | +0.2 | +0.9 | +0.6 |
| POC | −0.9 | −0.6 | +1.1 |
| VAH | −0.8 | −1.4 | −0.9 |
| VAL | +1.9 | +3.9 (z 2.3) | +0.1 |

Verdict: LVN rejection is **weak**.
- It is about +2 pp with A's broad definition and not significant with the trough definition.
- It is null on BTC for troughs.
- It agrees with X15's "reject-or-run −0.3 pp".
- HVN / POC stalling: null in every cell.

### 2.5 B's replications: value-based events (B3, B4) and BTC levels (B5) [B-NEW]

**B3. Composite failed auction ("look above / below and fail").** 120 h composite, one-row 70% VA, touch within 30 bars, clock-hour baseline, week clusters.

| Event → target | CME | BTC |
|---|---|---|
| Look above and fail → far VA edge | −2.9 (n.s.), n 214 | −4.0 (z −2.1), n 585 |
| Look below and fail → far VA edge | +3.4 (n.s.), n 220 | **−11.1 (z −5.6)**, n 526 |
| Look above and fail → POC | −2.5 | −1.6 |
| Look below and fail → POC | +2.8 | −3.6 (z −1.7) |
| Race after the failure: far edge before the probe extreme re-breaks | +1.1 / −0.1 pp vs matched races | −0.6 / −4.5 pp (z −2.7) |
| POC from inside VA (every 6 bars) | +1.9 (z 1.5), n 2,272 | +2.0 (z 2.4), n 6,043 |
| "Balanced target" (py-market-profile) | −2.4 (z −2.0) | −1.9 (z −2.6) |

**B4. Acceptance damping (A's AMT-4), within-bar.** Targets away from value vs back toward value, at bars where both exist.

| Composite depth | Accepted (≥ 3 closes beyond VA) | Probe (1-2 closes) |
|---|---|---|
| CME 48 h | −2.7 pp (z −1.4) | −1.7 |
| CME 120 h | **−4.3 (z −2.0)** | +1.3 |
| CME 240 h | −3.2 (z −1.5) | +0.8 |
| BTC 120 h | **+2.3 (z +1.6)** | +4.0 (z 1.95) |

The sign flips across asset classes. It is a ledger bit at most.

**B5. BTC 1h 2017-2025, UTC-day sessions** (clock-hour baseline, week clusters; touch for POC, strict trade-through for PDH/PDL).

| Level | H = 24 | H = 120 |
|---|---|---|
| Prior-day POC (n 2,426) | +2.2 (z 2.5) | −0.3 (z −0.4) |
| Naked POC aged ≥ 2 days (n 5,204) | **−2.7 (z −5.8)** | **−6.1 (z −5.3)** |
| PDH/PDL flat (≥ 2 hourly bars within 0.1 ATR of the extreme) | −2.2 (z −2.0) | −1.0 |
| PDH/PDL plain (1 bar) | −1.8 (z −3.3) | −0.8 |
| PDH touches 1 / 2 / 3 / 4+ | −2.0 / +0.3 / +3.6 / −16.9 | −1.6 / +2.1 / +3.2 / −12.6 |
| PDL touches 1 / 2 / 3 / 4+ | −1.6 / −4.1 / −7.4 / −3.0 | −0.1 / −2.8 / −9.9 / −0.8 |

### 2.6 Evidence limitations
- CME: 1 year of hourly and 3 months of 1-minute data (2025-26, one volatility regime). BTC: 9 years of hourly data. No FX spot. Volume comes from the public datasets (BTC exchange volume, not consolidated).
- Hourly composites are coarse (48 rows over 48-240 h). The fine 1-minute RTH profiles (E-OWN-2) gave the same nulls.
- TPO samples are small (n = 39-456). External tests are secondary write-ups (X15, X9) with confidence intervals but not full methods.
- All candidates in B1-B8 are chart pivots (5/5). Key levels, FVGs and OBs were not re-tested for path effects.

---

## 3. Engine gap analysis (re-checked against `baseline_v2.pine`)

| # | Concept | Status | Lines | What the engine does / what differs |
|---|---|---|---|---|
| G1 | Composite volume profile | **present** [A✓] | 978-1015 (charts ≤ 1H: `request.security("60")` with `[1]` and `lookahead_on`; charts > 1H: `request.security_lower_tf`), 1052-1057 (cache), 1384-1414 (`f_profile`), 1900-1909 (rebuild) | Rolling 120 × 1H composite, 48 rows. Non-repainting. Rebuilt on each new hour only when `usePathVP`, otherwise on `tailBar` (1901). **[B-NEW]** With zero or na volume (cash indices, many CFDs), `lvV` holds zeros (`nz(h1V)`, 997 / 1007): `vpMean` = 0, `f_pathVol` returns 1.0 and the LVN render finds `peak` = 0. Every profile feature is then silently off; there is no time-at-price fallback (AMT-5) |
| G2 | POC | **missing** (correct as a target) | `vpSm` max never exposed | Display and value state only (AMT-3) |
| G3 | Value area | **missing** | none | Needed only for UX and the ledger bits (AMT-3) |
| G4 | Naked POC | **missing (correct)** | none | Null or negative on CME, BTC and QQQ/SPY (E-OWN-1, B5, X15) |
| G5 | HVN | **missing (correct)** | none | HVN stalling or pull is null (B8, X15) |
| G6 | LVN display | **partial** [A✓, extended] | 202-207 (inputs), 2250-2287 | Threshold runs < 0.30·peak, tails excluded, `lvnN` per side; off by default. Boxes span `f_x(lvB.first())` → `xR`. **[B-NEW]** Three further defects: (a) not distance-limited, so a far LVN stretches autoscale; (b) a run that straddles `close` (`zBot < close < zTop`) is never drawn, because the loops test `zTop < close` and `zBot > close`, so the LVN price is currently in is invisible; (c) the label "LVN" gives no semantics, while the tooltip and README call thin paths accelerators (README 52) |
| G7 | Path cost | **wrong** [A, CORRECTED mechanism] | 151-152 (input and tooltip), 570-571 (`f_row` clamp), 1417-1424 (`f_pathVol`), 1945-1947 (multiplier) | ×1.10 if vf < 0.6, ×0.85 if vf > 1.4. (a) 63-86% of the thin class are beyond-range targets clamped onto tail rows; (b) in-range thin is null to negative (within-bar −5.8 / −6.8 pp on CME at 120 / 240 h; BTC null); (c) thick is null or positive, so ×0.85 is the largest unjustified penalty in this subsystem; (d) about 30% of all pivot candidates currently get ×1.10 just for being outside the composite (43% beyond × 75% clamped thin at 120 h). On by default |
| G8 | TPO profile | **missing (correct)** | none | Would need a feed of ≤ 30 minutes; the concepts it enables are null |
| G9 | Single prints / tails | **missing**; FVG analogue present | 135-137, 689-690 (origin lockout) | The continuation reading is already encoded |
| G10 | Poor highs/lows | **partial** [A✓] | 95 (`eqTol`), 1111-1139 (EQ fold for chart swings), 807-863 (trackers keep only the extreme), 1211 (`f_pushExt`), 1790-1809 (calls) | Flat key-level extremes get no eqCount. **[CORRECTED]** Evidence is now null (B5, X9) and EQ density is neutralised by ICT-10, so this is **not a gap worth closing** |
| G11 | IB, extensions, day types | **missing (correct)** | none | Hit rate = random (E-OWN-3); descriptive statistics only |
| G12 | Open types | **missing (correct)** | none | No statistics exist (§1.12) |
| G13 | 80% rule / failed auction | **missing (correct)** | none | Rejected (X3, E-OWN-4, B3) |
| G14 | Value migration as bias | **missing (correct)** | none | E-OWN-10 |
| G15 | Balance vs imbalance | **partial** [A✓] | 887-893 (`coilScore` → density), 1892-1895 (displacement in D) | **[B-NEW]** The measurable balance proxy is the *volatility state* (B7). REG-1 owns it (PoT key), so no profile-based balance state is needed |
| G16 | Acceptance beyond value | **missing** | none | Sign flips across asset classes (B4): ledger bit only |
| G17 | Overnight H/L | **partial** [A✓] | 948-950, 597-602 | Covered; see TIME-7 |
| G18 | Baseline matching (`pBase`, PoT) | **partial / biased** [A, extended] | 1059-1062 (`sUp` / `sDn` keyed by HTF regime), 1284-1322 (`f_empPoT` / `f_potModel` / `f_potBase`), 1426-1431 (`f_openTrial` `pBase`) | Neither clock (E-OWN-0) nor volatility state (B7) is in the key. **[B-NEW]** Volatility state is the larger bias for ATR-normalised distances (±6-8 pp by tercile). Fix: REG-1 and TIME-2, including `f_potBase` (REG-1 step 3 already lists 1318) |
| G19 | LVN as invalidation | **missing (correct)** [CORRECTED: A proposed adding it] | 1343-1365 | LVN trough rejection does not replicate (B8); keep the current invalidation |
| G20 **[B-NEW]** | Multiplier semantics | n/a | 657 (`mult := 1.0` in `track`), 693-695 (score = raw × mult), 1303-1311 (PoT independent of mult) | Multipliers only re-rank candidates within a bar. Every profile multiplier must therefore be justified by *within-snapshot* evidence (B2 / B6), not by pooled hit rates |
| G21 **[B-NEW]** | Calibration ledger estimator | partial | 1376-1382 (`f_calMult`: pooled (k+2)/(e+2) per family), 1461-1499 (`f_book`) | The pooled per-family lift has the B6 problem: a family that is over-represented in low- or high-volatility bars inherits that regime as its "skill". ICT-1 copies the estimator for features. AMT-2 amends it |

---

## 4. Proposals (best first)

Design rules:
1. A multiplier is a ranking device, so its default must come from within-snapshot evidence (B2 / B6) and be neutral wherever the sign flips across datasets.
2. Pooled effects go to the PoT key (REG-1, TIME-2) or to calibration, never into `lv.mult`.
3. Every AMT feature is registered in the candidate ledger with neutral priors, so the user's own chart decides.

Changes from A's set:
- AMT-1 is kept with corrected defaults.
- AMT-2 is kept, with a corrected estimator.
- A's AMT-3 is kept as AMT-3, downgraded to P3 (UX).
- A's AMT-4 (acceptance damping) is **dropped as a multiplier** and becomes a ledger bit inside AMT-2.
- A's AMT-5 is **split**. The invalidation change is dropped (B8). The display fix becomes AMT-4.
- A's AMT-6 (poor extreme → eqCount) is **dropped** (null evidence; ICT-10).
- AMT-5 (time-at-price fallback) is new.

### AMT-1 (P1, effort S) · Fix the volume-profile path cost: no clamp bonus, neutral thick, mild thin penalty [A, CORRECTED defaults]
- **Why.**
  - The current mapping (1947) gives ×1.10 to a class that is 63-86% clamped beyond-range targets, which have no ranking edge (within-snapshot lift 0.99-1.06, B6).
  - It gives the same ×1.10 to in-range thin paths, which rank *worse* on CME (within-bar −5.8 / −6.8 pp at 120 / 240 h, z −2.6 / −3.0) and neutral on BTC.
  - It gives ×0.85 to thick paths, whose within-bar sign flips (+5.2 / +0.9 / −2.8 / −0.5 pp). The pooled thick result is positive everywhere.
  - Net: the subsystem, on by default, adds noise of ±10-15% to about 60% of the candidates, with the wrong sign where it has any.
- **Inputs (G_SCORE)**, replacing A's defaults. All get `display = display.none` (overhaul finding: 76 inputs in the legend).
  ```
  float vpThinM  = input.float(0.97, "VP · Thin-Path (LVN) Target", minval = 0.5, maxval = 1.2, step = 0.01, group = G_SCORE, display = display.none,
    tooltip = "Targets behind a low-volume path (inside the 1H composite). Measured: NOT reached more often than a random level at the same distance; slightly less on index futures.")
  float vpThickM = input.float(1.00, "VP · Thick-Path Target", minval = 0.5, maxval = 1.2, step = 0.01, group = G_SCORE, display = display.none)
  float vpOutM   = input.float(1.00, "VP · Beyond-Profile Target", minval = 0.5, maxval = 1.2, step = 0.01, group = G_SCORE, display = display.none,
    tooltip = "Targets outside the composite's price range. Neutral: they are hit less often mostly because of the volatility state, which the PoT model handles.")
  ```
- **Helper** (replaces 1417-1424). It returns `na` when the target edge lies outside the profile, so the clamp can no longer fake a thin path:
  ```
  f_pathVol(float a, float b) =>
      int   rows = vpSm.size()
      float res  = na
      if rows > 0 and vpStep > 0 and vpMean > 0
          float top = vpLo + rows * vpStep
          if b >= vpLo and b <= top
              int r0 = f_row(math.min(a, b), vpLo, vpStep, rows)
              int r1 = f_row(math.max(a, b), vpLo, vpStep, rows)
              res := (vpCum.get(r1 + 1) - vpCum.get(r0)) / (r1 - r0 + 1) / vpMean
      res
  ```
  - `a` (= `close`) may sit outside the profile, for example a new high inside the current hour, because the profile uses closed hours. Its clamp then starts the path at the edge row, which is the intended reading.
  - `na` is returned when there is no usable profile (`vpMean` = 0) as well, and the caller below guards `vpSm.size() > 0 and vpMean > 0`, so `na` means "beyond the range" only.
- **Multiplier** (replaces 1945-1947):
  ```
  if usePathVP and vpSm.size() > 0 and vpMean > 0
      float vf = f_pathVol(close, lv.nearEdge())
      lv.mult *= na(vf) ? vpOutM : vf < 0.6 ? vpThinM : vf > 1.4 ? vpThickM : 1.0
  ```
- **Tooltip and README.**
  - Input 151-152: replace "Targets behind a thin-volume path score higher, targets behind a high-volume wall lower" with "Small, measured adjustment: targets behind a low-volume node are reached slightly less often (index futures); see the VP tooltips."
  - README line 52: replace "thin-volume paths score higher than high-volume walls" with "low-volume paths get a small measured penalty; price does not travel further through them at the 1-hour scale".
- **Ledger.** With AMT-2, the class becomes bits VP_OUT / PATH_THIN / PATH_THICK, and once gated the learned lift replaces the inputs.
- **Value.**
  - Removes a ×1.10 bias toward far, out-of-balance pools and a ×0.85 bias against in-balance pools. These are a plausible source of "targets look wrong" and of jumping targets: a 10-25% relative swing can flip the ranking near the hysteresis threshold (`hyst` = 4 points).
  - The selection becomes slightly more "nearest-pool-like". That agrees with the cross-study finding that distance explains almost everything.
- **Evidence.** Moderate that the current mapping is wrong (4 datasets, within-snapshot design). Weak for the exact ×0.97.
- **Risk.**
  - Effects are small, 2-7 pp. Other asset classes may differ (BTC is already neutral), hence the mild defaults plus learning.
  - The change alters which pool wins in some states. The overhaul's verify step should A/B it on the ledger's SELECTION EDGE.
- **Effort.** S (about 15 lines).

### AMT-2 (P1, effort M; S on top of CAL-3 / ICT-1) · AMT feature bits on the candidate ledger with **cohort-demeaned (within-snapshot) lifts** [A, CORRECTED estimator; amends ICT-1 / CAL-3]
- **Why.**
  - B6 shows that ICT-1's pooled lift `((k_b+2)/(e_b+2)) / ((k_all+2)/(e_all+2))` mixes regime with ranking:
    - VP_OUT: pooled 0.85-0.92 vs within 0.99-1.06;
    - LVN_BAR on BTC: pooled 0.60 vs within 0.83;
    - IN_VALUE: pooled 1.04-1.12 vs within 0.97-1.03.
  - A multiplier fitted to pooled lifts re-ranks candidates by a regime property they all share at that bar. That is exactly the selection error the ledger exists to prevent.
  - Centring each probe's residual by its own snapshot's mean residual also cancels, to first order, any bar-level bias in `pBase`: clock (E-OWN-0) and volatility state (B7). So the feature lifts become robust even before REG-1 / TIME-2 land.
  - Every AMT effect is ≤ 7 pp and sign-unstable across assets, so per-chart learning is the only honest default.
- **Snapshot design: synchronised cohorts** (replaces ICT-1's staggered per-level probes for *feature learning*; CAL-3's role probes can share the same cohort).
  - Every H bars (`na(cohBar) or bar_index - cohBar >= H`, inside `inCalc`, past `warmup`), in step 17 after the `evaluate` loop (after 1948):
    1. **Finalise the previous cohort.** Unresolved probes get y = 0. Skip the cohort if it has fewer than 2 probes. Compute r̄ = mean(y − pBase). For each bit b: `s_b = Σ_{i∈b} (y_i − pBase_i − r̄)`, then `fR[b] += s_b`, `fV[b] += s_b*s_b` (the cohort is the cluster: cohorts never overlap), `fN[b] += n_b`, `fE[b] += Σ_{i∈b} pBase_i`.
    2. **Clear and snapshot.** Every pool level with 0.25 ≤ d/atr ≤ `maxATR` (cap 128) is pushed as `Probe {side, liq, edge, pBase = f_potBase(d, side), mask, y = -1}`. Set `cohBar := bar_index`.
  - **Grading** (step 2b, every confirmed bar): for probes with `y == -1`, apply the hit test of `f_step` (1436): `liq ? (side == 1 ? high > edge : low < edge) : (side == 1 ? high >= edge : low <= edge)`; on a hit set `y := 1`.
  - The window from `bar0+1` to `bar0+H` is exactly H bars, because finalisation runs at the next snapshot.
- **Lift and gate** (per bit):
  - `lift_b = 1 + fR[b] / max(fE[b], 1e-9)`;
  - `z_b = fR[b] / sqrt(max(fV[b], 1e-12))`;
  - `w = fN[b] / (fN[b] + featN0)`;
  - `m_b = (abs(z_b) >= featZ and fN[b] >= 100) ? f_clamp(1 + w * (lift_b - 1), 1 - featB, 1 + featB) : 1.0`.
  - Reuse ICT-1's inputs: `featN0` = 60, `featB` = 0.15, `featZ` = 2.0.
- **Apply** in the multiplier loop (1939-1948): `lv.mult *= f_clamp(Π m_b, 0.80, 1.25)` over the level's current bits.
  - While a VP bit is ungated, AMT-1's fixed input applies. Once it is gated, the learned `m_b` replaces the input (do not multiply both).
- **AMT bits** (append to ICT-1's table; NF grows by 7-8):

  | Bit | Name | Rule at snapshot | Prior evidence (within-snapshot lift, CME 48 / 120 / 240 h; BTC) |
  |---|---|---|---|
  | +0 | VP_OUT | `na(f_pathVol(close, edge))` with a valid profile | 0.99 / 0.99 / 1.04; 1.06 |
  | +1 | PATH_THIN | in range, vf < 0.6 | 0.95 / 0.92 / 0.92; 1.01 |
  | +2 | PATH_THICK | in range, vf > 1.4 | 1.06 / 1.02 / 0.97; 0.98 |
  | +3 | LVN_BAR | ≥ 1 SMC-7 trough strictly between `close` and the edge (in range) | ≥ 2 troughs: 1.03 / 0.90 / 1.04; 0.83 |
  | +4 | NEAR_EDGE | in range and (side == 1 ? vpLo + rows·vpStep − edge : edge − vpLo) ≤ 1·atr | 1.00 / 0.94 / 0.92; 0.98 |
  | +5 | IN_VALUE | `vpVAL ≤ edge ≤ vpVAH` (AMT-3) | 1.01 / 1.03 / 1.02; 0.97 |
  | +6 | EXT_FROM_VALUE | `vaRun >= 3 and side == vaPos` (AMT-3; A's AMT-4) | 0.97 / 0.95 / 0.96; 1.03 |
  | +7 (optional) | POOR_EXT | key level whose tracker counted ≥ 2 flat touches (A's AMT-6 tracker change) | null (B5, X9); add only if the tracker change ships for other reasons |

- **Pine notes.**
  - `type Probe` goes after `Trial` (396).
  - State: `var array<Probe> coh`, `var int cohBar = na`, and `var array<float> fN, fR, fE, fV` (size NF) after 1079.
  - Troughs: compute `var array<float> lvnPx` at each profile rebuild (step 15) with SMC-7's loop (at most 48 × 2N comparisons once per hour).
  - The LVN_BAR test per candidate is a loop over at most 6 troughs.
  - CPU per H bars: ≤ 128 × (NF + 6) operations; per bar: ≤ 128 hit tests. Negligible next to the 500 ms loop limit.
- **UX** (Terminal, Accuracy = Full): a "PROFILE · this chart" block, for example `VP_OUT ×1.00 (n 412, z 0.3) ~ · PATH_THIN ×0.96 (n 188, z −2.2) ✓ · LVN_BAR ×0.97 (n 240, z −1.1) ~`. Clean style: unchanged.
- **Value.**
  - Correct multipliers for every ledger feature, not only the AMT ones: ICT, SMC and classic-level bits all have the same regime confound.
  - Robustness to `pBase` miscalibration.
  - An honest per-symbol answer to "do LVNs / value matter here?".
- **Evidence.** Moderate for the estimator: B6 shows the pooled / within divergence on 4 datasets, and demeaning is the standard fixed-effects / conditional-logit identity (`calib_ml.md` §E). Weak to null for the individual AMT features.
- **Risk.**
  - Probes in one cohort share a price path. The cohort-as-cluster variance handles it.
  - Synchronised snapshots probe each level at most once per H bars, the same rate as ICT-1.
  - Cohorts with a single candidate carry no ranking information and are skipped, so charts with sparse pools learn slowly. The gate keeps those bits neutral.
  - Coordinate with CAL-3 / CAL-4 so that only one ledger exists: the cohort can carry CAL-3's role probes.
- **Effort.** M standalone; S if CAL-3 is built with synchronised cohorts.

### AMT-3 (P3, effort S) · Composite value area and value state as Terminal context (no score weight) [A's AMT-3, downgraded P2 → P3]
- **Why.**
  - It is the infrastructure for the IN_VALUE and EXT_FROM_VALUE bits (AMT-2).
  - It is the context AMT traders expect ("in value / accepted above").
  - It is explicitly **not** a target source (E-OWN-1/2, X15) and **not** a bias (E-OWN-10). Downgraded because the bits it feeds have null-to-mixed evidence.
- **Inputs (G_LVN):**
  - `useVA` = false. **[CORRECTED]** Default off: it feeds no score unless AMT-2 is on.
  - `vaPct` = 70 (50-90).
  - `showVA` = false.
  - All with `display = display.none`.
  - `needVP` (979) becomes `showLVN or usePathVP or useVA`.
  - Rebuild condition (1901): `(usePathVP or useVA) ? (newHour or h1Lower or vpSm.size() == 0) : tailBar`.
- **Compute.** In step 15, after `vpCum` (1909): A's one-row expansion loop, with ties going to the upper row (B's `blib.va_one_row` is the tested reference):
  ```
  int   nR  = vSm.size()
  int   pI  = vSm.indexof(vSm.max())
  float tot = vSm.sum()
  int   lo  = pI
  int   hi  = pI
  float acc = vSm.get(pI)
  while acc < vaPct / 100.0 * tot and (lo > 0 or hi < nR - 1)
      float up = hi < nR - 1 ? vSm.get(hi + 1) : -1.0
      float dn = lo > 0 ? vSm.get(lo - 1) : -1.0
      if up >= dn
          hi  += 1
          acc += up
      else
          lo  -= 1
          acc += dn
  vpPOC := vLo + (pI + 0.5) * vStep
  vpVAH := vLo + (hi + 1) * vStep
  vpVAL := vLo + lo * vStep
  ```
  - The `while` runs at most 48 iterations, once per hour.
  - `array.indexof` and `array.max` are documented in `reference/array.md`.
- **Value state.** Once per hourly close (`newHour` on charts < 1H using `h1C`; every confirmed bar on charts ≥ 1H using `close`):
  ```
  int p = cH > vpVAH ? 1 : cH < vpVAL ? -1 : 0
  vaRun := p != 0 and p == vaPos ? vaRun + 1 : p != 0 ? 1 : 0
  vaPos := p
  ```
- **UX.**
  - Terminal row, for example `VALUE ▲ ACCEPTED ABOVE (4h) · POC 5123.25 · VA 5110.0-5131.5`.
  - Optional POC (solid) and VAH / VAL (dotted) lines from `f_x(lvB.first())` to `xR`, drawn only within `maxATR` of the close.
  - The tooltip must say "composite 1H, 48 rows, not a TPO VA", because platforms disagree (X1: tie rule and VA % move edges on 20-65% of sessions).
  - Clean style: unchanged.
- **Evidence.** n/a (context). **Risk:** users may read it as a signal; the tooltip says "context, not a forecast". **Effort.** S.

### AMT-4 (P3, effort S) · Honest LVN display: troughs, the in-price LVN, distance limit, truthful tooltip [A's AMT-5 display half + B-NEW defects]
- **Why.**
  - G6 has three defects:
    - an LVN straddling price is never drawn;
    - there is no distance limit, so autoscale stretches;
    - the semantics are wrong: README and tooltip say thin paths accelerate.
  - The LVN zones are a reference-product feature ("LVN zones from 1H volume profile"), so they stay. They just stop implying a measured property they do not have.
  - The invalidation change in A's AMT-5 is **dropped**: SMC-7 trough rejection is +1.7 pp (z 1.2) on CME and 0.0 on BTC (B8).
- **Spec** (rendering, 2250-2287):
  1. Detect SMC-7 troughs (shared with AMT-2's `lvnPx`). Keep A's threshold runs as an input option `lvnMode` = "Troughs" / "Threshold" (default "Troughs").
  2. Draw a zone `[trough − half-width, trough + half-width]`. Half-width = the run of rows around the trough below `(trough + 0.5·(neighbour peak − trough))`, at least 1 row.
  3. Add the straddling case: if `zBot <= close and zTop >= close`, draw it first and label it "LVN ·in".
  4. Skip zones with `math.abs(mid − close) / atr > maxATR` (competitors.final distance limit).
  5. Use `lvnN` per side, as now.
- **Tooltip:** "Low-volume node of the 1H composite. Measured on index futures and BTC: price moves ~8% faster through these at the 15-minute scale, is not reliably rejected here, and targets beyond them are reached no more often (slightly less on index futures)."
- **Evidence.** Weak (display semantics follow B8, X15 and E-OWN-8). **Risk.** None to scoring. **Effort.** S.

### AMT-5 (P3, effort S) · Time-at-price fallback when the symbol has no volume [B-NEW]
- **Why.** On symbols without volume, every profile feature (path cost, LVN zones, VA) is silently disabled (G1):
  - `nz(h1V)` pushes zeros (997, 1007);
  - `vpMean` = 0, so `f_pathVol` returns 1.0;
  - `peak` = 0, so no LVN is drawn.
  
  That covers cash indices (SPX, NDX, DJI), many CFDs and some FX feeds. Market Profile's original unit is time at price (TPO), which needs no volume.
- **Spec.** In `f_profile` (1384), compute `float vTot = lvV.sum()` first. If `vTot <= 0`, use `hv = 1.0` for every hour (each hourly bar spreads one unit over its range at 60% and its body at 40%, as now). That is an hourly TPO-like profile.
  - Expose `vpTPO = vTot <= 0` and show "Profile: time-at-price (no volume)" in the Terminal / tooltip.
  - Optional input `vpSrc` = "Auto" / "Volume" / "Time": "Time" forces the TPO profile even where volume exists, for AMT purists.
- **Evidence.** n/a (robustness). The TPO-based tests in this study (E-OWN-2/5/6) behaved like the volume ones, so the same AMT-1 / AMT-2 semantics apply.
- **Risk.** Users may not notice which source is active, hence the readout. **Effort.** S (about 6 lines).

### Dependencies to note (owned by other studies; strengthened by this one)
- **REG-1 / QPOT-03: volatility state as the PoT surface key, including `f_potBase`.** B7 independently finds ±6-8 pp hit-vs-base swings by volatility tercile on CME and BTC (z up to −12). It is the largest bar-level bias found in this domain. AMT-2's demeaning protects the feature lifts, but the displayed PoT and the ledger's EDGE verdict still need REG-1.
- **TIME-2 / TIME-3: clock dimension.** E-OWN-0 (A): −6 to −11 pp spurious edges without clock matching.
- **ICT-10: neutral EQ density.** It removes the motivation for A's AMT-6.

### Considered and rejected (with the evidence)
- **Naked POC, prior VAH / VAL / POC, composite POC as DOL level sources.** Null or negative vs distance-matched random levels on CME, BTC and QQQ/SPY (E-OWN-1/2, B5, X1, X15). Offer them only as display (AMT-3) or as ledger bits.
- **80% rule and composite failed auction.** X3, E-OWN-4, B3 (BTC −11.1 pp, z −5.6).
- **Extended-acceptance damping as a default multiplier** (A's AMT-4). Within-bar the sign flips across asset classes: CME −4.3 (z −2.0) vs BTC +2.3 (z +1.6) (B4). Kept only as bit EXT_FROM_VALUE.
- **LVN trough as invalidation anchor** (A's AMT-5). Trough rejection +1.7 pp (z 1.2) on CME, 0.0 on BTC (B8); external −0.3 pp [−5.0, +4.4] (X15).
- **Poor (flat) key-level extremes → eqCount** (A's AMT-6). CME +1.6 pp (z 1.1), BTC −0.4 pp vs plain (B5), NQ +1.0 [−2.8, +4.8], QQQ/SPY null (X9). EQ density itself is null (ICT-10).
- **Balanced target** (py-market-profile). −2.4 / −1.9 pp (B3).
- **Profile / range width as a balance-regime key.** Absorbed by the volatility ratio (B7); REG-1 covers it.
- **IB extremes / extensions as targets, overnight H/L specials, open types, day types, profile shapes, single prints as magnets, TPO construction, value migration as bias.** As in A: null, no statistics, or RTH-specific judgement.
- **`request.footprint()` for per-bar POC / VA.** Premium/Ultimate-only and one call per script (`limitations.md`). It would lock out most users.

---

## 5. Sources

External (re-opened by B unless noted):
- tradeify, "Market Profile Explained With a 589 Session TPO Test" (VA algorithm, tie rules, 2-hour IB, POC revisit, 80% rule): https://tradeify.co/education/market-profile
- tradingstats.net:
  - "Initial Balance Breakout Statistics: ES & NQ Futures (2015-2025)": https://tradingstats.net/initial-balance-breakout-statistics/
  - "Single Prints: 3,847 Zones Backtested": https://tradingstats.net/single-prints-market-profile-research/
  - "How Often Does the High of the Day Hold?": https://tradingstats.net/high-of-the-day-hold/
- ULTIMA "Volume & Time" lessons (independent distance-matched replications; secondary write-ups):
  - M2.01 Point of Control: https://www.ultimaresearch.xyz/en/lessons/m2-01/
  - M2.03 HVN / LVN: https://www.ultimaresearch.xyz/en/lessons/m2-03/
  - M2.09 Poor highs and lows: https://www.ultimaresearch.xyz/en/lessons/m2-09/
- Osler, C. (2000). Support for Resistance: Technical Analysis and Intraday Exchange Rates. FRBNY Economic Policy Review 6(2), 53-68: https://www.newyorkfed.org/medialibrary/media/research/epr/00v06n2/0007osle.html
- Kavajecz, K. & Odders-White, E. (2004). Technical Analysis and Liquidity Provision. RFS 17(4), 1043-1071: https://ideas.repec.org/a/oup/rfinst/v17y2004i4p1043-1071.html
- Chung, K. & Bellotti, A. (2021). Evidence and Behaviour of Support and Resistance Levels in Financial Time Series. arXiv:2101.07410: https://arxiv.org/abs/2101.07410
- Garzarelli, F., Cristelli, M., Pompa, G., Zaccaria, A. & Pietronero, L. (2014). Memory effects in stock price dynamics: evidences of technical trading. Scientific Reports 4:4487: https://www.nature.com/articles/srep04487
- Jung, J. & Lee, K. (2026). Do Round Numbers Hold Prices? arXiv:2610.34787: https://arxiv.org/abs/2610.34787
- Moustafa, A., Neagu, R.-M. & Kalita, J. (2026). ViperQ: Order Flow Pattern Recognition via Auction Market Theory for RL Trading. arXiv:2609.13825: https://arxiv.org/abs/2609.13825
- Farmer, J.D., Gillemot, L., Lillo, F., Mike, S. & Sen, A. (2004). What really causes large price changes? Quantitative Finance 4(4) (via `orderflow_micro.md`; not re-opened)
- Park, C.-H. & Irwin, S. The Profitability of Technical Trading Rules in US Futures Markets (not re-opened): https://farmdoc.illinois.edu/publications/the-profitability-of-technical-trading-rules-in-us-futures-markets-a-data-snooping-free-test
- LuxAlgo concept library (definitions; "treat the claim skeptically"):
  - naked POC: https://www.luxalgo.com/library/concept/naked-poc/
  - poor high/low: https://www.luxalgo.com/library/concept/poor-high-poor-low/
  - 80% rule: https://www.luxalgo.com/library/concept/80-percent-rule/
  - open types: https://www.luxalgo.com/library/concept/open-types/
- Poor highs / lows (practitioner):
  - https://axiafutures.com/blog/trading-strategies-around-poor-lows-and-poor-highs/
  - https://www.marketcalls.in/market-profile/poor-high-and-poor-low-market-profile-structure-explained.html
- Open types (practitioner; A's list, not re-opened):
  - https://paracurve.com/2020/02/day-opening-types.html
  - https://www.trenddaytrading.com/market-profile-trading
- 80% rule (practitioner):
  - https://www.elitetrader.com/et/threads/value-area-80-rule.95941/
  - https://mypivots.com/article/details/30/the-80-rule (search summary only; host blocked here)
- Pine v6 limits: `docsrc/jabez4jc_pinescriptv6/writing_scripts/limitations.md` (§Intrabars: 100K on non-professional plans; `request.footprint()` note) and `concepts/other_timeframes_and_data.md` (§`request.footprint()`)
- Data: CME continuous OHLCV, https://github.com/axb0306/cme-futures-ohlc; BTC 1h (`study/classic_tools/btc_1h.csv`)

Internal:
- `study/amt_profile.md` (A)
- `study/ict_liq.final.md` (ICT-1, ICT-10)
- `study/calib_ml.md` (CAL-3, CAL-4, §E ranking)
- `study/quant_regime.md` (REG-1), `study/quant_pot.md` (QPOT-03)
- `study/ict_time.final.md` (TIME-2, TIME-3, TIME-7)
- `study/smc_impl.final.md` (SMC-7)
- `study/competitors.final.md` (LVN distance limit)
- `study/classic_levels.md` (VWAP)
- `study/orderflow_micro.md` (`request.footprint`, Farmer et al.)

Not reachable in this session:
- tradingview.com (A's NPOC script and the "Naked POCs Explained" post);
- direct fetches of ultimaresearch.xyz pages M2.02 / M2.07 / M2.08 (value area, IB, single prints); the web-scraping credits ran out before these could be read.
