from datetime import datetime, timezone
import sqlite3
import discord
from discord.ext import commands


class MemberEventsListener(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = sqlite3.connect("leveling.db")
        self.cursor = self.db.cursor()
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS guild_settings (
                guild_id INTEGER PRIMARY KEY,
                auto_role_id INTEGER,
                welcome_channel_id INTEGER,
                log_channel_id INTEGER
            )
        """
        )
        self.db.commit()

    def get_guild_settings(self, guild_id: int):
        self.cursor.execute(
            "SELECT auto_role_id, welcome_channel_id, log_channel_id FROM guild_settings WHERE guild_id = ?",
            (guild_id,),
        )
        row = self.cursor.fetchone()
        if row:
            return {
                "auto_role_id": row[0],
                "welcome_channel_id": row[1],
                "log_channel_id": row[2],
            }
        return {
            "auto_role_id": None,
            "welcome_channel_id": None,
            "log_channel_id": None,
        }

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild = member.guild
        settings = self.get_guild_settings(guild.id)

        if settings["auto_role_id"]:
            role = guild.get_role(settings["auto_role_id"])
            if role:
                try:
                    await member.add_roles(role)
                except discord.Forbidden:
                    print(
                        "Failed to assign auto-role: Check hierarchy and permissions."
                    )

        if settings["welcome_channel_id"]:
            welcome_channel = guild.get_channel(settings["welcome_channel_id"])
            if welcome_channel and isinstance(
                welcome_channel, discord.TextChannel
            ):
                rules_channel_id = 1540138907126202470
                announcements_channel_id = 1540138907126202473
                general_channel_id = 1540138907126202475

                embed = discord.Embed(
                    title=f"👋 Welcome to {guild.name}!",
                    description=(
                        f"Hello there, {member.mention}! We are absolutely thrilled to have you here with us.\n\n"
                        f"**📌 Getting Started:**\n"
                        f"• Read our ground rules in <#{rules_channel_id}>\n"
                        f"• Stay updated with server news via <#{announcements_channel_id}>\n"
                        f"• Jump into the community conversation over at <#{general_channel_id}>\n\n"
                        f"Have a fantastic stay! ✨"
                    ),
                    color=discord.Color.from_rgb(30, 144, 255),
                )
                embed.set_thumbnail(url=member.display_avatar.url)
                embed.set_footer(text=f"Member #{guild.member_count}")

                view = discord.ui.View()
                greet_button = discord.ui.Button(
                    style=discord.ButtonStyle.primary,
                    label="👋 Say Welcome!",
                    custom_id=f"welcome_greet:{member.id}",
                )
                view.add_item(greet_button)

                await welcome_channel.send(embed=embed, view=view)

        if settings["log_channel_id"]:
            log_channel = guild.get_channel(settings["log_channel_id"])
            if log_channel and isinstance(log_channel, discord.TextChannel):
                now = datetime.now(timezone.utc)
                account_age_days = (now - member.created_at).days
                is_new_account = account_age_days < 7

                log_embed = discord.Embed(
                    title="📥 Member Joined — Staff Review",
                    color=(
                        discord.Color.red()
                        if is_new_account
                        else discord.Color.cyan()
                    ),
                )
                log_embed.set_thumbnail(url=member.display_avatar.url)
                log_embed.add_field(
                    name="User",
                    value=f"{member.name} ({member.mention})",
                    inline=False,
                )
                log_embed.add_field(
                    name="User ID", value=str(member.id), inline=True
                )
                log_embed.add_field(
                    name="Account Created",
                    value=f"<t:{int(member.created_at.timestamp())}:R>",
                    inline=True,
                )
                log_embed.add_field(
                    name="Account Risk",
                    value=(
                        "⚠️ **NEW ACCOUNT** (< 7 days old)"
                        if is_new_account
                        else "✅ Normal"
                    ),
                    inline=False,
                )

                view = discord.ui.View()
                ban_button = discord.ui.Button(
                    style=discord.ButtonStyle.primary,
                    label="🔨 Ban",
                    custom_id=f"staff_ban:{member.id}",
                )
                view.add_item(ban_button)

                await log_channel.send(embed=log_embed, view=view)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        guild = member.guild
        settings = self.get_guild_settings(guild.id)

        if settings["log_channel_id"]:
            log_channel = guild.get_channel(settings["log_channel_id"])
            if log_channel and isinstance(log_channel, discord.TextChannel):
                log_embed = discord.Embed(
                    title="📤 Member Left Server", color=discord.Color.red()
                )
                log_embed.set_thumbnail(url=member.display_avatar.url)
                log_embed.add_field(
                    name="User Tag", value=str(member), inline=True
                )
                log_embed.add_field(
                    name="User ID", value=str(member.id), inline=True
                )
                log_embed.add_field(
                    name="Account Created",
                    value=f"<t:{int(member.created_at.timestamp())}:R>",
                    inline=False,
                )
                log_embed.set_footer(
                    text=f"Total Members: {guild.member_count}"
                )

                view = discord.ui.View()
                ban_btn = discord.ui.Button(
                    style=discord.ButtonStyle.danger,
                    label="Ban User",
                    custom_id=f"staff_ban:{member.id}",
                )
                view.add_item(ban_btn)

                await log_channel.send(embed=log_embed, view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(MemberEventsListener(bot))