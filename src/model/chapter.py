from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship
from ..util.db import Base
from src.model.staff import Staff
from src.model.project import Project


class Chapter(Base):
    __tablename__ = "chapters"
    id = Column(Integer, primary_key=True)
    number = Column(Float)
    title = Column(String)
    notes = Column(String)
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

    typesetter_id = Column(Integer, ForeignKey("staff.id", ondelete='SET NULL'))
    translator_id = Column(Integer, ForeignKey("staff.id", ondelete='SET NULL'))
    redrawer_id = Column(Integer, ForeignKey("staff.id", ondelete='SET NULL'))
    proofreader_id = Column(Integer, ForeignKey("staff.id", ondelete='SET NULL'))
    project_id = Column(Integer, ForeignKey("projects.id"))

    typesetter = relationship("Staff", foreign_keys=[typesetter_id], backref='chapters_typesetter', uselist=False)
    translator = relationship("Staff", foreign_keys=[translator_id], backref='chapters_translator', uselist=False)
    redrawer = relationship("Staff", foreign_keys=[redrawer_id], backref="chapters_redrawer", uselist=False)
    proofreader = relationship("Staff", foreign_keys=[proofreader_id], backref="chapters_proofreader", uselist=False)
    project = relationship("Project", back_populates="chapters", uselist=False)

    def __init__(self, number, link_raw):
        self.number = number
        self.link_raw = link_raw
        self.link_tl = None
        self.link_ts = None
        self.link_rd = None
        self.link_pr = None
        self.link_rl = None
        self.notes = ""
