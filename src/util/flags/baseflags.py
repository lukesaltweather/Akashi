from typing import Optional

from discord.ext.commands import FlagConverter
from src.model.chapter import Chapter


class ChapterFlags(FlagConverter):
    chapter: Chapter
