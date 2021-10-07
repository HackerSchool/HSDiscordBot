from __future__ import annotations

import os
from typing import Optional

import discord
from discord import message
from discord.embeds import EmbedProxy

from activepanel import ActivePanel
from cfg import ERROR_COLOR, NUMBERS, SUCCESS_COLOR, WARNING_COLOR
from client import HSBot
from jsonembed import json_to_embed
from panels import (DeletableActivePanel, InputActivePanel,
                    ScrollableActivePanel, YesNoActivePanel)
from rolepanel import ObtainableRole, RolePanel
from utils import basedir, role_from_incomplete_name

EMOJI_ADD = "▶"
EMOJI_REMOVE = "⛔"
EMOJI_UP = "⬆"
EMOJI_DOWN = "⬇"


class RolePanelCreator(ActivePanel):
    def __init__(self, guild: discord.Guild, channel: discord.TextChannel, pages, userid=None):
        self.dap = YesNoActivePanel(self.on_accept, self.on_decline, userid=userid)
        self.iap = InputActivePanel(self.on_message, userid=userid)
        self.sap = ScrollableActivePanel(self._on_page_change, pages, userid=userid)
        self.userid = userid
        self.server: discord.Guild = guild
        self.roles: list[ObtainableRole] = []
        self.current_channel: discord.channel.TextChannel = channel
        self.selected_channel: discord.channel.TextChannel = channel
        self.field: int = 0
        self.message: discord.Message = None

    async def init(self, client: HSBot, message: discord.Message):
        self.message = message
        await self.dap.init(client, message)
        await self.iap.init(client, message)
        await self.sap.init(client, message)
        await message.add_reaction(EMOJI_UP)
        await message.add_reaction(EMOJI_DOWN)
        await message.add_reaction(EMOJI_ADD)
        await message.add_reaction(EMOJI_REMOVE)

        await self.select_field(message)

    async def on_reaction(self, client: HSBot, reaction: discord.Reaction, user: discord.User):
        self.message = reaction.message
        await self.dap.on_reaction(client, reaction, user)
        await self.iap.on_reaction(client, reaction, user)
        await self.sap.on_reaction(client, reaction, user)
        await self._on_reaction(client, reaction, user)

    async def on_decline(self, yn: YesNoActivePanel, client: HSBot, reaction: discord.Reaction, user: discord.User):
        await yn.message.delete()

    async def on_accept(self, yn: YesNoActivePanel, client: HSBot, reaction: discord.Reaction, user: discord.User):
        if len(self.roles) == 0:
            await client.send_error(reaction.message.channel, "I'm not creating a role panel with no roles.", DeletableActivePanel())
            return

        for role in self.roles:
            if role.role == None or role.description == None or role.emoji == None:
                await client.send_error(reaction.message.channel, "Not all fields are filled!")
                return

        role_panel = RolePanel(self.roles, self.selected_channel, userid=user.id)
        role_panel_msg = await role_panel.send_msg()
        await client.add_active_panel(role_panel_msg, role_panel, timeout=52594876) # timeout = 1 century
        scc_embed = discord.Embed(title="Role Panel Added!", colour=SUCCESS_COLOR)
        success_msg = await reaction.message.channel.send(embed=scc_embed)
        await client.add_active_panel(success_msg, DeletableActivePanel())

    async def _on_reaction(self, client: HSBot, reaction: discord.Reaction, user: discord.User):
        if str(reaction.emoji) == EMOJI_ADD:
            await self.add_role(reaction.message)
        if str(reaction.emoji) == EMOJI_REMOVE:
            await self.remove_role(reaction.message)
        if str(reaction.emoji) == EMOJI_DOWN:
            await self.select_down(reaction.message)
        if str(reaction.emoji) == EMOJI_UP:
            await self.select_up(reaction.message)
        await self.select_field(reaction.message)

    async def select_down(self, message: discord.Message):
        fields = len(message.embeds[0].fields) - 1
        if fields >= 2:
            self.field += 1
            self.field %= fields
            await self.select_field(message)

    async def select_up(self, message: discord.Message):
        fields = len(message.embeds[0].fields) - 1
        if fields >= 2:
            self.field -= 1
            self.field %= fields
            await self.select_field(message)

    async def select_field(self, message: discord.Message):
        if self.field >= len(message.embeds[0].fields):
            self.field = len(message.embeds[0].fields) - 1
        embed = await self.sap.page_func()
        field_as_new: EmbedProxy = embed.fields[self.field + 1]
        embed.set_field_at(self.field + 1, name=":point_right: " + field_as_new.name,
                           value=field_as_new.value, inline=field_as_new.inline)
        await self.message.edit(embed=embed)

    async def add_role(self, message: discord.Message):
        self.roles.append(ObtainableRole(None, None, None))
        self.sap.pages += 1

    async def remove_role(self, message: discord.Message):
        if self.sap.page < 1:
            return
        cur_role = self.roles[self.sap.page - 1]
        self.roles.remove(cur_role)
        self.sap.pages -= 1
        self.sap.page -= 1
        embed = await self.sap.page_func()
        await self.message.edit(embed=embed)

    async def _on_page_change(self, scrollable: ScrollableActivePanel) -> discord.Embed:
        # all roles use the same base embed
        if self.sap.page + 1 >= 2:
            tmp_page = 2
        else:
            tmp_page = self.sap.page + 1
        base_embed = self.sap.embed_from_json(
            "rsrc", "rolepanel_creator", tmp_page)
        return await self.on_page_change(base_embed, self.sap.page)

    async def on_page_change(self, base : discord.Embed, page : int) -> discord.Embed:
        if page == 0:
            title = base.fields[1].name
            value = "**Selected: **"
            if self.current_channel == self.selected_channel:
                value += f"Current channel ({self.current_channel.mention})"
            else:
                value += f"{self.selected_channel.mention}"
            value += "\n(type the channel name to change it)"
            base.set_field_at(1, name=title, value=value)

        elif 0 <= page - 1 < len(self.roles):
            title = base.fields[0].name
            # Number roles, always update their preview
            role = self.roles[page - 1]
            title = f"Role {page} Preview"
            value = role.dm_preview()
            base.set_field_at(0, name=title, value=value)
            vals = [role.emoji, role.role, role.description]
            for i in range(1, 4):
                base.set_field_at(i, name=base.fields[i].name, value=str(vals[i-1]), inline=base.fields[i].inline)
        
        base.set_footer(text=f"Page {page + 1}/{len(self.roles) + 1}")
        return base

    async def on_message(self, client: HSBot, message: discord.Message):
        if self.sap.page == 0:
            channel = await self.channel_str_to_discord_channel(client, message.content)
            if channel is not None:
                self.selected_channel = channel
                await self.message.edit(embed=await self.sap.page_func())

        elif self.sap.page - 1 >= 0 and self.sap.page - 1 < len(self.roles):
            if self.field == 1: # edit emoji
                try:
                    await self.message.add_reaction(message.content)
                    await self.message.remove_reaction(message.content, client.user)
                    self.roles[self.sap.page - 1].emoji = message.content
                except discord.errors.HTTPException:
                    await client.send_error(self.message.channel, "I don't know that emoji, sorry!", active_panel= DeletableActivePanel())
            if self.field == 2: # edit role
                new_role = role_from_incomplete_name(
                    self.server, message.content)
                if isinstance(new_role, str):
                    await client.send_error(self.message.channel, new_role, DeletableActivePanel())
                else:
                    self.roles[self.sap.page - 1].role = new_role
            elif self.field == 3: # edit description
                self.roles[self.sap.page - 1].description = message.content
            await self.message.edit(embed=await self.sap.page_func())
        await self.select_field(self.message)

    async def channel_str_to_discord_channel(self, client: HSBot, name: str):
        def verify_c(channel : discord.TextChannel):
            if not isinstance(channel, discord.channel.TextChannel):
                return False
            if name.isdigit():
                if channel.id == int(name):
                    return True
            if name.lower() in channel.name.lower():
                return True

        valid_channels = tuple(filter(
            verify_c,
            self.current_channel.guild.channels
        ))
        if len(valid_channels) == 1:
            return valid_channels[0]
        return None

    async def role_str_to_discord_role(self, client: HSBot, message: discord.Message):
        def verify_r(role):
            if not isinstance(role, discord.Role):
                return False
            if message.content.isdigit():
                if role.id == int(message.content):
                    return True
            if message.content.lower() in role.name.lower():
                return True

        valid_roles = tuple(filter(
            verify_r,
            self.current_channel.guild.roles
        ))
        if len(valid_roles) == 1:
            return valid_roles[0]
        return None


async def command_rolepanel(client: HSBot, message: discord.Message, args: list[str]):

    if len(args) == 0:
        panel = RolePanelCreator(message.guild, message.channel,
                                 1, message.author.id)
        channel = await message.author.create_dm()
        msg = await channel.send(embed=await panel.sap.page_func())
        await client.add_active_panel(msg, panel)
    else:
        fail_embed = discord.Embed(
            title="Too many arguments", color=ERROR_COLOR)
        fail_embed.description = "Command `rolepanel` should be called without extra arguments"
        fail_dap = DeletableActivePanel()
        fail_msg = await message.channel.send(embed=fail_embed)
        client.add_active_panel(fail_msg, fail_dap)
