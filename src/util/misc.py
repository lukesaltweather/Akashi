import asyncio
import functools
import io
import json
from time import strftime
from typing import Any

import aiohttp
import discord
import prettytable
from discord import member
from PIL import Image, ImageDraw, ImageFont
from sqlalchemy import or_
from sqlalchemy.orm import sessionmaker


async def get_roles(member: discord.Member):
    """
    get a list of roles the user posesses
    @param member: discord user object
    @return: list of string, with possible entries ts, rd, pr and tl as string
    """
    with open('src/util/config.json', 'r') as f:
        config = json.load(f)
    return member.roles


async def has_role(user, role, bot):
    """
    returns whether discord user has role
    @param user: discord user object
    @param role: (string), can be ts, pr, rd or tl
    @param bot: bot instance
    @return: boolean
    """
    if role in get_roles(user, bot):
        return True
    return False

async def toggle_mentionable(role:discord.Role):
    """if not role.mentionable:
        await role.edit(mentionable=True)
    else:
        await role.edit(mentionable=False)"""
    pass


async def make_mentionable(role:discord.Role):
    # await role.edit(mentionable=True)
    return role.mention


async def disable_mentionable(role:discord.Role):
    # await role.edit(mentionable=False)
    pass

def strx(sti):
    if sti is None:
        return "\u200b"
    else:
        return sti

def strlist(stl:str):
    stlist = []
    for l in stl:
        if l is None:
            stlist.append("\u200b")
        else:
            stlist.append(l)
    return stlist

def is_ts(ctx):
    with open('src/util/config.json', 'r') as f:
        config = json.load(f)
    ts = discord.utils.find(lambda r: r.id == config["ts_id"], ctx.message.guild.roles)
    if ts in ctx.member.roles:
        return True
    return False

def is_tl(ctx):
    with open('src/util/config.json', 'r') as f:
        config = json.load(f)
    tl = discord.utils.find(lambda r: r.id == config["tl_id"], ctx.message.guild.roles)
    if tl in ctx.member.roles:
        return True
    return False

def is_rd(ctx):
    with open('src/util/config.json', 'r') as f:
        config = json.load(f)
    rd = discord.utils.find(lambda r: r.id == config["rd_id"], ctx.message.guild.roles)
    if rd in ctx.member.roles:
        return True
    return False

def is_pr(ctx):
    with open('src/util/config.json', 'r') as f:
        config = json.load(f)
    pr = discord.utils.find(lambda r: r.id == config["pr_id"], ctx.message.guild.roles)
    if pr in ctx.member.roles:
        return True
    return False

async def webhook(string):
    async with aiohttp.ClientSession() as session:
        webhook = discord.Webhook.from_url('https://discordapp.com/api/webhooks/695781829353144350/5K5v6t590fqBynVLTGfS0vafI43vDsvNE3zzl6gOzMHwwS1dDaa9HK2Zn53VsqbMTHvh', adapter=discord.AsyncWebhookAdapter(session))
        embed = discord.Embed(
            colour=discord.Colour.green()
        )
        embed.add_field(name="\u200b", value=f"```{string}```")
        await webhook.send(embed=embed, username="Akashi")


def drawimage(string):
    loop = asyncio.get_event_loop()
    thing = functools.partial(async_drawimage, string)
    return loop.run_in_executor(None, thing)

def async_drawimage(string):
    fontsize = 25  # starting font size
    font = ImageFont.truetype('src/util/fonts/DroidSansMono.ttf', fontsize)
    lines = string.split("\n")
    img = Image.new('RGB', (font.getsize(lines[0])[0]+40, len(lines)*30+70), color=(255, 255, 255))
    offset = 30
    margin = 20
    d = ImageDraw.Draw(img)
    for line in lines:
        d.text((margin, offset), line, font=font, fill="black")
        offset+=font.getsize(line)[1]
    arr = io.BytesIO()
    img.save(arr, format='PNG')
    arr.seek(0)
    file = discord.File(arr, "image.png")
    return file

def formatNumber(num):
    if num % 1 == 0:
        return int(num)
    else:
        return num

def table_one_chapter(**kwargs):
    session = kwargs["session"]
    table = prettytable.PrettyTable()
    for key, value in kwargs.items():
        if key == "ts":
            table.add_column("Typesetter", value)
        elif key == "title":
            table.add_column("Title", value)
        elif key == "tl":
            table.add_column("Translator", value)
        elif key == "pr":
            table.add_column("Proofreader", value)
        elif key == "rd":
            table.add_column("Redrawer", value)
        elif key == "project":
            table.add_column("Project", value)
        elif key == "chapter":
            table.add_column("Chapter", value)
        elif key == "link_tl":
            table.add_column("Translation", value)
        elif key == "link_rd":
            table.add_column("Redraws", value)
        elif key == "link_ts":
            table.add_column("Typeset", value)
        elif key == "link_pr":
            table.add_column("Proofread", value)
        elif key == "link_raw":
            table.add_column("Raws", value)
        elif key == "date_created":
            table.add_column("Created on", strftime(value))
        elif key == "date_tl":
            table.add_column("Translated on", strftime(value))
        elif key == "date_rd":
            table.add_column("Redrawn on", strftime(value))
        elif key == "date_ts":
            table.add_column("Typeset on", strftime(value))
        elif key == "date_pr":
            table.add_column("Proofread on", strftime(value))
    return table

