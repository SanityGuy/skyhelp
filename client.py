import os
import discord
from discord.ext import commands

class SouyanBot(commands.Bot):

    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        super().__init__(command_prefix=[], intents=intents)

    async def setup_hook(self):
        folders = ["commands", "listeners"]

        for folder in folders:
            if os.path.exists(folder):
                for file in os.listdir(folder):
                    if file.endswith(".py") and not file.startswith("__"):
                        extension = f"{folder}.{file[:-3]}"
                        print(f"Loading {extension}...")
                        await self.load_extension(extension)

        synced = await self.tree.sync()
        print(f"Synced {len(synced)} commands.")