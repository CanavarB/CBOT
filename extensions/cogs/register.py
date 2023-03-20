from extensions.command_utils import *
from random import randint
from time import time

TRYTIMEOUT = 45 # minute

class Register(commands.Cog):
    SUB_LIMIT = 3
    QUOTA_LIMIT = 10
    def __init__(self, client : cb) -> None:
        super().__init__()
        self.CBOT = client
        self.TICKETS : dict[int, Ticket] = dict()
     
    @commands.Cog.listener()
    async def on_member_join(self, member : discord.Member):
        if member.bot: return
        
        if member.guild.id == GATEWAY_GUILD_ID:

            reason = 'Origin'
            try:
                if DB.is_member_exist(member):
                    await member.send(TEXT['ALREADY_REGISTERED'])
                    reason=TEXT['REASON']['ALREADY_REGISTERED']
                else:
                    await member.send(TEXT['WELCOMEMSG'])
                    self.TICKETS[member.id] = Ticket(client=self.CBOT, member=member)
                    reason = await self.TICKETS[member.id].start()
            finally:
                await self.CBOT.GATEWAY.kick(member, reason=reason)

        elif member.guild.id == GUILD_ID:
            if self.is_complate(member=member):
                await self.init_member(member=member)
                del self.TICKETS[member.id]
            else:
                try:
                    await member.send(f"{TEXT['NOTICKET']}\n{GATEWAY_INVITE_LINK}")
                finally:
                    await self.CBOT.GUILD.kick(member, reason='NO TICKET')

    def is_complate(self, member : discord.Member) -> bool:
        if member.id in self.TICKETS:
            return self.TICKETS[member.id].complate
        return False

    async def init_member(self, member: discord.Member):
        ticket = self.TICKETS[member.id]
        memberRoles = []
        
        departmentName = DB.select_department(DB.select_user(ticket.UserID,
                                            'department',
                                            ticket.type)[0],
                        'name')
        departmentRole = utils.get(self.CBOT.GUILD.roles, name=departmentName)
        if departmentRole is not None: memberRoles.append(departmentRole)


        if ticket.type == DB.ACADEMIC or ticket.type == DB.RESEARCHER:
            memberRoles.append(utils.get(self.CBOT.GUILD.roles, name='Görevli'))
        elif ticket.type == DB.STUDENT:
            memberRoles.append(utils.get(self.CBOT.GUILD.roles, name='Öğrenci'))
        

        lectures = ()
        if ticket.type == DB.RESEARCHER:
            departmentCategory : discord.CategoryChannel = utils.get(
                self.CBOT.GUILD.categories,
                name=departmentName)
            for channel in departmentCategory.text_channels:
                  memberRoles.append(utils.get(channel.changed_roles, name=channel.name))
        
        else:
            lectures = DB.select_user_lectures(userID=ticket.UserID, type=ticket.type)
        
        for code, branch in lectures:
            DB.update_lecture_sub(code=code)
            name, quota, subs, dep = DB.select_lecture(code=code, branch= branch, 
                                                       required='name, quota, subscriber, department')
            try:
                memberRoles.append(
                    utils.get(
                        self.CBOT.GUILD.roles,
                        id=DB.select_guild_lecture(code=code,
                                                    required='roleID')[0]
                    )
                )
            except GuildLectureNotFoundError:
                if quota >= self.QUOTA_LIMIT and subs >= self.SUB_LIMIT:
                    memberRoles.append(await self.create_guild_lecture(
                        code=code, name=name, departmentID=dep
                        )
                    )

        
        await member.edit(nick=ticket.name, roles=memberRoles)

        DB.insert_member(member=member, userID=ticket.UserID, type=ticket.type)
    
    async def create_guild_lecture(self, code : str, name : str, departmentID : str) -> discord.Role:
        role = await self.CBOT.GUILD.create_role(
            name=code,
            permissions=discord.Permissions(0),
            mentionable=True)
        category : discord.CategoryChannel = utils.get(self.CBOT.GUILD.categories, name=DB.select_department(departmentID=departmentID))
        channel = await self.CBOT.GUILD.create_text_channel(
            name=code,
            topic=name,
            category=category,
            default_auto_archive_duration=10080,
            overwrites={
                role : discord.PermissionOverwrite.from_pair(
                    discord.Permissions(448825510976), discord.Permissions(86704795665)
                ),
                self.CBOT.GUILD.default_role : discord.PermissionOverwrite.from_pair(
                    discord.Permissions.none(), discord.Permissions.all()
                )
            })
        DB.insert_guild_lecture(role=role, channel=channel)

        return role



