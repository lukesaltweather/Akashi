import logging

from attr import dataclass
from discord import embeds
from discord.ext import commands, tasks
from src.util.checks import is_admin
import asyncpg
from uuid import uuid4
import boto3
import io
import subprocess
import discord
import datetime


class Database(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.auto_backup.start()

    @tasks.loop(hours=24, reconnect=True)
    async def auto_backup(self):
        channel = await self.bot.fetch_channel(
            self.bot.config["server"]["channels"]["backups"]
        )
        initial_msg = await channel.send("Backing up the database...")
        buffer = io.BytesIO()
        try:
            subprocess.Popen(
                [
                    "pg_dump",
                    "-Fc",
                    "-h localhost",
                    "--no-password",
                    "-U Akashi",
                    "-t chapters",
                    "-t projects",
                    "-t note",
                    "-t staff",
                    "Akashi",
                ],
                stdout=buffer,
            )
        except Exception as e:
            logging.getLogger("akashi.db").debug(f"Error while backing up the database: {e}")
            return
        buffer.seek(0)
        file = discord.File(
            buffer, datetime.datetime.utcnow().strftime("akashi-backup-%Y-%m-%d.dump")
        )
        await channel.send(
            "Here's todays backup.\n"
            "See https://docs.akashi.app/developers/restore_backup.html for info on how to restore the backup.",
            file=file,
        )
        await initial_msg.delete()

    @commands.command()
    @is_admin()
    async def backup(self, ctx):
        """
        Description
        ==============
        Manually backups the database and sends the resulting backup as a message attachment.

        Required Role
        =====================
        Role `Neko Herders`.
        """
        initial_msg = await ctx.send("Backing up the database...")
        buffer = io.BytesIO()
        subprocess.Popen(
            [
                "pg_dump",
                "-Fc",
                "-h localhost",
                "--no-password",
                "-U Akashi",
                "-t chapters",
                "-t projects",
                "-t note",
                "-t staff",
                "Akashi",
            ],
            stdout=buffer,
        )

        buffer.seek(0)
        file = discord.File(
            buffer, datetime.datetime.utcnow().strftime("akashi-manual-backup-%Y-%m-%d.dump")
        )
        await ctx.reply(
            "Backup complete.\n"
            "See https://docs.akashi.app/en/stable/Developers/restore_backup.html for info on how to restore the backup.",
            file=file,
        )
        await initial_msg.delete()

    @commands.command(enabled=False)
    async def read_only_user(self, ctx):
        pass


def setup(bot):
    bot.add_cog(Database(bot))
