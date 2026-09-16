import discord
from discord import app_commands
from discord.ext import commands

class UserInfo(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="userinfo", description="Fetches all available profile and server information for a user.")
    @app_commands.describe(target="The user to lookup (defaults to you)")
    async def userinfo(self, interaction: discord.Interaction, target: discord.User = None):
        target_user = target or interaction.user
        
        embed = discord.Embed(
            title="👤 User Information",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=target_user.display_avatar.url)
        
        embed.add_field(name="Username", value=f"`{target_user.name}`", inline=True)
        embed.add_field(name="User ID", value=f"`{target_user.id}`", inline=True)
        embed.add_field(name="Is Bot?", value=f"`{'Yes' if target_user.bot else 'No'}`", inline=True)
        
        created_timestamp = f"<t:{int(target_user.created_at.timestamp())}:R>"
        embed.add_field(name="Account Created", value=created_timestamp, inline=True)

        if interaction.guild:
            member = interaction.guild.get_member(target_user.id)
            
            if member:
                embed.title = f"👥 Member Information — {member.display_name}"
                embed.color = member.color if member.color != discord.Color.default() else discord.Color.blue()
                
                joined_timestamp = f"<t:{int(member.joined_at.timestamp())}:R>"
                embed.add_field(name="Joined Server", value=joined_timestamp, inline=True)
                
                if member.premium_since:
                    boost_timestamp = f"<t:{int(member.premium_since.timestamp())}:R>"
                    embed.add_field(name="Boosting Server Since", value=boost_timestamp, inline=True)
                else:
                    embed.add_field(name="Server Booster?", value="`No`", inline=True)

                roles = [role.mention for role in member.roles if role != interaction.guild.default_role]
                roles_display = ", ".join(roles) if roles else "None"
                if len(roles_display) > 1024:
                    roles_display = f"{len(roles)} roles (Too many to list)"
                embed.add_field(name=f"Roles ({len(roles)})", value=roles_display, inline=False)

                key_perms = []
                if member.guild_permissions.administrator:
                    key_perms.append("Administrator")
                if member.guild_permissions.manage_guild:
                    key_perms.append("Manage Server")
                if member.guild_permissions.manage_roles:
                    key_perms.append("Manage Roles")
                if member.guild_permissions.manage_channels:
                    key_perms.append("Manage Channels")
                if member.guild_permissions.kick_members:
                    key_perms.append("Kick Members")
                if member.guild_permissions.ban_members:
                    key_perms.append("Ban Members")
                
                perms_display = ", ".join(key_perms) if key_perms else "None"
                embed.add_field(name="Administrator Permissions", value=perms_display, inline=False)
            else:
                embed.description = "⚠️ *This user is not a member of this server. Showing global profile data only.*"
        else:
            embed.description = "📬 *Executed inside Direct Messages. Showing global profile data only.*"

        embed.set_footer(
            text=f"Requested by {interaction.user.name}", 
            icon_url=interaction.user.display_avatar.url
        )

        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(UserInfo(bot))
