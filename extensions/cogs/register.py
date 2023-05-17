from extensions.command_utils import sleep, YesNoButton
from common.globals import DEBUG, BASKENTMAIL, TEXT, GUILD_ID, GUILD_INVITE_CHANNEL_ID, GATEWAY_GUILD_ID, GATEWAY_INVITE_CHANNEL_ID
from common.utils import bold
from CDB import CDB, UserNotFoundError, GuildLectureNotFoundError
from CLogger import CLogger
from CMail import CMail
import discord
from discord.ext import tasks, commands
from random import randint
import datetime

TRYTIMEOUT_BASE = 30 # minute
TRYTIMEOUT = TRYTIMEOUT_BASE
TICKET_DELETE_TIME = 60 # minute
INVITE_LINK_EXPIRE = 600 # second 

DISCORD_NICK_LENGTH_LIMIT = 32

LOGGER = CLogger(name="COG.REGISTER")
MAIL = CMail()
DB = CDB()

class Ticket():
    tryTimeoutRange = datetime.timedelta(minutes=TRYTIMEOUT)
    TYPE_STUDENT = DB.STUDENT
    TYPE_ACADEMIC = DB.ACADEMIC
    TYPE_RESEARCHER = DB.RESEARCHER
    def __init__(self, member : discord.Member) -> None:
        
        self.member = member
        self.created_at = discord.utils.utcnow()
        
        self._id : str = None
        self._type : int = None
        self._title : str = None
        self._name : str = None
        self._surname : str = None
        self._fullname : str = None
        self._nick : str = None
        self._mailAdd : str = None
        self._verCode : int = None
        
        self._verCodeaAttempt = 3
        self._mailAttempt = 3
        self._emailTimeout = None
        self._complate = False
    
    def set_type(self, type : int):
        if type == Ticket.TYPE_STUDENT:
            self._type = type
        elif type == DB.ACADEMIC:
            if DB.is_academic_researcher(self._id):
                self._type = Ticket.TYPE_RESEARCHER
            else:
                self._type = type
    def set_id(self, id : str):
        if not DB.is_user_exist(userID=id):
            raise UserNotFoundError(f'User ({id}) not Found')
        if DB.is_user_banned(userID=id):
            raise UserBannedError
        if DB.is_user_registered(userID=id):
            raise UserRegisteredError
        
        self._id = id
    def set_name_surname_title(self):
        if self._type == Ticket.TYPE_ACADEMIC:
            self._name, self._surname, self._title = DB.select_user(userID=self._id, type=self._type, required='name, surname, title')
        else:
            self._name, self._surname = DB.select_user(userID=self._id, type=self._type, required='name, surname')
    def set_nick(self, nick : str):
        if len(nick) <= 32:
            self._nick = nick
        else:
            raise NicknameLong
    def set_verCode(self) -> int:
        self._verCodeaAttempt = 3
        self._verCode = randint(100000,999999)
        return self._verCode
    def get_fullname(self) -> str:
        if self._fullname is None:
            if self._type == Ticket.TYPE_ACADEMIC:
                if self._name != None or self._surname != None or self._title != None:
                    self._fullname = self._title + ' ' + self._name + ' ' + self._surname
                else:
                    raise Exception("Name, surname or title not setten")
            else:
                if self._name != None or self._surname != None:
                    self._fullname = self._name + ' ' + self._surname
                else:
                    raise Exception("Name or surname not setten")
        return self._fullname
    def get_mailAdd(self) -> str:
        if self._mailAdd is None:
            self._mailAdd = MAIL.address if DEBUG else self._id + BASKENTMAIL
        return self._mailAdd
    def set_complate(self):
        if isinstance(self._id, str) and isinstance(self._type, int) and self._emailTimeout is None and isinstance(self._nick, str):
            LOGGER.info(f"{self.member} 's ticket complated. id: {self._id}, type: {self._type}")
            self._complate = True
        else:
            LOGGER.error(f"{self.member} 's ticket NOT complated. id: {self._id}, type: {self._type}, timeout: {self._emailTimeout}")
    def get_complate(self) -> bool:
        return self._complate
    def get_credential(self) -> tuple[str, int, str, discord.Member]:
        return (self._id, self._type, self._nick, self.member)
    
    def is_verCode_valid(self, verCode) -> bool:
        self._verCodeaAttempt -= 1
        if self._verCodeaAttempt >= 0:
            try:
                return int(verCode) == self._verCode
            except ValueError:
                return False
        else:
            raise ManyVerCodeAttempt("VerCode attempt passed.") 
    def send_verCode_mail(self):
        self._mailAttempt -= 1
        if self._mailAttempt >= 0:
            MAIL.sendVerCode(emailTo=self.get_mailAdd(), name=self.get_fullname(), verCode=self.set_verCode())
        else:
            self._emailTimeout = discord.utils.utcnow()
            raise ManyEmailAttempt(f"Mail attempt passed.")
    def is_timeout(self):
        if self._emailTimeout is not None:
            if (discord.utils.utcnow() - self._emailTimeout) > self.tryTimeoutRange:
                return True
            else:
                self._emailTimeout = None
        return False
    
    async def start(self):

        if self.is_timeout():
            await self.member.send(TEXT['MANYEMAIL'])
            return TEXT['MANYEMAIL']
        
        view = ChooseButtons(ticket=self, timeout = 600.0)
        await self.member.send(TEXT['STARTMSG'], view=view)
        await view.wait()

        if view.status == ChooseButtons.STATUS_NOT_COMPLATE:
            return await self.time_out()
        elif view.status == ChooseButtons.STATUS_BANNED:
            return "Banned"
        #TODO: elif status == STATUS_GUEST
        elif view.status == ChooseButtons.STATUS_COMPLATE:
            view = EMailButton(ticket=self, timeout=1000.0)
            await self.member.send(
                content=f"{bold(self.get_mailAdd())} adresine bir doğrulama kodu gönderdim. Kodu girmek için butona tıkla.",
                view=view
            )        
            await view.wait()

            if view.status == EMailButton.STATUS_NOT_COMPLATE:
                return await self.time_out()
            elif view.status == EMailButton.STATUS_BANNED:
                return TEXT['MANYEMAIL']
            elif view.status == EMailButton.STATUS_VERIFIED:
                nicks = self.create_nicks()
                
                if len(nicks) > 1:
                    msg = nicks.copy()
                    for i in range(len(msg)):
                        msg[i] = str(i + 1) + ')' + msg[i]
                    
                    msg = '\n'.join(msg)
                    print(msg)
                    view = NameChooseButtons(nicks, timeout=120.0)
                    await self.member.send(content=TEXT['NAMECHOOSE'] + '\n' + msg, view=view)
                    await view.wait()
                    self.set_nick(nicks[view.choosen])
                else:
                    self.set_nick(nicks[0])

                self.set_complate()
                return 'Kayıt tamamlandı'

        return "Unknown Error"             

    async def time_out(self):
        await self.member.send(f"{TEXT['TIMEOUTFORANSWER']}\n")
        return TEXT['REASON']['TIMEOUTFORANSWER']

    def create_nicks(self) -> list[str]:
        nick = self.get_fullname()
        if self._type == Ticket.TYPE_STUDENT: nick = nick + ' |' + self._id

        if len(nick) > DISCORD_NICK_LENGTH_LIMIT:
            names = list()
            
            if self._type == Ticket.TYPE_STUDENT:
                constLen = len(self._surname) + 11 # <name><space(1)><surname><space(1)><pipe(1)><id(8)>
            elif self._type == Ticket.TYPE_RESEARCHER:
                constLen = len(self._surname) + 1 #<name><space(1)><surname>
            elif self._type == Ticket.TYPE_ACADEMIC:
                constLen = len(self._title) + len(self._surname) + 2 #<title><space(1)><name><space(1)><surname>
            
            nameList = self._name.split(' ')
            for i in range(len(nameList)):
                tempList = nameList.copy()
                for j in range(len(nameList) - i):
                    tempList[j+i] = tempList[j+i][0] + '.'
                    temp = ' '.join(tempList)
                    if len(temp) + constLen <= DISCORD_NICK_LENGTH_LIMIT: names.append(temp)

            if self._type == Ticket.TYPE_STUDENT:
                nicks = [f"{name} {self._surname} |{self._id}"for name in names]
            elif self._type == Ticket.TYPE_RESEARCHER:
                nicks = [f"{name} {self._surname}" for name in names]
            elif self._type == Ticket.TYPE_ACADEMIC:
                nicks = [f"{self._title} {name} {self._surname}" for name in names]
            
            return nicks
        else:
            return [nick]



