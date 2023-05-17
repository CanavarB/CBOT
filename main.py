from common.globals import DEBUG, CBOT_SECRET_TOKEN
from CLogger import LOG_LEVEL
from CBOT import CBOT

# ANSI escape codes
RESET = '\033[0m'
RED = '\033[31m'
GREEN = '\033[32m'

def main():
    if DEBUG:
        print(GREEN, "Developer Mode", RESET)
    else:
        print(RED, "Production Mode", RESET)

    cbot = CBOT()    
        
    cbot.run(CBOT_SECRET_TOKEN, log_level=LOG_LEVEL)

if __name__ == '__main__':
    main()