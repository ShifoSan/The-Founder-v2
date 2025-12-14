import discord
from discord import app_commands
from discord.ext import commands
import settings

class AdminControls(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def is_admin(self, interaction: discord.Interaction):
        return interaction.user.guild_permissions.administrator

    @app_commands.command(name="automod-toggle", description="Toggle AutoMod on or off.")
    async def automod_toggle(self, interaction: discord.Interaction, enabled: bool):
        if not self.is_admin(interaction):
            await interaction.response.send_message("You do not have permission.", ephemeral=True)
            return

        # Store state on the bot instance so StaffCommands cog can see it
        self.bot.automod_enabled = enabled
        state = "enabled" if enabled else "disabled"
        await interaction.response.send_message(f"AutoMod has been {state}.", ephemeral=True)

    @app_commands.command(name="custom-status-list", description="List active custom statuses.")
    async def custom_status_list(self, interaction: discord.Interaction):
        if not self.is_admin(interaction):
            await interaction.response.send_message("You do not have permission.", ephemeral=True)
            return

        statuses = "\n".join([f"{i+1}. {s}" for i, s in enumerate(settings.CUSTOM_STATUSES)])
        # Discord messages have 2000 char limit, truncate if needed
        if len(statuses) > 1900:
            statuses = statuses[:1900] + "..."

        await interaction.response.send_message(f"**Custom Statuses:**\n{statuses}", ephemeral=True)

    @app_commands.command(name="custom-status-manage", description="Enable or disable custom status rotation.")
    async def custom_status_manage(self, interaction: discord.Interaction, enable: bool):
        if not self.is_admin(interaction):
            await interaction.response.send_message("You do not have permission.", ephemeral=True)
            return

        passive_cog = self.bot.get_cog("PassiveStatus")
        if passive_cog:
            passive_cog.set_rotation_state(enable)
            state = "enabled" if enable else "disabled"
            await interaction.response.send_message(f"Custom status rotation {state}.", ephemeral=True)
        else:
            await interaction.response.send_message("PassiveStatus cog not loaded.", ephemeral=True)

    @app_commands.command(name="custom-status-rotation", description="Set rotation time in seconds.")
    async def custom_status_rotation(self, interaction: discord.Interaction, seconds: int):
        if not self.is_admin(interaction):
            await interaction.response.send_message("You do not have permission.", ephemeral=True)
            return

        passive_cog = self.bot.get_cog("PassiveStatus")
        if passive_cog:
            passive_cog.set_rotation_speed(seconds)
            await interaction.response.send_message(f"Rotation time set to {seconds} seconds.", ephemeral=True)
        else:
            await interaction.response.send_message("PassiveStatus cog not loaded.", ephemeral=True)

    @app_commands.command(name="set-logs-channel", description="Set the moderation logs channel.")
    async def set_logs_channel(self, interaction: discord.Interaction, channel: discord.TextChannel, toggle: bool):
        if not self.is_admin(interaction):
            await interaction.response.send_message("You do not have permission.", ephemeral=True)
            return

        if toggle:
            self.bot.modlog_channel_id = channel.id
            await interaction.response.send_message(f"Moderation logs will be sent to {channel.mention}.", ephemeral=True)
        else:
            # Revert to default or disable?
            # Prompt says "toggle (enable or disable)".
            # If disabled, maybe stop logging or revert to hardcoded?
            # I'll set it to None to disable logging, or revert to settings.MODLOG_CHANNEL?
            # Prompt phrasing "Set any channel as moderation logs channel ... [toggle (enable or disable]"
            # This implies enabling logging in that channel, or disabling logging.
            self.bot.modlog_channel_id = None
            await interaction.response.send_message("Moderation logging disabled (or reverted).", ephemeral=True)

async def setup(bot):
    await bot.add_cog(AdminControls(bot))
