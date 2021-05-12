import time


class ActivePanel:
    def __init__(self):
        self.userid = None
        self.message = None
        
    async def on_reaction(self, client, reaction, user):
        pass
        
    async def on_message(self, client, message):
        pass
    
    async def on_deactivate(self, client):
        pass
    
    async def init(self, message):
        self.message = message
    
    async def can_interact(self, client, user):
        if self.userid is not None:
            return user.id == self.userid 
        if self.message is not None:
            return user.id == self.message.author.id 
        return False
