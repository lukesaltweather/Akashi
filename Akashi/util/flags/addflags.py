from typing import Optional

from discord import Member
from discord.ext.commands.flags import FlagConverter, flag

from Akashi.model.project import Project
from Akashi.model.staff import Staff


class AddChapterFlags(FlagConverter):
    chapter: str = flag(aliases=["c"])
    raws: str
    ts: Optional[Staff]
    rd: Optional[Staff]
    pr: Optional[Staff]
    tl: Optional[Staff]
    note: Optional[str]


class AddProjectFlags(FlagConverter):
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


class AddStaffFlags(FlagConverter):
    member: Member


class MassAddFlags(FlagConverter):
    chapter: int
    project: Project
