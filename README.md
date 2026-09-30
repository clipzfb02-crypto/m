# MNQ 5-minute ORB buy/sell signals for TradingView

This is a TradingView Pine Script v6 indicator, plus a matching strategy, built only for **MNQ1! (Micro E-mini Nasdaq-100) on the 5-minute chart**.
The rules were picked by backtesting 3 years of real Nasdaq futures data, and several popular alternatives were rejected along the way.

> **Read this first.** No indicator can promise profits. This one had a small but consistent edge from 2023 to 2025: about a **69% win rate** and a
> **profit factor of 1.23** after costs, with **every year profitable**. On a separate, never-touched 2026 test period it **lost a little money**
> (see [Results](#results)). Paper-trade it or run it on the smallest size before you risk real money.

| File | What it is |
|---|---|
| [`pine/MNQ_5m_ORB_Signals.pine`](pine/MNQ_5m_ORB_Signals.pine) | **Indicator.** BUY/SELL labels, entry/stop/target lines, alerts, and a live stats table (win rate, profit factor, net P&L). |
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
| Target | **0.5 × the stop distance** (0.5R), rounded down to a whole tick. |
| End of day | Anything still open is closed at the 15:50 bar. |

Signals only fire on **closed** candles, and the script uses no higher-timeframe data, so **signals do not repaint**.
The stop is often wide: the median is about 90 points ($180 per MNQ contract), and 10% of days are wider than about 170 points ($340).
If that is too much for your account, use the optional **"Skip signal if risk is above"** setting. It is off in the backtest.

## Results

Data: real NQ futures 1-minute bars, resampled to 5-minute. NQ and MNQ move identically, and MNQ is worth $2 per point.
Every trade is charged **1.5 points ($3 per MNQ contract) round-trip** for commission and slippage.
Results are for **1 MNQ contract**. Entries fill at the next bar's open, the same way TradingView's Strategy Tester fills them.

| Period | Trades | Win rate | Profit factor | Net (1 MNQ) | Max drawdown |
|---|---:|---:|---:|---:|---:|
| 2023 | 251 | 69.3% | 1.23 | +$2,452 | $869 |
| 2024 | 248 | 67.3% | 1.17 | +$2,184 | $714 |
| 2025 | 230 | 70.9% | 1.29 | +$4,526 | $1,168 |
| **2023–2025** | **729** | **69.1%** | **1.23** | **+$9,162** | **$1,178** |
| 2026 blind test, NQ file (Feb 17 – Apr 28) | 50 | 66.0% | 0.96 | −$224 | $1,180 |
| 2026 blind test, MNQ file (Mar 5 – May 1) | 41 | 58.5% | 0.65 | −$1,674 | $1,683 |

* **25 of 36 months were profitable** from 2023 to 2025. The worst month lost $235 and the best made $1,292.
* **2026 blind test:** these months were set aside and never used to choose any setting. Both files lost money.
  A 50-trade stretch as weak as the NQ result (profit factor 0.96) happened about **1 time in 4** when resampling the 2023–25 trades, so it fits normal variance.
  The MNQ result (0.65) is rarer, below 3%, so treat it as a real warning sign. The two files disagree partly because tiny price differences change which candles pass the "top 20%" test.
* **Costs:** at 2.5 points ($5) per trade the 2023–25 profit factor falls to 1.19, and at 3.5 points ($7) to 1.15.
* **Win rate vs profit.** You can change the target in the settings:

| Target | Win rate 2023–25 | Profit factor | Net 2023–25 | 2026 NQ win rate / PF |
|---|---:|---:|---:|---:|
| 0.4R | 73.4% | 1.19 | +$6,814 | 72.0% / 0.95 |
| **0.5R (default)** | **69.1%** | **1.23** | **+$9,162** | 66.0% / 0.96 |
| 0.75R | 61.2% | 1.26 | +$12,562 | 60.0% / 1.09 |
| 1.0R | 55.7% | 1.26 | +$14,141 | 54.0% / 0.98 |

### What was tested and rejected

The rules were chosen on 2023–2024 data and checked on 2025. Only ideas that held up in **both** periods were kept.

* **EMA 9/21/50 trend pullback with VWAP:** lost money in 2023–24 in every stop/target combination tried (profit factor about 0.9).
* **RSI(2) mean reversion:** won about 65% of trades but **lost money** in 2023–24 in every variant (profit factor 0.87–0.97). A high win rate alone is not an edge.
* **30-minute opening range:** worked in 2023–24 but failed in 2025. The 10-, 15- and 20-minute ranges all worked. 15 minutes sits in the middle of that stable zone.
* **Filters that didn't help consistently:** higher-timeframe trend, VWAP side, ADX, volume, gap direction, and opening-range size.
* **Extra trades per day and limit-order retest entries:** both lowered the profit factor.
* **The "close in the top/bottom 20%" filter** was the one addition that helped in both periods. Every nearby setting (10/15/20-minute range × 0.7/0.8/0.9 strength × 0.5/0.75/1.0R) was profitable in 2023–24, and all but one in 2025.
  See `research/backtest.py` for the full grid.

## Checking the scripts for errors

I couldn't run TradingView's own compiler from here, so both scripts were checked three independent ways:

1. **`pinescript-v6-validator`** (static Pine v6 checks for function names, parameter names, argument counts and scope rules): **0 errors, 0 warnings** on both files.
2. **`pynescript`** (a Pine grammar parser): both files parse.
3. **PineTS** (a Pine v6 runtime): the **unmodified** scripts ran on 2023–2025 NQ data with MNQ contract specs.
   * **Indicator:** it produced the same 729 signals, on the same bars, with the same wins and the same net points as the Python backtest.
   * **Strategy:** it produced identical entries and win counts, and was profitable every year after commission and slippage ($2,327 / $2,299 / $4,586).
     A handful of exits land one bar apart. That's mostly because PineTS requires price to trade *through* a limit order, while TradingView's default fills on a touch. Slippage shifting the bracket by one tick, and early-close holidays, account for the rest.

If TradingView ever reports an error, copy the message and line number back to me and I'll fix it.

## Caveats

* TradingView's `MNQ1!` data, contract rolls and your broker's fills will differ slightly from this data, so your Strategy Tester numbers won't match these exactly.
* On early-close holidays (e.g. the day after Thanksgiving), a trade still open at the early close is exited at the next session's first bar.
* The edge is modest (profit factor about 1.2), and past results don't guarantee future results. Losing weeks and months will happen. This is not financial advice.

## Reproduce the numbers

```bash
cd research
./fetch_data.sh                 # public NQ/MNQ minute data (~80 MB, not committed)
python prepare_data.py          # resample to TradingView-style 5-minute bars
python backtest.py              # every table in this README
cd verify_pinets && npm install && python verify.py   # validator + PineTS equivalence checks
```

Requires Python 3.10+ with `pandas`, `numpy` and `numba`, plus Node 18+ for the verification step.
