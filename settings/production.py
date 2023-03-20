from settings.globals import *
from logging import WARNING

#ENVs
GUILD_ID = int(getenv('MAIN_GUILD_ID'))           #Başkent Üniversitesi Mühendislik Fakültesi Server ID
FORUM_CHANNEL_ID = int(getenv('FORUMCHANNELID')) #Başkent Üniversitesi Mühendislik Fakültesi Server Forum Channel ID

#PATHs
SEMESTER_DB_PATH = DB_PATH / f'{SEMESTER}.db'
GUILD_DB_PATH = DB_PATH / f'{GUILD_ID}.db'
LOG_PATH = LOGS_PATH / 'production'

#CONSTs
LOG_LEVEL = WARNING
