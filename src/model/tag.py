from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float, BigInteger
from sqlalchemy.orm import relationship
from ..util.db import Base
from src.model.staff import Staff
from src.model.project import Project


class Tag(Base):
    __tablename__ = "tag"
    tag = Column(String, primary_key=True, nullable=False)
    content = Column(String, nullable=False)
    author = Column(BigInteger, nullable=False)

    def __init__(self, tag: str, content: str, author: int):
        self.tag = tag
        self.content = content
        self.author = author
