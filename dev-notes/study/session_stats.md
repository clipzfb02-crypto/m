# Session / day / week statistics: study for DOL Engine v2

Domain: published and reproducible statistics on sessions, days and weeks for ES/NQ/YM/RTY, CL, (GC), EURUSD and BTC:
- PDH/PDL taken next day, and in which session;
- which session prints the daily high/low;
- Asia / London / NY AM / overnight ranges and whether later sessions take them;
- what happens after the first break of a range;
- ADR distribution, "ADR exhaustion" and range-used state;
- weekday of the weekly high/low, PWH/PWL during the week, Monday range;
- gap fills (RTH, weekend FX, BTC "CME gap");
- ORB / IB / NR7 / inside days, from sibling studies and external sources.

The goal is priors for the engine: which key level is taken, when, and with what probability.

Line numbers refer to `brief/baseline_v2.pine` (identical to `indicators/dol_engine.pine`).

Sibling studies cover adjacent ground and are referenced rather than repeated:
- `ict_time.md`: volatility clock, killzones, session-window bugs, TIME-1..9.
- `quant_pot.md`: PoT models, QPOT-01..09.
- `bias_dol.md`: previous-candle statistics, NR7/inside, BIAS-1..7.
- `amt_profile.md`: IB, overnight, value area.
- `ict_pd.md`: opening gaps as PD arrays, ICTPD-6.
- `orderflow_micro.md`, `quant_regime.md`.

**Reproduction.** Every number tagged **[this study]** comes from the scripts in `study/session_tools/`. Run them with `python3 -I <script> <args>` from that folder; outputs go to `out_*.txt`.

| Script | What it computes |
|---|---|
| `daystats.py` | PD, sessions, hazard, exhaustion, ADR |
| `afterbreak.py` | What happens after the first break of a range |
| `pooled.py` | Pooled tables across datasets |
| `hazmodels.py` | Causal model comparison |
| `weekly.py` | Weekly statistics |
| `gaps.py` | Gap fill vs mirror |
| `nullcheck.py` | Null calibration check |
| `sesslib.py` | Shared helpers |

**Research-tool note.** The Firecrawl account ran out of credits at the start of this study, and WebFetch could not resolve the vendor hosts (edgeful.com, nexusfi.com, linnsoft.com, trevor-trades.vercel.app). Those hosts would need to be allowed in the session's network settings. External numbers below therefore come from search-engine result snippets (marked *snippet*) or from sibling studies that read the pages. The core evidence is this study's own reproducible computation.

---

## 0. Executive summary

1. **Every popular session / day / week statistic I could reproduce is, to within a few points, what a random path with the right clock and the right volatility does from the same starting price.** I compared real outcomes to a **day-bootstrap null**: another day's whole path, rescaled by ADR and placed at today's price at the same clock time. The null keeps the intraday volatility clock, within-day clustering and the day-range distribution (checked, §2.0). It breaks only the link between today's path and today's levels. Against it:
   - **PDH/PDL take rates.** Real is within about ±3 pp of the null on 7 markets.
     - ES PDH 58.8% vs 57.0%, PDL 44.4% vs 43.7%.
     - BTC 48.6% vs 51.6% and 41.4% vs 44.0%.
     - EURUSD 56.2% vs 56.6% and 40.6% vs 43.5%.
   - **Session that first takes PDH.** ES by end of Asia 25.6% vs 30.1%; by end of NY AM 51.2% vs 50.6%.
   - **Session that prints the HOD/LOD.** Within ±2 pp of the null (ES high: NY PM 45.6% vs 46.1%).
   - **Asia and London ranges taken later the same day.** Within ±3 pp, mostly.
   - **Weekday of the weekly high/low.** The arcsine U-shape: Mon/Fri 23-34%, Tue-Thu 12-18%, equal to a day-order shuffle.
   - **"Weekly low by Tuesday in up weeks".** 72-75% vs the null's 76-77%.
   - **PWH/PWL during the week.** Within ±3 pp.

   So session/day/week levels are **real, frequent targets, but they are not stronger magnets than geometry says.** Hard-coded session affinities (`f_kzAff`, lines 597-602, applied at 1941) and weekday priors have no support. [this study]

2. **The residuals that do survive are small, consistent in sign, and of one kind: once one side of a range breaks, the other side is taken less often than random.** This is a continuation/trend effect.

   | Range | Opposite side after the first break, real − null |
   |---|---|
   | PDH/PDL | −1.9 pp on average (−5.4 to +1.3 across 7 markets) |
   | NY AM range (10:00-12:00) | −3.1 pp on average (−0.5 to −5.7) |
   | PWH/PWL | −1.6 to −6.5 pp |
   | "Both PDH and PDL taken the same day" | below the null in 6 of 7 markets: −0.5 to −5.8 pp, NQ +0.5 |

   - The exception is the **Asia range (20:00-00:00 ET) on index futures**: after its first break the other side is taken **more** often than random, +3.5 to +6.2 pp on ES/NQ/YM/RTY (≈3 SE pooled). That is a measurable "Judas"-type two-sided raid.
   - The Asia exception does not appear in CL (−1.2), EURUSD (+0.5) or BTC (−1.3).
   - These effects belong in a learned, per-chart table, not in fixed multipliers. [this study]

3. **ADR "exhaustion" is false. A used-up ADR predicts *more* extension, not less.** Test: from each hour, does price extend beyond the running day extreme by x·ADR before the day ends? Compare to the ADR-scaled null.
   - When the day has already used ≥ 1 ADR, real extension exceeds the null by +4 to +10 pp:
     - indices x = 0.10: 26.3% vs 20.4%;
     - BTC x = 0.25: 15.7% vs 6.6%.
   - When the day has used < 0.4 ADR, real is 2-6 pp **below** the null.
   - Logistic coefficient of log(range used) beyond the null:
     - indices +0.215 (se 0.013);
     - BTC +0.230 (0.008);
     - CL +0.10 (0.03);
     - EURUSD 2017-18 −0.03 (0.03).
   - The weekly version is the same: SPX/NASDAQ weeks that used ≥ 1.1 AWR by Wednesday extend 0.25 AWR further 24-27% of the time vs 15% under the null.
   - This is volatility clustering, the "intraday component" of Engle & Sokalska's (2012) daily × diurnal × intraday variance model.
   - **Design consequence:** never cap reach at "ADR remaining". Instead **scale the forward variance by today's range-so-far relative to the normal range by this hour** (proposal SESS-1). [this study]

4. **Horizon matters as much as distance.** For an untaken PDH/PDL at the same distance, P(taken by day end) collapses through the day. Pooled ES/NQ/YM/RTY, distance 0.2-0.35 ADR: **64% when the forecast is made in Asia → 57% in London → 47% in NY AM → 19% in NY PM.**
   - The engine's PoT uses a fixed H-bar horizon (line 305, default 30 bars) and a time-blind σ (line 916). It cannot answer "today?".
   - Causal model comparison for "PDH/PDL taken by day end" (Brier after 2-fold time-split recalibration):

     | Model | IDX | CL | EURUSD | BTC |
     |---|---|---|---|---|
     | Engine-like flat σ | 0.1508 | 0.1373 | 0.1342 | 0.1284 |
     | + volatility clock | 0.1477 | 0.1380 | **0.1308** | 0.1274 |
     | + clock × today factor | **0.1436** | **0.1346** | 0.1344 | **0.1261** |

     The best model beats the flat σ by −4.8% (IDX), −2.0% (CL), −2.5% (EURUSD, clock only) and −1.8% (BTC). [this study]
   - Uncalibrated, the ADR-based analytic over-predicts BTC by about 11 pp (mean p 0.33 vs 0.22). **The level of the variance must be learned per chart**, which is why SESS-2 is an empirical surface and not a formula.

5. **ADR profile, very consistent across 8 markets** [this study]:

   | Statistic | Value |
   |---|---|
   | Day range / ADR14, median | 0.87-0.97 |
   | P(≥ 1 ADR) | 38-46% |
   | P(≥ 1.5 ADR) | 10-16% |
   | P(≥ 2 ADR) | 2.4-7.3% |
   | Max excursion from the open, larger side, median / 80th / 95th | 0.66-0.76 / 1.01-1.12 / 1.41-1.97 ADR |
   | Counter-move from the open (smaller side), median / 80th / 95th | 0.17-0.20 / 0.32-0.36 / 0.49-0.53 ADR |
   | Lag-1 autocorrelation of range/ADR | 0.19-0.41 (futures, BTC); 0.00 EURUSD 2017-18 |

   ADR is a good **unit** (distances in ADR are comparable across symbols and timeframes). It is a bad **cap**.

6. **Gaps.** "Gaps must fill" is not supported beyond distance.
   - **BTC "CME gap"** (Fri 17:00 ET → Sun 18:00 ET, spot, 415 weekends):
     - fills within 4 weeks 86.7%, against 89.4% for a **mirror level** at the same distance on the other side;
     - gaps > 1 ADR fill 43.5% vs mirror 78.3%: large gaps continue.
   - **EURUSD weekend gaps:** fill = mirror (73.2% vs 73.0% on Monday).
   - **Index-futures RTH opening gaps** (n = 204, 2026 only) fill +6.9 pp more than the mirror, growing with size. That is consistent with the documented opening reversal, but the sample is small.
   - Plastun et al. (2020, 1928-2018 US indices) also reject the fill myth (momentum in the gap direction).
   - Feed this into ICTPD-6 as "no fixed gap prior". [this study]

7. **Best proposals** (§4). They complement, not repeat, TIME-1/TIME-4/QPOT-02/QPOT-05:
   1. **SESS-1 (P1):** day-state variance ("today factor") from the engine's own day tracker, plus ADR as a unit. Explicitly no ADR cap.
   2. **SESS-2 (P1):** a learned key-level **day-end hazard surface**: time bucket × distance in ADR × "opposite side already taken". It powers a "PoT today" for PDH/PDL/PWH/PWL/session targets and grades itself by Brier.
   3. **SESS-3 (P2):** replace `f_kzAff` and the probability role of source tiers with a bounded multiplier derived from SESS-2, neutral until learned. Per-family ledger split.
   4. **SESS-4 (P2):** day/week context readout and key-level taken alerts.
   5. **SESS-5 (P3):** weekly horizon and week-state for PWH/PWL.
   6. **SESS-6 (P3):** day-boundary input and ADR distance units.

---

## 1. Concepts: definitions and parameters

