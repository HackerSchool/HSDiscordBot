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
        
    @staticmethod
    def page_change(instance):
        return discord.Embed()
    
    def get_embed(self):
        e = self.on_page_change(self)
        if self.auto_footer:
            e.set_footer(text=f"Page {self.page}/{self.pages}")
        return e

    def next_page(self):
        self.page += 1
        if self.page > self.pages:
            self.page = 1
        e = self.on_page_change(self)
        if self.auto_footer:
            e.set_footer(text=f"Page {self.page}/{self.pages}")
        return e
    
    def previous_page(self):
        self.page -= 1
        if self.page == 0:
            self.page = self.pages
        e = self.on_page_change(self)
        if self.auto_footer:
            e.set_footer(text=f"Page {self.page}/{self.pages}")
        return e
    
    
class SmartScrollable(Scrollable):
    def __init__(self, pages, page=1, on_page_change=None, auto_footer=True):
        super().__init__(pages, page, on_page_change, auto_footer)
        self.message = None
        

async def reaction_scrollable(self, reaction, user, panel):
    if str(reaction.emoji) == RIGHT:
        if reaction.message.guild is not None:
            await reaction.remove(user)
        new_embed = panel["info"]["scrollable"].next_page()
        content = reaction.message.content
        await reaction.message.edit(content=content, embed=new_embed)
        
    if str(reaction.emoji) == LEFT:
        if reaction.message.guild is not None:
            await reaction.remove(user)
        content = reaction.message.content
        new_embed = panel["info"]["scrollable"].previous_page()
        await reaction.message.edit(content=content, embed=new_embed)
