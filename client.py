import os
import discord
from discord.ext import commands


class SouyanBot(commands.Bot):

    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = False

        super().__init__(
            command_prefix=[],
            intents=intents
        )

    async def setup_hook(self):
        folders = ["commands", "listeners"]
        
        for folder in folders:
            if os.path.exists(folder):
                for file in os.listdir(folder):
                    if file.endswith(".py") and not file.startswith("__"):
                        await self.load_extension(f"{folder}.{file[:-3]}")

        await self.tree.sync()