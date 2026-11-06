import logging
import os
import discord

from dotenv import load_dotenv
from client import SouyanBot

load_dotenv()

TOKEN = os.getenv("TOKEN")
INVITE_LINK = os.getenv("INVITE_LINK")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

if not TOKEN:
    raise RuntimeError("TOKEN was not found in the environment.")

if INVITE_LINK:
    logging.info("Invite Link: %s", INVITE_LINK)
else:
    logging.warning("No invite link provided.")

bot = SouyanBot()

if __name__ == "__main__":
    try:
        bot.run(TOKEN, log_handler=None)
    except discord.LoginFailure:
        logging.critical("Invalid Discord bot token.")
    except KeyboardInterrupt:
        logging.info("SkyHelp stopped.")
