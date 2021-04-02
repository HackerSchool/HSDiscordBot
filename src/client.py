import asyncio
import datetime
import logging
import pickle
import shlex
import time

import discord
from discord.ext import tasks


@tasks.loop(minutes=1)
async def task_worker(self):
    past = []
    for task in self.tasks:
        if task["start"] >= datetime.datetime.now():
            await task["callback"](self)
            if task["once"] == True:
                past.append(task)
            elif task["end"] >= datetime.datetime.now():
                past.append(task)
    for task in past:
        self.tasks.remove(task)


class HSBot(discord.Client):
    """HS bot client class"""

    def __init__(self, prefix, sprint_path="."):
        intents = discord.Intents.default()
        intents.members = True
        super().__init__(intents=intents)

        self.fetch_offline_members = True
        self.prefix = prefix
        self.active_panel = {}
        self.commands = {}
        self.reactions = {}
        self.custom_msg_handlers = {}
        self.data = {}
        self.tasks = []
        self.description = f"{self.prefix}hello"
        self.sprint_path = sprint_path

    def schedule(self, start, end, callback, once=True):
        """Schedule a task

        Args:
            start (datetime.datetime): Task start
            end (datetime.datetime): Task end
            callback (function): Callback function
            once (bool, optional): True if task should only run once. Defaults to True.
        """
            
        self.tasks.append({
            "start": start,
            "end": end,
            "callback": callback,
            "once": once
        })

    def save(self, file):
        """Save client info to a file"""
        with open(file, "wb") as f:
            pickle.dump((self.dm, self.pcs, self.npcs, self.items), f)

    def load(self, file):
        """Load client info from a file"""
        with open(file, "rb") as f:
            self.dm, self.pcs, self.npcs, self.items = pickle.load(f)

    def get_data(self, key):
        """Get custom data from a server / DM

        Args:
            key (int): Guild ID / Channel ID

        Returns:
            dict: Custom data
        """
        if key not in self.data:
            self.data[key] = {}
        return self.data[key]

    def set_data(self, key, value):
        """Set custom data for a server / DM

        Args:
            key (int): Guild ID / Channel ID
            value (dict): Custom data
        """
        self.data[key] = value

    def get_active_panels(self, key, user):
        """Get the active panels for a specific user

        Args:
            key (int): Guild or channel ID
            user (int): User ID

        Returns:
            dict: Active panels
        """
        total = {}
        if key not in self.active_panel:
            return total
        if "all" in self.active_panel[key]:
            total.update(self.active_panel[key]["all"])
        if user in self.active_panel[key]:
            total.update(self.active_panel[key][user])
        return total

    def add_active_panel(self, message, user, types, info=None):
        """Add an active panel for a specific user

        Args:
            message (discord.Message): Message object (to be the active panel)
            user (discord.User | str): User
            types (set): types of panel
            info (dict, Optional): useful panel info
        """
        key = message.channel.id if message.guild is None else message.guild.id
        if key not in self.active_panel:
            self.active_panel[key] = {}
        if user != "all":
            user = user.id

        if user not in self.active_panel[key]:
            self.active_panel[key][user] = {}
        self.active_panel[key][user][message.id] = {"id": message.id, "types": types, "info": info, "user": user}
            
    async def remove_active_panel(self, message, user, remove_reactions=True):
        """Remove an active panel from a specific user

        Args:
            message (discord.Message): Message object (to be the active panel)
            user (discord.User | str): User
        """
        if remove_reactions:
            if message.guild is not None:
                await message.clear_reactions()
            else:
                for reaction in message.reactions:
                    if reaction.me:
                        await reaction.remove(self.user)
        key = message.channel.id if message.guild is None else message.guild.id
        del self.active_panel[key][user][message.id]

    def add_command(self, name, func, text=True, dm=False):
        """Add a command to the bot

        Args:
            name (str): Command string
            func (function): Python corroutine
        """
        self.commands[name] = {"callback": func, "text": text, "dm": dm}

    def add_custom_message_handler(self, name, func, text=True, dm=False):
        """Add a custom message handler to the bot

        Args:
            name (str): Handler name
            func (function): Python corroutine
        """
        self.custom_msg_handlers[name] = {
            "callback": func, "text": text, "dm": dm}

    def add_reaction(self, name, func, text=True, dm=True):
        """Add a reaction handler to the bot

        Args:
            name (str): Panel type
            func (function): Python corroutine
        """
        self.reactions[name] = {"callback": func, "text": text, "dm": dm}

    async def send_info(self, channel, message):
        """Send an info message

        Args:
            channel (discord.Channel): Discord channel to send the message to
            message (str): Message string
        """
        embed = discord.Embed(title="Info", color=0x6db977)
        embed.description = message
        return await channel.send(embed=embed)

    async def send_error(self, channel, message):
        """Send an error message

        Args:
            channel (discord.Channel): Discord channel to send the message to
            message (str): Message string
        """
        embed = discord.Embed(title="Error", color=0xa00000)
        embed.description = message
        return await channel.send(embed=embed)

    async def on_ready(self):
        """Event triggered when the bot becomes online"""
        logging.info(f"{self.user} is online")
        task_worker.start(self)
        await self.change_presence(status=discord.Status.online, activity=discord.Game(self.description))

    async def on_message(self, message):
        """Event triggered when a user sends a message"""
        if message.author == self.user:
            return

        if message.content.startswith(self.prefix):
            msg_content = message.content[1:]
            command, *args = shlex.split(msg_content)
            if command in self.commands:
                if any((all((isinstance(message.channel, discord.channel.TextChannel),
                             self.commands[command]["text"])),
                        all((isinstance(message.channel, discord.channel.DMChannel),
                             self.commands[command]["dm"])))):
                    await self.commands[command]["callback"](self, message, args)

        else:
            for handler in self.custom_msg_handlers:
                if any((all((isinstance(message.channel, discord.channel.TextChannel),
                             self.custom_msg_handlers[handler]["text"])),
                        all((isinstance(message.channel, discord.channel.DMChannel),
                             self.custom_msg_handlers[handler]["dm"])))):
                    await self.custom_msg_handlers[handler]["callback"](self, message)
        # elif len(message.attachments) != 0:
        #    await sprint.process_attachments(self, message)

    async def on_reaction_add(self, reaction, user):
        """Event triggered when a user reacts to a message"""
        if user == self.user:
            return

        message = reaction.message
        key = (message.channel if message.guild is None else message.guild).id
        active = self.get_active_panels(key, user.id)
        for mid in active:
            if message.id == mid:
                for t in active[mid]["types"]:
                    if t in self.reactions:
                        if any((all((isinstance(message.channel, discord.channel.TextChannel),
                                     self.reactions[t]["text"])),
                                all((isinstance(message.channel, discord.channel.DMChannel),
                                     self.reactions[t]["dm"])))):
                            await self.reactions[t]["callback"](self, reaction, user, active[mid])
