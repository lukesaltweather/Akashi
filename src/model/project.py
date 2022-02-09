from sqlalchemy import String, Integer, Column, ForeignKey
from sqlalchemy.orm import relationship, backref

from src.util.db import Base
from src.model.ReportMixin import ReportMixin
import src.util.search as search

icon_default = "https://cdn.discordapp.com/icons/345797456614785024/9ef2a960cb5f91439556068b8127512a.webp?size=128"


class Project(Base, ReportMixin):
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

    def __str__(self):
        return self.title
