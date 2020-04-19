import asyncio
import os
import random
import sys
import time
from datetime import datetime, timedelta
from io import BytesIO

import aiohttp
import discord
import sqlalchemy
from discord import Embed, AsyncWebhookAdapter
from discord.ext import commands, tasks
from discord.ext.commands import MissingRequiredArgument
from sqlalchemy import or_, text, func, Date
from sqlalchemy.orm import sessionmaker, joinedload, aliased
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

from src.cogs.add import Add
from src.cogs.assign import Assign
from src.cogs.done import Done
from src.cogs.edit import Edit
from src.cogs.help import MyCog
from src.cogs.info import Info
from src.cogs.misc import Misc
from src.cogs.note import Note
from src.util.checks import is_admin, is_worker, is_power_user
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

from src.util.exceptions import ReactionInvalidRoleError
from src.util.search import *
from src.util.misc import *
import logging

with open('src/util/config.json', 'r') as f:
    config = json.load(f)

with open('src/util/help.json', 'r') as f:
    jsonhelp = json.load(f)

engine = loadDB(config["db_uri"])
logger = logging.getLogger('discord')
logger.setLevel(logging.WARNING)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)


if config["online"]:
    bot = commands.Bot(command_prefix='$')
else:
    bot = commands.Bot(command_prefix='-')


def block_dms():
    def globally_block_dms(ctx):
        return ctx.guild is not None
    return commands.check(globally_block_dms)


@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))
    activity = discord.Activity(name='Watashi', type=discord.ActivityType.watching)
    await bot.change_presence(activity=activity)
    deletemessages.start()
    refreshembed.start()
    bot.add_cog(Assign(bot))
    bot.add_cog(Edit(bot))
    bot.add_cog(Misc(bot))
    bot.add_cog(Info(bot))
    bot.add_cog(Add(bot))
    bot.add_cog(Done(bot))
    bot.add_cog(Note(bot))
    bot.add_cog(MyCog(bot))
    bot.config = config
    bot.Session = sessionmaker(bind=engine)
    print(discord.version_info)
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
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Command doesn't exist.")
    if isinstance(error, ValueError):
        await ctx.send("Error while parsing parameters.")
    if isinstance(error, exceptions.NoResultFound):
        await ctx.send(error.message)
    if isinstance(error, exceptions.StaffNotFoundError):
        await ctx.send("Can't find the staffmember you were searching for.")
    if isinstance(error, LookupError):
        await ctx.send("Sorry, I couldn't find what you were looking for.")
    if isinstance(error, commands.CheckFailure):
        await ctx.send("Sorry, but you don't have the required permissions for this command.")
    if isinstance(error, exceptions.MissingRequiredPermission):
        await ctx.send(error.message)
    if isinstance(error, exceptions.MissingRequiredParameter):
        await ctx.send("Missing %s" % error.param)
    if isinstance(error, sqlalchemy.orm.exc.NoResultFound):
        await ctx.send("Sorry, I couldn't find what you were looking for.")



@bot.command(hidden=True)
@is_admin()
@block_dms()
async def restart(ctx):
    os.system("systemctl restart akashi")


