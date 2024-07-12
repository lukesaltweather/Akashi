import discord
import discord.app_commands as ac
from discord.ext import commands
from sqlalchemy import select

from Akashi.model import Chapter, Project
from Akashi.slash.autocomplete import project_autocomplete, chapter_autocomplete
from Akashi.slash.helper import monitor_changes
from Akashi.util.db import get_one
from Akashi.util.flags.converters import DateTimeConverter
from Akashi.util.search import get_staff_from_discord_id


class EditC(commands.GroupCog, name="edit"):
    def __init__(self, bot) -> None:
        self.bot = bot
        super().__init__()

    @commands.command()
    async def sync(self, ctx):
        await self.bot.tree.sync()
        await ctx.send("Done.")

    @ac.command(name="chapter", description="Edit a chapter")
    @ac.autocomplete(chapter=chapter_autocomplete, to_project=project_autocomplete)
    @ac.checks.has_role(345799525274746891)
    @ac.describe(
        chapter="The chapter to be edited.",
        to_project="The project to move the chapter to.",
        tl="Translator",
        ts="Typesetter",
        rd="Redrawer",
        pr="Proofreader",
        link_tl="Link to Translation",
        link_ts="Link to Typeset",
        link_rd="Link to Redraws",
        link_pr="Link to Proofread Doc",
        link_qcts="Link to Finished Chapter.",
        link_raw="Link to chapter's raws.",
        date_release="The date the chapter was released.",
        date_tl="The date the chapter was translated.",
        date_ts="The date the chapter was typeset.",
        date_rd="The date the chapter was redrawn.",
        date_pr="The date the chapter was proofread.",
        date_qcts="The date the chapter was finished.",
        date_created="The date the chapter's raws were uploaded.",
        title="The title of the chapter.",
        to_chapter="Used for editing the chapter's number.",
    )
    async def chapter(
        self,
        inter: discord.Interaction,
        chapter: Chapter,
        title: str | None,
        tl: discord.Member | None,
        rd: discord.Member | None,
        ts: discord.Member | None,
        pr: discord.Member | None,
        link_tl: str | None,
        link_rd: str | None,
        link_ts: str | None,
        link_pr: str | None,
        link_qcts: str | None,
        link_raw: str | None,
        date_created: DateTimeConverter | None,
        date_tl: DateTimeConverter | None,
        date_rd: DateTimeConverter | None,
        date_ts: DateTimeConverter | None,
        date_pr: DateTimeConverter | None,
        date_qcts: DateTimeConverter | None,
        date_release: DateTimeConverter | None,
        to_project: Project | None,
        to_chapter: float | None,
    ):
        "Edit a chapters properties. Will prompt for confirmation."
        async with self.bot.Session() as session:
            chapter = await get_one(
                session, select(Chapter).where(Chapter.id == chapter.id)
            )
            await inter.response.defer(thinking=True)
            if title is not None:
                chapter.title = title
            if tl is not None:
                chapter.translator = await get_staff_from_discord_id(tl.id, session)
            if rd is not None:
                chapter.redrawer = await get_staff_from_discord_id(rd.id, session)
            if ts is not None:
                chapter.typesetter = await get_staff_from_discord_id(ts.id, session)
            if pr is not None:
                chapter.proofreader = await get_staff_from_discord_id(pr.id, session)
            if link_tl is not None:
                chapter.link_tl = link_tl
            if link_rd is not None:
                chapter.link_rd = link_rd
            if link_ts is not None:
                chapter.link_ts = link_ts
            if link_pr is not None:
                chapter.link_pr = link_pr
            if link_qcts is not None:
                chapter.link_qcts = link_qcts
            if link_raw is not None:
                chapter.link_raw = link_raw
            if date_created is not None:
                chapter.date_created = date_created
            if date_tl is not None:
                chapter.date_tl = date_tl
            if date_rd is not None:
                chapter.date_rd = date_rd
            if date_ts is not None:
                chapter.date_ts = date_ts
            if date_pr is not None:
                chapter.date_pr = date_pr
            if date_qcts is not None:
                chapter.date_qcts = date_qcts
            if date_release is not None:
                chapter.date_release = date_release
            if to_project is not None:
                to_project = await get_one(
                    session, select(Project).where(Project.id == to_project.id)
                )
                chapter.project = to_project
            if to_chapter is not None:
                chapter.number = to_chapter
            image = await chapter.get_report(str(chapter))
            embed1 = discord.Embed(
                color=discord.Colour.dark_blue(),
                title="Do you want to commit these changes to this chapter?",
            )
            embed1.set_image(url="attachment://image.png")
            await monitor_changes(
                chapter,
                embed=embed1,
                file=image,
                inter=inter,
                session=session,
                bot=self.bot,
            )


async def setup(bot):
    await bot.add_cog(EditC(bot))
