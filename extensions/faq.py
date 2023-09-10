import asyncio
import logging

import discord
from discord import app_commands
from discord.ext import commands, tasks

skinflow_faq = {
    "How do I get access to the Trading Channel?": {
        "title": "In order to get access to the Trading Channel, you need the Trader Role.",
        "description": "The <@&1146543213159653386> role is a linked role.\nTo get it, go to `Server Settings -> Linked Roles`,\nand then select the Role!",
    },
    "How long does it take to receive my money?": {
        "title": "Payment times differ depending on the chosen withdrawal method",
        "description": f"We strive to process payments within 15 minutes although some withdrawals can be delayed for a bit longer (mostly PayPal).",
    },
    "Why can I not trade some skins on Skinflow?": {
        "title": "Some of the reasons why your skin might not be tradable on our website are:",
        "description": "> 1.) - Your skin's price is too low for our inventory. We do not purchase skins below a certain threshold amount.\n> 2.) - Your skin's price is too volatile or not liquid enough. We do not purchase skins which do not have an active market around them.\n> 3.) - Your skin might just be trade locked. In this case, wait out the 1 to 8 days timer before transacting with it on our website.",
    },
}


class PersistentViewFAQ(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(FAQsDropDown())


class FAQsDropDown(discord.ui.Select):
    def __init__(self):

        options = []
        for label, value in skinflow_faq.items():
            options.append(discord.SelectOption(label=label, value=label))

        super().__init__(
            placeholder="Click here to see our FAQs",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="persistentview:faq"
        )

    async def callback(self, interaction: discord.Interaction):
        selected_value = interaction.data["values"][0]
        selected_question = (skinflow_faq)[selected_value]
        selected_title = selected_question["title"]
        selected_description = selected_question["description"]

        embed = discord.Embed(
            title=f"{selected_title}",
            description=f"{selected_description}",
            color=0x44A8D,
        )
        embed.set_footer(text="SkinFlow - Instantly Sell your CSGO Skins")

        await interaction.response.send_message(embed=embed, ephemeral=True)


class FAQ(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.logger = logging.getLogger(f"SkinFlow.{self.__class__.__name__}")
        self.bot = bot

    @app_commands.command(name="faq", description="Sends the FAQ Dropdown")
    async def faq(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "Sorry, only admins can use this command."
            )
            return
        await interaction.response.send_message(
            "Sending the FAQ Dropdown...", ephemeral=True
        )

        await asyncio.sleep(2)

        channel = interaction.channel
        faq_embed = discord.Embed(
            title="SkinFlow FAQs",
            description="These are the Frequently Asked Questions regarding SkinFlow and this server.\nUse the dropdown below to see the answers to these questions.",
            color=0x44A8D,
        )
        faq_embed.set_footer(text="SkinFlow - Instantly Sell Your CSGO Skins")
        await channel.send(embed=faq_embed, view=PersistentViewFAQ())


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(FAQ(bot))
