import json

import discord
from discord.ext import commands
from sqlalchemy import func
from sqlalchemy.orm import aliased
from src.util.exceptions import MissingRequiredParameter
from src.model.chapter import Chapter
from src.model.message import Message
from src.model.project import Project
from src.model.staff import Staff
from src.util import exceptions
from src.util.search import searchproject, searchstaff, fakesearch, dbstaff
from src.util.misc import FakeUser, formatNumber, make_mentionable, toggle_mentionable
from src.util.checks import is_pr, is_rd, is_tl, is_ts
from abc import abstractmethod

with open('src/util/help.json', 'r') as f:
    jsonhelp = json.load(f)

class General_helper:
    def __init__(self, bot: discord.ext.commands.Bot, ctx: discord.ext.commands.Context, arg: str):
        self.bot = bot
        self.ctx = ctx
        self.session = self.bot.Session()
        arg = arg[1:]
        d = dict(x.split('=', 1) for x in arg.split(' -'))
        if "link" not in d:
            raise MissingRequiredParameter("Link")
        if "id" not in d and "p" in d and "c" in d:
            ts_alias = aliased(Staff)
            rd_alias = aliased(Staff)
            tl_alias = aliased(Staff)
            pr_alias = aliased(Staff)
            query = self.session.query(Chapter).outerjoin(ts_alias, Chapter.typesetter_id == ts_alias.id). \
                outerjoin(rd_alias, Chapter.redrawer_id == rd_alias.id). \
                outerjoin(tl_alias, Chapter.translator_id == tl_alias.id). \
                outerjoin(pr_alias, Chapter.proofreader_id == pr_alias.id). \
                join(Project, Chapter.project_id == Project.id)
            proj = searchproject(d["p"], self.session)
            self.chapter = query.filter(Chapter.project_id == proj.id).filter(float(d["c"]) == Chapter.number).one()
        elif "id" in d:
            ts_alias = aliased(Staff)
            rd_alias = aliased(Staff)
            tl_alias = aliased(Staff)
            pr_alias = aliased(Staff)
            query = self.session.query(Chapter).outerjoin(ts_alias, Chapter.typesetter_id == ts_alias.id). \
                outerjoin(rd_alias, Chapter.redrawer_id == rd_alias.id). \
                outerjoin(tl_alias, Chapter.translator_id == tl_alias.id). \
                outerjoin(pr_alias, Chapter.proofreader_id == pr_alias.id). \
                join(Project, Chapter.project_id == Project.id)
            self.chapter = query.filter(int(d["id"]) == Chapter.id).one()
        else:
            raise MissingRequiredParameter("Project and Chapter or ID")
        self.message = True
        if "msg" in d:
            if d["msg"] in ("True", "true", "t", "yes", "Yes", "y", "Y"):
                self.message = True
            elif d["msg"] in ("False", "false", "n", "f", "N", "F", "no", "No"):
                self.message = False
            else:
                raise ValueError
        self.link = d.get("link")

    def get_chapter(self):
        return self.chapter

    def get_message(self):
        return self.message

    def get_session(self):
        return self.session

    def get_channel(self):
        return self.ctx.guild.get_channel(self.ctx.channel.id)

    def get_context(self):
        return self.ctx

    def get_link(self):
        return self.link

    def get_bot(self):
        return self.bot

class command_helper:
    def __init__(self, helper: General_helper):
        self.helper = helper
        self.bot = helper.get_bot()
        self.ctx = helper.get_context()
        self.channel = helper.get_channel()
        self.message = helper.get_message()
        self.chapter = helper.get_chapter()
        self.session = helper.get_session()

    @abstractmethod
    async def execute(self):
        pass

