from logging import ERROR
import discord
from cfg import WARNING_COLOR, SUCCESS_COLOR, ERROR_COLOR, MINIMUM_SUFFICIENT_ATTENDANCE_PERCENTAGE
import datetime
import logging


class PresenceMarker:
    def __init__(self, guild, channel):
        self.guild = guild
        self.channel = channel
        self.attendees = []
    
    async def mark_presence(self, client=None):
        cur_active_members = members_in_vc(self.guild)
        if len(cur_active_members) == 0:
            return
        for member in cur_active_members:
            if member in self.attendees:
                cur_active_members.remove(member)
        self.attendees.extend(cur_active_members)
    
    async def deliver_attendance(self, client=None):
        await _deliver_attendance(self.attendees, self.channel)

def members_in_vc(guild : discord.Guild):
    all_members = guild.members
    members = []
    for member in all_members:
        if member.voice is not None:
            members.append(member)
    return members

async def _deliver_attendance(members, channel):
    names = [member.display_name for member in members ]

    if len(names) == 0:
        embed = discord.Embed(title="Marked attendance of zero users.", color=ERROR_COLOR)
        embed.description = "Looks like no one showed up."
    elif len(names) == 1:
        embed = discord.Embed(title=f"Marked attendance of one user.", color=SUCCESS_COLOR)
        embed.description = "Attendee:\n" + ", ".join(names)
    else:
        embed = discord.Embed(title=f"Marked attendance of {len(names)} users.", color=SUCCESS_COLOR)
        embed.description = "Attendees:\n" + ", ".join(names)

    await channel.send(embed=embed)

def mark_presence_over_time(client, guild, channel, duration_seconds):
    now = datetime.datetime.now()
    
    check_intervals = duration_seconds*MINIMUM_SUFFICIENT_ATTENDANCE_PERCENTAGE/100
    attendance_checker = PresenceMarker(guild, channel)
    
    mark_attendance_time = 0
    while mark_attendance_time < duration_seconds:
        t1 = now + datetime.timedelta(seconds = mark_attendance_time)
        client.schedule(t1, t1, attendance_checker.mark_presence)
        mark_attendance_time += check_intervals
    t2 = now + datetime.timedelta(seconds = duration_seconds)
    client.schedule(t2, t2, attendance_checker.deliver_attendance)
    


async def command_present(self, message, args):
    user_input = True
    if '-y' in args:
        user_input = False

    if len(args) == 0:
        present = members_in_vc(message.channel.guild)
        await _deliver_attendance(present, message.channel)
        return
    
    if len(args) == 1:
        try:
            duration_minutes = float(args[0])
            
            duration_seconds = duration_minutes * 60
            mark_presence_over_time(self, message.guild, message.channel, duration_seconds)

            embed = discord.Embed(title="Recording attendance", color=SUCCESS_COLOR)
            embed.description = f"Tracking attendance starting now for {duration_minutes} minutes.\n"
            embed.description += "Marked attendance is only guaranteed for members which stay on a voice channel for "
            embed.description += f"at least {MINIMUM_SUFFICIENT_ATTENDANCE_PERCENTAGE}% of the total recording time."
            await message.channel.send(embed=embed)
            return
        except NameError:
            logging.log(NameError)
            pass

    
    embed = discord.Embed(title="Improper command usage!", color=ERROR_COLOR)
    embed.description = f"Arguments '{args}' are invalid."
