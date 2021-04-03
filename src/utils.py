import os


def basedir(f):
    return os.path.abspath(os.path.join(f, os.pardir))


def get_key(message):
    return (message.channel if message.guild is None else message.guild).id
