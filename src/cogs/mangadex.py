import aiohttp
from discord.ext.menus import button, Last

from src.util import mangadex
import src.util.mangadex
import asyncpg
import discord
from discord.ext import commands
from discord.ext import menus

from discord.ext import menus

async def generate(number, p):
    for i in range(number):
        arr = await p[i].async_download()
        yield arr

class Source(menus.AsyncIteratorPageSource):
    def __init__(self, p, session: aiohttp.ClientSession):
        super().__init__(generate(len(p), p), per_page=1)
        self.session = session
        self.hashes = []

    async def format_page(self, menu, entries):
        start = menu.current_page * self.per_page
        async with self.session.post('https://api.imgur.com/3/upload', data={'name': 'page.png', 'image': entries}, headers={'Authorization': 'Client-ID 223de056d30d21d'}) as resp:
            r = await resp.json()
        embed = discord.Embed(color=discord.Colour.gold())
        embed.set_author(name="Page",
                         icon_url="https://pbs.twimg.com/profile_images/1191033858424233987/pyULgeym_400x400.jpg")
        embed.set_image(url=r.get('data').get('link'))
        self.hashes.append(r.get('data').get('deletehash'))
        return embed

    async def destroy_images(self):
        for hash in self.hashes:
            async with self.session.post('https://api.imgur.com/3/image/{}'.format(hash), headers={'Authorization': 'Client-ID 223de056d30d21d'}) as r:
                pass

class MyMenu(menus.MenuPages):
    def __init__(self, source, **kwargs):
        super().__init__(source, **kwargs)

    @button('\N{BLACK SQUARE FOR STOP}\ufe0f', position=Last(2))
    async def stop_pages(self, payload):
        """stops the pagination session."""
        await self._source.destroy_images()
        self.stop()

    async def update(self, payload):
        if self._can_remove_reactions:
            if payload.event_type == 'REACTION_ADD':
                await self.bot.http.remove_reaction(
                    payload.channel_id, payload.message_id,
                    discord.Message._emoji_reaction(payload.emoji), payload.member.id
                )
            elif payload.event_type == 'REACTION_REMOVE':
                return
        await super().update(payload)

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
        if len(ints) == 2:
            query = """SELECT * FROM mangadex WHERE id = $1 LIMIT 1;"""
            title = ints[1]
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
            pages = MyMenu(source=Source(pages, self.session), clear_reactions_after=True)
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