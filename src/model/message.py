from sqlalchemy import Column, Integer, String, ForeignKey, BigInteger, DateTime, Boolean
from ..util.db import Base


class Message(Base):

    __tablename__ = "messages"
    id = Column(Integer, primary_key=True)
    message_id = Column(BigInteger)
    author = Column(BigInteger)
    awaiting = Column(String)
    emote = Column(String)
    chapter = Column(Integer)
    created_on = Column(DateTime)
    reminder = Column(Boolean)

    def __init__(self, message_id, awaiting, emote):
        self.message_id = message_id
        self.awaiting = awaiting
        self.emote = emote
        self.reminder = False
