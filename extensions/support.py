import asyncio
import logging
import os
import uuid

import aiofiles
import chat_exporter
import discord
from discord import app_commands
from discord.ext import commands

from config import save_directory

ticket_reasons = [
    "I want to know how long payments take",
    "I have not recieved my payment",
    "I won a giveaway",
    "I sent my items but my status says declined",
    "I want to purchase an item from Skinflow",
]


class TransactionID(discord.ui.Modal, title="TransactionID"):
    transaction_id = discord.ui.TextInput(
        label="Provide your Transaction ID.",
        style=discord.TextStyle.long,
        placeholder="Please paste your transaction ID in this box...\nDon't know how to get it? Check out #FAQ!",
        required=True,
        max_length=100,
    )

    def __init__(self, reason, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.reason = reason

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            f"Thank you, creating your ticket now...", ephemeral=True
        )
        await open_ticket(
            interaction.user, interaction.guild, self.reason, self.transaction_id.value
        )
        await interaction.edit_original_response(content="Ticket created!")


class SteamID(discord.ui.Modal, title="SteamID"):
    steam_id = discord.ui.TextInput(
        label="Steam ID",
        style=discord.TextStyle.long,
        placeholder="Please give us your steam id...",
        required=True,
        max_length=50,
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            f"Thank you, creating your ticket now...", ephemeral=True
        )
        reason = "I won a giveaway"
        await open_ticket(
            interaction.user, interaction.guild, reason, self.steam_id.value
        )
        await interaction.edit_original_response(content="Ticket created!")


class SupportButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Get Support",
        style=discord.ButtonStyle.blurple,
        emoji="<:skinflow_ticket:1146808977343135766>",
        custom_id="button:startsupport",
    )
    async def open_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.defer(ephemeral=True)
        embed = discord.Embed(
            title="Please choose what you need support for:",
            description="",
            color=0x444A8D,
        )
        await interaction.followup.send(
            embed=embed, view=PersistentViewReasons(), ephemeral=True
        )


class PersistentViewReasons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ReasonsDropDown())


class ReasonsDropDown(discord.ui.Select):
    def __init__(self):
        options = []
        for value in ticket_reasons:
            options.append(discord.SelectOption(label=value, value=value))

        super().__init__(
            placeholder="Choose a Support Reason",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="persistentview:reasons",
        )

    async def callback(self, interaction: discord.Interaction):
        selected_reason = interaction.data["values"][0]
        if selected_reason == "I want to know how long payments take":
            embed = discord.Embed(
                title="How long do payments take?",
                description="If you are withdrawing **crypto**, the payment usually takes less than an hour.\nIf you are withdrawing through **PayPal**, it usually takes 8-15 hours.",
                color=0x444A8D,
            )
            await interaction.response.send_message(embed=embed)
        if selected_reason == "I have not recieved my payment":
            result = await check_tickets(
                interaction.guild, interaction.user, selected_reason
            )
            if result == True:
                await interaction.response.send_message(
                    "You already have a ticket open for this topic!", ephemeral=True
                )
                return
            await interaction.response.send_modal(TransactionID(selected_reason))
            await interaction.delete_original_response()
        if selected_reason == "I sent my items but my status says declined":
            result = await check_tickets(
                interaction.guild, interaction.user, selected_reason
            )
            if result == True:
                await interaction.response.send_message(
                    "You already have a ticket open for this topic!", ephemeral=True
                )
                return
            await interaction.response.send_modal(TransactionID(selected_reason))
            await interaction.delete_original_response()
        if selected_reason == "I won a giveaway":
            result = await check_tickets(
                interaction.guild, interaction.user, selected_reason
            )
            if result == True:
                await interaction.response.send_message(
                    "You already have a ticket open for this topic!", ephemeral=True
                )
                return
            await interaction.response.send_modal(SteamID())
            await interaction.delete_original_response()
        if selected_reason == "I want to purchase an item from Skinflow":
            result = await check_tickets(
                interaction.guild,
                interaction.user,
                selected_reason,
            )
            if result == True:
                await interaction.response.send_message(
                    "You already have a ticket open for this topic!", ephemeral=True
                )
                return
            else:
                await interaction.response.send_message(
                    "Thank you, creating your ticket now...", ephemeral=True
                )
            await open_ticket(
                interaction.user, interaction.guild, selected_reason, None
            )
            await interaction.edit_original_response(
                content="Ticket Created!", ephemeral=True
            )


async def check_tickets(guild, user, reason):
    result = False
    for channel in guild.channels:
        if isinstance(channel, discord.TextChannel):
            if channel.topic == f"{user}'s Ticket - {reason}":
                result = True
    return result


async def get_transcript(member, channel: discord.TextChannel):
    export = await chat_exporter.export(channel=channel)
    getcurrenttime = discord.utils.utcnow()
    date = getcurrenttime.strftime("%A,%B%d,%Y,%I:%M%pUTC")
    file_name = os.path.join(save_directory, f"{date}-{member}-{uuid.uuid4()}.html")
    async with aiofiles.open(file_name, mode="w", encoding="utf-8") as file:
        await file.write(export)
    return file_name


