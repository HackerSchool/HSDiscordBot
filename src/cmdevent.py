import os
import logging

from jsonembed import json_to_embed
from scrollable import LEFT, RIGHT, SmartScrollable
from utils import basedir


class Event(SmartScrollable):
    def __init__(self, channel, message, pages, page=1, on_page_change=None, auto_footer=True):
        super().__init__(message, pages, page, on_page_change, auto_footer)
        self.current_channel = channel
        self.selected_channel = channel
        self.start_time = None
        self.duration = None
        self.event_name = None
        self.repeat = None
        self.event_description = None
        self.role_mentions = []

def get_event_embed(self):
    logging.info(self.page)
    path = os.path.join(basedir(__file__), "rsrc", "events", f"page{self.page}.json")
    with open(path, "r") as f:
        base = json_to_embed(f.read())
    
    if self.page == 1:
        value = "**Selected: **"
        if self.current_channel == self.selected_channel:
            value += f"Current channel ({self.current_channel.mention})"
        else:
            value += f"{self.selected_channel.mention}"
        value += "\n(type the channel name to change it)"
        base.set_field_at(0, name=base.fields[0].name, value=value)
        
    elif self.page == 2:
        value = str(self.event_name)
        base.set_field_at(0, name=base.fields[0].name, value=value)
        
    return base

async def command_event(self, message, args):
    channel = await message.author.create_dm()
    
    panels = self.get_active_panels(channel.id, message.author.id)
    for panel in panels:
        msg = await channel.fetch_message(panel["id"])
        self.remove_active_panel(msg, panel["user"])
        
    s = Event(message.channel, None, 2, 1, get_event_embed)
    msg = await channel.send(embed=s.update_page())
    s.message = msg
    self.add_active_panel(msg, message.author, {"scrollable"}, info={
        "scrollable": s
    })
    await msg.add_reaction(LEFT)
    await msg.add_reaction(RIGHT)
