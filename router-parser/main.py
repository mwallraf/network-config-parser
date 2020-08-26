

import re
import logging
import logging.config


from datetime import datetime, timedelta
from time import time
from router import Router, RouterFactory
from reporter import Reporter
import sys
import os

logging.config.fileConfig("etc/logging.conf")
log = logging.getLogger("findhost")
version = "0.1a"



class CpeModule(object):

    dryrun = True                   # simulate the script, do not connect to CPE devices
    dryrun_config_folder = '/opt/SCRIPTS/exscript-backup/configs/'  # location where to find configs to parse in offline mode
    dryrun_config_folder = './data/configs_test/'  # location where to find configs to parse in offline mode
    dryrun_config_age = 7;           # include config files which are not older then this value in days, 0 to ignore this check
    #iosdriver = None
    #accounts = None
    cpelist = []
    pelist = [ 'telnet://nos-emlp-01', 'telnet://ant-emlp-01', 'ssh://nos-mar-02', 'ssh://ant-mar-02', 'ssh://ant-ipsec-01', 'ssh://nos-ipsec-01', 'ssh://ant-ipsec-02', 'ssh://nos-ipsec-02', 'ssh://ant-var-01', 'ssh://nos-var-01', 'ssh://ant-var-02', 'ssh://nos-var-02', 'ssh://ant-var-03', 'ssh://nos-var-03', 'ssh://ant-var-04', 'ssh://nos-var-04', 'ssh://ant-var-05', 'ssh://nos-var-05', 'ssh://ar06bru', 'ssh://ant-imlp-01', 'ssh://nos-ha-01', 'ssh://ant-ha-01' ]
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

    def __init__(self):
        pass


    # stores the router object in the pe_objects or p2p_objects hash
    # for CPE => store in hash with key = P2P ip address, need to check if it's unique
    def _store_router_object(self, rtr):
        #print "--------- HOSTNAME: %s" % rtr.GetProp('hostname')
        if not rtr:
            log.warning('Router object is empty %s' % rtr)

        ## determine which list to add the interface object
        if rtr.isCPE():
            log.debug("Storing P2P interfaces for CPE router object: %s" % rtr.GetProp('hostname'))
            l = self.p2p_objects
            ## generate an error if the CPE does not have P2P interfaces, this means that it will not be reported
            if not len(rtr.getP2PInterfaces()) > 0:
                 log.error("Router %s does not have any P2P interfaces!" % rtr.GetProp('hostname'))
            #[ self.p2p_objects.setdefault(i.getId()).append(i) for i in rtr.getP2PInterfaces() ]
        elif rtr.isPE():
            log.debug("Storing P2P interfaces for PE router object: %s" % rtr.GetProp('hostname'))
            l = self.pe_objects
            #[ self.pe_objects.setdefault(i.getId()).append(i) for i in rtr.getP2PInterfaces() ]
        else:
            log.error('Unexpected router object found %s' % rtr)

        ## add the interface object to the list
        [ l.setdefault(i.getId(), []).append(i) for i in rtr.getP2PInterfaces() ]
        #print "len for %s = %s" % (rtr.GetProp('hostname'), len(rtr.getP2PInterfaces()))



    ## function for dryrun mode (no telnet connection is made, offline configs are used)
    def _dryrun_method(self):
        if not self.dryrun: return
        if not self.dryrun_config_folder:
            log.warning('DRYRUN folder %s not found - exit script' % self.dryrun_config_folder)

        log.debug('** DRYRUN folder = %s' % self.dryrun_config_folder)
        pe_routers = [ p.split('//')[1] for p in self.pelist ]
        log.debug("PE router list = %s" % pe_routers)
        configs = [ f for f in os.listdir(self.dryrun_config_folder) ]
        for c in configs:
            ## skip files starting with "."
            if c.startswith("."):
                log.info("skipping hostname starting with . : %s" % c)
                continue
            ## remove any extensions from the hostnames
            routername = c.split(".")[0]
            ## check if we allow IP addresses as hostname
            if not self.allow_ip_as_hostname:
                if re.match("[0-9]+\.[0-9]+\.[0-9]+\.[0-9]", routername):
                    log.info("skipping hostname '%s' because ip addresses are not allowed" % routername)
                    continue
            #r = RouterFactory()
            if routername.lower() in pe_routers:
                type = "PE"
            else:
                type = "CPE"
            #rtr = r.factory(routertype=type, saveconfig=None)
            rtr = RouterFactory.NewRouter(routertype=type, configfile=c)
            log.debug("Opening config file: {}".format("%s/%s" % (self.dryrun_config_folder, c)))
            with open("%s/%s" % (self.dryrun_config_folder, c), encoding="latin-1") as configfile:
                config=configfile.read()
            log.debug('** DRYRUN - parsing: %s (%s)' % (c, type))
            self._parser_running_config(rtr, config)

            # for CPE routers in dryrun method, check the config file age
            if int(self.dryrun_config_age) > 0 and type == "CPE":
                log.debug('check if config is less then %s days old' % self.dryrun_config_age)
                oldest_time = int(time()) - (self.dryrun_config_age * 3600 * 24)

                if int(rtr.getLastSeen()) < int(oldest_time):
                    log.warning('config is older then the expected {} days ({}) -- skipping: {}'.format(self.dryrun_config_age, oldest_time, c))
                    continue
                else:
                    log.debug('config age = %s' % (rtr.getLastSeen()))

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
                log.debug("PE INTERFACE LIST = %s" % self.pe_interface_ip)

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
        ip = "%s/%s" % (h['ip'], h['prefix'])
        if ip in self.pe_interface_ip:
            log.warning("IP address %s is known as an PE interface, do not process as CPE" % ip)
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






if __name__ == '__main__':
    now = datetime.now()
    cpe = CpeModule()

    cpe.include_pe_interfaces = True

    cpe.ParseAllDevices()
    now = datetime.now() - now
    #print "Running time = %s" % now
    ###print "CPE objects %s" % cpe.p2p_objects
    ###print "PE objects %s" % cpe.pe_objects
    #print "Router objects %s" % cpe.routers

    rpt = Reporter(cpe.p2p_objects)
    for l in rpt.report:
        print(l)



