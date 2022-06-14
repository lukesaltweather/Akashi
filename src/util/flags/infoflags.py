from typing import Optional, Literal, List

from discord.ext.commands import FlagConverter, flag

from src.model.chapter import Chapter
from src.model.project import Project
from src.model.staff import Staff
from src.util.flags.converters import CommaList, DateTimeConverter
from src.util.misc import MISSING


class InfoChapter(FlagConverter):
    project: List[Project] = flag(default=MISSING, aliases=["p"])
    title: List[str] = flag(default=MISSING)
    chapter_from: Optional[float]
    chapter_upto: Optional[float]
    chapter: List[float] = flag(default=[], aliases=["c", "ch"])
    id: List[int] = flag(default=[])
    tl: List[Staff] = flag(default=[])
    rd: List[Staff] = flag(default=[])
    ts: List[Staff] = flag(default=[])
    pr: List[Staff] = flag(default=[])
    release_from: Optional[DateTimeConverter]
    release_upto: Optional[DateTimeConverter]
    release_on: Optional[DateTimeConverter]
    links: Optional[bool]
    status: Optional[Literal["active", "tl", "ts", "rd", "pr", "qcts", "ready"]]
    fields: Optional[CommaList[str]] = flag(default=tuple())


class InfoProject(FlagConverter):
    status: Optional[str] = flag(default=MISSING)
    project: Optional[str]
    tl: Optional[Staff] = flag(default=MISSING)
    rd: Optional[Staff] = flag(default=MISSING)
    ts: Optional[Staff] = flag(default=MISSING)
    pr: Optional[Staff] = flag(default=MISSING)
    fields: Optional[CommaList[str]]


class MonitorFlags(FlagConverter):
    chapter: Optional[Chapter]
    project: Optional[Project]
