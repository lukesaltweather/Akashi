import asyncio
import json
from typing import Union, Literal

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
from src.util.checks import is_admin, is_pu

from src.util.flags.editflags import EditStaffFlags, EditChapterFlags, EditProjectFlags, ReleaseFlags

with open('src/util/help.json', 'r') as f:
    jsonhelp = json.load(f)

class Edit(commands.Cog):
    """
    Test description
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


    @commands.command(aliases=["editch", "editc", "ec"])
    @commands.max_concurrency(1, per=discord.ext.commands.BucketType.default, wait=True)
    async def editchapter(self, ctx, *, flags: EditChapterFlags):
        """
        Description
        ==============
        Edit a chapters attributes.

        Required Role
        =====================
        Role `Neko Workers`.

        Parameters
        ===========

        Required
        ---------
        :chapter: The chapter to edit, in format: projectName chapterNbr

        Optional
        ------------
        :title: Title of the chapter.
        :tl, rd, ts, pr: Staff for the chapter.
        :link_tl, link_rd, link_ts, link_pr, link_qcts, link_raw: Links to specific steps of chapter on Box.
        :to_project: Change the project the chapter belongs to.
        :to_chapter: Change the chapter number.
        :notes: Replaces all the chapters notes with this.
        """
        session = ctx.session
        async with ctx.channel.typing():
            record = flags.chapter
            if flags.title:
                if flags.title in ("None", "none"):
                    record.title = None
                else:
                    record.title = flags.title
            if flags.tl:
                tl = flags.tl
                if tl in ("None", "none"):
                    record.translator = None
                else:
                    record.translator = tl
            if flags.rd:
                rd = flags.rd
                if rd in ("None", "none"):
                    record.redrawer = None
                else:
                    record.redrawer = rd
            if flags.ts:
                ts = flags.ts
                if ts in ("None", "none"):
                    record.typesetter = None
                else:
                    record.typesetter = ts
            if flags.pr:
                pr = flags.pr
                if pr in ("None", "none"):
                    record.proofreader = None
                else:
                    record.proofreader = pr
            if flags.link_ts:
                if flags.link_ts in ("None", "none"):
                    record.link_ts = None
                else:
                    record.link_ts = flags.link_ts
            if flags.link_tl:
                if flags.link_tl in ("None", "none"):
                    record.link_tl = None
                else:
                    record.link_tl = flags.link_tl
            if flags.link_rd:
                if flags.link_rd in ("None", "none"):
                    record.link_rd = None
                else:
                    record.link_rd = flags.link_rd
            if flags.link_pr:
                if flags.link_pr in ("None", "none"):
                    record.link_pr = None
                else:
                    record.link_pr = flags.link_pr
            if flags.link_qcts:
                if flags.link_qcts in ("None", "none"):
                    record.link_rl = None
                else:
                    record.link_rl = flags.link_qcts
            if flags.link_raw:
                if flags.link_raw in ("None", "none"):
                    record.link_raw = None
                else:
                    record.link_raw = flags.link_raw
            if flags.to_project:
                proj = flags.to_project
                record.project = proj
            if flags.to_chapter:
                record.number = flags.to_chapter
            if flags.notes:
                record.notes = flags.notes
            image = await record.get_report(f"{record.project.title} {formatNumber(record.number)}")
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

    @commands.command(aliases=["editproj", "editp", "ep"])
    @is_pu()
    async def editproject(self, ctx, *, flags: EditProjectFlags):
        """
        Description
        ==============
        Edit a project's attributes.

        Required Role
        =====================
        Role `Akashi's Minions`.

        Parameters
        ===========

        Required
        ---------
        :project: The project to edit.

        Optional
        ------------
        :title: The title of the project.
        :link: Link to the project on box.
        :thumbnail: Large picture for the entry in the status board.
        :icon: Small Image for the status board in the upper left corner.
        :ts, rd, pr, tl: Default staff for the project. Enter "none" to set the staff to none at all.
        :status: Current status of the project, defaults to "active".
        :altnames: Aliases for the project, divided by comma.
        :color: The color the project's embed has in the info board. Can be a hex or one of these colors:
        :position: Where the embed of the project appears in the info board.
        """
        session = ctx.session
        record = flags.project
        if flags.title:
            record.title = flags.title
        if flags.status:
            record.status = flags.status
        if flags.color:
            if isinstance(flags.color, str):
                record.color = None
            else:
                record.color = str(flags.color)[1:]
        if flags.position:
            if flags.position in ("None", "none"):
                record.position = None
            else:
                record.position = flags.position
        if flags.tl:
            tl = flags.tl
            if tl in ("None", "none"):
                record.translator = None
            else:
                record.translator = tl
        if flags.rd:
            rd = flags.rd
            if rd in ("None", "none"):
                record.redrawer = None
            else:
                record.redrawer = rd
        if flags.ts:
            ts = flags.ts
            if ts in ("None", "none"):
                record.typesetter = None
            else:
                record.typesetter = ts
        if flags.pr:
            pr = flags.pr
            if pr in ("None", "none"):
                record.proofreader = None
            else:
                record.proofreader = pr
        if flags.altnames:
            record.altNames = flags.altnames
        if flags.thumbnail:
            record.thumbnail = flags.thumbnail
        if flags.icon:
            record.icon = flags.icon
        if flags.link:
            record.link = flags.link
        image = await record.get_report(f"{record.title}")
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


    @commands.command()
    @is_admin()
    @commands.max_concurrency(1, per=discord.ext.commands.BucketType.default, wait=True)
    async def editstaff(self, ctx, *, flags: EditStaffFlags):
        """
        Description
        ==============
        Edit a staffmembers attributes.

        Required Role
        =====================
        Role `Neko Herders`.

        Parameters
        ===========

        Required
        ---------
        :member: Staffmember to edit.

        Optional
        ------------
        :id: The staff's discord id.
        :name: The staff's username.
        :status: Can be "active" or "inactive".
        """
        member = flags.member
        if flags.id:
            member.discord_id = flags.id
        if flags.name:
            member.name = flags.name
        if flags.status:
            member.status = flags.status
        await ctx.message.add_reaction("👍")

    @commands.command()
    async def release(self, ctx, *, flags: ReleaseFlags):
        """
        Description
        ==============
        Mark a chapter as released.

        Required Role
        =====================
        Role `Neko Workers`.

        Parameters
        ===========
        Required
        ---------
        :chapter: The chapter to set as released, in format: projectName chapterNbr

        Optional
        ------------
        :date: The date on which it was finished, defaults to current date and time.
        """
        record = flags.chapter
        if flags.date:
            record.date_release = flags.date
        else:
            record.date_release = func.now()
        ctx.session.commit()
        embed = discord.Embed(color=discord.Colour.green())
        embed.set_author(name="Success!",
                         icon_url="https://cdn.discordapp.com/icons/345797456614785024/9ef2a960cb5f91439556068b8127512a.webp?size=128")
        embed.add_field(name="\u200b",
                        value=f"Releasedate of {record.project.title} {record.number} set to {record.date_release.strftime('%Y/%m/%d')}")
        await ctx.send(embed=embed)

def setup(Bot):
    Bot.add_cog(Edit(Bot))