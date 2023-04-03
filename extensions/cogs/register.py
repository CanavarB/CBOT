from extensions.command_utils import *
from random import randint
import datetime

TRYTIMEOUT_BASE = 30 # minute
TRYTIMEOUT = TRYTIMEOUT_BASE
TICKET_DELETE_TIME = 60 # minute
INVITE_LINK_EXPIRE = 600 # second 

class Register(commands.Cog):
    SUB_LIMIT = 0
    QUOTA_LIMIT = 10
    def __init__(self, client : cb) -> None:
        super().__init__()
        self.CBOT = client
        self.TICKETS : dict[int, Ticket] = dict()
        self.GUILD_INVITE_CHANNEL : discord.TextChannel = None

        #background tasks
        self.ticketControlTask.start()
        self.assign_new_TRYTIMEOUT.start()
    def cog_unload(self):
        self.ticketControlTask.cancel()
        self.assign_new_TRYTIMEOUT.cancel()
    
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
                    self.TICKETS[member.id] = Ticket(member=member)
                    reason = await self.TICKETS[member.id].start()
            finally:
                if self.is_complate(member=member):
                    await member.send(await self.get_invite_url(reason=f'For {member}'))
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
    
    async def get_invite_url(self, reason=' '):
        if self.GUILD_INVITE_CHANNEL is None:
            self.GUILD_INVITE_CHANNEL : discord.TextChannel = discord.utils.get(self.CBOT.GUILD.channels, id=GUILD_INVITE_CHANNEL_ID)
        invite = await self.GUILD_INVITE_CHANNEL.create_invite(max_age=INVITE_LINK_EXPIRE, max_uses=1, unique=True, reason=reason)

        return invite.url
  
    async def init_member(self, member: discord.Member):
        ticket = self.TICKETS[member.id]
        
        memberRoles = []

        #BASE ROLE
        if ticket.type == DB.ACADEMIC or ticket.type == DB.RESEARCHER:
            memberRoles.append(utils.get(self.CBOT.GUILD.roles, name=DB.ACADEMIC_NAME))
        elif ticket.type == DB.STUDENT:
            memberRoles.append(utils.get(self.CBOT.GUILD.roles, name=DB.STUDENT_NAME))
        #BASE ROLE

        #DEPARTMENT ROLE
        departmentID = DB.select_user(type=ticket.type, userID=ticket.UserID,required='department')
        departmentName = DB.select_department(departmentID=departmentID, required='name')[0]
        departmentRole : discord.Role = utils.get(self.CBOT.GUILD.roles, name=departmentName)
        if departmentRole is not None: memberRoles.append(departmentRole)
        #DEPARTMENT ROLE

        
        #LECTURE ROLES     
        lectures = DB.select_user_lectures(userID=ticket.UserID, type=ticket.type)
        
        for code, branch in lectures:
            DB.make_sub(code=code, member=member)
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
                    newLectureRole = await self.create_guild_lecture(code=code, name=name, departmentID=dep)
                    self.CBOT.loop.create_task(self.sublist_control_task(lectureCode=code, lectureRole=newLectureRole))
                    memberRoles.append(newLectureRole)
        
        if ticket.type == DB.RESEARCHER:
            departmentCategory : discord.CategoryChannel = utils.get(self.CBOT.GUILD.categories,name=departmentName)
            for channel in departmentCategory.text_channels:
                  memberRoles.append(utils.get(channel.changed_roles, name=channel.name))
        
        #LECTURE ROLES
        
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

    @tasks.loop(minutes=5)
    async def assign_new_TRYTIMEOUT(self):
        '''
        Assing timeout value respect to ticket number. (Server load)
        Each active ticket increases the timeout value by half a minute.
        '''

        TRYTIMEOUT = TRYTIMEOUT_BASE + int(len(self.TICKETS) * 0.5)
        LOGGER.info(f"New timeout asinged: {TRYTIMEOUT}")
    @tasks.loop(minutes=TICKET_DELETE_TIME)
    async def ticketControlTask(self):
        LOGGER.info(f"Ticket Control Task started.")
        current = discord.utils.utcnow()
        for memberID, ticket in self.TICKETS.items():
            diff = current - ticket.created_at
            if diff > datetime.timedelta(minutes=TICKET_DELETE_TIME):
                LOGGER.info(f"Ticket deleted {memberID},  current time : {current}, ticket created at : {ticket.created_at}, time diff.: {diff}")
                del self.TICKETS[memberID]
        LOGGER.info("Ticket Control Task ended.")
    @ticketControlTask.before_loop
    async def beforeTicketControlTask(self):
        await self.CBOT.wait_until_ready()
        await discord.utils.sleep_until(discord.utils.utcnow() + datetime.timedelta(minutes=5))
    async def sublist_control_task(self, lectureCode : str, lectureRole : discord.Role):
        LOGGER.info("Sublist control tast requested.")
        await sleep(300)
        for memberID in DB.select_sublist(lectureCode=lectureCode):
            member : discord.Member = utils.get(self.CBOT.GUILD.members, id=memberID)
            if member is not None:
                member.add_roles(lectureRole, reason=TEXT['REASON']['SUBLIST_ACHIEVED'])

