
import sqlite3
import discord
from discord import app_commands
from discord.ext import commands
from contextlib import closing


class ConfigsCommand(commands.Cog):

    configs = app_commands.Group(
        name="configs",
        description="Manage NodeMC server configurations."
    )

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        with closing(sqlite3.connect("leveling.db")) as db:
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS guild_settings (
                    guild_id INTEGER PRIMARY KEY,
                    auto_role_id INTEGER,
                    welcome_channel_id INTEGER,
                    log_channel_id INTEGER
                )
                """
            )
            db.commit()

    def get_settings(self, guild_id: int):
        with closing(sqlite3.connect("leveling.db")) as db:
            db.row_factory = sqlite3.Row
            row = db.execute(
                """
                SELECT auto_role_id, welcome_channel_id, log_channel_id
                FROM guild_settings
                WHERE guild_id = ?
                """,
                (guild_id,)
            ).fetchone()

        if row is None:
            return {
                "auto_role_id": None,
                "welcome_channel_id": None,
                "log_channel_id": None
            }

        return dict(row)

    def update_setting(self, guild_id: int, column: str, value: int | None):
        allowed_columns = {
            "auto_role_id",
            "welcome_channel_id",
            "log_channel_id"
        }

        if column not in allowed_columns:
            raise ValueError("Invalid configuration setting.")

        with closing(sqlite3.connect("leveling.db")) as db:
            db.execute(
                """
                INSERT INTO guild_settings (guild_id)
                VALUES (?)
                ON CONFLICT(guild_id) DO NOTHING
                """,
                (guild_id,)
            )
            db.execute(
                f"UPDATE guild_settings SET {column} = ? WHERE guild_id = ?",
                (value, guild_id)
            )
            db.commit()

    def make_embed(self, interaction: discord.Interaction, title: str, description: str, color: discord.Color):
        embed = discord.Embed(
            title=title,
            description=description,
            color=color
        )

        if interaction.guild and interaction.guild.icon:
            embed.set_thumbnail(url=interaction.guild.icon.url)

        embed.set_footer(
            text=f"Requested by {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url
        )

        return embed

    async def require_guild(self, interaction: discord.Interaction) -> bool:
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used inside a server.",
                ephemeral=True
            )
            return False

        return True

    @configs.command(
        name="view",
        description="View the current server configuration."
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def view(self, interaction: discord.Interaction):
        if not await self.require_guild(interaction):
            return

        settings = self.get_settings(interaction.guild_id)
        guild = interaction.guild

        role = guild.get_role(settings["auto_role_id"]) if settings["auto_role_id"] else None
        welcome = guild.get_channel(settings["welcome_channel_id"]) if settings["welcome_channel_id"] else None
        logs = guild.get_channel(settings["log_channel_id"]) if settings["log_channel_id"] else None

        embed = self.make_embed(
            interaction,
            "⚙️ Server Configuration",
            "Current NodeMC member event settings.",
            discord.Color.blurple()
        )

        embed.add_field(
            name="🎭 Automatic Role",
            value=role.mention if role else "`Not configured`",
            inline=False
        )
        embed.add_field(
            name="👋 Welcome Channel",
            value=welcome.mention if isinstance(welcome, discord.TextChannel) else "`Not configured`",
            inline=False
        )
        embed.add_field(
            name="📋 Member Log Channel",
            value=logs.mention if isinstance(logs, discord.TextChannel) else "`Not configured`",
            inline=False
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @configs.command(
        name="autorole",
        description="Set the role assigned to new members."
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def autorole(self, interaction: discord.Interaction, role: discord.Role):
        if not await self.require_guild(interaction):
            return

        guild = interaction.guild

        if role.is_default() or role.managed:
            await interaction.response.send_message(
                "That role cannot be assigned as an automatic role.",
                ephemeral=True
            )
            return

        bot_member = guild.me
        if bot_member is None or role >= bot_member.top_role:
            await interaction.response.send_message(
                "I cannot assign that role. Move my highest role above it in Server Settings.",
                ephemeral=True
            )
            return

        self.update_setting(guild.id, "auto_role_id", role.id)

        embed = self.make_embed(
            interaction,
            "✅ Automatic Role Updated",
            f"New members will receive {role.mention} when they join.",
            discord.Color.green()
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @configs.command(
        name="welcome",
        description="Set the channel for welcome messages."
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def welcome(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if not await self.require_guild(interaction):
            return

        self.update_setting(
            interaction.guild_id,
            "welcome_channel_id",
            channel.id
        )

        embed = self.make_embed(
            interaction,
            "✅ Welcome Channel Updated",
            f"Welcome messages will be sent to {channel.mention}.",
            discord.Color.green()
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @configs.command(
        name="logs",
        description="Set the channel for member join and leave logs."
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def logs(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if not await self.require_guild(interaction):
            return

        self.update_setting(
            interaction.guild_id,
            "log_channel_id",
            channel.id
        )

        embed = self.make_embed(
            interaction,
            "✅ Member Log Channel Updated",
            f"Join and leave logs will be sent to {channel.mention}.",
            discord.Color.green()
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @configs.command(
        name="reset",
        description="Clear a server configuration setting."
    )
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.choices(
        setting=[
            app_commands.Choice(name="Automatic Role", value="autorole"),
            app_commands.Choice(name="Welcome Channel", value="welcome"),
            app_commands.Choice(name="Member Log Channel", value="logs")
        ]
    )
    async def reset(
        self,
        interaction: discord.Interaction,
        setting: app_commands.Choice[str]
    ):
        if not await self.require_guild(interaction):
            return

        columns = {
            "autorole": "auto_role_id",
            "welcome": "welcome_channel_id",
            "logs": "log_channel_id"
        }

        self.update_setting(
            interaction.guild_id,
            columns[setting.value],
            None
        )

        embed = self.make_embed(
            interaction,
            "🗑️ Configuration Reset",
            f"**{setting.name}** has been cleared.",
            discord.Color.orange()
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @view.error
    @autorole.error
    @welcome.error
    @logs.error
    @reset.error
    async def configs_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError
    ):
        if isinstance(error, app_commands.MissingPermissions):
            message = "You need the **Administrator** permission to use this command."
        else:
            message = "Something went wrong while processing the configuration."

        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(ConfigsCommand(bot))
