from typing import Optional, Literal, List, Tuple, Union

from discord.ext.commands import FlagConverter, flags
from .converters import ChapterConverter, StaffConverter, DateTimeConverter, ProjectConverter

from .baseflags import ChapterFlags

class InfoChapter(FlagConverter):
    project: Optional[List[ProjectConverter]]
    title: Optional[List[str]]
    chapter_from: Optional[float]
    chapter_upto: Optional[float]
    chapter: Optional[List[float]]
    id: Optional[List[int]]
    tl: List[StaffConverter] = flags.flag(default = [])
    rd: List[StaffConverter] = flags.flag(default = [])
    ts: List[StaffConverter] = flags.flag(default = [])
    pr: List[StaffConverter] = flags.flag(default = [])
    release_from: Optional[DateTimeConverter]
    release_upto: Optional[DateTimeConverter]
    release_on: Optional[DateTimeConverter]
    links: Optional[bool]
    status: Optional[Literal["active", "tl", "ts", "rd", "pr", "qcts", "ready"]]
    fields: Optional[Tuple[str]]

class InfoProject(FlagConverter):
    status: Optional[str]
    project: Optional[str]
    tl: Optional[StaffConverter]
    rd: Optional[StaffConverter]
    ts: Optional[StaffConverter]
    pr: Optional[StaffConverter]
    fields: Optional[Tuple[str]]


