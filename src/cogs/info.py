import json

import discord
from discord.ext import commands
from datetime import datetime, timedelta

from prettytable import PrettyTable
from sqlalchemy import Date, text, or_, and_
from sqlalchemy.sql.expression import select

from src.helpers.arghelper import arghelper
from src.util import exceptions
from src.util.misc import (
    drawimage,
    format_number,
    async_drawimage,
    BoardPaginator,
    MISSING,
)
from src.util.search import searchstaff, searchproject
from src.util.checks import is_admin
from sqlalchemy.orm import aliased

from src.model.chapter import Chapter
from src.model.project import Project
from src.model.staff import Staff

from src.util.flags.infoflags import InfoChapter, InfoProject
from src.util.context import CstmContext
from src.util.db import get_all


class Info(commands.Cog):
    def __init__(self, client):
        self.bot = client

    @commands.command(
        aliases=["infochapters", "ic", "infoc"],
        extras={"doc": "https://akashi.readthedocs.io/en/stable/Info/infochapter.html"}
    )
    async def infochapter(self, ctx: CstmContext, *, flags: InfoChapter):
        """
        Description
        ==============
        Get info on chapters.

        Required Role
        =====================
        Role `Neko Workers`.

        Arguments
        ===========

        Optional
        ------------
        :project: List of projects the chapters can belong to.
        :tl, rd, ts, pr: List of staff working on respective steps.
        :chapter_from, chapter_upto: Give a minimum and/or maximum chapter number to look for.
        :chapter: A list of numbers the found chapters can have.
        :id: A list of ids the found chapters can have.
        :release_from, release_upto, release_on: Filter for release Date.
        :status: Current status of the chapter. Can be one of "active", "tl", "ts", "rd", "pr", "qcts" or "ready".
        :fields: What columns to include in the result table.
        :links: Either true or false, whether the bot sends the links to each steps of the chapters.

        Related Articles:
        ^^^^^^^^^^^^^^^^^^^^

        You can find a tutorial on how to pass a list of arguments here:
        :doc:`/Tutorials/ParamListTut`

        Dates have to be in following format:
        :doc:`/Tutorials/DateTutorial`
        """
        session = ctx.session
        async with ctx.channel.typing():
            ts_alias = aliased(Staff)
            rd_alias = aliased(Staff)
            tl_alias = aliased(Staff)
            pr_alias = aliased(Staff)
            query = (
                select(Chapter)
                .outerjoin(ts_alias, Chapter.typesetter_id == ts_alias.id)
                .outerjoin(rd_alias, Chapter.redrawer_id == rd_alias.id)
                .outerjoin(tl_alias, Chapter.translator_id == tl_alias.id)
                .outerjoin(pr_alias, Chapter.proofreader_id == pr_alias.id)
                .join(Project, Chapter.project_id == Project.id)
            )
            if flags.project:
                if len(flags.project) > 1:
                    helper = arghelper(flags.project)
                    pro = helper.get_project(session)
                else:
                    pro = flags.project[0] == Chapter.project
                if pro:
                    query = query.filter(pro)
                else:
                    pass
            if flags.title is not MISSING:
                if flags.title:
                    helper = arghelper(flags.title)
                    query = query.filter(helper.get_title())
                else:
                    query = query.filter(Chapter.title == None)
            if flags.chapter_from:
                query = query.filter(Chapter.number >= flags.chapter_from)
            if flags.chapter_upto:
                query = query.filter(Chapter.number <= flags.chapter_upto)
            if flags.chapter:
                if len(flags.chapter) > 1:
                    helper = arghelper(flags.chapter)
                    fi = helper.get_number()
                else:
                    fi = Chapter.number == flags.chapter[0]
                query = query.filter(fi)
            if flags.id:
                query = query.filter(Chapter.id == flags.id)
            if flags.ts:
                query = query.filter(
                    Chapter.typesetter_id.in_([staff.id for staff in flags.ts])
                )
            if flags.rd:
                conds = list()
                for arg in flags.rd:
                    conds.append(Chapter.redrawer == arg)
                query = query.filter(or_(*conds))
            if flags.tl:
                conds = list()
                for arg in flags.tl:
                    conds.append(Chapter.translator == arg)
                query = query.filter(or_(*conds))
            if flags.pr:
                conds = list()
                for arg in flags.pr:
                    conds.append(Chapter.proofreader == arg)
                query = query.filter(or_(*conds))
            if flags.release_on:
                query = query.filter(
                    Chapter.date_release.cast(Date) == flags.release_on
                )
            if flags.release_from:
                query = query.filter(
                    Chapter.date_release.cast(Date) >= flags.release_from
                )
            if flags.release_upto:
                query = query.filter(
                    Chapter.date_release.cast(Date) <= flags.release_upto
                )
            if flags.status:
                status = flags.status.lower()
                if status == "active":
                    query = query.filter(
                        or_(Chapter.link_rl == None, Chapter.date_release is None)
                    )
                elif status == "tl":
                    query = query.filter(Chapter.link_tl == None)
                elif status == "rd":
                    query = query.filter(Chapter.link_tl != None)
                    query = query.filter(Chapter.link_tl != "")
                    query = query.filter(
                        or_(Chapter.link_rd == None, Chapter.link_rd == "")
                    )
                elif status == "ts":
                    query = query.filter(Chapter.link_tl != None)
                    query = query.filter(Chapter.link_tl != "")
                    query = query.filter(Chapter.link_rd != None)
                    query = query.filter(Chapter.link_rd != "")
                    query = query.filter(
                        or_(Chapter.link_ts == None, Chapter.link_ts == "")
                    )
                elif status == "pr":
                    query = query.filter(Chapter.link_tl != None)
                    query = query.filter(Chapter.link_tl != "")
                    query = query.filter(Chapter.link_rd != None)
                    query = query.filter(Chapter.link_rd != "")
                    query = query.filter(Chapter.link_ts != None)
                    query = query.filter(Chapter.link_ts != "")
                    query = query.filter(
                        or_(Chapter.link_pr == None, Chapter.link_pr == "")
                    )
                elif status == "qcts":
                    query = query.filter(Chapter.link_tl != None)
                    query = query.filter(Chapter.link_tl != "")
                    query = query.filter(Chapter.link_rd != None)
                    query = query.filter(Chapter.link_rd != "")
                    query = query.filter(Chapter.link_ts != None)
                    query = query.filter(Chapter.link_ts != "")
                    query = query.filter(Chapter.link_pr != None)
                    query = query.filter(Chapter.link_pr != "")
                    query = query.filter(
                        or_(Chapter.link_rl == None, Chapter.link_rl == "")
                    )
                elif status == "ready":
                    query = query.filter(
                        and_(Chapter.link_rl != None, Chapter.link_rl != "")
                    )
                    query = query.filter(Chapter.date_release != None)

            stmt = query.order_by(Project.title).order_by(Chapter.number)
            records = await get_all(session, stmt)
            embed = BoardPaginator(color=discord.Colour.blue(), title="Infochapter")
            embed.set_author(
                name="Links",
                icon_url="https://cdn.discordapp.com/icons/345797456614785024/9ef2a960cb5f91439556068b8127512a.webp?size=128",
                url=None,
            )
            if flags.fields:
                table = PrettyTable()
                projects = [
                    str(chapter.project.title)
                    if chapter.project is not None
                    else "None"
                    for chapter in records
                ]
                table.add_column("Project", projects)
                chapters = [
                    str(format_number(chapter.number))
                    if chapter is not None
                    else "None"
                    for chapter in records
                ]
                table.add_column("Chapter", chapters)
                links_tl = []
                links_rd = []
                links_ts = []
                links_pr = []
                links_qcts = []
                for field in flags.fields:
                    if field == "title":
                        titles = [
                            chapter.title if chapter.title is not None else "None"
                            for chapter in records
                        ]
                        table.add_column("Title", titles)
                    elif field == "id":
                        id = [str(chapter.id) for chapter in records]
                        table.add_column("ID", id)
                    elif field == "link_tl":
                        for chapter in records:
                            if chapter.link_tl is not None:
                                links_tl.append(
                                    f"[`{chapter.project.title} {format_number(chapter.number)}`]({chapter.link_tl})"
                                )
                        if len(links_tl) != 0:
                            embed.add_category(
                                title="Translations", l="\n".join(links_tl)
                            )
                    elif field == "link_rd":
                        for chapter in records:
                            if chapter.link_rd is not None:
                                links_rd.append(
                                    f"[`{chapter.project.title} {format_number(chapter.number)}`]({chapter.link_rd})"
                                )
                        if len(links_rd) != 0:
                            embed.add_category(title="Redraws", l="\n".join(links_rd))
                    elif field == "link_ts":
                        for chapter in records:
                            if chapter.link_ts is not None:
                                links_ts.append(
                                    f"[`{chapter.project.title} {format_number(chapter.number)}`]({chapter.link_ts})"
                                )
                        if len(links_ts) != 0:
                            embed.add_category(title="Typesets", l="\n".join(links_ts))
                    elif field == "link_pr":
                        for chapter in records:
                            if chapter.link_pr is not None:
                                links_pr.append(
                                    f"[`{chapter.project.title} {format_number(chapter.number)}`]({chapter.link_pr})"
                                )
                        if len(links_pr) != 0:
                            embed.add_category(
                                title="Proofreads", l="\n".join(links_pr)
                            )
                    elif field == "link_qcts":
                        for chapter in records:
                            if chapter.link_qcts is not None:
                                links_qcts.append(
                                    f"[`{chapter.project.title} {format_number(chapter.number)}`]({chapter.link_qcts})"
                                )
                        if len(links_qcts) != 0:
                            embed.add_category(
                                title="QC Typesets", l="\n".join(links_qcts)
                            )
                    elif field == "ts":
                        ts = [
                            chapter.typesetter.name
                            if chapter.typesetter is not None
                            else "None"
                            for chapter in records
                        ]
                        table.add_column("Typesetter", ts)
                    elif field == "rd":
                        rd = [
                            chapter.redrawer.name
                            if chapter.redrawer is not None
                            else "None"
                            for chapter in records
                        ]
                        table.add_column("Redrawer", rd)
                    elif field == "pr":
                        pr = [
                            chapter.proofreader.name
                            if chapter.proofreader is not None
                            else "None"
                            for chapter in records
                        ]
                        table.add_column("Proofreader", pr)
                    elif field == "tl":
                        tl = [
                            chapter.translator.name
                            if chapter.translator is not None
                            else "None"
                            for chapter in records
                        ]
                        table.add_column("Translator", tl)
                    elif field == "date":
                        tl = [
                            chapter.date_created
                            if chapter.date_created is not None
                            else "None"
                            for chapter in records
                        ]
                        table.add_column("Created on", tl)
                    elif field == "date_tl":
                        tl = [
                            chapter.date_tl if chapter.date_tl is not None else "None"
                            for chapter in records
                        ]
                        table.add_column("Translated on", tl)
                    elif field == "date_rd":
                        tl = [
                            chapter.date_rd if chapter.date_rd is not None else "None"
                            for chapter in records
                        ]
                        table.add_column("Redrawn on", tl)
                    elif field == "date_ts":
                        tl = [
                            chapter.date_ts if chapter.date_ts is not None else "None"
                            for chapter in records
                        ]
                        table.add_column("Typeset on", tl)
                    elif field == "date_pr":
                        tl = [
                            chapter.date_pr if chapter.date_pr is not None else "None"
                            for chapter in records
                        ]
                        table.add_column("Proofread on", tl)
                    elif field == "date_qcts":
                        tl = [
                            chapter.date_qcts
                            if chapter.date_qcts is not None
                            else "None"
                            for chapter in records
                        ]
                        table.add_column("QC Typeset on", tl)
                    elif field == "date_rl":
                        tl = [
                            chapter.date_release
                            if chapter.date_release is not None
                            else "None"
                            for chapter in records
                        ]
                        table.add_column("Released on", tl)
            else:
                table = PrettyTable()
                projects = [
                    str(chapter.project.title)
                    if chapter.project is not None
                    else "None"
                    for chapter in records
                ]
                table.add_column("Project", projects)
                chapters = [
                    str(format_number(chapter.number))
                    if chapter is not None
                    else "None"
                    for chapter in records
                ]
                table.add_column("Chapter", chapters)
                links_tl = []
                links_rd = []
                links_ts = []
                links_pr = []
                links_qcts = []
                titles = [
                    chapter.title if chapter.title is not None else "None"
                    for chapter in records
                ]
                table.add_column("Title", titles)
                id = [str(chapter.id) for chapter in records]
                table.add_column("ID", id)
                if flags.links:
                    for chapter in records:
                        if chapter.link_tl is not None:
                            links_tl.append(
                                f"[`{chapter.project.title} {format_number(chapter.number)}`]({chapter.link_tl})"
                            )
                        if chapter.link_rd is not None:
                            links_rd.append(
                                f"[`{chapter.project.title} {format_number(chapter.number)}`]({chapter.link_rd})"
                            )
                        if chapter.link_ts is not None:
                            links_ts.append(
                                f"[`{chapter.project.title} {format_number(chapter.number)}`]({chapter.link_ts})"
                            )
                        if chapter.link_pr is not None:
                            links_pr.append(
                                f"[`{chapter.project.title} {format_number(chapter.number)}`]({chapter.link_pr})"
                            )
                        if chapter.link_rl is not None:
                            links_qcts.append(
                                f"[`{chapter.project.title} {format_number(chapter.number)}`]({chapter.link_rl})"
                            )
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
                tl = [
                    chapter.translator.name
                    if chapter.translator is not None
                    else "None"
                    for chapter in records
                ]
                table.add_column("Translator", tl)
                ts = [
                    chapter.typesetter.name
                    if chapter.typesetter is not None
                    else "None"
                    for chapter in records
                ]
                table.add_column("Typesetter", ts)
                rd = [
                    chapter.redrawer.name if chapter.redrawer is not None else "None"
                    for chapter in records
                ]
                table.add_column("Redrawer", rd)
                pr = [
                    chapter.proofreader.name
                    if chapter.proofreader is not None
                    else "None"
                    for chapter in records
                ]
                table.add_column("Proofreader", pr)

            file = await drawimage(table.get_string(title="Chapters"))
            embed1 = discord.Embed(color=discord.Colour.dark_green())
            embed1.set_author(
                name="Results",
                icon_url="https://cdn.discordapp.com/icons/345797456614785024/9ef2a960cb5f91439556068b8127512a.webp?size=128",
            )
            embed1.set_image(url="attachment://image.png")
            await ctx.send(file=file, embed=embed1)
            if flags.links:
                for e in embed.embeds:
                    await ctx.send(embed=e)

    @commands.command(
        aliases=["infoprojects", "infop", "ip"],
        usage="https://akashi.readthedocs.io/en/stable/Info/infoproject.html",
    )
    async def infoproject(self, ctx, *, flags: InfoProject):
        """
        Description
        ==============
        Get info on projects.

        Required Role
        =====================
        Role `Neko Workers`.

        Arguments
        ===========

        Optional
        ------------
        :status: Filter by current status of the project.
        :tl, rd, ts, pr: Filter by Staff working on project.
        :project: Filter by name.
        :fields: What columns to include in the result table.

        Related Articles:
        ^^^^^^^^^^^^^^^^^^^^

        You can find a list of possible fields here:
        :doc:`/Tutorials/Fields`
        """
        session = ctx.session
        ts_alias = aliased(Staff)
        rd_alias = aliased(Staff)
        tl_alias = aliased(Staff)
        pr_alias = aliased(Staff)
        query = (
            select(Project)
            .outerjoin(ts_alias, Project.typesetter_id == ts_alias.id)
            .outerjoin(rd_alias, Project.redrawer_id == rd_alias.id)
            .outerjoin(tl_alias, Project.translator_id == tl_alias.id)
            .outerjoin(pr_alias, Project.proofreader_id == pr_alias.id)
        )

        if flags.status is not MISSING:
            query = query.filter(Project.status.match(flags.status))  # type: ignore
        if flags.project:
            query = query.filter(
                or_(
                    Project.title.match(flags.project),  # type: ignore
                    Project.altNames.contains(flags.project),  # type: ignore
                )
            )
        if flags.ts is not MISSING:
            query = query.filter(ts_alias == flags.ts)
        if flags.rd is not MISSING:
            query = query.filter(rd_alias == flags.rd)
        if flags.tl is not MISSING:
            query = query.filter(tl_alias == flags.tl)
        if flags.pr is not MISSING:
            query = query.filter(pr_alias == flags.pr)
        records = await get_all(session, query)
        table = PrettyTable()
        embed = None
        if flags.fields:
            fields = flags.fields
            for field in fields:  # type: ignore
                if field == "title":
                    titles = [
                        project.title if project is not None else "None"
                        for project in records
                    ]
                    table.add_column(fieldname="Title", column=titles)
                elif field == "status":
                    states = [
                        project.status if project is not None else "None"
                        for project in records
                    ]
                    table.add_column(fieldname="Status", column=states)
                elif field == "id":
                    ids = [project.id for project in records]
                    table.add_column(fieldname="ID", column=ids)
                elif field == "altNames":
                    altnames = [
                        project.altNames if project is not None else "None"
                        for project in records
                    ]
                    table.add_column(fieldname="AltNames", column=altnames)
                elif field == "link":
                    links = [
                        project.link if project is not None else "None"
                        for project in records
                    ]
                    table.add_column(fieldname="Links", column=links)
                elif field == "ts":
                    ts = [
                        project.typesetter.name
                        if project.typesetter is not None
                        else "None"
                        for project in records
                    ]
                    table.add_column(fieldname="Typesetters", column=ts)
                elif field == "rd":
                    rd = [
                        project.redrawer.name
                        if project.redrawer is not None
                        else "None"
                        for project in records
                    ]
                    table.add_column(fieldname="Redrawers", column=rd)
                elif field == "pr":
                    pr = [
                        project.proofreader.name
                        if project.proofreader is not None
                        else "None"
                        for project in records
                    ]
                    table.add_column(fieldname="Proofreaders", column=pr)
                elif field == "tl":
                    tl = [
                        project.translator.name
                        if project.translator is not None
                        else "None"
                        for project in records
                    ]
                    table.add_column(fieldname="Translators", column=tl)
                elif field == "link":
                    links = []
                    for project in records:
                        if project.link is not None:
                            links.append(f"[`{project.title}`]({project.link})")
                    if len(links) != 0:
                        embed = discord.Embed(color=discord.Colour.greyple())
                        embed.add_field(
                            name="Links", value="\n".join(links), inline=False
                        )
        else:
            ids = [project.id for project in records]
            table.add_column(fieldname="ID", column=ids)
            titles = [
                project.title if project is not None else "None" for project in records
            ]
            table.add_column("Title", titles)
            states = [
                project.status if project.status is not None else "None"
                for project in records
            ]
            table.add_column("Status", states)
            altnames = [
                project.altNames if project.altNames is not None else "None"
                for project in records
            ]
            table.add_column("AltNames", altnames)
            links = []
            for project in records:
                if project.link is not None:
                    links.append(f"[`{project.title}`]({project.link})")
            if len(links) != 0:
                embed = discord.Embed(color=discord.Colour.greyple())
                embed.add_field(name="Links", value="\n".join(links), inline=False)
            tl = [
                project.translator.name if project.translator is not None else "None"
                for project in records
            ]
            table.add_column("Translators", tl)
            rd = [
                project.redrawer.name if project.redrawer is not None else "None"
                for project in records
            ]
            table.add_column("Redrawers", rd)
            ts = [
                project.typesetter.name if project.typesetter is not None else "None"
                for project in records
            ]
            table.add_column("Typesetters", ts)
            pr = [
                project.proofreader.name if project.proofreader is not None else "None"
                for project in records
            ]
            table.add_column("Proofreaders", pr)

        file = await drawimage(table.get_string(title="Projects"))
        embed1 = discord.Embed(color=discord.Colour.greyple())
        embed1.set_author(
            name="Results",
            icon_url="https://cdn.discordapp.com/icons/345797456614785024/9ef2a960cb5f91439556068b8127512a.webp?size=128",
        )
        embed1.set_image(url="attachment://image.png")
        await ctx.send(file=file, embed=embed1)
        if embed:
            await ctx.send(embed=embed)

    @commands.command(
        usage="https://akashi.readthedocs.io/en/stable/Info/allprojects.html"
    )
    async def allprojects(self, ctx):
        """
        Description
        ==============
        Return a list of all project.

        .. caution::
            This command doesn't take any arguments.

        Required Role
        =====================
        Role `Neko Workers`.

        Arguments
        ===========

        Optional
        ------------


        Related Articles:
        ^^^^^^^^^^^^^^^^^^^^

        """
        session = ctx.session
        ts_alias = aliased(Staff)
        rd_alias = aliased(Staff)
        tl_alias = aliased(Staff)
        pr_alias = aliased(Staff)
        stmt = (
            select(Project)
            .outerjoin(ts_alias, Project.typesetter_id == ts_alias.id)
            .outerjoin(rd_alias, Project.redrawer_id == rd_alias.id)
            .outerjoin(tl_alias, Project.translator_id == tl_alias.id)
            .outerjoin(pr_alias, Project.proofreader_id == pr_alias.id)
        )
        records = await get_all(session, stmt)
        table = PrettyTable()
        titles = [project.title for project in records]
        table.add_column(fieldname="Titles", column=titles)
        states = [
            project.status if project is not None else "None" for project in records
        ]
        table.add_column("Status", states)
        altnames = [
            project.altNames if project is not None else "None" for project in records
        ]
        table.add_column("Alternative Titles", altnames)
        links = [f"[`{project.title}`]({project.link})" for project in records]
        tl = [
            project.translator.name if project.translator is not None else "None"
            for project in records
        ]
        table.add_column("Translator", tl)
        ts = [
            project.typesetter.name if project.typesetter is not None else "None"
            for project in records
        ]
        table.add_column("Typesetter", ts)
        rd = [
            project.redrawer.name if project.redrawer is not None else "None"
            for project in records
        ]
        table.add_column("Redrawer", rd)
        pr = [
            project.proofreader.name if project.proofreader is not None else "None"
            for project in records
        ]
        table.add_column("Proofreader", pr)
        file = await drawimage(table.get_string(title="Projects"))
        embed1 = discord.Embed(color=discord.Colour.greyple())
        l = "\n".join(links)

        embed1.set_author(
            name="Results",
            icon_url="https://cdn.discordapp.com/icons/345797456614785024/9ef2a960cb5f91439556068b8127512a.webp?size=128",
        )
        embed1.set_image(url="attachment://image.png")
        embed1.description = l
        await ctx.send(file=file, embed=embed1)

    @is_admin()
    @commands.command(
        usage="https://akashi.readthedocs.io/en/stable/Info/allstaff.html"
    )
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

        Arguments
        ===========

        Optional
        ------------


        Related Articles:
        ^^^^^^^^^^^^^^^^^^^^

        """
        session = ctx.session
        staff = await get_all(session, select(Staff))
        embed = discord.Embed(colour=discord.Colour.purple())
        embed.add_field(
            name="\u200b",
            value=("**ID\n**" + ("\n".join(str(person.id) for person in staff))),
            inline=True,
        )
        embed.add_field(
            name="\u200b",
            value=("**Name\n**" + ("\n".join(person.name for person in staff))),
            inline=True,
        )
        embed.add_field(
            name="\u200b",
            value=(
                "**Discord ID\n**"
                + (
                    "\n".join(
                        f"{person.discord_id}: {person.status}" for person in staff
                    )
                )
            ),
            inline=True,
        )
        await ctx.send(embed=embed)

    @commands.command(
        usage="https://akashi.readthedocs.io/en/stable/Info/mycurrent.html"
    )
    async def mycurrent(self, ctx):
        """
        Description
        ==============
        Get info on projects you are currently working on.

        .. caution::
           Doesn't take any arguments.

        Required Role
        =====================
        Role `Neko Workers`.

        Arguments
        ===========

        Optional
        ------------

        Related Articles:
        ^^^^^^^^^^^^^^^^^^^^

        """
        session = ctx.session
        ts_alias = aliased(Staff)
        rd_alias = aliased(Staff)
        tl_alias = aliased(Staff)
        pr_alias = aliased(Staff)
        query = (
            select(Chapter)
            .outerjoin(ts_alias, Chapter.typesetter_id == ts_alias.id)
            .outerjoin(rd_alias, Chapter.redrawer_id == rd_alias.id)
            .outerjoin(tl_alias, Chapter.translator_id == tl_alias.id)
            .outerjoin(pr_alias, Chapter.proofreader_id == pr_alias.id)
            .join(Project, Chapter.project_id == Project.id)
        )
        typ = await searchstaff(str(ctx.message.author.id), ctx, session)
        to_tl = await get_all(
            session,
            (
                query.filter(Chapter.translator == typ).filter(
                    Chapter.link_tl.is_(None)
                )  # type: ignore
            ),
        )
        to_rd = await get_all(
            session,
            (
                query.filter(Chapter.redrawer == typ).filter(
                    Chapter.link_rd.is_(None)
                )  # type: ignore
            ),
        )
        to_ts = await get_all(
            session,
            (
                query.filter(Chapter.typesetter == typ).filter(
                    Chapter.link_ts.is_(None)
                )  # type: ignore
            ),
        )
        to_pr = await get_all(
            session,
            (
                query.filter(Chapter.proofreader == typ).filter(
                    Chapter.link_pr.is_(None)
                )  # type: ignore
            ),
        )
        to_qcts = await get_all(
            session,
            (
                query.filter(Chapter.typesetter == typ)
                .filter(or_(Chapter.link_rl == None, Chapter.link_rl == ""))
                .filter(Chapter.link_pr != None, Chapter.link_pr != "")
                .filter(Chapter.link_ts != None, Chapter.link_ts != "")
            ),
        )
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
        embed.set_author(name="Current chapters", icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @commands.command(usage="https://akashi.readthedocs.io/en/stable/Info/current.html")
    async def current(self, ctx, member: discord.Member):
        """
        Description
        ==============
        See what the given staffmember is currently working on.

        Required Role
        =====================
        Role `Neko Workers`.

        Arguments
        ===========

        Required
        ------------
        :Member: The person to look for.

        .. danger::
            Doesn't use the "normal" way to do commands. Just write the member's name `directly` after the command name like so:

            `$current lukesaltweather`

        Related Articles:
        ^^^^^^^^^^^^^^^^^^^^

        """
        session = ctx.session
        ts_alias = aliased(Staff)
        rd_alias = aliased(Staff)
        tl_alias = aliased(Staff)
        pr_alias = aliased(Staff)
        query = (
            select(Chapter)
            .outerjoin(ts_alias, Chapter.typesetter_id == ts_alias.id)
            .outerjoin(rd_alias, Chapter.redrawer_id == rd_alias.id)
            .outerjoin(tl_alias, Chapter.translator_id == tl_alias.id)
            .outerjoin(pr_alias, Chapter.proofreader_id == pr_alias.id)
            .join(Project, Chapter.project_id == Project.id)
        )
        typ = await searchstaff(str(member.id), ctx, session)
        to_tl = await get_all(
            session,
            (
                query.filter(Chapter.translator == typ).filter(
                    Chapter.link_tl.is_(None)
                )  # type: ignore
            ),
        )
        to_rd = await get_all(
            session,
            (
                query.filter(Chapter.redrawer == typ).filter(
                    Chapter.link_rd.is_(None)
                )  # type: ignore
            ),
        )
        to_ts = await get_all(
            session,
            (
                query.filter(Chapter.typesetter == typ).filter(
                    Chapter.link_ts.is_(None)
                )  # type: ignore
            ),
        )
        to_pr = await get_all(
            session,
            (
                query.filter(Chapter.proofreader == typ).filter(
                    Chapter.link_pr.is_(None)
                )  # type: ignore
            ),
        )
        to_qcts = await get_all(
            session,
            (
                query.filter(Chapter.typesetter == typ)
                .filter(or_(Chapter.link_rl == None, Chapter.link_rl == ""))
                .filter(Chapter.link_pr != None, Chapter.link_pr != "")
                .filter(Chapter.link_ts != None, Chapter.link_ts != "")
            ),
        )
        desc = ""
        if len(to_tl) != 0:
            desc = "`To translate:` "
            for chapter in to_tl:
                desc = f"{desc}\n[{chapter.project.title} {format_number(chapter.number)}]({chapter.link_raw})"
        if len(to_rd) != 0:
            desc = f"{desc}\n`To redraw:`"
            for chapter in to_rd:
                desc = f"{desc}\n[{chapter.project.title} {format_number(chapter.number)}]({chapter.link_raw})"
        if len(to_ts) != 0:
            desc = f"{desc}\n`To typeset:`"
            for chapter in to_ts:
                desc = f"{desc}\n{chapter.project.title} {format_number(chapter.number)}: [RD]({chapter.link_rd}) [TL]({chapter.link_tl})"
        if len(to_pr) != 0:
            desc = f"{desc}\n`To proofread:`"
            for chapter in to_pr:
                desc = f"{desc}\n{chapter.project.title} {format_number(chapter.number)}: [TS]({chapter.link_ts}) [TL]({chapter.link_tl})"
        if len(to_qcts) != 0:
            desc = f"{desc}\n`To qcts:`"
            for chapter in to_qcts:
                desc = f"{desc}\n{chapter.project.title} {chapter.number}: [TS]({chapter.link_ts}) [PR]({chapter.link_pr})"
        embed = discord.Embed(color=discord.Colour.gold(), description=desc)
        embed.set_author(
            name=f"{member.display_name}'s current chapters",
            icon_url=member.display_avatar.url,
        )
        await ctx.send(embed=embed)


def setup(Bot):
    Bot.add_cog(Info(Bot))
