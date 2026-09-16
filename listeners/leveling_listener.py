import math
import random
import sqlite3
import time

import discord
from discord.ext import commands


DATABASE = "leveling.db"

XP_COOLDOWN_MS = 60_000
MIN_XP = 15
MAX_XP = 29

XP_BASE = 50

ROLE_REWARDS = {
    5: 1540138906119315530,
    10: 1540138906119315531,
    20: 1540138906119315532,
    30: 1540138906119315533,
    50: 1540138906119315534,
}


class LevelingListener(commands.Cog):
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
        """
        Total XP required to reach a level.

        Level 0 = 0 XP
        Level 1 = 50 XP
        Level 2 = 200 XP
        Level 3 = 450 XP
        Level 4 = 800 XP
        Level 5 = 1250 XP
        """

        if level <= 0:
            return 0

        return XP_BASE * (level ** 2)

    @staticmethod
    def level_from_xp(xp: int) -> int:
        """
        Calculate the highest level reached from total XP.
        """

        if xp <= 0:
            return 0

        return math.isqrt(xp // XP_BASE)

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

        return (
            row["xp"],
            row["level"],
            row["last_xp_time"],
        )

    def save_user(
        self,
        guild_id: int,
        user_id: int,
        xp: int,
        level: int,
        last_xp_time: int,
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
                    await member.add_roles(role, reason=f"Reached Level {level}")

                elif not should_have and has_role:
                    await member.remove_roles(role, reason=f"Level decreased to {level}")

            except discord.Forbidden:
                continue
            except discord.HTTPException:
                continue

    async def send_level_up_message(
        self,
        message: discord.Message,
        old_level: int,
        new_level: int,
    ):

        member = message.author
        unlocked_roles = []

        for required_level, role_id in ROLE_REWARDS.items():
            if old_level < required_level <= new_level:
                role = message.guild.get_role(role_id)
                if role:
                    unlocked_roles.append(role.mention)

        if unlocked_roles:
            roles = ", ".join(unlocked_roles)
            content = (
                f"> ## 🎉 {member.mention} reached "
                f"**Level {new_level}**!\n"
                f"> 🔓 Unlocked: {roles}"
            )

        else:
            content = (
                f"> ## 🎉 {member.mention} reached "
                f"**Level {new_level}**!"
            )

        try:
            await message.channel.send(content)
        except discord.HTTPException:
            pass

    @commands.Cog.listener()
    async def on_message(
        self,
        message: discord.Message,
    ):

        if message.author.bot:
            return

        if message.guild is None:
            return

        guild_id = message.guild.id
        user_id = message.author.id

        current_time = int(time.time() * 1000)

        xp, old_level, last_xp_time = self.get_user(
            guild_id,
            user_id,
        )

        if current_time - last_xp_time < XP_COOLDOWN_MS:
            return

        added_xp = random.randint(
            MIN_XP,
            MAX_XP,
        )

        new_xp = xp + added_xp

        new_level = self.level_from_xp(new_xp)

        self.save_user(
            guild_id,
            user_id,
            new_xp,
            new_level,
            current_time,
        )

        if new_level <= old_level:
            return

        await self.sync_roles(
            message.guild,
            message.author,
            new_level,
        )

        await self.send_level_up_message(
            message,
            old_level,
            new_level,
        )

    def cog_unload(self):
        try:
            self.db.commit()
            self.db.close()
        except sqlite3.Error:
            pass


async def setup(bot: commands.Bot):
    await bot.add_cog(LevelingListener(bot))