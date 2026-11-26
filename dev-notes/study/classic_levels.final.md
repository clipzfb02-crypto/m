# Classic reference levels as liquidity: final combined report (Researcher A + Researcher B)

Domain: floor pivots (classic, CPR), Camarilla, Fibonacci / Woodie / DeMark pivots; daily / weekly / monthly and "naked" pivots; round numbers and option-strike pinning; session VWAP, anchored VWAP and deviation bands; daily / weekly / monthly / quarterly / yearly opens; previous day / week / month / quarter / year highs and lows; 52-week, all-time and N-day extremes; previous settlement; opening gaps (including the BTC "CME gap"). The engine's question is: **which liquidity is reached next, how likely within H bars, and does a classic reference level change that?**

**Markers.**
- **[A✓]**: A's claim, checked by B (source re-read through search summaries, or test re-run).
- **[B-fix]**: A's claim corrected or downgraded by B.
- **[B-new]**: added by B.
- **[B-test]**: B's own test (scripts in `study/classic_b_tools/`).
- Unmarked material is A's and was not re-checked.

**Method note.**
- Firecrawl was out of credits and WebFetch could not resolve any external host in this session (newyorkfed.org, arxiv.org, github.io, mypivots.com and dspace.cuni.cz all failed). Published evidence therefore comes from WebSearch result summaries, which are secondary: numbers are quoted as the summaries report them.
- The core evidence is own tests on the shared data (CME 1h futures, BTC 1h, daily SPX/NDX), using the engine ledger's own baseline: a random level at the same distance.
- B re-ran A's main test with **scale-matched placebos, trend controls and two better volatility units**, and that changed A's headline conclusion (see 0.1).

---

## 0. Headline findings (read this first)

