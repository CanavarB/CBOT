from extensions.command_utils import *


class Synchronize(commands.Cog):
    def __init__(self, CBOT : cb) -> None:
        super().__init__()
        self.CBOT = CBOT
        
        self.BASE_TEMPLATE = utils.read_json(BASE_TEMPLATE_PATH)
        self.ROLE_TEMPLATE = utils.read_json(ROLE_TEMPLATE_PATH)

    async def sync(self):
        await self.check_roles(template=self.ROLE_TEMPLATE['admins'])
        await self.sync_roles(template=self.ROLE_TEMPLATE['base'])
        #await self.sync_roles(template=self.ROLE_TEMPLATE['mods']) TODO: 
        
        await self.sync_channels(template=self.BASE_TEMPLATE)

        
    async def sync_channels(self, template : dict):
        if 'Text' in template:
            
            await self.sync_TextChannel(template['Text'])
        await sleep(0.01)
        if 'Voice' in template:
            
            await self.sync_VoiceChannel(template['Voice'])
        await sleep(0.01)
        if 'Forum' in template:
            
            await self.sync_ForumChannel(template['Forum'])
        await sleep(0.01)
        if 'Stage' in template:
            
            await self.sync_StageChannel(template['Stage'])
        await sleep(0.01)
        if 'Category' in template:
            
            await self.sync_CategoryChannel(template['Category'])

    async def sync_roles(self, template : dict):
        for roleName, RoleTemplate in template.items():
            role = discord.utils.get(self.CBOT.GUILD.roles, name=roleName) 
            if role is None: role = self.CBOT.GUILD.create_role(name=roleName)
            color = role.color.value
            hoist = role.hoist
            mentionable = role.mentionable
            permissions = role.permissions.value
            
            if (color != RoleTemplate['color'] or
                hoist != RoleTemplate['hoist'] or
                mentionable != RoleTemplate['mentionable'] or 
                permissions != 0):
                
                await role.edit(color=RoleTemplate['color'],
                                hoist=RoleTemplate['hoist'],
                                mentionable=RoleTemplate['mentionable'],
                                permissions=discord.Permissions(0))

    def check_roles(self, template : dict):
        for roleName, RoleTemplate in template.items():
            role = discord.utils.get(self.CBOT.GUILD.roles, name=roleName)
            if role is None: raise Exception(f'There is no {roleName} role')
            color = role.color.value
            hoist = role.hoist
            mentionable = role.mentionable

            if (color != RoleTemplate['color'] or
                hoist != RoleTemplate['hoist'] or
                mentionable != RoleTemplate['mentionable']):
                
                raise Exception(f'Role ({roleName}) attributes are not matching!')
    
    async def sync_TextChannel(self, template : dict):
        for TextChannelName, TextChannelTemplate in template.items():
            if TextChannelTemplate['category'] is None:
                TextChannel = discord.utils.get(self.CBOT.GUILD.text_channels,
                            name= TextChannelName, category=TextChannelTemplate['category'])
            else:
                TextChannel = discord.utils.get(self.CBOT.GUILD.text_channels,
                            name= TextChannelName, category__name=TextChannelTemplate['category'])
            
            if TextChannel is None:
                category =  discord.utils.get(self.CBOT.GUILD.categories, 
                            name=TextChannelTemplate['category']) \
                            if TextChannelTemplate['category'] is not None\
                            else None
                
                TextChannel = await self.CBOT.GUILD.create_text_channel(
                                name=TextChannelName,
                                category=category)
            
            nsfw = TextChannelTemplate['nsfw']
            default_auto_archive_duration = TextChannelTemplate['default_auto_archive_duration']
            topic = TextChannelTemplate['topic']

            if (TextChannel.default_auto_archive_duration != default_auto_archive_duration or
                TextChannel.nsfw != nsfw or
                TextChannel.topic != topic):
                await TextChannel.edit(default_auto_archive_duration=default_auto_archive_duration,
                                       nsfw=nsfw,
                                       topic=topic)
            
            if TextChannelTemplate['permissions_synced']:
                await TextChannel.edit(sync_permissions=True)
            else:
                await self.sync_PermissionOverwrite(TextChannel, TextChannelTemplate['overwrites'])

    async def sync_VoiceChannel(self, template : dict):
        for VoiceChannelName, VoiceChannelTemplate in template.items():
            if VoiceChannelTemplate['category'] is None:
                VoiceChannel = discord.utils.get(self.CBOT.GUILD.voice_channels,
                            name= VoiceChannelName, category=VoiceChannelTemplate['category'])
            else:
                VoiceChannel = discord.utils.get(self.CBOT.GUILD.voice_channels,
                            name= VoiceChannelName, category__name=VoiceChannelTemplate['category'])
            if VoiceChannel is None:
                category =  discord.utils.get(self.CBOT.GUILD.categories,
                            name=VoiceChannelTemplate['category']) \
                            if VoiceChannelTemplate['category'] is not None \
                            else None
                VoiceChannel = await self.CBOT.GUILD.create_voice_channel(
                                name=VoiceChannelName,
                                category=category)
            
            nsfw = VoiceChannelTemplate['nsfw']
            bitrate = VoiceChannelTemplate['bitrate']
            rtc_region = VoiceChannelTemplate['rtc_region']

            if(VoiceChannel.nsfw != nsfw or
               VoiceChannel.bitrate != bitrate or
               VoiceChannel.rtc_region != rtc_region):
               await VoiceChannel.edit(nsfw=nsfw, bitrate=bitrate, rtc_region=rtc_region)
            
            if VoiceChannelTemplate['permissions_synced']:
                await VoiceChannel.edit(sync_permissions=True)
            else:
                await self.sync_PermissionOverwrite(VoiceChannel, VoiceChannelTemplate['overwrites'])
    
    async def sync_ForumChannel(self, template : dict):
        for ForumChannelName, ForumChannelTemplate in template.items():
            if ForumChannelTemplate['category'] is None:
                ForumChannel = discord.utils.get(self.CBOT.GUILD.forums,
                            name= ForumChannelName, category=ForumChannelTemplate['category'])
            else:
                ForumChannel = discord.utils.get(self.CBOT.GUILD.forums,
                            name= ForumChannelName, category__name=ForumChannelTemplate['category'])
            
            if ForumChannel is None:
                category =  discord.utils.get(self.CBOT.GUILD.categories,
                            name=ForumChannelTemplate['category']) \
                            if ForumChannelTemplate['category'] is not None \
                            else None
                ForumChannel = await self.CBOT.GUILD.create_forum(
                                name=ForumChannelName,
                                category=category)
            
            nsfw = ForumChannelTemplate['nsfw']
            topic = ForumChannelTemplate['topic']
            default_auto_archive_duration = ForumChannelTemplate['default_auto_archive_duration']
            require_tag = ForumChannelTemplate['require_tag']
            slowmode_delay = ForumChannelTemplate['slowmode_delay']
            if(ForumChannel.nsfw != nsfw or
               ForumChannel.topic != topic or
               ForumChannel.flags.require_tag != require_tag or
               ForumChannel.slowmode_delay != slowmode_delay or
               ForumChannel.default_auto_archive_duration != default_auto_archive_duration):
               await ForumChannel.edit(nsfw=nsfw, topic=topic, require_tag=require_tag, slowmode_delay=slowmode_delay,
                default_auto_archive_duration=default_auto_archive_duration)
            
            available_tags : list = ForumChannelTemplate['available_tags']
            available_tag_names = [tag.name for tag in ForumChannel.available_tags]
            
            if sorted(available_tags) != sorted(available_tag_names):
                tags = [discord.ForumTag(name=tagName) for tagName in available_tags]
                await ForumChannel.edit(available_tags=tags)      

            if ForumChannelTemplate['permissions_synced']:
                await ForumChannel.edit(sync_permissions=True)
            else:
                await self.sync_PermissionOverwrite(ForumChannel, ForumChannelTemplate['overwrites'])
 
    async def sync_StageChannel(self, template : dict):
        pass #TODO: stage

    async def sync_CategoryChannel(self, template : dict):
        for CategoryChannelName, CategoryChannelTemplate in template.items():
            CategoryChannel = discord.utils.get(self.CBOT.GUILD.categories,
            name=CategoryChannelName)
            if CategoryChannel is None: Exception(f'There is no {CategoryChannelName} category!')

            nsfw = CategoryChannelTemplate['nsfw']
            if nsfw != CategoryChannel.nsfw:
                CategoryChannel.edit(nsfw=nsfw) 
            
            await self.sync_PermissionOverwrite(CategoryChannel, CategoryChannelTemplate['overwrites'])

            await self.sync_channels(template=utils.read_json(DATA_PATH / (CategoryChannelName + '_category_template.json')))

    async def sync_PermissionOverwrite(self, channel: discord.TextChannel |
    discord.VoiceChannel | discord.ForumChannel | discord.StageChannel | discord.CategoryChannel,
    overwrites: dict[str,int]):
        
        PermissionOverwrite = {}
        PermissionOverwrite[self.CBOT.GUILD.default_role] = discord.PermissionOverwrite.from_pair(
            discord.Permissions.none(), discord.Permissions.all()
        )
        for identifierName, pair in overwrites.items():
            identifier = discord.utils.get(self.CBOT.GUILD.members, name = identifierName[0:]) \
                        if identifierName.startswith('@') \
                        else discord.utils.get(self.CBOT.GUILD.roles, name = identifierName)
            
            
            overwrite = discord.PermissionOverwrite.from_pair(
                discord.Permissions(pair[0]),
                discord.Permissions(pair[1]))
            PermissionOverwrite[identifier] = overwrite
            
            
        if channel.overwrites != PermissionOverwrite:
            await channel.edit(overwrites=PermissionOverwrite)
    
    @commands.command()
    @commands.check(is_owner)
    async def sync(self, ctx, *, arg):
        
        if arg == '-reload' or arg == '-r':
            print(arg)
            self.BASE_TEMPLATE = utils.read_json(BASE_TEMPLATE_PATH)

    @commands.command()
    @commands.check(is_owner)
    async def sc(self, ctx):
        await self.sync_channels(template=self.BASE_TEMPLATE)

#Cogs setup req.
async def setup(client : cb):
    await client.add_cog(Synchronize(client))