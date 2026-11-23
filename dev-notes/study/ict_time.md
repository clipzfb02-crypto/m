# ICT Time & Price: study for the DOL Engine v2

Domain covered:
- killzones, sessions and session ranges;
- algorithmic macros and Silver Bullet windows;
- Power of 3 / AMD and the Judas swing;
- time anchors: midnight open (true day open), 08:30 and 09:30 opens, weekly open;
- quarterly theory;
- CBDR, Asian range and Flout with standard-deviation projections;
- daily and weekly profiles;
- IPDA 20/40/60-day data ranges and quarterly shifts;
- seasonal tendencies and scheduled news times.

The question throughout: which of these change the **probability** or the **timing** of a level being taken, and how the engine should use them.

Engine studied: `brief/baseline_v2.pine`. Line numbers refer to it; it is identical to `/home/user/m/indicators/dol_engine.pine`. Companion study: `study/ict_liq.md` (liquidity theory). Its ICT-1 candidate ledger and ICT-2 sweep learner are referenced, not repeated, here.

Evidence grades:
- **strong**: peer-reviewed, or a large replicated quantitative study.
- **moderate**: published numbers that can be reproduced.
- **weak**: practitioner consensus, or small/vendor samples.
- **none**: folklore.

Reproducible computations for this report are in `study/ict_time_calc/`:
- `baselines.py` and `baselines_out.txt`;
- `baselines2.py` and `baselines2_out.txt`;
- `pot_error.py` and `pot_error_out.txt`.

---

## 0. Executive summary

1. **Time matters to "which liquidity is taken next, and when" through one dominant, very well documented channel: the intraday (and weekly) volatility clock.**
   - Volatility is strongly periodic: U-shaped around cash opens, with peaks at the London open and the London/NY overlap, troughs at the Tokyo lunch and NY lunch, and spikes at scheduled releases.
   - Andersen & Bollerslev (1997, 1998) is the canonical reference (strong).
   - On 16 years of hourly data the busiest hour is **2.1x-4.0x** wider than the quietest (EURUSD 27.7 vs 8.1 pips; US30 4.0x; US100 3.9x).
   - The Fed decision hour is **5.2x** a normal hour, NFP 2.7x, CPI 2.1x.
   - The killzones are, quantitatively, the high-variance parts of this clock.

2. **Most ICT time "facts" are what a random walk does on that clock.** I simulated Brownian motion whose per-minute variance follows the published hourly profiles (`baselines.py`). The baseline reproduces the published statistics within a few points:

   | Statistic | Observed | Random walk on the clock |
   |---|---|---|
   | Hour of the daily high, EURUSD | 00:00 8.8%, 14:00 7.9% | 10.7%, 7.0% |
   | Share of the daily range done by 08:00 UTC, EURUSD | 47.9% | 48.5% |
   | Asian range broken later the same day, US100 | 82 / 74 / 56% | 76 / 76 / 52% |
   | NY takes London H/L, YM (single break) | 83% | 77-78% |
   | ES HOD in the first 15 minutes | 17.2% | 17.7%, with a 2x open variance |
   | "Red first hour → red day", YM | 66.2% | **65.0-66.3%**, mechanical overlap |

   The weekly "Tuesday low" folklore must be read against the arcsine baseline:

   | Weekday | Mon | Tue | Wed | Thu | Fri |
   |---|---|---|---|---|---|
   | Share of weekly extremes under a random walk | 29.5% | 14.1% | 12.8% | 14.1% | 29.5% |

   Under the same baseline the weekly low is in by Tuesday's close 43.6% of the time.

   Takeaways:
   - "London raids Asia" and "NY raids London" are what a random walk does. They are not extra information.
   - In FX the Asian range is **more** respected than random: both sides break 37.7% of days, against 48.9% under the random walk.
   - So the engine's fixed killzone affinity multipliers (`f_kzAff`, lines 597-602, applied at 1941) have no support beyond the volatility clock.

3. **Reversal timing claims (Judas swing / AMD manipulation leg) fail mechanical tests.**
   - Fading the first Asian-range break in FX resolves at **49.4%**: 9,598 races, z = -1.25, not significant.
   - In crypto the first break **continues** 55-58% of the time.
   - The London opening-range break follows through **50.3%**: 92,947 breaks across 26 instruments.
   - Equity intraday momentum is real but small: first half-hour → last half-hour, R² 1.6% (Gao et al. 2018, JFE). It is absent in FX and commodities.

4. **One time anchor shows a modest real excess: the midnight open.**
   - RTH revisits it 65.6-68.0% of days (9,226 days, NQ/ES/YM, 2014-2026).
   - A random walk on the clock gives 52-61%.
   - So there is a +5 to +15 pp excess, plausibly the opening-hour reversal of overnight drift (NY Fed SR917).
   - Distance dominates: 85-87% when RTH opens near the midnight open, 42-46% when far.

5. **No evidence was found for** macros, Silver Bullet, quarterly theory, IPDA ranges, quarterly shifts, CBDR/Asian SD rungs, or the named weekly profiles. Treat them as hypotheses the ledger can test, not as scoring weights.
   - The one mechanical Silver Bullet test found: 108 trades, 38.9% win rate at 1:1, a net loss.

6. **The engine's biggest time-related defect:**
   - PoT, reachability, race odds and reach bands use a **time-blind trailing σ**: `potSig = ta.stdev(chg, 50)`, line 916.
   - The empirical surface is pooled over all hours (1528-1532).
   - On a 5m chart with the defaults (H = 30, potLen = 50), the trailing σ is **1.9-2.1x too low at 08:30-09:30 ET**: a displayed 20% PoT is really about 50-55%.
   - It is **1.2-1.3x too high from 11:45 to 15:00**: a displayed 20% is really 9-14% (`pot_error.py`, US100 profile).
   - The same blindness biases the ledger's random baseline (`f_potBase`, 1314-1322). Trials cluster in killzones because of `f_kzAff` and the off-killzone hysteresis (976), so EDGE can be inflated by timing alone.

7. **Two correctness bugs:**
   - Sessions are tested with `time(timeframe.period, sess, tz)`, which checks only the bar's **open** time. Docs: "returns a UNIX timestamp for the *opening time* of the current bar, or na if the bar is not in the specified session" (concepts/sessions.md line 47).
   - On a 1H chart (the default Day Trading execution TF), the "NY AM Range 0930-1200" therefore starts at the 10:00 bar. It **misses 09:30-10:00, the most active half-hour of the day**.
   - The "New York Open" anchor (0930-1030) becomes the 10:00 open.
   - The NY AM killzone ends at 10:00 and no London-close killzone exists. So **10:00-11:00 ET, the single most volatile hour for US index futures, is "OFF-KZ"**: hysteresis is doubled and the affinity is off.

8. **Best proposals:**
   1. TIME-1: a learned volatility clock that replaces the trailing σ in PoT, reach, race and the empirical surface.
   2. TIME-2: a time-aware ledger, with a clock-based baseline and a PoT calibration (Brier) A/B. It makes TIME-1's value measurable on the user's own chart.
   3. TIME-3: session-window correctness, plus overnight (ONH/ONL) and NY PM ranges.
   4. TIME-4: "PoT by session end" and an ETA in clock time ("~10:40 ET").

---

## 1. Concepts: definitions and parameters

All clock times are **New York local time** (IANA `America/New_York`, DST-aware), as ICT teaches. Practitioner sources disagree by 30-90 minutes on several boundaries. The most-cited values come first; variants follow.

### 1.1 Killzones
- **Windows** (LuxAlgo Library, "How it's calculated"; innercircletrader.net; TradingFinder):

  | Killzone | Main window (NY time) | Variants and notes |
  |---|---|---|
  | Asian | 20:00-00:00 | 19:00-22:00 or 20:00-22:00 |
  | London open | 02:00-05:00 | the most consistent across sources |
  | New York AM (FX) | 07:00-10:00 | **index-futures variant 08:30-11:00** |
  | London close | 10:00-12:00 | |
  | NY lunch | 12:00-13:00 or 13:30 | ICT's "no trade" window |
  | New York PM | 13:30-16:00 | |

- **Algorithm.** A killzone is a pure clock filter.
  - `inKZ = bar overlaps [start, end)` in NY time.
  - The killzone high and low are `max(H_t)` and `min(L_t)` over the bars inside it, carried forward as liquidity.
- **ICT expectations per window:**
  - Asia builds a range.
  - London often sets the high or low of the day, frequently via a Judas swing.
  - NY AM extends or reverses London.
  - London close is corrective.
  - NY PM makes the last push.
- **How practitioners use it.** As a time filter on setups, and to pre-select targets: "NY draws to the London high/low".
- **What is real.** These are the windows where participation and volatility concentrate. The fxbacktest hourly study (E2) puts the peak in 12:00-16:00 UTC for **10 of 10** instruments, with peak/quiet ratios of 2.1-4.0x.
- **What is not supported.** That a level is *more* likely to be raided in a killzone than a random walk on the same volatility would predict. See E6, E9 and §2.2.
- **Failure modes:**
  - DST mismatch between the US and UK (about 3 weeks per year).
  - Charts in UTC or exchange time.
  - 24/7 crypto, where sessions are only volume clusters.
  - Bar-open session tests on coarse bars (gap analysis G3).

