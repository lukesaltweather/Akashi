from typing import Optional, List

from discord.ext.commands.flags import FlagConverter, flag
from discord import Member

from src.model.project import Project
from src.model.staff import Staff


class AddChapterFlags(FlagConverter):
    chapter: float
    project: Project
    raws: str
    ts: Optional[Staff]
    rd: Optional[Staff]
    pr: Optional[Staff]
    tl: Optional[Staff]


class AddProjectFlags(FlagConverter):
    ts: Optional[Staff]
    rd: Optional[Staff]
    pr: Optional[Staff]
    tl: Optional[Staff]
    icon: Optional[str]
    thumbnail: str
    title: str
    status: str = flag(default = "active")
    altnames: str = flag(default=None)
    link: str

class AddStaffFlags(FlagConverter):
    member: Member

class MassAddFlags(FlagConverter):
    chapter: int
    project: Project

