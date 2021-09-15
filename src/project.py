import logging
from typing import Optional

import discord
from client import HSBot

from utils import get_category_named, get_role_named, get_text_channel_named, get_voice_channel_named, member_from_participant
from panels import DeletableActivePanel, YesNoActivePanel
from cfg import PROJECTS_CATEGORY, WARNING_COLOR, SUCCESS_COLOR, ERROR_COLOR, MANAGEMENT_ROLES, MASTER_FOLDER_ID

from gdrive import get_gdrive_folder_named, create_gdrive_folder

class DeleteProjectYesNo(YesNoActivePanel):
    def __init__(self, project_voice_channel, project_text_channel, project_role, project_folder, userid=None):
        super().__init__(userid=userid)
        self.userid = userid
        self.project_voice_channel = project_voice_channel
        self.project_text_channel = project_text_channel
        self.project_role = project_role
        self.project_folder = project_folder

    async def delete_project_data(self):
        await del_proj_data(self.project_voice_channel, self.project_text_channel, self.project_role, self.project_folder)

    async def on_accept(self, client : HSBot, reaction : discord.Reaction, user : discord.User):
        channel = reaction.message.channel
        await self.delete_project_data()
        msg_deletion_success_embed = discord.Embed(
            title="Deletion successful!", description=f"**{self.project_role.name}** removed")
        await channel.send(embed=msg_deletion_success_embed)
        await reaction.message.clear_reactions()

    async def on_decline(self, client : HSBot, reaction : discord.Reaction, user : discord.User):
        channel = reaction.message.channel
        msgreff_embed = discord.Embed(color=WARNING_COLOR)
        msgreff_embed.title = "Project deletion aborted!"
        msgreff_embed.description = f"**{self.project_name} was untouched"
        await channel.send(embed=msgreff_embed)
        await reaction.message.clear_reactions()


async def del_proj_data(project_voice_channel : discord.VoiceChannel, project_text_channel : discord.TextChannel, project_role : discord.Role, project_folder):
    if project_voice_channel is not None:
        await project_voice_channel.delete()
    if project_text_channel is not None:
        await project_text_channel.delete()
    if project_role is not None:
        await project_role.delete()

    if project_folder is not None:
        project_folder['title'] = project_folder['title'] + '-CLOSED'
        project_folder.Upload()

def did_you_mean_project(guild : discord.Guild, failed_name : str):
    def verify(project : str):
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


async def members_from_participants(self : HSBot, guild : discord.Guild, info_channel : discord.TextChannel, participants : list[discord.User]):
    members = []
    for participant in participants:
        new_member = member_from_participant(guild, participant)
        if new_member is not None:
            members.append(new_member)
        else:
            msg_not_valid_member_embed = discord.Embed(
                color=ERROR_COLOR, title="Error", description=f"{participant} is not a valid member!")
            msg_not_valid_member = await info_channel.send(embed=msg_not_valid_member_embed)
            await self.add_active_panel(msg_not_valid_member, DeletableActivePanel())
    if len(members):
        return members
    else:
        return None

def new_project_confirmation_embed(project_name : str, names_str : str):
    msg_scc_embed = discord.Embed(color=WARNING_COLOR)
    msg_scc_embed.title = "Are you sure?"
    msg_scc_embed.description = f"This action will create one role, one voice channel, one text channel and a corresponding google drive folder!\n" \
                                f"Both channels will only be visible for the project members and management\n" \
                                f"**Project name:** {project_name}\n"\
                                f"**Participants:** {names_str}"
    return msg_scc_embed