@bot.event
async def on_raw_reaction_add(payload):
    guild = await bot.fetch_guild(config["guild_id"])
    nw = discord.utils.find(lambda r: r.id == config["neko_workers"], guild.roles)
    has_role = nw in (await guild.fetch_member(payload.user_id)).roles
    channel = bot.get_channel(payload.channel_id)
    user = await guild.fetch_member(payload.user_id)
    if payload.user_id != 603216263484801039 and has_role:
        msg = None
        try:
            session = bot.Session()
            msg = session.query(Message).filter(payload.message_id == Message.message_id).one()
            ca = await bot.fetch_channel(payload.channel_id)
            ma = await ca.fetch_message(ca)
            await ma.unpin()
        except:
            session.close()
        try:
            if int(msg.awaiting) == config["ts_id"]:
                ts = (await bot.fetch_guild(payload.guild_id)).get_role(config["ts_id"])
                if ts not in await get_roles(user):
                    raise ReactionInvalidRoleError
                ts_alias = aliased(Staff)
                chp = session.query(Chapter).outerjoin(ts_alias, Chapter.typesetter_id == ts_alias.id).filter(Chapter.id == msg.chapter).one()
                chp.typesetter = await dbstaff(payload.user_id, session)
                await channel.send(f'{chp.typesetter.name} was assigned `{chp.project.title} {chp.number}`')
                await channel.send(f'Translation: {chp.link_tl}')
                await channel.send(f'Redraws: {chp.link_rd}')
                session.delete(msg)
                channel.fetch_message(payload.message_id).clear_reactions()
                channel.fetch_message(payload.message_id).edit(f"Task was taken by {chp.typesetter.name}!")
                channel.fetch_message(payload.message_id).add_reaction("✅")
                session.commit()
                session.close()
            elif int(msg.awaiting) == config["rd_id"]:
                rd = (await bot.fetch_guild(payload.guild_id)).get_role(config["rd_id"])
                if rd not in await get_roles(user):
                    raise ReactionInvalidRoleError
                rd_alias = aliased(Staff)
                chp = session.query(Chapter).outerjoin(rd_alias, Chapter.redrawer_id == rd_alias.id).filter(
                    Chapter.id == msg.chapter).one()
                chp.redrawer = await dbstaff(payload.user_id, session)
                await channel.send(f'{chp.redrawer.name} was assigned `{chp.project.title} {chp.number}`')
                await channel.send(f'Translation: {chp.link_tl}')
                await channel.send(f'Raws: {chp.link_raw}')
                session.delete(msg)
                msg2 = await channel.fetch_message(payload.message_id)
                await msg2.clear_reactions()
                await msg2.edit(content=f"Task was taken by {chp.redrawer.name}!")
                await msg2.add_reaction("✅")
                session.commit()
                session.close()
            elif int(msg.awaiting) == config["tl_id"]:
                tl = (await bot.fetch_guild(payload.guild_id)).get_role(config["tl_id"])
                if tl not in await get_roles(user):
                    raise ReactionInvalidRoleError
                ts_alias = aliased(Staff)
                chp = session.query(Chapter).outerjoin(ts_alias, Chapter.typesetter_id == ts_alias.id).filter(
                    Chapter.id == msg.chapter).one()
                chp.typesetter = await dbstaff(payload.user_id, session)
                await channel.send(f'{chp.typesetter.name} was assigned `{chp.project.title} {chp.number}`')
                await channel.send(f'Raws: {chp.link_raw}')
                session.delete(msg)
                channel.fetch_message(payload.message_id).clear_reactions()
                channel.fetch_message(payload.message_id).edit(f"Task was taken by {chp.translator.name}!")
                channel.fetch_message(payload.message_id).add_reaction("✅")
                session.commit()
                session.close()
            elif int(msg.awaiting) == config["pr_id"]:
                pr = (await bot.fetch_guild(payload.guild_id)).get_role(config["pr_id"])
                if pr not in await get_roles(user):
                    raise ReactionInvalidRoleError
                pr_alias = aliased(Staff)
                chp = session.query(Chapter).outerjoin(pr_alias, Chapter.proofreader_id == pr_alias.id).filter(
                    Chapter.id == msg.chapter).one()
                chp.proofreader = await dbstaff(payload.user_id, session)
                await channel.send(f'{chp.proofreader.name} was assigned `{chp.project.title} {chp.number}`')
                await channel.send(f'Translation: {chp.link_tl}')
                await channel.send(f'Typeset: {chp.link_ts}')
                session.delete(msg)
                channel.fetch_message(payload.message_id).clear_reactions()
                channel.fetch_message(payload.message_id).edit(f"Task was taken by {chp.proofreader.name}!")
                channel.fetch_message(payload.message_id).add_reaction("✅")
                session.commit()
                session.close()
        except Exception:
            pass


@is_admin()
@bot.command(enable=False, hidden=True)
@block_dms()
async def allcommands(ctx):
    list = ""
    for command in bot.commands:
        list= f"{command.name}, {list}"
    await ctx.send(list)



