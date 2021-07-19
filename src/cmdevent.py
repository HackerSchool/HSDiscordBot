import datetime
import logging
import os
import re
import shlex

import discord

from activepanel import ActivePanel
from panels import YesNoActivePanel, InputActivePanel, ScrollableActivePanel
from event import Event
from jsonembed import json_to_embed
from utils import basedir


class EventCreator(ActivePanel):
    PATTERN1 = re.compile(
        "((?:mon|tues|wednes|thurs|fri|satur|sun)day) +at +(\\d+(?:\\:\\d+)?) *(pm|am)?")
    PATTERN2 = re.compile("(tomorrow|today) +at +(\\d+(?:\\:\\d+)?) *(pm|am)?")
    PATTERN3 = re.compile(
        "(\\d\\d?)[\\-\\/](\\d\\d?)[\\-\\/](\\d\\d\\d\\d) *(?:at)? *(\\d\\d?(?:\\:\\d\\d)?) *(am|pm)?")
    PATTERN4 = re.compile(
        "(?:(\\d+) *h(?:ours?)?)? *(?:and)? *(?:(\\d+) *min(?:utes?)?)?")
    WEEKDAYS = ("monday", "tuesday", "wednesday",
                "thursday", "friday", "saturday", "sunday")

    def __init__(self, channel, pages, userid=None):
        self.dap = YesNoActivePanel(self.on_accept, self.on_decline, userid=userid)
        self.iap = InputActivePanel(self.on_message, userid=userid)
        self.sap = ScrollableActivePanel(self.on_page_change, pages, userid=userid)
        self.userid = userid
        self.current_channel = channel
        self.selected_channel = channel
        self.author = None
        self.event_name = None
        self.event_description = None
        self.event_start = None
        self.event_duration = None
        self.event_repeat = "Never"
        self.role_mentions = ()
        
    async def init(self, client, message):
        self.message = message
        await self.dap.init(client, message)
        await self.iap.init(client, message)
        await self.sap.init(client, message)
        
    async def on_reaction(self, client, reaction, user):
        await self.dap.on_reaction(client, reaction, user)
        await self.iap.on_reaction(client, reaction, user)
        await self.sap.on_reaction(client, reaction, user)
        
    async def on_decline(self, yn, client, reaction, user):
        await yn.message.delete() 

    async def on_page_change(self, scrollable):
        path = os.path.join(basedir(__file__), "rsrc",
                            "event_creator", f"page{scrollable.page+1}.json")
        with open(path, "r") as f:
            base = json_to_embed(f.read())

        if scrollable.page == 0:
            value = "**Selected: **"
            if self.current_channel == self.selected_channel:
                value += f"Current channel ({self.current_channel.mention})"
            else:
                value += f"{self.selected_channel.mention}"
            value += "\n(type the channel name to change it)"

        elif scrollable.page == 1:
            value = str(self.event_name)
        elif scrollable.page == 2:
            value = str(self.event_description)
        elif scrollable.page == 3:
            value = "None" if self.event_start is None else self.event_start.strftime(
                "%d/%m/%Y %H:%Mh")
        elif scrollable.page == 4:
            value = str(self.event_duration)

        elif scrollable.page == 5:
            if len(self.role_mentions) != 0:
                value = ", ".join(map(lambda r: r.name, self.role_mentions))
            else:
                value = "None"
                
        elif scrollable.page == 6:
            value = self.event_repeat

        base.set_field_at(0, name=base.fields[0].name, value=value)

        return base

    async def on_message(self, client, message):
        if self.sap.page == 0:
            def verify_c(channel):
                if not isinstance(channel, discord.channel.TextChannel):
                    return False
                if message.content.isdigit():
                    if channel.id == int(message.content):
                        return True
                if message.content.lower() in channel.name.lower():
                    return True

            valid_channels = tuple(filter(
                verify_c,
                self.current_channel.guild.channels
            ))
            if len(valid_channels) == 1:
                self.selected_channel = valid_channels[0]
                await self.message.edit(embed=await self.sap.page_func())

        elif self.sap.page == 1:
            self.event_name = message.content
            await self.message.edit(embed=await self.sap.page_func())

        elif self.sap.page == 2:
            self.event_description = message.content
            await self.message.edit(embed=await self.sap.page_func())

        elif self.sap.page == 3:
            n = datetime.datetime.now()
            date = self.parse_date(message.content)
            if date is not None and n <= date:
                self.event_start = date
                await self.message.edit(embed=await self.sap.page_func())

        elif self.sap.page == 4:
            duration = self.parse_duration(message.content)
            if duration is not None:
                self.event_duration = duration
                await self.message.edit(embed=await self.sap.page_func())

        elif self.sap.page == 5:
            roles = shlex.split(message.content)

            def verify_r(r):
                for role in roles:
                    if role.isdigit() and int(role) == r.id:
                        return True
                    if role.lower() in r.name.lower():
                        return True
                return False
            valid_roles = tuple(filter(
                verify_r,
                self.current_channel.guild.roles
            ))
            self.role_mentions = valid_roles
            await self.message.edit(embed=await self.sap.page_func())
            
        elif self.sap.page == 6:
            repeat = self.parse_repeat(message.content)
            if repeat is not None:
                self.event_repeat = repeat
                await self.message.edit(embed=await self.sap.page_func())

    async def on_accept(self, yn, client, reaction, user):
        if self.event_name is not None and self.event_start is not None:
            event = Event(
                self.event_name,
                self.event_description,
                self.event_start,
                self.event_duration,
                self.event_repeat,
                self.author,
                self.role_mentions,
                userid=self.userid
            )
            embed = event.get_embed()
            mentions = " ".join(map(lambda r: r.mention, self.role_mentions))
            msg = await self.selected_channel.send(mentions, embed=embed)
            event.message = msg
            duration = (self.event_start - datetime.datetime.now() + self.event_duration).total_seconds() / 60 + 10
            logging.info(duration)
            await client.add_active_panel(msg, event, duration)
        else:
            await client.send_error(yn.message.channel, "Not all required fields are filled out")

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
    def parse_duration(string):
        string = string.strip().lower()
        match = __class__.PATTERN4.match(string)
        if match is not None:
            groups = match.groups()
            argc = len(tuple(filter(lambda i: i is not None, match.groups())))
            if argc != 0:
                hours, minutes = groups
                if hours is None:
                    hours = 0
                else:
                    hours = int(hours)
                if minutes is None:
                    minutes = 0
                else:
                    minutes = int(minutes)
                return datetime.timedelta(hours=hours, minutes=minutes)
        return None
    
    @staticmethod
    def parse_repeat(string):
        string = string.strip().lower()
        if string == "daily" or string == "1":
            return "Daily"
        elif string == "weekly" or string == "2":
            return "Weekly"
        elif string == "monthly" or string == "3":
            return "Monthly"
        elif string == "monthly by weekday" or string == "4":
            return "Monthly (by weekday)"
        elif string == "never" or string == "5":
            return "Never"
        return None

    @staticmethod
    def parse_date(string):
        string = string.strip().lower()
        if string == "now":
            return datetime.datetime.now()
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


async def command_event(self, message, args):
    channel = await message.author.create_dm()

    panels = await self.get_active_panels(channel.id, message.author)
    for panel in panels:
        msg = await channel.fetch_message(panel.message.id)
        await self.remove_active_panel(msg)

    creator = EventCreator(message.channel, 7, message.author.id)
    msg = await channel.send(embed=await creator.sap.page_func())
    creator.message = msg
    creator.author = message.author

    await self.add_active_panel(msg, creator)

