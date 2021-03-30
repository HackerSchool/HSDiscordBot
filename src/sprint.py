import os

import aiohttp
import discord


async def download_file(url, path):
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

def on_accept(attachment):
    async def on_accept_wrapper(self, reaction, user, panel):
        self.remove_active_panel(reaction.message, panel["user"])
        
        name = os.path.join(self.sprint_path, attachment.filename)
        result = await download_file(attachment.url, name)
        
        content = reaction.message.content
        if result:
            embed = discord.Embed(title="Success!", color=0x6db977)
            embed.description = "Downloaded sprint report"
        else:
            embed = discord.Embed(title="Fail!", color=0xff0000)
            embed.description = "Download failed"
        await reaction.message.edit(content=content, embed=embed)
        await reaction.message.clear_reactions()
    return on_accept_wrapper

async def process_attachments(self, message):
    for attachment in message.attachments:
        if "sprint" in attachment.filename.lower():
            msg = await self.send_info(message.channel, f"Should I capture '{attachment.filename}' as a sprint report?")
            self.add_active_panel(msg, message.author, {"yesno"}, {
                "on_accept": on_accept(attachment)
            })
            await msg.add_reaction("✅")
            await msg.add_reaction("❌")