@is_admin()
@bot.command(enable=False, hidden=True)
@block_dms()
async def createtables(ctx):
    await testdb.createtables()


@tasks.loop(hours=2)
async def deletemessages():
    session = bot.Session()
    messages = session.query(Message).all()
    for message in messages:
        if message.created_on < (datetime.utcnow() - timedelta(hours=48)) and message.reminder:
            channel = bot.get_channel(config["command_channel"])
            m = await channel.fetch_message(message.message_id)
            await m.clear_reactions()
            await m.unpin()
            await m.add_reaction("❌")
            msg = m.jump_url
            embed = discord.Embed(color=discord.Colour.red())
            embed.set_author(name="Assignment", icon_url="https://cdn.discordapp.com/icons/345797456614785024/9ef2a960cb5f91439556068b8127512a.webp?size=128")
            chapter = session.query(Chapter).filter(Chapter.id == message.chapter).one()
            wordy = (await bot.fetch_user(345845639663583252)).mention
            embed.description = f"*{chapter.project.title}* {formatNumber(chapter.number)}\nNo staffmember assigned themselves to Chapter.\n[Jump!]({msg})\n"
            await channel.send(message={wordy}, embed=embed)
            session.delete(message)
        elif message.created_on < (datetime.utcnow() - timedelta(hours=24)) and not message.reminder:
            channel = bot.get_channel(config["command_channel"])
            m = await channel.fetch_message(message.message_id)
            msg = m.jump_url
            embed = discord.Embed(color=discord.Colour.red())
            embed.set_author(name="Assignment Reminder", icon_url="https://cdn.discordapp.com/icons/345797456614785024/9ef2a960cb5f91439556068b8127512a.webp?size=128")
            chapter = session.query(Chapter).filter(Chapter.id == message.chapter).one()
            who = {    config["ts_id"]: "Typesetter",
                        config["rd_id"]: "Redrawer",
                        config["tl_id"]: "Translator",
                        config["pr_id"]: "Proofreader",
            }
            embed.description = f"*{chapter.project.title}* {formatNumber(chapter.number)}\nStill requires a {who.get(int(message.awaiting))}!\n[Jump!]({msg})\n"
            await channel.send(embed=embed)
            message.reminder = True
        else:
            pass
    session.commit()
    session.close()


