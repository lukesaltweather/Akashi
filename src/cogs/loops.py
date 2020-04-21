import datetime
import time

import discord
from discord.ext import tasks , commands

from src.model.chapter import Chapter
from src.model.message import Message
from src.util.misc import formatNumber


class Loops(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.refreshembed.start()
        self.deletemessages.start()

    def cog_unload(self):
        self.refreshembed.cancel()

    @tasks.loop(hours=2)
    async def deletemessages(self):
        session = self.bot.Session()
        messages = session.query(Message).all()
        for message in messages:
            if message.created_on < (datetime.datetime.utcnow() - datetime.timedelta(hours=48)) and message.reminder:
                channel = self.bot.get_channel(self.bot.config["command_channel"])
                m = await channel.fetch_message(message.message_id)
                await m.clear_reactions()
                await m.unpin()
                await m.add_reaction("❌")
                msg = m.jump_url
                embed = discord.Embed(color=discord.Colour.red())
                embed.set_author(name="Assignment",
                                 icon_url="https://cdn.discordapp.com/icons/345797456614785024/9ef2a960cb5f91439556068b8127512a.webp?size=128")
                chapter = session.query(Chapter).filter(Chapter.id == message.chapter).one()
                wordy = (await self.bot.fetch_user(345845639663583252)).mention
                embed.description = f"*{chapter.project.title}* {formatNumber(chapter.number)}\nNo staffmember assigned themselves to Chapter.\n[Jump!]({msg})\n"
                await channel.send(message={wordy}, embed=embed)
                session.delete(message)
            elif message.created_on < (datetime.datetime.utcnow() - datetime.timedelta(hours=24)) and not message.reminder:
                channel = self.bot.get_channel(self.bot.configconfig["command_channel"])
                m = await channel.fetch_message(message.message_id)
                msg = m.jump_url
                embed = discord.Embed(color=discord.Colour.red())
                embed.set_author(name="Assignment Reminder",
                                 icon_url="https://cdn.discordapp.com/icons/345797456614785024/9ef2a960cb5f91439556068b8127512a.webp?size=128")
                chapter = session.query(Chapter).filter(Chapter.id == message.chapter).one()
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
        session.close()