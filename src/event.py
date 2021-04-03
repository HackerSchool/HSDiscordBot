import discord

from utils import Deletable

ACCEPT, DECLINE, TENTATIVE = "✅", "❌", "❓"


class Event(Deletable):
    MAX_ELEMENT_DISPLAY = 20

    def __init__(self, name, description, start, duration, author, roles):
        self.message = None
        self.name = name
        self.description = description
        self.start = start
        self.duration = duration
        self.author = author
        self.roles = roles
        self.accepted = []
        self.declined = []
        self.tentative = []

    async def update_page(self):
        mentions = " ".join(map(lambda r: r.mention, self.roles))
        embed = self.get_embed()
        await self.message.edit(content=mentions, embed=embed)

    def get_embed(self):
        start = self.start.strftime("%a %b %d, %Y ⋅ %I%p")
        if self.duration is not None:
            duration = str(self.duration) + "h"
        else:
            duration = ""

        embed = discord.Embed()
        embed.title = self.name
        if self.description is not None:
            embed.description = self.description
        embed.color = 0x6db977
        embed.add_field(name="Start Time & Duration",
                        value=start+"\n"+duration, inline=False)
        embed.add_field(
            name=f"✅ Accepted ({len(self.accepted)})", value="-", inline=True)
        embed.add_field(
            name=f"❌ Declined ({len(self.declined)})", value="-", inline=True)
        embed.add_field(
            name=f"❓ Tentative ({len(self.tentative)})", value="-", inline=True)
        embed.set_footer(text=f"Created by {self.author.display_name}")

        c = 1
        for field in ("accepted", "declined", "tentative"):
            l = getattr(self, field)
            if len(l) != 0:
                data = "\n".join(
                    map(lambda u: f"> {u.display_name}", l[:__class__.MAX_ELEMENT_DISPLAY]))
                if len(l) > __class__.MAX_ELEMENT_DISPLAY:
                    data += "\n..."
                embed.set_field_at(c, name=embed.fields[c].name, value=data)
            c += 1
        return embed

    async def on_delete(self, client, reaction, user, panel):
        pass

    async def on_accept(self, client, reaction, user, panel):
        if user in self.declined:
            self.declined.remove(user)
        if user in self.tentative:
            self.tentative.remove(user)
        if user not in self.accepted:
            self.accepted.append(user)
        await self.update_page()

    async def on_decline(self, client, reaction, user, panel):
        if user not in self.declined:
            self.declined.append(user)
        if user in self.tentative:
            self.tentative.remove(user)
        if user in self.accepted:
            self.accepted.remove(user)
        await self.update_page()

    async def on_tentative(self, client, reaction, user, panel):
        if user in self.declined:
            self.declined.remove(user)
        if user not in self.tentative:
            self.tentative.append(user)
        if user in self.accepted:
            self.accepted.remove(user)
        await self.update_page()


async def reaction_event(self, reaction, user, panel):
    if len(panel.instance.roles) != 0:
        allowed = False
        for role in panel.instance.roles:
            if role in user.roles:
                allowed = True
                break
    else:
        allowed = True

    if allowed:
        if str(reaction.emoji) == ACCEPT:
            await panel.instance.on_accept(self, reaction, user, panel)
            await reaction.remove(user)

        elif str(reaction.emoji) == DECLINE:
            await panel.instance.on_decline(self, reaction, user, panel)
            await reaction.remove(user)

        elif str(reaction.emoji) == TENTATIVE:
            await panel.instance.on_tentative(self, reaction, user, panel)
            await reaction.remove(user)
