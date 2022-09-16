import json
import logging

"""
Base object for storing device info, this is to be used in the Models
"""


class _base(object):
    def __init__(self, **kwargs):
        ##
        self._id = None
        self.logger = logging.getLogger(__name__)

    def __str__(self):
        """
        Used to display the unique reference of a class (ex. hostname or interface id)
        Set _id to the variable that contains the unique reference
          ex. _id = 'hostname'
        """
        _str = self.__class__.__name__
        if self._id:
            _str = getattr(self, self._id, _str)
        return "{}".format(_str)

    def _init_list(self, val):
        """
        Initialize a list variable. If __init__(kwargs) is called then the KW is just a string
        but perhaps the class expects a list
        """
        if not val:
            return []
        if type(val) is list:
            return val
        else:
            return [val]

    def json(self, allownull=False):
        """
        Return a JSON representation of the class, if "allownull" is False then parameters without
        value are not displayed
        """

        def _is_class(o):
            """
            Checks if a variable is a Class object (Class)
            Returns True if it is
                    False if it's not
            """
            return True if hasattr(o, "__dict__") else False

        def _object_to_string(o):
            """if o is an object then return str(_o_) because JSON connect handle classes
            or else just return str(o)
            """
            if type(o) is list:
                o = ["#{}#".format(str(x)) if _is_class(x) else x for x in o]
            elif _is_class(o):
                o = "#{}#".format(str(o))
            return str(o)

        # j = { k: _object_to_string(self.__dict__[k]) for k in self.__dict__ if (allownull is True or self.__dict__[k] is not None or (type(self.__dict__[k]) is list and len(self.__dict__[k]) > 0)) }
        j = {
            k: _object_to_string(self.__dict__[k])
            for k in self.__dict__
            if (
                allownull is True
                or (
                    type(self.__dict__[k]) is not list
                    and self.__dict__[k] is not None
                )
                or (
                    type(self.__dict__[k]) is list
                    and len(self.__dict__[k]) > 0
                )
            )
        }
        return json.dumps(j, indent=4, separators=(",", ": "))

    def update_parameters(self, **kwargs):
        """
        This function updates the parameters of an object. All key,value pairs passed via kwargs
        will be set in the object if the key exists otherwise it will be ignored.

        If the key is a list then the value will be appended
        """
        for name, value in kwargs.items():
            if name in self.__dict__:
                if type(self.__dict__[name]) is list:
                    self.__dict__[name].append(value)
                else:
                    self.__dict__[name] = value


"""
Class to store generic host info
"""


class _host(_base):
    def __init__(self, **kwargs):
        super(_host, self).__init__(**kwargs)
        self._id = "hostname"
        self.hostname = kwargs.get("hostname", None)
        self.mgmtIp = kwargs.get("mgmtIp", None)
        self.gateway = kwargs.get("gateway", None)
        self.chassisid = kwargs.get("chassisid", None)


"""
Class to store system info (related to the device itself)
"""


class _system(_base):
    def __init__(self, **kwargs):
        super(_system, self).__init__(**kwargs)
        self.vendor = kwargs.get("vendor", None)
        self.hwtype = kwargs.get("hwtype", None)
        self.software = kwargs.get("software", None)
        self.os = kwargs.get("OS", None)


"""
Class to store the info of an LLDP neighbor device
"""


class _lldpneighbor(_base):
    def __init__(self, **kwargs):
        super(_lldpneighbor, self).__init__(**kwargs)
        self.nbrPort = kwargs.get("nbrPort", None)  # port of the neighbor
        self.nbr = kwargs.get("nbr", None)  # id or reference of the neighbor
        self.localPort = kwargs.get("localPort", None)  # local port


"""
Class to store ring info
"""


class _ring(_base):
    def __init__(self, **kwargs):
        super(_ring, self).__init__(**kwargs)
        self._id = "name"
        self.name = kwargs.get("name", None)  # ring name
        self.ringstatus = kwargs.get(
            "ringstatus", None
        )  # ring status: open or closed


"""
Class to store logical ring info
"""


class _logicalring(_ring):
    def __init__(self, **kwargs):
        super(_logicalring, self).__init__(**kwargs)
        self.id = kwargs.get("id", None)  # ring id
        self.type = "logical-ring"
        self.westport = kwargs.get("westport", None)
        self.eastport = kwargs.get("eastport", None)
        self.ringmembers = self._init_list(
            kwargs.get("ringmembers")
        )  # list of all neighbors in the ring
        self.virtualrings = self._init_list(
            kwargs.get("virtualrings")
        )  # link to all virtual rings connected to this ring
        # self.ringmembers = kwargs.get('ringmembers', [])  # list of all neighbors in the ring
        # self.virtualrings = kwargs.get('virtualrings', [])  # list of all virtual rings connected to this ring