class Ticket():
    tryTimeoutRange = TRYTIMEOUT * 60 # minute * 60 (second)
    def __init__(self, client: cb, member : discord.Member) -> None:
        self.CBOT = client
        self.member = member
        self.created_at = time() #TODO: background task delete ticket
        self.tryTimeout = None
        self.complate = False
        self.name = None
    
    async def start(self):

        if self.tryTimeout is not None:
            if (time() - self.tryTimeout) < self.tryTimeoutRange:
                await self.member.send(TEXT['MANYEMAIL'])
                return TEXT['MANYEMAIL']
            else:
                self.tryTimeout = None

        view = ChooseButtons(timeout = 5000)
        await self.member.send(TEXT['STARTMSG'], view=view)
        
        await view.wait()
        view_UserID = view.UserID
        view_UserType = view.UserType
        del view

        if view_UserID is None:
            return await self.time_out()
            
        elif view_UserType == DB.STUDENT:
            if (len(view_UserID) != 8 or not view_UserID.isnumeric()):
                return await self.send_retry_message(message=TEXT['WRONGNUMMSG'])
        elif view_UserType == DB.ACADEMIC:
            pass #TODO: LOG
        
        
        #CHECKS
        try:
            user = DB.select_user(userID=view_UserID, type=view_UserType, required='id, name')
        except UserNotFoundError:
            return await self.send_retry_message(
                message = f"{TEXT['SORRY']} {utils.bold(view_UserID)} {TEXT['NOTFOUNDSTUMSG'] if view_UserType == DB.STUDENT else TEXT['NOTFOUNDPERMSG']}"
                )
            #TODO: hard coded plain text
        if DB.is_user_banned(userID=user[0]):
            await self.member.send(f"{TEXT['SORRY']} {utils.bold(user[1])} {TEXT['BANNED']}")
            return f'Banned {user[0]}'
        
        if DB.is_user_registered(userID=user[0]):
            return await self.send_retry_message(
                message = f"{TEXT['SORRY']} {utils.bold(user[1])} {TEXT['FOUNDMSG']}"
                )
            #TODO: hard coded plain text
        #CHECKS

        if view_UserType == DB.ACADEMIC and DB.is_academic_researcher(view_UserID):
            self.type = DB.RESEARCHER
        else:
            self.type = view_UserType
        self.UserID = user[0]

        userMail = self.UserID + BASKENTMAIL
        view = EMailButton(mail_add=userMail,name=user[1])
        

        for _ in range(3):
            await self.member.send(content=
                f"{TEXT['WELCOME']} {utils.bold(user[1])}!\n\
                {TEXT['SENDVERMSG']} butonuna tıkladığında {utils.bold(userMail)} {TEXT['EMAILMSG']}",
                view=view)
            view.wait()

            if not view.is_finished():
                return await self.time_out()
                
            
            if not view.verified:
                await self.member.send(TEXT['WRONGVERCODEMSG']) #TODO: yeniden denemek ister misin view button
            else:
                del view
                self.complate = True
                return 'Kayıt tamamlandı'

        del view
        self.tryTimeout = time()

        await self.member.send(TEXT['MANYEMAIL'])

        return 'Fazla deneme'







    async def time_out(self):
        await self.member.send(f"{TEXT['TIMEOUTFORANSWER']}\n")
        return TEXT['REASON']['TIMEOUTFORANSWER']
    
    async def send_retry_message(self, message : str = None):
        if message is None: message = 'Lütfen yeniden deneyin..'
        view = ReTryButton()
        await self.member.send(content=message, view=view)
        await view.wait()
        view_isClicked = view.isClicked
        del view
        if view_isClicked:
            return await self.start()
        else:
            return await self.time_out()
        


