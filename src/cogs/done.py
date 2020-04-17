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
from src.util.search import searchproject, searchstaff, fakesearch
from src.util.misc import FakeUser, formatNumber, make_mentionable, toggle_mentionable


class Done(commands.Cog):

    def __init__(self, bot, sessionmaker, config):
        self.bot = bot
        self.Session = sessionmaker
        self.config = config


    async def cog_check(self, ctx):
        worker = ctx.guild.get_role(self.config["neko_workers"])
        ia = worker in ctx.message.author.roles
        ic = ctx.channel.id == self.config["command_channel"]
        guild = ctx.guild is not None
        if ia and ic and guild:
            return True
        elif ic:
            raise exceptions.MissingRequiredPermission("Missing permission `poweruser`.")
        elif not guild:
            raise exceptions.MissingRequiredPermission("Missing permission `Server Member`.")

    @commands.command()
    async def donetl(self, ctx, *, arg):
        session = self.Session()
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
                chapter = query.filter(Chapter.project_id == proj.id).filter(int(d["c"]) == Chapter.number).one()
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
            message = True
            if "msg" in d:
                if d["msg"] in ("True", "true", "t", "yes", "Yes", "y", "Y"):
                    message = True
                elif d["msg"] in ("False", "false", "n", "f", "N", "F", "no", "No"):
                    message = False
                else:
                    raise ValueError
            if chapter.translator is None:
                chapter.translator = await searchstaff(ctx.author.id, ctx, session)
            chapter.link_tl = d["link"]
            chapter.status_tl = "done"
            chapter.date_tl = func.now()
            if chapter.link_rd is not None:
                if chapter.typesetter is not None:
                    if message:
                        ts = fakesearch(chapter.typesetter.discord_id, ctx).mention
                        await ctx.send(
                            f'{ts}\nThe translation and redraws for `{chapter.project.title} {formatNumber(chapter.number)}` are done.\nTranslation: {chapter.link_tl}\nRedraws:{chapter.link_rd}\nNotes: {chapter.notes}')
                    await ctx.message.add_reaction("✅")
                elif chapter.typesetter is None and chapter.project.typesetter is not None:
                    ts = fakesearch(chapter.project.typesetter.discord_id, ctx).mention
                    if message:
                        await ctx.send("Couldn't find a typesetter. Falling back to project defaults.")
                        await ctx.send(
                            f'{ts}\nThe translation and redraws for `{chapter.project.title} {formatNumber(chapter.number)}` are done.\nTranslation: {chapter.link_tl}\nRedraws:{chapter.link_rd}\nNotes: {chapter.notes}')
                    else:
                        await ctx.send("Couldn't find a typesetter. Falling back to project defaults.")
                    await ctx.message.add_reaction("✅")
                else:
                    ts = await make_mentionable(ctx.guild.get_role(int(self.config["ts_id"])))
                    msg = await ctx.send(
                        f"{ts}\nTypesetter required for `{chapter.project.title} {formatNumber(chapter.number)}`. React below to assign yourself.")
                    await msg.add_reaction("🙋")
                    await toggle_mentionable(ctx.guild.get_role(int(self.config["ts_id"])))
                    await msg.pin()
                    msgdb = Message(msg.id, self.config["ts_id"], "🙋")
                    msgdb.chapter = chapter.id
                    msgdb.created_on = func.now()
                    session.add(msgdb)
            else:
                if chapter.redrawer is not None:
                    await ctx.message.add_reaction("✅")
                    if message:
                        ts = fakesearch(chapter.redrawer.discord_id, ctx).mention
                        await ctx.send(
                            f'{ts}\nThe translation `{chapter.project.title} {formatNumber(chapter.number)}` is done.\nRaws: {chapter.link_raw}\nNotes: {chapter.notes}')
                elif chapter.redrawer is None and chapter.project.redrawer is not None:
                    rd = fakesearch(chapter.project.redrawer.discord_id, ctx).mention
                    if message:
                        await ctx.send("Couldn't find a redrawer. Falling back to project defaults.")
                        await ctx.send(
                            f'{rd}\nThe translation for `{chapter.project.title} {formatNumber(chapter.number)}` is done.\nRaws: {chapter.link_raw}\nNotes: {chapter.notes}')
                    else:
                        await ctx.send("Couldn't find a redrawer. Falling back to project defaults.")
                    await ctx.message.add_reaction("✅")
                else:
                    rd = await make_mentionable(ctx.guild.get_role(int(self.config["rd_id"])))
                    msg = await ctx.send(
                        f"{rd}\nRedrawer required for `{chapter.project.title} {formatNumber(chapter.number)}`. React below to assign yourself.")
                    await msg.add_reaction("🙋")
                    await toggle_mentionable(ctx.guild.get_role(int(self.config["rd_id"])))
                    msgdb = Message(msg.id, self.config["rd_id"], "🙋")
                    await msg.pin()
                    msgdb.chapter = chapter.id
                    msgdb.created_on = func.now()
                    session.add(msgdb)
        finally:
            session.commit()
            session.close()


    @commands.command()
    async def donets(self, ctx, *, arg):
        session = self.Session()
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
                chapter = query.filter(Chapter.project_id == proj.id).filter(int(d["c"]) == Chapter.number).one()
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
            if chapter.typesetter is None:
                chapter.typesetter = await searchstaff(ctx.author.id, ctx, session)
            message = True
            if "msg" in d:
                if d["msg"] in ("True", "true", "t", "yes", "Yes", "y", "Y"):
                    message = True
                elif d["msg"] in ("False", "false", "n", "f", "N", "F", "no", "No"):
                    message = False
                else:
                    raise ValueError
            chapter.link_ts = d["link"]
            chapter.date_ts = func.now()
            if chapter.proofreader is not None:
                if message:
                    ts = fakesearch(chapter.proofreader.discord_id, ctx).mention
                    await ctx.send(
                        f"{ts}\n`{chapter.project.title} {formatNumber(chapter.number)}` is ready to be proofread.\nTypeset: {chapter.link_ts}\nTranslation:{chapter.link_tl}\nNotes: {chapter.notes}")
                else:
                    await ctx.send(
                        f"`{chapter.project.title} {formatNumber(chapter.number)}` is ready to be proofread.\nTypeset: {chapter.link_ts}\nTranslation:{chapter.link_tl}\nNotes: {chapter.notes}")
                await ctx.message.add_reaction("✅")
            else:
                if chapter.project.proofreader is not None:
                    chapter.proofreader = chapter.project.proofreader
                    await ctx.send("Couldn't find a proofreader. Falling back to project defaults.")
                    await ctx.message.add_reaction("✅")
                    if message:
                        ts = fakesearch(chapter.project.proofreader.discord_id, ctx).mention
                        await ctx.send(
                            f"{ts}\n`{chapter.project.title} {formatNumber(chapter.number)}` is ready to be proofread.\nTypeset: {chapter.link_ts}\nTranslation:{chapter.link_tl}\nNotes: {chapter.notes}")
                    else:
                        await ctx.send(
                            f"`{chapter.project.title} {formatNumber(chapter.number)}` is ready to be proofread.\nTypeset: {chapter.link_ts}\nTranslation:{chapter.link_tl}\nNotes: {chapter.notes}")
                else:
                    pr = await make_mentionable(ctx.guild.get_role(int(self.config["pr_id"])))
                    msg = await ctx.send(
                        f"{pr}\nProofreader required for `{chapter.project.title} {formatNumber(chapter.number)}`. React below to assign yourself.")
                    await msg.add_reaction("🙋")
                    await toggle_mentionable(ctx.guild.get_role(int(self.config["pr_id"])))
                    await msg.pin()
                    msgdb = Message(msg.id, self.config["rd_id"], "🙋")
                    msgdb.chapter = chapter.id
                    msgdb.created_on = func.now()
                    session.add(msgdb)
        finally:
            session.commit()
            session.close()


    @commands.command()
    async def donepr(self, ctx, *, arg):
        session = self.Session()
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
                chapter = query.filter(Chapter.project_id == proj.id).filter(int(d["c"]) == Chapter.number).one()
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
                raise MissingRequiredParameter("Project and Chapter and ID")
            if chapter.proofreader is None:
                chapter.proofreader = await searchstaff(ctx.author.id, ctx, session)
            message = True
            if "msg" in d:
                if d["msg"] in ("True", "true", "t", "yes", "Yes", "y", "Y"):
                    message = True
                elif d["msg"] in ("False", "false", "n", "f", "N", "F", "no", "No"):
                    message = False
                else:
                    raise ValueError
            chapter.link_pr = d["link"]
            chapter.date_pr = func.now()
            if chapter.typesetter is not None:
                ts = fakesearch(chapter.typesetter.id).mention
                if message:
                    await ctx.send(
                        f"{ts}\nThe proofread for `{chapter.project.title} {formatNumber(chapter.number)}` is ready.\nLink: {chapter.link_pr}\nNotes: {chapter.notes}\nNotes: {chapter.notes}")
                else:
                    await ctx.send(
                        f"The proofread for `{chapter.project.title} {formatNumber(chapter.number)}` is ready.\nLink: {chapter.link_pr}\nNotes: {chapter.notes}\nNotes: {chapter.notes}")
                await ctx.message.add_reaction("✅")
            else:
                await ctx.send(f"Something is wrong. Couldn't determine a typesetter. Updated chapter data anyway.")
                await ctx.message.add_reaction("✅")
        finally:
            session.commit()
            session.close()


    @commands.command()
    async def doneqcts(self, ctx, *, arg):
        session = self.Session()
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
                chapter = query.filter(Chapter.project_id == proj.id).filter(int(d["c"]) == Chapter.number).one()
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
            message = True
            if "msg" in d:
                if d["msg"] in ("True", "true", "t", "yes", "Yes", "y", "Y"):
                    message = True
                elif d["msg"] in ("False", "false", "n", "f", "N", "F", "no", "No"):
                    message = False
                else:
                    raise ValueError
            chapter.link_pr = d["link"]
            chapter.date_pr = func.now()
            if chapter.proofreader is not None:
                pr = fakesearch(chapter.proofreader.id, ctx).mention
                if message:
                    await ctx.send(
                        f"{pr} \nThe QCTS for `{chapter.project.title} {formatNumber(chapter.number)}` is ready.\nLink: {chapter.link_rl}\nNotes: {chapter.notes}\nNotes: {chapter.notes}")
                else:
                    await ctx.send(
                        f"The QCTS for `{chapter.project.title} {formatNumber(chapter.number)}` is ready.\nLink: {chapter.link_rl}\nNotes: {chapter.notes}\nNotes: {chapter.notes}")
                await ctx.message.add_reaction("✅")
            else:
                await ctx.send(f"Something is wrong. Couldn't determine a Proofreader. Updated chapter data anyway.")
                await ctx.message.add_reaction("✅")
        finally:
            session.commit()
            session.close()


    @commands.command()
    async def donerd(self, ctx, *, arg):
        session = self.Session()
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
                chapter = query.filter(Chapter.project_id == proj.id).filter(int(d["c"]) == Chapter.number).one()
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
                        await ctx.send("Couldn't find a redrawer. Falling back to project defaults.")
                    await ctx.message.add_reaction("✅")
                else:
                    if message:
                        ts = await make_mentionable(ctx.guild.get_role(int(self.config["ts_id"])))
                        msg = await ctx.send(
                            f"{ts}\nTypesetter required for `{chapter.project.title} {formatNumber(chapter.number)}`. React below to assign yourself.")
                        await msg.add_reaction("🙋")
                        await toggle_mentionable(ctx.guild.get_role(int(self.config["ts_id"])))
                        msgdb = Message(msg.id, self.config["ts_id"], "🙋")
                        await msg.pin()
                        msgdb.chapter = chapter.id
                        msgdb.created_on = func.now()
                        session.add(msgdb)
                    else:
                        await ctx.send("No typesetter assigned to this chapter.")
            else:
                await ctx.say(f"Typesetter required for `{chapter.project.title} {formatNumber(chapter.number)}`")
        finally:
            session.commit()
            session.close()
