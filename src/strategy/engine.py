import pandas as pd
import pandas_ta as ta
import math
from src.utils.logger import log

class StrategyEngine:
    def __init__(self):
        # Configuration matches indicator.pine
        self.ema_fast_len = 14
        self.vol_ma_len = 20
        self.vol_multiplier = 1.1
        self.wick_multiplier = 1.5
        self.opp_wick_max = 0.6
        
        # State: Dictionary mapping symbol to a dictionary of timeframe to DataFrame
        self.dataframes = {}

    def bootstrap_data(self, symbol: str, timeframe: str, df: pd.DataFrame):
        """
        Initializes the DataFrame for a given symbol and timeframe.
        df should have columns: ['time', 'open', 'high', 'low', 'close', 'volume']
        """
        if symbol not in self.dataframes:
            self.dataframes[symbol] = {}
        
        self.dataframes[symbol][timeframe] = df.copy()
        log.info(f"Bootstrapped data for {symbol} - {timeframe} with {len(df)} candles.")
        self._calculate_indicators(symbol, timeframe)

    def _calculate_indicators(self, symbol: str, timeframe: str):
        df = self.dataframes[symbol][timeframe]
        
        if len(df) < max(self.ema_fast_len, self.vol_ma_len):
            return # Not enough data
            
        # Moving Averages and VWAP
        df['ema_fast'] = ta.ema(df['close'], length=self.ema_fast_len)
        
        # VWAP usually requires high, low, close, volume. Simple approximation if no cumulative session data
        # pandas-ta vwap requires datetime index or typical price
        df['datetime'] = pd.to_datetime(df['time'])
        df.set_index('datetime', inplace=True)
        df.ta.vwap(append=True) 
        df.reset_index(inplace=True)
        
        # Volume SMA
        df['vol_sma'] = ta.sma(df['volume'], length=self.vol_ma_len)

    def process_new_candle(self, symbol: str, timeframe: str, candle: dict):
        """
        candle: dict with keys 'time', 'open', 'high', 'low', 'close', 'volume'
        Returns a signal dict if generated, else None.
        """
        if symbol not in self.dataframes or timeframe not in self.dataframes[symbol]:
            log.warning(f"Dataframe not initialized for {symbol} - {timeframe}")
            return None

        df = self.dataframes[symbol][timeframe]
        
        # Append new candle
        new_row = pd.DataFrame([candle])
        df = pd.concat([df, new_row], ignore_index=True)
        
        # Keep window size reasonable (e.g., 500 max)
        if len(df) > 500:
            df = df.iloc[-500:].reset_index(drop=True)
            
        self.dataframes[symbol][timeframe] = df
        
        # Recalculate indicators for the latest bars (optimization can be done later)
        self._calculate_indicators(symbol, timeframe)
        
        return self._check_signal(symbol, timeframe, df.iloc[-1])

    def _check_signal(self, symbol: str, timeframe: str, current_bar: pd.Series):
        if pd.isna(current_bar.get('ema_fast')) or pd.isna(current_bar.get('VWAP_D')):
            return None # Not enough history
            
        open_p, high_p, low_p, close_p, vol = current_bar['open'], current_bar['high'], current_bar['low'], current_bar['close'], current_bar['volume']
        ema_fast = current_bar['ema_fast']
        vwap_val = current_bar['VWAP_D']
        vol_sma = current_bar['vol_sma']
        
        # Anatomy of the Candle
        candle_body = max(abs(close_p - open_p), 0.05) # Prevent divide by zero issues with 0 tick
        wick_upper = high_p - max(close_p, open_p)
        wick_lower = min(close_p, open_p) - low_p
        
        # Trigger Conditions
        touch_fast_ema = low_p <= ema_fast and high_p >= ema_fast
        touch_vwap = low_p <= vwap_val and high_p >= vwap_val
        touch_key_level = touch_fast_ema or touch_vwap
        
        vol_condition = vol >= (vol_sma * self.vol_multiplier)
        
        signal = None
        
        # Long Entry Sweep
        long_sweep_structure = wick_lower >= (candle_body * self.wick_multiplier) and wick_upper <= (candle_body * self.opp_wick_max)
        if long_sweep_structure and touch_key_level and close_p > open_p and vol_condition:
            signal = 'LONG'
            sl = low_p
            
        # Short Entry Sweep
        short_sweep_structure = wick_upper >= (candle_body * self.wick_multiplier) and wick_lower <= (candle_body * self.opp_wick_max)
        if short_sweep_structure and touch_key_level and close_p < open_p and vol_condition:
            signal = 'SHORT'
            sl = high_p
            
        if signal:
            entry = close_p
            risk = abs(entry - sl)
            
            # Suggest strike (simplified logic, round to nearest 100 for Nifty, just an example)
            # In real scenario, needs instrument specific offset
            suggested_strike = str(int(round(entry / 100.0)) * 100) + (" CE" if signal == "LONG" else " PE")

            return {
                "symbol": symbol,
                "timeframe": timeframe,
                "direction": signal,
                "entry_price": entry,
                "sl_price": sl,
                "t1_price": entry + (risk * 2) if signal == 'LONG' else entry - (risk * 2),
                "t2_price": entry + (risk * 3) if signal == 'LONG' else entry - (risk * 3),
                "t3_price": entry + (risk * 5) if signal == 'LONG' else entry - (risk * 5),
                "suggested_strike": suggested_strike
            }
            
        return None
