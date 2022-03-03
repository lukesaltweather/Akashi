from typing import Optional

from discord import Member
from discord.ext.commands.flags import FlagConverter, flag

from src.model.project import Project
from src.model.staff import Staff


class AddChapterFlags(FlagConverter, error_on_unknown=True):
    chapter: str = flag(aliases=["c"])
    raws: str
    ts: Optional[Staff]
    rd: Optional[Staff]
    pr: Optional[Staff]
    tl: Optional[Staff]
    note: Optional[str]


class AddProjectFlags(FlagConverter, error_on_unknown=True):
    ts: Optional[Staff]
    rd: Optional[Staff]
    pr: Optional[Staff]
    tl: Optional[Staff]
    icon: Optional[str]
    thumbnail: str
    title: str
    status: str = flag(default="active")
    altnames: str = flag(default=None)
    link: str


class AddStaffFlags(FlagConverter, error_on_unknown=True):
    member: Member


class MassAddFlags(FlagConverter, error_on_unknown=True):
    chapter: int
    project: Project
