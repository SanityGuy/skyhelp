import discord
from discord.ext import commands


class StartupListener(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

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

async def setup(bot: commands.Bot):
    await bot.add_cog(StartupListener(bot))