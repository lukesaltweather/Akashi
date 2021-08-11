from discord.ext import commands


class CstmContext(commands.Context):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.session = self.bot.Session()
        