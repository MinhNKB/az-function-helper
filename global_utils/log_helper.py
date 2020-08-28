import logging
from datetime import datetime

class LogHelper:
    def __init__(self):
        pass

    @classmethod
    def log_info(cls, tag, message):
        log_message = "LOGGING INFO - %s - %s" % (tag, message)
        logging.info(log_message)