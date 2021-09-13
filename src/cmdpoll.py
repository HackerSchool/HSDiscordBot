from typing import Optional
import discord

from jsonembed import json_to_embed
from utils import basedir
import os
from activepanel import ActivePanel
from client import HSBot
from panels import DeletableActivePanel, YesNoActivePanel, ScrollableActivePanel, InputActivePanel
from cfg import ERROR_COLOR, NUMBERS, SUCCESS_COLOR, WARNING_COLOR

from poll import Poll



class CreatePollYesNo(YesNoActivePanel):
    def __init__(self, guild: discord.Guild, name: str, options: list[str], channel: discord.TextChannel, userid=None, dm=False):
        super().__init__(userid=userid)
        self.poll_server: discord.Guild = guild
        self.poll_name: Optional[str] = name
        self.options : list[str] = options
        self.poll_channel: discord.channel.TextChannel = channel
        self.dm = dm

    async def on_accept(self, client: HSBot, reaction: discord.Reaction, user):
        
        poll_panel = Poll(self.poll_name, self.options, self.poll_channel)
        poll_msg = await poll_panel.send_msg()

        await client.add_active_panel(poll_msg, poll_panel)

        if self.dm == False:
            await reaction.message.clear_reactions()

    async def on_decline(self, client: HSBot, reaction: discord.Reaction, user):
        channel = reaction.message.channel
        msgreff_embed = discord.Embed(color=WARNING_COLOR)
        msgreff_embed.title = "New project creation aborted!"
        await channel.send(embed=msgreff_embed)
        if self.dm == False:
            await reaction.message.clear_reactions()


async def err_too_many_options(client: HSBot, channel: discord.TextChannel, n_options: int, max_options : int):
    invalid_input_embed = discord.Embed(color=ERROR_COLOR)
    invalid_input_embed.title = "Invalid input!"
    invalid_input_embed.description = f"\"{n_options}\" is too many options. {max_options} max!"
    bad_options_msg = await channel.send(embed=invalid_input_embed)
    bad_options_ap = DeletableActivePanel()
    await client.add_active_panel(bad_options_msg, bad_options_ap)

