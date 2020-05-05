import asyncio
import json

import discord
from discord.ext import commands
from src.util.exceptions import TagAlreadyExists
from src.model.tag import Tag
import asyncpg

def run_and_get(coro):
    task = asyncio.create_task(coro)
    asyncio.get_running_loop().run_until_complete(task)
    return task.result()

with open('src/util/help.json', 'r') as f:
    jsonhelp = json.load(f)

class Tags(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pool = bot.pool
        self.private_channels = [390395499355701249, 408848958232723467, 701831937001652286, 440955931296006154]

    @commands.command(invoke_without_command=True, description=jsonhelp["tag"]["description"],
                      usage=jsonhelp["tag"]["usage"], brief=jsonhelp["tag"]["brief"], help=jsonhelp["tag"]["help"])
    async def tag(self, ctx, *, t):
        connection = await self.pool.acquire()
        query = """SELECT * FROM tag WHERE tag % $1"""
        tag = f"%{t}%"
        try:
            tags = await connection.fetch(query, tag)
            if len(tags) == 1:
                if not tags[0].get("private", True):
                    await ctx.send(tags[0].get("content"))
                elif tags[0].get("private", True) and ctx.channel.id in self.private_channels:
                    await ctx.send(tags[0].get("content"))
                else:
                    raise RuntimeError("Sorry, this Tag is private.")
            elif len(tags) > 1:
                l = list()
                for p in tags:
                    if p.get("tag").lower() == t.lower():
                        if tags[0].get("private") and ctx.channel.id in self.private_channels:
                            l.append(p)
                        elif not tags[0].get("private"):
                            l.append(p)
                        else:
                            pass
                if len(l) != 1:
                    l = list()
                    for t in tags:
                        if t.get("private") and ctx.channel.id in self.private_channels:
                            l.append(t.get("tag"))
                        elif not t.get("private"):
                            l.append(t.get("tag"))
                        else:
                            pass
                    l = "\n".join(l)
                    await ctx.send(f"Couldn't find a tag like this. Did you mean:\n{l}")
                else:
                    if not l[0].get("private", True):
                        await ctx.send(l[0].get("content"))
                    elif l[0].get("private", True) and ctx.channel.id in self.private_channels:
                        await ctx.send(l[0].get("content"))
                    else:
                        raise RuntimeError("Sorry, this Tag is private.")
            else:
                await ctx.send("Couldn't find a tag like this.")
        finally:
            await self.pool.release(connection)

    @commands.command(description=jsonhelp["tagcreate"]["description"],
                      usage=jsonhelp["tagcreate"]["usage"], brief=jsonhelp["tagcreate"]["brief"], help=jsonhelp["tagcreate"]["help"])
    async def tagcreate(self, ctx):
        message = ''
        def check(message: discord.Message) -> bool:
            return message.author == ctx.author
        try:
            await ctx.send(
                f"Please enter a name for your tag. Enter 'cancel' to cancel at any time.")
            message = await self.bot.wait_for('message', timeout=30.5, check=check)
        except asyncio.TimeoutError:
            await ctx.send("The author didn't respond.")
        if message == '' or message.content.lower() == "cancel":
            raise RuntimeError("Cancelled by user.")
        tag = message.clean_content
        def check(message: discord.Message) -> bool:
            return message.author == ctx.author
        try:
            await ctx.send(
                f"Please enter the contents of your tag. Enter 'cancel' to cancel at any time.")
            message = await self.bot.wait_for('message', timeout=30.5, check=check)
        except asyncio.TimeoutError:
            await ctx.send("The author didn't respond.")
        if message == '' or message.content.lower() == "cancel":
            raise RuntimeError("Cancelled by user.")
        content = message.clean_content
        if ctx.channel.id == 701831937001652286:
            private = True
        else:
            private = False
        connection = await self.pool.acquire()
        try:
            query = """SELECT * FROM tag WHERE LOWER(tag)=$1;"""
            row = await connection.fetchrow(query, tag.lower())
            if row is not None:
                raise RuntimeError("This Tag already exists.")
            query = """INSERT INTO tag (tag, content, author, private) VALUES($1, $2, $3, $4)
            """
            await connection.execute(query, tag, content, ctx.author.id, private)
            await connection.close()
        except RuntimeError as e:
            await ctx.send(e)
        finally:
            await self.pool.release(connection)
        desc = f"__Added tag {tag} with the content:__\n{content}"
        await ctx.send(desc)

    @commands.command(description=jsonhelp["tagedit"]["description"],
                      usage=jsonhelp["tagedit"]["usage"], brief=jsonhelp["tagedit"]["brief"], help=jsonhelp["tagedit"]["help"])
    async def tagedit(self, ctx, *, arg):
        arg = arg[1:]
        d = dict(x.split('=', 1) for x in arg.split(' -'))
        if "tag" not in d or "content" not in d:
            raise RuntimeError("Missing Tag or new Content")
        connection = await self.pool.acquire()
        try:
            tag = d.pop("tag").lower()
            content = d.pop("content")
            query = """SELECT * FROM tag WHERE LOWER(tag)=$1;"""
            row = await connection.fetch(query, tag)
            if len(row) != 1:
                raise RuntimeError("Something is wrong, tag isn't unique.")
            row = row[0]
            row_tag = row.get("tag")
            row_owner = row.get("author")
            row_content = row.get("content")
            admin = ctx.guild.get_role(self.bot.config.get("neko_herders"))
            if row_owner != ctx.author.id or not admin in ctx.author.roles:
                raise RuntimeError("Sorry, you can't edit this tag, since you're not the owner.")
            query = """UPDATE tag SET content = $1 WHERE tag = $2"""
            await connection.execute(query, content, row_tag)
        finally:
            await self.pool.release(connection)
        description = f"__Old content:__\n{row_content}\n__New Content:__\n{content}"
        await ctx.send(description)

    @commands.command(description=jsonhelp["tagdelete"]["description"],
                      usage=jsonhelp["tagdelete"]["usage"], brief=jsonhelp["tagdelete"]["brief"], help=jsonhelp["tagdelete"]["help"])
    async def tagdelete(self, ctx, tag: str):
        con = await self.pool.acquire()
        try:
            query = """SELECT * FROM tag WHERE LOWER(tag) = LOWER($1)"""
            rows = await con.fetch(query, tag)
            if len(rows) != 1:
                raise RuntimeError("Couldn't find a Tag like this.")
            row = rows[0]
            admin = ctx.guild.get_role(self.bot.config.get("neko_herders"))
            if row.get("author") != ctx.author.id or admin in ctx.author.roles:
                raise RuntimeError("Sorry, this Tag doesn't belong to you.")
            query = """DELETE FROM tag WHERE tag = $1"""
            await con.execute(query, row.get("tag"))
        finally:
            await self.pool.release(con)

    @commands.command(description=jsonhelp["tagtoggleprivate"]["description"],
                      usage=jsonhelp["tagtoggleprivate"]["usage"], brief=jsonhelp["tagtoggleprivate"]["brief"], help=jsonhelp["tagtoggleprivate"]["help"])
    async def tagtoggleprivate(self, ctx, tag:str):
        con = await self.pool.acquire()
        try:
            tag = tag
            query = query = """SELECT * FROM tag WHERE LOWER(tag) = LOWER($1)"""
            row = await con.fetchrow(query, tag)
            if row is None:
                raise RuntimeError("Couldn't find a tag like this.")
            row_owner = row.get("author")
            print(f"Ower: {row_owner}")
            admin = ctx.guild.get_role(self.bot.config.get("neko_herders"))
            if row_owner != ctx.author.id or admin not in ctx.author.roles:
                raise RuntimeError("Sorry, you can't edit this tag, since you're not the owner.")
            tag = row
            if tag.get("private"):
                p = False
            else:
                p = True
            query = """UPDATE tag SET private = $1 WHERE tag = $2"""
            await con.execute(query, p, tag.get("tag"))
            await ctx.send(f"Set private to {p}")
        finally:
            await self.pool.release(con)

def setup(bot: commands.bot):
    bot.add_cog(Tags(bot))