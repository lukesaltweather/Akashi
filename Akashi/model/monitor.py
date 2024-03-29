from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql.schema import Column, ForeignKey
from sqlalchemy.sql.sqltypes import Integer

from Akashi.util.db import Base


class MonitorRequest(Base):
    __tablename__ = "monitorrequest"
    id = Column(Integer, primary_key=True)
    chapter_id = Column(Integer, ForeignKey("chapters.id"))
    project_id = Column(Integer, ForeignKey("projects.id"))
    staff_id = Column(Integer, ForeignKey("staff.id"), nullable=False)
    chapter = relationship(
        "Chapter",
        lazy="joined",
        backref=backref("to_notify", lazy="joined", uselist=True),
        foreign_keys=[chapter_id],
    )
    staff = relationship(
        "Staff",
        lazy="joined",
        backref=backref("to_notify", lazy="joined", uselist=True),
        foreign_keys=[staff_id],
        innerjoin=True,
    )
    project = relationship(
        "Project",
        lazy="joined",
        backref=backref("to_notify", lazy="joined", uselist=True),
        foreign_keys=[project_id],
    )

    def __init__(self, staff, *, chapter=None, project=None) -> None:
        super().__init__()
        self.project_id = project.id if project else None
        self.chapter_id = chapter.id if chapter else None
        self.staff_id = staff.id
