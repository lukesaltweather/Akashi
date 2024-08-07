import discord
import prettytable
from discord.ext import commands
from prettytable import PrettyTable
from sqlalchemy import Date, or_, and_
from sqlalchemy.sql.expression import select

from Akashi.model.chapter import Chapter
from Akashi.model.monitor import MonitorRequest
from Akashi.model.project import Project
from Akashi.model.staff import Staff
from Akashi.util.arghelper import arghelper
from Akashi.util.checks import is_admin
from Akashi.util.context import CstmContext
from Akashi.util.db import get_all
from Akashi.util.flags.infoflags import InfoChapter, InfoProject, MonitorFlags
from Akashi.util.misc import (
    drawimage,
    format_number,
    BoardPaginator,
    MISSING,
)
from Akashi.util.search import searchstaff


class Info(commands.Cog):
    def __init__(self, client):
        self.bot = client

    @commands.command(
        aliases=["infochapters", "ic", "infoc"],
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
        :project:
            | List of projects the chapters can belong to. [:doc:`/Types/project`]
        :tl, rd, ts, pr, qc:
            | List of staff working on respective steps. [:doc:`/Types/staff`]
        :chapter_from, chapter_upto:
            | Give a minimum and/or maximum chapter number to look for. [:doc:`/Types/number`]
        :chapter:
            | A list of numbers the found chapters can have. [:doc:`/Types/number`]
        :id:
            | A list of ids the found chapters can have. [:doc:`/Types/number`]
        :release_from, release_upto, release_on:
            | Filter for release Date. [:doc:`/Types/datetime`]
        :status:
            | Current status of the chapter. Can be one of "active", "tl", "ts", "rd", "pr", "qcts" or "ready". [:doc:`/Types/literals`]
        :fields:
            |  What columns to include in the result table.
             Can be one of "link_tl" ("link_ts", "link_rd", ..),"date", "date_tl", .., "date_rl", "tl", "ts", "rd", "pr", "qcts" or "ready". [:doc:`/Types/literals`]
        :links:
            | Either true or false, whether the bot sends the links to each steps of the chapters. [:doc:`/Types/text`]

        Related Articles:
        ^^^^^^^^^^^^^^^^^^^^

        You can find a tutorial on how to pass a list of arguments here:
        :doc:`/Tutorials/ParamListTut`
        """
        session = ctx.session
        async with ctx.channel.typing():
            query = select(Chapter).join(Project)
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
                conds = list()
                for arg in flags.ts:
                    conds.append(Chapter.typesetter == arg)
                query = query.filter(or_(*conds))
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
            embed = BoardPaginator()
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
            await ctx.success()
            if flags.links:
                await ctx.reply(file=file, embeds=[embed1, *embed.embeds])
            else:
                await ctx.reply(file=file, embed=embed1)

    @commands.hybrid_command(
        name="infoproject",
        aliases=["infoprojects", "infop", "ip"],
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
        :status:
            | Filter by current status of the project.
        :tl, rd, ts, pr:
            | Filter by Staff working on project.
        :project:
            | Filter by name.
        :fields:
            | What columns to include in the result table.

        Related Articles:
        ^^^^^^^^^^^^^^^^^^^^

        You can find a list of possible fields here:
        :doc:`/Tutorials/Fields`
        """
        session = ctx.session
        query = select(Project)  # .join(Chapter)

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
            query = query.filter(Project.typesetter == flags.ts)
        if flags.rd is not MISSING:
            query = query.filter(Project.redrawer == flags.rd)
        if flags.tl is not MISSING:
            query = query.filter(Project.translator == flags.tl)
        if flags.pr is not MISSING:
            query = query.filter(Project.proofreader == flags.pr)
        records = await get_all(session, query)
        table = PrettyTable()
        link_embed = None
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
                        link_embed = discord.Embed(color=discord.Colour.greyple())
                        link_embed.add_field(
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
                link_embed = discord.Embed(color=discord.Colour.greyple())
                link_embed.add_field(name="Links", value="\n".join(links), inline=False)
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
        embed_results = discord.Embed(color=discord.Colour.greyple())
        embed_results.set_author(
            name="Results",
            icon_url="https://cdn.discordapp.com/icons/345797456614785024/9ef2a960cb5f91439556068b8127512a.webp?size=128",
        )
        embed_results.set_image(url="attachment://image.png")
        if link_embed:
            await ctx.reply(file=file, embeds=[embed_results, link_embed])
        else:
            await ctx.reply(file=file, embed=embed_results)

    @commands.command()
    async def allprojects(self, ctx):
        """
        Description
        ==============
        Return a list of all project.

        Required Role
        =====================
        Role `Neko Workers`.
        """
        session = ctx.session
        stmt = select(Project)
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
        await ctx.reply(file=file, embed=embed1)

    @is_admin()
    @commands.command()
    async def allstaff(self, ctx):
        """
        Description
        ==============
        Return a list of all staff members.

        Required Role
        =====================
        Role `Neko Herders`.
        """
        session = ctx.session
        staff = await get_all(session, select(Staff))
        embed = discord.Embed(
            colour=discord.Colour.purple(), title="All Existing Staff"
        )
        table = prettytable.PrettyTable()
        table.add_column("Internal ID", [str(person.id) for person in staff])
        table.add_column("Name", [person.name for person in staff])
        table.add_column("Discord ID", [f"{person.discord_id}" for person in staff])
        table.add_column("Status", [f"{person.status}" for person in staff])
        embed.set_image(url="attachment://image.png")
        file = await drawimage(table.get_string(title="All Staff"))
        await ctx.reply(embed=embed, file=file)

    @commands.command()
    async def mycurrent(self, ctx):
        """
        Description
        ==============
        Get info on chapters you are currently working on.

        .. caution::
           Doesn't take any arguments.

        Required Role
        =====================
        Role `Neko Workers`.
        """
        session = ctx.session
        query = select(Chapter)
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
                query.filter(Chapter.redrawer == typ).filter(Chapter.link_rd.is_(None))  # type: ignore
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
                .filter(or_(Chapter.link_rl.is_(None), Chapter.link_rl == ""))
                .filter(or_(Chapter.link_pr.is_not(None), Chapter.link_pr != ""))
                .filter(or_(Chapter.link_ts.is_not(None), Chapter.link_ts != ""))
            ),
        )
        desc = ""
        if to_tl:
            desc = "`To translate:` "
            for chapter in to_tl:
                desc = f"{desc}\n[{chapter.project.title} {chapter.number}]({chapter.link_raw})"
        if to_rd:
            desc = f"{desc}\n`To redraw:`"
            for chapter in to_rd:
                desc = f"{desc}\n[{chapter.project.title} {chapter.number}]({chapter.link_raw})"
        if to_ts:
            desc = f"{desc}\n`To typeset:`"
            for chapter in to_ts:
                desc = f"{desc}\n{chapter.project.title} {chapter.number}: [RD]({chapter.link_rd}) [TL]({chapter.link_tl})"
        if to_pr:
            desc = f"{desc}\n`To proofread:`"
            for chapter in to_pr:
                desc = f"{desc}\n{chapter.project.title} {chapter.number}: [TS]({chapter.link_ts}) [TL]({chapter.link_tl})"
        if to_qcts:
            desc = f"{desc}\n`To qcts:`"
            for chapter in to_qcts:
                desc = f"{desc}\n{chapter.project.title} {chapter.number}: [TS]({chapter.link_ts}) [PR]({chapter.link_pr})"
        embed = discord.Embed(color=discord.Colour.gold(), description=desc)
        embed.set_author(name="Current chapters", icon_url=ctx.author.avatar.url)
        await ctx.reply(embed=embed)

    @commands.command()
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
        :Member:
            | The person to look for.

        .. danger::
            Doesn't use the "normal" way to do commands. Just write the member's name `directly` after the command name like so:

            `$current lukesaltweather`s

        """
        session = ctx.session
        query = select(Chapter)
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
                query.filter(Chapter.redrawer == typ).filter(Chapter.link_rd.is_(None))  # type: ignore
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
        if to_tl:
            desc = "`To translate:` "
            for chapter in to_tl:
                desc = f"{desc}\n[{chapter.project.title} {format_number(chapter.number)}]({chapter.link_raw})"
        if to_rd:
            desc = f"{desc}\n`To redraw:`"
            for chapter in to_rd:
                desc = f"{desc}\n[{chapter.project.title} {format_number(chapter.number)}]({chapter.link_raw})"
        if to_ts:
            desc = f"{desc}\n`To typeset:`"
            for chapter in to_ts:
                desc = f"{desc}\n{chapter.project.title} {format_number(chapter.number)}: [RD]({chapter.link_rd}) [TL]({chapter.link_tl})"
        if to_pr:
            desc = f"{desc}\n`To proofread:`"
            for chapter in to_pr:
                desc = f"{desc}\n{chapter.project.title} {format_number(chapter.number)}: [TS]({chapter.link_ts}) [TL]({chapter.link_tl})"
        if to_qcts:
            desc = f"{desc}\n`To qcts:`"
            for chapter in to_qcts:
                desc = f"{desc}\n{chapter.project.title} {chapter.number}: [TS]({chapter.link_ts}) [PR]({chapter.link_pr})"
        embed = discord.Embed(color=discord.Colour.gold(), description=desc)
        embed.set_author(
            name=f"{member.display_name}'s current chapters",
            icon_url=member.display_avatar.url,
        )
        await ctx.success()
        await ctx.reply(embed=embed)

    @commands.command(aliases=["follow", "track", "watch"])
    async def monitor(self, ctx: CstmContext, *, flags: MonitorFlags):
        """
        Description
        ==============
        Start tracking changes to a chapter or project. When a specific chapter or one of the chapters of the given project is updated,
        a message is sent to the tracking user.

        Required Role
        =====================
        Role `$role`.

        Arguments
        ===========
        Optional
        ------------
        :chapter:
            | Singular chapter to track. [:doc:`/Types/chapter`]
        :project:
            | Project of which all chapters will be tracked. [:doc:`/Types/project`]


        Related Articles:
        ^^^^^^^^^^^^^^^^^^^^
        """
        chapter_or_project = flags.chapter or flags.project
        if (not chapter_or_project) or (flags.chapter and flags.project):
            raise commands.CommandError(
                "*One* of chapter/project arguments is required for this command."
            )

        registered_event = MonitorRequest(
            staff=await searchstaff(ctx.author.id.__str__(), ctx, ctx.session),
            chapter=flags.chapter,
            project=flags.project,
        )
        ctx.session.add(registered_event)
        await ctx.prompt_and_commit(
            text=f"Do you really want to track {chapter_or_project}?"
        )


async def setup(bot):
    await bot.add_cog(Info(bot))
