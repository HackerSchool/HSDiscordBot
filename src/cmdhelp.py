import os

from jsonembed import json_to_embed
from scrollable import LEFT, RIGHT, Scrollable
from utils import DELETE, basedir


def get_help_embed(self):
    PAGES = 1
    if self.page > 0 and self.page <= PAGES:
        path = os.path.join(basedir(__file__), "rsrc", "help", f"page{self.page}.json")
        with open(path, "r") as f:
            return json_to_embed(f.read())
    return None

async def command_help(self, message, args):
    s = Scrollable(1, 1, get_help_embed)
    embed = s.update_page()
    msg = await message.channel.send(embed=embed)
    self.add_active_panel(msg, "all", {"deletable", "scrollable"}, info={
        "scrollable": s
    })
    await msg.add_reaction(DELETE)
    await msg.add_reaction(LEFT)
    await msg.add_reaction(RIGHT)
