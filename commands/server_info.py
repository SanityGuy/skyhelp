import discord
from discord import app_commands
from discord.ext import commands

class ServerInfo(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="serverinfo",
        description="View the server's current information"
    )
    async def serverinfo(self, interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        await interaction.response.defer()
        server = interaction.guild

        embed = discord.Embed(
            title="🖥️ Server Information",
            description=f"Current information about **{server.name}** and its content.",
            color=discord.Color.blue()
        )
        
        if server.icon:
            embed.set_thumbnail(url=server.icon.url)

        embed.add_field(name="Server Name", value=server.name, inline=True)
        embed.add_field(name="Server ID", value=str(server.id), inline=True)
        embed.add_field(name="Server Owner", value=server.owner.mention if server.owner else "Unknown", inline=True)

        embed.add_field(name="Member Count", value=str(server.member_count), inline=True)
        embed.add_field(name="Roles Count", value=str(len(server.roles)), inline=True)

        created_timestamp = f"<t:{int(server.created_at.timestamp())}:R>"
        embed.add_field(name="Server Created", value=created_timestamp, inline=True)

        embed.set_footer(
            text=f"Requested by {interaction.user.name}", 
            icon_url=interaction.user.display_avatar.url
        )

        await interaction.followup.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(ServerInfo(bot))