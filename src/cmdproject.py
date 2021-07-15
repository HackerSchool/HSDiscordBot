import logging
import os

import discord

from choosable import NUMBERS
from panels import DeletableActivePanel, YesNoActivePanel, ScrollableActivePanel
from jsonembed import json_to_embed
from utils import basedir

# google drive folder creation and deletion
from pydrive.auth import GoogleAuth     
from pydrive.drive import GoogleDrive

NEW_PROJECT_ARG = "-p"
PROJECTS_CATEGORY = "PROJECTS"
MANAGEMENT_ROLES = ("Chefes", "Dev", "RH", "Marketing")


class CreateProjectYesNo(YesNoActivePanel):
    def __init__(self, project_name, members, userid=None):
        super().__init__(userid)
        self.userid = userid
        self.project_name = project_name
        self.members = members

    async def on_accept(self, client, reaction, user):
        channel = reaction.message.channel
        server = reaction.message.channel.guild
        await make_new_project(self.members, self.project_name, channel, server)
        await reaction.message.clear_reactions()

    async def on_delete(self, client, reaction, user):
        channel = reaction.message.channel
        msgreff_embed = discord.Embed(color=0x6db977)
        msgreff_embed.title = "New project creation aborted!"
        await channel.send(embed=msgreff_embed)
        await reaction.message.clear_reactions()


class DeleteProjectYesNo(YesNoActivePanel):
    def __init__(self, project_voice_channel, project_text_channel, project_role, userid=None):
        super().__init__(userid=userid)
        self.userid = userid
        self.project_voice_channel = project_voice_channel
        self.project_text_channel = project_text_channel
        self.project_role = project_role

    async def delete_project_data(self):
        if self.project_voice_channel is not None:
            await self.project_voice_channel.delete()
        if self.project_text_channel is not None:
            await self.project_text_channel.delete()
        if self.project_role is not None:
            await self.project_role.delete()

    async def on_accept(self, client, reaction, user):
        channel = reaction.message.channel
        await self.delete_project_data()
        msg_deletion_success_embed = discord.Embed(
            title="Deletion successful!", description=f"**{self.project_role.name}** removed")
        await channel.send(embed=msg_deletion_success_embed)
        await reaction.message.clear_reactions()

    async def on_decline(self, client, reaction, user):
        channel = reaction.message.channel
        msgreff_embed = discord.Embed(color=0x6db977)
        msgreff_embed.title = "Project deletion aborted!"
        msgreff_embed.description = f"**{self.project_name} was untouched"
        await channel.send(embed=msgreff_embed)
        await reaction.message.clear_reactions()


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


def get_role_named(guild, name):
    for role in guild.roles:
        if role.name == name:
            return role
    return None


def get_voice_channel_named(category, name):
    for channel in category.voice_channels:
        if channel.name == name:
            return channel
    return None


def get_text_channel_named(category, name):
    for channel in category.text_channels:
        if channel.name == name.lower():
            return channel
    return None


def get_category_named(guild, name):
    """
    If a role with a given name exists, it is returned, otherwise return None
    """
    for category in guild.categories:
        if category.name == name:
            return category
    return None


async def get_category_named_or_create(guild, name):
    """
    If a role with a given name exists, it is returned, otherwise create one
    """
    category = get_category_named(guild, name)
    if category is not None:
        return category
    return await guild.create_category_channel(name=name, reason="Added at project creation because none existed")


def member_from_participant(self, message, participant):
    def verify(member):
        # if not isinstance(member, discord.Member):
        #    return False
        #logging.info((participant, member.display_name))
        return participant.lower() in member.name.lower()

    #logging.info((participant, message.guild.members))
    valid_members = tuple(filter(
        verify,
        message.guild.members
    ))
    if len(valid_members) == 1:
        return valid_members[0]
    else:
        return None


def did_you_mean_project(guild, failed_name):
    def verify(project):
        if failed_name in project.lower():
            if project in MANAGEMENT_ROLES:
                return False
            return True
        return False

    role_names = [role.name for role in guild.roles]

    valid_names = tuple(filter(
        verify,
        role_names
    ))
    if len(valid_names) >= 1:
        return valid_names
    else:
        return None


async def members_from_participants(self, message, participants):
    members = []
    for participant in participants:
        new_member = member_from_participant(self, message, participant)
        if new_member is not None:
            members.append(new_member)
        else:
            msg_not_valid_member_embed = discord.Embed(
                color=0xc23f2b, title="Error", description=f"{participant} is not a valid member!")
            msg_not_valid_member = await message.channel.send(embed=msg_not_valid_member_embed)
            await self.add_active_panel(msg_not_valid_member, DeletableActivePanel(userid=message.author.id))
    if len(members):
        return members
    else:
        return None


