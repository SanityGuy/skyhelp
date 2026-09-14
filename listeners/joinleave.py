import discord
from discord.ext import commands

class JoinLeave(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.bot:
            return

        await member.send(f"> ## Welcome to the server, {member.mention}!")

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        if member.bot:
            return

        await member.send(f"> ## Goodbye, {member.mention}!")

async def setup(bot: commands.Bot):
    await bot.add_cog(JoinLeave(bot))