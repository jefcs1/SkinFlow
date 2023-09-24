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
    "Ak": "AK-47"
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
    print(highest_similarity)
    if highest_similarity < 65:
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
    timeframe_r = discord.utils.format_dt(discord.utils.utcnow()+time_difference, style="F")
    return timeframe_r

def check_if_wear(item):
    split_item_name = item[0].split()
    found=False
    for full_name in conditions.values():
        if full_name in split_item_name:
            found = True
            break
    return found

def get_image(item):
    with open('json/item_images.json', 'r') as file:
        data = json.load(file)
        for name, url in data.items():
            if name == item[0]:
                image_url = url
        return image_url

class Prices(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.logger = logging.getLogger(f"SkinFlow.{self.__class__.__name__}")
        self.bot = bot

    @commands.command(aliases=["p"])
    async def price(self, ctx, *, user_input):
        m = await ctx.send("Finding price...")
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{skinflow_api}"
            ) as resp:
                api_data = await resp.json()

        item = convert_user_input(user_input, api_data)
        print(item)
        if item:
            price = int(api_data[item[0]]["price"]) / 100
            if price == 0:
                embed = discord.Embed(
                    title="Item Not Accepted",
                    description=f"We do not currently accept the {item[0]}.\nThis is most likely because it's price is too volatile.",
                    color=0xFF0000,
                )
                embed.set_footer(text="If the item isn't accurate, provide a more descriptive item name.")
                await m.edit(content=None, embed=embed)
            else:
                embed = discord.Embed(
                    title=f"Sell instantly for ${price}!",
                    description=f"SkinFlow will buy a {item[0]} for ${price}!",
                    color=0x4448AD,
                )
                if check_fire_deals(item, api_data) != False:
                    fire_deal = check_fire_deals(item, api_data)
                    if fire_deal[1] is not None:
                        embed.add_field(
                            name=f":fire: FIRE DEAL! :fire: Get an extra ${fire_deal[0]} if you sell before:",
                            value=f"{fire_deal[1]}",
                            inline=False,
                        )
                if item[1] == False and check_if_wear(item) == True:
                    embed.add_field(
                        name="Please provide a wear value for more accurate pricing.",
                        value="",
                        inline=False,
                    )
                if get_image(item) is not None:
                    embed.set_thumbnail(url=get_image(item))
                embed.set_footer(text="If the item isn't accurate, provide a more descriptive item name.")
                await m.edit(content=None, embed=embed)
        else:
            embed = discord.Embed(
                title="Item not Found!",
                description="Check your spelling and try again.",
                color=0xFF0000,
            )
            embed.set_footer(text="If the item isn't accurate, provide a more descriptive item name.")
            await m.edit(content=None, embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Prices(bot))
