# -*- coding:utf-8 -*-

from ciscoconfparse import CiscoConfParse
from logzero import logger as log
import logzero
import re

# from netaddr import IPNetwork, IPAddress
# from ipaddress import IPv4Network
import ipaddress
from time import time


## v0.1a - 2015-06-01: add lastseen property
## v0.1b - 2016-02-02: add properties "FIRST SEEN", "SERIALNUMBER", "VDSL LINEPROFILE"
## v0.1c - 2016-03-16: update getVdslLineProfile() + add property "VDSL LINEPROFILE UPDATED"
## v0.1d - 2016-05-24: add tunnel interface on IPSEC routers for 4G
## v0.1e - 2016-10-24: add property APN + SOFTWARE
## v0.1f - 2017-01-18: match VT regex on 5 or 6 digits, to make it work with new 6 digit VT's
## v0.1f - 2017-04-12: add properties for CELLULAR
## v0.1h - 2022-01-25: fix mismatches between ops/conf info about interfaces (uppercase/lowercase),
##                     for LBB15x devices


version = "v0.1h"


class RouterFactory(object):

    SUPPORTED_ROUTER_TYPES = ["CPE", "PE"]

    @staticmethod
    def NewRouter(routertype="CPE", configfile=""):
        log.debug("===> new router object from config file: %s" % configfile)
        rtr = ""
        if routertype == "PE":
            return PERouter(configfile)
        elif routertype == "CPE":
            return CPERouter(configfile)
        else:
            log.error("unsupported router type: %s" % routertype)
            raise ValueError('Unsupported router type: "%s".' % routertype)

    @staticmethod
    def SupportedRouterTypes():
        """
        Returns the supported router types
        """
        return RouterFactory.SUPPORTED_ROUTER_TYPES


