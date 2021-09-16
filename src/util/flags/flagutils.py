from typing import Literal, Union

from discord.ext.commands.flags import FlagConverter

from src.model.chapter import Chapter


class ChapterFlags(FlagConverter):
    chapter: Chapter


NoneLiteral = Literal["None", "none"]


class __TypeOrMissing(type):
    def __getitem__(self, parameter):
        return Union[NoneLiteral, parameter]


class TypeOrMissing(metaclass=__TypeOrMissing):
    pass
