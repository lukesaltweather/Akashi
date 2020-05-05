from discord.ext import commands
import asyncpg
from uuid import uuid4
import boto3


class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(enabled=False)
    async def get_csv(self, ctx):
        query = """                   SELECT
                    chapters.id, projects.title, chapters.number as chapternumber, chapters.title, translator.name as translator, redrawer.name as redrawer, typesetter.name as typesetter, proofreader.name as proofreader, date_created, date_tl, date_rd, date_ts, date_pr, date_qcts, date_release
                    FROM chapters
                    LEFT OUTER JOIN projects ON chapters.project_id = projects.id
                    LEFT OUTER JOIN staff translator ON chapters.translator_id = translator.id
                    LEFT OUTER JOIN staff redrawer ON chapters.redrawer_id = redrawer.id
                    LEFT OUTER JOIN staff typesetter ON chapters.typesetter_id = typesetter.id
                    LEFT OUTER JOIN staff proofreader ON chapters.proofreader_id = proofreader.id"""
        con = await asyncpg.connect(self.bot.config["db_uri"])
        i = uuid4()
        await con.copy_from_query(query, output=f'files/{i}.csv', format='csv', delimiter=',', header=True)
        object = f"public/{str(i)}.csv"
        s3.Bucket('akashi-csvs').upload_file(f"files/{str(i)}.csv", object)
        url = f"http://s3-eu-central-1.amazonaws.com/akashi-csvs/{object}"
        await ctx.author.send(url)

    @commands.command(enabled=False)
    async def read_only_user(self, ctx):
        pass

def setup(bot):
    bot.add_cog(Stats(bot))