"""
Class to store virtual ring info
"""


class _virtualring(_ring):
    def __init__(self, **kwargs):
        super(_virtualring, self).__init__(**kwargs)
        self.type = "virtual-ring"
        self.logicalring = kwargs.get(
            "logicalring", None
        )  # name of logical ring this ring belongs to
        self.rapsvid = kwargs.get("rapsvid", None)
        self.subring = kwargs.get(
            "subring", None
        )  ## this contains east-port-termination, west-port-termination, no-port-termination
        self._eastport_termination = self._init_list(
            kwargs.get("_eastport_termination")
        )  ## generated - will contain all hostnames in the vring that have subring east-port-termination configured
        self._westport_termination = self._init_list(
            kwargs.get("_westport_termination")
        )  ## generated - will contain all hostnames in the vring that have subring west-port-termination configured
        # self.eastportrpl = kwargs.get('eastportrpl', None)
        self.rplownerport = self._init_list(kwargs.get("rplownerport"))
        self.rplowner = self._init_list(
            kwargs.get("rplowner")
        )  # hostname that has an rplownerport
        self.vlans = self._init_list(
            kwargs.get("vlans")
        )  ## link to the S-vlans assigned to this VR
        self.vswitches = self._init_list(
            kwargs.get("vswitches")
        )  ## link to the vswitches assigned to this VR
        # self.vlans = kwargs.get('vlans', [])
        # self.vswitches = kwargs.get('vswitches', [])


"""
Class to store general L2 port info  (L2 interfaces)
"""


class _port(_base):
    def __init__(self, **kwargs):
        super(_port, self).__init__(**kwargs)
        self._id = "name"
        self.name = kwargs.get("name", None)  ## ex FastEthernet0/1
        self.maxframe = kwargs.get("maxframe", None)  ## max frame size
        self.mtu = kwargs.get("mtu", None)  ## max frame size
        self.rstp = kwargs.get("rstp", None)  ## RSTP enabled or disabled
        self.mstp = kwargs.get("mstp", None)  ## MSTP enabled or disabled
        self.type = kwargs.get("type", "L2 generic port")  ## port type
        self.lldp = kwargs.get("lldp", None)  ## LLDP enabled or disabled
        self.lldpnbr = kwargs.get("lldpnbr", None)  ## LLDP neighbor
        self._vlans = self._init_list(
            kwargs.get("_vlans")
        )  ## links to vlans assigned to this port
        self.description = kwargs.get("description", None)  ## ex 0/1, 1
        self.operstate = kwargs.get(
            "operstate", None
        )  ## enabled|disabled|Up|Down
        self.adminstate = kwargs.get(
            "adminstate", None
        )  ## enabled|disabled|Up|Down
        self.qosmapin = kwargs.get(
            "qosmapin", None
        )  ## name of inbound QOS map
        self.qosmapout = kwargs.get(
            "qosmapout", None
        )  ## name of inbound QOS map
        self.stormcontrol = kwargs.get("stormcontrol", None)
        self.broadcastlimit = kwargs.get("broadcastlimit", None)
        self.multicastlimit = kwargs.get("multicastlimit", None)
        self.stp = kwargs.get("stp", None)  ## STP enabled or disabled
        self.defaultvlanid = kwargs.get(
            "defaultvlanid", None
        )  ## default vlan id this port has
        self.linkstateduration = kwargs.get(
            "linkstateduration", None
        )  ## 3d13h21m
        self.speedcapability = kwargs.get("speedcapability", None)  ## 10/100/G
        self.adminspeedduplex = kwargs.get(
            "adminspeedduplex", None
        )  ## 100FD, 10HD, ..
        self.operspeedduplex = kwargs.get(
            "operspeedduplex", None
        )  ## 100FD, 10HD, ..


"""
Class to store switch port info  (L2 interfaces)
"""


class _switchport(_port):
    def __init__(self, **kwargs):
        super(_switchport, self).__init__(**kwargs)
        # self._id = 'portidx'
        self.type = kwargs.get(
            "type", "L2 switchport"
        )  ## MSTP enabled or disabled
        self.portidx = kwargs.get("portidx", None)  ## ex 0/1, 1
        self.xsvrstatus = kwargs.get("xsvrstatus", None)  ## Ena or Dis
        self.autoneg = kwargs.get("autoneg", None)  ## on|off
        self.untaggedframesdiscard = kwargs.get("untaggedframesdiscard", None)
        self.tdp = kwargs.get("tdp", None)
        self.vplsporttype = kwargs.get(
            "vplsporttype", None
        )  ## Subsc = UNI or Ntwrk = NNI
        self.ethvcethertype = kwargs.get(
            "ethvcethertype", None
        )  ## usually 8100 on SDS
        self.egressshaper = kwargs.get(
            "egressshaper", None
        )  ## ex. shaper-rate 10000
        self.egressqueue = kwargs.get(
            "egressqueue", None
        )  ## ex. weighted-deficit-round-robin


