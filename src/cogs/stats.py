from discord.ext import commands
import asyncpg
from uuid import uuid4
import boto3


class Backup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(enabled=False)
    async def backup(self, ctx):
        pass

    @commands.command(enabled=False)
    async def read_only_user(self, ctx):
        pass


def setup(bot):
    bot.add_cog(Backup(bot))
