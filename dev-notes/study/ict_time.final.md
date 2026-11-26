# ICT Time & Price: combined final study (Researcher A + Researcher B) for DOL Engine v2

Domain:
- killzones, sessions and session ranges;
- algorithmic macros and Silver Bullet windows;
- Power of 3 / AMD and the Judas swing;
- time anchors (midnight / true day open, 08:30 and 09:30 opens, weekly open) and opening gaps (NDOG / NWOG / ORG);
- quarterly theory;
- CBDR, Asian range and Flout standard-deviation projections;
- daily and weekly profiles and weekday effects;
- IPDA 20/40/60-day data ranges and quarterly shifts;
- seasonal tendencies, scheduled news times, and the institutional clock (FX fixes, option cuts, settlements).

The question throughout: which of these change the **probability** or the **timing** of a level being taken, and how the engine should use them.

Engine studied: `brief/baseline_v2.pine`. Line numbers refer to it; it is byte-identical to `/home/user/m/indicators/dol_engine.pine` (checked with `diff`). Every line reference below was re-checked in this pass.

## How this report was made

Inputs:
- A's study `study/ict_time.md`, with its computations in `study/ict_time_calc/`.
- B's first pass (offline re-tests on CME data) in `study/ict_time_b_tools/`.
- B's second pass (web verification, new literature, new tests) in `study/ict_time_b2_tools/`. The first-pass report is kept there as `ict_time.final.prev_pass.md` for diffing.
- Sibling studies used for cross-checks: `quant_pot.md` (QPOT-xx), `session_stats.md` (SESS-xx), `classic_levels.md`, `asset_specific.md`, `trade_mgmt.md`, `skeptic.md` (SKEP-xx), `quant_regime.md`, `academic_sr.md`, `calib_ml.md`, `ict_liq.final.md`.

**Marking.**
- `[A]`: A's finding, kept as is.
- `[B]`: new in B's first pass (data re-tests).
- `[B2]`: new in B's second pass (web-verified sources, new literature, new tests).
- `[B-corrected]` / `[B2-corrected]`: an earlier finding changed; the entry says what changed and why.

**Evidence grades:**
- **strong**: peer-reviewed, or a large replicated quantitative study.
- **moderate**: published or reproducible numbers with a sound null.
- **weak**: practitioner consensus, or small/vendor samples.
- **none**: folklore, or tested and not supported.

**Verification status of A's web sources (honest note).**
- First pass: no web access, so B verified A's numbers against sibling studies, arXiv papers and real CME data.
- Second pass:
  - WebSearch worked (result summaries only).
  - WebFetch could not reach most hosts (fxbacktest.app, intercom.help and others fail DNS in this sandbox).
  - Firecrawl web search had no credits, but the Firecrawl research index (arXiv full text) worked.
- Result per source:
  - **Confirmed:** Gao et al. (R² 1.6% / OOS 1.2%); NY Fed SR917 (3.7% a year at 02:00-03:00 ET) and its 2026 decay; Ederington & Lee; Krohn-Mueller-Whelan; Evans; the macro windows; the killzone windows (with one correction); quarterly theory having no validation (LuxAlgo); mypivots' sample (1 Mar 1998-9 Jun 2004, 27 × 15-min RTH segments, 09:30-16:15).
  - **Partly confirmed:**
    - Midnight-open retrace: edgeful and LuxAlgo give 57-74%, consistent with A's 65.6-68.0%, but tradingstats itself was not found.
    - Overnight range: NexusFi independently reports that at least one side breaks 96.4% (A: 94.2%).
  - **Not confirmable here** (marked "as reported by A"): every fxbacktest.app number (hourly ranges, release multiples, Asian-range and London ORB tests); the tradingstats numbers; tradestar's Silver Bullet test; edgeful's YM session table; Aldous's "746 blocks".

---

## 0. Executive summary

1. **Time changes "which liquidity is taken next, and when" mainly through one channel: the intraday volatility clock.** [A; confirmed by B on real data]
   - Volatility is strongly periodic. The ES 5-min variance at the 09:30 bucket is 4.7x the daily mean, and 0.20x at 23:30 (quant_pot).
   - Ederington & Lee (1993, J. Finance) show that scheduled announcements cause most of the time-of-day and day-of-week volatility pattern in rates and FX futures. [B2]
   - The engine's PoT ignores the clock. On a 5-min chart with H = 30 (6 CME futures, about 1.2 M level-windows, causal), the default Empirical PoT is biased by hour:

     | NY hour | Observed touch rate | Engine predicted | Bias |
     |---|---|---|---|
     | 07:00 | 68.3% | 52.4% | -16 pp |
     | 08:00 | 69.1% | 52.3% | -17 pp |
     | 11:00 | 42.1% | 52.3% | +10 pp |
     | 16:00 | 44.5% | 52.7% | +8 pp |
     | 21:00 | 42.0% | 52.7% | +11 pp |

   - Mean absolute hour bias: 7.3 pp on 5m with H = 30, and **8.4 pp on 1H with H = 12** [B2]. It is only 3.1 pp on 1H with H = 30, where the 30-hour window averages the clock out. [B]

2. **There is one real time-of-day effect beyond volatility: the US cash-open drive in equity-index futures.** [B2, new test]
   - Unit: 20-minute windows starting 09:20-09:59 ET, on 1-min ES/NQ/YM/RTY.
   - Each window takes the prior 60-minute high or low **+10 to +15 pp more often** than a generous variance clock predicts. Observed 90-93% vs model 79%; day-clustered SE 1.6-3.2 pp; 60 days.
   - It is absent at 08:30 (data releases: -2.8 ± 3.0 pp), after 10:00 (+1.0 ± 2.6), in the rest of RTH (-2.6 ± 1.0), and in CL/GC.
   - This **corrects B's first-pass reading**, which attributed the "09:50-10:10 macro" excess to 10:00 ET data releases. It is the tail of the cash-open drive.
   - An empirical time-of-day surface learns it automatically; a pure volatility clock cannot.

3. **What to build.** Two robust PoT upgrades and one correctness fix. [B, extended by B2]
   - **Time-of-day empirical surface (TIME-2).**
     - Brier gain: +2.2% (5m, H = 30 and H = 60), +3.75% (1H, H = 12), +0.4% (1H, H = 30).
     - It improved Brier on all six symbols in every setting tested.
     - 12 "landmark" blocks aligned to the killzones and the cash open were tested in this pass: **no better** than 8 uniform 3-hour blocks (+2.20% vs +2.18% on 5m; +3.20% vs +3.75% on 1H with H = 12). [B2]
   - **Robust NY-keyed volatility clock (TIME-3).**
     - Brier gain: +3.9% (5m, H = 30), +5.5% (5m, H = 60), +3.9% (1H, H = 12).
     - Mean hour bias 7.3 → 2.1 pp.
     - It fails on GC 1H (-9.8%), so it is switched on per chart by a measured scorecard (TIME-4).
   - **Session windows (TIME-1).** On the default 1H chart, the engine's NY AM range is wrong on 76% of days, because session membership tests only the bar open. Details in item 7.

4. **Most ICT time "facts" are what a random path does on that clock.** [A; refined by B]
   - The day-bootstrap null (session_stats) puts the session, day and week statistics within ±3 pp of geometry.
   - The weekly "Tuesday low" must beat the arcsine baseline:

     | Weekday | Mon | Tue | Wed | Thu | Fri |
     |---|---|---|---|---|---|
     | Share of weekly extremes | 29.5% | 14.1% | 12.8% | 14.1% | 29.5% |

   - "Red first hour → red day" (66.2%) is overlap arithmetic.
   - The one Judas-like residual: on index futures, after the first break of the **Asia range**, the other side is taken +3.5 to +6.2 pp more often than the null.

5. **Power of 3 / AMD has now been tested directly, and it fails as a directional and a timing rule.** [B2]
   - Taylor (2026, arXiv:2610.35887): NQ 2022-2026, N = 484 signal days.
   - After London sweeps the Asia low, the day closes above the Asia midpoint only 46.9% of the time (a coin flip). After it sweeps the Asia high, the bearish call is right 39.9% (inverted, p = 0.002).
   - The daily trend explains all of it: with-trend signals are right 62-71% of the time, counter-trend 25-30%.
   - On 57% of signal days the "distribution" target was already delivered **before** the 09:40 NY entry.

6. **Macros and Silver Bullet: tested, null.** [B; B2 attribution]
   - Macro windows: +0.6 ± 0.5 pp sweep residual beyond the clock (61k windows).
   - Silver Bullet hours: +0.2 ± 0.6 pp.
   - The clock itself shows no volatility bump in the macro windows; only 09:50 is above its neighbours (1.22x).
   - The only exception, 09:50-10:10, is the cash-open drive on the indices: ES +12.5, NQ +12.9, RTY +8.8, YM +7.5 pp; GC -0.5 and CL -5.9 pp.
   - The FX WM/R 16:00 London fix (11:00 ET) is a real flow event in FX (strong literature), but the 10:50-11:10 window is null on CME futures (-1.1 ± 2.2 pp).

7. **The session-window bugs, quantified.** [A found them; B measured them]
   - On a 1H futures chart the "NY AM 09:30-12:00" range is really 10:00-12:00.
     - At least one of the engine's NY H/L pools is the wrong level on **76% of days**, off by 14-16% of the day's range when wrong.
     - The NY open anchor is the 10:00 open, a median 15.6% of the day's range away from the true 09:30 open.
   - **New in B2: on 2H and 4H charts the killzone label is arbitrary.**
     - Example, 4H futures bars: the 10:00-14:00 bar, the busiest four hours of the US day, is classed OFF-KZ, which doubles hysteresis.
     - Sessions are already restricted to charts ≤ 1H; killzones are not.

8. **Other corrections.**
   - **Midnight open [B-corrected].** It is not special. Against neighbouring hourly opens at equal distance its excess is +0.3 ± 1.1 pp (1,412 instrument-days). A's "Target: MO" is dropped.
   - **Intraday momentum [B-corrected].** No OHLCV intraday-momentum family survives costs on MNQ 2021-25. A's TIME-9 is dropped.
   - **IPDA extremes [B-corrected].** 20/60-day extremes are reached at the random-level rate. Driessen, Lin & Van Hemert (2013) show 52-week extremes act as **volatility barriers**: realised variance is +19% / +43% the day after a break of the high / low [B2]. They matter for volatility, not as magnets.
   - **Pre-FOMC drift [B2-corrected].** About 40 bp on press-conference days up to 2018, substantially weaker since 2016. The overnight drift is flat in 2021-25. Directional calendar drifts are not worth modelling.
   - **Ledger EDGE.** The clock bias is now measured (skeptic §2.3 F) [B2]. No-skill pickers timed in busy windows show +2-3 pp of fake EDGE, and in quiet windows -2 to -3 pp. A mirror control cuts mean |z| from 0.69 to 0.24.
   - **Event multipliers [B2-corrected].** B's first pass used the release-hour **range** ratios (FOMC 5.2x, NFP 2.7x, CPI 2.1x, as reported by A) as **variance** multipliers. Variance scales with range squared, so the event input must be stated in σ units and squared.
   - **Session opens in confluence [B2-corrected].** The first pass made them default-off. The feature spec names "Session Opens" as a confluence anchor, so they stay **on** by default, made exact. The evidence (no magnet effect) is reported, and the per-group calibration can down-weight them.

9. **Best proposals (§4), best first:**
   1. TIME-1: exact session windows, killzones only on charts ≤ 1H, London close and London DST.
   2. TIME-2: time-of-day empirical surface.
   3. TIME-3: robust NY-keyed clock with a z-surface, gated.
   4. TIME-4: per-chart PoT scorecard, auto-selection, and a time-neutral EDGE.
   5. TIME-5: neutral killzone affinity and continuous hysteresis.
   6. TIME-6: PoT by session end and ETA in clock time.
   7. TIME-7: ONH/ONL pools.
   8. TIME-8: scheduled-event scaling (manual input plus an NFP rule, in σ units).

---

## 1. Concepts: definitions, parameters, edge cases

All clock times are **New York local time** (IANA `America/New_York`, DST-aware), as ICT teaches. Practitioner sources disagree by 30-90 minutes on several boundaries. The most-cited values come first; variants follow.

