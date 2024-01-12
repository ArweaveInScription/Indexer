import logging
from colorlog import ColoredFormatter
from config import DEBUG

def setup_logger(Debug=False):
    logger = logging.getLogger('index_logger')
    ch = logging.StreamHandler()
    if Debug:
        logger.setLevel(logging.DEBUG)
        ch.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
        ch.setLevel(logging.INFO)

    formatter = ColoredFormatter(
        "%(log_color)s%(asctime)s - %(levelname)-8s%(reset)s %(blue)s%(message)s",
        datefmt='%Y-%m-%d %H:%M:%S', 
        reset=True,
        log_colors={
            'DEBUG':    'cyan',
            'INFO':     'green',
            'WARNING':  'yellow',
            'ERROR':    'red',
            'CRITICAL': 'red,bg_white',
        },
        secondary_log_colors={},
        style='%'
    )

    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger

log = setup_logger(DEBUG)
