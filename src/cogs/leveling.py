import discord
import random
import json
import datetime

from ..helpers.cooldownmgr import CooldownManager
from ..util.levels_xp import levels
from discord.ext import commands


class Leveling(commands.Cog):

    def __init__(self, client):
        self.bot = client
        self.pool = client.pool
        self.cdmanager = CooldownManager(client.loop)

    @commands.Cog.listener()
    async def on_ready(self):

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        con = await self.pool.acquire()

        author_id = message.author.id
        user_query = """SELECT * FROM users WHERE discord_id=$1"""
        user_info = await con.fetchrow(user_query, author_id)

        if not user_info:
            create_user_query = """INSERT INTO users (discord_id, username, level, xp) VALUES ($1, $2, $3, $4) ON CONFLICT DO NOTHING"""
            await con.execute(create_user_query, author_id,
                              message.author.name, 0, 0)
        else:
            if self.cdmanager.on_cooldown(author_id):
                return

            fianl_xp = user_info['xp'] + random.randint(15, 30)
            final_level = user_info['level']

            if fianl_xp > levels[user_info['level']+1][0]:
                print('level up')
                final_level += 1
                if levels[final_level+1][1] is not None:
                    role_name = levels[final_level+1][1]
                    role = discord.utils.get(
                        message.guild.roles, name=role_name)
                    member = message.author
                    await member.add_roles(role)

            give_xp_query = """UPDATE users SET xp=$1, level=$2 WHERE discord_id=$3"""
            await con.execute(give_xp_query, fianl_xp,
                              final_level, user_info['discord_id'])
            self.cdmanager.add(author_id)

        await self.pool.release(con)

    # @commands.command()
    # async def addme(self, ctx):
    #     id = ctx.message.author.id
    #     username = ctx.message.author.name

    #     con = await self.pool.acquire()
    #     query1 = """SELECT * FROM users WHERE discord_id=$1"""
    #     user_info = await con.fetchrow(query1, id)

    #     if not user_info:
    #         time_control = datetime.datetime.utcfromtimestamp(0)

    #         query_add = """INSERT INTO users (discord_id, username, level, xp, cooldown) values ($1,$2,$3,$4,$5)"""
    #         current_cd = (datetime.datetime.utcnow() -
    #                       time_control).total_seconds()
    #         await con.execute(query_add, id, username, 0, 0, current_cd)

    #         await ctx.send('User added successfully')
    #     else:
    #         await ctx.send('User already in the DB')

    #     await self.pool.release(con)


def setup(bot: commands.bot):
    bot.add_cog(Leveling(bot))