class TL_helper(command_helper):
    def __init__(self, helper: General_helper):
        super().__init__(helper)
        self.helper = super().helper
        self.channel = super().channel

    async def execute(self):
        """
        Checks and execute action here.
        """
        await self._set_translator()
        self.chapter.link_tl = self.helper.get_link()
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
        self.session.close()

    async def _typesetter(self):
        """
        Called when the redraws are finished, and a typesetter is assigned to the chapter.
        """
        if self.message:
            await self._typesetter_msg()
        else:
            await self._typesetter_no_msg()

    async def _no_redraws(self):
        """
        Called wghen redraws aren't finished, but rd is assigned.
        @return:
        """
        if self.message:
            await self._no_redraws_msg()
        else:
            await self._no_redraws_no_msg()

    async def _no_redrawer(self):
        if self.message:
            await self._no_redrawer_msg()
        else:
            await self._no_redrawer_no_msg()

    async def _no_typesetter(self):
        if self.message:
            await self._no_typesetter_msg()
        else:
            await self._no_typesetter_no_msg()


    async def _typesetter_msg(self):
        """
        Called when the redraws are finished, and a typesetter is assigned to the chapter.
        Will ping typesetter.
        @return: None
        """
        ts = fakesearch(self.chapter.typesetter.discord_id, self.ctx).mention
        await self.channel.send(
            f'{ts}\nThe translation and redraws for `{self.chapter.project.title} {formatNumber(self.chapter.number)}` are done.\nTranslation: {self.chapter.link_tl}\nRedraws:{self.chapter.link_rd}\nNotes: {self.chapter.notes}')
        await self.ctx.message.add_reaction("✅")

    async def _typesetter_no_msg(self):
        """
        Called when the redraws are finished, and a typesetter is assigned to the chapter.
        Will not ping typesetter.
        @return: None
        """
        ts = fakesearch(self.chapter.typesetter.discord_id, self.ctx).display_name
        await self.channel.send(
            f'{ts}\nThe translation and redraws for `{self.chapter.project.title} {formatNumber(self.chapter.number)}` are done.\nTranslation: {self.chapter.link_tl}\nRedraws:{self.chapter.link_rd}\nNotes: {self.chapter.notes}')
        await self.ctx.message.add_reaction("✅")

    async def _no_redraws_msg(self):
        """
        Called when the redraws are aren't finished, but a redrawer is assigned.
        Will ping redrawer.
        @return: None
        """
        await self.ctx.message.add_reaction("✅")
        ts = fakesearch(self.chapter.redrawer.discord_id, self.ctx).mention
        await self.channel.send(
            f'{ts}\nThe translation `{self.chapter.project.title} {formatNumber(self.chapter.number)}` is done.\nRaws: {self.chapter.link_raw}\nNotes: {self.chapter.notes}')

    async def _no_redraws_no_msg(self):
        """
        Called when the redraws are aren't finished, but a redrawer is assigned.
        Will not ping redrawer.
        @return: None
        """
        await self.ctx.message.add_reaction("✅")
        ts = fakesearch(self.chapter.redrawer.discord_id, self.ctx).display_name
        await self.channel.send(
            f'{ts}\nThe translation `{self.chapter.project.title} {formatNumber(self.chapter.number)}` is done.\nRaws: {self.chapter.link_raw}\nNotes: {self.chapter.notes}')

    async def _no_redrawer_msg(self):
        """
        Called when there's no redrawer assigned, and the redraws aren't finished.
        Will ping redrawer role or default redrawer.
        @return: None
        """
        if self.chapter.project.redrawer is None:
            rd = await make_mentionable(self.ctx.guild.get_role(int(self.bot.config["rd_id"])))
            msg = await self.channel.send(f"{rd}\nRedrawer required for `{self.chapter.project.title} {formatNumber(self.chapter.number)}`. React below to assign yourself.")
            await msg.add_reaction("🙋")
            msgdb = Message(msg.id, self.bot.config["rd_id"], "🙋")
            await msg.pin()
            msgdb.chapter = self.chapter.id
            msgdb.created_on = func.now()
            self.session.add(msgdb)
        else:
            rd = fakesearch(self.chapter.project.redrawer.discord_id, self.ctx).mention
            await self.channel.send("Couldn't find a redrawer. Falling back to project defaults.")
            await self.channel.send(
                f'{rd}\nThe translation for `{self.chapter.project.title} {formatNumber(self.chapter.number)}` is done.\nRaws: {self.chapter.link_raw}\nNotes: {self.chapter.notes}')
            await self.ctx.message.add_reaction("✅")
            self.chapter.redrawer = self.chapter.project.redrawer
            self.session.commit()

    async def _no_redrawer_no_msg(self):
        """
        Called when there's no redrawer assigned, and the redraws aren't finished.
        Will not ping anyone.
        @return: None
        """
        if self.chapter.project.redrawer is None:
            rd = await make_mentionable(self.ctx.guild.get_role(int(self.bot.config["rd_id"])))
            msg = await self.channel.send(
                f"{rd}\nRedrawer required for `{self.chapter.project.title} {formatNumber(self.chapter.number)}`. React below to assign yourself.")
            await msg.add_reaction("🙋")
            await toggle_mentionable(self.ctx.guild.get_role(int(self.bot.config["rd_id"])))
            msgdb = Message(msg.id, self.bot.config["rd_id"], "🙋")
            await msg.pin()
            msgdb.chapter = self.chapter.id
            msgdb.created_on = func.now()
            self.session.add(msgdb)
        else:
            rd = fakesearch(self.chapter.project.redrawer.discord_id, self.ctx).display_name
            await self.channel.send("Couldn't find a redrawer. Falling back to project defaults.")
            await self.channel.send(
                f'{rd}\nThe translation for `{self.chapter.project.title} {formatNumber(self.chapter.number)}` is done.\nRaws: {self.chapter.link_raw}\nNotes: {self.chapter.notes}')
            await self.ctx.message.add_reaction("✅")
            self.chapter.redrawer = self.chapter.project.redrawer
            self.session.commit()

    async def _no_typesetter_msg(self):
        """
        Called when redraws are finished, but no typesetter is assigned.
        @return:
        """
        if self.chapter.project.typesetter is None:
            ts = await make_mentionable(self.ctx.guild.get_role(int(self.helper.bot.config["ts_id"])))
            msg = await self.channel.send(
                f"{ts}\nTypesetter required for `{self.chapter.project.title} {formatNumber(self.chapter.number)}`. React below to assign yourself.")
            await msg.add_reaction("🙋")
            await msg.pin()
            msgdb = Message(msg.id, self.helper.bot.config["ts_id"], "🙋")
            msgdb.chapter = self.chapter.id
            msgdb.created_on = func.now()
            self.session.add(msgdb)
        else:
            ts = fakesearch(self.chapter.project.typesetter.discord_id, self.ctx).mention
            await self.channel.send("Couldn't find a typesetter. Falling back to project defaults.")
            await self.channel.send(
                f'{ts}\nThe translation and redraws for `{self.chapter.project.title} {formatNumber(self.chapter.number)}` are done.\nTranslation: {self.chapter.link_tl}\nRedraws:{self.chapter.link_rd}\nNotes: {self.chapter.notes}')
            await self.ctx.message.add_reaction("✅")
            self.chapter.typesetter = self.chapter.project.typesetter

    async def _no_typesetter_no_msg(self):
        """
        Called when redraws are finished, but no typesetter is assigned.
        Will not ping.
        @return:
        """
        if self.chapter.project.typesetter is None:
            ts = await make_mentionable(self.ctx.guild.get_role(int(self.helper.bot.config["ts_id"])))
            msg = await self.channel.send(
                f"{ts}\nTypesetter required for `{self.chapter.project.title} {formatNumber(self.chapter.number)}`. React below to assign yourself.")
            await msg.add_reaction("🙋")
            await msg.pin()
            msgdb = Message(msg.id, self.helper.bot.config["ts_id"], "🙋")
            msgdb.chapter = self.chapter.id
            msgdb.created_on = func.now()
            self.session.add(msgdb)
        else:
            ts = fakesearch(self.chapter.project.typesetter.discord_id, self.ctx).display_name
            await self.channel.send("Couldn't find a typesetter. Falling back to project defaults.")
            await self.channel.send(
                f'{ts}\nThe translation and redraws for `{self.chapter.project.title} {formatNumber(self.chapter.number)}` are done.\nTranslation: {self.chapter.link_tl}\nRedraws:{self.chapter.link_rd}\nNotes: {self.chapter.notes}')
            await self.ctx.message.add_reaction("✅")
            self.chapter.typesetter = self.chapter.project.typesetter

    async def _set_translator(self):
        if self.chapter.translator is None:
            translator = await dbstaff(self.ctx.author.id, self.helper.get_session())
            self.chapter.translator = translator