class ChooseButtons(discord.ui.View):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        student_button = discord.ui.Button(label= "Öğrenci",style=discord.ButtonStyle.gray)
        academic_button = discord.ui.Button(label= "Görevli",style=discord.ButtonStyle.gray)

        self.UserType = None
        self.UserID = None

        student_button.callback = self.student_button_callback
        academic_button.callback = self.academic_button_callback

        self.add_item(student_button)
        self.add_item(academic_button)

    async def student_button_callback(self, interaction : discord.Interaction):
        self.UserType = DB.STUDENT

        askIDModal = AskIDStudent(timeout=self.timeout)
        await interaction.response.send_modal(askIDModal)

        await askIDModal.wait()
        self.UserID = askIDModal.text_input.value
        del askIDModal
        self.stop()
    
    async def academic_button_callback(self, interaction : discord.Interaction):
        self.UserType = DB.ACADEMIC

        askIDModal = AskIDAcademic(timeout=self.timeout)
        await interaction.response.send_modal(askIDModal)
        
        await askIDModal.wait()
        self.UserID = askIDModal.text_input.value
        del askIDModal
        self.stop()


class EMailButton(discord.ui.View):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        email_button = discord.ui.Button(label= TEXT['SENDVERMSG'],style=discord.ButtonStyle.green)
        
        self.mailAdd = kwargs['mail_add']
        self.name = kwargs['name']
        self.verCode = randint(1000000,9999999)
        self.verified = False


        email_button.callback = self.email_button_callback

        self.add_item(email_button)

    async def email_button_callback(self, interaction : discord.Interaction):
        
        MAIL.sendVerCode(emailTo=self.mailAdd, name=self.name, verCode=self.verCode)

        verCodeModal = AskVercode()
        await interaction.response.send_modal(verCodeModal)

        await verCodeModal.wait()
        modal_response = verCodeModal.text_input.value
        del verCodeModal

        if int(modal_response) == self.verCode: self.verified = True

        self.stop()

class ReTryButton(discord.ui.View):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        retry_button = discord.ui.Button(label= "Yeniden Dene",style=discord.ButtonStyle.green)
        
        self.isClicked = False

        retry_button.callback = self.retry_button_callback

        self.add_item(retry_button)

    async def retry_button_callback(self, interaction : discord.Interaction):
        await interaction.response.edit_message(content='Yeniden Deneniyor...')
        self.isClicked = True
        self.stop()

class AskID(discord.ui.Modal, title = TEXT['ASKID_TITTLE']):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.text_input = discord.ui.TextInput(
            label=kwargs['label'],
            style=discord.TextStyle.short,
            placeholder=kwargs['placeholder'],
            required=True
        )

        self.add_item(self.text_input)
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(f'{self.text_input.value}!')

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.response.send_message('--root message--')

class AskIDStudent(AskID):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs,
            label='Öğrenci Numarası:',
            placeholder='Öğrenci Numarası... (örn: 21996842)')
class AskIDAcademic(AskID):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs,
            label='Başkent Üniversitesi Kullanıcı Adı:',
            placeholder='Kullanıcı Adı... (örn: ayilmaz)')
class AskVercode(AskID):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs,
            label='Doğrulama Kodu',
            placeholder='123456')



#Cogs setup req.
async def setup(client : cb):
    await client.add_cog(Register(client))