class Router(object):
    # configdir = ""
    TELNETOK = 1  # number of days since "lastseen" timestamp that we consider telnet to be working
    INTERNAL_VRF = [
        "MODEM"
    ]  # internally used for mgmt purposes, exclude these from props like "is_multivrf"

    def __init__(self, configfile):
        self.props = {
            "hostname": "",  # this is the actual hostname found on the device
            "hostname_guess": "",  # this is the hostname found by "guessing" based on interface description
            "mgmt_interfaces": [],  # list of all mgmt (loopback for IPVPN or WAN P2P for CI) interfaces
            "p2p_interfaces": [],  # list of all WAN P2P interfaces
            "ipsec_tunnel_interfaces": [],  # list of all IPSEC Tunnel interfaces
            "mobile_interfaces": [],  # list of all mobile interfaces (ex. 3G, 4G)
            "all_interfaces": [],
            "all_vrfs": [],  # list of all VRF objects
            "lastseen": "0",  # epoch timestamp when the config was last saved, router was last seen
            "vendor": "",  # ex. CISCO | ONEACCESS
            "hardware": "",  # ex. 888C | LBB4G
            "function": "",  # ex. CPE | PE
            "apn": "",  # APN configured on the router
            "cellularimei": "",  # IMEI of sim card
            "cellularimsi": "",  # IMSI of sim card
            "cellularcellid": "",  # connected cell id
            "cellularoperator": "",  # connected operator
            "software": "",  # router software
            "telnetok": False,  # assume telnet is ok if lastseen date is recent
            "configfile": configfile,  # name of the config file that is being parsed
        }

    @property
    def is_multivrf(self):
        """Returns True if the router has at least 1 VRF configured
        VRFs used for management are excluded here
        """
        vrflist = [
            vrf for vrf in self.props["all_vrfs"] if vrf.vrf not in self.INTERNAL_VRF
        ]
        if len(vrflist) > 0:
            return True
        return False

    # parse the running config of a router and get all info
    def ParseRunningConfig(self, config):
        self.parser = CiscoConfParse(str(config).splitlines())
        # self.rtr._parse_running_config(parser)

        # generic parsers
        self._parse_config_header(
            [
                "HOSTNAME",
                "VENDOR",
                "LAST SEEN",
                "HARDWARE",
                "FUNCTION",
                "FIRST SEEN",
                "SERIALNUMBER",
                "VDSL BW DOWNLOAD",
                "VDSL BW UPLOAD",
                "VDSL LINEPROFILE",
                "VDSL LINEPROFILE UPDATED",
                "APN",
                "SOFTWARE",
                "CELLULAR IMEI",
                "CELLULAR IMSI",
                "CELLULAR CELLID",
                "CELLULAR OPERATOR",
            ]
        )
        self._parse_vrfs()
        self._parse_interfaces()

        # routertype specific parsers
        self._parse_running_config()

        # try to indicate if telnet has worked by checking the "last seen" time
        # let's assume that if it's more than 24h that telnet was not ok
        self.props["telnetok"] = self._calculate_lastseen()

    def GetProp(self, property):
        return self.props[property]

    def GetAllProps(self):
        return self.props

    def SetProp(self, property, value):
        self.props[property] = value

    def _calculate_lastseen(self):
        now = int(time())
        return (now - int(self.props["lastseen"])) < self.TELNETOK * 24 * 3600

    ## parse header parameters which are generated in the config files by the backup script
    ## they all should start with ! <param>: <value>
    def _parse_config_header(self, keywords):
        for kw in keywords:
            lines = self.parser.find_lines(r"^! %s:" % kw)
            if len(lines) > 0:
                log.info(
                    "property found in header: %s = %s" % (kw, lines[0].split(": ")[-1])
                )
                val = lines[0].split(": ")
                if len(val) > 1:
                    self.props[kw.replace(" ", "").lower()] = val[-1]
            else:
                # if kw == 'VDSL LINEPROFILE' or kw == 'VDSL LINEPROFILE UPDATED' or kw == 'FIRST SEEN' or kw == 'SERIALNUMBER':
                if kw in (
                    "VDSL LINEPROFILE",
                    "VDSL LINEPROFILE UPDATED",
                    "FIRST SEEN",
                    "SERIALNUMBER",
                    "VDSL BW DOWNLOAD",
                    "VDSL BW UPLOAD",
                ):
                    self.props[kw.replace(" ", "").lower()] = ""
                log.debug("property %s is not found in the config header" % kw)

    def GetAllVTFromRouter(self):
        allvt = []
        for i in self.props["all_interfaces"]:
            [allvt.append(vt) for vt in i.vt]
            [allvt.append(vt) for o in self.props["all_interfaces"] for vt in o.vt]
        return allvt

    def _merge_two_interfaces(self, intf1, intf2):
        """Merges two IOSCfgline objects into 1
        The interface of the intf1 is used as the new interface
        This returns again an IOSCfgline object
        """
        new_interface = CiscoConfParse(
            [intf1.text]
            + [line.text for line in intf1.children]
            + [line.text for line in intf2.children]
        )
        intf_cfg = new_interface.find_objects(intf1.text)
        return intf_cfg

    # parse the output of "show ip int brief" to find all L3 interfaces
    # for all the interfaces found, create an interface object
    # we use output of "show ip int brief" to make sure that we see the IP for DHCP interfaces and virtual interfaces
    def _parse_interfaces(self):
        lines = self.parser.find_lines(
            r"^! INT: .*\W([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+|<unassigned>).*([Uu]p|[Dd]own).*"
        )
        for l in lines:
            m = re.match(
                r"! INT: +([\w\/\. \-]+\w).*\W([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}|<unassigned>).*(?:[upUP]|[downDOWN])",
                l,
            )
            if not m:
                log.warn(
                    "skip parsing, no interface and ip found for line: {}".format(l)
                )
                continue
            if not (m and len(m.groups()) > 0):
                log.warn(
                    "L3 interface found but unable to parse interface or ip address (%s)"
                    % l
                )
            else:
                _intf = m.groups()[0].strip()
                _ip = m.groups()[1]
                _intf_name = _intf
                _intf_idx = ""

                log.debug("**** line = {}".format(l))
                log.debug("**** _intf = {}".format(_intf))
                log.debug("**** _ip = {}".format(_ip))

                ##### SOME INTERFACES CAN BE SKIPPED
                ## for OneAccess: skip interfaces matching ip = 127.0.0.1
                if _ip == "127.0.0.1":
                    log.debug("Skipping interface (%s) because of ip 127.0.0.1" % _intf)
                    continue
                elif _ip == "<unassigned>" and "Tunnel" not in _intf:
                    log.debug(
                        "Unassigned IP found for a none-tunnel interface - removing it"
                    )
                    continue
                elif _ip == "<unassigned>":
                    _ip = ""
                ## skip Cisco NVI interfaces
                if "NVI" in _intf:
                    log.debug(
                        "Skipping interface (%s) because of interface name" % _intf
                    )
                    continue
                if "Virtual-Access70." in _intf:
                    log.debug(
                        "Skipping interface (%s) because of interface name" % _intf
                    )
                    continue

                # we need to match the interface name found in "show ip int brief" with
                # the interface name found in "show running-config"
                # With severeal OS there is a mismatch due to change in upper/lower case
                # Exception: we don't want to match Dialer from "show ip int brief" with dialer from "show run"
                #            because this should be mapped to virtual-template instead
                all_interfaces = self.parser.find_lines("^interface \w+")
                m = re.findall(
                    r"interface ((?!Virtual-Access)[\w\/\. \-]+\w)",
                    "\n".join(all_interfaces),
                    re.MULTILINE,
                )
                matched_interfaces = [i for i in m if _intf.lower() == i.lower()]
                if matched_interfaces:
                    log.debug(
                        "matched the interface show_ip_int_brief={}, show_run={}".format(
                            _intf, matched_interfaces[0]
                        )
                    )
                    _intf = matched_interfaces[0]

                m = re.match(r"([^0-9]+)(.*)", _intf)
                # interface may be truncated in "show ip int brief" output
                if len(m.groups()) > 0:
                    _intf_name = m.groups()[0]
                    _intf_idx = m.groups()[1]
                log.debug("---> new L3 interface found: {} - {}".format(_intf, _ip))
                try:
                    # in some OS versions the first letter does not always correspond between
                    # operational output and config output
                    # caveat: don't lowercase Dialer interfaces because this messes up the
                    #         translation from dialer to virtual-template ppp
                    #         there also exists a dialer interface in the config but this
                    #         config does not have the ip address info etc
                    # if _intf_name.startswith("Dialer") or _intf_name.startswith(
                    #     "Virtual-Access"
                    # ):
                    #     first_letter = _intf_name[0]
                    # else:
                    #     first_letter = "[{}{}]".format(
                    #         _intf_name[0].lower(), _intf_name[0].upper()
                    #     )

                    # log.debug(m)
                    # for i in m:
                    #     log.debug("i={}".format(i))
                    #     log.debug("to match={}".format(_intf_name))
                    #     if i.lower() == _intf_name.lower():
                    #         print("MATCH FOUND")
                    # log.debug("all interfaces: {}".format(m))
                    # log.debug("matched interface: {}".format(found_interface))

                    # match the "show run" interfaces withe the "show ip int brief" interface
                    # intf_cfg = self.parser.find_objects(
                    #     "^interface {}{}[^0-9]*{}( .*)?$".format(
                    #         first_letter, _intf_name[1:], _intf_idx
                    #     )
                    # )
                    intf_cfg = self.parser.find_objects(
                        "^interface {}[^0-9]*{}( .*)?$".format(_intf_name, _intf_idx)
                    )

                    # if the interface is a dialer then we want to include the config from the virtual-template as well
                    m = re.match("[dD]ialer (.*)", _intf_name)
                    if m:
                        # intf_cfg.children = (
                        #     intf_cfg.children + virtual_template_cfg[0].children
                        # )

                        virtual_template_cfg = self.parser.find_objects(
                            "^%s[^0-9]*%s( .*)?$" % ("^virtual-template ppp", _intf_idx)
                        )
                        if len(virtual_template_cfg) > 0:
                            intf_cfg = self._merge_two_interfaces(
                                virtual_template_cfg[0], intf_cfg[0]
                            )
                            # log.debug(intf_cfg)
                            # log.debug(virtual_template_cfg)
                            # log.debug(
                            #     [line.text for line in virtual_template_cfg[0].children]
                            # )
                            log.debug(
                                "found virtual-template ppp configuration: {}".format(
                                    intf_cfg
                                )
                            )
                        pass

                except:
                    intf_cfg = []
                if not len(intf_cfg) > 0:
                    ### config was not found, maybe we should replace the virtual interface with the real interface
                    ### on LBB => replace "Dialer x" by "virtual-template ppp x"
                    DOCONTINUE = True
                    while DOCONTINUE:
                        ## replace Dialer by "virtual-template ppp"
                        m = re.match("Dialer (.*)", _intf)
                        if m:
                            log.debug(
                                "Trying to find a matching virtual-template interface"
                            )
                            _intf_name = _intf_name.replace(
                                "Dialer ", "virtual-template ppp"
                            )
                            intf_cfg = self.parser.find_objects(
                                "^%s[^0-9]*%s( .*)?$" % (_intf_name, _intf_idx)
                            )
                            if len(intf_cfg) > 0:
                                log.debug(
                                    "Match found: substituted Dialer interface by %s"
                                    % _intf_name
                                )
                                DOCONTINUE = False
                                continue
                        ## replace Virtual-Access by Virtual-Template
                        m = re.match("Virtual-Access[0-9]+", _intf)
                        if m:
                            log.debug(
                                "Trying to find a matching Virtual-Template interface"
                            )
                            _intf_name = _intf_name.replace(
                                "Virtual-Access", "Virtual-Template"
                            )
                            intf_cfg = self.parser.find_objects(
                                "^interface %s[^0-9]*%s( .*)?$"
                                % (_intf_name, _intf_idx)
                            )
                            if len(intf_cfg) > 0:
                                log.debug(
                                    "Match found: substituted Virtual-Access interface by %s"
                                    % _intf_name
                                )
                                DOCONTINUE = False
                                continue
                            else:
                                log.debug(
                                    "No substitute found for %s so assuming it's generated by a dialer interface"
                                    % _intf
                                )
                                DOCONTINUE = False
                                continue
                        DOCONTINUE = False
                        log.error("L3 interface found but no matching config (%s)" % l)

                elif len(intf_cfg) > 1:
                    log.warn(
                        "L3 interface found with multiple matches in the config (%s)"
                        % l
                    )
                for obj in intf_cfg:
                    intf = interface(obj, self, _ip)
                    if intf.isMgmt():
                        self.props["mgmt_interfaces"].append(intf)
                    elif intf.isP2P():
                        self.props["p2p_interfaces"].append(intf)
                    elif intf.isIPSEC():
                        self.props["ipsec_tunnel_interfaces"].append(intf)
                    elif intf.isMOBILE():
                        self.props["mobile_interfaces"].append(intf)
                    self.props["all_interfaces"].append(intf)

    def _parse_vrfs(self):
        # get all VRF config
        all_vrfs = self.parser.find_objects("^ip vrf ")
        for obj in all_vrfs:
            vrf = VRF(obj, self)
            self.props["all_vrfs"].append(vrf)

    # part of config header
    # def _parse_apn_4g(self):
    #    # check for the 4G APN FIXB2B4G.BE
    #    apn = self.parser.find_objects("apn FIXB2B4G.BE")
    #    if len(apn) > 0:
    #        self.props['apn'] = "FIXB2B4G.BE"

    def getP2PInterfaces(self, includeIPSEC=True, includeMOBILE=False):
        rc = self.props["p2p_interfaces"]
        if includeIPSEC:
            rc = rc + self.props["ipsec_tunnel_interfaces"]
        if includeMOBILE:
            rc = rc + self.props["mobile_interfaces"]
        return rc

    def getMgmtInterfaces(self):
        return self.props["mgmt_interfaces"]

    def getIpsecTunnelInterfaces(self):
        return self.props["ipsec_tunnel_interfaces"]

    def getMobileInterfaces(self):
        return self.props["mobile_interfaces"]

    def getLastSeen(self):
        return self.props["lastseen"]

    def getFirstSeen(self):
        return self.props["firstseen"]

    def getSerialNumber(self):
        return self.props["serialnumber"]

    def getVdslLineProfile(self):
        vdsl = {"LP": "", "BW_DOWN": "", "BW_UP": ""}
        m = re.match("(LP[0-9]+) \((.*)\/(.*)\)", self.props["vdsllineprofile"])
        if m:
            vdsl["LP"] = m.group(1)
            vdsl["BW_DOWN"] = m.group(2)
            vdsl["BW_UP"] = m.group(3)
        return vdsl
        # return self.props['vdsllineprofile']


