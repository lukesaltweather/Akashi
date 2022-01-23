import json

import discord
from discord.ext import commands
from datetime import datetime, timedelta

from prettytable import PrettyTable
import prettytable
from sqlalchemy import Date, text, or_, and_

from src.helpers.arghelper import arghelper
from src.util import exceptions
from src.util.misc import drawimage, formatNumber, async_drawimage, BoardPaginator
from src.util.search import searchstaff, searchproject
from src.util.checks import is_admin
from sqlalchemy.orm import aliased

from src.model.chapter import Chapter
from src.model.project import Project
from src.model.staff import Staff


with open('src/util/help.json', 'r') as f:
    jsonhelp = json.load(f)


class Info(commands.Cog):

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

    @commands.command(aliases=["infochapters", "ic", "infoc"], description=jsonhelp["infochapter"]["description"],
                      usage=jsonhelp["infochapter"]["usage"], brief=jsonhelp["infochapter"]["brief"], help=jsonhelp["infochapter"]["help"])
    async def infochapter(self, ctx, *, arg):
        session = self.bot.Session()
        try:
            async with ctx.channel.typing():
                arg = arg[1:]
                d = dict(x.split('=', 1) for x in arg.split(' -'))
                ts_alias = aliased(Staff)
                rd_alias = aliased(Staff)
                tl_alias = aliased(Staff)
                pr_alias = aliased(Staff)
                query = session.query(Chapter).outerjoin(ts_alias, Chapter.typesetter_id == ts_alias.id).\
                                                    outerjoin(rd_alias, Chapter.redrawer_id == rd_alias.id).\
                                                    outerjoin(tl_alias, Chapter.translator_id == tl_alias.id).\
                                                    outerjoin(pr_alias, Chapter.proofreader_id == pr_alias.id).\
                                                    join(Project, Chapter.project_id == Project.id)
                # joinen geschieht in zukunft hier. damit wird vermieden dass beim sortieren kacke passiert
                links = False
                if "p" in d:
                    if ',' in d["p"]:
                        helper = arghelper(d.get("p"))
                        pro = helper.get_project(session)
                    else:
                        pro = searchproject(d["p"], session).id == Chapter.project_id
                    if pro is not None:
                        query = query.filter(pro)
                    else:
                        pass
                if "title" in d:
                    if ',' in d["title"]:
                        helper = arghelper(d.get("title"))
                        fi = helper.get_title()
                    else:
                        fi = Chapter.title.match(d["title"])
                    query = query.filter(fi)
                if "chapter_from" in d:
                    query = query.filter(Chapter.number >= int(d["chapter_from"]))
                if "chapter_upto" in d:
                    query = query.filter(Chapter.number <= int(d["chapter_upto"]))
                if "c" in d:
                    if ',' in d["c"]:
                        helper = arghelper(d.get("c"))
                        fi = helper.get_number()
                    else:
                        fi = Chapter.number == float(d["c"])
                    query = query.filter(fi)
                if "id" in d:
                    query = query.filter(Chapter.id == int(d["id"]))
                if "ts" in d:
                    if ',' in d["ts"]:
                        helper = arghelper(d.get("ts"))
                        ts = await helper.get_typesetter(ctx, session)
                    else:
                        ts = await searchstaff(d["ts"], ctx, session) == Chapter.typesetter
                    # typ = typ.id
                    query = query.filter(ts)
                if "rd" in d:
                    if ',' in d["rd"]:
                        helper = arghelper(d.get("rd"))
                        rd = await helper.get_redrawer(ctx, session)
                    else:
                        rd = await searchstaff(d["rd"], ctx, session) == Chapter.redrawer
                    # typ = typ.id
                    query = query.filter(rd)
                if "tl" in d:
                    if ',' in d["tl"]:
                        helper = arghelper(d.get("tl"))
                        tl = await helper.get_translator(ctx, session)
                    else:
                        tl = await searchstaff(d["tl"], ctx, session) == Chapter.translator
                    # typ = typ.id
                    query = query.filter(tl)
                if "pr" in d:
                    if ',' in d["pr"]:
                        helper = arghelper(d.get("pr"))
                        pr = await helper.get_proofreader(ctx, session)
                    else:
                        pr = await searchstaff(d["pr"], ctx, session) == Chapter.proofreader
                    query = query.filter(pr)
                if "link_pr" in d:
                    if d["link_pr"] == "None" or d["link_pr"] == "none":
                        query = query.filter(Chapter.link_pr == None)
                    else:
                        query = query.filter(Chapter.link_pr == d["link_pr"])
                if "link_ts" in d:
                    if d["link_ts"] == "None" or d["link_ts"] == "none":
                        query = query.filter(Chapter.link_ts == None)
                    else:
                        query = query.filter(Chapter.link_ts == d["link_ts"])
                if "link_rd" in d:
                    if d["link_rd"] == "None" or d["link_rd"] == "none":
                        query = query.filter(Chapter.link_rd == None)
                    else:
                        query = query.filter(Chapter.link_rd == d["link_rd"])
                if "link_tl" in d:
                    if d["link_tl"] == "None" or d["link_tl"] == "none":
                        query = query.filter(Chapter.link_tl == None)
                    else:
                        query = query.filter(Chapter.link_tl == d["link_tl"])
                if "link_qcts" in d:
                    if d["link_rl"] == "None" or d["link_rl"] == "none":
                        query = query.filter(Chapter.link_rl == None)
                    else:
                        query = query.filter(Chapter.link_rl == d["link_qcts"])
                if "creation_from" in d:
                    date = datetime.strptime(d["creation_from"], "%Y %m %d").date()
                    query = query.filter(Chapter.date_created.cast(Date) >= date)
                if "creation_upto" in d:
                    date = datetime.strptime(d["creation_upto"], "%Y %m %d").date()
                    query = query.filter(Chapter.date_created.cast(Date) <= date)
                if "creation_on" in d:
                    if d["creation_on"] == "None":
                        query = query.filter(Chapter.date_created.cast(Date) == None)
                    else:
                        date = datetime.strptime(d["creation_on"], "%Y %m %d").date()
                        query = query.filter(Chapter.date_created.cast(Date) == date)
                if "tl_on" in d:
                    if d["tl_on"] == "None" or d["tl_on"] == "none":
                        query = query.filter(Chapter.date_tl.cast(Date) == None)
                    else:
                        date = datetime.strptime(d["tl_on"], "%Y %m %d").date()
                        query = query.filter(Chapter.date_tl.cast(Date) == date)
                if "tl_from" in d:
                    date = datetime.strptime(d["tl_from"], "%Y %m %d").date()
                    query = query.filter(Chapter.date_tl.cast(Date) >= date)
                if "tl_upto" in d:
                    date = datetime.strptime(d["tl_upto"], "%Y %m %d").date()
                    query = query.filter(Chapter.date_tl.cast(Date) <= date)
                if "rd_on" in d:
                    if d["rd_on"] == "None" or d["rd_on"] == "none":
                        query = query.filter(Chapter.date_rd.cast(Date) == None)
                    else:
                        date = datetime.strptime(d["rd_on"], "%Y %m %d").date()
                        query = query.filter(Chapter.date_rd.cast(Date) == date)
                if "rd_from" in d:
                    date = datetime.strptime(d["rd_from"], "%Y %m %d").date()
                    query = query.filter(Chapter.date_rd.cast(Date) >= date)
                if "rd_upto" in d:
                    date = datetime.strptime(d["rd_upto"], "%Y %m %d").date()
                    query = query.filter(Chapter.date_rd.cast(Date) <= date)
                if "ts_on" in d:
                    if d["ts_on"] == "None" or d["ts_on"] == "none":
                        query = query.filter(Chapter.date_ts.cast(Date) == None)
                    else:
                        date = datetime.strptime(d["ts_on"], "%Y %m %d").date()
                        query = query.filter(Chapter.date_ts.cast(Date) == date)
                if "ts_from" in d:
                    date = datetime.strptime(d["ts_from"], "%Y %m %d").date()
                    query = query.filter(Chapter.date_ts.cast(Date) >= date)
                if "ts_upto" in d:
                    date = datetime.strptime(d["ts_upto"], "%Y %m %d").date()
                    query = query.filter(Chapter.date_ts.cast(Date) <= date)
                if "pr_on" in d:
                    if d["pr_on"] == "None" or d["pr_on"] == "none":
                        query = query.filter(Chapter.date_pr.cast(Date) == None)
                    else:
                        date = datetime.strptime(d["pr_on"], "%Y %m %d").date()
                        query = query.filter(Chapter.date_pr.cast(Date) == date)
                if "pr_from" in d:
                    date = datetime.strptime(d["pr_from"], "%Y %m %d").date()
                    query = query.filter(Chapter.date_pr.cast(Date) >= date)
                if "pr_upto" in d:
                    date = datetime.strptime(d["pr_upto"], "%Y %m %d").date()
                    query = query.filter(Chapter.date_pr.cast(Date) <= date)
                if "qcts_on" in d:
                    if d["qcts_on"] == "None" or d["qcts_on"] == "none":
                        query = query.filter(Chapter.date_qcts.cast(Date) == None)
                    else:
                        date = datetime.strptime(d["qcts_on"], "%Y %m %d").date()
                        query = query.filter(Chapter.date_qcts.cast(Date) == date)
                if "qcts_from" in d:
                    date = datetime.strptime(d["qcts_from"], "%Y %m %d").date()
                    query = query.filter(Chapter.date_qcts.cast(Date) >= date)
                if "qcts_upto" in d:
                    date = datetime.strptime(d["qcts_upto"], "%Y %m %d").date()
                    query = query.filter(Chapter.date_qcts.cast(Date) <= date)
                if "rl_on" in d:
                    if d["rl_on"] == "None" or d["rl_on"] == "none":
                        query = query.filter(Chapter.date_release.cast(Date) == None)
                    else:
                        date = datetime.strptime(d["rl_on"], "%Y %m %d").date()
                        query = query.filter(Chapter.date_release.cast(Date) == date)
                if "rl_from" in d:
                    date = datetime.strptime(d["rl_from"], "%Y %m %d").date()
                    query = query.filter(Chapter.date_release.cast(Date) >= date)
                if "rl_upto" in d:
                    date = datetime.strptime(d["rl_upto"], "%Y %m %d").date()
                    query = query.filter(Chapter.date_release.cast(Date) <= date)
                if "links" in d:
                    if d.get("links").lower() in ("yes", "y", "true"):
                        links = True
                    else:
                        links = False
                if "status" in d:
                    status = d.get("status").lower()
                    if status == "active":
                        query = query.filter(or_(Chapter.link_rl == None, Chapter.date_release is None))
                    elif status == "tl":
                        query = query.filter(Chapter.link_tl == None)
                    elif status == "rd":
                        query = query.filter(Chapter.link_tl != None)
                        query = query.filter(Chapter.link_tl != "")
                        query = query.filter(or_(Chapter.link_rd == None,Chapter.link_rd == ""))
                    elif status == "ts":
                        query = query.filter(Chapter.link_tl != None)
                        query = query.filter(Chapter.link_tl != "")
                        query = query.filter(Chapter.link_rd != None)
                        query = query.filter(Chapter.link_rd != "")
                        query = query.filter(or_(Chapter.link_ts == None,Chapter.link_ts == ""))
                    elif status == "pr":
                        query = query.filter(Chapter.link_tl != None)
                        query = query.filter(Chapter.link_tl != "")
                        query = query.filter(Chapter.link_rd != None)
                        query = query.filter(Chapter.link_rd != "")
                        query = query.filter(Chapter.link_ts != None)
                        query = query.filter(Chapter.link_ts != "")
                        query = query.filter(or_(Chapter.link_pr == None, Chapter.link_pr == ""))
                    elif status == "qcts":
                        query = query.filter(Chapter.link_tl != None)
                        query = query.filter(Chapter.link_tl != "")
                        query = query.filter(Chapter.link_rd != None)
                        query = query.filter(Chapter.link_rd != "")
                        query = query.filter(Chapter.link_ts != None)
                        query = query.filter(Chapter.link_ts != "")
                        query = query.filter(Chapter.link_pr != None)
                        query = query.filter(Chapter.link_pr != "")
                        query = query.filter(or_(Chapter.link_rl == None, Chapter.link_rl == ""))
                    elif status == "ready":
                        query = query.filter(and_(Chapter.link_rl != None, Chapter.link_rl != ""))
                        query = query.filter(Chapter.date_release != None)

                # if "order_by" in d:
                #     try:
                #         query = query.order_by(text(d["order_by"]))
                #     except Exception:
                #         await ctx.send("Your sorting parameter seems to be off. Use the help command to verify.")
                output = "image"
                if "output" in d:
                    if d["output"] == "text":
                        output = "text"
                    else:
                        output = "image"
                records = query.order_by(Project.title).order_by(Chapter.number).all()
                embed = BoardPaginator(color=discord.Colour.blue(), title="Infochapter")
                embed.set_author(name="Links", icon_url='https://cdn.discordapp.com/icons/345797456614785024/9ef2a960cb5f91439556068b8127512a.webp?size=128', url=None)
                if "fields" in d:
                    fields = d["fields"].replace("\u0020", "").split(",")
                    table = PrettyTable()
                    projects = [str(chapter.project.title) if chapter.project is not None else "None" for chapter in records]
                    table.add_column("Project", projects)
                    chapters = [str(formatNumber(chapter.number)) if chapter is not None else "None" for chapter in records]
                    table.add_column("Chapter", chapters)
                    links_tl = []
                    links_rd = []
                    links_ts = []
                    links_pr = []
                    links_qcts = []
                    for field in fields:
                        if field == "title":
                            titles = [chapter.title if chapter.title is not None else "None" for chapter in records]
                            table.add_column("Title", titles)
                        elif field == "id":
                            id = [str(chapter.id) for chapter in records]
                            table.add_column("ID", id)
                        elif field == "link_tl":
                            for chapter in records:
                                if chapter.link_tl is not None:
                                    links_tl.append(f"[`{chapter.project.title} {formatNumber(chapter.number)}`]({chapter.link_tl})")
                            if len(links_tl) != 0:
                                embed.add_category(title="Translations", l="\n".join(links_tl))
                        elif field == "link_rd":
                            for chapter in records:
                                if chapter.link_rd is not None:
                                    links_rd.append(f"[`{chapter.project.title} {formatNumber(chapter.number)}`]({chapter.link_rd})")
                            if len(links_rd) != 0:
                                embed.add_category(title="Redraws", l="\n".join(links_rd))
                        elif field == "link_ts":
                            for chapter in records:
                                if chapter.link_ts is not None:
                                    links_ts.append(f"[`{chapter.project.title} {formatNumber(chapter.number)}`]({chapter.link_ts})")
                            if len(links_ts) != 0:
                                embed.add_category(title="Typesets", l="\n".join(links_ts))
                        elif field == "link_pr":
                            for chapter in records:
                                if chapter.link_pr is not None:
                                    links_pr.append(f"[`{chapter.project.title} {formatNumber(chapter.number)}`]({chapter.link_pr})")
                            if len(links_pr) != 0:
                                embed.add_category(title="Proofreads", l="\n".join(links_pr))
                        elif field == "link_qcts":
                            for chapter in records:
                                if chapter.link_qcts is not None:
                                    links_qcts.append(f"[`{chapter.project.title} {formatNumber(chapter.number)}`]({chapter.link_qcts})")
                            if len(links_qcts) != 0:
                                embed.add_category(title="QC Typesets", l="\n".join(links_qcts))
                        elif field == "ts":
                            ts = [chapter.typesetter.name if chapter.typesetter is not None else "None" for chapter in records]
                            table.add_column("Typesetter", ts)
                        elif field == "rd":
                            rd = [chapter.redrawer.name if chapter.redrawer is not None else "None" for chapter in records]
                            table.add_column("Redrawer", rd)
                        elif field == "pr":
                            pr = [chapter.proofreader.name if chapter.proofreader is not None else "None" for chapter in records]
                            table.add_column("Proofreader", pr)
                        elif field == "tl":
                            tl = [chapter.translator.name if chapter.translator is not None else "None" for chapter in records]
                            table.add_column("Translator", tl)
                        elif field == "date":
                            tl = [chapter.date_created if chapter.date_created is not None else "None" for chapter in records]
                            table.add_column("Created on", tl)
                        elif field == "date_tl":
                            tl = [chapter.date_tl if chapter.date_tl is not None else "None" for chapter in records]
                            table.add_column("Translated on", tl)
                        elif field == "date_rd":
                            tl = [chapter.date_rd if chapter.date_rd is not None else "None" for chapter in records]
                            table.add_column("Redrawn on", tl)
                        elif field == "date_ts":
                            tl = [chapter.date_ts if chapter.date_ts is not None else "None" for chapter in records]
                            table.add_column("Typeset on", tl)
                        elif field == "date_pr":
                            tl = [chapter.date_pr if chapter.date_pr is not None else "None" for chapter in records]
                            table.add_column("Proofread on", tl)
                        elif field == "date_qcts":
                            tl = [chapter.date_qcts if chapter.date_qcts is not None else "None" for chapter in records]
                            table.add_column("QC Typeset on", tl)
                        elif field == "date_rl":
                            tl = [chapter.date_release if chapter.date_release is not None else "None" for chapter in records]
                            table.add_column("Released on", tl)
                else:
                    table = PrettyTable()
                    projects = [str(chapter.project.title) if chapter.project is not None else "None" for chapter in records]
                    table.add_column("Project", projects)
                    chapters = [str(formatNumber(chapter.number)) if chapter is not None else "None" for chapter in records]
                    table.add_column("Chapter", chapters)
                    links_tl = []
                    links_rd = []
                    links_ts = []
                    links_pr = []
                    links_qcts = []
                    titles = [chapter.title if chapter.title is not None else "None" for chapter in records]
                    table.add_column("Title", titles)
                    id = [str(chapter.id) for chapter in records]
                    table.add_column("ID", id)
                    if links:
                        for chapter in records:
                            if chapter.link_tl is not None:
                                links_tl.append(f"[`{chapter.project.title} {formatNumber(chapter.number)}`]({chapter.link_tl})")
                            if chapter.link_rd is not None:
                                links_rd.append(f"[`{chapter.project.title} {formatNumber(chapter.number)}`]({chapter.link_rd})")
                            if chapter.link_ts is not None:
                                links_ts.append(f"[`{chapter.project.title} {formatNumber(chapter.number)}`]({chapter.link_ts})")
                            if chapter.link_pr is not None:
                                links_pr.append(f"[`{chapter.project.title} {formatNumber(chapter.number)}`]({chapter.link_pr})")
                            if chapter.link_rl is not None:
                                links_qcts.append(f"[`{chapter.project.title} {formatNumber(chapter.number)}`]({chapter.link_rl})")
                        if len(links_tl) != 0:
                            embed.add_category(title="Translations", l="\n".join(links_tl))
                        if len(links_rd) != 0:
                            embed.add_category(title="Redraws", l="\n".join(links_rd))
                        if len(links_ts) != 0:
                            embed.add_category(title="Typesets", l="\n".join(links_ts))
                        if len(links_pr) != 0:
                            embed.add_category(title="Proofreads", l="\n".join(links_pr))
                        if len(links_qcts) != 0:
                            embed.add_category(title="QC Typesets", l="\n".join(links_qcts))
                    tl = [chapter.translator.name if chapter.translator is not None else "None" for chapter in records]
                    table.add_column("Translator", tl)
                    ts = [chapter.typesetter.name if chapter.typesetter is not None else "None" for chapter in records]
                    table.add_column("Typesetter", ts)
                    rd = [chapter.redrawer.name if chapter.redrawer is not None else "None" for chapter in records]
                    table.add_column("Redrawer", rd)
                    pr = [chapter.proofreader.name if chapter.proofreader is not None else "None" for chapter in records]
                    table.add_column("Proofreader", pr)
                if output == "text":
                    await ctx.send(f"```{table}```")
                else:
                    file = await drawimage(table.get_string(title="Chapters"))
                    embed1 = discord.Embed(
                        color=discord.Colour.dark_green()
                    )
                    embed1.set_author(name="Results",
                                     icon_url='https://cdn.discordapp.com/icons/345797456614785024/9ef2a960cb5f91439556068b8127512a.webp?size=128')
                    embed1.set_image(url="attachment://image.png")
                    await ctx.send(file=file, embed=embed1)
                if links:
                    for e in embed.embeds:
                        await ctx.send(embed=e)
        finally:
            session.close()

    @commands.command(aliases=["infoprojects", "infop", "ip"], description=jsonhelp["infoproject"]["description"],
                      usage=jsonhelp["infoproject"]["usage"], brief=jsonhelp["infoproject"]["brief"], help=jsonhelp["infoproject"]["help"])
    async def infoproject(self, ctx, *, arg):
        session = self.bot.Session()
        try:
            async with ctx.channel.typing():
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

                if "status" in d:
                    query = query.filter(Project.status.match(d["status"]))
                if "p" in d:
                    query = query.filter(or_(Project.title.match(d["p"]), Project.altNames.contains(d["p"])))
                if "id" in d:
                    query = query.filter(Project.id == int(d["id"]))
                if "ts" in d:
                    typ = await searchstaff(d["ts"], ctx, session)
                    typ = typ.id
                    query = query.filter(ts_alias.id == typ)
                if "rd" in d:
                    typ = await searchstaff(d["rd"], ctx, session)
                    typ = typ.id
                    query = query.filter(rd_alias.id == typ)
                if "tl" in d:
                    typ = await searchstaff(d["tl"], ctx, session)
                    typ = typ.id
                    query = query.filter(tl_alias.id == typ)
                if "pr" in d:
                    typ = await searchstaff(d["pr"], ctx, session)
                    typ = typ.id
                    query = query.filter(pr_alias.id == typ)
                if "order_by" in d:

                    try:
                        query = query.order_by(d["order_by"])
                    except Exception:
                        await ctx.send("Your sorting parameter seems to be off. Use the help command to verify.")
                if "all" in d:
                    pass
                records = query.all()
                output = "image"
                if "output" in d:
                    if d["output"] == "text":
                        output = "text"
                    else:
                        output = "image"
                table = PrettyTable()
                embed = None
                if "fields" in d:
                    fields = d["fields"].strip(" ").split(",")
                    for field in fields:
                        if field == "title":
                            titles = [project.title if project is not None else "None" for project in records]
                            table.add_column(fieldname="Title", column=titles)
                        elif field == "status":
                            states = [project.status if project is not None else "None" for project in records]
                            table.add_column(fieldname="Status", column=states)
                        elif field == "id":
                            ids = [project.id for project in records]
                            table.add_column(fieldname="ID", column=ids)
                        elif field == "altNames":
                            altnames = [project.altNames if project is not None else "None" for project in records]
                            table.add_column(fieldname="AltNames", column=altnames)
                        elif field == "link":
                            links = [project.link if project is not None else "None" for project in records]
                            table.add_column(fieldname="Links", column=links)
                        elif field == "ts":
                            ts = [project.typesetter.name if project.typesetter is not None else "None" for project in
                                  records]
                            table.add_column(fieldname="Typesetters", column=ts)
                        elif field == "rd":
                            rd = [project.redrawer.name if project.redrawer is not None else "None" for project in records]
                            table.add_column(fieldname="Redrawers", column=rd)
                        elif field == "pr":
                            pr = [project.proofreader.name if project.proofreader is not None else "None" for project in
                                  records]
                            table.add_column(fieldname="Proofreaders", column=pr)
                        elif field == "tl":
                            tl = [project.translator.name if project.translator is not None else "None" for project in
                                  records]
                            table.add_column(fieldname="Translators", column=tl)
                        elif field == "link":
                            links = []
                            for project in records:
                                if project.link is not None:
                                    links.append(f"[`{project.title}`]({project.link})")
                            if len(links) != 0:
                                embed = discord.Embed(color=discord.Colour.greyple())
                                embed.add_field(name="Links", value="\n".join(links), inline=False)
                else:
                    ids = [project.id for project in records]
                    table.add_column(fieldname="ID", column=ids)
                    titles = [project.title if project is not None else "None" for project in records]
                    table.add_column("Title", titles)
                    states = [project.status if project.status is not None else "None" for project in records]
                    table.add_column("Status", states)
                    altnames = [project.altNames if project.altNames is not None else "None" for project in records]
                    table.add_column("AltNames", altnames)
                    links = []
                    for project in records:
                        if project.link is not None:
                            links.append(f"[`{project.title}`]({project.link})")
                    if len(links) != 0:
                        embed = discord.Embed(color=discord.Colour.greyple())
                        embed.add_field(name="Links", value="\n".join(links), inline=False)
                    tl = [project.translator.name if project.translator is not None else "None" for project in records]
                    table.add_column("Translators", tl)
                    rd = [project.redrawer.name if project.redrawer is not None else "None" for project in records]
                    table.add_column("Redrawers", rd)
                    ts = [project.typesetter.name if project.typesetter is not None else "None" for project in records]
                    table.add_column("Typesetters", ts)
                    pr = [project.proofreader.name if project.proofreader is not None else "None" for project in records]
                    table.add_column("Proofreaders", pr)
                if output == "text":
                    await ctx.send(f"```{table}```")
                    if embed is not None:
                        await ctx.send(embed=embed)
                else:
                    file = await drawimage(table.get_string(title="Projects"))
                    embed1 = discord.Embed(
                        color=discord.Colour.greyple()
                    )
                    embed1.set_author(name="Results",
                                      icon_url='https://cdn.discordapp.com/icons/345797456614785024/9ef2a960cb5f91439556068b8127512a.webp?size=128')
                    embed1.set_image(url="attachment://image.png")
                    await ctx.send(file=file, embed=embed1)
                    if embed is not None:
                        await ctx.send(embed=embed)
        finally:
            session.close()


    @commands.command(description=jsonhelp["allprojects"]["description"],
                      usage=jsonhelp["allprojects"]["usage"], brief=jsonhelp["allprojects"]["brief"], help=jsonhelp["allprojects"]["help"])
    async def allprojects(self, ctx):
        session = self.bot.Session()
        try:
            ts_alias = aliased(Staff)
            rd_alias = aliased(Staff)
            tl_alias = aliased(Staff)
            pr_alias = aliased(Staff)
            records = session.query(Project).outerjoin(ts_alias, Project.typesetter_id == ts_alias.id). \
                outerjoin(rd_alias, Project.redrawer_id == rd_alias.id). \
                outerjoin(tl_alias, Project.translator_id == tl_alias.id). \
                outerjoin(pr_alias, Project.proofreader_id == pr_alias.id).all()
            table = PrettyTable()
            titles = [project.title for project in records]
            table.add_column(fieldname="Titles", column=titles)
            states = [project.status if project is not None else "None" for project in records]
            table.add_column("Status", states)
            altnames = [project.altNames if project is not None else "None" for project in records]
            table.add_column("Alternative Titles", altnames)
            links = [f"[`{project.title}`]({project.link})" for project in records]
            tl = [project.translator.name if project.translator is not None else "None" for project in records]
            table.add_column("Translator", tl)
            ts = [project.typesetter.name if project.typesetter is not None else "None" for project in records]
            table.add_column("Typesetter", ts)
            rd = [project.redrawer.name if project.redrawer is not None else "None" for project in records]
            table.add_column("Redrawer", rd)
            pr = [project.proofreader.name if project.proofreader is not None else "None" for project in records]
            table.add_column("Proofreader", pr)
            file = await drawimage(table.get_string(title="Projects"))
            embed1 = discord.Embed(
                color=discord.Colour.greyple()
            )
            l = "\n".join(links)

            embed1.set_author(name="Results",
                              icon_url='https://cdn.discordapp.com/icons/345797456614785024/9ef2a960cb5f91439556068b8127512a.webp?size=128')
            embed1.set_image(url="attachment://image.png")
            embed1.description = l
            await ctx.send(file=file, embed=embed1)
        finally:
            session.close()

    @is_admin()
    @commands.command(description=jsonhelp["allstaff"]["description"],
                      usage=jsonhelp["allstaff"]["usage"], brief=jsonhelp["allstaff"]["brief"], help=jsonhelp["allstaff"]["help"])
    async def allstaff(self, ctx):
        """
        Description
        ==============
        Return a list of all staff members.

        .. error::
           Currently not working.

        Required Role
        =====================
        Role `Neko Herders`.
        """
        session = self.bot.Session()
        staff = session.query(Staff).all()
        embed = discord.Embed(colour=discord.Colour.purple(), title="All Existing Staff")
        table = prettytable.PrettyTable()
        table.add_column("Internal ID", [str(person.id) for person in staff])
        table.add_column("Name", [person.name for person in staff])
        table.add_column("Discord ID", [f"{person.discord_id}" for person in staff])
        table.add_column("Status", [f"{person.status}" for person in staff])
        embed.set_image(url="attachment://image.png")
        file = await drawimage(table.get_string(title="All Staff"))
        await ctx.send(embed=embed, file=file)
        session.close()

    @commands.command(description=jsonhelp["mycurrent"]["description"],
                      usage=jsonhelp["mycurrent"]["usage"], brief=jsonhelp["mycurrent"]["brief"], help=jsonhelp["mycurrent"]["help"])
    async def mycurrent(self, ctx):
        session = self.bot.Session()
        ts_alias = aliased(Staff)
        rd_alias = aliased(Staff)
        tl_alias = aliased(Staff)
        pr_alias = aliased(Staff)
        query = session.query(Chapter).outerjoin(ts_alias, Chapter.typesetter_id == ts_alias.id). \
            outerjoin(rd_alias, Chapter.redrawer_id == rd_alias.id). \
            outerjoin(tl_alias, Chapter.translator_id == tl_alias.id). \
            outerjoin(pr_alias, Chapter.proofreader_id == pr_alias.id). \
            join(Project, Chapter.project_id == Project.id)
        typ = await searchstaff(str(ctx.message.author.id), ctx, session)
        to_tl = query.filter(Chapter.translator == typ).filter(Chapter.link_tl.is_(None)).all()
        to_rd = query.filter(Chapter.redrawer == typ).filter(Chapter.link_rd.is_(None)).all()
        to_ts = query.filter(Chapter.typesetter == typ).filter(Chapter.link_ts.is_(None)).all()
        to_pr = query.filter(Chapter.proofreader == typ).filter(Chapter.link_pr.is_(None)).all()
        to_qcts = query.filter(Chapter.typesetter == typ).filter(or_(Chapter.link_rl == None, Chapter.link_rl == "")).filter(Chapter.link_pr != None, Chapter.link_pr != "").filter(Chapter.link_ts != None, Chapter.link_ts != "").all()
        desc = ""
        if len(to_tl) != 0:
            desc = "`To translate:` "
            for chapter in to_tl:
                desc = f"{desc}\n[{chapter.project.title} {chapter.number}]({chapter.link_raw})"
        if len(to_rd) != 0:
            desc = f"{desc}\n`To redraw:`"
            for chapter in to_rd:
                desc = f"{desc}\n[{chapter.project.title} {chapter.number}]({chapter.link_raw})"
        if len(to_ts) != 0:
            desc = f"{desc}\n`To typeset:`"
            for chapter in to_ts:
                desc = f"{desc}\n{chapter.project.title} {chapter.number}: [RD]({chapter.link_rd}) [TL]({chapter.link_tl})"
        if len(to_pr) != 0:
            desc = f"{desc}\n`To proofread:`"
            for chapter in to_pr:
                desc = f"{desc}\n{chapter.project.title} {chapter.number}: [TS]({chapter.link_ts}) [TL]({chapter.link_tl})"
        if len(to_qcts) != 0:
            desc = f"{desc}\n`To qcts:`"
            for chapter in to_qcts:
                desc = f"{desc}\n{chapter.project.title} {chapter.number}: [TS]({chapter.link_ts}) [PR]({chapter.link_pr})"
        embed = discord.Embed(color=discord.Colour.gold(), description=desc)
        embed.set_author(name="Current chapters",
                         icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)
        session.close()

    @commands.command(description=jsonhelp["current"]["description"],
                      usage=jsonhelp["current"]["usage"], brief=jsonhelp["current"]["brief"], help=jsonhelp["current"]["help"])
    async def current(self, ctx, member: discord.Member):
        session = self.bot.Session()
        ts_alias = aliased(Staff)
        rd_alias = aliased(Staff)
        tl_alias = aliased(Staff)
        pr_alias = aliased(Staff)
        query = session.query(Chapter).outerjoin(ts_alias, Chapter.typesetter_id == ts_alias.id). \
            outerjoin(rd_alias, Chapter.redrawer_id == rd_alias.id). \
            outerjoin(tl_alias, Chapter.translator_id == tl_alias.id). \
            outerjoin(pr_alias, Chapter.proofreader_id == pr_alias.id). \
            join(Project, Chapter.project_id == Project.id)
        typ = await searchstaff(str(member.id), ctx, session)
        to_tl = query.filter(Chapter.translator == typ).filter(Chapter.link_tl.is_(None)).all()
        to_rd = query.filter(Chapter.redrawer == typ).filter(Chapter.link_rd.is_(None)).all()
        to_ts = query.filter(Chapter.typesetter == typ).filter(Chapter.link_ts.is_(None)).all()
        to_pr = query.filter(Chapter.proofreader == typ).filter(Chapter.link_pr.is_(None)).all()
        to_qcts = query.filter(Chapter.typesetter == typ).filter(or_(Chapter.link_rl == None, Chapter.link_rl == "")).filter(Chapter.link_pr != None, Chapter.link_pr != "").filter(Chapter.link_ts != None, Chapter.link_ts != "").all()
        desc = ""
        if len(to_tl) != 0:
            desc = "`To translate:` "
            for chapter in to_tl:
                desc = f"{desc}\n[{chapter.project.title} {formatNumber(chapter.number)}]({chapter.link_raw})"
        if len(to_rd) != 0:
            desc = f"{desc}\n`To redraw:`"
            for chapter in to_rd:
                desc = f"{desc}\n[{chapter.project.title} {formatNumber(chapter.number)}]({chapter.link_raw})"
        if len(to_ts) != 0:
            desc = f"{desc}\n`To typeset:`"
            for chapter in to_ts:
                desc = f"{desc}\n{chapter.project.title} {formatNumber(chapter.number)}: [RD]({chapter.link_rd}) [TL]({chapter.link_tl})"
        if len(to_pr) != 0:
            desc = f"{desc}\n`To proofread:`"
            for chapter in to_pr:
                desc = f"{desc}\n{chapter.project.title} {formatNumber(chapter.number)}: [TS]({chapter.link_ts}) [TL]({chapter.link_tl})"
        if len(to_qcts) != 0:
            desc = f"{desc}\n`To qcts:`"
            for chapter in to_qcts:
                desc = f"{desc}\n{chapter.project.title} {chapter.number}: [TS]({chapter.link_ts}) [PR]({chapter.link_pr})"
        embed = discord.Embed(color=discord.Colour.gold(), description=desc)
        embed.set_author(name=f"{member.display_name}'s current chapters",
                         icon_url=member.avatar_url)
        await ctx.send(embed=embed)
        session.close()

def setup(Bot):
    Bot.add_cog(Info(Bot))
"""
class order_parser:
    def __init__(self, user_input):
        self.input = user_input

    def parse(self):
        if self.input.like("p"):
            return"""
