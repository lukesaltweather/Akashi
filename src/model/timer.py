from sqlalchemy import Column, Integer, String, ForeignKey, BigInteger, DateTime
from ..util.db import Base


class Reminder(Base):

    __tablename__ = "reminders"
    id = Column(Integer, primary_key=True)
    author = Column(BigInteger)
    to_remind = Column(BigInteger)
    msg = Column(String)
    date = Column(DateTime)

    def __init__(self, author, msg, date, to_remind=author):
        self.author = author
        self.to_remind = to_remind
        self.msg = msg
        self.date = date
