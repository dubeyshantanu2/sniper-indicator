import requests
from src.utils.config import Config
from src.utils.logger import log

class DiscordNotifier:
    def __init__(self):
        self.webhook_url = Config.DISCORD_WEBHOOK_URL

    def _send_embed(self, embed: dict):
        if not self.webhook_url:
            log.warning("Discord webhook URL not configured. Skipping notification.")
            return

        payload = {"embeds": [embed]}
        try:
            response = requests.post(self.webhook_url, json=payload)
            response.raise_for_status()
            log.debug(f"Successfully sent Discord notification.")
        except requests.exceptions.RequestException as e:
            log.error(f"Failed to send Discord notification: {e}")

    def send_startup_briefing(self, active_trades: list):
        if not active_trades:
            description = "No active trades at startup."
        else:
            description = "\n".join([
                f"**{t['trade_id']}**: {t['symbol']} {t['timeframe']} {t['direction']} @ {t['entry_price']} (Status: {t['status']})"
                for t in active_trades
            ])

        embed = {
            "title": "🟢 Sniper Trading Assistant Started",
            "description": description,
            "color": 3066993, # Green
        }
        self._send_embed(embed)

    def send_new_signal(self, trade_data: dict):
        color = 3066993 if trade_data['direction'] == 'LONG' else 15158332 # Green / Red
        
        embed = {
            "title": f"🚨 NEW SIGNAL: {trade_data['symbol']} {trade_data['timeframe']}",
            "description": f"**Direction:** {trade_data['direction']}\n**Trade ID:** {trade_data['trade_id']}",
            "color": color,
            "fields": [
                {"name": "Entry Price", "value": str(trade_data['entry_price']), "inline": True},
                {"name": "Stop Loss", "value": str(trade_data['sl_price']), "inline": True},
                {"name": "Suggested Strike", "value": trade_data['suggested_strike'], "inline": False},
                {"name": "Target 1 (1:2)", "value": str(trade_data['t1_price']), "inline": True},
                {"name": "Target 2 (1:3)", "value": str(trade_data['t2_price']), "inline": True},
                {"name": "Target 3 (1:5)", "value": str(trade_data['t3_price']), "inline": True}
            ]
        }
        self._send_embed(embed)

    def send_target_update(self, trade_data: dict, target_level: str, message: str):
        embed = {
            "title": f"🎯 TARGET ACHIEVED: {trade_data['symbol']} - {target_level}",
            "description": f"**Trade ID:** {trade_data['trade_id']}\n{message}",
            "color": 15844367, # Gold
            "fields": [
                {"name": "New SL Price", "value": str(trade_data['sl_price']), "inline": True}
            ]
        }
        self._send_embed(embed)

    def send_sl_hit(self, trade_data: dict):
        embed = {
            "title": f"🛑 STOP LOSS HIT: {trade_data['symbol']}",
            "description": f"**Trade ID:** {trade_data['trade_id']}\nStop loss was triggered.",
            "color": 15158332, # Red
        }
        self._send_embed(embed)