async def make_new_project(members, project_name, output_info_channel, server):
    # Useful information to show the user
    info_str = ""

    # Check if project role exists, if so, use it
    existent_role = get_role_named(server, project_name)
    if existent_role is None:
        project_role = await server.create_role(name=project_name, reason="Project Created", mentionable=True)
        info_str = info_str + "Project role did not exist so one was created\n"
    else:
        project_role = existent_role
        info_str = info_str + "Used previously created project role\n"

    projects_category = await get_category_named_or_create(server, PROJECTS_CATEGORY)

    overwrites = {
        server.default_role: discord.PermissionOverwrite(read_messages=False),
        project_role: discord.PermissionOverwrite(
            read_messages=True, send_messages=True)
    }
    # Assign project members their role
    for member in members:
        await member.add_roles(project_role, reason="Project Added")

    # Check if voice channel exists, if so, use it and update permissions
    existent_voice_channel = get_voice_channel_named(
        projects_category, project_name)

    if existent_voice_channel is None:
        project_voice_channel = await projects_category.create_voice_channel(project_name, reason=f"Project {project_name} was created", overwrites=overwrites, position=0)
        await project_voice_channel.set_permissions(project_role, read_messages=True, send_messages=True)
        info_str = info_str + "Project voice channel did not exist so one was created\n"
    else:
        project_voice_channel = existent_voice_channel
        info_str = info_str + "Used previously created project voice channel\n"

    # Check if text channel exists, if so, use it and update permissions
    existent_text_channel = get_text_channel_named(
        projects_category, project_name)

    if existent_text_channel is None:
        project_text_channel = await projects_category.create_text_channel(project_name, reason=f"Project {project_name} was created", overwrites=overwrites, position=0)
        await project_text_channel.set_permissions(project_role, read_messages=True, send_messages=True)
        info_str = info_str + "Project text channel did not exist so one was created\n"
    else:
        project_text_channel = existent_text_channel
        info_str = info_str + "Used previously created project text channel\n"

    # create new google drive folder with "project_name" as its name if none exists
    gauth = GoogleAuth()
    drive = GoogleDrive(gauth)
    if gdrive_folder_exists(project_name, drive):
        info_str = info_str + "Used previously created project google drive folder for project\n"
    else:
        folder = drive.CreateFile({'title' : project_name, 'mimeType' : 'application/vnd.google-apps.folder'})
        folder.Upload()
        info_str = info_str + "Created project google drive folder for project\n"

    # If the project already exists, let the user know
    if existent_text_channel is not None and existent_voice_channel is not None and existent_role is not None:
        msg_duplicate_embed = discord.Embed(
            color=0xf2d61b, title="Project already exists!", description="Nothing was done")
        await output_info_channel.send(embed=msg_duplicate_embed)
        return

    # Give read/write access to all management roles
    for role_name in MANAGEMENT_ROLES:
        role = get_role_named(server, role_name)
        if role is not None:
            await project_text_channel.set_permissions(role, read_messages=True, send_messages=True, manage_messages=True)
            await project_voice_channel.set_permissions(role, read_messages=True, send_messages=True, manage_messages=True)

    enum_prefix = "• "

    msgacc_embed = discord.Embed(color=0x6db977)
    msgacc_embed.title = f"Successfully created new project - {project_name}!"
    msgacc_embed.description = enum_prefix.join(
        (enum_prefix+info_str).splitlines(True))
    await output_info_channel.send(embed=msgacc_embed)

def gdrive_folder_exists(folder_name, drive):
    # Checks if there's a folder with similar name in a given google drive
    folders = drive.ListFile(
        {'q': "mimeType='application/vnd.google-apps.folder' and trashed=false"}).GetList()
    for folder in folders:
        if folder['title'].lower() == folder_name.lower():
            return True
    return False
            
