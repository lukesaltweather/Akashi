from typing import Optional, Literal, List, Tuple, Union, TypeVar, Generic

from discord.ext.commands import FlagConverter, flag
from src.util.flags.converters import CommaList, DateTimeConverter

from src.model.staff import Staff
from src.util.flags.flagutils import TypeOrMissing
from src.util.misc import MISSING
from src.model.project import Project


class InfoChapter(FlagConverter):
    project: List[Project] = flag(default=MISSING)
    title: List[str] = flag(default=MISSING, noneable=True)
    chapter_from: Optional[float]
    chapter_upto: Optional[float]
    chapter: List[float] = flag(default=[])
    id: List[int] = flag(default=[])
    tl: List[Staff] = flag(default=[], noneable=True)
    rd: List[Staff] = flag(default=[], noneable=True)
    ts: List[Staff] = flag(default=[], noneable=True)
    pr: List[Staff] = flag(default=[], noneable=True)
    release_from: Optional[DateTimeConverter]
    release_upto: Optional[DateTimeConverter]
    release_on: Optional[DateTimeConverter]
    links: Optional[bool]
    status: Optional[Literal["active", "tl", "ts", "rd", "pr", "qcts", "ready"]]
    fields: Optional[CommaList[str]] = flag(default=tuple())


class InfoProject(FlagConverter):
    status: Optional[str]
    project: Optional[str]
    tl: Optional[Staff] = flag(default=[], noneable=True)
    rd: Optional[Staff] = flag(default=[], noneable=True)
    ts: Optional[Staff] = flag(default=[], noneable=True)
    pr: Optional[Staff] = flag(default=[], noneable=True)
    fields: Optional[CommaList[str]]