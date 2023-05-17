from common.globals import TEXT, FORUM_CHANNEL_ID
from common.utils import bold, quote
from extensions.command_utils import is_active_member, is_in_DMChannel, sleep
from discord.ext import commands
import discord
from CDB import CDB

DB = CDB()


@commands.command()
@commands.dm_only()
@commands.check(is_active_member)
async def anon(ctx : commands.Context):
    view = AnonAgreementButton(timeout = 5000)
    await ctx.send(TEXT['ANON']['AGREEMENTTEXT'], view=view)
    
    await view.wait()
    view_msg_body = view.msg_body
    view_msg_title = view.msg_title
    view_choose = view.choose
    del view


    if view_choose is None:
        await ctx.send(TEXT['ANON']['TIMEOUTMSG'])
        return
    elif view_msg_body is not None or view_msg_title is not None:
        FORUM_CHANNEL : discord.ForumChannel = ctx.bot.get_channel(FORUM_CHANNEL_ID)
        ANON_TAG : discord.ForumTag = discord.utils.get(FORUM_CHANNEL.available_tags, name='anonim')
        msg_body = f'{bold(DB.get_member_anonName(member=ctx.author))} diyor ki:\n\n {quote(view_msg_body)}'
        await FORUM_CHANNEL.create_thread(name=view_msg_title, content=msg_body, applied_tags=[ANON_TAG])
    


@anon.error
async def anon_error(ctx : commands.Context, error : commands.errors.CheckFailure):
    if not is_in_DMChannel(ctx=ctx):
        await ctx.message.delete()
        await sleep(0.01)
        await ctx.author.send(TEXT['ANON']['DM_USAGE_WARNING'])

class AnonModal(discord.ui.Modal, title = "Anonim Mesaj"):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
    
    
        self.msg_title = discord.ui.TextInput(label='Başlık', placeholder='Anonim Mesaj Başlığı')
        self.msg_body = discord.ui.TextInput(label="Mesaj İçeriği", style=discord.TextStyle.long)
        
        self.add_item(self.msg_title)
        self.add_item(self.msg_body)


    async def on_submit(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(f"Anonim etiketinde paylaşılacak:\n\n{self.msg_title}\n{self.msg_body}")
    
class AnonAgreementButton(discord.ui.View):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        agree_button = discord.ui.Button(label= "✓",style=discord.ButtonStyle.green)
        disagree_button = discord.ui.Button(label= "𐄂",style=discord.ButtonStyle.red)

        self.choose = None
        self.msg_title = None
        self.msg_body = None

        agree_button.callback = self.agree_button_callback
        disagree_button.callback = self.disagree_button_callback

        self.add_item(agree_button)
        self.add_item(disagree_button)

   
    async def agree_button_callback(self, interaction : discord.Interaction):
        self.choose = "✓"
        
        anonModal = AnonModal()
        await interaction.response.send_modal(anonModal)
        await anonModal.wait()
        self.msg_title = anonModal.msg_title.value
        self.msg_body = anonModal.msg_body.value
        
        del anonModal

        self.stop()

    async def disagree_button_callback(self, interaction : discord.Interaction):
        self.choose = "𐄂"
        self.stop()
        await interaction.response.send_message(content="Reddedildi")
    

async def setup(client : commands.Bot):
    client.add_command(anon)