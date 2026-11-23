# ICT Time & Price: combined final study (Researcher A + Researcher B) for DOL Engine v2

Domain:
- killzones, sessions and session ranges;
- algorithmic macros and Silver Bullet windows;
- Power of 3 / AMD and the Judas swing;
- time anchors (midnight / true day open, 08:30 and 09:30 opens, weekly open);
- quarterly theory;
- CBDR, Asian range and Flout standard-deviation projections;
- daily and weekly profiles and weekday effects;
- IPDA 20/40/60-day data ranges and quarterly shifts;
- seasonal tendencies and scheduled news times.

The question throughout: which of these change the **probability** or the **timing** of a level being taken, and how the engine should use them.

Engine studied: `brief/baseline_v2.pine`. Line numbers refer to it; it is identical to `/home/user/m/indicators/dol_engine.pine`. B re-checked every line reference used below.

Inputs to this report:
- A's study `study/ict_time.md`, with its computations in `study/ict_time_calc/`.
- B's verification and new computations in `study/ict_time_b_tools/` (scripts and `out_*.txt`, listed in §6).
- Sibling studies used for cross-checks: `quant_pot.md` (QPOT-xx), `session_stats.md` (SESS-xx), `classic_levels.md`, `asset_specific.md`, `trade_mgmt.md`, `skeptic.md`, `quant_regime.md`, `ict_liq.final.md`.

**Marking.** `[A]` is A's finding kept as is. `[B]` is new from B. `[B-corrected]` is A's finding changed by B, and the entry says what changed and why.

**Evidence grades:**
- **strong**: peer-reviewed, or a large replicated quantitative study.
- **moderate**: published or reproducible numbers with a sound null.
- **weak**: practitioner consensus, or small/vendor samples.
- **none**: folklore, or tested and not supported.

**Verification limits (B, honest note).**
- B could not re-open A's web pages in this session:
  - the web-search budget was exhausted;
  - the Firecrawl account had no credits;
  - the sandbox network blocks fxbacktest.app, tradingstats.net, luxalgo.com, ssrn.com, newyorkfed.org and repec.org (DNS failures).
- B verified A's numbers in three other ways:
  1. against sibling studies that read the same or related sources independently;
  2. against arXiv papers read through the research index;
  3. above all, by **re-testing the key claims on real CME data** (6 futures; 1-min and 5-min Jan-Apr 2026, 1-hour Mar 2025-Apr 2026).
- Numbers that come only from A's web reading are marked "(as reported by A)".

---

## 0. Executive summary

1. **Time changes "which liquidity is taken next, and when" through one dominant channel: the intraday volatility clock.** [A, confirmed by B on real data]
   - Volatility is strongly periodic. The ES 5-min variance at the 09:30 bucket is 4.7x the daily mean and 0.20x at 23:30 (quant_pot).
   - The killzones are the high-variance parts of this clock.
   - The engine's PoT ignores the clock. B measured the bias of the **default Empirical PoT** by New York hour (6 CME futures, 5-min chart, H = 30, about 1.2 M level-windows, causal):

     | NY hour | Observed touch rate | Engine predicted | Bias |
     |---|---|---|---|
     | 07:00 | 68.3% | 52.4% | -16 pp |
     | 08:00 | 69.1% | 52.3% | -17 pp |
     | 11:00 | 42.1% | 52.3% | +10 pp |
     | 16:00 | 44.5% | 52.7% | +8 pp |
     | 21:00 | 42.0% | 52.7% | +11 pp |

     Mean absolute hour bias: 7.3 pp.
   - The engine is well calibrated overall but has **no time resolution**. [B]

2. **A volatility clock keyed to New York time fixes most of this on intraday horizons. It must be built robustly and switched on per chart.** [B]
   - B simulated the clock bar by bar, exactly as Pine would run it, causally on the same rows:

     | Setting | Brier gain vs engine | Symbols improved | Hour bias |
     |---|---|---|---|
     | 5-min, H = 30 | **+3.9%** | 6/6 (+1.6 to +6.6%) | 7.3 → 2.1 pp |
     | 5-min, H = 60 | **+5.5%** | 6/6 (+2.1 to +9.7%) | |
     | 1-hour, H = 30 (Day Trading default) | **-1.0%** | GC -9.8% | |

   - On the default 1H chart with H = 30 the clock gives nothing. A 30-hour window averages the clock out.
   - **A's spec as written** gains only +0.8 to +1.0%. It also **breaks numerically**: a multiplicative update zeroes a bucket on a zero-change bar, and a 40-day EWMA started at 1.0 barely converges.
   - B gives a robust spec (TIME-2) and a per-chart A/B scorecard that switches it on only where it wins (TIME-3).

3. **The cheapest robust win is a time-of-day split of the existing empirical surface.** [B]
   - 8 three-hour NY blocks, partially pooled to the all-hours surface.
   - Brier gain: +2.2% (5m, H = 30 and H = 60), +0.4% (1H, H = 30), +3.75% (1H, H = 12).
   - It was **positive on every symbol in every setting tested**, with ECE ≤ 0.015 (TIME-1).

4. **Most ICT time "facts" are what a random path does on that clock.** [A, refined by B]
   - The weekly "Tuesday low" folklore must beat the arcsine baseline:

     | Weekday | Mon | Tue | Wed | Thu | Fri |
     |---|---|---|---|---|---|
     | Share of weekly extremes | 29.5% | 14.1% | 12.8% | 14.1% | 29.5% |

   - "Red first hour → red day" (66.2%) is overlap arithmetic.
   - session_stats' **day-bootstrap null** is better than A's Gaussian random walk. It puts the session/day/week statistics within ±3 pp of geometry.
   - The one Judas-like residual is the **Asia range on index futures**: after its first break, the other side is taken +3.5 to +6.2 pp more often than the null. It is absent in CL, EURUSD and BTC.

5. **Macros and Silver Bullet: now tested, and null.** [B, new tests]
   - Macro windows: the chance that a 60-minute pool is swept, beyond what the clock predicts, is **+0.6 ± 0.5 pp** (61k windows).
   - Silver Bullet hours: +0.2 ± 0.6 pp. The 10:00-11:00 hour alone: -0.8 ± 1.0 pp.
   - The only exception is **09:50-10:10, at +6.1 ± 1.5 pp**. It brackets the 10:00 ET data releases: a scheduled-news effect, not a "macro".
   - Independent mechanical Silver Bullet tests also lose: profit factor 0.66-0.94, 0 of 10 variants profitable (trade_mgmt).

6. **The midnight open is NOT special.** [B-corrected]
   - A reported it as "the only time anchor with a measured excess" (65.6-68.0% RTH revisit vs 52-61% under a Gaussian random walk).
   - B compared it with the opens of the **neighbouring hours** at the same distance (1,412 instrument-days):

     | Anchor | Excess over distance-matched rate |
     |---|---|
     | 00:00 open | +0.3 ± 1.1 pp |
     | 23:00 open | +0.0 pp |
     | 01:00 open | -0.3 pp |
     | 00:00 open, 1-min data, exact 09:30-16:00 RTH | +0.35 ± 2.6 pp |

   - The Gaussian null simply understates how often *any* recent open is revisited.
   - A's TIME-6 ("Target: MO") is dropped.

7. **Two correctness bugs, now quantified.** [A found them; B measured them]
   - **Session ranges on 1H futures charts.** Session membership tests only the bar **open** (doc-verified). So on a 1H futures chart the "NY AM 09:30-12:00" range is really 10:00-12:00.
     - On **76% of days** at least one of the engine's NY H/L pools is the wrong level.
     - When wrong, it is off by 14-16% of the day's range (349 instrument-days, 1-min data).
   - **NY open anchor.** It is the 10:00 open, which differs from the 09:30 open by a median 15.6% of the day's range.
   - **The fix.**
     - An overlap test cuts the error to 35% of days, off by 6-7% of the day's range.
     - 30-minute lower-timeframe intrabars make it exact (TIME-4).

