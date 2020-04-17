import sqlalchemy
from discord.ext import commands
from discord.ext.commands import MissingRequiredArgument
from sqlalchemy.orm import aliased

from src.model.chapter import Chapter
from src.model.project import Project
from src.model.staff import Staff
from src.util import exceptions
from src.util.exceptions import MissingRequiredParameter
from src.util.search import searchproject


class Assign(commands.Cog):
    def __init__(self, bot, sessionmaker, config):
        self.bot = bot
        self.Session = sessionmaker
        self.config = config

    async def cog_check(self, ctx):
        admin = ctx.guild.get_role(self.config["neko_herders"])
        poweruser = ctx.guild.get_role(self.config["power_user"])
        ia = admin in ctx.message.author.roles or ctx.message.author.id == 358244935041810443 or poweruser in ctx.message.author.roles
        ic = ctx.channel.id == self.config["command_channel"]
        guild = ctx.guild is not None
        if ia and ic and guild:
            return True
        elif ic:
            raise exceptions.MissingRequiredPermission("Missing permission `poweruser`.")
        elif not guild:
            raise exceptions.MissingRequiredPermission("Missing permission `Server Member`.")

    @commands.command()
    async def assign(self, ctx, *, arg):
        """Says hello"""
        session = self.Session()
        try:
            arg = arg[1:]
            d = dict(x.split('=', 1) for x in arg.split(' -'))
            ts_alias = aliased(Staff)
            rd_alias = aliased(Staff)
            tl_alias = aliased(Staff)
            pr_alias = aliased(Staff)
            query = session.query(Chapter).outerjoin(ts_alias, Chapter.typesetter_id == ts_alias.id). \
                outerjoin(rd_alias, Chapter.redrawer_id == rd_alias.id). \
                outerjoin(tl_alias, Chapter.translator_id == tl_alias.id). \
                outerjoin(pr_alias, Chapter.proofreader_id == pr_alias.id). \
                join(Project, Chapter.project_id == Project.id)
            if "p" in d and "c" in d:
                project = searchproject(d["p"], session)
                record = query.filter(Chapter.project.id == project.id).filter(Chapter.number == float(d["c"])).one()
            elif "id" in d:
                record = query.filter(Chapter.id == int(d["id"])).one()
            else:
                raise MissingRequiredParameter("Project and Chapter or ID")
            await ctx.send(record.id)
        finally:
            session.close()

