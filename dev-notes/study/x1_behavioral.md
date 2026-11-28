# x1_behavioral · Behavioural finance and crowd reflexivity of liquidity

Domain: the behavioural mechanisms that decide **where orders rest and whose stops get run**, and the cognitive biases of the indicator's own user.
- Disposition effect, reference (cost-basis) prices and capital-gains overhang (Shefrin & Statman; Odean 1998; Kaustia 2010; Grinblatt & Han 2005; Frazzini 2006).
- Intraday futures traders: Locke & Mann 2005; Coval & Shumway 2005; Choe & Eom 2009.
- Break-even supply and "trapped traders" after failed breakouts.
- Cost-basis distributions: anchored VWAP, a turnover-decayed reference price, crypto realised price and in/out-of-the-money maps.
- Attention and salience (Barber & Odean 2008; Yuan 2015; round numbers).
- Herding and retail flow (Robinhood, social trading, micro futures).
- **Reflexivity of the SMC/ICT crowd**: did crowding since about 2020 change how liquidity levels behave? Tested pre-2019 vs post-2021 on the same instruments.
- The user's own biases that `ux_design.final.md` does not already cover: automation bias, outcome / hindsight bias from reached-target stamps, overreaction to live PoT ticks.

Engine studied: `brief/baseline_v2.pine` (line numbers below refer to it; identical to `indicators/dol_engine.pine`).

**Evidence grades.** strong = peer-reviewed or large replicated quantitative study; moderate = published or reproducible numbers; weak = practitioner consensus or a small / vendor sample; none = folklore. Whether evidence **supports**, is **null on**, or **contradicts** a claim is stated separately from its grade.

**Research-tool note.** The Firecrawl allowance was exhausted on the first call, and WebFetch could not resolve papers' hosts (arxiv.org, nber.org, faculty pages are outside this session's network). All literature numbers below come from WebSearch result summaries of abstracts and publisher/index pages (sources listed in §7). Where a number came only from a secondary page or from memory of the paper, it is marked **[not re-verified]**. The original tests (§2.2) ran on local data only; scripts and raw outputs are in `study/x1_beh_tools/`.

---

## 0. Executive summary

1. **The SMC/ICT crowd has not measurably changed how liquidity levels behave.** Same-instrument, engine-faithful test (pivLen 5 pools, strict trade-through, era-internal distance-matched baselines), pre-2019 vs post-2021, on BTC 1h (2017-18 vs 2021-22 and 2023-24), EURUSD 1h (2017-18 vs 2024-26) and SPX daily (1999-2008, 2009-2018 vs 2021-26):
   - **Reach beyond distance**: unchanged. Post minus pre: BTC +2.3 ± 1.6 and +1.3 ± 1.2 pp; EURUSD −0.1 ± 2.3 pp; SPX −2.9 ± 4.0 pp. The SPX placebo (2009-18 minus 1999-2008, no SMC crowd in either) is −2.1 ± 3.6 pp, the same size.
   - **Sweep depth** (median penetration of the first trade-through bar, ATR): BTC 0.63 → 0.63 / 0.72; EURUSD 0.53 → 0.54; SPX 0.37 / 0.31 → 0.34. **Stops have not moved further away.** Equal-high/low (the most "obvious") pools were swept *less* deeply after 2021 on BTC (1.18 → 0.76 / 0.70 ATR, z −1.5), the opposite of the "deeper micro-sweeps" hypothesis.
   - **Front-running** (the share of close approaches, within 0.25 ATR, that fail to trade through, against a matched empty-space control): no increase. BTC levels were passed *more* often after 2021 (stall −1.2 → +3.1 / +2.3 pp); EURUSD −2.1 → −2.6 pp.
   - **Post-sweep behaviour**: the share of sweeps that close back inside moved in **opposite directions** by market (BTC 41.5% → 46-50%, z +2.6 / +4.7; EURUSD 50.0% → 36.8%, z −5.8; SPX 44% → 40%, z −0.7). There is no common era effect, so nothing an "era prior" could encode.
   - Reading: ICT labels had no distance-adjusted edge **before** the crowd arrived (consistent with `ict_liq`), so there was nothing for crowding to decay (contrast McLean & Pontiff: published anomalies lose about 32-58% of their returns after publication). **Do not build era-aware priors.** A cheap drift monitor on the ledger (X1B-5) covers the residual risk.
2. **Cost-basis levels are not magnets beyond what time-averaging already gives.**
   - A swing-anchored VWAP (the average cost of everyone who traded since the last confirmed swing) is reached exactly as often as distance implies: NQ 15m −0.5 / −0.6 ± 0.5 pp (n ≈ 11,500 each side), NQ 1h +0.7 / −0.4 ± 1.0 pp, SPX daily −1 to −4 ± 2-4 pp. A time-weighted placebo from the same anchor gives the same numbers.
   - Price *does* stall slightly near both averages (−2 to −3 pp vs a push-bar control), but the volume-weighted (cost-basis) line stalls no more than the time-weighted line: −0.6 ± 0.5 pp (15m), +0.1 ± 1.0 pp (1h).
   - With `classic_levels` (session VWAP +1.5 pp, weekly / monthly AVWAP null or negative), the conclusion is: **no VWAP or cost-basis family as targets.**
3. **A turnover-decayed reference price (Grinblatt-Han capital-gains overhang) tilts which side is taken first only as much as trend does.** NQ 15m: lowest CGO quintile −3.7 ± 1.6 pp (sell-side first more than geometry), highest +3.5 ± 1.7 pp. Within the same trend stratum the effect mostly disappears, and on NQ 1h and SPX daily there is no monotone pattern. It is a momentum proxy, not a new draw input.
4. **"Trapped trader" break-even supply at failed-breakout levels is market-specific.** When price returns to a level whose sweep closed back inside, it stalls more than empty space on EURUSD (−6.8 ± 3.7 pp pooled) but less on BTC (+2.4 ± 1.3 pp). Grade the feature per chart; never score it by default.
5. **The live PoT readout moves a lot inside a single bar.** With the engine's analytic model on NQ 1m paths inside 1h (15m) bars:
   - the median intrabar range of the live PoT is **10.9 (10.2) pp**, the 90th percentile **26.4 (25.0) pp**;
   - the readout crosses 70% inside **27% (22%)** of bars and crosses 50% inside 18%.
   - Field evidence on professional traders says frequent outcome feedback lowers risk-taking and profits (Larson, List & Metcalfe: infrequent price information → +33% risky investment, +53% profits; Gneezy & Potters 1997; Haigh & List 2005: CBOT pros show *more* myopic loss aversion than students). **Anchor the readout to the bar-close value** (X1B-2).
6. **The default Clean style shows a confident "PoT: 70.1%" with no reliability cue.** The ledger computes HIT %, EDGE z and a verdict (2380-2392), but only the Terminal panel shows them. Automation-bias research (Goddard et al. 2012, 74 studies) shows that decision aids without reliability information lead users to follow wrong advice; continuously updated confidence information improves trust calibration (McGuirl & Sarter 2006). **Show the ledger state on the Clean label in the two states that matter: "calibrating" and "no measured edge"** (X1B-1).
7. **The chart's visual record over-represents hits.** Replaced targets vanish silently: a ghost is drawn only when the target became ineligible (2021-2023), not when a challenger wins or the score sags. Ghosts are off by default anyway. Outcome bias (Baron & Hershey 1988, replicated 2023) and hindsight bias (Biais & Weber 2009: more hindsight-biased bankers underestimate volatility and perform worse) predict that users will overrate the tool from what they remember seeing. Make misses as visible as hits (X1B-3).
8. **What the disposition literature *does* justify is already in the engine's geometry.** Break-even and loss-averse behaviour concentrate orders at prior extremes, round numbers and cost bases. The engine already places pools at extremes with strict trade-through, and the measured reach of those pools is fully explained by distance. Behavioural features belong in the **shadow ledger as discovery bits** (X1B-4), not in the score.

**Proposals (best first):** X1B-1 reliability cue on the Clean label (P1, S); X1B-2 live-PoT anchoring and a "PoT swing" readout (P1, S); X1B-3 outcome-symmetric visual record (P2, S); X1B-4 behavioural discovery bits in the shadow ledger: obviousness, trap level, cost basis (P3, M); X1B-5 drift monitor instead of era priors (P3, S); X1B-6 crypto on-chain cost basis as a shadow-graded family (P3, M).

---

## 1. Concepts (definitions and parameters)

Each concept gives a precise definition, the parameters that matter, how practitioners use it for WHERE / WHEN / HOW LIKELY, and its failure modes.

### 1.1 Disposition effect
- **Definition (Shefrin & Statman 1985).** Investors sell winners too early and ride losers too long, relative to their purchase price.
- **Measurement (Odean 1998).** Proportion of gains realised PGR = realised gains / (realised gains + paper gains), counted on each day a sale occurs. PLR is the same for losses. Disposition = PGR − PLR > 0.
  - Odean, 10,000 discount-brokerage accounts 1987-93: PGR 0.148 vs PLR 0.098, about 1.5× [numbers via a secondary page; not re-verified]. The effect held in every month except December (tax-loss selling).