class FakeUser(discord.Object):
    @property
    def avatar_url(self):
        return 'https://cdn.discordapp.com/embed/avatars/0.png'

    @property
    def display_name(self):
        return str(self.id)

    @property
    def mention(self):
        return str(self.id)

    @property
    def name(self):
        return str(self.id)

    def __str__(self):
        return str(self.id)


def divide_chunks(l, n):
    # looping till length l
    for i in range(0, len(l), n):
        yield l[i:i + n]

class BoardPaginator:
    def __init__(self, color, title=None, url="https://nekyou.com"):
        self.color = color
        self.title = title
        self.url = url
        self.current_length = 0
        self.embeds = list()
        self.thumbnail = ""

    def __len__(self):
        l = 0
        for e in self.embeds:
            l += len(e)
        return l

    async def send_all(self, channel):
        for e in self.embeds:
            await channel.send(embed=e)

    def title(self, title):
        self.title = title

    def url(self, url):
        self.url = url

    def embed(self):
        return self.embeds

    def set_author(self, name, url, icon_url):
        self.name = name
        self.icon_url = icon_url

    def set_thumbnail(self, tn):
        """

        :param tn:
        :return:
        """
        self.thumbnail = tn

    def add_field(self, name: str, value: str, inline: bool=False):
        if self.current_length + len(value)+len(name) >= 5000:
            self.embeds.append(discord.Embed(color=self.color))
            self.embeds[-1].add_field(name=name, value=value, inline=inline)
            self.current_length = (len(value)+len(name))
        else:
            if len(self.embeds) == 0:
                self.embeds.append(discord.Embed(color=self.color))
                self.embeds[-1].url = self.url
                self.embeds[-1].title = self.title
                self.embeds[-1].set_author(name=self.name, icon_url=self.icon_url, url=self.url)
                self.embeds[-1].set_thumbnail(url=self.thumbnail)
                self.embeds[-1].add_field(name=name, value=value, inline=inline)
                self.current_length += (len(value)+len(name))
            else:
                self.embeds[-1].add_field(name=name, value=value, inline=inline)
                self.current_length += (len(value)+len(name))

    def add_category(self, l, title):
        if len(l) > 1000:
            chunks = list()
            lines = l.split("\n")
            length = 0
            chunks.append("")
            for line in lines:
                if length+len(line) > 1000:
                    chunks.append("")
                    chunks[-1] = f"{chunks[-1]}\n{line}"
                    length = len(chunks[-1])
                else:
                    chunks[-1] = f"{chunks[-1]}\n{line}"
                    length = len(chunks[-1])
            first = True
            for chunk in chunks:
                if first:
                    self.add_field(name=title, value=chunk, inline=False)
                    first = False
                else:
                    self.add_field(name="\u200b", value=chunk, inline=False)
        else:
            self.add_field(name=title, value=l)

class Transaction:
    def __init__(self, maker: sessionmaker):
        self.sessionmaker = maker

    def __enter__(self):
        self.session = self.sessionmaker()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.session.rollback()
            self.session.close()
            return True
        else:
            self.session.commit()
            self.session.close()


def get_emojis(bot, chapter):
    em = bot.em
    s = ""
    if chapter.link_tl in (None, ""):
        tl = em.get("tlw")
    else:
        tl = em.get("tl")
    if chapter.link_rd in (None, ""):
        rd = em.get("rdw")
    else:
        rd = em.get("rd")
    if chapter.link_ts in (None, ""):
        ts = em.get("tsw")
    else:
        ts = em.get("ts")
    if chapter.link_pr in (None, ""):
        pr = em.get("prw")
    else:
        pr = em.get("pr")
    if chapter.link_rl in (None, ""):
        qcts = em.get("qctsw")
    else:
        qcts = em.get("qcts")

    return f"<:{tl}> - <:{rd}> - <:{ts}> - <:{pr}> - <:{qcts}>"



def completed_embed(chapter, author: discord.Member, mem: discord.Member, step: str, next_step: str, bot) -> discord.Embed:
    project = chapter.project.title
    notes = chapter.notes
    number = chapter.number
    links = {}
    emojis = get_emojis(bot, chapter)
    if next_step == "TS":
        links["Redraws"] = chapter.link_rd
        links["Translation"] = chapter.link_ts
    elif next_step == "RD":
        links["Raws"] = chapter.link_raw
        links["Translation"] = chapter.link_tl
    elif next_step == "PR":
        links["Typeset"] = chapter.link_ts
        links["Translation"] = chapter.link_tl
    elif next_step == "QCTS":
        links["Proofread"] = chapter.link_pr
        links["Typeset"] = chapter.link_ts
    elif next_step == "RL":
        links["QCTS"] = chapter.link_rl
    e = discord.Embed(color=discord.Colour.green())
    e.set_author(name=f"Next up: {mem.display_name} | {next_step}", icon_url=mem.avatar_url)
    e.description=f"{author.mention} finished `{project}` Ch. `{formatNumber(number)}` | {step}\n"
    links = '\n'.join(['[%s](%s)' % (key, value) for (key, value) in links.items()])
    e.description=f"{e.description}\n{links}\n\n`Notes:`\n```{notes}```"
    e.description=f"{e.description}\n{get_emojis(bot, chapter)}"
    e.set_footer(text=f"Step finished by {author.display_name}", icon_url=author.avatar_url)
    return e

class _MissingSentinel:
    # stolen from https://github.com/Rapptz/discord.py/blob/master/discord/utils.py
    def __eq__(self, other):
        return False

    def __bool__(self):
        return False

    def __repr__(self):
        return '...'

MISSING: Any = _MissingSentinel()