Notation:
- "Taken" = traded **through** (strict `>` / `<`), matching the engine's liquidity touch (`touched`, line 623).
- ADR14 = mean of the prior 14 full-day ranges (H − L), known at the day open. AWR10 is the weekly equivalent.
- Day definitions:
  - CME: 18:00-17:00 ET (the TradingView daily session, what `timeframe.change("D")` uses).
  - FX: 17:00-17:00 ET.
  - Crypto: 00:00-24:00 UTC.
- Sessions in New York time (1-hour resolution in this study): Asia 18:00-02:00, London 02:00-08:00, NY AM 08:00-12:00, NY PM 12:00-17:00.
- The engine's own windows (inputs 107-109, 223-226): Asia range 20:00-00:00, London 02:00-05:00, NY AM 09:30-12:00 (10:00-12:00 on a 1H chart, see ict_time G3).

### 1.1 PDH / PDL taken next day
- **Definition.** P(next day's high > prior day's high). The same for the low, both, or neither.
- **Conditioned on the open location:**
  - above PDH (gap beyond);
  - upper half of the prior range;
  - lower half;
  - below PDL.
- **Edge cases:**
  - A gap beyond the level = taken at the open. The engine does not push such a level (`f_pushExt` requires `high <= px`, line 1212).
  - Holidays and short days: dropped when < 20 hourly bars.
  - Weekends: the prior day is the previous trading day.
- **Practitioner use:**
  - "PDH/PDL is the day's first draw."
  - ICT daily bias: closed above PDH → PDH+ next. See bias_dol §1.3; the bias rule adds nothing beyond geometry there.
  - edgeful-style: "PDH broken → green session 67%".
- **Probability driver.** Distance from the open in ADR units, then time left.

### 1.2 Session of first take; session of the HOD/LOD
- **Definitions:**
  - The session containing the first bar that trades through the level.
  - The session containing the bar that prints the day's high (first print on ties).
- **Practitioner use:**
  - "London makes the high or low of the day."
  - "NY takes London's high or low."
  - Killzone timing.
- **Null logic.** The time of an extreme follows the arcsine law in business (variance) time (ict_time §2.3). The first and last high-variance slices get the mass.

### 1.3 Session ranges and later raids
- **Definition.** H/L of a fixed clock window. After the window closes, record whether each side is traded through before the day ends:
  - single break (one side);
  - double break (both);
  - none.
- Windows tested:
  - Asia 20:00-00:00 (engine);
  - Asia 18:00-02:00;
  - London 02:00-05:00 (engine);
  - London 02:00-08:00;
  - NY AM 10:00-12:00 (engine on 1H);
  - overnight 18:00-09:00 (ONH/ONL proxy at 1-hour resolution).
- **Width conditioning.** Session width in ADR terciles.

### 1.4 After the first break of a range ("one side taken")
- **Definition.** For a range [L, H] (PD, PW, Asia, London, NY AM, ON), let the first through-trade of either side happen on bar k. Measure, until the day (week) end:
  - (a) P(the opposite side is also taken);
  - (b) P(the broken side extends +0.25 / +0.5 ADR beyond the level);
  - (c) P(the day closes back inside the range): the failed-break rate.
- A same-bar double break is ambiguous and excluded.
- **Practitioner use:** "sweep and reverse to the other side" (Judas, Turtle Soup) vs "break and run".

### 1.5 Time-of-day hazard of an untaken key level
- **Definition.** At each hour boundary t, for each untaken PDH/PDL:
  - d = distance from the close to the level, in ADR units;
  - outcome y = taken by day end.
- Tabulate P(y | d bin, session at t).
- **Engine relevance.** This is the "PoT today" a trader means. It needs a horizon that ends at the session or day end, not a fixed bar count.

### 1.6 ADR, range used, "ADR exhaustion"
- **ADR(N).** Mean of N prior daily ranges (N = 5, 10, 14 or 20 in practice).
- **Practitioner rules:**
  - "When price has done its ADR, the day's extremes are in".
  - "Targets beyond the ADR projection are unlikely".
  - ADR projections from the open: open ± ADR, or day low + ADR / day high − ADR.
- **Test.** At hour t, the range used so far is u = (running high − running low)/ADR. Does P(extend beyond the running extreme by x·ADR before the day ends) fall with u (exhaustion) or rise (clustering), relative to a null that only knows ADR?
- **"Today factor".** ratio = range so far / E[range so far at this clock time]. It is a day-state variance multiplier.

