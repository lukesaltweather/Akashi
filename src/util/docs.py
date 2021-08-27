import os
import subprocess
from typing import List

import discord
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


def parse_rst(text: str) -> docutils.nodes.document:
    parser = docutils.parsers.rst.Parser()
    components = (docutils.parsers.rst.Parser,)
    settings = docutils.frontend.OptionParser(components=components).get_default_values()
    document = docutils.utils.new_document('<rst-doc>', settings=settings)
    parser.parse(text, document)
    return document

class MyVisitor(docutils.nodes.NodeVisitor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sections = dict()
        self.params = dict()
        self.curr_field = None
        self.current_section = None
        self.required = False

    def visit_paragraph(self, node: docutils.nodes.paragraph):
        self.sections[self.current_section] = node.astext()

    def visit_document(self, node):
        pass

    def visit_section(self, node: docutils.nodes.section):
        pass

    def visit_title(self, node: docutils.nodes.title):
        self.current_section = node.astext()

    def visit_Text(self, node: docutils.nodes.Text):
        pass

    def visit_title_reference(self, node):
        pass

    def visit_field_list(self, node: docutils.nodes.field_list):
        if self.current_section == "Required":
            self.required = True
        elif self.current_section == "Optional":
            self.required = False

    def depart_field_list(self, node: docutils.nodes.field_list):
        self.required = False

    def visit_field(self, node: docutils.nodes.field):
        pass

    def visit_field_name(self, node: docutils.nodes.field_name):
        self.curr_field = f"{node.astext()} {'(Required)' if self.required else ''}"

    def visit_field_body(self, node: docutils.nodes.field_body):
        self.params[self.curr_field] = node.astext()

    def visit_image(self, node: docutils.nodes.image):
        pass

    def visit_caution(self, node: docutils.nodes.caution):
        pass

    def visit_warning(self, node: docutils.nodes.warning):
        pass

    def visit_error(self, node: docutils.nodes.error):
        pass

    def visit_danger(self, node: docutils.nodes.danger):
        pass

    def unknown_visit(self, node: docutils.nodes.Node) -> None:
        """Called for all other node types."""
        pass

    def unknown_departure(self, node):
        pass