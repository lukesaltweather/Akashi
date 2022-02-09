from sqlalchemy import Column, Integer, String, BigInteger
from sqlalchemy.orm import relationship

from src.util.db import Base
import src.util.search as s


class Staff(Base):

    __tablename__ = "staff"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    discord_id = Column(BigInteger)
    status = Column(String)

    notes = relationship(
        "Note", back_populates="author", lazy="selectin", innerjoin=False, uselist=True
    )

    def __init__(self, discord_id, name):
        self.discord_id = discord_id
        self.name = name

    @classmethod
    async def convert(cls, ctx, arg):
        return await s.searchstaff(arg, ctx, ctx.session)
