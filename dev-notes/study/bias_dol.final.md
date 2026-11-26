# Forecasting the next draw (bias methods): combined final study (Researcher A + Researcher B)

**Domain.** How practitioners and researchers decide whether the next session, day or week takes **buy-side or sell-side liquidity** first, how likely that is within a horizon, and how that should drive the engine's draw vector **D** and the selection's side choice. Covered:
- ICT daily bias, Candle Range Theory (CRT);
- previous-candle high/low "taken next candle" statistics on W/D/4H/1H, including the Taylor / Raschke close-location rule;
- weekly profiles, open-relative bias (midnight / weekly open);
- order-flow / structure bias, dealing-range position;
- momentum vs mean reversion, sweep-and-reverse vs breakout-continuation (Turtle Soup, Oops, smash day);
- Crabel contraction, AMD / Power of 3, the value-area "80% rule", the Taylor 3-day cycle;
- the quant formulation (triple barrier, meta-labeling, prequential scoring).

**Engine.** `brief/baseline_v2.pine`. All line numbers refer to it; the file is identical to `/home/user/m/indicators/dol_engine.pine`.

**How this report was made.**
- Researcher A wrote `study/bias_dol.md`, with original tests in `study/bias_tools/` (data in `study/bias_data/` and the sibling hourly files in `scratchpad/sim/data/`).
- Researcher B (this merge):
  1. re-ran A's scripts: `race.py` reproduces `out_race.txt` byte for byte;
  2. re-checked A's definitions, numbers, line references and external sources;
  3. ran five new tests, with tools and logs in `study/bias_b_tools/`:
     - `b1_fair_ict.py` → `out_b1.txt`: the ICT rule vs geometry on the same cases, and the Taylor/Raschke rule;
     - `b2_sidemodel.py` → `out_b2.txt`: a prequential test of the proposed side model on engine-like pool races;
     - `b2b_boot.py` → `out_b2b.txt`: block-bootstrap confidence intervals for the B2 differences;
     - `b3_period.py` and `b3b_calib.py` → `out_b3.txt`, `out_b3b.txt`: calibration of the previous-candle readout;
  4. read three open-source implementations from GitHub (cloned to `study/bias_b_ext/`, read only, no code copied);
  5. re-checked the gap analysis and rewrote the proposals.
- Run any script with `python3 -I <script>` from its folder.

**Markers.**

| Marker | Meaning |
|---|---|
| **[A✓]** | B re-checked it and it holds |
| **[CORRECTED]** | B changed a claim, a number, a grade or a spec |
| **[NEW-B]** | B added it |
| **[A, not re-fetched]** | B could not reopen the source (see the network note); kept as A reported it, grade capped at weak unless replicated here |

**Network note.** The Firecrawl scraper ran out of credits during this session. The proxy blocked edgeful.com, elitetrader.com, roguequant.substack.com, ttrades.com, luxalgo.com, tradingwyckoff.com, arxiv.org and ssrn.com for WebFetch and curl. B verified sources through:
- the paper index (`firecrawl_research_*`, arXiv full text);
- web-search result summaries;
- GitHub clones;
- sibling studies that had opened the same pages.

**Evidence grades.**

| Grade | Meaning |
|---|---|
| strong | peer-reviewed, or a large quantitative result replicated across many series or by independent agents |
| moderate | published or reproduced statistics with numbers |
| weak | practitioner consensus, small or vendor samples, or single unverified sources |
| none | folklore, or definitions only |

---

## 0. Executive summary

1. **"Which liquidity is taken next" is almost entirely range geometry. The evidence is now strong.** [A✓, upgraded]
   - **A's previous-candle test.** The parameter-free gambler's-ruin rule P(prior high first) = (C − L1)/(H1 − L1) picks the first-taken prior extreme **70-81%** of the time across 17 dataset/reference combinations. B re-ran it and it reproduces exactly.
   - **B's engine-like races (B2).** Nearest unswept pivot pool above vs below, 0.5-8 ATR away, H = 30 bars intraday / 10 bars daily, 7 datasets with 568-1,430 resolved races each. Geometry was right **67-75%** of the time and calibrated within a few points.
   - **Sibling ict_struct, 8 markets.** 65.3% observed vs 65.8% predicted, n 12,148.
   - Path continuity makes this exact: the next pool touched is always the nearest one above or the nearest one below. So "which liquidity next" *is* a two-barrier race.
2. **Every named bias rule adds at most a few points over geometry, with a sign that changes by market. Several are worse than geometry when used as hard rules.**
   - **ICT daily bias** ("closed through PDH → PDH next; swept and closed back inside → opposite side"): it ties a shape-shuffle null (A✓).
   - **[CORRECTED]** A wrote that, as a hard rule, it is "right 64-73%". That figure counted the rule's neutral days as down calls. Scored fairly on the rule's own called cases:
     - the rule is right **68.8-76.3%**;
     - geometry on the **same** cases is right **71.6-80.3%**, a gap of **+2.0 to +6.5 pp** on 12 of 13 datasets;
     - when the two disagree (13-18% of called cases), the rule is right only **31-43%**.
   - **CRT** target-first 39-48% = null (A✓).
   - **Turtle Soup** ≤ geometry (A✓).
   - **Open-relative bias** adds nothing out of sample (A).
   - **The value-area "80% rule"**: 25-28% vs a 27-29% base rate (sibling amt_profile).
   - **AMD**: direction tracks the daily trend regime, not the sweep (B read the full text; see the correction in §2.3).
3. **The best-known "previous high taken" statistic is true, and it is geometry.** [NEW-B]
   - Taylor's rule, via Raschke & Connors: when a session closes near its high, the high is retested next session "80-90%" of the time, but the next close is higher only about 50%.
   - Replicated on 13 series:
     - close in the top 20% of the range (CLV ≥ 0.8) → prior high exceeded next candle **75-89%**;
     - CLV ≥ 0.9 → **79-94%**;
     - next close higher **43-57%** (base 45-56%).
4. **The engine's side choice runs on a vote with no measured skill. That evidence is strong.** [A✓, upgraded]
   - D (structure 50% / displacement 20% / raids 30%, gate 0.35) carries the 30% draw pillar, the ×0.5 counter-draw penalty and draw-side-first eligibility.
   - Sibling replicas put D at 47-54% on 11 markets, inside the random-walk band.
   - **[NEW-B] B2.** Choosing the side by the legacy D proxy instead of geometry loses **3.8 to 8.3 pp** of first-touch accuracy on all 7 datasets. Every block-bootstrap 95% interval excludes 0. The legacy proxy's Brier score is **15-25% worse**.
5. **A's core redesign is right: D becomes a calibrated P(best buy-side finalist reached before best sell-side finalist).** Three corrections come from B2 [CORRECTED]:
   - **(a) Use zero drift.**
     - The engine's drift (`potMu` = 0.5·SMA of close changes) makes the side race **0.4-6.9% worse** (Brier) on all 7 datasets. This agrees with siblings QPOT-01 and REG-3.
     - The horizon-conditioned race `pW/(pW+pL)` from `f_raceH` beats the infinite race on 6 of 7 datasets (+1.0 to +3.0% Brier skill).
   - **(b) Gate the learned features.**
     - A's ungated online SGD over 9 bias features was **worse than geometry on 6 of 7 datasets** (−1.7 to −3.0% Brier; the interval excludes 0 on NQ, GC and EURUSD 1H).
     - The learned weights changed sign from market to market.
     - Features must therefore be *measured* by default and *applied* only after the chart shows significant prequential skill. This is the same principle as siblings CAL-4, ICTS-1 and SKEP-6.
   - **(c) Score in two phases.** A's spec scored finalists with stale previous-bar scores. Splitting `evaluate` into a draw-free pass and a draw pass removes both the staleness and the circularity.
