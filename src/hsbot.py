import logging
import sys

import client
import cmdevent
import cmdhelp
import cmdroom
import scrollable
import sprint
import utils


async def command_hello(self, message, args):
    """Dummy command"""
    await self.send_info(message.channel, "Hello!")

def setup(client):   
    """This function is responsible for registering all commands and reaction handlers with the client"""
    client.add_command("hello", command_hello)
    client.add_command("deletable", utils.command_deletable)
    client.add_command("help", cmdhelp.command_help)
    client.add_command("room", cmdroom.command_room)
    client.add_command("event", cmdevent.command_event)

    client.add_reaction("deletable", utils.reaction_deletable)
    client.add_reaction("yesno", utils.reaction_yesno)
    client.add_reaction("scrollable", scrollable.reaction_scrollable)
    
    client.add_custom_message_handler("sprint", sprint.handler_sprint)
    client.add_custom_message_handler("event", cmdevent.handler_event, text=False, dm=True)
    
    client.add_reaction("numbers", cmdroom.reaction_numbers)

if __name__ == "__main__":
    logging.basicConfig(format="%(asctime)s %(levelname)s - %(message)s", datefmt="[%d/%b/%Y %H:%M:%S]", level=logging.INFO)
    with open("token", "r") as file:
        token = file.readline()
    
    prefix = sys.argv[1] if len(sys.argv) > 1 else "+"
    if prefix != "+":
        logging.info(f"Using custom prefix '{prefix}'")
    
    hsbot = client.HSBot(prefix)
    setup(hsbot)
    hsbot.run(token)
