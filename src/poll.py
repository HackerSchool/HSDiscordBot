from __future__ import annotations
import logging

from typing import TypedDict
from typing import Any, Union

import discord

from activepanel import ActivePanel
from cfg import NUMBERS, SUCCESS_COLOR
from choosable import Choosable
from client import HSBot
from panels import DeletableActivePanel


class Poll(ActivePanel):
    
    def __init__(self, title : str, options : list[str], channel: discord.TextChannel, userid=None):
        self.cap = Choosable(self.on_choose)
        self.title : str = title
        self.options : list[str] = options
        self.totals : list[int] = [0]*len(options)
        self.votes : list[TypedDict('Vote', {'user': discord.User, 'idx' : int})] = []
        self.channel : discord.TextChannel = channel
        self.userid = userid
        self.message: discord.Message
        self.loaded = True
        self._vote_info = None
        self._msg_id = None
        self._channel_id = None

    @staticmethod
    def _from_raw_data(uid, mid, vinfo, cid, title, options, totals):
        new_poll = Poll(title, options, None, userid=uid)

        new_poll._vote_info = vinfo
        new_poll._msg_id = mid
        new_poll._channel_id = cid
        new_poll.loaded = False
        new_poll.totals = totals
        new_poll.loaded = False
        return new_poll

    def __reduce__(self) -> str | tuple[Any, ...]:
        return (self._from_raw_data, (
            self.userid,
            self.message.id,
            [{'userid': vote['user'].id, 'idx': vote['idx']}
                for vote in self.votes],
            self.channel.id,
            self.title,
            self.options,
            self.totals
        ))

    @property
    def persistent(self):
        return True

    async def init(self, client : HSBot, message : discord.Message):
        if self.loaded:
            self.message = message
        else:
            if self._channel_id is not None:
                self.channel = await client.fetch_channel(self._channel_id)
                if self._msg_id is not None:
                    self.message = await self.channel.fetch_message(self._msg_id)
                    client.add_message_to_cache(self.message)
                    self.votes = [{
                            'user': client.get_user(vote['userid']), 
                            'idx': vote['idx']
                        } for vote in self._vote_info
                    ]
                
                    self.loaded = True
                else:
                    logging.error("No message ID found for poll")
                    return
            else:
                logging.error("No channel ID found for poll")
                return

        await self.cap.init(client, self.message)

    async def on_reaction(self, client: HSBot, reaction: discord.Reaction, user: discord.User):
        await self.cap.on_reaction(client, reaction, user)

    async def on_choose(self, client : HSBot, reaction : discord.Reaction, user: discord.User, index : int):
        index -= 1 # Option numbers start at 1, indexes start at 0. function receives option number
        await reaction.remove(user)
        if index >= 0 and index < len(self.totals):
            for vote in self.votes:
                if user == vote['user']:
                    self.totals[vote['idx']] -= 1
                    self.votes.remove(vote)
            self.votes.append({'user' : user, 'idx' : index})
            self.totals[index] += 1
        await self.message.edit(embed = self.embed())

    def embed(self) -> discord.Embed:
        embed = discord.Embed(title=self.title)
        embed.colour = SUCCESS_COLOR
        for i in range(0, len(self.options)):
            embed.add_field(name="`" + str(i+1) + "` " + self.options[i], value=str(self.totals[i]))
        return embed
    
    async def send_msg(self) -> discord.Message:
        msg : discord.Message = await self.channel.send(embed = self.embed())
        for i in range(1, len(self.options) + 1):
            await msg.add_reaction(NUMBERS[i])
        return msg