"""
Class to store lagg port info (bundle of L2 ports)
"""


class _lagport(_port):
    def __init__(self, **kwargs):
        super(_lagport, self).__init__(**kwargs)
        self.type = kwargs.get(
            "type", "L2 lag port"
        )  ## MSTP enabled or disabled
        self.ports = self._init_list(kwargs.get("ports"))
        # self.ports = kwargs.get('ports', [])


"""
Class to store generic interface information  (L3 IP interfaces)
"""


class _interface(_base):
    def __init__(self, **kwargs):
        super(_interface, self).__init__(**kwargs)
        self._id = "name"
        self.name = kwargs.get("name", None)
        self.ip = kwargs.get("ip", None)


"""
Class to store a loopback interface
"""


class _interface_loopback(_interface):
    def __init__(self, **kwargs):
        super(_interface_loopback, self).__init__(**kwargs)
        self.type = "loopback"


"""
Class to store an ip interface
"""


class _interface_ip(_interface):
    def __init__(self, **kwargs):
        super(_interface_ip, self).__init__(**kwargs)
        self.type = "ip-interface"
        self.mask = kwargs.get("mask", None)
        self.mtu = kwargs.get("mtu", None)
        self.forwarding = kwargs.get("forwarding", None)
        self.vlan = kwargs.get("vlan", None)


"""
Class to store an ip "remote" interface
"""


class _interface_remote(_interface):
    def __init__(self, **kwargs):
        super(_interface_remote, self).__init__(**kwargs)
        self.type = "remote"
        self.description = "inband management"
        self.mask = kwargs.get("mask", None)
        self.vlan = kwargs.get("vlan", None)


"""
Class to store an ip "local" interface
"""


class _interface_local(_interface):
    def __init__(self, **kwargs):
        super(_interface_local, self).__init__(**kwargs)
        self.type = "local"
        self.description = "outband management"
        self.mask = kwargs.get("mask", None)


"""
Class to store an L3 SVI (vlan)
"""


class _svi(_base):
    def __init__(self, **kwargs):
        super(_svi, self).__init__(**kwargs)
        self._id = "vlan"
        self.vlan = kwargs.get("vlan", None)


"""
Class to store an L2 vlan
"""


class _vlan(_base):
    def __init__(self, **kwargs):
        super(_vlan, self).__init__(**kwargs)
        self._id = "vlan"
        self.vlan = kwargs.get("vlan", None)
        self.name = kwargs.get("name", None)
        self.description = kwargs.get("description", None)
        self.ports = self._init_list(
            kwargs.get("ports")
        )  # link to ports that have this vlan assigned
        self.type = self._init_list(
            kwargs.get("type")
        )  # ex. reserved-vlan, virtual-circuit, SVLAN, CVLAN
        # self.ports = kwargs.get('ports', [])
        # self.type = kwargs.get('type', [])  # ex. reserved-vlan, virtual-circuit, SVLAN, CVLAN
        self._vswitches = self._init_list(
            kwargs.get("_vswitches")
        )  ## links to the vswitches that have this vlan
        self._virtualrings = self._init_list(
            kwargs.get("_virtualrings")
        )  ## links to the vswitches that have this vlan


"""
Class to store services (VT... or GSID....)
"""


class _service(_base):
    def __init__(self, **kwargs):
        super(_service, self).__init__(**kwargs)
        self._id = "serviceid"
        self.serviceid = kwargs.get(
            "serviceid", None
        )  # this could be a L2 service id (VT or something else) or a customer facing service id (= VT), normally the vswitch name
        self.description = kwargs.get("description", None)
        self.vcircuit = kwargs.get("vcircuit", None)  ## will be link to s-vlan
        # when the service is linked, a vswitch parameter is added
        self.vswitch = kwargs.get("vswitch", None)


"""
Class store an object that represents a vlan but is actually not configured on the box
as it's just defined via tagging.
"""


class _tagged_vlan(_vlan):
    def __init__(self, **kwargs):
        super(_tagged_vlan, self).__init__(**kwargs)
        self.type = self._init_list(kwargs.get("type")) + [
            "TAGGED_VLAN"
        ]  # ex. reserved-vlan, virtual-circuit, SVLAN, CVLAN


