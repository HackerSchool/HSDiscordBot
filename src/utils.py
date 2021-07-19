import os

PROJECTS_CATEGORY = "PROJECTS"

SUCCESS_COLOR = 0x6db977
WARNING_COLOR = 0xf2d61b
ERROR_COLOR = 0xff0000

def basedir(f):
    return os.path.abspath(os.path.join(f, os.pardir))


def get_key(message):
    return (message.channel if message.guild is None else message.guild).id
