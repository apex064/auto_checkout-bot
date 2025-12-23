## main.py
import asyncio
from utils.discord import DiscordBot
from dispatcher import BotDispatcher
from utils.config import load_config, get_bot_config
from utils.driver_setup import setup_chromedriver

# Setup ChromeDriver (one-time check/update)
setup_chromedriver()

# Load full config
config = load_config()
bot_config = get_bot_config(config)

# Get Discord token directly from full config
DISCORD_TOKEN = config.get("discord_token")  # <-- fix here 

# Initialize dispatcher
dispatcher = BotDispatcher() 

# Initialize Discord bot 
discord_bot = DiscordBot(DISCORD_TOKEN, dispatcher) 

# Run bot
discord_bot.run()
