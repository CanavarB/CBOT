from common.globals import DEBUG, LOGS_PATH
from sys import stdout
import logging.handlers
import logging

if DEBUG:
    LOG_PATH = LOGS_PATH / 'development'
    LOG_LEVEL = logging.INFO
else:
    LOG_PATH = LOGS_PATH / 'production'
    LOG_LEVEL = logging.WARNING

class CLogger(logging.Logger):

    def __init__(self, PATH = LOG_PATH, LOGLEVEL = LOG_LEVEL, name='CBOT'):
        super().__init__(name)
        self.setLevel(LOGLEVEL)
        
        FileHandler = logging.handlers.RotatingFileHandler(
            filename= PATH / 'discord.log',
            encoding='utf-8',
            maxBytes=32 * 1024 * 1024,  # 32 MiB
            backupCount=5,  # Rotate through 5 files
        )
        ConsoleHandler=logging.StreamHandler(stdout)
        ConsoleHandler.setFormatter(_ColourFormatter())
        self.addHandler(ConsoleHandler)
        self.addHandler(FileHandler)

class _ColourFormatter(logging.Formatter):

    LEVEL_COLOURS = [
        (logging.DEBUG, '\x1b[40;1m'),
        (logging.INFO, '\x1b[34;1m'),
        (logging.WARNING, '\x1b[33;1m'),
        (logging.ERROR, '\x1b[31m'),
        (logging.CRITICAL, '\x1b[41m'),
    ]

    FORMATS = {
        level: logging.Formatter(
            f'\x1b[30;1m%(asctime)s\x1b[0m {colour}%(levelname)-8s\x1b[0m \x1b[35m%(name)s\x1b[0m %(message)s',
            '%Y-%m-%d %H:%M:%S',
        )
        for level, colour in LEVEL_COLOURS
    }

    def format(self, record):
        formatter = self.FORMATS.get(record.levelno)
        if formatter is None:
            formatter = self.FORMATS[logging.DEBUG]

        # Override the traceback to always print in red
        if record.exc_info:
            text = formatter.formatException(record.exc_info)
            record.exc_text = f'\x1b[31m{text}\x1b[0m'

        output = formatter.format(record)

        # Remove the cache layer
        record.exc_text = None
        return output