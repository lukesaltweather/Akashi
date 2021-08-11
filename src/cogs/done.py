import asyncio
import json

import discord
from discord.ext import commands
from sqlalchemy import func
from src.model.chapter import Chapter
from src.model.message import Message
from src.util import exceptions
from src.util.flags.doneflags import DoneFlags
from src.util.search import fakesearch, dbstaff
from src.util.misc import formatNumber, make_mentionable
from src.util.context import CstmContext
from abc import abstractmethod

with open('src/util/help.json', 'r') as f:
    jsonhelp = json.load(f)

class command_helper:
    def __init__(self, ctx: CstmContext, flags: DoneFlags):
        self.bot = ctx.bot
        self.ctx = ctx
        self.channel = ctx.guild.get_channel(self.bot.config.get("file_room", 408848958232723467))
        self.message = ctx.message
        self.chapter = flags.chapter
        self.session = ctx.session
        self.skip_confirm = flags.skipconfirm
        self.flags = flags

    @abstractmethod
    async def execute(self):
        pass

    async def confirm(self, preview):
        if self.skip_confirm is None:
            embed = discord.Embed(color=discord.Colour.gold())
            embed.description = f"This will do the following:\n```{preview}```\n\n Press ✉ to mention, 📝 to not mention, ❌ to cancel."

            message = await self.ctx.send(embed=embed)

            await message.add_reaction("✉")
            await message.add_reaction("📝")
            await message.add_reaction("❌")
            await asyncio.sleep(delay=0.5)

            def check(reaction, user):
                return user == self.ctx.message.author and (str(reaction.emoji) == '✉' or str(reaction.emoji) == '📝', str(reaction.emoji) == '❌')

            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
            except asyncio.TimeoutError:
                self.session.rollback()
                await message.delete()
                raise RuntimeError("No reaction from command author. No action was taken.")
            else:
                await message.delete()
                if str(reaction.emoji) == "✉":
                    await self.ctx.message.add_reaction("✅")
                    return discord.AllowedMentions(everyone=True, users=True, roles=True)
                elif str(reaction.emoji) == "📝":
                    await self.ctx.message.add_reaction("✅")
                    return discord.AllowedMentions(everyone=False, users=False, roles=False)
                else:
                    self.session.rollback()
                    raise RuntimeError("Command Cancelled.")
        else:
            if self.skip_confirm:
                return discord.AllowedMentions(everyone=True, users=True, roles=True)
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

    def completed_embed(self, chapter: Chapter, author: discord.Member, mem: discord.Member, step: str, next_step: str) -> discord.Embed:
        project = chapter.project.title
        notes = chapter.notes
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
        e.set_author(name=f"Next up: {mem.display_name} | {next_step}", icon_url=mem.avatar_url)
        e.description=f"{author.mention} finished `{project}` Ch. `{formatNumber(number)}` | {step}\n"
        links = '\n'.join(['[%s](%s)' % (key, value) for (key, value) in links.items()])
        e.description=f"{e.description}\n{links}\n\n`Notes:`\n```{notes}```"
        e.description=f"{e.description}\n{self.get_emojis(chapter)}"
        e.set_footer(text=f"Step finished by {author.display_name}", icon_url=author.avatar_url)
        return e


