import discord
import random

from ..helpers.cooldownmgr import CooldownManager
from ..util.levels_xp import levels
from discord.ext import commands


class Leveling(commands.Cog):

    def __init__(self, client):
        self.bot = client
        self.pool = client.pool
        self.cdmanager = CooldownManager(client.loop)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        author_id = message.author.id

        if self.cdmanager.on_cooldown(author_id):
            return

        con = await self.pool.acquire()
        user_query = """SELECT * FROM users WHERE discord_id=$1"""
        user_info = await con.fetchrow(user_query, author_id)

        if not user_info:
            create_user_query = """INSERT INTO users (discord_id, username, level, xp) VALUES ($1, $2, $3, $4) ON CONFLICT DO NOTHING"""
            await con.execute(create_user_query, author_id,
                              message.author.name, 0, 0)
        else:
            final_xp = user_info['xp'] + random.randint(15, 30)
            final_level = user_info['level']

            if final_xp > levels[user_info['level']+1][0]:
                final_level += 1
                channel = message.channel

                if levels[final_level+1][1] is not None:
                    role_name = levels[final_level+1][1]
                    role = discord.utils.get(
                        message.guild.roles, name=role_name)
                    member = message.author
                    await member.add_roles(role)
                    await channel.send(f'Congratulations, {message.author}! You just advanced to level {final_level}, enjoy your new fancy role - {role}')

                await channel.send(f'Congratulations, {message.author}! You just advanced to level {final_level}')

            give_xp_query = """UPDATE users SET xp=$1, level=$2 WHERE discord_id=$3"""
            await con.execute(give_xp_query, final_xp,
                              final_level, user_info['discord_id'])
            self.cdmanager.add(author_id)

        await self.pool.release(con)


def setup(bot: commands.bot):
    bot.add_cog(Leveling(bot))
