import os
from dotenv import load_dotenv
from client import SouyanBot

load_dotenv()

TOKEN = os.getenv("TOKEN")
INVITE_LINK = os.getenv("INVITE_LINK")

if not TOKEN:
    raise RuntimeError("TOKEN was not found")

bot = SouyanBot()

print(f"Invite Link: {INVITE_LINK}")

bot.run(TOKEN)