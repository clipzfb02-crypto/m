# x1 · Market internals and breadth for US index futures (final report)

Scope: NYSE / Nasdaq / Dow TICK and cumulative TICK; ADD (advance-decline); VOLD and the up/down volume ratio; TRIN (Arms);
S&P 500 internal breadth; percent of stocks above VWAP; equity and index put/call ratios; index premium vs fair value
(program-trading triggers); megacap "generals"; intraday VIX as a risk gauge. How practitioners use them (day-type
classification by 10:00-10:30 ET, TICK extremes at a level, breadth divergence at new highs/lows, internals confirming a
sweep), the published evidence, **our own tests on 36-38 sessions of 30-second intraday internals with ES/NQ/YM prices**,
a gap analysis against `baseline_v2.pine`, and Pine v6 feasibility.

Tags: **[T]** = our test (scripts in `study/x1_int_tools/`, outputs `out_*.txt`); **[L]** = literature with numbers;
**[P]** = practitioner material (weak); **[D]** = Pine documentation quote (mirror under `scratchpad/docsrc/`).

---

## 0. Executive summary (read this if nothing else)

1. **No incremental forecasting value found for the engine's problem.** After correct time alignment, on 35-37 sessions
   (Jul-Aug and Oct-Nov 2026; 1,571 race events, 511 sweeps, 10.6k minute observations) **none of TICK, ADD, VOLD, TRIN,
   S&P 500 breadth (ADSPD), NQ-vs-ES leadership or ΔVIX** predicts *which nearest pool is taken first* beyond the
   driftless geometry `b/(a+b)` and price momentum, or the next 5-60-minute ES return [T].
   - Race residual correlations (5-min bars): ΔADD −0.011 [−0.111, +0.089]; ΔADSPD +0.001; TICK 30-min mean +0.050
     [−0.074, +0.160]; ΔVOLD −0.056; TRIN −0.099 [−0.221, +0.031]; ΔVIX 0.000 (day-cluster bootstrap 95% CIs).
     Leave-one-day-out log-loss gets *worse* (−0.1% to −1.0%) when any internals feature is added to geometry+momentum.
   - Forward returns: every internals coefficient |t| < 2 given momentum (TICK +0.04-0.075 SD per SD at 30-60 min,
     t 1.0-1.5; TRIN −0.05 to −0.09, t −1.4 to −1.9).
   - This agrees with the literature: market-wide order-imbalance predictability lasted ≤ 30 min in 1996, ≤ 10 min in
     1999 and ≤ 5 min in 2002 (Chordia, Roll & Subrahmanyam 2005) [L]; daily imbalances do not predict next-day index
     returns (CRS 2002) [L]; index futures lead the cash market (20-45 min in 1984-85, ~5 min by 1990, seconds today) [L],
     so stock-based internals mostly *lag* ES.
2. **A large fake edge is easy to manufacture.** In the raw snapshot data the ES/NQ/YM prices were **585 s late** and VIX
   **930 s late** relative to the internals (10-minute-delayed CME feed, 15-minute-delayed Cboe index). Before alignment,
   ΔADD(15 min) "predicted" the next 5-minute ES return with coefficient +0.337 SD and day-clustered **t = +14.3**; after
   alignment it is −0.009 (t −0.4) [T]. TradingView itself serves CME data **10 minutes delayed** to users without a
   real-time CME subscription. Any internals feature in Pine therefore needs a **bar-time freshness guard**, or realtime
   bars on a delayed chart will see internals from the future.
3. **Practitioner claims tested [T]:**
   - *TICK extreme at a liquidity level = stop-run / exhaustion*: no effect on continuation vs failure after a sweep
     (difference −3.2 pp [−13.7, +7.8], n 103 extreme vs 408 not).
   - *Breadth divergence at a new high/low (SMT-like) = reversal*: not supported; if anything the reverse (ADD-divergent
     sweeps continued **more**: −5.3 pp [−12.2, +2.4] confirm-minus-diverge; at session extremes +18.3 pp excess vs +3.7 pp).
   - *Day type from ADD/VOLD by 10:00-10:30*: |ADD|, |ADSPD|, |VOLD ratio| and TICK mean are unrelated to the trend-day
     score (Spearman −0.12 … +0.13, n 33). The size of the price move by the cut correlates (+0.42 at 10:00, +0.51 at
     10:30, partly mechanical). Breadth sign and price sign pick the opening-range side that gets taken equally well.
   - *Claim C1 (trends: opposite liquidity holds)*: the pool on the breadth side is not taken first more often, even
     with strong breadth (ADD −2.8 pp, ADSPD −8.7 pp, TICK +4.2 pp, all CIs include 0). A **price** trend state does
     slightly better (60-min direction in the top efficiency tercile +5.9 pp [+0.4, +11.0]), matching quant_regime.
   - *Claim C2 (ranges: both sides raided)*: |ADD|, |ADSPD| and price efficiency show no gradient. **A balanced TICK tape
     (|30-min TICK mean| ≤ ~65) has +6.2 pp [+1.1, +12.5] more "both nearest pools raided within 60 min"** than geometry,
     clock and volatility state predict (base rate 9%); continuous-feature LOO log-loss gain +2.3% [−3.2, +6.7]. This is
     the only internals effect that survived controls, at one-of-many-tests strength: **weak**.
4. **Recommendation.** Do not feed internals into D, the Draw pillar, scoring or selection. Build an *optional*,
   US-index-only internals feed with data-health guards (INT-1) whose only default use is **ledger cells** that measure
   C1/C2 and the sweep claims on the user's own chart (INT-2, INT-4). A bounded adjustment (INT-3) and display (INT-5)
   come only after the ledger shows an effect. A chart-wide **delayed-feed detector** (INT-6) is cheap and valuable on its
   own. Requests: +3 (TICK, breadth, TRIN), total stays far below the 40-request cap.
5. **Data limits of our tests.** 36-38 sessions in one calm-to-moderate regime (VIX 14.8-28.0, no 80%/90% volume days),
   30-second snapshots (TICK extremes are under-sampled vs 1-minute bar highs/lows), one vendor (IQFeed). Effects of
   ±5 pp cannot be excluded; effects of ±10 pp on the race mostly can.

---

## 1. Concepts (definitions and parameters)

### 1.1 TICK (NYSE, Nasdaq, Dow) and cumulative TICK
- **Definition.** Number of issues whose last trade was an uptick minus the number whose last trade was a downtick, over
  the whole listing universe, updated continuously. NYSE ≈ 2,650-2,820 issues in our 2026 sample (`nyse_tot`).
  Vendors compute it differently: forum users report differences of a few hundred points between feeds (NinjaTrader
  forum) [P]; Barchart's `$TICK` uses a 10,000 baseline vs `$TICX` at 0 [P].
- **TradingView tickers** (from the USI symbol list mirrored at `raw.githubusercontent.com/thonguyen511/tdv/HEAD/data/USI.csv`):
  `USI:TICK` (labelled "NYSE CUMULATIVE TICK" in the list; it is the classic NYSE TICK chart), `USI:TICK.NY`
  ("NYSE TICK INDICATOR"), `USI:TICKQ` / `USI:TICK.NQ` (Nasdaq), `USI:TICKI` / `USI:TICK.DJ` (Dow 30),
  `USI:TICK.US` (all US stocks), `USI:TICKA` (AMEX), `USI:TICKBA.NY` (ticks of trades at bid/ask). An open-source TV
  script uses `USI:TICK.NY` as its default input (GitHub `ChartsLector/TV-Indicators`). Which family has longer history
  on TV is unverified; Pine should accept either via input and `ignore_invalid_symbol = true`.
- **Distribution [T].** 30-s snapshots of NYSE TICK (Jul-Nov 2026): 0.5% −848, 1% −732, 5% −403, median +18, 95% +398,
  99% +565, 99.5% +637; mean +9. A 5-minute bar's snapshot max reached ≥ +600 on 3.1% of bars, ≥ +800 on 0.5%; min ≤ −600
  on 4.1%, ≤ −800 on 1.5%. True 1-minute bar highs/lows reach ±1000 more often than these snapshots. Practitioners note
  raw TICK spends more time above zero than below (positive bias) [P]; Steenbarger's *adjusted TICK* subtracts a trailing
  mean to remove it [P].
- **Practitioner thresholds [P].** |TICK| < 400 = chop/ignore; ±600-800 = real push; ±1000 / ±1200 = extreme. Two opposite
  readings of the extreme: *exhaustion/washout* (fade it; "usually good for 4-8 ticks" anecdotally) and *thrust/trend-day
  signature* (repeated extremes on one side, TICK holding one side of zero for hours).
- **Cumulative TICK** (Steenbarger): running sum of 1-minute TICK closes over the session (or across days). Trend-day
  signature: TICK holding one side of zero while cumulative TICK trends; a 21-EMA of TICK staying positive/negative is
  another variant (LuxAlgo concept page) [P].
