import datetime

import sqlalchemy.sql.functions
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql.schema import Column, ForeignKey
from sqlalchemy.sql.sqltypes import String, Integer, DateTime, BigInteger

from src.util.db import Base


class Note(Base):
    __tablename__ = "note"
    id = Column(Integer, primary_key=True)
    chapter_id = Column(Integer, ForeignKey("chapters.id"))
    text = Column(String)
    author_id = Column(Integer, ForeignKey("staff.id"))
    created_on = Column(DateTime, default=datetime.datetime.now())
    chapter = relationship(
        "Chapter",
        backref=backref("notes",lazy="selectin", cascade="all,delete", innerjoin=False),
        lazy="selectin",
        innerjoin=False
    )
    author = relationship(
        "Staff",
        lazy="selectin",
        back_populates="notes",
        innerjoin=True
    )

    def __init__(self, chapter, text, author, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.text = text
        self.chapter_id = chapter.id
        self.author_id = author.id
