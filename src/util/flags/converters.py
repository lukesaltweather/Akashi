from datetime import datetime

from sqlalchemy.orm import aliased
from sqlalchemy import select

import discord

from discord.ext.commands.errors import ConversionError, BadArgument

from src.model.chapter import Chapter
from src.model.project import Project
from src.model.staff import Staff
from src.util.search import searchproject, searchstaff
from src.util.db import get_one
from src.util.misc import MISSING


class DateTimeConverter(discord.app_commands.Transformer):
    @classmethod
    async def convert(cls, ctx, arg):
        return datetime.strptime(arg, "%Y-%m-%d")

    @classmethod
    async def transform(cls, interaction, value):
        return datetime.strptime(value, "%Y-%m-%d")


class StaffConverter:
    @classmethod
    async def convert(cls, ctx, arg):
        return await searchstaff(arg, ctx, ctx.session)


class ProjectConverter:
    @classmethod
    async def convert(cls, ctx, arg):
        return await searchproject(arg, ctx.session)


class __CommaListMeta(type):
    def __getitem__(cls, arg):
        cls.__type__ = arg
        return cls


class CommaList(metaclass=__CommaListMeta):
    @classmethod
    async def convert(cls, context, arg: str):
        return [cls.__type__(item) for item in arg.replace(" ", "").split(",")]
