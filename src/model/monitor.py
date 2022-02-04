import datetime

import sqlalchemy.sql.functions
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql.schema import Column, ForeignKey
from sqlalchemy.sql.sqltypes import String, Integer, DateTime, BigInteger

from src.util.db import Base


class MonitorRequest(Base):
    __tablename__ = "monitorrequest"
    id = Column(Integer, primary_key=True)
    chapter_id = Column(Integer, ForeignKey("chapters.id"))
    project_id = Column(Integer, ForeignKey("projects.id"))
    staff_id = Column(Integer, ForeignKey("staff.id"), nullable=False)
    chapter = relationship(
        "Chapter",
        lazy="joined",
        back_populates="to_notify"
    )
    staff = relationship(
        "Staff",
        lazy="joined",
        backref="to_notify"
    )
    project = relationship(
        "Project",
        lazy="joined",
        backref="to_notify",
    )

    def __init__(self, staff, *, chapter=None, project=None) -> None:
        super().__init__()
        self.project_id = project.id if project else None
        self.chapter_id = chapter.id if chapter else None
        self.staff_id = staff.id
