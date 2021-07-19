import os

# category in which project channels reside
PROJECTS_CATEGORY = "PROJECTS"

# roles which who have access to project data
MANAGEMENT_ROLES = ("Chefes", "Dev", "RH", "Marketing")

# google drive folder in which all other folders are located
master_folder_ID = "1ofpR71Ljkq7VbVarSmkHWUB8JkPAUlj7"

# colors for discord embeds
SUCCESS_COLOR = 0x6db977
WARNING_COLOR = 0xf2d61b
ERROR_COLOR = 0xff0000

def basedir(f):
    return os.path.abspath(os.path.join(f, os.pardir))


def get_key(message):
    return (message.channel if message.guild is None else message.guild).id
