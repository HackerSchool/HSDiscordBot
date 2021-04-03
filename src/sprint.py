import os

import aiohttp
import discord
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

from common import CONFIRM, DECLINE, YesNo


class CollectYesNo(YesNo):
    def __init__(self, attachment):
        super().__init__()
        self.attachment = attachment

    async def on_accept(self, client, reaction, user, panel):
        await client.remove_active_panel(reaction.message, panel.user)

        name = os.path.join(client.sprint_path, self.attachment.filename)
        result = await download_file(self.attachment.url, name)

        content = reaction.message.content
        if result:
            if send_files(name, "Test"):
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
    Sends file to google drive folder
    Returns: 
        -True if successful
        -False if unsuccessful
    """
    gauth = GoogleAuth()
    # Try to load saved client credentials
    gauth.LoadCredentialsFile("credentials")
    if gauth.credentials is None:
        # Authenticate if they're not there
        gauth.LocalWebserverAuth()
    elif gauth.access_token_expired:
        # Refresh them if expired
        gauth.Refresh()
    else:
        # Initialize the saved creds
        gauth.Authorize()
    # Save the current credentials to a file
    gauth.SaveCredentialsFile("credentials")
    drive = GoogleDrive(gauth)

    folders = drive.ListFile(
        {'q': "title='" + folder_name + "' and mimeType='application/vnd.google-apps.folder' and trashed=false"}).GetList()
    for folder in folders:
        if folder['title'] == folder_name:
            gfile = drive.CreateFile({'parents': [{'id': folder['id']}]})
            gfile.SetContentFile(file_name)
            gfile.Upload()
            return True
    return False


async def handler_sprint(self, message):
    """Used when a file is sent to a channel"""
    for attachment in message.attachments:
        if "sprint" in attachment.filename.lower():
            msg = await self.send_info(message.channel, f"Should I capture '{attachment.filename}' as a sprint report?")
            yn = CollectYesNo(attachment)
            self.add_active_panel(msg, message.author, {"yesno"}, yn)
            await msg.add_reaction(CONFIRM)
            await msg.add_reaction(DECLINE)
