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