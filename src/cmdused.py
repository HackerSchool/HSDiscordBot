from datetime import datetime

from discord import colour
from discord.embeds import Embed

from client import HSBot
import discord
from discord import message
from discord.channel import TextChannel, _channel_factory
from cfg import WARNING_COLOR, SUCCESS_COLOR, ERROR_COLOR, PROJECTS_CATEGORY
from utils import get_category_named
from panels import DeletableActivePanel
from client import HSBot


async def used(client: HSBot, guild: discord.Guild, channel: discord.TextChannel, category_name: str = PROJECTS_CATEGORY):
    # strings to arguments
    title_str: str
    if category_name == "*":
        category = None
        title_str = "Most recent text channel uses across all categories"
    else:
        category = get_category_named(guild, category_name)
        if category == None:
            invalid_category_name_embed = discord.Embed(
                title="Invalid category name!")
            invalid_category_name_embed.colour = ERROR_COLOR
            invalid_category_name_embed.description = "Please input a valid category name"
            fail_ap = DeletableActivePanel()
            fail_msg = await channel.send(embed=invalid_category_name_embed)
            await client.add_active_panel(fail_msg, fail_ap)
            return
        title_str = f"Most recent text channel uses in **{category.name}** category"

    # get actual info
    info_used_text_channels = await used_info(guild, category)
    lines: list[str] = []
    for text_channel, date, author in info_used_text_channels:
        text_channel: discord.TextChannel
        date: datetime
        author: discord.Member
        lines.append(
            f"**{text_channel.name}** was last used **{date.date().isoformat()}** by **{author.mention}**")

    list_item_prefix = " • "
    info_text_channels_str = list_item_prefix + \
        f"\n{list_item_prefix}".join(lines)

    info_embed = discord.Embed(
        title=title_str, colour=SUCCESS_COLOR, allowed_mentions=discord.AllowedMentions(users=False))
    info_embed.description = info_text_channels_str

    info_msg = await channel.send(embed=info_embed)
    info_ap = DeletableActivePanel()
    await client.add_active_panel(info_msg, info_ap)


async def used_info(guild: discord.Guild, category: discord.CategoryChannel = None) -> list[(discord.TextChannel, datetime, discord.Member)]:
    used_info_list = []

    for text_channel in __category_text_channels(guild, category):
        last_message: discord.Message
        async for last_message in text_channel.history(limit=1, oldest_first=False):
            if last_message != None:
                used_info_list.append(
                    (text_channel, last_message.created_at, last_message.author))


    return used_info_list


def __category_text_channels(guild: discord.Guild, category: discord.CategoryChannel):
    return guild.text_channels if category == None else category.text_channels


async def command_used(client: HSBot, message: discord.Message, args: list[str]):

    if len(args) == 0:
        await used(client, message.guild, message.channel)

    elif len(args) == 1:
        await used(client, message.guild, message.channel, args[0])

    else:
        invalid_args_embed = discord.Embed(
            title="Too many arguments!", colour=ERROR_COLOR)
        invalid_args_embed.description = f"Do not input more than one category. If no category is input, {PROJECTS_CATEGORY} is used."
