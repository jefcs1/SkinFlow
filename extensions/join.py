import logging
import random
import sys

import discord
from discord import app_commands
from discord.ext import commands


class Join(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.logger = logging.getLogger(f"EmployeeBot.{self.__class__.__name__}")
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        TESTING = sys.platform == "darwin"
        if TESTING:
            return

        channel = await self.bot.fetch_channel(1061365944905105554)
        welcome_messages = [
            f"Everyone welcome {member.mention} to the SkinFlow discord!",
            f"Welcome {member.mention}, it's good to have you!",
            f"Hi {member.mention}, welcome to the server!",
            f"{member.mention} just showed up, make them feel welcome!>",
            f"Say hello to our newest member, {member.mention}!",
            f"Welcome {member.mention}, we hope you brought pizza!",
            f"Welcome to the SkinFlow community {member.mention}!",
            f"Howdy {member.mention}, we're glad you joined us!",
        ]
        message = random.choice(welcome_messages)
        await channel.send(message)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Join(bot))