class TS_helper(command_helper):
    def __init__(self, helper: General_helper):
        self.helper = helper
        super().__init__(helper)

    async def execute(self):
        await self.__set_typesetter()
        self.chapter.link_ts = self.helper.get_link()
        self.chapter.date_ts = func.now()
        if self.chapter.proofreader is None:
            await self.__no_proofreader()
        else:
            await self.__proofreader()
        self.session.commit()
        self.session.close()

    async def __set_typesetter(self):
        if self.chapter.typesetter is None:
            typesetter = await dbstaff(self.ctx.author.id, self.helper.get_session())
            self.chapter.typesetter = typesetter

    async def __no_proofreader(self):
        if self.message:
            await self.__no_proofreader_msg()
        else:
            await self.__no_proofreader_no_msg()

    async def __no_proofreader_msg(self):
        if self.chapter.project.proofreader is None:
            pr = await make_mentionable(self.ctx.guild.get_role(int(self.bot.config["pr_id"])))
            msg = await self.ctx.send(
                f"{pr}\nProofreader required for `{self.chapter.project.title} {formatNumber(self.chapter.number)}`. React below to assign yourself.")
            await msg.add_reaction("🙋")
            await toggle_mentionable(self.ctx.guild.get_role(int(self.bot.config["pr_id"])))
            await msg.pin()
            msgdb = Message(msg.id, self.bot.config["rd_id"], "🙋")
            msgdb.chapter = self.chapter.id
            msgdb.created_on = func.now()
            self.session.add(msgdb)
        else:
            self.chapter.proofreader = self.chapter.project.proofreader
            await self.ctx.send("Couldn't find a proofreader. Falling back to project defaults.")
            await self.ctx.message.add_reaction("✅")
            ts = fakesearch(self.chapter.project.proofreader.discord_id, self.ctx).mention
            await self.ctx.send(
                f"{ts}\n`{self.chapter.project.title} {formatNumber(self.chapter.number)}` is ready to be proofread.\nTypeset: {self.chapter.link_ts}\nTranslation:{self.chapter.link_tl}\nNotes: {self.chapter.notes}")

    async def __no_proofreader_no_msg(self):
        if self.chapter.project.proofreader is None:
            pr = await make_mentionable(self.ctx.guild.get_role(int(self.bot.config["pr_id"])))
            msg = await self.ctx.send(
                f"{pr}\nProofreader required for `{self.chapter.project.title} {formatNumber(self.chapter.number)}`. React below to assign yourself.")
            await msg.add_reaction("🙋")
            await toggle_mentionable(self.ctx.guild.get_role(int(self.bot.config["pr_id"])))
            await msg.pin()
            msgdb = Message(msg.id, self.bot.config["rd_id"], "🙋")
            msgdb.chapter = self.chapter.id
            msgdb.created_on = func.now()
            self.session.add(msgdb)
        else:
            self.chapter.proofreader = self.chapter.project.proofreader
            await self.ctx.send("Couldn't find a proofreader. Falling back to project defaults.")
            await self.ctx.message.add_reaction("✅")
            ts = fakesearch(self.chapter.project.proofreader.discord_id, self.ctx).display_name
            await self.ctx.send(
                f"{ts}\n`{self.chapter.project.title} {formatNumber(self.chapter.number)}` is ready to be proofread.\nTypeset: {self.chapter.link_ts}\nTranslation:{self.chapter.link_tl}\nNotes: {self.chapter.notes}")

    async def __proofreader(self):
        if self.message:
            await self.__proofreader_msg()
        else:
            await self.__proofreader_no_msg()

    async def __proofreader_msg(self):
        ts = fakesearch(self.chapter.proofreader.discord_id, self.ctx).mention
        await self.ctx.send(
            f"{ts}\n`{self.chapter.project.title} {formatNumber(self.chapter.number)}` is ready to be proofread.\nTypeset: {self.chapter.link_ts}\nTranslation:{self.chapter.link_tl}\nNotes: {self.chapter.notes}")

    async def __proofreader_no_msg(self):
        ts = fakesearch(self.chapter.proofreader.discord_id, self.ctx).display_name
        await self.ctx.send(
            f"{ts}\n`{self.chapter.project.title} {formatNumber(self.chapter.number)}` is ready to be proofread.\nTypeset: {self.chapter.link_ts}\nTranslation:{self.chapter.link_tl}\nNotes: {self.chapter.notes}")

