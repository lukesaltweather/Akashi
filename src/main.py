import asyncio
import os
import random
import sys
import threading
import time
import traceback
from datetime import datetime, timedelta
from io import BytesIO

import aiohttp
import asyncpg
import discord
import sqlalchemy
from aiohttp import web
from discord import Embed, AsyncWebhookAdapter
from discord.ext import commands, tasks
from discord.ext.commands import MissingRequiredArgument
from sqlalchemy import or_, text, func, Date, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, joinedload, aliased
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
import datetime

from src.cogs.add import Add
from src.cogs.assign import Assign
from src.cogs.done import Done
from src.cogs.edit import Edit
from src.cogs.help import MyCog
from src.cogs.info import Info
from src.cogs.misc import Misc
from src.cogs.note import Note
from src.util.checks import is_admin, is_worker
from src.model.message import Message
from src.model.staff import Staff
from src.model.chapter import Chapter
from src.model.project import Project
from src.util import misc, exceptions
from src.util.db import loadDB
from src.model import testdb
import json
import requests
from discord import Webhook, RequestsWebhookAdapter
from prettytable import PrettyTable

from src.util.exceptions import ReactionInvalidRoleError, TagAlreadyExists
from src.util.search import *
from src.util.misc import *
import logging

with open('src/util/config.json', 'r') as f:
    config = json.load(f)

with open('src/util/help.json', 'r') as f:
    jsonhelp = json.load(f)

with open('src/util/emojis.json', 'r') as f:
    emojis = json.load(f)

engine = loadDB(config["db_uri"])
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

"""logging.basicConfig(filename="sqlalchemy.log")
logger2 = logging.getLogger("myapp.sqltime")
logger2.setLevel(logging.DEBUG)

@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement,
                        parameters, context, executemany):
    conn.info.setdefault('query_start_time', []).append(time.time())
    logger2.debug("Start Query: %s" % statement)

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement,
                        parameters, context, executemany):
    total = time.time() - conn.info['query_start_time'].pop(-1)
    logger2.debug("Query Complete!")
    logger2.debug("Total Time: %f" % total)"""


if config["online"]:
    bot = commands.Bot(command_prefix='$')
else:
    bot = commands.Bot(command_prefix='-')


@bot.check
async def globally_block_dms(ctx):
    return ctx.guild is not None

@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))
    activity = discord.Activity(name='$help', type=discord.ActivityType.playing)
    await bot.change_presence(activity=activity)
    bot.Session = sessionmaker(bind=engine)
    bot.config = config
    bot.pool = await asyncpg.create_pool(bot.config.get("db_uri"), min_size=2, max_size=10)
    bot.load_extension('src.cogs.loops')
    bot.load_extension('src.cogs.edit')
    bot.load_extension('src.cogs.misc')
    bot.load_extension('src.cogs.info')
    bot.load_extension('src.cogs.add')
    bot.load_extension('src.cogs.done')
    bot.load_extension('src.cogs.note')
    bot.load_extension('src.cogs.help')
    bot.load_extension('src.cogs.reminder')
    bot.load_extension('src.cogs.stats')
    bot.load_extension("jishaku")
    bot.load_extension('src.cogs.tags')
    bot.em = emojis
    bot.debug = False
    print(discord.version_info)
    bot.uptime = datetime.datetime.now()
    # Set-up the engine here.
    # Create a session

@bot.event
async def on_command_error(ctx, error):
    # This prevents any commands with local handlers being handled here in on_command_error.
    if hasattr(ctx.command, 'on_error'):
        return
    error = getattr(error, 'original', error)
    await ctx.message.add_reaction("❌")
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Please enter at least one argument.")
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send("Command doesn't exist.")
    elif isinstance(error, ValueError):
        await ctx.send("Error while parsing parameters.")
        await ctx.send(error)
    elif isinstance(error, exceptions.NoResultFound):
        await ctx.send(error.message)
    elif isinstance(error, exceptions.StaffNotFoundError):
        await ctx.send("Can't find the staffmember you were searching for.")
    elif isinstance(error, LookupError):
        await ctx.send("Sorry, I couldn't find what you were looking for.")
    elif isinstance(error, commands.CheckFailure):
        await ctx.send("Sorry, but you don't have the required permissions for this command.")
    elif isinstance(error, exceptions.MissingRequiredPermission):
        await ctx.send(error.message)
    elif isinstance(error, exceptions.MissingRequiredParameter):
        await ctx.send("Missing %s" % error.param)
    elif isinstance(error, sqlalchemy.orm.exc.NoResultFound):
        await ctx.send("Sorry, I couldn't find what you were looking for. Does this chapter/project exist?")
    elif isinstance(error, TagAlreadyExists):
        await ctx.send(f"{error.message} Tag already exists.")
    else:
        await ctx.send(error)