### 1.7 Weekly: weekday of the weekly extreme, PWH/PWL, Monday range
- **Weekday of the weekly high/low.** First print within full weeks (5 trading days; 7 for BTC).
- **ICT weekly profiles:** "Tuesday low of week", "Wednesday reversal", and so on (ict_time §1.10).
- **PWH/PWL.** P(taken during the week); the weekday of the first take.
- **Monday range.** P(Monday's high/low is taken Tue-Fri).

### 1.8 Opening range breakout (Crabel), initial balance (IB), NR7 / inside day
- **ORB (Crabel 1990).** Stop orders a fixed "stretch" above and below the open. The stretch is the average of the smaller of (high − open, open − low) over the last 10 days. The first one hit gives the direction.
  - Note: this study measures the "smaller-side excursion from the open" at a median of 0.17-0.20 ADR. That is the Crabel stretch in ADR units.
- **IB.** RTH 09:30-10:30 range. Range extension = trade beyond it (amt_profile §1.11).
- **NR7.** The day's range is the smallest of the last 7.
- **Inside day.** H ≤ H[1] and L ≥ L[1].
- **Practitioner use.** Contraction → expansion breakout in either direction; trade the first break.
- Evidence comes from siblings (§2.8). Not re-run here.

### 1.9 Gaps
- **RTH gap.** 09:30 open vs the prior 16:00 close (index futures).
- **Weekend gap.** Friday close vs Sunday open.
  - FX: 17:00 ET.
  - BTC "CME gap": the spot price at the CME Friday 17:00 ET close vs the Sunday 18:00 ET reopen.
- **Fill.** Price trades back to the pre-gap close within the window.
- **Mirror.** Price trades the same distance in the gap's direction. Under a driftless walk, P(fill) = P(mirror). So **fill − mirror** isolates any magnet effect from pure distance.

---

## 2. Evidence (numbers and sources)

### 2.0 Data and method [this study]

**Datasets**

| Dataset | Coverage | Days / weeks | Notes |
|---|---|---|---|
| CME ES, NQ, YM, RTY, CL, GC, 1-hour (UTC, converted to NY) | 2025-03-21 → 2026-04-15 | 266 Globex days, 250 valid (CL 178) | from `amt_data/cme` (sibling AMT study). **GC has contract-roll gaps and is excluded from conclusions** (the null's range/ADR is 0.71 vs real 1.05) |
| ES/NQ/YM/RTY 1-minute | 2026-01-20 → 2026-04-15 | ≈ 60 RTH days each | RTH gaps only |
| EURUSD 1-hour (UTC) | 2017-04-19 → 2018-02-07 | 207 days, 192 valid | `bias_data/EURUSD.csv` |
| BTCUSD Bitstamp 1-minute → 1-hour | 2017-01-01 → 2025-01-06 | 2,928 UTC days, 2,913 valid | public GitHub dataset `ff137/bitstamp-btcusd-minute-data`. Cached as `session_data/btc_1h.pkl`; the raw file was deleted after caching |
| S&P 500, NASDAQ Composite daily | 1999-2018 | 863 full weeks, 694 valid | `bias_data` |
| EURUSD OANDA daily (17:00 NY sessions) | 2002-05 → 2026-04 | 1,220 full weeks | `dl_knn/.../pine_oanda_eurusd_1d_full_history.csv` |
| BTCUSD Coinbase daily | 2014-12 → 2026-05 | 591 full 7-day weeks | same folder |

**Null models**

- **Day-bootstrap (primary).**
  - A donor day's hourly path from the forecast slot onward is normalised: H, L and C relative to the slot open, ÷ the donor's ADR14.
  - It is rescaled by today's ADR14 and chained from today's real price at that slot.
  - Calibration check (`nullcheck.py`), mean range/ADR real vs null:

    | ES | NQ | YM | RTY | CL | EURUSD | BTC |
    |---|---|---|---|---|---|---|
    | 0.999 / 1.000 | 1.000 / 1.005 | 0.991 / 0.977 | 0.998 / 0.994 | 1.078 / 1.087 | 1.031 / 1.035 | 1.051 / 1.046 |
- **Slot null (random walk on the clock).** Each hour is drawn from a random day's same slot.
  - It matches ict_time's baselines.
  - It overstates BTC and CL ranges (median null range/ADR 1.03 vs real 0.87 for BTC), because shuffling hours destroys within-day clustering.
  - It is reported in `out_*_slot.txt` for comparison. Conclusions use the day null.
- **Weekly nulls.** Week-bootstrap (a donor week's normalised daily path). For the weekday-of-extreme test, a day-order shuffle within the week.
- **Gaps.** The mirror level (§1.9).

**Caveats**
- The four index futures share the same 250 days and are highly correlated. The pooled n overstates independence: treat the effective sample as roughly 1.5× one symbol.
- Hour-boundary records within a day overlap, so the naive logistic SEs are optimistic.
- Hourly resolution: same-bar double breaks are excluded. The 09:00 bar mixes premarket and RTH.
- The day null uses donors from the whole sample (in-sample shapes). The causal model comparison (§2.6) uses only past data.

### 2.1 PDH / PDL taken during the next day [this study, `daystats.py` §A]

All days, real vs day-bootstrap null:

| Market | P(PDH) | P(PDL) | both | neither | null P(PDH) | null P(PDL) | null both | null neither |
|---|---|---|---|---|---|---|---|---|
| ES | 0.588 | 0.444 | 0.144 | 0.112 | 0.570 | 0.437 | 0.149 | 0.142 |
| NQ | 0.596 | 0.436 | 0.144 | 0.112 | 0.571 | 0.435 | 0.139 | 0.133 |
| YM | 0.524 | 0.488 | 0.104 | 0.092 | 0.536 | 0.461 | 0.131 | 0.134 |
| RTY | 0.492 | 0.468 | 0.100 | 0.140 | 0.550 | 0.452 | 0.143 | 0.141 |
| CL | 0.511 | 0.416 | 0.079 | 0.152 | 0.525 | 0.466 | 0.137 | 0.146 |
| EURUSD 17-18 | 0.562 | 0.406 | 0.099 | 0.130 | 0.566 | 0.435 | 0.124 | 0.123 |
| BTC 17-24 | 0.486 | 0.414 | 0.107 | 0.207 | 0.516 | 0.440 | 0.154 | 0.198 |

- **By open location** (real / null):
  - ES, open in the upper half: PDH 0.754 / 0.755, PDL 0.246 / 0.273.
  - ES, open in the lower half: PDH 0.319 / 0.294, PDL 0.692 / 0.639.
  - BTC upper half: PDH 0.657 / 0.678. BTC lower half: PDL 0.604 / 0.633.
  - Opens beyond PDH/PDL are rare: ES 25 of 250 days, BTC 6 of 2,913 (continuous trading).
- **Distance gradient** (ES, opens inside the range, P(PDH by day end) real / null):

  | d/ADR | 0-0.1 | 0.1-0.2 | 0.2-0.35 | 0.35-0.5 | 0.5-0.75 | 0.75-1 | ≥ 1 |
  |---|---|---|---|---|---|---|---|
  | real / null | 0.97 / 0.94 | 0.77 / 0.84 | 0.56 / 0.70 | 0.50 / 0.57 | 0.31 / 0.35 | 0.38 / 0.22 | 0.16 / 0.08 |

  The far tail is fatter than the null, because big days cluster.
- **Which of PDH/PDL first** (opens inside, decided days):
  - The ruin rule "nearer side first" is right 79.7% (ES), 76.3% (NQ), 78.4% (EURUSD) and 76.3% (BTC). This confirms bias_dol's geometry finding.
  - When both are taken: from the upper half, PDH first 67% (ES) / 69% (BTC); from the lower half, 18% / 24%.
- **External agreement:**
  - Elite Trader user count: ES PDH or PDL touched 90.32% of days (168/186), via bias_dol. Here, "neither" is 11.2% for ES (88.8% at least one).
  - edgeful SPY inside-day report: PDH 52%, PDL 40%, both 15.3% (72 days), via bias_dol.
  - Linnsoft, ES: prior **close** touched on 1,048 of 1,803 days (58.1%) (*snippet*, linnsoft.com/homework).
- **Reading.** PDH/PDL are frequent targets: at least one side is taken 79-91% of days. Their take rate is geometry. "Both sides" is **rarer than random** in 6 of 7 markets: −0.5 to −5.8 pp, NQ +0.5 (a "one side per day" tendency).

### 2.2 When PDH/PDL is first taken; when the HOD/LOD prints [this study, §A3, §B]

Cumulative P(PDH taken by the end of each session), real / null:

| Market | by end of Asia | by end of London | by end of NY AM | by day end |
|---|---|---|---|---|
| ES | 0.256 / 0.301 | 0.348 / 0.379 | 0.512 / 0.506 | 0.588 / 0.570 |
| NQ | 0.276 / 0.315 | 0.356 / 0.391 | 0.528 / 0.528 | 0.596 / 0.571 |
| EURUSD | 0.286 / 0.276 | 0.417 / 0.444 | 0.521 / 0.538 | 0.562 / 0.566 |
| BTC (UTC day) | 0.247 / 0.284 | 0.350 / 0.387 | 0.427 / 0.459 | 0.486 / 0.516 |

PDL rows are equally close (ES 0.200 / 0.199 by Asia, 0.396 / 0.381 by NY AM).

Session that prints the day's high / low, real / null:

| Market | HIGH Asia | London | NY AM | NY PM | LOW Asia | London | NY AM | NY PM |
|---|---|---|---|---|---|---|---|---|
| ES | 16.0 / 17.1 | 12.4 / 12.0 | 26.0 / 24.8 | 45.6 / 46.1 | 29.2 / 28.6 | 14.4 / 14.8 | 24.0 / 26.0 | 32.4 / 30.6 |
| NQ | 18.8 / 19.5 | 10.0 / 9.8 | 30.8 / 31.4 | 40.4 / 39.3 | 27.6 / 27.9 | 14.0 / 12.2 | 28.0 / 29.8 | 30.4 / 30.1 |
| YM | 17.6 / 19.0 | 11.6 / 9.6 | 32.4 / 33.9 | 38.4 / 37.4 | 23.2 / 21.8 | 12.8 / 12.4 | 30.4 / 31.7 | 33.6 / 34.1 |
| EURUSD | 24.5 / 24.0 | 24.0 / 23.1 | 27.6 / 27.0 | 24.0 / 25.9 | 31.2 / 32.5 | 24.5 / 25.1 | 27.1 / 24.7 | 17.2 / 17.7 |
| BTC* | 44.3 / 43.3 | 14.7 / 15.5 | 16.7 / 16.8 | 24.3 / 24.4 | 43.8 / 44.1 | 16.7 / 17.1 | 16.3 / 16.0 | 23.2 / 22.9 |

\*BTC UTC day: "Asia" covers both the first ~6 h and the last ~4 h of the UTC day, the arcsine-favoured ends.

- **Median share of the final day range printed by the end of each session:**
  - ES: Asia 0.36, London 0.52, NY AM 0.87.
  - NQ: 0.38 / 0.54 / 0.91.
  - EURUSD: 0.37 / 0.74 / 1.00. EURUSD is done by noon on more than half the days.
  - fxbacktest (ict_time E5): EURUSD 47.9% of the range done by 08:00 UTC, US100 36.5%.
- **External:**
  - DailyFX 2005-2009: the first hour of the FX day set the daily high ~8% and the low ~6% of the time, vs 4.17% uniform (*snippet*). That is the arcsine end effect.
  - mypivots (ict_time E4): ES RTH HOD 17.2% / LOD 16.7% in the first 15 minutes.
  - TradeThatSwing: London high/low broken after the US open, single 70.66%, both 25.1%, neither 4.25% (*snippet*; the headline "98%" contradicts the body).
- **Reading.**
  - "London/NY makes the high or low of the day" is the clock plus arcsine. It equals the null within ±2.5 pp.
  - "Asia takes PDH first" is mostly geometry: Asia trades first from an open near the prior close. Real is slightly **below** the null in Asia (ES −4.5 pp, NQ −3.9, BTC −3.7) and catches up by NY. Overnight is a little quieter than a random day's overnight, which fits the US-index overnight-drift literature (ict_time E13).

### 2.3 Session ranges taken later the same day [this study, §C]

Real / null, after the window closes until the day end. Single = exactly one side taken; none = neither.

**Asia 20:00-00:00 (engine window)**

| Market | high | low | both | none |
|---|---|---|---|---|
| ES | 90.4 / 86.0 | 79.6 / 80.9 | 70.0 / 67.7 | 0.0 / 0.8 |
| NQ | 87.6 / 86.2 | 81.2 / 81.2 | 69.2 / 68.1 | 0.4 / 0.7 |
| YM | 89.2 / 86.1 | 84.4 / 84.6 | 73.6 / 71.1 | 0.0 / 0.4 |
| RTY | 91.6 / 85.4 | 82.8 / 83.6 | 74.4 / 69.4 | 0.0 / 0.4 |
| CL | 78.1 / 81.0 | 81.5 / 77.3 | 60.1 / 60.1 | 0.6 / 1.8 |
| EURUSD | 84.9 / 83.5 | 78.6 / 78.7 | 63.5 / 62.4 | 0.0 / 0.2 |
| BTC | 73.3 / 73.6 | 72.3 / 71.2 | 46.9 / 48.1 | 1.3 / 3.4 |

**London 02:00-05:00 (engine window)**

| Market | high | low | both | none |
|---|---|---|---|---|
| ES | 83.6 / 82.2 | 76.0 / 76.0 | 59.6 / 58.9 | 0.0 / 0.7 |
| NQ | 84.0 / 82.2 | 76.0 / 76.8 | 60.0 / 59.4 | 0.0 / 0.5 |
| YM | 82.8 / 82.3 | 82.0 / 80.3 | 65.2 / 62.9 | 0.4 / 0.3 |
| RTY | 86.0 / 83.6 | 81.2 / 79.6 | 67.6 / 63.7 | 0.4 / 0.5 |
| CL | 73.6 / 74.2 | 70.8 / 66.2 | 44.9 / 42.3 | 0.6 / 1.9 |
| EURUSD | 63.5 / 68.5 | 64.1 / 62.3 | 28.6 / 33.4 | 1.0 / 2.7 |
| BTC | 76.6 / 76.5 | 73.3 / 73.2 | 51.1 / 52.4 | 1.2 / 2.7 |

**NY AM 10:00-12:00 (the engine's window as seen on a 1H chart)**

| Market | high | low | both | single | none |
|---|---|---|---|---|---|
| ES | 59.2 / 59.6 | 45.6 / 46.7 | **13.6 / 19.1** | **77.6 / 68.0** | 8.8 / 12.9 |
| NQ | 58.0 / 57.5 | 45.2 / 44.8 | 16.0 / 17.3 | 71.2 / 67.7 | 12.8 / 15.0 |
| YM | 55.2 / 55.9 | 48.4 / 46.5 | 12.8 / 16.3 | 78.0 / 69.6 | 9.2 / 14.0 |
| RTY | 55.2 / 56.1 | 44.0 / 44.2 | 10.8 / 14.8 | 77.6 / 70.7 | 11.6 / 14.5 |
| CL | 53.9 / 55.2 | 45.5 / 46.2 | 11.2 / 15.8 | 77.0 / 69.9 | 11.8 / 14.4 |
| EURUSD | 47.9 / 51.2 | 42.7 / 42.0 | 9.4 / 11.9 | 71.9 / 69.4 | 18.8 / 18.7 |
| BTC | 64.1 / 65.2 | 60.8 / 61.1 | 30.8 / 35.3 | 63.3 / 55.7 | 5.9 / 9.0 |

**Overnight 18:00-09:00 (ONH/ONL proxy)**

| Market | high | low | both | none |
|---|---|---|---|---|
| ES | 66.8 / 64.9 | 52.4 / 53.1 | 23.2 / 26.2 | **4.0 / 8.2** |
| NQ | 66.8 / 64.1 | 54.8 / 53.5 | 25.2 / 25.1 | **3.6 / 7.4** |
| YM | 67.2 / 68.5 | 60.8 / 59.7 | 31.6 / 33.7 | 3.6 / 5.5 |
| RTY | 67.6 / 64.6 | 60.8 / 56.3 | 34.8 / 28.4 | 6.4 / 7.5 |
| CL | 44.9 / 49.1 | 46.1 / 47.4 | 10.7 / 13.1 | 19.7 / 16.7 |
| EURUSD | 45.8 / 45.4 | 36.5 / 38.1 | 4.7 / 6.9 | 22.4 / 23.3 |

- **Width conditioning** (ES, the full 18:00-02:00 Asia range):
  - narrow tercile: both sides taken 69.9% / 72.9%;
  - wide tercile: 38.1% / 26.0%.
  - Narrow ranges get taken on both sides more often, by geometry. Wide Asia ranges are taken on both sides **more than random**, which fits a two-sided "raid" of a large Asia range.
  - The NY AM range shows the opposite. In its narrow tercile (< 0.32 ADR, n = 83), both sides are taken 19.3% vs 35.9% under the null: a narrow late-morning range resolves to one side.
- **External:**
  - fxbacktest via ict_time E6: Asian range 00:00-06:59 UTC; EURUSD high 68.2, low 68.4, both 37.7, neither 1.0; US100 82.0 / 73.8 / 56.2 / 0.4.
  - edgeful YM via ict_time E9: NY vs London single 83.2, double 4.8, none 12.0; IB single 76, double 20, none 4.
  - tradingstats NQ via ict_time E11: ON range in RTH, only H 38.7, only L 32.6, both 22.9, none 5.8; 94.2% at least one side.
  - NexusFi: the day session touched the ON high or low 96% of the time; NQ ONH broken 66%, ONL 59%, both 29% (*snippet*).
- **Reading.**
  - Asia and London ranges: geometry ±3 pp.
  - NY AM range: afternoons break **one** side more than random (+3 to +10 pp single, −1 to −6 pp both).
  - RTH breaks at least one ON extreme more than random (none 3.6-4.0% vs 7.4-8.2% on ES/NQ). These are small effects, for a learned table.

### 2.4 After the first break [this study, `afterbreak.py`]

Opposite side taken by the day end, real / null, with the difference in pp:

| Range | ES | NQ | YM | RTY | CL | EURUSD | BTC |
|---|---|---|---|---|---|---|---|
| PDH/PDL | 14.8 / 14.9 (−0.1) | 15.3 / 14.0 (+1.3) | 11.1 / 12.7 (−1.6) | 11.5 / 14.8 (−3.3) | 8.6 / 14.0 (−5.4) | 11.2 / 13.2 (−2.0) | 13.3 / 15.4 (−2.0) |
| Asia 20-00 | 69.6 / 64.9 (**+4.7**) | 69.2 / 65.6 (+3.6) | 73.4 / 69.9 (+3.5) | 74.1 / 67.9 (+6.2) | 59.5 / 60.7 (−1.2) | 63.2 / 62.6 (+0.5) | 47.0 / 48.3 (−1.3) |
| London 02-05 | +1.2 | +0.8 | +0.6 | +4.4 | +3.5 | −6.5 | −0.6 |
| NY AM 10-12 | 14.3 / 20.0 (**−5.7**) | −0.5 | −2.7 | −2.1 | −2.6 | −4.5 | −3.3 |
| ON 18-09 | −1.8 | −0.1 | −0.6 | +4.3 | +0.4 | −0.9 | n/a |

- **Broken side extends +0.25 ADR** (real vs null): mixed, within ±5 pp. There is no robust "break continues further than random" effect. The effect is on the **opposite** side.
- **Failed breaks.** The day closes back inside the prior-day range after a PD break 39-50% of the time. After an Asia break, 13-21%.
- **Timing (BTC, PD).** The later the first break, the smaller the opposite-side chance: break in Asia 16.3%, London 13.3%, NY AM 8.7%, NY PM 4.4%. Each is 0.3-3.3 pp under the null (17.9 / 16.6 / 11.6 / 4.7).
- **Weekly (PWH/PWL).** Opposite side after the first PW break:

  | Market | real | null (both / any) |
  |---|---|---|
  | SPX | 12.0% | 14.8% |
  | NASDAQ | 13.0% | 14.6% |
  | EURUSD | 9.8% | 12.6% |
  | BTC | 10.4% | 16.9% |

- **External:**
  - The ICT "Judas swing" claim (the first break reverses to the other side) is supported only for the index-futures Asia range here.
  - fxbacktest: FX first Asian-break fade 49.4% (n = 9,598), a coin flip; crypto continues 55-58% (ict_time E7).
  - Sweeps → continuation in G10 FX: 65 of 66 folds (Mahadzva SSRN, ict_liq E7).
- **Reading.** A practical rule with modest support: **once one side of a day / week / NY-AM range is taken, discount the other side about 10-25% relative to geometry.** That is −2 to −6 pp on base rates of 10-20%. The exception: two-sided Asia raids on index futures. Learn it per chart (SESS-2/3).

### 2.5 Time-of-day hazard of an untaken PDH/PDL [this study, `pooled.py`]

P(taken by day end | d/ADR now, session when the forecast is made), pooled ES/NQ/YM/RTY, real / day null (n):

| d/ADR | Asia | London | NY AM | NY PM |
|---|---|---|---|---|
| 0-0.1 | 0.92 / 0.92 (544) | 0.87 / 0.89 (269) | 0.92 / 0.88 (110) | 0.67 / 0.70 (61) |
| 0.1-0.2 | 0.76 / 0.79 (1201) | 0.74 / 0.77 (722) | 0.67 / 0.71 (291) | 0.37 / 0.41 (224) |
| 0.2-0.35 | 0.64 / 0.61 (2086) | 0.57 / 0.58 (1356) | 0.47 / 0.52 (654) | 0.19 / 0.21 (484) |
| 0.35-0.5 | 0.40 / 0.44 (1915) | 0.39 / 0.41 (1524) | 0.33 / 0.34 (768) | 0.06 / 0.08 (546) |
| 0.5-0.75 | 0.29 / 0.28 (2357) | 0.27 / 0.25 (1935) | 0.17 / 0.18 (1102) | 0.03 / 0.03 (998) |
| 0.75-1.0 | 0.17 / 0.15 (1597) | 0.15 / 0.13 (1363) | 0.08 / 0.08 (855) | 0.01 / 0.01 (937) |
| 1.0-1.5 | 0.14 / 0.06 (1397) | 0.12 / 0.06 (1232) | 0.05 / 0.03 (873) | 0.00 / 0.00 (1239) |
| ≥ 1.5 | 0.04 / 0.02 (515) | 0.03 / 0.01 (566) | 0.02 / 0.01 (482) | 0.00 / 0.00 (752) |

BTC (UTC day, n = 94,208) has the same shape. Real is **below** the null by 2-9 pp in the 0.1-0.75 band, e.g. 0.2-0.35 ADR: Asia 0.49 / 0.53, NY AM 0.36 / 0.45, NY PM 0.19 / 0.28. That is the "quiet day stays quiet" state the ADR-scaled null cannot see.

- **Brier, time-aware day-bootstrap vs in-sample distance-only table:**

  | Market | time-aware | distance-only |
  |---|---|---|
  | IDX | 0.1511 | 0.1552 |
  | CL | 0.1349 | 0.1433 |
  | EURUSD | 0.1349 | 0.1428 |
  | BTC | 0.1398 | 0.1339 |

  BTC is the exception, explained in §2.6.
- **External:**
  - tradingstats via ict_time E11: 33.5% of ON first breaks happen in the first 5 RTH minutes, 68.7% by 10:00, 90% by 11:30.
  - Midnight-open retrace: ~80% by 11:00 (E10).
  - Same message: most of a day's level-taking happens early, and an untaken level's chance decays fast after the NY AM.

### 2.6 Causal model comparison: forecasting "taken by day end" [this study, `hazmodels.py`]

All models are driftless reflection, p = 2Φ(−d/√V), using only past data.

| Model | Variance V for the rest of the day |
|---|---|
| M_flat (engine-like) | σ² of the last 50 hourly close changes × bars left |
| M_clock | ADR² × Σ_remaining slots v_slot (v = Garman-Klass variance per hourly slot in ADR² units, mean of the last 250 days) |
| M_today | M_clock × f, f = clamp(range so far / E[range so far at this slot], 0.5, 2.5) |
| M_today_s | M_clock × (1 + w(f − 1)), w = E[fraction of the day's range printed by now] |

Brier (raw / after 2-fold time-split Platt recalibration):

| Group (n) | base rate | M_flat | M_clock | M_today | M_today_s |
|---|---|---|---|---|---|
| IDX pooled (26,137) | 0.2095 | 0.1539 / 0.1508 | 0.1473 / 0.1477 | **0.1437 / 0.1436** | 0.1444 / 0.1448 |
| CL (4,295) | 0.1886 | 0.1354 / 0.1373 | 0.1334 / 0.1380 | 0.1324 / **0.1346** | **0.1315** / 0.1349 |
| EURUSD (4,865) | 0.1958 | 0.1350 / 0.1342 | **0.1297 / 0.1308** | 0.1340 / 0.1344 | 0.1305 / 0.1315 |
| BTC (92,949) | 0.1708 | **0.1294** / 0.1284 | 0.1454 / 0.1274 | 0.1334 / 0.1264 | 0.1381 / **0.1261** |

Calibration slopes:
- M_flat 0.64-0.75: over-confident at the extremes.
- M_clock 0.75-0.89.
- M_today 0.81-0.90.

By today's range ratio (IDX; y / M_clock / M_today_s):

| Ratio | y | M_clock | M_today_s |
|---|---|---|---|
| < 0.6 | 0.367 | 0.428 | 0.394 |
| 0.85-1.15 | 0.256 | 0.248 | 0.247 |
| > 1.5 | 0.282 | 0.162 | 0.201 |

- The factor goes the right way but is still too weak at the top. The final multiplier should be learned (SESS-2 does that).
- BTC: M_clock over-predicts badly before calibration (mean p 0.33 vs y 0.22). ADR-mean variance is inflated by fat-tailed days. After calibration, the clock and today models win.
- **Lesson:** keep the variance *level* adaptive (QPOT-02 Lf/Ls) and calibrate online (QPOT-04). The *shape* (clock, today factor) adds −2% to −5% Brier on top.

### 2.7 ADR, range used, exhaustion [this study, §E/F, `pooled.py`]

Day range / ADR14:

| Market | q10 | q25 | q50 | q75 | q90 | P(≥ 1) | P(≥ 1.5) | P(≥ 2) | lag-1 corr |
|---|---|---|---|---|---|---|---|---|---|
| ES | 0.48 | 0.67 | 0.91 | 1.21 | 1.61 | 0.388 | 0.136 | 0.036 | 0.27 |
| NQ | 0.51 | 0.69 | 0.92 | 1.21 | 1.57 | 0.420 | 0.128 | 0.024 | 0.27 |
| YM | 0.55 | 0.71 | 0.90 | 1.19 | 1.55 | 0.376 | 0.120 | 0.024 | 0.20 |
| RTY | 0.53 | 0.69 | 0.91 | 1.21 | 1.58 | 0.412 | 0.124 | 0.040 | 0.19 |
| CL | 0.55 | 0.73 | 0.95 | 1.21 | 1.64 | 0.421 | 0.140 | 0.051 | 0.41 |
| EURUSD | 0.60 | 0.73 | 0.97 | 1.21 | 1.51 | 0.458 | 0.104 | 0.036 | 0.00 |
| BTC | 0.46 | 0.62 | 0.87 | 1.25 | 1.78 | 0.396 | 0.158 | 0.073 | 0.27 |

Max excursion from the day open, larger side, q50 / q80 / q95:
- ES 0.68 / 1.07 / 1.58.
- BTC 0.66 / 1.12 / 1.97.
- EURUSD 0.76 / 1.05 / 1.57.

Smaller side: q50 0.17-0.20, q80 0.32-0.36, q95 0.49-0.53 ADR, in all markets.

**Exhaustion test.** P(extend beyond the running extreme by x·ADR before the day ends), by range used u, real / null (pp):

| Group | x | u < 0.4 | 0.4-0.7 | 0.7-1.0 | 1.0-1.3 | ≥ 1.3 | logistic coef of log u |
|---|---|---|---|---|---|---|---|
| IDX | 0.10 | 63.5 / 65.9 (−2.5) | 44.2 / 41.8 (+2.5) | 29.5 / 25.9 (+3.5) | 26.3 / 20.4 (+5.9) | 19.7 / 14.9 (+4.8) | **+0.215 (se 0.013)** |
| IDX | 0.25 | 43.8 / 46.9 (−3.1) | 29.5 / 27.5 | 17.6 / 15.5 | 17.3 / 12.1 (+5.2) | 9.9 / 8.1 | |
| BTC | 0.25 | 31.9 / 37.8 (−5.9) | 22.3 / 22.7 | 15.9 / 14.2 | 16.0 / 10.8 (+5.1) | 15.7 / 6.6 (**+9.1**) | **+0.230 (se 0.008)** |
| CL | 0.25 | 42.4 / 47.2 (−4.8) | 29.3 / 27.2 | 12.6 / 15.2 | 10.7 / 11.7 | 11.4 / 6.8 (+4.6) | +0.102 (se 0.031) |
| EURUSD | 0.25 | 47.8 / 48.2 | 26.3 / 25.4 | 11.7 / 13.5 | 8.9 / 8.7 | 9.6 / 5.9 (+3.7) | −0.029 (se 0.032) |

Under the slot null the coefficient is +0.15 (IDX), +0.15 (BTC), +0.05 (CL), −0.13 (EURUSD).

- **Weekly version** (`weekly.py` W4). After Wednesday's close (Thursday for BTC), extension of 0.25 AWR before the week ends:

  | Market | u < 0.5 | u ≥ 1.1 |
  |---|---|---|
  | SPX | 20.5 / 27.5 | **23.9 / 15.0** |
  | NASDAQ | 20.2 / 27.8 | 26.8 / 15.2 |
  | EURUSD | 26.2 / 27.6 | 19.1 / 16.6 |
  | BTC | 11.7 / 23.2 | 15.8 / 9.2 |

- **External:**
  - DailyForex 2016 (FX majors, 15 years): a day range of 2× ATR20 occurs about 1 day in 40 (1 in 25 for USDJPY); 3× at most 1 in 125 (*snippet*). This matches P(≥ 2 ADR) of 2-7% here.
  - A forum claim that price "stays within ADR ~60% of the time" (20 years, *snippet*, unsourced) matches P(< 1 ADR) of 54-62% here.
  - Engle & Sokalska (2012, J. Financial Econometrics 10(1):54-83): intraday variance = daily × diurnal × stochastic intraday components, on 10-minute returns of > 2,500 US stocks. That is the structure of M_today.
- **Reading.**
  - The "ADR exhaustion" folklore has the sign backwards on 3 of 4 markets, and is neutral on EURUSD 2017-18, a period with zero day-to-day range autocorrelation.
  - A day that is quiet so far stays quiet; a busy day keeps going. **ADR should be a unit and a prior for the level, never a cap.**

### 2.8 Weekly statistics [this study, `weekly.py`]

**W1: weekday of the weekly high / low** (real / day-order shuffle null)

| Market | HIGH Mon | Tue | Wed | Thu | Fri | LOW Mon | Tue | Wed | Thu | Fri |
|---|---|---|---|---|---|---|---|---|---|---|
| SPX 99-18 | 23.3 / 26.8 | 14.7 / 13.6 | 14.8 / 13.1 | 14.8 / 15.1 | 32.3 / 31.4 | 29.0 / 32.8 | 15.4 / 15.0 | 14.7 / 13.1 | 17.1 / 14.0 | 23.8 / 25.2 |
| NASDAQ | 23.5 / 25.9 | 14.3 / 13.6 | 12.8 / 12.9 | 15.3 / 14.4 | 34.1 / 33.1 | 28.8 / 31.2 | 16.0 / 15.1 | 13.4 / 13.1 | 16.6 / 14.1 | 25.2 / 26.4 |
| EURUSD 02-26 | 27.0 / 29.1 | 13.3 / 13.7 | 13.8 / 12.9 | 18.2 / 14.8 | 27.7 / 29.5 | 29.8 / 31.5 | 13.2 / 13.9 | 12.4 / 12.7 | 14.6 / 14.0 | 30.0 / 27.9 |

- BTC (7-day UTC week): Mon high 26.9 / 21.2, low 35.1 / 29.0; Sat low 5.7 / 11.1; Sun high 17.7 / 26.0. Weekend days are quiet (Sat/Sun range 0.30-0.33 AWR vs 0.41-0.44 on weekdays), so extremes cluster on Monday.
- Arcsine baseline (ict_time E15): Mon 29.5, Tue 14.1, Wed 12.8, Thu 14.1, Fri 29.5.
- "At least one weekly extreme printed on Mon or Tue": 78.8-79.3% in every market.
- **"Weekly low by Tuesday in up weeks"** (the ICT Tuesday-low claim): 71.9% (SPX), 73.5% (NASDAQ), 75.2% (EURUSD), against shuffle null 76.0%, 76.9%, 76.5%. Not above chance. BTC: 74.2% vs 66.8%; the 7-day week puts the quiet weekend at the end.
- **Weekday range factor** (mean daily range / AWR): Mon 0.38-0.40 vs Thu 0.41-0.46 (equities, FX). Monday is 5-15% quieter. This is a variance factor (TIME-1 `c[d]`), not a direction.

**W2/W3: PWH / PWL during the week** (real / week-bootstrap null)

| Market | P(PWH) | P(PWL) | both | none |
|---|---|---|---|---|
| SPX | 58.2 / 55.5 | 44.7 / 45.3 | 11.4 / 13.0 | **8.5 / 12.2** |
| NASDAQ | 58.1 / 55.7 | 46.3 / 45.6 | 12.1 / 12.9 | 7.8 / 11.6 |
| EURUSD | 49.6 / 52.0 | 48.6 / 48.5 | 9.5 / 11.2 | 11.3 / 10.8 |
| BTC | 53.5 / 54.1 | 38.0 / 40.3 | **8.6 / 13.6** | 17.0 / 19.3 |

- Cumulative P(PWH taken by the end of each weekday), SPX: Mon 30.0 / 31.9, Tue 41.9 / 41.7, Wed 49.3 / 47.8, Thu 54.5 / 52.2, Fri 58.2 / 55.5. This is geometry.
- **W5: Monday range taken later in the week.** High 73-77%, low 65-71%, both 40-48%. Within ±5 pp of the null, mixed sign (SPX both +4.9, EURUSD −2.5, BTC −3.6).
- **External:**
  - Aldous (Berkeley, via ict_time E15): the time of the S&P maximum in 746 twenty-day blocks matches a random walk.
  - A forum tally of 51 EURUSD weeks found Tuesday the least likely day for a weekly extreme (*snippet*, energyexch). That is consistent with arcsine.
  - No published multi-year source for "Tuesday/Wednesday forms the weekly extreme" was found. Sources are practitioner claims (*snippets*).

### 2.9 Gaps [this study, `gaps.py`]

Fill vs mirror; difference in pp:

| Dataset | n | window | fill | mirror | diff | by size |
|---|---|---|---|---|---|---|
| Index futures RTH gap, ES/NQ/YM/RTY 2026 | 204 | same RTH | 0.593 | 0.525 | **+6.9** | 0.5-1 ADR +12.8; > 1 ADR +21 (n = 19) |
| EURUSD weekend 2002-26 | 641 (48% of weeks have zero gap) | Monday | 0.732 | 0.730 | +0.2 | 0.25-0.5 ADR +17.5 (n = 80); < 0.1 ADR −5.6 |
| EURUSD weekend | 641 | 5 days | 0.874 | 0.875 | −0.2 | |
| BTC "CME gap" 2017-24 | 415 (median gap 0.28 ADR) | 24 h | 0.557 | 0.614 | −5.8 | > 1 ADR: 8.7 vs 30.4 |
| BTC "CME gap" | 415 | to Friday (~5 d) | 0.766 | 0.788 | −2.2 | > 1 ADR: 21.7 vs 63.0 |
| BTC "CME gap" | 415 | 4 weeks | **0.867** | **0.894** | −2.7 | > 1 ADR: 43.5 vs 78.3 |

- **The S&P 500 cash daily gap test is invalid.** The fill came out −27 pp vs the mirror. The cash index's "open" prints before most components trade, so it understates the gap and inflates continuation. The test is reported in `out_gaps.txt` only as a warning.
- **External:**
  - BTC CME gaps: ~95% eventually filled; > 50% fill on the session-open day; 30% of the rest later that week (NewsBTC, Dec 2019 analysis, *snippet*).
  - Median time to fill 36 h (2024) → 19 h (2025) (CryptoSlate, *snippet*).
  - Cointelegraph "> 98%" (*snippet*, no dataset).
  - None of these compares against a distance-matched level. Here the 4-week fill rate (86.7%) is what any level at that distance gets (89.4%).
- **Academic:** Plastun, Sibande, Gupta & Wohar (2020), North American Journal of Economics and Finance, "Price gap anomaly in the US stock market: the whole story" (DJI, S&P 500, NASDAQ, 1928-2018). Prices tend to move in the gap's direction (temporary momentum), and the results are "contrary to the myth that price gaps tend to get filled".
- **Practitioner:** ES gap-fill probability 92% for small gaps → 18% for gaps > 30 points (NexusFi chart caption, *snippet*). Size dependence = distance.
- ict_pd §2.3 (via sibling): SPY opening gaps > 1% fill same-day 26-33% vs 78-80% for 0.1-0.25%. That is a base rate; the magnet question was untested there and is answered here: no magnet beyond distance, except possibly a small opening-reversal effect in index futures.

### 2.10 ORB / IB / NR7 / inside day (from siblings and external sources)

| # | Claim | Source | Numbers | Grade |
|---|---|---|---|---|
| O1 | London opening-range breakout follow-through | fxbacktest via ict_time E8, 26 instruments, 92,947 breaks | breaks 99.8% of days; follow-through 1 range 50.3% (47.6-52.5%) | moderate-strong (null: coin flip) |
| O2 | ORB on MNQ, walk-forward | arXiv 2605.04004 via bias_dol X9 | ORB long T = 0.88; 0 of 14 OHLCV signal families pass | moderate (negative) |
| O3 | IB breaks | tradingstats via amt_profile X5, ES/NQ 2015-25 | ≥ 1 IB break 97.8% / 96.2%; median extension 63.6% / 55.6% of IB; ES reaches +100% of IB 18.8%; first break fails 34% | moderate (descriptive) |
| O4 | IB vs a clock random walk | ict_time §2.2 (YM edgeful) | double break 20% real vs 36.8% random; respected more than random | weak (n ≈ 125) |
| O5 | IB extremes as targets | amt_profile §0 | hit at the random-level rate once the clock baseline is matched | moderate |
| O6 | NR7 / inside → expansion | bias_dol §2.8 | next range > 20-bar median: NR7 0.26-0.45 vs base 0.48-0.50 (contraction persists); both prior extremes taken 0.16-0.29 vs base 0.08-0.14 (geometry) | moderate |
| O7 | Crabel ORB / stretch / NR tables | Crabel 1990 (book) | tabulated statistics exist in the book; no numbers retrievable (*snippets*) | none retrieved |
| O8 | Intraday momentum | Gao, Han, Li & Zhou 2018 JFE | first half-hour → last half-hour R² 1.6% (SPY); absent in FX and commodities | strong (small effect) |

**Reading.**
- The ORB direction is a coin flip; IB breaks are near-certain (geometry); contraction does not predict expansion.
- The only robust use of the opening range is as a **unit**: the Crabel stretch ≈ the counter-move from the open, median 0.17-0.20 ADR.

---

## 3. Engine gap analysis (baseline_v2.pine)

| ID | Concept | Status | Lines | What the engine does / what differs |
|---|---|---|---|---|
| S1 | PDH/PDL as targets | **present** | 104, 807-832 (`f_rangeTrack`), 945, 952-958, 1790-1794 | Exchange-day extremes (`timeframe.change("D")`), anchored to the print bar, pushed to the registry with tier 0.80 (`f_tierW` 506-515) and a √(86400/chartS) freshness clock (1792). Correct source. Their *probability* uses the generic fixed-H PoT (1303-1311) with no day-end horizon and no ADR unit |
| S2 | PWH/PWL | **present** | 105, 946, 959-961, 1795-1799 | Tier 0.92. Same probability caveat: a week-end horizon is missing |
| S3 | Asia / London / NY AM session ranges | **present / partial** | 106-109, 835-863 (`f_sessTrack`), 948-950, 1800-1809 | Pushed at session end, tiers 0.55 / 0.60 / 0.60. Only on ≤ 1H charts (`intraOK`, 947). The NY AM window is misaligned on 1H (ict_time G3). No ON (18:00-09:30) or NY PM range (TIME-3 covers both) |
| S4 | Session in which levels get taken / HOD-LOD session | **wrong** (fixed prior) | 596-602 (`f_kzAff`), 1941 | London ×1.20 for Asia pools, NY AM ×1.20 for London and ×1.15 for PD, NY PM ×1.15 for NY AM. My data: first-take session and HOD/LOD session equal the clock/geometry null within ±2.5 pp, and session-range raids within ±3 pp (§2.2-2.3). These multipliers add selection bias with no measured edge, and inflate the ledger's EDGE by timing (ict_time G16) |
| S5 | Source tier as a hit-probability prior | **partial / unsupported** | 506-515, 682 (`1.2 * this.tier()` in density), 1582 (`liqEvt` weight) | PD/PW/session pools get large density boosts (PW 0.92, PD 0.80 vs chart 0.25). Their take rates equal distance-matched random paths (§2.1, §2.8). A tier may stand for "importance", but should not raise the *probability*. A per-family ledger is needed (S13) |
| S6 | ADR / day range | **missing** | none (`maxATR` 129, eject 131 are ATR-based) | No ADR anywhere. ATR on the chart timeframe is the only unit. Distances in ADR are what traders read and what transfers across timeframes |
| S7 | ADR exhaustion / "ADR remaining" cap | **missing (correctly)** | none | Must stay missing: refuted (§2.7) |
| S8 | Day-state variance (range so far vs normal by now) | **missing** | 914-917 (`potSig`, `potMu`), 665, 1303-1322, 1360-1363 | Trailing σ of 50 close changes, time-blind and day-blind. The day-state factor cuts IDX Brier −2.8% beyond the clock (§2.6) |
| S9 | Horizon to session / day end | **missing** | 305 (`H = potH`), 1303-1311, 1453-1455 (`t.bars >= H`) | Fixed H bars. On 1H, H = 30 crosses into the next day; on 5m it is 2.5 h. "PoT today" for PDH at 14:00 ET cannot be expressed (§2.5). TIME-4, QPOT-05 and OF-6 propose the analytic version; SESS-2 adds the learned surface |
| S10 | Opposite side after a range break | **missing** | 1575-1585 (`liqEvt` → D only) | Raid outcomes feed D globally. Nothing marks the sibling level of a broken range. Measured −2 to −6 pp (PD, PW, NY AM) and +4 pp (Asia on indices) (§2.4) |
| S11 | Weekday of weekly extremes, weekly profiles | **missing (correctly)** | none | Arcsine-explained (§2.8). Only a weekday variance factor is real (TIME-1 `c[d]`) |
| S12 | Opening / weekend gaps | **missing** | none (ICTPD-6 proposes) | Evidence: no magnet beyond distance for weekend gaps (FX, BTC CME gap); a possible small RTH fill excess on index futures (+6.9 pp, n = 204). If ICTPD-6 lands, use no gap prior and let the ledger grade it |
| S13 | Ledger granularity for key levels | **partial** | 635-637 (`grp`), 1376-1384 (`f_calMult`), 1426-1460 | All external liquidity (STF, HTF, Asia, London, NY, PD, PW) is one group (grp 1), so per-family edge cannot be measured or learned. Calibration is bounded 0.8-1.2 per group |
| S14 | Empirical PoT surface conditioning | **partial** | 1059-1062, 1284-1300, 1527-1532 | ATR-normalised H-bar excursions split by HTF bias, pooled over hours and day state. The time-aware null beats distance-only by 2.6-5.9% Brier on IDX/CL/EURUSD (§2.5). REG-1/QPOT-03 add a vol state; SESS-1 adds day state |
| S15 | Day boundary | **present (exchange day)** | 945 | `timeframe.change("D")`: CME 18:00 ET, FX 17:00 ET, crypto 00:00 UTC. Consistent per symbol. No choice of "NY midnight" day, which some ICT users apply to crypto (SESS-6) |
| S16 | ORB / IB as sources | **missing** | none | Not recommended as sources (O1-O5): the NY AM range already covers the morning range. The IB is in AMT-2's candidate ledger |
| S17 | NR7 / inside-day expansion prior | **missing (correctly)** | none | Contraction persists (O6) |
| S18 | Weekly horizon / week state for PW levels | **missing** | 946, 1795-1799 | PW levels are scored on the same H-bar PoT as everything else (SESS-5) |

---

## 4. Proposals (best first; maximum 10)

Ground rules:
- Every proposal is ledger-measurable and neutral by default where the evidence is small.
- Each builds on, and does not duplicate:
  - TIME-1 / QPOT-02: the volatility clock and V_H;
  - TIME-4 / QPOT-05 / OF-6: analytic session-end PoT and ETA;
  - QPOT-04 / SMC-1: PoT grading and recalibration;
  - TIME-5: learned killzone affinity;
  - ICTPD-6: gaps.

### SESS-1 (P1, effort M) · Day-state variance ("today factor") and ADR as a unit; never an ADR cap

**Why.**
- A day that has already moved more than normal for this hour keeps moving: the ADR-null excess reaches +4 to +10 pp at u ≥ 1 ADR. A quiet day stays quiet: −2 to −6 pp at u < 0.4.
- Logistic log(u) coefficients: +0.22 (IDX), +0.23 (BTC), +0.10 (CL).
- Causal Brier:
  - IDX: M_clock 0.1477 → M_today 0.1436 (−2.8%), −4.8% vs the engine-like flat σ;
  - CL: −2.0% vs flat;
  - BTC: M_today_s 0.1261 vs M_flat 0.1284 (−1.8%).
- Structure: Engle & Sokalska (2012), variance = daily × diurnal × intraday.
- The engine's σ (line 916) cannot know that today is a 1.8× day until 50 bars later.

**Algorithm.**
1. **ADR from the engine's own day tracker** (no new `request.*`). On `pdNew` (945), push `pdH − pdL` into `dRng` (keep `adrLen` = 14). `ADR = dRng.avg()` once there are ≥ 5 days.
2. **Running day extremes** `dHi`/`dLo`, reset on `timeframe.change("D")`. Day bucket `db = int((time − dStart) / (bkMin·60000))` with `bkMin = max(30, chartMin)`, `NBD = ceil(1440/bkMin) + 1`.
3. **Expected range so far by bucket**, `expR[db]`: an EWMA over days (α = 0.05, ≈ 20-day memory) of (range so far at the end of bucket db)/ADR. Also `expEnd`, the EWMA of the final range/ADR.
4. **Today factor:**
   - `ratio = (dHi − dLo)/ADR / expR[db]`
   - `f = clamp(ratio, 0.5, 2.5)`
   - `w = clamp(expR[db]/expEnd, 0, 1)` (share of a normal day already printed)
   - `fDay = 1 + w·(f − 1)`
   - Beyond the day end, carry `fNext = 1 + ρ·(fDay − 1)`, with ρ = 0.25 (measured lag-1 range autocorrelation 0.19-0.41; 0 for EURUSD 2017-18). It could be learned online as the EWMA correlation of consecutive days' ratios.
5. **Apply.**
   - Without QPOT-02: `σ_eff = potSig · √fDay` in `f_potModel` (1304), `f_potBase` (1315), `evaluate` reach (665, the `sig` argument) and `f_invalidation` (1360).
   - Empirical surface: look up at `dAtr / √fDay`.
   - With QPOT-02: multiply V(j) by fDay for the bars before the day end and by fNext after.
6. **Never cap, eject or penalise a level because "ADR is used up".** Document this in the tooltip.

**Pine v6 sketch.**
```
// INPUTS (G_POT)
bool useDay = input.bool(true, "Day-State Volatility", group = G_POT,
  tooltip = "PoT, reach and race scale with how active today has been versus a normal day at this hour. Busy days keep extending and quiet days stay quiet. A used-up ADR does not cap targets.")
int  adrLen = input.int(14, "ADR Length (days)", minval = 5, maxval = 30, group = G_POT)
// derived (after 308)
int  bkMin = math.max(30, int(chartS / 60))
int  NBD   = int(math.ceil(1440.0 / bkMin)) + 1
// STATE (after 1080)
var array<float> dRng  = array.new<float>()
var array<float> expR  = array.new<float>(NBD, na)
var array<float> dPath = array.new<float>(NBD, na)
var float dHi = na, var float dLo = na, var int dStart = na, var float dADR = na, var float expEnd = na
// SERIES (after 950; intraday only)
if timeframe.isintraday
    if pdNew                                   // finished day: learn its path, then reset
        if not na(dADR)
            for k = 0 to NBD - 1
                float v = dPath.get(k)
                if not na(v)
                    expR.set(k, na(expR.get(k)) ? v : expR.get(k) + 0.05 * (v - expR.get(k)))
                dPath.set(k, na)
            float fin = (pdH - pdL) / dADR
            expEnd := na(expEnd) ? fin : expEnd + 0.05 * (fin - expEnd)
        dRng.push(pdH - pdL)
        if dRng.size() > adrLen
            dRng.shift()
        dADR := dRng.size() >= 5 ? dRng.avg() : na
    if timeframe.change("D")
        dHi := high, dLo := low, dStart := time
    else
        dHi := math.max(nz(dHi, high), high), dLo := math.min(nz(dLo, low), low)
int   db    = na(dStart) ? 0 : math.min(NBD - 1, int((time - dStart) / (bkMin * 60000)))
if not na(dADR)
    dPath.set(db, (dHi - dLo) / dADR)
float eNow  = expR.get(db)
float rat   = na(eNow) or na(dADR) or eNow <= 0 ? na : (dHi - dLo) / dADR / eNow
float wDay  = na(expEnd) or na(eNow) ? 0.0 : f_clamp(eNow / expEnd, 0.0, 1.0)
float fDay  = useDay and not na(rat) ? 1.0 + wDay * (f_clamp(rat, 0.5, 2.5) - 1.0) : 1.0
float sigD  = nz(potSig) * math.sqrt(fDay)         // pass sigD wherever potSig feeds a probability
```
Notes on the sketch:
- `var` state rolls back on realtime ticks, so the live readout stays consistent.
- History needs no `barstate.isconfirmed` because every historical bar is confirmed.
- Per bar the cost is O(1). A day rollover costs one loop of NBD ≤ 49 iterations.

**Ledger / measurement.**
- At `f_openTrial` (1426-1431), store `pA0` (fDay = 1) and `pA1` (with fDay). At booking, accumulate the Brier of each.
- Panel row: `DAY-STATE Brier −3.1% (n 214)`.
- Optionally auto-disable when the running Brier gain is negative after 100 trials.

**Expected value.** PoT, reach and race stop over-promising on dead days and under-promising on trend days, which are the days users trade. Targets beyond 1 ADR stay alive on expansion days instead of being written off.

**Evidence:** moderate (own reproducible tests on 4 market groups; strong structural literature).

**Risk.**
- News spikes inflate the ratio. The clamp at 2.5 and the w-shrink early in the day handle that.
- Crypto weekends: buckets are per-day, so this is fine.
- No effect on daily or higher charts (intraday only).

### SESS-2 (P1, effort M) · Learned key-level day-end hazard surface ("PoT today") with a Brier grade

**Why.**
- For an untaken PDH/PDL at 0.2-0.35 ADR, P(today) is 64% → 57% → 47% → 19% from Asia to NY PM (§2.5). The fixed-H PoT cannot express that.
- The analytic level is mis-calibrated by market (BTC −4 to −9 pp vs an ADR-scaled model), so the probability must be **learned on the chart**.
- This is the empirical, self-grading counterpart of TIME-4/QPOT-05's analytic "PoT by session end". It also learns the after-break effect (§2.4) for free, through the `sib` dimension.

**Algorithm.**
- **Tracked key levels** (fixed list, ≤ 10): aPDH, aPDL, aPWH, aPWL, and today's finished Asia / London / NY AM H and L (`asH/asL`, `lnH/lnL`, `nyH/nyL` captured at session end), plus ONH/ONL if TIME-3 lands.
  - Family `fam`: 0 = PD, 1 = PW, 2 = session.
  - Sibling = the opposite side of the same range.
- **Per level and day:** `tk` (bar index of the first through-trade today, −1 if none). Update on confirmed bars with the strict liquidity test.
- **Snapshots.** At each new day bucket `db` (from SESS-1), on a confirmed bar, for each level that is untaken today (`tk < 0`) and has `d = distance / ADR ≤ 3`, push a snapshot `(fam, tb, dBin, sib, pModel, lvlIdx)`:
  - `tb = min(7, int(8 · elapsedFraction))`, where `elapsedFraction = (time − dStart)/(time_close("D") − dStart)` (`time_close(timeframe)`, reference/time.md l.378);
  - `dBin` over edges [0, .1, .2, .35, .5, .75, 1, 1.5, 2, 3];
  - `sib = sibling.tk >= 0`.
  - At most 10 levels × 49 buckets ≈ 490 per day.
- **Resolution on `pdNew`:** `y = tk[lvl] >= 0` (the level was untaken at the snapshot, so any take came later). Update `N[cell] += 1`, `K[cell] += y` with `cell = ((fam·8 + tb)·9 + dBin)·2 + sib` (432 cells). Accumulate `Σ(pModel − y)²` and `Σ(pSurf − y)²`, where pSurf is the surface estimate stored at snapshot time.
- **Estimate.**
  - `pSurf = (K + m·pA)/(N + m)`, with m = 20.
  - pA is the analytic day-end prior: TIME-4/QPOT-05 if present, else `f_pot(d·ADR, sigD, 0, barsLeftToday)` with `barsLeftToday = max(1, int((time_close("D") − time_close)/(chartS·1000)))`.
  - Interpolate linearly between dBin centres.
  - Pool `fam` when `N < 30`.
- **Use.**
  - (a) For key-level targets the Clean label tooltip and the Terminal HUD show `Today 38%` beside the H-bar PoT.
  - (b) Optional "PoT Horizon = Day End" makes it the headline PoT for key levels.
  - (c) SESS-3 multiplier.
- **Gate.** The update runs on every bar, outside the `calcBars` window, because it is cheap. That way 5-minute charts accumulate enough days.

**Pine v6 sketch (state).**
```
var array<int>   hzN  = array.new<int>(432, 0)
var array<int>   hzK  = array.new<int>(432, 0)
var array<int>   snC  = array.new<int>()      // packed cell index
var array<int>   snL  = array.new<int>()      // level slot 0..9
var array<float> snPm = array.new<float>()    // analytic p at snapshot
var array<float> snPs = array.new<float>()    // surface p at snapshot
var array<int>   lvTk = array.new<int>(10, -1)
var array<float> hzBr = array.from(0.0, 0.0, 0.0)   // [n, Σ(pm−y)², Σ(ps−y)²]
```
- Helpers go in STATE HELPERS (after 1340): `f_hzCell(fam, tb, dA, sib)`, `f_hzP(fam, tb, dA, sib, pA)`.
- The snapshot loop runs in a new block after the key-liquidity trackers (after 969) under `barstate.isconfirmed and timeframe.isintraday`.

**Ledger / measurement.**
- Panel row `KEY LEVELS day-end Brier: model .154 · learned .144 (n 812)`.
- The surface's own Brier against the analytic is its proof. If it is not better after 300 snapshots, the label falls back to the analytic.

**Expected value.**
- The trader gets the number they actually ask for: will PDH go today, and is it still realistic after lunch.
- A natural stale-target filter: P(today) decays toward the close.
- It learns the per-symbol residuals (Asia two-sided raids on indices, one-sided afternoons) without hard-coding.

**Evidence:** moderate (§2.4-2.6; tradingstats/edgeful timing data in ict_time E10-E11).

**Risk.**
- Thin cells early: the m-prior and fam pooling handle it.
- Holidays and short days distort `time_close("D")`. Use `max(1, …)` and treat partial days as normal.
- Memory and loops are trivial.

**Effort:** M.

### SESS-3 (P2, effort S) · Replace fixed session affinities and the tier "probability bonus" with a bounded, learned key-level multiplier; per-family ledger

**Why.**
- `f_kzAff` (597-602, used at 1941) hard-codes London/NY raid multipliers of ×1.05-1.20. My data shows first-take timing and session raids equal to the clock/geometry null within ±2.5-3 pp (§2.2-2.3), and ict_time reached the same conclusion with a different null.
- Source tiers raise density by up to `1.2 × 0.92` (682). PD/PW/session take rates equal distance-matched nulls (§2.1, §2.8).
- The real residuals are small and market-specific. Examples: Asia opposite side +3.5 to +6.2 pp on indices, NY AM / PD / PW opposite side −2 to −6 pp. They must be learned.

**Algorithm.**
1. Delete the `f_kzAff` multiplier at 1941. Optionally keep the function behind an input `Legacy Session Affinity` (default off).
2. For key-level pools (src 3-7), compute a multiplier from SESS-2:
   - `mKey = clamp(pSurf(cell) / pA(cell), 0.85, 1.20)`, with the cell aggregated over dBin and `N ≥ 40`; otherwise 1.0.
   - Apply `lv.mult *= mKey`.
   - This carries the after-break discount (sib = 1) and any real session-specific residual.
3. Ledger split: give `Trial` a `fam` field (0 chart, 1 STF/HTF, 2 PD, 3 PW, 4 session, 5 FVG, 6 OB/BRK) and resize the `stN/stK/stPE/...` arrays to 8. Keep `f_calMult` on the old 4 groups for continuity. Show per-family `hits / expected` in the Full view.
4. Keep the tier for *magnitude display* and the density pillar, but cap its contribution until per-family calibration has earned it. Coordinate with OF-3 / WYK-1.

**Pine v6.** These are small edits in the scoring loop (1939-1947) and in `f_book` (1461-1499). No new requests.

**Ledger / measurement.** Per-family EDGE vs `pBase`; A/B Brier of selection with and without `mKey`. This works directly with COMP-3's shadow-selector benchmark.

**Evidence:**
- moderate that the fixed affinities are unsupported (two independent nulls);
- weak for the size of any specific residual.

**Risk.** Removing affinities changes which target is shown during killzones. Users may notice fewer "London raids Asia" picks. That is the honest outcome.

**Effort:** S (after SESS-2). Without SESS-2: just remove `f_kzAff` and add the family split.

### SESS-4 (P2, effort S) · Day / week context readout and key-level alerts

**Why.**
- Traders reason in session terms: "PDH taken? Asia high taken? How much of the ADR is done?".
- The engine computes most of this but shows none of it.
- The alerts list (2077-2094) has no "key level taken" event, a common request in competitor threads (competitors.md: requests for PDH/PDL, session and gap levels).

**Spec.**
- **Terminal panel**, one row each:
  - `DAY  0.72 ADR (norm 0.55 by now) ×1.3 · PDH ✓ · PDL 12% today · ASIA H ✓ L 41%`;
  - `WEEK 0.81 AWR · PWH 22% · PWL 9% this week` (needs SESS-5).
- **Clean label tooltip.** For key-level targets append `Today: 38% (learned, n=812)`. The Clean face stays two lines.
- **Alerts:** `alert()` once per bar close when a tracked key level is first traded through today. The message carries what remains, e.g. `PDH taken · PDL today 9% · next BSL PWH 0.6 ADR`. Use `alert.freq_once_per_bar_close`; it reuses the `tk` updates from SESS-2.
- **Distance in the HUD** also as ADR: `0.42 ADR`.

**Evidence:** weak as a forecasting gain (UX value). The probabilities shown come from SESS-1/2, which are graded.

**Risk.** Panel clutter. Show it in Terminal only, plus the Clean tooltip.

**Effort:** S.

### SESS-5 (P3, effort S-M) · Weekly horizon and week state for PWH/PWL

**Why.**
- PW levels are the highest-tier pools (0.92) but are scored on the same H-bar PoT.
- Weekly statistics mirror the daily ones (§2.8):
  - take rates = geometry;
  - after the first PW break the opposite side is −1.6 to −6.5 pp;
  - week range used ≥ 1.1 AWR → +9 to +12 pp more extension (SPX/NASDAQ);
  - the weekday of the extreme is arcsine.

**Spec.**
- AWR from `pwNew` ranges (946). The week bucket is the weekday (`dayofweek`, reference/time.md l.19), 5 or 7 buckets.
- `expW[weekday]` = EWMA of the week range so far / AWR. Then `fWk` exactly as fDay.
- Surface: weekday × dBin(AWR) × sib, 5·9·2 = 90 cells per family, resolved on `pwNew`.
- Readout: `PWH this week 22%`.

**Evidence:** moderate (weekly tests on 4 markets, 581-1,194 weeks).

**Risk.** Few samples: about 50 weeks per year of chart history. The m-prior dominates for a long time, so show n.

**Effort:** S-M.

### SESS-6 (P3, effort S) · Day-boundary choice and ADR distance units

**Why.**
- PDH/PDL and the SESS-1/2 day use the exchange day (945). Crypto charts use 00:00 UTC, which is 19:00/20:00 ET, while ICT-style users anchor the crypto day at NY midnight or NY 17:00.
- Levels and statistics change with the anchor. This is a consistency and UX issue, not a forecasting edge.

**Spec.**
- `string dayAnchor = input.string("Exchange", "Day Boundary", options = ["Exchange", "NY Midnight", "NY 17:00"], group = G_KEY)`.
- `bool newDay`:
  - "Exchange": `timeframe.change("D")`;
  - "NY Midnight": `dayofmonth(time, tz) != dayofmonth(time[1], tz)`;
  - "NY 17:00": `not na(time(timeframe.period, "1700-1701", tz))` and not on the previous bar.
- Feed `f_rangeTrack(newDay)` and SESS-1.
- Show distances in ADR as well as ATR (SESS-4).

**Evidence:** none for forecasting (definitional).

**Risk.** Changing the anchor changes the levels. Default "Exchange" (current behaviour).

**Effort:** S.

### Explicitly not recommended (the evidence says no)

| Idea | Evidence against |
|---|---|
| ADR-remaining cap, "ADR hit → eject targets", ADR projection levels as targets | §2.7: the sign is reversed; extension rises with range used |
| Fixed session/killzone target affinities; "London makes the HOD/LOD" or "NY takes London" priors | §2.2-2.3: equal to the null within ±3 pp |
| Weekday priors ("Tuesday low of week", "Wednesday reversal", Monday-range rules) | §2.8: arcsine. "Low by Tuesday in up weeks" 72-75% vs null 76-77% |
| "CME gaps (weekend gaps) must fill" as a level prior | §2.9: 4-week fill 86.7% vs mirror 89.4%; large gaps continue |
| NR7 / inside-day expansion and ORB direction priors | §2.10: contraction persists; ORB follow-through ≈ 50% |

---

## 5. Sources

**This study (reproducible)**
- `study/session_tools/`: `sesslib.py`, `daystats.py`, `afterbreak.py`, `pooled.py`, `hazmodels.py`, `weekly.py`, `gaps.py`, `nullcheck.py`.
- Outputs: `out_<SYM>_day.txt`, `out_<SYM>_slot.txt`, `out_afterbreak_<SYM>.txt`, `out_pooled_day.txt`, `out_pooled_slot.txt`, `out_hazmodels.txt`, `out_weekly_<SYM>.txt`, `out_gaps.txt`.
- Data:
  - `study/amt_data/cme/` (public GitHub dataset `axb0306/cme-futures-ohlc`, cloned by the AMT study);
  - `study/bias_data/`;
  - `dl_knn/repo/tests/parity/baselines/` (OANDA EURUSD and Coinbase BTC daily);
  - BTC Bitstamp minute data from the public GitHub dataset `ff137/bitstamp-btcusd-minute-data`, cached as `study/session_data/btc_1h.pkl`.

**Academic**
- Engle, R. F. & Sokalska, M. E. (2012). Forecasting intraday volatility in the US equity market. Multiplicative component GARCH. *Journal of Financial Econometrics* 10(1):54-83. https://ideas.repec.org/a/oup/jfinec/v10yi1p54-83.html (working paper: https://archive.nyu.edu/handle/2451/26361)
- Plastun, A., Sibande, X., Gupta, R. & Wohar, M. (2020). Price gap anomaly in the US stock market: the whole story. *North American Journal of Economics and Finance*. https://ideas.repec.org/p/pre/wpaper/201963.html (repository: https://repository.up.ac.za/handle/2263/78336)
- Andersen, T. & Bollerslev, T. (1997). *J. Empirical Finance* 4:115-158, via ict_time E1.
- Gao, Han, Li & Zhou (2018). *JFE* 129(2):394-414, via ict_time E12.
- Boyarchenko, Larsen & Whelan, NY Fed Staff Report 917, via ict_time E13.
- Lévy arcsine law; Aldous (Berkeley) S&P 20-day blocks, via ict_time E15.
- Crabel, T. (1990). *Day Trading with Short Term Price Patterns and Opening Range Breakout* (book; no numbers retrieved). Article listing: https://store.traders.com/-v07-c04-orb-pdf.html
- arXiv 2605.04004 (MNQ intraday OHLCV signals, walk-forward), via bias_dol X9.

**Vendor / practitioner** (*snippet* = number read from search-result text; the page itself could not be fetched)
- TradeThatSwing, London H/L broken after the US open (single 70.66%, both 25.1%, neither 4.25%). *Snippet.* https://tradethatswing.com/98-of-the-time-existing-london-high-low-prices-are-broken-when-us-opens/
- Linnsoft "homework" (ES prior close touched 1,048/1,803 days; PDH/PDL study over 1,441 days ending 2017-10-16). *Snippet.* https://linnsoft.com/homework
- NexusFi, overnight-session analysis (day session touched the ON high or low 96%; NQ ONH 66%, ONL 59%, both 29%). *Snippet.* https://nexusfi.com/a/data/pre-market-data-overnight-session-analysis
- NexusFi, gap trading (ES fill probability 92% for small gaps → 18% for gaps > 30 pts, chart caption). *Snippet.* https://nexusfi.com/a/strategies/gap-trading-futures
- NewsBTC (Dec 2019 CME gap analysis: ~95% eventually filled, > 50% on the open day). *Snippet.* https://www.newsbtc.com/news/bitcoin-cme-futures-gaps-are-filled-with-95-certainty-but-trading-them-is-risky/
- CryptoSlate (median time to fill 36 h in 2024 → 19 h in 2025; "gaps do not have to fill"). *Snippet.* https://cryptoslate.com/do-cme-gaps-always-have-to-fill-bitcoins-60k-flush-says-no/
- DailyFX (2012), intraday seasonality (first FX hour sets the high ~8%, low ~6%, 2005-2009). *Snippet.* https://www.dailyfx.com/forex/technical/article/special_report/2012/07/21/Improving_Profitability_with_Intraday_Seasonality.html
- DailyForex (2016), volatility profiles of the majors (2× ATR20 ≈ 1 day in 40; 3× ≤ 1 in 125). *Snippet.* https://www.dailyforex.com/forex-trading-mind/2016/12/volatility-profiles-major-pairs/83545
- energyexch forum, EURUSD 51-week tally (Tuesday least likely weekly extreme). *Snippet.* https://www.energyexch.com/thread/post/10434555
- Edgeful IB report and ES strategies page (double-break 23.6% over 30 days; 37.0% in another report). *Snippet*, small samples. https://www.edgeful.com/blog/posts/initial-balance-breakout-report, https://www.edgeful.com/blog/posts/es-futures-trading-strategies
- Via sibling studies: fxbacktest.app (E2, E5-E8), tradingstats.net (E10-E11, X5), edgeful (E9, E14, X1-X3), mypivots (E4), Elite Trader ES count (bias_dol 2.1).