- **Raschke's view** (from her "Capturing Trend Days" article, as summarised by secondary sources): intraday TICK
  overbought/oversold readings "work well for S&P scalps in a normal consolidation market"; on trend days they fail [P].
- **Edge cases.** RTH only (09:30-16:00 ET); the opening minutes are dominated by opening auctions/idiosyncratic moves
  (stock correlations rise through the day, Allez & Bouchaud 2010 [L]); half days; vendor scale differences make fixed
  thresholds non-portable (Nasdaq TICK has a different range than NYSE).

### 1.2 ADD (NYSE net advancers) and the intraday A/D line
- **Definition.** ADD = advancing issues − declining issues (vs prior close), cumulative through the day by construction.
  Ratio form: ADV/DEC. TV: `USI:ADD`, `USI:ADVDEC.NY`, `USI:ADDQ` / `USI:ADVDEC.NQ`, `USI:ADVDEC.US`, `USI:ADVDEC.DJ`,
  components `USI:ADV`/`USI:DECL` and `.NY/.NQ/.US/.DJ` variants.
- **Scale [T].** |ADD| median 422 at 10:00 and 527 at 10:30; |ADD| ≥ 1000 on 21% (10:00) and 11% (10:30) of sessions;
  intraday terciles of |ADD| (10:00-15:00): 352 / 729.
- **Practitioner day-type rule [P]** (NexusFi article; numbers attributed to an unnamed trader, unverified): read ADD at
  10:00 ET after the opening noise and classify before 10:30: 0-400 range day, 400-800 moderate trend bias, ≈ ±1500
  after 30 min = high-probability trend day; community TV scripts use +1000 "bullish trend", ±500 "chop". Trend day
  (Raschke): open near one extreme, close near the other, range expansion, shallow retracements; "price stays above/below
  VWAP all day".
- **Divergence rule [P].** Index makes a new session high while ADD makes a lower high (or vice versa) = narrow/weak move,
  expect failure (the breadth analogue of ICT SMT).

### 1.3 VOLD, UVOL/DVOL ratio, 90% days
- **Definition.** VOLD = up volume − down volume (issues up vs down). Ratio UVOL/DVOL (signed: if DVOL > UVOL use
  −DVOL/UVOL). TV: `USI:VOLD`, `USI:ADVDECV.NY`, `USI:UVOL`/`USI:DVOL`, `USI:UPVOL.NY`/`USI:DNVOL.NY`, Nasdaq `USI:VOLDQ`,
  `USI:ADVDECV.NQ`, all-US `USI:ADVDECV.US`.
