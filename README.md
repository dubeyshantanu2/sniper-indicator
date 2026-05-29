# Sniper-Indicator (V6.6 Pro) & Trading Assistant

This project contains the Pine Script for **Sniper V6.6 Pro** indicator and a Python-based trading assistant backend that automates the generation and tracking of those signals.

## Pine Script Indicator (`indicator.pine`)

The indicator is a comprehensive trading tool that combines several popular concepts: moving averages, VWAP, Fair Value Gaps (FVG), volume analysis, Cumulative Volume Delta (CVD) divergence, Opening Range Breakouts (ORB), and specific candlestick pattern recognition (sweeps) for entry signals.

*   **Moving Averages & VWAP:** Calculates EMA (14, 50, 200) and VWAP to identify trend direction.
*   **Fair Value Gaps / Imbalances:** Detects and draws boxes for bullish and bearish FVGs.
*   **Divergence Delta / CVD:** Analyzes cumulative volume delta against price movement to find hidden divergences.
*   **Opening Range Breakout - ORB:** Draws breakout levels for a specific time window near the market open.
*   **Main Entry Signals / "Gatillos":** Core signal generation based on candlestick "sweeps" (rejection wicks) at key levels (EMA/VWAP), filtered by moving average volume. Generates LONG and SHORT alerts.

---

## Python Trading Assistant Backend

The Python backend automates the logic of the "Main Entry Signals" from the Pine Script. It connects to the Dhan HQ API to ingest live market data, calculates the required indicators (EMA 14, VWAP, Volume SMA) using `pandas` and `pandas-ta`, and manages trade lifecycles in a Supabase PostgreSQL database. Alerts are sent to Discord via webhooks.

### Features
*   **Multi-timeframe support:** Aggregates ticks into 1-minute and 4-hour candles.
*   **Trade State Machine:** Automatically tracks Active trades against Stop Loss (SL) and Targets (T1: 1:2, T2: 1:3, T3: 1:5 R:R). Updates SL automatically as targets are hit.
*   **Discord Notifications:** Rich embedded messages for Morning Briefings, New Signals, Target achievements, and Stop Loss hits.

### Project Structure
*   `src/main.py`: Entry point and main evaluation loop.
*   `src/api/market_data.py`: Dhan API WS/REST integration.
*   `src/strategy/engine.py`: Pandas dataframe calculations and signal logic.
*   `src/database/trade_manager.py`: Supabase connection and state management.
*   `src/notifications/notifier.py`: Discord Webhook integration.

### Setup Instructions

1.  **Environment Variables:** Create a `.env` file in the root directory (do not commit it).
    ```env
    DHAN_CLIENT_ID=your_client_id
    DHAN_ACCESS_TOKEN=your_access_token
    SUPABASE_URL=your_supabase_url
    SUPABASE_KEY=your_supabase_key
    DISCORD_WEBHOOK_URL=your_webhook_url
    ```
2.  **Dependencies:** Install via pip:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Run Locally:**
    ```bash
    python -m src.main
    ```

### Deployment (Fly.io)

This project is configured for deployment on Fly.io using Docker.

1.  Install the Fly CLI.
2.  Authenticate: `flyctl auth login`
3.  Launch the app (do not set up Postgres/Redis if asked, as we use Supabase):
    ```bash
    flyctl launch --no-deploy
    ```
4.  Set secrets on Fly:
    ```bash
    flyctl secrets set DHAN_CLIENT_ID=xxx DHAN_ACCESS_TOKEN=xxx SUPABASE_URL=xxx SUPABASE_KEY=xxx DISCORD_WEBHOOK_URL=xxx
    ```
5.  Deploy:
    ```bash
    flyctl deploy
    ```
