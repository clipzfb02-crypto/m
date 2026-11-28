# Asset-class specifics, sessions and events: final study (researcher A + researcher B)

Scope: how sessions, day boundaries, key levels, killzones, opens, news times, holidays, weekends and data artefacts differ across **CME index futures, other CME futures (energy, metals, FX futures), spot FX and spot metals, crypto, US equities and cash indices**, and what the engine must do on each so that its targets, PoT and ledger stay correct.

**Markers.**
- **[A]**: researcher A's content, kept.
- **[A✓]**: A's content, re-checked by B against a source or the data.
- **[B-corrected]**: A's content changed by B; the old claim is stated.
- **[B-new]**: added by B.

**What B did.**
- Re-ran A's scripts and read their code.
- Re-checked the Pine claims in the local v6 doc mirror (`docsrc/jabez4jc_pinescriptv6`).
- Re-searched the external claims (WebSearch summaries; Firecrawl had no credits, and cmegroup.com cannot be reached from this session).
- Ran five new tests (scripts and outputs in `study/asset_b_tools/`):
  - `asia_clock.py`: is a Tokyo-local Asia range a better London/NY target than the ICT NY-fixed range?
  - `fx_roll.py`: does the 17:00 NY rollover hour make fake sweeps?
  - `crypto_wkend.py`: is the weekend range taken more often than a weekday range at the same distance?
  - `gap_share.py`: what share of PDH/PDL "takes" are gap-throughs?
  - `gap_atr.py`: how much do session gaps inflate TR/ATR?

Sibling proposals this report builds on, with IDs as they stand in the **final** sibling reports. **[B-corrected]** A cited pre-final IDs ("TIME-3 overlap", "TIME-7 manual event", "SESS-3 per-family ledger"); those numbers are now wrong.

| Sibling | ID | What it does | Relation here |
|---|---|---|---|
| ict_time.final | TIME-1 (a) | Minute-of-day overlap membership for session windows | Used by ASSET-1, ASSET-6, ASSET-10 |
| ict_time.final | TIME-1 (b) | Exact session bounds on 1H from 30m intrabars | Used by ASSET-6 |
| ict_time.final | TIME-1 (e) | London DST tracking (+60 min in the US/UK mismatch weeks) | Replaces the London half of A's ASSET-2 |
| ict_time.final | TIME-3 | Volatility clock for PoT | Needs 7-day buckets on 24/7 symbols and an open/gap bucket on session-limited charts (ASSET-9) |
| ict_time.final | TIME-5 | Neutral killzone affinity, clock-based hysteresis | Makes killzone presets label-only |
| ict_time.final | TIME-7 | ONH/ONL registry pools, `src 8` | Code-space collision with A's ASSET-3 |
| ict_time.final | TIME-8 | Scheduled-event scaling of the clock (manual + NFP rule) | Extended by ASSET-5 |
| session_stats.final | SESS-6 | Day-boundary choice (Exchange / NY midnight / NY 17:00) | Kept; ASSET-3 measures whatever day is used |
| classic_levels.final | CL-2 | Neutral confluence pillar, no reference levels as positive anchors | So the RTH open/close are not added as anchors |
| classic_levels.final | CL-4 | Prior-session value target incl. settlement (`settlement_as_close.on`) | Covers "prior RTH close" (ES settlement = 16:00 ET) |
| ict_pd.final | ICTPD-6 | Large NDOG/NWOG gaps as targets | Gap levels are their domain; ASSET-2 only changes how gap bars sweep |
| calib_ml.final | CAL-10 | Gap filter (4 ATR) for the excursion surface | ASSET-4 gives it exact roll bars |
| calib_ml.final | CAL-3 | Candidate (shadow) ledger | Where per-family and per-asset grading lives |

---

## 0. Executive summary

1. **The engine reads no market metadata at all.** No `syminfo.type`, `syminfo.session`, `syminfo.root` or `current_contract`, and no measured session shape. [A✓]
   - Every symbol gets the same New-York-time sessions, killzones and anchors, and the same wall-clock bars-per-day. That produces visible mislabels:
     - "LDN H/L" on a US-stock extended chart is just 04:00-05:00 pre-market [B-new];
     - killzones and Asia/London/NY pools fire on crypto weekends;
     - Monday's crypto "PDH/PDL" is Sunday's thin range;
     - stock PD/PW freshness clocks run 1.9-2.3× too slow.
   - One market-profile switch (ASSET-1) plus a session-coverage check fixes the mislabels without new statistics.
2. **Gap-throughs are a large share of "sweeps" on gappy assets.** [B-new, `gap_share.py`]
   - GOOG daily (stock): 38% of PDH takes and 29% of PDL takes happen with the open already beyond the level.
   - ES/NQ 1H: 10% of PD-level takes are gap-throughs at the session open; on Sunday opens it is 38%. CL 9%/23%, SI 3%/16%.
   - The engine counts all of these as raids and feeds them into the draw vector D (1578-1582). ASSET-2 stops that.
3. **The bar clock is wrong on session-limited assets and on stub days.** [A✓ + B]
   - `f_tfRatio`, `hmD` and `hmW` use wall-clock seconds.
   - Stub "days" are pushed as full PDH/PDL:
     - the CME outage day of 2025-11-27/28 (4 bars);
     - Sunday mini-candles on FX feeds with a 00:00 UTC day.
   - ASSET-3 measures bars per day/week and merges stub days into the next day.
4. **Three of A's headline effects did not survive B's re-test.**
   - **Asia session clock.** A Tokyo-local Asia range (19:00-23:00 EST in US winter) is taken by London/NY at the same rate as the ICT NY-fixed range (20:00-00:00) at equal distance: logit coefficient +0.03, cluster-bootstrap 95% CI [−0.05, +0.11], 1,440 sides, 590 day-symbols [B, `asia_clock.py`].
     - A's Asia "DST fix" is a convention, not an edge; the 68-87% "different range" figure is pure geometry.
     - The London half is already TIME-1 (e).
     - **A's ASSET-2 is dropped.**
   - **Crypto weekend range.** With distance in non-deflated (weekday) ADR and the near side only, the weekend range is taken at the weekday rate: 91/88%, 76/75%, 52/52%, 36/34% across distance bins [B, `crypto_wkend.py`].
     - A's "+9 to +12 pp at the same distance" came from counting either side of a compressed range and from an ADR deflated by weekend days.
     - The weekend range is close (median 0.18 vs 0.36 ADR in 2023-25), so it is taken often. That is geometry, not magnetism.
   - **FX rollover hour.** On EURUSD 1-h (2017-18), the 17:00 NY hour breaks a prior 24-bar extreme on 10% of days (median hour 19%). Its wick-only share is 0.43 against a 0.52 median [B, `fx_roll.py`].
     - A's high wick fraction (0.70) is real, but at 1H it does not turn into excess fake sweeps.
     - The rollover guard is demoted to P3, for charts at or below 15m (ASSET-10).
5. **Continuous-futures rolls are real artefacts** on TradingView's default (unadjusted) continuous charts. [A✓, B-refined]
   - ES and NQ roll jumps run about +35-55 and +150-250 points per quarter at 2025-26 carry.
   - **[B-new]** One request (`backadjustment.on`) detects every historical roll exactly.
   - **[B-new]** A roll that happens live is only visible after the chart reloads.
6. **Scheduled events concentrate liquidity runs in time, by asset.** [A✓ + B]
   - This study's data:
     - FOMC 14:00 bar: GC 4.9× normal, ES 2.7×, CL 1.3× (n=8);
     - Thursday 08:00-hour bar (claims at 08:30): ES 1.33× vs Monday 1.02×.
   - Literature:
     - jumps follow FOMC, NFP and claims (Lee 2012, RFS);
     - top-of-book depth falls in the release minute (Scholtus et al. 2014);
     - most of the adjustment comes within about 40 s, with a small overreaction corrected in minutes 2-3 (Ederington & Lee 1995).
   - **[B-corrected]** Calendar rules break in practice. The 2025 and 2026 shutdowns moved NFP to:
     - Thursday 2025-11-20;
     - Tuesday 2025-12-16;
     - Wednesday 2026-02-11.
   - **[B-corrected]** The Fed revised its 2027 FOMC calendar on 2026-11-12: December moved to November 17, and October became strategy-only.
   - So recurring rules are "possible events", and date lists are user-maintained (ASSET-5).
7. **Structural changes that rule out constants.** [A, B-corrected dates]
   - CME crypto futures went 24/7 on **2026-05-29**. A had 06-01, which is the press-release and BVX date.
   - The SEC approved Nasdaq's extended hours on 2026-04-10, with a planned start on Sunday **2026-12-06**. It is not confirmed live.
   - TradingView now offers a 24h session (20:00-04:00 ET overnight via BOATS, Sunday-Thursday) on supported US stocks.

**Proposals (§4, best first).**

| # | Proposal | Priority |
|---|---|---|
| 1 | ASSET-1 Market profile + session-coverage guard | P1 |
| 2 | ASSET-2 Gap-through guard | P1 |
| 3 | ASSET-3 Measured session clock + stub-day merge | P1 |
| 4 | ASSET-4 Roll handler | P2 |
| 5 | ASSET-5 Asset-aware event calendar | P2 |
| 6 | ASSET-6 RTH H/L from a chart-side RTH tracker | P2 |
| 7 | ASSET-7 Data and timeframe guards | P3 |
| 8 | ASSET-8 Crypto weekend handling | P3 |
| 9 | ASSET-9 Gap-aware ATR and σ on session-limited charts | P3 |
| 10 | ASSET-10 Rollover close-confirm on ≤15m spot FX/metals | P3 |

---

## 1. Concepts: definitions and parameters

### 1.1 Trading day per asset class [A✓, B-corrected rows marked]

| Asset | Trading day (New York time unless noted) | TradingView daily bar | Notes |
|---|---|---|---|
| CME index futures (ES, NQ, YM, RTY + micros) | 18:00 → 17:00; daily halt 17:00-18:00; Sunday 18:00 opens **Monday's** day | ETH (named session `"regular"`) | RTH 09:30-16:15 ET = named session `"us_regular"` (concepts/sessions.md: ES1! "regular" is ETH; RTH chart = `"us_regular"`). Daily settlement = 30 s VWAP ending 16:00 ET (classic_levels §1.10). [B-new] A 15-min halt 16:15-16:30 ET is listed by secondary sources (MarketsWiki); not verified on CME's spec page |
| Other CME/NYMEX/COMEX futures (CL, NG, GC, SI, 6E, 6B, ZN) | Same Globex 18:00 → 17:00 | ETH | Pit-era "RTH": CL 09:00-14:30, GC 08:20-13:30. Named RTH sessions for these products were not verified |
| Spot FX | 17:00 → 17:00 NY on most feeds; week Sun 17:00 → Fri 17:00 | Feed-dependent | Pine docs: on FXCM:EURUSD "the Monday session starts on Sunday, 17:00" (reference/time.md, `time_tradingday`). [B-new] Feeds on a 00:00 UTC day (common on GMT-server brokers) make a Sunday stub candle; ASSET-3 merges it |
| Spot metals (XAUUSD, XAGUSD) | 18:00 → 17:00 NY, daily break 17:00-18:00 (mirrors COMEX) | Feed-dependent | [B-new] Broker guides (CMC, TMGM): break 22:00-23:00 UTC in winter. The reopen at 18:00 has wide spreads |
| Crypto spot / perps | 00:00 → 24:00 **UTC**, 7 days | UTC day | Binance funding 00/08/16 UTC, faster when the rate is capped |
| CME crypto futures (BTC, MBT, ETH, …) | 18:00 → 17:00 until 2026-05-29; **24/7 since Fri 2026-05-29** with a weekly weekend maintenance window of at least 2 h | ETH | [B-corrected] A said 2026-06-01. CME's page gives the start as 2026-05-29 16:02 CT; trade press says it went live. 06-01 is the press release and the BVX volatility-futures date. The trade-date convention for weekend trades was not verified |
| US stocks / ETFs | RTH 09:30-16:00; pre 04:00-09:30; post 16:00-20:00; **[B-new]** 24h view adds 20:00-04:00 overnight (BOATS, Sun-Thu nights) on supported stocks | RTH | `session.regular` / `session.extended`; `session.ismarket` / `ispremarket` / `ispostmarket`. Pine docs: hourly regular-session bars start at 09:30, not on the hour (concepts/sessions.md) |
| Cash indices (SPX, NDX, DJI) | 09:30-16:00, no volume | RTH | The cash "open" prints before most components trade, so gap statistics are biased (session_stats §2.9) |

