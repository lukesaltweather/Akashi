import os
import subprocess
from typing import List
import docutils.nodes
import docutils.parsers.rst
import docutils.utils
import docutils.frontend
from pathlib import Path


if __name__ == "__main__":
    from discord.ext import commands
    class Bot(commands.Bot):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

        def build_docs(self, path="docs/"):
            for cogname, cog in self.cogs.items():
                Path(f"docs/{cogname}").mkdir(parents=True, exist_ok=True)
                with open(f"docs/{cogname}/index.rst", "w+") as file:
                    file.write("==============================\n")
                    file.write(cogname)
                    file.write(f"""\n==============================
{cog.__cog_description__}

Commands
^^^^^^^^^^\n""")
                    commands = '\n    '.join(command.name for command in cog.walk_commands())
                    file.write(f""".. toctree::
    :maxdepth: 1

    {commands}
""")
                for command in cog.walk_commands():
                    command: commands.Command
                    with open(f"docs/{cogname}/{command.name}.rst", "w+") as file:
                        file.write("======================================================================\n")
                        file.write(f"{command.name}\n")
                        file.write("======================================================================\n")
                        if command.help:
                            file.write(command.help)

    bot = Bot(command_prefix="?")
    bot.load_extension('src.cogs.edit')
    bot.load_extension('src.cogs.misc')
    bot.load_extension('src.cogs.info')
    bot.load_extension('src.cogs.add')
    bot.load_extension('src.cogs.done')
    bot.load_extension('src.cogs.note')
    bot.load_extension('src.cogs.help')
    bot.load_extension('src.cogs.stats')
    bot.build_docs()