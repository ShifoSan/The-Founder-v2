import discord
from discord.ext import commands
from discord import app_commands
import settings
import os
import google.generativeai as genai

class GeminiCore(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ai_enabled = True
        self.chat_sessions = {} # {channel_id: chat_session}

        api_key = os.getenv("GEMINI_API_KEY")
        if api_key and api_key != "your_key_here":
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash-lite')
        else:
            print("Warning: GEMINI_API_KEY not found or invalid.")
            self.model = None

    def get_system_instructions(self):
        try:
            with open("System-Instructions", "r") as f:
                return f.read()
        except:
            return "You are a helpful assistant."

    def get_session(self, channel_id):
        if channel_id not in self.chat_sessions:
            # Initialize new session with system instructions as history or context
            # "System instructions will be in a seperate file ... The bot must follow it."
            # Gemini Python SDK supports system_instruction in GenerativeModel constructor usually,
            # but let's stick to sending it as the first message or context if constructor doesn't support it in this version.
            # Actually, `GenerativeModel` supports `system_instruction` in newer versions.
            # Or we can just start chat with history.

            instructions = self.get_system_instructions()

            # Re-initialize model with system instruction if possible or prepend it.
            # Since we initialized model in __init__ without instructions (dynamic reading),
            # We might want to construct a new model for the session or just use history.
            # Let's use history.

            history = [
                {"role": "user", "parts": [instructions]},
                {"role": "model", "parts": ["Understood. I will follow these instructions."]}
            ]
            self.chat_sessions[channel_id] = self.model.start_chat(history=history)

        return self.chat_sessions[channel_id]

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        # Check if AI is enabled and correct channel
        if not self.ai_enabled:
            return

        if message.channel.id != settings.AI_CHANNEL:
            return

        if not self.model:
            return

        async with message.channel.typing():
            try:
                session = self.get_session(message.channel.id)
                response = await session.send_message_async(message.content)

                # Split message if too long (Discord limit 2000)
                text = response.text
                if len(text) > 2000:
                    for i in range(0, len(text), 2000):
                        await message.channel.send(text[i:i+2000])
                else:
                    await message.channel.send(text)
            except Exception as e:
                print(f"Gemini Error: {e}")
                await message.channel.send("I encountered an error processing your request.")

    # Helper for config cog
    def toggle_ai(self, enabled: bool):
        self.ai_enabled = enabled

async def setup(bot):
    await bot.add_cog(GeminiCore(bot))