class PERouter(Router):
    def __init__(self, configfile):
        log.debug("new PE router object")
        Router.__init__(self, configfile)

    def _parse_running_config(self):
        log.debug("parse PE specific config")

    def getType(self):
        return "PE"

    def isPE(self):
        return True

    def isCPE(self):
        return False


class CPERouter(Router):
    def __init__(self, configfile):
        log.debug("new CPE router object")
        Router.__init__(self, configfile)

    def _parse_running_config(self):
        log.debug("parse CPE specific config")

    def getType(self):
        return "CPE"

    def isPE(self):
        return False

    def isCPE(self):
        return True


class interface(object):

    # STATIC variables
    NAT_NONE = 0
    NAT_IN = 1
    NAT_OUT = 2
    NAT_BOTH = 3

    ## precompiled regex
    # reIntf = re.compile(".*interface ([^ ]+)")
    # reIntf = re.compile("(interface|virtual-template) (?P<INTF>[^0-9]+[0-9][^ ]*).*")
    reIntf = re.compile("(?:interface )?(?P<INTF>[^0-9]+[0-9][^ ]*).*")
    reDescr = re.compile(".*description (.*)")
    reBW = re.compile(" bandwidth ([0-9]+)")
    reDot1q = re.compile(".*encapsulation dot1Q ([0-9]+)", re.IGNORECASE)
    reIp = re.compile(
        ".*ip(?:v4)? address (?P<IP>[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+) (?P<MASK>[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+) ?(?P<SEC>secondary)?"
    )
    rePolicy = re.compile(".*service-policy (?P<DIR>input|output) (?P<POL>.*)")
    reVRF = re.compile("(.*ip vrf forwarding|.*vrf) (?P<VRF>.*)")
    reSpeed = re.compile(".*speed ([0-9]+)")
    # TODO: fix reDuplex regex
    reDuplex = re.compile("(?:duplex )?(.*)(?:\-duplex)?")
    reStandby = re.compile(".*standby (?P<ID>[0-9]+) (?P<CMD>[^ ]+) (?P<PARM>[^ ]+)$")
    reAccessGroup = re.compile(".*ip access-group (?P<ACL>[^ ]+) (?P<DIR>[^ ]+).*")
    reNat = re.compile(".*ip nat (?P<DIR>inside|outside).*")
    reVDSL2SharedVlanPPP = re.compile(
        ".*ppp pap sent-username (?P<USER>[^ ]+) password [0-9] (?P<PASS>[^ ]+)"
    )
    reVDSL2SharedVlanPPPuser = re.compile(" *username +(?P<USER>VT\d+_MAIN.*)")
    reVDSL2SharedVlanPPPpassword = re.compile(" *password +(?P<PASS>MAIN_.*_PPP)")
    reDescrHostnameGuess = re.compile(
        ".*[ -](?:HN:)?(?P<HOSTNAME>[^ -]{2,}-[^ -]{3,}-[^ -]{2,})"
    )
    reDescrVtRef = re.compile("VT[0-9]{5,6}")
    reIpHelper = re.compile(
        ".*ip helper-address (?P<HELPER>[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)"
    )
    rePvc = re.compile(".*pvc (?P<PVC>[0-9]+\/[0-9]+)")
    reTunnel = re.compile(" +tunnel ")
    reTunnelVrf = re.compile(" +tunnel vrf (?P<VRF>\S+)")
    reTunnelKey = re.compile(" +tunnel key (?P<KEY>\S+)")
    reTunnelSource = re.compile(" +tunnel source (?P<SRC>\S+)")
    reTunnelDestination = re.compile(" +tunnel destination (?P<DST>\S+)")
    reTunnelIpsecProfile = re.compile(
        " +tunnel protection ipsec profile (?P<PROFILE>\S+)"
    )
    reTunnelHubIp = re.compile(" +ip nhrp nhs (?P<IP>[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)")

    # returns True if the interface is a management interface
    def isMgmt(self):
        return (self.product_obj.type == "LOOPBACK") and (
            self.product_obj.function == "MGMT"
        )

    # returns True if the interface is a P2P interface
    def isP2P(self):
        return (self.product_obj.type == "P2P") and (self.product_obj.function == "WAN")

    # return IPSEC P2P interfaces
    def isIPSEC(self):
        return self.product_obj.function == "IPSEC"

    # return MOBILE IP inteface
    def isMOBILE(self):
        return self.product_obj.transmission == "MOBILE"

    # conf = cisco conf parsers interface object
    # p = parent object (= router)
    def __init__(self, conf, p, ip):
        log.debug("new interface object for router %s" % p.GetProp("hostname"))
        self.intf = ""  # ex. FastEthernet0/0  (like found in the config)
        self.ip = ip  # ex. 10.10.10.10/24
        self.network = ""  # network address of the ip  (ex. 10.10.10.0)
        self.mask = ""  # mask of the ip ("ex. 255.255.255.0)
        self.secip = []  # secondary ips, ex. [ '1.2.2.2/24' ]
        # self.function = ""       # AUTO POPULATED: MGMT/LAN/WAN/OTHER
        # self.type = ""           # AUTO POPULATED: p2p/loopback/ipsec/ipsec-mgmt/other
        # self.product = ""        # AUTO POPULATED: IPVPN/CI/IP-UPLINK
        self.product_obj = Product()  # store the product related to this interface
        # self.transmission = ""   # ATM/Ethernet/VDSL/Explore/3G/4G/internet ...
        self.descr = ""  # int description
        self.hostname_guess = ""  # guess cpe hostname based on interface description
        self.pe_guess = ""  # guess the pe hostname base on the interface description
        ### TODO: refer to the VRF object
        self.vrf = ""  # VRF the interface belongs to
        self.policy_in = ""  # QOS input policy
        self.policy_out = ""  # QOS output policy
        self.intfbw = ""  # bandwidth statement
        self.vlan = ""  # vlan id (either from "interface vlan <id>" or dot1q value)
        self.subint = ""  # subinterface (ex. Gi3/0.112)
        self.speed = ""  # configured speed (10/100/1000)
        self.duplex = ""  # configured duplex (auto/half/full)
        self.standby = {}  # standby{'groupid': { 'ip', 'priority' }}
        self.acl_in = ""  # ACL inbound
        self.acl_out = ""  # ACL outbound
        # self.nat_in = False      # inbound NAT configured
        # self.nat_out = False     # outbound NAT configurd
        self.nat = 0  # nat is enabled (0 = not, 1 = inbound, 2 = outbound, 3 = both)
        self.vdsl2 = {}  # { 'type': shared|dedicated, 'ppp_user': "", 'ppp_pass': "" }
        self.rtr = ""  # parent router object
        self.pe_intf_objects = []  # list of corresponding PE interface objects
        self.vt = []  # VT reference for this interface
        self.iphelpers = []  # IP Helper addresses
        self.pvc = ""  # atm pvc  2/33
        self.tunnel = {  # tunnel details
            "vrf": "",  # tunnel vrf UNTRUST
            "key": "",  # tunnel key 1508
            "source": "",  # tunnel source Dialer1
            "destination": "",  # tunnel destination 94.105.139.186
            "ipsecprofile": "",  # tunnel protection ipsec profile PSK-ipsec-prof
            "hubip": "",  # ip nhrp nhs 192.0.0.254
        }

        self.rtr = p
        # parent router object where the interface belongs to

        # parse the interface config
        self.parse(conf)
        # find initial product based on IP address, to determine interface type
        # self._find_product_by_ip()
        self.UpdateProductInfo()

        log.debug(
            "-- summary for '%s': product=%s, function=%s, type=%s, transmission=%s"
            % (
                self.intf,
                self.product_obj.product,
                self.product_obj.function,
                self.product_obj.type,
                self.product_obj.transmission,
            )
        )

    ## returns what is supposed to be a unique key for this interface/product
    ## for regular P2P interfaces the P2P network address should be unique
    ## for IPSEC Tunnel interfaces it's the tunnel ID + network address
    def getId(self):
        id = self.network
        if self.isIPSEC():
            # for tunnels with tunnel key
            if self.tunnel["key"]:
                id = "%s-%s" % (id, self.tunnel["key"])
            # otherwise if function-source-destination (for PE) or function-destination-source
            elif self.tunnel["source"] and self.tunnel["destination"]:
                if self.rtr.isCPE():
                    id = "%s-%s-%s" % (
                        "tunnel",
                        self.tunnel["destination"],
                        self.tunnel["source"],
                    )
                else:
                    id = "%s-%s-%s" % (
                        "tunnel",
                        self.tunnel["source"],
                        self.tunnel["destination"],
                    )

        return id

    ## Procedure to override Product info based on extra parameters
    ## this should could after all the info about the interface, router, PE is known
    def UpdateProductInfo(self):
        self.product_obj.ProductByInterface(self.intf)
        self.product_obj.ProductByIp(self.ip)
        # self._find_product_by_pe_interface()
        # override automatic found product info
        if "ppp_user" in self.vdsl2:
            self.product_obj.UpdateProduct("transmission", "VDSL", "'VDSL2 user info'")

    ## try to determine the product or interface type based on pe interface
    ## only needed for PE to PE connections so skip it if this is a CPE interace
    ## TODO: CORRECT, only for PE to PE???
    def UpdateProductInfoPE(self):
        if self.rtr.isCPE():
            log.debug("CPE interface - no need to guess product based on PE interface")
            return
        else:
            self.product_obj.ProductByPEIntf(self.rtr.GetProp("hostname"), self.intf)
            # if not p: return
            # self.product = p['product']
            # self.type = p['type']
            # self.function = p['function']

    ## main parser function
    def parse(self, intfobj):
        m = self.reIntf.match(intfobj.text)
        if not (m and len(m.groups()) > 0):
            log.error("interface was not found in '%s'" % intfobj.text)
        else:
            # self._parse_interface_name(m.groups()[0])
            self._parse_interface_name(m.group("INTF"))

        for l in intfobj.children:
            log.debug("** INTERFACE CONFIG LINE: {}".format(l))
            # description
            m = self.reDescr.match(l.text)
            if m:
                self._parse_description(m.group(1))
                continue
            # bandwidth
            m = self.reBW.match(l.text)
            if m:
                self._parse_intf_bw(m.group(1))
                continue
            # ip address
            m = self.reIp.match(l.text)
            if m:
                self._parse_ipaddr(l.text, m)
                continue
            # VRF
            m = self.reVRF.match(l.text)
            if m:
                self._parse_vrf(m.group("VRF"))
                continue
            # service-policy
            m = self.rePolicy.match(l.text)
            if m:
                self._parse_service_policy(l.text, m)
                continue
            # dot1q
            m = self.reDot1q.match(l.text)
            if m:
                self._parse_dot1q(m.group(1))
                continue
            # interface speed (auto-10-100)
            m = self.reSpeed.match(l.text)
            if m:
                self._parse_speed(m.group(1))
                continue
            # interface duplex
            # m = self.reDuplex.match(l.text)
            # if m:
            #    self._parse_duplex(m.group(1))
            #    continue
            # HSRP standby
            m = self.reStandby.match(l.text)
            if m:
                self._parse_standby(l.text, m)
                continue
            # ACL access-group
            m = self.reAccessGroup.match(l.text)
            if m:
                self._parse_access_group(l.text, m)
                continue
            # NAT
            m = self.reNat.match(l.text)
            if m:
                self._parse_nat(l.text, m)
                continue
            m = self.reVDSL2SharedVlanPPP.match(l.text)
            if m:
                self._parse_vdls2_shared_ppp(l.text, m)
                continue
            m = self.reVDSL2SharedVlanPPPuser.match(l.text)
            if m:
                self._parse_vdls2_shared_ppp_user(l.text, m)
                continue
            m = self.reVDSL2SharedVlanPPPpassword.match(l.text)
            if m:
                self._parse_vdls2_shared_ppp_password(l.text, m)
                continue
            m = self.reIpHelper.match(l.text)
            if m:
                self._parse_iphelper(m)
                continue
            m = self.rePvc.match(l.text)
            if m:
                self._parse_pvc(m)
                continue
            m = self.reTunnel.match(l.text)
            if m:
                self._parse_tunnel(l.text)
                continue
            m = self.reTunnelHubIp.match(l.text)
            if m:
                self._parse_nhrp_hubip(m)
                continue
            else:
                ## catch-all rule for debugging
                log.debug("XXX skip: %s" % l.text)

        # for VDSL PPP Sessions it's possible that there is no IP address information
        # inside the virtual-template (IP is obtained dynamically)
        # In this case we will assume that the received IP is a /30 and we recalculate
        # the ip address information here
        if self.ip and self.vdsl2.get("ppp_user", None) and not self.network:
            log.debug(
                "IP subnet {}/30 is assumed because VDSL PPP ip was received dynamically".format(
                    self.ip
                )
            )
            calculated_ip = "ip address {} 255.255.255.252".format(self.ip)
            m = self.reIp.match(calculated_ip)
            if m:
                self._parse_ipaddr(calculated_ip, m)

    ## parse ip nhrp info
    def _parse_nhrp_hubip(self, m):
        self.tunnel["hubip"] = m.group("IP")
        log.debug("--> tunnel hub ip found: %s" % m.group("IP"))

    ## parse tunnel info
    def _parse_tunnel(self, line):
        m = self.reTunnelVrf.match(line)
        if m:
            self.tunnel["vrf"] = m.group("VRF")
            log.debug("--> tunnel vrf found: %s" % m.group("VRF"))
            return
        m = self.reTunnelKey.match(line)
        if m:
            self.tunnel["key"] = m.group("KEY")
            log.debug("--> tunnel key found: %s" % m.group("KEY"))
            return
        m = self.reTunnelSource.match(line)
        if m:
            self.tunnel["source"] = m.group("SRC")
            log.debug("--> tunnel source found: %s" % m.group("SRC"))
            return
        m = self.reTunnelDestination.match(line)
        if m:
            self.tunnel["destination"] = m.group("DST")
            log.debug("--> tunnel destination found: %s" % m.group("DST"))
            return
        m = self.reTunnelIpsecProfile.match(line)
        if m:
            self.tunnel["ipsecprofile"] = m.group("PROFILE")
            log.debug("--> tunnel ipsec profile found: %s" % m.group("PROFILE"))
            return

    ## parse PVC
    def _parse_pvc(self, m):
        self.pvc = m.group("PVC")
        log.debug("--> PVC found: %s" % m.group("PVC"))

    ## parse IP Helpers
    def _parse_iphelper(self, m):
        self.iphelpers.append(m.group("HELPER"))
        log.debug("--> IP Helper address found: %s" % (m.group("HELPER")))

    ## parse VDSL2 shared vlan ppp
    def _parse_vdls2_shared_ppp(self, text, m):
        self.vdsl2["ppp_user"] = m.group("USER")
        self.vdsl2["ppp_pass"] = m.group("PASS")
        log.debug(
            "--> VDLS2 shared vlan PPP found: %s (%s)"
            % (self.vdsl2["ppp_user"], self.vdsl2["ppp_pass"])
        )

    ## parse VDSL2 shared vlan ppp username
    def _parse_vdls2_shared_ppp_user(self, text, m):
        self.vdsl2["ppp_user"] = m.group("USER")
        log.debug(
            "--> VDLS2 shared vlan PPP username found: {}".format(
                self.vdsl2["ppp_user"]
            )
        )

    ## parse VDSL2 shared vlan ppp password
    def _parse_vdls2_shared_ppp_password(self, text, m):
        self.vdsl2["ppp_pass"] = m.group("PASS")
        log.debug(
            "--> VDLS2 shared vlan PPP password found: {}".format(
                self.vdsl2["ppp_pass"]
            )
        )

    ## parse NAT
    def _parse_nat(self, text, m):
        if m.group("DIR") == "inside":
            self.nat = self.nat | self.NAT_IN
            # self.nat_in = True
        else:
            # self.nat_out = True
            self.nat = self.nat | self.NAT_OUT
        log.debug("--> NAT found: %s" % self.nat)

    ## parse ACL access-group
    def _parse_access_group(self, text, m):
        if m.group("DIR") == "in":
            self.acl_in = m.group("ACL")
            log.debug("--> ACL INBOUND found: %s" % self.acl_in)
        else:
            self.acl_out = m.group("ACL")
            log.debug("--> ACL OUTBOUND found: %s" % self.acl_out)

    ## parse HSRP standby group
    def _parse_standby(self, text, m):
        if not m.group("ID") in self.standby:
            self.standby[m.group("ID")] = {}
        self.standby[m.group("ID")][m.group("CMD")] = m.group("PARM")
        log.debug(
            "--> HSRP line found: id=%s cmd=%s parm=%s"
            % (m.group("ID"), m.group("CMD"), m.group("PARM"))
        )

    ## parse interface duplex
    def _parse_duplex(self, text):
        self.duplex = text
        log.debug("--> interface duplex: %s" % self.duplex)

    ## parse interface speed
    def _parse_speed(self, text):
        self.speed = text
        log.debug("--> interface speed: %s" % self.speed)

    ## parse dot1q
    def _parse_dot1q(self, text):
        self.vlan = text
        log.debug("--> DOT1Q/vlan id found: %s" % self.vlan)

    ## parse service-policy
    def _parse_service_policy(self, text, m):
        if m.group("DIR") == "input":
            self.policy_in = m.group("POL")
            log.debug("--> INPUT QOS Policy found: %s" % self.policy_in)
        else:
            self.policy_out = m.group("POL")
            log.debug("--> OUTPUT QOS Policy found: %s" % self.policy_out)

    ## parse VRF info
    def _parse_vrf(self, text):
        self.vrf = text
        log.debug("--> VRF found: %s" % self.vrf)

    ## parse IP addresses
    def _parse_ipaddr(self, text, m):
        # print(m.group('IP'), m.group('MASK'))
        # net = IPv4Network("%s/%s" % (m.group('IP'), m.group('MASK')))
        net = ipaddress.ip_interface("{}/{}".format(m.group("IP"), m.group("MASK")))
        log.debug("--> ip address found:")
        ip = "%s/%s" % (net.ip, net.network.prefixlen)
        if not m.group("SEC"):
            self.ip = ip
            self.network = net.network
            self.mask = net.netmask
            log.debug("----> IP: %s" % self.ip)
            log.debug("----> NETWORK: %s" % self.network)
            log.debug("----> MASK: %s" % self.mask)
        else:
            self.secip.append(ip)
            log.debug("----> SECONDARY IP: %s" % ip)

    ## parse the interface name (FastEthernet0/0, ATM0.200, ...)
    def _parse_interface_name(self, text):
        self.intf = text
        log.debug("-> interface found: %s" % self.intf)
        # check for vlan id
        m = re.match("vlan *([0-9]+)", self.intf, re.IGNORECASE)
        if m:
            self.vlan = m.group(1)
            log.debug("--> vlan found: %s" % self.vlan)
        # check for subinterface
        m = re.match(".*\.(.*)", self.intf)
        if m:
            self.subint = m.group(1)
            log.debug("--> subinterface found: %s" % self.subint)

    ## parse the interface desciption
    def _parse_description(self, text):
        self.descr = text
        log.debug("--> description found: %s" % self.descr)
        ## try to find hostname in description
        m = re.match(self.reDescrHostnameGuess, text)
        if m:
            h = m.group("HOSTNAME")
            if self.rtr.isCPE():
                self.pe_guess = h
            else:
                self.hostname_guess = h
            log.debug("--> alternative hostname found in description: %s" % h)
        ## get all VT references
        m = re.findall(self.reDescrVtRef, text)
        if m:
            self.vt = m
            log.debug("--> found VT references in description: %s" % m)

    ## get all the VT references based on the PE objects
    def GetVTFromPEInterfaces(self):
        allvt = []
        # [ allvt.append(o.vt) for o in self.pe_intf_objects ]
        [allvt.append(vt) for o in self.pe_intf_objects for vt in o.vt]
        return allvt

    ## parse interface bandwidth
    def _parse_intf_bw(self, text):
        self.intfbw = text
        log.debug("--> bandwidth statement: %s" % self.intfbw)

    ## add PE interface object
    def add_pe_intf(self, obj):
        ## TODO: check for duplicates
        self.pe_intf_objects.append(obj)
        log.debug(
            "---> ADD PE data to CPE interface object: network=%s, PE=%s"
            % (self.network, obj.rtr.GetProp("hostname"))
        )
        ## update the hostname_guess value (just overwrite it every time a value is found)
        if obj.hostname_guess:
            log.debug(
                "---> OVERRIDE HOSTNAME_GUESS value: old=%s, new=%s"
                % (self.hostname_guess, obj.hostname_guess)
            )
            self.hostname_guess = obj.hostname_guess


