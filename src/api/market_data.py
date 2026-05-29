import json
import asyncio
import requests
from dhanhq import dhanhq
from src.utils.config import Config
from src.utils.logger import log

class MarketData:
    def __init__(self):
        self.client_id = Config.DHAN_CLIENT_ID
        self.access_token = Config.DHAN_ACCESS_TOKEN
        self.dhan = dhanhq(
            client_id=self.client_id,
            access_token=self.access_token
        )
        self.subscribers = [] # callbacks for new ticks

    def subscribe(self, callback):
        self.subscribers.append(callback)

    def fetch_historical_data(self, security_id, exchange_segment, timeframe='1', from_date=None, to_date=None):
        """
        Fetches historical intraday data using Dhan V2 API. Timeframe in minutes.
        Dates should be in 'YYYY-MM-DD HH:mm:ss' format.
        """
        try:
            log.info(f"Fetching historical data for {security_id} via V2 API")
            url = "https://api.dhan.co/v2/charts/intraday"
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "access-token": self.access_token,
                "client-id": self.client_id
            }
            payload = {
                "securityId": str(security_id),
                "exchangeSegment": exchange_segment,
                "instrument": "INDEX", # or pass this as parameter if needed
                "interval": str(timeframe),
                "oi": False,
                "fromDate": from_date,
                "toDate": to_date
            }
            
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') == 'success':
                return data.get('data')
            else:
                log.error(f"Failed to fetch historical data: {data}")
                return data # Return the failure response so backtest can generate mock data
        except requests.exceptions.RequestException as e:
            log.error(f"Error fetching historical data: {e}")
            return {"status": "failure", "remarks": str(e)}

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
