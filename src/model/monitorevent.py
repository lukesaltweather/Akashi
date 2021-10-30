import datetime

import sqlalchemy.sql.functions
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql.schema import Column, ForeignKey
from sqlalchemy.sql.sqltypes import String, Integer, DateTime, BigInteger

from src.util.db import Base


class MonitorEvent(Base):
    __tablename__ = "monitorevent"
    id = Column(Integer, primary_key=True)
    chapter_id = Column(Integer, ForeignKey("chapters.id"))
    project_id = Column(Integer, ForeignKey("projects.id"))
    staff_id = Column(Integer, ForeignKey("staff.id"), nullable=False)
    chapter = relationship(
        "Chapter",
        lazy="selectin",
        innerjoin=False
    )
    staff = relationship(
        "Staff",
        lazy="selectin",
        backref=backref("to_notify",lazy="selectin", cascade="all,delete", innerjoin=False),
        innerjoin=True
    )

    project = relationship(
        "Project",
        lazy="selectin",
        backref=backref("to_notify", lazy="selectin", cascade="all,delete", innerjoin=False),
        innerjoin=True
    )

    def __init__(self, staff, *, chapter=None, project=None) -> None:
        super().__init__()
        self.project_id = project.id
        self.chapter_id = chapter.id
        self.staff_id = staff.id