class TL_helper(command_helper):
    async def execute(self):
        """
        Checks and execute action here.
        """
        try:
            await self._set_translator()
            self.chapter.link_tl = self.flags.link
            self.chapter.date_tl = func.now()
            if self.chapter.link_rd is None or self.chapter.link_rd == "":
                if self.chapter.redrawer is not None:
                    await self._no_redraws()
                else:
                    await self._no_redrawer()
            else:
                if self.chapter.typesetter is not None:
                    await self._typesetter()
                else:
                    await self._no_typesetter()
            self.session.commit()
        except RuntimeError as e:
            raise RuntimeError(str(e))
        finally:
            self.session.close()

    async def _typesetter(self):
        """
        Called when the redraws are finished, and a typesetter is assigned to the chapter.
        Will ping typesetter.
        @return: None
        """
        self.message = await self.confirm("Notify Typesetter")
        embed = self.completed_embed(self.chapter, self.ctx.author, fakesearch(self.chapter.typesetter.discord_id, self.ctx), "TL", "TS")
        ts = fakesearch(self.chapter.typesetter.discord_id, self.ctx).mention
        await self.channel.send(content=f"{ts}", embed=embed, allowed_mentions=self.message)

    async def _no_redraws(self):
        """
        Called when the redraws are aren't finished, but a redrawer is assigned.
        Will ping redrawer.
        @return: None
        """
        self.message = await self.confirm("Notify Redrawer")
        embed = self.completed_embed(self.chapter, self.ctx.author, fakesearch(self.chapter.redrawer.discord_id, self.ctx), "TL", "RD")
        rd = fakesearch(self.chapter.redrawer.discord_id, self.ctx).mention
        await self.channel.send(content=f"{rd}", embed=embed, allowed_mentions=self.message)

    async def _no_redrawer(self):
        """
        Called when there's no redrawer assigned, and the redraws aren't finished.
        Will ping redrawer role or default redrawer.
        @return: None
        """
        if self.chapter.project.redrawer is None:
            self.message = await self.confirm("Notify Redrawer Role")
            rd = await make_mentionable(self.ctx.guild.get_role(int(self.bot.config["rd_id"])))
            msg = await self.channel.send(f"{rd}\nRedrawer required for `{self.chapter.project.title} {formatNumber(self.chapter.number)}`. React below to assign yourself.", allowed_mentions=self.message)
            await msg.add_reaction("🙋")
            msgdb = Message(msg.id, self.bot.config["rd_id"], "🙋")
            await msg.pin()
            msgdb.chapter = self.chapter.id
            msgdb.created_on = func.now()
            self.session.add(msgdb)
        else:
            self.message = await self.confirm("Notify Default Redrawer")
            rd = fakesearch(self.chapter.project.redrawer.discord_id, self.ctx).mention
            embed = self.completed_embed(self.chapter, self.ctx.author, fakesearch(self.chapter.project.redrawer.discord_id, self.ctx), "TL", "RD")
            await self.channel.send(content=f"{rd}", embed=embed, allowed_mentions=self.message)

            self.chapter.redrawer = self.chapter.project.redrawer
            self.session.commit()

    async def _no_typesetter(self):
        """
        Called when redraws are finished, but no typesetter is assigned.
        @return:
        """
        if self.chapter.project.typesetter is None:
            self.message = await self.confirm("Notify Typesetter Role")
            ts = await make_mentionable(self.ctx.guild.get_role(int(self.bot.config["ts_id"])))
            msg = await self.channel.send(
                f"{ts}\nTypesetter required for `{self.chapter.project.title} {formatNumber(self.chapter.number)}`. React below to assign yourself.", allowed_mentions=self.message)
            await msg.add_reaction("🙋")
            await msg.pin()
            msgdb = Message(msg.id, self.bot.config["ts_id"], "🙋")
            msgdb.chapter = self.chapter.id
            msgdb.created_on = func.now()
            self.session.add(msgdb)
        else:
            self.message = await self.confirm("Notify Default Typesetter")
            ts = fakesearch(self.chapter.project.typesetter.discord_id, self.ctx).mention
            embed = self.completed_embed(self.chapter, self.ctx.author, fakesearch(self.chapter.project.typesetter.discord_id, self.ctx), "TL", "TS")
            await self.channel.send(content=ts, embed=embed, allowed_mentions=self.message)
            self.chapter.typesetter = self.chapter.project.typesetter

    async def _set_translator(self):
        if self.chapter.translator is None:
            translator = await dbstaff(self.ctx.author.id, self.session)
            self.chapter.translator = translator

class TS_helper(command_helper):
    async def execute(self):
        try:
            await self.__set_typesetter()
            self.chapter.link_ts = self.flags.link
            self.chapter.date_ts = func.now()
            if self.chapter.proofreader is None:
                await self.__no_proofreader()
            else:
                await self.__proofreader()
            self.session.commit()
        except RuntimeError as e:
            raise RuntimeError(str(e))
        finally:
            self.session.close()

    async def __set_typesetter(self):
        if self.chapter.typesetter is None:
            typesetter = await dbstaff(self.ctx.author.id, self.session)
            self.chapter.typesetter = typesetter

    async def __no_proofreader(self):
        if self.chapter.project.proofreader is None:
            self.message = await self.confirm("Notify Proofreader Role")
            pr = await make_mentionable(self.ctx.guild.get_role(int(self.bot.config["pr_id"])))
            msg = await self.channel.send(
                f"{pr}\nProofreader required for `{self.chapter.project.title} {formatNumber(self.chapter.number)}`. React below to assign yourself.", allowed_mentions=self.message)
            await msg.add_reaction("🙋")
            await msg.pin()
            msgdb = Message(msg.id, self.bot.config["pr_id"], "🙋")
            msgdb.chapter = self.chapter.id
            msgdb.created_on = func.now()
            self.session.add(msgdb)
        else:
            self.message = await self.confirm("Notify Default Proofreader")
            self.chapter.proofreader = self.chapter.project.proofreader
            ts = fakesearch(self.chapter.project.proofreader.discord_id, self.ctx).mention
            embed = self.completed_embed(self.chapter, self.ctx.author, fakesearch(self.chapter.project.proofreader.discord_id, self.ctx), "TS", "PR")
            await self.channel.send(content=ts, embed=embed, allowed_mentions=self.message)

    async def __proofreader(self):
        self.message = await self.confirm("Notify Proofreader")
        ts = fakesearch(self.chapter.proofreader.discord_id, self.ctx).mention
        embed = self.completed_embed(self.chapter, self.ctx.author,
                                     fakesearch(self.chapter.proofreader.discord_id, self.ctx), "TS", "PR")
        await self.channel.send(content=ts, embed=embed, allowed_mentions=self.message)

