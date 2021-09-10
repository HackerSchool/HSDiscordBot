import os
import discord

def basedir(f):
    return os.path.abspath(os.path.join(f, os.pardir))


def get_key(message : discord.Message):
    return (message.channel if message.guild is None else message.guild).id
