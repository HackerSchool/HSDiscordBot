import aiohttp
import discord


async def download_file(self, reaction, user, panel):
    self.remove_active_panel(reaction.message, panel["user"])
    content = reaction.message.content
    embed = discord.Embed(title="Success!", color=0x6db977)
    embed.description = "Downloaded sprint report"
    await reaction.message.edit(content=content, embed=embed)
    await reaction.message.clear_reactions()

async def process_attachments(self, message):
    for attachment in message.attachments:
        if "sprint" in attachment.filename.lower():
            msg = await self.send_info(message.channel, f"Should I capture '{attachment.filename}' as a sprint report?")
            self.add_active_panel(msg, message.author, {"yesno"}, {
                "on_accept": download_file
            })
            await msg.add_reaction("✅")
            await msg.add_reaction("❌")
