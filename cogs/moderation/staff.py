import discord
from discord import app_commands
from discord.ext import commands
import settings
import datetime

class StaffCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.automod_enabled = True # Default enabled as per prompt? "A passive Auto-mod feature..."
        # Actually prompt says: "/automod-toggle [custom words (true or false)]"
        # and "AutoMod custom banned words should be hardcoded".
        # I'll default it to True.

    def is_staff_or_admin(self, interaction: discord.Interaction):
        # Check for Admin permission or Staff Role
        if interaction.user.guild_permissions.administrator:
            return True
        if settings.STAFF_ROLE_ID in [r.id for r in interaction.user.roles]:
            return True
        return False

    async def log_action(self, guild, action, user, target, reason, channel=None):
        log_channel_id = settings.MODLOG_CHANNEL
        # Check if dynamic override exists (will be implemented in Admin Controls)
        # For now, use settings.MODLOG_CHANNEL
        # Note: If I want dynamic settings shared across cogs, I might need a shared state or singleton.
        # But for this simple bot, reading from settings.py (which is static) and maybe a bot variable is enough.
        # Admin controls need to update something persistent or runtime.
        # Since I can't use a database, runtime variable in `bot` is best.

        # Check if bot has a shared state for log channel
        if hasattr(self.bot, 'modlog_channel_id'):
            log_channel_id = self.bot.modlog_channel_id

        log_channel = guild.get_channel(log_channel_id)
        if not log_channel:
            return

        embed = discord.Embed(title="Moderation Action", timestamp=datetime.datetime.now())
        embed.add_field(name="Action", value=action, inline=True)
        embed.add_field(name="Moderator", value=user.mention, inline=True)
        embed.add_field(name="Target", value=target.mention if target else "N/A", inline=True)
        if channel:
            embed.add_field(name="Channel", value=channel.mention, inline=True)
        embed.add_field(name="Reason", value=reason or "No reason provided", inline=False)

        await log_channel.send(embed=embed)

    @app_commands.command(name="timeout", description="Temporarily prevent a user from chatting.")
    @app_commands.describe(user="The user to timeout", time="Time in minutes (default 5)")
    async def timeout(self, interaction: discord.Interaction, user: discord.Member, time: int = 5):
        if not self.is_staff_or_admin(interaction):
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        try:
            duration = datetime.timedelta(minutes=time)
            await user.timeout(duration, reason=f"Timeout by {interaction.user.name}")
            await interaction.response.send_message(f"Timed out {user.mention} for {time} minutes.")
            await self.log_action(interaction.guild, "Timeout", interaction.user, user, f"{time} minutes", interaction.channel)
        except Exception as e:
            await interaction.response.send_message(f"Failed to timeout user: {e}", ephemeral=True)

    @app_commands.command(name="purge", description="Delete recent messages.")
    @app_commands.describe(amount="Number of messages", till_message="Message ID to stop at", from_user="Filter by user", from_bot="Filter by bot messages")
    async def purge(self, interaction: discord.Interaction, amount: int, till_message: str = None, from_user: discord.Member = None, from_bot: bool = False):
        if not self.is_staff_or_admin(interaction):
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        def check(m):
            if from_user and m.author != from_user:
                return False
            if from_bot and not m.author.bot:
                return False
            return True

        # Logic for 'till_message'
        after = None
        if till_message:
            try:
                after = await interaction.channel.fetch_message(int(till_message))
            except:
                pass # Invalid ID, ignore or handle error

        deleted = await interaction.channel.purge(limit=amount, check=check, after=after)

        await interaction.followup.send(embed=discord.Embed(description=f"Purged {len(deleted)} messages. Action by {interaction.user.mention}"))
        await self.log_action(interaction.guild, "Purge", interaction.user, None, f"{len(deleted)} messages deleted", interaction.channel)

    @app_commands.command(name="warn", description="Warn a user.")
    async def warn(self, interaction: discord.Interaction, user: discord.Member, reason: str):
        if not self.is_staff_or_admin(interaction):
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        await interaction.response.send_message(f"{user.mention} has been warned for: {reason}")
        await self.log_action(interaction.guild, "Warn", interaction.user, user, reason, interaction.channel)

    @app_commands.command(name="say", description="Echo message with optional attachment.")
    async def say(self, interaction: discord.Interaction, text: str, file: discord.Attachment = None):
        if not self.is_staff_or_admin(interaction):
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        files = []
        if file:
            files.append(await file.to_file())

        await interaction.channel.send(content=text, files=files)
        await interaction.response.send_message("Message sent!", ephemeral=True)
        # Note: /say does not need logging as per requirements.

    @app_commands.command(name="announce", description="Create an announcement.")
    async def announce(self, interaction: discord.Interaction):
        if not self.is_staff_or_admin(interaction):
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        await interaction.response.send_modal(AnnouncementModal())

    # AutoMod Listener
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        # Exclude Staff/Admin from AutoMod
        is_staff = False
        if message.author.guild_permissions.administrator:
            is_staff = True
        elif settings.STAFF_ROLE_ID in [r.id for r in message.author.roles]:
            is_staff = True

        if is_staff:
            return

        # Check if AutoMod is enabled
        # We need a way to check the toggle state.
        # I'll check self.bot.automod_enabled (set by Admin cog) or default to self.automod_enabled
        enabled = getattr(self.bot, 'automod_enabled', self.automod_enabled)

        if not enabled:
            return

        # Check content
        content_lower = message.content.lower()
        if any(word.lower() in content_lower for word in settings.BANNED_WORDS):
            await message.delete()
            warning_msg = await message.channel.send(f"{message.author.mention}, that word is not allowed here!")
            await self.log_action(message.guild, "AutoMod Delete", self.bot.user, message.author, f"Used banned word in message: {message.content}", message.channel)
            # Delete warning after a few seconds to reduce clutter
            await warning_msg.delete(delay=5)


class AnnouncementModal(discord.ui.Modal, title="Make an Announcement"):
    a_title = discord.ui.TextInput(label="Title", style=discord.TextStyle.short)
    body = discord.ui.TextInput(label="Body", style=discord.TextStyle.paragraph)
    footer = discord.ui.TextInput(label="Footer", style=discord.TextStyle.short)

    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(title=self.a_title.value, description=self.body.value, color=discord.Color.blue())
        embed.set_footer(text=self.footer.value)
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)

        if settings.ANNOUNCE_THUMBNAIL_URL and settings.ANNOUNCE_THUMBNAIL_URL.startswith("http"):
             embed.set_thumbnail(url=settings.ANNOUNCE_THUMBNAIL_URL)

        await interaction.channel.send(embed=embed)
        await interaction.response.send_message("Announcement sent!", ephemeral=True)


async def setup(bot):
    await bot.add_cog(StaffCommands(bot))
