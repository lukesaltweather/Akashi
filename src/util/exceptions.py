import discord.ext.commands as commands

class ProjectAlreadyExists(commands.CommandError):
    def __init__(self, message="This project already exists."):
        self.message = message

class ChapterAlreadyExists(commands.CommandError):
    def __init__(self, message="This chapter already exists."):
        self.message = message

class MemberAlreadyExists(commands.CommandError):
    def __init__(self, message="This chapter already exists."):
        self.message = message