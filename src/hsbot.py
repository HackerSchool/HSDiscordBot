import logging
import sys

import client
import cmdevent
import cmdhelp
import cmdpresent
import cmdproject
import cmdpoll
import cmdused
import cmdrolepanel
import sprint


def setup(client : client.HSBot):
    """This function is responsible for registering all commands and reaction handlers with the client"""
    client.add_command("help", cmdhelp.command_help)
    client.add_command("event", cmdevent.command_event)
    client.add_command("present", cmdpresent.command_present)
    client.add_command("project", cmdproject.command_project)
    client.add_command("poll", cmdpoll.command_poll)
    client.add_command("used", cmdused.command_used)
    client.add_command("rolepanel", cmdrolepanel.command_rolepanel)
    

    client.add_custom_message_handler("sprint", sprint.handler_attachment)
    sprint.add_member_name_change(client)


if __name__ == "__main__":
    logging.basicConfig(format="%(asctime)s %(levelname)s - %(message)s",
                        datefmt="[%d/%b/%Y %H:%M:%S]", level=logging.INFO)
    with open("token", "r") as file:
        token = file.readline()

    prefix = sys.argv[1] if len(sys.argv) > 1 else "+"
    if prefix != "+":
        logging.info(f"Using custom prefix '{prefix}'")

    hsbot = client.HSBot(prefix)
    setup(hsbot)
    hsbot.run(token)
