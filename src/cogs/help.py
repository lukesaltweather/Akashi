import inspect
import itertools

import discord
from discord.ext import commands
from discord.ext import menus
from typing import List
from discord.ext.commands.core import Group, Command

from src.util import exceptions
from src.util.docs import parse_rst, MyVisitor


class Source(menus.ListPageSource):
    def __init__(self, embeds: List[discord.Embed]):
        super().__init__(embeds, per_page=1)

    async def format_page(self, menu, page):
        return page


class MyHelpCommand(commands.MinimalHelpCommand):
    def __init__(self, **options):
        self.sort_commands = options.pop("sort_commands", True)
        self.commands_heading = options.pop("commands_heading", "Commands")
        self.dm_help = options.pop("dm_help", False)
        self.dm_help_threshold = options.pop("dm_help_threshold", 1000)
        self.aliases_heading = options.pop("aliases_heading", "Aliases:")
        self.no_category = options.pop("no_category", "No Category")
        self.paginator = options.pop("paginator", None)
        super().__init__(**options)

    async def prepare_help_command(self, ctx, command):
        self.helper = EmbedHelper()

    async def command_callback(self, ctx, *, command=None):
        """|coro|

        The actual implementation of the help command.

        It is not recommended to override this method and instead change
        the behaviour through the methods that actually get dispatched.

        - :meth:`send_bot_help`
        - :meth:`send_cog_help`
        - :meth:`send_group_help`
        - :meth:`send_command_help`
        - :meth:`get_destination`
        - :meth:`command_not_found`
        - :meth:`subcommand_not_found`
        - :meth:`send_error_message`
        - :meth:`on_help_command_error`
        - :meth:`prepare_help_command`
        """
        await self.prepare_help_command(ctx, command)
        bot = ctx.bot

        if command is None:
            mapping = self.get_bot_mapping()
            return await self.send_bot_help(mapping)

        # Check if it's a cog
        cog = bot.get_cog_insensitive(command)
        if cog is not None:
            return await self.send_cog_help(cog)

        maybe_coro = discord.utils.maybe_coroutine

        # If it's not a cog then it's a command.
        # Since we want to have detailed errors when someone
        # passes an invalid subcommand, we need to walk through
        # the command group chain ourselves.
        keys = command.split(" ")
        cmd = bot.all_commands.get(keys[0])
        if cmd is None:
            string = await maybe_coro(
                self.command_not_found, self.remove_mentions(keys[0])
            )
            return await self.send_error_message(string)

        for key in keys[1:]:
            try:
                found = cmd.all_commands.get(key)
            except AttributeError:
                string = await maybe_coro(
                    self.subcommand_not_found, cmd, self.remove_mentions(key)
                )
                return await self.send_error_message(string)
            else:
                if found is None:
                    string = await maybe_coro(
                        self.subcommand_not_found, cmd, self.remove_mentions(key)
                    )
                    return await self.send_error_message(string)
                cmd = found

        if isinstance(cmd, Group):
            return await self.send_group_help(cmd)
        else:
            return await self.send_command_help(cmd)

    def get_command_signature(self, command):
        return "{0.clean_prefix}{1.qualified_name} {1.signature}".format(self, command)

    async def send_bot_help(self, mapping):
        ctx = self.context
        bot = ctx.bot

        no_category = "\u200b{0.no_category}".format(self)

        def get_category(command, *, no_category=no_category):
            cog = command.cog
            return cog.qualified_name if cog is not None else no_category

        filtered = await self.filter_commands(bot.commands, sort=True, key=get_category)
        to_iterate = itertools.groupby(filtered, key=get_category)

        for category, commands in to_iterate:
            commands = (
                sorted(commands, key=lambda c: c.name)
                if self.sort_commands
                else list(commands)
            )
            if category != "MyCog":
                self.helper.start_page(commands, category)
                self.helper.add_cog(commands, category)

        await self.send_pages()
        self.helper.clear()

    async def send_command_help(self, command):
        self.helper.clear()
        self.helper.add_command(command)
        await self.get_destination().send(embed=self.helper.embed[0])

    async def send_cog_help(self, cog: commands.Cog):
        cogcommands = cog.get_commands()
        filtered = await self.filter_commands(cogcommands, sort=True)
        self.helper.add_cog(filtered, cog.qualified_name)
        await self.get_destination().send(embed=self.helper.embed[1])

    async def send_pages(self):
        menu = HelpMenu(
            source=Source(self.helper.allembeds()),
            delete_message_after=True,
            timeout=60,
        )
        await menu.start(self.context)


class MyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._original_help_command = bot.help_command
        bot.help_command = MyHelpCommand(dm_help=True)
        bot.help_command.cog = self

    def cog_unload(self):
        self.bot.help_command = self._original_help_command


