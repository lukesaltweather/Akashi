from prettytable import PrettyTable
from sqlalchemy import inspect

from src.util import misc
import src.model as model

class ReportMixin:
    def get_report(self, title):
        table = PrettyTable()
        table.add_column("", ["ORIGINAL", "EDIT"])
        state = inspect(self)
        changes = 0
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
            changes += 1
        if changes == 0:
            raise RuntimeError("You didn't change any values. Cancelling.")
        text = table.get_string(title=title)
        return misc.drawimage(text)