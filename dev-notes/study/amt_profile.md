# Auction Market Theory, Market Profile and Volume Profile: study for DOL Engine v2

Scope: every AMT / Market Profile (TPO) / Volume Profile concept that bears on WHERE price goes next (which liquidity is taken), WHEN, and HOW LIKELY. Engine studied: `brief/baseline_v2.pine` (line numbers refer to it; identical to `/home/user/m/indicators/dol_engine.pine`).

Companion studies, referenced and not repeated here:
- `study/ict_liq.md`: ICT-1 candidate ledger. Section 4 plugs AMT features into it.
- `study/ict_time.md`: G2 / TIME-1, the PoT and baseline time-of-day bias. This study confirms it independently, see E-OWN-0.
- `study/smc_impl.md`: SMC-7, LVN troughs, and E8, the naked-POC folklore numbers.
- `study/competitors.md`: LVN distance limit and LVN colour contrast.

Reproducibility:
- Scripts: `study/amt_tools/` (`amtlib.py`, `s1_npoc.py` … `s7_bounce.py`). Outputs: `out_*.txt`.
- Data: public CME continuous OHLCV CSVs (github.com/axb0306/cme-futures-ohlc) in `study/amt_data/cme/`.
  - 1-hour bars, 2025-03-21 → 2026-04-15, for ES, NQ, RTY and YM; CL from 2025-06-01.
  - 1-minute bars, 2026-01-20 → 2026-04-15, for the same five.
  - GC was excluded: its 1h file interleaves two contract months.

---

## 0. Executive summary (read this first)

1. **Volume-profile levels are reached at the random-level rate.** Prior-session POC, VAH, VAL, older naked POCs, IB extremes and overnight extremes all hit at the rate of a random price at the same ATR distance, once the baseline is matched on clock time.
   - Prior-session POC within 5 sessions: 83.6% hit vs 84.7% random.
   - Naked POCs older than one session: 38.7% vs 43.4%.
   - The popular "84-87% of naked POCs get revisited" figure is true but is a **distance artifact**. An independent 589-session test agrees: POC revisit is 77-79% with a median of 1 session, and "the magnet story is not proven".
   - **Do not add naked POCs / VA edges as DOL level sources.**
2. **The engine's volume-profile path cost points the wrong way** (1945-1947).
   - Targets behind a *thin* path (vf < 0.6, the engine gives ×1.10) are hit **3.5-4.6 pp *less*** than random. This holds at composite depths 48/120/240 h (z_clu ≈ -3 to -4.7) and on 4 of 5 instruments.
   - Targets *beyond the composite's price range* are hit **2.5-3.3 pp less** (z_clu -3.2 to -4.6). The engine *boosts* them, because `f_row` clamps them onto the thin tail rows.
   - At the 1-hour scale price does **not** move faster through LVNs. At the 15-minute scale it is about 7-9% more volatile there.
   - LVN troughs act as mild **rejection barriers**: bounce +3.2 pp vs random (z 2.9).
3. **AMT bias rules carry no information beyond distance** (logit LR tests):
   - value migration (2-day VA relationship): χ²=1.05, df 2;
   - close vs POC: χ²=0.17;
   - close vs VA: χ²=5.6, df 2, and its sign is mean-reverting, not continuation.
   - The 80% rule: our test gives 61.9% vs a 54.0% matched baseline (n=42, z 1.2). The independent test gives 25-28% vs a 27-29% base rate.
4. **"Acceptance outside value" does not mean continuation at a 30-hour horizon.** After ≥3 hourly closes beyond the composite value area, targets further from value are hit 3.8-6.0 pp *less* than random in 5 of 6 configurations. This is a small exhaustion effect.
5. **Poor (flat) extremes are only weakly more likely to be repaired:**
   - +1.6 pp overall (z 1.1);
   - +5.7 pp at 2-4 ATR (z 1.9);
   - monotonic in the number of flat touches;
   - TPO version +1.4 to +5.8 pp, not significant (n.s.).
   - Single prints are filled *less* often than random (53% vs 64%, n=98).
6. **Measurement trap: an unmatched baseline manufactures spurious edges.** The engine's PoT surface (1059-1062, 1284-1300) and the ledger's `pBase` (1314-1322) are pooled over all hours.
   - Measured from session ends without clock matching, every level family showed a *spurious* -6 to -11 pp "edge".
   - Matching the baseline on clock hour removed it.
   - This independently confirms `ict_time.md` G2 / TIME-1. The ledger's EDGE verdict inherits the bias.

Net: AMT's value to this engine is mostly **negative knowledge** (what *not* to add) plus one concrete bug fix (the path-cost sign and the out-of-range clamp). The rest are small, symbol-dependent effects (≤ 5 pp). These belong in the **learned candidate ledger** (ICT-1) with neutral priors, not in hard-coded multipliers.

---

## 1. Concepts (definitions and parameters)

### 1.1 Auction Market Theory (AMT): balance, imbalance, acceptance, rejection
- **Premise (Steidlmayer, CBOT 1985; Dalton, *Mind Over Markets* 1990).**
  - The market is a two-way auction that facilitates trade.
  - **Balance**: two-sided rotation around a fair price. The profile is bell-shaped ("D").
  - **Imbalance**: one-sided, directional search for new value. The profile is elongated, with thin areas.
- **Acceptance** = time and volume build at new prices. Operational definitions:
  - ≥ 2 consecutive 30-minute TPO periods beyond a reference; or
  - ≥ 1 hour of trade there; or
  - a developing POC that migrates there.
- **Rejection** = prices visited briefly: tails, single prints, LVNs.
- **Initiative vs responsive activity.**
  - Initiative buying happens above value; responsive buying happens below value.
  - Responsive activity at the edges of value keeps balance. Initiative activity beyond value starts an imbalance.
- **OTF** (other-timeframe participants) drive imbalance. Day timeframe participants rotate within balance.
- **DOL role (theory).**
  - In balance: targets inside value (rotation to the opposite edge) are favoured.
  - In imbalance with acceptance: targets beyond value (continuation) are favoured.
  - After rejection: price returns to value.
- **Measured** (section 2): only weak, mixed support. Rotation inside value is slightly favoured: POC from inside VA +2.1 pp, z 2.0. Continuation after acceptance is **not** favoured; it is slightly *disfavoured*.

### 1.2 TPO profile (Market Profile)
- **Session.** For index futures: RTH 09:30-16:00 ET, 13 periods of 30 minutes, lettered A-M.
- **Row (bracket) size.**
  - Each period prints its letter on every row its high-low range touched.
  - Common choices: ES 1 tick to 2.5 pts, NQ 10 pts.
  - TradingView "Auto" targets about 80 rows over the last 300 bars.
- **TPO count per row** = number of periods that traded there.
- **Parameters that move every derived level:** session window, period length, row size, VA %.
  - Switching VA 70%→80% moved the ES VAH on 31 of 49 sessions.
  - Changing the tie rule moved it on 10 of 49 (tradeify).

### 1.3 Volume profile
- **Definition.** Traded volume per price row.
- **Approximations from OHLCV:**
  - spread each bar's volume uniformly over its range;
  - TradingView: built from lower-TF bars;
  - this engine (1384-1414): 60% of each hourly bar's volume flat over its range and 40% over its body, then 1-2-1 smoothing.
- **Composite profile.** Several sessions aggregated, to reveal multi-day balance areas. Variants:
  - fixed session composites (daily, weekly);
  - rolling N-bar composites, as in the engine: the last `lvnHours` = 120 hourly bars, 48 rows (204-205, 1900-1909).

