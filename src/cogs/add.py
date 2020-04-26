import asyncio
import json

import discord
from discord.ext import commands
from src.util.exceptions import MissingRequiredParameter
from prettytable import PrettyTable
from sqlalchemy import func
from sqlalchemy.orm import aliased

from datetime import datetime, timedelta
from src.model.chapter import Chapter
from src.model.project import Project
from src.model.staff import Staff
from src.util import exceptions, misc
from src.util.search import searchproject, searchstaff
from src.util.misc import formatNumber, drawimage
from src.util.checks import is_admin
import time

with open('src/util/config.json', 'r') as f:
    config = json.load(f)

with open('src/util/help.json', 'r') as f:
    jsonhelp = json.load(f)

class Add(commands.Cog):
    """
        Cog with all of the commands used for adding to the database
    """
    def __init__(self, client):
        self.bot = client



    async def cog_check(self, ctx):
        worker = ctx.guild.get_role(self.bot.config["neko_workers"])
        ia = worker in ctx.message.author.roles
        ic = ctx.channel.id == self.bot.config["command_channel"]
        guild = ctx.guild is not None
        if ia and ic and guild:
            return True
        elif ic:
            raise exceptions.MissingRequiredPermission("Wrong Channel.")
        elif not guild:
            raise exceptions.MissingRequiredPermission("Missing permission `Server Member`")


    @commands.command(description=jsonhelp["addstaff"]["description"], usage=jsonhelp["addstaff"]["usage"], brief=jsonhelp["addstaff"]["brief"], help=jsonhelp["addstaff"]["help"])
    @is_admin()
    async def addstaff(self, ctx, *, arg):
        session1 = self.bot.Session()
        try:
            arg = arg[1:]
            d = dict(x.split('=', 1) for x in arg.split(' -'))
            if d["id"] is not None:
                stobject = discord.utils.find(lambda m: m.id == int(d["id"]), ctx.guild.members)
                if stobject is not None:
                    st = Staff(d["id"], stobject.name)
                    session1.add(st)
                    session1.commit()
                    session1.close()
                    await ctx.send("Successfully added {} to staff. ".format(stobject.name))
                else:
                    await ctx.send("Sorry, could not find a user with that ID")
            else:
                await ctx.send("There seems to be a mistake in the command syntax.")
        finally:
            session1.close()

    @commands.command(description=jsonhelp["addstaffexp"]["description"], usage=jsonhelp["addstaffexp"]["usage"], brief=jsonhelp["addstaffexp"]["brief"], help=jsonhelp["addstaffexp"]["help"])
    @is_admin()
    async def addstaffexp(self, ctx, *, arg):
        session1 = self.bot.Session()
        try:
            arg = arg[1:]
            d = dict(x.split('=', 1) for x in arg.split(' -'))
            if d["id"] is not None:
                st = Staff(d["id"], d["name"])
                session1.add(st)
                session1.commit()
                session1.close()
                await ctx.send(f"Successfully added {d['name']} to staff with id {d['id']}")
            else:
                await ctx.send("There seems to be a mistake in the command syntax.")
        finally:
            session1.close()



    @commands.command(aliases=["ap", "addp", "addproj"], description=jsonhelp["addproject"]["description"],
                      usage=jsonhelp["addproject"]["usage"], brief=jsonhelp["addproject"]["brief"], help=jsonhelp["addproject"]["help"])
    async def addproject(self, ctx, *, arg):
        session1 = self.bot.Session()
        try:
            arg = arg[1:]
            d = dict(x.split('=', 1) for x in arg.split(' -'))
            if "link" in d and "title" in d and "altNames" in d and "status" in d:
                try:
                    projects = searchproject(d["title"], session1)
                    raise AttributeError
                except exceptions.NoResultFound:
                    pr = Project(d["title"], d["status"] if "status" in d else "inactive", d["link"], d["altNames"])
                    if "ts" in d:
                        pr.typesetter = await searchstaff(d["ts"], ctx, session1)
                    if "rd" in d:
                        pr.redrawer = await searchstaff(d["rd"], ctx, session1)
                    if "pr" in d:
                        pr.proofreader = await searchstaff(d["pr"], ctx, session1)
                    if "tl" in d:
                        pr.translator = await searchstaff(d["tl"], ctx, session1)
                    if "icon" in d:
                        pr.icon = d["icon"]
                    if "thumbnail" in d:
                        pr.thumbnail = d["thumbnail"]
                    session1.add(pr)
                    await ctx.send(
                        "✅ Successfully added {} to projects with the status {}".format(d["title"], d["status"]))
                except AttributeError:
                    raise AttributeError
            else:
                raise MissingRequiredParameter("link, title, altNames or status")
            session1.commit()
        finally:
            session1.close()


    @commands.command(aliases=["ac", "addch", "addc"], description=jsonhelp["addchapter"]["description"],
                      usage=jsonhelp["addchapter"]["usage"], brief=jsonhelp["addchapter"]["brief"], help=jsonhelp["addchapter"]["help"])
    async def addchapter(self, ctx, *, arg):
        session1 = self.bot.Session()
        try:
            arg = arg[1:]
            d = dict(x.split('=', 1) for x in arg.split(' -'))
            table = PrettyTable()
            if "c" in d and "link_raw" in d and "p" in d:
                chp = Chapter(d["c"], d["link_raw"])
                chp.project = searchproject(d["p"], session1)
            elif "c" in d and "link" in d and "p" in d:
                chp = Chapter(d["c"], d["link"])
                chp.project = searchproject(d["p"], session1)
            else:
                raise MissingRequiredParameter("c, p or link_raw")
            table.add_column("Project", [chp.project.title])
            table.add_column("Chapter", [formatNumber(float(chp.number))])
            table.add_column("Raws", [chp.link_raw])
            if "ts" in d:
                chp.typesetter = await searchstaff(d["ts"], ctx, session1)
                table.add_column(fieldname="Typesetter", column=[chp.typesetter.name])
            if "rd" in d:
                chp.redrawer = await searchstaff(d["rd"], ctx, session1)
                table.add_column(fieldname="Redrawer", column=[chp.redrawer.name])
            if "pr" in d:
                chp.proofreader = await searchstaff(d["pr"], ctx, session1)
                table.add_column(fieldname="Proofreads", column=[chp.proofreader.name])
            if "tl" in d:
                chp.translator = await searchstaff(d["tl"], ctx, session1)
                table.add_column(fieldname="Translation", column=[chp.translator.name])
            if "link_ts" in d:
                chp.link_ts = d["link_ts"]
                table.add_column(fieldname="Link TS", column=[chp.link_ts])
            if "link_rd" in d:
                chp.link_rd = d["link_rd"]
                table.add_column(fieldname="Link RD", column=[chp.link_rd])
            if "link_tl" in d:
                chp.link_tl = d["link_tl"]
                table.add_column(fieldname="Link TL", column=[chp.link_tl])
            if "link_pr" in d:
                chp.link_pr = d["link_pr"]
                table.add_column(fieldname="Link PR", column=[chp.link_pr])
            chp.date_created = func.now()
            session1.add(chp)
            t = table.get_string(title="Chapter Preview")
            message = await ctx.send(file=await misc.drawimage(t))
            await message.add_reaction("✅")
            await message.add_reaction("❌")
            await asyncio.sleep(delay=0.5)

            def check(reaction, user):
                return user == ctx.message.author and (str(reaction.emoji) == '✅' or str(reaction.emoji) == '❌')

            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
            except asyncio.TimeoutError:
                await message.delete()
                await ctx.channel.send('No reaction from command author. Chapter was not added.')
                session1.rollback()
            else:
                if str(reaction.emoji) == "✅":
                    num = formatNumber(float(chp.number))
                    await ctx.channel.send('Sucessfully added {} {} to chapters.'.format(chp.project.title, num))
                    session1.commit()
                    await message.clear_reactions()
                else:
                    await message.delete()
                    await ctx.channel.send('Action cancelled by user.')
                    session1.rollback()
                    await message.clear_reactions()
        finally:
            session1.close()

def setup(Bot):
    Bot.add_cog(Add(Bot))