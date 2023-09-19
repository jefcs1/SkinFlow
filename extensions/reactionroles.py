import logging

import discord
from discord import app_commands
from discord.ext import commands

reaction_channel_id = 1153799452251930634
reaction_roles = {
    # Emoji ID: Role ID
    1153439071050399754: 1153436634486943784,
    1153439147927814144: 1153436552853213225,
    1153439113752612865: 1153436643869593750,
}

class ReactionRoles(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.logger = logging.getLogger(f"SkinFlow.{self.__class__.__name__}")
        self.bot = bot
        
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.channel_id != reaction_channel_id:
            return
        if payload.emoji.id in reaction_roles:
            emoji = payload.emoji.id
            guild = self.bot.get_guild(payload.guild_id)
            role = guild.get_role(reaction_roles[emoji])
            member = guild.get_member(payload.user_id)
            await member.add_roles(role)
        else:
            return

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if payload.channel_id != reaction_channel_id:
            return
        if payload.emoji.id in reaction_roles:
            emoji = payload.emoji.id
            guild = self.bot.get_guild(payload.guild_id)
            role = guild.get_role(reaction_roles[emoji])
            member = guild.get_member(payload.user_id)
            await member.remove_roles(role)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ReactionRoles(bot))
