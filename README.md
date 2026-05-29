# Sniper-Indicator (V6.6 Pro)

This Pine Script file (`indicator.pine`) for **Sniper V6.6 Pro** is a comprehensive trading indicator that combines several popular concepts: moving averages, VWAP, Fair Value Gaps (FVG), volume analysis, Cumulative Volume Delta (CVD) divergence, Opening Range Breakouts (ORB), and specific candlestick pattern recognition (sweeps) for entry signals.

Here is a breakdown of the logic, section by section:

## 1. Moving Averages & VWAP
The script calculates and plots three Exponential Moving Averages (EMA): a fast one (14 periods), an intermediate one (50 periods), and a macro one (200 periods). It also plots the Volume Weighted Average Price (VWAP). These are standard tools used to identify trend direction and dynamic support/resistance levels.

## 2. Fair Value Gaps / Imbalances
The script automatically detects and draws boxes for Fair Value Gaps (FVGs), which represent price imbalances:
*   **Bullish FVG:** Occurs when the `low` of the current candle is higher than the `high` of the candle two periods ago, leaving a gap.
*   **Bearish FVG:** Occurs when the `high` of the current candle is lower than the `low` of the candle two periods ago.
*   **Mitigation Logic:** The script keeps track of these FVG boxes in an array. If future price action comes back and fully "fills" the gap (e.g., price drops below the bottom of a bullish FVG), the script deletes that specific box, considering the imbalance resolved.

## 3. Divergence Delta / CVD
This part analyzes the relationship between price movement and buying/selling pressure (volume):
*   It calculates **Cumulative Volume Delta (CVD)**. If a candle closes green, its volume is added; if red, it's subtracted.
*   **Bullish Divergence:** Detects if the price makes a *lower low* compared to the previous bar, but the CVD is *higher* (indicating less selling pressure or hidden buying on the dip), and the candle closes green.
*   **Bearish Divergence:** Detects if the price makes a *higher high*, but the CVD is *lower* (buying pressure is exhausting), and the candle closes red.
*   It highlights the borders of the candles where these divergences occur (Aqua for bullish, Fuchsia for bearish).

## 4. Opening Range Breakout - ORB
The ORB logic focuses on a specific time window, typically near the market open:
*   It defines a session (default is `0915-0930` in the Kolkata time zone).
*   During this 15-minute window, it records the highest high (`ORB-H`) and lowest low (`ORB-L`).
*   Once that session ends, it draws horizontal lines extending to the right from those price levels. Traders often use these lines to trade breakouts (price crossing above the high or below the low) later in the day.

## 5. Main Entry Signals / "Gatillos"
This is the core signal generation part of the indicator. It looks for specific candlestick "sweeps" (rejection wicks) at key levels, filtered by volume:
*   **Candle Anatomy:** It measures the body size, upper wick size, and lower wick size of the candle.
*   **Key Level Touch:** It checks if the candle's price range has touched either the **EMA 14** or the **VWAP**.
*   **Volume Filter:** It checks if the current candle's volume is higher than a moving average of the volume multiplied by a factor (default 1.1x). This ensures signals happen on above-average volume.
*   **LONG Signal:**
    *   The lower wick must be significantly larger than the body (default 1.5x larger). This shows strong rejection of lower prices.
    *   The upper wick must be small (default max 0.6x the body).
    *   The candle must touch the EMA 14 or VWAP.
    *   It must be a bullish candle (close > open).
    *   Volume filter must be met.
*   **SHORT Signal:**
    *   The upper wick must be significantly larger than the body (rejection of higher prices).
    *   The lower wick must be small.
    *   The candle must touch the EMA 14 or VWAP.
    *   It must be a bearish candle (close < open).
    *   Volume filter must be met.

When all these conditions align, it prints "LONG" (green triangle below) or "SHORT" (red triangle above) and triggers alerts.

**In summary:** This script looks for precise candlestick rejection patterns (long wicks) that bounce off the fast EMA or VWAP, backed by strong volume, while also providing structural context like Fair Value Gaps, Volume Delta Divergences, and Opening Range levels.
