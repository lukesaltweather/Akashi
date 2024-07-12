from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base

Base = declarative_base()


async def get_all(session, stmt):
    return (await session.execute(stmt)).scalars().unique().all()


async def get_first(session, stmt):
    return (await session.execute(stmt)).scalars().unique().first()


async def get_one(session, stmt):
    return (await session.execute(stmt)).scalars().unique().one()
