import discord
from discord import app_commands
from discord.ext import commands


class PingCommand(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="ping",
        description="Check if the bot is alive."
    )
    async def ping(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000)

        embed = discord.Embed(
            title="🏓 Pong!",
            description="Bot status and websocket latency.",
            color=discord.Color.green()
        )

        if interaction.guild and interaction.guild.icon:
            embed.set_thumbnail(url=interaction.guild.icon.url)

        embed.add_field(name="Latency", value=f"`{latency} ms`", inline=True)
        embed.set_footer(
            text=f"Requested by {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url
        )

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(PingCommand(bot))