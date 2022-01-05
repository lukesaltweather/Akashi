import asyncio
import datetime
import json

import discord
import humanize
from discord.ext import commands
from discord.ext.commands.errors import CommandError
from sqlalchemy import func
from src.model.chapter import Chapter
from src.model.message import Message
from src.model.note import Note
from src.model.staff import Staff
from src.util import exceptions
from src.util.flags.doneflags import DoneFlags, AssignFlags
from src.util.search import fakesearch, dbstaff, searchstaff, discordstaff
from src.util.misc import format_number, MISSING
from src.util.context import CstmContext
from abc import abstractmethod

from src.util.types import staffroles


class command_helper:
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

    @abstractmethod
    async def execute(self):
        pass

    async def confirm(self, preview):
        if not self.skip_confirm:
            embed = discord.Embed(color=discord.Colour.gold())
            embed.description = f"This will do the following:\n```{preview}```\n\n Press ✉ to mention, 📝 to not mention, ❌ to cancel."

            message = await self.ctx.send(embed=embed)

            await message.add_reaction("✉")
            await message.add_reaction("📝")
            await message.add_reaction("❌")
            await asyncio.sleep(delay=0.5)

            def check(reaction, user):
                return user == self.ctx.message.author and (
                    str(reaction.emoji) == "✉" or str(reaction.emoji) == "📝",
                    str(reaction.emoji) == "❌",
                )

            try:
                reaction, user = await self.bot.wait_for(
                    "reaction_add", timeout=30.0, check=check
                )
            except asyncio.TimeoutError:
                self.session.rollback()
                await message.delete()
                raise CommandError(
                    "No reaction from command author. No action was taken."
                )
            else:
                await message.delete()
                if str(reaction.emoji) == "✉":
                    await self.ctx.message.add_reaction("✅")
                    return discord.AllowedMentions(
                        everyone=True, users=True, roles=True
                    )
                elif str(reaction.emoji) == "📝":
                    await self.ctx.message.add_reaction("✅")
                    return discord.AllowedMentions(
                        everyone=False, users=False, roles=False
                    )
                else:
                    raise CommandError("Command Cancelled.")
        else:
            return discord.AllowedMentions(everyone=False, users=False, roles=False)

    def get_emojis(self, chapter):
        em = self.bot.em
        if chapter.link_tl in (None, ""):
            tl = em.get("tlw")
        else:
            tl = em.get("tl")
        if chapter.link_rd in (None, ""):
            rd = em.get("rdw")
        else:
            rd = em.get("rd")
        if chapter.link_ts in (None, ""):
            ts = em.get("tsw")
        else:
            ts = em.get("ts")
        if chapter.link_pr in (None, ""):
            pr = em.get("prw")
        else:
            pr = em.get("pr")
        if chapter.link_rl in (None, ""):
            qcts = em.get("qctsw")
        else:
            qcts = em.get("qcts")

        return f"<:{tl}> - <:{rd}> - <:{ts}> - <:{pr}> - <:{qcts}>"

    async def completed_embed(
        self,
        chapter: Chapter,
        author: discord.Member,
        mem: discord.Member,
        step: str,
        next_step: str,
    ) -> discord.Embed:
        project = chapter.project.title
        notes = "\n".join([f"[{(await Staff.convert(self.ctx, note.author_id)).name} {humanize.naturaldelta(note.created_on - datetime.datetime.now())}] {note.text}" for note in chapter.notes])
        number = chapter.number
        links = {}
        if next_step == "TS":
            links["Redraws"] = chapter.link_rd
            links["Translation"] = chapter.link_ts
        elif next_step == "RD":
            links["Raws"] = chapter.link_raw
            links["Translation"] = chapter.link_tl
        elif next_step == "PR":
            links["Typeset"] = chapter.link_ts
            links["Translation"] = chapter.link_tl
        elif next_step == "QCTS":
            links["Proofread"] = chapter.link_pr
            links["Typeset"] = chapter.link_ts
        elif next_step == "RL":
            links["QCTS"] = chapter.link_rl
        e = discord.Embed(color=discord.Colour.green())
        e.set_author(
            name=f"Next up: {mem.display_name} | {next_step}",
            icon_url=mem.display_avatar.url,
        )
        e.description = f"{author.mention} finished `{project}` Ch. `{format_number(number)}` | {step}\n"
        links = "\n".join(["[%s](%s)" % (key, value) for (key, value) in links.items()])
        e.description = f"{e.description}\n{links}\n\n`Notes:`\n```{notes}```"
        e.description = f"{e.description}\n{self.get_emojis(chapter)}"
        e.set_footer(
            text=f"Step finished by {author.display_name}",
            icon_url=author.display_avatar.url,
        )
        return e


