import os
import pickle
import pandas as pd

import client

import aiohttp
import discord
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

from panels import YesNoActivePanel

from utils import PROJECTS_CATEGORY, WARNING_COLOR, SUCCESS_COLOR, ERROR_COLOR

from enum import Enum, auto
from itertools import combinations

from project import make_new_project, member_from_participant

# first position: index of column containing discord usernames
# second position: index of column containing wanted server nicknames
cols_name_pairs = (0, 1)

# index of header line. if none, header_name_pairs should be set to None
header_name_pairs = None
header_projects = None

# first position: index of column cntaining project names
# second position: index of first column containing member names, it is assumed that all populated columns to the right contain members' names
# cols_projects = (0, 1)


# file to store all name pairs
name_pairs_file = "names.pkl"

# attachments' file names started with these characters are detected, others are ignored
sprint_prefix = "sprint"        # as sprint reports
names_prefix = "name"           # as name pairs
projects_prefix = "project"     # as new projects

class type(Enum):
    sprint = auto()
    name_pairs = auto()
    projects = auto()

class CollectYesNo(YesNoActivePanel):
    def __init__(self, attachment, type, userid=None):
        super().__init__(userid=userid)
        self.attachment = attachment
        self.type = type

    async def on_accept(self, client, reaction, user):
        name = os.path.join(client.sprint_path, self.attachment.filename)
        result = await download_file(self.attachment.url, name)

        content = reaction.message.content
        project_name = reaction.message.channel.name

        if self.type == type.sprint:
            if result:
                if send_files(name, project_name):
                    embed = discord.Embed(title="Success!", color=SUCCESS_COLOR)
                    embed.description = "Downloaded sprint report"
                else:
                    embed = discord.Embed(title="Fail!", color=ERROR_COLOR)
                    embed.description = "Upload to storage has failed"
                os.remove(name)
            else:
                embed = discord.Embed(title="Fail!", color=ERROR_COLOR)
                embed.description = "Download failed"

        if self.type == type.name_pairs:
            if result:
                embed = discord.Embed(title="Success!", color=SUCCESS_COLOR)
                embed.description = "Downloaded name pairs"
                await store_new_pairs(name, reaction.message.channel)
                os.remove(name)
            else:
                embed = discord.Embed(title="Fail!", color=ERROR_COLOR)
                embed.description = "Download failed"

        if self.type == type.projects:
            if result:
                embed = discord.Embed(title="Success!", color=SUCCESS_COLOR)
                embed.description = "Downloaded new projects file. Analising project data and attempting to create projects"
                # doing this here so the order is and if an error occurs this message has already been sent
                await reaction.message.edit(content=content, embed=embed)
                await reaction.message.clear_reactions()
                await create_new_projects(name, reaction.message.channel)
                os.remove(name)
            else:
                embed = discord.Embed(title="Fail!", color=ERROR_COLOR)
                embed.description = "Download failed"


        await reaction.message.edit(content=content, embed=embed)
        await reaction.message.clear_reactions()

        
    async def on_decline(self, client, reaction, user):
        await self.message.delete()

async def create_new_projects(new_pair_name, channel):
    # read excel and convert to list
    df = pd.read_excel(new_pair_name, header=header_projects, squeeze=True)
    new_projects_data = df.values.tolist()

    # create projects and store invalid names
    invalid_names = []
    for project in new_projects_data:
        project_name, *participants = project
        participants = [name for name in participants if str(name) != 'nan']
        
        project_members = []
        for participant in participants:
            new_member = member_from_participant(channel.guild, participant)
            if new_member is not None:
                project_members.append(new_member)
            else:
                invalid_names.append(participant)

        await make_new_project(project_members, project_name, channel, channel.guild)

    # notify user of invalid names so they can add them to their projects
    if len(invalid_names) > 0:
        embed = discord.Embed(title="Invalid project participants", color=WARNING_COLOR)
        embed.description = f"No server members maching these names could be found. Add them to their projects by giving them the project role.\n{invalid_names}"
        await channel.send(embed=embed)

