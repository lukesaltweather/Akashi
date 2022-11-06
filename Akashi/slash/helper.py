import typing
from Akashi.model.chapter import Chapter
from Akashi.model.project import Project
from Akashi.model.staff import Staff

from Akashi.util.context import ConfirmationView
from Akashi.util.misc import drawimage

import discord
from prettytable import PrettyTable
from sqlalchemy import inspect


class ConfirmationView(discord.ui.View):
    def __init__(
        self,
        *,
        timeout: float,
        author_id: int,
        reacquire: bool,
        delete_after: bool,
    ) -> None:
        super().__init__(timeout=timeout)
        self.value: typing.Optional[bool] = None
        self.delete_after: bool = delete_after
        self.author_id: int = author_id
        self.reacquire: bool = reacquire
        self.message: typing.Optional[discord.Message] = None

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
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        self.value = True
        await interaction.response.defer()
        if self.delete_after:
            await interaction.delete_original_message()
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        await interaction.response.defer()
        if self.delete_after:
            await interaction.delete_original_message()
        self.stop()


async def monitor_changes(
    entity,
    color=discord.Color.blue(),
    *,
    embed=None,
    file=None,
    text="Do you want to confirm?",
    inter: discord.Interaction,
    session,
    bot,
):
    if not embed:
        embed = discord.Embed(color=color, title=text)
    if file:
        embed.set_image(url="attachment://image.png")
    view = ConfirmationView(
        delete_after=False,
        author_id=inter.user.id,
        reacquire=True,
        timeout=30,
    )
    await inter.followup.send(embed=embed, file=file, view=view, ephemeral=True)
    await view.wait()
    if view.value:
        await inter.followup.send("Commited changes.")
        if entity is list:
            for e in entity:
                await notify(e, bot, inter)
        else:
            await notify(entity, bot, inter)
        await session.commit()
    else:
        await session.rollback()
        await inter.followup.send("Discarded changes.")


async def notify(entity, bot, inter):
    to_notify = (
        entity.to_notify
        if isinstance(entity, Project)
        else [*entity.to_notify, *entity.project.to_notify]
    )
    if to_notify:
        table = PrettyTable()
        table.add_column("", ["ORIGINAL", "EDIT"])
        state = inspect(entity)
        changes = 0
        for attr in state.attrs:
            hist = attr.history
            if not hist.has_changes():
                continue
            old_value = hist.deleted[0] if hist.deleted else None
            if isinstance(old_value, Staff):
                old_value = old_value.name
            new_value = hist.added[0] if hist.added else None
            if isinstance(new_value, Staff):
                new_value = new_value.name
            table.add_column(attr.key.capitalize(), [old_value, new_value])
            changes += 1
        if changes == 0:
            return
        for request in to_notify:
            user = bot.get_user(request.staff.discord_id)
            # differentiate between chapter and project here
            if isinstance(entity, Chapter):
                await user.send(
                    embed=discord.Embed(
                        title=f"{inter.user.display_name} added changes to {entity.project.title} {entity.number}.",
                        color=discord.Color.blurple(),
                    ).set_image(url="attachment://image.png"),
                    file=await drawimage(table.get_string()),
                )
            elif isinstance(entity, Project):
                await user.send(
                    embed=discord.Embed(
                        title=f"{inter.user.display_name} added changes to {entity.title}.",
                        color=discord.Color.blurple(),
                    ).set_image(url="attachment://image.png"),
                    file=await drawimage(table.get_string()),
                )
