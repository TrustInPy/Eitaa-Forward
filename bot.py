import os
import json
from dotenv import load_dotenv
from telethon.sync import TelegramClient

load_dotenv()
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")

proxies = {
    "http":"http://127.0.0.1:1071",
    "https":"http://127.0.0.1:1071",
}

client = TelegramClient("TelBot", API_ID, API_HASH, proxy=("socks5", "127.0.0.1", 10809, True))
client.parse_mode = "md"
