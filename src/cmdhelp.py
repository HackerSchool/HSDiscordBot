from __future__ import annotations

import os

import discord

from activepanel import ActivePanel
from client import HSBot
from jsonembed import json_to_embed
from panels import DeletableActivePanel, ScrollableActivePanel
from utils import basedir


class HelpScrollable(ActivePanel):
    def __init__(self, pages : int, userid=None):
        self.dap = DeletableActivePanel(userid=userid)
        self.sap = ScrollableActivePanel(self.on_page_change, pages, userid=userid)
        
    async def init(self, client : HSBot, message : discord.Message):
        self.message = message
        await self.dap.init(client, message)
        await self.sap.init(client, message)

    async def on_page_change(self, scrollable : ScrollableActivePanel):
        path = os.path.join(basedir(__file__), "rsrc",
                            "help", f"page{scrollable.page+1}.json")
        with open(path, "r") as f:
            return json_to_embed(f.read())
        
    async def on_reaction(self, client : HSBot, reaction : discord.Reaction, user : discord.User):
        if await self.sap.can_interact(client, user):
            await self.sap.on_reaction(client, reaction, user)
        if await self.dap.can_interact(client, user):
            await self.dap.on_reaction(client, reaction, user)
            
    async def can_interact(self, client : HSBot, user : discord.User):
        return any((await self.dap.can_interact(client, user),
                    await self.sap.can_interact(client, user)))


async def command_help(client : HSBot, message : discord.Message, args : list[str]):
    s = HelpScrollable(2, message.author.id)
    msg = await message.channel.send(embed=await s.sap.page_func())
    await client.add_active_panel(msg, s)
