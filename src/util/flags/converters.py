from datetime import datetime

from sqlalchemy.orm import aliased
from sqlalchemy import select

from discord.ext.commands.errors import ConversionError, BadArgument

from src.model.chapter import Chapter
from src.model.project import Project
from src.model.staff import Staff
from src.util.search import searchproject, searchstaff
from src.util.db import get_one
from src.util.misc import MISSING


class ChapterConverter:
    @classmethod
    async def convert(cls, ctx, arg: str):
        chapter = float(arg.split(" ")[-1])
        proj = arg[0 : len(arg) - len(arg.split(" ")[-1])]

        session = ctx.session
        try:
            project = searchproject(proj, session)

            ts_alias = aliased(Staff)
            rd_alias = aliased(Staff)
            tl_alias = aliased(Staff)
            pr_alias = aliased(Staff)
            query = (
                select(Chapter)
                .outerjoin(ts_alias, Chapter.typesetter_id == ts_alias.id)
                .outerjoin(rd_alias, Chapter.redrawer_id == rd_alias.id)
                .outerjoin(tl_alias, Chapter.translator_id == tl_alias.id)
                .outerjoin(pr_alias, Chapter.proofreader_id == pr_alias.id)
                .join(Project, Chapter.project_id == Project.id)
            )
            return await get_one(
                session,
                query.filter(Chapter.project_id == project.id).filter(
                    Chapter.number == chapter
                ),
            )
        except Exception as e:
            raise BadArgument(cls, e)


class DateTimeConverter:
    @classmethod
    async def convert(cls, ctx, arg):
        return datetime.strptime(arg, "%Y-%m-%d")


class StaffConverter:
    @classmethod
    async def convert(cls, ctx, arg):
        return await searchstaff(arg, ctx, ctx.session)


class ProjectConverter:
    @classmethod
    async def convert(cls, ctx, arg):
        return await searchproject(arg, ctx.session)


class __CommaListMeta(type):
    def __getitem__(cls, arg):
        cls.__type__ = arg
        return cls


class CommaList(metaclass=__CommaListMeta):
    @classmethod
    async def convert(cls, context, arg: str):
        return [cls.__type__(item) for item in arg.replace(" ", "").split(",")]
