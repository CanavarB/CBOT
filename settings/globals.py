from os import getenv
from dotenv import load_dotenv
from pathlib import Path
import utils
import discord
from discord.ext import commands, tasks


#PATHs (directory)
ROOT_PATH = Path(__file__).parent.parent.absolute()
SETTINGS_PATH = ROOT_PATH / 'settings'
DATA_PATH = ROOT_PATH / 'data'
DB_PATH = ROOT_PATH / 'db'
LOGS_PATH = ROOT_PATH / 'logs'
EXTENSIONS_PATH = ROOT_PATH / 'extensions'
COGS_PATH = EXTENSIONS_PATH / 'cogs'
COMMANDS_PATH = EXTENSIONS_PATH / 'commands'

# PATHs (files)
ENV_PATH = ROOT_PATH / '.env'
PLAIN_TEXT_PATH = DATA_PATH / 'plaintext.json'
BASE_TEMPLATE_PATH = DATA_PATH / 'base_template.json'
ROLE_TEMPLATE_PATH = DATA_PATH / 'role_template.json'

#ENVs
if not load_dotenv(ENV_PATH): raise Exception('Failed to load .env')


CBOT_SECRET_TOKEN = getenv('CBOT_TOKEN')         #CBOT's Discord API Token
GATEWAY_GUILD_ID = int(getenv('GATEWAY_GUILD_ID'))    #Geçiş Kapısı Server ID
GATEWAY_INVITE_LINK = getenv('GATEWAYINVITELINK')
CBOT_MAIL_ADD = getenv('MAILADD')                #CBOT E-Mail Address
CBOT_MAIL_PASS = getenv('MAILADD_PASS')          #CBOT E-Mail Address's Password
BASKENTMAIL = getenv('BASKENTMAIL')              #Başkent's MAIL DOMAIN
SEED = getenv('SEED')                            #SEED for hashing

#CONSTs
COMMAND_PREFIX = '$'
SEMESTER = '20222320'
TEXT = utils.read_json(PLAIN_TEXT_PATH)

COGS = utils.get_Cogs(COGS_PATH)
COMMANDS = utils.get_Commands(COMMANDS_PATH)

