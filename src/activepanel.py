import discord
import time

from client import HSBot

class ActivePanel:
    def __init__(self):
        self.userid = None
        self.message = None
        
    async def on_reaction(self, client : HSBot, reaction : discord.Reaction, user : discord.User):
        pass
        
    async def on_message(self, client : HSBot, message : discord.Message):
        pass
    
    async def on_deactivate(self, client : HSBot):
        pass
    
    async def init(self, client : HSBot, message : discord.Message):
        self.message = message
    
    async def can_interact(self, client : HSBot, user : discord.User):
        if self.userid is not None:
            return user.id == self.userid 
        if self.message is not None:
            return user.id == self.message.author.id 
        return False
