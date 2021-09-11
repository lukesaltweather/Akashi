from typing import Optional, Literal, List, Tuple, Union, TypeVar, Generic

from discord.ext.commands import FlagConverter, flag
from .converters import DateTimeConverter

from src.model.staff import Staff
from .editflags import none_or, NoneLiteral
from ..misc import MISSING
from ...model.project import Project

T = TypeVar("T")


class Test(List[T], Generic[T]):
    def __init__(self, *args, **kwargs):
        super().__init__()


class InfoChapter(FlagConverter):
    project: List[Project] = flag(default=MISSING)
    title: List[str] = flag(default=MISSING, noneable=True)
    chapter_from: Optional[float]
    chapter_upto: Optional[float]
    chapter: List[float] = flag(default=[])
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
    fields: Tuple[str] = flag(default=tuple())


class InfoProject(FlagConverter):
    status: Optional[str]
    project: Optional[str]
    tl: Optional[Staff]
    rd: Optional[Staff]
    ts: Optional[Staff]
    pr: Optional[Staff]
    fields: Optional[Tuple[str]]
