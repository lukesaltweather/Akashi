import discord
import discord.ext
from discord.ext.commands import CommandError
from sqlalchemy.sql.expression import select, or_, func

import Akashi.model.project as project
import Akashi.model.staff as staff
from Akashi.util import misc
from Akashi.util.db import get_first, get_one, get_all


async def discordstaff(sti: str, ctx):
    try:
        conv = discord.ext.commands.MemberConverter()
        user = await conv.convert(ctx=ctx, argument=sti)
        if user is not None:
            return user
    except:
        pass
    return None


async def get_staff_from_discord_id(discord_id, session):
    stmt = select(staff.Staff).where(staff.Staff.discord_id == discord_id)
    return await get_one(session, stmt)


async def dbstaff(passid: int, session2):
    stmt = select(staff.Staff).filter(staff.Staff.discord_id == passid)
    st = await get_first(session2, stmt)
    if st:
        return st
    else:
        raise CommandError("Staff doesn't exist.")


def fakesearch(did, ctx):
    try:
        user = ctx.guild.get_member(int(did))
        if user is not None:
            return user
    except:
        pass
    return misc.FakeUser(did)


async def searchstaff(passstr: str, ctx, sessions):
    if passstr in ("None", "none"):
        return None
    dst = await discordstaff(passstr, ctx)
    if dst is None:
        try:
            staff = await dbstaff(int(passstr), sessions)
            if staff is not None:
                return staff
        except ValueError:
            raise CommandError("Staff doesn't exist.")
    return await dbstaff(dst.id, sessions)


async def searchstaffpayload(passstr, sessions):
    if passstr in ("None", "none"):
        return None
    return await dbstaff(passstr, sessions)


async def searchproject(sti, session):
    sti = sti.lower()
    stmt = select(project.Project).where(
        or_(
            func.word_similarity(sti, project.Project.title) > 0.4,
            func.lower(project.Project.altNames).contains(sti),
        )
    )
    proj = await get_first(session, stmt)
    if proj:
        return proj
    raise CommandError("This project doesn't exist.")


async def searchprojects(sti, session):
    stmt = select(project.Project).where(
        or_(
            func.word_similarity(sti, project.Project.title) > 0.4,
            func.lower(project.Project.altNames).contains(sti),
        )
    )
    return await get_all(session, stmt)
