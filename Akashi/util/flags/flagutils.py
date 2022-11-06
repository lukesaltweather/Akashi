from typing import Literal, Union

from discord.ext.commands.flags import FlagConverter, flag

from Akashi.model.chapter import Chapter


class ChapterFlags(FlagConverter):
    chapter: Chapter = flag(aliases=["c"])


NoneLiteral = Literal["none"]


class __TypeOrMissing(type):
    def __getitem__(self, parameter):
        return Union[NoneLiteral, parameter]


class TypeOrMissing(metaclass=__TypeOrMissing):
    pass
