import asyncio
import logging

import discord
from discord import app_commands
from discord.ext import commands


class TicketButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Open a Ticket",
        style=discord.ButtonStyle.blurple,
        emoji="<:skinflow_ticket:1146808977343135766>",
        custom_id="button:openticket",
    )
    async def open_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.defer(ephemeral=True)

        opener = interaction.user

        guild = interaction.guild
        ticket_category_id = 1146488953759875112

        ticket_category = discord.utils.get(guild.categories, id=ticket_category_id)

        guild = interaction.guild
        for channel in guild.channels:
            if isinstance(channel, discord.TextChannel):
                if channel.topic == f"{interaction.user}'s Ticket":
                    await interaction.followup.send(
                        "You already have a ticket open", ephemeral=True
                    )
                    return

        permission_overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(
                read_messages=True, send_messages=True, embed_links=True
            ),
        }

        ticket_channel = await ticket_category.create_text_channel(
            name=f"Ticket: {interaction.user}",
            topic=f"{interaction.user}'s Ticket",
            overwrites=permission_overwrites,
        )

        TicketEmbed2 = discord.Embed(
            description="Someone will be with you shortly.",
            color=0x444A8D,
        )
        TicketEmbed2.add_field(
            name='To close the ticket, click "Close the Ticket" below.', value="Thanks!"
        )
        TicketEmbed2.set_footer(text="SkinFlow - Instantly Sell Your CSGO Skins")

        await ticket_channel.send(
            content=f"Thank you for opening a ticket {interaction.user.mention},\n(||<@&1152597297599893525>||)",
            embed=TicketEmbed2,
            view=CloseButton(opener),
        )
        await interaction.followup.send(
            "Your ticket was successfully created!", ephemeral=True
        )


class CloseButton(discord.ui.View):
    def __init__(self, opener):
        super().__init__(timeout=None)
        self.opener = opener

    @discord.ui.button(
        label="Close the Ticket",
        style=discord.ButtonStyle.blurple,
        emoji="<:skinflow_lock:1146810034261598290>",
        custom_id="button:closeticket",
    )
    async def close_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.defer(ephemeral=True)

        await interaction.followup.send(
            "Closing the ticket in a couple of seconds...", ephemeral=True
        )
        await asyncio.sleep(3)

        guild = interaction.guild

        permission_overwrites = {
            guild.default_role: discord.PermissionOverwrite(
                read_messages=False, send_messages=False
            ),
            self.opener: discord.PermissionOverwrite(
                read_messages=True, send_messages=False
            ),
        }

        await interaction.channel.edit(overwrites=permission_overwrites)

        closeEmbed = discord.Embed(
            title="Ticket Closed",
            description=f"This ticket was closed by {interaction.user.mention}\nOnly Staff Members can send messages.",
            color=0xFF0000,
        )
        closeEmbed.set_footer(text="SkinFlow - Instantly Sell Your CSGO Skins")

        await interaction.channel.send(embed=closeEmbed, view=DeleteButton())


class DeleteButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Delete the Ticket",
        style=discord.ButtonStyle.red,
        emoji="<:skinflow_trash:1146810798992265318>",
        custom_id="button:deleteticket",
    )
    async def delete_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.guild_permissions.administrator:
            await interaction.response.defer(ephemeral=True)
            await interaction.followup.send(
                "Deleting the channel in a couple of seconds...", ephemeral=True
            )
            await asyncio.sleep(4)
            await interaction.channel.delete()
        else:
            await interaction.response.send_message(
                "Only administrators can use this button.", ephemeral=True
            )


class Tickets(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.logger = logging.getLogger(f"SkinFlow.{self.__class__.__name__}")
        self.bot = bot

    async def cog_load(self) -> None:
        view = TicketButton()
        self.bot.add_view(view)

    @app_commands.command(name="ticket", description="Sends the ticket Embed")
    async def slash_ticket(self, interaction: discord.Interaction):
        TicketEmbed2 = discord.Embed(
            title="SkinFlow Support",
            description="To create a ticket, press the button below.",
            color=0x444A8D,
        )
        TicketEmbed2.set_footer(text="SkinFlow - Instantly Sell Your CSGO Skins")
        ticket_embed_channel = interaction.channel
        await interaction.response.send_message(
            "Ticket Embed Successfully sent!", ephemeral=True
        )
        await ticket_embed_channel.send(embed=TicketEmbed2, view=TicketButton())


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Tickets(bot))