### 1.1 Killzones [A; B2-corrected windows]
- **Windows** (innercircletrader.net, LuxAlgo, TradingFinder, community scripts; re-checked by B2):

  | Killzone | Main window | Variants and notes |
  |---|---|---|
  | Asian | **20:00-22:00** (ICT original; most sources) [B2-corrected] | 20:00-00:00 is the Asian *session range* (LuxAlgo toolkit; the engine's `kzAs`). 19:00-22:00 also seen |
  | London open | 02:00-05:00 | the most consistent; about an hour before the London cash open |
  | New York AM (FX) | 07:00-10:00 | index variants 08:30-11:00 (TradingFinder and community "NY open") and 09:30-11:00 (LuxAlgo toolkit) |
  | London close | 10:00-12:00 | brackets the WM/R 16:00 London fix = 11:00 ET (§1.18) |
  | NY lunch | 12:00-13:00 or 13:30 | ICT's "no trade" window |
  | New York PM | 13:30-16:00 | |

- **Algorithm.**
  - `inKZ` means the bar interval `[open, open + tf)` overlaps `[start, end)` in NY time.
  - The killzone high and low are the extremes of the bars inside it, carried forward as liquidity.
- **What is real.** These are the windows where volatility and participation concentrate (Andersen-Bollerslev; quant_pot; B's clock). Dacorogna et al. (1993) model this as the overlapping presence of the East Asian, European and American markets. [B2]
- **What is not supported.** That a level is *more* likely to be raided in a killzone than the clock predicts (§2.2-2.4). The single exception is the cash-open drive (§1.17), which sits in the 09:20-10:00 slice, not in a killzone as such.
- **Edge cases:**
  - **US/UK DST mismatch:** about 3 weeks in March and 1 week in late October/early November. During it, London 08:00 is 04:00 NY instead of 03:00, and the WM/R fix is at 12:00 NY instead of 11:00.
  - Charts in UTC or exchange time.
  - **24/7 crypto**, whose periodicity is set by US/EU hours and perpetual-funding times (00/08/16 UTC). Volatility peaks near 16 UTC, troughs near 05 UTC, and is lower at weekends (Hansen, Kim & Kimbrough 2021). [B]
  - **Bar-open tests on coarse bars:** wrong session bounds on 1H (§1.2); an arbitrary killzone label on 2H and 4H (G20). [B2]
- **10:00-11:00 ET.** It is the busiest single *hour* for US index futures. Yet on a 5m chart with H = 30, a forward window starting at 10:00 has a **below**-average touch rate (46.4% vs 51.9%), because it runs into the lunch lull. A killzone label says nothing about the next H bars; only the clock does. [B]

### 1.2 Sessions and session ranges [A; B quantified the window bug]
- **Definition.** The high and low printed inside a fixed clock window. They become "session liquidity" once the window closes.
  - Asia 20:00-00:00; London 02:00-05:00 (or 00:00-05:00); NY AM 08:30/09:30-11:00/12:00; lunch 12:00-13:00/13:30; NY PM 13:30-16:00.
  - Futures **overnight/Globex** range 18:00-09:30, with extremes ONH/ONL.
- **Edge cases:**
  - windows that cross midnight;
  - ties (take the first or the outermost print);
  - **bars straddling a boundary**;
  - holidays and early closes;
  - charts coarser than the window.
- **Pine membership rule.** "The `time()` function returns a UNIX timestamp for the *opening time* of the current bar, or `na` if the bar is not in the specified session" (local docs, `concepts/sessions.md` line 47, re-read by B2). It is a **bar-open** test.
  - On 1H futures, FX and crypto charts (bars on the hour), a window starting at :30 begins at the next bar.
  - US stocks have 1H bars at 09:30, 10:30, … so the window is aligned there.
- **B's measurement** (1-min CME, 349 instrument-days, `sess_bug.py`):

  | Construction on a 1H chart | Wrong extreme (high / low / either) | Mean error when wrong |
  |---|---|---|
  | Engine, bar-open: "09:30-12:00" = 10:00-12:00 | 37.5% / 40.7% / **76.2%** of days | 14% / 16% of the day's range |
  | Overlap test: 09:00-12:00 | 14.9% / 19.8% / 34.7% | 6-7% of the day's range |
  | Exact (30-min intrabars) | 0 | 0 |

  - The 09:30-10:00 half-hour holds one of the two NY AM extremes on most days. That is the arcsine law plus the open burst (and the cash-open drive, §1.17).
  - The NY open anchor on 1H, the **10:00** open, is a median **15.6%** of the day's range away from the true 09:30 open.
  - The NY PM killzone on 1H starts at 14:00. The 13:30-16:00 high is missed on 25% of days, the low on 36%.

### 1.3 Time anchors: midnight open, 08:30, 09:30, weekly and session true opens [A defs; B-corrected evidence; B2 sources]
- **Midnight open (MO / TDO).** The open of the 00:00 NY bar, extended through the day.
  - ICT: on a bullish day the low forms below the MO early (manipulation), and price distributes above it afterwards.
  - "The low is below the open" is close to a tautology (low ≤ open). The testable claim is that the NY session gravitates back to the MO.
- **How the commercial statistics define it** [B2]. edgeful's "ICT opening retracement" counts a return to the MO inside 09:30-16:00. "Opened above / below" compares the 09:30 open with the MO; London uses its 03:00 open.
  - edgeful snapshots (rolling 6 months): ES 58% / 69% (above / below), NQ 57% / 63%, YM 63% / 67%.
  - LuxAlgo, NQ: 74% / 63%.
  - Both are consistent with A's tradingstats 65.6-68.0%.
- **08:30 open.** The release time for CPI, NFP, PPI and similar data.
- **09:30 open.** The US cash open.
- **Weekly open.** Sunday 18:00. The quarterly-theory "true week open" is Monday 18:00.
- **Session true opens** (quarterly theory): 19:30, 01:30, 07:30, 13:30.
- **Evidence [B-corrected].** The MO statistic is a fact about *distance and recency*. B's anchor-neighbour test (`mo_test.py`) compares the RTH revisit rate of each hourly open from 18:00 to 08:00 with a rate pooled across all anchors in the same distance bin (distance from the RTH open, in ADR units):

  | Data | Days | 00:00 open | 23:00 | 01:00 |
  |---|---|---|---|---|
  | CME 1h, Mar 2025-Apr 2026 (6 futures) | 1,412 | +0.27 ± 1.14 pp | +0.04 | -0.25 |
  | 1-min, exact 09:30-16:00 | 256 | +0.35 ± 2.6 pp | | |

  - Raw revisit rates rise smoothly with recency, because later opens sit closer to the RTH open: 18:00 → 46.7%, 00:00 → 52.4%, 08:00 → 61.1% (1h proxy).
  - classic_levels T5: pools near the engine's time anchors score +0.6 pp at CME (not significant) and -3.3 pp at BTC H8 (z -3.6).
  - Grade for "MO is a magnet": **none** (tested, not supported).
  - The 08:30 and 09:30 times are strong as **volatility times** and untested as levels.
  - classic_levels: weekly and monthly opens act as barriers (-5 to -7 pp).

### 1.4 Quarterly theory [A; B2 verified]
- **The day in 6-hour quarters:** 18-00 Asia, 00-06 London, 06-12 NY, 12-18 afternoon.
- **Sub-quarters:** 90-minute quarters inside each session.
- **Recursion:** the same grid applies to the week, the month and the year.
- **Phases:** AMDX, or XAMD for "delivery-first" cycles. The true open is the Q2 open (midnight for the day). Credited to a trader named Daye.
- **Evidence:** none.
  - LuxAlgo publishes no validation.
  - Community tools describe cycle identification as discretionary.
  - The AMDX/XAMD choice makes the scheme close to unfalsifiable.

### 1.5 Algorithmic macros [A defs; B tested; B2 attribution]
- **Windows** (verified against community trackers whose release notes cite an ICT livestream):
  - London: 02:33-03:00 and 04:03-04:30;
  - pre-market: 08:50-09:10;
  - AM 1: 09:50-10:10;
  - AM 2: 10:50-11:10;
  - lunch: 11:50-12:10;
  - PM: 13:10-13:40 (some lists 13:10-13:50);
  - last hour: 15:15-15:45.
- **Claim.** Inside a window, price sweeps nearby liquidity and/or rebalances an FVG.
- **B's test** (`macro_test.py`; 1-min ES/NQ/YM/RTY/CL/GC, Jan 20-Apr 15 2026):
  - **Unit:** 20-minute windows starting every 5 minutes from 01:00 to 16:00.
  - **Pool:** the prior 60-minute high and low.
  - **Distance:** in clock σ, using a per-minute clock times the same day's level (a generous model).
  - **Outcome:** the window trades through either side.
  - **Model:** a logistic fit of the outcome on a spline of distance, with symbol effects.
  - **Reported:** the mean residual with clustered SE. Results (61,244 windows; base sweep rate 61.1%):

    | Window | Residual (pp) | SE |
    |---|---|---|
    | All macro windows | +0.58 | 0.48 |
    | 02:33-03:00 | +2.38 | 1.47 |
    | 04:03-04:30 | +3.45 | 1.49 |
    | 08:50-09:10 | -0.34 | 1.59 |
    | **09:50-10:10** | **+6.11** | 1.47 |
    | 10:50-11:10 | -1.07 | 1.52 |
    | 11:50-12:10 | -2.74 | 1.64 |
    | 13:10-13:40 | -1.26 | 1.49 |
    | 15:15-15:45 | -2.12 | 1.45 |
    | Silver Bullet hours (03, 10, 14) | +0.19 | 0.61 |
    | Silver Bullet 10:00-11:00 | -0.83 | 1.04 |

  - **Volatility in the windows.** Clock variance in each macro window relative to its ±30-minute neighbours: 08:50 0.39, 09:50 1.22, 10:50 0.85, 11:50 0.92, 13:10 0.97, 15:15 0.78. The macro times are **not** volatility bursts either.
- **B2 attribution of the 09:50-10:10 excess** (`macro_attr.py`, `macro_attr2.py`, day-clustered SE):

  | Window starts | Indices (ES/NQ/YM/RTY) | CL + GC |
  |---|---|---|
  | 09:20-09:40 (cash open) | **+13.1 ± 1.7** | +3.3 ± 2.8 |
  | 09:50-10:10 | **+10.4 ± 2.4** | -3.5 ± 2.9 |
  | 08:20-08:40 (08:30 data) | -2.8 ± 3.0 | +1.7 ± 3.1 |
  | 10:15-10:35 | +1.0 ± 2.6 | |
  | rest of RTH (10:40-15:40) | -2.6 ± 1.0 | |

  - Per symbol at 09:50-10:10: ES +12.5, NQ +12.9, YM +7.5, RTY +8.8, CL -5.9, GC -0.5 pp.
  - It is index-only, absent at the 08:30 releases (the larger data slot), and gone by 10:00. So it is **not** a 10:00 data-release effect (B's first-pass reading, corrected). It is the end of the cash-open drive (§1.17).
- **Grade:** none for macros as such.

### 1.6 Silver Bullet [A; B and B2 added evidence]
- **Windows:** 03:00-04:00, 10:00-11:00, 14:00-15:00.
- **Rule.** After a liquidity sweep, enter on the first displacement FVG toward the draw, and target the next pool.
- **Evidence (negative):**
  - tradestar: 108 trades, 38.9% win rate at 1:1, net loss (as reported by A; not re-found).
  - trade_mgmt P3: profit factor 0.66-0.94; 0 of 10 variants profitable (2R target, 2020-2025). The GBB script on 1-min ES/NQ/YM/GC 2011-2026 found "the Silver Bullet hours are not special".
  - Other mechanical tests found by B2 (weak, uncontrolled):
    - a fully mechanical ICT bot on EURUSD 15m: 29.6% win rate, profit factor 0.81 over one year;
    - a "25,000 Silver Bullet trades" summary: about 52% win rate for the best variants, and 1.7% of configurations survived its test stack.
  - B's window test: +0.2 ± 0.6 pp.
- **Grade:** none for the claim; the negative evidence is moderate.

### 1.7 Power of 3 (AMD) and the Judas swing [A; B refined; B2 direct test]
- **Power of 3.** Each candle runs accumulation, a manipulation leg against the eventual direction, then distribution.
- **Judas swing.** The early-session manipulation leg, measured from the MO or the session open.
  - It must fail: rejection, then displacement back through short-term structure.
  - If price holds beyond the swept level, it is a trending open, not a Judas.
- **Direct test (Taylor 2026, arXiv:2610.35887, preprint, code public)** [B2]:
  - **Rules:**
    - Asia 19:00-00:00 ET is the accumulation range.
    - A London (02:00-05:00) 15-min candle breaches it by at least δ = 10 NQ points before 04:00.
    - A candle closes back inside before 05:00.
    - Bilateral breaches are excluded.
  - **Outcome:** the 16:00 close vs the Asia midpoint.
  - **Results, N = 484:**
    - Bullish (low swept): 46.9% correct (CI 40.5-53.4).
    - Bearish (high swept): 39.9% (inverted, p = 0.002). After London sweeps the Asia high, the close is above the midpoint 60.1% of the time.
    - With the daily trend (20-EMA regime): 62-71% correct. Against it: 25-30%. Robust to δ = 5-20.
  - **Timing:** on 57% of valid signals the opposite Asia side was delivered **before** the 09:40 NY entry; most of those during 05:00-09:40, and 28.7% already inside London.
  - So the opposite-side raid is frequent (consistent with session_stats' index-futures Asia residual), but it is early, and it says nothing about direction.
- **Other evidence:**
  - fxbacktest (as reported by A): FX Asian-range first-break fade 49.4% (n 9,598, not significant); London ORB follow-through 50.3% (n 92,947); crypto continues 55-58%.
  - G10 FX sweeps favour continuation (ict_liq E7).
  - session_stats day-bootstrap null [B]:
    - After the first break, the opposite side is taken **less** often than the null for PD (-1.9 pp on average), NY AM (-3.1 pp) and PW ranges.
    - The **exception is the Asia 20:00-00:00 range on index futures**: +3.5 to +6.2 pp (ES +4.7, NQ +3.6, YM +3.5, RTY +6.2; about 3 SE pooled). It is absent in CL (-1.2), EURUSD (+0.5) and BTC (-1.3).
  - Mesfin (2026, arXiv:2605.04004, preprint): Asia-session expansion bars on MNQ reverse at the next bar (T = -10.96).
  - Nava, Di Matteo & Aste (arXiv:1508.07428) find anti-persistent behaviour at the open and close on 30-second index data (S&P 500, 105 days) [B2]. That is a microstructure-scale reversal; at the 20-minute scale the open is *expansive* (§1.17).
- **Grade:**
  - none as a directional or timing rule (now tested; moderate negative evidence);
  - weak-moderate for the narrow "index-futures Asia two-sided raid", a learnable cell (SESS-2), not a fixed rule.

### 1.8 CBDR, Asian range, Flout and SD projections [A; B2 notes]
- **CBDR:** 14:00-20:00 NY. One "SD" is the range height. Rungs: `U_k = H + k·R` and `D_k = L - k·R`, k ∈ {1, 1.5, 2, 2.5, 3, 4}. The London extreme is expected at 1-3 SD, and 4 SD on news days.
- **Range-size rules** [B2]:
  - The "< 40 pips" rule is a **community convention**. Scripts attribute to ICT an ideal of about a third of ADR, and say the range should not be used beyond 40% of ADR.
  - No primary statement was found.
  - When the CBDR is too wide, the Asian range (20-30 pips in FX) is used instead.
- **Asian range:** 20:00-00:00, projected 2-4 SD.
- **Flout:** CBDR plus Asia, about 15:00-00:00.
- **Evidence:** none. The underlying size fact is a volatility ratio (the Asian session holds about 48% of EURUSD's daily range, as reported by A), which the clock already provides.

### 1.9 Daily profiles [A]
- **Templates:** London/NY reversal or continuation; consolidation day.
- **Evidence:** none. A day can only be classified after the fact.

### 1.10 Weekly profiles and weekday effects [A; B-corrected magnitude; B2 mechanism]
- **ICT templates:** Tuesday/Wednesday low (high) of week, Wednesday reversal, Consolidation Thursday reversal, Seek & Destroy Friday.
- **Null:** the arcsine law (§1.15).
  - session_stats found the weekday U-shape equal to a day-order shuffle: Mon/Fri 23-34%, Tue-Thu 12-18%.
  - "Weekly low by Tuesday in up weeks": 72-75%, vs the null's 76-77%.
- **Real effect: volatility** [B-corrected]. Day range / ADR14 on full CME trading days (1 year of 1h data, `weekday.py`):

  | | Mon | Tue | Wed | Thu | Fri |
  |---|---|---|---|---|---|
  | ES | 0.99 | 0.90 | 0.95 | 1.05 | 1.11 |
  | NQ | 0.99 | 0.90 | 0.99 | 1.03 | 1.10 |
  | YM | 1.01 | 0.95 | 0.90 | 1.04 | 1.08 |
  | RTY | 0.97 | 0.94 | 0.96 | 1.04 | 1.08 |
  | GC | 1.10 | 0.98 | 0.93 | 1.08 | 1.11 |

  - The variance factor is 0.80-1.23, about ±10% in σ. A cited "Monday about 20% lower" from edgeful's NY-session range, as reported by A.
  - **Mechanism** [B2]: Ederington & Lee (1993) attribute most day-of-week volatility patterns to scheduled announcements (e.g. employment Fridays). A learned weekday factor is a blunt proxy for the release calendar (see TIME-8).

### 1.11 IPDA data ranges and quarterly shifts [A defs; B-corrected evidence; B2 additions]
- **Definition.** The highest high and lowest low of the last 20 / 40 / 60 **trading days** (daily candles regardless of chart timeframe), and their 50% levels. Untaken extremes are "cast forward" draws for the next 20-60 days.
  - Variants [B2]: some tools use 50 instead of 60 days. The anchor is either "now" (rolling) or a chosen shift date.
- **Quarterly shift.** A change in the dominant daily direction around a quarter turn.
  - Definitions vary [B2]: every 20/40/60 days; a close beyond the prior 60-day extreme; or a discretionary daily MSS near a quarter turn.
- **Evidence.** classic_levels T2, distance-matched random-level edges:

  | Level | 5 days | 20 days |
  |---|---|---|
  | 20dH / 20dL | +0.21 / +0.72 pp | -0.83 / +0.32 pp |
  | 60dH / 60dL | +0.43 / +0.30 pp | -0.56 / +0.80 pp |
  | 252dH / 252dL | at baseline | at baseline |

  - Driessen, Lin & Van Hemert (2013, Review of Finance) [B2]:
    - Approaching a 52-week high or low, implied volatility and beta **fall**.
    - After a breakthrough, realised variance rises about 19% (high) and 43% (low) the next day (working-paper figures).
    - So old extremes are volatility barriers, not magnets.
- **Grade:** none beyond distance (tested). Prior month and quarter extremes are also at baseline. Monthly and quarterly **opens** are reached *less* often than random (QOPEN -4.1 pp, z -3.2, at 20 days).

### 1.12 Seasonal tendencies and scheduled times [A; B and B2 corrected]
- **Overnight drift** (Boyarchenko, Larsen & Whelan; NY Fed SR917 / RFS 2023):
  - ES returns at 02:00-03:00 ET about 3.7% a year (1.48 bp a day). [B2 confirmed]
  - **About zero since 2021** ("The Disappearing Overnight Drift", Liberty Street Economics, 1 July 2026). The authors attribute the fade to smaller closing order imbalances. [B2 confirmed]
- **Pre-FOMC drift** (Lucca & Moench 2015):
  - +49 bp in the 24 hours before scheduled FOMC announcements (1994-2011).
  - The 2018 update: about 40 bp, but only on press-conference days.
  - Kurov, Wolfe & Gilbert: substantially weaker since 2016, even with press conferences. [B2-corrected]
- **Scheduled releases** (as reported by A, fxbacktest, 3,963 releases):
  - The release hour's **range** is FOMC 5.2x, NFP 2.7x and CPI 2.1x that of a normal same-clock hour.
  - Variance scales with range squared, so these are roughly 27x / 7x / 4x in variance over that hour. [B2-corrected units]
  - Ederington & Lee: the bulk of the price adjustment comes in the first minute; volatility stays well above normal for about 15 minutes and slightly elevated for hours. [B2]
- **NFP timing** [B2]. BLS releases the Employment Situation on the **third Friday after the reference week** (the week that includes the 12th), not "the first Friday". It is usually the first Friday, with holiday and shutdown exceptions (e.g. the December 2026 report falls on 8 January 2027).
- **Relevance.**
  - Drifts are 0.1-0.2σ per hour or less, so they barely move touch probabilities.
  - Release-time variance is large and foreseeable (TIME-8).

### 1.13 The quantitative core: the volatility clock [A; B built and tested it; B2 lineage]
- **Model** (Andersen & Bollerslev 1997/1998; Engle & Sokalska 2012):

  `r_t = σ_day · s(τ_t) · z_t`

  - `s(τ)` is a deterministic periodic factor by NY time of day and weekday.
  - `σ_day` is a slowly varying level.
- **Lineage** [B2]:
  - Dacorogna, Müller, Nagler, Olsen & Pictet (1993, JIMF): integrating a seasonal activity function over time gives a business-time scale ("ϑ-time") on which FX volatility has no daily or weekly seasonality. Active hours are stretched, weekends compressed.
  - Aldrich, Heckenbach & Laughlin (arXiv:1408.3650): ES returns are close to Gaussian in *trade time* once scheduled news is controlled for.
  - Allez & Bouchaud (arXiv:1009.4785): kurtosis is lowest at the open, when volatility peaks.
- **First passage.** For a driftless walk the touch probability depends on `z = d / √V`, with `V = Σ_{k∈window} σ²_day · s²(τ_k)`. It depends on the **variance remaining in the window**, not the bar count.
- **B's measured consequences:**
  - **Horizon gate.** Time of day matters when the horizon is shorter than about a day.
    - On 1H with H = 30 it averages out: mean hour bias 3.1 pp; the clock -1.0%; tod8 +0.4%.
    - On 1H with H = 12 the bias is 8.4 pp [B2], and the clock or tod surface gains +3.8-4.1%.
  - **Key to the session time zone, not UTC.** A UTC-keyed clock gained +3.5% vs +3.9% NY-keyed (hour bias 2.7 vs 2.1 pp). The sample holds only 5 post-DST weeks out of 12, so a full year would cost more. QPOT-02 as written uses UTC buckets: switch it to `tz`.
  - **Robust estimation matters more than the idea** (§2.2).

### 1.14 Intraday momentum [A; B-corrected relevance; B2 verified]
- **Gao, Han, Li & Zhou (JFE 2018):** SPY 1993-2013. The first half-hour return predicts the last half-hour return: R² 1.6% in sample, 1.2% out of sample (B2-verified). It is stronger on high-volatility days (quant_regime).
- **Against tradability:** Mesfin (2026, preprint). 14 OHLCV intraday-momentum families on MNQ 2021-25, walk-forward with costs: **none pass**. The 09:30-09:55 ORB has T = 0.88-1.50 and is unstable across years.
- **A practical time-of-day band** [B2]: Zarattini, Aziz & Barbon (2024, SFI RP 24-97). A "noise area" = open × (1 ± the average absolute move from the open at the same minute over the last 14 days). It is a published, simple time-of-day reach band (backtest figures not verified here).
- **Grade:** moderate for existence; none for a usable late-session tilt today. A's TIME-9 is dropped.

### 1.15 Arcsine law [A, verified]
- For Brownian motion on [0, T], the time of the maximum has density `1/(π√(t(T-t)))`.
- `P(max in [a, b]) = (2/π)[asin√(b/T) - asin√(a/T)]`.
- In business (variance) time, high-variance edges get even more mass.
- B checked A's weekly numbers: `(2/π)·asin√0.2 = 29.5%`, the next slice 14.1%, the middle 12.8%.
- Empirical: Panas (2005, Applied Economics) finds a U-shaped time of the daily maximum and minimum on 1-minute data [B2]. mypivots' ES table (as reported by A): 17.2% / 16.7% in the first 15-minute segment vs 17.7% from arcsine plus clock.
- Aldous's Berkeley page states the arcsine prediction for the time of the maximum. A's figure of "746 S&P blocks matching" was not confirmed in B2's search.

### 1.16 Session-horizon probability and ETA [A; B cross-referenced]
- **Concepts:**
  - "P(touch before the killzone end / 16:00 / day end)".
  - "ETA = the time at which V(τ) reaches (d/0.6745)²" (driftless median first passage).
- **Supporting numbers:**
  - session_stats: for an untaken PDH/PDL at 0.2-0.35 ADR, P(taken by day end) is **64% from Asia → 57% London → 47% NY AM → 19% NY PM**.
  - quant_pot: a vol-time ETA ranks the actual time-to-touch correctly (rank correlation +0.11 / +0.16 / +0.22 at 1 / 2 / 3 ATR). A constant-σ ETA ranks it wrongly (-0.09).
  - Taylor (2026): AMD targets are mostly delivered 05:00-09:40, earlier than the narrative says. [B2]

### 1.17 The US cash-open drive (equity-index futures) [B2, new]
- **Finding.** For ES/NQ/YM/RTY, 20-minute windows starting between 09:20 and 09:59 ET take out the prior 60-minute high or low far more often than a variance clock with the same-day level predicts:

  | Start (10-min bin) | 09:10 | 09:20 | 09:30 | 09:40 | 09:50 | 10:00 | 10:10 |
  |---|---|---|---|---|---|---|---|
  | Observed | 70.1% | 90.1% | 93.2% | 87.2% | 79.2% | 67.3% | 62.6% |
  | Model | 66.5% | 79.4% | 79.0% | 72.4% | 68.8% | 66.0% | 61.6% |
  | Residual (pp) ± SE | +3.6 ± 3.2 | +10.7 ± 2.5 | +14.3 ± 1.6 | +14.8 ± 2.5 | +10.5 ± 3.2 | +1.3 ± 3.4 | +1.0 ± 3.5 |

  - Per symbol (09:20-09:40 starts): ES +14.7, NQ +13.9, YM +12.0, RTY +11.9 pp. CL +1.3 and GC +5.7 pp are not significant.
- **Reading.** The cash open is not only high-variance; it is *directional* over 20-40 minutes. Ranges built in the quieter pre-market break more than a diffusion with that variance would allow. That fits Gao et al.'s first-half-hour momentum and session_stats' finding that RTH takes at least one overnight side more often than the null.
- **Limits.**
  - One 3-month sample (Jan 20-Apr 15 2026, 60 days).
  - The four indices move together; the day-clustered SE accounts for that.
  - It does not say *which* side.
- **Engine use.** The effect lives at short horizons (minutes after 09:30). At the engine's 5m, H = 30 horizon (2.5 hours) it is diluted:
  - the time-of-day surface's 09:00-12:00 block absorbs it;
  - landmark blocks with a separate 09:30-10:00 cell gave no extra Brier gain on 5m.
  - On 1-minute charts a finer block might pay; that is untested.
- **Grade:** moderate (one sample, strong signal).

### 1.18 The institutional clock behind the ICT windows [B2, new]
Several ICT windows bracket real scheduled flow events. These events change volatility and, in FX, produce small reversals. Times are ET with the normal 5-hour US/UK offset:

| Event | Time (ET) | ICT window it falls in | Evidence | Size |
|---|---|---|---|---|
| WM/R 4 pm London FX fix | 11:00 (12:00 in mismatch weeks) | London close KZ 10-12; macro 10:50-11:10 | Evans 2018 (JBF): pre/post-fix changes strongly negatively correlated in all 21 currencies over a decade, strongest at month-end. Krohn, Mueller & Whelan 2024 (J. Finance): the dollar rises before fixes and falls after (a "W" over the day), about 2 bp daily swings for a G9 basket. Michelberger & Witte (arXiv:1501.07778): volatility spike in the minute before 16:00 London across 12 pairs | strong (exists), tiny vs daily σ |
| ECB fix (14:15 CET) | 08:15 | NY AM KZ (FX) | Krohn et al. | small |
| Tokyo fix (about 10:00 JST) | 20:00 (EST) / 21:00 (EDT) | Asian KZ start | Krohn et al. | small |
| NY option cut (FX options) | 10:00 | macro 09:50-10:10; Silver Bullet 10-11 | Michelberger & Witte: a second consistent volatility spike at 15:00-15:02 London = 10:00 ET (US data plus the NY cut). Practitioner reports of pinning near large strikes before the cut | moderate |
| LBMA gold price PM (15:00 London) | 10:00 | macro 09:50-10:10 | asset_specific | GC: no sweep residual (-0.5 pp, B2) |
| COMEX gold settlement | about 13:29-13:30 (secondary source) | macro 13:10-13:40 | NexusFi table | residual -1.3 ± 2.0 pp (all symbols) |
| NYMEX crude settlement | about 14:28-14:30 (secondary source) | Silver Bullet 14-15 | NexusFi table | not tested separately |
| ES daily settlement | 15:59:30-16:00 (14:59:30-15:00 CT) | end of NY PM | NexusFi; CME filings | not tested |

- **Reading.** Where ICT times coincide with real flows (fixes, cuts, settlements, releases), the effect on **probability of touch** comes through volatility, which a learned clock captures on average. Day-specific events need a calendar (TIME-8).
- The FX fix reversal is real, but at about 2 bp it is irrelevant to target selection.

### 1.19 Opening gaps: NDOG, NWOG, ORG [B2, new; cross-ref session_stats]
- **Definitions** (community scripts):
  - **NDOG:** the gap between the 17:00 close and the 18:00 reopen each day (futures).
  - **NWOG:** Friday 17:00 close → Sunday 18:00 open.
  - **ORG** (opening range gap): the previous RTH close (16:00 or 16:15) → the 09:30 open.
  - **CE:** the 50% of a gap. The claim is that gaps are magnets for days or weeks.
- **Evidence** (session_stats `gaps.py`, fill rate vs a mirrored placebo level at the same distance):

  | Gap | Sample | 1-day fill vs mirror |
  |---|---|---|
  | S&P 500 cash daily gaps | 1999-2018, n 3,026 | 63.7% vs 90.5% (**-26.8 pp**: the gap edge acts as a barrier) |
  | EURUSD weekend gaps | 2002-2026, n 641 | 73.2% vs 73.0% (+0.2) |
  | BTC "CME gap" | 2017-2025, n 415, 24h | 55.7% vs 61.4% (-5.8) |
  | Index-futures ORG | Jan-Apr 2026, n 204 | 59.3% vs 52.5% (+6.9, not significant) |

- **Grade:** none for "gaps are magnets". At most weak for the index ORG.
- Not proposed as targets. ict_pd covers gaps as PD arrays.

### 1.20 Time-of-day directional drifts in FX [B2, new]
- Breedon & Ranaldo (2013, JMCB; also Ranaldo 2009, JBF): currencies tend to **depreciate during their home market's trading hours**. The pattern shows up in order flow too: participants are net buyers of foreign currency in their own hours.
- A public replication (QuantRocket) finds EURUSD falling during the European day and rising through the US day.
- **Size:** a few bp. Like the fix "W", it is real but far below the PoT noise floor. Not modelled.

---

## 2. Evidence (numbers and sources)

### 2.1 Table

| # | Claim / effect | Source, sample | Numbers | Grade | Status |
|---|---|---|---|---|---|
| E1 | Intraday periodicity of volatility | Andersen & Bollerslev 1997/1998; Engle & Sokalska 2012; Dacorogna et al. 1993; Hansen-Kim-Kimbrough 2021 (crypto) | U-shape and session peaks; FX geographic seasonality; crypto peak near 16 UTC, trough near 05 UTC | strong | [A]+[B]+[B2] |
| E2 | Hourly range profile | fxbacktest, 922,937 H1 bars (as reported by A, not re-checkable); quant_pot (ES 5-min) | Peak/quiet hour 2.1-4.0x in range; ES 5-min variance at 09:30 = 4.7x the daily mean, 23:30 = 0.20x | strong (reproduced on CME) | [A]+[B] |
| E3 | Scheduled news drive volatility | Ederington & Lee 1993 (J. Finance); ABDV 2003; fxbacktest 3,963 releases (as reported by A) | Announcements cause most time-of-day and day-of-week volatility patterns; vol well above normal about 15 min, elevated for hours; release-hour range FOMC 5.2x, NFP 2.7x, CPI 2.1x (≈ 27x / 7x / 4x variance) | strong (mechanism); moderate (multiples) | [A]+[B2-corrected units] |
| E4 | HOD/LOD timing | mypivots ES 1 Mar 1998-9 Jun 2004, 27 segments (sample verified, numbers as reported by A); Panas 2005 | 09:30 segment: HOD 17.2%, LOD 16.7%; arcsine + clock gives 17.7%; U-shaped timing of extremes | strong (descriptive) | [A]+[B2] |
| E5 | Session ranges vs the null | session_stats, day-bootstrap null, 7 markets | Asia/London within ±3 pp; NY AM range: afternoons break one side more (+3 to +10 pp single); RTH takes at least one ON side more (none 3.6-4.0% vs 7.4-8.2%, ES/NQ) | moderate | [B] |
| E6 | Asian range, FX vs index | fxbacktest (A) vs session_stats (B) | A: EURUSD both sides 37.7% vs 48.9% Gaussian. B (day-bootstrap, 20:00-00:00): EURUSD 63.5 vs 62.4 (≈ null); index futures, opposite side after the first break +3.5 to +6.2 pp | moderate | [B-corrected] |
| E7 | First-break fade / ORB | fxbacktest (as reported by A); Mesfin 2026 | FX fade 49.4% (ns); London ORB 50.3%; MNQ 09:30-09:55 ORB T 0.88-1.50, unstable across years | moderate | [A]+[B] |
| E8 | Midnight-open revisit | tradingstats (as reported by A); edgeful, LuxAlgo (B2); B `mo_test.py` | 65.6-68.0% (A); 57-74% by open side (edgeful/LuxAlgo). **Excess over neighbouring opens at equal distance: +0.3 ± 1.1 pp** (1,412 days) | none (as a magnet) | [B-corrected]+[B2] |
| E9 | ON range in RTH | tradingstats NQ 2,827 days (A); NexusFi (B2); session_stats | At least one side 94.2% (A) / 96.4% (NexusFi: high 66, low 59, both 29%); vs null: none 3.6-4.0% vs 7.4-8.2% | moderate | [A]+[B]+[B2] |
| E10 | Intraday momentum | Gao et al. JFE 2018 (B2-verified); Mesfin 2026 | R² 1.6% IS / 1.2% OOS; 0 of 14 MNQ families pass after costs | moderate (exists) / none (usable) | [B-corrected] |
| E11 | Overnight drift | NY Fed SR917 / RFS 2023; Liberty Street, July 2026 (both B2-verified) | About 3.7% a year at 02-03 ET (1.48 bp/day); about zero since 2021 | strong but decayed | [B2 verified] |
| E12 | Weekday volatility | B `weekday.py` (CME 1h, 1 year); Ederington & Lee | Full-day range/ADR: Tue 0.90-0.98, Fri 1.08-1.11; variance factor 0.80-1.23; mostly the release calendar | moderate | [B-corrected]+[B2] |
| E13 | Weekly extreme timing | Arcsine; session_stats shuffle | Mon 29.5 / Tue 14.1 / Wed 12.8 / Thu 14.1 / Fri 29.5% null; real data = shuffle | strong (null) | [A]+[B] |
| E14 | Silver Bullet | tradestar (A); trade_mgmt P3; other mechanical tests (B2); B window test | 38.9% win at 1:1; PF 0.66-0.94; 0/10 variants profitable; EURUSD bot 29.6% win, PF 0.81; window residual +0.2 ± 0.6 pp | none (claim); moderate (negative) | [B]+[B2] |
| E15 | Macros | B `macro_test.py`; B2 attribution | All macro windows +0.6 ± 0.5 pp; no volatility bump; 09:50-10:10 excess is index-only (cash-open drive) | none | [B]+[B2-corrected] |
| E16 | IPDA / N-day extremes | classic_levels T2; Driessen-Lin-Van Hemert 2013 | 20/60/252-day extremes within ±0.8 pp of random; 52-week extremes: IV and beta fall on approach, realised variance +19% / +43% after a break | none (as magnets); strong (as volatility barriers, equities) | [B-corrected]+[B2] |
| E17 | Engine PoT bias by hour | B `tod_calib.py`, `clock_sim2.py`; B2 rerun | 5m H30: 07-09 ET -12 to -17 pp, 11:00 +10, 16:00 +8, 21:00 +11; mean \|bias\| 7.3 pp. 1H H12: 8.4 pp. 1H H30: 3.1 pp | moderate (measured) | [B]+[B2] |
| E18 | Time-aware PoT gains | B `clock_sim2.py`; B2 `clock_sim_lm.py` (causal, walk-forward) | See §2.2 | moderate | [B]+[B2] |
| E19 | Session-window bug size | B `sess_bug.py` | Bar-open: 76% of days wrong, 14-16% of the day range; overlap: 35%, 6-7%; NY open anchor off by a median 15.6% of the day range | strong (measured + doc) | [B] |
| E20 | Horizon collapse of "taken today" | session_stats | 0.2-0.35 ADR PDH/PDL: 64 / 57 / 47 / 19% from Asia / London / NY AM / NY PM | moderate | [B cross-ref] |
| E21 | Vol-time ETA | quant_pot | Rank correlation +0.11 / +0.16 / +0.22 vs -0.09 (constant σ) | moderate | [B cross-ref] |
| E22 | Asia expansion bars reverse | Mesfin 2026 (preprint) | MNQ, 1.5x-range Asia bars: next-bar T = -10.96 | weak-moderate | [B] |
| E23 | Arcsine "first-hour colour" | A's maths | `0.5 + asin(ρ)/π` with ρ ≈ 0.45-0.49 gives 65-66% vs 66.2% observed | strong | [A] |
| E24 | Power of 3 / AMD on NQ | Taylor 2026, arXiv:2610.35887 (preprint, code public), N = 484 | Bull 46.9% (ns), bear 39.9% (inverted); trend-aligned 62-71%, counter 25-30%; 57% of targets delivered before 09:40 | moderate (negative) | [B2] |
| E25 | US cash-open drive | B2 `macro_attr2.py` (1-min ES/NQ/YM/RTY, 60 days) | 20-min windows starting 09:20-09:59: +10.5 to +14.8 pp over the clock (SE 1.6-3.2); 08:30 -2.8; after 10:00 +1; CL/GC null | moderate | [B2] |
| E26 | FX fixes | Evans 2018 (JBF); Krohn-Mueller-Whelan 2024 (J. Finance); Michelberger & Witte 2016; B2 CME window test | Pre/post-fix reversal in all 21 pairs; "W"-shaped dollar, about 2 bp daily swings; volatility spike in the fix minute; CME 10:50-11:10 residual -1.1 ± 2.2 pp | strong (exists), negligible for PoT | [B2] |
| E27 | FX home-hours depreciation | Breedon & Ranaldo 2013 (JMCB) | Currencies weaken in their own trading hours; order flow matches | strong, small | [B2] |
| E28 | Pre-FOMC drift | Lucca & Moench 2015; Liberty Street 2018; Kurov-Wolfe-Gilbert | +49 bp (1994-2011); about 40 bp on press-conference days to 2018; weaker since 2016 | strong but decayed | [B2-corrected] |
| E29 | Opening gaps (NDOG/NWOG/ORG) | session_stats `gaps.py` | S&P cash gaps -26.8 pp vs mirror; EURUSD weekend +0.2; BTC CME gap -5.8; index ORG +6.9 (n 204, ns) | none (magnet) | [B2 cross-ref] |
| E30 | EDGE inflated by clock timing | skeptic §2.3 F (16 seeds × 12 cells) | No-skill pickers: busy +2-3 pp, quiet -2 to -3 pp; mirror control: mean \|z\| 0.69 → 0.24 | moderate | [B2 cross-ref] (G16 magnitude) |
| E31 | ICT AMD timing vs London | Taylor 2026 | Of 223 pre-swept days: 31% delivered 05-06, 55% by 08:00, 80% by 09:00; plus 64 days inside London | moderate | [B2] |

### 2.2 Simulations of time-aware PoT models (real CME data, causal) [B; B2 additions]

**Setup** (`clock_sim2.py`; B2's `clock_sim_lm.py` adds landmark blocks):
- Rows: quant_pot's walk-forward rows. Every bar, both sides, distances 0.5-6 ATR; y = touched within H.
- Comparator: the engine's default Empirical model (`p_eng_emp`).
- Models, simulated bar by bar as they would run in Pine:
  - `todK`: the engine ATR surface split by K NY-time blocks, partially pooled to the all-hours surface, `p = (nb·pb + 60·pPool)/(nb + 60)` (nb in effective windows, n/(0.6H)); then the engine's analytic prior.
  - `tod12` (B2): 12 **landmark** blocks: 00-02, 02-05, 05-07, 07-08:30, 08:30-09:30, 09:30-10, 10-12, 12-13:30, 13:30-16, 16-18, 18-20, 20-24.
  - `clkB`: the robust clock (spec in TIME-3) → a z-unit surface with an analytic clock prior.
  - `clkA`: the analytic clock only.

Brier gain vs the engine:

| Setting | rows | engine Brier | clkA | clkB | tod8 | tod12 (landmark) | tod24 | clkB+tod8 |
|---|---|---|---|---|---|---|---|---|
| 5-min H = 30 | 1.20 M | 0.1905 | +3.90% | **+3.86%** | +2.18% | +2.20% | +1.88% | +3.81% |
| 5-min H = 60 | 1.19 M | 0.1903 | +5.52% | **+5.45%** | +2.15% | | +1.33% | +5.40% |
| 1-hour H = 30 | 0.41 M | 0.1883 | -2.97% | -1.05% | **+0.38%** | +0.33% | +0.20% | -1.02% |
| 1-hour H = 12 | 0.41 M | 0.1766 | +0.92% | +3.86% | +3.75% | +3.20% | +2.41% | **+4.12%** |

Per symbol, clkB and tod8:

| Setting | CL | ES | GC | NQ | RTY | YM |
|---|---|---|---|---|---|---|
| 5m H30 clkB | +1.6 | +3.5 | +1.8 | +4.1 | +5.0 | +6.6 |
| 5m H30 tod8 | +1.1 | +2.0 | +1.2 | +2.1 | +2.9 | +3.6 |
| 1h H30 clkB | +0.6 | +1.9 | **-9.8** | +2.0 | +0.1 | -0.4 |
| 1h H30 tod8 | +0.2 | +0.4 | +0.1 | +0.4 | +0.5 | +0.7 |
| 1h H12 clkB | +2.6 | +6.2 | **-6.9** | +6.9 | +7.4 | +6.3 |
| 1h H12 tod8 | +1.8 | +4.0 | +0.1 | +4.2 | +5.7 | +5.9 |

**Further results:**
- **Calibration (ECE, 5m H30):** engine 0.012; tod8 0.009; tod12 0.009; clkB 0.015; clkA 0.030. The z-surface keeps the analytic clock honest.
- **Hour bias, mean \|pred - obs\| over NY hours:**

  | Setting | engine | tod8 | tod12 | clkB | clkB+tod8 |
  |---|---|---|---|---|---|
  | 5m H30 | 7.3 pp | 4.7 | 4.9 | 2.1 | 1.8 |
  | 1h H12 | 8.4 pp | 5.0 | 5.6 | 2.4 | 1.9 |

- **Example hours, 5m H30 (observed / engine / clkB):**

  | Hour | Observed | Engine | clkB |
  |---|---|---|---|
  | 07:00 | 0.683 | 0.524 | 0.647 |
  | 08:00 | 0.691 | 0.523 | 0.675 |
  | 11:00 | 0.421 | 0.523 | 0.442 |
  | 16:00 | 0.445 | 0.527 | 0.468 |
  | 21:00 | 0.420 | 0.527 | 0.417 |

- **Landmark blocks (B2).** They align cells with the killzones and isolate the 09:30-10:00 cash-open drive, but they do not beat uniform 3-hour blocks: thinner cells, and on 1H some blocks hold one or no bar opens. Keep tod8.
- **A's spec as written** (multiplicative EWMA, close-to-close r², 40-day memory started at 1.0, no floors):
  - without a warm start: clkA +0.82%, clkB +0.96% (`out_clock_variants_H30.txt`);
  - with a 1/n warm start: buckets hit zero on zero-change bars, and the run failed (division by zero);
  - with a range-based variance: GC fell to -23.9%.
  - **The robust spec is required.**
- **GC failure on 1H.** GC 1h has 768 jump bars (more than 8x the rolling median |r|), irregular hourly coverage, and a 3x volatility regime shift in Jan-Mar 2026. A fast-level clock z-surface is fragile there; the ATR surface is not. **The clock must be switched per chart by measured skill (TIME-4)**, not on by default.

### 2.3 Arcsine and random-walk baselines
- See §1.15.
- A's Gaussian random-walk baselines (`ict_time_calc/baselines*.py`) remain a useful illustration.
- For session statistics they are **superseded** by session_stats' day-bootstrap null; for anchors, by B's anchor-neighbour test; for macros, by B's clock-residual test. All three keep the real path features: intraday mean reversion, fat tails and clustering.

---

## 3. Engine gap analysis (baseline_v2.pine; every line reference re-checked)

| ID | Concept | Status | Lines | What the engine does / what differs |
|---|---|---|---|---|
| G1 | Volatility clock in PoT / reach / race | **missing** | 914-917, 1303-1311, 1314-1322, 1343-1364, 665, 1948, 2066-2067 | `potSig = ta.stdev(chg, potLen)` (916) is a trailing, time-blind σ. It feeds the analytic PoT (1304), the baseline (1315), the race (1360-1363) and the proximity reach (665: `f_pot(dist, sig, mu, potH)`, with `sig = nz(potSig)` passed at 1948). On 5m charts the forward variance swings 0.2x-4.7x by hour. [A] |
| G2 | Empirical surface conditioning | **wrong for intraday timing** [B-corrected from "partial"] | 1059-1062, 1284-1300, 1527-1532, 2108-2111 | Excursions are normalised by `atr[H]` and split only by HTF bias (rows `bias+1`), pooled over all hours. This is the default model: well calibrated unconditionally, but **biased -17 to +11 pp by hour** on 5m and 8.4 pp mean on 1H with H = 12 (E17). `f_reachD` and the reach bands inherit it. The surface learns on every confirmed bar (1527-1532 are not gated by `inCalc`, 1519), which suits a split. [B; B2] |
| G3 | Session membership on coarse bars | **wrong** (1H) | 798-803, 835-863, 948-950, 964-966, 971-974; inputs 107-109, 220-226 | `time(timeframe.period, sess, tz)` is a bar-**open** test (docs re-read). On 1H futures charts: NY AM range = 10:00-12:00 (**wrong on 76% of days**, E19); NY open anchor = the 10:00 open; the NY PM killzone starts at 14:00. Asia, London and midnight are exact on 1H. On 4H futures/FX charts `midOpen` stays `na` forever (no bar opens in 00:00-01:00, and `var o = na` is never set), so it drops out of confluence (1931); `nyOpen` = the 10:00 open. [A; B quantified] |
| G4 | Killzone set | **partial** | 223-226, 587-594, 970-976 | Asia, London, NY AM 07-10 and NY PM exist; there is no London close (10-12). The Asian KZ is the 20:00-00:00 session, where ICT's original window is 20:00-22:00 (harmless as an activity label). [B2] On 1H, `kz == 0` (OFF) covers the bars at 00, 01, 05, 06, 10-13 and 16-19: 12 of 24 hours, with hysteresis doubled (976). |
| G5 | Killzone affinity | **wrong** (unsupported prior) | 596-602, applied 1941 | London ×1.20 Asia pools, ×1.10 PD; NY AM ×1.20 London, ×1.15 PD, ×1.05 Asia; NY PM ×1.15 NY AM, ×1.10 PD. Applied regardless of distance and forward variance. session_stats: session/day pools are taken at the null rate ±3 pp. The real residuals (Asia two-sided raids on index futures; the cash-open drive, which takes *any* nearby pool) are not what `f_kzAff` encodes. skeptic SKEP-6 also proposes `useKzAff = false` (null-default modifiers). [A; B; B2] |
| G6 | Session ranges as liquidity | **partial** | 106-109, 945-951, 1800-1809, 316, 505-529 | Asia, London and NY AM H/L are pushed at session end (`useSess and intraOK`, ≤ 1H), anchored to the print bar. **Missing:** ONH/ONL (18:00-09:30), which also covers the 05:00-09:30 pre-market extremes that no current pool holds. NY PM and lunch ranges are low value. [A; B narrowed] |
| G7 | Midnight open | **present as confluence; no target needed** [B-corrected] | 220, 964, 1931, 677 | No excess over any recent open (E8). The time opens (`midOpen`, `ldnOpen`, `nyOpen` in `anchors`, 1931; +0.35 per hit, 677) are in the feature spec ("Session Opens"). Keep them, but exact (G3) and down-weightable by calibration. [B2-corrected: B's first pass removed them by default] |
| G8 | 08:30 / 09:30 / weekly opens; NDOG / NWOG / ORG | **partial** | 221-222, 965-966 | London 02:00 and NY 09:30 opens are confluence anchors (09:30 wrong on 1H). No 08:30 open, weekly open or opening gaps; all low value as levels (E29; weekly and monthly opens are barriers). [B; B2] |
| G9 | Macros, Silver Bullet | **missing** (correctly) | none | Tested null (E14, E15). The 09:50-10:10 excess is the index cash-open drive (E25), which a time-of-day surface learns. [B; B2] |
| G10 | Power of 3 / Judas | **partial** (implicit) and unsupported | 1580-1582 | `liqEvt`: raid + close back inside = reversal, close beyond = continuation, at any time. E24: the AMD direction carries no information beyond trend. Covered by ict_liq ICT-2 (learn the sign). [A; B2] |
| G11 | CBDR / Asian / Flout SD | **missing** (correctly) | none | No evidence; redundant with a clock-aware distance. [A] |
| G12 | Weekday | **missing** | none | The weekday variance factor is ±10% in σ (E12), mostly release-calendar driven. It belongs in the clock (TIME-3 `c[d]`) and TIME-8, not in profiles. [B; B2] |
| G13 | IPDA 20/40/60 | **missing** (acceptable) | (PWH/PWL 1795-1799; HTF pivots 1782-1789; htfEQ 968) | N-day extremes are reached at the random-level rate (E16). Optional at most, tier ≤ 0.70. [B] |
| G14 | Drifts | **n/a** | 917 (`potMu`, `driftW` 185) | The overnight and pre-FOMC drifts have decayed (E11, E28). quant_pot QPOT-01: remove drift from all PoT maths (the 0.5 × 50-bar drift costs 3.7-7.1% log-loss). [B; B2] |
| G15 | Scheduled news | **missing** | none | No calendar in Pine. Release hours run about 4-27x the variance of a normal hour (E3). |
| G16 | Ledger baseline and PoT grading | **partial / biased** | 1313-1322, 1426-1431, 1433-1459, 1461-1499, 2037-2045 | `pBase` uses the same time-blind model, so EDGE can credit timing as skill. Trials open **whenever the active DOL has no open trial** (2037-2045): at a new DOL, and right after the previous trial on the same DOL resolves (hit, or H bars: 1453-1456). Trial starts therefore cluster where DOL turnover is high (active hours). **Magnitude now measured** (E30): ±2-3 pp per clock window for no-skill pickers, the same size as the edges the evidence allows. The displayed PoT is never stored or graded (QPOT-04). [B; B2] |
| G17 | Session horizon and clock-time ETA | **partial** | 2105-2126, 2240-2243 | `ETA\|hit` = median bars-to-hit of past hits within ±0.5 ATR (bars, not clock time). H is a fixed bar count (305), so "before the NY close?" cannot be asked. Scalping mode (exec 5m) and Day Trading mode (exec 1H) share the same H = 30, i.e. 2.5 hours vs 30 hours. [A; B2] |
| G18 | Intraday momentum | **n/a** [B-corrected] | 1536-1541, 1893-1894 | The generic displacement term with a 12-bar half-life is fine. No session-return tilt (E10). |
| G19 | Session time zone for learned statistics | **n/a today** [B] | 220 (`tz`) | Every new time statistic (clock, time-of-day surface, killzone ledger) must key on `tz` (NY by default), not UTC. QPOT-02 as written uses UTC. |
| G20 | Killzones on 2H/4H charts | **wrong** [B2, new] | 970-976, 1941, 2012 | Sessions are gated to ≤ 1H (`intraOK`, 947), killzones are not. 4H futures bars open at 18, 22, 02, 06, 10, 14: kz = OFF, ASIA, LONDON, OFF, **OFF**, NY PM. The 10:00-14:00 bar is "OFF-KZ" and gets doubled hysteresis (`need`, 2012) and no affinity. On 2H the 10:00 and 12:00 bars are OFF. The labels and hysteresis are arbitrary there. |
| G21 | London windows across DST mismatch | **minor** [B2, new] | 221, 224, 108 | London windows are fixed in NY time. For about 4 weeks a year (US on DST, UK not), the London open is 04:00 NY, so the London killzone and range cover the hour *before* the open. The volatility clock (keyed to NY) smears too. |

---

## 4. Proposals (best first; maximum 12)

General notes for all specs:
- All learning and state updates run on `barstate.isconfirmed` only.
- Functions are declared before use; globals before the functions that read them. New inputs go in `G_POT` / `G_KEY` / `G_CONF` / `G_FLOW`, and use `display = display.none` (the overhaul's legend fix).
- Built-ins were checked in the local v6 reference:
  - `dayofmonth(time, timezone)`, `dayofweek(time, timezone)`, `hour(time, timezone)`, `minute(time, timezone)` (reference/time.md 170, 191, 210, 229);
  - `time(timeframe, session, timezone, bars_back)`, with bars_back from -1 to -500 projecting future bars (time.md 290-301);
  - `str.format_time(time, format, timezone)` (str.md 182);
  - `input.time` (input.md 488);
  - `request.security_lower_tf(..., ignore_invalid_timeframe, calc_bars_count)` (request.md 289).
- Limits:
  - arrays ≤ 100,000 elements (limitations.md 367);
  - 40 unique `request.*` calls (limitations.md 206); the engine uses 7;
  - `max_bars_back = 500` (line 31), so any `x[H]` with H ≤ 450 is safe;
  - 100k intrabars on non-professional plans (limitations.md 263-269).
- Every proposal keeps the engine non-repainting. Every new state update reads closed bars only. Lower-timeframe arrays are consumed only on confirmed chart bars, as the VP feed does (982-1015).

### TIME-1 (P1, effort M): exact session windows and anchors; London close killzone; killzones only on charts ≤ 1H; London DST
- **Why.**
  - On the default Day Trading chart (1H) the NY AM pools are wrong on 76% of days, by 14-16% of the day range (E19).
  - The NY open anchor is the 10:00 open; the NY PM killzone starts at 14:00.
  - On 2H/4H the killzone label and the hysteresis are arbitrary (G20).
  - These are visible errors on the user's chart, with strong evidence (doc quote plus measurement).
- **(a) Overlap membership** (all intraday TFs ≤ 1H).
  - Parse each session input once at global scope:
    ```
    f_hhmm(string s, int at) => int(str.tonumber(str.substring(s, at, at + 2))) * 60 + int(str.tonumber(str.substring(s, at + 2, at + 4)))
    // sM = f_hhmm(sess, 0); eM = f_hhmm(sess, 5); eM <= sM means "wraps midnight" ("2000-0000" -> [1200,1440) and an empty [0,0))
    ```
  - `chMin = math.max(1, int(chartS / 60))`; `b0 = hour(time, tz) * 60 + minute(time, tz)`.
  - `f_ov(a0, a1, s, e) => a0 < e and s < a1`.
  - `f_inWin(sM, eM)`: the window is `[sM, eM)`, or `[sM, 1440) ∪ [0, eM)` when `eM <= sM`. Test the bar `[b0, b0 + chMin)` and its copy shifted by -1440 (bars that run past midnight). Also return `exact = b0 >= sM_seg and b0 + chMin <= eM_seg` for the anchor flag.
  - Replace `not na(time(timeframe.period, sess, tz))` at 799, 836 and 971-974 with `f_inWin(...)`.
  - This alone cuts the NY AM error to 35% of days and 6-7% of the range (the straddling 09:00 bar adds pre-open prices).
- **(b) Exact bounds on charts of 1H and below with :30 boundaries.** One new request at global scope:
  ```
  [ltT, ltO, ltH, ltL] = request.security_lower_tf(syminfo.tickerid, "30", [time, open, high, low], ignore_invalid_timeframe = true)
  ```
  - It is used only when `chartS > 1800 and intraOK`. On 1H that is 2 intrabars per bar, so 100k intrabars cover 50k chart bars.
  - `f_sessTrackLT(sM, eM)` is called on every bar; its body runs only on `barstate.isconfirmed`:
    - `for [j, t] in ltT`; membership `m = hour(t, tz)*60 + minute(t, tz)` inside the window (exact on a 30-minute grid);
    - `var` hi/lo extended from `ltH.get(j)` / `ltL.get(j)`, anchored at the chart `bar_index`;
    - `var bool wasIn` carries state across intrabars and bars;
    - it emits when the first out-of-session intrabar follows in-session ones, as the same tuple as `f_sessTrack`.
  - `f_sessOpenLT` takes `ltO.get(j)` of the first in-session intrabar. This gives the exact 09:30 open on 1H.
  - Input: `exactSess = input.bool(true, "Exact Session Bounds (30m data)", group = G_KEY)`.
  - On charts ≤ 30m, `ignore_invalid_timeframe` returns `na` arrays; fall back to (a), which is exact there.
- **(c) London close killzone.**
  - `kzLC = input.session("1000-1200", "London Close Killzone", group = G_CONF)` as kz 5.
  - `f_kzName`: 5 → "LDN CLOSE KZ"; `f_kzAff`: 5 → 1.0.
  - Precedence: London > NY AM > London close > NY PM > Asia.
- **(d) Killzones only on charts ≤ 1H.** At 975:
  ```
  int kz = not timeframe.isintraday or chartS > 3600 ? -1 : inKzLo ? 2 : inKzNA ? 3 : inKzLC ? 5 : inKzNP ? 4 : inKzAs ? 1 : 0
  ```
  - On 2H/4H this shows "HTF", with no off-killzone doubling and no affinity.
- **(e) London DST tracking.**
  - Input: `bool ldnDst = input.bool(true, "Track London DST", group = G_CONF)`.
  - `int offLN = (hour(time, "Europe/London") - hour(time, tz) + 24) % 24`.
  - When `ldnDst and offLN == 4` (mismatch weeks), add 60 minutes to `sM` and `eM` of the London windows (`sessLo`, `sessLdn`, `kzLo`, and `kzLC`), so they keep their London local time. This is trivial once (a) exists.
- **(f) Session opens in confluence** (feature spec: "Session Opens").
  - Keep them **on** by default, using the exact opens from (b).
  - Add `openConf = input.bool(true, "Session Opens as Confluence", group = G_CONF)`; when off, leave `midOpen`, `ldnOpen` and `nyOpen` out of `anchors` (1931).
  - Show "≈" in the HUD/tooltip for any approximate anchor (`exact == false`).
  - The evidence that opens are not magnets (E8; classic_levels T5; calib_ml CAL-3, confluence -0.25 logit) goes in the tooltip. `useCal` per-group calibration can down-weight them.
- **Risk.**
  - Lower-TF arrays can differ between realtime and history; consume them only on confirmed bars.
  - One more request (8 of 40).
  - The midnight-wrapping logic needs unit cases: Asia 2000-0000, ON 1800-0930, a 1H bar at 23:00.

### TIME-2 (P1, effort M): NY time-of-day dimension in the empirical PoT surface, with partial pooling
- **Why.**
  - The default PoT is biased by up to 17 pp by hour (E17). This is the smallest change that removes a third to a half of that bias.
  - It improved Brier in all 24 symbol × setting tests: +0.1 to +5.9%, ECE ≤ 0.015.
  - Because it is empirical, it also learns the effect beyond volatility (the cash-open drive, E25), which a pure clock cannot.
  - It also fixes the time-blind EDGE baseline (`f_potBase` uses the same surface).
- **Inputs** (G_POT):
  ```
  bool todOn = input.bool(true, "Time-of-Day PoT Surface", group = G_POT, display = display.none,
    tooltip = "Learns how far price travels within the horizon separately for each 3-hour block of the New York day. A block borrows from the all-hours surface until it has enough history.")
  ```
- **Derived** (after 309): `const int NQ = 8`, `const int NQ1 = 9` (row 8 = pooled), `const float TODM = 60.0`.
- **Series** (after 920):
  ```
  int todQ = todOn and timeframe.isintraday and chartS <= 3600 ? int(hour(time, tz) / 3) : NQ   // 0 = 00-03 … 7 = 21-24
  ```
  - Charts above 1H use pooled rows only: at H ≥ 30 the clock averages out.
- **State** (1061-1062): `var array<int> sUp = array.new<int>(3 * NQ1 * NB1, 0)`, and the same for `sDn` (1,647 ints each). Row index = `regime * NQ1 + q`; `f_bump` and `f_surv` take the row unchanged.
- **Step 0** (1528-1532) bumps both the cell and the pooled row:
  ```
  int   bH = htfBias[H]
  int   qH = todQ[H]
  float xu = (fwdHi - close[H]) / aH
  float xd = (close[H] - fwdLo) / aH
  f_bump(sUp, (bH + 1) * NQ1 + NQ, xu)
  f_bump(sDn, (1 - bH) * NQ1 + NQ, xd)
  if qH < NQ
      f_bump(sUp, (bH + 1) * NQ1 + qH, xu)
      f_bump(sDn, (1 - bH) * NQ1 + qH, xd)
  ```
- **`f_empPoT`** (1284) gains `int q`:
  - pooled `pP`, `nP` from row `r*NQ1+NQ`, with the current gate and fallback (the all-regime sum `nAll` uses the pooled rows `(k*NQ1+NQ)*NB1`);
  - cell `pC`, `nC` from row `r*NQ1+q` (skipped when `q == NQ`);
  - `nCe = nC / max(1, 0.6*H)`;
  - `p = (nCe*pC + TODM*pP)/(nCe + TODM)`;
  - return `[p, nP]`, so the analytic blend weight is unchanged.
- **Callers:**
  - `f_potModel` (1307) and `f_potBase` (1318) pass `todQ` (the live bar's block for the live PoT);
  - `f_reachD` and the reach bands (2108-2111) use the cell row when its count is ≥ `max(150, 20*H)`, else the pooled row.
- **Cost:** O(NB) per bump, twice per bar. Memory 3.3k ints.
- **Evidence:** moderate (§2.2), consistent with QPOT-03 (whose fallback used session buckets).
- **Tested and rejected:** 12 landmark blocks (§2.2). Hourly blocks (tod24) are worse on 5m and 1H. On 1-minute charts with a short H, hourly blocks may pay; untested.
- **Risk:**
  - Slower convergence per cell (handled by pooling).
  - The DST shift of the London open is about 1 hour for about 4 weeks a year; a 3-hour block absorbs most of it.

### TIME-3 (P1, effort L): robust NY-keyed volatility clock with a z-unit empirical surface (gated)
- **Why.**
  - On 5m, and on 1H with H ≤ about a session, it is the largest PoT improvement measured in any sibling study: +3.9% (5m H30), +5.5% (5m H60), +3.9% (1H H12); all 6 symbols positive on 5m. It cuts the hour bias to 2.1 pp.
  - It is the quantitative, symbol-learned form of killzones, sessions, the weekday effect and Dacorogna's ϑ-time.
  - It yields the forward variance needed by TIME-5, TIME-6 and TIME-8.
- **Inputs** (G_POT):
  ```
  string clkMode = input.string("Auto", "Volatility Clock", options = ["Auto", "On", "Off"], group = G_POT, display = display.none,
    tooltip = "Learns this symbol's volatility by New York time of day and weekday, and uses the variance expected in the coming bars. Auto: used only where it beats the plain surface on this chart (see PoT MODEL in the panel).")
  int   clkMin = input.int(30, "Clock Bucket (minutes)", options = [15, 30, 60], group = G_POT, display = display.none)
  float clkMem = input.float(40.0, "Clock Memory (days)", minval = 5.0, step = 5.0, group = G_POT, display = display.none)
  ```
- **Derived** (after 309):
  ```
  int   chMin = math.max(1, int(chartS / 60))
  int   bkMin = math.max(clkMin, chMin)
  bool  clkOK = clkMode != "Off" and timeframe.isintraday and bkMin <= 240 and 1440 % bkMin == 0
  int   NBK   = clkOK ? 1440 / bkMin : 1
  float bpb   = bkMin * 60.0 / chartS
  ```
- **Series** (after 917): a log Garman-Klass-plus-gap variance proxy:
  ```
  float lHL  = math.log(high / low)
  float lCO  = math.log(close / open)
  float lOC  = na(close[1]) ? 0.0 : math.log(open / close[1])
  float xVar = math.max(0.0, 0.5 * lHL * lHL - (2.0 * math.log(2.0) - 1.0) * lCO * lCO) + lOC * lOC
  int   cB   = int((hour(time, tz) * 60 + minute(time, tz)) / bkMin)
  int   cD   = dayofweek(time, tz) - 1
  ```
- **State** (after 1080):
  - floats: `clkA[NBK]` (init 1), `clkD[7]` (init 1), `clkLs`, `clkLf` (na);
  - ints: `clkNb[NBK]`, `clkNd[7]`, `clkC[7*NBK]`, `clkDy`.
- **Learning.** Global scope, right after the series; confirmed bars; **all** loaded bars, not only `calcBars`. The robust form, as simulated:
  ```
  if clkOK and barstate.isconfirmed and low > 0
      float s0 = math.max(clkA.get(cB) * clkD.get(cD), 0.05)
      if na(clkLs)
          clkLs := math.max(xVar, 1e-12)
      float ratio = math.min(xVar / math.max(clkLs, 1e-12), 50.0)
      clkNb.set(cB, clkNb.get(cB) + 1)
      clkNd.set(cD, clkNd.get(cD) + 1)
      float aB = math.max(1.0 - math.pow(0.5, 1.0 / (clkMem * bpb)), 1.0 / clkNb.get(cB))   // cumulative mean while young
      clkA.set(cB, math.max(0.05, clkA.get(cB) + aB * (ratio / clkD.get(cD) - clkA.get(cB)))) // additive, floored
      float aD = math.max(1.0 - math.pow(0.5, 1.0 / (clkMem * NBK * bpb / 5.0)), 1.0 / clkNd.get(cD))
      clkD.set(cD, math.max(0.2, clkD.get(cD) + aD * (ratio / clkA.get(cB) - clkD.get(cD))))
      float y = xVar / s0
      clkLs += (1.0 - math.pow(0.5, 1.0 / (5.0 * NBK * bpb))) * (math.min(y, 25.0 * clkLs) - clkLs)
      clkLf := na(clkLf) ? y : clkLf + 2.0 / (potLen + 1.0) * (math.min(y, 25.0 * clkLf) - clkLf)
      clkLf := math.max(clkLf, 0.2 * clkLs)
      clkC.set(cD * NBK + cB, clkC.get(cD * NBK + cB) + 1)
      if timeframe.change("D")
          clkDy += 1
          // renormalise: bar-weighted mean of clkA (weights Σ_d clkC) = 1, likewise clkD; O(7·NBK) once a day
  ```
- **Why this form.** It differs from A's spec in four ways:
  - an additive EWMA of a deseasonalised ratio, instead of a multiplicative update;
  - a cumulative-mean warm start (`1/n`);
  - floors on the factors and the level;
  - a range-based variance proxy.
  A's multiplicative form zeroes a bucket on a zero-range bar and gained only +0.8 to +1.0% (§2.2).
- **Forward variance `f_fwdVar(h)`.** A grid walk:
  - the remainder of the current bucket, then whole open cells;
  - a cell is open when `clkC ≥ 0.3·(clkDy/7)·bpb` (this skips halts, weekends and closed hours);
  - guard `7·NBK + 8` iterations;
  - returns `v · clkLf`, in log variance;
  - computed **once per bar** at global scope (`fwdV`), never per level.
  - Optional refinement (QPOT-02): a mean-reverting level path `clkLs + φ^j (clkLf - clkLs)` with φ = 0.5^(1/30).
- **Phase B, the z-surface:**
  - `float fwdSd = clkOK and clkDy >= 5 ? close * math.sqrt(fwdV) : na` (a series, so `fwdSd[H]` is valid).
  - New arrays `zUp` / `zDn` with the same row layout as TIME-2 (regime × NQ1 tod rows; the tod split adds +0.3% on 1H H12, and nothing on 5m), grid `bZ = 5.0 / NB`. Bump in step 0 with `(fwdHi - close[H]) / fwdSd[H]`.
  - Query: `z = d / fwdSd`.
  - Prior: the driftless `pA = f_erfc(z / math.sqrt(2.0))`, capped at 0.95 (QPOT-01).
  - Blend `(nEff·pE + priorM·pA)/(nEff + priorM)` as now.
- **Wiring:**
  - A model switch `potSel` (0 pooled ATR, 1 time-of-day ATR, 2 clock z), set by TIME-4 when `clkMode = "Auto"`, or forced by "On".
  - Reach (665, via `sig` at 1948) and the race (1360) use `sigH = close*math.sqrt(fwdV/H)` when `potSel == 2`.
- **Cost:**
  - the walk is about H/bpb plus skipped cells (5 iterations for H = 30 on 5m; ≤ 7·NBK + 8 over weekends);
  - memory < 1k;
  - no new request.
- **Evidence:** strong (concept: E1, E2, E3), moderate (B's test, §2.2).
- **Risk:**
  - GC-type jump series and regime shifts: the 1H failure (-9.8%) is why the default is "Auto" (scorecard-gated).
  - Holidays and early closes overstate V.
  - The US/UK DST mismatch smears the London bucket for about 4 weeks a year (TIME-1e handles the windows, not the clock).
  - The empirical z-surface needs warm-up; it falls back to pooled until `nMin`.

### TIME-4 (P1, effort M): per-chart PoT scorecard with model auto-selection, a time-neutral EDGE, and EDGE by killzone
- **Why.**
  - The best PoT model depends on timeframe, horizon and symbol (§2.2): the clock wins on 5m, loses on GC 1H, and ties on 1H H30. Only the user's chart can decide.
  - DOL trials are too few to detect 1-4% Brier differences; cheap **probes** are not (B's evaluation design, ported to Pine).
  - The EDGE statistic is biased ±2-3 pp by clock timing (E30, G16), as large as the edges the evidence allows.
- **Probes.** At every confirmed bar, 6 probes (k = 1, 2, 3 ATR × side), with the PoT of each candidate model m ∈ {0 pooled, 1 time-of-day (TIME-2), 2 clock (TIME-3)}:
  - Ring buffer: `var array<float> prb = array.new<float>((H + 1) * 18, na)`, index `((bar_index % (H+1))*6 + j)*3 + m`.
  - At bar t ≥ H, resolve slot `(t - H) % (H+1)`: `y = side == 1 ? fwdHi - close[H] >= k*atr[H] : close[H] - fwdLo >= k*atr[H]` (the same window as step 0).
  - For each model accumulate `n`, `Σ(p - y)²`, and the per-bar difference `dB_m = Σ_j[(p_m - y)² - (p_0 - y)²]`.
  - Use 2H-bar block sums for a cluster-robust z (the same pattern as `cluSt`, 1463-1469): `var array<float> scSt = array.new<float>(3 * 5, 0.0)`.
- **Selection.**
  - Once a day (`timeframe.change("D")`): `potSel` = the model with the lowest Brier among those with ≥ 2,000 resolved probe bars **and** z ≤ -2 against model 0. Otherwise 0.
  - Hold the choice at least 5 days, so the display does not flicker.
  - All inputs are confirmed history, so it is non-repainting.
- **Time-neutral EDGE.**
  - `f_potBase` (1314) uses the selected model, driftless. EDGE then measures level selection net of timing.
  - Pair it with skeptic **SKEP-2's mirror control** (a mirrored level on the opposite side, opened on the same bar), which removes what remains of the clock bias (mean |z| 0.69 → 0.24 in E30). The two fixes are complementary: a better baseline, then a placebo that shares its errors.
- **Trials** (375-395) gain `float pPot` (the displayed PoT at open, QPOT-04) and `int kz0`. `f_book` adds `kzN/kzK/kzE` arrays (size 7, index `kz0 + 1`) holding hits vs baseline by killzone.
- **Panel** (Terminal, Accuracy = Full):
  - `PoT MODEL  CLOCK ✓ · Brier -3.9% vs surface · z 6.1 · 14k bars`
  - `PoT CAL    pred 44% · obs 46% · n 212` (QPOT-04)
  - `EDGE by KZ LDN +5.8 · NYAM +6.3 · OFF +1.9 pp` (lets users test the ICT killzone claims on their own chart)
- **Cost:** 18 O(1) PoT evaluations per confirmed bar, plus 18 resolutions. Memory (H+1)·18 ≤ 8.1k floats.
- **Evidence:** moderate (the need is shown in §2.2 and E30; Brier and cluster-robust z are standard).
- **Risk:**
  - Probes grade models at fixed distances, not at the DOL's own distance. That is fine for model choice; QPOT-04's trial-level calibration covers the DOL itself.
  - Early-history noise (gated by n and z).

### TIME-5 (P2, effort S): neutral killzone affinity by default; continuous, clock-based hysteresis
- **Why.**
  - `f_kzAff` (596-602, applied at 1941) adds 5-20% to session/PD pools in fixed killzones, regardless of distance. session_stats shows those raids at the null rate ±3 pp.
  - The two real time residuals (E25 cash-open drive; the index Asia two-sided raid) are not what it encodes, and TIME-2 learns the first.
  - With TIME-2/3 the timing is already in reach, so keeping the multipliers double-counts it and biases the ledger.
  - The binary off-killzone rule (976) is a crude stand-in for "the next bars are quiet".
- **Spec.**
  - `string kzAffMode = input.string("Off", "Killzone Affinity", options = ["Off", "Fixed (legacy)", "Learned"], group = G_FLOW, display = display.none)`.
  - At 1941: `lv.mult *= kzAffMode == "Fixed (legacy)" ? f_kzAff(kz, lv.src) : kzAffMode == "Learned" ? f_kzLearn(kz, lv.src) : 1.0`.
  - "Learned" delegates to session_stats **SESS-3** (a bounded multiplier from the key-level hazard surface, neutral until learned) or to ict_liq ICT-1 probes. Shrink with `w = n/(n+40)`, bound to [0.85, 1.15].
  - Hysteresis (976):
    ```
    float hystEff = clkUse ? hyst * f_clamp(math.sqrt(H / math.max(fwdSum, 1e-9)), 1.0, kzHx) : (kz == 0 ? hyst * kzHx : hyst)
    ```
    - `fwdSum` = the sum of seasonal factors over the next H bars (`f_fwdVar(H)/clkLf`).
    - Stickier exactly when the coming bars are expected to be quiet.
    - With TIME-1d, coarse charts get kz = -1, so the binary fallback does not double there.
- **Evidence:** moderate (E5, E6, E25; §2.2).
- **Risk:** users who like the ICT narrative can choose "Fixed (legacy)".

### TIME-6 (P2, effort M): PoT by session end and an ETA in clock time (shared with QPOT-05 / SESS-2)
- **Why.**
  - Traders ask "will it be taken in NY AM / before the close?". P(taken today) collapses through the day: 64 → 57 → 47 → 19% from Asia → London → NY AM → NY PM (E20).
  - A vol-time ETA ranks time-to-touch correctly; a bar-count one does not (E21).
  - Scalping (5m) and Day Trading (1H) share H = 30, i.e. 2.5 hours vs 30 hours (G17).
- **Inputs** (G_POT):
  - `potHor = input.string("Bars (H)", "PoT Horizon", options = ["Bars (H)", "Killzone End", "NY Close 16:00", "Day End 17:00"])`;
  - `showEta = input.bool(true, "Show ETA (clock time)")`.
- **Spec.**
  - Use the TIME-3 grid walk to count open-cell bars `hS` to the end minute (in `tz`), and the variance `V(hS)`.
  - PoT_S = the z-surface at `z = d/(close·√V)` (horizon-free under Brownian scaling), or the analytic `2Φ(-z)`.
  - ETA50: walk until `V(τ) ≥ (d/0.6745)²`. ETA80: `(d/1.2816)²`.
  - On `barstate.islast`, convert to a timestamp with `time(timeframe.period, "", tz, -k)` (k ≤ 500) and `str.format_time(t, "HH:mm", tz)`.
  - Without the clock, fall back to the ATR surface and the bar-count ETA.
- **Display:**
  - Terminal HUD: `PoT 30b 41% · →16:00 63% · ETA ≈10:40`.
  - Clean: tooltip only, so the Clean face stays two lines as in the reference screenshot.
- **Ledger.** When the horizon is not "Bars", trials store `hT`, and `f_step` (1455) uses `t.bars >= t.hT`.
- **Evidence:** strong (model), moderate (tests).
- **Risk:** future-time projection does not know holidays, so the ETA is labelled "≈". It requires TIME-3.

### TIME-7 (P2, effort S): overnight (Globex) high/low as registry pools
- **Why.**
  - These are the most-watched index-futures pools.
  - RTH breaks at least one ON extreme 94-96% of NQ days (E9), somewhat more than the null ("none" 3.6-4.0% vs 7.4-8.2% on ES/NQ). The cash-open drive (E25) is the mechanism.
  - They also hold the 05:00-09:30 pre-market extremes, which no current pool covers.
- **Spec.**
  - `sessON = input.session("1800-0930", "Overnight Range", group = G_KEY)`.
  - `useON = input.string("Auto", "Overnight H/L", options = ["Auto", "On", "Off"])`. Auto = on when `syminfo.type` is "futures" or "index".
  - Track with `f_sessTrack` using the overlap test (TIME-1a), or `f_sessTrackLT` (TIME-1b). The window wraps midnight.
  - Push at session end like 1800-1809: `src 8`, `f_tierW` 0.60 (not above PD; classic_levels and SESS-3 caution against tier probability bonuses).
  - Names: `f_levelName` "ONH" / "ONL"; `f_shortName` falls through; update the src comment at 316.
  - `f_pushExt` de-duplicates prices equal to the Asia/London extremes.
  - Consider raising the registry cap (1813) from 60 to 64.
- **Evidence:** moderate.
- **Risk:** 24-hour FX and crypto have no natural overnight, hence the Auto default.

### TIME-8 (P3, effort S): scheduled-event scaling of the clock (manual input plus an NFP rule), in σ units
- **Why.**
  - Release hours carry several times a normal hour's variance (E3), and Ederington & Lee show they drive the time-of-day and weekday patterns.
  - The average clock under-reaches on release days and over-reaches on quiet ones.
  - Pine has no calendar.
- **Spec.**
  - Manual event:
    - `evOn = input.bool(false, "Scheduled Event")`;
    - `evT = input.time(timestamp("2026-01-01T00:00:00-05:00"), "Event Time")`;
    - `evX = input.float(2.0, "Event Volatility x (σ)", minval = 1.0, step = 0.5)`; the variance multiplier is `evX * evX` [B2-corrected: B's first pass applied a range ratio as a variance multiplier];
    - `evMin = input.int(60, "Event Window (min)")`.
  - Automatic NFP (optional, US-linked symbols):
    - `nfpOn = input.bool(false, "Auto NFP (approx.)")`.
    - Release date = the **third Friday after the Saturday that ends the week containing the 12th of the previous month**, at 08:30 ET.
    - Compute with millisecond arithmetic, then rebuild the date with `timestamp(tz, y, m, d, 8, 30)` to avoid DST drift. If it falls on 1 January, add 7 days.
    - It is labelled approximate: BLS holiday and shutdown shifts break it, and the manual input overrides it.
  - In `f_fwdVar`, buckets whose projected start time (from the walk's day and bucket offsets relative to `time`) falls in `[evT, evT + evMin·60000)` get their variance multiplied by `evX²`.
  - Ignored once `timenow > evT + evMin·60000`.
  - The HUD shows "⚑ EVENT" while the window lies inside the horizon.
- **Defaults.** `evX = 2.0` (σ) is deliberately below the as-reported NFP range ratio of 2.7: the learned 08:30 bucket already includes release days, and Ederington & Lee's decay means most of the extra variance falls in the first 15 minutes.
- **Evidence:** strong (mechanism), moderate (magnitudes).
- **Risk:** user error; a stale event (auto-expiry handles it); the NFP rule drifts on holiday months. Requires TIME-3.

**Count: 8 proposals.** Fewer than the maximum on purpose. The other candidates are dropped or merged, for the reasons in §5.

---

## 5. Not proposed (and why)

| Item | Decision | Evidence |
|---|---|---|
| A's TIME-6: midnight open as a target ("Target: MO") | **Dropped** [B] | No excess over neighbouring opens at equal distance (E8: +0.3 ± 1.1 pp, n 1,412) |
| A's TIME-9: equity late-session momentum tilt in D | **Dropped** [B] | Small R² and decayed; no OHLCV intraday-momentum family survives costs on MNQ 2021-25 (E10) |
| A's TIME-8: IPDA 20/40/60 pools | **Optional only** (tier ≤ 0.70, default off, if ever) [B] | 20/60/252-day extremes at the random-level rate (E16); PWH/PWL and HTF pivots already cover the HTF objective |
| A separate "cash-open drive" scoring term | **Not proposed** [B2] | TIME-2's empirical cells learn it per symbol; a fixed term would be wrong for FX, CL and GC (E25) |
| Landmark (killzone-aligned) time blocks | **Tested, not better** [B2] | tod12 +2.20% vs tod8 +2.18% (5m H30); +3.20% vs +3.75% (1H H12) |
| Business-time (ϑ-time) freshness: age pools in clock variance instead of bars | **Deferred** [B2] | Sound in principle (Dacorogna 1993), but untested for target selection; revisit once TIME-3 exists and the ledger can A/B it |
| Macros and Silver Bullet as scoring or time filters | Not proposed | Tested null (E14, E15); no volatility bump |
| CBDR / Asia / Flout SD rungs as targets | Not proposed | No evidence; the 40-pip rule is a community convention; the clock-aware distance already sizes the day's extension |
| Quarterly theory, quarterly shifts, named daily/weekly profiles | Not proposed | Unvalidated, or equal to the arcsine/shuffle null (E13) |
| Weekday priors (Tuesday low etc.) | Not proposed | Shuffle null. The weekday **variance** factor (±10% σ) is inside TIME-3 |
| Overnight-drift / pre-FOMC / FX home-hours / fix "W" tilts | Not proposed | Decayed (E11, E28) or a few bp (E26, E27) |
| NDOG / NWOG / ORG as targets | Not proposed | Gap fills at or below the mirror placebo (E29) |
| FX fixes, NY cut, gold fix, settlements as anchors | Not proposed | Real flow times, but their effect on touch probability is volatility, which the clock learns |
| Session-conditioned Judas sign | Defer to ict_liq ICT-2 + SESS-2 cells | AMD direction has no information beyond trend (E24); only the index-futures Asia two-sided raid is a residual (+3.5 to +6.2 pp) |

---

## 6. Sources

**B's reproducible computations.** Run with `python3 -I <script> <args>` from the folder.

`study/ict_time_b_tools/` (first pass):

| Script | Output | What it does |
|---|---|---|
| `tod_calib.py ../quant_pot_tools/rows_5min_30.pkl 5min` | `out_tod_5min.txt` | ES engine PoT bias by NY hour and weekday |
| `clock_sim.py` | `out_clock_5min_30.txt`, `out_clock_variants_H30.txt` | A's clock spec as written, incl. failure modes |
| `clock_sim2.py rows5_H30.pkl 5min 8,24 60 [UTC]` | `out_sim2_*.txt` | Robust clock, time-of-day surface, UTC vs NY keying |
| `sess_bug.py` | `out_sess_bug.txt` | Session-window error on 1H |
| `macro_test.py` | `out_macro.txt` | Macro / Silver Bullet windows vs the clock |
| `mo_test.py` | `out_mo.txt` | Midnight open vs neighbouring opens |
| `weekday.py` | `out_weekday.txt` | Weekday range factors |

`study/ict_time_b2_tools/` (second pass):

| Script | Output | What it does |
|---|---|---|
| `macro_attr.py` | `out_macro_attr.txt`, `macro_rows.pkl` | Per-symbol / per-window attribution of the macro residuals |
| `macro_attr2.py macro_rows.pkl` | `out_macro_attr2.txt` | Day-clustered SEs; cash-open drive by 10-min start bin |
| `clock_sim_lm.py ../ict_time_b_tools/rows5_H30.pkl 5min 8,12 60` (also 1h H12, 1h H30) | `out_lm_*.txt` | Landmark (killzone-aligned) blocks vs uniform blocks |

- Data:
  - CME 1-min/5-min, Jan 20-Apr 15 2026 (ES, NQ, YM, RTY, CL, GC): `study/amt_data/cme/`;
  - 1h, Mar 2025-Apr 2026: `study/smt_data/cme/`.
- A's computations: `study/ict_time_calc/` (`baselines.py`, `baselines2.py`, `pot_error.py`).

**Sibling studies cross-checked:**
- `quant_pot.md` (QPOT-01..05, the ES seasonal profile, ETA rank correlation)
- `session_stats.md` (day-bootstrap null, session-range tables, horizon collapse, gaps, SESS-1..3)
- `classic_levels.md` (T2 N-day extremes, T5 anchor confluence, opens as barriers)
- `asset_specific.md` (overnight-drift decay, fixes table, settlement-as-close)
- `trade_mgmt.md` (Silver Bullet tests)
- `skeptic.md` (§2.3 F mirror control, SKEP-2, C10-C13)
- `quant_regime.md`, `academic_sr.md` (intraday momentum, Mesfin, Taylor)
- `ict_liq.final.md` (ICT-1/ICT-2, G10 sweeps)
- `calib_ml.md` (CAL-3 confluence)

**Papers and pages verified or read in B's second pass:**
- Taylor, V. (2026). Evaluating the Predictive Validity of ICT's AMD Model on CME E-Mini NASDAQ-100 Futures. arXiv:2610.35887 (passages read). https://arxiv.org/abs/2610.35887
- Krohn, I., Mueller, P. & Whelan, P. (2024). Foreign Exchange Fixings and Returns Around the Clock. *J. Finance* 79(1), 541-578. https://econpapers.repec.org/RePEc:bla:jfinan:v:79:y:2024:i:1:p:541-578 · BoC SWP 2021-48: https://www.bankofcanada.ca/2021/10/staff-working-paper-2021-48/
- Evans, M. (2018). Forex trading and the WMR Fix. *J. Banking & Finance* 87, 233-247. https://ideas.repec.org/a/eee/jbfina/v87y2018icp233-247.html
- Michelberger, P. S. & Witte, J. H. (2016). Foreign Exchange Market Microstructure and the WM/Reuters 4pm Fix. arXiv:1501.07778 (passages read). https://arxiv.org/abs/1501.07778
- Breedon, F. & Ranaldo, A. (2013). Intraday patterns in FX returns and order flow. *JMCB* 45(5), 953-965. https://econpapers.repec.org/RePEc:wly:jmoncb:v:45:y:2013:i:5:p:953-965
- Ederington, L. & Lee, J. H. (1993). How Markets Process Information: News Releases and Volatility. *J. Finance* 48(4), 1161-1191. https://ideas.repec.org/a/bla/jfinan/v48y1993i4p1161-91.html
- Dacorogna, M., Müller, U., Nagler, R., Olsen, R. & Pictet, O. (1993). A geographical model for the daily and weekly seasonal volatility in the foreign exchange market. *JIMF* 12(4), 413-438. https://econpapers.repec.org/RePEc:eee:jimfin:v:12:y:1993:i:4:p:413-438
- Driessen, J., Lin, T.-C. & Van Hemert, O. (2013). How the 52-week high and low affect option-implied volatilities and stock return moments. *Review of Finance* 17(1), 369-401. https://ideas.repec.org/a/oup/revfin/v17y2013i1p369-401.html
- Zarattini, C., Aziz, A. & Barbon, A. (2024). Beat the Market: An Effective Intraday Momentum Strategy for S&P500 ETF (SPY). SFI Research Paper 24-97. https://ideas.repec.org/p/chf/rpseri/rp2497.html
- Panas, E. (2005). Applied Economics 37(2), 191-199 (U-shaped timing of daily extremes). https://ideas.repec.org/a/taf/applec/v37y2005i2p191-199.html
- Nava, N., Di Matteo, T. & Aste, T. Time-dependent scaling patterns in high frequency financial data. arXiv:1508.07428 (passages read).
- Allez, R. & Bouchaud, J.-P. (2010). Individual and collective stock dynamics: intra-day seasonalities. arXiv:1009.4785.
- Aldrich, E., Heckenbach, I. & Laughlin, G. (2014). The Random Walk of High Frequency Trading. arXiv:1408.3650.
- Gao, L., Han, Y., Li, S. Z. & Zhou, G. (2018). Market intraday momentum. *JFE* 129(2), 394-414. https://econpapers.repec.org/RePEc:eee:jfinec:v:129:y:2018:i:2:p:394-414
- Boyarchenko, N., Larsen, L. & Whelan, P. The Overnight Drift. NY Fed SR917 / *RFS* 2023. https://www.newyorkfed.org/research/staff_reports/sr917 · "The Disappearing Overnight Drift", Liberty Street Economics, 1 July 2026: https://libertystreeteconomics.newyorkfed.org/2026/07/the-disappearing-overnight-drift/
- Lucca, D. & Moench, E. (2015). *J. Finance* 70. Update: https://libertystreeteconomics.newyorkfed.org/2018/11/the-pre-fomc-announcement-drift-more-recent-evidence.html · Kurov, Wolfe & Gilbert, The disappearing pre-FOMC announcement drift: https://www.skidmore.edu/economics/documents/KurovWolfeGilbert-TheDisappearingPre-FOMC-Announce-Drift-200914.pdf
- BLS Employment Situation schedule: https://www.bls.gov/schedule/news_release/empsit.htm · Marketplace (third-Friday rule): https://www.marketplace.org/story/2023/03/03/why-no-jobs-report-first-friday-this-month
- edgeful, ICT opening retracement: https://www.edgeful.com/blog/posts/ICT-opening-retracement-report · LuxAlgo Midnight Open Retracement: https://www.luxalgo.com/library/indicator/midnight-open-retracement/
- NexusFi, overnight session analysis: https://nexusfi.com/a/data/pre-market-data-overnight-session-analysis · settlement table: https://nexusfi.com/a/data/futures-settlement-data
- Killzones: https://innercircletrader.net/tutorials/master-ict-kill-zones/ ; https://tradingfinder.com/education/forex/ict-kill-zones ; https://www.luxalgo.com/library/concept/killzones/
- Macro lists: the open-source "ICT Algorithmic Macro Tracker" (toodegrees) and "Macro Times" (Blu_Ju) scripts on TradingView (seen through search; the host is blocked).
- Quarterly theory: https://www.luxalgo.com/library/concept/quarterly-theory/
- Silver Bullet / ICT mechanical tests (weak): https://offbeatforex.com/is-ict-strategy-profitable/ ; the "I backtested 25,000 ICT Silver Bullet trades" summary (gist.ly).
- mypivots, Timing the High/Low of the Day: https://www.mypivots.com/articles/articles.aspx?artnum=20
- Aldous, Arc Sine laws and stock prices: https://www.stat.berkeley.edu/~aldous/Real-World/arc-sine.html

**Papers read by B in the first pass:**
- Hansen, P. R., Kim, C. & Kimbrough, W. (2021). Periodicity in Cryptocurrency Volatility and Liquidity. arXiv:2109.12142.
- Mesfin, M. (2026). Structural Limits of OHLCV-Based Intraday Signals in MNQ Futures. arXiv:2605.04004 (preprint).
- Heston, Korajczyk & Sadka (2010). arXiv:1005.3535.
- Stroud & Johannes (2012). arXiv:1211.2961.
- Yan (2021). arXiv:2111.02376.

**A's sources not re-confirmable in this sandbox** (numbers marked "as reported by A"):
- fxbacktest.app research pages (hourly range, release volatility, Asian range, London ORB, daily high/low timing): https://fxbacktest.app/research/
- tradingstats.net (midnight open; overnight high/low): https://tradingstats.net/
- tradestar Silver Bullet test: https://tradestar.app/blog/i-tested-the-ict-silver-bullet-mechanically
- edgeful blog (YM session table; weekday ranges); formiq EURUSD.
- Arjo's ICT Core Content notes (CBDR; IPDA): https://arjoio.notion.site/
- funded.now weekly profiles: https://funded.now/lessons/ict-weekly-profiles
- Andersen & Bollerslev (1997, *J. Empirical Finance* 4; 1998, *J. Finance* 53); Andersen, Bollerslev, Diebold & Vega (2003, *AER* 93).

**Pine v6 docs (local mirror, `docsrc/jabez4jc_pinescriptv6/`):**
- `concepts/sessions.md` line 47: `time()` tests the bar's opening time.
- `reference/time.md` 191 / 210 / 229 / 290-301: `dayofweek`, `hour`, `minute`, `time` with negative `bars_back`.
- `reference/str.md` 182: `str.format_time`.
- `reference/input.md` 488: `input.time`.
- `reference/request.md` 284-310: `request.security_lower_tf`.
- `writing_scripts/limitations.md` 206 (40 requests), 263-269 (intrabar limits), 367 (100k array elements).
