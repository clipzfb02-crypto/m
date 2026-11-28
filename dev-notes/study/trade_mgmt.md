# Trade execution around a Draw on Liquidity: study for DOL Engine v2

Domain: what a trader does with a DOL target, and how the engine should support it. This covers:
- entry models that aim at a DOL (sweep of opposing liquidity → MSS → FVG/OB entry; iFVG continuation; breaker retest; market entry at target activation);
- where to place invalidation (beyond the opposing pool, beyond the sweep extreme, beyond the FVG, protected swing, MAE-based);
- partial exits at intermediate liquidity, R:R, expectancy, MAE/MFE, time stops and ETA;
- what the chart must show at decision time, and which alerts are actionable.

It also audits the engine's invalidation, R:R, WIN≤H race, EV and ETA logic (`baseline_v2.pine`, line numbers as in the brief).

Tools, data and raw outputs:
- folder: `/tmp/claude-0/-home-user-m/7ce60006-3639-59b1-8cd3-87355409d58a/scratchpad/brief/study/trade_tools/`
- scripts: `tlib.py`, `series.py`, `t1_order.py`, `t2_ev.py`, `t34.py`, `analyze.py`
- raw outputs: `out_5min.txt`, `out_1h.txt`

Section 7 gives the commands to reproduce everything.

---

## 0. Executive summary (read this first)

1. **The HUD's EV is a geometric artefact, not an expectancy.** EV is shown at lines 2245 and 2359 as `EV = invWin·RR − (1 − invWin)`, where `invWin` = P(target first | the race is decided within H).
   - Under a driftless walk, the true expectancy of *any* stop/target/time-stop bracket is 0 (optional stopping; Kaminski & Lo 2014).
   - The formula drops the undecided mass. It therefore shows about 0 for near targets and **−0.34R to −0.97R for far targets** (T2), purely from geometry.
   - On 163,249 real race records (6 CME futures at 5-min and 1h, plus BTC 1h; T4-B), **corr(EV shown, realized R) = +0.02**. The mean shown EV for R:R > 4 was −0.39R, while the mean realized R was **+0.03R / +0.06R**.
   - The drift term (`potMu`, line 917) adds about ±0.19R of pure noise per standard error of the 50-bar mean. The driftless WIN≤H is better calibrated: log-loss 0.568 vs 0.582 (5-min) and 0.577 vs 0.593 (1h).
   - **Fix (TM-1):** use a driftless race. Then P(target first) = risk/(risk + reward) = the breakeven win rate. Only the ledger's learned shift (`f_raceAdj`) can move WIN above BE, so EV becomes `(WIN − BE)·(1 + RR)`. Show the ledger's realized R for the active R:R bucket next to it.

