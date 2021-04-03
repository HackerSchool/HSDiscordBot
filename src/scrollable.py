import discord

import utils

LEFT = "⬅️"
RIGHT = "➡️"


class Scrollable(utils.BasicPanel):
    def __init__(self, pages, page=1, auto_footer=True):
        super().__init__()
        self.pages = pages
        self.page = 1
        self.auto_footer = auto_footer

    def on_page_change(self):
        return discord.Embed()

    def get_embed(self):
        e = self.on_page_change()
        if self.auto_footer:
            e.set_footer(text=f"Page {self.page}/{self.pages}")
        return e

    def next_page(self):
        self.page += 1
        if self.page > self.pages:
            self.page = 1
        e = self.on_page_change()
        if self.auto_footer:
            e.set_footer(text=f"Page {self.page}/{self.pages}")
        return e

    def previous_page(self):
        self.page -= 1
        if self.page == 0:
            self.page = self.pages
        e = self.on_page_change()
        if self.auto_footer:
            e.set_footer(text=f"Page {self.page}/{self.pages}")
        return e


class SmartScrollable(Scrollable):
    def __init__(self, pages, page=1, auto_footer=True):
        super().__init__(pages, page, auto_footer)
        self.message = None


async def reaction_scrollable(self, reaction, user, panel):
    if str(reaction.emoji) == RIGHT:
        if reaction.message.guild is not None:
            await reaction.remove(user)
        new_embed = panel.instance.next_page()
        content = reaction.message.content
        await reaction.message.edit(content=content, embed=new_embed)

    if str(reaction.emoji) == LEFT:
        if reaction.message.guild is not None:
            await reaction.remove(user)
        content = reaction.message.content
        new_embed = panel.instance.previous_page()
        await reaction.message.edit(content=content, embed=new_embed)
