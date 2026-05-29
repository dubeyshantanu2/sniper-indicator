import os
import pandas as pd
import pandas_ta as ta
from datetime import datetime, timedelta
import time
from src.api.market_data import MarketData
from src.strategy.engine import StrategyEngine
from src.notifications.notifier import DiscordNotifier
from src.utils.logger import log

def format_dhan_historical(dhan_data):
    """
    Converts Dhan API historical data dictionary into a pandas DataFrame.
    Expected dhan_data format:
    {
        'start_Time': [...],
        'open': [...],
        'high': [...],
        'low': [...],
        'close': [...],
        'volume': [...]
    }
    """
    df = pd.DataFrame(dhan_data)
    # Ensure columns match what StrategyEngine expects
    if 'start_Time' in df.columns:
        # Convert unix timestamps to datetime strings or just datetime objects
        df['time'] = pd.to_datetime(df['start_Time'], unit='s').dt.tz_localize('UTC').dt.tz_convert('Asia/Kolkata').dt.tz_localize(None)
        df = df.drop(columns=['start_Time'])
    elif 'timestamp' in df.columns:
        df['time'] = pd.to_datetime(df['timestamp'], unit='s').dt.tz_localize('UTC').dt.tz_convert('Asia/Kolkata').dt.tz_localize(None)
        df = df.drop(columns=['timestamp'])
        
    # Capitalization fixes just in case
    df = df.rename(columns={'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume'})
    return df

