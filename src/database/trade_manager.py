import uuid
import random
from datetime import datetime
from zoneinfo import ZoneInfo
from supabase import create_client, Client
from src.utils.config import Config
from src.utils.logger import log

class TradeManager:
    def __init__(self):
        self.supabase: Client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
        self.table_name = "active_trades"

    def _generate_trade_id(self):
        return str(random.randint(1000, 9999))

    def get_open_trades(self):
        try:
            response = self.supabase.table(self.table_name).select("*").neq("status", "Closed").execute()
            return response.data
        except Exception as e:
            log.error(f"Error fetching open trades: {e}")
            return []

    def create_trade(self, trade_data: dict):
        trade_id = self._generate_trade_id()
        now = datetime.now(ZoneInfo('Asia/Kolkata')).isoformat()
        
        record = {
            "id": str(uuid.uuid4()),
            "trade_id": trade_id,
            "symbol": trade_data['symbol'],
            "timeframe": trade_data['timeframe'],
            "direction": trade_data['direction'],
            "entry_price": trade_data['entry_price'],
            "sl_price": trade_data['sl_price'],
            "t1_price": trade_data['t1_price'],
            "t2_price": trade_data['t2_price'],
            "t3_price": trade_data['t3_price'],
            "suggested_strike": trade_data.get('suggested_strike', ''),
            "status": "Active",
            "created_at": now,
            "updated_at": now
        }
        
        try:
            response = self.supabase.table(self.table_name).insert(record).execute()
            log.info(f"Created new trade in DB: {trade_id}")
            return response.data[0]
        except Exception as e:
            log.error(f"Error creating trade: {e}")
            return None

    def update_trade_status(self, db_id: str, new_status: str, new_sl: float = None):
        now = datetime.now(ZoneInfo('Asia/Kolkata')).isoformat()
        update_data = {
            "status": new_status,
            "updated_at": now
        }
        if new_sl is not None:
            update_data["sl_price"] = new_sl
            
        try:
            response = self.supabase.table(self.table_name).update(update_data).eq("id", db_id).execute()
            log.info(f"Updated trade {db_id} status to {new_status}")
            return response.data[0] if response.data else None
        except Exception as e:
            log.error(f"Error updating trade {db_id}: {e}")
            return None
