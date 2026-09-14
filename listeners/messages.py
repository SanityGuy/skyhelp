import os
import discord
from discord.ext import commands


class MessagesEvent(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.swear_words = self.load_swear_words()

    def load_swear_words(self) -> list[str]:
        file_path = os.path.join("listeners", "swear_words.txt")
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                return [line.strip().lower() for line in f if line.strip()]
        return []

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        content_words = message.content.lower().split()
        if any(word in self.swear_words for word in content_words):
            try:
                await message.delete()
            except discord.NotFound:
                pass

            try:
                await message.author.send("Your message was deleted because it contained a swear word.")
            except discord.Forbidden:
                await message.channel.send("Swear words are not allowed in this server!", delete_after=5)



async def setup(bot: commands.Bot):
    await bot.add_cog(MessagesEvent(bot))