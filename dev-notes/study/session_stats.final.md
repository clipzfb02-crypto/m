# Session / day / week statistics: combined final study (Researcher A + Researcher B) for DOL Engine v2

Domain: published and reproducible statistics on sessions, days and weeks for ES/NQ/YM/RTY, CL, (GC), EURUSD and BTC:
- PDH/PDL taken next day, and in which session;
- which session prints the daily high/low;
- Asia / London / NY AM / overnight ranges and whether later sessions take them;
- what happens after the first break of a range;
- ADR distribution, "ADR exhaustion", range-used state and how ADR relates to volatility;
- weekday of the weekly high/low, PWH/PWL during the week, Monday range;
- gap fills (RTH, weekend FX, BTC "CME gap") and opening reversals;
- ORB / IB / NR7 / inside days.

The question throughout: which key level is taken, when, and with what probability, and how the engine should use that.

Line numbers refer to `brief/baseline_v2.pine`, which is byte-identical to `/home/user/m/indicators/dol_engine.pine` (checked with `diff -q` in this pass). Every engine line reference below was re-checked by B.

## How this report was made

- **Researcher A** wrote `study/session_stats.md`. Its computations are in `study/session_tools/` (`daystats.py`, `afterbreak.py`, `pooled.py`, `hazmodels.py`, `weekly.py`, `gaps.py`, `nullcheck.py`, `sesslib.py`).
- **Researcher B** (this pass) verified A, replicated A's tests on a new period, ran new tests and added literature. B's scripts are in `study/session_b_tools/`:

  | Script | What it computes | Output |
  |---|---|---|
  | `b_units.py` | chart ATR vs ADR on 1m/5m/15m/1h; ADR vs close-to-close σ; ADR profile vs Brownian and stochastic-volatility benchmarks | `out_units.txt` |
  | `b_hz5m.py` | 5-minute causal test: does the "today factor" add to a trailing σ or double count? | `out_hz5m.txt` |
  | `b_hz1h.py` | the same test on A's 1h rows (A's `hazmodels.py`, two columns added) | `out_hz1h.txt` |
  | `b_hz2.py` | which day-state estimator should scale the clock: today factor vs fast deseasonalised level vs blend; day-end and H-bar horizons | `out_hz2_*.txt` |
  | `b_surface.py` | prequential test: does a per-chart learned calibration surface (A's SESS-2) beat one global offset? | `out_surface.txt` |
  | `b_expr.py` | can the expected range-so-far curve be derived from the variance clock? | `out_expr.txt` |
  | `b_replicate.py` | A's `daystats.py`/`afterbreak.py` on a new dataset: EURUSD 2022-10 → 2023-10 | `out_EURUSD23_day.txt`, `out_afterbreak_EURUSD23.txt` |
  | `b_afterbreak_pool.py` | day-clustered pooled SE of A's after-break residuals on the four index futures | `out_afterbreak_pool.txt` |

  Run any of them with `python3 -I <script> [args]` from that folder.

**Marking.**
- `[A]`: A's finding, kept as is.
- `[A✓B]`: A's finding, re-checked by B (re-run, replicated on new data, or confirmed by a new source).
- `[A, CORRECTED by B]`: changed; the entry says what changed and why.
- `[B-NEW]`: new in this pass.

**Evidence grades:**
- **strong**: peer-reviewed, or a large replicated quantitative study;
- **moderate**: reproducible numbers with a sound null;
- **weak**: practitioner consensus, small or vendor samples, or a marginal statistic;
- **none**: folklore, or tested and not supported.

**Research-tool note (honest).**
- Firecrawl web search and scrape had no credits in either pass. The Firecrawl research index (arXiv full text) worked.
- WebFetch could not resolve most hosts. B tried ideas.repec.org, concretumgroup.com, fxstreet.com and edgeful.com; all failed DNS. A also failed on edgeful, nexusfi, linnsoft and trevor-trades. Those hosts would have to be allowed in the session's network settings.
- WebSearch worked, but it returns result summaries only.
- Numbers marked *snippet* come from search-result text; the page itself was not read. Numbers marked *[this study]* come from A's or B's own reproducible scripts, and they carry the main weight.

---

## 0. Executive summary

1. **Session, day and week levels are frequent targets, but they are not stronger magnets than geometry and the volatility clock predict.** [A✓B]
   - A's day-bootstrap null takes another day's whole path, rescales it by ADR and starts it at today's price at the same clock time. Against it, PDH/PDL take rates, first-take session, HOD/LOD session, Asia/London raids, the weekday of the weekly extreme and PWH/PWL take rates all agree within about ±3 pp on 7 markets.
   - **B replicated it out of period** on EURUSD 2022-23 (238 days), using A's code on new data. Every table matched its null again:
     - PDH 50.4% vs 52.5%, PDL 49.6% vs 50.7%;
     - HOD session within ±1.1 pp;
     - the day-end hazard table overall 28.3% vs 28.7%.
   - Peer-reviewed support: Mok, Lam & Li (2000) cannot reject an intraday random walk for the **time of the daily high/low** in S&P 500 futures.
   - That is market-specific. Hang Seng futures (Mok, Lam & Li) and FTSE-100/CAC-40 futures (Copeland, Lam & Jones 2004) do show an excess of extremes at the open. A per-chart clock surface (TIME-2/TIME-3) learns that; a fixed session prior does not.
   - Fixed session/killzone affinities (`f_kzAff`, 597-602, applied at 1941) and weekday priors therefore have no support.

2. **[A, CORRECTED by B] The "opposite side after the first break" residuals are weak, not moderate.**
   - A reported each index future separately and called the Asia two-sided raid "≈3 SE pooled". ES, NQ, YM and RTY share the same 250 days. With day-clustered pooling (B):

     | Range | Pooled real − null | Day-clustered SE | z |
     |---|---|---|---|
     | Asia 20:00-00:00 | +4.2 pp | 2.1 | **+2.0** |
     | London 02:00-05:00 | +1.7 | 2.2 | +0.8 |
     | NY AM 10:00-12:00 | −2.5 | 1.7 | −1.5 |
     | Overnight 18:00-09:00 | 0.0 | 1.8 | 0.0 |
     | PDH/PDL | −0.5 | 1.7 | −0.3 |

   - Five ranges were tested, so z = 2.0 is marginal.
   - On EURUSD 2022-23 the PD and London residuals **flip sign** (+1.9 and +2.1 pp, against A's −2.0 and −6.5 pp on 2017-18).
   - A calibrated clock × day-state model leaves **no** consistent "sibling taken" residual (§2.14).
   - Only the NY AM "one-sided afternoon" keeps its sign in all 8 datasets, and it is small (−1.5 to −5.7 pp).
   - Conclusion: no sibling or after-break multiplier, fixed or learned.

3. **"ADR exhaustion" is false; the ADR profile is Brownian motion plus stochastic volatility.** [A✓B]
   - A: a day that has used ≥ 1 ADR extends 4-10 pp **more** than an ADR-scaled null. Logistic coefficient on log(range used): +0.22 indices, +0.23 BTC, +0.10 CL. EURUSD is neutral.
   - B replicated this on EURUSD 2022-23: at ≥ 1.3 ADR used, +4.9 pp (x = 0.10) and +2.9 pp (x = 0.25); otherwise at the null.
   - **[B-NEW]** A constant-volatility Brownian day gives P(range ≥ 1 ADR) = 43.7%. Adding lognormal day volatility (sd 0.35, AR 0.6) gives:

     | | P(≥ 1 ADR) | P(≥ 1.5) | P(≥ 2) | lag-1 corr |
     |---|---|---|---|---|
     | BM + stochastic vol | 42.5% | 15.3% | 5.2% | 0.30 |
     | Real, 8 markets | 38.5-45.8% | 10.4-16.4% | 2.4-8.0% | 0.00-0.41 |

   - Every published "ADR completion" number is therefore volatility arithmetic.
   - ADR is a good **unit**: σ_day ≈ ADR / 1.55 (measured 1.53-1.57 on CME, EURUSD and BTC; Brownian theory sqrt(8/π) = 1.596). It is a bad **cap**.

4. **Horizon matters as much as distance.** [A✓B]
   - For an untaken PDH/PDL 0.2-0.35 ADR away, P(taken by day end) falls through the day:

     | Forecast made in | Asia | London | NY AM | NY PM |
     |---|---|---|---|---|
     | Index futures (A) | 64% | 57% | 47% | 19% |
     | EURUSD 2022-23 (B) | 62% | 57% | 47% | 7% |

   - The engine's PoT uses a fixed H-bar horizon (`potH`, 183/305) and cannot say "today".
   - **[B-NEW]** In ADR units the engine's candidate universe depends on the chart timeframe:

     | Chart | `maxATR` = 10 ATR equals | eject distance (15 ATR) equals |
     |---|---|---|
     | 1m | 0.16-0.20 ADR | 0.24-0.31 ADR |
     | 5m | 0.41-0.50 ADR | 0.62-0.75 ADR |
     | 15m | 0.79-0.90 ADR | 1.18-1.35 ADR |
     | 1h | 1.67-1.86 ADR | 2.50-2.79 ADR |

   - So on 1-5 minute charts a PDH that still has a 17-29% chance today is outside the pool.

5. **[A, CORRECTED by B] Where day state belongs. A's SESS-1 spec (`sigD = potSig·√fDay`) would make PoT worse.**
   - **Multiplying the engine's trailing σ by A's "today factor" raises Brier everywhere** (day-end forecasts, 2-fold recalibrated):

     | Chart | Market | Brier change |
     |---|---|---|
     | 1h | IDX | +2.2% |
     | 1h | CL | +4.9% |
     | 1h | EURUSD | +4.8% |
     | 1h | BTC | +3.3% |
     | 5m | IDX | **+4.6%** (day-block CI +1.8 to +7.5%) |

     The trailing 50-bar σ already holds most of today's activity, so the factor double counts.
   - The today factor helps only a **clock-based** variance (ADR × time-of-day shape). There it competes with TIME-3's fast deseasonalised level (`clkLf`):
     - **H-bar PoT** (the engine's main PoT): the fast level is as good or better (5m IDX by 2.5%, 5m CL by 11%, 1h by 0-1%). The today factor adds nothing there.
     - **Day-end horizons:** the today factor wins on 5m IDX (−7.4%), ties on 1h, and loses badly on 5m CL (+19.8%). A geometric blend is never far from the best.
   - Design: the day state enters **only** the day-end and week-end key-level PoT, as `V = sqrt(V_clockFast × V_ADR·fDay)`. It never multiplies `potSig` or the ATR surface, and it never caps.

6. **[A, CORRECTED by B] A learned per-chart hazard surface (A's SESS-2, 432 cells) adds nothing.**
   - Prequential test (B): ES, NQ, YM, RTY and CL 1h for 2025-26, BTC 1h for 2017-24. Each surface was learned online, day by day, on top of the analytic clock × day-state model.
   - Cell surfaces (time bucket × sibling, and × distance) scored 0.1-1.1% **worse** than one global logit offset on every CME symbol.
   - The global offset itself helps only where the analytic level is off: BTC −9.0%; CME −0.1 to +0.9%.
   - A 5-minute chart holds about 17 days of history at 5,000 bars, so cells would never fill there anyway.
   - Keep one prequentially gated calibration offset per chart (QPOT-04 style).

7. **Gaps: no magnet beyond distance in FX and BTC; a small, dated opening-reversal effect in index futures.** [A✓B + B-NEW literature]
   - A's data:
     - BTC "CME gap": 4-week fill 86.7% vs mirror 89.4%; gaps > 1 ADR continue;
     - EURUSD weekend gaps: fill = mirror;
     - index RTH gaps: +6.9 pp (n = 204).
   - Literature:
     - Fung, Mok & Lam (2000) and Grant, Wolf & Yu (2005; S&P futures 1987-2002) find intraday reversals after large opening moves, weakened after costs.
     - On MNQ 2021-25 a gap-fill fade has T = −0.3 to −0.6 (Mesfin 2026, preprint).
     - Plastun et al. (2020) find gap-direction momentum, the opposite of the fill myth.
   - Use no fixed gap prior; the ledger grades any gap level (ICTPD-6).

8. **[B-NEW] Engine bug: stale key-level labels.**
   - A registry entry keeps `src = 6` ("PDH", tier 0.80, `f_kzAff`) after the next day starts (`f_pushExt` 1211-1223, registry → pool 1833-1852). The same holds for weeks and sessions.
   - So the engine can show "Target: PDH" for a high that is three days old while the real PDH sits elsewhere. SESS-2 fixes it.

9. **Proposals** (§4, best first):

   | # | Proposal | Priority |
   |---|---|---|
   | SESS-1 | Key-level PoT to day end and week end ("Today %", "This week %"), from the clock with a day-state level and one gated calibration offset. Replaces A's SESS-1, SESS-2 and SESS-5 | P1 |
   | SESS-2 | Demote stale PD/PW/session labels | P2 |
   | SESS-3 | Session affinity neutral by default; no learned session or sibling multiplier; tier means importance, not probability | P2 |
   | SESS-4 | Key-level "taken" alerts and a day/week context row | P2 |
   | SESS-5 | ADR as a unit, from a non-repainting daily request, plus an optional ADR distance mode | P3 |
   | SESS-6 | Day-boundary input | P3 |

   - Mapping from A's IDs: A-SESS-1, 2 and 5 → SESS-1; A-SESS-3 → SESS-3 (corrected); A-SESS-4 → SESS-4; A-SESS-6 → SESS-6 and SESS-5.
   - Siblings that cite "SESS-2" (TIME-6) or "SESS-3 learned" (TIME-5) should read the new SESS-1 and SESS-3.

---

## 1. Concepts: definitions and parameters

Notation [A]:
- "Taken" = traded **through** (strict `>` / `<`), matching the engine's liquidity touch (`touched`, 622-623).
- ADR14 = mean of the prior 14 full-day ranges (H − L), known at the day open. AWR10 is the weekly equivalent.
- Day definitions:
  - CME: 18:00-17:00 ET (the TradingView daily session, what `timeframe.change("D")` uses).
  - FX: 17:00-17:00 ET.
  - Crypto: 00:00-24:00 UTC.
- Sessions in New York time (1-hour resolution in the tests): Asia 18:00-02:00, London 02:00-08:00, NY AM 08:00-12:00, NY PM 12:00-17:00.
- The engine's own windows (inputs 107-109; killzones 223-226): Asia range 20:00-00:00, London 02:00-05:00, NY AM 09:30-12:00.
  - `time()` tests only the bar open, so on a 1h chart the NY AM window is 10:00-12:00 (ict_time §1.2).

### 1.1 PDH / PDL taken next day [A]
- **Definition.** P(next day's high > prior day's high). The same for the low, both, or neither.
- **Conditioned on the open location:** above PDH (gap beyond), upper half of the prior range, lower half, below PDL.
- **Edge cases:**
  - A gap beyond the level counts as taken at the open. The engine does not push such a level (`f_pushExt` requires `high <= px`, 1212), which is consistent.
  - Holidays and short days: dropped when there are < 20 hourly bars.
  - Weekends: the prior day is the previous trading day.
- **Practitioner use:**
  - "PDH/PDL is the day's first draw."
  - ICT daily bias: closed above PDH → PDH+ next. bias_dol §1.3 finds the bias rule adds nothing beyond geometry.
  - edgeful-style: "PDH broken → green session 67% (YM)". That is a statement about direction, not about reach.
- **Probability driver.** Distance from the open in ADR units, then time left (§1.5).

### 1.2 Session of first take; session of the HOD/LOD [A; B added the academic tests]
- **Definitions:**
  - The session containing the first bar that trades through the level.
  - The session containing the bar that prints the day's high (first print on ties).
- **Null logic.** The time of an extreme follows the arcsine law in business (variance) time: the first and last high-variance slices get the mass.
- **Academic form [B-NEW].** Mok, Lam & Li (2000) and Copeland, Lam & Jones (2004) test the empirical distribution of daily high/low *times* against the arcsine distribution an intraday random walk implies. Their null has no volatility clock. A's day-bootstrap null does, so it is the stricter test.
- **"High or low of the day in the first hour"** [B-NEW]. This is the same arcsine arithmetic. One S&P 500 test of 885 days (2021-25) found 70.5%, against a random-direction baseline of 68.5% (*snippet*, TradingView idea).

### 1.3 Session ranges and later raids [A]
- **Definition.** The H/L of a fixed clock window. After the window closes, record whether each side is traded through before the day ends: single (one side), double (both) or none.
- **Windows tested:** Asia 20:00-00:00 (engine); Asia 18:00-02:00; London 02:00-05:00 (engine); London 02:00-08:00; NY AM 10:00-12:00 (engine on 1h); overnight 18:00-09:00 (ONH/ONL proxy at 1-hour resolution).
- **Width conditioning.** Session width in ADR terciles.
- **[B] Comparability warning.** Vendor numbers use different windows and different "later" periods, so they cannot be compared without the exact definition. For example:
  - edgeful YM, "NY breaks both London H/L": 4.8%;
  - A, ES London 02:00-05:00 range, both sides taken by day end: 59.6%.

### 1.4 After the first break of a range [A]
- **Definition.** For a range [L, H], let the first through-trade of either side happen on bar k. Until the day (or week) end, measure:
  - (a) P(the opposite side is also taken);
  - (b) P(the broken side extends +0.25 / +0.5 ADR beyond the level);
  - (c) P(the day closes back inside the range), the failed-break rate.
- A same-bar double break is ambiguous and excluded.
- **Practitioner use:** "sweep and reverse to the other side" (Judas swing, Turtle Soup) vs "break and run".

### 1.5 Time-of-day hazard of an untaken key level [A; B added the analytic form]
- **Definition.** At each clock point t, for each untaken PDH/PDL, take d = distance from the close to the level in ADR units. The outcome y = traded through by day end. Tabulate P(y | d, session at t).
- **Analytic form [B-NEW].** Driftless reflection: `P = erfc(d / sqrt(2·V_rest))`.
  - `V_rest` = variance expected from now to the day end = σ_day² × (share of the day's clock variance still to come) × day-state factor.
  - With σ_day = ADR/1.596 and the whole day ahead, a level d ADR from the open has P = 2Φ(−1.596·d):

    | d (ADR) | 0.05 | 0.15 | 0.275 | 0.425 | 0.625 | 0.875 | 1.25 |
    |---|---|---|---|---|---|---|---|
    | 2Φ(−1.596·d) | 0.94 | 0.81 | 0.66 | 0.50 | 0.32 | 0.16 | 0.05 |
    | ES real (bins 0-.1 … ≥ 1) | 0.97 | 0.77 | 0.56 | 0.50 | 0.31 | 0.38 | 0.16 |

  - Real days have fatter far tails because day volatility varies.

### 1.6 ADR, range used, "ADR exhaustion", day state [A; B corrected and extended]
- **ADR(N).** Mean of N prior daily ranges (N = 5, 10, 14 or 20 in practice).
- **Practitioner rules:**
  - "When price has done its ADR, the day's extremes are in."
  - "Targets beyond the ADR projection are unlikely."
  - ADR projections: open ± ADR; day low + ADR / day high − ADR.
- **Test [A].** At time t, the range used so far is u = (running high − running low)/ADR. Does P(extend beyond the running extreme by x·ADR before the day ends) fall with u (exhaustion) or rise (clustering), relative to a null that knows only ADR?
- **Day-state estimators [A, CORRECTED and extended by B]:**
  - **Today factor** (A): `f = clamp(rangeSoFar/ADR ÷ E[rangeSoFar/ADR at this clock time], 0.5, 2.5)`.
    - Shrunk form: `fs = 1 + w·(f − 1)`, with w = the expected share of the day's range already printed.
    - **[B-NEW]** The denominator can be derived from the clock: `E[rangeSoFar(t)] ≈ E[R] · sqrt(Vcum(t)/Vday)` (Brownian scaling), with E[R]/ADR ≈ 1.00-1.08. Max error vs the empirical curve: 0.021 (ES), 0.023 (NQ), 0.026 (BTC), 0.10 (CL, early-evening slots) (`out_expr.txt`).
  - **Fast deseasonalised level** (TIME-3's `clkLf`): an EWMA (span `potLen` = 50 bars) of bar variance ÷ the clock's expected variance for that slot.
  - **Blend** [B-NEW]: `sqrt(fastLevel × fs)`.
- **"Noise area"** (Zarattini, Aziz & Barbon 2024, *secondary description*): the open ± the 14-day average absolute move from the open at the same minute, with a gap adjustment. This is a practitioner-academic form of the same "expected move by this time of day" denominator.
- **Range-based volatility** [B-NEW]:
  - Parkinson (1980) and Garman & Klass (1980) give the range-based variance estimators. The engine's TIME-3 proxy is Garman-Klass.
  - Alizadeh, Brandt & Diebold (2002): log range is close to Gaussian, and volatility has one highly persistent and one fast mean-reverting factor. That is why a day-state term can add to a multi-day level.
  - Martens & van Dijk (2007): the "realized range" (a sum of intraday ranges), scaled by the average daily range, is an efficient volatility measure. ADR-scaled intraday ranges are a standard construction.

### 1.7 ADR ↔ σ conversion and distance units [B-NEW]
- **Brownian range constant** (Feller 1951): E[max − min over T] = sqrt(8/π)·σ·√T = 1.596·σ·√T.
  - Discrete bars and fat tails lower the measured ratio ADR14 / σ_close-to-close(20d):

    | Data | ADR / σ |
    |---|---|
    | ES, NQ, CL (1h → daily) | 1.53-1.54 |
    | EURUSD (1h → daily) | 1.56 |
    | BTC (1h → daily) | 1.55 |
    | OANDA EURUSD daily 2002-26 | 1.57 |
    | Coinbase BTC daily | 1.54 |
    | Cash SPX / NASDAQ daily | 1.31 / 1.22 (the RTH range excludes the overnight gap that σ includes) |

  - Rule: **σ_day ≈ ADR / 1.55** for the intraday session.
- **Chart ATR vs ADR.** The engine measures every distance in chart-timeframe ATR(14). Median ATR(14)/ADR14 is 0.016-0.020 (1m), 0.041-0.050 (5m), 0.079-0.090 (15m) and 0.167-0.186 (1h) on six CME futures. The consequences are in §0.4 and §2.15.

### 1.8 Weekly: weekday of the weekly extreme, PWH/PWL, Monday range [A]
- **Weekday of the weekly high/low.** First print within full weeks (5 trading days; 7 for BTC).
- **ICT weekly profiles:** "Tuesday low of week", "Wednesday reversal", and so on (ict_time §1.10).
- **PWH/PWL.** P(taken during the week); the weekday of the first take.
- **Monday range.** P(Monday's high/low is taken Tue-Fri).

### 1.9 ORB (Crabel), initial balance, NR7 / inside day [A; B verified the stretch definition]
- **ORB.** Stop orders at the open ± a "stretch". The stretch is the 10-day average of the smaller of (high − open, open − low).
  - Verified against oxfordstrat and mypivots definitions. One forum notes that signed vs absolute differences give different values.
  - The first stop hit sets the direction.
  - Here the smaller-side excursion from the open has a median of 0.17-0.20 ADR [A] (EURUSD 2022-23: 0.22 [B]). That is the stretch in ADR units.
- **IB.** The RTH 09:30-10:30 range; "range extension" = trading beyond it.
- **NR7.** The day's range is the smallest of the last 7. **Inside day.** H ≤ H[1] and L ≥ L[1].
- **Practitioner use:** contraction → expansion; trade the first break.

### 1.10 Gaps and opening reversals [A; B added the literature]
- **RTH gap:** the 09:30 open vs the prior 16:00 close (index futures).
- **Weekend gap:** Friday close vs Sunday open.
  - FX: 17:00 ET.
  - BTC "CME gap": the spot price at the CME Friday 17:00 ET close vs the Sunday 18:00 ET reopen.
- **Fill:** price trades back to the pre-gap close within the window. **Mirror:** price trades the same distance in the gap's direction. Under a driftless walk P(fill) = P(mirror), so **fill − mirror** isolates any magnet effect.
- **Opening reversal** [B-NEW]: after a large opening price change, intraday returns run against it (overreaction). Fung, Mok & Lam (2000); Grant, Wolf & Yu (2005).

---

## 2. Evidence (numbers and sources)

### 2.0 Data and method

**Datasets [A]**

| Dataset | Coverage | Days / weeks | Notes |
|---|---|---|---|
| CME ES, NQ, YM, RTY, CL, GC 1-hour (UTC → NY) | 2025-03-21 → 2026-04-15 | 266 Globex days, 250 valid (CL 178) | `amt_data/cme`. GC has contract-roll gaps and is excluded from conclusions (null range/ADR 0.71 vs real 1.05) |
| ES, NQ, YM, RTY, CL, GC 1-minute | 2026-01-20 → 2026-04-15 | ≈ 60 days each | A: RTH gaps. B: 5-minute bars for the day-state tests |
| EURUSD 1-hour | 2017-04-19 → 2018-02-07 | 192 valid days | `bias_data/EURUSD.csv` |
| BTCUSD Bitstamp 1-minute → 1-hour | 2017-01-01 → 2025-01-06 | 2,913 valid UTC days | public GitHub dataset `ff137/bitstamp-btcusd-minute-data`, cached as `session_data/btc_1h.pkl` |
| S&P 500, NASDAQ Composite daily | 1999-2018 | 694 valid weeks | `bias_data` |
| EURUSD OANDA daily (17:00 NY sessions) | 2002-05 → 2026-04 | 1,220 weeks | `dl_knn/.../pine_oanda_eurusd_1d_full_history.csv` |
| BTCUSD Coinbase daily | 2014-12 → 2026-05 | 591 seven-day weeks | same folder |

**Added by B [B-NEW]**

| Dataset | Coverage | Use |
|---|---|---|
| EURUSD 15-minute (MT5 broker time = Europe/Athens, so 00:00 broker = 17:00 NY) → 1-hour | 2022-10-10 → 2023-10-02, 238 valid days | out-of-period replication |
| The OANDA and Coinbase dailies above | | range persistence and ADR/σ over 24 / 11 years |

**Null models [A]**
- **Day-bootstrap (primary).**
  - A donor day's hourly path from the forecast slot onward is normalised (H, L, C relative to the slot open, ÷ the donor's ADR14).
  - It is rescaled by today's ADR14 and chained from today's real price at that slot.
  - Calibration check (mean range/ADR, real / null): ES 0.999/1.000, NQ 1.000/1.005, YM 0.991/0.977, RTY 0.998/0.994, CL 1.078/1.087, EURUSD 1.031/1.035, BTC 1.051/1.046.
- **Slot null** (each hour drawn from a random day's same slot). It overstates BTC and CL ranges, so it is reported only for comparison.
- **Weekly:** a week-bootstrap; for the weekday test, a day-order shuffle. **Gaps:** the mirror level.

**Causal forecast tests [A; extended by B]**
- Models are driftless reflection forecasts using only past data.
- Brier scores are reported raw and after a 2-fold time-split Platt recalibration. B adds day-block bootstrap CIs, because snapshots within a day share one path.

**Caveats [A + B]**
- The four index futures share the same days. Pool them only with day clustering (B, §2.12). A's naive pooled SEs were too small.
- Snapshots within a day overlap, so naive logistic SEs are optimistic.
- Hourly resolution: same-bar double breaks are excluded, and the 09:00 bar mixes premarket and RTH.
- The day null uses donors from the whole sample (in-sample shapes). The causal comparisons use only past data.
- B's 5-minute tests cover about 37-45 days per symbol. Treat them as directional, with the CIs shown.

### 2.1 PDH / PDL taken during the next day [A✓B]

All days, real vs day-bootstrap null [A]:

| Market | P(PDH) | P(PDL) | both | neither | null P(PDH) | null P(PDL) | null both | null neither |
|---|---|---|---|---|---|---|---|---|
| ES | 0.588 | 0.444 | 0.144 | 0.112 | 0.570 | 0.437 | 0.149 | 0.142 |
| NQ | 0.596 | 0.436 | 0.144 | 0.112 | 0.571 | 0.435 | 0.139 | 0.133 |
| YM | 0.524 | 0.488 | 0.104 | 0.092 | 0.536 | 0.461 | 0.131 | 0.134 |
| RTY | 0.492 | 0.468 | 0.100 | 0.140 | 0.550 | 0.452 | 0.143 | 0.141 |
| CL | 0.511 | 0.416 | 0.079 | 0.152 | 0.525 | 0.466 | 0.137 | 0.146 |
| EURUSD 17-18 | 0.562 | 0.406 | 0.099 | 0.130 | 0.566 | 0.435 | 0.124 | 0.123 |
| BTC 17-24 | 0.486 | 0.414 | 0.107 | 0.207 | 0.516 | 0.440 | 0.154 | 0.198 |
| **EURUSD 22-23 [B]** | **0.504** | **0.496** | **0.130** | **0.130** | **0.525** | **0.507** | **0.144** | **0.112** |

- **By open location** (real / null):
  - ES upper half: PDH 0.754/0.755, PDL 0.246/0.273. ES lower half: PDH 0.319/0.294, PDL 0.692/0.639.
  - BTC upper half: PDH 0.657/0.678. BTC lower half: PDL 0.604/0.633.
  - EURUSD 22-23 [B]: upper half PDH 0.721/0.772; lower half PDL 0.732/0.757.
- **Distance gradient** (ES, opens inside the range, P(PDH by day end) real / null) [A]:

  | d/ADR | 0-0.1 | 0.1-0.2 | 0.2-0.35 | 0.35-0.5 | 0.5-0.75 | 0.75-1 | ≥ 1 |
  |---|---|---|---|---|---|---|---|
  | real / null | 0.97 / 0.94 | 0.77 / 0.84 | 0.56 / 0.70 | 0.50 / 0.57 | 0.31 / 0.35 | 0.38 / 0.22 | 0.16 / 0.08 |

- **Nearer side first** (ruin rule): right 79.7% (ES), 76.3% (NQ), 78.4% (EURUSD 17-18), 76.3% (BTC), 80.7% (EURUSD 22-23 [B]).
- **"Both taken" is below the null in 7 of 8 datasets:** −0.5 to −5.8 pp; NQ +0.5. Each dataset has n ≈ 200-250 and SE ≈ 2-2.5 pp, so the effect is small and only consistent in sign.
- **External agreement:**
  - Elite Trader user count, ES: PDH or PDL touched on 90.32% of days (168/186), via bias_dol. Here at least one side is taken on 88.8% of ES days.
  - edgeful SPY inside days: PDH 52%, PDL 40%, both 15.3% (72 days), via bias_dol.
  - [B] edgeful (inside-day post): yesterday's high/low reached on 81-88% of NY sessions over 6 months on ES, NQ, TSLA and NVDA (*snippet*; "either" is implied).
  - Linnsoft, ES: prior close touched on 1,048 of 1,803 days (58.1%) (*snippet*).
  - [B] edgeful: on NQ, when price opens below PDL it does not test PDL 75% of the time over a year (*snippet*). This is the gapped-through case, which the engine already treats as taken.
- **Reading.** PDH/PDL are frequent targets: at least one side is taken on 79-91% of days. Their take rate is geometry: distance in ADR, then time left.

### 2.2 When PDH/PDL is first taken; when the HOD/LOD prints [A✓B]

Cumulative P(PDH taken by the end of each session), real / null [A]:

| Market | by end of Asia | by end of London | by end of NY AM | by day end |
|---|---|---|---|---|
| ES | 0.256 / 0.301 | 0.348 / 0.379 | 0.512 / 0.506 | 0.588 / 0.570 |
| NQ | 0.276 / 0.315 | 0.356 / 0.391 | 0.528 / 0.528 | 0.596 / 0.571 |
| EURUSD 17-18 | 0.286 / 0.276 | 0.417 / 0.444 | 0.521 / 0.538 | 0.562 / 0.566 |
| BTC (UTC day) | 0.247 / 0.284 | 0.350 / 0.387 | 0.427 / 0.459 | 0.486 / 0.516 |
| EURUSD 22-23, PDL [B] | 0.214 / 0.214 | 0.349 / 0.355 | 0.479 / 0.481 | 0.496 / 0.507 |

Session that prints the day's high / low, real / null:

| Market | HIGH Asia | London | NY AM | NY PM | LOW Asia | London | NY AM | NY PM |
|---|---|---|---|---|---|---|---|---|
| ES | 16.0 / 17.1 | 12.4 / 12.0 | 26.0 / 24.8 | 45.6 / 46.1 | 29.2 / 28.6 | 14.4 / 14.8 | 24.0 / 26.0 | 32.4 / 30.6 |
| NQ | 18.8 / 19.5 | 10.0 / 9.8 | 30.8 / 31.4 | 40.4 / 39.3 | 27.6 / 27.9 | 14.0 / 12.2 | 28.0 / 29.8 | 30.4 / 30.1 |
| YM | 17.6 / 19.0 | 11.6 / 9.6 | 32.4 / 33.9 | 38.4 / 37.4 | 23.2 / 21.8 | 12.8 / 12.4 | 30.4 / 31.7 | 33.6 / 34.1 |
| EURUSD 17-18 | 24.5 / 24.0 | 24.0 / 23.1 | 27.6 / 27.0 | 24.0 / 25.9 | 31.2 / 32.5 | 24.5 / 25.1 | 27.1 / 24.7 | 17.2 / 17.7 |
| BTC* | 44.3 / 43.3 | 14.7 / 15.5 | 16.7 / 16.8 | 24.3 / 24.4 | 43.8 / 44.1 | 16.7 / 17.1 | 16.3 / 16.0 | 23.2 / 22.9 |
| **EURUSD 22-23 [B]** | 22.3 / 22.0 | 26.1 / 26.0 | 31.1 / 31.6 | 20.6 / 20.5 | 23.1 / 22.2 | 21.0 / 22.1 | 30.7 / 29.5 | 25.2 / 26.2 |

\*BTC UTC day: "Asia" covers both the first ~6 h and the last ~4 h of the UTC day, the arcsine-favoured ends.

- **Median share of the final day range printed by each session's end:**
  - ES: Asia 0.36, London 0.52, NY AM 0.87. NQ: 0.38 / 0.54 / 0.91.
  - EURUSD 17-18: 0.37 / 0.74 / 1.00. EURUSD 22-23 [B]: 0.36 / 0.70 / 1.00.
  - FX is mostly done by noon NY.
- **External:**
  - DailyFX 2005-2009: the first FX hour set the daily high ~8% and the low ~6% of the time, vs 4.17% uniform (*snippet*). That is the arcsine end effect.
  - mypivots: ES RTH HOD 17.2% / LOD 16.7% in the first 15 minutes (via ict_time E4).
  - TradeThatSwing: London H/L broken after the US open, single 70.66%, both 25.1%, neither 4.25% (*snippet*; the "98%" headline contradicts the body).
  - [B] S&P 500 first hour, 885 days 2021-25: HOD or LOD in the first hour 70.5%, random baseline 68.5%. None of 16 first-hour rules survived costs (*snippet*).
  - [B] An "Al Brooks 90-minute" claim (≈ 90%) came out at 59% over 29 ES days (*snippet*).
- **Academic [B-NEW]:**
  - **Mok, Lam & Li (2000)**, *Review of Quantitative Finance and Accounting* 14(4):381-397. Daily high/low **times** in S&P 500 futures are consistent with an intraday random walk. Hang Seng futures have significantly more highs and lows in the first 15 minutes of both the morning and afternoon sessions. A later HKMA-linked study reports that this Hang Seng effect has disappeared.
  - **Copeland, Lam & Jones (2004)**, *Journal of Futures Markets* 24(4):337-357. On FTSE-100 and CAC-40 futures the arcsine-law test rejects the random walk both before and after screen trading; the authors suggest intraday overreaction.
- **Reading:**
  - "London/NY makes the high or low of the day" is the clock plus the arcsine law, within ±2.5 pp of the null on 6 datasets.
  - Where markets deviate (open-burst excess), the deviation is market-specific. TIME-2's time-of-day surface learns it per chart.
  - "Asia takes PDH first" is mostly geometry. In Asia real is slightly **below** the null (ES −4.5 pp, NQ −3.9, BTC −3.7) and catches up by NY.

### 2.3 Session ranges taken later the same day [A✓B]

Real / null, from the window close to the day end.

**Asia 20:00-00:00 (engine window)**

| Market | high | low | both | none |
|---|---|---|---|---|
| ES | 90.4 / 86.0 | 79.6 / 80.9 | 70.0 / 67.7 | 0.0 / 0.8 |
| NQ | 87.6 / 86.2 | 81.2 / 81.2 | 69.2 / 68.1 | 0.4 / 0.7 |
| YM | 89.2 / 86.1 | 84.4 / 84.6 | 73.6 / 71.1 | 0.0 / 0.4 |
| RTY | 91.6 / 85.4 | 82.8 / 83.6 | 74.4 / 69.4 | 0.0 / 0.4 |
| CL | 78.1 / 81.0 | 81.5 / 77.3 | 60.1 / 60.1 | 0.6 / 1.8 |
| EURUSD 17-18 | 84.9 / 83.5 | 78.6 / 78.7 | 63.5 / 62.4 | 0.0 / 0.2 |
| BTC | 73.3 / 73.6 | 72.3 / 71.2 | 46.9 / 48.1 | 1.3 / 3.4 |
| EURUSD 22-23 [B] | 81.5 / 82.3 | 82.8 / 83.1 | 64.3 / 65.5 | 0.0 / 0.1 |

**London 02:00-05:00 (engine window)**

| Market | high | low | both | none |
|---|---|---|---|---|
| ES | 83.6 / 82.2 | 76.0 / 76.0 | 59.6 / 58.9 | 0.0 / 0.7 |
| NQ | 84.0 / 82.2 | 76.0 / 76.8 | 60.0 / 59.4 | 0.0 / 0.5 |
| YM | 82.8 / 82.3 | 82.0 / 80.3 | 65.2 / 62.9 | 0.4 / 0.3 |
| RTY | 86.0 / 83.6 | 81.2 / 79.6 | 67.6 / 63.7 | 0.4 / 0.5 |
| CL | 73.6 / 74.2 | 70.8 / 66.2 | 44.9 / 42.3 | 0.6 / 1.9 |
| EURUSD 17-18 | 63.5 / 68.5 | 64.1 / 62.3 | 28.6 / 33.4 | 1.0 / 2.7 |
| BTC | 76.6 / 76.5 | 73.3 / 73.2 | 51.1 / 52.4 | 1.2 / 2.7 |
| EURUSD 22-23 [B] | 65.1 / 67.0 | 72.7 / 72.0 | 38.7 / 40.6 | 0.8 / 1.6 |

**NY AM 10:00-12:00 (the engine's window as seen on a 1h chart)**

| Market | high | low | both | single | none |
|---|---|---|---|---|---|
| ES | 59.2 / 59.6 | 45.6 / 46.7 | **13.6 / 19.1** | **77.6 / 68.0** | 8.8 / 12.9 |
| NQ | 58.0 / 57.5 | 45.2 / 44.8 | 16.0 / 17.3 | 71.2 / 67.7 | 12.8 / 15.0 |
| YM | 55.2 / 55.9 | 48.4 / 46.5 | 12.8 / 16.3 | 78.0 / 69.6 | 9.2 / 14.0 |
| RTY | 55.2 / 56.1 | 44.0 / 44.2 | 10.8 / 14.8 | 77.6 / 70.7 | 11.6 / 14.5 |
| CL | 53.9 / 55.2 | 45.5 / 46.2 | 11.2 / 15.8 | 77.0 / 69.9 | 11.8 / 14.4 |
| EURUSD 17-18 | 47.9 / 51.2 | 42.7 / 42.0 | 9.4 / 11.9 | 71.9 / 69.4 | 18.8 / 18.7 |
| BTC | 64.1 / 65.2 | 60.8 / 61.1 | 30.8 / 35.3 | 63.3 / 55.7 | 5.9 / 9.0 |
| EURUSD 22-23 [B] | 36.1 / 41.5 | 44.1 / 42.7 | 4.6 / 8.2 | 71.0 / 67.9 | 24.4 / 24.0 |

**Overnight 18:00-09:00 (ONH/ONL proxy)**

| Market | high | low | both | none |
|---|---|---|---|---|
| ES | 66.8 / 64.9 | 52.4 / 53.1 | 23.2 / 26.2 | **4.0 / 8.2** |
| NQ | 66.8 / 64.1 | 54.8 / 53.5 | 25.2 / 25.1 | **3.6 / 7.4** |
| YM | 67.2 / 68.5 | 60.8 / 59.7 | 31.6 / 33.7 | 3.6 / 5.5 |
| RTY | 67.6 / 64.6 | 60.8 / 56.3 | 34.8 / 28.4 | 6.4 / 7.5 |
| CL | 44.9 / 49.1 | 46.1 / 47.4 | 10.7 / 13.1 | 19.7 / 16.7 |
| EURUSD 17-18 | 45.8 / 45.4 | 36.5 / 38.1 | 4.7 / 6.9 | 22.4 / 23.3 |
| EURUSD 22-23 [B] | 42.9 / 44.2 | 46.6 / 47.0 | 7.1 / 10.4 | 17.6 / 19.2 |

- **Width conditioning** [A]:
  - ES full Asia (18:00-02:00): narrow tercile both sides 69.9% / 72.9%; wide 38.1% / 26.0%.
  - NY AM narrow tercile (< 0.32 ADR, n = 83): both 19.3% vs 35.9%.
  - EURUSD 22-23 [B]: wide Asia 18:00-02:00 both 50.0 / 38.0; NY AM narrow both 11.4 / 18.1.
  - Same signs as A: wide Asia ranges are taken two-sided a little more than random; narrow late-morning ranges resolve to one side.
- **External:**
  - fxbacktest via ict_time E6, Asian range 00:00-06:59 UTC: EURUSD high 68.2, low 68.4, both 37.7, neither 1.0; US100 82.0 / 73.8 / 56.2 / 0.4.
  - edgeful YM via ict_time E9: NY vs London single 83.2, double 4.8, none 12.0. The window differs from this table (§1.3).
  - tradingstats NQ via ict_time E11: ON range in RTH: only H 38.7, only L 32.6, both 22.9, none 5.8.
  - NexusFi: ON high or low touched 96% (*snippet*; ict_time confirmed 96.4%).
  - [B] Vendor "Asian range sweep + reversal" claims, such as 69.6% wins over 168 setups (*snippet*, promotional): no null, not usable.
  - [B] A vendor backtest of the plain GBPUSD London breakout, 2016-2026: −60% (*snippet*).
- **Reading:**
  - Asia and London ranges are geometry ±3 pp.
  - Afternoons break **one** side of the NY AM range more than random: +3 to +10 pp single and −1 to −6 pp both, sign-consistent in 8 of 8 datasets.
  - RTH breaks at least one ON extreme slightly more often than random on ES/NQ, which supports TIME-7 (ONH/ONL pools).
  - All of these are small effects.

### 2.4 After the first break [A, CORRECTED by B]

Opposite side taken by the day end, real / null and the difference in pp [A]:

| Range | ES | NQ | YM | RTY | CL | EURUSD 17-18 | BTC | **EURUSD 22-23 [B]** |
|---|---|---|---|---|---|---|---|---|
| PDH/PDL | −0.1 | +1.3 | −1.6 | −3.3 | −5.4 | −2.0 | −2.0 | **+1.9** |
| Asia 20-00 | +4.7 | +3.6 | +3.5 | +6.2 | −1.2 | +0.5 | −1.3 | −0.7 |
| London 02-05 | +1.2 | +0.8 | +0.6 | +4.4 | +3.5 | −6.5 | −0.6 | **+2.1** |
| NY AM 10-12 | −5.7 | −0.5 | −2.7 | −2.1 | −2.6 | −4.5 | −3.3 | −1.5 |
| ON 18-09 | −1.8 | −0.1 | −0.6 | +4.3 | +0.4 | −0.9 | n/a | +0.6 |

- **[B] Day-clustered pooling** of the four index futures (`b_afterbreak_pool.py`; the null is re-drawn, so the per-symbol values differ slightly from A's):

  | Range | Pooled | SE | z | Per symbol |
  |---|---|---|---|---|
  | Asia | +4.2 pp | 2.1 | 2.0 | ES +4.7, NQ +2.4, RTY +6.0, YM +3.7 |
  | London | +1.7 | 2.2 | 0.8 | |
  | NY AM | −2.5 | 1.7 | −1.5 | |
  | ON | 0.0 | 1.8 | 0.0 | |
  | PD | −0.5 | 1.7 | −0.3 | |

  A's "≈3 SE pooled" treated four series that share the same days as independent.
- **Broken side extends +0.25 ADR:** mixed, within ±5 pp [A]; EURUSD 22-23 −3.1 to +1.1 [B]. There is no robust "the break runs further than random" effect.
- **Failed breaks:** the day closes back inside the prior-day range after a PD break 39-50% of the time [A]; 44.1% for EURUSD 22-23 [B]. After an Asia break: 13-21% [A]; 15.0% [B].
- **Timing:**
  - BTC [A]: the later the first PD break, the smaller the opposite-side chance: Asia 16.3%, London 13.3%, NY AM 8.7%, NY PM 4.4%, each 0.3-3.3 pp under the null.
  - EURUSD 22-23 [B]: Asia 23.2/17.4, London 7.7/13.0, NY AM 4.3/4.5.
  - This decay is the clock, not a liquidity effect.
- **Weekly [A]:** opposite side after the first PW break:

  | Market | real | null |
  |---|---|---|
  | SPX | 12.0% | 14.8% |
  | NASDAQ | 13.0% | 14.6% |
  | EURUSD | 9.8% | 12.6% |
  | BTC | 10.4% | 16.9% |

  With n ≈ 630 weeks the SE is about 1.3 pp, so these are 1-4 SE.
- **External:**
  - fxbacktest: FX first Asian-break fade 49.4% (n = 9,598), a coin flip; crypto continues 55-58% (ict_time E7).
  - [B] Mesfin (2026, arXiv 2605.04004, MNQ 2021-25): an Asia-session "liquidity grab" (wick through a session extreme, close back inside), 6,442 events. Fading it: mean −2.20 pts, T = −14.1. Following it: −1.80 pts, T = −13.2. Gross directional content is only 0.2-0.8 pts either way.
  - [B] Taylor (2026, arXiv 2610.35887, NQ 2022-26, N = 484): after London sweeps the Asia range, there is no directional information beyond the daily trend (ict_time §0.5).
- **Reading (corrected):**
  - There is no robust "Judas" effect. The index-futures Asia two-sided raid is a 2-SE result among five ranges tested.
  - The PD, London and ON after-break residuals are noise.
  - The NY AM and PW "one-sided" lean has a consistent sign but is small.
  - With a calibrated clock × day-state model there is no residual left to learn (§2.14). **Evidence: weak.**

### 2.5 Time-of-day hazard of an untaken PDH/PDL [A✓B]

P(taken by day end | d/ADR now, session when the forecast is made), pooled ES/NQ/YM/RTY, real / day null (n) [A]:

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

- **EURUSD 22-23 [B]**, same layout:

  | d/ADR | Asia | London | NY AM | NY PM |
  |---|---|---|---|---|
  | 0.1-0.2 | 0.79 / 0.80 | 0.76 / 0.76 | 0.63 / 0.66 | 0.20 / 0.22 |
  | 0.2-0.35 | 0.62 / 0.65 | 0.57 / 0.57 | 0.47 / 0.44 | 0.07 / 0.06 |
  | 0.5-0.75 | 0.30 / 0.30 | 0.22 / 0.24 | 0.09 / 0.12 | 0.01 / 0.01 |
  | 1.0-1.5 | 0.14 / 0.07 | 0.09 / 0.05 | 0.02 / 0.02 | 0.00 / 0.00 |

  - Overall real 0.283 vs null 0.287; Brier of the null used as a forecast 0.1415 vs base rate 0.2028.
  - FX's afternoon is quieter than the index afternoon (NY PM 0.07 vs 0.19), which is the clock again.
- **BTC [A]** (UTC day, n = 94,208): the same shape, with real 2-9 pp **below** the null at 0.1-0.75 ADR (0.2-0.35: Asia 0.49/0.53, NY AM 0.36/0.45, NY PM 0.19/0.28). That is the "quiet day stays quiet" state an ADR-scaled null cannot see.
- **The far tail** (≥ 1 ADR) is 2× the null in Asia/London on every dataset: big days cluster (§2.13).
- **External:**
  - tradingstats via ict_time E11: 33.5% of ON first breaks happen in the first 5 RTH minutes, 68.7% by 10:00, 90% by 11:30.
  - Taylor (2026): 57% of AMD targets were already delivered before 09:40 NY.

### 2.6 Causal model comparison: forecasting "taken by day end" [A]

All models are driftless reflection, p = 2Φ(−d/√V), using only past data.

| Model | Variance V for the rest of the day |
|---|---|
| M_flat (engine-like) | σ² of the last 50 hourly close changes × bars left |
| M_clock | ADR² × Σ remaining slots v_slot (Garman-Klass variance per slot in ADR² units, mean of the last 250 days) |
| M_today | M_clock × f, f = clamp(range so far / E[range so far at this slot], 0.5, 2.5) |
| M_today_s | M_clock × (1 + w(f − 1)), w = E[share of the day's range printed by now] |

Brier (raw / after 2-fold time-split Platt recalibration):

| Group (n) | base rate | M_flat | M_clock | M_today | M_today_s |
|---|---|---|---|---|---|
| IDX pooled (26,137) | 0.2095 | 0.1539 / 0.1508 | 0.1473 / 0.1477 | **0.1437 / 0.1436** | 0.1444 / 0.1448 |
| CL (4,295) | 0.1886 | 0.1354 / 0.1373 | 0.1334 / 0.1380 | 0.1324 / **0.1346** | **0.1315** / 0.1349 |
| EURUSD 17-18 (4,865) | 0.1958 | 0.1350 / 0.1342 | **0.1297 / 0.1308** | 0.1340 / 0.1344 | 0.1305 / 0.1315 |
| BTC (92,949) | 0.1708 | **0.1294** / 0.1284 | 0.1454 / 0.1274 | 0.1334 / 0.1264 | 0.1381 / **0.1261** |

- **Calibration slopes:** M_flat 0.64-0.75 (over-confident at the extremes); M_clock 0.75-0.89; M_today 0.81-0.90.
- **BTC:** M_clock over-predicts before calibration (mean p 0.33 vs y 0.22), because the ADR mean is inflated by fat-tailed days. **The variance level must be adaptive or calibrated per chart.**
- **[B] Note on this table.** The `M_flat` row is a day-end forecast with the correct day-end horizon. The engine's live PoT also has the wrong horizon (fixed H), so its real gap to these models for a "today" question is larger than shown.

### 2.7 ADR, range used, exhaustion [A✓B]

Day range / ADR14:

| Market | q10 | q25 | q50 | q75 | q90 | P(≥ 1) | P(≥ 1.5) | P(≥ 2) | lag-1 corr |
|---|---|---|---|---|---|---|---|---|---|
| ES | 0.48 | 0.67 | 0.91 | 1.21 | 1.61 | 0.388 | 0.136 | 0.036 | 0.27 |
| NQ | 0.51 | 0.69 | 0.92 | 1.21 | 1.57 | 0.420 | 0.128 | 0.024 | 0.27 |
| YM | 0.55 | 0.71 | 0.90 | 1.19 | 1.55 | 0.376 | 0.120 | 0.024 | 0.20 |
| RTY | 0.53 | 0.69 | 0.91 | 1.21 | 1.58 | 0.412 | 0.124 | 0.040 | 0.19 |
| CL | 0.55 | 0.73 | 0.95 | 1.21 | 1.64 | 0.421 | 0.140 | 0.051 | 0.41 |
| EURUSD 17-18 | 0.60 | 0.73 | 0.97 | 1.21 | 1.51 | 0.458 | 0.104 | 0.036 | 0.00 |
| BTC | 0.46 | 0.62 | 0.87 | 1.25 | 1.78 | 0.396 | 0.158 | 0.073 | 0.27 |
| EURUSD 22-23 [B] | 0.58 | 0.72 | 0.90 | 1.21 | 1.53 | 0.391 | 0.105 | 0.025 | 0.09 |
| EURUSD OANDA D 2002-26 [B] | | | 0.92 | | | 0.428 | 0.129 | 0.041 | 0.01 |
| BTC Coinbase D 2014-26 [B] | | | 0.86 | | | 0.392 | 0.164 | 0.080 | 0.28 |
| **BM, constant vol [B]** | | | 0.95 | | | 0.437 | 0.082 | 0.010 | 0 |
| **BM + lognormal day vol (sd 0.35, AR 0.6) [B]** | | | 0.91 | | | 0.425 | 0.153 | 0.052 | 0.30 |

- **Max excursion from the day open, larger side, q50 / q80 / q95** [A]: ES 0.68 / 1.07 / 1.58; BTC 0.66 / 1.12 / 1.97; EURUSD 0.76 / 1.05 / 1.57. EURUSD 22-23 [B]: 0.67 / 1.02 / 1.58.
- **Smaller side:** q50 0.17-0.20 (EURUSD 22-23: 0.22), q80 0.32-0.36, q95 0.49-0.53 ADR.
- **[B] Range persistence in FX is weak in every era**, not just 2017-18. OANDA EURUSD lag-1 corr of range/ADR: −0.09 (2002-09), 0.05 (2010-17), 0.14 (2018-26). Futures run 0.19-0.41 and BTC 0.24-0.34. This is why day-state terms help FX least.

**Exhaustion test** [A]: P(extend beyond the running extreme by x·ADR before the day ends), by range used u, real / null:

| Group | x | u < 0.4 | 0.4-0.7 | 0.7-1.0 | 1.0-1.3 | ≥ 1.3 | logistic coef of log u |
|---|---|---|---|---|---|---|---|
| IDX | 0.10 | 63.5 / 65.9 | 44.2 / 41.8 | 29.5 / 25.9 | 26.3 / 20.4 | 19.7 / 14.9 | **+0.215** |
| IDX | 0.25 | 43.8 / 46.9 | 29.5 / 27.5 | 17.6 / 15.5 | 17.3 / 12.1 | 9.9 / 8.1 | |
| BTC | 0.25 | 31.9 / 37.8 | 22.3 / 22.7 | 15.9 / 14.2 | 16.0 / 10.8 | 15.7 / 6.6 | **+0.230** |
| CL | 0.25 | 42.4 / 47.2 | 29.3 / 27.2 | 12.6 / 15.2 | 10.7 / 11.7 | 11.4 / 6.8 | +0.102 |
| EURUSD 17-18 | 0.25 | 47.8 / 48.2 | 26.3 / 25.4 | 11.7 / 13.5 | 8.9 / 8.7 | 9.6 / 5.9 | −0.029 |
| EURUSD 22-23 [B] | 0.10 | 68.4 / 67.4 | 41.2 / 39.3 | 20.4 / 20.0 | 13.8 / 13.1 | 16.3 / 11.4 | |
| EURUSD 22-23 [B] | 0.25 | 47.4 / 49.0 | 25.6 / 25.8 | 9.6 / 11.7 | 7.5 / 6.9 | 7.8 / 4.9 | |

- A's SEs (0.008-0.032) are naive: hourly records overlap within a day. The sign is consistent across five datasets, so it is not in doubt; the size is.
- **Weekly** [A, `weekly.py` W4]: after Wednesday's close, extension of 0.25 AWR before the week ends:

  | Market | u < 0.5 | u ≥ 1.1 |
  |---|---|---|
  | SPX | 20.5 / 27.5 | 23.9 / 15.0 (n = 94, ≈ 2 SE) |
  | NASDAQ | 20.2 / 27.8 | 26.8 / 15.2 |
  | EURUSD | 26.2 / 27.6 | 19.1 / 16.6 |
  | BTC | 11.7 / 23.2 | 15.8 / 9.2 |

- **External:**
  - DailyForex 2016: a day range of 2× ATR20 occurs about 1 day in 40 (*snippet*). That matches P(≥ 2 ADR) = 2.4-8%.
  - A forum claim that price "stays within ADR ~60%" matches P(< 1 ADR) = 54-62%.
  - [B] A TradingView script author's claim that "a quarter to a third of days exceed 100% of ADR" is **contradicted**: 38-46% here, 44% under Brownian motion.
  - Engle & Sokalska (2012, *J. Financial Econometrics* 10(1):54-83): intraday variance = daily × diurnal × stochastic intraday components.
  - [B] Andersen & Bollerslev (1998, *J. Finance* 53(1):219-265): absolute intraday returns = daily volatility × an intraday periodic pattern. Their daily factor is the "level"; the day state is an online estimate of it.
- **Reading.** The ADR profile is Brownian motion plus stochastic volatility (B's benchmark matches the real quantiles and lag-1 correlation). "Exhaustion" has the sign backwards on 3 of 4 market groups and is neutral to slightly reversed on FX. **ADR is a unit and a level prior, never a cap.**

### 2.8 Weekly statistics [A]

**W1: weekday of the weekly high / low** (real / day-order shuffle null):

| Market | HIGH Mon | Tue | Wed | Thu | Fri | LOW Mon | Tue | Wed | Thu | Fri |
|---|---|---|---|---|---|---|---|---|---|---|
| SPX 99-18 | 23.3 / 26.8 | 14.7 / 13.6 | 14.8 / 13.1 | 14.8 / 15.1 | 32.3 / 31.4 | 29.0 / 32.8 | 15.4 / 15.0 | 14.7 / 13.1 | 17.1 / 14.0 | 23.8 / 25.2 |
| NASDAQ | 23.5 / 25.9 | 14.3 / 13.6 | 12.8 / 12.9 | 15.3 / 14.4 | 34.1 / 33.1 | 28.8 / 31.2 | 16.0 / 15.1 | 13.4 / 13.1 | 16.6 / 14.1 | 25.2 / 26.4 |
| EURUSD 02-26 | 27.0 / 29.1 | 13.3 / 13.7 | 13.8 / 12.9 | 18.2 / 14.8 | 27.7 / 29.5 | 29.8 / 31.5 | 13.2 / 13.9 | 12.4 / 12.7 | 14.6 / 14.0 | 30.0 / 27.9 |

- **BTC** (7-day UTC week): Mon high 26.9 / 21.2, low 35.1 / 29.0; Sat low 5.7 / 11.1; Sun high 17.7 / 26.0. Weekend days are quiet (Sat/Sun range 0.30-0.33 AWR vs 0.41-0.44 on weekdays).
- Arcsine baseline (ict_time E15): Mon 29.5, Tue 14.1, Wed 12.8, Thu 14.1, Fri 29.5.
- "Weekly low by Tuesday in up weeks": 71.9% (SPX), 73.5% (NASDAQ), 75.2% (EURUSD) vs shuffle null 76.0 / 76.9 / 76.5%. Not above chance.
- **Weekday range factor** (mean daily range / AWR): Mon 0.38-0.40 vs Thu 0.41-0.46. Monday is 5-15% quieter. That is a variance factor (TIME-3 `clkD`), not a direction.
- **W2/W3: PWH/PWL during the week** (real / week-bootstrap null):

  | Market | P(PWH) | P(PWL) | both | none |
  |---|---|---|---|---|
  | SPX | 58.2 / 55.5 | 44.7 / 45.3 | 11.4 / 13.0 | 8.5 / 12.2 |
  | NASDAQ | 58.1 / 55.7 | 46.3 / 45.6 | 12.1 / 12.9 | 7.8 / 11.6 |
  | EURUSD | 49.6 / 52.0 | 48.6 / 48.5 | 9.5 / 11.2 | 11.3 / 10.8 |
  | BTC | 53.5 / 54.1 | 38.0 / 40.3 | 8.6 / 13.6 | 17.0 / 19.3 |

  - Cumulative P(PWH by the end of each weekday), SPX: Mon 30.0/31.9 → Fri 58.2/55.5. This is geometry.
- **W5: Monday range** taken later in the week: high 73-77%, low 65-71%, both 40-48%; within ±5 pp of the null, mixed sign.
- **External:**
  - Aldous (via ict_time E15): the timing of the S&P maximum in 20-day blocks matches a random walk.
  - [B] No published multi-year statistic for "Tuesday/Wednesday forms the weekly extreme" was found. TradingView scripts compute it; their authors themselves note the start/end-of-week overweighting (*snippets*).

### 2.9 Gaps [A✓B]

Fill vs mirror, difference in pp [A]:

| Dataset | n | window | fill | mirror | diff | by size |
|---|---|---|---|---|---|---|
| Index futures RTH gap, ES/NQ/YM/RTY 2026 | 204 | same RTH | 0.593 | 0.525 | **+6.9** | 0.5-1 ADR +12.8; > 1 ADR +21 (n = 19) |
| EURUSD weekend 2002-26 | 641 (48% of weeks have no gap) | Monday | 0.732 | 0.730 | +0.2 | 0.25-0.5 ADR +17.5 (n = 80); < 0.1 ADR −5.6 |
| EURUSD weekend | 641 | 5 days | 0.874 | 0.875 | −0.2 | |
| BTC "CME gap" 2017-24 | 415 (median gap 0.28 ADR) | 24 h | 0.557 | 0.614 | −5.8 | > 1 ADR: 8.7 vs 30.4 |
| BTC "CME gap" | 415 | 4 weeks | **0.867** | **0.894** | −2.7 | > 1 ADR: 43.5 vs 78.3 |

- The S&P 500 cash daily gap test is invalid: the cash index's "open" prints before most components trade, which inflates continuation.
- **Academic** [A + B-NEW]:
  - Plastun, Sibande, Gupta & Wohar (2020, *NAJEF*; US indices 1928-2018): prices move in the gap's direction on the gap day, "contrary to the myth that price gaps tend to get filled"; the momentum is temporary.
  - [B] Caporale & Plastun (2017, *Investment Analysts Journal* 46(4):279-293; stocks, FX and commodities 2000-15): gap behaviour is mostly consistent with efficiency; FX is the exception, with an exploitable gap anomaly.
  - [B] **Fung, Mok & Lam (2000)**, *J. Banking & Finance* 24(7):1179-1201: intraday reversals after large **opening** price changes in S&P 500 and Hang Seng futures. Reversal size tracks the opening move; profits after costs are modest.
  - [B] **Grant, Wolf & Yu (2005)**, *J. Banking & Finance* 29(5):1311-1327: S&P futures, Nov 1987-Sep 2002. Significant intraday reversals after large opening changes, stronger after large up-opens, also by year and weekday. Significance drops sharply after bid-ask costs.
  - [B] **Mesfin (2026)**, arXiv 2605.04004 (MNQ, 947 RTH days, 2021-25; independent preprint):

    | Rule | Result |
    |---|---|
    | Gap-fill fade at 09:30 / 09:45 / 10:00 | T = −0.44 / −0.32 / −0.59, win rate 47-48% |
    | Gap continuation short with a velocity filter | T = 3.23, but only N = 22 |

- **Practitioner:**
  - ES fill probability 92% for small gaps → 18% for gaps > 30 points (NexusFi chart, *snippet*). Size dependence = distance.
  - TradeFlightPlan 2009 (slopeofhope): the best fill results for gaps ≤ 5-6 ES points.
  - BTC CME gaps "~95% eventually filled" (NewsBTC 2019, *snippet*), median time to fill 36 h → 19 h (CryptoSlate, *snippet*). None of these compares against a distance-matched level.
- **Reading:**
  - BTC weekend and FX weekend gaps show no magnet beyond distance.
  - Index futures show a small opening-reversal tendency. It is documented in 1987-2002 data and was +6.9 pp in A's 204 gaps of 2026. A recent 5-year MNQ test cannot trade it after costs.
  - Treat the RTH gap level as an ordinary level graded by the ledger (ICTPD-6). No fixed prior.

### 2.10 ORB / IB / NR7 / inside day [A✓B]

| # | Claim | Source | Numbers | Grade |
|---|---|---|---|---|
| O1 | London opening-range breakout follow-through | fxbacktest via ict_time E8, 26 instruments, 92,947 breaks | follow-through of 1 range 50.3% (47.6-52.5%) | moderate (a coin flip) |
| O2 | ORB on MNQ, walk-forward | arXiv 2605.04004 | [B re-read] 09:30-09:55 range; long b+15 T = 1.50, b+1 T = 1.17; short T −1.33 / −0.04; pullback entry stopped out 80.7% (T −1.27); year-unstable | moderate (negative) |
| O3 | IB breaks | tradingstats via amt_profile, ES/NQ 2015-25 | ≥ 1 IB break 97.8% / 96.2%; median extension 63.6% / 55.6% of IB | moderate (descriptive) |
| O4 | IB vs a clock random walk | ict_time §2.2 (YM edgeful) | double break 20% vs 36.8% random | weak (n ≈ 125) |
| O5 | IB extremes as targets | amt_profile §0 | hit at the random-level rate once the clock is matched | moderate |
| O6 | NR7 / inside → expansion | bias_dol §2.8 | next range > 20-bar median: 0.26-0.45 vs base 0.48-0.50 (contraction persists) | moderate |
| O7 | Crabel ORB / stretch / NR tables | Crabel 1990 (book) | definition verified (§1.9); no numbers retrievable | none retrieved |
| O8 | Intraday momentum | Gao, Han, Li & Zhou 2018 *JFE* | first half-hour → last half-hour R² 1.6% (SPY) | strong (small effect) |
| O9 [B] | ORB on crude oil futures | Holmberg, Lönnbark & Lundström 2013, *Finance Research Letters* 10(1):27-33 | 1983-2011; significantly profitable, mostly in the last decade (secondary description) | moderate (positive; one market) |
| O10 [B] | Volatility-volume-gap day classifier | Mesfin 2026, arXiv 2605.11423 | 4.4% of MNQ days; 77.6% reverse from the intraday peak before the close; no directional rule survives | weak |

**Reading.** ORB direction is a coin flip in recent index data (one older positive result in crude oil). IB breaks are near-certain (geometry). Contraction does not predict expansion. The only robust use of the opening range is as a **unit**: the Crabel stretch ≈ the counter-move from the open, median 0.17-0.22 ADR.

### 2.11 [B-NEW] Out-of-period replication: EURUSD 2022-10 → 2023-10

The aim was to check whether A's conclusions are artefacts of A's datasets. Method: A's `daystats.py` and `afterbreak.py`, unchanged, on new data (`b_replicate.py`, NREP = 30).

| Statistic | A, EURUSD 2017-18 | B, EURUSD 2022-23 | Verdict |
|---|---|---|---|
| P(PDH) / P(PDL), real − null | −0.4 / −2.9 pp | −2.1 / −1.1 pp | geometry ✓ |
| Both PD sides, real − null | −2.5 | −1.4 | small "one side" lean ✓ |
| HOD/LOD session, max abs(real − null) | 2.4 pp | 1.2 pp | clock ✓ |
| Asia 20-00 both, real − null | +1.1 | −1.2 | geometry ✓ |
| NY AM both, real − null | −2.5 | −3.6 | one-sided afternoon ✓ |
| Day-end hazard, overall real / null | (A: pooled tables match) | 0.283 / 0.287 | clock ✓ |
| Exhaustion at ≥ 1.3 ADR used (x = 0.25) | +3.7 | +2.9 | clustering sign ✓ |
| After-break PD / London | −2.0 / −6.5 | **+1.9 / +2.1** | **sign flips → noise** |
| Lag-1 range corr | 0.00 | 0.09 | FX persistence weak ✓ |

### 2.12 [B-NEW] Day-clustered pooling of the after-break residuals

See the table in §2.4. Method:
- Per-row residual y − p_null, summed per calendar day across ES/NQ/YM/RTY.
- Day-block bootstrap (4,000 draws).
- 781-989 rows on 230-250 days per range.

Result: only the Asia range reaches |z| = 2.0, and five ranges were tested. Grade **weak**.

### 2.13 [B-NEW] Where does day state belong? Double counting and estimator choice

**Test 1: today factor on the engine's trailing σ** (`b_hz1h.py`, `b_hz5m.py`). Day-end forecasts of untaken PDH/PDL; recalibrated Brier; F50 = σ of the last 50 bar-to-bar close changes × bars left.

| Data | F50 | F50 × f | F50 × fs |
|---|---|---|---|
| 1h IDX (26,137) | 0.1508 | 0.1541 (**+2.2%**) | 0.1512 (+0.3%) |
| 1h CL | 0.1373 | 0.1440 (**+4.9%**) | 0.1387 (+1.0%) |
| 1h EURUSD 17-18 | 0.1342 | 0.1407 (**+4.8%**) | 0.1361 (+1.4%) |
| 1h BTC | 0.1284 | 0.1326 (**+3.3%**) | 0.1297 (+1.0%) |
| 5m IDX (9,223; 148 day-groups) | 0.1606 | 0.1680 (**+4.6%**, CI +1.8 to +7.5%) | 0.1622 (+1.0%, n.s.) |
| 5m CL (37 days) | 0.1321 | 0.1254 (−5.1%, n.s.) | 0.1277 (−3.4%) |
| 5m GC (25 days) | 0.1344 | 0.1407 (+4.7%, n.s.) | 0.1370 (+1.9%) |

→ **A's SESS-1 spec, which applies fDay wherever `potSig` feeds a probability, degrades PoT in 6 of 7 cells.** The same logic applies to the ATR-normalised empirical surface, because ATR(14) is also a trailing state.

**Test 2: which level for the clock** (`b_hz2.py`). C = ADR² × remaining clock variance.

| Model | Definition |
|---|---|
| Cf | C × f |
| Cfs | C × shrunk f |
| CL50 | C × the fast deseasonalised level (TIME-3 `clkLf` form: EWMA span 50 of bar GK / expected slot GK) |
| CL50f | C × sqrt(CL50 level × f) |

Recalibrated Brier:

| Horizon / data | F50 | C | Cf | Cfs | CL50 | CL50f | Key contrasts (day-block 95% CI) |
|---|---|---|---|---|---|---|---|
| Day end, 5m IDX | .1606 | .1436 | **.1386** | .1401 | .1496 | .1429 | Cf − CL50 −7.4% [−11.5, −3.4]; CL50f − CL50 −4.5% |
| Day end, 5m CL | .1321 | .1640 | .1485 | .1579 | **.1240** | .1351 | Cf − CL50 +19.8% [+6.1, +32.3] |
| Day end, 1h IDX (25,484) | .1561 | .1517 | .1484 | .1491 | .1474 | **.1464** | Cf − CL50 +0.6% (n.s.); CL50 − F50 −5.6% |
| Day end, 1h CL | .1396 | .1402 | .1373 | .1374 | .1400 | **.1373** | all within ±2% (n.s.) |
| H = 30 bars, 5m IDX (51,840) | .1812 | .1733 | .1670 | .1694 | **.1630** | .1634 | Cf − CL50 +2.5% [+1.4, +3.6]; CL50 − F50 −10.1% |
| H = 30 bars, 5m CL | .1775 | .2081 | .1930 | .1995 | **.1739** | .1821 | Cf − CL50 +11.0% |
| H = 12 bars, 1h IDX (148,544) | .1699 | .1596 | .1576 | .1574 | .1559 | **.1553** | Cf − CL50 +1.1% [+0.5, +1.7]; CL50 − F50 −8.2% |
| H = 12 bars, 1h CL | .1646 | .1644 | .1617 | .1613 | .1603 | **.1595** | |

The H-bar rows use generic levels at 0.5, 1, 1.5 and 2 × σ50·√H above and below price, so F50 is not disadvantaged.

**Reading:**
1. For the engine's **main H-bar PoT**, a clock with a fast deseasonalised level (TIME-3) beats the trailing σ by 2-10%. The today factor adds nothing on top (0 to +11% worse).
2. For **day-end horizons** the today factor is the better level on index futures at 5m (−7.4%). It fails when the ADR level is off (5m CL in early 2026, mean p 0.33 vs y 0.17). A geometric blend is never the worst and is within 3-9% of the best everywhere.
3. The engine's current trailing σ is the worst model in every index cell (5-14% behind).
4. The CL 5m sample is 36-37 days; treat its large numbers as "level shift sensitivity", not as a precise effect.

### 2.14 [B-NEW] Does a learned key-level surface help? (Prequential)

Setup (`b_surface.py`):
- Snapshots of untaken PDH/PDL at the first slot of each of 8 equal day buckets, so each level-day enters a cell once.
- Analytic pA = Cfs.
- Learners are updated only after each day ends; m = 20 pseudo-observations.
  - G: one global logit offset;
  - TS: offsets per (time bucket × sibling-taken), shrunk to G;
  - TSD: TS × 4 distance bins, shrunk to TS.

| Symbol (snapshots; ~level-days) | raw | G vs raw | TS vs G | TSD vs TS |
|---|---|---|---|---|
| ES (2,432; 424) | 0.1557 | +0.7% | +0.5% | +0.1% |
| NQ (2,434; 424) | 0.1637 | +0.9% | +0.6% | −0.1% |
| YM (2,513; 424) | 0.1422 | −0.1% | −0.1% | +1.1% |
| RTY (2,531; 424) | 0.1507 | +0.7% | +0.4% | +0.9% |
| CL (1,657; 284) | 0.1404 | +0.4% | +0.1% | +0.6% |
| BTC (33,401; 5,742) | 0.1501 | **−9.0%** | −0.3% | −0.0% |

**Sibling effect under the calibrated model** (y vs pA when the opposite PD side was already taken):

| | ES | NQ | YM | RTY | CL | BTC |
|---|---|---|---|---|---|---|
| sib = 1: y / pA | 0.149 / 0.129 | 0.133 / 0.122 | 0.122 / 0.098 | 0.119 / 0.100 | 0.075 / 0.111 | 0.100 / 0.165 |
| sib = 0: y / pA | 0.422 / 0.415 | 0.427 / 0.411 | 0.436 / 0.410 | 0.394 / 0.409 | 0.374 / 0.383 | 0.315 / 0.429 |

There is no consistent "discount the sibling" residual. On indices the sibling is, if anything, slightly **under**-predicted.

**Reading:**
- A per-chart surface costs Brier on ~1 year of 1h data. On 5m (~17 days per 5,000 bars) it cannot fill at all.
- One gated global offset is enough, and it matters only where the analytic level is biased (crypto).

### 2.15 [B-NEW] Distance units: what the engine's ATR settings mean in ADR

`b_units.py`, six CME futures, median over bars:

| Chart | ATR14 / ADR14 | `maxATR` 10 = | eject 15 ATR = | `potH` 30 bars = |
|---|---|---|---|---|
| 1m | 0.016-0.020 | 0.16-0.20 ADR | 0.24-0.31 ADR | 0.5 h |
| 5m | 0.041-0.050 | 0.41-0.50 ADR | 0.62-0.75 ADR | 2.5 h |
| 15m | 0.079-0.090 | 0.79-0.90 ADR | 1.18-1.35 ADR | 7.5 h |
| 1h | 0.167-0.186 | 1.67-1.86 ADR | 2.50-2.79 ADR | 30 h |

- With the default "Day Trading" mode on a 5m chart:
  - PDH/PDL beyond ~0.45 ADR get proximity 0 (`evaluate`, 661-667);
  - they are ejected beyond ~0.7 ADR (1578);
  - they re-enter only within 10 slow-ATR (1834).
- Yet from Asia a PDH 0.5-0.75 ADR away is taken today 29-30% of the time (§2.5). The key-level feature is therefore invisible on 1-5m charts except near price, and "the DOL" means a different radius on every timeframe.
- B's interpretation: this is a design choice, not a bug (an intraday target universe can be local). But it means key-level odds must be shown **independently of the pool** (SESS-1), and users should see distances in ADR (SESS-5).

### 2.16 Evidence grading summary (combined)

| Claim | Grade | Change |
|---|---|---|
| PD/PW/session take rates = geometry + clock (±3 pp) | **strong** for the null conclusion (8 datasets, two researchers, replicated out of period; Mok-Lam-Li agree on timing for S&P); moderate for the exact numbers | A moderate → B strong (conclusion) |
| Session of the HOD/LOD = clock + arcsine | moderate (market-specific open-burst deviations in HSI, FTSE, CAC) | kept |
| Weekday of the weekly extreme = arcsine; no weekday prior | strong | kept |
| Opposite side after the first break (any range) | **weak** | A moderate → weak |
| NY AM "one-sided afternoon" | weak-moderate (8/8 sign, small) | new split |
| ADR exhaustion false; extension rises with range used | moderate | kept, replicated |
| ADR profile = BM + stochastic volatility; σ_day ≈ ADR/1.55 | strong (theory + 10 datasets) | B-NEW |
| Time-of-day hazard of key levels (horizon effect) | strong for the shape (clock theory, replicated); moderate for the numbers | upgraded |
| Today factor on the trailing σ | **none / harmful** (+2 to +5% Brier) | B-NEW, corrects A |
| Day state as the level of a clock model, day-end horizon | moderate (helps on indices, unstable on CL; gate it) | A moderate, re-scoped |
| Learned per-chart key-level surface | **none** (prequential: no gain) | A moderate → none |
| Gap "must fill" | none (FX/BTC); weak for a small index opening reversal | refined |
| ORB direction / NR7 expansion | moderate (negative) | kept |

---

## 3. Engine gap analysis (baseline_v2.pine, re-checked by B)

| ID | Concept | Status | Lines | What the engine does / what differs |
|---|---|---|---|---|
| S1 | PDH/PDL as targets | **present** | 104, 807-832 (`f_rangeTrack`), 945, 952-958, 1790-1794 | Exchange-day extremes, anchored to the print bar, pushed with tier 0.80 (`f_tierW` 506-515) and a √(86400/chartS) freshness clock (1792). The source is correct. Its *probability* uses the fixed-H PoT (`f_potModel` 1303-1311) with no day-end horizon and no ADR unit [A✓B] |
| S2 | PWH/PWL | **present** | 105, 946, 959-961, 1795-1799 | Tier 0.92. Same caveat: no week-end horizon [A✓B] |
| S3 | Asia / London / NY AM session ranges | **partial** | 106-109, 835-863 (`f_sessTrack`), 947-950, 1800-1809 | Pushed at session end with tiers 0.55/0.60/0.60, only on ≤ 1h charts (`intraOK`, 947). The NY AM window is misaligned on 1h (bar-open `time()` test; wrong extreme on 76% of days, ict_time §1.2). No ON range (TIME-7) [A✓B] |
| S4 | Session in which levels get taken; HOD/LOD session | **wrong** (fixed prior) | 596-602 (`f_kzAff`), 1941 | London ×1.20 for Asia pools; NY AM ×1.20 for London and ×1.15 for PD; NY PM ×1.15 for NY AM. First-take session, HOD/LOD session and session raids equal the clock/geometry null within ±2.5-3 pp; the prequential sibling/time-bucket test found no learnable residual (§2.14). The multipliers add selection bias and fake ledger EDGE by timing (ict_time G16) [A✓B] |
| S5 | Source tier as a hit-probability prior | **partial / unsupported** | 506-515; 682 (`1.2 * this.tier()` in density); 1582 (`liqEvt` weight); 1813-1823 (registry eviction); 2053 | PD/PW/session pools get large density boosts (PW 0.92 vs chart 0.25). Their take rates equal distance-matched random paths. A tier can mean "importance" (eviction order, display), but should not raise probability [A✓B] |
| S6 | ADR / day range as a unit | **missing** | none (`maxATR` 129, eject 1521/1578 and re-entry 1834 are in chart ATR) | No ADR anywhere. In ADR terms the candidate radius is 0.16-0.20 ADR on 1m, 0.41-0.50 on 5m and 1.7-1.9 on 1h (§2.15) [A; B quantified] |
| S7 | ADR exhaustion / "ADR remaining" cap | **missing (correctly)** | none | Must stay missing: refuted (§2.7) [A✓B] |
| S8 | Day-state variance | **partial** | 914-917 (`potSig`, `potMu`), 665, 1303-1322, 1360-1363 | [A, CORRECTED by B] A called it missing. On ≤ 15m charts the 50-bar trailing σ already spans most of the active day, so it **contains** day state. Adding a today factor to it double counts (+2-5% Brier, §2.13). What is missing is a clock (TIME-3) with an adaptive level, and for day-end horizons an ADR × day-state level |
| S9 | Horizon to session / day / week end | **missing** | 183/305 (`H = potH`), 1303-1311, 1453-1456 (`t.bars >= H` at 1455) | Fixed H bars: 2.5 h on 5m, 30 h on 1h. "PoT today" for PDH at 14:00 ET cannot be expressed. TIME-6 / QPOT-06 add the analytic horizon; SESS-1 adds key-level day/week odds [A✓B] |
| S10 | Opposite side after a range break | **missing (correctly)** | 1575-1585 (`liqEvt` → D only) | [A, CORRECTED by B] A proposed learning it. Day-clustered evidence is weak (§2.4/2.12), and under a calibrated model there is no residual (§2.14). No change needed |
| S11 | Weekday of weekly extremes, weekly profiles | **missing (correctly)** | none | Arcsine. Only a weekday variance factor is real (TIME-3 `clkD`) [A✓B] |
| S12 | Opening / weekend gaps | **missing** | none (ICTPD-6 proposes) | No magnet beyond distance in FX/BTC; a small opening reversal in index futures (literature, 1987-2002; A +6.9 pp, n = 204; MNQ 2021-25 not tradable). If ICTPD-6 lands: no gap prior [A✓B] |
| S13 | Ledger granularity for key levels | **partial** | 635-637 (`grp`), 1376-1384 (`f_calMult`), 1426-1499 | All external liquidity is grp 1. calib_ml shows per-family learning on the selected-target ledger cannot work (family SEs 3-5 pp > lifts; bandit feedback). Per-family numbers belong in a display or a candidate (shadow) ledger with EB shrinkage (CAL-1/CAL-3), not in a multiplier [A, CORRECTED by B] |
| S14 | Empirical PoT surface conditioning | **partial** | 1059-1062, 1284-1300, 1527-1532 | ATR-normalised H-bar excursions split by HTF bias, pooled over hours. TIME-2/TIME-3/REG-1 add the clock and the state. A's "look up at dAtr/√fDay" is dropped (double counting, S8) [A, CORRECTED by B] |
| S15 | Day boundary | **present (exchange day)** | 945 | `timeframe.change("D")`: CME 18:00 ET, FX 17:00 ET, crypto 00:00 UTC. Consistent per symbol; no "NY midnight" option (SESS-6) [A✓B] |
| S16 | ORB / IB as sources | **missing (correctly)** | none | The NY AM range covers the morning; the IB is in AMT-2's candidate ledger [A✓B] |
| S17 | NR7 / inside-day expansion prior | **missing (correctly)** | none | Contraction persists (O6) [A✓B] |
| S18 | Week state for PW levels | **missing** | 946, 1795-1799 | PW levels use the same H-bar PoT. Covered by SESS-1's week horizon [A✓B] |
| **S19** | **Stale key-level labels and tiers** | **wrong** | 518-521 (`f_levelName`), 1211-1223 (`f_pushExt`: only upgrades `src`), 1127-1128 (`f_mergeAt`), 1833-1852 (registry → pool) | [B-NEW] An untaken PDH pushed yesterday keeps `src = 6` ("PDH", tier 0.80, `f_kzAff`) after the next day starts, until it is swept or evicted (registry cap 60, 1813). The same holds for PW (7) and sessions (3-5). The engine can label a three-day-old high "PDH" while the real PDH (`aPDH`, 957) is elsewhere. SESS-2 |
| **S20** | **Key levels on low timeframes** | **partial** | 129, 663-667, 1521, 1578, 1834 | [B-NEW] On 1-5m charts key levels beyond 0.2-0.5 ADR are out of the pool. Nothing shows their odds. SESS-1 shows them independently of the pool; SESS-5 offers an ADR radius |
| **S21** | **Panel capacity** | constraint | 2291 (`table.new(..., 4, 22, ...)`) | [B-NEW] The Terminal panel is fixed at 22 rows. SESS-1/SESS-4 rows must fit, or raise the row count |
| S22 | Daily/weekly charts | **wrong** (known overhaul P1) | 945-946 | On a D chart `timeframe.change("D")` fires every bar, so every candle becomes a PDH/PDL pool. On a W chart the same happens for PW. Key-level day logic must be gated by `timeframe.isintraday` (and W logic by < W) [B cross-ref] |

---

## 4. Proposals (best first)

Ground rules:
- Every proposal is non-repainting:
  - requests use `[1]` with `lookahead_on`;
  - state updates happen on confirmed bars;
  - live readouts are labelled live, like the PoT.
- Every proposal is measured, and neutral by default where the evidence is small.
- They build on, and do not duplicate:
  - TIME-3 / QPOT-05: the clock and forward variance;
  - TIME-6 / QPOT-06: session-end PoT and ETA;
  - TIME-4 / QPOT-04 / CAL-6: scorecard and calibration gates;
  - TIME-5: the affinity switch;
  - TIME-7: ONH/ONL;
  - ICTPD-6: gaps;
  - CAL-1 / CAL-3: family statistics.

### SESS-1 (P1, effort M) · Key-level PoT to day end and week end ("Today %", "This week %"), from the clock with a day-state level and one gated calibration offset [A's SESS-1 + SESS-2 + SESS-5, CORRECTED and merged by B]

**Why.**
- Traders ask "will PDH go today?". The answer depends as much on the clock as on distance: 64% → 57% → 47% → 19% (indices) and 62% → 57% → 47% → 7% (EURUSD 22-23), from Asia to NY PM, at 0.2-0.35 ADR.
- The fixed-H PoT (183/305) cannot say it, and on 1-5m charts the levels are not even in the pool (§2.15).
- Among causal models for this question (§2.6, §2.13):
  - the clock with an adaptive level is best (1h IDX: −5.0 to −6.2% vs a trailing σ with the same horizon; 5m IDX: −11 to −14%);
  - an ADR × day-state level adds value on index futures at 5m (−7.4% vs the fast level);
  - a geometric blend is the robust choice.
- A learned cell surface adds nothing (§2.14). One calibration offset fixes crypto's level bias (BTC −9%).

**What changed vs A.**
- Day state is **not** applied to `potSig` or the ATR surface (that raised Brier +2-5%, §2.13).
- There is no 432-cell surface; it was 0.1-1.1% worse prequentially.
- ADR comes from a non-repainting daily request, not the chart's own day tracker. On a 5,000-bar 5m chart (~17 days) EWMA curves with α = 0.05 never warm up.
- The expected range-so-far curve comes from the clock (Brownian scaling, error ≤ 0.026 ADR on ES/NQ/BTC).
- PW odds are folded in (A's SESS-5).

**Inputs** (G_KEY, `display = display.none` as for other new inputs):
```
bool useKeyPoT = input.bool(true, "Key-Level Odds (Today / This Week)", group = G_KEY, display = display.none,
  tooltip = "Chance that PDH/PDL, PWH/PWL and today's session highs/lows trade through before the day (week) ends. It uses this symbol's time-of-day volatility and how active today has been. A used-up ADR never caps a level: busy days keep extending.")
int  adrLen    = input.int(14, "ADR Length (days)", minval = 5, maxval = 30, group = G_KEY, display = display.none)
```

**Series** (after 950; intraday only). Two new requests; the budget is fine (about 6 in use, limit 40):
```
float dADR = request.security(syminfo.tickerid, f_tfSafe("D"), ta.sma(high - low, adrLen)[1], lookahead = barmerge.lookahead_on)
float wAWR = request.security(syminfo.tickerid, f_tfSafe("W"), ta.sma(high - low, 10)[1], lookahead = barmerge.lookahead_on)
bool  kOK  = useKeyPoT and timeframe.isintraday and nz(dADR) > 0
```
- `f_tfSafe` (564) never requests below the chart timeframe.
- `[1]` with `lookahead_on` is the engine's verified non-repainting pattern.

**Clock and level.**
- **(a) With TIME-3 present:** `V_T3` = TIME-3/TIME-6's forward variance from now to `time_close("D")` (time.md l.378: `time_close(timeframe)` returns the close of the current daily bar), in price² units: `close² · fwdVar`. The share of the day's clock still to come is `rest = Σ remaining clkA·clkD ÷ Σ day clkA·clkD`; it comes from the same walk.
- **(b) Standalone fallback**, if TIME-3 is not built. A 30-minute NY-clock bucket array of Garman-Klass variance in ADR² units:
  ```
  int   bkK  = math.max(30, int(chartS / 60))
  int   NKB  = int(math.ceil(1440.0 / bkK))
  var array<float> kvB = array.new<float>(NKB, na)    // EWMA expected GK variance per bucket (ADR² units)
  var array<float> kvT = array.new<float>(NKB, 0.0)   // today's sums
  var float kHi = na
  var float kLo = na
  int   kb  = int((hour(time, tz) * 60 + minute(time, tz)) / bkK)
  float gkV = math.max(0.0, 0.5 * math.pow(high - low, 2) - (2.0 * math.log(2.0) - 1.0) * math.pow(close - open, 2))
  if kOK and timeframe.change("D")
      for j = 0 to NKB - 1
          float x = kvT.get(j)
          if x > 0
              float o = kvB.get(j)
              kvB.set(j, na(o) ? x : o + 0.1 * (x - o))
          kvT.set(j, 0.0)
      kHi := high
      kLo := low
  else
      kHi := math.max(nz(kHi, high), high)
      kLo := math.min(nz(kLo, low), low)
  if kOK and barstate.isconfirmed
      kvT.set(kb, kvT.get(kb) + gkV / (dADR * dADR))
  ```
  - `rest` = (Σ of `kvB` over the buckets from `kb` to the bucket of `time_close("D")`, plus the unfinished fraction of bucket `kb`) ÷ (Σ of all non-na `kvB`). It is one forward walk of ≤ NKB = 48 iterations per bar at global scope, never per level.
  - `vDay = Σ non-na kvB` (≈ 0.42 on a normal day).
  - `V_ADR0 = dADR² · vDay · rest`.
  - `kHi`/`kLo` update on every tick: the live readout is live by design, and `var` state rolls back on unconfirmed bars.
- **Day state** (Brownian scaling, so no extra learned curve):
  ```
  float done = math.max(0.02, 1.0 - rest)
  float fRaw = ((kHi - kLo) / dADR) / math.sqrt(done)     // E[day range]/ADR ≈ 1.00-1.08
  float fD   = 1.0 + math.sqrt(done) * (f_clamp(fRaw, 0.5, 2.5) - 1.0)   // shrunk early in the day
  float V_ADR = V_ADR0 * fD
  float Vday  = na(V_T3) ? V_ADR : math.sqrt(V_T3 * V_ADR)               // geometric blend (CL50f)
  ```
- **Week:** `Vwk = Vday + nLeft · dADR² · vDay`.
  - `nLeft = math.max(0, math.round((time_close("W") - time_close("D")) / 86400000.0))`.
  - Crypto weekends are quieter (0.30-0.33 vs 0.41-0.44 AWR), so scale Saturday and Sunday by 0.75 when `syminfo.type == "crypto"`.
  - Also show `wAWR` in the readout.

**Probability per tracked level** (O(1) each):
```
pK = d <= 0 ? 1.0 : math.min(0.95, f_erfc(d / math.sqrt(2.0 * V)))
```
- `f_erfc` is at 411. Driftless, as in QPOT-01.
- d = distance from `close` to the level; V = `Vday` (today) or `Vwk` (this week).

**Tracked levels** (fixed slots, ≤ 10; independent of the pool and the eject distance):
- slots 0-1: `aPDH`/`aPDL` (day horizon);
- slots 2-3: `aPWH`/`aPWL` (day and week horizons);
- slots 4-9: today's finished Asia/London/NY AM H/L, captured at `asEnd`/`lnEnd`/`nyEnd` (948-950) and cleared at the day rollover;
- ONH/ONL if TIME-7 lands.

Per slot, keep `kTk` = the bar of the first strict through-trade today (−1 if none). It updates on confirmed bars with the `touched` rule (strict `>`/`<`).

**Calibration** (one offset per chart and horizon type, prequential, gated):
- **Snapshots:** when `tb = int(8·done)` changes, on a confirmed bar, push `(slot, pK)` for every untaken slot. That is ≤ 8 × 10 per day, so each level-day enters each time bucket once (A's spec snapshotted every 30-minute bucket and counted overlapping rows as independent).
- **Resolution** at the day rollover: `y = kTk ≥ 0`. Then:
  - `N += 1`, `K += y`, `E += pK`;
  - `Br0 += (pK − y)²`, `Br1 += (pCal − y)²`, where `pCal` was computed at snapshot time with the offset then in force.
- **Offset:** `δ = f_logit((K + 20·E/N)/(N + 20)) − f_logit(E/N)` (`f_logit` 484). Apply `pCal = f_sigm(f_logit(pK) + δ)` (`f_sigm` 488) only when ≥ 30 resolved days **and** `Br1 < Br0`. That is the QPOT-04 prequential gate.
- State: 5 floats per horizon plus ≤ 80 snapshot pairs.

**Display:**
- **Terminal** panel, one row (mind the 22-row table at 2291; raise it to 24 if needed):
  ```
  KEY  PDH 38% · PDL 9% · ASIA H ✓ · LDN L 41%  |  WK PWH 22% · PWL 6%
  ```
  ✓ = already taken today. The row is dimmed when the calibration gate is off.
- **Clean:** when the active DOL is a key level (src 3-8), the label tooltip adds `Today 38% · This week 61%`. The Clean face stays two lines, as in the reference screenshot.
- With TIME-6's `potHor = "Day End"`, key-level targets use `pCal` as the headline PoT, and trials store `hT` (TIME-6's ledger rule at 1455).

**Ledger / measurement.**
- The Brier pair `Br0`/`Br1` and N are shown in the Full accuracy view: `KEY TODAY Brier .142 → .139 (n 412 d)`.
- TIME-4's scorecard can also compare `Vday` against `V_T3` alone and against `V_ADR` alone on these snapshots, and pick per chart.

**Guards** (state them in the tooltip and the README):
- Never multiply `potSig`, the ATR surface or reach by `fD`.
- Never cap, eject or penalise a level because "the ADR is used up".

**Pine v6 feasibility.** Arrays ≤ 48 floats, one ≤ 48-iteration walk per bar, ≤ 80 snapshots a day, two requests. No drawing objects (table cells only). No forward references if the block sits after the key-liquidity trackers (after 950-961) and after TIME-3's state, when present.

**Evidence:** moderate. The horizon effect is strong and replicated (§2.5, §2.11). The model ranking is moderate (§2.6, §2.13, with day-block CIs). The calibration conclusion is moderate (§2.14).

**Risk:**
- Holidays and early closes: `time_close("D")` follows the regular session, so the odds are a little high on half days (label it "≈").
- The CL-type level shifts are why the blend and the calibration gate exist.
- Crypto week boundaries follow the symbol's weekly bar.

### SESS-2 (P2, effort S) · Demote stale key-level labels and tiers when a new day, week or session starts [B-NEW]

**Why.** S19: yesterday's untaken PDH stays `src = 6` ("PDH", tier 0.80, f_kzAff) indefinitely. Labels such as "Target: PDH" can then point to a level that is not the previous day's high, which a trader will notice at once. This is correctness, not edge.

**Spec:**
- New source codes:
  - 9 = older day extreme ("OLD PDH" / "OLD PDL");
  - 10 = older week extreme ("OLD PWH" / "OLD PWL");
  - 11 = older session extreme ("OLD ASIA H" style is too long, so use "OLD SESS H" / "OLD SESS L").
- Add them to `f_levelName` (518-521), `f_shortName` (532), the src comment (316) and `f_tierW` (506-515):
  - 9 → 0.65, 10 → 0.75, 11 → 0.40;
  - these are importance only: no evidence favours any tier for probability (S5);
  - `f_kzAff` returns 1.0 for them automatically.
- Demotion runs in the engine block, immediately **before** the pushes at 1790/1795/1800:
  ```
  if pdNew or pwNew or asEnd or lnEnd or nyEnd
      for e in extReg
          if pdNew and e.src == 6
              e.src := 9
          else if pwNew and e.src == 7
              e.src := 10
          else if (asEnd and e.src == 3) or (lnEnd and e.src == 4) or (nyEnd and e.src == 5)
              e.src := 11
      for lv in pool
          // the same three tests on lv.src, so pool copies are demoted too
  ```
  - Then the fresh PDH/PDL (etc.) are pushed with their normal src.
  - `f_pushExt`'s duplicate check (1216-1219) re-upgrades an entry whose price equals the new PDH, which is the desired result.
- No UDT change is needed: `src` is a mutable field of both `Ext` and `Level`.

**Measurement.** None needed; it is a labelling fix. The ledger's per-family view (CAL-1/CAL-3) then separates "current" from "old" key levels.

**Evidence:** none for forecasting; it is a correctness fix (verified by code reading).

**Risk:** fewer pools labelled PDH/PWH. Older extremes keep their liquidity role, with a truthful name.

### SESS-3 (P2, effort S) · Session affinity neutral by default; no learned session or sibling multiplier; tier means importance, not probability [A's SESS-3, CORRECTED by B]

**Why.**
- `f_kzAff` (597-602, applied at 1941) hard-codes ×1.05-1.20. First-take timing, HOD/LOD timing and session raids equal the null within ±2.5-3 pp (two independent nulls: A's day bootstrap and ict_time's clock walk), and B's replication agrees (§2.11).
- A's replacement, a learned bounded multiplier `mKey` from the surface's sibling and time cells, has nothing to learn. The prequential cell offsets lost 0.1-1.1% (§2.14). It is dropped; so should be TIME-5's "Learned" option.
- Tiers raise density by up to 1.2 × 0.92 (682) for pools whose take rates are geometry.

**Spec:**
1. Adopt TIME-5's `kzAffMode` with default **"Off"**. Keep "Fixed (legacy)" for users who want the ICT narrative. Remove "Learned", or have it return 1.0 until a real per-chart signal exists.
2. Density (682): replace `1.2 * this.tier()` with `1.2 * (tierMode == "Probability (legacy)" ? this.tier() : 0.25)`, a flat chart-level contribution. Keep the tier for:
   - registry eviction (1818), so far PW/PD pools are kept for re-entry;
   - the display ordering at 2053;
   - a tie-breaker `+ 0.5·tier` points in `lv.score` (≤ 0.5 of 100) so the more important level wins exact ties.
   Coordinate with OF-3 and WYK-1, which touch the same pillar.
3. Per-family numbers for key levels (PD, PW, session, old key) go to CAL-3's candidate ledger with CAL-1's EB shrinkage, **display only**. `f_calMult` stays on its four groups or is replaced as CAL-1 specifies.

**Measurement.** CAL-3's shadow selector: key-level hit rate vs `pBase` per family, with intervals.

**Evidence:** moderate that the fixed affinities and tier probability bonuses are unsupported (two nulls, replication, prequential test). None for any specific session residual.

**Risk.** Fewer "London raids Asia" picks in killzones. That is the honest outcome, and legacy modes keep the old behaviour.

### SESS-4 (P2, effort S) · Key-level "taken" alerts and a day/week context row [A's SESS-4, sharpened by B]

**Why.**
- Traders reason in session terms: "PDH taken? Asia high taken? How much of the ADR is done?". The engine tracks these levels but shows none of the state.
- The alert set (2077-2094) has no key-level event, a frequent request in competitor threads (competitors.final).

**Spec:**
- **Alert.** On a confirmed bar, when a SESS-1 slot's `kTk` turns from −1 to `bar_index`:
  ```
  alert("DOL Engine ▸ " + name + " taken · " + str.tostring(pRemainOpp * 100, "0") + "% for " + oppName + " today · " + syminfo.ticker, alert.freq_once_per_bar_close)
  ```
  - Example message: `PDH taken · PDL today 9% · next BSL PWH 0.6 ADR`.
  - Add `alertcondition(keyTaken, "Key Level Taken", "DOL Engine: a key level (PDH/PDL/PWH/PWL/session) traded through on {{ticker}}")`.
- **Context row** (Terminal):
  ```
  DAY 0.72 ADR · ×1.3 (busy) · PDH ✓ · PDL 12% | WEEK 0.81 AWR
  ```
  "×1.3" is SESS-1's `fD`, worded as "busy" / "normal" / "quiet" for 1.25 / 0.8 thresholds.
- Fit the 22-row panel (2291) or raise it.

**Evidence:** weak as a forecasting gain (UX value). The probabilities shown are SESS-1's and are graded.

**Risk:** clutter; keep it to Terminal style and the tooltip.

### SESS-5 (P3, effort S) · ADR as a unit everywhere a distance is shown, plus an optional ADR distance radius [B-NEW, from A's SESS-6 second half]

**Why.**
- On 1-5m charts the candidate radius is 0.16-0.50 ADR, and on 1h it is 1.7-1.9 ADR (§2.15).
- ATR distances mean nothing across timeframes; ADR distances are what traders compare and what transfers across symbols (σ_day ≈ ADR/1.55).

**Spec:**
- HUD distances `0.42 ADR` beside ATR, using SESS-1's `dADR`.
- Optional `string distUnit = input.string("Chart ATR", "Max Distance Unit", options = ["Chart ATR", "ADR"], group = G_SCORE)` and `float maxADR = input.float(1.0, "Max Distance (ADR)", minval = 0.2, step = 0.1, group = G_SCORE)`.
  - In ADR mode, per bar: `float maxD = kOK ? maxADR * dADR / atr : maxATR`.
  - Pass `maxD` into `evaluate` as a new parameter. Inside a method the global `dADR` would be a forward reference, because `evaluate` is declared at 661 and the request is at ~950.
  - Use `maxD` at the eject (1521/1578) and re-entry (1834) tests.
- Default "Chart ATR" keeps current behaviour.

**Evidence:** moderate for the units (measured); none for which radius is "right".

**Risk:** in ADR mode on 1m charts the pool fills with far levels. That is why it is P3 and off by default.

### SESS-6 (P3, effort S) · Day-boundary choice [A's SESS-6, kept]

**Why.**
- PD levels and SESS-1's day use the exchange day (945): CME 18:00 ET, FX 17:00 ET, crypto 00:00 UTC.
- ICT-style users anchor the crypto day at NY midnight or NY 17:00. Levels and statistics change with the anchor; under the null none is better.

**Spec:**
- `string dayAnchor = input.string("Exchange", "Day Boundary", options = ["Exchange", "NY Midnight", "NY 17:00"], group = G_KEY)`.
- `bool newDay`:
  - "Exchange": `timeframe.change("D")`;
  - "NY Midnight": `dayofmonth(time, tz) != dayofmonth(time[1], tz)`;
  - "NY 17:00": the first bar with `hour(time, tz) >= 17` after a bar with `hour(time[1], tz) < 17`, or a calendar-day change in `tz`.
- Feed `f_rangeTrack(newDay)` (945) and SESS-1's rollover.
- With a non-exchange anchor, SESS-1 must compute ADR from the chart's own day tracker (≥ 5 days), not the daily request.

**Evidence:** none for forecasting; it is definitional.

**Risk.** Changing the anchor changes the levels. The default keeps current behaviour.

### Explicitly not recommended (the evidence says no)

| Idea | Evidence against |
|---|---|
| ADR-remaining cap, "ADR hit → eject targets", ADR projection levels as targets | §2.7: the sign is reversed; extension rises with range used; the ADR profile is BM + stochastic volatility |
| **Today factor on `potSig`, the ATR surface, reach or the race (A's SESS-1 as specified)** | §2.13: +2.2 to +4.9% Brier on 1h, +4.6% on 5m IDX (CI excludes 0); trailing σ already holds the day state |
| **A learned key-level hazard surface (432 cells) or session/sibling multipliers (A's SESS-2/3 `mKey`, TIME-5 "Learned")** | §2.14: 0.1-1.1% worse than one global offset, prequentially; no sibling residual under a calibrated model |
| Fixed session/killzone affinities; "London makes the HOD/LOD" or "NY takes London" priors | §2.2-2.3, §2.11: equal to the null within ±3 pp on 8 datasets |
| "Judas" / after-break opposite-side priors | §2.4, §2.12: z ≤ 2.0, sign flips across periods |
| Weekday priors ("Tuesday low of week", Monday-range rules) | §2.8: arcsine |
| "CME gaps (weekend gaps) must fill" as a level prior | §2.9: fill ≈ mirror; large gaps continue |
| NR7 / inside-day expansion and ORB direction priors | §2.10: contraction persists; ORB ≈ 50%; recent MNQ ORB fails |

---

## 5. Sources

**This study (reproducible)**
- A: `study/session_tools/`. Scripts: `sesslib.py`, `daystats.py`, `afterbreak.py`, `pooled.py`, `hazmodels.py`, `weekly.py`, `gaps.py`, `nullcheck.py`. Outputs: `out_<SYM>_day.txt`, `out_<SYM>_slot.txt`, `out_afterbreak_<SYM>.txt`, `out_pooled_*.txt`, `out_hazmodels.txt`, `out_weekly_*.txt`, `out_gaps.txt`.
- B: `study/session_b_tools/`. Scripts: `b_units.py`, `b_hz5m.py`, `b_hz1h.py`, `b_hz2.py`, `b_surface.py`, `b_expr.py`, `b_replicate.py`, `b_afterbreak_pool.py`. Outputs: `out_units.txt`, `out_hz5m.txt`, `out_hz1h.txt`, `out_hz2_{1h,5m,1h_H12,5m_H30}.txt`, `out_surface.txt`, `out_expr.txt`, `out_EURUSD23_day.txt`, `out_afterbreak_EURUSD23.txt`, `out_afterbreak_pool.txt`.
- Data:
  - `study/amt_data/cme/` (public GitHub dataset `axb0306/cme-futures-ohlc`);
  - `study/bias_data/`;
  - `study/ict_pd_b_tools/ext/smc/tests/test_data/EURUSD/EURUSD_15M.csv` (EURUSD 15m 2022-23, bundled with an open-source SMC library's tests);
  - `dl_knn/repo/tests/parity/baselines/` (OANDA EURUSD and Coinbase BTC daily);
  - Bitstamp BTC minute data (public GitHub dataset `ff137/bitstamp-btcusd-minute-data`) cached as `study/session_data/btc_1h.pkl`.

**Academic**
- Mok, D. M. Y., Lam, K. & Li, W. (2000). Using daily high/low time to test for intraday random walk in two index futures markets. *Review of Quantitative Finance and Accounting* 14(4):381-397. https://scholars.hkbu.edu.hk/en/publications/using-daily-highlow-time-to-test-for-intraday-random-walk-in-two-/ [B]
- Copeland, L., Lam, K. & Jones, S. (2004). The index futures markets: is screen trading more efficient? *Journal of Futures Markets* 24(4):337-357. https://econpapers.repec.org/RePEc:wly:jfutmk:v:24:y:2004:i:4:p:337-357 · https://orca.cardiff.ac.uk/2780 [B]
- Fung, A. K.-W., Mok, D. M. Y. & Lam, K. (2000). Intraday price reversals for index futures in the US and Hong Kong. *Journal of Banking & Finance* 24(7):1179-1201. https://scholars.hkbu.edu.hk/en/publications/intraday-price-reversals-for-index-futures-in-the-us-and-hong-kon/ [B]
- Grant, J. L., Wolf, A. & Yu, S. (2005). Intraday price reversals in the US stock index futures market: a 15-year study. *Journal of Banking & Finance* 29(5):1311-1327. https://ideas.repec.org/a/eee/jbfina/v29y2005i5p1311-1327.html [B]
- Plastun, A., Sibande, X., Gupta, R. & Wohar, M. (2020). Price gap anomaly in the US stock market: the whole story. *NAJEF*. https://ideas.repec.org/p/pre/wpaper/201963.html · https://repository.up.ac.za/handle/2263/78336 [A]
- Caporale, G. M. & Plastun, A. (2017). Price gaps: another market anomaly? *Investment Analysts Journal* 46(4):279-293. https://bura.brunel.ac.uk/handle/2438/14372 [B]
- Holmberg, U., Lönnbark, C. & Lundström, C. (2013). Assessing the profitability of intraday opening range breakout strategies. *Finance Research Letters* 10(1):27-33. https://econpapers.repec.org/RePEc:eee:finlet:v:10:y:2013:i:1:p:27-33 · https://swopec.hhs.se/umnees/abs/umnees0845.htm [B]
- Engle, R. F. & Sokalska, M. E. (2012). Forecasting intraday volatility in the US equity market: multiplicative component GARCH. *Journal of Financial Econometrics* 10(1):54-83. https://ideas.repec.org/a/oup/jfinec/v10yi1p54-83.html [A]
- Andersen, T. G. & Bollerslev, T. (1998). Deutsche mark-dollar volatility: intraday activity patterns, macroeconomic announcements, and longer run dependencies. *Journal of Finance* 53(1):219-265 (standard reference; not fetched). Andersen & Bollerslev (1997), *J. Empirical Finance* 4:115-158, via ict_time E1. [A/B]
- Alizadeh, S., Brandt, M. W. & Diebold, F. X. (2002). Range-based estimation of stochastic volatility models. *Journal of Finance* 57(3):1047-1091. https://econpapers.repec.org/RePEc:bla:jfinan:v:57:y:2002:i:3:p:1047-1091 [B]
- Martens, M. & van Dijk, D. (2007). Measuring volatility with the realized range. *Journal of Econometrics* 138(1):181-207. https://econpapers.repec.org/RePEc:eee:econom:v:138:y:2007:i:1:p:181-207 [B]
- Parkinson, M. (1980). The extreme value method for estimating the variance of the rate of return. *Journal of Business* 53(1):61-65. Garman, M. B. & Klass, M. J. (1980). On the estimation of security price volatilities from historical data. *Journal of Business* 53(1):67-78. Feller, W. (1951). The asymptotic distribution of the range of sums of independent random variables. *Annals of Mathematical Statistics* 22(3):427-432. (Standard references; not fetched.) [B]
- Cheung, Y.-W. (2007). An empirical model of daily highs and lows. *International Journal of Finance & Economics* 12(1):1-20. https://ideas.repec.org/a/ijf/ijfiec/v12y2007i1p1-20.html (working paper: https://cesifo.org/DocDL/cesifo1_wp1695.pdf). Daily highs and lows of DJIA, NASDAQ and S&P 500 are cointegrated; the VECM explains 40-50%. [B]
- Zarattini, C., Aziz, A. & Barbon, A. (2024). Beat the market: an effective intraday momentum strategy for S&P500 ETF (SPY). Swiss Finance Institute WP 24-97. https://www.sfi.ch/de/publications/n-24-97-beat-the-market-an-effective-intraday-momentum-strategy-for-s-p500-etf-spy. Noise-area definition from the CXO Advisory summary: https://www.cxoadvisory.com/momentum-investing/complex-intraday-time-series-momentum-strategy-applied-to-spy/ (*secondary*). [B]
- Mesfin, M. (2026). Structural limits of OHLCV-based intraday momentum signals in MNQ futures. arXiv:2605.04004 (independent preprint; passages read via the research index). Also arXiv:2605.11423 (VVG classifier). [B]
- Taylor, V. (2026). Evaluating the predictive validity of ICT's AMD model on CME E-mini NASDAQ-100 futures. arXiv:2610.35887 (via ict_time; abstract re-read). [B]
- Gao, Han, Li & Zhou (2018). *JFE* 129(2):394-414, via ict_time E12. Boyarchenko, Larsen & Whelan, NY Fed SR 917, via ict_time E13. The arcsine law and Aldous's S&P 20-day blocks, via ict_time E15. [A]
- Crabel, T. (1990). *Day Trading with Short Term Price Patterns and Opening Range Breakout* (book; no numbers retrieved). Stretch definition verified via https://oxfordstrat.com/trading-strategies/narrow-range/ and https://www.mypivots.com/dictionary/definition/206/stretch [A/B]

**Vendor / practitioner** (*snippet* = read from search-result text; the page could not be fetched)
- TradeThatSwing, London H/L broken after the US open. *Snippet.* https://tradethatswing.com/98-of-the-time-existing-london-high-low-prices-are-broken-when-us-opens/ [A]
- Linnsoft "homework" (ES prior close touched 1,048/1,803 days). *Snippet.* https://linnsoft.com/homework [A]
- NexusFi, overnight-session analysis (ON high or low touched 96%); gap trading (92% → 18% by size). *Snippets.* https://nexusfi.com/a/data/pre-market-data-overnight-session-analysis · https://nexusfi.com/a/strategies/gap-trading-futures [A]
- NewsBTC 2019 and CryptoSlate on CME gaps. *Snippets.* https://www.newsbtc.com/news/bitcoin-cme-futures-gaps-are-filled-with-95-certainty-but-trading-them-is-risky/ · https://cryptoslate.com/do-cme-gaps-always-have-to-fill-bitcoins-60k-flush-says-no/ [A]
- DailyFX 2012, intraday seasonality; DailyForex 2016, volatility profiles; energyexch EURUSD 51-week tally. *Snippets.* https://www.dailyfx.com/forex/technical/article/special_report/2012/07/21/Improving_Profitability_with_Intraday_Seasonality.html · https://www.dailyforex.com/forex-trading-mind/2016/12/volatility-profiles-major-pairs/83545 · https://www.energyexch.com/thread/post/10434555 [A]
- edgeful: initial-balance report and ES strategies [A]; previous day's range report and posts (YM 67% green after PDH broken, 62% red after PDL broken), inside-day post (yesterday's H/L reached 81-88%, 6 months), NQ open below PDL → no test 75% [B]. *Snippets.* https://www.edgeful.com/blog/posts/initial-balance-breakout-report · https://www.edgeful.com/blog/posts/previous-days-range-report · https://www.edgeful.com/blog/posts/previous-days-range-trading-mistake · https://www.edgeful.com/blog/posts/inside-day-in-trading-breakout-data
- S&P 500 first-hour HOD/LOD test, 885 days 2021-25 (70.5% vs 68.5% baseline), and the "Al Brooks 90-minute" check (59%, 29 days); TradingView ideas. *Snippets.* https://tradingview.com/chart/SPY/HO4hFgeD/ · https://tradingview.com/chart/ES1!/nsWMvqn4-Debunking-Al-Brook-s-90-Minute-Theory-81-Win-Rate-Strategy [B]
- "Daily Range Exhaustion" script claim ("a quarter to a third of days exceed 100% ADR"), contradicted here. *Snippet.* https://www.tradingview.com/script/rH2pZylf-Daily-Range-Exhaustion-ADR-Probability-Map/ [B]
- TradeFlightPlan 2009 ES gap fills. *Snippet.* https://slopeofhope.com/?p=7470 [B]
- Backtrex London breakout GBPUSD 2016-2026 (−60%). *Snippet.* https://backtrex.com/en/backtests/london-breakout-gbp-usd [B]
- Via sibling studies: fxbacktest.app (E2, E5-E8), tradingstats.net (E10-E11), edgeful (E9, E14), mypivots (E4), Elite Trader ES count (bias_dol 2.1).

**Sibling proposal cross-references (current IDs).** ict_time.final: TIME-2 (time-of-day surface), TIME-3 (clock, `clkLf`/`clkLs`/`clkD`), TIME-4 (scorecard), TIME-5 (affinity switch), TIME-6 (session-end PoT/ETA), TIME-7 (ONH/ONL). quant_pot.final: QPOT-01 (zero drift), QPOT-04 (graded PoT and recalibration gate), QPOT-05 (forward variance), QPOT-06 (ETA and session-end PoT). calib_ml: CAL-1 (EB family multiplier), CAL-3 (candidate ledger), CAL-6 (PoT calibration layer). ict_pd.final: ICTPD-6 (gaps). quant_regime.final: REG-1. A cited "TIME-1 c[d]", "TIME-3 = ON range" and "TIME-4/QPOT-05 analytic session-end PoT"; in the final numbering these are TIME-3 `clkD`, TIME-7 and TIME-6/QPOT-06. [B-corrected]
