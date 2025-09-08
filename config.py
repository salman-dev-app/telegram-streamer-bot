import os
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv("API_ID", 0))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
MONGO_URI = os.getenv("MONGO_URI", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", 0))
WEB_SERVER_URL = os.getenv("WEB_SERVER_URL", "https://your-app-name.koyeb.app")
