import os
import pickle
import pandas as pd

import client

import aiohttp
import discord
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

from panels import YesNoActivePanel

from utils import PROJECTS_CATEGORY

from enum import Enum, auto
from itertools import combinations

# 1ª posição: índice da coluna em que estão os nomes iniciais
# 2ª posição: índice da coluna em que estão os nomes destino
cols = (0, 1)

# índice da linha em que está o header [linha 1 (excel ou google sheets) -> índice 0]. se nenhuma, escolher None
header = None

# file to store all name pairs
name_pairs_file = "names.pkl"


class type(Enum):
    sprint = auto()
    name_pairs = auto()

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
                    embed = discord.Embed(title="Success!", color=0x6db977)
                    embed.description = "Downloaded sprint report"
                else:
                    embed = discord.Embed(title="Fail!", color=0xff0000)
                    embed.description = "Upload to storage has failed"
                os.remove(name)
            else:
                embed = discord.Embed(title="Fail!", color=0xff0000)
                embed.description = "Download failed"

        if self.type == type.name_pairs:
            if result:
                embed = discord.Embed(title="Success!", color=0x6db977)
                embed.description = "Downloaded name pairs"
                await store_new_pairs(name, reaction.message.channel)
                os.remove(name)
            else:
                embed = discord.Embed(title="Fail!", color=0xff0000)
                embed.description = "Download failed"
        await reaction.message.edit(content=content, embed=embed)
        await reaction.message.clear_reactions()

        
    async def on_decline(self, client, reaction, user):
        await self.message.delete()

async def store_new_pairs(new_pair_name, channel):
    # read excel and convert to list
    df = pd.read_excel(new_pair_name, header=None, usecols=(0, 1), squeeze=True)
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
        embed = discord.Embed(title="Bad usernames!", color=0xff0000)
        embed.description = "These pairs were removed for containing invalid discord usernames (in the first position): " + str(invalid_pairs)
        await channel.send(embed=embed)

    if len(known_pairs) > 0:
        embed = discord.Embed(title="Username Pairs Added!", color=0x6db977)
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
        if "sprint" in attachment.filename.lower():
            if message.channel.category.name.lower() == PROJECTS_CATEGORY.lower():
                msg = await self.send_info(message.channel, f"Should I capture '{attachment.filename}' as a sprint report?")
                yn = CollectYesNo(attachment, type.sprint, userid=message.author.id)
                await self.add_active_panel(msg, yn)
            else:
                await self.send_info(message.channel, f"If you mean to register '{attachment.filename}' as a sprint report, "
                                                       "you need to send it through your project's text channel, which should "
                                                      f"be under {PROJECTS_CATEGORY} category!")


        if "name" in attachment.filename.lower():
            msg = await self.send_info(message.channel, f"Should I store name pairs in '{attachment.filename}' to replace newcomers' names?")
            yn = CollectYesNo(attachment, type.name_pairs, userid=message.author.id)
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