class Ticket():
    tryTimeoutRange = datetime.timedelta(minutes=TRYTIMEOUT)
    def __init__(self, member : discord.Member) -> None:
        
        self.member = member
        self.name = None
        self.created_at = discord.utils.utcnow()
        self.tryTimeout = None
        self.complate = False
    
    async def start(self):

        if self.tryTimeout is not None:
            if (discord.utils.utcnow() - self.tryTimeout) > self.tryTimeoutRange:
                await self.member.send(TEXT['MANYEMAIL'])
                return TEXT['MANYEMAIL']
            else:
                self.tryTimeout = None
        
        view = ChooseButtons(timeout = 5000)
        await self.member.send(TEXT['STARTMSG'], view=view)
        await view.wait()

        if not view.complete: return await self.time_out()        
        
        
        #CHECKS
        if view.UserType == DB.STUDENT and (len(view.UserID) != 8 or not view.UserID.isnumeric()):
            return await self.send_retry_message(message=TEXT['WRONGNUMMSG'])
        try:
            user = DB.select_user(userID=view.UserID, type=view.UserType, required='id, name, surname')
        except UserNotFoundError:
            return await self.send_retry_message(message = f"{TEXT['SORRY']} {utils.bold(view.UserID)} {TEXT['NOTFOUNDSTUMSG'] if view.UserType == DB.STUDENT else TEXT['NOTFOUNDPERMSG']}")
        if DB.is_user_banned(userID=user[0]):
            await self.member.send(f"{TEXT['SORRY']} {utils.bold(user[0])} {TEXT['BANNED']}")
            return f'Banned {user[0]}'
        if DB.is_user_registered(userID=user[0]):
            return await self.send_retry_message(message = f"{TEXT['SORRY']} {utils.bold(user[0])} {TEXT['FOUNDMSG']}")
        #CHECKS

        
        self.type = DB.RESEARCHER if view.UserType == DB.ACADEMIC and DB.is_academic_researcher(view.UserID) else view.UserType
        self.UserID = user[0]
        #self.userMail = self.UserID + BASKENTMAIL
        self.userMail = 'cbot.baskent@gmail.com'
        self.name = user[1] + ' ' + user[2]

        verCode = randint(1000000,9999999)
        MAIL.sendVerCode(emailTo=self.userMail, name=self.name, verCode=verCode)
        view = EMailButton(mail_add=self.userMail, name=self.name, verCode=verCode, timeout=1000.0)
        await self.member.send(
            content=f"Hoşgeldin, {self.name}!\n{utils.bold(self.userMail)} adresine bir doğrulama kodu gönderdim. Kodu girmek için butona tıkla.",
            view=view
        )        
        await view.wait()

        if not view.is_finished:
            return await self.time_out()
        elif view.emailTimeout:
            self.tryTimeout = discord.utils.utcnow()
            return 'Fazla deneme'
        elif view.verified:
            
            self.complate = True
            return 'Kayıt tamamlandı'

        return "Unknown Error"             

    async def time_out(self):
        await self.member.send(f"{TEXT['TIMEOUTFORANSWER']}\n")
        return TEXT['REASON']['TIMEOUTFORANSWER']
    
    async def send_retry_message(self, message : str = None):
        if message is None: message = 'Lütfen yeniden deneyin..'
        view = ReTryButton(timeout=120.0)
        await self.member.send(content=message, view=view)
        await view.wait()

        if view.isClicked:
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
        self.complete = False

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
        self.complete = True
        self.stop()
    
    async def academic_button_callback(self, interaction : discord.Interaction):
        self.UserType = DB.ACADEMIC

        askIDModal = AskIDAcademic(timeout=self.timeout)
        await interaction.response.send_modal(askIDModal)
        
        await askIDModal.wait()
        self.UserID = askIDModal.text_input.value
        self.complete = True
        self.stop()

