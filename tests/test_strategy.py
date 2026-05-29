import pytest
import pandas as pd
from src.strategy.engine import StrategyEngine

@pytest.fixture
def strategy_engine():
    return StrategyEngine()

def test_long_sweep_signal(strategy_engine):
    """
    Test that a valid LONG sweep signal is generated when:
    - Candle touches EMA/VWAP
    - Candle is green (close > open)
    - Lower wick >= body * 1.5
    - Upper wick <= body * 0.6
    - Volume > Vol SMA * 1.1
    """
    symbol = "NIFTY50"
    timeframe = "1m"
    
    # Create 25 dummy candles to bootstrap EMA (14) and Vol SMA (20)
    # We will set a base price around 22000
    base_data = []
    for i in range(25):
        base_data.append({
            'time': f'2024-05-29T10:00:{i:02d}Z',
            'open': 22000.0,
            'high': 22010.0,
            'low': 21990.0,
            'close': 22005.0,
            'volume': 1000
        })
    
    df = pd.DataFrame(base_data)
    strategy_engine.bootstrap_data(symbol, timeframe, df)
    
    # The last calculated EMA should be around 22000-22005.
    # Volume SMA should be 1000.
    
    # Generate a trigger candle that fits LONG criteria.
    # EMA/VWAP is around 22005.
    # Open: 22010, Close: 22020 (Body = 10, Green)
    # Low: 21980 (Lower wick = 22010 - 21980 = 30) -> 30 >= 10 * 1.5 (True)
    # High: 22022 (Upper wick = 22022 - 22020 = 2) -> 2 <= 10 * 0.6 (True)
    # Touches EMA: Low is 21980, High is 22022, EMA is ~22005 (True)
    # Volume = 1200 (1200 >= 1000 * 1.1) (True)
    
    trigger_candle = {
        'time': '2024-05-29T10:00:25Z',
        'open': 22010.0,
        'high': 22022.0,
        'low': 21980.0,
        'close': 22020.0,
        'volume': 1200
    }
    
    signal = strategy_engine.process_new_candle(symbol, timeframe, trigger_candle)
    
    assert signal is not None
    assert signal['direction'] == 'LONG'
    assert signal['entry_price'] == 22020.0
    assert signal['sl_price'] == 21980.0
    
    risk = 22020.0 - 21980.0 # 40
    assert signal['t1_price'] == 22020.0 + (risk * 2)
    assert signal['t2_price'] == 22020.0 + (risk * 3)
    assert signal['t3_price'] == 22020.0 + (risk * 5)
    
def test_short_sweep_signal(strategy_engine):
    """
    Test that a valid SHORT sweep signal is generated.
    """
    symbol = "BANKNIFTY"
    timeframe = "1m"
    
    base_data = []
    for i in range(25):
        base_data.append({
            'time': f'2024-05-29T10:00:{i:02d}Z',
            'open': 48000.0,
            'high': 48020.0,
            'low': 47980.0,
            'close': 48000.0, # Flat candles
            'volume': 1000
        })
    
    df = pd.DataFrame(base_data)
    strategy_engine.bootstrap_data(symbol, timeframe, df)
    
    # EMA/VWAP around 48000. Vol SMA = 1000.
    
    # Trigger Candle for SHORT:
    # Open: 47990, Close: 47970 (Body = 20, Red)
    # High: 48040 (Upper wick = 48040 - 47990 = 50) -> 50 >= 20 * 1.5 (True)
    # Low: 47960 (Lower wick = 47970 - 47960 = 10) -> 10 <= 20 * 0.6 (True)
    # Touches EMA: Low 47960, High 48040, EMA ~ 48000 (True)
    # Volume: 1500 (1500 >= 1000 * 1.1) (True)
    
    trigger_candle = {
        'time': '2024-05-29T10:00:25Z',
        'open': 47990.0,
        'high': 48040.0,
        'low': 47960.0,
        'close': 47970.0,
        'volume': 1500
    }
    
    signal = strategy_engine.process_new_candle(symbol, timeframe, trigger_candle)
    
    assert signal is not None
    assert signal['direction'] == 'SHORT'
    assert signal['entry_price'] == 47970.0
    assert signal['sl_price'] == 48040.0
    
def test_no_signal_due_to_volume(strategy_engine):
    """
    Test that a structurally perfect sweep is ignored if volume is low.
    """
    symbol = "NIFTY50"
    timeframe = "1m"
    
    base_data = []
    for i in range(25):
        base_data.append({
            'time': f'2024-05-29T10:00:{i:02d}Z',
            'open': 22000.0,
            'high': 22010.0,
            'low': 21990.0,
            'close': 22005.0,
            'volume': 1000
        })
    
    df = pd.DataFrame(base_data)
    strategy_engine.bootstrap_data(symbol, timeframe, df)
    
    # Same as LONG test, but with low volume (1000, not >= 1100)
    trigger_candle = {
        'time': '2024-05-29T10:00:25Z',
        'open': 22010.0,
        'high': 22022.0,
        'low': 21980.0,
        'close': 22020.0,
        'volume': 1000 # Fails volume check
    }
    
    signal = strategy_engine.process_new_candle(symbol, timeframe, trigger_candle)
    
    assert signal is None
