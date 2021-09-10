import discord

from client import HSBot
from activepanel import ActivePanel
from cfg import NUMBERS


class Choosable(ActivePanel):
    def __init__(self, on_choose=None, userid=None):
        self.message = None
        self.userid = userid
        self._on_choose = on_choose
        
    async def init(self, client, message : discord.Message):
        self.message = message

    async def on_reaction(self, client : HSBot, reaction : discord.Reaction, user : discord.User):
        try:
            idx = NUMBERS.index(reaction.emoji)
            await self.on_choose(client, reaction, user, idx)
        except ValueError:
            pass

    async def on_choose(self, client : HSBot, reaction : discord.Reaction, user : discord.User, index : int):
        if self._on_choose is not None:
            await self._on_choose(client, reaction, user, index)