async def store_new_pairs(new_pair_name, channel):
    # read excel and convert to list
    df = pd.read_excel(new_pair_name, header=header_name_pairs, usecols=cols_name_pairs, squeeze=True)
    new_pairs = df.values.tolist()

    # load previous known name pairs
    open(name_pairs_file,"a+")
    try:
        known_pairs = pickle.load(open(name_pairs_file,"rb"))
    except EOFError:
        known_pairs = []

    # append newly created name pairs -     
            # if a source username is present more than once, discard one
            # if a destination username is present more than once, do nothing
    known_pairs.extend(new_pairs)
    for combo in combinations(known_pairs, 2):
        kpair1 = combo[0]
        kpair2 = combo[1]
        if kpair1[0] == kpair2[0]:
            kpair1[1] = kpair2[1]
            known_pairs.remove(kpair1)

    # if any aren't valid discord usernames with discriminator, send warning message with those names
    invalid_pairs = []
    for pair in known_pairs:
        usr = pair[0]
        if len(usr) < 5 or usr[-5] != '#' or int(usr[-4:]) < 0 or int(usr[-4:]) > 9999:
            invalid_pairs.append(pair)
            known_pairs.remove(pair)
            if pair in new_pairs:
                new_pairs.remove(pair)

    if len(invalid_pairs) > 0:
        embed = discord.Embed(title="Bad usernames!", color=ERROR_COLOR)
        embed.description = "These pairs were removed for containing invalid discord usernames (in the first position): " + str(invalid_pairs)
        await channel.send(embed=embed)

    if len(known_pairs) > 0:
        embed = discord.Embed(title="Username Pairs Added!", color=WARNING_COLOR)
        embed.description = "The following pairs were added or updated: " + str(new_pairs)
        await channel.send(embed=embed)

    # store everything in name_pairs_file
    file_to_store = open(name_pairs_file, 'wb')
    pickle.dump(known_pairs, file_to_store)

async def download_file(url, path):
    """Download a file from the internet

    Args:
        url (str): URL pointing to the file
        path (str): Where to save the file to

    Returns:
        bool: True if the operation was successfull
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                return False
            content = await response.read()
    try:
        with open(path, "wb") as file:
            file.write(content)
    except Exception:
        return False
    return True


def send_files(file_name, folder_name):
    """
    Sends file to google drive folder, assuming first two characters in file name are '.\'
    Returns: 
        -True if successful
        -False if unsuccessful
    """
    gauth = GoogleAuth()
    drive = GoogleDrive(gauth)
    gfile = drive.CreateFile({'title': file_name})

    folders = drive.ListFile(
        {'q': "title='" + folder_name + "' and mimeType='application/vnd.google-apps.folder' and trashed=false"}).GetList()
    for folder in folders:
        if folder['title'].lower() == folder_name.lower():
            
            gfile = drive.CreateFile({'title': file_name[2:], 'parents': [{'id': folder['id']}]})
            gfile.SetContentFile(file_name)
            gfile.Upload()
            return True
    return False



async def handler_attachment(self, message):
    """Used when a file is sent to a channel"""
    for attachment in message.attachments:
        if sprint_prefix in attachment.filename.lower():
            if message.channel.category.name.lower() == PROJECTS_CATEGORY.lower():
                msg = await self.send_info(message.channel, f"Should I capture '{attachment.filename}' as a sprint report?")
                yn = CollectYesNo(attachment, type.sprint, userid=message.author.id)
                await self.add_active_panel(msg, yn)
            else:
                await self.send_info(message.channel, f"If you mean to register '{attachment.filename}' as a sprint report, "
                                                       "you need to send it through your project's text channel, which should "
                                                      f"be under {PROJECTS_CATEGORY} category!")


        if names_prefix in attachment.filename.lower():
            msg = await self.send_info(message.channel, f"Should I store name pairs in '{attachment.filename}' to replace newcomers' names?")
            yn = CollectYesNo(attachment, type.name_pairs, userid=message.author.id)
            await self.add_active_panel(msg, yn)

        if projects_prefix in attachment.filename.lower():
            msg = await self.send_info(message.channel, f"Should I use '{attachment.filename}' to create new projects?")
            yn = CollectYesNo(attachment, type.projects, userid=message.author.id)
            await self.add_active_panel(msg, yn)



def add_member_name_change(client):
    @client.event
    async def on_member_join(member):
        open(name_pairs_file,"a+")
        try:
            known_pairs = pickle.load(open(name_pairs_file,"rb"))
        except EOFError:
            known_pairs = []

        for pair in known_pairs:
            if pair[0] == str(member):
                await member.edit(nick = pair[1], reason="Name pair present in given file")
                return

