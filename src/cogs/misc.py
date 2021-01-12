import itertools
import json
import time
from io import BytesIO

import aiohttp
import discord
import pkg_resources
from discord.ext import commands

from src.model.staff import Staff
from src.util import exceptions, checks
from src.util.checks import is_admin, is_worker, has_worker
import math as m
import psutil
import datetime
import humanize
import pygit2

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

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = await self.bot.fetch_channel(345797456614785028)
        rules = await self.bot.fetch_channel(345829173438316545)
        if channel:
            await channel.send('{0.mention} Welcome to the Land of Nekos. Please read all the information in {1.mention}'.format(member, rules))
            await self.bot.http.add_role(345797456614785024, member.id, 440714683587231744, reason="Initial Role")
        else:
            await (self.bot.get_user(self.bot.owner_id)).send("kein channel")
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

    @commands.command()
    async def apply(self, ctx):
        role = ctx.guild.get_role(345886396046770176)
        await ctx.author.add_roles(role)

    @commands.command()
    @has_worker()
    async def kouhai(self, ctx, member: discord.Member):
        role = ctx.guild.get_role(345886396046770176)
        await member.add_roles(role)

    @commands.command(description='Add a self-assignable role. Use $roles to see a list of roles.', usage='$iam <role>',  brief='Add a self-assignable role.')
    async def iam(self, ctx: commands.Context, role: str):
        l = role.lower()
        roles = {
            'kouhai':345886396046770176,
            'recipes': 464213892109828097,
            'tabletop':717869655695425558,
            'roleplaying':538484121375211550,
            'gamers':717869966136967330,
            'programming':717869431623254028
        }
        role = ctx.guild.get_role(roles.get(l, None))
        if not role:
            raise RuntimeError
        await ctx.author.add_roles(role, reason="Added Self-Assignable role.")
        embed = discord.Embed()
        embed.title = "Enjoy your new role!"
        embed.color = discord.Colour.dark_green()
        await ctx.send(embed=embed, delete_after=20)

    @commands.command(description='Remove a self-assignable role. Use $roles to see a list of roles.', usage='$iam <role>', brief='Remove a self-assignable role.')
    async def iamnot(self, ctx: commands.Context, role: str):
        l = role.lower()
        roles = {
            'kouhai': 345886396046770176,
            'recipes': 464213892109828097,
            'tabletop': 717869655695425558,
            'roleplaying': 538484121375211550,
            'gamers': 717869966136967330,
            'programming': 717869431623254028
        }
        role = ctx.guild.get_role(roles.get(l, None))
        if not role:
            raise RuntimeError
        await ctx.author.remove_roles(role, reason='Used Command to remove self-assigned role.')
        embed = discord.Embed()
        embed.title = "Removed role."
        embed.color = discord.Colour.dark_orange()
        await ctx.send(embed=embed, delete_after=20)

    @commands.command(description='Shows Self-Assignable roles.', brief='Shows Self-Assignable roles.' ,usage='$roles')
    async def roles(self, ctx: commands.Context):
        em = discord.Embed()
        em.color = discord.Colour.blurple()
        em.title = "Self-Assignable Roles"
        em.description="Kouhai\nRecipes\nTabletop\nRoleplaying\nGamers\nProgramming"
        await ctx.send(embed=em)

    @iam.error
    async def iamerror(self, ctx, e):
        await ctx.send(f"Oops... Something went wrong.\n{e}")

    @iamnot.error
    async def iamnoterror(self, ctx, e):
        await ctx.send(f"Oops... Something went wrong.\n{e}")


    def get_bot_uptime(self):
        delta = (self.bot.uptime-datetime.datetime.now()).total_seconds()
        print(delta)
        delta = datetime.timedelta(seconds=delta)
        return humanize.naturaldelta(delta)

    def get_last_commits(self, count=3):
        repo = pygit2.Repository('.git')
        commits = list(itertools.islice(repo.walk(repo.head.target, pygit2.GIT_SORT_TOPOLOGICAL), count))
        return '\n'.join(self.format_commit(c) for c in commits)

    def format_commit(self, commit):
        short, _, _ = commit.message.partition('\n')
        short_sha2 = commit.hex[0:6]
        commit_tz = datetime.timezone(datetime.timedelta(minutes=commit.commit_time_offset))
        commit_time = datetime.datetime.fromtimestamp(commit.commit_time).replace(tzinfo=commit_tz)

        # [`hash`](url) message (offset)
        offset = humanize.naturaldelta(commit_time.astimezone(datetime.timezone.utc).replace(tzinfo=None)+datetime.timedelta(hours=2))
        return f'[`{short_sha2}`](https://github.com/lukesaltweather/akashi/commit/{commit.hex}) {short} ({offset} ago)'

    @commands.command(aliases=["statistics", "status", "usage", 'about', 'uptime', 'akashi'])
    async def stats(self, ctx):
        embed = discord.Embed(color=discord.Colour.blurple())
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory()
        disc = psutil.disk_usage("/")
        revision = self.get_last_commits()
        description = f"**`Latest Changes:`**\n\n {revision}\n\n"
        embed.description = description
        icon = self.bot.get_user(358244935041810443).avatar_url
        embed.set_author(icon_url=icon, name='Created by lukesaltweather#1111')
        version = pkg_resources.get_distribution('discord.py').version
        embed.set_footer(text=f'Powered by discord.py {version} and SQLAlchemy {pkg_resources.get_distribution("SQLAlchemy").version}', icon_url='https://dinte0h0exzgg.cloudfront.net/logo/7c84429c642945eeaee7f459484bdc34-akashi_12392.jpg')
        embed.timestamp = datetime.datetime.utcnow()
        embed.add_field(name='CPU Usage', value=f'{cpu} %', inline=False)
        embed.add_field(name='Memory', value=f'{round((mem.total-mem.available)/1073741824, 2)} **GB** / {round(mem.total/1073741824, 2)} **GB** *({round((mem.total-mem.available)*100/mem.total, 2)}* **%** used)', inline=False)
        embed.add_field(name='Disk Usage', value=f'{round((disc.used/1073741824), 2)} **GB** / {round((disc.total/1073741824), 2)} **GB** (*{disc.percent}* **%**)', inline=False)
        embed.add_field(name='Websocket Latency', value=f'{round(self.bot.latency*1000, 2)} **ms**', inline=True)
        embed.add_field(name='Uptime', value=f'{self.get_bot_uptime()}')
        await ctx.send(embed=embed)

    @commands.command()
    async def tos(self, ctx):
        embed = discord.Embed(color=discord.Colour.dark_blue())
        embed.set_author(name="Terms of Service", icon_url='https://dinte0h0exzgg.cloudfront.net/logo/7c84429c642945eeaee7f459484bdc34-akashi_12392.jpg')
        embed.timestamp = datetime.datetime.utcnow()
        embed.add_field(name='Clause 1', value='We are storing some public information about you: the username and the id, which are stored on a secured database.')
        embed.add_field(name='Clause 2', value='You may request deletion of your stored data. However, this information is required for the bot to work properly. After such a request has been fullfilled, the bot will cease working for you.')
        embed.add_field(name='Clause 3', value='We do not keep logs of your commands, messages, presence or similar. Member update event information is only used to update aforementioned user database.')
        embed.add_field(name='Clause 4', value='While backups of the database are kept, we are not liable in case any data is lost.')
        embed.add_field(name='Clause 5', value='We reserve the right to ban you from using the bot, for any reason. In most cases, that would be trolling, trying to find exploits or even destructive behaviours.')
        embed.add_field(name='Clause 6', value='These terms of service are OPT-OUT, by using the bot and not opting out, you agree to them.')
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

    # @commands.command(description=jsonhelp['addrelease']['description'], usage=jsonhelp["addrelease"]["usage"], bried=jsonhelp["addrelease"]['brief'], help=jsonhelp["addrelease"]['help'])
    # @is_admin()
    # async def add_release(self, date: CustomDateConverter, *, text: str):
    #     pass

def setup(Bot):
    Bot.add_cog(Misc(Bot))