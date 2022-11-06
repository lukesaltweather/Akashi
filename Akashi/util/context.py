import logging
from typing import Optional

import discord
from discord.ext import commands
from prettytable import PrettyTable
from sqlalchemy import inspect
from sqlalchemy.orm.collections import InstrumentedList

from Akashi.model.chapter import Chapter
from Akashi.model.project import Project
from Akashi.model.staff import Staff
from Akashi.util.misc import drawimage


class ConfirmationView(discord.ui.View):
    def __init__(
        self,
        *,
        timeout: float,
        author_id: int,
        reacquire: bool,
        ctx: "CstmContext",
        delete_after: bool,
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


class CstmContext(commands.Context):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        logging.getLogger("akashi.db").debug(f"Starting SQLAlchemy Session.")
        self._session = self.bot.Session(autoflush=False, autocommit=False)

    @property
    def session(self):
        return self._session

    async def notify(self, entity: Chapter | Project | list):
        if isinstance(entity, Chapter):
            to_notify = [*entity.to_notify, *entity.project.to_notify]
        elif isinstance(entity, Project):
            to_notify = entity.to_notify
        else:
            to_notify = [item.to_notify for item in entity]
            entity = entity[0]
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
                user = self.bot.get_user(request.staff.discord_id)
                # differentiate between chapter and project here
                if isinstance(entity, Chapter):
                    await user.send(
                        embed=discord.Embed(
                            title=f"{self.author.display_name} added changes to {entity.project.title} {entity.number}.",
                            color=discord.Color.blurple(),
                        ).set_image(url="attachment://image.png"),
                        file=await drawimage(table.get_string()),
                    )
                elif isinstance(entity, Project):
                    await user.send(
                        embed=discord.Embed(
                            title=f"{self.author.display_name} added changes to {entity.title}.",
                            color=discord.Color.blurple(),
                        ).set_image(url="attachment://image.png"),
                        file=await drawimage(table.get_string()),
                    )

    async def prompt_and_commit(
        self,
        color=discord.Color.blurple(),
        *,
        embed=None,
        file=None,
        text="Do you want to confirm?",
    ):
        if not embed:
            embed = discord.Embed(color=color, title=text)
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
            await self.session.commit()
            await self.reply("Commited changes.", mention_author=False)
            await self.success()
            return True
        else:
            await self.session.rollback()
            await self.reply("Discarded changes.", mention_author=False)
            return False

    async def monitor_changes(
        self,
        entity,
        color=discord.Color.blue(),
        *,
        embed=None,
        file=None,
        text="Do you want to confirm?",
    ):
        if not embed:
            embed = discord.Embed(color=color, title=text)
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
            if isinstance(entity, (InstrumentedList, list)):
                for e in entity:
                    await self.notify(e)
            else:
                await self.notify(entity)
            await self.session.commit()
            await self.success()
        else:
            await self.session.rollback()
            await self.reply("Discarded changes.", mention_author=False)

    async def prompt(
        self,
        *,
        color=discord.Color.blue(),
        embed=None,
        file=None,
        text="Do you want to confirm?",
    ):
        if not embed:
            embed = discord.Embed(color=color, title=text)
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
            await self.success()
        return view.value

    async def success(self):
        await self.message.add_reaction("👍")

    async def failure(self):
        await self.message.add_reaction("👎")