async def make_new_project(members : Optional[list[discord.User]], project_name : str, output_info_channel : discord.TextChannel, server : discord.Guild):
    # Useful information to show the user
    info_str = ""
    just_add_members = False
    names_str = ""

    # Check if project role exists, if not, create it
    projects_category = get_category_named(server, PROJECTS_CATEGORY)
    if projects_category is None:
        info_str = info_str + "Project category did not exist so one was created\n"
        projects_category = await server.create_category_channel(name=PROJECTS_CATEGORY, reason="Added at project creation because none existed")

    # Check if project role exists, if so, use it
    existent_role = get_role_named(server, project_name)
    if existent_role is None:
        project_role = await server.create_role(name=project_name, reason="Project Created", mentionable=True)
        info_str = info_str + "Project role did not exist so one was created\n"
    else:
        project_role = existent_role
        info_str = info_str + "Used previously created project role\n"

    overwrites = {
        server.default_role: discord.PermissionOverwrite(read_messages=False),
        project_role: discord.PermissionOverwrite(
            read_messages=True, send_messages=True)
    }

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
    existent_gdrive_folder = get_gdrive_folder_named(project_name)
    if existent_gdrive_folder is None:
        create_gdrive_folder(project_name)
        info_str = info_str + "Created project google drive folder for project\n"
    else:
        info_str = info_str + "Used previously created project google drive folder for project\n"

    if members is None or len(members) == 0:
        info_str = info_str + "This project contains no members. Add them by assigning them the newly created project role\n"
    else:
        names = list(member.display_name for member in members)
        names_str = ", ".join(names)
        info_str = info_str + names_str

    # If the project already exists, let the user know
    if existent_text_channel is not None and existent_voice_channel is not None and existent_role is not None and existent_gdrive_folder is not None:
        if members is None or len(members) == 0:
            msg_duplicate_embed = discord.Embed(
                color=WARNING_COLOR, title=f"Project '{project_name}' already exists!", description=f"Nothing was done.")
            await output_info_channel.send(embed=msg_duplicate_embed)
            return
        else:
            msg_duplicate_embed = discord.Embed(
                color=WARNING_COLOR, title=f"Project '{project_name}' already exists!", description="Only assigned new members")
            await output_info_channel.send(embed=msg_duplicate_embed)
            just_add_members = True

    # Assign project members their role
    if members is not None:
        for member in members:
            await member.add_roles(project_role, reason=f"Project '{project_name}' Added")

    if just_add_members == True:
        return

    # Give read/write access to all management roles
    for role_name in MANAGEMENT_ROLES:
        role = get_role_named(server, role_name)
        if role is not None:
            await project_text_channel.set_permissions(role, read_messages=True, send_messages=True, manage_messages=True)
            await project_voice_channel.set_permissions(role, read_messages=True, send_messages=True, manage_messages=True)

    enum_prefix = "• "

    welcome_message = f"<@&{project_role.id}>\n"
    welcome_message += f"This channel homes project '{project_name}'\n"
    welcome_message += f"Currently, the members are {names_str}\n"
    welcome_message += f"You can submit sprint reports through this text channel by simply sending your "
    welcome_message += f"sprint report as an attachment to the channel, ensuring its name "
    welcome_message += f"starts with 'sprint'. Examples of valid names are 'sprint1.pdf', "
    welcome_message += f"'sprint_january.zip', 'sprint_buffer' and 'sprint report.jpg'\n"
    welcome_message += f"That's all from me!"
    await project_text_channel.send(content = welcome_message)

    msgacc_embed = discord.Embed(color=SUCCESS_COLOR)
    msgacc_embed.title = f"Successfully created new project - {project_name}!"
    msgacc_embed.description = enum_prefix.join(
        (enum_prefix+info_str).splitlines(True))
    await output_info_channel.send(embed=msgacc_embed)
            
