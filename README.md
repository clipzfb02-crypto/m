# MNQ 5-minute ORB buy/sell signals for TradingView

This is a TradingView Pine Script v6 indicator, plus a matching strategy, built only for **MNQ1! (Micro E-mini Nasdaq-100) on the 5-minute chart**.
The rules were picked by backtesting 3 years of real Nasdaq futures data, and several popular alternatives were rejected along the way.

> **Read this first.** No indicator can promise profits. With the default settings it won **85.7% of trades** from 2023 to 2025,
> with a **profit factor of 1.24** after costs and **every year profitable**. The catch: wins are small and losses are big.
> **One loss (about $185 per MNQ) wipes out about 5 wins (about $38 each)**, so always use the stop. Results on 2026 data were mixed
> (see [Results](#results)). Paper-trade it or run it on the smallest size before you risk real money.

| File | What it is |
|---|---|
| [`pine/MNQ_5m_ORB_Signals.pine`](pine/MNQ_5m_ORB_Signals.pine) | **Indicator.** BUY/SELL labels, entry/stop/target lines, liquidity levels (prior-day and overnight highs/lows), alerts, and a live stats table (win rate, profit factor, net P&L). |
| [`pine/MNQ_5m_ORB_Strategy.pine`](pine/MNQ_5m_ORB_Strategy.pine) | **Strategy.** The same rules for TradingView's Strategy Tester, with commission and slippage. |
| [`research/`](research/) | The Python backtest, data download script, and verification harness. Every number below can be reproduced from it. |

## Install on TradingView

1. Open a chart of **`MNQ1!`** and set the timeframe to **5 minutes**.
2. Open the **Pine Editor** tab at the bottom, then choose **New → Indicator**. Delete the template, paste the full contents of `pine/MNQ_5m_ORB_Signals.pine`, then click **Save** and **Add to chart**.
3. Optional: repeat with `pine/MNQ_5m_ORB_Strategy.pine` and open the **Strategy Tester** tab to see TradingView's own backtest on your data.
4. Alerts: click **Alert** (clock icon), set *Condition* to **MNQ ORB**, and pick one of these:
   * `ORB BUY`, `ORB SELL` or `ORB any signal`: a simple alert at the signal bar's close.
   * `Any alert() function call`: the message includes entry, stop, target and risk, plus a second alert when the trade closes (TP/SL/EOD).

On any other symbol or timeframe, the indicator shows no signals and its table tells you to switch to MNQ1! 5m.
You can turn that lock off in the settings. NQ1! is also allowed, since it has identical price action.

## The rules

All times are New York time. You don't need to change anything if your chart uses a different timezone.

| Step | Rule |
|---|---|
| Opening range | High and low of the first **15 minutes** after the 09:30 open (the 09:30, 09:35 and 09:40 bars). |
| BUY | The **first** 5-minute candle between 09:45 and 12:00 that **closes above** the range high **and** closes in the **top 20%** of its own high-low range. |
| SELL | Mirror image: closes below the range low, in the bottom 20% of the candle. |
| One trade per day | Once a qualifying breakout fires, there are no more signals that day. |
| Stop | The opposite side of the opening range. |
| Target | **0.2 × the stop distance** (0.2R), rounded down to a whole tick. Change it in the settings (see the trade-off table below). |
| End of day | Anything still open is closed at the 15:50 bar. |

## Liquidity levels

The indicator also draws the four liquidity levels most traders watch on NQ. These are the places where stop orders tend to cluster:

| Line | Colour | Meaning |
|---|---|---|
| **PDH / PDL** | orange | Previous day's high / low (regular session, 09:30–16:00 NY) |
| **ONH / ONL** | purple | Overnight high / low (18:00–09:30 NY) |

* **Swept levels:** once today's price trades through a level, the line fades and a small **×** marks the bar where it was swept. The table shows a ✓ next to it.
* **"LIQ" signals:** a BUY is labelled **"BUY LIQ"** when sell-side liquidity (the overnight or prior-day low) was already swept earlier that morning. A SELL is labelled **"SELL LIQ"** when buy-side liquidity (the overnight or prior-day high) was. This is the classic "grab the stops, then go the other way" pattern.
* **Optional filter:** **"Only signal after a liquidity sweep"** shows only the LIQ signals. It's **off by default** because the results are mixed:

| Period | Filter | Trades | Win rate | Profit factor | Net (1 MNQ) | Max drawdown |
|---|---|---:|---:|---:|---:|---:|
| 2023–2025 | off | 729 | 85.7% | 1.24 | +$4,548 | $1,722 |
| 2023–2025 | **on** | 290 | **86.6%** | **1.62** | +$3,956 | **$530** |
| 2026 NQ | off | 50 | 88.0% | 1.23 | +$477 | $1,295 |
| 2026 NQ | on | 23 | 82.6% | 0.83 | −$238 | $1,027 |
| 2026 MNQ | off | 41 | 80.5% | 0.74 | −$600 | $1,284 |
| 2026 MNQ | on | 18 | 77.8% | 0.51 | −$672 | $1,040 |

In 2023–2025 the filter cut the number of trades by 60%, raised the profit factor from 1.24 to 1.62, and cut the worst drawdown by two-thirds.
On 2026 data it did worse than no filter, and the win rate barely changes in any period. So treat LIQ as extra confirmation, not a guarantee.

Two other liquidity ideas were tested and rejected:
* **Fading sweeps** (selling when price pokes above the prior-day or overnight high and closes back below): lost money in most versions.
* **Avoiding trades with untouched liquidity just ahead:** no consistent effect.

Signals only fire on **closed** candles, and the script uses no higher-timeframe data, so **signals do not repaint**.
The stop is often wide: the median is about 90 points ($180 per MNQ contract), and 10% of days are wider than about 170 points ($340).
If that is too much for your account, use the optional **"Skip signal if risk is above"** setting. It is off in the backtest.

## Results

Data: real NQ futures 1-minute bars, resampled to 5-minute. NQ and MNQ move identically, and MNQ is worth $2 per point.
Every trade is charged **1.5 points ($3 per MNQ contract) round-trip** for commission and slippage.
Results are for **1 MNQ contract**. Entries fill at the next bar's open, the same way TradingView's Strategy Tester fills them.

| Period | Trades | Win rate | Profit factor | Net (1 MNQ) | Max drawdown |
|---|---:|---:|---:|---:|---:|
| 2023 | 251 | 84.1% | 1.13 | +$724 | $1,344 |
| 2024 | 248 | 85.9% | 1.34 | +$1,956 | $671 |
| 2025 | 230 | 87.4% | 1.24 | +$1,868 | $1,722 |
| **2023–2025** | **729** | **85.7%** | **1.24** | **+$4,548** | **$1,722** |
| 2026, NQ file (Feb 17 – Apr 28) | 50 | 88.0% | 1.23 | +$477 | $1,295 |
| 2026, MNQ file (Mar 5 – May 1) | 41 | 80.5% | 0.74 | −$600 | $1,284 |

* **26 of 36 months were profitable** from 2023 to 2025. The worst month lost $570 and the best made $653. The worst losing streak was 2 trades in a row.
* **Average win about $38, average loss about $185.** The high win rate comes from taking a small target against a wide stop.
* **2026:** the rules were first built with a 0.5R target, and on the untouched 2026 data that lost money on both files (−$224 NQ, −$1,674 MNQ).
  The 0.2R default was picked **after** seeing 2026, so the 2026 rows above are **not a blind test** any more. The MNQ file still lost money.
  The two files disagree partly because tiny price differences change which candles pass the "top 20%" test.
* **Costs matter more with small targets:** at 2.5 points ($5) per trade the 2023–25 profit factor falls to 1.16, and at 3.5 points ($7) to 1.08.
* **High win rate is more fragile.** At 0.2R some nearby settings lose money in some years (e.g. 0.9 candle strength in 2023–24, or a 10-minute range in 2025).
  At 0.5R every nearby setting was profitable in 2023–24. Keep the other settings at their defaults.
* **Win rate vs profit.** You can change the target in the settings:

| Target | Win rate 2023–25 | Profit factor | Net 2023–25 | 2026 NQ win rate / PF |
|---|---:|---:|---:|---:|
| 0.1R | 91.9% | 1.14 | +$1,394 | 88.0% / 0.58 |
| 0.15R | 88.3% | 1.07 | +$1,187 | 88.0% / 0.91 |
| **0.2R (default)** | **85.7%** | **1.24** | **+$4,548** | 88.0% / 1.23 |
| 0.25R | 82.6% | 1.22 | +$5,230 | 86.0% / 1.31 |
| 0.3R | 79.7% | 1.21 | +$5,952 | 76.0% / 0.84 |
| 0.5R | 69.1% | 1.23 | +$9,162 | 66.0% / 0.96 |
| 0.75R | 61.2% | 1.26 | +$12,562 | 60.0% / 1.09 |
| 1.0R | 55.7% | 1.26 | +$14,141 | 54.0% / 0.98 |

Targets below 0.2R push the win rate to 88–92% but barely make money, and lost clearly on 2026 data. Costs eat most of each tiny win.
**0.2R is the highest win rate that stayed profitable in every year.** 0.5R wins less often but made about twice as much.
Profit-lock stops (moving the stop to a small profit once price moves in your favour) were also tested. They didn't beat a plain 0.2R target.

### What was tested and rejected

The rules were chosen on 2023–2024 data and checked on 2025. Only ideas that held up in **both** periods were kept.

* **EMA 9/21/50 trend pullback with VWAP:** lost money in 2023–24 in every stop/target combination tried (profit factor about 0.9).
* **RSI(2) mean reversion:** won about 65% of trades but **lost money** in 2023–24 in every variant (profit factor 0.87–0.97). A high win rate alone is not an edge.
* **30-minute opening range:** worked in 2023–24 but failed in 2025. The 10-, 15- and 20-minute ranges all worked. 15 minutes sits in the middle of that stable zone.
* **Filters that didn't help consistently:** higher-timeframe trend, VWAP side, ADX, volume, gap direction, and opening-range size.
* **Extra trades per day and limit-order retest entries:** both lowered the profit factor.
* **Liquidity-sweep reversal entries** (fading a run above or below the prior-day or overnight high/low): lost money in most versions.
* **The "close in the top/bottom 20%" filter** was the one addition that helped in both periods. At 0.5R, every nearby setting (10/15/20-minute range × 0.7/0.8/0.9 strength) was profitable in 2023–24, and all but one in 2025.
  See `research/backtest.py` for the full grid.

## Checking the scripts for errors

I couldn't run TradingView's own compiler from here, so both scripts were checked three independent ways:

1. **`pinescript-v6-validator`** (static Pine v6 checks for function names, parameter names, argument counts and scope rules): **0 errors, 0 warnings** on both files.
2. **`pynescript`** (a Pine grammar parser): both files parse.
3. **PineTS** (a Pine v6 runtime): the **unmodified** scripts ran on 2023–2025 NQ data with MNQ contract specs.
   * **Indicator:** it produced the same 729 signals, on the same bars, with the same wins and the same net points as the Python backtest. This holds with the liquidity filter both off and on.
   * **Liquidity levels:** PDH, PDL, ONH, ONL and the sweep flags are identical to the Python reference on every bar.
   * **Strategy:** it produced identical entries, win counts within one trade per year, and was profitable every year after commission and slippage ($832 / $1,975 / $2,005).
     A handful of exits land one bar apart. That's mostly because PineTS requires price to trade *through* a limit order, while TradingView's default fills on a touch. Slippage shifting the bracket by one tick, and early-close holidays, account for the rest.

If TradingView ever reports an error, copy the message and line number back to me and I'll fix it.

## Caveats

* TradingView's `MNQ1!` data, contract rolls and your broker's fills will differ slightly from this data, so your Strategy Tester numbers won't match these exactly.
* On early-close holidays (e.g. the day after Thanksgiving), a trade still open at the early close is exited at the next session's first bar.
* The edge is modest (profit factor about 1.2), and past results don't guarantee future results. With an 86% win rate, a losing day still costs about 5 winning days. Losing weeks and months will happen. This is not financial advice.

## Reproduce the numbers

```bash
cd research
./fetch_data.sh                 # public NQ/MNQ minute data (~80 MB, not committed)
python prepare_data.py          # resample to TradingView-style 5-minute bars
python backtest.py              # every table in this README
cd verify_pinets && npm install && python verify.py   # validator + PineTS equivalence checks
```

Requires Python 3.10+ with `pandas`, `numpy` and `numba`, plus Node 18+ for the verification step.
