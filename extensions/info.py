import logging

import discord
from discord.ext import commands


class Info(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.logger = logging.getLogger(f"Skinflow.{self.__class__.__name__}")
        self.bot = bot

    @commands.hybrid_command(name="ranks", aliases=["ranking", "skinflow_ranks"])
    async def ranks(self, ctx: commands.Context):
        await ctx.send(file=discord.File("images/skinflow_ranks.png"))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Info(bot))
