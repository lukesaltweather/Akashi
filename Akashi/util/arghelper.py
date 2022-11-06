from sqlalchemy import or_

from Akashi.model.chapter import Chapter
from Akashi.util.search import searchproject, searchstaff


class arghelper:
    def __init__(self, args):
        if isinstance(args, list):
            self.args = args
        else:
            self.args = args.split(",")

    def list(self):
        return self.args

    def get_project(self, session):
        conds = list()
        for arg in self.args:
            conds.append(Chapter.project_id == arg.id)
        return or_(*conds)

    def get_title(self):
        conds = list()
        for arg in self.args:
            conds.append(Chapter.title.ilike(f"%{arg}%"))
        return or_(*conds)

    def get_number(self):
        conds = list()
        for arg in self.args:
            conds.append(Chapter.number == float(arg))
        return or_(*conds)

    async def get_translator(self, ctx, session):
        conds = list()
        for arg in self.args:
            typ = await searchstaff(arg, ctx, session)
            conds.append(Chapter.translator == typ)
        return or_(*conds)

    async def get_redrawer(self, ctx, session):
        conds = list()
        for arg in self.args:
            typ = await searchstaff(arg, ctx, session)
            conds.append(Chapter.redrawer == typ)
        return or_(*conds)

    async def get_typesetter(self, ctx, session):
        conds = list()
        for arg in self.args:
            typ = await searchstaff(arg, ctx, session)
            conds.append(Chapter.typesetter == typ)
        return or_(*conds)

    async def get_proofreader(self, ctx, session):
        conds = list()
        for arg in self.args:
            typ = await searchstaff(arg, ctx, session)
            conds.append(Chapter.proofreader == typ)
        return or_(*conds)
