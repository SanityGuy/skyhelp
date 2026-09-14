import discord
import random
from discord.ext import commands


class DMMessageListener(commands.Cog):

    greetings = ["hello", "hi", "hey", "sup", "what's up", "whats up"]

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if message.channel.type == discord.ChannelType.private:
            for greeting in self.greetings:
                if greeting in message.content.lower():
                    random_greeting = random.choice(self.greetings)
                    await message.author.send(f"{random_greeting}, {message.author.mention}!")


async def setup(bot: commands.Bot):
    await bot.add_cog(DMMessageListener(bot))