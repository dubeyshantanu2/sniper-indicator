# Strategy Improvements TODO

This document tracks potential improvements to the Sniper-Indicator strategy (both Pine Script and Python backend) based on backtesting and visual analysis.

## 1. Solve "Late Entry" (Intra-Candle Triggers)
*   **Problem:** Signals are generated only at the close of the candle, missing the optimal entry point during high momentum sweeps.
*   **Solution:** Implement "Touch & Reclaim" logic tick-by-tick. If the price drops below the EMA 14/VWAP and crosses back above it with high volume, trigger the entry instantly rather than waiting for the candle close.
*   **Complexity:** High (requires tick-level streaming and state management).

## 2. Integrate FVG Confluence into Python Automation
*   **Problem:** The Python backend trades EMA/VWAP touches blindly, ignoring structural context like Fair Value Gaps (FVG) which are visually present on the chart.
*   **Solution:** Port the FVG array logic from Pine Script to `strategy/engine.py`. Add a strict rule to only take LONG sweeps if the wick taps into an active Bullish FVG, and SHORT sweeps if they tap a Bearish FVG.
*   **Complexity:** Medium (requires maintaining FVG state arrays in pandas).

## 3. Smarter Stop Losses (ATR Buffer)
*   **Problem:** Stop Losses placed exactly at the candle low/high are vulnerable to liquidity grabs by market makers.
*   **Solution:** Add an Average True Range (ATR) buffer to the Stop Loss. 
*   **Formula:** `Stop Loss = Candle Low - (ATR * 0.5)` for LONGs.
*   **Complexity:** Low (requires adding `pandas-ta` ATR calculation).

## 4. Multi-Timeframe Alignment
*   **Problem:** Taking 5-minute sweeps against the macro trend leads to low win rates.
*   **Solution:** Introduce a higher timeframe filter (e.g., 1-hour or 4-hour EMA 200). Only allow LONGs if the price is above the macro EMA.
*   **Complexity:** Medium (requires tracking state across multiple timeframes concurrently).
