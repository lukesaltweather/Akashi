import discord
from discord.ext import commands

from sqlalchemy import func

from src.util.misc import MISSING

from src.util.checks import is_admin, is_pu

from src.util.context import CstmContext

from src.util.flags.editflags import (
    EditStaffFlags,
    EditChapterFlags,
    EditProjectFlags,
    ReleaseFlags,
)


class Edit(commands.Cog):
    """
    Test description
    """

    def __init__(self, client):
        self.bot = client

    @commands.command(
        aliases=["editch", "editc", "ec"],
    )
    @commands.max_concurrency(1, per=discord.ext.commands.BucketType.default, wait=True)  # type: ignore
    async def editchapter(self, ctx: CstmContext, *, flags: EditChapterFlags):
        """
        Description
        ==============
        Edit a chapters attributes.

        Required Role
        =====================
        Role `Neko Workers`.

        Arguments
        ===========

        Required
        ---------
        :chapter:
            | The chapter to edit, in format: projectName chapterNbr [:doc:`/Types/chapter`]

        Optional
        ------------
        :title:
            | Title of the chapter. [:doc:`/Types/text`]
        :tl, rd, ts, pr:
            | Staff for the chapter. [:doc:`/Types/staff`]
        :link_tl, link_rd, link_ts, link_pr, link_qcts, link_raw:
            | Links to specific steps of chapter on Box. [:doc:`/Types/text`]
        :to_project:
            | Change the project the chapter belongs to. [:doc:`/Types/project`]
        :to_chapter:
            | Change the chapter number. [:doc:`/Types/number`]
        """
        session = ctx.session
        record = flags.chapter
        if flags.title is not MISSING:
            record.title = flags.title
        if flags.tl is not MISSING:
            tl = flags.tl
            record.translator = tl
        if flags.rd is not MISSING:
            rd = flags.rd
            record.redrawer = rd
        if flags.ts is not MISSING:
            ts = flags.ts
            record.typesetter = ts
        if flags.pr is not MISSING:
            pr = flags.pr
            record.proofreader = pr
        if flags.link_ts is not MISSING:
            record.link_ts = flags.link_ts
        if flags.link_tl is not MISSING:
            record.link_tl = flags.link_tl
        if flags.link_rd is not MISSING:
            record.link_rd = flags.link_rd
        if flags.link_pr is not MISSING:
            record.link_pr = flags.link_pr
        if flags.link_qcts is not MISSING:
            record.link_rl = flags.link_qcts
        if flags.link_raw is not MISSING:
            record.link_raw = flags.link_raw
        if flags.to_project:
            proj = flags.to_project
            record.project = proj
        if flags.to_chapter:
            record.number = flags.to_chapter
        image = await record.get_report(str(record))
        embed1 = discord.Embed(
            color=discord.Colour.dark_blue(),
            title="Do you want to commit these changes to this chapter?",
        )
        embed1.set_image(url="attachment://image.png")
        await ctx.monitor_changes(record, embed=embed1, file=image)

    @commands.command(
        aliases=["editproj", "editp", "ep"],
    )
    @is_pu()
    async def editproject(self, ctx: CstmContext, *, flags: EditProjectFlags):
        """
        Description
        ==============
        Edit a project's attributes.

        Required Role
        =====================
        Role `Akashi's Minions`.

        Arguments
        ===========

        Required
        ---------
        :project:
            | The project to edit. [:doc:`/Types/project`]

        Optional
        ------------
        :title:
            | The title of the project. [:doc:`/Types/text`]
        :link:
            | Link to the project on box. [:doc:`/Types/text`]
        :thumbnail:
            | Large picture for the entry in the status board. [:doc:`/Types/text`]
        :icon:
            | Small Image for the status board in the upper left corner. [:doc:`/Types/text`]
        :ts, rd, pr, tl:
            | Default staff for the project. Enter "none" to set the staff to none at all. [:doc:`/Types/staff`]
        :status:
            | Current status of the project, defaults to "active". [:doc:`/Types/literals`]
        :altnames:
            | Aliases for the project, divided by comma. [:doc:`/Types/text`]
        :color:
            | The color the project's embed has in the info board. Can be a hex or one of these colors: [:doc:`/Types/color`]
        :position:
            | Where the embed of the project appears in the info board. [:doc:`/Types/number`]
        """
        record = flags.project
        if flags.title:
            record.title = flags.title
        if flags.status:
            record.status = flags.status
        if flags.color is not MISSING:
            record.color = str(flags.color)[1:]  # type: ignore
        if flags.position is not MISSING:
            record.position = flags.position
        if flags.tl is not MISSING:
            tl = flags.tl
            record.translator = tl
        if flags.rd is not MISSING:
            rd = flags.rd
            record.redrawer = rd
        if flags.ts is not MISSING:
            ts = flags.ts
            record.typesetter = ts
        if flags.pr is not MISSING:
            pr = flags.pr
            record.proofreader = pr
        if flags.altnames is not MISSING:
            record.altNames = flags.altnames
        if flags.thumbnail:
            record.thumbnail = flags.thumbnail  # type: ignore
        if flags.icon is not MISSING:
            record.icon = flags.icon
        if flags.link:
            record.link = flags.link
        image = await record.get_report(f"{record.title}")

        await ctx.monitor_changes(
            text="Do you want to commit these changes to this project?",
            file=image,
            entity=record,
        )

    @commands.command()
    @is_admin()
    @commands.max_concurrency(1, per=discord.ext.commands.BucketType.default, wait=True)  # type: ignore
    async def editstaff(self, ctx: CstmContext, *, flags: EditStaffFlags):
        """
        Description
        ==============
        Edit a staffmembers attributes.

        Required Role
        =====================
        Role `Neko Herders`.

        Arguments
        ===========

        Required
        ---------
        :member:
            | Staffmember to edit. [:doc:`/Types/staff`]

        Optional
        ------------
        :id:
            | The staff's discord id. [:doc:`/Types/number`]
        :name:
            | The staff's username. [:doc:`/Types/text`]
        :status:
            | Can be "active" or "inactive". [:doc:`/Types/literals`]
        """
        member = flags.member
        if flags.id:
            member.discord_id = flags.id
        if flags.name:
            member.name = flags.name
        if flags.status:
            member.status = flags.status  # type: ignore
        image = await member.get_report(f"{member.name}")

        await ctx.prompt_and_commit(
            text="Do you want to commit these changes to this staffmember?", file=image
        )

    @commands.command()
    async def release(self, ctx: CstmContext, *, flags: ReleaseFlags):
        """
        Description
        ==============
        Mark a chapter as released.

        Required Role
        =====================
        Role `Neko Workers`.

        Arguments
        ===========
        Required
        ---------
        :chapter:
            | The chapter to set as released, in format: projectName chapterNbr [:doc:`/Types/chapter`]

        Optional
        ------------
        :date: The date on which it was finished, defaults to current date and time.
            | [:doc:`/Types/datetime`]
        """
        record = flags.chapter
        if flags.date:
            record.date_release = flags.date  # type: ignore
        else:
            record.date_release = func.now()
        image = await record.get_report(record)
        await ctx.monitor_changes(
            text="Do you want to set this chapter as released?",
            file=image,
            entity=record,
        )


async def setup(Bot):
    await Bot.add_cog(Edit(Bot))
