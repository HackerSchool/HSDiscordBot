import logging

import client


async def command_hello(self, message, args):
    await self.send_info(message.channel, "Hello!")
    

def setup(client):   
    client.add_command("hello", command_hello)
    

if __name__ == "__main__":
    with open("token", "r") as file:
        token = file.readline()
    
    logging.basicConfig(format="%(asctime)s %(levelname)s - %(message)s", datefmt="[%d/%b/%Y %H:%M:%S]", level=logging.INFO)
    hsbot = client.HSBot("+")
    setup(hsbot)
    hsbot.run(token)