1. **No classic level is a magnet beyond its distance.** [A✓, B-test]
   - Daily floor, Camarilla, Fibonacci, Woodie and DeMark levels are reached at the random-level rate: -3.0 to +1.2 pp over about 1,500 CME days and 3,300 BTC days, the same as range-scaled placebo levels.
   - B re-ran this test (T1) with the volatility-unit baseline that sibling REG-1 proposes. Every pivot edge stays within ±0.5 pp of A's value (table B4).
   - On daily bars, monthly / quarterly opens and monthly pivots are reached *less* often than random (QOPEN -1.9 pp, z -3.8 at 5 days; MOPEN -3.2 pp, z -3.0 at 20 days). Prior month / quarter / year extremes and 52-week / N-day extremes are at baseline (A's T2; not re-run by B).

2. **[B-fix] A's main finding, the "weekly-reference path barrier", is mostly an artefact. A's CL-1 is rejected.**
   - A found that pools beyond a weekly PP / R1 / S1 or the weekly open are swept 2-6 pp less often (z -5 to -7). B reproduces the raw numbers exactly (CME -6.25 pp, BTC -5.45 pp).
   - **The same "barrier" appears for meaningless levels on the weekly scale.** These are random prices inside the prior week's range (CME **-6.70 pp, z -6.1**), weekly pivots shifted by 0.12-0.25 of the weekly range (CME -6.34 pp), and the weekly pivots of three weeks earlier (CME -5.54 pp). A's placebo was on the *daily* scale and was crossed by 87% of pools, so it could not detect this (B1).
   - The generic part has two mechanisms, both of which matter for the probability engine:
     - **Volatility-unit bias.** Pool edge versus the ATR14 baseline falls from +3.3 to -9.9 pp (CME) and from +10.0 to -11.7 pp (BTC) across ATR14/ATR200 quintiles.
     - **Distance in prior-week-range units.** Edge falls from +3.5 to -9.5 pp (CME) and from +5.1 to -12.3 pp (BTC) even though the ATR distance is already matched (B2).
   - With these controls, the **real** weekly levels add nothing on CME (-0.006 logit, t -0.1 at H24; -0.06, t -0.9 at H8).
   - On BTC, only the **weekly PP** keeps a residual: -0.19 logit (t -2.9 at H24, -2.6 at H8). The monthly open keeps -0.26 on CME (t -2.6) but +0.14 on BTC (t +1.9): opposite signs (B3).
   - **Verdict:** a pivot-specific barrier is at most a small, market-specific effect (weak evidence). Do not hand-code it. Record it in the ledger against a placebo control (CL-3), and fix the generic part in the reach unit (REG-1, CL-7).

3. **Small genuine "return to prior value" pull, and it survives the unit change.** [A✓ + B-test]
   - Distance-matched edges:
     - CME, H24, blended-unit baseline: prior settlement **+3.45 pp (z 3.7)**, prior-day mid / CPR BC **+3.96 (z 3.6)**, prior-day VWAP +2.84 (z 2.6), PP +2.27 (z 2.2). At H8: SETT +3.60, PP +3.06.
     - BTC: CPR TC +2.13 (z 3.6), PP +1.73 (z 2.4).
   - Placebo levels near the prior close show about 0; placebos near the PP show the same pull. So this is a **prior value centre** effect, not a formula effect.
   - Liquidity pools at matched distance sit at **-2.5 pp** (CME, blended unit). Value levels therefore beat them by about 5-6 pp, which makes them a candidate *target type* (CL-4).

4. **Confluence with reference levels is never positive.** [A✓ + B-test + B-fix wording]
   - No anchor family raises the sweep rate (A's T5).
   - With the blended-unit baseline, a weekly or monthly open within 0.35 ATR of a pool lowers it in all four sets: CME **-6.25 (z -3.2)** and -4.22 (z -4.6); BTC -3.39 (z -2.8) and -1.61 (z -2.7) (B6).
   - [B-fix] A wrote that the sibling `calib_ml` "found the same (-0.25 logit)". After its Holm correction that coefficient is not significant (p 0.11; pooled -0.04, t -0.7). The correct wording is "unsupported, not proven harmful".
   - [B-new, via calib_ml CAL-5] Every PDH/PDL/PWH/PWL pool is *self-confluent*: it is pushed at exactly the price of its own anchor, so it gets conf ≥ 0.35, about +5 score points.
   - CL-2 neutralises the pillar.

5. **Opening gaps: only large gaps fill more than distance predicts, and the literature is mixed.** [A✓ + B-new]
   - Own tests:
     - NDX cash gaps ≥ 0.5 daily ATR: +7.9 pp (z 4.5); gap-downs +12.0 pp. Gap-ups about 0.
     - Sibling `ict_pd` B, CME futures gaps ≥ 0.5 ATR: +7.4 pp (z 2.2).
   - Literature:
     - Grant, Wolf & Yu (2005): opening reversals in index futures, *stronger after large up opens*, and sharply weaker after bid-ask costs.
     - [B-new] Plastun, Sibande, Gupta & Wohar (2020): US indices 1928-2018, prices move *in the gap's direction* on gap days, "contrary to the myth that price gaps tend to get filled".
   - [B-new] The BTC "CME gap" folklore is moot for new gaps: CME moved crypto futures to 24/7 trading on 29 May 2026.

6. **VWAP.** [A, not re-run]
   - A frozen session VWAP is a weak magnet (CME +1.5 pp, z 2.9; BTC +0.3).
   - The moving line is touched mostly for mechanical reasons.
   - σ-bands and weekly / monthly AVWAP are null or negative (BTC -2.6 to -2.9 pp).
   - It must not become a static target.
   - [A✓] Zarattini & Aziz (2023), a VWAP trend filter on QQQ: +671% and Sharpe 2.1 (2018-Sep 2023); third parties report decay. That is about bias, not targets.

7. **The folklore rules fail.** [A]
   - "Narrow CPR → trend day" is reversed or inconsistent (n 8,699 days).
   - "Above pivot / VWAP / weekly open / monthly open = bullish" adds nothing to which of PDH / PDL is taken first beyond the geometry of price in the prior range.

8. **[B-new] Pine v6 facilities A did not use.** All are verified in the local v6 reference mirror.
   - `ta.pivot_point_levels(type, anchor, developing)` returns 11 levels for "Traditional", "Fibonacci", "Woodie", "Classic", "DM" and "Camarilla" in one call.
   - `ticker.modify(tickerid, ..., settlement_as_close = settlement_as_close.on)` gives the exchange **settlement** as the daily close for futures.
   - `session.isfirstbar_regular` / `session.islastbar_regular` mark the regular session.
   - The engine makes 6 `request.*` calls (923-925, 939, 981-982) against a limit of 40 (64 on the Ultimate plan), so one settlement request is affordable.

9. **For the engine:**
   - Neutralise the Confluence pillar and stop self-confluence (**CL-2, P1**).
   - Add an optional **prior-session value target**: PP, D-EQ or the exchange settlement, with an optional gap gate (**CL-4**).
   - Measure the reference context per chart *against a phantom-level control* (**CL-3**).
   - Optionally put the prior-week range into the reach unit (**CL-7**, through REG-1's scorecard).
   - PMH/PML pools (**CL-5**) and a display-only overlay (**CL-6**) are completeness items.
   - **Do not** add a weekly-pivot barrier multiplier, pivots, opens or VWAP as targets, or any reference level as a positive anchor.

### 0.1 What B changed relative to A

| # | Change | Why |
|---|---|---|
| 1 | **CL-1 (weekly-reference barrier, P1) rejected**; replaced by a ledger bit with a phantom control (CL-3) and a unit candidate (CL-7) | Weekly-scale placebos reproduce the "barrier"; real levels add ≈ 0 on CME after controls; BTC weekly PP -0.19 logit only (B1-B3) |
| 2 | Weekly pivots' evidence grade moderate → **weak** (for a level-specific effect) | Same |
| 3 | Literature link "fits Osler 2000 / Kavajecz & Odders-White 2004" qualified | Those papers test firm-published S/R and order-book depth, not formula pivots; B's placebo test shows formula weekly pivots are not special on CME |
| 4 | Prior-day value effect re-tested with the volatility-unit baseline: **confirmed** | B4 |
| 5 | CL-4 widened: prior-session value target (PP / D-EQ / settlement) with an *optional* gap gate; settlement through `settlement_as_close`; unified object with ICTPD-6 | B4; Pine docs; sibling ICTPD-6 B uses kinds 8/9 and src 11-13 |
| 6 | calib_ml confluence wording corrected; self-confluence bug added to the gap analysis | calib_ml.final §0 item 6, CAL-5 |
| 7 | PW tier claim softened: "not supported" → "inconsistent across markets" | B5: PW pools are the worst source on CME but neutral to best on BTC under better baselines |
| 8 | New literature added and A's sources checked: mypivots ES/YM test, Plastun et al. 2020, Donaldson & Kim 1993, Aggarwal & Lucey 2007, Urquhart 2017, Lee & Seong 2019, Driessen et al. 2013, Cboe 0DTE, CME 24/7 crypto | §2.1 |
| 9 | Minor engine-ref fix: the live PoT assignment is at **2067** (A wrote 2066) | grep |
| 10 | CL-6 rebuilt on `ta.pivot_point_levels`; CL-2 adds hysteresis rescaling and a skip of the anchor loop | Pine docs; score arithmetic |

---

## 1. Concepts: precise definitions, parameters, practitioner use, failure modes

Notation: H, L, C, O are the prior period's high, low, close and open (a day, week or month); R = H − L. "Day" means the instrument's trading session: for CME the Globex day (18:00-17:00 ET); for crypto the 00:00 UTC day. TradingView's `timeframe.change("D")` follows the symbol session.

### 1.1 Classic floor pivots (Standard / "Traditional") [A✓]
- **Formulas:** PP = (H + L + C)/3; R1 = 2PP − L; S1 = 2PP − H; R2 = PP + R; S2 = PP − R; R3 = H + 2(PP − L); S3 = L − 2(H − PP).
  - TradingView's "Traditional" type continues the pattern with R4/S4 and R5/S5.
  - Its "Classic" type differs from R3 on (R3 = PP + 2R).
  - In Pine v6: `array<float> lv = ta.pivot_point_levels("Traditional", timeframe.change("W"))` returns [P, R1, S1, R2, S2, R3, S3, R4, S4, R5, S5]. The values freeze on the anchor bar unless `developing = true`. [B-new]
- **Timeframes:**
  - daily pivots for intraday charts;
  - weekly pivots for 1H and below;
  - monthly pivots for 4H and daily.
- **Practitioner use:**
  - "Above PP = bullish".
  - R1/S1 are first targets or fades, R2/S2 extended targets.
  - In range days price rotates between PP and R1/S1; in trend days it walks R1 → R2.
  - Vendors report touch counts conditional on where the open sits (YM opened between PP and R1, n 62: PP touched 74%).
- **Edge cases:**
  - Which close (settlement or last trade; see 1.10).
  - The session template: RTH-only pivots differ from 24h pivots.
  - DST.
  - Crypto weekends.
- **Failure modes:**
  - Touch rates are high only because R1/S1 sit about 1-2.5 ATR(1h) from price.
  - With 7 levels per timeframe across 3 timeframes, some level is always near, so any reaction reads as confirmation.

### 1.2 Central pivot range (CPR) and virgin / naked pivots (Ochoa, *Secrets of a Pivot Boss*) [A]
- **Formulas:** BC = (H + L)/2 (the engine's `dayEQ`, line 967); TC = 2PP − BC; width |TC − BC| = |2C − H − L|/3.
- **Folklore:**
  - A narrow CPR (bottom quartile of about 20-50 sessions) → a trend day; a wide one → a range day.
  - Price above the CPR is bullish.
  - A "virgin" pivot (never traded in its session) is a magnet later.
- **Evidence:** no published test. A's T6 reverses the width rule. Naked pivots are at baseline (T1; B4: -0.8 to +0.0 pp under the blended unit).

### 1.3 Camarilla (Nick Scott, 1989) [A✓]
- **Formulas:** H_k = C + R·m_k and L_k = C − R·m_k with m = 1.1/12, 1.1/6, 1.1/4, 1.1/2 (0.0917, 0.183, 0.275, 0.55). TradingView's Camarilla adds R5 = (H/L)·C.
- **Use:**
  - Fade at H3/L3; breakout through H4/L4.
  - "70% of moves stay inside H3-L3, 90% inside H4-L4": unsourced vendor copy.
- **Evidence:** null (T1). B4 under the blended unit: CME H3/L3/H4/L4 between -0.6 and +0.5 pp; BTC between -1.7 and 0.0.

### 1.4 Fibonacci, Woodie, DeMark pivots [A✓]
- **Fibonacci:** PP ± 0.382R / 0.618R / 1.000R.
- **Woodie:** PP_w = (H + L + 2C)/4; R1 = 2PP_w − L; S1 = 2PP_w − H; R2/S2 = PP_w ± R.
- **DeMark:** X = 2H + L + C if C > O; H + 2L + C if C < O; H + L + 2C if C = O. PP = X/4; R1 = X/2 − L; S1 = X/2 − H. In Pine "DM" returns only P/R1/S1. Woodie cannot be `developing`.
- All are deterministic functions of (H, L, C[, O]) that differ only in multipliers, so a range-scaled placebo is the right control.
- **Evidence:** null. On BTC, FIB_R1 and FIB_S1 are reached *less* often: -2.3 / -2.6 pp, z -2.9 / -3.3 under the blended unit (B4).

### 1.5 Weekly and monthly pivots [B-fix]
- The same formulas on the prior week / month.
- **As levels:** weekly pivots are at baseline (T2: +0.1 to +0.6 pp). Monthly pivots are reached less often (T2: M_PP -1.75 pp at 5 days, -3.3 pp at 20 days).
- **As path barriers:**
  - A measured a strong barrier (T8).
  - B shows that weekly-scale *placebo* levels give the same result on CME. With controls for the volatility unit and for distance in weekly-range units, the real levels add nothing on CME.
  - On BTC only the weekly PP keeps a residual of about -0.19 logit (z ≈ -3) (B1-B3).
- **Mechanism, corrected:**
  - "Count of weekly-scale levels between price and target" is a proxy for (a) distance measured on a longer volatility scale than ATR14 and (b) how much of the path runs through the prior week's balance area.
  - It is not, in general, evidence that orders rest at the formula prices.

### 1.6 Round numbers, psychological levels, option strikes [A✓ + B-new]
- **Grid:** step S (00 / 50 / 25). Auto step per sibling OF-4: S = 10^floor(log10(2·daily ATR)) and the half step. Examples: ES (daily ATR ≈ 60) → 100 / 50; BTC (≈ 2,500) → 1,000 / 500; EURUSD (≈ 0.006) → 0.01 / 0.005; gold (≈ 40) → 10 / 5.
- **Order placement (strong):** Osler (2003): take-profits sit at "00" 9.3% of the time; stop-buys sit at 01-10 above a round 14.4% vs 7.4% at 90-99 (via `ict_liq` E1). Bhattacharya, Holden & Jacobsen (2012): buy-sell imbalance flips at round numbers.
- **Barriers in index levels and gold:** [B-new]
  - Donaldson & Kim (1993, JFQA 28(3)): DJIA 1952-1990 shows significant price barriers; the Australian All Ordinaries shows none.
  - Aggarwal & Lucey (2007, RFE 16): gold barriers at round numbers affect the conditional mean and variance.
  - O'Connor & Lucey (2016): gold yes (0 / 00), silver no.
- **Crypto:** [B-new]
  - Urquhart (2017, Econ. Letters): over 10% of BTC prices end in 00, but there is **no significant return pattern after round numbers**.
  - Lee & Seong (ICIS 2019): barriers at 1,000 and 10,000 on Coinbase, Bitstamp and Bitfinex; the 1,000 barrier weakens after the all-time high.
- **Bar tests (siblings):** rounds are not magnets. A sweep wick beyond a pool stops short of a round number just past it (-4.2 pp, OF-4).
  - A's T5: a pool within 0.35 ATR of a round is swept -1.0 to -1.4 pp less often. Never use rounds as a positive anchor.
- **Option-strike pinning:**
  - Ni, Pearson & Poteshman (2005): optionable stocks cluster at strikes on expiration Fridays.
  - Golez & Jackwerth (2012, JFE 106(3)): S&P 500 futures, Nov 1992-Nov 2009; at least $115 m notional shift per expiration day. They attribute it to last-minute sales of in-the-money options by individuals, not to market makers being short gamma. [A✓, mechanism B-new]
  - Elms (2026, SSRN, via a Substack summary): no pinning on 2,294 days in 2016-2025.
  - [B-new] Cboe: 0DTE hedging flows are 0.04-0.17% of daily S&P futures liquidity. A 2026 Princeton thesis does not support the gamma-feedback channel.
  - Not usable in Pine (no open-interest data), and the effect depends on the regime.

### 1.7 VWAP family [A✓ for definitions]
- **Session VWAP:** VWAP_t = Σ(tp·v)/Σv from the anchor, tp = hlc3. σ_t = sqrt(Σv·tp²/Σv − VWAP²).
  - Pine v6 signatures: `ta.vwap(source, anchor) → series float` and `ta.vwap(source, anchor, stdev_mult) → [vwap, upper, lower]`, where `anchor` is a bool such as `timeframe.change("D")`.
- **Anchored VWAP (Shannon):** the same sum from a chosen event (earnings, gap, swing, week / month / YTD start). No published backtest; the anchor is subjective.
- **Use:**
  - Institutional benchmark (about half of institutional flow is VWAP-benchmarked; weak-moderate source).
  - "Above VWAP = buyers in control": Zarattini & Aziz 2023 [A✓].
  - Fade at ±2σ.
- **Failure modes:**
  - The line moves toward price, so "return to VWAP" is partly mechanical.
  - Early-session estimates are thin.
  - The crypto anchor is arbitrary.
  - [B-new] No peer-reviewed test of "probability of returning to VWAP after a deviation" was found. One self-published TradingView study claims "150,000 Bonferroni-significant results"; no grade (data-mined).

### 1.8 Period opens [A✓]
- Daily (session) open; ICT "true day" / midnight open (sibling `ict_time`: not special against neighbouring hourly opens, +0.3 ± 1.1 pp); weekly open (futures Sunday 18:00 ET, crypto Monday 00:00 UTC); monthly / quarterly / yearly open (the period's first trade).
- **Use:** "above the monthly open = bullish month"; opens as magnets ("the weekly open is retested in X% of weeks": Edgeful publishes conditional retrace rates with no distance control); opens as S/R.
- **Evidence:**
  - Not magnets (T2: Q / M opens reached *less* often on daily bars).
  - No bias value beyond geometry (T7, `bias_dol`).
  - Negative as confluence *at* a pool, replicated 4/4 under the blended unit (B6).
  - As a path barrier, after B's controls: the weekly open is null in both markets; the monthly open is -0.26 on CME and +0.14 on BTC, so inconsistent (B3).

### 1.9 Prior-period highs / lows and N-period extremes [A✓ + B-new]
- PDH/PDL and PWH/PWL are in the engine. PMH/PML, PQH/PQL and PYH/PYL are not.
- 52-week high/low = extreme over 252 sessions; ATH = the full-history extreme; N-day extremes = ICT IPDA 20/40/60.
- As pools they are swept on a trade-through (the engine's strict `>` / `<`).
- **Evidence:**
  - Monthly-horizon anchoring in stocks is strong (George & Hwang 2004; Li & Yu 2012).
  - [B-new] Driessen, Lin & Van Hemert (2013, Review of Finance 17(1)): implied volatility and beta *fall* approaching a 52-week high or low. Volatility *rises* after a breakthrough: return variance +19% the day after a 52-week-high break and +43% after a low break (working-paper figures). These are volatility barriers, not magnets.
  - At DOL horizons, A's T2 is null.

### 1.10 Previous settlement / close, opening gaps, CME weekend gaps [A✓ + B-new]
- **CME ES settlement:** a 30-second VWAP ending 15:00 CT (16:00 ET), effective **26 Oct 2020**; before that, 15:14:30-15:15:00 CT. [A✓ via the CME FAQ; the SER number A cited was not re-verified]
  - In Pine, `ticker.modify(syminfo.tickerid, settlement_as_close = settlement_as_close.on)` makes "1D and higher" `close` the settlement on supported futures. [B-new]
- **Opening gap:** gap = session open − prior close or settlement (Caporale & Plastun 2017 use open vs prior close). "Gap fill" = trading back to the prior close within the session or N sessions.
  - On 24h futures charts the RTH "gap" is not a chart gap; NDOG/NWOG (17:00→18:00, Friday→Sunday) are the chart gaps (sibling ICTPD-6).
- **Folklore and vendor statistics:**
  - "80% of small gaps fill".
  - Vendor fill rates, SPY about 20 years: 0.10-0.25% gaps 77-85%, 0.25-0.5% 62%, 0.5-1% 33-42%, ≥ 1 ATR 23%.
  - [B-new] Linnsoft: price touched the prior close on 1,048 of 1,803 days (58.1%), with no distance control.
- **BTC "CME gap"** [B-new]: the gap between CME BTC futures' Friday close and Sunday reopen.
  - Folklore: "98% fill", with no methodology. CryptoSlate: 6 of 6 filled in early 2025, mean fill time 29 h.
  - **CME moved crypto futures to 24/7 trading on 29 May 2026** (CME press release dated 1 Jun 2026), so no new gaps form. Do not build it.

### 1.11 [B-new] Weekly-scale geometry and the volatility unit (why "weekly barriers" appear)
- The engine's reach baseline (`f_empPoT` / `f_potBase`, 1284-1322) measures distance in ATR14 at the window start.
- **Volatility mean-reverts, so ATR14 overstates the next H bars' movement after an expansion and understates it after a compression** (sibling REG-1).
- Even with REG-1's blended unit √(ATR14·ATR100), distance measured in **prior-week-range units** still predicts lower reach (B2, B3). That matches HAR logic: realised volatility has daily, weekly and monthly components, and the weekly component is missing from the unit.
- Any feature that counts weekly-scale levels between price and target is correlated with that distance (corr 0.47-0.64), so it picks up the bias.
- **Lesson for every sibling proposing "levels between price and target" features:** test them against scale-matched phantom levels, not against daily-scale or uniform placebos.

---

## 2. Evidence

### 2.1 Published evidence (graded)

| # | Claim | Source | Numbers | Grade | Check |
|---|---|---|---|---|---|
| P1 | Published S/R levels interrupt intraday trends | Osler (2000), FRBNY EPR 6(2):53-68 | Levels from 6 FX firms (Jan 1996-Mar 1998) vs 10,000 sets of arbitrary levels; 1-minute quotes 9:00-16:00 NY. "Strong evidence" the levels predict trend interruptions; power varies across firms and currencies; firms largely disagree; it lasts at least 5 business days | **strong** for *firm-published* levels and for bounce once reached | A✓. [B-fix] Not a test of formula pivots and not a reach test. B1-B3 show formula weekly pivots are not special on CME |
| P2 | S/R levels sit at limit-order-book depth peaks | Kavajecz & Odders-White (2004), RFS 17(4):1043-1071; Taiwan and China replications | S/R coincides with depth peaks; MA signals locate depth | **strong** (depth location) | A✓ (same caveat as P1) |
| P3 | Stops beyond, take-profits at round numbers; crossings cascade | Osler (2003, 2005); Bhattacharya, Holden & Jacobsen (2012) | TP 9.3% at 00; stop-buys 14.4% vs 7.4%; extra move after a crossing of +0.27 to +2.35 hundredths of a percent over 15 min to 2 h | strong | A✓ via siblings |
| P4 | Pivot points in FX: no value in the traditional form | Johnsson & Frykmer (2019), Lund MSc thesis | Not profitable as standard; "can be profitable if implemented inversely for two of the pairs" | weak (thesis) | A✓ |
| P5 | Pivots "work" as S/R 53-58% | Bulkowski, ThePatternSite | Counts "support or resistance near a pivot" and "transits of the band"; no random control | weak | [B] page not reachable; percentages not re-verified |
| P6 | R1/S1 touch rates | Steenbarger (S&P, 963 days, forum relay); FXNX; Tradeify (ES); Edgeful (YM) | About 80% of days hit R1 or S1; FX R1 46%, S1 44%; YM opened between PP and R1 → PP touched 74.2% (n 62) | weak (no distance control) | A |
| P6b | Pivot bands vs a random system | [B-new] mypivots.com, "Do Pivot Points work?" | ES/YM/ER2/NQ RTH, 630 days to June 2005: "only marginally more probable areas for reversal (or picking the high and low of the day) than a random system". ES 34.2% random vs 34.6% high / 37.3% low; YM 32.4% vs 29.8% / 35.9% | weak (has a random control, small n, method partly unseen) | B (search summary) |
| P6c | Pivot + opening-range system on Chinese futures | [B-new] Tian, Quan, Zhang & Cai (2012), JILSA 4:279-284 | Profitable on index futures, weaker on illiquid commodities; trading system, no random control | weak | B |
| P7 | Camarilla containment / reversal rates | vendor guides | "70% inside H3-L3, 90% inside H4-L4" | none | A |
| P8 | Narrow CPR → trend day | Ochoa; LuxAlgo; TradingView scripts | no statistics | none (T6 contradicts) | A |
| P9 | VWAP trend filter | Zarattini & Aziz (2023), SSRN 4631351 | QQQ 2 Jan 2018-28 Sep 2023: $25k → $192,656 net (+671%), MDD 9.4%, Sharpe 2.1, vs buy-and-hold +126% / MDD 37% / Sharpe 0.7. Third-party replications report decay | moderate-weak (bias use, not target) | A✓ |
| P10 | VWAP benchmark share | working paper citing a BofA survey | about 50% | weak-moderate | A |
| P11 | Anchored VWAP as S/R | Shannon; StockCharts; TrendSpider | definitions only | none | A |
| P12 | Gap fill rates by size | Tradeify; stockwirex; thetrading.tools; [B-new] Linnsoft | 77-85% (small) … 23% (≥ 1 ATR); prior close touched on 58.1% of 1,803 days | weak (no distance control) | A + B |
| P13 | Reversals after large opening moves in index futures | Grant, Wolf & Yu (2005), JBF 29(5):1311-1327, Nov 1987-Sep 2002 | Significant reversals, stronger after large *up* opens; significance sharply reduced after a bid-ask cost proxy | **strong** (peer-reviewed; small and costly) | A✓ |
| P13b | Gaps are *not* reliably filled; gap-day continuation | [B-new] Plastun, Sibande, Gupta & Wohar (2020), N. Am. J. Econ. & Finance 52:101177 (DJI, S&P 500, NASDAQ 1928-2018); Caporale & Plastun (2017), Investment Analysts Journal 46(4) | Prices move in the gap's direction on the gap day; momentum is temporary; "contrary to the myth that price gaps tend to get filled". 2017: stocks, FX, commodities 2000-2015, efficient except FX | moderate (peer-reviewed, not distance-matched) | B (abstracts) |
| P14 | Overnight drift and opening reversal | Boyarchenko, Larsen & Whelan (NY Fed) | The opening reversal is weakly related to the overnight move | moderate | A |
| P15 | Option-strike pinning | Ni, Pearson & Poteshman (2005); Golez & Jackwerth (2012); Elms (2026); [B-new] Cboe 0DTE note | 1992-2009 at least $115 m per expiry; none 2016-2025; 0DTE hedging 0.04-0.17% of ES liquidity | strong (historical); moderate (current absence) | A✓ + B |
| P16 | CME ES settlement procedure | CME settlement-time FAQ (2020) | 30-second VWAP ending 15:00 CT from 26 Oct 2020 (previously 15:15 CT) | strong (exchange document) | A✓ (date and time); SER id not re-checked |
| P17 | 52-week-high anchoring | George & Hwang (2004); Li & Yu (2012) | Monthly-horizon momentum; Dow nearness to its 52-week high predicts higher returns, nearness to its historical high lower returns | strong (wrong horizon for the DOL) | A✓ via siblings |
| P18 | 52-week extremes are volatility barriers | [B-new] Driessen, Lin & Van Hemert (2013), Review of Finance 17(1):369-401 | Implied volatility and beta fall on the approach; variance +19% / +43% the day after a high / low break | strong (volatility, not reach) | B (abstract and WP) |
| P19 | Round-number barriers in indices and gold | [B-new] Donaldson & Kim (1993) JFQA 28(3):313-330; Aggarwal & Lucey (2007) RFE 16:217-230; O'Connor & Lucey (2016) | DJIA 1952-1990 barriers (Australia none); gold barriers at 00 (silver none) | strong (barrier / variance effects, not magnets) | B |
| P20 | Round-number clustering in BTC | [B-new] Urquhart (2017) Econ. Letters 159:145-148; Lee & Seong (ICIS 2019) | Over 10% of prices end in 00, no return pattern after rounds; barriers at 1,000 / 10,000 | moderate | B |
| P21 | CME crypto futures 24/7 | [B-new] CME press release (1 Jun 2026); trade press | Live from 29 May 2026 for nine crypto assets; no new weekend gaps | strong (exchange) | B |

### 2.2 Own tests: method

- **Data** (shared with the sibling studies):
  - CME 1h futures (ES, NQ, RTY, YM, GC, CL), Mar 2025-Apr 2026, about 1,500 Globex days;
  - CME 1-minute data for the 4 index futures, Jan-Apr 2026;
  - BTC/USD Bitstamp 1h, Jan 2016-Jan 2025 (79,057 bars, about 3,290 days);
  - daily SPX/NDX 1999-2018 and BTC daily.
- **Baseline (A):** the engine ledger's. A level at distance d (ATR14 units) on side s counts as hit if touched within H bars. The baseline is P(max H-bar excursion on side s ≥ d), from the instrument's empirical excursion surface, matched to the hour of day (T4/T5/T8) or taken at day-start bars (T1).
  - Touch rule: touch for references; strict trade-through for pools.
  - SE clustered by day.
- **Placebos (A):** range-scaled levels (T1); 13 random prices in the prior *day* range ±50% (T5/T8); daily pivots shifted by ±U(0.08, 0.2)R (T5); TWAP for VWAP (T4).
- **[B-test] B's additions** (`classic_b_tools/t8b_path.py`, `t8c_path.py`, `t8b_an*.py`, `t8c_an.py`, `t1b_daystart.py`). Same pools (1h swings 5/5 plus PDH/PDL/PWH/PWL, 0.5-6 ATR away, age ≤ 500 bars, strict sweep), same checkpoints every 2 bars, same H (8 and 24), same day clusters as A's T8.
  1. **Weekly-scale placebos:**
     - `WSH`: the 3 weekly pivots each shifted by ±U(0.12, 0.25)·R_week;
     - `WSTALE`: the weekly PP/R1/S1 of 3 weeks earlier;
     - `WGRID`: 3 uniform random prices in [PWL − 0.25R, PWH + 0.25R].
  2. **Controls:**
     - week-move sign (close − weekly open, toward the pool);
     - 24-bar momentum toward the pool;
     - `lvr` = ln(ATR14/ATR200);
     - `dw` = distance / prior-week range;
     - `inPW` = price inside the prior week's range.
  3. **Two alternative baselines with the surface rebuilt in that unit:**
     - `pbU`: REG-1's blended unit √(ATR14·ATR100);
     - `pb3`: a three-term unit (ATR14·ATR100·R_week)^(1/3). A constant factor does not change an empirical surface.
  4. **Offset logit** logit P(hit) = logit(baseline) + Xb, with day-clustered sandwich SEs.
  5. **A's T1 re-run** with the blended-unit baseline.

### 2.3 Own tests: A's results (condensed, with B's annotations)

**T1. Daily-derived levels from the session open, 1h bars.** CME at H24, n ≈ 1,400-1,530 per level. Edge in pp (z), ATR14 baseline (A) → blended-unit baseline (B4):

| Level | CME ATR14 | CME blended | BTC ATR14 | BTC blended |
|---|---|---|---|---|
| SETT (prior 16:00 ET close) | **+3.46 (3.7)** | **+3.45 (3.7)** | n/a | n/a |
| CPR_BC (= dayEQ) | **+3.95 (3.6)** | **+3.96 (3.6)** | +0.31 | +0.47 |
| CPR_TC | +2.34 (2.5) | +2.09 (2.3) | **+1.88 (3.2)** | **+2.13 (3.6)** |
| PP | +2.34 (2.2) | +2.27 (2.2) | +1.47 (2.1) | +1.73 (2.4) |
| PD_VWAP | +2.76 (2.5) | +2.84 (2.6) | +1.17 | +1.41 (1.9) |
| PDOPEN | +1.92 | +2.13 | -0.33 | -0.36 |
| R1 / S1 | -0.12 / -0.48 | -0.08 / +0.03 | -1.51 / -1.10 | -1.94 / -1.40 |
| R2 / S2 | **-2.98 (-3.1)** / -0.69 | -2.97 (-3.1) / -0.07 | +0.81 / +0.98 | +0.67 / +1.01 |
| CAM H3 / L3 | +0.57 / -0.26 | +0.39 / -0.18 | +0.06 / -0.63 | 0.00 / -0.64 |
| CAM H4 / L4 | +0.31 / -1.16 | +0.48 / -0.57 | -1.23 / -0.51 | -1.73 / -0.89 |
| FIB R1 / S1 | +0.88 / -0.59 | +1.08 / -0.49 | -2.09 / -2.31 | -2.27 (-2.9) / -2.64 (-3.3) |
| NAKED_PP | +0.77 (n 345) | +0.04 | -0.98 | -0.77 |
| W_AVWAP / M_AVWAP | +2.30 / +0.63 | +2.42 / +0.91 | **-2.94 / -2.78** | -2.56 / -2.35 |
| Placebo PP ± 0.15R | +2.54 / +1.96 | +2.53 / +1.87 | +1.01 / +1.04 | +1.23 / +0.83 |
| Placebo close ± 0.15R | +0.37 / +0.99 | +0.48 / +0.72 | -0.01 / -0.03 | -0.06 / +0.18 |

- At H8 on CME the value levels hold: SETT +3.60 (z 2.6), PP +3.06 (2.6), CPR_BC +3.13 (2.8). R2 -1.48 (z -3.6).
- The terminal test (do moves end at the level more often than at a random one?) is null. On BTC, touched PDH/PDL overshoot *more* (stop-run continuation).
- **Multiple testing:** about 50 level series per dataset. A Bonferroni cut at |z| ≈ 3.3 keeps CME SETT, CME CPR_BC and BTC CPR_TC (all three about 3.6-3.7).

**T2. HTF levels on daily bars** (SPX + NDX 1999-2018, BTC 2016-2025; edge pp at H = 5 / 20 days). B did not re-run it; it uses an ATR14 baseline, which REG-1 keeps on daily charts.

| Level | H5 | H20 |
|---|---|---|
| QOPEN | **-1.88 (-3.8)** | **-4.08 (-3.2)** |
| MOPEN | -1.03 | **-3.22 (-3.0)** |
| YOPEN | -0.89 | +0.70 |
| WOPEN | +1.13 | -0.56 |
| M_PP | **-1.75 (-3.0)** | **-3.28 (-2.8)** |
| W_PP / W_R1 / W_S1 | +0.62 / +0.14 / +0.50 | -0.42 / -0.61 / -0.27 |
| PMH / PML | +0.28 / +0.33 | -3.55 (-2.1) / +1.80 |
| PQH / PQL; PYH / PYL | about 0 | -2.85 / -0.44; +1.31 / -1.52 |
| 252dH / 252dL; 60d; 20d | ±0.7 | ±0.9 |

**T3. Gap fill vs a distance-matched random level.**
- NDX cash 2003-2018, ≥ 0.5 daily ATR: 30.6% vs 22.7% (**+7.9 pp, z 4.5, n 700**).
- Pooled SPX + NDX gap-downs ≥ 0.5 ATR: +12.0 (z 4.9); gap-ups +0.3.
- 0.25-0.5 ATR: +2.3 (z 1.6); < 0.25 ATR: +1.2.
- CME RTH gaps (n 218): +4.5 ± 4.8, inconclusive.
- Sibling ICTPD-6 B, CME session-break gaps ≥ 0.5 ATR: +7.4 pp (z 2.2). Small NDOGs: +0.7.

**T4. Session VWAP, 1h, H8.**

| | CME | BTC |
|---|---|---|
| Frozen VWAP | +1.51 (z 2.9) | +0.28 |
| Frozen TWAP | +2.89 (z 5.2) | +0.11 |
| Moving VWAP minus moving TWAP | +8.5 to +10.7 | +1.1 to +4.6 |
| ±2σ bands | about 0 | -1.70 / -1.44 (z -4.3 / -3.7) |

**T5. Confluence, pools within 0.35 ATR of an anchor** (flagged minus unflagged, distance-bucketed, day-cluster bootstrap; ATR14 baseline):

| Anchor family | CME H24 | BTC H24 |
|---|---|---|
| Engine pools PDH/PDL/PWH/PWL | **-4.78 (-3.6)** | -1.14 |
| Engine EQ / midnight / London opens | +0.57 | -2.62; H8 -3.25 (-3.6) |
| Daily pivots (13 levels) | +3.69 (3.6) | -0.82; H8 -1.84 (-4.4) |
| Weekly pivots | **-6.08 (-4.3)** | **-3.75 (-3.9)** |
| Weekly / monthly opens | **-7.43 (-3.9)** | **-4.48 (-4.0)** |
| Value levels (2% of pools flagged) | +2.65 | -1.68 |
| Round numbers | -1.38 | -1.00 |
| Placebo | +2.04 | +0.27 |

[B] The daily-pivot sign flips between markets. The weekly-pivot result is partly generic: at-pool weekly-scale placebos are negative too (B6).

**T6. CPR width → next day** (n 8,699 days):
- After a narrow CPR the next range is 0.919 ATR; after a wide one, 1.102.
- Trend days: 34.6% vs 37.7%.
- Controlling for the prior range, the CPR coefficient is +0.42 (BTC, t 5.2) and -0.27 (NDX, t -4.2): inconsistent.

**T7. "Above the reference = bullish" vs geometry** (which of PDH / PDL is traded first):
- Geometry-only out-of-sample accuracy: 0.664 (CME, n 1,945) and 0.718 (BTC, n 3,227).
- Adding the side of PP, VWAP, weekly AVWAP, weekly open or monthly open changes Brier by -0.0006 to +0.0061: no gain.

**T8 (A). References strictly between price and the pool** (stratified distance × outside-PD × outside-PW × age × source; ATR14 baseline):
- Weekly PP/R1/S1: CME -6.23 (z -5.3), BTC -5.43 (z -6.9).
- Weekly open: -2.13 / -3.08.
- Monthly open: -7.13 / -0.53.
- Daily pivots, Camarilla, 3 daily-scale placebos: null.
- Raw dose-response for weekly pivots (0 / 1 / 2 / 3 crossed): CME -1.7 / -5.3 / -9.4 / -10.6; BTC +0.5 / -4.2 / -11.4 / -14.4.
- **[B-fix] This dose-response is raw. The count of weekly pivots crossed correlates 0.64 (CME) / 0.47 (BTC) with distance in weekly-range units, which carries its own strong gradient (B2). See B1-B3.**

### 2.4 Own tests: B's results [B-test]

**B1. A's estimator with weekly-scale placebos** (ATR14 baseline; "≥ 1 between vs none", A's strata):

| Between price and pool | CME H24 | BTC H24 | CME H8 | BTC H8 |
|---|---|---|---|---|
| Weekly PP/R1/S1 (real) | -6.25 (z -5.3) | -5.45 (z -7.1) | -3.46 (-5.9) | -2.03 (-5.9) |
| Weekly PP only | -4.55 (-3.8) | -5.91 (-6.9) | n/a | n/a |
| **Shifted pivots (WSH)** | **-6.34 (-5.5)** | -3.59 (-4.8) | -2.88 (-5.2) | -1.66 (-4.8) |
| **Stale pivots, 3 weeks old (WSTALE)** | **-5.54 (-4.9)** | -3.36 (-3.4) | -2.77 (-5.0) | -1.03 (-2.4) |
| **Random levels in prior-week range (WGRID)** | **-6.70 (-6.1)** | -2.51 (-3.2) | -3.08 (-6.0) | -1.00 (-2.7) |
| Weekly open | -2.21 (-1.8) | -3.18 (-3.5) | n/a | n/a |
| Monthly open | -7.10 (-5.7) | -0.50 | n/a | n/a |

- Adding the week-move sign and 24-bar momentum as extra strata barely moves anything (CME real -5.91, grid -6.20). Trend is not the confound.
- When the weekly PP lies between price and pool, the pool sits against the week's move 63-66% of the time vs 37-44% otherwise, yet stratifying on that sign leaves the estimate unchanged.

**B2. What the generic part is** (pool edge vs the ATR14 baseline, H24):

| | CME | BTC |
|---|---|---|
| By ATR14/ATR200 quintile (low → high) | +3.3, -0.5, -3.9, -7.3, -9.9 | +10.0, +3.3, -1.5, -6.7, -11.7 |
| By distance in prior-week-range units (≤ 0.1, 0.1-0.2, 0.2-0.35, 0.35-0.5, 0.5-0.75, > 0.75) | +3.5, +0.2, -2.5, -5.8, -6.8, -9.5 | +5.1, +2.3, -1.9, -6.0, -10.2, -12.3 |

- Offset logit with distance buckets, outD, outW, key / swing, age, `lvr`, `dw`, `inPW`, week move and momentum: real weekly pivots crossed are **-0.041 (t -0.6) on CME** and -0.100 (t -2.0) on BTC.
- By level type with placebos: BTC weekly PP -0.21 (t -3.3); CME monthly open -0.26 (t -2.6); BTC monthly open +0.13 (t +1.7).

**B3. Three baselines on the same pool events** (log-loss of the baseline alone; then the residual coefficients):

| Set | ATR14 (engine today) | Blended √(ATR14·ATR100) (REG-1) | 3-term (+ prior-week range) |
|---|---|---|---|
| CME H24 | 0.5506 (base 36.2% vs hit 32.6%) | 0.5420 (35.4%) | **0.5380** (34.6%) |
| BTC H24 | 0.5435 (32.2% vs 30.9%) | 0.5296 (32.0%) | **0.5277** (32.3%) |
| CME H8 | 0.3166 (17.1% vs 14.1%) | 0.3087 (16.6%) | **0.3064** (16.4%) |
| BTC H8 | 0.3379 (14.9% vs 14.3%) | **0.3316** (15.0%) | 0.3326 (15.5%) |

- The blended unit improves the pool-event log-loss by 1.6-2.6%, which confirms REG-1 on a new event type.
- The 3-term unit adds a further -0.7% (CME H24 and H8) and -0.4% (BTC H24), but **+0.3% on BTC H8** (worse). It is a scorecard candidate, not a default (CL-7).
- **Residual coefficients** against the 3-term baseline, with placebos and all controls:

  | Term | H24 | H8 |
  |---|---|---|
  | Real weekly pivots, CME | -0.006 (t -0.1) | -0.06 (t -0.9) |
  | Weekly PP, BTC | **-0.185 (t -2.9)** | **-0.169 (t -2.6)** |
  | Weekly R1/S1, BTC | +0.02 | +0.03 |
  | Weekly open (both markets) | -0.03 to -0.05 (ns) | -0.03 to -0.05 (ns) |
  | Monthly open, CME | -0.26 (t -2.6) | -0.28 (t -2.5) |
  | Monthly open, BTC | +0.14 (t +1.9) | +0.16 (t +2.2) |
  | WGRID placebo, CME | -0.16 (t -3.1) | -0.11 (t -1.8) |

- The CME WGRID residual reads as *path overlap with the prior week's balance area*, which is the AMT path cost the engine already models with `f_pathVol`.
- Against the blended baseline with A's estimator: real weekly pivots CME -3.27 (z -2.8) vs placebos -3.6 to -4.7. BTC real -3.10 (z -4.0), weekly PP -4.08 (z -4.8), vs placebos -0.6 to -1.6.

**B4. T1 re-run with the blended unit:** see the T1 table. The value effect is unchanged, so it is not a unit artefact.

**B5. Pool edge by source under each baseline** (pp, z):

| Source | CME H24 ATR14 / blended / 3-term | BTC H24 ATR14 / blended / 3-term |
|---|---|---|
| Swing pools | -3.24 / -2.50 / -1.86 | -1.04 / -1.13 / -1.44 |
| PDH/PDL | -3.35 / -2.50 / -1.79 | -1.58 / -1.40 / -1.69 |
| PWH/PWL | **-6.90 / -5.40 / -3.82** | -1.71 / **+0.45 / +1.13** |

H8 has the same pattern: CME PW -4.33 / -3.44 / -2.75; BTC PW -0.04 / +1.26 (z 2.6) / +1.48 (z 3.1). **The engine's PW tier (0.92, highest) is contradicted on CME and mildly supported on BTC**, so it is market-specific. Let the ledger learn it (CL-3).

**B6. Confluence ("at the pool", within 0.35 ATR) vs the blended baseline:**

| Flag | CME H24 | CME H8 | BTC H24 | BTC H8 |
|---|---|---|---|---|
| Weekly pivot at the pool | -4.22 (-3.2) | -2.35 (-3.1) | -1.92 (-2.0) | -0.96 (-1.9) |
| Shifted-pivot placebo at the pool | -2.94 (-1.9) | -2.40 (-3.2) | -0.32 | -0.28 |
| Random weekly-range placebo at the pool | -2.05 (-1.3) | -1.70 (-2.2) | -2.61 (-2.5) | -0.54 |
| **Weekly or monthly open at the pool** | **-6.25 (-3.2)** | **-4.22 (-4.6)** | **-3.39 (-2.8)** | **-1.61 (-2.7)** |

**Limitations (A + B):**
- 1h bars only; H = 8 and 24. Behaviour on 1-5 minute charts with H = 30 is untested.
- CME covers 13 months; BTC is a single 24/7 asset.
- The surfaces are fitted in-sample on the full sample (as in A), so B3's unit comparison has one fixed functional form and no tuned parameter. REG-1 B's 2-fold out-of-sample test supports the blended unit; the 3-term unit is not tested out of sample.
- Many tests were run. Treat |z| < 3 results that are not replicated across both markets and both horizons as exploratory.

### 2.5 Synthesis: what each classic level is

- **Weak "prior value" magnets near price (real, small, robust to the unit):**
  - prior settlement, prior-day mid / CPR / PP, prior-day VWAP: +1.5 to +4 pp;
  - mean reversion toward the prior session's value over 8-24 h.
- **Distance only:**
  - daily floor / Camarilla / Fibonacci / Woodie / DeMark pivots;
  - weekly pivots as levels;
  - prior month / quarter / year and 52-week / N-day extremes;
  - naked pivots;
  - small gaps.
- **Below distance:**
  - quarterly / monthly opens and monthly pivots (daily bars);
  - BTC anchored VWAPs and ±2σ bands;
  - BTC Fibonacci R1/S1.
- **Barrier-like, market-specific, small:**
  - BTC weekly PP (-0.17 to -0.19 logit);
  - CME monthly open (-0.26, opposite sign on BTC).
  - Mechanism candidates: P1 / P2 (resting depth at watched levels).
- **Generic geometry, not level-specific:**
  - "levels between price and target" on the weekly scale is the volatility unit plus distance in prior-week-range units plus prior-balance path overlap.
- **Negative at a pool:** period opens; weekly levels; round numbers (mild).
- **Folklore refuted:** narrow CPR → trend day; above / below reference = bullish beyond geometry; "most gaps fill"; any classic level as a positive confluence.

---

## 3. Engine gap analysis (baseline_v2.pine line numbers)

| Concept | Status | Lines | What the engine does / differs |
|---|---|---|---|
| PDH/PDL pools | present | 104, 945, 952-961, 1790-1794 | Chart-TF `f_rangeTrack(timeframe.change("D"))`, exact print bar, registry src 6, strict sweep. Consistent with the evidence (distance-level). Known overhaul issue: on D charts every bar becomes a PDH/PDL pool. [A✓] |
| PWH/PWL pools | present | 105, 946, 1795-1799 | src 7, tier 0.92 (highest). [B-fix] Measured edge: worst source on CME, neutral to best on BTC (B5). Market-specific. |
| Source tier in density | partial / unsupported | 506-516 (`f_tierW`), 682 (`1.2*tier`) | PW 0.92 > PD 0.80 > HTF 0.65 > sessions 0.55-0.60 > STF 0.45 > chart 0.25, worth up to about +0.8 in the density exponent. Inconsistent across markets (B5); calib_ml: unsupported after Holm. Learn it per chart (CL-3 TIER bit); no hand reorder. |
| Confluence pillar | **wrong** | 139 (`confATR` 0.35), 143 (`wConf` 15), 220-222, 963-968, 674-680 (`conf = min(1, 0.35*hits)`), 1930-1934, 1986 (`oKey`), 2208 (tooltip) | Rewards overlap with aPDH, aPDL, aPWH, aPWL, dayEQ, midOpen, ldnOpen, nyOpen and htfEQ. No anchor family is positive (T5, B6). [B-new via calib_ml CAL-5] **Self-confluence**: key pools are pushed at exactly their own anchor prices (1793-1799 vs 957-960), so each gets conf ≥ 0.35, about +5.25 points (10.5 when PDH = PWH). → CL-2 |
| Daily floor / Camarilla / Fibonacci / Woodie / DeMark pivots | missing (correct) | grep finds only swing `ta.pivothigh` / `ta.pivotlow` (709, 879) | No reach edge, no barrier, no bias value. Display only (CL-6, via `ta.pivot_point_levels`). |
| Weekly pivots / weekly open as barriers | missing (**correct**) [B-fix] | n/a | A's CL-1 would add them. B: not level-specific on CME; small BTC weekly-PP residual only. Measure via CL-3 instead. |
| Volatility unit of the reach surface | wrong (sibling REG-1) | 1284-1322 (`f_empPoT`, `f_potModel`, `f_potBase`), 1527-1532 (surface update), 665 (proximity reach) | ATR14 unit: pool edge spans about 13-22 pp across ATR-ratio quintiles (B2). REG-1's blended unit fixes most of it; the weekly-range term is a further candidate (CL-7). |
| Weekly / monthly / quarterly / yearly opens | missing (only intraday opens as anchors) | 964-966 (`f_sessOpen`), 1931 | Opens at a pool are negative 4/4 (B6). Q / M opens below random on daily bars (T2). Keep them out of anchors and targets. |
| Prior month / quarter / year H/L | missing | `f_rangeTrack` only for D and W (945-946) | Baseline reach (T2). Optional Swing-mode completeness: CL-5. |
| 52-week / ATH / N-day extremes | missing | n/a | Baseline at DOL horizons; volatility barriers (P18). If siblings add them (ACAD-5/6, ICTPD-5), tier ≤ PD. |
| Prior settlement / prior-day value | **missing as a target**; `dayEQ` (967) is an anchor only | 963-968, 1931 | Value levels: +2 to +4 pp vs random, robust to the unit (B4). → CL-4 |
| Opening gaps | missing | n/a | Large gaps only (T3, ICTPD-6 B); one object with CL-4. |
| Session VWAP / bands / AVWAP | missing (correct as targets) | grep "vwap": none | A moving target inflates the ledger edge against a static baseline. Display only (CL-6). |
| Round numbers | missing | n/a | Sibling OF-4 / ICT-3 (cap wicks at rounds). Never a positive anchor. CL-3 bit. |
| Path cost | partial | 1404-1414 (`f_pathVol`), 1944-1947 (×1.10 / ×0.85) | Volume-profile path only. B's CME residual (path through prior-week balance) is the same kind of effect. No extra reference-level barrier. |
| PoT readout | present | 1302-1311 (`f_potModel`), **2067** (`activePoT`; A wrote 2066) | No reference terms; correct after B's re-test. Drift term: sibling QPOT-01. |
| Ledger families | present (coarse) | 635-636 (`grp`), 543-548 (`f_grpName`), 1066-1071 (`array.new(5)`), 1314-1322 (`f_potBase`), 1376-1383 (`f_calMult`, ALL = index 4 at 1380-1381), 1426-1431 (`f_openTrial`), 1461-1500 (`f_book`, `array.from(t.grp, 4)` at 1470), 2375-2403, 2411, 2443 | The random-level baseline is the right estimator. Only the active target opens trials (2045), so per-feature learning needs the candidate ledger (CAL-3) or per-trial bits. Adding a family means moving "ALL" from index 4 to 5 at every listed line (use a `const int GALL`). |
| Array delivery for reference lines | n/a today | 1566-1577 | Any new touch-semantics line kind (8/9) would be cropped by the CE-delivery code. Guard with `lv.kind <= 7` (CL-4). |
| Above / below-reference bias | n/a (correctly absent from D) | draw vector | T7: no value beyond geometry. Do not add. |
| Request budget | 6 of 40 used | 923-925, 939, 981-982 | One settlement request (CL-4) is affordable. |

---

## 4. Proposals (best first)

**A's CL-1 (weekly-reference path barrier in score and PoT) is withdrawn.** See 0.1 and §5. Its measurement part survives in CL-3, and its generic part in CL-7 / REG-1.

### CL-2 (P1, scoring, S) · Neutralise the Confluence pillar, remove self-confluence, and never add reference levels as positive anchors [A + B amended]
- **Why:**
  - No anchor family raises the sweep rate (T5).
  - Opens at a pool lower it in 4/4 sets under the better baseline (B6).
  - The weekly levels and round numbers that siblings proposed as anchors are negative.
  - calib_ml: the pillar is unsupported after multiplicity correction.
  - Key pools receive confluence from their own print (about +5 points), double-counting the tier they already get in density (682).
  - Together, 15/100 of the score tilts selection toward pools that are not more likely to be taken.
- **Spec:**
  1. `wConf` (143): default **15 → 0**. Keep the input with `display = display.none`. Tooltip: "Overlap with reference levels was measured not to raise reach (study: classic levels T5/B6); 0 by default."
  2. Rescale the thresholds so behaviour for conf = 0 levels is unchanged. With wConf = 0, `wSum` (304) falls from 100 to 85 and every conf = 0 score rises by 100/85 = 1.176:
     - `minScore` (146): 35 → **41**;
     - `hyst` (147): 4.0 → **4.7**.
     - The `kzHx` multiplier (163, 976) and the 2× side-flip rule (2012) scale automatically.
  3. Step 17 (1930-1934): wrap the anchor build in `if wConf > 0`. Otherwise pass an empty array: `evaluate`'s loop (677-679) then costs nothing and `conf` stays 0.
  4. If a user re-enables `wConf`, apply calib_ml **CAL-5**: fixed anchor slots with own-print exclusion, `own = this.src >= 6 and k <= 3 and math.abs(a - this.price) <= syminfo.mintick`. Drop `midOpen`, `ldnOpen`, `nyOpen` (measured neutral to negative) from the default slots.
  5. Hide "Confluence" in the score-breakdown tooltip (2208) when `wConf == 0`. The HTF-objective key (`oKey`, 1986) is unaffected (its term is 0).
  6. README "How a level is scored": replace the Confluence row with "Confluence (default off): overlap with reference levels was tested and does not raise reach; reference levels are not used as score bonuses."
  7. Never push weekly pivots, weekly / monthly opens, round numbers or daily pivots into `anchors`.
- **Ledger check:** the share of DOLs by family before and after; EDGE; the TIER bit of CL-3.
- **Evidence:** moderate (A's T5 on 2 markets × 2 horizons; B6 under a better baseline; calib_ml independent regression; the self-confluence bug is certain from code reading).
- **Risk:**
  - Scores shift; the threshold rescale contains it.
  - Arrays (FVG/OB) also lose confluence credit, which was not tested in this domain; the per-family `f_calMult` still adapts.
- **Effort:** S (about 10 lines).

### CL-4 (P2, level-source, M) · Prior-session value target ("Target: D-PIV / D-EQ / SETT"), optional gap gate, one object with ICTPD-6 [A's CL-4, widened by B]
- **Why:**
  - The only classic levels reached more often than random from the session start are the prior session's *value* levels (T1, B4, survives the unit change):
    - CME SETT +3.45 pp (z 3.7), D-EQ +3.96 (z 3.6), PP +2.27; repeated at H8;
    - BTC PP +1.73 (z 2.4), CPR TC +2.13 (z 3.6).
  - Liquidity pools at matched distance score -2.5 pp (CME) and -1.2 pp (BTC). So when a value level and a pool sit at similar distances, the value level is the better bet.
  - Large gaps add more: NDX +7.9 pp; CME futures ≥ 0.5 ATR +7.4 pp (sibling).
  - In ICT terms the prior day's 50% (D-EQ) is the daily equilibrium, a recognised draw, so the target fits the product's vocabulary.
- **Inputs** (G_KEY, all with `display = display.none`):
  - `bool useVal = input.bool(false, "Prior-Session Value Target")`
  - `string valSrc = input.string("Pivot", "  Level", options = ["Pivot", "Day EQ", "Settlement"])`. "Pivot" = (H + L + C)/3 of the prior daily bar: positive in both markets. "Day EQ" = `dayEQ`: strongest on CME, weak on BTC. "Settlement" = prior daily close with `settlement_as_close.on`: CME-tested.
  - `float valGap = input.float(0.0, "  Min Open Gap (x daily ATR)", minval = 0.0, step = 0.05)`. 0 = every session; 0.5 = A's gap-fill mode (largest measured effect on cash indices).
- **Series** (after 968; one new request, 6 → 7 of 40):
  ```pine
  string tkSet = ticker.modify(syminfo.tickerid, settlement_as_close = settlement_as_close.on)
  [dC1, dH1, dL1, dAtr1] = request.security(tkSet, f_tfSafe("D"), [close[1], high[1], low[1], ta.atr(14)[1]], lookahead = barmerge.lookahead_on)
  bool dNew   = timeframe.change("D")           // global scope, every bar
  bool valOK  = useVal and timeframe.isintraday and not na(dC1) and not na(dAtr1) and dAtr1 > 0
  ```
  - Doc basis: `ticker.modify(... settlement_as_close)` "specifies whether a futures symbol's close value represents the actual closing price or the settlement price on "1D" and higher timeframes". On non-futures symbols it is the ordinary daily close.
  - The `[1]` + `lookahead_on` pattern is the engine's non-repainting standard.
- **Engine, new step 12c** (confirmed bars, next to the key-liquidity pushes 1790-1799):
  ```pine
  if valOK and dNew
      float vPx = valSrc == "Settlement" ? dC1 : valSrc == "Day EQ" ? (dH1 + dL1) / 2.0 : (dH1 + dL1 + dC1) / 3.0
      float gD  = math.abs(open - dC1) / dAtr1
      float dV  = math.abs(vPx - close) / atr
      if gD >= valGap and dV >= minDistATR and dV <= maxATR
          float hw = 0.05 * atr
          nextId += 1
          Level vl = f_newLevel(nextId, vPx > close ? 8 : 9, 14, vPx + hw, vPx - hw, vPx, bar_index, bar_index, 0.0, 0.0)
          vl.qual   := valGap > 0 ? math.min(1.0, gD / 1.5) : 0.6
          vl.hlMult := math.sqrt(math.max(1.0, 86400.0 / chartS))
          pool.push(vl)
  // expiry: at the next dNew, remove any src-14 level still in the pool (one loop over pool)
  ```
- **Code touch points**, shared with ICTPD-6, which uses kinds 8/9 and src 11-13:
  - `f_newLevel` side map (1085): add `or kind == 8`. Kind 8 = above price, 9 = below.
  - `touched()` (623-624) already uses touch semantics for kind ≥ 2.
  - Delivery block 1566: add `and lv.kind <= 7` so a 0.1-ATR line is not CE-cropped.
  - `grp()` (635-636): kinds 8/9 → **new family 4 "REF"**:
    - `f_grpName` gains `4 => "REF"`;
    - STATE arrays 1066-1071 go from size 5 to 6;
    - "ALL" moves to index 5 at 1380-1381, 1470, 2375-2403 and 2443;
    - the Full-view loop at 2411 becomes `for g = 0 to 4`.
    - Introduce `const int GALL = 5` to remove the magic number.
    - If ICTPD-6 lands first with family 2, move its kinds to family 4 too so gaps and value lines are graded together and apart from FVGs.
  - `f_levelName` / `f_shortName`: `8, 9 => src == 14 ? (valSrc == "Settlement" ? "SETT" : valSrc == "Day EQ" ? "D-EQ" : "D-PIV") : src == 12 ? "NWOG" : src == 13 ? "ORG" : "NDOG"`.
  - `evaluate`: arrays branch. Density = 0.5·qual (+ coil / induce); freshness half-life applies. No origin lockout (src ≠ 0). `f_kzAff` / `f_tierW` defaults are fine.
- **Ledger check:** the REF family EDGE against `pBase`. Expect about +2 to +4 pp on futures and about +1 to +2 on BTC. If the chart's REF edge is ≤ 0 after 100 trials, `f_calMult` (×0.8 floor) demotes it automatically.
- **Evidence:** moderate for a small value effect (2 markets, 2 horizons, robust to the unit; SETT, CME D-EQ and BTC CPR TC pass Bonferroni). Large-gap mode: moderate for cash indices, weak for futures. Published evidence is mixed (P13 reversal vs P13b gap-day continuation).
- **Risk:**
  - Overlap with ICTPD-6 / PA-2: build one object.
  - Tested only from the Globex / UTC day start on 1h bars.
  - A near value line (median 0.5-1.4 ATR) competes with pools inside `minDistATR`, and the taper limits it.
  - Off by default.
- **Effort:** M (about 40 lines plus the family re-index).

### CL-3 (P2, statistics-ledger, M) · Reference-context feature bits in the candidate ledger, **each graded against a phantom-level control** [A's CL-3, re-designed by B]
- **Why:**
  - B1-B3 show how easily a reference-level feature looks predictive when it merely proxies distance on a longer scale or the volatility state.
  - Per-chart lifts are still the right tool for the market-specific residuals: BTC weekly PP, CME monthly open, the PW tier.
  - Each such bit must ship with a **scale-matched phantom twin**. The readout shows the *net* lift (real ÷ phantom), not the raw lift that would have "confirmed" A's CL-1.
- **Spec** (on top of calib_ml CAL-3's candidate ledger; fallback: per-trial bits on active trials):
  - **Weekly references** (global, every bar; reuse `pwNew`, `pwH`, `pwL` from 946):
    ```pine
    var float wPP = na, var float wR1 = na, var float wS1 = na, var float wOpn = na, var float mOpn = na
    var int   wkIx = 0
    var float ph0 = na, var float ph1 = na, var float ph2 = na
    if pwNew
        float r = pwH - pwL
        wPP := (pwH + pwL + close[1]) / 3.0
        wR1 := 2.0 * wPP - pwL
        wS1 := 2.0 * wPP - pwH
        wkIx += 1
        // deterministic phantoms: 3 golden-ratio-spaced prices across [PWL - 0.25R, PWH + 0.25R]
        ph0 := pwL - 0.25 * r + 1.5 * r * ((wkIx * 0.6180339887) % 1.0)
        ph1 := pwL - 0.25 * r + 1.5 * r * ((wkIx * 0.6180339887 + 0.381966) % 1.0)
        ph2 := pwL - 0.25 * r + 1.5 * r * ((wkIx * 0.6180339887 + 0.763932) % 1.0)
    if timeframe.change("W")
        wOpn := open
    if timeframe.change("M")
        mOpn := open
    ```
    (Declare one variable per line in real code; the commas above are shorthand.)
  - **Bits per graded candidate**, with `tol = confATR·atr` and "between" = strictly between price + 0.1 ATR and near edge − tol:
    - `XWPP` = the weekly PP is between;
    - `XW` = count of {wPP, wR1, wS1, wOpn} between, capped at 2;
    - `XPH` = count of phantoms between, capped at 2 (**control**);
    - `ATO` = weekly or monthly open within tol of the level;
    - `ATPH` = a phantom within tol (**control**);
    - `ATRN` = round level within tol (OF-4 step);
    - `ATV` = PP / dayEQ / settlement within tol;
    - `TIER` = class 0-4 (chart, STF/HTF, session, PD, PW).
  - **Accumulators:** for each bit value, n, k and E = ΣpBase. Lift = ((k + 2)/(E + 2)) / ((K + 2)/(E_all + 2)), the `f_calMult` algebra (1376-1383). Readout **net lift** = lift(XW ≥ 1) / lift(XPH ≥ 1), and likewise ATO / ATPH. Show n and a delta-method 95% CI on log(net).
  - **Full view row:** `CTX  W-REF× 0.94 (412) · PHANTOM× 0.96 (390) → net 0.98 ±0.08 · OPEN@ 0.90 (120) · TIER PW 1.03`.
  - **Use:** display only by default. Optional: when n ≥ 200 for both twins and the net-lift CI excludes 1, multiply `lv.mult` by the net lift clamped to [0.85, 1.05], for XWPP / XW / ATO only.
- **Cost:** about 20 floats of state and O(8) per graded candidate. No `request.*`.
- **Evidence:** moderate for the method (B1-B3 show why the control is needed). The features themselves are weak / market-specific.
- **Risk:**
  - Multiple comparisons: show n and the CI; the default is display only.
  - Phantoms change weekly, so a single chart needs months of history to fill the cells.
- **Effort:** M (S if CAL-3 lands first).

### CL-7 (P3, probability, S) · Prior-week range as the third term of the reach unit: a scorecard candidate for REG-1 [B-new; replaces the useful part of A's CL-1]
- **Why:**
  - Even with REG-1's blended unit, distance measured in prior-week-range units keeps a strong gradient: about -1 logit per weekly range, t -3.7 to -4.2 (B2/B3).
  - Adding the weekly range as a third geometric term cut pool-event log-loss a further 0.7% on CME (H24 and H8) and 0.4% on BTC H24. It was 0.3% worse on BTC H8 (B3).
  - This is HAR logic: daily, weekly and monthly volatility components.
  - Since the benefit is mixed, it belongs in REG-1's unit options and TIME-4's per-chart PoT scorecard, not in the default.
- **Spec** (requires REG-1's `aU`, `atr100`):
  ```pine
  var float pwR = na
  var int   wBars = 0
  var int   wBarsPrev = na
  if pwNew
      pwR       := pwH - pwL
      wBarsPrev := wBars
      wBars     := 0
  wBars += 1
  float aW  = not na(pwR) and nz(wBarsPrev) > 0 ? pwR / math.sqrt(wBarsPrev) : na   // weekly range in per-bar scale (random-walk scaling)
  float aU3 = timeframe.isintraday and not na(aW) and nz(atr100) > 0 ? math.pow(atr * atr100 * aW, 1.0 / 3.0) : aU
  ```
  - Add "Blended + Week" to REG-1's `surfUnit` options, or run a parallel surface `sUp3` / `sDn3` (2 × 3 × 61 ints) as a TIME-4 candidate.
  - The `aW` normalisation keeps `aU3` about ATR-sized, so the surface grid (`bStep`, 307) keeps its resolution on every timeframe.
- **Evidence:** weak-moderate (in-sample, 2 markets × 2 horizons, mixed sign on BTC H8; the mechanism is strong).
- **Risk:**
  - The first week of history has no `pwR` (falls back to `aU`).
  - Holiday weeks give a short `wBarsPrev`.
  - Not tested on 5-15m charts.
- **Effort:** S on top of REG-1.

### CL-5 (P3, level-source, S) · Monthly high / low pools (PMH / PML) for Swing mode, tier no higher than PD [A, specs checked]
- **Why:**
  - In Swing mode (W / D / 4H) PDH/PWH are often already near or taken, and the monthly extremes are the external liquidity swing traders watch.
  - Reach is at baseline (T2: +0.3 pp at 5 days; -3.6 / +1.8 at 20 days): completeness, not edge.
- **Spec:**
  - `[pmNew, pmH, pmHB, pmL, pmLB] = f_rangeTrack(timeframe.change("M"))` next to 945-946 (global).
  - Input `useKeyM = input.bool(false, "PMH / PML", group = G_KEY, display = display.none)`.
  - Registry push like 1795-1799 with **src 9**: `regNew := f_pushExt(extReg, pmH, true, 9, pmHB, (pmH - pmL) / atr * 0.5, math.sqrt(math.max(1.0, 2592000.0 / chartS))) or regNew`, and the same for PML.
  - `f_tierW` (506-516): add `9 => 0.80`. The default would otherwise be 0.40, and it must not exceed PW (0.92).
  - `f_levelName` (520-521): `src == 9 ? "PMH"` / `"PML"`.
  - Anchors on low timeframes are clamped by `f_x` (404-405).
  - `f_kzAff` default 1.0.
  - Avoid src 11-14 (ICTPD-6, CL-4).
- **Evidence:** weak (neutral reach). **Risk:** low; the ledger grades it. **Effort:** S.

### CL-6 (P3, visual-ux, S) · Optional display-only reference overlay on `ta.pivot_point_levels` (and session VWAP), with honest tooltips [A, rebuilt by B]
- **Why:**
  - Traders look for pivots, Camarilla and VWAP, and competitors plot them.
  - A built-in now makes this one call.
  - Showing them with measured tooltips teaches users what the levels are (distance-only; value pull near PP / settlement) without polluting the score.
- **Spec:**
  - Inputs (G_DISP, `display = display.none`):
    - `refOv` = "Off" / "Daily" / "Weekly" / "Daily + Weekly" (default "Off");
    - `refType` = the six `ta.pivot_point_levels` types (default "Traditional");
    - `refN` = levels per side 1-3 (default 1: P, R1, S1);
    - `showVW` = Session VWAP (default false).
  - Global, every bar:
    - `array<float> pivD = ta.pivot_point_levels(refType, timeframe.change("D"))` and `pivW = ta.pivot_point_levels(refType, timeframe.change("W"))`;
    - store `bar_index` at each change as the line's left anchor;
    - `[vw, vwU, vwL] = ta.vwap(hlc3, timeframe.change("D"), 1.0)`;
    - `plot(showVW ? vw : na, "Session VWAP", color = cDim, display = display.pane)`.
  - Drawing on `barstate.islast` only: a `var array<line>` and `var array<label>` of at most 12 each, updated with `line.set_xy1/xy2` rather than recreated. Dotted, theme `dim` colours, right-edge tiny labels (W-PP, W-R1, …), never in Clean style unless chosen.
  - Tooltips:
    - pivots: "Classic pivot: reached at the rate its distance predicts (study). Not a target."
    - PP / settlement: "Prior-session value: reached slightly more often than distance predicts (+2-4 pp, futures)."
    - VWAP: "Moving benchmark; touches are partly mechanical."
- **Evidence:** n/a (UX). **Risk:** clutter (off by default; at most 12 drawings). **Effort:** S.

---

## 5. Do NOT add (evidence-based)

| Item | Why not |
|---|---|
| **Weekly-reference path barrier multiplier / PoT logit shift (A's CL-1)** [B-fix] | Weekly-scale placebos give the same "barrier" (B1). With unit and distance controls the real levels add ≈ 0 on CME; BTC weekly PP only -0.17 to -0.19 logit (B3). A hand multiplier would encode a geometry artefact. Measure it with CL-3 (phantom-controlled) and fix the generic part with REG-1 / CL-7. |
| Daily floor / Camarilla / Fibonacci / Woodie / DeMark pivots as targets or positive confluence | T1 / B4: placebo-like edges; terminal test null; T5 sign flips; P4, P6b. |
| Narrow-CPR trend-day rule | T6 reversed or inconsistent. |
| "Above pivot / VWAP / open = bullish" in D | T7: no out-of-sample gain over geometry. |
| Monthly / quarterly / yearly opens and monthly pivots as targets | T2: reached *less* than random. |
| Any period open as a confluence anchor | B6: negative at the pool in 4/4 sets. |
| Session VWAP as a static DOL target | Moving line: mechanical touches; frozen VWAP weak. Would need a moving-TWAP baseline. Display only (CL-6). |
| VWAP σ-bands, weekly / monthly AVWAP as targets | T4 / T1: null or negative (BTC -2.4 to -2.9 pp). |
| Naked / virgin pivots, naked POCs | T1 / B4 null; `amt_profile`: naked POC -2.3 to -4.7 pp. |
| 52-week / ATH with an elevated tier | T2 baseline; volatility barriers, not magnets (P18). Tier ≤ PD. |
| Round numbers as a positive anchor | T5 -1.0 to -1.4 pp; OF-4: wicks stop short. |
| Option-strike pinning / gamma levels | Needs open interest (not in Pine); absent since 2016 (Elms); 0DTE hedging is tiny (Cboe). |
| **BTC "CME gap" levels** [B-new] | Folklore without methodology; CME crypto is 24/7 since 29 May 2026, so no new gaps; it would also need an extra request. |
| Hand reordering of the PW / PD tier | B5: market-specific sign. Learn it (CL-3 TIER). |

---

## 6. Coordination with sibling proposals

- **REG-1 (quant_regime):**
  - B3 independently confirms the blended unit on pool-sweep events (log-loss -1.6% CME, -2.6% BTC at H24).
  - CL-7 is an option inside REG-1's unit / TIME-4 scorecard, not a separate model.
  - Any "levels between price and target" feature anywhere in the study should be re-tested against REG-1's unit and a scale-matched phantom.
- **calib_ml CAL-3 / CAL-5:** CL-3 is a feature list for CAL-3, with phantom twins added. CL-2 adopts CAL-5's own-print exclusion for users who re-enable confluence.
- **ict_pd ICTPD-6 (NDOG/NWOG) and price_action PA-2 (RTH gap):**
  - One object with CL-4: kinds 8/9, src 11 NDOG / 12 NWOG / 13 ORG / **14 VALUE**.
  - Size-gated gaps; target = the pre-break close or settlement.
  - Grade all of them in a separate ledger family "REF" (CL-4 touch points).
- **ict_liq ICT-3 / orderflow OF-4 (round numbers):** keep the zone cap at the round and stops beyond it. Never add rounds to anchors. CL-3 carries an ATRN bit.
- **academic_sr ACAD-5/6 and ict_pd ICTPD-5 (52-week / ATH / IPDA extremes):** fine as pools with `f_tierW` ≤ 0.80. Siblings found 20/60-day extremes at baseline, and 52-week extremes are volatility barriers.
- **ict_time TIME-6 (midnight open as a target):** already dropped by ict_time B (+0.3 ± 1.1 pp vs neighbouring opens). Opens are not anchors either (B6).
- **amt_profile (path cost):** B3's CME residual for paths through the prior week's range is the AMT "prior balance slows price" effect. It belongs in `f_pathVol` (volume profile), not in a pivot multiplier.

---

## 7. Reproduction

A's code is in `study/classic_tools/` and B's in `study/classic_b_tools/`. Run with `python3 -I`; CSVs are gzipped.

**A:**
- `mk_btc1h.py`: Bitstamp 1-minute → `btc_1h.csv`.
- `clib.py`: loaders, ATR, the excursion `Surface` baseline, the clustered `summ`.
- `t1_daystart.py <cme|btc> <H>`: daily-derived levels from the session open.
- `t2_htf.py <H>`, `t2_sum.py`: daily HTF levels.
- `t3_gaps.py`, `t3b.py`: gap fill.
- `t4_vwap.py <cme|btc> <H>`: VWAP, bands, TWAP, moving lines.
- `t5_confluence.py <cme|btc> <H>`, `t5_diff.py`: confluence.
- `t6_cpr.py`: CPR width.
- `t7_bias.py <cme|btc>`: reference-side bias vs geometry.
- `t8_path.py <cme|btc> <H>`, `t8_an.py`: path barriers.

**B:**
- `t8b_path.py <cme|btc> <H>`: A's T8 pools plus weekly-scale placebos (WSH, WSTALE, WGRID), trend and volatility controls, and the blended-unit baseline `pbU`.
- `t8c_path.py`: the same plus the 3-term-unit baseline `pb3`.
- `t8b_an.py <csv>`: A's stratified estimator on real vs placebo flags, plus offset logits.
- `t8b_an2.py <csv>`: unit / distance controls (B2).
- `t8b_an3.py <csv>`: B1 / B2 with `pbU` as the baseline.
- `t8c_an.py <csv>`: log-loss of three baselines, and logits against `pb3` (B3).
- `t1b_daystart.py <cme|btc> <H>`: T1 with the blended-unit baseline (B4).
- Outputs: `out_t8b_*`, `out2_*`, `out3_*`, `out_t8c_*`, `out_t1b.txt`.

---

## 8. Sources

**Verified by B through search summaries** (full texts were not reachable):
- Osler, C. (2000). Support for Resistance: Technical Analysis and Intraday Exchange Rates. FRBNY Economic Policy Review 6(2):53-68. https://www.newyorkfed.org/research/epr/00v06n2/0007osle ; https://ideas.repec.org/a/fip/fednep/y2000ijulp53-68nv.6no.2.html
- Kavajecz, K., Odders-White, E. (2004). Technical Analysis and Liquidity Provision. RFS 17(4):1043-1071. https://ideas.repec.org/a/oup/rfinst/v17y2004i4p1043-1071.html
- Grant, J., Wolf, A., Yu, S. (2005). Intraday price reversals in the US stock index futures market: A 15-year study. JBF 29(5):1311-1327. https://ideas.repec.org/a/eee/jbfina/v29y2005i5p1311-1327.html
- Golez, B., Jackwerth, J. (2012). Pinning in the S&P 500 futures. JFE 106(3):566-585. https://ideas.repec.org/a/eee/jfinec/v106y2012i3p566-585.html ; Elms (2026) summary: https://harbourfrontquant.substack.com/p/from-pinning-to-amplification-evidence
- Cboe, "Much Ado About 0DTEs". https://www.cboe.com/insights/posts/volatility-insights-evaluating-the-market-impact-of-spx-0-dte-options
- Johnsson, O., Frykmer, D. (2019). Pivot Point Trading in the Foreign Exchange Market. Lund MSc thesis. https://lup.lub.lu.se/student-papers/search/publication/8979805
- mypivots.com, "Do Pivot Points work?" https://www.mypivots.com/articles/articles.aspx?artnum=35
- Tian, X., Quan, C., Zhang, J., Cai, H. J. (2012). JILSA 4:279-284. https://www.scirp.org/html/24829.html
- Zarattini, C., Aziz, A. (2023). VWAP: The Holy Grail for Day Trading Systems. SSRN 4631351. https://concretumgroup.com/volume-weighted-average-price-vwap-the-holy-grail-for-day-trading-systems/ ; replication discussion https://www.quantconnect.com/forum/discussion/16706/
- CME Group, Daily Settlement Price Determination Time Change FAQ (2020). https://cmegroup.com/education/articles-and-reports/faq-daily-settlement-price-determination-time-change.html
- CME Group, 24/7 cryptocurrency futures and options (2026). https://www.cmegroup.com/media-room/press-releases/2026/6/01/cme_group_announceslaunchof247cryptocurrencyfuturesandoptionstra.html ; https://cmegroup.com/markets/cryptocurrencies/24-7-crypto-trading.html
- Plastun, A., Sibande, X., Gupta, R., Wohar, M. (2020). Price gap anomaly in the US stock market: the whole story. NAJEF 52:101177. https://ideas.repec.org/p/pre/wpaper/201963.html ; Caporale, G. M., Plastun, A. (2017). Price gaps: another market anomaly? Investment Analysts Journal 46(4):279-293. https://bura.brunel.ac.uk/handle/2438/14372
- Donaldson, R. G., Kim, H. Y. (1993). Price Barriers in the Dow Jones Industrial Average. JFQA 28(3):313-330. https://ideas.repec.org/a/cup/jfinqa/v28y1993i03p313-330_00.html
- Aggarwal, R., Lucey, B. (2007). Psychological barriers in gold prices? Review of Financial Economics 16:217-230. https://ideas.repec.org/a/eee/revfin/v16y2007i2p217-230.html
- Urquhart, A. (2017). Price clustering in Bitcoin. Economics Letters 159:145-148. https://ideas.repec.org/a/eee/ecolet/v159y2017icp145-148.html ; Lee & Seong (ICIS 2019) https://aisel.aisnet.org/icis2019/blockchain_fintech/blockchain_fintech/12
- Driessen, J., Lin, T.-C., Van Hemert, O. (2013). How the 52-week high and low affect option-implied volatilities and stock return moments. Review of Finance 17(1):369-401. https://ideas.repec.org/a/oup/revfin/v17y2013i1p369-401.html
- Linnsoft "homework" gap statistics. https://linnsoft.com/homework
- Gap-fill folklore for BTC CME gaps. https://cryptoslate.com/do-cme-gaps-always-have-to-fill-bitcoins-60k-flush-says-no/

**A's sources, not re-verified by B:**
- Osler (2003) J. Finance 58(5), FRBNY SR125 https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr125.pdf
- Bulkowski, Pivot Points https://thepatternsite.com/PivotPoints.html
- Steenbarger (TraderFeed 2007) https://traderfeed.blogspot.com/2007/10/pivot-level-support-and-resistance-how.html
- FXNX https://fxnx.com/en/blog/pivot-point-hit-rates-r1-s1-daily-pivot-tested
- Tradeify https://tradeify.co/education/pivot-points
- Edgeful https://www.edgeful.com/blog/posts/pivot-points-report-full-guide ; https://www.edgeful.com/blog/posts/weekly-open-retracement-report
- Barchart / LuxAlgo / takeprofitapp (Camarilla, CPR)
- Babypips pivot methods https://www.babypips.com/learn/forex/other-pivot-point-calculation-methods
- StockCharts / TrendSpider AVWAP
- VWAP benchmark share https://core.ac.uk/download/201501336.pdf
- Boyarchenko, Larsen & Whelan https://libertystreeteconomics.newyorkfed.org/2021/05/the-overnight-drift-in-us-equity-returns
- Lou, Polk & Skouras https://personal.lse.ac.uk/polk/research/TugOfWar.pdf
- stockwirex, thetrading.tools gap statistics
- Ni, Pearson & Poteshman (2005) https://ideas.repec.org/a/eee/jfinec/v78y2005i1p49-87.html
- George & Hwang (2004) https://www.bauer.uh.edu/tgeorge/papers/gh4-paper.pdf

**Pine v6 reference** (local mirror `docsrc/jabez4jc_pinescriptv6/reference/`):
- `ta.md`: `ta.pivot_point_levels()`, `ta.vwap()`.
- `ticker.md`: `ticker.modify()` with `settlement_as_close`.
- `session.md`: `session.isfirstbar_regular`.
- `writing_scripts/profiling_and_optimization.md`: "up to 40 unique calls to the request.*() family … or up to 64" on the Ultimate plan.

**Sibling studies used:**
- `calib_ml.final.md` (Holm-corrected lifts, CAL-3, CAL-5 self-confluence);
- `quant_regime.final.md` (REG-1 blended unit);
- `ict_pd.final.md` (ICTPD-6 gaps);
- `ict_liq.final.md` and `orderflow_micro.final.md` (round numbers, OF-4);
- `academic_sr.final.md` (52-week, Plastun);
- `ict_time.final.md` (midnight open);
- `bias_dol.final.md` (open-relative bias);
- `amt_profile.final.md` (naked POC, path cost).
