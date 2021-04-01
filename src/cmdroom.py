import os

import discord

from choosable import NUMBERS
from jsonembed import json_to_embed
from scrollable import LEFT, RIGHT, Scrollable
from utils import DELETE, CONFIRM, basedir


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


async def accept_new_project(self, reaction, user, panel):
    channel = reaction.message.channel
    msgacc_embed = discord.Embed(color=0x6db977)
    msgacc_embed.title = "Successfully created new project!"
    await channel.send(embed=msgacc_embed)
    self.remove_active_panel(reaction.message, panel["user"])


async def refuse_new_project(self, reaction, user, panel):
    channel = reaction.message.channel
    msgreff_embed = discord.Embed(color=0x6db977)
    msgreff_embed.title = "New project creation aborted!"
    await channel.send(embed=msgreff_embed)


async def command_room(self, message, args):
    if len(args) >= 1:
        if args[0] == "-p":
            if len(args) >= 3:
                project_name, *participants = args[1:]
                msgscc_embed = discord.Embed(color=0x99ab65)
                msgscc_embed.title = "Are you sure?"
                msgscc_embed.description = f"This action will create one role, one voice channel and one text channel!\nProject name: {project_name}\nParticipants: {participants}"
                msgscc = await message.channel.send(embed=msgscc_embed)
                self.add_active_panel(msgscc, message.author, {"yesno"}, info={
                    "on_accept": accept_new_project,
                    "on_delete": refuse_new_project
                })
                await msgscc.add_reaction(DELETE)
                await msgscc.add_reaction(CONFIRM)
            else:
                msgerr_embed = discord.Embed(color=0xfcba03)
                msgerr_embed.title = "Improper command usage"
                msgerr_embed.description = f"*-p* command requires project_name and participants\n{self.prefix}room for more information"
                msgerr = await message.channel.send(embed=msgerr_embed)
                self.add_active_panel(msgerr, message.author, {
                                      "deletable"}, info={})
                await msgerr.add_reaction(DELETE)
        else:
            msgerr_embed = discord.Embed(color=0xfcba03)
            msgerr_embed.title = f"Unknown command *{args[0]}*"
            msgerr_embed.description = f"{self.prefix}room for more information"
            msgerr = await message.channel.send(embed=msgerr_embed)
            self.add_active_panel(msgerr, message.author, {"deletable"})
            await msgerr.add_reaction(DELETE)
        return
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