async def delete_project(project_name : str, message : discord.Message, user_input : bool =False, self : Optional[HSBot] = None):
    output_info_channel, guild = message.channel, message.guild
    info_str = ""
    projects_category = get_category_named(guild, PROJECTS_CATEGORY)

    # Gather all project data
    project_voice_channel = get_voice_channel_named(projects_category, project_name)
    project_text_channel = get_text_channel_named(projects_category, project_name)
    project_role = get_role_named(guild, project_name)
    project_folder = get_gdrive_folder_named(project_name)

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

        if project_folder is None:
            info_str = info_str + "No Google Drive project folder detected"
        else:
            info_str = info_str + "Google Drive project folder detected and will be marked as CLOSED\n"

        if project_voice_channel is None and project_text_channel is None and project_role is None:
            msg_usr_none_embed = discord.Embed(color=ERROR_COLOR)
            msg_usr_none_embed.title = "Oops, no project found!"
            possibilities = did_you_mean_project(guild, project_name)
            possibilities_str = ", ".join(possibilities)
            msg_usr_none_embed.description = f"Did you mean any of the following?\n{possibilities_str}"
            await output_info_channel.send(embed=msg_usr_none_embed)
            return

        enum_prefix = "• "
        info = enum_prefix.join((enum_prefix+info_str).splitlines(True))

        msg_usr_confirm_embed = discord.Embed(color=WARNING_COLOR)
        msg_usr_confirm_embed.title = "Are you sure?"
        msg_usr_confirm_embed.description = f"This action will delete project **{project_name}**\n"
        msg_usr_confirm_embed.add_field(name="Info", value=info, inline=False)
        msg_usr_confirm = await output_info_channel.send(embed=msg_usr_confirm_embed)

        yn = DeleteProjectYesNo(project_voice_channel,
                                project_text_channel, 
                                project_role,
                                project_folder,
                                userid=message.author.id)

        await self.add_active_panel(msg_usr_confirm, yn)
        return
    # If no user input, just delete it
    else:
        await del_proj_data(project_voice_channel, project_text_channel, project_role, project_folder)

async def project_help(self : HSBot, message : str): # message contains both user and channel info
    help_embed = discord.Embed(color=WARNING_COLOR, title="Project Help",
                                description=f"**Usage**: {self.prefix}project [arg] [options]\n"
                                            f"Square bracketed arguments are optional\n"
                                            f"List of possible arguments:\n"
                                )
    help_embed.add_field(
        name="new", value="**Description**: Creates new project.\n"
        "• Creates one role, one voice channel, one text channel and corresponding google drive folder named \"project_name\"\n"
        "• Assigns role to participants\n"
        "• Assigns channel managing permissions to management roles, and viewing permission only to participants\n"
        f"• Channels created under **{PROJECTS_CATEGORY}** category\n"
        "• If no arguments are given, a private message is sent and the project is configured through guided text input\n"
        "**Options**: project_name participant1 [participant2] ...\n", inline=False)
    help_embed.add_field(
        name="delete", value="**Description**: Deletes existent project or projects.\n"
        "• Deletes role and text/voice channels for each project if they exist\n"
        f"• Only affects text/voice channels under **{PROJECTS_CATEGORY}** category\n"
        "• Calling it with the option '-y' disables the need for further user input\n"
        "**Options**: project1 [project2] ...", inline=False)
    help_msg = await message.channel.send(embed=help_embed)
    await self.add_active_panel(help_msg, DeletableActivePanel(userid=message.author.id))

async def validate_participants(self : HSBot, guild : discord.Guild, channel : discord.TextChannel, participants : list[discord.User]):
    participants_str = ", ".join(participants)
    members = await members_from_participants(self, guild, channel, participants)
    names_str = ""
    if members is not None:
        names = list(member.display_name for member in members)
        names_str = ", ".join(names)
        if len(members) < len(participants):
            msg_invalid_members_embed = discord.Embed(
                color=WARNING_COLOR, title="Some members not found", description=f"Names provided: {participants_str}\n Valid corresponding server members: {names_str}")
            msg_no_members = await channel.send(embed=msg_invalid_members_embed)
            await self.add_active_panel(msg_no_members, DeletableActivePanel())
    if members is None or len(members) == 0:
        names_str = "<none>"
        msg_no_members_embed = discord.Embed(
            color=WARNING_COLOR, title="Warning! No members!", description=f"You're about to create a project without any members!\n" \
                                                                        "Project role will be created, and will have to be manually " \
                                                                        "assigned to project members, or you can rerun the command " \
                                                                        "with member names later and they will be added to the project " \
                                                                        "withouth creating new voice/text channels, role and google drive folder.")
        msg_no_members = await channel.send(embed=msg_no_members_embed)
    return members, names_str
