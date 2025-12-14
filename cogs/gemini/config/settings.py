import discord
from discord import app_commands
from discord.ext import commands
import settings

class GeminiConfig(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def is_admin(self, interaction: discord.Interaction):
        return interaction.user.guild_permissions.administrator

    @app_commands.command(name="ai-toggle", description="Turn the AI chat on or off.")
    async def ai_toggle(self, interaction: discord.Interaction):
        if not self.is_admin(interaction):
            await interaction.response.send_message("You do not have permission.", ephemeral=True)
            return

        gemini_cog = self.bot.get_cog("GeminiCore")
        if gemini_cog:
            new_state = not gemini_cog.ai_enabled
            gemini_cog.toggle_ai(new_state)
            state_str = "enabled" if new_state else "disabled"
            await interaction.response.send_message(f"AI chat has been {state_str}.", ephemeral=True)
        else:
            await interaction.response.send_message("GeminiCore cog not loaded.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(GeminiConfig(bot))