class PR_helper(command_helper):
    def __init__(self, helper: General_helper):
        super().__init__(helper)

    async def execute(self):
        await self.__set_proofreader()
        self.chapter.link_pr = self.helper.get_link()
        self.chapter.date_pr = func.now()
        if self.chapter.typesetter is not None:
            await self.__typesetter()
        else:
            await self.__no_typesetter()
        self.session.commit()
        self.session.close()

    async def __set_proofreader(self):
        if self.chapter.proofreader is None:
            proofreader = await dbstaff(self.ctx.author.id, self.helper.get_session())
            self.chapter.proofreader = proofreader

    async def __typesetter(self):
        if self.message:
            await self.__typesetter_msg()
        else:
            await self.__typesetter_no_msg()

    async def __no_typesetter(self):
        await self.ctx.send(f"Something is wrong. Couldn't determine a typesetter. Updated chapter data anyway.")
        await self.ctx.message.add_reaction("❓")

    async def __typesetter_msg(self):
        ts = fakesearch(self.chapter.typesetter.discord_id, self.ctx).mention
        await self.ctx.send(
            f"{ts}\nThe proofread for `{self.chapter.project.title} {formatNumber(self.chapter.number)}` is ready.\nLink: {self.chapter.link_pr}\nNotes: {self.chapter.notes}\nNotes: {self.chapter.notes}")
        await self.ctx.message.add_reaction("✅")

    async def __typesetter_no_msg(self):
        ts = fakesearch(self.chapter.typesetter.discord_id, self.ctx).display_name
        await self.ctx.send(
            f"{ts}\nThe proofread for `{self.chapter.project.title} {formatNumber(self.chapter.number)}` is ready.\nLink: {self.chapter.link_pr}\nNotes: {self.chapter.notes}\nNotes: {self.chapter.notes}")
        await self.ctx.message.add_reaction("✅")

