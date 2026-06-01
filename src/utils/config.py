import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Dhan API
    DHAN_CLIENT_ID = os.getenv("DHAN_CLIENT_ID")
    DHAN_ACCESS_TOKEN = os.getenv("DHAN_ACCESS_TOKEN")
    
    # Supabase
    SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
    SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()
    
    # Discord
    DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
    DISCORD_HEALTH_WEBHOOK_URL = os.getenv("DISCORD_HEALTH_WEBHOOK_URL")

    @classmethod
    def validate(cls):
        missing = []
        for attr in ['DHAN_CLIENT_ID', 'DHAN_ACCESS_TOKEN', 'SUPABASE_URL', 'SUPABASE_KEY', 'DISCORD_WEBHOOK_URL']:
            if not getattr(cls, attr):
                missing.append(attr)
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
