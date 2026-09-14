import discord
from discord import app_commands
from discord.ext import commands

class Purge(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="purge", description="Deletes a specified number of messages.")
    @app_commands.checks.has_permissions(manage_messages=True)
    @app_commands.describe(amount="The number of messages to delete (a number or 'all')")
    async def purge(self, interaction: discord.Interaction, amount: str):
        if not interaction.guild:
            return await interaction.response.send_message(
                "> ## ❌ This command can only be used inside a server!", 
                ephemeral=True
            )

        purge_limit = None

        if amount.lower() != "all":
            if not amount.isdigit() or int(amount) <= 0:
                return await interaction.response.send_message(
                    "> ## Make sure to input a valid positive number or 'all'!", 
                    ephemeral=True
                )
            purge_limit = int(amount)
        
        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=purge_limit)
        
        embed = discord.Embed(
            title="🧹 Messages Purged",
            description=f"Successfully deleted `{len(deleted)}` messages from this channel.",
            color=discord.Color.green()
        )
        embed.add_field(name="Target Amount", value=f"`{amount}`", inline=True)
        embed.set_footer(
            text=f"Requested by {interaction.user.name}", 
            icon_url=interaction.user.display_avatar.url
        )
        
        await interaction.followup.send(embed=embed, ephemeral=True)

    @purge.error
    async def purge_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):   
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message(
                "> ## ❌ You do not have permission to use this command! (Requires `Manage Messages`)", 
                ephemeral=True
            )

async def setup(bot: commands.Bot):
    await bot.add_cog(Purge(bot))
