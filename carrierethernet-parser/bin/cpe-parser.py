# -*- coding: utf-8 -*-

import os
import re
import pprint
#from netaddr import IPNetwork
import logging
import argparse
import json
import sys
from nmsnetlib.parsers.carrierethernet import CiscoIOSParser
from operator import itemgetter, attrgetter

# required for ascii table parsing:
#import docutils.statemachine
#import docutils.parsers.rst.tableparser


## GLOBAL VARIABLES
VERSION = "2.0"
VERSION_HISTORY = '''\
-- HISTORY --
1.0 - 20170804 - initial version
2.0 - 20201211 - dockerize
                  '''
HOMEDIR = os.path.abspath(os.path.dirname(__file__))  ## This directory
DEBUG_FILE = os.path.join(HOMEDIR, '..', 'debug', 'debug.log')
ERSDIR = ""


# define logging options
logger = logging.getLogger('CENparser')
logger.setLevel(logging.DEBUG)
## log formatting
screenformatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fileformatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
## filters
## screen log handlers (disable by default -> Level 100)
logprinter = logging.StreamHandler()
logprinter.setFormatter(screenformatter)
logprinter.setLevel(logger.getEffectiveLevel())
## file log handlers
debugprinter = logging.FileHandler(DEBUG_FILE)
debugprinter.setFormatter(fileformatter)
debugprinter.setLevel(logging.DEBUG)
## add handlers to the logger
logger.addHandler(logprinter)
logger.addHandler(debugprinter)







'''
    get the commandline arguments
'''
def get_args():
    description = "Parse all ERS backup config files and generate a list of TDI's and the corresponding UNI + Ring information."
    epilog = "Current version: {}\n\n".format(VERSION) + VERSION_HISTORY
    parser = argparse.ArgumentParser(description=description, epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-c", "--config-dir", help="Dir where the ERS backup configs can be found (default = {})".format(ERSDIR),
                    default=ERSDIR)
    parser.add_argument("-D", "--delim", help="Column delimiter used for output (default = |)",
                    default="|")
    parser.add_argument("-v", "--verbose", help="Show extra logging info on screen (default = False)",
                    action="store_true", default=False)
    parser.add_argument("-q", "--quiet", help="Quiet output, only show the summary results (default = False)",
                    action="store_true", default=False)
    parser.add_argument("-d", "--debug", help="Enable debug mode, logs are saved in the debug folder (default = False)",
                    action="store_true", default=False)

    args = parser.parse_args()
    ## if quiet then disable the logprinter, set loglevel too high
    if args.quiet:
        logprinter.setLevel(200)
    ## if debug then enable debugprinter, set global loglevel to DEBUG
    if args.debug:
        logger.setLevel(logging.DEBUG)
        debugprinter.setLevel(logger.getEffectiveLevel())
    ## if verbose then set to INFO logging level (unless debug is enabled) (default = CRITICAL)
    if args.verbose:
        if not args.debug:
            logger.setLevel(logging.INFO)
        logprinter.setLevel(logger.getEffectiveLevel())
    return args




'''
    -----------------------------------------------------
                    START OF MAIN SCRIPT
    -----------------------------------------------------
'''

cmdargs = get_args()

ERSDIR = cmdargs.config_dir

CONFIGDIR = '/Users/mwallraf/dev/alfie/trops-carrierethernet-parser.git/test_configs/IOS/'

configs = [ f for f in os.listdir(CONFIGDIR) ]

def parser():
    for s in configs:
        cfg = CiscoIOSParser(configfile=CONFIGDIR+s, debug=True)
        cfg.parse()
        print(">> parsing {}".format(s))
        print(cfg.json())

parser()