async def open_ticket(opener, guild, reason, provided_id):
    payment_category_id = 1161783033272225852
    buying_category_id = 1161783176142786630
    other_category_id = 1161783108677406790
    if reason == "I have not recieved my payment":
        ticket_category = discord.utils.get(guild.categories, id=payment_category_id)
    if reason == "I sent my items but my status says declined":
        ticket_category = discord.utils.get(guild.categories, id=payment_category_id)
    if reason == "I won a giveaway":
        ticket_category = discord.utils.get(guild.categories, id=other_category_id)
    if reason == "I want to purchase an item from Skinflow":
        ticket_category = discord.utils.get(guild.categories, id=buying_category_id)

    mode_role_id = 1061365943806214241
    mod_role = guild.get_role(mode_role_id)
    permission_overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        mod_role: discord.PermissionOverwrite(
            read_messages=True,
            send_messages=True,
            manage_messages=True,
            embed_links=True,
        ),
        opener: discord.PermissionOverwrite(
            read_messages=True, send_messages=True, embed_links=True
        ),
    }

    ticket_channel = await ticket_category.create_text_channel(
        name=f"Ticket: {opener}",
        topic=f"{opener}'s Ticket - {reason}",
        overwrites=permission_overwrites,
    )

    if provided_id:
        embed = discord.Embed(
            title="Someone will assist you shortly",
            description="To close the ticket, click the button below.\nThank you!",
            color=0x444A8D,
        )
        embed.add_field(name="Provided ID:", value=f"{provided_id}")
        embed.set_footer(text="SkinFlow - Instantly Sell Your CS Skins")
        await ticket_channel.send(
            content=f"Thank you for opening a ticket {opener.mention}",
            embed=embed,
            view=CloseButton(opener),
        )
    else:
        TicketEmbed2 = discord.Embed(
            description="Someone will be with you shortly.",
            color=0x444A8D,
        )
        TicketEmbed2.add_field(
            name='To close the ticket, click "Close the Ticket" below.', value="Thanks!"
        )
        TicketEmbed2.set_footer(text="SkinFlow - Instantly Sell Your CS Skins")
        await ticket_channel.send(
            content=f"Thank you for opening a ticket {opener.mention}",
            embed=TicketEmbed2,
            view=CloseButton(opener),
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
        mod_role_id = 1061365943806214241
        mod_role = interaction.guild.get_role(mod_role_id)

        permission_overwrites = {
            guild.default_role: discord.PermissionOverwrite(
                read_messages=False, send_messages=False
            ),
            mod_role: discord.PermissionOverwrite(
                read_messages=True, send_messages=True, manage_messages=True
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
        closeEmbed.set_footer(text="SkinFlow - Instantly Sell Your CS Skins")

        await interaction.channel.send(embed=closeEmbed, view=DeleteTranscriptButtons())


class DeleteTranscriptButtons(discord.ui.View):
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

    @discord.ui.button(
        label="Save Transcript",
        style=discord.ButtonStyle.green,
        custom_id="button:savetranscript",
    )
    async def transcript_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.guild_permissions.administrator:
            await interaction.response.defer(ephemeral=True)
            topic_parts = interaction.channel.topic.split(" - ")
            member = topic_parts[0].split("'s Ticket")[0]
            file_name = await get_transcript(member=member, channel=interaction.channel)
            ticket_log_channel_id = 1161791115750547456
            ticket_log_channel = discord.utils.get(
                interaction.guild.channels, id=ticket_log_channel_id
            )
            embed = discord.Embed(
                title=f"Download {member}'s ticket",
                description="Click the link below to download the HTML file.",
                color=discord.Color.green(),
            )
            embed.add_field(name="File Link", value=f"[Click here to download](http://5.161.184.99/{file_name})")
            embed.add_field(name="File Name", value="output.html")
            embed.add_field(
                name="File Size", value=f"{os.path.getsize(file_name) / 1024:.2f} KB"
            )
            await ticket_log_channel.send(embed=embed, file=discord.File(file_name))
        else:
            await interaction.response.send_message(
                "Only administrators can use this button.", ephemeral=True
            )


class Support(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.logger = logging.getLogger(f"SkinFlow.{self.__class__.__name__}")
        self.bot = bot

    async def cog_load(self) -> None:
        view = SupportButton()
        self.bot.add_view(view)

    @app_commands.command(name="support", description="Sends the support system!")
    async def slash_support(self, interaction: discord.Interaction):
        SupportEmbed = discord.Embed(
            title="SkinFlow Support",
            description="To recieve support, press press the button below.",
            color=0x444A8D,
        )
        SupportEmbed.set_footer(text="SkinFlow - Instantly Sell Your CSGO Skins")
        ticket_embed_channel = interaction.channel
        await interaction.response.send_message(
            "Ticket Embed Successfully sent!", ephemeral=True
        )
        await ticket_embed_channel.send(embed=SupportEmbed, view=SupportButton())


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Support(bot))
