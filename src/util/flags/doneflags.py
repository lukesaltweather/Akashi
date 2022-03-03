from typing import Optional, Literal

from discord.ext.commands import flag

from src.model.staff import Staff
from src.util.flags.flagutils import ChapterFlags
from src.util.misc import MISSING


class DoneFlags(ChapterFlags, error_on_unknown=True):
    link: str
    note: Optional[str]
    skipconfirm: bool = flag(default=False)
    step: Literal["tl", "ts", "rd", "pr", "qcts", "qc", "prts"]


class AssignFlags(ChapterFlags, error_on_unknown=True):
    staff: Optional[Staff] = flag(default=MISSING)
    step: Literal["tl", "rd", "ts", "pr", "qc"] = flag(aliases=["role", "as"])
