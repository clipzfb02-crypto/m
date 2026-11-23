# ICT Liquidity Theory: combined final study (Researcher A + Researcher B)

Domain: ICT (Inner Circle Trader) liquidity theory.
- Buy-side and sell-side liquidity; equal and relative equal highs/lows; old-high hierarchy.
- IRL/ERL and the delivery cycle; premium/discount.
- Low-hanging fruit vs major liquidity; high- vs low-resistance runs.
- Sweep vs run, purge, MSS, turtle soup, inducement, trendline liquidity.
- How deep stops sit, when a pool is spent, and how ICT picks the draw on liquidity.

Plus all the hard evidence found on where stops sit and what price does after they are taken.

Engine studied: `brief/baseline_v2.pine`. Line numbers below refer to it, and it is byte-identical to `/home/user/m/indicators/dol_engine.pine` (checked with `diff`).

**Markers.**

| Marker | Meaning |
|---|---|
| **[A]** | Researcher A's finding, kept as written. |
| **[A✓]** | A's finding, re-checked (by B's own data or a sibling study that re-read the source). |
| **[CORRECTED]** | A's finding changed by B; the reason is given. |
| **[NEW-B]** | Added by B. |
| **[B-test]** | Number from B's original tests. Scripts and raw outputs are in `study/ict_liq_tools/` (Appendix A). |

**Evidence grades.**

| Grade | Meaning |
|---|---|
| strong | Peer-reviewed, or a large replicated quantitative study. |
| moderate | Published or reproducible numbers. |
| weak | Practitioner consensus, or a small or vendor sample. |
| none | Folklore. |

A grade measures how strong the evidence is. Whether that evidence **supports**, is **null** on, or **contradicts** the ICT claim is stated separately.

**Research-tool note (B).**
- The shared WebSearch budget for this turn was already used up on B's first call.
- WebFetch could not resolve papers.ssrn.com or quartersequence.com: both are outside this session's allowed network. Those hosts must be allowed before the SSRN pages can be re-fetched.
- B did not route around these limits through other scraping services.
- Instead, B verified A's sources by cross-checking sibling studies that had read them (mainly `academic_sr.md`, `orderflow_micro.md`, `skeptic.md`, `bias_dol.md`, `ict_struct.md`). B also ran original tests on local data: 7 hourly datasets and 5 five-minute datasets.
- Sources that nobody in this project could open are marked "not re-verified", and their grades are capped.

---

## 0. Executive summary (combined, corrected)

1. **Distance and volatility decide which pool is reached. The ICT labels add almost nothing beyond distance.**
   - Engine-faithful pools (pivLen 5, strict trade-through), measured against a distance-matched random level `S(d)`, i.e. the engine's `f_potBase` idea: pools 0.25-4 ATR away are reached exactly as often as distance implies.
     - 1H, 7 datasets: +0.1 ± 0.4 pp, n 52,762.
     - 5m, 5 CME futures: +0.8 ± 0.6 pp, n 30,887.
   - Equal highs/lows: +0.3 ± 1.8 pp (1H) and −0.1 ± 2.1 pp (5m), against +0.2 / +0.9 pp for single swings. **[B-test]** This replicates A's E6 ("< 1 pp") with independent data.
   - Test count, ICT "priming" and swing prominence show no consistent effect across timeframes.
   - The engine's first-passage / empirical PoT backbone is the right architecture. ICT features belong as bounded, **learned** modifiers.
2. **After a pool is taken there is no reversal edge.** **[CORRECTED]** A wrote "continuation dominates"; that is overstated, because the continuation lean is only 0-2 pp.
   - ±1 ATR race after a sweep, against the chart's unconditional odds:
     - 1H: all +1.1 ± 0.5 pp (n 12,550); REJECT (close back inside) +1.5 ± 0.7 (continuation, not reversal); HOLD +1.0 ± 0.9.
     - 5m: all −0.2 ± 0.7 (n 7,705). **[B-test]**
   - Siblings agree:
     - REJECT → continuation 52.6% (n 1,402, `ict_struct`);
     - race 0.497-0.510 after holds and rejects (`skeptic`);
     - Turtle Soup never above geometry on 9 datasets (`bias_dol`).
   - The sign differs by market. REJECT excess: NQ +4.9, GC +6.1, ES −4.6, EURUSD −0.8 pp (1H).
   - So the engine's fixed "REJECT = reversal (−1)" mapping (line 1581) is **wrong**. The useful static rule is narrower: a HOLD *against* the HTF bias leans to reversal (−2.3 ± 1.6 pp here; 56% reversal, n 381, in `ict_struct`). Everything else should be learned per chart.
3. **ICT's context rules for sweeps fail on data.** **[NEW-B]**
   - Premium/discount: a REJECT sweep on ICT's reversal side (BSL in premium, SSL in discount) **continued** more, not less: +1.7 ± 1.4 pp (1H, n 1,369) and +5.1 ± 1.9 pp (5m, n 770). On the other side it was −1.4 / −3.4 pp. If anything, ICT's sign is wrong.
   - The IRL↔ERL alternation, measured as excess over driftless race geometry vs a control:
     - after liquidity is taken, IRL first: +1.8 pp (1H) but −2.3 pp (5m);
     - after IRL is tagged, ERL first: about 1 pp.
   - **Not supported.** Keep both only as display and ledger features.
4. **ICT's high- vs low-resistance run is the one ICT path claim with support.** **[NEW-B]**
   - Each untouched *opposing* FVG between price and a pool lowers the chance of reaching it within 30 bars by about 2-3 pp beyond distance:
     - 1H: −2.8 ± 0.8 pp (n 4,757);
     - 5m: −2.1 ± 1.0 pp (n 3,387).
   - It is negative in 11 of 12 datasets and holds within both trend strata (with −2.4, against −3.2 pp).
   - The engine's path term is volume-only (1945-1947). This is a cheap, evidence-backed addition (ICT-5).
5. **Stacked pools ("low-hanging fruit" vs "outermost is the draw") are heterogeneous. Neither fixed rule is justified.** **[NEW-B, CORRECTED]**
   - The sibling study's hourly "path crowding" penalty (−6 / −10 / −29 pp for 1 / 2 / ≥3 intermediate pools, `academic_sr` §2.4) is **contaminated**.
     - Its 1H sample included `amt_data/cme/GC/GC_1h_*.csv`, which interleaves two contract months: 742 bars with jumps over 1.5%, 279 of them jump-and-back.
     - That file alone gives −9.6 / −18.8 / −31.5 pp.
   - On clean data, crowding at 1H is mixed: NQ −3.0 / −8.5 / −8.6, GC −0.9 / −4.7 / −2.9, BTC +2.2 / +4.9 / +8.0. At 5m it is positive (+4.0 / +4.3 / +5.1 pp). The sibling 1m numbers on clean files are negative.
   - The engine's hard inner ×0.70 and `+0.45·stack` (682-685) are much larger than any measured effect, in either direction. Make them neutral and learned (ICT-10).
6. **Where stops sit is well documented; it shapes geometry, not the draw.**
   - Osler (J. Finance 2003; JIMF 2005; RBS order data): stop-buys sit just beyond round numbers (14.4% in 01-10 vs 7.4% in 90-99) and take-profits sit at them. Crossings cascade for 15 minutes to 2 hours.
   - Kavajecz & Odders-White (RFS 2004): S/R locates book depth.
   - On bars, sweep wicks penetrate a median 0.23-0.28 ATR and an 80th percentile of 0.51-0.64 ATR **[B-test, replicates `orderflow_micro` T1]**. They **stop short** of a round number just beyond a pool (−4.2 pp, `orderflow_micro` T2d).
   - **[CORRECTED]** A's ICT-3 extended zones *past* round numbers. That is replaced by the OF-4 rule: cap zones at the round and place stops beyond it.
7. **The ICT daily-bias close rule is pure geometry.** **[CORRECTED]**
   - "Closed above PDH → PDH+ next" is right 69-76% of the time; a shuffle null gives 68-76% (−2.2 to +1.9 pp, 13 datasets, `bias_dol`).
   - A's ICT-6 (feed it into D) is dropped. It survives only as a readout (BIAS-3) and a ledger bit.
8. **Engine code findings A missed.** **[NEW-B]**
   - (a) **EQ merges are one-sided.** A right-hand print beyond the stored pool trades through it at step 3 (strict `>`) before the pivot is confirmed `pivLen` bars later. So `f_mergeAt`'s "outer" branch (1116-1126) is effectively dead for chart pivots. EQ pools are only "left ≥ right" (ICT's "primed") or exact pairs. A "right slightly higher" pair becomes a raid event plus a fresh single pool.
   - (b) **Raid events are noisy.** Every pool hit on a bar adds `±tier` to `liqEvt` (1580-1582), so one wide bar through a 3-pool stack moves D by up to 0.75 × `wL`. A 1-tick relative-equal poke counts as a full REJECT. The HOLD threshold `lv.top` depends on the display input `zoneATR`.
   - (c) **Exact touches are invisible.** `high == level` is neither a test (`gap > 0`, 654) nor a sweep (strict `>`, 624).
