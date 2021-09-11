import asyncio
import random
from traceback import print_exc

from sqlalchemy.sql.expression import select

import discord
from discord.ext import tasks, commands
from sqlalchemy.orm import joinedload

from src.model.chapter import Chapter
from src.model.project import Project
from src.util.misc import format_number, divide_chunks, BoardPaginator
from src.util.db import get_all


class Loops(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.refreshembed.start()

    def cog_unload(self):
        self.refreshembed.cancel()

    @tasks.loop(seconds=60, reconnect=True)
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
            for curr_proj, x in enumerate(projects):
                stmt = (
                    select(Chapter)
                    .options(
                        joinedload(Chapter.translator),
                        joinedload(Chapter.typesetter),
                        joinedload(Chapter.redrawer),
                        joinedload(Chapter.proofreader),
                    )
                    .filter(Chapter.project_id == x.id)
                    .order_by(Chapter.number.asc())
                )
                chapters = await get_all(session, stmt)
                list_in_progress_project = []
                list_done_project = []
                for y in chapters:
                    done = 0
                    chapter = f" [Raws]({y.link_raw}) |"
                    if not y.translator and not y.link_tl:
                        chapter = chapter + " ~~TL~~ |"
                    elif y.translator and not y.link_tl:
                        chapter = chapter + f" **TL** ({y.translator.name}) |"
                    elif y.link_tl:
                        chapter = "{} [TL ({})]({}) |".format(
                            chapter,
                            y.translator.name if y.translator is not None else "None",
                            y.link_tl,
                        )
                        done += 1
                    if not y.redrawer and not y.link_rd:
                        chapter = chapter + " ~~RD~~ |"
                    elif y.redrawer and not y.link_rd:
                        chapter = chapter + f" **RD** ({y.redrawer.name}) |"
                    elif y.link_rd:
                        chapter = (
                            chapter
                            + f" [RD ({y.redrawer.name if y.redrawer is not None else 'None'})]({y.link_rd}) |"
                        )
                        done += 1
                    if not y.typesetter and not y.link_ts:
                        chapter = chapter + " ~~TS~~ |"
                    elif y.typesetter and not y.link_ts:
                        chapter = chapter + f" **TS** ({y.typesetter.name}) |"
                    elif y.link_ts:
                        chapter = (
                            chapter
                            + f" [TS ({y.typesetter.name if y.typesetter is not None else 'None'})]({y.link_ts}) |"
                        )
                        done += 1
                    if not y.proofreader and not y.link_pr:
                        chapter = chapter + " ~~PR~~ |"
                    elif y.proofreader and not y.link_pr:
                        chapter = chapter + f" **PR** ({y.proofreader.name}) |"
                    elif y.link_pr:
                        chapter = (
                            chapter
                            + f" [PR ({y.proofreader.name if y.proofreader is not None else 'None'})]({y.link_pr}) |"
                        )
                    if y.link_rl:
                        chapter = chapter + f" [QCTS]({y.link_rl})"
                        done += 1
                    else:
                        chapter = chapter + f" ~~QCTS~~"
                    done += 1
                    if chapter and done != 5 and not y.date_release:
                        num = format_number(y.number)
                        chapter = "Chapter {}:{}".format(num, chapter)
                        list_in_progress_project.append(f"{chapter}\n")
                    elif chapter and done == 5 and not y.date_release:
                        num = format_number(y.number)
                        chapter = "Chapter {}:{}".format(num, chapter)
                        list_done_project.append(f"{chapter}\n")
                if not x.color:
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
                    color = discord.Colour(int(x.color, 16))
                project_embed = BoardPaginator(color)
                project_embed.set_author(name=x.title, icon_url=x.icon, url=x.link)
                project_embed.set_thumbnail(
                    x.thumbnail
                    if x.thumbnail
                    else "https://nekyou.mangadex.com/wp-content/uploads/sites/83/2019/06/About-Nekyou.png"
                )
                project_embed.title = "Link to project"
                project_embed.url = x.link
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
            for x, e in enumerate(all_embeds):
                if currlen + len(e) <= 6000:
                    message_embeds[-1].append(e)
                    currlen += len(e)
                else:
                    message_embeds.append([])
                    message_embeds[-1].append(e)
                    currlen = len(e)
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
                self.bot.config["server"]["board_message"] = used_ids
                await self.bot.store_config()
        except Exception as e:
            raise e
        finally:
            await session.close()

    @refreshembed.error
    async def refresherror(self, e):
        ch = await self.bot.fetch_channel(
            self.bot.config["server"]["channels"]["board"]
        )
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
        await ch.send("Restarted task successfully")

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


def setup(bot):
    bot.add_cog(Loops(bot))
