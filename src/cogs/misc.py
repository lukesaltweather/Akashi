import json
from io import BytesIO

import aiohttp
import discord
from discord.ext import commands

from src.model.staff import Staff
from src.util import exceptions, checks
from src.util.checks import is_admin, is_worker
import math as m
import psutil
import datetime
import humanize

with open('src/util/help.json', 'r') as f:
    jsonhelp = json.load(f)

class Misc(commands.Cog):
    """
        Miscellaneous Commands
    """
    def __init__(self, client):
        self.bot = client


    async def cog_check(self, ctx):
        return ctx.guild is not None

    @commands.command(name='reload', hidden=True)
    @is_admin()
    async def _reload(self, ctx, module: str):
        """Reloads a module."""
        try:
            self.bot.unload_extension(module)
            self.bot.load_extension(module)
        except Exception as e:
            await ctx.send('\N{PISTOL}')
            await ctx.send('{}: {}'.format(type(e).__name__, e))
        else:
            await ctx.send('\N{OK HAND SIGN}')

    @commands.command()
    @is_worker()
    async def hello(self, ctx):
        message = discord.AllowedMentions(everyone=False, roles=False, users=False)
        luke = self.bot.get_user(358244935041810443)
        await ctx.send(f"Hello, I'm Akashi. I keep track of Nekyou's projects.\n{luke.mention} made me.", allowed_mentions=message)

    def get_bot_uptime(self):
        delta = (self.bot.uptime-datetime.datetime.now()).total_seconds()
        print(delta)
        delta = datetime.timedelta(seconds=delta)
        return humanize.naturaldelta(delta)

    @commands.command(aliases=["statistics", "status", "usage"])
    @is_admin()
    async def stats(self, ctx):
        embed = discord.Embed(color=discord.Colour.blurple())
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory()
        disc = psutil.disk_usage("/")
        description = f"CPU Usage | **{cpu}** %\nMemory | **{round((mem.total-mem.available)/1073741824, 2)} GB** / **{round(mem.total/1073741824, 2)} GB** ({round((mem.total-mem.available)*100/mem.total, 2)}% used)" \
                      f"\nDisk Usage | **{round((disc.used/1073741824), 2)} GB** / **{round((disc.total/1073741824), 2)} GB** ({disc.percent}%)\nLatency | **{round(self.bot.latency, 2)}** s\n" \
                      f"Uptime | **{self.get_bot_uptime()}**\n"
        embed.description = description
        embed.set_author(name="Usage Statistics", icon_url="https://dinte0h0exzgg.cloudfront.net/logo/7c84429c642945eeaee7f459484bdc34-akashi_12392.jpg")
        await ctx.send(embed=embed)

    @commands.command(hidden=True, enabled=False)
    @is_admin()
    async def addall(self, ctx):
        session = self.bot.Session()
        members = ctx.guild.get_role(self.bot.config.get("neko_workers")).members
        for member in members:
            st = Staff(member.id, member.name)
            session.add(st)
            await ctx.send("Successfully added {} to staff. ".format(member.name))
        session.commit()
        session.close()

    @is_admin()
    @commands.command(hidden=True)
    async def toggledebug(self, ctx):
        if self.bot.debug == False:
            self.bot.debug = True
        else:
            self.bot.debug = False
        await ctx.send(f"Debugmode is now {self.bot.debug}")

    @commands.command(description=jsonhelp["debugboard"]["description"],
                      usage=jsonhelp["debugboard"]["usage"], brief=jsonhelp["debugboard"]["brief"], help=jsonhelp["debugboard"]["help"])
    @is_admin()
    async def debugboard(self, ctx):
        with open('src/util/board.json', 'r') as f:
            msgs = json.load(f)
        messages = list()
        ch = await self.bot.fetch_channel(self.bot.config["board_channel"])
        for msg in msgs.values():
            for me in msg:
                messages.append(await ch.fetch_message(me))
        for message in messages:
            await message.delete()
        messages = {}
        with open('src/util/board.json', 'w') as f:
            json.dump(messages, f, indent=4)

    @is_worker()
    @commands.command(description=jsonhelp["avatar"]["description"],
                      usage=jsonhelp["avatar"]["usage"], brief=jsonhelp["avatar"]["brief"], help=jsonhelp["avatar"]["help"])
    async def avatar(self, ctx, member: discord.Member):
        await ctx.send(member.avatar_url)

    @commands.command(description=jsonhelp["cat"]["description"],
                      usage=jsonhelp["cat"]["usage"], brief=jsonhelp["cat"]["brief"], help=jsonhelp["cat"]["help"])
    @is_worker()
    async def cat(self, ctx, *, arg):
        try:
            arg = arg[1:]
            d = dict(x.split('=', 1) for x in arg.split(' -'))
            if "breed" in d:
                params = {"q": d["breed"], "limit": 1}
                headers = {"x-api-key": "6290e11c-ffe2-4ba0-8a18-eca68efb4246"}
                url = "https://api.thecatapi.com/v1/breeds/search"
                async with aiohttp.ClientSession() as session:
                    # note that it is often preferable to create a single session to use multiple times later - see below for this.
                    async with session.get(url, params=params, headers=headers) as resp:
                        r = await resp.json()
                        id = r[0]["id"]
                        url = "https://api.thecatapi.com/v1/images/search"
                        if "type" not in d:
                            params = {"breed_ids": id, "limit": 1}
                        else:
                            params = {"breed_ids": id, "mime_types": d["type"], "limit": 1}
                        async with session.get(url, headers=headers, params=params) as resp:
                            r = await resp.json()
                            url = r[0]['url']
                            async with session.get(url) as resp:
                                buffer = BytesIO(await resp.read())
                                file = discord.File(fp=buffer, filename=f"something.{d['type']}")
                                await ctx.send(file=file)
            else:
                headers = {"x-api-key": "6290e11c-ffe2-4ba0-8a18-eca68efb4246"}
                async with aiohttp.ClientSession() as session:
                    # note that it is often preferable to create a single session to use multiple times later - see below for this.
                    url = "https://api.thecatapi.com/v1/images/search"
                    if "type" in d:
                        params = {"mime_types": d["type"], "limit": 1}
                    async with session.get(url, headers=headers, params=params) as resp:
                        r = await resp.json()
                        url = r[0]['url']
                        async with session.get(url) as resp:
                            buffer = BytesIO(await resp.read())
                            file = discord.File(fp=buffer, filename=f"something.{d['type']}")
                            await ctx.send(file=file)
        except IndexError:
            raise exceptions.NoResultFound(message="Could not find an image like this.")

    @commands.command(description=jsonhelp["embed"]["description"],
                      usage=jsonhelp["embed"]["usage"], brief=jsonhelp["embed"]["brief"], help=jsonhelp["embed"]["help"])
    @is_worker()
    async def embed(self, ctx, color: str):
        color = color.strip("#")
        eger = int(color, 16)
        color = discord.Colour(eger)
        embed = discord.Embed(color=color)
        await ctx.send(embed=embed)

    @commands.command(description=jsonhelp['addrelease']['description'], usage=jsonhelp["addrelease"]["usage"], bried=jsonhelp["addrelease"]['brief'], help=jsonhelp["addrelease"]['help'])
    @is_admin()
    async def add_release(self, date: CustomDateConverter, *, text: str):
        pass

def setup(Bot):
    Bot.add_cog(Misc(Bot))