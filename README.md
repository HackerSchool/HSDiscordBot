# HS Discord Bot
## A Discord bot to help manage hackerschool events
____


### General description

This bot aims to facilitate Hackerschool's management through the discord server.  
Types of actions that trigger the bot:

- Commands
    ```
    Usage:
    [prefix][command] [arguments]
    ```
- Sending certain files


### Wanted specifications
- [ ] Discord nickname from google forms (excel)
- [ ] Announcement creation similar to Apollo
- [ ] Automatic attendance detection
- [ ] Some way to track people who don't answer event announcements
- [ ] Sprint report tracking
- [ ] Brainstorm help in the form of voice room creation
- [ ] Project setup and emoji (?)
- [x] Project setup (role, text channel, voice channel) and deletion
- [ ] "Mass" project setup from file containing necessary information

## Documentation


### Commands

1. `event`  
Sends a private message to the user who prompted the command with an event configuration panel.
``` 
Usage: 
[prefix]event
```

2. `project`  
Aids in manual project creation/deletion without the need to mess with roles, text, voice channels and their respective permissions.
``` python
Usage: 
[prefix]project  # displays help menu        
[prefix]project new project_name participant_1 [participant_2] ... [participant_n] # creates project with given participants
[prefix]project delete project_name_1 [project_name_2] ... [project_name_n] # deletes given projects

```
Values for arg:  
- new
- delete

### Detectable Files

1. Sprint reports: files which contain the word "sprint" are detected and prompt the user to confirm sending it to storage.
2. [TODO] Forms responses [exported as csv] containing discord name with discriminator
3. [TODO] CSV files containing several projects and their participants
