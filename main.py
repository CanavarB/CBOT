from settings import *
from CBOT import CBOT

def main():
    cbot = CBOT()    
        
    cbot.run(CBOT_SECRET_TOKEN, log_level=LOG_LEVEL)

if __name__ == '__main__':
    main()