class EMailButton(discord.ui.View):
    def __init__(self, mail_add, name, verCode, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.email_button = discord.ui.Button(label= TEXT['SENDAGAIN'],style=discord.ButtonStyle.grey)
        self.verCode_button = discord.ui.Button(label= "Kodu Gir",style=discord.ButtonStyle.green)

        self.mailAdd = mail_add
        self.name = name
        self.verCode = verCode
        self.verified = False
        self.email_tries = 1
        self.emailTimeout = False
        self.verCode_tries = 0

        self.verCode_button.callback = self.verCode_button_callback
        self.email_button.callback = self.email_button_callback
        self.add_item(self.verCode_button)
        self.add_item(self.email_button)

    async def email_button_callback(self, interaction : discord.Interaction):
        self.email_tries += 1
        if self.email_tries <= 3 and self.emailTimeout == False:
            self.verCode_tries = 0
            self.verCode_button.disabled = False
            self.verCode = randint(1000000,9999999)
            MAIL.sendVerCode(emailTo=self.mailAdd, name=self.name, verCode=self.verCode)
            await interaction.response.edit_message(content=f"Yeni doğrulama kodu {self.mailAdd} adresine gönderildi. Kodu girmek için kodu gir butonuna tıkla.",view=self)
        else:
            await interaction.response.send_message(TEXT['MANYEMAIL'])
            self.emailTimeout = True
            self.stop()
    async def verCode_button_callback(self, interaction : discord.Interaction):
        self.verCode_tries += 1
        if self.verCode_tries <= 3:
            askVercodeModal = AskVercode(parrent=self, verCode=self.verCode)
            await interaction.response.send_modal(askVercodeModal)
            await askVercodeModal.wait()
            
            if askVercodeModal.verified:
                self.verified = True
                self.stop()
            else:
                self.verified = False
        else:
            self.verCode_button.disabled = True
            await interaction.response.send_message(TEXT["MANYTRYMSG"], view=self)

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
    def __init__(self, label, placeholder, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.text_input = discord.ui.TextInput(
            label=label,
            style=discord.TextStyle.short,
            placeholder=placeholder,
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
class AskVercode(discord.ui.Modal, title = 'Doğrulama'):
    def __init__(self, parrent, verCode, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.verCode = verCode
        self.verified = None
        self.parrent = parrent
        self.text_input = discord.ui.TextInput(
            label="Doğrulama Kodu",
            style=discord.TextStyle.short,
            placeholder="12345",
            required=True
        )
        self.add_item(self.text_input)
    async def on_submit(self, interaction: discord.Interaction):
        try:
            if int(self.text_input.value) == self.verCode:
                self.verified = True
                await interaction.response.send_message('Doğrulandı!')
            else:
                self.verified = False
                await interaction.response.send_message(TEXT['WRONGVERCODEMSG'],view=self.parrent)
        except ValueError:
            self.verified = False
            await interaction.response.send_message(TEXT['WRONGVERCODEMSG'],view=self.parrent)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        LOGGER.error(error)
        await interaction.response.send_message('--root message--')

class NameChooseButtons(discord.ui.View):
    def __init__(self, names : list, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.choosen = 1
        self.buttons = [discord.ui.Button(label=str(names.index(name) + 1), style=discord.ButtonStyle.gray) for name in names]
    
    async def on_interaction(self, interaction : discord.Interaction, /):
        self.choosen = self.buttons.index(interaction.component)







#Cogs setup req.
async def setup(client : cb):
    await client.add_cog(Register(client))