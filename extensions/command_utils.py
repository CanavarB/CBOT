from CBOT import CBOT as cb
from settings import *
from asyncio import sleep

#CONVERTERS
def to_lower(argument : str):
    return argument.lower()
def to_upper(argument : str):
    return utils.upper(argument)
#CONVERTERS

#CHECKS
def is_member(ctx: commands.Context) -> bool:
    return DB.is_member_exist(member=ctx.author)
    
def is_active_member(ctx: commands.Context) -> bool:
    try:
        query = DB.select_member(memberID=ctx.author.id, required='type')
    except MemberNotFoundError:
        return False
    if query[0] == DB.AWAY:
        return False
    return True

def is_in_DMChannel(ctx: commands.Context) -> bool:
    return not bool(ctx.guild)
def is_in_GUILD(ctx: commands.Context) -> bool:
    return bool(ctx.guild and ctx.guild.id == GUILD_ID)
def is_owner(ctx: commands.Context) -> bool:
    try:
        if ctx.guild.owner == ctx.author:
            return True
    except AttributeError:
        if ctx.bot.GUILD.owner == ctx.author:
            return True
    return False
#CHECKS