### 1.2 Sessions and session ranges (Asia / London / NY AM / lunch / PM / overnight)
- **Definition.** A session range is the high and low printed inside a fixed clock window. It becomes "session liquidity" once the window closes.
  - ICT and community windows: Asia 20:00-00:00, London 02:00-05:00 (or 00:00-05:00), NY AM 08:30/09:30-11:00/12:00, NY lunch 12:00-13:00, NY PM 13:30-16:00.
  - Futures **overnight (Globex/ETH)** range: 18:00-09:30. Its extremes are ONH/ONL.
- **Edge cases:**
  - Sessions crossing midnight.
  - The high/low tie printed twice: take the first or the outermost print.
  - Bars straddling the window start or end.
  - Holidays and early closes.
  - Charts coarser than the window.
- **Practitioner use.** The next session's target is a prior session's high or low. Typical patterns: "London takes one side of Asia", "NY takes London's high or low", "RTH breaks the ONH/ONL".
- **Evidence summary** (details in §2):
  - The Asian range is broken on at least one side ~99% of FX days and 99.6% of US-index days (E6).
  - NY breaks one side of London 83.2% of days (YM, E9).
  - RTH breaks at least one overnight extreme 94.2% of days (NQ, E11).
  - All of these sit close to a random walk on the volatility clock (§2.2). They are real, very frequent targets, but the *probability* is explained by distance and remaining variance.

### 1.3 Time anchors: midnight open (true day open), 08:30, 09:30, weekly and session true opens
- **Midnight open (MO / TDO).** The open price of the 00:00 NY bar, extended through the day.
  - ICT: the "true day" runs from midnight NY. On a bullish day the low should form **below** the MO early (the manipulation leg), with distribution above it afterwards. Bearish days mirror this.
  - Note: "the daily low is below the open" is close to a tautology for any day measured from that open (low ≤ open). The non-trivial claim is about **where the NY session trades relative to the MO**.
- **08:30 open.** Release time for CPI, NFP, PPI, retail sales and similar data. The push away from it is read as manipulation, and the reclaim as the true direction.
- **09:30 open.** The US cash open.
- **Weekly open.** Futures open Sunday 18:00. The quarterly-theory "true week open" is Monday 18:00, the start of Tuesday's trading day (LuxAlgo: "Monday evening for the week").
- **Session true opens** (quarterly theory): the open of each cycle's second quarter, i.e. 19:30, 01:30, 07:30 and 13:30 for the four 6-hour sessions.
- **Practitioner use:**
  - As a premium/discount split for the day: buy below the MO on bullish days.
  - As a magnet or target: "price retraces to the MO".
- **Evidence.**
  - MO revisit in RTH: 65.6-68.0% across 9,226 days (moderate, E10).
  - The random walk on the clock gives 52-61%, an excess of about 5-15 pp.
  - The 08:30 anchor is strong as a **volatility time** (E3) and untested as a level.

### 1.4 Quarterly theory (Daye; built on ICT time components)
- **The day in four 6-hour quarters:**
  - Q1 Asia, 18:00-00:00;
  - Q2 London, 00:00-06:00;
  - Q3 New York, 06:00-12:00;
  - Q4 afternoon, 12:00-18:00.
- **Sub-quarters.** Each session splits into four 90-minute quarters, e.g. NY 06:00-07:30, 07:30-09:00, 09:00-10:30, 10:30-12:00.
- **Recursion.** The same grid is applied to the week, the month and the year.
- **Phase sequence.** AMDX (accumulation, manipulation, distribution, continuation-or-reversal), or the shifted XAMD.
- **True open.** The open of Q2: midnight for the day. The year is anchored to the first Monday of April.
- **Evidence:** none. LuxAlgo: "the grid has no independent statistical validation". Choosing between AMDX and XAMD is discretionary, so the scheme is close to unfalsifiable.

### 1.5 Algorithmic macros
- **Windows** (ICT macro lists as compiled by LuxAlgo and open-source trackers; NY time):
  - London: 02:33-03:00 and 04:03-04:30;
  - pre-market: 08:50-09:10;
  - AM macro 1: **09:50-10:10**;
  - AM macro 2: **10:50-11:10**;
  - lunch: 11:50-12:10;
  - PM: **13:10-13:40** (some sources say 13:10-13:50);
  - last hour: **15:15-15:45**.
- **ICT claim.** Inside the window price either runs to nearby resting liquidity or rebalances an FVG, often both: "sweep then rebalance" in about 20 minutes.
- **Evidence: none.**
  - No published test exists.
  - LuxAlgo notes that the windows bracket mundane cadences: the 10:00 ET data releases, hourly execution schedules and round-time option flows.
  - A volatility clock with 15-minute buckets captures any real periodic burst automatically. If the burst exists on the user's symbol, the PoT will reflect it.

### 1.6 Silver Bullet
- **Windows:** 03:00-04:00, **10:00-11:00**, 14:00-15:00 NY.
- **Rule.** Inside the window, after a liquidity sweep, enter at the first FVG created by displacement toward the draw on liquidity, and target the next pool. Practitioner versions require a minimum distance to the target.
- **Evidence:** weak and negative. A mechanical test of the 10:00 window gave 108 trades, a **38.9% win rate at 1:1**, and a net loss (tradestar). A vendor run on another market gave 43.1% WR and PF 1.26 over 608 trades. That market is irrelevant here.
- **Engine relevance.** Only as a window tag the ledger can test.

### 1.7 Power of 3 (AMD) and the Judas swing
- **Power of 3.** Each candle (day, week, session) is accumulation around the open, then a manipulation move against the eventual direction that prints one extreme early, then distribution to the other extreme with a close near it.
- **Judas swing.** The manipulation leg early in a session, measured from the MO or the session open.
  - It is a liquidity sweep "with a schedule", in the London KZ (often 00:00-02:00 or 02:00-05:00) or around the NY open.
  - It must fail: rejection beyond the level, then displacement back through short-term structure, often leaving an FVG.
  - If price holds beyond the swept level, it is a trending open, not a Judas.
- **Evidence.**
  - Mechanical fade tests are coin flips in FX: Asian-range first break fade 49.4% (E7); London ORB follow-through 50.3% (E8).
  - Continuation dominates in crypto (E7), in G10-FX sweeps (ict_liq E7) and after releases: the first-15-minute direction holds 4 hours later 63.5% of the time (E3).
  - Equity intraday momentum (E12) also argues against systematic early reversals.
  - Grade: none for the reversal claim.
- **Engine relevance.** The order-flow vector's raid rule (1581) encodes Judas-style "close back inside = reversal". ict_liq ICT-2 proposes learning its sign. The time domain adds that the sign may also depend on the session.

