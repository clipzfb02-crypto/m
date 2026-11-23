# ICT PD Array Matrix: study for the DOL engine

Domain: premium/discount and equilibrium, the PD array hierarchy (old highs/lows, rejection block, order block, FVG (BISI/SIBI), liquidity void, breaker, mitigation block, propulsion block, vacuum block, volume imbalance, opening gaps NWOG/NDOG, BPR, consequent encroachment, mean threshold), inversion FVGs, which arrays act as TARGETS and which as ENTRY zones, the exact candle rules, how ICT ranks arrays for the draw, HTF arrays as magnets, and what "filled", "respected" and "disrespected" mean.

Engine file: `baseline_v2.pine` (line numbers below; identical to `/home/user/m/indicators/dol_engine.pine`).

---

## 0. Executive summary (read this if nothing else)

1. **PD arrays are not magnets beyond distance. Five independent controlled studies agree** (section 2.1). Price returns to FVGs and order blocks about as often as it returns to random zones of the same size at the same distance:
   - FVGs: 73.0% vs 72.9% (Nordman, 38,114 returns, ES/NQ/6E/6A, 5-minute charts).
   - Order blocks: 73.7% vs 73.7% (Nordman, 10,986 touches).
   - S&P 500 daily bullish FVGs: 69% vs 69% within 20 days.
   - BTC 1H FVGs: 75.6% vs 72.4% within 24 hours.
   - SSRN, about 40,000 FVGs: about 5 pp above random as a measurement, no tradeable edge.

   The reaction at a zone is real but small (+2.5 to +5 pp) and short-lived (5 to 15 minutes). For a *forecasting* engine, the probability that an array is reached is explained almost entirely by distance and volatility.

   The engine already uses the right methodology: its ledger compares each family with a distance-matched random level (`f_potBase`, `f_calMult`). It does **not** use the right *prior*. It gives arrays a density bonus for displacement quality, gap size and HTF origin (line 687). The evidence says that bonus is neutral at best. For near-term reach it has the **wrong sign**: large gaps and large displacement fill *less* often soon (BTC daily: large-tercile gaps fill 46% within 7 days vs 79% for the small tercile; SPY opening gaps over 1% fill same-day 26 to 33% vs 78 to 80% for 0.1 to 0.25% gaps).

2. **The engine's breaker filter is on the wrong side.** ICT's own definition is: "Bearish Breaker Block is a bearish range or Down Close Candle in the most recent Swing Low prior to an Old High being violated" (mirror for bullish). The liquidity that must be taken is the *old extreme violated by the leg away from the block*. The engine instead requires that the order block's *own origin* swept a 20-bar extreme (`tookL`/`tookH`, lines 1691, 1706, 1734, 1747). That discards most canonical breakers and keeps an unrelated subset. The engine also misses wick-raid breakers, because order blocks are only created after a body-close BOS, and it never tracks mitigation blocks.

3. **ICT's own rule for choosing the draw is liquidity first, with arrays as waypoints.** Delivery alternates between external range liquidity (old highs/lows beyond the dealing range) and internal range liquidity (FVGs inside it). The engine has the directional half of this (a raid that holds means continuation and a raid that rejects means reversal, line 1581), but not the *target-type* sequencing. This doctrine has no published statistics (weak evidence). The engine's ledger can measure it.

4. **Premium/discount is only displayed** (Terminal ZONE column, lines 2327-2332) and used as two confluence anchors (`dayEQ`, `htfEQ`, lines 967-968). It plays no part in bias or selection. The strong literature is *against* a naive premium/discount mean-reversion rule at long horizons: George and Hwang (2004) find that nearness to the 52-week high predicts *continuation*. At intraday horizons there is no evidence either way. Recommendation: learn it adaptively from the ledger rather than hard-code ICT's "longs only in discount".

5. **Missing level sources with ICT standing:**
   - IPDA 20/40/60-day extremes. These are the canonical HTF external range. Donchian/Turtle breakout stops also cluster there.
   - Opening gaps (NWOG/NDOG). Base fill rates are documented and depend strongly on gap size.

   Both can be built with no extra `request.*` calls.

Ten proposals follow in section 4, best first.

---

## 1. Concepts: definitions, parameters, edge cases

Notation: bar `t` is the current confirmed bar, `[k]` is k bars back, H/L/O/C are high/low/open/close, ATR is ATR(14).

### 1.1 Dealing range, premium, discount, equilibrium (EQ)

- **Dealing range**: "the swing low and high of the most recent leg that did something meaningful, such as sweeping a prior low or breaking structure" (LuxAlgo, premium-and-discount). ICT draws it on the HTF (4H/D) and executes inside it on a lower TF. Nested ranges are fractal; when they conflict, defer to the higher TF.
  - Re-anchor rule: "a close beyond either extreme, or a new leg through major liquidity, retires it; redraw from the new swings."
- **EQ** = (R_high + R_low) / 2. **Premium** is above EQ and **discount** is below. Sub-levels:
  - quadrants at 0.25 and 0.75;
  - OTE at 0.62 to 0.79 retracement (sits in discount for longs by construction);
  - "deep discount/premium" beyond the quadrant.
