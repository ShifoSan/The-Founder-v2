import discord
from discord import app_commands
from discord.ext import commands
import settings

class UtilityTools(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def is_staff_or_admin(self, interaction: discord.Interaction):
        if interaction.user.guild_permissions.administrator:
            return True
        if settings.STAFF_ROLE_ID in [r.id for r in interaction.user.roles]:
            return True
        return False

    @app_commands.command(name="poll", description="Create a poll.")
    async def poll(self, interaction: discord.Interaction, question: str, option_1: str, option_2: str = None, option_3: str = None, option_4: str = None, option_5: str = None, option_6: str = None, option_7: str = None, option_8: str = None, option_9: str = None, option_10: str = None):
        if not self.is_staff_or_admin(interaction):
            await interaction.response.send_message("You do not have permission.", ephemeral=True)
            return

        options = [opt for opt in [option_1, option_2, option_3, option_4, option_5, option_6, option_7, option_8, option_9, option_10] if opt]

        if len(options) < 2:
            await interaction.response.send_message("You need at least 2 options for a poll.", ephemeral=True)
            return

        emoji_numbers = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

        description = ""
        for i, option in enumerate(options):
            description += f"{emoji_numbers[i]} {option}\n"

        embed = discord.Embed(title=question, description=description, color=discord.Color.gold())
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)

        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()

        for i in range(len(options)):
            await message.add_reaction(emoji_numbers[i])

    @app_commands.command(name="ping", description="Check bot latency.")
    async def ping(self, interaction: discord.Interaction):
        # Allow Staff/Admin
        if not self.is_staff_or_admin(interaction):
             await interaction.response.send_message("You do not have permission.", ephemeral=True)
             return

        latency = round(self.bot.latency * 1000)
        await interaction.response.send_message(f"Pong! 🏓 {latency}ms", ephemeral=True)

    @app_commands.command(name="help", description="Show help information.")
    async def help(self, interaction: discord.Interaction):
        embed = discord.Embed(title="Bot Help", description="Here are the available commands:", color=discord.Color.blue())

        # We can dynamically list commands, but for now hardcoding categories is cleaner for the embed structure requested.

        embed.add_field(name="Moderation (Staff)", value="`/timeout`, `/purge`, `/warn`, `/say`, `/announce`", inline=False)
        embed.add_field(name="Admin Controls", value="`/automod-toggle`, `/custom-status-list`, `/custom-status-manage`, `/custom-status-rotation`, `/set-logs-channel`", inline=False)
        embed.add_field(name="Utility", value="`/poll`, `/ping`, `/welcome`, `/leave`", inline=False)
        embed.add_field(name="AI", value="Just chat in the AI channel!", inline=False)

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(UtilityTools(bot))
