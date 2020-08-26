import os
import sys
import logging
import logzero
from logzero import logger as log


class Config():

    VERSION = 1

    LOG_FOLDER = os.environ.get('ROUTER_PARSER_LOG_FOLDER', "log")
    OUTPUT_FOLDER = os.environ.get('ROUTER_PARSER_OUTPUT_FOLDER', "output")
    CONFIG_FOLDER = os.environ.get('ROUTER_PARSER_CONFIG_FOLDER', "configs")
    MAX_CONFIG_AGE = os.environ.get('ROUTER_PARSER_MAX_CONFIG_AGE', 5)  # max config age of a file, otherwise it's ignored
    CREATE_FOLDERS = True

    VERBOSE = eval(os.environ.get('VERBOSE', "False"))
    DEBUG = eval(os.environ.get('DEBUG', "False"))
    LOGLEVEL = logging.INFO
    LOGFILE = os.environ.get('ROUTER_PARSER_LOGFILE') or "router-parser.log"

    OFFLINE = False

    ENV = "PRODUCTION"

    # ADD YOUR CUSTOM APPLICATION PARAMETERS HERE, IF YOU WANT TO BE ABLE TO
    # OVERRIDE THEM IN config.env THEN USE 'os.environ.get()'
    # EX:
    # MY_VARIABLE = os.environ.get('MY_VARIABLE') or 'value for my variable'

    def __init__(self):
        # make sure all folders exist
        if self.CREATE_FOLDERS:
            for d in [ self.LOG_FOLDER, self.OUTPUT_FOLDER ]:
                if not os.path.exists(d):
                    os.makedirs(d)        

        # set logging level
        if self.LOGFILE:
            logzero.logfile(os.path.join(self.LOG_FOLDER, self.LOGFILE), maxBytes=1e6, backupCount=3)
        logzero.loglevel(self.LOGLEVEL)




    @classmethod
    def get_config(cls):
        """
        Supports 2 config modes, based on environment variable:
           ENV=DEBUG
           ENV=PRODUCTION
        """
        cfg = None
        if os.environ.get('ENV', "PROD").upper().startswith("DEB"):
            cfg = DebugConfig()
        else:
            cfg = ProductionConfig()

        log.debug("Configuration profile = {}".format(cfg.ENV))

        return cfg



class DebugConfig(Config):

    VERBOSE = True
    DEBUG = True
    LOGLEVEL = logging.DEBUG
    OFFLINE = True

    ENV = "DEBUG"
    DRYRUN = True

    def __init__(self):
        Config.__init__(self)




class ProductionConfig(Config):

    ENV = "PRODUCTION"

    def __init__(self):
        Config.__init__(self)



