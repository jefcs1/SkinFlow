import datetime
import logging

import discord
from discord import app_commands
from discord.ext import commands
import json

class Twitter(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.logger = logging.getLogger(f"Skinflow.{self.__class__.__name__}")
        self.bot = bot

    twitter_stream_endpoint = 'https://api.twitter.com/2/tweets/search/stream'


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Twitter(bot))
