from typing import TYPE_CHECKING
import zipfile
from io import BytesIO

from discord.ext import commands
from discord import app_commands as ac

import discord
import hondana

from src.model import Chapter
from src.slash.autocomplete import chapter_autocomplete
from src.util.misc import format_number


class Mangadex(commands.Cog, ac.Group):
    def __init__(self, bot) -> None:
        self.bot = bot
        super().__init__()

    @ac.command(name="upload", description="Upload a chapter to mangadex.")
    @ac.describe(
        chapter="The chapter to upload.",
        files="A compressed zip file with all the pages of the chapter.",
    )
    @ac.autocomplete(chapter=chapter_autocomplete)
    @ac.checks.has_role(702185392795025471)
    @ac.rename(files="files")
    async def upload(
        self,
        inter: discord.Interaction,
        chapter: Chapter,
        files: discord.Attachment,
        title: str | None = None,
        volume: float | None = None,
    ):
        await inter.response.defer(thinking=True)
        image_files = []
        file_buffer = BytesIO()
        await files.save(file_buffer, seek_begin=True)
        with zipfile.ZipFile(file_buffer) as z:
            for item in z.infolist():
                image_files.append(z.open(item).read())
        async with self.bot.mangadex_client.upload_session(
            chapter.project.mangadex_id,
            chapter=str(format_number(chapter.number)),
            translated_language="en",
            scanlator_groups=["824b7e1b-1915-4784-aec3-62af709fbd3e"],
            volume=str(volume) if volume else None,
            title=chapter.title if chapter.title else title,
        ) as session:
            await session.upload_images(image_files)
            released_chapter = await session.commit()
        await inter.followup.send(released_chapter.url)


async def setup(bot):
    await bot.add_cog(Mangadex(bot))
