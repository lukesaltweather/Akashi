import json

from discord.ext import commands

from Akashi.util import exceptions


def is_worker():
    async def predicate(ctx):
        return (
            ctx.guild.get_role(ctx.bot.config["server"]["roles"]["member"])
            in ctx.author.roles
        )

    return commands.check(predicate)


def is_admin():
    def predicate(ctx):
        return (
            ctx.guild.get_role(ctx.bot.config["server"]["roles"]["admin"])
            in ctx.author.roles
        )

    return commands.check(predicate)


def is_pu():
    def predicate(ctx):
        return (
            ctx.guild.get_role(ctx.bot.config["server"]["roles"]["power_user"])
            in ctx.author.roles
        )

    return commands.check(predicate)
