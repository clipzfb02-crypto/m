# x1_positioning · Derivatives positioning and crowding

Lens scope: dealer gamma (GEX, zero-gamma / flip, call and put walls), vanna and charm flows, 0DTE, max pain, futures open interest, crypto perpetuals (OI, funding, premium, long/short ratio), CFTC Commitments of Traders, short interest. The crowded-side hypothesis, OI flushes at sweeps, and how to ingest external positioning levels that Pine cannot compute.

Already covered elsewhere, not redone here:
- strike pinning on expiry (`classic_levels` P15, `asset_specific` H3);
- crypto liquidation heatmaps (`orderflow_micro` B9, a null result);
- round numbers (`classic_levels` 1.6: they act as barriers, not magnets).

The engine's question: **which liquidity is reached next, when, and how likely within H bars.** The question for this lens: does positioning data change that answer beyond what distance, volatility and structure already give?

---

## 0. Headline findings

1. **Dealer gamma is a volatility-state variable, not a direction or target variable.**
   - Own test, SPX daily 2011-2026 (n = 2,665 days): yesterday's SqueezeMetrics GEX rank predicts today's range in ATR units.
     - Q1 (low gamma) to Q5: range/ATR20 falls from **1.154 to 0.803**.
     - The effect is incremental to the VIX-implied daily σ: OLS t = **-10.8**, R² 0.192 → 0.231.
   - Pine-computable proxies (the VIX/VIX3M term structure plus the VIX-implied σ in ATR units) recover about 75% of that gain (R² 0.194 → 0.230). Pasted GEX adds only +0.0115 more (t = -5.8).
   - Gamma changes the **upside** reach only. P(PDH traded) at a fixed ATR distance falls with GEX rank (t = -6.3). P(PDL) does not move (t = -0.7).
   - In the low-gamma regime, PDH breaks hold more often: 36.5% close back inside, against 44.9% when gamma is high. PDL shows no difference.
2. **The literature agrees on volatility.**
   - Ni, Pearson, Poteshman & White (RFS 2021): negative market-maker gamma raises absolute returns and the chance of large moves.
   - Barbon & Buraschi: negative gamma imbalance goes with intraday momentum and positive imbalance with reversal, strongest in illiquid names.
   - Baltussen et al. (JFE 2021): intraday momentum in the last 30 minutes, tied to short-gamma hedging.
   - **0DTE evidence points to damping, not amplification:**
     - Dim, Eraker & Vilkov: high 0DTE open-interest gamma does not propagate volatility.
     - Adams, Fontaine & Ornthanalai: dealers are net long gamma on 0DTE days, which lowers volatility for about 10-60 minutes.
     - Cboe: market-maker hedging is at most about 0.2% of SPX liquidity.
     - The dissenter is Brogaard, Han & Won: +1 sd of 0DTE volume ≈ +14% daily volatility.
3. **Max pain is folklore for index charts.**
   - SPX 2004-2026: 46.9% of closes land within 1% of the price 4 trading days earlier, and 74.8% within 1% of the prior close, with no options data at all.
   - So a vendor's "48% of SPX expiries closed within 1% of max pain" is no better than no information.
   - The only supportive study, Filippou, Garcia-Ares & Zapatero (2022), is a cross-sectional reversal of about 0.4% in single-stock expiration weeks, concentrated in small, illiquid names.
4. **"Window of weakness" and vanna/charm OPEX-week flows are folklore.**
   - SPX 1999-2026 weekly: no stable pattern in return, range or P(PWH first) for the OPEX week or the week after, in either sub-period.
   - Only weak effect: **monthly-OPEX Fridays have a 6-8% smaller range** than other Fridays (t = -1.6 and -1.4 in two separate periods). The Monday after shows no effect.
5. **The crowded-side hypothesis is partly supported for crypto funding only. COT is null.**
   - Real Binance funding data, BTC 1h 2019-09 to 2025-01 (7,444 decided races):
     - Negative funding (shorts crowded): BSL is run first **+5.2 ± 2.1 pp** above calibrated geometry (sweep bars: +5.9 ± 3.0). The sign holds in both halves.
     - Crowded longs show a weaker mirror effect (-1.9 to -4.8 pp, not significant on their own).
     - Jointly with 72-hour momentum, the funding rank is contrarian (-6 pp from bottom to top, t = -2.2). Momentum continues (t = +4.3).
     - After an SSL sweep with crowded longs (funding rank ≥ 70%), the move continues to the next SSL **+6.1 ± 2.5 pp** more often. With funding rank < 30%, it reverses more often (-5.2 ± 2.5). The signs hold in both halves.
     - In short: crowded longs whose stops get hit cascade, while uncrowded SSL sweeps are raids.
   - COT, E-mini S&P 2008-2026 (723 weeks): neither the speculator nor the hedger COT index predicts which side of the prior week's range is taken first (slopes -0.017, t = -0.3, and +0.073, t = 1.4, non-monotonic).
6. **An OI flush does not mark a pool as spent.**
   - BTC 2026, 217 sweeps with real Binance OI: after an OI flush, 54% close back inside, against 62% for flat OI. After an OI build, 51%. Breakout-first rates are 0.44, 0.44 and 0.58.
   - If anything, an OI *build* on the sweep bar leans toward breakout (n = 47, about +14 pp, t ≈ 1.6). The sample is underpowered and this is not a usable signal.
7. **TradingView exposes enough to test all of this per chart:**
   - futures OI as `<symbol>_OI` (end of day only for CME);
   - crypto OI intraday as `BINANCE:BTCUSDT.P_OI`;
   - the perp premium index as `BINANCE:BTCUSDT_PREMIUM`;
   - long/short ratio as `_LSR` (community scripts);
   - COT through the official `LibraryCOT` ticker scheme `COT{,2,3}:<code>_<F|FO>_<metric>`;
   - FINRA short *volume* (not short interest).

   Options open interest by strike is **not** available, so GEX levels, walls and max pain can only come in as pasted text.
8. **Recommended path.** Gate everything through the per-chart candidate (shadow) ledger (`calib_ml` CAL-3), in four pieces:
   - (a) a gamma-regime volatility state for PoT on index charts, using the Pine proxies with an optional pasted GEX token;
   - (b) a date-stamped, auto-expiring pasted-levels box that forms a shadow-graded "OPT" family;
   - (c) a funding state for crypto perps;
   - (d) positioning covariates logged on every probe.

   Never let max pain, COT or long/short ratio into scoring by default.

---

## 1. Concepts (definitions and parameters)

Notation:
- Γ = Black-Scholes gamma = φ(d1) / (S·σ·√T);
- vanna = ∂Δ/∂σ = -φ(d1)·d2/σ;
- charm = -∂Δ/∂t;
- OI_i = open interest of contract i;
- M = contract multiplier (100 for SPX/SPY options);
- S = spot.

### 1.1 Dealer gamma exposure (GEX)
- **Classic / "naive" GEX** (SqueezeMetrics white paper, Dec 2017; reproduced by every vendor):
  - per contract: `GEX_i = sign_i · Γ_i · OI_i · M · S² · 0.01`;
  - `sign = +1` for calls and `-1` for puts. This assumes dealers are long calls (customers overwrite) and short puts (customers buy protection).
  - Total GEX is the sum over all strikes and expiries. It is the dollar amount of underlying dealers must trade per 1% move.
    - Positive GEX: dealers sell rallies and buy dips. Mean-reversion and damping.
    - Negative GEX: dealers sell dips and buy rallies. Momentum and amplification.
- **Flow-signed GEX** (vendor v2 methods; Ni et al. 2021 with Cboe Open/Close data; Glassnode taker-flow GEX for Deribit):
  - The dealer side is inferred from trade aggressor or open/close flags, not assumed.
  - The sign assumption is the weakest link of classic GEX: OI does not say who is long.
- **Normalisation.** Raw GEX trends with market size. Use a trailing rank, or GEX divided by its trailing mean |GEX|. Our tests use a trailing 252-day rank, available at t-1.
- **Data timing.** SqueezeMetrics publishes after the close. Every use must be GEX[t-1] for session t, which is non-repainting.
- **Failure modes:**
  - the sign assumption fails in squeeze regimes (customers long calls, as in 2020-21);
  - 0DTE flow is not in end-of-day OI;
  - gamma decays to zero at expiry (GEX drops 5.5% on average on the first session after monthly OPEX, own data);
  - GEX is strongly tied to VIX (corr of rank -0.65) and to trend (corr with the 20-day return 0.56).

### 1.2 Zero-gamma ("gamma flip", HVL, Volatility Trigger)
- **Definition.** Recompute total GEX on a grid of hypothetical spots S' (usually ±10% in 0.1-0.5% steps), holding IV at sticky-strike or sticky-moneyness. Zero gamma is the S' where the total crosses zero, interpolated linearly between grid points.
- **Vendor variants:**
  - "HVL" (high-volatility level) is the same idea;
  - SpotGamma's "Volatility Trigger" is proprietary. SpotGamma pages describe it both as equal to zero gamma and as a level a few points above it;
  - "Hedge Wall" is described only qualitatively.
- **Practitioner use:**
  - above the flip, sell rallies at walls and expect ranges;
  - below the flip, expect trend days and the PDL / put wall as the draw;
  - a cross of the flip changes the regime.
- **Evidence:** none for the level itself as a target or barrier. The regime evidence is in §2.1. A wrong IV or sign assumption moves the flip by tens of SPX points.