### 1.4 Point of Control (POC)
- **Definition.** The row with the most TPOs (TPO-POC) or the most volume (VPOC).
- **Ties:**
  - CQG: the row closest to the range midpoint;
  - TradingView: the row closest to the POC rule (for VA expansion), then the higher row.
- **Developing POC (dPOC).** The POC of the session so far. Its migration shows where value is moving.

### 1.5 Value Area (VAH / VAL)
- **Definition.** The band around the POC holding ~70% (68-70%) of TPOs or volume. It is roughly ±1 standard deviation under a normal assumption (CBOT).
- **Algorithm (one-row expansion; TradingView / most platforms):**
  1. Start at the POC row; total T; target 0.70·T.
  2. Compare the next row above with the next row below and add the larger.
  3. Tie: the row closer to the POC, then the higher row. Some tutorials use "upper wins".
  4. Repeat until the accumulated amount ≥ target.
  5. VAH = top of the highest included row; VAL = bottom of the lowest included row.
- **CBOT / Sierra "two rows at a time" variant.** Compare the *sums* of the next two rows above and below, and add the larger pair. `amtlib.value_area()` uses this variant.
- **Edge cases:**
  - a POC at the profile edge expands on one side only;
  - a flat profile defaults to the higher side;
  - VA % below 50% or above 90% is unusual.

### 1.6 Two-day value relationships (value migration)
Compare today's VA [VAL₁, VAH₁] with yesterday's [VAL₀, VAH₀] (Dalton):

| Relationship | Rule | Dalton's reading |
|---|---|---|
| Higher | VAL₁ > VAH₀ | bullish |
| Overlapping-higher | VAH₁ > VAH₀, VAL₁ ≥ VAL₀, overlap | moderately bullish |
| Inside | VAH₁ ≤ VAH₀, VAL₁ ≥ VAL₀ | balance / breakout pending |
| Outside | VAH₁ > VAH₀, VAL₁ < VAL₀ | balance |
| Overlapping-lower | VAL₁ < VAL₀, VAH₁ ≤ VAH₀, overlap | moderately bearish |
| Lower | VAH₁ < VAL₀ | bearish |

- **Developing value migration** applies the same idea intraday, using the dVAH / dVAL / dPOC drift.

### 1.7 Naked (virgin) POC
- **Definition.** The POC of a *completed* session that no later bar's range has touched since the session ended.
- **Retirement.** Usually the first touch (bar high ≥ POC ≥ bar low). Some traders require a trade-through.
- **Claim.** "Magnets"; "84-87% revisited within 5 days".
- **Proper estimator.** A survival / life-table model with censoring: fill hazard by age, as in the open-source "NPOC Magnetism" script. It also needs a **distance-matched baseline**, which none of the published claims use.

### 1.8 HVN / LVN (high- and low-volume nodes)
- **HVN** = a local maximum (peak) of the profile.
- **LVN** = a local minimum (trough), typically *between* two HVNs. It separates two balance areas.
- **Detection:**
  1. Trough / peak against N neighbouring rows on *each* side (LuxAlgo node detection), plus a prominence (depth) test.
  2. Absolute threshold vs peak (the engine: rows < 0.30 × peak form an LVN run, tails excluded; 2250-2269). This marks broad thin shoulders, not true troughs (SMC-7).
  3. Swing-anchored profiles (LuxAlgo "VP voids", 21% threshold).
- **Claims.** "Price moves fast through LVNs and stalls at HVNs"; "LVNs are rejection points / edges of balance"; "HVNs are acceptance and magnets".
- **Measured** (sections 2.3 and 2.5):
  - **Rejection at LVN:** mildly true.
  - **Faster through LVN:** true only at the 15-minute scale (+7-9% range), not at 1 hour.
  - **HVN stalls:** not true.
  - **HVN magnet:** not robust.

### 1.9 Single prints, tails (excess)
- **TPO single print.** A row printed by exactly one period.
- **Mid-profile single prints.** ≥ 2 contiguous single rows, *not* at an extreme, sandwiched by multi-TPO rows (tradingstats' definition; zones 2-25% of the day's range).
  - Reading: an aggressive one-sided move (initiative). The "unfinished business" claim says they get filled later.
- **Tail / excess.** ≥ 2 single-print rows at the session high or low (Dalton: "excess", the auction ended properly by aggressive opposite activity).
  - Reading: the extreme is "complete" and unlikely to be revisited soon.
- **Edge cases:**
  - single prints formed in the final period;
  - single prints spanning an RTH/ETH gap;
  - row size dominates the count: at 80 rows per range almost every extreme has a 2-row tail; at 25 rows, far fewer.

### 1.10 Poor highs / poor lows (unfinished auction)
- **TPO definition.** ≥ 2 TPOs (periods) at the extreme row, i.e. a flat top or bottom with no tail.
  - Reading: the auction stopped because one side was exhausted, not rejected. "Should be repaired": traded through later.
- **Variants:**
  - "weak high/low": ≥ 2 TPOs within 1-2 ticks;
  - "unsecured" extremes;
  - an extreme formed in the closing period.
- **Engine-feasible proxy (bars, no TPO).** A session extreme with ≥ 2 separated bars whose high (low) lies within `tol·ATR` of it. **This is an equal-high at the extreme**, so the engine's EQH/EQL logic is the natural home.

### 1.11 Initial Balance (IB) and range extension; day types
- **IB** = range of the first hour of RTH (periods A+B, 09:30-10:30 ET). **Range extension (RE)** = trade beyond the IB.
- **Extension levels:** IB high/low ± k·IB, with k ∈ {0.5, 1, 1.5, 2, 3}.
- **Dalton day types:**

| Type | Range vs IB |
|---|---|
| Normal | ~85% of the range in the IB |
| Normal variation | RE up to ~2×IB |
| Trend | RE > 2×IB, close near the extreme |
| Double-distribution trend | two value areas separated by single prints |
| Neutral (centre / extreme) | RE on both sides; close in the centre or at an extreme |
| Non-trend | small IB, no RE |

### 1.12 Open location and open types (Dalton)
**Open location** relative to yesterday's value and range:
1. inside value;
2. outside value but inside the range;
3. outside the range (imbalance; the gap must find acceptance or get rejected).

**Open types**, ordered by conviction. These are proxies for code. Each label needs ~30 minutes to firm up.

| Open type | Algorithmic proxy | Practitioner claim |
|---|---|---|
| Open-Drive (OD) | Price leaves the open immediately and never trades back through it during period A. Open within the bottom/top ~10% of the A range; A range ≥ k·ATR(30-min). | Highest conviction; "most reliable extreme"; often a trend day |
| Open-Test-Drive (OTD) | An early probe beyond a reference (prior VAH/VAL, overnight high/low, prior high/low) fails within the first 5-15 minutes. Price then drives back through the open the other way. | The probe extreme holds; second-most reliable |
| Open-Rejection-Reverse (ORR) | An initial directional move is met by opposite activity strong enough to return price *through* the opening range in period A/B. | Initial extreme holds only "about half the time" |
| Open-Auction (in / out of range) | Rotation around the open; both sides traded repeatedly; open near the middle of the A range. | Low conviction; early extremes unlikely to hold; rotational day (in range), more potential for direction (out of range) |

No quantitative study of open-type outcomes was found (searched). The claims are practitioner consensus.

### 1.13 The 80% rule
- **Rule.** Price opens outside the prior session's VA (or moves outside), then trades back inside and "holds" for two consecutive 30-minute periods. It then has "80%" odds of traversing to the opposite VA edge.
- **Variants:**
  - an early trigger on period-1 close inside plus period-2 open inside;
  - "acceptance" judged by time and volume instead of brackets.
