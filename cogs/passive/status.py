import discord
from discord.ext import commands, tasks
import settings
import itertools

class PassiveStatus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.statuses = itertools.cycle(settings.CUSTOM_STATUSES)
        self.rotation_time = 10  # Default rotation time in seconds
        self.is_rotating = True
        self.status_loop.start()

    def cog_unload(self):
        self.status_loop.cancel()

    @tasks.loop(seconds=10)
    async def status_loop(self):
        if self.is_rotating and settings.CUSTOM_STATUSES:
            next_status = next(self.statuses)
            await self.bot.change_presence(activity=discord.CustomActivity(name=next_status))

    @status_loop.before_loop
    async def before_status_loop(self):
        await self.bot.wait_until_ready()

    # Helper methods to be used by Admin controls
    def set_rotation_speed(self, seconds: int):
        self.rotation_time = seconds
        self.status_loop.change_interval(seconds=seconds)

    def set_rotation_state(self, enabled: bool):
        self.is_rotating = enabled
        if not enabled:
            # Maybe clear status or keep the last one?
            # Requirement says "Enable or disable custom statuses".
            # I will keep the last one displayed or I could clear it.
            # Let's just stop updating.
            pass

async def setup(bot):
    await bot.add_cog(PassiveStatus(bot))