- **Lowry 90% days** (Desmond 2002 Dow Award paper, 69 years of NYSE data): a 90% downside day has downside volume and
  points lost each ≥ 90% of the totals; "most major market bottoms contained at least one, usually more than one"; an
  isolated one has no long-term implication; two or more usually persist; the bullish signal is a 90% upside day (or
  back-to-back 80% days) within a few days after [L, practitioner-research]. Independent checks are mixed (a 2008 blog:
  "by itself a 90% down volume day is not a clear sign of a washout"; Lowry's own indicators "stopped working" in 2007) [P].
- **Scale [T].** |VOLD ratio| median 1.42 at 10:00, 1.39 at 10:30, 1.34 at the close; ≥ 3:1 on 3% of sessions at 10:00;
  closing up-volume share ranged 0.29-0.70, i.e. **no 80% or 90% days in our sample**.

### 1.4 TRIN (Arms index)
- **Definition.** TRIN = (ADV/DEC) / (UVOL/DVOL). < 1 = volume concentrated in advancers (bullish), > 1 bearish.
  Practitioner extremes: intraday > 2.0 panic, < 0.5 strong buying; closing > 1.5 oversold. TV: `USI:TRIN.NY`,
  `USI:TRIN.NQ`, `USI:TRIN.US`, `USI:TRIN.DJ`, `USI:TRIN.AM`.
- **Swing use.** Connors: SPY > 200-day SMA, RSI(2) < 50 and TRIN closing > 1.0 three days in a row → buy, exit RSI(2) > 65;
  reported 72-76% winners (90 trades over 12 years, vendor summary of the book) [P/moderate-weak; daily horizon].
- **Scale [T].** TRIN median ≈ 1.02-1.05; 5-min Δlog TRIN correlates −0.19 with ES.

### 1.5 S&P 500 internal breadth and Dow breadth
- ADSPD = S&P 500 constituents advancing − declining (in the vendor data as `spx_adv − spx_dec`). TV has no exact
  S&P-500-only adv/dec in the USI list; closest: `USI:ADVDEC.US` (all US) or the Dow-only `USI:ADVDEC.DJ`. For YM the
  natural set is `USI:TICKI` / `USI:TICK.DJ`, `USI:ADVDEC.DJ`, `USI:TRIN.DJ`.

### 1.6 Percent of stocks above VWAP
- Share of stocks trading above their own session VWAP. TV: `USI:PCTABOVEVWAP.NY`, `.NQ`, `.US`, `.DJ`, `.AM`, `.AX`.
- Use [P]: 50% midline; < 40% no longs, > 60% no shorts (one script's rules); on trend days the great majority stays on
  one side all day (Steenbarger 2016). Script authors warn the raw series is noisy and RTH-only. **Not tested** (not in
  our data). It is a level-type breadth measure like ADD and can replace ADD as the breadth source in INT-1.

### 1.7 Put/call ratios
- Total, equity-only and index-only CBOE ratios. TV: `USI:PCC` (equities + indices), `USI:PCCE` (equities), `USI:PCCI`
  (indices), `USI:PCSPX` (SPX), `USI:PC`, `USI:PCE`, `USI:PCI`, volumes `USI:PVOL`/`USI:CVOL`, `USI:PVSPX`/`USI:CVSPX`.
  Whether TV updates them intraday is unverified; treat as daily.
- Use: contrarian sentiment at multi-day horizons (high P/C = fear = bullish). Index P/C is hedging-dominated and
  inversely interpreted by some.

### 1.8 Index premium vs fair value (program-trading triggers)
- Premium = futures − cash index. Fair value = cash × (financing − dividend yield) × days/360 (+ costs). Index-arbitrage
  bands: sell-active, sell-threshold, fair value, buy-threshold, buy-active; "no profitable index arbitrage programs occur
  ... within the range from the sell threshold to the buy threshold" (indexarb.com glossary; a 2013 example put the ES
  thresholds at 3.72 and 6.10 points) [P]. Classic use: premium crossing the buy (sell) threshold triggers basket buying
  (selling) that lifts (drops) the cash index and TICK.
- Today arbitrage executes in milliseconds; the futures lead (20-45 min in 1984-85 per Kawaller, Koch & Koch; ~5 min in
  Stoll & Whaley 1990) has shrunk to seconds [L]. NYSE weekly reports put program trading at 24-49% of NYSE volume in
  2012-13 [L, descriptive].

### 1.9 Megacap leadership ("generals")
- NQ is driven by a few names: Nasdaq's own analysis puts the Magnificent Seven at ~35% of the (capped) Nasdaq-100 on
  2026-06-30 (top 5 ≈ 28%, top 10 ≈ 45%; uncapped would be 43/55/63%) [L, index-provider data]. Practitioners watch
  whether the generals confirm an NQ high ("generals vs soldiers": index up on a few megacaps with weak breadth).
- Our proxy [T]: NQ minus ES 30-minute return ("NQ leadership"); no effect (below). Real generals tracking needs one
  request per stock (7 requests).

### 1.10 Intraday VIX as a risk gauge
- VIX (`CBOE:VIX`) is computed from SPX options; intraday it moves inversely and asymmetrically with SPX. Lead-lag at
  minute scale: VIX futures now lead the cash VIX (Bollen, O'Neill & Whaley 2017); the S&P/VIX lead-lag is asymmetric and
  concentrated in the tails at 1-60-minute horizons, not at the daily horizon (arXiv 2206.13138 and the 2003-2011
  quantile study it cites) [L]. Practitioner use: VIX making a higher high while ES makes a higher high = risk-off
  divergence. **Our 5-min contemporaneous correlation ΔES vs ΔVIX is −0.77 [T]**; as a predictor it is null (below).
  The *level* of VIX/VIX1D as a variance input belongs to the sibling lens `x1_implied_vol.md` (X1-1/X1-2).

### 1.11 The practitioner playbooks bearing on "which liquidity is taken next"
| Playbook | Algorithmic form used in our tests | Claimed use for DOL |
|---|---|---|
| Day type by 10:00-10:30 | ADD, ADSPD, VOLD ratio, TICK mean since 09:30 at the cut; compare with ES move from 09:30 | Trend day: only the breadth-side opening-range extreme / PDH-PDL is taken, opposite holds (C1). Rotational: both get raided (C2). |
| TICK extreme at a level | Sweep of a pool (5-min 2-bar pivot or session high/low) with the sweep-direction TICK max in the top quintile (≥ +556 snapshot) | Stop-run / exhaustion → the sweep rejects; or thrust → continuation |
| Breadth divergence (SMT-like) | At the sweep bar, ADD (ADSPD) below its value at the bar that formed the swept extreme | Divergent new high/low fails → reversal toward opposite liquidity |
| Internals confirm the sweep | ADD sign with/against the sweep direction; bar close beyond vs back inside | Confirmed sweeps hold, unconfirmed reject |
| Breadth as regime | |breadth| terciles; sign of ADD / ADSPD / 30-min TICK mean | Regime state for C1/C2 |

---

## 2. Evidence (numbers and sources)

### 2.1 Literature
| # | Claim | Source | Numbers | Grade |
|---|---|---|---|---|
| L1 | Market-wide order imbalance moves index returns contemporaneously; reversal after large negative-imbalance days; **no one-day-ahead predictability** | Chordia, Roll & Subrahmanyam (2002), JFE 65(1) 111-130 (NYSE daily, Lee-Ready signed) | abstract-level: imbalance affects returns beyond volume and liquidity; imbalances persistent; aggregate market "resilient to microstructure effects" | strong |
| L2 | Intraday imbalance predicts returns only briefly, and less over time | CRS (2005), JFE 76(2) 271-292 (150 large NYSE stocks) | lagged imbalances predict returns up to 30 min (1996), 10 min (1999), 5 min (2002) | strong |
| L3 | Index futures lead the cash index | Kawaller, Koch & Koch (1987, J. Finance, 1984-85 minute data); Stoll & Whaley (1990, JFQA) | futures lead 20-45 min; index rarely leads futures > 1 min (1984-85); ~5 min in 5-min data | strong (historical) |
| L4 | ES order-flow shocks dissipate within about a second | Takahashi (2025), arXiv 2508.06788 | SVAR at 1-s frequency per 15-min interval | moderate |
| L5 | Lagged cross-asset order-flow imbalance forecasts decay rapidly | Cont, Cucuringu & Zhang (2021), arXiv 2112.13213 | short-horizon only | moderate |
| L6 | Extreme order-flow imbalance accompanies *pinned* prices, not large returns | Patzelt & Bouchaud (2017), arXiv 1706.04163 | arc-shaped probability of mid-price change vs order-sign bias, all intraday scales | moderate (mechanism for "TICK extremes do not mean much") |
| L7 | Intraday ES/NQ returns are not forecastable by generic models | Upadhyay (2026), arXiv 2611.12141 (pre-registered) | 0 of 160 model × representation × horizon × market cells beat no-change at 5-120 min; SPA p = 1.000 | moderate (context: the bar is no-change) |
| L8 | Contrarian sentiment (VIX, put/call, TRIN) forecasts S&P futures over 10-30 days | Simon & Wiggins (2001), J. Futures Markets 21(5) 447-462 (as indexed on RePEc), 1989-1999 | "frequently statistically and economically significant"; out-of-sample: buying when fear indicators were high improved profits and risk-adjusted profits | moderate (old sample, daily horizon) |
| L9 | Sentiment measures (A/D, put/call, ARMS among them) correlate with contemporaneous returns but **do not predict near-term returns** | Brown & Cliff (2004), J. Empirical Finance 11 1-27 | "little evidence" of short-run predictability; not profitable as a trading signal | strong |
| L10 | Put/call and A/D ratios are **caused by** past returns, not the reverse | Wang, Keswani & Taylor (2006), IJF 22 109-123 | Granger: returns → sentiment; earlier sentiment→volatility results overstated | strong |
| L11 | Open-buy put/call from non-public data predicts single-stock returns | Pan & Poteshman (2006), RFS 19(3) 871-908 | low-P/C stocks beat high-P/C by > 40 bp next day, > 1% next week; source is non-public information | strong, but not reproducible from public P/C |
| L12 | 90% days mark panic bottoms; isolated ones mean little | Desmond (2002) Dow Award paper | 69 years (1933-2002) NYSE; qualitative frequencies | moderate (practitioner research) |
| L13 | Hindenburg Omen (breadth divergence at highs) | Fisher Investments review; SentimenTrader | 7 of 28 pre-2013 signals "accurate"; creator: false ~75% of the time; definitions revised repeatedly | weak (negative) |
| L14 | Cumulative / adjusted TICK and forward returns (SPY) | Steenbarger TraderFeed 2005-2008 | adjusted TICK < −600 → next day −0.13% (34 up / 40 down) vs +0.07%; TICK ≤ −1000 on 108 of 775 sessions (2003-06), next day SPY +0.15% (64 up / 44 down) vs +0.06% average, but sessions with heavy selling and no offsetting buying TICK carried weakness into the next day (subnormal returns); cumulative line > +4000 → negative 5-10 days out; 4-day average < −500 → next 4 days +0.48%; author: "correlational data only" | weak (small n, unreplicated) |
| L15 | Many −1000 prints → bounce | thetrading.tools (5-min TICK bars since 1997, stats 2010+) | ≥ 10 prints of −1000 in a session → SPY +0.65% next 5 sessions vs +0.25% all days; "base rates, not signals", overlapping windows | weak |
| L16 | Closing-TICK oscillator lows → 2-3-day bounce | Quantifiable Edges (2012) | "strong propensity to bounce" | weak |
| L17 | TRIN > 1 three days in an uptrend → SPY mean reversion | Connors (book; vendor summary) | 72-76% winners, 90 trades, 12 years | weak-moderate (daily) |
| L18 | Stock correlations rise through the trading day; open is idiosyncratic | Allez & Bouchaud (2010), arXiv 1009.4785 | early hours dominated by idiosyncratic/sector effects | moderate (relevant to "ADD by 10:00") |

**Net of the literature for the DOL problem.** Internals are contemporaneous/lagging descriptions of order flow at the
bar scale the engine uses (1-60 minutes); the documented predictive content is either sub-5-minute, multi-day
contrarian, or based on non-public data. Practitioner statistics are small-sample and mostly daily-horizon.

### 2.2 Our dataset and the timestamp artefact [T]
- **Source.** The git history of a public dashboard repository (`hbout56-arsenal/arsenal-dashboard-public`, file
  `internals_snapshot.json`, 26,481 commits, 2026-06-29 → 2026-11-12). Each commit holds the latest rows of a live IQFeed
  internals log: NYSE TICK, TRIN, NYSE adv/dec/total, up/down/total volume, ADD, VOLD, S&P 500 adv/dec (ADSPD), ES, NQ, YM,
  SOX, VIX. Extracted with `extract.py` (26,902 unique rows at ~31-s spacing). Untrusted third-party data, used only for
  local statistics; not redistributed.
- **Coverage.** 38 sessions after removing a holiday (2026-07-03, frozen values) and fragmentary days; 33-37 full sessions
  per test. VIX 14.8-28.0. Calm-to-moderate regime only.
- **Timestamp artefact.** Cross-correlation of 1-minute changes (`chk_lag.py`, `chk_lag2.py`):
  - raw labels: corr(ΔADD(t), ΔES(t + lag)) ≈ 0 at lag 0 and peaks at **+10 min (+0.30)**; TICK level likewise
    (+0.30 at +10 min); ES vs NQ/YM peak at 0 (+0.86/+0.71).
  - fine scan (15-s grid): ES lags internals by **585 s**; VIX lags ES by 345 s, i.e. VIX lags internals by **930 s**.
    Consistent with a 10-minute-delayed CME feed and a 15-minute-delayed Cboe index feed beside real-time internals.
  - after re-timing (`int_common.load_rows(align=True)`: ES/NQ/YM − 585 s, VIX − 930 s, 30-s grid, carry-forward ≤ 2 min)
    the peaks sit at lag 0: ΔADD +0.36, ΔADSPD +0.23, TICK +0.32 (TICK also correlates +0.05…+0.22 with *past* ES changes:
    it lags futures).
  - **Effect on conclusions** (raw → aligned): forward-return coefficient of ΔADD(15) on the next 5-min ES return
    +0.337 SD (t +14.3) → −0.009 (t −0.4); race residual correlation of TICK +0.128 [+0.014, +0.232] → +0.050
    [−0.074, +0.160]. All raw-label outputs are kept as `out_*_RAWLABELS_artefact.txt` for audit.
- **Contemporaneous 5-min correlations with ΔES (aligned):** ΔADD +0.52, ΔVOLD +0.46, TICK mean +0.41, ΔADSPD +0.33,
  ΔlogTRIN −0.19, ΔVIX −0.77.

### 2.3 T1 · Day type and C1/C2 at the day level (`t1_daytype.py`, `t1b_pdhl.py`; n = 33 sessions) [T]
| Measure at the cut | 10:00 | 10:30 |
|---|---|---|
| Spearman ρ of \|ADD\| with trend score \|C−O\|/(H−L) | −0.06 (p .75) | −0.05 (p .78) |
| \|ADSPD\| | −0.12 | −0.00 |
| \|VOLD ratio\| | +0.03 | +0.13 |
| \|TICK mean since 09:30\| | −0.05 | −0.01 |
| \|TRIN − 1\| | **−0.47 (p .005)** (opposite of expectation; 1 of 12 tests, Bonferroni p ≈ .06) | −0.11 |
| \|ES move since open\| / OR range | **+0.42 (p .015)** | **+0.51 (p .003)** (partly mechanical) |
| Sign accuracy for rest-of-day return: ADD / VOLD / TICK / ADSPD / price | 0.58 / 0.58 / 0.55 / 0.39 / 0.42 | 0.52 / 0.55 / 0.52 / 0.45 / 0.33 |
| OR extreme on the ADD side taken after the cut / opposite taken | 0.79 / 0.58 | 0.64 / 0.48 |
| same, using the **price** sign | 0.76 / 0.61 | 0.64 / 0.48 |
| Both OR sides taken after the cut (base) | 0.39 | 0.18 |
| Both sides taken, top vs bottom \|ADD\| tercile | 0.55 vs 0.18 (Fisher p .18) — opposite to C2 | 0.18 vs 0.00 (p .48) |
| Untouched RTH PDH/PDL taken after cut: ADD side vs against | 0.33 (n 18) vs 0.19 (n 27) | 0.20 (n 15) vs 0.12 (n 25) |
| same with price side | 0.30 vs 0.18 | 0.22 vs 0.09 |
| same with ADSPD side | 0.18 vs 0.30 | 0.06 vs 0.22 |
Trend-day share (score ≥ 0.6): 26%. Reading: breadth adds nothing over the price move by the cut; samples are small.

### 2.4 T2 · Which side first (`t2_race.py`, `t2b_buckets.py`) [T]
- **Design.** At each bar close 10:00-15:00 ET, nearest unswept pool above and below (today's confirmed 2-bar pivots plus
  the session high/low), strict trade-through, first touch. Baseline logit offset = log(b/a) (the engine's `f_race`
  geometry). Features over 30 min: momentum (ES return / σ), ΔADD, ΔADSPD, ADD level, TICK mean, ΔVIX, NQ−ES return,
  ΔVOLD, log TRIN. Leave-one-day-out logistic; day-cluster bootstrap.
- **5-min bars:** n = 1,571 events, 35 days, P(up first) 0.489 vs geometry 0.522.
  - Residual correlations (y − p_geo), 95% day-bootstrap CI: momentum +0.000 [−0.067, +0.060]; ΔADD −0.011
    [−0.111, +0.089]; ΔADSPD +0.001 [−0.092, +0.081]; TICK +0.050 [−0.074, +0.160]; ΔVOLD −0.056 [−0.145, +0.027];
    TRIN −0.099 [−0.221, +0.031]; NQ−ES −0.069 [−0.153, +0.020]; ΔVIX +0.000 [−0.080, +0.079].
  - OOS log-loss vs geometry+momentum: +ΔADD −0.69% [−1.29, −0.23]; +ΔADSPD −0.50%; +ADD −0.96%; +TICK −0.47%
    [−1.84, +0.86]; +ΔVIX −0.32%; +NQ−ES +0.21% [−1.32, +1.54]; +ΔVOLD −0.08%; +TRIN +0.17% [−2.23, +2.46]; all
    features −1.23%. Geometry alone beats every fitted model (fitted intercepts add noise across days).
  - Terciles (excess up-first over geometry, low / mid / high): TICK −3.4 / −4.4 / −1.9 pp; ΔADD −0.3 / −8.5 / −0.9;
    ΔADSPD −2.3 / −3.7 / −3.7; TRIN −2.0 / +0.6 / −8.2; momentum −2.2 / −4.2 / −3.2. Flat across terciles (the common
    negative offset is the sample's down-drift). "Internals up while price momentum down" −4.9 pp (n 120), "internals
    down while price up" −3.9 pp (n 151): no divergence effect.
- **15-min bars:** n = 429; TICK +0.094 [−0.048, +0.206]; TRIN −0.169 [−0.372, +0.058]; NQ−ES −0.098; ΔADD +0.019.
  Same verdict.

### 2.5 T3 · Fixed-horizon forward returns (`t3_fwd.py`; 1-min grid, n ≈ 10.6k minute observations, 36 days) [T]
Coefficient in SD of the forward return per SD of the feature, controlling for momentum, day-clustered t; skip 0 or
2 minutes (the skip rules out residual sub-minute misalignment):
| Lookback 30 min | h = 5 | h = 15 | h = 30 | h = 60 |
|---|---|---|---|---|
| ΔADD (skip 2) | +0.014 (+0.5) | +0.013 (+0.3) | +0.003 (+0.1) | +0.019 (+0.4) |
| TICK mean (skip 2) | +0.015 (+0.8) | +0.038 (+1.2) | +0.045 (+1.0) | +0.075 (+1.5) |
| ΔADSPD (skip 2) | +0.024 (+1.0) | +0.039 (+1.2) | +0.025 (+0.6) | +0.031 (+0.7) |
| log TRIN (skip 2) | −0.013 (−0.9) | −0.032 (−1.3) | −0.050 (−1.5) | −0.082 (−1.8) |
| ΔVIX (skip 2) | −0.004 (−0.2) | −0.030 (−0.8) | −0.009 (−0.2) | +0.042 (+0.5) |
| momentum alone | +0.030 (+1.7) | +0.042 (+1.2) | +0.040 (+0.9) | +0.058 (+1.1) |
The 15-minute lookback gives the same picture. TICK (+) and TRIN (−) lean in the "breadth persists" direction at 30-60
minutes, never reaching |t| = 2.

### 2.6 T4 · Sweeps: TICK extremes, breadth divergence, hold vs reject (`t4_sweeps.py`) [T]
- **Design.** A 5-min bar (10:00-15:25) trades through the outermost of the pools formed before it (2-bar pivots unswept
  until then, or the session extreme). Race from the sweep bar's close: continuation = +u beyond the swept level,
  failure = −u back through it, u = 2 × mean 5-min range of the last hour. Geometry baseline = position of the close
  between the two barriers.
- n = 542 sweeps, 511 decided, 37 days. Continuation first 0.599 vs geometry 0.551: **excess +4.8 pp** (the small
  continuation lean siblings also found).
| Context at the sweep bar | n | P(cont.) | geometry | excess |
|---|---|---|---|---|
| bar closes beyond the level (engine "hold") | 331 | 0.665 | 0.635 | +3.0 pp |
| bar closes back inside (engine "reject") | 180 | 0.478 | 0.397 | +8.1 pp |
| TICK in sweep direction in top quintile (≥ +556 snapshot) | 103 | 0.592 | 0.570 | +2.2 pp |
| TICK not extreme | 408 | 0.600 | 0.546 | +5.4 pp |
| TICK extreme & reject | 32 | 0.375 | 0.347 | +2.8 pp |
| ADD confirms (≥ its value at the swept extreme) | 333 | 0.616 | 0.586 | +2.9 pp |
| ADD diverges | 178 | 0.567 | 0.485 | +8.2 pp |
| session extreme & ADD diverges | 93 | 0.656 | 0.473 | +18.3 pp |
| session extreme & ADD confirms | 205 | 0.644 | 0.607 | +3.7 pp |
| ADD sign with the sweep | 309 | 0.654 | 0.558 | +9.6 pp |
| ADD sign against the sweep | 202 | 0.515 | 0.540 | −2.5 pp |
Differences of geometry-excess (day bootstrap): TICK extreme − not −3.2 pp [−13.7, +7.8]; ADD confirms − diverges
−5.3 pp [−12.2, +2.4]; ADSPD confirms − diverges −2.4 pp [−10.3, +5.0]; hold − reject −5.1 pp [−14.0, +3.9]; ADD sign
with − against +12.1 pp [−3.2, +26.5]; momentum with − against +0.5 pp.
Reading: no TICK exhaustion signature; no reversal on breadth divergence (the opposite lean); after geometry, the
engine's hold/reject split carries no information (consistent with the sibling finding that the raid → D mapping is
wrong). The only lean is "ADD on the side of the sweep" (ns).

### 2.7 T5 · Internals as the regime state for C1/C2 (`t5_regime.py`; n = 1,805 bars, 37 days) [T]
- **C1** (pool on the breadth side taken first, excess over geometry): ADD −1.6 pp [−7.9, +5.2], strong-breadth tercile
  −2.8; ADSPD −3.7, strong −8.7 [−18.5, +2.0]; TICK +0.1, strong +4.2 [−3.6, +11.8]. **Price trend** (60-min direction;
  terciles of 60-min efficiency ratio): +4.0 pp overall [−0.5, +8.3], strong tercile **+5.9 pp [+0.4, +11.0]**.
- **C2** (both nearest pools raided within 60 min; base 9.0%), excess after a LOO logistic on distances (in units of the
  recent 5-min range), clock (midday / late) and volatility state:
  - |ADD| terciles −1.8 / +1.3 / +0.6 pp; |ADSPD| +0.6 / +0.1 / −0.6; |ER| 0.0 / −0.6 / +0.4 (all CIs include 0).
  - **|TICK 30-min mean| weak tercile (≤ ~64) +6.2 pp [+1.1, +12.5]**, mid −3.2 [−5.6, −0.9], strong −3.4 [−6.5, +0.2].
  - As a continuous feature: LOO log-loss +2.3% [−3.2, +6.7] (not significant).
  - |TICK| is uncorrelated with the volatility state (r 0.06) and weakly with the farther pool's distance (r 0.17).
- Thresholds from this sample (10:00-15:00 ET): |TICK 30-min mean| terciles 64 / 145 (median 101; no strong time-of-day
  profile: hourly medians 89-122); |ADD| terciles 352 / 729.

### 2.8 Evidence grades
| Concept / claim | Grade | Why |
|---|---|---|
| Internals describe concurrent order flow (corr with ΔES +0.3 to +0.5) | strong | L1, T2.2 |
| Internals predict which pool is hit first / next 5-60-min return beyond price | none (null) | T2.4, T2.5; L2, L7, L9 |
| TICK extreme at a level = exhaustion / stop-run | none (null) | T2.6; L6 |
| Breadth divergence at a new high/low = reversal (SMT-like) | none (null, opposite lean) | T2.6; L13 |
| ADD/VOLD by 10:00-10:30 classifies trend vs rotational day | none at n 33 (weak practitioner support) | T2.3; P |
| C1 conditioned on breadth | none | T2.7 |
| C2 conditioned on a balanced TICK tape | weak | T2.7 (one surviving cell; multiple tests) |
| Multi-day contrarian sentiment (P/C, TRIN, 90% days, many −1000 prints) | weak-moderate | L8, L12, L14-L17 vs L9-L10 |
| Program-trading premium as a bar-scale predictor | none today | L3, L4 |
| Intraday VIX direction as a draw input | none (null) | T2.4, T2.5 |
| Megacap leadership (NQ−ES proxy) | none (null) | T2.4; real generals untested |
| Data delay creates spurious internals edges | strong | T2.2; TradingView CME 10-min delay statement |

---

## 3. Engine gap analysis (line refs in `baseline_v2.pine`)
| Concept | Status | Engine lines | What the engine does / differs |
|---|---|---|---|
| NYSE/Nasdaq/Dow TICK, cumulative TICK | missing (correctly) | 923-925, 939, 981-982 are the only requests; all on `syminfo.tickerid` | No cross-symbol data. Our tests give no reason to add TICK to the forecast; only to the ledger (INT-2/4). |
| ADD, VOLD, TRIN, %>VWAP | missing (correctly) | — | Same. |
| Put/call ratios | missing (correctly for intraday) | — | Daily contrarian context at most (INT-8, ledger only). |
| Premium vs fair value | missing (correctly) | — | Not a bar-scale predictor today. |
| Megacap generals | missing | — | Sibling SMT module (smt_inter) covers one correlated symbol; generals untested (INT-7). |
| Intraday VIX | missing | — | VIX level as a variance input is the sibling's X1-1; VIX direction null here. |
| Trend vs rotational day / regime state | partial | D vector 1891-1898 (`sV` structure 1892, `mV` displacement 1893, `liqEvt` raids 1535/1579-1582); killzone hysteresis 970-976 | No day-type or efficiency state. D components test null (quant_regime). Breadth does not fix that (T2.7). Sibling REG-2 adds the E/V axes; INT-2 adds a breadth axis for the ledger only. |
| C1 (opposite liquidity holds in trends) | partial/wrong | D-first eligibility 1975, counter-draw fallback 2000-2004, `ctrMult` 685-686, Draw pillar 684 | Encoded as an assumption; not measured. Breadth-conditioned C1 is null; price-trend C1 +5.9 pp in the strongest tercile. |
| C2 (both sides raided in ranges) | missing | `f_invalidation` 1343-1364; `f_raceAdj` 1367-1371 | The race readout does not model "both pools raided". REG-5 (sibling) adds a stop-run readout; the balanced-TICK cell (INT-2/3) can grade a breadth condition for it. |
| TICK extreme at a level | missing | sweep loop 1559-1589 | Correctly absent; null in T4. INT-4 grades it per chart. |
| Breadth divergence at new HOD/LOD | missing | — | Correctly absent; null/opposite in T4. |
| Internals confirming hold/reject | wrong mapping (bar close) | `evt` 1581, `liqEvt` 1582, half-life 1535 | Engine maps a close beyond = continuation, close inside = reversal. After geometry, hold vs reject carries no information (T4, −5.1 pp ns), agreeing with siblings. Internals do not rescue it. |
| Bias table with an internals row | missing | Clean 2293-2307, Terminal 2310-2343, table size 2290 (4 × 22) | INT-5 (optional row, off by default). |
| Data-health: delayed feeds, RTH gaps, invalid symbols | missing | `tfWarn` 1017 is the only data warning | No delayed-feed detection; no cross-symbol freshness logic (needed for any USI request). INT-1/INT-6. |
| Auto-off outside US equity indices | n/a | — | INT-1 applicability rule via `syminfo.type`, `syminfo.root`, `syminfo.country`. |
| Ledger able to measure an internals feature | present (infrastructure) | `Trial` 375-395, `f_openTrial` 1426-1431, `f_step` 1434-1459, `f_book` 1461-1499, stats arrays 1064-1079, cluster variance 1076-1077 | Extend with a breadth class per trial (INT-2) and a sweep-context store (INT-4); sibling CAL-3 shadow probes multiply the sample. |

---

## 4. Proposals (spec level; best first)

Order of value (best first): INT-1, INT-2, INT-6, INT-3, INT-4, INT-5, INT-7, INT-8 (IDs are stable labels).

Principles: nothing here changes scoring or selection by default; every internals feature is US-index-only, off unless
enabled, measured by the ledger, and protected by a freshness guard. All inputs `display = display.none` (overhaul legend
finding). Request budget: baseline uses 7 unique `request.*()` calls (923, 924, 925, 939, 981, 982 + the lower-TF call);
INT-1 adds 3 (TICK, breadth, TRIN), INT-7 up to 7, INT-8 1. The cap is "40 unique calls to the functions in the
`request.*()` namespace, or up to 64 ... on the Ultimate plan" [D: writing_scripts/limitations.md 206]. Tuple elements stay
far under the documented limit (an example with 128 elements errors; limitations.md ~280-306).

### INT-1 (P2, M) · Optional US-index internals feed with data-health guards (foundation)
**Why.** Every other INT item needs internals that are (a) only active where they mean something, (b) only used when
their bar time matches the chart's, (c) RTH-only, (d) safe when a symbol is unavailable. Our T2.2 shows (b) is not
optional: delayed CME data on TradingView (10 min for free users) plus real-time internals reproduces a t = 14 fake edge on
realtime bars.

**Inputs** (new `const string G_INT = "Market Internals (US indices)"`):
```pine
string intMode = input.string("Off", "Market Internals", options = ["Off", "Auto", "On"], group = G_INT, display = display.none,
  tooltip = "US equity index futures, ETFs and large caps only. Auto = on for ES/NQ/YM/RTY (and micros), SPX/NDX/DJI/RUT, US stocks/ETFs; intraday charts up to 1H. Internals describe the tape; tests found no forecasting edge beyond price, so they only feed the accuracy ledger unless it proves otherwise on this chart.")
string intUni  = input.string("Auto", "Universe", options = ["Auto", "NYSE", "Nasdaq", "Dow", "US total"], group = G_INT, display = display.none)
string intBrd  = input.string("ADD", "Breadth Source", options = ["ADD", "% Above VWAP", "VOLD"], group = G_INT, display = display.none)
float  balThr  = input.float(65, "Balanced TICK |30-min mean| ≤", minval = 0, step = 5, group = G_INT, display = display.none)
float  oneThr  = input.float(145, "One-sided TICK |30-min mean| ≥", minval = 0, step = 5, group = G_INT, display = display.none)
```
(Defaults = terciles of |30-min TICK mean| in our NYSE sample, §2.7. For Nasdaq/Dow TICK the scale differs; INT-2 can
self-calibrate with a rolling tercile if wanted.)

**Applicability and universe** (global scope, after the mode block ~86):
```pine
string rtI    = syminfo.root
bool   idxFut = syminfo.type == "futures" and (rtI == "ES" or rtI == "MES" or rtI == "NQ" or rtI == "MNQ" or rtI == "YM" or rtI == "MYM" or rtI == "RTY" or rtI == "M2K")
bool   usEq   = syminfo.country == "US" and (syminfo.type == "stock" or syminfo.type == "fund" or syminfo.type == "index")
bool   intOK  = timeframe.isintraday and timeframe.in_seconds() <= 3600 and (intMode == "On" or (intMode == "Auto" and (idxFut or usEq)))
string tkr    = syminfo.ticker
string uni    = intUni != "Auto" ? intUni : (rtI == "NQ" or rtI == "MNQ" or tkr == "QQQ" or tkr == "NDX") ? "Nasdaq" : (rtI == "YM" or rtI == "MYM" or tkr == "DIA" or tkr == "DJI") ? "Dow" : "NYSE"
string sx     = uni == "Nasdaq" ? ".NQ" : uni == "Dow" ? ".DJ" : uni == "US total" ? ".US" : ".NY"
string symTk  = "USI:TICK" + sx
string symBr  = intBrd == "% Above VWAP" ? "USI:PCTABOVEVWAP" + sx : intBrd == "VOLD" ? "USI:ADVDECV" + sx : "USI:ADVDEC" + sx
string symTr  = "USI:TRIN" + sx
```
Doc basis: `syminfo.type` and `syminfo.country` are simple strings [D: reference/syminfo.md 829-833, 15-19]. Ticker names
come from TradingView's USI list (§1); classic aliases (`USI:TICK`, `USI:ADD`, `USI:VOLD`, `USI:TICKQ`, `USI:ADDQ`,
`USI:VOLDQ`, `USI:TICKI`) can be offered as a fallback input. Verify on a live chart before release.

**Requests** (SERIES section, after 982; 3 unique calls):
```pine
f_intReq(string sym) =>
    request.security(sym, timeframe.period, [close[1], high[1], low[1], time[1]], lookahead = barmerge.lookahead_on, ignore_invalid_symbol = true)
[tkC, tkH, tkL, tkT] = f_intReq(intOK ? symTk : syminfo.tickerid)
[brC, brH, brL, brT] = f_intReq(intOK ? symBr : syminfo.tickerid)
[trC, trH, trL, trT] = f_intReq(intOK ? symTr : syminfo.tickerid)
```
- `ignore_invalid_symbol`: "if `true`, the function will return `na` and execution will continue" [D: reference/request.md 215].
- `timeframe.period` is never below the chart TF, so the engine's `f_tfSafe` rule holds. `[1]` + `lookahead_on` at the
  chart TF returns the previous internals bar on historical bars, the engine's non-repainting idiom.
- Realtime caveat: "lookahead ... Has no effect on realtime values" [D: request.md 214] and "the chart's data feeds and
  feeds requested from providers by the script are managed by independent, concurrent processes" [D:
  other_timeframes_and_data.md 492]; realtime data "may be delayed, depending on your account type" [D: same file 479].
  Hence the freshness guard below.

