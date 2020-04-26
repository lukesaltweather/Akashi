from discord.ext import commands
import asyncpg

class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def get_csv(self):
        query = """SELECT
                    chapters.id, projects.title, chapters.number as chapternumber, chapters.title, translator.name as translator, redrawer.name as redrawer, typesetter.name as typesetter, proofreader.name as proofreader, date_created, date_tl, date_rd, date_ts, date_pr, date_qcts, date_release
                FROM chapters
                FULL OUTER JOIN projects ON chapters.project_id = projects.id
                FULL OUTER JOIN staff translator ON chapters.translator_id = translator.id
                FULL OUTER JOIN staff redrawer ON chapters.redrawer_id = redrawer.id
                FULL OUTER JOIN staff typesetter ON chapters.typesetter_id = typesetter.id
                FULL OUTER JOIN staff proofreader ON chapters.proofreader_id = proofreader.id;
                """
        con = await asyncpg.connect(self.bot.config["db_uri"])
        result = await con.copy_from_query(query, output='test.csv', format='csv')

def setup(bot):
    bot.add_cog(Stats(bot))