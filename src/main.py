import asyncio
import datetime
import json
import logging
import os
from typing import Optional

import aiofiles
import asyncpg
import discord
import sqlalchemy
import toml
from discord import version_info, Intents
from discord.ext import commands
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from src.model.staff import Staff
from src.util.checks import is_admin
from src.util.context import CstmContext
from src.util.exceptions import (
    MissingRequiredPermission,
    NoResultFound,
    StaffNotFoundError,
    MissingRequiredParameter,
    TagAlreadyExists,
    CancelError,
)

with open("src/util/emojis.json", "r") as f:
    emojis = json.load(f)

logger = logging.getLogger("discord")
logger.setLevel(logging.WARNING)
handler = logging.FileHandler(filename="bot.log", encoding="utf-8", mode="w")
handler.setFormatter(
    logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")
)
logger.addHandler(handler)


class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = toml.load("config.toml")
        self.pool = self.loop.run_until_complete(
            asyncpg.create_pool(
                "postgres://Akashi:CWyYxRCvRg5hs@51.15.107.70:5432/akashitest",
                min_size=1,
                max_size=10,
            )
        )
        self.Session = sessionmaker(
            create_async_engine(
                self.config["general"]["uri"], pool_size=20, future=True
            ),
            class_=AsyncSession,
        )
        self.em = emojis
        self.uptime = datetime.datetime.now()
        self.load_extension("src.cogs.loops")
        self.load_extension("src.cogs.edit")
        self.load_extension("src.cogs.misc")
        self.load_extension("src.cogs.info")
        self.load_extension("src.cogs.add")
        self.load_extension("src.cogs.done")
        self.load_extension("src.cogs.note")
        self.load_extension("src.cogs.help")
        self.load_extension("src.cogs.stats")
        self.load_extension("jishaku")

    async def store_config(self):
        async with aiofiles.open("config.toml.new", mode="w") as file:
            await file.write(toml.dumps(self.config))
        os.replace("config.toml.new", "config.toml")

    async def on_message(self, message):
        ctx = await self.get_context(message, cls=CstmContext)
        await self.invoke(ctx)

    def get_cog_insensitive(self, name):
        """Gets the cog instance requested.

        If the cog is not found, ``None`` is returned instead.

        Parameters
        -----------
        name: :class:`str`
            The name of the cog you are requesting.
            This is equivalent to the name passed via keyword
            argument in class creation or the class name if unspecified.
        """
        a_lower = {k.lower(): v for k, v in self.cogs.items()}
        return a_lower.get(name.lower())


bot = Bot(command_prefix="$", intents=Intents.all())

print(version_info)


@bot.after_invoke
async def after_invoke_hook(ctx: CstmContext):
    await ctx.session.close()


@bot.check
async def globally_block_dms(ctx):
    return ctx.guild is not None


@bot.check
async def only_members(ctx):
    worker = ctx.guild.get_role(ctx.bot.config["server"]["roles"]["member"])
    ia = worker in ctx.message.author.roles
    ic = ctx.channel.id in ctx.bot.config["server"]["channels"]["commands"]
    guild = ctx.guild is not None
    if ia and ic and guild:
        return True
    elif ic:
        raise MissingRequiredPermission("Wrong Channel.")
    elif not guild:
        raise MissingRequiredPermission("Missing permission `Server Member`")


@bot.event
async def on_ready():
    activity = discord.Activity(name="$help", type=discord.ActivityType.playing)
    await bot.change_presence(activity=activity)


# @bot.event
# async def on_command_error(ctx, error):
#     # rollback command's db session
#     ctx.session.rollback()
#     # This prevents any commands with local handlers being
#     # handled here in on_command_error.
#     print(error)
#     if hasattr(ctx.command, "on_error"):
#         return
#     error = getattr(error, "original", error)
#     # match error:
#     #    case commands.CommandError:
#     #        await ctx.send(error)


@bot.command(hidden=True)
@is_admin()
async def restart(ctx):
    os.system("systemctl restart akashi")


@bot.event
async def on_member_update(before: discord.Member, after: discord.Member):
    worker = before.guild.get_role(345799525274746891)
    if worker not in before.roles and worker in after.roles:
        session1 = bot.Session()
        try:
            st = Staff(after.id, after.name)
            session1.add(st)
            await session1.commit()
            channel = before.guild.get_channel_or_thread(390395499355701249)
            await channel.send("Successfully added {} to staff. ".format(after.name))  # type: ignore
        finally:
            await session1.close()


bot.run(bot.config["general"]["bot_key"])