**Freshness guard** (global):
```pine
int  tfMsI = timeframe.in_seconds() * 1000
bool inRTH = not na(time(timeframe.period, "0930-1600", "America/New_York"))
f_fresh(int t) =>
    not na(t) and t < time and time - t <= 2 * tfMsI
bool tkOK = intOK and inRTH and f_fresh(tkT)
bool brOK = intOK and inRTH and f_fresh(brT)
bool trOK = intOK and inRTH and f_fresh(trT)
```
- Historical, aligned: `t = time − tfMs` → fresh.
- 09:30 bar: `[1]` is yesterday's last bar → stale → excluded. Overnight ES bars: stale → excluded.
- Delayed chart + real-time internals on realtime bars: the internals bar time is ahead (`t ≥ time`) → excluded
  (prevents the T2.2 look-ahead). Internals more delayed than the chart: stale → excluded.

**Derived state** (confirmed bars, just before step 14 ~1891; O(30) per bar):
```pine
int nI = math.max(1, int(math.round(1800.0 / chartS)))     // 30 minutes of chart bars
var array<float> tkBuf = array.new<float>()
var float tick30 = na
if barstate.isconfirmed
    tkBuf.push(tkOK ? tkC : na)
    if tkBuf.size() > nI
        tkBuf.shift()
    float s = 0.0
    int   k = 0
    for v in tkBuf
        if not na(v)
            s += v
            k += 1
    tick30 := k >= math.max(1, int(0.6 * nI)) ? s / k : na
int brState = na(tick30) ? -9 : math.abs(tick30) <= balThr ? 0 : math.abs(tick30) >= oneThr ? 2 * int(math.sign(tick30)) : int(math.sign(tick30))
```
`brState`: −9 n/a, 0 balanced, ±1 mild, ±2 one-sided. Breadth level (`brC`) and TRIN (`trC`) are kept for display and
INT-4. No use in `evaluate`, `drawD` or selection.