async def delete_project(project_name, message, user_input=False, self=None):
    output_info_channel, guild = message.channel, message.guild
    info_str = ""
    projects_category = get_category_named(guild, PROJECTS_CATEGORY)

    # Gather all project data
    project_voice_channel = get_voice_channel_named(
        projects_category, project_name)
    project_text_channel = get_text_channel_named(
        projects_category, project_name)
    project_role = get_role_named(guild, project_name)

    if user_input:
        # Fill info string for display
        if project_voice_channel is None:
            info_str = info_str + "No project voice channel detected\n"
        else:
            info_str = info_str + "Project voice channel detected and will be deleted\n"

        if project_text_channel is None:
            info_str = info_str + "No project text channel detected\n"
        else:
            info_str = info_str + "Project text channel detected and will be deleted\n"

        if project_role is None:
            info_str = info_str + "No project role detected\n"
        else:
            info_str = info_str + "Project role detected and will be deleted\n"

        if project_voice_channel is None and project_text_channel is None and project_role is None:
            msg_usr_none_embed = discord.Embed(color=0x99ab65)
            msg_usr_none_embed.title = "Oops, no project found!"
            possibilities = did_you_mean_project(guild, project_name)
            possibilities_str = ", ".join(possibilities)
            msg_usr_none_embed.description = f"Did you mean any of the following?\n{possibilities_str}"
            await output_info_channel.send(embed=msg_usr_none_embed)
            return

        enum_prefix = "• "
        info = enum_prefix.join((enum_prefix+info_str).splitlines(True))

        msg_usr_confirm_embed = discord.Embed(color=0x99ab65)
        msg_usr_confirm_embed.title = "Are you sure?"
        msg_usr_confirm_embed.description = f"This action will delete project **{project_name}**\n"
        msg_usr_confirm_embed.add_field(name="Info", value=info, inline=False)
        msg_usr_confirm = await output_info_channel.send(embed=msg_usr_confirm_embed)

        yn = DeleteProjectYesNo(project_voice_channel,
                                project_text_channel, 
                                project_role,
                                userid=message.author.id)

        await self.add_active_panel(msg_usr_confirm, yn)
        return

    # If no user input, just delete it
    await delete_project_data(project_voice_channel, project_text_channel, project_role)


async def command_project(self, message, args):
    if len(args) == 0:
        help_embed = discord.Embed(color=0x6db977, title="Project Help",
                                   description=f"**Usage**: {self.prefix}project [arg] [options]\n"
                                               f"Square bracketed arguments are optional\n"
                                               f"List of possible arguments:\n"
                                   )
        help_embed.add_field(
            name="new", value="**Description**: Creates new project.\n"
            "• Creates one role, one voice channel and one text channel named \"project_name\"\n"
            "• Assigns role to participants\n"
            "• Assigns channel managing permissions to management roles, and viewing permission only to participants\n"
            f"• Channels created under **{PROJECTS_CATEGORY}** category\n"
            "**Options**: project_name participant1 [participant2] ...\n", inline=False)
        help_embed.add_field(
            name="delete", value="**Description**: Deletes existent project or projects.\n"
            "• Deletes role and text/voice channels for each project if they exist\n"
            f"• Only affects text/voice channels under **{PROJECTS_CATEGORY}** category\n"
            "**Options**: project1 [project2] ...", inline=False)
        help_msg = await message.channel.send(embed=help_embed)
        await self.add_active_panel(help_msg, DeletableActivePanel(userid=message.author.id))
        
    elif len(args) >= 2:
        if args[0] == "new":
            project_name, *participants = args[1:]
            participants_str = ", ".join(participants)
            names_str = ""
            members = await members_from_participants(self, message, participants)
            if members is not None:
                names = list(member.display_name for member in members)
                names_str = ", ".join(names)
            if members is None or len(members) != len(args) - 2:
                msg_no_members_embed = discord.Embed(
                    color=0xc23f2b, title="Input Error", description=f"Please provide valid member names.\n Names provided: {participants_str}\n Corresponding server members: {names_str}")
                msg_no_members = await message.channel.send(embed=msg_no_members_embed)
                await self.add_active_panel(msg_no_members, DeletableActivePanel(userid=message.author.id))
                return
            msg_scc_embed = discord.Embed(color=0x99ab65)
            msg_scc_embed.title = "Are you sure?"
            msg_scc_embed.description = f"This action will create one role, one voice channel and one text channel!\n" \
                                        f"Both channels will only be visible for the project members and management\n" \
                                        f"**Project name:** {project_name}\n"\
                                        f"**Participants:** {names_str}"
            msg_scc = await message.channel.send(embed=msg_scc_embed)

            yn = CreateProjectYesNo(project_name, members, userid=message.author.id)

            await self.add_active_panel(msg_scc, yn)
            
        elif args[0] == "delete":
            if len(args) >= 2:
                projects_to_delete = args[1:]

                for project in projects_to_delete:
                    await delete_project(project, message, user_input=True, self=self)
        else:
            msg_unrecognized_embed = discord.Embed(color=0x99ab65)
            msg_unrecognized_embed.title = "Unrecognized option!\n"
            msg_unrecognized_embed.description = f"Try \"**{self.prefix}project**\" for more information"
            msg_unrecognized = await message.channel.send(embed=msg_unrecognized_embed)
            self.add_active_panel(msg_unrecognized, DeletableActivePanel(userid=message.author.id))

    else:
        msg_err_embed = discord.Embed(color=0xfcba03)
        msg_err_embed.title = "Improper command usage"
        msg_err_embed.description = f"{self.prefix}project for more information"
        msgerr = await message.channel.send(embed=msg_err_embed)
        self.add_active_panel(msgerr, DeletableActivePanel(userid=message.author.id))
