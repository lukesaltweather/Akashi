from datetime import datetime

from sqlalchemy.orm import aliased

from discord.ext.commands.errors import ConversionError

from src.model.chapter import Chapter
from src.model.project import Project
from src.model.staff import Staff
from src.util.search import searchproject, searchstaff


class ChapterConverter:
    @classmethod
    async def convert(cls, ctx, arg: str):
        chapter = float(arg.split(" ")[-1])
        project = arg[0:len(arg)-len(arg.split(" ")[-1])]

        session = ctx.bot.Session()
        try:
            project = searchproject(project, session)

            ts_alias = aliased(Staff)
            rd_alias = aliased(Staff)
            tl_alias = aliased(Staff)
            pr_alias = aliased(Staff)
            query = session.query(Chapter).outerjoin(ts_alias, Chapter.typesetter_id == ts_alias.id). \
                outerjoin(rd_alias, Chapter.redrawer_id == rd_alias.id). \
                outerjoin(tl_alias, Chapter.translator_id == tl_alias.id). \
                outerjoin(pr_alias, Chapter.proofreader_id == pr_alias.id). \
                join(Project, Chapter.project_id == Project.id)
            return query.filter(Chapter.project_id == project.id).filter(Chapter.number == chapter).one()
        except Exception as e:
            raise ConversionError(cls, e)

class DateTimeConverter:
    @classmethod
    async def convert(cls, ctx, arg):
        return datetime.strptime(arg, "%Y %m %d")

class StaffConverter:
    @classmethod
    async def convert(cls, ctx, arg):
        return await searchstaff(arg, ctx, ctx.bot.Session())

class ProjectConverter:
    @classmethod
    async def convert(cls, ctx, arg):
        return searchproject(arg, ctx.bot.Session())