**Expected value.** Enables measurement on the user's chart; prevents the most likely way an internals feature would
mislead (feed delay). **Evidence:** infrastructure (delay finding strong). **Risk:** symbol names change; history length
of USI symbols on TV unknown; realtime races between feeds; small extra load. **Effort:** M (~70 lines).

### INT-2 (P2, S-M) · Breadth-state ledger cells: C1/C2 measured on the user's chart
**Why.** Practitioners believe C1/C2 depend on breadth; our sample says C1 does not and C2 maybe does with a balanced
TICK tape (+6.2 pp). The ledger can settle it per chart without changing a single target.

**Algorithm.**
1. `Trial` (375-395) gains `int bCls = -9`. In `f_openTrial` (1426-1431):
   `bCls := brState == -9 ? -9 : brState == 0 ? 0 : math.abs(brState) == 1 ? 3 : (math.sign(brState) == lv.side ? 1 : 2)`
   (0 BALANCED · 1 ONE-SIDED WITH target · 2 ONE-SIDED AGAINST · 3 MILD).
2. State (after 1079): `var array<float> bSt = array.new<float>(4 * 5, 0.0)` = per class [n, k, Σ pBase, Σ pBase(1 − pBase),
   Σ race wins] and a cluster block per class as in `cluSt` (1076-1077).
