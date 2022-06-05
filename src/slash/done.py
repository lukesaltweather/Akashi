import typing as t
from datetime import datetime

import discord
import discord.app_commands as ac
from PIL import Image, ImageDraw
from discord.ext import commands
from sqlalchemy import select

from src.cogs.done import DoneView
from src.model import Chapter, Staff, Note
from src.slash.autocomplete import chapter_autocomplete
from src.util.db import get_one


class DoneHandler:
    def __init__(
        self,
        chapter: Chapter,
        finished_step_staff: Staff,
        step: t.Literal["tl", "rd", "ts", "pr", "qcts"],
        link: str,
        note: str | None,
        session,
        interaction: discord.Interaction,
    ):
        self.finished_step_staff = finished_step_staff
        self.step = step
        self.link = link
        self.note = note
        self.chapter = chapter
        self.next_step: str | None = None
        self.next_staff: Staff | None = None
        self.session = session
        self.interaction = interaction

    def determine_next_step(self):
        if self.step == "tl":
            self.determine_tl_finished()
        elif self.step == "rd":
            self.determine_rd_finished()
        elif self.step == "ts":
            self.determine_ts_finished()
        elif self.step == "pr":
            self.determine_pr_finished()
        elif self.step == "qcts":
            self.determine_qcts_finished()

    def determine_tl_finished(self):
        if self.chapter.link_rd:  # rd are finished, ts next
            self.next_step = "ts"
            self.ts_or_default()
        else:  # rd are not finished, rd next
            self.next_step = "rd"
            self.rd_or_default()

    def determine_rd_finished(self):
        if self.chapter.link_ts:  # ts is finished, pr next bacause tl must be done
            self.next_step = "pr"
            self.pr_or_default()
        elif self.chapter.link_tl:  # tl is finished, ts next
            self.next_step = "ts"
            self.ts_or_default()
        else:  # tl is not finished, tl next
            self.next_step = "tl"
            self.tl_or_default()

    def determine_ts_finished(self):
        if self.chapter.link_rd:  # rd are finished, pr next
            self.next_step = "pr"
            self.pr_or_default()
        else:  # rd are not finished, rd next
            self.next_step = "rd"
            self.rd_or_default()

    def determine_pr_finished(self):
        self.next_step = "qcts"
        self.ts_or_default()

    def determine_qcts_finished(self):
        self.next_step = "rl"

    def tl_or_default(self):
        if self.chapter.tl:
            self.next_staff = self.chapter.tl

    def rd_or_default(self):
        if self.chapter.rd:
            self.next_staff = self.chapter.rd

    def ts_or_default(self):
        if self.chapter.ts:
            self.next_staff = self.chapter.ts

    def pr_or_default(self):
        if self.chapter.pr:
            self.next_staff = self.chapter.pr

    def edit_chapter(self):
        if self.step == "tl":
            self.chapter.link_tl = self.link
            self.chapter.date_tl = datetime.now()
        elif self.step == "rd":
            self.chapter.link_rd = self.link
            self.chapter.date_rd = datetime.now()
        elif self.step == "ts":
            self.chapter.link_ts = self.link
            self.chapter.date_ts = datetime.now()
        elif self.step == "pr":
            self.chapter.link_pr = self.link
            self.chapter.date_pr = datetime.now()
        elif self.step == "qcts":
            self.chapter.link_qcts = self.link
            self.chapter.date_qcts = datetime.now()
        if self.note:
            self.session.add(Note(self.chapter, self.note, self.finished_step_staff))

    def construct_embed(self):
        embed = discord.Embed()

    async def send_card_to_file_room(self):
        image = Image.new("RGB", (800, 600))
        draw = ImageDraw.Draw(image)

        draw.rounded_rectangle(((70, 50), (730, 550)), 10, fill=0x1E1E1E)
        draw.text((100, 100), "Chapter {}".format(self.chapter.number), fill=0xFFFFFF)

    async def prompt_for_confirmation(self):
        embed = discord.Embed(color=discord.Colour.gold())
        preview = (
            f"Notify {self.interaction.guild.get_member(self.next_staff.discord_id).mention} of you having finished {self.chapter.project.title} Ch. {self.chapter.number} | {self.step})"
            if self.next_staff
            else f"Notify Calendars."
        )
        embed.description = f"This will do the following:\n```{preview}```\n\n Press ✉ to mention, 📝 to not mention, ❌ to cancel."
        view = DoneView(
            timeout=15,
            author_id=self.interaction.user.id,
            reacquire=True,
            delete_after=True,
        )
        await self.interaction.followup.send(embed=embed, view=view, ephemeral=True)
        await view.wait()
        if view.value:
            return discord.AllowedMentions(everyone=True, users=True, roles=True)
        elif view.value is False:
            return discord.AllowedMentions(everyone=False, users=False, roles=False)
        elif view.value is None:
            raise discord.app_commands.AppCommandError("Command Cancelled.")

    async def run(self):
        pass


class SlashDoneCog(commands.GroupCog):
    def __init__(self, bot) -> None:
        super().__init__()
        self.bot = bot

    @ac.command(name="chapter", description="Mark a step as done.")
    @ac.autocomplete(chapter=chapter_autocomplete)
    @ac.checks.has_role(345799525274746891)
    @ac.describe(
        step="The step you want to mark as done.",
        link="The link to the finished step.",
        note="A note about the finished step.",
        chapter="The chapter you've completed a step of.",
    )
    async def done(
        self,
        inter: discord.Interaction,
        step: t.Literal["tl", "rd", "pr", "ts", "qcts"],
        chapter: Chapter,
        link: str,
        note: str | None,
    ):
        async with self.bot.Session() as session:
            finished_step_staff = await get_one(
                session, select(Staff).where(Staff.discord_id == inter.user.id)
            )
            handler = DoneHandler(
                chapter, finished_step_staff, step, link, note, session, inter
            )
            await handler.run()


def setup(bot):
    bot.add_cog(SlashDoneCog(bot))
