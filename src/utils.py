import os


DELETE = "<:delete:827871952336715776>"
CONFIRM = "✅"
DECLINE = "❌"


def basedir(f):
    return os.path.abspath(os.path.join(f, os.pardir))


def asynchronize(func):
    async def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    wrapper.__doc__ = func.__doc__
    wrapper.__name__ = func.__name__
    return wrapper
    

@asynchronize
def can_interact_default(self, reaction, user, panel):
    return True


async def command_deletable(self, message, args):
    """Dummy command"""
    sent = await self.send_info(message.channel, "This message can be deleted")
    self.add_active_panel(sent, "all", {"deletable"})
    await sent.add_reaction(DELETE)


async def delete_message(self, reaction, user, panel):
    if panel["info"] is not None:
        if "on_delete" in panel["info"]:
            await panel["info"]["on_delete"](self, reaction, user, panel)
    await self.remove_active_panel(reaction.message, panel["user"])
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
        if "on_accept" in panel["info"]:
            await panel["info"]["on_accept"](self, reaction, user, panel)
