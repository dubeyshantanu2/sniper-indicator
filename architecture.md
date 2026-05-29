# Architecture Document: Sniper Trading Assistant

## 1. Objective
To build a Python-based, multi-timeframe (1-minute and 4-hour) trading assistant that ingests live market data via the Dhan API, identifies "Sweep" trade setups based on specific Pine Script logic, manages trade lifecycle state in Supabase, and provides real-time, actionable alerts via Discord Webhooks. The system will be designed for deployment on Fly.io and will initialize by providing a briefing of active trades upon startup.

## 2. High-Level Architecture

*   **Language:** Python 3.11+
*   **Market Data & Execution:** Dhan HQ API v2 (WebSocket for live ticks, REST for historical bootstrapping).
*   **Data Processing:** `pandas` and `pandas-ta` for calculating EMAs, VWAP, and volume averages.
*   **Database (State Management):** Supabase (PostgreSQL) using the `supabase-py` client.
*   **Notifications:** Discord Webhooks for formatted channel alerts.
*   **Deployment:** Docker container deployed on Fly.io.

## 3. Core Modules

### 3.1 `main.py` (Application Entry Point)
*   **Startup Routine:** Upon startup, it queries Supabase for all trades where `status != 'Closed'`. It compiles these into a "Morning Briefing" message and sends it to Discord.
*   **Bootstrapping:** Fetches historical data (last 200 candles for 1m and 4h timeframes) via Dhan REST API to "warm up" the indicators.
*   **Connection:** Initializes the Dhan Live Market WebSocket and begins listening to ticks.

### 3.2 `market_data.py` (Dhan Integration)
*   Handles authentication with DhanHQ.
*   Manages the WebSocket connection, subscribes to required instruments (e.g., Nifty 50, BankNifty), and handles reconnections.
*   Aggregates live ticks into 1-minute and 4-hour candle structures (`Open, High, Low, Close, Volume`).

### 3.3 `strategy.py` (The Brains)
*   Translates the Pine Script logic into Python.
*   Maintains a rolling window DataFrame of candles for each instrument and timeframe.
*   **Calculations:** Computes EMA 14, VWAP, and 20-period Volume SMA.
*   **Signal Detection:** Evaluates the anatomical structure of every closed candle (wick-to-body ratios) and checks for touches on key levels (EMA/VWAP) accompanied by volume spikes.
*   **Trade Setup Generation:** When a signal occurs, it calculates:
    *   **Stop Loss (SL):** High/Low of the signal candle.
    *   **Targets:** T1 (1:2 R:R), T2 (1:3 R:R), T3 (1:5 R:R).
    *   **Suggested Strike:** Determines 1 strike In-The-Money (ITM) based on current spot price (e.g., nearest 50 interval for Nifty + 1 strike depth).

### 3.4 `trade_manager.py` (State Machine)
*   **New Trades:** Receives signal from `strategy.py`, generates a random 4-digit `trade_id`, inserts the record into Supabase as `Active`, and triggers a Discord alert.
*   **Live Evaluation:** For every new price tick received from `market_data.py`, it evaluates the current price against the SL, T1, T2, and T3 of all `Active`, `T1_Hit`, or `T2_Hit` trades in Supabase.
*   **State Transitions:**
    *   **Hits T1:** Updates status to `T1_Hit`, updates SL to Entry Price. Triggers alert: "Close 40%, Move SL to Entry".
    *   **Hits T2:** Updates status to `T2_Hit`, updates SL to T1. Triggers alert: "Close 40%, Move SL to T1".
    *   **Hits T3:** Updates status to `Closed`. Triggers alert: "Target 3 Hit! Close remaining 20%".
    *   **Hits SL:** Updates status to `Closed`. Triggers alert: "Stop Loss Hit".

### 3.5 `notifier.py` (Discord Integration)
*   Formats rich Discord embeds for clean presentation.
*   Handles different message types: New Signal, Target Achieved, Stop Loss, and Startup Briefing.

## 4. Database Schema (Supabase)

Table: `sniper_active_trades`
*   `id` (UUID, Primary Key)
*   `trade_id` (String, 4-digit random, e.g., "7492")
*   `symbol` (String, e.g., "NIFTY50")
*   `timeframe` (String, "1m" or "4h")
*   `direction` (String, "LONG" or "SHORT")
*   `entry_price` (Float)
*   `sl_price` (Float) - *Note: This value updates dynamically as targets are hit.*
*   `t1_price` (Float)
*   `t2_price` (Float)
*   `t3_price` (Float)
*   `suggested_strike` (String, e.g., "22500 CE")
*   `status` (Enum: `Active`, `T1_Hit`, `T2_Hit`, `Closed`)
*   `created_at` (Timestamp)
*   `updated_at` (Timestamp)

## 5. Deployment Profile

*   **Infrastructure:** Fly.io
*   **Process:** A single `worker` process running the asynchronous Python script.
*   **Environment Variables:**
    *   `DHAN_CLIENT_ID`
    *   `DHAN_ACCESS_TOKEN`
    *   `SUPABASE_URL`
    *   `SUPABASE_KEY`
    *   `DISCORD_WEBHOOK_URL`

## 6. Implementation Steps

1.  **Project Setup:** Initialize Python project, `requirements.txt`, and basic directory structure.
2.  **Supabase Setup:** Create the `sniper_active_trades` table and configure the Python client.
3.  **Dhan Connection:** Implement REST historical fetch and WebSocket tick ingestion.
4.  **Strategy Engine:** Build the logic to convert ticks to candles and apply the EMA/VWAP/Sweep logic using `pandas`.
5.  **Trade Management Loop:** Implement the logic to create trades in Supabase and track them against live ticks.
6.  **Discord Integration:** Build the formatter for alerts and the startup briefing logic.
7.  **Testing:** Validate logic with static historical data.
8.  **Deployment:** Create `Dockerfile` and `fly.toml` for deployment.