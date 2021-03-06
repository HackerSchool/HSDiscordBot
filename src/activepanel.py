from __future__ import annotations

import time

import discord


class ActivePanel:
    def __init__(self):
        self.userid = None
        self.message = None
        
    @property
    def persistent(self):
        return False
        
    async def on_reaction(self, client, reaction : discord.Reaction, user : discord.User):
        pass
        
    async def on_message(self, client, message : discord.Message):
        pass
    
    async def on_deactivate(self, client):
        pass
    
    async def init(self, client, message : discord.Message):
        self.message = message
    
    async def can_interact(self, client, user : discord.User):
        if self.userid is None:
            return True
        if self.userid is not None:
            return user.id == self.userid 
        if self.message is not None:
            return user.id == self.message.author.id 
        return False
