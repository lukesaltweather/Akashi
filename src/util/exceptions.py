import discord.ext


class ReactionInvalidRoleError(discord.ext.commands.CommandError):
    pass


class StaffNotFoundError(discord.ext.commands.CommandError):
    pass


class MissingRequiredPermission(discord.ext.commands.CommandError):
    def __init__(self, message):
        self.message = message


class MissingRequiredParameter(discord.ext.commands.CommandError):
    def __init__(self, param):
        self.param = param


class NoResultFound(discord.ext.commands.CommandError):
    def __init__(self, message=None):
        self.message = message


class TagAlreadyExists(discord.ext.commands.CommandError):
    def __init__(self, message=None):
        self.message = message


class CancelError(discord.ext.commands.CommandError):
    pass
