from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship, aliased, joinedload
from sqlalchemy.sql.expression import select
from src.model.monitor import MonitorRequest

from src.model.note import Note
from src.model.project import Project
from src.model.staff import Staff
from src.model.ReportMixin import ReportMixin
from src.util.db import Base, get_one
from src.util.misc import format_number
from src.util.search import searchproject


class Chapter(Base, ReportMixin):
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
        backref="chapters_typesetter",
        uselist=False,
        lazy="joined",
    )
    translator = relationship(
        "Staff",
        foreign_keys=[translator_id],
        backref="chapters_translator",
        uselist=False,
        lazy="joined",
    )
    redrawer = relationship(
        "Staff",
        foreign_keys=[redrawer_id],
        backref="chapters_redrawer",
        uselist=False,
        lazy="joined",
    )
    proofreader = relationship(
        "Staff",
        foreign_keys=[proofreader_id],
        backref="chapters_proofreader",
        uselist=False,
        lazy="joined",
    )
    project = relationship(
        "Project", back_populates="chapters", uselist=False, lazy="joined"
    )

    to_notify = relationship(
        "MonitorRequest",
        lazy="joined",
        back_populates="chapter",
        uselist=True,
    )

    # notes = relationship(
    #     "Note", back_populates="chapter", innerjoin=False, lazy="selectin", cascade="all,delete"
    # )

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

        session = ctx.session
        project = await searchproject(proj, session)

        ts_alias = aliased(Staff)
        rd_alias = aliased(Staff)
        tl_alias = aliased(Staff)
        pr_alias = aliased(Staff)
        query = (
            select(Chapter)
            .outerjoin(ts_alias, Chapter.typesetter_id == ts_alias.id)
            .outerjoin(rd_alias, Chapter.redrawer_id == rd_alias.id)
            .outerjoin(tl_alias, Chapter.translator_id == tl_alias.id)
            .outerjoin(pr_alias, Chapter.proofreader_id == pr_alias.id)
            .filter(Chapter.project_id == project.id)
            .filter(Chapter.number == chapter)
            .options(joinedload(Chapter.to_notify).joinedload(MonitorRequest.staff),
            joinedload(Chapter.to_notify).joinedload(MonitorRequest.project))
        )
        return await get_one(ctx.session, query)

    def __str__(self):
        return f"{self.project} {format_number(self.number)}"