@tasks.loop(seconds=60)
async def refreshembed():
    with open('src/util/board.json', 'r') as f:
        messages = json.load(f)
    ch = bot.get_channel(config['board_channel'])
    session = bot.Session()
    projects = session.query(Project).filter\
        (Project.status == "active").order_by(Project.position.asc()).all()
    for x in projects:
        chapters = session.query(Chapter).options(
            joinedload(Chapter.translator),
            joinedload(Chapter.typesetter),
            joinedload(Chapter.redrawer),
            joinedload(Chapter.proofreader)).\
            filter(Chapter.project_id == x.id).order_by(Chapter.number.asc()).all()
        list_in_progress_project = []
        list_done_project = []
        for y in chapters:
            done = 0
            chapter = f" [Raws]({y.link_raw}) |"
            if y.translator is None and y.link_tl is None:
                chapter = chapter + " ~~TL~~ |"
            elif y.translator is not None and y.link_tl is None:
                chapter = chapter + f" **TL**({y.translator.name}) |"
            elif y.link_tl is not None:
                chapter = "{} [TL ({})]({}) |".format(chapter, y.translator.name if y.translator is not None else "None", y.link_tl)
                done += 1
            if y.redrawer is None and y.link_rd is None:
                chapter = chapter + " ~~RD~~ |"
            elif y.redrawer is not None and y.link_rd is None:
                chapter = chapter + f" **RD**({y.redrawer.name}) |"
            elif y.link_rd is not None:
                chapter = chapter + f" [RD ({y.redrawer.name if y.redrawer is not None else 'None'})]({y.link_rd}) |"
                done += 1
            if y.typesetter is None and y.link_ts is None:
                chapter = chapter + " ~~TS~~ |"
            elif y.typesetter is not None and y.link_ts is None:
                chapter = chapter + f" **TS**({y.typesetter.name}) |"
            elif y.link_ts is not None:
                chapter = chapter + f" [TS ({y.typesetter.name if y.typesetter is not None else 'None'})]({y.link_ts}) |"
                done += 1
            if y.proofreader is None and y.link_pr is None:
                chapter = chapter + " ~~PR~~ |"
            elif y.proofreader is not None and y.link_pr is None:
                chapter = chapter + f" **PR**({y.proofreader.name}) |"
            elif y.link_pr is not None:
                chapter = chapter + f" [PR ({y.proofreader.name  if y.proofreader is not None else 'None'})]({y.link_pr}) |"
            if y.link_rl is not None:
                chapter = chapter + f" [QCTS]({y.link_rl})"
                done += 1
            done += 1
            if chapter != "" and done != 5 and y.date_release is None:
                num = misc.formatNumber(y.number)
                chapter = "Chapter {}:{}".format(num, chapter)
                list_in_progress_project.append(f"{chapter}\n")
            elif chapter != "" and done == 5 and y.date_release is None:
                num = misc.formatNumber(y.number)
                chapter = "Chapter {}:{}".format(num, chapter)
                list_done_project.append(f"{chapter}\n")
        if f"{x.id}" in messages:
            msg = await ch.fetch_message(messages[f"{x.id}"])
            if x.color is None:
                color = random.choice([discord.Colour.blue(), discord.Colour.green(), discord.Colour.purple(), discord.Colour.dark_red(), discord.Colour.dark_teal()])
            else:
                color = discord.Colour(int(x.color, 16))
            embed = discord.Embed(
                colour=color
            )
            embed.set_author(name=x.title, icon_url=x.icon, url=x.link)
            embed.set_thumbnail(url=x.thumbnail)
            embed.title = "Link to project"
            embed.url = x.link
            if len(list_in_progress_project) != 0:
                c = " ".join(b for b in list_in_progress_project)
                embed.add_field(name="Chapters in Progress", value=""+c, inline=False)
            if len(list_done_project) != 0:
                c = " ".join(b for b in list_done_project)
                embed.add_field(name="Chapters ready for release", value=""+c, inline=False)
            await msg.edit(embed=embed)
        else:
            if x.color is None:
                color = random.choice([discord.Colour.blue(), discord.Colour.green(), discord.Colour.purple(), discord.Colour.dark_red(), discord.Colour.dark_teal()])
            else:
                color = discord.Colour(int(x.color, 16))
            embed = discord.Embed(
                colour=color
            )
            embed.title = "Link to project"
            embed.url = x.link
            embed.set_author(name=x.title, icon_url=x.icon, url=x.link)
            embed.set_thumbnail(url=x.thumbnail)
            if len(list_in_progress_project) != 0:
                c = " ".join(b for b in list_in_progress_project)
                embed.add_field(name="Chapters in Progress", value=""+c, inline=False)
            if len(list_done_project) != 0:
                c = " ".join(b for b in list_done_project)
                embed.add_field(name="Chapters ready for release", value=""+c, inline=False)
            message = await ch.send(embed=embed)
            messages[f"{x.id}"] = message.id
            with open('src/util/board.json', 'w') as f:
                json.dump(messages, f, indent=4)

    session.commit()
    session.close()


@bot.command(hidden=True)
@is_admin()
@block_dms()
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
@block_dms()
async def editconfig(ctx, *, arg):
    arg = arg[1:]
    d = dict(x.split('=', 1) for x in arg.split(' -'))
    if "neko_workers" in d:
        config["neko_workers"] = d["neko_workers"]
    if "neko_herders" in d:
        config["neko_herders"] = d["neko_herders"]
    if "power_user" in d:
        config["power_user"] = d["power_user"]
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
@block_dms()
async def displayconfig(ctx):
    with open('src/util/config.json', 'r') as f:
        r = json.load(f)
        del r["heroku_key"]
        del r["offline_key"]
        j = json.dumps(r, indent=4, sort_keys=True)
        await ctx.author.send(j)

if config["online"]:
    bot.run(config["heroku_key"])
else:
    bot.run(config["offline_key"])