- Origin: Dalton Capital "Profile Reports" (1987-91).

### 1.14 Overnight inventory / overnight high-low
- Overnight (ETH) high/low as references for RTH.
- Overnight inventory "net long/short": the position of the RTH open within the ON range. It is expected to correct early in RTH.
- In this engine, Asia/London session highs and lows already cover the ON extremes (948-950).

### 1.15 Profile shapes
- **P-shape:** short covering / buying, POC high, thin tail below.
- **b-shape:** long liquidation, the mirror of P.
- **D-shape:** balance.
- **Double distribution:** two separate value areas.
- These describe the past; there is no predictive evidence (not tested).

---

## 2. Evidence (numbers and sources)

Evidence grades:
- **strong**: peer-reviewed or large, replicated quantitative study;
- **moderate**: published or reproducible statistics with a proper baseline;
- **weak**: statistics without a baseline, or small samples;
- **none**: folklore.

### 2.1 External evidence

| ID | Claim | Source | Numbers | Grade |
|---|---|---|---|---|
| X1 | Prior POC "magnet" | tradeify 589-session ES/NQ test (hourly, 2024-26) | Prior POC traded again within 5 sessions: ES 77.05%, NQ 78.60%; **median 1 session**. VA did not overlap the prior VA on 41.7% / 42.0% of sessions. "The magnet story is not proven by this number." | moderate (vs folklore) |
| X2 | Naked POCs get revisited | TradingView author post "Naked POCs Explained" (via `smc_impl.md` E8) | Gold 84%, ES 87%, BTC 87% within 5 days (n ≈ 962-1,034). By distance: < 0.5 ADR 82%, 0.5-1 ADR 59%, 1-2 ADR 32%. No baseline. | weak |
| X3 | 80% rule | tradeify 589-session test | Confirmed setups reached the far edge 25.00% (ES, 9/36) and 28.13% (NQ, 9/32). Base rate (any outside open): 28.65% / 27.17%. Rerun 27.27% vs 29.22%. 30-minute version: ES 2/5, NQ 0/8. | moderate (vs folklore) |
| X4 | 80% rule | Elite Trader thread (practitioner) | "It isn't anywhere close to 80%." | weak |
| X5 | IB breaks almost every day | tradingstats.net, ES/NQ 2015-2025 (2,686 / 2,833 days) | ≥1 IB break: 97.8% / 96.2%. Median extension 63.6% / 55.6% of IB. ES: 52% reach +25%, 18.8% reach 100%, 4.4% reach 200%. Narrow IB (< 0.5 ATR): 98.7% break, median ext 74.8%. Extreme IB (> 1.5 ATR): 66.7-76.9% break. C-period close beyond IB → 45.5% reach 100% (vs 18.8%). First break failed 34%. > 80% of first breaks by 11:30. | moderate (descriptive) |
| X6 | IB breaks; session range vs IB | tradeify | IB broken 93.55% / 89.81%; both ways 16.6% / 11.5%. Median session range 1.52× / 1.39× IB. ≥ 3× IB: 4.9% / 3.1%. | moderate (descriptive) |
| X7 | Single prints get filled | tradingstats.net, NQ/ES/YM/RTY 2014-2026, 3,847 zones | Form on 37-53% of days. Full reversal of the single-print day only 6-10%. Fill D+1 ~32%, D+5 63-67%, D+10 74-76%; never within 30 days 14-17%. Small zones fill faster (D+5 64-70%). After D+7 unfilled, P(ever) < 50%. No random-level baseline. | weak for "magnet"; moderate for "reversal is rare" |
| X8 | Shallow extremes fade, deep extremes hold | tradingstats.net, 2019-2026, ~14,300 extremes per market | 58-59% of running extremes retrace 50%. Shallow (≈ 0.25 ATR) ~85%; > 1 ATR ~20%. Lows fade more (NQ 61% vs 55%). Walk-forward AUC ≈ 0.82. | moderate |
| X9 | Poor highs/lows get repaired | Searches; The Right Trader states "no reliable published figure" | No statistic exists | none |
| X10 | Published S/R levels interrupt intraday trends | Osler 2000, FRBNY *EPR* 6(2) | Compared with 10,000 arbitrary level sets: significant predictive power for trend *interruptions*, lasting ≥ 5 business days. Firms could not rank levels by strength. | strong (for "levels stop trends", not for "levels attract price") |
| X11 | S/R coincide with order-book depth | Kavajecz & Odders-White 2004, *RFS* 17(4) | S/R levels line up with peaks in limit-order-book depth (the HVN analogue: depth, not reach) | strong (mechanism) |
| X12 | Bounce probability rises with prior bounces, and decays | Chung & Bellotti 2021, arXiv:2101.07410 | Bounce probability rises with the number of prior bounces (permutation-test significant). It decays with the lag window: EURUSD 1-bounce levels reach 0.5 at a ~350-minute window, 4-bounce levels at ~900 minutes. | moderate |
| X13 | Round numbers / deep queues | Jung & Lee 2026, arXiv:2610.34787 | Round levels attract more liquidity but do **not** show longer depth-adjusted durations | moderate |
| X14 | Technical rules in futures after data-snooping control | Park & Irwin (farmdoc) | Generally not profitable in US futures, 1985-2004, after correcting for data snooping | strong (context) |

### 2.2 Own tests: profile levels as targets

All tests:
- Hit = the level is reached within the horizon. Pools need a trade-through; profile levels a touch.
- **Baseline** = P(the excursion on that side reaches the same distance) from the same instrument's empirical surface, **matched on clock time**. Distances are in ATR(14, 1h) or in the 14-session mean RTH range.
- z: naive binomial, or block-clustered by day (`z_clu`) where trials overlap.

**E-OWN-0. Baseline matching matters (1h, 5 futures, H=30).** The test measures the prior session's references from the first bar of the next Globex session.

| Level | vs the engine-style all-hours baseline | vs the clock-matched baseline |
|---|---|---|
| PDH | -11.6 pp (z -9.3) | -3.2 pp (z -2.5) |
| POC | -7.5 pp | -1.5 pp |
| VAH | -6.6 pp | 0.0 pp |
| MID | -6.4 pp | +0.1 pp |
| nPOC_old | -11.0 pp | -2.3 pp |

- Reason: ATR(14) at the session end includes the RTH hours, so ATR-normalised distances understate how far the coming quiet hours travel.
- **The engine's `pBase` and empirical PoT have the same issue** (confirms `ict_time.md` G2).

**E-OWN-1. Prior-session levels and naked POCs (1h, engine-identical profile construction, 40 rows).**

| Level | n | Hit % (H=30) | Base % | Edge pp | z | H=115 (≈5 sessions): hit / base |
|---|---|---|---|---|---|---|
| POC | 879 | 67.7 | 69.2 | -1.5 | -1.1 | 83.6 / 84.7 |
| VAH | 1,098 | 68.0 | 68.0 | 0.0 | 0.0 | 85.0 / 85.7 |
| VAL | 1,106 | 59.4 | 62.2 | -2.8 | -2.2 | 78.9 / 79.0 |
| PDH | 1,181 | 51.7 | 54.9 | -3.2 | -2.5 | 77.8 / 78.6 |
| PDL | 1,219 | 45.5 | 46.7 | -1.2 | -1.0 | 67.7 / 67.9 |
| Range midpoint | 1,134 | 65.7 | 65.6 | +0.1 | 0.1 | 85.1 / 82.9 |
| Naked POCs aged ≥ 2 sessions | 2,054 | 15.7 | 18.0 | -2.3 | -3.2 | 38.7 / 43.4 (-4.7, z -4.7) |

