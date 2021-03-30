import os

from jsonembed import json_to_embed
from scrollable import LEFT, RIGHT, Scrollable
from utils import basedir


def get_help_embed(page):
    PAGES = 1
    if page > 0 and page <= PAGES:
        path = os.path.join(basedir(__file__), "rsrc", "help", f"page{page}.json")
        with open(path, "r") as f:
            return json_to_embed(f.read())
    return None

async def command_help(self, message, args):
    embed = get_help_embed(1)
    msg = await message.channel.send(embed=embed)
    self.add_active_panel(msg, "all", {"deletable", "scrollable"}, info={
        "scrollable": Scrollable(1, 1, get_help_embed)
    })
    await msg.add_reaction(LEFT)
    await msg.add_reaction(RIGHT)
