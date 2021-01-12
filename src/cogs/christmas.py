import discord
import enum
import random
import secrets
import asyncio
import prettytable
import typing

from discord.ext import commands

class CooldownManager:
    """Track XP cooldowns of members
    """

    __slots__ = ("__dict__", "_cooldown", "_task")

    def __init__(self, loop, cooldown: float = 30):
        self._loop = loop
        self._cooldown = cooldown
        self._task: asyncio.Task = None
        self.on_cooldown = False

    def activate(self):
        self.on_cooldown = True
        self._task = self._loop.create_task(self._remove())

    async def _remove(self):
        await asyncio.sleep(self._cooldown)
        self.on_cooldown = False

    def cancel_cooldown(self):
        if self._task:
            self._task.cancel()
        self.on_cooldown = False


class Christmas(commands.Cog):

    def __init__(self, client: commands.bot):
        self.bot = client
        self.pool = client.pool
        self.manager = CooldownManager(self.bot.loop, cooldown=30)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if self.manager.on_cooldown:
            return
        if message.author == message.guild.me or message.author.id in (329668530926780426, 172002275412279296, 603216263484801039) or message.author.bot:
            return
        if random.choices((True, False), weights=[5, 45])[0]:
            print('a')
            self.manager.activate()
            emoji = random.choice(('🎁', '🧸', '⚽', '🕹️', '🕯️'))
            await message.add_reaction(emoji)
            con = await self.pool.acquire()
            def present_check(rea: discord.Reaction, u):
                return rea.message.id == message.id and str(rea.emoji) == emoji and u.id != self.bot.user.id and u.id != self.bot.owner_id
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
        embed = discord.Embed()
        embed.set_author(name='Christmas Event', icon_url='https://images.theconversation.com/files/249293/original/file-20181206-128196-12nfo28.jpg?ixlib=rb-1.1.0&q=45&auto=format&w=1200&h=1200.0&fit=crop')
        embed.description = "```It's close to christmas.\n\nPresent production has long been outsourced as Elf wages have been going through the roof,\nand Santa is in a rush to collect presents from factories around the world.\n\n" \
                            "After one of his trips to a factory, Santa discovers a hole in one of his magic bags. All the presents are gone!\nSanta is at his budget limit, and can't afford to have the presents be produced again.\n\n" \
                            "Help Santa out by picking up stray presents you find! They will appear randomly as reactions on messages. Click on the reaction to pick the present up, return it to santa and climb up the Santa's list!\n\n" \
                            "Use command $me to see your stats, and command $event to see the overall leaderboard!```"
        embed.color = discord.Color.red()
        await ctx.send(embed=embed)


    @commands.command()
    async def winner(self, ctx):
        con = await self.pool.acquire()
        em = discord.Embed(color=discord.Color.gold(), title='Top Present Collectors')
        winners = await con.fetch('select id from christmas_users order by amt desc limit 3')
        em.description = f'''Ho Ho Ho! Thank you all for saving Christmas! Special Thanks to our Top Present Collectors!\n
        **{await ctx.guild.fetch_member(winners[0][0])}** found the most presents among all participants!\n Coming in second is **{await ctx.guild.fetch_member(winners[1][0])}**!\nAnd finally, **{await ctx.guild.fetch_member(winners[2][0])}** earned themselves the bronze medal!!\n\n Thank you all for participating! Hopefully you had some fun!'''
        em.set_author(
            icon_url='https://images.theconversation.com/files/249293/original/file-20181206-128196-12nfo28.jpg?ixlib=rb-1.1.0&q=45&auto=format&w=1200&h=1200.0&fit=crop',
            name='Christmas Event')
        await ctx.send(embed=em)
        await self.pool.release(con)

    @commands.command(aliases=["eventstats", "event", "hw"])
    async def leaderboard(self, ctx: commands.Context):
        con = await self.pool.acquire()
        p = """SELECT SUM(amt) FROM christmas_users"""
        u = """SELECT id, amt from christmas_users order by amt desc"""

        presents = await con.fetchrow(p)
        leaders_li = await con.fetch(u)


        # leaders = '\n'.join([f'{num}. {st}' for num, st in enumerate([f'{ctx.guild.get_member(user[0]).name}\t|\t{user[1]}' for user in leaders], start=1)])

        leaders = prettytable.PrettyTable(field_names=('Place', 'Member', 'Presents'))
        leaders.add_rows([[place, tup[0], tup[1]] for place, tup in enumerate([[ctx.guild.get_member(u[0]).name, u[1]] for u in leaders_li], start=1)])
        embed = discord.Embed(title='Event Stats')
        embed.add_field(name="Santa's List", value=f"```{leaders.get_string()}```")
        embed.add_field(name="Presents in total", value=f"{presents[0]}", inline=False)
        embed.set_author(
            icon_url='https://images.theconversation.com/files/249293/original/file-20181206-128196-12nfo28.jpg?ixlib=rb-1.1.0&q=45&auto=format&w=1200&h=1200.0&fit=crop',
            name='Christmas Event')
        embed.set_footer(text=f"Command used by {ctx.author.display_name}", icon_url=ctx.author.avatar_url)
        embed.color = discord.Color.dark_green()
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
            icon_url='https://images.theconversation.com/files/249293/original/file-20181206-128196-12nfo28.jpg?ixlib=rb-1.1.0&q=45&auto=format&w=1200&h=1200.0&fit=crop',
            text='Christmas Event').set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        embed.color = discord.Color.dark_green()
        await ctx.send(embed=embed)
        await self.pool.release(con)

    @me.error
    async def handle(self, ctx, error):
        await ctx.send(f"Sorry, it seems like an error occured. Please try again. \n```{error}```")

def setup(bot: commands.bot):
    bot.add_cog(Christmas(bot))


