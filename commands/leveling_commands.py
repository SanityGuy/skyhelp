import math
import sqlite3
from typing import Literal, Optional

import discord
from discord import app_commands
from discord.ext import commands


DATABASE = "leveling.db"

XP_BASE = 75

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
        if level <= 0:
            return 0
        return XP_BASE * (level ** 2)

    @staticmethod
    def level_from_xp(xp: int) -> int:
        if xp <= 0:
            return 0
        return math.isqrt(xp // XP_BASE)

    @staticmethod
    def get_progress(
        xp: int,
        level: int,
    ) -> tuple[int, int]:
        current_level_xp = LevelingCommands.xp_for_level(level)
        next_level_xp = LevelingCommands.xp_for_level(level + 1)
        progress = max(0, xp - current_level_xp)
        required = next_level_xp - current_level_xp
        return progress, required

    def get_user(
        self,
        guild_id: int,
        user_id: int,
    ) -> tuple[int, int, int]:

        row = self.db.execute(
            """
            SELECT xp, level, last_xp_time
            FROM users
            WHERE guild_id = ?
              AND user_id = ?
            """,
            (guild_id, user_id),
        ).fetchone()

        if row is None:
            return 0, 0, 0
        return row["xp"], row["level"], row["last_xp_time"]

    def save_user(
        self,
        guild_id: int,
        user_id: int,
        xp: int,
        level: int,
        last_xp_time: int = 0,
    ):

        self.db.execute(
            """
            INSERT INTO users (
                guild_id,
                user_id,
                xp,
                level,
                last_xp_time
            )
            VALUES (?, ?, ?, ?, ?)

            ON CONFLICT(guild_id, user_id)
            DO UPDATE SET
                xp = excluded.xp,
                level = excluded.level,
                last_xp_time = excluded.last_xp_time
            """,
            (
                guild_id,
                user_id,
                xp,
                level,
                last_xp_time,
            ),
        )

        self.db.commit()

    @staticmethod
    def is_admin(
        interaction: discord.Interaction,
    ) -> bool:
        if not isinstance(interaction.user, discord.Member):
            return False
        return interaction.user.guild_permissions.administrator

    async def sync_roles(
        self,
        guild: discord.Guild,
        member: discord.Member,
        level: int,
    ):
        for required_level, role_id in ROLE_REWARDS.items():
            role = guild.get_role(role_id)
            if role is None:
                continue
            should_have = level >= required_level
            has_role = role in member.roles
            try:
                if should_have and not has_role:
                    await member.add_roles(role, reason=f"Level {level}")
                elif not should_have and has_role:
                    await member.remove_roles(role, reason=f"Level decreased to {level}")
            except discord.Forbidden:
                continue
            except discord.HTTPException:
                continue

    @app_commands.command(
        name="rank",
        description="Check your or another member's rank.",
    )
    @app_commands.guild_only()
    async def rank(
        self,
        interaction: discord.Interaction,
        member: Optional[discord.Member] = None,
    ):

        target = member or interaction.user
        xp, level, _ = self.get_user(interaction.guild_id, target.id)
        progress, required = self.get_progress(xp, level)
        percentage = progress / required * 100 if required > 0 else 100
        bars = 10
        filled = min(bars, int(progress / required * bars) if required > 0 else bars)
        progress_bar = "█" * filled + "░" * (bars - filled)

        embed = discord.Embed(
            title=f"📊 Rank Overview • {target.display_name}",
            color=discord.Color.blue(),
        )

        embed.set_thumbnail(
            url=target.display_avatar.url
        )

        embed.add_field(
            name="Level",
            value=f"**{level}**",
            inline=True,
        )

        embed.add_field(
            name="Total XP",
            value=f"**{xp:,}**",
            inline=True,
        )

        embed.add_field(
            name="Next Level",
            value=f"**Level {level + 1}**",
            inline=True,
        )

        embed.add_field(
            name=f"Progress to Level {level + 1}",
            value=(
                f"**{percentage:.1f}%**"
                f"`{progress_bar}`\n"
                f"`{progress:,} / {required:,} XP`\n"
            ),
            inline=False,
        )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="leaderboard",
        description="View the server XP leaderboard.",
    )
    @app_commands.guild_only()
    async def leaderboard(
        self,
        interaction: discord.Interaction,
    ):

        rows = self.db.execute(
            """
            SELECT user_id, xp, level
            FROM users
            WHERE guild_id = ?
            ORDER BY xp DESC
            LIMIT 10
            """,
            (interaction.guild_id,),
        ).fetchall()

        if not rows:

            await interaction.response.send_message("📊 No ranking data available yet.")
            return

        medals = {
            1: "🥇",
            2: "🥈",
            3: "🥉",
        }

        lines = []

        for position, row in enumerate(
            rows,
            start=1,
        ):

            member = interaction.guild.get_member(
                row["user_id"]
            )

            if member:
                name = member.display_name
            else:
                name = f"Unknown User ({row['user_id']})"

            prefix = medals.get(
                position,
                f"**#{position}**",
            )

            lines.append(
                f"{prefix} **{name}**\n"
                f"└ Level **{row['level']}** "
                f"• `{row['xp']:,} XP`"
            )

        embed = discord.Embed(
            title=f"🏆 {interaction.guild.name} Leaderboard",
            description="\n".join(lines),
            color=discord.Color.gold(),
        )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="add",
        description="Add XP or levels to a member.",
    )
    @app_commands.guild_only()
    @app_commands.default_permissions(
        administrator=True
    )
    async def add(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        target_type: Literal["xp", "level"],
        amount: int,
    ):

        if not self.is_admin(interaction):

            await interaction.response.send_message(
                "❌ You need Administrator permission.",
                ephemeral=True,
            )

            return

        if amount <= 0:

            await interaction.response.send_message(
                "❌ Amount must be greater than 0.",
                ephemeral=True,
            )

            return

        xp, level, last_xp_time = self.get_user(
            interaction.guild_id,
            member.id,
        )

        old_level = level

        if target_type == "xp":

            new_xp = xp + amount

            new_level = self.level_from_xp(
                new_xp
            )

        else:

            new_level = level + amount

            new_xp = self.xp_for_level(
                new_level
            )

        self.save_user(
            interaction.guild_id,
            member.id,
            new_xp,
            new_level,
            last_xp_time,
        )

        await self.sync_roles(
            interaction.guild,
            member,
            new_level,
        )

        await interaction.response.send_message(
            f"✅ Added **{amount:,} {target_type.upper()}** "
            f"to {member.mention}.\n"
            f"Level: **{old_level} → {new_level}**\n"
            f"XP: **{new_xp:,}**"
        )

    @app_commands.command(
        name="set",
        description="Set a member's XP or level.",
    )
    @app_commands.guild_only()
    @app_commands.default_permissions(
        administrator=True
    )
    async def set_data(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        target_type: Literal["xp", "level"],
        amount: int,
    ):

        if not self.is_admin(interaction):

            await interaction.response.send_message(
                "❌ You need Administrator permission.",
                ephemeral=True,
            )

            return

        if amount < 0:

            await interaction.response.send_message(
                "❌ Amount cannot be negative.",
                ephemeral=True,
            )

            return

        _, _, last_xp_time = self.get_user(
            interaction.guild_id,
            member.id,
        )

        if target_type == "xp":

            new_xp = amount

            new_level = self.level_from_xp(
                new_xp
            )

        else:

            new_level = amount

            new_xp = self.xp_for_level(
                new_level
            )

        self.save_user(
            interaction.guild_id,
            member.id,
            new_xp,
            new_level,
            last_xp_time,
        )

        await self.sync_roles(
            interaction.guild,
            member,
            new_level,
        )

        await interaction.response.send_message(
            f"✅ Set {member.mention}'s "
            f"**{target_type.upper()}** to **{amount:,}**.\n"
            f"Level: **{new_level}**\n"
            f"XP: **{new_xp:,}**"
        )

    @app_commands.command(
        name="reduce",
        description="Remove XP or levels from a member.",
    )
    @app_commands.guild_only()
    @app_commands.default_permissions(
        administrator=True
    )
    async def reduce(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        target_type: Literal["xp", "level"],
        amount: int,
    ):

        if not self.is_admin(interaction):

            await interaction.response.send_message(
                "❌ You need Administrator permission.",
                ephemeral=True,
            )

            return

        if amount <= 0:

            await interaction.response.send_message(
                "❌ Amount must be greater than 0.",
                ephemeral=True,
            )

            return

        xp, level, last_xp_time = self.get_user(
            interaction.guild_id,
            member.id,
        )

        if target_type == "xp":

            new_xp = max(
                0,
                xp - amount,
            )

            new_level = self.level_from_xp(
                new_xp
            )

        else:

            new_level = max(
                0,
                level - amount,
            )

            new_xp = self.xp_for_level(
                new_level
            )

        self.save_user(
            interaction.guild_id,
            member.id,
            new_xp,
            new_level,
            last_xp_time,
        )

        await self.sync_roles(
            interaction.guild,
            member,
            new_level,
        )

        await interaction.response.send_message(
            f"🔻 Reduced {member.mention}'s "
            f"**{target_type.upper()}**.\n"
            f"Level: **{new_level}**\n"
            f"XP: **{new_xp:,}**"
        )

    @app_commands.command(
        name="reset",
        description="Reset a member's leveling data.",
    )
    @app_commands.guild_only()
    @app_commands.default_permissions(
        administrator=True
    )
    async def reset(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        target_type: Literal[
            "xp",
            "level",
            "all",
        ],
    ):

        if not self.is_admin(interaction):

            await interaction.response.send_message(
                "❌ You need Administrator permission.",
                ephemeral=True,
            )

            return

        _, _, last_xp_time = self.get_user(
            interaction.guild_id,
            member.id,
        )

        self.save_user(
            interaction.guild_id,
            member.id,
            0,
            0,
            last_xp_time,
        )

        await self.sync_roles(
            interaction.guild,
            member,
            0,
        )

        await interaction.response.send_message(
            f"🔄 Reset **{target_type.upper()}** "
            f"for {member.mention}.\n"
            f"Level: **0**\n"
            f"XP: **0**"
        )

    def cog_unload(self):
        try:
            self.db.commit()
            self.db.close()
        except sqlite3.Error:
            pass


async def setup(bot: commands.Bot):
    await bot.add_cog(LevelingCommands(bot))