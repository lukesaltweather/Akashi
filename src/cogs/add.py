import asyncio
import json

import discord
from discord.ext import commands

from src.util.context import CstmContext
from src.util.exceptions import MissingRequiredParameter
from prettytable import PrettyTable
from sqlalchemy import func
from src.model.chapter import Chapter
from src.model.project import Project
from src.model.staff import Staff
from src.util import exceptions, misc
from src.util.flags.addflags import AddStaffFlags, AddProjectFlags, AddChapterFlags, MassAddFlags
from src.util.search import searchproject, searchstaff
from src.util.misc import formatNumber
from src.util.checks import is_admin

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


    @commands.command()
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
        member =  flags.member
        st = Staff(member.id, member.name)
        ctx.session.add(st)
        await ctx.send("Successfully added {} to staff. ".format(member.name))

    @commands.command(aliases=["ap", "addp", "addproj"])
    @is_admin()
    async def addproject(self, ctx, *, flags: AddProjectFlags):
        """
        Description
        ==============
        Add a project to the database.

        Required Role
        =====================
        Role `Neko Herder`.

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
            raise discord.ext.commands.CommandError(f"Project {flags.title} already exists.")

        pr = Project(flags.title, flags.status, flags.link, flags.altnames)
        pr.tl = flags.tl
        pr.rd = flags.rd
        pr.ts = flags.ts
        pr.pr = flags.pr
        pr.icon = flags.icon
        pr.thumbnail = flags.thumbnail
        session.add(pr)

    @commands.command(aliases=["mac", "massaddchapters", "addchapters", 'bigmac'], description=jsonhelp["massaddchapter"]["description"],
                      usage=jsonhelp["massaddchapter"]["usage"], brief=jsonhelp["massaddchapter"]["brief"], help=jsonhelp["massaddchapter"]["help"])
    async def massaddchapter(self, ctx: CstmContext, *, flags: MassAddFlags):
        start_chp = flags.chapter
        date_created = func.now()
        project = flags.project
        session = ctx.session

        message = await ctx.send('Please paste the links, with one link per line.')

        def check(message):
            return message.author == ctx.message.author and message.channel == ctx.channel

        try:
            message2 = await self.bot.wait_for('message', timeout=30.0, check=check)
        except asyncio.TimeoutError:
            await message.edit(content='No reaction from command author. Chapters was not added.')
        else:
            content = message2.content.split('\n')
            for i, link in enumerate(content, start_chp):
                chp = Chapter(i, link)
                chp.date_created = date_created
                chp.project = project
                session.add(chp)
            await ctx.send(f'Successfully added {str(len(content))} chapters of `{project.title}`!')

    @commands.command(aliases=["ac", "addch", "addc"], description=jsonhelp["addchapter"]["description"],
                      usage=jsonhelp["addchapter"]["usage"], brief=jsonhelp["addchapter"]["brief"], help=jsonhelp["addchapter"]["help"])
    async def addchapter(self, ctx: CstmContext, *, flags: AddChapterFlags):
        table = PrettyTable()
        chp = Chapter(flags.chapter, flags.raws)
        chp.project = flags.project
        table.add_column("Project", [chp.project.title])
        table.add_column("Chapter", [formatNumber(flags.chapter)])
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
            ctx.session.rollback()
        else:
            if str(reaction.emoji) == "✅":
                num = formatNumber(chp.number)
                await ctx.channel.send(f'Sucessfully added {chp.project.title} {num} to chapters.')
                ctx.session.commit()
                await message.clear_reactions()
            else:
                await message.delete()
                await ctx.channel.send('Action cancelled by user.')
                ctx.session.rollback()
                await message.clear_reactions()

def setup(Bot):
    Bot.add_cog(Add(Bot))