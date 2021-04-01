import datetime
import logging
import os
import re

import discord

from jsonembed import json_to_embed
from scrollable import LEFT, RIGHT, SmartScrollable
from utils import CONFIRM, DELETE, basedir


class Event(SmartScrollable):
    PATTERN1 = re.compile(
        "((?:mon|tues|wednes|thurs|fri|satur|sun)day) +at +(\d+(?:\:\d+)?) *(pm|am)?")
    PATTERN2 = re.compile("(tomorrow|today) +at +(\d+(?:\:\d+)?) *(pm|am)?")
    PATTERN3 = re.compile(
        "(\\d\\d?)[\\-\\/](\\d\\d?)[\\-\\/](\\d\\d\\d\\d) *(?:at)? *(\\d\\d?(?:\\:\\d\\d)?) *(am|pm)?")
    WEEKDAYS = ("monday", "tuesday", "wednesday",
                "thursday", "friday", "saturday", "sunday")

    def __init__(self, channel, message, pages, page=1, on_page_change=None, auto_footer=True):
        super().__init__(message, pages, page, on_page_change, auto_footer)
        self.current_channel = channel
        self.selected_channel = channel
        self.start_time = None
        self.duration = None
        self.event_name = None
        self.repeat = None
        self.event_description = None
        self.role_mentions = []

    async def on_delete(self, client, reaction, user, panel):
        del client.get_data(self.message.channel.id)["active_event"]

    async def on_message(self, message):
        if self.page == 1:
            def verify(channel):
                if not isinstance(channel, discord.channel.TextChannel):
                    return False
                if message.content.isdigit():
                    if channel.id == int(message.content):
                        return True
                if message.content.lower() in channel.name.lower():
                    return True

            valid_channels = tuple(filter(
                verify,
                self.current_channel.guild.channels
            ))
            if len(valid_channels) == 1:
                self.selected_channel = valid_channels[0]
                await self.message.edit(embed=self.update_page())

        elif self.page == 2:
            self.event_name = message.content
            await self.message.edit(embed=self.update_page())

        elif self.page == 3:
            self.event_description = message.content
            await self.message.edit(embed=self.update_page())

        elif self.page == 4:
            date = self.parse_date(message.content)
            if date is not None and datetime.datetime.now() <= date:
                self.start_time = date
                await self.message.edit(embed=self.update_page())

    async def publish(self, client, reaction, user, panel):
        await self.message.channel.send("Hurray!")

    @staticmethod
    def parse_time(string, half):
        time = string.split(":")
        if len(time) == 1:
            hours, minutes = int(time[0]), 0
        else:
            hours, minutes = int(time[0]), int(time[1])
        if hours < 12 and half == "pm":
            hours += 12
        return hours, minutes

    @staticmethod
    def parse_date(string):
        string = string.strip().lower()
        if string == "now":
            n = datetime.datetime.now()
            return n.replace(hour=hours, minute=minutes, second=0, microsecond=0)
        else:
            match = __class__.PATTERN1.match(string)
            if match is not None:
                weekday, time, half = match.groups()
                delta = (__class__.WEEKDAYS.index(weekday) -
                         datetime.datetime.now().weekday()) % 7
                hours, minutes = __class__.parse_time(time, half)
                try:
                    next_date = datetime.datetime.today() + datetime.timedelta(days=delta)
                    next_date = next_date.replace(
                        hour=hours, minute=minutes, second=0, microsecond=0)
                except ValueError:
                    return None
                return next_date

            match = __class__.PATTERN2.match(string)
            if match is not None:
                relday, time, half = match.groups()
                hours, minutes = __class__.parse_time(time, half)
                try:
                    next_date = datetime.datetime.today()
                    if relday == "tomorrow":
                        next_date += datetime.timedelta(days=1)
                    next_date = next_date.replace(
                        hour=hours, minute=minutes, second=0, microsecond=0)
                except ValueError:
                    return None
                return next_date

            match = __class__.PATTERN3.match(string)
            if match is not None:
                day, month, year, time, half = match.groups()
                hours, minutes = __class__.parse_time(time, half)
                try:
                    date = datetime.datetime(int(year), int(
                        month), int(day), hours, minutes)
                except ValueError:
                    return None
                return date


def get_event_embed(self):
    path = os.path.join(basedir(__file__), "rsrc",
                        "events", f"page{self.page}.json")
    with open(path, "r") as f:
        base = json_to_embed(f.read())

    if self.page == 1:
        value = "**Selected: **"
        if self.current_channel == self.selected_channel:
            value += f"Current channel ({self.current_channel.mention})"
        else:
            value += f"{self.selected_channel.mention}"
        value += "\n(type the channel name to change it)"
        base.set_field_at(0, name=base.fields[0].name, value=value)

    elif self.page == 2:
        value = str(self.event_name)
        base.set_field_at(0, name=base.fields[0].name, value=value)

    elif self.page == 3:
        value = str(self.event_description)
        base.set_field_at(0, name=base.fields[0].name, value=value)

    elif self.page == 4:
        value = str(self.start_time)
        base.set_field_at(0, name=base.fields[0].name, value=value)

    return base


async def command_event(self, message, args):
    channel = await message.author.create_dm()

    panels = self.get_active_panels(channel.id, message.author.id)
    for panel in panels:
        msg = await channel.fetch_message(panels[panel]["id"])
        self.remove_active_panel(msg, panels[panel]["user"])

    s = Event(message.channel, None, 4, 1, get_event_embed)
    msg = await channel.send(embed=s.update_page())
    s.message = msg
    self.add_active_panel(msg, message.author, {"scrollable", "yesno"}, info={
        "scrollable": s,
        "on_accept": s.publish,
        "on_delete": s.on_delete
    })

    self.get_data(channel.id)["active_event"] = s

    await msg.add_reaction(CONFIRM)
    await msg.add_reaction(DELETE)

    await msg.add_reaction(LEFT)
    await msg.add_reaction(RIGHT)


async def handler_event(self, message):
    if message.guild is not None:
        return
    if "active_event" not in self.get_data(message.channel.id):
        return

    await self.get_data(message.channel.id)["active_event"].on_message(message)
