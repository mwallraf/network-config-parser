import json
from nmsnetlib.models.netobjects.netobjects import _host, _system, _tacacs
import datetime
import re
import logging

UNKNOWN = "-unknown-"

class BaseModel(object):
    """
    Base model class
    """
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        self.host = _host()
        self.system = _system()
        self.tacacs = _tacacs()
        self.interfaces = []  ## L3 interfaces
        self.ntpservers = []
        self.nameservers = []
        self.syslogservers = []
        self.switchports = []   ## L2 interfaces
        self.vlans = []
        self.tacacsservers = []
        self.vcircuits = []  ## = sub_ports on SAOS
        self.vswitches = []
        self.subports = []
        self.cpuinterfaces = []
        self.lldpneighbors = []
        self.rings = []
        self.services = []
        ## firstseen and lastseen 
        self.firstseen = None    # datetime object when the config was first seen
        self.lastseen = None     # datetime object when the config was last seen

    def __str__(self):
        return "{} <{}>".format(self.__class__.__name__, self.host.hostname)

    def _is_class(self, o):
        """
        Checks if a variable is a Class object (Class)
        Returns True if it is
                False if it's not
        """
        return True if hasattr(o, '__dict__') else False

    def json(self, allownull=False):
        j = {
            "host": json.loads(self.host.json(allownull)),
            "system": json.loads(self.system.json(allownull)),
            "tacacs": json.loads(self.tacacs.json(allownull)),
            "tacacsservers": [ json.loads(i.json(allownull)) for i in self.tacacsservers ],
            "interfaces": [ json.loads(i.json(allownull)) for i in self.interfaces ],
            "ntpservers": [ json.loads(i.json(allownull)) for i in self.ntpservers ],
            "nameservers": [ json.loads(i.json(allownull)) for i in self.nameservers ],
            "syslogservers": [ json.loads(i.json(allownull)) for i in self.syslogservers ],
            "switchports": [ json.loads(i.json(allownull)) for i in self.switchports ],
            "vlans": [ json.loads(i.json(allownull)) for i in self.vlans ],
            "vcircuits": [ json.loads(i.json(allownull)) for i in self.vcircuits ],
            "vswitches": [ json.loads(i.json(allownull)) for i in self.vswitches ],
            "subports": [ json.loads(i.json(allownull)) for i in self.subports ],
            "cpuinterfaces": [ json.loads(i.json(allownull)) for i in self.cpuinterfaces ],
            "lldpneighbors": [ json.loads(i.json(allownull)) for i in self.lldpneighbors ],
            "rings": [ json.loads(i.json(allownull)) for i in self.rings ],
            "services": [ json.loads(i.json(allownull)) for i in self.services ],
        }
        return json.dumps(j, indent=4, separators=(',', ': '))


    def get_management_ip(self):
        """
            Returns the management IP address
        """
        pass

    def virtual_rings(self):
        """
            Returns all virtual rings
        """
        return [ x for x in self.rings if x.type == 'virtual-ring' ]

    def logical_rings(self):
        """
            Returns all logical rings
        """
        return [ x for x in self.rings if x.type == 'logical-ring' ]

    def virtual_interfaces(self):
        """
            Returns a combination of all virtual interfaces.
            For SAOS vswitch: subports + cpuinterfaces
        """
        return self.subports + self.cpuinterfaces

    def update_datetime_from_epoch(self, **kwargs):
        """
           Sets the model parameter (ex. firstseen)
           kw = { "firstseen": 1501637092 }
        """
        for (k, v) in kwargs.items():
            if k in self.__dict__:
                try:
                    self.__dict__[k] = datetime.datetime.fromtimestamp(int(v))
                except:
                    self.__dict__[k] = v

    def get_last_config_date(self, indays=False):
        """
            Returns the last config date (lastseen)
            if indays = True:  returns the age of the config in number of days
            else: returns the timestamp as found in lastseen

        """
        if indays:
            if not 'datetime' in str(type(self.lastseen)):
                return None
            today = datetime.datetime.now()
            delta = today - self.lastseen
            return delta.days
        return self.lastseen

    def get_netjson_lldp(self):
        """
            Returns a netjson representation of nodes and links based on LLDP.
            As nodename we use the chassis-id
            {
                "nodes": [ { "id": "00387-SDS39-002","properties": { "Management IP": "10.8.91.98" } },
                        ],
                "links": [ { "source": "", "target": "", "properties": {} }
                        ]
            }
        """
        nodes = []
        links = []
        self_chassis_id = self.host.chassisid
        self_hostname = self.host.hostname
        nodes.append({ 'id': self_chassis_id, 'properties': { 'hostname': self_hostname } })
        for neighbor in self.lldpneighbors:
            nbr = neighbor.nbr
            if self._is_class(nbr):
                nbr_chassis_id = nbr.model.host.chassisid
                nbr_hostname = nbr.model.host.hostname or nbr.model.host.chassisid
                #print("{}: {}".format(nbr_chassis_id, nbr_hostname))
            else:
                nbr_chassis_id = nbr
                nbr_hostname = UNKNOWN
            ## add neighbor to the nodes list if it doesn't exist yet
            n = next(iter(list(filter(lambda x: str(x['id']) == str(nbr_chassis_id), nodes))), None)
            if not n:
                nodes.append({ 'id': nbr_chassis_id, 'properties': { 'hostname': nbr_hostname } })
            ## add the new link if it doesn't exist yet
            (aside, bside) = (self_chassis_id, nbr_chassis_id) if (self_chassis_id < nbr_chassis_id) else (nbr_chassis_id, self_chassis_id)
            n = next(iter(list(filter(lambda x: "{}-{}".format(x['source'], x['target']) == "{}-{}".format(aside, bside), links))), None)
            if not n:
                links.append({ 'source': aside, 'target': bside, 'properties': { 'linksource': 'lldp' }})
        j = { 'nodes': nodes, 'links': links }
        return json.dumps(j, indent=4, separators=(',', ': '))


    ### TODO: TO BE REMOVED ###
    def get_switchport_status(self):
        """
            Returns a list of interfaces and the configured + operational status
            {
                "hostname": "",
                "ports': [
                    { 'port': '', 'rstp': '', 'mstp': '', 'lldp': '', 'lldpnbr': '',
                      'descr': '', 'operstate': '', 'adminstate': '', 'adminspeedduplex': '', 
                      'operspeedduplex': '', 'linkstateduration': '', 'xsvrstatus': '',
                      'autoneg': '', 'stormcontrol': '', 'mtu': '', 'vlans': [], 'egress-policy': ''
                    }
                ]
            }
        """
        hostname = self.host.hostname or self.host.chassisid or UNKNOWN

        #for p in [ x for x in self.switchports ]:
        #    ports.append(json.loads(p.json()))

        #ports = [ json.loads(i.json(False)) for i in self.switchports ]
        ports = self.switchports

        #for p in [ x for x in self.switchports if x.type != "L2 lag port" ]:
        #    port = { 'port': str(p.name), 'type': str(p.type), 'rstp': str(p.rstp), 'mstp': str(p.mstp), 'lldp': str(p.lldp), 'lldpnbr': str(p.lldpnbr),
        #             'descr': str(p.description), 'operstate': str(p.operstate), 'adminstate': str(p.adminstate), 
        #             'adminspeedduplex': str(p.adminspeedduplex), 'operspeedduplex': str(p.operspeedduplex),
        #             'linkstateduration': str(p.linkstateduration), 'xsvrstatus': str(p.xsvrstatus), 
        #             'autoneg': str(p.autoneg), 'stormcontrol': str(p.stormcontrol), 'lag_ports': str([]), 'mtu': str(p.mtu), 'vlans': str(p._vlans)
        #           }
        #    ports.append(port)

        #for p in [ x for x in self.switchports if x.type == "L2 lag port" ]:
        #    port = { 'port': str(p.name), 'type': str(p.type), 'rstp': str(p.rstp), 'mstp': str(p.mstp), 'lldp': str(p.lldp), 'lldpnbr': str(p.lldpnbr),
        #             'descr': str(p.description), 'operstate': str(p.operstate), 'adminstate': str(p.adminstate), 
        #             'adminspeedduplex': str(""), 'operspeedduplex': str(""),
        #             'linkstateduration': str(p.linkstateduration), 'xsvrstatus': str(""), 
        #             'autoneg': str(""), 'stormcontrol': str(p.stormcontrol), 'lag_ports': str(p.ports), 'mtu': str(p.mtu), 'vlans': str(p._vlans)
        #           }
        #    ports.append(port)
        #print(ports)
        j = { "hostname": hostname, "ports": ports }
        #return json.dumps(j, indent=4, separators=(',', ': '))
        return j
