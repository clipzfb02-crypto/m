# Wyckoff Method and Supply/Demand · final study (researcher A + researcher B, combined and corrected)

Domain: the Wyckoff method (trading ranges, accumulation/distribution schematics, PS/PSY, SC/BC, AR, ST, spring/shakeout, UT/UTAD, test, SOS/SOW, LPS/LPSY, JAC/BUEC, composite operator, cause and effect with point-and-figure counts, effort vs result) and supply/demand zone trading (rally-base-drop zones, departure strength, time at level, fresh vs tested). The question throughout: does any of it help predict **which liquidity price takes next, when, and how likely**, and how would it be detected in Pine v6?

Line numbers refer to `brief/baseline_v2.pine` (identical to `indicators/dol_engine.pine`). Sibling studies are cited by their **final** proposal ids: `ict_liq.final.md` (ICT-1, ICT-9, ICT-10), `ict_pd.final.md` (ICTPD-1), `ict_struct.final.md` (ICTS-1, ICTS-2), `bias_dol.final.md` (BIAS-1/2/4/7), `smc_impl.final.md` (SMC-2, SMC-3), `quant_regime.md` (REG-1..6), `orderflow_micro.md` (OF-3), `academic_sr.md` (S1-S18).

**Tags.** `[A✓]` A's claim re-checked and kept · `[CORRECTED]` A's claim changed · `[DOWNGRADED]` evidence grade lowered · `[NEW-B]` added by researcher B · `[B2]` added or fixed in B's second pass · `[SUPERSEDED]` covered by a sibling proposal, kept here only as a pointer · `[not re-fetched]` the source host was blocked for B, so the number is A's reading.

**Two B passes.** B's first pass (B1) wrote this file and ran `wyckoff_b_tools/`, but its run was cut off by the account usage limit before it returned. The second pass (B2) re-checked B1's draft against the engine, the sibling studies and the primary sources (thepatternsite.com and TradingView became reachable through Firecrawl in B2), and added new tests in `wyckoff_b2_tools/`. B2 changes are tagged `[B2]`. Three B1 "corrections" of A turned out wrong and are reverted: Bulkowski's busted-rectangle numbers (W4), A's partial rise/decline rates (W3, §1.6), and the claim that OF-3 keeps the coil and inducement terms (§4 WYK-1).

**Reproduction.**
- A's scripts: `study/wyckoff_tools/*.py` (S&P 500, NASDAQ, GOOG daily with volume; EURUSD 1H 2017-18 with tick volume; NQ, GC, EURUSD 1H 2024-26 without volume). Outputs `out_*.txt`.
- B's scripts (independent code, new data): `study/wyckoff_b_tools/`.
  - `wyckB.py dens|pivots|wyck|wyckloose|wyckbtc|climax|volvol`, `agedetail.py`, `agedetail_sim.py`, `climaxnull.py`. Run with `python3 -I <script> [section]`. Outputs `out_*.txt` next to them.
  - Data: CME futures 1H with real volume (ES, NQ, RTY, YM, CL; 2025-03 to 2026-04, about 4,500-6,300 bars each), CME 5m resampled from 1-minute bars with real volume (ES, NQ, GC, RTY, YM, CL; 2026-01 to 2026-04, about 13,900-16,800 bars each), BTC 1H 2017-25 (70,273 bars, no volume), plus A's daily files.
  - The CME GC 1H file mixes contract months (64 close-to-close jumps > 5 ATR, 7% zero-range bars), so B excluded it.
  - `wyckoff_b_tools/ext/` holds two cloned public repositories used for definitions and a vendor validation (MIT-licensed; nothing copied into the engine).
- **[B2] Second-pass scripts:** `study/wyckoff_b2_tools/`.
  - `climax_tod.py`: the 5m climax test against a time-of-day-stratified null. Output `out_climax_tod.txt`.
  - `sdzones.py`: Seiden-style supply/demand zones on the same 15 series. It tests reach, and first vs second touch reaction, by departure strength, base length and zone type. Output `out_sdzones.txt`.
  - Run with `python3 -I <script>`.
- **Network limits.**
  - B1: WebFetch could not resolve thepatternsite.com, wyckoffanalytics.com, arxiv.org or nber.org, and the Firecrawl scraper was out of credits. B1 verified through search-engine summaries, the Firecrawl paper index (arXiv full text) and GitHub clones.
  - B2: the Firecrawl scraper worked for thepatternsite.com (rectangles, partial rises and declines, busted rectangles, breakout volume, Study of Studies), wyckoffanalytics.com and three TradingView script pages, until the daily credits ran out. tradingwyckoff.com does not resolve in this session.
  - Numbers neither pass could re-read are tagged `[not re-fetched]`.

---

## 0. Executive summary

