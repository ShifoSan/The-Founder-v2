import discord
from discord import app_commands
from discord.ext import commands
import settings

class WelcomeLeave(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.welcome_enabled = True
        self.leave_enabled = True

    def is_admin(self, interaction: discord.Interaction):
        return interaction.user.guild_permissions.administrator

    @app_commands.command(name="welcome", description="Enable or disable welcome messages.")
    async def welcome(self, interaction: discord.Interaction, enable: bool):
        if not self.is_admin(interaction):
            await interaction.response.send_message("You do not have permission.", ephemeral=True)
            return
        self.welcome_enabled = enable
        await interaction.response.send_message(f"Welcome messages {'enabled' if enable else 'disabled'}.", ephemeral=True)

    @app_commands.command(name="leave", description="Enable or disable leave messages.")
    async def leave(self, interaction: discord.Interaction, enable: bool):
        if not self.is_admin(interaction):
            await interaction.response.send_message("You do not have permission.", ephemeral=True)
            return
        self.leave_enabled = enable
        await interaction.response.send_message(f"Leave messages {'enabled' if enable else 'disabled'}.", ephemeral=True)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if not self.welcome_enabled:
            return

        channel = member.guild.get_channel(settings.WELCOME_CHANNEL_ID)
        if channel:
            # Create a beautiful embed
            embed = discord.Embed(
                title=f"Welcome to {member.guild.name}!",
                description=f"Hello {member.mention}, we are glad to have you here!",
                color=discord.Color.green()
            )
            embed.add_field(name="Member Count", value=str(member.guild.member_count))
            if member.avatar:
                embed.set_thumbnail(url=member.avatar.url)

            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if not self.leave_enabled:
            return

        channel = member.guild.get_channel(settings.LEAVE_CHANNEL_ID)
        if channel:
            msg = f"Goodbye **{member.name}**. We will miss you from **{member.guild.name}**. Now we are {member.guild.member_count} members."
            await channel.send(msg)

async def setup(bot):
    await bot.add_cog(WelcomeLeave(bot))