9. **Best single improvement: fix the raid-event mapping now** (ICT-9: small, evidence-backed, removes a wrong-sign D input that can flip the target). **The backbone:** grade every candidate on a shadow ledger with ICT feature bits (ICT-1, built on CAL-3's ledger), so each ICT claim is measured on the user's own chart and earns or loses weight. Section 4 lists 9 proposals; two of A's are dropped (ICT-6, ICT-8).

---

## 1. Concepts: precise definitions and parameters

ICT primary-source quotes are timestamped in the Quarter Sequence study pages and the 2022 Mentorship notes (Tanja, Forex Factory). "Ep." means 2022 Mentorship episode. **[A]** B could not re-fetch Quarter Sequence (host blocked). `ict_struct.md` independently quotes several of the same definitions with timestamps (e.g. 3-candle swing, Ep. 3, 17:53; MSS, Ep. 6, 20:52).

### 1.1 Buy-side / sell-side liquidity (BSL / SSL) [A, evidence A✓]
- **Definition (ICT).** "Liquidity is buy orders and sell orders."
  - Buy-side liquidity sits **above old highs**: short sellers' protective buy stops plus breakout buy orders.
  - Sell-side liquidity sits **below old lows**.
  - "A single point of reference" (one old high) forms a pool (Liquidity Purge & Revert, 2020, 5:09).
- **Algorithm.** Pool = unswept swing extreme. BSL price = swing high; zone = `[high, high + depth]`. Swept when `high > level`: a strict trade-through, and a wick is enough ("it does not need to close above that", Ep. 3, 13:47).
- **Evidence and direction.**
  - Stops really do sit just beyond such levels: strong (E1-E3).
  - **[NEW-B]** "Price is drawn to them more than distance implies" is **null**:
    - +0.1 ± 0.4 pp (1H) and +0.8 ± 0.6 pp (5m) **[B-test]**;
    - −2.0 ± 0.3 pp at 1m (`academic_sr` §2.3).
  - Pools are **where** stops are, not **attractors**.

### 1.2 Equal highs/lows and *relative* equal highs/lows [A + NEW-B]
- **Definition (ICT).** "Multiple candles or levels that look very close to one another in height or depth". "It doesn't make a difference if it's exactly or off by one or two pips" (2017, 8:08). There is no numeric tolerance. Practitioner settings: 0.05-0.1% of price, a few ticks, or 0.10-0.15 ATR (LuxAlgo-style ATR margins).
- **Reading.** Equal highs are liquidity, not resistance: "smooth edges like to be made jagged" (2023, 2:33:47).
- **"Priming"** (ICT 2024 Mentorship L1, 1:15:22). When the left of two relative equal highs is slightly higher than the right, ICT calls a run on them "very very high probability". Mirror for lows. **[A]**
- **Algorithm.** Merge a new pivot into an existing same-kind unswept pool when `|p_new − p_pool| ≤ tol` (0.10 ATR in the engine). The pool moves to the outermost print; `eqCount++`.
- **[NEW-B] What the engine actually does (asymmetry).**
  - Step 3 (sweeps, 1559-1589) runs on every confirmed bar, before the pivot that printed the second high is confirmed `pivLen` bars later (step 9, 1753-1776).
  - So a second high even 1 tick **above** the first trades through the first pool. The engine records a raid (`liqEvt`), ghosts it if active, and deletes the pool. When the new pivot confirms, `f_mergeLiq` finds nothing and creates a **single** pool.
  - Only second prints **at or inside** the stored level merge. This is ICT's "primed" configuration plus exact equals.
  - `f_mergeAt`'s outer-move branch (1116-1126) is reachable only for registry re-entry merges (1845, `countEq = false`).
  - Consequences:
    - the `EQx2` tag appears only for primed or exact pairs;
    - every "right-higher relative equal" injects a spurious raid event into D;
    - the "EQ" feature is not what ICT means.
- **Evidence [B-test]** (pools 0.25-4 ATR, reach within 30 bars, edge vs `S(d)`):

  | Class | 1H edge (n) | 5m edge (n) |
  |---|---|---|
  | Single | +0.2 ± 0.4 (49,047) | +0.9 ± 0.6 (28,765) |
  | EQ, any | +0.3 ± 1.8 (2,230) | −0.1 ± 2.1 (1,350) |
  | EQ primed (later print inside) | +0.1 ± 2.1 (1,550) | +3.9 ± 2.6 (899) |
  | EQ exact (≤ 0.02 ATR) | +0.7 ± 3.4 (680) | −8.0 ± 3.8 (451) |
  | Right-beyond relative equal ("RH") | −1.6 ± 2.1 (1,553) | −0.8 ± 3.0 (792) |

  - Distance-bucket matched (0.25-1 / 1-2 / 2-4 ATR), EQ minus single is within noise in every bucket.
  - Priming vs exact flips sign between 1H and 5m. That is a multiple-comparison blip, not an effect.
  - **Verdict:** the EQ label and priming add nothing to reach (moderate evidence, null). It agrees with A's E6 and with `orderflow_micro` T3 (equal prints carry no post-sweep information).

### 1.3 Old-high hierarchy: STH → ITH → LTH (ICT 2022 Ep. 8 and Ep. 12) [A, evidence NEW-B]
- **STH.** A 3-candle swing, confirmed when the candle after it closes.
- **ITH.** An STH with a lower STH on each side.
- **LTH.** An ITH with a lower ITH on each side, "generally ... linked to a higher time frame, daily chart" (Ep. 12, 29:39).
- **Use.** The higher the order, the bigger the pool and the more important the draw.
- **[NEW-B] Evidence, using swing prominence as the measurable proxy** (`prom` = height above the right-side low, in ATR; what the engine's density uses, 682):
  - 1H: high-prominence pools are reached **less** than distance implies (high tercile −1.4 ± 0.7 vs low +1.7 ± 0.7 pp). It holds in both trend strata.
  - 5m: no difference (+1.1 vs +0.5).
  - The sibling found prominence predicts a *larger run after the take* (+0.15 ATR, `orderflow_micro` T3), not a higher reach probability.
  - So "higher-order swing = more likely draw" is not supported. Within a pivLen-5 pool set, the ITH flag is nearly automatic, because neighbours within 5 bars are lower by construction. A's ICT-8 is dropped.

### 1.4 Internal vs external range liquidity (IRL / ERL) and the delivery cycle [A, evidence NEW-B]
- **Dealing range.** Swing low to swing high of the current leg.
- **ERL.** Stops beyond the range extremes.
- **IRL.** "Short-term lows or short-term highs inside a price leg ... or an imbalance in that same range" (Ep. 3, 35:04).
- **Cycle (community codification).** ERL taken → draw to IRL (FVG / OB / short-term swing inside the leg) → IRL rebalanced → draw to the next ERL. ICT uses it for trade management: "partials, internal range, external range" (Ep. 6, 45:49).
- **Engine note (sibling `ict_struct` §1.9 and ICTS-4).** `f_structure`'s `rngH/rngL` are the last pivots, not ICT's `[protected, weak]` leg range. Any IRL/ERL logic needs ICTS-4 first.
- **[NEW-B] Test.** Race between the nearest live pool (ERL proxy) and the nearest *untouched* opposite-side FVG (IRL proxy), 48 bars. Excess = observed P(FVG first) minus driftless gambler's-ruin geometry `dPool/(dPool + dFVG)`.

  | Phase | 1H excess (n) | 5m excess (n) |
  |---|---|---|
  | Control (neither just happened) | −0.1 ± 0.6 (19,442) | −0.3 ± 0.7 (11,871) |
  | Liquidity just taken (≤ 3 bars): ICT says IRL next | +1.7 ± 0.9 (3,267) | −2.6 ± 1.1 (2,006) |
  | IRL just tagged (≤ 3 bars): ICT says ERL next | −1.0 ± 0.8 (5,317) | −1.0 ± 0.9 (4,239) |

  - Geometry alone is accurate to within 0.3 pp in the control. That confirms the sibling finding that the race math is right (`ict_struct` §2.2: 62.8% vs 64.8% predicted).
  - The ICT phase effects are 1-2 pp and flip sign between timeframes. **Verdict: not supported** (weak evidence, null). Display only (ICT-4).

### 1.5 Premium / discount [A, evidence NEW-B]
- **Definition.** Premium is above 50% of the dealing range; discount is below (Ep. 2). "Any time the market trades above an old high it's a short-term premium" (Ep. 14).
- **ICT use.** A run below an old low *in discount* is "probably going to be a turtle soup buy"; above an old high in premium, a turtle-soup sell (Core Content M1, 7:14 / 40:16). Buy in discount, target premium ERL.
- **[NEW-B] Test** (post-sweep ±1 ATR race, excess over the chart's unconditional odds for the same direction):

  | Sweep type | 1H, P(continuation) excess | 5m |
  |---|---|---|
  | REJECT on ICT's reversal side (BSL in premium / SSL in discount, inside the range) | **+1.7 ± 1.4** (n 1,369) | **+5.1 ± 1.9** (n 770) |
  | REJECT on the continuation side | −1.4 ± 1.9 (699) | −3.4 ± 2.5 (416) |
  | REJECT of the range extreme (ERL) against the 100-bar trend (textbook turtle soup) | +2.9 ± 1.7 (1,085) | −0.2 ± 2.2 (721) |

  - ICT predicts the first row to *reverse*. It continued more.
  - The sibling `skeptic` C15 finds premium → sell contradicted at monthly horizons (George & Hwang 2004: nearness to the 52-week high predicts continuation).
  - **Verdict: contradicted** (moderate evidence). Do not condition the draw on P/D by default.

### 1.6 Low-hanging fruit vs major liquidity; stacked pools [A, CORRECTED]
- **ICT.**
  - "Look for low hanging fruit, aim for the easiest target to get to, aka the next spot where previous stops are waiting" (Ep. 3).
  - "Pick the lowest hanging fruit and be happy when it hits that" (Ep. 14).
  - The major draw (HTF ERL) is the "objective".
- **[NEW-B] Logical point A missed.** For "which liquidity is reached **next**", the nearest unswept pool on a side is the only candidate on that side: the outer pool cannot be reached before the inner one. The engine's inner ×0.70 penalty (684-685) and `+0.45·stack` density (682) make the DOL the *outermost* pool, i.e. ICT's "objective", not its "next". The HUD's PoT is honest about the lower odds, but the "next draw" framing is not.
- **Evidence on whether the outer pool is reached as its distance implies** (same-side intermediate pools `nIn`, targets 1-4 ATR, no opposing FVG in the path):

  | Dataset | nIn 0 | 1 | 2 | ≥ 3 |
  |---|---|---|---|---|
  | NQ 1H (clean) | −0.1 | −3.0 | −8.5 | −8.6 |
  | GC 1H (clean) | +1.3 | −0.9 | −4.7 | −2.9 |
  | BTC 1H | +0.0 | +2.2 | +4.9 | +8.0 |
  | 1H pooled, 7 sets | +0.0 ± 0.4 | +1.3 ± 0.6 | +2.3 ± 1.1 | +3.2 ± 2.2 |
  | 5m pooled, 5 CME | +0.7 ± 0.6 | +4.0 ± 0.9 | +4.3 ± 1.7 | +5.1 ± 4.1 |
  | 1m (sibling, clean files) | −1.2 | −1.5 | −3.5 | −6.1 |
  | **GC 1H corrupted file alone** | −0.5 | **−9.6** | **−18.8** | **−31.5** |

  - **[CORRECTED, sibling]** `academic_sr`'s 1H crowding prior (−6.0 / −10.3 / −29.3 pp) is driven by the corrupted GC 1H file. Its 1-minute result stands.
  - **Verdict:** the sign differs by market and timeframe (moderate evidence, heterogeneous). Neither "outermost is the draw" (engine) nor a strong crowding penalty (ACAD-1) should be hard-coded: neutral default, learned per chart (ICT-10, ICT-1).
  - Osler-type cascades (crossing inner stops accelerates price into the outer pool) explain the positive cases. Barrier depth (Kavajecz) explains the negative ones.

### 1.7 High- vs low-resistance liquidity runs (Core Content M1 "Liquidity Runs", 7:26 and 19:25) [A, evidence NEW-B]
- **High-resistance run.** A run back to an old high behind lower highs and opposing PD arrays: "the least probable trading condition".
- **Low-resistance run.** In the trend direction with a clear path: "like a hot knife through butter".
- **[NEW-B] Test: untouched opposing FVGs between price and the pool** (bearish FVGs above price for a BSL target, bullish below for SSL; size ≥ 0.15 ATR; removed when first touched), pools 1-4 ATR, no same-side intermediate pool:

  | Opposing FVGs | 1H edge (n) | 5m edge (n) |
  |---|---|---|
  | 0 | +0.0 ± 0.4 (21,269) | +0.7 ± 0.6 (12,125) |
  | 1 | **−2.8 ± 0.8** (4,757) | **−2.1 ± 1.0** (3,387) |
  | ≥ 2 | −2.6 ± 1.8 (919) | −1.7 ± 1.9 (889) |

  - By the 100-bar trend toward the target, 1H, one FVG: with −2.4 ± 1.2, against −3.2 ± 1.2. So it is not just a trend proxy.
  - Per dataset (≥ 1 minus 0): NQ −0.2, GC −2.4, EU −4.3, ES +1.6, RTY −4.1, YM −5.4, BTC −2.9, ES5 −3.6, NQ5 −2.8, GC5 −3.2, RTY5 −1.7, YM5 −2.5. **Negative in 11 of 12.**
  - **Verdict: supported, small** (moderate evidence). This is the only ICT path claim with support. The engine's path cost is volume-only (1945-1947) → ICT-5.

### 1.8 Sweep vs run; purge; market structure shift [A + CORRECTED evidence]
- **ICT names.**
  - Run = liquidity run / raid / stop run.
  - Sweep = a shallow run through liquidity that reverses.
  - Run = goes through and continues.
  - Purge = run plus revert; the stops count as purged "only if we start to move away from it" (2020, 21:31).
  - An MSS is counted "only on the basis of a liquidity purge" (22:02). ICT wants a **body close** beyond the short-term swing plus displacement (Ep. 6, 19:39).
- **Bar-close classification (the engine's own, 1581), BSL** (mirror for SSL):
  - HOLD: `close > lv.top` (= level + `zoneATR`·ATR at creation);
  - REJECT: `close < level`;
  - NEUTRAL: otherwise.
- **Evidence (combined).**
  - 1H **[B-test]**: REJECT → continuation +1.5 ± 0.7 pp (n 5,899); HOLD +1.0 ± 0.9 (4,924); HOLD with the 100-bar trend +2.3 ± 1.1; HOLD against −2.3 ± 1.6.
  - 5m **[B-test]**: REJECT +0.6 ± 0.9; HOLD −1.6 ± 1.1.
  - `ict_struct`: REJECT → continuation 52.6% (n 1,402). HOLD against the HTF swing → **reversal 56%** (n 381). HOLD with it → continuation 53.2% (n 423). MSS reversal reads 45.6% (n 171) without displacement and 50.5% (n 97) with it.
  - `skeptic`: ±1 ATR race 0.497-0.510 after holds and rejects (5m / 15m / 1h).
  - `orderflow_micro` T1: the post-sweep burst is **symmetric** (volatility, not direction) for 3-10 bars.
  - Osler 2005: cascade continuation for 15 minutes to 2 hours. `academic_sr` §2.5 at bar level: +1.1 pp hold (z 2) at 30-120 minutes, +5.1 pp (z 3.3) for pools that were 4-12 hours old.
- **Verdict:** no reversal edge after REJECT (strong: several independent large replications); at most a 1-2 pp continuation lean; failed-breakout lean only for HOLD against the HTF trend. Market-specific signs (NQ +4.9 / GC +6.1 / ES −4.6 pp) justify a per-chart learner (ICT-2), with a corrected static prior now (ICT-9).
- **[NEW-B] Purge depth (how far stops are run):**

  | Sample | REJECT q25 / q50 / q80 / q90 penetration (ATR) |
  |---|---|
  | 1H, B | 0.12 / 0.28 / 0.64 / 0.91 |
  | 5m, B | 0.11 / 0.23 / 0.51 / 0.76 |
  | Pooled, `orderflow_micro` T1 | median 0.233, q80 0.518 |

  - No depth bucket carries directional information (T1).

### 1.9 Turtle soup [A, evidence CORRECTED]
- **Original** (Connors & Raschke, *Street Smarts*, 1995), long side:
  1. a new 20-day low;
  2. the prior 20-day low is at least 4 sessions older;
  3. buy stop 5-10 ticks above the prior low, good for today only;
  4. stop 1 tick under today's low.
- **ICT version.** A fake break of an old low in discount, an aggressive response, then an MSS (Ep. 7, 25:28).
- **Evidence.**
  - `bias_dol`: Turtle Soup excess over geometry on 9 datasets ranges from −0.129 to +0.082; it is "never reliably above geometry".
  - B: REJECT sweeps of pools ≥ 50 bars old +1.4 ± 1.6 pp continuation (1H); textbook context (ERL, against trend) +2.9 / −0.2 pp.
  - **Verdict: contradicted / null** (moderate).

### 1.10 Trendline liquidity ("phantom trend line") [A]
- Stops rest beyond an obvious diagonal with 3+ touches. ICT himself says "everybody's going to have a different diagonal trend line" (2024, 2:23:52).
- **Not worth building**: no evidence, and the definition is not unique.

### 1.11 Inducement (IDM): a retail SMC term, not ICT's [A]
- The first pullback low after a BOS, followed lower until a candle makes no new low. Taken on a wick. Definitions disagree (pullback before vs after the break).
- It is the first liquidity met on the retrace, i.e. low-hanging fruit. It overlaps inner pools. Not built.

### 1.12 Liquidity voids, NWOG/NDOG, SMT [A]
Out of scope here (PD-array and intermarket studies).

### 1.13 When is a pool "spent"? [A + NEW-B]
- **ICT.** Once traded through, its orders are filled, and the next untouched high or low is the one to watch. A wick is enough. The engine matches this: binary removal on a strict trade-through (1583-1589), kept by the decision history.
- Stops are a **band** beyond the level (Osler; penetration quantiles in 1.8), so a 1-tick poke spends only the nearest stops.
- **[NEW-B] What becomes the next liquidity:**
  - (a) **The sweep wick itself.** A fresh extreme carries stops at once: 60.8% of REJECT wicks are re-taken within 5 bars, but only 38% ever become pivLen-5 pivots, so the engine never offers the rest (`orderflow_micro` T6, proposal OF-1).
  - (b) **The opposite side of a range after one side is taken is *less* likely than geometry**, by about 10-25% relative (`session_stats` §2.4). ICT's "one side taken → the other is the draw" is therefore contradicted.

### 1.14 How ICT chooses the draw on liquidity (DOL) [A + NEW-B]
1. Top-down: weekly → daily → 4H/1H ("start on the daily chart", Ep. 14). Name the HTF draw, then trade the legs.
2. The draw is the unswept obvious pool or unfilled imbalance in the direction the HTF delivers: "Algos reach for liquidity or to fill imbalances" (Ep. 14).
3. Premium/discount and IRL/ERL phase decide retracement vs expansion (both null on data: 1.4, 1.5).
4. Time: raids in killzones (London 2-5 am NY, NY 7-10 am); no trades 12-1 pm.
5. "If it can go either way, you will regret it" (Ep. 8).

**[NEW-B] What the data says about "which side first".**
- The parameter-free race `P(up first) = (C − L)/(H − L)` (gambler's ruin) is right 70-81% for previous-candle extremes on 17 dataset/reference pairs (`bias_dol`).
- The engine's `D` scores 0.49-0.54 out of sample (`ict_struct`).
- Choosing the side by structure instead of geometry costs 4-10 pp of which-side-first accuracy (`bias_dol` §2.7).
- ICT's top-down narrative adds nothing measurable beyond the race the engine already implements (`f_race` / `f_raceH`, 447-482).

### 1.15 Daily bias from the previous day's range (community codification) [A, evidence CORRECTED]
- Let `H2/L2` be day t−2 and `H1/L1/C1` be day t−1.
  - Bullish if `C1 > H2`, or if `L1 < L2 and C1 > L2` (swept and closed back inside). Draw = H1.
  - Bearish mirrors.
  - Otherwise neutral; an outside day should be neutral unless the close is beyond.
- **Evidence:** right 69-76%, but the shuffle null scores 68-76% (−2.2 to +1.9 pp, 13 datasets, `bias_dol` §2.2). A hard rule (64-73%) is *worse* than geometry.
- A's E9 (edgeful YM: PDH break → green session 67 / 81%) is real but **all geometry**.

### 1.16 [NEW-B] Tests (approaches without a take)
- **Engine.** A test is a bar within 0.30 ATR that does not trade through, at least 3 bars apart (650-658). Density rewards it with `0.35·min(tests, 6)` (682).
- **Evidence.**
  - High frequency: each prior bounce raises the next bounce probability (Garzarelli 2014, strong; decays in minutes to hours, Chung & Bellotti 2021).
  - Bars:
    - 1H, 1 test: +0.8 ± 0.9 pp; ≥ 3 tests: +2.4 ± 4.6 pp.
    - 5m, 1 test: +2.8 ± 1.2 pp; ≥ 3 tests: −2.4 ± 4.5 pp.
    - 1m (sibling): ≥ 3 tests −7.3 ± 3.6 pp.
  - **No monotone effect.** The engine's monotone reward is unsupported (SMC-3, OF-3 agree).

---

## 2. Evidence (numbers and sources)

### 2.1 A's evidence table, re-checked

| # | Claim | Source and sample | Result | Grade (direction) | B's check |
|---|---|---|---|---|---|
| E1 | Stops just beyond round numbers; take-profits at them | Osler, J. Finance 58(5) 2003 (FRBNY SR125); RBS, about 9,700 orders, 1999-2000 | TP 9.3% exactly at 00 (uniform ≈ 1%). Stop-buys 14.4% in 01-10 vs 7.4% in 90-99 (p = 0.029); stop-sells 10.0% in 90-99 vs 5.1% in 01-10. Bounces +4.6 pp at rounds | strong (supports the location claim) | A✓ via `academic_sr` S5 and `orderflow_micro` L1 (same numbers). A's "8.7% of all orders at 00" not re-verified |
| E2 | Crossing stop clusters accelerates price | Osler, JIMF 24(2) 2005 (FRBNY SR150); 9,655 orders, $55 bn | MVCR − MVRV (1/100 %): DEM 1.12 / 0.89 / 0.57 / 0.85 at 15m / 30m / 1h / 2h; JPY 1.30 / 1.34 / 1.26 / 2.35; GBP 0.77 / 0.80 / 0.27 / 0.35. Reversals at rounds 58-60% vs 55-57% arbitrary | strong | A✓ via `orderflow_micro` L2. **[CORRECTED]** A wrote "signs turn negative at 1-2 days". Actual 1-day values: DEM −5.23, GBP −2.60, **JPY +1.27**, i.e. mixed. A's "18.1% / 6.3% around 50" not re-verified |
| E3 | S/R = book depth | Kavajecz & Odders-White, RFS 17(4) 2004; NYSE SuperDOT | Support = "lowest bid reached at least twice". 84% of level/depth series cointegrated at 5%. S/R significant for 49-73% of stocks. Technical levels *locate* existing depth; no new clustering afterwards | strong (mechanism) | Consistent with `academic_sr` S4. PDF not re-fetched |
| E4 | Prior bounces raise the next bounce probability | Garzarelli et al., Sci. Rep. 4:4487 (2014); 9 LSE stocks, 2002 ticks | p(b \| b_prev) > 0.5 and rising at 45 / 60 / 90 s (p < 0.0001). Not significant at 180 s (p = 0.077 resistance, 0.318 support) | strong (HF only) | A✓ via `academic_sr` S2 (adds the 180-s p-values) |
| E5 | Same at 1 minute, with decay | Chung & Bellotti, arXiv 2101.07410 (2021) | EURUSD: a 1-bounce level decays to 0.5 at about a 350-minute window; a 4-bounce level at about 900 minutes. Brent: a 1-bounce level falls below 0.5 beyond about 300 minutes | moderate | A✓ via `academic_sr` S3 |
| E6 | Equal highs/lows taken more than single swings? | Open-source TradingView script "Equal Highs & Lows Odds" (8 markets, 1H, 2 years, distance-matched) | EQ taken 63-82% vs singles 68-76%; "equal" adds < 1 pp beyond distance | moderate (null) | Script not re-fetchable (tradingview blocked). **Conclusion independently replicated by B (§1.2, n 2,230 + 1,350 EQ samples) and `orderflow_micro` T3.** **[CORRECTED]** A also cites "reversal after the sweep 39-44%" as continuation evidence. That metric is not a race against a baseline and should not be used that way |
| E7 | Sweeps → continuation, not reversal | Mahadzva, SSRN 7430998 (2026), G10 FX walk-forward | 65 of 66 fold-selections favour continuation; CHoCH + FVG reversal "should be faded" | **weak** (unverified preprint) | **[CORRECTED grade]** Nobody in this project opened the paper; `skeptic` saw a vendor-blog summary only. Its direction is consistent with 3 large internal replications (§1.8), so the claim stands on those, not on E7 |
| E8 | SMC detectors predict returns | Tangirala, SSRN 7483658 (2026); 44 detectors from 2 open-source Pine scripts; 496 S&P 500 stocks, daily 2010-2026, 2.2 M events | None beats random; liquidity-sweep detectors 11-12 bp over 10 days, p ≥ 0.23; in-sample picks −31 bp OOS | moderate (null) | Not re-verified this session (quoted consistently by `smc_impl` and `ict_struct`) |
| E9 | PDH/PDL break → session direction | edgeful blog, YM, 6 months, NY session | PDH broken → green 67% (open→close) / 81% (close→close); PDL → red 62% / 66% | weak (descriptive) | **[CORRECTED]** `bias_dol` shows previous-candle outcomes are explained by geometry (§1.15). Vendor host unreachable |
| E10 | Lower high → next-day PDL visit | Barot, SSRN 7359378 (2026), 6 markets | Lift positive in all 6 markets but small; absent in 2024-25 on index futures; buying the tag has no edge | weak-moderate | Not re-verified |
| E11 | FVG reaction vs random | Barot, SSRN 7148099; about 40,000 FVGs | About 5 pp above a distance-matched random level; not tradeable | moderate | Consistent with Nordman edge ratio +3.7% (5m) / −0.2% (1h) (`skeptic` C6) |
| E12 | Killzone filter for sweeps | Backtrex (EURUSD + XAU H1, 2019-24) | Killzones 53.2% WR, PF 1.68 (1,247 trades) vs 24 h 47.1%, PF 1.21 (3,891) | weak (vendor) | Not re-verified |
| E13 | Sweep significance across TFs | Quantzee (600+ setups) | 60-70% of 5-minute sweeps not significant on 1H | weak | — |
| E14 | Order-book clustering at round prices | Lallouache & Abergel, arXiv 1307.5440 (EBS) | Limit orders keep clustering at old round grids; algos front-run by one tick | moderate | A✓ via `orderflow_micro` L7 |
| E15 | ICT definitions | ICT lectures 2017-2024 | Definitions only; no validation | none | Partly re-quoted in `ict_struct` |

### 2.2 [NEW-B] B's original tests

**Data.**
- 1H:
  - NQ, GC and EURUSD, 2024-26 (about 11-12k bars each; the clean sibling copies in `scratchpad/sim/data/`);
  - ES, RTY, YM, Mar 2025 - Apr 2026 (6.3k each);
  - BTC 2017-2025 (70k).
- 5m: ES, NQ, GC, RTY and YM, Jan-Apr 2026 (resampled from clean 1-minute files, about 14-17k bars each).
- Excluded: GC 1H from `amt_data` (corrupted) and CL 1H (roll jumps).

**Method (engine-faithful).**
- ATR(14) Wilder; pivLen-5 pivots (left strict, right ≥); eqTol 0.10 ATR merge; zone 0.20 ATR; tests within 0.30 ATR at least 3 bars apart.
- Strict trade-through for pools; touch for FVGs. Pools are ejected beyond 15 ATR.
- **Reach edge** = hit within 30 bars minus `S(d)`. `S(d)` is the share of all bars on that chart whose 30-bar excursion toward that side exceeds d ATR. Checkpoints every 5 bars, pools 0.25-4 ATR away.
- **Post-sweep race**: ±1 ATR from the sweep-bar close, 30 bars, decided only, minus the chart's unconditional P(same direction first).
- **IRL/ERL race**: see §1.4.
- Standard errors are cluster-robust over 60-100-bar blocks per dataset.

| # | Claim tested | Result (1H, 7 datasets / 5m, 5 datasets) | Grade (direction) |
|---|---|---|---|
| B1 | Pools are drawn to more than distance implies | +0.1 ± 0.4 (n 52,762) / +0.8 ± 0.6 (n 30,887) | moderate (null) |
| B2 | EQ / primed / RH pools reach more | See §1.2: all within noise; priming flips sign | moderate (null) |
| B3 | Tests raise or lower reach | 1 test +0.8 ± 0.9 / +2.8 ± 1.2; ≥ 3 tests +2.4 ± 4.6 / −2.4 ± 4.5 | moderate (null) |
| B4 | Prominent swings reach more | 1H high vs low tercile −1.4 vs +1.7 (−3.1 pp, about 3σ); 5m +1.1 vs +0.5 | weak (contradicts at 1H) |
| B5 | Opposing untouched FVGs in the path (ICT high-resistance) | 1 FVG −2.8 ± 0.8 / −2.1 ± 1.0; robust to trend; 11 of 12 datasets negative | moderate (supports) |
| B6 | Same-side intermediate pools | See §1.6: sign differs by market and timeframe | moderate (heterogeneous) |
| B7 | Sweep → reversal (REJECT) | REJECT +1.5 ± 0.7 / +0.6 ± 0.9 continuation; all sweeps +1.1 ± 0.5 / −0.2 ± 0.7 | strong with siblings (contradicts) |
| B8 | P/D-conditioned turtle soup | Reversal side continues more: +1.7 ± 1.4 / +5.1 ± 1.9 | moderate (contradicts) |
| B9 | IRL↔ERL alternation | +1.8 / −2.3 pp after liquidity taken; −0.9 / −0.7 after IRL tag | weak (null, inconsistent) |
| B10 | Stop-run depth | REJECT q50 0.28 / 0.23, q80 0.64 / 0.51 ATR | moderate (replication) |
| B11 | Sibling 1H crowding prior | Reproduced only with the corrupted GC 1H file (−31.5 ± 4.1 at nIn ≥ 3); clean sets −8.6 to +8.0 | moderate (correction) |

### 2.3 Sibling replications this report relies on (all `study/*.md`)

| # | Finding | Source |
|---|---|---|
| X1 | Daily-bias close rule = geometry (−2.2 to +1.9 pp vs shuffle, 13 datasets). Turtle Soup never above geometry. CRT target reached first only 39-48% of decided cases, the same as the null | `bias_dol` §2.2-2.3 |
| X2 | REJECT → continuation 52.6% (n 1,402). HOLD against HTF → 56% reversal (n 381). MSS reversal 45.6% / 50.5%. Race geometry within 2 pp | `ict_struct` §2.2 |
| X3 | ±1 ATR race 0.497-0.510 after hold/reject (5m / 15m / 1h) | `skeptic` C4 |
| X4 | Sweep anatomy and symmetric burst (T1). Pool-size features null (T3). Round numbers not magnets; wick stops short −4.2 pp (T2, T2d). 61% of reject wicks re-taken in 5 bars (T6) | `orderflow_micro` §2.2 |
| X5 | 1m: tests ≥ 3 −7.3 ± 3.6 pp; stale pools > 12 h −7.5 ± 1.1; crowding −1.5 / −3.5 / −6.1; cascade +1.1 pp hold, +5.1 for 4-12-h-old pools | `academic_sr` §2.3-2.5 |
| X6 | Once one side of a day / week / NY-AM range is taken, the other side is about 10-25% less likely than geometry | `session_stats` §2.4 |

### 2.4 Net reading for the forecasting problem
- **Where.** The obvious unswept pools are where stops are (E1-E3). That makes them the right *candidate set*, but no ICT label makes one pool more reachable than its distance implies, except for opposing imbalances in the path (−2 to −3 pp each).
- **When.** Cascades last minutes to hours, not days (E2, X5). The post-sweep burst is symmetric for 3-10 bars (X4).
- **What next.** No reversal edge after a sweep. A small, market-specific continuation lean. Failed breakout only when a HOLD runs against the HTF bias. ICT's P/D, IRL/ERL and daily-bias selectors do not beat geometry.
- **How likely.** First-passage geometry (`f_pot`, `f_raceH`, the empirical surface) is accurate to within a few pp in every test (control excess −0.3 to −0.1 pp in B9). The ICT layer should be a learned, bounded correction, displayed honestly.

---

## 3. Engine gap analysis (line refs to `baseline_v2.pine`)

| Concept | Status | Where | What the engine does / what differs |
|---|---|---|---|
| BSL/SSL from swings | present | 1753-1776; `touched` 623-624 | pivLen 5, zone 0.20 ATR (93), strict trade-through. Matches ICT and the decision history **[A✓]** |
| Relative equal highs/lows | **partial (asymmetric) [CORRECTED]** | `f_mergeAt` 1111-1131; called at 1758 / 1770; outer branch 1116-1126 | Only "left ≥ right" or exact pairs merge (step 3 sweeps the left pool before the right pivot confirms). Right-higher pairs become a raid event plus a new single pool. `EQx2` tags and the EQ feature are one-sided (§1.2). ICT-11 |
| EQ density weight | **wrong (magnitude) [CORRECTED]** | 682 (`0.9·eqCount`) | EQ adds nothing to reach (B2, E6). Should be neutral and learned (ICT-10 / OF-3) |
| Priming | missing (implicitly the only EQ case) | 1114-1116 | No flag. Null evidence. Feature bit only (ICT-1) |
| STH/ITH/LTH, prominence | partial | `f_tierW` 506-516; `prom` 1757 / 1769; density 682 (`0.8·min(1, prom/3)`) | Prominence lowers 1H reach (B4) but enlarges the post-take run (X4). The density reward is unsupported for reach. A's ICT-8 is dropped |
| PDH/PDL, PWH/PWL, sessions | present | 945-961, 1790-1809, registry re-entry 1824-1852 | Good. **[NEW-B]** Registry levels in range but not yet re-entered (re-entry only when `regNew or bar_index % 5 == 0`, 1825) are removed silently at step 4 (1592-1596). No raid event and no ghost for up to 4 bars. Minor |
| Stack: inner vs outermost | **wrong (fixed magnitude) [CORRECTED]** | `f_stackSide` 1230-1251; inner ×0.70 684-685; `+0.45·stack` 682 | Evidence is heterogeneous (§1.6). ×0.70 is far larger than any measured effect. Conceptually, the outer pool is ICT's "objective", never the "next" pool. ICT-10 |
| Low-hanging fruit vs objective | partial | proximity 661-667; HTF objective 1984-1989 | Both exist. With a neutral stack rule the DOL becomes the next pool and the objective stays as the optional `showObj` display |
| IRL/ERL classification and cycle | missing (correctly, for scoring) | `htfEQ` / `dayEQ` 967-968 are only anchors | Null evidence (B9). Display or ledger bit only, after ICTS-4 fixes the dealing range |
| Premium/discount in the draw | partial (display only) | 2324-2333 | Contradicted as a reversal condition (B8). Keep display-only |
| Sweep outcome → D (`liqEvt`) | **wrong [A✓, sharpened]** | 1580-1582; decay 1535; `wL` 157; D 1892-1894 | REJECT → −1 (reversal) is contradicted (B7, X2, X3). **[NEW-B]** Additional defects: (a) every pool hit on a bar adds `±tier`, so a wide bar through stacked pools moves `liqEvt` by up to the sum of their tiers, and D can flip on one bar (`dGate` 0.35); (b) a 1-tick relative-equal poke is a full REJECT; (c) the HOLD threshold `lv.top` = level + `zoneATR`·ATR (1762, 1774, 1848), so the display input "Liquidity Zone Depth" changes the draw vector. ICT-9 |
| Purge + MSS | missing | `f_structure` 708-782; `bosUp/bosDn` 1542-1547 | Reversal reads 45.6-50.5% (X2). Alert only, with measured odds (ICT-2) |
| Turtle soup (age, context) | partial | 1580-1582 | Age and context add nothing (X1, B8). No change beyond ICT-9 |
| Inducement | partial | `induceBar` 892-895 | Density feature; no IDM level. Fine |
| High/low-resistance run | **missing (supported) [CORRECTED]** | path term 1945-1947 (volume only) | Opposing untouched FVGs cost −2 to −3 pp each (B5). ICT-5 |
| Tests | **wrong (monotone reward)** | `track` 650-658; density 682 (`0.35·min(tests,6)`) | No monotone effect on bars (B3, X5). **[NEW-B]** Exact touches (`high == level`) are neither tests (`gap > 0`, 654) nor sweeps (strict, 624) |
| When a pool is spent | present (binary) | 1583-1589; 1592-1596 | Matches the decision history. The fresh sweep wick is not offered as a pool (OF-1) |
| Stop depth | partial | `zoneATR` 0.20 (93); invalidation buffer 0.10 ATR (1344) | 0.20 ≈ the median REJECT penetration (B10). q80 0.51-0.64 ATR → OF-2 / ICT-7. A deeper buffer buys win rate with R, not edge (`orderflow_micro` T4) |
| Round numbers | missing | none (grep) | Strong order-placement evidence (E1, E2, E14). Not magnets; wicks stop short (X4). ICT-3 → OF-4 version |
| Killzone timing | present | `f_kzAff` 597-602; 975-976 | Fixed affinities. KZ bit in ICT-1; SESS-3 learns them |
| ICT daily bias | missing (correctly) | D 1892-1894 | It is geometry (X1). Readout only (BIAS-3); ledger bit DBIAS |
| Which side first | partial | D 1891-1899; `f_race` / `f_raceH` 447-482 | Geometry is right 70-81%; D is 0.49-0.54. BIAS-1/2, ICTS-1/3 |
| Freshness / age | present (unsupported ramp) | 668-673 | Maturation ramp unsupported; stale pools at 1m reach less (X5) |
| Self-measurement | present (active DOL only) | ledger 2037-2045; `f_book` 1461-1499; `f_calMult` 1376-1382 | About 1 trial per H window. Per-feature learning needs the candidate ledger (ICT-1 on CAL-3) |
| Live sweep alert | present | 1504-1509, 2085, 2092 | Deliberately live. Bar-close outcome and odds missing (ICT-2) |

---

## 4. Proposals (best first; 9 total)

Pine v6 notes for every spec:
- **No bitwise operators.** Encode a feature set as an int and decode with `math.floor(mask / pow2.get(b)) % 2 == 1`, where `var array<int> pow2 = array.from(1, 2, 4, ..., 32768)`. The quotient is floored explicitly, because the docs do not guarantee integer division semantics for `/`.
- New state updates go inside the confirmed-bar ENGINE block (1518). New functions are declared before first use, and the globals they read before them.
- No new `request.security` calls.
- The decision history is kept: strict trade-through sweeps, draw-side-first selection, 2-bar challenger, 2× flip hysteresis.

Overlap map with sibling proposals:

| This report | Sibling proposals |
|---|---|
| ICT-9 | merges ICTS-2 and BIAS-4 |
| ICT-1 | uses CAL-3 / CAL-4's candidate ledger, not a second ledger |
| ICT-10 | amends ACAD-1; aligns with OF-3, SMC-3, SKEP-6 |
| ICT-3 | adopts OF-4 |
| ICT-7 | adopts OF-2 |
| ICT-4 | depends on ICTS-4 |

### ICT-9 (P1, S) · Fix the raid → draw mapping now: neutral REJECT, HTF-conditioned HOLD, one event per bar per side, micro-pokes ignored [NEW-B; merges ICTS-2 / BIAS-4]

**Why.**
- `liqEvt` (1580-1582) feeds 30% of D (`wL`, 157), and D drives the draw pillar (weight 30), the ×0.50 counter-draw penalty and side selection.
- Its REJECT = reversal sign is contradicted (B7: +1.5 ± 0.7 pp *continuation*, n 5,899; X2; X3).
- Stacked-pool hits sum, 1-tick pokes count, and the HOLD threshold follows a display input. These are plausible sources of the "targets jump around" complaint.

**Spec.**
- Input (G_FLOW):
  ```pine
  float holdATR = input.float(0.20, "Raid Hold Distance (ATR)", minval = 0.0, step = 0.05, group = G_FLOW,
    tooltip = "A raid whose bar closes this far beyond the level counts as HOLD.")
  ```
- In the ENGINE block, just before the pool loop (1559): `float evB = 0.0` and `float evS = 0.0`.
- Replace 1580-1582 with:
  ```pine
  if hit and lv.isLiquidity()
      float pen   = (lv.side == 1 ? high - lv.price : lv.price - low) / atr
      bool  back  = lv.side == 1 ? close < lv.price : close > lv.price
      bool  hold  = lv.side == 1 ? close > lv.price + holdATR * atr : close < lv.price - holdATR * atr
      bool  micro = back and pen <= eqTol
      float e     = 0.0
      if hold and not micro
          e := htfBias == lv.side ? 1.0 : htfBias == -lv.side ? -0.5 : 0.5
      float sv = lv.side * e * lv.tier()
      if lv.side == 1
          evB := math.abs(sv) > math.abs(evB) ? sv : evB
      else
          evS := math.abs(sv) > math.abs(evS) ? sv : evS
  ```
- After the loop (after 1589): `liqEvt := f_clamp(liqEvt + evB + evS, -1.0, 1.0)`.
- Behaviour:
  - REJECT and NEUTRAL add 0.
  - HOLD with the HTF bias: +1 toward the raided side. HOLD against: −0.5 (failed-breakout lean). HOLD with a neutral HTF: +0.5.
  - At most one event per side per bar, using the strongest tier.
- Evidence for the values: HOLD with trend +2.3 ± 1.1 pp and against −2.3 ± 1.6 pp (B, 1H); with 53.2% / against 56% reversal (X2). 5m is weaker (HOLD −1.5 / −1.4).
- **Later:** ICT-2 replaces these static values with per-chart learned ones. ICTS-1 scales `wL` by D's measured skill.

**Risk.** D reacts less to raids, so draw flips are rarer. That is intended, and it is measurable with ICTS-1's skill readout.

**Evidence:** strong (no reversal edge after REJECT, replicated) / moderate (HOLD alignment). **Effort:** S.

### ICT-1 (P1, M) · ICT feature bits on the candidate (shadow) ledger: measure every ICT claim on this chart [A, revised; built on CAL-3/CAL-4]

**Why.**
- Every ICT effect measured here is either ≈ 0 on average or **changes sign by market or timeframe**: stacking (NQ −8.5 vs BTC +4.9 pp), sweep outcome (GC +6.1 vs ES −4.6), priming (1H vs 5m).
- Fixed weights are therefore wrong somewhere for certain. A per-chart, evidence-gated lift is the only defensible design, and it shows the trader which ICT claims hold on their symbol.
- The current ledger grades about 1 trial per H window (active DOL only), and `f_calMult` is 4 families with no significance gate (`calib_ml` shows it is mostly noise).

**Spec.**
- Build on CAL-3's candidate ledger: one `Probe` per pool level per H-bar window, graded against `f_potBase` (1314-1322).
- Inputs (G_ACC): `useFeat` (true), `featN0` (int 60, shrinkage), `featB` (float 0.15, per-feature bound), `featZ` (float 2.0, evidence gate).
- `type Probe { int lvId; int side; bool liq; float edge; int bar0; float pBase; int mask }`, declared after `Trial` (396). Add `int lastProbe = -100000` to `Level` (317-348).
- State: cap 128 open probes (at most one per live level).

  | Array | Size | Holds |
  |---|---|---|
  | `fN`, `fK` | NF + 1 | probes and hits per bit; index NF = all probes |
  | `fE` | NF + 1 | Σ pBase per bit |
  | `fB0`, `fB1`, `fB2` | NF + 1 | per-bit block-cluster residual accumulators (current block id, open-block Σ(y − pBase), Σ closed-block residual²; same pattern as `cluSt`, 1077 / 1464-1469) |

- Feature bits, NF = 16, set at snapshot from the Level plus engine state:

  | Bit | Name | Rule | Prior evidence |
  |---|---|---|---|
  | 0 | EQ | `eqCount > 0` | null (B2) |
  | 1 | PRIMED | last merge inside the stored price by > 0.02 ATR (set in `f_mergeAt` when `countEq and not outer and not samePx`) | null |
  | 2 | RH | right-beyond relative equal (ICT-11) | null |
  | 3 | TESTED | `tests >= 1` | null (B3) |
  | 4 | STACKED | `stack > 0` (outermost of a stack) | heterogeneous (§1.6) |
  | 5 | INNER | `inner` | heterogeneous |
  | 6 | OPP | ≥ 1 opposing untouched FVG in the path (ICT-5) | −2 to −3 pp (B5) |
  | 7 | PROM | `prom >= 1.5` | −3 pp at 1H (B4) |
  | 8 | KEY | `src >= 6` | SESS-3 |
  | 9 | SESSION | `src` 3-5 | SESS-3 |
  | 10 | MTF | `src` 1-2 | — |
  | 11 | DRAW | `side == dirSide` | 0.49-0.54 (X2) |
  | 12 | KZ | `f_kzAff(kz, src) > 1` | weak |
  | 13 | RN | target within 0.35 ATR inside a round (ICT-3 / OF-4) | — |
  | 14 | ERL | beyond the leg's weak extreme ± 0.1 ATR (ICT-4) | null (B9) |
  | 15 | DBIAS | key level on the daily-bias side (`bias_dol` BIAS-3 state) | geometry (X1) |

- **Snapshot** (step 17, after `lv.evaluate` at 1948, `inCalc` and past `warmup`). For each `lv` with `bar_index - lv.lastProbe >= H` and `0 < dist/atr <= maxATR`: push a Probe and set `lv.lastProbe := bar_index`. **Grade every candidate regardless of score**, so there is no selection feedback.
- **Grading** (new step 2b, after 1557):
  - `hit = liq ? (side == 1 ? high > edge : low < edge) : (side == 1 ? high >= edge : low <= edge)`.
  - On a hit, or at `bar_index - bar0 >= H`, book `y`. For each set bit and for NF: `fN += 1`, `fK += y`, `fE += pBase`, and the block residual accumulators. Remove the probe.
- **Lift with gates:**
  - `lift_b = ((fK_b + 2)/(fE_b + 2)) / ((fK_NF + 2)/(fE_NF + 2))`;
  - `z_b = (fK_b − fE_b) / sqrt(Σ closed-block residual²_b)`;
  - `w = fN_b / (fN_b + featN0)`.
  - `m_b = (abs(z_b) >= featZ and fN_b >= 100) ? f_clamp(1 + w*(lift_b − 1), 1 − featB, 1 + featB) : 1.0`.
- **Apply** in the multiplier loop (1940-1947): `lv.mult *= f_clamp(Π_{b ∈ mask} m_b, 0.80, 1.25)`. Every bit starts **neutral**, which is the evidence default.
- **UX** (Terminal, Accuracy = Full): an "ICT CLAIMS · this chart" block, one row per bit, e.g. `OPP ×0.95 (n 812, z −2.6) ✓` or `EQ ×1.00 (n 214, z 0.3) ~`. A "SELECTION EDGE" row: DOL hit/base ÷ candidate hit/base.
- **Cost.** About one new probe per bar (40 levels / H); grading ≤ 128 checks per bar; booking O(NF) per resolved probe. Negligible against the loop budget.

**Risk.**
- Probes on different levels share one price path. That is handled by the block-cluster z-gate and the shrinkage.
- Multiple comparisons across 16 bits: the gate |z| ≥ 2 plus bounds limits the damage (SKEP-9).
- Adds a UDT and arrays (memory is fine).

**Evidence:** moderate (method; motivated by B1-B9 heterogeneity). **Effort:** M.

### ICT-5 (P2, S) · Opposing undelivered imbalances in the path: ICT's high-resistance run [A, upgraded with B5 evidence]

**Why.** The one ICT path claim with consistent support: each untouched opposing FVG between price and the target costs −2 to −3 pp of reach beyond distance. It is negative in 11 of 12 datasets and robust within trend strata (B5). The engine's path term is volume-only (1945-1947).

**Spec.**
- Input (G_SCORE): `float oppK = input.float(0.05, "Opposing Imbalance Penalty", minval = 0.0, maxval = 0.2, step = 0.01, group = G_SCORE)`.
- In step 17, before the multiplier loop (1939), collect undelivered opposing FVG near edges once per bar. Bear FVGs are side +1 and bull FVGs side −1 by `f_newLevel` (1085):
  ```pine
  array<float> oppUp = array.new<float>()   // bottoms of untouched bearish FVGs above price
  array<float> oppDn = array.new<float>()   // tops of untouched bullish FVGs below price
  for o in pool
      if o.fill == 0.0
          if o.kind == 3 and o.bottom > close
              oppUp.push(o.bottom)
          else if o.kind == 2 and o.top < close
              oppDn.push(o.top)
  ```
- Inside the multiplier loop, per `lv`:
  ```pine
  int   nOpp = 0
  float e    = lv.nearEdge()
  if lv.side == 1
      for b in oppUp
          if b < e
              nOpp += 1
  else
      for t in oppDn
          if t > e
              nOpp += 1
  lv.mult *= 1.0 - oppK * math.min(nOpp, 2)
  ```
- Strict `<` / `>` excludes a target FVG's own edge.
- Set the OPP bit (ICT-1) when `nOpp >= 1`. The ledger then confirms or reverses the default on this chart.
- Default ×0.95 per zone, floor ×0.90, matches −2.5 pp on a ~45% hit rate.

**Notes.**
- B's test counted all FVGs ≥ 0.15 ATR. The pool holds only quality-gated FVGs (`fvgQMin` 0.45). An option is to also count `fvgTrk` zones that have no touch since birth, which needs a `touched` flag on `Zone`.
- Order blocks were not tested, so they are not counted by default.
- Cost: O(pool × opposing zones), ≤ 40 × 10 per `inCalc` bar.

**Risk.** Some overlap with the counter-draw penalty, since opposing arrays are common in counter-trend paths; the effect survives within trend strata. The ledger bit guards it.

**Evidence:** moderate. **Effort:** S.

### ICT-10 (P2, S) · Neutral stack and magnitude defaults: no fixed "outermost is the draw" [NEW-B; amends ACAD-1, aligns OF-3 / SMC-3 / SKEP-6]

**Why.**
- Inner ×0.70 (684-685) and `+0.45·stack`, `0.9·eqCount`, `0.35·min(tests, 6)` and `0.8·min(1, prom/3)` in density (682) are fixed rewards for claims that are null or change sign (B2-B4, B6, X5).
- The sibling ACAD-1 would instead install a strong crowding *penalty*, but its 1H numbers are contaminated (B11).
- Neutral defaults with learned bits (ICT-1) are the only setting that is not wrong on some charts. They also make the DOL the *next* pool, as ICT's low-hanging fruit says, while the outermost pool stays available as the objective (`showObj`, 1984-1989).

**Spec.**
- Input (G_SCORE): `string magModel = input.string("Evidence", "Pool Magnitude Model", options = ["Evidence", "ICT Classic"], group = G_SCORE)`. The current behaviour is the "ICT Classic" option.
- In `evaluate` (681-685), with `bool ev = magModel == "Evidence"`:
  ```pine
  float x = ev ? 1.2 * this.tier() + 0.4 * math.min(1.0, this.prom / 3.0)
               : 0.9 * this.eqCount + 0.45 * this.stack + 0.35 * math.min(this.tests, 6) + 0.8 * math.min(1.0, this.prom / 3.0) + 1.2 * this.tier()
  this.dens := 0.60 * (1.0 - math.exp(-x)) + 0.25 * this.coil + 0.15 * this.induce
  if this.inner and not ev
      this.mult *= 0.70
  ```
  Prominence keeps a halved term: it predicts run size (X4), but reach is negative at 1H (B4).
- `f_stackSide` stays (tags `STK`, bits STACKED / INNER).
- Tell ACAD-1 implementers to drop the hard-coded 1H crowding prior. Use the STACKED / INNER bits instead.

**Risk.**
- Visible change: inside a 0.75-ATR stack the nearer pool now often wins.
- The README line "the outermost pool in a stack is the draw" must change, or the ICT Classic option can be kept as the default if the user prefers the old look.

**Evidence:** moderate (heterogeneous / null). **Effort:** S.

### ICT-2 (P2, M) · Per-chart raid-outcome learner with control races; Purge + MSS alert with measured odds [A, revised; downgraded from P1]

**Why.**
- Average post-sweep effects are 0-2 pp (B7), so the static fix (ICT-9) captures most of the value.
- But market-specific signs are large (REJECT: GC +6.1, NQ +4.9, ES −4.6 pp, 1H). A learner turns them into D input on the charts where they exist, and gives the trader a measured answer to "what usually happens after a raid here".

**Spec.**
- Input (G_FLOW): `swLearn` (true), `swK` (float 1.0, race distance in ATR), `swWin` (int 8, MSS window).
- Type:
  ```pine
  type RaidRec
      int   side    // +1 BSL raided (continuation = up), -1 SSL; control records use +1
      int   cell    // cls*3 + align: cls 0 HOLD / 1 REJECT / 2 NEUTRAL; align 0 with HTF / 1 against / 2 none
                    // 9 = control, 10 = PURGE+MSS
      float up
      float dn
      int   bar0
      float base
      float mss
  ```
- State: `var array<RaidRec> raids` (cap 96); `var array<float> rN`, `rC`, `rP`, each `array.new<float>(11, 0.0)`.
- **Create:**
  - One record per side per bar, using the strongest-tier liquidity hit (same place as ICT-9).
  - `up = close + swK*atr`, `dn = close − swK*atr`.
  - `mss = side == 1 ? nz(obSwingL, exeRL) : nz(obSwingH, exeRH)`, captured now because `obSwing*` is reset on a BOS (1667 / 1710).
  - `base` = the current control estimate for that direction (below).
  - **Controls:** `if bar_index % 10 == 0`, push `cell = 9`.
- **Resolve** (step 2c, after 1557):
  - `upHit = high >= up`, `dnHit = low <= dn`.
  - Both on one bar → drop. Either → `cont = side == 1 ? upHit : dnHit` (controls: `cont = upHit`); book `rN[cell] += 1`, `rC[cell] += cont`, `rP[cell] += base`.
  - Expire after H bars without booking.
  - **Purge + MSS upgrade:** a REJECT record within `swWin` bars where `side == 1 ? close < mss and dispDn : close > mss and dispUp` sets `purgeEvt := true` and pushes a copy with `cell = 10`.
- **Estimate:**
  - `pCtl = (rC[9] + 10) / (rN[9] + 20)` gives P(up first) on this chart; `base = side == 1 ? pCtl : 1 − pCtl`.
  - Per cell: `lift_c = f_logit((rC[c] + 40*p̄_c) / (rN[c] + 40)) − f_logit(p̄_c)`, with `p̄_c = rP[c] / rN[c]`.
  - Learned event: `eL = f_clamp((f_sigm(f_logit(0.5) + lift_c) − 0.5) / 0.05, −1, 1)`; a 5 pp measured excess gives a full event.
  - Blend with ICT-9's static `e`: `e = (n_c·eL + 40·e_static) / (n_c + 40)`.
- **UX:**
  - Terminal row `RAIDS ▸ HOLD↑HTF cont 54% (n 61) · HOLD↓HTF 46% (22) · REJECT 51% (88) · base 50%`.
  - Bar-close alert when the active DOL is raided: `DOL raided · REJECT · on this chart continuation 51% (n 88) vs base 50%`.
  - `alertcondition(purgeEvt, "Liquidity Purge + MSS", ...)` with the measured cell-10 reversal rate in the `alert()` text.
- **Cost:** ≤ 96 records × O(1) per bar.

**Risk.** Sparse cells early on; the κ = 40 blend falls back to ICT-9. Alerts must say "on this chart, n = …".

**Evidence:** strong (no average edge) / moderate (market-specific signs). **Effort:** M.

### ICT-3 (P2, S) · Round-number layer: adopt OF-4 (amends A's ICT-3) [A, CORRECTED]

**Why.** Order placement around round numbers is the strongest evidence in the domain (E1, E2, E14). On bars it is geometry, not a draw:
- rounds are not magnets (X4 T2);
- sweep wicks **stop short** of a round just beyond a pool (−4.2 pp, about 3σ; T2d);
- once price is at a coarse round, it passes slightly more often (+3.3 pp).

A's ICT-3 confluence bonus and "extend the zone to R + 0.10 step" contradict T2d.

**Spec.** Exactly OF-4 (`orderflow_micro.md`):
- **Step.** The smallest {1, 5}×10^k at or above one daily ATR (`atrD = atrSlow·sqrt(86400/chartS)`), recomputed once per day with `timeframe.change("D")` evaluated at global scope.
- **Zone cap.** At 1762 / 1774 / 1848, `top := R` when `ph < R < top`; mirror for SSL.
- **Invalidation.** In `f_invalidation` (1343-1364), place it just beyond a round that lies within the stop band.
- **Confluence** only with `rnConf` (default off).
- **RN bit** for ICT-1.

**Evidence:** strong (placement) / moderate (bar geometry). **Effort:** S.

### ICT-11 (P3, S) · Relative-equal symmetry: a micro-poke followed by a right-beyond pivot is one EQ pool, not a raid [NEW-B]

**Why.** The engine merges only "left ≥ right" pairs (§1.2). A right print 1 tick above the left is booked as a sweep: `liqEvt` (until ICT-9), a ghost, and the live alert if active. A fresh single pool loses the `EQx2` tag. ICT's "relative equal" is symmetric. Reach is the same either way (RH −1.6 ± 2.1 pp), so this is a correctness and labelling fix, plus a ledger bit.

**Spec.**
- State: `var array<float> msPx`, `var array<int> msKind`, `var array<int> msBar`, `var array<int> msEq` (cap 16).
- In step 3, on `hit and lv.isLiquidity()` with `micro` (ICT-9): push `(lv.price, lv.kind, bar_index, lv.eqCount)`. Drop entries older than `2*pivLen + 1` bars.
- In step 9, when a new chart pool is created (1761-1764 / 1773-1776):
  - scan `ms*` for the same kind with `0 < (kind == 0 ? ph − msPx : msPx − pl) <= eqPx`;
  - set `nh.eqCount := msEq + 1` and a new `Level` field `bool rh = true`;
  - remove the entry.
- The ghost and the live "DOL Target Swept" alert are unchanged: strict trade-through stays a sweep per the decision history.
- `tag()` shows `EQx2 ⇡` for RH pools. Bit RH in ICT-1.

**Risk.** Slightly more EQ tags; no score effect under ICT-10. **Evidence:** weak (null reach; logic fix). **Effort:** S.

### ICT-4 (P3, M) · IRL/ERL and premium/discount: delivery readout and ledger bits only, no multipliers [A, downgraded from P2]

**Why.** Traders think in this vocabulary, so the classification is worth showing. But the alternation and the P/D reversal condition failed on data (B8, B9). A's `kPhase` / `kPD` multipliers would inject noise or a wrong sign.

**Spec.**
- Requires ICTS-4 (`f_structure` returns the leg's `[protected, weak]` range).
- `f_isERL(lv)`: liquidity beyond the weak extreme ± 0.1 ATR; everything else is IRL.
- Phase state as in A: 1 = ERL taken, 2 = IRL tagged; expires after H bars.
- HUD and tooltip tag `ERL` / `IRL`.
- Terminal `DELIVERY ERL▲ taken 3 bars ago · on this chart IRL-first 52% vs geometry 51% (n 140)`, using ICT-1 bits ERL and PHASE.
- Defaults `kPhase = 0`, `kPD = 0` (advanced inputs).

**Evidence:** weak (null). **Effort:** M.

### ICT-7 (P3, S) · Stop depth from observed sweeps: adopt OF-2 [A, merged]

**Why.** Penetration quantiles are stable and chart-specific (B10: q50 0.23-0.28, q80 0.51-0.64 ATR). The fixed 0.20-ATR zone is about the median, and the 0.10-ATR invalidation buffer sits inside the stop band.

**Spec.** OF-2 (`orderflow_micro.md`):
- learned zone depth from REJECT penetrations (`array.percentile_linear_interpolation`, cap 300, n ≥ 30);
- sweep classes;
- an optional invalidation beyond q80.

`orderflow_micro` T4 shows deeper buffers change win rate and R, not expectancy, so the EV readout stays honest.

**Evidence:** moderate. **Effort:** S.

### Dropped or rejected (with reasons)

| Proposal | Reason |
|---|---|
| A's ICT-6 (daily bias into D) | The rule is geometry (X1). Kept only as the BIAS-3 readout and the DBIAS bit |
| A's ICT-8 (STH/ITH/LTH pools) | No evidence; prominence lowers 1H reach (B4); ITH is nearly automatic for pivLen-5 pools |
| Extending zones past round numbers (part of A's ICT-3) | Contradicted (T2d) |
| Turtle-soup age filter or P/D-conditioned reversal | Contradicted or null (X1, B8) |
| Trendline / phantom liquidity | No evidence; not unique |
| IDM levels | Overlap with inner pools; definitions disputed |
| SMT | Other domain |

---

## 5. Sources

**Peer-reviewed / academic** (A's citations; verification status in §2.1):
- Osler, C. (2003). Currency Orders and Exchange-Rate Dynamics. *J. Finance* 58(5):1791-1819 (FRBNY SR125). https://fraser.stlouisfed.org/files/docs/publications/frbnysr/frbny_sr125.pdf
- Osler, C. (2005). Stop-Loss Orders and Price Cascades in Currency Markets. *JIMF* 24(2) (FRBNY SR150). https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr150.pdf
- Osler, C. (2000). Support for Resistance. FRBNY EPR 6(2). https://www.newyorkfed.org/research/epr/00v06n2/0007osle (via `academic_sr`)
- Kavajecz, K. & Odders-White, E. (2004). Technical Analysis and Liquidity Provision. *RFS* 17(4):1043-1071. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=315660
- Garzarelli, F. et al. (2014). Memory effects in stock price dynamics. *Sci. Rep.* 4:4487. https://arxiv.org/abs/1110.5197
- Chung, K. & Bellotti, A. (2021). Evidence and Behaviour of Support and Resistance Levels. https://arxiv.org/abs/2101.07410
- Lallouache, M. & Abergel, F. (2013). Tick Size Reduction and Price Clustering in a FX Order Book. https://arxiv.org/abs/1307.5440
- George, T. & Hwang, C.-Y. (2004). The 52-Week High and Momentum Investing. *J. Finance* 59(5) (via `academic_sr` / `skeptic`).
- Brock, Lakonishok & LeBaron (1992), *J. Finance* 47(5); Sullivan, Timmermann & White (1999), *J. Finance* 54(5) (trading-range breaks and their decay; via `academic_sr`).

**Preprints / vendor** (capped grades):
- Mahadzva (2026), SSRN 7430998. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7430998
- Tangirala (2026), SSRN 7483658. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7483658
- Barot (2026), SSRN 7359378 and SSRN 7148099.
- "Equal Highs & Lows Odds" (open-source TradingView script). https://www.tradingview.com/script/NvqGg3bD-Nambou-Equal-Highs-Lows-Odds-Are-They-Really-Liquidity/
- edgeful previous-day range blog. https://www.edgeful.com/blog/posts/previous-days-range-trading-mistake
- Backtrex liquidity-sweep backtest. https://backtrex.com/en/blog/liquidity-sweep-strategy-backtest-results
- Quantzee pages (sweeps, SFP). https://quantzee.com/anatomy-of-a-liquidity-sweep-the-four-bar-sequence-that-sepa/

**ICT primary material:**
- Quarter Sequence study pages. https://quartersequence.com/the-study/ict-liquidity/ · https://quartersequence.com/the-study/ict-market-structure/
- ICT 2022 Mentorship notes. https://www.forexfactory.com/attachment/file/4435106?d=1681044827
- Turtle soup rules (Connors & Raschke, *Street Smarts*, 1995). https://proea.app/en/blog/turtle-soup
- TradingFinder IRL/ERL. https://tradingfinder.com/education/forex/ict-internal-and-external-range-liquidity
- R2F 2022 model. https://www.r2ftrading.com/learn/ict-2022-model-explained
- LuxAlgo concept pages. https://www.luxalgo.com/library/concept/equal-highs-lows-as-liquidity/

**Sibling studies used** (all in `brief/study/`): `academic_sr.md` (S1-S28, §2.3-2.5), `orderflow_micro.md` (L1-L8, T1-T6, OF-1/2/3/4), `bias_dol.md` (§2.1-2.7, BIAS-1..4), `ict_struct.md` (§2.2, ICTS-1..7), `skeptic.md` (C4, C15, SKEP-6/9), `session_stats.md` (§2.4, SESS-3), `calib_ml.md` (CAL-1/3/4), `smc_impl.md` (SMC-3).

**Pine v6 docs used:**
- `docsrc/jabez4jc_pinescriptv6/language/operators.md`: no bitwise operator class.
- `docsrc/mmmy_pine-script-doc-v6/pine-script-reference/Operators.md:287`: integer remainder semantics.
- `reference/array.md:1085`: `array.percentile_linear_interpolation`.

---

## Appendix A. Reproduction (B's tests)

Scripts are in `brief/study/ict_liq_tools/`: `data.py` (loaders, ATR) and `ictliq.py` (T1-T4).

```
cd brief/study/ict_liq_tools
python3 -I ictliq.py "$PWD/data.py" NQ,GC,EU,ES,RTY,YM,BTC        > out_1h.txt
python3 -I ictliq.py "$PWD/data.py" ES5,NQ5,GC5,RTY5,YM5            > out_5m.txt
python3 -I ictliq.py "$PWD/data.py" ES,NQamt,RTY,YM,GCraw,CLraw     > out_cme1h_raw.txt   # contamination check
```

- `out_all_1h5m.txt` is the 9-dataset pooled run (1H + ES/NQ 5m).
- Data-quality check: `amt_data/cme/GC/GC_1h_*.csv` has 742 bars with |Δclose| > 1.5% and 279 jump-and-back bars (two contract months interleaved). `CL_1h` has 150 bars > 1.5% (rolls). Every 1-minute file has ≤ 1 jump-and-back.
- Limitations:
  - Checkpoints overlap; standard errors are block-clustered.
  - 1H covers 13-24 months per market (BTC 8 years). 5m covers one quarter.
  - The IRL/ERL proxy uses the nearest pool and the nearest untouched FVG, not ICT's discretionary leg.
  - Results describe pivLen-5 engine pools, not hand-drawn levels.
