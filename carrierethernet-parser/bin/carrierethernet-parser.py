# -*- coding: utf-8 -*-

import os
import re
import pprint
#from netaddr import IPNetwork
import logging
import argparse
import json
import sys
from nmsnetlib.parsers.carrierethernet import ERSParser, SAOSParser
from nmsnetlib.parsers.parsercollection import ParserCollection
from operator import itemgetter, attrgetter
import time
from configure import config as AppConfig
from datetime import datetime


## SETUP LOGGING
myconfig = AppConfig.get(os.environ.get("ENV").lower(), "prod")
logger = myconfig.main_logger
today = datetime.now().strftime("%Y-%m-%d")

# required for ascii table parsing:
#import docutils.statemachine
#import docutils.parsers.rst.tableparser


## GLOBAL VARIABLES
VERSION = "1.0"
VERSION_HISTORY = '''\
-- HISTORY --
1.0 - 20170804 - initial version
1.2 - 20200401 - add logging
                 update saos definition: PORTS section was changed after upgrades and therefore
                    LAG ports were not detected if they had any traffic-services
                    configure
'''



##### 
##### 
##### # define logging options
##### logger = logging.getLogger('blockparser')
##### logger.setLevel(logging.TRACE)
##### 
##### 
##### ## log formatting
##### screenformatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s : %(message)s')
##### fileformatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s : %(message)s')
##### ## filters
##### ## screen log handlers (disable by default -> Level 100)
##### logprinter = logging.StreamHandler()
##### logprinter.setFormatter(screenformatter)
##### logprinter.setLevel(logger.getEffectiveLevel())
##### ## file log handlers
##### debugprinter = logging.FileHandler(DEBUG_FILE)
##### debugprinter.setFormatter(fileformatter)
##### debugprinter.setLevel(logging.TRACE)
##### ## add handlers to the logger
##### logger.addHandler(logprinter)
##### logger.addHandler(debugprinter)
##### 
##### 




'''
    get the commandline arguments
'''
def get_args(default_config_dir="."):
    description = "Parse all CES backup."
    epilog = "Current version: {}\n\n".format(VERSION) + VERSION_HISTORY
    parser = argparse.ArgumentParser(description=description, epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-c", "--config-dir", help="Dir where the CES backup configs can be found (default = {})".format(default_config_dir),
                    default=default_config_dir)
    parser.add_argument("-D", "--delim", help="Column delimiter used for output (default = |)",
                    default="|")
    #parser.add_argument("-v", "--verbose", help="Show extra logging info on screen (default = False)",
    #                action="store_true", default=False)
    #parser.add_argument("-q", "--quiet", help="Quiet output, only show the summary results (default = False)",
    #                action="store_true", default=False)
    #parser.add_argument("-d", "--debug", help="Enable debug mode, logs are saved in the debug folder (default = False)",
    #                action="store_true", default=False)
    #parser.add_argument("-t", "--trace", help="Enable trace debug mode, logs are saved in the debug folder (default = False)",
    #                action="store_true", default=False)

    args = parser.parse_args()

    ## if quiet then disable the logprinter, set loglevel too high
    #if args.quiet:
    #    logprinter.setLevel(200)
    ## if debug then enable debugprinter, set global loglevel to DEBUG
    #if args.debug:
    #    logger.setLevel(logging.DEBUG)
    #    debugprinter.setLevel(logger.getEffectiveLevel())
    ## if debug then enable debugprinter, set global loglevel to DEBUG
    #if args.trace:
    #    logger.setLevel(logging.TRACE)
    #    debugprinter.setLevel(logger.getEffectiveLevel())
    ## if verbose then set to INFO logging level (unless debug is enabled) (default = CRITICAL)
    #if args.verbose:
    #    if not args.debug:
    #        logger.setLevel(logging.INFO)
    #    logprinter.setLevel(logger.getEffectiveLevel())

    return args




'''
    -----------------------------------------------------
                    START OF MAIN SCRIPT
    -----------------------------------------------------
'''


# def parseERS():
#     ### parse each ERS and print out the result, only the first time we want to see the CSV header
#     print_title = True
#     for f in configs:
#         ers = ERS(hostname=f, configfile=ERSDIR+f, delim=cmdargs.delim)
#         ers.parse()
#         if cmdargs.debug:
#             ers.debug_printer()
#         ers.printer_tdi(print_title=print_title, print_info=print_title)
#         print_title = False



def append_hostname(saos, db_file="db/hosts.json"):
    """
        Store hostname + mgmt IP in a json db db/hosts.json
        This can be used to generate a hosts file that is not dependant if parsing of a device fails or not
        { 'hostname': { 'mgmtip': '', 'added': 'timestamp', 'laststeen': 'timestamp' } }
    """
    db = {}
    now = str(time.time())
    hostname = saos.model.host.hostname
    chassisid = saos.model.host.chassisid
    mgmtip = saos.model.get_management_ip()

    ## read the hosts db
    try:
        with open(db_file) as f:
            db = json.load(f)
    except:
        logger.info("Hosts DB does not exist or is not valid, creating it now")

    ## update the hosts db
    if hostname in db:
        db[hostname]['mgmtip'] = mgmtip
        db[hostname]['lastseen'] = now
        db[hostname]['chassisid'] = chassisid
    else:
        h = { 'mgmtip': mgmtip, 'added': now, 'lastseen': now, 'chassisid': chassisid }
        db[hostname] = h

    ## write the hosts db
    with open(db_file, 'w') as f:
        logger.debug(db)
        json.dump(db, f, indent=4, sort_keys=True)