3. `f_book` (1461-1499): if `t.bCls >= 0`, accumulate `y`, `t.pBase` and the race outcome into the class block.
4. Readout (Terminal, Full accuracy view, after the per-family rows): `BREADTH  BAL 41% vs 37% · n 88 | WITH 52% vs 46% ·
   n 60 | AGAINST 38% vs 44% · n 41`, with a verdict only when n ≥ 100 per compared class and the cluster-robust z ≥ 2.5
   (peeking-safe rule of sibling CAL-2). C1 test = WITH vs AGAINST excess; C2 test = BAL stop-run excess (step 5).
5. When sibling REG-5's stop-run grading exists, store `bCls` with each stop-run probe and show `STOP-RUN cal by breadth:
   BAL +x pp (n) / other`. When sibling CAL-3 shadow probes exist, add `bCls` to `Probe` for a 2-3× larger sample.
6. Sibling REG-2's E/V axes and this B axis are reported side by side, so a trader sees whether price efficiency or breadth
   is the informative regime on this chart (our data: efficiency).

**Pine notes.** All in confirmed-bar code; O(1) per booking. **Expected value:** answers "does breadth matter on my
chart?" with numbers; guards the engine against adopting folklore. **Evidence:** weak (T2.7). **Risk:** RTH-only trials
reduce n (only trials opened 09:30-16:00 are classed); multiple-comparison noise across 4 classes (verdict gate handles
it). **Effort:** S-M (~45 lines).

### INT-6 (P2, S) · Chart-wide delayed-feed detector
**Why.** TradingView states "All of CME Group's data is available on TradingView for free in 10-minute-delay mode"
(tradingview.com/cme). On a delayed chart the live PoT, the sweep alert and every realtime bar are 10 minutes late, and
any cross-symbol request can be out of sync (T2.2). Traders should see it.

**Spec.** Global scope:
```pine
bool feedDelayed = barstate.isrealtime and timenow > time_close + 90000
var bool everDelayed = false
everDelayed := everDelayed or feedDelayed
```
`timenow` = "Current time in UNIX format" [D: reference/time.md 127-131]. On a live feed the developing bar's `time_close`
is in the future, so the test is false; on a 10-minute-delayed feed it is ~10 minutes in the past. Show `⚠ DELAYED FEED`
(Clean row like `tfWarn`, Terminal header cell), append `(delayed feed)` to the sweep alert text, and let INT-1 treat
internals as unusable on realtime bars while `feedDelayed`. Optional: flag ledger trials opened on delayed realtime bars.

**Evidence:** strong for the problem (TradingView statement; our 585-s measurement). **Risk:** sparse ticks on illiquid
symbols can trip the 90-s margin (scale the margin by the chart TF: `max(90000, tfMs)`). **Effort:** S (~15 lines).

### INT-3 (P3, S) · Ledger-gated rotation adjustment of the stop-run readout
**Why.** If INT-2 confirms the C2 cell on a chart (balanced tape → more two-sided raids), the STOP-RUN readout (sibling
REG-5: probability that the invalidation beyond the opposing pool is traded within H) should reflect it there, and only
there. `WIN≤H` (`f_raceAdj` 1367-1371) is left alone: "both sides raided" says nothing about which side is first.

**Algorithm.**
1. Gate (sibling CAL-11 style, prequential): enable only when the BAL class has ≥ 100 graded stop-run probes (effective,
   after the 0.6·H overlap discount the engine already uses in `f_empPoT` 1282-1283) and the cumulative out-of-sample
   log score of the adjusted readout beats the unadjusted one.
2. Shift: `p̄` = mean model stop-run probability in BAL, `k`/`n` = BAL hits/probes;
   `δ = clamp(logit((k + 30·p̄) / (n + 30)) − logit(p̄), −0.5, +0.5)`.
3. For the active target while `brState == 0`: `pStop' = sigm(logit(pStop) + δ)`; HUD `STOP-RUN 34% (bal +6)`; tooltip
   gives n and the excess.