### 1.3 Call wall, put wall, absolute-gamma strike, OI walls
- **Call wall:**
  - the strike with the largest call gamma, or in some vendors the largest net call gamma or largest call OI, aggregated over all expiries or the front expiry;
  - used as intraday resistance and the upper bound of the expected range.
- **Put wall:** the strike with the largest put gamma or put OI. Used as support and the lower bound.
- **Absolute-gamma strike:** the maximum of |Γ_call| + |Γ_put| over strikes, a "magnet" in positive gamma.
- **OI walls:** the largest OI strikes, a cruder version.
- **Failure modes:**
  - walls migrate daily as OI rolls;
  - front-expiry walls vanish at expiry;
  - SPX walls must be mapped to ES (basis) or SPY (×1/10, dividends);
  - the claims are untested in peer-reviewed work;
  - historical pinning at high-OI strikes (Ni, Pearson & Poteshman 2005; Golez & Jackwerth 2012) faded after 2016 (Elms 2026, via `classic_levels` P15).
- **Engine relevance:** these levels cannot be computed in Pine, because there is no options OI by strike. The only route is pasted levels (§5, X1P-2).

### 1.4 Vanna and charm flows
- **Dealer vanna exposure:** `VEX = Σ sign_i · vanna_i · OI_i · M · S · Δσ`, usually per 1 vol point.
  - The story: if IV falls (for example after an event), dealers short puts see put deltas shrink and buy back short hedges. That is a "vanna rally".
  - SqueezeMetrics' companion analysis assumes "1% spot ⇒ -10% IV".
- **Dealer charm exposure:** `CEX = Σ sign_i · charm_i · OI_i · M · S` per day.
  - Into monthly OPEX, OTM put deltas decay and dealers unwind short hedges ("supportive into OPEX").
  - Folklore corollary, the "window of weakness": the one to two weeks after monthly OPEX are when these supportive flows are absent.
- **Evidence (§2.3):**
  - Stivers & Sun (JBF 2013): higher returns in option-expiration weeks for S&P 100 stocks, attributed partly to short-hedge reduction.
  - Own SPX test (1999-2026): no stable index effect.
  - "Window of weakness": no systematic backtest exists, and ours is null.

### 1.5 0DTE options
- These are options expiring the same session. They were **59% of SPX volume in 2025** (Cboe, 2.3 M contracts/day), with retail about half.
- Their gamma is huge per contract near the money, but customer flow is roughly balanced. The evidence (§2.2) says net dealer 0DTE gamma is small and usually long, so 0DTE damps rather than amplifies.
- End-of-day GEX misses 0DTE entirely, because it opens and closes the same day.

### 1.6 Max pain
- **Definition:** for an expiry with strikes K_j,

  `MP = argmin_X Σ_j [ OI_call(K_j) · max(0, X - K_j) + OI_put(K_j) · max(0, K_j - X) ]`

  This is the settlement price that minimises the total intrinsic value paid to option holders.
- **Folklore:** price "gravitates" to MP into expiry because "market makers" push it there.
- **Mechanical bias:** OI concentrates near the money when it is created, so MP is usually within a few percent of spot when computed. Any hit rate must be compared with "spot at computation time" (§2.3).

### 1.7 Futures open interest
- **Definition:** the number of open contracts. A volume print opens or closes positions.
- **Practitioner quadrant (folklore):**
  - price ↑ OI ↑ = new longs (strong);
  - price ↑ OI ↓ = short covering (weak);
  - price ↓ OI ↑ = new shorts;
  - price ↓ OI ↓ = long liquidation.
- **CME:** OI is end-of-day. Preliminary OI for day t is published the next morning. TradingView serves it as a daily series `<EXCHANGE>:<SYMBOL>_OI`, such as `CME_MINI:ES1!_OI`. The built-in Open Interest indicator requests "1D" on intraday futures charts.
- **Non-repainting use:**
  - on intraday charts: `request.security(t + "_OI", "1D", close[1], lookahead_on)`;
  - for strict publication safety, use `close[2]`, because day t-1's OI may not be public at t's open.

### 1.8 Crypto perpetuals: OI, funding, premium, long/short ratio
- **OI:** intraday OHLC of open interest, for example `BINANCE:BTCUSDT.P_OI`, `BINANCE:BTCUSD.P_OI`, `BITMEX:XBTUSD.P_OI`, `BYBIT:…_OI`, `OKX:…_OI`. The patterns come from TradingView's own built-in OI script logic and community aggregators.
  - Some venues misquote OI (Giagkiozis & Said 2023).
  - In crashes OI clears 25-70% (Garcia Seuma 2026).
- **Funding (Binance-style):**
  - `F = P̄ + clamp(I - P̄, -0.05%, +0.05%)` per 8 hours;
  - I = interest component, 0.01% per 8h;
  - P̄ = time-weighted premium index over the interval;
  - settlement at 00/08/16 UTC, with faster intervals when capped.
  - Consequences: F < 0 iff P̄ < -0.05%; F = 0.01% (the "base rate") whenever |0.01% - P̄| ≤ 0.05%; F > 0.01% iff P̄ > 0.06%.
- **Premium index:** `(max(0, impact bid - index) - max(0, index - impact ask)) / index`. TradingView symbol `BINANCE:<PAIR>_PREMIUM`; the units must be checked on the platform.
- **Basis / premium:** perp minus spot. He, Manela, Ross & von Wachter (arXiv 2212.06888) report that past return momentum explains more than 50% of the time-series variation of the premium. So "funding extreme" ≈ "trailing return extreme", and any test must control for momentum (ours does).
- **Long/short ratio:** accounts or positions net long divided by net short (Binance top-trader or global ratio). TradingView `_LSR` suffix (community scripts). No published predictive evidence.

### 1.9 CFTC Commitments of Traders
- **Report:** Tuesday positions, released Friday 15:30 ET.
  - Legacy groups: commercial, noncommercial, nonreportable.
  - Disaggregated (commodities): producer/merchant, swap, managed money, other.
  - Traders in Financial Futures (TFF): dealer, asset manager, leveraged funds, other.
- **COT index (Williams):** `(net - min_N) / (max_N - min_N)` with N = 156 weeks (3 years) of net or net/OI. Extremes are < 10% or > 90%.
- **TradingView:** the official `LibraryCOT` builds tickers as `"COT{type}:{CFTCcode}_{F|FO}_{metric}{_L|_S|_SPREAD}{|_OLD|_OTHER}"`.
  - type "" = Legacy, "2" = Disaggregated, "3" = Financial;
  - metric codes include `OI`, `NCP` (noncommercial positions), `CP`, `LMP` (leveraged funds), `AMP`, `DP`, `MMP`;
  - CFTC codes: ES 13874A, NQ 209742, YM 124603, RTY 239742, GC 088691, CL 067651, 6E 099741, CME BTC 133741.
  - Requested with `request.security(t, "1D", close, ignore_invalid_symbol = true)`. Each call counts toward the 40-request limit.

### 1.10 Short interest
- Short interest is shares sold short and not covered. It is reported twice monthly (FINRA).
- Short ratio = SI / shares. Days to cover = SI / average daily volume (Hong et al. 2016).
- TradingView exposes only **FINRA short-sale volume** (`FINRA:<SYM>_SHORT_VOLUME`, end of day). That is daily short-sale *activity*, dominated by market-maker shorting, not outstanding short interest.

### 1.11 The crowded-side hypothesis (operational form)
- **State:** a positioning extreme at bar t, using only information available at t:
  - funding rank ≥ 90% = longs crowded;
  - rank ≤ 10% or funding < 0 = shorts crowded;
  - a COT index extreme;
  - an OI build with trend.
- **Claim A (side):** the crowded side's stops are run first. Crowded longs mean SSL is reached before BSL more often than geometry predicts.
- **Claim B (sweep reading):** when the crowded side's pool is swept, the move cascades (continuation). When the uncrowded side's pool is swept, it is a raid (reversal).
- **Claim C (OI flush):** an OI drop on the sweep bar means the pool's stops were consumed, so the pool is spent and price reverses. An OI rise means new positions entered the break, so it is a breakout.
- **Test protocol (used throughout):**
  - race the nearest unswept pivot-high pool (BSL) and pivot-low pool (SSL), each within [0.5, 8] ATR, over 30 bars;
  - baseline: driftless gambler's-ruin geometry `dD / (dU + dD)`, recalibrated by logistic regression;
  - report residuals with cluster-robust SEs over 2H-bar blocks.

### 1.12 External positioning levels (ingestion concept)
These are levels a third party computes from options OI or flow: call wall, put wall, zero gamma, absolute-gamma strike, OI wall, max pain, and also the "regime" (GEX sign). The trader pastes them daily. They are date-stamped and valid only from their stamp, and they expire automatically. They form an optional level family that the per-chart shadow ledger grades before it may influence scoring (§5, X1P-2).

---

## 2. Evidence

### 2.1 Dealer gamma and volatility, momentum or reversal (literature)

