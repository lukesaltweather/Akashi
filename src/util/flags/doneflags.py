from typing import Optional, Literal

from discord.ext.commands import flag

from .baseflags import ChapterFlags

class DoneFlags(ChapterFlags):
    link: str
    note: Optional[str]
    skipconfirm: bool = flag(default=False)
    step: Literal["tl", "ts", "rd", "pr", "qcts"]