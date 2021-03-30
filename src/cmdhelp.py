import os

from jsonembed import json_to_embed
from scrollable import Scrollable


def get_help_embed(page):
    PAGES = 1
    if page > 0 and page <= PAGES:
        with open(os.path.join("rsrc", "help", f"page{page}.json"), "r") as f:
            return json_to_embed(f.read())
    return None

async def command_help(self, message, args):
    embed = get_help_embed(1)
    msg = await message.channel.send(embed=embed)
    self.add_active_panel(msg, "all", {"deletable", "scrollable"}, info={
        "scrollable": Scrollable(1, 1, get_help_embed)
    })
