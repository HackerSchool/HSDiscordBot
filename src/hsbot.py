import client


async def command_hello(self, message, args):
    await message.channel.send("Hello!")
    

def setup(client):   
    client.add_command("hello", command_hello)
    

if __name__ == "__main__":
    with open("token", "r") as file:
        token = file.readline()
    
    hsbot = client.HSBot("+")
    setup(hsbot)
    hsbot.run(token)