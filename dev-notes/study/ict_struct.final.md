# ICT Market Structure and Models: combined final study (Researcher A + Researcher B)

**Domain.** Swing points (3-candle vs N-candle fractals), the STH/ITH/LTH hierarchy, BOS vs CHoCH vs MSS, displacement, CISD, protected (strong) and weak extremes, the dealing range and premium/discount, market maker buy/sell models (MMXM), turtle soup, OTE (62-79%), the "2022 mentorship model", and intermediate-term highs/lows as targets. For each concept the report covers how it implies the next draw on liquidity, how the engine's bias and draw vector should reflect it, and what the evidence says.

**Engine.** `brief/baseline_v2.pine`. All line numbers refer to it; the file is identical to `/home/user/m/indicators/dol_engine.pine`.

**How this report was made.**
- Researcher A wrote `study/ict_struct.md`, including an original test on NQ, gold and EURUSD hourly data (tools in `study/ict_struct_tools/`).
- Researcher B (this merge):
  1. re-checked A's definitions, numbers, line references and sources;
  2. researched open-source implementations and academic literature;
  3. ran new tests on **8 markets plus 8 matched random walks** (tools and logs in `study/ict_struct_b_tools/`);
  4. re-checked the gap analysis;
  5. rewrote the proposals.

**Markers.**

| Marker | Meaning |
|---|---|
| **[A✓]** | B re-checked it and it holds |
| **[CORRECTED]** | B changed a claim or a grade |
| **[NEW-B]** | B added it |
| **[A, not re-fetched]** | B could not reopen the source (see the note below); kept as A reported it |

**Network note.** In B's session the web-search budget was already used up and the Firecrawl scraper was out of credits. WebFetch could not resolve nordman-algorithms.com, arxiv.org, ssrn.com, tradingview.com or luxalgo.com. B therefore verified sources through:
- the paper index (`firecrawl_research_*`: arXiv full text);
- GitHub (raw files and READMEs);
- sibling studies that had opened the same pages.

To re-verify the remaining items, those hosts have to be allowed in the session's network settings.

**Evidence grades.**

| Grade | Meaning |
|---|---|
| strong | peer-reviewed, or a large replicated quantitative study |
| moderate | published statistics or backtests with numbers, reproducible |
| weak | practitioner consensus, small or vendor samples, or unverified preprints |
| none | folklore, or definitions only |

---

## 0. Executive summary

1. **Market structure does not tell which side's liquidity is taken first. The evidence for this is now strong.** [A✓, strengthened]
   - **Engine replica, A (3 markets).** The engine's draw vector `D`, rebuilt from the code, called the first-touched side of close ± 1.5 ATR within 30 bars correctly 49.9-51.6% of the time on NQ, gold and EURUSD.
   - **Engine replica, B (8 markets).** NQ, gold, EURUSD, ES, RTY, YM, CL and BTC hourly: **`D` scored 47.4-52.7%**. Gated `D` (|D| ≥ 0.35) scored 41.6-52.7%. Eight matched random walks scored 48.4-52.1% and 47.9-54.5% (§2.3, B-ref).
   - **External studies:**
     - Taylor's AMD study, which B verified in full text (S5);
     - two open-source ICT/SMC falsification backtests that B read on GitHub: the 2022 model on ES/NQ from 2014 to 2026 has a profit factor of 0.74-0.87, and a multi-timeframe SMC rule set loses −0.33R out of sample (S4b, S4c);
     - Nordman, Tangirala and IvanSetuper, which point the same way [A, not re-fetched];
     - sibling REG-3, which simulated 23 series and found that choosing the side by `D` loses 9-12 pp of first-touch accuracy against plain geometry.
2. **The engine's heaviest scoring lever rests on that non-skill.**
   - Draw is the largest pillar (`wDraw` 30, line 145).
   - The counter-draw multiplier halves a target (×0.50, lines 162 and 692-693).
   - Selection is draw-side first, with 2× hysteresis for flipping sides (1964-2035).

   On most charts this pushes targets to the farther side and flips them on noise.

   **[CORRECTED]** A's fix (ICTS-1) measured `D` online but switched it on with a linear ramp from 50% to 56% accuracy. B simulated exactly that gate:
   - it switched on 8.2% of the time on random walks (35.6% of the time on one walk);
   - the periods when it was on were followed by **46.4% (real) and 48.8% (random walk)** accuracy;
   - a significance-gated version (one-sided lower bound, measured overlap design effect about 1.6) never switched on, on real data or on random walks.

   The revised ICTS-1 uses that gate.
3. **The sweep read in `liqEvt` is mis-signed. Fix it with sibling ICT-9.** [A✓]
   - Raids that close back inside are followed by continuation 52.6% of the time (n 1,402; sibling ict_liq B7: +1.5 ± 0.7 pp, n 5,899), not reversal.
   - HOLDs against the HTF swing reverse 56% of the time (n 381).
   - ICTS-2 is now implemented as `ict_liq.final.md` ICT-9.
4. **ICT's MSS is not a reversal signal, and the "with-HTF resumption" reading does not rescue it either.** [CORRECTED, NEW-B] B tested an ICT-faithful MSS on 8 markets:
   - **Definition:** a raid of any old high or low (5-bar pool or 3-candle swing), then a close through the 3-candle swing formed before the run, within 8 bars.
   - **All MSS:** 4,032 events, **49.4%** in the MSS direction (random walk 50.3%).
   - **Split by HTF swing bias:** with the HTF bias **50.0%** (n 2,031); against it 48.7% (n 1,979).
   - **With displacement:** 50.2%.
   - **The 2022-model target race:** the nearest opposite 5-bar pool against a stop beyond the raid was won **55.7% vs 56.8% predicted by geometry** (−1.2 ± 0.8 pp, n 3,784). The control was −0.1 pp.

   A had written that ICT's MSS "matches the evidence" through Taylor's trend-aligned cells. That overstates it: Taylor's cells measure the trend regime, not the MSS (S5).
5. **"Which pool is hit first" is geometry, and the engine already has the right math.** [A✓, replicated]
   - The race from the weak extreme to the protected extreme matched the gambler's-ruin prediction on 8 markets: **65.3% observed vs 65.8% predicted, n 12,148**. The random-walk difference was −0.2 pp.
   - `f_race` / `f_raceH` (446-482) and the ledger correction `f_raceAdj` (1367-1371) are exactly this model.
   - Show the odds of the target against the opposing pool to the Clean user (ICTS-3). **[CORRECTED]** Put them in the label tooltip by default, so that the Clean look stays identical to the reference.
6. **The dealing range in `f_structure` is the last pivot high and low, not ICT's range.** [A✓] ICT's range is [protected, weak] of the current leg.
   - The engine already computes both ends: `protH/protL` are returned unused, and `legH/legL` are not returned.
   - ICTS-4 is a two-line fix for premium/discount, `htfEQ` and the structural invalidation.
   - **[NEW-B]** Neither range predicts the side: the ICT rule "bull bias + discount → up" scored **49.5% / 49.1%** (exec / HTF, n ≈ 3,000 each). The fix is semantic.
   - **[NEW-B]** Once the range is ICT's, the premium/discount % in bullish structure *is* the geometric probability that the weak high is taken before the protected low. That probability is calibrated (point 5), so ICTS-4 shows it as "W1st %".
