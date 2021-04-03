import os

from jsonembed import json_to_embed
from scrollable import LEFT, RIGHT, Scrollable
from utils import DELETE, Deletable, basedir


class HelpScrollable(Scrollable, Deletable):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def on_page_change(self):
        path = os.path.join(basedir(__file__), "rsrc",
                            "help", f"page{self.page}.json")
        with open(path, "r") as f:
            return json_to_embed(f.read())


async def command_help(self, message, args):
    s = HelpScrollable(1, 1)
    embed = s.get_embed()
    msg = await message.channel.send(embed=embed)
    self.add_active_panel(msg, "all", {"deletable", "scrollable"}, s)
    await msg.add_reaction(DELETE)
    await msg.add_reaction(LEFT)
    await msg.add_reaction(RIGHT)
