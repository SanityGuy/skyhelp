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
        ):
            return

        custom_id = interaction.data.get("custom_id", "")

        if custom_id.startswith("staff_ban:"):
            if not interaction.user.guild_permissions.ban_members:
                await interaction.response.send_message(
                    "> ## ❌ You need **Ban Members** permission to perform this action.",
                    ephemeral=True,
                )
                return

            target_user_id = int(custom_id.split(":")[1])

            try:
                await interaction.guild.ban(
                    discord.Object(id=target_user_id),
                    reason=f"Banned via Staff Audit Log by {interaction.user.display_name}",
                )
                await interaction.response.send_message(
                    f"✅ User `{target_user_id}` was successfully banned."
                )
            except Exception as e:
                await interaction.response.send_message(
                    f"❌ Failed to ban user: {e}", ephemeral=True
                )

        elif custom_id.startswith("welcome_greet:"):
            target_user_id = custom_id.split(":")[1]

            await interaction.channel.send(
                f"> ### <@{target_user_id}> has been welcomed into the server by {interaction.user.mention}! 🎉"
            )
            await interaction.response.defer_update()


async def setup(bot: commands.Bot):
    await bot.add_cog(ButtonEventsListener(bot))