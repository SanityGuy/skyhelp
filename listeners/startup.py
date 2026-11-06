
import logging
import random

import discord
from discord.ext import commands, tasks


class StartupListener(commands.Cog):
    STATUS_LIST = [
        discord.Game(name="SkyHelp is made by SouyanDev 🌌"),
        discord.Activity(type=discord.ActivityType.watching, name="Watching over the SkyFlix Server"),
        discord.Activity(type=discord.ActivityType.listening, name="Listening to your commands"),
        discord.Game(name="Try some minigames! /coinflip"),
        discord.Activity(type=discord.ActivityType.watching, name="Building the SkyFlix Network"),
    ]

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.notified = False
        self.change_status.start()

    @tasks.loop(seconds=20)
    async def change_status(self):
        activity = random.choice(self.STATUS_LIST)
        await self.bot.change_presence(activity=activity)
        self.change_status.change_interval(seconds=random.randint(15, 30))

    @change_status.before_loop
    async def before_status_change(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info("Logged in as %s (ID: %s)", self.bot.user, self.bot.user.id)

        if self.notified:
            return

        self.notified = True

        try:
            app_info = await self.bot.application_info()
            owner = app_info.owner

            if owner:
                await owner.send(f"🤖 **{self.bot.user.name}** is now online and ready!")
                logging.info("Startup DM sent to %s", owner)

        except discord.Forbidden:
            logging.warning("Could not send startup DM. Owner DMs are disabled.")
        except discord.HTTPException:
            logging.exception("Failed to send startup DM")

    def cog_unload(self):
        self.change_status.cancel()


async def setup(bot: commands.Bot):
    await bot.add_cog(StartupListener(bot))