8. **Other corrections.** [B]
   - **Overnight drift.** It was flat in 2021-25 (via asset_specific), so it cannot explain anything today.
   - **Intraday momentum (A's TIME-9).** It does not survive costs on MNQ 2021-25 (14 signal families fail). TIME-9 is dropped.
   - **IPDA 20/60-day extremes.** They are reached at the random-level rate, within ±0.5 pp (classic_levels T2). TIME-8 (IPDA pools) is dropped to optional.
   - **Weekday factor.** On full CME days it is ±10% in σ (Tue lowest, Fri highest), not "Monday -20%".
   - **Ledger trials.** They open whenever the active DOL lacks an open trial, not only "when a new DOL is chosen".

9. **Best proposals (§4):**
   1. TIME-1: time-of-day surface.
   2. TIME-2: robust NY-keyed clock with a z-unit surface, gated.
   3. TIME-3: per-chart PoT scorecard and auto-selection, with a time-aware EDGE baseline.
   4. TIME-4: exact session windows and anchors.
   5. TIME-5: neutral killzone affinity and continuous hysteresis.
   6. TIME-6: PoT by session end and ETA in clock time.
   7. TIME-7: ONH/ONL pools.
   8. TIME-8: manual event input.

---

## 1. Concepts: definitions, parameters, edge cases

All clock times are **New York local time** (IANA `America/New_York`, DST-aware), as ICT teaches. Practitioner sources disagree by 30-90 minutes on several boundaries. The most-cited values come first; variants follow.

### 1.1 Killzones [A; B notes]
- **Windows** (LuxAlgo Library; innercircletrader.net; TradingFinder, as reported by A):

  | Killzone | Main window | Variants and notes |
  |---|---|---|
  | Asian | 20:00-00:00 | 19:00-22:00 or 20:00-22:00 |
  | London open | 02:00-05:00 | the most consistent across sources |
  | New York AM (FX) | 07:00-10:00 | index variant 08:30-11:00 |
  | London close | 10:00-12:00 | |
  | NY lunch | 12:00-13:00 or 13:30 | ICT's "no trade" window |
  | New York PM | 13:30-16:00 | |

- **Algorithm.**
  - `inKZ` = the bar interval `[open, open + tf)` overlaps `[start, end)` in NY time.
  - The killzone high and low are the extremes of the bars inside it, carried forward as liquidity.
- **What is real.** These are the windows where volatility and participation concentrate (Andersen-Bollerslev; quant_pot; B's clock).
- **What is not supported.** That a level is *more* likely to be raided in a killzone than the clock predicts (§2.2-2.4).
- **Edge cases:**
  - **DST mismatch** between the US and the UK: about 3 weeks in March and 1 week in October/November. During it, London 08:00 is 04:00 NY instead of 03:00.
  - Charts in UTC or exchange time.
  - **24/7 crypto**, whose periodicity is set by US/EU hours and **perpetual-futures funding times** (00/08/16 UTC on Binance). Volatility peaks near 16 UTC and bottoms near 05 UTC; weekends (Saturday most) are quieter; volatility bursts in the first minute of each hour and at :15/:30/:45 (Hansen, Kim & Kimbrough 2021, arXiv:2109.12142). [B]
  - **Bar-open session tests** on coarse bars (§1.2, G3).
- **B note on 10:00-11:00 ET.** It is the busiest *single hour* for US index futures, but on a 5m chart with H = 30 the touch rate of a forward window that starts at 10:00 is **below** average (46.4% vs 51.9%), because the window runs into the lunch lull. A killzone label says nothing about the next H bars; only the clock does. [B]

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
- **Pine membership rule.** "The `time()` function returns a UNIX timestamp for the *opening time* of the current bar, or `na` if the bar is not in the specified session" (local docs, `concepts/sessions.md` line 47). It is a **bar-open** test.
  - On 1H futures/FX/crypto charts (bars on the hour), a window that starts at :30 begins at the next bar.
  - US stocks have 1H bars at 09:30, 10:30, … so the window is aligned there.
- **B's measurement (1-min CME, 349 instrument-days, `sess_bug.py`):**

  | Construction on a 1H chart | Wrong extreme (high / low / either) | Mean error when wrong |
  |---|---|---|
  | Engine, bar-open: "09:30-12:00" = 10:00-12:00 | 37.5% / 40.7% / **76.2%** of days | 14% / 16% of the day's range |
  | Overlap test: 09:00-12:00 | 14.9% / 19.8% / 34.7% | 6-7% of the day's range |
  | Exact (30-min intrabars) | 0 | 0 |

  - The 09:30-10:00 half-hour holds one of the two NY AM extremes on most days. That is the arcsine law plus the open burst.
  - Also measured: the NY open anchor on 1H, the **10:00** open, differs from the true 09:30 open by a median **15.6%** of the day's range.
  - The NY PM killzone on 1H starts at 14:00. The 13:30-16:00 high is missed 25%, the low 36%.

### 1.3 Time anchors: midnight open, 08:30, 09:30, weekly and session true opens [A-defs; B-corrected evidence]
- **Midnight open (MO / TDO).** The open of the 00:00 NY bar, extended through the day.
  - ICT: on a bullish day the low forms below the MO early (manipulation), and price distributes above it afterwards.
  - "The low is below the open" is close to a tautology (low ≤ open). The testable claim is that the NY session gravitates back to the MO.
- **08:30 open.** The release time for CPI, NFP, PPI and similar data.
- **09:30 open.** The US cash open.
- **Weekly open.** Sunday 18:00. The quarterly-theory "true week open" is Monday 18:00.
- **Session true opens** (quarterly theory): 19:30, 01:30, 07:30, 13:30.
- **Evidence.** [B-corrected]
  - A's MO statistic (RTH revisit 65.6-68.0% across 9,226 days, tradingstats, as reported by A) is a fact about *distance and recency*.
  - B's anchor-neighbour test (`mo_test.py`): the RTH revisit rate of each hourly open from 18:00 to 08:00, against a rate pooled across all anchors in the same distance bin (distance from the RTH open in ADR units):

    | Data | Days | 00:00 open | 23:00 | 01:00 |
    |---|---|---|---|---|
    | CME 1h, Mar 2025-Apr 2026 (6 futures) | 1,412 | +0.27 ± 1.14 pp | +0.04 | -0.25 |
    | 1-min, exact 09:30-16:00 | 256 | +0.35 ± 2.6 pp | | |

  - Raw revisit rates rise smoothly with recency because later opens sit closer to the RTH open: 18:00 → 46.7%, 00:00 → 52.4%, 08:00 → 61.1% (1h proxy).
  - classic_levels T5 agrees: pools near the engine's time anchors (dayEQ, midnight, London opens) score +0.6 pp at CME (not significant) and -3.3 pp at BTC H8 (z -3.6).
  - Grade for "MO is a magnet": **none** (tested and not supported).
  - The 08:30 and 09:30 times are strong as **volatility times** and untested as levels.

### 1.4 Quarterly theory [A]
- **The day in 6-hour quarters:** 18-00 Asia, 00-06 London, 06-12 NY, 12-18 afternoon.
- **Sub-quarters:** 90-minute quarters inside each session.
- **Recursion:** the same grid applies to the week, the month and the year.
- **Phases:** AMDX or XAMD. The true open is the Q2 open (midnight for the day).
- **Evidence:** none. LuxAlgo: "no independent statistical validation". AMDX vs XAMD is discretionary, so the scheme is close to unfalsifiable.

### 1.5 Algorithmic macros [A-defs; B tested]
- **Windows** (ICT lists via LuxAlgo and open-source trackers):
  - 02:33-03:00 and 04:03-04:30;
  - 08:50-09:10;
  - 09:50-10:10;
  - 10:50-11:10;
  - 11:50-12:10;
  - 13:10-13:40 (some lists 13:10-13:50);
  - 15:15-15:45.
- **Claim.** Inside a window, price sweeps nearby liquidity and/or rebalances an FVG.
- **B's test** (`macro_test.py`; 1-min ES/NQ/YM/RTY/CL/GC, Jan-Apr 2026):
  - **Unit:** 20-minute windows starting every 5 minutes from 01:00 to 16:00.
  - **Pool:** the prior 60-minute high and low.
  - **Distance:** expressed in clock σ, using a per-minute clock times the same day's level (a generous model).
  - **Outcome:** the window trades through either side.
  - **Model:** a logistic fit of the outcome on a spline of distance, with symbol effects.
  - **Reported:** the mean residual with day-clustered SE. Results (61,244 windows; base sweep rate 61.1%):

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

  - Only 09:50-10:10 stands out. It contains the 10:00 ET releases (ISM, JOLTS, sentiment, …), whose day-specific spike an average clock smooths.
- **Grade:** none for macros as such. The 10:00 release effect belongs to scheduled news (§1.12, TIME-8).

### 1.6 Silver Bullet [A; B added evidence]
- **Windows:** 03:00-04:00, 10:00-11:00, 14:00-15:00.
- **Rule.** After a liquidity sweep, enter on the first displacement FVG toward the draw, and target the next pool.
- **Evidence (negative):**
  - tradestar: 108 trades, 38.9% win rate at 1:1, net loss (as reported by A).
  - trade_mgmt P3 (independent write-ups): profit factor 0.66-0.94; 0 of 10 variants profitable (2R target, 2020-2025); GBB script on 1-min ES/NQ/YM/GC 2011-2026: "the Silver Bullet hours are not special".
  - B's window test: +0.2 ± 0.6 pp.
- **Grade:** none for the claim. The negative evidence is moderate.

### 1.7 Power of 3 (AMD) and the Judas swing [A; B refined]
- **Power of 3.** Each candle runs accumulation, a manipulation leg against the eventual direction, then distribution.
- **Judas swing.** The early-session manipulation leg, measured from the MO or the session open.
  - It must fail: rejection, then displacement back through short-term structure.
  - If price holds beyond the swept level, it is a trending open, not a Judas.
- **Evidence:**
  - fxbacktest (as reported by A): FX Asian-range first-break fade 49.4% (n 9,598, ns). London ORB follow-through 50.3% (n 92,947). Crypto continues 55-58%.
  - G10 FX sweeps favour continuation (ict_liq E7).
  - session_stats day-bootstrap null [B]:
    - After the first break, the opposite side is taken **less** often than the null for PD (-1.9 pp on average), NY AM (-3.1 pp) and PW ranges.
    - The **exception is the Asia 20:00-00:00 range on index futures**: +3.5 to +6.2 pp (ES +4.7, NQ +3.6, YM +3.5, RTY +6.2; about 3 SE pooled). It is absent in CL (-1.2), EURUSD (+0.5) and BTC (-1.3).
  - Mesfin (2026, arXiv:2605.04004, preprint): Asia-session expansion bars on MNQ reverse at the next bar (T = -10.96). The burst is spent inside the bar.
- **Grade:**
  - none as a general rule;
  - weak-moderate for the narrow index-futures Asia two-sided raid. That is a learnable cell (SESS-2), not a fixed rule.

### 1.8 CBDR, Asian range, Flout and SD projections [A]
- **CBDR:** 14:00-20:00, preferably narrower than 40 pips. One "SD" is the range height. Rungs: `U_k = H + kR`, `D_k = L - kR`, k ∈ {1, 1.5, 2, 2.5, 3, 4}.
- **Asian range:** 20:00-00:00, projected 2-4 SD.
- **Flout:** CBDR plus Asia, about 15:00-00:00.
- **Evidence:** none. The underlying size fact is a volatility ratio, which the clock already provides.

### 1.9 Daily profiles [A]
- **Templates:** London/NY reversal or continuation, consolidation day.
- **Evidence:** none. Classification is only possible after the fact.

### 1.10 Weekly profiles and weekday effects [A; B-corrected magnitude]
- **ICT templates:** Tuesday/Wednesday low (high) of week, Wednesday reversal, Consolidation Thursday reversal, Seek & Destroy Friday.
- **Null:** the arcsine law (§2.5).
  - session_stats found the weekday U-shape equal to a day-order shuffle (Mon/Fri 23-34%, Tue-Thu 12-18%).
  - "Weekly low by Tuesday in up weeks": 72-75% vs the null's 76-77%.
- **Real effect: volatility.** [B-corrected]
  - A cited "Monday about 20% lower" (edgeful, NY-session range, as reported by A).
  - On **full CME trading days** (1 year of 1h data, `weekday.py`), day range / ADR14:

    | | Mon | Tue | Wed | Thu | Fri |
    |---|---|---|---|---|---|
    | ES | 0.99 | 0.90 | 0.95 | 1.05 | 1.11 |
    | NQ | 0.99 | 0.90 | 0.99 | 1.03 | 1.10 |
    | YM | 1.01 | 0.95 | 0.90 | 1.04 | 1.08 |
    | RTY | 0.97 | 0.94 | 0.96 | 1.04 | 1.08 |
    | GC | 1.10 | 0.98 | 0.93 | 1.08 | 1.11 |

  - The variance factor is 0.80-1.23, i.e. **about ±10% in σ**. It is a modest weekday factor for the clock, not a directional prior.

### 1.11 IPDA data ranges and quarterly shifts [A-defs; B-corrected evidence]
- **Definition.** The highest high and lowest low of the last 20 / 40 / 60 **trading days**, and their 50% levels. Untaken extremes are "cast forward" draws for 20-60 days.
- **Quarterly shift.** A change in the dominant daily direction around a quarter turn.
- **Evidence.** classic_levels T2, distance-matched random-level edges:

  | Level | 5 days | 20 days |
  |---|---|---|
  | 20dH / 20dL | +0.21 / +0.72 pp | -0.83 / +0.32 pp |
  | 60dH / 60dL | +0.43 / +0.30 pp | -0.56 / +0.80 pp |
  | 252dH / 252dL | at baseline | at baseline |

- **Grade:** none beyond distance (tested). Prior month/quarter extremes are also at baseline. Monthly and quarterly **opens** are reached *less* often than random (QOPEN -4.1 pp, z -3.2, at 20 days).

### 1.12 Seasonal tendencies and scheduled times [A; B-corrected]
- **Overnight drift** (Boyarchenko, Larsen & Whelan; NY Fed SR917 / RFS 2023):
  - ES 02:00-03:00 ET about 3.6-3.7% a year (1998-2019).
  - **Flat in 2021-25** ("The Disappearing Overnight Drift", Liberty Street 2026, via asset_specific). [B-corrected: A presented it without the decay.]
- **Pre-FOMC drift** (Lucca & Moench 2015): +49 bp in the 24 h before FOMC (1994-2011), "puzzling" after 2011.
- **Scheduled releases** (as reported by A, fxbacktest, 3,963 releases): the release hour runs FOMC 5.2x, NFP 2.7x and CPI 2.1x a normal same-clock hour.
  - B's 09:50-10:10 residual (+6.1 pp) is the same phenomenon at 10:00.
- **Relevance.** Drifts are 0.1-0.2σ per hour or less, so they barely move touch probabilities. Release-time variance is large and foreseeable (TIME-8).

### 1.13 The quantitative core: the volatility clock [A; B built and tested it]
- **Model** (Andersen & Bollerslev 1997/1998; Engle & Sokalska 2012):

  `r_t = σ_day · s(τ_t) · z_t`

  - `s(τ)` is a deterministic periodic factor by NY time of day and weekday.
  - `σ_day` is a slowly varying level.
- **First passage.** For a driftless walk the touch probability depends on `z = d / √V`, with `V = Σ_{k∈window} σ²_day · s²(τ_k)`, i.e. on the **variance remaining in the window, not the bar count**.
- **B's measured consequences:**
  - **Horizon gate.** Time of day matters when the horizon is shorter than a day. On 1H with H = 30 (30 hours) it averages out: the engine's mean hour bias is only 3.1 pp, and the clock does not help (-1.0%). On 1H with H = 12 it helps again (+3.9%).
  - **Key to the session time zone, not UTC.** On the same data a UTC-keyed clock gained +3.5% vs +3.9% NY-keyed, with hour bias 2.7 vs 2.1 pp. The sample has only 5 post-DST weeks out of 12, so a full year would cost more. QPOT-02 as written uses UTC buckets: switch it to `tz`.
  - **Robust estimation matters more than the idea.** The fragile and robust specs are compared in §2.2.

### 1.14 Intraday momentum [A; B-corrected relevance]
- **Gao, Han, Li & Zhou (JFE 2018):** SPY 1993-2013, first half-hour → last half-hour. R² 1.6% in sample, 1.2% out of sample. It is stronger on high-volatility days (quant_regime).
- **Recent evidence against tradability:** Mesfin (2026, preprint). 14 OHLCV intraday-momentum families on MNQ 2021-25, walk-forward with costs: **none pass**. The 09:30-09:55 ORB has T = 0.88-1.50 and is year-unstable.
- **Grade:** moderate for existence; none for a usable intraday tilt today. A's TIME-9 is dropped.

### 1.15 Arcsine law [A, verified]
- For Brownian motion on [0, T], the time of the maximum has density `1/(π√(t(T-t)))`.
- `P(max in [a, b]) = (2/π)[asin√(b/T) - asin√(a/T)]`.
- In business (variance) time, high-variance edges get even more mass.
- B checked A's weekly numbers: `(2/π)·asin√0.2 = 29.5%`, the next slice 14.1%, the middle 12.8%.
- This is why "the HOD forms at the open" and "the weekly low forms Monday/Tuesday" need a null before they say anything.

### 1.16 Session-horizon probability and ETA [A; B cross-referenced]
- **Concepts:** "P(touch before the killzone end / 16:00 / day end)" and "ETA = the time at which V(τ) reaches (d/0.6745)²" (driftless median first passage).
- **Supporting numbers:**
  - session_stats: for an untaken PDH/PDL at 0.2-0.35 ADR, P(taken by day end) is **64% from Asia → 57% London → 47% NY AM → 19% NY PM**.
  - quant_pot: a vol-time ETA ranks the actual time-to-touch correctly (rank correlation +0.11 / +0.16 / +0.22 at 1 / 2 / 3 ATR). A constant-σ ETA ranks it wrongly (-0.09).

---

## 2. Evidence (numbers and sources)

### 2.1 Table

| # | Claim / effect | Source, sample | Numbers | Grade | Status |
|---|---|---|---|---|---|
| E1 | Intraday periodicity of volatility | Andersen & Bollerslev 1997/1998; Engle & Sokalska 2012; Hansen-Kim-Kimbrough 2021 (crypto) | U-shape and session peaks; crypto peaks near 16 UTC, troughs near 05 UTC, funding-time spikes (00/08/16 UTC), weekends lower | strong | [A]+[B] |
| E2 | Hourly range profile | fxbacktest, 922,937 H1 bars (as reported by A); quant_pot (ES 5-min) | Peak/quiet hour 2.1-4.0x in range; ES 5-min variance at 09:30 = 4.7x the daily mean, 23:30 = 0.20x | strong | [A]+[B] |
| E3 | Scheduled news hours | fxbacktest, 3,963 releases (as reported by A) | FOMC 5.2x, NFP 2.7x, CPI 2.1x a normal hour | moderate | [A] |
| E4 | HOD/LOD timing, ES RTH | mypivots, 1,586 days (as reported by A; also cited by academic_sr) | 09:30 segment: HOD 17.2%, LOD 16.7%. Arcsine + clock gives 17.7% | strong (descriptive) | [A] |
| E5 | Session ranges vs the null | session_stats, day-bootstrap null, 7 markets | Asia/London within ±3 pp; NY AM range: afternoons break one side more (+3 to +10 pp single); RTH takes at least one ON side more (none 3.6-4.0% vs 7.4-8.2%, ES/NQ) | moderate | [B] (supersedes A's Gaussian baselines) |
| E6 | Asian range, FX vs index | fxbacktest (A) vs session_stats (B) | A: EURUSD both sides 37.7% vs 48.9% Gaussian. B (day-bootstrap, 20:00-00:00): EURUSD 63.5 vs 62.4 (≈ null); index futures opposite side after the first break +3.5 to +6.2 pp | moderate | [B-corrected]: "FX respects Asia more than random" is not robust to a better null and window |
| E7 | First-break fade / ORB | fxbacktest (as reported by A); Mesfin 2026 | FX fade 49.4% (ns); London ORB 50.3%; MNQ 09:30-09:55 ORB T 0.88-1.50, year-unstable | moderate | [A]+[B] |
| E8 | Midnight-open revisit | tradingstats (as reported by A); B `mo_test.py` | 65.6-68.0% in RTH. **Excess over neighbouring opens at equal distance: +0.3 ± 1.1 pp** (1,412 days); 1-min +0.35 ± 2.6 | none (as a magnet) | [B-corrected] |
| E9 | ON range in RTH | tradingstats NQ 2,827 days (as reported by A); session_stats | At least one side 94.2%; open above the ON mid → high first 76.2%; 68.7% of first breaks by 10:00; vs null: none 3.6-4.0% vs 7.4-8.2% | moderate | [A]+[B] |
| E10 | Intraday momentum | Gao et al. JFE 2018; Mesfin 2026 | R² 1.6% IS / 1.2% OOS (SPY 1993-2013); 0 of 14 MNQ families pass after costs | moderate (exists) / none (usable) | [B-corrected] |
| E11 | Overnight drift | NY Fed SR917 / RFS 2023; Liberty Street 2026 (via asset_specific) | About 3.6%/yr at 02-03 ET in 1998-2019; flat in 2021-25 | strong but decayed | [B-corrected] |
| E12 | Weekday volatility | B `weekday.py` (CME 1h, 1 year); edgeful/formiq (as reported by A) | Full-day range/ADR: Tue 0.90-0.98, Fri 1.08-1.11; variance factor 0.80-1.23 | moderate | [B-corrected] |
| E13 | Weekly extreme timing | Arcsine; Aldous (746 S&P blocks, as reported by A); session_stats | Mon 29.5 / Tue 14.1 / Wed 12.8 / Thu 14.1 / Fri 29.5% null; real = shuffle | strong (null) | [A]+[B] |
| E14 | Silver Bullet | tradestar (A); trade_mgmt P3; B window test | 38.9% win at 1:1; PF 0.66-0.94; 0/10 variants profitable; window residual +0.2 ± 0.6 pp | none (claim); moderate (negative) | [B-upgraded negative] |
| E15 | Macros | B `macro_test.py` | All macro windows +0.6 ± 0.5 pp; only 09:50-10:10 +6.1 ± 1.5 (10:00 releases) | none | [B] (A: "no test exists") |
| E16 | IPDA / N-day extremes | classic_levels T2 | 20dH/L, 60dH/L, 252dH/L within ±0.8 pp of random at 5 and 20 days | none beyond distance | [B-corrected] |
| E17 | Engine PoT bias by hour | B `tod_calib.py`, `clock_sim2.py` (6 CME futures, 5-min, H = 30) | Engine default: 07-09 ET -12 to -17 pp; 11:00 +10 pp; 16:00 +8 pp; 21:00 +11 pp; mean \|bias\| 7.3 pp. 1H H = 30: mean \|bias\| 3.1 pp | moderate (measured) | [B] (replaces A's model-based E18) |
| E18 | Clock / time-of-day PoT gains | B `clock_sim2.py` (causal, walk-forward) | See §2.2 | moderate | [B] |
| E19 | Session-window bug size | B `sess_bug.py` | Bar-open: 76% of days wrong, 14-16% of the day range; overlap: 35%, 6-7%; NY open anchor median 15.6% of the day range | strong (measured + doc) | [B] |
| E20 | Horizon collapse of "taken today" | session_stats | 0.2-0.35 ADR PDH/PDL: 64 / 57 / 47 / 19% from Asia / London / NY AM / NY PM; clock × today factor: Brier -4.8% IDX | moderate | [B cross-ref] |
| E21 | Vol-time ETA | quant_pot | Rank correlation +0.11 / +0.16 / +0.22 vs -0.09 (constant σ) | moderate | [B cross-ref] |
| E22 | Asia expansion bars reverse | Mesfin 2026 (preprint) | MNQ, 1.5x-range Asia bars: next-bar T = -10.96 | weak-moderate | [B] |
| E23 | Arcsine "first hour colour" | A's math | `0.5 + asin(ρ)/π` with ρ ≈ 0.45-0.49 gives 65-66% vs 66.2% observed | strong | [A] |

### 2.2 B's simulation of time-aware PoT models (real CME data, causal) [B]

**Setup** (`clock_sim2.py`):
- Rows: quant_pot's walk-forward rows — every bar, both sides, distances 0.5-6 ATR; y = touched within H.
- Comparator: the engine default Empirical model (`p_eng_emp`).
- Models simulated bar by bar as they would run in Pine:
  - `todK`: the engine ATR surface split by K NY-time blocks, partially pooled to the all-hours surface: `p = (nb·pb + 60·pPool)/(nb + 60)`, with nb counted in effective windows (n/(0.6H)); then the engine's analytic prior.
  - `clkB`: the robust clock (spec in TIME-2) → a z-unit surface with an analytic clock prior.
  - `clkA`: the analytic clock only.

| Setting | rows | engine Brier | clkA | clkB | tod8 | tod24 | clkB+tod8 | quant_pot `p_srng_cal` (UTC) |
|---|---|---|---|---|---|---|---|---|
| 5-min H = 30 | 1.20 M | 0.1905 | +3.90% | **+3.86%** | +2.18% | +1.88% | +3.81% | +1.87% |
| 5-min H = 60 | 1.19 M | 0.1903 | +5.52% | **+5.45%** | +2.15% | +1.33% | +5.40% | +4.27% |
| 1-hour H = 30 | 0.41 M | 0.1883 | -2.97% | -1.05% | **+0.38%** | +0.20% | -1.02% | -1.21% |
| 1-hour H = 12 | 0.41 M | 0.1766 | +0.92% | +3.86% | +3.75% | +2.41% | **+4.12%** | +3.02% |

**Per symbol, clkB (and tod8):**

| Setting | CL | ES | GC | NQ | RTY | YM |
|---|---|---|---|---|---|---|
| 5m H30 clkB | +1.6 | +3.5 | +1.8 | +4.1 | +5.0 | +6.6 |
| 5m H30 tod8 | +1.1 | +2.0 | +1.2 | +2.1 | +2.9 | +3.6 |
| 1h H30 clkB | +0.6 | +1.9 | **-9.8** | +2.0 | +0.1 | -0.4 |
| 1h H30 tod8 | +0.2 | +0.4 | +0.1 | +0.4 | +0.5 | +0.7 |
| 1h H12 clkB | +2.6 | +6.2 | **-6.9** | +6.9 | +7.4 | +6.3 |
| 1h H12 tod8 | +1.8 | +4.0 | +0.1 | +4.2 | +5.7 | +5.9 |

Further results:
- **Calibration (ECE, 5m H30):** engine 0.012; tod8 0.009; clkB 0.015; clkA 0.030. The z-surface keeps the analytic clock honest.
- **Hour bias (5m H30), mean \|pred - obs\| over NY hours:** engine 7.3 pp; tod8 4.7; tod24 5.5; clkB 2.1; clkB+tod 1.8.
- **Example hours (obs / engine / clkB):**

  | Hour | Observed | Engine | clkB |
  |---|---|---|---|
  | 07:00 | 0.683 | 0.524 | 0.647 |
  | 08:00 | 0.691 | 0.523 | 0.675 |
  | 11:00 | 0.421 | 0.523 | 0.442 |
  | 16:00 | 0.445 | 0.527 | 0.468 |
  | 21:00 | 0.420 | 0.527 | 0.417 |

- **A's spec as written** (multiplicative EWMA, close-to-close r², 40-day memory started at 1.0, no floors):
  - without a warm start: clkA +0.82%, clkB +0.96% (`out_clock_variants_H30.txt`);
  - with a 1/n warm start: buckets hit zero on zero-change bars, and the run failed (division by zero);
  - with a range-based variance: GC fell to -23.9%.
  - **The robust spec is required.**
- **GC failure on 1H.** GC 1h has 768 jump bars (> 8x the rolling median |r|), irregular hourly coverage, and a 3x volatility regime shift in Jan-Mar 2026. A fast-level clock z-surface is fragile there; the ATR surface is not. **The clock must be switched per chart by measured skill (TIME-3)**, not on by default.

### 2.3 Arcsine baselines (A's computation, verified)
See §1.15. A's Gaussian random-walk baselines (`ict_time_calc/baselines*.py`) remain a useful illustration. For session statistics they are **superseded** by session_stats' day-bootstrap null, and for anchors by B's anchor-neighbour test. Those keep the real path features: intraday mean reversion, fat tails, clustering.

---

## 3. Engine gap analysis (baseline_v2.pine; line references re-checked by B)

| ID | Concept | Status | Lines | What the engine does / what differs |
|---|---|---|---|---|
| G1 | Volatility clock in PoT / reach / race | **missing** | 916-917, 1303-1311, 1314-1322, 1343-1364, 665, 1948, 2066-2067 | `potSig = ta.stdev(chg, potLen)` (916) is a trailing, time-blind σ. It feeds the analytic PoT (1304), the baseline (1315), the race (1360-1363) and the proximity reach (665, via `sig` at 1948). On 5m charts the forward variance swings 0.2x-4.7x by hour. [A] |
| G2 | Empirical surface conditioning | **wrong for intraday timing** [B-corrected from "partial"] | 1059-1062, 1284-1300, 1527-1532, 2108-2111 | Excursions are normalised by `atr[H]` and split only by HTF bias (rows `bias+1`). They are pooled over all hours. This is the default model: well calibrated unconditionally, **biased -17 to +11 pp by hour** on 5m (E17). `f_reachD` and the reach bands inherit it. [B] |
| G3 | Session membership on coarse bars | **wrong** (1H and coarser) | 798-803, 835-863, 948-950, 964-966, 971-974; inputs 107-109, 220-226 | `time(timeframe.period, sess, tz)` is a bar-**open** test. On 1H futures charts: NY AM range = 10:00-12:00 (**wrong on 76% of days**, E19); NY open anchor = the 10:00 open (median 15.6% of the day range off); NY PM KZ starts at 14:00. Asia, London and midnight are exact on 1H. On 4H futures/FX charts `midOpen` stays `na` (no bar opens at 00:00-01:00), so it drops from confluence (1931). [A; B quantified] |
| G4 | Killzone set and use | **partial** | 223-226, 587-594, 970-976 | Asia, London, NY AM 07-10 and NY PM exist; there is no London close (10-12). `kz == 0` doubles hysteresis (`hystEff`, 976). This is a binary activity proxy; the forward variance (clock) is the right quantity. 10:00-11:00 is OFF-KZ, but on 5m the H = 30 window from 10:00 is below-average reach (46.4% vs 51.9%), so stickiness there is not obviously wrong. [B-corrected nuance] |
| G5 | Killzone affinity | **wrong** (unsupported prior) | 596-602, applied 1941 | London ×1.20 Asia pools, ×1.10 PD; NY AM ×1.20 London, ×1.15 PD, ×1.05 Asia; NY PM ×1.15 NY AM, ×1.10 PD. Applied regardless of distance and forward variance. session_stats: session/day pools are taken at the null rate ±3 pp; the only residual (Asia two-sided raids on index futures) is not what f_kzAff encodes. [A; B evidence] |
| G6 | Session ranges as liquidity | **partial** | 106-109, 945-951, 1800-1809, 316, 505-529 | Asia, London and NY AM H/L are pushed at session end, anchored to the print bar. **Missing:** ONH/ONL (18:00-09:30), which also covers the 05:00-09:30 pre-market extremes that no current pool holds. NY PM and lunch ranges are low value. [A; B narrowed] |
| G7 | Midnight open | **present as confluence; no target needed** [B-corrected] | 220, 964, 1931 | A wanted it as a target. B's test shows no excess over any recent open (E8). The confluence credit for time opens (`midOpen`, `ldnOpen`, `nyOpen` in `anchors`, 1931; +0.35 per hit, line 677) is unsupported (classic_levels T5) and misaligned on 1H (G3). [B] |
| G8 | 08:30 / 09:30 / weekly opens | **partial** | 221-222, 965-966 | London 02:00 and NY 09:30 opens are confluence anchors (09:30 wrong on 1H). There is no 08:30 or weekly open; both are low value as levels (classic_levels: weekly and monthly opens are barriers, -5 to -7 pp). [B] |
| G9 | Macros, Silver Bullet | **missing** (correctly) | none | Tested null (E14, E15). The 10:00 release bump is scheduled news (G15). [B] |
| G10 | Power of 3 / Judas | **partial** (implicit) | 1580-1582 | `liqEvt`: raid + close back inside = reversal, close beyond = continuation, at any time. Evidence: coin flip or continuation except the index-futures Asia range. Covered by ict_liq ICT-2 (learn the sign); a session × range cell could be a feature of SESS-2. [A] |
| G11 | CBDR / Asian / Flout SD | **missing** (correctly) | none | No evidence; redundant with a clock-aware distance. [A] |
| G12 | Weekday | **missing** | none | The weekday variance factor is ±10% in σ (E12). It belongs in the clock (TIME-2 `c[d]`), not in profiles. [B-corrected size] |
| G13 | IPDA 20/40/60 | **missing** (acceptable) | (PWH/PWL 1795-1799; HTF pivots 1782-1789; htfEQ 968) | N-day extremes are reached at the random-level rate (E16). Optional at most, tier ≤ 0.70. [B-corrected] |
| G14 | Drifts | **n/a** | 917 (`potMu`) | The overnight drift has decayed (E11). quant_pot QPOT-01: remove drift from all PoT maths (the 0.5×50-bar drift costs 3.7-7.1% log-loss). [B cross-ref] |
| G15 | Scheduled news | **missing** | none | No calendar in Pine. FOMC 5.2x, CPI 2.1x; the 10:00 residual +6.1 pp shows the average clock under-reaches on release days. [A; B evidence] |
| G16 | Ledger baseline and PoT grading | **partial / biased** | 1313-1322, 1426-1431, 1433-1459, 1461-1499, 2037-2045 | `pBase` uses the same time-blind model, so EDGE can credit timing as skill. [B-corrected mechanism]: trials open **whenever the active DOL has no open trial** (2037-2045): at a new DOL and right after the previous trial on the same DOL resolves (hit or H bars, 1453-1456). Trial starts therefore cluster wherever DOL turnover is high, i.e. active hours (hits resolve faster there, and off-KZ hysteresis (976) slows switches). Magnitude unmeasured. The displayed PoT is never stored or graded (QPOT-04). |
| G17 | Session horizon and clock-time ETA | **partial** | 2105-2126, 2240-2243 | `ETA\|hit` = median bars-to-hit of past hits within ±0.5 ATR (bars, not clock time). H is a fixed bar count, so "before the NY close?" cannot be asked. [A] |
| G18 | Intraday momentum | **n/a** [B-corrected from "partial"] | 1536-1541, 1893-1894 | The generic displacement term with a 12-bar half-life is fine. A session-return tilt is not recommended (E10). |
| G19 | Session timezone for learned statistics | **n/a today** [B] | 220 (`tz`) | Every new time statistic (clock, time-of-day surface, killzone ledger) must key on `tz` (NY by default), not UTC: QPOT-02 as written uses UTC. |

---

## 4. Proposals (best first; maximum 12)

General notes for all specs:
- All learning and state updates run on `barstate.isconfirmed` only.
- Functions are declared before use; globals before the functions that read them. New inputs go in `G_POT` / `G_KEY` / `G_CONF`.
- Built-ins were checked in the local v6 reference:
  - `hour(time, timezone)`, `minute(time, timezone)`, `dayofweek(time, timezone)` (reference/time.md 191, 210, 229);
  - `time(timeframe, session, timezone, bars_back)`, with bars_back from -1 to -500 projecting future bars (time.md 290-301);
  - `str.format_time(time, format, timezone)` (str.md 182);
  - `input.time` (input.md 488);
  - `request.security_lower_tf(..., ignore_invalid_timeframe, calc_bars_count)` (request.md 289).
- Limits:
  - arrays ≤ 100,000 elements (limitations.md 367);
  - 40 unique `request.*` calls (limitations.md 206); the engine uses 7;
  - 100k intrabars on non-professional plans (limitations.md 263-269).
- Every proposal keeps the engine non-repainting. Every new state update reads closed bars only. The lower-timeframe read is consumed only on confirmed chart bars, as the existing VP feed does (982-1015).

### TIME-1 (P1, effort M): NY time-of-day dimension in the empirical PoT surface, with partial pooling
- **Why.** The default PoT is biased by up to 17 pp by hour (E17). This is the smallest change that removes about a third of that bias.
  - It was **never harmful** in 24 symbol × setting tests: +0.1 to +5.9% Brier, ECE ≤ 0.015.
  - It also fixes the time-blind EDGE baseline (`f_potBase` uses the same surface).
- **Inputs** (G_POT): `bool todOn = input.bool(true, "Time-of-Day PoT Surface", group = G_POT, tooltip = "Learns how far price travels within the horizon separately for each 3-hour block of the New York day. A block borrows from the all-hours surface until it has enough history.")`
- **Derived** (after 309): `const int NQ = 8`, `const int NQ1 = 9` (row 8 = pooled), `const float TODM = 60.0`.
- **Series** (after 920): `int todQ = todOn and timeframe.isintraday ? int(hour(time, tz) / 3) : NQ` (0 = 00-03 … 7 = 21-24).
- **State** (1061-1062): `var array<int> sUp = array.new<int>(3 * NQ1 * NB1, 0)`, and the same for `sDn`. That is 1,647 ints each. Row index = `(regime * NQ1 + q)`; `f_bump` and `f_surv` take the row unchanged.
- **Step 0** (1528-1532): bump both the cell and the pooled row:
  ```
  int bH = htfBias[H]
  int qH = todQ[H]
  float xu = (fwdHi - close[H]) / aH
  float xd = (close[H] - fwdLo) / aH
  f_bump(sUp, (bH + 1) * NQ1 + NQ, xu)
  f_bump(sDn, (1 - bH) * NQ1 + NQ, xd)
  if qH < NQ
      f_bump(sUp, (bH + 1) * NQ1 + qH, xu)
      f_bump(sDn, (1 - bH) * NQ1 + qH, xd)
  ```
- **f_empPoT** (1284) gains `int q`:
  - pooled `pP`, `nP` from row `r*NQ1+NQ`, with the current gate and fallback (the all-regime sum uses pooled rows);
  - cell `pC`, `nC` from row `r*NQ1+q`;
  - `nCe = nC / max(1, 0.6*H)`;
  - `p = (nCe*pC + TODM*pP)/(nCe + TODM)`;
  - return `[p, nP]` so the analytic blend weight is unchanged.
- **Callers:**
  - `f_potModel` (1307) and `f_potBase` (1318) pass `todQ`;
  - `f_reachD` and the reach bands (2108-2111) use the pooled row `(htfBias+1)*NQ1+NQ`.
- **Cost:** O(NB) per bump, twice. Memory 3.3k ints.
- **Evidence:** moderate (B §2.2). It is consistent with QPOT-03, whose fallback used session buckets.
- **Relation to QPOT-03.** QPOT-03's volatility-state rows can be added later. Cells thin out multiplicatively, so keep the pooling.
- **Risk:**
  - Slower convergence per cell (handled by pooling).
  - On D/W charts `todQ = NQ` (pooled only).
  - The DST shift of the London open is about 1 hour for about 4 weeks a year; a 3-hour block absorbs most of it.

### TIME-2 (P1, effort L): robust NY-keyed volatility clock with a z-unit empirical surface (gated)
- **Why.**
  - On 5m (and on 1H with H ≤ about a session) it is the largest PoT improvement measured in any sibling study: +3.9% (H30), +5.5% (H60), +3.9% (1H H12), all 6 symbols positive on 5m. It cuts the hour bias to 2.1 pp.
  - It is the quantitative, symbol-learned form of killzones, sessions and weekday effects.
  - It also yields the forward variance needed by TIME-5 and TIME-6.
- **Inputs** (G_POT):
  ```
  string clkMode = input.string("Auto", "Volatility Clock", options = ["Auto", "On", "Off"], group = G_POT,
    tooltip = "Learns this symbol's volatility by New York time of day and weekday, and uses the variance expected in the coming bars. Auto: used only where it beats the plain surface on this chart (see PoT MODEL in the panel).")
  int   clkMin = input.int(30, "Clock Bucket (minutes)", options = [15, 30, 60], group = G_POT)
  float clkMem = input.float(40.0, "Clock Memory (days)", minval = 5.0, step = 5.0, group = G_POT)
  ```
- **Derived** (after 309):
  ```
  int   chMin = math.max(1, int(chartS / 60))
  int   bkMin = math.max(clkMin, chMin)
  bool  clkOK = clkMode != "Off" and timeframe.isintraday and bkMin <= 240 and 1440 % bkMin == 0
  int   NBK   = clkOK ? 1440 / bkMin : 1
  float bpb   = bkMin * 60.0 / chartS
  ```
- **Series** (after 917): a log GK-plus-gap variance proxy:
  ```
  float lHL  = math.log(high / low)
  float lCO  = math.log(close / open)
  float lOC  = na(close[1]) ? 0.0 : math.log(open / close[1])
  float xVar = math.max(0.0, 0.5 * lHL * lHL - (2.0 * math.log(2.0) - 1.0) * lCO * lCO) + lOC * lOC
  int   cB   = int((hour(time, tz) * 60 + minute(time, tz)) / bkMin)
  int   cD   = dayofweek(time, tz) - 1
  ```
- **State** (after 1080): `clkA[NBK]` (init 1), `clkD[7]` (init 1), `clkNb[NBK]`, `clkNd[7]`, `clkC[7*NBK]` (ints), `clkLs`, `clkLf` (floats, na), `clkDy` (int).
- **Learning** (global scope, right after the series; confirmed bars; **all** loaded bars, not only calcBars). The **robust** form:
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
- **Forward variance `f_fwdVar(h)`.** A's grid walk:
  - the remainder of the current bucket, then whole open cells;
  - a cell is open when `clkC ≥ 0.3·(clkDy/7)·bpb`;
  - guard `7·NBK + 8`;
  - returns `v · clkLf`, in log variance.
  - Optional refinement (QPOT-02): a mean-reverting level path `clkLs + φ^j (clkLf - clkLs)` with φ = 0.5^(1/30).
- **Phase B z-surface:**
  - `float fwdSd = clkOK and clkDy >= 5 ? close * math.sqrt(f_fwdVar(H)) : na` (series, so `fwdSd[H]` is valid).
  - New arrays `zUp` / `zDn` (3·NB1), grid `bZ = 5.0 / NB`; bump in step 0 with `(fwdHi - close[H]) / fwdSd[H]`.
  - Query: `z = d / fwdSd`.
  - Prior: the driftless `pA = f_erfc(z / math.sqrt(2.0))`, capped at 0.95 (QPOT-01).
  - Blend `(nEff·pE + priorM·pA)/(nEff + priorM)` as now.
- **Wiring:**
  - Add a model switch `potSel` (0 pooled ATR, 1 time-of-day ATR, 2 clock z), set by TIME-3 when `clkMode = "Auto"`, or forced by "On".
  - Reach (665) and the race (1360) use `sigH = close*math.sqrt(f_fwdVar(H)/H)` when `potSel == 2`.
- **Cost.**
  - The walk: about H/bpb + skipped cells (5 iterations for H = 30 on 5m; ≤ 7·NBK + 8 over weekends).
  - Memory < 1k.
  - It needs no new request.
- **Evidence:** strong (concept: E1, E2), moderate (B's test §2.2).
- **Risk:**
  - GC-type jump series and regime shifts: the 1H failure (-9.8%) is why the default is "Auto" (scorecard-gated).
  - Holidays and early closes overstate V.
  - The US/UK DST mismatch smears the London bucket for about 3 weeks.
  - The empirical z-surface needs warm-up (it falls back to pooled until `nMin`).

### TIME-3 (P1, effort M): per-chart PoT scorecard with model auto-selection, a time-aware EDGE baseline, and EDGE by killzone
- **Why.**
  - The best PoT model depends on timeframe, horizon and symbol (§2.2: the clock wins on 5m, loses on GC 1H, and ties on 1H H30). Only the user's chart can decide.
  - DOL trials are too few to detect 1-4% Brier differences. Cheap **probes** are not: B's own evaluation design, ported to Pine.
  - It also stops EDGE crediting timing (G16) and lets the user test ICT killzone claims on their own chart.
- **Probes.** At every confirmed bar, 6 probes (k = 1, 2, 3 ATR × side), with the PoT of each candidate model m ∈ {0 pooled, 1 time-of-day (TIME-1), 2 clock (TIME-2)}:
  - Store them in a ring buffer: `var array<float> prb = array.new<float>((H + 1) * 18, na)`, index `((bar_index % (H+1))*6 + j)*3 + m`.
  - At bar t ≥ H, resolve the slot `(t - H) % (H+1)`: `y = side == 1 ? fwdHi - close[H] >= k*atr[H] : close[H] - fwdLo >= k*atr[H]` (the same window as step 0).
  - For each model accumulate `n`, `Σ(p - y)²`, and the per-bar difference `dB_m = Σ_j[(p_m - y)² - (p_0 - y)²]`.
  - Use 2H-bar block sums for a cluster-robust z, the same pattern as `cluSt` (1463-1469): `var array<float> scSt = array.new<float>(3 * 5, 0.0)`.
- **Selection.**
  - Once a day (`timeframe.change("D")`): `potSel` = the model with the lowest Brier among those with ≥ 2,000 resolved probe bars and **z ≤ -2** against model 0. Otherwise 0.
  - Hold the choice for at least 5 days, so the display does not flicker.
  - All inputs are confirmed history, so this is non-repainting.
- **Baseline.**
  - `f_potBase` (1314) uses the selected model, driftless. EDGE then measures level selection net of timing.
  - Trials (375-395) gain `float pPot` (the displayed PoT at open, QPOT-04) and `int kz0`.
  - `f_book` adds `kzN/kzK/kzE` arrays (size 7, index `kz0 + 1`) holding hits vs baseline by killzone.
- **Panel** (Terminal, Accuracy = Full):
  - `PoT MODEL  CLOCK ✓ · Brier -3.9% vs surface · z 6.1 · 14k bars`
  - `PoT CAL    pred 44% · obs 46% · n 212` (QPOT-04)
  - `EDGE by KZ LDN +5.8 · NYAM +6.3 · OFF +1.9 pp`
- **Cost:** 18 O(1) PoT evaluations per confirmed bar, plus 18 resolutions. Memory (H+1)·18 ≤ 8.1k floats.
- **Evidence:** moderate. The method is B's evaluation design; the need is shown by the heterogeneity in §2.2. Brier and cluster-robust z are standard.
- **Risk:**
  - Probes measure model quality at fixed distances, not at the DOL's own distance. That is fine for model choice; QPOT-04's trial-level calibration covers the DOL itself.
  - Early-history noise (gated by n and z).

### TIME-4 (P1, effort M): session windows and time anchors made exact; London-close killzone; no fixed confluence credit for opens
- **Why.**
  - On the default 1H execution chart the NY AM pools are wrong on 76% of days, by 14-16% of the day range (E19).
  - The NY open anchor is the 10:00 open.
  - The NY PM KZ starts at 14:00.
- **(a) Overlap membership** (all intraday TFs ≤ 1H).
  - Parse each session input once: `f_hhmm(s, at)`; `sM`, `eM` in minutes; an end of 0000 means 1440; `eM ≤ sM` wraps.
  - Replace `not na(time(timeframe.period, sess, tz))` at 799, 836 and 971-974 with `f_inWin(sM, eM)`: a half-open test of `[b0, b0 + chMin)` against `[sM, eM)`, plus the copy shifted by -1440 for bars that run past midnight. A's code (ict_time.md TIME-3a) was checked by B.
  - This alone cuts the NY AM error to 35% of days, 6-7% of the range.
- **(b) Exact bounds on charts coarser than 30 minutes.** One new request at global scope:
  ```
  [ltT, ltO, ltH, ltL] = request.security_lower_tf(syminfo.tickerid, "30", [time, open, high, low], ignore_invalid_timeframe = true)
  ```
  - Used only when `chartS > 1800 and intraOK`. 1H gives 2 intrabars per bar; 100k intrabars cover 50k chart bars.
  - A new `f_sessTrackLT(sM, eM)` is read on `barstate.isconfirmed` only:
    - it iterates the intrabars with `for [j, t] in ltT`;
    - each intrabar's membership uses `hour(t, tz)*60 + minute(t, tz)`;
    - it extends `var` hi/lo with the chart `bar_index` as the anchor;
    - it emits when the first out-of-session intrabar follows in-session ones (same tuple as `f_sessTrack`).
  - Session opens (`f_sessOpenLT`) take the open of the first in-session intrabar. This gives the exact 09:30 open on 1H.
  - Input `exactSess = input.bool(true, "Exact Session Bounds (30m data)", group = G_KEY)`.
- **(c) Killzones.**
  - Add `kzLC = input.session("1000-1200", "London Close Killzone", group = G_CONF)` as kz 5 (`f_kzName` 5 → "LDN CLOSE KZ").
  - The kz label uses the overlap test (an activity label).
  - Precedence stays London > NY AM > NY PM > Asia, with LC after NY AM.
- **(d) Time opens in confluence.**
  - New input `bool openConf = input.bool(false, "Session Opens as Confluence", group = G_CONF)`.
  - When off, `midOpen`, `ldnOpen` and `nyOpen` are left out of `anchors` (1931).
  - Evidence: no magnet effect (E8; classic_levels T5 engine anchors +0.6 pp ns at CME, -3.3 pp z -3.6 at BTC H8); calib_ml CAL-3 shows confluence at -0.25 logit overall.
  - When on, use the exact opens from (b), and show "≈" for any approximate anchor.
  - README "Confluence" row to be updated.
- **Evidence:** strong (doc quote plus measurement).
- **Risk:**
  - Lower-TF arrays can differ between realtime and history. They are consumed only on confirmed chart bars (as the VP feed at 1000-1008 does).
  - `ignore_invalid_timeframe` returns na on charts ≤ 30m, so fall back to (a).
  - One more request (8 of 40).

### TIME-5 (P2, effort S): neutral killzone affinity by default; continuous, clock-based hysteresis
- **Why.**
  - `f_kzAff` (596-602, applied at 1941) adds 5-20% to session/PD pools in fixed killzones, regardless of distance.
  - session_stats shows those raids at the null rate ±3 pp, and the one real residual (index-futures Asia two-sided raids) is not what it encodes.
  - With TIME-1/2 the timing is already in reach, so keeping the multipliers double-counts it and biases the ledger.
  - The binary off-KZ rule (976) is a crude stand-in for "the next bars are quiet".
- **Spec.**
  - `string kzAffMode = input.string("Off", "Killzone Affinity", options = ["Off", "Fixed (legacy)", "Learned"], group = G_FLOW)`.
  - "Learned" delegates to session_stats **SESS-3** (a bounded multiplier from the key-level hazard surface, neutral until learned) or to ict_liq ICT-1 probes. Shrink with `w = n/(n+40)` and bound to [0.85, 1.15].
  - Hysteresis (976): `float hystEff = clkUse ? hyst * f_clamp(math.sqrt(H / math.max(fwdSum, 1e-9)), 1.0, kzHx) : (kz == 0 ? hyst * kzHx : hyst)`.
    - `fwdSum = Σ` of seasonal factors over the next H bars (= `f_fwdVar(H)/clkLf`).
    - Stickier exactly when the coming bars are expected to be quiet.
- **Evidence:** moderate (E5, E6; B §2.2).
- **Risk:** users who like the ICT narrative can select "Fixed (legacy)".

### TIME-6 (P2, effort M): PoT by session end and an ETA in clock time (shared with QPOT-05 / SESS-2)
- **Why.**
  - Traders ask "will it be taken in NY AM / before the close?". P(taken today) collapses through the day: 64 → 57 → 47 → 19% from Asia → London → NY AM → NY PM (E20).
  - A vol-time ETA ranks the time to touch correctly; a bar-count one does not (E21).
- **Inputs** (G_POT):
  - `potHor = input.string("Bars (H)", "PoT Horizon", options = ["Bars (H)", "Killzone End", "NY Close 16:00", "Day End 17:00"])`;
  - `showEta = input.bool(true, "Show ETA (clock time)")`.
- **Spec.**
  - Use the TIME-2 grid walk to count open-cell bars `hS` to the end minute (in `tz`), and the variance `V(hS)`.
  - PoT_S = the z-surface at `z = d/(close·√V)` (horizon-free under Brownian scaling), or the analytic `2Φ(-z)`.
  - ETA50: walk until `V(τ) ≥ (d/0.6745)²`. ETA80: `(d/1.2816)²`.
  - On `barstate.islast`, convert to a timestamp with `time(timeframe.period, "", tz, -k)` (k ≤ 500) and `str.format_time(t, "HH:mm", tz)`.
  - Without the clock, fall back to the ATR surface and the bar-count ETA.
- **Display:**
  - Terminal HUD: `PoT 30b 41% · →16:00 63% · ETA ≈10:40`.
  - Clean: tooltip only, so the Clean face stays two lines.
- **Ledger.** When the horizon is not "Bars", trials store `hT`, and `f_step` (1455) uses `t.bars >= t.hT`.
- **Evidence:** strong (model), moderate (tests).
- **Risk:** future-time projection does not know holidays; the ETA is labelled "≈". It requires TIME-2.

### TIME-7 (P2, effort S): overnight (Globex) high/low as registry pools
- **Why.**
  - These are the most-watched index-futures pools.
  - RTH breaks at least one ON extreme 94.2% of NQ days (as reported by A). That is somewhat more than the null: "none" 3.6-4.0% vs 7.4-8.2% on ES/NQ (session_stats).
  - They also hold the 05:00-09:30 pre-market extremes, which no current pool covers.
- **Spec.**
  - `sessON = input.session("1800-0930", "Overnight Range", group = G_KEY)`.
  - `useON = input.string("Auto", "Overnight H/L", options = ["Auto", "On", "Off"])`; Auto = on when `syminfo.type` is "futures" or "index".
  - Track with `f_sessTrack` (overlap) or `f_sessTrackLT` (TIME-4b). The window wraps midnight.
  - Push at session end like 1800-1809: `src 8`, `f_tierW` 0.60 (not above PD; classic_levels and SESS-3 caution against tier probability bonuses).
  - Names: `f_levelName` "ONH" / "ONL"; `f_shortName` falls through; src comment at 316.
  - `f_pushExt` de-duplicates prices that equal the Asia/London extremes.
  - Consider raising the registry cap (1813) from 60 to 64.
- **Evidence:** moderate.
- **Risk:** 24-hour FX/crypto have no natural overnight, hence the Auto default.

### TIME-8 (P3, effort S): manual scheduled-event input that scales the clock
- **Why.**
  - The release hour runs FOMC 5.2x, NFP 2.7x and CPI 2.1x (E3).
  - The average clock under-reaches on release days (09:50-10:10 residual +6.1 pp, E15).
  - Pine has no calendar.
- **Spec.**
  - `evOn = input.bool(false, "Scheduled Event")`;
  - `evT = input.time(timestamp("2026-01-01T00:00:00-05:00"), "Event Time")`;
  - `evX = input.float(3.0, "Event Variance x", minval = 1.0)`;
  - `evMin = input.int(60, "Event Window (min)")`.
  - In `f_fwdVar`, buckets whose projected start time (from the walk's day and bucket offsets relative to `time`) falls in `[evT, evT + evMin·60000)` get their variance multiplied by `evX`.
  - It is ignored once `timenow > evT + evMin·60000`.
  - The HUD shows "⚑ EVENT" while the window lies inside the horizon.
- **Evidence:** strong for the magnitudes.
- **Risk:** user error; a stale event (auto-expiry handles it). It requires TIME-2.

**Count: 8 proposals.** B kept fewer than the maximum on purpose. A's other items are dropped or merged below, for the reasons given.

---

## 5. Not proposed (and why)

| Item | Decision | Evidence |
|---|---|---|
| A's TIME-6: midnight open as a target ("Target: MO") | **Dropped** [B] | No excess over neighbouring opens at equal distance (E8: +0.3 ± 1.1 pp, n 1,412) |
| A's TIME-9: equity late-session momentum tilt in D | **Dropped** [B] | Small R² and decayed; no OHLCV intraday-momentum family survives costs on MNQ 2021-25 (E10); asset_specific also rejects fixed session-directional priors |
| A's TIME-8: IPDA 20/40/60 pools | **Optional only** (tier ≤ 0.70, default off, if ever) [B] | 20/60/252-day extremes at the random-level rate (E16); PWH/PWL and HTF pivots already cover the HTF objective |
| Macros and Silver Bullet as scoring or time filters | Not proposed | Tested null (E14, E15). The 10:00 bump is scheduled news (TIME-8) |
| CBDR / Asia / Flout SD rungs as targets | Not proposed | No evidence; the clock-aware distance already sizes the day's extension |
| Quarterly theory, quarterly shifts, named daily/weekly profiles | Not proposed | Unfalsifiable, or equal to the arcsine/shuffle null (E13) |
| Weekday priors (Tuesday low etc.) | Not proposed | Shuffle null. The weekday **variance** factor (±10% σ) is inside TIME-2 |
| Overnight-drift / pre-FOMC directional tilts | Not proposed | Decayed (E11); effects ≤ 0.2σ per hour |
| Session-conditioned Judas sign | Defer to ict_liq ICT-2 + SESS-2 cells | Only the index-futures Asia range shows a two-sided-raid residual (+3.5 to +6.2 pp) |

---

## 6. Sources

**B's reproducible computations** (`study/ict_time_b_tools/`; run with `python3 -I <script> <args>` from that folder):

| Script | Output | What it does |
|---|---|---|
| `tod_calib.py ../quant_pot_tools/rows_5min_30.pkl 5min` | `out_tod_5min.txt` | ES engine PoT bias by NY hour and weekday |
| `clock_sim.py` | `out_clock_5min_30.txt`, `out_clock_variants_H30.txt` | A's TIME-1 spec as written, incl. failure modes |
| `clock_sim2.py rows5_H30.pkl 5min 8,24 60 [UTC]` | `out_sim2_5min_H30.txt`, `out_sim2_5min_H60.txt`, `out_sim2_1h_H30.txt`, `out_sim2_1h_H12.txt`, `out_sim2_5min_H30_UTC.txt` | Robust clock, time-of-day surface, UTC vs NY keying |
| `sess_bug.py` | `out_sess_bug.txt` | Session-window error on 1H |
| `macro_test.py` | `out_macro.txt` | Macro / Silver Bullet windows vs the clock |
| `mo_test.py` | `out_mo.txt` | Midnight open vs neighbouring opens |
| `weekday.py` | `out_weekday.txt` | Weekday range factors |

- Inputs: `rows5_H30.pkl`, `rows5_H60.pkl`, `rows1h_H30.pkl` and `rows1h_H12.pkl` are horizon slices of quant_pot's walk-forward rows (`quant_pot_tools/pot_eval.py`).
- Data:
  - CME 1-min/5-min, Jan 20-Apr 15 2026 (ES, NQ, YM, RTY, CL, GC): `study/amt_data/cme/`;
  - 1h, Mar 2025-Apr 2026: `study/smt_data/cme/`.
- A's computations: `study/ict_time_calc/` (`baselines.py`, `baselines2.py`, `pot_error.py`).

**Sibling studies cross-checked:**
- `quant_pot.md`: QPOT-01..05, the ES seasonal profile, ETA rank correlation.
- `session_stats.md`: day-bootstrap null, session-range tables, horizon collapse, SESS-1..3.
- `classic_levels.md`: T2 N-day extremes, T5 anchor confluence.
- `asset_specific.md`: overnight-drift decay, pre-FOMC.
- `trade_mgmt.md`: Silver Bullet tests.
- `quant_regime.md` and `skeptic.md`: intraday momentum, Mesfin.
- `ict_liq.final.md`: ICT-1/ICT-2, G10 sweeps.
- `calib_ml.md`: CAL-3 confluence.

**Papers read or verified by B through the research index:**
- Hansen, P. R., Kim, C. & Kimbrough, W. (2021). Periodicity in Cryptocurrency Volatility and Liquidity. arXiv:2109.12142.
- Mesfin, M. (2026). Structural Limits of OHLCV-Based Intraday Signals in MNQ Futures. arXiv:2605.04004 (preprint, not peer-reviewed).
- Heston, S., Korajczyk, R. & Sadka, R. (2010). Intraday Patterns in the Cross-section of Stock Returns. arXiv:1005.3535 (abstract): half-hour return continuation at daily lags, for 40+ days.
- Stroud, J. & Johannes, M. (2012). Bayesian modeling and forecasting of 24-hour high-frequency volatility. arXiv:1211.2961: seasonal time-of-day components plus announcement effects in index futures.
- Yan, X. (2021). Multiplicative Component GARCH Model of Intraday Volatility. arXiv:2111.02376: the Engle (2012) / Andersen-Bollerslev multiplicative model.

**A's sources** (not re-opened by B in this session; numbers marked "as reported by A"):
- LuxAlgo Library: Killzones, ICT Macros, ICT Time Anchors, Standard-deviation Projections, Quarterly Theory, Judas Swing, Session & Weekly Profiles. https://www.luxalgo.com/library/
- Arjo's ICT Core Content notes: CBDR; IPDA data ranges. https://arjoio.notion.site/
- Killzone variants: https://innercircletrader.net/tutorials/master-ict-kill-zones/ ; https://tradingfinder.com/education/forex/ict-kill-zones
- Weekly profiles: https://funded.now/lessons/ict-weekly-profiles
- fxbacktest.app research: when the daily high/low forms; volatility by hour; economic-release volatility; London ORB; Asian range break. https://fxbacktest.app/research/
- mypivots: Timing the High/Low of the Day. https://www.mypivots.com/article/details/20/timing-the-high-low-of-the-day
- tradingstats: midnight open; overnight high/low breakout. https://tradingstats.net/
- edgeful: session breakout / IB / OCC; day-of-week ranges; midnight-open retracement. https://www.edgeful.com/blog/
- formiq EURUSD: https://formiq.jp/data/eurusd
- tradestar Silver Bullet test: https://tradestar.app/blog/i-tested-the-ict-silver-bullet-mechanically
- Andersen & Bollerslev (1997). *J. Empirical Finance* 4, 115-158. Andersen & Bollerslev (1998). *J. Finance* 53(1).
- Andersen, Bollerslev, Diebold & Vega (2003). *AER* 93(1).
- Gao, Han, Li & Zhou (2018). *JFE* 129(2), 394-414.
- Boyarchenko, Larsen & Whelan. The Overnight Drift. NY Fed SR917 / *RFS* 2023. "The Disappearing Overnight Drift", Liberty Street Economics, 2026 (via asset_specific).
- Lucca & Moench (2015). *J. Finance* 70.
- Aldous, Arc Sine laws and stock prices: https://www.stat.berkeley.edu/~aldous/Real-World/arc-sine.html

**Pine v6 docs (local mirror, `docsrc/jabez4jc_pinescriptv6/`):**
- `concepts/sessions.md` line 47: `time()` tests the bar's opening time.
- `reference/time.md` 191 / 210 / 229 / 290-301: `dayofweek`, `hour`, `minute`, `time` with negative `bars_back`.
- `reference/str.md` 182: `str.format_time`.
- `reference/input.md` 488: `input.time`.
- `reference/request.md` 284-310: `request.security_lower_tf`.
- `writing_scripts/limitations.md` 206 (40 requests), 263-269 (intrabar limits), 367 (100k array elements).
