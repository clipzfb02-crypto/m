# Asset-class specifics: study for DOL Engine v2

Scope: how sessions, day boundaries, key levels, killzones, opens, news times, holidays, weekends and data artefacts differ across **index futures, other CME futures (energy, metals, FX futures), spot FX / spot metals, crypto and US equities**, and what the engine must do differently on each so that its targets, PoT and ledger stay correct.

This report complements, and does not repeat, the sibling studies:
- `ict_time.md`: TIME-1 (volatility clock), TIME-3 (overlap membership on coarse bars, London-close killzone, ONH/ONL, NY PM range), TIME-4 (PoT by session end), TIME-7 (one manual event that scales the clock).
- `session_stats.md`: SESS-1 (day-state variance), SESS-2 (day-end hazard), SESS-3 (learned killzone affinity, per-family ledger), SESS-6 (day-boundary input), and gap statistics (BTC CME gap, EURUSD weekend gap, index RTH gap).

Where one of those already covers an idea, this report cites it and adds only the asset-specific part.

All "[this study]" numbers come from scripts in `study/asset_tools/` (outputs `out_*.txt`), run on the public CME continuous OHLCV CSVs already in `study/amt_data/cme/` and `study/smt_data/cme/` (ES, NQ, YM, RTY, GC, CL, 6E, 6B, MBT; 1-min 2026-01-20 → 2026-04-15, 1-h 2025-03-21 → 2026-04-15), BTC/USD 1-h 2017-01 → 2025-01 (`session_data/btc_1h.pkl`) and EURUSD 1-h 2017-04 → 2018-02 (`bias_data/EURUSD.csv`). Timestamps were verified as UTC: no bars at 17:00 ET (the CME daily halt), the FX weekly gap runs Friday 21:00 → Sunday 21:00/22:00 UTC.

