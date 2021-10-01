from __future__ import annotations

from typing import TypedDict

import discord

from activepanel import ActivePanel
from cfg import NUMBERS, SUCCESS_COLOR
from choosable import Choosable
from client import HSBot
from panels import DeletableActivePanel


class Poll(ActivePanel):
    
    def __init__(self, title : str, options : list[str], channel: discord.TextChannel, userid=None):
        self.cap = Choosable(self.on_choose)
        self.dap = DeletableActivePanel(userid=userid)
        self.title : str = title
        self.options : list[str] = options
        self.totals : list[int] = [0]*len(options)
        self.votes : list[TypedDict('Vote', {'user': discord.User, 'idx' : int})] = []
        self.channel : discord.TextChannel = channel
        self.userid = userid
        self.message : discord.Message

    async def init(self, client : HSBot, message : discord.Message):
        self.message = message
        await self.dap.init(client, message)
        await self.cap.init(client, message)

    async def on_reaction(self, client: HSBot, reaction: discord.Reaction, user: discord.User):
        await self.dap.on_reaction(client, reaction, user)
        await self.cap.on_reaction(client, reaction, user)

    async def on_choose(self, client : HSBot, reaction : discord.Reaction, user: discord.User, index : int):
        index -= 1 # Option numbers start at 1, indexes start at 0. function receives option number
        await reaction.remove(user)
        if index >= 0 and index < len(self.totals):
            for vote in self.votes:
                if user == vote['user']:
                    self.totals[vote['idx']] -= 1
                    self.votes.remove(vote)
            self.votes.append({'user' : user, 'idx' : index})
            self.totals[index] += 1
        await self.message.edit(embed = self.embed())

    def embed(self) -> discord.Embed:
        embed = discord.Embed(title=self.title)
        embed.colour = SUCCESS_COLOR
        for i in range(0, len(self.options)):
            embed.add_field(name="`" + str(i+1) + "` " + self.options[i], value=str(self.totals[i]))
        return embed
    
    async def send_msg(self) -> discord.Message:
        msg : discord.Message = await self.channel.send(embed = self.embed())
        for i in range(1, len(self.options) + 1):
            await msg.add_reaction(NUMBERS[i])
        return msg
