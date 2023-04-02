from settings import CBOT_SECRET_TOKEN, LOG_LEVEL
from CBOT import CBOT

def main():
    cbot = CBOT()    
        
    cbot.run(CBOT_SECRET_TOKEN, log_level=LOG_LEVEL)

if __name__ == '__main__':
    main()