## class to separate code for guessing the Mobistar Product based on IP address, description, hostname, etc
class Product(object):

    rfc1918 = ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"]

    def __init__(self):
        log.debug("new Product object")
        self.function = "NONE"  # MGMT/LAN/WAN/NNI/OTHER
        self.type = "NONE"  # P2P/LOOPBACK/IPSEC/IPSEC-MGMT/OTHER
        self.product = "NONE"  # IP-VPN/CI/IP-UPLINK/VOIPT
        self.transmission = "NONE"  # ATM/ETHERNET/VDSL/EXPLORE/3G/4G/INTERNET

    def UpdateProduct(self, key, value, reason):
        log.debug("update product info by %reason: %s = %s" % (reason, key, value))
        setattr(self, key, value)

    def ProductByInterface(self, intf):
        transmission = {
            "loopback": {"transmission": "VIRTUAL", "type": "LOOPBACK"},
            "dialer": {"transmission": "VIRTUAL", "type": "DIALER"},
            "atm": {"transmission": "ATM"},
            "cellular": {"transmission": "MOBILE", "type": "CELLULAR"},
            "ppp": {"transmission": "VDSL", "type": "PPP"},
            "ethernet": {"transmission": "ETHERNET"},
            "bundle-ether": {"transmission": "ETHERNET"},
            "tengigE": {"transmission": "ETHERNET"},
            "port-channel": {"transmission": "ETHERNET"},
            "bvi": {"transmission": "VIRTUAL", "type": "BVI"},
            "vlan": {"transmission": "VIRTUAL", "type": "VLAN"},
            "virtual-template": {"transmission": "VIRTUAL"},
            "tunnel": {"transmission": "GRE", "type": "TUNNEL", "function": "IPSEC"},
        }
        for t in transmission:
            m = re.search(t, intf, re.I)
            if m:
                for k in transmission[t]:
                    setattr(self, k, transmission[t][k])
                    log.debug(
                        "found by interface (%s): %s = %s"
                        % (intf, k, transmission[t][k])
                    )
                return
        log.error("Transmission was not found based on interface name: %s" % intf)

    ## guess the product based on the PE router interface
    # @staticmethod
    def ProductByPEIntf(self, pe, intf):
        pe_interfaces = {
            "ant-ipsec-01": {
                "gigabitethernet0\/1.*": {
                    "product": "DMVPN",
                    "type": "pe_p2p",
                    "function": "ipsec-internet",
                },
                "gigabitethernet0\/3.*": {
                    "product": "DMVPN",
                    "type": "pe_p2p",
                    "function": "ipsec-ipvpn",
                },
                "tunnel4[0-9][0-9][0-9][0-9].*": {},
            },
            "nos-ipsec-01": {
                "gigabitethernet0\/1.*": {
                    "product": "DMVPN",
                    "type": "pe_p2p",
                    "function": "ipsec-internet",
                },
                "gigabitethernet0\/3.*": {
                    "product": "DMVPN",
                    "type": "pe_p2p",
                    "function": "ipsec-ipvpn",
                },
                "tunnel4[0-9][0-9][0-9][0-9].*": {},
            },
            "ant-ipsec-02": {
                "gigabitethernet0\/1.*": {
                    "product": "DMVPN",
                    "type": "pe_p2p",
                    "function": "ipsec-internet",
                },
                "gigabitethernet0\/3.*": {
                    "product": "DMVPN",
                    "type": "pe_p2p",
                    "function": "ipsec-ipvpn",
                },
                "tunnel4[0-9][0-9][0-9][0-9].*": {},
            },
            "nos-ipsec-02": {
                "gigabitethernet0\/1.*": {
                    "product": "DMVPN",
                    "type": "pe_p2p",
                    "function": "ipsec-internet",
                },
                "gigabitethernet0\/3.*": {
                    "product": "DMVPN",
                    "type": "pe_p2p",
                    "function": "ipsec-ipvpn",
                },
                "tunnel4[0-9][0-9][0-9][0-9].*": {},
            },
            "ant-var-05": {
                "gigabitethernet3\/0\/7.*": {
                    "product": "DMVPN",
                    "type": "pe_p2p",
                    "function": "ipsec-ipvpn",
                },
            },
            "nos-var-05": {
                "gigabitethernet3\/0\/7.*": {
                    "product": "DMVPN",
                    "type": "pe_p2p",
                    "function": "ipsec-ipvpn",
                },
            },
            "ant-var-01": {
                "gigabitethernet3\/0\/19.*": {
                    "product": "DMVPN",
                    "type": "pe_p2p",
                    "function": "ipsec-internet",
                },
            },
            "nos-var-01": {
                "gigabitethernet3\/0\/19.*": {
                    "product": "DMVPN",
                    "type": "pe_p2p",
                    "function": "ipsec-internet",
                },
            },
            "nos-emlp-01": {
                "loopback5[0-9]{5}.*": {
                    "transmission": "VDSL",
                    "type": "p2p",
                    "function": "WAN",
                }
            },
            "ant-emlp-01": {
                "loopback5[0-9]{5}.*": {
                    "transmission": "VDSL",
                    "type": "p2p",
                    "function": "WAN",
                }
            },
        }

        ## make sure the PE is in lowercase
        pe = pe.lower()
        # intf = intf.partition(".")[0].lower()
        intf = intf.lower()

        if pe in pe_interfaces:
            for i in pe_interfaces[pe]:
                m = re.match(i, intf)
                if m:
                    for k in ["product", "function", "type", "transmission"]:
                        if k in pe_interfaces[pe][i]:
                            setattr(self, k, pe_interfaces[pe][i][k])
                            log.debug(
                                "found by PE interface (%s): %s = %s"
                                % (intf, k, pe_interfaces[pe][i][k])
                            )

        # if pe in pe_interfaces:
        #    if intf in pe_interfaces[pe]:
        #        log.debug("Product found based on PE + intf (%s, %s): %s" % (pe, intf, pe_interfaces[pe][intf]))
        #        return pe_interfaces[pe][intf]
        # log.debug("Product not found based on PE + interface (%s, %s)" % (pe, intf))

    ## guess the product based on IP address (ex. IPVPN, CI, IP UPLINK, ..)
    ## returns UNKNOWN if not found
    ## this function sets: function + product
    # @staticmethod
    def ProductByIp(self, ip):
        # initialize the IP address if it could not be found
        if not ip:
            ip = "0.0.0.0"

        ## TODO: check if correct/complete
        ##       move this to general config file
        ipranges = {
            "94.105.20.2/32": {
                "function": "IPSEC",
                "transmission": "MOBILE",
            },  ## for 4G IPSEC tunnels
            "94.105.25.2/32": {
                "function": "IPSEC",
                "transmission": "MOBILE",
            },  ## for 4G IPSEC tunnels
            "94.105.20.9/32": {
                "function": "IPSEC",
                "transmission": "MOBILE",
            },  ## for 4G IPSEC tunnels
            "94.105.25.9/32": {
                "function": "IPSEC",
                "transmission": "MOBILE",
            },  ## for 4G IPSEC tunnels
            "94.105.0.0/18": {"product": "IPVPN", "function": "MGMT"},
            "94.105.128.0/17": {"product": "IPVPN", "function": "WAN"},
            "94.106.0.0/16": {"product": "CI", "function": "LAN"},
            "94.107.0.0/17": {
                "product": "CI",
                "function": "LAN",
            },  ## corporate internet is split up because some ranges are used for other purposes
            "94.107.128.0/18": {"product": "CI", "function": "LAN"},
            "94.107.192.0/20": {"product": "CI", "function": "LAN"},
            "94.107.208.0/24": {"product": "CI", "function": "LAN"},
            "94.107.209.0/24": {"product": "CI", "function": "LAN"},
            "94.107.210.0/23": {
                "function": "WAN",
                "type": "CELLULAR",
                "transmission": "MOBILE",
            },  ## 4G Mobile ip
            "94.107.212.0/24": {"product": "CI", "function": "LAN"},
            "94.107.213.0/24": {"product": "CI", "function": "LAN"},
            "94.107.214.0/24": {"product": "CI", "function": "LAN"},
            "94.107.215.0/24": {"product": "CI", "function": "LAN"},
            "94.107.216.0/21": {"product": "CI", "function": "LAN"},
            "94.107.224.0/22": {"product": "CI", "function": "LAN"},
            "94.104.128.0/17": {"product": "CI", "function": "WAN"},
            "94.104.20.0/22": {"product": "IPVPN-UNMGD", "function": "WAN"},
            "1.107.0.0/16": {"product": "IPVPN", "function": "MGMT"},
            "1.108.0.0/16": {"product": "IPVPN", "function": "MGMT"},
            "1.7.0.0/16": {"product": "IPVPN", "function": "WAN"},
            "1.8.0.0/16": {"product": "IPVPN", "function": "WAN"},
            "94.104.18.0/23": {"product": "ISDN", "function": "WAN"},
            "134.222.220.0/24": {"product": "NNI-KPNI", "function": "NNI"},
            "134.222.217.0/24": {"product": "NNI-KPNI", "function": "NNI"},
            "192.0.0.0/16": {"product": "IPVPN", "function": "IPSEC"},
            "192.0.0.0/24": {"product": "IPVPN", "function": "IPSEC"},
            "192.2.0.0/24": {"product": "IPVPN", "function": "IPSEC"},
            "192.0.2.0/24": {"product": "IPVPN", "function": "IPSEC"},
            "192.2.2.0/24": {"product": "IPVPN", "function": "IPSEC"},
            "192.4.2.0/24": {
                "function": "IPSEC",
                "transmission": "MOBILE",
            },  ## TODO: only for tunnel interfaces
            "192.4.9.0/24": {
                "function": "IPSEC",
                "transmission": "MOBILE",
            },  ## TODO: only for tunnel interfaces
            "192.4.21.0/24": {
                "function": "IPSEC",
                "transmission": "MOBILE",
            },  ## TODO: only for tunnel interfaces
            "192.4.91.0/24": {
                "function": "IPSEC",
                "transmission": "MOBILE",
            },  ## TODO: only for tunnel interfaces
            "192.99.0.0/16": {"product": "MGMT", "function": "IPSEC"},
        }
        # ipobj = IPv4Network(ip)
        ipobj = ipaddress.ip_interface(ip)
        for i in ipranges:
            # if ipobj in IPv4Network(i):
            if ipobj.ip in ipaddress.ip_interface(i).network:
                for k in ["product", "function", "type", "transmission"]:
                    if k in ipranges[i]:
                        setattr(self, k, ipranges[i][k])
                        log.debug("found by ip (%s): %s = %s" % (ip, k, ipranges[i][k]))
                # self.product = ipranges[i]['product']
                # self.function = ipranges[i]['function']
                if self.function == "MGMT" and ipobj.network.prefixlen == 32:
                    self.type = "LOOPBACK"
                elif self.function == "WAN" and ipobj.network.prefixlen == 30:
                    self.type = "P2P"
                elif self.product == "CI" and ipobj.network.prefixlen == 32:
                    self.function = "MGMT"
                if not self.type == "NONE":
                    log.debug("found by ip (%s): %s = %s" % (ip, "type", self.type))
                # log.debug('product + function found based on ip "%s": %s - %s' % (ip, ipranges[i]['product'], ipranges[i]['function']))
                return
        ## nothing was found - see if it matches RFC1918 and then assign as LAN interface
        for i in self.rfc1918:
            # if ipobj in IPv4Network(i):
            if ipobj.ip in ipaddress.ip_interface(i).network:
                log.debug('Function found based on ip "%s": %s' % (ip, "LAN"))
                self.function = "LAN"
                return
        log.debug('Product could not be found based on ip "%s"' % ip)


