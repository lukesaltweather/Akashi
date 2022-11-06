import asyncio

import discord.ext.commands as commands
import sqlalchemy
from prettytable import PrettyTable, prettytable
from sqlalchemy import func

from Akashi.model.chapter import Chapter
from Akashi.model.project import Project
from Akashi.model.staff import Staff
from Akashi.util import misc
from Akashi.util.checks import is_admin, is_pu
from Akashi.util.context import CstmContext
from Akashi.util.exceptions import ProjectAlreadyExists
from Akashi.util.flags.addflags import (
    AddStaffFlags,
    AddProjectFlags,
    AddChapterFlags,
    MassAddFlags,
)
from Akashi.util.misc import format_number
from Akashi.util.search import searchproject


class Add(commands.GroupCog, name="add"):
    """
    Cog with all of the commands used for adding to the database
    """

    def __init__(self, client):
        self.bot = client
        super().__init__()

    @commands.command()
    @is_admin()
    async def staff(self, ctx: CstmContext, *, flags: AddStaffFlags):
        """
        Description
        ==============
        Add a staffmember to the database.

        Required Role
        =====================
        Role `Neko Herder`.

        Arguments
        ===========
        :member:
            | The Member to be added by Mention, ID, or Name  [:doc:`/Types/discord`]
        """
        member = flags.member
        st = Staff(member.id, member.name)
        ctx.session.add(st)
        await ctx.session.commit()
        await ctx.reply(f"Successfully added {st.name} to staff. ")
        await ctx.success()

    @commands.command(
        aliases=["ap", "addp", "addproj"],
    )
    @is_pu()
    async def project(self, ctx: CstmContext, *, flags: AddProjectFlags):
        """
        Description
        ==============
        Add a project to the database.

        Required Role
        =====================
        Role `Akashi's Minions`.

        Arguments
        ===========
        Required
        ---------
        :title:
            | Title of the Project. [:doc:`/Types/text`]
        :link:
            | Link to the project on box. [:doc:`/Types/text`]
        :thumbnail:
            | Link to large picture for the entry in the status board.  [:doc:`/Types/text`]

        Optional
        ------------
        :icon:
            | Link to small Image for the status board in the upper left corner.  [:doc:`/Types/text`]
        :ts, rd, pr, tl:
            | Default staff for the project.  [:doc:`/Types/staff`]
        :status:
            | Current status of the project, defaults to "active".  [:doc:`/Types/text`]
        :altnames:
            | Aliases for the project, divided by comma.  [:doc:`/Types/text`]
        """
        session = ctx.session

        pr = Project(flags.title, flags.status, flags.link, flags.altnames)
        pr.tl = flags.tl
        pr.rd = flags.rd
        pr.ts = flags.ts
        pr.pr = flags.pr
        pr.icon = flags.icon
        pr.thumbnail = flags.thumbnail  # type: ignore
        session.add(pr)
        await ctx.prompt_and_commit(
            text=f"Do you really want to add the project {pr.title}"
        )

    @commands.command(
        aliases=["mac", "massaddchapters", "addchapters", "bigmac"],
    )
    @is_pu()
    async def massaddchapter(self, ctx: CstmContext, *, flags: MassAddFlags):
        """
        Description
        ==============
        Add multiple chapters at once.
        After entering the command, you are expected to post links to the raws of the chapters.
        Each link must be on its own line.

        Required Role
        =====================
        Role `Neko Workers`.

        Example
        ========
        .. image:: /images/bigmac.png
          :width: 400
          :alt: bigmac Example


        Arguments
        ===========
        Required
        ---------
        :chapter:
            | Chapter on which to start on. Chapter to end on is determined by amount of links sent.  [:doc:`/Types/chapter`]
        :project:
            | Project the chapters belong to.  [:doc:`/Types/project`]
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
            return
        else:
            content = message2.content.split("\n")
            chapters = []
            for i, link in enumerate(content, start_chp):
                chp = Chapter(i, link)
                chp.date_created = date_created
                session.add(chp)
                chp.project = project
                chapters.append(chp)

        # prompt user to confirm
        table = prettytable.PrettyTable(["Chapter", "Link"])
        for chp in chapters:
            table.add_row([chp.number, chp.link_raw])
        image = await misc.drawimage(table.get_string())
        await ctx.prompt_and_commit(
            text=f"Do you really want to add these chapters to project {project.title}?",
            file=image,
        )

    @is_pu()
    @commands.command(
        aliases=["ac", "addch", "addc"],
    )
    async def chapter(self, ctx: CstmContext, *, flags: AddChapterFlags):
        """
        Description
        ==============
        Add a chapter to the database.

        Required Role
        =====================
        Role `Akashi's Minions`.

        Arguments
        ===========
        Required
        ---------
        :chapter:
            | Project and chapter number of the chapter to add.  [:doc:`/Types/chapter`]
        :raws:
            | Link to raws on Box.  [:doc:`/Types/text`]

        Optional
        ------------
        :tl, rd, ts, pr:
            | Staff for the chapter.  [:doc:`/Types/staff`]
        """
        arg = flags.chapter
        project_str = arg[0 : len(arg) - len(arg.split(" ")[-1])]
        chapter_nbr = float(arg.split(" ")[-1])

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
        await ctx.prompt_and_commit(
            text="Do you really want to add this chapter?",
            file=await misc.drawimage(t),
        )

    @chapter.error
    async def on_chapter_error(self, ctx, error):
        if isinstance(error.original, sqlalchemy.exc.IntegrityError):
            await ctx.send("Chapter couldn't be added, as it already exists.")
        else:
            await ctx.send(f"An error occured while adding the chapter: {error}")


async def setup(Bot):
    await Bot.add_cog(Add(Bot))
