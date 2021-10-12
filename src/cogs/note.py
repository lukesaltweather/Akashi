import asyncio
from datetime import datetime
from typing import Optional

import discord
import humanize
from discord import SelectOption
from discord.ext import commands
from discord.ext.commands import CommandError
from discord.ui import Select
from sqlalchemy import select

from src.model.note import Note as _Note
from src.util.checks import is_admin
from src.util.context import CstmContext
from src.util.db import get_all, get_one
from src.util.flags.noteflags import AddNoteFlags, RemoveNoteFlags
from src.util.search import searchstaff


class RemoveView(discord.ui.View):
    def __init__(
            self,
            *,
            timeout: float,
            ctx: "CstmContext",
            delete_after: bool,
    ) -> None:
        super().__init__(timeout=timeout)
        self.value = []
        self.delete_after: bool = delete_after
        self.author_id: int = ctx.author.id
        self.ctx: CstmContext = ctx
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

    @discord.ui.select(max_values=25, row=0)
    async def selected(self, select: discord.ui.Select, interaction: discord.Interaction):
        self.value = select.values

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green, row=1)
    async def confirm(
            self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        print()
        await interaction.response.defer()
        if self.delete_after:
            await interaction.delete_original_message()
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red, row=1)
    async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.value = None
        await interaction.response.defer()
        if self.delete_after:
            await interaction.delete_original_message()
        self.stop()

class Note(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["an", "note", "annotate"])
    async def addnote(self, ctx: CstmContext, *, flags: AddNoteFlags):
        """
        Description
        ==============
        Add a note to the specified chapter.

        Required Role
        =====================
        Role `Neko Workers`.

        Arguments
        ===========

        Required
        ------------
        :chapter:
            | The chapter to add the note to. [:doc:`/Types/chapter`]
        :text:
            | The actual text of the note to add. [:doc:`/Types/text`]
        """
        session = ctx.session
        session.add(_Note(flags.chapter, flags.text, await searchstaff(str(ctx.author.id), ctx, ctx.session)))
        await ctx.message.add_reaction("👍")
        await session.commit()

    @commands.command(aliases=["n", "viewnotes"])
    async def notes(self, ctx, *, flags: RemoveNoteFlags):
        session = ctx.session
        notes = flags.chapter.notes
        embed = discord.Embed(colour=discord.Colour.purple(), title=flags.chapter.__str__())
        embed.description = "\n".join([f"{note.author.name} ({humanize.naturaldate(note.created_on)}):\n```{note.text}```" for note in notes])
        embed.set_image(url=flags.chapter.project.thumbnail)
        await ctx.send(embed=embed)



    @commands.command(aliases=["en", "updatenote", "un"])
    async def editnote(self, ctx, *, flags: RemoveNoteFlags):
        session = ctx.session
        notes = [SelectOption(label=note.text, value=note.id, description=f"{humanize.naturaldelta(note.created_on - datetime.now())} ago") for note in flags.chapter.notes if note.author.discord_id == ctx.author.id]
        if not notes:
            raise CommandError("This chapter has no notes that can be deleted by you.")
        view = RemoveView(timeout=60.0, ctx=ctx, delete_after=False)
        view.children[0].options = notes
        view.children[0].max_values = 1
        view_msg = await ctx.send(content="Which of your notes do you want to edit?", view=view)
        await view.wait()

        stmt = select(_Note).filter(_Note.id == int(view.value[0]))
        note = await get_one(session, stmt)
        msg = await ctx.send(content="The next message you send will be used as the new note text.")

        def check(message):
            return message.author == ctx.message.author
        try:
            message = await self.bot.wait_for(
                "message", timeout=60.0, check=check
            )
        except asyncio.TimeoutError:
            await msg.delete()
            raise CommandError("No response from command author, cancelling.")
        else:
            await msg.delete()
            note.text = message.content
            await session.commit()
            await message.delete()
            await view_msg.edit(view=None, content="Successfully edited note.")


    @commands.command(aliases=["rn"])
    async def removenote(self, ctx: CstmContext, *, flags: RemoveNoteFlags):
        """

        """
        notes = [SelectOption(label=note.text, value=note.id, description=f"{humanize.naturaldelta(note.created_on - datetime.now())} ago") for note in notes if note.author.discord_id == ctx.author.id]
        if not notes:
            raise CommandError("This chapter has no notes that can be deleted by you.")
        view = RemoveView(timeout=60.0, ctx=ctx, delete_after=True)
        view.children[0].options = notes
        view.children[0].max_values = len(notes)
        await ctx.send(content="Which of your notes do you want to delete?", view=view)
        await view.wait()

        stmt = select(_Note).filter(_Note.id.in_([int(value) for value in view.value]))
        notes = await get_all(ctx.session, stmt)
        if notes:
            for note in notes:
                await ctx.session.delete(note)
            await ctx.session.commit()

    @commands.command()
    @is_admin()
    async def purgenotes(self, ctx: CstmContext, *, flags: RemoveNoteFlags):
        notes = flags.chapter.notes
        result = await ctx.prompt(text=f"Do you really want to purge {len(notes)} note(s) from {flags.chapter}?")
        if result:
            for note in notes:
                await ctx.session.delete(note)
            await ctx.session.commit()
        else:
            await ctx.send("Cancelling...", delete_after=10)


def setup(Bot):
    Bot.add_cog(Note(Bot))