6. **Honest caveat on BIAS-2.** Choosing the side by geometry raises raw DOL HIT % (+2 to +7 pp hit-within-H in A's simulation). It cannot raise the ledger's distance-matched **EDGE**, because geometry *is* distance. The panel and README must say this.
7. **The trader-facing "daily bias" readout (BIAS-3) is worth building, but it needs calibration intraday.** [NEW-B, B3]
   - The readout is P(prior high first), P(prior low first) and P(neither) for D/4H/1H.
   - **Weekly from daily:** the f_raceH readout is calibrated (which-first 76-77%; Brier skill vs base rates +0.18 to +0.31).
   - **4-hour blocks from 1H:** it overstates the chance that either side is reached. At the period open it predicts P(decided) 0.86-0.89 against 0.79-0.83 observed. Late in a period it predicts P(neither) 0.03 against 0.16-0.24 observed (volatility clock).
   - A gated two-parameter calibration of P(decided) per timeframe fixes most of this (Brier −1.6 to −6.1% on 4-hour blocks). Which-first at the open (73-82%) needs no calibration.
8. **Final proposal set** (8, best first):
   - **BIAS-1:** side ledger with a calibrated, gated side model;
   - **BIAS-2:** Draw Source = Calibrated;
   - **BIAS-8:** zero-drift, horizon-conditioned races everywhere, including `f_invalidation`;
   - **BIAS-3:** previous-candle module with a CLV base-rate table and calibrated odds in the Clean table tooltip;
   - **BIAS-4:** implemented as sibling ICT-9, plus separate hold/reject features;
   - **BIAS-5:** measured bias-table skill in the tooltip, with no dimming by default;
   - **BIAS-7:** HTF candle-close alerts with calibrated odds;
   - **BIAS-6:** merged into sibling REG-1.

---

## 1. Concepts: precise definitions and parameters

**Notation** (any timeframe):
- Candle t−2 has high/low H2/L2.
- Candle t−1, the "previous candle", has O1/H1/L1/C1.
- Candle t is the one being forecast.
- CLV = (C1 − L1)/(H1 − L1).

**Rules used throughout:**
- "Taken" = **traded through** (strict `>`/`<`), as the engine does for liquidity (`touched`, 623).
- Outcomes are resolved at bar granularity. A bar that trades through both levels is "ambiguous" and excluded from first-touch rates.
- "Undecided" means neither level was taken within the horizon. It is reported separately, because the engine also needs that probability.

### 1.1 The race (geometry baseline) [A✓]

- **Driftless random walk**, price x between U above and D below: P(U before D) = (x − D)/(U − D).
- **With drift μ and volatility σ**, k = 2μ/σ², a = U − x, b = x − D: P = (1 − e^{k·b})/(e^{−k·a} − e^{k·b}).
  - B checked the limits: the formula tends to b/(a+b) as μ → 0 and to 1 for large positive μ.
  - `f_race` (447-464) implements it exactly.
- **Horizon-truncated version.** `f_raceH(a, b, σ, μ, h)` (466-482) = P(U first **and** within h bars), by eigen-expansion.
  - `pW = f_raceH(a, b, σ, 0, H)` and `pL = f_raceH(b, a, σ, 0, H)`.
  - `pW + pL` = P(decided within H).
  - `pW/(pW + pL)` = P(U first | decided). `f_invalidation` already uses this form (1360-1365).
- **[NEW-B] "Next taken" vs "destination".**
  - By path continuity the *next* pool touched is either the nearest unswept pool above or the nearest below. "Which liquidity next" is therefore exactly the nearest-pool race (sibling QPOT-06 / ICTS-3 readout).
  - The engine's DOL is a *destination*: the best-scored level, often the outer pool of a stack or a PDH. Its side question is the race between the two sides' **finalists**. Intermediate pools do not change a random-walk race, so geometry still applies.
  - D should answer the finalist race. The "NEXT ▲/▼" readout answers the nearest-pool race.
- **[NEW-B] Parameters that matter** (B2):
  - **drift: use 0.** Drift costs 0.4-6.9% Brier.
  - **σ:** `potSig`, the 50-bar standard deviation of close changes.
  - **horizon:** H, using the conditional `pW/(pW+pL)` form (+1 to +3% Brier over the infinite race).
  - **finalist floor:** at least `minDistATR`, so a level price is "sitting on" does not dominate the race. That is consistent with the proximity taper (666-667).

### 1.2 Previous-candle range states (exhaustive taxonomy) [A✓]

| Class | Rule (t−1 vs t−2) | Practitioner reading |
|---|---|---|
| close-through up | H1 > H2, L1 ≥ L2, C1 > H2 | continuation, "PDH+ next" (draw = H1) |
| sweep-reject up (bear CRT) | H1 > H2, L1 ≥ L2, C1 ≤ H2 | "swept PDH, failed to close above" → target L2 (CRT) or L1 |
| close-through down | L1 < L2, H1 ≤ H2, C1 < L2 | continuation (draw = L1) |
| sweep-reject down (bull CRT) | L1 < L2, H1 ≤ H2, C1 ≥ L2 | target H2 (CRT) or H1 |
| inside | H1 ≤ H2 and L1 ≥ L2 | neutral, "expansion next", both extremes are targets |
| outside, close > H2 / < L2 / inside | H1 > H2 and L1 < L2 | continuation / continuation / neutral |

**Edge cases:**
- **Equal extremes.** H1 = H2 is not a sweep (the engine's equal-high rule).
- **Day boundary.**
  - The engine uses `timeframe.change("D")`, the exchange day (945).
  - ICT uses midnight or 18:00 ET. edgeful uses the NY RTH session.
  - Numbers differ in detail, not in kind.
- **Gap opens beyond H1 or L1.** The prior extreme is taken at the open, so the race is decided at once. Exclude these from first-touch statistics.

### 1.3 ICT daily bias and its weekly version [A✓]

- **Bullish** if C1 > H2 (close-through) or if L1 < L2 and C1 ≥ L2 (swept the prior low, closed back inside). The draw is H1.
- **Bearish** mirrors it. **Neutral** otherwise (inside, or an outside bar closing inside).
- **Weekly:** the same rule on weekly bars for PWH/PWL.
- **TTrades framing** (ttrades.com, no numbers published) [A, not re-fetched]: a continuation day "respects the 50% of the previous day's range" before taking PDH.
- **[NEW-B] Open-source practice** (a GitHub Pine v6 "ICT Daily Bias" indicator, read only):
  - six hand-weighted confluence votes: daily structure/displacement 2, untapped PDH/PDL/PWH/PWL 2, premium/discount 1, day open 1, week open 1, SMT 1;
  - "regime-aware" vote suppression on displacement days;
  - the bias is **frozen at 09:30**;
  - the draw = the nearest untapped pool on the bias side;
  - a self-tracked hit rate ("close direction" and "draw hit") per confluence, **with no geometry or null baseline**.

  That is the same unvalidated-vote design as the engine's D. Its tracker overstates skill, because "draw hit" for the nearest pool is high by geometry alone. Two ideas are worth adopting: freezing the bias at the open, and per-component tracking with a baseline (BIAS-3, BIAS-5).

### 1.4 Candle Range Theory (CRT) [A✓ definitions; CORRECTED sources]

- **Roles.**
  - Candle 1 = range (high, low, 50%).
  - Candle 2 trades beyond one extreme and **closes back inside**; a close beyond voids the setup.
  - Candle 3 targets the opposite extreme, sometimes the 50% first.
- **Variants:**
  - strict vs flexible (extra inside candles, a confirmation candle);
  - HTF range candle (monthly to 1H) with an LTF MSS/FVG entry;
  - practitioners weight "CRT into an HTF key level" and discount "CRT in open space".
- **It is Turtle Soup applied to one candle's range** (sibling ICT/SMC notes; eltraderfinanciado CRT guide).
- **[CORRECTED]** A quoted tradingwyckoff.com as claiming "raw CRT 45-50%, CRT + Wyckoff + killzone + key level 60-65%". B could not find these figures (page blocked; search summary shows the definition only). Treat them as unverified.

### 1.5 Sweep-and-reverse family [A✓]

- **Turtle Soup** (Raschke & Connors, *Street Smarts*, 1995):
  - setup: a new 20-day low, where the prior 20-day low is at least 4 days old;
  - entry: price trades back above the old low → long; stop under the new low. Mirror for shorts.
- **Oops** (Williams): a gap open beyond the prior day's extreme, then a trade back to it.
- **Smash day** (Williams): a close below the prior low (often a 3-8 day extreme); buy above the smash-day high the next day; exit at the first profitable open.
- **[NEW-B] Hikkake** (Chesler): an inside bar, a false break of one side, then a reversal through the other side. Bulkowski reports about 60% of bullish hikkakes meeting their price target in bull markets [weak, vendor statistics]. It is the same family as CRT.

### 1.6 Open-relative bias [A✓]

- **Rule.** Price above the period's opening price → the period's high (or the prior period's high) is the draw.
- **Anchors:** 00:00 NY, 18:00 futures open, Sunday weekly open; ICT's "true day open".
- **Parameters:** the anchor, and the decision time.
- **Engine:** the midnight, London and NY opens are confluence anchors only (964-966, 1931).
- **[NEW-B] Academic intraday version.** "Market intraday momentum": the first half-hour return (from the prior close) predicts the last half-hour return.
  - SPY 1993-2013, predictive R² about 1.6% (Gao, Han, Li & Zhou 2018, JFE 129(2) 394-414) [strong, small effect].
  - It is a statement about the session *close*, not about which liquidity is taken first.
  - The related end-of-day reversal in stocks has decayed since 2019 in a pre-registered retest (arXiv 2611.09286: 3.13 → 1.69 bps/day).

### 1.7 Weekly profiles [A✓]

- Named weekly shapes (low or high of the week formed Monday/Tuesday, midweek reversal, consolidation then Thursday reversal) are covered by `ict_time.final.md` 1.10.
- The arcsine law explains most of the "extreme forms early" effect.
- As a side predictor they reduce to the PWH/PWL race (§2.6).

### 1.8 Order-flow / structure bias, the engine's D [A✓]

- **ICT "institutional order flow."** HTF candles respect bullish PD arrays: bodies close beyond the consequent encroachment (CE). Disrespect flips it. Sources are video lectures with no thresholds.
- **SMC structure.** Swing bias from BOS/CHoCH (`f_structure` 708-782); internal bias flips on a body close through the last swing.
- **Engine** (1891-1898):
  - sV = 0.5·htfBias + 0.3·stfBias + 0.2·exeIB;
  - mV = displacement direction with half-life 12;
  - liqEvt = decayed raid outcomes (1579-1582);
  - D = clamp((wS·sV + wM·mV + wL·liqEvt)/(wS + wM + wL)), with wS/wM/wL = 0.50/0.20/0.30 (155-157);
  - dirSide = ±1 when |D| ≥ `dGate` 0.35.
- **Where D is used:**
  - the draw pillar `0.5 + 0.5·D·side` (691), weight 30 (145);
  - the counter-draw ×`ctrMult` 0.50 (692-693);
  - eligibility, `ctrHold`, `curElig` and `activeCtr` (1975, 2001, 2004, 2029);
  - the HTF objective (1985);
  - the flip alert (1896-1898, 2086-2088);
  - the panel (2338-2341).

### 1.9 Dealing-range position, premium/discount, CLV [A✓]

- **Position.** pos = (x − rangeLow)/(rangeHigh − rangeLow). ICT: buy in discount toward the premium draw.
- **The previous-candle version is CLV.** It carries the geometry: the logistic weight on CLV is +2.3 to +4.7 in every fit (A).
- **[NEW-B]** Sibling ICTS-4 shows that, once the range is ICT's [protected, weak] leg, the premium/discount % in bullish structure *is* the geometric probability that the weak high is taken first. As a separate directional feature it is about 0:
  - ICT rule "bull bias + discount → up" scores 49.5% / 49.1% (sibling);
  - B2's learned HTF-position weight ranged from −0.32 to +0.20 across datasets.

### 1.10 Momentum vs mean reversion; breakout vs sweep [A✓, extended]

- **Breakout:** close beyond the 20-bar extreme → continuation. **Sweep:** wick beyond, close inside → reversal.
- **Academic picture:**
  - **Time-series momentum** at 1-12 months (Moskowitz, Ooi & Pedersen 2012) [strong, outside DOL horizons].
  - **Trending regime from hours to years**, reversion at shorter and longer scales; weak trends persist, strong ones revert (Safari & Schmidhuber, arXiv 2501.16772) [B✓ abstract].
  - **SPY** ρ(1) = −0.081 (7.4 SE), **magnitude-driven** (sign test p = 0.11). Directional reversal appears only at lag 3 (p = 0.02). Short-horizon mean reversion is confined to exchange-traded equities and sovereign bonds; FX, commodities and crypto are random-walk-like at daily scale (arXiv 2606.29591) [B✓ full text].
- **[NEW-B] Additional evidence:**
  - **Crypto, 15 minutes.** Directional reversal is significant in **90% of 183 Binance pairs vs 2.7% of 187 US stocks and ETFs**; "betting against the previous candle" captures most of it; the gross edge is about 1.3 bp, below costs (arXiv 2608.21888) [moderate].
  - **Short-term trend following** stopped working after about 2009 on small-tick futures but survives on large-tick ones (Kurth, Eisler, Rej & Bouchaud, arXiv 2607.01550) [moderate].
  - **Stop-run cascades.** Crossing FX stop clusters adds +0.27 to +2.35 hundredths of a percent for **15 minutes to 2 hours, gone or reversed at 1-2 days** (Osler 2005, JIMF 24(2); detailed in sibling `academic_sr.md` S5/S6) [strong].
  - **Drift bursts** (short explosive trends) occur about weekly across asset classes, and most are followed by reversion (Christensen, Oomen & Renò) [strong, minute scale].
  - **A pre-declared EURUSD H1 study on GitHub:**
    - 20-bar range breakout: mean −0.094R, PF 0.86 (730 trades);
    - failed breakout (the sweep-reversal reading): −0.085R, PF 0.87 (835 trades);
    - 12-bar momentum: −0.062R;
    - all negative after costs in TRAIN and VALIDATION [moderate-weak].

    Neither sign of the same event survives costs.
- **Reading.** The sign of "continuation vs reversal" after a level is crossed depends on the asset, the timescale and the regime, and it decays within hours. It can only be learned per chart, never hard-coded.

### 1.11 Contraction then expansion (Crabel NR4/NR7/inside) [A✓]

- **NR4 / NR7:** the narrowest range of the last 4 / 7 candles.
- **Premise:** contraction is followed by expansion.
- **Evidence:** false in absolute terms, because volatility clusters. After a narrow candle, *both* prior extremes are taken about twice as often, which is geometry (§2.11).

### 1.12 AMD / Power of 3 [CORRECTED operational detail]

As operationalized by Taylor (arXiv 2610.35887, NQ 15m, January 2022 to July 2026):
- **Asia range:** 19:00-00:00 ET.
- **Signal:** London (02:00-05:00) breaches one Asia extreme by δ = 10 points before 04:00, then a later candle closes back inside before 05:00. Bilateral breaches are excluded.
- **[CORRECTED] Outcome.** The **16:00 ET close relative to the Asia midpoint**, not delivery to the opposite Asia extreme. 09:40-10:30 is only the entry window of the mechanical strategy (6 valid trades in 4 years).
- **[CORRECTED] "No directional information beyond the trend regime"** is the author's interpretation of the regime-split table. No trend-only baseline was run; the paper defers that to "Paper 2".

### 1.13 [NEW-B] Taylor / Raschke close-location follow-through ("80-20s")

- **Taylor** (*The Taylor Trading Technique*, 1950), as quoted by Raschke & Connors (*Street Smarts*): when the market closes near its high, there is an "80-90% probability of a follow-through the next morning" (a retest of the high), but the market closes higher only about 50% of the time. Source: Traders' Technical Analysis summary [A, not re-fetched: book].
- **Raschke's "80-20" setup:** the day opens in the bottom 20% of its range and closes in the top 20% (mirror for shorts).
- **Parameters:** the CLV threshold (0.8 or 0.9) and the session definition.
- **What it is:** the cleanest practitioner statement of "previous candle high taken next candle". It is geometry: a close near H1 puts H1 near the next open.

### 1.14 [NEW-B] Taylor 3-day cycle ("Book method")

- **Cycle:** buy day (low made first) → sell day (rally that exceeds the buy-day high) → short-sale day (exceeds the sell-day high, then declines).
- **Statistics:** vendor webinars claim "84%" or "91% of cycles positive", with undefined criteria.
- **Evidence:** none (unfalsifiable as stated). A testable version is just "previous high taken next day", which §2.10 measures (it is geometry).

### 1.15 [NEW-B] Value-area "80% rule" (Market Profile)

- **Rule:** the open is outside the prior value area, then two 30-minute periods close inside it → the far side of the value area is reached "80%" of the time.
- **Sibling `amt_profile.md`:**
  - own test: 61.9% vs a 54.0% matched baseline (n = 42, z 1.2);
  - independent 589-session test: 25-28% vs a 27-29% base rate.
- **Evidence:** moderate (negative).

### 1.16 [NEW-B] The quant formulation: triple barrier, meta-labeling, prequential scoring

- **Triple barrier** (López de Prado, *Advances in Financial Machine Learning*, 2018, ch. 3). Each event is labelled by which of an upper barrier, a lower barrier or a time barrier is hit first. That is exactly the engine's "BSL first / SSL first / undecided within H".
- **Meta-labeling.** A primary rule supplies the *side*; a secondary model learns P(primary rule is right). It is calibrated and only acts on the size. Joubert 2022 (*Journal of Financial Data Science* 4(3)) formalizes it. Applied here:
  - the "primary" is geometry;
  - bias features are the secondary model;
  - its skill must be shown prequentially, against the primary.
- **Prequential (Dawid) scoring.** Each forecast is frozen at issue and scored when it resolves. That gives out-of-sample Brier and log-loss on the chart itself (BIAS-1).
- **[NEW-B] Mixture with a safe expert.** With cumulative-loss weighting between "geometry" and "geometry + features", the combined forecast is at most about log 2 / n worse than the better expert (Cesa-Bianchi & Lugosi 2006) [strong, theory]. B2 shows that the tempered version stays within −1.3% to +2.5% of geometry.

### 1.17 Contents carried over from A without change [A✓]

- Multi-candle reach of prior extremes and the side-level ledger concept.
- The multi-timeframe bias table semantics (Clean 2293-2305, Terminal 2321-2336).
- HTF previous-candle probabilities for 4H/1H (CRT on 4H).

All are detailed in §2 and §3.

---

## 2. Evidence (numbers and sources)

### 2.0 Data and method

**A's data:**

| Dataset | Coverage |
|---|---|
| S&P 500 and NASDAQ Composite daily (`arch` datasets) | 1999-2018, 5,031 bars each |
| GOOG daily | 2004-13 |
| EURUSD 1H, timestamped | 2017-18, 5,000 bars |
| NQ / GC / EURUSD 1H, sibling Yahoo files, no timestamps | 2024-11 to 2026-11, 11,400-12,285 bars |

- Weekly bars are aggregated from daily bars.
- "4bar" = non-clock-aligned 4-hour blocks.

**A's nulls:**
- a volatility-preserving shape shuffle, which keeps candle shapes and volatility clustering and destroys sequence;
- the parameter-free ruin model.

**B's methods:**
- **B1:** A's rule and classes, re-scored on the same cases as geometry.
- **B2:** engine-like races.
  - Pools: unswept pivot pools (5-bar pivots intraday, 3-bar daily); a pool is removed when traded through.
  - At every 6th bar (every 2nd daily), the nearest pool above and the nearest below, each 0.5-8 ATR away (≤ 6 ATR daily).
  - Outcome: which is traded through first within H = 30 bars (H = 10 daily).
  - Predictions are frozen at trial open and scored when the trial resolves (prequential).
  - Features: structure vote sV (HTF = 24-bar blocks, or 5-bar for daily); displacement mV (half-life 12); raid HOLD and REJECT accumulators (half-life 24); previous-HTF-block ICT rule; HTF range position; HTF CRT flag.
- **B2b:** moving-block bootstrap (blocks of 20 consecutive trials, 2,000 draws).
- **B3/B3b:** for every period (week from daily, day from EURUSD 1H, 4-bar and 24-bar blocks from 1H), the f_raceH readout of the prior period's high vs low, with h = bars left in the period; scored against outcomes.

**Caveats:**
- No costs. They are not needed for probability forecasts.
- Overlapping windows mean the effective n is smaller than the count; B2b's block bootstrap accounts for this.
- Daily equity data ends in 2018.

### 2.1 Base rates: how often the previous candle's extremes are taken [A✓]

| Dataset | P(H1 taken next) | P(L1 taken next) | P(both) | P(inside) | P(≥1 side) |
|---|---|---|---|---|---|
| S&P 500 D | 0.513 | 0.446 | 0.090 | 0.130 | 0.870 |
| NASDAQ D | 0.554 | 0.465 | 0.107 | 0.088 | 0.912 |
| GOOG D | 0.503 | 0.453 | 0.089 | 0.133 | 0.867 |
| S&P 500 W | 0.592 | 0.439 | 0.119 | 0.089 | 0.911 |
| NASDAQ W | 0.601 | 0.447 | 0.121 | 0.074 | 0.926 |
| NQ 1H | 0.511 | 0.461 | 0.116 | 0.145 | 0.855 |
| GC 1H | 0.489 | 0.463 | 0.117 | 0.165 | 0.835 |
| EURUSD 1H (24-26) | 0.432 | 0.440 | 0.079 | 0.206 | 0.794 |

**Multi-candle reach:**
- S&P D, either extreme taken within k days: 0.870 / 0.970 / 0.991 / 0.998 for k = 1 / 2 / 3 / 5.
- NQ 1H, the same: 0.855 / 0.945 / 0.970 / 0.987.

**External agreement:**
- **[CORRECTED attribution]** "PDH or PDL broken 90.32% of days (168/186)". Web-search summaries attribute this count to a NexusFi thread (NQ, 2015), which also gives both ≈ 12% and inside ≈ 10%, not to an Elite Trader ES thread [weak, forum count].
- edgeful, ES opening inside the prior range: one side broken 80.25% over 6 months [weak, vendor, not re-fetched].
- **[CORRECTED]** A's edgeful SPY inside-day numbers (PDH 52%, PDL 40%, both 15.28%, 72 days) could not be re-found; only "40% touch PDL" appears in search summaries [weak, unverified].

### 2.2 The ICT previous-candle rule vs the shuffle null [A✓] and vs geometry on the same cases [NEW-B, CORRECTED]

**A's result** (bias side first | decided within 3 candles; real vs null): S&P D 0.688/0.710, NASDAQ D 0.702/0.704, GOOG D 0.697/0.678, S&P W 0.753/0.763, NASDAQ W 0.763/0.758, EURUSD 1H 0.706/0.726, NQ 1H 0.727/0.739, GC 1H 0.708/0.725. Difference −2.2 to +1.9 pp on 13 datasets. B re-ran the same cases (B1) and the real values match.

**[CORRECTED] B1: the rule vs geometry on the rule's own called cases** (K = 3, decided only):

| Dataset | Called / decided | ICT rule | Geometry, same cases | Disagree n | Rule right when they disagree | Neutral share |
|---|---|---|---|---|---|---|
| S&P 500 D | 3,799 / 4,509 | 0.688 | **0.716** | 522 | 0.397 | 0.157 |
| S&P 500 W | 799 / 907 | 0.753 | **0.773** | 106 | 0.425 | 0.119 |
| NASDAQ D | 3,897 / 4,435 | 0.702 | **0.728** | 534 | 0.403 | 0.121 |
| NASDAQ W | 806 / 904 | 0.763 | **0.793** | 102 | 0.382 | 0.108 |
| GOOG D | 1,586 / 1,903 | 0.697 | **0.724** | 293 | 0.427 | 0.167 |
| EURUSD 1H 17-18 | 3,349 / 4,238 | 0.706 | **0.753** | 601 | 0.369 | 0.210 |
| EURUSD D (from 1H) | 152 / 178 | **0.763** | 0.743 | 19 | 0.579 | 0.146 |
| NQ 1H | 7,832 / 9,663 | 0.727 | **0.775** | 1,322 | 0.357 | 0.189 |
| NQ 4bar | 1,823 / 2,306 | 0.758 | **0.803** | 265 | 0.343 | 0.209 |
| GC 1H | 7,546 / 9,547 | 0.708 | **0.755** | 1,302 | 0.363 | 0.210 |
| GC 4bar | 1,816 / 2,356 | 0.717 | **0.776** | 324 | 0.333 | 0.229 |
| EURUSD 1H 24-26 | 8,139 / 10,587 | 0.704 | **0.742** | 1,399 | 0.390 | 0.231 |
| EURUSD 4bar | 1,984 / 2,556 | 0.710 | **0.775** | 347 | 0.314 | 0.224 |

- A's "hard rule 64-73%" (`race.py`, "ICT rule hard") scored the rule's 11-23% neutral days as down calls. The table above is the fair comparison.
- **Conclusion (unchanged, now properly measured):** the rule is a coarse proxy for geometry. Geometry wins on 12 of 13 datasets by +2.0 to +6.5 pp. The exception is EURUSD daily (n = 152).
- **By class** (A, S&P D, close-through up): P(H1) 0.663 vs null 0.708. The headline "after a close above PDH, PDH is taken next about 2/3 of days" is real, and it is all geometry.

### 2.3 CRT, Turtle Soup and AMD [A✓ internal numbers; CORRECTED external]

**CRT target first** (opposite extreme of candle 1 before the candle-2 sweep extreme, within 3 candles, decided cases; real vs null):

| Dataset | Real | Null |
|---|---|---|
| S&P D | 0.458 | 0.458 |
| NASDAQ D | 0.472 | 0.470 |
| GOOG D | 0.435 | 0.431 |
| S&P W | 0.480 | 0.465 |
| NASDAQ W | 0.476 | 0.477 |
| EURUSD 1H | 0.449 | 0.403 |
| EURUSD 4H | 0.399 | 0.391 |
| NQ 1H | 0.430 | 0.411 |
| NQ 4bar | 0.433 | 0.396 |
| GC 1H | 0.412 | 0.426 |
| GC 4bar | 0.388 | 0.425 |
| EURUSD 1H 24-26 | 0.456 | 0.441 |

- After an equity-index up-sweep that closes back inside, the swept high is retaken within 3 days **more** often than the null: S&P D 0.691 vs 0.639; NASDAQ D 0.714 vs 0.650.

**Turtle Soup excess over geometry** (A, `turtle.py`): from −0.129 to +0.082, never reliably positive (S&P D bull −0.105, n 58; NQ 1H −0.02/−0.04; GC 1H +0.003/+0.014).

**[CORRECTED] External CRT evidence:**
- **The "4,200-variant CRT backtest" (Strange Labs, YouTube) that A cited could not be found** by B's searches. Downgraded to unverified (none).
- A different summary (eltraderfinanciado.com CRT guide) reports a published mechanical 1H CRT backtest with **43-49% win rates**, "very similar to flipping a coin", with no R:R or cost analysis [weak].
- **[NEW-B]** A pre-declared EURUSD CRT + supply/demand structural study on GitHub compared target-first with a **distance-matched null**:
  - TRAIN: 16.7% vs 26.3% (n 30);
  - VALIDATION: 36.4% vs 29.9% (n 11);
  - "INCONCLUSIVE (sample)" [weak, but the method is right].
- **[NEW-B]** A GitHub GBPUSD CRT project (100 manually replayed trades, 63% win) is anecdotal: chart replay, selection bias, n = 100 [none].

**AMD** (arXiv 2610.35887, B read the full text):

| Cell | n | Correct |
|---|---|---|
| bullish signal, uptrend | 112 | 61.6% |
| bullish signal, downtrend | 71 | 29.6% |
| bearish signal, uptrend | 153 | 24.8% |
| bearish signal, downtrend | 72 | 70.8% |
| ranging | 33-43 | 37-42%, not significant |

- The signal fires on 44% of days; 57% are delivered before 09:40.
- Robust to δ = 5-20 points and EMA 10-50.
- The pooled bearish signal is 39.9% correct (inverted).
- "After London sweeps the Asia high in a bull market, price closes above the midpoint 75.2% of the time."
- [CORRECTED] The outcome is the 16:00 close vs the Asia midpoint (see §1.12). Grade: moderate.

### 2.4 Geometry vs bias features out of sample [A✓, reproduced exactly]

Outcome: H1 before L1 within 3 candles, decided cases, decision at the close of t−1. Two-fold logistic regression.

| Dataset | Ruin (no fit) acc (Brier) | Geometry + ICT + CRT + CLV + colour + trend + 5-bar return + pivot bias |
|---|---|---|
| S&P 500 D | 0.702 (0.207) | 0.703 (0.198) |
| NASDAQ D | 0.719 (0.199) | 0.720 (0.189) |
| GOOG D | 0.708 (0.188) | 0.710 (0.188) |
| S&P 500 W | 0.771 (0.157) | 0.750 (0.166) |
| NASDAQ W | 0.788 (0.145) | 0.779 (0.153) |
| EURUSD 1H 17-18 | 0.746 (0.172) | 0.743 (0.174) |
| EURUSD 4H | 0.719 (0.181) | 0.720 (0.182) |
| NQ 1H | 0.761 (0.162) | 0.762 (0.162) |
| NQ 4bar | 0.789 (0.149) | 0.789 (0.150) |
| GC 1H | 0.747 (0.173) | 0.745 (0.174) |
| GC 4bar | 0.758 (0.163) | 0.752 (0.163) |
| EURUSD 1H 24-26 | 0.731 (0.185) | 0.732 (0.181) |
| EURUSD 4bar | 0.759 (0.171) | 0.742 (0.174) |

- **From the next open** (open inside [L1, H1]; which extreme is taken first during that candle): ruin 0.756-0.811.
- **Feature weights:** pivot-structure −0.12 to +0.05 on 12 of 13 datasets; ICT class −0.1 to +0.24; CRT −0.23 to +0.35, with mixed signs.
- Features add ≤ ±2 pp accuracy. They improve Brier only where raw ruin is mis-calibrated (daily equities).

### 2.5 Excess over geometry by class × trend regime [A, not re-run]

Regime: close vs EMA20 (±0.5% D, ±1% W, ±0.1% 1H, ±0.2% 4bar).

- **Daily equities.**
  - Ruin is overconfident after close-throughs: S&P D close-through up in an uptrend, P 0.73 vs geometry 0.83 (excess −0.099 ± 0.011, n 972).
  - Close-through down and bear CRT: H1 first +7 to +22 pp above geometry, i.e. daily mean reversion.
- **NQ and GC intraday:** within ±3 pp.
- **EURUSD 1H 24-26:** close-through up −5 to −7 pp (mean reversion).
- **Trend regime:** S&P D uptrend −3.6 pp; S&P W +2.2; NQ 1H +1.5/−1.2.
- These effects are small, and their sign is asset- and timescale-specific.

### 2.6 Open-relative bias [A]

Weekly open, S&P and NASDAQ, decision after 1-2 days of the week:

| Case | "Above the weekly open → PWH first" | Ruin geometry |
|---|---|---|
| S&P, after 1 day | 0.515 | 0.721 |
| S&P, after 2 days | 0.636 | 0.805 |
| NASDAQ, after 1 day | 0.608 | 0.749 |
| NASDAQ, after 2 days | 0.623 | 0.732 |

- Adding the open sign to geometry leaves OOS Brier unchanged (e.g. 0.1777 vs 0.1780). The fitted weight is −0.03 to −0.21.
- EURUSD midnight-open samples (21-92 days) are inconclusive.

### 2.7 Engine-like side selection [A✓] and its replication with confidence intervals [NEW-B]

**A's `sidesel.py`** (nearest pivot pools ≤ 3 ATR, every 3 bars; D proxy = 0.5·HTF + 0.3·STF + 0.2·internal pivot bias, gate 0.35, geometry fallback):

| Dataset | D-first: acc / hit≤H | Geometry: acc / hit≤H |
|---|---|---|
| NQ 1H | 0.562 / 0.679 | 0.602 / 0.698 |
| GC 1H | 0.564 / 0.644 | 0.640 / 0.681 |
| EURUSD 1H | 0.551 / 0.648 | 0.638 / 0.705 |
| S&P D | 0.521 / 0.443 | 0.620 / 0.514 |
| NASDAQ D | 0.544 / 0.462 | 0.635 / 0.518 |

**[NEW-B] B2/B2b.** These use the full engine D proxy: structure, displacement and the raid accumulator with REJECT = reversal, as at 1580-1582. Geometry minus legacy D, first-touch accuracy, with block-bootstrap 95% CIs:

| Dataset | Geometry − legacy D |
|---|---|
| NQ 1H | +7.4 pp [+4.8, +9.7] |
| GC 1H | +3.8 [+1.4, +6.5] |
| EURUSD 1H 24-26 | +5.1 [+2.4, +7.6] |
| EURUSD 1H 17-18 | +8.3 [+4.8, +13.0] |
| S&P D | +6.3 [+3.5, +9.9] |
| NASDAQ D | +5.4 [+2.8, +8.6] |
| GOOG D | +5.6 [+0.5, +10.5] |

- **The legacy D's Brier score is 15.3-24.8% worse than geometry.**
- **Sibling cross-checks:**
  - ict_struct: D 47.4-52.7% on 8 markets vs random walks 48.4-52.1%;
  - A's `ict_struct_tools/results.txt`: engine D (|D| ≥ gate) 0.543 / 0.488 / 0.490 on NQ / GC / EURUSD, htfBias alone 0.502-0.522 [B✓ file read];
  - REG-3: −9 to −12 pp on 23 series.
- Grade for "D has no side skill and costs accuracy against geometry": **strong** (four independent replications, CIs exclude 0).

### 2.8 [NEW-B] Prequential test of the BIAS-1 side model (B2)

Brier skill vs driftless infinite-horizon geometry (positive = better). The column "SGD (A's spec)" is the learner A specified: 9 features, w0 = geometry, η = 0.05/√(1+n/200), λ = 0.01.

| Dataset (resolved / undecided) | Geometry acc | Drift (engine `potMu`) | **Horizon-conditioned geoH** | Calibration (b0 + slope) | SGD (A's spec) | Tempered mixture | Legacy D |
|---|---|---|---|---|---|---|---|
| NQ 1H (1,265 / 265) | 0.710 | −4.1% | **+1.4%** | −0.4% | −2.3% | −0.7% | −21.3% |
| GC 1H (1,339 / 300) | 0.673 | −6.7% | −0.4% | −0.8% | −2.9% | −1.1% | −15.7% |
| EURUSD 1H 24-26 (1,430 / 393) | 0.703 | −3.2% | **+1.0%** | −0.9% | −2.4% | −1.1% | −15.3% |
| EURUSD 1H 17-18 (568 / 151) | 0.706 | −6.9% | **+2.1%** | −0.6% | −3.0% | −1.3% | −24.8% |
| S&P D (1,332 / 713) | 0.713 | −0.4% | **+1.9%** | 0.0% | −1.7% | −0.3% | −21.0% |
| NASDAQ D (1,342 / 662) | 0.728 | −0.5% | **+3.0%** | +0.4% | −2.3% | 0.0% | −18.7% |
| GOOG D (573 / 284) | 0.745 | −1.7% | +1.2% | +2.8% | +2.0% | +2.5% | −20.6% |

**Block-bootstrap 95% CIs** (`out_b2b.txt`):
- SGD minus geometry Brier: +0.0043 [+0.0005, +0.0078] (NQ), +0.0059 [+0.0018, +0.0101] (GC), +0.0048 [+0.0012, +0.0090] (EURUSD 1H 24-26). The other four intervals include 0.
- geoH minus geometry: −0.0040 [−0.0069, −0.0014] (EURUSD 17-18), −0.0054 [−0.0089, −0.0020] (NASDAQ D). The others are borderline.

**Learned weights** (end of sample) change sign across datasets:

| Feature | Range |
|---|---|
| Structure vote | −0.31 to +0.12 |
| HOLD | −0.23 to +0.15 |
| REJECT | −0.31 to +0.10 |
| ICT rule | −0.19 to +0.17 |
| HTF position | −0.32 to +0.20 |
| CRT | −0.19 to +0.19 |

The geometry slope is 0.90-1.46: geometry is slightly under-confident in this race design. Contrast A's previous-candle race, which is over-confident on daily equities.

**Undecided within H:** 15-24% of races intraday, 33-35% daily.

**Consequences for BIAS-1 (all [CORRECTED] relative to A's spec):**
- the prior is the horizon-conditioned race with **zero drift**;
- features are learned in a shadow model and applied **only behind a significance gate**;
- report Brier and log-loss with n.

### 2.9 [NEW-B] Calibration of the previous-candle readout (BIAS-3): B3 / B3b

Readout: P(prior high first), P(prior low first), P(neither) from f_raceH with h = bars left in the period.

| Periods | Decisions | Which-first acc (decided) | Brier skill vs base rates (U / D / N) | Calibration of P(neither) |
|---|---|---|---|---|
| S&P W from D | all bars, n 1,018 | 0.767 | +0.31 / +0.24 / +0.28 | p 0.04 → obs 0.10; otherwise ±0.04 |
| NASDAQ W from D | all bars, n 949 | 0.764 | +0.22 / +0.23 / +0.18 | p 0.04 → obs 0.14 |
| EURUSD D from 1H | all bars, n 1,375 | 0.701 | +0.19 / +0.26 / +0.36 | p 0.36 → obs 0.24 (2017-18 trend) |
| NQ / GC / EURUSD 4-bar from 1H | all bars, n 2,765-3,445 | 0.769-0.786 | +0.18-0.21 / +0.13-0.21 / +0.05-0.16 | **p 0.03 → obs 0.18-0.24; p 0.17 → 0.36-0.43** |

**At the period open only** (one prediction per period; B3b):

| Periods | P(decided) raw | Observed | Two-parameter calibration, Brier change | Which-first acc |
|---|---|---|---|---|
| S&P / NASDAQ W | 0.922 / 0.907 | 0.905 / 0.906 | −0.5% / +0.5% (no gain) | 0.80 / 0.81 |
| NQ / GC / EURUSD 4-bar | 0.889 / 0.860 / 0.887 | 0.834 / 0.811 / 0.789 | **−2.9% / −2.5% / −6.1%** | 0.82 / 0.79 / 0.75 |
| NQ / GC / EURUSD 24-bar | 0.873 / 0.858 / 0.892 | 0.873 / 0.848 / 0.835 | +2.4% / −0.3% / +1.7% (no gain) | 0.81 / 0.80 / 0.77 |

**Reading:**
- Which-first is calibrated everywhere and needs no correction.
- "Will either extreme be taken this period" is over-predicted on short intraday periods, and badly so late in a period. The cause is the volatility clock, compare sibling ict_time TIME-1/2.
- So: split the readout into P(decided) and P(high first | decided), and calibrate P(decided) per timeframe and elapsed third of the period, behind a gate.

### 2.10 [NEW-B] Taylor / Raschke follow-through replicated (B1)

Next candle after the previous candle closed in the top 20% (CLV ≥ 0.8) or top 10% of its range:

| Dataset | CLV ≥ 0.8: P(H1 exceeded) | CLV ≥ 0.9: P(H1 exceeded) | CLV ≥ 0.8: P(next close up) | Base P(close up) | CLV ≤ 0.2: P(L1 taken) |
|---|---|---|---|---|---|
| S&P 500 D | 0.753 (n 1,614) | 0.786 | 0.501 | 0.531 | 0.741 |
| S&P 500 W | 0.860 | 0.909 | 0.536 | 0.556 | 0.817 |
| NASDAQ D | 0.794 | 0.813 | 0.531 | 0.540 | 0.770 |
| NASDAQ W | 0.890 | 0.941 | 0.567 | 0.546 | 0.866 |
| GOOG D | 0.834 | 0.903 | 0.520 | 0.520 | 0.782 |
| EURUSD 1H 17-18 | 0.829 | 0.877 | 0.455 | 0.505 | 0.780 |
| NQ 1H | 0.842 (n 2,870) | 0.900 | 0.508 | 0.519 | 0.842 |
| NQ 4bar | 0.850 | 0.917 | 0.537 | 0.537 | 0.838 |
| GC 1H | 0.806 | 0.879 | 0.498 | 0.507 | 0.836 |
| GC 4bar | 0.817 | 0.904 | 0.540 | 0.519 | 0.858 |
| EURUSD 1H 24-26 | 0.763 | 0.813 | 0.430 | 0.453 | 0.757 |
| EURUSD 4bar | 0.804 | 0.898 | 0.474 | 0.475 | 0.795 |

- **Raschke 80-20** (open in the bottom 20%, close in the top 20%): P(H1 exceeded) 0.750-0.935; next close up 0.43-0.58.
- **The practitioner claim holds:** "80-90% retest, about 50% close in that direction".
- It is pure geometry plus no direction, which is exactly what the race readout gives. The CLV-bucket table belongs in BIAS-3 as a chart-learned base rate, not as a separate directional signal.

### 2.11 Contraction (Crabel) [A✓]

| | P(next range > 20-bar median) | P(next bar takes both prior extremes) |
|---|---|---|
| base | 0.48-0.50 | 0.08-0.14 |
| NR7 | **0.26-0.45** (below base on every dataset) | **0.16-0.29** |
| inside | 0.32-0.57 | 0.12-0.21 |

### 2.12 External evidence table (verified status)

| # | Claim | Source | Result | Status / grade |
|---|---|---|---|---|
| X1 | PDH/PDL break → session direction | edgeful, YM, 6 months | PDH broken → green 67% (open→close), 81% on another page; PDL broken → red 62% (open→close), 63-66% elsewhere | [CORRECTED] the pages differ; host blocked; **weak** |
| X2 | Gap beyond PDH/PDL retraces | edgeful outside-days, NQ | 65% / 58%; small gaps 93% / 83%, large 25% / 0% (distance gradient) | [A, not re-fetched] **weak** |
| X3 | Inside-day breakout | edgeful, SPY June-December 2024 | 52% / 40% / both 15.28% | [CORRECTED] unverifiable; **weak** |
| X4 | Smash day | RogueQuant substack | S&P longs 80% win, PF 6.94 | [CORRECTED] single paywalled source, sample and costs unclear; a reader comment disputes significance; **weak** |
| X5 | AMD / Power of 3 | arXiv 2610.35887 | §2.3 | B✓ full text; **moderate** |
| X6 | CRT 4,200-variant placebo | Strange Labs video | survivors tie a coin flip | [CORRECTED] not found; **none** (replaced by X15, X16) |
| X7 | Equity autocorrelation is magnitude, not sign | arXiv 2606.29591 | ρ(1) −0.081, 7.4 SE, sign p 0.11; lag-3 sign p 0.02 | B✓ full text; **moderate** |
| X8 | Trend vs reversion by timescale | arXiv 2501.16772 | trending from hours to years | B✓ abstract; **moderate** |
| X9 | OHLCV intraday momentum on MNQ | arXiv 2605.04004 | 0/14 families pass; ORB long T 0.88 | B✓ abstract; **moderate** |
| X10 | Apparent skill vs nulls | arXiv 2611.12141 | 0/160 cells beat no-change; a sign-randomised null reproduces about 95% of RankIC | B✓ full text; **moderate (method)** |
| X11 | Time-series momentum | Moskowitz, Ooi & Pedersen 2012 | 1-12 months | **strong** (not at DOL horizons) |
| X12 | Sweeps → continuation | Mahadzva SSRN 7430998 (sibling E7) | 65/66 folds | [A, not re-fetched] **moderate** |
| X13 | Equal highs vs plain swings | sibling E6 | < 1 pp beyond distance | **moderate** |
| X14 | Close near the high → retest next session 80-90%, close higher about 50% | Taylor via Raschke & Connors | replicated in §2.10 | [NEW-B] **moderate** |
| X15 | Mechanical 1H CRT | eltraderfinanciado summary | 43-49% win, "coin flip" | [NEW-B] **weak** |
| X16 | EURUSD H1 breakout vs failed breakout, pre-declared | GitHub research repo | −0.094R vs −0.085R, both negative after costs | [NEW-B] **moderate-weak** |
| X17 | Stop-run cascades | Osler 2005 (via academic_sr S6) | +0.27-2.35 hundredths of a percent for 15 minutes-2 hours; reversed at 1-2 days | [NEW-B] **strong** |
| X18 | Intraday momentum, first half-hour → last half-hour | Gao et al. 2018 JFE | R² about 1.6%, SPY 1993-2013 | [NEW-B] **strong** (small, close-specific) |
| X19 | End-of-day reversal decay | arXiv 2611.09286 | 3.13 → 1.69 bps/day after 2019 | [NEW-B] **moderate** |
| X20 | Crypto 15m directional reversal | arXiv 2608.21888 | 90% of pairs vs 2.7% of US equities | [NEW-B] **moderate** |
| X21 | Short-term trend decay | arXiv 2607.01550 | collapse on small-tick futures since 2009 | [NEW-B] **moderate** |
| X22 | 80% rule | sibling amt_profile | 25-28% vs a 27-29% base rate | [NEW-B] **moderate (negative)** |
| X23 | Open-source daily-bias indicator self-tracking | GitHub Pine v6 | per-vote hit rate with no baseline | [NEW-B] n/a (design lesson) |
| X24 | Taylor 3-day cycle "84-91% positive" | vendor webinars | undefined criteria | [NEW-B] **none** |

### 2.13 Net reading for the forecasting problem

- **Where (which side).** Relative distance between the two finalists is the best single predictor (strong). Every named bias method adds at most a few points, and several subtract points as hard rules. The engine's current vote subtracts 4-8 pp (strong).
- **How likely.**
  - Horizon-conditioned, zero-drift geometry is calibrated to within a few points for side races (67-75% accuracy).
  - Previous-candle which-first: 70-82%.
  - P(decided within the period) needs calibration on short intraday periods.
- **When.**
  - At least one prior extreme is taken within 1 candle 79-93% of the time, and within 2 candles 92-99%.
  - After narrow candles, both sides are taken about twice as often.
  - Late-period odds need the volatility clock (ict_time).
- **What D should be.** The calibrated P(buy-side finalist first). Every other bias input may move it only by weight the chart has proven prequentially.

---

## 3. Engine gap analysis (`baseline_v2.pine`) [A✓, CORRECTED line refs and items]

| # | Concept | Status | Lines | What the engine does / how it differs |
|---|---|---|---|---|
| 1 | Race geometry between opposing targets | **partial** | `f_race` 447-464, `f_raceH` 466-482; used only in `f_invalidation` **1343**-1365 [CORRECTED from 1334] and `f_raceAdj` 1367-1371 | Correct math, but used only for target-vs-invalidation odds (R:R, WIN≤H). The side choice ignores it |
| 2 | Drift in races | **wrong (evidence)** [NEW-B] | `f_invalidation` 1360-1362 (`m = potMu * tgt.side`); `potMu` 917 (`driftW` 0.5, 185) | The race uses drift; B2 shows drift costs 0.4-6.9% Brier on side races. Siblings QPOT-01 / REG-3 agree → BIAS-8 |
| 3 | Side choice / draw vector D | **wrong (no skill)** [upgraded to strong evidence] | D 1891-1898; pillar 691; ×`ctrMult` 692-693; eligibility 1975; `ctrHold` 2001; `curElig` 2004; `activeCtr` 2029; HTF objective 1985; flip 1896-1898 and 2086-2088; panel 2338-2341 | Hard-coded vote, measured at coin-flip skill, costs 3.8-8.3 pp (B2). Its prominence: heaviest pillar (30), ×0.5 counter-draw, gates eligibility |
| 4 | Score staleness for a side model | **design constraint** [NEW-B] | `track` resets `mult` at **657** [CORRECTED from 659]; D computed at step 14 (1891), scores at step 17 (1943-1948) | A side model needs this bar's draw-free scores. Today `evaluate` bakes the draw in (691-695) → split it into two phases (BIAS-1) |
| 5 | Raid-outcome sign | **wrong for REJECT** [A✓] | 1579-1582 | REJECT (close back inside) pushes D toward reversal. Fix = ICT-9 (neutral REJECT, HTF-conditioned HOLD) |
| 6 | Previous-candle state of HTF/STF/EXE | **partial** [A✓] | `f_rangeTrack` 807-833; 945-961; registry 1790-1799 | PDH/PDL/PWH/PWL exist with exact anchors. There is no candle class, no prior close or CLV, no 4H/1H prior candle, no which-first / neither probability, no base rates |
| 7 | ICT daily bias / CRT | **missing (correctly as a forecast)** | — | Geometry-equivalent or worse. Readout, alerts and learned features only (BIAS-3 / 7 / 1) |
| 8 | Open-relative bias | **present as confluence only (correct)** | 964-966, 1931 | Keep. No directional use |
| 9 | Weekly profiles, Taylor 3-day cycle, 80% rule | **missing (correct)** | — | Reduce to the PWH/PWL or previous-candle race |
| 10 | Dealing range / premium-discount | **partial** | Terminal 2324-2333; `htfEQ`/`dayEQ` 967-968 | Display and confluence only. Range = last pivots, not ICT's leg (sibling ICTS-4). Directional skill about 0 |
| 11 | Trend regime | **missing** | — | Mixed evidence (AMD regime cells vs ±2-4 pp of variable sign). A learned feature only (REG-6) |
| 12 | Momentum vs mean reversion | **partial** | empirical surface 1526-1532, `f_empPoT` 1284-1301 (split by `htfBias`) | `htfBias` has no skill, so the 3-way split dilutes samples. `f_empPoT` already falls back to pooled rows below `nMin` (1292-1299), but not when the split row is full yet uninformative → REG-1 (absorbs BIAS-6) |
| 13 | Contraction → both sides | **partial** | `coilScore` 888-891 | Density only. Use it for "both sides" odds in the readout, not as an expansion prior |
| 14 | AMD timing | **partial** | `f_kzAff` 597-602 | Timing affinity only. Direction must not come from the sweep |
| 15 | Side-level ledger ("which side first") | **missing** | ledger 1426-1499 grades only the active DOL's hit within H vs `f_potBase` (1314-1322) | EDGE is distance-matched (good), but neither the side forecast nor D is tested → BIAS-1 |
| 16 | Bias table | **present, unmeasured** | Clean 2293-2305; Terminal 2321-2336 | Swing (else internal) bias. About 50% skill. Cells have no tooltip; `table.cell` accepts `tooltip` and `table.cell_set_tooltip` exists (reference/table.md) |
| 17 | Draw-flip alert | **noisy by design** [NEW-B] | 1896-1898, 2086-2088 | Fires on every crossing of ±dGate. With a geometry-driven D it would fire after most sweeps unless persistence is added (BIAS-2) |
| 18 | Pine restriction relevant to the specs | **constraint** [NEW-B] | — | Functions cannot reassign fundamental-type globals. Docs: "Unlike some of the other built-in types, namely *fundamental* types, scripts can modify globally-assigned arrays from within local scopes" (`language/arrays.md` 263). Keep learner state in arrays; compute gate booleans at the call site |

---

## 4. Proposals (best first; 8)

**General Pine v6 notes for every spec:**
- All new state updates run inside the confirmed-bar ENGINE block (`if barstate.isconfirmed`, 1518). Sides and scores are computed on `inCalc` bars only.
- There are **no new `request.security` calls**.
- Functions must be declared before first use: after `f_race` 447, `f_raceH` 466, `f_logit` 484, `f_sigm` 488.
- Globals go in STATE (1020-1080).
- One declaration per line.
- UDT fields may hold arrays. Docs: "Programmers can explicitly define variables, parameters, and fields that accept references to objects of specific collection types" (`language/type_system.md` 781).
- `timeframe.change(series string) → series bool` (`reference/timeframe.md` 109-121).
- `table.cell(..., tooltip)` takes a series string (`reference/table.md`, the `tooltip` argument).

**Overlap map with sibling proposals:**

| This report | Siblings |
|---|---|
| BIAS-1 | The learner follows CAL-4's "measure, apply when proven" gate and can reuse its adPredictor update. It **replaces ICTS-1's probe** (ICTS-1 says so) and is the home for REG-6 features |
| BIAS-2 | Supersedes REG-3 / ICTS-1 as the *default* draw source. Those remain as the "Structure (gated)" option. REG-4 (`ctrMult` 0.85) applies to the legacy option |
| BIAS-8 | Same direction as QPOT-01 (drift 0); extends it to the race in `f_invalidation` |
| BIAS-3 | The Clean-table tooltip; the DBIAS bit in ICT-1; feeds BIAS-1 features and BIAS-7 |
| BIAS-4 | Implement as `ict_liq.final.md` ICT-9 |
| BIAS-5 | Complements ICTS-4's "W1st %" |
| BIAS-6 | Merged into REG-1 |
| BIAS-7 | Aligns with ICTS-6 / WYK-4 (event layer, zero forecast weight) |

### BIAS-1 (P1, M) · Side ledger + calibrated side model: P(best buy-side target before best sell-side target), with gated feature learning [A, CORRECTED]

**Why.**
- The core question is which side is reached first. The engine neither measures it nor models it.
- Horizon-conditioned zero-drift geometry answers it at 67-75% (pool races) or 70-82% (previous candle), calibrated (§2.4, §2.8).
- Bias features have no stable sign (§2.8), and A's ungated SGD cost 1.7-3.0% Brier on 6 of 7 datasets (CI excludes 0 on 3).
- So the model must start at geometry, measure every feature, and apply features only after this chart proves they help.

**What changed vs A's spec:**
- the prior is `f_raceH`-conditioned with **zero drift** (BIAS-8), not `f_race(…, potMu)`;
- `sdMode` gate: "Measure" by default; "Apply when proven" requires a significant prequential log-loss gain;
- scoring is split into two phases, so finalists use **this bar's** draw-free scores, not the previous bar's;
- the finalist floor is `minDistATR`;
- learner state lives in arrays, because Pine functions cannot reassign fundamental globals (§3 #18).

**TYPES** (after `Trial`, around 396):
```pine
type SideTrial
    float        up        // near edge of the buy-side finalist at open
    float        dn        // near edge of the sell-side finalist at open
    float        pGeo      // zero-drift, horizon-conditioned race (prior)
    float        pMod      // shadow model at open
    float        pUse      // probability actually used / shown at open
    float        pLeg      // legacy structure vote as a probability (0.75 / 0.5 / 0.25)
    array<float> x
    int          bar0
```

**Level fields** (after `float score`, 347): `float rawND = 0.0` and `float scoreND = 0.0`.

**LEVEL METHODS: two-phase scoring.**
- In `evaluate` (661-696), drop the `dirD` parameter.
- Replace lines 691-695 (draw, counter-draw, raw, score) with:
```pine
    this.rawND   := (wProx * this.prox + wFresh * this.fresh + wConf * this.conf + wDens * this.dens) / wSum
    this.scoreND := f_clamp(100.0 * this.rawND * this.mult, 0.0, 100.0)
    this.scoreND

// second phase, after the side model: identical to the old formula,
// 100·mult·(Σ w·pillar)/wSum, with the draw pillar and ctrMult folded in
method applyDraw(Level this, float dirD, float gate) =>
    this.draw := 0.5 + 0.5 * dirD * this.side
    if dirD * this.side <= -gate
        this.mult *= ctrMult
    this.score := f_clamp(100.0 * (this.rawND + wDraw * this.draw / wSum) * this.mult, 0.0, 100.0)
    this.score
```

**INPUTS** (G_FLOW, after 166) and derived constants (after 309):
```pine
string drawSrc  = input.string("Calibrated", "Draw Source", options = ["Calibrated", "Structure Vote"], group = G_FLOW,
  tooltip = "Calibrated: D = 2·P(best buy-side target is reached before the best sell-side target) − 1, from first-passage geometry; bias features move it only after they have out-predicted geometry on this chart. Structure Vote: the classic MTF structure / displacement / raid vote.")
float  sideGate = input.float(0.10, "Side Gate |P − 50%|", minval = 0.0, maxval = 0.4, step = 0.01, group = G_FLOW)
string sdMode   = input.string("Measure", "Bias Features", options = ["Off", "Measure", "Apply when proven"], group = G_FLOW,
  tooltip = "Measure: structure, displacement, raids, previous-candle class, HTF position and CRT are scored against geometry on this chart (Terminal panel) but do not move D. Apply when proven: they move D only while their out-of-sample log-loss gain is significant.")
float dGateEff = drawSrc == "Calibrated" ? 2.0 * sideGate : dGate
int   sdSp     = math.max(1, int(math.round(H / 5.0)))
```

**STATE** (after 1080):
```pine
var array<float>     sdW       = array.from(0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
var array<float>     sdW0      = array.from(0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
var array<SideTrial> sideT     = array.new<SideTrial>()
// [0 n, 1 ΣΔLL, 2 ΣΔLL², 3 Brier geo, 4 Brier used, 5 Brier legacy, 6 hits used, 7 undecided, 8 ambiguous]
var array<float>     sdSt      = array.new<float>(9, 0.0)
var bool             sdApply   = false
var float            pUp       = 0.5
var float            pGeoS     = 0.5
var float            liqHold   = 0.0
var float            liqRej    = 0.0
var int              sideC     = 0
var int              sidePend  = 0
var int              sidePendN = 0
```

**STATE HELPERS** (after `f_raceAdj`, 1371):
```pine
f_dot(array<float> w, array<float> x) =>
    float z = 0.0
    for i = 0 to w.size() - 1
        z += w.get(i) * x.get(i)
    z

// Zero-drift race between two targets a above / b below, conditioned on a decision within h bars (BIAS-8).
f_sideP(float a, float b, float sig, int h) =>
    float pw = f_raceH(a, b, sig, 0.0, h)
    float pl = f_raceH(b, a, sig, 0.0, h)
    pw + pl > 1e-9 ? pw / (pw + pl) : f_race(a, b, sig, 0.0)

// Prequential booking of one resolved side trial (y = 1: buy-side target first), then one shadow-learner step.
f_sideBook(SideTrial s, int y) =>
    float lg = y == 1 ? -math.log(math.max(s.pGeo, 1e-4)) : -math.log(math.max(1.0 - s.pGeo, 1e-4))
    float lm = y == 1 ? -math.log(math.max(s.pMod, 1e-4)) : -math.log(math.max(1.0 - s.pMod, 1e-4))
    float dl = lg - lm
    sdSt.set(0, sdSt.get(0) + 1.0)
    sdSt.set(1, sdSt.get(1) + dl)
    sdSt.set(2, sdSt.get(2) + dl * dl)
    sdSt.set(3, sdSt.get(3) + math.pow(s.pGeo - y, 2))
    sdSt.set(4, sdSt.get(4) + math.pow(s.pUse - y, 2))
    sdSt.set(5, sdSt.get(5) + math.pow(s.pLeg - y, 2))
    sdSt.set(6, sdSt.get(6) + ((s.pUse >= 0.5) == (y == 1) ? 1.0 : 0.0))
    float p  = f_sigm(f_dot(sdW, s.x))
    float lr = 0.05 / math.sqrt(1.0 + sdSt.get(0) / 200.0)
    for i = 0 to sdW.size() - 1
        float wi = sdW.get(i)
        sdW.set(i, wi + lr * ((y - p) * s.x.get(i) - 0.01 * (wi - sdW0.get(i))))
    y
```
CAL-4's Bayesian probit (adPredictor) update can replace the SGD step without changing anything else. The gate makes the learner's quality matter only once it has proven itself.

**ENGINE.**

*Step 1* (1535): decay both new accumulators with `liqHL`:
```pine
    liqHold *= math.pow(0.5, 1.0 / liqHL)
    liqRej  *= math.pow(0.5, 1.0 / liqHL)
```

*Step 3* (1580-1582, inside `if hit and lv.isLiquidity()`, next to ICT-9's new `liqEvt` mapping):
```pine
                    bool hold = lv.side == 1 ? close > lv.top : close < lv.bottom
                    bool rej  = lv.side == 1 ? close < lv.price : close > lv.price
                    liqHold := f_clamp(liqHold + (hold ? lv.side * lv.tier() : 0.0), -1.0, 1.0)
                    liqRej  := f_clamp(liqRej + (rej ? -lv.side * lv.tier() : 0.0), -1.0, 1.0)
```

*Step 2b* (new, right after the Trial loop at 1557, before sweeps delete levels):
```pine
    if sideT.size() > 0
        for i = sideT.size() - 1 to 0
            SideTrial s = sideT.get(i)
            if bar_index > s.bar0
                bool u = high > s.up
                bool d = low < s.dn
                if u != d
                    f_sideBook(s, u ? 1 : 0)
                    sideT.remove(i)
                else if u and d
                    sdSt.set(8, sdSt.get(8) + 1.0)
                    sideT.remove(i)
                else if bar_index - s.bar0 >= H
                    sdSt.set(7, sdSt.get(7) + 1.0)
                    sideT.remove(i)
    float sdN = sdSt.get(0)
    if sdN >= 200
        float mD = sdSt.get(1) / sdN
        float vD = math.max(sdSt.get(2) / sdN - mD * mD, 1e-12)
        // design effect 2 for overlapping windows; one-sided ~97.5% bound
        sdApply := sdMode == "Apply when proven" and mD - 2.0 * math.sqrt(2.0 * vD / sdN) > 0
```

*Step 14* (1891-1898):
- Keep the legacy formula and add `float drawLeg = drawD` after 1894.
- Wrap the legacy flip block 1896-1898 in `if drawSrc != "Calibrated"`.

*Step 17* (1948): call `lv.evaluate(close, atr, anchors, confTol, nz(potSig), nz(potMu))`, with no `drawD`.

*Step 17b* (new, after the scoring loop and before step 18, inside `if inCalc`):
```pine
        float upE  = na
        float dnE  = na
        float kU   = -1.0
        float kD   = -1.0
        float dMin = math.max(minDistATR * atr, syminfo.mintick)
        for lv in pool
            float dd = lv.distance(close)
            if dd >= dMin and dd <= maxATR * atr
                if lv.side == 1 and lv.scoreND > kU
                    kU  := lv.scoreND
                    upE := lv.nearEdge()
                else if lv.side == -1 and lv.scoreND > kD
                    kD  := lv.scoreND
                    dnE := lv.nearEdge()
        bool sideOK = not na(upE) and not na(dnE) and nz(potSig) > 0
        if sideOK
            pGeoS := f_sideP(upE - close, close - dnE, potSig, H)
            float hPos = not na(htfRH) and not na(htfRL) and htfRH > htfRL ? f_clamp(2.0 * (close - htfRL) / (htfRH - htfRL) - 1.0, -1.0, 1.0) : 0.0
            // pcRuleH / pcCrtH come from BIAS-3 (0 until it is built)
            array<float> xv = array.from(1.0, f_logit(pGeoS), sV, mV, liqHold, liqRej, float(pcRuleH), hPos, float(pcCrtH))
            float pMod = f_sigm(f_dot(sdW, xv))
            pUp := sdApply ? pMod : pGeoS
            float pLeg = drawLeg >= dGate ? 0.75 : drawLeg <= -dGate ? 0.25 : 0.5
            if sdMode != "Off" and bar_index % sdSp == 0 and sideT.size() < 64
                sideT.push(SideTrial.new(upE, dnE, pGeoS, pMod, pUp, pLeg, xv, bar_index))
        // BIAS-2: the draw source (persistence: a new side must hold for 2 confirmed bars)
        if drawSrc == "Calibrated"
            drawD := sideOK ? 2.0 * pUp - 1.0 : 0.0
            int cand = drawD >= dGateEff ? 1 : drawD <= -dGateEff ? -1 : 0
            sidePendN := cand == sidePend ? sidePendN + 1 : 1
            sidePend  := cand
            if cand != sideC and sidePendN >= 2
                drawFlip := cand != 0 and sideC != 0
                sideC    := cand
                if cand != 0
                    lastDirSide := cand   // keeps the flip alert text (2087) correct
            dirSide := sideC
        for lv in pool
            lv.applyDraw(drawD, dGateEff)
```

**Scope notes:**
- `sV`, `mV` and `dirSide` are declared in step 14 in the same engine block, so the nested block can read them and reassign `dirSide` with `:=`.
- `drawFlip` is a global (1513).
- On non-`inCalc` bars nothing is scored and selection does not run, so the legacy D left there is harmless.

**UX.**
- **Terminal DRAW row** (2338-2341, using `dGateEff`): `▲ BSL 1st 63% · GEO` (or `· LEARNED`) and `skill +1.2% · n 412`, where skill = 1 − Brier used / Brier geometry.
- **Full view:** `legacy vote skill −19%`, the learned weights with names, and `undecided 21%`.
- **Clean:** append to the label tooltip (2206): `"\nBuy-side target first: 63% (geometry 63%) · side forecasts scored: 412"`.
- **Data Window:** `plot(pUp * 100.0, "P(buy-side first) %", display = display.data_window)`.

**Cost.**
- Finalists: one pass over the pool (≤ 80).
- `f_sideP`: 2 × 12-20 series terms for typical L/σ.
- Trials: ≤ 64 × 9 multiplies per resolution.
- Negligible next to step 17.

**Expected value.**
- The trader's central question gets an honest, calibrated, self-measured answer.
- Every bias claim (structure, raids, CRT, P/D) becomes a measured number on the chart.
- With no proven skill the model stays at geometry (B2: tempered or gated mixtures stay within −1.3% to +2.5% of geometry).

**Evidence:** strong (geometry, D null) / moderate (gate design: B2, CAL-4).

**Risk.**
- Overlapping trials (spacing `sdSp`) shrink the effective n. The gate uses a design effect of 2.
- The gate may never open, which is the expected outcome on most charts. The panel says "measured, not applied".
- The finalist choice uses draw-free scores, so there is no circularity.

**Effort:** M.

### BIAS-2 (P1, S) · Draw Source = Calibrated: D := 2·P(buy-side finalist first) − 1 [A, CORRECTED]

**Why.**
- Choosing the side by the legacy vote loses 3.8-8.3 pp of first-touch accuracy, and every CI excludes 0 (§2.7). It also loses 2-7 pp of hit-within-H (A).
- The decision history requires "draw-side first with counter-draw fallback". This keeps the architecture and changes what the draw *is*.
- With the default weights, the draw pillar (691) becomes the calibrated P(this side's target is reached first).

**Algorithm.** It is in BIAS-1 step 17b:
- `drawD := 2·pUp − 1`, or 0 when a side has no finalist. [CORRECTED: A fell back to the legacy vote.]
- Dead band `sideGate` 0.10, i.e. a side needs P ≥ 0.60.
- 2-bar persistence before `dirSide` and `drawFlip` change.
- `dGateEff` replaces `dGate` in `applyDraw` and in the panel (2338).
- The legacy vote stays as "Structure Vote". With ICTS-1 or REG-3 built, those gates apply to that option.

**Edge cases:**
- **A finalist inside `minDistATR`.** It is excluded, so a level price is sitting on cannot swing D. This also protects against the overhaul-P1 "taper swaps the target just before the hit" pattern.
- **After a sweep.** The new finalist on the swept side is farther, so D often flips to the other side. Geometry alone reproduces the ICT heuristic "after BSL is taken, the draw becomes SSL", and the 2-bar persistence prevents flip spam.
- **Arrays as finalists** (FVG/OB): they are reached on a touch. The trial uses a strict trade-through, a conservative bias of one tick.

**[NEW-B] Honest caveat (README and tooltip).**
- Geometry-chosen sides raise raw **DOL HIT %**.
- They **cannot** raise the ledger's **EDGE**, which is matched on distance (1461-1499). Geometry is distance.
- So the README must say: "Draw = which side's target is likelier to be reached first; it is not a claim of edge beyond distance."

**README.** Redefine D: "D = 2·P(best buy-side target reached before best sell-side target) − 1, from first-passage geometry; structure, raids and candle context move it only by the weight they have earned on this chart (Bias Features)."

**A/B.** Toggle `drawSrc` on the same chart and compare DOL HIT %, EDGE, the side ledger skill, and the number of target-side switches and `drawFlip` events.

**Evidence:** strong (side accuracy) / moderate (effect on DOL HIT %, from proxies).

**Risk.**
- **Targets nearer on average.** The minDist floor, the proximity taper and minScore limit trivial picks.
- **Look change:** "Structure Vote" is one click away.
- **Interplay with `ctrMult` 0.50:** under Calibrated it fires only when the other side is at least 60% likely. Sibling REG-4's 0.85 is still worth A/B testing.

**Effort:** S (after BIAS-1).

### BIAS-8 (P1, S) · Zero-drift, horizon-conditioned races everywhere sides are compared [NEW-B]

**Why.**
- B2: adding the engine's drift (`potMu` = 0.5·SMA(Δclose, 50), 917) to the side race makes Brier **0.4-6.9% worse on all 7 datasets**.
- The conditional form `pW/(pW+pL)` beats the infinite race on 6 of 7 datasets (+1.0 to +3.0%; CI excludes 0 on 2).
- Siblings agree: QPOT-01 (PoT drift → 0) and REG-3 ("drift adds error in every regime").

**Change.**
- `f_invalidation` 1361: `float m = raceDrift ? potMu * tgt.side : 0.0`, with `bool raceDrift = input.bool(false, "Drift in Races", group = G_POT, tooltip = "Off by default: trend drift was tested and made first-touch odds worse on every market tested.")`.
- BIAS-1, BIAS-2 and BIAS-3 use `f_sideP` / `f_raceH` with μ = 0.
- `f_raceAdj` (1367-1371) keeps its ledger correction.

**Evidence:** moderate (B2, 7 datasets; siblings).

**Risk:** in persistent trends, drift could help on some charts. The ledger's race calibration (`f_raceAdj`) absorbs systematic bias.

**Effort:** S.

### BIAS-3 (P2, M) · Previous-candle module for HTF/STF/EXE: class, calibrated P(prior high first / prior low first / neither), CLV base rates [A, CORRECTED + NEW-B]

**Why.**
- Traders ask "is today a PDH day or a PDL day?" The geometry readout answers it, and so do the chart's own base rates.
- §2.10: after a close in the top 20% of the range, the prior high is exceeded next candle 75-89% of the time.
- The class labels (close-through / CRT / inside / outside) are what traders look for. They must come with their measured lift, which is usually about 0.
- B3 shows the raw readout is calibrated on weekly-from-daily periods but over-predicts "decided" on short intraday periods. So calibration is part of the spec.

**SERIES-STATE FUNCTION** (after `f_rangeTrack`, 833):
```pine
// Previous candle of a higher timeframe tracked on chart bars: its high / low / close, the candle before it,
// the running extremes and bar counts of the current candle, and the previous candle's class.
// cls: 1 close-through up · 2 sweep-reject up (bear CRT) · -1 close-through down · -2 sweep-reject down (bull CRT)
//      0 inside · 3 / -3 outside closing above / below the prior range · 4 outside closing inside
f_candleTrack(bool isNew) =>
    var float h0 = na
    var float l0 = na
    var float h1 = na
    var float l1 = na
    var float c1 = na
    var float h2 = na
    var float l2 = na
    var int   n0 = 0
    var int   n1 = 0
    if isNew
        h2 := h1
        l2 := l1
        h1 := h0
        l1 := l0
        c1 := close[1]
        n1 := n0
        h0 := high
        l0 := low
        n0 := 1
    else
        h0 := na(h0) ? high : math.max(h0, high)
        l0 := na(l0) ? low : math.min(l0, low)
        n0 += 1
    int cls = 0
    if not na(h2) and not na(c1)
        bool upO = h1 > h2 and l1 >= l2
        bool dnO = l1 < l2 and h1 <= h2
        bool out = h1 > h2 and l1 < l2
        cls := upO ? (c1 > h2 ? 1 : 2) : dnO ? (c1 < l2 ? -1 : -2) : out ? (c1 > h2 ? 3 : c1 < l2 ? -3 : 4) : 0
    [h1, l1, c1, h0, l0, n0, n1, cls]
```

**Calls** (global scope, after 946). Each call site keeps its own `var` state:
```pine
[pcH1a, pcL1a, pcC1a, pcH0a, pcL0a, pcN0a, pcN1a, pcClsA] = f_candleTrack(timeframe.change(tfH))
[pcH1b, pcL1b, pcC1b, pcH0b, pcL0b, pcN0b, pcN1b, pcClsB] = f_candleTrack(timeframe.change(tfS))
[pcH1c, pcL1c, pcC1c, pcH0c, pcL0c, pcN0c, pcN1c, pcClsC] = f_candleTrack(timeframe.change(tfE))
int pcRuleH = pcClsA == 1 or pcClsA == 3 or pcClsA == -2 ? 1 : pcClsA == -1 or pcClsA == -3 or pcClsA == 2 ? -1 : 0
int pcCrtH  = pcClsA == -2 ? 1 : pcClsA == 2 ? -1 : 0
```
- `tfH = "D"` uses the same exchange-day convention as PDH/PDL (945).
- On a chart whose timeframe equals `tfE`, the EXE row's "previous candle" is the previous bar, which is correct.

**Readout** (each confirmed `inCalc` bar, per timeframe k):
- `open_ = h0 <= h1 and l0 >= l1` (neither extreme taken yet).
- **[CORRECTED] Remaining bars** `hRem = math.max(1, n1 − n0)`, from the previous candle's bar count. This is robust to session gaps; A's wall-clock `time_close` estimate counted overnight hours on RTH symbols.
- `pw = f_raceH(h1 − close, close − l1, potSig, 0, hRem)` and `pl = f_raceH(close − l1, h1 − close, potSig, 0, hRem)`.
- `pDec = pw + pl` and `pHi = pDec > 1e-9 ? pw/pDec : 0.5`.
- **Calibrated P(decided).** For the elapsed third `e = math.min(2, int(3·n0/n1))`:
  - `pDecC = f_sigm(w0 + w1·f_logit(pDec))`;
  - weights live in `array<float> pcW` (3 TF × 3 thirds × 2, initialised to 0 and 1);
  - online logistic with shrinkage toward (0, 1), as in `f_sideBook`;
  - it is applied only behind the same ΔLL gate (≥ 50 booked periods per TF, design effect 1).
- **Shown:** P(prior high first) = pDecUse·pHi; P(prior low first) = pDecUse·(1 − pHi); P(neither) = 1 − pDecUse.
- **Which-first is not recalibrated.** B3b: calibrated at the open, 73-82% accuracy. Its observed rate per class is booked for the "class lift" line.

**Bookkeeping** (prequential, one record per TF per third):
- **Issue:** at the bars where `n0 == 1`, `round(n1/3)` and `round(2·n1/3)`, while `open_`, store (pDec, pHi, cls, e, and the bias for BIAS-5) in `array<float>` slots.
- **Resolve:** on the first bar where the high or low is taken:
  - high only → decided and high-first;
  - low only → decided and low-first;
  - both on one bar → ambiguous, drop;
  - at `isNew` → not decided.
- **Update:**
  - the P(decided) calibration and its ΔLL gate statistics;
  - which-first n / k / Σp per TF and per class, to give the class lift = k/n − Σp/n;
  - the BIAS-5 cells.

**[NEW-B] CLV base-rate table** (per TF, 5 CLV buckets × 4 counts in `array<int>`):
- On `isNew`, book the period that just ended into the bucket stored at its start:
  - `tookHi = pcH0a[1] > pcH1a[1]`;
  - `tookLo = pcL0a[1] < pcL1a[1]`;
  - counts n, kHi, kLo, kBoth.
- Then store the new bucket `q = math.min(4, int(5·(c1 − l1)/(h1 − l1)))`.
- History references on the tuple outputs are safe, because the calls run unconditionally at global scope.

**UX.**
- **Clean:** keep the two-column look. After the `f_cellC` at 2304, add `table.cell_set_tooltip(dash, 1, k + 1, tipK)` (reference/table.md 252-264), for example:
  `Prev D: swept high, closed back inside (CRT ▼) · closed at 23% of its range`
  `Today: PDH first 31% · PDL first 52% · neither 17% (at open 28% / 55% / 17%)`
  `After prev-D closes in this zone: PDH taken 41% · PDL 71% · both 18% (n 212)`
  `CRT ▼ days: low first 54% vs geometry 53% (lift +1%, n 64)`
- **Terminal:** a `PREV` row group: TF · class · H% · L% · 0%.
- **Optional, default off:** push the STF/EXE prior extremes into `extReg` as new src codes (tier between session and STF). This needs `f_tierW` and `f_levelName` entries.

**Evidence:** moderate (geometry and base rates, B3 calibration) / weak-to-none (class lift).

**Risk:**
- **Session conventions differ** (18:00 vs RTH vs midnight). The readout uses the exchange day like PDH/PDL; say so in the tooltip.
- **Small n per class** (about 1 per day on D). Shrinkage and the gate keep the numbers at geometry until data accrue.

**Cost:** 3 × 2 `f_raceH` per bar plus O(1) bookkeeping.

**Effort:** M.

### BIAS-4 (P2, S) · Raid outcome: implement `ict_liq.final.md` ICT-9; keep HOLD and REJECT as separate learned features [A, MERGED]

**Why.** At 1581 a REJECT pushes D toward reversal. The evidence against that reading:
- CRT target-first 39-48% = null;
- Turtle Soup ≤ geometry;
- swept equity highs are retaken more often than the null;
- AMD direction follows the regime;
- REJECT continues 52.6% (sibling);
- B2's learned REJECT weight ranges from −0.31 to +0.10.

**Change.**
- `liqEvt` per ICT-9: neutral REJECT, HTF-conditioned HOLD, one event per side per bar, micro-pokes ignored.
- The separate `liqHold` / `liqRej` accumulators of BIAS-1 feed the side model, so each sign is *measured* per chart.
- A's `rejW` input is not needed once ICT-9 is in.

**Evidence:** strong (REJECT ≠ reversal) / moderate (HOLD alignment).

**Effort:** S.

### BIAS-5 (P3, S) · Bias table with measured skill, in the tooltip by default [A, CORRECTED UX]

**Why.**
- Traders read BULLISH/BEARISH as a forecast. Its side skill is about 50% (§2.7).
- [CORRECTED] A dimmed the cells by default. That breaks the reference look, so the default is tooltip-only.

**Algorithm.**
- In BIAS-3's bookkeeping, also store each row's displayed bias b (swing, else internal) at the period open.
- On resolution with b ≠ 0, book n, k (bias side first) and Σp (the geometric P(bias side first) at the open).
- lift = k/n − Σp/n; se = √(Σp(1−p))/n.
- **Tooltip line:** `When D is BULLISH: prior high first 61% (geometry 58%, n 140) → lift +3% ± 4%`.
- **Optional input** `Bias Skill Shading` (default off): alpha 60 on the text when lift < 1.5·se.
- **Terminal:** a `SKILL` column with `+3% (n 140)`.

**Evidence:** strong (need) / weak (UX benefit).

**Effort:** S (after BIAS-3).

### BIAS-7 (P3, S) · HTF candle-close event alerts (CRT / close-through) with calibrated odds [A✓]

- On `timeframe.change(tfH)` or `timeframe.change(tfS)`, with cls ∈ {±1, ±2} from BIAS-3:
  `alert("DOL Engine ▸ " + f_tfLabel(tf) + " " + clsText + " · prior high first " + pct(pHiShown) + " · prior low first " + pct(pLoShown) + " · neither " + pct(pNone) + " · class lift " + f_signed(lift * 100, "0") + "% (n " + str.tostring(n) + ")", alert.freq_once_per_bar_close)`.
- Add `alertcondition(htfCandleEvt, "HTF Candle Event", ...)`.
- Input `Alert · HTF candle events`, default off; limited to tfH and tfS.

**Evidence:** weak (UX). **Risk:** users may read CRT as a signal; the message shows the lift. **Effort:** S.

### BIAS-6 (P3, M) · Empirical PoT surface regime key by held-out score → **merged into sibling REG-1** [A, MERGED]

- `f_bump` / `f_empPoT` split the reach surface by `htfBias`, which has no side skill.
- `f_empPoT` already pools when a row has fewer than `nMin` samples (1292-1299), but it never pools a full yet uninformative row.
- REG-1 replaces the key with a volatility state chosen by held-out score. Implement it there.
- The candidate keys here (pooled; previous-HTF class from BIAS-3) can be offered to REG-1's selector.

**Evidence:** weak-moderate. **Effort:** M (in REG-1).

### Explicitly not recommended (tested and rejected)

- **Fixed-weight bias rules in D:** the ICT daily-bias rule, CRT, open-relative bias, weekly profiles, the Taylor 3-day cycle, the value-area 80% rule, the EMA trend regime. All are ≤ geometry or change sign by market (§2.2-2.6, X22, X24). They enter only as gated learned features (BIAS-1).
- **An ungated learned D.** It is worse than geometry (B2) and worse than a coin without geometry (sibling ict_struct).
- **Drift in side races** (BIAS-8).
- **Crabel "contraction → expansion" as a volatility prior.** It is false in absolute terms (§2.11).
- **Raising `wDraw` or lowering `ctrMult` under the Structure Vote.** That would amplify an input with no skill.
- **Hit-rate displays without a baseline** (as in the open-source daily-bias tracker, X23). Every rate shown must sit next to its geometry expectation for the same cases.

---

## 5. Notes for implementers

1. **Order:** BIAS-8 (one line) → BIAS-1 in "Measure" mode (two-phase scoring + ledger) → BIAS-2 (default Calibrated) → BIAS-3 → BIAS-5 and BIAS-7. BIAS-4 lands with ICT-9.
2. **Compile checks (doc-grounded):**
   - UDT array fields (`type_system.md` 781).
   - `array.from` with floats.
   - Methods may call other globals declared before them.
   - `table.cell_set_tooltip` exists (`table.md` 252).
   - `timeframe.change(series string)`.
   - Functions must not reassign fundamental-type globals; this spec keeps all learner state in arrays and computes `sdApply` at the call site (`arrays.md` 263).
   - `dirSide` and `drawFlip` are reassigned with `:=` in nested blocks of the engine `if`, not inside a function.
3. **Data Window plots for testing:** P(buy-side first) %, side skill, and the gate state (0/1).
4. **Validation on charts:** NQ, ES, EURUSD, XAU and BTC at 15m and 1H. The expected result is side skill about 0 against geometry with the gate closed. DOL HIT % should rise under Calibrated; EDGE should be unchanged.

---

## 6. Sources

**This study.** All scripts are reproducible with `python3 -I`.
- **A** (`study/bias_tools/`):
  - `prevcandle.py` → `out_daily.txt`, `out_weekly.txt`, `out_intra.txt`;
  - `race.py` → `out_race.txt` (B re-ran it: identical, `bias_b_tools/out_race_rerun.txt`);
  - `cells.py`, `openrel.py`, `turtle.py`, `nr.py` and `sidesel.py`, each with its `out_*.txt`.
- **B** (`study/bias_b_tools/`):
  - `b1_fair_ict.py` → `out_b1.txt`;
  - `b2_sidemodel.py` → `out_b2.txt`;
  - `b2b_boot.py` → `out_b2b.txt`;
  - `b3_period.py` → `out_b3.txt`;
  - `b3b_calib.py` → `out_b3b.txt`.
- **Data:**
  - `arch` 9.0.0 datasets: S&P 500 and NASDAQ daily 1999-2018;
  - `backtesting` 0.6.6: GOOG daily 2004-13, EURUSD 1H 2017-18;
  - sibling NQ/GC/EURUSD 1H 2024-26 (`scratchpad/sim/data/`).

**Papers** (B✓ = B read the text or abstract in this session):
- Taylor, V. (2026). Evaluating the Predictive Validity of ICT's AMD Model on CME E-Mini NASDAQ-100 Futures. arXiv:2610.35887. Code: github.com/veertaylor19/amd-backtest. B✓ full text.
- Portnaya, V. (2026). The Bounce Has No Direction. arXiv:2606.29591. B✓ full text.
- Safari, S. A., & Schmidhuber, C. (2025). Trends and Reversion in Financial Markets on Time Scales from Minutes to Decades. arXiv:2501.16772. B✓ abstract.
- Mesfin, M. (2026). Structural Limits of OHLCV-Based Intraday Momentum Signals in MNQ Futures. arXiv:2605.04004. B✓ abstract.
- Upadhyay, R. (2026). Do Time-Series Foundation Models Forecast Index-Futures Returns? arXiv:2611.12141. B✓ full text.
- Kitron, N. A., & Wengrowicz, J. M. (2026). Short-horizon mean reversion in cryptocurrency markets. arXiv:2608.21888. B✓ abstract.
- Kurth, J. G., Eisler, Z., Rej, A., & Bouchaud, J.-P. (2026). Is Trend Still Your Friend? arXiv:2607.01550. B✓ abstract.
- Vidovich, A., & Zerjal, Z. (2026). The End-of-Day Reversal After 2019. arXiv:2611.09286. B✓ abstract.
- Christensen, K., Oomen, R. C. A., & Renò, R. The drift burst hypothesis. arXiv:2601.08974 listing. B✓ abstract.
- Gao, L., Han, Y., Li, S. Z., & Zhou, G. (2018). Market intraday momentum. *Journal of Financial Economics* 129(2), 394-414. Via web-search summaries (R² 1.6%).
- Osler, C. L. (2005). Stop-loss orders and price cascades in currency markets. *JIMF* 24(2). NY Fed Staff Report 150 via web search; numbers from sibling `academic_sr.md` S6.
- Moskowitz, T., Ooi, Y. H., & Pedersen, L. H. (2012). Time series momentum. *JFE* 104(2), 228-250.
- López de Prado, M. (2018). *Advances in Financial Machine Learning*, ch. 3 (triple barrier, meta-labeling). Wiley.
- Joubert, J. F. (2022). Meta-Labeling: Theory and Framework. *Journal of Financial Data Science* 4(3).
- Cesa-Bianchi, N., & Lugosi, G. (2006). *Prediction, Learning, and Games*. Cambridge University Press (expert mixtures).
- Graepel, T., et al. (2010). Web-scale Bayesian click-through rate prediction (adPredictor). ICML (via sibling `calib_ml.md`).
- Mahadzva (2026) SSRN 7430998; Chung & Bellotti (2021) arXiv:2101.07410. Via sibling studies [A, not re-fetched].

**Books and practitioners:**
- Raschke, L. B., & Connors, L. (1995). *Street Smarts* (Turtle Soup, 80-20s, Taylor quote). Summary: technical.traders.com (Traders' Technical Analysis) [not re-fetched].
- Taylor, G. D. (1950). *The Taylor Trading Technique* (3-day cycle). Vendor stats: NexusFi and PTG webinar transcripts [none].
- Crabel, T. (1990). *Day Trading with Short Term Price Patterns and Opening Range Breakout* (NR4/NR7). StockCharts ChartSchool NR7 page.
- Williams, L. (Oops, smash day). RogueQuant substack: roguequant.substack.com/p/i-backtested-larry-williams-trading [blocked; search summary only].
- **edgeful** (blocked; web-search summaries only):
  - edgeful.com/blog/posts/previous-days-range-trading-mistake
  - …/inside-bar-pattern-day-trading-strategy
  - …/trading-bullish-bearish-outside-days
  - …/ultimate-bullish-setup-trading-NQ
- **CRT definitions:**
  - luxalgo.com/library/concept/candle-range-theory/
  - tradingwyckoff.com/en/crt/
  - eltraderfinanciado.com/ar/blog/crt-trading
- TTrades: ttrades.com/easy-daily-bias-a-mechanical-trading-framework/ [A, not re-fetched].
- NexusFi PDH/PDL count (NQ 2015, 168/186); attribution per search summary.
- Bulkowski: thepatternsite.com (hikkake, outside days).

**Open-source implementations** (read only, cloned to `study/bias_b_ext/`):
- GitHub `d-leeee/ICT-Daily-Bias-First-Presented-Indicator`: Pine v6 daily-bias vote with a self-tracked hit rate.
- GitHub `YannVladimir/fx-structural-momentum-bot`: EURUSD pre-declared breakout / failed-breakout / CRT structural studies.
- GitHub `CodeAlamin2024/DataScience-Project`: CRT manual backtest, n = 100.
- GitHub `issbguru-png/ict-daily-bias`: Python ICT bias engine (structure-shift scoring).

**Sibling studies** (`brief/study/`):
- `ict_struct.final.md` (D nulls, ICTS-1/3/4);
- `ict_liq.final.md` (ICT-9);
- `academic_sr.md` (Osler S1-S6);
- `amt_profile.md` (80% rule);
- `quant_regime.md` (REG-1/3/4/6);
- `quant_pot.md` (QPOT-01/06);
- `calib_ml.md` (CAL-4 gate, SGD failure);
- `skeptic.md` (SKEP-6);
- `ict_time.final.md` (TIME-1/2, weekly profiles, volatility clock).

**Pine docs** (local mirror `docsrc/jabez4jc_pinescriptv6/`):
- `language/type_system.md` 781 (collection-typed fields);
- `language/arrays.md` 263 (globals in local scopes);
- `reference/table.md` (`table.cell` `tooltip`, `table.cell_set_tooltip` 252);
- `reference/timeframe.md` 109 (`timeframe.change`);
- `reference/time.md` 378 (`time_close`).
