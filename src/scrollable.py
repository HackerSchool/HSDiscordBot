import discord


LEFT = "⬅️"
RIGHT = "➡️"

class Scrollable:
    def __init__(self, pages, page=1, on_page_change=None, auto_footer=True):
        self.pages = pages
        self.page = 1
        if on_page_change is None:
            self.on_page_change = self.page_change
        else:
            self.on_page_change = on_page_change
        self.auto_footer = auto_footer
        
    def page_change(self):
        return discord.Embed()

    def next_page(self):
        self.page += 1
        if self.page > self.pages:
            self.page = 1
        e = self.on_page_change()
        if self.auto_footer:
            e.set_footer(f"Page {self.page}/{self.pages}")
        return e
    
    def previous_page(self):
        self.page -= 1
        if self.page == 0:
            self.page = self.pages
        e = self.on_page_change()
        if self.auto_footer:
            e.set_footer(f"Page {self.page}/{self.pages}")
        return e
        

async def reaction_scrollable(self, reaction, user, panel):
    if reaction.emoji == RIGHT:
        await reaction.remove(user)
        new_embed = panel["info"]["scrollable"].next_page()
        content = reaction.message.content
        await reaction.message.edit(content=content, embed=new_embed)
        
    if reaction.emoji == LEFT:
        await reaction.remove(user)
        content = reaction.message.content
        new_embed = panel["info"]["scrollable"].previous_page()
        await reaction.message.edit(content=content, embed=new_embed)