class PollCreator(ActivePanel):
    def __init__(self, guild: discord.Guild, channel : discord.TextChannel, pages, userid=None):
        self.dap = YesNoActivePanel(
            self.on_accept, self.on_decline, userid=userid)
        self.iap = InputActivePanel(self.on_message, userid=userid)
        self.sap = ScrollableActivePanel(
            self.on_page_change, pages, userid=userid)
        self.userid = userid
        self.poll_server: discord.Guild = guild
        self.poll_name: Optional[str] = None
        self.number_of_options: int = 0
        self.options : list[str] = []
        self.current_channel: discord.channel.TextChannel = channel
        self.selected_channel: discord.channel.TextChannel = channel

    def __repr__(self) -> str:
        name = f"Title: {self.poll_name}"
        options = f"Options: {', '.join(self.options)}"
        return "\n".join([name, options])

    async def init(self, client: HSBot, message: discord.Message):
        self.message = message
        await self.dap.init(client, message)
        await self.iap.init(client, message)
        await self.sap.init(client, message)

    async def on_reaction(self, client: HSBot, reaction: discord.Reaction, user: discord.User):
        await self.dap.on_reaction(client, reaction, user)
        await self.iap.on_reaction(client, reaction, user)
        await self.sap.on_reaction(client, reaction, user)

    async def on_decline(self, yn: YesNoActivePanel, client: HSBot, reaction: discord.Reaction, user: discord.User):
        await yn.message.delete()

    async def on_accept(self, yn, client: HSBot, reaction: discord.Reaction, user: discord.User):
        msg_scc = await reaction.message.channel.send(embed=discord.Embed(title="Are you sure you want to create this poll?", description = str(self)))
        yn = CreatePollYesNo(
            self.poll_server, self.poll_name, self.options, self.selected_channel, userid=user.id, dm=True)
        await client.add_active_panel(msg_scc, yn)

    async def on_page_change(self, scrollable: ScrollableActivePanel) -> discord.Embed:
        
        # all options point to the same page
        if scrollable.page + 1 >= 4:
            tmp_page = 4
        else:
            tmp_page = scrollable.page + 1
        
        path = os.path.join(basedir(__file__), "rsrc",
                            "poll_creator", f"page{tmp_page}.json")
        with open(path, "r") as f:
            base = json_to_embed(f.read())


        title = base.fields[0].name
        if scrollable.page == 0:
            value = str(self.poll_name)
        elif scrollable.page == 1:
            value = "Current number of options: `" + str(self.number_of_options) + "`"
            value += "\nCaution! Changing the number of options resets existing options."
        elif scrollable.page == 2:
            value = "**Selected: **"
            if self.current_channel == self.selected_channel:
                value += f"Current channel ({self.current_channel.mention})"
            else:
                value += f"{self.selected_channel.mention}"
            value += "\n(type the channel name to change it)"
        elif scrollable.page - 3 < len(self.options):
            value = self.options[scrollable.page - 3]
            title += " " + str(scrollable.page - 2) # Add option number to each option's title


        base.set_field_at(0, name=title, value=value)

        return base

    async def on_message(self, client: HSBot, message: discord.Message):
        if self.sap.page == 0:
            self.poll_name = message.content
            await self.message.edit(embed=await self.sap.page_func())

        elif self.sap.page == 1:
            number_of_options_str = message.content
            try:
                self.number_of_options = int(number_of_options_str)
                if self.number_of_options <= 0:
                    self.number_of_options = 0
                    invalid_input_embed = discord.Embed(color=ERROR_COLOR)
                    invalid_input_embed.title = "Invalid input!"
                    invalid_input_embed.description = f"\"{number_of_options_str}\" is not a positive integer. Please input a positive integer as the number of options."
                    bad_options_msg = await message.channel.send(embed=invalid_input_embed)
                    bad_options_ap = DeletableActivePanel()
                    await client.add_active_panel(bad_options_msg, bad_options_ap)
                else:
                    max_options = len(NUMBERS)-1
                    if self.number_of_options > max_options:  # no more emojis
                        await err_too_many_options(client, message.channel, self.number_of_options, max_options)
                        self.number_of_options = 0
                    else:  # success
                        self.sap.pages = 3 + self.number_of_options
                        self.options = ["None"]*self.number_of_options
                        await self.message.edit(embed=await self.sap.page_func())

            except ValueError:
                invalid_input_embed = discord.Embed(color=ERROR_COLOR)
                invalid_input_embed.title = "Unrecognized input!"
                invalid_input_embed.description = f"\"{number_of_options_str}\" is not a valid integer. Please input a positive integer as the number of options."
                bad_options_msg = await message.channel.send(embed=invalid_input_embed)
                bad_options_ap = DeletableActivePanel()
                await client.add_active_panel(bad_options_msg, bad_options_ap)
        elif self.sap.page == 2:
            def verify_c(channel):
                if not isinstance(channel, discord.channel.TextChannel):
                    return False
                if message.content.isdigit():
                    if channel.id == int(message.content):
                        return True
                if message.content.lower() in channel.name.lower():
                    return True

            valid_channels = tuple(filter(
                verify_c,
                self.current_channel.guild.channels
            ))
            if len(valid_channels) == 1:
                self.selected_channel = valid_channels[0]
                await self.message.edit(embed=await self.sap.page_func())


        elif self.sap.page - 3 >= 0 and self.sap.page - 3 < self.number_of_options:
            self.options[self.sap.page - 3] = message.content
            await self.message.edit(embed=await self.sap.page_func())





async def command_poll(client : HSBot, message : discord.Message, args : list[str]):
    
    if len(args) == 0:
        panel = PollCreator(message.guild, message.channel, 3, message.author.id)
        channel = await message.author.create_dm()
        msg = await channel.send(embed=await panel.sap.page_func())
        await client.add_active_panel(msg, panel)

    elif len(args) > 2:
        name, *options = args

        max_options = len(NUMBERS)-1
        if len(options) > max_options:  # no more emojis
            await err_too_many_options(client, message.channel, len(options), max_options)
            return

        msg_scc = await message.channel.send(embed=discord.Embed(title="Are you sure you want to create this poll?", description = "\n".join([name, ", ".join(options)])))
        yn = CreatePollYesNo(
            message.guild, name, options, message.channel, userid=None, dm=False)
        await client.add_active_panel(msg_scc, yn)
