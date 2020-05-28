import mangadex
import asyncpg
import discord
from discord.ext import commands

class MangaDex(commands.Cog):
    """
        Mangadex Commands
    """
    def __init__(self, bot):
        self.bot = bot
        self.pool = bot.pool

    @commands.command()
    async def search(self,ctx, *, title: str):
        connection = await self.pool.acquire()
        query = """SELECT url,id, title, similarity(title, $1) AS sml FROM mangadex WHERE title % $1 GROUP BY id,title,url ORDER BY sml DESC,id  LIMIT 10;"""
        try:
            text = ""
            tags = await connection.fetch(query, f"%{title}%")
            nr = 1
            for row in tags:
                if row['title'][0] == ' ':
                    title = row['title'][1:]
                else:
                    title = row['title']
                text = f"{text}**{nr}. **[`{title}`]({row.get('url')})\n"
                nr = nr+1
            embed = discord.Embed(color=discord.Colour.gold())
            embed.set_author(name="Search Results", icon_url="https://pbs.twimg.com/profile_images/1191033858424233987/pyULgeym_400x400.jpg")
            embed.description = text
            await ctx.send(embed=embed)
        finally:
            await self.pool.release(connection)

    @commands.command()
    async def chapter(self,ctx, chapter: int, page: int, *, title: str):
        connection = await self.pool.acquire()
        query = """SELECT * FROM mangadex WHERE title % $1;"""
        try:
            chap = await connection.fetchrow(query, f"%{title}%")
            m = mangadex.Manga(chap.get('id'))
            m.populate()
            chaps = m.get_chapters()
            c = chaps[chapter]
            pages = c.get_pages()
            embed = discord.Embed(color=discord.Colour.gold())
            embed.set_author(name="Search Results", icon_url="https://pbs.twimg.com/profile_images/1191033858424233987/pyULgeym_400x400.jpg")
            embed.set_image(url=pages[page].url)
            await ctx.send(embed=embed)
        finally:
            await self.pool.release(connection)

def setup(bot: commands.bot):
    bot.add_cog(MangaDex(bot))