@bot.command(hidden=True)
@is_admin()
async def restart(ctx):
    os.system("systemctl restart akashi")


@bot.event
async def on_member_update(before: discord.Member , after: discord.Member):
    worker = before.guild.get_role(345799525274746891)
    if worker not in before.roles and worker in after.roles:
        session1 = bot.Session()
        try:
            st = Staff(after.id, after.name)
            session1.add(st)
            session1.commit()
            session1.close()
            channel = before.guild.get_channel(390395499355701249)
            await channel.send("Successfully added {} to staff. ".format(after.name))
        finally:
            session1.close()


@bot.event
async def on_raw_reaction_add(payload):
    guild = bot.get_guild(config["guild_id"])
    nw = discord.utils.find(lambda r: r.id == config["neko_workers"], guild.roles)
    has_role = nw in guild.get_member(payload.user_id).roles
    channel = bot.get_channel(payload.channel_id)
    user = guild.get_member(payload.user_id)
    if payload.user_id != 603216263484801039 and has_role:
        msg = None
        session = bot.Session()
        message = await channel.fetch_message(payload.message_id)
        try:
            msg = session.query(Message).filter(payload.message_id == Message.message_id).one()
        except:
            session.close()
        try:
            if int(msg.awaiting) == config["ts_id"]:
                ts = (await bot.get_guild(payload.guild_id)).get_role(config["ts_id"])
                if ts not in await get_roles(user):
                    raise ReactionInvalidRoleError
                else:
                    ts_alias = aliased(Staff)
                    chp = session.query(Chapter).outerjoin(ts_alias, Chapter.typesetter_id == ts_alias.id).filter(Chapter.id == msg.chapter).one()
                    chp.typesetter = await dbstaff(payload.user_id, session)
                    author = await bot.get_user(msg.author)
                    embed = misc.completed_embed(chp, author, user, "RD", "TS", bot)
                    session.delete(msg)
                    msg2 = await channel.get_message(payload.message_id)
                    await msg2.clear_reactions()
                    await msg2.unpin()
                    await msg2.edit(embed=embed)
                    await msg2.add_reaction("✅")
                    session.commit()
                session.close()
            elif int(msg.awaiting) == config["rd_id"]:
                rd = (await bot.get_guild(payload.guild_id)).get_role(config["rd_id"])
                if rd not in await get_roles(user):
                    raise ReactionInvalidRoleError
                else:
                    rd_alias = aliased(Staff)
                    chp = session.query(Chapter).outerjoin(rd_alias, Chapter.redrawer_id == rd_alias.id).filter(
                        Chapter.id == msg.chapter).one()
                    chp.redrawer = await dbstaff(payload.user_id, session)
                    author = await bot.get_user(msg.author)
                    embed = misc.completed_embed(chp, author, user, "TL", "RD", bot)
                    session.delete(msg)
                    msg2 = await channel.get_message(payload.message_id)
                    await msg2.clear_reactions()
                    await msg2.unpin()
                    await msg2.edit(embed=embed)
                    await msg2.add_reaction("✅")
                    session.commit()
                session.close()
            elif int(msg.awaiting) == config["tl_id"]:
                tl = (await bot.get_guild(payload.guild_id)).get_role(config["tl_id"])
                if tl not in await get_roles(user):
                    raise ReactionInvalidRoleError
                else:
                    ts_alias = aliased(Staff)
                    chp = session.query(Chapter).outerjoin(ts_alias, Chapter.typesetter_id == ts_alias.id).filter(
                        Chapter.id == msg.chapter).one()
                    chp.translator = await dbstaff(payload.user_id, session)
                    author = await bot.get_user(msg.author)
                    embed = misc.completed_embed(chp, author, user, "RAW", "RD", bot)
                    session.delete(msg)
                    msg2 = await channel.get_message(payload.message_id)
                    await msg2.clear_reactions()
                    await msg2.unpin()
                    await msg2.edit(embed=embed)
                    await msg2.add_reaction("✅")
                    session.commit()
                session.close()
            elif int(msg.awaiting) == config["pr_id"]:
                pr = (await bot.get_guild(payload.guild_id)).get_role(config["pr_id"])
                if pr not in await get_roles(user):
                    raise ReactionInvalidRoleError
                else:
                    pr_alias = aliased(Staff)
                    chp = session.query(Chapter).outerjoin(pr_alias, Chapter.proofreader_id == pr_alias.id).filter(
                        Chapter.id == msg.chapter).one()
                    chp.proofreader = await dbstaff(payload.user_id, session)
                    author = await bot.get_user(msg.author)
                    embed = misc.completed_embed(chp, author, user, "TS", "PR", bot)
                    session.delete(msg)
                    msg2 = await channel.get_message(payload.message_id)
                    await msg2.clear_reactions()
                    await msg2.unpin()
                    await msg2.edit(embed=embed)
                    await msg2.add_reaction("✅")
                    session.commit()
                session.close()
        except Exception:
            pass
        finally:
            session.close()


