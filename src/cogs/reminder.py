import asyncio

import discord
from dateutil.tz import tzstr, gettz
from dateutil.zoneinfo import get_zonefile_instance
from discord.ext import commands

from src.util import exceptions
from src.model.timer import Reminder
from datetime import *
from dateutil import *

from src.util.search import searchstaff


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

    @commands.command()
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
                u = await searchstaff(d.get("u"), ctx, session)
            else:
                u = ctx.author
            r = Reminder(ctx.author.id, d.get("message"), date, u.id)
            def check(message: discord.Message) -> bool:
                return message.author == ctx.author
            try:
                await ctx.send(f"Do you really want to add this reminder on {date.strftime('%Y/%B/%d %H:%M TZ: %Z')}")
                self.message = await self.bot.wait_for('message', timeout=30.5, check=check)
            except asyncio.TimeoutError:
                await ctx.send("The author didn't respond.")
            if self.message.content in("yes", "Yes", "y", "Y"):
                await ctx.message.add_reaction("👍")
                session.add(r)
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