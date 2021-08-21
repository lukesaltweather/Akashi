import asyncio

from discord.ext import commands
import discord

from src.util.misc import formatNumber


class CstmContext(commands.Context):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.session = self.bot.Session(autoflush=False, autocommit=False)

    async def confirm(self, text = "", color = discord.Color.blue(),*, embed = None, file = None):
        if not embed:
            embed = discord.Embed(description=text, color=color)
        if file:
            embed.set_image(url="attachment://image.png")
        message = await self.send(file=file, embed=embed)
        await message.add_reaction("✅")
        await message.add_reaction("❌")
        await asyncio.sleep(delay=0.5)

        def check(reaction, user):
            return user == self.message.author and (str(reaction.emoji) == '✅' or str(reaction.emoji) == '❌')

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
        except asyncio.TimeoutError:
            return None
        else:
            if str(reaction.emoji) == "✅":
                return True
            else:
                return False