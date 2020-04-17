import json

from discord.ext import commands

from src.util import exceptions

with open('src/util/config.json', 'r') as f:
    config = json.load(f)

def is_worker():
    async def predicate(ctx):
        workers = ctx.guild.get_role(config["neko_workers"])
        ia = workers in ctx.message.author.roles
        ic = ctx.channel.id == config["command_channel"]
        return ia and ic
    return commands.check(predicate)

def is_power_user():
    def predicate(ctx):
        admin = ctx.guild.get_role(config["neko_herders"])
        pu = ctx.guild.get_role(config["power_user"])
        ia = admin in ctx.message.author.roles or ctx.message.author.id == 358244935041810443
        ip = pu in ctx.message.author.roles
        ic = ctx.channel.id == config["command_channel"]
        if (ia or ip) and ic:
            return True
        elif ic:
            raise exceptions.MissingRequiredPermission("Missing permission `poweruser`.")
    return commands.check(predicate)

def is_admin():
    def predicate(ctx):
        admin = ctx.guild.get_role(config["neko_herders"])
        ia = admin in ctx.message.author.roles or ctx.message.author.id == 358244935041810443
        ic = ctx.channel.id == config["command_channel"]
        if ia and ic:
            return True
        elif ic:
            raise exceptions.MissingRequiredPermission("Missing permission `admin`.")
    return commands.check(predicate)