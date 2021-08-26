from typing import Optional, Literal, Union, TypeVar, Generic

from discord import Colour
from discord.ext.commands import FlagConverter, flag, ColourConverter
from .converters import ChapterConverter, DateTimeConverter

from .baseflags import ChapterFlags
from src.model.staff import Staff
from src.model.project import Project

from src.util.misc import MISSING

NoneLiteral = Literal["None", "none"]

def NoneOr(t):
    return Union[NoneLiteral, t]

class EditChapterFlags(ChapterFlags):
    title: NoneOr(str) = flag(default=MISSING)
    tl: NoneOr(Staff) = flag(default=MISSING)
    rd: NoneOr(Staff) = flag(default=MISSING)
    ts: NoneOr(Staff) = flag(default=MISSING)
    pr: NoneOr(Staff) = flag(default=MISSING)
    link_tl: NoneOr(str) = flag(default=MISSING)
    link_rd: NoneOr(str) = flag(default=MISSING)
    link_ts: NoneOr(str) = flag(default=MISSING)
    link_pr: NoneOr(str) = flag(default=MISSING)
    link_qcts: NoneOr(str) = flag(default=MISSING)
    link_raw: NoneOr(str) = flag(default=MISSING)
    to_project: Optional[Project]
    to_chapter: Optional[float]
    notes: NoneOr(str) = flag(default=MISSING)

class ReleaseFlags(ChapterFlags):
    date: Optional[DateTimeConverter]


class EditProjectFlags(FlagConverter):
    project: Project
    title: Optional[str]
    status: Optional[str]
    color: Union[Colour,NoneLiteral] = flag(default=None)
    position: Union[NoneLiteral, int] = flag(default=None)
    tl: Union[NoneLiteral,Staff] = flag(default=None)
    rd: Union[NoneLiteral,Staff] = flag(default=None)
    ts: Union[NoneLiteral,Staff] = flag(default=None)
    pr: Union[NoneLiteral,Staff] = flag(default=None)
    altnames: Optional[str]
    thumbnail: Optional[str]
    icon: Optional[str]
    link: Optional[str]

class EditStaffFlags:
    member: Staff
    id: Optional[int]
    name: Optional[str]
    status: Literal["active", "inactive"]