- **IPDA data ranges** (ICT's HTF version): "rolling look-backs of 20, 40, and 60 trading days". The highest high and lowest low of each window frame the short-, intermediate- and long-term dealing ranges (LuxAlgo, IPDA).
- **Usage**:
  - Bullish read: longs only in discount. Bearish read: shorts only in premium.
  - Target ladder from a discount entry: first EQ, then premium-side liquidity (the old high).
  - Arrays above EQ are "premium arrays": entries for shorts and **targets for longs**. Mirror for discount.
- **Failure modes**:
  - "A trending market can spend a long time on the 'wrong' side of 50% without ever rebalancing."
  - When the 50% keeps getting left behind, the drawn range is obsolete.
- **DOL role**: a side prior (from discount the draw is buy-side, from premium it is sell-side) plus a target ladder (EQ, then the opposite extreme).

### 1.2 The PD array matrix (ordering)

Canonical 2016 mentorship order, read from the range extreme back toward EQ:

| Premium (above EQ) | Discount (below EQ) |
|---|---|
| Old High (or Low) | Old Low (or High) |
| Bearish Rejection Block | Bullish Rejection Block |
| Bearish Order Block | Bullish Order Block |
| Fair Value Gap (SIBI) | Fair Value Gap (BISI) |
| Liquidity Void | Liquidity Void |
| Bearish Breaker | Bullish Breaker |
| Bearish Mitigation Block | Bullish Mitigation Block |
| (EQ) | (EQ) |

Sources: LuxAlgo PD arrays; ICT Tips Season 4 notes (studocu).

- Later eras add volume imbalance, BPR, iFVG, NWOG/NDOG, propulsion and vacuum blocks, and the Unicorn.
- **The ordering is spatial (where each array tends to sit relative to the range extreme), not a strength ranking**. LuxAlgo: "Treat it as a checklist of what to look for in sequence, not a law... the list differs slightly across eras of the teaching."
- ICT ranking for the *draw* (LuxAlgo, draw-on-liquidity):
  - "Higher-timeframe pools outrank lower ones."
  - "Engineered pools under equal highs or lows rank above single swing points."
  - "An untapped weekly extreme [is] a stronger magnet than one already probed."
  - Liquidity (old highs/lows) is the primary DOL. Arrays are where price *reacts on the way* or where it rebalances after an external raid.
- **Targets vs entries**: "Ahead of price they are draws (candidate targets ranked by proximity and importance); behind price they are entry inventory." With a bullish HTF read: buy from discount arrays, aim at premium arrays and buy-side liquidity.

### 1.3 Old high / old low (top of the matrix)

A prior swing extreme with resting stops beyond it (buy stops above, sell stops below). It is swept when price trades through. This is the engine's core liquidity object and belongs to another study domain. It appears here because it heads the PD matrix and has the strongest evidence of any array (section 2.4, Osler).

### 1.4 Rejection block (RB)

- ICT text: "Bearish Rejection Block is when a Price High has formed with long wick(s) on the high(s) of the candlestick(s) and Price reaches high above the body of the candle(s) to run Buy Side Liquidity out before Price Drops lower."
- **Zone**: from the top of the swing candle's body, max(O, C), to the wick high. The bullish RB mirrors this (min(O, C) to the low).
- **Parameters**: no fixed wick size. The wick should be conspicuous relative to recent bars, sit at a genuine swing extreme, and ideally record a sweep.
- **Use**:
  - Entry: inside the wick span on the revisit, stop beyond the extreme.
  - As a **target**: "profit objectives are trimmed to the near edge of the prior extreme's wick, on the view that a reaction can arrive before the precise level prints."
- **Failure**: body acceptance beyond the wick extreme.
- **DOL role**: refines *where on an old high* a target realistically completes (body extreme vs wick extreme).

### 1.5 Order block (OB) and mean threshold (MT)

- **Bullish OB**: the last down-close candle (or consecutive down-close group) before an impulsive up move that breaks structure or trades through a prior swing, ideally leaving an FVG. The bearish OB mirrors this.
  - ICT original: "A Down Close candle ... which has the most range between the open and close". That is the largest-bodied down candle in the swing, not necessarily the last one.
  - ICT validation: price trades above the OB candle's high.
  - Expected behavior: "Price trades Higher away from the Bullish Order Block and then Returns to the Bullish Order Block Candle or Price Bar High" (return to origin, RTO).
- **Zone conventions**: full high-low (most common); body only; or open-to-extreme. There is no official rule. "Pick one convention ... and apply it consistently."
- **Mean threshold (MT)**: the 50% line of the block, measured over either the range or the body (sources disagree). Entries in the deeper half are preferred. A body close beyond MT is the first warning.
- **Lifecycle**:
  - *mitigated* = price has returned into the block (downgrade after first use);
  - *invalidated* = a close through the far side, after which it is re-read as a breaker candidate (section 1.10).
- **Grading**: displacement away (required); a sweep of nearby liquidity just before the block; an FVG in the leg; location (bullish blocks in discount).

### 1.6 Fair value gap (FVG): BISI / SIBI

- **Bullish FVG (BISI)** at bar t: `low[0] > high[2]`. Zone = [high[2], low[0]], all three candles wick-to-wick.
- **Bearish FVG (SIBI)**: `high[0] < low[2]`. Zone = [high[0], low[2]].
- **Common parameters**: minimum size (0.10 to 0.25 x ATR); the middle candle should be a displacement candle (large body, closes near its extreme). Some tools wait N bars before showing the gap. Merging consecutive same-direction FVGs into one zone (highest top, lowest bottom) is the `join_consecutive` convention of the popular `smartmoneyconcepts` Python library.
- **First presented FVG**: the first FVG after a time anchor (commonly the 09:30 NY open) is ranked above later gaps.
- **Immediate rebalance**: a gap re-entered on the very next candle, read as continuation, not weakness.
- **Implied FVG** (wick midpoints stand in for boundaries; ranked one grade below a true FVG):
  - `UWM_x = (H_x + max(O_x, C_x)) / 2` and `LWM_x = (min(O_x, C_x) + L_x) / 2`.
  - Bullish if `LWM_t > UWM_(t-2)` and `L_t <= H_(t-2)`; zone = [UWM_(t-2), LWM_t].

### 1.7 Consequent encroachment (CE) and FVG behavior rules (filled / respected / disrespected)

- **CE** = the 50% line of an FVG. By extension it is also used for a wick, an opening gap or a liquidity void.
- **Respected**: price trades into the gap (often only to CE) and continues in the gap's direction. "A gap as respected while closes hold on the near side of CE, and as weakened once price closes through it" (closes through CE shift expectation toward a full fill).
- **Disrespected**: a candle *body closes beyond the far edge*. The gap is then violated and re-labelled an inversion FVG (section 1.8).
- **Fill ladder**: tap (any re-entry), then CE (50%), then full fill (traded through the far edge). The empirical ladder (BTC 1H, 24 h horizon): touch 85.3%, CE 80.6%, full 75.6%. Details in section 2.2.
- **Breakaway gaps** (from a base or a sweep, with urgency) are *not expected* to fill. Ordinary gaps are expected to rebalance eventually.

### 1.8 Inversion FVG (iFVG)

- **Formation**: "a candle body closing beyond the far side of the gap; a wick-through alone is usually read as a probe". Some tools act on a close beyond CE.
- After inversion, the span acts with the opposite polarity: a failed bullish FVG becomes resistance.
- **Invalidation**: a reclaim (a close back through the span). It stays valid until reclaimed; there is no fixed duration.
- **Role**: retest entry, bias flip, confirmation leg of sweep models. It is an **entry zone, not a target**.
- Evidence (section 2.3): on S&P daily data, broken gaps held on retest exactly as often as random zones.

### 1.9 Liquidity void, vacuum block, volume imbalance, opening gaps (NWOG/NDOG), BPR

- **Liquidity void**: "Sudden runs in Price will leave porous Price Action that tends to fill in at a later time." It is a multi-candle one-directional run (several consecutive displacement candles, usually a stack of FVGs). Practically: merge consecutive same-direction FVGs of one leg into a single zone with its own CE.
- **Vacuum block**: "created in Price Action as a result of a volatility event. The gap forms by a 'vacuum' of liquidity directly related to an event." That is a true price gap (news gap, or a session/day/week opening gap). It is not a synonym for a rejection block.
- **Volume imbalance (VI)**: two consecutive candles whose *bodies* do not overlap (`open[0] > close[1]` for bullish, measured body to body) while the *wicks still overlap*. If even the wicks do not overlap, it is an opening gap. It is the smallest inefficiency and is mostly used to refine entries at the edge of an OB or FVG.
- **NWOG** (New Week Opening Gap): Friday's close to the new week's first open (futures: Friday 17:00 ET close vs the Sunday 18:00 ET reopen). Mark the high, low and CE, and keep "commonly the last five". Usage:
  - as a destination after a sweep of a prior week's extreme;
  - as S/R at its edges and CE;
  - clusters of overlapping NWOGs count as a stronger draw.
- **NDOG** (New Day Opening Gap): the CME 17:00 ET close vs the 18:00 ET reopen. Keep "the current gap plus at most a few recent ones". On RTH-only stock charts the equivalent is the overnight opening gap. Crypto has no true NDOG/NWOG.
- **BPR** (balanced price range): the *intersection* (not the union) of a bullish FVG and a later bearish FVG over the same prices, or the reverse. The newer displacement carries the bias. "Fill is the wrong frame; the overlap has already traded in both directions." It is an entry zone only.

### 1.10 Breaker block, mitigation block, propulsion block

- **Bearish breaker** (ICT original, verbatim): "a bearish range or Down Close Candle in the most recent Swing Low prior to an Old High being violated."
  - Sequence: swing high H1, swing low L1 (the down-close candle at L1 is a bullish OB), a rally that violates H1 (wick or close; BSL taken), then a drop that **closes below L1**.
  - The down-close candle at L1 is now the bearish breaker (resistance on retest).
- **Bullish breaker** (verbatim): "a bullish range or Up Close Candle in the most recent Swing High prior to an Old Low being violated." Mirror sequence: L1, H1, a decline that violates L1 (SSL taken), then a close above H1.
- **The sweep that qualifies a breaker is made by the failing leg that leaves the block**, not by the block's own origin. The strict ICT form requires that sweep; the loose retail form treats any violated OB as a breaker.
- **Mitigation block**: the same role-flip **without** the sweep. The failing swing falls short of the prior extreme (a lower high for the bearish case), then structure breaks. "Sweep means breaker, failure means mitigation block." Conventions disagree on exactly which candle is marked; the most common is the same block a breaker would use, graded lower.
- **Propulsion block**: a candle that trades back into an earlier OB (commonly to its MT) without closing through it and then launches away. It becomes a new, tighter continuation block. It is an entry zone only.

### 1.11 HTF arrays as magnets

- ICT: "a higher-timeframe array (a daily gap or order block) defines the zone worth trading, and the lower-timeframe arrays that form inside it refine the actual entry." HTF arrays are said to be the draw; LTF arrays are the entry.
- Evidence: daily S&P bullish FVGs are reached exactly as often as random zones. Daily *bearish* FVGs are reached about 9 pp more often than random within 20 days. That is plausibly the post-selloff bounce of an equity index, not a gap effect (the author: "The bounce fills the gap; the gap doesn't cause the bounce").

### 1.12 Internal vs external range liquidity (IRL/ERL), and price delivery

- **ERL**: stops beyond the range extremes. **IRL**: FVGs, OBs and minor equal highs/lows inside the range.
- **Alternation rule**: "After external liquidity is taken, the next draw on liquidity is commonly internal (back into the range to rebalance an inefficiency), and once internal liquidity is filled, expectation rotates outward toward the opposite extreme." ICT shorthand: ERL to IRL to ERL.
- **Failure**: "a genuine breakout takes the external pool and keeps going." Models therefore require "a sharp rejection or a lower-timeframe structure shift" after the raid before targeting internal liquidity.
- **Low- vs high-resistance runs**: a path through already-swept swings and same-direction FVGs is low resistance (fast and direct). A path through fresh, unswept swings and *opposing* imbalances is high resistance (slow, overlapping, "a pool behind many intact swings may never be reached on this attempt").

---

## 2. Evidence (numbers and sources)

Grades: **strong** = peer-reviewed or large replicated quantitative study; **moderate** = published, reproducible statistics or backtests with numbers; **weak** = practitioner consensus or anecdote; **none** = folklore or unfalsifiable.

### 2.1 Are PD arrays magnets? (Moderate, highly consistent across five independent controlled studies)

| Study | Data | Result vs distance-matched random level |
|---|---|---|
| Nordman Algorithms, "Do Fair Value Gaps Work?" (Nov 2026) | ES, NQ, 6E, 6A futures, 5m, Oct 2023 to Sep 2026; 38,114 returns to real FVGs vs 380,599 returns to fakes (10 same-size, same-distance twins per gap, same NY hour and month); 384 settings | **Came back to 73.0% of FVGs vs 72.9% of random levels** (ES 72.7 vs 72.6, NQ 72.4 vs 72.9, 6E 73.7 vs 73.2, 6A 73.3 vs 73.1), both after a median of 5 bars. Reaction (edge ratio MFE/MAE after the touch): **+3.7% at 5 min, +2.5% at 15 min** (passed pre-registered tests); +2.9% at 1 min (failed); **−0.2% at 1 h, −0.9% at 1 day**. 98% of settings beat fakes at 5 min, vs 44% for noise posing as real. Gap size "barely matters". Net after costs is negative (ES −$8.90/trade). Exploratory: FVGs left by the MSS leg scored 1.08 vs 0.99 for fakes at 15 min and 1 h. |
| Nordman, "Do Order Blocks Work?" (Nov 2026) | Same markets; 14,916 OBs, 10,986 touched; 109,975 random-zone touches | **Came back to 73.7% of OBs vs 73.7% of random zones**, half within about 10 bars. A limit at the edge is no better than random (1 min: 1.032 vs 1.042). Next-bar entry after the touch bar closes: +4.8% at 1 min, +3.3% at 5 min. Fresh OBs best (20-bar life: +7.5% at 1 min vs +4.0% unlimited). Bigger gaps do not make stronger OBs. Gaps with an OB behind them lost their edge. Standalone: negative after costs except NQ (+$0.82). |
| Barot, SSRN 7148099, "Fair Value Gaps Work: Until You Try to Trade Them" (2026) | 7 years, 4 liquid futures (ES, NQ, gold, silver), 3 timeframes, about 40,000 FVGs | Reaction "approximately five percentage points above random", "no tradeable edge". One apparently profitable construction (PF about 2.4) was look-ahead bias from hourly-bar exits; on 1-minute data PF is about 1.0. Consistent across all instruments and timeframes. |
| Trader Markus, "FVG: a test on 26 years of S&P 500" (Oct 2026) | S&P 500 daily, 2000 to 2026; 1,337 bullish and 887 bearish FVGs; control zone = same width and distance from a nearby non-gap day | **Bullish filled within 20 days 69% vs random 69%; within 60 days 80% vs 79%**. Bearish 81% vs 72% within 20 days (2014 to 2026: 84% vs 76%). Ever filled: 92% (bullish), 100% (bearish). iFVG: broken bullish gaps held as resistance on **38% of retests vs 38%** random; broken bearish gaps held as support **47% vs 47%** (2014 to 2026: 50% vs 43 to 49%). |
| MarketTrace, "Fair value gaps: we measured 4,827 of them on Bitcoin" (Aug 2026) | Coinbase BTC-USD, May 2024 to Aug 2026; 3,690 1H, 952 4H, 185 1D FVGs | 1H full fill **75.6% vs random 72.4% within 24 h (+3.2 pp)**, 85.2 vs 83.1 within 3 days, 90.9 vs 89.4 within 7 days. Direction after the first touch: bullish FVG 53.0% positive over 24 h vs a 51.1% baseline; bearish 50.8% (coin flip). |

Conclusion for the engine: the probability that an array is reached within H bars is about the probability of a random level at the same distance. The only array-specific signals with support are:
- a few pp of short-lived reaction;
- **displacement size reduces near-term fill probability** (section 2.2);
- possibly, MSS-leg FVGs react slightly longer (exploratory only).

### 2.2 Fill ladder and size effects (Moderate)

- **BTC (MarketTrace)**, touch / CE (50%) / full fill:
  - 1H: 24 h 85.3 / 80.6 / 75.6; 7 days 94.7 / 92.7 / 90.9.
  - 4H: 24 h 71.8 / 62.3 / 54.2; 7 days 88.0 / 84.3 / 80.8.
  - 1D: 7 days 74.5 / 67.9 / 62.0; 30 days 86.5 / 82.6 / 79.2.
  - Implied conditional ladder at short horizons: P(CE | touch) is about 0.87 to 0.95 and P(full | touch) about 0.75 to 0.89.
  - Median hourly gap fully filled in 5 h (first touch 2 h); p90 is 105 h, and 57 days for daily gaps.
- **Size terciles, full fill within 7 days** (MarketTrace): 1H 95.0 / 92.6 / 85.0%; 4H 89.2 / 82.1 / 71.1%; **1D 78.7 / 61.7 / 46.0%**. "Displacement size is the residual signal."
- **FXNX** (method undisclosed, no control, **weak**): edge tap 74.6%, CE 61.2%, full closure 48.7%. "Daily and H4 imbalances ... 82.4% mitigation within 15 to 20 bars"; M1/M5 survival 44.2%.
- **Edgeful** (YM 30-minute, last 6 months, **weak to moderate**): bullish FVGs unmitigated by close 60.71% (by wick 52.38%); bearish 63.2% (50.4%) within the same session.

### 2.3 Opening gaps (Moderate for base rates; magnet-vs-random untested)

- **SPY, every overnight gap since 1993** (thetrading.tools):
  - Up-gaps, same-day fill: 0.1 to 0.25%: **78%** (5 sessions: 91%, n=1,213); 0.25 to 0.5%: 60% (82%); 0.5 to 1%: 46% (70%); 1 to 2%: **26%** (53%); 2%+: 27% (52%).
  - Down-gaps: 80 / 66 / 43 / 33 / 29% same day (91 / 89 / 76 / 68 / 60% within 5 sessions).
  - For 1%+ up-gaps the average open-to-close return is positive and 60% of days close up ("gap-and-go, not gap-and-fade").
- **QuantifiedStrategies** (SPY): 1,967 gap-ups 50.5% filled same day; 1,556 gap-downs 54.9% (82.0% within 5 sessions). 0.25 to 0.5% up-gaps 59.5%; 1 to 2% up-gaps 30.2%.
- **Finabase** (10 large US stocks/ETFs, Oct 2024 to Oct 2026, 5,000 symbol-days): same-day fill 0.5 to 1%: 55 to 57%; 1 to 2%: about 36%; 2 to 4%: 25 to 28%; 4%+: 14 to 19%. "Small gaps filled a little more than half the time, which is close to what random intraday movement would produce."
- **Edgeful** (ES, recent window): gap ups and gap downs both filled 67% of the time (50/75 and 34/51 days).
- NWOG/NDOG specifically: "practitioner lore plus visible examples, not audited statistics" (LuxAlgo). **Weak**.

### 2.4 Old highs/lows and S/R reactions (Strong)

- **Osler (2000)**, "Support for Resistance: Technical Analysis and Intraday Exchange Rates", FRBNY Economic Policy Review 6(2). Levels published by six FX firms (DEM, JPY, GBP, 1996 to 1998):
  - Intraday trends "bounced off the published levels **60.8 percent** of the time on average" vs **56.2%** for 10,000 sets of artificial levels.
  - Excess by currency: +4.2 pp (mark), +5.6 pp (yen), +4.0 pp (pound). The best firm was +9.2 pp.
  - The effect persisted 5 days after publication (1.7 pp weaker).
- **Osler (2003)**, J. Finance, "Currency orders and exchange-rate dynamics: explaining the success of technical analysis":
  - Take-profit orders cluster at round numbers (reversals).
  - Stop-loss orders cluster just beyond them, so trends accelerate after crossing (stop cascades).
  - This is the mechanism behind "liquidity beyond old highs/lows". The engine encodes it as "swept only when traded through".

### 2.5 Premium/discount, range position, 20-day extremes (Mixed)

- **George and Hwang (2004)**, J. Finance, "The 52-Week High and Momentum Investing" (**strong**, cited more than 1,300 times). Nearness to the 52-week high "dominates and improves upon the forecasting power of past returns". The 52WH winner-minus-loser spread is significant (for example 0.45%/month, t=2.00, and 1.23%/month, t=7.06, in their tables). At monthly horizons in stocks, being in "premium" predicts **continuation**, the opposite of a naive "sell premium".
- **Donchian/Turtle**: 20- and 55-day breakout entries and 10/20-day exits are among the most widely used systematic rules. That is a mechanism for resting stop/entry orders beyond N-day extremes (**weak to moderate** as a liquidity argument).
  - Tradeify (ES/NQ daily, 252 sessions to Nov 2026, **weak**, one year): "20 session breaks often failed to hold the close. Ten-session follow-through trailed random entries."
- ICT premium/discount and IPDA 20/40/60-day ranges as directional rules: **no published statistics** (weak).

### 2.6 Structure and displacement (Moderate; context for bias)

- **Nordman, "ICT Displacement and the Market Structure Shift"** (15,817 MSS signals, ES/NQ/6E/6A, 5m, swing strength 5):
  - Edge ratios with/without displacement at 5 min / 15 min / 1 h / 1 day: big candle 1.08/1.03, 1.04/1.04, 1.00/1.00, 0.99/1.00; FVG 1.05/1.04, 1.06/1.00, 1.02/0.97, 1.00/1.01; both 1.13/1.03, 1.08/1.03, 1.02/1.00, 0.99/1.00.
  - "With or without displacement, price went about as far against the trade as in its favour."
- **Taylor (2026), arXiv 2610.35887**, "Evaluating the Predictive Validity of ICT's Accumulation-Manipulation-Distribution (AMD) Model on CME E-Mini NASDAQ-100 Futures" (NQ 15m, 2022 to 2026, N=484 signal days). "No directional information beyond the daily trend regime was observed." Aligned with trend: 62 to 71% correct. Against trend: 25 to 30%. This supports letting HTF trend dominate the draw vector (the engine already weights `htfBias` 0.5, line 1892).

### 2.7 Concepts with no statistics (None or weak)

There are no audited statistics for: CE as a reaction level ("a convention with anecdotal support and no published statistics"), MT, rejection blocks, breakers, mitigation blocks, propulsion blocks, vacuum blocks, BPR ("no audited statistics"), volume imbalance, implied FVG, IRL/ERL alternation, or the PD matrix ordering. Grade: weak (practitioner consensus) or none.

---

## 3. Engine gap analysis (`baseline_v2.pine`)

| # | Concept | Status | Where | What the engine does / differs |
|---|---|---|---|---|
| 1 | FVG (BISI/SIBI) detection | **present** | 907-912, 1867-1889 | Wick-to-wick `low > high[2]` / `high < low[2]`, size ≥ `fvgMin`·ATR (0.15). Quality `fvgQBase` + size + BOS-within-3-bars; middle candle must close in the gap's direction or quality is halved; gate `fvgQMin` 0.45. All FVGs also go to `fvgTrk` for inversion. |
| 2 | Array target quality (displacement/size used as target density) | **wrong** (sign) | 687, 912, 1870, 1880, 1692, 1735, 1863 | Arrays' density = 0.5·qual + 0.3·coil + 0.2·induce **+0.20 for HTF**. qual grows with middle-candle body/ATR, gap size, and for OBs with leg size. Evidence: size/displacement does not raise reach probability and lowers near-term fill (2.1, 2.2). As a creation *gate* it is fine; as a *score bonus* it inflates exactly the arrays least likely to be revisited soon. |
| 3 | Arrays as targets vs entries (origin lockout) | **present** | 689-690, 135-137 | A fresh chart FVG/OB/BRK is ×0.25 until `originBars` have passed and price has left by `awayATR`: arrays behind price are entry inventory, not destinations. Matches ICT. |
| 4 | CE / delivery semantics | **present** | 123-124, 306, 1565-1577 | Non-active arrays count as delivered at CE by default (`delivIn`); the partially filled zone is cropped. The active DOL counts a touch (design decision). The core glow line of an array target is at `price` = original mid = CE (1862, 1874, 2219). |
| 5 | Fill ladder (tap → CE → full) readout | **missing** | — | PoT is to the near edge only. No CE/full probabilities and no ledger stats on how deep fills go. |
| 6 | Respected / disrespected | **partial** | 1598-1627 | Disrespect = body close beyond the far edge, which becomes an iFVG (correct rule). "Respected" (wick in, close back, continuation) is not tracked, and neither event feeds the draw vector D. |
| 7 | iFVG | **present** | 1598-1644, 195-200 | Inversion on a close beyond the far edge. Removed when it fails (close back through) or after > `ifvgMaxIn` body closes inside. Display and alert only, not a target. Consistent with evidence (iFVG retests ≈ random). |
| 8 | Order block | **present** (minor differences) | 1663-1748 | Created only on a **body-close BOS** through the last chart swing (`bosUp`/`bosDn`, 1542-1543). The OB is the **last** down-close candle at or up to 5 bars before the leg low (ICT original: the *largest-body* down-close candle in the swing; consecutive candles are not merged). Zone = full range; MT = range mid. Validation `close > high[obI]`. Quality = FVG in leg 0.4 + origin sweep 0.3 + leg size 0.3, min 0.40. Already-mitigated blocks (revisited to MT) are skipped. |
| 9 | Mean threshold | **partial** | 1684, 1696-1700, 1727, 1737-1741 | Used only to reject already-mitigated OBs. Not used for respect/disrespect or as a level. |
| 10 | Breaker | **wrong** (filter on the wrong side) | 1646-1661, 1691, 1706-1707, 1734, 1747-1748 | OBs reach `obTrk` only if `tookL`/`tookH` is true: the block's *own origin* swept a prior 20-bar extreme. ICT requires the sweep by the *failing leg leaving the block* (old high violated for a bearish breaker). For BOS-created OBs that condition is always true, so `tookL` is the wrong test: it drops most canonical breakers and keeps a non-ICT subset. Wick raids (old high violated by wick, then MSS) never create a tracked block because OBs need a body-close BOS. |
| 11 | Mitigation block | **missing** | — | Failure swings (lower high, then break) are never tracked. |
| 12 | Rejection block | **missing** | 1752-1776 | Chart pools are anchored at the swing wick; the zone extends *beyond* the swing by `zoneATR` (stops). The body-to-wick span inside the swing (the RB) is not stored, so "near-miss into the wick zone" is invisible. |
| 13 | Propulsion block | **missing** | — | Entry-only concept; low DOL value. |
| 14 | Liquidity void | **partial** | 1945-1947, 203-207 | The VP path cost (thin-volume path ×1.10, wall ×0.85) and LVN zones capture "porous" price. Consecutive same-direction FVGs are separate levels (duplicate candidates, CE of a single sub-gap). |
| 15 | Vacuum block / opening gaps NWOG/NDOG | **missing** | — | True price gaps at session/day/week breaks are not detected. They become FVGs only if a 3-candle gap also exists. Session *opens* are confluence anchors only (964-966). |
| 16 | Volume imbalance | **missing** | — | Low DOL value. |
| 17 | BPR | **missing** | — | Entry-only; low DOL value. |
| 18 | Implied FVG | **missing** | — | Low DOL value. |
| 19 | Dealing range and premium/discount | **partial** | 776-779, 967-968, 1930-1933, 2323-2336 | `f_structure` keeps a rolling dealing range (`rngH`/`rngL`) per TF. The Terminal shows "PREM/DISC %". `dayEQ` and `htfEQ` are confluence anchors (+0.35 per anchor hit). **Not used in D, selection, or the ledger.** |
| 20 | IPDA 20/40/60-day ranges | **missing** | — | No N-day extremes. Only PDH/PDL, PWH/PWL (945-961, 1790-1799), and HTF/STF pivots. |
| 21 | HTF arrays | **partial** | 785-796, 939-942, 1854-1865 | HTF FVGs only (from `tfH`, [1]+lookahead_on, exact anchors via `f_barAtTime`), +0.20 density, slower decay `hlMult` = sqrt(TF ratio). No HTF OB, no STF FVG. Evidence does not support extra HTF magnetism (2.1, 1.11). |
| 22 | PD matrix ordering / array ranking | **partial** | 505-516, 661-696 | Liquidity has source tiers. Arrays are scored with the same pillars and no type prior. No rule like "arrays are waypoints on the way to liquidity". |
| 23 | IRL ↔ ERL alternation | **partial** | 1580-1582, 1891-1894 | Liquidity raids feed D (hold = continuation, reject = reversal, weighted by tier). There is no target-*type* sequencing (favor internal arrays after an external raid rejects; favor external pools after an array rebalances and price departs). |
| 24 | Low/high-resistance runs (arrays in the path) | **partial** | 684-685, 1912-1927, 1945-1947 | Inner stacked pools ×0.70; volume path cost. Opposing unfilled arrays between price and a pool are ignored. |
| 25 | Displacement validation of arrays | **present** | 897-904, 1666-1681, 1869-1870 | Displacement flags and BOS-proximity feed FVG quality; OBs require a BOS. (MSS evidence says displacement adds little directional information; it is fine as a gate.) |
| 26 | Distance-matched random baseline (the method of section 2.1) | **present** | 1313-1322, 1376-1382, 1426-1431, 1461-1499 | `f_potBase` is the empirical P(reach) of a random level at the same distance by HTF regime. `f_calMult` = bounded ((k+2)/(e+2)) ÷ global for 4 families. This is exactly the external studies' control. But the Full panel shows family hit % without the expected % (2410-2418), and bounds are [0.8, 1.2] with n ≥ 10. |

---

## 4. Proposals (best first; max 10)

Common infrastructure, which several proposals reuse: a **context-calibration helper** like `f_calMult` (line 1376). For each context dimension *c* (array size tercile, IRL/ERL phase, premium/discount zone × side) keep arrays `cxN`, `cxK`, `cxE` (trials, hits, Σ pBase) per cell, booked in `f_book` (line 1461) from fields stored on the `Trial` at open (`f_openTrial`, line 1426):

```pine
// generic bounded edge multiplier for one context cell, shrunk toward 1 by sample size
f_ctxMult(array<float> N, array<float> K, array<float> E, int cell, float lo, float hi, float nMin) =>
    float n  = N.get(cell)
    float kc = K.get(cell)
    float ec = E.get(cell)
    float KA = N.sum() > 0 ? K.sum() : 0.0
    float EA = E.sum()
    float r  = ((kc + 2.0) / (ec + 2.0)) / ((KA + 2.0) / (EA + 2.0))
    float w  = n / (n + nMin)                       // shrinkage: 0 at n=0, 0.5 at n=nMin
    n >= 5 ? f_clamp(1.0 + w * (r - 1.0), lo, hi) : 1.0
```

Dimensions multiply as in naive Bayes, each bounded to about [0.85, 1.15]. This avoids sparse joint cells.

### ICTPD-1 (P1) · Evidence-based array target model: neutral density, large-displacement penalty, array prior, honest family edge

**Why.** Five controlled studies (2.1) show that arrays are reached at the distance-matched random rate. Large gaps and large displacement are reached *less* often in the near term (2.2, 2.3). The engine rewards exactly those features in the target score (line 687), and also adds +0.20 for HTF arrays. That biases selection toward arrays the market is *least* likely to revisit within H. It also explains a likely complaint: targets that look "wrong" because the engine chases a big displacement FVG that price never revisits.

**Algorithm.**
1. Keep quality as a **creation gate** (`fvgQMin`, `obQMin`, unchanged).
2. In `evaluate()` (array branch, line 687) replace the density with a neutral, structure-only term, `dens = 0.40 + 0.30·coil + 0.30·induce` (no `qual`, no HTF bonus).
3. Add a new Level field `sz`: the zone height at birth in ATR for FVG/HTF-FVG/gaps, or leg size / ATR for OB/BRK. If `sz > bigDisp` (default 1.0 ATR), multiply `mult` by `bigPen` (default 0.85).
4. Multiply every array's `mult` by `arrPrior` (default 0.90), so that at equal pillars a liquidity pool outranks an array (ICT: liquidity first; the evidence also favors S/R pools, 2.4).
5. Calibrate arrays additionally by **size tercile** (bins < 0.35 ATR, 0.35 to 0.8, > 0.8) with `f_ctxMult` (bounds 0.8 to 1.2, `nMin` 30). `Trial.szBin` is −1 for liquidity.
6. Full panel (line 2410-2418): show **expected %** next to hit % per family (`stPE.get(g)/ng`), so the user sees the "FVG 72% vs exp 71%" test of section 2.1 on their own chart.

**Pine sketch.**
```pine
// INPUTS (G_SCORE / G_ARR)
float arrPrior = input.float(0.90, "Array Target Prior", minval = 0.5, maxval = 1.2, step = 0.05, group = G_SCORE,
  tooltip = "FVG / OB / breaker targets start at this multiplier: controlled studies find price revisits them about as often as random levels at the same distance. The accuracy ledger then calibrates each family.")
float bigDisp  = input.float(1.0, "Large Displacement (ATR)", minval = 0.2, step = 0.1, group = G_ARR)
float bigPen   = input.float(0.85, "Large Displacement Target x", minval = 0.5, maxval = 1.0, step = 0.05, group = G_ARR)
// TYPE Level: add   float sz = 0.0
// evaluate(), array branch (replaces 687-688)
    else
        this.dens := 0.40 + 0.30 * this.coil + 0.30 * this.induce
        this.mult *= (1.0 - 0.5 * this.fill) * arrPrior * (this.sz > bigDisp ? bigPen : 1.0)
// creation: nfu.sz := (low - high[2]) / atr (1874); nob.sz := (close - loV) / atr (1703); HTF FVG nf.sz := (hfTop - hfBot) / atr (1862)
```

**Value.** Fewer chase targets after strong displacement, and fewer flips between adjacent arrays. A liquidity-first DOL matches ICT practice and the evidence. The family edge row makes the engine's honesty visible.

**Measurable.** Per-family EDGE (k − E)/n and z before/after, plus the hit rate by size tercile.

**Risk.** On instruments where arrays genuinely outperform, the prior under-weights them until calibration catches up (bounded, about 20 to 30 trials per family). The Clean screenshot shows "Target: BEFVG", so arrays will still be chosen when they are the best candidate.

**Effort:** S.

### ICTPD-2 (P1) · Correct breaker definition, add wick-raid breakers, optional mitigation blocks

**Why.** Section 3 row 10: the engine's `tookL`/`tookH` filter checks the wrong liquidity. ICT verbatim: the breaker is the block "in the most recent Swing Low prior to an Old High being violated." The qualifying sweep is by the leg *leaving* the block. Mislabelled or missing breakers are a visible correctness problem for an ICT trader.

**Algorithm.**
1. Lines 1706 and 1747: push every BOS-created OB into `obTrk` (`if useBRK`). The BOS leg already violated an old extreme by close. Keep `tookL`/`tookH` as a +0.15 quality bonus, not a gate.
2. **Wick-raid path** (ICT's canonical breaker). In step 1 (around line 1542), detect `raidUp = not na(obSwingH) and high > obSwingH and close <= obSwingH and not raidH` (mirror for `raidDn`). On a raid:
   - locate the OB candidate at the leg low exactly as step 8 does (last down-close candle at or before the lowest low since `obSwingHBar`, `loI..loI+5`);
   - push `Zone(top, bottom, dir = +1, qual = 0.5, tookLiq = true)` to `obTrk` (no pool level: there was no BOS);
   - set `raidH := true`, reset when step 9 sets a new `obSwingH`.

   Step 7 (1651) already flips it to a bearish breaker on `close < z.bottom`.
3. **Mitigation block** (optional input, default off; conventions disagree). At each confirmed chart pivot low, store the OB candidate at that low together with the previous pivot high value. If the next confirmed pivot high is *lower* (failure swing) and a later close breaks the candidate's bottom, create kind 7 with `qual *= 0.7` and a tag. Add a Level field `variant` (0 = breaker, 1 = MB) for the label "BEMB"/"BUMB".
4. Split the ledger family `grp 3` into OB vs BRK (or use `f_ctxMult` on `variant`) so breaker edge is measured separately.

**Pine sketch** (step 1 additions, all at confirmed bars).
```pine
var bool raidH = false
var bool raidL = false
bool raidUp = not na(obSwingH) and high > obSwingH and close <= obSwingH and not raidH
if raidUp and useBRK
    raidH := true
    int   spanR = math.max(1, math.min(obLook, bar_index - nz(obSwingHBar, bar_index - obLook)))
    int   lI    = 0
    float lV    = low
    for k = 1 to spanR
        if low[k] < lV
            lV := low[k]
            lI := k
    for k = lI to lI + 5
        if close[k] < open[k]
            obTrk.push(Zone.new(top = high[k], bottom = low[k], dir = 1, bornBar = bar_index - k, createdBar = bar_index, qual = 0.5, tookLiq = true))
            break
// step 9: when obSwingH := ph, also raidH := false (mirror for lows)
```
History references on built-in series inside an `if` scope are already used this way in step 8 (1672-1680).

**Value.** Breakers that match the ICT definition, and more of them, with honest calibration.

**Risk.** More array candidates. ICTPD-1's prior and the pool cap (`poolMax`, 1951) contain this. `obTrk` is capped at 30 (1749).

**Effort:** S (mitigation block: M).

### ICTPD-3 (P2) · Fill-ladder probabilities (CE / full) for array targets, plus ledger depth stats

**Why.** Traders size targets and partials at the near edge, CE or full fill. Section 2.2 shows the ladder is large on higher TFs (4H, 24 h: touch 71.8% → CE 62.3% → full 54.2%). The engine already has the empirical surface needed.

**Algorithm.**
- In LIVE READOUTS (2066-2067), for an array target compute `dCE = side == 1 ? price - close : close - price` (clamped ≥ 0; `price` is the original mid) and `dFull = side == 1 ? oTop - close : close - oBot`. Then `potCE = f_potModel(dCE, side, mu)` and `potFull = f_potModel(dFull, side, mu)`. Both are O(1).
- Show "CE 61% · FULL 52%" in the Clean label tooltip (2206) and on a Terminal HUD line.
- Ledger: keep array trials that hit the near edge in a light list until `bar0 + H`. Track whether they reach CE and the far edge, then report "tap→CE x% → FULL y%" in the Full view. This needs Trial fields `ce`, `far`, flags `ceHit`, `fullHit`, and the arrays `ladN`/`ladCE`/`ladFull`.

**Value.** Realistic partial-target planning. It also reveals the momentum effect: large zones rarely fill fully.

**Measurable.** The model's CE/FULL probability vs the observed ladder (calibration).

**Risk.** Minimal. Extra lines in the tooltip only; the Clean look is unchanged.

**Effort:** S.

### ICTPD-4 (P2) · IRL ↔ ERL delivery phase, with arrays as waypoints

**Why.** This is ICT's central rule for which liquidity comes next (1.12). The engine models the direction after raids but not the target *type*. The evidence is weak (doctrine only), but the effect is directly measurable by the ledger, and it is the most ICT-specific selection logic missing.

**Algorithm.** State `irlSide`, `irlBar`, `erlSide`, `erlBar`, plus a pending array.
1. **ERL event** (step 3, line 1580). A liquidity level is hit with `ext = lv.src >= 1 or lv.eqCount > 0 or lv.stack > 0`.
   - If `evt == -lv.side` (the raid rejects): `irlSide := -lv.side`, `erlSide := 0`.
   - If `evt == lv.side` (it holds): `erlSide := lv.side`, `irlSide := 0`.
2. **IRL event.** An array level is hit: store `pendSide = lv.side`, `pendNear`, `pendFar`, `pendBar`.
   - On later bars (≤ 6), if `close` moves ≥ 0.5 ATR away from `pendNear` in direction `-pendSide` without a close beyond `pendFar`: it was respected and rebalanced, so set `erlSide := -pendSide`, `irlSide := 0`.
   - If it closes beyond `pendFar`: clear the pending array (disrespect).
3. **Expiry**: `bar_index - xxxBar > phaseLen` (default `2*H`) sets the side to 0.
4. **Scoring** (step 17, before `evaluate`):
   - arrays on `irlSide`: `mult *= phB` (1.15); liquidity on `irlSide`: `mult *= 0.92`;
   - liquidity on `erlSide`: `mult *= phB`; arrays on `erlSide`: `mult *= 0.90` (waypoints).

   Once the ledger has ≥ 20 trials per phase, `phB` is replaced by `f_ctxMult(phase cell)`.
5. **Waypoint UX**: when the active target is an array, the tooltip names the best liquidity pool beyond it on the same side, "then → BSL @ x (PoT y%)".
6. **Ledger**: `Trial.ph` ∈ {0 none, 1 IRL-phase array, 2 ERL-phase pool}. The Full view row shows "PHASE IRL k/n vs exp, ERL k/n vs exp".

**Pine.** A handful of `var int`/`var float` values; all logic in the confirmed-bar block; O(pool) loops that already exist.

**Value.** Fewer cases of "DOL is a far pool while price is obviously rotating into the gap below", and the reverse.

**Risk.** Weak evidence. It can amplify a wrong read after breakouts (the failure mode "a genuine breakout ... keeps going"). That is mitigated by requiring rejection for IRL and by the bounded multipliers.

**Effort:** M.

### ICTPD-5 (P2) · IPDA 20/40/60-day extremes as external-range liquidity (no new request call)

**Why.** These are ICT's canonical HTF external range. They are also the levels where Donchian/Turtle breakout stops and entries cluster (mechanism: Osler 2003 stop clustering plus wide use of 20/55-day rules). PDH/PWH and pivots do not cover them.

**Algorithm.**
- Ring buffer of the last 60 *completed* days from the existing `f_rangeTrack(timeframe.change("D"))` outputs (`pdH`, `pdHB`, `pdL`, `pdLB`, line 945). Exact anchor bars come for free.
- On `pdNew`, for N ∈ {20, 40, 60} with buffer size ≥ N: compute max high / min low and their bars, then `f_pushExt` them into the registry with new `src` codes 8/9/10.
  - Tiers 0.84 / 0.88 / 0.95.
  - `hlMult` = sqrt(N·86400/chartS).
  - Names "20D H", "40D L", and so on.
  - Duplicate prices are merged, and the higher tier wins (`f_pushExt` 1211-1225).
- Enabled only when `timeframe.in_seconds() <= 86400`.

**Pine sketch.**
```pine
var array<float> dH  = array.new<float>()
var array<int>   dHB = array.new<int>()
var array<float> dL  = array.new<float>()
var array<int>   dLB = array.new<int>()
bool dayOK = timeframe.in_seconds() <= 86400
if pdNew and dayOK          // place right after line 961
    dH.push(pdH)
    dHB.push(pdHB)
    dL.push(pdL)
    dLB.push(pdLB)
    if dH.size() > 60
        dH.shift()
        dHB.shift()
        dL.shift()
        dLB.shift()
f_nDay(int n, bool isHigh) =>
    float px = na
    int   b  = na
    int   s  = dH.size()
    for i = s - n to s - 1
        float v = isHigh ? dH.get(i) : dL.get(i)
        if na(px) or (isHigh ? v > px : v < px)
            px := v
            b  := isHigh ? dHB.get(i) : dLB.get(i)
    [px, b]
// step 10 (after 1799)
if useIPDA and pdNew and dayOK
    for n in array.from(20, 40, 60)
        if dH.size() >= n
            [hx, hb] = f_nDay(n, true)
            [lx, lb] = f_nDay(n, false)
            int   sN  = n == 20 ? 8 : n == 40 ? 9 : 10
            float hmN = math.sqrt(math.max(1.0, n * 86400.0 / chartS))
            regNew := f_pushExt(extReg, hx, true, sN, hb, (hx - lx) / atr * 0.5, hmN) or regNew
            regNew := f_pushExt(extReg, lx, false, sN, lb, (hx - lx) / atr * 0.5, hmN) or regNew
// f_tierW: 8 => 0.84, 9 => 0.88, 10 => 0.95 ; f_levelName: "20D H" / "40D H" / "60D H" (and L)
```

**Value.** Canonical swing/HTF targets with ICT names; better HTF objectives (`showObj`).

**Measurable.** The ext-liq family edge (or a new src-level breakdown).

**Risk.** Registry crowding (cap 60, 1813). Low-TF charts with fewer than 20 days of history get nothing (graceful). Sizing the buffer from 5000 bars is fine.

**Effort:** M.

### ICTPD-6 (P2) · Opening gaps (NWOG / NDOG / RTH opening gap) as imbalance targets

**Why.** These are widely watched ICT references, and their base rates are documented and strongly size-dependent (2.3). They cost no request calls.

**Algorithm.**
- **Break detection**: `sesBrk = timeframe.isintraday and time - time[1] > 1.5 * timeframe.in_seconds() * 1000`. This catches the CME 17:00 to 18:00 halt, weekends, and RTH-only overnight gaps; crypto has none.
- **Gap**: `gHi = max(open, close[1])`, `gLo = min(open, close[1])`. Require `gHi - gLo >= max(gapMin·ATR, 2·mintick)`. The weekly flag is `timeframe.change("W")`.
- **Level** (on the confirmed break bar; the target zone is the *far half*, so the near edge is the CE):
  - gap up (`open > close[1]`, price above): kind 9 (side −1), zone `[gLo, CE]`, `price = CE`, created only if `close > CE`;
  - gap down: kind 8 (side +1), zone `[CE, gHi]`, created only if `close < CE`.
- `src` = 7 for weekly (label "NWOG"), 6 for daily (label "NDOG").
- Retention: last 5 weekly and last 3 daily. Track their ids in two small `var array<int>`; when over capacity, remove the oldest from the pool.
- Apply ICTPD-1's `sz` penalty: a large gap is a continuation signal (SPY 1%+ up-gaps fill same-day only 26%, with a positive open-to-close drift).
- Code touch points:
  - `f_newLevel` side map (1085): add kind 8 → +1;
  - `grp()` (636): kinds 8/9 → family 2 ("imbalances") to avoid resizing the stats arrays;
  - `f_levelName`/`f_shortName`: 8/9 → "NWOG"/"NDOG";
  - non-active delivery: treat gaps as delivered on touch of CE (their zone is already the far half).

**Value.** Targets ICT traders actually watch on index futures, with size-aware probabilities.

**Measurable.** Family-2 edge, or split by `src`.

**Risk.** Feed quirks (missing bars on FX rollover create spurious "breaks"; the size gate handles them). On daily charts weekend gaps appear only via weekly logic (keep `isintraday`).

**Effort:** M.

### ICTPD-7 (P3) · Adaptive premium/discount side prior (learned, not hard-coded)

**Why.** ICT says "longs only in discount, targets in premium". The strong literature (George and Hwang 2004) points the other way at long horizons, and there are no intraday statistics. So learn it from the chart.

**Algorithm.**
- Zone = quartile of `close` within the IPDA 20-day range (from ICTPD-5). Fall back to the HTF structure range `htfRH`/`htfRL` (923).
- Cell = (target side +1/−1) × (zone 0..3), 8 cells.
- `Trial.pz` stored at open. In step 17: `lv.mult *= f_ctxMult(pzN, pzK, pzE, cell(lv.side, zoneNow), 0.85, 1.15, 40)`.
- Optional static prior input "Premium/Discount Prior" (default 0 = off): when > 0, buy-side targets from discount and sell-side targets from premium get ×(1 + w).
- Terminal: add the "IPDA20 PREM 72%" row. Full view: "BUY-side from DISC k/n vs exp; from PREM k/n vs exp".

**Value.** Tells the user, with evidence from their own chart, whether premium/discount helps, and only then uses it.

**Risk.** Slow learning (8 cells). The bounds keep the impact small.

**Effort:** M.

### ICTPD-8 (P3) · iFVG retest honesty stats against a race baseline

**Why.** The commercial spec sells "iFVG continuation", but a controlled S&P daily test found iFVG retests hold no better than random (38% vs 38%, 47% vs 47%). Users should see this measured on their own chart.

**Algorithm.**
- On the **first** retest of an active iFVG (bearish iFVG: `high >= z.bottom`), open a light record: `tgt = touch - x·ATR` (x = 1.0), `fail = close > z.top`, expiry H.
- Baseline `p0 = f_race(x·atr, z.top - touch, potSig, -potMu)` (the existing two-barrier first passage, line 447). That is the probability that a *random* level with the same geometry "holds".
- Accumulate n, k, Σp0, and show "iFVG HOLD k/n (exp p0)" in the Full view.
- Needs Zone field `retested`, plus a small type or a parallel array.

**Value.** An honest read of a feature that is heavily marketed.

**Risk.** Close-vs-touch mismatch in the race approximation (documented).

**Effort:** S to M.

### ICTPD-9 (P3) · Rejection-block metadata on liquidity targets: near-miss statistic and target band

**Why.** RB practice trims targets to the body extreme of the old high/low. The engine's strict "through the wick" sweep rule is a deliberate decision and stays. This proposal *measures* how often price reaches the wick zone but fails to sweep, which informs the trader's take-profit placement.

**Algorithm.**
- Level field `body` set at chart-pivot creation: BSL `math.max(open[pivLen], close[pivLen])` (1762); SSL `math.min(...)` (1774). It is `na` for external pools.
- Trial field `rb` and flag `rbHit` (set in `f_step` when `high >= rb` for a buy-side pool).
- At booking, among expired misses report "near-miss in wick zone x%". Optionally draw a thin RB band inside the target zone in the Terminal style.

**Value.** Realistic expectations for take-profits at old highs/lows.

**Risk.** None to selection.

**Effort:** S.

### ICTPD-10 (P3) · Liquidity-void merge of consecutive same-direction FVGs

**Why.** A displacement leg often prints 2 to 4 adjacent FVGs. The engine creates a level for each, which makes duplicate candidates, possible flicker between adjacent zones, and a CE that belongs to one sub-gap only. ICT treats the leg as one liquidity void. This is the `join_consecutive` convention of the `smartmoneyconcepts` Python library.

**Algorithm.** In step 13 (1868-1886), keep `lastBuId`/`lastBuBar` (and the bearish pair). If a new bullish FVG forms on `bar_index == lastBuBar + 1` and that level is still in `pool` with `fill == 0`, extend it instead of creating a new one:
- `top := max(top, low)`, `oTop := top`, `price := (oTop + oBot) / 2`;
- `qual := max(qual, qU)`, `sz` recomputed.

Leave `fvgTrk` (iFVG tracking) per-gap.

**Value.** Cleaner pool and a stable target, with the void's true CE.

**Risk.** A merged void's CE sits deeper, so non-active delivery at CE takes longer (intended).

**Effort:** S.

---

## 5. Notes for implementers

- **Non-repainting**: every proposal runs inside the `barstate.isconfirmed` engine block, except the ICTPD-3 readouts, which are live like PoT by design. No proposal adds a `request.*` call. ICTPD-5 reuses `f_rangeTrack` on the chart TF; the engine currently has 6 unique requests (limit 40).
- **Declaration order**: put the ICTPD-5 buffer and `f_nDay` after line 961 (after `pdNew` exists) and before the engine block. Put `f_ctxMult` among the STATE HELPERS (after 1382). New Level/Trial fields go in the TYPES block (317-395) with defaults.
- **Ledger compatibility**: new families can map into existing `grp` 2/3 so the stats arrays (`stN` etc., size 5 with index 4 = ALL) do not need resizing. Context stats live in separate arrays.
- **Clean look**: only tooltip text changes (ICTPD-3, ICTPD-4 waypoint) plus new target codes (NWOG, NDOG, 20D H, BEMB). Everything else is Terminal or Full view.

## 6. Sources

**Controlled quantitative studies**
- Nordman Algorithms (2026). Do Fair Value Gaps Work? We Tested 38,114 Returns to FVGs. https://www.nordman-algorithms.com/blog/do-fair-value-gaps-work/
- Nordman Algorithms (2026). Do Order Blocks Work? 10,986 Touches Tested Against Random Levels. https://www.nordman-algorithms.com/blog/do-order-blocks-work/
- Nordman Algorithms (2026). ICT Displacement and the Market Structure Shift: 15,817 Signals. https://www.nordman-algorithms.com/blog/ict-displacement-market-structure-shift/
- Barot, D. (2026). Fair Value Gaps Work: Until You Try to Trade Them. SSRN 7148099. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7148099
- Trader Markus (2026). Fair value gap (FVG): A test on 26 years of S&P 500 data. https://tradermarkus.com/fair-value-gap/
- MarketTrace (2026). Fair value gaps: we measured 4,827 of them on Bitcoin. https://markettrace.ai/blog/fair-value-gap
- Taylor, V. (2026). Evaluating the Predictive Validity of ICT's AMD Model on CME E-Mini NASDAQ-100 Futures. arXiv 2610.35887.

**Gap-fill base rates and other statistics**
- Gap analysis, SPY/QQQ fill rates by gap size. https://www.thetrading.tools/gap-analysis
- QuantifiedStrategies, gap trading strategies. https://quantifiedstrategies.substack.com/p/gap-trading-strategies
- Finabase, gap trading. https://finabase.io/learn/trading/gap-trading
- Edgeful, FVG guide (YM statistics). https://www.edgeful.com/blog/posts/fair-value-gap-best-practices-guide
- Edgeful, ES futures strategies (gap fill). https://www.edgeful.com/blog/posts/es-futures-trading-strategies
- FXNX, FVG fill rate (weak; methodology undisclosed). https://fxnx.com/en/blog/fair-value-gap-fill-rate-measured-across-thousands-gaps
- Tradeify, Donchian 20-session breakout test (ES/NQ). https://tradeify.co/education/donchian-channels

**Peer-reviewed literature**
- Osler, C. (2000). Support for Resistance: Technical Analysis and Intraday Exchange Rates. FRBNY Economic Policy Review 6(2). https://www.newyorkfed.org/medialibrary/media/research/epr/00v06n2/0007osle.html
- Osler, C. (2003). Currency orders and exchange-rate dynamics: explaining the success of technical analysis. J. Finance. Working-paper copy: https://www.econstor.eu/bitstream/10419/60582/1/331762730.pdf
- George, T. and Hwang, C.-Y. (2004). The 52-Week High and Momentum Investing. J. Finance 59(5). https://www.bauer.uh.edu/tgeorge/papers/gh4-paper.pdf

**Definitions (LuxAlgo Library concept pages, free with attribution)**
- https://www.luxalgo.com/library/concept/pd-arrays/
- https://www.luxalgo.com/library/concept/premium-and-discount/
- https://www.luxalgo.com/library/concept/bullish-bearish-order-block/
- https://www.luxalgo.com/library/concept/order-block-anatomy-and-refinement/
- https://www.luxalgo.com/library/concept/breaker-block/
- https://www.luxalgo.com/library/concept/mitigation-block/
- https://www.luxalgo.com/library/concept/rejection-block/
- https://www.luxalgo.com/library/concept/propulsion-block/
- https://www.luxalgo.com/library/concept/fvg-behavior-rules/
- https://www.luxalgo.com/library/concept/consequent-encroachment/
- https://www.luxalgo.com/library/concept/inversion-fvg/
- https://www.luxalgo.com/library/concept/volume-imbalance/
- https://www.luxalgo.com/library/concept/balanced-price-range/
- https://www.luxalgo.com/library/concept/implied-fvg/
- https://www.luxalgo.com/library/concept/new-week-opening-gap/
- https://www.luxalgo.com/library/concept/new-day-opening-gap/
- https://www.luxalgo.com/library/concept/internal-vs-external-range-liquidity/
- https://www.luxalgo.com/library/concept/ipda-and-price-delivery-theory/
- https://www.luxalgo.com/library/concept/draw-on-liquidity/
- https://www.luxalgo.com/library/concept/low-resistance-vs-high-resistance-liquidity-runs/

**ICT original wording (mentorship transcriptions)**
- ICT summary notes (breaker, rejection block, vacuum block, liquidity void). https://www.studocu.com/en-us/document/the-american-college-of-financial-services/techniques-for-exploring-personal-markets/ict-summary-ict-trading/46530291
- ICT's Institutional Order Block Theory guide (order block, breaker). https://www.studocu.com/in/document/mats-university/business-tax-procedure-and-management/507266371-institutional-trading/57868256
- ICT PD Array matrix article. https://innercircletrader.net/tutorials/ict-pd-array-key-to-trade-execution/

**Open-source conventions**
- joshyattridge/smart-money-concepts (Python): `fvg(join_consecutive)`, `MitigatedIndex`, `ob`, `bos_choch`. https://github.com/joshyattridge/smart-money-concepts
