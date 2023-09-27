import logging

import discord
from discord import app_commands
from discord.ext import commands


class Staff(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.logger = logging.getLogger(f"SkinFlow.{self.__class__.__name__}")
        self.bot = bot
        self.reaction_message = None
        self.reacted_users = set()  

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):

        if payload.message_id == self.reaction_message.id:
            user = self.bot.get_user(payload.user_id)
            if user.bot:
                return
            if user.id not in self.reacted_users:
                self.reacted_users.add(user.id)
            if user.id in self.reacted_users:
                channel = self.bot.get_channel(payload.channel_id)
                message = await channel.fetch_message(payload.message_id)
                emoji = str(payload.emoji)
                if emoji == '✅':
                    await message.remove_reaction("❌", user)
                elif emoji == '❌':
                    await message.remove_reaction("✅", user)

    @app_commands.command(name="question", description="Create a yes/no poll that users can react to")
    async def reaction(self, interaction:discord.Interaction, question: str):
        embed = discord.Embed(title=f"{question}", description="React with :white_check_mark: for yes!\n\nReact with :x: for no!", color=0x444a8d)
        await interaction.response.send_message(embed=embed)
        self.reaction_message = await interaction.original_response()
        await self.reaction_message.add_reaction('✅')
        await self.reaction_message.add_reaction('❌')

    @commands.command()
    async def kickunverified(self, ctx):
        msg = await ctx.send("Kicking losers...")
        guild = self.bot.get_guild(1061365943768469575)
        for member in guild.members:
            if len(member.roles) == 1:
                await member.kick(reason="Didn't complete verification")
        await msg.edit(content="Finished!")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Staff(bot))
