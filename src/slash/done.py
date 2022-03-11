import typing as t
import re

from sqlalchemy import select

import discord
import discord.app_commands as ac
from discord.ext import commands

from src.model import Chapter, Project
from src.util.search import searchprojects
from src.util.db import get_all


class DoneHandler:
    def __init__(self, session, chapter, finished_step_staff, step, link):
        self.next_staff_mem = None
        self.current_staff_mem = None
        self.finished_step = None
        self.next_step = None
        self.info_text = None
        self.default_staff_mem = False

    def determine_next_step(self):
        pass

    def determine_info_text(self):
        pass

    def tl_or_default(self):
        pass

    def rd_or_default(self):
        pass

    def ts_or_default(self):
        pass

    def pr_or_default(self):
        pass

    async def run(self):
        pass


class SlashDoneCog(commands.Cog):
    def __init__(self, bot) -> None:
        super().__init__()
        self.bot = bot

    @ac.command()
    async def done(
        self,
        inter: discord.Interaction,
        step: t.Literal["tl", "rd", "pr", "ts", "qcts"],
        chapter: str,
        link: str,
    ):
        handler = DoneHandler()
        resonse_embed = await handler.run()

    @done.autocomplete("chapter")
    async def autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
        namespace: discord.app_commands.Namespace,
    ) -> list[ac.Choice[str]]:
        session = self.bot.Session(autoflush=False, autocommit=False)
        match = re.search(r"^([^\d]*)(\d+\.?\d*)?$", current)
        projects = (
            await searchprojects(match.group(0), session)
            if match.group(0)
            else await get_all(session, select(Project))
        )
        chapters = []
        for project in projects:
            chapters += list(
                filter(
                    lambda c: str(c.number).startswith(match.group(1))
                    if match.group(1).rstrip()
                    else True,
                    project.chapters,
                )
            )
        res = list(
            map(lambda chapter: f"{chapter.project.title} {chapter.number}", chapters)
        )[:25]
        await session.close()
        return [ac.Choice(name=i, value=i) for i in res]


def setup(bot):
    bot.add_cog(SlashDoneCog(bot))
