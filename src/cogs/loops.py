import datetime
import json
import random
import time

import discord
from discord.ext import tasks , commands
from sqlalchemy.orm import joinedload

from src.model.chapter import Chapter
from src.model.message import Message
from src.model.project import Project
from src.model.timer import Reminder
from src.util.misc import formatNumber, divide_chunks, BoardPaginator


class Loops(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.refreshembed.start()
        self.deletemessages.start()
        self.reminder.start()

    def cog_unload(self):
        self.refreshembed.cancel()
        self.deletemessages.cancel()
        self.reminder.cancel()

    @tasks.loop(minutes=1)
    async def reminder(self):
        session = self.bot.Session()
        try:
            reminders = session.query(Reminder).all()
            for reminder in reminders:
                if reminder.date - datetime.datetime.utcnow() <= datetime.timedelta(seconds=30):
                    author = await self.bot.fetch_user(reminder.author)
                    await (await self.bot.fetch_user(reminder.to_remind)).send(f"Hey! {author.name} tasked me with reminding you of:\n```{reminder.msg}```")
                    session.delete(reminder)
                    session.commit()
        except Exception as e:
            raise e
        finally:
            session.close()


    @tasks.loop(minutes=5)
    async def deletemessages(self):
        session = self.bot.Session()
        try:
            channel = self.bot.get_channel(self.bot.config["file_room"])
            messages = session.query(Message).all()
            for message in messages:
                chapter = session.query(Chapter).filter(Chapter.id == message.chapter).one()
                if message.awaiting == self.bot.config.get("tl_id") and chapter.translator is not None:
                    session.delete(message)
                    await self.foundStaff(channel, chapter.translator.name, await channel.fetch_message(message.message_id), chapter)
                elif message.awaiting == self.bot.config.get("rd_id") and chapter.redrawer is not None:
                    session.delete(message)
                    await self.foundStaff(channel, chapter.redrawer.name, await channel.fetch_message(message.message_id), chapter)
                elif message.awaiting == self.bot.config.get("ts_id") and chapter.typesetter is not None:
                    session.delete(message)
                    await self.foundStaff(channel, chapter.typesetter.name, await channel.fetch_message(message.message_id), chapter)
                elif message.awaiting == self.bot.config.get("pr_id") and chapter.proofreader is not None:
                    session.delete(message)
                    await self.foundStaff(channel, chapter.proofreader.name, await channel.fetch_message(message.message_id), chapter)
                else:
                    if message.created_on < (datetime.datetime.utcnow() - datetime.timedelta(hours=48)) and message.reminder:
                        m = await channel.fetch_message(message.message_id)
                        await m.clear_reactions()
                        await m.unpin()
                        await m.add_reaction("❌")
                        msg = m.jump_url
                        embed = discord.Embed(color=discord.Colour.red())
                        embed.set_author(name="Assignment",
                                         icon_url="https://cdn.discordapp.com/icons/345797456614785024/9ef2a960cb5f91439556068b8127512a.webp?size=128")
                        wordy = (self.bot.get_user(345845639663583252)).mention
                        embed.description = f"*{chapter.project.title}* {formatNumber(chapter.number)}\nNo staffmember assigned themselves to Chapter.\n[Jump!]({msg})\n"
                        await channel.send(embed=embed, content=wordy)
                        session.delete(message)
                    elif message.created_on < (datetime.datetime.utcnow() - datetime.timedelta(hours=24)) and not message.reminder:
                        m = await channel.fetch_message(message.message_id)
                        msg = m.jump_url
                        embed = discord.Embed(color=discord.Colour.red())
                        embed.set_author(name="Assignment Reminder",
                                         icon_url="https://cdn.discordapp.com/icons/345797456614785024/9ef2a960cb5f91439556068b8127512a.webp?size=128")
                        who = {self.bot.config["ts_id"]: "Typesetter",
                               self.bot.config["rd_id"]: "Redrawer",
                               self.bot.config["tl_id"]: "Translator",
                               self.bot.config["pr_id"]: "Proofreader",
                               }
                        embed.description = f"*{chapter.project.title}* {formatNumber(chapter.number)}\nStill requires a {who.get(int(message.awaiting))}!\n[Jump!]({msg})\n"
                        await channel.send(embed=embed)
                        message.reminder = True
                    else:
                        pass
            session.commit()
        except Exception as e:
            raise e
        finally:
            session.close()

    @tasks.loop(seconds=60)
    async def refreshembed(self):
        with open('src/util/board.json', 'r') as f:
            messages = json.load(f)
        ch = self.bot.get_channel(self.bot.config['board_channel'])
        mes = list()
        for value in messages.get("0", list()):
            msg = await ch.fetch_message(value)
            mes.append(msg)
        session = self.bot.Session()
        try:
            projects = session.query(Project).filter \
                (Project.status == "active").order_by(Project.position.asc()).all()
            embeds = list()
            for x in projects:
                chapters = session.query(Chapter).options(
                    joinedload(Chapter.translator),
                    joinedload(Chapter.typesetter),
                    joinedload(Chapter.redrawer),
                    joinedload(Chapter.proofreader)). \
                    filter(Chapter.project_id == x.id).order_by(Chapter.number.asc()).all()
                list_in_progress_project = []
                list_done_project = []
                for y in chapters:
                    done = 0
                    chapter = f" [Raws]({y.link_raw}) |"
                    if y.translator is None and y.link_tl is None:
                        chapter = chapter + " ~~TL~~ |"
                    elif y.translator is not None and y.link_tl is None:
                        chapter = chapter + f" **TL** ({y.translator.name}) |"
                    elif y.link_tl is not None:
                        chapter = "{} [TL ({})]({}) |".format(chapter,
                                                              y.translator.name if y.translator is not None else "None",
                                                              y.link_tl)
                        done += 1
                    if y.redrawer is None and y.link_rd is None:
                        chapter = chapter + " ~~RD~~ |"
                    elif y.redrawer is not None and y.link_rd is None:
                        chapter = chapter + f" **RD** ({y.redrawer.name}) |"
                    elif y.link_rd is not None:
                        chapter = chapter + f" [RD ({y.redrawer.name if y.redrawer is not None else 'None'})]({y.link_rd}) |"
                        done += 1
                    if y.typesetter is None and y.link_ts is None:
                        chapter = chapter + " ~~TS~~ |"
                    elif y.typesetter is not None and y.link_ts is None:
                        chapter = chapter + f" **TS** ({y.typesetter.name}) |"
                    elif y.link_ts is not None:
                        chapter = chapter + f" [TS ({y.typesetter.name if y.typesetter is not None else 'None'})]({y.link_ts}) |"
                        done += 1
                    if y.proofreader is None and y.link_pr is None:
                        chapter = chapter + " ~~PR~~ |"
                    elif y.proofreader is not None and y.link_pr is None:
                        chapter = chapter + f" **PR** ({y.proofreader.name}) |"
                    elif y.link_pr is not None:
                        chapter = chapter + f" [PR ({y.proofreader.name if y.proofreader is not None else 'None'})]({y.link_pr}) |"
                    if y.link_rl is not None:
                        chapter = chapter + f" [QCTS]({y.link_rl})"
                        done += 1
                    done += 1
                    if chapter != "" and done != 5 and y.date_release is None:
                        num = formatNumber(y.number)
                        chapter = "Chapter {}:{}".format(num, chapter)
                        list_in_progress_project.append(f"{chapter}\n")
                    elif chapter != "" and done == 5 and y.date_release is None:
                        num = formatNumber(y.number)
                        chapter = "Chapter {}:{}".format(num, chapter)
                        list_done_project.append(f"{chapter}\n")
                if x.color is None:
                    color = random.choice([discord.Colour.blue(), discord.Colour.green(), discord.Colour.purple(),
                                           discord.Colour.dark_red(), discord.Colour.dark_teal()])
                else:
                    color = discord.Colour(int(x.color, 16))
                embed = BoardPaginator(color)
                embed.set_author(name=x.title, icon_url=x.icon, url=x.link)
                embed.set_thumbnail(x.thumbnail)
                embed.title = "Link to project"
                embed.url = x.link
                if len(list_in_progress_project) != 0:
                    lists = list(divide_chunks(list_in_progress_project, 2))
                    first = True
                    for lis in lists:
                        if first:
                            c = " ".join(b for b in lis)
                            embed.add_field(name="Chapters in Progress", value="" + c, inline=False)
                            first = False
                        else:
                            c = " ".join(b for b in lis)
                            embed.add_field(name="\u200b", value="" + c, inline=False)
                if len(list_done_project) != 0:
                    lists = list(divide_chunks(list_done_project, 2))
                    first = True
                    for lis in lists:
                        if first:
                            c = " ".join(b for b in lis)
                            embed.add_field(name="Chapters ready for release", value="" + c, inline=False)
                            first = False
                        else:
                            c = " ".join(b for b in lis)
                            embed.add_field(name="\u200b", value="" + c, inline=False)
                for e in embed.embed():
                    embeds.append(e)
            new_messages = list()
            for embed in embeds:
                if len(mes) > 0:
                    m = mes.pop(0)
                    await m.edit(embed=embed)
                    new_messages.append(m.id)
                else:
                    message = await ch.send(embed=embed)
                    new_messages.append(message.id)
            for i in range(0, len(mes)):
                m = mes.pop(-1)
                print(f"Deleted: {m.id}")
                await m.delete()
            messages = {"0":new_messages}
            with open('src/util/board.json', 'w') as f:
                json.dump(messages, f, indent=4)
        except Exception as e:
            raise e
        finally:
            session.close()

    @staticmethod
    async def foundStaff(channel: discord.TextChannel, member: str, m: discord.Message, chapter):
        await m.clear_reactions()
        await m.unpin()
        await m.add_reaction("✅")
        msg = f"`{chapter.project.title} {formatNumber(chapter.number)}` was assigned to {member}."
        await m.edit(content=msg)
        msg = m.jump_url
        embed = discord.Embed(color=discord.Colour.green())
        embed.set_author(name="Assignment",
                         icon_url="https://cdn.discordapp.com/icons/345797456614785024/9ef2a960cb5f91439556068b8127512a.webp?size=128")
        embed.description = f"*{chapter.project.title}* {formatNumber(chapter.number)}\nA staffmember has already been assigned!\n[Jump!]({msg})\n"
        await channel.send(embed=embed)

def setup(bot):
    bot.add_cog(Loops(bot))