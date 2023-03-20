from settings.globals import *
from logging import INFO

#ENVs
GUILD_ID = int(getenv('MAIN_GUILD_ID'))          #Test Server ID
FORUM_CHANNEL_ID = int(getenv('FORUMCHANNELID')) #Başkent Üniversitesi Mühendislik Fakültesi Server Forum Channel ID

#PATHs
SEMESTER_DB_PATH = DB_PATH / f'{SEMESTER}_test.db'
GUILD_DB_PATH = DB_PATH / f'{GUILD_ID}.db'
LOG_PATH = LOGS_PATH / 'development'

#CONSTs
LOG_LEVEL = INFO


