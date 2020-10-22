from logzero import logger as log
import logzero
import os
import re
from time import time

from lib.router import Router, RouterFactory


class CpeModule(object):

    #dryrun = True                   # simulate the script, do not connect to CPE devices
    #dryrun_config_folder = '/opt/SCRIPTS/exscript-backup/configs/'  # location where to find configs to parse in offline mode
    #dryrun_config_folder = './data/configs_test/'  # location where to find configs to parse in offline mode
    #dryrun_config_age = 7;           # include config files which are not older then this value in days, 0 to ignore this check
    
    #iosdriver = None
    #accounts = None
    cpelist = []
    #pelist = [ 'telnet://nos-emlp-01', 'telnet://ant-emlp-01', 'ssh://nos-mar-02', 'ssh://ant-mar-02', 'ssh://ant-ipsec-01', 'ssh://nos-ipsec-01', 'ssh://ant-ipsec-02', 'ssh://nos-ipsec-02', 'ssh://ant-var-01', 'ssh://nos-var-01', 'ssh://ant-var-02', 'ssh://nos-var-02', 'ssh://ant-var-03', 'ssh://nos-var-03', 'ssh://ant-var-04', 'ssh://nos-var-04', 'ssh://ant-var-05', 'ssh://nos-var-05', 'ssh://ar06bru', 'ssh://ant-imlp-01', 'ssh://nos-ha-01', 'ssh://ant-ha-01' ]
    pelist = []
    #logdir = 'log'
    #configdir = 'configs'
    debug = None
    ## only connect to CPE's matching the filters, processed in top to bottom order
    ## CPE's not matching will be ignored
    connect_cpe_filters = [
                    '.*',
                    #'94.105.8.9',
                ]
    include_pe_interfaces = True    # if enabled then report on configured interfaces even if no matching online CPE was found
    allow_ip_as_hostname = False    # in dryrun method, allows filenames which exist of ip address

    stats = {}

    ## these are the references to all the router objects
    p2p_objects = {}   # 'P2P-ip': object
    pe_objects = {}
    pe_interface_ip = [] # list of all PE IP addresses, to quickly check if an IP was already processed
    ###routers = []  ## DEBUGGING ONLY

    UNKNOWN_FUNCTION = "unknown"
    RE_HEADER_FUNCTION = r"^! FUNCTION.*"


    def __init__(self, dryrun=True, dryrun_config_age=7,
                dryrun_config_folder="configs", include_pe_interfaces=True,
                allow_ip_as_hostname=False):

        self.dryrun = dryrun
        self.dryrun_config_age = int(dryrun_config_age)
        self.dryrun_config_folder = dryrun_config_folder
        self.include_pe_interfaces = include_pe_interfaces
        self.allow_ip_as_hostname = allow_ip_as_hostname

        # pre-parses all config files to retrieve the function of the config
        # file. This assumes that each config file has the line:
        #     ! FUNCTION: PE|CPE|...
        # in the first 100 caracters of the file
        self.parse_function = True

        # list of all the functions found by the preparser
        self.functions = []
        # { "function": [config1, config2, ..], "unknown": [configX, ..] }
        self.config_function_map = {}


    # stores the router object in the pe_objects or p2p_objects hash
    # for CPE => store in hash with key = P2P ip address, need to check if it's unique
    def _store_router_object(self, rtr):
        #print "--------- HOSTNAME: %s" % rtr.GetProp('hostname')
        if not rtr:
            log.warning('Router object is empty {}'.format(rtr))

        ## determine which list to add the interface object
        if rtr.isCPE():
            log.debug("Storing P2P interfaces for CPE router object: {}".format(rtr.GetProp('hostname')))
            l = self.p2p_objects
            ## generate an error if the CPE does not have P2P interfaces, this means that it will not be reported
            if not len(rtr.getP2PInterfaces()) > 0:
                 log.error("Router {} does not have any P2P interfaces!".format(rtr.GetProp('hostname')))
            #[ self.p2p_objects.setdefault(i.getId()).append(i) for i in rtr.getP2PInterfaces() ]
        elif rtr.isPE():
            log.debug("Storing P2P interfaces for PE router object: {}".format(rtr.GetProp('hostname')))
            l = self.pe_objects
            #[ self.pe_objects.setdefault(i.getId()).append(i) for i in rtr.getP2PInterfaces() ]
        else:
            log.error('Unexpected router object found {}'.format(rtr))

        ## add the interface object to the list
        [ l.setdefault(i.getId(), []).append(i) for i in rtr.getP2PInterfaces() ]
        #print "len for %s = %s" % (rtr.GetProp('hostname'), len(rtr.getP2PInterfaces()))


    def pre_parser(self, configs, header=20):
        """
        Checks the first 20 lines of each file for the line:
        ! FUNCTION: PE|CPE|...
        to find the function of each config file
        """

        def _parse_header(f, max_lines, rex):
            lines = []
            for line in f.readlines()[0:max_lines]:
                if rex.match(line):
                    lines.append(line.strip())
            return lines


        if not self.parse_function:
            return

        d = self.dryrun_config_folder
        rex = re.compile(self.RE_HEADER_FUNCTION)

        for cfg in configs:
            # read first N lines of a file
            with open(os.path.join(d, cfg), encoding='utf-8', errors='ignore') as f:
                # find all function header lines
                header_lines = _parse_header(f, header, rex)

                function = self.UNKNOWN_FUNCTION

                # add to the unkown function if not found
                if header_lines:
                    function = header_lines[0].split(" ")[-1]

                if function not in self.config_function_map:
                    self.config_function_map[function] = []
                    self.functions.append(function)

                self.config_function_map[function].append(cfg)

                log.debug("header_lines = {}".format(header_lines))
                log.debug("function = {}".format(function))

        log.debug("config_function_map: {}".format(self.config_function_map))


    def find_config_function(self, cfg):
        """
        Finds the function of a config file based on the pre_parser,
        cfg = the config filename
        The function is filtered from self.config_function_map
        """
        function = self.UNKNOWN_FUNCTION
        for f in self.functions:
            if cfg in self.config_function_map.get(f, []):
                function = f
                break
        log.debug("function found for config '{}': {}".format(cfg, function))
        return function



    ## function for dryrun mode (no telnet connection is made, offline configs are used)
    def _dryrun_method(self):
        if not self.dryrun: return

        if not self.dryrun_config_folder:
            log.warning('config folder {} not found - exit script'.format(self.dryrun_config_folder))
            sys.exit("config folder {} not found".format(self.dryrun_config_folder))

        log.debug('** config folder = {}'.format(self.dryrun_config_folder))
        #pe_routers = [ p.split('//')[1] for p in self.pelist ]
        #log.debug("PE router list = %s" % pe_routers)


        def validate_config_filename(d, f):
            """
            Some validation if we want to use the config file
            """
            validated = True
            if not os.path.isfile(os.path.join(d, f)):
                validated = False
            if f.startswith("."):
                validated = False
            return validated


        configs = [ f for f in os.listdir(self.dryrun_config_folder) if validate_config_filename(self.dryrun_config_folder, f) ]
        log.debug("configs found in {}: {}".format(self.dryrun_config_folder, configs))

        supported_routertypes = RouterFactory.SupportedRouterTypes()

        # start the preparser to find the function of each config
        self.pre_parser(configs)

        for c in configs:
            ## skip files starting with "."
            #if c.startswith("."):
            #    log.info("skipping hostname starting with . : %s" % c)
            #    continue
            ## remove any extensions from the hostnames
            routername = c.split(".")[0]
            ## check if we allow IP addresses as hostname
            if not self.allow_ip_as_hostname:
                if re.match("[0-9]+\.[0-9]+\.[0-9]+\.[0-9]", routername):
                    log.info("skipping hostname '{}' because ip addresses are not allowed".format(routername))
                    continue
            #r = RouterFactory()

            #if routername.lower() in pe_routers:
            #    type = "PE"
            #else:
            #    type = "CPE"

            config_function = self.find_config_function(c)

            if config_function not in supported_routertypes:
                log.warn("unsupported router type '{}', skip config file: {}".format(config_function, c))
                continue

            #rtr = r.factory(routertype=type, saveconfig=None)
            rtr = RouterFactory.NewRouter(routertype=config_function, configfile=c)

            log.debug("Opening config file: {}".format("{}/{}".format(self.dryrun_config_folder, c)))
            with open("{}/{}".format(self.dryrun_config_folder, c), encoding="latin-1") as configfile:
                config=configfile.read()
            log.debug('** DRYRUN - parsing: {} ({})'.format(c, config_function))
            self._parser_running_config(rtr, config)

            # for CPE routers in dryrun method, check the config file age
            if int(self.dryrun_config_age) > 0 and config_function == "CPE":
                log.debug('check if config is less then {} days old'.format(self.dryrun_config_age))
                oldest_time = int(time()) - (self.dryrun_config_age * 3600 * 24)

                if int(rtr.getLastSeen()) < int(oldest_time):
                    log.warning('config is older than the expected {} days ({}) -- skipping: {}'.format(self.dryrun_config_age, oldest_time, c))
                    continue
                else:
                    log.debug('config age = {}'.format(rtr.getLastSeen()))

            ## store the router object
            self._store_router_object(rtr)




    ## function for parsing the running config using the Router object
    ## rtr = Router object
    ## conf = running config
    def _parser_running_config(self, rtr, conf):
        #log.debug("CONFIG = %s" % conf)
        rtr.ParseRunningConfig(conf)


    ## single procedure to parse all known device types
    def ParseAllDevices(self):
        types = [ 'PE', 'CPE' ]
        if self.dryrun:
            ## configs can be in any order, avoid parsing 2x by overriding types array
            types = [ 'offline' ]
        for type in types:
            self.ParseDevices(type)
            ## after parsing PE devices then make a list of PE interface IP's, to check later on if an IP is already processed
            ## not needed in offline mode because CPE IP's are not taken from routing table in offline mode
            if type == 'PE':
                ##self.pe_interface_ip = [ str(self.pe_objects[x].ip) for x in self.pe_objects ]
                self.pe_interface_ip = [ o.ip for x in self.pe_objects for o in self.pe_objects[x] ]
                log.debug("PE INTERFACE LIST = {}".format(self.pe_interface_ip))

        ## update CPE data with info found on PE
        self.UpdateCpeFromPe()

        ## add PE data for interfaces not yet known in the CPE database
        ## TODO: add logging
        if self.include_pe_interfaces:
            self.AddPeData()

        ## procedure to generate the product info for each interface
        self.FindProductInfo()





    ## confirm if the IP really is a CPE device,  if it was already processed as PE interface then skip it
    def _is_cpe(self, h):
        ip = "{}/{}".format(h['ip'], h['prefix'])
        if ip in self.pe_interface_ip:
            log.warning("IP address {} is known as an PE interface, do not process as CPE".format(ip))
            return False
        return True



    # type = CPE or PE
    def ParseDevices(self, type):
        if self.dryrun:
            log.debug('DRYRUN MODE - no telnet/ssh connections made')
            self._dryrun_method()
            return



    ## go over all interfaces and try to find the product info
    ## this should be the last step, after all info is retrieved
    def FindProductInfo(self):
        log.info("Update product info for each interface")
        for p2p in self.pe_objects:
            for pe in self.pe_objects[p2p]:
                pe.UpdateProductInfoPE()
        for p2p in self.p2p_objects:
            for cpe in self.p2p_objects[p2p]:
                cpe.UpdateProductInfoPE()

    ## go over all the CPE P2P interfaces, if it's known in the PE info then add the extra info to the CPE interface object
    def UpdateCpeFromPe(self):
        # go over each CPE P2P object, check if it's known on the PE and then add the PE info to the CPE P2P object
        for p2p in self.p2p_objects:
            if p2p in self.pe_objects:
                for cpe_int in self.p2p_objects[p2p]:
                    ## TODO: what if duplicate CPE IP
                    for pe_int in self.pe_objects[p2p]:
                        cpe_int.add_pe_intf(pe_int)


    ## add PE interface information to the cpe p2p information database
    def AddPeData(self):
        # go over each PE P2P object, add it to the CPE P2P object database if it doesn't exist
        for p2p in self.pe_objects:
            if p2p not in self.p2p_objects:
               for pe_int in self.pe_objects[p2p]:
                   if p2p not in self.p2p_objects:
                       self.p2p_objects[p2p] = []
                   self.p2p_objects[p2p].append(pe_int)