@is_admin()
@bot.command(enable=False, hidden=True)
async def allcommands(ctx):
    list = ""
    for command in bot.commands:
        list= f"{command.name}, {list}"
    await ctx.send(list)



@is_admin()
@bot.command(enable=False, hidden=True)
async def createtables(ctx):
    await testdb.createtables()


@bot.command(hidden=True)
@is_admin()
async def deletechapter(ctx, *, arg):
    arg = arg[1:]
    d = dict(x.split('=', 1) for x in arg.split(' -'))
    try:
        session = bot.Session()
        query = session.query(Chapter)
        if "id" in d:
            record = query.filter(Project.id == int(d["id"])).one()
        else:
            raise MissingRequiredArgument
        session.delete(record)
    finally:
        session.close()


@is_admin()
@bot.command(hidden=True)
async def editconfig(ctx, *, arg):
    arg = arg[1:]
    d = dict(x.split('=', 1) for x in arg.split(' -'))
    if "neko_workers" in d:
        config["neko_workers"] = d["neko_workers"]
    if "neko_herders" in d:
        config["neko_herders"] = d["neko_herders"]
    if "board_channel" in d:
        config["board_channel"] = d["board_channel"]
    if "command_channel" in d:
        config["command_channel"] = d["command_channel"]
    if "ts_id" in d:
        config["ts_id"] = d["ts_id"]
    if "rd_id" in d:
        config["rd_id"] = d["rd_id"]
    if "tl_id" in d:
        config["tl_id"] = d["tl_id"]
    if "pr_id" in d:
        config["pr_id"] = d["pr_id"]
    with open('src/util/config.json', 'w') as f:
        json.dump(config, f, indent=4)


@is_admin()
@bot.command(hidden=True)
async def displayconfig(ctx):
    with open('src/util/config.json', 'r') as f:
        r = json.load(f)
        del r["heroku_key"]
        del r["offline_key"]
        j = json.dumps(r, indent=4, sort_keys=True)
        await ctx.author.send(j)

# def aiohttp_server():
#     async def say_hello(request):
#         json = await request.post()
#         print(json.get("hello"))
#         return web.Response(text='Hello, world')
#
#     app = web.Application()
#     app.add_routes([web.post('/', say_hello)])
#     runner = web.AppRunner(app)
#     return runner
#
#
# def run_server(runner):
#     loop = asyncio.new_event_loop()
#     asyncio.set_event_loop(loop)
#     loop.run_until_complete(runner.setup())
#     site = web.TCPSite(runner, 'localhost', 8080)
#     loop.run_until_complete(site.start())
#     loop.run_forever()
#
#
# t = threading.Thread(target=run_server, args=(aiohttp_server(),))
# t.start()


if config["online"]:
    bot.run(config["heroku_key"])
else:
    bot.run(config["offline_key"])

