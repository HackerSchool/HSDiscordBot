import os

import discord

DELETE = "<:delete:827871952336715776>"
CONFIRM = "✅"
DECLINE = "❌"


class BasicPanel:
    def __init__(self):
        pass

    def get_embed(self):
        return discord.Embed()

    async def can_interact(self, client, reaction, user, panel):
        return True


class Deletable(BasicPanel):
    def __init__(self):
        super().__init__()

    async def on_delete(self, client, reaction, user, panel):
        pass


class YesNo(BasicPanel):
    def __init__(self):
        super().__init__()

    async def on_accept(self, client, reaction, user, panel):
        pass

    async def on_delete(self, client, reaction, user, panel):
        pass


def basedir(f):
    return os.path.abspath(os.path.join(f, os.pardir))


def get_key(message):
    return (message.channel if message.guild is None else message.guild).id


async def command_deletable(self, message, args):
    """Dummy command"""
    sent = await self.send_info(message.channel, "This message can be deleted")
    self.add_active_panel(sent, "all", {"deletable"}, Deletable())
    await sent.add_reaction(DELETE)


async def delete_message(self, reaction, user, panel):
    await panel.instance.on_delete(self, reaction, user, panel)
    await self.remove_active_panel(reaction.message, panel.user)
    await reaction.message.delete()


async def reaction_deletable(self, reaction, user, panel):
    """Triggered when a deletable message is reacted on"""
    if str(reaction.emoji) == DELETE:
        await delete_message(self, reaction, user, panel)


async def reaction_yesno(self, reaction, user, panel):
    """Triggered when a yes-no message is reacted on"""

    if str(reaction.emoji) == DECLINE:
        await delete_message(self, reaction, user, panel)

    if str(reaction.emoji) == CONFIRM:
        if reaction.message.guild is not None:
            await reaction.remove(user)
        await panel.instance.on_accept(self, reaction, user, panel)
