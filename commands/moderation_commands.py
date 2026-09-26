import discord
from discord.ext import commands
from discord import app_commands

class ConfirmView(discord.ui.View):
    def __init__(self, author: discord.Member, action):
        super().__init__(timeout=30)
        self.author = author
        self.action = action
        self.message = None

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("This isn't your confirmation.", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True

        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass

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

    def can_moderate(self, interaction: discord.Interaction, user: discord.Member):
        if interaction.guild is None:
            return "This command can only be used in a server!"

        if user.id == interaction.user.id:
            return "You cannot moderate yourself!"

        if user == interaction.guild.owner:
            return "You cannot moderate the server owner!"

        if interaction.user != interaction.guild.owner and user.top_role >= interaction.user.top_role:
            return "You cannot moderate a member with an equal or higher role than you."

        if interaction.guild.me.top_role <= user.top_role:
            return "I cannot moderate this user because their role is equal to or higher than mine."

        return None

    @app_commands.command(name="ban", description="Bans a user from the server")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, user: discord.Member, reason: str | None = None):
        if interaction.guild is None:
            await interaction.response.send_message("This command can only be used in a server!", ephemeral=True)
            return

        error = self.can_moderate(interaction, user)

        if error:
            await interaction.response.send_message(error, ephemeral=True)
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

        confirmembed = discord.Embed(title="Confirm Ban", description=f"Are you sure you want to ban {user.mention}?\n*This action cannot be undone.*", color=discord.Color.yellow())
        confirmembed.add_field(name="Reason", value=banreason)
        confirmembed.add_field(name="Target", value=user.mention)
        confirmembed.set_footer(text="You have 30 seconds to confirm.")

        view = ConfirmView(interaction.user, banUser)

        await interaction.response.send_message(embed=confirmembed, view=view)
        view.message = await interaction.original_response()

    @app_commands.command(name="kick", description="Kicks a user from the server")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, user: discord.Member, reason: str | None = None):
        if interaction.guild is None:
            await interaction.response.send_message("This command can only be used in a server!", ephemeral=True)
            return

        error = self.can_moderate(interaction, user)

        if error:
            await interaction.response.send_message(error, ephemeral=True)
            return

        kickreason = reason or "No reason provided"

        async def kickUser(interaction: discord.Interaction):
            try:
                await user.kick(reason=kickreason)

                try:
                    await user.send(f"You have been kicked from {interaction.guild.name} by {interaction.user.display_name}.\nReason: {kickreason}")
                except discord.Forbidden:
                    pass

                await interaction.response.edit_message(content=f"Kicked {user.mention}.", embed=None, view=None)

            except discord.Forbidden:
                await interaction.response.edit_message(content="I don't have permission to kick this user.", embed=None, view=None)
            except discord.HTTPException:
                await interaction.response.edit_message(content="Failed to kick user.", embed=None, view=None)

        confirmembed = discord.Embed(title="Confirm Kick", description=f"Are you sure you want to kick {user.mention}?\n*This action cannot be undone.*", color=discord.Color.yellow())
        confirmembed.add_field(name="Reason", value=kickreason)
        confirmembed.add_field(name="Target", value=user.mention)
        confirmembed.set_footer(text="You have 30 seconds to confirm.")

        view = ConfirmView(interaction.user, kickUser)

        await interaction.response.send_message(embed=confirmembed, view=view)
        view.message = await interaction.original_response()


async def setup(bot: commands.Bot):
    await bot.add_cog(ModerationCommands(bot))