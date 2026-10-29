
import discord
from discord.ext import commands


class ButtonEventsListener(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if (
            interaction.type != discord.InteractionType.component
            or not interaction.guild
            or not isinstance(interaction.data, dict)
        ):
            return

        custom_id = interaction.data.get("custom_id", "")

        if custom_id.startswith("staff_ban:"):
            if not interaction.user.guild_permissions.ban_members:
                await interaction.response.send_message(
                    "> ## ❌ You need **Ban Members** permission to perform this action.",
                    ephemeral=True
                )
                return

            if not interaction.guild.me.guild_permissions.ban_members:
                await interaction.response.send_message(
                    "❌ I need the **Ban Members** permission to perform this action.",
                    ephemeral=True
                )
                return

            try:
                target_user_id = int(custom_id.split(":", 1)[1])
                target = discord.Object(id=target_user_id)

                await interaction.response.defer(ephemeral=True)

                await interaction.guild.ban(
                    target,
                    reason=f"Banned via Staff Audit Log by {interaction.user} ({interaction.user.id})"
                )

                await interaction.followup.send(
                    f"✅ User `{target_user_id}` was successfully banned.",
                    ephemeral=True
                )

            except ValueError:
                message = "❌ Invalid user ID in this button."
                if interaction.response.is_done():
                    await interaction.followup.send(message, ephemeral=True)
                else:
                    await interaction.response.send_message(message, ephemeral=True)

            except discord.Forbidden:
                message = "❌ I cannot ban this user. Check my permissions and role hierarchy."
                if interaction.response.is_done():
                    await interaction.followup.send(message, ephemeral=True)
                else:
                    await interaction.response.send_message(message, ephemeral=True)

            except discord.HTTPException:
                message = "❌ Discord rejected the ban request. Please try again."
                if interaction.response.is_done():
                    await interaction.followup.send(message, ephemeral=True)
                else:
                    await interaction.response.send_message(message, ephemeral=True)

        elif custom_id.startswith("welcome_greet:"):
            if not interaction.response.is_done():
                await interaction.response.defer()

            target_user_id = custom_id.split(":", 1)[1]

            if not target_user_id.isdigit():
                return

            channel = interaction.channel

            if channel is None:
                return

            try:
                await channel.send(
                    f"> ### <@{target_user_id}> has been welcomed into the server by {interaction.user.mention}! 🎉"
                )
            except discord.Forbidden:
                if interaction.is_expired():
                    return

                await interaction.followup.send(
                    "❌ I cannot send messages in this channel.",
                    ephemeral=True
                )


async def setup(bot: commands.Bot):
    await bot.add_cog(ButtonEventsListener(bot))
