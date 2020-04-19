import json
from io import BytesIO

import aiohttp
import discord
from discord.ext import commands

from src.util import exceptions
from src.util.checks import is_admin

with open('src/util/help.json', 'r') as f:
    jsonhelp = json.load(f)

class Misc(commands.Cog):
    """
        Miscellaneous Commands
    """
    def __init__(self, client):
        self.bot = client


    async def cog_check(self, ctx):
        return ctx.guild is not None

    @commands.command(description=jsonhelp["debugboard"]["description"],
                      usage=jsonhelp["debugboard"]["usage"], brief=jsonhelp["debugboard"]["brief"], help=jsonhelp["debugboard"]["help"])
    @is_admin()
    async def debugboard(self, ctx, amount: int):
        ch = self.bot.config["board_channel"]
        channel = self.bot.get_channel(ch)
        await channel.purge(limit=amount)
        messages = {}
        with open('src/util/board.json', 'w') as f:
            json.dump(messages, f, indent=4)

    @commands.command(description=jsonhelp["avatar"]["description"],
                      usage=jsonhelp["avatar"]["usage"], brief=jsonhelp["avatar"]["brief"], help=jsonhelp["avatar"]["help"])
    async def avatar(self, ctx, member: discord.Member):
        await ctx.send(member.avatar_url)

    @commands.command(description=jsonhelp["cat"]["description"],
                      usage=jsonhelp["cat"]["usage"], brief=jsonhelp["cat"]["brief"], help=jsonhelp["cat"]["help"])
    async def cat(self, ctx, *, arg):
        try:
            arg = arg[1:]
            d = dict(x.split('=', 1) for x in arg.split(' -'))
            if "breed" in d:
                params = {"q": d["breed"], "limit": 1}
                headers = {"x-api-key": "6290e11c-ffe2-4ba0-8a18-eca68efb4246"}
                url = "https://api.thecatapi.com/v1/breeds/search"
                async with aiohttp.ClientSession() as session:
                    # note that it is often preferable to create a single session to use multiple times later - see below for this.
                    async with session.get(url, params=params, headers=headers) as resp:
                        r = await resp.json()
                        id = r[0]["id"]
                        url = "https://api.thecatapi.com/v1/images/search"
                        if "type" not in d:
                            params = {"breed_ids": id, "limit": 1}
                        else:
                            params = {"breed_ids": id, "mime_types": d["type"], "limit": 1}
                        async with session.get(url, headers=headers, params=params) as resp:
                            r = await resp.json()
                            url = r[0]['url']
                            async with session.get(url) as resp:
                                buffer = BytesIO(await resp.read())
                                file = discord.File(fp=buffer, filename=f"something.{d['type']}")
                                await ctx.send(file=file)
            else:
                headers = {"x-api-key": "6290e11c-ffe2-4ba0-8a18-eca68efb4246"}
                async with aiohttp.ClientSession() as session:
                    # note that it is often preferable to create a single session to use multiple times later - see below for this.
                    url = "https://api.thecatapi.com/v1/images/search"
                    if "type" in d:
                        params = {"mime_types": d["type"], "limit": 1}
                    async with session.get(url, headers=headers, params=params) as resp:
                        r = await resp.json()
                        url = r[0]['url']
                        async with session.get(url) as resp:
                            buffer = BytesIO(await resp.read())
                            file = discord.File(fp=buffer, filename=f"something.{d['type']}")
                            await ctx.send(file=file)
        except IndexError:
            raise exceptions.NoResultFound(message="Could not find an image like this.")

    @commands.command(description=jsonhelp["embed"]["description"],
                      usage=jsonhelp["embed"]["usage"], brief=jsonhelp["embed"]["brief"], help=jsonhelp["embed"]["help"])
    async def embed(self, ctx, color: str):
        color = color.strip("#")
        eger = int(color, 16)
        color = discord.Colour(eger)
        embed = discord.Embed(color=color)
        await ctx.send(embed=embed)