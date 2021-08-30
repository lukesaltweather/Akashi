import json

import discord
import discord.ext
from sqlalchemy.orm.exc import MultipleResultsFound

import src.model.staff as staff
import src.model.project as project
from src.util import exceptions, misc
from src.util.exceptions import StaffNotFoundError, NoResultFound

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
    st = session2.query(staff.Staff).filter(staff.Staff.discord_id == passid).first()
    if st is not None:
        return st
    else:
        raise StaffNotFoundError


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
            raise StaffNotFoundError
    return await dbstaff(dst.id, sessions)


async def searchstaffpayload(passstr, sessions):
    if passstr in ("None", "none"):
        return None
    return await dbstaff(passstr, sessions)

def searchproject(sti, session):
    if sti.isdigit():
        return session.query(project.Project).filter(int(sti) == project.Project.id).one()
    for i in range(1, 3):
        try:
            if i == 1:
                return session.query(project.Project).filter(project.Project.title.ilike("%" + sti + "%")).one()
            if i == 2:
                return session.query(project.Project).filter(project.Project.altNames.ilike("%"+sti+",%")).one()
        except:
            pass
    raise NoResultFound(message="Couldn't find a project like this.")
