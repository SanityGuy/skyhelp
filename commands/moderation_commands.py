import discord
from discord.ext import commands
from discord.ext.commands import has_permissions
from discord import app_commands

class ConfirmView(discord.ui.View):
    def __init__(self, author: discord.Member, action):
        super().__init__(timeout=30)
        self.author = author
        self.action = action

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("This isn't your confirmation.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.action(interaction)
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Action cancelled.", embed=None, view=None)
        self.stop()


class ModerationCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ban", description="Bans a user from the server")
    @has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, user: discord.Member, reason: str | None = None):
        if interaction.guild is None:
            await interaction.response.send_message("This command can only be used in a server!", ephemeral=True)
            return

        if user.id == interaction.user.id:
            await interaction.response.send_message("You cannot ban yourself!", ephemeral=True)
            return

        if user == interaction.guild.owner:
            await interaction.response.send_message("You cannot ban the server owner!", ephemeral=True)
            return

        if interaction.user != interaction.guild.owner and user.top_role >= interaction.user.top_role:
            await interaction.response.send_message("You cannot ban a member with an equal or higher role than you.", ephemeral=True)
            return

        if interaction.guild.me.top_role <= user.top_role:
            await interaction.response.send_message("I cannot ban this user because their role is equal to or higher than mine.", ephemeral=True)
            return

        banreason = reason or "No reason provided"

        async def banUser(interaction: discord.Interaction):
            try:
                await user.ban(reason=banreason)

                try:
                    await user.send(f"You have been banned from {interaction.guild.name} by {interaction.user.display_name}.\nReason: {banreason}")
                except discord.Forbidden:
                    pass

                await interaction.response.edit_message(content=f"Banned {user.mention}.", embed=None, view=None)

            except discord.Forbidden:
                await interaction.response.edit_message(content="I don't have permission to ban this user.", embed=None, view=None)
            except discord.HTTPException:
                await interaction.response.edit_message(content="Failed to ban user.", embed=None, view=None)

        confirmembed = discord.Embed(
            title="Confirm Ban",
            description=f"Are you sure you want to ban {user.mention}?\n*This action cannot be undone.*",
            color=discord.Color.yellow()
        )
        confirmembed.add_field(name="Reason", value=banreason)
        confirmembed.add_field(name="Target", value=user.mention)
        confirmembed.set_footer(text="You have 30 seconds to confirm.")

        await interaction.response.send_message(embed=confirmembed, view=ConfirmView(interaction.user, banUser))


async def setup(bot: commands.Bot):
    await bot.add_cog(ModerationCommands(bot))