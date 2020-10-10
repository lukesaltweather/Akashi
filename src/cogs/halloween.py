import discord
import enum
import random

from discord.ext import commands

class Species(enum.Enum):
    Werewolf = 0
    Vampire = 1
    Zombie = 2

class Halloween(commands.Cog):

    def __init__(self, client):
        self.bot = client
        self.pool = client.pool

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == message.guild.me:
            return
        author_id = message.author.id
        con = await self.pool.acquire()
        query1 = """INSERT INTO halloween_users (author, amt, species) VALUES ($1, $2, $3) ON CONFLICT DO NOTHING"""
        query2 = """UPDATE halloween_users SET amt = amt + 1 WHERE author = $1"""

        await con.execute(query1, author_id, 0, random.choice([0, 1, 2]))
        await con.execute(query2, author_id)
        await self.pool.release(con)

    @commands.command()
    async def start(self, ctx):
        pass
        # assign members teams
        # start message

    @commands.command()
    async def tally(self, ctx):
        pass
        # results

    @commands.command()
    async def team(self, ctx: commands.Context, team: str = None):
        con = await self.pool.acquire()
        if team:
            pass
            # fetch info on team
        else:
            query = """SELECT species FROM halloween_users WHERE author = $1"""
            res = await con.fetchrow(query, ctx.author.id)
            species = res[0]
            query = """SELECT SUM(amt), COUNT(*) FROM halloween_users WHERE species = $1"""
            res = await con.fetchrow(query, int(species))
            embed = discord.Embed(title=f'Team {Species(species).name}')
            embed.add_field(name="Members", value=f"{res[1]}", inline=True).add_field(name="Messages in total", value=f"{res[0]}").set_author(icon_url='https://upload.wikimedia.org/wikipedia/commons/thumb/a/a2/Jack-o%27-Lantern_2003-10-31.jpg/220px-Jack-o%27-Lantern_2003-10-31.jpg', name='Halloween Event')
            embed.set_footer(text=ctx.author.display_name, icon_url=ctx.author.avatar_url)
            await ctx.send(embed=embed)
            await self.pool.release(con)

    @commands.command(alias=["eventstats"])
    async def halloween(self, ctx):
        con = await self.pool.acquire()
        wolfs = """SELECT SUM(amt), COUNT(*) FROM halloween_users WHERE species = 0"""
        vamps = """SELECT SUM(amt), COUNT(*) FROM halloween_users WHERE species = 1"""
        zombies = """SELECT SUM(amt), COUNT(*) FROM halloween_users WHERE species = 2"""
        res = list()
        for q in [wolfs, vamps, zombies]:
            res.append(await con.fetchrow(q))

        embed = discord.Embed(title='Event Stats')
        embed.add_field(name="Participants", value=f"{res[0][1]+res[1][1]+res[2][1]} Monsters", inline=True)
        embed.add_field(name="Messages in total", value=f"{res[0][0]+res[1][0]+res[2][0]}", inline=True)
        embed.add_field(name="Wolf Messages", value=f"{res[0][0]}", inline=False)
        embed.add_field(name="Vampire Messages", value=f"{res[1][0]}", inline=True)
        embed.add_field(name="Zombie Messages", value=f"{res[2][0]}", inline=True)
        embed.set_author(
            icon_url='https://upload.wikimedia.org/wikipedia/commons/thumb/a/a2/Jack-o%27-Lantern_2003-10-31.jpg/220px-Jack-o%27-Lantern_2003-10-31.jpg',
            name='Halloween Event')
        embed.set_footer(text="Created by luke", icon_url=ctx.get_member(ctx.bot.owner_id).avatar_url)
        await ctx.send(embed=embed)
        await self.pool.release(con)

    @commands.command()
    async def me(self, ctx):
        con = await self.pool.acquire()
        query = """SELECT species,amt FROM halloween_users WHERE author = $1"""
        res = await con.fetchrow(query, ctx.author.id)
        if not res:
            await ctx.send("Creating DB entry. Please try again!")
            await self.pool.release(con)
            return
        embed = discord.Embed()
        embed.add_field(name="Monster / Team", value=f"{Species(res[0]).name}", inline=True).add_field(name="Total Messages", value=f"{res[1]}").set_footer(
            icon_url='https://upload.wikimedia.org/wikipedia/commons/thumb/a/a2/Jack-o%27-Lantern_2003-10-31.jpg/220px-Jack-o%27-Lantern_2003-10-31.jpg',
            text='Halloween Event').set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)
        await self.pool.release(con)

    @me.error
    async def handle(self, ctx, error):
        await ctx.send(f"Sorry, it seems like an error occured. Please try again. \n```{error}```")

def setup(bot: commands.bot):
    bot.add_cog(Halloween(bot))


