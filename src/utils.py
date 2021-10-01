import os
from typing import Optional, Union

import discord


def basedir(f):
    return os.path.abspath(os.path.join(f, os.pardir))


def get_key(message : discord.Message):
    return (message.channel if message.guild is None else message.guild).id


def get_role_named(guild: discord.Guild, name: str) -> Optional[discord.Role]:
    """
    If a role with a given name exists, it is returned, otherwise return None
    """
    for role in guild.roles:
        if role.name.lower() == name.lower():
            return role
    return None

def role_from_incomplete_name(guild: discord.Guild, name: str) -> Union[discord.Role, None]:
    def verify(role: discord.Role):
        if name.isdigit():
            if role.id == int(name):
                return True
        return name.lower() in role.name.lower()

    valid_roles = tuple(filter(
        verify,
        guild.roles
    ))
    if len(valid_roles) == 1:
        return valid_roles[0]
    elif len(valid_roles) > 1:
        return f"There are {len(valid_roles)} roles matching that name"
    else:
        return f"There is no role matching that name"

def get_voice_channel_named(category: discord.CategoryChannel, name: str) -> Optional[discord.VoiceChannel]:
    """
    If a voice channel with a given name exists, it is returned, otherwise return None
    """
    for channel in category.voice_channels:
        if channel.name.lower() == name.lower():
            return channel
    return None


def get_text_channel_named(category: discord.CategoryChannel, name: str) -> Optional[discord.TextChannel]:
    """
    If a text channel with a given name exists, it is returned, otherwise return None
    """
    for channel in category.text_channels:
        if channel.name.lower() == name.lower():
            return channel
    return None


def get_category_named(guild: discord.Guild, name: str) -> Optional[discord.CategoryChannel]:
    """
    If a category with a given name exists, it is returned, otherwise return None
    """
    for category in guild.categories:
        if category.name.lower() == name.lower():
            return category
    return None


def member_from_participant(guild: discord.Guild, participant: str) -> Optional[discord.User]:
    def verify(member):
        return participant.lower() in member.name.lower()

    valid_members = tuple(filter(
        verify,
        guild.members
    ))
    if len(valid_members) == 1:
        return valid_members[0]
    else:
        return None