| Study | Data | Finding (numbers) | Grade |
|---|---|---|---|
| Ni, Pearson, Poteshman & White, RFS 34(4) 2021, "Does option trading have a pervasive impact on underlying stock prices?" | US stocks; daily net gamma of likely delta-hedgers from Cboe/ISE open-close data | Highly significant negative relation between net delta-hedger gamma and volatility, which they call a "noninformational channel". Draft versions: the low-MM-gamma group's daily absolute return is about **100 bp above** the high-gamma group's (other summaries: 37-50 bp per shock; published magnitudes not verified) | strong (direction); magnitude moderate |
| Barbon & Buraschi, "Gamma Fragility" (WP 2020/21) | US stocks and indices, intraday | Negative aggregate gamma imbalance × illiquidity → intraday **momentum**; positive → **reversal**. Linked to flash-crash frequency and size. Strongest in the least liquid names. Companion (Barbon, Beckmeyer, Buraschi & Moerke 2021): end-of-day momentum from LETF / option imbalance, reverting at the next open | moderate (working paper; magnitudes not retrieved) |
| Baltussen, Da, Lammers & Martens, JFE 142(1) 2021 | 60+ futures, 1974-2020 | Last-30-minute return predicted by the rest-of-day return in every asset class; reverts over the following days. Attributed to short-gamma hedging (options MMs, LETFs). Secondary summary (Alpha Architect, their Table 7): **much stronger on negative-gamma days, insignificant on positive-gamma days** | strong (momentum); moderate (gamma link) |
| Vidovich & Zerjal, arXiv 2611.09286 (2026, pre-registered) | S&P 500 stocks | The stock-level end-of-day *reversal* holds at 3.05 bp/day (t = 3.0) in 2023-26, but is about 0 in 2020-22 and weak in the largest names | moderate |
| SqueezeMetrics GEX white paper (2017) | SPX | High GEX goes with low subsequent variance (paper's summary). Classic sign assumption | weak (vendor) |
| **Own test X1P-T1** (§2.6) | SPX daily 2011-2026 + SqueezeMetrics GEX | Range/ATR Q1 → Q5: 1.154 → 0.803. Incremental to VIX-implied σ: t = -10.8 | moderate (one index, 15 years, vendor-computed GEX) |

### 2.2 0DTE

| Study | Finding | Grade |
|---|---|---|
| Dim, Eraker & Vilkov (SSRN 4692190, 2023-24) | "High open interest gamma in 0DTEs does not propagate past volatility". 0DTE volume shocks do not amplify past returns. A higher 0DTE gamma goes with **lower** intraday volatility, and the effect is small and short-lived | moderate |
| Adams, Fontaine & Ornthanalai (2024-25) | Dealers keep a **positive** net gamma through 0DTE days. Higher net gamma → lower SPX volatility over the next **10 minutes**, fading after about 1 hour. Robust negative relation between 0DTE days and realised volatility | moderate |
| Brogaard, Han & Won (2023) | +1 sd 0DTE volume → about **+14%** daily SPX volatility (5-minute data, 10 years) | moderate (contested) |
| Cboe (2023-25) | MM 0DTE hedging is "de minimis", at best about 0.2% of SPX daily liquidity (`classic_levels`: 0.04-0.17%). 0DTE share: **59% of SPX volume in 2025**, record 62.4% in August 2025 | moderate (exchange analysis) |
| Princeton thesis (2026, via `classic_levels`) | Does not support the gamma-feedback channel | weak |

The net effect on the engine: 0DTE does not justify a gamma-amplification term. If anything it supports damping near large same-day OI, which Pine cannot see.

### 2.3 Max pain, OPEX, vanna and charm

| Item | Evidence | Grade |
|---|---|---|
| Max pain, single stocks | Filippou, Garcia-Ares & Zapatero (SSRN 4140487, 2022), "No Max Pain, No Max Gain": US stocks 1996-2021. Stocks with max pain above price rise about **0.4%** in expiration week (long-short weekly). Stronger in small, illiquid names, weaker in large caps and indices (from summaries) | moderate (cross-sectional, single stocks) |
| Max pain, index | Vendor and blog tests: "48% of 100 SPX expiries closed within ±1% of max pain" (no baseline); 60-close placebo test, 20 vs 22, i.e. none. **Own hurdle (X1P-T6):** with no options data, 74.8% of SPX closes are within 1% of the prior close, 61.2% of the close 2 days earlier and 46.9% of the close 4 days earlier (2004-2026; OPEX Fridays 75.6 / 61.8 / 43.3%). The 48% claim is at or below the no-information baseline | **none → folklore** |
| Pinning at strikes | Ni, Pearson & Poteshman (JFE 2005); Golez & Jackwerth (JFE 2012): at least $115 m per expiry 1992-2009; absent 2016-2025 (Elms 2026) | strong historically; decayed (see `classic_levels` P15) |
| OPEX-week returns (stocks) | Stivers & Sun (JBF 37(11) 2013): S&P 100 stocks earn higher OE-week returns, and the fourth-Friday week underperforms modestly. CXO: 0.83% vs 0.14% for high vs low option/stock volume weeks, 1996-2008 | moderate (stocks) |
| "Window of weakness" (index) | Practitioner newsletters only; no systematic backtest. **Own X1P-T6:** no stable effect (below) | **none → folklore** |
| OPEX Friday range | **Own:** SPX OPEX Friday range / 20-day mean is 0.940 vs 1.006 for other Fridays (2004-18, t = -1.6) and 0.995 vs 1.085 (2019-26, t = -1.4). The Monday after shows no difference (0.974 vs 0.974; 0.974 vs 0.957) | weak (consistent sign, two periods) |

### 2.4 Futures OI, COT and hedging pressure

| Study | Finding | Grade |
|---|---|---|
| Bessembinder, RFS 5(4) 1992 | Returns in currency and agricultural futures vary with hedgers' net positions after controlling for systematic risk. A **risk-premium** effect at monthly horizons | strong (premia); n/a intraday |
| de Roon, Nijman & Veld, JF 55(3) 2000 | 20 futures markets: own and cross hedging pressure significantly affect futures returns, robust to price pressure | strong (premia); n/a intraday |
| Kang, Rouwenhorst & Tang, JF 75(1) 2020 | Two premia of opposite sign: hedgers pay speculators for insurance (slow), and speculators pay for short-term liquidity (fast). Speculators' position *changes* lose in the short term | strong; n/a intraday |
| Wang, AFE 13(12) 2003 (S&P 500 futures) | Large-speculator sentiment = **continuation**, large-hedger sentiment = **contrarian**. Extremes are more reliable. Small traders have no power | moderate |
| Sanders, Irwin & Merrin, JARE 2009 | Granger tests: "very little evidence" that COT positions lead returns in 10 agricultural markets | moderate (null) |
| Hong & Yogo, JFE 105(3) 2012 | Commodity OI growth predicts commodity returns, bond returns and short rates. Weaker for stocks and FX. Monthly | strong; n/a intraday |
| **Own X1P-T5** (§2.6) | COT extremes do not predict which side of the prior week's range ES/SPX takes first, 2008-2026 | null (moderate power) |

### 2.5 Crypto perpetuals

| Study | Finding | Grade |
|---|---|---|
| He, Manela, Ross & von Wachter, arXiv 2212.06888 | Momentum explains more than 50% of the premium (funding) variation. Arbitrage deviations comove and shrink over time | strong (mechanism) |
| Memon, Anklesaria-Dalal & Mishra (Aug 2026, abstract via search) | Binance, funding ranked against the prior 180 days. **Extreme negative funding → +0.506% average 24h BTC return**, robust to FDR. Positive extremes show no comparable effect. Asymmetric and nonlinear | moderate (one paper; full text not read) |
| Cheng, Deng, Wang & Yu, arXiv 2102.04591 | BitMEX: daily forced liquidations are 3.51% (long) / 1.89% (short) of OI; liquidated traders average **60×** leverage | strong (descriptive) |
| Garcia Seuma, arXiv 2608.03616 | 7 cascades 2022-25: 88% of forced selling within 30 minutes, OI clears 25-70%, abrupt not critical. No scalar pre-state measure grades severity | moderate |
| Giagkiozis & Said, arXiv 2310.14973 | Several large exchanges systematically misquote BTC perp OI | moderate |
| Medium analysis ("funding rates and price predictability") | R² = 0.003 for funding → 8h return, slight negative slope | weak |
| Long/short ratio | No published validation found | none |
| **Own X1P-T3, T4** (§2.6) | Funding: moderate-weak support for claims A and B. OI flush (claim C): null | see below |

### 2.6 Own tests (scripts in `study/x1_pos_tools/`, data in `study/x1_pos_data/`)

#### X1P-T1 · GEX and next-day liquidity outcomes, SPX daily (`t1_gex_daily.py`)
- **Data:** SqueezeMetrics DIX/GEX daily, mirrored on GitHub (2011-05 to 2026-11); S&P 500 daily OHLC merged from three files; VIX and VIX3M from Cboe.
- **Predictors at t-1:** GEX trailing 252-day rank, VIX, ATR20.
- **Sample:** days opening inside the prior day's range (n = 2,665, 2011-11-29 to 2026-09-23). GEX < 0 on 8.8% of days.

| GEX quintile | VIX | range / ATR20 | P(PDH) | P(PDL) | P(both) | mean \|ret\| |
|---|---|---|---|---|---|---|
| Q1 (low) | 23.2 | 1.154 | 0.448 | 0.493 | 0.078 | 1.09% |
| Q2 | 18.4 | 0.995 | 0.519 | 0.403 | 0.080 | 0.74% |
| Q3 | 17.1 | 0.945 | 0.492 | 0.445 | 0.092 | 0.63% |
| Q4 | 16.1 | 0.886 | 0.484 | 0.447 | 0.106 | 0.54% |
| Q5 (high) | 14.9 | 0.803 | 0.558 | 0.386 | 0.098 | 0.39% |
| GEX < 0 | 28.1 | 1.157 | 0.419 | 0.521 | 0.077 | |

**Incremental tests (OLS, SE clustered by month; all include the PDH and PDL distances in ATR).**
- `ivA = VIX/100/√252 · close / ATR20` is the implied daily σ in ATR units, computable in Pine.
- Range/ATR:
  - distance only: R² 0.129;
  - + ivA: 0.192 (ivA t = 9.8);
  - + GEX rank: 0.231 (GEX rank **-0.352, t = -10.8**);
  - + GEX < 0 dummy instead of rank: 0.203 (+0.190, t = 5.8).
- P(PDH traded): R² 0.2197 (+ivA) → **0.2317** (+GEX rank -0.199, t = -6.3).
- P(PDL traded): unchanged at 0.196 (GEX rank t = -0.7).
- Pine-computable proxies, all at t-1: drawdown from the 252-day high, 20-day return, and **VIX/VIX3M**.
  - Correlations with GEX rank: drawdown 0.40, 20-day return 0.56, VIX/VIX3M -0.60.
  - Range R²: ivA alone 0.194; + proxies 0.230 (VIX/VIX3M t = 5.3); + GEX rank 0.2415 (GEX t = -5.8).
  - For P(PDH): 0.222 → 0.232 → 0.237.
  - **About 75% of the GEX increment is available in Pine.**
- Raid vs breakout (share of PDH or PDL sweeps that close back inside):

  | Swept level | Low GEX (rank < 0.3) | Mid | High (≥ 0.7) | GEX < 0 |
  |---|---|---|---|---|
  | PDH | **0.365 ± 0.027** | 0.444 | **0.449 ± 0.023** | 0.378 |
  | PDL | 0.482 | 0.462 | 0.509 | 0.459 |

- Next-day return autocorrelation: low gamma **-0.213 ± 0.085 (t = -2.5)**, mid -0.004, high +0.041. Momentum within the day (literature) and reversal the next day.
- Split halves, low-GEX minus high-GEX range within VIX terciles:
  - 2011-18: +0.21 / +0.13 / +0.28 ATR;
  - 2019-26: +0.03 / +0.24 / +0.17 ATR.
  - The range effect is stable. P(both) is not.
- **Reading:** GEX is a volatility and upside-reach state. It does not predict the side or P(both), except through regime drift: Q5 shows PDH-only 0.46 vs PDL-only 0.29, the calm-uptrend regime.

#### X1P-T2 · Intraday check on ES 1h (`t2_gex_intraday.py`)
- 179 sessions, 2025-04 to 2026-04.
- Last-hour vs rest-of-day slope: -0.7 bp per sd (low GEX) and -1.0 bp (high GEX), both t < 0.5. **No intraday momentum in 2025-26 in either regime.**
- RTH range relative to its 20-day mean: 1.148 (low GEX) vs 0.924 (high GEX).
- Overnight-extreme raids: n = 20-43, inconclusive.
- Underpowered.

#### X1P-T3 · Crowded side with real funding data (`t3_funding_race.py`)
- BTC 1h 2019-09-10 to 2025-01-07 with Binance BTCUSDT 8h funding (last settled print; trailing-180-day rank as in Memon et al.).
- 9,756 trials: 7,444 decided, 23.3% undecided, 0.4% same-bar. P(BSL first) 0.532.
- corr(funding rank, z72) = 0.16.

| Routine trials | n | P(BSL first) | Geometry | Residual |
|---|---|---|---|---|
| funding < 0 | 586 | 0.587 | 0.535 | **+0.052 ± 0.021** |
| 0 .. 0.01% | 1,374 | 0.517 | 0.517 | +0.001 ± 0.017 |
| = 0.01% (base) | 1,979 | 0.542 | 0.539 | +0.003 ± 0.015 |
| 0.01 .. 0.03% | 372 | 0.497 | 0.543 | -0.046 ± 0.029 |
| ≥ 0.03% per 8h | 523 | 0.545 | 0.564 | -0.019 ± 0.030 |

- Sweep bars:
  - funding < 0: +0.059 ± 0.030;
  - ≥ 0.03%: -0.048 ± 0.032;
  - by rank: bottom decile +0.033, top decile -0.015.
- Joint OLS of the residual (all trials, cluster 2H):
  - funding rank, centred: **-0.062 (t = -2.2)**;
  - z72, clipped: **+0.036 (t = +4.3)**.
  - Funding is contrarian once momentum, which continues, is controlled.
- Split halves:
  - bottom decile: +0.028 ± 0.031 (H1), +0.073 ± 0.036 (H2);
  - top decile: -0.051 ± 0.038 (H1), +0.001 ± 0.044 (H2);
  - funding < 0: +0.030 ± 0.029 (H1), +0.085 ± 0.029 (H2).
- **Sweep reading (claim B):** continuation = the next pool beyond the swept one is taken first; the residual is against geometry.

  | Swept pool | Funding rank < 30% | 30-70% | ≥ 70% |
  |---|---|---|---|
  | BSL (shorts' stops) | +0.001 ± 0.022 | -0.020 | +0.012 ± 0.024 |
  | SSL (longs' stops) | **-0.052 ± 0.025** | +0.001 | **+0.061 ± 0.025** |

  - Halves for SSL with rank ≥ 70%: +0.096 ± 0.039 and +0.034 ± 0.033.
  - Halves for SSL with rank < 30%: -0.028 ± 0.033 and -0.078 ± 0.039.
  - BSL cells are inconsistent across halves.
- **Reading:**
  - Claim A holds on the short-crowded side: about +5 pp BSL-first after negative funding, matching Memon et al.'s asymmetric result.
  - Claim B holds for longs: crowded-long SSL sweeps cascade, and uncrowded SSL sweeps are raids.
  - Grade **moderate-weak**: one asset, one venue, many cells, t ≈ 2-2.5.

#### Supporting proxy test from the earlier run of this lens (`x1_tools/crowd_race.py`, re-run identical: `x1_pos_tools/out_crowd_race_rerun.txt`)
Trailing return z as the crowding proxy.
- **BTC:** continuation. In the z72 top decile, BSL first is **+8.1 ± 2.3 pp** above geometry (slope t = 4.6).
- **ES, YM, RTY, NQ, GC, 6E, EURUSD pooled (n = 6,061):** no consistent effect. z24 top +3.8 ± 1.9; sweep bars z168 top -5.2 ± 2.8 and bottom +5.4 ± 2.6, a weak weekly-horizon contrarian lean after a sweep.
- Price-only crowding is therefore not a clean signal outside crypto.

#### X1P-T4 · OI flush at sweeps, BTC 2026 (`t4_oi_flush.py`)
- **Data:**
  - Binance hourly OI (2026-04-05 to 05-24) with spot 1h klines;
  - Binance 4h OI (2026-06-27 to 08-31) with 4h bars.
- **Method:** ΔOI on the sweep bar, z-scored on a trailing 48 bars. Outcomes: closed back inside on the sweep bar; breakout (+1 ATR beyond) vs reversal (-1 ATR back through) within 12 (1h) or 8 (4h) bars.

| ΔOI on the sweep bar (pooled n = 217) | Closed back inside | Breakout first |
|---|---|---|
| Flush (z ≤ -1), n = 37 | 0.54 ± 0.08 | 0.44 ± 0.08 |
| Flat, n = 133 | 0.62 ± 0.04 | 0.44 ± 0.04 |
| Build (z ≥ 1), n = 47 | 0.51 ± 0.07 | 0.58 ± 0.08 |

- 1h only: build gives 0.62 ± 0.08 breakout-first vs 0.43 ± 0.05 for flat.
- **Reading:** "flush = spent pool = reversal" is **not supported**. A possible build → breakout lean is underpowered (49 + 65 days of OI was all that was publicly reachable).

#### X1P-T5 · COT extremes and the weekly range (`t5_cot_weekly.py`)
- **Data:** ES legacy COT (2006-2026); each report applied from the Monday after its Friday release. SPX daily.
- **Sample:** weeks opening inside the prior week's range with a decided first touch (n = 723, 2008-2026). P(PWH first) 0.624.

| Speculator COT index | n | Residual |
|---|---|---|
| < 10% | 49 | -0.049 ± 0.039 |
| 10-30% | 90 | +0.066 ± 0.036 |
| 30-70% | 389 | -0.021 ± 0.019 |
| 70-90% | 147 | +0.025 ± 0.027 |
| ≥ 90% | 48 | +0.017 ± 0.055 |

- Speculator slope: -0.017 (t = -0.3).
- Hedger index cells: +0.024, -0.082, +0.017, +0.066, -0.093. Slope +0.073 (t = 1.4). Non-monotonic.
- Weekly speculator flow terciles: +0.035, -0.017, -0.019 (all within 1.5 SE).
- **Null.** This agrees with Sanders, Irwin & Merrin and with the slow, monthly nature of hedging-pressure premia.

#### X1P-T6 · OPEX cycle and max-pain hurdle (`t6_opex_maxpain.py`)
- **SPX weekly, 1999-2018 (n = 762):**
  - OPEX-M week: return +0.04%, range 1.090, P(PWH first) -0.4 pp;
  - post-M: +0.39%, range 0.984 (t = -1.5);
  - post-Q: -0.38% (t = -1.9), range **0.938** (t = -1.8), i.e. *smaller*, the opposite of "weakness = larger ranges".
- **SPX weekly, 2019-2026 (n = 413):**
  - OPEX-M week: P(PWH first) **+13.5 ± 6.2 pp**, not present in 1999-2018;
  - post-Q: -14.1 ± 9.9 pp;
  - range ratios 1.007-1.098, all |t| < 0.6.
  - There is no pattern that holds in both periods, out of 12 cells per period.
- OPEX Friday range and the max-pain hurdle are as in §2.3.
- GEX log-change on the first session after OPEX: **-0.055**, against about 0 on average. Expiring gamma does show up in GEX. The post-OPEX week's range does not rise.

---

## 3. TradingView data availability and limits

| Data | Ticker pattern (verified from code) | Granularity | Notes |
|---|---|---|---|
| CME futures OI | `ticker.standard(syminfo.tickerid) + "_OI"`, e.g. `CME_MINI:ES1!_OI` | daily | TradingView's built-in OI logic requests "1D" for intraday futures. Use `[1]` (or `[2]`) with lookahead_on |
| Crypto perp OI | `BINANCE:BTCUSDT.P_OI`, `BINANCE:BTCUSD.P_OI`, `BITMEX:XBTUSD.P_OI`, `KRAKEN:…USD.P_OI`, `BYBIT:…_OI`, `OKX:…_OI` | intraday OHLC | Built-in Open Interest indicator: candles for crypto. TradingView announced derivatives indicators for Binance, Bybit and OKX (funding, OI, long/short) |
| Perp premium index | `BINANCE:BTCUSDT_PREMIUM` (no `.P`) | intraday | Funding is estimated as `P̄ + clamp(0.01% - P̄, ±0.05%)`; community scripts warn the estimate is approximate. Units must be checked on the platform |
| Long/short ratio | `BINANCE:<PAIR>.P_LSR`, `BYBIT:…_LSR` (community scripts) | intraday | Undocumented. Use `ignore_invalid_symbol = true` |
| COT | `COT:13874A_F_NCP_L` (legacy noncommercial long), `COT3:…_LMP_S`, etc., built by the official `LibraryCOT` | weekly, on daily bars | Each metric is one request. CFTC root map is in the library |
| Short volume | `FINRA:<SYM>_SHORT_VOLUME` | daily | Short *volume* only, not short interest |
| VIX / VIX3M / VIX9D / VIX1D | `CBOE:VIX`, `CBOE:VIX3M`, … | daily, intraday | Gamma-regime proxies (X1P-1) |
| Options OI by strike, GEX, walls, max pain | **not available** | — | External only, by pasting (X1P-2) |

**Limits** (local docs mirror, `writing_scripts/limitations`):
- "up to 40 *unique* calls to the functions in the `request.*()` namespace, or up to 64 … with the Ultimate plan"; identical calls do not count again.
- The engine uses 6 today: lines 923-925, 939, 981 and 982.
- X1P-1 adds 2 (VIX, VIX3M); X1P-3 adds 1 (premium); X1P-4 adds 1 (OI).
- `input.text_area` holds up to 40,960 characters and parses line terminators (concepts/inputs.md).
- Real-time CME data needs a paid exchange add-on, otherwise it is delayed. Crypto exchange data is generally real-time. Futures OI is end-of-day regardless.

---

## 4. Engine gap analysis (line numbers in `baseline_v2.pine`)

| Concept | Status | Where / what differs |
|---|---|---|
| Volatility unit for PoT and reach | **partial** | `potSig = ta.stdev(chg, potLen)` (916) and the empirical surface keyed only on HTF bias (`f_empPoT` 1284-1301, `f_potModel` 1303-1312, `f_potBase` 1314-1323) are realised-only and regime-blind. T1: a gamma or implied-vol state adds R² 0.19 → 0.23 for the next-day range and changes P(PDH) by about 16 pp across quintiles at a fixed distance. The proximity reach in `evaluate` (665) uses the same σ |
| Dealer GEX / regime | **missing** | No options data in Pine. A proxy is possible (VIX/VIX3M). No request exists (923-982) |
| Zero-gamma, call wall, put wall, absolute gamma, OI walls | **missing** | Need pasted levels. No `input.text_area` anywhere in INPUTS (40-310). No level `src` for external levels (src codes 0-7, comment at 316; `f_tierW` 506-516; `f_levelName` 518-530) |
| Vanna / charm / "window of weakness" | **missing (correctly)** | Folklore (T6 null) |
| OPEX-day compression | **missing** | Weak σ multiplier of about 0.93 on monthly-OPEX Fridays. Belongs in the event calendar (`asset_specific` ASSET-5 / TIME-8), not in scoring |
| 0DTE | **n/a** | No data; evidence says damping |
| Max pain | **missing (correctly)** | Folklore for indices (T6 hurdle). Must never be a default target |
| Futures OI (EOD) | **missing** | No DOL evidence. Shadow covariate at most (X1P-4) |
| Crypto OI and OI flush at sweep | **missing** | T4 null for "flush = spent". The engine's sweep handling (1566-1585) uses only price |
| Funding / premium (crypto) | **missing** | T3: negative funding → BSL lean +5 pp; crowded-long SSL sweeps continue (+6 pp). D (1891-1897) has no positioning term. Sweep events update `liqEvt` from price alone (1579-1582) |
| Raid-vs-breakout reading | **partial / wrong** | 1579-1582: "a raid that holds = continuation, a raid that rejects = reversal", uniform across regimes. Sibling lenses found the reject → reversal mapping has no edge. T1 shows the hold rate of PDH breaks depends on the gamma regime. T3 shows the SSL-sweep continuation rate depends on crowding |
| Crowded side via momentum | **partial** | D's structure term `sV` and displacement `mV` (1892-1893) carry momentum. T3 shows z72 momentum continues (t = 4.3) with funding as a separate contrarian term. No explicit trailing-return term |
| Long/short ratio | **missing (correctly)** | No evidence |
| COT | **missing (correctly)** | T5 null; premia are monthly-scale |
| Short interest | **n/a** | Monthly; not in TradingView (short volume only) |
| External positioning levels (text box, expiry, ledger gating) | **missing** | Registry (`Ext`, 361-370; `f_pushExt` 1211-1228; registry → pool 1824-1856) and the confluence anchor list (1931-1933) are where such a family would plug in. The ledger (`Trial` 372-393, `f_openTrial` 1426-1431, `f_book` 1461-1500, `f_calMult` 1376-1382) grades only the *selected* target per group 0-3. There is no per-family shadow grading yet (`calib_ml` CAL-3 proposes it) |
| Alerts | **partial** | 2077-2094 has four events, none for regime changes (gamma proxy flip, funding state) |

---

## 5. Proposals (best first; every one is measurable by the engine's own ledger)

All proposals:
- keep structural logic on `barstate.isconfirmed`;
- read every request with a `[1]` offset and `lookahead_on`;
- default to *shadow* (graded, displayed in the Full accuracy panel, no scoring effect) until the per-chart ledger shows an edge.

They depend on `calib_ml` CAL-3 (candidate probes) where noted. Each gives a self-contained fallback mini-ledger.

### X1P-1 (P1, M) · Gamma-regime volatility state for PoT and reach on index and equity charts
**Why.**
- T1: the dealer-gamma state moves the next-day range by about ±15-20% and P(PDH) by about 16 pp at a fixed ATR distance, incrementally to VIX.
- About 75% of that is reproducible in Pine through VIX/VIX3M plus the VIX-implied σ in ATR units.
- The engine's σ (916) and its empirical surface are realised-only and regime-blind.
- This is the strongest, best-replicated positioning effect (Ni et al. 2021; Barbon & Buraschi; own test), and it acts on **PoT**, which the ledger can score (Brier and log-loss on trials).

**Inputs** (`G_POT`, `display = display.none`):
```pine
bool   grOn   = input.bool(true, "Gamma/vol regime state (index & equity charts)", group = G_POT, display = display.none)
string grSym  = input.string("CBOE:VIX", "Implied-vol index", group = G_POT, display = display.none)
string grSym3 = input.string("CBOE:VIX3M", "3-month implied-vol index", group = G_POT, display = display.none)
```

**Series** (SERIES block, after 917):
```pine
bool  grUse = grOn and (syminfo.type == "index" or syminfo.type == "futures" or syminfo.type == "stock" or syminfo.type == "fund")
// two separate top-level calls (simpler to audit than a nested request)
float iv1   = request.security(grSym,  "D", close[1], lookahead = barmerge.lookahead_on, ignore_invalid_symbol = true)
float iv3   = request.security(grSym3, "D", close[1], lookahead = barmerge.lookahead_on, ignore_invalid_symbol = true)
float grTS  = na(iv1) or na(iv3) or iv3 <= 0 ? 1.0 : iv1 / iv3     // > 1 = backwardation = low-gamma proxy
int   grReg = not grUse or na(iv1) ? 1 : grTS >= 1.0 ? 2 : grTS >= 0.90 ? 1 : 0   // 0 calm/long-gamma · 1 mid · 2 stressed/short-gamma
```
- The bucket edges come from T1 section I: VIX/VIX3M ≥ 1.0 holds about 10-15% of days, 0.90-1.0 about 30%, and < 0.90 the rest. Re-fit them per asset if the user overrides the symbols.

**State** (STATE, after 1080): a learned σ scale per regime bucket b and side s.
```pine
// per (regime b, side s): [Σ realised squared H-bar excursion (ATR²), Σ model σ²·H (ATR²), n windows]
// index = (b * 2 + s) * 3
var array<float> grSt = array.new<float>(18, 0.0)
```

**Update** (step 0, next to `f_bump` at 1527-1531, using the regime stored H bars ago):
```pine
int   rH = grReg[H]
float up = (fwdHi - close[H]) / aH
float dn = (close[H] - fwdLo) / aH
float m2 = math.pow(nz(potSig[H]) / aH, 2) * H
for s = 0 to 1
    int   j = (rH * 2 + s) * 3
    float e = s == 0 ? up : dn
    grSt.set(j,     grSt.get(j) + e * e)
    grSt.set(j + 1, grSt.get(j + 1) + m2)
    grSt.set(j + 2, grSt.get(j + 2) + 1)
```

**Use.** The multiplier scales the σ passed to `f_pot` in `f_potModel` (1303) and in `evaluate`'s reach (665).
- Bucket ratio: `ratio_bs = Σreal_bs / Σmodel_bs`.
- Pooled ratio over all buckets and sides: `ref = Σreal / Σmodel`.
- Shrunk ratio: `r̃ = (n_bs·ratio_bs + α·ref) / (n_bs + α)`, with α = 30·0.6·H effective windows (overlapping windows carry about 0.6·H times less information, as in `f_empPoT`).
- `kσ(b, s) = sqrt(r̃ / ref)`, clamped to [0.75, 1.35]; equal to 1 while `n_bs < 20·H`.
- The side-specific scale reproduces T1's finding that low gamma raises the upside reach more than the downside.
- Optionally make the empirical surface's regime key `r` (`f_empPoT`) the pair (HTF bias, grReg), with fallback to the pooled cells when n < nMin. This is already how `f_empPoT` falls back.

**Ledger measure.**
- Add `pReg` to `Trial`, the PoT with the regime scale, next to the existing `pBase`.
- Report the Brier score of `pReg` vs `pBase` on settled trials and on CAL-3 probes.
- Ship the default "on" only if the Brier improvement's 95% interval (block bootstrap on 2H blocks) excludes 0 on the reference charts (ES1!, NQ1!, SPY, an index).

**Raid reading (sub-item).**
- In step 3 (1579-1582), on index and equity charts, scale the "reject = reversal" contribution by regime: `evt *= grReg == 2 ? 0.5 : 1.0` for buy-side sweeps. Under low gamma PDH breaks hold: T1-D, 36.5% vs 44.9% close back inside.
- Shadow first. Coordinate with the sibling finding that the reject → reversal mapping is already too strong.

**Overlap.** Merge with x1_implied_vol's implied-vol unit, so that VIX enters PoT once. This proposal contributes the **term-structure regime and the side split**.

**Evidence:** moderate (own 15-year test, t ≈ 6-11; consistent literature).

**Risk:**
- 2 requests;
- VIX is US-equity specific. Gate by `syminfo.type`, and add a user override symbol for other assets (`CBOE:GVZ` gold, `CBOE:OVX` oil, `VOLMEX:BVIV` BTC; the last is not tested);
- adds a slow-moving state that can lag intraday shocks.

**Effort:** M (about 50 lines).

### X1P-2 (P2, M) · Pasted positioning levels: date-stamped, auto-expiring, an "OPT" family graded per chart before it may score
**Why.**
- Traders use GEX walls, zero gamma and max pain, and Pine cannot compute them.
- The evidence for these *levels* as targets or barriers is weak (walls) or none (max pain; T6 hurdle).
- So the honest design is ingestion plus **per-chart grading**, against a distance-matched random baseline, before any scoring effect. This answers "is my vendor's call wall worth anything on this chart?"

**Input format** (`G_POS = "Positioning Levels (pasted)"`, all `display = display.none`).
- One level per line: `YYYY-MM-DD[ HH:MM]; TYPE; PRICE[; EXPIRY YYYY-MM-DD]`.
- TYPE ∈ `CW` call wall · `PW` put wall · `ZG` zero gamma / flip / HVL · `AG` absolute-gamma strike · `OI` OI wall · `MP` max pain · `LV` generic.
- Optional regime line: `YYYY-MM-DD; GEX; NEG|POS`.

```pine
bool   posOn   = input.bool(false, "Use pasted positioning levels", group = G_POS, display = display.none)
string posTxt  = input.text_area("", "Levels (one per line)", group = G_POS, display = display.none,
  tooltip = "YYYY-MM-DD[ HH:MM]; TYPE; PRICE[; EXPIRY]. TYPE: CW PW ZG AG OI MP LV. Active from the stamp (exchange time), expires at EXPIRY's session end or after 'Life'. Append new days; keep ≤ 60 lines.")
string posMode = input.string("Shadow", "Use", options = ["Display", "Shadow", "Anchor when proven", "Target when proven"], group = G_POS, display = display.none)
float  posMul  = input.float(1.0, "Price × (SPY→SPX = 10)", group = G_POS, display = display.none)
float  posOff  = input.float(0.0, "Price + (SPX→ES basis)", group = G_POS, display = display.none)
int    posLife = input.int(1, "Life (sessions) if no expiry", minval = 1, maxval = 20, group = G_POS, display = display.none)
```

**Type** (TYPES, after `Trial`, about 393):
```pine
type PosLv
    int   t0
    int   t1
    float px
    int   typ          // 0 CW · 1 PW · 2 ZG · 3 AG · 4 OI · 5 MP · 6 LV
    int   lvId = -1
    int   probeBar = -1
```

**Parsing** (once, at global scope after STATE):
```pine
var array<PosLv> posLv  = array.new<PosLv>()
var int          posErr = 0
var array<int>   gexNegT = array.new<int>()      // session stamps flagged GEX NEG
if barstate.isfirst and posOn
    for ln in str.split(posTxt, "\n")
        string s = str.trim(ln)
        array<string> f = str.split(s, ";")
        string ds = f.size() > 0 ? str.trim(f.get(0)) : ""
        if str.length(s) > 0 and str.length(ds) < 10
            posErr += 1                                   // malformed date: skip before any substring call
        else if str.length(s) > 0
            int y  = int(str.tonumber(str.substring(ds, 0, 4)))
            int mo = int(str.tonumber(str.substring(ds, 5, 7)))
            int dd = int(str.tonumber(str.substring(ds, 8, 10)))
            int hh = str.length(ds) >= 16 ? int(str.tonumber(str.substring(ds, 11, 13))) : 0
            int mi = str.length(ds) >= 16 ? int(str.tonumber(str.substring(ds, 14, 16))) : 0
            int t0 = timestamp(syminfo.timezone, y, mo, dd, hh, mi)
            string tp = f.size() > 1 ? str.upper(str.trim(f.get(1))) : ""
            if tp == "GEX" and f.size() > 2
                if str.upper(str.trim(f.get(2))) == "NEG"
                    gexNegT.push(t0)
            else
                int typ = switch tp
                    "CW" => 0
                    "PW" => 1
                    "ZG" => 2
                    "AG" => 3
                    "OI" => 4
                    "MP" => 5
                    "LV" => 6
                    => -1
                float px = f.size() > 2 ? str.tonumber(str.trim(f.get(2))) : na
                int t1 = t0 + posLife * 86400000
                if f.size() > 3 and str.length(str.trim(f.get(3))) >= 10
                    string es = str.trim(f.get(3))
                    t1 := timestamp(syminfo.timezone, int(str.tonumber(str.substring(es, 0, 4))), int(str.tonumber(str.substring(es, 5, 7))), int(str.tonumber(str.substring(es, 8, 10))), 23, 59)
                if typ < 0 or na(px) or na(t0) or na(t1) or posLv.size() >= 60
                    posErr += 1
                else
                    posLv.push(PosLv.new(t0, t1, px * posMul + posOff, typ))
```
- Doc-grounded: `input.text_area` ("multiline text input", up to 40,960 characters), `str.split`, `str.trim`, `str.substring`, `str.tonumber` (returns na on failure), `str.upper`, and `timestamp(timezone, y, m, d, h, mi)` all exist in `reference/str.md` and `time.md`.
- Validate on TradingView that a text-area newline splits with `"\n"`. The docs say line terminators are parsed.
- An `int(na)` timestamp yields na; it is guarded.

**Activation and expiry** (ENGINE, new step 4b after the registry drop at 1586-1592, confirmed bars only):
- For each `PosLv` with `time >= t0 and time < t1` and `lvId == -1`:
  - create a pool `Level` with `kind = px > close ? 0 : 1`, `src = 9` (new code `OPT`; codes 8 and up are contested by sibling proposals, so pick the next free code at integration);
  - `top/bottom = px ± 0.5·wPx`, `anchorBar = f_barAtTime(t0, anchorMax)`;
  - mark the family `opt = true` (new `Level` field) so that a **touch** counts as reached, like arrays, not strict-through. Walls are magnets or barriers, not resting stops.
- At `time >= t1`, remove the pool level (ghost `⌛ EXPIRED` when Ghost Trail is on).
- Levels beyond `maxATR` stay in `posLv` and enter when in range, like the registry re-entry at 1824-1856.

**Modes:**
- *Display*: dotted lines with type labels; no pool entry.
- *Shadow* (default): pool entry with `mult = 0` for selection (never chosen, never ranked), graded by probes.
- *Anchor when proven*: pushes `px` into `anchors` (1931-1933), so the confluence pillar counts it, once proven.
- *Target when proven*: normal scoring with family calibration (`f_calMult`-style lift, bounded [0.8, 1.2]).

**Grading:**
- With CAL-3: routine probes, group "OPT" with a sub-key per type.
- Fallback: a self-contained mini-ledger.
  - Open a probe when an OPT level first comes within `[0.25, maxATR]` ATR, at most once per H bars per level.
  - Fields: `pb = f_potBase(d, side)`; outcome = touch within H bars.
  - Stats per type group (walls CW/PW/AG/OI, flip ZG, MP, LV): `posSt[g] = [n, k, Σpb, Σpb(1-pb)]`, plus 2H-block cluster residuals as in `f_book` (1461-1470).
  - Second metric, the barrier rate: among touched levels, the share where price closes back on the approach side within 3 bars. Compare it with the same rate for chart pools.
- **Gate:** a mode beyond Shadow takes effect for a type group only when `n ≥ 40`, `z = (k - Σpb) / sqrt(deff · Σpb(1-pb)) > 1.96`, and the lift's lower bound > 1. Otherwise the panel shows `OPT: shadow (n, lift, z)`.
- **MP is shadow-only by default**, even when "proven" (folklore prior); the user must tick a separate box.
- `GEX NEG` stamps (the session after the stamp) can feed X1P-1 as an override regime (`grReg := 2`).

**Non-repainting and look-ahead.**
- A level exists only from its stamp `t0`, so historical bars before the stamp never see it.
- A trader who pastes a vendor archive dated by the session it applies to gets an honest backtest.
- Pasting a level dated *before* its real publication time is the user's look-ahead. The tooltip says so.

**UX:**
- Terminal panel row: `OPT  12 live · walls lift 1.08 (z 1.1, n 63) · MP shadow`.
- Parse errors: `OPT ⚠ 2 lines skipped`.

**Evidence:**
- infrastructure: strong (ledger theory, `calib_ml`);
- the levels: weak (walls), none (max pain).

**Risk:**
- user burden (daily pasting);
- basis mapping errors on futures (`posOff` changes with the roll);
- small per-chart samples (a few levels per day), so the gate may stay closed for months. That is correct behaviour.

**Effort:** M (about 120 lines).

### X1P-3 (P2, M) · Crypto-perp funding state: buy-side tilt when shorts are crowded, cascade reading of crowded-long SSL sweeps
**Why.** T3, real Binance funding 2019-2025:
- negative funding → BSL first +5.2 ± 2.1 pp (sweep bars +5.9 ± 3.0), sign stable in both halves;
- crowded-long SSL sweeps continue +6.1 ± 2.5 pp, and uncrowded SSL sweeps reverse -5.2 ± 2.5 pp, signs stable;
- consistent with Memon et al. (extreme negative funding → +0.51% over 24h);
- the funding term is contrarian net of momentum (t = -2.2).

**Data** (SERIES; one request; crypto perps only):
```pine
bool   fdOn  = input.bool(true, "Funding state (crypto perps)", group = G_FLOW, display = display.none)
bool   isPerp = syminfo.type == "crypto" and str.endswith(syminfo.ticker, ".P")
string premTk = syminfo.prefix + ":" + str.replace(syminfo.ticker, ".P", "") + "_PREMIUM"
string fdTF   = f_tfSafe("60")
float  prem8  = request.security(premTk, fdTF, ta.sma(close, math.max(1, math.round(28800 / timeframe.in_seconds(fdTF))))[1],
                  lookahead = barmerge.lookahead_on, ignore_invalid_symbol = true)
float  fEst   = na(prem8) ? na : prem8 + math.max(-0.0005, math.min(0.0005, 0.0001 - prem8))
int    fdSt   = not (fdOn and isPerp) or na(fEst) ? 0 : fEst < 0 ? -1 : fEst >= 0.0003 ? 1 : 0   // -1 shorts crowded · +1 longs hot
```
- The premium's units must be confirmed on TradingView. If the median |premium| is above 0.01, it is in percent, so divide by 100. Detect this once on the last historical bar and show `FUND ⚠ units` if ambiguous.
- `ta.sma` inside `request.security` with a `simple int` length is fine. `timeframe.in_seconds(fdTF)` is simple.

**Effects** (both start in shadow):
1. **Draw tilt** in step 14 (1892-1894): `drawD += wF * (fdSt == -1 ? +0.15 : fdSt == 1 ? -0.07 : 0.0)`, with `wF` = 0 (shadow) or 1 (live). Asymmetric weights follow the asymmetric evidence.
2. **SSL-sweep reading** in step 3 (1579-1582), for `kind == 1` pools only:
   - if `fdSt == 1` (longs hot) or the trailing funding is high, set `evt := -1` (continuation down) even when the bar closes back above `lv.price`;
   - if `fdSt == -1`, keep `evt := +1` on a close back inside.
   - BSL sweeps are unchanged (no evidence).

**Ledger.**
- Add `fd` (funding state) to `Trial` and to CAL-3 probes.
- For the race module, compute the buy-minus-sell residual of probes by `fd`.
- Turn `wF` live when, in state -1, the BSL probes' residual minus the SSL probes' residual has `z > 2` with at least 100 probes per side. Turn it off again if z < 0 over the last 300.

**Evidence:** moderate-weak (one asset and venue, multiple cells; one supporting paper).

**Risk:**
- `_PREMIUM` naming and units are verified only from community scripts;
- other venues may not have it, in which case `ignore_invalid_symbol` makes `fdSt = 0`;
- funding regimes changed after 2024 (ETF era): the H2 effects are similar, but monitor them.

**Effort:** M (about 40 lines).

### X1P-4 (P3, S) · Positioning covariates logged on every probe and trial (for per-chart discovery, no scoring)
**Why.**
- The OI-flush (T4) and COT (T5) hypotheses are null or underpowered on our data, but traders keep asking for them.
- Logging them per chart lets the ledger answer them on each user's own market for free, without touching scores.

**Fields** added to `Trial` (372-393) and to the CAL-3 `Probe`:
- `dOIz`: ΔOI z-score on the opening bar;
- `fd`: the X1P-3 funding state;
- `gr`: the X1P-1 regime;
- `opt`: the X1P-2 nearest-level type within 0.5 ATR, or -1.

**OI:** one request.
```pine
float oiC = request.security(ticker.standard(syminfo.tickerid) + "_OI", syminfo.type == "crypto" ? timeframe.period : "1D", close[1], lookahead = barmerge.lookahead_on, ignore_invalid_symbol = true)
```
- Daily for CME futures, where each value is the prior session's OI, so the z-score is day-level only.
- Intraday for crypto.

**Report** (Full accuracy view):
- residual `Σ(y - pb)/n ± SE` for terciles of `dOIz` and for `fd`, `gr`, `opt`;
- one row per covariate, shown only when n ≥ 30 per cell;
- for sweep bars specifically, the breakout-vs-reversal residual (T4's design).
- The text says "observational; no effect on targets".

**Evidence:** n/a (instrumentation). It turns folklore into per-chart tests.

**Risk:** 1 request; panel clutter (Full view only).

**Effort:** S (about 30 lines once CAL-3 exists).

### X1P-5 (P3, S) · OPEX-Friday volatility multiplier for US index and equity charts
**Why:**
- T6: monthly-OPEX Fridays have a 6-8% smaller range than other Fridays, in both 2004-18 and 2019-26 (t = -1.6, -1.4);
- consistent with residual pinning on expiry day;
- no post-OPEX "weakness".

**Spec:**
- In the event-calendar table (`asset_specific` ASSET-5 / TIME-8), add the entry "monthly OPEX Friday (third Friday; Thursday if a holiday): σ × 0.93, US index, equity and ETF charts".
- Detection in Pine: `dayofweek(time, "America/New_York") == dayofweek.friday and dayofmonth(time, "America/New_York") >= 15 and dayofmonth(time, "America/New_York") <= 21`.
- The holiday-Thursday case is ignored (rare).
- Ledger: the σ multiplier is scored by PoT calibration, the same as other calendar multipliers.
- No HUD clutter beyond a `⚑ OPEX` tag in the Terminal style.

**Evidence:** weak. **Risk:** negligible (it reduces PoT by about 4% on 12 days a year). **Effort:** S (about 8 lines).

### X1P-6 (P3, S) · Honesty notes: say in the UI and README which positioning tools are absent and why
**Why.**
- The user and commercial competitors expect GEX levels, max pain, COT bias, liquidation maps and long/short ratios.
- Our tests show these are folklore, null, or only volatility states (§2).
- Saying so builds trust and stops "missing features" complaints.

**Spec:**
- README section "Positioning data: what we use and what we don't", with one line per item and the test result.
- Tooltip on the X1P-2 MP type: "max pain: no measured edge on indices; shadow only".

**Evidence:** strong for the null claims tested here (T5, T6, B9). **Effort:** S.

---

## 6. Folklore and do-not-build list

| Idea | Verdict | Basis |
|---|---|---|
| Max pain as a DOL target or magnet (index) | **folklore** | T6 hurdle: the 46.9-74.8% no-information base rates match or exceed vendor hit rates. Only single-stock weekly reversal evidence (Filippou et al.) |
| Vanna/charm "supportive into OPEX", "window of weakness" after | **folklore** | T6: no effect stable across 1999-2018 and 2019-2026. No systematic backtest exists |
| COT extremes pick the side of the weekly range | **null** | T5 (723 weeks). Premia are monthly-scale (Bessembinder; de Roon et al.) |
| OI flush at a sweep means a spent pool, so a reversal | **not supported** | T4 (217 sweeps). A build may lean breakout (underpowered) |
| Crowded side always gets run (generic, price-only proxy) | **mixed** | BTC: momentum continues. Other futures: no consistent effect (crowd_race). Only real funding shows a contrarian component (T3) |
| Long/short ratio extremes | **no evidence** | No study found |
| 0DTE gamma amplifies intraday moves | **contested, mostly no** | Dim et al.; Adams et al.; Cboe; vs Brogaard et al. |
| Liquidation heatmap clusters as magnets | **null** | `orderflow_micro` B9 |
| Short interest for intraday targets | **n/a** | Monthly predictor of aggregate returns (Rapach, Ringgenberg & Zhou 2016: out-of-sample R² 13.24% annual); TradingView has short volume only |

---

## 7. Reproducibility

- **Scripts:** `study/x1_pos_tools/`. Run each with `python3 -I <script>` (system python, numpy and pandas, no scipy).
  - `x1p_common.py`: loaders, race engine, cluster SEs;
  - `t1_gex_daily.py` → `out_t1_gex_daily.txt`;
  - `t2_gex_intraday.py` → `out_t2_gex_intraday.txt`;
  - `t3_funding_race.py` → `out_t3_funding_race.txt`;
  - `t4_oi_flush.py` → `out_t4_oi_flush.txt`;
  - `t5_cot_weekly.py` → `out_t5_cot_weekly.txt`;
  - `t6_opex_maxpain.py` → `out_t6_opex_maxpain.txt`;
  - the earlier run of this lens: `x1_tools/crowd_race.py`, `pool_crowd.py`, `opex_cycle.py` (re-run identical: `x1_pos_tools/out_crowd_race_rerun.txt`).
- **Data:** `study/x1_pos_data/`, public mirrors fetched from raw.githubusercontent.com. The exchange APIs, cftc.gov and squeezemetrics.com were blocked by the session proxy.
  - `gex/caribbel_DIX_HEAD_DIX.csv` (SqueezeMetrics DIX/GEX 2011-05 to 2026-11);
  - `crypto/VivekWar_Crypto-Funding-Rate-Arbitrage.csv` (Binance BTCUSDT funding 2019-09 to 2026-06);
  - `crypto/remyroche_Ares_oi.csv` and `crypto/82e46e_oi.csv` (Binance OI);
  - `crypto/k_2026*.csv` (Binance spot 1h klines 2026-04 to 08);
  - `cot/23bde3_cot.csv` (CFTC legacy COT, E-mini S&P, 2006-2026);
  - `spx/g1.csv` (S&P 500 daily 2011-2023);
  - `pine_refs/` (open-source Pine scripts read only to verify ticker conventions: `LibraryCOT`, OI indicators; no code copied into proposals).
- **Caveats:**
  - GEX is SqueezeMetrics' proprietary, classic-sign estimate;
  - funding is Binance only;
  - OI covers only about 115 days;
  - ES 1h covers only 179 complete sessions;
  - several literature numbers come from abstracts or secondary summaries, as flagged in the tables.

---

## 8. Sources

**Gamma, 0DTE, OPEX:**
- Barbon & Buraschi, "Gamma Fragility": https://abarbon.com/papers/gamma-fragility ; https://www.alexandria.unisg.ch/261487
- BSIC summary: https://bsic.it/how-dealers-gamma-impacts-underlying-stocks/
- Ni, Pearson, Poteshman & White (RFS 2021): https://ideas.repec.org/a/oup/rfinst/v34y2021i4p1952-1986..html ; draft: https://www.ou.edu/dam/price/Finance/CFS/paper/pdf/pearsonPoteshmanWhite.pdf
- Baltussen, Da, Lammers & Martens (JFE 2021): https://econpapers.repec.org/RePEc:eee:jfinec:v:142:y:2021:i:1:p:377-403 ; https://www3.nd.edu/~zda/intramom.pdf ; summary: https://alphaarchitect.com/hot-topic-does-gamma-hedging-actually-affect-stock-prices/
- Vidovich & Zerjal (2026), arXiv 2611.09286
- Dim, Eraker & Vilkov, 0DTE: https://www.maths.ox.ac.uk/node/67396 ; SSRN 4692190
- Adams, Fontaine & Ornthanalai: https://www.jean-sebastienfontaine.com/papers/0dte-options-volatility.pdf ; https://quantpedia.com/do-sp500-0dtes-options-increase-market-volatility/
- Brogaard, Han & Won (via Bloomberg summary): https://readwise.io/reader/shared/01hdsk5sncbn8w94mb14gc6w85
- Cboe, 0DTE: https://www.cboe.com/insights/posts/volatility-insights-evaluating-the-market-impact-of-spx-0-dte-options ; https://ir.cboe.com/news/news-details/2026/Cboe-Global-Markets-Reports-Trading-Volume-for-December-and-Full-Year-2025/ ; https://www.cboe.com/insights/posts/spx-0-dte-options-jump-to-record-62-share-in-august
- SqueezeMetrics GEX white paper (copy): https://slopeofhope.com/wp-content/uploads/2020/11/GEX-white_paper.pdf
- SpotGamma levels: https://spotgamma.com/options-key-levels-explained/ ; https://support.spotgamma.com/hc/en-us/articles/15297958613907-Zero-Gamma ; https://spotgamma.com/call-wall-put-wall-explained/

**Max pain and OPEX:**
- Filippou, Garcia-Ares & Zapatero, "No Max Pain, No Max Gain": https://www.econbiz.de/Record/no-max-pain-no-max-gain-stock-return-predictability-at-options-expiration-filippou-ilias/10013405282 ; https://fmai.memberclicks.net/assets/docs/Derivatives2025/GarciaAres.pdf
- Max pain practitioner tests: https://advancedautotrades.com/does-max-pain-really-work/ ; https://tradermarkus.com/max-pain-options/ ; https://optioncharts.io/blog/how-accurate-is-max-pain-in-option-trading
- Stivers & Sun (JBF 2013): https://ideas.repec.org/a/eee/jbfina/v37y2013i11p4226-4240.html ; https://cxoadvisory.com/calendar-effects/option-expiration-week-stock-return-drill-down
- "Window of weakness" commentary: https://investing.com/analysis/sp-500-welcome-to-the-window-of-weakness-200641914

**Hedging pressure and open interest:**
- Bessembinder (RFS 1992): https://ideas.repec.org/a/oup/rfinst/v5y1992i4p637-67.html
- de Roon, Nijman & Veld (JF 2000): https://ideas.repec.org/a/bla/jfinan/v55y2000i3p1437-1456.html
- Kang, Rouwenhorst & Tang (JF 2020): https://ideas.repec.org/a/bla/jfinan/v75y2020i1p377-417.html
- Wang (AFE 2003): https://ideas.repec.org/a/taf/apfiec/v13y2003i12p891-898.html
- Sanders, Irwin & Merrin (JARE 2009): https://ageconsearch.umn.edu/record/54547/files/JARE_Aug09__04R_pp276-296.pdf
- Hong & Yogo (JFE 2012): https://www.nber.org/papers/w16712

**Crypto perpetuals:**
- He, Manela, Ross & von Wachter: arXiv 2212.06888
- Cheng, Deng, Wang & Yu: arXiv 2102.04591
- Garcia Seuma: arXiv 2608.03616, 2607.27070
- Giagkiozis & Said: arXiv 2310.14973
- Funding-return evidence: https://medium.com/@fulgur.ventures/bitcoin-funding-rates-and-price-predictability-27ce95535af1 ; Memon, Anklesaria-Dalal & Mishra (2026), "Extreme Perpetual Futures Funding and Subsequent Bitcoin Returns" (abstract via web search)
- Binance funding mechanics: https://www.binance.com/en/support/faq/introduction-to-binance-futures-funding-rates-360033525031

**Short interest:**
- Rapach, Ringgenberg & Zhou (JFE 2016): https://econpapers.repec.org/RePEc:eee:jfinec:v:121:y:2016:i:1:p:46-65
- Hong, Li, Ni, Scheinkman & Yan, days to cover: https://nber.org/papers/w21166

**TradingView data:**
- TradingView crypto derivatives indicators: https://www.tradingview.com/blog/en/crypto-derivatives-indicators-on-tradingview-53558
- Request library (`_OI`, FINRA short volume): https://www.tradingview.com/script/Rpmobpw5-Request/
- Pine docs mirror: `docsrc/jabez4jc_pinescriptv6/reference/request.md` (LibraryCOT note, request.security), `writing_scripts/limitations` (40/64 unique requests), `mmmy_pine-script-doc-v6/pine-script-docs/concepts/inputs.md` (text_area up to 40,960 characters)

**Data mirrors:**
- GEX: https://raw.githubusercontent.com/caribbel/DIX/HEAD/DIX.csv
- Funding: https://raw.githubusercontent.com/VivekWar/Crypto-Funding-Rate-Arbitrage/HEAD/notebooks/BTCUSDT_historical_funding.csv
- OI: https://raw.githubusercontent.com/remyroche/Ares/HEAD/data/open_interest_hourly/BTCUSDT.csv ; https://raw.githubusercontent.com/zargul123/zar-x/HEAD/data/oi_history/BTCUSDT_4h.csv
- COT: https://raw.githubusercontent.com/krss1985-prog/seasonality-cot/HEAD/cot_spx_emini.csv
- SPX: https://raw.githubusercontent.com/AnswerXuan/Galformer-Improved-Transformer-for-Time-Series-Prediction/HEAD/Datasets/GSPC.csv
- BTC 1h: https://raw.githubusercontent.com/Cyber1king/crypto-paper-trader/HEAD/research_engine/data/oos/binance_spot_BTCUSDT_1h_2026MM.csv
