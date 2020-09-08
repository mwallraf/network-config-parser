# Merges the output of the network-discovery script with the output of the router-parser script

import argparse
import sys
import pandas as pd



def check_arg(args=None):
    """
    Parse command line arguments provided via command line.
    See the manual for argparse online for more information
    """
    parser = argparse.ArgumentParser(description='Merge router-parser results with network-discovery results')
    parser.add_argument('--router-parser-result',
                        help='Output file of the router-parser script',
                        required=True,
                        default='output/output.csv.tmp')
    parser.add_argument('--router-parser-delim',
                        help='Delimiter of the router-parser output file',
                        required=False,
                        default='|')
    parser.add_argument('--network-discovery-result',
                        help='Output file of the network-discovery script',
                        required=True,
                        default='network-discovery/network-discovery.csv')
    parser.add_argument('--network-discovery-delim',
                        help='Delimiter of the network-discovery output file',
                        required=False,
                        default=',')
    parser.add_argument('--output-file',
                        help='Location of the resulting output file',
                        required=True,
                        default='output/output.csv')

    results = parser.parse_args(args)
    return results



def run_app(args={}):
    """
    Main code
    """

    # read the router parser file and convert all hostnames to lower case
    df1 = pd.read_csv(args.router_parser_result, delimiter=args.router_parser_delim, dtype=str)
    df1["CE_HOSTNAME"] = df1["CE_HOSTNAME"].str.lower()
    
    # read the network-discovery file and conver all hostnames to lower case + remove unnecessary columns
    df2 = pd.read_csv(args.network_discovery_result, delimiter=args.network_discovery_delim, dtype=str)
    df2 = df2.drop(columns=[ "managementip", "ip", "datasource", "sysdescr", "syscontact", "errors" ])
    df2["host"] = df2["host"].str.lower()
    
    # merge both files based on CE_HOSTNAME = hostname
    # drop the host column and rename all the network-discovery columns by prepending DISC_*
    df = pd.merge(df1, df2, how="left", left_on="CE_HOSTNAME", right_on="host")
    df = df.drop(columns=["host"])
    df = df.rename(columns={ "domainname": "DISC_DOMAINNAME", 
    	                     "community": "DISC_COMMUNITY", 
    	                     "sysobjid": "DISC_SYSOBJID", 
    	                     "vendor": "DISC_VENDOR", 
    	                     "hwtype": "DISC_HWTYPE",
                             "function": "DISC_FUNCTION", 
                             "service": "DISC_SERVICE", 
                             "napalm_driver": "NAPALM_DRIVER", 
                             "protocol": "DISC_PROTOCOL" })
    
    df.to_csv(args.output_file, index=False, sep=args.router_parser_delim)




if __name__ == '__main__':
    """
    """

    # get commandline arguments
    script_args = check_arg(sys.argv[1:])

    run_app(script_args)