class PR_helper(command_helper):
    async def execute(self):
        try:
            await self.__set_proofreader()
            self.chapter.link_pr = self.flags.link
            self.chapter.date_pr = func.now()
            if self.chapter.typesetter is not None:
                await self.__typesetter()
            else:
                await self.__no_typesetter()
            self.session.commit()
        except RuntimeError as e:
            raise RuntimeError(str(e))
        finally:
            self.session.close()

    async def __set_proofreader(self):
        if self.chapter.proofreader is None:
            proofreader = await dbstaff(self.ctx.author.id, self.session)
            self.chapter.proofreader = proofreader

    async def __no_typesetter(self):
        await self.channel.send(f"Something is wrong. Couldn't determine a typesetter. Updated chapter data anyway.")
        await self.ctx.message.add_reaction("❓")

    async def __typesetter(self):
        self.message = await self.confirm("Notify OG Typesetter")
        ts = fakesearch(self.chapter.typesetter.discord_id, self.ctx).mention
        embed = self.completed_embed(self.chapter, self.ctx.author,
                                     fakesearch(self.chapter.typesetter.discord_id, self.ctx), "PR", "QCTS")
        await self.channel.send(content=ts, embed=embed, allowed_mentions=self.message)

class QCTS_helper(command_helper):
    async def execute(self):
        try:
            self.chapter.link_rl = self.flags.link
            self.chapter.date_rl = func.now()
            if self.chapter.proofreader is not None:
                await self.__proofreader()
            else:
                await self.__no_proofreader()
            self.session.commit()
        except RuntimeError as e:
            raise RuntimeError(str(e))
        finally:
            self.session.close()

    async def __proofreader(self):
        self.message = await self.confirm("Notify Proofreader")
        pr = fakesearch(self.chapter.proofreader.discord_id, self.ctx).mention
        embed = self.completed_embed(self.chapter, self.ctx.author,
                                     fakesearch(self.chapter.proofreader.discord_id, self.ctx), "QCTS", "PR")
        await self.channel.send(content=pr, embed=embed, allowed_mentions=self.message)

    async def __no_proofreader(self):
        self.message = await self.confirm("Error: No Proofreader to notify")
        await self.channel.send(f"Something is wrong. Couldn't determine a Proofreader. Updated chapter data anyway.")
        await self.ctx.message.add_reaction("❓")

