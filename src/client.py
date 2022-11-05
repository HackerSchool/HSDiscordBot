from __future__ import annotations

import datetime
import logging
import pickle
import shlex
import time

import discord
from discord.ext import tasks

from cfg import ERROR_COLOR, SUCCESS_COLOR, WARNING_COLOR


class HSBot(discord.Client):
    """HS bot client class"""

    def __init__(self, prefix : str, sprint_path=".", save_path="./data.pkl"):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(intents=intents)

        self.fetch_offline_members = True
        self.prefix = prefix
        self.active_panels = {}
        self.commands = {}
        self.reactions = {}
        self.custom_msg_handlers = {}
        self.data = {}
        self.tasks = []
        self.description = f"{self.prefix}help"
        self.sprint_path = sprint_path
        self.save_path = save_path
        
    def save(self):
        """Save the persistent active panels to a file"""
        data = []
        for key in self.active_panels:
            for messageid in self.active_panels[key]:
                if self.active_panels[key][messageid]["panel"].persistent:
                    data.append((
                        key, 
                        messageid, 
                        self.active_panels[key][messageid]["panel"],
                        self.active_panels[key][messageid]["timestamp"],
                        self.active_panels[key][messageid]["timeout"]
                    ))     
        with open(self.save_path, "wb") as f:
            pickle.dump(data, f)
            
    async def load(self):
        """Load active panels from a file"""
        logging.info("Loading...")
        try:
            with open(self.save_path, "rb") as f:
                for key, messageid, panel, timestamp, timeout in pickle.load(f):
                    self.active_panels.setdefault(key, {})
                    self.active_panels[key][messageid] = {
                        "panel": panel,
                        "timestamp": timestamp,
                        "timeout": timeout
                    }
                    try:
                        await panel.init(self, None)
                        logging.info(
                            f"Loaded panel {key, messageid, panel, timestamp, timeout}")
                    except Exception as e:
                        del self.active_panels[key][messageid]
                        logging.error(
                            f"Failed to load panel {key, messageid, panel, timestamp, timeout}: {e}")
            logging.info("Loaded!")
        except (FileNotFoundError, EOFError):
            logging.warning(f"Couldn't load save file '{self.save_path}'")

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

    def get_active_panel(self, key, message):
        if key not in self.active_panels:
            return None
        if message.id not in self.active_panels[key]:
            return None
        return self.active_panels[key][message.id]["panel"]
    
    def add_message_to_cache(self, message):
        self._connection._messages.append(message)

    async def get_active_panels(self, key, user):
        """Get the active panels for a specific user"""
        total = set()
        if key not in self.active_panels:
            return total
        
        for panel in self.active_panels[key]:
            if await self.active_panels[key][panel]["panel"].can_interact(self, user):
                total.add(self.active_panels[key][panel]["panel"])
        return total
    
    async def is_active_panel(self, key, user, message):
        """Check if this message is an active panel that can interact with the user"""
        if key not in self.active_panels:
            return False
        if message.id not in self.active_panels[key]:
            return False
        return await self.active_panels[key][message.id]["panel"].can_interact(self, user)

    async def add_active_panel(self, message : discord.Message, panel, timeout=5):
        """Add an active panel"""
        key = message.channel.id if message.guild is None else message.guild.id
        if key not in self.active_panels:
            self.active_panels[key] = {}

        self.active_panels[key][message.id] = {
            "panel": panel, 
            "timestamp": time.time(), 
            "timeout": timeout
        }
        await panel.init(self, message)

    async def remove_active_panel(self, message, remove_reactions:bool=True):
        """Remove an active panel"""
        if remove_reactions:
            if message.guild is not None:
                await message.clear_reactions()
            else:
                for reaction in message.reactions:
                    if reaction.me:
                        await reaction.remove(self.user)
        key = message.channel.id if message.guild is None else message.guild.id
        await self.active_panels[key][message.id]["panel"].on_deactivate(self)
        del self.active_panels[key][message.id]

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
        embed = discord.Embed(title="Info", color=WARNING_COLOR)
        embed.description = message
        return await channel.send(embed=embed)

    async def send_error(self, channel, message, active_panel=None):
        """Send an error message

        Args:
            channel (discord.Channel): Discord channel to send the message to
            message (str): Message string
        """
        embed = discord.Embed(title="Error", color=ERROR_COLOR)
        embed.description = message
        msg = await channel.send(embed=embed)
        if active_panel != None:
            await self.add_active_panel(msg, active_panel)
        return msg

    async def on_ready(self):
        """Event triggered when the bot becomes online"""
        logging.info(f"{self.user} is online")
        await self.load()
        task_worker.start(self)
        cleanup_active_panels.start(self)
        autosave.start(self)
        await self.change_presence(status=discord.Status.online, activity=discord.Game(self.description))

    async def on_message_delete(self, message):
        """Event triggered when a message is deleted"""
        key = message.channel.id if message.guild is None else message.guild.id
        to_remove = []
        if key in self.active_panels:
            if message.id in self.active_panels[key]:
                to_remove.append(message.id)
        for msgid in to_remove:
            del self.active_panels[key][msgid]

    async def on_message(self, message):
        """Event triggered when a user sends a message"""
        print("WT ACTUAL FUCK", message.content)
        if message.author == self.user:
            return

        key = message.channel.id if message.guild is None else message.guild.id

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
            key = (message.channel if message.guild is None else message.guild).id
            for panel in await self.get_active_panels(key, message.author):
                await panel.on_message(self, message)
            
            for handler in self.custom_msg_handlers:
                if any((all((isinstance(message.channel, discord.channel.TextChannel),
                             self.custom_msg_handlers[handler]["text"])),
                        all((isinstance(message.channel, discord.channel.DMChannel),
                             self.custom_msg_handlers[handler]["dm"])))):
                    await self.custom_msg_handlers[handler]["callback"](self, message)

    async def on_reaction_add(self, reaction, user):
        """Event triggered when a user reacts to a message"""
        if user == self.user:
            return

        message = reaction.message
        key = (message.channel if message.guild is None else message.guild).id
        
        if await self.is_active_panel(key, user, message):
            await self.get_active_panel(key, message).on_reaction(self, reaction, user)
            
        for handler in self.reactions:
            await self.reactions[handler]["callback"](self, reaction, user)



@tasks.loop(seconds=5)
async def task_worker(self : HSBot):
    past = []
    for task in self.tasks:
        if task["start"] <= datetime.datetime.now():
            await task["callback"](self)
            if task["once"] == True:
                past.append(task)
            elif task["end"] <= datetime.datetime.now():
                past.append(task)
    for task in past:
        self.tasks.remove(task)
        
@tasks.loop(minutes=1)
async def cleanup_active_panels(client : HSBot):
    t = time.time()
    to_remove = []
    for key in client.active_panels:
        for panel in client.active_panels[key]:
            if (t - client.active_panels[key][panel]["timestamp"]) >= client.active_panels[key][panel]["timeout"]*60:
                to_remove.append((key, panel))
    for key, panel in to_remove:
        await client.active_panels[key][panel]["panel"].on_deactivate(client)
        del client.active_panels[key][panel]
        
@tasks.loop(minutes=1)
async def autosave(client : HSBot):
    logging.info("Autosaving...")
    client.save()
    logging.info("Autosaving done!")
