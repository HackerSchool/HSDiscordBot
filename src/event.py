from __future__ import annotations

import datetime
import logging
import traceback
from typing import Any, Optional, Tuple

import discord

from activepanel import ActivePanel
from cfg import (ACCEPT, DECLINE, ERROR_COLOR, SUCCESS_COLOR, TENTATIVE,
                 WARNING_COLOR)
from client import HSBot
from panels import DELETE

WEEKDAYS = ("monday", "tuesday", "wednesday",
            "thursday", "friday", "saturday", "sunday")


class Event(ActivePanel):
    MAX_ELEMENT_DISPLAY = 20

    def __init__(self, name, description, start, duration, repeat, author, roles, delete_emoji=DELETE, userid=None):
        self.userid = userid
        self.message : Optional[discord.Message] = None
        self._msg_channel_id : Tuple[int] | None = None
        self.name : str = name
        self.description : str = description
        self.start = start
        self.duration = duration
        self.repeat = repeat
        self.author = author
        self._author_id: int | None = None
        self.roles = roles
        self._roles_id : list[int] | None = None
        self.accepted : list[discord.User] = []
        self._accepted_id : list[int] | None = None
        self.declined : list[discord.User] = []
        self._declined_id : list[int] | None = None
        self.tentative : list[discord.User] = []
        self._tentative_id : list[int] | None = None
        self.delete_emoji = delete_emoji
        self.loaded = True
        
    @staticmethod
    def _from_raw_data(uid, cid, mid, name, desc, start, dur, repeat, author, roles, accepted, declined, tentative, delete_emoji):
        new_event = Event(name, desc, start, dur, repeat, None, None, delete_emoji, uid)
        new_event.loaded = False
        new_event._msg_channel_id = cid, mid 
        new_event._author_id = author
        new_event._roles_id = roles
        new_event._accepted_id = accepted
        new_event._declined_id = declined
        new_event._tentative_id = tentative
        return new_event
    
    def __reduce__(self) -> str | Tuple[Any, ...]:
        return (self._from_raw_data, (
            self.userid, 
            self.message.channel.id if self.message is not None else None,
            self.message.id if self.message is not None else None,
            self.name,
            self.description,
            self.start,
            self.duration,
            self.repeat,
            self.author.id if self.author is not None else None,
            [role.id for role in self.roles] if self.roles is not None else [],
            [user.id for user in self.accepted],
            [user.id for user in self.declined],
            [user.id for user in self.tentative],
            self.delete_emoji
        ))
        
    @property
    def persistent(self):
        return True
        
    async def can_interact(self, client : HSBot, user : discord.User):
        if len(self.roles) == 0: return True
        for role in user.roles:
            if role in self.roles:
                return True
        return await super().can_interact(client, user)
        
    async def init(self, client : HSBot, message : discord.Message):
        if self.loaded:
            self.message = message
            for role in self.roles:
                for user in role.members:
                    if user not in self.declined:
                        self.declined.append(user)
            await self.message.add_reaction(self.delete_emoji)
            await self.message.add_reaction(ACCEPT)
            await self.message.add_reaction(DECLINE)
            await self.message.add_reaction(TENTATIVE)
            await self.update_page()
        else:
            logging.info("Loading active panel (loaded from file)")
            if self._msg_channel_id is not None:
                cid, mid = self._msg_channel_id
                if cid is not None and mid is not None:
                    channel = await client.fetch_channel(cid)
                    self.message = await channel.fetch_message(mid)
                    logging.info(f"Fetched message: {self.message}")
                    client.add_message_to_cache(self.message)
                    self.roles = []
                    for role in await self.message.guild.fetch_roles():
                        if role.id in self._roles_id:
                            self.roles.append(role)
                else:
                    logging.error("No guild/message ID specified")
                    return
            else:
                logging.error("No message ID specified")
                return
            if self._author_id is not None:
                self.author = await client.fetch_user(self._author_id)
            if self._accepted_id is not None:
                self.accepted = [await client.fetch_user(uid) for uid in self._accepted_id]
            if self._declined_id is not None:
                self.declined = [await client.fetch_user(uid) for uid in self._declined_id]
            if self._tentative_id is not None:
                self.tentative = [await client.fetch_user(uid) for uid in self._tentative_id]
            logging.info("Success!")
        
        if self.repeat:
            async def task(client : HSBot):
                logging.info("Activating event repetition")
                try:
                    await client.remove_active_panel(message)
                except Exception:
                    logging.info(traceback.format_exc())
                    logging.info("Canceled by user")
                    return
                new_msg = await self.message.channel.send(content=self.message.content, embed=self.message.embeds[0]) 
                if self.repeat == "Daily":
                    self.start += datetime.timedelta(days=1)
                elif self.repeat == "Weekly":
                    self.start += datetime.timedelta(weeks=1)
                elif self.repeat == "Monthly":
                    d = self.start.day
                    while True:
                        try:
                            if self.start.month != 12:
                                self.start = self.start.replace(month=self.start.month+1)
                            else:
                                self.start = self.start.replace(year=self.start.year+1, month=1, day=d)
                            break
                        except ValueError:
                            d -= 1
                self.accepted, self.declined, self.tentative = [], [], []
                await client.add_active_panel(new_msg, self)     
                logging.info("Done")
            
            stime = self.start + datetime.timedelta(minutes=5)
            if self.duration is not None:
                stime += self.duration
            client.schedule(stime, stime, task)

    async def update_page(self):
        mentions = " ".join(map(lambda r: r.mention, self.roles))
        embed = self.get_embed()
        await self.message.edit(content=mentions, embed=embed)

    def get_embed(self):
        start = self.start.strftime("%a %b %d, %Y ⋅ %I:%M%p")
        if self.duration is not None:
            duration = str(self.duration) + "h"
        else:
            duration = ""

        embed = discord.Embed()
        embed.title = self.name
        if self.description is not None:
            embed.description = self.description
        embed.color = WARNING_COLOR
        embed.add_field(name="Start Time & Duration",
                        value=start+"\n"+duration, inline=False)
        if self.repeat != "Never":
            embed.add_field(name="Repeats", value=get_repeat(self.repeat, self.start), inline=False)
        
        embed.add_field(
            name=f"✅ Accepted ({len(self.accepted)})", value="-", inline=True)
        embed.add_field(
            name=f"❌ Declined ({len(self.declined)})", value="-", inline=True)
        embed.add_field(
            name=f"❓ Tentative ({len(self.tentative)})", value="-", inline=True)
        embed.set_footer(text=f"Created by {self.author.display_name}")

        c = 2 if self.repeat != "Never" else 1
        for field in ("accepted", "declined", "tentative"):
            l = getattr(self, field)
            if len(l) != 0:
                data = "\n".join(
                    map(lambda u: f"> {u.display_name}", l[:__class__.MAX_ELEMENT_DISPLAY]))
                if len(l) > __class__.MAX_ELEMENT_DISPLAY:
                    data += "\n..."
                embed.set_field_at(c, name=embed.fields[c].name, value=data)
            c += 1
        return embed
    
    async def on_accept(self, client: HSBot, reaction : discord.Reaction, user : discord.User):
        if user in self.declined:
            self.declined.remove(user)
        if user in self.tentative:
            self.tentative.remove(user)
        if user not in self.accepted:
            self.accepted.append(user)
        await self.update_page()

    async def on_decline(self, client: HSBot, reaction : discord.Reaction, user : discord.User):
        if user not in self.declined:
            self.declined.append(user)
        if user in self.tentative:
            self.tentative.remove(user)
        if user in self.accepted:
            self.accepted.remove(user)
        await self.update_page()

    async def on_tentative(self, client: HSBot, reaction : discord.Reaction, user : discord.User):
        if user in self.declined:
            self.declined.remove(user)
        if user not in self.tentative:
            self.tentative.append(user)
        if user in self.accepted:
            self.accepted.remove(user)
        await self.update_page()

    async def on_reaction(self, client: HSBot, reaction : discord.Reaction, user : discord.User):
        if str(reaction.emoji) == self.delete_emoji and user.id == self.userid:
            await self.message.delete()
            return
        
        if len(self.roles) != 0:
            allowed = False
            for role in self.roles:
                if role in user.roles:
                    allowed = True
                    break
        else:
            allowed = True
            
        if allowed:
            if str(reaction.emoji) == ACCEPT:
                await self.on_accept(self, reaction, user)
                await reaction.remove(user)

            elif str(reaction.emoji) == DECLINE:
                await self.on_decline(self, reaction, user)
                await reaction.remove(user)

            elif str(reaction.emoji) == TENTATIVE:
                await self.on_tentative(self, reaction, user)
                await reaction.remove(user)


def get_ending(i : int):
    if i % 10 == 1 and i != 11:
        return "st"
    if i % 10 == 2 and i != 12:
        return "nd"
    if i % 10 == 3 and i != 13:
        return "rd"
    return "th"

def get_weekday_count(date):
    m = datetime.date(date.year, date.month, 1)
    return (date.day - m.day) // 7 + 1

def get_repeat(string, start):
    if string == "Daily":
        return "Every day"
    elif string == "Weekly":
        return f"Every {WEEKDAYS[start.weekday()]}"
    elif string == "Monthly":
        return f"On the {start.day}{get_ending(start.day)} of every month"
    elif string == "Monthly (by weekday)":
        wd = WEEKDAYS[start.weekday()]
        count = get_weekday_count(start)
        return f"On the {count}{get_ending(count)} {wd} of every month"
    return "???"
