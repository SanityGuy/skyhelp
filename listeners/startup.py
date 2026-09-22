import discord
from discord.ext import commands, tasks
import random


class StartupListener(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.change_status.start()

    STATUS_LIST = [
        discord.Game(name="SkyHelp is made by SouyanDev🌌"),
        discord.Activity(type=discord.ActivityType.watching, name="Watching over the SkyFlix Server"),
        discord.Activity(type=discord.ActivityType.listening, name="Listening to your commands"),
        discord.Game(name="Try some minigames! /coinflip")
    ]

    @tasks.loop(seconds=20)
    async def change_status(self):
        await self.bot.wait_until_ready()
        
        new_activity = random.choice(self.STATUS_LIST)
        await self.bot.change_presence(activity=new_activity)

        next_delay = random.randint(15, 30)
        self.change_status.change_interval(seconds=next_delay)

        print(f"Current status: {self.bot.status}")
        print(f"Status changed to {new_activity.name} in {next_delay} seconds")

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Logged in as {self.bot.user} (ID: {self.bot.user.id})")

        try:
            app_info = await self.bot.application_info()
            owner = app_info.owner

            await owner.send(f"🤖 **{self.bot.user.name}** is now online and ready!")
            print(f"Startup DM successfully sent to {owner.name}!")

        except discord.Forbidden:
            print("Failed to send DM, Owner might have DMs disabled.")
        except Exception as e:
            print(f"Startup DM failed to send: {e}")

    def cog_unload(self):
        self.change_status.cancel()

async def setup(bot: commands.Bot):
    await bot.add_cog(StartupListener(bot))
