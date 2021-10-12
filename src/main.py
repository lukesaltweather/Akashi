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

with open("src/util/emojis.json", "r") as f:
    emojis = json.load(f)

logger = logging.getLogger("discord")
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename="bot.log", encoding="utf-8", mode="w")
handler.setFormatter(
    logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")
)
logger.addHandler(handler)

loggerBot = logging.getLogger("akashi")
loggerBot.setLevel(logging.INFO)
loggerBot.addHandler(handler)


class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = loggerBot
        self.config = toml.load("config.toml")
        self.logger.info(msg="Loaded Config.")
        self.logger.info(msg="Creating asnypg pool...")
        self.pool = self.loop.run_until_complete(
            asyncpg.create_pool(
                "postgres://Akashi:CWyYxRCvRg5hs@51.15.107.70:5432/akashitest",
                min_size=1,
                max_size=10,
            )
        )
        self.logger.info(msg="Finished setting up asyncpg connection pool.")
        self.logger.info(msg="Setting up SQLAlchemy Sessionmaker...")
        self.Session = sessionmaker(
            create_async_engine(
                self.config["general"]["uri"], pool_size=20, future=True
            ),
            class_=AsyncSession,
        )
        self.logger.info(msg="Finished setting up SQLAlchemy Sessionmaker.")
        self.em = emojis
        self.uptime = datetime.datetime.now()
        self.logger.info(msg="Loading Cogs...")
        self.load_extension("src.cogs.loops")
        self.load_extension("src.cogs.edit")
        self.load_extension("src.cogs.misc")
        self.load_extension("src.cogs.info")
        self.load_extension("src.cogs.add")
        self.load_extension("src.cogs.done")
        self.load_extension("src.cogs.note")
        self.load_extension("src.cogs.help")
        self.load_extension("src.cogs.database")
        self.load_extension("jishaku")
        self.logger.info(msg="Finished loading Cogs.")
        self.logger.info(msg="Init complete.")

    async def get_context(self, message, *, cls=None):
        return await super().get_context(message, cls=CstmContext)

    async def store_config(self):
        async with aiofiles.open("config.toml.new", mode="w") as file:
            await file.write(toml.dumps(self.config))
        os.replace("config.toml.new", "config.toml")
        self.logger.info(msg="Config File overridden.")

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
    logging.getLogger("akashi.db").debug(f"Closing SQLAlchemy Session.")


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
    await bot.wait_until_ready()
    logging.getLogger("akashi").info(f"Login and startup complete.")


@bot.event
async def on_command_error(ctx, error):
    logging.getLogger("akashi.commands").warning(f"Now handling error in main error handler for command {ctx.command.name}.")
    # rollback command's db session
    await ctx.session.rollback()
    await ctx.session.close()
    # This prevents any commands with local handlers being
    # handled here in on_command_error.
    if hasattr(ctx.command, "on_error"):
        logging.getLogger("akashi.commands").info(f"Error for command {ctx.command.name} has already been dealt with in local error handler.")
        return
    error = getattr(error, "original", error)
    logging.getLogger("akashi.commands").error(f"The error that occured for {ctx.command.name}: {type(error)} / {getattr(error, 'message', 'No Message')}.")
    if error is commands.CommandNotFound:
        pass
    elif error is commands.CommandError:
        await ctx.send(error.message or error.__str__)
    elif error is commands.FlagError:
        await ctx.send(error.message or error.__str__)
    else:
        await ctx.send("An unknown error ocurred...")
        logging.getLogger("akashi.commands").critical(f"Error for {ctx.command.name} couldn't be resolved gracefully: Message: {getattr(error, 'message', 'No Message')}; \n Type: {type(error)}; \n String: {str(error)}.")


@bot.command(hidden=True)
@is_admin()
async def restart(ctx):
    logging.getLogger("akashi").info(f"Restarting bot...")
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
            logging.getLogger("akashi").info(f"Added staffmember {before.display_name}.")
        finally:
            await session1.close()

bot.run(bot.config["general"]["bot_key"])
