# ICT PD Array Matrix: combined final study (researcher A + researcher B)

Domain: premium/discount and equilibrium; the PD array hierarchy (old highs/lows, rejection block, order block, FVG (BISI/SIBI), liquidity void, breaker, mitigation block, propulsion block, vacuum block, volume imbalance, opening gaps NWOG/NDOG, BPR, consequent encroachment, mean threshold); inversion FVGs; which arrays are TARGETS and which are ENTRY zones; exact candle rules; how ICT ranks arrays for the draw; HTF arrays as magnets; "filled", "respected", "disrespected".

Engine file: `brief/baseline_v2.pine` (line numbers below; identical to `/home/user/m/indicators/dol_engine.pine`).

Provenance markers used in this file:
- **[A]** Researcher A's finding, kept as is.
- **[B-verified]** A's finding re-checked by B (source re-read, sibling verification, or B's own replication agreed).
- **[B-corrected]** A's finding changed by B. The old claim and the reason are given.
- **[B-new]** Added by B.

B's own tests are reproducible: scripts and raw outputs are in `study/ict_pd_b_tools/` (`e1_fvg.py` … `e6_ifvg_htf.py`, `out_e*.txt`).

---

## 0. Executive summary

1. **PD arrays are not magnets beyond distance. [B-verified, strengthened]** A cited five external controlled studies (Nordman FVG 73.0% vs 72.9% random; Nordman OB 73.7% vs 73.7%; S&P daily bullish FVG 69% vs 69%; BTC 1H 75.6% vs 72.4%; Barot SSRN about +5 pp reaction, no tradeable edge). B could not re-fetch those pages this session (network blocked, see 2.9), so B **replicated the test with the engine's own method**:
   - the engine's origin lockout (3 bars, price ≥ 1 ATR away, untouched);
   - the engine's distance-matched random baseline (the empirical H-bar excursion surface, i.e. `f_potBase`);
   - local data: CME ES/NQ/RTY/YM/CL 1H and 5m, BTC 1H 2016-2025, SPX/NDX daily 1999-2018.

   Result: FVG near-edge reach minus baseline is **+0.4 pp (z 0.3, n 1,756) CME 1H; -0.6 pp (n 4,950) CME 5m; -1.6 pp (z -1.8, n 3,337) BTC 1H; -2.9 pp (z -1.5, n 935) daily**. Order blocks: -1.8 to +2.4 pp. 4H FVGs used on the 1H chart: +1.6 pp (CME, n.s.) and -2.8 pp (BTC, z -2.3). Whether an array is reached within H bars is a distance and volatility question. The engine's PoT model already answers it.

2. **Displacement "quality" is the wrong prior for a target. [B-corrected and strengthened]** A argued that large gaps and large displacement "fill LESS often", using raw fill rates (BTC daily terciles 78.7/61.7/46.0%; SPY gaps over 1% fill 26-33% same day). **Those raw rates are mostly distance.** A bigger gap has a farther far edge.
   - Against the distance-matched baseline, gap size has no consistent effect on CME (full fill by size tercile: raw 67/63/46%, baseline 67/62/49%).
   - Large **opening** gaps on index futures fill *more* than distance predicts (+7.4 pp, z 2.2, see point 6).
   - What B does find: the **engine's FVG quality score is not a target signal**:
     - CME 1H: FVGs the engine *rejects* (q < 0.45) beat the baseline by +7.0 pp (z 3.3); FVGs it accepts sit at -1.8 pp.
     - BTC 1H: the top tercile of middle-candle displacement is at -5.5 pp (z -3.8).
     - 5m and daily: flat.

   Quality is never positive in any dataset. The array density term `0.5·qual + … + 0.20·HTF` (line 687) should become neutral (ICTPD-1).

3. **Breakers: the engine's definition is wrong, and breakers are weak targets. [B-verified + B-new data]** A's diagnosis is correct: the `tookL/tookH` gate (1691, 1706, 1734, 1747) tests the OB's *own origin* sweep, whereas ICT's sweep is made by the leg *leaving* the block. B measured it against the open-source ICT breaker template (zigzag C-D-E, old extreme taken, close through D):
   - the engine reproduces only **11-24%** of template breakers;
   - removing the gate reproduces **57-77%**;
   - 20-39% of template breakers are wick-only stop runs, which the engine can never see.

   Once price has left a breaker, it is reached **less** often than a random level at the same distance on 1H (BTC -7.5 pp, z -4.4; CME -4.9 to -8.3 pp). On 5m it is about 0. The first retest holds about 50%. So fix the definition (correct labels for ICT users), and give breakers a target weight below 1 plus their own ledger family.

4. **Respect, disrespect, iFVG and "first presented FVG" carry no directional information at the 1-ATR scale. [B-new]** In a race between +1 ATR and -1 ATR from the close of the touch bar:
   - first touch of an FVG: the gap direction wins 50.0% (CME 1H, n 4,283), 50.0% (5m, n 12,717), 52.0% (BTC), 52.3% (daily);
   - touch bars that close beyond the far edge (disrespect): 50.5-51.2%;
   - iFVG first retest holds 49.1% / 50.2% / 49.5% / 49.7% (n about 25,000), the same as Trader Markus's 38% vs 38% on S&P daily;
   - first FVG after 09:30 on CME 5m: no reach edge, and the gap direction wins only 41% of 244 races.

   Keep iFVGs as display and alert only. Do not feed respect or disrespect into D.

