import typing as t

import discord
from sqlalchemy import String, Integer, Column, ForeignKey
from sqlalchemy.orm import relationship, backref

import Akashi.util.search as search
from Akashi.model.ReportMixin import ReportMixin
from Akashi.util.db import Base

icon_default = "https://cdn.discordapp.com/icons/345797456614785024/9ef2a960cb5f91439556068b8127512a.webp?size=128"


class Project(Base, ReportMixin, discord.app_commands.Transformer):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    status = Column(String)
    link = Column(String)
    altNames = Column(String)
    thumbnail = Column(String)
    icon = Column(String)
    position = Column(Integer)
    color = Column(String)
    typesetter_id = Column(Integer, ForeignKey("staff.id", ondelete="SET NULL"))
    redrawer_id = Column(Integer, ForeignKey("staff.id", ondelete="SET NULL"))
    translator_id = Column(Integer, ForeignKey("staff.id", ondelete="SET NULL"))
    proofreader_id = Column(Integer, ForeignKey("staff.id", ondelete="SET NULL"))
    mangadex_id = Column(String, nullable=True)

    typesetter = relationship(
        "Staff",
        foreign_keys=[typesetter_id],
        backref=backref("project_typesetter", lazy="joined"),
        lazy="joined",
    )
    translator = relationship(
        "Staff",
        foreign_keys=[translator_id],
        backref=backref("project_translator", lazy="joined"),
        lazy="joined",
    )
    redrawer = relationship(
        "Staff",
        foreign_keys=[redrawer_id],
        backref=backref("project_redrawer", lazy="joined"),
        lazy="joined",
    )
    proofreader = relationship(
        "Staff",
        foreign_keys=[proofreader_id],
        backref=backref("project_proofreader", lazy="joined"),
        lazy="joined",
    )

    def __init__(
        self, title: str, status: str, link: str, altNames: str, icon=icon_default
    ):
        self.title = title
        self.status = status
        self.link = link
        self.altNames = altNames
        self.icon = icon

    @classmethod
    async def convert(cls, ctx, arg):
        return await search.searchproject(arg, ctx.session)

    @classmethod
    async def transform(cls, interaction: discord.Interaction, value):
        return await search.searchproject(value, interaction.client.Session())

    @classmethod
    async def autocomplete(
        cls, interaction: discord.Interaction, value: t.Union[int, float, str]
    ) -> t.List[discord.app_commands.Choice[t.Union[int, float, str]]]:
        session = interaction.client.Session()
        res = await search.searchprojects(value, session)
        await session.close()
        return [discord.app_commands.Choice(name=i.title, value=i.title) for i in res]

    def __str__(self):
        return self.title