def parser(configdir="", configlist=[], 
                debug=False, 
                stopafter=800, 
                max_config_age_days=4,
                filefilter=None
                ):
    """
    Main parser script.
    Parameters:
      configlist = list of config files to parse
      debug = True|False
      stopafter = max number of files to parse
      max_config_age_days = ignore configs alder then specified
      file_filter = if specified: only parse files matching the filter
    """

    saoslist = ParserCollection(debug=debug)
    count = 0
    hosts_db_file = 'db/hosts.json'
    #filefilter = [ "28050-SDS39-001.txt", "00009-SAS51-011.txt", "00009-SAS51-010.txt", "00009-SAS87-001.txt", "00009-SAS87-002.txt", "00002-SAS87-001.txt", "00002-SAS87-002.txt", "00009-SAS51-002.txt" ]
    #filefilter = [ "28959-SDS39-001.txt", "28967-SDS39-001.txt", "28977-SDS39-001.txt", "00002-SAS51-008.txt", "00002-SAS51-009.txt", "26604-SDS39-001.txt" ]
    #filefilter = [ "28959-SDS39-001.txt", "28967-SDS39-001.txt", "28977-SDS39-001.txt", "00002-SAS51-008.txt", "00002-SAS51-009.txt", "26604-SDS39-001.txt" ]
    #filefilter = [ "00009-SAS51-019.txt", "00002-SAS51-019.txt" ]
    #filefilter = [ "00009-SAS51-060.txt", "00009-SAS51-061.txt", "28103-SDS39-002.txt",  #NOT OK: LR-ASR-BRU_17_35
    #                "00387-SAS51-001.txt", "00387-SAS51-002.txt", "28930-SDS39-001.txt" ] # OK: LR-ASR-BRU_19_45
    #filefilter = [ "00009-SAS51-060.txt" ]
    #filefilter = [ "00387-SAS51-001.txt" ]
    #filefilter = [ "00009-SAS51-024.txt" ]

    for s in configlist:

        configfile = os.path.join(configdir, s)

        # SAOS 8700 - parsing
        #if s != "00002-SAS87-001.txt":
        #if s != "00002-SAS51-001.txt":
        #    continue
        if count > stopafter:
            logger.warn("MAX number of parsed configs has been reached: {}".format(stopafter))
            break

        if filefilter and s not in filefilter:
            logger.info("Config is filtered out - skipping ({})".format(s))
            continue

        logger.info("Parsing {}".format(s))
        saos = SAOSParser(configfile=configfile, debug=debug)
        saos.parse()

        logger.debug("SAOS object: {}".format(saos))

        #for i in saos.model.switchports:
        #    print(i.name)

        count += 1
        ### append hostname + mgmt IP to the hosts DB
        ### keep track of historical hostnames because if parsing fails somehow then the hosts file will not be complete
        append_hostname(saos, hosts_db_file)

        # at the moment we skip parsing of 8700
        #if saos.model.system.hwtype and saos.model.system.hwtype is not "8700":
        #if saos.model.system.hwtype and saos.model.system.hwtype == "8700":
        if saos.model.system.hwtype:
            config_age = saos.model.get_last_config_date(indays=True)
            if config_age < max_config_age_days:
            #if config_age >= 5:
                saoslist.append(saos)
            else:
                logger.warn("SKIPPING OLD CONFIG: {}".format(configfile))
            #print(">>>>>>>>>>>> config age = {}".format())
            #print(">>>>>>>>>>>> firstseen: {}".format(saos.model.firstseen))
            #print(">>>>>>>>>>>> lastseen: {}".format(saos.model.lastseen))
        else:
            logger.info("SKIPPING UNKNOWN DEVICE: {} (file: {})".format(saos.model.host.hostname, configfile))

        #print saos.model.get_netjson_lldp()

    logger.info("finished parsing configs: {}".format(count))

    # saoslist.test();

    # connect the configs together based on LLDP
    saoslist.linkCollection()

    ### GENERAL INVENTORY INFO
    F = open('debug/raw.general_inventory.json', 'w')
    F.write(saoslist.get_general_inventory())
    F.close()
    F = open('output/general.inventory.{}.csv'.format(today), 'w')
    for line in saoslist.report_general_inventory():
        F.write("{}\n".format(",".join(line)))
    F.close()

    ### CONFIG CHECKS INVENTORY
    F = open('output/general.config_check.{}.csv'.format(today), 'w')
    for line in saoslist.report_config_check():
        F.write("{}\n".format(",".join(line)))
    F.close()

    ### GENERATE HOSTS FILE based on the hosts DB
    hosts_db = {}
    try:
        if os.path.isfile(hosts_db_file):
            with open(hosts_db_file) as f:
                hosts_db = json.load(f)
    except:
        pass
    F = open('output/hosts', 'w')
    F.write('## CARRIER ETHERNET\n')
    for h in hosts_db:
        F.write("{} {}\n".format(hosts_db[h].get('mgmtip', ''), h))
    F.close()
    
    ### SWITCHPORT INFO
    F = open('debug/raw.get_switchport_status.json', 'w')
    F.write(saoslist.get_switchport_status())
    F.close()
    F = open('output/switchport-status.inventory.{}.csv'.format(today), 'w')
    for line in saoslist.report_switchport_status():
        #print(line)
        F.write("{}\n".format(",".join(line)))
    F.close()
    
    ### LLDP debug info
    F = open('debug/raw.get_netjson_lldp.json', 'w')
    F.write(saoslist.get_netjson_lldp())
    F.close()

    ### LOGICAL RING INFO
    F = open('debug/raw.logical_ring_info.json', 'w')
    F.write(saoslist.get_logical_ring_info())
    F.close()
    F = open('output/logical-ringinfo.inventory.{}.csv'.format(today), 'w')
    for line in saoslist.report_logical_ring_inventory():
        F.write("{}\n".format(",".join(line)))
    F.close()

    ### VIRTUAL RING INFO
    F = open('debug/raw.virtual_ring_info.json', 'w')
    F.write(saoslist.get_virtual_ring_info())
    F.close()
    F = open('output/virtual-ringinfo.inventory.{}.csv'.format(today), 'w')
    for line in saoslist.report_virtual_ring_inventory():
        F.write("{}\n".format(",".join(line)))
    F.close()

    ### VLAN INFO
    F = open('debug/raw.vlan_info.json', 'w')
    F.write(saoslist.get_vlan_info())
    F.close()
    F = open('output/vlaninfo.inventory.{}.csv'.format(today), 'w')
    for line in saoslist.report_vlan_inventory():
        F.write("{}\n".format(",".join(line)))
    F.close()

    ### SERVICE INFO
    F = open('debug/raw.service_info.json', 'w')
    F.write(saoslist.get_service_info())
    F.close()
    F = open('output/services.inventory.{}.csv'.format(today), 'w')
    for line in saoslist.report_service_inventory():
        F.write("{}\n".format(",".join(line)))
    F.close()

    ### debug json per host
    for s in saoslist.parserlist:
        F = open('debug/raw.{}.json'.format(s.model.host.hostname), 'w')
        F.write(s.json())
        F.close()
    
    return

    # connect the configs together based on LLDP
    #SAOSParser.linkCollection(saoslist.parserlist)

    #    # generate the logical ringinfo report
    #    fn_logical_rings = "output/logical-ringinfo"
    #    _report_logical_ringinfo(saoslist.parserlist, fn_logical_rings)
    #
    #    # generate the virtual ringinfo report
    #    fn_virtual_rings = "output/virtual-ringinfo"
    #    _report_virtual_ringinfo(saoslist.parserlist, fn_virtual_rings)
    #
    #    # generate the CES/SVLAN report
    #    fn_svlans = "output/svlan-info"
    #    _report_svlans(saoslist.parserlist, fn_svlans)



