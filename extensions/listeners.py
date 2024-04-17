import logging

import discord
from discord.ext import commands

from config import (announcements_role_id, events_role_id, giveaways_role_id,
                    member_role_id, mod_logs_channel_id, skinflow_server_id)

assignable_role_ids = [
    giveaways_role_id,
    announcements_role_id,
    events_role_id,
    member_role_id,
]


class Listeners(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.logger = logging.getLogger(f"SkinFlow.{self.__class__.__name__}")
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild:
            return

        if message.guild.id != skinflow_server_id:
            return

        if message.author.bot:
            return

        if isinstance(message.author, discord.Member):
            if message.author.guild_permissions.mention_everyone:
                return

            if any(
                r in message.author.roles
                for r in message.guild.roles[1:]
                if r.id not in assignable_role_ids
            ):
                return
            if "@everyone" in message.content or "@here" in message.content:
                await message.author.ban(
                    delete_message_days=1, reason="Attempted to @everyone."
                )

                mod_logs_channel = self.bot.get_channel(mod_logs_channel_id)
                await mod_logs_channel.send(
                    f"Banned {message.author.mention} for attempting to `@everyone` without any non-assignable roles."
                )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Listeners(bot))
