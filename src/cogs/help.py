import inspect
import itertools

import discord
from discord.ext import commands

from src.util import exceptions


class MyHelpCommand(commands.MinimalHelpCommand):

    def __init__(self, **options):
        self.sort_commands = options.pop('sort_commands', True)
        self.commands_heading = options.pop('commands_heading', "Commands")
        self.dm_help = options.pop('dm_help', False)
        self.dm_help_threshold = options.pop('dm_help_threshold', 1000)
        self.aliases_heading = options.pop('aliases_heading', "Aliases:")
        self.no_category = options.pop('no_category', 'No Category')
        self.paginator = options.pop('paginator', None)
        self.helper = EmbedHelper()


        super().__init__(**options)

    def get_command_signature(self, command):
        return '{0.clean_prefix}{1.qualified_name} {1.signature}'.format(self, command)

    async def send_bot_help(self, mapping):
        ctx = self.context
        bot = ctx.bot
        self.helper.reset()

        if bot.description:
            self.paginator.add_line(bot.description, empty=True)

        note = self.get_opening_note()
        if note:
            self.paginator.add_line(note, empty=True)

        no_category = '\u200b{0.no_category}'.format(self)
        def get_category(command, *, no_category=no_category):
            cog = command.cog
            return cog.qualified_name if cog is not None else no_category

        filtered = await self.filter_commands(bot.commands, sort=True, key=get_category)
        to_iterate = itertools.groupby(filtered, key=get_category)

        for category, commands in to_iterate:
            commands = sorted(commands, key=lambda c: c.name) if self.sort_commands else list(commands)
            if category != "MyCog":
                self.helper.add_cog(commands, category)

        note = self.get_ending_note()
        if note:
            self.paginator.add_line()
            self.paginator.add_line(note)

        await self.context.message.add_reaction("📧")
        await self.send_pages(cat="")

    async def send_command_help(self, command):
        self.helper.clear()
        self.helper.add_command(command)
        await self.send_pages(cat="command")

    async def send_pages(self, cat):
        if cat == "command":
            destination = self.context
        else:
            destination = self.context.author
        for embed in self.helper.allembeds():
            await destination.send(embed=embed)



class MyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._original_help_command = bot.help_command
        bot.help_command = MyHelpCommand(dm_help=True)
        bot.help_command.cog = self

    async def cog_check(self, ctx):
        worker = ctx.guild.get_role(self.bot.config["neko_workers"])
        ia = worker in ctx.message.author.roles
        ic = ctx.channel.id == self.bot.config["command_channel"]
        guild = ctx.guild is not None
        if ia and ic and guild:
            return True
        elif ic:
            raise exceptions.MissingRequiredPermission("Wrong Channel.")
        elif not guild:
            raise exceptions.MissingRequiredPermission("Missing permission `Server Member`")

    def cog_unload(self):
        self.bot.help_command = self._original_help_command

class EmbedHelper:
    """Create an Embed for the help command"""
    def __init__(self):
        self.embed = [discord.Embed(color=discord.Colour.dark_green())]
        self.embed[0].set_author(name="Help", icon_url="https://rei.animecharactersdatabase.com/uploads/chars/9225-1377974027.png")
        self.embed[0].title = "Akashi Help"
        self.embed[0].url = "https://docs.lukesaltweather.de"
        self.embed[0].description = "Bot created by lukesaltweather@Nekyou.\nIf this help command doesn't help you with a problem, try visiting the docs first.\n" \
                                    "All commands are described in detail on there, as well as how to write commands in general."
        self.embed[0].set_footer(text="© Created by lukesaltweather#1111", icon_url="https://cdn.discordapp.com/avatars/358244935041810443/0c7effd92795854ef836c9ebe6404ff2.webp?size=1024")
    def add_cog(self, coms, cogname: str):
        self.embed.append(discord.Embed(color=discord.Colour.dark_green()))
        emoji = {
            "Info": "🔎",
            "Add": "📥",
            "Misc": "📎",
            "Edit": "📝",
            "Assign": "🙋",
            "Done": "👍",
            "Note": "🗒️"
        }.pop(cogname, "")
        self.embed[-1].set_author(name=f"{emoji} {cogname}")
        string = ""
        for command in coms:
            description = command.brief if command.description != "" else "No description"
            string = f"{string}[**`{command.name}`**]({command.help})\n*{description}*\n\n"
        self.embed[-1].description = string

    def add_command(self, command):
        self.embed.append(discord.Embed(color=discord.Colour.dark_green()))
        self.embed[-1].set_author(name=command.name, icon_url="https://rei.animecharactersdatabase.com/uploads/chars/9225-1377974027.png")
        self.embed[-1].title = "Docs"
        self.embed[-1].url = command.help
        description = command.description if command.description != "" else "No description"
        usage = ""
        parameters = command.usage
        for parameter in parameters:
            usage = f"{usage}`{parameter['p']}` {parameter['e']}\n"
        self.embed[-1].add_field(name='\u200b', value=f"__Description:__\n{description}", inline=False)
        self.embed[-1].add_field(name='\u200b', value=f"__Usage:__\n{usage}", inline=False)

    def reset(self):
        self.embed = []
        self.embed = [discord.Embed(color=discord.Colour.dark_green())]
        self.embed[0].set_author(name="Help",
                                 icon_url="https://rei.animecharactersdatabase.com/uploads/chars/9225-1377974027.png")
        self.embed[0].title = "Akashi Help"
        self.embed[0].url = "https://docs.lukesaltweather.de"
        self.embed[
            0].description = "Bot created by lukesaltweather@Nekyou.\nIf this help command doesn't help you with a problem, try visiting the docs first.\n" \
                             "All commands are described in detail on there, as well as how to write commands in general."
        self.embed[0].set_footer(text="© Created by lukesaltweather#1111", icon_url="https://cdn.discordapp.com/avatars/358244935041810443/0c7effd92795854ef836c9ebe6404ff2.webp?size=1024")

    def clear(self):
        self.embed = []

    def allembeds(self):
        return self.embed

def setup(Bot):
    Bot.add_cog(MyCog(Bot))