class QCTS_helper(command_helper):
    def __init__(self, helper):
        self.helper = helper
        super().__init__(helper)

    async def execute(self):
        self.chapter.link_rl = self.helper.get_link()
        self.chapter.date_rl = func.now()
        if self.chapter.proofreader is not None:
            await self.__proofreader()
        else:
            await self.__no_proofreader()
        self.session.commit()
        self.session.close()

    async def __proofreader(self):
        if self.message:
            await self.__proofreader_msg()
        else:
            await self.__proofreader_no_msg()

    async def __proofreader_msg(self):
        pr = fakesearch(self.chapter.proofreader.discord_id, self.ctx).mention
        await self.ctx.send(
            f"{pr} \nThe QCTS for `{self.chapter.project.title} {formatNumber(self.chapter.number)}` is ready.\nLink: {self.chapter.link_rl}\nNotes: {self.chapter.notes}\nNotes: {self.chapter.notes}")
        await self.ctx.message.add_reaction("✅")

    async def __proofreader_no_msg(self):
        pr = fakesearch(self.chapter.proofreader.discord_id, self.ctx).display_name
        await self.ctx.send(
            f"{pr} \nThe QCTS for `{self.chapter.project.title} {formatNumber(self.chapter.number)}` is ready.\nLink: {self.chapter.link_rl}\nNotes: {self.chapter.notes}\nNotes: {self.chapter.notes}")
        await self.ctx.message.add_reaction("✅")

    async def __no_proofreader(self):
        await self.ctx.send(f"Something is wrong. Couldn't determine a Proofreader. Updated chapter data anyway.")
        await self.ctx.message.add_reaction("✅")

class RD_helper(command_helper):
    def __init__(self, helper):
        self.helper = helper
        super().__init__(self.helper)
        self.channel = super().channel

    async def execute(self):
        self.chapter.link_rd = self.helper.get_link()
        self.chapter.date_rd = func.now()
        await self.__set_redrawer()
        if self.chapter.link_tl in (None, ""):
            await self.__no_translation()
        else:
            await self.__typesetter()
        self.session.commit()
        self.session.close()

    async def __set_redrawer(self):
        if self.chapter.redrawer is None:
            self.chapter.redrawer = await dbstaff(self.ctx.author.id, self.session)

    async def __no_translation(self):
        await self.ctx.message.add_reaction("✅")
        await self.ctx.send(
            f'\nThe redraws for `{self.chapter.project.title} {formatNumber(self.chapter.number)}` are done but the translation isnt ready.{fakesearch(self.chapter.translator.discord_id, self.ctx).mention}\nRedraws: {self.chapter.link_raw}\nNotes: {self.chapter.notes}')

    async def __typesetter(self):
        if self.chapter.typesetter is None:
            if self.chapter.project.typesetter is not None:
                pass
            else:
                pass
        else:
            pass

