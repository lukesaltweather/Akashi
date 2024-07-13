import datetime
import typing as t

import discord
import humanize
from discord.ext import commands
from discord.ext.commands.errors import CommandError

from Akashi.model.chapter import Chapter
from Akashi.model.note import Note
from Akashi.model.staff import Staff
from Akashi.util.context import CstmContext
from Akashi.util.flags.doneflags import DoneFlags, AssignFlags
from Akashi.util.misc import format_number
from Akashi.util.search import (
    fakesearch,
    get_staff_from_discord_id,
)
from Akashi.util.types import staffroles


class Color:
    gray = 30
    red = 31
    green = 32
    yellow = 33
    white = 37


class DoneView(discord.ui.View):
    def __init__(
        self,
        *,
        timeout: float,
        author_id: int,
        reacquire: bool,
        delete_after: bool,
    ) -> None:
        super().__init__(timeout=timeout)
        self.value: t.Optional[bool] = None
        self.delete_after: bool = delete_after
        self.author_id: int = author_id
        self.reacquire: bool = reacquire
        self.message: t.Optional[discord.Message] = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user and interaction.user.id == self.author_id:
            return True
        else:
            await interaction.response.send_message(
                "This confirmation dialog is not for you.", ephemeral=True
            )
            return False

    async def on_timeout(self) -> None:
        if self.delete_after and self.message:
            await self.message.delete()

    @discord.ui.button(label="Notify", style=discord.ButtonStyle.green, emoji="✉")
    async def ping_mention(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        self.value = True
        await interaction.response.defer()
        if self.delete_after:
            await interaction.delete_original_response()
        self.stop()

    @discord.ui.button(
        label="Don't Notify", style=discord.ButtonStyle.green, emoji="📝"
    )
    async def ping_no_mention(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        self.value = False
        await interaction.response.defer()
        if self.delete_after:
            await interaction.delete_original_response()
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red, emoji="❌")
    async def cancel(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        self.value = None
        await interaction.response.defer()
        if self.delete_after:
            await interaction.delete_original_response()
        self.stop()


def get_progress_text(chapter):
    s = f"```ansi\n\u001b[{0};{Color.green if chapter.link_tl else Color.red}mTL\u001b[0m » "
    s += f"\u001b[{0};{Color.green if chapter.link_pr else Color.red}mPR\u001b[0m » "
    s += f"\u001b[{0};{Color.green if chapter.link_rd else Color.red}mRD\u001b[0m » "
    s += f"\u001b[{0};{Color.green if chapter.link_ts else Color.red}mTS\u001b[0m » "
    s += f"\u001b[{0};{Color.green if chapter.link_qc else Color.red}mQC\u001b[0m » "
    s += (
        f"\u001b[{0};{Color.green if chapter.link_qcts else Color.red}mQCTS\u001b[0m```"
    )
    return s


def determine_next_step(finished_step: str, chapter: Chapter) -> str:
    if finished_step == "tl":
        if chapter.link_pr and not chapter.link_rd:
            return "rd"
        elif chapter.link_pr and chapter.link_rd:
            return "ts"
        elif not chapter.link_rd and not chapter.link_pr:
            return "pr"
        return "pr"
    elif finished_step == "pr":
        if not chapter.link_rd:
            return "rd"
        return "ts"
    elif finished_step == "rd":
        return "ts"
    elif finished_step == "ts":
        return "qc"
    elif finished_step == "qc":
        return "qcts"
    elif finished_step == "qcts":
        return None
    elif finished_step == "release":
        return None


def determine_next_in_line(next_step, chapter):
    if next_step == "pr":
        return chapter.proofreader.discord_id if chapter.proofreader else None
    elif next_step == "ts":
        return chapter.typesetter.discord_id if chapter.typesetter else None
    elif next_step == "rd":
        return chapter.redrawer.discord_id if chapter.redrawer else None
    elif next_step == "qc":
        return chapter.qualitychecker.discord_id if chapter.qualitychecker else None
    elif next_step == "qcts":
        return chapter.typesetter.discord_id


def get_links(next_step, chapter):
    links = {}
    if next_step == "ts":
        links["Redraws"] = chapter.link_rd
        links["Translation"] = chapter.link_ts
    elif next_step == "rd":
        links["Raws"] = chapter.link_raw
        links["Translation"] = chapter.link_tl
    elif next_step == "pr":
        links["Translation"] = chapter.link_tl
    elif next_step == "qc":
        links["Proofread"] = chapter.link_pr
        links["Translation"] = chapter.link_tl
        links["Typeset"] = chapter.link_ts
    elif next_step == "qcts":
        links["Proofread"] = chapter.link_pr
        links["Translation"] = chapter.link_tl
        links["Typeset"] = chapter.link_ts
    elif next_step == "tl":
        links["QCTS"] = chapter.link_rl
    return links


class DoneCommand:
    def __init__(self, ctx: CstmContext, flags: DoneFlags):
        self.bot = ctx.bot
        self.ctx = ctx
        self.channel = ctx.guild.get_channel(
            self.bot.config["server"]["channels"]["updates"]
        )
        self.message = ctx.message
        self.chapter = flags.chapter
        self.session = ctx.session
        self.skip_confirm = flags.skipconfirm
        self.flags = flags
        self.finished_step = flags.step
        self.progress_text = None
        self.next_step = determine_next_step(self.finished_step, self.chapter)
        self.next_in_line = determine_next_in_line(self.next_step, self.chapter)

    async def run(self):
        self.edit_chapter()
        self.progress_text = get_progress_text(self.chapter)
        if not self.next_in_line:
            await self.check_project_for_next_staffmember()
        if self.next_in_line:
            await self.send_to_file_room_with_next_staffmember()
        else:
            await self.send_to_file_room_without_next_staffmember()

    async def check_project_for_next_staffmember(self):
        staff = None
        if self.next_step == "tl":
            staff = self.chapter.project.translator
            self.chapter.translator = staff
        elif self.next_step == "pr":
            staff = self.chapter.project.proofreader
            self.chapter.proofreader = staff
        elif self.next_step == "rd":
            staff = self.chapter.project.redrawer
            self.chapter.redrawer = staff
        elif self.next_step == "ts":
            staff = self.chapter.project.typesetter
            self.chapter.typesetter = staff
        elif self.next_step == "qc":
            staff = await get_staff_from_discord_id(
                358244935041810443, self.ctx.session
            )
            self.chapter.qualitychecker = staff
        if staff:
            self.next_in_line = staff.discord_id

    def edit_chapter(self):
        if self.finished_step == "tl":
            self.chapter.link_tl = self.flags.link
            self.chapter.date_tl = datetime.datetime.now()
        elif self.finished_step == "pr":
            self.chapter.link_pr = self.flags.link
            self.chapter.date_pr = datetime.datetime.now()
        elif self.finished_step == "rd":
            self.chapter.link_rd = self.flags.link
            self.chapter.date_rd = datetime.datetime.now()
        elif self.finished_step == "ts":
            self.chapter.link_ts = self.flags.link
            self.chapter.date_ts = datetime.datetime.now()
        elif self.finished_step == "qc":
            self.chapter.link_qc = self.flags.link
            self.chapter.date_qc = datetime.datetime.now()
        elif self.finished_step == "qcts":
            self.chapter.link_qcts = self.flags.link
            self.chapter.date_qcts = datetime.datetime.now()
        elif self.finished_step == "release":
            self.chapter.date_release = datetime.datetime.now()

    async def confirm(self, preview):
        if not self.skip_confirm:
            embed = discord.Embed(color=discord.Colour.gold())
            embed.description = f"This will do the following:\n```{preview}```\n\n Press ✉ to mention, 📝 to not mention, ❌ to cancel."
            view = DoneView(
                timeout=15,
                author_id=self.ctx.author.id,
                reacquire=True,
                delete_after=True,
            )
            message = await self.ctx.send(embed=embed, view=view)
            await view.wait()
            if view.value:
                await self.ctx.message.add_reaction("✅")
                return discord.AllowedMentions(everyone=True, users=True, roles=True)
            elif view.value is False:
                await self.ctx.message.add_reaction("✅")
                return discord.AllowedMentions(everyone=False, users=False, roles=False)
            elif view.value is None:
                raise CommandError("Command Cancelled.")
        else:
            return discord.AllowedMentions(everyone=False, users=False, roles=False)

    async def get_notes(self):
        notes = "\n".join(
            [
                f"[{(await Staff.convert(self.ctx, note.author.discord_id)).name} {humanize.naturaldelta(note.created_on - datetime.datetime.now())} ago] {note.text}"
                for note in self.chapter.notes
            ]
        )
        return notes

    async def send_to_file_room_with_next_staffmember(
        self,
    ) -> discord.Embed:
        mem = fakesearch(self.next_in_line, self.ctx)
        project = self.chapter.project.title
        notes = await self.get_notes()
        number = self.chapter.number
        links = get_links(self.next_step, self.chapter)
        e = discord.Embed(color=discord.Colour.green())

        e.set_author(
            name=f"Next up: {mem.display_name} | {self.next_step}",
            icon_url=mem.display_avatar.url,
        )
        e.description = f"{self.ctx.author.mention} finished `{project}` Ch. `{format_number(number)}` | {self.finished_step.upper()}\n"
        links = "\n".join(["[%s](%s)" % (key, value) for (key, value) in links.items()])
        if notes:
            e.description = f"{e.description}\n{links}\n\n`Notes:`\n```{notes}```"
        e.description = f"{e.description}\n{self.progress_text}"
        e.set_footer(
            text=f"Step finished by {self.ctx.author.display_name}",
            icon_url=self.ctx.author.display_avatar.url,
        )
        await self.channel.send(
            content=f"{mem.mention}",
            embed=e,
            allowed_mentions=await self.confirm(f"Notify {mem.display_name}"),
        )

    async def send_to_file_room_without_next_staffmember(
        self,
    ) -> discord.Embed:
        project = self.chapter.project.title
        links = get_links(self.next_step, self.chapter)
        notes = await self.get_notes()
        number = self.chapter.number
        e = discord.Embed(color=discord.Colour.green())

        e.set_author(
            name=f"No next staffmember",
        )
        e.description = f"{self.ctx.author.mention} finished `{project}` Ch. `{format_number(number)}` | {self.finished_step.upper()}\n"
        links = "\n".join(["[%s](%s)" % (key, value) for (key, value) in links.items()])
        if notes:
            e.description = f"{e.description}\n{links}\n\n`Notes:`\n```{notes}```"
        e.description = f"{e.description}\n{self.progress_text}"
        e.set_footer(
            text=f"Step finished by {self.ctx.author.display_name}",
            icon_url=self.ctx.author.display_avatar.url,
        )
        await self.channel.send(
            content=f"<@&453730138056556544>",
            embed=e,
            allowed_mentions=await self.confirm(f"Notify calendars"),
        )


class Done(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.max_concurrency(1, per=discord.ext.commands.BucketType.guild, wait=True)
    async def done(self, ctx: CstmContext, *, flags: DoneFlags):
        """
        Description
        ==============
        Mark a specific step of a chapter as finished.
        Will prompt for an answer, click on the corresponding emoji reaction.
        The options are: Ping the next member with a proper notification appearing for them,
        or instead ping, but don't send out a (for some people annoying) notification.

        Required Role
        =====================
        Role `Neko Workers`.

        Arguments
        ===========
        Required
        ---------
        :chapter:
            | The chapter to edit, in format: projectName chapterNbr [:doc:`/Types/chapter`]
        :step:
            | The step you have finished. Can be one of: tl, rd, ts, pr or qc. [:doc:`/Types/literals`]
        :link:
            | The link to the folder on box. [:doc:`/Types/Text`]

        Optional
        ----------
        :note:
            | Add a note to the chapters notes. [:doc:`/Types/Text`]
        """
        if flags.note is not None:
            ctx.session.add(
                Note(
                    flags.chapter,
                    flags.note,
                    await get_staff_from_discord_id(ctx.author.id, ctx.session),
                )
            )

        cmd = DoneCommand(ctx, flags)
        await cmd.run()

        await ctx.notify(flags.chapter)
        await ctx.session.commit()
        await ctx.success()

    @commands.command(aliases=["claim", "take"])
    async def assign(self, ctx: CstmContext, *, flags: AssignFlags):
        """
        Description
        ==============
        Assign a staffmember (or yourself) for a step on a chapter.

        Required Role
        =====================
        Role `Neko Workers`.

        Arguments
        ===========
        Required
        ---------
        :chapter:
            | The chapter to edit, in format: projectName chapterNbr [:doc:`/Types/chapter`]
        :step:
            | The step to assign the staffmember to. Can be one of: tl, rd, ts, pr or qc. [:doc:`/Types/literals`]
        :link:
            | The link to the folder on box. [:doc:`/Types/Text`]
        Optional
        ----------
        :staff:
            | The staffmember to assign. If omitted, the command's author is assigned instead. [:doc:`/Types/literals`]
        """
        chapter = flags.chapter
        staff = flags.staff
        step = flags.step
        if not staff:
            staff = await Staff.convert(ctx, ctx.author.id)
        if step == "tl" and not chapter.translator:
            chapter.translator = staff
        elif step == "rd" and not chapter.redrawer:
            chapter.redrawer = staff
        elif step == "ts" and not chapter.typesetter:
            chapter.typesetter = staff
        elif step in ("qc", "pr") and not chapter.proofreader:
            chapter.proofreader = staff
        else:
            raise CommandError(
                "A staffmember has already been assigned for this step.\nConsider using $editchapter to edit the staffmember for a step."
            )
        await ctx.monitor_changes(
            text=f"Do you really want to assign {'yourself' if staff.discord_id == ctx.author.id else staff.name} "
            f"as the {staffroles.get(step, 'Proofreader')} for {chapter}?",
            color=discord.Colour.dark_magenta(),
            entity=chapter,
        )


async def setup(Bot):
    await Bot.add_cog(Done(Bot))
