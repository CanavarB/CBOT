from . import utils
from pathlib import Path
from dotenv import load_dotenv
from os import getenv
from logging import ERROR, WARNING, DEBUG, INFO

##############################
                            ##
DEBUG = True                ##
                            ##
##############################



COMMON_PATH = Path(__file__).parent
ROOT_PATH = COMMON_PATH.parent.absolute()
DATA_PATH = ROOT_PATH / 'data'
DB_PATH = ROOT_PATH / 'db'
LOGS_PATH = ROOT_PATH / 'logs'
EXTENSIONS_PATH = ROOT_PATH / 'extensions'

COGS_PATH = EXTENSIONS_PATH / 'cogs'
COMMANDS_PATH = EXTENSIONS_PATH / 'commands'

# PATHs (files)
PLAIN_TEXT_PATH = DATA_PATH / 'plaintext.json'
BASE_TEMPLATE_PATH = DATA_PATH / 'base_template.json'
ROLE_TEMPLATE_PATH = DATA_PATH / 'role_template.json'

#CONSTs
TEXT = utils.read_json(PLAIN_TEXT_PATH)
COGS = utils.get_Cogs(COGS_PATH)
COMMANDS = utils.get_Commands(COMMANDS_PATH)


#ENVs
ENV_PATH = ROOT_PATH / '.env_test' if DEBUG else '.env'
if not load_dotenv(ENV_PATH): raise Exception(f'Failed to load {ENV_PATH}')

CBOT_MAIL_ADD = getenv('MAILADD')             #CBOT E-Mail Address
CBOT_MAIL_PASS = getenv('MAILADD_PASS')       #CBOT E-Mail Address's Password
BASKENTMAIL = getenv('BASKENTMAIL')           #Başkent's MAIL DOMAIN
SEED = getenv('SEED')                         #SEED for hashing
SEMESTER = getenv('SEMESTER')                 #CURRENT SEMESTER
COMMAND_PREFIX = getenv('PREFIX')             #Command prefix 

CBOT_SECRET_TOKEN = getenv('CBOT_TOKEN')                            #CBOT's Discord API Token
GUILD_ID = int(getenv('MAIN_GUILD_ID'))                             #Başkent Üniversitesi Mühendislik Fakültesi Server ID
GATEWAY_GUILD_ID = int(getenv('GATEWAY_GUILD_ID'))                  #Geçiş Kapısı Server ID
FORUM_CHANNEL_ID = int(getenv('FORUM_CHANNEL_ID'))                    #Başkent Üniversitesi Mühendislik Fakültesi Server Forum Channel ID
GUILD_INVITE_CHANNEL_ID = int(getenv('GUILD_INVITE_CHANNEL_ID'))       #Başkent Üniversitesi Mühendislik Fakültesi Server 'Fakülte Genel' Text Channel
GATEWAY_INVITE_CHANNEL_ID = int(getenv('GATEWAY_INVITE_CHANNEL_ID'))   #Geçiş Kapısı Main Channel ID

   