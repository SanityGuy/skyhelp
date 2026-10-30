import discord
from discord import app_commands
from discord.ext import commands

class ServerInfoCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="serverinfo",
        description="View the servers current information"
    )
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.defer()
        server = interaction.guild

        embed = discord.Embed(
            "🖥️ Server Information",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=server.icon.url)
        embed.add_field(name="Title", value={server.name}, inline=True)
        embed.add_field(name="Server ID", value={server.id}, inline=True)
        embed.add_field(name="Member Count", value={server.member_count}, inline=True)
        embed.add_field(name="Roles Count", value={server.roles.count}, inline=True)

        created_timestamp = f"<t:{int(server.created_at.timestamp)}:R>"
        embed.add_field(name="Server Created", value=created_timestamp, inline=True)

        embed.set_footer(
                    text=f"Requested by {interaction.user.name}", 
                    icon_url=interaction.user.display_avatar.url
                )

        await interaction.followup.send(embed=embed)