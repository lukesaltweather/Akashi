import json

import discord
from discord.ext import commands
from sqlalchemy import func
from sqlalchemy.orm import aliased

from src.util.context import CstmContext
from src.util.exceptions import MissingRequiredParameter
from src.model.chapter import Chapter
from src.model.message import Message
from src.model.project import Project
from src.model.staff import Staff
from src.util import exceptions
from src.util.search import searchproject, searchstaff, fakesearch
from src.util.misc import (
    FakeUser,
    format_number,
    make_mentionable,
    toggle_mentionable,
    strx,
)


class Note(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["an"])
    async def addnote(self, ctx: CstmContext, *, arg):
        session = self.bot.Session()
        query = session.query(Chapter)
        proj = searchproject(d["p"], session)
        record = (
            query.filter(Chapter.project_id == proj.id)
            .filter(Chapter.number == int(d["c"]))
            .one()
        )
        record.notes = strx(record.notes) + ("{}\n".format(d["note"]))
        await ctx.message.add_reaction("👍")
        session.commit()

    @commands.command()
    async def note(self, ctx, *, arg):
        session = self.bot.Session()
        try:
            arg = arg[1:]
            d = dict(x.split("=", 1) for x in arg.split(" -"))
            proj = searchproject(d["p"], session)
            note = (
                session.query(Chapter)
                .filter(proj.id == Chapter.project_id)
                .filter(Chapter.number == int(d["c"]))
                .one()
            )
            await ctx.send(note.notes)
        finally:
            session.close()


def setup(Bot):
    Bot.add_cog(Note(Bot))
