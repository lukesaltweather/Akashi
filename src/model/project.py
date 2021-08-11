from sqlalchemy import String, Integer, Column, ForeignKey
from sqlalchemy.orm import relationship
from ..util.db import Base
from ..util.search import searchproject

icon_default = 'https://cdn.discordapp.com/icons/345797456614785024/9ef2a960cb5f91439556068b8127512a.webp?size=128'

class Project(Base):
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
    # pic = Column(String)
    typesetter_id = Column(Integer, ForeignKey("staff.id", ondelete='SET NULL'))
    redrawer_id = Column(Integer, ForeignKey("staff.id", ondelete='SET NULL'))
    translator_id = Column(Integer, ForeignKey("staff.id", ondelete='SET NULL'))
    proofreader_id = Column(Integer, ForeignKey("staff.id", ondelete='SET NULL'))

    chapters = relationship("Chapter", back_populates="project")
    typesetter = relationship("Staff", foreign_keys=[typesetter_id], backref='project_typesetter')
    translator = relationship("Staff", foreign_keys=[translator_id], backref='project_translator')
    redrawer = relationship("Staff", foreign_keys=[redrawer_id], backref="project_redrawer")
    proofreader = relationship("Staff", foreign_keys=[proofreader_id], backref="project_proofreader")

    def __init__(self, title: str, status: str, link: str, altNames: str, icon=icon_default):
        self.title = title
        self.status = status
        self.link = link
        self.altNames = altNames
        self.icon = icon

    @classmethod
    async def convert(cls, ctx, arg):
        return searchproject(arg, ctx.session)