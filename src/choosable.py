import discord

import utils

NUMBERS = ("0️⃣", "1️⃣", "2️⃣", "3️⃣", "4️⃣",
           "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟")


class Choosable(utils.BasicPanel):
    def __init__(self):
        super().__init__()

    async def on_choose(self, reaction, user, panel, index):
        pass


async def reaction_choosable(self, reaction, user, panel):
    """Triggered when a message that has multiple choices is reacted on"""
    try:
        index = NUMBERS.index(reaction.emoji)
    except ValueError:
        return

    if reaction.message.guild is not None:
        await reaction.remove(user)

    await panel["info"]["on_choose"](self, reaction, user, panel, index)