#VIEWS

class ChooseButtons(discord.ui.View):
    STUDENT_BUTTON_TYPE = Ticket.TYPE_STUDENT
    ACADEMIC_BUTTON_TYPE = Ticket.TYPE_ACADEMIC
    STATUS_BANNED = -1
    STATUS_NOT_COMPLATE = 0
    STATUS_COMPLATE = 1
    def __init__(self, ticket : Ticket,  *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ticket : Ticket = ticket 
        self.status = ChooseButtons.STATUS_NOT_COMPLATE

        self.student_button = discord.ui.Button(label= "Öğrenci",style=discord.ButtonStyle.gray)
        self.student_button.callback = self.student_button_callback
        
        self.academic_button = discord.ui.Button(label= "Görevli",style=discord.ButtonStyle.gray)
        self.academic_button.callback = self.academic_button_callback
        
        self.retry_button = discord.ui.Button(label= "Yeniden Dene",style=discord.ButtonStyle.green)
        self.retry_button.callback = self.retry_button_callback

        self.init_choose_buttons()


    def init_retry_button(self):
        self.clear_items()
        self.add_item(self.retry_button)

    def init_choose_buttons(self):
        self.clear_items()

        self.add_item(self.student_button)
        self.add_item(self.academic_button)
    
    async def retry_button_callback(self, interaction : discord.Interaction):
        self.init_choose_buttons()
        await interaction.response.edit_message(content="Kimliğini belirt. (butona tıkla)", view=self)

    async def student_button_callback(self, interaction : discord.Interaction):
        askIDModal = AskID(parent=self, button_type = ChooseButtons.STUDENT_BUTTON_TYPE, timeout=self.timeout)
        await interaction.response.send_modal(askIDModal)
        
        await askIDModal.wait()
        if askIDModal.status == ChooseButtons.STATUS_COMPLATE:
            self.status = ChooseButtons.STATUS_COMPLATE
            self.stop()
        
    
    async def academic_button_callback(self, interaction : discord.Interaction):
        askIDModal = AskID(parent=self, button_type = ChooseButtons.ACADEMIC_BUTTON_TYPE, timeout=self.timeout)
        await interaction.response.send_modal(askIDModal)
        
        await askIDModal.wait()
        if askIDModal.status:
            self.status = askIDModal.status
            self.stop()

class EMailButton(discord.ui.View):
    STATUS_BANNED = -1
    STATUS_NOT_COMPLATE = 0
    STATUS_VERIFIED = 1
    STATUS_NOT_VERIFIED = 2
    def __init__(self, ticket : Ticket, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ticket = ticket
        self.ticket.send_verCode_mail()
        
        self.email_button = discord.ui.Button(label= TEXT['SENDAGAIN'],style=discord.ButtonStyle.grey)
        self.verCode_button = discord.ui.Button(label= "Kodu Gir",style=discord.ButtonStyle.green)
        

        self.verCode_button.callback = self.verCode_button_callback
        self.email_button.callback = self.email_button_callback
        
        self.add_item(self.verCode_button)
        self.add_item(self.email_button)
        
        self.status = EMailButton.STATUS_NOT_COMPLATE
        

    

    async def email_button_callback(self, interaction : discord.Interaction):
        self.verCode_button.disabled = False
        try:
            self.ticket.send_verCode_mail()
            await interaction.response.edit_message(content=f"Yeni doğrulama kodu {self.ticket.get_mailAdd()} adresine gönderildi. Kodu girmek için kodu gir butonuna tıkla.",view=self)
        except ManyEmailAttempt:
            self.status = EMailButton.STATUS_BANNED
            self.clear_items()
            await interaction.response.edit_message(content=TEXT['MANYEMAIL'], view=self)
            self.stop()

    async def verCode_button_callback(self, interaction : discord.Interaction):
        askVercodeModal = AskVercode(parent=self , timeout=self.timeout)
        await interaction.response.send_modal(askVercodeModal)
        await askVercodeModal.wait()
        if askVercodeModal.verified:
            self.status = EMailButton.STATUS_VERIFIED
            self.stop()
        else:
            self.status = EMailButton.STATUS_NOT_VERIFIED


class AskID(discord.ui.Modal, title = TEXT['ASKID_TITTLE']):
    
    def __init__(self, parent : ChooseButtons, button_type : int, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.parent = parent
        self.type = button_type
        self.status = self.parent.STATUS_NOT_COMPLATE
        
        if self.type == ChooseButtons.STUDENT_BUTTON_TYPE:
            self.LABEL = 'Öğrenci Numarası:'
            self.PLACEHOLDER = 'Öğrenci Numarası... (örn: 21996842)'
        elif self.type == ChooseButtons.ACADEMIC_BUTTON_TYPE:
            self.LABEL = 'Başkent Üniversitesi Kullanıcı Adı:'
            self.PLACEHOLDER = 'Kullanıcı Adı... (örn: ayilmaz)'

        self._text_input = discord.ui.TextInput(
            label=self.LABEL,
            placeholder=self.PLACEHOLDER,
            style=discord.TextStyle.short,
            required=True,
            min_length= 8 if self.type == ChooseButtons.STUDENT_BUTTON_TYPE else 3,
            max_length= 8 if self.type == ChooseButtons.STUDENT_BUTTON_TYPE else 15)
    
        self.add_item(self._text_input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            self.parent.ticket.set_id(self._text_input.value)
        except UserNotFoundError:
            self.parent.init_retry_button()
            if self.type == ChooseButtons.STUDENT_BUTTON_TYPE:
                await interaction.response.edit_message(content=bold(self._text_input.value) + "kayıtlı öğrenciler arasında bulunamadı!", view=self.parent)
            elif self.type == ChooseButtons.ACADEMIC_BUTTON_TYPE:
                await interaction.response.edit_message(content=bold("User not found"), view=self.parent)

        except UserRegisteredError:
            self.parent.init_retry_button()
            await interaction.response.edit_message(content=bold("User already registered"), view=self.parent)
        except UserBannedError:
            self.status = self.parent.STATUS_BANNED
            self.parent.clear_items()
            await interaction.response.edit_message(content=f"{TEXT['SORRY']} {bold(self._text_input.value)} {TEXT['BANNED']}", view=self.parent)
        else:
            self.status = self.parent.STATUS_COMPLATE
            self.parent.ticket.set_type(self.type)
            self.parent.ticket.set_name_surname_title()
            self.parent.clear_items()
            await interaction.response.edit_message(content=f"Hoşgeldin, {self.parent.ticket.get_fullname()}!", view=self.parent)

class AskVercode(discord.ui.Modal, title = 'Doğrulama'):
    def __init__(self, parent : EMailButton, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.verified = None
        self.parent = parent
        
        self.text_input = discord.ui.TextInput(
            label="Doğrulama Kodu",
            placeholder="123456",
            style=discord.TextStyle.short,
            required=True,
            min_length=6
        )
        self.add_item(self.text_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            if self.parent.ticket.is_verCode_valid(self.text_input.value):
                self.verified = True
                self.parent.clear_items()
                await interaction.response.edit_message(content='Doğrulandı!', view=self.parent)
            else:
                self.verified = False
                await interaction.response.edit_message(content= bold(TEXT['WRONGVERCODEMSG']))
        except ManyVerCodeAttempt:
            self.parent.verCode_button.disabled = True
            await interaction.response.edit_message(content=bold(TEXT["MANYTRYMSG"]), view=self.parent)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        LOGGER.error(error)
        await interaction.response.send_message('--root message--')

class NameChooseButtons(discord.ui.View):
    def __init__(self, names : list, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.names = names
        self.choosen = 1
        self.init_buttons()
    
    def init_buttons(self):
        for i in range(1,len(self.names) + 1):
            number_button = discord.ui.Button(label=str(i), style=discord.ButtonStyle.gray)
            async def number_button_callback(interaction : discord.Interaction, iter=i):
                self.choosen = iter - 1
                self.clear_items()
                await interaction.response.edit_message(content=self.names[self.choosen] + TEXT['SELECTED'], view=self)
                self.stop()
            number_button.callback = number_button_callback
            self.add_item(number_button)


#EXCEPTIONS

class UserBannedError(ValueError):
    pass
class UserRegisteredError(ValueError):
    pass
class ManyEmailAttempt(ValueError):
    pass
class ManyVerCodeAttempt(ValueError):
    pass
class NicknameLong(ValueError):
    pass

class Register(commands.Cog):
    SUB_LIMIT = 0
    QUOTA_LIMIT = 10

    def __init__(self, client : commands.Bot) -> None:
        super().__init__()
        self.CBOT = client
        self.TICKETS : dict[int, Ticket] = dict()
        self.GUILD_INVITE_CHANNEL : discord.TextChannel = None
        self.GATEWAY_INVITE_CHANNEL : discord.TextChannel = None
        
        #background tasks
        self.ticketControlTask.start()
        self.assign_new_TRYTIMEOUT.start()
        #TODO: research assistant check
    def cog_unload(self):
        self.ticketControlTask.cancel()
        self.assign_new_TRYTIMEOUT.cancel()

    @commands.Cog.listener()
    async def on_member_join(self, member : discord.Member):
        if member.bot: return
        
        if member.guild.id == GATEWAY_GUILD_ID:

            reason = 'Origin'
            
            try:
                if member.id in self.TICKETS:
                    ticket = self.TICKETS[member.id]
                    if self.is_complate(member=member):
                        view = YesNoButton(timeout = 30.0)
                        await member.send(f"Kayıt işlemini {ticket.get_fullname()} olarak tamamladınız. Yeniden Kayıt yapmak ister misiniz?", view=view)
                        await view.wait()

                        if view.status == YesNoButton.STATUS_YES:
                            del self.TICKETS[member.id]
                            await member.send(await self.get_gateway_invite_url())
                            reason="New register requested."                            
                        else:
                            await member.send("Sunucuya katılmak için gönderilen davet bağlantısını kullanın.")
                            reason = "New register NOT requested."
                                                    
                    elif ticket.is_timeout():
                        await member.send(TEXT['MANYEMAIL'])
                        reason = TEXT['MANYEMAIL']
                    else:
                        reason = await ticket.start()
                else:
                    if DB.is_member_exist(member):
                        await member.send(TEXT['ALREADY_REGISTERED'])
                        reason=TEXT['REASON']['ALREADY_REGISTERED']
                    else:
                        await member.send(TEXT['WELCOMEMSG'])
                        self.TICKETS[member.id] = Ticket(member=member)
                        reason = await self.TICKETS[member.id].start()
                        if self.is_complate(member=member):
                            await member.send(await self.get_guild_invite_url(reason=f'For {member}'))
            finally:
                await self.GATEWAY.kick(member, reason=reason)

        elif member.guild.id == GUILD_ID:
            if self.is_complate(member=member):
                try:
                    await self.init_member(ticket=self.TICKETS[member.id])
                finally:
                    del self.TICKETS[member.id]
            else:
                try:
                    await member.send(f"{TEXT['NOTICKET']}\n{await self.get_gateway_invite_url()}")
                finally:
                    await self.GUILD.kick(member, reason='NO TICKET')

    @commands.Cog.listener()
    async def on_member_remove(self, member : discord.Member):
        if member.bot: return
        
        if member.guild.id == GUILD_ID:
            DB.delete_member(member=member)
        
    
    @commands.Cog.listener()
    async def on_member_ban(self, guild : discord.Guild, member : discord.Member):
        if member.bot: return

        if guild.id == GUILD_ID:
            DB.insert_banned(member=member)
    
    @commands.Cog.listener()
    async def on_member_unban(self, guild : discord.Guild, member : discord.Member):
        if member.bot: return
        
        if guild.id == GUILD_ID:
           DB.delete_banned(member=member)
    
    @commands.Cog.listener()
    async def on_ready(self):
        self.GUILD : discord.Guild = self.CBOT.get_guild(GUILD_ID)
        self.GATEWAY : discord.Guild = self.CBOT.get_guild(GATEWAY_GUILD_ID)
    
    def is_complate(self, member : discord.Member) -> bool:
        if member.id in self.TICKETS:
            return self.TICKETS[member.id].get_complate()
        return False
    
    async def get_guild_invite_url(self, reason=' '):
        if self.GUILD_INVITE_CHANNEL is None:
            self.GUILD_INVITE_CHANNEL : discord.TextChannel = discord.utils.get(self.GUILD.channels, id=GUILD_INVITE_CHANNEL_ID)
        invite = await self.GUILD_INVITE_CHANNEL.create_invite(max_age=INVITE_LINK_EXPIRE, max_uses=1, unique=True, reason=reason)

        return invite.url
    async def get_gateway_invite_url(self):
        if self.GATEWAY_INVITE_CHANNEL is None:
            self.GATEWAY_INVITE_CHANNEL : discord.TextChannel = discord.utils.get(self.GATEWAY.channels, id=GATEWAY_INVITE_CHANNEL_ID)
        invite = await self.GATEWAY_INVITE_CHANNEL.create_invite(max_age=0, max_uses=0, unique=False)

        return invite.url

    async def init_member(self, ticket : Ticket):
        
        _id , _type, _nick, _member = ticket.get_credential()
        memberRoles = []

        #BASE ROLE
        if _type == Ticket.TYPE_ACADEMIC or _type == Ticket.TYPE_RESEARCHER:
            memberRoles.append(discord.utils.get(self.GUILD.roles, name=DB.ACADEMIC_NAME))
        elif _type == Ticket.TYPE_STUDENT:
            memberRoles.append(discord.utils.get(self.GUILD.roles, name=DB.STUDENT_NAME))
        #BASE ROLE

        #DEPARTMENT ROLE
        departmentID = DB.select_user(type=_type, userID=_id, required='department')
        departmentName = DB.select_department(departmentID=departmentID, required='name')[0]
        departmentRole : discord.Role = discord.utils.get(self.GUILD.roles, name=departmentName)
        if departmentRole is not None: memberRoles.append(departmentRole)
        #DEPARTMENT ROLE

        
        #LECTURE ROLES     
        lectures = DB.select_user_lectures(userID=_id, type=_type)
        
        for code, branch in lectures:
            DB.update_lecture_sub(code=code)
            name, quota, subs, dep = DB.select_lecture(code=code, branch= branch, 
                                                       required='name, quota, subscriber, department')
            try:
                memberRoles.append(
                    discord.utils.get(
                        self.GUILD.roles,
                        id=DB.select_guild_lecture(code=code,
                                                    required='roleID')[0]
                    )
                )
            except GuildLectureNotFoundError:
                if quota < self.QUOTA_LIMIT:
                    continue
                elif subs < self.SUB_LIMIT:
                    DB.make_sub(code=code, member=_member)
                else:
                    newLectureRole = await self.create_guild_lecture(code=code, name=name, departmentID=dep)
                    self.CBOT.loop.create_task(self.sublist_control_task(lectureCode=code, lectureRole=newLectureRole))
                    memberRoles.append(newLectureRole)
        
        if _type == DB.RESEARCHER:
            departmentCategory : discord.CategoryChannel = discord.utils.get(self.GUILD.categories,name=departmentName)
            for channel in departmentCategory.text_channels:
                  memberRoles.append(discord.utils.get(channel.changed_roles, name=channel.name))
        
        #LECTURE ROLES
        
        await _member.edit(nick=_nick, roles=memberRoles)
        DB.insert_member(member=_member, userID=_id, type=_type)
    
    async def create_guild_lecture(self, code : str, name : str, departmentID : str) -> discord.Role:
        role = await self.GUILD.create_role(
            name=code,
            permissions=discord.Permissions(0),
            mentionable=True)
        category : discord.CategoryChannel = discord.utils.get(self.GUILD.categories, name=DB.select_department(departmentID=departmentID))
        channel = await self.GUILD.create_text_channel(
            name=code,
            topic=name,
            category=category,
            default_auto_archive_duration=10080,
            overwrites={
                role : discord.PermissionOverwrite.from_pair(
                    discord.Permissions(448825510976), discord.Permissions(86704795665)
                ),
                self.GUILD.default_role : discord.PermissionOverwrite.from_pair(
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
            if ticket.get_complate(): continue
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
            member : discord.Member = discord.utils.get(self.GUILD.members, id=memberID)
            if member is not None:
                await member.add_roles(lectureRole, reason=TEXT['REASON']['SUBLIST_ACHIEVED'])
        DB.remove_sublist(lectureCode=lectureCode)
    def __del__(self):
        self.cog_unload()



#Cogs setup req.
async def setup(client : commands.Bot):
    await client.add_cog(Register(client))