import asyncio
from typing import Optional

from discord.ext import commands
import discord
import sqlalchemy
from sqlalchemy.ext.asyncio import AsyncSession

from src.util.misc import MISSING, format_number


class ConfirmationView(discord.ui.View):
    def __init__(
        self,
        *,
        timeout: float,
        author_id: int,
        reacquire: bool,
        ctx: "CstmContext",
        delete_after: bool
    ) -> None:
        super().__init__(timeout=timeout)
        self.value: Optional[bool] = None
        self.delete_after: bool = delete_after
        self.author_id: int = author_id
        self.ctx: CstmContext = ctx
        self.reacquire: bool = reacquire
        self.message: Optional[discord.Message] = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user and interaction.user.id == self.author_id:
            return True
        else:
            await interaction.response.send_message(
                "This confirmation dialog is not for you.", ephemeral=True
            )
            return False

    async def on_timeout(self) -> None:
        if self.delete_after and self.message:
            await self.message.delete()

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        self.value = True
        await interaction.response.defer()
        if self.delete_after:
            await interaction.delete_original_message()
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.value = False
        await interaction.response.defer()
        if self.delete_after:
            await interaction.delete_original_message()
        self.stop()


class CstmContext(commands.Context):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._session = self.bot.Session(autoflush=False, autocommit=False)

    @property
    def session(self):
        return self._session

    async def prompt_and_commit(
        self, color=discord.Color.blue(), *, embed=None, file=None
    ):
        if not embed:
            embed = discord.Embed(color=color, title="Do you want to confirm?")
        if file:
            embed.set_image(url="attachment://image.png")
        view = ConfirmationView(
            ctx=self,
            delete_after=True,
            author_id=self.author.id,
            reacquire=True,
            timeout=30,
        )
        await self.send(embed=embed, file=file, view=view)
        await view.wait()
        if view.value:
            await self.reply("Commited changes.", mention_author=False)
            await self.session.commit()
        else:
            await self.reply("Discarded changes.", mention_author=False)
            await self.session.rollback()
