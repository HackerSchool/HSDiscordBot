import os


DELETE = "❌"
CONFIRM = "✅"

def basedir(f):
    return os.path.abspath(os.path.join(f, os.pardir))    

async def command_deletable(self, message, args):
    """Dummy command"""
    sent = await self.send_info(message.channel, "This message can be deleted")
    self.add_active_panel(sent, "all", {"deletable"})
    await sent.add_reaction(DELETE)
    
async def reaction_deletable(self, reaction, user, panel):
    """Triggered when a deletable message is reacted on"""
    if reaction.emoji == DELETE:
        self.remove_active_panel(reaction.message, panel["user"])
        await reaction.message.delete()
        
async def reaction_yesno(self, reaction, user, panel):
    """Triggered when a yes-no message is reacted on"""
    if reaction.emoji == DELETE:
        self.remove_active_panel(reaction.message, panel["user"])
        await reaction.message.delete()
    
    if reaction.emoji == CONFIRM:
        if reaction.message.guild is not None:
            await reaction.remove(user)
        await panel["info"]["on_accept"](self, reaction, user, panel)