from typing import Optional, Literal, List, Tuple, Union

from discord.ext.commands import FlagConverter, flags
from .converters import DateTimeConverter

from src.model.staff import Staff

class InfoChapter(FlagConverter):
    project: List[str] = flags.flag(default=[])
    title: List[str] = flags.flag(default=[])
    chapter_from: Optional[float]
    chapter_upto: Optional[float]
    chapter: List[float] = flags.flag(default=[])
    id: List[int] = flags.flag(default=[])
    tl: List[Staff] = flags.flag(default = [])
    rd: List[Staff] = flags.flag(default = [])
    ts: List[Staff] = flags.flag(default = [])
    pr: List[Staff] = flags.flag(default = [])
    release_from: Optional[DateTimeConverter]
    release_upto: Optional[DateTimeConverter]
    release_on: Optional[DateTimeConverter]
    links: Optional[bool]
    status: Optional[Literal["active", "tl", "ts", "rd", "pr", "qcts", "ready"]]
    fields: Tuple[str] = flags.flag(default=tuple())

class InfoProject(FlagConverter):
    status: Optional[str]
    project: Optional[str]
    tl: Optional[Staff]
    rd: Optional[Staff]
    ts: Optional[Staff]
    pr: Optional[Staff]
    fields: Optional[Tuple[str]]