**Evidence:** weak. **Risk:** per-chart overfitting; mitigated by the gate and the clamp. **Effort:** S (~25 lines).
Depends on INT-1, INT-2, REG-5.

### INT-4 (P3, S) · Sweep-context grading (TICK extreme, breadth divergence, breadth side) without feeding D
**Why.** The most common internals claims are about sweeps. T4 says they carry nothing beyond geometry; a per-chart cell
lets the user see that (or the opposite) instead of the engine assuming it, and keeps `liqEvt` free of them.

**Algorithm.**
1. `Level` gains `float brAt = na` (breadth level at creation; set in `f_newLevel` callers when `brOK`).
2. In step 3 (1579-1582), when a liquidity level is swept on this bar and `tkOK and brOK`:
   `tkX = lv.side == 1 ? tkH >= tkExt : tkL <= -tkExt` (input `tkExt`, default 800 for NYSE 1-min highs/lows),
   `div = not na(lv.brAt) and (lv.side == 1 ? brC < lv.brAt : brC > lv.brAt)`, `withB = math.sign(brC) == lv.side`.
   Push `SweepCtx(side, level, bar, u = 2 × ATR-scaled 5-bar range, ctx bits)` into a ≤ 64-element array.
3. Each confirmed bar, resolve open contexts by the race of T4: continuation `level + side·u` vs failure
   `level − side·u` (strict; same-bar both = drop), geometry `p_geo` from the close at the sweep bar; expire after H.
4. Stats per context bit: [n, k, Σ p_geo]. Full view row `SWEEP CTX  TICK-X +2.2pp n54 · DIV +8.2pp n71 · WITH +9.6pp n90`.
5. Sweep alert (1509, 2084): append `· TICK +1012 · breadth diverging` when known (descriptive only).

**Evidence:** none for an effect (T4 nulls). **Risk:** traders may read the tags as signals; tooltip states the
measured numbers. **Effort:** S (~50 lines).

### INT-5 (P3, S) · Optional "Breadth" row in the bias table and one HUD line
**Why.** Traders who use internals want them in view; the Clean style must stay uncluttered.

**Spec.**
- `bool showBrRow = input.bool(false, "Breadth Row in Bias Table", group = G_INT, display = display.none)`.
- Clean table (2293-2307): when `showBrRow and intOK`, row 4 = `Breadth | ▲ ONE-SIDED` (bias green) / `▼ ONE-SIDED`
  (bias red) / `BALANCED` (neutral) / `RTH ONLY` (dim) from `brState`; move the `⚠ CHART TF` row (2305-2306) to row 5.
- Terminal (2310-2343): after the DRAW row, `BREADTH  TICK30 +172  ADD +840  TRIN 0.82  1-SIDED ▲`, plus the INT-2 verdict
  when available (`ledger: no effect`). Check the 22-row table capacity (2290) in Full view; raise to 24 if needed.
- Values are the `[1]` (previous bar) series; an optional live readout would need a second, `lookahead_off` request
  per symbol (deliberately live like PoT); not recommended for the budget.

**Evidence:** n/a (display). **Risk:** clutter (off by default), stale values outside RTH (shown as RTH ONLY).
**Effort:** S (~25 lines).

### INT-7 (P3, M) · NQ "generals" breadth (display and ledger cell only)
**Why.** NQ's top-7 names are ~35% of the capped index (Nasdaq, 2026-06-30). Traders ask whether the generals confirm an
NQ high. Untested here (our NQ−ES proxy: −0.069 [−0.153, +0.020]).

**Spec.** Input `string genList = input.text_area("NASDAQ:NVDA,NASDAQ:MSFT,NASDAQ:AAPL,NASDAQ:AMZN,NASDAQ:GOOGL,NASDAQ:META,NASDAQ:AVGO", "Generals")`
(user-editable; index membership changes). Only when `uni == "Nasdaq" and intOK`. For each symbol (≤ 7 requests; dynamic
requests allow a loop, but all contexts must be requested on historical bars [D: other_timeframes_and_data.md 302]):
`request.security(sym, timeframe.period, [close[1] > ta.vwap[1] ? 1 : -1, time[1]], lookahead = barmerge.lookahead_on, ignore_invalid_symbol = true)`
with the same freshness guard. `gen = Σ votes` (−7…+7). Classes: ≥ +5 bid, ≤ −5 offered, else mixed → an extra ledger
class (as INT-2) and a Terminal cell `GENERALS +5/7`. No scoring use.

**Evidence:** none. **Risk:** 7 requests and load; ticker list maintenance. **Effort:** M.

### INT-8 (P3, S) · Daily put/call and closing-breadth context for Swing mode (ledger cell)
**Why.** The only internals with published forecasting power at the engine's swing horizons are multi-day contrarian
measures (L8; L12; L14-L17), contradicted by L9-L10. A ledger cell for Swing mode (W/D/4H, H spanning days) tests it.

**Spec.** `pcZ = request.security("USI:PCCE", "D", ((ta.sma(close, 10) - ta.sma(close, 252)) / ta.stdev(ta.sma(close, 10), 252))[1], lookahead = barmerge.lookahead_on, ignore_invalid_symbol = true)`;
classes FEAR (z ≥ +1.5), COMPLACENT (z ≤ −1.5), NORMAL; record in `Trial` like `bCls` when `modeIn == "Swing"`; Full view
row `P/C FEAR: long targets 61% vs 52% (n 40)`. Optional second input: closing VOLD ratio ≥ 9 (90% day) flags.

**Evidence:** weak-moderate (old, daily). **Risk:** small n on swing charts; P/C history on TV unverified. **Effort:** S.

### Not proposed (and why)
- **Internals in D (`drawD` 1894), the Draw pillar (684) or selection (1964-2035):** null after alignment (T2.4-T2.7);
  D components are already null (quant_regime REG-3).
- **TICK ±1000 fade or "exhaustion" flip of the target side:** null (T4 −3.2 pp); extreme imbalance co-occurs with pinned
  prices (L6).
- **Breadth-divergence (SMT-like) reversal at new HOD/LOD:** null with the opposite lean (T4).
- **10:00-10:30 ADD day-type classifier gating selection:** null at n 33; the price move by the cut is at least as
  informative; sibling REG-2's efficiency axis is the better regime input.
- **Program-trading premium vs fair value:** needs the cash index (Cboe/S&P feeds have their own delays on TV), rates and
  dividends; the futures-cash lead is now seconds (L3-L4).
- **ΔVIX as a draw input:** null (corr 0.000; forward |t| < 1). VIX level for variance: sibling X1-1.
- **Hindenburg Omen / 90% days as intraday inputs:** daily-to-monthly horizon, high false-positive rates (L12-L13).

---

## 5. Pine v6 feasibility notes (summary)
- **Tickers:** §1.1-1.7 (USI exchange; ".NY/.NQ/.US/.DJ" families plus classic aliases). Use `input.symbol` overrides and
  `ignore_invalid_symbol = true`.
- **Sessions:** USI internals exist 09:30-16:00 ET only. On 23-hour futures charts `gaps_off` carries the last RTH value
  overnight; the freshness guard (bar time within 2 chart bars, strictly before the chart bar) removes stale and
  future values. `gaps_on` alone is not enough (it does not catch a feed that is ahead).
