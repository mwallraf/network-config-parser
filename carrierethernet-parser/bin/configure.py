import logging
from logging.config import fileConfig

import os, sys


# create a TRACE loglevel
trace_level = logging.TRACE = logging.DEBUG - 5

def log_logger(self, message, *args, **kwargs):
    if self.isEnabledFor(trace_level):
        self._log(trace_level, message, args, **kwargs)

logging.getLoggerClass().trace = log_logger

def log_root(msg, *args, **kwargs):
    logging.log(trace_level, msg, *args, **kwargs)

logging.addLevelName(trace_level, "TRACE")
logging.trace = log_root

# initialize variables, tak from environment if exists
SCRIPTDIR = os.path.abspath(os.path.dirname(__file__))  ## This directory
CARRIERETHERNET_PARSER_LOG_FOLDER = os.environ.get("CARRIERETHERNET_PARSER_LOG_FOLDER", "log")
CARRIERETHERNET_PARSER_LOGFILE = os.environ.get("CARRIERETHERNET_PARSER_LOGFILE", "carrier-ethernet-parser")
CARRIERETHERNET_PARSER_DIR = os.environ.get("CARRIERETHERNET_PARSER_DIR", SCRIPTDIR)

# check that the logs folder exists
try: 
    os.mkdir(CARRIERETHERNET_PARSER_LOG_FOLDER) 
except OSError as error: 
    #print(error)
    pass

# set the logging files
logging.CARRIERETHERNET_PARSER_LOGFILE_MAIN = "{}/{}.log".format(CARRIERETHERNET_PARSER_LOG_FOLDER, CARRIERETHERNET_PARSER_LOGFILE)
logging.CARRIERETHERNET_PARSER_LOGFILE_MOD = "{}/{}-mod.log".format(CARRIERETHERNET_PARSER_LOG_FOLDER, CARRIERETHERNET_PARSER_LOGFILE)

# check that logging.config exists
fileConfig('{}/bin/logging.conf'.format(CARRIERETHERNET_PARSER_DIR))


class Config:

    main_logger = logging.getLogger("carrierethernet-parser")
    mod_logger = logging.getLogger("nmsnetlib")
        
    GLOBAL_KEY = "some value"

    APP_DIR = CARRIERETHERNET_PARSER_DIR
    CARRIERETHERNET_PARSER_CONFIG_FOLDER = os.environ.get("CARRIERETHERNET_PARSER_CONFIG_FOLDER", os.path.join(SCRIPTDIR, "configs"))
    CARRIERETHERNET_PARSER_DB_FOLDER = os.environ.get("CARRIERETHERNET_PARSER_DB_FOLDER", os.path.join(SCRIPTDIR, "db"))
    CARRIERETHERNET_PARSER_DEBUG_FOLDER = os.environ.get("CARRIERETHERNET_PARSER_DEBUG_FOLDER", os.path.join(SCRIPTDIR, "debug"))
    CARRIERETHERNET_PARSER_OUTPUT_FOLDER = os.environ.get("CARRIERETHERNET_PARSER_OUTPUT_FOLDER", os.path.join(SCRIPTDIR, "output"))
    CARRIERETHERNET_PARSER_MAX_CONFIG_AGE = int(os.environ.get("CARRIERETHERNET_PARSER_MAX_CONFIG_AGE", 4))
    CARRIERETHERNET_PARSER_MAX_PARSED_FILES = int(os.environ.get("CARRIERETHERNET_PARSER_MAX_PARSED_FILES", 1200))


    #print("config mode")


class ProductionConfig(Config):
    DEBUG = False
    DEVELOPMENT = False
    VERBOSE = False

    def __init__(self):
        Config.main_logger.setLevel(logging.NOTSET)
        Config.mod_logger.setLevel(logging.NOTSET)


class ProductionVerboseConfig(Config):
    DEBUG = False
    DEVELOPMENT = False
    VERBOSE = True

    def __init__(self):
        Config.main_logger.setLevel(logging.INFO)
        Config.mod_logger.setLevel(logging.INFO)


class DebugConfig(Config):
    DEBUG = True
    DEVELOPMENT = True
    VERBOSE = True

    def __init__(self):
        Config.main_logger.setLevel(logging.DEBUG)
        Config.mod_logger.setLevel(logging.DEBUG)


class TraceConfig(Config):
    DEBUG = True
    DEVELOPMENT = True
    VERBOSE = True

    def __init__(self):
        Config.main_logger.setLevel(logging.TRACE)
        Config.mod_logger.setLevel(logging.TRACE)


config = {
    'debug': DebugConfig,
    'trace': TraceConfig,
    'prod': ProductionConfig,
    'prod_verbose': ProductionVerboseConfig,
}
