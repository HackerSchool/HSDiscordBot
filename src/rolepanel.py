from typing import TypedDict, Union
import discord
from activepanel import ActivePanel
from choosable import Choosable
from panels import DeletableActivePanel
from client import HSBot
from cfg import NUMBERS, SUCCESS_COLOR
from dataclasses import dataclass


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
        self.channel: discord.TextChannel = channel
        self.userid = userid
        self.message: discord.Message

    async def init(self, client: HSBot, message: discord.Message):
        self.message = message
        await self.dap.init(client, message)

    async def on_reaction(self, client: HSBot, reaction: discord.Reaction, user: discord.User):
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