**Pine primitives** [A✓ against reference/syminfo.md, reference/time.md and concepts/sessions.md].
- `syminfo.type` (simple string): "stock", "fund", "dr", "right", "bond", "warrant", "structured", "index", "forex", "futures", "spread", "economic", "fundamental", "crypto", "spot", "swap", "option", "commodity".
  - [B-new] No "cfd" is listed, so index and metal CFDs must fall to a fallback or an empirical check (ASSET-1).
- `syminfo.root` (simple; "ES" for ES1!), `syminfo.basecurrency` ("BTC", "CAD" for 6C1!, "" for stocks), `syminfo.current_contract` (simple string, na unless continuous futures), `syminfo.timezone`, `syminfo.session`.
- **[B-corrected] `syminfo.session`.** The reference lists only `session.regular` / `session.extended`. The sessions concept page shows it returns `"us_regular"` on an ES1! RTH chart and `"xetr_regular"` / `"fwb_regular"` on FDAX. So it is the active named-session string.
- **[B-corrected] `syminfo.volumetype`.** The docs say "Only some data feed suppliers provide information qualifying volume … will return a value on some symbols only, mostly in the crypto sector."
  - So `"n/a"` does **not** mean "no volume".
  - A's ASSET-9 rule (force the volume profile off when the type is "n/a") would have switched VP off on most futures and stocks. See ASSET-7 for an empirical test instead.
- `time_tradingday`: 00:00 UTC of the bar's trading day. `dayofweek` uses the bar open, so on overnight sessions it can name the previous calendar day (reference/time.md).
- `time(tf, session, timezone)`: `session` and `timezone` are **series string** (reference/time.md). IANA zones handle DST.
- **[B-corrected] Session-string days.** "1700-1700:23456" is "an overnight session. The Monday session starts Sunday at 17:00" (concepts/sessions.md). For overnight windows the day digit names the day the session **ends**.
  - A's "Asia days `12345` (Sunday-Thursday evenings)" is therefore probably wrong; `23456` would be the overnight reading.
  - "2000-0000" (ending exactly at midnight) is ambiguous in the docs. ASSET-1 gates with `dayofweek(time, "UTC")` instead of day digits.
- `session.isfirstbar_regular`: "For futures, the ETH session *is* the regular session". On futures it fires at 18:00, not 09:30 [B-new, concepts/sessions.md].
- Request limits: 40 unique `request.*()` calls (64 on Ultimate). v6 requests are dynamic by default, so series ticker strings are allowed (writing_scripts/limitations.md; concepts/other_timeframes_and_data.md).

### 1.2 RTH vs ETH key levels [A✓; B-corrected Pine approach]
- **ETH PDH/PDL**: extremes of the exchange day (futures 18:00-17:00; stocks 04:00-20:00 on an extended chart).
- **RTH PDH/PDL**: extremes of 09:30-16:15 (index futures) or 09:30-16:00 (stocks).
- **Prior RTH close**: the gap reference. On index futures it is close to the 16:00 ET settlement, which CL-4 already covers.
- **ONH/ONL**: 18:00-09:30, covered by TIME-7.
- **[B-new] Request alignment risk.** A's `request.security(ticker.new(prefix, ticker, "us_regular"), "D", high[1], lookahead_on)` is only safe if the RTH daily series aligns to ETH chart bars by trading day. The docs do not say how a session-filtered daily series maps onto chart bars outside its session (18:00-09:30).
  - If it maps by bar time, the overnight would still show the day-before-yesterday's RTH high until 09:30.
  - A chart-side RTH window tracker (TIME-1 a/b) has no such ambiguity, anchors exactly, and emits at 16:15. ASSET-6 uses it.
- **[B-new] `f_anchorScan` on 1H ETH charts.** The scan (1141-1160) marks a level invalid when a later bar traded beyond it.
  - The 09:00-10:00 ETH bar contains pre-09:30 prices.
  - An RTH high below that bar's high would therefore be rejected.
  - The chart-side tracker records the anchor bar while tracking, so it avoids the problem.

### 1.3 Session clock and DST [A✓; B-corrected evidence]

| Window | ICT / engine (NY time) | Local-clock meaning |
|---|---|---|
| Asia | 20:00-00:00 | Tokyo 09:00 = 20:00 EDT but 19:00 EST; Shanghai/HK 09:00-09:30 = 20:00-20:30 EST / 21:00-21:30 EDT; Tokyo cash runs to 15:30 JST (01:30 EST) |
| Frankfurt open | 02:00 (engine "London Open" 0200-0300) | 08:00 CET = 02:00 ET, except 03:00 in the US/EU mismatch weeks |
| London/Xetra cash open | inside 02:00-05:00 | 08:00 London / 09:00 CET = 03:00 ET, except 04:00 in the mismatch weeks |
| NY | 08:30, 09:30 | Local; never shifts |

