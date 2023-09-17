import datetime
import logging

import discord
from discord import app_commands
from discord.ext import commands

from config import DISBOARD_BOT_ID


class Bump(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.logger = logging.getLogger(f"SkinFlow.{self.__class__.__name__}")
        self.bot = bot
        self.next_bump_dt = None

    def has_embed_and_description(self, msg: discord.Message) -> bool:
        return bool(msg.embeds) and msg.embeds[0].description is not None

    def is_bump_interaction(self, msg: discord.Message) -> bool:
        return msg.interaction is not None and msg.interaction.name == "bump"

    def is_bump_message(self, msg: discord.Message) -> bool:
        return (
            msg.author.id == DISBOARD_BOT_ID
            and self.is_bump_interaction(msg)
            and self.has_embed_and_description(msg)
        )

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        channel = msg.channel

        if not msg.guild:
            return

        if not self.is_bump_message(msg):
            return

        if not msg.interaction:
            return

        await channel.send(
            f"Thank you for bumping {msg.interaction.user.display_name}, I'll ping you when you can bump again!"
        )

        two_hours_future = discord.utils.utcnow() + datetime.timedelta(hours=2)
        self.next_bump_dt = two_hours_future

        await discord.utils.sleep_until(two_hours_future)

        embed = discord.Embed(
            title="Bump is avaliable again!",
            description="Please type `/bump` again!",
            color=0x444A8D,
        )
        embed.add_field(
            name=" Bumping will help us to stay at the top of the Counter-Strike Tags on Disboard, so that more people can find SkinFlow!.",
            value="Thank you so much for your help <:sfheart:1148972539746459740>",
        )

        await channel.send(content=f"{msg.interaction.user.mention}", embed=embed)

    @app_commands.command(
        name="nextbump", description="Tells you when the next bump is"
    )
    async def slash_nextbump(self, interaction: discord.Interaction):
        if not self.next_bump_dt:
            return await interaction.response.send_message(
                "Haven't seen a previous bump"
            )

        await interaction.response.send_message(
            f"{discord.utils.format_dt(self.next_bump_dt)}"
        )

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Bump(bot))
