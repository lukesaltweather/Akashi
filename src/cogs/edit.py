import asyncio
import json

import discord
from discord.ext import commands
from discord.ext.commands import MissingRequiredArgument
from prettytable import PrettyTable
from sqlalchemy import func
from sqlalchemy.orm import aliased

from datetime import datetime, timedelta
from src.model.chapter import Chapter
from src.model.project import Project
from src.model.staff import Staff
from src.util import exceptions
from src.util.exceptions import MissingRequiredParameter
from src.util.search import searchproject, searchstaff
from src.util.misc import formatNumber, drawimage
import time
from src.util.checks import is_admin


with open('src/util/help.json', 'r') as f:
    jsonhelp = json.load(f)

class Edit(commands.Cog):

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


    @commands.command(aliases=["editch", "editc", "ec"], description=jsonhelp["editchapter"]["description"],
                      usage=jsonhelp["editchapter"]["usage"], brief=jsonhelp["editchapter"]["brief"], help=jsonhelp["editchapter"]["help"])
    @commands.max_concurrency(1, per=discord.ext.commands.BucketType.default, wait=True)
    async def editchapter(self, ctx, *, arg):
        session = self.bot.Session()
        try:
            async with ctx.channel.typing():
                arg = arg[1:]
                d = dict(x.split('=', 1) for x in arg.split(' -'))
                ts_alias = aliased(Staff)
                rd_alias = aliased(Staff)
                tl_alias = aliased(Staff)
                pr_alias = aliased(Staff)
                query = session.query(Chapter).outerjoin(ts_alias, Chapter.typesetter_id == ts_alias.id). \
                    outerjoin(rd_alias, Chapter.redrawer_id == rd_alias.id). \
                    outerjoin(tl_alias, Chapter.translator_id == tl_alias.id). \
                    outerjoin(pr_alias, Chapter.proofreader_id == pr_alias.id). \
                    join(Project, Chapter.project_id == Project.id)
                table = PrettyTable()
                table.add_column("", ["ORIGINAL", "EDIT"])
                if "p" in d and "c" in d:
                    proj = searchproject(d["p"], session)
                    record = query.filter(Chapter.project_id == proj.id).filter(Chapter.number == float(d["c"])).one()
                elif "id" in d:
                    record = query.filter(Chapter.id == int(d["id"])).one()
                else:
                    raise MissingRequiredParameter("Project and Chapter or ID")
                if "title" in d:
                    if record.title is not None:
                        table.add_column("Title", [record.title, d["title"]])
                    else:
                        table.add_column("Title", ["None", d["title"]])
                    record.title = d["title"]
                if "tl" in d:
                    if d["tl"] in ("None", "none"):
                        if record.translator is not None:
                            table.add_column("Translator", [record.translator.name, "None"])
                        else:
                            table.add_column("Translator", ["None", d["tl"]])
                        record.translator = None
                    else:
                        tl = await searchstaff(d["tl"], ctx, session)
                        if tl is not None:
                            if record.translator is not None:
                                table.add_column("Translator", [record.translator.name, d["tl"]])
                            else:
                                table.add_column("Translator", ["None", d["tl"]])
                            record.translator = tl
                        else:
                            raise exceptions.StaffNotFoundError
                if "rd" in d:
                    if d["rd"] in ("None", "none"):
                        if record.redrawer is not None:
                            table.add_column("Redrawer", [record.redrawer.name, d["rd"]])
                        else:
                            table.add_column("Redrawer", ["None", d["rd"]])
                        record.redrawer = None
                    else:
                        rd = await searchstaff(d["rd"], ctx, session)
                        if rd is not None:
                            if record.redrawer is not None:
                                table.add_column("Redrawer", [record.redrawer.name, d["rd"]])
                            else:
                                table.add_column("Redrawer", ["None", d["rd"]])
                            record.redrawer = rd
                        else:
                            raise exceptions.StaffNotFoundError
                if "ts" in d:
                    if d["ts"] in ("None", "none"):
                        if record.typesetter is not None:
                            table.add_column("Typesetter", [record.typesetter.name, d["ts"]])
                        else:
                            table.add_column("Typesetter", ["None", d["ts"]])
                        record.typesetter = None
                    else:
                        ts = await searchstaff(d["ts"], ctx, session)
                        if ts is not None:
                            if record.typesetter is not None:
                                table.add_column("Typesetter", [record.typesetter.name, d["ts"]])
                            else:
                                table.add_column("Typesetter", ["None", d["ts"]])
                            record.typesetter = ts
                        else:
                            raise exceptions.StaffNotFoundError
                if "pr" in d:
                    if d["pr"] in ("None", "none"):
                        if record.proofreader is not None:
                            table.add_column("Proofreader", [record.proofreader.name, d["pr"]])
                        else:
                            table.add_column("Proofreader", ["None", d["pr"]])
                        record.proofreader = None
                    else:
                        pr = await searchstaff(d["pr"], ctx, session)
                        if pr is not None:
                            if record.proofreader is not None:
                                table.add_column("Proofreader", [record.proofreader.name, d["pr"]])
                            else:
                                table.add_column("Proofreader", ["None", d["pr"]])
                            record.proofreader = pr
                        else:
                            raise exceptions.StaffNotFoundError
                if "link_ts" in d:
                    table.add_column("Link TS", [record.link_ts, d["link_ts"]])
                    if d["link_ts"] != "":
                        record.link_ts = d["link_ts"]
                    else:
                        record.link_ts = None
                if "link_tl" in d:
                    table.add_column("Link TL", [record.link_tl, d["link_tl"]])
                    if d["link_tl"] != "":
                        record.link_tl = d["link_tl"]
                    else:
                        record.link_tl = None
                if "link_rd" in d:
                    table.add_column("Link RD", [record.link_rd, d["link_rd"]])
                    if d["link_rd"] != "":
                        record.link_rd = d["link_rd"]
                    else:
                        record.link_rd = None
                if "link_pr" in d:
                    table.add_column("Link PR", [record.link_pr, d["link_pr"]])
                    if d["link_pr"] != "":
                        record.link_pr = d["link_pr"]
                    else:
                        record.link_pr = None
                if "link_qcts" in d:
                    table.add_column("Link QCTS", [record.link_rl, d["link_qcts"]])
                    if d["link_qcts"] != "":
                        record.link_rl = d["link_qcts"]
                    else:
                        record.link_rl = None
                if "link_raw" in d:
                    table.add_column("Link Raw", [record.link_raw, d["link_raw"]])
                    record.link_raw = d["link_raw"]
                if "date_tl" in d:
                    # table.add_column("Date TL", [time.strftime("%Y %m %d", record.date_tl), d["date_tl"]])
                    if d["date_tl"] != "":
                        record.date_tl = datetime.strptime(d["date_tl"], "%Y %m %d")
                    else:
                        record.date_tl = None
                if "date_rd" in d:
                    # table.add_column("Date RD", [time.strftime("%Y %m %d", record.date_rd), d["date_rd"]])
                    if d["date_rd"] != "":
                        record.date_rd = datetime.strptime(d["date_rd"], "%Y %m %d")
                    else:
                        record.date_rd = None
                if "date_ts" in d:
                    # table.add_column("Date TS", [time.strftime("%Y %m %d", record.date_ts), d["date_ts"]])
                    if d["date_ts"] != "":
                        record.date_rd = datetime.strptime(d["date_ts"], "%Y %m %d")
                    else:
                        record.date_ts = None
                if "date_pr" in d:
                    # table.add_column("Date PR", [time.strftime("%Y %m %d", record.date_pr), d["date_pr"]])
                    if d["date_pr"] != "":
                        record.date_pr = datetime.strptime(d["date_pr"], "%Y %m %d")
                    else:
                        record.date_pr = None
                if "date_qcts" in d:
                    # table.add_column("Date QCTS", [time.strftime("%Y %m %d", record.date_qcts), d["date_qcts"]])
                    if d["date_qcts"] != "":
                        record.date_qcts = datetime.strptime(d["date_qcts"], "%Y %m %d")
                    else:
                        record.date_qcts = None
                if "date_rl" in d:
                    # table.add_column("Date Release", [time.strftime("%Y %m %d", record.date_release), d["date_rl"]])
                    if d["date_rl"] != "":
                        record.date_release = datetime.strptime(d["date_rl"], "%Y %m %d")
                    else:
                        record.date_release = None
                if "to_project" in d:
                    proj = searchproject(d["to_project"], session)
                    record.project = proj
                    table.add_column("New Project", [record.project.title, d["to_project"]])
                if "to_chapter" in d:
                    table.add_column("New Ch. Number", [record.number, d["to_chapter"]])
                    record.number = int(d["to_chapter"])
                if "notes" in d:
                    record.notes = d["notes"]
                    table.add_column("Notes", [record.notes, d["notes"]])
                t = table.get_string(title=f"{record.project.title} {formatNumber(record.number)}")
                image = await drawimage(t)
                embed1 = discord.Embed(
                    color=discord.Colour.dark_red()
                )
                embed1.set_image(url="attachment://image.png")
                message = await ctx.send(file=image, embed=embed1)
                await message.add_reaction("✅")
                await message.add_reaction("❌")
                await asyncio.sleep(delay=0.5)

                def check(reaction, user):
                    return user == ctx.message.author and (str(reaction.emoji) == '✅' or str(reaction.emoji) == '❌')

                try:
                    reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
                except asyncio.TimeoutError:
                    await ctx.channel.send('No reaction from command author. Chapter was not added.')
                    session.rollback()
                else:
                    if str(reaction.emoji) == "✅":
                        num = formatNumber(float(record.number))
                        await ctx.channel.send('Successfully edited chapter.'.format(record.project.title, num))
                        await ctx.message.add_reaction("✅")
                        session.commit()
                    else:
                        await ctx.channel.send('Transaction cancelled by user.')
                        session.rollback()
                        await ctx.message.add_reaction("❌")
                await message.delete()
        finally:
            session.close()

    @commands.command(aliases=["editproj", "editp", "ep"],description=jsonhelp["editproject"]["description"],
                      usage=jsonhelp["editproject"]["usage"], brief=jsonhelp["editproject"]["brief"], help=jsonhelp["editproject"]["help"])
    async def editproject(self, ctx, *, arg):
        session = self.bot.Session()
        try:
            arg = arg[1:]
            d = dict(x.split('=', 1) for x in arg.split(' -'))
            ts_alias = aliased(Staff)
            rd_alias = aliased(Staff)
            tl_alias = aliased(Staff)
            pr_alias = aliased(Staff)
            query = session.query(Project).outerjoin(ts_alias, Project.typesetter_id == ts_alias.id). \
                outerjoin(rd_alias, Project.redrawer_id == rd_alias.id). \
                outerjoin(tl_alias, Project.translator_id == tl_alias.id). \
                outerjoin(pr_alias, Project.proofreader_id == pr_alias.id)
            if "p" in d:
                proj = searchproject(d["p"], session)
                record = query.filter(Project.id == proj.id).one()
            elif "id" in d:
                record = query.filter(Project.id == int(d["id"])).one()
            else:
                raise MissingRequiredParameter(param="Project and Chapter or ID")
            table = PrettyTable()
            table.add_column("", ["ORIGINAL", "EDIT"])
            if "title" in d:
                if record.title is not None:
                    table.add_column("Title", [record.title, d["title"]])
                else:
                    table.add_column("Title", ["None", d["title"]])
                record.title = d["title"]
            if "status" in d:
                if record.status is not None:
                    table.add_column("Status", [record.status, d["status"]])
                else:
                    table.add_column("Status", ["None", d["status"]])
                record.status = d["status"]
            if "color" in d:
                if d["color"] in ("None", "none"):
                    record.color = None
                else:
                    d["color"] = d["color"].strip("#")
                    if record.color is not None:
                        table.add_column("Color", [record.color, d["color"]])
                    else:
                        table.add_column("Color", ["None", d["color"]])
                    record.color = d["color"]
            if "position" in d:
                if d["position"] in ("None", "none"):
                    record.position = None
                else:
                    if record.position is not None:
                        table.add_column("Pos", [record.position, d["position"]])
                    else:
                        table.add_column("Pos", ["None", d["position"]])
                    record.position = int(d["position"])
            if "tl" in d:
                if d["tl"] in ("None", "none"):
                    if record.translator is not None:
                        table.add_column("Translator", [record.translator.name, "None"])
                    else:
                        table.add_column("Translator", ["None", d["tl"]])
                    record.translator = None
                else:
                    tl = await searchstaff(d["tl"], ctx, session)
                    if tl is not None:
                        if record.translator is not None:
                            table.add_column("Translator", [record.translator.name, d["tl"]])
                        else:
                            table.add_column("Translator", ["None", d["tl"]])
                        record.translator = tl
                    else:
                        raise exceptions.StaffNotFoundError
            if "rd" in d:
                if d["rd"] in ("None", "none"):
                    if record.redrawer is not None:
                        table.add_column("Redrawer", [record.redrawer.name, d["rd"]])
                    else:
                        table.add_column("Redrawer", ["None", d["rd"]])
                    record.redrawer = None
                else:
                    rd = await searchstaff(d["rd"], ctx, session)
                    if rd is not None:
                        if record.redrawer is not None:
                            table.add_column("Redrawer", [record.redrawer.name, d["rd"]])
                        else:
                            table.add_column("Redrawer", ["None", d["rd"]])
                        record.redrawer = rd
                    else:
                        raise exceptions.StaffNotFoundError
            if "ts" in d:
                if d["ts"] in ("None", "none"):
                    if record.typesetter is not None:
                        table.add_column("Typesetter", [record.typesetter.name, d["ts"]])
                    else:
                        table.add_column("Typesetter", ["None", d["ts"]])
                    record.typesetter = None
                else:
                    ts = await searchstaff(d["ts"], ctx, session)
                    if ts is not None:
                        if record.typesetter is not None:
                            table.add_column("Typesetter", [record.typesetter.name, d["ts"]])
                        else:
                            table.add_column("Typesetter", ["None", d["ts"]])
                        record.typesetter = ts
                    else:
                        raise exceptions.StaffNotFoundError
            if "pr" in d:
                if d["pr"] in ("None", "none"):
                    if record.proofreader is not None:
                        table.add_column("Proofreader", [record.proofreader.name, d["pr"]])
                    else:
                        table.add_column("Proofreader", ["None", d["pr"]])
                    record.proofreader = None
                else:
                    pr = await searchstaff(d["pr"], ctx, session)
                    if pr is not None:
                        if record.proofreader is not None:
                            table.add_column("Proofreader", [record.proofreader.name, d["pr"]])
                        else:
                            table.add_column("Proofreader", ["None", d["pr"]])
                        record.proofreader = pr
                    else:
                        raise exceptions.StaffNotFoundError
            if "altNames" in d:
                if record.altNames is not None:
                    table.add_column("Altnames", [record.altNames, d["altNames"]])
                else:
                    table.add_column("Altnames", ["None", d["altNames"]])
                record.altNames = d["altNames"]
            if "thumbnail" in d:
                if record.altNames is not None:
                    table.add_column("Thumbnail", [record.thumbnail, d["thumbnail"]])
                else:
                    table.add_column("Thumbnail", ["None", d["thumbnail"]])
                record.thumbnail = d["thumbnail"]
            if "icon" in d:
                if record.icon is not None:
                    table.add_column("icon", [record.icon, d["icon"]])
                else:
                    table.add_column("icon", ["None", d["icon"]])
                record.icon = d["icon"]
            if "link" in d:
                if record.link is not None:
                    table.add_column("Link", [record.link, d["link"]])
                else:
                    table.add_column("link", ["link", d["link"]])
                record.link = d["link"]
            t = table.get_string(title=f"{record.title}")
            image = await drawimage(t)
            embed1 = discord.Embed(
                color=discord.Colour.dark_red()
            )
            embed1.set_image(url="attachment://image.png")
            message = await ctx.send(file=image, embed=embed1)
            await message.add_reaction("✅")
            await message.add_reaction("❌")
            await asyncio.sleep(delay=0.5)

            def check(reaction, user):
                return user == ctx.message.author and (str(reaction.emoji) == '✅' or str(reaction.emoji) == '❌')

            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
            except asyncio.TimeoutError:
                await ctx.channel.send('No reaction from command author. Project was not edited.')
                session.rollback()
            else:
                if str(reaction.emoji) == "✅":
                    await ctx.channel.send('Sucessfully edited project {}.'.format(record.title))
                    await ctx.message.add_reaction("✅")
                    session.commit()
                else:
                    await ctx.channel.send('Transaction cancelled by user.')
                    await ctx.message.add_reaction("❌")
                    session.rollback()
            await message.delete()
        finally:
            session.commit()
            session.close()


    @commands.command(description=jsonhelp["editstaff"]["description"],
                      usage=jsonhelp["editstaff"]["usage"], brief=jsonhelp["editstaff"]["brief"], help=jsonhelp["editstaff"]["help"])
    @is_admin()
    @commands.max_concurrency(1, per=discord.ext.commands.BucketType.default, wait=True)
    async def editstaff(self, ctx, *, arg):
        session = self.bot.Session()
        try:
            arg = arg[1:]
            d = dict(x.split('=', 1) for x in arg.split(' -'))
            if "id" in d:
                member = session.query(Staff).filter(Staff.id == int(d["id"])).one()
                if "discord_id" in d:
                    member.discord_id = int(d["discord_id"])
                if "name" in d:
                    member.name = d["name"]
                if "status" in d:
                    member.status = d["status"]
                session.commit()
                await ctx.message.add_reaction("👍")
                await ctx.send("Success.")
            else:
                raise MissingRequiredParameter("ID")
        finally:
            session.close()

    @commands.command(description=jsonhelp["clear"]["description"],
                      usage=jsonhelp["clear"]["usage"], brief=jsonhelp["clear"]["brief"], help=jsonhelp["clear"]["help"])
    @is_admin()
    @commands.max_concurrency(1, per=discord.ext.commands.BucketType.default, wait=True)
    async def clear(self, ctx, *, arg):
        session = self.bot.Session()
        try:
            arg = arg[1:]
            d = dict(x.split('=', 1) for x in arg.split(' -'))
            if "p" in d and "c" in d:
                project = searchproject(d["p"], session)
                chapter = session.query(Chapter).filter(Chapter.project_id == project.id).filter(
                    Chapter.number == int(d["c"])).one()
            elif "id" in d:
                chapter = session.query(Chapter).filter(Chapter.id == int(d["id"])).one()
            else:
                raise MissingRequiredParameter("Project and Chapter or ID")
            chapter.title = ""
            chapter.notes = ""
            chapter.link_raw = ""
            chapter.link_tl = ""
            chapter.link_ts = ""
            chapter.link_rd = ""
            chapter.link_pr = ""
            chapter.link_qcts = ""
            chapter.date_tl = None
            chapter.date_rd = None
            chapter.date_ts = None
            chapter.date_pr = None
            chapter.date_qcts = None
            chapter.date_release = None
            chapter.typesetter = None
            chapter.redrawer = None
            chapter.proofreader = None
            chapter.translator = None
            session.commit()
        finally:
            session.close()


    @commands.command(description=jsonhelp["release"]["description"],
                      usage=jsonhelp["release"]["usage"], brief=jsonhelp["release"]["brief"], help=jsonhelp["release"]["help"])
    async def release(self, ctx, *, arg):
        async with ctx.channel.typing():
            arg = arg[1:]
            d = dict(x.split('=', 1) for x in arg.split(' -'))
            session = self.bot.Session()
            query = session.query(Chapter). \
                join(Project, Chapter.project_id == Project.id)
            if "p" in d and "c" in d:
                proj = searchproject(d["p"], session)
                record = query.filter(Chapter.project_id == proj.id).filter(Chapter.number == float(d["c"])).one()
            elif "id" in d:
                record = query.filter(Chapter.id == int(d["id"])).one()
            else:
                raise MissingRequiredArgument
            if "date" in d:
                record.date_release = datetime.strptime(d["date"], "%Y %m %d")
            else:
                record.date_release = func.now()
            session.commit()
            if "p" in d and "c" in d:
                proj = searchproject(d["p"], session)
                record = query.filter(Chapter.project_id == proj.id).filter(Chapter.number == float(d["c"])).one()
            elif "id" in d:
                record = query.filter(Chapter.id == int(d["id"])).one()
            else:
                raise MissingRequiredArgument
            embed = discord.Embed(color=discord.Colour.green())
            embed.set_author(name="Success!",
                             icon_url="https://cdn.discordapp.com/icons/345797456614785024/9ef2a960cb5f91439556068b8127512a.webp?size=128")
            embed.add_field(name="\u200b",
                            value=f"Releasedate of {record.project.title} {record.number} set to {record.date_release.strftime('%Y/%m/%d')}")
            await ctx.send(embed=embed)
            session.close()

def setup(Bot):
    Bot.add_cog(Edit(Bot))