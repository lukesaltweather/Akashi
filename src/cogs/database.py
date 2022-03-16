import datetime
import io
import logging
import subprocess

import discord
from discord.ext import commands, tasks

from src.util.checks import is_admin


class Database(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.auto_backup.start()

    @tasks.loop(hours=24, reconnect=True)
    async def auto_backup(self):
        channel = await self.bot.fetch_channel(
            self.bot.config["server"]["channels"]["backups"]
        )
        buffer = io.BytesIO()
        try:
            process = subprocess.Popen(
                [
                    "pg_dump",
                    "-Fc",
                    "-h",
                    "localhost",
                    "--no-password",
                    "-U",
                    "Akashi",
                    "-t",
                    "chapters",
                    "-t",
                    "projects",
                    "-t",
                    "note",
                    "-t",
                    "staff",
                    "Akashi",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            buffer = io.BytesIO(process.stdout.read())
        except Exception as e:
            logging.getLogger("akashi.db").debug(
                f"Error while backing up the database: {e}"
            )
            return
        buffer.seek(0)
        file = discord.File(
            buffer, datetime.datetime.utcnow().strftime("akashi-backup-%Y-%m-%d.dump")
        )
        bkp_message = self.bot.config["server"].get("bkp_message", None)
        if bkp_message:
            msg = await channel.fetch_message(self.bot.config["server"]["bkp_message"])
            await msg.edit(
                f"Here's the backup on {datetime.datetime.utcnow().strftime('%Y-%m-%d')}.\n"
                "See https://docs.akashi.app/developers/restore_backup.html for info on how to restore the backup.",
                attachments=[file],
            )
        else:
            new_message = await channel.send(
                "Here's todays backup.\n"
                "See https://docs.akashi.app/developers/restore_backup.html for info on how to restore the backup.",
                file=file,
            )
            self.bot.config["server"]["bkp_message"] = new_message.id
            await self.bot.save_config()

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
        process = subprocess.Popen(
            [
                "pg_dump",
                "-Fc",
                "-h",
                "localhost",
                "--no-password",
                "-U",
                "Akashi",
                "-t",
                "chapters",
                "-t",
                "projects",
                "-t",
                "note",
                "-t",
                "staff",
                "Akashi",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        buffer = io.BytesIO(process.stdout.read())

        buffer.seek(0)
        file = discord.File(
            buffer,
            datetime.datetime.utcnow().strftime("akashi-manual-backup-%Y-%m-%d.dump"),
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