### 1.8 CBDR, Asian range, Flout and standard-deviation projections
- **CBDR** (Central Bank Dealers Range): the range from 14:00 to 20:00 NY. Some notes say 16:00-20:00.
  - ICT prefers it **narrow** (< 40 pips in FX). Bodies are preferred to wicks.
  - **One "standard deviation" is the CBDR height** (no statistics are involved).
  - The rungs are `U_k = H + k·R` and `D_k = L - k·R`, with k ∈ {1, 1.5, 2, 2.5, 3, 4}.
  - The London high on a bearish day (or low on a bullish day) is expected at 1-3 SD.
  - 4 SD is reserved for high-impact news or a NY reversal profile (ICT Core Content Month 08, via Arjo's notes).
- **Asian range** (20:00-00:00). Used when the CBDR is too wide; typically projected 2-4 SD.
- **Flout.** The combined CBDR plus Asian range (commonly quoted 15:00-00:00). It is used when either range alone is unusable.
- **Modern variant.** The ladder is anchored to an opening range or to the manipulation leg itself, with -2 to -2.5 as the watched exhaustion zone.
- **Evidence: none for the rules.**
  - There is a measurable fact underneath: the Asian session holds 47.9% of EURUSD's average daily range and 36.5% of US100's (E5). That makes "1-2 Asian heights beyond the range" about the right size for the day's extension.
  - But that is the volatility ratio again: the clock gives the same information continuously, without fixed rungs.
  - The rungs could serve as optional confluence anchors that the ledger tests.

### 1.9 Daily profiles
Daily profiles are named templates:
- London reversal: London prints the day's extreme against the higher-timeframe draw, then reverses.
- NY reversal.
- London continuation.
- NY continuation.
- Range or consolidation day ("seek and destroy").

Classification is only possible after the fact. There is no published hit rate (LuxAlgo). Evidence: none.

### 1.10 Weekly profiles and day-of-week effects
- **ICT weekly profiles** (Core Content Month 07; LuxAlgo; funded.now):
  - Classic Tuesday low (high) of week;
  - Wednesday low (high) of week;
  - Wednesday weekly reversal;
  - Consolidation Thursday reversal;
  - Consolidation midweek rally;
  - Seek & Destroy Friday.
  - The template: in a bullish week the low forms Monday to Wednesday, then expansion follows. Bearish weeks mirror this.
- **The null hypothesis.** Under a random walk the time of the weekly extreme is arcsine-distributed (§2.3):

  | Weekday | Mon | Tue | Wed | Thu | Fri |
  |---|---|---|---|---|---|
  | Share of weekly extremes | 29.5% | 14.1% | 12.8% | 14.1% | 29.5% |

  - The weekly low is in by Tuesday's close 43.6% of the time.
  - With Monday's variance at 0.64x (Monday is the quietest day), the baseline becomes Mon 24.2% and Tue 16.3%.
  - Aldous (Berkeley) checked 746 non-overlapping 20-day S&P 500 blocks: the time of the maximum matches a random-walk simulation.
- **Real day-of-week effect: volatility.**
  - ES NY-session range: Monday $60.81 against Thursday $76.03 and Friday $76.98.
  - NQ: Monday 301.88 against Friday 390.31 (edgeful).
  - EURUSD over 10 years: Monday 68.1 pips against Thursday 84.7 (formiq; about 520 days each).
  - Grade: moderate. This is a variance factor, not a directional prior.

### 1.11 IPDA data ranges and quarterly shifts
- **Definition.** The highest high and lowest low of the last **20, 40 and 60 trading days**, counted in daily candles, not calendar days.
  - Untaken extremes inside the 60-day window are candidate draws for the next 20-60 days: the "cast forward".
  - Each range's 50% is its equilibrium (premium/discount).
  - ICT (Core Content Month 5; Arjo's notes): anchor at the start of the month in which the last major liquidity grab or market-structure shift happened, then cast forward 20/40/60 days.
  - Some students re-measure every day.
- **Quarterly shift.** A change in the dominant daily direction around a calendar-quarter turn (January, April, July, October). It is identified by a daily displacement plus an MSS. It is said to occur about every 3-4 months.
- **Evidence:** none for IPDA as such. N-day highs are widely watched (Donchian, the 52-week-high literature), but no touch-probability study exists.

### 1.12 Seasonal tendencies and scheduled-time effects
- **ICT seasonals.** Asset-specific seasonal charts (e.g. Moore Research) used as a long-horizon bias.
- **Robust calendar drifts** (cited, not re-verified here):
  - the turn-of-the-month effect (Lakonishok & Smidt 1988; McConnell & Xu 2008);
  - the pre-FOMC drift (Lucca & Moench 2015, J. Finance 70:329-371, cited in Gao et al.);
  - the overnight drift.
- **The overnight drift** (NY Fed SR917, Boyarchenko, Larsen & Whelan):
  - ES returns are concentrated at **02:00-03:00 ET** (the European open): 3.7% a year from that hour alone, 1.5 bp per hour, t = 7.1, significant in 17 of 23 years.
  - The 09:00-10:00 return is negative: -1.2 bp, t = 2.6.
  - Grade: strong.
- **Relevance to PoT.** These drifts are 0.1-0.2σ per hour or less, so they barely move touch probabilities. They matter only as an explanation of the MO excess (opening-hour reversal of overnight gains).

### 1.13 The quantitative core: intraday periodicity (the "volatility clock")
- **Model** (Andersen & Bollerslev 1997/1998):

  `r_t = σ_day · s(τ_t) · z_t`

  - `s(τ)` is a deterministic periodic factor by time of day (and day of week).
  - `σ_day` is the slowly varying volatility level.
  - Standardising by `s(τ)` removes the U-shape. Estimating volatility dynamics without that filter distorts them.
- **First-passage consequence.** For a driftless walk, the probability of touching a level at distance d within a window depends only on

  `z = d / √V`, where `V = Σ_{k in window} σ²_day · s²(τ_k)`

  i.e. on the **variance remaining in the window, not on the number of bars**.
- **The same model** reproduces the arcsine "time of high/low" artefacts, the range-completion curve, and the session-break frequencies (§2.2).
- This is the single most useful formalisation of "killzones" for a probability engine.

### 1.14 Intraday momentum (the measured opposite of Judas)
- **Gao, Han, Li & Zhou (JFE 2018).** On SPY, 1993-2013, the first half-hour return (previous close to 10:00) predicts the last half-hour return.
  - Slope 0.069, R² 1.6%, rising to 2.6% with the 12th half-hour; out-of-sample R² 1.2-1.7%.
  - It also holds in other equity ETFs and in FTSE and Euro Stoxx futures.
  - It does **not** hold in major currency pairs or commodity futures.
- Grade: strong. Effect size: small.

---

## 2. Evidence (numbers and sources)

### 2.1 Table

| # | Claim / effect | Source and sample | Numbers | Grade |
|---|---|---|---|---|
| E1 | Intraday periodicity of volatility; must be filtered | Andersen & Bollerslev 1997 (J. Empirical Finance 4:115-158); 1998 (J. Finance 53); U-shape: Wood, McInish & Ord 1985 | Pronounced, persistent periodic component in DM-$ and S&P 500 futures; a flexible Fourier form filter restores long-memory daily volatility dynamics | strong |
| E2 | Hourly volatility profile | fxbacktest.app, 922,937 Dukascopy H1 bars, 2010-2026, 10 instruments | Peak/quiet 2.1x-4.0x. EURUSD 27.7 pips (14:00 UTC) vs 8.1 (22:00); US30 132 vs 33 (4.0x); US100 74 vs 19 (3.9x). All peak in 12-16 UTC. Session averages (EURUSD): Asia 13.3, London 20.3, overlap 26.1, NY 15.1, late NY 8.6 | moderate-strong |
| E3 | Scheduled news hours | fxbacktest.app, 3,963 US high-impact releases, 2007-2026 | EURUSD release hour vs a normal same-clock hour: FOMC 5.21x, NFP 2.69x, CPI 2.08x, pooled 1.82x. US100: CPI 2.68x, claims 0.49x. NFP surprise size does not predict range (terciles 60.7 / 64.6 / 65.5 pips). First-15-minute direction still intact after 4h: 63.5% (n=327) | moderate |
| E4 | Time of HOD/LOD, ES RTH | mypivots.com, 1-min ES, 1998-2004, 1,586 days, 27 × 15-min segments | 09:30 segment: HOD 17.2%, LOD 16.7%. 09:45: 8.4 / 6.8. Midday segments about 1-2%. 16:00 segment: 12.1 / 9.1. A uniform spread would give 3.7% each. Friday HOD and Monday LOD at 09:30 about 20%. | strong (descriptive) |
| E5 | Range completion and hour of the high, 22 instruments | fxbacktest.app, EURUSD 4,162 days (2010-2026), indices 2,576 days | EURUSD: 47.9% of range done by 08:00 UTC, 80.8% by 14:00, 99.0% by 21:00. US100: 36.5% by 08:00, jumping from 52.5% to 73.9% between 13:00 and 15:00. Hour of the daily high: max 8.8% (00:00) vs flat 4.2%, described by the authors as an "arcsine artefact". Both extremes inside 12-16 UTC on only 6.2% of EURUSD days | moderate-strong |
| E6 | Asian range (00:00-06:59 UTC) broken later the same day | same | EURUSD: high 68.2, low 68.4, both 37.7, neither 1.0%. US100: 82.0 / 73.8 / 56.2 / 0.4. AUDJPY: 57.6 / 54.0 / 18.4 / 6.8 | moderate |
| E7 | Asian-range first break: fade or follow | fxbacktest.app, 22 instruments, M15, 2021-2026, 17,593 resolved symmetric 1R races | FX reversal 49.4% (9,598 races, z -1.25, ns). ETHUSD continuation 58.2% (z -4.23, survives Bonferroni). BTCUSD 55.0%. Indices break both sides 62.8-68.1% of days | moderate |
| E8 | London opening-range (07:00 UTC hour) break | fxbacktest.app, 26 instruments, 2010-2026, 92,947 breaks | Broke on 99.8% of days. Follow-through of 1 range before failing: 50.3% (instrument range 47.6-52.5%) | moderate-strong |
| E9 | NY vs London range; initial balance; opening-candle colour | edgeful blog, YM, 6 months | After 11:00 ET: single break 83.2%, double 4.8%, none 12%. IB (09:30-10:30): single 76%, double 20%, none 4%. Red first hour → red NY session 66.23% | weak (small vendor sample) |
| E10 | Midnight-open revisit during RTH | tradingstats.net, 9,226 days NQ/ES/YM, 2014-2026; edgeful ES/NQ | NQ 68.0%, ES 65.7%, YM 65.6%. Near MO 85-87%, far 42-46%. Median retrace 09:41-09:48; 58-66% in the first 30 min; about 80% by 11:00. Non-retrace days close on the opening side 99.6-100%. Wednesday 70-71%, Monday 59.7-63.1%. Edgeful ES: open above MO → retrace 58%; below → 69% | moderate |
| E11 | Overnight (18:00-09:30) high/low broken in RTH | tradingstats.net, NQ, 2,827 days, 2015-2025 | At least one side 94.2%: only high 38.7, only low 32.6, both 22.9, none 5.8%. Open above the ON midpoint → high breaks first 76.2%. 33.5% of first breaks in the first 5 min; 68.7% by 10:00; 90% by 11:30 | moderate |
| E12 | Market intraday momentum | Gao, Han, Li & Zhou, JFE 129(2):394-414 (2018); SSRN 2440866 | SPY first half-hour → last half-hour: slope 0.069, R² 1.6%; with the 12th half-hour R² 2.6%; OOS R² 1.2-1.7%. Not present in FX or commodity futures | strong |
| E13 | Overnight drift around the European open | Boyarchenko, Larsen & Whelan, NY Fed Staff Report 917 | ES 02:00-03:00 ET: 1.5 bp per hour, t = 7.1, 3.7% a year, significant in 17 of 23 years. 09:00-10:00 ET: -1.2 bp, t = 2.6 | strong |
| E14 | Day-of-week volatility | edgeful (ES/NQ NY range by weekday); formiq.jp (EURUSD, 10 y, about 520 days per weekday) | ES Monday $60.81 vs Thursday $76.03 / Friday $76.98. NQ Monday 301.88 vs Friday 390.31. EURUSD Monday 68.1 vs Thursday 84.7 pips | moderate |
| E15 | Weekly extreme timing | Arcsine law (Lévy); Aldous (Berkeley), S&P 500, 746 non-overlapping 20-day blocks | Random-walk baseline Mon 29.5 / Tue 14.1 / Wed 12.8 / Thu 14.1 / Fri 29.5%. S&P blocks match a random-walk simulation. No dependable published hit rate for "Tuesday low of week" (LuxAlgo) | strong (null); none (ICT profiles) |
| E16 | Silver Bullet | tradestar.app mechanical test | 10:00 window: 108 trades, 38.9% WR at 1:1, net loss | weak (negative) |
| E17 | Macros | LuxAlgo Library; open-source trackers | No published test. Windows coincide with 10:00 ET releases and round-time flows | none |
| E18 | PoT error from a trailing σ (this study) | `pot_error.py`, from the E2 US100 profile, EDT; engine defaults (5m chart, potLen 50, H 30) | σ_forward / σ_trailing: 02:00 1.24; 08:30 2.14; 09:30 1.90; 10:30 1.30; 11:45 0.88; 13:30 0.81; 15:00 0.76. "20%" is really 30 / 55 / 50 / 32 / 14 / 12 / 9%. "50%" is really 59 / 75 / 72 / 60 / 44 / 41 / 37% | derived from strong premises |
| ict_liq E7 | Sweeps → continuation | Mahadzva, SSRN (2026), G10 FX walk-forward | 65 of 66 fold-selections favour continuation after sweeps | moderate |

### 2.2 Random-walk-on-the-clock baselines (this study, `baselines.py`, `baselines2.py`)

- **Method.**
  - Brownian motion over a 24-hour day, simulated on a 1-minute grid (40,000 paths).
  - Per-minute variance is proportional to the square of the published average hourly range (E2) for that UTC hour.
  - Exit and extreme probabilities depend only on **variance ratios**, so the daily volatility level cancels.
  - Indices are mapped to NY time with both the EST (UTC-5) and EDT (UTC-4) offsets, because E2 mixes DST states.
- **Results.**

| Statistic | Observed | Random walk on the clock | Reading |
|---|---|---|---|
| EURUSD Asian range: high / low / both / neither | 68.2 / 68.4 / 37.7 / 1.0 | 74.1 / 74.7 / 48.9 / 0.1 | FX respects the Asian range *more* than random (fewer double breaks). "London raids Asia" is no extra edge |
| US100 Asian range | 82.0 / 73.8 / 56.2 / 0.4 | 75.7 / 76.1 / 51.9 / 0.1 | ≈ random walk plus upward drift |
| US30 Asian range | 79.6 / 73.4 / 53.6 / 0.5 | 77.7 / 78.0 / 55.8 / 0.0 | ≈ random walk |
| EURUSD share of range by 08:00 UTC | 47.9% | 48.5% | ≈ random walk |
| EURUSD hour of the daily high | 00:00 8.8%, 14:00 7.9%, 13:00 6.4%, 15:00 6.6% | 10.7, 7.0, 6.3, 5.9% | ≈ random walk (arcsine plus clock) |
| YM: NY (11-16 ET) vs London (03-11 ET) | single 83.2, double 4.8, none 12.0 | 77-78 / 4.6-5.1 / 17-18 | slightly more single breaks than random (n ≈ 125, SE ≈ 3.4 pp: weak) |
| YM IB break (10:30-16:00) | 76 / 20 / 4 | 62.5 / 36.8 / 0.7 | IB is respected more than random (fewer double breaks): mean reversion in midday |
| "First hour colour = day colour" (YM) | 66.2% | **65.0-66.3%** | entirely mechanical (overlap: `0.5 + asin(ρ)/π`, ρ = √(first-hour variance share) ≈ 0.45-0.49) |
| ES HOD/LOD in the first 15 min (mypivots) | 17.2 / 16.7% | 12.3% calendar-time arcsine; 17.7% with the open at 2x variance and lunch at 0.7x | arcsine plus a U-shaped clock |
| Midnight open touched in RTH (NQ/ES/YM) | 65.6-68.0% | 52-61% (EST/EDT); the 08:30-open anchor gives 67-76% | **real excess of about 5-15 pp**, but nearer anchors are touched more in any random walk |
| NQ overnight range in RTH: only H / only L / both / none | 38.7 / 32.6 / 22.9 / 5.8 | 39-40 / 39-40 / 10-18 / 5-10 | more double breaks than random: a wide-RTH or trend-day effect, sensitive to the DST mapping |
| Weekly extreme weekday | (folklore) | Mon 29.5, Tue 14.1, Wed 12.8, Thu 14.1, Fri 29.5% | the baseline every weekly profile must beat |

- **Limitations.**
  - Hourly averages smooth the 09:30 burst.
  - DST mixing in E2 adds about ±4 pp.
  - Daily volatility clustering within a day is ignored.
  - Fat tails and intraday mean reversion are ignored; the IB and FX Asian results show they matter.
- **Conclusion.** The baselines are good enough to show that the **bulk** of each ICT time statistic is variance timing plus arcsine geometry. The residuals are small: an FX/IB mean-reversion tendency, the MO excess, and crypto continuation. They are exactly what an engine should *learn per chart*, not hard-code.

### 2.3 Arcsine law (why "the high forms at the open / on Monday" is mostly arithmetic)
- For Brownian motion on [0, T], the time of the maximum has density `1 / (π √(t (T - t)))`.
- The probability that the maximum falls in a sub-interval [a, b] is `(2/π) [asin √(b/T) - asin √(a/T)]`.
- In **business time** (cumulative variance), t is replaced by τ(t) = V(t)/V(T). A high-variance open therefore gets even more mass.
- Consequences:
  - Any fixed window's first and last slices are over-represented.
  - Moving the window boundary moves the bumps.
  - Statistics like "the HOD forms in the first hour 2/3 of the time" or "the weekly low forms Monday/Tuesday" need this baseline before they say anything about the market.

---

## 3. Engine gap analysis (baseline_v2.pine)

| ID | Concept | Status | Lines | What the engine does / what differs |
|---|---|---|---|---|
| G1 | Volatility clock in PoT / reach / race | **missing** (most important) | 914-917, 1303-1311, 1314-1322, 1343-1364, 665-667, 1948, 2066-2067 | `potSig = ta.stdev(ta.change(close), potLen)` is a trailing, time-blind σ. It feeds `f_pot` in the analytic PoT, the proximity reach (665), the race (`f_raceH`, 1360-1363) and the baseline. The forward-window variance depends on the clock: 1.9-2.1x the trailing estimate at 08:30-09:30 and 0.76-0.88x after 11:45 (E18) |
| G2 | Empirical PoT surface conditioning | **partial** | 1059-1062, 1284-1300, 1527-1532 | Excursions are normalised by `atr[H]` (a 14-bar trailing ATR) and split only by HTF bias, pooled over all hours. They are unconditionally calibrated but conditionally biased by time of day. `f_reachD` and the reach bands inherit the same issue |
| G3 | Session membership on coarse bars | **wrong** (1H charts) | 798-803, 835-863, 971-974; inputs 107-109, 220-226 | `time(timeframe.period, sess, tz)` tests only the bar **open**. On 1H bars opening on the hour: "NY AM Range 0930-1200" = bars 10:00 and 11:00, missing 09:30-10:00. The "New York Open" (0930-1030) anchor is the **10:00** open. `kzNP 1330-1600` starts at 14:00. On 4H/D charts the midnight anchor is never set (`midOpen` stays na), so it silently drops from confluence (1931) |
| G4 | Killzone set | **partial** | 223-226, 587-594, 970-976 | Asia, London, NY AM (07:00-10:00) and NY PM exist. No London-close (10:00-12:00), lunch or index NY AM (08:30-11:00) window. **10:00-11:00 ET, the peak-volatility hour for US index futures, is classed OFF-KZ**: `hystEff = hyst × kzHx` (976) and no affinity. A binary in/out switch, not a continuous activity measure |
| G5 | Killzone affinity of session pools | **wrong** (unsupported fixed prior) | 596-602, 1941 | London ×1.20 for Asia pools and ×1.10 PD; NY AM ×1.20 London, ×1.15 PD, ×1.05 Asia; NY PM ×1.15 NY AM, ×1.10 PD. Applied regardless of distance or remaining variance. A random walk on the clock already produces these raids (§2.2), and FX shows *fewer* double breaks than random. These are double-counted priors |
| G6 | Session ranges as liquidity | **partial** | 106-109, 945-951, 1800-1809, 316, 505-529 | Asia (20-24), London (02-05) and NY AM (09:30-12:00) H/L are pushed to the registry at session end, anchored to the exact print. **Missing:** overnight/Globex ONH/ONL (18:00-09:30; broken 94.2% of RTH days, E11), NY PM range, NY lunch range |
| G7 | Midnight open / true day open | **partial** | 220, 964, 1931 | A confluence anchor only (±0.35 ATR). Not a candidate target, although it has the best time-anchor evidence (E10). na on charts above 1H |
| G8 | 08:30 / 09:30 / weekly opens; NDOG/NWOG | **partial / missing** | 221-222, 965-966 | London 02:00 and NY 09:30 opens are confluence anchors (09:30 misaligned on 1H, G3). No 08:30 open, weekly open or opening gaps. The gaps belong to the PD-array domain |
| G9 | Macros, Silver Bullet | **missing** (correctly) | none | Evidence none or negative (E16, E17). A volatility clock with 15-30 min buckets subsumes any genuine periodic burst |
| G10 | Power of 3 / Judas swing | **partial** (implicit) | 1580-1582 | `liqEvt` treats "raid then close back inside" as reversal and "close beyond" as continuation, at any time. Evidence: first-break fades are coin flips in FX and continuation in crypto (E7, E8), and sweeps continue in G10 FX. Covered by ict_liq ICT-2 (learn the sign). Session-conditioning the learned sign is a possible extension |
| G11 | CBDR / Asian / Flout SD projections | **missing** | none | Not recommended as targets: no evidence, and redundant with clock-aware distance. Could be optional confluence anchors tested by the ledger |
| G12 | Daily / weekly profiles; day-of-week | **missing** | none | No day-of-week logic at all. Weekly profiles have no evidence beyond the arcsine law. The real effect (Monday about 20% lower range, E14) is a variance factor, which belongs in the clock (TIME-1) |
| G13 | IPDA 20/40/60-day ranges, quarterly shifts | **missing** | (PWH/PWL 1795-1799; HTF pivots 1782-1789; htfEQ 968) | Weekly extremes and HTF (D in Day Trading mode) pivots exist. No N-day extremes or 60-day equilibrium. Evidence weak or none: a P3 source for the HTF objective |
| G14 | Seasonal tendencies, pre-FOMC, overnight drift | **n/a** | 917 (`potMu`) | Drift effects are far smaller than intraday σ. Not worth modelling for PoT |
| G15 | Scheduled news times | **missing** | none | Pine has no economic calendar. The clock learns the *average* 08:30 / 10:00 bump. FOMC days (5.2x) need a manual event input (TIME-7) |
| G16 | Ledger baseline and PoT calibration | **partial / biased** | 1313-1322, 1426-1431, 1461-1499, 2037-2045 | `pBase` uses the same time-blind σ and pooled surface. Trials open when a new DOL is chosen, and choices concentrate in killzones (1941 multipliers; 976 doubles hysteresis off-KZ), so `pBase` is too low there and **EDGE is inflated by timing**. Trials do not store the model PoT, so PoT calibration (the headline number) is never measured |
| G17 | Time-aware ETA / session horizon | **partial** | 2106-2126, 2240 | `ETA|hit` is the median bars-to-hit of past hits at similar distance: bars, not clock time. Horizon H is a fixed bar count, so "will it be taken before the NY close?" cannot be asked |
| G18 | Intraday momentum / opening drive | **partial** | 1536-1541, 1893 | Displacement enters D with a 12-bar half-life, time-agnostic. No session-return term. Evidence strong but small, equities only (E12) |

---

## 4. Proposals (best first; maximum 10)

General notes for all specs:
- All learning and state updates run only when `barstate.isconfirmed` is true.
- Functions are declared before use. Globals must precede the functions that read them. New inputs go in the existing groups.
- Existing compiled constructs (`array`, `map`, `for…in`, methods, `str.*`, `timeframe.change`) are reused.
- Built-in signatures used below were checked in the local v6 reference (reference/time.md): `hour(time, timezone)`, `minute(time, timezone)`, `dayofweek(time, timezone)`, `time(timeframe, session, timezone, bars_back, timeframe_bars_back)` (negative `bars_back` from -1 to -500 projects future bar times), `time_close(timeframe, session, timezone, …)`.
- No new `request.*` call is needed except in TIME-8, which adds one.
- Pine has no bitwise operators: use separate arrays or bools.

### TIME-1 (P1): learned volatility clock for PoT, reach, race and the empirical surface
- **Why.**
  - The engine's headline number (PoT %), the reach pillar of proximity, the WIN≤H race and the reach bands all assume the next H bars have the volatility of the last 50.
  - Intraday they do not: the peak/quiet hour ratio is 2.1-4.0x (E2), release hours run up to 5.2x (E3), and Mondays run about 20% quieter (E14).
  - On a 5m chart with the defaults, a displayed 20% PoT is really about 50-55% at 08:30-09:30 ET and about 9-14% in the afternoon (E18).
  - A volatility clock is the quantitative, symbol-learned form of ICT's killzones, macros and session timing. It also generalises: it learns whatever periodicity the symbol actually has (crypto included).
- **Model:**

  `r²_t ≈ L_t · a[b_t] · c[d_t]`

  - b is the time-of-day bucket and d the weekday, both in `tz`.
  - L is the deseasonalised per-bar variance level.
  - Forward variance over the next h bars: `V(h) = L · Σ_{k=1..h} a[b_{t+k}] · c[d_{t+k}]`.
- **Inputs (G_POT):**
  ```
  bool  useClk = input.bool(true, "Volatility Clock (time of day)", group = G_POT,
    tooltip = "PoT, reach and race use the variance this symbol normally shows in the coming bars (learned by time of day and weekday) instead of the last bars' volatility.")
  int   clkMin = input.int(30, "Clock Bucket (minutes)", options = [15, 30, 60], group = G_POT)
  float clkMem = input.float(40.0, "Clock Memory (days)", minval = 5.0, step = 5.0, group = G_POT)
  bool  useDow = input.bool(true, "Weekday Factor", group = G_POT)
  ```
- **Derived** (after line 309):
  ```
  int   chMin = math.max(1, int(timeframe.in_seconds() / 60))
  int   bkMin = math.max(clkMin, chMin)
  bool  clkOK = useClk and timeframe.isintraday and bkMin <= 240 and 1440 % bkMin == 0
  int   NBK   = clkOK ? 1440 / bkMin : 1
  float bpb   = bkMin * 60.0 / chartS                           // bars per bucket
  ```
  On D/W charts with `clkOK` false, a weekday-only factor can still be used (5-7 buckets). That is optional.
- **State** (STATE section, about line 1080):
  ```
  var array<float> clkA  = array.new<float>(NBK, 1.0)          // time-of-day factor a[b]
  var array<float> clkD  = array.new<float>(7, 1.0)            // weekday factor c[d]
  var array<int>   clkC  = array.new<int>(7 * NBK, 0)          // bars seen per (d, b): open-cell mask
  var float        clkL  = na                                  // deseasonalised per-bar variance (log-return²)
  var int          clkDy = 0                                   // days seen
  ```
- **Learning** (global scope, right after the PoT series at 914-920):
  ```
  int   cB  = int(math.floor((hour(time, tz) * 60 + minute(time, tz)) / bkMin))
  int   cD  = dayofweek(time, tz) - 1
  float r2  = math.pow(math.log(close / close[1]), 2)          // close-to-close: includes session gaps
  if clkOK and barstate.isconfirmed and not na(r2)
      float s0 = clkA.get(cB) * (useDow ? clkD.get(cD) : 1.0)
      if not na(clkL) and clkL > 0
          float x  = math.min(25.0, r2 / (clkL * s0))         // standardised and clipped (news spikes)
          float aB = 1.0 - math.pow(0.5, 1.0 / (clkMem * bpb))
          clkA.set(cB, clkA.get(cB) * (1.0 + aB * (x - 1.0)))
          if useDow
              float aD = 1.0 - math.pow(0.5, 1.0 / (clkMem * NBK * bpb / 5.0))
              clkD.set(cD, clkD.get(cD) * (1.0 + aD * (x - 1.0)))
      float y = r2 / s0
      clkL := na(clkL) ? y : clkL + 2.0 / (potLen + 1.0) * (math.min(y, 25.0 * clkL) - clkL)
      clkC.set(cD * NBK + cB, clkC.get(cD * NBK + cB) + 1)
  if clkOK and barstate.isconfirmed and timeframe.change("D")
      clkDy += 1
      // renormalise: bar-weighted mean of a over traded buckets = 1, likewise c; fold the scale into clkL
  ```
  - Use the bar-weighted mean with weights `w_b = Σ_d clkC[d·NBK+b]`.
  - Shrink thin buckets toward 1: `a_b ← (n_b·a_b + 20) / (n_b + 20)` when used.
- **Open-cell mask.** A cell counts as open if `clkC[cell] ≥ 0.3 · (clkDy / 7) · bpb`, i.e. it traded on at least 30% of its weekdays. This skips weekends, the 17:00-18:00 futures break and the overnight hours of RTH-only stocks.
- **Forward variance** (STATE HELPERS, before `f_potModel` at 1303):
  ```
  // Σ variance (log-return²) of the next h bars, walking the weekly grid from the current bar
  f_fwdVar(int h) =>
      float v    = 0.0
      int   need = h
      int   b    = cB
      int   d    = cD
      int   into = (hour(time, tz) * 60 + minute(time, tz)) % bkMin
      int   take = math.min(need, math.max(0, int(math.floor((bkMin - into) * 60.0 / chartS)) - 1))
      v    += take * clkA.get(b) * (useDow ? clkD.get(d) : 1.0)
      need -= take
      int guard = 0
      while need > 0 and guard < 7 * NBK + 8
          b += 1
          if b >= NBK
              b := 0
              d := (d + 1) % 7
          if clkC.get(d * NBK + b) >= 0.3 * (clkDy / 7.0) * bpb
              int t = math.min(need, int(math.round(bpb)))
              v    += t * clkA.get(b) * (useDow ? clkD.get(d) : 1.0)
              need -= t
          guard += 1
      v * clkL
  ```
  - The cost is about H/bpb + (closed cells skipped) iterations: 5 for H = 30 on 5m with 30-min buckets, at most about 7·NBK + 8 over a weekend.
  - Optional O(log n) version: rebuild prefix sums `cumVar` and `cumBars` over the 7·NBK grid once per day, then binary-search the end cell.
- **Wiring:**
  ```
  float fwdV = clkOK and clkDy >= 5 ? f_fwdVar(H) : na
  float sigH = na(fwdV) ? potSig : close * math.sqrt(fwdV / H)    // per-bar σ (price) for the coming H bars
  ```
  - Pass `sigH` instead of `potSig` at 1304, 1315, 1360 and 1948 (the `sig` argument of `evaluate`).
  - `potMu` (drift) is unchanged.
  - Fallback: `potSig` until the clock has 5 days.
- **Phase B (z-unit empirical surface).**
  - Store `float fwdSd = close * math.sqrt(fwdV)`, the price σ of the window that starts now.
  - In step 0 (1528-1532), use `sdH = fwdSd[H]` instead of `aH = atr[H]`, with the grid `bStepZ = 5.0 / NB`.
  - `f_empPoT` takes `z = d / fwdSd`.
  - Reach bands convert back for display: `dATR = z · fwdSd / atr`.
  - For Brownian motion `P(max ≥ z·√V)` is horizon-invariant, so the z-surface also serves any horizon (TIME-4). It keeps the empirical fat-tail and mean-reversion shape while the clock supplies the timing.
- **Ledger hook.** TIME-2 measures the gain (Brier score with the clock vs without).
- **Expected value.**
  - The PoT filter, the PoT label, the R:R race and the CORE/EXTENDED/STRETCH classes become honest by time of day.
  - Pre-open targets stop showing artificially low PoT; lunch-time targets stop showing inflated PoT.
  - Proximity's reach term ranks near-in-time-reachable pools correctly (a 3 ATR pool before the NY open beats a 1.5 ATR pool at 12:15 when variance says so).
  - This replaces the ad-hoc `f_kzAff` (TIME-5) with one coherent mechanism.
- **Evidence:** strong (E1-E3, E14, §2.2, E18).
- **Risk.**
  - Thin history per bucket on short charts: mitigated by shrinkage, the 5-day gate and long memory (the clock learns from **all** loaded bars, not only `calcBars`).
  - Holidays and early closes overstate V on those days.
  - US/UK DST mismatch weeks smear the London bucket. Optionally offer a "Clock timezone" input (the exchange timezone for non-US symbols).
  - Phase B changes the surface units: verify the reach-band display.
  - Every edit stays non-repainting (updates are confirmed-bar only).
- **Effort:** L in total. Phase A (analytic σ) is M; Phase B is M.

### TIME-2 (P1): time-aware ledger (clock baseline, PoT calibration A/B, killzone-split edge)
- **Why.**
  - The ledger's EDGE compares hits with `pBase`, a time-blind random-level baseline (G16).
  - DOL choices cluster in killzones, so EDGE partly measures *timing*, not level selection.
  - PoT, the number traders act on, is never checked for calibration.
  - The clock's value should be proven on the user's chart, not asserted.
- **Trial fields** (type at 375-395):
  - `float pMod`: displayed PoT at open (clock);
  - `float pAlt`: same, computed without the clock;
  - `int kz0`: killzone at open.
- **f_openTrial (1426).**
  - `pMod = f_potModel(d, side, potMu·side)` with `sigH`.
  - `pAlt` = the same with `potSig`.
  - `pBase = f_potBase` with the clock.
  - `kz0 = kz`.
- **f_book (1461).** Add:
  - `var array<float> calSt = array.new<float>(8, 0.0)` holding [n, Σy, Σp, Σ(y-pMod)², Σ(y-pAlt)², block-Σ of d, closed-block Σd², blockId], where d = (y-pMod)² - (y-pAlt)². Reuse the 2H-block cluster variance of `cluSt` (1463-1469) for a robust z of the Brier difference.
  - `var array<int> kzN, kzK` and `var array<float> kzE` (size 6), indexed by `kz0 + 1`: edge per killzone.
- **Panel** (Terminal, Accuracy = Full):
  - `PoT CAL  pred 44% · obs 46% · n 212`
  - `BRIER   .212 vs .231 no-clock · z 2.4 ✓`
  - `EDGE by KZ  LDN +5.8 · NYAM +6.3 · OFF +1.9 pp`
- **Value.**
  - Honest EDGE: timing is no longer counted as skill.
  - A direct, visible test that the time model helps on this symbol.
  - Shows whether killzone targets truly outperform. This feeds TIME-5.
- **Evidence:** moderate. The method is standard (Brier score, matched baseline, cluster-robust SE); the motivation is strong (G16, E18).
- **Risk.** Overlapping trials (handled by the block variance). The `pAlt` computation doubles PoT calls at trial open only (cheap).
- **Effort:** M.

### TIME-3 (P1): session-window correctness and coverage (overlap test, London close / index NY AM, ONH/ONL, NY PM)
- **Why.**
  - G3: on the default 1H execution chart the NY AM range misses 09:30-10:00, and the "NY open" is the 10:00 open.
  - G4: 10:00-11:00 ET is OFF-KZ.
  - G6: the most-watched index-futures levels (ONH/ONL) are absent.
- **(a) Overlap membership.** Replace every `not na(time(timeframe.period, sess, tz))` (799, 836, 971-974) with a minute-of-day overlap test. Parse each session string once.
  ```
  f_hhmm(string s, int at) => int(str.tonumber(str.substring(s, at, at + 2))) * 60 + int(str.tonumber(str.substring(s, at + 2, at + 4)))
  f_ov(int a0, int a1, int c0, int c1) => a0 < c1 and c0 < a1          // half-open interval overlap
  // window [sM, eM) in minutes of the NY day; eM <= sM wraps midnight; an end of "0000" means 1440
  f_inWin(int sM, int eM0) =>
      int  eM  = eM0 == 0 ? 1440 : eM0
      int  b0  = hour(time, tz) * 60 + minute(time, tz)
      int  b1  = b0 + math.max(1, int(chartS / 60))                     // a bar may run past midnight (b1 > 1440)
      bool hit = false
      if eM > sM
          hit := f_ov(b0, b1, sM, eM) or f_ov(b0 - 1440, b1 - 1440, sM, eM)
      else                                                                // wrapping window: [sM, 1440) ∪ [0, eM)
          hit := f_ov(b0, b1, sM, 1440) or f_ov(b0, b1, 0, eM) or f_ov(b0 - 1440, b1 - 1440, 0, eM)
      hit
  ```
  - Examples: "2000-0000" gives sM = 1200, eM = 1440; "1800-0930" wraps. A 4H bar 22:00-02:00 hits [0, 570) through the shifted copy.
  - An `exact` flag (`b0 == sM` on the opening bar) marks anchors that are approximations. Show "≈" in the HUD and tooltip when the chart's bars do not open at the session start.
  - Optional, exact 09:30 open on 1H/4H charts: `request.security_lower_tf(syminfo.tickerid, "30", [time, open], ignore_invalid_timeframe = true)`, read on confirmed bars only. This mirrors the VP feed at 982.
- **(b) Killzones.**
  - Add `kzLC = input.session("1000-1200", "London Close Killzone")` as kz 5 ("LDN CLOSE KZ").
  - Change the NY AM default to "0700-1100", or expose an "Index NY AM 0830-1100" preset.
  - `f_kzName` gains a code 5.
  - With TIME-1 and TIME-5 in place, the killzone stays a label and hysteresis hint, not a score multiplier.
- **(c) New session sources** (registry, like 1800-1809):
  - Overnight / Globex `sessON = input.session("1800-0930", "Overnight Range")`: `src 8` "ONH/ONL", tier 0.62.
  - NY PM `sessPM = "1330-1600"`: `src 9` "PM H/L", tier 0.55.
  - Optional NY lunch `sessLU = "1200-1330"`: `src 10` "LUNCH H/L", tier 0.45.
  - Each uses `f_sessTrack` with the overlap test. Add the codes in `f_tierW` (505-516), `f_levelName` (518-529) and the `src` comment (316).
  - `f_pushExt` de-duplicates identical prices (Asia/London extremes are often also the ONH/ONL) and keeps the higher tier.
- **Value.** Correct session pools and anchors on the most-used execution TF, plus the most-watched futures liquidity (ONH/ONL is broken 94.2% of RTH days; open above the ON midpoint → the high breaks first 76.2%; E11). The killzone label matches where activity actually is.
- **Evidence:** strong (doc-verified correctness, E2) and moderate (E11).
- **Risk.** Including a straddling bar adds pre-session prices (e.g. 09:00-09:30) to the NY range on 1H. This is flagged by `exact`. The lower-TF read is optional. More registry entries: the cap of 60 (1813) may need +10.
- **Effort:** S-M.

### TIME-4 (P2): "PoT by session end" and an ETA in clock time
- **Why.** ICT traders ask "will the PDH be taken in the NY AM / before the close?", not "within 30 bars?". Timing is predictable from the clock: the MO retrace median is 09:41-09:48 (E10), and 68.7% of ON breaks happen by 10:00 (E11).
- **Inputs (G_POT).**
  - `string potHor = input.string("Bars (H)", "PoT Horizon", options = ["Bars (H)", "Killzone End", "NY Close 16:00", "Day End 17:00"])`
  - `bool showEta = input.bool(true, "Show ETA (clock time)")`
- **Bars to the horizon.** The same grid walk as `f_fwdVar`, counting open-cell bars until the end minute: `hS`. Then `V = f_fwdVar(hS)`.
  - Analytic: `PoT_S = f_pot(d, close·√(V/hS), mu, hS)`.
  - Empirical: TIME-1 phase B with `z = d / (close·√V)`.
- **ETA.**
  - Walk the grid accumulating variance until `V(τ) ≥ (d / 0.6745)²`. That is the driftless median first passage: `P(touch by τ) = 2(1 - Φ(d/√V)) = 0.5`.
  - Convert the bar count k to a timestamp. On `barstate.islast` only: `time(timeframe.period, "", tz, -k)` for k ≤ 500, then `str.format_time(t, "HH:mm", tz)`.
  - Also an 80% "by" time: `V ≥ (d / 1.2816)²`.
- **Display.**
  - Terminal HUD: `PoT 30b 41% · →16:00 63% · ETA ~10:40`.
  - Clean label tooltip: `By 16:00: 63% · ETA ~10:40 ET`. The Clean face stays two lines.
- **Ledger.**
  - When the horizon is not "Bars", trials get `int hT` and `f_step` uses `t.bars >= t.hT` (1455).
  - The surface update keeps the fixed H; it is horizon-free in z-units.
- **Value.** A target that cannot plausibly be reached this session shows it (PoT decays toward the close). A natural stale-target filter, the "time stop" ICT traders apply by hand.
- **Evidence:** strong for the model (as TIME-1); UX value high.
- **Risk.** `time(..., bars_back < 0)` projects using the symbol session; holidays are not known. Treat the ETA as approximate and label it "~".
- **Effort:** M (requires TIME-1).

### TIME-5 (P2): replace the fixed killzone affinity with a clock-consistent learned affinity; continuous hysteresis
- **Why.** `f_kzAff` (597-602) adds +5-20% to session and PD pools in fixed killzones, regardless of distance. A random walk on the clock already explains the raids (§2.2), FX respects the Asian range more than random (E6), and TIME-1 puts timing into reach. Keeping the multipliers double-counts the effect and biases the ledger (G16).
- **Input.**
  - `string kzAffMode = input.string("Learned", "Killzone Affinity", options = ["Learned", "Fixed (legacy)", "Off"])`.
  - Default "Off" until the ledger has 40 outcomes.
- **Learned affinity.**
  - Cells: killzone at snapshot (0-5) × source class (session pools 3-5 and 8-10; PD/PW 6-7; other) = 18 cells.
  - Outcomes come from the ict_liq ICT-1 candidate probes (preferred) or from DOL trials, each scored against the **clock-aware** `pBase`.
  - `lift = ((k + 2) / (e + 2)) / ((K + 2) / (E + 2))`, shrunk with `w = n / (n + 40)`, bounded to [0.85, 1.15].
  - Applied at 1941 instead of `f_kzAff`.
- **Hysteresis (976).** Replace the binary rule with:

  `hystEff = hyst · f_clamp(math.sqrt(clkL · H / fwdV), 1.0, kzHx)`

  The target becomes stickier in proportion to how quiet the coming bars are expected to be. 10:00-11:00 is no longer "off". The rule falls back to the current binary one when the clock is off.
- **Value.** Removes an unsupported bias and lets the chart reveal any real session affinity. It also makes TIME-2's per-killzone EDGE meaningful.
- **Evidence:** moderate: §2.2 baselines, E6-E9.
- **Risk.** Learning noise with few outcomes (shrinkage plus bounds). Users who like the ICT narrative may want "Fixed (legacy)", which stays available.
- **Effort:** S with ICT-1, M without.

### TIME-6 (P3): midnight open as a candidate target ("Target: MO"), ledger-gated
- **Why.** The only time anchor with a measured excess over a random walk: RTH revisit 65.6-68.0% vs 52-61% for the random walk on the clock (E10). It is strongly distance-dependent and early (median 09:41-09:48). Traders explicitly use the MO as a draw. Today it is only a confluence anchor (1931).
- **Spec.**
  - New `kind 8 = OPEN`: a magnet, not liquidity.
  - `touched` = touch. `side` is recomputed each bar from its position against `close`. `price = top = bottom = midOpen`, with zone depth `0.10·atr`.
  - `src 11 = MO`; optional `src 12 = 08:30 open` and `src 13 = weekly open`, as inputs.
  - Created when `midOpen` sets (`f_sessOpen` transition), expired at 16:00 or when touched.
  - Pillars: proximity and reach as usual (clock-aware). Freshness counts from the session open. Confluence as usual. Density = 0.35 + 0.30 if the overnight direction disagrees with the gap (E10: 77-82%).
  - `grp 4 = OPENS` in the ledger (stats arrays of size 6).
  - Clean code "MO".
- **Value.** A frequently correct, early-session target that the ledger can confirm or reject per symbol. It is also a sanity check on the clock (its ETA is usually in the first 30 minutes).
- **Evidence:** moderate (E10, E13).
- **Risk.** The kind enum is touched in several helpers: `f_newLevel` side logic (1085), `touched` (624), `isLiquidity`/`isArray`, `grp` (636), `f_levelName`/`f_shortName`, and the `delivAt` crop (1566). A careful but mechanical change.
- **Effort:** M.

### TIME-7 (P3): manual scheduled-event input (FOMC / CPI / NFP) that scales the clock
- **Why.** Pine has no event calendar. The clock learns the *average* 08:30 bump, but the FOMC hour is 5.2x normal and CPI 2.1-2.7x (E3), and both are known in advance.
- **Inputs (G_POT).**
  - `bool evOn = input.bool(false, "Scheduled Event")`
  - `int evT = input.time(timestamp("2026-12-16T14:00:00-05:00"), "Event Time")`
  - `float evX = input.float(3.0, "Event Variance x", minval = 1.0)`
  - `int evMin = input.int(60, "Event Window (min)")`
- **Spec.** In `f_fwdVar`, cells whose projected time falls in `[evT, evT + evMin)` get their variance multiplied by `evX`. The PoT label shows "⚑ EVENT".
- **Value.** Correct reachability into known news, and an honest warning that PoT is event-driven.
- **Evidence:** strong for the magnitudes (E3; Andersen-Bollerslev-Diebold-Vega 2003).
- **Risk.** User error in the time zone of `input.time` (it is a UNIX timestamp, so it is unambiguous once set).
- **Effort:** S.

### TIME-8 (P3): IPDA 20/40/60-day extremes as registry sources for the HTF objective
- **Why.** These are the ICT "where is the big liquidity" levels. They are cheap to add; the evidence is weak, so they go through the registry and ledger, not fixed weights.
- **Spec.** One `request.security(syminfo.tickerid, "D", …, lookahead_on)` call, gated by `f_tfSafe("D")`:
  ```
  [ta.highest(high, 20)[1], ta.lowest(low, 20)[1], ta.highest(high, 40)[1], ta.lowest(low, 40)[1],
   ta.highest(high, 60)[1], ta.lowest(low, 60)[1], time[1 - ta.highestbars(high, 60)[1]], time[1 - ta.lowestbars(low, 60)[1]]]
  ```
  - Push to `extReg` when a value changes: `src 14/15/16` = "20D/40D/60D H|L", tiers 0.70 / 0.78 / 0.85.
  - Anchor with `f_barAtTime`.
  - Add the 60D equilibrium to the confluence anchors (1931).
  - They feed the HTF objective naturally (ranked without proximity, 1984-1989).
- **Value.** Swing traders get the IPDA map; the ledger shows whether those pools are hit above baseline.
- **Evidence:** weak (no touch study; N-day extremes are widely watched).
- **Risk.**
  - Overlap with PWH/PWL and HTF pivots: handled by de-duplication and the tier upgrade.
  - One more request (limit 40; currently about 6).
  - The dynamic index `time[1 - ta.highestbars(...)]` inside the requested expression may hit a max_bars_back error in the daily context. The safe fallback is to request prices only and anchor them on the chart with `f_anchorScan` (1141) or `f_barAtTime` (1191).
- **Effort:** S.

### TIME-9 (P3): equity-index session-return continuation in D (last hour), ledger-gated
- **Why.** The measured opposite of the Judas narrative: intraday momentum. For SPY the first half-hour predicts the last half-hour (R² 1.6%; 2.6% with the 12th half-hour; E12). It is absent in FX and commodities.
- **Spec.**
  - Only when `syminfo.type` is "index" or "futures" on an equity-index root (input toggle, default off), and only between 15:00 and 16:00.
  - `mR = f_clamp((close - rthPrevClose) / (rthSd), -1, 1)`, where `rthSd` comes from the clock's RTH variance.
  - `drawD` gets `+ wR · mR`, with wR = 0.15.
  - Grade with TIME-2's per-killzone EDGE; switch off automatically if the lift is ≤ 0 after 40 outcomes.
- **Value.** Small: a tilt for late-session target choice.
- **Evidence:** strong (but a small effect).
- **Risk.** Symbol classification. Futures sessions require the RTH previous close (via `session.isfirstbar_regular` / `islastbar_regular`).
- **Effort:** S.

**Not proposed, and why:**
- Macros and Silver Bullet as scoring (E16, E17): the clock covers genuine bursts.
- CBDR/Asia/Flout SD rungs as targets (no evidence; redundant with clock-aware distance). They could become optional ledger-tested confluence anchors later.
- Quarterly theory, quarterly shifts, named daily and weekly profiles (no evidence; arcsine baselines explain the folklore).
- Seasonal and FOMC drifts (negligible relative to intraday σ).

---

## 5. Sources

**ICT definitions (practitioner):**
- LuxAlgo Library: Killzones https://www.luxalgo.com/library/concept/killzones/ ; ICT Macros https://www.luxalgo.com/library/concept/ict-macros/ ; ICT Time Anchors https://www.luxalgo.com/library/concept/ict-time-anchors/ ; Standard-deviation Projections https://www.luxalgo.com/library/concept/standard-deviation-projections/ ; Quarterly Theory https://www.luxalgo.com/library/concept/quarterly-theory/ ; Judas Swing https://www.luxalgo.com/library/concept/judas-swing/ ; Session & Weekly Profiles https://www.luxalgo.com/library/concept/session-and-weekly-profiles/
- ICT Core Content notes (Arjo): CBDR https://arjoio.notion.site/Central-Bank-Dealers-Range-3af2483d98b7462fb34bc229d0af8b38 ; IPDA data ranges https://arjoio.notion.site/Using-IPDA-Data-Ranges-635ee59cfcb64311ae2a1525b8f9e5d1
- IPDA look-back ranges: https://fibalgo.com/education/ipda-ict ; https://backtrex.com/en/blog/ict-dealing-range-ipda-data-range-guide
- Killzone variants: https://innercircletrader.net/tutorials/master-ict-kill-zones/ ; https://tradingfinder.com/education/forex/ict-kill-zones
- Weekly profiles: https://funded.now/lessons/ict-weekly-profiles ; ICT Mentorship Core Content Month 07 (YouTube: "Short Term Trading Defining Weekly Range Profiles")

**Quantitative (large samples):**
- fxbacktest.app: When the daily high and low form https://fxbacktest.app/research/when-daily-high-low-forms/ ; Volatility by hour https://fxbacktest.app/research/forex-volatility-by-hour/ ; Economic release volatility https://fxbacktest.app/research/economic-release-volatility/ ; London opening-range break https://fxbacktest.app/research/london-opening-range-break/ ; Asian range break https://fxbacktest.app/research/asian-range-break/
- mypivots.com: Timing the High/Low of the Day (ES 1998-2004) https://www.mypivots.com/article/details/20/timing-the-high-low-of-the-day
- tradingstats.net: Midnight Open (9,226 days) https://tradingstats.net/midnight-open-futures-analysis/ ; Overnight range breakout (NQ 2,827 days) https://tradingstats.net/overnight-high-low-breakout-strategy/
- edgeful: Session breakout / IB / OCC https://www.edgeful.com/blog/posts/market-session-breakout-report-trading-strategy ; Day-of-week ranges https://www.edgeful.com/blog/posts/best-day-of-week-trading-strategy ; Midnight open https://www.edgeful.com/blog/posts/ICT-trading-strategy-midnight-open-retracement-report ; High/low by weekday (method) https://www.edgeful.com/blog/posts/high-and-low-by-weekday-report
- formiq.jp EURUSD by weekday/hour: https://formiq.jp/data/eurusd
- tradestar: Silver Bullet mechanical test https://tradestar.app/blog/i-tested-the-ict-silver-bullet-mechanically

**Academic:**
- Andersen, T. G. & Bollerslev, T. (1997). Intraday periodicity and volatility persistence in financial markets. *J. Empirical Finance* 4, 115-158. https://ideas.repec.org/a/eee/empfin/v4y1997i2-3p115-158.html (PDF: https://finance.martinsewell.com/stylized-facts/volatility/AndersenBollerslev1997b.pdf)
- Andersen, T. G. & Bollerslev, T. (1998). Deutsche Mark-Dollar volatility: intraday activity patterns, macroeconomic announcements, and longer run dependencies. *J. Finance* 53(1).
- Andersen, Bollerslev, Diebold & Vega (2003). Micro effects of macro announcements. *AER* 93(1).
- Gao, L., Han, Y., Li, S. Z. & Zhou, G. (2018). Market intraday momentum. *JFE* 129(2), 394-414. https://ideas.repec.org/a/eee/jfinec/v129y2018i2p394-414.html ; SSRN 2440866 https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2440866
- Boyarchenko, N., Larsen, L. C. & Whelan, P. The Overnight Drift. FRBNY Staff Report 917. https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr917.pdf
- Lucca, D. & Moench, E. (2015). The pre-FOMC announcement drift. *J. Finance* 70, 329-371 (cited, not re-verified here).
- Wood, R., McInish, T. & Ord, K. (1985). An investigation of transactions data for NYSE stocks. *J. Finance* 40(3) (U-shape; cited).
- Arcsine law: Aldous, Arc Sine laws and stock prices https://www.stat.berkeley.edu/~aldous/Real-World/arc-sine.html ; https://en.wikipedia.org/wiki/Arcsine_laws_(Wiener_process)

**Pine v6 docs (local mirror):**
- `docsrc/jabez4jc_pinescriptv6/concepts/sessions.md`, line 47: `time()` tests the bar's opening time.
- `reference/time.md`, lines 191, 210, 229, 290-301, 383-384: signatures of `dayofweek`, `hour`, `minute`, `time` (with negative `bars_back`) and `time_close`.

**This study's computations:** `study/ict_time_calc/baselines.py`, `baselines2.py`, `pot_error.py` and their `_out.txt` outputs.
