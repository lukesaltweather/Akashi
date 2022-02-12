import discord.ext.commands as commands


class AkashiException(Exception):
    def __init__(self, message="Sorry. An error occured."):
        self.message = message


class ProjectAlreadyExists(AkashiException):
    def __init__(self, message="This project already exists."):
        self.message = message


class ChapterAlreadyExists(AkashiException):
    def __init__(self, message="This chapter already exists."):
        self.message = message


class MemberAlreadyExists(AkashiException):
    def __init__(self, message="This chapter already exists."):
        self.message = message


class StaffNotFound(AkashiException):
    def __init__(
        self,
        message="Sorry, I couldn't find that staffmember. Please check for proper capitalization.",
    ):
        self.message = message


class ChapterNotFound(AkashiException):
    def __init__(self, message="Sorry, I couldn't find this specific chapter. "):
        self.message = message


class ProjectNotFound(AkashiException):
    def __init__(
        self, message="Sorry, this project doesn't appear to be in my database."
    ):
        self.message = message


class InsufficientPermissions(AkashiException):
    def __init__(self, message="Sorry, you're not permitted to use this command."):
        self.message = message


class NoCommandChannel(AkashiException):
    def __init__(self, message="Please use one of the command channels."):
        self.message = message
