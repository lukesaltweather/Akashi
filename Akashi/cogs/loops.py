import asyncio

from discord.ext import tasks, commands
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.expression import select

from Akashi.model.chapter import Chapter
from Akashi.model.project import Project
from Akashi.util.board import get_chapter_string, join_chapters
from Akashi.util.db import get_all
from Akashi.util.misc import BoardPaginator


class Loops(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self) -> None:
        self.refreshembed.start()

    def cog_unload(self):
        self.refreshembed.cancel()

    @tasks.loop(seconds=60)
    async def refreshembed(self):
        await self.bot.wait_until_ready()
        session = self.bot.Session()
        used_ids = []
        channel = self.bot.get_channel(self.bot.config["server"]["channels"]["board"])
        all_embeds = list()
        try:
            stmt = (
                select(Project)
                .filter(Project.status == "active")
                .order_by(Project.position.asc())
            )
            projects = await get_all(session, stmt)
            for project in projects:
                stmt = (
                    select(Chapter)
                    .options(
                        joinedload(Chapter.translator),
                        joinedload(Chapter.typesetter),
                        joinedload(Chapter.redrawer),
                        joinedload(Chapter.proofreader),
                        joinedload(Chapter.qualitychecker),
                    )
                    .filter(Chapter.project_id == project.id)
                    .order_by(Chapter.number.asc())
                )
                chapters = await get_all(session, stmt)
                in_progress_chapters = []
                ready_chapters = []

                for chapter in chapters:
                    s = get_chapter_string(chapter)
                    if chapter.link_qcts and not chapter.date_release:
                        ready_chapters.append(s)
                    elif not chapter.date_release:
                        in_progress_chapters.append(s)

                project_embed = BoardPaginator(project)
                if len(in_progress_chapters) != 0:  # -> join_chapters
                    join_chapters(
                        in_progress_chapters, project_embed, "Chapters in Progress"
                    )
                if len(ready_chapters) != 0:
                    join_chapters(ready_chapters, project_embed, "Finished Chapters")
                all_embeds += project_embed.embeds

            currlen = 0
            message_embeds = [[]]
            for embed in all_embeds:
                if currlen + len(embed) <= 6000:
                    message_embeds[-1].append(embed)
                    currlen += len(embed)
                else:
                    message_embeds.append([])
                    message_embeds[-1].append(embed)
                    currlen = len(embed)
            for group in message_embeds:
                message_to_edit_id = None
                for msg in self.bot.config["server"]["board_message"]:
                    if not msg in used_ids:
                        message_to_edit_id = msg
                        used_ids.append(msg)
                        break
                if message_to_edit_id:
                    message = await channel.fetch_message(message_to_edit_id)
                    await message.edit(embeds=group)
                else:
                    new_msg = await channel.send(embeds=group)
                    used_ids.append(new_msg.id)
            if self.bot.config["server"]["board_message"] != used_ids:
                unused_ids = set(self.bot.config["server"]["board_message"]) - set(
                    used_ids
                )
                for msg in unused_ids:
                    message = await channel.fetch_message(msg)
                    await message.delete()
                self.bot.config["server"]["board_message"] = used_ids
                await self.bot.store_config()
        except Exception as embed:
            self.bot.logger.error(embed)
            await session.close()
        finally:
            await session.close()

    @refreshembed.error
    async def refresherror(self, e):
        self.bot.logger.info("Now handling board loop error")
        await self.bot.wait_until_ready()
        ch = await self.bot.fetch_user(self.bot.owner_id)
        await ch.send(f"Board errored with error: {e} {type(e)}")
        try:
            self.refreshembed.cancel()
            await asyncio.sleep(20)
        except Exception as e:
            await ch.send(f"Exception while Cancelling: {e}")
        if self.refreshembed.is_running():
            await ch.send("Task still running!")
        if self.refreshembed.is_being_cancelled():
            await ch.send("Task is being cancelled!")
            await asyncio.sleep(20)
        self.refreshembed.start()
        self.refreshembed.restart()
        await ch.send("Restarted task successfully")

    @refreshembed.before_loop
    async def embed_before_loop(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(Loops(bot))
