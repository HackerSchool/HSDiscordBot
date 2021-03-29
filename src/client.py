import asyncio
import logging
import pickle
import shlex
import time

import discord


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
        self.description = f"{self.prefix}hello"
        
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
            dict: Active panel
        """
        total = set()
        if server not in self.active_panel:
            return total
        if "all" in self.active_panel[server]:
            total.update(self.active_panel[server]["all"])
        if user in self.active_panel[server]:
            total.update(self.active_panel[server][user])
        return total
    
    def add_active_panel(self, message, user, type, info=None):
        """Add an active panel for a specific user

        Args:
            message (discord.Message): Message object (to be the active panel)
            user (discord.User): User
            type (str): Type of panel
        """
        if message.guild.id not in self.active_panel:
            self.active_panel[message.guild.id] = {}
        if user != "all":
            self.active_panel[message.guild.id][user.id] = {"id": message.id, "type": type, "info": info}
        else:
            self.active_panel[message.guild.id][user] = {"id": message.id, "type": type, "info": info}
    
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
        await channel.send(embed=embed)
        
    async def send_error(self, channel, message):
        """Send an error message

        Args:
            channel (discord.Channel): Discord channel to send the message to
            message (str): Message string
        """
        embed = discord.Embed(title="Error", color=0xa00000)
        embed.description = message
        await channel.send(embed=embed)
        
    async def on_ready(self):
        """Event triggered when the bot becomes online"""
        logging.info(f"{self.user} is online")
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
        
        active = self.get_active_panel(reaction.message.guild.id, user.id)
        if reaction.message.id == active["id"]:
            if active["type"] in self.reactions:
                await self.reactions[active["type"]](self, reaction, user)
