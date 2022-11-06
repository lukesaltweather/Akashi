from sqlalchemy import Column, String, BigInteger

from Akashi.util.db import Base


class Tag(Base):
    __tablename__ = "tag"
    tag = Column(String, primary_key=True, nullable=False)
    content = Column(String, nullable=False)
    author = Column(BigInteger, nullable=False)

    def __init__(self, tag: str, content: str, author: int):
        self.tag = tag
        self.content = content
        self.author = author