class TL_helper(command_helper):
    async def execute(self):
        """
        Checks and execute action here.
        """
        await self._set_translator()
        self.chapter.link_tl = self.flags.link
        self.chapter.date_tl = func.now()
        self.session.add(Note(self.chapter, self.flags.note, self.ctx.author))
        if not self.chapter.link_rd:
            if self.chapter.redrawer:
                await self._no_redraws()
            else:
                await self._no_redrawer()
        else:
            if self.chapter.typesetter:
                await self._typesetter()
            else:
                await self._no_typesetter()

    async def _typesetter(self):
        """
        Called when the redraws are finished, and a typesetter is assigned to the chapter.
        Will ping typesetter.
        @return: None
        """
        self.message = await self.confirm("Notify Typesetter")
        embed = await self.completed_embed(
            self.chapter,
            self.ctx.author,
            fakesearch(self.chapter.typesetter.discord_id, self.ctx),
            "TL",
            "TS",
        )
        ts = fakesearch(self.chapter.typesetter.discord_id, self.ctx).mention
        await self.channel.send(
            content=f"{ts}", embed=embed, allowed_mentions=self.message
        )

    async def _no_redraws(self):
        """
        Called when the redraws are aren't finished, but a redrawer is assigned.
        Will ping redrawer.
        @return: None
        """
        self.message = await self.confirm("Notify Redrawer")
        embed = await self.completed_embed(
            self.chapter,
            self.ctx.author,
            fakesearch(self.chapter.redrawer.discord_id, self.ctx),
            "TL",
            "RD",
        )
        rd = fakesearch(self.chapter.redrawer.discord_id, self.ctx).mention
        await self.channel.send(
            content=f"{rd}", embed=embed, allowed_mentions=self.message
        )

    async def _no_redrawer(self):
        """
        Called when there's no redrawer assigned, and the redraws aren't finished.
        Will ping redrawer role or default redrawer.
        @return: None
        """
        if self.chapter.project.redrawer is None:
            self.message = await self.confirm("Notify Redrawer Role")
            rd = self.ctx.guild.get_role(self.bot.config["server"]["roles"]["rd"])
            msg = await self.channel.send(
                f"{rd}\nRedrawer required for `{self.chapter.project.title} {format_number(self.chapter.number)}`. React below to assign yourself.",
                allowed_mentions=self.message,
            )
            await msg.add_reaction("🙋")
            msgdb = Message(msg.id, self.bot.config["server"]["roles"]["rd"], "🙋")
            await msg.pin()
            msgdb.chapter = self.chapter.id
            msgdb.created_on = func.now()
            self.session.add(msgdb)
        else:
            self.message = await self.confirm("Notify Default Redrawer")
            rd = fakesearch(self.chapter.project.redrawer.discord_id, self.ctx).mention
            embed = await self.completed_embed(
                self.chapter,
                self.ctx.author,
                fakesearch(self.chapter.project.redrawer.discord_id, self.ctx),
                "TL",
                "RD",
            )
            await self.channel.send(
                content=f"{rd}", embed=embed, allowed_mentions=self.message
            )

            self.chapter.redrawer = self.chapter.project.redrawer

    async def _no_typesetter(self):
        """
        Called when redraws are finished, but no typesetter is assigned.
        @return:
        """
        if self.chapter.project.typesetter is None:
            self.message = await self.confirm("Notify Typesetter Role")
            ts = self.ctx.guild.get_role(self.bot.config["server"]["roles"]["ts"])
            msg = await self.channel.send(
                f"{ts}\nTypesetter required for `{self.chapter.project.title} {format_number(self.chapter.number)}`. React below to assign yourself.",
                allowed_mentions=self.message,
            )
            await msg.add_reaction("🙋")
            await msg.pin()
            msgdb = Message(msg.id, self.bot.config["server"]["roles"]["ts"], "🙋")
            msgdb.chapter = self.chapter.id
            msgdb.created_on = func.now()
            self.session.add(msgdb)
        else:
            self.message = await self.confirm("Notify Default Typesetter")
            ts = fakesearch(
                self.chapter.project.typesetter.discord_id, self.ctx
            ).mention
            embed = await self.completed_embed(
                self.chapter,
                self.ctx.author,
                fakesearch(self.chapter.project.typesetter.discord_id, self.ctx),
                "TL",
                "TS",
            )
            await self.channel.send(
                content=ts, embed=embed, allowed_mentions=self.message
            )
            self.chapter.typesetter = self.chapter.project.typesetter

    async def _set_translator(self):
        if self.chapter.translator is None:
            translator = await dbstaff(self.ctx.author.id, self.session)
            self.chapter.translator = translator


