import os

from jsonembed import json_to_embed
from scrollable import LEFT, RIGHT, Scrollable
from utils import DELETE, basedir

NUMBERS = ('0️⃣', '1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣')

def get_room_embed(self=None, init=False):
    PAGES = 1
    if init:
        path = os.path.join(basedir(__file__), "rsrc", "room", f"page1.json")
        with open(path, "r") as f:
            return json_to_embed(f.read())

    if self.page > 0 and self.page <= PAGES:
        path = os.path.join(basedir(__file__), "rsrc", "room", f"page{self.page}.json")
        with open(path, "r") as f:
            return json_to_embed(f.read())
    return None

async def command_room(self, message, args):
    embed = get_room_embed(init = True)
    msg = await message.channel.send(embed=embed)
    self.add_active_panel(msg, "all", {"deletable", "scrollable", "numbers"}, info={
        "scrollable": Scrollable(1, 1, get_room_embed)
    })
    await msg.add_reaction(DELETE)
    await msg.add_reaction(LEFT)
    await msg.add_reaction(RIGHT)
    await msg.add_reaction('1️⃣')
    await msg.add_reaction('2️⃣')
    #await msg.add_reaction('3️⃣')
    #await msg.add_reaction('4️⃣')
    #await msg.add_reaction('5️⃣')

async def reaction_numbers(self, reaction, user, panel):
    """Triggered when a yes-no message is reacted on"""
    
    if reaction.emoji == NUMBERS[0]:
        await reaction.remove(user)
        await self.send_info(reaction.message.channel, "Room 0 selected")

    if reaction.emoji == NUMBERS[1]:
        await reaction.remove(user)
        await self.send_info(reaction.message.channel, "Room 1 selected")

    if reaction.emoji == NUMBERS[2]:
        await reaction.remove(user)
        await self.send_info(reaction.message.channel, "Room 2 selected")