7. **Two robustness defects in swing detection.** [NEW-B]
   - **(a) Ties.** The Pine reference does not document how `ta.pivothigh` treats equal highs. Exact ties at the window maximum are common:
     - 1H: 3-11% of 5-bar swing windows on ES, CL, YM and RTY;
     - 5m: 22% on ES, 40% on 6E.

     Under a strict rule these "equal highs" (ICT's engineered liquidity) produce **no pivot at all**. A leftmost-wins rule recovers 11.5% (ES 5m) to 22.5% (6E 5m) of all pivots. ICTS-9 hand-codes it and passes the tie count to the EQ density.
   - **(b) Lag.** 71-75% of raided 3-candle swings were never 5-bar pivot pools. That is the same as on random walks (74-76%), so it is geometry, not lost information: no proposal is needed for targeting. It does mean `liqEvt` hears about only a quarter of raids.
8. **Mechanised ICT models add no forecastable edge beyond distance and geometry:** OTE, MMXM ladders, CISD, the 2022 model and AMD. They stay out of scoring. The right place for ICT structure is the **candidate ledger as measurable bits** (ICTS-8, built on ICT-1). Each chart can then show which claims hold there.
   - Two weak, consistent hints are worth measuring, not hard-coding:
     - displacement that leaves an FVG *with* the HTF swing continued **54.0%** (n 965) vs 47.1% against it (n 946); "with" beat "against" in 7 of 8 markets;
     - a swing CHoCH (close through the protected extreme) continued **53.7%** (n 1,016; random walk 50.1%), at least 52% in 6 of 8 markets.
   - Both cells were selected after looking at the pooled table, so they are hypotheses.

Nine proposals follow (section 4), best first.

---

## 1. Concepts: definitions, parameters, edge cases

**Notation.**
- Bar t is the current confirmed bar; `[k]` means k bars back.
- ATR is ATR(14).
- A "pool" is a liquidity level in the engine's `pool`.

### 1.1 Swing points: 3-candle vs N-candle fractals
- **ICT** [A, not re-fetched]. A swing high is three candles whose middle candle has the highest high, with a lower high on each side. It is confirmed when the third candle closes (2022 Mentorship Ep. 3, 17:53; via Quarter Sequence). ICT credits Larry Williams for the idea (Ep. 12).
- **N-candle fractal.** Strength p needs p lower highs on each side and is known p bars late. Williams uses p = 2.
- **[NEW-B] Open-source conventions, read from code:**
  - **LuxAlgo SMC** (public mirror, read on GitHub). `leg(size)` marks a bar as a candidate high when its high is greater than the highest high of the `size` bars **after** it. There is **no left-side test**.
    - A state machine forces highs and lows to alternate, so the result is the extreme of each leg (zigzag-like).
    - Sizes: swing 50 (minimum 10), internal 5 (fixed), equal-H/L pivots 3.
  - **Python `smartmoneyconcepts` (smc.py).** A swing high is the maximum of a **centred** window of 2 × `swing_length` bars (default 50, so 100 bars).
    - Ties are non-strict, and consecutive same-type swings are pruned (the lower high is dropped).
    - The centred window uses future bars. Any backtest that uses these flags at the swing bar has look-ahead bias.
    - Its liquidity tolerance is a share of the **whole dataset's** high-low range, which is also look-ahead.
  - A's other parameter survey (Leviathan 20; TradingFinder 15 left / 30 right for CHoCH and 1 for BOS; via ProEA) [A, not re-fetched].
- **Pine algorithm.** `ph = ta.pivothigh(high, p, p)` returns a value at bar t that refers to bar t − p. **Ties:** `docsrc/.../reference/ta.md` (`ta.pivothigh`) says only "returns price of the pivot high point. It returns 'NaN', if there was no pivot high point". [A✓]
- **[NEW-B] How often ties matter** (`out_ties.txt`). Share of 5-bar swing windows whose maximum is tied exactly:

  | Data | Tied windows | Pivots recovered by a "strictly above older, at least equal to newer" rule |
  |---|---|---|
  | NQ 1H | 0.8% | 0.4% |
  | GC 1H | 5.1% | 1.7% |
  | ES 1H | 9.8% | 5.0% |
  | RTY 1H | 3.2% | 1.5% |
  | YM 1H | 3.7% | 1.6% |
  | CL 1H | 10.8% | 5.2% |
  | BTC 1H | 3.8% | 1.8% |
  | EURUSD 1H (4-5 decimal feed) | 35.7% | 19.4% |
  | ES 5m | 22.0% | 11.5% |
  | NQ 5m | 4.4% | 1.9% |
  | GC 5m | 6.0% | 3.0% |
  | 6E 5m | 40.3% | 22.5% |

  A strict-both-sides fractal returns nothing for an exact double top inside the window. That is precisely ICT's "equal highs". → ICTS-9.
- **Trade-off.** A larger p gives fewer, larger swings, with p bars of lag. The engine's chart pivots (`pivLen` 5, line 90; series at 879-880) are 5 bars late. A swing taken within 5 bars of printing never becomes a pool, so its sweep never reaches `liqEvt`.
  - **[NEW-B] Measured:** 71.5-75.3% of 3-candle-swing raids hit swings that never were 5-bar pivot pools, against 74.1-76.0% on random walks. Of the raided 3-candle swings, 44-51% were at most 5 bars old.
  - This is fractal geometry, not missed information: near short-term swings are trivially reachable targets.
- **DOL role.** Swings are where stops rest (Osler 2003/2005; ict_liq E1-E2). The next unswept swing on each side is the nearest candidate draw.

### 1.2 Short-, intermediate- and long-term highs/lows (STH / ITH / LTH)
- **ICT (Ep. 12)** [A, not re-fetched]:
  - **STH:** the 3-candle swing.
  - **ITH:** an STH with a lower STH on each side, or "the high made when price trades back up to rebalance an imbalance".
  - **LTH:** an ITH with lower ITHs on each side, "generally linked to a higher time frame, daily chart".
  - Breaking an ITL is "a significant break in market structure". Breaking an STL is only a "shift".
- **Algorithm.** Rolling three-element rings of STH prices; promote the middle one when both neighbours are lower (sibling `ict_liq` ICT-8).
- **Engine.** The order of a swing is proxied by its timeframe tier (`f_tierW`, 506-516: chart 0.25, STF 0.45, HTF 0.65). [A✓]
- **Evidence.** None for edge. Tier labels add little beyond distance (ict_liq E6; calib_ml: the tier term inside density has a negative lift, t up to −2.9).

### 1.3 Break of structure (BOS)
- **SMC definition.** A candle **close** beyond the last swing in the trend direction (continuation). ICT has no separate term for it.
- **Parameters that change the label:** swing strength, wick vs close confirmation, and a minimum break distance.
- **Open-source conventions** [NEW-B, from code]:
  - **LuxAlgo:** close crossing the last unbroken swing pivot; BOS if the swing trend already pointed that way, else CHoCH.
  - **`smartmoneyconcepts`:** BOS/CHoCH from the pattern of the **last four alternating swings**. Bullish BOS = L(A) < L(C) < H(B) < H(D). The break is confirmed by the first close through H(B) when `close_break=True`, otherwise by the high.
- **Engine** [A✓]:
  - `f_structure` (708-782) on each MTF timeframe: `upBrk = close > swH` (747-748), where `swH` is the last unbroken pivot of strength `biasLen` (3, line 65). On a break, `swH := na`.
  - The chart-level BOS used for OBs is `bosUp = close > obSwingH` (1542-1547).
- **Academic analogue** [NEW-B]. The "trading range break" (TRB) rule, which buys a close above the prior N-day maximum, is a daily-bar BOS.
  - Brock, Lakonishok & LeBaron (1992): TRB signals on the DJIA 1897-1986 were significant against bootstrapped random-walk, AR(1) and GARCH-M nulls.
  - Sullivan, Timmermann & White (1999): after data-snooping correction, the in-sample winners did not hold out of sample (1987-96).
  - Zhu et al. (2015, arXiv 1504.04254; B read the abstract): TRB beat MA rules on Chinese indexes, but "once transaction costs are included, trading profits will be eliminated completely".
  - Intraday technical rules on US index futures do not survive data-snooping tests (Marshall, Cahan & Cahan 2008) [B, from the literature, not re-fetched].

### 1.4 Change of character (CHoCH)
- **SMC definition.** The first close through a swing against the prevailing structure.
- **[CORRECTED]** A wrote that a LuxAlgo-style "swing" CHoCH requires a close through the **protected** extreme. The LuxAlgo code says otherwise:
  - the CHoCH is a close through the **last unbroken swing pivot** (size 50) against the current swing trend;
  - its "Strong Low" label is the trailing minimum since the last swing-low pivot, i.e. the **most recent** swing low.

  So two conventions exist:

  | Convention | CHoCH level in an uptrend |
  |---|---|
  | LuxAlgo / most TradingView SMC scripts | the latest higher low, as soon as it is confirmed |
  | **Protected-low convention (the engine's swing bias)** | the low of the pullback that preceded the last BOS; it only moves up at the next BOS |

  They differ between the confirmation of a new higher low and the next BOS. The engine's protected convention is the stricter one and is closer to ICT's "ITL is protected" (1.2).
- **Engine** [A✓]:
  - Swing CHoCH = close through `protH/protL` (760-773).
  - Internal `ibias` flips on any close through the last pivot (749-753). It uses the same `biasLen` 3 pivots, so it is a LuxAlgo-like CHoCH with a much shorter swing.
  - The Clean bias table shows the swing bias and falls back to the internal bias while the swing bias is 0 (2294-2305).
- **Failure modes.** In ranges, small swings flip on every pullback. One move can be both a CHoCH on small swings and a BOS on large swings.
- **[NEW-B] Measured (8 markets, 1H, ±1.5 ATR / 30 bars, in the new direction):**

  | Event | n | In the new direction | Random walk |
  |---|---|---|---|
  | Internal CHoCH | 2,467 | 50.1% | 50.4% |
  | Swing CHoCH (protected break), all | 1,016 | **53.7%** | 50.1% |
  | Swing CHoCH with the HTF swing | 485 | 55.3% | — |

  The swing CHoCH was at least 52% in 6 of 8 markets (`out_permarket.txt`). It is a weak hint, and the cell was chosen after looking.

### 1.5 Market structure shift (MSS, ICT)
- **ICT definition** [A, not re-fetched; quotes via Quarter Sequence]: "If you're bearish and you see price run above an old high, then it breaks below the old high and takes out a short-term low prior to that run above" (Ep. 6). It has three parts:
  1. **The run:** a trade through an old high. A wick is enough.
  2. **The break:** a close below the short-term low that formed before the run.
  3. **The force:** displacement, usually leaving an FVG.

  ICT calls it "a bias for the day … market structure shift, not market structure break" (Ep. 3).
- **Reading** [A]. The MSS is defined inside an HTF bias ("if you're bearish"), so it marks the end of a counter-trend retracement.
- **[CORRECTED]** A said that reading "matches the evidence" through Taylor's trend-aligned cells. It does not:
  - Taylor tests an AMD close-vs-midpoint outcome, and the trend regime does the predicting (S5).
  - B tested MSS × HTF directly: with the HTF bias 50.0% (n 2,031), against it 48.7% (n 1,979).
- **Algorithm** (bearish; mirror for bullish) [A, refined by B]:
  1. Track the last confirmed 3-candle swing low: `stl = ta.pivotlow(low, 1, 1)`.
  2. When a bar trades through any unswept old high (chart pool or 3-candle swing), arm the MSS: level = last `stl`, extreme = the running raid high, window = 8 bars from the latest raid.
  3. The first close below the level inside the window is the MSS. Optional displacement gate: a displacement bar on the MSS bar or the one before.
  4. It fires once. A new raid re-arms it with the latest `stl`.
- **[NEW-B] Measured** (§2.3 B1; 8 markets; ±1.5 ATR / 30 bars in the MSS direction):

  | MSS subset | Result |
  |---|---|
  | All | 49.4% (n 4,032; random walk 50.3%) |
  | With displacement | 50.2% (n 1,685) |
  | Leaving an FVG | 47.7% (n 1,291) |
  | Displacement + FVG, with the HTF | 54.1% (n 244) |
  | Displacement + FVG, against the HTF | 43.6% (n 296) |
  | Per market | 43.1% (CL) to 52.1% (GC) |

- **Nordman** [A, not re-fetched]: 15,817 MSS on ES/NQ/6E/6A, edge ratio (MFE/MAE) 0.97-1.13; displacement does not improve it. B's result agrees in direction.

### 1.6 Displacement
- **ICT** [A]: "an obvious displacement", "energetic". No size rule.
- **Operational versions:**
  - one candle with body ≥ k·ATR (k 1.0-2.0) and body/range ≥ 0.6-0.7;
  - body far above the average of the last 20 bodies (Nordman's example: 4.5×) [A, not re-fetched];
  - "leaves an FVG";
  - [NEW-B] an open-source Silver Bullet backtest uses body > 1.5 × ATR(20) and body ≥ 70% of range (hindsight-finance README).
- **Engine** [A✓]: `dispUp/dispDn` (897-903) = body ≥ `dispMult` (1.2) × ATR[1] with ratio ≥ 0.6, or a two-candle leg (both ratios ≥ 0.5, combined body ≥ 1.8 ATR). It is used:
  - as the FVG/OB quality gate (1666-1681, 1867-1889);
  - as 20% of `D` (`wM`, line 156; half-life 12, line 158; 1893).
- **[NEW-B] Literature: large intraday moves do not default to continuation.**
  - Zawadowski, Andor & Kertész (2006; arXiv cond-mat/0406696, B read the abstract): "significant reversal for both intraday price decreases and increases" after extreme moves in NYSE/NASDAQ stocks.
  - Heston, Korajczyk & Sadka (2010; arXiv 1005.3535): short-term reversal is "driven by temporary liquidity imbalances lasting less than an hour".
  - Grant, Wolf & Yu (2005, S&P futures 1987-2002): intraday reversals after large opening moves [B, not re-fetched].
  - Mesfin (2026; arXiv 2605.04004): 14 OHLCV intraday momentum families on MNQ, none passing an out-of-sample, cost and year-stability gate.
- **[NEW-B] Measured (8 markets):**

  | Displacement subset | n | Continuation |
  |---|---|---|
  | All displacement bars | 4,347 | 51.3% (random walk 50.6%) |
  | Leaving an FVG | 1,918 | 50.6% |
  | FVG + with the HTF swing | 965 | 54.0% |
  | FVG + against the HTF swing | 946 | 47.1% |

  "With" beat "against" in 7 of 8 markets. This is a weak hint, not a rule.

### 1.7 Change in state of delivery (CISD)
- **Definition** [A]. Take the last run of consecutive down-close candles into a swept low. A **body close** above the **open of the first candle** of that run is the bullish CISD. It fires earlier than an MSS.
- **DOL role.** An entry trigger only.
- **Evidence.** None (no statistics found; B found only uncommented open-source indicators on GitHub). Not recommended for the engine.

### 1.8 Protected (strong) vs weak extremes
- **Definition.** In a bullish swing, the low that launched the leg that broke structure is protected (strong), and the running high is weak, i.e. it is the target.
  - **[CORRECTED, see 1.4]** In LuxAlgo, "Strong Low" is the trailing low since the latest swing-low pivot.
- **Engine** [A✓]. `f_structure` keeps exactly these values:
  - `protL/protH` are set at each BOS/CHoCH (755-773), e.g. `protL := legL`, the low of the pullback since the previous break;
  - `legH/legL` are the running extremes since the last break (729-730, re-armed at each break).

  `protH/protL` are returned (782) but never read after 923-925. `legH/legL` are not returned.
- **Measured** [A✓ + NEW-B]. P(weak extreme before protected extreme) follows gambler's-ruin geometry, `(C − prot)/(weak − prot)`:

  | Source | Observed | Geometry | n |
  |---|---|---|---|
  | A, NQ | 0.628 | 0.648 | 1,551 |
  | A, gold | 0.624 | 0.646 | 1,595 |
  | **B, 8 markets pooled** | **0.653** | **0.658** | **12,148** |
  | B, random walks | 0.673 | 0.675 | — |

  Per market, B's differences run from −3.4 pp (CL) to +3.0 pp (BTC).
- **DOL role.** The weak extreme of the HTF leg is the textbook objective, and the protected extreme is the structural invalidation. The weak extreme is not a magnet beyond geometry.

### 1.9 Dealing range, premium and discount
- **ICT.** The dealing range runs from the swing low to the swing high of the most recent leg that "did something meaningful" (broke structure or swept). Premium is above 50%, discount below. Buy in discount toward premium liquidity. Sub-levels are in `ict_pd.final.md`.
- **Structure-consistent definition:**
  - bullish bias: `[protL, legH]`;
  - bearish bias: `[legL, protH]`.
- **[NEW-B] Variant.** LuxAlgo draws premium/discount zones between the trailing top and bottom (the most recent swing extremes). That range is narrower right after a new higher low.
- **Engine** [A✓]. `rngH/rngL` (727-779) are the **last pivot high** and the **last pivot low**, each extended by the running extreme while its swing is broken. After a lower high forms inside an up-leg, `rngH` drops to it. These values are used by:
  - `htfEQ` (968; a confluence anchor at 1931);
  - the Terminal PREM/DISC % (2323-2333; clamped to 0-100%);
  - the `f_invalidation` fallback (1354);
  - registry prominence (1783-1789).
- **[NEW-B] Measured (§2.3 B3).** The ICT rule "bull bias + discount → up first; bear bias + premium → down first" scored:

  | Range used | Exec | HTF |
  |---|---|---|
  | ICT [prot, weak] range | 49.5% (n 3,001) | 49.1% (n 2,878) |
  | Engine's old range | 49.3% | 50.4% |
  | Random walks | 49.0% | 50.2% |

- **[NEW-B] Reinterpretation.** In bullish structure with the ICT range, `pos = (C − protL)/(legH − protL)` is exactly the driftless gambler's-ruin probability that the weak high is taken before the protected low. That number is calibrated (1.8). "Discount" therefore means the leg is closer to failing than to completing, not that it is cheap. → ICTS-4 readout.

### 1.10 Optimal trade entry (OTE, 62-79%)
- **Definition.** The 62-79% retracement band of the displacement leg; 70.5% is ICT's "sweet spot". Usually it must sit in discount and overlap an FVG or OB.
- **DOL role.** An entry location. For the draw, only geometry matters: a deeper pullback means a nearer protected low and a farther old high.
- **Evidence:**
  - Tradeify, ES/NQ daily, 100 legs (+163 on AAPL/MSFT/NVDA): continuation odds fall **monotonically** with depth (33.3% after 23.6%, ~20% after 61.8%, 13.5% after 78.6%), with "no bump" at any Fibonacci level [A, not re-fetched].
  - [NEW-B] Gurrib et al. (2022, *Financial Innovation*; B read the abstract): a Fibonacci-retracement trading system beat buy-and-hold on US energy stocks over 2017-2020. It has no distance control and no random-level baseline.
- **Grade: weak.** No study shows Fibonacci levels to be special beyond the geometry of depth.

### 1.11 Market maker buy/sell models (MMXM)
- **Definition** (ICT; LuxAlgo and TMGM summaries) [A, not re-fetched]. In an MMBM:
  1. price leaves an original consolidation;
  2. it steps down through smaller consolidations, each leg taking SSL ("engineering liquidity"), to a sell-side objective;
  3. a smart money reversal follows (sweep + MSS or CISD);
  4. the buy side of the curve retraces the path: interior consolidations and short-term highs are targets **nearest first**, ending at the original consolidation;
  5. targets beyond it come from −2 to −2.5 standard-deviation projections.

  Invalidation: a close back through the swept extreme.
- **Engine.** Implicitly present: lower highs left on the way down are BSL pools, and proximity picks the nearest one once `D` flips. There is no SMR detector.
- **Evidence: none.** Its core (sweep → MSS reversal toward opposing liquidity) tests at geometry (B1b: −1.2 ± 0.8 pp).

### 1.12 The "2022 mentorship model"
- **Sequence:**
  1. HTF bias and the draw.
  2. A raid of an obvious pool (Asia, London, PDH/PDL, equal highs or lows), ideally in a killzone.
  3. A displacement close through the STH/STL that led into the raid (the MSS).
  4. Entry on the retrace into the FVG.
  5. Stop beyond the raid.
  6. Target: the **opposite pool**.
- **Mechanised tests:**
  - **IvanSetuper** (open TradingView script, 12 markets, Feb 2021-Aug 2025) [A, not re-fetched]: within ±0.05R before costs on every timeframe. After costs: 1m −0.25R (41,541 trades), 5m −0.08R, 15m −0.04R.
  - **[NEW-B] truongxxxx/ict-backtest** (GitHub README; ES/NQ index CFDs, Mar 2014-Aug 2026; M5 sweep → structure shift → FVG limit entry; 2R target):

    | Setup | Trades | Win rate | Profit factor | Result |
    |---|---|---|---|---|
    | 2022 model, ES | 337 | 35.3% | 0.87 | −26R |
    | 2022 model, NQ | 322 | 35.4% | 0.74 | −51R |
    | London variant, ES / NQ | 420 / 395 | — | 0.94 / 0.66 | — |
    | Silver Bullet, ES / NQ | 2,403 / 2,391 | — | 0.72 / 0.77 | — |

    With a daily or H4 bias filter, the best profit factor was 0.96.
  - **[NEW-B] AaroNLaU0307/quant-backtest-framework** (multi-timeframe SMC, D1→H1→M5; XAU, EUR, GBP, GBPJPY, WTI; 2015-2025): walk-forward pooled E[R] **−0.329R** (95% CI −0.416 to −0.228); **0 of 42** configurations survive BH-FDR.
- **[NEW-B] The target claim itself** (B1b, n 3,784). The opposite 5-bar pool was reached before the raid extreme **55.7%** of the time vs **56.8%** predicted by driftless geometry. The control was −0.1 pp. The "opposite liquidity" is not a magnet after an MSS.

### 1.13 Turtle soup
- Rules (Connors-Raschke): a new 20-day low below a prior 20-day low that is at least 4 sessions old; buy stop just above the old low. ICT adds premium/discount context and a later MSS. Details in `ict_liq.final.md`.
- **Data.** Closes back inside after a raid lean to **continuation** (A: 52.6%, n 1,402; ict_liq B7: +1.5 ± 0.7 pp, n 5,899). The age filter is untested here.
- **[NEW-B]** An open-source XAUUSD turtle-soup backtest exists on GitHub without published statistics. Grade: weak.

### 1.14 Intermediate-term highs/lows as targets
- **ICT.** Once an ITL forms after the first raid of an STL in a bullish leg, the ITH/LTH above is the target and the ITL is protected.
- **Engine.** STF/HTF pivots enter the registry only when confirmed and unswept (1779-1789; `hValid/lValid`, 780-781). That happens `biasLen` (3) HTF bars plus the `[1]` shift after the pivot: about 4 days on D and about 16 hours on 4H. The trailing HTF extreme of the current leg is not a level until then.

### 1.15 HTF trend regime and trend persistence
- **[CORRECTED] Split the claim by horizon:**

  | Horizon | Evidence | Grade |
  |---|---|---|
  | 1-12 months | Moskowitz, Ooi & Pedersen (2012): 58 futures. Lempérière et al. (2014; arXiv 1404.3274, B read the abstract): trend-following t-stat ≈ 5 since 1960 and ≈ 10 since 1800, stable across asset classes, but "shorter trends have significantly withered" | strong |
  | Hours to days | Safari & Schmidhuber (2025; arXiv 2501.16772, B read the full text): from a few hours to several days "small trends tend to persist, while strong trends tend to revert", with small coefficients. **Up to 15 minutes weak trends revert** | moderate |
  | Short-term, recent | Kurth, Eisler, Rej & Bouchaud (2026; arXiv 2607.01550): since about 2009 "short-term trends have ceased to deliver reliable returns", collapsing on small-tick contracts | moderate |
  | **The engine's horizon (30 hourly bars)** | B: HTF swing bias 48.3-52.4% on 8 markets; random walks 47.8-51.8% | **none** |

- **Engine.** `htfBias` carries 0.5 of `sV` (1892) and keys the empirical PoT surface (`f_bump` 1530-1531; `f_empPoT` 1284).
  - **[CORRECTED]** A called the regime split "good". At this horizon the key carries no side information and splits the samples three ways.
  - Siblings REG-1 and BIAS-6 propose a volatility key or a held-out choice instead.

### 1.16 How the models imply the next draw (summary)

| Model | Next draw it implies | Engine equivalent | Evidence for the implied draw |
|---|---|---|---|
| HTF trend / swing bias | weak extreme / next old high in the trend direction | `htfBias` in `sV` (1892); PoT regime key (1531) | none at 30 1H bars (B: 48.3-52.4%, 8 markets); strong at 1-12 months |
| BOS | continuation to the next swing pool | same | null intraday (Tangirala [A, not re-fetched]; Marshall et al.); TRB edges vanish OOS or after costs |
| Swing CHoCH (protected break) | new direction | swing `bias` (not in `sV` for exec) | weak hint: 53.7% (n 1,016) |
| Internal CHoCH | new direction | `exeIB` (0.2 of `sV`) | null: 50.1% (n 2,467) |
| MSS | ICT: opposite pool (with-HTF resumption) | none (sweeps and structure are independent) | null: 49.4% (n 4,032); with HTF 50.0%; 2022 race −1.2 pp vs geometry |
| Sweep that holds | continuation | `liqEvt` +1 | mixed: with HTF 53%; **against HTF reverses 56%** |
| Sweep that rejects | reversal | `liqEvt` −1 | **contradicted**: continuation 52.6% / +1.5 pp |
| Displacement | continuation | `mV` (20% of D) | null: 51.3% (n 4,347); with-HTF + FVG 54.0% (weak hint) |
| MMXM | interior pools nearest first | nearest draw-side pool | none |
| 2022 model | opposite pool after sweep + MSS | selection after `D` flips | null: PF 0.74-0.87; −0.33R OOS (SMC); race = geometry |
| OTE / premium-discount | from discount, the premium old high | not used | null: 49.1-49.5% (B3); depth = geometry |
| Weak vs protected race | weak extreme first with odds `(C − prot)/(weak − prot)` | `f_race` (446-482), Terminal only | **strong**: 65.3% vs 65.8%, n 12,148 |
| DC overshoot | about δ beyond confirmation, exponential tail | not used | strong as a law; identical to a random walk |

---

## 2. Evidence (numbers and sources)

### 2.1 Published evidence

| # | Claim tested | Data | Result | Grade | B's check |
|---|---|---|---|---|---|
| S1 | SMC/ICT event detectors predict returns | Tangirala, SSRN 7483658 (2026): 44 detectors from two open-source Pine scripts; 496 S&P 500 stocks, daily 2010-2026; 2.2 M events; ticker-matched null; BH over 352 tests | None beats random entry at any horizon. Largest estimates are 11-12 bp over 10 days (the liquidity-sweep detectors, p ≥ 0.23). In-sample picks earn −31 bp out of sample | moderate (null) | [A, not re-fetched]; quoted consistently by `smc_impl` and `ict_liq` |
| S2 | ICT/SMC rules on G10 FX | Mahadzva, SSRN 7430998 (2026): walk-forward, bootstrap, permutation | "No evidence ICT/SMC concepts work as literally taught". Sweeps predict continuation in 65/66 fold selections. Fade the CHoCH+FVG reversal | **weak** [CORRECTED from moderate] | Nobody in the project opened the paper (same correction as `ict_liq.final` E7). Its direction is carried by internal replications |
| S3 | Displacement improves the MSS | Nordman Algorithms (Nov 2026): 15,817 MSS, ES/NQ/6E/6A 5m, Oct 2023-Sep 2026 | Edge ratio (MFE/MAE) 0.97-1.13 with or without displacement, at 5m/15m/1h/1d | moderate (vendor, large n) | [A, not re-fetched]. **B1 agrees:** 49.4% (n 4,032), displacement 50.2% |
| S4 | Mechanised 2022 model | IvanSetuper, open TradingView script: 12 markets, Feb 2021-Aug 2025 | Within ±0.05R before costs; after costs 1m −0.25R (41,541), 5m −0.08R, 15m −0.04R | moderate | [A, not re-fetched] |
| S4b | Mechanised 2022 model, Silver Bullet, London | **[NEW-B]** truongxxxx/ict-backtest (GitHub README): ES/NQ CFD, Mar 2014-Aug 2026, M1/M5, 2R | 2022 model PF 0.87 (ES, 337 trades) / 0.74 (NQ, 322); Silver Bullet 0.72 / 0.77 (2,400 trades each); best with a bias filter 0.96 | moderate (individual, open code, 12 years) | B read the README |
| S4c | Multi-timeframe SMC rule set | **[NEW-B]** AaroNLaU0307/quant-backtest-framework (README): 5 instruments, 2015-2025, walk-forward | OOS E[R] −0.329R (CI −0.416 to −0.228); 0/42 configurations survive BH-FDR; 11/12 calendar periods negative | moderate | B read the README |
| S5 | AMD / Power of 3 | Taylor, arXiv 2610.35887 (2026): NQ 15m, Jan 2022-Jul 2026, N = 484 signal days; outcome = **4 PM close vs Asia midpoint**; regime = daily EMA20 ±0.5% | Fires on 44% of days. 57% of targets are delivered before 9:40. Bullish 46.9% (p 0.35); bearish 39.9% (inverted, p 0.002). By regime: aligned 61.6% (n 112) / 70.8% (n 72); against 29.6% (n 71) / 24.8% (n 153); ranging n.s. Taylor: "the signal reflects the trend direction, and the trend is doing the predicting" | moderate | **[A✓, full text]**. **[CORRECTED reading]** The regime cells are in-sample labels of a daily-close outcome in a strongly trending market (2023-25). They show the AMD signal adds nothing; they are **not** evidence that trend alignment forecasts the intraday draw. Taylor also cites Agarwal (2023), a positive Power-of-3 preprint on 14 FX pairs with no permutation baseline (B could not locate it) |
| S6 | Trend persistence across scales | Schmidhuber (2021), arXiv 2006.07847; Safari & Schmidhuber (2025), arXiv 2501.16772 | Up to 15 min: weak trends revert. From about 30 min to a few hours, the linear term turns positive. Hours to days: weak trends persist and strong ones revert, with small coefficients (R² of order 0.01 bp). Effects peak at 6-12 months and reverse beyond about 2 years | strong (as a law); none at the engine's horizon (B) | **[A✓, full text; horizons refined]** |
| S7 | Time-series momentum | Moskowitz, Ooi & Pedersen, *JFE* 104 (2012) | The past 12-month return predicts the next month in 58 futures | strong (monthly) | Classic, not re-fetched |
| S7b | Two centuries of trend following | **[NEW-B]** Lempérière, Deremble, Seager, Potters & Bouchaud, arXiv 1404.3274 (2014) | Excess returns t ≈ 5 since 1960 and ≈ 10 since 1800. Saturation for large signals. "Shorter trends have significantly withered" | strong | B read the abstract |
| S7c | Demise of short-term trend | **[NEW-B]** Kurth, Eisler, Rej & Bouchaud, arXiv 2607.01550 (2026): about 100 futures, 1995-2025 | Since about 2009 short-term trend following has failed, especially on small-tick contracts; large-tick contracts survive | moderate (preprint, large sample) | B read the abstract |
| S8 | Directional-change scaling laws | Glattfelder, Dupuis & Olsen, arXiv 0809.1040 / *Quant. Finance* 11(4) (2011): 13 FX pairs | 12 scaling laws over about three orders of magnitude; average overshoot ≈ δ. A's simulation: a driftless random walk gives the same law (median 0.70δ, P(≥ δ) ≈ 0.37). [NEW-B] Houweling (arXiv 2511.14408, 2025): directional changes make up ≈ 1 − 1/e = 0.632 of events, consistent with a memoryless hazard process | strong (law), none (edge) | B confirmed both papers exist (index) |
| S9 | Head-and-shoulders (a CHoCH-type pattern) | Chang & Osler (*EJ* 1999); Savin, Weller & Zvingelis (*JFEc* 2007) | FX: profitable for 2 of 6 currencies and dominated by filter rules. US stocks: 5-7% per year risk-adjusted, partly through negative momentum | strong (old samples) | Classic, not re-fetched |
| S10 | Fibonacci / OTE | Tradeify (2026), ES/NQ daily 100 legs plus 163 stock legs | Continuation falls monotonically with depth; no Fibonacci bump; median continuing depth 60.4% | weak | [A, not re-fetched] |
| S11 | Trading-range-break rules (daily BOS) | **[NEW-B]** Brock, Lakonishok & LeBaron (*J. Finance* 1992); Sullivan, Timmermann & White (*J. Finance* 1999); Zhu, Jiang, Li & Zhou, arXiv 1504.04254 (2015) | TRB significant on the DJIA 1897-1986 against bootstrap nulls; not out of sample after data-snooping correction; profits eliminated by costs on Chinese indexes | strong (null after correction) | Zhu: B read the abstract; the others are classics, not re-fetched |
| S12 | Large intraday moves: continuation or reversal? | **[NEW-B]** Zawadowski, Andor & Kertész, arXiv cond-mat/0406696 (*QF* 2006); Heston, Korajczyk & Sadka, arXiv 1005.3535 (*JF* 2010); Grant, Wolf & Yu (*JBF* 2005) | Significant intraday reversal after extreme moves (NYSE/NASDAQ). Short-term reversal comes from liquidity imbalances lasting under an hour. S&P futures reverse after large opening moves | strong (equities) | First two: B read the abstracts. Grant et al. not re-fetched |
| S13 | Intraday OHLCV momentum on MNQ | **[NEW-B]** Mesfin, arXiv 2605.04004 (2026): 947 days, 5m, 14 signal families, walk-forward | None of 14 passes OOS t ≥ 2, cost, year-stability and permutation gates. The ORB long is year-unstable | moderate | B read the abstract |
| S14 | Open-source structure algorithms | **[NEW-B]** LuxAlgo SMC (public mirror on GitHub); `smartmoneyconcepts` (`smc.py`) | Definitions in 1.1-1.4 and 1.9. The Python library's swings use a centred window and its liquidity tolerance uses the full-sample range, so both look ahead | none (definitions) | B read the code |
| S15 | ICT definitions | Quarter Sequence (lecture timestamps); LuxAlgo concept library; ProEA survey; TMGM | Definitions only | none | [A, not re-fetched] |

### 2.2 A's original test (NQ, gold, EURUSD hourly, Nov 2024-Nov 2026) [A✓: code and results re-read]

**Design** (`study/ict_struct_tools/structtest.py`):
- **Label:** which of `close ± 1.5·ATR14` is touched first within 30 bars. Robustness checks used K = 3 / HZ = 120 and K = 1 / HZ = 12.
- **Sampling:** every 6th bar from bar 600.
- **Null:** random walks with matched volatility.
- **Features:** engine replicas: `f_structure` on 1H, on 4-bar aggregates and on 24-bar aggregates (each used from the bar after the aggregate closes, matching `[1]` + `lookahead_on`); `D` and its parts.

**B's code review:** the aggregate alignment has no look-ahead; pivots are strict on both sides; the sweep classes follow the engine.

**Directional accuracy (K 1.5, HZ 30):**

| Feature | NQ | Gold | EURUSD | Random walks |
|---|---|---|---|---|
| `D` | 0.499 | 0.516 | 0.504 | 0.497-0.506 |
| `D` gated | 0.520 | 0.504 | 0.502 | 0.48-0.52 |
| HTF swing bias | 0.508 | 0.524 | 0.515 | 0.49-0.52 |
| Exec internal bias | 0.502 | 0.499 | 0.462 | 0.49-0.51 |
| Displacement momentum | 0.508 | 0.495 | 0.483 | 0.50 |
| `liqEvt` | 0.501 | 0.485 | 0.504 | 0.47-0.48 |
| Logistic learner (11 features), out of sample | 0.480 | 0.478 | 0.496 | 0.526-0.537 |

- **[NEW-B note]** In the second half alone, gated `D` reached 0.543 on NQ, 0.488 on gold and 0.490 on EURUSD (`results.txt`, "skill-weighted D"). Window-to-window swings of ±5 pp are noise of the same size as any claimed skill. A skill gate must therefore be significance-based (ICTS-1).

**Events, pooled over 3 markets:**

| Event | n | Result |
|---|---|---|
| REJECT sweep → continuation | 1,402 | 0.526 |
| HOLD with the HTF swing → continuation | 423 | 0.532 |
| HOLD against the HTF swing → continuation | 381 | 0.438 (56% reversal) |
| MSS plain → reversal | 171 | 0.456 |
| MSS with displacement → reversal | 97 | 0.505 |

**Geometry and persistence:**
- Weak-before-protected race: NQ 0.628 vs 0.648, gold 0.624 vs 0.646.
- Directional-change overshoot/δ: gold 1.39 vs random walk 1.19 ± 0.04; NQ 1.29 vs 1.17 ± 0.06; EURUSD 1.14 vs 1.11 ± 0.07.

### 2.3 [NEW-B] B's original tests: 8 markets plus 8 random walks

**Data:**
- Yahoo 1H, Nov 2024-Nov 2026: NQ (11,400 bars), GC (11,429), EURUSD (12,285).
- CME 1H, Mar 2025-Apr 2026: ES, RTY, YM (about 6,270 bars each); CL (Jun 2025-Apr 2026, 4,521).
- BTC 1H, Sep 2022-Jan 2025 (20,000 bars).
- 8 matched random walks (`sim/rw11-18`, 11,400 bars each).
- For the tie test: CME 5-minute ES, NQ and GC (Jan-Apr 2026) and 6E (Mar-Apr 2026).

The index futures are correlated, so the effective number of independent markets is below 8.

**Code:** `study/ict_struct_b_tools/` (`common.py`, `btest.py`, `permarket.py`, `ties.py`, `ties5.py`). **Logs:** `out_b.txt`, `out_permarket.txt`, `out_ties.txt`.

**Default label:** which of `close ± 1.5 ATR` is touched first within 30 bars, from the event bar's close. Ambiguous and undecided rows are dropped. The standard errors quoted use n/3 to allow for overlap.

**B-ref. Side accuracy of `D` and its parts** (every 6 bars):

| Market | D | sV | HTF bias | D gated (n) |
|---|---|---|---|---|
| NQ | 0.509 | 0.505 | 0.508 | 0.527 (771) |
| GC | 0.511 | 0.519 | 0.524 | 0.506 (877) |
| EU | 0.501 | 0.506 | 0.515 | 0.502 (806) |
| ES | 0.527 | 0.510 | 0.519 | 0.494 (453) |
| RTY | 0.474 | 0.479 | 0.492 | 0.455 (444) |
| YM | 0.476 | 0.490 | 0.493 | 0.490 (435) |
| CL | 0.478 | 0.481 | 0.489 | 0.416 (293) |
| BTC | 0.501 | 0.489 | 0.483 | 0.498 (1,369) |
| 8 random walks | 0.484-0.521 | 0.489-0.518 | 0.478-0.518 | 0.479-0.545 |

**B1. ICT MSS** (definition in 1.5):

| Subset | Real n | Real P (MSS direction) | Random walk n | Random walk P |
|---|---|---|---|---|
| All | 4,032 | 0.494 (se 0.014) | 5,167 | 0.503 |
| With displacement | 1,685 | 0.502 | 2,221 | 0.488 |
| Plain | 2,347 | 0.489 | 2,946 | 0.514 |
| FVG left | 1,291 | 0.477 | 2,269 | 0.506 |
| With HTF swing | 2,031 | 0.500 | 2,549 | 0.512 |
| Against HTF swing | 1,979 | 0.487 | 2,605 | 0.491 |
| Disp + FVG, with HTF | 244 | 0.541 (se 0.055) | 503 | 0.511 |
| Disp + FVG, against HTF | 296 | 0.436 (se 0.050) | 534 | 0.493 |

Per market (all MSS): NQ 0.491 (640), GC 0.521 (583), EU 0.507 (517), ES 0.505 (327), RTY 0.513 (345), YM 0.475 (379), CL 0.431 (216), BTC 0.486 (1,025).

**B1b. 2022-model race.** Target = nearest unswept 5-bar pool on the MSS side, within 8 ATR. Stop = raid extreme ± 0.1 ATR. Races run until resolved (up to 500 bars). Geometry = the driftless gambler's-ruin probability.

| Set | n | Target first | Geometry | Difference |
|---|---|---|---|---|
| Real, all MSS | 3,784 | 0.557 | 0.568 | −0.012 (se 0.008) |
| Real, MSS with HTF | 1,832 | 0.563 | 0.570 | −0.007 |
| Real, MSS against HTF | 1,933 | 0.549 | 0.567 | −0.017 |
| Random walks, MSS | 4,898 | 0.585 | 0.587 | −0.002 |
| Real control (every 6th bar; stop = 8-bar extreme ± 0.1 ATR) | 21,329 | 0.376 | 0.377 | −0.001 |
| Random-walk control | 25,204 | 0.397 | 0.394 | +0.003 |

**B2. Weak extreme (`legH`/`legL`) before protected extreme (`protL`/`protH`)**, exec `f_structure` p = 3:

| Set | n | Weak first | Geometry |
|---|---|---|---|
| Real pooled | 12,148 | 0.653 | 0.658 |
| Random walks | 14,382 | 0.673 | 0.675 |

Per market, observed / geometry: NQ .661/.679; GC .645/.667; EU .654/.656; ES .631/.651; RTY .646/.661; YM .630/.661; CL .633/.667; BTC .670/.640.

**B3. Premium/discount rules** (accuracy, n):

| TF | Set | ICT range rule | Old range rule | "Below mid → up" | Bias only |
|---|---|---|---|---|---|
| exec | real | 0.495 (3,001) | 0.493 (4,769) | 0.498 | 0.499 |
| exec | random walks | 0.490 | 0.497 | 0.493 | 0.502 |
| HTF | real | 0.491 (2,878) | 0.504 (4,388) | 0.493 | 0.503 |
| HTF | random walks | 0.502 | 0.497 | 0.499 | 0.502 |

**B4. Online draw-skill gate** (probes every 5 bars; gate state uses only probes already resolved):

| Gate | Set | Share of time on: mean (max) | `D` accuracy while on | While off |
|---|---|---|---|---|
| A's ramp (prior 60, full at 56%, on at skill ≥ 53%) | real | 2.3% (9.9%, RTY) | **0.464** (n 278) | 0.500 |
| A's ramp | random walks | **8.2%** (35.6%, RW15) | 0.488 (n 1,415) | 0.506 |
| One-sided 95% lower bound, design effect 3 (also with a 300-probe half-life) | real and random walks | 0% | — | 0.499 / 0.505 |

The autocorrelation of probe correctness on random walks was 0.25 / 0.07 / 0.01 at lags 1-3, a design effect of about **1.6**.

**B5. Pivot lag.** Share of 3-candle-swing raids whose swing never was a 5-bar pivot pool:

| Set | Share | Raided swings ≤ 5 bars old |
|---|---|---|
| Real | 0.715-0.746 (STL 0.728-0.753) | 0.443-0.514 |
| Random walks | 0.741-0.760 | — |

**B6. Structure and displacement events** (continuation in the event direction):

| Event | Real n | Real P | Random walk n | Random walk P |
|---|---|---|---|---|
| Displacement | 4,347 | 0.513 | 6,239 | 0.506 |
| Displacement + FVG | 1,918 | 0.506 | 3,520 | 0.508 |
| Displacement + FVG, with HTF | 965 | 0.540 (se 0.028) | 1,737 | 0.500 |
| Displacement + FVG, against HTF | 946 | 0.471 | 1,771 | 0.514 |
| Internal CHoCH | 2,467 | 0.501 | 3,126 | 0.504 |
| Swing CHoCH | 1,016 | 0.537 (se 0.027) | 1,422 | 0.501 |
| Swing CHoCH, with HTF | 485 | 0.553 | 685 | 0.508 |

Per market (`out_permarket.txt`):
- Displacement + FVG with vs against HTF: with > against in 7 of 8 markets (NQ 0.500 vs 0.507 is the exception).
- Swing CHoCH: at least 0.52 in 6 of 8 markets (ES 0.495 and RTY 0.489 are below).

**Ties.** See 1.1.

**Reading.**
- Across 8 markets nothing in the structure family calls the side at the engine's horizon. The race geometry is calibrated to within 0.5-1.2 pp.
- Two interaction cells (displacement + FVG × HTF; swing CHoCH) lean 3-4 pp toward continuation, but they were chosen after looking at the pooled table. They belong on the candidate ledger as hypotheses (ICTS-8), not in the score.
- **Limits:** about 1-2 years per market; hourly bars only; one label definition; overlapping windows; correlated index futures; no killzone timestamps on the Yahoo series.
- **Grade:** moderate as an original test. Combined with A, the siblings and S1-S5, the null on structure-derived side skill is **strong**.

---

## 3. Engine gap analysis (`baseline_v2.pine`)

All of A's line references were re-checked against the file. [A✓]

| # | Concept | Status | Where | What the engine does / differs |
|---|---|---|---|---|
| 1 | Swing points | **partial** | 90, 879-880 (`pivLen` 5); 65, 709-710 (`biasLen` 3); 1752-1776 | Strict-or-undocumented ties: `ta.pivothigh` tie semantics are not documented. Exact equal highs are 3-11% of 1H windows on futures and 22-40% of 5m windows on ES/6E (1.1). If ties are strict, these double tops make no pool at all and no EQ count. **[NEW-B]** → ICTS-9. The 5-bar lag hides 71-75% of raided short-term swings from `liqEvt` (geometric, see 1.1) |
| 2 | STH/ITH/LTH | **partial** | 506-516, 1779-1789 | Order proxied by timeframe tier; no nested ITH/LTH (`ict_liq` ICT-8) |
| 3 | BOS | **present** | 742-759; 1542-1547 | Close-based, protected low re-armed at each BOS. Correct |
| 4 | CHoCH | **present** | 760-773 (swing, protected); 749-753 (internal) | Protected-low convention (stricter than LuxAlgo's latest-swing convention, 1.4). The internal bias uses the same 3-bar pivots as the swing bias |
| 5 | MSS (ICT) | **missing** | — | Sweeps (1579-1582) and structure (708-782) are independent. Measured null (B1), so only an alert with measured follow-through is justified (ICTS-6) |
| 6 | Displacement | **present / over-weighted** | 897-903; `wM` 0.20 (156), 1893 | Good as a quality gate. As 20% of `D` it is null (51.3%, n 4,347). Weight should follow measured skill (ICTS-1) |
| 7 | Protected / weak extremes | **partial (computed, unused)** | 755-773; returned 782; read nowhere after 923-925 | Not used for invalidation (1343-1365), the HTF objective (1984-1989) or the panel |
| 8 | Dealing range / premium-discount | **wrong (definition), harmless for forecasting** | 727-779; 968; 2323-2333; 1354; 1783-1789 | Last pivot high/low, not [prot, weak]. Neither definition predicts the side (B3) → ICTS-4 for semantics plus the W1st readout |
| 9 | Structure → draw vector | **wrong (calibration)** | 155-162, 1891-1898; `wDraw` 30 (145); 691-693; 1964-2035 | Fixed weights assume skill. Measured `D` 47.4-52.7% on 8 markets; gated 41.6-52.7%. Draw pillar, side-first selection, ×0.5 counter-draw and the "⚠ COUNTER-DRAW" label all act on noise → ICTS-1 (with REG-3/4, BIAS-1/2) |
| 10 | Sweep outcome read | **wrong (sign)** | 1579-1582 | REJECT = −1 contradicted; HOLD ignores the HTF; stacked hits sum → ICT-9 (= ICTS-2) |
| 11 | 2022 model | **partial (pieces), rejected for scoring** | 1579-1582, 1895-1899, 1964-2035 | The "opposite pool" target race = geometry (B1b); PF < 1 in open backtests (S4b) |
| 12 | MMXM | **missing (implicit via proximity)** | 661-697 | No evidence for the ladder |
| 13 | Turtle soup | **partial** | 1579-1582 | See `ict_liq.final.md` |
| 14 | OTE | **n/a (by design)** | — | Entry concept |
| 15 | CISD | **n/a** | — | Entry trigger |
| 16 | ITH/LTH and HTF weak extreme as targets | **partial** | 1779-1789, 780-781 | HTF/STF pivots register about 4 HTF bars late; the current HTF leg's weak extreme is invisible until then (ICTS-7) |
| 17 | HTF trend regime in probability | **present, but the key carries no information at this horizon** [CORRECTED] | 1527-1531, 1284-1301 | A called it "good". At 30 1H bars `htfBias` has no side skill (B-ref), so the three-way split only dilutes samples. Sibling REG-1 / BIAS-6 own the change |
| 18 | First-passage race | **present (Terminal only)** | 446-482, 1343-1371, 2127-2130 | Calibrated (B2, B1b). Not visible in the Clean style → ICTS-3 |
| 19 | Bias table | **present** | 2294-2309 | Per-TF bias ≈ 50%. Keep the look (reference screenshot); honesty via BIAS-5 / ICTS-4 |
| 20 | Structure-shift alerts | **missing** | 2077-2094 | ICTS-6 |
| 21 | Directional-change scaling | **missing (not needed)** | — | Random-walk law; the empirical PoT already learns excursions |
| 22 | **[NEW-B]** Draw flip alert | **present, fires on noise** | 1896-1898, 2086-2088, 2094 | Fires on every `dirSide` change of a skill-less `D`. Gate it with ICTS-1 |
| 23 | **[NEW-B]** Structure claims measured per chart | **missing** | — | No ledger bit for "target = weak extreme", "target on HTF side", "recent MSS / displacement toward target" → ICTS-8 (on ICT-1 / CAL-3) |

---

## 4. Proposals (best first; 9)

**Common Pine notes:**
- New structural state updates inside `if barstate.isconfirmed` (ENGINE, line 1518).
- Functions must be declared before first use, and the globals they read before them.
- `request.*` tuple budget: "All the `request.*()` function calls in a script taken together cannot return more than 127 tuple elements" (`docsrc/jabez4jc_pinescriptv6/writing_scripts/limitations.md`, around line 274). The current total is 3×12 + 5 + 6 + 5 = 52.

**Overlap map with sibling proposals:**

| This report | Sibling proposals |
|---|---|
| ICTS-1 | Common evidence gate for `D`. REG-3's efficiency factor multiplies into it. REG-4 (`ctrMult` 0.85) becomes the "Always" default. BIAS-1/2, if built, replaces the probe with its prequential side skill. CAL-7 / SKEP-6 share the "neutral until earned" principle |
| ICTS-2 | **Implement as `ict_liq.final.md` ICT-9** (which merged ICTS-2 and BIAS-4) |
| ICTS-3 | Same math as QPOT-06 (Terminal "NEXT ▲/▼") and BIAS-1; this one is the Clean tooltip for the active target |
| ICTS-4 | Prerequisite for ICT-4 (IRL/ERL), ICT-1 bit 14 (ERL), and the `ict_pd.final.md` P/D items |
| ICTS-8 | Extends ICT-1 (CAL-3/CAL-4 candidate ledger) with structure bits |
| ICTS-9 | Feeds the EQ density (`eqCount`), which calib_ml finds supported (+0.29, t +3.6, 1H) |
| ICTS-6 | Aligns with BIAS-7 (HTF candle-close alerts) and WYK-4 (event layer, zero forecast weight) |

### ICTS-1 (P1, M) · Evidence-gated draw: `D` steers target choice only after this chart shows statistically significant side skill [A, CORRECTED gate]

**Why:**
- The draw pillar (`wDraw` 30, the heaviest), the ×0.50 counter-draw multiplier (692-693), draw-side-first selection (1975) and 2× flip hysteresis all assume `D` knows the direction.
- On 11 markets (A + B) `D` scored 47.4-52.7%, inside the random-walk band. Sibling REG-3 finds side-first selection loses 9-12 pp of first-touch accuracy against geometry.
- **[CORRECTED]** A's ramp switched on spuriously on random walks (8.2% of the time on average, 35.6% on one) and was followed by worse-than-coin accuracy (B4). The gate below never switched on falsely in B's simulation.
- **Decision-history note:** in "Measured" mode, charts without measured skill lose draw-side-first selection. That changes a recorded decision ("Selection is draw-side first"), so it is exposed as an input with "Always" (classic) one click away. The evidence for the change is strong (§2.3). The user should confirm the default.

**Inputs** (G_FLOW, after line 166):
```pine
string drawMode = input.string("Measured", "Draw Steering", options = ["Measured", "Always", "Off"], group = G_FLOW,
  tooltip = "Measured: the draw vector steers target choice only after it has called the first-touched side significantly better than a coin on this chart. Always: classic. Off: display only.")
float  dSkK     = input.float(1.5, "Skill Probe Distance (ATR)", minval = 0.5, step = 0.25, group = G_FLOW)
int    dSkEvery = input.int(5, "Skill Probe Every N Bars", minval = 1, maxval = 50, group = G_FLOW)
float  dFloor   = input.float(0.25, "Draw Weight Without Skill", minval = 0.0, maxval = 1.0, step = 0.05, group = G_FLOW)
```
Constants (no inputs, to keep the panel small): prior 60 pseudo-probes at 50%, design effect 2.0, z 1.96. B measured a design effect of about 1.6 on random walks; 1.96·√2 ≈ 2.8 ≈ the 1.645·√3 that B tested.

**Type** (TYPES, after `Trial`, around 396):
```pine
type DProbe
    float up
    float dn
    int   bar0
    int   dS      // dirSide at open
    int   sS      // sign of sV
    int   mS      // sign of mV
    int   lS      // sign of liqEvt
    int   hS      // htfBias
```

**State** (after line 1080): `var array<DProbe> dq = array.new<DProbe>()`, `var array<float> skN = array.new<float>(5, 0.0)`, `var array<float> skK = array.new<float>(5, 0.0)` (cells: 0 D, 1 structure, 2 displacement, 3 raids, 4 HTF bias), `var float drawRho = 1.0`.

**Helpers** (after the state, before first use):
```pine
f_skill(int c) =>
    (skK.get(c) + 30.0) / (skN.get(c) + 60.0)
f_skLB(int c) =>
    f_skill(c) - 1.96 * math.sqrt(0.25 * 2.0 / (skN.get(c) + 60.0))
f_skBook(int c, int s, int y) =>
    if s != 0
        skN.set(c, skN.get(c) + 1.0)
        skK.set(c, skK.get(c) + (s == y ? 1.0 : 0.0))
    s
```

**Resolve** (ENGINE step 2b, right after the Trial loop at about 1557):
- For each probe with `bar_index > q.bar0`: `u = high >= q.up`, `d = low <= q.dn`.
- If exactly one of them is true, book all five cells with `y = u ? 1 : -1` and remove the probe.
- If both are true, or `bar_index - q.bar0 >= H`, remove it unbooked.
- At most about H / `dSkEvery` (≈ 6) probes are open.

**Open and gate** (step 14, right after `dirSide` at 1895; `sV` and `mV` are in scope):
```pine
if bar_index % dSkEvery == 0 and dq.size() < 64
    dq.push(DProbe.new(close + dSkK * atr, close - dSkK * atr, bar_index, dirSide,
      int(math.sign(sV)), int(math.sign(mV)), int(math.sign(liqEvt)), htfBias))
drawRho := drawMode == "Always" ? 1.0 : drawMode == "Off" ? 0.0 : math.max(dFloor, f_clamp((f_skLB(0) - 0.5) / 0.03, 0.0, 1.0))
int dirSel = drawRho >= 0.5 ? dirSide : 0
```

**Use:**
- **Step 17 (1948):** `lv.evaluate(close, atr, anchors, confTol, drawD * drawRho, nz(potSig), nz(potMu))`. At the floor (0.25) the draw pillar spans ±3.75 points, and `ctrMult` never fires because |0.25·D| < `dGate` 0.35 (692).
- **Step 19:** replace `dirSide` with `dirSel` in `elig` (1975), `ctrHold` (2001), `curElig` (2004), `activeCtr` (2029) and the `⊘ INVALIDATED` ghost condition. The HTF objective (1985) keeps `dirSide` (display only).
- **`drawFlip` (1896-1898):** `drawFlip := lastDirSide != 0 and inCalc and drawRho >= 0.5`.
- **REG-3, if implemented:** pass `drawD * drawRho * regFactor`.
- **UX:**
  - Terminal DRAW row (2338-2342): `▲ +0.42 · skill 51% (n 812) · ×0.25`.
  - Full accuracy view: one row with the five component skills.
  - Data window: `plot(drawRho * 100, "Draw weight %", display = display.data_window)`.

**Cost:** ≤ 64 probes (≈ 6 in practice), O(1) each per confirmed bar.

**Measurement:** the ledger EDGE (1461-1499) before and after on NQ, ES, EURUSD, XAU and BTC at 15m and 1H; also the count of `drawFlip` events and of target side switches.

**Evidence:** strong (null on `D`'s skill: A + B on 11 markets, random-walk nulls, REG-3, S1-S5). Gate design: moderate (B4 simulation).

**Risk:**
- The "Draw Direction" feature from the product spec becomes mostly neutral on most charts. The floor keeps the pillar visible and the readout honest.
- On a chart where `D` has real skill, it takes about 400-600 resolved probes before the gate opens.

**Effort:** M.

### ICTS-2 (P1, S) · Fix the raid → draw mapping: implement `ict_liq.final.md` ICT-9 [A, merged]

**What ICT-9 specifies** (replaces 1580-1582):
- REJECT and NEUTRAL add 0.
- HOLD with the HTF swing adds +1 toward the raided side; against the HTF −0.5; neutral HTF +0.5. All are multiplied by `lv.tier()`.
- At most one event per side per bar (the strongest tier).
- 1-tick pokes within `eqTol` are ignored.
- The HOLD distance is a dedicated `holdATR` (0.20) instead of the display depth `zoneATR`.

**This domain's support:** A: HOLD against the HTF reverses 56% (n 381); REJECT continues 52.6% (n 1,402). B1: the MSS that ICT builds on a rejected raid is 49.4% (n 4,032).

**Evidence:** strong (no reversal after REJECT) / moderate (HOLD alignment). **Effort:** S.

### ICTS-3 (P2, S) · "Which pool first": the calibrated first-touch race against the opposing pool, in the Clean label tooltip [A, CORRECTED placement]

**Why:**
- The user's question is which liquidity is taken next. Direction from structure is a coin flip, but the race between two known pools is geometry, and B measured it calibrated on 8 markets: 65.3% vs 65.8%; after an MSS 55.7% vs 56.8%.
- The engine already computes it (`f_invalidation` 1343-1365 → `f_raceH`; `f_raceAdj` 1367-1371) but shows it only in the Terminal HUD.

**[CORRECTED]** A appended a third line to the Clean label. That breaks the reference two-line "Target / PoT" look, so the default is the tooltip.

**Spec:**
- `f_invalidation` also returns the opposing level's index:
  - loop with `for [i, lv] in pool`;
  - keep `int oppI = -1` and set `oppI := i` when `best` updates;
  - return `[inv, d / risk, p, oppI]`.
- Update both destructurings with distinct names: 1428 `[inv, rr, pR, oI0]` and 2127 `[i0, i1, i2, i3]`.
- Input (G_DOL): `string raceShow = input.string("Tooltip", "First-Touch Odds", options = ["Tooltip", "Label line", "Off"], group = G_DOL)`.
- In the Clean branch (2213-2226):
  ```pine
  string oppTag = i3 >= 0 ? f_shortName(pool.get(i3).kind, pool.get(i3).src) : "-1.5 ATR"
  string rTxt   = "1st vs " + oppTag + ": " + str.tostring(invWin * 100.0, "0") + "%"
  ```
  - "Tooltip" mode: `tip += "\n" + rTxt + " (target touched before the opposing pool, among races decided within " + str.tostring(H) + " bars; corrected by this chart's " + str.tostring(raceSt.get(0), "0") + " decided races)"`.
  - "Label line" mode: also append `"\n" + rTxt` to the label text.
  - `i3` must be kept in a global `var int invOpp` set next to `invWin` (2127-2130).
- With no opposing pool within `maxATR`, the barrier is 1.5 ATR, and the tag says so.
- Optional: one dotted line at the opposing pool's near edge (1 line object).

**Evidence:** strong (math; B2 and B1b calibration). **Effort:** S.

### ICTS-9 (P2, S) · Tie-safe swing pivots ("leftmost wins") with the tie count fed to EQ density [NEW-B]

**Why:**
- `ta.pivothigh`'s tie rule is undocumented (reference text in 1.1). Exact equal highs at the window maximum occur in 3-11% of 1H windows on futures and 22-40% of 5m windows on ES/6E.
- If Pine treats ties strictly, a double top inside the window yields **no pivot**: no BSL pool, no EQ count, no OB BOS reference (`obSwingH`, 1754), and no HTF/STF structure pivot. Those are exactly ICT's "equal highs".
- A leftmost-wins rule recovers 11.5% (ES 5m) to 22.5% (6E 5m) of all pivots.
- EQ is the one density input with measured support (calib_ml: +0.29, t +3.6, 1H).

**Spec** (PURE HELPERS, before 699):
```pine
// Swing high of strength p, ties resolved leftmost-wins: strictly above the p older
// bars, at least equal to the p newer bars. Returns [price or na, newer bars that printed the same price].
f_pivHi(float src, int p) =>
    float hh    = ta.highest(src, p)
    float older = hh[p + 1]
    float pv    = na
    int   ties  = 0
    if bar_index >= 2 * p and src[p] > older and src[p] >= hh
        pv := src[p]
        for k = 0 to p - 1
            if math.abs(src[k] - src[p]) <= syminfo.mintick * 0.5
                ties += 1
    [pv, ties]
f_pivLo(float src, int p) =>
    float ll    = ta.lowest(src, p)
    float older = ll[p + 1]
    float pv    = na
    int   ties  = 0
    if bar_index >= 2 * p and src[p] < older and src[p] <= ll
        pv := src[p]
        for k = 0 to p - 1
            if math.abs(src[k] - src[p]) <= syminfo.mintick * 0.5
                ties += 1
    [pv, ties]
```

**Notes:**
- `ta.highest`/`ta.lowest` are called unconditionally every bar (global or series-function scope). A history reference on a series result is already used at line 892.
- `hh` covers bars 0..p−1 (newer); `hh[p+1]` covers p+1..2p (older).

**Use:**
- Lines 879-880: `[ph, phTies] = f_pivHi(high, pivLen)` and `[pl, plTies] = f_pivLo(low, pivLen)`.
- New-level paths (1761-1763 and 1773-1775): `nh.eqCount := phTies`, `nlo.eqCount := plTies`. The merge path already counts one EQ per separate print.
- In `f_structure` (709-710): `[pvHi, tH] = f_pivHi(high, len)`, `[pvLo, tL] = f_pivLo(low, len)`. The tie counts are unused there; the tuple shape is unchanged.

**Check before shipping:** a 10-line TradingView script that counts `ta.pivothigh` vs `f_pivHi` on ES 5m. If `ta.pivothigh` already keeps one of the tied bars, the change only adds explicit semantics plus the EQ count.

**Evidence:** moderate (descriptive tie frequencies; EQ lift from calib_ml). **Risk:** slightly more pools on coarse-tick charts (these are real equal highs). **Effort:** S.

### ICTS-4 (P2, S) · ICT's dealing range from `f_structure` ([protected, weak] of the current leg) and an honest "weak-first" readout [A + NEW-B readout]

**Why:**
- `rngH/rngL` shrink to a sub-swing after any internal lower high or higher low. That corrupts the Terminal P/D %, the `htfEQ` anchor (968, 1931), the `f_invalidation` fallback (1354), and every dealing-range proposal in the sibling studies.
- Neither definition forecasts the side (B3). The value is correct semantics plus one honest number.

**Code** (in `f_structure`, after the bias block (ends at 773) and before the range extension at 775-779):
```pine
float drH = bias == 1 ? legH : bias == -1 ? protH : rngH
float drL = bias == 1 ? protL : bias == -1 ? legL : rngL
```
- Return `drH[1], drL[1]` in place of `rngH[1], rngL[1]` (782). The tuple shape is unchanged, so no call site changes.
- **Checks:**
  - `protL` (or `protH`) is set at every transition into a bias, so there are no `na` holes.
  - The neutral state falls back to the old range.
  - Registry prominence (1783-1789) uses the values only as magnitudes.

**Readout** (Terminal ZONE cell, 2327-2332):
```pine
float wf = sb == 1 ? pos : sb == -1 ? 1.0 - pos : na
zn := (pos >= 0.5 ? "PREM " : "DISC ") + str.tostring(pos * 100.0, "0") + "%" + (na(wf) ? "" : " · W1st " + str.tostring(wf * 100.0, "0") + "%")
```
- "W1st" is the driftless probability that the weak extreme is taken before the protected one. B2 measured it calibrated (65.3% vs 65.8%).
- Tooltip text: "In discount of a bullish leg the protected low is nearer than the weak high."

**Evidence:** none for edge (B3). Readout: strong (B2). **Risk:** `htfEQ` values change, so some confluence scores shift. **Effort:** S.

### ICTS-8 (P2, S on top of ICT-1) · Structure bits on the candidate ledger: let each chart measure ICT's structure claims [NEW-B]

**Why:**
- The only structure effects that survived in B's data are two interaction hints:
  - displacement + FVG with vs against the HTF swing: 54.0% vs 47.1%, 7 of 8 markets;
  - swing CHoCH continuation: 53.7%, 6 of 8 markets.
- Both were selected after looking. Building them into scoring would be data-snooping. ICT-1's candidate ledger already grades every pool against `f_potBase` with a block-cluster z-gate and neutral defaults, which is the right home for them.

**Spec.** Raise ICT-1's NF from 16 to 21 and add bits, set at snapshot (step 17, after 1948):

| Bit | Name | Rule |
|---|---|---|
| 16 | WEAKX | Target is within `eqTol·atr` of the exec, STF or HTF weak extreme (`legH` in bull / `legL` in bear; needs ICTS-4/7 values) |
| 17 | HTFSIDE | `lv.side == htfBias` |
| 18 | MSSDIR | An execution MSS (ICTS-6 state) pointing to `lv.side` fired within the last H bars |
| 19 | DISPHTF | `dispDir == lv.side` and `dispDir == htfBias` and `bar_index - dispBar <= dispHL` |
| 20 | CHOCH | The exec swing bias flipped to `lv.side` within the last H bars |

- Lifts, gates and UX are exactly as in ICT-1, e.g. `WEAKX ×1.00 (n 214, z 0.3) ~`.
- Keep DRAW (bit 11), which already measures `D`'s side alignment at target level.

**Evidence:** weak (hints) / moderate (method). **Risk:** more bits mean more multiple comparisons. ICT-1's |z| ≥ 2 gate and bounds apply (SKEP-9). **Effort:** S once ICT-1 exists.

### ICTS-5 (P3, S) · Structural anchors: protected-swing invalidation option and a weak-extreme tag on the HTF objective [A✓]

**Why:** ICT/SMC traders put risk beyond the protected low and aim at the weak high. `f_invalidation` uses the nearest opposing pool, often an inner pool, so the Terminal R:R, WIN≤H and EV describe a different trade. This is semantic alignment, not edge: B2 shows the odds are geometry.

**Spec:**
- Input `invMode = ["Nearest Opposing Pool", "Protected Swing (Exec)", "Protected Swing (STF)"]` (G_DOL).
- In `f_invalidation`, when protected mode is on and `tgt.side` equals that TF's swing bias:
  - `sw = tgt.side == 1 ? exeProtL : exeProtH` (or the `stf*` pair; already returned at 924-925);
  - if `sw` is on the correct side of `close` and within `maxATR`, `inv := sw - tgt.side * buf`;
  - else use the current rule.
- Step 19 (1984-1989): if the HTF objective lies within `eqTol·atr` of `htfRH` (bull) or `htfRL` (bear) after ICTS-4, append `· WEAK H/L` to its label.
- Terminal: one dotted `PROT` line at the exec protected level.

**Risk:** wider stops show a lower R:R (honest). **Effort:** S.

### ICTS-6 (P3, S) · Structure-shift alerts (HTF swing flip; execution MSS after a raid) with this chart's measured follow-through [A, refined]

**Why:** ICT users want these alerts. The MSS measures 49.4% (n 4,032), so each alert carries the chart's own rate instead of an implied promise.

**Spec:**
- **Globals:**
  ```pine
  float stlP = ta.pivotlow(low, 1, 1)
  float sthP = ta.pivothigh(high, 1, 1)
  var float lastStl = na
  var float lastSth = na
  var int mssArmD = na
  var float mssLvlD = na
  var int mssArmU = na
  var float mssLvlU = na
  var int mssEvt = 0
  var array<float> mssSt = array.new<float>(2, 0.0)
  ```
- **Arming (step 3).** On any `hit and lv.isLiquidity()` (any raid, not only REJECT; B1's definition):
  - BSL raid: `mssLvlD := lastStl` and `mssArmD := bar_index`;
  - SSL raid: the mirror.
- **Each confirmed bar:**
  - `mssEvt := 0`.
  - If `bar_index - mssArmD <= mssWin` (input, 8) and `close < mssLvlD`: set `mssEvt := -1`, disarm, and open a follow-through probe (`close ∓ 1.5·atr` within H, booked into `mssSt` [n, wins]). Mirror for up.
  - After the checks, update `lastStl`/`lastSth` from `stlP`/`sthP`. They are known one bar late, which is already non-repainting.
- **HTF flip:** `bool htfShift = barstate.isconfirmed and htfBias != htfBias[1] and htfBias[1] != 0`. It is non-repainting via the `[1]` + `lookahead_on` read.
- **Alerts** (after 2094):
  ```pine
  alertcondition(htfShift, "HTF Structure Shift", "DOL Engine: higher-timeframe swing structure flipped on {{ticker}} ({{interval}})")
  alertcondition(mssEvt != 0, "Execution MSS", "DOL Engine: market structure shift after a liquidity raid on {{ticker}} ({{interval}})")
  ```
  plus an `alert()` call with text such as `MSS ▼ after BSL raid · follow-through here 49% (n 171)`.
- **Terminal row:** `STRUCT  MSS ▼ 3b ago · FT 49% (n 171)`.

**Evidence:** none for edge (B1, S3, S4). Value is UX and transparency. **Risk:** alert noise on low timeframes; `mssWin` and an optional displacement gate reduce it. **Effort:** S.

### ICTS-7 (P3, M→S) · Register the HTF/STF weak extreme before pivot confirmation [A, CORRECTED cost]

**Why:** The current HTF leg's weak extreme, the textbook objective, enters the registry only about 4 HTF bars late. The benefit is correct labelling and HTF tier and freshness. Tier itself adds little beyond distance, so the evidence is weak.

**[CORRECTED]**
- With ICTS-4, `drH` already *is* `legH` in bull bias and `drL` is `legL` in bear bias.
- Only the print time is missing: add one element, `wkT[1]` (the `time` at which the weak extreme last set a new extreme), to each `f_structure` tuple. That is 13 × 3 = 39, total 55 of 127. A's plan of +4 per call is not needed.

**Spec** (step 10, 1779-1789, confirmed bars):
- If `htfBias == 1`, `(htfRH - close)/atr >= minDistATR`, and `htfRH` is not already in `extReg` (`f_pushExt` dedups by price), call `f_pushExt(extReg, htfRH, true, 2, f_barAtTime(htfWkT, anchorMax), prom, hmH)`.
- Mirror for bear bias.
- Same for STF with `src` 1.
- The step-4 raid check (1591-1597) removes the entry when a higher high prints. The new extreme registers once price leaves it by `minDistATR`.

**Risk:** registry churn (dedup handles it). **Effort:** S with ICTS-4 in place.

### Considered and rejected
- **MSS / CHoCH / CISD as scoring or `D` inputs.** Null (B1 n 4,032; B6 internal CHoCH n 2,467; S3). The swing-CHoCH and displacement × HTF hints go to the ledger (ICTS-8), not the score.
- **The 2022 model or MMXM as a target engine.** The "opposite pool" race equals geometry (B1b). The models lose in open backtests (S4, S4b, S4c).
- **OTE / Fibonacci levels.** No level-specific effect (S10); geometry is already in the race model.
- **Premium/discount as a draw input.** Null (B3: 49.1-49.5%).
- **A's linear skill ramp.** False activations on random walks and worse-than-coin accuracy while on (B4). Replaced by the significance gate.
- **A multi-feature learned `D`.** It was worse than a coin out of sample (A). BIAS-1, if built, must stay prequentially gated.
- **3-candle STH pools as targets.** 71-75% of raids hit such swings, but the share equals the random-walk share and the swings are trivially near. They are useful only for ICTS-6's MSS level.
- **"Regime-confirmed" bias table.** Agreement 51.7% vs disagreement 52.1% (A). Not worth a UX change.
- **Directional-change leg or a Schmidhuber cubic term in `D`.** 47-56% and inconsistent signs (A). Coefficients are tiny (S6), and short-term trend has decayed (S7c).

---

## 5. Notes for implementers

**Order of work:**
1. ICT-9 (= ICTS-2), ICTS-4 and ICTS-9: small and independent.
2. ICTS-1: it changes selection behaviour, so record ledger EDGE, the `drawFlip` count and target switches before and after on NQ, ES, EURUSD, XAU and BTC (15m and 1H).
3. ICTS-3 and ICTS-5 both touch `f_invalidation`'s signature. Update both destructurings (1428, 2127) in one edit.
4. ICTS-8 after ICT-1.

**Non-repainting:**
- All new state changes sit in the confirmed-bar ENGINE block.
- ICTS-6 uses the `[1]`-offset `htfBias`, and ICTS-7 the `[1]`-offset `wkT`.
- ICTS-9's pivots use only closed bars (`src[p]` with `p` newer bars).
- No live value enters scoring.

**Pine specifics:**
- `math.sign()` returns a float; wrap it in `int()` for `DProbe`.
- Tuple names must be distinct.
- Declare `DProbe` in TYPES before STATE uses it.
- `f_skill`, `f_skLB` and `f_skBook` read global arrays, so declare them after STATE.
- `f_pivHi`/`f_pivLo` must sit before `f_structure` (699) because `f_structure` calls them.
- In `f_pivHi`, compute `ta.highest` into a variable before taking its history (`hh[p + 1]`), so the call runs every bar.

**Decision history:** ICTS-1 "Measured" mode alters draw-side-first selection on charts without skill. Keep "Always" available and ask the user to confirm the default.

**Measurement:** with ICTS-1 the Full panel shows component skills. If a component sits at ≤ 50% on most symbols over long histories, set its weight input default to 0. Displacement (`wM`) is the likely first candidate (B6: 51.3%), then `wL` (after ICT-9).

---

## 6. Sources

**Primary and secondary (A, re-checked by B where marked):**
- Taylor, V. (2026). *Evaluating the Predictive Validity of ICT's Accumulation-Manipulation-Distribution (AMD) Model on CME E-Mini NASDAQ-100 Futures.* arXiv 2610.35887. https://arxiv.org/abs/2610.35887 **[A✓, full text]**
- Safari, S. A. & Schmidhuber, C. (2025). *Trends and Reversion in Financial Markets on Time Scales from Minutes to Decades.* arXiv 2501.16772. https://arxiv.org/abs/2501.16772 **[A✓, full text]** · Schmidhuber, C. (2021). arXiv 2006.07847. https://arxiv.org/abs/2006.07847
- Glattfelder, J. B., Dupuis, A. & Olsen, R. B. (2011). *Patterns in high-frequency FX data: discovery of 12 empirical scaling laws.* arXiv 0809.1040; *Quantitative Finance* 11(4). https://arxiv.org/abs/0809.1040 **[A✓, exists]**
- Tangirala, K. H. (2026). SSRN 7483658. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7483658 [A, not re-fetched]
- Mahadzva, S. (2026). SSRN 7430998. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7430998 [A, not re-fetched; grade weak]
- Nordman Algorithms (2026). *ICT Displacement and the Market Structure Shift.* https://www.nordman-algorithms.com/blog/ict-displacement-market-structure-shift/ · *BOS vs CHoCH.* https://www.nordman-algorithms.com/blog/bos-vs-choch/ [A, not re-fetched]
- IvanSetuper (2026). *ICT 2022 Model - Liquidity Sweep, MSS & FVG Entry.* https://www.tradingview.com/script/Doc312Ae-ICT-2022-Model-Liquidity-Sweep-MSS-FVG-Entry/ [A, not re-fetched]
- Moskowitz, T., Ooi, Y. H. & Pedersen, L. H. (2012). *Time Series Momentum.* JFE 104(2). http://docs.lhpedersen.com/TimeSeriesMomentum.pdf
- Chang, P. H. K. & Osler, C. L. (1999). *Economic Journal* 109. https://www.jstor.org/stable/2565638 · Savin, G., Weller, P. & Zvingelis, J. (2007). *J. Financial Econometrics.* https://www.biz.uiowa.edu/faculty/gsavin/papers/hsrevision_paw_10%2019%2006.pdf
- Tradeify (2026). *Fibonacci Retracements and Extensions Put to the Test.* https://tradeify.co/education/fibonacci-retracements-and-extensions [A, not re-fetched]
- Quarter Sequence, *ICT Market Structure* (lecture quotes with timestamps). https://quartersequence.com/the-study/ict-market-structure/ [A, not re-fetched]
- LuxAlgo concept library: https://www.luxalgo.com/library/concept/market-maker-models/ · https://www.luxalgo.com/library/concept/model-2022/ · https://www.luxalgo.com/library/concept/change-in-state-of-delivery/ · https://www.luxalgo.com/library/concept/displacement/ [A, not re-fetched]
- ProEA (2026). https://proea.app/en/blog/best-bos-choch-indicator-tradingview · https://proea.app/en/blog/turtle-soup [A, not re-fetched] · TMGM. https://www.tmgm.com/en/academy/trading-academy/market-maker-model

**[NEW-B] Added by B:**
- Lempérière, Y., Deremble, C., Seager, P., Potters, M. & Bouchaud, J.-P. (2014). *Two centuries of trend following.* arXiv 1404.3274. https://arxiv.org/abs/1404.3274
- Kurth, J. G., Eisler, Z., Rej, A. & Bouchaud, J.-P. (2026). *Is Trend Still Your Friend? A Microstructural Account of the Demise of Short-Term Trend-Following.* arXiv 2607.01550. https://arxiv.org/abs/2607.01550
- Zawadowski, A. G., Andor, G. & Kertész, J. (2006). *Short-term market reaction after extreme price changes of liquid stocks.* arXiv cond-mat/0406696; Quantitative Finance 6(4). https://arxiv.org/abs/cond-mat/0406696
- Heston, S. L., Korajczyk, R. A. & Sadka, R. (2010). *Intraday Patterns in the Cross-section of Stock Returns.* arXiv 1005.3535; J. Finance 65(4). https://arxiv.org/abs/1005.3535
- Mesfin, M. (2026). *Structural Limits of OHLCV-Based Intraday Momentum Signals in MNQ Futures.* arXiv 2605.04004. https://arxiv.org/abs/2605.04004
- Zhu, H., Jiang, Z.-Q., Li, S.-P. & Zhou, W.-X. (2015). *Profitability of simple technical trading rules of Chinese stock exchange indexes.* arXiv 1504.04254. https://arxiv.org/abs/1504.04254
- Houweling, T. (2025). *The Hidden Constant of Market Rhythms: How 1-1/e Defines Scaling in Intrinsic Time.* arXiv 2511.14408. https://arxiv.org/abs/2511.14408
- Gurrib, I., Nourani, M. & Bhaskaran, R. K. (2022). *Energy crypto currencies and leading U.S. energy stock prices: are Fibonacci retracements profitable?* Financial Innovation 8. https://doi.org/10.1186/s40854-021-00311-8
- Brock, W., Lakonishok, J. & LeBaron, B. (1992). *Simple Technical Trading Rules and the Stochastic Properties of Stock Returns.* J. Finance 47(5). https://doi.org/10.1111/j.1540-6261.1992.tb04681.x [classic, not re-fetched]
- Sullivan, R., Timmermann, A. & White, H. (1999). *Data-Snooping, Technical Trading Rule Performance, and the Bootstrap.* J. Finance 54(5). https://doi.org/10.1111/0022-1082.00163 [classic, not re-fetched]
- Marshall, B. R., Cahan, R. H. & Cahan, J. M. (2008). *Does intraday technical analysis in the U.S. equity market have value?* J. Empirical Finance 15(2). https://doi.org/10.1016/j.jempfin.2007.04.003 [not re-fetched]
- Grant, J. L., Wolf, A. & Yu, S. (2005). *Intraday price reversals in the US stock index futures market: A 15-year study.* J. Banking & Finance 29(5). https://doi.org/10.1016/j.jbankfin.2004.05.004 [not re-fetched]
- LuxAlgo *Smart Money Concepts* (public mirror, CC BY-NC-SA 4.0), read for algorithm only, no code copied: https://github.com/RouZuoMong2003/SmartMoneyConcepts-LuxAlgo
- `smartmoneyconcepts` Python library, `smc.py` (swing, BOS/CHoCH, liquidity, retracements): https://github.com/joshyattridge/smart-money-concepts
- truongxxxx, *ict-backtest* (2022 model / Silver Bullet / London on ES/NQ 2014-2026): https://github.com/truongxxxx/ict-backtest
- AaroNLaU0307, *quant-backtest-framework* (multi-timeframe SMC falsification): https://github.com/AaroNLaU0307/quant-backtest-framework
- hindsight-finance, *Silver-Bullet-AM-Session* (displacement parameters only; no results published): https://github.com/hindsight-finance/Silver-Bullet-AM-Session

**Pine v6 docs used:**
- `docsrc/jabez4jc_pinescriptv6/reference/ta.md` (`ta.pivothigh`, ties undocumented).
- `docsrc/jabez4jc_pinescriptv6/writing_scripts/limitations.md` ("Tuple element limit": 127 across all `request.*()` calls).

**Data and code:**
- **A:** `study/ict_struct_tools/` (Yahoo 60m NQ=F, GC=F, EURUSD=X, Nov 2024-Nov 2026).
- **B:** `study/ict_struct_b_tools/` on the project's local copies: `sim/data/{nq,gc,eu}.csv`, `study/amt_data/cme/{ES,RTY,YM,CL}/*_1h_*.csv`, `study/classic_tools/btc_1h.csv` (last 20,000 bars), `sim/rw11-18.csv`, and `study/smt_data/cme/{ES,NQ,GC,6E}/*_5min_*.csv`.

**Sibling studies cross-referenced** (`brief/study/`): `ict_liq.final.md` (ICT-1, ICT-4, ICT-8, ICT-9; E1-E15; B7), `ict_pd.final.md`, `bias_dol.md` (BIAS-1..7), `quant_regime.md` (REG-1..4), `quant_pot.md` (QPOT-01, QPOT-06), `calib_ml.md` (CAL-3/4/7; EQ and tier lifts), `skeptic.md` (SKEP-6, SKEP-9), `price_action.md` (PA-4), `smc_impl.md`, `wyckoff_sd.md` (WYK-4).
