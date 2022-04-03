from typing import Optional, Literal, Type, Union, TypeVar, Generic

from discord import Colour
from discord.ext.commands import FlagConverter, flag, ColourConverter
from .converters import DateTimeConverter

from src.util.flags.flagutils import ChapterFlags
from src.model.staff import Staff
from src.model.project import Project

from src.util.misc import MISSING
from src.util.flags.flagutils import TypeOrMissing


class EditChapterFlags(ChapterFlags, error_on_unknown=True):
    title: TypeOrMissing[str] = flag(default=MISSING)
    tl: TypeOrMissing[Staff] = flag(default=MISSING)
    rd: TypeOrMissing[Staff] = flag(default=MISSING)
    ts: TypeOrMissing[Staff] = flag(default=MISSING)
    pr: TypeOrMissing[Staff] = flag(default=MISSING)
    link_tl: TypeOrMissing[str] = flag(default=MISSING)
    link_rd: TypeOrMissing[str] = flag(default=MISSING)
    link_ts: TypeOrMissing[str] = flag(default=MISSING)
    link_pr: TypeOrMissing[str] = flag(default=MISSING)
    link_qcts: TypeOrMissing[str] = flag(default=MISSING)
    link_raw: TypeOrMissing[str] = flag(default=MISSING)
    to_project: Optional[Project]
    to_chapter: Optional[float]
    date_created: TypeOrMissing[DateTimeConverter] = flag(default=MISSING)
    date_tl: TypeOrMissing[DateTimeConverter] = flag(default=MISSING)
    date_rd: TypeOrMissing[DateTimeConverter] = flag(default=MISSING)
    date_ts: TypeOrMissing[DateTimeConverter] = flag(default=MISSING)
    date_pr: TypeOrMissing[DateTimeConverter] = flag(default=MISSING)
    date_qcts: TypeOrMissing[DateTimeConverter] = flag(default=MISSING)
    date_release: TypeOrMissing[DateTimeConverter] = flag(default=MISSING)


class ReleaseFlags(ChapterFlags, error_on_unknown=True):
    date: Optional[DateTimeConverter]


class EditProjectFlags(FlagConverter, error_on_unknown=True):
    project: Project = flag(aliases=["p"])
    title: Optional[str]
    status: Optional[str]
    color: TypeOrMissing[Colour] = flag(default=MISSING)
    position: TypeOrMissing[int] = flag(default=MISSING)
    tl: TypeOrMissing[Staff] = flag(default=MISSING)
    rd: TypeOrMissing[Staff] = flag(default=MISSING)
    ts: TypeOrMissing[Staff] = flag(default=MISSING)
    pr: TypeOrMissing[Staff] = flag(default=MISSING)
    altnames: TypeOrMissing[str] = flag(default=MISSING)
    thumbnail: Optional[str]
    icon: TypeOrMissing[str] = flag(default=MISSING)
    link: Optional[str]


class EditStaffFlags(FlagConverter, error_on_unknown=True):
    member: Staff
    id: Optional[int]
    name: Optional[str]
    status: Optional[Literal["active", "inactive"]]
