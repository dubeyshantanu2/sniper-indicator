import json
import asyncio
from dhanhq import dhanhq
from src.utils.config import Config
from src.utils.logger import log

class MarketData:
    def __init__(self):
        self.dhan = dhanhq(
            client_id=Config.DHAN_CLIENT_ID,
            access_token=Config.DHAN_ACCESS_TOKEN
        )
        self.subscribers = [] # callbacks for new ticks

    def subscribe(self, callback):
        self.subscribers.append(callback)

    def fetch_historical_data(self, security_id, exchange_segment, timeframe='1', from_date=None, to_date=None):
        """
        Fetches historical intraday data. Timeframe in minutes.
        """
        try:
            # Note: The dhanhq library requires dates in YYYY-MM-DD format
            log.info(f"Fetching historical data for {security_id}")
            response = self.dhan.historical_minute_charts(
                symbol=security_id,
                exchange_segment=exchange_segment,
                instrument_type='INDEX',
                expiry_code=0,
                from_date=from_date,
                to_date=to_date
            )
            if response['status'] == 'success':
                return response['data']
            else:
                log.error(f"Failed to fetch historical data: {response}")
                return None
        except Exception as e:
            log.error(f"Error fetching historical data: {e}")
            return None

    async def start_websocket(self, instruments):
        """
        Starts the websocket connection. This is a simplified mock representation,
        as the actual dhanhq websocket client (marketfeed) requires a slightly
        different asynchronous setup with its own custom handlers.
        """
        log.info("Starting Dhan WebSocket connection...")
        # In a real implementation using dhanhq.marketfeed:
        # 1. Initialize Feed client
        # 2. Assign on_message callback
        # 3. Subscribe to instruments (e.g., NIFTY 50)
        # 4. run_forever()
        
        # Here we mock the continuous feed for architectural completeness
        # since we can't establish a real Dhan WS without live credentials
        while True:
            # Simulate a tick received
            # tick = await self._mock_receive()
            # for sub in self.subscribers:
            #     sub(tick)
            await asyncio.sleep(1)

    def _notify_subscribers(self, tick_data):
        for sub in self.subscribers:
            sub(tick_data)