"""
Class to store an virtual circuit
"""


class _vcircuit(_base):
    def __init__(self, **kwargs):
        super(_vcircuit, self).__init__(**kwargs)
        self._id = "name"
        self.name = kwargs.get("name", None)
        self.vlan = kwargs.get("vlan", None)  ## will be link to s-vlan
        self.statistics = kwargs.get("statistics", None)
        self._vswitches = kwargs.get(
            "_vswitches", []
        )  ## link to all the virtual switches assigned


"""
Class to store a subport, similar as a vcircuit but used for SAOS 8700 for example
"""


class _subport(_base):
    def __init__(self, **kwargs):
        super(_subport, self).__init__(**kwargs)
        self._id = "name"
        self.name = kwargs.get("name", None)
        # self.type = kwargs.get('type', None)
        self.parentport = kwargs.get("parentport", None)  ## link to the port
        self.classifierprecedence = kwargs.get("classifierprecedence", None)
        self.ingressl2transform = kwargs.get("ingressl2transform", None)
        self.egressl2transform = kwargs.get("egressl2transform", None)
        self.resolvedqospolicy = kwargs.get("resolvedqospolicy", None)
        self.resolvedqosprofile = kwargs.get("resolvedqosprofile", None)
        self.classelement = kwargs.get("classelement", None)
        self.vtags = self._init_list(kwargs.get("vtags"))  ## link to s-vlans
        # self.vtags = kwargs.get('vtags', [])


"""
Class to store an virtual switch
"""


class _vswitch(_base):
    def __init__(self, **kwargs):
        super(_vswitch, self).__init__(**kwargs)
        self._id = "name"
        self.name = kwargs.get("name", None)
        self.reservedvlan = kwargs.get("reservedvlan", None)
        self.vcircuit = kwargs.get("vcircuit", None)  ## link to the vcircuit
        self.description = kwargs.get("description", None)
        self.port = kwargs.get("port", None)  ## link to the port
        self.vlan = kwargs.get("vlan", None)  ## link to the C(?)-vlan
        self.datatagging = kwargs.get("datatagging", None)
        self.encapcospolicy = self._init_list(kwargs.get("encapcospolicy"))
        self.virtualinterfaces = kwargs.get(
            "virtualinterfaces", []
        )  ## this is for SAOS 87xx
        self.serviceid = kwargs.get(
            "serviceid", None
        )  # service id's found in the vswitch description (VT or GSID)
        # self.virtualinterfaces = kwargs.get('virtualinterfaces', [])


"""
Class to store NTP information
"""


class _ntpserver(_base):
    def __init__(self, **kwargs):
        super(_ntpserver, self).__init__(**kwargs)
        self._id = "ip"
        self.ip = kwargs.get("ip", None)
        self.name = kwargs.get("name", None)


"""
Class to store nameserver information
"""


class _nameserver(_base):
    def __init__(self, **kwargs):
        super(_nameserver, self).__init__(**kwargs)
        self._id = "ip"
        self.ip = kwargs.get("ip", None)
        self.name = kwargs.get("name", None)


"""
Class to store syslog server information
"""


class _syslogserver(_base):
    def __init__(self, **kwargs):
        super(_syslogserver, self).__init__(**kwargs)
        self._id = "ip"
        self.ip = kwargs.get("ip", None)
        self.name = kwargs.get("name", None)
        self.severity = kwargs.get("severity", None)
        self.local = kwargs.get("local", None)


"""
Class to store systemwide tacacs information
"""


class _tacacs(_base):
    def __init__(self, **kwargs):
        super(_tacacs, self).__init__(**kwargs)
        self.servers = self._init_list(kwargs.get("servers"))
        # self.servers = kwargs.get('servers', [])
        self.secret = kwargs.get("secret", None)
        self.authorization = kwargs.get(
            "authorization", None
        )  # authorization is enabled or disabled
        self.accounting = kwargs.get(
            "accounting", None
        )  # accounting is enabled or disabled
        self.accounting_session = kwargs.get(
            "accounting_session", None
        )  # accounting is enabled or disabled
        self.accounting_command = kwargs.get(
            "accounting_command", None
        )  # accounting is enabled or disabled


"""
Class to store tacacs server information
"""


class _tacacsserver(_base):
    def __init__(self, **kwargs):
        super(_tacacsserver, self).__init__(**kwargs)
        self._id = "name"
        self.ip = kwargs.get("ip", None)
        self.name = kwargs.get("name", None)
        self.tcpport = kwargs.get("tcpport", None)
        self.secret = kwargs.get("secret", None)
