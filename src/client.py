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
        
    def get_active_panel(self, server, player):
        """Get the active panel for a specific user

        Args:
            server (int): Guild ID
            player (int): Player ID

        Returns:
            dict: Active panel
        """
        if server not in self.active_panel:
            return None
        if player not in self.active_panel[server]:
            return None
        return self.active_panel[server][player]
    
    def set_active_panel(self, message, player, type, page, pages):
        """Set the active panel for a specific user

        Args:
            message (discord.Message): Message object (to be the active panel)
            player (discord.User): User
            type (str): Type of panel
            page (int): Page number
            pages (int): Number of pages
        """
        if message.guild.id not in self.active_panel:
            self.active_panel[message.guild.id] = {}
        self.active_panel[message.guild.id][player.id] = {"id": message.id, "page": page, "pages": pages, "type": type}
    
    async def update_active_panel(self, message, func):
        panel = self.get_active_panel(message.guild.id, message.author.id)
        if panel is not None:
            msg = await message.channel.fetch_message(panel["id"])
            await msg.edit(embed=func(panel))
    
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
        embed = discord.Embed(title="Info", color=0x00a000)
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
