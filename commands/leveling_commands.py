
import math
import sqlite3
from typing import Literal, Optional

import discord
from discord import app_commands
from discord.ext import commands


DATABASE = "leveling.db"
XP_BASE = 20
EMBED_COLOR = discord.Color(0x2563EB)

ROLE_REWARDS = {
    5: 1540138906119315530,
    10: 1540138906119315531,
    20: 1540138906119315532,
    30: 1540138906119315533,
    50: 1540138906119315534,
}


class LevelingCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = sqlite3.connect(DATABASE, timeout=10)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=NORMAL")
        self.db.execute("PRAGMA busy_timeout=10000")
        self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                xp INTEGER NOT NULL DEFAULT 0,
                level INTEGER NOT NULL DEFAULT 0,
                last_xp_time INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (guild_id, user_id)
            )
            """
        )
        self.db.commit()

    @staticmethod
    def xp_for_level(level: int) -> int:
        return XP_BASE * level ** 2 if level > 0 else 0

    @staticmethod
    def level_from_xp(xp: int) -> int:
        return math.isqrt(max(0, xp) // XP_BASE)

    @staticmethod
    def progress_bar(current: int, required: int, length: int = 12) -> str:
        filled = min(length, int(current / required * length)) if required else length
        return f"{'▰' * filled}{'▱' * (length - filled)}"

    def get_user(self, guild_id: int, user_id: int) -> tuple[int, int, int]:
        row = self.db.execute(
            "SELECT xp, level, last_xp_time FROM users WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id),
        ).fetchone()

        return (row["xp"], self.level_from_xp(row["xp"]), row["last_xp_time"]) if row else (0, 0, 0)

    def save_user(self, guild_id: int, user_id: int, xp: int, level: int, last_xp_time: int):
        with self.db:
            self.db.execute(
                """
                INSERT INTO users (guild_id, user_id, xp, level, last_xp_time)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(guild_id, user_id)
                DO UPDATE SET xp = excluded.xp, level = excluded.level, last_xp_time = excluded.last_xp_time
                """,
                (guild_id, user_id, xp, level, last_xp_time),
            )

    @staticmethod
    def is_admin(interaction: discord.Interaction) -> bool:
        return isinstance(interaction.user, discord.Member) and interaction.user.guild_permissions.administrator

    async def respond(self, interaction: discord.Interaction, title: str, description: str, *, ephemeral: bool = False, color: discord.Color = EMBED_COLOR):
        embed = discord.Embed(title=f"✦ SKYFLIX NETWORK • {title}", description=description, color=color, timestamp=discord.utils.utcnow())
        embed.set_footer(text="SkyFlix Network • Leveling System")
        await interaction.response.send_message(embed=embed, ephemeral=ephemeral)

    async def sync_roles(self, guild: discord.Guild, member: discord.Member, level: int):
        for required_level, role_id in sorted(ROLE_REWARDS.items()):
            role = guild.get_role(role_id)

            if role is None or not role.is_assignable():
                continue

            try:
                if level >= required_level and role not in member.roles:
                    await member.add_roles(role, reason=f"Level {level}")
                elif level < required_level and role in member.roles:
                    await member.remove_roles(role, reason=f"Level decreased to {level}")
            except discord.HTTPException:
                continue

    async def update_member(self, interaction: discord.Interaction, member: discord.Member, target_type: Literal["xp", "level"], amount: int, action: Literal["add", "set", "reduce"]):
        xp, level, last_xp_time = self.get_user(interaction.guild_id, member.id)
        old_level = level

        if action == "add":
            new_xp = xp + amount if target_type == "xp" else self.xp_for_level(level + amount)
        elif action == "set":
            new_xp = amount if target_type == "xp" else self.xp_for_level(amount)
        else:
            new_xp = max(0, xp - amount) if target_type == "xp" else self.xp_for_level(max(0, level - amount))

        new_level = self.level_from_xp(new_xp)
        self.save_user(interaction.guild_id, member.id, new_xp, new_level, last_xp_time)
        await self.sync_roles(interaction.guild, member, new_level)

        return old_level, new_level, new_xp

    @app_commands.command(name="rank", description="Check your or another member's rank.")
    @app_commands.guild_only()
    async def rank(self, interaction: discord.Interaction, member: Optional[discord.Member] = None):
        target = member or interaction.user
        xp, level, _ = self.get_user(interaction.guild_id, target.id)

        current = xp - self.xp_for_level(level)
        required = self.xp_for_level(level + 1) - self.xp_for_level(level)
        percentage = current / required * 100 if required else 100

        embed = discord.Embed(
            title="✦ SKYFLIX NETWORK • RANK",
            description=f"## 📊 {target.display_name}\nHere's your leveling overview.",
            color=EMBED_COLOR,
            timestamp=discord.utils.utcnow(),
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="🏆 Level", value=f"**{level}**", inline=True)
        embed.add_field(name="💎 Total XP", value=f"**{xp:,}**", inline=True)
        embed.add_field(name="🎯 Next Level", value=f"**{level + 1}**", inline=True)
        embed.add_field(
            name=f"Progress to Level {level + 1}",
            value=f"**{percentage:.1f}%**\n`{self.progress_bar(current, required)}`\n`{current:,} / {required:,} XP`",
            inline=False,
        )
        embed.set_footer(text="SkyFlix Network • Leveling System")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="leaderboard", description="View the server XP leaderboard.")
    @app_commands.guild_only()
    async def leaderboard(self, interaction: discord.Interaction):
        rows = self.db.execute(
            "SELECT user_id, xp, level FROM users WHERE guild_id = ? ORDER BY xp DESC LIMIT 10",
            (interaction.guild_id,),
        ).fetchall()

        if not rows:
            await self.respond(interaction, "LEADERBOARD", "No ranking data is available yet.")
            return

        medals = {1: "🥇", 2: "🥈", 3: "🥉"}
        lines = []

        for position, row in enumerate(rows, start=1):
            member = interaction.guild.get_member(row["user_id"])
            name = member.display_name if member else f"Unknown User ({row['user_id']})"
            prefix = medals.get(position, f"`#{position}`")
            level = self.level_from_xp(row["xp"])
            lines.append(f"{prefix} **{name}**\n└ Level **{level}** • `{row['xp']:,} XP`")

        embed = discord.Embed(
            title=f"✦ SKYFLIX NETWORK • LEADERBOARD",
            description="\n\n".join(lines),
            color=EMBED_COLOR,
            timestamp=discord.utils.utcnow(),
        )
        embed.set_footer(text="Top 10 Members • SkyFlix Network")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="add", description="Add XP or levels to a member.")
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    async def add(self, interaction: discord.Interaction, member: discord.Member, target_type: Literal["xp", "level"], amount: int):
        if not self.is_admin(interaction):
            await self.respond(interaction, "ACCESS DENIED", "Administrator permission is required.", ephemeral=True, color=discord.Color.red())
            return

        if amount <= 0:
            await self.respond(interaction, "INVALID AMOUNT", "Amount must be greater than zero.", ephemeral=True, color=discord.Color.red())
            return

        old, new, xp = await self.update_member(interaction, member, target_type, amount, "add")
        await self.respond(interaction, "MEMBER UPDATED", f"Added **{amount:,} {target_type.upper()}** to {member.mention}.\n\n**Level:** {old} → {new}\n**Total XP:** {xp:,}")

    @app_commands.command(name="set", description="Set a member's XP or level.")
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    async def set_data(self, interaction: discord.Interaction, member: discord.Member, target_type: Literal["xp", "level"], amount: int):
        if not self.is_admin(interaction):
            await self.respond(interaction, "ACCESS DENIED", "Administrator permission is required.", ephemeral=True, color=discord.Color.red())
            return

        if amount < 0:
            await self.respond(interaction, "INVALID AMOUNT", "Amount cannot be negative.", ephemeral=True, color=discord.Color.red())
            return

        _, new, xp = await self.update_member(interaction, member, target_type, amount, "set")
        await self.respond(interaction, "MEMBER UPDATED", f"Set {member.mention}'s **{target_type.upper()}** to **{amount:,}**.\n\n**Level:** {new}\n**Total XP:** {xp:,}")

    @app_commands.command(name="reduce", description="Remove XP or levels from a member.")
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    async def reduce(self, interaction: discord.Interaction, member: discord.Member, target_type: Literal["xp", "level"], amount: int):
        if not self.is_admin(interaction):
            await self.respond(interaction, "ACCESS DENIED", "Administrator permission is required.", ephemeral=True, color=discord.Color.red())
            return

        if amount <= 0:
            await self.respond(interaction, "INVALID AMOUNT", "Amount must be greater than zero.", ephemeral=True, color=discord.Color.red())
            return

        old, new, xp = await self.update_member(interaction, member, target_type, amount, "reduce")
        await self.respond(interaction, "MEMBER UPDATED", f"Reduced **{amount:,} {target_type.upper()}** from {member.mention}.\n\n**Level:** {old} → {new}\n**Total XP:** {xp:,}")

    @app_commands.command(name="reset", description="Reset a member's leveling data.")
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    async def reset(self, interaction: discord.Interaction, member: discord.Member, target_type: Literal["xp", "level", "all"]):
        if not self.is_admin(interaction):
            await self.respond(interaction, "ACCESS DENIED", "Administrator permission is required.", ephemeral=True, color=discord.Color.red())
            return

        xp, level, last_xp_time = self.get_user(interaction.guild_id, member.id)

        if target_type == "xp":
            new_xp = 0
            new_level = 0
        elif target_type == "level":
            new_level = 0
            new_xp = 0
        else:
            new_xp = 0
            new_level = 0

        self.save_user(interaction.guild_id, member.id, new_xp, new_level, last_xp_time)
        await self.sync_roles(interaction.guild, member, new_level)

        await self.respond(interaction, "LEVELING RESET", f"Reset **{target_type.upper()}** for {member.mention}.\n\n**Previous Level:** {level}\n**Previous XP:** {xp:,}\n**Current Level:** 0\n**Current XP:** 0")

    def cog_unload(self):
        try:
            self.db.close()
        except sqlite3.Error:
            pass


async def setup(bot: commands.Bot):
    await bot.add_cog(LevelingCommands(bot))
