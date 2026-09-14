import os
from dotenv import load_dotenv
from client import SouyanBot

load_dotenv()

TOKEN = os.getenv("TOKEN")

if not TOKEN:
    raise RuntimeError("TOKEN was not found")

bot = SouyanBot()
bot.run(TOKEN)