from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base

# TODO: Fix usage of global
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


async def get_all(session, stmt):
    return (await session.execute(stmt)).scalars().all()


async def get_first(session, stmt):
    return (await session.execute(stmt)).scalars().first()


async def get_one(session, stmt):
    return (await session.execute(stmt)).scalars().one()