- Per instrument, POC edge at H=30: CL -1.2, ES -1.5, NQ -1.4, RTY -0.6, YM -2.9 pp.
- **No magnet in any market.**
- The H=115 POC hit rate (83.6%) reproduces the folklore's "84-87%". The random level hits 84.7%.

**E-OWN-2. Fine RTH profiles from 1-minute data** (5 futures, ~57 sessions each, 1-minute volume over each bar's range, 30-hour horizon).

| Level | n | Hit % | Base % | Edge pp | z |
|---|---|---|---|---|---|
| RTH POC | 285 | 82.8 | 84.1 | -1.3 | -0.7 |
| RTH VAH | 285 | 73.3 | 76.3 | -3.0 | -1.4 |
| RTH VAL | 285 | 75.4 | 77.2 | -1.8 | -0.8 |
| RTH MID | 285 | 75.8 | 79.8 | -4.0 | -1.8 |

**E-OWN-3. IB and overnight extremes** as same-session targets (1-minute data, trade-through by 16:00, baseline matched on clock minute).

| Level | n | Hit % | Base % | Edge pp | z |
|---|---|---|---|---|---|
| IB high (from 10:30) | 295 | 61.0 | 61.4 | -0.4 | -0.2 |
| IB low (from 10:30) | 295 | 58.6 | 56.5 | +2.2 | +0.9 |
| Overnight high (from 09:30) | 242 | 54.1 | 53.3 | +0.9 | +0.3 |
| Overnight low (from 09:30) | 264 | 52.7 | 50.7 | +1.9 | +0.7 |

IB descriptive stats, same data:
- Any break 97.5%; both sides 22.8% (narrow-IB tercile 33.7%, wide 10.5%).
- Given a break, extension beyond the IB: median 0.46×IB; P(≥1×) 24%, P(≥1.5×) 11%, P(≥2×) 6%.

**E-OWN-4. 80% rule** (1-minute data, VA from the prior RTH volume profile, two consecutive 30-minute closes inside, target = the far edge by 16:00, baseline matched on clock minute).

| Open | n | Hit % | Base % | Edge pp |
|---|---|---|---|---|
| All | 42 | 61.9 | 54.0 | +7.9 (z 1.2, n.s.) |
| Above value | 18 | 66.7 | 49.4 | +17.2 |
| Below value | 24 | 58.3 | 57.4 | +0.9 |

Conclusion: no reliable edge, and the absolute rate is far below 80%. Together with X3 (25-28% vs 27-29%): **rejected**.

**E-OWN-5. Poor vs tailed extremes.**
- (a) TPO, 1-minute data, RTH, trade-through within 30 h:

| Rows per median range | Poor: n / edge | Excess (tail ≥ 2 rows): n / edge | Plain |
|---|---|---|---|
| 80 | 39 / +5.8 pp (z 1.0) | 456 / +0.3 | +2.2 |
| 40 | 72 / +4.0 (z 0.9) | 367 / +1.3 | -1.9 |
| 25 | 109 / +1.4 (z 0.4) | 292 / +1.7 | -0.8 |

- Poor extremes sit closer to the close (mean distance 0.38 vs 0.6 range units). That makes the *raw* repair rate high (73-79%) but explains most of it.
- (b) Engine-feasible hourly proxy (1 year, 5 futures): a session extreme is "poor (flat)" when ≥ 2 hourly bars lie within 0.10·ATR of it.

| Class | n | Edge pp | z |
|---|---|---|---|
| Poor (flat) | 851 | +1.6 | 1.1 |
| Plain | 851 | -2.7 | -1.9 |
| Tail (wick ≥ 0.5 ATR) | 854 | -1.5 | -1.0 |
| Poor, 2-4 ATR away | 253 | +5.7 | 1.9 |

| Bars within tolerance of the extreme | 1 | 2 | 3 | 4+ |
|---|---|---|---|---|
| Edge pp | -2.1 | +1.1 | +2.4 | +4.4 |

- Grade: **weak**. The direction is consistent; significance is marginal.

**E-OWN-6. Mid-profile single prints** (1-minute TPO, 80 rows, zones of ≥ 2 rows, 30-hour horizon, n = 98).
- Full fill (far edge): 53.1% vs 63.9% baseline (-10.8 pp).
- First touch of the near edge: 64.3% vs 72.1% (-7.8 pp).
- Single prints are **less** likely to be revisited than a random level. This is consistent with X7's "full reversal only 6-10%": they are initiative / continuation footprints, not magnets.

### 2.3 Own tests: profile shape and path (the engine's VP path-cost multiplier)

**E-OWN-7. Path volume between price and target** (`s3_path.py`).
- Composite: rolling 120-hour, **identical to `f_profile`** (48 rows, 60/40 range/body, 1-2-1 smoothing).
- vf = mean profile volume over the rows between close and target, divided by the profile mean, **with the same `f_row` clamping**.
- Targets: unswept 5/5 pivot highs and lows (strict trade-through), 0.5-10 ATR away.
- Sample: 65,946 target-bars, 1,203 day clusters, H=30, baseline matched on clock hour.

| vf class (engine multiplier) | n | Hit % | Base % | Edge pp | z_clu |
|---|---|---|---|---|---|
| < 0.6 (×1.10) | 12,465 | 28.4 | 32.1 | **-3.7** | **-3.2** |
| 0.6-0.8 | 6,631 | 25.2 | 27.1 | -1.9 | -1.8 |
| 0.8-1.0 | 8,925 | 23.4 | 24.2 | -0.8 | -0.9 |
| 1.0-1.2 | 14,130 | 16.7 | 18.7 | -1.9 | -3.2 |
| 1.2-1.4 | 10,017 | 21.7 | 23.7 | -2.0 | -2.2 |
| > 1.4 (×0.85) | 13,778 | 38.8 | 36.9 | **+1.8** | +1.7 |
| Target beyond the composite's price range | 28,141 | 14.2 | 17.5 | **-3.3** | **-4.6** |
| Target inside the range | 37,805 | 34.9 | 34.7 | +0.1 | +0.2 |

Robustness:
- Thin path, edge pp at composite depth 48 / 120 / 240 h: **-4.6 / -3.7 / -3.5**.
- Beyond range: **-2.5 / -3.3 / -2.8**.
- Thick path: +3.1 / +1.8 / -1.1 (not robust).
- Thin-path edge by instrument (120 h): CL -0.5, ES -3.5, NQ -4.6, RTY -4.5, YM -4.5.
- Restricted to targets inside the composite range, thin path is still -3.4 pp (z -2.1).

**Why the engine gets this backwards.**
- `f_pathVol` (1417-1424) clamps the target row with `f_row` (570-571). A target above `vpLo + rows·vpStep` therefore averages the thin top tail rows.
- These out-of-range targets get the ×1.10 "thin path" bonus, yet they are the worst class.
- Inside the range, a thin path means the target lies beyond an LVN, i.e. outside the current balance area. AMT itself predicts rejection there.

**E-OWN-8. Speed through LVN vs HVN.**
- Hourly: the next bar's |Δclose| / ATR is the same at low and high density: 0.566 at density ≤ 0.3·peak vs 0.568 at > 0.7·peak.
- 1-minute (prior 5-session composite):

| Density at price | Next-15-minute range (RTH-range units) |
|---|---|
| ≤ 0.2 | 0.196 |
| 0.2-0.4 | 0.198 |
| 0.6-0.8 | 0.182 |
| 0.8-1.0 | 0.181 |

  Next-15-minute |move|: 0.094-0.096 vs 0.088-0.089.
- So price is **about 7-9% more volatile in LVNs at the 15-minute scale** (partly mechanical volatility clustering). It is **not** more likely to reach targets beyond them (E-OWN-7).

**E-OWN-9. Do profile levels stop price (Osler-style bounce test).**
- At the first touch of the level, "bounce" = price moves X·ATR back before X·ATR through, within 24 bars.
- Random levels drawn uniformly inside the composite: bounce 51.8% (X=0.5) / 60.9% (X=1.0).

| Level | n | Bounce % (X = 1.0) | vs random pp | z_clu | X = 0.5: vs random pp (z) |
|---|---|---|---|---|---|
| LVN trough (< 0.3 peak, local minimum) | 7,212 | 64.1 | **+3.2** | **2.9** | +2.2 (2.0) |
| HVN peak (> 0.7 peak) | 3,328 | 61.3 | +0.3 | 0.2 | +0.6 |
| POC | 3,569 | 60.0 | -1.0 | -0.7 | -0.8 |
| VAH | 3,528 | 62.3 | +1.4 | 1.0 | +0.1 |
| VAL | 2,522 | 61.5 | +0.6 | 0.4 | +1.8 |

- "HVNs stall price" is **not supported**.
- "LVNs reject price" is **mildly supported**. This is the S/R "trend interruption" effect of X10-X12, and it matches the E-OWN-7 sign.

### 2.4 Own tests: value-based bias

**E-OWN-10. Which prior-day extreme is taken first** (1 year, 5 futures, 1,273 sessions, next 30 hourly bars).
- Unconditional: PDH first 47.9%, PDL first 42.5%, neither 9.6%.
- Raw tables look predictive:
  - value "higher": PDH first 60.7%;
  - value "lower": PDL first 60.8%;
  - close > VAH: PDH first 78.1%;
  - close < VAL: PDL first 76.5%.
- But that is mostly distance: when the close is above VAH, PDH is the nearer side 98.2% of the time.
- Logit of P(PDH first | decided) on log(d_PDL / d_PDH): coefficient 0.97, z 16.5. Adding features:

| Feature | LR χ² | df | Coefficients |
|---|---|---|---|
| Value migration | 1.05 | 2 | n.s. |
| Close vs POC | 0.17 | 1 | n.s. |
| Close vs VA | 5.58 | 2 | close > VAH −0.51 (z −2.05); close < VAL +0.40 (z 1.41) |

- The close-vs-VA signs are **mean-reverting**, not AMT continuation.
- Next 23-hour direction by value relationship: 50.6-61.3% up, against an unconditional 55.0%. No pattern.

**E-OWN-11. Composite value state** (engine composite, 120 h).
- Return to POC from outside value: -0.2 pp (above) / +1.5 pp (below).
- POC from inside value: +2.1 pp (z 2.0).
- Full rotation (the far VA edge) from outside value after ≥ 2 closes outside: -3.2 to -4.9 pp (z ≈ -2.5).
- Targets *further from value* after accepted acceptance (≥ 3 consecutive hourly closes beyond VA):

| Depth | Above value: edge pp (z) | Below value: edge pp (z) |
|---|---|---|
| 120 h | -3.8 (-2.0) | -5.3 (-3.0) |
| 48 h | -4.3 | -3.9 |
| 240 h | -0.6 | -6.0 |

  Targets back toward value: about the baseline. In "probe" states (1-2 closes outside), targets with the direction are about the baseline.
- Grade: weak-moderate. AMT's "acceptance means continuation" is not supported at this horizon. The data lean toward exhaustion.

**E-OWN-12. Target located inside the composite VA or at an HVN row.**
- 120 h: +2.5 pp (z 2.4) and +4.5 pp (z 2.6).
- 48 h: +0.8 / +3.2. 240 h: -0.6 / -0.5.
- **Not robust.** Do not hard-code it.

### 2.5 Evidence limitations
- One year of hourly data and three months of 1-minute data, almost entirely index futures plus CL. It covers one volatility regime (2025-26). No FX spot or crypto. The volume is the public dataset's.
- Hourly-bar profiles are coarse. The fine 1-minute RTH profiles (E-OWN-2) gave the same null result.
- Several z-scores are not cluster-robust (E-OWN-1/2/5): trials overlap only lightly there (one per level per day).
- TPO-based samples (poor highs, single prints, 80% rule) are small (n = 39-456).

---

## 3. Engine gap analysis

| # | Concept | Status | Lines | What the engine does / what differs |
|---|---|---|---|---|
| G1 | Volume profile (composite) | **present** | 978-1015 (1H feed: `request.security("60")` `[1]` + `lookahead_on` on charts ≤ 1H; `request.security_lower_tf` on charts > 1H), 1052-1057 (cache), 1384-1414 (`f_profile`), 1900-1909 (rebuild) | Rolling 120 × 1H composite, 48 rows, 60/40 range/body, 1-2-1 smoothing. Non-repainting. Rebuilt per new hour only when `usePathVP`; otherwise only on `tailBar` (1901) |
| G2 | POC | **missing** | (`vpSm` max never exposed) | No POC level, line or state. Evidence says POC is not a target (E-OWN-1/2, X1), so this is fine as a level source. Useful only as display and value state |
| G3 | Value area VAH/VAL | **missing** | none | Not computed. Needed only for value state / UX (AMT-3) |
| G4 | Naked POC | **missing (correct)** | none | Evidence null or negative (E-OWN-1, X1, X2 confounded). Keep it out of target selection |
| G5 | HVN | **missing** | none | Not needed as a target (E-OWN-9, E-OWN-12 not robust) |
| G6 | LVN display | **partial** | 202-207, 2250-2287 | Runs of rows < `lvnThr` (0.30) × peak, tails excluded, `lvnN` per side. Off by default. Not distance-limited. Shoulders rather than troughs (SMC-7). No semantics: the label says "LVN" but the engine treats LVNs as *accelerators* elsewhere |
| G7 | LVN/HVN path cost | **wrong** | 151-152 (input), 1417-1424 (`f_pathVol`), 1945-1947 (multiplier) | ×1.10 if vf < 0.6, ×0.85 if vf > 1.4. Measured: thin path -3.7 pp, thick +1.8 pp (E-OWN-7). `f_row` clamping gives out-of-range targets (the worst class, -3.3 pp) the thin-path bonus. On by default |
| G8 | TPO / time-at-price profile | **missing** | none | Volume only. TPO would need a ≤ 30-minute feed. Not worth it (E-OWN-2/5/6 nulls) |
| G9 | Single prints / tails (excess) | **missing**; FVG analogue present | 1862-1880 (FVG) | Single prints behave as continuation footprints, not magnets (E-OWN-6, X7). The FVG origin lockout (`originBars`, `awayATR`, 135-137, 689-690) already encodes "an origin is not a target" |
| G10 | Poor highs/lows | **partial** | 95 (`eqTol`), 1111-1139 (`f_mergeAt`/`f_mergeLiq` EQ fold for chart swings), 807-863 (`f_rangeTrack` / `f_sessTrack`), 1793-1809 (`f_pushExt` for PDH/PDL/PWH/PWL/session H/L) | Chart-swing EQH/EQL count flatness (density). Key-level trackers record only the extreme and its bar, not how many bars printed it: a flat PDH gets no `eqCount` unless a chart pivot merges in. Weak evidence (E-OWN-5) |
| G11 | Initial balance, extensions, day types | **missing** | none | IB extremes hit at the random rate (E-OWN-3). The descriptive stats (X5, X6) could inform a "time/reach" readout, but the engine's empirical PoT already learns reach |
| G12 | Open location / open types | **missing** | none | No quantitative support found. RTH-specific (index futures). Not worth it |
| G13 | 80% rule | **missing (correct)** | none | Rejected (X3, E-OWN-4) |
| G14 | Two-day value relationship / developing value migration | **missing (correct)** | none | No information beyond distance (E-OWN-10) |
| G15 | Balance vs imbalance | **partial** | 887-893 (`coilScore` from candle overlap → density), 1892-1895 (displacement in D) | Compression feeds density, not path or PoT. Composite value state is absent. Measured value-state effects are small (E-OWN-11) |
| G16 | Acceptance / rejection outside value | **missing** | none | ≥ 3 closes beyond VA → with-direction targets -3.8 to -6.0 pp (E-OWN-11). Candidate feature (AMT-4) |
| G17 | Overnight high/low and inventory | **partial** | 948-950 (Asia/London/NY session H/L), 597-602 (killzone affinity) | Covered by the session levels; the measured edge is about 0 (E-OWN-3) |
| G18 | Baseline / PoT time-of-day matching | **partial / biased** | 1059-1062, 1284-1322 (`f_empPoT`, `f_potModel`, `f_potBase`), 1426-1431 (trial `pBase`) | Surfaces are split only by HTF regime. E-OWN-0 shows -6 to -11 pp spurious edges for session-anchored starts. Fix: `ict_time.md` TIME-1, and also feed `f_potBase` |
| G19 | LVN as stop / invalidation reference | **missing** | 1343-1365 (`f_invalidation`) | Invalidation goes beyond the nearest opposing pool / execution swing / 1.5 ATR. LVN rejection (E-OWN-9) is unused |

---

## 4. Proposals (best first)

Design rule: every new effect is small (≤ 5 pp) and some vary by symbol (CL often differs). So:
- fixed defaults are tiny and point in the measured direction;
- every feature is registered in the **candidate ledger** (`ict_liq.md` ICT-1), so the chart's own outcomes set the multiplier.

### AMT-1 (P1, effort S): fix the volume-profile path cost (sign and out-of-range clamp)
- **Why.** E-OWN-7. The current mapping rewards the two classes that underperform: thin path (-3.7 pp, z -3.2) and beyond-profile targets (-3.3 pp, z -4.6). It penalises the one class that does not underperform (thick path, +1.8 pp). The setting is on by default (151).
- **Inputs (G_SCORE).** Keep `usePathVP`. Add:
  ```
  float vpOutM   = input.float(0.95, "VP · Beyond-Profile Target", minval = 0.5, maxval = 1.2, step = 0.01, group = G_SCORE,
    tooltip = "Targets outside the 1H composite's price range (not visited in Profile Depth hours) are reached less often than a random level at the same distance.")
  float vpThinM  = input.float(0.97, "VP · Thin-Path (LVN) Target", minval = 0.5, maxval = 1.2, step = 0.01, group = G_SCORE)
  float vpThickM = input.float(1.02, "VP · Thick-Path (in-balance) Target", minval = 0.5, maxval = 1.2, step = 0.01, group = G_SCORE)
  ```
- **Helper** (replaces `f_pathVol`, 1417-1424). Return na when the target edge is outside the profile, so clamping cannot fake a thin path:
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
- **Multiplier** (replaces 1945-1947):
  ```
  if usePathVP and vpSm.size() > 0
      float vf = f_pathVol(close, lv.nearEdge())
      lv.mult *= na(vf) ? vpOutM : vf < 0.6 ? vpThinM : vf > 1.4 ? vpThickM : 1.0
  ```
  `close` lies inside the profile on charts ≤ 1H in practice. If it does not, the clamp of `a` is harmless.
- **Ledger.** Record the class on each `Trial` (`int vpc`: 0 thin, 1 mid, 2 thick, 3 beyond). With ICT-1, register it as feature bits PATH_THIN / PATH_THICK / VP_OUT (AMT-2). Once a class has ≥ 30 graded probes, the learned bounded lift replaces the fixed input.
- **Tooltip / README.** Rewrite "thin-volume paths score higher" to "targets beyond the composite range or behind a low-volume node score slightly lower (measured)".
- **Value.**
  - It removes a systematic bias toward far, out-of-balance targets, which are the targets that "look wrong / never get hit".
  - It also slightly reduces target jumping: out-of-range candidates no longer get +10%.
  - Measurable directly: the per-class hit-vs-base in the ledger.
- **Evidence.** Moderate: own test, 66k target-bars, 1,203 day clusters, 5 futures; robust over three composite depths and 4 of 5 instruments.
- **Risk.**
  - Small effect; another regime or asset class (crypto, FX tick volume) may differ. That is why the multipliers are mild and learnable.
  - PWH/PWL often sit beyond a 120-hour composite and get ×0.95. Their tier weight (0.92) dominates, and ICT-1 will correct it if this is wrong.
- **Effort.** S (about 15 lines).

### AMT-2 (P1, effort M): register AMT features in the candidate ledger (no hard-coding)
- **Why.**
  - Every AMT effect measured here is ≤ 5 pp, has the wrong sign versus folklore, or is not robust across parameters or symbols (E-OWN-5/7/11/12).
  - The engine's DOL-only ledger books about one trial per H bars (2045), too few to learn feature lifts.
  - ICT-1's probe ledger grades *all* candidates against `f_potBase`, the same design used in this study.
- **Feature bits** (extend ICT-1's table at bits 14-20, so NF → 21):

  | Bit | Name | Rule at snapshot (needs AMT-3 for VA / value state) |
  |---|---|---|
  | 14 | VP_OUT | target edge outside [vpLo, vpLo + rows·vpStep] |
  | 15 | PATH_THIN | in range and vf < 0.6 |
  | 16 | PATH_THICK | in range and vf > 1.4 |
  | 17 | IN_VALUE | vpVAL ≤ target edge ≤ vpVAH |
  | 18 | AT_HVN | the row of the target edge is a local peak > 0.7·peak |
  | 19 | EXT_FROM_VALUE | `vaRun >= 3 and lv.side == vaPos` (AMT-4) |
  | 20 | POOR_EXT | key level with a flat-touch count ≥ 2 (AMT-6) |

- **Defaults.** Lift prior = 1 (neutral), `featN0` = 40, bound ±0.15, exactly as in ICT-1. The fixed AMT-1 multipliers apply until a bit has ≥ 30 graded probes, then the learned lift replaces them. With ICT-1 the AMT-1 inputs become priors.
- **Fallback if ICT-1 is not built.** Add `int vpc` and `bool inVal` to `Trial` (375-396). Keep 4 + 2 counter triplets (`n`, `k`, `Σ pBase`) booked in `f_book` (1461) for the DOL trials. Show them in Terminal / Full as `VP PATH  thin 31/44 vs 35.2 exp · out 9/30 vs 11.8 · thick …`. Learning is slower, but measurement is honest.
- **UX.** The "FEATURE LIFT" block (ICT-1) shows `VP_OUT ×0.93 (n 212) · PATH_THIN ×0.96 · IN_VALUE ×1.01 …`.
- **Value.** It lets each chart decide whether profile structure matters, instead of trusting folklore that our data contradicts. It also gives the trader an honest answer to "do LVNs matter on this symbol".
- **Evidence.** Moderate for the method (a distance-matched lift is the design used in E-OWN-1 to E-OWN-12). The individual features are weak to moderate.
- **Risk.**
  - Probes on many levels share one price path, so variance is understated. Shrinkage and the bounds mitigate this (as in ICT-1).
  - CPU: 7 extra bit tests per probe; negligible.
- **Effort.** M (S on top of ICT-1).

### AMT-3 (P2, effort S): composite value area and value state (POC / VAH / VAL, inside / probe / accepted)
- **Why.**
  - It is the infrastructure for AMT-2 bits 17-19 and AMT-4.
  - It gives the Terminal UX something AMT traders expect ("are we in value?") at almost no cost.
  - It is *not* proposed as a target source (E-OWN-1/2) and *not* as a directional bias (E-OWN-10).
- **Inputs (G_LVN, "Volume Profile").**
  ```
  bool  useVA  = input.bool(true, "Composite Value Area", group = G_LVN)
  float vaPct  = input.float(70.0, "Value Area %", minval = 50.0, maxval = 90.0, step = 1.0, group = G_LVN)
  bool  showVA = input.bool(false, "Show POC / VAH / VAL (Terminal)", group = G_LVN)
  ```
  `needVP` (979) becomes `showLVN or usePathVP or useVA`.
- **State (1052-1057).**
  ```
  var float vpPOC = na
  var float vpVAH = na
  var float vpVAL = na
  var int   vaPos = 0
  var int   vaRun = 0
  ```
- **Compute** (step 15, after `vpCum`, 1909). Change the rebuild condition at 1901 to `(usePathVP or useVA) ? (newHour or h1Lower or vpSm.size() == 0) : tailBar`.
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
  The ≥ tie goes to the higher row, which is TradingView-compatible once both neighbours sit at equal distance.
- **Value state** (inside `inCalc`, once per hourly close). On charts < 1H use `h1C` when `newHour`; on charts ≥ 1H use `close`:
  ```
  if useVA and not na(vpVAH) and (newHour or h1Lower)
      float cH = h1Lower ? close : h1C
      int   p  = cH > vpVAH ? 1 : cH < vpVAL ? -1 : 0
      vaRun := p != 0 and p == vaPos ? vaRun + 1 : p != 0 ? 1 : 0
      vaPos := p
  ```
- **UX.**
  - Terminal panel row: `VALUE ▲ ACCEPTED ABOVE (4h) · POC 5123.25 · VA 5110.0-5131.5`. Labels: `IN VALUE`, `▲ PROBE ABOVE`, `▲ ACCEPTED ABOVE`, and the mirror images.
  - Data-window plots for POC / VAH / VAL.
  - Optional lines when `showVA` (Terminal only):
    - POC solid 1 px;
    - VAH / VAL dotted;
    - left = `f_x(lvB.first())`, right = `xR`;
    - only when within `maxATR` of `close`, for autoscale safety (competitors.md).
  - Clean style: unchanged.
- **Value.** Context and infrastructure; zero risk to target selection.
- **Evidence.** n/a (infrastructure). The value-state effects themselves are weak to moderate (E-OWN-11).
- **Risk.** Platforms disagree on VA edges (X1: tie and VA % settings move edges on 20-65% of sessions). Document "composite, 1H, 48 rows" in the tooltip so users do not compare it with a TPO VA.
- **Effort.** S.

### AMT-4 (P2, effort S): extended-acceptance damping (exhaustion after time beyond value)
- **Why.** E-OWN-11. After ≥ 3 consecutive hourly closes beyond the composite VA, targets *further from value* are hit 3.8-6.0 pp less than random in 5 of 6 depth × side cells (z up to -3.1). Targets back toward value are at the baseline.
  - This contradicts the AMT folklore "acceptance means continuation" over a 30-hour horizon.
  - It is consistent with tradingstats X8: deep extensions are trend, but further extension is not more likely than random.
  - It is consistent with the logit sign in E-OWN-10.
- **Inputs (G_FLOW).**
  ```
  int   accN = input.int(3, "Acceptance Closes Beyond Value", minval = 1, maxval = 12, group = G_FLOW)
  float accM = input.float(0.95, "Extended-From-Value Multiplier", minval = 0.7, maxval = 1.1, step = 0.01, group = G_FLOW)
  ```
- **Apply** (multiplier loop, 1939-1948):
  ```
  if useVA and vaRun >= accN and lv.side == vaPos
      lv.mult *= accM
  ```
  Register it as AMT-2 bit 19, so the learned lift replaces `accM`.
- **Value.** Fewer over-extended continuation targets late in a move. That is a typical "target looked right but never got hit" failure. It is measured directly by the bit-19 lift.
- **Evidence.** Weak to moderate (own; consistent sign, mixed significance).
- **Risk.**
  - It may conflict with the draw vector D in strong trends, where D points away from value. The ×0.95 is small next to the draw pillar (weight 30) and the counter-draw penalty.
  - Keep it learnable.
- **Effort.** S (requires AMT-3).

### AMT-5 (P3, effort M): LVN troughs as rejection barriers (invalidation anchor and barrier feature), and LVN display semantics
- **Why.**
  - E-OWN-9: LVN troughs reject price more than random levels (+3.2 pp, z 2.9, at 1 ATR).
  - E-OWN-7: targets behind thin paths are reached less often.
  - E-OWN-8: price moves about 8% faster inside LVNs at the 15-minute scale ("through fast or rejected").
  - The engine treats LVNs as accelerators (G7) and displays them without semantics (G6).
- **Detection.** Adopt SMC-7: troughs are strict local minima over ±N rows with depth ≥ `lvnProm·peak`, tails excluded. Compute once per profile rebuild in step 15 into `var array<float> lvnPx` (trough centres) and `lvnHalf` (half-widths).
- **Barrier feature.** `nBar` = number of troughs strictly between `close` and `lv.nearEdge()`. Register it as an AMT-2 feature `LVN_BARRIER` (`nBar ≥ 1`). No default multiplier: use the learned lift only, because barrier counts were not tested directly.
- **Invalidation (`f_invalidation`, 1343-1365).** If no opposing pool lies within `maxATR`, prefer the nearest LVN trough on the opposite side at 0.5-1.5 ATR, before falling back to the execution swing or 1.5 ATR. Set `inv` beyond its far edge plus `buf`.
  - The race statistics (WIN≤H, avg R in the Terminal ledger) measure whether this helps.
- **Display (2250-2287).**
  - Draw troughs instead of threshold runs.
  - Limit them to `maxATR` from `close` (competitors.md).
  - Tooltip: "Low-volume node: price tends to be rejected here or to pass quickly; targets beyond it are reached slightly less often (measured on index futures)."
- **Value.** Better invalidation placement, plus honest LVN semantics. Measurable through race stats and the barrier lift.
- **Evidence.** Moderate for LVN rejection (E-OWN-9; consistent with Osler 2000, Kavajecz & Odders-White 2004, Chung & Bellotti 2021). Weak for stop placement (not tested directly).
- **Risk.**
  - With 48 rows over 120 hours, troughs are coarse. On charts > 1H, `request.security_lower_tf` already supplies the hourly intrabars.
  - Invalidation changes alter R:R readouts. Keep them behind an input `invLVN = input.bool(true, ...)`.
- **Effort.** M.

### AMT-6 (P3, effort S): poor (flat) key-level extremes count as equal highs/lows
- **Why.**
  - E-OWN-5: flat session extremes (≥ 2 separated bars within 0.10·ATR of the extreme) show +1.6 pp overall (z 1.1) and +5.7 pp at 2-4 ATR (z 1.9).
  - The edge rises monotonically with the touch count: 1 bar -2.1, 2 bars +1.1, 3 bars +2.4, 4+ bars +4.4 pp.
  - Chart-swing EQH/EQL already add density (`eqCount`, 682-683). Key levels (PDH/PDL/PWH/PWL/session H/L) never do, because `f_rangeTrack` / `f_sessTrack` (807-863) keep only the extreme.
- **Change.** Give `f_rangeTrack(bool isNew, float tol)` and `f_sessTrack(..., float tol)` two extra `var int` counters, `hiN` and `loN`, plus `var int hiLast` and `loLast`:
  ```
  if isNew  -> hiN := 1, hiLast := bar_index (and the same for lo)
  else if na(hi) or high > hi + tol  -> hi := high, hiB := bar_index, hiN := 1, hiLast := bar_index
  else if high >= hi - tol and bar_index - hiLast >= 3
      hiN += 1
      hiLast := bar_index
      if high > hi
          hi := high
          hiB := bar_index
  ```
  `tol = eqTol * atr` is computed at global scope. The 3-bar separation mirrors the test tracker at 652 (`bar_index - this.lastTest >= 3`).
  - Emit `oHiN` / `oLoN` with the period's extremes.
  - Add `int eqN = 0` to `Ext` (365-372) and pass it in `f_pushExt` (1793-1809).
  - When an `Ext` materialises (1848), set `ne.eqCount := math.max(ne.eqCount, eqN - 1)`.
  - The label tag shows `EQx2` as usual. The tooltip says "flat (poor) high".
  - Register it as AMT-2 bit 20.
- **Value.** A small, theory-consistent density boost to exactly the key levels traders call "poor highs". Measurable via bit 20.
- **Evidence.** Weak (own; directionally consistent across two constructions, marginal significance; no external statistics exist, X9).
- **Risk.**
  - Minimal. Density saturates (`1 - exp(-x)`), so one extra EQ adds at most about 0.9·0.6·weight.
  - Function signatures change, so update all 5 call sites (945-950).
- **Effort.** S.

### Considered and rejected (with the evidence)
- **Naked POC / prior VAH / VAL / VPOC as DOL level sources.** Edge -1.5 / 0.0 / -2.8 pp at H=30. Older naked POCs -2.3 pp (H=30) and -4.7 pp (H=115). Fine RTH profiles -1.3 to -3.0 pp (E-OWN-1/2, X1). If users ask for them, offer them only as *display* with an honest tooltip, or as ledger features (they will measure about 1.0).
- **80% rule.** E-OWN-4: +7.9 pp, n=42, n.s. X3: 25-28% vs a 27-29% base rate.
- **IB extremes / IB extensions as targets.** E-OWN-3: -0.4 / +2.2 pp. IB stats are useful context only (X5, X6).
- **Overnight high/low as special RTH targets.** E-OWN-3: +0.9 / +1.9 pp, n.s. Already covered by the session levels.
- **Value migration or close-vs-value as a draw bias.** E-OWN-10: no information beyond distance; the close-vs-VA signs are mean-reverting.
- **Single prints as magnets.** E-OWN-6: filled less than random (-10.8 pp). They act as continuation footprints, which the FVG origin lockout already encodes.
- **"HVNs stall price" (HVN as invalidation or target).** E-OWN-9: +0.3 pp. Targets in HVN or in value are not robust (E-OWN-12).
- **Open types, day types, profile shapes.** No quantitative evidence found. RTH-specific. Classification needs judgement. Not worth the Pine complexity.
- **TPO profile construction.** Needs a ≤ 30-minute feed and per-row period counting. The concepts it enables (poor highs, single prints, the TPO POC) measured null or weak.
- **Time-of-day-matched PoT and baseline.** Needed (E-OWN-0), but already proposed as TIME-1 in `ict_time.md`. Make sure `f_potBase` (1314-1322) uses the same clock-conditioned surface, otherwise the ledger's EDGE verdict stays biased.

---

## 5. Sources
- tradingstats.net, Initial Balance Breakout Statistics (ES/NQ 2015-2025): https://tradingstats.net/initial-balance-breakout-statistics/
- tradingstats.net, Single Prints: Fill Rates, Reversal Odds, and Decay (NQ/ES/YM/RTY 2014-2026): https://tradingstats.net/single-prints-market-profile-research/
- tradingstats.net, How Often Does the High of the Day Hold? (2019-2026): https://tradingstats.net/high-of-the-day-hold/
- tradeify, Market Profile Explained With a 589 Session TPO Test (VA algorithm, tie rules, IB, POC revisit, 80% rule): https://tradeify.co/education/market-profile
- "Naked POC Magnetism: Fill Probability & Median Wait" (open-source script; survival-analysis method): https://in.tradingview.com/script/MfTpypsI-Naked-POC-Magnetism-Fill-Probability-Median-Wait/
- "Naked POCs Explained" (revisit statistics, quoted via smc_impl.md E8): https://www.tradingview.com/chart/XAUUSD/G1M0dKF0-Naked-POCs-Explained-Why-Price-Keeps-Coming-Back-to-Them/
- LuxAlgo concept library:
  - naked POC: https://www.luxalgo.com/library/concept/naked-poc/
  - poor high/low: https://www.luxalgo.com/library/concept/poor-high-poor-low/
  - 80% rule: https://www.luxalgo.com/library/concept/80-percent-rule/
  - open types: https://www.luxalgo.com/library/concept/open-types/
- Open types:
  - https://paracurve.com/2020/02/day-opening-types.html
  - https://www.trenddaytrading.com/market-profile-trading
  - https://medium.com/@bhattacharya.ratul/opening-types-open-range-strategy-and-practical-applications-153df89e2bf5
  - https://www.windotrader.com/market-profile/market-profile-glossary-index/
- 80% rule:
  - Market Profile Education Series (MarketDelta/CBOT material): https://www.forexfactory.com/attachment/file/1462817?d=1404702306
  - https://www.metrotrade.com/what-is-the-80-rule-in-futures-trading/
  - https://www.elitetrader.com/et/threads/value-area-80-rule.95941/
- Poor highs/lows:
  - https://axiafutures.com/blog/trading-strategies-around-poor-lows-and-poor-highs/
  - https://therighttrader.com/learn/volume-and-order-flow/poor-highs-and-lows
- Osler, C. (2000). Support for Resistance: Technical Analysis and Intraday Exchange Rates. FRBNY Economic Policy Review 6(2): https://www.newyorkfed.org/research/epr/00v06n2/0007osle
- Osler, C. (2001/2003). Currency Orders and Exchange-Rate Dynamics (stop-loss clustering), FRBNY Staff Report 125: https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr125.html
- Kavajecz, K. & Odders-White, E. (2004). Technical Analysis and Liquidity Provision. Review of Financial Studies 17(4): https://ideas.repec.org/a/oup/rfinst/v17y2004i4p1043-1071.html
- Chung, K. & Bellotti, A. (2021). Evidence and Behaviour of Support and Resistance Levels in Financial Time Series. arXiv:2101.07410: https://arxiv.org/abs/2101.07410
- Jung, J. & Lee, K. (2026). Do Round Numbers Hold Prices? arXiv:2610.34787: https://arxiv.org/abs/2610.34787
- Park, C.-H. & Irwin, S. The Profitability of Technical Trading Rules in US Futures Markets: A Data Snooping Free Test: https://farmdoc.illinois.edu/publications/the-profitability-of-technical-trading-rules-in-us-futures-markets-a-data-snooping-free-test
- Data: public CME continuous OHLCV CSVs: https://github.com/axb0306/cme-futures-ohlc
- Internal: `study/ict_liq.md` (ICT-1), `study/ict_time.md` (G2, TIME-1), `study/smc_impl.md` (SMC-7, E8), `study/competitors.md` (LVN distance limit and contrast).
