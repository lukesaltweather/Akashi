import re

import discord
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship, backref, synonym
from sqlalchemy.sql.expression import select

from Akashi.model.ReportMixin import ReportMixin
from Akashi.model.project import Project
from Akashi.util.db import Base, get_one, get_all
from Akashi.util.misc import format_number
from Akashi.util.search import searchproject, searchprojects


class Chapter(Base, ReportMixin, discord.app_commands.Transformer):
    __tablename__ = "chapters"
    id = Column(Integer, primary_key=True)
    number = Column(Float)
    title = Column(String)
    link_raw = Column(String)
    link_tl = Column(String)
    link_ts = Column(String)
    link_rd = Column(String)
    link_pr = Column(String)
    link_rl = Column(String)
    link_qcts = synonym("link_rl")

    date_created = Column(DateTime)
    date_tl = Column(DateTime)
    date_rd = Column(DateTime)
    date_ts = Column(DateTime)
    date_pr = Column(DateTime)
    date_qcts = Column(DateTime)
    date_release = Column(DateTime)

    typesetter_id = Column(Integer, ForeignKey("staff.id", ondelete="SET NULL"))
    translator_id = Column(Integer, ForeignKey("staff.id", ondelete="SET NULL"))
    redrawer_id = Column(Integer, ForeignKey("staff.id", ondelete="SET NULL"))
    proofreader_id = Column(Integer, ForeignKey("staff.id", ondelete="SET NULL"))
    project_id = Column(Integer, ForeignKey("projects.id"))

    typesetter = relationship(
        "Staff",
        foreign_keys=[typesetter_id],
        uselist=False,
        lazy="joined",
    )
    translator = relationship(
        "Staff",
        foreign_keys=[translator_id],
        uselist=False,
        lazy="joined",
    )
    redrawer = relationship(
        "Staff",
        foreign_keys=[redrawer_id],
        uselist=False,
        lazy="joined",
    )
    proofreader = relationship(
        "Staff",
        foreign_keys=[proofreader_id],
        uselist=False,
        lazy="joined",
    )
    project = relationship(
        "Project",
        backref=backref("chapters", uselist=True, lazy="joined"),
        lazy="joined",
        foreign_keys=[project_id],
        primaryjoin="Project.id==Chapter.project_id",
    )

    def __init__(self, number, link_raw):
        self.number = number
        self.link_raw = link_raw
        self.link_tl = None
        self.link_ts = None
        self.link_rd = None
        self.link_pr = None
        self.link_rl = None

    @classmethod
    async def convert(cls, ctx, arg: str):
        chapter = float(arg.split(" ")[-1])
        proj = arg[0 : len(arg) - len(arg.split(" ")[-1])]
        proj = proj.rstrip()

        session = ctx.session
        project = await searchproject(proj, session)

        query = (
            select(Chapter)
            .filter(Chapter.project_id == project.id)
            .filter(Chapter.number == chapter)
        )
        try:
            return await get_one(ctx.session, query)
        except Exception:
            raise discord.ext.commands.BadArgument(f"{chapter} could not be found.")

    @classmethod
    async def transform(cls, interaction: discord.Interaction, value):
        async with interaction.client.Session() as session:
            chapter = float(value.split(" ")[-1])
            proj = value[0 : len(value) - len(value.split(" ")[-1])]
            proj = proj.rstrip()

            project = await searchproject(proj, session)

            query = (
                select(Chapter)
                .filter(Chapter.project_id == project.id)
                .filter(Chapter.number == chapter)
            )
            try:
                return await get_one(session, query)
            except Exception:
                pass

    @classmethod
    async def autocomplete(
        cls, interaction: discord.Interaction, current: str | int | float
    ) -> list[discord.app_commands.Choice[str]]:
        session = interaction.client.Session(autoflush=False, autocommit=False)
        match = re.search(r"^([^\d]*)((?:\d{1,2})?(?:\.\d{1,2})?)$", current)
        projects = (
            await searchprojects(match.group(1), session)
            if match.group(1)
            else await get_all(session, select(Project))
        )
        chapters = []
        for project in projects:
            chapters += list(
                filter(
                    lambda c: str(c.number).startswith(match.group(2))
                    if match.group(2)
                    else True,
                    project.chapters,
                )
            )
        res = list(
            map(
                lambda chapter: f"{chapter.project.title} {format_number(chapter.number)}",
                chapters,
            )
        )[:10]
        await session.close()
        return [discord.app_commands.Choice(name=i, value=i) for i in res]

    def __str__(self):
        return f"{self.project} {format_number(self.number)}"