## class to parse + hold VRF objects
class VRF(object):
    reVrf = re.compile("^ip vrf (?P<VRF>\S+)")
    reRtExport = re.compile(" route-target export (?P<RT>\S+)")
    reRtImport = re.compile(" route-target import (?P<RT>\S+)")
    reRd = re.compile(" rd (?P<RD>\S+)")
    reExportMap = re.compile(" export map (?P<MAP>\S+)")

    ## initialize object, conf=cli, p=parent router object
    def __init__(self, conf, p):
        self.vrf = ""
        self.rt_import = []
        self.rt_export = []
        self.export_map = ""
        self.rd = ""

        # parse the interface config
        self.parse(conf)

    ## main parser function
    def parse(self, vrfobj):
        m = self.reVrf.match(vrfobj.text)
        self._parse_vrf_name(m.group("VRF"))

        for l in vrfobj.children:
            # RT Export
            m = self.reRtExport.match(l.text)
            if m:
                self._parse_rtExport(m.group("RT"))
                continue
            # RT Import
            m = self.reRtImport.match(l.text)
            if m:
                self._parse_rtImport(m.group("RT"))
                continue
            # RD
            m = self.reRd.match(l.text)
            if m:
                self._parse_RD(m.group("RD"))
                continue
            # ExportMap
            m = self.reExportMap.match(l.text)
            if m:
                self._parse_ExportMap(m.group("MAP"))
                continue
            else:
                ## catch-all rule for debugging
                log.debug("XXX skip: %s" % l.text)

    ## parse the VRF name
    def _parse_vrf_name(self, vrf):
        log.debug("-> VRF found: %s" % vrf)
        self.vrf = vrf

    ## parse the RT Export
    def _parse_rtExport(self, rt):
        log.debug("--> EXPORT RT found: %s" % rt)
        self.rt_export.append(rt)

    ## parse the RT Import
    def _parse_rtImport(self, rt):
        log.debug("--> IMPORT RT found: %s" % rt)
        self.rt_import.append(rt)

    ## parse the RD
    def _parse_RD(self, rd):
        log.debug("--> RD found: %s" % rd)
        self.rd = rd

    ## parse the export map
    def _parse_ExportMap(self, map):
        log.debug("--> Export map found: %s" % map)
        self.export_map = map