class Done(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        worker = ctx.guild.get_role(self.bot.config["neko_workers"])
        ia = worker in ctx.message.author.roles
        ic = ctx.channel.id == self.bot.config["command_channel"]
        guild = ctx.guild is not None
        if ia and ic and guild:
            return True
        elif ic:
            raise exceptions.MissingRequiredPermission("Missing permission `Neko Worker`.")
        elif not guild:
            raise exceptions.MissingRequiredPermission("Missing permission `Server Member`.")

    @commands.command(checks=[is_tl], description=jsonhelp["donetl"]["description"],
                      usage=jsonhelp["donetl"]["usage"], brief=jsonhelp["donetl"]["brief"], help=jsonhelp["donetl"]["help"])
    @commands.max_concurrency(1, per=discord.ext.commands.BucketType.default, wait=True)
    async def donetl(self, ctx, *, arg):
        general = General_helper(self.bot, ctx, arg)
        TL = TL_helper(general)
        await TL.execute()


    @commands.command(checks=[is_ts], description=jsonhelp["donets"]["description"],
                      usage=jsonhelp["donets"]["usage"], brief=jsonhelp["donets"]["brief"], help=jsonhelp["donets"]["help"])
    @commands.max_concurrency(1, per=discord.ext.commands.BucketType.default, wait=True)
    async def donets(self, ctx, *, arg):
        general = General_helper(self.bot, ctx, arg)
        channel = await general.get_channel()
        TS = TS_helper(general)
        await TS.execute()


    @commands.command(checks=[is_pr],description=jsonhelp["donepr"]["description"],
                      usage=jsonhelp["donepr"]["usage"], brief=jsonhelp["donepr"]["brief"], help=jsonhelp["donepr"]["help"])
    @commands.max_concurrency(1, per=discord.ext.commands.BucketType.default, wait=True)
    async def donepr(self, ctx, *, arg):
        helper = General_helper(self.bot, ctx, arg)
        PR = PR_helper(helper)
        await PR.execute()

    @commands.command(checks=[is_ts], description=jsonhelp["doneqcts"]["description"],
                      usage=jsonhelp["doneqcts"]["usage"], brief=jsonhelp["doneqcts"]["brief"], help=jsonhelp["doneqcts"]["help"])
    @commands.max_concurrency(1, per=discord.ext.commands.BucketType.default, wait=True)
    async def doneqcts(self, ctx, *, arg):
        helper = General_helper(self.bot, ctx, arg)
        QCTS = QCTS_helper(helper)
        await QCTS.execute()


    @commands.command(checks=[is_rd], description=jsonhelp["donerd"]["description"],
                      usage=jsonhelp["donerd"]["usage"], brief=jsonhelp["donerd"]["brief"], help=jsonhelp["donerd"]["help"])
    @commands.max_concurrency(1, per=discord.ext.commands.BucketType.default, wait=True)
    async def donerd(self, ctx, *, arg):
        session = self.bot.Session()
        try:
            arg = arg[1:]
            d = dict(x.split('=', 1) for x in arg.split(' -'))
            if "link" not in d:
                raise MissingRequiredParameter("Link")
            if "id" not in d and "p" in d and "c" in d:
                ts_alias = aliased(Staff)
                rd_alias = aliased(Staff)
                tl_alias = aliased(Staff)
                pr_alias = aliased(Staff)
                query = session.query(Chapter).outerjoin(ts_alias, Chapter.typesetter_id == ts_alias.id). \
                    outerjoin(rd_alias, Chapter.redrawer_id == rd_alias.id). \
                    outerjoin(tl_alias, Chapter.translator_id == tl_alias.id). \
                    outerjoin(pr_alias, Chapter.proofreader_id == pr_alias.id). \
                    join(Project, Chapter.project_id == Project.id)
                proj = searchproject(d["p"], session)
                chapter = query.filter(Chapter.project_id == proj.id).filter(float(d["c"]) == Chapter.number).one()
            elif "id" in d:
                ts_alias = aliased(Staff)
                rd_alias = aliased(Staff)
                tl_alias = aliased(Staff)
                pr_alias = aliased(Staff)
                query = session.query(Chapter).outerjoin(ts_alias, Chapter.typesetter_id == ts_alias.id). \
                    outerjoin(rd_alias, Chapter.redrawer_id == rd_alias.id). \
                    outerjoin(tl_alias, Chapter.translator_id == tl_alias.id). \
                    outerjoin(pr_alias, Chapter.proofreader_id == pr_alias.id). \
                    join(Project, Chapter.project_id == Project.id)
                chapter = query.filter(int(d["id"]) == Chapter.id).one()
            else:
                raise MissingRequiredParameter("Project and Chapter or ID")
            if chapter.redrawer is None:
                chapter.redrawer = await searchstaff(ctx.author.id, ctx, session)
            message = True
            if "msg" in d:
                if d["msg"] in ("True", "true", "t", "yes", "Yes", "y", "Y"):
                    message = True
                elif d["msg"] in ("False", "false", "n", "f", "N", "F", "no", "No"):
                    message = False
                else:
                    raise ValueError
            chapter.link_rd = d["link"]
            chapter.date_rd = func.now()
            if chapter.typesetter is not None and chapter.link_tl is not None:
                await ctx.message.add_reaction("✅")
                if message:
                    ts = fakesearch(chapter.typesetter.discord_id, ctx).mention
                    await ctx.send(
                        f'{ts}\nThe redraws for `{chapter.project.title} {formatNumber(chapter.number)}` are done.\nRedraws: {chapter.link_rd}\nTranslation: {chapter.link_tl}\nNotes: {chapter.notes}')
                    embed = discord.Embed(color=discord.Colour.dark_red())
                    embed.add_field(name="\u200b", value=f"```{chapter.notes}```")
                    await ctx.send(embed=embed)
            elif chapter.typesetter is not None and chapter.link_tl is None:
                await ctx.message.add_reaction("✅")
                await ctx.send(
                    f'\nThe redraws for `{chapter.project.title} {formatNumber(chapter.number)}` are done but the translation isnt ready.{fakesearch(chapter.translator.discord_id, ctx).mention}\nRedraws: {chapter.link_raw}\nNotes: {chapter.notes}')
            elif chapter.typesetter is None and chapter.link_tl is not None:
                if chapter.project.typesetter is not None:
                    ts = fakesearch(chapter.project.typesetter.discord_id, ctx).mention
                    if message:
                        await ctx.send("Couldn't find a typesetter. Falling back to project defaults.")
                        await ctx.send(
                            f'{ts}\nThe translation and redraws for `{chapter.project.title} {formatNumber(chapter.number)}` are done.\nRedraws: {chapter.link_rd}\nTranslation: {chapter.link_tl}\nNotes: {chapter.notes}')
                    else:
                        await ctx.send(
                            f'The translation and redraws for `{chapter.project.title} {formatNumber(chapter.number)}` are done.\nRedraws: {chapter.link_rd}\nTranslation: {chapter.link_tl}\nNotes: {chapter.notes}')
                        await ctx.send("Couldn't find a typesetter. Falling back to project defaults.")
                    await ctx.message.add_reaction("✅")
                else:
                    if message:
                        ts = await make_mentionable(ctx.guild.get_role(int(self.bot.config["ts_id"])))
                        msg = await ctx.send(
                            f"{ts}\nTypesetter required for `{chapter.project.title} {formatNumber(chapter.number)}`.\nReact below to assign yourself.")
                        await msg.add_reaction("🙋")
                        await toggle_mentionable(ctx.guild.get_role(int(self.bot.config["ts_id"])))
                        msgdb = Message(msg.id, self.bot.config["ts_id"], "🙋")
                        await msg.pin()
                        msgdb.chapter = chapter.id
                        msgdb.created_on = func.now()
                        session.add(msgdb)
                    else:
                        await ctx.send("No typesetter assigned to this chapter.")
            else:
                msg = await ctx.send(f"Typesetter required for `{chapter.project.title} {formatNumber(chapter.number)}`")
                await msg.add_reaction("🙋")
                await toggle_mentionable(ctx.guild.get_role(int(self.bot.config["ts_id"])))
                await msg.pin()
                msgdb = Message(msg.id, self.bot.config["ts_id"], "🙋")
                msgdb.chapter = chapter.id
                msgdb.created_on = func.now()
                session.add(msgdb)
        finally:
            session.commit()
            session.close()

def setup(Bot):
    Bot.add_cog(Done(Bot))