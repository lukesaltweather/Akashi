import asyncio
import json

import asyncpg.exceptions
import discord
import sqlalchemy
from discord.ext import commands

from src.util.context import CstmContext
from src.util.exceptions import ProjectAlreadyExists, ChapterAlreadyExists
from prettytable import PrettyTable
from sqlalchemy import func
from src.model.chapter import Chapter
from src.model.project import Project
from src.model.staff import Staff
from src.util import exceptions, misc
from src.util.flags.addflags import (
    AddStaffFlags,
    AddProjectFlags,
    AddChapterFlags,
    MassAddFlags,
)
from src.util.search import searchproject, searchstaff
from src.util.misc import format_number
from src.util.checks import is_admin, is_pu


class Add(commands.Cog):
    """
    Cog with all of the commands used for adding to the database
    """

    def __init__(self, client):
        self.bot = client

    @commands.command(usage="https://akashi.readthedocs.io/en/stable/Add/addstaff.html")
    @is_admin()
    async def addstaff(self, ctx: CstmContext, *, flags: AddStaffFlags):
        """
        Description
        ==============
        Add a staffmember to the database.

        Required Role
        =====================
        Role `Neko Herder`.

        Parameters
        ===========
        :member: The Member to be added by Mention, ID, or Name
        """
        member = flags.member
        st = Staff(member.id, member.name)
        ctx.session.add(st)
        await ctx.session.commit()
        await ctx.send("Successfully added {} to staff. ".format(member.name))

    @commands.command(
        aliases=["ap", "addp", "addproj"],
        usage="https://akashi.readthedocs.io/en/stable/Add/addproject.html",
    )
    @is_pu()
    async def addproject(self, ctx: CstmContext, *, flags: AddProjectFlags):
        """
        Description
        ==============
        Add a project to the database.

        Required Role
        =====================
        Role `Akashi's Minions`.

        Parameters
        ===========
        Required
        ---------
        :title: Title of the Project.
        :link: Link to the project on box.
        :thumbnail: Large picture for the entry in the status board.

        Optional
        ------------
        :icon: Small Image for the status board in the upper left corner.
        :ts, rd, pr, tl: Default staff for the project.
        :status: Current status of the project, defaults to "active".
        :altnames: Aliases for the project, divided by comma.
        """
        session = ctx.session
        if searchproject(flags.title, session):
            raise ProjectAlreadyExists()

        pr = Project(flags.title, flags.status, flags.link, flags.altnames)
        pr.tl = flags.tl
        pr.rd = flags.rd
        pr.ts = flags.ts
        pr.pr = flags.pr
        pr.icon = flags.icon
        pr.thumbnail = flags.thumbnail  # type: ignore
        session.add(pr)
        await ctx.prompt_and_commit(
            embed=discord.Embed(
                title=f"Do you really want to add the project {pr.title}"
            )
        )

    @commands.command(
        aliases=["mac", "massaddchapters", "addchapters", "bigmac"],
        usage="https://akashi.readthedocs.io/en/stable/Add/massaddchapters.html",
    )
    @is_pu()
    async def massaddchapter(self, ctx: CstmContext, *, flags: MassAddFlags):
        """
        Description
        ==============
        Add multiple chapters at once.

        Required Role
        =====================
        Role `Neko Workers`.

        Example
        ========
        .. image:: /images/bigmac.png
          :width: 400
          :alt: bigmac Example


        Parameters
        ===========
        Required
        ---------
        :chapter: Chapter on which to start on. Chapter to end on is determined by amount of links sent.
        :project: Project the chapters belong to.
        """
        start_chp = flags.chapter
        date_created = func.now()
        project = flags.project
        session = ctx.session

        message = await ctx.send("Please paste the links, with one link per line.")

        def check(message):
            return (
                message.author == ctx.message.author and message.channel == ctx.channel
            )

        try:
            message2 = await self.bot.wait_for("message", timeout=30.0, check=check)
        except asyncio.TimeoutError:
            await message.edit(
                content="No reaction from command author. Chapters was not added."
            )
        else:
            content = message2.content.split("\n")
            for i, link in enumerate(content, start_chp):
                chp = Chapter(i, link)
                chp.date_created = date_created
                chp.project = project
                session.add(chp)
            await ctx.send(
                f"Successfully added {str(len(content))} chapters of `{project.title}`!"
            )
            await session.commit()

    @commands.command(
        aliases=["ac", "addch", "addc"],
        usage="https://akashi.readthedocs.io/en/stable/Add/addchapter.html",
    )
    async def addchapter(self, ctx: CstmContext, *, flags: AddChapterFlags):
        """
        Description
        ==============
        Add a project to the database.

        Required Role
        =====================
        Role `Akashi's Minions`.

        Parameters
        ===========
        Required
        ---------
        :chapter: Project and chapter number of the chapter to add.
        :raws: Link to raws on Box.

        Optional
        ------------
        :tl, rd, ts, pr: Staff for the chapter.
        """
        arg = flags.chapter
        project_str = arg[0: len(arg) - len(arg.split(' ')[-1])]
        chapter_nbr = float(arg.split(' ')[-1])

        table = PrettyTable()
        chp = Chapter(chapter_nbr, flags.raws)
        chp.project = await Project.convert(ctx, project_str)
        table.add_column("Project", [chp.project.title])
        table.add_column("Chapter", [format_number(chp.number)])
        table.add_column("Raws", [chp.link_raw])
        if flags.ts:
            chp.typesetter = flags.ts
            table.add_column(fieldname="Typesetter", column=[chp.typesetter.name])
        if flags.rd:
            chp.redrawer = flags.rd
            table.add_column(fieldname="Redrawer", column=[chp.redrawer.name])
        if flags.pr:
            chp.proofreader = flags.pr
            table.add_column(fieldname="Proofreads", column=[chp.proofreader.name])
        if flags.tl:
            chp.translator = flags.tl
            table.add_column(fieldname="Translation", column=[chp.translator.name])
        chp.date_created = func.now()
        ctx.session.add(chp)
        t = table.get_string(title="Chapter Preview")
        await ctx.prompt_and_commit(file=await misc.drawimage(t))

    @addchapter.error
    async def on_chapter_error(self, ctx, error):
        if isinstance(error.original, sqlalchemy.exc.IntegrityError):
            await ctx.send("Chapter couldn't be added, as it already exists.")

def setup(Bot):
    Bot.add_cog(Add(Bot))