if __name__ == "__main__":

    logger.info("-- start script --")
    
    cmdargs = get_args(myconfig.CARRIERETHERNET_PARSER_CONFIG_FOLDER)
    SAOSDIR = cmdargs.config_dir
    #DEBUG = True if (cmdargs.debug or cmdargs.trace) else False
    #SAOSDIR = '/Users/mwallraf/dev/alfie/trops-carrierethernet-parser.git/test_configs/SDS/'
    
    #logger.info("info")
    #logger.warning("warn")
    #logger.error("error")
    #logger.debug("debug")
    #logger.trace("trace")
    
    ## default config folders, use the first one that exists
    ## can be overridden by the --config-dir commandline option
    
    
    #for p in [ 
    #            #'/Users/mwallraf/dev/alfie/trops-carrierethernet-parser.git/test_configs/SDS/',
    #            '/opt/SCRIPTS/exscript-backup/configs/',
    #            '/Users/mwallraf/Documents/dev/Orange/trops-carrierethernet-parser/test-configs/'
    #        ]:
    #    if os.path.exists(p):
    #        SAOSDIR = p
    #        break
    
    if not SAOSDIR:
        logger.error("no SAOS config dir found")
        sys.exit()

    
    logger.info("SAOS config dir: {}".format(SAOSDIR))
    
    saosconfigs = [ f for f in os.listdir(SAOSDIR) if ( ("-SAS" in f.upper() or "-SDS" in f.upper()) and not f.startswith(".")) ]
    
    logger.debug("SAOS configs: {}".format(saosconfigs))
    
    # start the main parser
    max_parsed_files = 1200  # do not parse more then x files
    max_config_age = 4      # do not parse files older than x days
    config_filter = None    # if specified - only use configs matching the filter

    parser(configdir=SAOSDIR,
           configlist=saosconfigs, 
           debug=myconfig.DEBUG, 
           stopafter=max_parsed_files, 
           max_config_age_days=max_config_age, 
           filefilter=config_filter)
    


