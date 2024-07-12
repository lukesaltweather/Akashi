from typing import Optional, Literal, List

from discord.ext.commands import FlagConverter, flag

from Akashi.model.chapter import Chapter
from Akashi.model.project import Project
from Akashi.model.staff import Staff
from Akashi.util.flags.converters import CommaList, DateTimeConverter
from Akashi.util.misc import MISSING


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
    qc: List[Staff] = flag(default=[])
    release_from: Optional[DateTimeConverter]
    release_upto: Optional[DateTimeConverter]
    release_on: Optional[DateTimeConverter]
    links: Optional[bool]
    status: Optional[Literal["active", "tl", "ts", "rd", "pr", "qcts", "ready"]]
    fields: Optional[CommaList[str]] = flag(default=tuple())


class InfoProject(FlagConverter):
    status: Optional[str]
    project: Optional[str]
    tl: Optional[Staff]
    rd: Optional[Staff]
    ts: Optional[Staff]
    pr: Optional[Staff]
    fields: Optional[CommaList[str]]


class MonitorFlags(FlagConverter):
    chapter: Optional[Chapter]
    project: Optional[Project]
