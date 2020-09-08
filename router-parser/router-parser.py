import config
import logging
from logzero import logger as log
import logzero

import argparse
import sys

from lib.cpemodule import CpeModule
from lib.reporter import Reporter


def check_arg(args=None):
    """
    Parse command line arguments provided via command line.
    See the manual for argparse online for more information
    """
    parser = argparse.ArgumentParser(description='Script to learn basic argparse')
    #parser.add_argument('-H', '--host',
    #                    help='host ip',
    #                    required='True',
    #                    default='localhost')

    results = parser.parse_args(args)
    return results



def run_app(cfg={}, args={}):
    """
    Main code
    """

    cpe = CpeModule(dryrun=True, dryrun_config_age=cfg.MAX_CONFIG_AGE,
                    dryrun_config_folder=cfg.CONFIG_FOLDER, include_pe_interfaces=True,
                    allow_ip_as_hostname=False)

    cpe.ParseAllDevices()

    rpt = Reporter(cpe.p2p_objects)
    for l in rpt.report:
        print(l)



if __name__ == '__main__':
    """
    Main script, to use logzero you can do:
        log.info("some info")
    """

    # load the config file
    # to access parameters in the log file use
    #   ex: log.VERSION
    cfg = config.Config().get_config()

    # get commandline arguments
    script_args = check_arg(sys.argv[1:])
    log.debug("Command-line arguments: {}".format(script_args))

    run_app(cfg, script_args)



