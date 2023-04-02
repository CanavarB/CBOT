from termcolor import colored

from CDB import CDB, MemberNotFoundError, UserNotFoundError, ColumnValueError, GuildLectureNotFoundError
from CMail import CMail
from CLogger import CLogger


##############################
                            ##
DEBUG = True                ##
                            ##
##############################

if DEBUG:
    print(colored("Development Mode", 'green'))
    from settings.development import *
else:
    print(colored("Production Mode", 'red'))
    from settings.production import *


#CONSTs
LOGGER = CLogger(PATH = LOG_PATH, LOGLEVEL=LOG_LEVEL)
DB = CDB(SEMESTER_DB_PATH, GUILD_DB_PATH, logger=LOGGER)
MAIL = CMail(MAILADD=CBOT_MAIL_ADD, MAILADD_PASS=CBOT_MAIL_PASS, logger=LOGGER)
