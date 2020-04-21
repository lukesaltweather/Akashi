import json

import discord
from discord.ext import commands
from sqlalchemy import func
from sqlalchemy.orm import aliased
from src.util.exceptions import MissingRequiredParameter
from src.model.chapter import Chapter
from src.model.message import Message
from src.model.project import Project
from src.model.staff import Staff
from src.util import exceptions
from src.util.search import searchproject, searchstaff, fakesearch
from src.util.misc import FakeUser, formatNumber, make_mentionable, toggle_mentionable, strx

with open('src/util/help.json', 'r') as f:
    jsonhelp = json.load(f)


class Note(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    async def cog_check(self, ctx):
        worker = ctx.guild.get_role(self.bot.config["neko_workers"])
        ia = worker in ctx.message.author.roles
        ic = ctx.channel.id == self.bot.config["command_channel"]
        guild = ctx.guild is not None
        if ia and ic and guild:
            return True
        elif ic:
            raise exceptions.MissingRequiredPermission("Missing permission `Neko Worker`.")
        elif not guild:
            raise exceptions.MissingRequiredPermission("Missing permission `Server Member`.")


    @commands.command(aliases=["an"], description=jsonhelp["addnote"]["description"],
                      usage=jsonhelp["addnote"]["usage"], brief=jsonhelp["addnote"]["brief"], help=jsonhelp["addnote"]["help"])
    async def addnote(self, ctx, *, arg):
        session = self.bot.Session()
        try:
            arg = arg[1:]
            d = dict(x.split('=', 1) for x in arg.split(' -'))
            if "p" in d and "c" in d and "note" in d:
                query = session.query(Chapter)
                proj = searchproject(d["p"], session)
                record = query.filter(Chapter.project_id == proj.id).filter(Chapter.number == int(d["c"])).one()
                record.notes = strx(record.notes)+("{}\n".format(d["note"]))
                await ctx.message.add_reaction("👍")
                session.commit()
        finally:
            session.close()


    @commands.command(aliases=["n", "notes"],description=jsonhelp["note"]["description"],
                      usage=jsonhelp["note"]["usage"], brief=jsonhelp["note"]["brief"], help=jsonhelp["note"]["help"])
    async def note(self, ctx, *, arg):
        session = self.bot.Session()
        try:
            arg = arg[1:]
            d = dict(x.split('=', 1) for x in arg.split(' -'))
            proj = searchproject(d["p"], session)
            note = session.query(Chapter).filter(proj.id == Chapter.project_id).filter(Chapter.number == int(d["c"])).one()
            await ctx.send(note.notes)
        finally:
            session.close()

def setup(Bot):
    Bot.add_cog(Note(Bot))