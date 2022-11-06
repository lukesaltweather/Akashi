import asyncio
import random

import discord
from discord.ext import tasks, commands
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.expression import select

from Akashi.model.chapter import Chapter
from Akashi.model.project import Project
from Akashi.util.db import get_all
from Akashi.util.misc import format_number, divide_chunks, BoardPaginator


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
        try:
            stmt = (
                select(Project)
                .filter(Project.status == "active")
                .order_by(Project.position.asc())
            )
            projects = await get_all(session, stmt)
            all_embeds = list()
            for project in projects:
                stmt = (
                    select(Chapter)
                    .options(
                        joinedload(Chapter.translator),
                        joinedload(Chapter.typesetter),
                        joinedload(Chapter.redrawer),
                        joinedload(Chapter.proofreader),
                    )
                    .filter(Chapter.project_id == project.id)
                    .order_by(Chapter.number.asc())
                )
                chapters = await get_all(session, stmt)
                list_in_progress_project = []
                list_done_project = []
                for chapter in chapters:
                    done = 0
                    chapter_string = f" [Raws]({chapter.link_raw}) |"
                    if not chapter.translator and not chapter.link_tl:
                        chapter_string = chapter_string + " ~~TL~~ |"
                    elif chapter.translator and not chapter.link_tl:
                        chapter_string = (
                            chapter_string + f" **TL** ({chapter.translator.name}) |"
                        )
                    elif chapter.link_tl:
                        chapter_string = "{} [TL ({})]({}) |".format(
                            chapter_string,
                            chapter.translator.name if chapter.translator else "None",
                            chapter.link_tl,
                        )
                        done += 1
                    if not chapter.redrawer and not chapter.link_rd:
                        chapter_string = chapter_string + " ~~RD~~ |"
                    elif chapter.redrawer and not chapter.link_rd:
                        chapter_string = (
                            chapter_string + f" **RD** ({chapter.redrawer.name}) |"
                        )
                    elif chapter.link_rd:
                        chapter_string = (
                            chapter_string
                            + f" [RD ({chapter.redrawer.name if chapter.redrawer else 'None'})]({chapter.link_rd}) |"
                        )
                        done += 1
                    if not chapter.typesetter and not chapter.link_ts:
                        chapter_string = chapter_string + " ~~TS~~ |"
                    elif chapter.typesetter and not chapter.link_ts:
                        chapter_string = (
                            chapter_string + f" **TS** ({chapter.typesetter.name}) |"
                        )
                    elif chapter.link_ts:
                        chapter_string = (
                            chapter_string
                            + f" [TS ({chapter.typesetter.name if chapter.typesetter else 'None'})]({chapter.link_ts}) |"
                        )
                        done += 1
                    if not chapter.proofreader and not chapter.link_pr:
                        chapter_string = chapter_string + " ~~PR~~ |"
                    elif chapter.proofreader and not chapter.link_pr:
                        chapter_string = (
                            chapter_string + f" **PR** ({chapter.proofreader.name}) |"
                        )
                    elif chapter.link_pr:
                        chapter_string = (
                            chapter_string
                            + f" [PR ({chapter.proofreader.name if chapter.proofreader else 'None'})]({chapter.link_pr}) |"
                        )
                    if chapter.link_rl:
                        chapter_string = chapter_string + f" [QCTS]({chapter.link_rl})"
                        done += 1
                    else:
                        chapter_string = chapter_string + f" ~~QCTS~~"
                    done += 1
                    if chapter_string and done != 5 and not chapter.date_release:
                        num = format_number(chapter.number)
                        chapter_string = "Chapter {}:{}".format(num, chapter_string)
                        list_in_progress_project.append(f"{chapter_string}\n")
                    elif chapter_string and done == 5 and not chapter.date_release:
                        num = format_number(chapter.number)
                        chapter_string = "Chapter {}:{}".format(num, chapter_string)
                        list_done_project.append(f"{chapter_string}\n")
                if not project.color:
                    color = random.choice(
                        [
                            discord.Colour.blue(),
                            discord.Colour.green(),
                            discord.Colour.purple(),
                            discord.Colour.dark_red(),
                            discord.Colour.dark_teal(),
                        ]
                    )
                else:
                    color = discord.Colour(int(project.color, 16))
                project_embed = BoardPaginator(color)
                project_embed.set_author(
                    name=project.title, icon_url=project.icon, url=project.link
                )
                project_embed.set_thumbnail(
                    project.thumbnail
                    if project.thumbnail
                    else "https://nekyou.mangadex.com/wp-content/uploads/sites/83/2019/06/About-Nekyou.png"
                )
                project_embed.title = "Link to project"
                project_embed.url = project.link
                if len(list_in_progress_project) != 0:
                    lists = list(divide_chunks(list_in_progress_project, 2))
                    first = True
                    for lis in lists:
                        if first:
                            c = " ".join(b for b in lis)
                            project_embed.add_field(
                                name="Chapters in Progress", value="" + c, inline=False
                            )
                            first = False
                        else:
                            c = " ".join(b for b in lis)
                            project_embed.add_field(
                                name="\u200b", value="" + c, inline=False
                            )
                if len(list_done_project) != 0:
                    lists = list(divide_chunks(list_done_project, 2))
                    first = True
                    for lis in lists:
                        if first:
                            c = " ".join(b for b in lis)
                            project_embed.add_field(
                                name="Chapters ready for release",
                                value="" + c,
                                inline=False,
                            )
                            first = False
                        else:
                            c = " ".join(b for b in lis)
                            project_embed.add_field(
                                name="\u200b", value="" + c, inline=False
                            )
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
            raise embed
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


@staticmethod
async def foundStaff(
    channel: discord.TextChannel, member: str, m: discord.Message, chapter
):
    await m.clear_reactions()
    await m.unpin()
    await m.add_reaction("✅")
    msg = f"`{chapter.project.title} {format_number(chapter.number)}` was assigned to {member}."
    await m.edit(content=msg)
    msg = m.jump_url
    embed = discord.Embed(color=discord.Colour.green())
    embed.set_author(
        name="Assignment",
        icon_url="https://cdn.discordapp.com/icons/345797456614785024/9ef2a960cb5f91439556068b8127512a.webp?size=128",
    )
    embed.description = f"*{chapter.project.title}* {format_number(chapter.number)}\nA staffmember has already been assigned!\n[Jump!]({msg})\n"
    await channel.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Loops(bot))