- **The shape of the selling schedule (Kaustia 2010, JFQA 45(3)).** The propensity to sell **jumps at zero return** (the purchase price), stays roughly flat over a wide range of losses, and is flat or rising over gains. This is not prospect theory's V-shape. It is a break-even threshold.
  - **Algorithmic consequence.** If a cohort's cost basis is C, selling pressure from that cohort steps up when price returns to C from below (losers "get out even"). The break-even level is a *step*, not a gradient.
- **Futures and professionals.**
  - Locke & Mann (JFE 2005, CME floor traders): professional traders also hold losers longer and sell winners sooner; the authors found no contemporaneous measurable cost, and "discipline" is the practitioners' word for suppressing it.
  - Choe & Eom (J. Futures Markets 2009, KOSPI 200 futures): strong disposition effect, far stronger for individuals than institutions and foreigners, stronger in long than short positions, and negatively related to performance. Eom (2020): day traders are reluctant to close losing *day* trades.
  - Crypto: Schatzmann & Haslhofer (Digital Finance 2023; on-chain transfers to exchanges as a sale proxy): a disposition effect, varying over time, most evident from the 2017 boom-bust onwards.
- **Social amplification.**
  - Heimer (RFS 2016, myForexBook): joining a social trading network roughly **doubles** a trader's disposition effect; connected traders converge to similar levels.
  - Pelster & Hofmann (JBF 2018): becoming a followed "leader" trader increases the disposition effect (difference-in-differences).
- **DOL role (WHERE).** Disposition and break-even behaviour predict *where limit orders rest*: take-profits of winners just before obvious targets, break-even exits of losers at their entry. It does not, by itself, predict *which* level is reached first.
- **Failure modes.** Cost bases are unobservable on futures and FX (no account data); any proxy (VWAP, turnover decay) is an assumption about who holds what.

### 1.2 Reference price and capital-gains overhang (CGO)
- **Grinblatt & Han (JFE 2005).** A reference price R_t is the turnover-weighted average of past prices, with older purchases surviving only if they were not turned over since:
  - `R_t = (1/k) Σ_{n≥1} V_{t−n} Π_{τ=1}^{n−1} (1 − V_{t−n+τ}) P_{t−n}`, V = turnover (shares traded / shares outstanding), k normalises the weights.
  - `CGO_t = (P_{t−1} − R_t) / P_{t−1}`.
  - Result: CGO subsumes momentum in the cross-section; once it is controlled for, past returns no longer predict.
