from typing import Optional

from discord.ext.commands import FlagConverter
from .converters import ChapterConverter, StaffConverter, DateTimeConverter, ProjectConverter


class ChapterFlags(FlagConverter):
    chapter: ChapterConverter