- **Mismatch weeks.** In 2026: Mar 8 → Mar 29 (US on DST, EU not) and Oct 25 → Nov 1. Japan and China have no DST.
- **[B-corrected] What the activity data show** (A's `dst2.py`).
  - The index-futures 03:00 → 04:00 spike shift in the mismatch weeks is clean: 93% of 15 days.
  - The EUR/GBP futures **02:00** bucket stays elevated in the mismatch weeks (+0.50 log-ratio, 93% of days) next to the new 03:00 bump (+0.77). The Frankfurt shift is not clean.
  - In US winter the index futures show bumps at **both** 19:00 (Tokyo) and 20:00 (China/HK/SGE).
  - So "Asia follows Tokyo" is one of several defensible clocks.
- **[B-new] Forecasting value.** None measurable for Asia (§2, B1). TIME-1 (e) covers London.

### 1.4 Weekends, gaps, halts, rollovers, rolls [A✓ + B-new]

| Asset | Weekend / halt | What happens to levels |
|---|---|---|
| CME futures | Fri 17:00 → Sun 18:00; daily 17:00-18:00 | First bar after a gap can open beyond a level. ES/NQ: **38%** of PD-level takes on Sunday opens are gap-throughs; weekday 18:00 opens about 3% [B, `gap_share.py`] |
| Spot FX | Fri 17:00 → Sun 17:00 | Thin Sunday open. At 17:00 the rollover widens spreads; bid-plotted charts can print wicks that never traded at mid |
| Spot metals | As FX, plus a daily 17:00-18:00 break | [B-new] Reopen at 18:00 with wide spreads (broker guides). EURUSD-1h hints: the 18:00 hour's wick-only share is 0.74, but on only 19 breaks |
| Crypto | 7 days | No gap. Saturday/Sunday compressed (0.46/0.72 of a weekend-inclusive ADR in 2023-25) |
| US stocks | Every RTH open gaps | GOOG daily: **38%** of PDH takes and 29% of PDL takes are gap-throughs; the overnight return carries **38%** of daily return variance [B, 2004-13] |
| Continuous futures | Roll: ES/NQ/YM/RTY quarterly; CL monthly; GC bi-monthly (Feb/Apr/Jun/Aug/Oct/Dec) | Unadjusted chart (TradingView default): price jump at the switch bar. [B-new] Size ≈ cost of carry S·(r−q)·T: ES about 0.6-0.8% of price (+35-55 pts), NQ about +150-250 pts at 2025-26 rates |

**Definitions for the engine.**
- **[B-corrected] Gap bar.** `(time − time[1]) ≥ max(2·chartS, 1800 s)`. A used 2·chartS only. The 30-minute floor stops thin crypto pairs with skipped one-minute bars from counting as gaps.
- **[B-corrected] Gap-through.** `open` is beyond the level's **near edge**: `lv.side == 1 ? open > lv.bottom : open < lv.top`, i.e. `nearEdge()`, 615-616.
  - A used `open > lv.top`, the far edge of a BSL zone (`top = price + zoneATR·atr`). That misses gaps that land inside the zone width.
- **Rollover window** (spot FX/metals): 16:55-17:15 NY; for metals add 18:00-18:10 (reopen) [B].
- **[B-new] TradingView roll timing.** Volume-driven per instrument, with a "fitted rule". The switch happens at a session boundary (TradingView support 43000691027, via search). It can be detected exactly with `ticker.modify(..., backadjustment = backadjustment.on)` (reference/ticker.md: "only affects the data from symbols with this option available").

### 1.5 Holidays, half days, outages, stub days [A; B-corrected]
- **CME equity holidays.** Globex halts around 12:00 CT (13:00 ET) on holidays such as Thanksgiving; Black Friday closes early (12:15 CT in recent years).
- **[B-new] NYSE 2026 early closes** (13:00 ET): Fri **Nov 27** (tomorrow) and Thu Dec 24. July 3, 2026 is a full closure (Independence Day observed); July 2 is a normal day.
- **CME Globex outage.** A cooling failure at CyrusOne CHI1 started late Thursday 2025-11-27 and lasted more than 10 hours. It shows as a 4-bar "day" in the 1-h data.
- **[B-corrected] What the data say about short days** (A's own `asia_hol.py`).
  - Holiday and half days are compressed: median range/ADR ES 0.76, NQ 0.65.
  - Their extremes are **not** weaker next-day targets: taken next day "either side" 90.9% vs 87.6% on normal days (ES and NQ, n=11).
  - A's "weak previous-day liquidity" and the proposed tier demotion are unsupported.
  - The real defects are:
    - stub days (fewer than about 35% of normal bars: outage days, Sunday FX candles) treated as full days;
    - the wall-clock bar count (§1.8).

### 1.6 Scheduled macro and market events [A✓; B-corrected and B-new rows]

| Event | Time | Assets most affected | Recurrence / caveat |
|---|---|---|---|
| US data (CPI, PPI, retail sales, GDP, NFP) | 08:30 ET | Index futures, UST, gold, USD FX, crypto (weekdays) | Claims every Thursday. **[B-corrected]** NFP "first Friday" is unreliable: shutdowns moved it to Thu 2025-11-20 (Sep report), Tue 2025-12-16 (Nov report, with October's partial data) and Wed 2026-02-11 (Jan report) |
| US 10:00 data (ISM, JOLTS, sentiment) | 10:00 ET | Same | Monthly |
| EIA petroleum | Wed 10:30 ET | CL, RB, HO | Weekly. A's test was inconclusive in 2025-26 |
| EIA natural gas | Thu 10:30 ET | NG | Weekly |
| FOMC statement / press conference | 14:00 / 14:30 ET | All USD assets; gold most | 2026: Jan 28, Mar 18, Apr 29, Jun 17, Jul 29, Sep 16, Oct 28, **Dec 9**. **[B-new]** 2027 decision days (Fed revision of 2026-11-12): Jan 27, Mar 17, Apr 28, Jun 9, Jul 28, Sep 15, **Nov 17**. Oct 26-27 is strategy-only, with no decision expected |
| ECB decision / press conference | 14:15 / 14:45 CET | EUR FX, DAX, Euro Stoxx | 8 per year |
| WM/R 4 pm fix | 16:00 London; **[B-new]** 5-minute window 15:57:30-16:02:30 since Feb 2015 | FX; strongest at month-end | Daily. 11:00 ET (10:00 ET in the mismatch weeks) |
| Tokyo fix | 09:55 JST | JPY pairs | Daily |
| LBMA Gold Price | 10:30 and 15:00 London | XAU, GC | Daily |
| Earnings (stocks) | Pre-open or post-close | Single stocks | **[B-new]** `earnings.future_time` gives the next report time (fetched once at load) |
| Index option expiry (3rd Friday; quarterly "witching") | Expiry day | ES, SPX | **[B-new]** Pinning to the ATM strike on serial expiries 1992-2009 (Golez & Jackwerth 2012, JFE). A 2026 SSRN paper (Elms) finds no pinning in 2016-25 |

**Mechanics** [A✓ + B-new].
1. **Before the release.**
   - Depth is pulled and volatility is "somewhat elevated just before" (Ederington & Lee 1995, abstract).
   - About 9 of 20 market-moving releases drift in the surprise's direction from about 30 minutes before, worth about 40-50% of the total move. E-mini and T-note, 2008-14 (Kurov, Sancetta, Strasser & Wolfe 2019, JFQA). [A✓; the share is 40% in the 2017 draft and about half in the 2015/ECB versions]
2. **At the release.**
   - Most of the adjustment comes in many small moves that begin within about 10 s and are mostly done by about 40 s, with some overreaction corrected in minutes 2-3 (Ederington & Lee 1995, JFQA 30(1)).
   - Conditional-mean jumps scale with the surprise (ABDV 2003, AER).
   - [B-new] Jumps are predictable in time: they "follow soon after" FOMC, NFP and jobless claims (Lee 2012, RFS 25(2)).
   - [B-new] In the release minute, volume, volatility and best-quote depth rise while total book depth falls (Scholtus, van Dijk & Frijns 2014, JBF 38; SPY 2009-11).
3. **After the release.** Volatility stays well above normal for about 15 minutes and slightly elevated for hours (Ederington & Lee 1993, JF 48(4)).
   - **[B-corrected]** A's "later moves are essentially unrelated to the first minute" could not be confirmed in the abstracts. The supported reading: the first minute **is** the information-driven repricing, minus a small overreaction. A release-bar sweep reflects news, not a stop-run-and-reverse.
4. **[B-new] FOMC press conference.** Press-conference days carry a higher equity risk premium and attention (Boguth, Grégoire & Martineau 2019, JFQA). The 14:30 press conference is a second window after the 14:00 statement.

**DOL relevance.**
- Timing of liquidity runs: strong.
- Direction from a release-bar raid: none. Treat it as news, not a raid.
- Size per asset: moderate (this study, n=8 FOMC).

### 1.7 Session-directional drifts (documented, unstable: do not hard-code) [A✓ + B-new]
- **S&P futures overnight drift.** Concentrated at 02:00-03:00 ET, about **3.7%** p.a. in 1998-2019 [B-corrected from 3.6%]. It averaged close to zero after 2021, apparently because closing order-imbalance dispersion roughly halved. The overnight share of E-mini volume moved only from 15% to 16% (NY Fed Liberty Street, 2026-07-01).
- **Pre-FOMC drift.** +49 bp in the 24 h before FOMC, 1994-2011 (Lucca & Moench 2015); weak after 2011.
- **[B-new] FX fixing cycle.** The dollar appreciates in the hours before the Tokyo, Frankfurt and London fixes and depreciates after them. This makes a W-shaped 24-hour pattern, every weekday, month and year of a 20-year sample. It is stronger when volatility is high and liquidity low (Krohn, Mueller & Whelan 2024, JF 79(1)). Earlier work: currencies weaken in their own trading hours (Breedon & Ranaldo 2013).
- **[B-new] Market intraday momentum.** The first half-hour return, measured from the prior close, predicts the last half-hour return. R² about 1.6% in-sample and 1.2% out-of-sample, SPY 1993-2013 (Gao, Han, Li & Zhou 2018, JFE 129(2)).
- **Gold.** Night returns positive, day returns negative (COMEX; Chinese futures). **Crypto.** The Monday anomaly is not exploitable (Caporale & Plastun).
- **Verdict.** These are useful as timing context. As fixed priors in D they are not recommended: decay is documented for the two best-known (overnight drift, pre-FOMC). At most, a learned, ledger-gated term.

### 1.8 Bars per period on session-limited assets [A✓]

`f_tfRatio(tf) = in_seconds(tf)/chartS` (567-568), `hmD = √(86400/chartS)` (1792), `hmW = √(604800/chartS)` (1797). The real 5-minute counts:

| Asset | Bars/day | Bars/week | vs wall clock |
|---|---|---|---|
| US stock (RTH) | 78 | 390 | 0.27 / 0.19 |
| CME futures | 276 | 1380 | 0.96 / 0.68 |
| Spot FX | 288 | 1440 | 1.0 / 0.71 |
| Crypto | 288 | 2016 | exact |

- So PD/PW/HTF freshness runs √(288/78) = 1.9× (D) and √(2016/390) = 2.3× (W) too slow on stocks, and about 1.2× too slow weekly on futures and FX.
- Callers: 1780-1781 (registry half-lives), 1792, 1797, 1864 (HTF FVG). [B-new] Sibling CL-4 copies the same wall-clock constant.

### 1.9 Volume availability [A; B-corrected]
- Cash indices have no volume.
- **[B-corrected]** The test must be empirical, not `syminfo.volumetype` (§1.1).
- Guards already in place: LVN drawing needs `peak > 0` (2252-2254); `f_pathVol` needs `vpMean > 0` (1420). Nothing tells the user that VP is inert.

### 1.10 Continuous futures, settlement, roll [A✓ + B-new]
- **Back-adjustment.** Off by default on TradingView. When on, it shifts past contracts by "the difference between the Close of the new and old contracts for the nearest daily bar to the switching point" (support 43000685266; calib_ml also verified).
- **Settlement as close.** On by default for futures daily bars (support 43000685268). ES settlement = 16:00 ET.
- **[B-new] Live rolls.** Request histories are computed at load. If a roll happens while the chart is live, the back-adjusted request shows no step on the switch bar; the step appears only after a reload. A live roll is therefore handled only by the gap guard (ASSET-2) until the next reload.

### 1.11 [B-new] Session coverage and bar alignment
- **Coverage.** A tracked window (Asia, London, NY AM) that the chart covers only partly makes a mislabelled range:
  - US-stock extended charts start at 04:00, so "London 02:00-05:00" = 04:00-05:00 only (33% coverage);
  - stock 24h (BOATS) charts give Asia and midnight-open values from thin overnight prints;
  - holiday half-sessions cut NY windows.
  - `f_sessTrack` (836-866) has no coverage check.
- **Bar alignment.** TradingView's 1H/4H bars align to the session start:
  - CME futures: 18:00 → 4H at 18/22/02/06/10/14;
  - FX: 17:00;
  - crypto: 00:00 UTC;
  - US stocks RTH: 09:30 → 1H 09:30-10:30 … 15:30-16:00, and 4H = 09:30-13:30 plus a 2.5-hour 13:30-16:00 bar.
- **Consequence.** In Day Trading mode (D/4H/1H) the 4H structure (STF) is built from unequal bars on stocks. Killzones and 09:30 anchors on 1H charts need TIME-1 (a/b).

### 1.12 [B-new] Venue-specific wicks (crypto)
- **Event.** In the 2025-10-10/11 liquidation cascade (about $19 bn liquidated), illiquid tokens printed venue-specific wicks: ATOM about −99.96% momentarily on one venue. USDe hit $0.65 on Binance while staying about $0.99 on-chain.
- **Implication.** A single-venue wick through a pool is not market-wide liquidity being taken.
- **Evidence:** weak-moderate (secondary sources; facts disputed by venue).
- **Use here.** Documentation and an optional user-chosen confirm feed only (§4 "Not recommended").

---

## 2. Evidence (numbers and sources)

### 2.1 B's new tests (this report)

| # | Claim tested | Result | Script | Grade |
|---|---|---|---|---|
| B1 | A Tokyo-local Asia range (19:00-23:00 EST) is a better London+NY (02:00-12:00) target than ICT 20:00-00:00 | **No.** Take rate by distance bin (NY-fixed / Tokyo-local): 0-0.1 ADR 93.0/92.1%; 0.1-0.2 78.9/79.6%; 0.2-0.35 57.7/65.5%; 0.35-0.6 43.0/38.0%; >0.6 37.3/36.0%. Logit(taken ~ log dist + TokyoLocal) coefficient **+0.031**, cluster-bootstrap 95% CI [−0.053, +0.112]. ES/NQ/YM/RTY/GC/CL/SI 1-h, US-winter days, n = 1,440 sides / 590 day-symbols. The Tokyo range is wider (median distance 0.22 vs 0.19 ADR), so it is taken a little less overall (65.3% vs 68.1%): geometry | `asia_clock.py` | moderate (one winter, 7 symbols; clean null) |
| B2 | The 17:00 NY rollover hour on spot EURUSD makes fake sweeps | **No excess at 1H.** Breaks of the prior 24-bar extreme: 17:00 10.1% of days vs 18.9% median hour; wick-only share (close back inside) 0.43 vs median 0.52 (range 0.31-0.74). The 18:00 hour shows 0.74 on 19 breaks | `fx_roll.py` | moderate for 1H; untested ≤15m |
| B3 | The BTC weekend range is taken more often on Monday than a weekday range at the same distance | **No.** Near side only, distance in weekday-only ADR: 0-0.1 91.2/87.8%; 0.1-0.25 75.8/74.6%; 0.25-0.5 51.9/52.4%; 0.5-1 36.0/34.4% (weekend/weekday). Vol-neutral (distance / next-day range): 88/90%, 77/79%, 69/68%, 51/50%. 2023-25 raw take 75.5% vs 53.7% is explained by distance (median 0.18 vs 0.36 ADR). Monday range / weekday ADR 0.93-1.09 | `crypto_wkend.py` | moderate (8 years, n=1,661 windows) |
| B4 | Share of PDH/PDL takes that are gap-throughs | GOOG daily 2004-13: PDH 38.4%, PDL 29.4%. ES/NQ 1-h CME day: 10.3/10.0% of PD-level takes; Sunday opens 37.9/37.5%. CL 8.6% (Sunday 23.1%). SI 3.4% (16.4%) | `gap_share.py` | moderate (data fact) |
| B5 | Gap inflation of TR/ATR | ES/NQ/CL 1-h Sunday-open bars: TR/range median 1.34/1.31/1.10 (p90 2.4-2.7). ATR14 inflation on that bar median +1-2%, p90 +14-17%. GOOG daily: the overnight return is **38%** of daily return variance; median \|gap\| = 0.24 × median day range | `gap_atr.py` | moderate |
| B6 | Roll jumps in A's ES example | Jumps around roll weeks: ES Dec-14-2025 +56.5 and NQ +260.75 (Sunday opens: roll plus weekend mixed); Mar-15-2026 +34.5 / +164.75; Sep-2025 shows no clean step (the vendor flipped contracts on Sep 3 instead). Cost of carry predicts about +40-50 ES pts per quarter | ad-hoc check | moderate (vendor-specific data); the mechanism is strong |

### 2.2 A's evidence, re-graded

| # | Claim | Numbers | Source | A's grade → final |
|---|---|---|---|---|
| A1 | European-open spike moves with the US/UK mismatch | Index futures 04:00 > 03:00 bucket: W 21%, **M 93%**, S 46%; log-ratio +0.35 [0.24, 0.46] in M. M = 15 days | A `dst2.py` | moderate → **moderate** (n=15 days, one spring) |
| A2 | SGE gold open moves with US DST | GC 21:00 vs 20:45: W +0.11, M +0.55 (100%) | A `dst2.py` | moderate → moderate |
| A3 | Frankfurt 08:00 CET spike moves | 03:00 vs 02:45 ET in M +0.77 (100%), S +0.22 | A | moderate → **weak [B-corrected]**: the 02:00 bucket also stays high in M (+0.50, 93%), so two bumps, not a clean shift |
| A4 | US 08:30/09:30 spikes do not move | Same NY minute in W/M/S | A | moderate → moderate |
| A5 | Asia range differs by clock convention in US winter | 85-87% of days (index), 76% GC, 68% CL; 0% in summer | A `asia_hol.py` | strong (definitional) → **strong as arithmetic; no forecasting value (B1)** |
| A6 | Literature: FX activity follows local hours | EBS USD-JPY, EUR-USD: U-shapes for Tokyo and London participants but not NY; activity and volatility do not rise toward the NY close (Ito & Hashimoto 2006, JJIE 20(4)) | NBER w12413 abstract | strong → strong |
| B1 (A) | ETH extremes printed outside RTH | High 45.8%, low 50.0%, either 70-85%; median gap 0.19-0.28 ADR (index futures 1-min, n=216) | A `rth_eth.py` | moderate → moderate (3 months) |
| B2 (A) | RTH levels taken more next day | ES RTH PDH 58.5% vs ETH 50.9% | A | moderate → **moderate as geometry; no evidence of excess over distance** |
| C1 | Roll jumps on unadjusted continuous futures | See B6 | A `sanity.py` | strong → **strong (mechanism); A's ES example is mixed with a weekend gap** |
| C2 | TradingView back-adjust off by default | Support 43000685266 | Vendor | strong → strong |
| C3 | FX rollover-hour wicks | 17:00 NY median wick fraction 0.70 vs 0.51-0.61 | A `fx.py` | moderate → **moderate as a bar-shape fact; does not become fake sweeps at 1H (B2)** |
| C4 | Rollover spreads widen | CME "When FX futures pause" (2026): spot rolls at 17:00 NY; a fraction-of-a-pip spread "can expand to several pips"; size stops for the widest observed spread; FX futures pause 60 min daily. A's "0.5 → 18 pips" example was not verified (page unreachable). [B-new] BidFX: under 0.6% of daily FX volume trades 16:00-18:00 ET. Krohn, Mueller & Whelan (AEA 2020 draft): spreads highest and volume lowest at 17:00 NY | CME, BidFX via GlobalTrading, AEA draft | moderate → moderate |
| D1 | Holiday/short sessions compressed | Median range/ADR ES 0.76, NQ 0.65, GC 0.58 (GC includes data-gap days) | A | weak-moderate → weak-moderate. **[B-corrected]** Next-day take of short-day extremes is not lower (90.9% vs 87.6%) |
| D2 | Holiday volume | Black Friday about 45%, Christmas Eve about 20% of normal | Russell | weak → weak (not re-checked) |
| E1 | Thursday 08:00-hour bar | ES 1.33 vs Mon 1.02 (Tue 1.06, Wed 1.14, Fri 1.15); NQ 1.36 vs 1.07; GC 1.75 vs 1.27 (Tue-Fri 1.45-1.55) | A `news.py` | moderate → moderate (the Thursday excess over Tue-Fri is modest) |
| E2 | FOMC 14:00 bar vs trailing 20-day median | ES 2.70×, NQ 2.32×, GC **4.88×**, CL 1.34× (n=8) | A | moderate → moderate |
| E3 | EIA Wednesday in CL | Not distinguishable in 2025-26 | A | weak → weak |
| E4 | "Both sides of the pre-release range taken" | Noisy, n≈12 per weekday | A | weak/none → none |
| E5 | Release mechanics | Ederington & Lee 1993/1995; Fleming & Remolona 1999; ABDV 2003; **[B-new]** Lee 2012 (RFS 25(2)): jumps follow FOMC/NFP/claims; Scholtus et al. 2014 (JBF 38): total depth falls in the release minute | Abstracts | strong → strong. [B-corrected] "later moves unrelated to the first minute" is unverified; overreaction is corrected within minutes 2-3 |
| E6 | Pre-release drift | About 9/20 releases, from about 30 min before, 40-50% of the adjustment (2008-14) | Kurov et al. 2019 | strong → strong for that sample |
| E7 | Pre-FOMC drift | +49 bp / 24 h (1994-2011); weak afterwards | Lucca & Moench 2015 | strong but decaying |
| E8 | Gold fix | Elevated activity at the PM fix (Caminschi & Heaney 2014) | Abstract | moderate |
| E9 | WM/R fix | Volatility and reversal around the fix (Evans 2018). **[B-new]** 5-minute window since 2015-02-15; W-shaped fix cycle (Krohn, Mueller & Whelan 2024) | Abstracts, FCA, WM presentation | strong |
| E10 | EIA crude reaction | Effect lasts about 25 min | J. Energy Markets; Energy Journal | moderate |
| F1 | BTC weekend compression | Sat 0.83 → 0.70 → 0.46, Sun 0.86 → 0.81 → 0.72 of a weekend-inclusive ADR (2017-19 → 2020-22 → 2023-25) | A `crypto.py` | strong → strong |
| F2 | Weekend range taken on Monday | A: either side 81.7% vs 66.3%; "+9-12 pp within bins" | A | moderate → **none for any excess (B3); moderate for a high raw take rate from geometry** |
| F3 | Weekend volume share | Kaiko: 28% (2019 peak) → 13% (Jan-Feb 2024) → 16% (H1 2024); US venues 11%. A uniform 7-day spread would give 28.6% | The Block, Bloomberg | moderate → moderate [A✓] |
| F4 | BTC US-hours concentration | 13-20 UTC share of weekday activity 35.3% → 43.7%; Kaiko US hours 46% of 2024 volume | A, Bloomberg | strong → strong. [B-new] Baur, Cahill, Godfrey & Liu (2019, FRL 31): activity consistently lower in local evenings and on weekends across 7 exchanges; return anomalies do not persist |
| F5 | Funding-hour bars | 1.05-1.12 vs 0.98-1.02, confounded | A | weak → weak |
| F6 | Day-boundary sensitivity (BTC) | UTC vs NY-midnight day: high differs 45.7%, low 42.7% (n=2,927) | A | strong (definitional) |
| F7 | CME gaps | session_stats: 4-week fill 86.7% vs mirror 89.4%. **24/7 since 2026-05-29** | CME, trade press | strong (structural) |
| G1 | Overnight drift gone | 3.7% p.a. (1998-2019) → about 0 since 2021 | NY Fed 2026 | strong |
| G2 | FX own-hours depreciation, fix cycle | See §1.7 | Breedon & Ranaldo; Krohn et al. | strong (published), not re-measured |
| H1 | US equities 22-24 h | NYSE 22-h initial approval (Feb 2025); **[B-corrected]** SEC approved Nasdaq's extended hours on 2026-04-10, planned start Sun 2026-12-06 (unconfirmed); TradingView 24h session (BOATS) | Cooley, Arnold & Porter / CLS Blue Sky, TradingView support | strong (structural) |
| H2 | [B-new] Shutdown release shifts | NFP: Sep 2025 report Thu 2025-11-20; Nov report Tue 2025-12-16; Jan 2026 report Wed 2026-02-11 | Bloomberg Government, NPR, PBS | strong (fact) |
| H3 | [B-new] Option pinning | S&P futures pinned on serial option expiries 1992-2009 (Golez & Jackwerth 2012, JFE 106(3)); none in 2016-25 per Elms (SSRN 2026, secondary summary) | Abstracts | strong historically; decaying |

### 2.3 Reading [A + B]
- **Clock conventions are labels, not edges** (A5 + B1). Exchange opens move with DST, and activity follows them (A1, A2). But a pool defined on the "true" clock is not a better target at equal distance. The forecasting problem is distance and volatility, as the sibling studies found. Clock options are UX, not P1.
- **Gaps change what a "sweep" means** (B4). On stocks, a third of key-level takes are gap-throughs; on futures, Sunday opens. A gap-through jumps resting orders instead of running them, so it is not evidence about raid behaviour, whatever the raid → D mapping ends up being.
- **Artefacts are correctness bugs** (C1, B6). Rolls are definite and fixable; rollover wicks are minor at 1H (B2).
- **Calendar compression is geometry** (F1, B3, D1). Compressed periods leave close levels that get taken often. A distance-aware PoT and the ledger's random-level baseline already price that in. The engine needs the *levels* (and correct day definitions), not a bonus.
- **Events concentrate when runs happen** (E1, E2, E5, H2), per asset, with no directional content beyond the surprise itself. Calendars are fragile (H2, the 2027 FOMC revision).

---

## 3. Engine gap analysis (baseline_v2.pine; A's table re-checked by B)

| ID | Concept | Status | Lines | What the engine does / what differs |
|---|---|---|---|---|
| X1 | Asset-class detection | **missing** [A✓] | none (grep finds no `syminfo.type`, `.session`, `.root`, `.current_contract`, `.volumetype`) | One set of NY sessions, killzones and anchors, and wall-clock ratios, for every symbol |
| X2 | Day boundary | present (exchange day), no choice [A✓] | 945-946 | `f_rangeTrack(timeframe.change("D"/"W"))`, run every bar at global scope. CME 18:00, FX 17:00 (or 00:00 UTC on some feeds), crypto 00:00 UTC, stocks 04:00 on ETH. Choice = SESS-6 |
| X3 | RTH vs ETH key levels | partial [A✓] | 945, 952-961, 1790-1794 | Chart session only. No RTH H/L on ETH futures charts; stock ETH "PDH" includes pre/post-market. `nyOpen` (966) is a 09:30-10:30 confluence anchor only |
| X4 | Session clock / DST | **convention, partial** [B-corrected from "wrong"] | 107-109, 219-226, 799, 836, 948-950, 964-966, 971-974 | One `tz` for all windows. London mismatch weeks (about 4 a year): fixed by TIME-1 (e). Asia: Tokyo-local vs NY-fixed changes the range on most winter days, but with no forecasting difference (B1) |
| X5 | Sessions on 24/7 and RTH-only assets | partial [A✓ + B-new] | 106-109, 947, 971-976 | Crypto: sessions and killzones fire Saturday/Sunday (no day digits). Stocks RTH: Asia/London/midnight silently inert; NY AM KZ 07:00-10:00 covers only 09:30-10:00; 10:00-13:30 is OFF-KZ (hysteresis × `kzHx`, 976). **[B-new]** Stocks ETH: the London tracker records 04:00-05:00 and pushes it as "LDN H/L" (src 4, tier 0.60); the London KZ boosts Asia pools via `f_kzAff`. Stocks 24h (BOATS): Asia and midnight fire on thin overnight prints |
| X6 | Midnight open per asset | partial [A✓] | 220, 798-803, 964, 1931 | `f_sessOpen` → na where no bar opens in 00:00-01:00 (stocks; CME 4H bars at 22:00/02:00). Silently dropped from `anchors`. The sibling found MO is not special (+0.3 ± 1.1 pp), and CL-2 neutralises the confluence pillar, so the fix is labelling only |
| X7 | Gap handling in sweeps | **missing** [A✓; B-corrected details] | 1554-1585 (pool), 1580-1582 (`liqEvt`), 1587-1592 (registry), 1433-1460 (`f_step`) | A gap-through deletes the pool level and adds `evt·tier` to `liqEvt`. **[B-corrected]** The registry loop (1587-1592) only removes entries and does **not** feed `liqEvt`. The correct gap test is against `nearEdge()`, not `top`. `f_step` counts a gap-through as a hit (`tgtOpn` settles it at the open), which is right for "price reached X"; the panel cannot show how many hits were gaps |
| X8 | FX rollover | missing; **low impact at ≥1H** [B-corrected] | same | No rule. B2 finds no excess fake sweeps at 1H. Exposure is mainly on ≤15m charts of spot FX/metals |
| X9 | Continuous-futures roll | **missing** [A✓ + B-new] | 1554-1592, FVG/OB creation 1600-1760, `atr` 874 | The roll jump sweeps pools, makes a fake FVG and displacement, and shifts every distance by the basis. **[B-new]** A roll during a live session is invisible to a back-adjusted request until the next load (§1.10) |
| X10 | Holidays / short sessions | **[B-corrected]** missing only for **stub** days | 945, 1790-1794 | Holiday days are fine as PD sources (D1). Stub days (outage 4-bar day, FX Sunday candle, first partial day on the chart) are pushed as full PDH/PDL with tier 0.80 (506-515). The first-period issue is the overhaul's P1 "partial first-period PWH/PWL" |
| X11 | Bars per day/week | **wrong** on session-limited assets [A✓] | 567-568, 1780-1781, 1792, 1797, 1864 | Wall-clock ratios (§1.8) |
| X12 | Time → bar mapping | present, robust [A✓] | 1191-1207 | Binary search over `time[]` handles session gaps; only the beyond-window fallback uses wall clock |
| X13 | Scheduled events | **missing** [A✓] | none | No calendar, no flag, no event-aware variance, no ledger tag. TIME-8 adds one manual event |
| X14 | Fixes as time anchors | missing [A] | none | Timing context for FX/gold only |
| X15 | Crypto weekend range | missing [A]; **value = geometry only** [B-corrected] | none | On Monday, PDH/PDL = Sunday's compressed range (UTC day) |
| X16 | Volume availability | partial [A; B-corrected test] | 978-1016, 1384-1424, 2250-2287 | VP is silently inert on symbols with no volume. `syminfo.volumetype` cannot detect this (§1.1) |
| X17 | D/W chart gating | **partial, P1 on D** [B-corrected] | 945-946, 1790-1799 | **D chart:** `timeframe.change("D")` is true on every bar, so every candle's H/L is pushed as PDH/PDL (overhaul P1). **W chart:** PDH = prior week high (de-duplicated against PWH) |
| X18 | Settlement as close | n/a, minor [A✓] | 923-925 | HTF D structure uses settlement closes on futures; consistent with the D chart |
| X19 | Session-directional priors | absent (correctly) [A✓] | — | Keep out of fixed scoring |
| X20 | **[B-new]** Session coverage | missing | 836-866, 1800-1809 | `f_sessTrack` emits whatever bars fell in the window. No minimum coverage, so partial windows (stock ETH London, half-days) become full session pools |
| X21 | **[B-new]** Gap-contaminated ATR and σ on session-limited charts | partial | 874 (`ta.atr`), 915-917 (`chg`, `potSig`) | TR includes the overnight gap. `potSig` = stdev of close changes, including one gap change per day. On RTH stock charts the overnight return carries about 38% of daily variance in one bar per day. Futures 1H: small (B5) |
| X22 | **[B-new]** 4H STF on stocks | partial | 923-925 (`tfS`) | Day Trading STF = 4H. On RTH stocks a 4H "bar" is 09:30-13:30 plus a 2.5-hour 13:30-16:00 bar, so pivots and bias come from unequal bars |
| X23 | **[B-new]** `src` code space | crowded | 312-316, 505-529, 597-602 | Siblings claim src 8 (ONH/ONL, TIME-7), 8-10 (N-day extremes, ICTPD-5), 9 (PMH, CL-5), 11-14 (NDOG/NWOG/ORG/VALUE), and 14-16 (PA-1). A's ASSET-3 (src 8) and ASSET-6 (src 9) collide with these |

---

## 4. Proposals (best first; 10)

Ground rules:
- Structure, pool and ledger logic stays inside `barstate.isconfirmed`.
- New `request.security` calls use `[1]` + `lookahead_on` + `f_tfSafe`, except same-timeframe requests (noted).
- Globals are declared before the functions that read them.
- Defaults keep current behaviour where evidence is absent.

**Map from A's IDs.**

| A's ID | Becomes |
|---|---|
| ASSET-1 | **ASSET-1** (sharpened) |
| ASSET-2 (DST clock) | **dropped**: London half = TIME-1 (e); Asia half = no edge (B1) → §4 "Not recommended" |
| ASSET-3 (RTH) | **ASSET-6** (redesigned: chart-side tracker, P2) |
| ASSET-4 | split into **ASSET-2** (gaps, P1) and **ASSET-10** (rollover, P3) |
| ASSET-5 (roll) | **ASSET-4** (one request, phased) |
| ASSET-6 (crypto) | **ASSET-8** (P3, geometry only) |
| ASSET-7 | **ASSET-3** (stub merge instead of tier demotion; P1) |
| ASSET-8 | **ASSET-5** |
| ASSET-9 | **ASSET-7** (empirical volume test) |

**Source-code proposal for the synthesis.** Use named constants and keep asset sources clear of the siblings' 8-16: `const int SRC_RTH = 20`, `const int SRC_WKND = 21`. Every switch on `src` (`f_tierW` 505-516, `f_levelName` 518-529, `f_kzAff` 597-602, the comment at 316) gets explicit branches.

### ASSET-1 (P1, M) · Market profile: auto-detection, per-asset session presets and a session-coverage guard [A's ASSET-1, sharpened by B]

**Why.** X1, X5, X6 and X20 cause visible mislabels today:
- "LDN H/L" on stock pre-market;
- Asia/London/NY pools and killzones on crypto weekends;
- a silently missing midnight open on stocks.

Each later proposal reads the profile. No forecasting claim is made; this is correctness and UX.

**Inputs** (`G_CONF`, `display = display.none`):
```pine
string mktIn = input.string("Auto", "Market Profile", options = ["Auto", "Index Futures", "Other Futures", "FX / Spot Metals", "Crypto", "US Stocks", "Cash Index", "Other"], group = G_CONF, display = display.none,
  tooltip = "Auto reads the symbol type and checks the chart's own session shape. Sets sessions, killzone days, gap rules and event presets.")
float covMin = input.float(0.6, "Min Session Coverage", minval = 0.0, maxval = 1.0, step = 0.05, group = G_KEY, display = display.none,
  tooltip = "A session range is pushed only if chart bars covered at least this share of its window.")
```

**Detection** (global; `mktS` is simple, the empirical flags are series):
```pine
bool   isIdxRoot = str.contains("|ES|MES|NQ|MNQ|YM|MYM|RTY|M2K|EMD|NKD|", "|" + syminfo.root + "|")
string bc  = syminfo.basecurrency
string ty  = syminfo.type
int mktS = switch mktIn
    "Index Futures"    => 0
    "Other Futures"    => 1
    "FX / Spot Metals" => 2
    "Crypto"           => 3
    "US Stocks"        => 4
    "Cash Index"       => 5
    "Other"            => 6
    => ty == "crypto" or (ty == "futures" and (bc == "BTC" or bc == "ETH" or bc == "SOL" or bc == "XRP")) ? 3 :
       ty == "futures" ? (isIdxRoot ? 0 : 1) :
       ty == "forex" or bc == "XAU" or bc == "XAG" or bc == "XPT" or bc == "XPD" ? 2 :
       ty == "stock" or ty == "fund" or ty == "dr" ? 4 :
       ty == "index" ? 5 : 6
// empirical refinement (catches CFDs typed "spot"/"commodity" etc.): any bar on a UTC Saturday means the symbol trades 24/7
var bool sawSat = false
if dayofweek(time, "UTC") == dayofweek.saturday
    sawSat := true
int  mkt    = mktIn == "Auto" and sawSat and mktS != 3 ? 3 : mktS
bool is247  = mkt == 3
bool wkend  = is247 and (dayofweek(time, "UTC") == dayofweek.saturday or dayofweek(time, "UTC") == dayofweek.sunday)
bool stkETH = mkt == 4 and syminfo.session == session.extended
```
- Doc basis: `syminfo.type`, `syminfo.root`, `syminfo.basecurrency` and `syminfo.session` are simple strings (reference/syminfo.md); `str.contains(source, str)` (reference/str.md); `dayofweek(time, timezone)` (reference/time.md).
- The 24/7 flag becomes true on the first Saturday bar. Before that, a misdetected CFD on crypto behaves as today.

**Preset table** (applied only where the user left the defaults):

| mkt | Sessions pushed | Killzone days | Midnight open | Gap rule (ASSET-2) | Event preset (ASSET-5) |
|---|---|---|---|---|---|
| 0 Index futures | Asia, London, NY AM (+ ONH/ONL TIME-7, RTH H/L ASSET-6) | trading days | yes | on | US 08:30/10:00, FOMC |
| 1 Other futures | as 0 | trading days | yes | on; roll (ASSET-4) | CL/RB/HO EIA Wed 10:30; NG Thu 10:30; GC/SI US data + FOMC + LBMA |
| 2 FX / spot metals | Asia, London, NY AM | trading days | yes | on (+ ASSET-10 on ≤15m) | US data, FOMC, WM/R 16:00 London, Tokyo 09:55 JST |
| 3 Crypto | Asia/London/NY **weekdays only** (`not wkend`) | `kz := 0` on weekends, label "WEEKEND" | yes | on (thin-pair skipped bars excluded by the 30-min floor) | US data on weekdays, FOMC |
| 4 US stocks | NY AM only; Asia/London off; on `stkETH` a "PRE" range 04:00-09:30 optional | weekdays | **RTH open 09:30** replaces MO as the open anchor; label "OPEN" | on (every RTH open) | US data, FOMC, earnings via `earnings.future_time` |
| 5 Cash index | NY AM only | weekdays | RTH open | on, with the note "cash open is stale" | as 4 |
| 6 Other | as today | as today | as today | on | none |

**Session-coverage guard** [B-new; asset-agnostic, fixes X20].
- Extend `f_sessTrack` (836) with `var int nIn = 0`: reset at session start, `nIn += 1` while `inS`, and return `nIn` as a sixth element.
- The window length comes from TIME-1 (a)'s parsed minutes: `winMin = eM > sM ? eM − sM : eM + 1440 − sM`.
- At the push (1800-1809): `bool covOK = nIn * chartS / 60.0 >= covMin * winMin`. Push only when `covOK` (and `not wkend` on crypto).
- Results:
  - stock ETH London (1 bar of 3 on 1H) → 0.33 → not pushed;
  - normal 1H futures London → 1.0 → pushed;
  - half-day NY AM (09:30-12:00 on a 13:00-close day) → full → pushed.

**Display.**
- Terminal panel line: `MKT IDX FUT · DAY 18:00 ET · RTH 09:30-16:15`.
- Clean style: one tooltip line `Market: Index futures (auto)`.
- Killzone label "WEEKEND" in `f_kzName` (587-594).

**Where.**
- Inputs after 226.
- Detection in SERIES before 945.
- Gating at 947 (`intraOK`), 948-950, 964-966, 971-976.
- `f_sessTrack` 836-866; pushes 1800-1809.

**Evidence:** strong (doc-verified built-ins; definitional mislabels; F3/F4 weekend and US-hours activity).

**Risk.**
- Exotic symbols are misclassified: "Other" equals today's behaviour, and a manual override exists.
- The coverage guard drops a few legitimate partial windows on charts with missing bars; `covMin` is exposed.
- `mkt` becomes series once `sawSat` is used. Keep requests keyed on `mktS` (simple) so request contexts stay simple.

**Effort:** M.

### ASSET-2 (P1, S) · Gap-through guard: a session-open gap is not a raid [A's ASSET-4 gap half, corrected and quantified by B]

**Why.**
- B4: 38%/29% of stock PDH/PDL takes, and 38% of futures Sunday-open PD takes, are gap-throughs.
- The engine deletes the pool and adds `evt·tier` to `liqEvt` (1578-1582) on all of them, so a weekend headline gap becomes a "raid that held".

**State** (global):
```pine
bool gapBar = not na(time[1]) and (time - time[1]) >= math.max(2.0 * chartS, 1800.0) * 1000.0   // weekend, daily halt, overnight on RTH charts, holiday, outage
```
- Declare it at the top of SERIES, before 874, so that ASSET-9's ATR can read it. `chartS` is defined at 308.

**Rules.**
1. Sweep loop (1554-1585), liquidity levels only:
   ```pine
   bool gapThru = gapBar and (lv.side == 1 ? open > lv.nearEdge() : open < lv.nearEdge())
   ```
   - `if hit and lv.isLiquidity() and not gapThru` → the existing `evt` / `liqEvt` update (1579-1582).
   - `if gapThru` → remove as today, but ghost it as `"⤳ GAPPED"` instead of `"✕ SWEPT"` (1585).
   - Arrays are unchanged: a gap through an FVG is a delivery.
2. Registry (1587-1592): no `liqEvt` there [B-corrected]. Optionally count `gapRemovals` for the panel.
3. Ledger: add `bool gapHit = false` to `Trial`. In `f_step` (1436-1460) set `t.gapHit := hit and tgtOpn and gapBar`. The Full accuracy view shows `HIT% … (gapped k)`. `f_book` (1461) is unchanged: a gap-through still counts as reaching the target.
4. Live sweep alert (1505-1509): unchanged. It is a touch alert.

**Value.**
- D stops absorbing weekend and overnight news gaps as raid outcomes.
- Users see which hits were gaps.
- Measurable: compare `liqEvt` contributions and EDGE z before and after on ES1! and a stock.

**Evidence:**
- moderate (B4 data facts; the gap mechanism);
- none on whether excluding gaps improves the D forecast. Siblings already found the raid → D mapping itself weak, so this removes noise rather than signal.

**Risk.**
- A genuine stop-run that opens just beyond a level and keeps going is treated as a gap. That is the intent.
- Thin symbols skipping bars are covered by the 30-minute floor.

**Effort:** S.

### ASSET-3 (P1, S) · Measured session clock: bars per day/week, stub-day merge, no partial first period [A's ASSET-7, re-designed by B]

**Why.**
- X11: freshness is 1.9-2.3× too slow on stocks.
- X10: stub days (outage, FX Sunday candle) are pushed as full PDH/PDL.
- The overnight's P1 "partial first-period" bug shares the same root.
- **[B-corrected]** No tier demotion for holidays: short-day extremes are taken as often as normal ones (D1).

**State** (global, every bar, **before** the `f_rangeTrack` calls at 945):
```pine
var int   dBars = 0
var int   wBars = 0
var float bpd   = na              // EMA of bars per full trading day
var float bpw   = na
var bool  dSeen = false           // a complete day has been seen
var bool  wSeen = false
bool  dChg = timeframe.change("D")
bool  wChg = timeframe.change("W")
float dFrac = 1.0
float wFrac = 1.0
if dChg
    if dSeen and dBars > 0
        dFrac := na(bpd) ? 1.0 : dBars / bpd
        if na(bpd) or dFrac >= 0.6
            bpd := na(bpd) ? dBars : 0.9 * bpd + 0.1 * dBars
    dSeen := true                 // the first dChg closes the partial first day without emitting it
    dBars := 0
if wChg
    if wSeen and wBars > 0
        wFrac := na(bpw) ? 1.0 : wBars / bpw
        if na(bpw) or wFrac >= 0.6
            bpw := na(bpw) ? wBars : 0.9 * bpw + 0.1 * wBars
    wSeen := true
    wBars := 0
dBars += 1
wBars += 1
// stub period (< 35% of normal bars): no reset, so its range merges into the next period
[pdNew0, pdH, pdHB, pdL, pdLB] = f_rangeTrack(dChg and dFrac >= 0.35)
[pwNew0, pwH, pwHB, pwL, pwLB] = f_rangeTrack(wChg and wFrac >= 0.35)
bool pdNew = pdNew0 and dSeen[1]        // the partial first period resets the tracker but is never pushed
bool pwNew = pwNew0 and wSeen[1]
```
- A stub day does not reset the tracker, so its range merges into the next day.
- The partial first day resets the tracker but is never pushed: `dSeen[1]` is false on that bar, so `pdNew` is false. The `aPDH`/`aPWH` updates at 952-958 read the gated `pdNew`/`pwNew`.
- Results:
  - CME holiday Mondays (19/23 bars) → normal;
  - outage day (4/23) and FX Sunday candle (3/24) → merged.

**Clock replacement.** Declare right after the block:
```pine
f_tfBars(simple string tf) =>
    float wall = math.max(1.0, float(timeframe.in_seconds(tf)) / chartS)
    tf == "D" ? nz(bpd, wall) : tf == "W" ? nz(bpw, wall) : wall
```
- Use it at 1780-1781, 1864, 1792 (`hmD = math.sqrt(f_tfBars("D"))`) and 1797 (`hmW = math.sqrt(f_tfBars("W"))`).
- Keep `f_tfRatio` for intraday tfs.
- Note to the synthesis: CL-4 should use `f_tfBars("D")` too.

**Display.** Terminal shows `½ DAY` when the current day's projected bar count is below 0.75·bpd, as a label only.

**Evidence:** strong (arithmetic; stub days are definitional). Tier unchanged (D1).

**Risk.**
- `f_tfBars` is series-valued; callers already use the result as a series float.
- Before the first full day, the wall clock applies.
- On D/W charts `timeframe.change("D")` is true every bar. ASSET-7 gates key levels there.

**Effort:** S.

### ASSET-4 (P2, M) · Continuous-futures roll handler with one request, phased [A's ASSET-5, simplified and corrected by B; coordinate with CAL-10]

**Why.**
- C1/C2/B6: on TradingView's default unadjusted continuous charts, each roll (4 a year on index, 12 on CL, 6 on GC) jumps by the carry. That is about +40-50 ES points (6× a median 1-h range).
- The jump:
  - sweeps pools;
  - makes a fake FVG and displacement;
  - injects a jump into the ATR and the excursion surface (CAL-10);
  - shifts every stored distance.

**Detection** (same timeframe, one request; A used two):
```pine
bool   isCont = syminfo.type == "futures" and not na(syminfo.current_contract)
string tkAdj  = isCont ? ticker.modify(syminfo.tickerid, backadjustment = backadjustment.on) : syminfo.tickerid
float  cAdj   = request.security(tkAdj, timeframe.period, close)
float  adjD   = isCont ? close - nz(cAdj, close) : 0.0        // = −(future roll coefficients) on an unadjusted chart; ≡ 0 if the chart is already B-ADJ
float  rollJ  = adjD - nz(adjD[1], adjD)                       // +C on the switch bar
bool   rollBar = math.abs(rollJ) > 2 * syminfo.mintick and barstate.isconfirmed
```
- Doc basis: `ticker.modify(tickerid, …, backadjustment)`, where the setting "only affects the data from symbols with this option available on their charts" (reference/ticker.md). `syminfo.current_contract` is na unless the symbol is continuous (reference/syminfo.md).
- If the user enabled B-ADJ, `syminfo.tickerid` carries it and `cAdj == close`, so the handler is a no-op.
- **Live limit** [B-new]: a roll during a live session shows no step until the next load. Until then ASSET-2 treats the 18:00 roll open as a gap bar (no `liqEvt`).

**Phase 1** (S; ship first):
- On `rollBar`:
  - skip new FVG/OB creation and `dispUp`/`dispDn` for this bar and the next two (any 3-bar FVG window straddling the switch);
  - gap-guard sweeps as in ASSET-2;
  - expose `rollBar` to CAL-10 so the surface skips windows that contain it (more exact than CAL-10's 4-ATR heuristic).
- The panel shows `⚠ ROLL +56.5 — enable B-ADJ` for 50 bars.

**Phase 2** (M; input `rollMode = "Shift levels" | "Drop levels" | "Ignore"`, default "Shift levels"):
- Before the sweep loop on `rollBar`, add `rollJ` to every stored price:
  - `pool` (`price`, `top`, `bottom`, `oTop`, `oBot`);
  - `extReg[].px`;
  - iFVG trackers;
  - `aPDH`/`aPDL`/`aPWH`/`aPWL`;
  - `midOpen`/`ldnOpen`/`nyOpen` (via `var` copies);
  - `obSwingH`/`obSwingL`;
  - open `Trial`s (`edge`, `inv`, `entry`).
- Tooltips say "roll-adjusted +x".
- "Drop levels" ghosts them all as `⤳ ROLL`.

**Evidence:** strong (mechanism and vendor documentation). Moderate for the exact vendor example.

**Risk.**
- One extra request (about 8 of 40 after TIME-1 b).
- With "Shift levels", zones sit off their anchor candles by the basis (visual).
- Must be checked on ES1! and CL1! in TradingView before release.

**Effort:** M (Phase 1: S).

### ASSET-5 (P2, M) · Asset-aware event calendar on top of TIME-8 [A's ASSET-8, corrected by B]

**Why.**
- Runs concentrate at known times, per asset: E1, E2 (GC 4.9× vs CL 1.3× at FOMC), E5 (Lee 2012 jump timing; Scholtus depth).
- A release sweep carries news, not raid information (E5).
- TIME-8 has one manual event and an NFP rule.
- **[B-corrected]** Calendars break (H2: three NFP shifts in four months; the 2027 FOMC revision). Rules are "possible", and lists are user-maintained.

**Inputs** (`G_CONF`, `display = display.none`):
```pine
bool   evOn   = input.bool(true, "Scheduled Events")
string fomcIn = input.text_area("2026-12-09,2027-01-27,2027-03-17,2027-04-28,2027-06-09,2027-07-28,2027-09-15,2027-11-17", "FOMC decision days (14:00 ET)")
string evIn   = input.text_area("", "Other events: YYYY-MM-DD HH:MM (ET), comma-separated")
```

**Parsing** (once):
```pine
var array<int> fomcT = array.new<int>()
if barstate.isfirst and evOn
    for s in str.split(fomcIn, ",")
        string t = str.trim(s)
        if str.length(t) >= 10
            fomcT.push(timestamp("America/New_York", int(str.tonumber(str.substring(t, 0, 4))), int(str.tonumber(str.substring(t, 5, 7))), int(str.tonumber(str.substring(t, 8, 10))), 14, 0))
```
- `timestamp(timezone, y, m, d, h, mi)` handles DST through the IANA zone (reference/time.md). `str.split`, `str.trim` and `str.substring` exist (reference/str.md).
- `evIn` is parsed the same way, with hour and minute at characters 11-12 and 14-15.

**Recurring presets** (per bar; NY calendar via `dayofweek(time, "America/New_York")` and `dayofmonth(time, …)`). Kinds and default σ multipliers for TIME-8:

| Event | Assets | Certainty | σ multiplier |
|---|---|---|---|
| US 08:30, Thursday (claims) | all USD-linked; crypto weekdays only | certain | 1.15 |
| US 08:30, other weekdays | same | possible | 1.05 |
| US 10:00, weekdays | same | possible | 1.05 |
| EIA Wed 10:30 | CL/MCL/RB/HO | certain | 1.1 |
| EIA Thu 10:30 | NG | certain | 1.1 |
| LBMA 10:30 / 15:00 London | metals | certain | 1.05 |
| WM/R 16:00 London (11:00 ET; 10:00 in mismatch weeks via `timestamp("Europe/London", …)`) | FX | certain | 1.05 |
| FOMC 14:00 (list) | all USD assets | certain | 2.0 (σ); 2.5 on metals (√ of the 4.9× range ratio ≈ 2.2, rounded up because 14:30 adds a second window) |
| Earnings | stocks | `earnings.future_time` | HUD only |

- These are σ multipliers, as TIME-8 corrected them, not range ratios.
- The engine has no data calendar, so "possible" events get small multipliers.

**Uses.**
1. **UI.**
   - HUD line `⚑ FOMC 14:00 in 2h10`.
   - Clean style: a tooltip line, plus a small `⚑` on the label face only when an event falls inside the PoT horizon (`evT > time and evT ≤ time + H·chartS·1000`).
   - Optional alert "Scheduled event inside PoT horizon".
2. **Variance.** Hand the event timestamps and σ multipliers to TIME-8/TIME-3. No separate PoT path.
3. **Raids.**
   - A pool sweep whose bar overlaps `[ev − 1 min, ev + 15 min)` for a certain event adds **0** to `liqEvt`. A had 0.5. Input `evRaidW` (default 0.0).
   - Rationale: E5 says the move is the news repricing, not a stop run.
4. **Ledger.** Trials opened in `[ev − 30 min, ev + 15 min)` get `t.news := true`. The Full accuracy view splits HIT% and EDGE into news and non-news (`f_book` 1461: one more pair of counters).

**Evidence:**
- strong for the mechanics (E5-E7, E9, H2);
- moderate for the asset magnitudes (E1, E2, n=8 FOMC);
- none for any directional use.

**Risk.**
- Stale lists: the 2027 list above is current as of 2026-11-12, and the tooltip says to update it.
- NFP and CPI dates are not computable reliably (H2), so they stay "possible" or manual.
- Parsing runs once (`barstate.isfirst`).

**Effort:** M.

### ASSET-6 (P2, M) · RTH H/L key levels from a chart-side RTH window tracker [A's ASSET-3, re-designed by B]

**Why.**
- B1 (A): on index futures at least one ETH extreme differs from RTH on 70-85% of days (median 0.2 ADR).
- RTH levels are what AMT and stock traders watch (practitioner, weak).
- Stock ETH charts currently push a pre/post-market "PDH".
- No forecasting edge over distance is claimed (A's B2 is geometry). CAL-3 grades the family.
- **[B-corrected]** Approach changes:
  - A chart-side tracker replaces the named-session D request (alignment risk, §1.2).
  - Prior RTH close → CL-4 "Settlement".
  - The RTH open is not added to `anchors` (CL-2 neutralises confluence).
  - `SRC_RTH = 20` replaces src 8.

**Input.** `keySess = input.string("Auto", "Key Level Session", options = ["Auto", "Chart", "RTH", "Both"], group = G_KEY, display = display.none)`.
- Auto = Both for index futures; RTH for stocks on ETH charts (`stkETH`); Chart otherwise.

**Tracker.**
- Window: `rthWin = mkt == 0 ? "0930-1615" : "0930-1600"` (America/New_York).
- On charts ≤ 15m, use `f_sessTrack(rthWin, "America/New_York")` with TIME-1 (a) overlap membership. Every boundary is exact.
- On 30m/1H, use TIME-1 (b)'s 30-minute intrabar tracker `f_sessTrackLT`: 09:30 exact; 16:15 rounds to 16:30 (adds 15 ETH minutes; stated in the tooltip).
- Above 1H: off.
- The tracker records the exact anchor bar while tracking, so no `f_anchorScan` is needed (avoids its "later bar traded beyond" rejection on 1H; §1.2).
- **Emission** at the end of the window (16:15/16:00). That is the moment RTH closes, not at 18:00 as A's request would give.
- Coverage guard (ASSET-1) applies.

**Push** (next to 1790-1794):
```pine
if wantRth and rthEnd and rthCovOK
    regNew := f_pushExt(extReg, rthH, true,  SRC_RTH, rthHB, (rthH - rthL) / atr * 0.5, math.sqrt(f_tfBars("D"))) or regNew
    regNew := f_pushExt(extReg, rthL, false, SRC_RTH, rthLB, (rthH - rthL) / atr * 0.5, math.sqrt(f_tfBars("D"))) or regNew
```
- `f_tierW(SRC_RTH)` = 0.78 (below PD 0.80), `f_levelName` "RTH H"/"RTH L", `f_kzAff` neutral.
- `f_pushExt` de-duplicates prices equal to the ETH PDH/PDL; the higher tier (PD) stays.
- In "RTH" mode on stock ETH charts, the chart PD push (1790-1794) is replaced by this push. "PDH" then means the RTH high.
- **Request-free.**

**Evidence:**
- moderate (B1 A) for the levels differing;
- weak (practitioner) for usage;
- none for any edge.
- Feasibility: strong (named sessions documented; tracker = existing pattern).

**Risk.**
- Needs TIME-1 (a/b).
- Non-US futures have other RTH windows (FDAX `xetr_regular` 09:00-17:30 CET); the preset is US-only, and "Other futures" defaults to Chart.

**Effort:** M.

### ASSET-7 (P3, S) · Data and chart-timeframe guards [A's ASSET-9, corrected by B]

1. **D/W gating** (X17).
   - `useKeyD` is effective only when `timeframe.in_seconds() < 86400`; `useKeyW` only when `< 604800` (gate at 1790/1795).
   - It overlaps the overhaul's P1 fix; keep whichever lands first.
2. **Volume** [B-corrected].
   - Not `syminfo.volumetype`. Use `bool vpDead = needVP and lvV.size() >= 24 and lvV.sum() == 0.0`.
   - When true: skip the VP build (1384-1414); the panel shows `VOL n/a`; the LVN tooltip says "No volume on this symbol (cash index?): use the futures contract".
   - When `syminfo.volumetype == "tick"`: show `VOL tick` (FX).
3. **Cash index** (`mkt == 5`): HUD note "cash index: open print stale; gaps unreliable".
4. **24h stock session.** When `mkt == 4` and bars exist in 20:00-04:00 NY: the panel shows `SESSION 24h`. Asia/MO stay off by the ASSET-1 preset.
5. **Stock 4H STF** (X22). When `mkt == 4` and `tfS == "240"`: a tooltip note "4H bars on RTH stocks are uneven (4h + 2.5h)". Suggest Custom mode with 2H.
6. **Settlement** (X18). A tooltip note on futures D structure: "Daily closes are settlement prices". No code.

**Evidence:** strong (definitional; doc remarks). **Effort:** S.

### ASSET-8 (P3, S) · Crypto weekend handling: weekday gating, optional weekend range pools [A's ASSET-6, downgraded by B]

**Why.**
- F1/F3: weekends are compressed and thin.
- The engine runs killzones and sessions on them, and uses Sunday's range as Monday's PDH/PDL.
- **[B-corrected]** The weekend range is **not** a stronger target than a weekday range at equal distance (B3). Its value is a close, natural Monday candidate, not a bonus.

**Spec** (`mkt == 3`).
- **Gating.** Weekday gating of killzones and sessions is part of ASSET-1.
- **Weekend pools.** Input `wkPools = input.bool(false, "Crypto: Weekend High/Low Pools")`.
  - Track `wkH/wkL` and their bars over `wkend` (UTC Saturday-Sunday).
  - On the first non-weekend bar, push `SRC_WKND = 21` (tier 0.65, "WKND H/L") with `hlm = √f_tfBars("D")`.
- **Weekend PD levels.** Input `wkPD = input.string("Include", "Crypto: Weekend Days in PDH/PDL", options = ["Include", "Skip"])`.
  - "Skip" suppresses `pdEmit` for Saturday/Sunday UTC trading days (use `dayofweek(time_tradingday, "UTC")`), so Friday's levels remain Monday's PD.
  - Default "Include" = today's behaviour; under the null neither is better.
- **TIME-3 note.** Its weekly clock must use 7 day-buckets on 24/7 symbols. That is where the weekend compression is priced into PoT.

**Evidence:**
- strong for compression and activity (F1, F3, F4, Baur et al. 2019);
- none for any target excess (B3).

**Risk:** NY-anchored users may prefer the weekend as Friday 17:00 to Sunday 17:00 NY; that is SESS-6's day anchor. **Effort:** S.

### ASSET-9 (P3, S) · Gap-aware ATR and σ on session-limited charts [B-new]

**Why.**
- X21/B5: on RTH stock charts the overnight return is about 38% of daily variance, and it lands in one bar per day.
- `ta.atr` and `potSig` absorb it:
  - ATR jumps after every open;
  - the bar σ that PoT scales by √H is inflated all day, then spent in one bar.
- On futures 1H the effect is small (ATR p90 +16% on Sunday bars).

**Spec** (when `mkt == 4 or mkt == 5`, or input `gapATR = "Auto" | "On" | "Off"`):
```pine
float trX  = gapBar ? high - low : ta.tr(true)
float atrG = ta.rma(trX, atrLen)                 // every ta.* call at global scope, every bar
float atrS = ta.atr(atrLen)
float atr  = useGapATR ? atrG : atrS              // replaces 874
float chg0 = ta.change(close)
float chg  = useGapATR and gapBar ? close - open : chg0   // replaces 915
```
- Hand the overnight variance to TIME-3 as an explicit "session open" bucket, so a horizon that crosses the close gets it once.
- Doc basis: `ta.tr(handle_na)` and `ta.rma` (reference/ta.md).

**Evidence:** moderate (B5). **Risk:** a different ATR than the user's built-in ATR; the tooltip says so. **Effort:** S.

### ASSET-10 (P3, S) · Rollover and reopen close-confirm on spot FX/metals, ≤15m only [A's ASSET-4 rollover half, demoted by B]

**Why.**
- C3/C4: at the 17:00 NY rollover (and the 18:00 metals reopen), bid-plotted spreads widen from a fraction of a pip to several pips, on under 0.6% of daily volume.
- At 1H this does not turn into excess fake sweeps (B2). On 1-15m bars, though, a spread wick can be several bar ranges.

**Spec.** When `mkt == 2`, `chartS <= 900`, and the bar overlaps 16:55-17:15 NY (metals: also 18:00-18:10) via the TIME-1 (a) overlap test:
- a liquidity level needs a **close** beyond `nearEdge()` to count as swept;
- a wick-only touch increments `lv.tests` and the level stays.
- `f_step`: on those bars, liquidity hits need a close too.
- Input `rollGuard` (default on in that context).

**Evidence:**
- moderate for the mechanism;
- weak for the effect at ≥1H (B2);
- untested at ≤15m.

**Risk:** a real rollover-minute run that closes back inside is ignored as a sweep (still recorded as a test). **Effort:** S.

### Not recommended [A + B]

| Idea | Why not |
|---|---|
| **A's ASSET-2: Tokyo-local Asia clock as the default** [B] | No forecasting difference at equal distance (B1: +0.03 logit, CI spans 0, n=590 day-symbols). London DST is already in TIME-1 (e). At most an optional "Asia clock" setting in ASSET-1, default ICT NY-fixed |
| Holiday tier demotion (A's ASSET-7 part) [B] | Short-day extremes are taken next day as often as normal ones (D1). Only stub days are wrong (ASSET-3) |
| Weekend-range or holiday-range probability bonus [B] | B3: geometry only; PoT and the ledger baseline already price distance |
| Fixed session-directional priors in D (overnight drift, pre-FOMC, fix cycle, intraday momentum, gold night) | G1/E7 decay. The fix cycle (Krohn et al. 2024) and intraday momentum (Gao et al. 2018) are real but are return drifts of a few bp, not liquidity targets. At most a learned, ledger-gated term |
| Funding-time anchors (crypto) | F5: weak, confounded, and intervals vary |
| "CME gap must fill" | Fill = mirror (session_stats); no new gaps since 2026-05-29 |
| News whipsaw rule ("both sides get taken") | E4: noise |
| Option-expiry pinning to strikes | No open-interest data in Pine; pinning faded in 2016-25 (H3) |
| `syminfo.volumetype == "n/a"` as a no-volume test [B] | The docs say it is unspecified on most feeds (§1.1) |
| Cross-venue confirm feed for crypto sweeps | Venue-specific wicks are real (§1.12), but a reference feed adds a request, carries a basis, and needs a per-symbol mapping. Leave it to the user (documentation) |
| Hard-coded per-asset killzone multipliers | TIME-5 / SESS-3: neutral by default |

---

## 5. Sources

**B's tests** (`study/asset_b_tools/`): `asia_clock.py` → `out_asia_clock.txt`; `fx_roll.py` → `out_fx_roll.txt`; `crypto_wkend.py` → `out_crypto_wkend.txt`; `gap_share.py` → `out_gap_share.txt`; `gap_atr.py` → `out_gap_atr.txt`.

**A's tests** (`study/asset_tools/`): `sanity.py`, `dst.py`, `dst2.py`, `asia_hol.py`, `rth_eth.py`, `news.py`, `crypto.py`, `fx.py` with `out_*.txt`.

**Data:**
- public CME continuous OHLCV (github.com/axb0306/cme-futures-ohlc) in `study/amt_data/cme/` and `study/smt_data/cme/`;
- BTC 1-h 2017-2025 `study/session_data/btc_1h.pkl`;
- EURUSD 1-h 2017-18 and GOOG daily 2004-13 in `study/bias_data/`.

**Pine v6 docs** (local mirror `docsrc/jabez4jc_pinescriptv6/`):
- `reference/syminfo.md`: type, root, basecurrency, current_contract, session, volumetype (with its "some symbols only" remark), timezone, expiration_date;
- `reference/ticker.md`: `ticker.modify(tickerid, session, adjustment, backadjustment, settlement_as_close)`, `ticker.new`;
- `reference/time.md`: `time()` with series `session`/`timezone`; `time_tradingday` with the FXCM:EURUSD Sunday-17:00 example; `dayofweek` remarks; `timestamp(timezone, …)` with optional h/m/s; `hour(time, timezone)`;
- `reference/str.md`: contains, split, trim, substring;
- `reference/ta.md`: tr, rma;
- `reference/earnings.md`: `earnings.future_time`;
- `concepts/sessions.md`:
  - session strings and the overnight-day rule ("1700-1700:23456");
  - named sessions: ES1! "regular" = ETH, RTH = "us_regular"; FDAX `xetr_regular` / `fwb_regular`;
  - fallback to the default session for missing names;
  - `session.isfirstbar_regular` on futures;
  - hourly RTH bars start at 09:30;
- `concepts/other_timeframes_and_data.md`: dynamic requests in v6;
- `writing_scripts/limitations.md`: 40/64 unique requests; tuple element limit.

**Exchanges, vendors, official:**
- CME 24/7 crypto: https://cmegroup.com/markets/cryptocurrencies/24-7-crypto-trading.html ; https://www.theblock.co/news/markets/2026-02-19-cme-group-launch-24-7-crypto-futures-options-trading-may-29-390491 ; https://fxnewsgroup.com/forex-news/exchanges/cme-group-launches-24-7-trading-for-cryptocurrency-futures-and-options/ ; CME press release 2026-06-01: https://www.cmegroup.com/media-room/press-releases/2026/6/01/cme_group_announceslaunchof247cryptocurrencyfuturesandoptionstra.html
- CME, "When FX futures pause" (2026): https://www.cmegroup.com/articles/2026/when-fx-futures-pause.html (search summary; the page was unreachable from this session)
- BidFX research on the 16:00-18:00 ET liquidity gap: https://www.globaltrading.net/?p=27059
- E-mini S&P 500 hours: https://www.cmegroup.com/education/lessons/product-e-mini-s-and-p.html ; https://www.marketswiki.com/wiki/CME_Group_E-mini_S%26P_500
- CME Globex outage 2025-11-27/28: https://fortune.com/2025/11/30/cme-outage-financial-markets-data-center-cyrusone-aurora-illinois/ ; https://www.morningstar.com/news/marketwatch/20251128179/us-equity-futures-trading-resumes-after-cme-glitch-causes-lengthy-outage
- NYSE 2026 holidays and early closes: https://www.nyse.com/trade/hours-calendars ; https://www.businesswire.com/news/home/20251223981478/en/NYSE-Group-Announces-2026-2027-and-2028-Holiday-and-Early-Closings-Calendar
- Fed 2027 FOMC calendar (revised 2026-11-12): https://www.federalreserve.gov/newsevents/pressreleases/monetary20261112a.htm ; https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm
- BLS shutdown schedule changes: https://www.bloomberg.com/news/articles/2025-11-14/bls-says-september-jobs-report-will-be-released-nov-20 ; https://www.npr.org/2025/11/14/nx-s1-5609321/jobs-report-government-shutdown-economic-data ; https://news.bgov.com/daily-labor-report/january-us-jobs-report-rescheduled-for-feb-11-bls-says
- Nasdaq extended hours: https://clsbluesky.law.columbia.edu/2026/04/29/arnold-porter-discusses-sec-approval-of-nasdaq-proposal-to-expand-trading-hours/ ; https://governancebeat.cooley.com/24-hour-trading-nasdaqs-faqs-and-secs-roundtable/ ; https://www.bloomberg.com/news/articles/2025-03-07/nasdaq-joins-exchanges-seeking-to-offer-round-the-clock-trading
- TradingView:
  - 24h (overnight) session: https://in.tradingview.com/support/solutions/43000790593-how-to-view-the-overnight-session-24h-on-your-chart/
  - continuous-futures switching date: https://www.tradingview.com/support/solutions/43000691027-how-is-the-switching-date-of-contracts-determined-in-continuous-futures/
  - back-adjustment: https://www.tradingview.com/support/solutions/43000685266
  - settlement as close: https://in.tradingview.com/support/solutions/43000685268
  - RTH for CME futures: https://www.tradingview.com/blog/en/regular-trading-hours-for-cme-futures-28648
- WM/R fix window (5 min since 2015-02-15): https://ECB.eu/paym/groups/pdf/fxcg/2015/1211/2015-11-12_WM_presentation.pdf ; https://www.lseg.com/content/dam/ftse-russell/en_us/documents/other/wmr-fx-benchmarks-october-2024.pdf
- LBMA Gold Price: https://www.ice.com/iba/lbma-gold-price
- Spot gold hours (broker guides): https://www.cmcmarkets.com/en-gb/commodities/gold-trading-hours ; https://www.tmgm.com/en/academy/trading-academy/gold-trading-hours
- FX day-boundary conventions (forums, weak): https://www.quantconnect.com/forum/discussion/18398/daily-bar-data-in-forex-do-not-match/ ; https://fxstreet.com/education/why-any-serious-trader-should-use-the-new-york-close-chart-201705240853
- Kaiko weekend share: https://www.theblock.co/news/markets/2024-02-27-bitcoin-weekend-trading-279353 ; https://www.bloomberg.com/news/articles/2024-06-29/-boring-bitcoin-sends-weekend-trading-volume-to-all-time-lows ; US-hours share: https://www.bloomberg.com/news/articles/2024-05-21/share-of-bitcoin-volume-during-us-market-hours-surges-to-record
- 2025-10-10 crypto crash, venue-specific wicks: https://www.coingecko.com/learn/october-10-crypto-crash-explained ; https://insights4vc.substack.com/p/inside-the-19b-flash-crash ; https://www.fticonsulting.com/uk/insights/articles/crypto-crash-october-2025-leverage-met-liquidity
- Binance funding: https://www.binance.com/en/support/faq/introduction-to-binance-futures-funding-rates-360033525031
- Russell holiday volumes: https://russellinvestments.com/content/ri/us/en/insights/russell-research/2025/11/holiday-trading-effect.html
- DST 2026: https://admiralmarkets.com/about-us/news/us-daylight-saving-time-march-2026

**Academic** (abstracts or working-paper summaries unless stated):
- Andersen, T. & Bollerslev, T. (1998). Deutsche mark-dollar volatility: intraday activity patterns, macroeconomic announcements, and longer run dependencies. *JF* 53(1), 219-265. https://www.nber.org/papers/w5783
- Andersen, Bollerslev, Diebold & Vega (2003). Micro effects of macro announcements. *AER* 93(1). https://www.nber.org/papers/w8959
- Baur, D., Cahill, D., Godfrey, K. & Liu, Z. (2019). Bitcoin time-of-day, day-of-week and month-of-year effects in returns and trading volume. *FRL* 31, 78-92. https://ideas.repec.org/a/eee/finlet/v31y2019icp78-92.html
- Boguth, O., Grégoire, V. & Martineau, C. (2019). Shaping expectations and coordinating attention: the unintended consequences of FOMC press conferences. *JFQA* 54(6), 2327-2353. https://ideas.repec.org/a/cup/jfinqa/v54y2019i6p2327-2353_2.html
- Boyarchenko, N., Larsen, L. & Whelan, P. (2023). The overnight drift. *RFS*. https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr917.pdf ; "The Disappearing Overnight Drift" (2026-07-01): https://libertystreeteconomics.newyorkfed.org/2026/07/the-disappearing-overnight-drift/
- Breedon, F. & Ranaldo, A. (2013). Intraday patterns in FX returns and order flow. *JMCB* 45(5). https://www.snb.ch/en/publications/research/working-papers/2011/working_paper_2011_04
- Caminschi, A. & Heaney, R. (2014). Fixing a leaky fixing. *J. Futures Markets* 34(11). https://ideas.repec.org/a/wly/jfutmk/v34y2014i11p1003-1039.html
- Caporale, G.M. & Plastun, A. The day of the week effect in the cryptocurrency market. *FRL*. https://bura.brunel.ac.uk/handle/2438/17208
- Ederington, L. & Lee, J.H. (1993). How markets process information: news releases and volatility. *JF* 48(4). https://ideas.repec.org/a/bla/jfinan/v48y1993i4p1161-91.html
- Ederington, L. & Lee, J.H. (1995). The short-run dynamics of the price adjustment to new information. *JFQA* 30(1), 117-134. https://ideas.repec.org/a/cup/jfinqa/v30y1995i01p117-134_00.html
- Eross, McGroarty, Urquhart & Wolfe (2019). The intraday dynamics of bitcoin. *RIBAF* 49. https://centaur.reading.ac.uk/81745
- Evans, M.D.D. (2018). Forex trading and the WMR Fix. *JBF* 87. https://econpapers.repec.org/RePEc:eee:jbfina:v:87:y:2018:i:c:p:233-247
- Fleming, M. & Remolona, E. (1999). Price formation and liquidity in the U.S. Treasury market. *JF* 54(5). https://econpapers.repec.org/RePEc:bla:jfinan:v:54:y:1999:i:5:p:1901-1915
- Gao, L., Han, Y., Li, S.Z. & Zhou, G. (2018). Market intraday momentum. *JFE* 129(2), 394-414. https://econpapers.repec.org/RePEc:eee:jfinec:v:129:y:2018:i:2:p:394-414
- Golez, B. & Jackwerth, J. (2012). Pinning in the S&P 500 futures. *JFE* 106(3), 566-585. https://ideas.repec.org/a/eee/jfinec/v106y2012i3p566-585.html
- Ito, T. & Hashimoto, Y. (2006). Intraday seasonality in activities of the foreign exchange markets: evidence from the electronic broking system. *JJIE* 20(4), 637-664. https://www.nber.org/papers/w12413
- Krohn, I., Mueller, P. & Whelan, P. (2024). Foreign exchange fixings and returns around the clock. *JF* 79(1), 541-578. https://econpapers.repec.org/RePEc:bla:jfinan:v:79:y:2024:i:1:p:541-578 ; AEA 2020 draft: https://benny.aeaweb.org/conference/2020/preliminary/paper/2dedYfDH
- Kurov, A., Sancetta, A., Strasser, G. & Wolfe, M.H. (2019). Price drift before U.S. macroeconomic news. *JFQA* 54(1), 449-479. https://www.skidmore.edu/economics/documents/KSSW2017-PriceDriftBeforeUSMacroeconomicNews.pdf ; https://ecb.europa.eu/pub/pdf/scpwps/ecbwp1901.lv.pdf
- Lee, S.S. (2012). Jumps and information flow in financial markets. *RFS* 25(2), 439-479. https://ideas.repec.org/a/oup/rfinst/v25y2012i2p439-479.html
- Lucca, D. & Moench, E. (2015). The pre-FOMC announcement drift. *JF*. https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr512.pdf
- Scholtus, M., van Dijk, D. & Frijns, B. (2014). Speed, algorithmic trading, and market quality around macroeconomic news announcements. *JBF* 38, 89-105. https://repub.eur.nl/pub/50214
- EIA and crude intraday response: https://www.risk.net/journal-of-energy-markets/5728636/an-analysis-of-intraday-market-response-to-crude-oil-inventory-shocks ; https://www.iaee.org/ej/ejexec/ej44-5-Xu-exsum.pdf
- Gold day/night returns: https://link.springer.com/10.1007/s12197-017-9403-0 ; https://ideas.repec.org/a/eee/glofin/v64y2025ics1044028325000110.html

**Tooling notes.**
- Firecrawl had no credits during B's pass.
- `www.cmegroup.com` is outside the session's allowed network domains, so WebFetch of CME pages failed. CME facts come from search summaries and secondary coverage, and are marked as such where it matters.
