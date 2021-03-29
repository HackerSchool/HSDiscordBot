async def command_deletable(self, message, args):
    sent = await self.send_info(message.channel, "This message can be deleted")
    self.add_active_panel(sent, "all", {"deletable"})
    await sent.add_reaction("❌")
    
async def reaction_deletable(self, reaction, user, panel):
    if reaction.emoji == "❌":
        self.remove_active_panel(reaction.message, panel["user"])
        await reaction.message.delete()