class RD_helper(command_helper):

    async def execute(self):
        try:
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
            self.session.commit()
        except RuntimeError as e:
            raise RuntimeError(str(e))
        finally:
            self.session.close()

    async def __set_redrawer(self):
        if self.chapter.redrawer is None:
            self.chapter.redrawer = await dbstaff(self.ctx.author.id, self.session)

    async def __no_translation(self):
        self.message = await self.confirm("No Translation available. Notifies Translator.")
        tl = fakesearch(self.chapter.translator.discord_id, self.ctx).mention
        embed = self.completed_embed(self.chapter, self.ctx.author,
                                     fakesearch(self.chapter.translator.discord_id, self.ctx), "RD", "TL")
        await self.channel.send(content=tl,embed=embed,allowed_mentions=self.message)

    async def __no_translator(self):
        calendar = self.ctx.guild.get_role(453730138056556544)
        self.message = await self.confirm("No Translator assigned. Notifies Calendars.")
        tl = calendar.mention
        embed = self.completed_embed(self.chapter, self.ctx.author,
                                     fakesearch(345845639663583252, self.ctx), "RD", "TL")
        await self.channel.send(content=tl,embed=embed,allowed_mentions=self.message)

    async def __typesetter(self):
        self.message = await self.confirm("Notify Typesetter")
        embed = self.completed_embed(self.chapter, self.ctx.author, fakesearch(self.chapter.typesetter.discord_id, self.ctx), "RD", "TS")
        await self.channel.send(embed=embed)

    async def __no_typesetter(self):
        if self.chapter.project.typesetter is not None:
            self.message = await self.confirm("Mention Default Typesetter")

            ts = fakesearch(self.chapter.project.typesetter.discord_id, self.ctx).mention
            embed = self.completed_embed(self.chapter, self.ctx.author,
                                         fakesearch(self.chapter.project.typesetter.discord_id, self.ctx), "PR", "QCTS")
            await self.channel.send(content=ts, embed=embed, allowed_mentions=self.message)

        else:
            self.message = await self.confirm("Notify Typesetter Role")
            ts = await make_mentionable(self.ctx.guild.get_role(int(self.bot.config["ts_id"])))
            msg = await self.channel.send(
                f"{ts}\nTypesetter required for `{self.chapter.project.title} {formatNumber(self.chapter.number)}`.\nReact below to assign yourself.", allowed_mentions=self.message)
            await msg.add_reaction("🙋")
            msgdb = Message(msg.id, self.bot.config["ts_id"], "🙋")
            await msg.pin()
            msgdb.chapter = self.chapter.id
            msgdb.created_on = func.now()
            self.session.add(msgdb)

class Done(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        worker = ctx.guild.get_role(self.bot.config["neko_workers"])
        herder = ctx.guild.get_role(345798301322575882)
        ia = (worker in ctx.message.author.roles) or (herder in ctx.message.author.roles)
        ic = ctx.channel.id == self.bot.config["command_channel"]
        guild = ctx.guild is not None
        if ia and ic and guild:
            return True
        elif ic:
            raise exceptions.MissingRequiredPermission("Missing permission `Neko Worker`.")
        elif not guild:
            raise exceptions.MissingRequiredPermission("Missing permission `Server Member`.")

    @commands.command(description=jsonhelp["donetl"]["description"],
                      usage=jsonhelp["donetl"]["usage"], brief=jsonhelp["donetl"]["brief"], help=jsonhelp["donetl"]["help"])
    @commands.max_concurrency(1, per=discord.ext.commands.BucketType.guild, wait=True)
    async def donetl(self, ctx, *, flags: DoneFlags):
        TL = TL_helper(ctx, flags)
        await TL.execute()


    @commands.command(description=jsonhelp["donets"]["description"],
                      usage=jsonhelp["donets"]["usage"], brief=jsonhelp["donets"]["brief"], help=jsonhelp["donets"]["help"])
    @commands.max_concurrency(1, per=discord.ext.commands.BucketType.guild, wait=True)
    async def donets(self, ctx, *, flags: DoneFlags):
        TS = TS_helper(ctx, flags)
        await TS.execute()


    @commands.command(description=jsonhelp["donepr"]["description"],
                      usage=jsonhelp["donepr"]["usage"], brief=jsonhelp["donepr"]["brief"], help=jsonhelp["donepr"]["help"])
    @commands.max_concurrency(1, per=discord.ext.commands.BucketType.guild, wait=True)
    async def donepr(self, ctx, *, flags: DoneFlags):
        PR = PR_helper(ctx, flags)
        await PR.execute()

    @commands.command(description=jsonhelp["doneqcts"]["description"],
                      usage=jsonhelp["doneqcts"]["usage"], brief=jsonhelp["doneqcts"]["brief"], help=jsonhelp["doneqcts"]["help"])
    @commands.max_concurrency(1, per=discord.ext.commands.BucketType.guild, wait=True)
    async def doneqcts(self, ctx, *, flags: DoneFlags):
        QCTS = QCTS_helper(ctx, flags)
        await QCTS.execute()

    @commands.command(description=jsonhelp["donerd"]["description"],
                      usage=jsonhelp["donerd"]["usage"], brief=jsonhelp["donerd"]["brief"], help=jsonhelp["donerd"]["help"])
    @commands.max_concurrency(1, per=discord.ext.commands.BucketType.guild, wait=True)
    async def donerd(self, ctx, *, flags: DoneFlags):
        RD = RD_helper(ctx, flags)
        await RD.execute()

def setup(Bot):
    Bot.add_cog(Done(Bot))