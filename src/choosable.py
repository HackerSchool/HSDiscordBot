import discord

from activepanel import ActivePanel

NUMBERS = ("0️⃣", "1️⃣", "2️⃣", "3️⃣", "4️⃣",
           "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟")


class Choosable(ActivePanel):
    def __init__(self, on_choose=None, userid=None):
        self.message = None
        self.userid = userid
        self._on_choose = on_choose
        
    async def on_reaction(self, client, reaction, user):
        try:
            i = NUMBERS.index(reaction.emoji)
            await self.on_choose(self, client, i)
        except ValueError:
            pass

    async def on_choose(self, client, index):
        if self._on_choose is not None:
            await self._on_choose(self, client, index)
