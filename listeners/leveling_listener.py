
import logging
import math
import random
import sqlite3
import time

import discord
from discord.ext import commands


DATABASE = "leveling.db"

XP_COOLDOWN_MS = 60_000
MIN_XP = 5
MAX_XP = 15
XP_BASE = 20
EMBED_COLOR = discord.Color(0x2563EB)

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

    async def sync_roles(self, guild: discord.Guild, member: discord.Member, level: int):
        for required_level, role_id in sorted(ROLE_REWARDS.items()):
            role = guild.get_role(role_id)

            if role is None or not role.is_assignable():
                continue

            try:
                if level >= required_level and role not in member.roles:
                    await member.add_roles(role, reason=f"Reached Level {level}")
                elif level < required_level and role in member.roles:
                    await member.remove_roles(role, reason=f"Level decreased to {level}")
            except discord.HTTPException:
                logging.exception("Failed to synchronize reward role %s for %s", role_id, member.id)

    async def send_level_up_message(self, message: discord.Message, old_level: int, new_level: int, added_xp: int, total_xp: int):
        member = message.author
        progress = total_xp - self.xp_for_level(new_level)
        required = self.xp_for_level(new_level + 1) - self.xp_for_level(new_level)

        unlocked = [
            message.guild.get_role(role_id).mention
            for level, role_id in ROLE_REWARDS.items()
            if old_level < level <= new_level and message.guild.get_role(role_id)
        ]

        embed = discord.Embed(
            title="✦ SKYFLIX NETWORK",
            description=f"## 🎉 Level Up!\nCongratulations {member.mention}!\nYou've reached **Level {new_level}**.",
            color=EMBED_COLOR,
            timestamp=discord.utils.utcnow(),
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(
            name="📊 Level Progress",
            value=f"**Level {new_level} → {new_level + 1}**\n`{self.progress_bar(progress, required)}`\n`{progress:,} / {required:,} XP`",
            inline=False,
        )
        embed.add_field(name="✨ XP Earned", value=f"**+{added_xp:,} XP**", inline=True)
        embed.add_field(name="💎 Total XP", value=f"**{total_xp:,} XP**", inline=True)

        if unlocked:
            embed.add_field(name="🔓 Rewards Unlocked", value="\n".join(unlocked), inline=False)

        embed.set_footer(text="SkyFlix Network • Leveling System")

        try:
            await message.channel.send(
                embed=embed,
                allowed_mentions=discord.AllowedMentions(users=[member], roles=False, everyone=False),
            )
        except discord.HTTPException:
            logging.exception("Failed to send level-up message")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or message.guild is None or not isinstance(message.author, discord.Member):
            return

        current_time = time.time_ns() // 1_000_000
        xp, old_level, last_xp_time = self.get_user(message.guild.id, message.author.id)

        if current_time - last_xp_time < XP_COOLDOWN_MS:
            return

        added_xp = random.randint(MIN_XP, MAX_XP)
        new_xp = xp + added_xp
        new_level = self.level_from_xp(new_xp)

        self.save_user(message.guild.id, message.author.id, new_xp, new_level, current_time)

        if new_level <= old_level:
            return

        await self.sync_roles(message.guild, message.author, new_level)
        await self.send_level_up_message(message, old_level, new_level, added_xp, new_xp)

    def cog_unload(self):
        try:
            self.db.close()
        except sqlite3.Error:
            logging.exception("Failed to close leveling database")


async def setup(bot: commands.Bot):
    await bot.add_cog(LevelingListener(bot))
