################### Aesthetics ###################
# colors for discord embeds
SUCCESS_COLOR = 0x6db977
WARNING_COLOR = 0xf2d61b
ERROR_COLOR = 0xff0000

# TENTATIVE is only for events
ACCEPT, DECLINE, TENTATIVE = "✅", "❌", "❓"

DELETE = "<:delete:827871952336715776>"

NUMBERS = ("0️⃣", "1️⃣", "2️⃣", "3️⃣", "4️⃣",
           "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟")

################### Management ###################

# category in which project channels reside
PROJECTS_CATEGORY = "PROJECTS"

# roles which who have access to project data
MANAGEMENT_ROLES = ("Chefes", "Dev", "RH", "Marketing")

# google drive folder in which all other folders are located
MASTER_FOLDER_ID = "1ofpR71Ljkq7VbVarSmkHWUB8JkPAUlj7"

# a user which is continuously present in least this % of the event guaranteed
# is to be marked as present, when [prefix]presence time_minutes is run
MINIMUM_SUFFICIENT_ATTENDANCE_PERCENTAGE = 10

################### Attachment detection ###################

##### file name triggers #####
# attachments' file names started with these characters are detected, others are ignored
SPRINT_PREFIX = "sprint"        # as sprint reports
NAMES_PREFIX = "name"           # as name pairs
PROJECTS_PREFIX = "project"     # as new projects

# index of header lines. if none, HEADER_NAME_PAIRS should be set to None
HEADER_PROJECTS = None
HEADER_NAME_PAIRS = None

##### mass project setup #####
# first column must contain project names
# second and all adjacent populated columns must members' names

##### name pairs #####
# first position: index of column containing discord usernames
# second position: index of column containing wanted server nicknames
COLS_NAME_PAIRS = (0, 1)
# file to store all name pairs
NAME_PAIRS_FILE = "names.pkl"
