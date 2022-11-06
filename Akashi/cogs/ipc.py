from discord.ext import commands, ipc
import discord

from Akashi.util.misc import format_number


class IpcRoutes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @ipc.server.route()  # type: ignore
    async def TL(self, data):
        guild = self.bot.get_guild(345797456614785024)
        author = guild.get_member(int(data.user))

        next_step = data.next_step
        next_step = next_step.upper()
        chapter = data.chapter
        project = data.project

        e = discord.Embed()
        mention = None

        if data.next_role == "member":
            mem = guild.get_member(int(data.next_id))
            e = discord.Embed(color=discord.Colour.green())
            e.set_author(
                name=f"Next up: {mem.display_name} | {next_step}",
                icon_url=mem.avatar_url,
            )
            e.description = f"{author.mention} finished `{project}` Ch. `{format_number(chapter)}` | TL\n"
            e.description = f"{e.description}\n[Link]({data.link})"
            e.set_footer(
                text=f"Step finished by {author.display_name}",
                icon_url=author.avatar_url,
            )
            mention = mem.mention
        else:
            mem = guild.get_role(int(data.next_id))
            e = discord.Embed(color=discord.Colour.red())
            e.set_author(name=f"Next up: {mem.display_name} | {next_step}")
            e.description = f"{author.mention} finished `{project}` Ch. `{format_number(chapter)}` | TL\n"
            e.description = f"{e.description}\n[Link]({data.link})"
            e.set_footer(
                text=f"Step finished by {author.display_name}",
                icon_url=author.avatar_url,
            )
            mention = ""

        channel = guild.get_channel(408848958232723467)
        await channel.send(
            mention,
            embed=e,
            allowed_mentions=discord.AllowedMentions(
                everyone=False, users=True, roles=False
            ),
        )

    @ipc.server.route()  # type: ignore
    async def RD(self, data):
        guild = self.bot.get_guild(345797456614785024)
        author = guild.get_member(int(data.user))

        next_step = data.next_step
        next_step = next_step.upper()
        chapter = data.chapter
        project = data.project

        e = discord.Embed()
        mention = None

        if data.next_role == "member":
            mem = guild.get_member(int(data.next_id))
            e = discord.Embed(color=discord.Colour.green())
            e.set_author(
                name=f"Next up: {mem.display_name} | {next_step}",
                icon_url=mem.avatar_url,
            )
            e.description = f"{author.mention} finished `{project}` Ch. `{format_number(chapter)}` | RD\n"
            e.description = f"{e.description}\n[Link]({data.link})"
            e.set_footer(
                text=f"Step finished by {author.display_name}",
                icon_url=author.avatar_url,
            )
            mention = mem.mention
        else:
            mem = guild.get_role(int(data.next_id))
            e = discord.Embed(color=discord.Colour.red())
            e.set_author(name=f"Next up: {mem.display_name} | {next_step}")
            e.description = f"{author.mention} finished `{project}` Ch. `{format_number(chapter)}` | RD\n"
            e.description = f"{e.description}\n[Link]({data.link})"
            e.set_footer(
                text=f"Step finished by {author.display_name}",
                icon_url=author.avatar_url,
            )
            mention = ""

        channel = guild.get_channel(408848958232723467)
        await channel.send(
            mention,
            embed=e,
            allowed_mentions=discord.AllowedMentions(
                everyone=False, users=True, roles=False
            ),
        )

    @ipc.server.route()  # type: ignore
    async def TS(self, data):
        guild = self.bot.get_guild(345797456614785024)
        author = guild.get_member(int(data.user))

        next_step = data.next_step
        next_step = next_step.upper()
        chapter = data.chapter
        project = data.project

        e = discord.Embed()
        mention = None

        if data.next_role == "member":
            mem = guild.get_member(int(data.next_id))
            e = discord.Embed(color=discord.Colour.green())
            e.set_author(
                name=f"Next up: {mem.display_name} | {next_step}",
                icon_url=mem.avatar_url,
            )
            e.description = f"{author.mention} finished `{project}` Ch. `{format_number(chapter)}` | TS\n"
            e.description = f"{e.description}\n[Link]({data.link})"
            e.set_footer(
                text=f"Step finished by {author.display_name}",
                icon_url=author.avatar_url,
            )
            mention = mem.mention
        else:
            mem = guild.get_role(int(data.next_id))
            e = discord.Embed(color=discord.Colour.red())
            e.set_author(name=f"Next up: {mem.display_name} | {next_step}")
            e.description = f"{author.mention} finished `{project}` Ch. `{format_number(chapter)}` | TS\n"
            e.description = f"{e.description}\n[Link]({data.link})"
            e.set_footer(
                text=f"Step finished by {author.display_name}",
                icon_url=author.avatar_url,
            )
            mention = ""

        channel = guild.get_channel(408848958232723467)
        await channel.send(
            mention,
            embed=e,
            allowed_mentions=discord.AllowedMentions(
                everyone=False, users=True, roles=False
            ),
        )

    @ipc.server.route()  # type: ignore
    async def PR(self, data):
        guild = self.bot.get_guild(345797456614785024)
        author = guild.get_member(int(data.user))

        next_step = data.next_step
        next_step = next_step.upper()
        chapter = data.chapter
        project = data.project

        e = discord.Embed()
        mention = None

        if data.next_role == "member":
            mem = guild.get_member(int(data.next_id))
            e = discord.Embed(color=discord.Colour.green())
            e.set_author(
                name=f"Next up: {mem.display_name} | {next_step}",
                icon_url=mem.avatar_url,
            )
            e.description = f"{author.mention} finished `{project}` Ch. `{format_number(chapter)}` | PR\n"
            e.description = f"{e.description}\n[Link]({data.link})"
            e.set_footer(
                text=f"Step finished by {author.display_name}",
                icon_url=author.avatar_url,
            )
            mention = mem.mention
        else:
            mem = guild.get_role(int(data.next_id))
            e = discord.Embed(color=discord.Colour.red())
            e.set_author(name=f"Next up: {mem.display_name} | {next_step}")
            e.description = f"{author.mention} finished `{project}` Ch. `{format_number(chapter)}` | PR\n"
            e.description = f"{e.description}\n[Link]({data.link})"
            e.set_footer(
                text=f"Step finished by {author.display_name}",
                icon_url=author.avatar_url,
            )
            mention = ""

        channel = guild.get_channel(408848958232723467)
        await channel.send(
            mention,
            embed=e,
            allowed_mentions=discord.AllowedMentions(
                everyone=False, users=True, roles=False
            ),
        )

    @ipc.server.route()  # type: ignore
    async def QCTS(self, data):
        guild = self.bot.get_guild(345797456614785024)
        author = guild.get_member(int(data.user))

        next_step = data.next_step
        next_step = next_step.upper()
        chapter = data.chapter
        project = data.project

        e = discord.Embed()
        mention = None

        if data.next_role == "member":
            mem = guild.get_member(int(data.next_id))
            e = discord.Embed(color=discord.Colour.green())
            e.set_author(
                name=f"Next up: {mem.display_name} | {next_step}",
                icon_url=mem.avatar_url,
            )
            e.description = f"{author.mention} finished `{project}` Ch. `{format_number(chapter)}` | QCTS\n"
            e.description = f"{e.description}\n[Link]({data.link})"
            e.set_footer(
                text=f"Step finished by {author.display_name}",
                icon_url=author.avatar_url,
            )
            mention = mem.mention
        else:
            mem = guild.get_role(int(data.next_id))
            e = discord.Embed(color=discord.Colour.red())
            e.set_author(name=f"Next up: {mem.display_name} | {next_step}")
            e.description = f"{author.mention} finished `{project}` Ch. `{format_number(chapter)}` | QCTS\n"
            e.description = f"{e.description}\n[Link]({data.link})"
            e.set_footer(
                text=f"Step finished by {author.display_name}",
                icon_url=author.avatar_url,
            )
            mention = ""

        channel = guild.get_channel(408848958232723467)
        await channel.send(
            mention,
            embed=e,
            allowed_mentions=discord.AllowedMentions(
                everyone=False, users=True, roles=False
            ),
        )


async def setup(bot):
    await bot.add_cog(IpcRoutes(bot))
