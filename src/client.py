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
            task["callback"](self)
            if task["once"] == True:
                past.append(task)
            elif task["end"] >= datetime.datetime.now():
                past.append(task)
    for task in past:
        del self.tasks[task]


class HSBot(discord.Client):
    """HS bot client class"""
    def __init__(self, prefix):
        intents = discord.Intents.default()
        intents.members = True
        super().__init__(intents=intents)
        
        self.fetch_offline_members = True
        self.prefix = prefix
        self.active_panel = {}
        self.commands = {}
        self.reactions = {}
        self.tasks = []
        self.description = f"{self.prefix}hello"
        
    def schedule(self, start, end, callback, once=False):
        """Schedule a task

        Args:
            start (datetime.datetime): Task start
            end (datetime.datetime): Task end
            callback (function): Callback function
            once (bool, optional): True if task should only run once. Defaults to False.
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
        
    def get_active_panels(self, server, user):
        """Get the active panels for a specific user

        Args:
            server (int): Guild ID
            user (int): User ID

        Returns:
            dict: Active panels
        """
        total = {}
        if server not in self.active_panel:
            return total
        if "all" in self.active_panel[server]:
            total.update(self.active_panel[server]["all"])
        if user in self.active_panel[server]:
            total.update(self.active_panel[server][user])
        return total
    
    def add_active_panel(self, message, user, types, info=None):
        """Add an active panel for a specific user

        Args:
            message (discord.Message): Message object (to be the active panel)
            user (discord.User | str): User
            types (set): types of panel
        """
        if message.guild.id not in self.active_panel:
            self.active_panel[message.guild.id] = {}
        if user != "all": user = user.id
        
        if user not in self.active_panel[message.guild.id]:
            self.active_panel[message.guild.id][user] = {}
        self.active_panel[message.guild.id][user][message.id] = {"id": message.id, "types": types, "info": info, "user": user}
            
    def remove_active_panel(self, message, user):
        """Remove an active panel from a specific user

        Args:
            message (discord.Message): Message object (to be the active panel)
            user (discord.User | str): User
        """
        del self.active_panel[message.guild.id][user][message.id]
    
    def add_command(self, name, func):
        """Add a command to the bot

        Args:
            name (str): Command string
            func (function): Python corroutine
        """
        self.commands[name] = func
        
    def add_reaction(self, name, func):
        """Add a reaction handler to the bot

        Args:
            name (str): Panel type
            func (function): Python corroutine
        """
        self.reactions[name] = func
        
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
                await self.commands[command](self, message, args)
                
    async def on_reaction_add(self, reaction, user):
        """Event triggered when a user reacts to a message"""
        if user == self.user:
            return
        
        active = self.get_active_panels(reaction.message.guild.id, user.id)
        for mid in active:
            if reaction.message.id == mid:
                for t in active[mid]["types"]:
                    if t in self.reactions:
                        await self.reactions[t](self, reaction, user, active[mid])
