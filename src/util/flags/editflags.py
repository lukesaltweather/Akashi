from typing import Optional, Literal, Union, TypeVar, Generic

from discord import Colour
from discord.ext.commands import FlagConverter, flag, ColourConverter
from .converters import ChapterConverter, DateTimeConverter

from .baseflags import ChapterFlags
from src.model.staff import Staff
from src.model.project import Project

from src.util.misc import MISSING

NoneLiteral = Literal["None", "none"]


def none_or(t: type) -> type:
    return Union[NoneLiteral, t]


class EditChapterFlags(ChapterFlags):
    title: none_or(str) = flag(default=MISSING)
    tl: none_or(Staff) = flag(default=MISSING)
    rd: none_or(Staff) = flag(default=MISSING)
    ts: none_or(Staff) = flag(default=MISSING)
    pr: none_or(Staff) = flag(default=MISSING)
    link_tl: none_or(str) = flag(default=MISSING)
    link_rd: none_or(str) = flag(default=MISSING)
    link_ts: none_or(str) = flag(default=MISSING)
    link_pr: none_or(str) = flag(default=MISSING)
    link_qcts: none_or(str) = flag(default=MISSING)
    link_raw: none_or(str) = flag(default=MISSING)
    to_project: Optional[Project]
    to_chapter: Optional[float]
    notes: none_or(str) = flag(default=MISSING)


class ReleaseFlags(ChapterFlags):
    date: Optional[DateTimeConverter]


class EditProjectFlags(FlagConverter):
    project: Project
    title: Optional[str]
    status: Optional[str]
    color: none_or(Colour) = flag(default=MISSING)
    position: none_or(int) = flag(default=MISSING)
    tl: none_or(Staff) = flag(default=MISSING)
    rd: none_or(Staff) = flag(default=MISSING)
    ts: none_or(Staff) = flag(default=MISSING)
    pr: none_or(Staff) = flag(default=MISSING)
    altnames: none_or(str) = flag(default=MISSING)
    thumbnail: Optional[str]
    icon: none_or(str) = flag(default=MISSING)
    link: Optional[str]


class EditStaffFlags:
    member: Staff
    id: Optional[int]
    name: Optional[str]
    status: Literal["active", "inactive"]
