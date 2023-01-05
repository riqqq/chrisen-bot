# Importing libraries
import discord
import os
import asyncio
from discord.ext import commands
from dotenv import load_dotenv

# Load variables from .env file where BOT_TOKEN is stored
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Discord bot Initialization
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# Load cogs by looking for .py files in ./cogs folder
async def load():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')

# Call load() function and start the bot
async def main():
    await load()
    await bot.start(BOT_TOKEN)

asyncio.run(main())