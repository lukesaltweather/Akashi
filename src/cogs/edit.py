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
from src.util.checks import is_admin

from src.util.flags.editflags import EditStaffFlags, EditChapterFlags, EditProjectFlags, ReleaseFlags

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
    async def editchapter(self, ctx, *, flags: EditChapterFlags):
        session = ctx.session
        async with ctx.channel.typing():
            record = flags.chapter
            table = PrettyTable()
            table.add_column("", ["ORIGINAL", "EDIT"])

            if flags.title:
                if flags.title in ("None", "none"):
                    table.add_column("Title", [record.title, ""])
                    record.title = None
                else:
                    table.add_column("Title", [record.title, flags.title])
                    record.title = flags.title
            if flags.tl:
                tl = flags.tl
                if tl in ("None", "none"):
                    table.add_column("Translator", [record.translator.name, "None"])
                    record.translator = None
                else:
                    table.add_column("Translator", [record.translator.name, tl.name])
                    record.translator = tl
            if flags.rd:
                rd = flags.rd
                if rd in ("None", "none"):
                    table.add_column("Redrawer", [record.redrawer, "None"])
                    record.redrawer = None
                else:
                    table.add_column("Redrawer", [record.redrawer.name, rd.name])
                    record.redrawer = rd
            if flags.ts:
                ts = flags.ts
                if ts in ("None", "none"):
                    table.add_column("Typesetter", [record.typesetter.name, "None"])
                    record.typesetter = None
                else:
                    table.add_column("Typesetter", [record.typesetter.name, ts.name])
                    record.typesetter = ts
            if flags.pr:
                pr = flags.pr
                if pr in ("None", "none"):
                    table.add_column("Proofreader", [record.proofreader.name, "None"])
                    record.proofreader = None
                else:
                    table.add_column("Proofreader", [record.proofreader.name, pr.name])
                    record.proofreader = pr
            if flags.link_ts:
                table.add_column("Link TS", [record.link_ts, flags.link_ts])
                if flags.link_ts in ("None", "none"):
                    record.link_ts = None
                else:
                    record.link_ts = flags.link_ts
            if flags.link_tl:
                table.add_column("Link TL", [record.link_tl, flags.link_tl])
                if flags.link_tl in ("None", "none"):
                    record.link_tl = None
                else:
                    record.link_tl = flags.link_tl
            if flags.link_rd:
                table.add_column("Link RD", [record.link_rd, flags.link_rd])
                if flags.link_rd in ("None", "none"):
                    record.link_rd = None
                else:
                    record.link_rd = flags.link_rd
            if flags.link_pr:
                table.add_column("Link PR", [record.link_pr, flags.link_pr])
                if flags.link_pr in ("None", "none"):
                    record.link_pr = None
                else:
                    record.link_pr = flags.link_pr
            if flags.link_qcts:
                table.add_column("Link QCTS", [record.link_rl, flags.link_qcts])
                if flags.link_qcts in ("None", "none"):
                    record.link_rl = None
                else:
                    record.link_rl = flags.link_qcts
            if flags.link_raw:
                table.add_column("Link Raw", [record.link_raw, flags.link_raw])
                if flags.link_raw in ("None", "none"):
                    record.link_raw = None
                else:
                    record.link_raw = flags.link_raw
            if flags.to_project:
                proj = flags.to_project
                table.add_column("New Project", [record.project.title, proj.title])
                record.project = proj
            if flags.to_chapter:
                table.add_column("New Ch. Number", [record.number, flags.to_chapter])
                record.number = flags.to_chapter
            if flags.notes:
                record.notes = flags.notes
                table.add_column("Notes", [record.notes, flags.notes])
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

    @commands.command(aliases=["editproj", "editp", "ep"],description=jsonhelp["editproject"]["description"],
                      usage=jsonhelp["editproject"]["usage"], brief=jsonhelp["editproject"]["brief"], help=jsonhelp["editproject"]["help"])
    @is_admin()
    async def editproject(self, ctx, *, flags: EditProjectFlags):
        session = ctx.session
        record = flags.project
        table = PrettyTable()
        table.add_column("", ["ORIGINAL", "EDIT"])
        if flags.title:
            table.add_column("Title", [record.title, flags.title])
            record.title = flags.title
        if flags.status:
            table.add_column("Status", [record.status, flags.status])
            record.status = flags.status
        if flags.color:
            if isinstance(flags.color, str):
                record.color = None
                table.add_column("Color", [record.color, "None"])
            else:
                table.add_column("Color", [record.color, flags.color])
                record.color = str(flags.color)[1:]
        if flags.position:
            if flags.position in ("None", "none"):
                table.add_column("Pos", [record.position, "None"])
                record.position = None
            else:
                table.add_column("Pos", [record.position, flags.position])
                record.position = flags.position
        if flags.tl:
            tl = flags.tl
            if tl in ("None", "none"):
                table.add_column("Translator", [record.translator.name, "None"])
                record.translator = None
            else:
                table.add_column("Translator", [record.translator.name, tl.name])
                record.translator = tl
        if flags.rd:
            rd = flags.rd
            if rd in ("None", "none"):
                table.add_column("Redrawer", [record.redrawer, "None"])
                record.redrawer = None
            else:
                table.add_column("Redrawer", [record.redrawer.name, rd.name])
                record.redrawer = rd
        if flags.ts:
            ts = flags.ts
            if ts in ("None", "none"):
                table.add_column("Typesetter", [record.typesetter.name, "None"])
                record.typesetter = None
            else:
                table.add_column("Typesetter", [record.typesetter.name, ts.name])
                record.typesetter = ts
        if flags.pr:
            pr = flags.pr
            if pr in ("None", "none"):
                table.add_column("Proofreader", [record.proofreader.name, "None"])
                record.proofreader = None
            else:
                table.add_column("Proofreader", [record.proofreader.name, pr.name])
                record.proofreader = pr
        if flags.altnames:
            table.add_column("AltNames", [record.altNames, flags.altnames])
            record.altNames = flags.altnames
        if flags.thumbnail:
            table.add_column("Thumbnail", [record.thumbnail, flags.thumbnail])
            record.thumbnail = flags.thumbnail
        if flags.icon:
            table.add_column("Icon", [record.icon, flags.icon])
            record.icon = flags.icon
        if flags.link:
            table.add_column("Link", [record.link, flags.link])
            record.link = flags.link
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


    @commands.command(description=jsonhelp["editstaff"]["description"],
                      usage=jsonhelp["editstaff"]["usage"], brief=jsonhelp["editstaff"]["brief"], help=jsonhelp["editstaff"]["help"])
    @is_admin()
    @commands.max_concurrency(1, per=discord.ext.commands.BucketType.default, wait=True)
    async def editstaff(self, ctx, *, flags: EditStaffFlags):
        member = flags.member
        if flags.id:
            member.discord_id = flags.id
        if flags.name:
            member.name = flags.name
        if flags.status:
            member.status = flags.status
        await ctx.message.add_reaction("👍")

    @commands.command(description=jsonhelp["release"]["description"],
                      usage=jsonhelp["release"]["usage"], brief=jsonhelp["release"]["brief"], help=jsonhelp["release"]["help"])
    async def release(self, ctx, *, flags: ReleaseFlags):
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