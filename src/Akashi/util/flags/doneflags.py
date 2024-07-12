from typing import Optional, Literal

from discord.ext.commands import flag

from Akashi.model.staff import Staff
from Akashi.util.flags.flagutils import ChapterFlags
from Akashi.util.misc import MISSING


class DoneFlags(ChapterFlags):
    link: str
    note: Optional[str]
    skipconfirm: bool = flag(default=False)
    step: Literal["tl", "ts", "rd", "pr", "qcts", "qc"]


class AssignFlags(ChapterFlags):
    staff: Optional[Staff] = flag(default=MISSING)
    step: Literal["tl", "rd", "ts", "pr", "qc"] = flag(aliases=["role", "as"])
