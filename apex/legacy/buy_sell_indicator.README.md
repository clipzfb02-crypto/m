# TradingView Buy/Sell Indicator

A professional multi-signal buy/sell indicator for TradingView, combining RSI, Moving Averages, and MACD to generate reliable trading signals.

## Features

- **Multi-Signal Analysis**: Combines three technical indicators for better accuracy
  - RSI (Relative Strength Index) for overbought/oversold conditions
  - Moving Average Crossovers (EMA or SMA)
  - MACD (Moving Average Convergence Divergence)

- **Configurable Signal Strength**: Set minimum number of indicators that must align before generating a signal

- **Visual Indicators**:
  - Green triangles for buy signals
  - Red triangles for sell signals
  - Colored backgrounds highlighting buy/sell zones
  - Moving average lines overlay

- **Alerts**: Built-in alert conditions for real-time notifications

- **Flexible Settings**: Fully customizable parameters for all indicators

## Installation

1. Open TradingView and navigate to the Pine Script editor
2. Create a new indicator script
3. Copy the contents of `buy_sell_indicator.pine` into the editor
4. Click "Add to Chart"

## Configuration

### RSI Settings
- **RSI Length**: Period for RSI calculation (default: 14)
- **Overbought Level**: RSI threshold for overbought (default: 70)
- **Oversold Level**: RSI threshold for oversold (default: 30)

### Moving Average Settings
- **Fast MA Length**: Period for fast moving average (default: 9)
- **Slow MA Length**: Period for slow moving average (default: 21)
- **MA Type**: Choose between EMA or SMA (default: EMA)

### MACD Settings
- **MACD Fast Length**: Fast EMA period (default: 12)
- **MACD Slow Length**: Slow EMA period (default: 26)
- **MACD Signal Length**: Signal line period (default: 9)

### Signal Settings
- **Minimum Signals for Trade**: Number of indicators that must align (default: 2)
  - 1: Any single indicator triggers a signal (most frequent)
  - 2: At least 2 indicators must agree (balanced)
  - 3: All 3 indicators must agree (most conservative)

### Visual Settings
- Toggle individual signal displays (RSI, MA, MACD)
- Show/hide moving average lines

## How It Works

### Buy Signal
A buy signal is generated when:
- **RSI Condition**: RSI falls below the oversold level (default 30)
- **MA Condition**: Fast MA crosses above the Slow MA
- **MACD Condition**: MACD line crosses above the signal line

The number of conditions that must be met is configurable via "Minimum Signals for Trade".

### Sell Signal
A sell signal is generated when:
- **RSI Condition**: RSI rises above the overbought level (default 70)
- **MA Condition**: Fast MA crosses below the Slow MA
- **MACD Condition**: MACD line crosses below the signal line

## Usage Tips

1. **For Conservative Trading**: Set minimum signals to 3 (requires all indicators)
2. **For Active Trading**: Set minimum signals to 1 (more frequent signals)
3. **Balanced Approach**: Use minimum signals of 2 (default)

4. **Timeframe Recommendation**: Works best on 1H, 4H, and Daily timeframes
5. **Asset Types**: Suitable for stocks, forex, and cryptocurrencies

6. **Combine with Support/Resistance**: Use in conjunction with key support and resistance levels
7. **Volume Confirmation**: Verify signals with volume for better reliability

## Alert Setup

To enable alerts:
1. Click the alarm bell icon on the indicator
2. Select "Buy Signal Alert" or "Sell Signal Alert"
3. Set your notification preferences (pop-up, email, SMS, etc.)

## Disclaimer

This indicator is for educational and informational purposes only. Always do your own research and consult with a financial advisor before making trading decisions. Past performance does not guarantee future results.

## Version

Version: 1.0
Last Updated: September 30, 2024