- **Frazzini (JF 2006).** Post-announcement drift is strongest when the news and the overhang share a sign: stocks with large unrealised gains underreact only to good news, those with large losses only to bad news. An event strategy earns over 200 bp/month alpha [abstract; net figures differ by source].
- **Bar-data proxy used here (T4).** A recursive volume-time EMA: `RP_t = (1 − w_t) RP_{t−1} + w_t · hlc3_t`, `w_t = min(1, vol_t / (N_turn · mean vol over 500 bars))`. N_turn is the average holding period in bars (tested 50 and 200 on 15m / 1h; 20 and 60 on daily). `CGO_t = (close − RP) / ATR`.
- **Pine v6.** Needs only `volume` and a `var float`. Exact Grinblatt-Han for stocks would use `syminfo.shares_outstanding_total` for turnover.
- **DOL role.** Draw-side tilt (which side's liquidity is taken first). **Measured: a trend proxy (T4).**
- **Failure modes.** Futures roll and session volume patterns distort w_t; CGO is collinear with trend.

### 1.3 Loss chasing within the day (Coval & Shumway 2005)
- **Finding (JF 60(1), CBOT Treasury-bond futures locals).** Traders with morning losses are about **16% more likely** to take above-average afternoon risk than those with morning gains. Their price-setting trades are less permanent: prices revert strongly within about **10 minutes**. Short-term afternoon volatility rises with the prevalence of morning losses; overall afternoon volatility does not.
- Murphy ("Do losses linger", working paper; professional stock traders): traders most influenced by morning losses perform far worse.
- **DOL role (WHEN).** Behavioural noise is real but short-lived and absorbed by other participants. At the engine's 15m-1h resolution it is invisible. **No feature proposed.**

### 1.4 Break-even effect and "trapped traders"
- **Break-even effect (Thaler & Johnson 1990, Mgmt Sci 36(6)).** After prior losses, gambles that offer a chance to break even become attractive. Futures-market evidence exists (Taiwan futures, Pacific-Basin Finance J. 2014; Sydney Futures Exchange locals, Frino et al. 2008) [abstracts not retrieved].
- **Trapped traders (practitioner, e.g. Brooks).** Breakout traders who bought a new high that immediately failed are "trapped". When price returns to their entry, they exit at break-even, supplying resistance at the failed-breakout level.
- **Algorithm used in T2 (trap-level stall).**
  1. A pool is swept (first strict trade-through) and the sweep bar **closes back inside** (REJECT).
  2. Store the level for 300 bars.
  3. Arm it once price has moved ≥ 0.5 ATR back inside.
  4. On the first later bar whose extreme comes within (0, 0.25] ATR of the level without trading through it, record whether price trades through within K = 10 bars.
  5. Compare with a push-bar control (bars whose high ≥ the previous 5 highs, a random level U(0, 0.25] ATR beyond, matched in five gap bins).
- **DOL role (WHERE).** A candidate resistance on the path to a buy-side target.
- **Measured: market-specific (T2).** Prior studies: failed-breakout reversal is geometry (`price_action`); RECLAIM as a D input −1.5 ± 0.7 pp with varying sign (`orderflow_micro`).

### 1.5 Cost-basis distributions
- **Anchored VWAP (Shannon).** `AVWAP_t = Σ_{i=a..t} tp_i v_i / Σ v_i` from an anchor bar a (swing, gap, earnings, week or month start); tp = hlc3. Practitioners read it as "the average cost of everyone who traded since the event". There is no peer-reviewed test of AVWAP as support / resistance (search result: vendor pages and indicator descriptions only).
  - **Swing-anchored version tested (T3).** Bull AVWAP from the last confirmed pivot low (recent buyers' cost), bear AVWAP from the last pivot high. Frozen at the checkpoint, so the moving-target bias is avoided. Placebo: ATWAP, the time-weighted average from the same anchor.
  - `classic_levels` already tested session VWAP (+1.5 pp, z 2.9 on CME, +0.3 BTC) and weekly / monthly AVWAP (null to −2.9 pp on BTC).
- **Crypto on-chain cost basis.**
  - *Realised price* = realised cap / supply, i.e. the average price at which each coin last moved. Since MVRV = market cap / realised cap, **realised price = price / MVRV**.
  - *Short-term-holder realised price*: the same for coins that moved within about 155 days. Analysts call it bull-market support; evidence is anecdotal (for example "reclaimed twice since 2023, each followed by ≥ 30%": a two-event sample).
  - *IntoTheBlock IOMAP*: addresses clustered by their weighted-average acquisition price within ±15% of price, classified in / at / out of the money. Large clusters are "expected" to act as support / resistance: an explicit behavioural assumption, untested in public.
  - **TradingView availability.** IntoTheBlock data is on TradingView under the `INTOTHEBLOCK:` prefix (for example a `BTC_BREAKEVENADDRESSES` symbol page exists; community scripts use `INTOTHEBLOCK:{TOKEN}_MVRV`). Glassnode data was announced under `GLASSNODE:` (community scripts use `GLASSNODE:{TOKEN}_MARKETCAP`). Exact tickers, plan requirements and granularity (daily) must be verified in the editor; use `ignore_invalid_symbol = true`.
- **Leverage-cohort cost basis (liquidation heatmaps).** Mostly *modelled*: assumed leverage tiers (10×/25×/50×/100×) applied to estimated entry prices, scaled to open interest. On-chain variants read actual liquidation prices from one venue (Hyperliquid, about 16% of global OI). No published accuracy test. Grade none-to-weak; see `x1_positioning` for OI and funding.

### 1.6 Attention and salience ("obviousness")
- **Barber & Odean (RFS 2008).** Individual investors are net buyers of attention-grabbing stocks (news, abnormal volume, extreme one-day returns). Attention affects *buying*, because buyers search thousands of names while sellers choose among the few they own.
- **Yuan (JFE 2015).** Market-wide attention events (Dow record highs, front-page market stories) make investors **sell** when the market is high; returns fall about **19 bp** on the following days.
- **Round numbers.**
  - Bhattacharya, Holden & Jacobsen (Mgmt Sci 2012; over 100 million trades): liquidity demanders buy one penny **below** and sell one penny **above** round numbers ("cluster undercutting" of limit orders resting at the round). Losses approach $1 billion a year.
  - Osler (2003, 2005; covered in `ict_liq` / `orderflow_micro`): stop-buys just above rounds, take-profits at them.
  - Urquhart (Econ. Letters 2017): over 10% of Bitcoin prices end in 00, with no return pattern after a round.
- **52-week and all-time highs.** George & Hwang 2004; Li & Yu 2012: the best-documented anchors. Already covered by `academic_sr` ACAD-6, not repeated here.
- **Operational "obviousness" score for a level** (used as discovery bits in X1B-4). A level is obvious when it is any of:
  - (a) an EQ pool (≥ 2 prints within 0.1 ATR);
  - (b) PDH/PDL/PWH/PWL;
  - (c) within 0.1 ATR of a round number (the step = 10^floor(log10(price)) / 10, e.g. 100 for NQ at 20,000);
  - (d) the most extreme high or low of the last 200 bars (what a default chart window shows);
  - (e) a swing that the most popular free SMC script would draw (LuxAlgo SMC default: swing size 50, where a swing high is `high[50] > ta.highest(high, 50)`; EQ detector 0.1 × ATR(200), pivots of length 3; see `smc_impl`).
- **DOL role.** Obvious levels are where the crowd's stops and limits rest, so they set sweep geometry. Whether they are *reached* more than distance implies is an empirical question, and the answer so far is no: EQ +0.3 pp (1H), `ict_liq`; PD ≈ 0 here (T1).

### 1.7 Herding and retail flow
- **Robinhood herding (Barber, Huang, Odean & Schwarz, JF 2022).** Herding episodes (the top 0.5% of jumps in Robinhood user counts per stock) are followed by negative abnormal returns: −4.7% over 20 days for the top stocks bought each day; about −9% for the most extreme events. The data run May 2018 to August 2020.
- **Retail share.** US equity retail volume share rose from under 12% (2018-19) to about 20% or more in 2020 to early 2021 (Virtu estimate, via CME). CME Micro E-mini equity futures (launched May 2019): 214 million contracts in year one, 527 million in year two.
- **0DTE, dealer gamma, crypto funding.** Covered in `x1_positioning`: dealer gamma is a volatility-state variable, 0DTE dampens rather than amplifies, crowded crypto funding has a +5.2 ± 2.1 pp buy-side-first effect.
- **DOL role.** These changes are the reason one might *expect* an era shift in level behaviour after 2020. T1 tests it directly.

### 1.8 Reflexivity of the SMC/ICT crowd
- **The hypotheses**, each operationalised in T1:
  - **H1, attraction.** More traders aim at the same EQH/EQL/PDH, so obvious pools are reached more than distance implies after 2020. Metric: reach excess M1 by class.
  - **H2, stops moved further.** Traders know "obvious stops get run" and place them deeper, so sweeps penetrate further. Metric: sweep depth M2.
  - **H3, front-running.** Profit-taking and fading move ahead of the obvious level, so price stalls just short of it more often. Metric: approach stall M4.
  - **H4, the stop-hunt-and-reverse pattern** became more or less common. Metric: REJECT share and post-sweep continuation M3.
- **Prior expectation from the anomaly literature.** McLean & Pontiff (JF 2016; 97 published cross-sectional predictors): average monthly return 0.582% in sample, 0.402% out of sample before publication, 0.264% after publication. The working paper states it as 26% lower out of sample and 58% lower after publication, a ≥ 32% publication effect. Crowding erodes real edges.
- **Self-fulfilling levels.** Osler (FRBNY 2000): firms' published S/R levels predict trend interruptions. Chung & Bellotti (arXiv 2101.07410, 2021): bounce probability at algorithmically found S/R levels rises with prior bounces and **decays over time** (level age, not calendar era).
- **Popularity timeline.** ICT's methods date from about 2016, and SMC spread on YouTube, Discord and TikTok around 2020-22. No quantitative popularity series was retrievable (search found only vendor claims), so "post-2021" is taken as the crowded era.

### 1.9 The user's own biases (not covered by `ux_design.final.md`)
- **Automation bias.** The tendency to over-rely on automated advice. It produces errors of commission (following wrong advice) and omission (not acting without a prompt).
  - Goddard, Roudsari & Wyatt (JAMIA 2012): systematic review, 74 of 13,821 papers. Mediated by experience, workload and time pressure. A secondary citation reports erroneous advice raising commission errors by about 26% [not re-verified].
  - Parasuraman & Manzey (2010) treat complacency and automation bias as overlapping forms of misuse [via Goddard].
  - **Mitigation.** Show *dynamic* reliability. In McGuirl & Sarter (Human Factors 2006, in-flight icing aid), pilots given continuously updated system confidence estimated the aid's accuracy more accurately and precisely, and performed better, than pilots told only its overall reliability.
- **Algorithm aversion** (Dietvorst, Simmons & Massey, JEP: General 2015, 5 experiments). After seeing a model err, people prefer a worse human forecaster. Showing misses *with their stated probability* keeps trust calibrated (COMP-5's framing).
- **Outcome bias** (Baron & Hershey, JPSP 1988, 5 studies; a pre-registered replication in 2023 succeeded). Decisions with good outcomes are rated as better thinking and more competent, even by subjects who say outcomes should not matter.
- **Hindsight bias** (Biais & Weber, Mgmt Sci 2009). 66 students: hindsight bias lowers volatility estimates. 85 investment bankers: more biased bankers have **lower performance**.
  - **Engine link.** "✕ SWEPT" stamps and ghosts of hits, with misses vanishing, feed both outcome and hindsight bias. The user remembers a tool that "always gets there".
- **Myopic loss aversion and overreaction to frequent feedback.**
  - Gneezy & Potters (QJE 1997; 12 rounds of an identical lottery): the more often returns are evaluated, the less is bet. About 51% vs 67% of the endowment [from memory of the paper; not re-verified].
  - Haigh & List (JF 2005; 54 CBOT pit traders vs students): professionals show **more** myopic loss aversion than students.
  - Larson, List & Metcalfe (NBER w22605, 2016; natural field experiment, 864,000 price realisations): professional traders who receive price information **infrequently** invest **33% more** in risky assets and earn **53% higher profits**.
  - **Engine link.** The live PoT is a P&L-like number updated every tick (2066-2068). T5 measures how much it moves.
- **Base rates for the user.** Chague, De-Losso & Giovannetti (2019/20; all 19,646 first-time day traders of Brazilian mini-index futures 2013-15): only 1.1% earned more than the minimum wage, with no evidence of learning. That is relevant to how confidently a target is presented.

---

## 2. Evidence (numbers and sources)

### 2.1 Literature table

| # | Claim | Source | Numbers | Grade | Direction for the DOL |
|---|---|---|---|---|---|
| L1 | Disposition effect (retail) | Odean 1998, JF 53(5) | PGR 0.148 vs PLR 0.098 [secondary]; no December | strong | where orders rest; not which level is hit |
| L2 | Selling jumps at break-even | Kaustia 2010, JFQA 45(3) | jump at zero return; flat over losses | strong | break-even is a step at cost basis |
| L3 | Professionals show disposition | Locke & Mann 2005, JFE 76(2) | CME floor traders; no measurable contemporaneous cost | strong | same |
| L4 | Futures individuals ≫ institutions | Choe & Eom 2009, JFM 29(6) | stronger in longs; hurts performance | strong | same |
| L5 | Social networks double it | Heimer 2016, RFS 29(11) | ≈ 2× after joining | strong | crowds amplify break-even behaviour |
| L6 | Leaders show more | Pelster & Hofmann 2018, JBF 94 | DiD increase | moderate-strong | same |
| L7 | CGO subsumes momentum | Grinblatt & Han 2005, JFE 78(2) | momentum vanishes given CGO | strong (stocks) | draw tilt; our T4: trend proxy |
| L8 | CGO × news drift | Frazzini 2006, JF 61(4) | > 200 bp/month alpha (gross) | strong (stocks) | — |
| L9 | Afternoon loss chasing | Coval & Shumway 2005, JF 60(1) | +16% risk-taking; 10-min reversal | strong | too short for 15m-1h |
| L10 | Break-even effect | Thaler & Johnson 1990 | lab; futures replications exist | strong (lab) | trapped-trader mechanism |
| L11 | Attention buying | Barber & Odean 2008, RFS 21(2) | net buying after attention | strong | salience of levels |
| L12 | Record-high attention selling | Yuan 2015, JFE 116(3) | −19 bp next days | strong | index-level only |
| L13 | Round-number undercutting | Bhattacharya et al. 2012, Mgmt Sci 58(2) | buys 1¢ below, sells 1¢ above; ≈ $1 bn/yr | strong | zones stop short of rounds (OF-4) |
| L14 | BTC round clustering | Urquhart 2017, Econ. Lett. 159 | > 10% of prices end in 00; no return pattern | moderate | — |
| L15 | Robinhood herding | Barber et al. 2022, JF 77(6) | −4.7% 20-day; ≈ −9% extreme | strong | retail era change |
| L16 | Retail share up | Virtu via CME | < 12% → ≈ 20% (2018-19 → 2020-21) | weak-moderate | retail era change |
| L17 | Anomaly decay after publication | McLean & Pontiff 2016, JF | 0.582 → 0.402 → 0.264 %/month | strong | crowding erodes real edges |
| L18 | S/R bounce decays with level age | Chung & Bellotti 2021, arXiv | qualitative (abstract) | weak-moderate | level age, not era |
| L19 | Automation bias | Goddard et al. 2012, JAMIA 19(1) | 74 studies; +26% commission errors [secondary] | strong (clinical) / weak (transfer) | reliability cue |
| L20 | Dynamic confidence improves calibration | McGuirl & Sarter 2006, Hum. Factors 48(4) | better accuracy estimates and performance | moderate | reliability cue |
| L21 | Algorithm aversion | Dietvorst et al. 2015, JEP:G 144 | prefer humans after seeing model errors | strong | show misses with stated PoT |
| L22 | Outcome bias | Baron & Hershey 1988; replicated 2023 | 5 studies | strong (lab) | symmetric outcome record |
| L23 | Hindsight bias hurts bankers | Biais & Weber 2009, Mgmt Sci 55(6) | n 85 bankers, n 66 students | moderate | symmetric outcome record |
| L24 | Frequent feedback hurts pros | Larson, List & Metcalfe 2016, NBER w22605 | +33% risk, +53% profit when infrequent | moderate-strong | anchor the live PoT |
| L25 | MLA in pit traders | Haigh & List 2005, JF 60(1) | pros > students | strong (lab) | same |
| L26 | Evaluation frequency | Gneezy & Potters 1997, QJE 112(2) | ≈ 51% vs 67% bet [not re-verified] | strong (lab) | same |
| L27 | Day-trader base rate | Chague et al. 2019/20 | 1.1% earn > min wage (n 19,646) | moderate-strong | honesty framing |
| L28 | STH realised price as support | CryptoQuant / Cointelegraph posts | 2 events since 2023 | weak | shadow-grade only |
| L29 | IOMAP clusters as S/R | IntoTheBlock docs | assumption, no test | none | shadow-grade only |
| L30 | Liquidation heatmaps | vendor docs | modelled; no accuracy test | none-weak | not built |
| L31 | AVWAP as S/R | vendor / indicator docs | no test | none | null in T3 |

### 2.2 Original tests (scripts in `study/x1_beh_tools/`)

**Common engine-faithful machinery.**
- Pivots: pivLen 5, strict left and non-strict right, confirmed 5 bars later.
- Pools: same-kind merge within 0.10 ATR (outermost print); strict trade-through sweep; ejection beyond 15 ATR; ATR(14) Wilder.
- Distance-matched baseline S(d): the share of **all** bars in the same era whose H-bar excursion exceeds d ATR. This is the engine's `f_potBase` idea, computed inside each era, so volatility and trend differences between eras are absorbed.
- Inference: block bootstrap over time blocks (500 bars intraday, 120 daily; 400 reps). Differences post − pre use SE = √(se₁² + se₂²).

#### T1 · Era test: pre-2019 vs post-2021 (`era_test.py`, outputs `out_era_{btc,eur,spx}.txt`)

| Metric | BTC 1h 2017-18 | BTC 2019-20 | BTC 2021-22 | BTC 2023-24 | EUR 1h 2017-18 | EUR 1h 2024-26 | SPX D 99-08 | SPX D 09-18 | SPX D 21-26 |
|---|---|---|---|---|---|---|---|---|---|
| Reach excess, all pools (pp) | −0.7 ± 0.8 | +1.0 ± 1.2 | +1.7 ± 1.4 | +0.6 ± 0.9 | −1.0 ± 2.0 | −1.1 ± 1.2 | +2.4 ± 2.7 | +0.3 ± 2.4 | −0.6 ± 2.9 |
| Reach excess, EQ pools | +5.1 ± 5.6 (n 330) | +5.7 ± 3.8 | +7.2 ± 6.5 | +2.1 ± 4.6 | −2.7 ± 10.0 | −7.1 ± 5.3 | n < 30 | n < 30 | n < 30 |
| Reach excess, prior UTC-day H/L | −1.4 ± 1.1 | −1.3 ± 1.3 | +2.7 ± 1.3 | −0.1 ± 1.2 | — | — | — | — | — |
| Sweep depth, median (ATR) | 0.63 | 0.76 | 0.63 | 0.72 | 0.53 | 0.54 | 0.37 | 0.31 | 0.34 |
| Sweep depth, p80 (ATR) | 1.49 | 1.83 | 1.37 | 1.63 | 1.20 | 1.20 | 0.66 | 0.76 | 0.61 |
| Sweep depth, EQ pools, median | 1.18 (n 85) | 1.10 | 0.76 | 0.70 | — | 0.70 (n 63) | — | — | — |
| REJECT share (close back inside) | 41.5% | 50.7% | 46.0% | 50.0% | 50.0% | 36.8% | 44.3% | 43.3% | 40.4% |
| Post-sweep ±1 ATR continuation − base (pp) | +2.5 ± 1.8 | +0.9 ± 1.5 | +0.4 ± 1.1 | −1.1 ± 1.3 | −4.4 ± 2.8 | −0.4 ± 1.8 | −1.6 ± 3.9 | +5.8 ± 3.3 | +5.6 ± 4.8 |
| Approach stall vs control (pp; − = stalls) | −1.2 ± 2.4 | +1.4 ± 1.9 | +3.1 ± 1.9 | +2.3 ± 1.6 | −2.1 ± 3.7 | −2.6 ± 1.9 | +10.0 ± 3.0 | +2.5 ± 3.5 | +4.7 ± 3.4 |
| Trap-level stall (pp) | +3.4 ± 2.7 (n 313) | +1.0 ± 2.6 | +5.3 ± 2.5 | −0.5 ± 2.6 | −7.6 ± 6.2 (n 70) | −6.3 ± 4.6 (n 103) | n < 30 | −1.2 ± 8.5 | n < 30 |

Key differences (post − pre, ± SE, z):

| Market | Reach all | Sweep depth median | REJECT share | Stall | Placebo comparison |
|---|---|---|---|---|---|
| BTC 2021-22 − 2017-18 | +2.3 ± 1.6 (z 1.4) | −0.01 ± 0.05 | +4.4 ± 1.7 (z 2.6) | +4.3 ± 3.1 (z 1.4) | 2019-20 − 2017-18 (transition): reach +1.7, depth +0.12 (z 2.4), REJECT +9.2 (z 4.5) |
| BTC 2023-24 − 2017-18 | +1.3 ± 1.2 (z 1.1) | +0.08 ± 0.06 (z 1.4) | +8.5 ± 1.8 (z 4.7) | +3.4 ± 2.9 (z 1.2) | — |
| EURUSD 2024-26 − 2017-18 | −0.1 ± 2.3 | +0.01 ± 0.04 | −13.2 ± 2.3 (z −5.8) | −0.5 ± 4.1 | data vendors differ between files |
| SPX 2021-26 − 1999-2008 | −2.9 ± 4.0 | −0.03 ± 0.04 | −4.0 ± 5.7 | −5.3 ± 4.6 | SPX 2009-18 − 1999-2008: reach −2.1 ± 3.6, stall −7.5 ± 4.7 |

**Reading.**
- **H1 (attraction): null.** No era moves reach excess by more than about 2 pp, and the pre-vs-pre placebo moves it as much. The one significant cell (prior-day H/L on BTC 2021-22, +2.7 pp) reverts to −0.1 in 2023-24.
- **H2 (deeper stops): rejected.** Median and p80 sweep depth are unchanged on all three markets. EQ pools were swept *less* deeply post-2021 on BTC.
- **H3 (front-running): rejected.** Close approaches pass through as often or *more* often after 2021.
- **H4 (stop-hunt-and-reverse): no common shift.** REJECT share moved in opposite directions on BTC (+) and EURUSD (−), with significant z in both, so it is market or vendor microstructure, not a crowd-wide effect. Continuation after sweeps stays within ±5 pp of the base everywhere.
- **Caveats.**
  - Same instruments but different structure. BTC 2017-18 was a spot-led market; EURUSD pre and post come from different files and possibly different feeds; SPX daily has few EQ pools.
  - A real crowd effect smaller than about 2-3 pp per metric could hide in these SEs.
  - Pre-2019 intraday CME futures data were not available locally.
- **Grade: moderate (null).** Three markets, about 140,000 bars, era-internal baselines, with a placebo.

#### T2 · Trap-level (break-even) stall (in `era_test.py`)
- Pooled: **BTC +2.4 ± 1.3 pp** (n 1,449, levels passed *more* than empty space); **EURUSD −6.8 ± 3.7 pp** (n 173, stalls); SPX 2009-18 −1.2 ± 8.5 (n 34).
- Opposite signs, each about |z| 1.8. **Grade: moderate (market-specific; null in aggregate).** Per-chart grading only (X1B-4).

#### T3 · Swing-anchored VWAP, the cost basis of recent buyers / sellers (`costbasis_test.py`, outputs `out_costbasis_{nq,spx}.txt`)

| Set | Bull AVWAP reach excess | Bull ATWAP (placebo) | Bear AVWAP | Bear ATWAP | AVWAP stall vs push control | ATWAP stall vs push control | **AVWAP − ATWAP touch on approach** |
|---|---|---|---|---|---|---|---|
| NQ 15m 2022-25 (70,685 bars) | −0.48 ± 0.46 (n 11,565) | −0.13 ± 0.50 | −0.63 ± 0.47 | +0.18 ± 0.45 | −2.79 ± 0.47 | −2.15 ± 0.55 | **−0.57 ± 0.48** |
| NQ 1h 2022-25 (18,243 bars) | +0.68 ± 1.06 | −0.90 ± 0.91 | −0.39 ± 1.00 | −0.87 ± 0.89 | −3.16 ± 1.00 | −3.13 ± 0.82 | **+0.07 ± 0.95** |
| SPX D 1999-2018 | −1.49 ± 1.78 | −1.13 ± 1.64 | −1.18 ± 1.85 | −1.23 ± 1.74 | −3.43 ± 1.70 | −2.35 ± 1.94 | **−0.95 ± 1.82** |
| SPX D 2021-26 | −3.13 ± 3.86 | −1.30 ± 3.70 | −3.77 ± 3.82 | −4.20 ± 3.82 | −5.70 ± 4.13 | −10.40 ± 3.65 | **+3.00 ± 3.98** |

**Reading.**
- The cost-basis line is no magnet: every cell is within 1 SE of zero intraday.
- Its small "stall" is shared by the time-weighted placebo, so it is a property of a mean-like level inside the range, not of volume-weighted cost.
- **Grade: moderate (null).**

#### T4 · Capital-gains overhang tilt on the nearest-BSL vs nearest-SSL race (`costbasis_test.py`)
- Race between the nearest unswept pivLen-5 BSL and SSL (both ≤ 6 ATR), strict trade-through. Excess = upFirst − p0, where p0 = d_S / (d_B + d_S) is the driftless gambler's-ruin geometry.

| Set (N_turn) | All | CGO Q1 | Q2 | Q3 | Q4 | Q5 | Trend − & Q1 | Trend + & Q5 |
|---|---|---|---|---|---|---|---|---|
| NQ 15m (50) | +0.5 ± 0.9 (n 10,134) | **−3.7 ± 1.6** | +0.9 | +0.4 | +1.5 | **+3.5 ± 1.7** | −4.3 ± 1.6 (n 1,883) | +3.3 ± 1.7 (n 1,919) |
| NQ 15m (200) | — | −3.2 ± 1.8 | +0.5 | +0.5 | +2.2 | +2.7 ± 1.7 | −3.8 ± 2.0 | +2.6 ± 1.7 |
| NQ 1h (50) | −0.1 ± 2.0 (n 2,350) | +0.5 | +0.3 | +0.2 | −5.2 | +3.6 | +1.3 | +3.8 |
| SPX D 1999-2018 (20) | −1.0 ± 3.5 (n 638) | +2.9 | −6.6 | −4.3 | +1.5 | +1.2 | −2.4 | +2.0 |

**Reading.**
- On 15m the CGO extremes lean with momentum (a few pp). 92-95% of the extreme-quintile samples sit in the matching trend stratum, so CGO is almost a re-labelled trend.
- 1h and daily show no monotone pattern.
- **Grade: moderate (null as an independent input).** Keep it at most as a logged covariate (X1B-4).

#### T5 · Live PoT movement inside one chart bar (`livepot_test.py`, output `out_livepot.txt`)
- NQ 1m paths inside 1h and 15m chart bars. Target = the nearest unswept pivLen-5 pool 0.5-6 ATR away at the previous close.
- Engine analytic driftless model 2Φ(−d / (σ√H)), capped at 95%; σ = 50-bar stdev of chart-bar close changes; H = 30.
- The live value is recomputed on every 1-minute close, like the engine's tick readout (2066-2068).

| Chart TF | Bars | Intrabar PoT range: median | p75 | p90 | Crosses 50% | Crosses 70% | "False surge" (+15 pp then closes below the open value, no sweep) |
|---|---|---|---|---|---|---|---|
| 1h | 16,481 | **10.9 pp** | 17.4 | **26.4** | 17.7% | **27.3%** | 0.9% |
| 15m | 67,734 | **10.2 pp** | 16.7 | **25.0** | 17.5% | **22.4%** | 0.9% |

- Context: bar-close analytic calibration on 1h is good (decile PoT 0.19 → hit 0.27 … 0.90 → 0.91). On 15m it is overconfident in the middle (0.79 → 0.66), which the engine's default Empirical model is meant to correct (`quant_pot`, CAL-4).
- **Reading.** A trader watching the label sees it swing by about ±5 pp on a typical bar and by 25 pp on one bar in ten. It flips across "70%" inside one bar in four. That is noise around a value which is only meaningful at bar close for the ledger, yet it is the most salient number on the chart.
- **Grade: strong (measurement)** for the size of the swing; **moderate** (field evidence L24-L26) for the harm.

---

## 3. Engine gap analysis (line numbers in `baseline_v2.pine`)

| Concept | Status | Lines | What the engine does / differs |
|---|---|---|---|
| Stops at obvious extremes (disposition, break-even, round numbers) | **present** (as geometry) | 90-100, 614-626, 1553-1589 | Pools at swing extremes with strict trade-through. T1 shows their reach is fully explained by distance in every era. Round-number capping belongs to `orderflow_micro` OF-4 |
| Era-aware priors | **missing (correctly)** | — | No era effect to encode (T1). Ledger and empirical PoT are cumulative over `calcBars` (1059-1062, 1376-1382, 1460-1500), with no drift readout → X1B-5 |
| "Obviousness" as a scoring input | **partial (wrong sign of confidence)** | 666-679 (confluence 0.35 per anchor: PDH/PDL/PWH/PWL/opens/EQs), 680-685 (density: 0.9·eqCount + 0.45·stack + 0.35·tests + tier) | Obviousness is rewarded in two pillars (35% of weight). Measured reach gain is ≈ 0 (T1 here; `ict_liq`; `classic_levels`). Handled by CAL-1 / ICT-10 neutralisation; this lens adds per-chart discovery bits (X1B-4) |
| Cost basis (AVWAP, VWAP, reference price) | **missing (correct as targets)** | grep `vwap`: none | T3 null; `classic_levels` CL-6 keeps VWAP display-only. CGO only as a logged covariate (X1B-4) |
| Trapped-trader (failed-breakout) levels | **missing** | 1579-1582 classify HOLD / REJECT but the level is then deleted (1588) | Market-specific (T2). Shadow bit only (X1B-4) |
| Crypto on-chain cost basis | **missing** | request budget: 6 calls used (923-925, 939, 981-982) | Available via `INTOTHEBLOCK:` / `GLASSNODE:` (daily, plan-dependent). Weak evidence → X1B-6 (shadow) |
| Live PoT readout | **present, unanchored** | 2066-2068 (`activePoT` recomputed every tick), 2225 (Clean label), 2443 (data window) | No bar-close anchor and no indication of the typical intrabar swing (T5: median 10-11 pp, p90 25 pp). The product spec requires live PoT, so anchor it rather than remove it → X1B-2. The filter flicker is handled by PENG-4 |
| "Swept" shown as 95% | **wrong** (already reported) | 2067 | COMP-4 / UX-3 own the fix ("✓ Reached") |
| Reliability information in the default view | **missing in Clean** | 2295-2308 (Clean table: bias only); 2376-2392 (verdict computed, Terminal only) | The default user sees "PoT: 70.1%" with no track record (automation-bias risk) → X1B-1. UX-5's accuracy row is opt-in |
| Outcome record symmetry | **wrong (survivorship)** | 1584-1586 (ghost on swept / ejected), 2021-2023 (ghost only when `not curElig`), 210 (`showGhost` false by default) | A challenger replacement or a score sag removes the old target silently. Expiry without a hit leaves no mark. Hits get "✕ SWEPT" ghosts. The ledger itself is unbiased (trials graded for H bars regardless, 2037-2045), but the picture is not → X1B-3 (extends COMP-5) |
| Sweep alert fires on the first intrabar touch | **present** (by design) | 2085, 2090 | 37-51% of first trade-throughs close back inside the same bar (T1 REJECT share). The bar-close class alert belongs to OF-2; X1B-2 adds the confirmed PoT to the alert text |
| Loss-chasing / afternoon noise (Coval-Shumway) | **n/a** | — | Effect lives at the 10-minute scale |

---

## 4. Proposals (spec-level, best first)

Measurement principle: each proposal either *is* a ledger readout or logs a ledger-measurable quantity. None changes the target score by default. The two P1 items change only what the user sees, in the direction of calibration.

### X1B-1 (P1, S, visual-ux) · Reliability cue on the Clean label (automation-bias guard)
**Problem.** In the default Clean style the user sees "Target: X / PoT: 70.1%" and nothing about whether this engine has any measured skill on this chart. The verdict exists (2376-2392) but is Terminal-only. Automation bias is strongest exactly when no reliability information is shown (L19); dynamic confidence information improves trust calibration (L20).

**Spec.**
1. **Hoist the verdict.** Move the verdict maths out of the panel block into a global helper `f_edgeState()`, declared after `f_book` (≈1500) so that `stN`, `stK`, `stPE`, `stPV` and `cluSt` (1068-1078) are already declared. It returns `[int st, float hitPct, float basePct, float nA, float zE]`:
   - `nA = stN.get(4)`, `kA = stK.get(4)`, `E = stPE.get(4)`;
   - `vEdge = math.max(stPV.get(4), cluSt.get(2) + cluSt.get(1) * cluSt.get(1))`;
   - `zE = vEdge > 0 ? (kA − E) / math.sqrt(vEdge) : na`;
   - `st = nA < 30 or na(zE) ? 0 (CAL) : zE >= 2 ? 3 (EDGE) : zE >= 1 ? 2 (WEAK) : 1 (NO EDGE)`.
   - When CAL-2 (peeking-safe verdict) lands, use its gate instead of the raw z.
   - The Terminal panel (2384-2391) calls the same helper, so there is one source of truth.
2. **Input.** `relCue = input.bool(true, "Show Reliability Cue", group = G_DOL, display = display.none, tooltip = "Dims the PoT and adds * while the accuracy ledger is calibrating or shows no edge over random levels at the same distances.")`.
3. **Clean label (2224-2226).** For states CAL and NO EDGE, when `relCue` is on:
   - text line 2 becomes `"PoT: 70.1%*"`;
   - the text colour is `color.new(c, 45)` instead of `c` (a dimmer neon, still readable on `#161616`);
   - the tooltip's first line becomes:
     - CAL: `"* calibrating: 12 of 30 graded targets so far"`;
     - NO EDGE: `"* no measured edge on this chart: hit 54% vs 53% for random levels at the same distances (n 140, z 0.4)"`.
   - States WEAK and EDGE: unchanged (reference look). The tooltip adds `"track record: hit 61% vs 52% random (n 140, z 2.3)"`.
4. **Terminal HUD (2238-2240).** Append `" · ✕ NO EDGE"` or `" · CALIBRATING"` to the PoT line in those states.
5. **Alerts (2078-2080).** Append `" · ledger: no measured edge (n 140)"` or `" · ledger: calibrating"` to the `alert()` text. Optional `muteNoEdge` (default false) skips the New-DOL `alert()` in state NO EDGE. Leave `alertcondition` unchanged (constant message).
6. **Data window.** `plot(st, "Ledger State (0 cal · 1 none · 2 weak · 3 edge)", display = display.data_window)`.

**Value.** The default user gets an honest, glanceable cue at exactly the moments when over-reliance is most costly, without cluttering the reference look when the engine has earned trust.
**Measurement.** The cue is a function of the ledger. Its own validity is CAL-2's job. Log the share of realtime bars shown with the cue.
**Evidence.** **moderate**: L19-L21 are strong in their domains (clinical decision support, aviation, forecasting); transfer to trading is assumed.
**Risk.**
- The raw z verdict is optimistic under optional stopping until CAL-2 lands, so use n ≥ 30 and the cluster variance.
- Users may dislike "no edge": that is the point.
- Coordinate with COMP-4 (tooltip lines) and UX-3 (state grammar), so `*` is the only new glyph.

**Effort.** S (about 25 lines; no new state).

### X1B-2 (P1, S, visual-ux / alerts) · Anchor the live PoT to its bar-close value, and show the typical swing
**Problem.** The live PoT moves a median 10-11 pp inside one chart bar and 25 pp at the 90th percentile. It crosses 70% within a quarter of bars (T5). Frequent outcome-like feedback lowers professional traders' risk-taking and profits (L24-L26). The product spec promises a tick-by-tick PoT, so keep it, but give the eye a stable anchor.

**Spec.**
1. **State.** `var float potClose = na` and `var int potCloseId = -1`. At the end of LIVE READOUTS (after 2068):
   - `if barstate.isconfirmed and not na(activeLv) and not sweptNow` → `potClose := activePoT`, `potCloseId := activeLv.id`;
   - when `na(activeLv) or activeLv.id != potCloseId`, use `potClose = na` for display (a new target has no anchor until its first close).
2. **Per-chart typical swing.** It is computable on history, so it needs no realtime data.
   - On each confirmed bar with an active target, `pHi = f_potModel(max(0, dist at high), side, mu)` and `pLo = f_potModel(max(0, dist at low), side, mu)`. Push `math.abs(pHi − pLo)` into `var array<float> potSw` (cap 300).
   - `potSwMed = potSw.median()`, computed on `barstate.islast` only.
   - `f_potModel` is O(1) (comment at 2063); two extra calls per confirmed bar.
3. **Input.** `potRead = input.string("Live", "PoT Readout", options = ["Live", "Live + anchor", "Bar close"], group = G_POT, display = display.none, tooltip = "Live updates every tick (as the reference). Live + anchor adds the last bar-close value when they differ by 5 points or more. Bar close shows only confirmed values.")`.
4. **Clean label (2225).**
   - Live: `"PoT: 70.1%"` (reference look).
   - Live + anchor: `"PoT: 70.1% (66)"` only when `|activePoT − potClose| ≥ 0.05`.
   - Bar close: `"PoT: 66.0%"`.
   - Tooltip in all modes: `"Bar-close PoT 66.0% · live readout typically moves ±" + str.tostring(potSwMed * 50, "0") + " pts within a bar on this chart"`.
5. **Terminal HUD (2239).** Same suffix, plus `"· swing ±5"`.
6. **Alerts.** New-DOL `alert()` text (2078) reports the **bar-close** PoT, which it already does in effect because `annNow` requires `barstate.isconfirmed`. The live "target swept" alert (2085) appends `" · intrabar touch, not yet closed"`. The bar-close sweep class (HOLD / REJECT / RECLAIM) comes from OF-2's alert, so implement both together.
7. **Data window.** `plot(potClose * 100, "DOL PoT % (bar close)")` and `plot(potSwMed * 100, "PoT intrabar swing (median)")`.
8. **Default.** "Live" keeps feature parity with the reference. Recommend "Live + anchor" in the README for discretionary use. The judges may prefer "Live + anchor" as the default, since the suffix appears only when the gap is ≥ 5 points.

**Value.** Removes the main source of tick-driven overreaction while keeping the promised live feature. It tells each user, per chart, how much of the movement is noise.
**Measurement.** `potSwMed` and the anchor are deterministic, and the ledger keeps using confirmed values. A user study is not possible inside Pine; log realtime label-text changes per bar as a flicker metric.
**Evidence.** **moderate**: T5 (strong measurement) plus L24-L26 (field and lab evidence that more frequent feedback harms risk-taking).
**Risk.** Low. One more input; label width grows by 5 characters in one mode. `potSwMed` uses the PoT model at historical bar extremes, an approximation of the tick path (it bounds the swing from above for the bar's own range).
**Effort.** S (about 30 lines).

### X1B-3 (P2, S, visual-ux) · Outcome-symmetric visual record (fix visual survivorship)
**Problem.**
- Hits leave "✕ SWEPT" ghosts (1586).
- Replaced targets vanish unless they became ineligible (2021-2023).
- Expiries leave nothing.
- Ghosts are off by default (210).
- The ledger grades correctly (2037-2045), but the user's *memory* of the chart is built from hits. Outcome bias (L22) and hindsight bias (L23) turn that into over-trust.

**Spec** (extends COMP-5; implement inside its stamp mechanism, not a second one).
1. **Ghost every abandoned active target.** In step 19, replace the `not curElig` guard (2021) with `curI >= 0 and pick != curI`. The reason is `"⇄ REPLACED"` when a challenger won, `"⊘ INVALIDATED"` when the side flipped, `"↓ FADED"` when the score fell below `minScore − hyst`.
2. **Expiry.** In step 2 (1549-1555), when `f_step(t)` returns 3 and the trial's `lvId` is still the active target, ghost it as `"⌛ EXPIRED · PoT was 62%"`. Add `float pShow` to `Trial`, set in `f_openTrial` at the asserted (bar-close) PoT, as COMP-4 already specifies.
3. **Outcome strip.** `var array<int> outS` (cap 10): +1 hit, 0 expired, −1 replaced / invalidated or faded before H. Pushed in `f_book` (1460) for active-target trials. Each trial carries its own `pShow`, so the strip's "expected" uses `Σ pShow`.
   - Terminal panel, after DOL HIT (2394): `"LAST 10  ✓✓✕⇄✓✕✓✓✕✓  6/10 · exp 6.4"`.
   - Clean: shown only if UX-5's `tblExtra` includes "Accuracy". It becomes the accuracy row's text.
4. **Default.** When `showGhost` is on, misses use the same ghost styling as hits (same opacity), not a dimmer one.

**Value.** What the user sees matches what the ledger counts. Misses sit next to their stated probability, which protects trust against algorithm aversion (L21) as well as over-trust (L22-L23).
**Measurement.** The strip *is* the ledger (k of n vs Σ pShow: a running calibration check).
**Evidence.** **moderate** (lab-strong biases; the transfer to chart reading is assumed).
**Risk.** Ghost budget (`ghostMax` 12) fills faster; FIFO handles it. Each "REPLACED" ghost is one box and one label.
**Effort.** S.

### X1B-4 (P3, M, statistics-ledger) · Behavioural discovery bits in the shadow ledger: obviousness, trap level, cost basis
**Problem.** Behavioural theory says obvious levels, trapped-trader levels and cost bases matter. The tests here (T1-T4) and in sibling lenses find ≈ 0 on average, with market-specific signs (T2). The honest design measures them **per chart** and lets them earn weight only through the CAL-3 / ICT-1 gate.

**Spec.** Build on CAL-3's candidate (shadow) ledger (`Probe` with feature bits); do not build a second ledger.
1. **Bits set at probe open:**
   - b0 `EQ`: `eqCount > 0`;
   - b1 `KEY`: src 6 or 7 (PD / PW);
   - b2 `ROUND`: `math.abs(nearEdge − math.round(nearEdge / rStep) * rStep) <= 0.1 * atr`, with `rStep = math.pow(10, math.floor(math.log10(close))) / 10`;
   - b3 `SCREEN`: the level is the highest high / lowest low of the last 200 bars (`ta.highest(high, 200)` evaluated at global scope each bar, compared within 0.05 ATR);
   - b4 `POPSMC`: within 0.1 ATR of a swing that the popular free SMC default draws. Track `var float popH`, set when `high[50] > ta.highest(high, 50)` (LuxAlgo-style leg, size 50, at global scope); mirror for lows;
   - b5 `TRAP`: within 0.1 ATR of a stored failed-breakout level;
   - b6 `CGO+`: CGO in the draw direction above its 80th percentile, using the T4 recursion with `N_turn = 50`;
   - b7 `AVWAP-SIDE`: price on the target's side of the swing AVWAP.
2. **Trap store.** In step 3 (1579-1582), when a liquidity pool is hit and the bar closes back inside (`evt == −1` for BSL or `+1` for SSL), push `[price, side, bar_index]` to `var array<float> trapPx` (cap 20, expire after 300 bars).
3. **Per-bit stats.** `var array<float> bitSt = array.new<float>(8 * 6, 0.0)`: for each bit, [n_on, k_on, ΣpBase_on, n_off, k_off, ΣpBase_off]. Use block-clustered SEs as in `f_book`.
4. **Full panel.** `"FEATURES  EQ +0.4±2.1 · KEY −0.8±1.5 · ROUND +1.1±2.4 · TRAP −3.0±3.2 · …"` (edge on − edge off, pp). No glyph verdicts.
5. **Promotion.** A bit enters scoring only through CAL-9 / CAL-3's gate (prequential improvement, multiplicity-corrected). The default stays off.

**Value.** Answers "do obvious / trapped / cost-basis levels matter on *my* chart?" with numbers instead of doctrine. It is also the measured replacement for the 35% of score weight currently spent on obviousness-like pillars.
**Evidence.** **moderate (null on average)**: T1-T4 here; EQ / tests / prominence null in `ict_liq`; reference levels null in `classic_levels`.
**Risk.** Multiplicity (8 bits) means users may chase noise. Show ± SEs and no verdict glyphs. CPU: about 10 comparisons per probe. Adds 2-3 global `ta.*` calls (`ta.highest` 200 and 50, lowest).
**Effort.** M (about 70 lines on top of CAL-3).

### X1B-5 (P3, S, statistics-ledger / robustness) · Drift monitor instead of era-aware priors
**Problem.** The fear that "the crowd changed the market" is not supported by T1, but structural change can happen (venue, tick size, retail share). The ledger and the empirical PoT surface are cumulative over `calcBars` (5,000 bars), so a recent change would be diluted silently.

**Spec.**
1. A rolling window of the last `driftN = 150` booked trials: `var array<float> rY`, `rP` (y and pBase), pushed in `f_book` (1461) next to `roll50`.
2. Recent edge `eR = (Σ rY − Σ rP) / n_R`; earlier edge `eE` from the cumulative stats minus the window. `zΔ = (eR − eE) / √(vR + vE)`, with block variances as in `f_book`.
3. **Terminal Full panel row.** `"DRIFT  recent +0.4pp · earlier +3.1pp · Δz −1.2  (stable)"`. Show "(changed)" only when |zΔ| ≥ 2 and both halves have n ≥ 60.
4. **Empirical PoT surface.** Store a second, recent-only count in the same `S[r][j]` layout only if `quant_pot` wants it. Log the prequential Brier of cumulative vs recent surfaces in the data window and switch nothing automatically.

**Value.** Cheap insurance and an honest answer to "is it decaying?", the McLean-Pontiff question asked per chart.
**Evidence.** **moderate (null)** for the SMC-crowd era shift (T1); **strong** for anomaly decay in general (L17).
**Risk.** Low power at a few hundred trials; that is why it shows "(stable)" by default.
**Effort.** S.

### X1B-6 (P3, M, level-source) · Crypto on-chain cost basis as a shadow-graded external family
**Problem.** Crypto traders watch realised price, short-term-holder realised price and in/out-of-the-money clusters as cost-basis S/R. Evidence is anecdotal (L28-L29), but the data exists on TradingView.

**Spec.**
1. **Gate.** `syminfo.type == "crypto"` and a base currency in {BTC, ETH}; chart TF ≥ 1H (daily data).
2. **Request**, one call, through `f_tfSafe("D")` with the standard [1] + lookahead_on pattern: `request.security("INTOTHEBLOCK:" + syminfo.basecurrency + "_MVRV", "D", close[1], lookahead = barmerge.lookahead_on, ignore_invalid_symbol = true)` → `mvrv`. Then `rp = dailyClose[1] / mvrv`. The ticker must be verified in the editor; if it is unavailable, fall back to `GLASSNODE:` market cap / realised cap where offered, or disable.
3. **Registry.** Push to `extReg` as src 15 "RP" (claim a free code in the crowded `src` space; see `asset_specific` X23), with `isHigh = rp > close`, and HTF aging `hlMult` = daily bars.
4. **Shadow only.** The family enters the pool with `mult *= 0` for selection, but probes and grades it as its own CAL-3 role ("RP family edge"). It may become eligible only through the CAL-3 gate.
5. **Display.** An optional dim dotted line labelled "Realised price" (input `showRP`, default false).

**Value.** Lets crypto users test a popular behavioural level honestly on their own chart.
**Evidence.** **weak** (anecdotal; the methodology is an assumption).
**Risk.** Ticker availability and data-plan requirements are unverified. Uses 1 of 40 request slots (6 used today). Daily granularity.
**Effort.** M.

---

## 5. Do-not-build list (from this lens)

| Idea | Why not | Evidence |
|---|---|---|
| Era-aware priors ("post-2021 the crowd hunts EQH deeper") | No common era shift in reach, depth, front-running or post-sweep behaviour; signs differ by market | T1, moderate (null) |
| Swing / weekly / monthly AVWAP as targets | Reached as often as distance implies; equal to a time-weighted placebo | T3 + `classic_levels` |
| Capital-gains overhang as a D input | A trend proxy; no monotone effect at 1h or daily | T4 |
| "Trapped trader" levels as a score bonus | Opposite signs by market | T2 |
| Afternoon "loss-chasing" timing rule | Effect reverts within about 10 minutes (Coval & Shumway) | L9 |
| Liquidation-heatmap levels | Modelled leverage assumptions, no accuracy test | L30 |
| Raising the weight of "obvious" levels (EQ, PD, rounds) | Reach ≈ distance in every era; already over-weighted in the confluence and density pillars | T1; `ict_liq`; `classic_levels` |
| Hiding the live PoT | The product spec promises it; anchor it instead (X1B-2) | spec |

---

## 6. Reproducibility

All scripts read local data only and are run with `python3 -I` (numpy 2.5.3, pandas 3.0.5). Paths are absolute inside the scripts.

| Test | Command (from `study/x1_beh_tools/`) | Output | Data |
|---|---|---|---|
| T1 + T2 BTC | `python3 -I era_test.py btc` | `out_era_btc.txt` | `session_data/btc_1h.pkl` (2017-01 → 2025-01, 70,273 1h bars) |
| T1 + T2 EURUSD | `python3 -I era_test.py eur` | `out_era_eur.txt` | `bias_data/EURUSD.csv` (2017-04 → 2018-02, 5,000 bars); `scratchpad/sim/data/eu.csv` (1H 2024-26, 12,285 bars) |
| T1 + T2 SPX / NASDAQ | `python3 -I era_test.py spx` | `out_era_spx.txt` | `bias_data/sp500.csv`, `nasdaq.csv` (1999-2018); `x1_iv_data/spx1.csv` (2021-08 → 2026-08) |
| T3 + T4 NQ | `python3 -I costbasis_test.py nq` | `out_costbasis_nq.txt` | `scratchpad/i2/dl/data_src/data/Dataset_NQ_1min_2022_2025.csv` (1m with volume, 2022-12 → 2025-12), resampled to 15m / 60m; 4 roll-gap bars |
| T3 + T4 SPX | `python3 -I costbasis_test.py spx` | `out_costbasis_spx.txt` | as above |
| T5 | `python3 -I livepot_test.py 60min,15min` | `out_livepot.txt` | NQ 1m as above |

**Parameters.**
- pivLen 5; eqTol 0.10 ATR; ejection 15 ATR; reach checkpoints every 5 bars, pools 0.25-4 ATR.
- H = 30 (intraday) / 20 (daily); approach gap ≤ 0.25 ATR; outcome window K = 10 bars; trap life 300 bars, armed after 0.5 ATR away.
- Bootstrap: 400 reps over 500-bar (120 daily) blocks; seeds 7 / 11.
- `costbasis_test.py` imports helpers from `era_test.py` (same folder).

---

## 7. Sources

Literature (numbers as given in the search summaries of these pages):
- Odean 1998, "Are investors reluctant to realize their losses?", JF 53(5): https://rpc.cfainstitute.org/research/cfa-digest/1999/05/are-investors-reluctant-to-realize-their-losses-digest-summary ; PGR/PLR figures via https://www.earnforex.com/blog/disposition-to-keep-losses-and-cut-winners/
- Kaustia 2010, "Prospect theory and the disposition effect", JFQA 45(3): https://econpapers.repec.org/RePEc:cup:jfinqa:v:45:y:2010:i:03:p:791-812_00 ; https://www.aalto.fi/sites/default/files/2018-12/prospect_theory_and_disposition_effect.pdf
- Locke & Mann 2005, JFE 76(2): https://ideas.repec.org/a/eee/jfinec/v76y2005i2p401-444.html
- Coval & Shumway 2005, JF 60(1): https://ideas.repec.org/a/bla/jfinan/v60y2005i1p1-34.html ; https://rpc.cfainstitute.org/research/cfa-digest/2005/11/do-behavioral-biases-affect-prices-digest-summary
- Choe & Eom 2009, J. Futures Markets 29(6): https://ideas.repec.org/a/wly/jfutmk/v29y2009i6p496-522.html
- Grinblatt & Han 2005, JFE 78(2): https://econpapers.repec.org/RePEc:eee:jfinec:v:78:y:2005:i:2:p:311-339
- Frazzini 2006, JF 61(4): https://ideas.repec.org/a/bla/jfinan/v61y2006i4p2017-2046.html ; https://www.aqr.com/Insights/Research/Journal-Article/The-Disposition-Effect-and-the-UnderReaction-to-News
- Heimer 2016, RFS 29(11): https://www.clevelandfed.org/publications/working-paper/2016/wp-1618-peer-pressure-social-interaction-and-the-disposition-effect
- Pelster & Hofmann 2018, JBF 94: https://econpapers.repec.org/RePEc:eee:jbfina:v:94:y:2018:i:c:p:75-88
- Schatzmann & Haslhofer, Digital Finance 2023 (arXiv 2010.12415): https://arxiv.org/abs/2010.12415
- Thaler & Johnson 1990 and futures follow-ups: https://ideas.repec.org/a/eee/pacfin/v26y2014icp1-13.html ; https://www.nuff.ox.ac.uk/Users/MurphyA/Do%20Losses%20Linger.pdf
- Barber & Odean 2008, RFS 21(2): https://ideas.repec.org/a/oup/rfinst/v21y2008i2p785-818.html
- Yuan 2015, JFE 116(3): https://econpapers.repec.org/RePEc:eee:jfinec:v:116:y:2015:i:3:p:548-564
- Bhattacharya, Holden & Jacobsen 2012, Mgmt Sci 58(2): https://ideas.repec.org/a/inm/ormnsc/v58y2012i2p413-431.html ; https://bm.hkust.edu.hk/bizinsight/2017/03/penny-wise-dollar-foolish
- Urquhart 2017, Econ. Letters 159: https://ideas.repec.org/a/eee/ecolet/v159y2017icp145-148.html ; Mbanga 2019: https://ideas.repec.org/a/taf/apeclt/v26y2019i10p807-811.html
- George & Hwang 2004; Li & Yu 2012 (covered by `academic_sr` ACAD-6): https://www.bauer.uh.edu/tgeorge/papers/gh5-paper.pdf ; https://econpapers.repec.org/RePEc:eee:jfinec:v:104:y:2012:i:2:p:401-419
- Barber, Huang, Odean & Schwarz 2022, JF 77(6): https://profiles.wustl.edu/en/publications/attention-induced-trading-and-returns-evidence-from-robinhood-use/ ; https://gsm.ucdavis.edu/news/what-effect-brokerage-robinhood-having-stock-market
- Retail share and micro futures: https://www.cmegroup.com/openmarkets/equity-index/2022/the-rise-in-equity-options-trading-extends-to-futures.html ; https://www.cmegroup.com/media-room/press-releases/2021/8/30/cme_group_micro_futuresandoptionssurpass1billioncontractstraded.html
- McLean & Pontiff 2016, JF: https://rpc.cfainstitute.org/research/cfa-digest/2016/06/does-academic-research-destroy-stock-return-predictability-digest-summary ; https://ivey.uwo.ca/media/3775549/pontiff.pdf
- Osler 2000, FRBNY EPR: https://www.newyorkfed.org/medialibrary/media/research/epr/00v06n2/0007osle.html
- Chung & Bellotti 2021: https://ideas.repec.org/p/arx/papers/2101.07410.html
- Goddard, Roudsari & Wyatt 2012, JAMIA 19(1): https://academic.oup.com/jamia/article/19/1/121/732254 ; https://pmc.ncbi.nlm.nih.gov/articles/PMC3240751
- McGuirl & Sarter 2006, Human Factors 48(4): https://swov.nl/en/publicatie/supporting-trust-calibration-and-effective-use-decision-aids-presenting-dynamic-system
- Dietvorst, Simmons & Massey 2015: https://repository.upenn.edu/fnce_papers/58
- Baron & Hershey 1988 and the 2023 replication: https://bear.warrington.ufl.edu/brenner/mar7588/Papers/baron-hershey-jpsp1988.pdf ; https://doaj.org/article/b01e7003c5574b1593d8309a66260878
- Biais & Weber 2009, Mgmt Sci 55(6): https://ideas.repec.org/a/inm/ormnsc/v55y2009i6p1018-1029.html
- Haigh & List 2005, JF 60(1): https://ideas.repec.org/a/bla/jfinan/v60y2005i1p523-534.html
- Larson, List & Metcalfe 2016, NBER w22605: https://www.nber.org/papers/w22605
- Gneezy & Potters 1997, QJE 112(2): https://ideas.repec.org/a/oup/qjecon/v112y1997i2p631-645..html
- Chague, De-Losso & Giovannetti, "Day trading for a living?": https://ideas.repec.org/p/fgv/eesptd/525.html ; https://quantpedia.com/retail-day-trading-is-an-uphill-battle/
- On-chain data on TradingView: https://www.tradingview.com/blog/en/intotheblock-defillama-data-on-tradingview-33845 ; https://www.tradingview.com/blog/en/blockchain-data-from-glassnode-now-available-on-tradingview-26223 ; https://www.tradingview.com/symbols/BTC_BREAKEVENADDRESSES
- IntoTheBlock IOMAP methodology: https://resources.intotheblock.com/indicators/financial/in-out-of-the-money/in-out-of-the-money-around-price
- STH realised price commentary: https://cryptoslate.com/bitcoins-short-term-holder-realized-price-remains-a-critical-support-amid-market-volatility/ ; https://cointelegraph.com/news/bitcoin-price-bull-market-trendline-last-sparked-30-gains
- Liquidation heatmaps: https://insights.glassnode.com/liquidation-heatmaps/ ; https://coinmarketcap.com/charts/liquidation-heatmap/
- AVWAP definitions: https://www.optuma.com/kb/tools/averages/anchored-volume-weighted-average-price-vwap ; https://toslc.thinkorswim.com/center/reference/Tech-Indicators/studies-library/A-B/AnchoredVWAP

Sibling studies cross-referenced: `ict_liq.final.md` (pool reach ≈ distance; EQ null), `classic_levels.final.md` (VWAP / AVWAP tests, CL-6), `orderflow_micro.final.md` (OF-2 sweep classes, OF-4 round-number cap), `academic_sr.final.md` (ACAD-6 52-week / ATH), `x1_positioning.md` (0DTE, gamma, funding), `calib_ml.final.md` (CAL-1/2/3/9), `competitors.final.md` (COMP-4/5), `pine_eng.final.md` (PENG-4), `ux_design.final.md` (UX-3/5), `smc_impl.final.md` (LuxAlgo defaults).