1. **Wyckoff range events do not tell which side is taken next beyond race geometry. Two independent implementations agree.** [A✓, replicated by B]
   - A (rolling frozen box, 7 datasets, 4 settings): after a **spring**, the opposite edge is taken before the spring low 12-37% of the time, against 16-26% from gambler's-ruin geometry. Excess over bar-shuffled nulls is −0.075 to +0.016 (SE about 0.04).
   - B (the *canonical* climax-anchored range: SC/BC → AR defines the box, as in Wyckoff's own schematic; 11 CME series plus BTC, 3 parameter sets): spring excess **+0.007 ± 0.032** (n 209), **+0.018 ± 0.027** (n 301), **+0.022 ± 0.040** (BTC, n 137). UTAD: −0.024 ± 0.038, −0.049 ± 0.032, +0.079 ± 0.044. SOS/SOW measured-move races change sign between settings.
   - "Spring → target the opposite side of the range" is not supported in either range definition, on daily, 1H or 5m bars.
2. **Wyckoff levels are reached at random-level rates** (range edges, spring/UT targets and extremes, the 50% automatic-rally level), A's magnet tests, edges −0.07 to +0.02. More touches on an edge do not make it a bigger magnet. [A✓]
3. **The engine's coil and inducement inputs carry no information, and inducement is a constant.** [A✓, replicated]
   - `indScore` ≥ 2/3 on **91-98%** of bars on 12 new series (A: 86-97% on 7). B's daily numbers match A's to three decimals, so the two implementations agree.
   - Coil at pivot birth: B finds −0.022 / −0.011 / −0.006 (low / mid / high coil, n 24,544). A found the opposite ordering (high coil slightly *worse*). The sign flips between studies, the spread is ≤ 1.6 pp, and `quant_regime` found no effect on 23 series. De-saturated forms (500-bar coil percentile, real 20-bar sweeps) are flat in both studies.
   - **Bug:** registry re-entries (1848) and HTF FVGs (1862) take the *current* bar's coil and inducement, not the birth values. [A✓]
4. **Pool age: [CORRECTED]** A wrote "age has no effect on reach". B's finer split on five data groups shows small but consistent ends:
   - pools 5-10 bars old are reached 0.6-1.9 pp *less* than a random level at the same distance (4 of 5 groups; [B2] B1 wrote "3 of 4");
   - intraday pools older than about 300-500 bars are reached 3-8 pp less (CME 5m, CME 1H, A's 1H set);
   - middle ages are inconsistent (+4.7 pp in one group, −1.4 pp in another).
   - The engine's ramp therefore points the right way at both ends but is **about 10-15× too strong** for young pools: about 4 score points (= `hyst`), which is worth roughly 15 pp of reach on the proximity scale, for a measured ~1 pp. The slow decay is consistent with the data. WYK-2 keeps the decay, drops the ramp, and lets the ledger learn the young/old effects.
5. **Climax bars: a real but timeframe-scoped partial reversal; volume does not matter.** [NEW-B]
   - Price-only selling climax on **CME 5m** (new 20-bar low, range ≥ 2 ATR, close in the upper half): the 50% retrace of the leg comes before the low is retaken **+6.6 ± 2.5 pp** more often than in bar-shuffled nulls. All 6 instruments are positive. Buying climax +4.1 ± 3.2 pp.
   - **[B2] It is not a time-of-day artefact.** Against a null that shuffles bars only within the same New York clock slot, which keeps the open/close volatility bursts, the selling-climax excess is still **+6.8 ± 2.5 pp** (buying climax +3.8 ± 3.2).
   - The effect sits in thin hours: overnight **+9.2 ± 3.1 pp** (n 231) and 08:30-09:30 ET +15 ± 9 pp (n 26). In regular hours it is −2 pp (n 102). That fits the liquidity-provision reading: short-term reversals pay most when liquidity is scarce (Nagel 2012; Grossman-Miller).
   - On **1H** it is gone (CME: −2.6 / +3.4 pp), and on **BTC 1H** it reverses into continuation (−3.5 ± 2.2 / −6.5 ± 2.8 pp). This matches the literature: drift bursts and 60-minute shocks partly revert within about an hour (Christensen-Oomen-Renò; Zawadowski et al.), and markets revert below a few hours but trend from hours to years (Safari & Schmidhuber 2025).
   - Splitting by relative volume (raw or time-of-day normalised) changes nothing. **Effort vs result adds no measurable information at 5m, 1H or daily** (A at 1H/daily, B at 5m with real futures volume). Relative volume also adds ≤ 3 pp of out-of-sample R² for next-30-bar ATR-scaled range at 1H, and nothing at 5m.
6. **Cause and effect is untested in its own form.** [A✓, CORRECTED detail] The measured move is reached at geometry rates; range duration and width do not predict extension (A). P&F *signal* rules were tested once (Anderson & Faff 2008, S&P futures: "mixed statistical significance", [B2]), but neither B pass found **any published test of P&F count targets**.
7. **Supply/demand odds enhancers have no quantitative support, and B2's own test finds none.** Online Trading Academy keeps its scoring proprietary. Arrays are reached at random-level rates (siblings). Departure size lowers fill (ICTPD-1).
   - **[B2] New test** (`sdzones.py`): Seiden-style zones (1-6 base candles, 1-3 bar departure ≥ 1.5 ATR) on 15 series, 10,019 zones with a valid reach test.
   - **Reach.** The proximal edge is revisited within 30 bars at random-level rates: −0.7 to +3.0 pp vs S(d). Departure strength and base length ("time at level") have no consistent sign across the four data groups.
   - **Reaction at the first touch** (+1 ATR bounce before the distal edge breaks, vs geometry): −0.6 to +2.2 pp excess over nulls. Fresh minus second touch is +0.0 to +3.1 pp, ≤ 2σ.
   - **Zone type.** Continuation zones (RBR/DBD) react better than reversal zones (DBR/RBD) in all four groups (+1.3 to +9.1 pp). That is the opposite of the school's claim that reversal zones are stronger, and it is a with-trend effect, not a zone effect.
   - Freshness therefore matters a little for *reaction* at most, never for reach, and S/R bounce memory points the other way (bounces rise with prior bounces).
8. **What this domain contributes to the engine.**
   - **Subtraction:** neutralise coil and inducement at their population means (so family balance is unchanged), fix the birth-value bug (WYK-1), and drop the young-pool freshness ramp (WYK-2).
   - **A learned, timeframe-scoped climax feature** for the shadow ledger (WYK-3).
   - **A Wyckoff range layer** for traders: canonical range box, Spring/UTAD/SOS/SOW labels and alerts with zero forecast weight, each showing its measured per-chart rate against geometry (WYK-4).
   - A's range-regime selection gate and regime-split ledger are **[SUPERSEDED]** by REG-3/REG-2. A's `liqEvt` change is **[SUPERSEDED]** by ICT-9. A's volume features are **[CORRECTED]** into the price-only climax feature.
9. **Grades.** Wyckoff schematic claims as forecasts: none to weak. Range/rectangle statistics: moderate (Bulkowski, no baseline), and strong only for "rectangle-conditioned return distributions differ in shape" (Lo-Mamaysky-Wang). Climax partial reversal: strong at ≤ 1 hour (literature) and moderate at 5m in B's data; none or continuation at 1H+. Supply/demand odds enhancers: none published; B2's null-controlled test is moderate evidence of *no* reach effect. Both researchers' null-controlled tests: moderate.
10. **[B2] Bulkowski re-read at the source.**
    - A's figures were right; B1's corrections of them are reverted.
      - Partial decline → up-breakout 80% (rectangle bottoms) and 91% (tops); partial rise → down-breakout 74% / 57%. These come from the partial rise and partial decline pages, 1989-2013, 5,959 patterns.
      - Busted rectangle tops: 51% bust; a single bust of a downward breakout rises 71% on average, against 51% for non-busted tops.
    - "Tall patterns outperform" (89% / 100% of pattern types) and "wide patterns outperform" (91% / 85%) are percentage moves without a volatility control. A tall pattern marks a volatile stock, so in ATR units the effect is what A measured: none (§2.5).
    - Breakout volume is not a consistent law even in Bulkowski's own tables. "After a high volume breakout, performance doesn't improve much but failures triple." Rectangle *bottoms* with upward breakouts do better on *light* volume.

---

## 1. Concepts: precise definitions and parameters

Notation: `A` = ATR(14) (the engine's `atr`; `atrE` = max(ATR14, ATR200) for range gates). `vr` = volume / SMA(volume, 20)[1]. "Taken" = strict trade-through, the engine's liquidity rule (`touched`, 623-624). All detection is on confirmed bars.

### 1.1 Trading range (TR), creek and ice, phases A-E [A✓]
- **Definition (Wyckoff Analytics, Pruden/Fraser school).** A TR is where "the previous trend has been halted and there is relative equilibrium between supply and demand". In accumulation it is bounded by the SC low (plus ST lows) and the AR high; mirror for distribution. "Creek" is the resistance of an accumulation range; "ice" is the support of a distribution range.
- **Phases.** A: stopping action (PS, SC, AR, ST). B: building the cause (multiple STs, upthrust-like actions). C: the test (spring, or a higher-low test in schematic #2). D: SOS/LPS; "During Phase D, the price will move at least to the top of the TR". E: markup. Re-accumulation ranges are shorter and smaller.
- **Two causal detectors.**
  1. **Rolling frozen box** (A's `wyck.tr_box`): at confirmed bar t, `hi = highest(high, N)[1]`, `lo = lowest(low, N)[1]`; qualify if `kmin·A ≤ hi − lo ≤ kmax·A` and each edge has ≥ 2 touches (bars within `tol·A`, ≥ 3 bars apart); freeze on the first qualifying bar. Parameters: N 20/30/50, kmin 1.5, kmax 6-8, tol 0.25. Seen elsewhere: FibAlgo lookback 50 with > 8 ATR filtered as a trend; trendcraft minRangeBars 20, tolerance 0.5 ATR; MQL5 article 22628 range 10-60 bars; Lo-Mamaysky-Wang rectangle = 5 alternating extrema, tops within 0.75% of their mean, bottoms within 0.75%.
  2. **[NEW-B] Climax-anchored range** (the canonical Wyckoff construction; parameters learned from the MIT-licensed `tianyaphoto/wyckoff` detector, all in ATR units, no code copied):
     - *Selling climax* at bar i: prior downtrend (`close < SMA50`), new 20-bar low (`low < lowest(low,20)[1]`), range ≥ **2.0·A**, `vr` ≥ **2.5** (price-only variant when the symbol has no volume).
     - *Climax extension:* new lows within 10 bars and before any rebound move the climax extreme.
     - *AR:* a rebound of ≥ **2.0·A** from the climax extreme within **10** bars; confirmed when a close is ≥ **1.0·A** below the rebound high; abandon after **30** bars.
     - *Range:* [SC low, AR high], width **2-8·A**; "confirmed" after **15** bars.
     - *Failure:* **3** closes > **1.5·A** outside.
     - *Spring:* low below the range low by ≤ **1.5·A**, a close back inside within **3** bars; re-armed only after a close ≥ 1·A off the edge.
     - *SOS:* close > range high + **0.5·A** with `vr` ≥ **1.5**.
     - Mirror everything for distribution (BC, AR reaction, UTAD, SOW).
- **Edge cases.** The box must be frozen (a rolling Donchian box swallows springs). A spring does not end the range. Ranges taller than about 8 ATR are trends. Use a slow ATR for width gates. The climax-anchored detector needs volume for its classic form; without volume it degrades to a price-only climax (B ran both).
- **[B2] More edge-case rules from published detectors** (rules read, no code copied):
  - *Touch count.* Bulkowski's rectangle needs ≥ 3 touches on one boundary and ≥ 2 on the other, "using distinct peaks and valleys". That matches Lo-Mamaysky-Wang's 5 alternating extrema and is stricter than A's 2 + 2.
  - *Phase A extension* (WillyAlgoTrader "Wyckoff Range Engine"). Before the first ST, a swing beyond the AR edge extends the range ("AR+"); it is not an upthrust. A swing beyond the climax extreme extends the climax. If the extended height exceeds 8 ATR, the candidate is a trend and is dropped.
  - *ST.* A pivot inside the 30% of the range nearest the climax edge (SRFX: "upper or lower 30%"; Willy: u ≤ 0.30), at most 3 per range.
  - *Spring needs a prior ST.* This is a default option in Willy. Without it, Phase B shakeouts are labelled as springs.
  - *Reclaim deadline.* 3 bars (`tianyaphoto`, FibAlgo) to 8 bars (Willy).
  - *Climax-volume breaks.* A break of the edge on climax volume is a failed pattern, not a spring (SRFX). That is the opposite of the "#1 / terminal shakeout" reading (§1.4).
  - *Range lifetime* 200-400 bars; invalidation when price runs 5 ATR beyond the edge (SRFX); 15-bar cooldown after a reset.
- **Use for DOL (practitioner claim).** The two edges are the obvious pools; Phase D means the opposite edge is the target once the test is done.

### 1.2 PS/PSY, selling/buying climax (SC/BC), automatic rally/reaction (AR) [A✓, extended]
- **SC.** "Widening spread and selling pressure usually climaxes, as heavy or panicky selling by the public is being absorbed … Often price will close well off the low." BC mirrors it. **AR:** the rebound after selling pressure dries up; its high defines the TR top. **PS:** the first substantial buying after a prolonged decline.
- **Bar-level algorithm** (implementations converge; parameters vary):
  - A: new 20-bar low, range ≥ 1.5·A[1], `vr` ≥ 2, close location `(C−L)/(H−L)` ≥ 0.5, after a ≥ 4·A down-leg; AR target = 50% retracement of the leg.
  - `tianyaphoto`: range ≥ 2.0·A, `vr` ≥ 2.5, new 20-bar extreme, prior trend by SMA50.
  - StockSharp "Volume Climax Reversal" uses volume > 2× SMA20.
  - [B2] FibAlgo "Wyckoff Selling & Buying Climax": prior trend by linear-regression slope; volume ≥ 2.0× average; spread ≥ 1.5× ATR; close position < 0.5 (BC) or an upper wick > 50% of the range. AR = within 10 bars, a bar closing near its extreme with spread ≥ 1.0× ATR and volume ≥ 0.8× average.
  - [B2] WillyAlgoTrader scores the whole climax *run*, not one bar: mean and peak effort, run length in ATR and speed. Gates: peak effort ≥ 2× baseline, score ≥ 60. AR = a retrace of ≥ 0.5 of the run, range height 3-8 ATR, confirmed within 60 bars.
  - **[NEW-B] Price-only climax** used in B's tests: new 20-bar low, range ≥ 2·A[1], close in the upper half. Volume was then tested as a split, not a gate.
- **Microstructure form.** A drift burst / extreme 60-minute move is the minute-scale analogue of an SC/BC; its partial reversal is the analogue of the AR (§2.1 W8-W9).

### 1.3 Secondary test (ST) and tests in general [A✓]
- **ST.** Price revisits the SC area on "significantly diminished" volume and spread, "generally stopping at or above the same price level as the SC". "If the ST goes lower than that of the SC, one can anticipate either new lows or prolonged consolidation."
- **Engine "test"** (650-656): a bar within `testATR`·A (0.30) of a pool that does not take it, ≥ 3 bars after the previous test.
- **[NEW-B] ST in data.** After a confirmed AR on CME 5m, the climax extreme is traded *through* before the AR extreme ~5 pp more often than geometry (§2.7). The classic "ST holds above the SC" reading is contradicted there; the ICT reading "the stops under the SC are a draw" is mildly supported on 5m, not on 1H or BTC.

### 1.4 Spring / shakeout and upthrust / UTAD [A✓]
- **Spring.** "A price move below the support level of the TR … that quickly reverses and moves back into the TR … a bear trap." Not required (schematic #2 has none). **UT** mirrors it; **UTAD** is an upthrust after distribution, late in the range (FibAlgo: a UT exceeding a previous UT high).
- **Types** (Evans via Fraser and Villahermosa): #1 / terminal shakeout ("wholesale breakdowns below support on volume that is much larger than that of prior downswings"); #2 deeper with some volume expansion; #3 "a modest penetration of support … accompanied by volume that is relatively light". Villahermosa: "volume is secondary information".
- **Algorithm.** Frozen box: `low < lo`, `lo < close < hi`, depth `(lo − low)/A ≤ 1.5`; or recovery within 3 bars (FibAlgo, `tianyaphoto`). Volume class by `vr`: ≤ 0.8 → #3, 0.8-1.5 → #2, > 1.5 → #1/SO (fis_wse caps spring volume at 0.7× MA; `tianyaphoto` labels < 1.0 "low volume").
- **[B2] The type numbers are inverted between sources.** Evans/Pruden/Fraser: #1 = heavy-volume terminal shakeout, #3 = light. FibAlgo's "Spring & Upthrust": "Type 1 (Low Volume) … Type 3 / Shakeout (High Volume)". A label "Spring #1" therefore means opposite things to different users. Label by words instead: `SPRING · light vol`, `SPRING · heavy vol (shakeout)`.
- **[B2] Other published spring rules.**
  - Wyckoff Analytics' algorithm note: a spring bar must not close at its low; tails show demand; reference low = the lowest low of the last 15 bars (try 20-25).
  - WillyAlgoTrader spring score: 40% shallowness (depth ≤ 1.5 ATR), 40% less effort than the climax run, 20% reclaim speed (≤ 10 bars). Reclaim deadline 8 bars; a decisive break is 0.5 ATR.
  - None of these sources publishes a hit rate against a baseline. Willy's dashboard shows descriptive per-chart counts (Spring → SOS follow-through, SOS → target hit rate) with no geometry baseline, which WYK-4 adds.
- **Close-based failed breakout** (Bulkowski "bust"): a **close** beyond the edge, then a close back inside within 3 bars.
- **[NEW-B] Related rule with its own tests: Turtle Soup** (Raschke & Connors, *Street Smarts*, 1995): a new 20-day low whose previous 20-day low is ≥ 4 sessions old, then a buy stop back above the old low. It is a spring without the range qualifier. `bias_dol.final.md` §2.3: excess over geometry −0.129 to +0.082, never reliably positive.
- **Mechanism (why springs are not systematic reversals).** Stop-loss orders cluster just beyond levels and take-profits at them (Osler 2003); crossing a stop cluster produces a cascade lasting 15 minutes to 2 hours (Osler 2005); S/R levels coincide with limit-order depth (Kavajecz & Odders-White 2004). A sweep releases stops in the sweep direction, so continuation and reversal are both mechanically plausible. The data show neither dominates (§2.2, §2.6).

### 1.5 SOS/SOW, JAC/BUEC, LPS/LPSY [A✓]
- **SOS.** "A price advance on increasing spread and relatively higher volume", often after a spring. **JAC** = the SOS that breaks the creek; **BUEC/LPS** = the low-volume pullback to the broken creek. SOW/LPSY mirror it ("a decline below the midpoint of the TR after a UT or UTAD").
- **Algorithms.** A: within 10 bars of a spring, a close above the range midpoint before the spring low breaks. `tianyaphoto`: a close beyond the edge by ≥ 0.5·A with `vr` ≥ 1.5.
- **Use for DOL.** After a JAC the target becomes the next pool beyond the range; the LPS is an entry, not a target. The engine's BOS + OB (1542-1547, 1663-1748) is the SMC restatement.

### 1.6 Partial rise / partial decline [A✓; B1's correction reverted in B2]
- **Bulkowski.** "Looping chart patterns that appear at the end of broadening patterns and rectangles"; a partial decline "predict[s] an immediate upward breakout but [is] not always correct".
- **[B2] Both sets of numbers exist; A's were right.**
  - The partial rises and partial declines pages (bull markets, 3/1989-11/2013, 5,959 patterns compared): partial decline → up-breakout **80%** (rectangle bottoms) and **91%** (tops); partial rise → down-breakout **74%** (bottoms) and **57%** (tops). Across broadening patterns the rates run from 14% to 87%.
  - The rectangle pages separately give: partial rise → down **75%** (tops and bottoms); partial decline → up **79%** (tops), **77%** (bottoms).
  - B1 had marked A's 57% "not found"; it is on the partial rises page.
- **Algorithm** (A): a 3-bar fractal low inside the box above `lo + 0.33·(hi − lo)`, the top touched in the previous N/3 bars; race top vs bottom.

### 1.7 Composite operator [A✓]
"All the fluctuations in the market … should be studied as if they were the result of one man's operations." An interpretive stance; unfalsifiable; nothing to detect beyond 1.1-1.6.

### 1.8 Cause and effect: P&F horizontal count, measured move [A✓, CORRECTED]
- **Law.** "The horizontal P&F count within a trading range represents the cause, while the subsequent price movement represents the effect."
- **Count.** Count columns across the TR from the LPS (or spring) leftward by whole phases; target = count × box × reversal (usually 3) added to the low or LPS. StockCharts: counts are "rough estimates … no guarantee"; some practitioners use two-thirds of the count for bearish objectives (Cohen).
- **Measured move** (Bulkowski rectangles): target = breakout edge ± height; met 79%/55% (bottoms, up/down) and 78%/54% (tops) in bull markets, with no random baseline. [A✓ via search summary]
- **[CORRECTED]** A wrote that P&F "has no published test at all". P&F *signal rules* were tested.
  - Anderson & Faff (2008, *IRFA* 17:198-217) built P&F charts from tick data for S&P 500 futures 1990-98 and tested eight pre-defined rules with a bootstrap. [B2] The published abstract reports "mixed statistical significance with some rules proving significant while many others were not". B1's "profits could be generated" came from an unpublished draft marked "do not quote".
  - A *Stocks & Commodities* test by M. Carr found simple P&F patterns have "no predictive value" alone.
  - **No test of horizontal-count target accuracy was found** (B1 and B2). Practitioner sources call the counts "rough" and say they are "more often than not, not met precisely"; the only quantitative example B2 found is a single-chart case study.
- **[B2] Bulkowski's "bigger base, bigger move".** Tall patterns outperform in 89% (up) and 100% (down) of pattern types, and wide ones in 91% / 85%. These are *percentage* moves with no volatility control. A tall rectangle marks a volatile stock, which moves more in percent. In ATR units A found no effect of width or duration (§2.5), so the "cause" adds nothing beyond volatility.
- **Pine feasibility.** Possible (columns from closes, box = k·ATR, 3-box reversal, stateful arrays), but the count's phase boundaries are subjective, so it is not unique.

### 1.9 Effort vs result; VSA; Weis waves; shortening of the thrust [A✓, extended]
- **Law.** Effort = volume; result = spread and close location. Heavy volume with little progress = absorption (reversal risk); big result on no volume = suspect.
- **VSA bars.** No demand: a narrow up-bar on volume below the previous two bars; no supply: the mirror; stopping volume: heavy volume on a down bar closing off the low.
- **Weis wave / SOT.** Volume summed per zig-zag swing; shortening of the thrust = successive pushes gain less distance ("after 3-4 up or down waves", LuxAlgo, which also calls Weis waves "descriptive").
- **Algorithm.** `vr`, `sr = (high − low)/A`, `clv = (close − low)/(high − low)`. Absorption: `vr ≥ 2 and sr ≤ 0.8`. Guard symbols without volume: `ta.cum(nz(volume)) == 0`. **[NEW-B]** On ≤ 5m charts normalise volume by time of day (median of the same clock slot over the last 20 sessions), because the intraday volume cycle dominates raw `vr`.
- **[NEW-B] Academic analogues** (daily/weekly, cross-section): returns on high-volume days reverse more than on low-volume days (Campbell-Grossman-Wang 1993); the sign depends on why volume is high, with hedging-driven trades reversing and informed trades continuing (Llorente-Michaely-Saar-Wang 2002); stocks with abnormally high volume over a day or week rise over the following month (Gervais-Kaniel-Mingelgrin 2001, "high-volume return premium"). None of these is a bar-level "effort vs result" rule for an intraday target.
- **[B2] The baseline and the contradiction.**
  - *Effort normally produces result.* Volume is positively related to the size of the price change, and in equities to the change itself (Karpoff 1987, survey). The size link is the more robust one. VSA's "effort without result" is a deviation from this stylised fact.
  - *The direction of the volume conditioning is not robust.* Conrad, Hameed & Niden (1994, weekly, NASDAQ 1983-90): high-transaction stocks reverse, low-transaction stocks continue. Cooper (1999, *RFS*, weekly, large NYSE/AMEX): *decreasing*-volume losers reverse most, and increasing-volume stocks reverse less. Goyal's later NBER work notes the two conflict and ties the difference to sample and liquidity.
  - B's 5m data side with Cooper: low-effort climaxes revert at least as much as high-effort ones (§2.7c). A fixed "high effort → reversal" weight would have the wrong sign on some samples.

### 1.10 Supply/demand zones (Seiden / Online Trading Academy school) [A✓, extended]
- **Zone types.** Continuation RBR / DBD; reversal DBR (demand) / RBD (supply). Base = 1-6 small candles; zone from the base's bodies or wicks to its extreme.
- **Odds enhancers.** OTA teaches eight (four in the Professional Trader class, four more in the XLT class), with a pass/fail score that is not published. Those named in public articles: strength of departure ("the less time price spends at a level, the more out of balance supply and demand is"), time at level, freshness, the profit zone ("the key Odds Enhancer most overlooked"), reward-to-risk, and higher-timeframe location. **[CORRECTED]** No point scale is public; any "0-2 points" scheme seen online is a reconstruction.
- **Engine relation.** An OB is a 1-candle base at the leg origin (1663-1748); FVG/OB "quality" is departure strength (912, 1692, 1735); mitigated OBs are skipped (1693-1700, 1736-1741), which is freshness.
- **Algorithm (Pine-feasible).** Base = k ∈ [1, 6] bars with body ≤ 0.5·A and combined range ≤ 1.0·A; departure = next 1-3 bars with body sum ≥ 1.5·A one way; zone = [min low, max body] (demand); fresh until the first touch; strength = departure/A.
- **[B2] Exact rules used in `sdzones.py`** (the test in §2.7g):
  - *Base:* the longest run of k ≤ 6 bars ending at bar i, each with |close − open| ≤ 0.5·ATR[i−1], and combined high − low ≤ 1.0·ATR.
  - *Departure:* the first m ≤ 3 following bars, all closing in the departure direction, whose body sum reaches ≥ 1.5·ATR. One zone per side per 4 bars.
  - *Zone:* demand = [base low, highest base body]; supply = [lowest base body, base high].
  - *Type:* reversal (DBR/RBD) if the 5 bars before the base moved against the departure, otherwise continuation (RBR/DBD).

### 1.11 Fresh vs tested zones [A✓, extended]
- Practitioner rule: the first return is the highest-probability reaction; each further test weakens the zone.
- **[NEW-B] Conflict in the evidence.** S/R studies find the opposite for *bounces*: each prior bounce raises the next bounce probability (Garzarelli et al. 2014; Chung & Bellotti 2021), decaying over hours. Vendor OB tests find fresh OBs *react* slightly more (Nordman, via `ict_pd.final.md`). Neither supports freshness for *reach*.
- **[B2] B's own test (§2.7g).** First-touch minus second-touch reaction excess is +2.5 pp (CME 1H), +3.1 pp (CME 5m), 0.0 (BTC 1H) and +0.6 pp (daily). Each is ≤ 2σ. So freshness is at most a small reaction effect on futures, and nothing for reach.

### 1.12 How practitioners map events to targets (the claims tested in §2)

| Event | Claimed next draw | Invalidation | Test |
|---|---|---|---|
| Spring (#3, low volume) | opposite range edge (creek) | spring low | A `spring`, `spring_tgt_hi`; B canonical `SPRING` |
| Spring + SOS | opposite edge, then beyond | spring low | A `spring_sos`; B `SOS` |
| UT / UTAD | range low (ice) | UT high | A `upthrust`, `ut_tgt_lo`; B `UTAD` |
| Failed breakout by close | opposite edge | breakout extreme | A `spring_cl`, `upthr_cl` |
| Partial decline / rise | top / bottom edge | — | A `part_dec`, `part_rise` |
| SC / BC → AR | AR (50% of the leg), then ST of the extreme | climax extreme | A `climax_dn/up`; B climax bars, B `AR` race |
| New TR | either edge | — | A `tr_first`, touch splits |
| Range breakout | measured move; throwback; longer cause → bigger effect | opposite edge | A `breakout.py` |
| Coiling / inducement before a pool forms | bigger draw (TradeAxis "density") | — | A `density.py`, `induce2.py`; B `pivots` |
| Equal highs/lows, tests, age | bigger, "matured" pools | — | A `eqtest.py`, `agetest.py`; B `agedetail.py` |
| High- vs low-volume sweep (effort) | effort without result → reversal | — | A `effort.py`; B `climax` |
| S/D zone: strong departure, short base, fresh, reversal type | a stronger magnet and a stronger reaction | distal edge | [B2] `sdzones.py` |

---

## 2. Evidence

Grades: **strong** = peer-reviewed or large replicated quantitative study; **moderate** = published, reproducible statistics or backtests with numbers; **weak** = practitioner consensus or anecdote; **none** = folklore or unfalsifiable.

### 2.0 Methods
- **Race outcome** (A and B). First strict trade-through of target T or stop S, bar by bar from the next bar, up to K bars (K = 30; A also 60). A bar crossing both is ambiguous and dropped; "neither" is dropped. Statistic `hit − geo`, with `geo = (C − S)/(T − S)` (gambler's ruin).
- **Null.** Bar-shuffled surrogates (A 6-8, B 4-6 per dataset): each bar keeps its gap, its high/low/close offsets from its open, and its volume; the sequence is destroyed; the same detector runs on the surrogate. **Excess** = `(hit − geo)_real − (hit − geo)_null`.
- **Magnet outcome.** Level traded through within K bars minus `S(d)`, the series' empirical probability that the K-bar excursion exceeds d ATR in that direction: the engine's own "random level at the same distance" baseline (`f_potBase` 1314-1322 without the regime split).
- **Checkpoints** (age, tests, EQ). A: every 10 bars for live pivots within 10 ATR. B: every 5 bars up to age 30, then every 10, within 6 ATR, split by distance band. SEs cluster-robust by pool. Overlapping pools share price paths, so these SEs are optimistic; treat |edge| < 2 pp as noise.
- **Limits.** Few Wyckoff events per series (n 30-300 per pooled cell); settings share data, so they are robustness checks, not replications; B's CME data cover about 13 months (1H) and 3 months (5m).

### 2.1 Published and external evidence (verification status)

| # | Claim | Source and design | Numbers | Grade · status |
|---|---|---|---|---|
| W1 | Rectangle (TR) patterns carry information | Lo, Mamaysky & Wang (2000), *J. Finance* 55:1705-1765; kernel-smoothed extrema; RTOP/RBOT = 5 alternating extrema within 0.75%; NYSE/AMEX and Nasdaq 1962-96 | A: RTOP n 1,482 / RBOT 1,616 (NYSE/AMEX), 1,134 / 1,320 (Nasdaq); KS p 0.002 / 0.000 and 0.000 / 0.001; volume trend adds little on Nasdaq | strong for distribution *shape*, not direction or targets · [not re-fetched]: B confirmed the paper and its "several patterns add incremental information" conclusion via the CFA digest and NBER listing, not the table |
| W2 | Rectangle breakout statistics | Bulkowski, thepatternsite.com (rectangle bottoms > 900 and tops > 1,000 "perfect trades", daily US stocks, bull markets) | Bottoms: up 59%; throwback/pullback 64% / 66%; average rise/decline 48% / 16%; break-even failure 15% / 24%; target met 79% up / 55% down. Tops: up 63%; throwback 66% / 64%; average 51% / 13%; failure 15% / 34%; target 78% / 54% | moderate (large n, no random baseline) · **[B2] all re-read at the source** |
| W3 | Partial rise/decline predicts the breakout side | Bulkowski partial rises / partial declines pages (bull markets, 3/1989-11/2013, 5,959 patterns); rectangle pages | Partial decline → up 80% (rectangle bottoms) / 91% (tops); partial rise → down 74% (bottoms) / 57% (tops). Rectangle pages: partial rise → down 75%, partial decline → up 79% (tops) / 77% (bottoms) | weak as an edge (no geometry baseline); A's test: geometry already gives 0.71-0.81, excess inconsistent (§2.2) · **[B2] A's numbers confirmed; B1's correction reverted** |
| W4 | Busted rectangles move far the other way | Bulkowski, Busted Rectangles | **[B2] A's numbers confirmed at the source:** "51% of rectangle tops will bust"; of those, 66% single-bust, 3% double, 31% triple. "The average rise is 71% (yes, 71% for downward breakouts which bust upward)" vs "Non-busted rectangle tops will see price rise by 51% on average". Bust = price moves ≤ 10% after the breakout, reverses and closes beyond the opposite side. No sample size on the page | weak (no baseline; % moves) · B1's "won 71% of trades" reading was wrong and is reverted |
| W5 | High breakout volume → more failures and throwbacks | Bulkowski, Volume Study; Breakout Day Volume; Study of Studies | Study of Studies [B2 re-read]: heavy breakout volume helps in 79% (up) / 67% (down) of pattern types, but "after a high volume breakout, performance doesn't improve much but failures triple". Breakout Day Volume [B2]: rectangle *tops* do better on heavy volume; rectangle *bottoms* with upward breakouts do better on *light* volume; bottoms with downward breakouts show no preference. Rising volume inside the pattern helps upward breakouts in 62% of types and falling volume helps downward ones in 56% ("close and mixed"). A's exact failure and throwback figures (14% vs 5%, 28% vs 11%, 57% vs 18%) | moderate (no baseline) · direction and "failures triple" [B2 verified]; A's exact figures [not re-fetched] |
| W6 | Bigger bases, bigger moves | Bulkowski, Study of Studies | **[B2 verified]** Tall patterns outperform in 89% (up) / 100% (down) of pattern types; wide in 91% / 85%. Throwbacks hurt performance in 97% of pattern types, pullbacks in 91% | weak: percentage moves without a volatility control (§1.8) |
| W7 | High-volume price changes reverse | Campbell, Grossman & Wang (1993), *QJE* 108(4) | First-order daily autocorrelation declines with volume, for indices and large stocks. A's coefficient (−0.233, s.e. 0.079) | strong (daily; small R²) · direction [A✓], coefficient [not re-fetched] |
| W8 | Drift bursts mostly revert, more with high volume (negative bursts) | Christensen, Oomen & Renò, "The drift burst hypothesis", *J. Econometrics*; arXiv 2601.08974 | **[A✓, B read full text]** 5-minute scatter quadrants Q1 324, Q2 670, Q3 279, Q4 828, so **71% are reversals** ("gradual jumps roughly one third"). ES: −37.39 bps in 5 min → +8.01 bps over the next 55 min (**21% retrace**); +36.41 → −5.44 (15%). Serial correlation −0.80 (negative) / −0.26 (positive). Reversal strongest for large drops with high volume; "these effects are not present in positive drift bursts" | strong (minutes; partial, not full, reversal) |
| W9 | Extreme intraday moves partly reverse within an hour | Zawadowski, Andor & Kertész (2006), *Quant. Finance*; arXiv cond-mat/0406696 | **[A✓, B read full text]** NASDAQ 60-min rises > 4% and 8× normal volatility: +5.34% → −1.68% over the next 60 min (t 7.9), and +0.02% (n.s.) over minutes 60-120. Rebound/shock slope −0.139 ± 0.046 (NYSE), −0.249 ± 0.042 (NASDAQ). Excess volume and volatility stay high for days | strong (≤ 1 hour) |
| W10 | Prior bounces raise the next bounce probability, decaying over hours | Garzarelli et al. (2014), *Sci. Rep.*; Chung & Bellotti (2021), arXiv 2101.07410 | Bounce p > 0.5 and rising with prior bounces; EURUSD decays to 0.5 at about 350-900 min | strong (HF) / moderate (intraday) · [A✓ via sibling `ict_liq.final.md` E4-E5] |
| W11 | Swept levels → continuation | Mahadzva, SSRN 7430998 (2026) | 65/66 fold selections favour continuation | **[DOWNGRADED]** weak (unverified preprint; `ict_liq.final.md` E7) |
| W12 | Equal highs/lows barely bigger draws | Open-source distance-matched test (sibling E6) | EQ 63-82% vs ordinary 68-76% at the same distance; < 1 pp | moderate · [A✓ via sibling] |
| W13 | "13,000 Wyckoff accumulation signals over 20 years" | Reddit r/Daytrading | 65.1% win at 40 days, no baseline | **[DOWNGRADED]** none (post not findable by B; method never published) |
| W14 | Wyckoff is hard to backtest | Villahermosa (tradingwyckoff.com, "Limitations"); MQL5 article 22628 ("full phase detection … requires subjective judgment that is difficult to codify reliably") | Quote "Lack of public quantitative backtests" | candid practitioner statements · Villahermosa [not re-fetched] (host blocked); MQL5 [A✓ via search summary] |
| W15 | Spring-type rules | Fraser, Villahermosa, FibAlgo, fis_wse, `tianyaphoto` | Definitions only (§1.4) | none (no statistics) |
| W16 | S/D odds enhancers | OTA instructor articles on FXStreet (eight enhancers, proprietary scoring); ProEA ("an assumption, not a measured result") | No quantitative tests found anywhere. One blog (El Trader Financiado) states that no source has measured whether zone confluences improve results | weak (reaction) / none (reach) · ProEA quote [not re-fetched]; OTA [NEW-B] |
| W17 | Wyckoff regimes as a statistical object | Srivastava & Bhattacharya (2018), arXiv 1812.02527 | Markov-switching regimes "loosely modeled on" Wyckoff; no event-level target tests | weak for this question · [A✓] |
| W18 | Deep-learning Wyckoff detection | Pal (2024), arXiv 2403.18839 | Trained on synthetic swing/filler points; no out-of-sample trading or target statistics | none · [A✓] |
| W19 | AMD (ICT restatement of accumulation → manipulation → distribution) | Taylor, arXiv 2610.35887; NQ 15m, n 484 | **[CORRECTED per `bias_dol.final.md`]** the outcome is the 16:00 close vs the Asia midpoint, not delivery to the opposite pool; "no directional information beyond the daily trend regime" is the author's reading of a regime split, without a trend-only baseline; with trend 62-71%, against 25-30% | moderate |
| W20 | [NEW-B] Vendor-validated Wyckoff accumulation engine (stock selection) | krentium.com via the public `signal-validation/wyckoff-validation` repo; 649 survivorship-corrected US stocks 2006-26; proprietary rules | Daily engine: 20-day Carhart α **+0.51% per signal (t 3.7)**; **5-day α +0.07% (t 1.1, n.s.)**; 40-day +0.96% (t 4.7). Win rate vs 50%: 57.9% train, 59.0% test | weak (vendor, hidden rules, development-search size unknown). Relevance: a multi-week cross-sectional drift, *not* a which-pool-first forecast; the short horizon is null |
| W21 | [NEW-B] Trading-range break rules | Brock, Lakonishok & LeBaron (1992), *J. Finance* 47(5); Sullivan, Timmermann & White (1999), *J. Finance* 54(5); [B2] Zhu, Jiang, Li & Zhou (2015), arXiv 1504.04254 | Range-break buy-minus-sell returns significant on the DJIA 1897-1986; no out-of-sample advantage 1987-96 (via `academic_sr.md` S17-S18). Chinese indices 1991-2013: TRB beats MA rules and survives White's Reality Check before costs, but "once transaction costs are included, trading profits will be eliminated completely" | strong (historical, decayed) |
| W22 | [NEW-B] Stops beyond levels; cascades when crossed; S/R = depth | Osler (2003) *J. Finance* 58(5), about 9,700 orders; Osler (2005) *JIMF* 24(2); Kavajecz & Odders-White (2004) *RFS* 17(4) | Stop-buys cluster just above round numbers, take-profits at them; extra move after crossing +0.27 to +2.35 hundredths of a percent for 15 min to 2 h, gone at 1-2 days; S/R coincide with peaks in book depth (via `academic_sr.md` S4-S6) | strong (mechanism) |
| W23 | [NEW-B] Volume-return relation is conditional | Llorente, Michaely, Saar & Wang (2002), *RFS* 15(4); Gervais, Kaniel & Mingelgrin (2001), *J. Finance* 56(3) | Hedging-driven high-volume returns reverse, informed ones continue; abnormal-volume stocks rise over the next month (premium larger when volume was abnormal *without* a large return) | strong (daily/weekly cross-section); not a bar-level target rule |
| W24 | [NEW-B] Reversion below hours, trends above | Safari & Schmidhuber (2025), arXiv 2501.16772; futures tick to centuries | "Markets are in a trending regime on time scales that range from a few hours to a few years, while they are in a reversion regime on shorter and longer time scales" | strong (consistent with B's 5m vs 1H split, §2.7) |
| W25 | [NEW-B] P&F signal rules | Anderson & Faff (2008), *IRFA* 17(1):198-217; Carr (*Stocks & Commodities*) | S&P 500 futures 1990-98, eight objective P&F rules, bootstrap. **[B2]** Published abstract: "mixed statistical significance with some rules proving significant while many others were not". Carr: simple P&F patterns have no predictive value alone. No test of count *targets* exists | weak (signals, not count targets) |
| W26 | [NEW-B] Spring "win rates" in the wild | TakeProfit VSA article; TradingView vendor scripts | "about 72%" for a spring setup; one EURUSD sample 22/32 = 68.8%; no method, no baseline | none |
| W27 | [B2] Volume conditioning of short-horizon reversals has no stable sign | Conrad, Hameed & Niden (1994), *J. Finance* 49(4):1305-29; Cooper (1999), *RFS* 12(4):901-935; Goyal (NBER 2004 conference paper) | CHN: weekly, high-transaction securities reverse, low-transaction ones continue. Cooper: weekly, large NYSE/AMEX; decreasing-volume stocks reverse more and increasing-volume stocks show weaker reversals. Goyal notes the conflict | strong (each), conflicting in direction · abstracts only |
| W28 | [B2] Effort normally gives result | Karpoff (1987), *JFQA* 22(1):109-126 (survey) | Volume rises with the absolute price change, and in equities with the price change itself; the absolute link is the more robust one | strong (stylised fact; the baseline VSA deviates from) |
| W29 | [B2] Reversal pay-off is larger when liquidity is scarce | Nagel (2012), "Evaporating Liquidity", *RFS* 25(7):2005-2039 | Short-term reversal returns, read as returns to liquidity provision, are strongly time-varying and predictable with the VIX; Sharpe ratios rise with it | strong (daily cross-section). Explains why B's 5m climax reversal lives in overnight and pre-open bars (§2.7f) |
| W30 | [B2] Sibling tests of "failure back inside → opposite edge" | `amt_profile.md` X3 / E-OWN-4 (Market Profile 80% rule); `price_action.md` T4 (Brooks 80% rule) | Value-area re-entry → far edge: 25-28% vs a 27-29% base rate (tradeify, 589 sessions); own test +7.9 pp, n 42, n.s. Breakouts by close come back inside within 5 bars in 53-64% of cases vs 48-53% in nulls, so failures are a little *more frequent* than random. But what follows a failure is geometry (A's `spring_cl` ≈ 0) | moderate · same null as springs in a different school |
| W31 | [B2] Published Wyckoff detectors | FibAlgo (climax; spring & upthrust; accumulation/distribution), SRFX "Wyckoff Phase & Volume Analyzer", WillyAlgoTrader "Wyckoff Range Engine", AlphaExtract "Wyckoff Event Detection" (TradingView descriptions) | Rules and parameters only (§1.1-1.4). One shows per-chart descriptive counts (SOS → target hit rate, Spring → SOS follow-through) with no geometry baseline. None publishes a tested edge | none (definitions) |

### 2.2 A's race tests after range events (`wyck.py`) [A✓; replicated in spirit by B §2.7]

Excess over the null, `(hit−geo)_real − (hit−geo)_null`, pooled over seven datasets; settings N (range length) / K (horizon) / kmax (max width in ATR); SE ≈ √(0.22/n).

| Event (expected side) | N20/K30/6 | N30/K30/8 | N50/K30/8 | N30/K60/8 |
|---|---|---|---|---|
| `tr_first` (top edge first at range birth) | −0.002 ± 0.020 (n 537) | +0.022 ± 0.022 (441) | −0.056 ± 0.030 (244) | +0.020 ± 0.022 (475) |
| `spring` → top edge before spring low | +0.016 ± 0.039 (143) | −0.044 ± 0.041 (132) | −0.075 ± 0.054 (76) | −0.013 ± 0.040 (138) |
| `spring_cl` (close-based) | −0.048 ± 0.053 (79) | −0.043 ± 0.057 (67) | −0.045 ± 0.075 (39) | +0.010 ± 0.055 (74) |
| `spring_sos` | −0.006 ± 0.072 (42) | −0.035 ± 0.084 (31) | −0.145 ± 0.177 (7) | −0.012 ± 0.084 (31) |
| `upthrust` → bottom edge before UT high | +0.037 ± 0.034 (186) | −0.002 ± 0.039 (144) | −0.034 ± 0.053 (79) | +0.008 ± 0.039 (148) |
| `upthr_cl` (close-based) | +0.090 ± 0.047 (100) | +0.145 ± 0.053 (77) | +0.096 ± 0.075 (39) | +0.163 ± 0.051 (83) |
| `upthr_sow` | −0.039 ± 0.068 (48) | −0.088 ± 0.108 (19) | −0.027 ± 0.166 (8) | −0.051 ± 0.105 (20) |
| `part_dec` → top first | +0.010 ± 0.040 (141) | −0.020 ± 0.035 (183) | −0.135 ± 0.038 (152) | −0.038 ± 0.034 (196) |
| `part_rise` → bottom first | −0.051 ± 0.043 (118) | +0.011 ± 0.039 (147) | +0.080 ± 0.041 (128) | +0.008 ± 0.037 (158) |
| `climax_dn` (SC) → 50% AR before SC low | +0.023 ± 0.022 (452) | same | same | +0.021 ± 0.022 (454) |
| `climax_up` (BC) → 50% AR before BC high | −0.047 ± 0.026 (315) | same | same | −0.050 ± 0.026 (316) |

- Raw rates make the geometry visible: after a spring the top is taken first in 0.12-0.38 of decided cases against geometry 0.16-0.26 (NQ 0.174 vs 0.259; GC 0.143 vs 0.248; EURUSD 1H 0.120 vs 0.199; S&P D 0.312 vs 0.226). Partial declines "work" 0.70-0.93 of the time, but geometry already says 0.71-0.81, which explains most of Bulkowski's figures.
- The only cell positive in all four settings is `upthr_cl` (+0.09 to +0.16, 2-3σ each), but the settings share data, the per-dataset signs are mixed (S&P −0.14, n 7; NASDAQ +0.32, n 6; NQ +0.25, n 15; GC +0.16, n 14; EURUSD +0.05 / −0.09, n 7), and the mirror `spring_cl` is negative. Per-chart ledger hypothesis only (weak).
- Spring and UT extremes are retaken at random-level rates: spring lows +0.018 ± 0.033 (N30) / −0.026 ± 0.034 (N20); UT highs −0.018 ± 0.028 / −0.014 ± 0.025.

### 2.3 A's magnet tests (`magnet.py`, K = 30) [A✓]

| Level | N = 30 edge (n) | N = 20 edge (n) | Null (N30 / N20) |
|---|---|---|---|
| Range high at range birth | +0.001 ± 0.019 (479) | +0.004 ± 0.017 (578) | +0.012 / −0.005 |
| Range low at range birth | −0.012 ± 0.020 (479) | +0.001 ± 0.019 (578) | +0.008 / +0.008 |
| Range edge, 2 touches | +0.000 ± 0.015 (808) | +0.003 ± 0.014 (972) | +0.018 / +0.004 |
| … 3 touches | −0.031 ± 0.038 (125) | +0.017 ± 0.035 (154) | −0.049 / −0.018 |
| … 4+ touches | −0.084 ± 0.095 (25) | −0.084 ± 0.085 (30) | +0.053 / −0.001 |
| Opposite edge after a spring | −0.036 ± 0.038 (141) | −0.037 ± 0.040 (153) | −0.002 / −0.008 |
| Spring low (retaken) | +0.018 ± 0.033 (141) | −0.026 ± 0.034 (153) | +0.003 / +0.005 |
| Range low after an upthrust | −0.073 ± 0.032 (153) | −0.013 ± 0.034 (198) | +0.033 / −0.016 |
| UT high (retaken) | −0.018 ± 0.028 (153) | −0.014 ± 0.025 (198) | −0.016 / +0.031 |
| 50% AR after an SC | +0.007 ± 0.016 (589) | same | −0.019 |
| 50% AR after a BC | −0.018 ± 0.022 (380) | same | −0.004 |

`quant_regime.md` (2.6) independently finds that ranges do not raise P(both sides raided) or pool magnetism.

### 2.4 The engine's density and freshness inputs (A + B)

**Input distributions per bar (engine definitions 888-895).**

| Series | coil P(= 0) | coil median | coil P(> 0.5) | ind P(= 1) | ind P(≥ 2/3) | ind P(= 0) | source |
|---|---|---|---|---|---|---|---|
| S&P 500 D | 0.004 | 0.54 | 0.550 | 0.881 | 0.964 | 0.005 | A = B (identical) |
| NASDAQ D | 0.015 | 0.42 | 0.375 | 0.873 | 0.970 | 0.004 | A = B |
| GOOG D | 0.043 | 0.39 | 0.336-0.337 | 0.835-0.836 | 0.954 | 0.005 | A = B |
| EURUSD 1H 17-18 / NQ / GC / EURUSD 1H 24-26 | 0.001-0.012 | 0.50-0.59 | 0.50-0.61 | 0.64-0.90 | 0.86-0.97 | 0.003-0.023 | A |
| ES / NQ / RTY / YM / CL 1H (CME) | 0.004-0.025 | 0.45-0.55 | 0.42-0.57 | 0.86-0.91 | 0.955-0.978 | 0.001-0.010 | **B** |
| ES / NQ / GC / RTY / YM / CL 5m (CME) | 0.005-0.037 | 0.55-0.63 | 0.57-0.66 | 0.76-0.89 | 0.909-0.961 | 0.004-0.021 | **B** |
| BTC 1H | 0.003 | 0.61 | 0.634 | 0.837 | 0.950 | 0.007 | **B** |

- **Population means** (B, 15 series): coil 0.41-0.63 (median **0.55**); indScore 0.88-0.96 (median **0.93**). WYK-1 uses these as neutral constants.
- `induceBar` fires on any wick through a 5-bar extreme that closes back inside, which happens every few bars; `min(1, count/3)` over 20 bars is about 1 always. **The inducement term is a constant**, +0.15 density for every liquidity pool and +0.13 to +0.20 for every array.
- De-saturated count (sweep of the prior 20-bar extreme by ≥ 0.10 ATR, close back inside): 0 / 1 / ≥ 2 on 15-25% / 29-37% / 39-53% of bars (A and B agree).

**Reach of pivots by density at birth** (K = 30, edge vs S(d), cluster SE).

| Split | A (pivLen 5, n 6,246; daily + 1H) | B (pivLen 5, n 24,544; CME 1H/5m, BTC 1H) |
|---|---|---|
| All pivots | −0.014 ± 0.006 (null +0.001) | −0.009 ± 0.003 |
| Coil low / mid / high | — / −0.008 (≤ 0.5) / **−0.019** (> 0.5) | **−0.022** ± 0.009 (≤ 0.25) / −0.011 ± 0.005 / −0.006 ± 0.004 (> 0.5) |
| Coil 500-bar percentile terciles | −0.013 / +0.002 / −0.028 (± 0.010) | −0.010 / −0.010 / −0.008 (± 0.005) |
| indScore < 2/3 vs ≥ 2/3 | n 55 vs −0.013 (93.9% of pivots) | −0.001 ± 0.012 (6%) vs −0.010 ± 0.003 (94%) |
| De-saturated sweeps 0 / 1 / ≥ 2 | −0.022 / −0.008 / −0.013 (± 0.009-0.013) | −0.007 / −0.014 / −0.007 (± 0.004-0.006) |

- **Reading [CORRECTED wording].** A described high coil as "slightly negative". B's larger sample orders it the other way. `quant_regime` (23 series, its own code) found high-coil terciles −0.005 to −0.018 with a similar null. The effect is **sign-unstable and ≤ 1.6 pp**: no information, in either direction.
- Note on the per-dataset level: all-pivot edges are slightly negative on every CME 1H series (−0.015 to −0.038) and near zero on 5m (−0.019 to +0.009): pivots are slightly "sticky" at 1H (consistent with W10).

**Freshness / age** [CORRECTED]. A (36,724 checkpoints, 4,783 pools): ≤ 30 bars −0.011 ± 0.006; 31-150 −0.007 ± 0.005; 151-500 −0.018 ± 0.006; > 500 −0.001 ± 0.006. B's finer split (`agedetail.py`, `agedetail_sim.py`):

| Age (bars) | CME 1H | CME 5m | BTC 1H | A's 1H set (NQ, GC, EU) | Daily (S&P, NASDAQ, GOOG) |
|---|---|---|---|---|---|
| 5-10 | **−0.019 ± 0.008** | **−0.006 ± 0.004** | **−0.008 ± 0.005** | **−0.018 ± 0.007** | +0.002 ± 0.012 |
| 11-30 | +0.020 ± 0.010 | −0.006 ± 0.005 | +0.006 ± 0.006 | −0.009 ± 0.009 | +0.011 ± 0.017 |
| 31-60 | +0.047 ± 0.015 | +0.009 ± 0.008 | +0.020 ± 0.009 | −0.014 ± 0.013 | −0.028 ± 0.023 |
| 61-150 | −0.036 ± 0.015 | +0.033 ± 0.009 | −0.018 ± 0.009 | −0.013 ± 0.013 | +0.018 ± 0.024 |
| 151-300 | −0.051 ± 0.017 | +0.020 ± 0.011 | +0.013 ± 0.012 | −0.018 ± 0.017 | +0.034 ± 0.038 |
| 301-500 | −0.032 ± 0.027 | **−0.041 ± 0.015** | +0.008 ± 0.018 | **−0.082 ± 0.022** | +0.002 ± 0.043 |
| 501-1000 | −0.052 ± 0.024 | **−0.057 ± 0.012** | −0.028 ± 0.016 | **−0.065 ± 0.019** | +0.103 ± 0.044 |
| 1001-2000 | −0.032 ± 0.030 | **−0.082 ± 0.017** | +0.000 ± 0.017 | +0.027 ± 0.025 | +0.164 ± 0.059 |

- **Reading.** (i) Pools 5-10 bars old are reached slightly *less* than a random level (−0.6 to −1.9 pp in 4 of 5 groups). (ii) Middle ages have no stable sign. (iii) Intraday pools older than about 300-500 bars are reached 3-8 pp less (old, "defended" levels; A also saw −0.075 within 1 ATR for age > 150). (iv) On daily equities in a bull sample, very old highs are retaken *more* (trend), so there is no universal decay either.
- **What the engine does** (671, `halfLife` 150): `fresh = (0.35 + 0.65·(1 − e^(−age/37.5)))·0.5^(age/600)` → 0.43 at age 5, 0.69 at 30, 0.85 at 100, 0.83 at 150, 0.79 at 200, 0.56 at 500, 0.32 at 1,000. With `wFresh` 10 of 100 a brand-new pool loses about **4.2 points** against a 100-bar pool, equal to `hyst` 4.
- **Scale check [NEW-B].** On the proximity pillar, moving a pool from 1 to 2 ATR costs about 4.4 points (Δlin 0.10, Δreach ≈ 0.25, × 25) for roughly 18 pp of K-bar reach on 1H, i.e. about **4 pp of reach per score point**. The ramp's 4 points for young pools are therefore worth ~15 pp of reach-equivalent, against a measured ~1 pp. The slow decay (0.56 at 500 bars, 0.32 at 1,000) is in proportion with the −3 to −8 pp for old intraday pools.

**Tests and equal highs/lows** [A✓]. Tests 0/1/2/≥3 → −0.010 / −0.011 / +0.003 / +0.027 (A); EQ count 0/1/≥2 → −0.007 / −0.028 / −0.049 (A); siblings replicate "≈ 0" (`ict_liq.final.md` T1: EQ any +0.5 ± 1.6 pp, tests == 1 +1.4 ± 0.8 pp). Handled by ICT-10 / OF-3 / SMC-3; not repeated here.

### 2.5 Cause and effect, measured move, throwback (A's `breakout.py`, N = 30, K = 30) [A✓]

| Subset | MM first | Geometry | Diff | Throwback | Random level | Diff |
|---|---|---|---|---|---|---|
| All (real) | 0.571 | 0.565 | +0.006 | 0.870 | 0.872 | −0.001 |
| All (null) | 0.546 | 0.571 | −0.025 | 0.883 | 0.883 | +0.000 |
| Up / down | 0.589 / 0.549 | 0.561 / 0.571 | +0.028 / −0.022 | 0.848 / 0.900 | 0.870 / 0.874 | −0.022 / +0.026 |
| Short / long cause (38 bars) | 0.561 / 0.582 | 0.564 / 0.566 | −0.003 / +0.015 | 0.906 / 0.833 | 0.880 / 0.863 | +0.026 / −0.030 |
| Narrow / wide (4.9 ATR) | 0.577 / 0.564 | 0.586 / 0.540 | −0.009 / +0.024 | 0.874 / 0.867 | 0.858 / 0.885 | +0.016 / −0.018 |

Null-adjusted MM excess about +0.03 ± 0.02. Longer or wider causes do not produce measurably bigger effects. Bulkowski's 64-66% throwback rate is proximity.

### 2.6 Effort vs result at swept pools (A's `effort.py`; daily and EURUSD 1H with volume) [A✓, CORRECTED magnitude]

| Subset | n | Continuation edge (1 ATR beyond the sweep extreme) | HOLD: throwback edge |
|---|---|---|---|
| All | 1,823 | +0.021 ± 0.010 | +0.003 ± 0.009 (n 1,021) |
| HOLD (closed beyond) | 1,021 | +0.008 ± 0.013 | — |
| HOLD by vr < 0.8 / 0.8-1.5 / > 1.5 | 55 / 694 / 272 | −0.024 / +0.008 / +0.013 | +0.033 / +0.014 / −0.031 (± 0.022-0.026) |
| REJECT (closed back inside, spring/UT shape) | 802 | +0.039 ± 0.016 | — |
| REJECT by vr < 0.8 / 0.8-1.5 / > 1.5 | 60 / 520 / 222 | −0.010 / +0.047 / +0.033 | — |

- The *direction* (no reversal edge after a rejected sweep) is replicated by siblings on much larger samples. **[CORRECTED]** The *size* of the continuation lean is smaller there: +1.5 ± 0.7 pp (n 5,899, `ict_liq.final.md` B7) and a symmetric ±1 ATR race of 0.497-0.510 for hold and reject alike on 5m/15m/1H (`quant_regime.md` 2.7). Treat REJECT as neutral, which is ICT-9's fix.
- Volume does not modulate outcomes at these timeframes. B extends this to 5m (§2.7).

### 2.7 [NEW-B] Researcher B's independent tests (new code, new data)

**(a) Canonical climax-anchored structures** (`wyckB.py wyck|wyckloose|wyckbtc`; §1.1 detector; race and null as §2.0).

| Event (target / stop) | Strict, CME 1H+5m (volume gate) | Loose (vr ≥ 1.5, range ≥ 1.5 ATR) | BTC 1H (price-only) |
|---|---|---|---|
| SPRING (range high / spring low) | +0.007 ± 0.032 (n 209; hit 0.292 vs geo 0.286) | +0.018 ± 0.027 (301) | +0.022 ± 0.040 (137) |
| UTAD (range low / UT high) | −0.024 ± 0.038 (149) | −0.049 ± 0.032 (210) | +0.079 ± 0.044 (115) |
| AR (climax extreme / AR extreme, at AR confirmation) | **+0.034 ± 0.016** (831) | **+0.037 ± 0.014** (1,197) | −0.010 ± 0.017 (797) |
| SOS (measured move / range low) | −0.067 ± 0.047 (100) | −0.111 ± 0.041 (132) | +0.029 ± 0.042 (122) |
| SOW (measured move / range high) | +0.101 ± 0.055 (73) | +0.037 ± 0.045 (108) | +0.023 ± 0.049 (91) |

- Split by timeframe, the AR cell is a **5m effect**: 5m +0.054 ± 0.020 (strict, n 555) and +0.045 ± 0.016 (loose, 853), magnet +0.06 to +0.08; 1H −0.005 ± 0.028 (strict) and +0.046 ± 0.026 (loose, magnet −0.003); BTC 1H −0.010.
- Spring magnets (opposite edge within K vs S(d)) are +0.025 to +0.054 while the *race* is null: after a spring *both* sides are reached more often than an unconditional random level, because volatility expands after the event (ATR lags). Only the race measures direction.
- **Reading.** The spring/UTAD claim fails in the canonical range definition too. The AR → "retest through the climax extreme" pattern is mildly positive on CME 5m only.

**(b) Price-only climax bars** (`climaxnull.py`; new 20-bar extreme, range ≥ 2·ATR[1], close in the far half; race = 50% retrace of the 20-bar leg before the climax extreme is retaken; excess over 6 bar-shuffled nulls per dataset).

| Data | SC: AR50-first excess | SC: 1-ATR reversal excess | BC: AR50-first excess | BC: 1-ATR reversal excess |
|---|---|---|---|---|
| CME 5m (6 instruments) | **+0.066 ± 0.025** (n 359; 6/6 positive: ES +0.06, NQ +0.09, GC +0.02, RTY +0.13, YM +0.08, CL +0.07 after null) | +0.057 ± 0.026 | +0.041 ± 0.032 (221) | +0.010 ± 0.034 |
| CME 1H (5) | −0.026 ± 0.032 (219) | −0.055 ± 0.034 | +0.034 ± 0.041 (130) | +0.074 ± 0.044 |
| BTC 1H | −0.035 ± 0.022 (443) | −0.031 ± 0.024 | **−0.065 ± 0.028** (287) | −0.063 ± 0.030 |
| Daily (3) | −0.025 ± 0.076 (38) | −0.107 ± 0.081 | n 14 | — |

**(c) Volume split of the same climax bars** (`wyckB.py climax`; hit − geometry, no null). CME 5m selling climaxes: vr ≥ 2.5 +0.048 ± 0.026 (n 239), 1-2.5 +0.074 ± 0.042 (98), < 1 +0.197 ± 0.082 (22); time-of-day-normalised vr: high +0.076 ± 0.031 (163), mid +0.074 ± 0.042 (98), low +0.055 ± 0.073 (34). CME 1H high-volume SC −0.027 ± 0.031. **High effort does not strengthen the reversal; low-effort climaxes revert at least as much.**

**(d) Does relative volume forecast how far price travels?** (`wyckB.py volvol`; y = log of the next-30-bar range in ATR(14); OLS on the first half, R² on the second half; baseline regressor ln(ATR5/ATR100), the V-axis of REG-1).

| Data | OOS R², ATR ratio | + relative volume | Volume alone |
|---|---|---|---|
| CME 1H (5) | 0.036-0.124 | 0.043-0.153 (+0.003 to +0.029) | −0.002 to 0.009 |
| CME 5m (6, ToD-normalised vr) | −0.003 to 0.052 | −0.003 to 0.024 (no gain; GC worse) | ≈ 0 to 0.035 |
| Daily (3) | 0.003-0.072 | 0.010-0.061 (+0.007 to +0.012; GOOG worse) | −0.006 to 0.009 |

Relative volume adds at most ~3 pp of variance explained at 1H and nothing at 5m. It is not worth a V-axis input beyond REG-1's ATR ratio.

**(e) The two open-source references.** `tianyaphoto/wyckoff` (MIT) supplied the canonical detector parameters (§1.1). `signal-validation/wyckoff-validation` supplied W20. Neither publishes a which-side or reach statistic.

**(f) [B2] Is the 5m climax reversal a time-of-day effect?** (`wyckoff_b2_tools/climax_tod.py`)
- *Why check.* Bar-shuffled nulls destroy the intraday volatility clock. Bars of ≥ 2 ATR cluster at the 08:30 and 09:30 ET opens, where opening reversals are a known pattern, so the "climax" label could just be a time-of-day proxy.
- *Method.* Same detector and race as (b), on CME 5m. A second null permutes bar tuples (gap, H−O, L−O, C−O) only among bars with the same New York clock slot. That keeps the volatility clock and destroys the within-day sequence. 6 surrogates of each kind per instrument.

| | n | Real hit − geo | Excess vs bar shuffle | Excess vs ToD-stratified shuffle |
|---|---|---|---|---|
| Selling climax (AR50 before the low is retaken) | 359 | +0.064 | +0.073 | **+0.068 ± 0.025** |
| Buying climax | 221 | +0.034 | +0.023 | +0.038 ± 0.032 |

Selling climaxes, hit − geometry by ET clock bucket (no null):

| Bucket | Share of all 5m bars | n | Hit − geo |
|---|---|---|---|
| Overnight / other | 67% | 231 | **+0.092 ± 0.031** |
| 08:30-09:30 | 4% | 26 | +0.154 ± 0.092 |
| RTH open 09:30-10:00 | 2% | 48 | −0.026 ± 0.068 |
| RTH 10:00-16:00 | 26% | 54 | −0.018 ± 0.064 |

- *Reading.* The effect survives a time-of-day control. It is concentrated outside regular trading hours, when liquidity is thin, and absent in RTH. That matches the liquidity-provision literature (W29) better than the Wyckoff story of absorption by a composite operator.
- *Consequence for WYK-3.* The ledger bit should be learned per chart and, if TIME-1's session state lands, split into in-session and off-session variants.
- *Caveat.* The CME 5m set covers 3 months. Per-instrument stratified nulls vary (−0.04 to +0.03), so the pooled SE is the honest one.

**(g) [B2] Supply/demand zones: departure strength, time at level, freshness, zone type** (`wyckoff_b2_tools/sdzones.py`; zone rules in §1.10; K = 30)
- *Reach:* is the proximal edge revisited within K bars more than S(d)?
- *Reaction:* at the first, then the second touch (after price left by ≥ 0.5 ATR), a race of +1 ATR away from the proximal edge against a trade-through of the distal edge − 0.1 ATR, minus gambler's-ruin geometry.
- Nulls: 4 bar-shuffled surrogates per series, same detector.

| Group (series) | Reach: real edge vs S(d) (n) | Reach by departure < 2 / 2-3 / ≥ 3 ATR | Reach by base 1 / 2 / 3-6 bars | 1st touch excess (n) | 2nd touch excess (n) | 1st touch excess, continuation vs reversal zones |
|---|---|---|---|---|---|---|
| CME 1H (5) | +0.007 (1,237) | +0.007 / +0.010 / −0.002 | −0.003 / +0.049 / −0.001 | +0.012 ± 0.020 (524) | −0.013 ± 0.036 (166) | +0.055 vs −0.027 |
| CME 5m (6) | +0.016 (4,795) | +0.008 / +0.030 / +0.048 | +0.023 / +0.003 / −0.000 | −0.006 ± 0.009 (2,504) | −0.037 ± 0.016 (909) | +0.000 vs −0.013 |
| BTC 1H | +0.030 (3,265) | +0.050 / +0.022 / −0.034 | +0.021 / +0.033 / +0.063 | +0.022 ± 0.012 (1,444) | +0.022 ± 0.021 (515) | +0.042 vs +0.003 |
| Daily (3) | −0.007 (722) | +0.011 / −0.053 / — | −0.001 / −0.020 / −0.041 | +0.006 ± 0.024 (388) | −0.000 ± 0.043 (118) | +0.059 vs −0.032 |

- *Reach.* Zones are revisited at random-level rates (−0.7 to +3.0 pp). The null-adjusted excess (+1.2 to +5.3 pp) is not a zone effect. In shuffled data, volatility collapses after the large departure bars that inflated ATR, so the null sits below S(d); real volatility clusters. Magnet tests against S(d) are sensitive to this, while race tests (reaction, §2.2, §2.7a-b) are not.
- *Departure strength and base length* have no consistent sign for reach or reaction across groups. "Strength of departure" and "less time at level" are not supported as odds enhancers. At the first touch, weaker departures react slightly better in 3 of 4 groups.
- *Freshness.* First minus second touch is +2.5 / +3.1 / 0.0 / +0.6 pp: at most a small reaction effect on futures.
- *Zone type.* Continuation zones react better than reversal zones in all four groups (+8.2, +1.3, +3.9, +9.1 pp; each ≤ 2σ). That is the opposite of the school's claim, and it is a with-trend effect, consistent with trending at hours-to-years scales (W24).

### 2.8 Net reading for the forecasting problem
- **Where.** Distance, plus the engine's empirical PoT, explains reach. Wyckoff/S&D labels move the odds by no more than ±2-4 pp in any replicated cell, with unstable signs. The engine should not add points for spring context, range edges, touches, equal prints, coil, inducement or pool youth.
- **When.** Range episodes do not change time-to-break beyond the null; extension does not depend on cause length. Timing belongs to the volatility clock (TIME-1/TIME-3, REG-1).
- **How likely.** Calibrated geometry is the right prior. The one timeframe-specific exception found here, the ≤ 5m climax partial reversal, belongs in a per-chart learned feature because it flips sign at 1H+ (WYK-3). [B2] It survives a time-of-day null and lives in thin, off-session hours.
- **[B2] S/D zones.** Departure strength, base length and freshness do not make a zone a bigger draw. This supports ICTPD-1's neutral array density and argues against any "zone strength" bonus.
- **Trader value.** The Wyckoff vocabulary is useful as labels and as per-chart hypotheses with measured rates (WYK-4), not as weights.

---

## 3. Engine gap analysis (`baseline_v2.pine`)

| Concept | Status | Line refs | What the engine does / what differs | Covered by |
|---|---|---|---|---|
| Trading range detection (frozen box or climax-anchored), creek/ice | **partial** | 708-782 (`f_structure` rolling dealing range `rngH/rngL` that follows the leg); 1111-1137 (EQ merge at `eqTol` 0.10 ATR); 1230-1251 (stacks within `clusATR` 0.75 ATR, outermost = draw) | No horizontal multi-touch or climax-anchored range state. Range edges appear as several stacked pivots; touches 0.10-0.25 ATR apart stay separate pools. No range label | WYK-4 (labels only); REG-2 (regime state) |
| Range-context selection | **wrong (D gates selection everywhere)** | 1891-1895 (`drawD`, `dirSide`), 1975 (eligibility), 1948 (`evaluate` with `drawD`) | Inside ranges D has no skill (A `tr_first`; ICTS-1; REG finding 4) | **[SUPERSEDED]** REG-3 (efficiency-gated D), ICTS-1, BIAS-2 |
| Spring / UT / UTAD as a D vote | **wrong** | 1579-1582 (`liqEvt`: a close back inside a swept pool votes reversal, `−side·tier`, `wL` 0.30, `liqHL` 24); 892-895 (`induceBar` counts mini-springs) | Every rejected raid is a reversal vote. Evidence: no reversal edge in range context (§2.2, §2.7a) and none overall (§2.6) | **[SUPERSEDED]** ICT-9 (neutral REJECT; merges ICTS-2 / BIAS-4) |
| Failed breakout by close (bust) | **partial** | 1646-1661 (breakers only from OBs that took liquidity), 1599-1627 (iFVG on a close through an FVG) | No range-level bust state. Evidence weak and mixed (`upthr_cl` +0.09 to +0.16; `spring_cl` ≈ 0) | WYK-4 (event + honesty rate) |
| SC / BC climax, AR, ST | **missing** | bar volume unused outside the profile (978-1015, 1900-1909, 1945-1947, 2250-2287) | No climax events. Evidence: 5m partial reversal (§2.7b), none at 1H+, continuation on BTC 1H; volume irrelevant | WYK-3 (learned bit), WYK-4 (labels) |
| Tests of a pool | **present, unsupported weight** | 650-656 (`track`, `testATR` 0.30, ≥ 3 bars, `gap > 0`); 682 (`0.35·min(tests,6)`) | Up to +2.1 to x. No reach effect (§2.4) | **[SUPERSEDED]** ICT-10 / SMC-3 |
| Equal highs/lows | **present, overweighted** | 1111-1137; 682 (`0.9·eqCount`) | Largest single magnitude term; EQ pools are not bigger draws | **[SUPERSEDED]** ICT-10 / OF-3 |
| Coiling (TradeAxis "density") | **present, non-predictive** | 888-891 (`coilScore`); 683 (`0.25·coil`), 687 (`0.30·coil`); birth reads at 1703, 1744, 1762, 1774, 1874, 1884 (`[offset+1]` or `[2]`, correct) | Sign-unstable ≤ 1.6 pp (§2.4). **Bug:** 1848 (registry re-entry) and 1862 (HTF FVG) pass the *current* `coilScore`. 1656 (breakers) also passes the current value, which is defensible because the breaker level is created on that bar | WYK-1 |
| Inducement sweeps | **wrong (saturated constant)** | 892-895; 683 (`0.15·induce`), 687 (`0.20·induce`); same birth-value bug at 1848, 1862 | `indScore` ≥ 2/3 on 86-98% of bars (22 series) | WYK-1 |
| Freshness / maturation of liquidity | **wrong (shape, scale)** | 668-671 | Ramp 0.35 → 1 with τ = 37.5 bars, then 600-bar half-life. Young-pool penalty ~4 points vs ~1 pp measured; decay consistent (§2.4) | WYK-2 (also adopted by OF-3) |
| Freshness of S/D zones (arrays) | **present** | 673 (array half-life), 1566-1577 (partial-fill crop), 1693-1700 / 1736-1741 (skip mitigated OBs), 1626 / 1660 (`trackAge`) | Consistent with the S/D fresh-zone rule. [B2] Fresh minus second touch is 0 to +3 pp for reaction (§2.7g) and nothing for reach. Keep as is; no extra weight | — |
| Departure strength (S/D) | **present, unsupported (sign unstable)** | 910-912 (`fvgQBase`), 1870-1871, 1880-1881 (FVG quality), 1692, 1735 (OB quality), 687 (`0.5·qual`) | ICTPD-1: larger displacement lowers fill (BTC 1D). [B2] Zone reach by departure tercile has no consistent sign across 4 data groups (§2.7g). A positive `0.5·qual` density weight has no support | **[SUPERSEDED]** ICTPD-1 (neutral array density) |
| Time at level / base length | **missing (correct)** | — | OBs are single candles. [B2] Base length 1 / 2 / 3-6 shows no consistent effect on reach or reaction (§2.7g). Leave missing | — |
| Zone type: reversal (DBR/RBD) vs continuation (RBR/DBD) | **missing** | OBs from the BOS leg (1663-1748) mix both | [B2] Continuation zones react 1-9 pp better at the first touch in 4 of 4 groups (weak; reaction, not reach). No score change; at most a ledger row | ICTPD-8 measurement-only checks, if built |
| Partial rise / decline | **missing** | — | Bulkowski's rates are geometry. Leave missing | — |
| SOS / SOW, JAC, LPS / LPSY, BUEC | **partial** | 1542-1547 (`bosUp/bosDn`: close beyond the last swing), 897-904 (displacement), 1663-1748 (OB from the BOS leg ≈ LPS zone) | SMC restatement; no range-midpoint rule. No evidence the refinement helps (§2.2, §2.7a) | WYK-4 (labels) |
| Composite operator | n/a | — | Unfalsifiable | — |
| Cause and effect (P&F count), measured move | **missing** | — | No evidence. Leave missing | — |
| Effort vs result (volume, spread, Weis wave) | **missing** | volume only in the profile path cost (1945-1947) and LVNs (2250-2287) | Null at 5m, 1H and daily (§2.6, §2.7c-d). Do not add volume weights | WYK-3 replaces A's volume features with a price-only climax bit |
| Throwback to a broken edge | **missing** | swept pools are deleted (1583-1589) | Throwbacks occur at random-level rates. No special handling | — |
| Per-regime accuracy | **missing** | ledger 1426-1499; panel 2374-2434 | No in-range vs trend split | **[SUPERSEDED]** REG-2 |

**[B2] Line refs re-verified.** B2 re-read every cited line in `baseline_v2.pine`, which is byte-identical to `indicators/dol_engine.pine`: 668-671, 681-687, 888-895, 1066-1079, 1211-1225, 1253-1263, 1314, 1470-1476, 1580-1582, 1656, 1703, 1744, 1762, 1774, 1848, 1862, 1874, 1884, 1894-1895, 1975. All match.

**Corrections to A's gap table.** The `liqEvt` lines are 1580-1582 (1579 is the comment). The coil block is 888-891 and inducement 892-895. Breakers (1656) were missing from A's list of births using the current coil. A's WYK-4 ledger plan (reuse `Trial` with `grp = 5` and `f_book`) would index past the 5-element `stN/stK/stPE/stPV/stMae/stBars` arrays in `f_book` (1470-1476: `for g in array.from(t.grp, 4)`), a runtime error, and would also pollute `roll50`, `ttHit`, `raceSt` and `cluSt`; it also collides with ICTPD-1, which makes index 5 the ALL row. WYK-4 below uses a separate resolver.

---

## 4. Proposals (best first)

Selection rule: only changes this domain's evidence supports and the ledger can measure; subtraction first. Each proposal names its sibling overlaps so nothing is implemented twice.

### WYK-1 (P1, scoring, S) · Coil and inducement: neutral constants at their population means, birth-value bug fix, de-saturated display [A, CORRECTED and narrowed]

**Why.**
- `indScore` is a constant (≥ 2/3 on 86-98% of bars across 22 series in two implementations). `coilScore` has no stable relation to reach: −1.6 to +1.1 pp across three studies with the sign flipping (§2.4).
- Together they control up to 0.40 of liquidity density and 0.50 of array density (0.60 under ICTPD-1's `0.40 + 0.30·coil + 0.30·induce`). With `wDens` 20 that is up to **5.5 points** for a pool and **7-9 points** for an array of pure noise, more than `hyst`.
- **[B2, corrected]** The siblings disagree on these terms:
  - ICT-10 rewrites the liquidity `x` term but **keeps** `0.25·coil + 0.15·induce`.
  - OF-3 follows A's original WYK-1. It **drops** both terms and rescales the rest to `dens = 1 − e^(−x)` (B1 wrote that OF-3 keeps them; it does not).
  - ICTPD-1 **raises** the array weights to `0.30·coil + 0.30·induce`.
  - So two of the three keep or amplify the noise, and the third removes it while changing the scale. WYK-1 settles this with one rule that works under any of them: wherever a formula reads `coil` or `induce`, read the neutral constant instead. A's EQ/tests changes are dropped here in favour of ICT-10 / OF-3.
- **[CORRECTED vs A]** Do not delete the terms: replace them with their population means. That keeps each family's mean density, and so the liquidity-vs-array balance the selection relies on, while removing the variance. Deleting them (A's spec) would shift every family by a different constant (−0.28 for liquidity, −0.35 or −0.44 for arrays).
- Registry re-entries (1848) and HTF FVGs (1862) use the current bar's coil and inducement: an outright bug in both modes.

**Spec.**
1. Input (G_SCORE, after 140), hidden from the legend like the other inputs:
   ```pine
   string densIn = input.string("Neutral", "Coil / Inducement Weight", options = ["Neutral", "Classic"], group = G_SCORE, display = display.none,
     tooltip = "Neutral: coiling and inducement are shown but scored at their typical values (tested on 22 series: they do not change how often a level is reached). Classic: the original live weights.")
   ```
2. Constants (after line 307): `const float COIL0 = 0.55` and `const float IND0 = 0.93` (medians of the per-series means of the engine's own definitions, §2.4).
3. `evaluate` (661-696), before 681:
   ```pine
   float cz = densIn == "Classic" ? this.coil : COIL0
   float iz = densIn == "Classic" ? this.induce : IND0
   ```
   Then use `cz` / `iz` in place of `this.coil` / `this.induce` at 683 and 687, and in ICT-10's and ICTPD-1's replacement lines if they land first.
4. **Birth-value fix (both modes).**
   - `type Ext` (365-372): add `float coil = 0.55` and `float ind = 0.93`.
   - `f_pushExt` (1211-1225), inside `if not dup`:
     ```pine
     int   off = bar_index - nz(aBar, bar_index)
     float cB  = off >= 0 and off <= 450 ? nz(coilScore[off], COIL0) : COIL0
     float iB  = off >= 0 and off <= 450 ? nz(indScore[off], IND0) : IND0
     reg.push(Ext.new(px, isHigh, src, f_x(nz(aBar, bar_index)), nz(aBar, bar_index), nz(prom), hlm, cB, iB))
     ```
   - 1848: pass `e.coil, e.ind` instead of `coilScore, indScore`.
   - 1862: `int offH = bar_index - nz(aHF, bar_index)`, then pass `offH <= 450 ? nz(coilScore[offH], COIL0) : COIL0` and the same for `indScore`.
   - Compile notes. A history offset may be a series int; the buffer is `max_bars_back = 500` (line 32), and the docs say "If a script references values beyond the historical buffer's limit, it causes a runtime error" (`writing_scripts/limitations.md` 375), hence the ≤ 450 guard. `anchorMax` is capped at 450 by its input (line 100), but PD/PW/session anchors can be farther, so the guard is needed. Referencing a global series' history inside a function called conditionally is fine because the global itself is evaluated on every bar.
5. **De-saturated display** (global scope, SERIES section after 895), shown in the HUD tooltip for spec parity ("coiling and inducement sweeps") and feeding ICT-1 bits:
   ```pine
   float coilPct = nz(ta.percentrank(overlap, 300)) / 100.0      // ta.percentrank(source, length): length is series int (reference/ta.md 1155-1166).
                                                                 // [B2] 300, not 500: a 500-bar lookback sits exactly on max_bars_back = 500 (line 32)
   float aPrev   = nz(atr[1], atr)
   bool  sweep20 = (high > hh20[1] + 0.10 * aPrev and close < hh20[1]) or (low < ll20[1] - 0.10 * aPrev and close > ll20[1])
   float sweepN  = math.sum(sweep20 ? 1.0 : 0.0, densLen)
   ```
   Tooltip text: `Coil pctl 71 · sweeps 2 (shown, not weighted)`. The `Level` fields `coil` / `induce` can carry `coilPct` / `min(1, sweepN/2)` at birth instead of the saturated values (same birth offsets as now).
6. **ICT-1 bits** (if the candidate ledger lands): `COIL` = birth `coilPct ≥ 0.67`; `SWEPT` = birth `sweepN ≥ 2`. Zero prior, gated learned lift.
7. README: the Density row must say that equal prints, tests, coiling and inducement are measured and shown but not weighted by default.

**Spec parity.** The reference spec says a level "scores significantly higher" after equal highs/lows or range-bound density. Under Neutral, the engine still computes, shows and logs both inputs, and with ICT-1 the score *does* rise on any chart where this chart's own ledger shows the effect (|z| ≥ `featZ`, n ≥ 100). That is the honest form of the spec claim. Classic keeps the literal one.

**Measurement.** Neutral vs Classic A/B on overall EDGE z, the per-family "hit vs expected" rows (ICTPD-1 step 6) and the target switch rate (SMC-2). Expected: EDGE unchanged or slightly better, fewer switches.

**Evidence.** Moderate: three independent implementations (A, B, `quant_regime`), 22+ series, null-controlled, consistent saturation and sign-unstable coil. [B2] Supported for arrays by §2.7g: zone strength attributes do not change reach.

**Risk.** Low. The Classic option keeps the original. Scores of individual levels move by at most ±5.5 (pools) / ±9 (arrays) points; family means are unchanged.

### WYK-2 (P2, scoring, S) · Liquidity freshness: drop the young-pool ramp, keep the slow decay, learn age per chart [A, CORRECTED rationale]

**Why.**
- [CORRECTED] Age *does* matter a little: pools 5-10 bars old are reached 0.6-1.9 pp less than a random level, and intraday pools older than ~300-500 bars 3-8 pp less; middle ages have no stable sign (§2.4).
- The ramp (671) gives a 5-bar-old pool 0.43 vs 0.85 at 100 bars: ~4.2 points, equal to `hyst`, worth ~15 pp of reach on the proximity scale, for a ~1 pp effect. It delays switching to new nearer pools by 30-40 bars and turns structure changes into target lag.
- The decay factor `0.5^(age/(4·halfLife))` (0.56 at 500 bars, 0.32 at 1,000) is in proportion with the old-pool deficit, so it stays.

**Spec.**
- Input (G_SCORE, after 138): `string freshLiq = input.string("Flat", "Liquidity Freshness", options = ["Flat", "Maturing"], group = G_SCORE, display = display.none, tooltip = "Flat: a pool starts at full freshness and fades slowly with age (tested: very young pools are reached only ~1 pp less often, far less than the old ramp's penalty). Maturing: the original ramp.")`.
- `evaluate` 669-671:
  ```pine
  if this.isLiquidity()
      float dec = math.pow(0.5, age / (4.0 * halfLife))
      this.fresh := freshLiq == "Flat" ? dec : (0.35 + 0.65 * (1.0 - math.exp(-age / (0.25 * halfLife)))) * dec
  ```
- ICT-1 bits (zero prior): `YOUNG` = `bar_index − bornBar ≤ 2·pivLen` (chart pools; for HTF/STF use age/hlMult like line 667); `STALE` = age (in `hlMult`-scaled bars) > 300. The ledger then learns the −1 pp / −3 to −8 pp effects per chart; on daily equities it can learn the opposite.
- `orderflow_micro.md` OF-3 adopts the same "Flat" line: implement once.

**Measurement.** Flat vs Maturing on DOL HIT %, EDGE z, BARS→HIT and (SMC-2) the switch rate.

**Evidence.** Moderate (A: 36,724 checkpoints; B: ~190,000 checkpoints in 5 data groups; cluster SEs).

**Risk.** Very low; a pure removal of an oversized shape.

### WYK-3 (P3, statistics-ledger, S) · Climax-bar reversal as a learned, timeframe-scoped ledger feature (price only) [NEW-B; replaces A's WYK-5 volume features]

**Why.**
- At ≤ 5m, after a price climax, the 50% retrace of the leg comes before the extreme is retaken **+6.6 ± 2.5 pp** more often than in nulls (selling climax, 6/6 CME instruments) and +4.1 ± 3.2 pp (buying climax). After a confirmed AR, the climax extreme is then retaken first +4.5 to +5.4 pp (§2.7a-b). This matches strong minute-scale literature (W8, W9, W24).
- At 1H it vanishes, and on BTC 1H it flips to continuation (−3.5 / −6.5 pp). A fixed weight would be wrong on half the charts; a gated learned lift is right on all of them.
- [B2] It survives a time-of-day-stratified null (+6.8 ± 2.5 pp) and is concentrated in thin hours: overnight +9.2 pp, 08:30-09:30 ET +15 pp, RTH −2 pp (§2.7f). This is the liquidity-provision reversal (W29), so it should be expected where liquidity is thin, not wherever a "climax" is drawn.
- Volume adds nothing (§2.6, §2.7c), so the feature needs no volume and works on symbols without it. That makes A's three volume features (`vrLast`, volume-gated `climax`, `absorb`) unnecessary.

**Spec** (requires ICT-1's candidate ledger; otherwise skip).
- Global series (SERIES section; `ta.*` at global scope):
  ```pine
  float cxA  = nz(atr[1], atr)
  bool  scB  = low < ta.lowest(low, 20)[1] and high - low >= 2.0 * cxA and close - low >= 0.5 * (high - low)
  bool  bcB  = high > ta.highest(high, 20)[1] and high - low >= 2.0 * cxA and high - close >= 0.5 * (high - low)
  float legH = ta.highest(high, 21)
  float legL = ta.lowest(low, 21)
  ```
- State (STATE section): `var int cxBar = na`, `var int cxDir = 0`, `var float cxExt = na`, `var float cxMid = na`. On confirmed bars (engine step 1, 1534-1547): if `scB` then `cxBar := bar_index`, `cxDir := 1`, `cxExt := low`, `cxMid := low + 0.5 * (legH - low)`; mirror for `bcB` with `cxDir := -1`.
- Bits at probe snapshot, when `bar_index - cxBar <= 10`:
  - `CLXREV`: `lv.side == cxDir` and the near edge lies between `close` and `cxMid + 0.5·atr` on that side (a pool inside the climax leg, toward the reversal);
  - `CLXEXT`: `lv.side == -cxDir` and the near edge is within 1 ATR beyond `cxExt` (the retest-through-the-extreme pool, as in the AR race).
- Zero prior, ICT-1's gate (`|z| ≥ featZ`, `n ≥ 100`), bounds ±`featB`.
- [B2] Session split, only if TIME-1's session state exists. Set `CLXREV` only when the climax bar is outside the main session (`not inKZ`-style flag at `cxBar`, stored as `var bool cxOff`), so the bit learns the thin-hours effect without being diluted by RTH climaxes. On charts above 1H or without sessions, ignore the flag.
- Bit budget: two bits (ICT-1 grows from 16 to 18). Do not add volume variants: volume does not change the effect (§2.7c, W27).
- Optional Terminal marker `SC` / `BC` (tiny label, ring buffer shared with WYK-4).

**Measurement.** ICT-1's per-bit lift and z. Expected: positive CLXREV on ≤ 5m index futures, ≤ 0 on 1H+ and crypto 1H.

**Evidence.** Moderate at 5m (B, 6 instruments, null-controlled; literature strong at ≤ 1 h); none or opposite at 1H+.

**Risk.** Feature-count creep in ICT-1 (16 → 18 bits); keep to these two.

### WYK-4 (P3, visual-ux / alerts, M) · Wyckoff range layer: canonical range box, Spring / UTAD / SOS / SOW / AR labels and alerts, zero forecast weight, per-chart honesty rates [A's WYK-3 UX part + WYK-4, CORRECTED]

**Why.**
- Traders read ranges in Wyckoff terms and look for springs and UTADs. The events do not predict the next draw (§2.2, §2.7a), so the honest product shows them with *their measured rate on this chart against geometry*, which competitors that paint "SPRING ✓" do not.
- **[SUPERSEDED parts of A's WYK-3/WYK-4]**: draw-neutral selection inside ranges → REG-3 (efficiency gate) / ICTS-1; in-range vs trend ledger split → REG-2; zero raid votes inside ranges → ICT-9 (REJECT neutral everywhere).

**Spec.**
- Inputs (new group "Wyckoff", all `display = display.none`): `useWyk` (false), `wykVol` (true: use the volume gate when `hasVol = ta.cum(nz(volume)) > 0`), `wykBox` (false: draw the range box in Clean style).
- **Detector** (confirmed bars, O(1) per bar, no loops; §1.1 climax-anchored parameters as defaults):
  - State: `var int wM = 0` (0 idle, 1 climax, 2 range); `var int wD = 0` (+1 accumulation, −1 distribution); `var float wX, wY, wLo, wUp`; `var int wCi, wYi, wRs, wFail, wTi`; `var bool wReb, wAway, wTp`; `var float wTx`.
  - Idle → climax: `scB`-like bar with `close < ta.sma(close, 50)` (prior downtrend), range ≥ 2.0·ATR[1], and `vr ≥ 2.5` when `wykVol and hasVol` (mirror for BC).
  - Climax → range: extend `wX` on deeper extremes before the rebound (≤ 10 bars); rebound ≥ 2.0·ATR within 10 bars; confirm on a close 1.0·ATR back from the rebound extreme; abandon after 30 bars or on a deeper extreme after the rebound; width 2-8·ATR else abandon. Emit **AR**.
  - Range: `confirmed = bar_index - wRs >= 15`. Fail on 3 consecutive closes > 1.5·ATR outside, or after 300 bars. Spring/UTAD: penetration ≤ 1.5·ATR, a close back inside within 3 bars, re-armed by a close ≥ 1·ATR off the edge. SOS/SOW: a close beyond by ≥ 0.5·ATR (and `vr ≥ 1.5` when gated); the range then ends.
  - [B2] Refinements from the published detectors (§1.1, §1.4):
    - *Phase A extension.* Before the first ST, a swing beyond the AR edge moves `wUp`/`wLo` outward and is not an upthrust; a deeper climax-side extreme moves `wX`. Re-check the 8·ATR height cap after each extension and abandon the candidate as a trend if it fails.
    - *ST.* A confirmed swing (reuse the engine's `pl` / `ph`, 879-880, so no new `ta.*` call is needed) inside the 30% of the box nearest the climax edge, counted up to 3. Input `wykNeedST` (default true): springs and UTADs count only after ≥ 1 ST, so Phase B shakeouts are not labelled as springs.
    - *Climax-volume penetration.* With `wykVol and hasVol` and `vr ≥ 2.5` on the penetrating bar, the event is tagged `BREAK (heavy vol)`, not `SPRING`. That follows the SRFX rule and keeps the heavy-volume shakeout as its own honesty row.
    - *Labels.* Use words, never "#1/#3", because the type numbers are inverted between sources: `SPRING · light vol`, `SPRING · heavy vol`.
    - *Cooldown.* 15 bars after a failure before a new climax can start a range.
  - Name the range-edge pools: when a range is confirmed, set a new `Level` field `bool rngEdge` on the nearest BSL/SSL within `0.25·atr` of `wUp` / `wLo` (`f_findLiq`, 1090-1107); `f_levelName` (518-530) returns `"RANGE H"` / `"RANGE L"` for them. **No score change.**
- **Honesty ledger** (separate from `f_book`; see the §3 correction):
  ```pine
  type WEvt
      int   kind      // 0 AR · 1 SPRING · 2 UTAD · 3 SOS/SOW
      int   side      // +1 target above
      float tgt
      float stp
      float p0        // geometry (close - stp) / (tgt - stp)
      int   bar0
  var array<WEvt>  wOpen = array.new<WEvt>()
  var array<float> wN = array.new<float>(4, 0.0), wK = array.new<float>(4, 0.0), wP = array.new<float>(4, 0.0)
  ```
  Targets: AR → climax extreme (stop = AR extreme); SPRING → range high (stop = spring low); UTAD → range low; SOS/SOW → measured move (stop = opposite edge). Resolve on confirmed bars: strict trade-through of `tgt` → win, of `stp` → loss, both in one bar → drop, `bar_index - bar0 >= H` → drop. On a decision: `wN += 1`, `wK += win`, `wP += p0`. Cap 20 open events.
- **Display** (Terminal style only, ring buffer of 10 tiny labels like the ghosts, 1253-1263): `SPRING · opp. edge first 29% vs 28% geo (n 14)`, greyed below n 20. Clean style: nothing unless `wykBox`, which draws one dashed box at 88% transparency extended on `tailBar` like the iFVG boxes.
- **Alerts**: `alert("Wyckoff ▸ SPRING at RANGE L · opposite edge first " + rate + " here vs " + geo + " geometry (n " + n + ") · " + syminfo.ticker, alert.freq_once_per_bar_close)`, and one `alertcondition` "Wyckoff Event".
- **Budget.** One box, ≤ 10 labels, ≤ 20 open records, no `request.*` calls, no loops beyond the ≤ 20-record resolver.

**Measurement.** The ledger rows are the measurement. An event type with a stable per-chart excess can be promoted into ICT-1 as a bit.

**Why this beats the published Wyckoff scripts** [B2]. The best of them (WillyAlgoTrader) already shows per-chart counts such as "Spring → SOS follow-through" and "SOS → target hit rate". Without a geometry baseline those counts mislead, because a raw rate mostly reflects where price sits in the box. After a spring the top is taken first 12-37% of the time, against 16-26% from geometry alone; partial declines "work" 70-93% of the time, against 71-81% from geometry (A, §2.2). Showing `rate vs geometry (n)` is the differentiator.

**Evidence.** Strong-to-moderate for "no edge" (A and B, three detector families, 19 series, null-controlled; §2.2, §2.7a). Weak for the UX value.

**Risk.** Label clutter (Terminal only, off by default); small-n rates (shown with n, greyed below 20). The climax state machine needs care with the `var` resets; it is O(1).

### Superseded, merged or rejected (with reasons)

| Item | Disposition |
|---|---|
| A's WYK-3 draw-neutral selection inside ranges (`trDK`) | **[SUPERSEDED]** by REG-3 (efficiency-gated D, measured +9-12 pp first-touch intraday) and ICTS-1 / BIAS-2. A box-based gate adds a lagging detector for the same effect |
| A's WYK-3 regime-split ledger | **[SUPERSEDED]** by REG-2 (RANGE / MIXED / TREND± and VOL classes) |
| A's WYK-4 "inside ranges raid events add 0 to `liqEvt`" | **[SUPERSEDED]** by ICT-9 (REJECT neutral everywhere, HOLD HTF-conditioned) |
| A's WYK-1 EQ and tests reductions | **[SUPERSEDED]** by ICT-10 / OF-3 / SMC-3; WYK-1 now covers only coil, inducement and the bug |
| A's WYK-5 volume features (`vrLast`, volume-gated climax, `absorb`) | **[CORRECTED → WYK-3]**: volume does not modulate outcomes at 5m, 1H or daily; the price-only climax bit carries the only signal |
| "Spring → target the opposite edge" as a rule or bonus | Rejected: excess +0.007 to +0.022 (B, canonical) and −0.075 to +0.016 (A, rolling) |
| Range-edge magnitude bonus; "the more-tested edge breaks first" | Rejected: 2 / 3 / 4+ touches +0.000 / −0.031 / −0.084 |
| Climax → AR50 as a *fixed* target or bonus | Rejected as fixed: TF-dependent sign (§2.7b); learned only (WYK-3) |
| P&F count and measured-move targets as candidate levels | Rejected: no published count test, measured move at geometry rates, and no liquidity behind them |
| Throwback / BUEC targets after a breakout | Rejected: random-level rates (0.870 vs 0.872) |
| Partial rise / decline as a side predictor | Rejected: geometry |
| S/D "time at base" and multi-candle base zones | Rejected: no evidence; arrays reach at random-level rates |
| "Busted range" bonus | Rejected: `upthr_cl` asymmetric and sign-mixed per dataset; WYK-4 measures it per chart if wanted |
| Phase A-E labelling | Rejected: labels are provisional until markup; no measurable content. WYK-4 shows events, not phases |
| Relative volume as a PoT / volatility key | Rejected: ≤ 3 pp OOS R² at 1H, none at 5m (§2.7d); REG-1's ATR ratio suffices |
| [B2] S/D "zone strength" bonus (departure strength, short base, reversal type) | Rejected: no consistent reach effect across 4 data groups (§2.7g); reversal zones react *worse* than continuation zones |
| [B2] Freshness bonus for arrays beyond the current half-life | Rejected: fresh minus tested is 0 to +3 pp for reaction only (§2.7g) |
| [B2] "Effort vs result" volume weights in either direction | Rejected: the published sign conflicts (CHN 1994 vs Cooper 1999, W27), and B's data show no volume effect (§2.6, §2.7c) |
| [B2] Spring type numbers (#1/#2/#3) in labels | Rejected: the numbering is inverted between sources (§1.4); label by volume class in words |

---

## 5. Notes for implementers
- **Order.** WYK-1 and WYK-2 are independent S-sized edits in `evaluate` (661-696), `Ext`, `f_pushExt` and two call sites; ship them with ICT-10 and ICTPD-1 so `evaluate` is edited once. WYK-3 needs ICT-1. WYK-4 is self-contained.
- **One `evaluate` edit.** If ICT-10 (`magModel`), ICTPD-1 (array density) and WYK-1 land together, the final lines are:
  - liquidity: `x = ev ? 1.2·tier + 0.4·min(1, prom/3) : <classic x>`; `dens = 0.60·(1 − e^(−x)) + 0.25·cz + 0.15·iz`;
  - arrays: `dens = 0.40 + 0.30·cz + 0.30·iz` (ICTPD-1), which is the constant 0.844 under Neutral.
  - [B2] If OF-3's form is chosen instead of ICT-10's (`dens = 1 − e^(−x)` with no coil/induce terms), the coil/induce noise is already gone for pools.
    - For a chart pivot (tier 0.25) with prominence 1-3 ATR and no stack, the density level is similar either way: about 0.49-0.58 with ICT-10 plus the neutral constants, about 0.43-0.67 with OF-3.
    - OF-3 doubles the spread due to prominence, and it lets stacks add up to +0.9 to `x`.
    - Pick ICT-10's or OF-3's liquidity line, not both. Whichever is picked, arrays still need `cz`/`iz` under ICTPD-1.
- **Compile notes** (doc-grounded): `ta.percentrank(source, length)` and `math.sum(source, length)` take a series int length (`reference/ta.md` 1155-1166; math reference). History offsets with a series int are legal within `max_bars_back = 500`. New `ta.*` calls go at global scope (SERIES), not inside the `if barstate.isconfirmed` block. New inputs use `display = display.none` (the overhaul's legend fix). Functions cannot reassign fundamental-type globals, so WYK-4's state stays in `var` globals updated at the call site or in arrays (`bias_dol.final.md` row 18).
- **Non-repainting.** Every proposal runs on confirmed bars with `[1]` history; none adds a `request.*` call.
- **Measuring.** The engine's EDGE baseline (`f_potBase` 1314-1322; panel 2385-2402) is the same distance-matched baseline used in §2.3-2.4 and §2.7, so A/B results are directly comparable to the numbers here.

---

## 6. Sources

Wyckoff method (definitions):
- Wyckoff Analytics, "Wyckoff Method" (Pruden/Fraser school; events, phases, schematics, P&F count guide): https://www.wyckoffanalytics.com/wyckoff-method/ [not re-fetched]
- Villahermosa, R., tradingwyckoff.com (method guide, spring/shakeout, cause and effect, limitations): https://tradingwyckoff.com/en/wyckoff-method/ · https://tradingwyckoff.com/en/spring-shakeout/ [not re-fetched]
- Fraser/Evans spring #1/#2/#3: https://www.financial-spread-betting.com/trading/wyckoff-spings-upthrusts.html
- StockCharts ChartSchool, P&F price objectives (horizontal counts) and Wyckoff tutorial: https://chartschool.stockcharts.com/table-of-contents/chart-analysis/point-and-figure-charts/p-and-f-price-objectives/p-and-f-price-objectives-horizontal-counts · https://chartschool.stockcharts.com/table-of-contents/market-analysis/wyckoff-analysis-articles/the-wyckoff-method-a-tutorial
- LuxAlgo Library (accumulation schematic, Weis waves, VSA, P&F cause counting): https://www.luxalgo.com/library/concept/wyckoff-accumulation-schematic/ · https://www.luxalgo.com/library/concept/point-and-figure-cause-counting.md
- ATAS, Weis waves: https://atas.net/blog/how-to-use-the-weis-waves-indicator/
- Evidence Finance, "Wyckoff: academic & empirical evidence" (critical overview): https://evidencefinance.neocities.org/wyckoff

Algorithmic implementations (parameters learned, no code copied):
- `tianyaphoto/wyckoff` (MIT; climax-anchored detector, `config/params.yaml`): https://github.com/tianyaphoto/wyckoff
- `signal-validation/wyckoff-validation` (vendor validation files): https://github.com/signal-validation/wyckoff-validation
- FibAlgo "Wyckoff Spring & Upthrust": https://www.tradingview.com/script/H3zpGMiK-Wyckoff-Spring-Upthrust-FibAlgo/
- fis_wse "Wyckoff Phase Classifier": https://www.tradingview.com/script/9ap94IDt-Wyckoff-Phase-Classifier/
- trendcraft `wyckoffPhases`: https://github.com/sawapi/trendcraft/blob/97586812ba94ce071dd5390b739c5986ab16e010/packages/core/docs/API.md
- MQL5 article 22628 (Wyckoff accumulation/distribution EA): https://www.mql5.com/en/articles/22628
- StockSharp Volume Climax Reversal: https://doc.stocksharp.com/en/api-examples/0115_Volume_Climax_Reversal
- ta4j Wyckoff package: https://github.com/ta4j/ta4j-wiki/blob/64256353c2402d60dc438d23ef36d9c17f8440cb/VWAP-Support-Resistance-and-Wyckoff.md
- [B2] FibAlgo "Wyckoff Selling & Buying Climax": https://www.tradingview.com/script/JoOjpvrc-Wyckoff-Selling-Buying-Climax-FibAlgo/ · FibAlgo "Wyckoff Accumulation & Distribution": https://www.tradingview.com/script/HzH1gd30-FibAlgo-Wyckoff-Accumulation-Distribution/
- [B2] WillyAlgoTrader "Wyckoff Range Engine" (Phase A extension, ST zone, spring score, per-chart counts): https://www.tradingview.com/script/mAqEoupb-Wyckoff-Range-Engine-WillyAlgoTrader/
- [B2] SRFX "Wyckoff Phase & Volume Analyzer" (non-climax-volume springs, invalidation rules): https://www.tradingview.com/script/dP3XYAR4-Wyckoff-Phase-Volume-Analyzer-SRFX/
- [B2] AlphaExtract "Wyckoff Event Detection": https://www.tradingview.com/script/CReJpjHe-Wyckoff-Event-Detection-Alpha-Extract/
- [B2] Wyckoff Analytics, "Identifying Wyckoff Springs with Algorithms" (rules, no statistics): https://www.wyckoffanalytics.com/identifying-wyckoff-springs-with-algorithmic-trading-strategies/

Quantitative evidence:
- Lo, A., Mamaysky, H., Wang, J. (2000). Foundations of Technical Analysis. *J. Finance* 55(4):1705-1765. https://www.nber.org/papers/w7613
- Bulkowski, T., thepatternsite.com ([B2] re-read: rectbots, recttops, partdecline, partrises, BustRectangles, volbkout, studystudy): https://thepatternsite.com/rectbots.html · https://thepatternsite.com/recttops.html · https://thepatternsite.com/partdecline.html · https://thepatternsite.com/partrises.html · https://thepatternsite.com/BustRectangles.html · https://thepatternsite.com/volbkout.html · https://thepatternsite.com/studystudy.html · (not re-read) https://thepatternsite.com/VolumeStudy.html · https://www.thepatternsite.com/TsversusWidth.html
- [B2] Karpoff, J. (1987). The Relation between Price Changes and Trading Volume: A Survey. *JFQA* 22(1):109-126. https://ideas.repec.org/a/cup/jfinqa/v22y1987i01p109-126_01.html
- [B2] Conrad, J., Hameed, A., Niden, C. (1994). Volume and Autocovariances in Short-Horizon Individual Security Returns. *J. Finance* 49(4):1305-1329. https://ideas.repec.org/a/bla/jfinan/v49y1994i4p1305-29.html
- [B2] Cooper, M. (1999). Filter Rules Based on Price and Volume in Individual Security Overreaction. *RFS* 12(4):901-935. https://ideas.repec.org/a/oup/rfinst/v12y1999i4p901-35.html · Goyal (NBER 2004 conference paper): https://users.nber.org/~confer/2004/mmsu04/goyal.pdf
- [B2] Nagel, S. (2012). Evaporating Liquidity. *RFS* 25(7):2005-2039. https://www.nber.org/papers/w17653
- [B2] Zhu, H., Jiang, Z.-Q., Li, S.-P., Zhou, W.-X. (2015). Profitability of simple technical trading rules of Chinese stock exchange indexes. arXiv 1504.04254.
- [B2] StockCharts ChartSchool, P&F price objectives (counts are rough estimates): https://chartschool.stockcharts.com/table-of-contents/chart-analysis/point-and-figure-charts/p-and-f-price-objectives
- Campbell, J., Grossman, S., Wang, J. (1993). Trading Volume and Serial Correlation in Stock Returns. *QJE* 108(4):905-939. https://www.nber.org/papers/w4193
- Christensen, K., Oomen, R., Renò, R. The drift burst hypothesis. *J. Econometrics*; arXiv 2601.08974 (full text read by B).
- Zawadowski, A., Andor, G., Kertész, J. (2006). Short-term market reaction after extreme price changes of liquid stocks. *Quant. Finance*; arXiv cond-mat/0406696 (full text read by B).
- Safari, S. A., Schmidhuber, C. (2025). Trends and Reversion in Financial Markets on Time Scales from Minutes to Decades. arXiv 2501.16772.
- Garzarelli, F. et al. (2014). Memory effects in stock price dynamics. *Sci. Rep.* 4:4487. https://arxiv.org/abs/1110.5197
- Chung, K., Bellotti, A. (2021). Evidence and Behaviour of Support and Resistance Levels. arXiv 2101.07410.
- Osler, C. (2003). Currency Orders and Exchange Rate Dynamics. *J. Finance* 58(5):1791-1819. https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr125.html · Osler (2005), *JIMF* 24(2), SR150: https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr150.pdf
- Kavajecz, K., Odders-White, E. (2004). Technical Analysis and Liquidity Provision. *RFS* 17(4):1043-1071. https://ideas.repec.org/a/oup/rfinst/v17y2004i4p1043-1071.html
- Brock, W., Lakonishok, J., LeBaron, B. (1992). *J. Finance* 47(5):1731-1764. https://ideas.repec.org/a/bla/jfinan/v47y1992i5p1731-64.html · Sullivan, R., Timmermann, A., White, H. (1999). *J. Finance* 54(5).
- Llorente, G., Michaely, R., Saar, G., Wang, J. (2002). Dynamic Volume-Return Relation of Individual Stocks. *RFS* 15(4):1005-1047. https://www.nber.org/papers/w8312
- Gervais, S., Kaniel, R., Mingelgrin, D. (2001). The High-Volume Return Premium. *J. Finance* 56(3):877-919. https://sites.duke.edu/sgervais/?p=64
- Anderson, J. A., Faff, R. W. (2008). Point and Figure charting: a computational methodology and trading rule performance in the S&P 500 futures market. *IRFA* 17(1):198-217. https://ideas.repec.org/a/eee/finana/v17y2008i1p198-217.html
- Srivastava, S., Bhattacharya, R. (2018). arXiv 1812.02527. · Pal, J. (2024). arXiv 2403.18839. · Taylor, V. (2026). arXiv 2610.35887.
- Mahadzva (2026), SSRN 7430998 (unverified preprint). · Reddit r/Daytrading "13000 Wyckoff accumulation signals" (not findable; ungraded).
- TakeProfit, VSA article (spring "win rates", no method): https://takeprofitapp.com/en/learn/volume-spread-analysis-vsa

Supply/demand zones:
- Online Trading Academy instructor articles on FXStreet ("XLT odds enhancers"): https://www.fxstreet.com/education/lessons-from-the-pros-201109070000 · https://www.fxstreet.com/education/lessons-from-the-pros-201506090000
- Sam Seiden, "Breaking In Supply/Demand Zones" (FXStreet webinar): https://www.youtube.com/watch?v=uX6TUrTxD7U
- Rayner Teo, supply and demand zones: https://www.tradingwithrayner.com/supply-and-demand-zones/
- ProEA, supply and demand zones (freshness "an assumption, not a measured result"): https://proea.app/en/blog/supply-and-demand-zones [not re-fetched]
- El Trader Financiado, supply and demand zones (no measured confluence effect; Chung & Bellotti contrast): https://www.eltraderfinanciado.com/en/blog/supply-and-demand-zones

Sibling studies referenced (`brief/study/`): `ict_liq.final.md` (ICT-1, ICT-9, ICT-10; E4-E7, B7), `ict_pd.final.md` (ICTPD-1, ICTPD-8), `ict_struct.final.md` (ICTS-1, ICTS-2), `bias_dol.final.md` (BIAS-1/2/4/7; Turtle Soup §2.3; Crabel §2.11; Pine constraint row 18), `quant_regime.md` (REG-1..3; findings 1-7), `orderflow_micro.md` (OF-3), `smc_impl.final.md` (SMC-2, SMC-3), `academic_sr.md` (S1-S18; ACAD-4), `ict_time.final.md` (TIME-1, TIME-3), [B2] `amt_profile.md` (80% rule X3 / E-OWN-4), `price_action.md` (T3, T4: Brooks 80% rule).
