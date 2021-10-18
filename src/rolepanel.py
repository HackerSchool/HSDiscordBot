from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Union

import discord

from activepanel import ActivePanel
from cfg import NUMBERS, SUCCESS_COLOR
from choosable import Choosable
from client import HSBot
from panels import DeletableActivePanel


@dataclass
class ObtainableRole:
    role: discord.Role
    description: str
    emoji: Union[str, discord.Emoji]

    def __str__(self) -> str:

        if self.role is None:
            role_str = "<no role>"
        else:
            role_str = self.role.mention
        return f"{self.emoji}: {role_str}. {self.description}"

    def dm_preview(self) -> str:
        if self.role is None:
            role_str = "<no role>"
        else:
            role_str = f"@{self.role.name}"
        return f"{self.emoji}: {role_str}. {self.description}"


class RolePanel(ActivePanel):
    def __init__(self, roles: list[ObtainableRole], channel: discord.TextChannel, userid=None):
        self.dap = DeletableActivePanel(userid=userid)
        self.title: str = "React with emoji to obtain role!\nReact again to remove it!"
        self.roles: list[ObtainableRole] = roles
        self._role_ids = None
        self.channel: discord.TextChannel = channel
        self._channel_id = None
        self.userid = None
        self.message: discord.Message
        self._msg_channel_id = None
        self.loaded = True
        
    @staticmethod
    def _from_raw_data(uid, mcid, mid, rids, cid):
        new_rolepanel = RolePanel([], None, userid=uid)
        new_rolepanel._role_ids = rids
        new_rolepanel._msg_channel_id = mcid, mid
        new_rolepanel._channel_id = cid
        new_rolepanel.loaded = False
        return new_rolepanel
        
    def __reduce__(self) -> str | tuple[Any, ...]:
        return (self._from_raw_data, (
            self.userid,
            self.message.channel.id if self.message is not None else None,
            self.message.id if self.message is not None else None,
            [(role.role.id, role.description, role.emoji) for role in self.roles] if self.roles is not None else [],
            self.channel.id if self.channel is not None else None
        ))
    
    @property
    def persistent(self):
        return True

    async def init(self, client: HSBot, message: discord.Message):
        if self.loaded:
            self.message = message
        else:
            logging.info("Loading active panel (loaded from file)")
            if self._msg_channel_id is not None:
                cid, mid = self._msg_channel_id
                if cid is not None and mid is not None:
                    channel = await client.fetch_channel(cid)
                    self.message = await channel.fetch_message(mid)
                    client.add_message_to_cache(self.message)
                    self.roles = []
                    #roles = await self.message.guild.fetch_roles()
                    #role_ids = tuple(role.id for role in roles)
                    for roleid, roledesc, roleemoji in self._role_ids:
                        try:
                            role = discord.utils.get(self.message.guild.roles, id=roleid)
                            #i = role_ids.index(roleid)
                            #new_role = ObtainableRole(roles[i], roledesc, roleemoji)
                            new_role = ObtainableRole(role, roledesc, roleemoji)
                            self.roles.append(new_role)
                        except IndexError:
                            pass
                else:
                    logging.error("No guild/message ID specified")
                    return
            else:
                logging.error("No message ID specified")
                return
            if self._channel_id is not None:
                self.channel = await client.fetch_channel(self._channel_id)
        await self.dap.init(client, self.message)

    async def on_reaction(self, client: HSBot, reaction: discord.Reaction, user: discord.User):
        if await self.dap.can_interact(client, user):
            await self.dap.on_reaction(client, reaction, user)
        await self._on_reaction(client, reaction, user)

    async def _on_reaction(self, client: HSBot, reaction: discord.Reaction, member: discord.Member):
        for obtainable_role in self.roles:
            if reaction.emoji == obtainable_role.emoji:
                if obtainable_role.role in member.roles:
                    await member.remove_roles(obtainable_role.role, reason="Role panel deletion")
                else:
                    await member.add_roles(obtainable_role.role, reason="Role panel addition")

    def embed(self) -> discord.Embed:
        embed = discord.Embed(title=self.title)
        embed.colour = SUCCESS_COLOR
        embed.description = '\n'.join([str(role) for role in self.roles])
        return embed

    async def send_msg(self) -> discord.Message:
        msg: discord.Message = await self.channel.send(embed=self.embed())
        for obtainable_role in self.roles:
            await msg.add_reaction(obtainable_role.emoji)
        return msg
