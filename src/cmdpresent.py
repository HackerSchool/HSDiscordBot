from logging import ERROR
import discord
from utils import WARNING_COLOR, SUCCESS_COLOR, ERROR_COLOR

def members_in_vc(guild : discord.Guild):
    all_members = guild.members
    members = []
    for member in all_members:
        if member.voice is not None:
            members.append(member)
    return members


async def command_present(self, message, args):
    user_input = True
    if '-y' in args:
        user_input = False

    present = members_in_vc(message.channel.guild)

    names = [member.display_name for member in present ]

    if len(names) == 0:
        embed = discord.Embed(title="There are no users in voice chat at the moment.", color=ERROR_COLOR)
        embed.description = "Looks like no one showed up yet."
    elif len(names) == 1:
        embed = discord.Embed(title=f"There is 1 user in voice chat at the moment.", color=SUCCESS_COLOR)
        embed.description = "Attendee:\n" + ", ".join(names)
    else:
        embed = discord.Embed(title=f"There are {len(names)} users in voice chat at the moment.", color=SUCCESS_COLOR)
        embed.description = "Attendees:\n" + ", ".join(names)

    await message.channel.send(embed=embed)
