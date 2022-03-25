import discord
import discord.ext
from discord.ext.commands import CommandError
from sqlalchemy.sql.expression import select, or_

import src.model.project as project
import src.model.staff as staff
from src.util import misc
from src.util.db import get_first, get_one, get_all


async def discordstaff(sti: str, ctx):
    try:
        conv = discord.ext.commands.MemberConverter()
        user = await conv.convert(ctx=ctx, argument=sti)
        if user is not None:
            return user
    except:
        pass
    return None


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
    stmt = select(project.Project).filter(
        or_(
            project.Project.title.ilike("%" + sti + "%"),
            project.Project.altNames.ilike("%" + sti + ",%"),
        )
    )
    proj = await get_first(session, stmt)
    if proj:
        return proj
    raise CommandError("This project doesn't exist.")


async def searchprojects(sti, session):
    stmt = select(project.Project).filter(
        or_(
            project.Project.title.ilike("%" + sti + "%"),
            project.Project.altNames.ilike("%" + sti + ",%"),
        )
    )
    return await get_all(session, stmt)
