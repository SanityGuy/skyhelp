import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import sqlite3

DATABASE = "birthdays.db"

class BirthdayCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = sqlite3.connect(DATABASE, timeout=10)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=NORMAL")
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS birthdays (
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                birthday TEXT NOT NULL,
                PRIMARY KEY (guild_id, user_id)
            )
        """)
        self.db.commit()

    def get_user(self, guild_id: int, user_id: int):
        cursor = self.db.cursor()
        cursor.execute(
            "SELECT * FROM birthdays WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id)
        )
        return cursor.fetchone()

    def set_user_birthday(self, guild_id: int, user_id: int, birthday: str):
        self.db.execute("""
            INSERT INTO birthdays (guild_id, user_id, birthday)
            VALUES (?, ?, ?)
            ON CONFLICT(guild_id, user_id)
            DO UPDATE SET birthday = excluded.birthday
        """, (guild_id, user_id, birthday))
        self.db.commit()

    def delete_user_birthday(self, guild_id: int, user_id: int):
        self.db.execute(
            "DELETE FROM birthdays WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id)
        )
        self.db.commit()

    def cog_unload(self):
        self.db.close()

    @app_commands.command(
        name="birthday",
        description="Set your birthday (format: DD/MM/YYYY)"
    )
    @app_commands.guild_only()
    async def birthday(self, interaction: discord.Interaction, birthday: str):
        try:
            parsed = datetime.strptime(birthday, "%d/%m/%Y")
            birthday = parsed.strftime("%d/%m/%Y")
        except ValueError:
            await interaction.response.send_message(
                "Invalid birthday! Please use DD/MM/YYYY.",
                ephemeral=True
            )
            return

        guild_id = interaction.guild_id
        user_id = interaction.user.id

        self.set_user_birthday(guild_id, user_id, birthday)

        await interaction.response.send_message(
            f"Your birthday has been set to **{birthday}**!",
            ephemeral=True
        )

    @app_commands.command(
        name="mybirthday",
        description="View your saved birthday"
    )
    @app_commands.guild_only()
    async def mybirthday(self, interaction: discord.Interaction):
        birthday = self.get_user(interaction.guild_id, interaction.user.id)

        if birthday is None:
            await interaction.response.send_message(
                "You haven't set your birthday yet.",
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            f"Your birthday is **{birthday['birthday']}**.",
            ephemeral=True
        )

    @app_commands.command(
        name="removebirthday",
        description="Remove your saved birthday"
    )
    @app_commands.guild_only()
    async def removebirthday(self, interaction: discord.Interaction):
        guild_id = interaction.guild_id
        user_id = interaction.user.id

        if self.get_user(guild_id, user_id) is None:
            await interaction.response.send_message(
                "You don't have a registered birthday.",
                ephemeral=True
            )
            return

        self.delete_user_birthday(guild_id, user_id)

        await interaction.response.send_message(
            "Your birthday has been removed.",
            ephemeral=True
        )

async def setup(bot: commands.Bot):
    await bot.add_cog(BirthdayCommand(bot)) 