class TS_helper(command_helper):
    async def execute(self):
        await self.__set_typesetter()
        self.chapter.link_ts = self.flags.link
        self.chapter.date_ts = func.now()
        self.session.add(Note(self.chapter, self.flags.note, self.ctx.author))
        if self.chapter.proofreader:
            await self.__proofreader()
        else:

            await self.__no_proofreader()

    async def __set_typesetter(self):
        if self.chapter.typesetter is None:
            typesetter = await dbstaff(self.ctx.author.id, self.session)
            self.chapter.typesetter = typesetter

    async def __no_proofreader(self):
        if self.chapter.project.proofreader is None:
            self.message = await self.confirm("Notify Proofreader Role")
            pr = self.ctx.guild.get_role(self.bot.config["server"]["roles"]["pr"])
            msg = await self.channel.send(
                f"{pr}\nProofreader required for `{self.chapter.project.title} {format_number(self.chapter.number)}`. React below to assign yourself.",
                allowed_mentions=self.message,
            )
            await msg.add_reaction("🙋")
            await msg.pin()
            msgdb = Message(msg.id, self.bot.config["server"]["roles"]["pr"], "🙋")
            msgdb.chapter = self.chapter.id
            msgdb.created_on = func.now()
            self.session.add(msgdb)
        else:
            self.message = await self.confirm("Notify Default Proofreader")
            self.chapter.proofreader = self.chapter.project.proofreader
            ts = fakesearch(
                self.chapter.project.proofreader.discord_id, self.ctx
            ).mention
            embed = await self.completed_embed(
                self.chapter,
                self.ctx.author,
                fakesearch(self.chapter.project.proofreader.discord_id, self.ctx),
                "TS",
                "PR",
            )
            await self.channel.send(
                content=ts, embed=embed, allowed_mentions=self.message
            )

    async def __proofreader(self):
        self.message = await self.confirm("Notify Proofreader")
        ts = fakesearch(self.chapter.proofreader.discord_id, self.ctx).mention
        embed = await self.completed_embed(
            self.chapter,
            self.ctx.author,
            fakesearch(self.chapter.proofreader.discord_id, self.ctx),
            "TS",
            "PR",
        )
        await self.channel.send(content=ts, embed=embed, allowed_mentions=self.message)


class PR_helper(command_helper):
    async def execute(self):
        await self.__set_proofreader()
        self.chapter.link_pr = self.flags.link
        self.chapter.date_pr = func.now()
        self.session.add(Note(self.chapter, self.flags.note, self.ctx.author))
        if self.chapter.typesetter:
            await self.__typesetter()
        else:
            await self.__no_typesetter()

    async def __set_proofreader(self):
        if self.chapter.proofreader is None:
            proofreader = await dbstaff(self.ctx.author.id, self.session)
            self.chapter.proofreader = proofreader

    async def __no_typesetter(self):
        await self.channel.send(
            f"Something is wrong. Couldn't determine a typesetter. Updated chapter data anyway."
        )
        await self.ctx.message.add_reaction("❓")

    async def __typesetter(self):
        self.message = await self.confirm("Notify OG Typesetter")
        ts = fakesearch(self.chapter.typesetter.discord_id, self.ctx).mention
        embed = await self.completed_embed(
            self.chapter,
            self.ctx.author,
            fakesearch(self.chapter.typesetter.discord_id, self.ctx),
            "PR",
            "QCTS",
        )
        await self.channel.send(content=ts, embed=embed, allowed_mentions=self.message)


class QCTS_helper(command_helper):
    async def execute(self):
        self.chapter.link_rl = self.flags.link
        self.chapter.date_rl = func.now()
        self.session.add(Note(self.chapter, self.flags.note, self.ctx.author))
        if self.chapter.proofreader:
            await self.__proofreader()
        else:
            await self.__no_proofreader()

    async def __proofreader(self):
        self.message = await self.confirm("Notify Proofreader")
        pr = fakesearch(self.chapter.proofreader.discord_id, self.ctx).mention
        embed = await self.completed_embed(
            self.chapter,
            self.ctx.author,
            fakesearch(self.chapter.proofreader.discord_id, self.ctx),
            "QCTS",
            "PR",
        )
        await self.channel.send(content=pr, embed=embed, allowed_mentions=self.message)

    async def __no_proofreader(self):
        self.message = await self.confirm("Error: No Proofreader to notify")
        await self.channel.send(
            f"Something is wrong. Couldn't determine a Proofreader. Updated chapter data anyway."
        )
        await self.ctx.message.add_reaction("❓")


