import logging
import os

import discord
from activepanel import ActivePanel

from choosable import NUMBERS
from panels import DeletableActivePanel, YesNoActivePanel, ScrollableActivePanel, InputActivePanel
from jsonembed import json_to_embed
from utils import basedir, PROJECTS_CATEGORY, WARNING_COLOR, SUCCESS_COLOR, ERROR_COLOR
from project import *

# google drive folder creation and deletion
from pydrive.auth import GoogleAuth     
from pydrive.drive import GoogleDrive

NEW_PROJECT_ARG = "-p"

class CreateProjectYesNo(YesNoActivePanel):
    def __init__(self, project_name, members, guild, userid=None, dm=False):
        super().__init__(userid=userid)
        self.project_name = project_name
        self.members = members
        self.guild = guild
        self.dm=dm

    async def init(self, message):
        await super().init(message)
    
    async def on_accept(self, client, reaction, user):
        channel = reaction.message.channel
        await make_new_project(self.members, self.project_name, channel, self.guild )
        if self.dm == False:
            await reaction.message.clear_reactions()

    async def on_decline(self, client, reaction, user):
        channel = reaction.message.channel
        msgreff_embed = discord.Embed(color=WARNING_COLOR)
        msgreff_embed.title = "New project creation aborted!"
        await channel.send(embed=msgreff_embed)
        if self.dm == False:
            await reaction.message.clear_reactions()


class ProjectCreator(ActivePanel):
    def __init__(self, guild, pages, userid=None):
        self.dap = YesNoActivePanel(self.on_accept, self.on_decline, userid=userid)
        self.iap = InputActivePanel(self.on_message, userid=userid)
        self.sap = ScrollableActivePanel(self.on_page_change, pages, userid=userid)
        self.userid = userid
        self.project_server = guild
        self.project_name = None
        self.members = []
        
    async def init(self, message):
        self.message = message
        await self.dap.init(message)
        await self.iap.init(message)
        await self.sap.init(message)

    
    async def on_reaction(self, client, reaction, user):
        await self.dap.on_reaction(client, reaction, user)
        await self.iap.on_reaction(client, reaction, user)
        await self.sap.on_reaction(client, reaction, user)
        
    async def on_decline(self, yn, client, reaction, user):
        await yn.message.delete() 

    async def on_page_change(self, scrollable):
        path = os.path.join(basedir(__file__), "rsrc",
                            "project_creator", f"page{scrollable.page+1}.json")
        with open(path, "r") as f:
            base = json_to_embed(f.read())

        if scrollable.page == 0:
            value = str(self.project_name)
        elif scrollable.page == 1:
            value = str(list(member.display_name for member in self.members))
            
        base.set_field_at(0, name=base.fields[0].name, value=value)

        return base


    async def on_message(self, client, message):
        if self.sap.page == 0:
            self.project_name = message.content
            await self.message.edit(embed=await self.sap.page_func())

        elif self.sap.page == 1:
            new_participant = message.content
            new_member = member_from_participant(self, self.project_server, new_participant)
            if new_member is None:
                invalid_participant_embed = discord.Embed(color=ERROR_COLOR)
                invalid_participant_embed.title = "Member not found!"
                invalid_participant_embed.description = f"Could not find any member named {new_participant} in '{self.project_server.name}' server"
                bad_name_msg = await message.channel.send(embed=invalid_participant_embed)
                bad_name_ap = DeletableActivePanel()
                await client.add_active_panel(bad_name_msg, bad_name_ap)
            else:
                self.members.append(new_member)
            await self.message.edit(embed=await self.sap.page_func())

    async def on_accept(self, yn, client, reaction, user):
        if self.project_name is not None:
            names = list(member.display_name for member in self.members)
            names_str = ", ".join(names)
            
            msg_scc = await reaction.message.channel.send(embed=new_project_confirmation_embed(self.project_name, names_str))
            yn = CreateProjectYesNo(self.project_name, self.members, self.project_server, dm=True, userid=user.id)
            await client.add_active_panel(msg_scc, yn)
            print(msg_scc)
        else:
            await client.send_error(yn.message.channel, "Project name missing")

async def command_project(self, message, args):
    if len(args) == 0:
        await project_help(self, message)
    
    # Only type give [help, new, delete]. If 'new' or 'delete', send user a private message and finish configuration with InputActivePanel(s)
    elif len(args) == 1:
        if args[0] == "help":
            await project_help(self, message)

        if args[0] == "new": # need user to input project name and members 
            channel = await message.author.create_dm()
            panels = await self.get_active_panels(channel.id, message.author)
            for panel in panels:
                msg = await channel.fetch_message(panel.message.id)
                await self.remove_active_panel(msg)

            creator = ProjectCreator(message.channel.guild, 2, message.author.id)
            msg = await channel.send(embed=await creator.sap.page_func())
            creator.message = msg
            creator.author = message.author

            await self.add_active_panel(msg, creator)

    # Complete arguments are given and all that's needed is argument validation and user confirmation
    elif len(args) >= 2:
        if args[0] == "new":
            project_name, *participants = args[1:]
            
            members, names_str = await validate_participants(self, message.guild, message.channel, participants)

            
            msg_scc = await message.channel.send(embed=new_project_confirmation_embed(project_name, names_str))

            yn = CreateProjectYesNo(project_name, members, message.channel.guild, userid=message.author.id)

            await self.add_active_panel(msg_scc, yn)
            
        elif args[0] == "delete":
            if len(args) >= 2:
                projects_to_delete = args[1:]

                for project in projects_to_delete:
                    await delete_project(project, message, user_input=True, self=self)
        else:
            msg_unrecognized_embed = discord.Embed(color=ERROR_COLOR)
            msg_unrecognized_embed.title = "Unrecognized option!\n"
            msg_unrecognized_embed.description = f"Try \"**{self.prefix}project**\" for more information"
            msg_unrecognized = await message.channel.send(embed=msg_unrecognized_embed)
            await self.add_active_panel(msg_unrecognized, DeletableActivePanel(userid=message.author.id))

    else:
        msg_err_embed = discord.Embed(color=ERROR_COLOR)
        msg_err_embed.title = "Improper command usage"
        msg_err_embed.description = f"{self.prefix}project for more information"
        msgerr = await message.channel.send(embed=msg_err_embed)
        await self.add_active_panel(msgerr, DeletableActivePanel(userid=message.author.id))
