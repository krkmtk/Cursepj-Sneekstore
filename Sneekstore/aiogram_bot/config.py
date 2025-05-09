import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Settings:
    bot_token: str

def get_settings() -> Settings:
    return Settings(bot_token=os.getenv("BOT_TOKEN", ""))
