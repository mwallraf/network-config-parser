import re

## Ciena SAOS definition
definition = {
            'SYSTEM CONFIG:': {
                    'regex': [ 
                        { 'mapper': 'HOST', 're': re.compile("system set host-name (?P<hostname>.*)") }
                    ],
            },
            'IP INTERFACE CONFIG:': {
                    'regex': [
                        { 'mapper': 'LOOPBACKINTERFACE', 're': re.compile("interface create loopback (?P<name>[^ ]+) ip (?P<ip>.*)") },
                        { 'mapper': 'IPINTERFACE', 're': re.compile("interface create ip-interface (?P<name>[^ ]+) ip (?P<ip>[^/]+)/(?P<mask>[^/]+) mtu (?P<mtu>[0-9]+) ip-forwarding (?P<forwarding>[^ ]+) vlan (?P<vlan>[0-9]+)") }
                    ],
            },
            'INTERFACE CONFIG:': {
                    'regex': [ 
                        { 'mapper': 'REMOTEINTERFACE', 're': re.compile("interface (?P<name>remote) set vlan (?P<vlan>[0-9]+)") },
                        { 'mapper': 'REMOTEINTERFACE', 're': re.compile("interface (?P<name>remote) set ip (?P<ip>[^/]+)/(?P<mask>[0-9]+)") },
                        { 'mapper': 'LOCALINTERFACE', 're': re.compile("interface set interface active ip (?P<ip>[^/]+)/(?P<mask>[0-9]+)") }
                    ],
            },
            'INTERFACE LOCAL CONFIG:': {
                    'regex': [ 
                        { 'mapper': 'LOCALINTERFACE', 're': re.compile("interface (?P<name>local) set ip (?P<ip>[^/]+)/(?P<mask>[0-9]+)") }
                    ],
            },
            ## for none-8700 SAOS
            'NTP CONFIG:': {
                    'regex': [ 
                        { 'mapper': 'NTPSERVER', 're': re.compile("ntp client add server (?P<ip>.+)") }
                    ],
            },
            ## for 8700 SAOS
            'NTP CLIENT CONFIG:': {
                    'regex': [ 
                        { 'mapper': 'NTPSERVER', 're': re.compile("ntp client add server (?P<ip>.+)") }
                    ],
            },
            'DNS CLIENT CONFIG:': {
                    'regex': [ 
                        { 'mapper': 'NAMESERVER', 're': re.compile("dns[- ]client add server (?P<ip>.+)") }
                    ],
            },
            'SYSLOG CONFIG:': {
                    'regex': [ 
                        { 'mapper': 'SYSLOGSERVER', 're': re.compile("syslog create collector (?P<ip>[^ ]+) severity (?P<severity>.*)") }
                    ],
            },
            'TACACS CONFIG:': {
                    'regex': [
                        { 'mapper': 'TACACS', 're': re.compile("tacacs add server (?P<servers>[^ ]+) tcp-port 4949") },
                        { 'mapper': 'TACACS', 're': re.compile("tacacs set secret (?P<secret>.*)") },
                        { 'mapper': 'TACACS', 're': re.compile("tacacs authorization (?P<authorization>[^ ]+)$") },
                        { 'mapper': 'TACACS', 're': re.compile("tacacs accounting (?P<accounting>[^ ]+)$") },
                        { 'mapper': 'TACACS', 're': re.compile("tacacs accounting set command (?P<accounting_command>.*)") },
                        { 'mapper': 'TACACS', 're': re.compile("tacacs accounting set session (?P<accounting_session>.*)") },
                        { 'mapper': 'TACACSSERVER', 're': re.compile("tacacs add server (?P<name>[^ ]+) tcp-port (?P<tcpport>[0-9]+)") }
                    ],
            },
            'PORT CONFIG:': {
            # match a port 4 or 4/6 by:  (?P<name>[0-9]+(?:\/[0-9]+)?)
                    'regex': [ 
                        { 'mapper': 'SWITCHPORT', 're': re.compile("port set port (?P<name>[^ ]+) description (?P<description>.*)") },
                        { 'mapper': 'SWITCHPORT', 're': re.compile("port (?P<adminstate>disable) port (?P<name>.+)") },
                        { 'mapper': 'SWITCHPORT', 're': re.compile("port set port (?P<name>[^ ]+) (?:speed (?P<adminspeedduplex>[^ ]+) )?auto-neg (?P<autoneg>on|off)") },     
                        { 'mapper': 'SWITCHPORT', 're': re.compile("port set port (?P<name>[^ ]+) max-frame-size (?P<maxframe>[0-9]+)(?: (ingress-to-egress-qmap|ingress-flood-container) (?P<qosmapin>.+))?") },     
                        { 'mapper': 'LAGPORT', 're': re.compile("aggregation create agg (?P<name>.+)") },     
                    ],
            },            
            'PORT CONFIG: ports': {
            # after SAOS upgrade the PORT CONFIG: section was renamged to PORT config: ports
            # match a port 4 or 4/6 by:  (?P<name>[0-9]+(?:\/[0-9]+)?)
                    'regex': [ 
                        { 'mapper': 'SWITCHPORT', 're': re.compile("port set port (?P<name>[^ ]+) description (?P<description>.*)") },
                        { 'mapper': 'SWITCHPORT', 're': re.compile("port (?P<adminstate>disable) port (?P<name>.+)") },
                        { 'mapper': 'SWITCHPORT', 're': re.compile("port set port (?P<name>[^ ]+) (?:speed (?P<adminspeedduplex>[^ ]+) )?auto-neg (?P<autoneg>on|off)") },     
                        { 'mapper': 'SWITCHPORT', 're': re.compile("port set port (?P<name>[^ ]+) max-frame-size (?P<maxframe>[0-9]+)(?: (ingress-to-egress-qmap|ingress-flood-container) (?P<qosmapin>.+))?") },     
                        { 'mapper': 'LAGPORT', 're': re.compile("aggregation create agg (?P<name>.+)") },     
                    ],
            },            
            'RSTP CONFIG:': {
                    'regex': [ 
                        { 'mapper': 'SWITCHPORT', 're': re.compile("rstp (?P<rstp>disable) port (?P<name>.+)") }
                    ],
            },            
            'MSTP CONFIG:': {
                    'regex': [ 
                        { 'mapper': 'SWITCHPORT', 're': re.compile("mstp (?P<mstp>disable) port (?P<name>.+)") }
                    ],
            },
            'NETWORK CONFIG:  vlans': {
                    'regex': [ 
                        { 'mapper': 'VLAN', 're': re.compile("vlan create vlan (?P<vlan>[0-9]+)") },
                    ],
                    'preprocessor': {
                        'regex': [
                            re.compile("vlan create vlan (?P<MIXRANGE>.*)"),
                        ]
                    }
            },            
            'VIRTUAL-CIRCUIT CONFIG:  virtual circuits': {
                    'regex': [ 
                        { 'mapper': 'VCIRCUIT', 're': re.compile("virtual-circuit ethernet create vc (?P<name>[^ ]+) vlan (?P<vlan>[0-9]+) statistics (?P<statistics>[^ ]+)") }
                    ],
            },
            ## for none-8700 SAOS
            'VIRTUAL-SWITCH CONFIG:': {
                    'regex': [ 
                        { 'mapper': 'VLAN_PORT', 're': re.compile("virtual-switch add (?P<type>[^ ]+) (?P<vlan>[0-9]+)") },
                        { 'mapper': 'VSWITCH', 're': re.compile("virtual-switch ethernet create vs (?P<name>[^ ]+) vc (?P<vcircuit>[^ ]+) description (?P<description>.*)") },                        
                        { 'mapper': 'VSWITCH', 're': re.compile("virtual-switch ethernet create vs (?P<name>[^ ]+) .*description (?P<serviceid>(GSID|VT)\d+)") },                        
                        { 'mapper': 'VSWITCH', 're': re.compile("virtual-switch ethernet create vs (?P<name>[^ ]+) reserved-vlan (?P<reservedvlan>[0-9]+)(?: encap-fixed-dot1dpri 0)? vc (?P<vcircuit>[^ ]+) description (?P<description>.*)") },                        
                        { 'mapper': 'VSWITCH', 're': re.compile("virtual-switch ethernet add vs (?P<name>[^ ]+) port (?P<port>[^ ]+)(?: vlan (?P<vlan>[0-9]+))?(?: encap-cos-policy (?P<encapcospolicy>.*))?") },
                        { 'mapper': 'VLAN', 're': re.compile("virtual-switch ethernet add vs (?P<name>[^ ]+) port (?P<ports>[^ ]+) vlan (?P<vlan>[0-9]+).*") },
                        { 'mapper': 'VSWITCH', 're': re.compile("port set port 1 (?P<datatagging>untagged-data-vs) (?P<name>[^ ]+) .*") },
                        { 'mapper': 'SERVICE', 're': re.compile("virtual-switch ethernet create vs (?P<serviceid>[^ ]+) .* description (?P<description>.*)") },                        
                    ],
                    'preprocessor': {
                        'regex': [
                            re.compile("virtual-switch add reserved-vlan (?P<MIXRANGE>.*)"),
                        ]
                    }
            },
            ## for 8700 SAOS
            'VIRTUAL SWITCH CONFIG:': {
                    'regex': [ 
                        { 'mapper': 'VSWITCH', 're': re.compile("virtual-switch create vs (?P<name>[^ ]+)") },
                        { 'mapper': 'VSWITCH', 're': re.compile("virtual-switch set vs (?P<name>[^ ]+) description \"?(?P<description>[^\"]*)") },
                    ],
            },
            'NETWORK CONFIG:  vlan members and attributes': {
                    'regex': [ 
                        { 'mapper': 'VLAN_PORT', 're': re.compile("vlan add vlan (?P<vlan>[0-9]+) port (?P<ports>.+)") },
                        { 'mapper': 'VLAN_PORT', 're': re.compile("vlan rename vlan (?P<vlan>[0-9]+) name (?P<name>.+)") }
                    ],
                    'preprocessor': {
                        'regex': [
                            re.compile("vlan add vlan (?P<MIXRANGE>[^ ]+) port .+"),
                        ]
                    }
            },
            'LLDP CONFIG:': {
                    'regex': [ 
                        { 'mapper': 'SWITCHPORT', 're': re.compile("lldp *set port (?P<name>[^ ]+) notification (?P<lldp>.*)") }
                    ],
                    'preprocessor': {
                        'regex': [
                            re.compile("lldp *set port (?P<MIXRANGE>[^ ]+) notification .*"),
                        ]
                    }
            },
            'SUB-PORT CONFIG:': {
                    'regex': [ 
                        { 'mapper': 'SUBPORT', 're': re.compile("sub-port create sub-port (?P<name>[^ ]+) parent-port (?P<parentport>[^ ]+)(?: classifier-precedence (?P<classifierprecedence>[^ ]+))(?: ingress-l2-transform (?P<ingressl2transform>[^ ]+))?(?: egress-l2-transform (?P<egressl2transform>[^ ]+))?(?: resolved-cos-policy (?P<resolvedqospolicy>[^ ]+))?(?: resolved-cos-profile (?P<resolvedqosprofile>[^ ]+))?") },
                        { 'mapper': 'SUBPORT', 're': re.compile("sub-port add sub-port (?P<name>[^ ]+) class-element (?P<classelement>[^ ]+) vtag-stack (?P<vtags>[0-9]+)") },                        
                        { 'mapper': 'TAGGEDVLAN', 're': re.compile("sub-port add sub-port [^ ]+ class-element [^ ]+ vtag-stack (?P<vlan>[0-9]+)") },                        
                    ],
            },
            'VIRTUAL INTERFACE CONFIG:': {
                    'regex': [ 
                        { 'mapper': 'VSWITCH', 're': re.compile("virtual-switch interface attach (sub-port|cpu-subinterface) (?P<virtualinterfaces>[^ ]+) vs (?P<name>.+)") }
                    ],
            },
            'LACP CONFIG:': {
                    'regex': [ 
                        { 'mapper': 'LAGPORT', 're': re.compile("aggregation add agg (?P<name>[^ ]+) port (?P<ports>.+)") }
                    ],
                    'preprocessor': {
                        'regex': [
                            re.compile("aggregation add agg [^ ]+ port (?P<MIXRANGE>.+)"),
                        ]
                    }
            },
            'LLDP': {
                    'regex': [ 
                        { 'mapper': 'LLDP', 're': re.compile("\|(?P<localPort>[^ ]+) +\|(?P<nbrPort>[^ ]+) +\| +Chassis Id: (?P<nbr>[A-Z0-9]{12}) +\|") }
                    ],
            },
            'EGRESS PORT CONFIG:': {
                    'regex': [ 
                        #{ 'mapper': 'LAGPORT', 're': re.compile("traffic-services queuing egress-port set port (?P<name>LAG[^ ]+) scheduler-algorithm (?P<egressqueue>[^ ]+)( shaper-rate ?P<egressshaper>[^ ]+)?") },
                        { 'mapper': 'SWITCHPORT', 're': re.compile("traffic-services queuing egress-port set port (?P<name>[^ ]+) scheduler-algorithm (?P<egressqueue>[^ ]+)( shaper-rate ?P<egressshaper>[^ ]+)?") }
                    ],
            },
            'RING PROTECTION CONFIG:': {
                    'regex': [ 
                        { 'mapper': 'LOGICALRING', 're': re.compile("ring-protection logical-ring create logical-ring-name (?P<name>[^ ]+) ring-id (?P<id>[0-9]+) west-port (?P<westport>[^ ]+) east-port (?P<eastport>[^ ]+)") },
                        { 'mapper': 'VIRTUALRING', 're': re.compile("ring-protection virtual-ring create virtual-ring-name (?P<name>[^ ]+) logical-ring (?P<logicalring>[^ ]+) raps-vid (?P<rapsvid>[0-9]+)(?: sub-ring (?P<subring>.+))?") },
                        { 'mapper': 'VIRTUALRING', 're': re.compile("ring-protection virtual-ring set ring (?P<name>[^ ]+) (?P<rplownerport>east-port-rpl|west-port-rpl) owner") },
                        { 'mapper': 'VIRTUALRING', 're': re.compile("ring-protection virtual-ring add ring (?P<name>[^ ]+) vid (?P<vlans>[0-9]+)") },
                        { 'mapper': 'VIRTUALRING', 're': re.compile("ring-protection virtual-ring add ring (?P<name>[^ ]+) vs (?P<vswitches>.+)") },
                    ],
                    'preprocessor': {
                        'regex': [
                            re.compile("ring-protection virtual-ring add ring .* vid (?P<MIXRANGE>.+)"),
                        ]
                    }
            },
            ## special config, when single line parsing is enabled this block is created automatically
            '_SINGLE_LINE_PARSING_': {
                    'regex': [ 
                        { 'mapper': 'HOST', 're': re.compile("! Chassis MAC: +(?P<chassisid>[A-F0-9]{12})") },
                        { 'mapper': 'DATETIMEEPOCH', 're': re.compile("! FIRST SEEN: +(?P<firstseen>[0-9]+)") },
                        { 'mapper': 'DATETIMEEPOCH', 're': re.compile("! LAST SEEN: +(?P<lastseen>[0-9]+)") },
                        { 'mapper': 'SYSTEM', 're': re.compile("! HARDWARE: +(?P<hwtype>.*)") },
                        { 'mapper': 'SYSTEM', 're': re.compile("! SOFTWARE: +(?P<software>.*)") },
                        { 'mapper': 'SWITCHPORT', 're': re.compile("! PORT_STATUS: \|(?P<name>[^ \|]+) *\|[^\|]+\| *(?P<operstate>Up|Down) *\| *(?P<linkstateduration>[^\|]+) *\| *(?P<xsvrstatus>[enabled|disabled]+)? *\| *(?P<stp>[a-zA-Z]+)? *\| *(?P<operspeedduplex>10+[HF]D)? *\| *(?P<mtu>[0-9]+)? *\|[^\|]+\|.*") },
                        { 'mapper': 'SWITCHPORT', 're': re.compile("! PORT_ETHERNET_CONFIGURATION: \| (?P<name>[^ \|]+) *\| *(?P<speedcapability>[^ \|]+) *\| *(?P<adminstate>enabled|disabled) *\| *(?P<adminspeedduplex>[^ \|]+) *\|[^\|]+\|[^\|]+\|[^\|]+\|[^\|]+\| *(?P<mtu>[0-9]+) *\|.*") },
                        #{ 'mapper': 'SWITCHPORT', 're': re.compile("! PORT_ETHERNET_CONFIGURATION: \| (?P<name>[^ \|]+) *\| *(?P<speedcapability>[^ \|]+) *\| *(?P<adminstate>enabled|disabled) *\| *(?P<adminspeedduplex>[^ \|]+) *\|[^\|]+\|[^\|]+\|[^\|]+\| *(?P<mtu>[0-9]+) *\|.*") },
                        { 'mapper': 'SWITCHPORT', 're': re.compile("! PORT_NETWORK_CONFIGURATION: \| (?P<name>[^ \|]+) *\|[^\|]+\|[^\|]+\|[^\|]+\|[^\|]+\|[^\|]+\|[^\|]+\|[^\|]+\|[^\|]+\| *(?P<vplsporttype>UNI|NNI) *\| *(?P<ethvcethertype>[^\|]+) *\|") },
                        { 'mapper': 'SWITCHPORT', 're': re.compile("! PORT_ETHERNET_CONFIGURATION: \| (?P<name>[^ \|]+) \| autoneg:(?P<autoneg>on|off).*") }
                    ],
                    'preprocessor': {
                        'regex': [
                            re.compile("! Chassis MAC: +(?P<MACTOUPPERSTRING>..:..:..:..:..:..)"),
                            re.compile("! Chassis MAC: +(?P<MACTOUPPERSTRING>[a-fA-F0-9]{12})"),
                            re.compile("! PORT_STATUS: .*\| *(?P<SWITCHPORTFORMAT>10[0G]*/[FH]D|Ena|Dis) *\|"),
                            re.compile("! PORT_NETWORK_CONFIGURATION: .*\| *(?P<PORTNNIUNI>Subsc|Ntwrk) *\|.*"),
                            re.compile("! PORT_ETHERNET_CONFIGURATION: .*\| *(?P<SWITCHPORTFORMAT>Ena|Dis) *\|.*"),
                            re.compile("! PORT_ETHERNET_CONFIGURATION: \| (?P<NAME>[^ \|]+) *\| *[^\|]+ *\| *[^\|]+ *\|.*(?P<AUTONEG>[aA]uto).*\| *[^\|]+ *\| *[^\|]+ *\| *[^\|]+ *\| *[^\|]+ *\| *[^\|]+ *\| *[^\|]+ *\| *[^\|]+ *\| *"),
                        ]
                    }
            },
            ## the mapping maps the above regular expressions to the model
            'mapping': {
                'DATETIMEEPOCH': { 'var': 'function', 'function': 'self.model.update_datetime_from_epoch' },
                'HOST': { 'var': 'self.model.host' },
                'SYSTEM': { 'var': 'self.model.system' },
                'LOOPBACKINTERFACE': { 'var': 'self.model.interfaces', 'class': '_interface_loopback' },
                'VLAN': { 'var': 'self.model.vlans', 'class': '_vlan' },
                'TAGGEDVLAN': { 'var': 'self.model.vlans', 'class': '_tagged_vlan', 'indexref': 'vlan' },
                'VLAN_PORT': { 'var': 'self.model.vlans', 'class': '_vlan', 'indexref': 'vlan' },
                'IPINTERFACE': { 'var': 'self.model.interfaces', 'class': '_interface_ip' },
                'REMOTEINTERFACE': { 'var': 'self.model.interfaces', 'class': '_interface_remote', 'index': 'remote' },
                'LOCALINTERFACE': { 'var': 'self.model.interfaces', 'class': '_interface_local', 'index': 'local' },
                'SWITCHPORT': { 'var': 'self.model.switchports', 'class': '_switchport', 'indexref': 'name' },
                'LAGPORT': { 'var': 'self.model.switchports', 'class': '_lagport', 'indexref': 'name' },
                'NTPSERVER': { 'var': 'self.model.ntpservers', 'class': '_nameserver' },
                'NAMESERVER': { 'var': 'self.model.nameservers', 'class': '_ntpserver' },
                'SYSLOGSERVER': { 'var': 'self.model.syslogservers', 'class': '_syslogserver' },
                'TACACS': { 'var': 'self.model.tacacs', 'class': '_tacacs' },
                'TACACSSERVER': { 'var': 'self.model.tacacsservers', 'class': '_tacacsserver' },
                'VCIRCUIT': { 'var': 'self.model.vcircuits', 'class': '_vcircuit' },
                'VSWITCH': { 'var': 'self.model.vswitches', 'class': '_vswitch', 'indexref': 'name' },
                'LLDP': { 'var': 'self.model.lldpneighbors', 'class': '_lldpneighbor' },
                'LOGICALRING': { 'var': 'self.model.rings', 'class': '_logicalring', 'indexref': 'name' },
                'VIRTUALRING': { 'var': 'self.model.rings', 'class': '_virtualring', 'indexref': 'name' },
                'SUBPORT': { 'var': 'self.model.subports', 'class': '_subport', 'indexref': 'name' },
                'SERVICE': { 'var': 'self.model.services', 'class': '_service', 'indexref': 'serviceid' }
            },
            ## regexes matches here will create a dynamic block automatically
            'dynamic_blocks': [
                re.compile("^! (?P<DYNAMICBLOCKNAME>LLDP): (?P<CONFIG>.*)$")
            ],
        }