5. **ICT's selection doctrines fail B's tests. [B-corrected: A rated them weak and proposed multipliers]**
   - **IRL→ERL alternation.** After a raid that rejects, the nearest internal FVG is reached -2.0 to +3.2 pp vs baseline, against -1.1 to +0.4 at ordinary bars, with inconsistent sign. After an FVG is respected, the nearest old high/low is reached -1.4 to +1.2 pp, the same as at ordinary bars (-1.7 to +0.6).
   - **Premium/discount.** From position *p* in a dealing range, the chance of reaching the range high before the low, minus *p* (the driftless gambler's-ruin value), shows no ICT effect:
     - engine-like pivot range: ±2 pp on CME 1H, about 0 on 5m and daily;
     - IPDA 20-day range: the opposite of ICT, i.e. **momentum** (in premium the 20-day high comes first +5 to +15 pp more than geometry on CME 1H, z about 3; +4.3 pp BTC; +2.3 pp daily). This agrees with George & Hwang (2004).

   A's ICTPD-4 (phase multipliers 1.15/0.92) and ICTPD-7 (P/D side prior) are **dropped as scoring changes**. Their measurable parts move into a measurement-only module (ICTPD-8).

6. **Opening gaps (NDOG/NWOG) are a level source only when large. [B-corrected]** CME 17:00→18:00 ET gaps (ES/NQ/RTY/YM/CL, n 1,216):
   - the median NDOG is 0.12 ATR and fills 96.2% within 24 bars, vs 95.5% for the clock-matched baseline: pure distance;
   - gaps of at least 0.5 ATR fill +7.4 pp (z 2.2) above baseline and +4.3 pp above the mirror level;
   - CE shows no excess at any size;
   - gap-downs fill +2.1 pp (z 2.0).

   This agrees with the sibling study (NDX gaps ≥ 0.5 daily ATR +7.9 pp, z 4.5) and with arXiv 2511.06177 (sell-side shocks are followed by stronger rebounds). It is the opposite on BTC weekend gaps: large gaps fill 43.5% vs a 78.3% mirror (continuation).

   A's ICTPD-6 must therefore:
   - gate on size;
   - target the full fill (the pre-break close), not CE;
   - not reuse `src` 6/7, which already mean PD/PW. With src 6/7, `f_kzAff` (597-602) would apply PDH/PWH killzone boosts to gaps.

7. **Old highs/lows: A's "strong evidence" is about reaction, not reach. [B-corrected]** Osler (2000) shows published S/R levels *interrupt* intraday trends (60.8% vs 56.2%), and stop-loss orders cluster beyond them (Osler 2003, 2005). Those are the liquidity *mechanism* and the *reaction*. Neither is evidence that such levels are *reached* more often. The engine's own swing pools are reached at random-level rates (sibling `price_action.md`: -1.5 to +2.2 pp). So the "liquidity first" array prior (A: `arrPrior` 0.90 on all arrays) has no reach support. B sets FVG/OB to neutral (1.0) and only breakers below 1.

8. **A missed an engine bug. [B-new]** The origin lockout applies only to `src == 0` (line 689). HTF FVGs (src 2) are never locked out, so a just-formed 4H/D gap sitting at price can be picked as the DOL at once and "hit" on the next tick. The fix is in ICTPD-1.

**Proposals (section 4), best first:**

| ID | Prio | What |
|---|---|---|
| ICTPD-1 | P1 | Evidence-based array scoring: neutral density, lockout for every PD array, breaker weight, mild strong-displacement weight, ledger split OB/BRK with expected % |
| ICTPD-2 | P2 | Correct breaker definition, wick-raid breakers, dedupe, corrected tooltip/README |
| ICTPD-3 | P2 | Touch / CE / FULL PoT and a "then → next pool" waypoint in the target tooltip, plus ledger depth stats |
| ICTPD-6 | P2 | Large opening gaps (NDOG/NWOG, unified with the sibling settlement/ORG target) as fill targets |
| ICTPD-10 | P3 | Liquidity-void merge |
| ICTPD-8 | P3 | Measurement-only "ICT checks": iFVG hold, P/D zone, IRL/ERL phase |
| ICTPD-9 | P3 | Rejection-block near-miss statistic |
| ICTPD-5 | P3 | IPDA 20/40/60-day extremes as names/objectives (one implementation shared with TIME-8/ACAD-5) |

### 0.1 Correction log (what B changed in A's study)

| # | A's claim | B's finding | Basis |
|---|---|---|---|
| C1 | "Larger gaps and larger displacement fill LESS often in the near term", so penalise gap size > 1 ATR with ×0.85 | Raw rates are mostly distance. Against a distance-matched baseline the size effect is inconsistent (CME ≈ 0; BTC -5 pp). Large *opening* gaps fill *more* (+7.4 pp). The fixed size penalty is replaced by a mild middle-candle-displacement weight (0.95) plus ledger calibration | B E1, E3; sibling classic T3 |
| C2 | Quality is "fine as a creation gate" | The engine's quality score does not identify more reachable targets (q < 0.45 is +7.0 pp vs -1.8 pp on CME 1H). The gate is only a clutter control | B E1 |
| C3 | `arrPrior` 0.90 on all arrays ("liquidity first; S/R evidence") | No reach evidence for pools over arrays. FVG/OB stay neutral; breakers get 0.90 (measured -5 to -9 pp on 1H) | B E2; sibling price_action |
| C4 | Old high/low: evidence **strong** | Strong for reaction and stop clustering (mechanism); reach ≈ random | academic_sr verification of Osler; sibling price_action |
| C5 | ICTPD-4 IRL/ERL multipliers (P2) | No target-type effect in 4 datasets. Dropped as scoring; the waypoint UX moves to ICTPD-3 and the measurement to ICTPD-8 | B E5 |
| C6 | ICTPD-7 adaptive P/D prior (P3) | No ICT-direction effect; momentum at the 20-day scale. Dropped as scoring; measurement in ICTPD-8 | B E4 |
| C7 | ICTPD-5 IPDA extremes P2 | 20/60-day extremes are reached at baseline (sibling T2: ±0.8 pp). P3, naming and objectives only, one shared implementation | sibling classic_levels T2 |
| C8 | ICTPD-6 spec: kinds 8/9 with `src` 6 (NDOG) / 7 (NWOG); zone = far half, near edge = CE | src 6/7 collide with PD/PW semantics in `f_kzAff` (597-602), `f_tierW` and `f_levelName`. CE shows no fill excess. Small gaps are pure distance. Use new src codes 11-13, a size gate, target = pre-break close, and unify with CL-4/PA-2 | B E3; engine read |
| C9 | ICTPD-2 spec | Needs dedupe (raid path and BOS path can push the same block), the `useBRK` tooltip text fix (121-122) and the README fix. It must ship with the breaker weight, because the fixed definition gives 3-4× more breakers, which are weak targets | B E2 |
| C10 | Gap analysis: lockout "present" | Lockout is `src == 0` only (689): HTF FVGs are never locked out | engine read |
| C11 | "HTF arrays: evidence does not support extra magnetism" (from S&P daily only) | Direct test: 4H FVGs on the 1H chart +1.6 pp (CME, n.s.) and -2.8 pp (BTC, z -2.3). The +0.20 HTF density bonus is unsupported | B E6b |
| C12 | Respected/disrespected "weak, no audited statistics" | Measured: the race after a first touch is 50.0-52.3%, and after a disrespect bar 50.5-51.2%. Graded **moderate** (null) | B E1 |
| C13 | arXiv 2610.35887 numbers | Verified from the full text: N = 484; aligned 61.6/70.8%, opposed 29.6/24.8% (Table 6) | research index read |
| C14 | Vendor studies (Nordman, MarketTrace, Trader Markus, Barot, thetrading.tools, LuxAlgo, studocu) | Not re-fetchable this session. Numbers are kept as A reported them and marked "not re-fetched". B's replications agree with their direction | 2.9 |

---

## 1. Concepts: definitions, parameters, edge cases

Notation: bar `t` is the current confirmed bar, `[k]` means k bars back, H/L/O/C are high/low/open/close, ATR = ATR(14).

### 1.1 Dealing range, premium, discount, equilibrium [A; B-new evidence]
- **Dealing range** = swing low and swing high of the most recent leg that did something meaningful (swept a prior extreme or broke structure), usually on 4H/D. Nested ranges are fractal; when they conflict, defer to the higher TF. Re-anchor when a close goes beyond either extreme.
- **EQ** = (H + L) / 2. Premium is above EQ, discount below. Quadrants at 0.25 and 0.75; OTE at the 0.62-0.79 retracement; "deep" premium/discount beyond the quadrants.
- **IPDA data ranges**: the highest high and lowest low of the last 20, 40 and 60 trading days (short, intermediate and long-term dealing ranges).
- **ICT usage**: longs only in discount and shorts only in premium. From discount, target EQ first, then premium liquidity. Arrays above EQ are short entries and targets for longs.
- **Failure mode**: trends can stay on the "wrong" side of 50% for a long time.
- **Engine definition issue [B-new, cross-ref]**: `f_structure` sets `rngH/rngL` to the last pivot high/low (727-779), not ICT's [protected extreme, weak extreme] of the current leg. Sibling `ict_struct.md` ICTS-4 fixes this. Any P/D readout depends on it.
- **Evidence [B-new]**: no intraday support for the ICT direction (2.6).

### 1.2 PD array matrix ordering [A]
Canonical 2016 order, from the range extreme toward EQ, mirrored for premium and discount:

> Old High/Low → Rejection Block → Order Block → FVG (SIBI/BISI) → Liquidity Void → Breaker → Mitigation Block → (EQ)

- Later eras add volume imbalance, BPR, iFVG, NWOG/NDOG, propulsion and vacuum blocks, the Unicorn (breaker + overlapping FVG), and 2023-24 terms such as the "suspension block". B did not verify those definitions; they are entry references with no statistics.
- **The order is spatial, not a strength ranking.**
- ICT's ranking for the *draw*:
  - HTF pools above LTF;
  - engineered equal highs/lows above single swings;
  - untapped above probed;
  - liquidity is the primary draw; arrays are where price reacts on the way, or rebalances after an external raid.
- **Targets vs entries**: ahead of price, arrays are candidate targets. Behind price they are entry inventory.

### 1.3 Old high / old low [A; B-corrected grade]
- A prior swing extreme with resting stops beyond it. It is swept when price trades *through* it, the engine's rule (623-624).
- Strong evidence that such levels carry orders and interrupt trends: Osler 2000, 2003, 2005; Kavajecz & Odders-White 2004.
- No evidence that they are reached more than random levels (2.4).

### 1.4 Rejection block [A]
- ICT: "a Price High has formed with long wick(s) … Price reaches high above the body of the candle(s) to run Buy Side Liquidity out before Price Drops lower."
- Zone: bearish = max(O,C) → high of the swing candle; bullish = min(O,C) → low.
- There is no fixed wick size. The wick should be conspicuous, at a real swing, ideally a sweep.
- Used to trim take-profits to the near edge of the old extreme's wick. Fails on body acceptance beyond the wick.

### 1.5 Order block and mean threshold [A; B-verified]
- **Bullish OB**: ICT original: "the lowest candle or price bar with a down close that has the most range between open to close", near support. The common retail form is the last down-close candle before the displacement that breaks structure (bearish mirrors this).
- **Validation**: price trades above the OB high. The engine requires a *close* above it (1680).
- **Zone**: full range, body, or open-to-extreme (no official rule).
- **Mean threshold (MT)**: 50% of the block (of the range or of the body; conventions differ). A body close beyond MT is the first warning.
- **Lifecycle**: mitigated (revisited), then invalidated (body close through the far side), at which point it becomes a breaker candidate.
- **Open-source conventions [B-new]**: the `smartmoneyconcepts` Python library takes the candle with the *lowest low* between the last swing high and the BOS candle, whatever its colour. Its breaker is any OB later traded through (wick, or body with `close_mitigation`), with no sweep condition, and it is removed when price trades back beyond the other side. The engine takes the first down-close candle at or up to 5 bars before the leg low (1675-1679).

### 1.6 Fair value gap (BISI/SIBI) [A; B-verified]
- Bullish (BISI): `low[0] > high[2]`, zone `[high[2], low[0]]`. Bearish (SIBI): `high[0] < low[2]`, zone `[high[0], low[2]]`.
- Usual filters: a minimum size of 0.10-0.25 ATR, and a middle candle that displaces (the `smartmoneyconcepts` library *requires* the middle candle's colour to match; the engine halves the quality instead, 1871).
- "First presented FVG" after 09:30 NY is ranked highest by ICT (no support in B's test, 2.7).
- **Implied FVG**: UWM = (H + max(O,C))/2 and LWM = (min(O,C) + L)/2. Bullish if LWM_t > UWM_(t-2) and L_t ≤ H_(t-2); zone [UWM_(t-2), LWM_t].
- **Consecutive gaps**: the `smartmoneyconcepts` `join_consecutive` option merges them, highest top to lowest bottom. **[B-new]** 15-34% of FVGs are followed by a same-direction FVG on the next bar (BTC 15%, CME 1H 21%, CME 5m 23%, daily 30%).

### 1.7 Consequent encroachment, filled / respected / disrespected [A; B-new statistics]
- **CE** = the 50% line of an FVG (also used for wicks, opening gaps and voids).
- **Filled** = traded to the far edge. **Respected** = traded into (often only to CE), then continued in the gap direction. **Disrespected** = a body close beyond the far edge, which makes it an iFVG. Breakaway gaps are not expected to fill.
- **Ladder [B-verified]**: within H = 30 bars of becoming a target, P(CE | touch) is 88-92% and P(full | touch) 79-85%:

  | Data | P(CE \| touch) | P(full \| touch) |
  |---|---|---|
  | CME 1H | 91.2% | 83.1% |
  | CME 5m | 92.1% | 85.3% |
  | BTC 1H | 88.4% | 78.7% |
  | daily | 92.2% | 81.6% |

  A's MarketTrace numbers (0.87-0.95 / 0.75-0.89) agree. CE and full-fill reach are both at the distance baseline (E1: CE -0.2 to -2.1 pp, full -0.4 to -2.5 pp).

### 1.8 Inversion FVG [A; B-new statistics]
- Formation: a body close beyond the far edge (some tools use beyond CE). After that the span has opposite polarity until it is reclaimed.
- It is a retest/entry concept, not a target.
- The retest holds about 50% (2.7).

### 1.9 Liquidity void, vacuum block, volume imbalance, opening gaps, BPR [A; B-corrected for gaps]
- **Liquidity void**: a sudden one-directional run that leaves porous price action, in practice a run of consecutive same-direction FVGs.
- **Vacuum block**: a true price gap from a volatility event or a session break.
- **Volume imbalance**: consecutive bodies do not overlap while the wicks do. If the wicks do not overlap either, it is an opening gap.
- **NWOG**: Friday 17:00 ET close → Sunday 18:00 ET open; mark high, low and CE; ICT keeps the last five.
- **NDOG**: 17:00 close → 18:00 reopen.
- **RTH opening range gap (ORG) [B-new, cross-ref]**: 16:00 (or 16:15) close → 09:30 open on index futures. On TradingView's default 23-hour ETH futures chart this is *not* a time break (sibling `price_action.md`, quoting the docs: "For futures, the 'Electronic trading hours' session *is* the regular session"). A time-break detector only sees the 17:00-18:00 halt.
- **BPR**: the overlap of a bullish FVG and a later bearish FVG (or the reverse); an entry zone only.

### 1.10 Breaker, mitigation, propulsion block [A; B-verified, B-new data]
- **Bearish breaker** (ICT, verbatim as A gives it): "a bearish range or Down Close Candle in the most recent Swing Low prior to an Old High being violated." Sequence:
  1. old high H1;
  2. swing low L1, whose down-close candle is the block;
  3. a rally that violates H1 (by wick or by close);
  4. a close below the block.
- **Bullish breaker**: the mirror. The up-close candle in the most recent swing high before an old low is violated, then a close above it.
- **The qualifying sweep is made by the leg leaving the block.** For every OB the engine creates at a BOS, the BOS leg already violated the old extreme by close, so every BOS-OB that later fails is a canonical breaker. The engine's extra condition (the block's own leg low took a 20-bar low) is not ICT.
- **Open-source template [B-verified via sibling smc_impl]** (LuxAlgo "Breaker Blocks with Signals", PyInd port):
  - zigzag of pivots (length 5);
  - bullish: low C, high D, newer low E < C, then a close above D;
  - the breaker candle is the first up-close candle scanning from D back to C;
  - mitigated by a close below its bottom.
- **Mitigation block**: the same role flip with no sweep (a failure swing: a lower high, then the break). Conventions differ.
- **Propulsion block**: a candle that trades into a prior OB (usually to MT) without closing through it, then launches away. Entry only.

### 1.11 HTF arrays as magnets; IPDA ranges [A; B-new data]
- ICT says HTF gaps and blocks are the draw and LTF arrays refine the entry.
- Data: HTF FVGs are reached at the baseline rate (2.2), and 20/60-day extremes are at baseline (2.6).

### 1.12 IRL / ERL alternation and low/high-resistance runs [A; B-new data]
- ICT: after external liquidity is taken (with rejection), the next draw is internal; after internal liquidity is rebalanced, the draw rotates to the opposite external extreme. A genuine breakout breaks the rule.
- Low-resistance path: through swept swings and same-direction FVGs. High-resistance path: through fresh swings and opposing imbalances.
- B's tests:
  - no alternation effect (2.5);
  - arrays in the path produce no measurable reaction at the 1-ATR scale (first touch ≈ 50%). An "opposing arrays in the path" penalty is not supported.
  - Pools *are* small barriers (sibling `academic_sr.md`: Osler bounce +4.6 pp).

---

## 2. Evidence

Grades: **strong** = peer-reviewed or large replicated quantitative study; **moderate** = published or reproducible statistics with numbers; **weak** = practitioner consensus; **none** = folklore.

### 2.1 External controlled studies [A; not re-fetched by B; direction corroborated by 2.2]

| Study | Data | Result vs a distance-matched random level |
|---|---|---|
| Nordman, "Do Fair Value Gaps Work?" (2026) | ES/NQ/6E/6A 5m, Oct 2023-Sep 2026; 38,114 returns vs 380,599 fakes | Returned to 73.0% vs 72.9%. Reaction edge ratio +3.7% at 5 min, +2.5% at 15 min, -0.2% at 1 h. Size "barely matters". Negative after costs |
| Nordman, "Do Order Blocks Work?" | Same markets; 10,986 touches | 73.7% vs 73.7%. Next-bar entry +4.8% at 1 min, +3.3% at 5 min. Fresh OBs react more |
| Barot, SSRN 7148099 | 4 futures, 3 TFs, about 40,000 FVGs | Reaction about 5 pp above random, "no tradeable edge". The PF 2.4 version was look-ahead (PF about 1.0 on 1-minute data) |
| Trader Markus | S&P 500 daily 2000-2026 | Bullish 69% vs 69% within 20 days; bearish 81% vs 72%. iFVG retest held 38% vs 38% and 47% vs 47% |
| MarketTrace | BTC 2024-2026, 4,827 FVGs | 1H 75.6% vs 72.4% (24 h). Ladder (touch/CE/full): 1H 85.3/80.6/75.6; 4H 71.8/62.3/54.2. Size terciles 1D full fill 78.7/61.7/46.0% (**raw, no distance control**, C1) |

### 2.2 B's replication with the engine's method [B-new]

**Method** (`e1_fvg.py`, `e2_blocks.py`, `e6_ifvg_htf.py`):
- Every FVG of at least 0.15 ATR(14) (the engine's `fvgMin`).
- Engine quality `q` recomputed exactly (lines 910-912 and 1868-1871, BOS from `pivLen` 5 swings).
- The target is eligible at the first bar u with u − t ≥ 3 and price ≥ 1 ATR away, while still untouched (the engine's lockout, 689). Distance cap 10 ATR.
- **hit** = near edge touched within H bars (H = 30; daily H = 20).
- **base** = the instrument's unconditional probability of an H-bar excursion of at least d ATR in that direction. This is `f_potBase` without the regime split.
- Clustered SE over 2H-bar blocks.
- **GC excluded** from CME pools: 329 FVGs per 1,000 bars, twice the other symbols, and +12.9 pp, which suggests feed artefacts in illiquid hours.
- Data: CME 1H Mar 2025-Apr 2026 (13 months, a bull market); CME 5m Jan-Apr 2026 (3 months); BTC 1H 2016-2025; SPX/NDX daily 1999-2018.

**FVG as a target (near-edge reach − baseline, pp; z in brackets)**

| Split | CME 1H (n 1,756) | CME 5m (n 4,950) | BTC 1H (n 3,337) | Daily (n 935) |
|---|---|---|---|---|
| ALL | +0.4 (0.3) | -0.6 (-0.7) | -1.6 (-1.8) | -2.9 (-1.5) |
| Engine gate passed, q ≥ 0.45 | -1.8 (-1.3) | -0.7 | -1.5 | -2.8 |
| Engine gate failed, q < 0.45 | **+7.0 (3.3)** | -0.3 | -2.1 | -3.3 |
| q tercile low / high | +5.7 (3.0) / -2.1 | -1.3 / 0.0 | -0.4 / **-4.7 (-3.2)** | -3.9 / -3.4 |
| Middle body/ATR tercile low / high | +5.4 (2.8) / -3.1 | -1.1 / -0.5 | +0.7 / **-5.5 (-3.8)** | -3.0 / -2.9 |
| Gap size tercile low / high (near) | +0.6 / -1.7 | -2.3 / -0.4 | +0.9 / **-4.9 (-3.4)** | -1.6 / -2.8 |
| Gap size high: full fill | -3.4 | +0.2 | **-5.6 (-3.8)** | -1.0 |
| BOS within 3 bars yes / no | -2.8 / +2.1 | -1.0 / -0.4 | -2.0 / -1.2 | -1.2 / -3.7 |
| Consecutive (void leg) yes / no | -0.1 / +0.5 | +0.6 / -0.9 | -3.6 / -1.2 | -3.7 / -2.6 |
| CE (50%) | -0.2 | -0.6 | -2.1 | -1.6 |
| Full fill (far edge) | -0.7 | -0.4 | -2.5 | -2.5 |
| Mirror level, same distance, other side | -2.1 | +0.7 | +1.3 | +3.7 |

Raw full-fill rate by size tercile (CME 1H) is 67.1 / 63.2 / 45.8%. The baseline is 67.4 / 61.6 / 49.2%. **The raw size effect is distance** (C1).

**Other arrays (same method; GC excluded)**

| Family | Count per 1,000 bars | Reach − base, pp (z): BTC 1H / CME 1H / CME 5m / daily | First-retest hold (±1 ATR race) |
|---|---|---|---|
| Engine OB (q ≥ 0.40, not mitigated) | 14.9-28.2 | -1.4 / -1.8 / +1.2 / +2.4 | 43.7-51.7% |
| Engine breaker (`tookL` gate) | 7.8-12.3 | **-8.6 (-2.8)** / -5.3 / +1.1 / -8.9 | 50.0-53.3% |
| All BOS-OB breakers (gate removed) | 35.6-39.9 | **-7.5 (-4.4)** / -4.9 (-1.8) / +0.5 / -8.1 | 49.0-55.9% |
| Zigzag template breakers | 10.0-14.2 | **-6.3 (-2.8)** / **-8.3 (-2.5)** / -0.8 / -4.5 | 46.1-51.9% |
| 4H FVG used on the 1H chart | n/a | -2.8 (-2.3) / +1.6 (1.0) / n/a / n/a | n/a |

- **OB with own-origin sweep** (`tookL`): BTC -4.9 pp (z -2.0), CME 1H -3.8, CME 5m +4.8 (z 2.5), daily +4.1. Inconsistent, so it is not a quality signal.
- **Template breakers also produced by the engine's definition**: 11% (BTC), 24% (CME 1H), 19% (5m), 21% (daily). With the gate removed: 57%, 64%, 65%, 77%. Wick-only stop-run breakers make up 39 / 29 / 29 / 20% of template breakers.

**Reaction after the first touch** (race +1 ATR vs −1 ATR from the touch-bar close; "gap direction first")

| | CME 1H | CME 5m | BTC 1H | Daily |
|---|---|---|---|---|
| All first touches | 50.0% (n 4,283) | 50.0% (12,717) | 52.0% (8,300) | 52.3% (2,470) |
| Touch bar closed beyond the far edge | 51.2% | 50.5% | 50.7% | n/a |
| iFVG first retest holds | 49.1% (3,857) | 49.5% (11,768) | 50.2% (7,399) | 49.7% (2,220) |

The unconditional race is 49.5-52.5%.

**Grade: moderate.** These are local, reproducible tests of 3 asset classes and 4 TFs; CME history is short.

### 2.3 Opening gaps [A base rates; B and sibling distance-controlled tests]

- **Base rates [A, not re-fetched]**:
  - SPY same-day fill by size: up-gaps 78/60/46/26/27%, down-gaps 80/66/43/33/29% (0.1-0.25, 0.25-0.5, 0.5-1, 1-2, 2%+).
  - 1%+ up-gaps close up 60% of days.
  - QuantifiedStrategies: 50.5% of up-gaps and 54.9% of down-gaps fill same day.
  - Finabase: small gaps fill "close to what random intraday movement would produce".
- **B E3** (CME 17:00→18:00 ET, ES/NQ/RTY/YM/CL, H = 24 1H bars; baseline = excursions from every 18:00 open):

  | Subset | n | Full fill | Clock baseline | Edge (z) | Mirror |
  |---|---|---|---|---|---|
  | NDOG | 959 | 96.2% | 95.5% | +0.7 (1.2) | 95.9% |
  | NWOG | 257 | 77.0% | 74.2% | +2.9 (1.1) | 75.5% |
  | < 0.25 ATR | 885 | 97.6% | 97.1% | +0.5 | n/a |
  | ≥ 0.5 ATR | 188 | 69.7% | 62.3% | **+7.4 (2.2)** | 65.4% |
  | gap-downs | 605 | n/a | n/a | +2.1 (2.0) | n/a |

  CE edge is about 0 for every subset. The median gap is 0.12 ATR.
- **Sibling classic_levels T3**: NDX cash gaps ≥ 0.5 daily ATR +7.9 pp (z 4.5, n 700), mostly gap-downs (+12.0 pp, z 4.9). Small gaps are not filled beyond distance (within 5 days they are under-filled by 2-5 pp).
- **Sibling session_stats**: BTC "CME gap" weekends fill 86.7% vs a mirror 89.4%; gaps > 1 ADR fill 43.5% vs 78.3% (continuation). EURUSD weekend gaps fill at the mirror rate.
- **Academic context [B-new]**:
  - Vlasiuk & Smirnov (arXiv 2511.06177, SPY NBBO): "large negative pushes are followed by stronger positive responses than equally large positive pushes."
  - Zawadowski et al. (cond-mat/0406696): significant short-term reversal after extreme intraday moves.
  - Plastun et al. (2020, via sibling) reject the "gaps must fill" myth.
- **Grade: moderate.** Only large gaps on equity-index (and CL) futures show a small fill excess. It is asset-dependent (crypto weekends continue). NWOG/NDOG as named ICT levels have no audited statistics.

### 2.4 Old highs/lows and S/R [A; B-corrected interpretation]
- **Osler (2000)**: published S/R levels stopped intraday FX trends 60.8% of the time vs 56.2% for 10,000 arbitrary sets (about 62,000 hits). Per currency, arbitrary vs firms: DEM 54.9 vs 56.6-62.0; JPY 57.3 vs 60.7-66.5; GBP 56.3 vs 58.8-63.0. The effect lasts at least 5 days. Firms' "strength" ratings had **no** predictive value. Verified by sibling `academic_sr.md`.
- **Osler (2003, 2005)**: take-profits cluster at round numbers; stop-losses cluster just beyond them; crossing a cluster gives an extra move of +0.27 to +2.35 hundredths of a percent over 15 min to 2 h.
- **Kavajecz & Odders-White (2004)**: S/R levels coincide with limit-order-book depth.
- **Reach**: the engine's swing pools are reached at -1.5 to +2.2 pp vs random (sibling `price_action.md`).
- **Grade**: strong for the liquidity mechanism and reaction; for "more likely to be reached" the evidence is moderate and null.

### 2.5 IRL ↔ ERL alternation [B-new; replaces A's "weak, untested"]
`e5_irl_erl.py`. Edge vs baseline in pp; the control is the same measurement at every third bar.

| Data | (A) nearest FVG after raid-reject | (A) after raid-hold | (A0) control | (B) nearest old H/L after FVG respected | (B0) control |
|---|---|---|---|---|---|
| CME 1H | +3.2 (z 2.1, n 1,190) | +2.3 | +0.4 | -0.3 (n 1,803) | -0.5 |
| BTC 1H | -2.0 (z -2.2, n 3,430) | +1.6 | -0.5 | -1.4 (n 4,174) | -1.7 |
| CME 5m | +1.2 (n 3,587) | +1.3 | -0.2 | +1.2 (n 6,108) | -0.3 |
| Daily | -3.0 (n 409) | -1.8 | -1.1 | +0.7 (n 1,034) | +0.6 |

- The phase effect (A − A0) is -1.9 to +2.8 pp with inconsistent sign.
- (B − B0) is +0.1 to +1.5 pp.
- Raw hit rates *look* phase-dependent (B 54.7% vs B0 46.1% on CME 1H) only because the distances differ (2.70 vs 3.37 ATR).
- **Grade: moderate (null).**

### 2.6 Premium/discount and IPDA ranges [A literature; B-new test]
- **George & Hwang (2004)**: nearness to the 52-week high predicts continuation (WML 0.45%/month, t 2.00, to 1.23%/month, t 7.06). Verified by sibling `academic_sr.md`.
- **B E4**: P(range high before range low) minus *p*, by zone (pp, z). The table lists the clearest cells:

  | Range | Deep discount | Discount | Premium | Deep premium |
  |---|---|---|---|---|
  | Engine-like pivot range, CME 1H | +2.1 (1.9) | +2.4 | -2.9 (-1.6) | -0.8 |
  | Pivot range, CME 5m / daily | ≈ 0 | ≈ 0 | ≈ 0 | ≈ 0 |
  | Pivot range, BTC | -0.5 | +2.2 (2.1) | +0.8 | +1.3 (2.3) |
  | IPDA20, CME 1H | -1.0 | -1.6 | **+15.2 (3.3)** | **+5.3 (2.9)** |
  | IPDA20, BTC | +1.7 | +5.6 | +4.1 | **+4.3 (3.0)** |
  | IPDA20, daily | +2.1 | +0.9 | -1.0 | +2.3 (2.0) |

  BTC's positive values in every zone reflect drift. CME 1H IPDA20 premium is momentum in a 2025-26 bull market.
- **Sibling classic_levels T2**: 20-day and 60-day highs/lows are reached at baseline: +0.21 / +0.72 and +0.43 / +0.30 pp at 5 days.
- **Grade: moderate, against the ICT directional rule** (a small reversion at most at the pivot-range scale; momentum at the 20-day scale).

### 2.7 First presented FVG [B-new]
- CME 5m, FVGs completed 09:30-12:00 NY.
- First FVG of the day: reach -2.9 pp (n 139, n.s.). At its first touch the gap direction wins only 41.2% of 244 races. Later FVGs: 51.2%.
- Later morning FVGs show -12.0 pp reach, but that is confounded by the intraday volatility clock (ATR is inflated just after the open).
- **Grade: weak, and it contradicts the claim.**

### 2.8 Structure and displacement [A; B-verified]
- **Nordman MSS** (15,817 signals): edge ratios of about 1.0 at 1 h with or without displacement [A, not re-fetched].
- **Taylor (2026), arXiv 2610.35887** [B-verified, full text]:
  - N = 484 manipulation-signal days on NQ 15m, 2022-2026.
  - Bullish/uptrend 61.6% (n 112); bearish/downtrend 70.8% (n 72); bullish/downtrend 29.6%; bearish/uptrend 24.8% (n 153).
  - "No directional information beyond the daily trend regime was observed."
  - 57% of signals see the target delivered before the 09:40 entry window.

### 2.9 Concepts with no statistics, and source status
- **No audited statistics**: MT, rejection block, mitigation block, propulsion block, vacuum block (as distinct from gaps), BPR, volume imbalance, implied FVG, PD-matrix order, the Unicorn, the suspension block. Grade: none or weak.
- **Not re-fetchable this session**: the web search budget was used up, the Firecrawl scraper was out of credits, and WebFetch could not resolve nordman-algorithms.com, luxalgo.com, arxiv.org or ssrn.com. These pages need to be allowed in the session's network settings to re-verify. Numbers from Nordman, MarketTrace, Trader Markus, Barot, thetrading.tools, QuantifiedStrategies, Finabase, Edgeful, FXNX, LuxAlgo and studocu are A's as reported.
- **Read directly by B**: arXiv 2610.35887 (research full-text index); the `smartmoneyconcepts` source code (public git clone); arXiv 2511.06177 and cond-mat/0406696 (abstracts).

---

## 3. Engine gap analysis (`baseline_v2.pine`) [A's table re-checked; B changes marked]

| # | Concept | Status | Lines | What the engine does / what differs |
|---|---|---|---|---|
| 1 | FVG detection | present | 907-912, 1867-1889 | Wick-to-wick, size ≥ `fvgMin`·ATR (0.15). Quality = 0.40·body/(1.2·ATR) + 0.20·body ratio + 0.20·size + 0.20·BOS-within-3, halved if the middle candle has the wrong colour (1871). Gate `fvgQMin` 0.45 (1872). Every FVG also goes to `fvgTrk`. **[B]** The gate removes about 29% of FVGs, and those are as reachable or more (2.2). |
| 2 | Array density from quality / HTF | **wrong** | 687 | `dens = min(1, 0.5·qual + 0.3·coil + 0.2·induce + 0.20·[src==2])`. **[B]** Quality and HTF origin never improve reach and lower it in 2 of 4 datasets (2.2). With `wDens` 20 of 100, `qual` alone moves the score by up to about 10 points. |
| 3 | Origin lockout (arrays behind price are entries) | **partial [B-corrected]** | 689-690 | ×0.25 until `originBars` have passed and price has moved `awayATR` away, **but only for `src == 0`**. HTF FVGs (src 2, created at 1855-1865, possibly right at price, `hGap ≥ 0`) are never locked out. |
| 4 | CE / delivery | present | 123-124, 306, 1565-1577 | Non-active arrays are delivered at CE by default (`delivIn`), with cropping. The active DOL counts a touch. The glow line sits at `price` = the original mid. |
| 5 | Fill-ladder readout | missing | none | PoT goes to the near edge only. **[B]** Arrays ≈ random levels, so `f_potModel` at the CE and far-edge distances is already calibrated (ICTPD-3). |
| 6 | Respected / disrespected | partial | 1598-1627 | Disrespect → iFVG. **[B]** Neither event carries directional information (≈ 50%), so *not* feeding them into D is correct. |
| 7 | iFVG | present | 1598-1644, 195-200 | Display and alert only. Correct given about 50% retest holds (2.2). |
| 8 | Order block | present | 1663-1748 | Body-close BOS through the last chart swing. The block is the first down-close candle from the leg low back 5 bars; close > OB high; quality = 0.4·FVG in leg + 0.3·`tookL` + 0.3·leg size; mitigated blocks are skipped. **[B]** Reach ≈ random; `tookL` is not a consistent quality signal. |
| 9 | Mean threshold | partial | 1684, 1696-1700, 1727, 1737-1741 | Used only to skip mitigated OBs. |
| 10 | Breaker | **wrong** | 121-122 (tooltip), 1646-1661, 1691, 1706-1707, 1734, 1747-1748, README "Blocks" row | `obTrk` only takes OBs with `tookL`/`tookH` (own-origin sweep). ICT requires the sweep by the leg leaving the block, which every BOS-OB already satisfies. Wick-raid breakers are never created (no body-close BOS). **[B]** Reproduces 11-24% of template breakers (2.2). The tooltip text "Only order blocks whose leg swept prior liquidity can become breakers" is also wrong. |
| 11 | Breaker as a target | **[B-new] unweighted** | 1652-1659, 635 | Breakers are scored like any array and share ledger family 3 with OBs. **[B]** They are reached -5 to -9 pp below random on 1H, while OBs are about 0, so the family calibration (`f_calMult(3)`) blends two different behaviours. |
| 12 | Mitigation block | missing | none | No statistics; label only. |
| 13 | Rejection block | missing | 1752-1776 | The pool zone extends *beyond* the swing by `zoneATR`. The body-to-wick span is not stored. |
| 14 | Propulsion block, VI, BPR, implied FVG | missing | none | Entry-only concepts; low DOL value. Not proposed. |
| 15 | Liquidity void | partial | 1945-1947, 1867-1889 | VP path cost and LVNs exist. Consecutive FVGs stay separate levels (15-34% of all FVGs). |
| 16 | Opening gaps (NDOG/NWOG/ORG) | missing | none | No session-break gap targets. Session opens are confluence anchors only (964-966). **[B]** Only gaps ≥ 0.5 ATR earn a target (2.3). `src` 6/7 are taken by PD/PW (`f_kzAff` 597-602, `f_tierW` 505-516, `f_levelName` 518-529). |
| 17 | Dealing range / premium-discount | partial | 727-779, 967-968, 2323-2333 | Panel display plus `dayEQ`/`htfEQ` anchors. The range is the last pivots, not the leg (ICTS-4). **[B]** Not using P/D in D or selection is supported by the data (2.6). |
| 18 | IPDA 20/40/60-day extremes | missing | none | **[B]** Reached at baseline (2.6); naming value only. |
| 19 | HTF arrays | partial / **wrong bonus** | 785-796, 939-942, 1854-1865, 687 | HTF FVGs only, with +0.20 density and a slower decay (`hlMult` = sqrt of the TF ratio). **[B]** No magnet (-2.8 / +1.6 pp); not locked out (row 3). |
| 20 | PD-matrix ordering / type prior | partial | 505-516, 661-696 | Liquidity has source tiers. Arrays have no type prior. **[B]** A type prior is supported only for breakers. |
| 21 | IRL ↔ ERL | partial | 1580-1582, 1891-1894 | Raids feed D; there is no target-type sequencing. **[B]** Sequencing is not supported (2.5); leave the scoring as it is. |
| 22 | Arrays in the path (high-resistance runs) | partial | 684-685, 1945-1947 | Inner stacked pools ×0.70; VP path cost. **[B]** Arrays show no reaction (≈ 50%); do not add an opposing-array penalty. |
| 23 | Distance-matched baseline (the right control) | present | 1313-1322, 1376-1382, 1426-1431, 1461-1499 | `f_potBase` plus `f_calMult` (bounds 0.8-1.2, n ≥ 10). The Full view (2410-2418) shows hit % without expected %, and with only 4 families OB and BRK are pooled. |

---

## 4. Proposals (best first)

Shared rules:
- Everything runs in the `barstate.isconfirmed` engine block, except the ICTPD-3 tooltip text, which is live like PoT.
- No proposal adds a `request.*` call.
- New `Level` fields go in TYPES (317-347) with defaults; new inputs go in the INPUTS groups shown.
- Kind and src codes after all proposals:
  - kinds: 0-7 as now; **8 = gap-fill target above price, 9 = below**;
  - sources: 0-7 as now; **8/9/10 = 20/40/60-day extremes (ICTPD-5); 11 = NDOG, 12 = NWOG, 13 = RTH/ORG/settlement (ICTPD-6 + CL-4 + PA-2)**;
  - sibling PA-1 projections must use kinds 10/11.

### ICTPD-1 (P1 · scoring · S) Evidence-based array scoring

**Why.** All arrays are reached at about the random-level rate (2.1, 2.2). The engine's quality and HTF bonuses (687) favour exactly the arrays that are never better and sometimes worse. Breakers are measurably worse than random after they form (-5 to -9 pp on 1H). HTF FVGs escape the lockout (689). And OB and breaker are pooled in one calibration family, so the ledger cannot learn the breaker deficit.

**Spec.**
1. **Neutral array density; weights only where measured.** In `evaluate()`, replace lines 687-690:
   ```pine
   else
       this.dens := 0.40 + 0.30 * this.coil + 0.30 * this.induce          // no qual, no HTF bonus
       this.mult *= 1.0 - 0.5 * this.fill
       if this.kind == 6 or this.kind == 7
           this.mult *= brkPrior                                           // breakers: retest zones, weak targets
       if this.disp >= dispHi
           this.mult *= dispPri                                            // FVG left by a very large middle candle
       // origin lockout for every PD array (HTF FVGs included); gap-fill targets (kinds 8/9) are exempt
       if this.kind <= 7 and (bar_index - this.createdBar < originBars or this.maxAway < awayATR)
           this.mult *= 0.25
   ```
2. **Inputs** (`G_ARR`, after line 124):
   ```pine
   float brkPrior = input.float(0.90, "Breaker Target Weight", minval = 0.5, maxval = 1.2, step = 0.05, group = G_ARR,
     tooltip = "Once price has left a breaker it is revisited less often than a random level at the same distance (1H tests: -5 to -9 pp). The accuracy ledger refines this per chart.")
   float dispPri  = input.float(0.95, "Strong-Displacement FVG Weight", minval = 0.5, maxval = 1.0, step = 0.05, group = G_ARR,
     tooltip = "FVGs left by a very large middle candle are revisited slightly less often than their distance predicts.")
   float dispHi   = input.float(1.3, "Strong Displacement (body x ATR)", minval = 0.3, step = 0.1, group = G_ARR)
   ```
3. **New field** `float disp = 0.0` on `Level`. Set it at creation:
   - `nfu.disp := fvB1 / fvA2` (after 1875);
   - `nfd.disp := fvB1 / fvA2` (after 1885).

   `fvB1` and `fvA2` are global series (910-911). OB, breaker and HTF FVG levels keep 0, because they were not tested by tercile.
4. **Quality** stays as a creation gate (`fvgQMin`, `obQMin`), which is now explicitly a clutter control. Update the `fvgQMin` tooltip: "Clutter filter. Displacement quality does not make a gap more likely to be revisited." Optionally lower the default to 0.30 once the ledger confirms it on real charts.
5. **Split the ledger family OB vs BRK** (5 families plus ALL):
   - `method grp` (635): `this.kind <= 1 ? (this.src == 0 ? 0 : 1) : this.kind <= 3 or this.kind >= 8 ? 2 : this.kind <= 5 ? 3 : 4`.
   - `f_grpName` (543): `3 => "OB"`, `4 => "BRK"`, `=> "ALL"`.
   - Stats arrays (1066-1071): size 5 → 6.
   - ALL index 4 → 5 at 1380-1381, 1470 (`array.from(t.grp, 5)`), 2375-2376, 2384, 2388-2389, 2403 and 2443. **Do not touch `raceSt` (1494, 2420), which is a different array.**
   - Step 17 (1935-1944): add `float cm4 = f_calMult(4)` and use `g == 3 ? cm3 : cm4`.
6. **Full view** (2411): loop `for g = 0 to 4`, and show expected next to hit, the external studies' test on the user's own chart:
   `str.tostring(100.0 * kg / ng, "0") + "% vs " + str.tostring(100.0 * stPE.get(g) / ng, "0")`.
7. *(Optional, later)* A displacement-tercile context multiplier learned by the ledger, using A's `f_ctxMult` (shrinkage n/(n+30), bounds 0.85-1.15), with `Trial.dBin` stored at `f_openTrial` (1426).

**Evidence.** Moderate: 2.1 (five external studies) and 2.2 (B, four datasets).

**Value.** Fewer chased "displacement" FVGs and fewer breaker picks that never get retested. HTF FVGs are no longer selected while price sits on them. Per-family honesty (hit % vs expected %) is visible.

**Risk.** Low. Arrays are still chosen when they are the best candidate (the Clean look "Target: BEFVG" is unchanged). Breaker weight 0.90 and FVG weight 0.95 are mild, and `f_calMult` corrects them per chart within about 10-30 outcomes.

**Effort.** S.

### ICTPD-2 (P2 · level-source · S) Correct breaker definition, wick-raid breakers, dedupe

**Why.** The ICT definition (1.10) is not what the engine implements (only 11-24% overlap with the template, 2.2). The `useBRK` tooltip and the README state the wrong rule, which ICT users will notice. **It must ship with ICTPD-1's `brkPrior` and family split**, because the corrected definition yields 3-4 times more breakers (35-40 per 1,000 bars) and breakers are weak targets.

**Spec.**
1. **BOS path.** Every BOS-created OB is a breaker candidate:
   - 1706: `if useBRK and not f_hasZone(obTrk, bar_index - obI, 1)` → push with `tookLiq = tookL`;
   - 1747: the mirror with `-1`;
   - 1654: `if useBRK and edgeD / atrE <= ejectD` (drop `z.tookLiq`).
2. **Stop-run path** (new step 8b, after line 1749). The leg away from the last swing low raids the old high by wick only:
   ```pine
   if useBRK and not na(obSwingH) and not raidedH and high > obSwingH      // bosUp already reset obSwingH to na
       raidedH := true
       int   spanR = math.max(1, math.min(obLook, bar_index - nz(obSwingHBar, bar_index - obLook)))
       int   rI    = 0
       float rV    = low
       for k = 1 to spanR
           if low[k] < rV
               rV := low[k]
               rI := k
       for k = rI to rI + 5
           if close[k] < open[k]
               if not f_hasZone(obTrk, bar_index - k, 1)
                   obTrk.push(Zone.new(top = high[k], bottom = low[k], dir = 1, bornBar = bar_index - k, createdBar = bar_index, qual = 0.5, tookLiq = true))
               break
   // mirror: raidedL / obSwingL / highest high / first up-close candle / dir = -1
   ```
   - In step 9 set `raidedH := false` where `obSwingH := ph` (1754) and `raidedL := false` at 1766.
   - Step 7 (1651) then flips the block on `close < z.bottom`.
   - History references inside an `if` already appear in step 8 (1672-1680), and the loop bound is ≤ `obLook` + 5 (max 65).
3. **Helper** (STATE HELPERS) and state (after 1050, `var bool raidedH = false`, `var bool raidedL = false`):
   ```pine
   f_hasZone(array<Zone> zs, int born, int dir) =>
       bool f = false
       for z in zs
           if z.bornBar == born and z.dir == dir
               f := true
               break
       f
   ```
4. **Text.**
   - `useBRK` tooltip (121-122): "An order block becomes a breaker when price closes through it after the leg away from it ran an old high / low (ICT)."
   - README "Blocks" row: "Breakers: order blocks that fail after the move away from them took an old high or low (stop run or break of structure)."
5. *(Optional, default off, label only)* Mitigation blocks: a failure swing (the next confirmed pivot high is lower than the prior one), then a close below the candidate. Same zone logic, `Level.variant = 1`, labels "BEMB"/"BUMB". No statistics exist.

**Evidence.** Moderate for the definition (ICT text plus the open-source template; overlap measured). Breakers' target value is weak to negative (2.2), handled by ICTPD-1.

**Risk.** More candidates, contained by `brkPrior`, the lockout, `poolMax` (1951) and the `obTrk` cap of 30 (1749).

**Effort.** S.

### ICTPD-3 (P2 · probability · S) Touch / CE / FULL PoT and "next pool" waypoint, plus ledger depth stats

**Why.** Traders plan partials at the near edge, CE and the far edge. Arrays behave like random levels (2.2), so the engine's distance model is already calibrated for those depths. The ladder is large on HTFs (BTC 4H 24 h: 71.8 → 62.3 → 54.2%). ICT's "arrays are waypoints to liquidity" is best served as information, not as a multiplier: the multiplier version failed B's test (2.5).

**Spec.**
- In the rendering block, after `string tip = …` (2206), for an array target:
  ```pine
  if activeLv.isArray()
      float mid  = (activeLv.oTop + activeLv.oBot) / 2.0
      float far  = activeLv.side == 1 ? activeLv.oTop : activeLv.oBot
      float pCE  = f_potModel(math.max(0.0, activeLv.side == 1 ? mid - close : close - mid), activeLv.side, potMu * activeLv.side)
      float pFar = f_potModel(math.max(0.0, activeLv.side == 1 ? far - close : close - far), activeLv.side, potMu * activeLv.side)
      tip += "\nTouch " + str.tostring(activePoT * 100.0, "0") + "% · CE " + str.tostring(pCE * 100.0, "0") + "% · Full " + str.tostring(pFar * 100.0, "0") + "%"
      Level nx = na
      float nd = 1e100
      for lv in pool
          if lv.isLiquidity() and lv.side == activeLv.side
              float dd = activeLv.side == 1 ? lv.price - far : far - lv.price
              if dd > 0 and dd < nd
                  nd := dd
                  nx := lv
      if not na(nx)
          tip += "\nthen → " + f_shortName(nx.kind, nx.src) + " @ " + str.tostring(nx.price, format.mintick) +
            " (PoT " + str.tostring(f_potModel(math.max(0.0, nx.distance(close)), nx.side, potMu * nx.side) * 100.0, "0") + "%)"
  ```
  This is O(pool ≤ 40) on the last bar only. Add the same line to the Terminal HUD.
- **Ledger depth (Full view).** When an array `Trial` books a hit (`f_book`, 1461), push `[ce, far, side, bar0 + H]` into a small `var` array. Update it in step 2 until `bar0 + H`; count `ladN`, `ladCE`, `ladFull`; show "TAP→CE x% → FULL y%". Expected from B's data: about 90% / about 82%.

**Evidence.** Moderate (2.1, 2.2).

**Risk.** None to selection; tooltip and HUD text only. Clean look unchanged.

**Effort.** S.

### ICTPD-6 (P2 · level-source · M) Large opening gaps as fill targets, one object with CL-4 / PA-2

**Why.**
- Small session-break gaps are pure distance.
- Gaps ≥ 0.5 ATR on index and CL futures fill +7.4 pp above a clock-matched baseline (z 2.2). The NDX cash equivalent is +7.9 pp (z 4.5).
- The fill excess is at the **pre-break close** (full fill), not at CE.
- NWOG/NDOG are names ICT traders watch.
- Sibling `classic_levels.md` CL-4 (prior settlement) and `price_action.md` PA-2 (RTH opening range gap) propose the same object. Implement it once.

**Spec.**
- **Inputs** (`G_KEY`):
  - `useGap = input.bool(true, "Opening Gap Fill (NDOG / NWOG)")`;
  - `gapMinD = input.float(0.10, "  Min Gap (x prior-day range)", minval = 0.0, step = 0.01)`. 0.10 × the prior-day range ≈ 0.5 × 1H ATR on index futures, which makes the threshold TF-independent.
- **Global scope** (after 961):
  - `bool sesBrk = timeframe.isintraday and not na(time[1]) and time - time[1] > 1500 * timeframe.in_seconds()`. This catches the CME 17:00-18:00 halt, weekends, and RTH-only overnight gaps; crypto has none.
  - `bool wkChg = timeframe.change("W")`. Evaluate it at global scope on every bar, not inside the engine's `if`, to keep its history consistent.
- **Engine, new step 12b**:
  ```pine
  if useGap and sesBrk and not na(aPDH) and not na(aPDL)
      float c0  = close[1]
      float gSz = math.abs(open - c0)
      bool  up  = open > c0
      if gSz >= math.max(gapMinD * (aPDH - aPDL), 2 * syminfo.mintick) and (up ? low > c0 : high < c0)
          int   sr = wkChg ? 12 : 11
          float hw = 0.05 * atr
          nextId += 1
          Level ng = f_newLevel(nextId, up ? 9 : 8, sr, c0 + hw, c0 - hw, c0, bar_index - 1, bar_index, coilScore, indScore)
          ng.hlMult := math.sqrt(math.max(1.0, (sr == 12 ? 604800.0 : 86400.0) / chartS))
          pool.push(ng)
          // retention: keep the last 3 NDOG and 5 NWOG ids in two var int arrays; drop the oldest from pool
  ```
- **Code touch points:**
  - `f_newLevel` side map (1085): add `or kind == 8`.
  - `grp()`: kinds 8/9 → family 2 (already in ICTPD-1's mapping).
  - `f_levelName` / `f_shortName`: `8, 9 => src == 12 ? "NWOG" : src == 13 ? "ORG" : "NDOG"`.
  - No `f_kzAff` / `f_tierW` change: src 11-13 fall to the defaults.
  - Exempt from the origin lockout (ICTPD-1 step 1, `kind <= 7`).
- The RTH variant (`src` 13: the 16:00 close or settlement, created at the 09:30 open with a daily-ATR gate) follows CL-4's spec and uses the same kinds.
- The Terminal style may draw the full gap box (pre-break close → open) with a CE line for ICT users. The *target* zone is the thin band at the pre-break close.

**Evidence.** Moderate (2.3): size-gated; asset-dependent (BTC weekend gaps continue). The ledger family edge measures it per chart.

**Risk.** Feed quirks (FX rollover, missing bars) create small spurious breaks; the size gate filters them. On 23-hour futures charts only NDOG/NWOG are seen; ORG needs CL-4/PA-2's session logic.

**Effort.** M.

### ICTPD-10 (P3 · robustness · S) Liquidity-void merge of consecutive same-direction FVGs [A, unchanged]

**Why.** 15-34% of FVGs sit in runs. Each run creates duplicate candidates, risks flicker between adjacent zones, and gives a CE of one sub-gap only. Merging does not change the edge (2.2: consecutive vs not, inside ±2 pp), so this is a cleanliness and stability change.

**Spec (step 13, 1868-1886).**
- Keep `var int lastBuId` / `lastBuBar` and the bearish pair.
- If a new bullish FVG forms at `bar_index == lastBuBar + 1` and that level is still in `pool` with `fill == 0`:
  - `top := math.max(top, low)`, `oTop := top`;
  - `price := (oTop + oBot) / 2`;
  - `disp := math.max(disp, fvB1 / fvA2)`.
- Otherwise create a new level as now.
- `fvgTrk` (iFVG tracking) stays per gap.

**Risk.** The merged CE is deeper, so non-active CE delivery takes longer (intended).

**Effort.** S.

### ICTPD-8 (P3 · statistics-ledger · M) Measurement-only "ICT checks" (replaces A's ICTPD-4, ICTPD-7 and ICTPD-8 scoring parts)

**Why.**
- The reference product markets "iFVG continuation".
- ICT traders believe in premium/discount and IRL/ERL.
- B's data says all three are null at the 1-ATR / H-bar scale (2.2, 2.5, 2.6).

Users should see that on their own chart, and nothing should change the score.

**Spec (Full view rows only).**
1. **iFVG HOLD k/n vs exp.**
   - On the first retest of an active iFVG (step 6, 1630-1644; bearish case: `high >= z.bottom`), open a light record: target = touch − 1·ATR, fail = close beyond `z.top`, expiry H.
   - Expected value p0 = `f_race(1.0 * atr, z.top - touchPx, potSig, -potMu)` (447).
   - Needs a `Zone.retested` flag and a parallel `var array<float>`.
   - Expected display about 50%.
2. **P/D: BUY-side from DISC k/n vs exp · SELL-side from PREM k/n vs exp.**
   - Store the zone quartile of `close` within the HTF range on `Trial` (`int pz`) at `f_openTrial`. Use the range after ICTS-4's fix, else `htfRH`/`htfRL` (923).
   - Book `pzN/pzK/pzE` (8 cells) in `f_book`.
3. *(Optional)* **PHASE.** A's ICTPD-4 event state (ERL raid-reject / IRL respect, expiry 2·H) tags `Trial.ph`. Report k/n vs expected per phase, with **no multipliers**.

**Evidence.** Moderate, for null effects.

**Risk.** None to selection; a few `var` arrays. Panel rows only in the Full view.

**Effort.** M.

### ICTPD-9 (P3 · statistics-ledger · S) Rejection-block near-miss statistic [A, unchanged]
- `Level.body` at chart-pivot creation: BSL `math.max(open[pivLen], close[pivLen])` (1762); SSL `math.min(…)` (1774); `na` for external pools.
- `Trial.rb` and an `rbHit` flag, set in `f_step` (1434).
- At booking, report "near-miss in wick zone x%" among expired misses. Optionally draw a thin RB band in the Terminal style.
- **Evidence:** weak (no statistics). **Risk:** none to selection. **Effort:** S.

### ICTPD-5 (P3 · level-source · M) IPDA 20/40/60-day extremes as named objectives [A, downgraded]
- **Why only P3:** they are reached at baseline (2.6), so their value is naming ("20D H") and better Swing-mode objectives. Sibling `academic_sr.md` (ACAD-5, 52-week/ATH) and `ict_time.md` (TIME-8) propose the same buffer. **Build one N-day ring buffer for all three.**
- **Spec as A:**
  - a ring buffer of the last 60 completed days from `f_rangeTrack` outputs (945), filled on `pdNew`;
  - `f_nDay(n, isHigh)`;
  - `f_pushExt(extReg, …, src 8/9/10, …)` after 1799;
  - `f_levelName` "20D H/L", "40D H/L", "60D H/L";
  - enabled when `timeframe.in_seconds() <= 86400`.
- **Change from A:** tiers must not exceed PW. Use `f_tierW` 8 ⇒ 0.70, 9 ⇒ 0.74, 10 ⇒ 0.78 (A had 0.84-0.95). There is no reach evidence for a high tier, and the sibling study asks for ≤ PW.
- **Risk:** registry crowding (cap 60, 1813). **Effort:** M.

---

## 5. Dropped or merged proposals (with reasons)

| A's proposal | Decision | Reason |
|---|---|---|
| ICTPD-1 `arrPrior` 0.90 on all arrays; `bigPen` 0.85 for size > 1 ATR | Replaced by neutral FVG/OB, `brkPrior` 0.90 and `dispPri` 0.95 | No reach evidence for liquidity over arrays (C3). The size effect was a distance artefact (C1). The middle-candle displacement effect is real in BTC 1H (-5.5 pp) and mild elsewhere |
| ICTPD-4 IRL↔ERL phase multipliers (×1.15 / ×0.92 / ×0.90) | Dropped. Waypoint → ICTPD-3; measurement → ICTPD-8 | E5: no phase effect, inconsistent sign (2.5) |
| ICTPD-7 adaptive premium/discount side prior | Dropped. Measurement → ICTPD-8 | E4: no ICT effect; momentum at the 20-day scale (2.6). A learned multiplier would mostly re-learn drift, which `potMu` and `htfBias` already carry |
| "Opposing arrays in the path" penalty (implied by A's concept 1.12) | Not proposed | Arrays show no reaction at first touch (≈ 50%) |
| Feeding respected/disrespected FVG events into D | Not proposed | 50.0-52.3% race outcomes (2.2) |

---

## 6. Notes for implementers
- **Order.** Ship ICTPD-1 before or with ICTPD-2. ICTPD-6 depends on ICTPD-1's `kind <= 7` lockout guard and the family mapping.
- **Declarations.**
  - New inputs go into the existing groups at the top (no forward references).
  - `f_hasZone` goes among the STATE HELPERS (after 1100); `Zone` is declared at 351-361.
  - `raidedH/L` go in STATE (1020-1080).
  - `sesBrk` goes at global scope after 961. `aPDH/aPDL` exist from 952.
- **Non-repainting.** All new logic is on confirmed bars. `time[1]`, `close[1]`, `open` and `wkChg` on a confirmed bar are final values.
- **Clean look.** Only new target codes (NDOG, NWOG, BEMB if enabled) and tooltip lines change. Everything else is Terminal or Full view.
- **Siblings to coordinate:**
  - `classic_levels.md` CL-4 and `price_action.md` PA-2 (one gap/settlement object, kinds 8/9, src 11-13);
  - `price_action.md` PA-1 (projections must use kinds 10/11);
  - `ict_struct.md` ICTS-4 (the dealing range behind P/D);
  - `smc_impl.md` §5 (zigzag breaker template, an alternative to ICTPD-2's BOS + raid paths, which produce largely the same blocks);
  - `academic_sr.md` ACAD-5 and `ict_time.md` TIME-8 (one N-day buffer).
- **Limitations of B's tests.**
  - CME 1H covers only 13 months of a bull market and 5m only 3 months.
  - B's baseline is unconditional per instrument (the engine's `f_potBase` also splits by HTF regime).
  - The ±1 ATR race ignores drift (the unconditional race is 49.5-52.5%).
  - GC is excluded as a suspected data artefact.
  - Results are for H = 30 (1H/5m) and H = 20 (daily).

## 7. Sources

**B's own tests (reproducible).** All under `study/ict_pd_b_tools/`:

| Script | What it tests | Output |
|---|---|---|
| `blib.py` | shared loaders, ATR, surface, pivots, clustered statistics | n/a |
| `e1_fvg.py` | FVG reach, ladder, reaction | `out_e1_*` |
| `e2_blocks.py` | OB and breakers | `out_e2_*` |
| `e3_gaps_pd.py` | NDOG/NWOG and premium/discount | `out_e3_e4.txt` |
| `e5_irl_erl.py` | IRL/ERL alternation | `out_e5.txt` |
| `e6_ifvg_htf.py` | iFVG retest, HTF FVG, first presented FVG | `out_e6.txt` |

Data came from sibling studies: `amt_data/cme`, `classic_tools/btc_1h.csv`, `bias_data`.

**Controlled vendor studies** [A; not re-fetched this session]:
- Nordman Algorithms (2026). Do Fair Value Gaps Work? https://www.nordman-algorithms.com/blog/do-fair-value-gaps-work/
- Nordman Algorithms (2026). Do Order Blocks Work? https://www.nordman-algorithms.com/blog/do-order-blocks-work/
- Nordman Algorithms (2026). ICT Displacement and the Market Structure Shift. https://www.nordman-algorithms.com/blog/ict-displacement-market-structure-shift/
- Barot (2026). Fair Value Gaps Work: Until You Try to Trade Them. SSRN 7148099. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7148099
- Trader Markus (2026). Fair value gap: a test on 26 years of S&P 500. https://tradermarkus.com/fair-value-gap/
- MarketTrace (2026). Fair value gaps: we measured 4,827 of them on Bitcoin. https://markettrace.ai/blog/fair-value-gap

**Gap base rates** [A; not re-fetched]:
- https://www.thetrading.tools/gap-analysis
- https://quantifiedstrategies.substack.com/p/gap-trading-strategies
- https://finabase.io/learn/trading/gap-trading
- https://www.edgeful.com/blog/posts/fair-value-gap-best-practices-guide
- https://www.edgeful.com/blog/posts/es-futures-trading-strategies
- https://fxnx.com/en/blog/fair-value-gap-fill-rate-measured-across-thousands-gaps (weak)
- https://tradeify.co/education/donchian-channels

**Academic:**
- Taylor, V. (2026). Evaluating the Predictive Validity of ICT's AMD Model on CME E-Mini NASDAQ-100 Futures. arXiv 2610.35887. **B read the full text.**
- Vlasiuk, D., Smirnov, M. (2025). Push-response anomalies in high-frequency S&P 500 price series. arXiv 2511.06177. [B-new]
- Zawadowski, A., Andor, G., Kertész, J. (2004). Short-term market reaction after extreme price changes of liquid stocks. arXiv cond-mat/0406696. [B-new]
- Osler, C. (2000). Support for Resistance. FRBNY EPR 6(2). https://www.newyorkfed.org/medialibrary/media/research/epr/00v06n2/0007osle.html (numbers verified by sibling `academic_sr.md`)
- Osler, C. (2003). Currency orders and exchange-rate dynamics. J. Finance 58(5). Osler, C. (2005). Stop-loss orders and price cascades. JIMF 24(2).
- Kavajecz, K., Odders-White, E. (2004). Technical analysis and liquidity provision. RFS 17(4) (via sibling).
- George, T., Hwang, C.-Y. (2004). The 52-Week High and Momentum Investing. J. Finance 59(5). https://www.bauer.uh.edu/tgeorge/papers/gh4-paper.pdf (numbers verified by sibling)
- Plastun et al. (2020), US index price gaps 1928-2018 (via sibling `session_stats.md`).

**Definitions** [A; LuxAlgo Library concept pages and ICT mentorship transcriptions; not re-fetched]:
- https://www.luxalgo.com/library/concept/pd-arrays/ (and the pages for premium-and-discount, order block, breaker-block, mitigation-block, rejection-block, propulsion-block, fvg-behavior-rules, consequent-encroachment, inversion-fvg, volume-imbalance, balanced-price-range, implied-fvg, new-week-opening-gap, new-day-opening-gap, internal-vs-external-range-liquidity, ipda-and-price-delivery-theory, draw-on-liquidity, low-resistance-vs-high-resistance-liquidity-runs)
- ICT summary notes (studocu 46530291, 57868256)
- https://innercircletrader.net/tutorials/ict-pd-array-key-to-trade-execution/

**Open source:**
- joshyattridge/smart-money-concepts (Python; B read `smc.py`: `fvg(join_consecutive)`, `ob` with breaker and `close_mitigation`). https://github.com/joshyattridge/smart-money-concepts
- LuxAlgo "Breaker Blocks with Signals" logic via the PyInd port (sibling `smc_impl.md` §1.10).

**Sibling studies used:**
- `classic_levels.md`: T2 N-day extremes, T3 gaps, CL-4.
- `session_stats.md`: weekend gaps.
- `price_action.md`: pool reach, PA-1, PA-2, the ETH-session note.
- `academic_sr.md`: Osler, George & Hwang, Kavajecz verification.
- `ict_struct.md`: ICTS-4 dealing range.
- `smc_impl.md`: breaker template.
- `skeptic.md`: claim register C5-C15.
