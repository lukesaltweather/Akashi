import asyncio
import json

import discord
from dateutil import *
from discord.ext import commands

from src.util import exceptions
from src.model.timer import Reminder
from datetime import *
from src.util.search import searchstaff, discordstaff

with open('src/util/help.json', 'r') as f:
    jsonhelp = json.load(f)

class ReminderCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.Session = self.bot.Session

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

    @commands.command(aliases=["r"],description=jsonhelp["remind"]["description"],
                      usage=jsonhelp["remind"]["usage"], brief=jsonhelp["remind"]["brief"], help=jsonhelp["remind"]["help"])
    async def remind(self, ctx, *, arg):
        session = self.Session()
        try:
            arg = arg[1:]
            d = dict(x.split('=', 1) for x in arg.split(' -'))
            if "msg" not in d or "date" not in d:
                raise commands.MissingRequiredArgument("Message or DateTime")
            date = parser.parse(timestr=d.get("date")).replace(tzinfo=tz.gettz(d.get("tz", "GMT")))
            date = date.astimezone(tz.UTC)
            print(date)
            if "u" in d:
                u = await discordstaff(d.get("u"), ctx)
            else:
                u = ctx.author
            r = Reminder(ctx.author.id, d.get("msg"), date, u.id)
            def check(message: discord.Message) -> bool:
                return message.author == ctx.author
            try:
                await ctx.send(f"Do you really want to add this reminder on {date.strftime('`%Y-%b-%d` | `%H:%M` `TZ: %Z`')}. Type Y/y/Yes/yes in chat to confirm, N/n/No/no to cancel.")
                self.message = await self.bot.wait_for('message', timeout=30.5, check=check)
            except asyncio.TimeoutError:
                await ctx.send("The author didn't respond.")
            if self.message.content in("yes", "Yes", "y", "Y"):
                await ctx.message.add_reaction("👍")
                session.add(r)
                print("commited")
                session.commit()
            else:
                await ctx.send("Reminder wasn't added.")
        except Exception as e:
            print(e)
            session.rollback()
        finally:
            session.close()

def setup(bot):
    bot.add_cog(ReminderCog(bot))