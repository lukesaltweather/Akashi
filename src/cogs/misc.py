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
from src.util.checks import is_admin, is_worker

import psutil
import datetime
import humanize
import pygit2

class Misc(commands.Cog):
    """
        Miscellaneous Commands
    """
    def __init__(self, client):
        self.bot = client

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = await self.bot.fetch_channel(345797456614785028)
        rules = await self.bot.fetch_channel(345829173438316545)
        await channel.send('{0.mention} Welcome to the Land of Nekos. Please read all the information in {1.mention}'.format(member, rules))
        await self.bot.http.add_role(345797456614785024, member.id, 440714683587231744, reason="Initial Role")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.message_id == 818205833220325404:
            guild: discord.Guild = await self.bot.fetch_guild(345797456614785024)
            member: discord.Member = await guild.fetch_member(payload.user_id)
            print(payload.emoji.__str__())
            if payload.emoji.__str__() == "⌨️":
                await member.add_roles(guild.get_role(717869431623254028))
            elif payload.emoji.__str__() == "🎲":
                await member.add_roles(guild.get_role(717869655695425558))
            elif payload.emoji.__str__() == "🎮":
                await member.add_roles(guild.get_role(717869966136967330))
            elif payload.emoji.__str__() == "✉️":
                await member.add_roles(guild.get_role(345886396046770176))
            elif payload.emoji.__str__() == "🍲":
                await member.add_roles(guild.get_role(464213892109828097))

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        if payload.message_id == 818205833220325404:
            guild: discord.Guild = await self.bot.fetch_guild(345797456614785024)
            member: discord.Member = await guild.fetch_member(payload.user_id)
            if payload.emoji.__str__() == "⌨️":
                await member.remove_roles(guild.get_role(717869431623254028))
            elif payload.emoji.__str__() == "🎲":
                await member.remove_roles(guild.get_role(717869655695425558))
            elif payload.emoji.__str__() == "🎮":
                await member.remove_roles(guild.get_role(717869966136967330))
            elif payload.emoji.__str__() == "✉️":
                await member.remove_roles(guild.get_role(345886396046770176))
            elif payload.emoji.__str__() == "🍲":
                await member.remove_roles(guild.get_role(464213892109828097))

    @commands.command()
    async def hello(self, ctx):
        message = discord.AllowedMentions(everyone=False, roles=False, users=False)
        luke = self.bot.get_user(358244935041810443)
        await ctx.send(f"Hello, I'm Akashi. I keep track of Nekyou's projects.\n{luke.mention} made me.", allowed_mentions=message)

    @commands.command()
    async def apply(self, ctx):
        role = ctx.guild.get_role(self.bot.config["server"]["roles"]["applicant"])
        await ctx.author.add_roles(role)

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

    @commands.command(hidden=True, enabled=False)
    @is_admin()
    async def addall(self, ctx):
        session = self.bot.Session()
        members = ctx.guild.get_role(self.bot.config["server"]["roles"]["members"]).members
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

    @commands.command()
    async def avatar(self, ctx, member: discord.Member):
        await ctx.send(member.avatar_url)

def setup(Bot):
    Bot.add_cog(Misc(Bot))