2. **Mechanical ICT entry models show no edge over geometry.** This agrees with every rigorous public test.
   - Our coded sweep → MSS → FVG limit entry, targeting the nearest opposing pool: 853 setups on 5-min and 1,124 on 1h (CME + BTC).
   - For three stop rules (beyond the sweep extreme, beyond the FVG, the engine's opposing-pool rule), the win rate was within 1-3 pp of the random-walk race prediction and of a random-entry null with the same geometry.
   - Mean R was −0.06 to +0.05 with SE 0.03-0.10.
   - Public tests: Silver Bullet profit factors 0.66-0.94; 0 of 10 variants profitable (2R target, 2020-2025); "the Silver Bullet hours are not special" (GBB script, 2011-2026 1-min data).
   - The engine should therefore not reward "setup alignment" in the score. It should show the trade honestly, with geometry and a ledger-measured track record.

3. **A stop "just beyond the opposing pool" is a race barrier, not a protective stop.**
   - Once a swing pool is traded through, a stop 0.3 ATR beyond it (the engine's 0.2 ATR zone + 0.1 ATR buffer, lines 93 and 1344) is hit:
     - **64-70% of the time on the sweep bar itself**;
     - **92% within 12 bars** and **95% within 30 bars** (5-min and 1h alike).
   - Random grid levels behave almost the same (57-62% / 90% / 93%).
   - After a "rejected" sweep (close back inside), the sweep-bar extreme is exceeded later in **76-82%** of cases within 30 bars. Random levels give 78-81%.
   - Pools are closed back inside on the sweep bar *less* often than random levels: 44.9% vs 52.7% (5-min) and 46.7% vs 54.8% (1h). This is consistent with Osler-style stop cascades, not with "sweep and reverse".
   - The invalidation therefore means "if the opposing pool is taken first, the draw failed" (a race), and it should be labelled that way (TM-7).

4. **The R:R/WIN readout describes a trade nobody took.** At line 2127 `f_invalidation` is re-run every tick from the *live* close, so R:R, WIN and EV move with each tick. The ledger grades a bracket frozen at activation (`f_openTrial`, 1426-1431). TM-2 freezes the plan from the open `Trial` and shows:
   - live progress in R, heat so far and bars left;
   - a status: target first, opposing pool first, or window expired.

5. **"Next obstacles" do not change the odds beyond distance.** Same-side inner pools and unfilled opposing FVGs between price and target leave the target-first residual (observed − driftless model) unchanged:
   - inner pools: −0.019 vs −0.018 (5-min), −0.024 vs −0.025 (1h);
   - opposing FVG: −0.008 vs −0.025 (5-min, weak), −0.021 vs −0.026 (1h).

   They matter as partial-profit points and as an explanation of the geometry, not as a scoring penalty (TM-3).

6. **Partials and time stops do not change expectancy measurably. They change dispersion and exposure.**
   - 50% at the first inner pool with a break-even runner cut the standard deviation of R from 1.12 to 0.94 (5-min) and from 1.01 to 0.84 (1h).
   - The mean change was +0.107R (SE 0.040) on 5-min and +0.010R (SE 0.028) on 1h, so it is inconclusive.
   - Exiting unresolved trades at 5, 10 or 20 bars instead of H = 30 changed mean R by −0.012 to +0.004 (SE about 0.02-0.03).
   - So show TP1 and time left as information, and measure them in the ledger (TM-3, TM-2). Do not hard-code them as edge.

7. **The geometric fill formula is calibrated.** For a limit entry e below price and a target d above, P(entry touched before target) = d/(d + e) (driftless).
   - Predicted 0.735 vs observed 0.696 on 5-min (4.0% of setups expired unfilled after 20 bars).
   - Predicted 0.774 vs observed 0.752 on 1h (4.7% expired).
   - About 20-26% of sweep → MSS → FVG setups ran to the target without filling.

   The entry-zone proposal (TM-4) can therefore show an honest fill probability and the R:R from the zone.

8. **The engine's intrabar race rule is better than TradingView's own.** `f_step` (1440-1441) assumes a bull bar goes O-L-H-C and a bear bar O-H-L-C. Judged against 1-minute truth:
   - it orders the high and low correctly in **88.1%** of 5-min bars (n = 93,428), 88.2% of 15-min and 88.7% of 60-min bars;
   - TradingView's broker-emulator rule (open closer to the high → high first) gets **80.6-80.7%**;
   - on two-long-wick bars it is 69.6-72.7% vs 64.4-66.8%.

   Keep it; no lower-timeframe request is needed.

9. **Winners' heat is small.** With the engine stop, winners' MAE was 0.27R at the median, 0.60R at p80 and 0.76R at p90 (5-min); 1h gave 0.26 / 0.58 / 0.75. Losers reached a median 19-20% of the way to the target (p80 48-49%). Under a random walk no stop distance adds expectancy (Kaminski & Lo). A ledger "stop curve" (TM-6) lets each chart show whether its DOL picks break that rule.

10. **At decision time the default Clean view shows only Target and PoT.**
    - Invalidation, R:R, race odds, ETA and the track record are Terminal-only, and `showInv` defaults to false (line 172).
    - Breakeven win rate, entry zone, obstacles, time left and plan status do not exist.
    - Alerts carry no plan fields (2079-2093).

    Proposals TM-1 to TM-5 close these gaps with ledger-measured, honest numbers.

---

## 1. Concepts (definitions and parameters)

### 1.1 R-multiple, expectancy, SQN, profit factor
- **R-multiple** (Tharp): a trade's result divided by its initial risk, R = side·(exit − entry)/|entry − stop|.
- **Expectancy** = mean R over trades = p·W̄ − (1 − p)·L̄ in R units.
- **SQN** = √N · mean(R)/sd(R) (Tharp; some practitioners cap N at 100). It is a t-statistic, so 2 means "probably real".
- **Profit factor** = gross win R / gross loss R.
- The engine's ledger already books a realized R per graded window:
  - `rOut` (1457-1458): +rr0 if the target came first; the stop R (−1, or worse on a gap through the stop, 1451-1452) if the stop came first; mark-to-market at H if neither;
  - avg R and PF in the Full view (2419-2426).
- **DOL role:** the honest unit for comparing targets at different distances. A 70% PoT target at R:R 0.3 and a 25% target at R:R 3 are both break-even under a random walk.

### 1.2 Traders' equation and breakeven win rate
- Breakeven win rate **BE = 1/(1 + RR)** (Brooks' "traders' equation": P·reward > (1 − P)·risk).
- **Identity:** for a driftless continuous martingale, P(target at distance d before stop at distance r) = r/(r + d) = 1/(1 + RR) = BE. A random walk always sits exactly at break-even, whatever the stop and target.
- Consequence: any displayed "WIN > BE" must come from information beyond geometry. In the engine, that information can only be the ledger's learned race shift `f_raceAdj` (1367-1371), or a measured selection edge.
- **DOL role:** "is this target worth trading?" is answered by WIN − BE, not by PoT or R:R alone.

### 1.3 Two-barrier race with a horizon (the triple-barrier method)
- For each event, López de Prado's triple-barrier labelling (AFML ch. 3) sets:
  - an upper barrier (profit-take);
  - a lower barrier (stop);
  - a vertical barrier (time).
- The label is the barrier touched first. On a time-out the label is the sign of the return, or the return itself.
- The engine's ledger is exactly this:
  - target = the DOL near edge;
  - stop = `f_invalidation`;
  - vertical = H bars (`f_step` 1434-1459).
- The engine reports three numbers:
  - **Unconditional** P(target first within H) = `pW = f_raceH(d, r, σ, μ, H)`;
  - P(stop first within H) = `pL`;
  - P(neither) = 1 − pW − pL.
- The engine's WIN≤H is the **conditional** pW/(pW + pL) (line 1364). An expectancy must also count the neither branch (marked to market). Section 2.2 T2 shows why the conditional alone misleads.
- **Meta-labelling** (López de Prado): a secondary model learns P(primary signal's bracket wins) from features and decides whether and how much to trade. The engine's ledger plus `f_raceAdj` is an intercept-only meta-label. Feature-based versions belong to the calibration study (`calib_ml.md`).

### 1.4 Optional stopping: brackets cannot create edge
- For a martingale price X and any bounded stopping time τ (first touch of target/stop, capped at H), E[X_τ] = X_0. Any bracket therefore has expected R exactly 0 before costs: tight or wide stop, partials, break-even stops, time stops.
- **Kaminski & Lo (2014, J. Financial Markets 18:234-254):** the "stopping premium" of a stop-loss rule is always negative for a random-walk (i.i.d.) asset. It can be positive only with momentum (positive serial correlation) or regime switching.
- **Lo & Remorov (2017, J. Financial Markets 34:1-15):** on a large sample of US stocks, tight stops underperform buy-and-hold because of trading costs. Outperformance requires sufficiently high serial correlation.
- **DOL role:** exits manage variance and exposure. Edge can only come from *where the target is* (selection) or *which side is taken first* (race information), and the ledger can measure both.

### 1.5 Entry models that target a DOL (exact rules as coded in this study)
Long side; mirror for short. Parameters are as tested; ICT itself does not fix them.

**(a) Sweep → MSS → FVG ("2022 model" / Silver Bullet without the time window).**
1. *Sweep.* A confirmed, unswept swing low (ta.pivotlow(5, 5)) is traded through: `low[s] < P`. Several pools swept on one bar: take the outermost P. Require a close back above: `close[s] > P`, and `low[s] > P − 3·ATR` (not a crash).
2. *Sweep extreme* SX = low[s], updated as the running minimum until the MSS.
3. *MSS level* M = the most recent confirmed 3-bar fractal high (pivot length 1) with its pivot bar in [s − 20, s − 1] and above close[s].
4. *MSS:* the first bar m ∈ (s, s + 12] with `close[m] > M`. Otherwise abandon the setup.
5. *FVG:* the last bullish gap `low[j] > high[j−2]` with j ∈ [s + 2, m + 1]. Entry E = FVG top (low[j]); variant CE = midpoint. No FVG → abandon. The setup is known at bar a = m + 1.
6. *Target:* the nearest live BSL (pivot high, strength 5, unswept) at least 0.25 ATR above close[a] and at most 10 ATR above E.
7. *Fill:* a limit at E, valid for 20 bars. If the target trades first, record "ran without fill".
8. *Stops:*
   - **sweep:** SX − 0.1 ATR;
   - **fvg:** FVG bottom − 0.1 ATR;
   - **engine:** the nearest live SSL below E minus 0.3 ATR, else E − 1.5 ATR.
   - All have a risk floor of 0.25 ATR.
9. *Outcome:* first touch on the 1-minute path (5-min test) or the engine's OHLC path (1h test), horizon H = 30 bars after the fill. A stop touched inside the fill minute counts as a loss.

ICT sources place the stop "below the liquidity low" (the sweep extreme). The target is usually the nearest opposing liquidity ("low-hanging fruit") (LuxAlgo Model 2022; TradingFinder script; community notes).

**(b) iFVG continuation.**
- An FVG is inverted by a candle *body close* beyond its far edge (engine: `close < z.bottom` for a bullish gap, 1603).
- Entry: the retest of the inverted zone with a hold.
- Stop: beyond the iFVG or beyond the sweep candle's extreme. Target: the first internal liquidity, then the DOL.
- No published statistics exist. Sibling `ict_pd.md` 2.3 found broken gaps held on retest exactly as often as random zones (S&P daily).

**(c) Breaker retest / "Unicorn".**
- A breaker is an order block whose leg swept liquidity and was then broken (engine 1646-1661, `tookLiq` only).
- Unicorn = the overlap of a breaker and an FVG in the same direction. Entry is in the overlap (not the whole gap). Stop just beyond the breaker, or 0.4 × zone height beyond in one scripted detector. Target: the next liquidity, often 2-3R.
- No statistics exist.

**(d) OTE** (62-79% retracement of the impulse) is covered in `ict_struct.md` 1.10.

**(e) Market entry at activation.**
- The engine's ledger implicitly assumes this: entry at the close of the bar the DOL is committed (`f_openTrial` 1426-1431).
- This is the right unit for grading a *forecast*. A trader using a limit entry faces a different R:R and a fill risk (1.12).

**Failure modes (all models).**
- The definitions are not standardised (sweep depth, MSS swing strength, FVG choice, retest confirmation), so results vary with how the rules are coded.
- Selection bias: annotated charts show the setups that worked.
- On rigorous tests the models' win rates match their R:R geometry (section 2).

### 1.6 Invalidation placement

| Rule | Definition | Engine |
|---|---|---|
| Opposing pool | Just beyond the nearest opposing level: liquidity zone bottom/top or the far edge of an opposing array, buffer 0.1 ATR. Ignore levels beyond maxATR. Fallback: the execution-TF range extreme (`exeRL/exeRH`), then 1.5 ATR. Risk floor 0.25 ATR | `f_invalidation` 1343-1358 |
| Sweep extreme (post-raid) | After a raid of the opposing pool that closed back inside: beyond the raid's extreme | missing |
| FVG/OB far edge | Beyond the entry array | missing |
| Protected swing | Beyond the strong low/high of the current leg (ICT/SMC) | fallback only; `ict_struct.md` ICTS-5 |
| Volatility | k·ATR from entry | 1.5 ATR fallback |
| MAE percentile (Sweeney) | Stop at the p75-p90 of winners' MAE from the strategy's history | heat p80 shown (2404-2408), not used |

In practice, the engine rule gave:
- median risk 1.53 ATR (5-min) and 1.69 ATR (1h); IQR 1.1-2.3 and 1.2-2.5 ATR;
- the 1.5 ATR fallback in 6.6% / 5.4% of cases and the 0.25 ATR floor in 0.3% / 0.6%;
- median R:R 1.68 / 1.50, median target distance 2.67 / 2.51 ATR (T4-B).

### 1.7 Sweep penetration depth and stop buffers
- **Depth** of a sweep = how far beyond the level price trades, measured in ATR (Wilder 14, previous bar) within N bars of the first trade-through.
- **Rejected sweep** = the sweep bar closes back inside. **Accepted** = it closes beyond.
- The only published practitioner statistic is a script that sets its stop at the p90 of the last 500 traps' depth.
- Our numbers are in 2.2 T3. Pools and random levels have nearly the same depth distribution: median 0.43-0.60 ATR on the sweep bar and 2.8-2.9 ATR within 30 bars.
- **DOL role:** no affordable buffer survives a sweep. A stop beyond the opposing pool is effectively "exit when the opposing pool is taken", which is the race's definition of failure.

### 1.8 Partials at intermediate liquidity, break-even stops, scaling out
- TP1 = the first same-side pool or opposing array between entry and target ("low-hanging fruit"). Typical rule: take 50% off, move the stop to entry, and let the runner go to the DOL.
- Under a martingale this cannot change expectancy (1.4). It cuts the dispersion of R and raises the win rate of "not a loss".
- Practitioner tests:
  - partial profit-taking reduced returns in every tested variant of a trend-following system (Enlightened Stock Trading, RealTest);
  - forum consensus: scaling out smooths equity "at the expense of expectancy".
- Our test (T4-A): sd of R fell by 16-17%; the mean change was inconclusive.

### 1.9 Next obstacles (path map)
Obstacles are levels between price and the target that price must cross first:
- same-side inner pools (the engine's `inner` flag inside stacks, 1240-1248);
- opposite-polarity PD arrays on the path. For a buy-side target these are bearish FVG/OB/breakers above price: in engine terms, every pool level with `side == tgt.side` that is nearer than the target;
- high-volume nodes (the engine's path-cost multiplier, `f_pathVol` 1417-1424 and 1945-1947).

Academic S/R work finds small, short-lived barrier effects:
- Osler 2000: 60.8% vs 56.2% bounce rate at published vs arbitrary levels;
- `academic_sr.md`: P(through) is 7-10 pp lower for a recently bounced level.

Our race test (T4-B) found no extra effect on target-first odds once distance is accounted for. The obstacle is already "priced" by the longer distance.

### 1.10 MAE / MFE
- **MAE** = maximum adverse excursion before exit. **MFE** = maximum favourable excursion.
- Sweeney (1997) proposed placing the stop beyond the MAE that most winners never reach (p75-p90 of winners' MAE, with about 60 or more winners).
- **MFE capture** = realized R / MFE. **Edge ratio** = mean MFE / mean MAE. In `ict_struct.md`, MSS signals scored 0.97-1.13 on 15,817 cases.
- The engine stores MAE per hit (`t.mae`, ATR units at entry, 1442-1443) and shows the p80 "heat" (2404-2408). It stores no MFE.

### 1.11 Time stops, horizon, ETA
- **Time stop:** exit after T bars if unresolved. It is the vertical barrier of 1.3.
- Practitioner guidance: time stops help only if MFE duration clusters. Tests of nine time and price exits on 481k short-option trades found none beat holding.
- **ETA:** the conditional first-passage time given a hit (Lévy / inverse-Gaussian; `quant_pot.md` 1.3).
- The engine:
  - grades within H (1455-1456);
  - shows "ETA|hit": the median bars-to-hit of past ledger hits whose distance at activation was within ±0.5 ATR of the current distance, with at least 5 samples (2116-2126).
- `quant_pot.md` found that the constant-σ ETA is anti-correlated with the realized time (−0.09), while a volatility-time ETA is positively correlated (+0.11 to +0.22).
- The live PoT is a *rolling* H-bar window from now. It never reflects the time already used by the current plan.

### 1.12 Limit-entry fill probability
- With entry e below price and target d above, P(touch the entry before the target) = d/(d + e), driftless and infinite horizon.
- Conditional on the fill, P(target before stop) = (r − e)/(r + d) = 1/(1 + RR_zone), where RR_zone = (d + e)/(r − e).
- So the expectancy of the limit plan is 0 under a martingale, as for the market plan. The trader gets a better R:R at the cost of the fill probability.
- Validated in T4-A (section 0, item 7).

### 1.13 Intrabar ambiguity
When both barriers are inside one bar, a path assumption decides the order:
- **Engine** (1440-1441): bull bar O-L-H-C, bear bar O-H-L-C. A gap beyond a barrier settles at the open (1438-1441, 1451).
- **TradingView broker emulator:** if the open is closer to the high, assume O-H-L-C, else O-L-H-C (Pine docs, concepts/strategies.md:124-129). Bar Magnifier uses lower-timeframe data instead (Premium plans).
- T1 shows the engine rule is the better of the two.

### 1.14 What a trader needs on the chart at decision time

| Item | Why | Engine today | Proposal |
|---|---|---|---|
| Target (where) | the objective | zone + `Target:` label (2214-2226) | — |
| PoT within H (how likely) | — | live, capped 95% (2067) | — |
| Which side first (race vs opposing pool) | the honest "which liquidity next" | Terminal HUD WIN≤H only when `showInv` | TM-1, `ict_struct` ICTS-3 |
| Invalidation (where wrong) | sizing and exits | off by default (172), Terminal | TM-2, TM-7 |
| R:R and breakeven win % | trade quality | R:R Terminal only; BE missing | TM-1 |
| Expectancy | should I trade it | shown but wrong (2245) | TM-1 |
| Entry zone + fill probability | how to get in | missing | TM-4 |
| Obstacles / TP1 | where price may stall; partials | missing | TM-3 |
| Timing (ETA, time left, killzone) | patience / exit | ETA|hit + killzone Terminal; time left missing | TM-2 |
| Track record on this chart | trust | Terminal accuracy panel | TM-1, TM-6 |
| Plan status (TP1, invalidated, expired) | management | missing | TM-2, TM-5 |

### 1.15 Actionable alerts
- An alert is actionable when its payload lets the trader act without opening the chart: event, side, target, entry/zone, invalidation, TP1, R:R, BE, probability and sample size, bars left.
- Events that map to decisions:
  - new plan;
  - entry zone tapped;
  - TP1 reached (scale out / move the stop);
  - opposing pool taken (thesis dead);
  - target reached;
  - plan window expired.
- Platform facts: `alert()` messages can be built at runtime; `alertcondition()` needs a const message but can embed `{{plot("title")}}`; alert budgets are small (Essential plan: 20). See `competitors.md` COMP-2.

### 1.16 Behaviour: the disposition effect and pre-commitment
- Odean (1998), 10,000 discount-brokerage accounts 1987-1993: investors realized gains far more readily than losses (PGR 0.148 vs PLR 0.098).
- A plan frozen at entry (stop, target, time) that the chart keeps showing counters ad-hoc exits. This is a UX argument, not an edge.

### 1.17 Position sizing (Kelly)
- Kelly f* = p − (1 − p)/RR. With p from geometry, p = BE and f* = 0.
- Showing Kelly would only be meaningful with a ledger-measured p and a confidence interval. It is not recommended for the chart (2.3).

---

## 2. Evidence

### 2.1 Published evidence

| # | Claim | Source and data | Numbers | Grade |
|---|---|---|---|---|
| P1 | Stop-loss rules cannot add expected return under a random walk | Kaminski & Lo 2014, J. Fin. Markets 18:234-254 (theory + index futures); WP version monthly 1950-2004 | Stopping premium always negative under i.i.d. returns; can be positive with momentum; certain rules +50 to +100 bp/month during stop-out periods (WP) | strong |
| P2 | Tight stops lose to buy-and-hold after costs unless serial correlation is high | Lo & Remorov 2017, J. Fin. Markets 34:1-15 (US stocks) | Closed-form; tight stops underperform; downside risk reduced "but not substantially" | strong |
| P3 | ICT Silver Bullet / 2022 model mechanical tests lose | Independent write-ups: 79 setups ES/NQ 2014-2026; backtestingmax 10 tests; Silver Bullet [GBB] script, 1-min ES/NQ/YM/GC 2011-2026 with costs; 16-year 25,000-variant study (video summary) | PF 0.66-0.94; SB win 26.5% ES / 27.9% NQ (BE at 2R = 33.3%); 0/10 tests profitable; win 22.5-26.3% (1m), 31.6-40.8% (5m); 2R target win 35.4%, 9/10 lost 2020-2025; GBB: "the Silver Bullet hours are not special"; stop beyond the sweep extreme was the best variant in held-out years but still unprofitable; 16-year study: best variants about 52% win, most 34-48% | moderate (independent, several, consistent; not peer-reviewed) |
| P4 | ICT FVG retest component has no edge | Backtrex FVG in NY AM kill zone, GBP/USD; mechanical ICT bot, 1 year | Win 33.89%, PF 0.80; bot −15.1R, win 29.6%, PF 0.81 | weak-moderate |
| P5 | FVGs behave like size-matched placebo zones | "FVG Statistics with Placebo Control" script: 3 asset classes × 3 TFs × 2 periods; `ict_pd.md` 2.1 (5 controlled studies) | No detectable advantage in 14 measurements; reaction +2.5 to +5 pp, 5-15 min | moderate |
| P6 | Stop clusters cascade after crossing | Osler 2003 (J. Finance 58(5)), 2005 (JIMF 24(2)) | Stops just beyond round numbers; extra move +0.27 to +2.35 hundredths of a percent for 15 min-2 h | strong |
| P7 | Published S/R interrupts trends slightly more than arbitrary levels | Osler 2000, FRBNY EPR 6(2) | Bounce 60.8% vs 56.2%; firms' "strength" ratings useless | strong |
| P8 | Partial profit-taking lowers return in trend following | Enlightened Stock Trading (RealTest, many parameter sets) | "Every instance of partial profit taking reduced the overall rate of return" | weak |
| P9 | MAE-based stops (p75-p90 of winners' MAE) | Sweeney 1997; practitioner guides (NexusFi, MQL5, LuxAlgo) | One anecdote: premature stop-outs 36% → 14%; no controlled study | weak |
| P10 | Time exits rarely beat holding | 9 daily-close exits on 481k short-option trades (FlashAlpha) | None beat hold-to-expiry at the same risk; average Sharpe lower | weak (other asset class) |
| P11 | Disposition effect | Odean 1998, J. Finance; 10,000 accounts | PGR 0.148 vs PLR 0.098 | strong |
| P12 | Triple-barrier labelling / meta-labelling | López de Prado 2018, *Advances in Financial ML*, ch. 3 (secondary summaries: Hudson & Thames, OpenQuant docs) | Definitions | n/a (method) |
| P13 | Broker-emulator intrabar assumption | Pine v6 docs, concepts/strategies.md:124-129 | Open nearer the high → O-H-L-C, else O-L-H-C | n/a (platform fact) |
| P14 | Expectancy / SQN definitions | Tharp; secondary glossaries | SQN = √N·mean R/sd R; "good" about 2-3 | n/a (definition) |

### 2.2 Our tests

**Data.**
- 6 CME futures (ES, NQ, RTY, YM, GC, CL), 1-minute, 2026-01-20 to 2026-04-15: about 67-84k minutes each. Resampled to 5-min, with races resolved on the real 1-minute path.
- The same 6 contracts on 1h, 2025-03-21 (CL 2025-06-01) to 2026-04-15.
- BTC/USD 1h, 2016-01-01 to 2025-01-07.

**Path on 1h data.** Three pseudo sub-bars per bar following the engine rule (bull O-L-H-C, bear O-H-L-C), so 1h races replicate `f_step` exactly.

**Common engine settings.** ATR = Wilder 14; pools = `ta.pivothigh/low(5, 5)`; a pool is swept when price trades through it (strict); inner pools = pivot strength 2; H = 30 bars; `potSig` = stdev of Δclose over 50 bars; `potMu` = 0.5·mean of Δclose over 50 bars (lines 915-917).

**Caveats.**
- Model-B records are sampled every 3rd (5-min) or 2nd (1h) bar with H = 30, so they overlap. Standard errors are inflated by a design effect of 10 / 15.
- The CME 1-minute sample is one quarter long.
- No costs are included. They would push every mean R below zero.

**T1. Which extreme came first inside a bar?** (`t1_order.py`)

| Bars | n | Engine rule correct | TradingView rule correct | Two-long-wick bars n | Engine | TV |
|---|---|---|---|---|---|---|
| 5-min | 93,428 | **0.881** | 0.806 | 17,757 | **0.696** | 0.644 |
| 15-min | 32,377 | **0.882** | 0.807 | 6,376 | **0.714** | 0.668 |
| 60-min | 8,211 | **0.887** | 0.807 | 1,702 | **0.727** | 0.666 |

Bars whose high and low fell in the same minute are excluded. "Two-long-wick" means both wicks are at least 25% of the range, which is the case where a two-barrier race is ambiguous.

**T2. What the EV readout means under a fair market** (`t2_ev.py`; σ = 1 per bar, H = 30, μ = 0; distances in units of σ√H)

| d | r | RR | pW | pL | neither | WIN≤H (engine) | BE | EV shown | true E[R] |
|---|---|---|---|---|---|---|---|---|---|
| 0.25 | 0.50 | 0.5 | 0.667 | 0.333 | 0.000 | 0.667 | 0.667 | +0.000 | 0 |
| 0.50 | 0.50 | 1.0 | 0.495 | 0.495 | 0.009 | 0.500 | 0.500 | +0.000 | 0 |
| 1.00 | 0.50 | 2.0 | 0.272 | 0.605 | 0.123 | 0.310 | 0.333 | −0.070 | 0 |
| 1.50 | 0.50 | 3.0 | 0.121 | 0.617 | 0.262 | 0.164 | 0.250 | **−0.343** | 0 |
| 2.00 | 0.50 | 4.0 | 0.043 | 0.617 | 0.340 | 0.065 | 0.200 | **−0.676** | 0 |
| 0.50 | 1.00 | 0.5 | 0.605 | 0.272 | 0.123 | 0.690 | 0.667 | +0.035 | 0 |
| 2.00 | 1.00 | 2.0 | 0.045 | 0.317 | 0.637 | 0.125 | 0.333 | **−0.624** | 0 |
| 3.00 | 1.00 | 3.0 | 0.003 | 0.317 | 0.680 | 0.008 | 0.250 | **−0.966** | 0 |

- A Monte Carlo with a time stop at H marked to market (200k Gaussian paths) gives E[R] of −0.001 / +0.092 / +0.024 / −0.056 for the four checked brackets. The residuals are discretisation error; the theoretical value is 0. The engine shows +0.000 / −0.343 / −0.624 / +0.000 for the same brackets.
- **Drift noise.** With μ = 0.5 × k standard errors of a 50-bar mean (k = ±1, ±2) and d = r, the shown WIN≤H is 0.40 / 0.60 (k = ∓1) and 0.32 / 0.69 (k = ∓2). The shown EV is ∓0.19R and ∓0.37R. The truth is 0.50 / 0R.

**T3. Sweep depth** (`t34.py`, `depth_stats`)
- Events: the first trade-through of an unswept pivot pool.
- Control: the first cross of a random-phase grid level (step 2 × median ATR) after at least 10 bars on one side (Osler-style arbitrary level).

| | 5-min pools | 5-min grid | 1h pools | 1h grid |
|---|---|---|---|---|
| n | 10,219 | 10,075 | 12,879 | 17,435 |
| Close back inside on the sweep bar | **0.449** | 0.527 | **0.467** | 0.548 |
| Depth on the sweep bar: median / P ≥ 0.3 ATR | 0.43 / **0.64** | 0.37 / 0.57 | 0.60 / **0.70** | 0.45 / 0.62 |
| Within 12 bars: median / P ≥ 0.3 / P ≥ 1 / P ≥ 1.5 | 1.76 / **0.92** / 0.70 / 0.56 | 1.68 / 0.90 / 0.67 / 0.54 | 1.88 / **0.92** / 0.71 / 0.58 | 1.69 / 0.90 / 0.67 / 0.54 |
| Within 30 bars: median / P ≥ 0.3 / P ≥ 1 / P ≥ 1.5 | 2.84 / **0.95** / 0.81 / 0.71 | 2.56 / 0.93 / 0.78 / 0.68 | 2.87 / **0.95** / 0.81 / 0.72 | 2.62 / 0.93 / 0.78 / 0.68 |
| Rejected sweeps: sweep-bar extreme exceeded later (30 bars) by > 0 / > 0.25 / > 0.5 ATR | 0.82 / 0.78 / 0.73 | 0.81 / 0.77 / 0.72 | 0.76 / 0.72 / 0.68 | 0.78 / 0.73 / 0.68 |
| Accepted sweeps: depth within 30 bars, median / P ≥ 1 | 3.31 / 0.88 | 3.20 / 0.88 | 3.55 / 0.91 | 3.42 / 0.90 |

Reading:
- Pools are slightly *more* penetrated and *less* often closed back inside than random levels (cascade, P6).
- Stops just beyond a pool do not survive its sweep.
- The wick of a rejected sweep is no more protective than a random level's.

**T4-B. The engine's readout on real data** (`t34.py`, model B)
- Sampling: every 3rd (5-min) / 2nd (1h) bar, both sides.
- Target: the nearest pool 0.5-10 ATR away.
- Stop: the engine rule (nearest opposing liquidity zone or unfilled opposing FVG, plus buffer; fallback 1.5 ATR; floor 0.25 ATR).
- Entry at the close; race on the path; H = 30; mark to market at H.

| | 5-min (n = 57,728) | 1h (n = 105,521) |
|---|---|---|
| Win / loss / neither | 0.323 / 0.533 / 0.145 | 0.340 / 0.510 / 0.150 |
| Mean realized R (SE with design effect) | −0.008 (0.019) | −0.001 (0.017) |
| Driftless model pW / pL | 0.341 / 0.545 | 0.365 / 0.526 |
| WIN≤H Brier / log-loss: engine drift | 0.1951 / 0.5816 | 0.2013 / 0.5928 |
| WIN≤H Brier / log-loss: driftless | **0.1921 / 0.5680** | **0.1967 / 0.5769** |
| corr(EV shown, realized R) | **+0.019** | **+0.016** |

Calibration of the displayed WIN≤H (decided races, 8 quantile bins). Columns: shown with drift → driftless → observed.
- 5-min: 0.041 → 0.089 → 0.104 · 0.139 → 0.185 → 0.177 · … · 0.622 → 0.585 → 0.585 · 0.792 → 0.737 → 0.738.
- 1h: 0.047 → 0.094 → 0.104 · … · 0.814 → 0.761 → 0.735.

The drift makes the readout over-confident at both ends. The driftless value tracks the observed rate.

EV shown vs realized R by R:R bucket (5-min | 1h):

| R:R | n | EV shown (drift) | EV shown (driftless) | Realized R | Win | BE | Neither |
|---|---|---|---|---|---|---|---|
| ≤ 0.5 | 6,017 / 13,552 | +0.055 / +0.055 | +0.037 / +0.033 | −0.016 / −0.039 | 0.661 / 0.647 | 0.749 / 0.751 | 0.125 / 0.126 |
| 0.5-1 | 10,900 / 22,272 | +0.033 / +0.038 | +0.022 / +0.020 | −0.005 / −0.011 | 0.500 / 0.494 | 0.576 / 0.578 | 0.136 / 0.144 |
| 1-2 | 16,329 / 29,343 | −0.053 / −0.050 | −0.043 / −0.042 | −0.023 / −0.001 | 0.333 / 0.335 | 0.412 / 0.414 | 0.144 / 0.164 |
| 2-4 | 15,119 / 25,190 | −0.232 / −0.231 | −0.161 / −0.161 | −0.015 / −0.005 | 0.193 / 0.192 | 0.266 / 0.267 | 0.159 / 0.168 |
| > 4 | 9,363 / 15,164 | **−0.393 / −0.381** | −0.326 / −0.291 | **+0.033 / +0.057** | 0.091 / 0.099 | 0.146 / 0.146 | 0.146 / 0.124 |

Other model-B results:
- **Obstacles.** Residual = observed target-first minus the driftless pW.
  - 5-min, inner pool: −0.018 (with) vs −0.019 (without); opposing unfilled FVG: −0.025 vs −0.008 (difference 1.4 SE).
  - 1h: −0.025 vs −0.024; −0.026 vs −0.021.
  - Distance alone explains the lower raw win rate of targets behind obstacles (0.245 vs 0.461 raw at 5-min).
  - The uniform −2 pp residual is consistent with the asymmetric hit rules: the target needs a trade-through (strict >), the stop a touch (≤). `f_raceAdj` learns exactly this offset.
- **Heat.** Winners' MAE (R): p50 / p80 / p90 = 0.27 / 0.60 / 0.76 (5-min) and 0.26 / 0.58 / 0.75 (1h). Losers' MFE as a fraction of the way to the target: p50 0.19-0.20, p80 0.48-0.49.
- **Time stops.** Exiting still-open trades at 5 / 10 / 20 bars instead of 30 changed mean R by −0.002 / +0.003 / +0.003 (5-min) and −0.012 / −0.000 / +0.004 (1h). SE is about 0.02-0.03. Share still open: 57 / 38 / 21% and 61 / 42 / 23%.

**T4-A. Sweep → MSS → FVG limit entry** (`t34.py`, model A; rules in 1.5a)

| | 5-min | 1h |
|---|---|---|
| Setups / filled / ran to target unfilled / expired | 853 / 594 / 225 / 34 | 1,124 / 845 / 226 / 53 |
| Fill before target: observed vs d/(d + e) | 0.696 vs 0.735 | 0.752 vs 0.774 |
| Median wait for the fill | 1 bar | 1 bar |
| Stop = sweep extreme: risk (ATR) / median R:R | 2.46 / 1.12 | 2.49 / 1.13 |
| Win / loss / neither | 0.394 / 0.446 / 0.160 | 0.351 / 0.407 / 0.241 |
| Model: r/(r + d) and finite-H pW | 0.473 / 0.381 | 0.477 / 0.378 |
| Random-entry null, same geometry | 0.375 | 0.370 |
| Win − finite-H model (SE) | +0.012 (0.019) | −0.027 (0.015) |
| Mean R (SE) | −0.004 (0.042) | −0.024 (0.036) |
| Stop = FVG far edge: risk / R:R / win / mean R (SE) | 0.53 / 4.80 / 0.195 / +0.047 (0.099) | 0.54 / 5.22 / 0.170 / −0.056 (0.079) |
| Stop = engine rule: risk / R:R / win / mean R (SE) | 2.88 / 1.00 / 0.406 / −0.012 (0.040) | 3.14 / 0.91 / 0.375 / −0.030 (0.032) |
| Winners' MAE p80 (sweep / FVG / engine stop) | 0.57 / 0.66 / 0.46 R | 0.49 / 0.69 / 0.45 R |
| Partials: 50% at the first inner pool, runner stop at break-even. Records with an inner pool / TP1 hit / TP1 R:R | 226 / 0.50 / 0.83 | 269 / 0.42 / 0.81 |
| Mean R full vs partial (sd) | −0.120 (1.12) vs −0.013 (0.94) | −0.154 (1.01) vs −0.144 (0.84) |
| Paired difference (SE) | +0.107 (0.040) | +0.010 (0.028) |

### 2.3 Evidence summary for the engine

| Finding | Grade | Implication |
|---|---|---|
| Brackets (stop, target, partial, time stop) cannot create expectancy under a martingale | strong (theory P1, P2) + moderate (T2, T4-B, T4-A) | The EV readout must come from the ledger, not from the geometry |
| The displayed EV has no predictive value (corr +0.02) and a geometric sign | moderate (T4-B, 163k records) | TM-1 |
| Drift in the race hurts calibration | moderate (T4-B; consistent with `quant_pot.md` QPOT-01) | TM-1 uses μ = 0 |
| Mechanical sweep → MSS → FVG has no edge over geometry | moderate (T4-A + P3, P4) | No score bonus; show the plan with its ledger record |
| Stops just beyond a pool do not survive its sweep (92-95%) | moderate (T3) | TM-7: it is a race barrier |
| Obstacles add no information beyond distance | moderate (T4-B) | TM-3: show, don't penalise |
| Partials reduce dispersion 16-17%; mean effect inconclusive | weak-moderate (T4-A, P8) | Show and measure (TM-3) |
| The fill formula d/(d + e) is calibrated within 2-4 pp | moderate (T4-A) | TM-4 |
| The engine's intrabar rule beats TradingView's (88% vs 81%) | moderate (T1) | Keep `f_step` |
| Disposition effect: plans should be frozen and visible | strong (P11) for the bias; weak for the UX benefit | TM-2 |

---

## 3. Engine gap analysis (`baseline_v2.pine`)

| Concept | Status | Lines | What the engine does and how it differs |
|---|---|---|---|
| Two-barrier finite-horizon race (math) | present | `f_race` 447-461, `f_raceH` 466-482 | Correct (`quant_pot.md` ported and Monte-Carlo-verified it) |
| WIN≤H readout | partial | 1343-1364, 2127-2130, HUD 2244-2246, panel 2358-2363 | Conditional on "decided within H" only; uses drift `potMu·side` (917, 1361), which worsens log-loss 2.4-2.8% (T4-B); recomputed from the live close every tick |
| EV readout | **wrong** | 2245, 2359 | `invWin·RR − (1 − invWin)` ignores the undecided branch and its mark-to-market. It is a function of geometry (T2) and does not predict realized R (corr +0.02, T4-B). It shows −0.39R for R:R > 4 where the realized value is +0.03 to +0.06R |
| Breakeven win rate | missing | — | Not shown; this is the comparison that makes WIN meaningful |
| Ledger realized R, PF, race win | present | `rOut` 1457-1458, `raceSt` 1078-1079 and 1489-1498, Full panel 2419-2426 | Honest numbers, but not tied to the active target's R:R and not shown in the HUD |
| Ledger race correction | present | `f_raceAdj` 1367-1371 | Intercept-only logit shift with m = 20; `pRace` is drift-based (1430), so its sum mixes drift noise into the baseline |
| Race edge vs geometry | missing | — | `raceSt` holds n, wins and Σp but shows no "wins − Σp" with a z-score |
| Invalidation beyond the nearest opposing level | present; semantics partial | 1343-1358 | Includes arrays as well as liquidity; zone depth 0.2 ATR + buffer 0.1 ATR; fallback `exeRL/exeRH` then 1.5 ATR (5-7% of cases); risk floor 0.25 ATR. T3: once the pool is swept, the stop is hit 92-95% of the time within 12-30 bars, so it is a race barrier. Labelled "⊗ INVALIDATION" (2212) |
| Post-raid stop (beyond the sweep extreme) | missing | raid detection exists at 1579-1582 | The ICT model's stop; no protective value beyond geometry (T3, T4-A), but it matches traders' semantics |
| Protected-swing stop | partial | fallback 1354; `exeProtL/H` returned at 925 but unused | See `ict_struct.md` ICTS-5 |
| Stop buffer from the sweep-depth distribution | partial | `zoneATR` 93, `buf` 1344 | Fixed 0.3 ATR; the data show no affordable buffer survives a sweep |
| Frozen trade plan (entry, stop, R:R at activation) | missing | ledger freezes at 1426-1431; HUD recomputes at 2127 | Display and ledger describe different trades |
| Plan status (target first / opposing pool first / expired) | missing | `t.race` and `t.status` exist (1444-1456) | Not displayed for the active target |
| Time left in the plan window | missing | `activeSince` 2035, `t.bar0` | The live PoT is a rolling H-bar window (2067) |
| ETA | present / partial | 2116-2126, HUD 2240 | Median bars-to-hit of similar-distance past hits (n ≥ 5); conditional on a hit; no clock time; constant-σ issues (`quant_pot.md` QPOT-05) |
| Entry zone (draw-aligned array between price and stop) | missing | arrays exist in `pool` (kinds 2/4/6 and 3/5/7) and `ifvgs` (1026) | Arrays are only targets, never entries |
| Limit fill probability | missing | — | d/(d + e) validated (T4-A) |
| Entry models (sweep → MSS → FVG, iFVG retest, breaker retest, Unicorn) | missing as models; components present | raids 1579-1582, BOS 1542-1547, FVG 907-913 and 1867-1889, iFVG 1598-1644, breakers 1646-1661 | Correctly not used to boost scores (no edge, T4-A, P3) |
| Obstacles between price and target | partial | `inner` 1240-1248 and 684-685; `f_pathVol` 1417-1424 and 1945-1947 | Inner pools are penalised ×0.70 *as targets*; obstacles are never listed. T4-B: no extra predictive value |
| Partials / TP1 | missing | — | — |
| MAE (heat) | present | 1442-1443, `maeHit` 1073 and 1483, p80 2404-2408 | MAE of hits only, ATR units at entry; not converted to R |
| MFE | missing | — | Needed for "how far do misses get" and for the TP1 hit rate |
| Stop-distance expectancy curve | missing | — | Computable from `t.mae` + `t.d0` + the mark-to-market at H with O(1) state (TM-6) |
| Time stop (vertical barrier) | present | 1455-1456 | Grading window = H; a long-lived DOL is re-graded in consecutive windows (2038-2045) |
| Intrabar path rule | present, verified | 1438-1452 | 88% correct vs TradingView's 81% (T1); gaps settled at the open |
| Alerts | partial | 2077-2093 | New target (tag/price/score/PoT), iFVG, live sweep, draw flip. No invalidation / R:R / BE / ETA fields; no entry-zone, TP1, opposing-pool-taken or expiry events; `alertcondition` messages carry no values |
| Decision-time info in Clean | partial | 2214-2226 | Target + PoT only; `showInv` default false (172) |
| Kelly / sizing | n/a | — | Not recommended (1.17) |

**Audit notes (detail).**
1. `f_invalidation` (1343-1364):
   - The loop accepts *any* opposing level, liquidity or array, nearest by `lv.distance(close)` with `dd ≥ 0`. Price inside an opposing FVG is skipped (dd < 0) and the next one is used. That is reasonable.
   - The distance gate uses `atr` (1350) while ejection uses `atrE`. This is a minor inconsistency.
   - The stop is placed at the opposing level's *far* edge minus 0.1 ATR. For an SSL zone that is pl − 0.2 ATR − 0.1 ATR.
2. Line 1364:
   - drift `m = potMu·side` enters both `f_raceH` calls (T2: ±0.19R of EV per standard error);
   - the returned probability is conditional on the race being decided;
   - `f_race` is the fallback when pW + pL ≈ 0.
3. `f_openTrial` (1426-1431) stores `pRace` (conditional, with drift) and `rr0`. `f_raceAdj` therefore learns a shift relative to a drift-contaminated baseline. With μ = 0, `pRace` = BE and the learned shift *is* the race edge.
4. `f_step` (1434-1459):
   - the target hit is strict for liquidity (`>`) while the stop is a touch (`<=`). This is consistent with the sweep definition and explains the uniform −2 pp target-first residual in T4-B; `f_raceAdj` absorbs it;
   - when both barriers fall in one bar, `advFirst` decides (88% / 70% accurate, T1);
   - after the stop is hit (race = −1) the record keeps running until the target is hit or H expires, so the PoT hit grade and the race grade coexist. This is correct;
   - `t.mae` keeps growing after a stop-out until the target is hit. "Heat" is therefore the heat of a stop-less hold, not of the bracketed trade. Label it that way.
5. Rendering (2111-2130) re-runs `f_invalidation(activeLv)` on the last bar with the live `close`, so R:R and WIN≤H change every tick (one of the "jumping numbers" complaints).
6. ETA (2116-2126): `dHit` holds `d0` at activation and `ttHit` the bars from activation. The comparison uses the *current* distance against activation distances, which is consistent. It needs at least 5 similar hits. It is shown as a bar count only.
7. Alerts (2079-2081): the new-target alert waits for the PoT filter (2071). Good. The message has no plan fields.

---

## 4. Proposals (best first; at most 10)

Interactions with sibling studies are noted per proposal. Line numbers refer to `baseline_v2.pine`.

### TM-1 (P1, S) · Honest race economics: driftless race, breakeven win rate, ledger-learned EV

**Why.** The EV shown at 2245 and 2359 is a geometric artefact. In a fair market it reads 0 for near targets and −0.3 to −1.0R for far ones. On 163k real records it has corr +0.02 with realized R (T2, T4-B). The drift term adds noise and worsens WIN≤H calibration (log-loss +2.4-2.8%). With μ = 0 the infinite-horizon race equals the breakeven win rate exactly (1.2). The only honest source of positive EV is therefore the ledger's measured race outcomes. The engine already learns them in `f_raceAdj`.

**Spec.**

1. `f_invalidation` (1343-1364): remove the drift and return the driftless race plus the unconditional finite-H probabilities:
   ```pine
   float d    = math.max(0.0, tgt.distance(close))
   float sg   = nz(potSig)
   float pInf = f_race(d, risk, sg, 0.0)          // = risk / (risk + d) = breakeven win rate
   float pW   = f_raceH(d, risk, sg, 0.0, H)      // target first within H (unconditional)
   float pL   = f_raceH(risk, d, sg, 0.0, H)      // opposing pool first within H
   [inv, d / risk, pInf, pW, pL]
   ```
   Update both call sites (Pine needs every tuple element named):
   - 1428: `[inv, rr, pR, pW0, pL0] = f_invalidation(lv)`;
   - 2127: `[i0, i1, i2, i3, i4] = f_invalidation(activeLv)`.
2. STATE (1079):
   - `raceSt` grows from 7 to 8 entries; index 7 = Σ p(1 − p) over decided races;
   - new `var array<float> rrSt = array.new<float>(12, 0.0)` holding [n, ΣR, ΣR²] × 4 R:R buckets (< 1, 1-2, 2-4, ≥ 4);
   - helper `f_rrB(float rr) => rr < 1.0 ? 0 : rr < 2.0 ? 1 : rr < 4.0 ? 2 : 3`.
3. `f_book` (1461-1499): inside `if t.race != 0`, add `raceSt.set(7, raceSt.get(7) + t.pRace * (1.0 - t.pRace))`. After `rOut` is final:
   ```pine
   int b = f_rrB(t.rr0) * 3
   rrSt.set(b, rrSt.get(b) + 1.0)
   rrSt.set(b + 1, rrSt.get(b + 1) + t.rOut)
   rrSt.set(b + 2, rrSt.get(b + 2) + t.rOut * t.rOut)
   ```
4. Readouts (2127-2130):
   - `invWin := f_raceAdj(i2)`. This equals BE until the ledger has decided races; after that BE is shifted by the learned edge;
   - `invBE := 1.0 / (1.0 + i1)`;
   - `invDec := i3 + i4` (share of races decided within H);
   - `float evL = raceSt.get(0) >= 30 ? (invWin - invBE) * (1.0 + i1) : na` (algebraically equal to `invWin·RR − (1 − invWin)`).
5. HUD line (2246): `"R:R 1.8 · BE 36% · WIN 38% · EV +0.06R"`. While `raceSt.get(0) < 30`, show `"EV —"`.

   Add one line (Normal/Large HUD): `"LEDGER R:R 1-2 · avg +0.03R ±0.10 · n 57"`, from `rrSt` of the active bucket, with SE = √((ΣR²/n − mean²)/n).
6. Panel (2358-2363): col 1 `R:R`, col 2 `BE 36 · WIN 38%`, col 3 `EV +0.06R` (colour by sign only when n ≥ 30).

   Full view RACE row (2422-2425): replace "WIN %" with `"EDGE " + f_signed(100*(wins − Σp)/n, "0.0") + "pp z " + z`, where z = (wins − Σp)/√Σp(1−p).
7. Tooltip: "Under a random walk every stop/target pair breaks even: P(target first) = risk/(risk + reward). WIN is that breakeven rate shifted by what this chart's past targets actually did. EV is (WIN − BE) × (1 + R:R)."

**Value to a trader.** EV stops lying about far targets. WIN vs BE answers "is this trade worth taking here?". The ledger bucket gives an out-of-sample realized number for trades like this one.

**Ledger-measurable.** Yes: the race edge z-score and the R:R-bucket realized R.

**Evidence.** Strong: the optional stopping theorem; Kaminski & Lo 2014. Moderate: T2 and T4-B.

**Risk.** EV reads "—" or near zero for most targets until the ledger has 30 decided races. That is honest and expected; explain it in the tooltip. QPOT-01 (`quant_pot.md`) removes drift elsewhere; TM-1 needs it only in `f_invalidation`.

**Effort.** S.

### TM-2 (P1, M) · Frozen trade plan with live progress, time left and status

**Why.**
- The HUD's R:R / WIN / EV are recomputed from the live close every tick (2127), so they jump and describe no trade anyone took.
- The ledger grades a bracket frozen at activation (1426-1431).
- Traders need a stable plan (entry reference, stop, target, horizon) and its state. The disposition effect (Odean: PGR 0.148 vs PLR 0.098) is why pre-committed, visible plans matter.

**Spec.**
1. At render (2111-2130): find the open trial for the active DOL. This is O(openT) ≤ 64:
   ```pine
   Trial aT = na
   for t in openT
       if t.lvId == activeId
           aT := t
           break
   ```
   Use `aT.entry`, `aT.inv`, `aT.rr0`, `aT.risk`, `aT.bar0`, `aT.atr0`, `aT.mae`, `aT.race` instead of re-running `f_invalidation` for the plan lines. Keep the live race (TM-1) as a secondary "from here" readout.
2. Derived live values (last bar; cheap):
   - `float prog = aT.side * (close - aT.entry) / aT.risk` (live R);
   - `float heatR = aT.mae * aT.atr0 / aT.risk`;
   - `int left = H - (bar_index - aT.bar0)`;
   - PoT over the remaining window: `pLeft = activePoT * f_pot(d, sig, 0, left) / math.max(f_pot(d, sig, 0, H), 1e-6)`. This is the analytic ratio, because the empirical surface is fixed at H; floor `left` at 1.
   - ETA clock: `str.format_time(time + int(etaHit * timeframe.in_seconds() * 1000), "HH:mm", tz)`, prefixed "≈" (sessions and weekends make it approximate).
3. HUD block (Terminal; Clean behind a new input `cleanPlan` default false, as a third label line):
   ```
   PLAN  ref 18452.25 · stop 18410.00 · R:R 1.8 · BE 36%
   NOW   +0.42R · heat 0.31R · 18/30b · PoT(left) 41% · ETA≈14:35
   ```
   Status prefix from `aT.race`:
   - `1` → `✓ TARGET FIRST`;
   - `-1` → `✕ OPP. POOL FIRST · draw failed`. The level can still be hit later; the PoT ledger grades that separately;
   - `left <= 0` → `⌛ WINDOW ENDED`. A new window opens on the next confirmed bar (2038-2045).
4. Lines: plan reference (dotted, cText at 60%) and stop (dotted, cIBear at 40%) from `f_x(aT.bar0)` to `xR`. This replaces the live invalidation line at 2210-2213 when `showInv`. Budget: 2 lines + 1 label.
5. Data window: `plot(planInv, "DOL Plan Stop", display = display.data_window)` and `plot(planRR, "DOL Plan R:R", ...)`. Alert placeholders can then reference them (TM-5).

**Value to a trader.** Numbers stop moving; the chart shows the plan that is being graded and where it stands. It also answers "how much time is left" and "is the thesis dead".

**Ledger-measurable.** It *is* the ledger record. No new statistics are needed.

**Evidence.** Moderate. The display/ledger mismatch is a fact (1426-1431 vs 2127); P11 supports pre-commitment. Time stops are EV-neutral (T4-B), so "time left" is information, not advice.

**Risk.** Two R:R numbers (plan vs from here) can confuse. Default to showing the plan; put the from-here race in the tooltip. Labels must survive the 5000-bar clamp (`f_x`).

**Effort.** M.

**Interaction.** `smc_impl.md` SMC-2 (target lock) and `competitors.md` COMP-5 (outcome stamps) are complementary. The status stamps here can feed COMP-5's ghost stamps.

### TM-3 (P2, M) · Path map: next obstacles as TP1 candidates, graded by the ledger

**Why.**
- Traders scale out at the first liquidity or opposing array on the path. The engine knows these levels (pool entries with `side == tgt.side` nearer than the target) but never shows them.
- Evidence says obstacles do not change target-first odds beyond distance: residuals −0.018 vs −0.019 and −0.025 vs −0.024 for inner pools; −0.025 vs −0.008 and −0.026 vs −0.021 for opposing FVGs (T4-B).
- So the engine should *show* them, not penalise targets for them. Partials cut the sd of R by 16-17% with no reliable mean effect (T4-A). The ledger should measure that per chart.

**Spec.**
1. Helper (STATE HELPERS, after `f_invalidation`). Pool size is ≤ 80 and nMax ≤ 2, so the cost is O(pool):
   ```pine
   f_obstacles(Level tgt, int nMax) =>
       array<int> out = array.new<int>()
       float dT = tgt.distance(close)
       for k = 1 to nMax
           int   bI = -1
           float bD = 1e100
           for [i, lv] in pool
               if lv.side == tgt.side and lv.id != tgt.id and not out.includes(i)
                   float dd = lv.distance(close)
                   if dd >= 0.25 * atr and dd < dT - 0.10 * atr and dd < bD
                       bD := dd
                       bI := i
           if bI >= 0
               out.push(bI)
       out
   ```
   For a buy-side target this returns, nearest first, both inner BSL pools and bearish FVG/OB/breakers above price, because all have `side == 1`.
2. Inputs (`G_DOL`):
   - `int obsN = input.int(1, "Path Obstacles", minval = 0, maxval = 3)`. Default 1 in Terminal style; the Clean label stays 2 lines unless `cleanPlan`.
   - `bool obsClean = input.bool(false, "Obstacles in Clean style")`.
3. Rendering (inside 2201-2248): for each obstacle, a dotted tick line from `bar_index` to `xR` at `lv.nearEdge()` and a tiny label `"TP1 · " + f_shortName(lv.kind, lv.src) + " · " + str.tostring(dd / risk, "0.0") + "R · " + str.tostring(f_potModel(dd, lv.side, 0.0) * 100, "0") + "%"`. Budget: ≤ 3 lines + 3 labels.
4. Ledger:
   - `Trial` gets `float tp1 = na`, `bool tp1Liq = false`, `bool tp1Hit = false`, `int tp1Bar = -1`, `bool beHit = false`;
   - `f_openTrial` sets tp1 = the first obstacle's near edge at activation;
   - in `f_step`, before the race update, use the same hit rules and the same `advFirst` ordering:
     ```pine
     if not na(t.tp1) and not t.tp1Hit and t.race == 0
         bool h1 = t.tp1Liq ? (t.side == 1 ? high > t.tp1 : low < t.tp1) : (t.side == 1 ? high >= t.tp1 : low <= t.tp1)
         if h1 and not (stp and advFirst)
             t.tp1Hit := true
             t.tp1Bar := t.bars
     if t.tp1Hit and t.race == 0 and t.bars > t.tp1Bar and (t.side == 1 ? low <= t.entry : high >= t.entry)
         t.beHit := true
     ```
   - in `f_book`:
     `rP = t.tp1Hit ? 0.5 * math.abs(t.tp1 - t.entry) / t.risk + 0.5 * (t.race == 1 ? t.rr0 : t.beHit ? 0.0 : t.rOut) : t.rOut`;
   - accumulate `tpSt = [n with TP1, TP1-before-stop count, ΣR, ΣR², ΣrP, ΣrP²]`.
5. Full panel row: `TP1 1ST 58% | PART +0.01R sd 0.84 | FULL −0.01R sd 1.01`.

**Value to a trader.** Shows where price must go first, the natural place to scale out, and this chart's measured record of doing so.

**Evidence.** Moderate. Obstacles are "priced by distance" (T4-B); partials reduce dispersion (T4-A); P8. **Do not** add an obstacle penalty to `evaluate()`.

**Risk.** Clutter. Defaults are Terminal-only with one tick. The f_step ordering must mirror the race rule exactly.

**Effort.** M.

### TM-4 (P2, M) · Entry zone with fill probability and R:R from the zone

**Why.**
- ICT traders enter on a retracement into a draw-aligned array (FVG / OB / breaker / iFVG) between price and the stop, not at market.
- The engine treats arrays only as targets.
- The geometric fill law d/(d + e) is calibrated: 0.735 predicted vs 0.696 observed (5-min, with 4% expired); 0.774 vs 0.752 (1h).
- 20-26% of setups ran to the target without filling (T4-A).
- A trader needs both numbers: the better R:R and the chance of missing the move.

**Spec.**
1. Helper:
   ```pine
   f_entryZone(Level tgt, float inv) =>
       int   bI = -1
       float bE = 1e100
       for [i, lv] in pool
           // a draw-aligned array on the far side of price: buy-side target -> bullish FVG/OB/BRK below price
           bool polar = tgt.side == 1 ? (lv.kind == 2 or lv.kind == 4 or lv.kind == 6) : (lv.kind == 3 or lv.kind == 5 or lv.kind == 7)
           if polar and lv.side == -tgt.side
               float e = lv.distance(close)                  // close - top (long)
               bool  inside = tgt.side == 1 ? lv.top > inv + 0.1 * atr : lv.bottom < inv - 0.1 * atr
               if e >= 0.10 * atr and inside and e < bE
                   bE := e
                   bI := i
       bI
   ```
   Also consider `ifvgs` zones with `dir == tgt.side` and the zone beyond price. Compare their near-edge distance the same way. Zone is a Zone, not a Level: handle it with a parallel loop that returns an index flag.
2. Numbers (last bar):
   - `e` = distance to the zone's near edge; `d = tgt.distance(close)`; `r = |close − inv|`;
   - `pFill = d / (d + e)`;
   - `rrZ = (d + e) / math.max(r - e, 0.25 * atr)`;
   - `beZ = 1 / (1 + rrZ)`.
3. Render:
   - re-draw the zone's box with a dotted border in the draw colour at 55%, from its anchor to `xR`;
   - tiny label `"ENTRY · BUFVG · fill 72% · R:R 2.4 · BE 29%"`;
   - Clean: only with `cleanPlan`;
   - budget: 1 box + 1 label.
4. Ledger (optional second stage). A limit trial: `Trial` fields `float limE = na`, `bool filled = false`, `bool missed = false`, `float pFill`.
   - In `f_step`, until filled: a target hit means missed (book to `fillSt`); touching `limE` means filled, and from then on the race runs from `limE` with the same `inv`.
   - Book fill rate vs Σ pFill, and win|fill vs Σ BE_zone. Panel: `FILL 70% (exp 73%) · WIN|fill 34% (BE 31%)`.

**Value to a trader.** It turns the DOL into an executable plan (where to get in, at what R:R) without overstating it.

**Evidence.** Moderate: the fill law in T4-A, and the martingale identity for win|fill.

**Risk.**
- The zone choice ("nearest" vs "best R:R") is a design choice; expose it as an input.
- Arrays the origin lockout (689-690) marks as "origin" are exactly the classic entry arrays. Allow them here (entry ≠ target).

**Effort.** M (S without the ledger stage).

### TM-5 (P2, S) · Execution alerts with a trade-plan payload

**Why.**
- Alerts today carry tag, price, score and PoT only (2079-2093). There is no stop, R:R, BE, TP1, entry or time left.
- There are no events for the decisions a trader takes after entry.
- `competitors.md` COMP-2 specifies the alert framework (event toggles, JSON, `{{plot()}}`). This proposal adds the plan fields and four plan events to it.

**Spec.**
1. Events, all on `barstate.isconfirmed` with `alert.freq_once_per_bar_close` except where noted:
   - **Entry Zone Tapped** (TM-4): `tgt.side == 1 ? low <= zoneTop : high >= zoneBot` while the DOL is active. An optional live variant uses `alert.freq_once_per_bar`.
   - **TP1 Reached** (TM-3): the active trial's `tp1Hit` flips to true on this bar.
   - **Opposing Pool Taken**: the active trial's `race` flips to −1 on this bar ("draw failed; target PoT now X%").
   - **Plan Window Ended**: the active trial is booked with `status == 3`.
   - Track flips with per-trial `bool` fields (`tp1Ann`, `invAnn`) so each fires once.
2. Payload: extend COMP-2's JSON with
   `"entry_ref","stop","tp1","target","rr","be","win","ev_ledger","n_ledger","pot","pot_left","bars_left","eta_bars","zone_top","zone_bot","p_fill"`.
   Text mode: `"DOL ▸ OPP. POOL TAKEN · BSL 18530.00 · stop 18410.00 hit · plan R −1.0 · NQ1!"`.
3. `alertcondition` (const messages) for the four events, titles fixed, embedding `{{plot("DOL Plan Stop")}}` and `{{plot("DOL Plan R:R")}}` (TM-2 plots; display.data_window plots are allowed, `competitors.md` 1.7).
4. Toggles: `alPlan` default false, so the user's 20-alert budget is not consumed by default.

**Value to a trader.** Trade management from alerts, with machine-readable fields for journals and bots.

**Evidence.** Weak (practitioner conventions; COMP-2 sources). **Risk.** Alert noise; defaults off. **Effort.** S (on top of COMP-2).

### TM-6 (P3, S) · Stop-distance expectancy curve from the ledger ("shadow stops")

**Why.**
- Traders ask "where should my stop be?". Under a random walk the answer is "nowhere is better" (Kaminski & Lo).
- If the engine's DOL selection has real edge, it shows up as a positive realized expectancy at some stop distances.
- The ledger already keeps the needed sufficient statistics per trial: `t.mae` (MAE until the hit or H, in ATR at entry) and `t.d0`, plus one new number, the mark-to-market at H.
- For any stop s, the bracket outcome is exact up to the intrabar rule: stopped iff `mae ≥ s`, because MAE is monotone in time.

**Spec.**
1. `Trial` gets `float endA = 0.0`. In `f_step`, when `status == 3`: `t.endA := t.side * (close - t.entry) / t.atr0`.
2. STATE: `var array<float> sgSt = array.new<float>(11, 0.0)` holding [ΣR, ΣR²] × grid `array.from(0.5, 1.0, 1.5, 2.0, 3.0)` ATR, with index 10 = n. The count must live in the array: a Pine function cannot reassign a global variable (language/user-defined-functions.md:32), but it can modify a global array.
3. `f_book`:
   ```pine
   sgSt.set(10, sgSt.get(10) + 1.0)
   for [k, s] in array.from(0.5, 1.0, 1.5, 2.0, 3.0)
       float r = t.mae >= s ? -1.0 : t.status == 1 ? t.d0 / s : t.endA / s
       sgSt.set(2 * k, sgSt.get(2 * k) + r)
       sgSt.set(2 * k + 1, sgSt.get(2 * k + 1) + r * r)
   ```
4. Full panel: `STOP·ATR 0.5 −0.03 | 1 +0.01 | 1.5 +0.04 | 2 +0.02 | 3 0.00 (n 140)`. Mark a cell when |mean| > 2 SE. Next to it, show the heat p80 in R (convert the existing p80 MAE).

**Value to a trader.** An empirical, per-chart answer to stop placement, and an honest demonstration of when no stop is "magic".

**Ledger-measurable.** That is all it is.

**Evidence.** Moderate. Strong theory (P1, P2); practitioner MAE method (P9); our winners' MAE p80 = 0.58-0.60R.

**Risk.**
- Small stops have high R variance; show SE.
- `mae` for hits after an early stop-out includes post-stop excursions. For s ≥ that MAE the trial counts as stopped, which is correct.

**Effort.** S.

### TM-7 (P3, S) · Invalidation semantics and modes: race barrier, post-raid extreme, protected swing

**Why.**
- T3: once the opposing pool is traded through, a stop 0.3 ATR beyond it is hit 64-70% of the time on that very bar and 92-95% within 12-30 bars.
- Random levels give 57-62% / 90-93%.
- The rejected sweep's wick is exceeded later 76-82% of the time (random levels: 78-81%).
- So the "invalidation" is a race barrier: "if this trades first, the draw failed". The label should say so.
- ICT traders' stop after a raid is the raid's extreme. Its R:R differs, but its odds match geometry (T4-A: win − model +1.2 pp (SE 1.9) and −2.7 pp (SE 1.5)).
- Offering the mode aligns the plan with how the user trades, without claiming edge.

**Spec.**
1. Relabel: `"⊗ OPP. POOL"` (2212). Tooltip: "If this level trades before the target, the draw failed. Once a pool is swept, a stop this close is taken 9 times in 10."
2. Input `string invMode = input.string("Opposing Pool", "Invalidation", options = ["Opposing Pool", "Post-Raid Extreme", "Protected Swing"], group = G_DOL)`. Protected Swing is `ict_struct.md` ICTS-5; share one input.
3. Post-raid state:
   - `var float raidX = na`, `var int raidSide = 0`, `var int raidBar = na`;
   - in step 3 (1580-1582), when a liquidity pool is hit and `evt` is a rejection (`lv.side == 1 ? close < lv.price : close > lv.price`): `raidSide := lv.side`, `raidX := lv.side == 1 ? high : low`, `raidBar := bar_index`;
   - while `bar_index − raidBar <= raidWin` (input, default 20 bars), extend `raidX` with new extremes.
4. In `f_invalidation`, if `invMode == "Post-Raid Extreme"` and `raidSide == -tgt.side` and `bar_index - raidBar <= raidWin` and `raidX` is on the far side of `close`: `inv := raidX - tgt.side * buf`. Otherwise use the current rule.
5. The ledger grades whichever mode is active, through `f_openTrial`. Users can compare modes by switching (TM-6 shows per-stop expectancy).

**Value to a trader.** The stop and R:R match the trader's model, and the label tells the truth about what that stop means.

**Evidence.** Moderate (T3, T4-A, P3: stop beyond the sweep extreme was GBB's best variant but still unprofitable).

**Risk.** Changing the mode changes R:R and the ledger's race statistics. Reset them, or label them per mode (store the mode index on the Trial).

**Effort.** S.

### Considered and rejected
- **Score bonus for sweep → MSS → FVG alignment toward a target.** No edge over geometry (T4-A) or in public tests (P3, P4). ICTS-6 (`ict_struct.md`) can alert on the structure shift with its measured follow-through rate. That is the honest version.
- **Penalising targets with obstacles in the path.** Obstacles add no information beyond distance (T4-B). Proximity already prices them.
- **An automatic time-decay or time stop on targets.** EV-neutral (T4-B). Show the time left instead (TM-2).
- **Kelly / position-size readout.** With p from geometry, f* = 0. A ledger-based f* would need confidence intervals and would invite over-sizing.
- **Lower-timeframe intrabar resolution in `f_step`** (`request.security_lower_tf`). The engine rule is already right 88% of the time (T1). The remaining errors hit only same-bar double touches. Not worth a request or the loop time.
- **Fixed 2R / 3R targets.** R:R is a geometric choice and EV-neutral. The DOL is the target.

---

## 5. Notes for implementers

**Order of work.**
1. TM-1 first. It is a small, self-contained change to `f_invalidation`, `f_book` and two readouts, and it removes a wrong number.
2. TM-2 next. It reuses the open `Trial` and fixes the jumping numbers.
3. TM-3 and TM-4 share the "levels on the path" loop.
4. TM-5 depends on TM-2, TM-3 and TM-4 plus `competitors.md` COMP-2.
5. TM-6 and TM-7 are independent.

**Tuple changes.** `f_invalidation`'s return shape changes in TM-1, and in ICTS-3 if the opposing index is added. Edit lines 1428 and 2127 together.

**Do not reuse `raceSt` across semantic changes** (drift removal, invalidation mode). The learned shift would carry stale baselines. Reset the arrays when the mode input changes; they are `var`, so reloading the script resets them.

**Pine constraints checked.**
- `str.format_time(time, format, timezone)` exists (reference/str.md:177-183).
- `for [k, s] in array.from(...)` is the verified `for [i, x] in array` form (CONTEXT).
- All new state is `var` arrays or UDT fields.
- All new computation runs on `barstate.isconfirmed` (ledger) or `barstate.islast` (render).
- Drawing budget: at most +6 lines, +5 labels, +1 box per tick, well under the declared 500 (lines 30-31).
- **Globals in functions.** "The function cannot modify its declared parameters or any global variables" (language/user-defined-functions.md:32). Ledger counters touched inside `f_book`/`f_step` must be array elements (as `raceSt`/`cluSt` already are) or UDT fields. TM-7's `raidX/raidSide/raidBar` are assigned in the engine block at global scope (fine) and only *read* inside `f_invalidation`. They must therefore be declared in STATE (1020-1080), before the function.

**Non-repainting.** Plan values come from the trial frozen on a confirmed bar. Only "NOW" fields (progress, PoT(left)) are live, like the existing PoT readout.

**Measurement.** Each proposal adds a ledger statistic: race EDGE z, R:R-bucket realized R, TP1-first rate and partial R, fill rate vs Σ pFill, the stop curve. Check before/after on NQ, ES, EURUSD, XAU and BTC at 15m and 1H.

---

## 6. Sources

**Published / web** (accessed 2026-11-23; WebFetch to most hosts was blocked, so figures come from search-engine summaries of these pages; peer-reviewed numbers were cross-checked against sibling studies):
- Kaminski, K. & Lo, A. (2014). When do stop-loss rules stop losses? J. Financial Markets 18:234-254. https://dspace.mit.edu/handle/1721.1/114876 ; https://econpapers.repec.org/RePEc:eee:finmar:v:18:y:2014:i:c:p:234-254 ; WP https://ideas.repec.org/p/hhs/sifrwp/0063.html
- Lo, A. & Remorov, A. (2017). Stop-loss strategies with serial correlation, regime switching, and transaction costs. J. Financial Markets 34:1-15. https://dspace.mit.edu/handle/1721.1/107017
- López de Prado, M. (2018). Advances in Financial Machine Learning, ch. 3 (triple barrier, meta-labelling). Summaries: https://hudsonthames.org/does-meta-labeling-add-to-signal-efficacy/ ; https://open-quant.github.io/openquant/modules/labeling
- Osler, C. (2000). Support for resistance. FRBNY EPR 6(2). https://www.newyorkfed.org/medialibrary/media/research/epr/00v06n2/0007osle.html
- Osler, C. (2003). Currency orders and exchange-rate dynamics. J. Finance 58(5). https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr125.pdf
- Osler, C. (2005). Stop-loss orders and price cascades. JIMF 24(2). https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr150.pdf
- Odean, T. (1998). Are investors reluctant to realize their losses? J. Finance 53(5). Summary: https://rpc.cfainstitute.org/-/media/documents/article/cfa-digest/1999/dig-v29-n2-469-pdf.pdf
- ICT Silver Bullet tests:
  - https://www.backtestingmax.com/backtests/ict-silver-bullet
  - https://dev.to/moonthetrain/ict-trading-strategy-backtest-79-setups-on-es-and-nq-d4o
  - Silver Bullet [GBB]: https://www.tradingview.com/script/teL2dDvS-Silver-Bullet-GBB/
  - https://es.tradingview.com/script/SuBXi3p8-ICT-Silver-Bullet-Backtest/
  - 16-year / 25,000-variant study (video summary): https://gist.ly/youtube-summarizer/i-backtested-25000-ict-silver-bullet-trades
  - vendor claims (not relied on): https://takeprofitapp.com/en/learn/ict-silver-bullet-strategy
- ICT FVG and bot tests:
  - https://backtrex.com/en/backtests/ict-kill-zone-fvg-gbp-usd
  - https://offbeatforex.com/is-ict-strategy-profitable/
- FVG placebo control: https://de.tradingview.com/script/Kbq3WncE-Fair-Value-Gap-FVG-Statistics-with-Placebo-Control/
- 2022 model rules:
  - https://www.luxalgo.com/library/concept/model-2022/
  - https://in.tradingview.com/script/FK960gz8-2022-Model-ICT-Entry-Strategy-TradingFinder-One-Setup-For-Life
- Unicorn / breaker:
  - https://www.luxalgo.com/blog/ict-unicorn-model-strategy-how-to-use/
  - https://www.tradingview.com/chart/XAUUSD/zb6bDQzM-The-Unicorn-Model-Guide-to-ICT-s-Best-Standalone-setup
- iFVG model rules:
  - https://www.tradezella.com/strategies/ifvg-trading-model
  - https://pl.tradingview.com/chart/BTCUSDT.P/L39WTf6H-Inversion-Fair-Value-Gaps-IFVGs-A-Deep-Dive-Trading-Guide
- Sweep depth (practitioner):
  - https://www.tradingview.com/script/FRKI2rGw-Liquidity-Sweeps-Stop-Depth-Rider-Algo/
  - https://raw.githubusercontent.com/yeboster/liquidity-sweep-freqtrade/main/README.md
- MAE / MFE:
  - https://nexusfi.com/wiki/trading-wiki/MAE
  - https://www.mql5.com/en/articles/23245
  - https://www.luxalgo.com/library/concept/mae-mfe-distributions.md
  - https://completetradersedge.com/maximum-adverse-excursion/
- Scaling out:
  - https://enlightenedstocktrading.com/trend-following-profit-targets-do-they-work
  - https://www.luxalgo.com/library/concept/scaling-out/
  - https://medium.com/trading-and-investing/why-scaling-out-of-positions-could-send-you-broke-4f6d01adac08
- Time stops:
  - https://www.tradesviz.com/glossary/time-stop/
  - https://flashalpha.com/articles/when-to-exit-short-options-take-profit-stop-loss-backtest
- Expectancy / SQN:
  - https://www.tradesviz.com/glossary/system-quality-number/
  - https://www.luxalgo.com/library/concept/sqn/

**Local:**
- Pine v6 docs: concepts/strategies.md:124-135 (broker emulator); reference/core.md:57 (`alert()` freq); reference/constants.md:13-15; reference/str.md:177-183 (`str.format_time`). Mirrors under `scratchpad/docsrc/`.
- Sibling studies:
  - `quant_pot.md` (QPOT-01 drift, QPOT-05 ETA, QPOT-06 next-liquidity race, QPOT-09);
  - `ict_struct.md` (ICTS-3 race in the Clean label, ICTS-5 protected-swing stop, ICTS-6 MSS alerts);
  - `ict_pd.md` (FVG/iFVG controlled evidence);
  - `academic_sr.md` (Osler, Chung & Bellotti);
  - `competitors.md` (COMP-2 alerts, COMP-5 stamps);
  - `smc_impl.md` (SMC-2 lock);
  - `price_action.md` (traders' equation).

## 7. Reproduction
```
cd /tmp/claude-0/-home-user-m/7ce60006-3639-59b1-8cd3-87355409d58a/scratchpad/brief/study/trade_tools
python3 -I t1_order.py $(pwd)            # T1 intrabar order (about 3 s)
python3 -I t2_ev.py $(pwd)               # T2 EV readout under a fair market
python3 -I t34.py $(pwd) 5min            # T3 + T4 on CME 5-min with 1-min path (about 10 s) -> res_5min.pkl
python3 -I t34.py $(pwd) 1h              # T3 + T4 on CME 1h + BTC 1h (about 15 s)       -> res_1h.pkl
python3 -I analyze.py $(pwd) 5min        # tables -> out_5min.txt
python3 -I analyze.py $(pwd) 1h          # tables -> out_1h.txt
```
Data come from sibling folders: `amt_data/cme/*` (1-min and 1h CME) and `classic_tools/btc_1h.csv`. Nothing is downloaded.
