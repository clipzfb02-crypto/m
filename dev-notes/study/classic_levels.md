# Classic reference levels as liquidity: pivots, Camarilla, VWAP, period opens, prior-period extremes, settlement, gaps

Domain: floor pivots (classic, CPR), Camarilla, Fibonacci / Woodie / DeMark pivots; daily / weekly / monthly pivots and "naked" pivots; round numbers (brief, the sibling studies cover them); session VWAP, anchored VWAP (week, month, prior day) and deviation bands; daily / weekly / monthly / quarterly / yearly opens; previous day / week / month / quarter / year highs and lows; 52-week and N-day extremes; previous settlement / close; opening gaps; option-strike pinning. The question is the engine's: **which liquidity is reached next, how likely within H bars, and does a classic reference level change that?**

Method note. Firecrawl was unavailable (credits exhausted; refresh in about 21 h) and WebFetch could not reach thepatternsite.com or traderfeed.blogspot.com (outside the session's allowed network). Published evidence below therefore comes from WebSearch result summaries (secondary; numbers quoted as reported) plus the sibling study reports. Because almost no published source tests these levels against a distance-matched control, the core evidence here is **eight own tests** on the same data the sibling studies used, with the engine ledger's own baseline (a random level at the same ATR distance). Scripts and raw outputs are in `study/classic_tools/` (section 7).

---

## 0. Headline findings (read this first)

1. **No classic level is a magnet beyond its distance.** Daily floor pivots, Camarilla, Fibonacci, Woodie and DeMark levels are reached at the random-level rate. Over about 1,500 CME futures days and 3,300 BTC days, edges sit between -3.0 and +1.2 pp (T1), and range-scaled placebo levels such as "prior close + 0.45 x prior range" behave the same. Monthly / quarterly / yearly opens and monthly pivots are reached *less* often than random on daily data: QOPEN -1.9 pp (z -3.8) at 5 days and -4.1 pp (z -3.2) at 20 days, MOPEN -3.2 pp (z -3.0) at 20 days. Prior month / quarter / year extremes and 52-week / 20-day / 60-day extremes are at baseline (±0.5 pp at 5 days) (T2).
2. **Weekly references are BARRIERS for other targets. This is the main actionable finding.** If the weekly floor pivot (PP / R1 / S1 from last week's H/L/C) or the weekly open lies between price and a liquidity pool, that pool is swept less often within 24 hourly bars:
   - weekly pivots: **-6.2 pp on CME (z -5.3) and -5.4 pp on BTC (z -6.9)**;
   - weekly open: -2.1 pp (CME) and -3.1 pp (BTC, z -3.8).

   The result holds after stratifying on distance, whether the pool sits outside the prior day's / prior week's range, pool age and pool source. It holds at H = 8 and H = 24. The effect grows with the number of levels crossed (BTC raw: 0 → +0.5, 1 → -4.2, 2 → -11.4, 3 → -14.4 pp), which is about **-0.25 logit per weekly level crossed**. Daily pivots, Camarilla H3/L3/H4/L4 and random placebo levels show no such effect (T8). This matches the strong literature: published S/R levels interrupt intraday trends (Osler 2000) and coincide with peaks in limit-order-book depth (Kavajecz & Odders-White 2004).
3. **The engine's Confluence pillar has the wrong sign for the anchors it uses, and for the anchors siblings propose to add.** We compared pools within 0.35 ATR of an anchor with pools that are not, within distance buckets, using a day-cluster bootstrap:

   | Anchor family | CME | BTC |
   |---|---|---|
   | Weekly pivots | -6.1 pp (z -4.3) | -3.8 pp (z -3.9) |
   | Weekly / monthly opens | -7.4 pp (z -3.9) | -4.5 pp (z -4.0) |
   | Engine pools PDH/PDL/PWH/PWL as anchors | -4.8 pp (z -3.6) | -1.1 pp |
   | Engine EQ / midnight / London opens | +0.6 pp | -2.6 pp, and -3.3 pp (z -3.6) at H = 8 |
   | Round numbers | -1.4 pp | -1.0 pp |
   | Daily pivots | inconsistent sign | inconsistent sign |

   No anchor family is consistently positive (T5). The sibling `calib_ml.md` found the same with a different method (confluence coefficient -0.25 logit, t -2.7).
4. **Small genuine "return to prior value" effect.** Prior-day central levels sit close to price (0.5-1.4 ATR) and are reached slightly more often than random:
   - prior settlement +3.5 pp (z 3.7);
   - prior-day mid / CPR BC +4.0 pp (z 3.6);
   - prior-day VWAP +2.8 pp (z 2.5);
   - classic PP +2.3 pp (z 2.2).

   These figures are CME at H = 24 and repeat at H = 8. On BTC the effect is smaller: PP +1.5 pp, CPR TC +1.9 pp (z 3.2). It is mean reversion toward the prior day's value, not stop liquidity. Any level near the prior PP shows it (placebo PP ± 0.15 R: +2.0 to +2.5 pp), so the pivot formula is not what matters (T1).
5. **Gap fill is a distance artefact, except for large gaps.** On NDX 2003-2018 cash data:
   - Gaps of at least 0.5 daily ATR are filled the same day 30.6% of the time vs 22.7% for a random level at the same distance (**+7.9 pp, z 4.5**). Pooled gap-downs of that size show +12.0 pp (z 4.9). Gap-ups are about 0.
   - Small gaps are not filled more than distance predicts.
   - The popular "80% of small gaps fill" is just distance.
   - CME futures RTH gaps (n = 218) give +4.5 ± 4.8 pp, which is inconclusive.

   Large-opening-move reversals are documented in index futures (Grant, Wolf & Yu 2005) (T3).
6. **VWAP.**
   - A frozen session VWAP is a weak magnet: CME +1.5 pp (z 2.9), BTC +0.3 pp.
   - The *moving* VWAP line is touched far more often than a fixed level. Most of that is mechanical, because it drifts toward price.
   - Against an equal-weight TWAP placebo, the volume-weighted part is +8 to +11 pp on CME at 0.5-4 ATR but only +1 to +5 pp on BTC.
   - σ-bands: about 0 on CME; -1.4 to -1.7 pp on BTC.
   - Anchored weekly / monthly VWAP: BTC -2.8 / -2.9 pp (z -3.7), CME +2.3 / +0.6 pp.

   VWAP should not become a static DOL target: a moving target would inflate the ledger's edge against its static random-level baseline (T4).
7. **The folklore rules fail.**
   - "Narrow CPR → trend day" is reversed: after a narrow CPR the next day's range is 0.92 ATR vs 1.10 after a wide one, and trend days are 34.6% vs 37.7% (n = 8,699 days). Once the prior range is controlled, the sign is inconsistent (T6).
   - "Above pivot / VWAP / weekly open / monthly open = bullish" adds nothing to which of PDH / PDL is taken first beyond the geometry of price inside the prior range. Out-of-sample Brier is unchanged or worse on CME (n = 1,945) and BTC (n = 3,227). The rule's apparent 68-72% accuracy is geometry (T7).
8. **For the engine:**
   - (a) Add a **weekly-reference path barrier** to score and PoT (CL-1).
   - (b) Neutralise the **Confluence** pillar and never add opens, pivots or round numbers as *positive* anchors (CL-2).
   - (c) Make the classic context measurable per symbol in the shadow ledger (CL-3).
   - (d) Optionally add a gap-gated **prior-settlement** target (CL-4).
   - Everything else in this domain is display-only or should not be added (section 5).

---

## 1. Concepts: precise definitions, parameters, practitioner use, failure modes

Notation: H, L, C, O are the prior period's high, low, close and open (a day, week or month); R = H − L. "Day" means the instrument's trading session. For CME that is the Globex day, 18:00-17:00 ET. TradingView's `timeframe.change("D")` follows the symbol session. For crypto it is the 00:00 UTC day.

### 1.1 Classic floor pivots (Standard / "floor trader")
- **Formulas:**
  - PP = (H + L + C)/3
  - R1 = 2PP − L; S1 = 2PP − H
  - R2 = PP + R; S2 = PP − R
  - R3 = H + 2(PP − L); S3 = L − 2(H − PP)

  Equivalent distances from the prior close: R1 − C = (2H − L − C)/3. The levels therefore scale with the prior range and the close location.
- **Timeframes:**
  - daily pivots from the prior day, used on intraday charts;
  - weekly pivots from the prior week, used on hourly charts or below;
  - monthly pivots from the prior month, used on 4H and daily charts.

  The level stays fixed for the whole next period.
- **Practitioner use:**
  - "Above PP = bullish, below = bearish".
  - R1/S1 are the first targets / fade levels; R2/S2 the extended targets.
  - In a range day price rotates PP ↔ R1/S1. In a trend day it walks R1 → R2.
  - Touch counts are reported conditionally on where the session opens (vendors: open between PP and R1 → PP touched 74%).
- **Edge cases:**
  - Which close to use (settlement or last trade). TradingView futures daily bars can use the settlement as the close.
  - The session template (RTH or ETH): RTH-only pivots differ from 24h pivots.
  - DST and session boundaries.
  - Weekends in crypto (24/7: the UTC day).
- **Failure modes:**
  - Untested magnetism: touch rates are high only because R1/S1 sit about 1-2.5 ATR(1h) from price.
  - Many levels: 7 per timeframe x 3 timeframes means some level is always "near", so any reaction can be read as confirmation.

### 1.2 Central pivot range (CPR) and "virgin / naked" pivots (Ochoa, *Secrets of a Pivot Boss*)
- **Formulas:** BC = (H + L)/2 (the prior-day midpoint, i.e. the engine's `dayEQ`); TC = 2PP − BC. Width = |TC − BC| = |2C − H − L|/3, so the width is the close's distance from the mid of the range.
- **Folklore:**
  - A narrow CPR (bottom quartile of about 20-50 sessions) foretells a trend / expansion day; a wide CPR foretells a range day.
  - Price above the CPR is bullish.
  - Virgin / naked CPR or pivot: a pivot never traded during its session "acts as a magnet" on later days.
- **Failure modes:** no published test was found (LuxAlgo and TradingView scripts describe the rule only). Our T6 reverses the claim, and T1 finds naked pivots at baseline.

### 1.3 Camarilla (Nick Scott, 1989)
- **Formulas:** H_k = C + R·m_k and L_k = C − R·m_k, with m1..m4 = 1.1/12, 1.1/6, 1.1/4, 1.1/2 = 0.0917, 0.183, 0.275, 0.55. Some implementations use 0.555 for H4. H5/H6 variants exist, e.g. H5 = (H/L)·C, but are not standardised.
- **Use:**
  - Fade at H3/L3: short at H3, target L1/L2.
  - Breakout continuation through H4/L4.
  - "H3-L3 contains about 70% of moves; H4-L4 about 90%".
- **Failure modes:** the containment and reversal rates in vendor copy are unsourced. L3 bounce "65% over a 2-bar hold" and "12 of 17 trades" are anecdotes.

### 1.4 Fibonacci, Woodie, DeMark pivots
- **Fibonacci:** PP as classic. R1/R2/R3 = PP + 0.382R / 0.618R / 1.000R, mirrored for S.
- **Woodie:** PP_w = (H + L + 2C)/4; R1 = 2PP_w − L; S1 = 2PP_w − H; R2/S2 = PP_w ± R. One source uses the open instead of the close; the close form is standard.
- **DeMark:**
  - X = 2H + L + C if C > O; H + 2L + C if C < O; H + L + 2C if C = O.
  - PP = X/4; R1 = X/2 − L; S1 = X/2 − H.
- All are deterministic functions of (H, L, C[, O]). They differ only in multipliers, which is why a range-scaled placebo is the right control.

### 1.5 Weekly and monthly pivots
The same formulas on the prior week / month. Swing traders use them as HTF S/R. **Our data say weekly pivots behave as path barriers** (T5, T8), not magnets (T2: W_PP / W_R1 / W_S1 at +0.1 to +0.6 pp, ns). Monthly pivots are reached *less* often than random (T2: M_PP -1.75 pp at 5 days, -3.3 pp at 20 days).

### 1.6 Round numbers (brief: see `ict_liq.md` ICT-3, `orderflow_micro.md` T2, `academic_sr.md` §1.5)
- Grid of step S (00 / 50 / 25 levels).
- Strong evidence (Osler 2003, 2005; Bhattacharya, Holden & Jacobsen 2012):
  - stops cluster just beyond rounds and take-profits at them;
  - crossings accelerate.
- Siblings' bar tests: rounds are not magnets, and sweep wicks stop short of them.
- Our T5 adds: a pool within 0.35 ATR of a round level is swept **less** often (-1.0 to -1.4 pp; "at the round" -2.3 pp CME, -2.6 pp BTC with z -3.3). So round numbers must not become a *positive* confluence anchor.
- **Option-strike pinning:**
  - Ni, Pearson & Poteshman (2005, JFE 78(1)): optionable stocks cluster at strikes on expiration Fridays, through hedging by net-short option holders.
  - Golez & Jackwerth (2012, JFE 106(3)): S&P 500 futures pinned to the ATM strike on serial-option expiry days, 1992-2009, with at least $115 m notional shift per expiration.
  - Elms (2026, SSRN): no pinning in 2016-2025 (2,294 days), a shift to "amplification".
  - Not usable in Pine: no open-interest data, and the effect depends on the regime.

### 1.7 VWAP family
- **Session VWAP:** VWAP_t = Σ(tp·v)/Σv from the session start, with tp = (H + L + C)/3. σ-bands use σ_t = sqrt(Σ v·tp²/Σv − VWAP²). TradingView's `ta.vwap(src, anchor, stdev_mult)` returns [vwap, upper, lower]; in v6 the anchor is a bool such as `timeframe.change("D")`.
- **Anchored VWAP (Shannon):** the same sum started at a chosen event: earnings, a gap, a swing high or low, the start of the week / month / quarter, the YTD start, or the highest-volume bar. No published backtest. The anchor choice is subjective (TrendSpider, StockCharts).
- **Practitioner use:**
  - VWAP is the institutional benchmark; about half of institutional orders are VWAP-benchmarked (a BofA survey cited in a working paper).
  - "Above VWAP = buyers in control" (a trend filter: Zarattini & Aziz 2023, QQQ 2018-2023, about +671% net, with disputed replications).
  - Fade at the ±2σ bands; "price returns to VWAP".
- **Failure modes:**
  - VWAP *moves toward price* by construction, so "price returned to VWAP" is partly mechanical.
  - Thin early-session estimates.
  - Crypto 24/7: the anchor choice is arbitrary.

### 1.8 Period opens
- **Definitions:**
  - daily open (session open);
  - "true day open" / midnight open (ICT; see `ict_time.md`);
  - weekly open (futures: Sunday 18:00 ET; crypto: Monday 00:00 UTC);
  - monthly / quarterly / yearly open (first trade of the period).
- **Use:**
  - "Above the monthly open = bullish month".
  - Opens as magnets: "the weekly open is retested in X% of weeks".
  - Opens as S/R.
- **Evidence:**
  - Sibling `bias_dol.md`: the weekly-open bias adds nothing beyond geometry.
  - Our T7: monthly open, weekly open and pivot side add nothing beyond geometry.
  - Our T2: opens are not magnets.
  - Our T5 / T8: weekly / monthly opens are barriers.

### 1.9 Prior-period highs / lows and N-period extremes
- PDH/PDL and PWH/PWL are in the engine. PMH/PML, PQH/PQL and PYH/PYL are not.
- 52-week high / low = max high / min low over 252 sessions. ATH = the full-history extreme. N-day extremes (ICT IPDA 20/40/60 days).
- As pools they are swept on a trade-through. The engine rule is strict `>` / `<`.
- Strong *monthly-horizon* stock anchoring evidence exists: George & Hwang (2004) and the sibling `academic_sr.md`. At DOL horizons, our T2 is null.

### 1.10 Previous settlement / close and opening gaps
- **CME ES settlement:** the VWAP of trades from 14:59:30 to 15:00:00 CT. CME SER-8591 moved it in 2020 from 15:14:30-15:15:00 CT. It is the official "prior close" for equity-index futures; floor pivots computed from it differ from last-trade pivots.
- **Opening gap** (session instruments): gap = RTH open − prior RTH close or settlement. "Gap fill" = price trades back to the prior close within the session or N sessions.
- **Folklore:** 80% of small gaps fill the same day.
- **Vendor data** (Tradeify, SPY ~20 years): same-session fill is 77% for 0.10-0.25% gaps, 62% for 0.25-0.5%, 42% for 0.5-1% and 35% for 1-2%. Gaps of at least 1 ATR fill 23%.
- **NDOG / NWOG** (ICT): the sibling `ict_pd.md` ICTPD-6.
- **On 24h futures charts** the RTH "gap" is not a chart gap. The prior settlement is simply a level the overnight session moved away from.

---

## 2. Evidence

### 2.1 Published evidence (graded)

| # | Claim | Source | Numbers | Grade |
|---|---|---|---|---|
| P1 | Published S/R levels interrupt intraday trends | Osler (2000), FRBNY Economic Policy Review 6(2) | Levels published daily by 6 firms, Jan 1996-Mar 1998, vs 10,000 sets of arbitrary levels. All 6 firms beat chance. Predictive power lasts at least 5 business days and varies by firm and currency. | **strong** (bootstrap control). Direction: **barrier**, not magnet |
| P2 | S/R levels sit at limit-order-book depth peaks | Kavajecz & Odders-White (2004), RFS 17(4):1043-1071; Taiwan replication | S/R coincides with peaks in book depth. The mechanism is "technical rules locate depth already in place". | **strong**. Supports the barrier reading |
| P3 | Stops beyond, take-profits at round numbers; crossings cascade | Osler (2003) JF 58(5); Osler (2005) JIMF; Bhattacharya, Holden & Jacobsen (2012) | See `ict_liq.md` E1/E2 | strong |
| P4 | Pivot points in FX: no value in the traditional form | Johnsson & Frykmer (2019), Lund MSc thesis (bootstrap, 3 pairs) | "No support for … pivot points … in their traditional way"; varies by pair; suggests inverse use | weak (thesis) |
| P5 | Pivots "work" as S/R 53-58% | Bulkowski, ThePatternSite "Pivot Points" | Support rates of 53-58% across P/R1/S1/R2/S2. No random control. | weak |
| P6 | R1/S1 touch rates | Steenbarger (S&P, 963 days, relayed on a forum); FXNX (EURUSD/GBPUSD); Tradeify (ES, 500 sessions Nov 2024-Nov 2026); Edgeful (YM) | About 80% of days hit R1 or S1. FX: R1 46%, S1 44%, either 84%, close beyond < 18%. ES: R1 reached in 221/500 sessions, 47.5% closed back below; S1 held 56.7%. YM opened between PP and R1 (n 62): PP touched 74.2%, S1 30.6%. | weak (vendor, no distance control) |
| P7 | Camarilla containment / reversal rates | vendor guides (takeprofitapp, Aron Groups) | "70% inside H3-L3, 90% inside H4-L4", "H3/L3 fade ~70%". Unsourced. | none |
| P8 | Narrow CPR → trend day | Ochoa (Pivot Boss); LuxAlgo CPR concept; TradingView CPR scripts | No statistics published | none (our T6 contradicts it) |
| P9 | VWAP trend filter | Zarattini & Aziz (2023), SSRN 4631351 | QQQ 2018-2023: $25k → $192,656 net (+671%); Sharpe about 2.1 (secondary). Replications report far less (QuantConnect thread). | moderate-weak (bias use, not target) |
| P10 | VWAP is a benchmark for about half of institutional flow | working paper citing a BofA survey | about 50% | weak-moderate |
| P11 | Anchored VWAP as S/R | Shannon; StockCharts; TrendSpider | Definitions only; "subjective anchor" | none |
| P12 | Gap fill rates by size | Tradeify (SPY ~20 years); stockwirex (2017-2026, about 2,400 sessions); thetrading.tools | 0.10-0.25%: 77-85%; 0.25-0.5%: 62%; 0.5-1%: 33-42% (67% when VIX > 30); at least 1 ATR: 23% | weak (no distance control; our T3 shows most of it is distance) |
| P13 | Reversals after large opening moves in index futures | Grant, Wolf & Yu (2005) JBF 29(5):1311-1327, S&P futures Nov 1987-Sep 2002; Fung, Mok & Lam (2000) | Highly significant reversals, stronger after large *up* opens; weaker after transaction costs | **strong** |
| P14 | Overnight drift and opening reversal | Boyarchenko, Larsen & Whelan (NY Fed SR917; Liberty Street 2021) | The opening reversal is only weakly related to the overnight move: not a pure gap fill | moderate |
| P15 | Option-strike pinning | Ni, Pearson & Poteshman (2005) JFE 78(1); Golez & Jackwerth (2012) JFE 106(3); Elms (2026) SSRN | Pinning on expiry days 1992-2009 (at least $115 m per expiry); none 2016-2025 | strong (historic), moderate (current absence) |
| P16 | CME ES settlement = 30-second VWAP 14:59:30-15:00:00 CT | CME SER-8591 (2020); CME client wiki | as stated | strong (exchange document) |
| P17 | 52-week high anchoring | George & Hwang (2004) etc., via `academic_sr.md` | monthly-horizon momentum in stocks | strong (wrong horizon for the DOL) |

### 2.2 Own tests: method

- **Data** (shared with the sibling studies):
  - CME 1h futures ES, NQ, RTY, YM, GC (Mar 2025-Apr 2026) and CL (Jun 2025-Apr 2026): about 1,500 Globex days;
  - CME 1-minute data for the four index futures, Jan-Apr 2026;
  - BTC/USD Bitstamp 1-minute data resampled to 1h, Jan 2016-Jan 2025: 79,057 bars, about 3,290 days;
  - daily SPX and NDX 1999-2018, and BTC daily.

  Daily SPX "opens" are stale on 39.8% of days (open equals the prior close), so SPX is excluded from the gap tests.
- **Engine-ledger baseline:** a level at distance d (in ATR14 of the bar timeframe) on side s counts as "hit" if the path touches it within H bars (`f_potBase` semantics). The baseline is P(max excursion on side s over H bars ≥ d), taken from the empirical excursion surface of the same instrument. It is matched to the time of day: day-start bars in T1, the hour of day in T4/T5/T8.
  - Touch rule: touch (`>=`) for reference levels; strict trade-through for PDH/PDL and other extremes, the engine rule.
  - Edge = hit% − base%.
  - SE is clustered by trading day (T1/T5/T8) or by 2H blocks (T2).
- **Placebos:**
  - range-scaled levels C ± u·R and PP ± u·R, u ∈ {0.15 … 1.0} (T1);
  - 13 random prices per day inside the prior range ± 50% (T5/T8);
  - pivot levels shifted by ± U(0.08, 0.2)·R (T5);
  - TWAP for VWAP (T4).
- **Terminal test** (T1): given a touch, does the move end within 0.25 ATR beyond the level more often than a random level's would? The baseline is P(d ≤ exc < d + 0.25 | exc ≥ d) from the same surface.

### 2.3 Own tests: results

**T1. Daily-derived levels from the session open, 1h bars** (`t1_daystart.py`; outputs `out_t1_*`)

CME, H = 24 bars (one Globex day). n ≈ 1,400-1,530 per level. Values are edge in pp (z):

| Level | Edge (z) | Level | Edge (z) | Level | Edge (z) |
|---|---|---|---|---|---|
| CPR_BC (= dayEQ) | **+3.95 (3.6)** | SETT (prior RTH close) | **+3.46 (3.7)** | PD_VWAP | **+2.76 (2.5)** |
| PP | +2.34 (2.2) | CPR_TC | +2.34 (2.5) | W_AVWAP | +2.30 (1.9) |
| PDOPEN | +1.92 (1.7) | WOOD_R1 | +1.24 | DEM_H | +1.03 |
| FIB_R1 | +0.88 | NAKED_PP (n 345) | +0.77 | M_AVWAP | +0.63 |
| CAM_H3 | +0.57 | CAM_H4 | +0.31 | S3 | +0.35 |
| R1 | -0.12 | PDL | -0.19 | CAM_L3 | -0.26 |
| S1 | -0.48 | FIB_S1 | -0.59 | S2 | -0.69 |
| WOOD_S1 | -0.74 | PDH | -0.88 | CAM_L4 | -1.16 |
| R3 | -1.62 (-2.6) | FIB_R2 | -1.66 | R2 | **-2.98 (-3.1)** |

Placebo controls: the range-scaled placebos run from -3.0 to +2.5 pp. Placebo levels near the prior PP (PP ± 0.15 R / 0.3 R) show **+2.0 to +2.5 pp**, the same as PP. So the effect belongs to the "prior-day centre of value", not to the formula. At H = 8 the same picture holds: SETT +3.4 (z 2.5), CPR_BC +3.2 (2.9), PP +3.1 (2.7), PD_VWAP +2.2 (1.9). R1/S1, Camarilla and Fibonacci levels range from -1.6 to +0.6 pp.

BTC, H = 24 (n ≈ 3,000-3,300 per level):
- Positive: CPR_TC +1.88 (z 3.2), PP +1.47 (2.1), PD_VWAP +1.17 (1.6).
- Negative: W_AVWAP -2.94 (-3.7), M_AVWAP -2.78 (-3.8), PDH -2.45 (-3.2), PDL -2.42 (-3.2), FIB_S1 -2.31, FIB_R1 -2.09, R1 -1.51, CAM_H4 -1.23.
- Others within ±1 pp.
- At H = 8 the central levels shrink: PP +0.5, PD_VWAP -0.3, CPR_TC +2.0 (z 2.7).

Terminal test: no level makes moves end at it more often than a random level would. Among about 50 tests, |z| ≤ 2.3 on CME. On BTC, touched PDH/PDL *overshoot* more: "ends within 0.25 ATR" falls 5.1-5.6 pp below baseline (z -4.1 / -4.4). That is stop-run continuation.

**T2. Higher-timeframe levels on daily bars** (`t2_htf.py`, `t2_sum.py`; SPX + NDX 1999-2018, BTC 2016-2025; `out_t2_sum.txt`)

| Level | H = 5 days, edge pp (z) | H = 20 days, edge pp (z) |
|---|---|---|
| QOPEN | **-1.88 (-3.8)** | **-4.08 (-3.2)** |
| MOPEN | -1.03 (-1.7) | **-3.22 (-3.0)** |
| YOPEN | -0.89 | +0.70 |
| WOPEN | +1.13 (1.8) | -0.56 |
| M_PP (monthly pivot) | **-1.75 (-3.0)** | **-3.28 (-2.8)** |
| M_R1 / M_S1 | -0.25 / -0.09 | -1.76 / -0.91 |
| M_CAM H3 / L3 | -1.35 / +0.29 | -2.83 / -1.30 |
| W_PP / W_R1 / W_S1 | +0.62 / +0.14 / +0.50 | -0.42 / -0.61 / -0.27 |
| PMH / PML (untaken) | +0.28 / +0.33 | -3.55 (-2.1) / +1.80 |
| PQH / PQL | -0.09 / -0.01 | -2.85 / -0.44 |
| PYH / PYL | -0.06 / -0.11 | +1.31 / -1.52 |
| 252dH / 252dL | -0.16 / +0.04 | +0.93 / -0.45 |
| 60dH / 60dL | +0.43 / +0.30 | -0.56 / +0.80 |
| 20dH / 20dL | +0.21 / +0.72 | -0.83 / +0.32 |
| PWH / PWL (reference) | +2.52 (3.2) / -0.53 | +0.44 / -1.04 |
| PDH / PDL (reference) | +1.38 (2.5) / -0.22 | +0.63 / +0.02 |

PDH/PWH's small positive H = 5 edge sits at 1-2 ATR: +7.2 pp (z 5.3) for PDH. That is a short-term reversal after a large down day, a property of the state rather than of the level.

**T3. Opening-gap fill vs distance-matched random level** (`t3_gaps.py`, `t3b.py`; `out_t3*.txt`)
- NDX cash 2003-2018, fill within the same day:
  - gaps of at least 0.5 daily ATR: 30.6% vs 22.7%, **+7.9 pp (z 4.5, n 700)**;
  - 0.25-0.5 ATR: +2.3 pp (z 1.6);
  - below 0.25 ATR: +1.2 pp (z 1.5).
- Pooled SPX + NDX gaps of at least 0.5 ATR:
  - by side: gap-down (fill upward) **+12.0 pp (z 4.9, n 374)**, gap-up +0.3 pp;
  - by era: 2003-10 +7.2 pp (z 2.5), 2011-18 +5.1 pp (z 2.6).
- Within 5 days, small gaps are slightly *under*-filled vs distance: -2 to -5 pp, though the pool includes the stale SPX opens.
- CME RTH gaps (09:30 open vs prior 16:00 close, Jan-Apr 2026, ES/NQ/RTY/YM, n 218): +4.5 ± 4.8 pp, inconclusive.

**T4. Session VWAP, bands and TWAP, 1h, H = 8, checkpoints every 2 bars** (`t4_vwap.py`; `out_t4_*`)

| | CME edge pp (z) | BTC edge pp (z) |
|---|---|---|
| Frozen VWAP | +1.51 (2.9) | +0.28 (0.8) |
| Frozen TWAP | +2.89 (5.2) | +0.11 |
| VWAP +1σ / -1σ | +1.47 / +0.52 | +0.29 / -0.32 |
| VWAP +2σ / -2σ | +1.44 / -0.82 | **-1.70 (-4.3) / -1.44 (-3.7)** |
| Moving VWAP minus moving TWAP, 0.5-1 / 1-2 / 2-4 ATR | +8.5 / +10.2 / +10.7 | +1.1 / +2.3 / +4.6 |

**T5. Confluence: pools within 0.35 ATR of an anchor** (`t5_confluence.py`, `t5_diff.py`; `out_t5_*`)

The pools are 1h swings (pivot 5/5, as the engine uses) plus PDH/PDL/PWH/PWL, 0.5-6 ATR away, live until traded through. The table gives the flagged-minus-unflagged edge in pp (z), distance-bucketed, with a day-cluster bootstrap (300 reps).

| Anchor group | CME H24 | CME H8 | BTC H24 | BTC H8 |
|---|---|---|---|---|
| ENG_POOL (PDH/PDL/PWH/PWL) | **-4.78 (-3.6)** | **-4.06 (-5.5)** | -1.14 | -0.92 (-1.9) |
| ENG_EQOPEN (dayEQ, midnight, London opens) | +0.57 | +0.59 | -2.62 (-1.8) | **-3.25 (-3.6)** |
| DPIV (13 daily floor/Camarilla/Fibonacci levels) | +3.69 (3.6) | +1.21 (2.0) | -0.82 | **-1.84 (-4.4)** |
| DPIV_SH (shifted placebo) | +0.95 | +0.07 | -0.57 | -1.45 (-3.6) |
| WPIV (weekly PP/R1/S1) | **-6.08 (-4.3)** | **-3.61 (-5.0)** | **-3.75 (-3.9)** | **-1.91 (-3.8)** |
| OPENS (weekly + monthly open) | **-7.43 (-3.9)** | **-5.34 (-5.5)** | **-4.48 (-4.0)** | **-2.32 (-3.6)** |
| VALUE (settlement, PD VWAP; flag share 2%) | +2.65 | +3.05 | -1.68 | -1.77 |
| ROUND (auto step and half step) | -1.38 (-1.6) | -1.22 (-2.3) | -1.00 (-1.6) | -0.14 |
| PLACEBO (13 random levels) | +2.04 (1.9) | +0.27 | +0.27 | -0.86 (-2.3) |

By position (H24), WPIV and OPENS are negative whether the anchor lies on the near side, exactly at the pool, or beyond it. For example, OPENS "at" (within 0.05 ATR) is -11.4 pp on CME (z -3.5). Overall pool edge vs random: CME -3.8 pp (z -5.8), BTC -1.1 to -1.7 pp. By source (CME / BTC):

| Source | CME | BTC |
|---|---|---|
| Swing pools | -3.4 | -1.1 |
| PDH | -3.9 | -1.5 |
| PDL | -3.2 | -1.7 |
| PWH | -5.1 | -1.1 |
| PWL | **-9.6** | -2.4 |

So the high source tier the engine gives PW pools (0.92) is not supported at hourly horizons.

**T8. Path barriers: references strictly between price and the pool** (outside the pool's ±0.35 ATR band) (`t8_path.py`, `t8_an.py`; `out_t8_*`)

The table gives the edge of "at least 1 reference between" minus "none" in pp (z), stratified on distance (6 buckets) x outside prior-day range x outside prior-week range x pool age (< 24, 24-120, > 120 bars) x source (swing / key):

| Between price and pool | CME H24 | BTC H24 | CME H8 | BTC H8 |
|---|---|---|---|---|
| Weekly PP/R1/S1 (any) | **-6.23 (-5.3)** | **-5.43 (-6.9)** | **-3.48 (-6.2)** | **-2.03 (-6.1)** |
| Weekly PP only | **-4.54 (-3.6)** | **-5.91 (-6.8)** | **-2.97 (-5.5)** | **-2.29 (-6.1)** |
| Weekly R1/S1 | **-5.07 (-4.2)** | **-3.35 (-3.3)** | -2.46 (-4.4) | -1.12 (-2.6) |
| Weekly open | -2.13 (-1.7) | **-3.08 (-3.8)** | -1.39 (-2.7) | -1.15 (-2.9) |
| Monthly open | **-7.13 (-5.4)** | -0.53 | **-3.23 (-5.6)** | +0.20 |
| Daily PP/R1/S1 | +1.49 | -1.51 | n/a | n/a |
| Camarilla H3/L3/H4/L4 | +1.20 | -1.33 | n/a | n/a |
| 3 random placebo levels | +0.11 | +0.81 | n/a | n/a |
| Engine anchors (dayEQ, midnight, London) | +0.65 | -0.45 | -1.77 (-2.1) | -1.42 (-3.1) |

Dose-response (raw mean edge by the number of weekly pivots crossed, H24):

| Weekly pivots crossed | CME | BTC |
|---|---|---|
| 0 | -1.7 | +0.5 |
| 1 | -5.3 | -4.2 |
| 2 | -9.4 | -11.4 |
| 3 | -10.6 | -14.4 |

The base rate of these pools is about 33-36%, so one crossed weekly level is about -0.25 in logit.

**T6. CPR width → next day** (`t6_cpr.py`; `out_t6.txt`)

Pooled n = 8,699 days (NDX 2003-18, BTC, 6 CME futures):
- After a narrow CPR (≤ 25th percentile of 20 days) the next-day range is 0.919 ATR; after a wide one (≥ 75th) it is 1.102.
- Trend days (a new extreme by at least 0.5 ATR): 34.6% after narrow vs 37.7% after wide.
- Controlling for the prior range, the CPR-width coefficient is -0.025 (t -0.6) pooled, +0.42 for BTC (t +5.2) and -0.27 for NDX (t -4.2). The sign is inconsistent: no usable rule.

**T7. "Above the reference = bullish" vs geometry** (`t7_bias.py`; `out_t7_*`)

Setup: at fixed decision hours, with PDH and PDL both untaken, which one is traded through first? The comparison is 2-fold out-of-sample Brier, geometry-only (position inside the range) vs geometry plus the sign of price relative to the reference.

| Data | Geometry-only accuracy | Feature | Rule accuracy | Change in Brier (+ = worse) |
|---|---|---|---|---|
| CME (n 1,945) | 0.664 | daily PP | 0.677 | +0.0018 ± 0.0011 |
| | | session VWAP | | +0.0031 ± 0.0012 |
| | | weekly AVWAP | | +0.0061 ± 0.0022 |
| | | weekly open | | +0.0001 |
| | | monthly open | | +0.0001 |
| BTC (n 3,227) | 0.718 | all five features | | between -0.0006 and +0.0003 |

### 2.4 Synthesis: what each classic level is
- **Barriers (resting liquidity or take-profits):**
  - weekly pivots and weekly / monthly opens, strongest and replicated;
  - round numbers, mildly.
  - Consistent with P1/P2/P3.
  - Use them as **path cost** and never as a positive confluence.
- **Weak "value" magnets near price:**
  - prior settlement, prior-day mid / CPR / PP, prior-day VWAP (+1.5 to +4 pp);
  - the moving session VWAP on CME.
  - This is mean reversion over 8-24h, not stop liquidity.
- **Distance only:**
  - daily floor / Camarilla / Fibonacci / Woodie / DeMark pivots;
  - prior month / quarter / year extremes;
  - 52-week and N-day extremes;
  - naked pivots;
  - small gaps.
- **Less than distance:** quarterly / monthly opens, monthly pivots, BTC anchored VWAPs, VWAP ±2σ (BTC).
- **Folklore refuted:** narrow CPR → trend day; "above pivot / VWAP / open = bullish" beyond geometry; "most gaps fill".

---

## 3. Engine gap analysis (baseline_v2.pine line numbers)

| Concept | Status | Lines | What the engine does / differs |
|---|---|---|---|
| PDH/PDL pools | present | 104, 945, 952-961, 1790-1794 | Chart-TF `f_rangeTrack(timeframe.change("D"))`, exact print bar, registry src 6, strict sweep. Matches the evidence (distance-level). |
| PWH/PWL pools | present | 105, 946, 1795-1799 | src 7, tier 0.92, the highest. T5 by source: PWH/PWL edges -5.1 / -9.6 pp (CME), -1.1 / -2.4 (BTC), *worse* than chart swings (-3.4 / -1.1). The tier ranking is not supported. |
| Source tier in density | partial / likely wrong | 506-516 (`f_tierW`), 682 (`1.2*tier`) | PW 0.92 > PD 0.80 > HTF 0.65 > sessions 0.55-0.60 > STF 0.45 > chart 0.25 adds up to about +0.8 to density x. No support at hourly horizons (T5; `calib_ml.md`: external -0.27 logit). |
| Confluence pillar | **wrong** | 139 (`confATR` 0.35), 143 (`wConf` 15), 220-222, 963-968, 1930-1933 (anchors aPDH, aPDL, aPWH, aPWL, dayEQ, midOpen, ldnOpen, nyOpen, htfEQ), 674-680 (`conf = min(1, 0.35*hits)`) | Rewards overlap. Measured effect (T5): PD/PW pools as anchors -4.8 pp (CME), opens / EQ neutral to -3.3 pp. Weekly references and round numbers, if added, would be strongly negative. Sibling `calib_ml.md`: -0.25 logit. |
| Daily floor / Camarilla / Fibonacci / Woodie / DeMark pivots | missing (correct) | grep finds only swing `ta.pivothigh` (709, 879) | No reach edge (T1), no barrier (T8), no bias value (T7). Keep them out of scoring. Optional display only (CL-6). |
| Weekly pivots | missing | n/a | **Path barrier** (T8: -5 to -6 pp per target, z -5 to -7). Not used anywhere: CL-1. |
| Weekly / monthly / quarterly / yearly opens | missing (only intraday opens 964-966 as anchors) | 964-966 (`f_sessOpen`) | Weekly and monthly opens are barriers (T5/T8). Q/M opens are reached less than random (T2). The intraday opens as anchors are neutral to negative (T5). |
| Prior month / quarter / year H/L | missing | `f_rangeTrack` only for D and W (945-946) | Reach at baseline (T2). Optional completeness for Swing mode: CL-5. |
| 52-week / ATH / N-day extremes | missing | n/a | Baseline (T2). If the sibling ACAD-5 adds them, the tier must not exceed PW. |
| Prior settlement / prior close | missing | `dayEQ` (967) is the prior-day mid, used only as an anchor | SETT +3.5 pp (z 3.7, CME); a large gap gives +7.9 pp. CL-4 (gated, optional). |
| Opening gaps | missing | n/a | Size-gated value (T3). Coordinate with ICTPD-6. |
| Session VWAP / bands / AVWAP | missing (correct as targets) | grep "vwap": none | A moving target inflates the ledger edge. Frozen VWAP is weak; bands and AVWAP are null or negative. |
| Round numbers | missing | n/a | The sibling ICT-3 adds them as confluence. T5 shows a negative confluence effect. Keep the stop-depth extension and drop the positive anchor (coordination note §6). |
| Path cost | partial | 1404-1414 (`f_pathVol`), 1944-1947 (x1.10 / x0.85) | Volume-profile path only. Reference-level barriers are absent: CL-1 adds them in the same loop. |
| PoT model | present | 1302-1311 (`f_potModel`), 2066 (`activePoT`) | Has no barrier term. CL-1 adds a logit shift. |
| Ledger families | present (coarse) | 635-636 (`grp`), 1066-1071 (`array.new(5)`), 1314-1322 (`f_potBase`), 1376-1383 (`f_calMult`), 1426-1431 (`f_openTrial`), 1461-1500 (`f_book`) | The random-level baseline is exactly the metric used in this study, so new features are measurable. Only the active target opens trials (2045), so per-feature learning needs a shadow ledger (sibling CAL-3) or per-trial feature bits (CL-1, CL-3). |
| Above / below-reference bias | n/a (correctly absent from D) | draw vector (D) not tied to pivots / VWAP / opens | T7: no value beyond geometry. Do not add. |

---

## 4. Proposals (best first; at most 10)

### CL-1 (P1, scoring + probability, S-M) · Weekly-reference path barrier
- **Why.** This is the strongest, best-replicated effect in the domain. Each weekly PP/R1/S1 or weekly open between price and a target cuts its 8-24 bar reach by about 2-6 pp, roughly -0.25 logit per level (T8). The cut grows with each level crossed, holds on CME and BTC, and survives distance, range-position, age and source controls. A placebo does not reproduce it, and daily pivots do not either. Published S/R levels are where depth rests and where trends get interrupted (P1, P2). Today the engine is blind to this. It can select a PWH target three weekly levels away with full proximity credit.
- **Inputs** (G_SCORE):
  - `bool useWkBar = input.bool(true, "Weekly Reference Barrier")`
  - `float wkBarM = input.float(0.90, "  Score x per Weekly Level Crossed", minval = 0.5, maxval = 1.0, step = 0.01)`
  - `float wkBarL = input.float(0.25, "  PoT Logit Shift per Level", minval = 0.0, maxval = 1.0, step = 0.05)`
  - `bool wkBarMO = input.bool(false, "  Include Monthly Open")` (CME strong, BTC null).
- **State** (SERIES, right after 946/961; chart TF, no `request.security`):
  ```
  var float wPP = na
  var float wR1 = na
  var float wS1 = na
  var float wOpn = na
  var float mOpn = na
  if pwNew
      float pwC = close[1]                 // last close of the finished week
      wPP  := (pwH + pwL + pwC) / 3.0
      wR1  := 2.0 * wPP - pwL
      wS1  := 2.0 * wPP - pwH
  if timeframe.change("W")
      wOpn := open
  if timeframe.change("M")
      mOpn := open
  ```
  Call `timeframe.change` at global scope on every bar, never inside a condition. If `f_rangeTrack` is already fed `timeframe.change("W")`, reuse a global `bool newW = timeframe.change("W")`.
- **Helper** (STATE HELPERS, after the globals above, so there are no forward references):
  ```
  f_xRef(float px, Level lv, float tol) =>
      int   k = 0
      float e = lv.nearEdge()
      for a in array.from(wPP, wR1, wS1, wOpn, wkBarMO ? mOpn : na)
          if not na(a)
              if lv.side == 1 ? (a > px and a <= e + tol) : (a < px and a >= e - tol)
                  k += 1
      math.min(k, 3)
  ```
  This counts levels between price and the near edge, plus those "at" the pool within `tol` (T5 shows "at" is also negative).
- **Score** (scoring loop 1939-1948, next to the volume-path multiplier):
  ```
  if useWkBar
      int k = f_xRef(close, lv, confTol)
      lv.xRef := k
      lv.mult *= math.pow(wkBarM, k)
  ```
  Add the field `int xRef = 0` to `Level` (TYPES 323-350).
- **PoT** (live readout 2066): after `activePoT := …`, add
  `if useWkBar and not sweptNow` → `activePoT := math.min(0.95, f_sigm(f_logit(activePoT) - wkBarL * f_xRef(close, activeLv, confATR * atr)))`.
  `f_logit` and `f_sigm` exist (484/488). Recounting live is O(5).
- **Ledger** (measurable):
  - Add `xr` to `Trial` and set it in `f_openTrial` (1429) as `xr = lv.xRef`.
  - In `f_book`, accumulate `xbN / xbK / xbPE` (3 buckets: 0, 1, 2+).
  - Terminal Full view row: `W-REF crossed 0 | 1 | 2+ : hit−base`.

  `pBase` stays the random-level baseline, so the EDGE readout shows whether avoiding barriers helps on this chart.
- **UX:** append " · across N weekly ref" to the Clean label tooltip when k > 0. In the Terminal HUD, show the tag `XW2`.
- **Expected value:** the selection moves toward targets on the near side of weekly value. PoT is less overconfident for targets beyond the weekly pivot. On the test data that is about a 15% relative reduction in false targets for k = 1 and 30-40% for k ≥ 2.
- **Evidence:** moderate. Own tests: 2 datasets, 2 horizons, z -2.6 to -7.1, with dose-response. The mechanism is backed by strong literature.
- **Risk:**
  - Untested on 1-5 minute charts with H = 30 bars (a 30-minute horizon), where the effect is probably smaller. Default `wkBarM` 0.90 is mild, and the ledger row will show it.
  - Weeks on exotic sessions.
  - The first week of history has no weekly levels (na-safe).
- **Effort:** S-M (about 40 lines).

### CL-2 (P1, scoring, S) · Neutralise the Confluence pillar and stop adding positive "reference" anchors
- **Why:**
  - T5 finds no anchor family with a consistently positive effect.
  - The engine's own anchors are neutral (EQ / opens on CME) or negative (PD/PW pools on CME -4.8 pp, z -3.6; opens / EQ on BTC -2.6 to -3.3 pp).
  - Candidates the siblings propose to add are negative: weekly levels (-4 to -7 pp), round numbers (-1 to -1.4 pp, "at" -2.3 to -2.6 pp).
  - An independent check (`calib_ml.md`) finds confluence at -0.25 logit (t -2.7).
- **Spec:**
  1. Change `wConf` (143) from 15 to **0**. Keep the input and the tooltip readout so users can still turn it on. `wSum` (304) renormalises automatically. Scores of levels with conf = 0 rise by 100/85 = 1.18x, so lift `minScore` (146) from 35 to about **41** to keep the same selection rate.
  2. Remove `midOpen`, `ldnOpen`, `nyOpen` and `aPWH`/`aPWL` from the anchor list at 1931. If any of them is kept, keep it for the tooltip only, because they are measured as neutral to negative.
  3. Add an explicit rule to the code comment and the README: "Reference levels (weekly / monthly opens, weekly pivots, round numbers, daily pivots) are barriers, not confluence. See CL-1."
  4. Optional: re-enable confluence only through ledger-learned signed lifts (CL-3).
- **Expected value:** removes a 15/100 weight that currently pushes selection toward pools that are *less* likely to be taken.
- **Evidence:** moderate (own T5, replicated across 2 datasets and 2 horizons, plus the sibling's independent regression).
- **Risk:**
  - The scores shift. Re-check the minScore and hysteresis defaults.
  - Arrays (FVG/OB) also lose confluence credit, and that part was not tested here. The ledger family lifts (`f_calMult`) protect arrays.
- **Effort:** S.

### CL-3 (P2, statistics-ledger, M) · Reference-context feature bits in the candidate (shadow) ledger
- **Why.** Effects vary between CME and BTC: the monthly open is a barrier on CME but null on BTC, and daily pivots have opposite signs. The engine already has the right estimator (hits vs the random-level `pBase`). Recording per-feature lifts lets each chart confirm or reject CL-1 and CL-2 and the sibling claims, and later feed bounded multipliers.
- **Spec** (on top of the sibling CAL-3 / ICT-1 candidate ledger; if absent, use per-trial bits on active-target trials). Each graded candidate stores a bitmask:
  - `XW` = weekly references crossed, 0 / 1 / 2+ (from CL-1);
  - `ATW` = a weekly reference within tol of the pool;
  - `ATD` = a daily PP/R1/S1 within tol;
  - `ATRN` = a round number (auto step `10^floor(log10(2*dailyATR))` and half step, as in ICT-3) within tol;
  - `ATV` = prior settlement / PP / dayEQ within tol;
  - `TIER` class (chart / STF / HTF / session / PD / PW).

  For each bit, accumulate n, k (hits) and E = ΣpBase. Lift = ((k + 2)/(E + 2)) / ((K + 2)/(E_all + 2)), clamped to 0.8-1.2, active when n ≥ 30, the same algebra as `f_calMult` (1376-1383). Full-view table: "Context lifts: XW1 0.86 · XW2+ 0.71 · ATRN 0.96 …" with n. Optionally multiply the learned lifts into `lv.mult` (default off until n ≥ 100).
- **State:** arrays of size 6 x 3 floats. That is O(bits) per graded candidate, which is cheap.
- **Expected value:** per-symbol truth about classic levels and an honest Terminal readout. It also tunes `wkBarM` without hand edits.
- **Evidence:** moderate for the features (T5/T8). The infrastructure is strongly motivated (sibling CAL-3).
- **Risk:** multiple comparisons. Show the n and the CI, and keep the default "display only".
- **Effort:** M (S if CAL-3 lands first).

### CL-4 (P2, level-source, M) · Gap-gated prior-settlement target ("Target: SETT") for session instruments
- **Why:**
  - The prior settlement / RTH close is reached more often than random from the next session open: +3.5 pp (z 3.7) on CME at H = 24, +3.4 pp at H = 8.
  - When price is far from it at the open (a gap of at least 0.5 daily ATR) it fills more than random: +7.9 pp (z 4.5) on NDX, mostly after gap-downs.
  - Small gaps show no excess.
  - Index-futures opening reversals are documented (P13).
  - This is the one classic level with a genuine (small) magnet effect, and traders know it as "gap fill / back to settlement".
- **Inputs** (G_KEY):
  - `bool useSett = input.bool(false, "Prior Settlement (gap fill)")`
  - `string sessRTH = input.session("0930-1600", "Cash / RTH Session")`
  - `float gapMin = input.float(0.5, "  Min Gap (x daily ATR)", minval = 0.0, step = 0.05)`

  Crypto has no gap: disable it automatically when `syminfo.type == "crypto"`.
- **State:**
  - Track the last close inside `sessRTH` using the `f_sessTrack` pattern (842-868): `var float sett`, updated when `inS` and the bar is confirmed.
  - At the first bar of the next RTH session (`inS and not inS[1]`), compute `atrD = nz(atrSlow) * math.sqrt(86400.0 / chartS * (390.0 / 1440.0))`, an RTH-scaled daily ATR proxy with no request, and `gapD = math.abs(open - sett) / atrD`.
  - If `gapD >= gapMin` and price has not already touched `sett` this bar, create the Level:
    - `kind 8` (new: a reference line, touch semantics, `isLiquidity()` false);
    - `src 8`, name "SETT", short code "SETT";
    - `price = sett`, top/bottom = sett ± 0.05·atr;
    - `side = sett > close ? 1 : -1`;
    - `anchorBar` = the bar that printed the settlement;
    - `qual = math.min(1.0, gapD / 1.5)`.
  - It expires at the end of the session or when touched.
- **Ledger:** map `kind 8` to a new group 4 in `grp()` (635) and `f_grpName` (543), and move "all" to index 5. Resize `stN/stK/stPE/stPV/stMae/stBars` to 6 (1066-1071), `f_calMult`'s index 4 → 5, and the `f_book` loop `array.from(t.grp, 5)`. This lets EDGE per family measure SETT separately.
- **Expected value:** a valid early-session DOL for gap days, measured by the ledger. Off by default.
- **Evidence:** weak-moderate (own tests: NDX strong but on cash-index data, the CME futures sample is small; literature P13/P14 is mixed on direction).
- **Risk:**
  - It overlaps the sibling ICTPD-6 (NDOG): implement one object, not two.
  - On 24h futures charts the "gap" is the overnight move, and that was only tested at the Globex open (SETT +3.5 pp), not at 09:30.
  - `kind 8` would otherwise flow through the array code paths: `isArray()` is `kind >= 2`, which brings in partial-fill / CE delivery (`delivIn`), origin lockout, and FVG / OB rendering and names. Guard them with `kind == 8` checks, or treat it like an array with `fill` fixed at 0 and `src` ≠ 0, so the origin lockout never applies.
- **Effort:** M.

### CL-5 (P3, level-source, S) · Monthly high / low pools (PMH / PML) for Swing mode
- **Why.** In Swing mode (W / D / 4H) PDH/PWH are often already near or taken. Monthly extremes are the natural external liquidity that swing traders watch, and users expect them. Evidence of extra reach is **neutral** (T2: +0.3 pp at 5 days; -3.6 / +1.8 at 20 days). This is completeness, not an edge.
- **Spec:**
  - `[pmNew, pmH, pmHB, pmL, pmLB] = f_rangeTrack(timeframe.change("M"))` next to 945-946.
  - `bool useKeyM = input.bool(false, "PMH / PML")`.
  - Push to the registry like 1795-1799 with `src 9`. `f_tierW(9)` = **0.80** (not above PW).
  - `hlMult = math.sqrt(2592000.0 / chartS)`.
  - Names "PMH" / "PML" in `f_levelName` (520-521).
  - The anchor is clamped by `f_x` (404-405) on low timeframes.
- **Evidence:** weak (neutral reach).
- **Risk:** low. It adds candidates the ledger grades at the baseline rate.
- **Effort:** S.

### CL-6 (P3, visual-ux, S) · Optional classic-levels overlay, display only, with honest tooltips
- **Why.** Many traders use pivots, Camarilla and VWAP and look for them, and several competitors plot them. Showing the **weekly references** that CL-1 uses also explains why a target got a lower score.
- **Spec:**
  - `string clsShow = input.string("Off", "Reference Overlay", options = ["Off", "Weekly Refs", "Weekly + Daily Pivots"], group = G_DISP)`.
  - Draw short dotted lines from the period's first bar to `xR`, with tiny right-edge labels: "W-PP", "W-R1", "W-S1", "W-O", and optionally "PP", "R1", "S1".
  - Draw them on `barstate.islast` with the existing `dLn` / `dLb` recycling, at most 8 lines and 8 labels. Use theme `dim` colours. Never in Clean style unless the user selects it.
  - Tooltip: "Weekly reference: measured as a barrier for targets beyond it (study T8); not a magnet."
- **Evidence:** n/a (UX).
- **Risk:** clutter. Off by default.
- **Effort:** S.

---

## 5. Do NOT add (evidence-based)

| Item | Why not |
|---|---|
| Daily floor / Camarilla / Fibonacci / Woodie / DeMark pivots as targets or positive confluence | T1: edges -3.0 to +1.2 pp, the same as range-scaled placebos. Terminal test null. T5: confluence sign flips between datasets. T8: not barriers. P4: an FX thesis rejects the traditional use. |
| Narrow-CPR trend-day rule (volatility / PoT input) | T6: reversed or inconsistent. |
| "Above pivot / VWAP / open = bullish" in the draw vector D | T7: no out-of-sample gain over geometry on CME or BTC. `bias_dol.md`: the same for opens. |
| Monthly / quarterly / yearly opens, monthly pivots as targets | T2: reached *less* than random (-1 to -4 pp, z to -3.8). |
| Session VWAP as a static DOL target | A frozen VWAP is weak (+1.5 CME, +0.3 BTC). The moving line is hit mostly mechanically, and its edge against the ledger's static baseline would be fake. If it is ever added, the baseline must be a moving TWAP placebo. |
| VWAP σ-bands, weekly / monthly AVWAP, prior-day VWAP as targets | T4/T1: null or negative (BTC AVWAP -2.8 to -2.9 pp, z -3.7). |
| Naked / virgin pivots (and naked POCs) | T1: -1.2 to +0.8 pp. `amt_profile.md`: naked POC -2.3 to -4.7 pp. |
| 52-week / ATH with elevated tier (0.95 / 1.0) | T2: baseline at 5 and 20 days. Do not rank above PW (applies to ACAD-5). |
| Round numbers as a *positive* confluence anchor | T5: -1.0 to -1.4 pp ("at" -2.3 / -2.6). Siblings: stop short. |
| Option-strike pinning | Needs open interest (not in Pine). The effect is gone since 2016 (Elms 2026). |

---

## 6. Coordination with sibling proposals
- **ICT-3 (round numbers, `ict_liq.md`):** keep the *stop-depth extension* (zone drawn just past the round). **Drop** "push round levels into the confluence anchors" (T5 negative). Optionally count round numbers inside the CL-1 barrier helper with a smaller factor (0.97) once the ledger confirms.
- **ACAD-5 (52-week / ATH, `academic_sr.md`):** fine as pools, but with `f_tierW` ≤ 0.80 (T2 null at DOL horizons).
- **ICTPD-6 (NDOG / NWOG, `ict_pd.md`):** gate gap targets by size (at least 0.5 daily ATR). Small gaps show no fill excess (T3). Merge it with CL-4 into one gap / settlement object.
- **TIME-6 (midnight open as a target, `ict_time.md`):** T2/T5/T8 show opens are not magnets beyond distance, and the weekly / monthly ones are barriers. The midnight open showed a modest excess in `ict_time.md` E10. Keep it ledger-gated and off by default, and do not also give it confluence credit.
- **CAL-3 / CAL-4 (`calib_ml.md`):** CL-3 is a feature list for that ledger. CL-2 agrees with its confluence finding.
- **Tier:** `calib_ml.md` (external -0.27 logit) and T5 by source (PW pools worst on CME) both argue for flattening `1.2*tier` at 682. Let the ledger learn TIER (CL-3).

---

## 7. Reproduction

All study code is in `/tmp/claude-0/-home-user-m/7ce60006-3639-59b1-8cd3-87355409d58a/scratchpad/brief/study/classic_tools/`. Run it with `python3 -I`. The per-trial CSVs are gzipped.
- `mk_btc1h.py`: Bitstamp 1-minute data → `btc_1h.csv`.
- `clib.py`: loaders, ATR, the excursion `Surface` baseline, the clustered `summ`.
- `t1_daystart.py <cme|btc> <H>`: daily-derived levels from the session open (→ `out_t1_*`).
- `t2_htf.py <H>`, `t2_sum.py`: daily HTF levels (→ `out_t2_*`).
- `t3_gaps.py`, `t3b.py`: gap fill (→ `out_t3*.txt`).
- `t4_vwap.py <cme|btc> <H>`: VWAP, bands, TWAP, moving lines (→ `out_t4_*`).
- `t5_confluence.py <cme|btc> <H>`, `t5_diff.py <csv> [any|near|at|far]`: confluence (→ `out_t5_*`).
- `t6_cpr.py`: CPR width (→ `out_t6.txt`).
- `t7_bias.py <cme|btc>`: reference-side bias vs geometry (→ `out_t7_*`).
- `t8_path.py <cme|btc> <H>`, `t8_an.py <csv> [strat] [age]`: path barriers (→ `out_t8_*`).

Limitations:
- The CME sample is 13 months. BTC is a single 24/7 asset.
- The hourly tests may not carry over to 1-5 minute charts with H = 30 bars.
- The NDX gap result uses cash-index opens.
- Many tests were run. Treat |z| < 3 effects that are not replicated across datasets as exploratory. CL-1's weekly-pivot barrier and CL-2's negative weekly / open confluence are replicated with |z| ≥ 3.3 in both datasets.

---

## 8. Sources
- Osler, C. (2000). Support for Resistance: Technical Analysis and Intraday Exchange Rates. FRBNY Economic Policy Review 6(2). https://www.newyorkfed.org/research/epr/00v06n2/0007osle ; PDF https://resources.newyorkfed.org/medialibrary/media/research/epr/00v06n2/0007osle.pdf
- Osler, C. (2003). Currency Orders and Exchange-Rate Dynamics. J. Finance 58(5); FRBNY SR125 https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr125.pdf
- Kavajecz, K., Odders-White, E. (2004). Technical Analysis and Liquidity Provision. Review of Financial Studies 17(4): 1043-1071. https://ideas.repec.org/a/oup/rfinst/v17y2004i4p1043-1071.html
- Johnsson, O., Frykmer, D. (2019). Pivot Point Trading in the Foreign Exchange Market: A Test for Market Efficiency. Lund University MSc thesis. https://lup.lub.lu.se/student-papers/search/publication/8979805
- Bulkowski, T. Pivot Points (test results). https://thepatternsite.com/PivotPoints.html
- Steenbarger, B. pivot-level support and resistance (TraderFeed, 2007). https://traderfeed.blogspot.com/2007/10/pivot-level-support-and-resistance-how.html ; Babypips forum relay https://forums.babypips.com/t/pivot-point-statistics/573135
- FXNX, pivot point hit rates. https://fxnx.com/en/blog/pivot-point-hit-rates-r1-s1-daily-pivot-tested
- Tradeify, pivot points (ES 500 sessions). https://tradeify.co/education/pivot-points ; gap strategies https://tradeify.co/education/gap-trading-strategies
- Edgeful, pivot points report guide. https://www.edgeful.com/blog/posts/pivot-points-report-full-guide ; weekly-open retracement https://www.edgeful.com/blog/posts/weekly-open-retracement-report ; midnight-open retracement https://www.edgeful.com/blog/posts/ICT-trading-strategy-midnight-open-retracement-report
- Barchart, Camarilla pivot points. https://www.barchart.com/education/technical-indicators/camarilla_pivots ; LuxAlgo Camarilla https://www.luxalgo.com/library/concept/camarilla/ ; takeprofitapp Camarilla https://takeprofitapp.com/en/learn/camarilla-pivot-points
- LuxAlgo, Central Pivot Range. https://www.luxalgo.com/library/concept/central-pivot-range/ ; CPR & Camarilla Stats script https://www.tradingview.com/script/F5MZa2fK/
- Babypips, other pivot point calculation methods (Fibonacci, Woodie, DeMark). https://www.babypips.com/learn/forex/other-pivot-point-calculation-methods
- Zarattini, C., Aziz, A. (2023). VWAP: The Holy Grail for Day Trading Systems. SSRN 4631351; summary https://concretumgroup.com/volume-weighted-average-price-vwap-the-holy-grail-for-day-trading-systems/ ; replication discussion https://www.quantconnect.com/forum/discussion/16706/
- StockCharts ChartSchool, Anchored VWAP. https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-overlays/anchored-vwap ; TrendSpider AVWAP https://trendspider.com/learning-center/anchored-vwap-trading-strategies/
- VWAP execution benchmark share (working paper). https://core.ac.uk/download/201501336.pdf ; arXiv 2502.13722 https://arxiv.org/html/2502.13722v1
- Grant, J., Wolf, A., Yu, S. (2005). Intraday price reversals in the US stock index futures market: A 15-year study. J. Banking & Finance 29(5): 1311-1327. https://ideas.repec.org/a/eee/jbfina/v29y2005i5p1311-1327.html
- Boyarchenko, N., Larsen, L., Whelan, P. The overnight drift (NY Fed SR917; Liberty Street Economics 2021). https://libertystreeteconomics.newyorkfed.org/2021/05/the-overnight-drift-in-us-equity-returns
- Lou, D., Polk, C., Skouras, S. A Tug of War: Overnight versus Intraday Expected Returns. https://personal.lse.ac.uk/polk/research/TugOfWar.pdf
- Gap-fill statistics: stockwirex https://stockwirex.com/?p=39795 ; thetrading.tools https://www.thetrading.tools/gap-analysis
- Ni, S., Pearson, N., Poteshman, A. (2005). Stock price clustering on option expiration dates. J. Financial Economics 78(1): 49-87. https://ideas.repec.org/a/eee/jfinec/v78y2005i1p49-87.html
- Golez, B., Jackwerth, J. (2012). Pinning in the S&P 500 futures. J. Financial Economics 106(3): 566-585. https://ideas.repec.org/a/eee/jfinec/v106y2012i3p566-585.html ; "From Pinning to Amplification" summary of Elms (2026) https://harbourfrontquant.substack.com/p/from-pinning-to-amplification-evidence
- CME Group, E-mini S&P 500 daily settlement procedure / SER-8591 (2020). https://cmegroup.com/notices/ser/2020/09/SER-8591.pdf ; https://cmegroupclientsite.atlassian.net/wiki/x/E4DaBw
- George, T., Hwang, C.-Y. (2004). The 52-Week High and Momentum Investing. J. Finance 59(5). https://www.bauer.uh.edu/tgeorge/papers/gh4-paper.pdf
- Sibling studies used: `ict_liq.md` (round numbers ICT-3, E1-E2), `orderflow_micro.md` (round-number bar tests), `academic_sr.md` (52-week, ACAD-5), `ict_pd.md` (NDOG/NWOG ICTPD-6), `ict_time.md` (midnight open), `bias_dol.md` (open-relative bias), `amt_profile.md` (naked POC), `calib_ml.md` (confluence -0.25 logit, CAL-3).
