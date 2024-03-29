import logging

import discord  # type: ignore
from discord import app_commands
from discord.ext import commands


class Fun(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.logger = logging.getLogger(f"Skinflow.{self.__class__.__name__}")
        self.bot = bot

    @app_commands.command(name="bing", description="For MaDiT")
    async def slash_bing(self, interaction: discord.Interaction):
        await interaction.response.send_message("Chilling! :icecream:")
    
    @commands.command(aliases=["site"])
    async def website(self, ctx):
        await ctx.send("<https://skinflow.gg?referral=DISCORD>")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Fun(bot))
