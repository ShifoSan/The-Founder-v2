import discord
from discord.ext import commands
import os
import settings
from dotenv import load_dotenv
from keep_alive import keep_alive

# Load environment variables
load_dotenv()

# Setup Intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=commands.when_mentioned, # Slash commands primarily, but prefix needed for some internals
            intents=intents,
            help_command=None, # We will implement our own help
            application_id=None # Will be auto-fetched
        )

    async def setup_hook(self):
        # Recursive cog loader
        for root, dirs, files in os.walk("cogs"):
            for file in files:
                if file.endswith(".py") and not file.startswith("__"):
                    # Convert file path to module path: cogs/moderation/admin -> cogs.moderation.admin
                    path = os.path.join(root, file)
                    module_path = path.replace(os.sep, ".")[:-3] # Remove .py

                    try:
                        await self.load_extension(module_path)
                        print(f"Loaded extension: {module_path}")
                    except Exception as e:
                        print(f"Failed to load extension {module_path}: {e}")

        # Sync commands to the specific GUILD_ID
        if settings.GUILD_ID:
            guild = discord.Object(id=settings.GUILD_ID)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            print(f"Synced commands to guild {settings.GUILD_ID}")
        else:
            print("GUILD_ID not found in settings.py, commands not synced!")

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print("Bot is ready!")

bot = MyBot()

if __name__ == '__main__':
    # Start the web server to keep the bot alive
    keep_alive()

    token = os.getenv("DISCORD_TOKEN")
    if not token or token == "your_token_here":
        print("Error: DISCORD_TOKEN not found in .env")
    else:
        bot.run(token)