class HelpMenu(menus.MenuPages):
    @menus.button("🔢", position=menus.Last(1))
    async def select_page(self, payload):
        channel = self.bot.get_channel(payload.channel_id)
        i = await channel.send(
            "Please enter the page you want to skip to:", delete_after=30
        )

        def check(msg):
            return (
                msg.channel.id == payload.channel_id
                and msg.author.id == self.ctx.author.id
            )

        try:
            message = await self.bot.wait_for("message", check=check, timeout=30)
        except Exception:
            # timeout
            return
        else:
            await i.delete()
        await message.delete()
        try:
            msg_int = int(message.content)
            await self.show_checked_page(msg_int - 1)
        except Exception:
            await self.ctx.send("Please enter a valid number...", delete_after=30)

    async def show_checked_page(self, page_number):
        max_pages = self._source.get_max_pages()
        try:
            if max_pages is None:
                # If it doesn't give maximum pages, it cannot be checked
                await self.show_page(page_number)
            elif max_pages > page_number >= 0:
                await self.show_page(page_number)
        except IndexError:
            # An error happened that can be handled, so ignore it.
            await self.ctx.send("This page doesn't exist...", delete_after=30)


class EmbedHelper:
    """Create an Embed for the help command"""

    def __init__(self):
        self.embed = list()
        self.page = 1
        self.cog_counter = 2

    def start_page(self, commands, cog):
        if len(self.embed) == 0:
            self.embed.append(discord.Embed(color=discord.Colour.dark_blue()))
            self.embed[0].set_author(
                name="Help",
                icon_url="https://rei.animecharactersdatabase.com/uploads/chars/9225-1377974027.png",
            )
            self.embed[0].title = "Akashi Help"
            self.embed[0].url = "https://docs.lukesaltweather.de"
            self.embed[0].set_footer(
                icon_url="https://upload.wikimedia.org/wikipedia/commons/thumb/2/25/Info_icon-72a7cf.svg/1200px-Info_icon-72a7cf.svg.png",
                text="For more detailed help on a command, use $help <command>",
            )
        else:
            string = f"\n\n**{cog}**  |  Page: **{self.page+1}**\n"
            first = True
            for command in commands:
                if first:
                    string = f"{string} **`{command.name}`**"
                else:
                    string = f"{string} | **`{command.name}`**"

            self.embed[0].description = f"{self.embed[0].description}{string}"
        self.page = self.page + 1

    def add_cog(self, coms, cogname: str):
        self.embed.append(discord.Embed(color=discord.Colour.dark_blue()))
        emoji = {
            "Info": "🔎",
            "Add": "📥",
            "Misc": "📎",
            "Edit": "📝",
            "Assign": "🙋",
            "Done": "👍",
            "Note": "🗒️",
            "ReminderCog": "📅",
            "Tags": "📓",
        }.pop(cogname, False)
        if not emoji:
            return
        self.embed[-1].set_author(name=f"{emoji} {cogname}")
        string = ""
        for command in coms:
            if command.callback.__doc__:
                docstring = inspect.cleandoc(command.callback.__doc__)
                parsed = parse_rst(docstring)
                v = MyVisitor(parsed)
                parsed.walkabout(v)
                string = f"{string}\n[**`{command.name}`**]({command.usage}){v.sections.get('Description', '')}"
        self.embed[-1].description = string
        self.embed[-1].set_footer(
            icon_url="https://upload.wikimedia.org/wikipedia/commons/thumb/2/25/Info_icon-72a7cf.svg/1200px-Info_icon-72a7cf.svg.png",
            text=f"Page {self.cog_counter} | For more detailed help on a command, use $help <command>",
        )
        self.cog_counter = self.cog_counter + 1

    def add_command(self, command):
        self.embed.append(discord.Embed(color=discord.Colour.dark_blue()))
        self.embed[-1].set_author(
            name=command.name,
            icon_url="https://rei.animecharactersdatabase.com/uploads/chars/9225-1377974027.png",
        )
        self.embed[-1].title = "Docs"
        self.embed[-1].url = command.usage
        if command.callback.__doc__:
            docstring = inspect.cleandoc(command.callback.__doc__)
            parsed = parse_rst(docstring)
            v = MyVisitor(parsed)
            parsed.walkabout(v)
            description = v.sections["Description"]
            aliases = ", ".join(command.aliases)
            parameters = v.params
        else:
            return
        for parameter, param_desc in parameters.items():
            self.embed[-1].add_field(
                name=parameter, value=f"`{param_desc}`", inline=False
            )
        self.embed[
            -1
        ].description = f"*Aliases*: `{aliases}`\n**Description:**\n```{description}```"

    def clear(self):
        self.embed = []

    def allembeds(self):
        return self.embed


def setup(Bot):
    Bot.add_cog(MyCog(Bot))
