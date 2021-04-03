import discord
import utils


class Interactive(utils.BasicPanel):
    def __init__(self):
        super().__init__()
        self.message = None

    async def on_message(self, message):
        pass


async def handler_interactive(self, message):
    key = utils.get_key(message)
    panels = self.get_active_panels(key, message.author.id)
    for panel in panels:
        if panels[panel].is_type("interactive"):
            await panels[panel].instance.on_message(message)
