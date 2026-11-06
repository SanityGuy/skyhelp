
import logging
from pathlib import Path

import discord
from discord.ext import commands


class SouyanBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        super().__init__(command_prefix=[], intents=intents)

    async def setup_hook(self):
        folders = ["listeners", "commands"]

        for folder in folders:
            path = Path(folder)

            if not path.exists():
                logging.warning("Extension folder '%s' does not exist.", folder)
                continue

            for file in sorted(path.glob("*.py")):
                if file.stem.startswith("_"):
                    continue

                extension = f"{folder}.{file.stem}"

                try:
                    await self.load_extension(extension)
                    logging.info("Loaded extension: %s", extension)
                except commands.ExtensionError:
                    logging.exception("Failed to load extension: %s", extension)

        try:
            synced = await self.tree.sync()
            logging.info("Successfully synchronized %s slash commands.", len(synced))
        except discord.HTTPException:
            logging.exception("Failed to synchronize slash commands.")

    async def on_error(self, event: str, *args, **kwargs):
        logging.exception("Unhandled error in event: %s", event)

    async def close(self):
        logging.info("Shutting down SkyHelp...")
        await super().close()
