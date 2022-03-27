import discord
import discord.app_commands as ac

from src.util.db import get_all
from src.util.search import searchprojects
from src.model import Project

from sqlalchemy import select
import re


async def chapter_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[ac.Choice[str]]:
    session = interaction.client.Session(autoflush=False, autocommit=False)
    match = re.search(r"^([^\d]*)((?:\d{1,2})?(?:\.\d{1,2})?)$", current)
    projects = (
        await searchprojects(match.group(1), session)
        if match.group(1)
        else await get_all(session, select(Project))
    )
    chapters = []
    for project in projects:
        chapters += list(
            filter(
                lambda c: str(c.number).startswith(match.group(2))
                if match.group(2)
                else True,
                project.chapters,
            )
        )
    res = list(
        map(lambda chapter: f"{chapter.project.title} {chapter.number}", chapters)
    )[:10]
    await session.close()
    return [ac.Choice(name=i, value=i) for i in res]


async def project_autocomplete(inter: discord.Interaction, current: str):
    session = inter.client.Session()
    res = await searchprojects(current, session)
    await session.close()
    return [ac.Choice(name=i.title, value=i.title) for i in res]
