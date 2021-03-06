# HS Discord Bot
## A Discord bot to help manage hackerschool events
____

### Setup

To get the bot running, run `pip3 install -r requirements.txt` to install all the required python packages and then `python3 src/hsbot.py [PREFIX]` to run the bot itself.

### General description

This bot aims to facilitate Hackerschool's management through the discord server.  
Types of actions that trigger the bot:

- Commands
    ```
    Usage:
    [prefix][command] [arguments]
    ```
- Sending certain files
- Insults

### Wanted specifications
- [x] Discord nickname from google forms (excel)
- [ ] Announcement creation similar to Apollo
- [x] Automatic attendance detection (run command to return list of people in voice chat)
- [ ] Some way to track people who don't answer event announcements
- [x] Sprint report tracking
- [x] Project setup info (role mention + basic info)
- [x] Project setup (role, text channel, voice channel) and deletion
- [x] "Mass" project setup from file containing necessary information
- [ ] Polls

## Documentation


### Commands

1. `help`
Displays helpful information about the bot and available commands.
``` 
Usage: 
[prefix]help
```

2. `event`  
Sends a private message to the user who prompted the command with an event configuration panel.
``` 
Usage: 
[prefix]event
```

3. `project`  
Aids in manual project creation/deletion without the need to mess with roles, text, voice channels and their respective permissions.
``` python
Usage: 
[prefix]project  # displays help menu   
[prefix]project new # opens project creation interface in a DM
[prefix]project new project_name participant_1 [participant_2] ... [participant_n] # creates project with given participants
[prefix]project delete project_name_1 [project_name_2] ... [project_name_n] [-y] # deletes given projects. if '-y' option is selected, no further user input is required

```

4. `present`  
Responds with a list of members which are currently in voice chat
``` 
Usage: 
[prefix]present # displays list of members which are currently in a voice channel
[prefix]present time_minutes # records all members which were in a voice channel for "a bit" from the moment the command is pressed, for time_minutes minutes
```

### Detectable Files

1. Sprint reports: files which contain the word "sprint" are detected and prompt the user to confirm sending it to storage.
2. Forms responses [exported as csv] containing discord name with discriminator
3. CSV files containing several projects and their participants
