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

def is_tl(ctx):
        admin = ctx.guild.get_role(config["neko_herders"])
        tl = ctx.guild.get_role(config["tl_id"])
        ia = admin in ctx.message.author.roles or tl in ctx.message.author.roles or ctx.message.author.id == 358244935041810443
        return ia


def is_rd(ctx):
    admin = ctx.guild.get_role(config["neko_herders"])
    rd = ctx.guild.get_role(config["rd_id"])
    ia = admin in ctx.message.author.roles or rd in ctx.message.author.roles or ctx.message.author.id == 358244935041810443
    return ia

def is_ts(ctx):
    admin = ctx.guild.get_role(config["neko_herders"])
    ts = ctx.guild.get_role(config["ts_id"])
    ia = admin in ctx.message.author.roles or ts in ctx.message.author.roles or ctx.message.author.id == 358244935041810443
    return ia

def is_pr(ctx):
    admin = ctx.guild.get_role(config["neko_herders"])
    pr = ctx.guild.get_role(config["pr_id"])
    ia = admin in ctx.message.author.roles or pr in ctx.message.author.roles or ctx.message.author.id == 358244935041810443
    return ia