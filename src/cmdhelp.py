import os

from jsonembed import json_to_embed
from activepanel import ActivePanel
from panels import DeletableActivePanel, ScrollableActivePanel
from utils import basedir


class HelpScrollable(ActivePanel):
    def __init__(self, pages, userid=None):
        self.dap = DeletableActivePanel(userid=userid)
        self.sap = ScrollableActivePanel(self.on_page_change, pages, userid=userid)
        
    async def init(self, message):
        self.message = message
        await self.dap.init(message)
        await self.sap.init(message)

    async def on_page_change(self, scrollable):
        path = os.path.join(basedir(__file__), "rsrc",
                            "help", f"page{scrollable.page+1}.json")
        with open(path, "r") as f:
            return json_to_embed(f.read())
        
    async def on_reaction(self, client, reaction, user):
        if await self.sap.can_interact(client, user):
            await self.sap.on_reaction(client, reaction, user)
        if await self.dap.can_interact(client, user):
            await self.dap.on_reaction(client, reaction, user)
            
    async def can_interact(self, client, user):
        return any((await self.dap.can_interact(client, user),
                    await self.sap.can_interact(client, user)))


async def command_help(self, message, args):
    s = HelpScrollable(1, message.author.id)
    msg = await message.channel.send(embed=await s.sap.page_func())
    await self.add_active_panel(msg, s)