def run_backtest(api_timeframe="5", display_timeframe="5m", days_back=5):
    log.info(f"Starting Backtest for {display_timeframe}...")
    
    # Initialize Market Data client
    md = MarketData()
    engine = StrategyEngine()
    notifier = DiscordNotifier()
    
    symbol = "13" # Nifty 50 Index standard Dhan ID
    exchange_segment = "IDX_I" # Index segment
    
    # We will test over the last days_back days
    to_date = datetime.now().strftime('%Y-%m-%d 15:30:00')
    from_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d 09:15:00')
    
    log.info(f"Fetching data for {symbol} from {from_date} to {to_date}")
    
    raw_data = md.fetch_historical_data(
        security_id=symbol,
        exchange_segment=exchange_segment,
        timeframe=api_timeframe,
        from_date=from_date,
        to_date=to_date
    )
    
    if not raw_data or 'status' in raw_data and raw_data['status'] == 'failure':
        log.warning("API fetch failed. Generating mock data for backtest demonstration...")
        # Generate 1000 candles of mock data
        now = int(time.time())
        raw_data = {
            'start_Time': [now - (1000-i)*300 for i in range(1000)],
            'open': [], 'high': [], 'low': [], 'close': [], 'volume': []
        }
        current_price = 22000.0
        import random
        for _ in range(1000):
            o = current_price
            h = current_price + random.uniform(10, 50)
            l = current_price - random.uniform(10, 50)
            c = o + random.uniform(-30, 30)
            # occasionally make a massive wick (sweep)
            if random.random() < 0.05:
                l = l - 100 # massive lower wick
                c = o + 10  # bullish close
            raw_data['open'].append(o)
            raw_data['high'].append(max(o, h, c))
            raw_data['low'].append(min(o, l, c))
            raw_data['close'].append(c)
            raw_data['volume'].append(random.randint(10000, 500000))
            current_price = c
            
    df = format_dhan_historical(raw_data)
    if df.empty:
        log.error("Formatted DataFrame is empty.")
        return
        
    if display_timeframe == '4h':
        # Resample from 60m to 4h, aligning at 9:15 (09:15 -> 13:15, 13:15 -> 15:30)
        df.set_index('time', inplace=True)
        # Using 4H frequency and offset to align with 09:15
        df = df.resample('4h', offset='15min').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna().reset_index()
        
    # Calculate ATR for SL buffer before iterating
    df['atr'] = ta.atr(df['high'], df['low'], df['close'], length=14)
        
    log.info(f"Loaded {len(df)} candles for backtesting.")
    
    # We need a minimum amount of data to bootstrap the indicators (e.g., 50 for EMA 50)
    bootstrap_size = 50
    if len(df) < bootstrap_size + 1:
        log.error("Not enough data to run backtest.")
        return
        
    # Bootstrap initial state
    initial_df = df.iloc[:bootstrap_size].copy()
    engine.bootstrap_data(symbol, display_timeframe, initial_df)
    
    trades = []
    active_trade = None
    
    # Iterate through the rest of the data
    for index, row in df.iloc[bootstrap_size:].iterrows():
        candle = {
            'time': row['time'],
            'open': row['open'],
            'high': row['high'],
            'low': row['low'],
            'close': row['close'],
            'volume': row['volume']
        }
        
        # Process the candle to update indicators and check for signals
        signal = engine.process_new_candle(symbol, display_timeframe, candle)
        
        # Manage active trade
        if active_trade:
            # Check if SL or Targets hit on this candle
            high = candle['high']
            low = candle['low']
            
            if active_trade['direction'] == 'LONG':
                if low <= active_trade['sl_price']:
                    active_trade['status'] = 'SL_HIT'
                    active_trade['exit_time'] = candle['time']
                    trades.append(active_trade)
                    active_trade = None
                elif high >= active_trade['t2_price']: # Using T2 as full exit for backtest simplicity
                    active_trade['status'] = 'TARGET_HIT'
                    active_trade['exit_time'] = candle['time']
                    trades.append(active_trade)
                    active_trade = None
            else: # SHORT
                if high >= active_trade['sl_price']:
                    active_trade['status'] = 'SL_HIT'
                    active_trade['exit_time'] = candle['time']
                    trades.append(active_trade)
                    active_trade = None
                elif low <= active_trade['t2_price']:
                    active_trade['status'] = 'TARGET_HIT'
                    active_trade['exit_time'] = candle['time']
                    trades.append(active_trade)
                    active_trade = None

        # Enter new trade if we don't have an active one
        if signal and not active_trade:
            signal['entry_time'] = candle['time']
            signal['status'] = 'ACTIVE'
            
            active_trade = signal
            log.info(f"Entered {signal['direction']} at {signal['entry_price']} on {signal['entry_time']}")
            log.info(f"Trade details: {signal}")

    # Print Results
    log.info("\n--- BACKTEST RESULTS ---")
    log.info(f"Total Trades: {len(trades)}")
    
    if len(trades) > 0:
        wins = [t for t in trades if t['status'] == 'TARGET_HIT']
        losses = [t for t in trades if t['status'] == 'SL_HIT']
        
        win_rate = (len(wins) / len(trades)) * 100
        
        log.info(f"Wins: {len(wins)}")
        log.info(f"Losses: {len(losses)}")
        log.info(f"Win Rate (T2 Exit): {win_rate:.2f}%")
        
        # Send to Discord
        notifier.send_backtest_result(
            symbol=symbol,
            timeframe=display_timeframe,
            total_trades=len(trades),
            wins=len(wins),
            losses=len(losses),
            win_rate=win_rate,
            from_date=from_date,
            to_date=to_date,
            trades=trades
        )
        
        log.info("\nTrade Log:")
        for t in trades:
            log.info(f"{t['entry_time']} | {t['direction']} | Entry: {t['entry_price']:.2f} | Result: {t['status']}")
    else:
        log.info("No trades executed during this period.")
        notifier.send_backtest_result(
            symbol=symbol,
            timeframe=display_timeframe,
            total_trades=0,
            wins=0,
            losses=0,
            win_rate=0.0,
            from_date=from_date,
            to_date=to_date,
            trades=[]
        )

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        api_tf = sys.argv[1]
        disp_tf = sys.argv[2] if len(sys.argv) > 2 else "5m"
        days = int(sys.argv[3]) if len(sys.argv) > 3 else 5
        run_backtest(api_timeframe=api_tf, display_timeframe=disp_tf, days_back=days)
    else:
        # Always run 1m and 4h backtests by default
        run_backtest(api_timeframe="1", display_timeframe="1m", days_back=5)
        run_backtest(api_timeframe="60", display_timeframe="4h", days_back=60)