- **Timeframe:** request at `timeframe.period` (chart TF ≤ 1H), never below the chart (engine's `f_tfSafe`, 564-565).
  On charts above 1H, internals are pointless for intraday regime features; auto-off.
- **[1] + lookahead_on vs live:** the `[1]` value (previous internals bar) is what the ledger and any gated logic use; a
  deliberately live display needs a separate `lookahead_off` request per symbol (doubling the requests), so INT-5 uses
  the `[1]` values with a "(prev bar)" note.
- **Delays and plans:** CME futures free = 10-minute delay (tradingview.com/cme); Cboe indices are commonly 15-minute
  delayed (our VIX lag 930 s); USI delay status on TV is not documented in what we could reach (ICE Data Services is the
  stated provider on TV symbol pages per a script description). INT-6 detects the chart's own delay.
- **Request budget:** baseline 7; INT-1 +3; INT-7 +7; INT-8 +1; siblings (SMT +1, implied vol +1-3) → ≤ 22 of 40.
- **Auto-off:** `syminfo.type` / `syminfo.root` / `syminfo.country` rule in INT-1; crypto, FX, commodities, non-US
  indices and daily+ charts never request USI data.
- **Clean style:** nothing visible by default; one optional table row.

---

## 6. Test inventory (all under `study/x1_int_tools`; run with `run.sh <script> [args]`, isolated Python with the local
wheels in `study/x1_tools/pylib`)
| Script | What | Output |
|---|---|---|
| `extract.py` | rebuild `x1_int_data/internals_rows.csv` from the repository history (`git cat-file --batch` on stdin) | 26,902 rows |
| `data_coverage.py` | per-day coverage of the raw rows | console |
| `chk_stale.py`, `chk_lag.py`, `chk_lag2.py` | staleness and the ES/VIX delay vs internals | §2.2 |
| `int_common.py` | loader with re-timing (`ES_DELAY_S = 585`, `VIX_DELAY_S = 930`), bars, LOO logistic, day bootstrap | — |
| `t0_desc.py` | distributions and contemporaneous correlations | `out_t0.txt` |
| `t1_daytype.py`, `t1b_pdhl.py` | day type, OR sides, PDH/PDL after the cut | `out_t1_aligned*.txt`, `out_t1b_aligned.txt` |
| `t2_race.py <min>`, `t2b_buckets.py <min>` | which side first (5/15-min) | `out_t2_*_aligned.txt`, `out_t2b_*_aligned.txt` |
| `t3_fwd.py` | forward returns, skip 0/2 min | `out_t3_aligned.txt` |
| `t4_sweeps.py` | sweeps: TICK extremes, divergence, hold/reject | `out_t4.txt` |
| `t5_regime.py` | C1/C2 with breadth vs price regime, controls | `out_t5.txt` |
| `t6_thr.py` | TICK / ADD tercile thresholds | console (§2.7) |
| `*_RAWLABELS_artefact.txt` | the same tests on unaligned labels (look-ahead artefact), kept for audit | — |

---

## 7. Sources
- Chordia, Roll & Subrahmanyam (2002), Order imbalance, liquidity, and market returns, JFE 65(1) 111-130: https://ideas.repec.org/a/eee/jfinec/v65y2002i1p111-130.html
- Chordia, Roll & Subrahmanyam (2005), Evidence on the speed of convergence to market efficiency, JFE 76(2) 271-292: https://ideas.repec.org/a/eee/jfinec/v76y2005i2p271-292.html ; CFA digest: https://rpc.cfainstitute.org/research/cfa-digest/2005/11/evidence-on-the-speed-of-convergence-to-market-efficiency-digest-summary
- Kawaller, Koch & Koch (1987) lead-lag, as cited in Sheng & Ma (2022), PMC9601484: https://pmc.ncbi.nlm.nih.gov/articles/PMC9601484/ ; Stoll & Whaley (1990), JFQA: https://cambridge.org/core/services/aop-cambridge-core/content/view/6C0C02141F02160D48AB9CA1FDFB2785/S0022109000007328a.pdf
- Takahashi (2025), arXiv 2508.06788: https://arxiv.org/abs/2508.06788
- Cont, Cucuringu & Zhang (2021), arXiv 2112.13213: https://arxiv.org/abs/2112.13213
- Patzelt & Bouchaud (2017), arXiv 1706.04163: https://arxiv.org/abs/1706.04163
- Allez & Bouchaud (2010), arXiv 1009.4785: https://arxiv.org/abs/1009.4785
- Upadhyay (2026), arXiv 2611.12141: https://arxiv.org/abs/2611.12141
- Simon & Wiggins (2001), S&P futures returns and contrary sentiment indicators, J. Futures Markets 21(5) 447-462: https://ideas.repec.org/a/wly/jfutmk/v21y2001i5p447-462.html
- Brown & Cliff (2004), Investor sentiment and the near-term stock market, JEF 11 1-27: https://ideas.repec.org/a/eee/empfin/v11y2004i1p1-27.html
- Wang, Keswani & Taylor (2006), IJF 22 109-123: https://eprints.lancs.ac.uk/id/eprint/44156
- Pan & Poteshman (2006), RFS 19(3) 871-908: https://www.nber.org/papers/w10925
- Desmond (2002), 2002 Dow Award paper (90% days): https://www.scribd.com/document/369653221/2002DowAward-pdf ; Quantifiable Edges on 90% days (2008): https://quantifiableedges.blogspot.com/2008/01/extremely-weak-breadth-and-possible-gap.html ; Schaeffer's (2015): https://www.schaeffersresearch.com/content/analysis/2015/07/09/wednesday-marked-yet-another-90-90-down-day
- Hindenburg Omen: https://fisherinvestments.com/en-us/marketminder/led-zeppelin ; https://sentimentrader.com/blog/ultimate-guide-to-the-hindenburg-omen
- Steenbarger (TraderFeed): https://traderfeed.blogspot.com/2006/09/cumulative-nyse-tick-valuable-measure.html ; https://traderfeed.blogspot.com/2006/03/weak-daily-tick-what-it-means.html ; https://traderfeed.blogspot.com/2005/12/nyse-tick-does-it-matter.html ; https://traderfeed.blogspot.com/2006/08/trading-with-nyse-tick-part-three.html?m=1 ; https://traderfeed.blogspot.com/2007/11/nyse-tick-and-intraday-market-movement.html ; https://traderfeed.blogspot.com/2020/04/how-can-you-identify-trend-day-in-stock.html?m=1 ; https://traderfeed.blogspot.com/2016/12/a-unique-measure-of-market-strength.html?m=1 ; https://traderfeed.blogspot.com/2009/03/nyse-advance-decline-line-identifying.html?m=0
- Raschke, Capturing Trend Days: https://www.traderslog.com/?p=823
- thetrading.tools NYSE TICK base rates: https://www.thetrading.tools/nyse-tick
- Quantifiable Edges TICK oscillator (2012): https://quantifiableedges.blogspot.com/2012/03
- Connors TRIN: https://tradingmarkets.com/?p=674135 ; https://quantifiedstrategies.substack.com/p/trin-arms-index-trading-strategy-a94
- NexusFi ADD / internals articles: https://nexusfi.com/a/indicators/add-nyse-advance-decline-line ; https://nexusfi.com/a/strategies/trading-with-market-internals
- LuxAlgo TICK concept: https://www.luxalgo.com/library/concept/tick-index.md
- Percent above VWAP script: https://in.tradingview.com/script/li58pHJ7-Percent-of-U-S-Stocks-Above-VWAP
- Index-arbitrage thresholds: https://indexarb.com/iaTermsDescriptions.html ; NYSE program trading weekly reports (e.g.): https://WWW.NYSE.COM/publicdocs/nyse/markets/nyse/PT100313.pdf
- Nasdaq-100 concentration: https://www.nasdaq.com/articles/global-indexes/broadening-nasdaq-100-with-equal-weighting
- VIX lead-lag: https://arxiv.org/pdf/2206.13138 ; Bollen, O'Neill & Whaley (2017): https://law-journals-books.vlex.com/vid/tail-wags-dog-intraday-855663936 ; Bangsgaard & Kokholm (2024): https://ideas.repec.org/a/eee/finmar/v67y2024ics1386418123000496.html
- TradingView CME delay: https://tradingview.com/cme
- TradingView USI symbol list (third-party mirror): https://raw.githubusercontent.com/thonguyen511/tdv/HEAD/data/USI.csv ; TICK.NY default in an open script: https://github.com/ChartsLector/TV-Indicators
- TICK vendor differences: https://forum.ninjatrader.com/forum/ninjatrader-8/platform-technical-support-aa/1085574-tick-differences-between-nt8-and-tos-tradingview ; Barchart TICK vs TICX: https://help.barchart.com/support/solutions/articles/247968-what-is-the-difference-between-tick-and-ticx-
- Intraday internals dataset (public repository history, IQFeed source): https://github.com/hbout56-arsenal/arsenal-dashboard-public (file `internals_snapshot.json`)
- Pine v6 docs (local mirror): writing_scripts/limitations.md (206, ~280-306); concepts/other_timeframes_and_data.md (99, 124, 204, 302, 479, 490-494); reference/request.md (210-216); reference/syminfo.md (15-19, 829-833); reference/time.md (127-131).
