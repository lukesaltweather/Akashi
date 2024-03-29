from prettytable import PrettyTable
from sqlalchemy import inspect

import Akashi.model as model
from Akashi.util import misc


class ReportMixin:
    def get_report(self, title):
        title = str(title)
        table = PrettyTable()
        table.add_column("", ["ORIGINAL", "EDIT"])
        state = inspect(self)
        for attr in state.attrs:
            hist = attr.history
            if not hist.has_changes():
                continue
            old_value = hist.deleted[0] if hist.deleted else None
            if isinstance(old_value, model.staff.Staff):
                old_value = old_value.name
            elif isinstance(old_value, model.project.Project):
                old_value = old_value.title
            new_value = hist.added[0] if hist.added else None
            if isinstance(new_value, model.staff.Staff):
                new_value = new_value.name
            elif isinstance(new_value, model.project.Project):
                new_value = new_value.title
            table.add_column(attr.key.capitalize(), [old_value, new_value])
        text = table.get_string(title=title)
        return misc.drawimage(text)
