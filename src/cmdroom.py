import os

from choosable import NUMBERS
from jsonembed import json_to_embed
from scrollable import LEFT, RIGHT, Scrollable
from utils import DELETE, basedir


def get_room_embed(self):
    PAGES = 1
    if self.page > 0 and self.page <= PAGES:
        path = os.path.join(basedir(__file__), "rsrc",
                            "room", f"page{self.page}.json")
        with open(path, "r") as f:
            return json_to_embed(f.read())
    return None


async def create_room(self, reaction, user, roomID):
    server = reaction.message.guild
    usr = str(user)
    reason = "Selected by" + usr
    name = "room " + str(roomID) + " by hsbot"
    await server.create_voice_channel(name, reason=reason)


async def on_choose(self, reaction, user, panel, index):
    await self.send_info(reaction.message.channel, f"Room {index} selected")
    await create_room(self, reaction, user, index)


async def command_room(self, message, args):
    s = Scrollable(1, 1, get_room_embed)
    embed = s.update_page()
    msg = await message.channel.send(embed=embed)
    self.add_active_panel(msg, "all", {"deletable", "scrollable", "choosable"}, info={
        "scrollable": s,
        "on_choose": on_choose
    })
    await msg.add_reaction(DELETE)
    await msg.add_reaction(LEFT)
    await msg.add_reaction(RIGHT)
    for i in range(1, 5):
        await msg.add_reaction(NUMBERS[i])
