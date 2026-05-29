import asyncio
import pandas as pd
from src.utils.config import Config
from src.utils.logger import log
from src.database.trade_manager import TradeManager
from src.notifications.notifier import DiscordNotifier
from src.api.market_data import MarketData
from src.strategy.engine import StrategyEngine

class SniperAssistant:
    def __init__(self):
        self.trade_manager = TradeManager()
        self.notifier = DiscordNotifier()
        self.market_data = MarketData()
        self.strategy_engine = StrategyEngine()
        
        self.active_trades_cache = []

    async def startup_routine(self):
        log.info("Starting up Sniper Trading Assistant...")
        Config.validate()
        
        # 1. Fetch Open Trades
        self.active_trades_cache = self.trade_manager.get_open_trades()
        self.notifier.send_startup_briefing(self.active_trades_cache)
        
        # 2. Bootstrap Historical Data (Mock implementation for setup completeness)
        # In reality, loop through required instruments and timeframes.
        log.info("Bootstrapping historical data...")
        # dummy_df = pd.DataFrame(columns=['time', 'open', 'high', 'low', 'close', 'volume'])
        # self.strategy_engine.bootstrap_data("NIFTY50", "1m", dummy_df)
        
    def _evaluate_active_trades(self, current_price: float, symbol: str):
        for trade in self.active_trades_cache:
            if trade['symbol'] != symbol:
                continue
                
            # simplified evaluation for both Long and Short
            direction = trade['direction']
            status = trade['status']
            
            if status == 'Closed':
                continue
                
            sl = trade['sl_price']
            t1 = trade['t1_price']
            t2 = trade['t2_price']
            t3 = trade['t3_price']
            
            # Check Stop Loss
            if (direction == 'LONG' and current_price <= sl) or (direction == 'SHORT' and current_price >= sl):
                self.trade_manager.update_trade_status(trade['id'], 'Closed', sl)
                self.notifier.send_sl_hit(trade)
                trade['status'] = 'Closed'
                continue
                
            # Check Targets
            if direction == 'LONG':
                if status == 'Active' and current_price >= t1:
                    new_sl = trade['entry_price']
                    self.trade_manager.update_trade_status(trade['id'], 'T1_Hit', new_sl)
                    self.notifier.send_target_update(trade, "Target 1 Hit", "Close 40%, Moved SL to Entry")
                    trade['status'] = 'T1_Hit'
                    trade['sl_price'] = new_sl
                elif status == 'T1_Hit' and current_price >= t2:
                    new_sl = t1
                    self.trade_manager.update_trade_status(trade['id'], 'T2_Hit', new_sl)
                    self.notifier.send_target_update(trade, "Target 2 Hit", "Close 40%, Moved SL to T1")
                    trade['status'] = 'T2_Hit'
                    trade['sl_price'] = new_sl
                elif status == 'T2_Hit' and current_price >= t3:
                    self.trade_manager.update_trade_status(trade['id'], 'Closed')
                    self.notifier.send_target_update(trade, "Target 3 Hit", "Close remaining 20%. Trade complete.")
                    trade['status'] = 'Closed'
            else: # SHORT
                if status == 'Active' and current_price <= t1:
                    new_sl = trade['entry_price']
                    self.trade_manager.update_trade_status(trade['id'], 'T1_Hit', new_sl)
                    self.notifier.send_target_update(trade, "Target 1 Hit", "Close 40%, Moved SL to Entry")
                    trade['status'] = 'T1_Hit'
                    trade['sl_price'] = new_sl
                elif status == 'T1_Hit' and current_price <= t2:
                    new_sl = t1
                    self.trade_manager.update_trade_status(trade['id'], 'T2_Hit', new_sl)
                    self.notifier.send_target_update(trade, "Target 2 Hit", "Close 40%, Moved SL to T1")
                    trade['status'] = 'T2_Hit'
                    trade['sl_price'] = new_sl
                elif status == 'T2_Hit' and current_price <= t3:
                    self.trade_manager.update_trade_status(trade['id'], 'Closed')
                    self.notifier.send_target_update(trade, "Target 3 Hit", "Close remaining 20%. Trade complete.")
                    trade['status'] = 'Closed'

    def on_new_tick(self, tick_data: dict):
        """Callback for WebSocket"""
        symbol = tick_data.get('symbol')
        current_price = tick_data.get('ltp') # Last Traded Price
        
        # 1. Evaluate Active Trades for targets/SL
        if current_price:
            self._evaluate_active_trades(current_price, symbol)
            
        # 2. In a real scenario, aggregate ticks into candles here.
        # For simulation, we assume `tick_data` represents a completed candle.
        if tick_data.get('is_candle_complete'):
            signal_data = self.strategy_engine.process_new_candle(
                symbol, 
                tick_data.get('timeframe'), 
                tick_data.get('candle')
            )
            
            if signal_data:
                # Save to DB
                new_trade = self.trade_manager.create_trade(signal_data)
                if new_trade:
                    # Notify
                    self.notifier.send_new_signal(new_trade)
                    # Add to tracking
                    self.active_trades_cache.append(new_trade)

    async def run(self):
        await self.startup_routine()
        
        self.market_data.subscribe(self.on_new_tick)
        
        # Start WS loop
        instruments = ["NIFTY50", "BANKNIFTY"]
        await self.market_data.start_websocket(instruments)

if __name__ == "__main__":
    assistant = SniperAssistant()
    try:
        asyncio.run(assistant.run())
    except KeyboardInterrupt:
        log.info("Shutting down...")
