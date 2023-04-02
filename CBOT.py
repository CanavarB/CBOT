from sys import exc_info
from settings import *

class CBOT(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=commands.when_mentioned_or(COMMAND_PREFIX),
            intents = discord.Intents.all()
            )
        
    async def setup_hook(self) -> None:
        for cog in COGS:
            await self.load_extension(cog)
        for command in COMMANDS:
            await self.load_extension(command)
    
    async def on_ready(self):
        self.GUILD : discord.Guild = discord.utils.get(self.guilds, id = GUILD_ID)
        LOGGER.info(f"Connected GUILD : {self.GUILD.name}|{self.GUILD.id}")

        self.GATEWAY : discord.Guild = discord.utils.get(self.guilds, id = GATEWAY_GUILD_ID)         
        LOGGER.info(f"Connected GATEWAY : {self.GATEWAY.name}|{self.GATEWAY.id}")      
    
    async def on_member_join(self, member : discord.Member):
        if member.bot: return
        
        if member.guild.id == GUILD_ID or member.guild.id == GATEWAY_GUILD_ID:
            LOGGER.info(f"{member} joined to {member.guild.name}.")
    async def on_member_remove(self, member : discord.Member):
        if member.bot: return
        
        if member.guild.id == GUILD_ID:
            LOGGER.info(f"{member} left {self.GUILD.name}")
            #TODO: delete member in database
        elif member.guild.id == GATEWAY_GUILD_ID:
            LOGGER.info(f"{member} left {self.GATEWAY.name}")
    async def on_member_ban(self, guild : discord.Guild, member : discord.Member):
        if member.bot: return
        
        if guild.id == GUILD_ID:
            LOGGER.info(f"{member} banned from {guild.name}.")
            userID = DB.select_member(memberID=member.id, required='userID')
            #TODO: insert to BANNED table
    async def on_member_unban(self, guild : discord.Guild, member : discord.Member):
        if member.bot: return
        
        if guild.id == GUILD_ID:
            LOGGER.info(f"{member} unbanned from {guild.name}.")
            userID = DB.select_member(memberID=member.id, required='userID')
            #TODO: delete from BANNED table
    
    async def on_message(self, message : discord.Message):
        if message.author.bot or message.is_system(): return #Bot ve sistem mesajları algılanmasın.
        
        if isinstance(message.channel, discord.channel.DMChannel):
            LOGGER.info(f"DM| {message.author} : {message.content}")
        await self.process_commands(message) #Komutların işletilmesi için. Asla kaldırma.
    