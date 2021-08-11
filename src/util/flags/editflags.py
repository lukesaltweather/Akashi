from typing import Optional, Literal, Union

from discord import Colour
from discord.ext.commands import FlagConverter, flag, ColourConverter
from .converters import ChapterConverter, DateTimeConverter

from .baseflags import ChapterFlags
from src.model.staff import Staff
from src.model.project import Project

NoneLiteral = Literal["None", "none"]

class EditChapterFlags(ChapterFlags):
    title: Optional[str]
    tl: Union[NoneLiteral,Staff] = flag(default=None)
    rd: Union[NoneLiteral,Staff] = flag(default=None)
    ts: Union[NoneLiteral,Staff] = flag(default=None)
    pr: Union[NoneLiteral,Staff] = flag(default=None)
    link_tl: Optional[str]
    link_rd: Optional[str]
    link_ts: Optional[str]
    link_pr: Optional[str]
    link_qcts: Optional[str]
    link_raw: Optional[str]
    to_project: Optional[Project]
    to_chapter: Optional[float]
    notes: Optional[str]

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