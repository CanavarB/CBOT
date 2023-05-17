from common.globals import GUILD_ID
from common import utils
import discord
from discord.ext import commands
from CDB import CDB, MemberNotFoundError

from asyncio import sleep

DB = CDB()

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

#VIEWS
class YesNoButton(discord.ui.View):
    STATUS_NOT_COMPLATE = -1 
    STATUS_NO = 0
    STATUS_YES = 1
    def __init__(self,  *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.status = YesNoButton.STATUS_NOT_COMPLATE

        yes_button = discord.ui.Button(label= "Evet",style=discord.ButtonStyle.green)
        no_button = discord.ui.Button(label= "Hayır",style=discord.ButtonStyle.red)

        yes_button.callback = self.yes_button_callback
        no_button.callback = self.no_button_callback

        self.add_item(yes_button)
        self.add_item(no_button)

    async def yes_button_callback(self, interaction : discord.Interaction):
        self.clear_items()
        await interaction.response.edit_message(content="Kabul edildi.", view=self)
        self.status = YesNoButton.STATUS_YES
        self.stop()
    async def no_button_callback(self, interaction : discord.Interaction):
        self.clear_items()
        await interaction.response.edit_message(content="Reddedildi.", view=self)
        self.status = YesNoButton.STATUS_NO
        self.stop()