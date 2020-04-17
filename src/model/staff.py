from sqlalchemy import Column, Integer, String, ForeignKey, BigInteger
from ..util.db import Base


class Staff(Base):

    __tablename__ = "staff"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    discord_id = Column(BigInteger)
    status = Column(String)

    def __init__(self, discord_id, name):
        self.discord_id = discord_id
        self.name = name