class RD_helper(command_helper):
    async def execute(self):
        self.chapter.link_rd = self.flags.link
        self.chapter.date_rd = func.now()
        await self.__set_redrawer()
        if self.chapter.link_tl in (None, ""):
            if self.chapter.translator is not None:
                await self.__no_translation()
            else:
                await self.__no_translator()
        else:
            if self.chapter.typesetter is not None:
                await self.__typesetter()
            else:
                await self.__no_typesetter()

    async def __set_redrawer(self):
        if self.chapter.redrawer is None:
            self.chapter.redrawer = await dbstaff(self.ctx.author.id, self.session)

    async def __no_translation(self):
        self.message = await self.confirm(
            "No Translation available. Notifies Translator."
        )
        tl = fakesearch(self.chapter.translator.discord_id, self.ctx).mention
        embed = await self.completed_embed(
            self.chapter,
            self.ctx.author,
            fakesearch(self.chapter.translator.discord_id, self.ctx),
            "RD",
            "TL",
        )
        await self.channel.send(content=tl, embed=embed, allowed_mentions=self.message)

    async def __no_translator(self):
        calendar = self.ctx.guild.get_role(453730138056556544)
        self.message = await self.confirm("No Translator assigned. Notifies Calendars.")
        tl = calendar.mention
        embed = await self.completed_embed(
            self.chapter,
            self.ctx.author,
            fakesearch(345845639663583252, self.ctx),
            "RD",
            "TL",
        )
        await self.channel.send(content=tl, embed=embed, allowed_mentions=self.message)

    async def __typesetter(self):
        self.message = await self.confirm("Notify Typesetter")
        embed = await self.completed_embed(
            self.chapter,
            self.ctx.author,
            fakesearch(self.chapter.typesetter.discord_id, self.ctx),
            "RD",
            "TS",
        )
        await self.channel.send(embed=embed)

    async def __no_typesetter(self):
        if self.chapter.project.typesetter is not None:
            self.message = await self.confirm("Mention Default Typesetter")

            ts = fakesearch(
                self.chapter.project.typesetter.discord_id, self.ctx
            ).mention
            embed = await self.completed_embed(
                self.chapter,
                self.ctx.author,
                fakesearch(self.chapter.project.typesetter.discord_id, self.ctx),
                "PR",
                "QCTS",
            )
            await self.channel.send(
                content=ts, embed=embed, allowed_mentions=self.message
            )

        else:
            self.message = await self.confirm("Notify Typesetter Role")
            ts = self.ctx.guild.get_role(self.bot.config["server"]["roles"]["ts"])
            msg = await self.channel.send(
                f"{ts}\nTypesetter required for `{self.chapter.project.title} {format_number(self.chapter.number)}`.\nReact below to assign yourself.",
                allowed_mentions=self.message,
            )
            await msg.add_reaction("🙋")
            msgdb = Message(msg.id, self.bot.config["server"]["roles"]["ts"], "🙋")
            await msg.pin()
            msgdb.chapter = self.chapter.id
            msgdb.created_on = func.now()
            self.session.add(msgdb)


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

        [FURTHER EXPLAINING TODO]

        Required Role
        =====================
        Role `Neko Workers`.

        Arguments
        ===========
        Required
        ---------
        :chapter: The chapter to edit, in format: projectName chapterNbr
        :step: The step that was finished. Can be one of: tl, rd, ts, pr or qcts.

        Optional
        ----------
        :note: Add a note to the chapters notes.
        """
        if flags.step == "tl":
            TL = TL_helper(ctx, flags)
            await TL.execute()
        elif flags.step == "ts":
            TS = TS_helper(ctx, flags)
            await TS.execute()
        elif flags.step == "pr":
            PR = PR_helper(ctx, flags)
            await PR.execute()
        elif flags.step == "qcts":
            QCTS = QCTS_helper(ctx, flags)
            await QCTS.execute()
        elif flags.step == "rd":
            RD = RD_helper(ctx, flags)
            await RD.execute()
        await ctx.session.commit()

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
        elif step == "rd"  and not chapter.redrawer:
            chapter.redrawer = staff
        elif step == "ts"  and not chapter.typesetter:
            chapter.typesetter = staff
        elif step in ("qc", "pr")  and not chapter.proofreader:
            chapter.proofreader = staff
        else:
            raise CommandError("A staffmember has already been assigned for this step.\nConsider using $editchapter to edit the staffmember for a step.")
        await ctx.prompt_and_commit(text=f"Do you really want to assign {'yourself' if staff.discord_id == ctx.author.id else staff.name} "
        f"as the {staffroles.get(step, 'Proofreader')} for {chapter}?", color=discord.Colour.dark_magenta())




def setup(Bot):
    Bot.add_cog(Done(Bot))
