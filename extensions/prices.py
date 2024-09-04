import datetime
import logging
import random
import sys
import json

import aiohttp
import discord
from config import skinflow_api
from discord import app_commands
from discord.ext import commands
from thefuzz import fuzz, process

conditions = {
    "Fn": "(Factory New)",
    "Mw": "(Minimal Wear)",
    "Ft": "(Field-Tested)",
    "Ww": "(Well-Worn)",
    "Bs": "(Battle-Scarred)",
}
shorthands = {
    "St": "StatTrak™",
    "Usps": "USP-S",
    "Usp": "USP-S",
    "Bfk": "Butterfly Knife",
    "Bayo": "Bayonet",
    "M9": "M9 Bayonet",
    "Deagle": "Desert Eagle",
    "Ak": "AK-47",
}
split_conditions = {
    "(Factory": "New)",
    "(Minimal": "Wear)",
    "Bs": "(Battle-Scarred)",
    "Ww": "(Well-Worn)",
    "Ft": "(Field-Tested)",
}


def get_input_tokens(user_input):
    input_title = user_input.title()

    for condition, full_name in conditions.items():
        input_title = input_title.replace(condition, full_name)

    words = input_title.split()
    if "Vanilla" in words:
        words.remove("Vanilla")
        words.append("Knife")
        for key, value in split_conditions.items():
            if key in words:
                words.remove(key)
            if value in words:
                words.remove(value)

    for i in range(len(words)):
        word = words[i]
        if word in shorthands:
            words[i] = shorthands[word]

    found = False

    for full_name in conditions.values():
        if full_name in words:
            found = True
            break
    return words, found


def match_item(user_input, data):
    input_tokens = get_input_tokens(user_input)
    matched_item = None
    highest_similarity = 0
    for item_name in data.keys():
        s1 = input_tokens[0]
        s2 = item_name.split()
        similarity = fuzz.token_sort_ratio(s1, s2)
        if similarity > highest_similarity:
            highest_similarity = similarity
            matched_item = item_name
    if highest_similarity < 55:
        return None
    else:
        return matched_item, input_tokens[1]


def convert_user_input(user_input, data):
    matching_item = match_item(user_input, data)
    if matching_item:
        return matching_item[0], matching_item[1]
    else:
        return None


def check_fire_deals(item, api_data):
    item_data = api_data[item[0]]
    if "itemBonus" in item_data and "sell_bonus" in item_data["itemBonus"]:
        bonus_info = item_data["itemBonus"]["sell_bonus"]
        if bonus_info.get("is_bonus"):
            original_price = int(item_data["price"]) / 100
            bonus_price = int(bonus_info["offered_with_bonus"]) / 100
            price_diff = round(bonus_price - original_price, 2)
            expire_time_str = bonus_info["expire_time"]
            timeframe = calculate_timeframe(expire_time_str)
            return price_diff, timeframe
    else:
        return False


def calculate_timeframe(expire_time_str):
    expire_time = datetime.datetime.strptime(expire_time_str, "%Y-%m-%dT%H:%M:%S.%fZ")
    current_time = datetime.datetime.utcnow()
    time_difference = expire_time - current_time
    if time_difference.total_seconds() < 0:
        return None
    timeframe_r = discord.utils.format_dt(
        discord.utils.utcnow() + time_difference, style="f"
    )
    return timeframe_r


def check_if_wear(item):
    split_item_name = item[0].split()
    found = False
    for full_name in conditions.values():
        if full_name in split_item_name:
            found = True
            break
    return found


def get_image(item):
    with open("json/item_images.json", "r") as file:
        data = json.load(file)
        for name, url in data.items():
            if name == item[0]:
                return url
    return None


def calculate_bonus(price, percentage):
    return round(price * percentage, 2)


def create_embed(title, description=None, color=0x4448AD, fields=None):
    embed = discord.Embed(title=title, color=color)
    if description:
        embed.description = description
    if fields:
        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)
    return embed


class Prices(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.logger = logging.getLogger(f"SkinFlow.{self.__class__.__name__}")
        self.bot = bot

    @commands.command(aliases=["p"])
    async def price(self, ctx, *, user_input):
        m = await ctx.send("Finding price...")
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{skinflow_api}") as resp:
                api_data = await resp.json()

        item = convert_user_input(user_input, api_data)

        if item:
            item_name = item[0]
            item_data = api_data[item_name]
            price = int(item_data["price"]) / 100
            fire_deal = check_fire_deals(item, api_data)

            two_percent_bonus = calculate_bonus(price, 0.02)
            fire_deal_bonus = calculate_bonus(price, 0.02) if fire_deal else 0
            total_bonus_price = (
                (price + two_percent_bonus + fire_deal_bonus)
            )

            if price == 0:
                embed = create_embed(
                    title="Item Not Accepted",
                    description=f"We do not currently accept the {item_name}.\nThis is most likely because its price is too volatile.",
                    color=0xFF0000,
                    fields=[
                        (
                            "If the item isn't accurate, provide a more descriptive item name.",
                            "",
                            False,
                        )
                    ],
                )
                await m.edit(content=None, embed=embed)
            else:
                fields = [
                    ("Base Price:", f"${price}", False),
                    (
                        'With the referral code "DISCORD":',
                        f"+ ${two_percent_bonus}",
                        False,
                    ),
                ]

                if fire_deal:
                    fields.append(
                        (
                            f"With a fire deal (only until {fire_deal[1]}):",
                            f":fire: + ${fire_deal_bonus} :fire:",
                            False,
                        )
                    )
                
                fields.append(
                    (
                        "Total with code DISCORD:",
                        f"${round(total_bonus_price, 2)}",
                        False,
                    ),
                )

                if item[1] == False and check_if_wear(item):
                    fields.append(
                        (
                            "Please provide a wear value for more accurate pricing.",
                            "",
                            False,
                        )
                    )

                embed = create_embed(title=f"{item_name}:", fields=fields)
                embed.set_author(
                    name="Skinflow - Instantly sell your skins.",
                    icon_url="https://fretgfr.com/u/XqAtnV.png",
                )
                if get_image(item) is not None:
                    embed.set_thumbnail(url=get_image(item))
                embed.set_footer(
                    text="If the item isn't accurate, provide a more descriptive item name."
                )
                await m.edit(content=None, embed=embed)
        else:
            embed = discord.Embed(
                title="Item not Found!",
                description="Check your spelling and try again.",
                color=0xFF0000,
            )
            embed.set_footer(
                text="If the item isn't accurate, provide a more descriptive item name."
            )
            await m.edit(content=None, embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Prices(bot))
