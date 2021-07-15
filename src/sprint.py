import os

import aiohttp
import discord
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

from panels import YesNoActivePanel

from utils import PROJECTS_CATEGORY

class CollectYesNo(YesNoActivePanel):
    def __init__(self, attachment, userid=None):
        super().__init__(userid=userid)
        self.attachment = attachment

    async def on_accept(self, client, reaction, user):
        name = os.path.join(client.sprint_path, self.attachment.filename)
        result = await download_file(self.attachment.url, name)

        content = reaction.message.content
        project_name = reaction.message.channel.name
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
        await reaction.message.edit(content=content, embed=embed)
        await reaction.message.clear_reactions()
        
    async def on_decline(self, client, reaction, user):
        await self.message.delete()


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



async def handler_sprint(self, message):
    """Used when a file is sent to a channel"""
    for attachment in message.attachments:
        if "sprint" in attachment.filename.lower():
            if message.channel.category.name.lower() == PROJECTS_CATEGORY.lower():
                msg = await self.send_info(message.channel, f"Should I capture '{attachment.filename}' as a sprint report?")
                yn = CollectYesNo(attachment, userid=message.author.id)
                await self.add_active_panel(msg, yn)
            else:
                await self.send_info(message.channel, f"If you mean to register '{attachment.filename}' as a sprint report, "
                                                       "you need to send it through your project's text channel, which should "
                                                      f"be under {PROJECTS_CATEGORY} category!")
