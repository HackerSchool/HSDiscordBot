from __future__ import annotations

import os

import discord
from discord.message import Message
from discord.reaction import Reaction

from activepanel import ActivePanel
from cfg import ACCEPT, DECLINE, DELETE
from client import HSBot
from jsonembed import json_to_embed
from utils import basedir


class DeletableActivePanel(ActivePanel):
    def __init__(self, delete_emoji=DELETE, userid=None):
        self.delete_emoji = delete_emoji
        self.message = None
        self.userid = userid
        
    async def init(self, client, message):
        self.message = message
        await message.add_reaction(self.delete_emoji)
        
    async def on_reaction(self, client, reaction, user):
        if str(reaction.emoji) == self.delete_emoji:
            await self.message.delete() 
            

class ScrollableActivePanel(ActivePanel):
    def __init__(self, page_func, pages : int, previous_emoji="⬅️", next_emoji="➡️", userid=None):
        self.previous_emoji = previous_emoji
        self.next_emoji = next_emoji
        self.message = None
        self.userid = userid
        self._page_func = page_func
        self.page = 0
        self.pages = pages
    
    async def init(self, client, message):
        self.message = message
        await message.add_reaction(self.previous_emoji)
        await message.add_reaction(self.next_emoji)
        
    async def on_reaction(self, client : HSBot, reaction : discord.Reaction, user : discord.User):
        changed = False
        
        if self.pages >= 2:
            if str(reaction.emoji) == self.next_emoji and (user.id == self.message.author.id or user.id == self.userid):
                self.page += 1
                self.page %= self.pages
                changed = True
                
            elif str(reaction.emoji) == self.previous_emoji and (user.id == self.message.author.id or user.id == self.userid):
                self.page -= 1
                self.page %= self.pages
                changed = True
                
        if changed:
            embed = await self._page_func(self)
            await self.message.edit(embed=embed)
            
        if (str(reaction.emoji) == self.previous_emoji or str(reaction.emoji) == self.next_emoji) and not isinstance(reaction.message.channel, discord.channel.DMChannel):
            await reaction.remove(user=user)
            
    async def page_func(self):
        if self._page_func is not None:
            return await self._page_func(self)

    def embed_from_json(self, folder : str, subfolder : str, page : int):
        path = os.path.join(basedir(__file__), folder,
                            subfolder, f"page{page}.json")
        with open(path, "r") as f:
            base_embed = json_to_embed(f.read())
        return base_embed
        

class YesNoActivePanel(ActivePanel):
    def __init__(self, on_accept=None, on_decline=None, confirm_emoji=ACCEPT, decline_emoji=DECLINE, userid=None):
        self._on_accept = on_accept
        self._on_decline = on_decline
        self.confirm_emoji = confirm_emoji
        self.decline_emoji = decline_emoji
        self.userid = userid
        
    async def init(self, client : HSBot, message : discord.Message):
        self.message = message
        await message.add_reaction(self.confirm_emoji)
        if self.on_decline is not None:
            await message.add_reaction(self.decline_emoji)
        
    async def on_reaction(self, client : HSBot, reaction : discord.Reaction, user : discord.User):
        if str(reaction.emoji) == self.confirm_emoji:
            await self.on_accept(client, reaction, user)
        
        elif str(reaction.emoji) == self.decline_emoji:
            await self.on_decline(client, reaction, user)
            
    async def on_decline(self, client : HSBot, reaction : discord.Reaction, user : discord.User):
        if self._on_decline is not None:
            return await self._on_decline(self, client, reaction, user)
    
    async def on_accept(self, client : HSBot, reaction : discord.Reaction, user : discord.User):
        if self._on_accept is not None:
            return await self._on_accept(self, client, reaction, user)

    
class InputActivePanel(ActivePanel):
    def __init__(self, input_func, userid=None):
        self.input_func = input_func
        self.message = None
        self.userid = userid
        
    async def init(self, client : HSBot, message : discord.Message):
        self.message = message
        
    async def on_message(self, client : HSBot, message : discord.Message):
        await self.input_func(message)
        
