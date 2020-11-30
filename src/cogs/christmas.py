import discord
import enum
import random
import secrets
import asyncio

from discord.ext import commands

class Christmas(commands.Cog):

    def __init__(self, client: commands.bot):
        self.bot = client
        self.pool = client.pool

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author == message.guild.me or message.author.id in (329668530926780426, 172002275412279296, 603216263484801039) or message.author.bot:
            return
        if random.choices((True, False), weights=[5, 45])[0]:
            emoji = random.choice(('🎁', '📦', '🧧'))
            await message.add_reaction(emoji)
            con = await self.pool.acquire()
            def present_check(rea: discord.Reaction, u):
                return rea.message.id == message.id and str(rea.emoji) == emoji and u.id is not self.bot.user.id
            try:
                reaction, user = await self.bot.wait_for('reaction_add', check=present_check, timeout=60)
            except asyncio.TimeoutError:
                await message.clear_reaction(emoji)
            else:
                query1 = """INSERT INTO christmas_users (id, amt) VALUES ($1, $2) ON CONFLICT DO NOTHING"""
                query2 = """UPDATE christmas_users SET amt = amt + 1 WHERE id = $1"""
                await con.execute(query1, user.id, 0)
                await con.execute(query2, user.id)
                await message.clear_reaction(emoji)
            finally:
                await self.pool.release(con)

    @commands.command()
    async def reveal(self, ctx):
        pass
        # start message

    @commands.command()
    async def tally(self, ctx):
        pass
        # results

    @commands.command(aliases=["eventstats", "event", "hw"])
    async def leaderboard(self, ctx):
        con = await self.pool.acquire()
        p = """SELECT SUM(amt) FROM christmas_users"""
        u = """SELECT id, amt from christmas_users order by amt desc"""

        presents = await con.fetchrow(p)
        leaders = await con.fetch(u)


        leaders = '\n'.join([f'{num}. {st}' for num, st in enumerate([f'{ctx.guild.get_member(user[0]).name}\t|\t{user[1]}' for user in leaders], start=1)])


        embed = discord.Embed(title='Event Stats')
        embed.add_field(name="Leaderboard", value=f"```{leaders}```")
        embed.add_field(name="Presents in total", value=f"{presents[0]}", inline=False)
        embed.set_author(
            icon_url='https://upload.wikimedia.org/wikipedia/commons/thumb/a/a2/Jack-o%27-Lantern_2003-10-31.jpg/220px-Jack-o%27-Lantern_2003-10-31.jpg',
            name='Halloween Event')
        embed.set_footer(text="Created by luke")
        await ctx.send(embed=embed)
        await self.pool.release(con)

    @commands.command()
    async def me(self, ctx):
        con = await self.pool.acquire()
        query = """SELECT species,amt FROM halloween_users WHERE author = $1"""
        res = await con.fetchrow(query, ctx.author.id)
        if not res:
            await ctx.send("Sorry, you don't appear to have collected a present yet!")
            await self.pool.release(con)
            return
        embed = discord.Embed()
        embed.add_field(name="Presents Collected", value=f"{res[1]}").set_footer(
            icon_url='https://ec.europa.eu/jrc/sites/jrcsh/files/styles/normal-responsive/public/adobestock_226013143.jpeg?itok=3dbnMDO6',
            text='Christmas Event').set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)
        await self.pool.release(con)

    @me.error
    async def handle(self, ctx, error):
        await ctx.send(f"Sorry, it seems like an error occured. Please try again. \n```{error}```")

def setup(bot: commands.bot):
    bot.add_cog(Christmas(bot))


