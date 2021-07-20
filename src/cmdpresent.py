from logging import ERROR
import discord
from utils import WARNING_COLOR, SUCCESS_COLOR, ERROR_COLOR
import datetime
import logging

# a user which is continuously present in least this % of the event is guaranteed to be marked as present
minimum_sufficient_attendance_percentage = 40

class PresenceMarker:
    def __init__(self, guild, channel):
        self.guild = guild
        self.channel = channel
        self.attendees = []
    
    async def mark_presence(self, dummy):
        cur_active_members = members_in_vc(self.guild)
        if len(cur_active_members) == 0:
            return
        for member in cur_active_members:
            if member in self.attendees:
                cur_active_members.remove(member)
        self.attendees.extend(cur_active_members)
    
    async def deliver_attendance(self, dummy):
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
        embed = discord.Embed(title=f"Marked attendance of one users.", color=SUCCESS_COLOR)
        embed.description = "Attendee:\n" + ", ".join(names)
    else:
        embed = discord.Embed(title=f"Marked attendance of {len(names)} users.", color=SUCCESS_COLOR)
        embed.description = "Attendees:\n" + ", ".join(names)

    await channel.send(embed=embed)

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
            now = datetime.datetime.now()
            
            duration_seconds = duration_minutes * 60
            check_intervals = duration_seconds*minimum_sufficient_attendance_percentage/100

            attendance_checker = PresenceMarker(message.guild, message.channel)
            
            mark_attendance_time = 0
            while mark_attendance_time < duration_seconds:
                t1 = now + datetime.timedelta(seconds = mark_attendance_time)
                self.schedule(t1, t1, attendance_checker.mark_presence)
                mark_attendance_time += check_intervals
            t2 = now + datetime.timedelta(seconds = duration_seconds)
            self.schedule(t2, t2, attendance_checker.deliver_attendance)

            return
        except NameError:
            logging.log(NameError)
            pass

    
    embed = discord.Embed(title="Improper command usage!", color=ERROR_COLOR)
    embed.description = f"Arguments '{args}' are invalid."
