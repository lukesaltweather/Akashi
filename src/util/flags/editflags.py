from typing import Optional, Literal

from discord.ext.commands import FlagConverter
from .converters import ChapterConverter, StaffConverter, DateTimeConverter, ProjectConverter

from .baseflags import ChapterFlags

class EditChapterFlags(ChapterFlags):
    title: Optional[str]
    tl: Optional[StaffConverter]
    rd: Optional[StaffConverter]
    ts: Optional[StaffConverter]
    pr: Optional[StaffConverter]
    link_tl: Optional[str]
    link_rd: Optional[str]
    link_ts: Optional[str]
    link_pr: Optional[str]
    link_qcts: Optional[str]
    link_raw: Optional[str]
    date_tl: Optional[DateTimeConverter]
    date_rd: Optional[DateTimeConverter]
    date_ts: Optional[DateTimeConverter]
    date_pq: Optional[DateTimeConverter]
    date_qcts: Optional[DateTimeConverter]
    date_rl: Optional[DateTimeConverter]
    to_project: Optional[ProjectConverter]
    to_chapter: Optional[float]
    notes: Optional[str]

class EditProjectFlags:
    project: ProjectConverter
    title: Optional[str]
    status: Optional[str]
    color: Optional[str]
    position: Optional[str]
    tl: Optional[StaffConverter]
    rd: Optional[StaffConverter]
    ts: Optional[StaffConverter]
    pr: Optional[StaffConverter]
    altnames: Optional[str]
    thumbnail: Optional[str]
    icon: Optional[str]
    link: Optional[str]

class EditStaffFlags:
    id: int
    to_id: Optional[int]
    name: Optional[str]
    status: Literal["active", "inactive"]