Note on tooling: the Firecrawl account ran out of credits and WebFetch could not reach external hosts (nber.org and mpra.ub.uni-muenchen.de are not in the session's allowed network domains). External evidence therefore comes from WebSearch summaries of abstracts and articles. Where a number could not be checked in the full text, it says so.

---

## 0. Executive summary

1. **Session activity follows local exchange clocks, not New York time.** The engine defines every session in New York time (lines 107-109, 219-226). For about four weeks a year the US and Europe are on different DST schedules, and for about four months a year Japan and China are an hour "earlier" in New York time. [this study, `dst.py`, `dst2.py`]
   - **European open spike.**
     - Index futures, 15-min activity normalised per day:
       - Winter: the spike is at 03:00 ET.
       - US/UK mismatch weeks (2026-03-08 → 03-28): it moves to 04:00 ET.
       - Summer: back at 03:00 ET.
     - The 04:00-04:15 bucket beats the 03:00-03:15 bucket on 21% of winter days, **93% of mismatch days** (mean log-ratio +0.35, 95% CI 0.24-0.46) and 46% of summer days.
   - **Gold Shanghai open (09:00 Beijing).** The 21:00 ET bucket over 20:45 ET is +0.11 in winter (SGE opens at 20:00 EST) and +0.55 in the mismatch weeks (21:00 EDT), with 100% of days positive.
   - **Control.** The US 08:30 and 09:30 spikes do not move.
   - **Consequence for the Asia range.** In US-winter months, "Asia = 20:00-00:00 New York" (the engine) and "Asia = 09:00-13:00 Tokyo" give a different Asia high or low on 68-87% of days:
     - index futures 85-87%;
     - GC 76%;
     - CL 68%;
     - n = 81-87 days each.
     They are identical in US-summer months.
2. **ETH vs RTH changes the key levels most of the time** on index futures. [this study, `rth_eth.py`, n = 216 day-symbols]
   - The full-session (18:00-17:00) high is printed outside RTH on 45.8% of days and the low on 50.0%.
   - At least one extreme differs on 70-85% of days.
   - The median gap is 0.19-0.28 ADR.
   - The engine uses whatever the chart session is (`timeframe.change("D")`, line 945), so the same symbol gives different PDH/PDL on an ETH and an RTH chart, and no "RTH PDH" is available on an ETH chart.
3. **Data artefacts create fake liquidity events.**
   - **Continuous-futures roll jumps.** ES Dec-14-2025 Sunday open: +56.5 points, 6.2× the median hourly range [this study, `sanity.py`]. TradingView back-adjustment is off by default.
   - **FX rollover wicks.** The 17:00 New York hour has a median wick fraction of 0.70, against 0.51-0.61 for every other hour, at low range [this study, `fx.py`]. CME describes spreads widening from 0.5 to 18 pips at the rollover.
   - **Session-open gaps.** Gaps trade "through" levels without a stop run.
   - The engine treats all three as sweeps (lines 1556-1585): it deletes the pool and feeds a raid event into the draw vector D.
4. **Calendar compression is not regime compression.** BTC weekend ranges are compressed by the calendar:
   - Saturday 0.46 ADR and Sunday 0.72 ADR in 2023-25 (0.83 and 0.86 in 2017-19).
   - That compression does not persist. Monday takes the Sat+Sun range high or low on **81.7%** of weeks (n = 416), against 66.3% for weekday two-day ranges taken the next day.
   - At the same near-side distance, the weekend range is taken **+9 to +12 pp** more often:
     - 0.10-0.25 ADR: 91.2% vs 83.4%;
     - 0.25-0.5 ADR: 78.5% vs 69.3%;
     - 0.5-1 ADR: 59.2% vs 47.3%.
   - [this study, `crypto.py`]
   - Kaiko: the weekend share of BTC volume fell from 28% (2019) to 13-16% (2024).
   - Holiday-shortened CME sessions have a median range of 0.58-0.76 ADR (ES/NQ/GC), against about 1.0 [this study].
5. **Crypto is now a US-hours market on weekdays.** The share of weekday BTC activity in 13-20 UTC rose from 35.3% (2017-19) to 43.7% (2023-25); a uniform spread would put 33.3% there [this study]. Kaiko/Bloomberg put US hours at 46% of 2024 volume through April.
   - The engine's NY killzones therefore apply to crypto on weekdays. On weekends they are noise, and the engine applies them anyway (line 975).
6. **Scheduled releases are asset-specific and partly deterministic by weekday.**
   - **Thursday 08:30 jobless claims.** The 08:00-09:00 ET bar, relative to the 07:00 bar, has median ratio:
     - ES 1.33 vs Monday 1.02;
     - NQ 1.36 vs 1.07;
     - GC 1.75 vs 1.27;
     - n ≈ 50-56 each.
   - **FOMC 14:00 bar** vs its trailing 20-day median: ES 2.7×, NQ 2.3×, GC **4.9×**, CL only 1.3× (n = 8 meetings).
   - [this study, `news.py`]
   - The literature confirms the mechanism:
     - prices jump within the first minute and volatility stays elevated about 15 minutes (Ederington & Lee 1993);
     - spreads widen at the release (Fleming & Remolona 1999);
     - 9-11 of 20-21 US releases show a pre-release drift starting about 30 minutes early (Kurov et al. 2019).
   - The engine has no notion of scheduled events.
7. **Session-directional drifts are real in the literature but unstable; do not hard-code them.**
   - The "overnight drift" in S&P futures (about 3.6% annualised in 02:00-03:00 ET, 1998-2019) was **flat in 2021-25** (NY Fed, 2026).
   - The pre-FOMC drift (+49 bp in 24 h, 1994-2011) became "puzzling" after 2011.
   - FX "currencies weaken in their own hours" (Breedon & Ranaldo 2013) is published but not re-measured here.
   - Any such tilt belongs in a learned, ledger-gated term, never a fixed prior.
8. **Structural changes in 2025-26 that the engine must not assume away:**
   - CME crypto futures have traded 24/7 since **June 1, 2026**, so no new "CME gaps".
   - NYSE has SEC approval for 22-hour trading (Feb 2025); Nasdaq targets 24/5 in H2 2026.
   - TradingView offers a "24h" session for some US stocks.
   - The CME Globex outage of Nov 28, 2025 (about 10 h) is visible in the data as a 4-bar "day".
   - Day boundaries and session sets per asset are therefore inputs to detect, not constants.

**Best proposals** (§4):
1. **ASSET-1:** market-profile auto-detection with per-asset presets.
2. **ASSET-2:** DST-correct session clock.
3. **ASSET-3:** RTH/ETH key levels from named sessions.
4. **ASSET-4:** session-artefact guard for rollover wicks and open gaps.
5. **ASSET-5:** continuous-futures roll handler.
6. **ASSET-6:** crypto weekend model.
7. **ASSET-7:** session completeness and measured bars-per-day.
8. **ASSET-8:** asset-aware scheduled-event calendar.
9. **ASSET-9:** data-availability and chart-timeframe guards.

---

## 1. Concepts: definitions and parameters

### 1.1 Trading day (day boundary) per asset class

| Asset | Trading day (New York time unless noted) | TradingView default daily bar | Notes |
|---|---|---|---|
| CME index futures (ES, NQ, YM, RTY + micros) | 18:00 → 17:00 next day; daily halt 17:00-18:00; Sunday 18:00 opens **Monday's** trading day | ETH ("regular" named session) | RTH = 09:30-16:15 ET (08:30-15:15 CT), named session `"us_regular"` (TradingView blog "Regular trading hours for CME futures"; Pine sessions manual) |
| Other CME/NYMEX/COMEX futures (CL, NG, GC, SI, 6E, 6B, ZN) | Same 18:00 → 17:00 Globex day | ETH | Classic "pit/RTH" hours differ by product: CL 09:00-14:30, GC 08:20-13:30 |
| Spot FX (EURUSD etc.), spot metals (XAUUSD) | 17:00 → 17:00 ("New York close"); week Sunday 17:00 → Friday 17:00 | Feed-dependent: most use the 17:00 NY close; some feeds use 00:00 GMT and produce a sixth, Sunday candle | Rollover at 17:00 NY: spreads widen, listed FX futures are halted 17:00-18:00 |
| Crypto spot / perps | 00:00 → 24:00 **UTC** (= 19:00/20:00 NY), 7 days | UTC day | Funding (Binance) 00:00/08:00/16:00 UTC; moves to 4-hourly or hourly when the funding rate hits its cap (Binance 2025) |
| CME crypto futures (BTC, MBT, ETH) | 18:00 → 17:00 until 2026-05; **24/7 since 2026-06-01** with a weekend maintenance window | ETH | No new weekend "CME gaps" after June 2026 |
| US stocks / ETFs | RTH 09:30-16:00; pre-market 04:00-09:30; post-market 16:00-20:00; some venues offer overnight 20:00-04:00 | RTH. TradingView documents the extended-hours option as intraday-only, so daily bars are almost certainly RTH. Not confirmed by an official statement | `session.regular` / `session.extended`; `session.ispremarket`, `ispostmarket`, `ismarket` |
| Cash indices (SPX, NDX, DJI) | 09:30-16:00, **no volume** (`syminfo.volumetype` = "n/a") | RTH | The cash "open" prints before most components trade, so gap statistics on cash indices are biased (session_stats §2.9) |

**Pine primitives.**
- `syminfo.type`: "stock", "fund", "dr", "right", "bond", "warrant", "structured", "index", "forex", "futures", "spread", "economic", "fundamental", "crypto", "spot", "swap", "option", "commodity" (reference/syminfo.md).
- Also `syminfo.session`, `syminfo.timezone`, `syminfo.root` (e.g. "ES" for ES1!), `syminfo.basecurrency` ("BTC" for CME:BTC1!, "CAD" for 6C1!), `syminfo.current_contract` (non-na only on continuous futures) and `syminfo.volumetype` ("base", "quote", "tick", "n/a").
- `time_tradingday` gives 00:00 UTC of the trading day the bar belongs to. Example from the docs: FXCM:EURUSD's Monday session starts Sunday 17:00. `timeframe.change("D")` follows the exchange trading day.
- Session strings default to all seven days: "If the days aren't specified, the session is considered to have been set from Sunday (1) to Saturday (7)" (reference/time.md).

### 1.2 RTH vs ETH key levels

- **ETH PDH/PDL:** extremes of the full exchange day (futures 18:00-17:00; stocks 04:00-20:00 on an extended chart). ICT-style futures traders use these.
- **RTH PDH/PDL:** extremes of the regular session (09:30-16:15 index futures, 09:30-16:00 stocks). AMT/Market-Profile and stock traders use these.
- **Prior RTH close** (gap reference) and **RTH open** (09:30) are anchors.
- **ONH/ONL** = ETH-only range 18:00-09:30 (TIME-3 adds it as a source).
- **Edge cases:**
  - On an RTH-only chart there are no overnight bars. Midnight open, Asia and London sessions are all na, and the engine silently drops them from confluence.
  - On stock charts with extended hours, `timeframe.change("D")` fires at 04:00. "PDH" then includes the prior day's post-market and pre-market, not what most stock traders call PDH.
- **Pine:**
  - Futures RTH: `ticker.new(syminfo.prefix, syminfo.ticker, "us_regular")`. Requesting a named session that does not exist falls back to the default: "If a script attempts to retrieve data using a named session that does not exist for that symbol, the default session is used instead" (concepts/sessions.md).
  - Stocks: `ticker.modify(syminfo.tickerid, session.regular)`.
  - For futures, `session.extended` equals `session.regular` (ETH), and the RTH name is `"us_regular"` (concepts/sessions.md, ES1! example).

### 1.3 Session clock and daylight-saving time

| Window | ICT / engine (New York time) | Local-clock meaning |
|---|---|---|
| Asia | 20:00-00:00 | Tokyo 09:00-13:00 JST: = 20:00-00:00 **EDT**, but **19:00-23:00 EST** |
| Gold Asia (SGE) | — | 09:00 Beijing: 20:00 EST / 21:00 EDT |
| Frankfurt open | 02:00 (engine's "London Open" anchor 0200-0300) | 08:00 CET: = 02:00 ET except **03:00 ET** in the US/EU mismatch weeks |
| London cash open | inside 02:00-05:00 | 08:00 London: = 03:00 ET except **04:00 ET** in the mismatch weeks |
| NY | 08:30, 09:30 | Local; never shifts |

- **Mismatch periods.** US DST starts on the second Sunday of March and ends on the first Sunday of November. EU/UK DST runs from the last Sunday of March to the last Sunday of October. That leaves 3 weeks in spring (2026: Mar 8 → Mar 29) and 1 week in autumn (2026: Oct 25 → Nov 1).
- **No DST in Asia.** Japan and China do not observe DST, so their opens are one hour earlier in New York time during US standard time (about November → mid-March).
- **Pine.** `time(tf, sess, tz)` takes a per-call IANA time zone and adjusts for DST automatically (concepts/time.md: "Using an IANA identifier allows the `time()` call to automatically adjust the session's UTC offset"). `hour(time, tz)` and `minute(time, tz)` return the local time.

### 1.4 Weekends, gaps, halts and rollovers

| Asset | Weekend / halt | What happens to levels |
|---|---|---|
| Index and other CME futures | Friday 17:00 → Sunday 18:00 closed; daily 17:00-18:00 halt | The first bar after a gap can open beyond a level (NWOG/NDOG in ICT terms; ict_pd covers the PD-array view) |
| Spot FX / metals | Friday 17:00 → Sunday 17:00 | Sunday open bars are thin; the 17:00 rollover hour has wide spreads, so bid-based charts print wicks that never traded at mid |
| Crypto | Trades 7 days | No gap, but Saturday and Sunday are compressed (0.46 / 0.72 ADR in 2023-25); weekend volume share is 13-16% (Kaiko 2024) |
| US stocks | Overnight 16:00/20:00 → 04:00/09:30 | Every RTH open can gap; earnings gaps |
| Continuous futures (ES1!, CL1!, GC1!) | Contract roll every quarter (index) or month (CL, often GC/SI) | Unadjusted chart: a price jump at the switch bar (ES quarterly about +40-60 pts of basis; ES Dec-2025 roll +56.5 [this study]). TradingView back-adjustment is **off by default** (support article 43000685266) |

**Definitions for the engine:**
- **Session-open gap bar:** `time - time[1] > 2 × chartS × 1000`. This catches weekends, daily halts, overnight gaps on RTH charts and holidays.
- **Gap-through:** on that bar, `open` is already beyond a level, e.g. `open > level` for buy-side liquidity.
- **Rollover window** (spot FX/metals/CFD): 16:55-17:15 New York.

### 1.5 Holidays and half days

**CME equity index.**
- Holiday sessions halt at 12:00 CT (13:00 ET) on Thanksgiving and resume at 17:00 CT for the Friday trade date.
- Black Friday closes early: 12:15 CT in 2022, 12:45 CT in 2015 (CME and DTN notices).
- Monday holidays (MLK, Presidents', Memorial, Labor) have a Globex session halting around 12:00-13:00 ET. These appear in the data as 19-bar days (1-h) [this study].
- On Good Friday 2026 (Apr 3) an abbreviated session ran to about 09:15 ET (NFP day): 16 bars in the data.

**US equities.** 13:00 ET early closes:
- July 3 (when applicable);
- the day after Thanksgiving;
- Christmas Eve.

**Volume.** Russell Investments' practitioner data:
- Thanksgiving Eve about 80% of normal;
- Black Friday about 45%;
- Christmas Eve about 20%;
- December 23 → New Year 45-70%.

**Exceptional closures.** The CME Globex outage of 2025-11-28 (data-centre cooling, about 10 h) shows as a 4-bar day in the 1-h data.

**Engine relevance.**
- A short session's high and low are weak "previous day" liquidity.
- A short session also has fewer chart bars than a normal day. Any wall-clock "bars per day" conversion is wrong on those days, and always wrong on session-limited assets (§1.8).

### 1.6 Scheduled macro and market events (where and when liquidity is run)

| Event | Time | Assets most affected | Recurrence |
|---|---|---|---|
| US data (CPI, PPI, retail sales, GDP, NFP) | 08:30 ET | Index futures, UST, gold, USD FX, crypto (weekdays) | NFP: usually the first Friday; claims: **every Thursday** |
| US 10:00 data (ISM, JOLTS, consumer confidence) | 10:00 ET | Same | Monthly |
| EIA Weekly Petroleum Status | **Wed 10:30 ET** | CL, RB, HO | Weekly |
| EIA natural gas storage | Thu 10:30 ET | NG | Weekly |
| FOMC statement / press conference | 14:00 / 14:30 ET | All USD assets; gold most in this sample | 8 per year (2026: Jan 28, Mar 18, Apr 29, Jun 17, Jul 29, Sep 16, Oct 28, Dec 9) |
| ECB decision / press conference | 14:15 / 14:45 CET | EUR FX, DAX, Euro Stoxx | 8 per year |
| WM/R 4 pm London FX fix | 16:00 London (11:00 ET; 10:00 ET during the mismatch weeks) | FX; month-end strongest | Daily |
| LBMA Gold Price auctions | 10:30 and 15:00 London | XAU, GC | Daily |
| Tokyo FX fix | 09:55 JST (19:55 EST / 20:55 EDT) | JPY pairs | Daily |
| Crypto funding | 00:00/08:00/16:00 UTC (Binance; can become hourly) | Perps | Daily |
| ETF NAV / US close | 16:00 ET | BTC (ETF era) | Weekdays |

**Mechanics** (literature):
1. **Before the release.**
   - Quotes thin and spreads widen exactly at the release (Fleming & Remolona 1999).
   - Some releases drift in the "correct" direction from about 30 minutes before. That drift is about 40-50% of the total adjustment, for 9-11 of 20-21 releases, in E-mini and T-note futures 2008-14 (Kurov, Sancetta, Strasser & Wolfe 2019).
2. **At the release.**
   - A near-instantaneous jump (Andersen, Bollerslev, Diebold & Vega 2003: conditional-mean jumps tied to surprises).
   - The adjustment is essentially complete within the first minute (40 seconds at 10-second resolution, Ederington 1995).
3. **After the release.** Volatility stays well above normal for about 15 minutes, then slightly elevated for hours, and later price moves are essentially unrelated to the first-minute return (Ederington & Lee 1993).
4. **Crude after EIA.** Return, volatility and volume respond within minutes and the effect lasts about 25 minutes (Journal of Energy Markets). Intraday momentum on EIA days runs from the release half-hour to the last half-hour (Energy Journal, Wen et al.).

**DOL relevance.**
- A release bar "runs" whichever pools are near. The direction of the first minute carries little information about the rest of the session.
- Raids inside the release window are therefore weaker evidence for continuation or reversal than ordinary raids.
- The *timing* of liquidity runs is predictable from the calendar.

### 1.7 Session-directional drifts (historical, unstable)

These effects are documented but should not be hard-coded:
- **US equity "overnight drift"** concentrated at the European open, 02:00-03:00 ET: about 3.6% annualised in S&P futures, 1998-2019. Boyarchenko, Larsen & Whelan (RFS 2023) link it to dealer inventory. It was **flat in 2021-25** ("The Disappearing Overnight Drift", NY Fed Liberty Street, 2026).
- **Pre-FOMC drift:** S&P +49 bp in the 24 h before FOMC, 1994-2011 (Lucca & Moench 2015), with no pre-announcement effect for other macro releases. Post-2011 it is "puzzling" (the authors' own blog).
- **FX:** currencies tend to depreciate during their own local trading hours, and order flow shows the same timing (Breedon & Ranaldo, JMCB 2013).
- **Gold:** COMEX gold overnight returns are significantly positive and day returns negative (Springer study). A "night effect" also appears in Chinese gold futures (Global Finance Journal 2025).
- **Crypto:** the Monday-return anomaly appears in Bitcoin only, and the simulated strategy was not significantly better than random (Caporale & Plastun, FRL).

Use: at most a learned, bounded term in D, graded by the ledger (§4 "not recommended" explains why it is not proposed).

### 1.8 Bars per period on session-limited assets

The engine converts timeframes to chart bars with wall-clock seconds: `f_tfRatio(tf) = in_seconds(tf) / chartS` (567-568), `hmD = √(86400/chartS)` (1792) and `hmW = √(604800/chartS)` (1797). On a 5-min chart that gives 288 bars/day and 2016 bars/week.

Real values on a 5-min chart:

| Asset | Bars/day | Bars/week | Ratio |
|---|---|---|---|
| US stock (RTH) | 78 | 390 | 0.27 / 0.19 of the assumed value |
| CME futures | 276 | 1380 | about 0.96 / 0.68 |
| Spot FX | 288 | 1440 | 1.0 / 0.71 |
| Crypto | 288 | 2016 | exact |

So the freshness clocks of PD, PW and HTF levels run 1.9-2.3× too slow on stocks, and the weekly ones about 1.2× too slow on futures and FX.

### 1.9 Volume availability

- Cash indices have no volume (`syminfo.volumetype` = "n/a").
- Spot FX on TradingView usually has tick volume.
- Crypto has base or quote volume.

On a no-volume symbol the engine's 1H volume profile (978-1016, 1384-1414) is all zeros. LVN zones are not drawn (guard `peak > 0`, 2252) and the path-volume factor is neutral (`vpMean > 0` guard, 1420). There is no crash, but nothing tells the user that a feature is inert.

### 1.10 Continuous futures, settlement and roll

- **Back-adjustment** (TradingView): "when the continuous is switched to the next new contract, all previous contracts are adjusted according to the coefficient … the difference between the Close of the new and old contracts for the nearest daily bar to the switching point". It is off by default.
- **Settlement as close:** on by default for futures daily bars. On "1D" and higher, `close` is the exchange settlement (support 43000685268), not the last trade at 17:00 that the intraday chart shows.
- **Pine:**
  - `ticker.modify(tickerid, session, adjustment, backadjustment, settlement_as_close)` with `backadjustment.on/off/inherit` and `settlement_as_close.on/off/inherit` (reference/ticker.md).
  - `syminfo.current_contract` is the underlying contract of a continuous symbol, else na.
  - `syminfo.expiration_date` works only on non-continuous contracts.

---

## 2. Evidence (numbers and sources)

### 2.1 Table

| # | Claim | Numbers | Source | Grade |
|---|---|---|---|---|
| A1 | European-open activity spike shifts with the US/UK DST mismatch | Index futures 04:00 vs 03:00 bucket: 21% of days (W), **93% (M)**, 46% (S). Mean log-ratio −0.17 / **+0.35 [0.24, 0.46]** / 0.00. 61 days, 4 index symbols averaged per day | [this study] `dst2.py`, `out_dst2.txt` | moderate (clean natural experiment, short sample) |
| A2 | Shanghai gold open shifts with US DST | GC 21:00 vs 20:45 bucket: W +0.11 (55% of days), M **+0.55** (100%). 20:00 vs 19:45: W +0.69 (100%) | [this study] `dst2.py` | moderate |
| A3 | Frankfurt 08:00 CET spike on EUR/GBP futures shifts | 03:00 vs 02:45 ET: M +0.77 (100% of days) vs S +0.22 | [this study] | moderate |
| A4 | US events do not shift | 08:30 and 09:30 spikes at the same NY minute in W/M/S (`out_dst.txt`, US morning table) | [this study] | moderate |
| A5 | Asia range depends on the clock convention in US winter | Different high or low on 85-87% of days (index futures), 76% GC, 68% CL (n = 81-87); 0% in summer | [this study] `asia_hol.py` | strong (arithmetic on real data; definitional) |
| A6 | Literature: intraday FX activity is tied to local market hours | EBS USD-JPY/EUR-USD U-shapes for Tokyo and London participants; analysis accounts for DST (Ito & Hashimoto 2006, JJIE 20(4)) | NBER w12413 (abstract) | strong (peer-reviewed; DST result not read in full) |
| B1 | ETH day extremes are often printed outside RTH | High 45.8%, low 50.0% of days; either 70-85%; median gap 0.19-0.28 ADR. ES/NQ/YM/RTY 1-min, n = 216 | [this study] `rth_eth.py` | moderate (3-month sample) |
| B2 | RTH levels are closer, so they are taken more often | ES next-day take: RTH PDH 58.5% vs ETH PDH 50.9%; RTH PDL 69.8% vs ETH PDL 60.4% (similar on NQ/YM/RTY) | [this study] | moderate (geometry, not magnetism) |
| C1 | Roll jumps on unadjusted continuous futures | ES 2025-12-14 Sunday open +56.5 pts (6.2× median 1-h range); ES 2025-09-03 contract flips ±53-56; GC Aug-2025 and CL contract flips of 40-50× the median range | [this study] `sanity.py`, `out_sanity.txt` | strong (data fact) |
| C2 | TradingView back-adjust off by default; roll gap ≈ inter-contract spread | ESZ23 → ESH24 +51 pts | TradingView support 43000685266; TradingView community idea | strong (vendor doc) |
| C3 | FX rollover wicks | 17:00 NY hour median wick fraction 0.70 vs 0.51-0.61 for all other hours; range 0.56 and tick volume 0.77 of the daily mean (EURUSD 1-h 2017-18, about 200 days) | [this study] `fx.py`, `out_fx.txt` | moderate |
| C4 | Rollover spreads widen; stops trigger on one side | Example 0.5 → 18 pips; stop triggered on the bid while mid never reached it; snaps back within minutes | CME Group article "When FX futures pause" (2026); FXCM, Forex.com FAQs | moderate (exchange/broker description) |
| D1 | Holiday/short sessions are compressed | Median range/ADR: ES 0.76, NQ 0.65, GC 0.58 vs 0.98-1.01 on normal days; Thanksgiving 2025 0.08-0.09 ADR | [this study] `asia_hol.py` (n = 11 ES/NQ, 24 GC including data-gap days) | weak-moderate (small n) |
| D2 | Holiday volume | Black Friday about 45%, Christmas Eve about 20% of normal | Russell Investments (practitioner) | weak |
| E1 | Weekly-scheduled 08:30 release (Thursday claims) raises the 08:00-09:00 hour | ES 1.33 vs Mon 1.02; NQ 1.36 vs 1.07; GC 1.75 vs 1.27 (median ratio to the 07:00 bar, n ≈ 50-56) | [this study] `news.py` | moderate |
| E2 | FOMC 14:00 bar | ES 2.70×, NQ 2.32×, GC **4.88×**, CL 1.34× its trailing 20-day median; 14:00/13:00 ratio 2.6-5.8 vs 0.87-0.90 on other days (n = 8) | [this study] | moderate |
| E3 | EIA Wednesday effect in CL | 1-h: Wed 10:00 bar/09:00 bar 0.92 vs 0.74-1.00 other days; 1-min first-15-min/pre-30-min 0.83 vs 0.60-1.00. **Not distinguishable** in 2025-26 (oil-shock period) | [this study] | weak (inconclusive) |
| E4 | "Both sides of the pre-release range taken within 60 min" | ES Thu 42% vs Mon 42%, Fri 9%; NQ Thu 50% vs Mon 25% (n = 11-13): noisy | [this study] | weak / none |
| E5 | Release mechanics | First-minute adjustment, about 15 min elevated volatility, later moves unrelated to the first minute (Ederington & Lee 1993, JF 48(4)); spreads widen at release (Fleming & Remolona 1999, JF 54(5)); conditional-mean jumps (ABDV 2003, AER 93(1)) | Abstracts and summaries | strong |
| E6 | Pre-release drift | Starts about 30 min before; about 40-50% of the adjustment; 9-11 of 20-21 releases; E-mini and T-note 2008-14 (Kurov et al. 2019, JFQA 54(1)) | Abstract and ECB WP 1901 | strong (peer-reviewed) |
| E7 | Pre-FOMC drift | +49 bp in 24 h, 1994-2011; none before 1980; none for other releases (Lucca & Moench 2015, JF); "puzzling post-2011" | NY Fed SR 512, Liberty Street | strong but decaying |
| E8 | Gold fixing | Elevated volume and volatility right after the PM fixing starts, before publication (Caminschi & Heaney 2014, J. Futures Markets 34(11)); disputed by LBMA commentators | Abstract and press | moderate |
| E9 | WM/R fix | "Extraordinary volatility and negative serial correlation around the Fix"; strongest at month-end; 21 currencies over a decade (Evans 2018, JBF 87) | Abstract | strong |
| E10 | EIA crude reaction | Effects last about 25 min; momentum from the release half-hour to the last half-hour | J. Energy Markets; Energy Journal (Wen, Indriawan, Lien, Xu) | moderate |
| F1 | BTC weekend compression | UTC-day range/ADR: Sat 0.83 → 0.70 → **0.46**; Sun 0.86 → 0.81 → 0.72 (2017-19 → 2020-22 → 2023-25); weekdays 0.97-1.28 | [this study] `crypto.py` | strong (8 years) |
| F2 | Weekend range taken on Monday | Either side 81.7% (n = 416) vs weekday two-day range next day 66.3% (n = 1245); within near-side bins +9 to +12 pp; both sides 9.6% vs 3.9% | [this study] | moderate (no clock-null; weekday baseline matched on distance) |
| F3 | Weekend volume share | 28% (2019) → 13% (Jan-Feb 2024) → 16% (H1 2024); US venues 11% | Kaiko via The Block, CoinDesk, Bloomberg | moderate |
| F4 | BTC US-hours concentration | 13-20 UTC share 35.3% → 37.5% → 43.7% [this study]; Kaiko: US hours 46% of 2024 volume through April; 57% of USD-pair volume | [this study], Bloomberg/Kaiko | strong |
| F5 | Funding-hour bars | 1.05-1.12 vs neighbouring hours 0.98-1.02 (confounded: 00 UTC is the day open, 08 UTC the London open) | [this study] | weak |
| F6 | Day-boundary sensitivity (BTC) | UTC-day vs NY-midnight-day: different high on 45.7%, low on 42.7% of days; NY-midnight vs NY-17:00: 58.4% / 55.3% (n ≈ 2927) | [this study] | strong (definitional) |
| F7 | CME gaps | 79 of 80 filled (CoinDesk 2025, no distance control); session_stats: 4-week fill 86.7% vs mirror 89.4%. **24/7 CME crypto from 2026-06-01** ends new gaps | CME press release 2026-06-01; session_stats §2.9 | strong (structural fact) |
| G1 | Overnight drift gone | 02:00-03:00 ET about 3.6% annualised (1998-2019) → flat 2021-25 | Boyarchenko et al. RFS 2023; Liberty Street 2026 | strong |
| G2 | FX own-hours depreciation | Published pattern; no magnitude retrieved | Breedon & Ranaldo, JMCB 45(5) | moderate (not re-measured) |
| H1 | US equities 22-24 h | NYSE 22-hour approval (Feb 2025); Nasdaq 24/5 targeted H2 2026 (proposed Dec 6, 2026); TradingView "24h" session for BOATS-supported stocks | Bloomberg, Cooley, TradingView support | strong (structural) |

### 2.2 Reading

- **Clock convention is not a forecasting edge in itself.** A1-A5 show that the "true" session boundaries move by an hour in New York time, while the engine's windows do not.
  - The size of the error is large (the Asia range differs on most winter days).
  - The forecasting value depends on whether pools defined on the true clock are better targets. That is testable only with a per-family ledger (SESS-3) running both definitions, which ASSET-2 enables.
- **ETH/RTH (B1-B2)** is a "which levels exist" question. Both sets are widely watched. The engine should show the one the user trades and optionally both, then let the ledger grade them.
- **Artefacts (C1-C4)** are correctness bugs. A wick that never traded at mid, or a roll jump, is not liquidity being taken.
- **Weekend and holiday compression (D1, F1-F2)** is the key asset-specific forecasting fact. Calendar-induced compression does not persist. The levels of a compressed calendar period sit close to price and are taken with high probability once the normal clock resumes. This is unlike regime compression (NR7, inside days), which persists (session_stats O6). PoT should know about the calendar (TIME-1's weekday factor) and the engine should expose the weekend range as a target.
- **Events (E1-E10).** The timing of liquidity runs is predictable from the calendar. The direction of the first minutes is not informative about the rest of the session. The magnitude differs by asset: gold 4.9× and crude 1.3× at FOMC in this sample.

---

## 3. Engine gap analysis (baseline_v2.pine)

| ID | Concept | Status | Lines | What the engine does / what differs |
|---|---|---|---|---|
| X1 | Asset-class detection | **missing** | none (no `syminfo.type`, `syminfo.session`, `syminfo.volumetype`, `syminfo.root`, `current_contract` anywhere) | One set of New York-time sessions, killzones and anchors for every symbol: stocks, FX, crypto, futures |
| X2 | Day boundary | **present (exchange day), no choice** | 945-946 (`f_rangeTrack(timeframe.change("D"/"W"))`) | CME 18:00 ET, FX 17:00 ET, crypto 00:00 UTC, stocks 04:00 on ETH charts. Choice of boundary is SESS-6. Day-boundary sensitivity for BTC is 43-58% of days (F6) |
| X3 | RTH vs ETH key levels | **partial** | 945, 952-961, 1790-1799 | PDH/PDL come from the chart session only. On an ETH futures chart there is no RTH PDH/PDL, prior RTH close or RTH open (except `nyOpen` 0930-1030 at 966, which is a confluence anchor and misaligned on 1H, ict_time G3). On a stock ETH chart, PDH includes pre/post-market |
| X4 | Session time zones / DST | **wrong** (for Asia in US winter and London in the mismatch weeks) | 107-109, 219-226, 799, 836, 948-950, 964-966, 971-974 | Every window uses one `tz` (default America/New_York). Asia 2000-0000 misses the Tokyo first hour Nov-Mar; London range/open/killzone are off by 1 h for about 4 weeks a year (A1-A5) |
| X5 | Sessions on 24/7 and RTH-only assets | **partial** | 106-109 (`useSess`), 947 (`intraOK`), 971-975 (`kz`) | Crypto: Asia/London/NY sessions and killzones fire on Saturday and Sunday too (session strings default to all 7 days). Stocks: Asia/London never fire; NY AM killzone 07:00-10:00 covers only 09:30-10:00 of RTH; 10:00-13:30 is OFF-KZ with hysteresis × `kzHx` (976) |
| X6 | Midnight open per asset | **partial** | 220, 964, 1931 | `f_sessOpen` returns na where no bar opens in 00:00-01:00 (stocks; charts above 1H), and the anchor silently disappears. No substitute (stock RTH open, 04:00 pre-market open) |
| X7 | Weekend / session-open gap handling | **missing** | 1556-1585 (sweeps, `liqEvt`), 1587-1592 (registry raid), 1434-1460 (`f_step`) | A gap-through on the first bar after a weekend/halt/overnight counts as a sweep and as a raid event (`evt` from that bar's close). `f_step` already settles gaps at the open correctly (bar-path rule), so the ledger is fine; D and the pool are not |
| X8 | FX rollover window | **missing** | same | Rollover wicks (C3-C4) delete pools and inject reversal events (`close < lv.price` after a wick through) into D |
| X9 | Continuous-futures roll | **missing** | same, plus FVG/OB creation 1600-1760 | On unadjusted charts a +40-60 pt (ES) roll jump sweeps every BSL in its path, creates a fake FVG, and drags every level's distance by the basis |
| X10 | Holidays / short sessions | **missing** | 952-958, 1790-1794 | A 4-bar or 13:00-close day's extremes become PDH/PDL with tier 0.80 (506-515) and full prominence |
| X11 | Bars per day/week | **wrong** on session-limited assets | 567-568 (`f_tfRatio`), 1780-1781, 1792, 1797, 1864 | Wall-clock ratios: stocks' PD/PW/HTF freshness clocks are 1.9-2.3× too slow; futures/FX weekly about 1.2× (§1.8) |
| X12 | Time → bar mapping | **present / robust** | 1191-1207 (`f_barAtTime`) | Recorded open bars plus binary search over `time[]` handle session gaps. Only the beyond-`anchorMax` fallback uses wall clock, which overshoots across gaps (minor) |
| X13 | Scheduled events | **missing** | none | No release calendar, no news flag, no event-aware variance, no tagging of ledger trials opened into a release. TIME-7 proposes one manual event; nothing is asset-aware |
| X14 | Fixes (WM/R, LBMA, Tokyo) as anchors/times | **missing** | none | Not needed as targets. Useful as time anchors and event windows for FX and gold (ASSET-8) |
| X15 | Crypto weekend range | **missing** | none | The strongest crypto-specific liquidity pool by this study (F2) is not tracked. On Monday, PDH/PDL = Sunday's compressed range |
| X16 | Volume availability | **partial** | 978-1016, 1384-1414, 1416-1424, 2250-2287 | No-volume symbols make LVN/path-VP silently inert; tick volume is not labelled |
| X17 | Daily/weekly chart gating | **partial** | 945-946, 1790-1799, 975 | On a W chart `timeframe.change("D")` is true on every bar, so "PDH" = the prior week's high (mislabelled, de-duplicated against PWH by `f_pushExt`). Killzones are correctly "HTF" above intraday |
| X18 | Settlement-as-close in HTF structure | **n/a / minor** | 923-925 (`request.security(... "D" ...)`) | Futures daily closes are settlement prices by default; body-break structure on D uses them while intraday bars show last trades. Consistent with what the user sees on a D chart; mention only |
| X19 | Session-directional drift priors | **missing (correctly)** | — | Evidence decays (G1, E7); keep out of fixed scoring |

---

## 4. Proposals (best first; maximum 10)

Ground rules for every spec:
- Structure, pool and ledger changes run only when `barstate.isconfirmed` is true.
- New `request.security` calls use `[1]` plus `lookahead_on` and `f_tfSafe`, except where noted (same-timeframe requests).
- Globals are declared before the functions that read them. Session-string defaults stay New York-time so that ICT users see what they expect.

### ASSET-1 (P1, M) · Market profile: auto-detect the asset class and apply per-asset session presets

**Why.**
- Every asset-specific behaviour below needs one switch.
- Today the engine applies futures-style New York sessions to stocks (where Asia, London and midnight never fire) and to crypto weekends (where they fire on noise) (X1, X5, X6).

**Inputs** (`G_CONF`):

```pine
string mktIn = input.string("Auto", "Market Profile", options = ["Auto", "Index Futures", "Other Futures", "FX / Spot Metals", "Crypto", "US Stocks", "Other"], group = G_CONF,
  tooltip = "Auto reads syminfo.type / root / base currency. Sets day boundary, sessions, killzone days, artefact guards and event presets.")
```

**Detection** (global scope, simple strings only):

```pine
bool eqIdx = str.contains("|ES|MES|NQ|MNQ|YM|MYM|RTY|M2K|EMD|", "|" + syminfo.root + "|")
string bc  = syminfo.basecurrency
int mkt = switch mktIn
    "Index Futures"    => 0
    "Other Futures"    => 1
    "FX / Spot Metals" => 2
    "Crypto"           => 3
    "US Stocks"        => 4
    "Other"            => 5
    => syminfo.type == "crypto" or (syminfo.type == "futures" and (bc == "BTC" or bc == "ETH")) ? 3 :
       syminfo.type == "futures" ? (eqIdx ? 0 : 1) :
       syminfo.type == "forex" or bc == "XAU" or bc == "XAG" ? 2 :
       syminfo.type == "stock" or syminfo.type == "fund" or syminfo.type == "dr" ? 4 : 5
bool is247 = mkt == 3
bool hasVol = syminfo.volumetype != "n/a"
```

- `str.contains(source, str)` is documented in `reference/str.md` ("Returns true if the `source` string contains the `str` substring").
- `str.format` documents DecimalFormat patterns such as `{0,number,#.#}` and `{0,number,integer}`. A zero-padded `{0,number,0000}` is not shown in the docs, so ASSET-2's fallback should pad by hand: `(h < 10 ? "0" : "") + str.tostring(h)`.

**Preset table** (applied where the user left the defaults):

| mkt | Day | Key-level session (ASSET-3) | Sessions | Killzone days | Guards (ASSET-4) | Event preset (ASSET-8) |
|---|---|---|---|---|---|---|
| 0 Index futures | exchange (18:00 ET) | Both: ETH PDH plus RTH H/L, RTH close | Asia, London, NY AM (+ ON range TIME-3) | Mon-Fri (by trading day) | open-gap | US 08:30 / 10:00 / FOMC 14:00 |
| 1 Other futures | exchange | ETH (+ product RTH optional) | as 0 | Mon-Fri | open-gap; roll (ASSET-5) | CL/RB/HO Wed 10:30; NG Thu 10:30; GC: US data + FOMC + LBMA 10:30/15:00 London |
| 2 FX / spot metals | 17:00 NY | ETH | Asia (Tokyo clock), London, NY | Mon-Fri | rollover 16:55-17:15 NY + open-gap | US data, FOMC, ECB/BoE (dates), WM/R 16:00 London, Tokyo fix 09:55 JST |
| 3 Crypto | exchange (UTC) or NY midnight (SESS-6) | n/a | Asia/London/NY **weekdays only** + weekend range (ASSET-6) | Mon-Fri (UTC); "WEEKEND" state | none | US data, FOMC; funding anchors optional (off) |
| 4 US stocks | RTH | RTH (request `session.regular` when the chart is ETH) + pre-market H/L | NY only; Asia/London off; MO → RTH open 09:30 | Mon-Fri | open-gap (every RTH open) | US data, FOMC; earnings flag via `request.earnings` (optional) |
| 5 Other / cash index | exchange | chart | as chart | Mon-Fri | open-gap | none; panel note "no volume" if applicable |

**Implementation notes.**
- **Killzone days.** For crypto the window test adds `dayofweek(time, "UTC")` not in {saturday, sunday}. Futures/FX need nothing: no bars on weekends, and Sunday-evening bars belong to Monday's Asia.
- **Stocks.** When `mkt == 4`:
  - `useSess` London/Asia are off;
  - `midOpen` falls back to the 09:30 open (stocks) or the 04:00 pre-market open (extended charts);
  - `kzNA` becomes "0930-1100" and `kzNP` "1500-1600" (opening drive and close); the alternative is to let TIME-5's learned affinity decide.
- **Terminal panel** (2289+): one line `MKT  IDX FUT · DAY 18:00 ET · RTH 09:30-16:15 · CLOCK LOCAL`.
- **Clean style:** unchanged; the tooltip on the target label gets one line `Market: Index futures (auto)`.

**Value.** Correct sources and states on every asset class with zero configuration. Each later proposal reads `mkt`.

**Ledger.** Store `mkt` with the ledger so per-family stats (SESS-3) are not mixed across classes when the user switches symbols. Nothing to store: the ledger is per chart load.

**Evidence:** strong (doc-verified built-ins; definitional).

**Risk.** Misclassification of exotic symbols (CFD indices, spot commodities with `syminfo.type` "commodity"/"spot"): "Other" is safe and manual override exists. Recompilation is not needed; all inputs are simple.

**Effort:** M.

### ASSET-2 (P1, S) · DST-correct session clock (local exchange time), keeping New York-time inputs

**Why.**
- A1-A5: activity follows Tokyo/Shanghai/Frankfurt/London clocks.
- With fixed New York windows:
  - the Asia range differs on 68-87% of US-winter days;
  - the London open anchor (02:00 ET) lands one hour *before* Frankfurt in the mismatch weeks, when the actual spike is at 04:00 ET on 93% of days.

**Input:**

```pine
string sessClock = input.string("Local (DST-correct)", "Session Clock", options = ["Local (DST-correct)", "New York fixed (ICT)"], group = G_CONF,
  tooltip = "Local: Asia follows Tokyo (Shanghai for metals), London follows Frankfurt/London, so windows shift by an hour when DST differs. Inputs stay in New York time as seen in US summer.")
```

**Algorithm.**
- Keep the user's New York-time strings as entered. They are interpreted as "New York time during the reference season", meaning US summer with Europe also on summer time, which is the ICT convention: Asia 20:00 = Tokyo 09:00, London 02:00 = Frankfurt 08:00.
- Each bar computes the current offset of the session's home zone from New York, in minutes, and shifts the window by the difference from the reference offset:

```pine
f_offMin(string zone) =>                      // home-zone clock minus New York clock, in minutes, wrapped to (-720, 720]
    int d = (hour(time, zone) * 60 + minute(time, zone)) - (hour(time, "America/New_York") * 60 + minute(time, "America/New_York"))
    d > 720 ? d - 1440 : d <= -720 ? d + 1440 : d
bool  locClk  = sessClock == "Local (DST-correct)"
bool  isMetal = (mkt == 1 and (syminfo.root == "GC" or syminfo.root == "MGC" or syminfo.root == "SI" or syminfo.root == "SIL")) or (mkt == 2 and (syminfo.basecurrency == "XAU" or syminfo.basecurrency == "XAG"))
string zAsia  = isMetal ? "Asia/Shanghai" : "Asia/Tokyo"      // metals: SGE/SHFE open 09:00 Beijing (20:00 EST / 21:00 EDT)
int   shAsia  = locClk ? (zAsia == "Asia/Tokyo" ? 780 : 720) - f_offMin(zAsia) : 0     // Tokyo-NY = 780 in US summer; Shanghai-NY = 720
int   shLdn   = locClk ? 360 - f_offMin("Europe/Berlin") : 0                            // Berlin-NY = 360 in summer and winter, 300 in mismatch weeks
```

- **Results.**
  - US winter: Tokyo − NY = 840 → `shAsia = −60`, so the Asia window becomes 19:00-23:00 ET.
  - Spring mismatch: Berlin − NY = 300 → `shLdn = +60`, so the London window becomes 03:00-06:00 and the open 03:00.
  - Otherwise all shifts are 0.
- **Membership.** Use TIME-3's minute-of-day overlap test `f_inWin(sM + sh, eM + sh)` with wrap handling (TIME-3 gives the code), instead of `time(timeframe.period, sess, tz)` at 799, 836 and 971-974.
- **Without TIME-3** (fallback, no overlap test): build the session string at runtime from the shifted minutes and call `time(timeframe.period, sessStr, "America/New_York")`.
  - `time()` accepts a series session string (reference/time.md: `session (series string)`).
  - Build "HHmm-HHmm" by hand: `f_hh(int m) => (m / 60 < 10 ? "0" : "") + str.tostring(int(m / 60)) + (m % 60 < 10 ? "0" : "") + str.tostring(m % 60)`, applied to the start and end minutes after wrapping them into [0, 1440).

**Applies to.** `f_sessTrack` (Asia, London), `f_sessOpen` (London open), the Asia/London killzones. NY windows and the midnight open are unchanged.

**Value.**
- Session pools and anchors match the real opens all year.
- ASIA H/L changes on most winter days (A5).
- With SESS-3's per-family ledger, the user can A/B the two clocks on their own symbol.

**Evidence:** moderate (A1-A4 natural experiment, consistent with A6).

**Risk.**
- ICT purists expect fixed New York times; the "New York fixed (ICT)" option keeps them.
- The shift changes historical levels in Nov-Mar, so ledger numbers change when toggled.
- `hour(time, zone)` is per-bar series and cheap (four calls per bar).

**Effort:** S.

### ASSET-3 (P1, M) · RTH and ETH key levels from named sessions (futures and stocks)

**Why.** B1: on index futures, at least one ETH extreme differs from RTH on 70-85% of days (median 0.2 ADR). Today the engine shows only the chart session's PDH/PDL (X3). Stock ETH charts produce a pre/post-market "PDH" (X3).

**Input** (`G_KEY`):

```pine
string keySess = input.string("Auto", "Key Level Session", options = ["Auto", "Chart", "RTH", "Both"], group = G_KEY,
  tooltip = "Auto: index futures = Both (ETH PDH/PDL + RTH H/L), stocks = RTH, others = Chart.")
```

**Data:**

```pine
string rthName = mkt <= 1 ? "us_regular" : session.regular                // falls back to the default session where the name does not exist
string rthTk   = mkt <= 1 ? ticker.new(syminfo.prefix, syminfo.ticker, rthName) : ticker.modify(syminfo.tickerid, session.regular)
bool   wantRth = (keySess == "RTH" or keySess == "Both" or (keySess == "Auto" and (mkt == 0 or mkt == 4))) and timeframe.isintraday
[rH, rL, rC, rT] = request.security(rthTk, f_tfSafe("D"), [high[1], low[1], close[1], time[1]], lookahead = barmerge.lookahead_on)
bool rthNew = wantRth and f_changedT(rT)
```

- This is one call. The engine is far below the 40-request limit; the current count is about 6.
- The trading-day alignment of the RTH daily series to ETH chart bars follows `time_tradingday`. During the overnight, `[1]` is the prior RTH day. That is the intended "previous RTH day" and is non-repainting.

**Sources.**
- New `src 8` = "RTH H"/"RTH L" in `f_tierW` (tier 0.78), `f_levelName` (518-529), the `src` comment (316) and `f_kzAff` (neutral).
- Pushed via `f_pushExt(extReg, rH, true, 8, aBar, prom, hmD)` with `aBar` from `f_anchorScan(rH, true, anchorMax)` (1141) so the zone anchors on the exact print candle.
- `f_pushExt` de-duplicates equal prices (when RTH = ETH extreme, the higher tier PDH stays).
- **"RTH" mode** (stocks on ETH charts): replace the chart PD push (1790-1794) by the RTH push, so that "PDH" means the RTH high.
- **Anchors** (1931): add `rC` (prior RTH close: the gap reference) and the RTH open (first bar where `session.isfirstbar_regular` for stocks, or the 09:30 window open for futures via `f_sessOpen("0930-0931", "America/New_York")` with TIME-3 overlap) to `anchors`.

**Display.**
- Clean target code `RTH H` / `RTH L`.
- Tooltip "RTH high 09:30-16:15 ET (prior day)".

**Value.**
- The levels AMT and stock traders actually watch, on the charts they use.
- The ledger (per-family, SESS-3) shows which set is the better target on the user's symbol.
- B2: RTH levels are taken more often next day (ES PDH 58.5% vs 50.9%), which is purely geometry; the ledger's random-level baseline is what tells whether they are *better than distance*.

**Evidence:** moderate (B1-B2) for relevance; strong for feasibility (concepts/sessions.md ES1! / `us_regular` example).

**Risk.**
- `"us_regular"` exists for US CME futures. Other exchanges use other names (FDAX `xetr_regular`), so non-US futures fall back to the default session, a duplicate of ETH. De-dup handles it.
- A 1H chart cannot anchor 09:30 exactly; `f_anchorScan` finds the bar that contains the price.

**Effort:** M.

### ASSET-4 (P1, S) · Session-artefact guard: rollover wicks and session-open gaps are not raids

**Why.**
- C3-C4: FX rollover wicks are spread artefacts.
- §1.4: session-open gaps jump over stops; they do not run them.
- The engine deletes the pool and feeds `liqEvt` (1580-1582) in both cases (X7, X8), which biases D toward reversal after rollover wicks and toward continuation after gaps.

**State:**

```pine
bool gapBar  = barstate.isconfirmed and not na(time[1]) and (time - time[1]) > 2 * chartS * 1000      // weekend, halt, overnight (RTH charts), holiday
bool rollWin = mkt == 2 and not na(time(timeframe.period, "1655-1715", "America/New_York"))             // use TIME-3 overlap test on coarse bars
```

**Rules**, in the sweep loop (1556-1585):
1. If `rollWin` and the level is liquidity, require a **close** beyond the level for a sweep (`lv.side == 1 ? close > lv.price : close < lv.price`). A wick-only touch increments `lv.tests` (density pillar) and the level stays. Arrays are unaffected.
2. If `gapBar` and the *open* is already beyond the level (`lv.side == 1 ? open > lv.top : open < lv.bottom`), the level is removed as swept.
   - The ghost label becomes "⤳ GAPPED".
   - `liqEvt` gets **no** contribution (`evt := 0`).
3. The registry raid check (1587-1592) gets the same two rules.
4. In `f_step` (1434), a rollover-window wick does not count as a hit for liquidity targets; a close is required. Gap hits are already settled at the open (bar-path rule). Add `t.gapHit := true` so the accuracy panel can show "of which gapped: k".

**Value.**
- On FX and spot gold, pools near price survive the daily rollover.
- D stops flipping on artefacts.
- The ledger's HIT% stops counting spread wicks as hits.
- On futures and stocks, Monday/RTH opens no longer feed fake raid outcomes into D.
- Measurable: count rollover hits and gap hits per 1000 bars before and after; the EDGE z should not fall.

**Evidence:** moderate (C3 this study; C4 CME/broker documentation).

**Risk.**
- A genuine rollover-hour run that closes back inside is ignored as a sweep. It is still recorded as a test.
- A broker feed with mid-based bars has no artefact; the rule then costs only a little sensitivity.

**Effort:** S.

### ASSET-5 (P2, M) · Continuous-futures roll handler (detect the switch bar, shift stored levels by the jump)

**Why.**
- C1-C2: with back-adjustment off (the TradingView default), the roll jump sweeps every pool in its path. On ES the jump is about +40-60 pts (6× the median hourly range).
- The jump also creates a fake FVG/displacement and shifts all distances by the basis.
- After the roll, the real liquidity of old levels sits at old price + basis in the new contract.

**Detection** (two same-timeframe requests; only meaningful on continuous futures):

```pine
bool isCont = mkt <= 1 and not na(syminfo.current_contract)
float cOff = request.security(ticker.modify(syminfo.tickerid, backadjustment = backadjustment.off), timeframe.period, close)
float cOn  = request.security(ticker.modify(syminfo.tickerid, backadjustment = backadjustment.on),  timeframe.period, close)
float adjD = isCont ? nz(cOff) - nz(cOn) : 0.0          // -cumulative future adjustments; steps by +jump at each roll
bool  chartAdj = math.abs(close - nz(cOn, close)) < math.abs(close - nz(cOff, close))   // user enabled B-ADJ: nothing to fix
float rollJump = isCont and not chartAdj and barstate.isconfirmed ? adjD - nz(adjD[1], adjD) : 0.0
bool  rollBar  = math.abs(rollJump) > syminfo.mintick
```

- Same-timeframe requests without an offset return the same bar's value; the step location is a calendar fact (no price lookahead).
- On non-futures, or where the option does not exist, `cOff == cOn`, so `adjD = 0`.

**On `rollBar`**, in the engine block before the sweep loop:
- Shift every stored price by `rollJump`:
  - `pool` levels (`price`, `top`, `bottom`, `oTop`, `oBot`);
  - `extReg[].px`;
  - iFVG trackers;
  - `aPDH`/`aPDL`/`aPWH`/`aPWL`, `midOpen`/`ldnOpen`/`nyOpen`;
  - `obSwingH`/`obSwingL`;
  - open ledger trials (`edge`, `inv`, `entry`).
  - Boxes and lines are redrawn on tail bars anyway; ghosts are left as history.
- Skip sweeps, raids and new FVG/OB creation on this bar (`continue` the relevant blocks).
- Mark the next 2 bars "no FVG" (the 3-candle window straddles the jump).
- Optionally (input) draw a thin vertical "ROLL +56.5" marker.

**Value.**
- Removes four wrong-sweep clusters per year (index) or twelve (CL) on default TradingView charts.
- Old pools keep their meaning in the new contract.
- The draw vector is not hit by a fake +6× displacement.

**Evidence:** strong (data fact plus vendor documentation). The improvement is measurable as fewer "swept" events on roll bars.

**Risk.**
- **Request count:** +2.
- **Back-adjusted request availability:** Pine docs: "This setting only affects the data from symbols with this option available on their charts". Where unavailable the handler is a no-op.
- **Coefficient source:** the coefficient is computed from daily closes near the switch, so `rollJump` approximates the intraday jump. That is acceptable.
- **Contract flips in thin holiday sessions** (seen in the data, ES 2025-09-03; GC Aug-2025) appear as two opposite jumps; both are handled.
- **Verification:** must be checked on ES1! in TradingView before release.

**Effort:** M.

### ASSET-6 (P2, S-M) · Crypto weekend model: weekend range as a Monday target, weekend state for killzones and PD levels

**Why.**
- F1-F2: weekend ranges are calendar-compressed (Sat 0.46 ADR) and are taken on Monday 81.7% of the time, +9 to +12 pp above weekday ranges at the same distance.
- F3: weekend volume share 13-16%.
- X5, X15: the engine runs killzones and session pools on weekends, and on Monday its "PDH/PDL" is Sunday's thin range.

**State** (crypto only, `mkt == 3`):

```pine
int  dowU   = dayofweek(time, "UTC")
bool wkend  = is247 and (dowU == dayofweek.saturday or dowU == dayofweek.sunday)
bool wkStart = wkend and not wkend[1]
bool wkEnd   = not wkend and wkend[1]                 // first Monday 00:00 UTC bar
var float wkH = na
var float wkL = na
var int wkHB = na
var int wkLB = na
if wkStart
    wkH := high
    wkL := low
    wkHB := bar_index
    wkLB := bar_index
else if wkend
    if high > wkH
        wkH := high
        wkHB := bar_index
    if low < wkL
        wkL := low
        wkLB := bar_index
```

**On `wkEnd`:** push `src 9` "WKND H"/"WKND L" (tier 0.70) to the registry with `hlm = √(bars per day)`, so they age on a day clock.

**Other rules.**
- **Killzones:** `kz := wkend ? 0 : kz`, labelled "WEEKEND" in `f_kzName`. Hysteresis uses `kzHx` on weekends.
- **Sessions:** Asia/London/NY trackers skip weekend days. Session-string days are "12345" for Asia (Sunday-Thursday evenings, NY time) and "23456" for London/NY; this needs no new code.
- **PD levels:** input `bool skipWkPD = input.bool(true, "Crypto: skip weekend days for PDH/PDL", group = G_KEY)`. When on, `pdNew` pushes are suppressed for days whose trading day is Saturday or Sunday UTC. Friday's PDH/PDL stay the previous-day levels on Monday, and the weekend range is handled by WKND H/L.
- **Ledger:** `grp` stays 1 (external liquidity). With SESS-3's per-family split, WKND gets its own family.
- **Clean code:** "WKND H"/"WKND L".

**Value.** The highest-take-rate crypto-specific pool becomes a first-class target with a natural Monday horizon. Weekend noise is removed from killzones and PD levels.

**Evidence:** moderate (F2 this study, 8 years; no clock-null) plus strong (F1, F3).

**Risk.**
- Users anchored on the NY-midnight day (SESS-6) may prefer the weekend defined as Friday 17:00 → Sunday 17:00 NY. Offer `wkDef = "UTC Sat-Sun" | "NY Fri 17:00 - Sun 17:00"`.
- The Monday take rate partly reflects the low weekend ATR inflating the ADR-normalised distance. The ledger baseline (random level at the same distance) controls for it.

**Effort:** S-M.

### ASSET-7 (P2, S) · Session completeness: measured bars per day/week, short-day (holiday) handling

**Why.**
- X10: holiday and half-day extremes (0.58-0.76 ADR, as low as 0.08) enter the registry as full PDH/PDL with tier 0.80.
- X11: wall-clock bars-per-day/week make PD/PW/HTF freshness clocks 1.9-2.3× too slow on stocks.

**State:**

```pine
var int   dayBars = 0
var float bpd     = na          // EMA of bars per completed trading day (full days only)
var float bpw     = na
var int   wkBars  = 0
int   lastDayBars = 0
if timeframe.change("D")
    lastDayBars := dayBars
    if dayBars > 0 and (na(bpd) or dayBars >= 0.75 * bpd)
        bpd := na(bpd) ? dayBars : 0.9 * bpd + 0.1 * dayBars
    dayBars := 0
dayBars += 1
// same for weeks with timeframe.change("W") → bpw
float dayFrac  = na(bpd) or bpd <= 0 ? 1.0 : math.min(1.0, lastDayBars / bpd)
bool  shortDay = dayFrac < 0.75
```

**Uses.**
1. PD push (1790-1794): `pdProm *= dayFrac`; when `shortDay`, use tier 0.55 (session-like) via a new `src 10` "½D H/L", or keep `src 6` with a `tierAdj` field. The tooltip says "short session (holiday)".
2. Replace `86400.0 / chartS` (1792) with `nz(bpd, 86400.0 / chartS)` and `604800.0 / chartS` (1797) with `nz(bpw, 604800.0 / chartS)`.
3. `f_tfRatio` (567) gets a measured override: for `tf == "D"` return `nz(bpd, …)`, for `"W"` `nz(bpw, …)`. Intraday tfs stay wall-clock; they are exact within a session.
4. **Also** shows "½ DAY" in the Terminal panel on short days. PoT is unchanged; TIME-1's clock handles the variance.

**Value.**
- Correct ageing of key levels on stocks (the most-used non-futures class).
- Thanksgiving/Christmas/outage days no longer create high-tier pools.
- Ledger-measurable through the PD-family hit rate (SESS-3).

**Evidence:** weak-moderate (D1-D2) for the holiday part; strong (arithmetic) for bars-per-day.

**Risk.**
- `f_tfRatio` takes a `simple string` and returns a series once measured. Its callers (1780-1781, 1864) already use the result as series floats.
- The first day on the chart has `na` → fallback.

**Effort:** S.

### ASSET-8 (P2, M) · Asset-aware scheduled-event calendar (recurring presets plus a date list), news flags and news-window rules

**Why.**
- X13: liquidity runs cluster at known times:
  - Thursday 08:30: ES 1.33× vs 1.02×;
  - FOMC 14:00: GC 4.9×;
  - EIA Wednesday 10:30 for crude.
- The first minutes after a release carry little directional information (E5), and some releases drift about 30 minutes before (E6).
- This extends TIME-7 (one manual event that scales TIME-1's clock) with asset presets, a multi-date list, UI and ledger rules.

**Inputs** (`G_CONF`):

```pine
bool   evOn    = input.bool(true, "Scheduled Events", group = G_CONF)
string fomcIn  = input.text_area("2026-12-09,2027-01-27,2027-03-17", "FOMC dates (YYYY-MM-DD, 14:00 ET)", group = G_CONF)
string evExtra = input.text_area("", "Other events (YYYY-MM-DD HH:MM ET, comma-separated)", group = G_CONF)
```

**Recurring presets**, computed per bar, no calendar needed:

```pine
int  dowNY = dayofweek(time, "America/New_York")
int  domNY = dayofmonth(time, "America/New_York")
bool usDataDay = dowNY >= dayofweek.monday and dowNY <= dayofweek.friday
int  ev0830 = usDataDay and (mkt != 3 or not wkend) ? timestamp("America/New_York", year(time, "America/New_York"), month(time, "America/New_York"), domNY, 8, 30) : na
bool certain0830 = dowNY == dayofweek.thursday or (dowNY == dayofweek.friday and domNY <= 7)     // claims; NFP (approximate rule)
int  evEIA  = mkt == 1 and (syminfo.root == "CL" or syminfo.root == "MCL" or syminfo.root == "RB" or syminfo.root == "HO") and dowNY == dayofweek.wednesday ? timestamp("America/New_York", ..., 10, 30) : na
// GC/SI/XAU: LBMA 10:30 and 15:00 Europe/London; FX: 16:00 Europe/London (WM/R), 09:55 Asia/Tokyo
```

**FOMC list.**
- Parse once with `var array<int> fomcT`. On the first bar: `str.split(fomcIn, ",")`, then for each `s`:

  `timestamp("America/New_York", int(str.tonumber(str.substring(s, 0, 4))), int(str.tonumber(str.substring(s, 5, 7))), int(str.tonumber(str.substring(s, 8, 10))), 14, 0)`

- `timestamp(timezone, y, m, d, h, mi)` exists in v6 (reference/time.md) and handles DST through the IANA zone.

**Next event.** `nextEv` = the soonest event timestamp ≥ `time_close` within the PoT horizon `time + H × chartS × 1000`, plus its kind.

**Uses.**
1. **UI.**
   - Terminal HUD: `⚑ FOMC 14:00 in 2h10`.
   - Clean: the label tooltip line `Event: FOMC 14:00 ET (in 2h10)`; the face of the label adds a small "⚑" only when the event is inside the horizon.
   - Alert: "Scheduled event inside PoT horizon" (optional).
2. **Variance.** If TIME-1 lands, multiply clock cells in `[ev, ev + 30 min)` by `evX[kind]`: FOMC 2.5 (GC 4.0), certain-08:30 1.3, possible-08:30 1.1, EIA 1.2 (defaults from E1-E2; learnable later). Without TIME-1, scale `potSig` in `f_pot` for horizons that contain an event by `√(1 + (evX − 1) × evBars / H)`.
3. **Raid weighting.** Sweeps whose bar overlaps `[ev, ev + 15 min)` add `0.5 × evt × tier` to `liqEvt` (1582), not the full weight (E5).
4. **Ledger tagging.** A trial opened within `[ev − 30 min, ev + 15 min)` sets `t.news := true`. The Full accuracy view shows HIT% and EDGE split news/non-news, so the user sees whether targets chosen into releases behave differently. This uses the existing `f_book` (1461) with one extra pair of counters.

**Value.**
- The trader is warned when a DOL decision depends on a release.
- PoT reflects the known variance bump.
- D is less whipsawed by release bars.
- The ledger can show the news split.

**Evidence:** strong for the mechanics and magnitudes (E5-E7, E9); moderate for the asset-specific magnitudes (E1-E2, this study, n = 8 FOMC).

**Risk.**
- User-maintained date lists go stale; the empty default makes them a no-op.
- The NFP "first Friday" rule is wrong in some months (BLS can release on the second Friday); it is tagged as "possible".
- `input.text_area` returns an input string; parsing runs once on the first bar.

**Effort:** M.

### ASSET-9 (P3, S) · Data-availability and chart-timeframe guards

**Why.** X16, X17, X18 and §1.1: silent inert features and mislabelled levels.

**Spec.**
- **No volume:** `if not hasVol` → force `showLVN` and `usePathVP` off (`needVP := false`, 979). The Terminal panel shows `VOL n/a` and the LVN tooltip says "No volume on this symbol (cash index?): use the futures contract".
- **Tick volume:** if `syminfo.volumetype == "tick"`, the panel shows `VOL tick` (an LVN caveat).
- **Cash index:** when `syminfo.type == "index"`, the HUD note "cash index: opening print is stale; gaps unreliable" (session_stats §2.9).
- **Timeframe gating:** `useKeyD` effective only when `timeframe.in_seconds() < 86400`; `useKeyW` only when `< 604800`. This prevents the "PDH" = prior-week-high mislabel on W charts.
- **Settlement:** a tooltip note on futures daily HTF structure: "Daily closes are settlement prices (TradingView default)". No code change. An optional input `settleAsClose` could request structure with `ticker.modify(syminfo.tickerid, settlement_as_close = settlement_as_close.off)`, so body breaks use the last trade. Default off (inherit), so D-chart users see the same candles.
- **Stock 24h session:** if `syminfo.session` is not "regular"/"extended" (e.g. a 24h session name), treat the day boundary as exchange and show `SESSION 24h` in the panel. This reuses `syminfo.session` as a string.

**Value:** fewer silent failures and clearer UX. Not a forecasting change.

**Evidence:** strong (definitional).

**Risk:** none material.

**Effort:** S.

### Not recommended (evidence says no, or too unstable)

| Idea | Why not |
|---|---|
| Fixed session-directional priors in D (overnight drift at the Europe open, pre-FOMC long tilt, "gold up in Asia / down in NY", "EUR weakens in European hours") | G1, E7: the S&P overnight drift was flat in 2021-25 and the pre-FOMC drift faded after 2011. If wanted at all, use a learned, bounded D term with ledger gating (like TIME-9) |
| Funding-time targets/anchors for crypto | F5: a weak, confounded bump; funding intervals change per symbol (Binance moves to 4-hourly or hourly at the cap) |
| "CME gap must fill" level for BTC | session_stats §2.9: fill = mirror level; since 2026-06-01 there are no new CME weekend gaps |
| News-whipsaw rule ("both sides of the pre-release range get taken") | E4: noisy, n ≈ 12 per weekday; no consistent excess |
| Hard-coded per-asset killzone multipliers | Same reasoning as SESS-3/TIME-5: learn them per chart |

---

## 5. Sources

**This study** (scripts and outputs in `study/asset_tools/`):
- `sanity.py` / `out_sanity.txt`: timezone check, 17:00 ET halt, roll/contract-flip jumps.
- `dst.py` / `out_dst.txt`: 15-min activity profiles by DST regime (ES, NQ, YM, RTY, GC, CL, 6E, 6B, MBT).
- `dst2.py` / `out_dst2.txt`: per-day bucket comparisons with bootstrap CIs.
- `asia_hol.py` / `out_asia_hol.txt`: Asia range NY-fixed vs Tokyo-local; short CME sessions.
- `rth_eth.py` / `out_rth_eth.txt`: ETH vs RTH day extremes and next-day take rates.
- `news.py` / `out_news.txt`: weekday-scheduled releases (08:30 Thursday, EIA Wednesday), FOMC 14:00.
- `crypto.py` / `out_crypto.txt`: BTC hourly profile, funding hours, weekend compression, weekend range taken Monday, day-boundary sensitivity.
- `fx.py` / `out_fx.txt`: EURUSD hourly profile and rollover-hour wick fraction.
- Data: public CME continuous OHLCV CSVs (github.com/axb0306/cme-futures-ohlc) in `study/amt_data/cme/` and `study/smt_data/cme/`; BTC 1-h in `study/session_data/btc_1h.pkl`; EURUSD 1-h in `study/bias_data/EURUSD.csv`.

**Pine v6 documentation** (local mirror `docsrc/jabez4jc_pinescriptv6/`):
- `reference/syminfo.md`: type, session, timezone, root, basecurrency, current_contract, expiration_date, volumetype.
- `reference/session.md`: isfirstbar(_regular), islastbar(_regular), ismarket, ispremarket, ispostmarket.
- `reference/ticker.md`: `ticker.modify(tickerid, session, adjustment, backadjustment, settlement_as_close)`.
- `reference/time.md`:
  - `time(tf, session, timezone, …)`: default days 1234567;
  - `time_tradingday`;
  - `timestamp(timezone, y, m, d, h, mi)`;
  - `dayofweek(time, timezone)`.
- `concepts/sessions.md`: named sessions; ES1! "regular" = ETH and "us_regular" = RTH; FDAX `xetr_regular`/`fwb_regular`; fallback to the default session for missing names.
- `concepts/time.md`: IANA zones adjust for DST.

**External** (WebSearch summaries; full texts not opened unless stated):
- Ito, T. & Hashimoto, Y. (2006). Intraday seasonality in activities of the foreign exchange markets: evidence from the electronic broking system. *J. Japanese & Int'l Economies* 20(4). https://www.nber.org/papers/w12413
- Breedon, F. & Ranaldo, A. (2013). Intraday patterns in FX returns and order flow. *JMCB* 45(5), 953-965. https://www.snb.ch/en/publications/research/working-papers/2011/working_paper_2011_04
- Evans, M.D.D. (2018). Forex trading and the WMR Fix. *J. Banking & Finance* 87, 233-247. https://econpapers.repec.org/RePEc:eee:jbfina:v:87:y:2018:i:c:p:233-247
- Andersen, Bollerslev, Diebold & Vega (2003). Micro effects of macro announcements. *AER* 93(1), 38-62. https://www.nber.org/papers/w8959
- Ederington, L. & Lee, J.H. (1993). How markets process information: news releases and volatility. *J. Finance* 48(4), 1161-1191. https://ideas.repec.org/a/bla/jfinan/v48y1993i4p1161-91.html
- Fleming, M. & Remolona, E. (1999). Price formation and liquidity in the U.S. Treasury market. *J. Finance* 54(5), 1901-1915. https://econpapers.repec.org/RePEc:bla:jfinan:v:54:y:1999:i:5:p:1901-1915
- Kurov, Sancetta, Strasser & Wolfe (2019). Price drift before U.S. macroeconomic news. *JFQA* 54(1), 449-479. https://www.skidmore.edu/economics/documents/KSSW2017-PriceDriftBeforeUSMacroeconomicNews.pdf
- Lucca, D. & Moench, E. (2015). The pre-FOMC announcement drift. *J. Finance*. https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr512.pdf ; https://libertystreeteconomics.newyorkfed.org/2012/07/the-puzzling-pre-fomc-announcement-drift
- Boyarchenko, Larsen & Whelan (2023). The overnight drift. *RFS*. https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr917.pdf ; "The Disappearing Overnight Drift" (2026): https://libertystreeteconomics.newyorkfed.org/2026/07/the-disappearing-overnight-drift/
- Caminschi, A. & Heaney, R. (2014). Fixing a leaky fixing. *J. Futures Markets* 34(11). https://ideas.repec.org/a/wly/jfutmk/v34y2014i11p1003-1039.html
- Caporale, G.M. & Plastun, A. The day of the week effect in the cryptocurrency market. *Finance Research Letters*. https://bura.brunel.ac.uk/handle/2438/17208
- Eross, McGroarty, Urquhart & Wolfe (2019). The intraday dynamics of bitcoin. *RIBAF* 49, 71-81. https://centaur.reading.ac.uk/81745
- EIA inventory shocks and WTI intraday response, *J. Energy Markets*: https://www.risk.net/journal-of-energy-markets/5728636/an-analysis-of-intraday-market-response-to-crude-oil-inventory-shocks ; Wen, Indriawan, Lien & Xu, *Energy Journal* exec summary: https://www.iaee.org/ej/ejexec/ej44-5-Xu-exsum.pdf
- Gold overnight vs day returns (COMEX): https://link.springer.com/10.1007/s12197-017-9403-0 ; Chinese gold/silver "night effect": https://ideas.repec.org/a/eee/glofin/v64y2025ics1044028325000110.html
- Kaiko via The Block / Bloomberg: weekend share of BTC volume, https://www.theblock.co/news/markets/2024-02-27-bitcoin-weekend-trading-279353 , https://www.bloomberg.com/news/articles/2024-06-29/-boring-bitcoin-sends-weekend-trading-volume-to-all-time-lows ; US-hours share, https://www.bloomberg.com/news/articles/2024-05-21/share-of-bitcoin-volume-during-us-market-hours-surges-to-record
- Binance funding schedule and interval changes: https://www.binance.com/en/support/faq/introduction-to-binance-futures-funding-rates-360033525031 ; https://www.binance.com/en/support/announcement/3243c81a35bd4f0c86a37315c3dc96cc
- CME 24/7 crypto futures launch (2026-06-01): https://www.cmegroup.com/media-room/press-releases/2026/6/01/cme_group_announceslaunchof247cryptocurrencyfuturesandoptionstra.html
- CME "When FX futures pause" (rollover spreads): https://www.cmegroup.com/articles/2026/when-fx-futures-pause.html
- CME holiday advisories (Thanksgiving): https://www.cmegroup.com/trading-hours.html ; https://cmegroup.com/tools-information/holiday-calendar/files/2025/2025-thanksgiving-clearing-advisory.pdf
- CME Globex outage 2025-11-28: https://fortune.com/2025/11/30/cme-outage-financial-markets-data-center-cyrusone-aurora-illinois/
- TradingView:
  - RTH for CME futures (08:30-15:15 CT): https://www.tradingview.com/blog/en/regular-trading-hours-for-cme-futures-28648
  - back-adjustment: https://www.tradingview.com/support/solutions/43000685266
  - settlement as close: https://in.tradingview.com/support/solutions/43000685268
  - 24h US stock session: https://it.tradingview.com/support/solutions/43000790593/
- LBMA Gold Price auction times (10:30 / 15:00 London): https://www.ice.com/iba/lbma-gold-price
- Russell Investments, holiday trading volumes: https://russellinvestments.com/content/ri/us/en/insights/russell-research/2025/11/holiday-trading-effect.html
- 24-hour US equities (NYSE approval, Nasdaq plan): https://governancebeat.cooley.com/24-hour-trading-nasdaqs-faqs-and-secs-roundtable/ ; https://www.bloomberg.com/news/articles/2025-03-07/nasdaq-joins-exchanges-seeking-to-offer-round-the-clock-trading
- DST mismatch 2026 (US Mar 8, EU Mar 29): https://admiralmarkets.com/about-us/news/us-daylight-saving-time-march-2026
