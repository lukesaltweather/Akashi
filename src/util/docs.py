from typing import List
import docutils

if __name__ == "__main__":
    from discord.ext import commands
    class Bot(commands.Bot):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

        def build_docs(self, path="docs/"):
            cmds = self.walk_commands()
            cmds: List[commands.Command]
            for command in cmds:
                docstr = command.help

    bot = Bot()
    bot.build_docs()

