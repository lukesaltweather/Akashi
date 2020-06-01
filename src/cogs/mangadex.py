import asyncio
import functools

import aiohttp
from discord.ext.menus import button, Last

from src.util import mangadex
import src.util.mangadex
import asyncpg
import discord
from discord.ext import commands
from discord.ext import menus
import shutil
from discord.ext import menus
import aiofiles
from aiofiles import os as aios
import pathlib

async def generate(number, p, session):
    for i in range(number):
        arr = await p[i].async_download()
        pathlib.Path(f'/var/www/api.lukesaltweather.de/static/{p[i].chapter_hash}').mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(f'/var/www/api.lukesaltweather.de/static/{p[i].chapter_hash}/{p[i].page_filename}', mode='wb') as f:
            await f.write(arr.getbuffer())
        yield f'https://api.lukesaltweather.de/static/{p[i].chapter_hash}/{p[i].page_filename}'

class Source(menus.AsyncIteratorPageSource):
    def __init__(self, p, session: aiohttp.ClientSession):
        super().__init__(generate(len(p), p, session), per_page=1)
        self.links = []
        self.hash = p[0].chapter_hash

    async def _get_single_page(self, page_number):
        if page_number < 0:
            raise IndexError('Negative page number.')

        if not self._exhausted and len(self._cache) <= page_number:
            await self._iterate((page_number + 1) - len(self._cache))
        return self._cache[page_number]

    async def format_page(self, menu, entries):
        embed = discord.Embed(color=discord.Colour.gold())
        embed.set_author(name="Page",
                         icon_url="https://pbs.twimg.com/profile_images/1191033858424233987/pyULgeym_400x400.jpg")
        embed.set_image(url=entries)
        await asyncio.sleep(0.5)
        return embed

    async def destroy_images(self):
        thing = functools.partial(shutil.rmtree, f'/var/www/api.lukesaltweather.de/static/{self.hash}')
        some_stuff = await asyncio.get_running_loop().run_in_executor(None, thing)
        await aios.rmdir(f'/var/www/api.lukesaltweather.de/static/{self.hash}')

class TestSource(menus.ListPageSource):
    def __init__(self, pages):
        super().__init__(pages, per_page=1)

    async def format_page(self, menu, entries):
        start = menu.current_page * self.per_page
        embed = discord.Embed(color=discord.Colour.gold())
        embed.set_author(name="Page",
                         icon_url="https://pbs.twimg.com/profile_images/1191033858424233987/pyULgeym_400x400.jpg")
        embed.set_image(url=entries.url)
        return embed

class MyMenu(menus.MenuPages):
    def __init__(self, source, **kwargs):
        super().__init__(source, **kwargs)

    def stop(self):
        self._running = False
        if self.__task is not None:
            self.__task.cancel()
            self.__task = None

    async def finalize(self):
        await self.source.destroy_images()

class MangaDex(commands.Cog):
    """
        Mangadex Commands
    """
    def __init__(self, bot):
        self.bot = bot
        self.pool = bot.pool
        self.session = aiohttp.ClientSession()

    @commands.command()
    async def search(self,ctx, *, title: str):
        connection = await self.pool.acquire()
        query = """SELECT *,title <-> $1 AS dis FROM mangadex WHERE title % $1 ORDER BY dis DESC LIMIT 10;"""
        try:
            text = ""
            tags = await connection.fetch(query, f"{title}%")
            nr = 1
            for row in tags:
                if row['title'][0] == ' ':
                    title = row['title'][1:]
                else:
                    title = row['title']
                text = f"{text}**{row.get('id')}: **[`{title}`]({row.get('url')})\n"
                nr = nr+1
            embed = discord.Embed(color=discord.Colour.gold())
            embed.set_author(name="Search Results", icon_url="https://pbs.twimg.com/profile_images/1191033858424233987/pyULgeym_400x400.jpg")
            embed.description = text
            await ctx.send(embed=embed)
        finally:
            await self.pool.release(connection)

    @commands.command()
    async def chapter(self,ctx, ints : commands.Greedy[int], *, title: str=""):
        chapter = ints[0]
        connection = await self.pool.acquire()
        try:
            if len(ints) == 2:
                m = mangadex.Manga(ints[1])
            else:
                query = """SELECT *, title <-> $1 as dis FROM mangadex WHERE title ILIKE $1 ORDER BY dis DESC;"""
                title = f"%{title}%"
                chap = await connection.fetchrow(query, title)
                m = mangadex.Manga(chap.get('id'))
            m.populate()
            chaps = m.get_chapters()
            c = chaps[chapter-1]
            pages = c.get_pages()
            pages = MyMenu(source=Source(pages, self.session), delete_message_after=True)
            await pages.start(ctx)
        finally:
            await self.pool.release(connection)

    @commands.command()
    async def chaptertest(self,ctx, ints : commands.Greedy[int], *, title: str=""):
        chapter = ints[0]
        connection = await self.pool.acquire()
        try:
            if len(ints) == 2:
                m = mangadex.Manga(ints[1])
            else:
                query = """SELECT *, title <-> $1 as dis FROM mangadex WHERE title ILIKE $1 ORDER BY dis DESC;"""
                title = f"%{title}%"
                chap = await connection.fetchrow(query, title)
                m = mangadex.Manga(chap.get('id'))
            m.populate()
            chaps = m.get_chapters()
            c = chaps[chapter-1]
            pages = c.get_pages()
            pages = MyMenu(source=TestSource(pages), clear_reactions_after=True)
            await pages.start(ctx)
        finally:
            await self.pool.release(connection)

    @commands.command()
    async def page(self,ctx, ints : commands.Greedy[int], *, title: str=""):
        chapter = ints[0]
        if len(ints) == 2:
            page = ints[1]
        else:
            page = 0
        connection = await self.pool.acquire()
        if len(ints) == 3:
            query = """SELECT * FROM mangadex WHERE id = $1 LIMIT 1;"""
            title = ints[2]
        else:
            query = """SELECT *, title <-> $1 as dis FROM mangadex WHERE title % $1 ORDER BY dis DESC;"""
            title = f"{title}%"
        try:
            chap = await connection.fetchrow(query, title)
            m = mangadex.Manga(chap.get('id'))
            m.populate()
            chaps = m.get_chapters()
            c = chaps[chapter]
            pages = c.get_pages()
            arr = await pages[page].async_download()
            embed = discord.Embed(color=discord.Colour.gold())
            embed.set_author(name="Page", icon_url="https://pbs.twimg.com/profile_images/1191033858424233987/pyULgeym_400x400.jpg")
            file = discord.File(arr, filename="image.png")
            embed.set_image(url="attachment://image.png")
            await ctx.send(file=file, embed=embed)
        finally:
            await self.pool.release(connection)

def setup(bot: commands.bot):
    bot.add_cog(MangaDex(bot))