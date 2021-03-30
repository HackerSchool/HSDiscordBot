import logging

import client
import utils


async def command_hello(self, message, args):
    """Dummy command"""
    await self.send_info(message.channel, "Hello!")

def setup(client):   
    """This function is responsible for registering all commands and reaction handlers with the client"""
    client.add_command("hello", command_hello)
    client.add_command("deletable", utils.command_deletable)
    
    client.add_reaction("deletable", utils.reaction_deletable)
    client.add_reaction("yesno", utils.reaction_yesno)
    

if __name__ == "__main__":
    with open("token", "r") as file:
        token = file.readline()
    
    logging.basicConfig(format="%(asctime)s %(levelname)s - %(message)s", datefmt="[%d/%b/%Y %H:%M:%S]", level=logging.INFO)
    hsbot = client.HSBot("+")
    setup(hsbot)
    hsbot.run(token)
