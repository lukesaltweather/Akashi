from sqlalchemy import or_

from src.model.chapter import Chapter


class arghelper:
    def __init__(self, args:str):
        self.args = args.split(",")

    def list(self):
        return self.args

    def get_title(self):
        conds = list()
        for arg in self.args:
            conds.append(Chapter.title.ilike(f"%{arg}%"))
        return or_(*conds)

    def get_number(self):
        conds = list()
        for arg in self.args:
            conds.append(Chapter.number == int(arg))
        return or_(*conds)
